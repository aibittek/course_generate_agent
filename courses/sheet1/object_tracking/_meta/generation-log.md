# EXP006b 生成日志

| 字段 | 值 |
|------|-----|
| 课程代码 | EXP006b |
| 课程名称 | 机器人大模型综合应用开发（通用目标追踪） |
| 生成日期 | 2026-09-07 |
| 生成器 | KnowledgeGraphAgent / SyllabusAgent / LabGuideExperimentAgent / QuizAgent |
| 规格源 | `input/course_spec_object_tracking.csv`（独立 CSV，未并入主 CSV） |
| 总学时 | 48h（理论 0 + 实验 48） |
| 实验数 | 9 |
| 技术栈 | YOLOv8 / DeepTrack(卡尔曼+ReID) / RKNN / RKLLM / LLM FunctionCall / VLM / KWS / ASR / TTS / 门控fail-closed / MJPEG |

## 产出文件

| 文件 | 说明 |
|------|------|
| `EXP006b_knowledge_graph.md` | 知识图谱（6 章 14 节 42 知识点） |
| `EXP006b_syllabus.md` | 教学大纲（48h 全实验） |
| `EXP006b_lab_guide.md` | 实验指导书（9 实验，合并版，1721 行） |
| `EXP006b_quiz.md` | 练测题库（34 题：单选20/多选8/简答4/编程2） |
| `_meta/course-spec.yaml` | 解析自 CSV 的课程规格 |
| `_parts/experiment-{1..9}.md` | 各实验分片（合并后保留） |

## 生成说明

- 源码位于 `ros2_ws/src/xflz_eai_car1/app/object_tracking/`，human_waiver 放行（未复制到 source-codes/）。
- 复用 elderly_companion 底层（common/speech/llm/vision），自研 tracking/ 核心。
- 一致性：lab_guide 9 实验学时 4+4+4+8+4+4+6+6+8=48h == syllabus == spec.total_hours。
- 知识点编号：1.1.1~6.2.3，42 个，quiz 覆盖 40/42。

## 版本

- v1.0 / 2026-09-07 初始生成。审核级别：内容审核 A 级（✅ 通过，2 项 🟡 建议），质量审核 A 级 91 分。