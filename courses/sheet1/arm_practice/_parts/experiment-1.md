## 实验1：机械臂URDF仿真运动控制实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/simulations/`，未复制到 `source-codes/EXP005/exp01/`。已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。后续补充源码后需触发 SourceCodeAnalysisAgent 并移除豁免。本指导书内容基于 `car1_description/launch/display.launch.py`、`car1_moveit_config/launch/demo.launch.py`、`car1_gazebo/launch/gazebo_arm.launch.py` 等仿真包源码。

### 1.1 关联知识点

本实验对应第 1 章"URDF建模与仿真认知"，覆盖以下 9 个知识点：

- 1.1.1 URDF概念 > 概念 > URDF 用 XML 描述机器人的连杆、关节、惯量与视觉/碰撞几何
- 1.1.2 link/joint > 原理 > `<link>` 定义刚体属性，`<joint>` 定义两连杆的运动关系（revolute/prismatic/fixed）
- 1.1.3 TF树 > 概念 > TF 树由 URDF 解析自动生成，base_link 为根节点，依次串联 link1~link5+tcp_link
- 1.2.1 display.launch > 流程 > `display.launch.py` 启动 robot_state_publisher + joint_state_publisher_gui + rviz2 三件套
- 1.2.2 TF渲染 > 原理 > RViz 通过 TF 与 joint_states 话题实时渲染模型姿态，可拖动滑块修改关节角
- 1.2.3 MoveIt2插件 > 概念 > MoveIt2 运动规划插件提供 RvizVisualTools GUI，支持拖拽目标点 + 路径预览
- 1.3.1 Gazebo概念 > 概念 > Gazebo 通过 ODE/Bullet 物理引擎模拟重力、摩擦与接触力，支持闭环控制
- 1.3.2 gazebo_arm.launch > 流程 > `gazebo_arm.launch.py` 同时加载 URDF + ros2_control 配置，发布 joint_states
- 1.3.3 joint_trajectory > 原理 > `joint_trajectory_controller` 在 Gazebo 中按时间戳插值执行轨迹，与 MoveIt2 协同

### 1.2 实验目标

1. 理解 URDF 文件的 link/joint 结构与 TF 树自动生成机制 — 原理理解
2. 掌握 display.launch / demo.launch / gazebo_arm.launch 三大 Launch 文件的差异与适用场景 — 流程掌握
3. 独立完成 RViz 中关节滑块拖动与 MoveIt2 Plan & Execute 运动规划 — 独立完成
4. 能够在 Gazebo 中通过 joint_trajectory 话题控制真实时间轨迹回放 — 独立完成
5. 将 URDF→TF→RViz→MoveIt2→Gazebo 链路迁移到其他机器人平台 — 迁移应用

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 机器人小车C1（含 5 自由度机械臂 + Jetson/RK3576 工作站） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| 仿真软件 | RViz2 + MoveIt2 Humble + Gazebo 11 (ros-humble-ros-gz) |
| 核心库 | urdf、xacro、robot_state_publisher、joint_state_publisher_gui、joint_trajectory_controller、moveit_ros_planning_interface |
| 核心包 | car1_description、car1_moveit_config、car1_gazebo |
| 主入口 | `car1_description/launch/display.launch.py`（RViz 可视化）<br>`car1_moveit_config/launch/demo.launch.py`（MoveIt2 规划）<br>`car1_gazebo/launch/gazebo_arm.launch.py`（Gazebo 物理仿真） |

### 1.4 实验难度

- 难度: ⭐ 易
- 重点: URDF 模型加载与 RViz 关节滑块交互；MoveIt2 运动规划；Gazebo 物理仿真
- 难点: MoveIt2 规划组（Planning Group）配置与 Gazebo ros2_control 桥接的时序协同

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：

> ⚠️ **环境提示**：本章 Gazebo 物理仿真**资源消耗较大**（物理引擎 ODE/Bullet 实时计算重力、接触力），**建议在虚拟机中运行**（如 Ubuntu 22.04 + VMware/VirtualBox，分配 ≥4 核 CPU + 8GB 内存）。在设备上也可运行，但 Gazebo 启动和仿真时间会更长，且需确保系统有独立 GPU 或较强的 CPU 算力。
> 
> ⚠️ **教学定位**：本章的 Gazebo + 抓取演示是**引导性介绍**，**不是本章学习重点**。目的是让初学者**先直观看到完整生态**——URDF 加载、RViz 可视化、MoveIt2 规划、Gazebo 物理仿真、夹爪抓取全流程，建立感性认识。详细原理、IK 解算、抓取参数调优等内容分别在后续实验 5（IK 实机验证）、实验 6（IK 抓取深入）、实验 7（视觉引导抓取）展开。

1. 进入工作空间根目录：`cd ~/ros2_ws`
2. source 环境：`source /opt/ros/humble/setup.bash && source install/setup.bash`
3. 启动 URDF 可视化：`ros2 launch car1_description display.launch.py`
4. 观察 RViz 窗口：弹出 5 自由度机械臂 3D 模型，右侧出现 joint_state_publisher_gui 关节滑块面板
5. 拖动任一滑块，机械臂对应关节实时跟随转动
6. 关闭 RViz，再启动 MoveIt2 demo：`ros2 launch car1_moveit_config demo.launch.py`
7. 在 MotionPlanning 面板中拖动目标球到新位姿，点击 "Plan & Execute"，机械臂自动规划无碰撞路径并执行
8. 关闭 MoveIt2，再启动 Gazebo 仿真：`ros2 launch car1_gazebo gazebo_arm.launch.py`
9. 关闭 Gazebo，启动固定位置抓取演示：`ros2 launch car1_gazebo grasp_demo.launch.py mode:=ik`

> **步骤 9 说明（铺垫性演示，非本章重点）**：本步骤让初学者**先直观看到"机械臂能完成完整抓取流程"**，理解抓取由"接近→下降→夹取→抬升→移动→释放"6 步组成，建立感性认识。**本章不深究抓取参数**（`gripper_depth`、`pre_grasp_height`、`grasp_pitch` 等）和 **IK 解算**的细节，相关内容分别在：
> - **实验 6（机械臂抓取与放置）**：固定位置抓取的完整原理（ik/manual/none 三模式 + 参数调优）
> - **实验 7（视觉引导抓取）**：基于深度相机的动态目标检测 + look-then-move 策略
>
> **关键问题引导**（请带着这些问题观察演示）：
> 1. **没有视觉**：本次抓取的目标方块位置是**预设固定**的。如果方块被移动到其他位置，机械臂还能成功抓取吗？
> 2. **不一定成功**：抓取过程会因**夹爪力度、方块位姿偏差、碰撞**等原因失败，需要多次尝试。
> 3. **延展思考**：如何让机械臂"看到"方块并自动调整位置？→ 视觉抓取（实验 7）

**预期效果描述**：
- **RViz 阶段**：3D 模型稳定渲染，TF 树列出 7 个坐标系（base_link→link1~link5→tcp_link），拖动滑块时坐标系间箭头实时更新
- **MoveIt2 阶段**：Planning Request 面板显示成功状态，Trajectory 面板可看到 RvizVisualTools 渲染的绿色路径
- **Gazebo 阶段**：仿真世界加载地面、桌面与机械臂模型，机械臂受重力影响下垂，订阅 `/joint_trajectory_controller/joint_trajectory` 即可驱动关节运动
- **固定抓取阶段（铺垫）**：Gazebo 工作区自动生成红色方块，机械臂按"张开夹爪→接近→下降→闭合→抬升→移动→放置→归位"8 步自动执行抓取。**本章仅观察现象**，详细原理与参数调优见实验 6/7
- **完整链路**：URDF 单一文件同时被 RViz（可视化）、MoveIt2（规划）、Gazebo（物理仿真）三个工具消费；grasp_demo 则展示了 Gazebo 物理引擎 + ROS2 控制 + 机械臂运动学的端到端集成，验证 URDF 作为"机器人单一数据源"的设计思想

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：URDF模型查看] --> B[步骤2：RViz三件套启动]
    B --> C[步骤3：关节滑块交互]
    C --> D[步骤4：MoveIt2 demo启动]
    D --> E[步骤5：Plan & Execute]
    E --> F[步骤6：Gazebo物理仿真]
    F --> G[步骤7：grasp_demo固定抓取演示]
    G --> H[完成]
```

> ⚠️ **步骤 7 是铺垫性演示**：固定位置抓取演示（`grasp_demo`）是**引导性介绍**，**不是本章学习重点**。目的让初学者**先直观看到"机械臂能完成完整抓取流程"**，理解抓取由"接近→下降→夹取→抬升→移动→释放"6 步组成，建立感性认识。详细原理（ik/manual/none 三模式 + 参数调优）见**实验 6**；基于视觉的动态抓取见**实验 7**。

---

#### 步骤1：URDF 模型结构查看（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`simulations/car1_description/urdf/car1_arm.urdf.xacro` 与 `simulations/car1_description/urdf/car1_arm.urdf`

**知识点讲解**：

**URDF 概念（1.1.1）**
- **原理**：URDF（Unified Robot Description Format）是 ROS 生态中用于描述机器人结构的标准 XML 格式。URDF 描述了机器人的**运动学结构**（link 与 joint）、**动力学属性**（惯量、质量）、**视觉外观**（mesh/stl 形状）与**碰撞模型**（简化几何）。car1 5 自由度机械臂的 URDF 描述了 base_link、link1~link5、tcp_link 共 7 个坐标系，以及 5 个 revolute 关节（关节限位、轴线方向）与末端执行器。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/simulations/car1_description/urdf/car1_arm.urdf.xacro`

**link/joint 定义（1.1.2）**
- **原理**：`<link>` 标签定义刚体的视觉几何（`<visual>`）、碰撞几何（`<collision>`）与惯量（`<inertial>`）。`<joint>` 标签定义两连杆的运动关系，常见类型包括：(1) **revolute**：绕固定轴旋转，有角度限位（用于 5 个机械臂关节）；(2) **continuous**：绕固定轴连续旋转；(3) **prismatic**：沿轴线平移；(4) **fixed**：刚性连接（用于传感器支架）。car1 机械臂使用 5 个 revolute 关节串联，最后通过 fixed 关节连接夹爪。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/simulations/car1_description/urdf/car1_arm.urdf` 中 `<joint name="joint1" type="revolute">` 等 5 个关节定义

**TF 树自动生成（1.1.3）**
- **原理**：TF（Transform）库维护所有坐标系之间的实时变换关系。URDF 文件被 `robot_state_publisher` 节点解析后，根据 `<joint>` 的父子关系自动构建 TF 树，根节点为 `base_link`，向下串联 link1→link2→link3→link4→link5→tcp_link 共 6 层。开发者无需手动发布静态 TF 变换。
- **源码对应**：`robot_state_publisher` 节点（ROS2 Humble 标准包）

**操作步骤**：

1. 查看 URDF 目录结构：
   ```bash
   cd ~/ros2_ws/src/xflz_eai_car1/simulations/car1_description/urdf/
   ls
   # 预期输出：car1_arm.urdf.xacro  car1_arm.urdf  meshes/  ...
   ```

2. 查看 URDF 头部与 link 定义：
   ```bash
   head -50 car1_arm.urdf
   # 看到 <robot name="car1_arm"> 与 <link name="base_link"> 等
   ```

3. 查看关节定义：
   ```bash
   grep -A 8 '<joint name=' car1_arm.urdf | head -60
   # 看到 5 个 revolute 关节及其 axis/limit/origin 定义
   ```

4. 解析 URDF 验证语法：
   ```bash
   check_urdf car1_arm.urdf
   # 预期输出：Successfully Parsed XML
   #          root link: base_link
   #          child links: link1, link2, link3, link4, link5, tcp_link
   ```

5. 可视化 URDF 树形结构（可选）：
   ```bash
   urdf_to_graphiz car1_arm.urdf
   # 生成 car1_arm.pdf 树状图
   ```

**易错点**：
- ⚠️ **URDF 解析报"joint axis not specified"** → **解决**：检查 `<axis xyz="0 0 1"/>` 是否缺失
- ⚠️ **URDF 解析报"parent link not found"** → **解决**：确认父子 link 命名拼写一致
- ⚠️ **xacro 文件未展开导致 launch 失败** → **解决**：在 launch 中使用 `xacro` 命令预处理：`xacro car1_arm.urdf.xacro > car1_arm.urdf`

---

#### 步骤2：RViz 可视化三件套启动（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`simulations/car1_description/launch/display.launch.py`

**知识点讲解**：

**display.launch 三件套（1.2.1）**
- **原理**：`display.launch.py` 是 URDF 可视化的标准模板，依次启动三个核心节点：(1) **robot_state_publisher**：解析 URDF，发布 TF 与 robot_description；(2) **joint_state_publisher_gui**：提供图形化滑块面板，发布 `/joint_states` 话题；(3) **rviz2**：加载预配置的 rviz 配置文件（包含 RobotModel、TF、JointState 等 Display）。三个节点通过 `/joint_states` 与 `/tf` 话题解耦。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/simulations/car1_description/launch/display.launch.py` 第 10-40 行

**RViz 渲染原理（1.2.2）**
- **原理**：RViz 通过订阅 `/tf`（坐标系关系）与 `/joint_states`（关节角）两个话题，实时计算并渲染机器人 3D 模型。每一帧的渲染流程为：(1) 从 `/joint_states` 获取 5 个关节角；(2) 根据 URDF 中的关节定义，从 base_link 开始通过 TF 链计算 link1~tcp_link 的位姿；(3) 加载 mesh 文件并按位姿摆放。当用户拖动滑块时，joint_state_publisher_gui 重新发布 `/joint_states`，RViz 下一帧立即更新显示。
- **源码对应**：`rviz2` 节点（ROS2 Humble 标准包），订阅 `/tf` 与 `/joint_states`

**操作步骤**：

1. 编译 URDF 包：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select car1_description
   source install/setup.bash
   ```

2. 启动 display.launch：
   ```bash
   ros2 launch car1_description display.launch.py
   # 预期输出：
   # [INFO] [launch]: process[robot_state_publisher-1]: started
   # [INFO] [launch]: process[joint_state_publisher_gui-2]: started
   # [INFO] [launch]: process[rviz2-3]: started
   ```

3. 在 RViz 中检查 Display 列表：
   - Global Options → Fixed Frame 设为 `base_link`
   - 确认 RobotModel、TF、JointState 三个 Display 存在并打勾
   - 调整 RobotModel → Visual Enabled 为 true

4. 验证 TF 树：
   ```bash
   ros2 run tf2_tools view_frames
   # 生成 frames_xxx.pdf，查看 base_link→link1~link5→tcp_link 完整链路
   ```

5. 监控 joint_states 话题：
   ```bash
   ros2 topic echo /joint_states
   # 拖动滑块时观察 name=["joint1"~"joint5"] 与 position 数组变化
   ```

6. 监控 TF 话题频率：
   ```bash
   ros2 topic hz /tf
   # 预期：稳定在 50Hz 左右
   ros2 topic hz /joint_states
   # 预期：随滑块拖动而变化
   ```

**易错点**：
- ⚠️ **RViz 中模型显示为坐标系无 mesh** → **解决**：检查 `meshes/` 目录是否存在，URDF 中 mesh 路径是否为相对路径 `package://car1_description/meshes/xxx.stl`
- ⚠️ **TF 报"lookup would require extrapolation"** → **解决**：增大 `robot_state_publisher` 的 `publish_frequency` 到 50Hz，或减小 rviz 的 queue 大小
- ⚠️ **joint_state_publisher_gui 启动报缺包** → **解决**：`sudo apt install ros-humble-joint-state-publisher-gui`

---

#### 步骤3：关节滑块交互与坐标系观察（阶段二：能理解，30min）

> ⚠️ 本步骤对应 src 目录源码：`simulations/car1_description/urdf/car1_arm.urdf` 中 `<limit lower="..." upper="..."/>` 字段

**知识点讲解**：

**RViz 交互式探索（1.2.2 延伸）**
- **原理**：RViz 不仅能渲染模型，还提供交互式探索能力：(1) 拖动滑块单关节调试；(2) 选中 TF Display 的坐标系可显示 6DoF 位姿标签；(3) RobotModel Display 的 alpha 通道可调透明度便于看内部结构。这种"所见即所得"的探索方式是理解机器人运动学的最佳入门手段。
- **源码对应**：RViz 内置交互功能

**操作步骤**：

1. 打开 joint_state_publisher_gui 窗口（步骤 2 启动后已自动弹出）：
   - 5 个滑块对应 joint1~joint5，每个滑块有最小/最大范围
   - 拖动滑块观察 RViz 中机械臂的对应关节转动

2. 关节限位验证：
   - 尝试将滑块拖到边界，RViz 中模型在到达 URDF 中 `<limit>` 设定角度时停止
   - car1 典型限位：joint1 ±180°（底座旋转）、joint2 -90°~+90°（大臂）、joint3 -135°~+135°（小臂）等

3. 观察 TF 坐标系：
   - 在 RViz 中展开 TF Display，勾选所有 link 前的复选框
   - 每个 link 都会显示为三色 RGB 坐标轴（X红/Y绿/Z蓝）
   - 拖动滑块时，坐标系随模型移动，体现 TF 链的实时传播

4. 关节角读取脚本（辅助理解）：
   ```python
   # read_joint_states.py
   import rclpy
   from rclpy.node import Node
   from sensor_msgs.msg import JointState
   
   class JointStateReader(Node):
       def __init__(self):
           super().__init__('joint_state_reader')
           self.sub = self.create_subscription(
               JointState, '/joint_states', self.cb, 10)
       def cb(self, msg):
           print(dict(zip(msg.name, msg.position)))
   
   rclpy.init()
   rclpy.spin(JointStateReader())
   ```

5. 关节限位表格（典型值，可记录到实验报告）：

   | 关节 | 名称 | 限位 (rad) | 限位 (deg) | 物理含义 |
   |------|------|----------|----------|---------|
   | 1 | joint1 | -3.14 ~ +3.14 | -180° ~ +180° | 底座旋转（Yaw） |
   | 2 | joint2 | -1.57 ~ +1.57 | -90° ~ +90° | 大臂俯仰（Pitch） |
   | 3 | joint3 | -2.36 ~ +2.36 | -135° ~ +135° | 小臂俯仰（Pitch） |
   | 4 | joint4 | -1.57 ~ +1.57 | -90° ~ +90° | 腕部旋转（Roll） |
   | 5 | joint5 | -1.57 ~ +1.57 | -90° ~ +90° | 腕部俯仰（Pitch） |
   | - | gripper | 0 ~ 0.04 | 0 ~ 40mm | 夹爪开合（Prismatic） |

**易错点**：
- ⚠️ **滑块拖到边界时模型跳变** → **解决**：URDF 中 `<limit>` 已硬编码，软件层会钳制，不会损伤硬件；仿真阶段属于正常现象
- ⚠️ **滑块拖动但 RViz 不响应** → **解决**：检查 `/joint_states` 话题是否在发布（`ros2 topic hz /joint_states`），若停止则重启 joint_state_publisher_gui

---

#### 步骤4：MoveIt2 运动规划演示（阶段二：能理解，45min）

> ⚠️ 本步骤对应 src 目录源码：`simulations/car1_moveit_config/launch/demo.launch.py`、`simulations/car1_moveit_config/config/car1_arm.srdf`

**知识点讲解**：

**MoveIt2 运动规划插件（1.2.3）**
- **原理**：MoveIt2 是 ROS2 下的运动规划框架，核心组件包括：(1) **Planning Scene**：维护机器人与环境的碰撞对象；(2) **Planning Pipeline**：通过 OMPL 库加载规划算法（RRT、PRM 等）；(3) **RvizVisualTools GUI**：在 RViz 中以按钮形式提供 Plan / Execute / Save 等操作。MoveIt2 通过 SRDF（Semantic Robot Description Format）扩展 URDF，定义规划组（Planning Group）、预定义位姿（home/work/pick/place）等。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/simulations/car1_moveit_config/config/car1_arm.srdf`

**SRDF 与规划组**
- **原理**：SRDF 是 MoveIt2 的语义描述，`<group name="arm">` 将 5 个关节组合为一个规划链，`<group name="gripper">` 定义夹爪组，`<virtual_joint>` 定义 base_link 与世界坐标系的关系。`demo.launch.py` 加载 SRDF + move_group 节点 + RViz 插件，提供完整的运动规划 UI。
- **源码对应**：`simulations/car1_moveit_config/config/car1_arm.srdf` 中 `<group name="arm">` 字段

**操作步骤**：

1. 编译 MoveIt2 配置包：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select car1_moveit_config
   source install/setup.bash
   ```

2. 启动 demo.launch：
   ```bash
   ros2 launch car1_moveit_config demo.launch.py
   # 预期输出：move_group 节点启动 + RViz 加载 MoveIt MotionPlanning 插件
   ```

3. 配置 MotionPlanning 面板：
   - Planning Library: OMPL
   - Planning Algorithm: RRTConnect
   - Planning Attempts: 10
   - Planning Time: 5.0s
   - Goal Tolerance: 0.01

4. 选择规划组：
   - "Planning Group" 下拉框选 `arm` 或 `manipulator`

5. 拖动目标球（InteractiveMarker）：
   - 在 RViz 中找到末端执行器上的橙色球（目标标记）
   - 用鼠标拖动球到新位置，机械臂预览 IK 解
   - 点击 "Plan" 按钮，MoveIt2 调用 RRT 算法规划无碰撞路径
   - 路径以绿色线条显示
   - 点击 "Execute" 按钮，关节按规划路径运动

6. 预定义位姿调用：
   - "Stored States" 下拉框选 `home`、`work`、`pick`、`place`
   - 点击 "Update" 预览，点击 "Plan & Execute" 执行

7. 查看规划结果：
   ```bash
   ros2 topic echo /display_planned_path
   # 显示 MoveIt2 发布的可视化消息
   ros2 topic echo /trajectory_execution_event
   # 显示执行状态事件
   ```

**易错点**：
- ⚠️ **Plan 按钮变灰无响应** → **解决**：检查 "Planning Request" 面板中 "Use Cartesian Path" 是否取消勾选；确认 Goal Tolerance 不为 0
- ⚠️ **Plan 成功但 Execute 失败** → **解决**：执行需要 hardware 或 fake controller 节点，demo.launch 默认加载 fake_arm_controller
- ⚠️ **拖动目标球机械臂不动** → **解决**：检查 IK 解算服务 `/compute_ik` 是否在线（`ros2 service list | grep compute_ik`）

---

#### 步骤5：Gazebo 物理仿真（阶段三：能改造，45min）

> ⚠️ 本步骤对应 src 目录源码：`simulations/car1_gazebo/launch/gazebo_arm.launch.py`、`simulations/car1_gazebo/config/controllers.yaml`

**知识点讲解**：

**Gazebo 物理引擎（1.3.1）**
- **原理**：Gazebo 是 3D 物理仿真平台，集成 ODE（Open Dynamics Engine）与 Bullet 两种物理引擎，可模拟：(1) **刚体动力学**：重力、惯性、摩擦；(2) **接触力**：碰撞检测与接触响应；(3) **传感器**：激光、IMU、相机。与 RViz 纯几何渲染不同，Gazebo 的机械臂关节会受重力影响下垂，更接近真实物理环境。
- **源码对应**：`gazebo` 可执行文件（ros-humble-ros-gz）

**gazebo_arm.launch 桥接（1.3.2）**
- **原理**：`gazebo_arm.launch.py` 同时完成三件事：(1) 启动 Gazebo 服务器（gzserver）与客户端（gzclient）；(2) 通过 `robot_state_publisher` 加载 URDF 并发布 TF；(3) 加载 `ros2_control` 配置 `controllers.yaml`（包含 `joint_state_broadcaster` 与 `arm_controller`），建立 ROS2 与 Gazebo 模型之间的桥接。Gazebo 中的机械臂关节通过 `JointTrajectoryController` 接收 ROS2 轨迹指令。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/simulations/car1_gazebo/launch/gazebo_arm.launch.py`

**joint_trajectory_controller（1.3.3）**
- **原理**：`joint_trajectory_controller` 是 ros2_controllers 包中的标准控制器，订阅 `~/joint_trajectory` 话题（trajectory_msgs/JointTrajectory），按照时间戳插值执行多关节同步运动。每个轨迹点包含目标位置、速度、加速度与到达时间。MoveIt2 的 Execute 操作最终通过向该话题发布轨迹来驱动 Gazebo 中的机械臂。
- **源码对应**：`simulations/car1_gazebo/config/controllers.yaml`

**操作步骤**：

1. 编译 Gazebo 包：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select car1_gazebo
   source install/setup.bash
   ```

2. 启动 Gazebo 仿真：
   ```bash
   ros2 launch car1_gazebo gazebo_arm.launch.py
   # 预期：
   # - 弹出 Gazebo 窗口，加载地面、桌面与机械臂
   # - 机械臂受重力影响略微下垂
   # - 终端打印 controller_manager 加载 joint_state_broadcaster 与 arm_controller
   ```

3. 检查 controller 状态：
   ```bash
   ros2 control list_controllers
   # 预期输出：
   # joint_state_broadcaster[JointStateBroadcaster] active
   # arm_controller[JointTrajectoryController] active
   ```

4. 发送简单轨迹指令：
   ```bash
   ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
   joint_names: ['joint1','joint2','joint3','joint4','joint5']
   points:
   - positions: [0.0, -0.5, 0.5, 0.0, 0.0]
     time_from_start: {sec: 2, nanosec: 0}
   "
   # 预期：Gazebo 中机械臂在 2 秒内平滑运动到指定姿态
   ```

5. 周期性摆动测试（5个关节往复运动）：
   ```bash
   ros2 topic pub -r 1 /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
   joint_names: ['joint1','joint2','joint3','joint4','joint5']
   points:
   - positions: [0.0, -0.5, 0.5, 0.0, 0.0]
     time_from_start: {sec: 1}
   - positions: [0.5, -0.3, 0.7, 0.2, 0.1]
     time_from_start: {sec: 2}
   - positions: [0.0, -0.5, 0.5, 0.0, 0.0]
     time_from_start: {sec: 3}
   "
   # 预期：机械臂循环摆动
   ```

6. MoveIt2 + Gazebo 集成（最终阶段）：
   - 单独终端启动 MoveIt2 demo（指向 Gazebo 仿真而非 fake_controller）
   - 在 RViz 中拖动目标球 → Plan & Execute
   - 观察 Gazebo 中机械臂按规划路径运动

**易错点**：
- ⚠️ **Gazebo 启动后机械臂瘫倒在地** → **解决**：检查 `controllers.yaml` 中 `arm_controller` 是否 `active`，可手动激活：`ros2 control set_controller_state arm_controller active`
- ⚠️ **发送轨迹后 Gazebo 中无响应** → **解决**：检查 `joint_names` 与 URDF 中 `<joint name=>` 完全一致，顺序无所谓但拼写必须匹配
- ⚠️ **MoveIt2 Plan 成功但 Gazebo 中不执行** → **解决**：MoveIt2 的 move_group 需配置 `follow_joint_trajectory` 指向 Gazebo 的 `arm_controller`，修改 `car1_moveit_config/config/controllers.yaml` 中的 `action_ns`

---

#### 步骤6：端到端联动验证（阶段三：能改造，30min）

**操作步骤**：

1. 三终端并发起飞完整链路：
   ```bash
   # 终端 1：Gazebo
   ros2 launch car1_gazebo gazebo_arm.launch.py
   
   # 终端 2：MoveIt2
   ros2 launch car1_moveit_config demo.launch.py
   
   # 终端 3：监控
   ros2 topic echo /joint_states
   ros2 topic echo /tf
   ros2 run tf2_tools view_frames
   ```

2. 性能基线（实验报告必填）：

   | 指标 | 期望值 | 实测值 |
   |------|-------|-------|
   | display.launch 启动时间 | < 5s |  |
   | MoveIt2 Plan 时间（典型目标） | < 1s |  |
   | Gazebo 启动时间 | < 15s |  |
   | joint_trajectory 单步执行误差 | < 0.01 rad |  |
   | 3D 模型渲染帧率 | ≥ 30 FPS |  |

3. 抓取场景预演（无实物）：
   - 在 MoveIt2 中将末端拖到目标位置上方 0.1m
   - Plan & Execute 第一次移动（接近）
   - 再拖到目标正上方下压
   - Plan & Execute 第二次移动（下压）
   - 观察 Gazebo 中夹爪是否准确接近目标

**易错点**：
- ⚠️ **Gazebo 物理仿真卡顿** → **解决**：降低 `real_time_factor` 或使用 headless 模式（`gzclient` 不启动）
- ⚠️ **MoveIt2 Plan 频繁失败** → **解决**：在 Planning Scene 中添加桌面/障碍物碰撞对象，或增大 `planning_time` 到 10s

---

#### 步骤7：grasp_demo 固定位置抓取演示（铺垫性，30min）

> ⚠️ **本步骤为引导性演示，非本章学习重点**：目的是让初学者**先直观看到"机械臂能完成完整抓取流程"**，理解抓取由"接近→下降→夹取→抬升→移动→释放"6 步组成，建立感性认识。详细原理（ik/manual/none 三模式 + 参数调优）见**实验 6**；基于视觉的动态抓取见**实验 7**。
> 
> ⚠️ **环境提示**：本步骤 Gazebo 物理仿真**资源消耗较大**（物理引擎 ODE/Bullet 实时计算重力、接触力），**建议在虚拟机中运行**（≥4 核 CPU + 8GB 内存）。实机也可运行但启动/仿真时间更长。

**知识点讲解**：

**固定位置抓取流程**
- **原理**：`grasp_demo.launch.py` 在 Gazebo 中自动生成一个红色方块，按预设目标位置触发机械臂执行完整抓取流程。机械臂依次执行 8 个动作：①张开夹爪 → ②接近目标上方 → ③下降到抓取高度 → ④闭合夹爪 → ⑤抬升物体 → ⑥移动到放置区 → ⑦释放物体 → ⑧归位 home。**目标方块位置是预设固定**的，没有视觉反馈。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/simulations/car1_gazebo/launch/grasp_demo.launch.py`

**抓取参数感性认识（仅观察）**
- **原理**：`grasp_demo` 内部使用 ik 模式（解析法 IK），目标位置和抓取参数（`gripper_depth`、`pre_grasp_height`、`grasp_pitch` 等）在 launch 中硬编码。**本章仅观察现象，不深究参数**。
- **源码对应**：`simulations/car1_gazebo/launch/grasp_demo.launch.py` 中 `grasp_demo_ik.py`

**操作步骤**：

1. 确保已关闭步骤 6 的 Gazebo 和 MoveIt2（避免节点冲突）：
   ```bash
   # Ctrl+C 关闭前述所有终端进程
   ```

2. 启动固定位置抓取演示：
   ```bash
   ros2 launch car1_gazebo grasp_demo.launch.py mode:=ik
   # 预期：
   # - Gazebo 弹出，加载地面、桌面、机械臂、红色方块
   # - 机械臂自动执行 8 步抓取流程
   # - 终端打印动作阶段：open→approach→descend→grasp→lift→move→place→home
   ```

3. 观察 Gazebo 中的抓取过程：

   | 阶段 | 动作 | 现象 |
   |------|------|------|
   | 1 | 张开夹爪 | gripper_controller 发布张开指令，夹爪张开 |
   | 2 | 接近 | 机械臂底座旋转 + 臂部运动，移动到目标上方 |
   | 3 | 下降 | 末端 z 下降至预设抓取高度 |
   | 4 | 闭合 | 夹爪闭合（gripper_controller）抓取方块 |
   | 5 | 抬升 | 末端抬升，方块离开桌面 |
   | 6 | 移动 | 机械臂平移到放置区上方 |
   | 7 | 释放 | 夹爪张开，方块落下 |
   | 8 | 归位 | 机械臂回到 home 姿态 |

4. 反复运行（Ctrl+C 关闭后重新启动），观察每次抓取是否都能成功。

5. 尝试改变方块位置（手动在 Gazebo 中拖动红色方块到其他位置），重新运行 `grasp_demo.launch.py`：
   - **现象**：抓取失败！因为目标位置是预设固定的，机械臂不知道方块已被移动。
   - **思考**：这正是"无视觉抓取"的局限性。

6. 尝试其他模式：
   ```bash
   # manual 模式：使用预设关节角度
   ros2 launch car1_gazebo grasp_demo.launch.py mode:=manual
   
   # none 模式：仅启动环境，不自动抓取
   ros2 launch car1_gazebo grasp_demo.launch.py mode:=none
   ```

**关键问题引导**（请带着这些问题观察演示）：

1. **没有视觉**：本次抓取的目标方块位置是**预设固定**的。如果方块被移动到其他位置，机械臂还能成功抓取吗？→ **答：不能**，因为机械臂不知道方块在哪。
2. **不一定成功**：抓取过程会因**夹爪力度、方块位姿偏差、碰撞**等原因失败，需要多次尝试。
3. **延展思考**：如何让机械臂"看到"方块并自动调整位置？→ **答：视觉抓取**（见实验 7）。

**易错点**：
- ⚠️ **Gazebo 启动后机械臂瘫倒** → **解决**：检查 `controllers.yaml` 中 `arm_controller` 与 `gripper_controller` 是否 `active`：`ros2 control list_controllers`
- ⚠️ **grasp_demo 启动后夹爪不动** → **解决**：检查 `/gripper_controller/joint_trajectory` 话题是否在发布（`ros2 topic list | grep gripper`）
- ⚠️ **物理仿真卡顿严重** → **解决**：降低 `real_time_factor` 或减小 mesh 复杂度；如在物理机运行，建议改用虚拟机
- ⚠️ **方块掉出抓取范围** → **解决**：确认 `arm_params.yaml` 中 `gripper_depth` / `pre_grasp_height` 未被修改为不合理值

---

#### 完整可运行代码 demo_urdf_view.py

> 独立 demo 脚本：使用 urdf_parser_py 直接加载并解析 URDF，打印 TF 树（不依赖 ROS2）

```python
# -*- coding: utf-8 -*-
"""
实验1 demo：URDF 模型加载与 TF 树打印
平台：B2 / C1
运行：python3 demo_urdf_view.py /path/to/car1_arm.urdf
"""
import sys
from urdf_parser_py.urdf import URDF


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 demo_urdf_view.py <urdf_path>")
        return
    urdf_path = sys.argv[1]
    
    # 解析 URDF
    robot = URDF.from_xml_file(urdf_path)
    print(f"[OK] 加载 URDF: {robot.name}")
    print(f"  根 link: {robot.robot.name}")
    print(f"  link 数量: {len(robot.links)}")
    print(f"  joint 数量: {len(robot.joints)}")
    print()
    
    # 打印 link 列表
    print("=== Links ===")
    for link in robot.links:
        print(f"  - {link.name} (visual={link.visual is not None}, "
              f"collision={link.collision is not None}, "
              f"inertial={link.inertial is not None})")
    print()
    
    # 打印 joint 列表
    print("=== Joints ===")
    for joint in robot.joints:
        limits = ""
        if joint.limit:
            limits = f"[{joint.limit.lower:.2f} ~ {joint.limit.upper:.2f}]"
        print(f"  - {joint.name} ({joint.type}) "
              f"{joint.parent.link} -> {joint.child.link} {limits}")
    print()
    
    # 简单 TF 链打印
    print("=== TF Chain (base_link -> tcp_link) ===")
    parent = robot.robot.name
    for _ in range(20):  # 防止循环
        child_joint = next((j for j in robot.joints if j.parent.link == parent), None)
        if not child_joint:
            break
        print(f"  {parent} --[{child_joint.name}]--> {child_joint.child.link}")
        parent = child_joint.child.link
        if "tcp" in parent or "gripper" in parent:
            break


if __name__ == "__main__":
    main()
```

### 1.7 实验总结

**完成成果**：
- 加载并解析 car1 5 自由度机械臂 URDF，理解 link/joint/TF 树结构
- 启动 display.launch 完成 RViz 可视化与关节滑块交互
- 启动 demo.launch 完成 MoveIt2 Plan & Execute 运动规划
- 启动 gazebo_arm.launch 完成 Gazebo 物理仿真与 joint_trajectory 控制
- **（v1.1 新增）** 体验 grasp_demo 固定位置抓取演示，直观感受"接近→下降→夹取→抬升→移动→释放→归位"完整抓取流程
- 验证 URDF→TF→RViz→MoveIt2→Gazebo→grasp_demo 完整仿真链路

**技能收获**：
- 掌握 URDF 模型描述规范（link、joint、limit、axis、origin）
- 理解 robot_state_publisher / joint_state_publisher / RViz 三件套的协作
- 熟悉 MoveIt2 运动规划框架（SRDF、Planning Group、OMPL）
- 掌握 Gazebo 物理仿真与 ros2_control 桥接
- **（v1.1 新增）** 了解固定位置抓取的感性认识（目标预设、无视觉反馈、8 步流程）
- **（v1.1 新增）** 理解"无视觉抓取"的局限性，与后续视觉抓取形成对照

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| RViz 中模型不显示 | mesh 路径错误 | 检查 `package://` 前缀与 meshes/ 目录 |
| TF "lookup would require extrapolation" | publish_frequency 过低 | 调高 robot_state_publisher 频率 |
| MoveIt2 Plan 失败 | 碰撞检测阻止 | 调整 Goal Tolerance 或添加 Allowed Collision Matrix |
| Gazebo 启动后机械臂瘫倒 | controller 未激活 | `ros2 control set_controller_state arm_controller active` |
| joint_trajectory 无响应 | joint_names 拼写错误 | 对照 URDF 中 `<joint name=>` 修正 |
| **grasp_demo 抓取失败** | **目标方块被移位/参数错误** | **确认方块在预设位置；检查 arm_params.yaml** |
| **grasp_demo 启动慢/卡顿** | **物理仿真资源消耗大** | **建议在虚拟机中运行（≥4 核 CPU + 8GB 内存）** |

### 1.8 思考题

1. URDF 与 XACRO 的关系是什么？为什么 car1 选用 XACRO 描述？请列举 XACRO 的至少 3 个核心特性（宏定义、参数化、文件包含）。
2. robot_state_publisher 与 joint_state_publisher 的职责边界是什么？它们之间如何解耦？如果移除 joint_state_publisher_gui，机械臂会保持当前姿态还是回到零位？
3. MoveIt2 Plan 成功但 Execute 失败的可能原因有哪些？请从 Planning Group、Controller、Trajectory 时间戳三个角度分析。
4. 同一份 URDF 如何同时驱动 RViz 几何渲染、MoveIt2 运动规划与 Gazebo 物理仿真？这背后体现了 ROS 生态的什么设计思想？
5. 在 Gazebo 物理仿真中加入一个桌面（box 障碍物）后，MoveIt2 的 Plan 行为会发生什么变化？这对实机抓取有什么启示？
6. **（v1.1 新增）** 在 `grasp_demo` 演示中，如果将红色方块手动移动到其他位置，再次启动 `grasp_demo` 还能成功抓取吗？为什么？如果想让机械臂自动适应方块位置变化，应该如何改进？

### 1.9 实验报告要求

**评分标准**：URDF 加载与解析 10 分 + RViz 交互 15 分 + MoveIt2 规划 20 分 + Gazebo 仿真 20 分 + grasp_demo 演示体验与思考 20 分 + 实验报告 15 分 = 100 分。

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初版生成（基于 _registry.yaml human_waiver 模式，标注 [待源码核实]） |
| v1.1 | 2026-08-10 | 新增步骤 7：grasp_demo 固定位置抓取演示（引导性介绍）；新增环境提示（虚拟机建议）、教学定位说明（铺垫性演示）、关键问题引导（无视觉抓取局限性→实验 7 视觉抓取）；更新 1.6/1.7/1.8/1.9 节；同步 course_spec.csv 字段更新 |
