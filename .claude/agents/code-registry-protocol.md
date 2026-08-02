---
name: 代码注册表规范
description: 源码仓库目录结构规范 + 代码注册表（code-registry.yaml）规范，定义源码存储、检索、自动触发分析的协议
type: protocol
last_updated: 2026-06-22
---

# 代码注册表规范

## 一、概述

本文档定义课程实验源码的**存储规范**和**注册协议**，是 LabGuideOrchestratorAgent 的 HOOK 机制能够**自动检测**源码存在并触发分析的基石。

> **设计目标**：
> 1. Orchestrator 无需人工干预，检测到源码 → 自动触发源码分析 → 分析完成后才生成内容
> 2. 源码仓库结构统一，任何 Agent 可按规范路径找到任意实验的源码
> 3. 注册表（registry）是源码与实验之间的**唯一索引**，确保"源码 → 分析 → 内容"的链路完整

---

## 二、源码仓库目录结构

### 2.1 整体目录结构

```
courses/
└── {sheet}/
    └── {course_id}/
        ├── _meta/
        │   ├── course-spec.yaml           # 课程规格（已有）
        │   └── run-state.yaml             # 运行状态（已有）
        │
        ├── source-codes/                  # ★ 新增：源码仓库根目录
        │   ├── _registry.yaml             # ★ 新增：代码注册表（索引文件）
        │   │
        │   ├── exp{01}/                   # 实验 1 源码目录
        │   │   ├── _meta.yaml             # 实验源码元数据
        │   │   ├── demo_{exp_name}.py     # 主入口 demo（必须）
        │   │   ├── config.py              # 配置参数（可选）
        │   │   ├── requirements.txt       # 依赖清单（必须）
        │   │   │
        │   │   ├── modules/               # 子模块（可选）
        │   │   │   ├── detector.py
        │   │   │   ├── tracker.py
        │   │   │   └── utils.py
        │   │   │
        │   │   ├── assets/                # 资源文件（可选）
        │   │   │   ├── model/             # 模型文件（.onnx/.tflite等）
        │   │   │   └── data/              # 测试数据
        │   │   │
        │   │   └── code-analysis/         # ★ 分析输出目录（SourceCodeAnalysisAgent 写入）
        │   │       ├── code-analysis-report.md
        │   │       └── analysis-status.yaml
        │   │
        │   ├── exp{02}/
        │   │   └── ...
        │   │
        │   └── exp{NN}/
        │       └── ...
        │
        ├── {course_id}_knowledge_graph.md  # 知识图谱（已有）
        ├── {course_id}_syllabus.md        # 教学大纲（已有）
        ├── {course_id}_lab_guide.md      # 实验指导书（已有）
        └── {course_id}_quiz.md           # 练测题库（已有）
```

### 2.2 实验源码目录（expXX/）结构

每个实验的源码目录有明确的**文件约束**：

| 文件 | 必须 | 说明 |
|------|------|------|
| `demo_{exp_name}.py` | ✅ 必须 | 主入口 demo，60-200行，含 main() + argparse + q键退出 |
| `requirements.txt` | ✅ 必须 | pip 依赖清单，每行一个包（格式：`包名==版本号`） |
| `_meta.yaml` | ✅ 必须 | 实验源码元数据（见 §三） |
| `config.py` | 建议 | 配置参数（阈值、超参数），避免硬编码 |
| `modules/` | 可选 | 子模块包，按功能拆分 |
| `assets/model/` | 可选 | 预训练模型文件 |
| `assets/data/` | 可选 | 测试图片/视频/数据文件 |
| `code-analysis/` | 自动生成 | SourceCodeAnalysisAgent 的输出目录 |

### 2.3 命名规范

```
# 主 demo 文件
demo_{实验名称缩写}.py
例如：
  demo_lab_color.py        （实验1：Lab颜色识别）
  demo_qrcode.py            （实验2：二维码识别）
  demo_line_follow.py       （实验3：巡线实验）
  demo_gesture.py           （实验4：手势识别）
  demo垃圾分类.py            （如用中文）

# 模块文件
{功能模块}.py
例如：
  hands_tracker.py          （手部追踪）
  pose_estimator.py         （姿态估计）
  qr_decoder.py             （二维码解码）

# 配置文件
config.py                   （通用）
config_{功能}.py            （专用，如 config_yolo.py）
```

---

## 三、代码注册表（_registry.yaml）

### 3.1 作用

`_registry.yaml` 是**源码仓库的索引文件**，位于 `source-codes/_registry.yaml`。
它记录每个实验的源码文件路径、分析状态、关联信息。

**Orchestrator 通过读取注册表判断**：
1. 哪些实验已有源码
2. 哪些实验源码已完成分析
3. 哪些实验需要触发源码分析

### 3.2 格式规范

```yaml
# ============================================================
# 课程源码注册表
# 生成规则：由 LabGuideOrchestratorAgent 初始化，SourceCodeAnalysisAgent 更新状态
# ============================================================
course_id: EXP001
course_name: 机器人视觉应用与开发
registry_version: "1.0"
updated_at: 2026-06-22T10:00:00

# 实验源码清单
experiments:

  # --------------------------------------------------
  # 实验1：源码存在，已分析
  # --------------------------------------------------
  - experiment_id: 1
    experiment_name: 基于Lab色彩空间的颜色识别实验
    code_status: analyzed          # analyzed / pending / missing
    source_files:
      - path: "exp1/demo_lab_color.py"
        type: main                 # main / module / config / asset
        lines: 145
        description: "主程序：摄像头采集→Lab转换→颜色分割→结果绘制"
      - path: "exp1/config.py"
        type: config
        lines: 28
        description: "颜色阈值配置（HSV/Lab可切换）"
      - path: "exp1/requirements.txt"
        type: dependency
        description: "opencv-python==4.8.0.74"
    analysis_status:
      status: completed            # pending / analyzing / completed / failed
      report_path: "exp1/code-analysis/code-analysis-report.md"
      status_file: "exp1/code-analysis/analysis-status.yaml"
      completed_at: 2026-06-22T10:15:00
      principles_identified: 3
      learning_steps: 9
      common_mistakes: 5

  # --------------------------------------------------
  # 实验2：源码存在，分析待执行
  # --------------------------------------------------
  - experiment_id: 2
    experiment_name: 二维码生成与识别检测实验
    code_status: pending            # 已有源码，待分析
    source_files:
      - path: "exp2/demo_qrcode.py"
        type: main
        lines: 98
        description: "二维码生成(pyqrcode)与识别(pyzbar)双模式"
      - path: "exp2/requirements.txt"
        type: dependency
        description: "qrcode[pil]==7.4.2, pyzbar==0.1.9"
    analysis_status:
      status: pending              # 将由 HOOK 触发后更新
      report_path: null
      status_file: "exp2/code-analysis/analysis-status.yaml"
      completed_at: null
      principles_identified: null
      learning_steps: null
      common_mistakes: null

  # --------------------------------------------------
  # 实验3：源码不存在（预留钩子）
  # --------------------------------------------------
  - experiment_id: 3
    experiment_name: 基于OpenCV的自主巡线实验
    code_status: missing           # 源码待补充
    source_files: []
    analysis_status:
      status: not_started
      report_path: null
      status_file: null
    missing_notice: "请在 source-codes/exp3/ 目录下补充 demo_openpose.py 和 requirements.txt"
    block_content_generation: true  # ★ 硬约束：源码缺失则阻止内容生成

  # ... 其余实验
```

### 3.3 实验源码元数据（expXX/_meta.yaml）

每个实验源码目录下必须有 `_meta.yaml`：

```yaml
# 实验源码元数据
experiment_id: 6
experiment_name: 基于MediaPipe的人机交互实验

# 源码仓库版本
code_version: "1.0"
author: {姓名}
last_updated: 2026-06-22

# 运行环境
runtime:
  python: "3.10"
  platform: [B2, C1]           # 支持的平台
  hardware: [摄像头, 深度相机]    # 所需硬件
  min_memory_gb: 2

# 依赖声明
dependencies:
  - opencv-python==4.8.0.74
  - mediapipe==0.10.9
  - numpy==1.24.3

# 核心算法标识（关联知识图谱）
algorithms:
  - { id: "3.1.1", name: "MediaPipe Hands", module: "utils/hands_tracker.py" }
  - { id: "3.4.1", name: "MediaPipe FaceMesh", module: "utils/face_mesh_tracker.py" }
  - { id: "3.5.1", name: "交互状态机", module: "demo_mediapipe.py" }

# 代码复杂度指标
metrics:
  total_lines: 487
  function_count: 12
  class_count: 3
  import_count: 8
  estimated_read_time_minutes: 45

# 与实验内容的对应关系
content_mapping:
  experiment_objective: "理解MediaPipe多任务融合原理，实现人机交互"
  key_steps_covered: [摄像头初始化, Hands初始化, 关键点绘制, 状态机设计]
  demo_script: "python3 demo_mediapipe.py --cam 0 --mode hands"
```

---

## 四、HOOK 触发协议

### 4.1 HOOK 是什么

**HOOK 是 LabGuideOrchestratorAgent 在生成实验内容前的一个强制检查点**。

```
┌─────────────────────────────────────────────────────────┐
│           LabGuideOrchestratorAgent                      │
│                                                         │
│  for each experiment:                                    │
│    ┌───────────────────────────────────────────┐         │
│    │ ★ HOOK: pre_experiment_generation         │ ← 新增  │
│    │   1. 读取 _registry.yaml                  │         │
│    │   2. 检查 experiment_id 的 code_status    │         │
│    │   3. 判断是否需要触发源码分析             │         │
│    └───────────────────────────────────────────┘         │
│                         │                               │
│           ┌─────────────┴─────────────┐                  │
│           ▼                           ▼                  │
│    code_status == analyzed    code_status != analyzed   │
│           │                           │                  │
│           ▼                           ▼                  │
│    继续生成实验内容           ┌──────────────────────┐   │
│                              │ SourceCodeAnalysis   │   │
│                              │ Agent (HOOK触发)     │   │
│                              │ → 等待分析完成        │   │
│                              │ → 更新 analysis_status│  │
│                              │ → 重新检查状态        │   │
│                              └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 4.2 HOOK 触发决策矩阵

| 代码状态 | 分析状态 | 豁免状态 | 行为 |
|---------|---------|---------|------|
| `analyzed` | `completed` | - | ✅ 直接生成实验内容 |
| `pending` | `pending` | - | ⚡ 触发 SourceCodeAnalysisAgent，分析完成后生成 |
| `pending` | `analyzing` | - | ⏳ 等待分析完成（轮询 status 文件，最长等待 5 分钟） |
| `missing` | `not_started` | `approved: false` | 🔴 **硬阻塞**：报错，要求人工补充源码 |
| `missing` | `not_started` | `approved: true` | ⚠️ **豁免放行**：生成内容，标注"待源码核实"，保持草稿版本 |
| `missing` | `failed` | - | 🔴 **硬阻塞**：报错，要求修复源码问题 |

> **豁免机制详见**: `.claude/rules/source-constraint-rule.md` §三"无源码豁免协议"。豁免由 `human_waiver.approved` 字段控制。

### 4.3 自动检测与触发（伪代码）

```python
# LabGuideOrchestratorAgent 中的 HOOK 实现（伪代码）

def pre_experiment_generation_hook(experiment_id):
    """
    实验内容生成前的强制 HOOK
    返回：analysis_report_path 或抛出异常
    """
    registry = read_registry()
    exp_entry = registry.get_experiment(experiment_id)

    code_status = exp_entry.code_status
    analysis_status = exp_entry.analysis_status.status

    if code_status == "missing":
        # 🔴 硬阻塞：源码不存在，内容不得生成
        raise CodeMissingError(
            f"实验 {experiment_id} 源码缺失。"
            f"请在 source-codes/exp{experiment_id:02d}/ 补充源码后重试。"
            f"必须包含：demo_*.py + requirements.txt + _meta.yaml"
        )

    if analysis_status == "completed":
        # ✅ 已分析，直接返回报告路径
        return exp_entry.analysis_status.report_path

    if analysis_status in ["pending", "analyzing"]:
        # ⚡ 触发或等待分析
        if code_status == "pending" and analysis_status == "pending":
            # 触发分析
            trigger_source_code_analysis(experiment_id)

        # 等待分析完成（最多 5 分钟）
        report_path = wait_for_analysis_completion(experiment_id, timeout=300)
        return report_path

    if analysis_status == "failed":
        raise CodeAnalysisFailedError(
            f"实验 {experiment_id} 源码分析失败，请检查源码后重试"
        )
```

### 4.4 轮询等待机制

```yaml
# 分析状态文件 analysis-status.yaml 的状态流转

initial:
  analysis_status: pending       # 由 orchestrator 创建
  trigger_by: hook               # 或 manual
  created_at: {timestamp}

after trigger:
  analysis_status: analyzing    # 由 SourceCodeAnalysisAgent 开始时更新
  started_at: {timestamp}
  agent: SourceCodeAnalysisAgent

after completion:
  analysis_status: completed     # 由 SourceCodeAnalysisAgent 完成时更新
  completed_at: {timestamp}
  report_path: "exp6/code-analysis/code-analysis-report.md"
  principles_identified: 4
  learning_steps: 9
  common_mistakes: 5

on failure:
  analysis_status: failed
  error_message: "源码文件不存在或语法错误"
  failed_at: {timestamp}
```

---

## 五、源码初始化流程

### 5.1 场景一：课程首次生成（无源码）

Orchestrator 在 `source-codes/` 目录不存在时，自动创建目录结构：

```
courses/sheet1/cv_practice/source-codes/
├── _registry.yaml              # Orchestrator 自动生成（骨架）
└── _template/
    └── expXX/
        ├── demo_template.py   # 示例模板
        ├── requirements.txt    # 依赖模板
        └── _meta.yaml          # 元数据模板
```

`_registry.yaml` 初始化为所有实验 `code_status: missing`：

```yaml
experiments:
  - experiment_id: 1
    experiment_name: {从 course-spec.yaml 读取}
    code_status: missing
    source_files: []
    analysis_status:
      status: not_started
    missing_notice: "请补充源码到 source-codes/exp1/ 目录"
    block_content_generation: true
  # ... 实验 2-N
```

**此时 workflow 进入"源码待补充"状态，需人工上传源码后重新触发。**

### 5.2 场景二：已有源码仓库

用户手动将源码放入 `source-codes/expXX/` 目录后，触发 Orchestrator 的**源码扫描**：

```python
def scan_source_codes():
    """
    扫描 source-codes/ 目录，更新 _registry.yaml
    """
    registry = read_registry()
    for exp_id in range(1, N+1):
        exp_dir = f"source-codes/exp{exp_id:02d}/"
        if not exists(exp_dir):
            registry.set_missing(exp_id)
            continue

        demo_files = glob(f"{exp_dir}/demo_*.py")
        req_files = glob(f"{exp_dir}/requirements.txt")
        meta_files = glob(f"{exp_dir}/_meta.yaml")

        if demo_files and req_files and meta_files:
            # 源码完整
            registry.set_pending(exp_id, source_files=[...])
        else:
            # 源码不完整（缺文件）
            registry.set_incomplete(exp_id, missing_files=[...])

    registry.save()
```

---

## 六、注册表维护协议

### 6.1 谁写入什么

| 文件 | 写入者 | 时机 |
|------|--------|------|
| `source-codes/_registry.yaml` | Orchestrator（初始化）+ SourceCodeAnalysisAgent（更新） | 课程生成开始 / 每次分析完成 |
| `source-codes/expXX/_meta.yaml` | 人工或代码生成Agent | 源码准备时 |
| `source-codes/expXX/code-analysis/analysis-status.yaml` | SourceCodeAnalysisAgent | 分析开始 / 分析完成 |
| `source-codes/expXX/code-analysis/code-analysis-report.md` | SourceCodeAnalysisAgent | 分析完成 |

### 6.2 版本管理

注册表有 `registry_version` 字段，版本升级时需保证向后兼容。
旧版本注册表可被 Orchestrator 自动迁移到新格式。

---

## 七、文件模板

### 7.1 requirements.txt 模板

```
# {实验名称} 依赖清单
# 平台：B2 实验箱 / C1 小车
# Python: 3.10

# 核心依赖（必须）
opencv-python==4.8.0.74
numpy==1.24.3

# 领域依赖（按实验选择）
mediapipe==0.10.9          # 实验6：人机交互
pyzbar==0.1.9              # 实验2：二维码
torch==2.0.1               # 实验5：深度学习（可选，CPU版）
# onnxruntime==1.15.1      # 实验7：ONNX推理（可选）

# 辅助工具
ipython==8.14.0             # 调试用
```

### 7.2 _meta.yaml 最小版

```yaml
experiment_id: 6
experiment_name: 基于MediaPipe的人机交互实验
code_version: "1.0"

dependencies:
  - opencv-python==4.8.0.74
  - mediapipe==0.10.9

run_command: python3 demo_mediapipe.py --cam 0 --mode hands

content_mapping:
  experiment_objective: "掌握MediaPipe Hands + FaceMesh + Pose三任务融合，理解交互状态机设计"
  key_steps_covered: [摄像头初始化, Hands检测, 关键点绘制, 状态机]
```

---

## 八、更新日志

| 日期 | 更新内容 |
|------|---------|
| 2026-06-22 | v1.0 初始版本：定义源码仓库结构 + 注册表格式 + HOOK触发协议 |
