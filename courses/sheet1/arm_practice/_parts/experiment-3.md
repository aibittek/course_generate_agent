## 实验3：机械臂ROS2架构认知与动作回放实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/`，未复制到 `source-codes/EXP005/exp03/`。已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。后续补充源码后需触发 SourceCodeAnalysisAgent 并移除豁免。本指导书 v1.2 改用 `bringup.launch.py` + `action_player` 节点路线（原 v1.1 的 test_servo_direct 录制迁移至 exp02），按 **3a（系统架构认知）→ 3b（动作回放）→ 3c（零位校准）** 三子阶段组织内容。**严禁使用** `/arm_controller/target_pose`（自动 IK）和 `/arm_controller/pick`/`/arm_controller/place`（完整抓取 pipeline）——这些接口将在 exp05/exp06 讲解，本实验仅使用 `joint_command` 话题和 `action_player` 节点（详见 1.6 步骤 3b）。

### 1.1 关联知识点

本实验对应第 3 章"机械臂 ROS2 架构与动作回放"，覆盖以下 10 个知识点：

- 3.1.1 bringup拓扑 > 概念 > `bringup.launch.py` 启动 7~8 个节点的拓扑结构（base_driver / robot_state_publisher / joint_state_publisher / imu_filter / odom_publisher / ekf_filter_node / servo_controller / init_pose）
- 3.1.2 rqt_graph > 流程 > 用 rqt_graph 插件观察 topic/service 的有向图，识别节点间的发布/订阅关系
- 3.1.3 node list/topic list > 流程 > `ros2 node list` / `ros2 topic list` / `ros2 service list` 三大命令快速勘察运行时系统
- 3.2.1 joint_command话题 > 原理 > `/arm_controller/joint_command` 接收 JointState 消息，position 字段为弧度（非 PWM），通过内部 PWM_TO_RAD=0.002356 换算后下发串口
- 3.2.2 PWM↔rad换算 > 原理 > 公式 `rad = (PWM - 1500) × 0.002356`（等价 `PWM = rad / 0.002356 + 1500`），由 arm_controller 内部自动完成
- 3.3.1 action_player节点 > 概念 > `action_player` 是 **节点**（非 launch），通过 console_scripts 注册为可执行命令；接收 YAML 动作文件并按顺序回放
- 3.3.2 YAML格式兼容 > 原理 > 导出的 YAML 字段 `name`/`description`/`actions[].name`/`actions[].duration`/`actions[].servos` 与 exp02 的 `export_yaml` 严格兼容
- 3.3.3 回放模式 > 概念 > 普通（play 服务）、单步（~/next 服务）、循环（启动时 loop:=true）、急停（~/stop 服务）四种控制方式
- 3.4.1 软件offset > 原理 > 软件层 offset 补偿（写入 `servo_offsets.yaml`）相比 EEPROM 写入更安全、可热更新，舵机寿命 10 万次
- 3.4.2 servo_calib GUI > 流程 > `servo_calib.launch.py` 启动校准 GUI 逐关节拖动滑块找机械中位并写入 offset

### 1.2 实验目标

1. 理解 `bringup.launch.py` 启动的 7~8 个 ROS2 节点的拓扑结构与协作关系 — 原理理解
2. 掌握用 `ros2 node list` / `ros2 topic list` / `rqt_graph` 勘察运行时系统的方法 — 流程掌握
3. 掌握 `/arm_controller/joint_command` 话题发送 5 关节弧度的用法（**严禁用 target_pose 触发 IK**）— 流程掌握
4. 独立使用 `action_player` 节点回放 exp02 导出的 `pick_and_place.yaml` 动作文件 — 独立完成
5. 掌握修改 YAML 某步参数后重新 colcon build 并回放观察差异的方法 — 迁移应用
6. 理解 `servo_calib` 校准 GUI 的工作流程，能用软件 offset 补偿消除装配偏差 — 流程掌握

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 机器人小车C1（含 5 自由度机械臂、工作桌面、待抓取物体） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 + rclpy |
| 核心工具 | rqt_graph、rqt_topic、ros2 cli |
| 动作文件 | `arm/car1_arm_controller/config/actions/pick_and_place.yaml`（**由 exp02 生成**） |
| 校准文件 | `calibration/config/servo_offsets.yaml` |
| **主入口** | `bringup/launch/bringup.launch.py`（启动 7~8 个节点）<br>`arm/car1_arm_controller/launch/arm_controller.launch.py`（启动 arm_controller，**仅用 joint_command**）<br>`arm/car1_arm_controller/car1_arm_controller/action_player.py`（**节点**而非 launch）<br>`calibration/launch/servo_calib.launch.py`（3c 阶段校准 GUI） |

> ⚠️ **严禁使用** `/arm_controller/target_pose` 话题（会自动调用 IK 解算）、`/arm_controller/pick` 与 `/arm_controller/place` 服务（会执行完整抓取 pipeline）—— 这些是 exp05/exp06 的内容。

### 1.4 实验难度

- 难度: ⭐⭐ 中
- 重点: ROS2 节点拓扑观察；`joint_command` 话题；`action_player` 节点回放；YAML 修改热更新；软件 offset 校准
- 难点: 区分 `action_player` 节点与 `action_player.launch.py`（本实验使用的是**节点**）；区分 `joint_command` 弧度与原始 PWM；rqt_graph 大量节点的可视化阅读

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：

1. 连接硬件：确保机械臂通电、串口连接到工作站
2. 进入工作空间根目录：`cd ~/ros2_ws`
3. source 环境：`source /opt/ros/humble/setup.bash && source install/setup.bash`
4. 启动 bringup（新终端）：`ros2 launch car1_bringup bringup.launch.py`
5. 启动 arm_controller（新终端）：`ros2 launch car1_arm_controller arm_controller.launch.py`
6. 观察节点列表（新终端）：`ros2 node list`
7. 启动 action_player（新终端）：`ros2 run car1_arm_controller action_player --ros-args -p action_file:=pick_and_place.yaml`
8. 触发普通回放（新终端）：`ros2 service call /action_player/play std_srvs/srv/Trigger`
9. 观察终端日志：依次执行 pre_grasp → gripper_open → grasp_down → gripper_close → lift → back_work，机械臂在 6~10 秒内完成整个抓取循环
10. 修改 YAML 中 gripper_open 的 PWM 从 1000 改为 1200，重新 `colcon build` 并重放，观察夹爪张开角度变小

**预期效果描述**：
- **架构阶段**：rqt_graph 弹出后显示有向图，可清晰看到 `servo_controller` → `/servo_command` → 串口 的链路，以及 `arm_controller` 订阅 `/arm_controller/joint_command` 的输入边
- **回放阶段**：action_player 节点按 YAML 顺序执行，6~10 秒完成一个完整抓放循环，每次执行 5 个舵机同时平滑转动
- **循环模式**：加 `loop:=true` 参数后无限循环，按 Ctrl+C 停止
- **单步模式**：调用 `/action_player/next` 服务后每步需手动按一次 Enter 才会执行下一步
- **急停模式**：调用 `/action_player/stop` 服务后立即中断后续动作，机械臂停在当前位置
- **校准阶段**：servo_calib GUI 弹出后，5 个滑块分别控制 5 个关节，拖动滑块找机械中位后 Apply，offset 写入 `servo_offsets.yaml`

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：启动bringup观察拓扑] --> B[步骤2：joint_command话题控制]
    B --> C[步骤3a：系统架构认知30min]
    C --> D[步骤3b：动作回放2h]
    D --> E[步骤3c：零位校准1.5h]
    E --> F[完成]
```

---

#### 步骤1：启动 bringup 并观察节点拓扑（阶段 3a：能理解，20min）

> ⚠️ 本步骤对应 src 目录源码：`ros2_ws/src/xflz_eai_car1/bringup/launch/bringup.launch.py`

**知识点讲解**：

**bringup 启动的 7~8 个节点（3.1.1）**
- **原理**：`bringup.launch.py` 是 car1 系统的"一站式启动入口"，会拉起 7~8 个 ROS2 节点构成完整的小车+机械臂系统。每个节点负责一个独立的功能模块：
  - `base_driver`：串口桥接，把 `/cmd_vel` 转成底盘串口指令并发布 `/odom`
  - `robot_state_publisher`：把 URDF 转成 TF 树
  - `joint_state_publisher`：发布 `/joint_states`
  - `imu_filter`：IMU 数据滤波
  - `odom_publisher`：轮式里程计
  - `ekf_filter_node`：EKF 融合 IMU + 里程计
  - `servo_controller`：舵机串口桥接，接收 `/servo_command` 发往 5 关节
  - `init_pose`：初始化位姿
- **源码对应**：`bringup.launch.py` 中各 `<node>` 标签

**用 rqt_graph 观察节点拓扑（3.1.2）**
- **原理**：`rqt_graph` 是 ROS2 官方提供的可视化插件，动态显示当前所有节点、话题、服务的有向图。**节点是圆圈、话题是方框、订阅/发布关系是有向箭头**。这种可视化能帮助快速理解"谁在和谁通信"。在 rqt_graph 中可以拖动节点、过滤话题、按 namespace 折叠。
- **源码对应**：系统级工具，无需源码

**操作步骤**：

1. 进入工作空间并 source 环境：
   ```bash
   cd ~/ros2_ws
   source /opt/ros/humble/setup.bash
   source install/setup.bash
   ```

2. 启动 bringup：
   ```bash
   ros2 launch car1_bringup bringup.launch.py
   # 预期：终端打印 7~8 个节点的启动日志
   # [INFO] [base_driver-1]: process started with pid [12345]
   # [INFO] [robot_state_publisher-2]: process started
   # ...
   ```

3. 查看所有运行中的节点（新终端）：
   ```bash
   ros2 node list
   # 预期输出（7~8 个）：
   # /base_driver
   # /robot_state_publisher
   # /joint_state_publisher
   # /imu_filter
   # /odom_publisher
   # /ekf_filter_node
   # /servo_controller
   # /init_pose
   ```

4. 查看所有话题：
   ```bash
   ros2 topic list
   # 预期：/cmd_vel /odom /joint_states /imu/data /servo_command /tf /tf_static 等
   ```

5. 启动 rqt_graph：
   ```bash
   rqt_graph
   # 预期：弹出可视化窗口，显示节点+话题+箭头
   # 关键观察：servo_controller → /servo_command（箭头）→ 串口
   ```

6. 启动 rqt_graph 高级视图（启用 Node-Graph 选项）：
   - 在 rqt_graph 窗口菜单 `View` → 勾选 `Node-Graph (debug)`
   - 可看到节点内部的发布/订阅回调函数

7. 验证 `/joint_states` 频率：
   ```bash
   ros2 topic hz /joint_states
   # 预期：约 50Hz
   ```

8. （**可选**）启动 arm_controller（步骤 3b 才会用）：
   ```bash
   ros2 launch car1_arm_controller arm_controller.launch.py
   # 预期：arm_controller 节点启动
   ros2 node list
   # 预期：增加 /arm_controller 节点
   ```

**易错点**：
- ⚠️ **rqt_graph 启动后无显示** → **解决**：先 `ros2 run` 一个节点（如 `ros2 topic pub /cmd_vel ...`），节点至少有一个订阅/发布时才会显示
- ⚠️ **看不到 arm_controller** → **解决**：arm_controller 由 `arm_controller.launch.py` 单独启动（不在 bringup 中），需手动 `ros2 launch car1_arm_controller arm_controller.launch.py`
- ⚠️ **节点数 < 7** → **解决**：检查 `bringup.launch.py` 是否完整 source，所有依赖包是否 `colcon build`

---

#### 步骤2：用 joint_command 话题控制 5 关节（阶段 3b 准备，30min）

> ⚠️ 本步骤对应 src 目录源码：`ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/car1_arm_controller/arm_controller.py`

**知识点讲解**：

**joint_command 话题（3.2.1）**
- **原理**：`/arm_controller/joint_command` 是 `arm_controller` 节点订阅的**关节角控制话题**，消息类型为 `sensor_msgs/msg/JointState`。关键字段：
  - `name`：关节名列表，必须为 `['arm_joint1', 'arm_joint2', 'arm_joint3', 'arm_joint4', 'arm_joint5']`
  - `position`：5 个关节目标**弧度**（rad），不是 PWM
  - `effort`（可选）：5 个关节的 duration 参数（秒），控制运动时间
- **源码对应**：`arm_controller.py` 中 `def joint_command_callback(self, msg)` 函数

**PWM ↔ 弧度换算（3.2.2）**
- **原理**：exp02 学习的 PWM 范围 500~2500、中位 1500、PWM_TO_RAD=0.002356 在本节点内**自动完成**。换算公式为：
  - `rad = (PWM - 1500) × 0.002356`
  - `PWM = rad / 0.002356 + 1500`
  - 例：PWM=1500（home）→ rad=0；PWM=1850 → rad=(1850-1500)×0.002356=0.8246 rad ≈ 47.2°
- **源码对应**：`arm_controller.py` 中 `self.PWM_TO_RAD = 0.002356` 常量

**为什么不用 target_pose 话题（教学顺序隔离）**
- **原理**：`/arm_controller/target_pose` 接收 `geometry_msgs/msg/PoseStamped`（末端目标位姿），由 arm_controller 内部调用 IK 解算（`solve_analytical_ik_auto_pitch`）转为 5 关节角再下发。**本实验还未学习 IK**（exp04/exp05 才会学），若用 target_pose 会导致：(1) 跳过 joint_command 的原理理解；(2) 不知道 IK 求解细节；(3) 不符合"螺旋式能力构建"教学顺序。
- **源码对应**：`arm_controller.py` 中 `def target_pose_callback(self, msg)` 函数（**本实验不调用**）

**操作步骤**：

1. 确认 arm_controller 已运行（步骤 1 末尾或重新启动）：
   ```bash
   ros2 launch car1_arm_controller arm_controller.launch.py
   # 预期：arm_controller 节点订阅 /arm_controller/joint_command
   ros2 node info /arm_controller | grep -A 5 "Subscribers"
   # 预期：/arm_controller/joint_command: sensor_msgs/msg/JointState
   ```

2. **测试 home 位姿**（5 关节全 0 rad）：
   ```bash
   ros2 topic pub /arm_controller/joint_command sensor_msgs/msg/JointState \
     "{name: ['arm_joint1','arm_joint2','arm_joint3','arm_joint4','arm_joint5'], position: [0.0, 0.0, 0.0, 0.0, 0.0], effort: [2.0]}" --once
   # 预期：机械臂回中位，duration 2 秒
   ```

3. **测试 work 位姿**（弧度来自 exp02 公式换算）：
   ```bash
   ros2 topic pub /arm_controller/joint_command sensor_msgs/msg/JointState \
     "{name: ['arm_joint1','arm_joint2','arm_joint3','arm_joint4','arm_joint5'], position: [0.0, -0.943, 1.65, 0.8246, 0.0], effort: [2.0]}" --once
   # 预期：5 关节转到 work 位姿 [1500, 1100, 2200, 1850, 1500] PWM
   # 换算：1500-1500=0, 1100-1500=-400×0.002356=-0.943, 2200-1500=700×0.002356=1.65, 1850-1500=350×0.002356=0.8246
   ```

4. **测试自定义位姿**：
   ```bash
   # 任意目标弧度，例如 J2 抬高 30°（J2 从 0 到 0.524 rad = 30°）
   ros2 topic pub /arm_controller/joint_command sensor_msgs/msg/JointState \
     "{name: ['arm_joint1','arm_joint2','arm_joint3','arm_joint4','arm_joint5'], position: [0.0, 0.524, 0.0, 0.0, 0.0], effort: [1.5]}" --once
   # 预期：J2 单独抬升 30°（PWM=1500+0.524/0.002356=1722）
   ```

5. **观察 5 关节同步运动**：
   ```bash
   ros2 topic echo /joint_states --once
   # 预期：name=['arm_joint1',...], position=[0, 0.524, 0, 0, 0]
   ```

6. **测试夹爪**（可选，3b 阶段详细用）：
   ```bash
   # 夹爪属于 gripper_controller 节点，不是 arm_controller
   # 通过 /gripper_controller/gripper_cmd 话题控制
   ros2 topic pub /gripper_controller/gripper_cmd std_msgs/msg/Float64 "{data: 0.0}" --once
   # 预期：夹爪张开（0.0=全开）
   ```

**易错点**：
- ⚠️ **使用 target_pose 报错"no IK solution"** → **解决**：本实验严禁用 target_pose，改用 joint_command 直接发弧度
- ⚠️ **机械臂不动** → **解决**：检查 arm_controller 是否运行；检查 `effort` 字段是否 ≥ 0.5（duration 太小舵机来不及响应）
- ⚠️ **机械臂撞限位** → **解决**：把 `position` 限制在软限位内（如 J2 范围约 -1.5~+1.5 rad）
- ⚠️ **弧度与 PWM 搞混** → **解决**：joint_command 用弧度，不是 PWM；用公式 `rad = (PWM-1500)×0.002356` 换算

---

#### 步骤3a：系统架构认知（30min）

> ⚠️ 本步骤是阶段 3a 的浓缩，承接步骤 1 的 bringup 启动，重点理解节点间的消息流。

**学习目标**：
- 能用 `rqt_graph` 画出节点-话题-服务的有向图
- 区分"发布者"、"订阅者"、"话题"、"服务"四类对象
- 理解 `servo_controller` 在系统中的位置（串口桥接点）

**操作步骤**：

1. **绘制完整系统图**：
   ```bash
   rqt_graph
   # 预期看到：
   # /base_driver ─pub─> /cmd_vel ─sub─> 底盘
   # /servo_controller ─pub─> /servo_command ─sub─> 串口
   # /arm_controller ─sub─> /arm_controller/joint_command
   # /joint_state_publisher ─pub─> /joint_states
   # /ekf_filter_node ─sub─> /imu/data + /odom, ─pub─> /odom/filtered
   ```

2. **观察 topic 频率**（用 rqt_topic 或 hz 命令）：
   ```bash
   ros2 topic hz /joint_states    # 预期 50Hz
   ros2 topic hz /odom             # 预期 30~50Hz
   ros2 topic hz /imu/data         # 预期 100~200Hz
   ```

3. **观察 topic 带宽**：
   ```bash
   ros2 topic bw /joint_states
   # 预期：约 2~5 KB/s
   ```

4. **查看节点间的 QoS 兼容性**：
   ```bash
   ros2 topic info /joint_states --verbose
   # 预期：Reliability: RELIABLE, Durability: VOLATILE, History: KEEP_LAST, Depth: 10
   ```

5. **理解 `servo_controller` 的关键地位**：
   - 它是软件与硬件的**唯一**桥接点
   - 所有上层节点（arm_controller、joint_state_publisher）都通过它间接控制串口
   - 关闭它则整个机械臂失联

**易错点**：
- ⚠️ **rqt_graph 看不到所有节点** → **解决**：rqt_graph 默认 1 秒刷新，可点击 🔄 强制刷新
- ⚠️ **节点连成一片糊** → **解决**：在 rqt_graph 菜单 `Nodes` → `Hide` 隐藏底盘/IMU 相关节点，只看机械臂部分

---

#### 步骤3b：动作回放（2h）

> ⚠️ 本步骤对应 src 目录源码：`ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/car1_arm_controller/action_player.py`

**知识点讲解**：

**action_player 节点（3.3.1）**
- **原理**：`action_player` 是 `car1_arm_controller` 包中通过 `console_scripts` 注册的**可执行节点**（不是 launch 文件！）。在 `setup.py` 中注册为 `action_player = car1_arm_controller.action_player:main`，因此可以用 `ros2 run car1_arm_controller action_player` 启动。节点启动时接收 `action_file` 参数指定 YAML 路径，内部解析 YAML 并按顺序回放。
- **源码对应**：`setup.py` 中 `entry_points={'console_scripts': ['action_player = car1_arm_controller.action_player:main']}`

**YAML 格式兼容（3.3.2）**
- **原理**：action_player 读取的 YAML 结构由 `action_player.py` 的 `_load_action` 函数定义，**必须与 exp02 的 `export_yaml` 输出一致**：
  ```yaml
  name: <动作组名>
  description: <描述>
  actions:
    - name: <步名>
      duration: <秒>
      servos: {<id>: <pwm>, ...}
  ```
  字段名严格区分大小写，duration 单位是**秒**（不是毫秒），servos 的键是舵机 ID 字符串（"0"~"5"）。
- **源码对应**：`action_player.py` 中 `def _load_action(yaml_path)` 函数（L90-120）

**回放模式（3.3.3）**
- **原理**：action_player 提供 4 种控制方式：
  - **普通（play）**：调用 `/action_player/play` 服务后按顺序执行
  - **单步（next）**：每次调用 `/action_player/next` 服务执行一步
  - **循环（loop）**：节点启动时加 `-p loop:=true` 参数
  - **急停（stop）**：调用 `/action_player/stop` 服务立即中断
- **源码对应**：`action_player.py` 中各 `srv_callback` 函数

**操作步骤**：

1. **确认 exp02 已生成 pick_and_place.yaml**：
   ```bash
   ls -l ~/ros2_ws/install/car1_arm_controller/share/car1_arm_controller/config/actions/pick_and_place.yaml
   # 预期：文件存在
   # 若不存在：回到 exp02 重新执行 yaml 导出
   ```

2. **启动 action_player 节点**（**注意是节点不是 launch**）：
   ```bash
   ros2 run car1_arm_controller action_player \
     --ros-args -p action_file:=pick_and_place.yaml
   # 预期：终端打印 "Loaded N actions from pick_and_place.yaml"
   # 节点启动后处于等待状态，等待 /action_player/play 服务
   ```

3. **查看 action_player 提供的服务**：
   ```bash
   ros2 service list | grep action_player
   # 预期：
   # /action_player/play
   # /action_player/next
   # /action_player/stop
   ```

4. **触发普通回放**：
   ```bash
   ros2 service call /action_player/play std_srvs/srv/Trigger
   # 预期：节点开始按 YAML 顺序执行，机械臂在 6~10 秒完成整个抓取循环
   # 终端打印：
   #   [INFO] Playing action 1/6: pre_grasp
   #   [INFO] Playing action 2/6: gripper_open
   #   ...
   #   [INFO] All actions completed
   ```

5. **观察执行进度**：
   ```bash
   ros2 topic echo /action_player/progress
   # 预期：current_index, total_count, current_action_name, status
   ```

6. **修改 YAML 某步参数**：
   ```bash
   # 假设 pick_and_place.yaml 在 install 目录下
   nano ~/ros2_ws/install/car1_arm_controller/share/car1_arm_controller/config/actions/pick_and_place.yaml
   # 把 gripper_open 的 PWM 从 1000 改为 1200（夹爪张开角度更大）
   # 改前：  - name: gripper_open  duration: 1.0  servos: {0: 1500, 1: 1100, 2: 2200, 3: 1850, 4: 1500, 5: 1000}
   # 改后：  - name: gripper_open  duration: 1.0  servos: {0: 1500, 1: 1100, 2: 2200, 3: 1850, 4: 1500, 5: 1200}
   ```

7. **重新编译安装**（**必须！**）：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select car1_arm_controller
   source install/setup.bash
   # 预期：编译成功
   ```

8. **重启 action_player 并重放**：
   ```bash
   # Ctrl+C 停止原 action_player
   ros2 run car1_arm_controller action_player --ros-args -p action_file:=pick_and_place.yaml
   ros2 service call /action_player/play std_srvs/srv/Trigger
   # 预期：夹爪张开角度比之前大（因为 PWM 1000→1200）
   ```

9. **单步模式**：
   ```bash
   # 重启 action_player，加 step_mode 参数
   ros2 run car1_arm_controller action_player \
     --ros-args -p action_file:=pick_and_place.yaml -p step_mode:=true
   # 每次调用 next 服务执行一步
   ros2 service call /action_player/next std_srvs/srv/Trigger
   # 预期：执行 step 1，等待
   ros2 service call /action_player/next std_srvs/srv/Trigger
   # 预期：执行 step 2，等待
   # ...
   ```

10. **循环模式**：
    ```bash
    # Ctrl+C 停止，启动循环模式
    ros2 run car1_arm_controller action_player \
      --ros-args -p action_file:=pick_and_place.yaml -p loop:=true
    # 节点启动后自动开始循环播放
    # 按 Ctrl+C 停止
    ```

11. **急停模式**：
    ```bash
    # 在循环播放中（新终端）
    ros2 service call /action_player/stop std_srvs/srv/Trigger
    # 预期：节点立即停止后续动作，机械臂停在当前位置
    ```

**易错点**：
- ⚠️ **"找不到 action_player 命令"** → **解决**：必须 `colcon build --packages-select car1_arm_controller` 后 `source install/setup.bash`
- ⚠️ **play 服务无响应** → **解决**：检查 YAML 路径是否正确（用 `ros2 pkg prefix car1_arm_controller` 获取 share 路径）
- ⚠️ **修改 YAML 后重放没变化** → **解决**：必须重新 `colcon build` 才会复制到 install 目录
- ⚠️ **循环模式停不下来** → **解决**：`ros2 service call /action_player/stop` 或 `kill -9 $(pgrep -f action_player)`
- ⚠️ **误用 target_pose 触发 IK** → **解决**：本实验严禁 target_pose，仅用 joint_command 话题

---

#### 步骤3c：零位校准（1.5h）

> ⚠️ 本步骤对应 src 目录源码：`ros2_ws/src/xflz_eai_car1/calibration/launch/servo_calib.launch.py`、`ros2_ws/src/xflz_eai_car1/calibration/config/servo_offsets.yaml`

**知识点讲解**：

**软件 offset 方案（3.4.1）**
- **原理**：car1 采用"软件层 offset"方案：(1) **不修改舵机 EEPROM**：原始中位 1500 保持不变；(2) **在 arm_controller 中应用 offset**：实际发送的 PWM = 目标 PWM + offset。例如机械中位实际在 PWM=1522，则 offset=22，所有目标 PWM 加上 22 才是"软件 0 rad"。这种方案的优势是：(1) 损坏时容易恢复（删除 offset 文件即可）；(2) 可热更新（修改 yaml 后重启节点即可）；(3) 不影响其他使用相同舵机的项目。舵机 EEPROM 寿命约 10 万次写入，软件 offset 可视为"无限寿命"。
- **源码对应**：`arm_controller.py` 中 `self.current_pwms[i] += self.offsets[i]`

**servo_calib 校准 GUI（3.4.2）**
- **原理**：`servo_calib.launch.py` 启动一个图形化 GUI 工具，提供 5 个关节的独立控制面板。界面包括：(1) 关节选择标签（joint1~joint5）；(2) PWM 滑块（500-2500）；(3) 实时位置显示（rad/deg）；(4) "Save" 按钮（写入 `servo_offsets.yaml`）。校准流程为：选择关节 → 缓慢移动滑块 → 找到机械中位 → 记录偏差 → 保存。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/calibration/launch/servo_calib.launch.py`

**操作步骤**：

1. **编译校准包**：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select calibration
   source install/setup.bash
   ```

2. **启动 arm_controller**（必须先运行）：
   ```bash
   ros2 launch car1_arm_controller arm_controller.launch.py
   ```

3. **启动 servo_calib**（新终端）：
   ```bash
   ros2 launch calibration servo_calib.launch.py
   # 预期：弹出 GUI 窗口，包含 5 个关节的控制面板
   ```

4. **校准 joint2（大臂）**：
   - 在 GUI 中选择"Joint 2"
   - 缓慢拖动 PWM 滑块从 1400 到 1600
   - 观察大臂姿态，找到"大臂水平向前"的位置
   - 读取该位置的 PWM 值（例如 1522）
   - 在 "Offset" 输入框填入 22
   - 点击 "Apply"

5. **校准 joint3（小臂）**：
   - 类似方法找到"小臂水平"的 PWM 值（例如 1513）
   - offset = 1513 - 1500 = 13
   - 填入 13 并 Apply

6. **校准剩余关节**（可选）：
   - joint1（底座）：offset 通常为 0（旋转对称）
   - joint4/5（腕部）：offset 视具体装配而定

7. **保存配置**：
   - 点击 "Save All" 按钮
   - 检查 `servo_offsets.yaml` 已更新

8. **验证 offset 已写入**：
   ```bash
   cat ~/ros2_ws/src/xflz_eai_car1/calibration/config/servo_offsets.yaml
   # 预期：joint2: 22, joint3: 13
   ```

9. **验证校准后归零对齐**（**用 joint_command 不用 target_pose**）：
   ```bash
   ros2 topic pub /arm_controller/joint_command sensor_msgs/msg/JointState \
     "{name: ['arm_joint1','arm_joint2','arm_joint3','arm_joint4','arm_joint5'], position: [0.0, 0.0, 0.0, 0.0, 0.0], effort: [2.0]}" --once
   # 预期：机械臂 5 关节全部转到"软件 0 rad"位置，视觉上对齐（水平、垂直）
   # 此时 arm_controller 内部实际发送的 PWM = [1500+offset1, 1500+offset2, ...]
   ```

10. **备份与回滚**：
    ```bash
    cp ~/ros2_ws/src/xflz_eai_car1/calibration/config/servo_offsets.yaml servo_offsets.yaml.bak
    # 若校准后异常，恢复：cp servo_offsets.yaml.bak servo_offsets.yaml
    ```

**易错点**：
- ⚠️ **校准后机械臂仍不齐** → **解决**：校准是渐进过程，可能需要"先粗调后精调"多轮迭代
- ⚠️ **GUI 启动报"display not found"** → **解决**：在工作站本地终端运行，不要通过 SSH 远程
- ⚠️ **Apply 后无响应** → **解决**：检查 arm_controller 是否运行，servo_calib 需要订阅 `/arm_controller/joint_states`
- ⚠️ **验证用 target_pose** → **解决**：本实验严禁 target_pose，验证用 joint_command 发 0 rad

---

#### 完整可运行代码 demo_action_player_pubsub.py

> 独立 demo 脚本：用 rclpy 编写一个客户端，调用 action_player 的 play/next/stop 服务

```python
# -*- coding: utf-8 -*-
"""
实验3 demo：action_player 服务化控制 demo
平台：B2 / C1
前置：ros2 launch car1_bringup bringup.launch.py 与 ros2 launch car1_arm_controller arm_controller.launch.py 已运行
     ros2 run car1_arm_controller action_player --ros-args -p action_file:=pick_and_place.yaml 已运行
运行：python3 demo_action_player_pubsub.py
"""
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
import time


class ActionPlayerClient(Node):
    """action_player 服务客户端（普通/单步/急停）"""
    
    def __init__(self):
        super().__init__('action_player_client')
        self.play_cli = self.create_client(Trigger, '/action_player/play')
        self.next_cli = self.create_client(Trigger, '/action_player/next')
        self.stop_cli = self.create_client(Trigger, '/action_player/stop')
        
        for cli, name in [(self.play_cli, 'play'),
                          (self.next_cli, 'next'),
                          (self.stop_cli, 'stop')]:
            while not cli.wait_for_service(timeout_sec=1.0):
                self.get_logger().info(f'Waiting for /action_player/{name}...')
    
    def call_play(self):
        """普通回放：一次执行所有 actions"""
        future = self.play_cli.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future)
        return future.result()
    
    def call_next(self):
        """单步模式：执行下一步"""
        future = self.next_cli.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future)
        return future.result()
    
    def call_stop(self):
        """急停：立即停止"""
        future = self.stop_cli.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future)
        return future.result()


def main():
    rclpy.init()
    node = ActionPlayerClient()
    
    print('=== action_player 控制 Demo ===')
    print('1. 普通回放（一次执行全部）')
    print('2. 单步模式（每步按 Enter）')
    print('3. 急停演示（5秒后自动停止）')
    
    choice = input('请选择 (1/2/3): ')
    
    if choice == '1':
        print('触发普通回放...')
        result = node.call_play()
        print(f'结果: success={result.success}, message="{result.message}"')
    
    elif choice == '2':
        n = int(input('请输入步数（YAML 中 action 数量）: '))
        for i in range(n):
            input(f'按 Enter 执行 step {i+1}...')
            result = node.call_next()
            print(f'  step {i+1}: success={result.success}')
    
    elif choice == '3':
        print('触发普通回放，5 秒后急停...')
        node.call_play()
        time.sleep(5.0)
        print('急停!')
        result = node.call_stop()
        print(f'急停结果: success={result.success}')
    
    else:
        print('Bye')
    
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 1.7 实验总结

**完成成果**：
- 理解 `bringup.launch.py` 启动的 7~8 个节点拓扑结构与协作关系
- 掌握用 `rqt_graph` 绘制节点-话题-服务有向图的方法
- 掌握用 `joint_command` 话题发送 5 关节弧度控制机械臂（**不触发 IK**）
- 独立使用 `action_player` 节点回放 exp02 导出的 `pick_and_place.yaml`
- 掌握修改 YAML 某步 PWM 后 `colcon build` 热更新并重放观察差异的方法
- 掌握 `servo_calib` 校准 GUI 的工作流程，能用软件 offset 补偿消除装配偏差
- 理解 4 种回放模式（普通/单步/循环/急停）的适用场景

**技能收获**：
- 掌握 ROS2 节点架构的可视化分析（rqt_graph）
- 区分 **action_player 节点** vs 常见的 action_player.launch.py
- 理解 `joint_command`（弧度）vs `target_pose`（末端位姿）的本质差异与教学顺序隔离
- 掌握动作文件的 YAML 结构、字段含义、热更新流程
- 掌握软件 offset 方案（不写 EEPROM、可热更新）

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 找不到 action_player 命令 | 未编译 | `colcon build --packages-select car1_arm_controller` |
| play 服务无响应 | YAML 路径错误 | 用 `ros2 pkg prefix car1_arm_controller` 获取 share 路径 |
| 修改 YAML 后重放没变化 | 未重新 colcon build | 必须 `colcon build` 才会复制到 install |
| 循环模式停不下来 | stop 服务未调用 | `ros2 service call /action_player/stop` 或 `kill -9` |
| 误用 target_pose 触发 IK | 教学顺序混淆 | 本实验严禁 target_pose，仅用 joint_command 话题 |
| 校准后仍不齐 | 渐进式校准未完成 | 多轮迭代粗调+精调 |
| servo_calib 报"display not found" | SSH 远程无显示 | 在工作站本地终端运行 |
| rqt_graph 不显示节点 | 节点刚启动未连接 | 点击 🔄 强制刷新或发布任意消息激活节点 |

### 1.8 思考题

1. `bringup.launch.py` 启动的 7~8 个节点中，哪些是"输入"（订阅命令），哪些是"输出"（发布状态）？画出完整的有向数据流图。
2. `action_player` 是节点还是 launch？为什么 ROS2 项目中既需要 launch（启动多节点）又需要节点（独立可执行）？两者各适合什么场景？
3. `joint_command` 话题用 `position` 字段（弧度）而不是 `PWM`，这种"应用层 vs 设备层"的抽象隔离有什么好处？如果直接发 PWM 会有什么问题？
4. 为什么不直接调用 `/arm_controller/target_pose`（更直观），而必须用 `joint_command`（更底层）？在什么教学阶段应该切换到 target_pose？
5. 软件 offset 方案相比直接写入舵机 EEPROM 有什么优缺点？在什么场景下必须使用 EEPROM 写入？
6. 命名快照（snapshot）与动作文件（action）的本质区别是什么？能否将两者合并为同一数据结构？
7. 单步模式适合哪些调试场景？为什么自动化测试通常不采用单步模式？
8. 急停后机械臂缓慢下垂的物理原因是什么？工业机械臂如何避免这个问题？

### 1.9 实验报告要求

**评分标准**：bringup 节点拓扑观察 15 分 + joint_command 弧度控制 15 分 + rqt_graph 架构图 10 分 + action_player 节点回放 20 分 + YAML 修改热更新 15 分 + servo_calib 校准 15 分 + 实验报告 10 分 = 100 分。

**实验报告必含项**：
- [ ] `rqt_graph` 截图（标注 7~8 个节点的关键链路：`servo_controller` → `/servo_command` → 串口）
- [ ] `joint_command` 控制 5 关节的录屏或截图（**严禁用 target_pose**）
- [ ] `action_player` 普通回放的录屏（机械臂完成 pre_grasp→gripper_open→...→back_work 全过程）
- [ ] YAML 修改前后夹爪张开角度对比图（修改 gripper_open PWM 从 1000→1200）
- [ ] servo_calib GUI 校准 joint2 截图与 offset 写入验证
- [ ] 思考题 8 题全部作答

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初版生成（基于 _registry.yaml human_waiver 模式，标注 [待源码核实]） |
| v1.1 | 2026-08-10 | （保留原 v1.1 记录：删除 LewanSoul/Hiwonder 品牌信息，替换为"总线舵机"） |
| **v1.2** | 2026-08-10 | **重大重构：放弃 test_servo_direct.py 录制 + action_player.launch.py 混合路线，改为 bringup.launch.py + action_player 节点路线**。原因：用户反馈实验3主题应是"ROS2 架构认知与动作回放"，而非重复实验2的 test_servo_direct 录制；新方案按 **3a（系统架构认知 30min）→ 3b（动作回放 2h）→ 3c（零位校准 1.5h）** 三子阶段组织，明确**严禁使用** `/arm_controller/target_pose`（自动 IK）和 `/arm_controller/pick`/`/arm_controller/place`（完整抓取 pipeline），仅使用 `joint_command` 话题和 `action_player` 节点；输入数据来自 exp02 导出的 `pick_and_place.yaml`；新增 10 个知识点（bringup 拓扑、rqt_graph、node list、joint_command、PWM↔rad 换算、action_player 节点、YAML 格式兼容、回放模式、软件 offset、servo_calib GUI）；1.6 重写为 8 步：启动 bringup→joint_command 弧度控制→3a 架构认知→3b 动作回放（4 种模式）→3c 零位校准（software offset） |
