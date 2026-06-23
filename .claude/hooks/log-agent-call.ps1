#!/usr/bin/env pwsh
# ============================================================
# Agent调用日志记录脚本
# ============================================================

# 读取stdin的JSON
$InputJson = [Console]::In.ReadToEnd()

$LogDir = "e:\Source\xflz_eai_car1\course_generate_agent\.claude\hooks\logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$LogFile = Join-Path $LogDir "agent-calls-$(Get-Date -Format 'yyyy-MM-dd').log"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

if (-not [string]::IsNullOrEmpty($InputJson)) {
    try {
        $Input = $InputJson | ConvertFrom-Json
        $AgentName = $Input.tool_input.subagent_type
        $LogEntry = "[$Timestamp] [post] Agent=$AgentName Description=$($Input.tool_input.description)"
    }
    catch {
        $LogEntry = "[$Timestamp] [post] Raw=$InputJson"
    }
}
else {
    $LogEntry = "[$Timestamp] [post] (no input)"
}

try {
    Add-Content -Path $LogFile -Value $LogEntry -Encoding UTF8
}
catch {
    # 日志失败不影响主流程
}
