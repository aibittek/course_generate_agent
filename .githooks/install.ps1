# .githooks/install.ps1
# Windows / PowerShell 一键启用本仓库内的 git hooks。
# 用法：powershell -ExecutionPolicy Bypass -File .githooks\install.ps1

$ErrorActionPreference = "Stop"

if (-not (git rev-parse --is-inside-work-tree 2>$null)) {
    Write-Error "[install] 当前不在 git 仓库内"
    exit 1
}

git config core.hooksPath .githooks
Write-Host "[install] core.hooksPath = .githooks"

Write-Host "[install] 已启用 csv 漂移检测 hooks："
Write-Host "  - post-checkout : 切分支时检测 csv 变更"
Write-Host "  - post-merge    : pull/merge 后检测 csv 变更"
Write-Host "  - pre-commit    : 提交前检测 csv 与 spec 不同步（默认非阻塞）"
Write-Host ""
Write-Host "[install] 卸载: git config --unset core.hooksPath"
Write-Host "[install] 阻塞模式: `$env:STRICT_CSV_DRIFT=1 ; git commit ..."
