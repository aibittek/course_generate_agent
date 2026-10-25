# AGENTS.md — 代理工作约定

本文件供 AI 编码代理 / 生成器在进入本项目时自动读取。若工具链只读取一个约定文件，以本文件为准；跨会话恢复细节见 `CONTEXT.md`。

## 项目一句话

本仓库是具身智能课程的内容生成与网页化输出项目：Markdown 课程源文档在 `courses/`，生成的网页课程包在 `training/output/`，两者是“源 → 产物”关系，方向不可逆。

## 不可违反的路由约束

1. 所有新建产物写入目标必须先经用户确认，不得自行推断落点。
2. 默认写入边界是 `training/output/`，不要改动 `training/output/` 之外的任何已有文件（含仓库根目录既有文件）。
3. `courses/sheet1/*/` 及 `courses_archive/` 内的 `.md` 是既有文档，只读不改；如需修订必须获得用户显式批准。
4. `training/output/courses/` 下已有的 `index.html` 与各 `exp-*/index.html` 实验页是既有资产，默认只读；如需覆盖必须获得用户显式批准。

## 源与产物

- 源（source of truth，只读）：
  - `courses/sheet1/ros_practice/EXP003_syllabus.md`、`EXP003_lab_guide.md`、`EXP003_knowledge_graph.md`、`EXP003_quiz.md`、`EXP003_README.md`
  - 参考案例源码：`courses_archive/robot_vision/source-codes/`（按 `exp{n}` 目录组织）
- 产物（可写边界）：`training/output/`
  - 静态站点根：`training/output/courses/`
  - 站首页：`training/output/courses/index.html`
  - 目录：`core/`、`cases/`、`industry/`、`renpei/`、`genome/`、`device/`、`quiz/`、`tools/`、`products/`

## 命名约定（与 `training/naming-conventions.md` 一致）

- 实验目录：`exp-NN-slug`，两位数字，短横线小写（如 `exp-05-node`）。
- 实验页：目录内 `index.html`。
- 衍生文档：`{exp-dir}` 前缀 + 角色后缀，如 `exp-05-node-guide.md`、`exp-05-node-solution.md`。
- 全项目文件名禁止中文、空格、大写混排；文档正文用简体中文，标识符用英文 snake_case。

## 完成一轮后必须做

- 核对产物是否落在 `training/output/` 边界内。
- 如产生了新的目录 / 文件约定，更新 `CONTEXT.md` 对应字段后再结束。