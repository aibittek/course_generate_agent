# 强制HOOK测试验证方案

本文档定义如何测试验证源码HOOK强制约束机制。

---

## 一、测试环境

### 1.1 测试课程
- **课程**：`cv_practice`（机器人视觉应用与开发）
- **测试实验**：实验6（基于MediaPipe的人机交互实验）

### 1.2 测试文件位置

```
courses/sheet1/cv_practice/source-codes/
├── _registry.yaml              # 源码注册表
└── exp06/
    ├── demo_mediapipe.py       # 测试用源码
    ├── requirements.txt
    └── code-analysis/
        └── analysis-status.yaml  # 分析状态文件

.claude/hooks/
├── enforce-source-hook.ps1      # 强制检查脚本
├── log-agent-call.ps1          # 日志记录脚本
└── logs/                       # Agent调用日志目录
```

### 1.3 HOOK脚本位置
- **强制检查脚本**：`e:\Source\xflz_eai_car1\course_generate_agent\.claude\hooks\enforce-source-hook.ps1`
- **settings.json配置**：
```json
{
  "hooks": {
    "pre-agent": ["pwsh -File .claude/hooks/enforce-source-hook.ps1 ..."],
    "post-agent": ["pwsh -File .claude/hooks/log-agent-call.ps1 ..."]
  }
}
```

---

## 二、测试用例

### 2.1 测试用例清单

| 用例ID | 测试场景 | analysis_status | 预期结果 |
|--------|---------|----------------|---------|
| TC-01 | 正常流程：分析已完成 | `completed` | ✅ HOOK通过，允许执行 |
| TC-02 | 拦截流程：分析尚未开始 | `pending` | 🔴 HOOK拦截，阻止执行 |
| TC-03 | 拦截流程：分析进行中 | `analyzing` | ⏳ HOOK等待，显示等待信息 |
| TC-04 | 拦截流程：分析失败 | `failed` | 🔴 HOOK拦截，显示失败原因 |
| TC-05 | 错误处理：状态文件不存在 | - | 🔴 HOOK拦截，提示文件不存在 |
| TC-06 | 错误处理：注册表不存在 | - | 🔴 HOOK拦截，提示仓库未初始化 |

---

## 三、测试执行步骤

### 3.1 准备：验证测试文件存在

```powershell
# 检查注册表
Test-Path "e:\Source\xflz_eai_car1\course_generate_agent\courses\sheet1\cv_practice\source-codes\_registry.yaml"

# 检查分析状态文件
Test-Path "e:\Source\xflz_eai_car1\course_generate_agent\courses\sheet1\cv_practice\source-codes\exp06\code-analysis\analysis-status.yaml"

# 检查HOOK脚本
Test-Path "e:\Source\xflz_eai_car1\course_generate_agent\.claude\hooks\enforce-source-hook.ps1"
```

---

### TC-01：✅ 正常流程（analysis_status = completed）

**目标**：验证HOOK在分析完成时允许通过

**前置条件**：
- `exp06/code-analysis/analysis-status.yaml` 的 `analysis_status` 为 `completed`

**执行步骤**：

1. 修改分析状态为 `completed`：
```yaml
# analysis-status.yaml
analysis_status: completed
completed_at: 2026-06-22T12:00:00
report_path: "exp06/code-analysis/code-analysis-report.md"
```

2. 执行HOOK脚本：
```powershell
pwsh -File "e:\Source\xflz_eai_car1\course_generate_agent\.claude\hooks\enforce-source-hook.ps1" `
     -AgentName "LabGuideExperimentAgent" `
     -ExperimentId "6" `
     -CoursePath "e:\Source\xflz_eai_car1\course_generate_agent\courses\sheet1\cv_practice"
```

3. 检查退出码：
```powershell
$LASTEXITCODE  # 应为 0
```

**预期结果**：
```
===============================================
[HOOK] 源码检查强制执行中...
[HOOK] Agent: LabGuideExperimentAgent
[HOOK] ExperimentId: 6
[HOOK] 当前分析状态: completed
===============================================
✅ HOOK通过: 实验6源码分析已完成
===============================================
退出码: 0
```

---

### TC-02：🔴 拦截流程（analysis_status = pending）

**目标**：验证HOOK在分析未开始时拦截

**前置条件**：
- `analysis-status.yaml` 的 `analysis_status` 为 `pending`

**执行步骤**：

1. 修改分析状态为 `pending`：
```yaml
# analysis-status.yaml
analysis_status: pending
```

2. 执行HOOK脚本：
```powershell
pwsh -File "e:\Source\xflz_eai_car1\course_generate_agent\.claude\hooks\enforce-source-hook.ps1" `
     -AgentName "LabGuideExperimentAgent" `
     -ExperimentId "6"
```

**预期结果**：
```
===============================================
[HOOK] 源码检查强制执行中...
[HOOK] Agent: LabGuideExperimentAgent
[HOOK] ExperimentId: 6
[HOOK] 当前分析状态: pending
===============================================
🔴 HOOK拦截: 实验6源码分析尚未开始
   状态: pending
   操作: 请先执行 SourceCodeAnalysisAgent
===============================================
退出码: 1  ← 非零退出码，阻止Agent执行
```

---

### TC-03：🔴 拦截流程（analysis_status = analyzing）

**目标**：验证HOOK在分析进行中时拦截

**执行步骤**：

1. 修改分析状态为 `analyzing`：
```yaml
analysis_status: analyzing
started_at: 2026-06-22T12:00:00
```

2. 执行HOOK脚本

**预期结果**：
```
🔴 HOOK拦截: 实验6正在分析中
   状态: analyzing
   操作: 等待分析完成或手动检查
退出码: 1
```

---

### TC-04：🔴 拦截流程（analysis_status = failed）

**目标**：验证HOOK在分析失败时拦截

**执行步骤**：

1. 修改分析状态为 `failed`：
```yaml
analysis_status: failed
error_message: "源码语法错误：第45行缺少冒号"
failed_at: 2026-06-22T12:00:00
```

2. 执行HOOK脚本

**预期结果**：
```
🔴 HOOK拦截: 实验6源码分析失败
   状态: failed
   操作: 请检查源码问题，修复后重置为 pending 状态
退出码: 1
```

---

### TC-05：🔴 错误处理（状态文件不存在）

**目标**：验证HOOK在状态文件缺失时拦截

**执行步骤**：

1. 删除分析状态文件：
```powershell
Remove-Item "e:\Source\xflz_eai_car1\course_generate_agent\courses\sheet1\cv_practice\source-codes\exp06\code-analysis\analysis-status.yaml"
```

2. 执行HOOK脚本

**预期结果**：
```
🔴 HOOK拦截: 实验6的源码分析状态文件不存在
   原因: 源码分析尚未执行或分析失败
   操作: 请先执行 SourceCodeAnalysisAgent 分析源码
退出码: 1
```

---

### TC-06：🔴 错误处理（注册表不存在）

**目标**：验证HOOK在注册表缺失时拦截

**执行步骤**：

1. 临时重命名注册表：
```powershell
Rename-Item "e:\Source\xflz_eai_car1\course_generate_agent\courses\sheet1\cv_practice\source-codes\_registry.yaml" "_registry.yaml.bak"
```

2. 执行HOOK脚本

**预期结果**：
```
🔴 HOOK拦截: 源码注册表不存在
   原因: 课程源码仓库未初始化
   操作: 请先运行课程初始化，生成 source-codes/_registry.yaml
退出码: 1
```

3. 恢复注册表：
```powershell
Rename-Item "_registry.yaml.bak" "_registry.yaml"
```

---

## 四、集成测试

### 4.1 端到端测试流程

```
1. 重置实验6状态为 pending
   ↓
2. 尝试直接调用 LabGuideExperimentAgent
   ↓
3. 验证HOOK拦截（退出码应为1）
   ↓
4. 修改状态为 completed
   ↓
5. 再次调用 LabGuideExperimentAgent
   ↓
6. 验证HOOK通过（退出码应为0）
```

### 4.2 自动化测试脚本

```powershell
# test-hook-enforcement.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HOOK强制约束自动化测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$CoursePath = "e:\Source\xflz_eai_car1\course_generate_agent\courses\sheet1\cv_practice"
$StatusFile = "$CoursePath\source-codes\exp06\code-analysis\analysis-status.yaml"
$HookScript = "e:\Source\xflz_eai_car1\course_generate_agent\.claude\hooks\enforce-source-hook.ps1"

# 测试用例
$Tests = @(
    @{ Name = "TC-02: pending状态拦截"; Status = "pending"; ExpectedExit = 1 },
    @{ Name = "TC-01: completed状态通过"; Status = "completed"; ExpectedExit = 0 }
)

$Results = @()

foreach ($Test in $Tests) {
    Write-Host "`n[Test] $($Test.Name)" -ForegroundColor Yellow

    # 修改状态
    $Content = Get-Content $StatusFile -Raw
    $Content = $Content -replace "analysis_status: \w+", "analysis_status: $($Test.Status)"
    Set-Content $StatusFile -Value $Content -NoNewline

    # 执行HOOK
    & pwsh $HookScript -AgentName "LabGuideExperimentAgent" -ExperimentId "6" -CoursePath $CoursePath

    $ActualExit = $LASTEXITCODE
    $Passed = ($ActualExit -eq $Test.ExpectedExit)

    $Results += @{
        Name = $Test.Name
        Expected = $Test.ExpectedExit
        Actual = $ActualExit
        Passed = $Passed
    }

    if ($Passed) {
        Write-Host "[PASS] 退出码: $ActualExit (预期: $($Test.ExpectedExit))" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] 退出码: $ActualExit (预期: $($Test.ExpectedExit))" -ForegroundColor Red
    }
}

# 输出汇总
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试结果汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$PassCount = ($Results | Where-Object { $_.Passed }).Count
$TotalCount = $Results.Count

foreach ($Result in $Results) {
    $Status = if ($Result.Passed) { "[PASS]" } else { "[FAIL]" }
    $Color = if ($Result.Passed) { "Green" } else { "Red" }
    Write-Host "$Status $($Result.Name)" -ForegroundColor $Color
}

Write-Host "`n通过: $PassCount / $TotalCount" -ForegroundColor $(if ($PassCount -eq $TotalCount) { "Green" } else { "Red" })
```

---

## 五、验证HOOK生效

### 5.1 验证settings.json配置

```powershell
Get-Content "e:\Source\xflz_eai_car1\course_generate_agent\.claude\settings.json" | ConvertFrom-Json | Select-Object -ExpandProperty hooks
```

预期输出：
```json
{
  "pre-agent": ["pwsh -File .claude/hooks/enforce-source-hook.ps1 ..."],
  "post-agent": ["pwsh -File .claude/hooks/log-agent-call.ps1 ..."]
}
```

### 5.2 验证日志记录

```powershell
# 查看Agent调用日志
Get-Content "e:\Source\xflz_eai_car1\course_generate_agent\.claude\hooks\logs\agent-calls-2026-06-22.log"
```

预期输出格式：
```
[2026-06-22 12:00:00] [pre] Agent=LabGuideExperimentAgent ExpId=6 Result=
[2026-06-22 12:00:05] [post] Agent=LabGuideExperimentAgent ExpId=6 Result=blocked
```

---

## 六、常见问题排查

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| HOOK未执行 | settings.json配置错误 | 检查hooks路径是否正确 |
| 退出码始终0 | 脚本内部错误 | 用 `-Verbose` 运行调试 |
| 状态解析失败 | YAML格式问题 | 检查缩进和空格 |
| 路径问题 | Windows路径包含空格 | 用引号包裹路径 |
