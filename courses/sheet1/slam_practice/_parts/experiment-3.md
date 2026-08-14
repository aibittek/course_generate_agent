## 实验3：基于Nav2的机器人自主导航实验（8h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/navigation/car1_navigation/`，未复制到 `source-codes/EXP004/exp03/`。已通过 human_waiver 放行，内容基于 `launch/navigation.launch.py`、`config/nav2_params.yaml` 等真实源码撰写。

**一句话读懂**：实验 2 我们给了小车一张地图。这节课让小车"学会看地图自己走路"——你在 RViz 里点一个目标点，它自己规划路线、自己转弯、自己躲开静态障碍，安全到达。这背后是 Nav2 导航栈在工作。

### 3.1 关联知识点

- 3.1.1 五大服务器 > 概念 > planner/controller/behavior/bt_navigator/velocity_smoother
- 3.1.2 Lifecycle > 原理 > 先 inactive 配置再 activate 激活
- 3.2.1 全局规划器 > 概念 > ThetaStarPlanner 在 map 系找无碰撞路径
- 3.2.2 全局代价地图 > 概念 > static + obstacle + inflation 三层
- 3.3.1 局部规划器 > 概念 > DWB FollowPath 在 odom 系跟踪路径
- 3.3.2 局部代价地图 > 概念 > 3m×3m 滚动窗口实时感知
- 3.4.1 行为树 > 原理 > XML 编排导航流程
- 3.4.2 两个导航器 > 概念 > NavigateToPose / NavigateThroughPoses
- 3.5.1 navigation.launch > 流程 > 一键启动导航系统
- 3.5.2 下发目标 > 流程 > RViz Nav2 Goal 或 ros2 action
- 3.5.3 导航三要素 > 原理 > 地图/定位/速度约束

### 3.2 实验目标

1. 理解 Nav2 五大服务器架构与 Lifecycle 生命周期 — **原理理解**
2. 掌握全局/局部代价地图的分层机制与膨胀区作用 — **流程掌握**
3. 独立完成"加载地图 → 设定目标 → 自主到达"的导航闭环 — **独立完成**
4. 能够分析导航失败（撞墙/绕路/超时）原因并修正 — **迁移应用**

### 3.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 小车C1 + COIN-D6 雷达；需先完成实验 2 得到地图 |
| OS | Ubuntu 22.04 + ROS 2 Humble |
| 核心库 | Nav2（planner/controller/bt_navigator/behavior_server）、slam_toolbox 或已存地图 |
| 依赖 | 地图文件位于 `slam/car1_slam/maps/`；`colcon build --packages-select car1_navigation` |
| 主入口 | `navigation/car1_navigation/launch/navigation.launch.py`、`config/nav2_params.yaml` |

### 3.4 实验难度

- 难度: ⭐⭐⭐（综合性）
- 重点: Nav2 架构；导航闭环（地图→定位→规划→执行）
- 难点: 行为树流程理解；代价地图分层与膨胀

### 3.5 实验现象

**快速验证流程**（先在 3m×3m 空旷场地）：

1. 启动导航：`ros2 launch car1_navigation navigation.launch.py map:=slam_map`
2. 观察 RViz：地图加载出来，机器人模型出现在地图内（AMCL 自动初始定位，默认 0,0,0）
3. 点击 RViz 顶部工具栏 **"Nav2 Goal"**，在地图上点一个目标点并拖出朝向
4. 小车自动规划绿色路径 → 沿路径行驶 → 到达后停下，RViz 显示 "Goal reached"
5. 途中放一个箱子（静态障碍）：再次导航时小车路径自动绕开

**预期效果描述**：

- RViz 显示全局路径（绿色曲线）从机器人到目标点，避开了墙和箱子
- 小车实际行驶轨迹与全局路径基本一致，转弯平滑（velocity_smoother 生效）
- 到达后机器人朝向与设定的 yaw 一致；`ros2 action send_goal` 返回值 status 为 4（SUCCEEDED）
- 若在路径上新增静态障碍，Nav2 会**重新规划**绕行

### 3.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：理解Nav2架构] --> B[步骤2：解读nav2_params]
    B --> C[步骤3：启动导航系统]
    C --> D[步骤4：下发导航目标]
    D --> E[步骤5：避障与故障排查]
```

---

#### 步骤1：理解 Nav2 架构（60min）

**知识点讲解**：

**五大服务器（3.1.1）**
- **原理**：Nav2 把导航拆成五个分工明确的服务器，各管一段：
  1. **planner_server（全局规划）**：在 map 坐标系里，从机器人位置到目标点找一条**全局路径**（避开静态墙）。本项目用 ThetaStarPlanner。
  2. **controller_server（局部规划）**：在 odom 坐标系里，**实时跟踪**全局路径，输出速度指令（cmd_vel），同时躲避动态障碍。本项目用 DWB（FollowPath）。
  3. **bt_navigator（行为树大脑）**：用行为树编排整个流程——"先规划、再跟踪、检查到没到、没到就恢复"。
  4. **behavior_server（行为服务器）**：提供异常恢复动作：spin（原地转）、backup（后退）、drive_on_heading（沿朝向直行）、assisted_teleop（辅助遥控）、wait。
  5. **velocity_smoother（速度平滑器）**：把下发的速度指令"软着陆"，防止急停急启，保护电机。
- **白话类比**：planner 是"看地图设计划线路的导航员"；controller 是"看路况实际开车的司机"；bt_navigator 是"总指挥"；behavior_server 是"故障救援队"；velocity_smoother 是"安全员"。
- **源码对应**：`config/nav2_params.yaml` 中 planner_server（L173-184）、controller_server（L113-172）、bt_navigator（L52-112）、behavior_server（L185-212）、velocity_smoother（L213-227）五段配置。

**Lifecycle 生命周期（3.1.2）**
- **原理**：Nav2 服务器都实现了 Lifecycle 状态机：启动后先 **inactive**（配置好但不出力）→ 收到激活命令变 **active**（开始工作）→ 停止变 **deactivated**。`lifecycle_manager_navigation` 统一管理（autostart: true 自动激活）。
- **源码对应**：`nav2_params.yaml` L326-338 lifecycle_manager_navigation（管理 controller/planner/behavior/bt_navigator/velocity_smoother 五个节点）。

**操作步骤**：

1. 打开 `nav2_params.yaml`，对照五大服务器把每个的 plugin 名抄到笔记。
2. 用 `ros2 node list`（启动后）观察这些节点，并 `ros2 lifecycle get /planner_server` 查看生命周期状态。
3. 画一张"目标点 → bt_navigator → planner → controller → cmd_vel → 底盘"的数据流图。

**易错点**：

- ⚠️ 混淆 planner 和 controller → **解决**：planner 管"走哪条路"（全局，慢），controller 管"怎么走"（局部，快），缺一不可。
- ⚠️ 以为 lifecycle 节点启动即工作 → **解决**：要等 lifecycle_manager 激活（autostart 自动做），激活前节点 inactive。

---

#### 步骤2：解读 nav2_params 关键配置（60min）

**知识点讲解**：

**全局代价地图（3.2.2）**
- **原理**：`global_costmap` 在 **map** 坐标系，三层叠加：
  - **static_layer**：读入实验 2 建好的静态地图（`map_subscribe_transient_local: true` 订阅 /map）
  - **obstacle_layer**：实时雷达点云标记动态障碍（scan topic /scan）
  - **inflation_layer**：把障碍**向外"吹"一层膨胀区**（`inflation_radius: 0.18`），代价从障碍处向外衰减，让机器人保持安全距离
- **源码对应**：`nav2_params.yaml` L268-301 global_costmap 三段 plugins。

**全局规划器（3.2.1）**
- **原理**：本项目 `planner_plugins: ["GridBased"]`，plugin 为 `nav2_theta_star_planner/ThetaStarPlanner`（带视线检查的 A* 变体，路径更直）。它在 global_costmap 上搜索从起点到目标的最优无碰撞路径。
- **源码对应**：`nav2_params.yaml` L173-184。

**局部代价地图与局部规划（3.3.1 + 3.3.2）**
- **原理**：`local_costmap` 在 **odom** 坐标系，是跟着机器人走的**滚动窗口**（3m×3m，`rolling_window: true`），只关心身边 3 米内的障碍。局部规划器 `DWB FollowPath`（`dwb_core::DWBLocalPlanner`）在这个小窗口里实时生成短轨迹跟踪全局路径。
- **源码对应**：`nav2_params.yaml` L228-266（local_costmap）、L133-171（FollowPath）。

**操作步骤**：

1. 抄录两个代价地图的关键差异表：

| 项 | global_costmap | local_costmap |
|----|----------------|---------------|
| 坐标系 | map | odom |
| 范围 | 全图 | 3m×3m 滚动窗口 |
| 图层 | static+obstacle+inflation | voxel+inflation |
| 更新频率 | 1.0Hz | 5.0Hz |

2. 找出 footprint（机器人轮廓）：`footprint: "[[0.18,0.135],...]"`，理解 0.18/0.135 是半长/半宽。
3. 思考（记录）：inflation_radius 从 0.18 改到 0.5 会怎样？（提示：机器人会把所有障碍当"危险区"绕很远，窄门过不去）

**易错点**：

- ⚠️ 地图没加载出来 → **解决**：map_server 的 yaml_filename 由 launch 传 `map:=slam_map`，确认地图文件名正确且位于 maps 目录。
- ⚠️ footprint 比通道宽 → **解决**：机器人过不去是正常的（代价地图算过不可行），换宽通道或缩小 inflation。

---

#### 步骤3：启动导航系统（60min）

**知识点讲解**：

**navigation.launch.py（3.5.1）**
- **原理**：一键启动：① bringup（驱动+里程计）→ ② lidar → ③ **localization**（map_server + amcl，加载地图并定位）→ ④ **navigation**（五大服务器）→ ⑤ RViz。地图路径直接从源码目录读取（`~/ros2_ws/src/xflz_eai_car1/slam/car1_slam/maps`），不依赖 install 目录。
- **源码对应**：`launch/navigation.launch.py` L13-69（launch_setup 中 maps_dir 硬编码、localization/navigation 两个 include、RViz 节点）。

**操作步骤**：

1. 启动导航：
   ```bash
   source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash
   ros2 launch car1_navigation navigation.launch.py map:=slam_map
   ```
2. 观察日志顺序：bringup 节点 → lidar → `map_server`（加载地图）→ `amcl` → 各 Nav2 服务器激活 → RViz 打开。
3. 检查节点与生命周期：
   ```bash
   ros2 node list | grep -E "planner|controller|bt_navigator|behavior|amcl|map_server"
   ros2 lifecycle get /planner_server    # 应为 active
   ros2 topic echo /map --once           # 地图话题正常
   ```
4. RViz 确认：Map（黑色墙）显示、机器人模型出现在 map 原点附近（AMCL 初始 0,0,0）、LaserScan 显示。

**易错点**：

- ⚠️ 启动报"找不到 map 文件" → **解决**：确认 `map:=slam_map` 对应 `maps/slam_map.yaml` 存在；路径硬编码为源码目录，别改文件名。
- ⚠️ 机器人模型与地图墙体重叠 → **解决**：初始定位默认 0,0,0；若地图原点不在 (0,0)，用实验 4 的"2D Pose Estimate"手动修正。
- ⚠️ 某服务器一直 inactive → **解决**：查看该节点日志（`ros2 lifecycle get` + 对应 screen 输出），常见是地图未加载导致 planner 无法初始化。

---

#### 步骤4：下发导航目标（90min）

**知识点讲解**：

**行为树流程（3.4.1 + 3.4.2）**
- **原理**：bt_navigator 加载行为树 XML（`navigate_to_pose_without_backup.xml`），流程大致：`收到目标 → 检查初始位姿 → 计算全局路径 → 跟踪路径 → 到达判定（xy_goal_tolerance 0.1m / yaw_goal_tolerance 0.1rad）→ 完成`。`navigators: ["navigate_to_pose", "navigate_through_poses"]` 对应单目标和多途经点两个导航器。
- **源码对应**：`nav2_params.yaml` L52-67（bt_navigator 配置与导航器注册）、L62-66（NavigateToPose / NavigateThroughPoses plugin）。

**下发目标两种方式（3.5.2）**
- **原理**：方式一 RViz "Nav2 Goal" 工具：点地图设定目标位置 + 拖拽设定朝向；方式二命令行 `ros2 action send_goal /navigate_to_pose`，适合脚本化与批量测试。
- **源码对应**：行为树 XML 中 `nav2_compute_path_to_pose_action_bt_node`（规划节点）与 `nav2_follow_path_action_bt_node`（跟踪节点）由 plugin_lib_names 注册（nav2_params.yaml L69-112）。

**操作步骤**：

1. RViz 方式：点击 "Nav2 Goal"，在空旷处点目标 + 拖朝向，观察：全局路径生成 → 小车转向 → 沿路径行驶 → 到达停稳。
2. 命令行方式（验证同样能到达）：
   ```bash
   ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
     "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 1.0}, orientation: {w: 1.0}}}}"
   ```
   观察返回：`status: SUCCEEDED`（4）。
3. 连续测试 3 个不同目标点，记录：路径长度、是否绕路、到达误差（用 `ros2 topic echo /amcl_pose` 对比实际位置与目标点）。
4. 目标点选在墙内测试：观察路径规划失败（"No valid path"），理解代价地图的约束。

**易错点**：

- ⚠️ 点目标后无反应 → **解决**：检查 bt_navigator 是否 active、/map 是否加载、机器人是否已定位（RViz 看粒子）。
- ⚠️ 小车在目标点附近反复打转 → **解决**：yaw 朝向未满足，调大 `yaw_goal_tolerance`（默认 0.1rad），或拖目标时把朝向对准。
- ⚠️ 到达判定失败（一直"接近中"）→ **解决**：xy_goal_tolerance 默认 0.10m，机械误差略大时可调大 0.15。

---

#### 步骤5：避障与故障排查（90min）

**知识点讲解**：

**导航三要素（3.5.3）**
- **原理**：导航能不能成功，取决于三件事：① **地图质量**（实验 2 的墙不能重影）；② **定位准确**（AMCL 粒子收敛，见实验 4）；③ **速度约束合理**（velocity_smoother 的 max_velocity/max_accel 与小车物理匹配）。三缺一就翻车。
- **源码对应**：`nav2_params.yaml` L213-227 velocity_smoother（max_velocity [0.4,0,3.0]）。

**静态障碍避让**
- **原理**：路径上新增一个箱子，global_costmap 的 obstacle_layer 收到雷达点云后会把箱子标记为障碍，下次规划**自动绕行**；若箱子在行驶中出现，local_costmap 的 voxel_layer 实时标记，controller 现场绕。
- **源码对应**：global_costmap obstacle_layer L284-296（observation_sources: scan）、local_costmap voxel_layer L246-265。

**操作步骤**：

1. 静态障碍测试：在两点路径中点放一个箱子 → 下发目标 → 观察全局路径是否绕开箱子。
2. 动态障碍测试：让小车出发后，把箱子移到路径前方 → 观察小车现场减速绕行 → 移开箱子 → 观察路径恢复。
3. 故障排查演练（任选 2 个）：
   - 现象 A：小车贴墙走 → 检查 inflation_radius 是否过小、路径是否贴边
   - 现象 B：小车原地转圈 → 检查目标朝向与 yaw_goal_tolerance
   - 现象 C：规划失败 → 检查目标是否在墙内 / 地图是否最新
4. 记录每个现象的"现象 → 原因 → 解决"到实验报告。

**易错点**：

- ⚠️ 箱子挡住后小车反复尝试硬挤 → **解决**：等 5-10s 让 planner 重规划；仍不行检查 footprint 是否比缝隙大。
- ⚠️ 避障时小车抖动 → **解决**：controller_frequency 20Hz 正常，抖动多为速度上限过高（max_vel_x 0.3 → 0.2）或 acc 过大。
- ⚠️ 动态障碍移开后小车不恢复原路径 → **解决**：正常！只要到达目标就行，路径本来就是动态的。

### 3.7 注意事项

- ⚠️ 导航测试场地至少 3m×3m 且无贵重物品，防止失控碰撞。
- ⚠️ 全程保持人跟车，发现异常立即按底盘急停或 Ctrl+C。
- ⚠️ 每次改 nav2_params.yaml 需**重启导航 launch** 才生效。
- ⚠️ 导航与建图不要同时跑（都占用 /scan 与 TF，会互相干扰）。

### 3.8 实验总结

**完成成果**：

- 理解 Nav2 五大服务器与 Lifecycle 生命周期
- 掌握全局/局部代价地图分层与膨胀机制
- 独立完成"加载地图 → 设定目标 → 自主到达"闭环（RViz 与命令行两种方式）
- 完成静态/动态障碍避让测试与常见故障排查

**技能收获**：

- 技能1：Nav2 一键启动与节点/生命周期检查
- 技能2：RViz Nav2 Goal 与 ros2 action 双通道下发目标
- 技能3：代价地图与行为树故障定位

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 地图没加载 | map:= 文件名错/文件缺失 | 检查 maps 目录与 launch 参数 |
| 目标无反应 | 未定位/节点未激活 | RViz 2D Pose Estimate 先定位；`ros2 lifecycle get` |
| 规划失败 | 目标在墙内/地图旧 | 目标点移到空旷处；重建图 |
| 到达判定失败 | 机械误差 > 容差 | 调大 xy_goal_tolerance/yaw_goal_tolerance |
| 撞墙 | inflation 太小/定位漂 | 调大 inflation_radius；重新定位 |

### 3.9 实验报告要求

**思考题**：

1. planner_server 与 controller_server 的分工是什么？为什么需要两层规划？
2. global_costmap 的 static/obstacle/inflation 三层各起什么作用？inflation_radius 调大对窄通道通行有何影响？
3. bt_navigator 用行为树而非硬编码 if-else 的好处是什么？NavigateToPose 与 NavigateThroughPoses 的区别？
4. 结合 velocity_smoother 参数，说明"急停急启"对底盘电机和定位的影响。

**评分标准**：Nav2 架构理解 20 分 + 参数解读 20 分 + 导航闭环操作 30 分 + 避障与故障排查 20 分 + 报告与思考题 10 分 = 100 分。
