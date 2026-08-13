# 机器人大模型综合应用开发 课程资源包

> 版本: v4.0
> 生成日期: 2026-08-14

## 资源包概述

本资源包包含 **机器人大模型综合应用开发**（EXP006）的全套教学资源，适用于人工智能/机器人工程/智能科学与技术 本科高年级。

本课程以**具身智能工厂 eai_factory**（装货/分拣/码垛/安全生产）综合项目为主线，覆盖需求分析 → 架构设计 → 接口设计 → 语音交互/视觉装货/分拣/码垛/具身智能工厂--危险急停集成测试 → 全功能快速验证的完整开发闭环。

## 资源清单

| 文件 | 说明 | 规模 |
|------|------|------|
| [知识图谱](EXP006_knowledge_graph.md) | 6 章 16 节三级知识结构 | 42 知识点 |
| [教学大纲](EXP006_syllabus.md) | 教学目标/学时分配/考核方式 | 48h / 9 实验 |
| [实验指导书](EXP006_lab_guide.md) | 9 个实验项目完整指导 | 190 KB |
| [练测题库](EXP006_quiz.md) | 多种题型配套练习 | 34 题 / 100 分 |
| 审核报告 | `_meta/content-audit-report.md` + `_meta/quality-review-report.md` | A 级 |

## 使用说明

### 1. 知识图谱
- 用于教师备课和学生预习
- 可作为课程内容规划的参考

### 2. 教学大纲
- 包含完整的教学目标、内容、学时、考核
- 需根据实际情况调整

### 3. 实验指导书
- 包含详细的实验步骤和评分标准
- 建议课前发放给学生预习

### 4. 练测题库
- 包含多种题型，覆盖全部知识点
- 可用于平时练习和期末考试

## 快速上手（全功能验证）

```bash
# 一键启动全部（bringup + 机械臂 + 相机 + eai_factory 节点 + 调试画面）
ros2 launch eai_factory eai_factory.launch.py

# 只测雷达安全（低内存）
ros2 launch eai_factory eai_factory.launch.py \
  start_base:=false start_voice:=false start_vision:=false \
  start_grasp:=false start_conveyor:=false start_radar:=true

# 停止（防残留）
bash scripts/stop_eai_factory.sh
```

## 关联资源

### 先修课程
- 机器人ROS2应用与开发（EXP003）— 必须
- 机器人机械臂控制基础（EXP005）— 必须
- 自然语言处理基础 — 建议

### 配套设备
- 具身智能实验箱B2 / 具身智能机器人小车C1
- 流水线附件（电机+光电传感器）、AprilTag 标签（tag36h11 id=3）、障碍物（安全测试）

### 源码位置
- `ros2_ws/src/xflz_eai_car1/app/eai_factory/`（6 节点 + launch + config + docs）

## 反馈渠道

如有问题或建议，请联系课程负责人。

---

**资源包版本**: v4.0
**最后更新**: 2026-08-14
