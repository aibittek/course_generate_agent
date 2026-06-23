---
name: source-code-hook-skill
description: 源码检查钩子技能 - 实验内容生成前的强制检查点
trigger: 自动触发，无需trigger关键词
---

# 源码检查HOOK

## 角色

这是实验指导书生成流程中的一个**强制检查节点**，在LabGuideOrchestratorAgent调用LabGuideExperimentAgent之前，必须执行此HOOK。

## 适用范围（v2.1 扩展）

本检查不仅在"首次生成"时触发，对以下场景同等适用，均不可绕过：

| 场景 | 触发工具 | 拦截脚本 |
|------|---------|---------|
| 首次生成实验指导书 | Task → LabGuideExperimentAgent | `.claude/hooks/enforce-source-hook.ps1` |
| 重新生成单个实验段落 | Edit / Write / MultiEdit 命中 `*_lab_guide.md` 且包含 `## 实验N：` 标题 | `.claude/hooks/enforce-source-on-edit.ps1` |
| 局部修改实验段落（步骤/代码/总结等） | Edit / Write / MultiEdit 命中实验段落 | `.claude/hooks/enforce-source-on-edit.ps1` |

只有目标实验对应的 `source-codes/exp<NN>/code-analysis/analysis-status.yaml` 中 `analysis_status: completed`，相关工具调用才会被放行。

## 触发时机

```
┌─────────────────────────────────────────────────────────┐
│  LabGuideOrchestratorAgent                               │
│                                                          │
│  for each experiment:                                    │
│    ┌──────────────────────────────────────────────┐     │
│    │ ★ 执行 HOOK: source_code_pre_check ★        │     │
│    │   1. 读取 source-codes/_registry.yaml       │     │
│    │   2. 检查 experiment_id 的 code_status      │     │
│    │   3. 检查 analysis_status.status            │     │
│    └──────────────────────────────────────────────┘     │
│                         │                               │
│          ┌──────────────┼──────────────┐                │
│          ▼              ▼              ▼                │
│       ✅ PASS        ⚡ TRIGGER      🔴 BLOCK          │
│    (已分析)      (待分析)        (缺失/失败)           │
└─────────────────────────────────────────────────────────┘
```

## 检查逻辑

### 1. 读取注册表

读取 `source-codes/_registry.yaml`，找到对应实验的条目：

```yaml
experiments:
  - experiment_id: 6
    experiment_name: 基于MediaPipe的人机交互实验
    code_status: pending       # analyzed / pending / missing
    source_files:
      - path: "exp6/demo_mediapipe.py"
        type: main
    analysis_status:
      status: completed        # pending / analyzing / completed / failed
      report_path: "exp6/code-analysis/code-analysis-report.md"
```

### 2. 决策矩阵

| code_status | analysis_status | 决策 | 行动 |
|------------|----------------|------|------|
| analyzed | completed | ✅ PASS | 直接返回报告路径，继续生成 |
| pending | pending | ⚡ TRIGGER | 调用SourceCodeAnalysisAgent |
| pending | analyzing | ⏳ WAIT | 轮询等待（最多5分钟） |
| missing | not_started | 🔴 BLOCK | 硬阻塞，输出错误 |
| missing | failed | 🔴 BLOCK | 硬阻塞，输出错误 |

### 3. 通过条件

**PASS的充分必要条件**：
- `code_status == "analyzed"` **且**
- `analysis_status.status == "completed"` **且**
- `analysis_status.report_path` 指向的文件存在

## 输出

### 通过时

```yaml
hook_result:
  status: pass
  experiment_id: 6
  report_path: "source-codes/exp6/code-analysis/code-analysis-report.md"
  next_action: proceed_to_generate
```

### 触发分析时

```yaml
hook_result:
  status: trigger_analysis
  experiment_id: 6
  source_files:
    - "exp6/demo_mediapipe.py"
    - "exp6/config.py"
    - "exp6/requirements.txt"
  next_action: invoke_source_code_analysis_agent
```

### 阻塞时

```yaml
hook_result:
  status: block
  experiment_id: 6
  reason: missing_code      # missing_code / analysis_failed / timeout
  required_files:
    - "demo_mediapipe.py"
    - "requirements.txt"
    - "_meta.yaml"
  message: |
    🔴 实验6源码缺失，内容生成被阻塞。
    请在 source-codes/exp6/ 补充以下文件：
      - demo_mediapipe.py（主程序，60-200行，含main()）
      - requirements.txt（依赖清单）
      - _meta.yaml（元数据）
    补充完成后重新触发。
  block_continue: true
```

## SourceCodeAnalysisAgent 的输出契约

当HOOK触发分析时，SourceCodeAnalysisAgent必须输出：

```yaml
# source-codes/exp6/code-analysis/analysis-status.yaml
experiment_id: 6
analysis_status: completed
completed_at: 2026-06-22T10:30:00
report_path: "exp6/code-analysis/code-analysis-report.md"

# 分析报告必须包含：
# 1. code_architecture - 文件结构和核心模块
# 2. principles[] - 原理分析（含code_location）
# 3. learning_steps - 三阶段学习路径
# 4. common_mistakes[] - 易错点清单
```

## 轮询等待机制

当 `analysis_status == "analyzing"` 时：

```python
timeout = 300  # 5分钟
interval = 5   # 每5秒检查一次
elapsed = 0

while elapsed < timeout:
    status = read_yaml("source-codes/exp6/code-analysis/analysis-status.yaml")
    if status.analysis_status == "completed":
        return report_path
    if status.analysis_status == "failed":
        raise HOOKBlockError("源码分析失败")
    sleep(interval)
    elapsed += interval

raise HOOKBlockError("源码分析超时")
```

## 强制约束

1. **不通过HOOK，不得调用LabGuideExperimentAgent**
2. **HOOK结果必须写入日志**
3. **阻塞实验必须记录到generation-progress.md**
4. **源码分析报告是LabGuideExperimentAgent的必需输入**

## 与LabGuideExperimentAgent的接口

HOOK通过后，传递给LabGuideExperimentAgent的上下文必须包含：

```yaml
experiment_context:
  id: 6
  name: 基于MediaPipe的人机交互实验
  # ... 其他字段

  # ★ 来自HOOK的输出
  source_code_analysis:
    report_path: "source-codes/exp6/code-analysis/code-analysis-report.md"
    principles:
      - id: "3.1.1"
        name: "MediaPipe Hands"
        code_location: "hands_tracker.py L30-35"  # ★ 必须有源码位置
    common_mistakes:
      - phenomenon: "关键点不显示"
        solution: "降低置信度阈值"
        code_location: "config.py L3"
```
