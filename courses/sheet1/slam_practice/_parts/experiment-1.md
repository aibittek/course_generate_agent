## 实验1：SLAM建图原理与URDF模型加载实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/simulations/car1_description/`（URDF）与 `ros2_ws/src/xflz_eai_car1/slam/car1_slam/`，未复制到 `source-codes/EXP004/exp01/`。已通过 human_waiver 模式放行，内容基于 `car1.urdf`、`display.launch.py`、`slam_toobox_tutorial.md` 等真实源码撰写。

**一句话读懂**：这节课不写一行复杂代码，目标就两件事——① 用"蒙眼逛新家"的比喻听懂 SLAM 到底在干什么；② 用 URDF + RViz 把 car1 机器人"搬"到电脑屏幕上，看看它长什么样、坐标怎么连。

### 1.1 关联知识点

- 1.4.1 SLAM概念 > 概念 > SLAM = 同时定位与建图，"鸡生蛋蛋生鸡"问题
- 1.4.2 建图三要素 > 原理 > 感知 → 定位 → 构图，循环往复
- 1.4.3 占据栅格地图 > 概念 > 0 空闲 / 100 占据 / -1 未知
- 1.1.1 URDF概念 > 概念 > `<link>` 身体部件 + `<joint>` 关节连接
- 1.1.2 joint类型 > 原理 > fixed 固定 / continuous 车轮 / revolute 舵机
- 1.1.3 TF树 > 概念 > URDF 自动生成，根节点 base_footprint
- 1.2.1 Xacro宏 > 概念 > 宏语言复用部件模板
- 1.3.1 car1三部分 > 概念 > 主体 + 机械臂 + 爪子
- 1.3.2 display三件套 > 流程 > joint_state_publisher_gui + robot_state_publisher + rviz2
- 1.5.1 建图环境 > 流程 > 驱动 + 雷达 + SLAM + RViz
- 1.5.2 好地图标准 > 概念 > 墙单线/尺寸误差<2%/直角≈90°

### 1.2 实验目标

1. 理解 SLAM 的基本概念与建图三要素 — **原理理解**
2. 掌握 URDF 的 link/joint 结构与 Xacro 宏语法 — **流程掌握**
3. 独立完成 car1 模型的 RViz 可视化加载 — **独立完成**
4. 能够判断什么样的地图是"好地图" — **理解**

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 工作站（Ubuntu 22.04 + ROS2 Humble）— 本实验可**不接真机**，纯软件可视化 |
| OS | Ubuntu 22.04 + ROS 2 Humble |
| 核心库 | ROS2（urdf / xacro / robot_state_publisher / joint_state_publisher_gui / rviz2） |
| 依赖 | `source /opt/ros/humble/setup.bash` + `source ~/ros2_ws/install/setup.bash`；已 `colcon build --packages-select car1_description` |
| 主入口 | `simulations/car1_description/launch/display.launch.py`、`simulations/car1_description/urdf/car1.urdf` |

### 1.4 实验难度

- 难度: ⭐（验证性，入门）
- 重点: SLAM 直觉理解；URDF 的 link/joint 概念；RViz 可视化
- 难点: 无（本实验为全课程铺垫）

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：

1. 打开终端：`ros2 launch car1_description display.launch.py`
2. RViz 窗口打开，左侧显示 car1 机器人 3D 模型（底盘 + 4 个麦轮 + 机械臂 + 爪子）
3. 左侧面板打开 "JointStatePublisher" 面板，拖动机械臂关节滑块，模型实时跟随
4. 打开 TF 显示（Add → TF），看到 base_footprint → base_link → ... → laser_link 的坐标轴树

**预期效果描述**：

- RViz 中机器人以网格/实体显示，底盘 4 麦轮可绕轮轴旋转（continuous 关节）
- 机械臂 5+ 关节滑块可拖动，爪子可张合（revolute 关节）
- TF 树显示红色 X / 绿色 Y / 蓝色 Z 坐标轴，从 base_footprint 逐级连接
- 关闭 display.launch 后无任何硬件动作（本实验纯仿真观察）

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：理解SLAM原理] --> B[步骤2：学习URDF语法]
    B --> C[步骤3：解析car1模型]
    C --> D[步骤4：RViz可视化]
    D --> E[步骤5：建图环境认知]
```

---

#### 步骤1：理解 SLAM 原理（30min）

**知识点讲解**：

**SLAM 概念（1.4.1）**
- **原理**：SLAM（Simultaneous Localization and Mapping）中文叫"同时定位与建图"。核心矛盾是：**定位需要地图，建图需要知道自己位置**——像"鸡生蛋、蛋生鸡"。解决思路是"一边猜一边画，互相校正"：先用粗略位置画个粗略地图，再用这个地图修正位置，越修越准。
- **白话类比**：蒙上眼睛走进一个新房间，你只能靠手摸墙（雷达扫描）和数自己走了几步（里程计）。你要么先大概知道自己在哪才能画地图，要么先有地图才能定位——解决办法是"边摸边画边猜"：摸到墙就记住"这里有一堵墙"，同时根据墙的位置猜"我可能在这附近"。SLAM 就是这个过程的高速版。
- **源码对应**：本课程使用 `slam/car1_slam/launch/slam.launch.py` 启动的 slam_toolbox 就是干这个活的（详见实验 2）。

**建图三要素（1.4.2）**
- **原理**：一次建图循环包括三步：① **感知**——激光雷达发出激光，扫到墙反射回来，得到一圈"到障碍的距离"（/scan）；② **定位**——结合上一帧的位置和里程计，猜"我现在在哪"；③ **构图**——把这一圈的墙写进地图。机器人每走一小步，就重复一次这三步。
- **源码对应**：感知来自 `peripherals/car1_peripherals/launch/lidar.launch.py` 启动的 COIN-D6 雷达（发布 `/scan`，frame 为 `laser_link`，10Hz）。

**占据栅格地图（1.4.3）**
- **原理**：电脑里的地图是一张张"小方格"组成的，叫占据栅格地图（OccupancyGrid）。每个格子有三个取值：**-1 未知**（没扫到过）、**0 空闲**（确定没东西）、**100 占据**（确定有墙）。分辨率 `resolution: 0.05` 表示每格边长 5cm。
- **白话类比**：就像用方格纸画房间平面图——纸上的格子要么空着（空闲），要么涂黑（墙），要么没画（未知）。

**操作步骤**：

1. 阅读课程知识图谱 `EXP004_knowledge_graph.md` 第 1 章，理解四个核心概念。
2. 用自己的话说一遍："SLAM 为什么是鸡生蛋蛋生鸡？解决办法是什么？"写在实验笔记中。
3. 查一下雷达话题：`ros2 topic hz /scan`（有真机时执行，观察 ~10Hz）。

**易错点**：

- ⚠️ 把"定位"和"建图"当成两个独立问题 → **解决**：记住它们是互相依赖的循环，这是理解 SLAM 一切设计（回环检测、粒子滤波）的钥匙。

---

#### 步骤2：学习 URDF 语法（45min）

**知识点讲解**：

**URDF 结构（1.1.1 + 1.1.2）**
- **原理**：URDF（Unified Robot Description Format）用 XML 描述机器人。两个核心标签：**`<link>`** 表示机器人的一个"身体部件"（比如底盘、大腿、爪子），定义它的尺寸、颜色、惯性；**`<joint>`** 表示两个 link 怎么连接，决定它们之间能否运动：
  - `type="fixed"`：焊死，不能动（如 base_footprint → base_link）
  - `type="continuous"`：连续旋转，没有角度限制（如车轮）
  - `type="revolute"`：有限旋转，有角度上下限（如机械臂关节）
- **源码对应**：`simulations/car1_description/urdf/car1.urdf` L7-11 展示了 fixed 关节的例子：

```xml
<link name="base_footprint" />
<joint name="base_joint" type="fixed">
  <origin xyz="0 0 0.029" rpy="0 0 0" />
  <parent link="base_footprint" />
  <child link="base_link" />
</joint>
```

**TF 树（1.1.3）**
- **原理**：机器人所有坐标系的关系组成一棵"树"，叫 TF 树。URDF 加载后会自动生成：`base_footprint`（根）→ `base_link` → `laser_link`（雷达）/`imu_link`（IMU）/各机械臂关节。SLAM 和导航都靠查这棵树做坐标换算。
- **源码对应**：`bringup/launch/bringup.launch.py` L32-38 用 robot_state_publisher 加载 URDF 并发布静态 TF。

**Xacro 宏（1.2.1）**
- **原理**：Xacro 是 URDF 的"宏"语言。如果一辆车有 4 个相同的轮子，不用复制粘贴 4 遍，用 `<xacro:macro name="wheel">...</xacro:macro>` 定义一次，然后调用 4 次即可。改一个参数（如轮径）所有轮子一起变。
- **源码对应**：`simulations/car1_description/gazebo/car1.gazebo.xacro` 用 xacro 扩展了 Gazebo 仿真所需的物理属性。

**操作步骤**：

1. 打开 `car1.urdf`，数一数有多少个 `<link>` 和 `<joint>`（`grep -c "<link" car1.urdf`）。
2. 找 3 种关节类型各一个例子，记录它们的 parent/child。
3. 阅读 `display.launch.py`，说出它启动了哪三个节点（答案：joint_state_publisher_gui、robot_state_publisher、rviz2）。

**易错点**：

- ⚠️ 混淆 link 和 joint → **解决**：link 是"身体"，joint 是"关节/螺丝"，joint 永远连接两个 link（parent 和 child）。
- ⚠️ 以为 TF 是手动画的 → **解决**：URDF 加载后 TF 树自动生成，机器人坐标关系不用自己写代码。

---

#### 步骤3：解析 car1 模型结构（45min）

**知识点讲解**：

**car1 三大部分（1.3.1）**
- **原理**：`car1.urdf` 描述的 car1 机器人由三部分拼成：
  1. **主体**：`base_footprint` → `base_link`（底盘）+ 4 个麦轮（continuous 关节，麦轮 = 全向轮，能横着走）
  2. **机械臂**：`arm_link1` ~ `arm_link6` 的串联链（revolute 关节，每个关节一个舵机）
  3. **爪子**：末端夹爪（gripper），用来抓取物体
- **源码对应**：`car1.urdf` 中 base_joint（fixed）连接底盘；4 个轮子关节为 continuous；机械臂关节为 revolute。

**操作步骤**：

1. 打开 `car1.urdf`，从上到下浏览，圈出三大部分的 link/joint 名称。
2. 对照下表记录：

| 部分 | 代表 link | 关节类型 | 说明 |
|------|-----------|----------|------|
| 主体 | base_link | fixed/continuous | 底盘 + 4 麦轮 |
| 机械臂 | arm_link1~6 | revolute | 5 自由度舵机臂 |
| 爪子 | gripper | revolute | 末端夹爪 |

3. 思考题（记录在笔记）：为什么底盘要单独用 base_footprint 而不是直接 base_link 当根？（提示：base_footprint 表示"投影在地面的参考点"，方便 2D 导航）

**易错点**：

- ⚠️ 找不到机械臂关节 → **解决**：搜索 `type="revolute"` 关键字即可定位。
- ⚠️ 混淆"自由度"概念 → **解决**：revolute 关节数量 = 自由度，car1 机械臂 5 个旋转关节 = 5 自由度。

---

#### 步骤4：RViz 可视化验证（60min）

**知识点讲解**：

**display.launch.py 三件套（1.3.2）**
- **原理**：`display.launch.py` 一行命令启动三件事：
  1. **joint_state_publisher_gui**：启动一个 GUI 面板，每个关节一个滑块，拖动滑块就发布关节角度（/joint_states）
  2. **robot_state_publisher**：读 URDF + 关节角度，实时计算每个 link 的位姿，发布 TF
  3. **rviz2**：把 TF 画成 3D 模型显示在屏幕上
- **源码对应**：`simulations/car1_description/launch/display.launch.py` L17-36 依次启动三个节点。

**操作步骤**：

1. 启动可视化：
   ```bash
   source /opt/ros/humble/setup.bash
   source ~/ros2_ws/install/setup.bash
   ros2 launch car1_description display.launch.py
   ```
2. RViz 出现机器人模型后，操作：
   - 左侧面板展开 "JointStatePublisher"（或 Add 面板），拖动 arm_joint1~5 滑块 → 机械臂跟随
   - Add → By topic → /tf → 显示 TF 坐标轴
   - 点击 "Interact" 工具 → 拖拽模型任意部位观察
3. 验证 TF 树：
   ```bash
   ros2 run tf2_tools view_frames   # 生成 frames.pdf，用浏览器打开
   ```
   观察 base_footprint 是否为根，laser_link / imu_link 是否挂在 base_link 下。
4. 思考：如果把轮子关节滑块拖到极限，模型会怎样？为什么 continuous 关节没有角度限制？

**易错点**：

- ⚠️ RViz 只显示坐标轴看不到模型 → **解决**：左侧 Add → RobotModel → 选择 /robot_description 话题。
- ⚠️ 关节滑块拖不动 → **解决**：确认 joint_state_publisher_gui 已启动（display.launch 已包含），且 RViz 勾选了对应 Display。
- ⚠️ `ros2 launch` 报找不到包 → **解决**：先 `source ~/ros2_ws/install/setup.bash`，确认已 build car1_description。

---

#### 步骤5：建图环境认知（45min）

**知识点讲解**：

**建图环境构成（1.5.1）**
- **原理**：真正建图时，系统由四层组成（本实验只认识，不启动）：
  1. **驱动层** `bringup.launch.py`：底盘驱动 + 机器人状态发布 + EKF 里程计（把轮速 + IMU 融合成 odom TF）
  2. **雷达层** `lidar.launch.py`：发布 /scan
  3. **SLAM 算法层**：slam_toolbox（实验 2 详解）
  4. **可视化层**：RViz
- **源码对应**：`slam/car1_slam/launch/slam.launch.py` L36-59 正是这种分层结构。

**好地图标准（1.5.2）**
- **原理**：一张"好地图"长这样：墙是**单线**（没有重影）、尺寸误差 < 2%、墙角是**直角**、绕一圈回到起点时位置误差小（闭环成功）。这些指标在实验 2 会实际测量。
- **白话类比**：好地图 = 清晰、没有"重影"、比例尺准的房间平面图。

**操作步骤**：

1. 打开 `slam/car1_slam/launch/slam.launch.py`，对照四层结构找对应代码（bringup 包含 / lidar 包含 / TimerAction 10s slam_toolbox / rviz 节点）。
2. 打开 `slam/car1_slam/config/slam.yaml`，找到 `mode: mapping`、`resolution: 0.05`、`do_loop_closing: true` 三个参数。
3. 阅读 `slam/doc/slam_toobox_tutorial.md` 第 8 节"检验标准"，记录 4 个量化指标。
4. 在实验笔记中绘制"建图四层结构"图。

**易错点**：

- ⚠️ 把"建图"和"导航"混为一谈 → **解决**：建图（实验 2）产出地图，导航（实验 3-6）消费地图，先有图才能导。
- ⚠️ 以为分辨率越小越好 → **解决**：0.05（5cm）已足够室内导航；再小地图文件巨大、算力吃紧、收益有限。

### 1.7 注意事项

- ⚠️ 本实验**不需要真机**，纯软件即可完成（有真机可顺带验证 /scan 话题）。
- ⚠️ 若使用真机，display.launch 只加载模型不动电机，安全无风险。
- ⚠️ view_frames 生成的 frames.pdf 可用 `firefox frames.pdf` 或 VS Code 打开。

### 1.8 实验总结

**完成成果**：

- 理解 SLAM 的"鸡生蛋蛋生鸡"本质与建图三要素
- 掌握 URDF 的 link/joint/fixed/continuous/revolute 语法
- 成功在 RViz 中加载 car1 模型并拖动关节滑块
- 认识建图四层结构并记录好地图标准

**技能收获**：

- 技能1：SLAM 直觉理解（类比法）
- 技能2：URDF 模型阅读能力
- 技能3：RViz + TF 树可视化操作

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| RViz 无模型 | 未选择 RobotModel Display | Add → RobotModel |
| 关节拖不动 | joint_state_publisher_gui 未启动 | display.launch 已包含，检查终端输出 |
| launch 报包找不到 | 未 source install | `source ~/ros2_ws/install/setup.bash` |

### 1.9 实验报告要求

**思考题**：

1. SLAM 为什么是"鸡生蛋蛋生鸡"问题？解决这个矛盾的核心思路是什么？
2. `<joint type>` 的三种类型各适合什么场景？为什么车轮用 continuous、机械臂用 revolute？
3. 占据栅格地图中 -1/0/100 分别代表什么？分辨率 0.05 表示什么？
4. 为什么导航前必须先建图？地图质量差会对导航产生什么影响？

**评分标准**：SLAM 原理理解 20 分 + URDF 语法 20 分 + car1 模型解析 20 分 + RViz 可视化操作 25 分 + 报告与思考题 15 分 = 100 分。
