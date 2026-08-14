# EXP004 课程生成进度

> 课程: 机器人SLAM与Nav应用开发
> 生成日期: 2026-08-14（**v1.0 全量生成**）
> 模式: human_waiver（源码位于 ROS2 工作空间 ros2_ws/src/xflz_eai_car1/slam/ 与 navigation/，未复制到 source-codes/EXP004/）

---

## 总体进度

| Step | 任务 | 状态 | 产出 | 行数/大小 |
|------|------|------|------|----------|
| 1 | 解析 EXP004 spec | ✅ 完成 | `_meta/course-spec.yaml`（car1 SLAM+Nav，7 实验/48h） | 165 行 |
| 2 | 知识图谱 + 教学大纲 | ✅ 完成 | `EXP004_knowledge_graph.md` + `EXP004_syllabus.md` | 380 + 190 行 |
| 3 | 源码仓库初始化 | ✅ 完成（human_waiver） | 源码位于 `ros2_ws/src/xflz_eai_car1/slam/car1_slam/` + `navigation/car1_navigation/` | - |
| 4 | 7 个实验内容生成 | ✅ 完成 | `_parts/experiment-{1..7}.md` | 1980+ 行 |
| 4.5 | 合并为 Lab Guide | ✅ 完成 | `EXP004_lab_guide.md` | 2115 行 |
| 5 | 练测题生成 | ✅ 完成 | `EXP004_quiz.md` | 44 题 / 100 分（覆盖 65/65） |
| 6 | 内容审核 | ✅ 完成（A 级 97.3/100） | `_meta/content-audit-report.md` | 1 文件 |
| 7 | 质量审核 | ✅ 完成（A 级，含 8 处源码抽查） | `_meta/quality-review-report.md` | 1 文件 |
| 8 | 资源整合输出 | ✅ 完成 | `README.md` | 1 文件 |

**完成度**: 8/8（全部完成，资源包可直接使用；exp07 待补源码后重做分析）

---

## 关键统计

### 实验概览
- 实验总数: 7
- 总学时: 48h（验证性 4h + 设计性 4h + 综合性 40h）
- 难度分布: ⭐ 1 + ⭐⭐ 1 + ⭐⭐⭐ 5
- 类型分布: 验证性 1 + 设计性 1 + 综合性 5

### 实验列表
| 编号 | 名称 | 学时 | 类型 | 难度 |
|------|------|------|------|------|
| exp01 | SLAM建图原理与URDF模型加载实验 | 4h | 验证性 | ⭐ |
| exp02 | 基于SLAM_Toolbox的二维激光建图实验 | 4h | 设计性 | ⭐⭐ |
| exp03 | 基于Nav2的机器人自主导航实验 | 8h | 综合性 | ⭐⭐⭐ |
| exp04 | 基于AMCL的自适应蒙特卡罗定位实验 | 8h | 综合性 | ⭐⭐⭐ |
| exp05 | 局部路径规划与动态避障实验 | 8h | 综合性 | ⭐⭐⭐ |
| exp06 | 基于激光雷达的单点与多点导航避障实验 | 8h | 综合性 | ⭐⭐⭐ |
| exp07 | 基于RTAB-Map的三维视觉SLAM导航实验 | 8h | 综合性 | ⭐⭐⭐ |

### 知识点覆盖
- 知识图谱: 7 章 27 节 **65 知识点**
  - 概念类: 26
  - 原理类: 18
  - 流程类: 21
- 难度分布: 记忆 16 + 理解 22 + 应用 22 + 分析 5
- 实验-知识点映射覆盖率: 100%（每实验均关联对应章节知识点）

### 测验题
- 总题数: 44（单选 27 × 2分 + 多选 11 × 2分 + 简答 5 × 3分 + 编程/操作 1 × 9分 = 100 分）
- 显式覆盖知识点: **65/65（100%）**，7/7 章全覆盖
- 难度分布: 容易 19 + 中等 16 + 困难 7

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-08-14 | **全量生成**：EXP004 机器人SLAM与Nav应用开发（7 实验 48h），覆盖 URDF 建模→SLAM_Toolbox 建图→Nav2 导航→AMCL 定位→DWA/TEB 避障→单点/多点导航→RTAB-Map 三维进阶；所有实验含源码锚点与"一句话读懂"入门引导；exp07 因源码缺失（无资源）按 human_waiver 以原理+演示型处理 |

## 关键事实锚点（源码）

- 建图一键启动: `ros2 launch car1_slam slam.launch.py`（bringup → lidar → [10s] slam_toolbox → rviz）
- 建图参数: `slam/car1_slam/config/slam.yaml`（mode: mapping / resolution 0.05 / do_loop_closing: true / minimum_travel_distance 0.01）
- 遥控: `slam_teleop.py`（w/s/a/d/空格 → cmd_vel）
- 保存地图: `map_save.py` → nav2_map_server map_saver_cli（产出 pgm+yaml）
- 导航一键启动: `ros2 launch car1_navigation navigation.launch.py map:=slam_map`
- 导航参数: `navigation/car1_navigation/config/nav2_params.yaml`（planner=ThetaStar / controller=DWB FollowPath / AMCL 粒子 500~2000 / local_costmap 3×3 滚动窗口 / inflation 0.18）
- 多点导航: `ros2 action send_goal /navigate_through_poses nav2_msgs/action/NavigateThroughPoses`
- 坐标系链: map → odom → base_footprint → laser_link（EKF 提供 odom，URDF 提供静态 TF）
