---
course_code: EXP006b
course_name: 机器人大模型综合应用开发（通用目标追踪）
version: v2.0
generated_at: 2026-09-07
generator: LabGuideExperimentAgent (合并版)
source_spec: courses/sheet1/object_tracking/_meta/course-spec.yaml
source_knowledge_graph: courses/sheet1/object_tracking/EXP006b_knowledge_graph.md
source_syllabus: courses/sheet1/object_tracking/EXP006b_syllabus.md
source_parts: courses/sheet1/object_tracking/_parts/experiment-{1..9}.md
csv_sha256: 5fc42d608003d2657215b33eeaa92a0fd338de1e4fcc87691a38c653c03de053
total_hours: 48
experiment_count: 9
tech_stack: YOLOv8, 多目标追踪DeepTrack(卡尔曼+外观ReID), 外观重识别ReID, RKNN NPU, 本地大模型RKLLM, LLM FunctionCall工具调用, VLM视觉选目标, 语音唤醒KWS, 流式ASR, 本地TTS, 门控路由fail-closed, MJPEG推流
hardware: 具身智能实验箱B2 / 具身智能机器人小车C1
source_code_status: external (位于 ros2_ws/src/xflz_eai_car1/app/object_tracking/，human_waiver 放行)
---

# 机器人大模型综合应用开发（通用目标追踪） 实验指导书（合并版）

> 课程代码: EXP006b
> 总学时: 48
> 实验数: 9
> 适用对象: 人工智能/机器人工程/智能科学与技术 本科高年级
> 制定日期: 2026-09-07
> 模式: human_waiver（源码位于 ROS2 工作空间 src/，未复制到 source-codes/EXP006b/）

---

## 目录

1. [实验1：通用目标追踪--项目需求分析](#实验1通用目标追踪--项目需求分析4h)
2. [实验2：通用目标检测与追踪底座--系统架构设计](#实验2通用目标检测与追踪底座--系统架构设计4h)
3. [实验3：追踪配置与接口设计](#实验3追踪配置与接口设计4h)
4. [实验4：多目标追踪底座集成测试](#实验4多目标追踪底座集成测试8h)
5. [实验5：LLM指令与门控集成测试](#实验5llm指令与门控集成测试4h)
6. [实验6：VLM描述选目标集成测试](#实验6vlm描述选目标集成测试4h)
7. [实验7：语音交互集成测试](#实验7语音交互集成测试6h)
8. [实验8：事件日志与故障降级集成测试](#实验8事件日志与故障降级集成测试6h)
9. [实验9：通用目标追踪全功能验证](#实验9通用目标追踪全功能验证8h)

---

## 实验总览

| 编号 | 名称 | 学时 | 类型 | 难度 | 源码路径 |
|------|------|------|------|------|----------|
| exp01 | 通用目标追踪--项目需求分析 | 4h | 验证性 | ⭐ | `ros2_ws/src/xflz_eai_car1/app/object_tracking/` |
| exp02 | 通用目标检测与追踪底座--系统架构设计 | 4h | 设计性 | ⭐⭐ | `ros2_ws/src/xflz_eai_car1/app/object_tracking/` |
| exp03 | 追踪配置与接口设计 | 4h | 设计性 | ⭐⭐ | `ros2_ws/src/xflz_eai_car1/app/object_tracking/` |
| exp04 | 多目标追踪底座集成测试 | 8h | 综合性 | ⭐⭐⭐ | `ros2_ws/src/xflz_eai_car1/app/object_tracking/` |
| exp05 | LLM指令与门控集成测试 | 4h | 综合性 | ⭐⭐⭐ | `ros2_ws/src/xflz_eai_car1/app/object_tracking/` |
| exp06 | VLM描述选目标集成测试 | 4h | 综合性 | ⭐⭐⭐ | `ros2_ws/src/xflz_eai_car1/app/object_tracking/` |
| exp07 | 语音交互集成测试 | 6h | 综合性 | ⭐⭐⭐ | `ros2_ws/src/xflz_eai_car1/app/object_tracking/` |
| exp08 | 事件日志与故障降级集成测试 | 6h | 综合性 | ⭐⭐⭐ | `ros2_ws/src/xflz_eai_car1/app/object_tracking/` |
| exp09 | 通用目标追踪全功能验证 | 8h | 综合性 | ⭐⭐⭐ | `ros2_ws/src/xflz_eai_car1/app/object_tracking/` |

**学时合计**: 4+4+4+8+4+4+6+6+8 = **48h**

**类型分布**: 验证性 1 个 + 设计性 2 个 + 综合性 6 个

**难度分布**: ⭐ 1 个 + ⭐⭐ 2 个 + ⭐⭐⭐ 6 个

---

## 跨实验知识脉络

```mermaid
graph LR
    E1["exp01 需求分析"] --> E2["exp02 架构设计"] --> E3["exp03 配置与接口设计"]
    E3 --> E4["exp04 多目标追踪底座"]
    E2 --> E5["exp05 LLM指令与门控"]
    E4 --> E5
    E5 --> E6["exp06 VLM描述选目标"]
    E2 --> E7["exp07 语音交互"]
    E5 --> E8["exp08 事件日志与故障降级"]
    E6 --> E8
    E7 --> E9["exp09 全功能快速验证"]
    E8 --> E9
```