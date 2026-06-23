# ============================================================
# Source-code enforcement hook (Edit/Write/MultiEdit variant)
# PreToolUse hook for Claude Code, fires when writing lab guides.
# stdin: JSON payload
# exit:  0 = allow, 2 = block
#
# Fix history (2026-06-23):
#   1. UTF-8 stdin: read raw bytes and decode as UTF-8 (PS 5.1 default is GBK,
#      which corrupts Chinese "实验" -> "瀹為獙" and breaks pattern matching).
#   2. Chinese matcher restored: "## 实验1:" / "实验 1" patterns now work.
#   3. Registry path: try protocol path first, then repo-root fallback.
#   4. If lab_guide.md is being seeded WITHOUT any experiment heading
#      (e.g. only contains the document header), allow — but still block any
#      subsequent edit that introduces an experiment heading whose source
#      hasn't been analyzed.
#   5. If the file is being CREATED (Write) and contains no experiment heading
#      at all, but ANY experiment in the registry is `missing`, we DO NOT block
#      the seed — the gate fires when content is added (Edit), not when an
#      empty/header-only file is created.
# ============================================================

# --- 1) UTF-8 stdin read (PS 5.1 workaround) ---
$stdin = [Console]::OpenStandardInput()
$ms = New-Object System.IO.MemoryStream
$buf = New-Object byte[] 4096
while (($n = $stdin.Read($buf, 0, $buf.Length)) -gt 0) {
    $ms.Write($buf, 0, $n)
}
$InputJson = [System.Text.Encoding]::UTF8.GetString($ms.ToArray())

if ([string]::IsNullOrEmpty($InputJson)) { exit 0 }

try {
    $Payload = $InputJson | ConvertFrom-Json
} catch {
    exit 0
}

$ToolName = $Payload.tool_name
if ($ToolName -ne "Edit" -and $ToolName -ne "Write" -and $ToolName -ne "MultiEdit") {
    exit 0
}

$FilePath = [string]$Payload.tool_input.file_path
if ([string]::IsNullOrEmpty($FilePath)) { exit 0 }

# --- 2) Only intercept lab_guide.md under courses/{sheet}/{folder}/ ---
$NormPath = $FilePath -replace '\\', '/'
if ($NormPath -notmatch 'courses/(sheet[12])/([^/]+)/[^/]*_lab_guide\.md$') {
    exit 0
}
$Sheet = $Matches[1]
$CourseFolder = "$Sheet/$($Matches[2])"

$FolderToCourse = @{
    "sheet1/cv_practice"          = "EXP001"
    "sheet1/speech_practice"      = "EXP002"
    "sheet1/ros_practice"         = "EXP003"
    "sheet1/slam_practice"        = "EXP004"
    "sheet1/arm_practice"         = "EXP005"
    "sheet1/llm_practice"         = "EXP006"
    "sheet1/training"             = "EXP007"
    "sheet2/sorting_scene"        = "IND001"
    "sheet2/manufacturing_scene"  = "IND002"
    "sheet2/home_scene"           = "IND003"
    "sheet2/inspection_scene"     = "IND004"
}
if (-not $FolderToCourse.ContainsKey($CourseFolder)) { exit 0 }
$CourseId = $FolderToCourse[$CourseFolder]

# --- 3) Collect all candidate text payloads ---
$TextChunks = New-Object System.Collections.Generic.List[string]
if ($null -ne $Payload.tool_input.old_string)  { $TextChunks.Add([string]$Payload.tool_input.old_string) }
if ($null -ne $Payload.tool_input.new_string)  { $TextChunks.Add([string]$Payload.tool_input.new_string) }
if ($null -ne $Payload.tool_input.content)     { $TextChunks.Add([string]$Payload.tool_input.content) }
if ($null -ne $Payload.tool_input.edits) {
    foreach ($e in $Payload.tool_input.edits) {
        if ($null -ne $e.old_string) { $TextChunks.Add([string]$e.old_string) }
        if ($null -ne $e.new_string) { $TextChunks.Add([string]$e.new_string) }
    }
}

# --- 4) Match experiment references (Chinese + English) ---
# NOTE: build Chinese pattern from code points to dodge PS 5.1's GBK
# script-file decoding that would otherwise mangle literal '实验' in source.
$cnExp = [char]0x5B9E + [char]0x9A8C   # 实验
$ExpIds = New-Object System.Collections.Generic.HashSet[int]
$Patterns = @(
    "(?:##\s*)?${cnExp}\s*(\d+)",
    '(?:##\s*)?Experiment\s*(\d+)',
    'experiment_id["\s:=]+(\d+)'
)
foreach ($chunk in $TextChunks) {
    foreach ($pat in $Patterns) {
        $rx = [regex]$pat
        foreach ($m in $rx.Matches($chunk)) {
            [void]$ExpIds.Add([int]$m.Groups[1].Value)
        }
    }
}

# If the edit doesn't reference any experiment heading, allow — this lets
# Orchestrators seed the file with a header-only template before per-experiment
# generation gates kick in.
if ($ExpIds.Count -eq 0) { exit 0 }

# --- 5) Locate registry ---
$BaseDir   = "e:\Source\xflz_eai_car1\course_generate_agent"
$RegistryCandidates = @(
    (Join-Path $BaseDir "courses\$CourseFolder\source-codes\_registry.yaml"),
    (Join-Path $BaseDir "source-codes\_registry.yaml")
)
$RegistryPath = $null
foreach ($p in $RegistryCandidates) {
    if (Test-Path $p) { $RegistryPath = $p; break }
}

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "[HOOK-EDIT] Source code check" -ForegroundColor Cyan
Write-Host "[HOOK-EDIT] Tool : $ToolName" -ForegroundColor Gray
Write-Host "[HOOK-EDIT] File : $FilePath" -ForegroundColor Gray
Write-Host "[HOOK-EDIT] Crs  : $CourseId -> $CourseFolder" -ForegroundColor Gray
Write-Host "[HOOK-EDIT] Exps : $([string]::Join(',', $ExpIds))" -ForegroundColor Gray
Write-Host "[HOOK-EDIT] Reg  : $RegistryPath" -ForegroundColor Gray
Write-Host "===============================================" -ForegroundColor Cyan

if (-not $RegistryPath) {
    Write-Host "[BLOCK] _registry.yaml not found." -ForegroundColor Red
    exit 2
}

# --- 6) Parse registry (lightweight scan, same logic as Task hook) ---
$RegLines = Get-Content $RegistryPath -Encoding UTF8
$ExpStatus = @{}
$curId = $null
foreach ($line in $RegLines) {
    if ($line -match '^\s*-\s*experiment_id:\s*(\d+)') {
        $curId = [int]$Matches[1]
        $ExpStatus[$curId] = @{ code_status = ""; analysis_status = ""; block = $false; waiver = $false }
    } elseif ($curId -and $line -match '^\s+code_status:\s*(\S+)') {
        $ExpStatus[$curId].code_status = $Matches[1].Trim()
    } elseif ($curId -and $line -match '^\s+block_content_generation:\s*(true|false)') {
        $ExpStatus[$curId].block = ($Matches[1] -eq "true")
    } elseif ($curId -and $line -match '^\s+status:\s*(\S+)') {
        if (-not $ExpStatus[$curId].analysis_status) {
            $ExpStatus[$curId].analysis_status = $Matches[1].Trim()
        }
    } elseif ($curId -and $line -match '^\s+analysis_status:\s*(\S+)\s*$') {
        $ExpStatus[$curId].analysis_status = $Matches[1].Trim()
    } elseif ($curId -and $line -match '^\s+approved:\s*(true|false)') {
        # human_waiver.approved — the only `approved:` key in the schema.
        $ExpStatus[$curId].waiver = ($Matches[1] -eq "true")
    }
}

# --- 7) Per-experiment gate ---
$Blocked = @()
$Waived = @()
foreach ($id in $ExpIds) {
    if (-not $ExpStatus.ContainsKey([int]$id)) {
        $Blocked += "exp${id}: not in registry"
        continue
    }
    $e = $ExpStatus[[int]$id]
    $cs = $e.code_status
    $as = $e.analysis_status

    # human_waiver: explicit human decision (after dialog) to proceed
    # without source. Honour it over code_status / block_content_generation.
    if ($e.waiver) {
        $Waived += "exp${id}: human_waiver.approved=true (code_status=${cs})"
        continue
    }

    if ($cs -eq "missing") {
        $Blocked += "exp${id}: code_status=missing"
    } elseif ($cs -eq "pending" -and $as -ne "completed") {
        $Blocked += "exp${id}: analysis_status=${as} (need completed)"
    } elseif ($cs -eq "analyzed" -and $as -ne "completed") {
        $Blocked += "exp${id}: inconsistent (analyzed but analysis_status=${as})"
    } elseif ($e.block) {
        $Blocked += "exp${id}: block_content_generation=true"
    }
}

if ($Blocked.Count -gt 0) {
    Write-Host "[BLOCK] Source-code precondition not satisfied:" -ForegroundColor Red
    foreach ($b in $Blocked) {
        Write-Host "        - $b" -ForegroundColor Red
    }
    Write-Host "        Fix: provide source under source-codes/expNN/ and run SourceCodeAnalysisAgent," -ForegroundColor Yellow
    Write-Host "        or add human_waiver.approved=true in _registry.yaml (no-source mode)." -ForegroundColor Yellow
    exit 2
}

if ($Waived.Count -gt 0) {
    Write-Host "[WARN] Proceeding under human waiver (NO source code):" -ForegroundColor Yellow
    foreach ($w in $Waived) {
        Write-Host "        - $w" -ForegroundColor Yellow
    }
    Write-Host "        Generated content MUST be tagged [WAIT-SOURCE] / 待源码核实." -ForegroundColor Yellow
}

Write-Host "[PASS]" -ForegroundColor Green
exit 0
