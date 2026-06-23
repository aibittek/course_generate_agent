# ============================================================
# Source-code enforcement hook (Task variant)
# PreToolUse hook for Claude Code, fires on Task subagent calls.
# stdin: JSON payload
# exit:  0 = allow, 2 = block
#
# Fix history (2026-06-23):
#   1. UTF-8 stdin: read raw bytes, decode as UTF-8 (PS 5.1 default is GBK).
#   2. Course-only prompt: if experiment_id cannot be extracted, fall back to
#      a registry-wide scan and block when ANY experiment is `missing` AND
#      the target agent is in the LabGuide family. This kills the "8 experiments
#      at once" bypass.
#   3. Registry path: try both
#        courses/{sheet}/{folder}/source-codes/_registry.yaml  (protocol-spec)
#        source-codes/_registry.yaml                            (current repo layout)
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

if ($Payload.tool_name -ne "Task") { exit 0 }

$AgentName = [string]$Payload.tool_input.subagent_type
$Prompt    = [string]$Payload.tool_input.prompt

# Course-id to folder mapping (single source of truth)
$CourseMapping = @{
    "EXP001" = "sheet1/cv_practice"
    "EXP002" = "sheet1/speech_practice"
    "EXP003" = "sheet1/ros_practice"
    "EXP004" = "sheet1/slam_practice"
    "EXP005" = "sheet1/arm_practice"
    "EXP006" = "sheet1/llm_practice"
    "EXP007" = "sheet1/training"
    "IND001" = "sheet2/sorting_scene"
    "IND002" = "sheet2/manufacturing_scene"
    "IND003" = "sheet2/home_scene"
    "IND004" = "sheet2/inspection_scene"
}

# --- 2) Extract course id ---
$CourseId = ""
if ($Prompt -match '(EXP\d{3}|IND\d{3})') {
    $CourseId = $Matches[1]
} elseif ($Prompt -match 'course_id["\s:=]+([A-Z]+\d{3})') {
    $CourseId = $Matches[1]
}

$CourseFolder = ""
if ($CourseId -and $CourseMapping.ContainsKey($CourseId)) {
    $CourseFolder = $CourseMapping[$CourseId]
}

# --- 3) Extract experiment id (Chinese + English patterns) ---
# NOTE: build Chinese pattern from code points to dodge PS 5.1's GBK
# script-file decoding that would otherwise mangle literal Chinese in source.
$cnExp = [char]0x5B9E + [char]0x9A8C   # 实验
$ExperimentId = ""
if ($Prompt -match "${cnExp}\s*(\d+)") {
    $ExperimentId = $Matches[1]
} elseif ($Prompt -match 'experiment_id["\s:=]+(\d+)') {
    $ExperimentId = $Matches[1]
} elseif ($Prompt -match 'exp(\d{1,2})\b') {
    $ExperimentId = $Matches[1]
} elseif ($Prompt -match 'Experiment\s*(\d+)') {
    $ExperimentId = $Matches[1]
}

# --- 4) Decide which agents are gated ---
# Only enforce for agents that generate lab content from source.
$GatedAgents = @(
    "LabGuideAgent",
    "LabGuideOrchestratorAgent",
    "LabGuideExperimentAgent",
    "CourseResourceOrchestrator"
)
$IsGated = $false
foreach ($a in $GatedAgents) {
    if ($AgentName -eq $a) { $IsGated = $true; break }
}
if (-not $IsGated) { exit 0 }

# --- 5) Locate registry (try protocol path first, then repo-root fallback) ---
$BaseDir   = "e:\Source\xflz_eai_car1\course_generate_agent"
$RegistryCandidates = @()
if ($CourseFolder) {
    $RegistryCandidates += (Join-Path $BaseDir "courses\$CourseFolder\source-codes\_registry.yaml")
}
$RegistryCandidates += (Join-Path $BaseDir "source-codes\_registry.yaml")

$RegistryPath = $null
foreach ($p in $RegistryCandidates) {
    if (Test-Path $p) { $RegistryPath = $p; break }
}

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "[HOOK-TASK] Source code check" -ForegroundColor Cyan
Write-Host "[HOOK-TASK] Agent : $AgentName" -ForegroundColor Gray
Write-Host "[HOOK-TASK] Course: $CourseId  Exp: $ExperimentId" -ForegroundColor Gray
Write-Host "[HOOK-TASK] Reg   : $RegistryPath" -ForegroundColor Gray
Write-Host "===============================================" -ForegroundColor Cyan

if (-not $RegistryPath) {
    Write-Host "[BLOCK] No _registry.yaml found. Run ResourceParser/init first." -ForegroundColor Red
    exit 2
}

# --- 6) Parse registry (lightweight YAML scan, no module dep) ---
$RegLines = Get-Content $RegistryPath -Encoding UTF8

# Build a per-experiment status map by scanning sequential blocks.
# Each block starts with "  - experiment_id: N"
$ExpStatus = @{}  # id -> hashtable with code_status, analysis_status, blocks_gen
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
        # First `status:` inside an experiment block belongs to analysis_status.
        if (-not $ExpStatus[$curId].analysis_status) {
            $ExpStatus[$curId].analysis_status = $Matches[1].Trim()
        }
    } elseif ($curId -and $line -match '^\s+analysis_status:\s*(\S+)\s*$') {
        # Flat form: analysis_status: completed
        $ExpStatus[$curId].analysis_status = $Matches[1].Trim()
    } elseif ($curId -and $line -match '^\s+approved:\s*(true|false)') {
        # human_waiver.approved — the only `approved:` key in the schema.
        # An explicit human decision recorded after dialog confirmation.
        $ExpStatus[$curId].waiver = ($Matches[1] -eq "true")
    }
}

if ($ExpStatus.Count -eq 0) {
    Write-Host "[BLOCK] Registry has no experiment entries." -ForegroundColor Red
    exit 2
}

# --- 7) Decide ids to check ---
$IdsToCheck = @()
if ($ExperimentId) {
    $IdsToCheck += [int]$ExperimentId
} else {
    # No specific experiment named in prompt — gate against ALL experiments.
    # This kills the "8 experiments at once" + "全部执行" bypass.
    $IdsToCheck = $ExpStatus.Keys
}

$Blocked = @()
$Waived = @()
foreach ($id in $IdsToCheck) {
    if (-not $ExpStatus.ContainsKey([int]$id)) {
        $Blocked += "exp${id}: not in registry"
        continue
    }
    $e = $ExpStatus[[int]$id]
    $cs = $e.code_status
    $as = $e.analysis_status

    # human_waiver is the highest-priority signal: an explicit human decision
    # (recorded after dialog confirmation) to proceed without source code.
    # Honour it regardless of code_status / block_content_generation.
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
    Write-Host "        Fix: provide source under source-codes/expNN/ then re-run," -ForegroundColor Yellow
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
