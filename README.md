# 具身智能课程资源生成系统

> 基于 Claude Code Multi-Agent 的课程资源自动化生成框架

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-latest-purple)](https://claude.ai/code)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 📖 项目简介

本项目是一套面向具身智能（Embodied AI）教育场景的课程资源生成系统，通过 Claude Code 多 Agent 协作，实现从课程规格表（CSV）到完整教学文档（知识图谱、教学大纲、实验指导书、练测题库）的全自动化生成。

**核心特性**：
- ✅ **CSV 唯一可信源**：input/course_spec.csv 作为所有课程内容的权威来源
- ✅ **8 步标准化流程**：规格解析 → 知识图谱 / 大纲 → 实验指导书 → 练测题 → 审核 → 整合
- ✅ **源码强制 HOOK**：实验指导书生成前，必须先完成源码分析（PreToolUse Hook 强制门控）
- ✅ **增量更新支持**：CSV 变更自动检测（Git Hook），定向更新受影响文档
- ✅ **多课程并行**：11 门课程（EXP001-007 核心实验 + IND001-004 行业应用）独立生成

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│  唯一可信源：input/course_spec.csv (11 门课程 / 61 实验)      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: ResourceParserAgent                                  │
│   触发 spec-parser-skill (Python 固定解析器)                  │
│   → courses/{sheet}/{folder}/_meta/course-spec.yaml          │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
┌─────────────────────┐                 ┌─────────────────────┐
│ KnowledgeGraphAgent │                 │   SyllabusAgent    │
│  (并行)             │                 │   (并行)           │
└─────────────────────┘                 └─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: LabGuideOrchestratorAgent                            │
│   源码仓库初始化 → source-codes/_registry.yaml               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: 实验生成循环（带源码 HOOK 强制门控）                   │
│   for each experiment:                                       │
│     ├─ HOOK: 检查 analysis-status.yaml                       │
│     ├─ pending → 触发 SourceCodeAnalysisAgent                │
│     ├─ missing → 🔴 硬阻塞（exit 2）                          │
│     └─ completed → LabGuideExperimentAgent 生成实验内容       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5-8: QuizAgent → ContentAudit → QualityReview          │
│           → ResourceIntegratorAgent                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 输出：courses/{sheet}/{folder}/                               │
│   ├── {folder}_knowledge_graph.md                            │
│   ├── {folder}_syllabus.md                                   │
│   ├── {folder}_lab_guide.md                                  │
│   ├── {folder}_quiz.md                                       │
│   └── _meta/course-spec.yaml + generation-log.md             │
└─────────────────────────────────────────────────────────────┘
```

> 完整架构图见 [Agent工作流架构图.html](Agent工作流架构图.html)

---

## 🛠 环境要求

### 必需依赖

| 软件/工具 | 版本要求 | 说明 |
|----------|---------|------|
| **Claude Code** | latest | Anthropic 官方 CLI 工具 |
| **Python** | ≥ 3.10.9 | 用于 spec-parser-skill 等固定解析器 |
| **Git** | ≥ 2.30 | 用于 Git Hooks（csv 漂移检测） |
| **Bash** | ≥ 4.0 | Git Hooks 执行环境（Windows 使用 Git Bash） |
| **PowerShell** | ≥ 5.1 | PreToolUse Hooks 执行环境（Windows） |

### Python 依赖包

```bash
pip install pyyaml>=6.0 pandas>=1.5.3 openpyxl>=3.0.10
```

或使用 `requirements.txt`（如存在）：
```bash
pip install -r requirements.txt
```

---

## 🚀 快速开始

### 1. 环境搭建

#### 安装 Claude Code

访问 [claude.ai/code](https://claude.ai/code) 下载并安装最新版本。

#### 克隆项目

```bash
git clone <repository_url>
cd course_generate_agent
```

#### 安装 Python 依赖

```bash
pip install pyyaml pandas openpyxl
```

#### 安装 Git Hooks

```bash
bash .githooks/install.sh
```

验证安装：
```bash
git config core.hooksPath
# 应输出：.githooks
```

---

### 2. 操作案例

#### 📦 案例 1：生成单门课程（首次生成）

在 Claude Code 对话框中输入自然语言指令：

```
生成 ROS机器人实践
```

或使用课程编号：

```
生成课程 EXP003 ROS机器人实践
```

**执行流程**：
1. CourseResourceOrchestrator 自动启动
2. ResourceParserAgent 解析 `input/course_spec.csv` → 生成 `course-spec.yaml`
3. 并行生成知识图谱 + 教学大纲
4. 初始化源码仓库（扫描 `source-codes/` 目录）
5. 循环生成每个实验（带源码 HOOK 检查）
6. 生成练测题库
7. 内容审核 + 质量评审
8. 资源整合 → 输出到 `courses/sheet1/ros_practice/`

**预期输出**：
```
✅ 课程资源生成完成！

课程名称: ROS机器人实践
生成时间: 2026-06-23 18:30:00
资源包路径: courses/sheet1/ros_practice/

产出清单:
├── 知识图谱: ros_practice_knowledge_graph.md
├── 教学大纲: ros_practice_syllabus.md
├── 实验指导书: ros_practice_lab_guide.md
└── 练测题库: ros_practice_quiz.md
```

---

#### 📦 案例 2：批量生成全部课程

```
生成Sheet1全部课程
```

或生成全部 11 门课程：

```
生成全部11门课程
```

**执行流程**：
```python
for course_id in [EXP001, EXP002, EXP003, EXP004, EXP005, EXP006, EXP007,
                  IND001, IND002, IND003, IND004]:
    1. python parser.py --course {course_id}  # 必须传 --course 参数
    2. 并行: KnowledgeGraph + Syllabus
    3-8. 依次执行完整流程...
    每门完成后更新 generation-progress.md
```

**注意事项**：
- 每门课程独立执行完整 8 步流程
- 跨课程只共享 Memory，不携带产出正文（防止上下文膨胀）
- 预计总耗时：约 3-5 小时（取决于实验数量与源码复杂度）

---

#### 🔄 案例 3：增量更新（CSV 变更后同步）

**场景**：修改了 `input/course_spec.csv` 中某门课程的实验学时/内容。

**Step 1: CSV 变更检测**

```bash
# 修改 csv 后，Git Hook 自动检测（或手动触发）
bash .githooks/post-checkout HEAD HEAD 1
```

**输出示例**：
```
[csv-drift] 检测到 1 份课程的 spec 与 csv 不一致：
  - courses/sheet1/cv_practice/_meta/course-spec.yaml (EXP001)

  方案 A — 仅重新生成 spec.yaml（轻，逐课程）
    python .claude/skills/spec-parser-skill/diff.py --course EXP001 --format text
    python .claude/skills/spec-parser-skill/parser.py --course EXP001

  方案 B — 同步下游文档（推荐）
    /incremental-update --course EXP001 --from-csv
```

**Step 2: 查看变更详情**

```bash
python .claude/skills/spec-parser-skill/diff.py --course EXP001 --format text
```

**输出示例**：
```
[DIFF] 课程字段变更 0 项 / 实验 +0 -0 ~1
--- 修改实验 ---
  ~4: 变更字段 [hours]
--- 级联更新提示（需修改文档） ---
  lab_guide:
    - 实验4 学时变化 → 实验头部学时字段同步
  syllabus:
    - 实验4 学时变化 → 更新学时分配
```

**Step 3: 触发增量更新**

在 Claude Code 对话框中：

```
我改了 csv，请同步 计算机视觉实践
```

或使用命令：

```
/incremental-update --course EXP001 --from-csv
```

**执行流程**：
1. IncrementalUpdateAgent 读取 diff.py 输出
2. 按 cascade_hints 拆分子任务：
   - `hours` 字段变化 → 仅同步 syllabus 学时表 + lab_guide 实验头
   - `source_code_path` 变化 → 必须重跑源码分析 + 重写实验段
3. 定向更新受影响文档（其余保持原样）
4. 触发 ContentAuditAgent 全量校验

**关键设计**：
- **字段级粒度**：仅改 `hours` 不必重跑源码分析；改 `source_code_path` 则必须重跑 HOOK
- **定向回放**：避免全流程重做，节省时间（预计耗时：5-15 分钟 vs 全量 30-60 分钟）

---

## 📂 目录结构

```
course_generate_agent/
├── .claude/                          # Claude Code 配置目录
│   ├── agents/                       # 8 个 Sub-Agent 定义
│   │   ├── course-resource-orchestrator.md    # 主控 Agent
│   │   ├── knowledge-graph-agent.md
│   │   ├── syllabus-agent.md
│   │   ├── lab-guide-orchestrator-agent.md
│   │   ├── lab-guide-experiment-agent.md
│   │   ├── source-code-analysis-agent.md
│   │   ├── quiz-agent.md
│   │   ├── content-audit-agent.md
│   │   ├── quality-review-agent.md
│   │   ├── resource-integrator-agent.md
│   │   └── incremental-update-agent.md
│   ├── hooks/                        # PreToolUse Hooks
│   │   ├── enforce-source-hook.ps1            # Task 门控（源码前置）
│   │   └── enforce-source-on-edit.ps1         # Edit/Write 门控
│   ├── memory/                       # 持久化记忆
│   │   ├── course-knowledge-base.md           # 11 门课程目录
│   │   ├── hardware-platform-spec.md          # B2 实验箱 / C1 小车
│   │   └── generation-progress.md             # 生成状态追踪
│   ├── rules/                        # 约束规则
│   │   ├── source-constraint-rule.md          # CSV 唯一可信源
│   │   ├── data-consistency-rule.md           # 数据一致性
│   │   ├── naming-convention.md               # 命名规范
│   │   ├── quality-standard.md                # 质量标准
│   │   └── content-accuracy.md                # 内容准确性
│   ├── skills/                       # 可复用技能
│   │   ├── spec-parser-skill/                 # CSV 解析器（Python）
│   │   │   ├── parser.py                      # 解析 csv → yaml
│   │   │   ├── validator.py                   # 校验 yaml
│   │   │   ├── diff.py                        # 计算 csv ↔ yaml 差异
│   │   │   └── schema.yaml                    # 字段定义
│   │   └── source-code-hook-skill/            # 源码 HOOK 检查
│   ├── workflows/                    # 工作流定义
│   │   └── course-generation-workflow.md      # 8 步标准流程
│   └── settings.json                 # Claude Code 配置（含 Hook 注册）
├── .githooks/                        # Git Hooks（csv 漂移检测）
│   ├── post-checkout                 # 切换分支后检测
│   ├── post-merge                    # 合并后检测
│   ├── pre-commit                    # 提交前检测
│   ├── _lib_csv_drift.sh             # 共享检测逻辑
│   └── install.sh                    # Hook 安装脚本
├── input/                            # 输入数据
│   └── course_spec.csv               # ⚠️ 唯一可信源（11 门课程规格表）
├── courses/                          # 输出目录
│   ├── sheet1/                       # 核心实验室（EXP001-007）
│   │   ├── cv_practice/              # 计算机视觉实践
│   │   ├── speech_practice/          # 语音交互实践
│   │   ├── ros_practice/             # ROS机器人实践
│   │   ├── slam_practice/            # SLAM机器人实践
│   │   ├── arm_practice/             # 机械臂应用开发实践
│   │   ├── llm_practice/             # 大模型交互实践
│   │   └── training/                 # 综合实训实践
│   └── sheet2/                       # 行业创新应用（IND001-004）
│       ├── sorting_scene/            # 物料分拣应用场景
│       ├── manufacturing_scene/      # 柔性制造应用场景
│       ├── home_scene/               # 家庭整理应用场景
│       └── inspection_scene/         # 室内巡检应用场景
├── Agent工作流架构图.html             # 可视化架构图（v3.0）
├── CLAUDE.md                         # 项目说明（给 Claude Code）
└── README.md                         # 本文档
```

---

## ⚙️ 核心机制

### 1. CSV 唯一可信源（硬约束）

**规则**（`.claude/rules/source-constraint-rule.md`）：
- ❌ 禁止未读取 csv 就直接生成内容
- ❌ 禁止随意减少实验数量或学时
- ❌ 禁止自行臆造实验内容
- ✅ 必须先调用 `ResourceParserAgent` 解析 csv → `course-spec.yaml`
- ✅ 所有下游 Agent 读取 `course-spec.yaml` 作为输入

**校验机制**：
- `ContentAuditAgent` 反查 csv，检测实验数/学时/技术栈是否一致
- 不一致 → 🔴 不通过，必须重做

### 2. 源码强制 HOOK（硬门控）

**问题**：如何确保实验指导书的实验内容生成前，必须先分析用户提供的源码？

**解决方案**：
- **PreToolUse Hook**（`.claude/hooks/enforce-source-hook.ps1`）拦截 `TaskCreate` 工具
- **PreToolUse Hook**（`.claude/hooks/enforce-source-on-edit.ps1`）拦截 `Edit/Write/MultiEdit` 工具
- 读取 `source-codes/_registry.yaml` + `code-analysis/analysis-status.yaml`
- 状态决策：
  - ✅ `completed` → 直接生成
  - ⚡ `pending` → 触发 SourceCodeAnalysisAgent
  - ⏳ `analyzing` → 轮询等待
  - 🔴 `missing` → 硬阻塞（exit 2），要求人工补码

### 3. 增量更新（字段级粒度）

**触发条件**：
- 用户修改 `input/course_spec.csv`
- Git Hook 检测到 csv ↔ yaml 漂移（exit 1）

**执行流程**：
1. `diff.py` 计算差异 → 输出 JSON（含 `cascade_hints`）
2. `IncrementalUpdateAgent` 按字段类型决策回放范围：
   - `hours` 变 → 仅同步学时表
   - `source_code_path` 变 → 重跑源码 HOOK
   - `objectives/exp_content` 变 → 重写实验段
3. 定向更新受影响文档，其余保持原样

**关键价值**：避免全流程重做，节省 80% 时间。

---

## 🔧 常见问题

### Q1: Git Hook 提示 "csv 与 yaml 不一致"？

**原因**：修改了 `input/course_spec.csv` 但未重新生成 `course-spec.yaml`。

**解决**：
```bash
# 查看变更详情
python .claude/skills/spec-parser-skill/diff.py --course <COURSE_ID> --format text

# 重新生成 spec.yaml
python .claude/skills/spec-parser-skill/parser.py --course <COURSE_ID>

# 或使用增量更新
/incremental-update --course <COURSE_ID> --from-csv
```

### Q2: 生成实验指导书时被 HOOK 阻塞？

**错误示例**：
```
[BLOCK] EXP001 实验4 尚未完成源码分析
  状态: missing
  路径: courses/sheet1/cv_practice/source-codes/exp04/
  → 请补充源码后重新运行
```

**解决**：
1. 确认源码已放置在 `source-codes/exp04/` 目录
2. 在 `source-codes/_registry.yaml` 中注册该实验
3. 触发 `SourceCodeAnalysisAgent` 生成分析报告
4. 验证 `analysis-status.yaml` 状态为 `completed`

### Q3: 如何跳过源码 HOOK（调试用）？

**不推荐**，但可临时禁用：
```bash
# 编辑 .claude/settings.json，注释掉 PreToolUse hooks
# 或修改 enforce-source-hook.ps1 逻辑（添加 --skip-hook 参数）
```

**恢复后记得重新启用！**

---

## 📊 质量标准

### 知识图谱
- 章节数 ≥ 3 章
- 每章节数 ≥ 3 节
- 总知识点数 ≥ 20 个
- 类型分布：概念 40% / 原理 30% / 流程 20% / 事实 10%

### 教学大纲
- 知识/能力/素养 三维目标各 ≥ 3 条
- 学时分配总和 = 课程总学时
- 理论:实验建议 4:6 或 5:5

### 实验指导书
- 9 段结构完整（关联知识点/目标/环境/难度/现象/步骤/注意/总结/报告）
- 每个核心步骤有「知识点讲解」（≥80 字）
- 算法步骤必须给公式/数学说明

### 练测题库
- 知识点覆盖率 ≥ 90%
- 难度分布：容易 50% / 中等 30% / 困难 20%
- 编程题必须取材于实验指导书

---

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v3.0 | 2026-06-23 | 多课程 CSV 支持（parser/validator/diff 必须传 `--course` 参数） |
| v2.1 | 2026-06-13 | 新增 IncrementalUpdateAgent（CSV 驱动增量更新） |
| v2.0 | 2026-06-12 | 新增源码 HOOK 强制门控（PreToolUse Hooks） |
| v1.0 | 2026-06-11 | 初始版本，8 步标准流程 |

---

## 📜 许可证

MIT License

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📧 联系方式

如有问题或建议，请提交 [Issue](../../issues)。

---

**Made with ❤️ by Claude Code Multi-Agent System**
