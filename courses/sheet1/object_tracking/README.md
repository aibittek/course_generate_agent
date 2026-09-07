# 通用目标追踪 课程资源包（EXP006b）

机器人大模型综合应用开发（通用目标追踪）课程资源。48h 全实验，9 个实验。

## 内容

| 文件 | 说明 |
|------|------|
| `EXP006b_knowledge_graph.md` | 知识图谱（6 章 14 节 42 知识点） |
| `EXP006b_syllabus.md` | 教学大纲 |
| `EXP006b_lab_guide.md` | 实验指导书（9 实验） |
| `EXP006b_quiz.md` | 练测题库（34 题） |
| `_parts/` | 各实验分片 |
| `_meta/` | 课程规格 + 生成日志 |

## 实验列表

| 实验 | 名称 | 学时 | 类型 |
|------|------|------|------|
| 1 | 通用目标追踪--项目需求分析 | 4h | 验证性 |
| 2 | 通用目标检测与追踪底座--系统架构设计 | 4h | 设计性 |
| 3 | 追踪配置与接口设计 | 4h | 设计性 |
| 4 | 多目标追踪底座集成测试 | 8h | 综合性 |
| 5 | LLM指令与门控集成测试 | 4h | 综合性 |
| 6 | VLM描述选目标集成测试 | 4h | 综合性 |
| 7 | 语音交互集成测试 | 6h | 综合性 |
| 8 | 事件日志与故障降级集成测试 | 6h | 综合性 |
| 9 | 通用目标追踪全功能验证 | 8h | 综合性 |

## 源码

`ros2_ws/src/xflz_eai_car1/app/object_tracking/` —— 通用目标追踪（YOLOv8 + DeepTrack 卡尔曼+ReID + LLM FunctionCall + VLM 选车 + 语音 + 事件日志），复用 elderly_companion 底层。

## 规格

课程规格由 `input/course_spec_object_tracking.csv` 解析，见 `_meta/course-spec.yaml`。