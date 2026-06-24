---
name: course-generation-workflow
description: 端到端课程资源生成工作流 - 从课程信息到完整资源包（含源码仓库+HOOK机制+增量更新）
trigger: /生成课程、生成课程资源、生成{course_name}
---

# 课程资源生成工作流

本文档定义从课程信息到完整课程资源包的端到端工作流程，包括全量生成和增量更新两种模式。

---

## 工作流模式

### 模式1: 全量生成（本文档）
- 适用场景: 新课程生成、大范围结构调整
- 执行时间: 10-30分钟
- 触发方式: `/生成课程 {course_id}` 或 `生成 {course_name}`

### 模式2: 增量更新（见 IncrementalUpdateAgent）
- 适用场景: 单实验/单章节修改
- 执行时间: 1-5分钟
- 触发方式: `更新 {course_id} 实验{N}` 或 `/incremental-update`

---

## 引用Skill

- `.claude/skills/spec-parser-skill/SKILL.md` — **CSV → course-spec.yaml 固定解析器（Step 1 唯一执行器）**
- `.claude/skills/source-code-hook-skill/SKILL.md` — **源码HOOK检查（强制执行）**

## 核心设计原则

1. **源码是内容的锚点** — 所有实验内容必须基于源码分析生成
2. **HOOK是强制门控** — 未经HOOK通过的实验，不得生成内容
3. **状态持久化** — 所有状态写入文件，断点可恢复

---

## 一、流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                         启动                                     │
│              用户输入: 生成 {课程名称}                            │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: 资源列表解析                                             │
│           resource-parser-agent ── 调用 spec-parser-skill        │
│  - 读取 input/course_spec.csv                                    │
│  - parser.py: csv → course-spec.yaml（唯一可信源）                │
│  - validator.py: 字段校验 + 课程目录硬比对                         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: 知识图谱 + 教学大纲 (并行)                               │
│ ┌─────────────────────┐  ┌─────────────────────┐               │
│ │ knowledge-graph-    │  │   syllabus-agent   │               │
│ │ agent              │  │                    │               │
│ └─────────────────────┘  └─────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: 源码仓库初始化                                           │
│           LabGuideOrchestratorAgent                             │
│  - 创建 source-codes/ 目录结构                                   │
│  - 初始化 _registry.yaml                                        │
│  - 扫描已有源码，更新 code_status                               │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: 实验生成（源码HOOK + 内容生成）                          │
│                                                                   │
│  for each experiment:                                            │
│    ┌─────────────────────────────────────────────────────┐      │
│    │ ★ HOOK: 源码检查（引用 source-code-hook-skill） ★  │      │
│    │   ├─ code_status=analyzed → ✅ 直接生成             │      │
│    │   ├─ code_status=pending → ⚡ 触发分析Agent       │      │
│    │   └─ code_status=missing → 🔴 硬阻塞              │      │
│    └─────────────────────────────────────────────────────┘      │
│                            │                                     │
│                            ▼                                     │
│    ┌──────────────────────────────────────────────────────┐   │
│    │ SourceCodeAnalysisAgent × N（并行，HOOK触发）          │   │
│    │  ├─ 读取源码文件                                       │   │
│    │  ├─ 输出：code-analysis-report.md                    │   │
│    │  └─ 更新：analysis-status.yaml → completed           │   │
│    └──────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│    ┌──────────────────────────────────────────────────────┐   │
│    │ LabGuideExperimentAgent × N（HOOK通过后执行）         │   │
│    │  ├─ 输入：experiment_context + source_code_analysis   │   │
│    │  ├─ 原理→源码位置对应                                │   │
│    │  └─ 输出：_parts/experiment-{id}.md                 │   │
│    └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: 练测题生成（串行，依赖实验内容）                        │
│           quiz-agent                                            │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: 内容审核                                                 │
│           content-audit-agent                                   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: 质量审核                                                 │
│           quality-review-agent                                  │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 8: 资源整合输出                                             │
│           resource-integrator-agent                              │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         完成                                     │
│                   输出课程资源包路径                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、详细步骤

### Step 1: 资源列表解析

**调用Agent**: `resource-parser-agent`

**核心动作**：触发 `.claude/skills/spec-parser-skill/`，本身不解析。

**操作**:
1. `python .claude/skills/spec-parser-skill/parser.py` — 读取 `input/course_spec.csv`，写出 `course-spec.yaml`
2. `python .claude/skills/spec-parser-skill/validator.py` — 字段校验（errors / warnings）
3. 课程目录硬比对：`len(experiments) == 预期` 且 `total_hours == 预期`
4. 校验通过 → 写入 `spec_validation` 块；失败 → spec.status=blocked，触发 CP-2

> ⚠️ 任意失败都不进入 Step 2；spec.yaml 不就绪 → 下游禁止启动。

---

### Step 2: 知识图谱 + 教学大纲（并行）

**调用Agent**:
- `knowledge-graph-agent`
- `syllabus-agent`

两者都基于 `course-spec.yaml` 生成。

---

### Step 3: 源码仓库初始化

**调用Agent**: `LabGuideOrchestratorAgent`

**操作**:
1. 检查 `source-codes/` 是否存在
   - 不存在 → 创建目录骨架 + 初始化 `_registry.yaml`（所有实验 = missing）
   - 存在 → 扫描并更新 `_registry.yaml`
2. 输出源码状态摘要

**输出**:
```
源码状态摘要：
- 已分析：2个（exp1, exp5）
- 待分析：3个（exp2, exp3, exp4）
- 缺失源码：2个（exp6, exp7）→ 🔴 内容生成阻塞
```

---

### Step 4: 实验生成（源码HOOK + 内容生成）

#### 4.1 HOOK检查（引用 source-code-hook-skill）

**对每个实验执行 HOOK**：

读取 `source-codes/_registry.yaml`，根据决策矩阵执行：

| code_status | analysis_status | 决策 |
|------------|----------------|------|
| analyzed | completed | ✅ 直接生成 |
| pending | pending | ⚡ 触发分析 |
| pending | analyzing | ⏳ 轮询等待 |
| missing | not_started | 🔴 硬阻塞 |

#### 4.2 触发源码分析（HOOK → SourceCodeAnalysisAgent）

**调用Agent**: `SourceCodeAnalysisAgent`

**分析维度**:

| 维度 | 输出内容 |
|------|---------|
| 代码架构 | 文件结构 + 核心模块职责 + Mermaid数据流 |
| 原理分析 | 算法/数学原理 + 公式 + **源码落点（文件名+行号）** |
| 学习路径 | 阶段一：能运行（30min）→ 阶段二：能理解（60min）→ 阶段三：能改造（30min） |
| 易错清单 | ≥5个：错误现象 + 原因 + 解决方法 |

**输出文件**:
- `source-codes/exp{xx}/code-analysis/code-analysis-report.md`
- `source-codes/exp{xx}/code-analysis/analysis-status.yaml`（status → completed）

#### 4.3 生成实验内容（LabGuideExperimentAgent）

**调用Agent**: `LabGuideExperimentAgent × N`

**输入（来自 HOOK）**:
```yaml
experiment_context:
  id: 6
  name: 基于MediaPipe的人机交互实验
  # ... spec字段

  # ★ 来自HOOK的源码分析
  source_code_analysis:
    report_path: "source-codes/exp6/code-analysis/code-analysis-report.md"
    principles:
      - id: "3.1.1"
        name: "MediaPipe Hands"
        code_location: "hands_tracker.py L30-35"  # ★ 必须有
    common_mistakes:
      - phenomenon: "关键点不显示"
        solution: "降低置信度阈值"
        code_location: "config.py L3"
```

**强制约束**:
- 原理讲解必须引用 `code_location`（源码落点）
- 易错点必须引用 `common_mistakes` 清单
- 学习步骤必须遵循三阶段规划

---

### Step 5: 练测题生成

**调用Agent**: `quiz-agent`

**依赖**: 实验指导书（编程题强制取材于实验内容）

---

### Step 6-8: 审核与整合

- **Step 6**: `content-audit-agent` — 完整性 + 一致性审核
- **Step 7**: `quality-review-agent` — 技术准确性审核
- **Step 8**: `resource-integrator-agent` — 资源整合输出

---

## 三、输出目录结构

```
courses/sheet1/{course_id}/
├── _meta/
│   ├── course-spec.yaml
│   └── generation-log.md
├── {course_id}_knowledge_graph.md
├── {course_id}_syllabus.md
├── {course_id}_lab_guide.md
├── {course_id}_quiz.md
├── README.md
└── source-codes/                      # 源码仓库
    ├── _registry.yaml                    # 源码索引
    ├── exp01/
    │   ├── demo_*.py
    │   ├── requirements.txt
    │   ├── _meta.yaml
    │   └── code-analysis/
    │       ├── code-analysis-report.md
    │       └── analysis-status.yaml
    └── exp02/ ...
```

---

## 四、异常处理

| 错误类型 | 处理 |
|---------|------|
| `missing_code` | 🔴 硬阻塞，要求人工补充源码 |
| `analysis_timeout` | 🔴 硬阻塞，要求检查源码 |
| `analysis_failed` | 🔴 硬阻塞，要求修复源码 |
| `agent_runtime_error` | 重试3次，仍失败则暂停 |
| `quality_reject` | 定向回退，最多2轮，仍失败则人工介入 |

---

## 五、Agent上下文契约

| Agent | 必需读取 |
|-------|---------|
| ResourceParser | input/course_spec.csv（经 spec-parser-skill 解析） |
| KnowledgeGraph | course-spec.yaml |
| Syllabus | course-spec.yaml |
| SourceCodeAnalysis | source-codes/exp{xx}/ 下的源码文件 |
| LabGuideOrchestrator | course-spec + knowledge_graph + _registry.yaml |
| LabGuideExperiment | experiment_context + source_code_analysis |
| Quiz | knowledge_graph + lab_guide |
| ContentAudit | course-spec + 5份产出 |
| QualityReview | 5份产出 + quality-standard.md |
| ResourceIntegrator | 5份产出 + 源码仓库 |
