# CONTEXT.md — 跨会话上下文恢复档案

重启会话时先读本文件，再读 `AGENTS.md`。字段如与实际不符，以实际路径为准并回写修正。

## 元字段

- updated: 2026-10-25
- scope: 具身智能课程生成项目 · 核心课程网页化
- boundary: training/output/

## 课程元数据（每门课程一行）

| course_id | category | course_dir(source) | output_dir | hours | experiments | hardware |
|---|---|---|---|---|---|---|
| exp003 | core | courses/sheet1/ros_practice | training/output/courses/core/exp003-ros2-application | 48 | 7 | B2+C1 |
| exp001 | core | courses/sheet1/cv_practice | training/output/courses/core/exp001-robot-vision | 48 | 12 | B2+C1 |
| exp002 | core | courses/sheet1/speech_practice | training/output/courses/core/exp002-speech-interaction | 32 | 7 | B2+C1 |
| exp004 | core | courses/sheet1/slam_practice | training/output/courses/core/exp004-slam-navigation | 48 | 7 | C1 only |
| exp005 | core | courses/sheet1/arm_practice | training/output/courses/core/exp005-robot-arm | 32 | 8 | B2+C1 |
| exp007 | cases | courses/sheet1/training | training/output/courses/cases/exp007-intelligent-factory | 96 | 3 | C1 only |
| exp008 | cases | courses/sheet1/training | training/output/courses/cases/exp008-smart-traffic | — | 4 | C1 only |
| exp006a | cases | courses/sheet1/elderly_companion | training/output/courses/cases/exp006a-elderly-companion | 48 | 9 | B2+C1 |
| exp006b | cases | —（待补） | training/output/courses/cases/exp006b-object-tracking | 48 | 9 | B2+C1 |
| ind01-ind05 | industry | —（待补） | training/output/courses/industry/ind01-… | 32×5 | 4×5 | LDT-01 等 |

## 参考实验指导书 / 参考案例源码

- guide_path: courses/sheet1/ros_practice/EXP003_lab_guide.md（指导书主文件；分段在 `courses/sheet1/ros_practice/_parts/`）
- solution_path: courses_archive/robot_vision/source-codes/exp{n}/（参考源码；开源原始资料在 `开源原始资料/`）
- 命名规则: 实验页目录 `exp-NN-slug/index.html`；衍生文档 `exp-NN-slug-guide.md`、`exp-NN-slug-solution.md`

## 约束

- write_boundary: 仅 training/output/，写入前必须经用户确认
- readonly: courses/ 与 courses_archive/ 内 md；training/output/ 下既有 index.html
- naming: 文件名禁中文/空格/大写；实验目录 exp-NN-slug；文档正文简体中文
- hardware_truth: 硬件事实以 `.claude/memory/hardware-platform-spec.md` 为准（B2/RK3576+STM32F407、C1 小车）；不得虚构传感器
- pipeline: 内容若涉及课程事实，源头是 `input/course_spec.csv` → `_meta/course-spec.yaml`，不可绕过

## 10 门课程开发自检清单（每门逐项打钩）

1. 单页 HTML 落点在该课程 output_dir 下，文件名 index.html，并入现有目录结构与站内互链。
2. 首屏给出四元组：课程目标、前置要求、学时、硬件适配（B2/C1 标注）。
3. 理论部分以图解/交互为主（话题模型、节点图、QoS、TF 树），纯文字不超过版面一半。
4. 分步实操与实验指导书 `EXP003_lab_guide.md` 对齐，每步有可复制命令与预期输出。
5. 源码示例可追溯到参考案例 source-codes 或 guide 文档，不虚构 API（ROS2 用 rclpy，禁 rospy）。
6. 每节末尾有当节验收（命令 + 判据 + 通过/失败提示）。
7. 页尾有总结 + 学习路线（下一实验直达链接）。
8. 响应式：移动端可读；样式复用站内既有 CSS 变量，不引入外部 CDN 依赖。
9. 全文简体中文，标识符英文；代码块必须标语言。