---
name: course-generation-workflow
description: 端到端课程资源生成工作流 - 从课程信息到完整资源包
trigger: /生成课程、生成课程资源、生成{course_name}
---

# 课程资源生成工作流

本文档定义从课程信息到完整课程资源包的端到端工作流程。

---

## 一、工作流概述

### 1.1 流程图（已优化 v2.0）
```
┌─────────────────────────────────────────────────────────────────┐
│                         启动                                     │
│              用户输入: 生成 {课程名称}                            │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: 资源列表解析（新增）                                     │
│           resource-parser-agent                                  │
│  - 读取 input/course_spec.xlsx                                         │
│  - 生成course-spec.yaml（唯一可信源）                            │
│  - 提取实验项目、学时、技术栈                                     │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: 知识图谱 + 教学大纲 (并行)                               │
│ ┌─────────────────────┐  ┌─────────────────────┐                 │
│ │ knowledge-graph-    │  │   syllabus-agent   │                 │
│ │ agent              │  │                    │                 │
│ │ 基于course-spec    │  │  基于course-spec   │                 │
│ └─────────────────────┘  └─────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: 实验指导书 → 练测题 (串行，依赖关系强制)                 │
│ ┌─────────────────────┐      ┌─────────────────────┐            │
│ │  lab-guide-agent   │  →   │    quiz-agent      │            │
│ │ 基于course-spec    │      │ 基于knowledge-graph│            │
│ │ +knowledge-graph   │      │ +lab_guide(编程题) │            │
│ └─────────────────────┘      └─────────────────────┘            │
│ 注：quiz 编程题取材于实验指导书，故必须在 lab-guide 之后        │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: 内容审核（优化）                                         │
│           content-audit-agent（新增）                            │
│  - 对照资源列表检查完整性                                        │
│  - 检查数据一致性                                                │
│  - 提出专家级补充建议                                            │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: 质量审核                                                 │
│           quality-review-agent                                   │
│           (审核技术准确性)                                       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
              ┌──────────┐                ┌──────────┐
              │ 通过审核  │                │ 未通过   │
              └────┬─────┘                └────┬─────┘
                   │                           │
                   ▼                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: 资源整合输出                                             │
│       resource-integrator-agent                                  │
│       - 整合4个文档                                              │
│       - 生成元数据                                               │
│       - 输出到courses/目录                                       │
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

### Step 1: 资源列表解析（新增）

**调用Agent**: `resource-parser-agent`

**输入**:
```
用户: 生成 ROS机器人实践
```

**操作**:
1. 解析课程名称 → `ROS机器人实践`
2. 匹配课程编号 → `EXP003`
3. **读取 input/course_spec.xlsx**（关键步骤）
4. 解析所有实验项目（8个实验）
5. 识别技术栈（ROS2）
6. 生成course-spec.yaml

**输出**: `courses/sheet1/ros_practice/_meta/course-spec.yaml`
```yaml
course_code: EXP003
course_name: ROS机器人实践
category: sheet1
prerequisites:
  - C++或Python编程
  - Linux系统应用
total_hours: 48
lab_hours: 48
tech_stack: [ROS2]
experiments:
  - id: 1
    name: ROS2系统搭建与节点通信实验
    hours: 6
    tech_stack: [ROS2]
    objectives: [...]
    contents: [...]
  # ... 其余7个实验
```

⚠️ **关键变化**: 不再凭通识知识，必须基于资源列表

---

### Step 2: 并行生成 - 知识图谱 + 教学大纲

**并行执行**:
```
Agent 1: knowledge-graph-agent（必须读取course-spec.yaml）
Agent 2: syllabus-agent（必须读取course-spec.yaml）
```

**强制约束**:
- ✅ 必须基于course-spec.yaml生成
- ✅ 知识图谱必须覆盖所有实验
- ✅ 总学时必须=course-spec.total_hours
- ❌ 禁止凭通识知识生成

**调用Skills**:
- `.claude/skills/embodied-ai-domain/`
- `.claude/skills/course-design-expert/`

**输出文件**:
- `knowledge_graph.md` - 三级知识结构
- `syllabus.md` - 教学大纲

**预计耗时**: 2-3分钟

---

### Step 3: 串行生成 - 实验指导书 → 练测题

**执行顺序（强制串行）**:
```
1. lab-guide-agent (先执行)
2. quiz-agent (后执行)
```

**依赖**:
- 依赖 Step 2 的产出（知识图谱 + 大纲）
- **quiz-agent 额外依赖 lab-guide-agent 的产出**：编程题强制取材于实验指导书的实际实验任务（相同 API/硬件接口），单选/多选/简答可参考实验原理解释。因此 quiz 不可与 lab-guide 并行。

**输出文件**:
- `lab_guide.md` - 实验指导书
- `quiz.md` - 练测题库

**预计耗时**: 3-5分钟

---

### Step 4: 内容审核（新增）

**调用Agent**: `content-audit-agent`

**审核维度**:
1. **完整性审核**：
   - 实验数量≥资源列表要求
   - 总学时=资源列表要求
   - 技术栈覆盖率≥95%

2. **数据一致性审核**：
   - 学时数据在所有文档中一致
   - 练测题数量统计准确
   - 知识点编号无重复

3. **专家补充建议**：
   - 基于行业前沿提出补充内容
   - 标注优先级和理由

**输出**: `content-audit-report.md`

---

### Step 5: 质量审核

**调用Agent**: `quality-review-agent`

**审核维度**:
| 维度 | 权重 |
|------|------|
| 准确性 | 40% |
| 可操作性 | 30% |
| 规范性 | 30% |

**评级标准**:
| 评级 | 说明 | 行动 |
|------|------|------|
| A级 | 优秀 | 直接输出 |
| B级 | 良好 | 微调后输出 |
| C级 | 一般 | 返回修改 |
| D级 | 较差 | 重新生成 |

**输出**: `quality-review-report.md`

---

### Step 6: 资源整合输出

**调用Agent**:
```
resource-integrator-agent
```

**操作**:
1. 创建目录结构
2. 移动/重命名文件
3. 生成元数据文件
4. 生成README

**输出目录**:
```
courses/sheet1/ros_practice/
├── _meta/
│   ├── course-info.yaml
│   └── generation-log.md
├── ros_practice_knowledge_graph.md
├── ros_practice_syllabus.md
├── ros_practice_lab_guide.md
├── ros_practice_quiz.md
└── README.md
```

---

## 三、执行时间估算

| 步骤 | Agent | 预计耗时 |
|------|-------|---------|
| Step 1 | resource-parser-agent | 30秒 |
| Step 2 | 2个Agent并行 | 2-3分钟 |
| Step 3 | 2个Agent串行 | 3-5分钟 |
| Step 4 | content-audit-agent | 1分钟 |
| Step 5 | quality-review-agent | 1-2分钟 |
| Step 6 | integrator-agent | 30秒 |
| **总计** | - | **8-12分钟** |

---

## 四、异常处理与恢复

> 设计目标：(1) 错误按类型分级处理，不再统一"重试3次"；(2) 失败可从断点恢复，不重跑已完成步骤；(3) 审核不过时定向回退到具体 Agent，不全量重做。

### 4.1 统一 Agent 返回结构

每个 Sub-Agent 执行后必须返回统一状态，供管家决策（而非把全部产出塞回管家上下文）：

```yaml
agent_result:
  agent: lab-guide-agent
  status: success        # success / warning / error
  error_type: null       # parse_error / agent_runtime_error / consistency_error / quality_reject
  output_file: courses/sheet1/ros_practice/ros_practice_lab_guide.md
  summary: "8个实验，覆盖知识点 1.1.1–4.2.3"
  warnings: []
```

管家只读 `status` / `error_type` / `output_file` / `summary` 做编排，**产出正文留在磁盘**，不回灌管家上下文（见 §六 上下文契约）。

### 4.2 错误分级与处理策略

| 错误类型 | 触发场景 | 处理策略 | 重试 | 人工介入 |
|---------|---------|---------|------|---------|
| `parse_error` | Step1 xlsx 读不了 / 字段缺失 / spec 自校验阻塞 | 🔴 硬停，不进入 Step2 | 否 | **CP-2 强制** |
| `agent_runtime_error` | Agent 超时 / 崩溃 / 写文件失败 | 重试，指数退避 | 最多3次 | 3次后标记 `需人工干预` 并暂停 |
| `consistency_error` | 学时/编号/数量对不上（一致性硬检查） | 定向修复对应 Agent | 自动修复1次 | 再失败转 quality_reject 流程 |
| `quality_reject` | Step5 评级 C/D | 带缺陷清单定向回退 | 最多2轮 | 2轮仍 C/D → **CP-3 强制** |

```yaml
retry_policy:
  agent_runtime_error: { max_attempts: 3, delay_seconds: 2, backoff: exponential }
  consistency_error:   { max_attempts: 1, then: directed_rollback }
  quality_reject:      { max_rounds: 2, then: checkpoint_CP3 }
  parse_error:         { max_attempts: 0, then: checkpoint_CP2 }
```

**关键原则**：任何错误在重试/回退耗尽后，**绝不静默输出低质内容**，一律暂停 + 写 run-state 留痕，交人工。

### 4.3 定向回退（审核不过时）

ContentAuditAgent / QualityReviewAgent 输出**结构化缺陷清单**（见各 Agent 的 `failed_items`），管家按 `target_agent` 只触发对应 Agent 的局部重做，并把 `issue` 作为输入上下文传入。未被点名的 Agent 不动。

```yaml
# 审核返回示例
review_result:
  grade: C
  failed_items:
    - target_agent: KnowledgeGraphAgent
      issue: "知识点 3.2.1 描述超过50字"
      severity: 🟡
    - target_agent: QuizAgent
      issue: "题库引用了不存在的知识点 4.1.1"
      severity: 🔴
```

回退路径（对照流程图 C/D 级返回箭头）：

```
quality_reject(C/D)
   └─ 解析 failed_items
        ├─ 仅 KnowledgeGraph/Syllabus 缺陷 → 回退 Step2 对应 Agent → 重跑 Step3(因依赖)
        ├─ 仅 LabGuide 缺陷            → 回退 lab-guide → 重跑 quiz(因依赖)
        ├─ 仅 Quiz 缺陷               → 仅回退 quiz
        └─ 重新执行 Step4/Step5 审核
   └─ 满 2 轮仍 C/D → CP-3 人工裁决
```

### 4.4 断点恢复（run-state 检查点）

每门课程在 `_meta/run-state.yaml` 维护断点，每步完成即落盘。中断/失败后重新触发该课程，从最后一个 `done` 步骤的下一步继续，已完成步骤不重跑。

```yaml
# courses/{sheet}/{course_id}/_meta/run-state.yaml
course_code: EXP003
workflow_version: v2.1
updated_at: 2026-06-13T10:30:00
current_step: Step3
status: in_progress      # in_progress / blocked / done / failed
steps:
  Step1_parse:        { status: done,    output: _meta/course-spec.yaml }
  Step2a_kg:          { status: done,    output: ros_practice_knowledge_graph.md }
  Step2b_syllabus:    { status: done,    output: ros_practice_syllabus.md }
  Step3a_lab:         { status: done,    output: ros_practice_lab_guide.md }
  Step3b_quiz:        { status: failed,  error_type: agent_runtime_error, attempts: 2 }
  Step4_audit:        { status: pending }
  Step5_quality:      { status: pending }
  Step6_integrate:    { status: pending }
rollback_rounds: 0
```

**恢复规则**：
- `status: blocked` → 等人工解除（通常是 CP-2 spec 问题），人工修正后从 Step1 重验。
- 某步 `failed` 且重试未耗尽 → 从该步重试。
- 定向回退会把目标步骤及其下游依赖步骤重置为 `pending`，其余保持 `done`。

### 4.5 人工检查点（CP）

| 检查点 | 位置 | 类型 | 触发条件 | 批量生成时 |
|-------|------|------|---------|-----------|
| **CP-1** spec 确认 | Step1 之后 | 可选 | 解析成功后，由人确认 spec 符合预期再开始昂贵生成 | 默认**关闭**（避免频繁打断） |
| **CP-2** 解析失败 | Step1 失败 | **强制阻塞** | xlsx 读不了 / 字段缺失 / spec 自校验阻塞 | 强制保留，跳过该课程继续其余 |
| **CP-3** 质量兜底 | Step5 之后 | **强制阻塞** | 定向回退满2轮仍为 C/D 级 | 强制保留，该课程挂起待人工 |

- **单门课**：建议开启 CP-1，生成前先让人过一眼 spec。
- **批量生成**（生成Sheet1全部）：默认仅保留 CP-2 / CP-3 两个强制阻塞点；遇阻塞课程**跳过并继续**其余课程，最后汇总 `BLOCKED` 清单交人工，不中断整批。

### 4.6 挂起 / 阻塞后的留痕

进入 CP-2 / CP-3 或重试耗尽时，必须：
1. 将 run-state `status` 置为 `blocked` / `failed`，写明 `error_type` 与详情；
2. 在 `.claude/memory/generation-progress.md` 对应课程行标记 ⚠️/❌ 并备注卡点步骤；
3. 输出给用户：卡在哪一步、为什么、人工需要做什么。

---

## 五、使用示例

### 示例1: 生成单门课程
```
用户: 生成 ROS机器人实践

系统:
1. ✅ 识别课程: EXP003 ROS机器人实践 (sheet1)
2. 🔄 启动并行任务...
   - knowledge-graph-agent: 执行中...
   - syllabus-agent: 执行中...
3. 🔄 串行生成...
   - lab-guide-agent: 执行中...
   - quiz-agent: 执行中...
4. 🔄 质量审核中...
5. 🔄 资源整合中...

✅ 完成！

📦 课程资源包已生成:
   courses/sheet1/ros_practice/

📄 产出清单:
├── ros_practice_knowledge_graph.md (知识图谱)
├── ros_practice_syllabus.md (教学大纲)
├── ros_practice_lab_guide.md (实验指导书)
└── ros_practice_quiz.md (练测题库)
```

### 示例2: 批量生成
```
用户: 生成Sheet1全部课程

系统:
1. ✅ 识别任务: 批量生成Sheet1的7门课程
2. 🔄 按顺序生成...
   [1/7] 计算机视觉实践 - ✅
   [2/7] 语音交互实践 - ✅
   [3/7] ROS机器人实践 - ✅
   ...

✅ 全部完成！7门课程已生成。
```

---

## 六、上下文依赖

### 激活的Memory
- `.claude/memory/course-scope-memory.md` - 课程规格数据（新增）
- `.claude/memory/course-knowledge-base.md` - 课程知识库
- `.claude/memory/generation-progress.md` - 生成进度

### 激活的Rules
- `.claude/rules/source-constraint-rule.md` - 源数据约束（新增）
- `.claude/rules/data-consistency-rule.md` - 数据一致性（新增）
- `.claude/rules/naming-convention.md` - 命名规范
- `.claude/rules/output-format.md` - 输出格式
- `.claude/rules/quality-standard.md` - 质量标准

### 激活的Skills
- `.claude/skills/embodied-ai-domain/` - 领域知识
- `.claude/skills/course-design-expert/` - 教学设计
- `.claude/skills/knowledge-graph-drawing/` - 图谱绘制

---

## 六之二、Agent 上下文契约（防上下文膨胀/压缩）

> 问题：若管家把每个子 Agent 的完整产出（动辄数千行 Markdown）都收进自己的上下文，多步之后上下文会被压缩，导致编排决策出错、引用丢失。

### 设计原则

1. **磁盘是唯一交接介质**：子 Agent 产出写入文件，管家与下游 Agent 通过**文件路径**交接，不传正文。
2. **管家只持有摘要**：管家上下文里每个 Agent 只保留 `agent_result`（status / 路径 / 一行 summary），不保留产出全文。
3. **子 Agent 按需读取最小输入**：每个子 Agent 启动时只读它声明的必需输入文件，不继承管家的完整历史。

### 各 Agent 输入契约（最小必要集）

| Agent | 必需读取 | 不需要读取 |
|-------|---------|-----------|
| ResourceParser | xlsx | 其他文档 |
| KnowledgeGraph | course-spec.yaml | 大纲/实验/题库 |
| Syllabus | course-spec.yaml | 实验/题库 |
| LabGuide | course-spec.yaml + knowledge_graph.md + hardware-platform-spec.md | 大纲/题库 |
| Quiz | knowledge_graph.md + lab_guide.md（编程题）| course-spec 全文（只需知识点编号） |
| ContentAudit | course-spec.yaml + 4份产出 | — |
| QualityReview | 4份产出 + quality-standard.md | xlsx |
| ResourceIntegrator | 4份产出 + 审核报告 | xlsx |

### 批量生成的上下文隔离

- 每门课程是**独立的编排单元**，完成后管家**清理该课程的中间摘要**，只在 `generation-progress.md` 留一行状态后再开始下一门。
- 跨课程共享的只有 Memory（硬件规格、知识库、进度），不跨课程携带产出正文。这样批量生成 11 门课程时，管家上下文不会随课程数线性膨胀。

---

## 七、更新日志
| 日期 | 更新内容 |
|------|---------|
| 2026-06-13 | v2.1 工程化优化：错误分级处理+断点恢复(run-state)+定向回退+人工检查点CP-1/2/3；Step1后spec自校验fail-fast；quiz串行依赖lab-guide；新增Agent上下文契约防膨胀 |
| 2026-06-11 | v2.0 优化版本：新增ResourceParserAgent和ContentAuditAgent，强制基于资源列表生成 |
| 2026-06-11 | v1.0 初始版本 |
