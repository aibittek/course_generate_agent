# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is **not a software project** — it is a content-generation pipeline for an Embodied AI (具身智能) curriculum. The "executable" components are Claude Code sub-agents, rules, memory, and skills under `.claude/`. The "build artifacts" are Markdown course documents under `courses/`. There is no compile, lint, or test step.

## Primary workflow

End-to-end course resource generation is triggered by a natural-language prompt:

```
生成 {课程名称}          # e.g. 生成 ROS机器人实践
生成课程 {编号} {名称}    # e.g. 生成课程 EXP003 ROS机器人实践
生成Sheet1全部课程        # batch
```

This invokes the orchestrator (`.claude/agents/course-resource-orchestrator.md`) which runs the pipeline defined in `.claude/workflows/course-generation-workflow.md`:

```
ResourceParserAgent        →  reads xlsx, writes course-spec.yaml (Step 1)
KnowledgeGraphAgent ║ SyllabusAgent       (parallel, Step 2)
LabGuideAgent  →  QuizAgent               (serial,   Step 3)
ContentAuditAgent          →  completeness vs. xlsx (Step 4)
QualityReviewAgent         →  A/B/C/D grade         (Step 5)
ResourceIntegratorAgent    →  final package         (Step 6)
```

Each course produces four core documents plus metadata under `courses/{sheet1|sheet2}/{course_id}/`:
- `{id}_knowledge_graph.md` — three-level knowledge structure (chapter → section → knowledge point)
- `{id}_syllabus.md` — teaching syllabus
- `{id}_lab_guide.md` — lab manual
- `{id}_quiz.md` — quiz/exam bank
- `_meta/course-spec.yaml` — the canonical course spec (see "Single source of truth" below)

## Single source of truth — non-negotiable

`具身智能人培方案SOP/课程逻辑/资源开发列表.xlsx` is the **only** authoritative source for course content. The constraint is enforced by `.claude/rules/source-constraint-rule.md`:

1. Never generate course content from generic knowledge before the xlsx has been parsed.
2. `ResourceParserAgent` must run first; it produces `_meta/course-spec.yaml`.
3. All downstream agents (knowledge-graph, syllabus, lab-guide, quiz) read `course-spec.yaml` and must respect its `experiments[]`, `total_hours`, `tech_stack`, and `prerequisites`.
4. Experts may *add* frontier content (e.g. YOLOv8) but must label it `专家建议` with a reason — they may not *reduce* what the xlsx specifies.
5. `ContentAuditAgent` re-checks generated output against the xlsx; mismatches block the pipeline.

If a user asks to generate or edit course content without referencing the xlsx, route them through the parser first.

## Course catalog

11 courses — IDs and identifiers are fixed by `.claude/rules/naming-convention.md`:

| ID | Course | Sheet | Folder | Hours | Labs |
|---|---|---|---|---|---|
| EXP001 | 计算机视觉实践 | sheet1 | `cv_practice` | 52h | 14 |
| EXP002 | 语音交互实践 | sheet1 | `speech_practice` | 32h | 7 |
| EXP003 | ROS机器人实践 | sheet1 | `ros_practice` | 48h | 8 |
| EXP004 | SLAM机器人实践 | sheet1 | `slam_practice` | 48h | 7 |
| EXP005 | 机械臂应用开发实践 | sheet1 | `arm_practice` | 32h | 8 |
| EXP006 | 大模型交互实践 | sheet1 | `llm_practice` | 48h | 11 |
| EXP007 | 综合实训实践 | sheet1 | `training` | 96h | 3 |
| IND001 | 物料分拣应用场景 | sheet2 | `sorting_scene` | 32h | — |
| IND002 | 柔性制造应用场景 | sheet2 | `manufacturing_scene` | 32h | — |
| IND003 | 家庭整理应用场景 | sheet2 | `home_scene` | 32h | — |
| IND004 | 室内巡检应用场景 | sheet2 | `inspection_scene` | 32h | — |

Folder names are lowercase, snake_case, ≤20 chars. Document filenames follow `{folder}_{type}.md`. **No Chinese characters, spaces, or mixed case in filenames.**

Current generation status lives in `.claude/memory/generation-progress.md` — keep it current after producing or revising a course.

## Hardware target

Course content (especially lab guides) targets two iFlytek (科大讯飞) platforms whose specs live in `.claude/memory/hardware-platform-spec.md`:
- **B2 实验箱** (`XFLZ_EAI_B2_PRO`) — RK3576 + STM32F407, Ubuntu 22.04 + ROS2, 6DOF arm, depth camera, lidar, 6-mic array
- **C1 机器人小车** (`XFLZ_EAI_CAR1`) — same SoC stack, mobile platform with arm

Lab content must align with the actual capabilities in this file — do not invent sensors, motors, or interfaces it does not list.

## Cross-document consistency rules

`.claude/rules/data-consistency-rule.md` defines hard checks every set of generated docs must pass. The recurring failure modes are:

- **Hour totals**: `course-spec.total_hours == knowledge_graph total == syllabus total == lab_guide total`. Discrepancy is 🔴 high-severity.
- **Lab counts**: `course-spec.experiments` count == syllabus lab table == lab_guide section count.
- **Quiz totals**: stated total == single + multi + short + programming counts. The quiz target counts per course are fixed in `.claude/rules/quality-standard.md` §4.1.
- **Knowledge-point IDs**: format `X.X.X`, globally unique, no gaps. Quiz/lab references must resolve to a real ID in the knowledge graph.

When editing one document, run the corresponding check on the others or call `ContentAuditAgent`.

## Versioning

`.claude/rules/version-control.md` governs version bumps:
- `v0.x` — drafts (any minor fix bumps minor version)
- `v1.0` — first human-reviewed release
- Major bump (`v2.0`) only on structural changes (chapters added/removed, scope shifts)

Each document carries a YAML front-matter `version` field plus a `## 更新日志` table. Historical versions are archived as `{name}_v{version}.md`. The `cv_practice` folder currently contains `v3` artifacts — preserve the `_vN` suffix when iterating.

## Output formatting

`.claude/rules/output-format.md` is strict about Markdown style. Notable points:
- Code fences must declare a language (` ```python `, ` ```yaml `, etc.).
- Allowed emoji are limited to ✅ ❌ ⚠️ 🔴 🟡 🟢 ⭐ ⏳ 🔄 — do not introduce others.
- Heading levels must not skip (no `#` jumping straight to `###`).
- Tables and code blocks need a blank line before and after.

`.claude/rules/content-accuracy.md` additionally forbids ROS1-specific APIs in ROS2 contexts (e.g. use `rclpy.node.Node`, not `rospy.Subscriber`) and exaggerated specs.

## Working with the .xlsx and .docx sources

Source materials under `具身智能人培方案SOP/` are binary Office files. The path contains Chinese characters, which breaks some shell tools on this Windows/Git-Bash environment — prefer the `Read`/`Glob` tools over `ls`/`cat`. To extract text from `.docx`, the project uses a Python `read_docx.py` script invoked via `python` (paths permitted in `.claude/settings.local.json`). The xlsx parsing happens inside `ResourceParserAgent`; do not attempt to re-parse it ad hoc — let the agent produce `course-spec.yaml` and read that instead.

## Language

User-facing content (course documents, agent dialogue, audit reports) is written in **Simplified Chinese**. Internal identifiers (folder names, YAML keys, agent names) are English snake_case.
