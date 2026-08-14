# 机器人SLAM与Nav应用开发 课程资源包

> 版本: v1.0
> 生成日期: 2026-08-14

## 资源包概述

本资源包包含 **机器人SLAM与Nav应用开发**（EXP004）的全套教学资源，适用于人工智能/机器人工程/智能科学与技术 本科高年级，**面向初学者友好**（每个实验都有"一句话读懂"白话引导）。

本课程以 car1 移动机器人为平台，覆盖"**建模 → 建图 → 定位 → 导航 → 避障 → 多点任务 → 三维进阶**"的完整技术闭环，强调从原理到工程落地的动手实践。

## 资源清单

| 文件 | 说明 | 规模 |
|------|------|------|
| [知识图谱](EXP004_knowledge_graph.md) | 7 章 27 节三级知识结构 | 65 知识点 |
| [教学大纲](EXP004_syllabus.md) | 教学目标/学时分配/考核方式 | 48h / 7 实验 |
| [实验指导书](EXP004_lab_guide.md) | 7 个实验项目完整指导 | 2115 行 |
| [练测题库](EXP004_quiz.md) | 多种题型配套练习 | 44 题 / 100 分（覆盖 65/65 知识点） |
| 实验分册 | `_parts/experiment-{1..7}.md` | 7 个独立文件 |

## 使用说明

### 1. 知识图谱
- 用于教师备课和学生预习
- 知识点 ID（如 2.2.2）与实验指导书中的"关联知识点"一一对应

### 2. 教学大纲
- 包含完整的教学目标、内容、学时、考核
- 需根据实际情况调整

### 3. 实验指导书
- 每个实验包含：一句话读懂 / 关联知识点 / 实验目标 / 快速验证流程 / 详细步骤 / 易错点 / 思考题
- 建议课前发放给学生预习，课中按"快速验证流程"先跑通再看原理

### 4. 练测题库
- 包含多种题型，覆盖全部知识点
- 可用于平时练习和期末考试

## 快速上手（建图 → 导航完整闭环）

```bash
# 1. 建图（bringup + 雷达 + slam_toolbox + RViz）
ros2 launch car1_slam slam.launch.py

# 2. 遥控建图（另开终端，真终端运行）
ros2 run car1_slam slam_teleop     # w/s/a/d/空格 控制，低速走闭环

# 3. 保存地图
ros2 run car1_slam map_save map_01

# 4. 导航（加载地图 + AMCL 定位 + Nav2）
ros2 launch car1_navigation navigation.launch.py map:=map_01

# 5. RViz 中：2D Pose Estimate 定位 → Nav2 Goal 下发目标
```

## 关联资源

### 先修课程
- 机器人ROS2应用与开发（EXP003）— 必须
- C++或Python编程基础 — 建议

### 配套设备
- 具身智能实验箱B2 / 具身智能机器人小车C1
- COIN-D6 激光雷达（/dev/ttyUSB1）、HP60C 深度相机（exp07 进阶）

### 源码位置
- 建图：`ros2_ws/src/xflz_eai_car1/slam/car1_slam/`（launch/config/map_save/slam_teleop）
- 导航：`ros2_ws/src/xflz_eai_car1/navigation/car1_navigation/`（nav2_params/navigation.launch）
- 模型：`ros2_ws/src/xflz_eai_car1/simulations/car1_description/`（car1.urdf）
- 技术文档：`ros2_ws/src/xflz_eai_car1/slam/doc/slam_toobox_tutorial.md`

## 反馈渠道

如有问题或建议，请联系课程负责人。

---

**资源包版本**: v1.0
**最后更新**: 2026-08-14
