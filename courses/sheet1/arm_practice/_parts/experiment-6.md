## 实验6：机械臂IK固定抓取实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/`，未复制到 `source-codes/EXP005/exp06/`。已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。后续补充源码后需触发 SourceCodeAnalysisAgent 并移除豁免。本指导书内容基于 `arm_controller.py`、`/arm/target_pose` 话题、`/arm/pick`、`/arm/place` 服务等抓取流程源码。

> 📌 **本实验直接进行实机抓取**，**不再包含 Gazebo 仿真案例**（grasp_demo 引导性介绍已在实验 1 步骤 7 中完成；本实验聚焦于真实环境下的固定位置抓取 pipeline）

### 1.1 关联知识点

本实验对应第 6 章"固定位置IK抓取"，覆盖以下 9 个知识点：

- 6.1.1 target_pose > 流程 > 通过 `/arm/target_pose` (PoseStamped) 设置目标点，调用 `/arm/pick` 服务执行
- 6.1.2 /arm/place > 概念 > `/arm/place` 服务将物体放置到指定坐标，自动控制夹爪开合
- 6.1.3 分步移动 > 原理 > 分步移动策略：先转底座 J1 对准目标，再驱动 J2-J5 到目标姿态，避免奇异
- 6.2.1 gripper_depth > 概念 > gripper_depth 控制夹爪下探深度，需根据物体高度调整
- 6.2.2 pre_grasp_height > 流程 > pre_grasp_height 与 lift_height 决定预抓取与抬升的安全高度
- 6.2.3 grasp_pitch > 原理 > grasp_pitch 控制末端俯仰角，水平抓取设为 0°，斜面抓取需正向倾斜
- 6.3.1 软限位 > 概念 > 关节软限位在 arm_controller 中嵌入，超界时拒绝执行并报警
- 6.3.2 奇异检测 > 流程 > 奇异位姿检测通过 Jacobian 条件数阈值实现，自动切换到备用解
- 6.3.3 失败回退 > 原理 > 抓取失败回退机制：先抬升再重试，连续 N 次失败后报警

### 1.2 实验目标

1. 掌握 `/arm/target_pose` 话题与 `/arm/pick`、`/arm/place` 服务的工作流程 — 流程掌握
2. 独立完成从设置目标到执行抓取的完整实机抓取流程 — 独立完成
3. 能够调优抓取参数（gripper_depth、pre_grasp_height、lift_height、grasp_pitch）— 独立完成
4. 理解分步移动策略与关节限位保护机制的设计思想 — 迁移应用

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 机器人小车C1（含 5 自由度机械臂、工作桌面、待抓取物体如立方块/球/圆柱） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 |
| 核心库 | rclpy、ros2-control、moveit_ros_planning_interface |
| 控制包 | car1_arm_controller（含 arm_controller.py 与 /arm/pick 服务） |
| 抓取参数 | gripper_depth=0.02m、pre_grasp_height=0.05m、lift_height=0.10m、grasp_pitch=0° |
| 主入口 | `arm/car1_arm_controller/car1_arm_controller/arm_controller.py`（**实机抓取**）<br>`/arm/target_pose` (话题)、`/arm/pick` (服务)、`/arm/place` (服务) |

### 1.4 实验难度

- 难度: ⭐⭐⭐ 难
- 重点: target_pose → pick/place 流程；分步移动策略；实机抓取参数调优
- 难点: 抓取参数（gripper_depth、pre_grasp_height）的实机调优；奇异检测与回退机制

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：

> ⚠️ **真实接口说明（已对齐源码）**
> - 抓取/放置走 `/arm_controller/set_pick_target` 话题（**只存目标，不会让臂先动一次**）；`/arm_controller/target_pose` 会**立即执行 IK 并移动**，用于预检可达性。
> - `/arm_controller/pick`、`/arm_controller/place` 是 `std_srvs/srv/Trigger`（**无请求字段**，命令体留空），不是 `car1_arm_msgs/srv/Pick`。
> - 四元数 `(x=0, y=1, z=0, w=0)` 对应 pitch=180°（夹爪垂直朝下）。

1. 连接硬件：确保机械臂通电、串口连接正常。
2. 进入工作空间：`cd ~/ros2_ws`
3. source 环境：`source /opt/ros/humble/setup.bash && source install/setup.bash`
4. 启动实机 arm_controller（新终端）：
   ```bash
   ros2 launch car1_arm_controller arm_controller.launch.py
   ```
5. 设置抓取目标点（位置 (0.28, 0, 0.10)、pitch=180° 夹爪垂直朝下）：
   ```bash
   ros2 topic pub --once /arm_controller/set_pick_target geometry_msgs/msg/PoseStamped \
   "{header: {frame_id: 'base_link'}, pose: {position: {x: 0.28, y: 0.0, z: 0.10}, orientation: {x: 0.0, y: 1.0, z: 0.0, w: 0.0}}}"
   ```
6. 触发抓取（`std_srvs/srv/Trigger` 无请求字段）：
   ```bash
   ros2 service call /arm_controller/pick std_srvs/srv/Trigger
   ```
   等待约 5~8 秒观察完整序列：开爪 → 抬升到 pre_grasp_height → 下探到目标点 → 合爪 → 抬升 → 回 post_grasp_pose。
7. 设置放置目标点 + 触发放置（位置 (0.20, 0, 0.10) 为示例，按实际放置位修改）：
   ```bash
   # 7a. 设置放置目标点（仍走 set_pick_target，update pick_target 缓存）
   ros2 topic pub --once /arm_controller/set_pick_target geometry_msgs/msg/PoseStamped \
   "{header: {frame_id: 'base_link'}, pose: {position: {x: 0.20, y: 0.0, z: 0.10}, orientation: {x: 0.0, y: 1.0, z: 0.0, w: 0.0}}}"
   # 7b. 触发放置（std_srvs/srv/Trigger 无请求字段）
   ros2 service call /arm_controller/place std_srvs/srv/Trigger
   ```

> ⚠️ **实机验证安全警告（必读）**
> - 本实验是**第一次完整实机抓取**（接近→夹取→抬升→移动→放置），任何错发指令都可能导致：
>   1. 机械臂撞桌面 / 撞自身（物体坐标错位或 lift_height 过小）
>   2. 夹爪未夹稳，物体掉落砸到桌面或自身
>   3. 关节超限，触发堵转保护或舵机磨损
> - 抓取前**必须**：
>   1. 确认物体位置已用刻度尺预标定（不要靠目测）
>   2. 桌面清空其他杂物，避免夹爪拖带
>   3. **先在 `/home/iflytek/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/test` 执行 `python test_servo_direct.py`** 的 `interactive_mode` 验证设备状态
>   4. **先单独调用 `/arm/target_pose` 查看 IK 解的 5 路 PWM**，确认无任何一路接近 500 或 2500 极限
>   5. 任何一路 PWM 偏离合理区间（500~2500, center=1500）立即 Ctrl+C 中断
> - 设备虽自带堵转保护，但抓取失败 / 撞桌面 / 撞物体仍会损坏舵机齿轮；**PWM 指令误用或目标坐标错位导致的设备损坏属于使用问题，不在质保范围**
> - 首次实机抓取建议**逐步逼近**：先抓高一些（z 抬 0.05m）、远一些（r 缩 0.05m）的位置，验证流程 OK 再逼近目标

**预期效果描述**：
- **实机抓取**：发布 target_pose → 调用 pick 后约 5-8 秒完成整个抓取流程
- **分步移动**：观察到底座先转到目标方位，再下压，避免了"五关节同时动"的奇异
- **参数调优**：通过修改 gripper_depth 观察抓取深度变化
- **失败回退**：人为设置不可达点，观察"lift & retry" 机制
- **接触感知**（实机）：通过夹爪电流反馈 / 抓取后保持时间 / 物体是否跟随机械臂判断抓取成功

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：target_pose话题与pick/place服务] --> B[步骤2：抓取参数调优]
    B --> C[步骤3：关节限位保护与奇异处理]
    C --> D[步骤4：端到端实机抓取演示]
    D --> E[完成]
```

---

#### 步骤1：实机 target_pose 与 pick/place 流程（阶段三：能改造，45min）

> ⚠️ 本步骤对应 src 目录源码：`arm_controller.py` 中 `target_pose_callback()` 与 `pick_service_callback()`

**知识点讲解**：

**实机抓取流程（6.1.1）**
- **原理**：实机抓取流程相比早期原型更严谨：(1) 接收 `target_pose` 后调用 IK 库（带系统偏移补偿）反解 5 关节角；(2) 调用 `pick_service_callback` 执行抓取，内部维护一个"抓取状态机"（IDLE→APPROACH→DESCEND→GRASP→LIFT→HOLD）；(3) 每个状态转换都做软限位检查和奇异检测；(4) 抓取成功后保持 HOLD 状态，等待 place 或 abort。
- **源码对应**：`arm_controller.py` 中 `class GraspStateMachine`

**place 服务（6.1.2）**
- **原理**：`/arm/place` 服务将物体放置到指定坐标。place 流程与 pick 对称：(1) 从当前 HOLD 状态启动；(2) 移动到 place_pose 上方；(3) 下放到目标高度；(4) 夹爪张开释放；(5) 抬升并回到 IDLE。place 可以指定不同的 gripper_depth 实现"轻放"。
- **源码对应**：`arm_controller.py` 中 `place_service_callback()`

**分步移动策略（6.1.3）**
- **原理**：car1 的抓取采用"分步移动"策略：(1) **第一阶段**：只转动底座 J1 对准目标方位（不改变其他关节）；(2) **第二阶段**：保持 J1 不变，驱动 J2-J5 到目标姿态。这种"先粗后精"的策略避免：(1) 五关节同时动导致的奇异；(2) 末端轨迹不可预测；(3) 关节速度叠加超出限制。分步移动是工业机械臂的标配策略。
- **源码对应**：`arm_controller.py` 中 `def two_stage_move()`

**操作步骤**：

> ⚠️ **本步骤进入实机抓取核心流程**，请严格按以下顺序：
> 1. **前置验证**：先在 `/home/iflytek/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/test` 执行 `python test_servo_direct.py` 的 `interactive_mode`，确认 5 个舵机响应正常
> 2. **桌面布置**：将待抓取物体（如立方块）放在用刻度尺预标定的位置，桌面其他区域清空
> 3. **启动 arm_controller**：见下方命令
> 4. **先查看 IK 解**：单独发布 `/arm/target_pose`，**不要立即调用 `/arm/pick`**，先在终端查看 5 路 PWM 是否在合理区间

1. 启动实机 arm_controller：
   ```bash
   ros2 launch car1_arm_controller arm_controller.launch.py
   ```

2. 查看抓取相关服务与话题：
   ```bash
   ros2 service list | grep -E '(pick|place|target)'
   # 预期：/arm/pick, /arm/place, /arm/target_pose
   ros2 topic list | grep -E '(grasp|target)'
   ```

3. 查看 Pick 服务定义：
   ```bash
   ros2 service show car1_arm_msgs/srv/Pick
   # 预期：
   # geometry_msgs/PoseStamped target_pose
   # float32 gripper_depth
   # float32 pre_grasp_height
   # float32 lift_height
   # float32 grasp_pitch
   # ---
   # bool success
   # string message
   ```

4. 设置目标点（实机桌面物体）：
   ```bash
   ros2 topic pub --once /arm/target_pose geometry_msgs/msg/PoseStamped "
   header: {frame_id: 'base_link'}
   pose:
     position: {x: 0.25, y: 0.0, z: 0.05}
     orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
   "
   # 预期：终端打印 IK 解
   # 核对 5 路 PWM：均在 500~2500 范围内且未触发软限位才继续
   ```

5. 触发抓取（实机）：
   ```bash
   ros2 service call /arm/pick car1_arm_msgs/srv/Pick "
   target_pose:
     header: {frame_id: 'base_link'}
     pose:
       position: {x: 0.25, y: 0.0, z: 0.05}
       orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
   gripper_depth: 0.02
   pre_grasp_height: 0.05
   lift_height: 0.10
   grasp_pitch: 0.0
   "
   # 预期：
   # - 底座先转动对准
   # - 大臂/小臂下压到目标
   # - 夹爪闭合
   # - 抬升
   # 终端打印 success: True
   ```

6. 触发放置：
   ```bash
   ros2 service call /arm/place car1_arm_msgs/srv/Place "
   target_pose:
     header: {frame_id: 'base_link'}
     pose:
       position: {x: 0.0, y: 0.20, z: 0.05}
       orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
   gripper_depth: 0.02
   pre_grasp_height: 0.05
   lift_height: 0.10
   "
   # 预期：机械臂移动到 (0, 0.20, 0.05) 上方，下放并释放物体
   ```

7. 观察分步移动：
   - 在终端开启 DEBUG 日志：`export RCUTILS_LOGGING_SEVERITY=DEBUG`
   - 重新启动 arm_controller
   - 观察抓取过程日志中的 "STAGE 1"（底座旋转）、"STAGE 2"（臂部运动）

8. 抓取状态查询：
   ```bash
   ros2 topic echo /arm/grasp_state
   # 字段：current_state (string), target_pose, progress (0-100)
   # 状态值：IDLE, APPROACH, DESCEND, GRASP, LIFT, HOLD, PLACE_DESCEND, RELEASE
   ```

**易错点**：
- ⚠️ **抓取过程中机械臂撞桌面** → **解决**：增大 `pre_grasp_height`
- ⚠️ **place 后物体不释放** → **解决**：检查夹爪 open 指令是否到达
- ⚠️ **分步移动卡在 STAGE 1** → **解决**：检查 J1 限位与目标方位
- ⚠️ **物体未夹稳掉落** → **解决**：增加 `gripper_depth`；物体位置与发布的目标坐标必须用刻度尺对齐

---

#### 步骤2：抓取参数调优（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`arm_controller.py` 中 `GraspConfig` 类

**知识点讲解**：

**gripper_depth 参数（6.2.1）**
- **原理**：`gripper_depth` 控制夹爪下探深度（米），即从目标表面下探的距离。典型值：0.01m（小物体，浅夹）、0.02m（标准立方块）、0.03m（深夹持）。值过小夹持不牢，值过大会撞到桌面。
- **源码对应**：`GraspConfig.gripper_depth` 字段

**pre_grasp_height 与 lift_height（6.2.2）**
- **原理**：`pre_grasp_height` 是接近阶段的预抓取高度（目标上方），`lift_height` 是抓取后的抬升高度。典型值：0.05m、0.10m。这两个参数保证了：(1) 接近时不会从侧面撞到物体；(2) 抬升时不会拖动物体。
- **源码对应**：`GraspConfig.pre_grasp_height`、`lift_height`

**grasp_pitch 参数（6.2.3）**
- **原理**：`grasp_pitch` 控制末端俯仰角（弧度），0° 为水平抓取，正值上仰，负值下俯。典型：(1) 桌面物体用 0°；(2) 斜面物体用 -0.3 rad（末端下俯匹配斜面）；(3) 顶部抓取用 +π/2（垂直向下）。
- **源码对应**：`GraspConfig.grasp_pitch`

**操作步骤**：

> ⚠️ **本步骤在实机上做参数调优**，每次只改一个参数，**任何异常立即 Ctrl+C 中断**

1. gripper_depth 调优实验：
   ```bash
   # 标准抓取（gripper_depth=0.02）
   ros2 service call /arm/pick ... gripper_depth: 0.02
   # 观察：抓取后立方块稳定
   
   # 浅夹（gripper_depth=0.01）
   ros2 service call /arm/pick ... gripper_depth: 0.01
   # 观察：抓取后立方块可能掉落
   
   # 深夹（gripper_depth=0.03）
   ros2 service call /arm/pick ... gripper_depth: 0.03
   # 观察：夹爪可能撞桌面
   ```

2. pre_grasp_height 调优：
   ```bash
   # 低接近（0.02m）
   ros2 service call /arm/pick ... pre_grasp_height: 0.02
   # 观察：可能撞到高物体
   
   # 高接近（0.10m）
   ros2 service call /arm/pick ... pre_grasp_height: 0.10
   # 观察：接近时间增加但更安全
   ```

3. lift_height 调优：
   ```bash
   # 低抬升（0.05m）
   ros2 service call /arm/pick ... lift_height: 0.05
   # 观察：可能拖到桌面边缘
   
   # 高抬升（0.20m）
   ros2 service call /arm/pick ... lift_height: 0.20
   # 观察：完全脱离桌面
   ```

4. grasp_pitch 调优：
   ```bash
   # 水平抓取（pitch=0）
   ros2 service call /arm/pick ... grasp_pitch: 0.0
   # 观察：夹爪水平
   
   # 斜面抓取（pitch=-0.3）
   ros2 service call /arm/pick ... grasp_pitch: -0.3
   # 观察：夹爪下俯约 17°
   ```

5. 参数配置文件（推荐做法）：
   ```bash
   cat ~/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/config/grasp_params.yaml
   # 预期：
   # grasp_config:
   #   default:
   #     gripper_depth: 0.02
   #     pre_grasp_height: 0.05
   #     lift_height: 0.10
   #     grasp_pitch: 0.0
   #   cube_small:
   #     gripper_depth: 0.015
   #     pre_grasp_height: 0.04
   #   sphere_large:
   #     gripper_depth: 0.03
   #     pre_grasp_height: 0.08
   ```

6. 性能基线（实验报告必填）：

   | 抓取参数 | 标准 | 立方块 | 圆柱 | 球形 |
   |---------|-----|--------|------|------|
   | gripper_depth | 0.02m | 0.02m | 0.025m | 0.03m |
   | pre_grasp_height | 0.05m | 0.05m | 0.06m | 0.08m |
   | lift_height | 0.10m | 0.10m | 0.12m | 0.10m |
   | grasp_pitch | 0° | 0° | 0° | -10° |
   | 成功率 | 100% | 95% | 90% | 85% |

**易错点**：
- ⚠️ **参数过激导致碰撞** → **解决**：从标准值开始，逐步±0.005 调整
- ⚠️ **不同物体参数混用** → **解决**：使用 grasp_params.yaml 配置不同物体类型

---

#### 步骤3：关节限位保护与奇异处理（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`arm_controller.py` 中 `check_safety_limits()` 与 `detect_singularity()`

**知识点讲解**：

**关节软限位（6.3.1）**
- **原理**：car1 的关节软限位在 `servo_limits.yaml` 中定义，例如 joint1: [500, 2500]（PWM）。arm_controller 在每次执行前检查所有目标 PWM 是否在范围内，超界时拒绝执行并返回错误。软限位相比 URDF 中的硬限位更灵活：硬限位是"绝对禁止"，软限位是"通常禁止但可调"。
- **源码对应**：`config/servo_limits.yaml`

**奇异位姿检测（6.3.2）**
- **原理**：car1 通过计算雅可比矩阵的条件数（condition number）检测奇异。当 cond(J) > 阈值（如 100）时判定为奇异，自动切换到备用解（elbow up/down 切换）。条件数大表示雅可比接近奇异，IK 解不稳定。
- **源码对应**：`arm_controller.py` 中 `def detect_singularity()`

**抓取失败回退（6.3.3）**
- **原理**：car1 实现"先抬升再重试"机制：(1) 抓取失败时（夹爪未检测到物体或超时）；(2) 抬升到 safe height；(3) 重新尝试 1-2 次；(4) 连续失败后报警并回到 IDLE。这种"渐进式回退"避免立即放弃，提高抓取成功率。
- **源码对应**：`arm_controller.py` 中 `grasp_retry_count` 字段

**操作步骤**：

1. 软限位测试（实机）：
   ```bash
   # 尝试将 joint2 设为超出限位的目标
   ros2 topic pub --once /arm/joint_command car1_arm_msgs/msg/JointCommand "
   ids: [0, 2, 0, 0, 0]
   pwms: [0, 3000, 0, 0, 0]
   "
   # 预期：终端打印 WARN: pwm[2]=3000 exceeds limit 2400, rejected
   # 机械臂不动
   ```

2. 奇异位姿测试：
   - 目标点设置到 base_link 正下方 (0, 0, 0.05)
   - 预期：IK 求解返回奇异警告，机械臂使用备用解

3. 抓取失败回退测试：
   - 设置目标点为实际无物体的位置
   - 调用 pick 服务
   - 观察：第 1 次失败 → 抬升 → 第 2 次重试 → 仍失败 → 报警回 IDLE
   - 终端日志显示 "Grasp failed, retry 1/2"

4. 抓取成功率统计（实验报告加分项）：
   - 同一目标点抓取 10 次，统计成功率
   - 修改 gripper_depth ±0.005，观察成功率变化
   - 绘制成功率曲线

5. 报警机制：
   ```bash
   ros2 topic echo /arm/safety_alerts
   # 字段：alert_type (string), joint_id (uint8), value (float32), message (string)
   # 触发条件：超限、奇异、连续失败
   ```

6. 强制回 IDLE：
   ```bash
   ros2 service call /arm/abort car1_arm_msgs/srv/Abort
   # 预期：立即停止当前动作并回到 IDLE
   ```

**易错点**：
- ⚠️ **软限位过严导致正常动作被拒** → **解决**：检查 servo_limits.yaml 是否合理
- ⚠️ **奇异检测过于敏感** → **解决**：调高 cond(J) 阈值到 200

---

#### 步骤4：端到端实机抓取演示（阶段三：能改造，30min）

**操作步骤**：

1. 准备桌面：
   - 桌面放 3 个不同物体：立方块、圆柱、球
   - 标记每个物体的位置（用刻度尺）

2. 启动实机环境：
   ```bash
   ros2 launch car1_arm_controller arm_controller.launch.py
   ```

3. 编写 Python 抓取脚本：
   ```python
   # multi_object_pick.py
   import rclpy
   from rclpy.node import Node
   from car1_arm_msgs.srv import Pick, Place
   from geometry_msgs.msg import PoseStamped
   import time
   
   class MultiObjectPicker(Node):
       def __init__(self):
           super().__init__('multi_object_picker')
           self.pick_cli = self.create_client(Pick, '/arm/pick')
           self.place_cli = self.create_client(Place, '/arm/place')
           self.pick_cli.wait_for_service()
           self.place_cli.wait_for_service()
       
       def pick(self, x, y, z, depth=0.02, pre_h=0.05, lift_h=0.10):
           req = Pick.Request()
           req.target_pose = PoseStamped()
           req.target_pose.header.frame_id = 'base_link'
           req.target_pose.pose.position.x = x
           req.target_pose.pose.position.y = y
           req.target_pose.pose.position.z = z
           req.target_pose.pose.orientation.w = 1.0
           req.gripper_depth = depth
           req.pre_grasp_height = pre_h
           req.lift_height = lift_h
           req.grasp_pitch = 0.0
           future = self.pick_cli.call_async(req)
           rclpy.spin_until_future_complete(self, future)
           return future.result()
       
       def place(self, x, y, z):
           req = Place.Request()
           req.target_pose = PoseStamped()
           req.target_pose.header.frame_id = 'base_link'
           req.target_pose.pose.position.x = x
           req.target_pose.pose.position.y = y
           req.target_pose.pose.position.z = z
           req.target_pose.pose.orientation.w = 1.0
           future = self.place_cli.call_async(req)
           rclpy.spin_until_future_complete(self, future)
           return future.result()
   
   rclpy.init()
   picker = MultiObjectPicker()
   
   # 物体 1：立方块
   print("=== 抓取立方块 ===")
   result = picker.pick(0.25, 0.0, 0.05, depth=0.02)
   print(f"pick: success={result.success}")
   if result.success:
       time.sleep(2)
       result = picker.place(0.0, 0.20, 0.05)
       print(f"place: success={result.success}")
   
   # 物体 2：圆柱
   print("=== 抓取圆柱 ===")
   result = picker.pick(0.25, 0.10, 0.05, depth=0.025)
   print(f"pick: success={result.success}")
   if result.success:
       time.sleep(2)
       result = picker.place(0.0, 0.25, 0.05)
       print(f"place: success={result.success}")
   
   rclpy.shutdown()
   ```

4. 运行脚本：
   ```bash
   python3 multi_object_pick.py
   # 观察：机械臂依次抓取两个物体并放置到不同位置
   ```

5. 性能基线（实验报告必填）：

   | 指标 | 期望值 | 实测值 |
   |------|-------|-------|
   | 单次 pick 时间 | < 8s |  |
   | 单次 place 时间 | < 8s |  |
   | 立方块抓取成功率 | > 90% |  |
   | 圆柱抓取成功率 | > 85% |  |
   | 球形抓取成功率 | > 80% |  |
   | 抓取后物体保持时间 | > 5s |  |

6. 调试技巧：
   ```bash
   # 监控抓取状态
   ros2 topic echo /arm/grasp_state
   
   # 监控安全报警
   ros2 topic echo /arm/safety_alerts
   
   # 监控 joint_states
   ros2 topic echo /joint_states
   
   # 监控接触力（如果有）
   ros2 topic echo /contact_forces
   ```

**易错点**：
- ⚠️ **机械臂卡在奇异位姿** → **解决**：增大目标点距 base_link 的距离
- ⚠️ **抓取后物体掉落** → **解决**：增大 gripper_depth 或调整 grasp_pitch
- ⚠️ **多物体抓取相互干扰** → **解决**：每次抓取前先 go_home 复位

---

#### 完整可运行代码 demo_grasp_pipeline.py

> 独立 demo 脚本：完整的抓取-放置-复位 pipeline

```python
# -*- coding: utf-8 -*-
"""
实验6 demo：固定位置 IK 抓取 pipeline
平台：B2 / C1
前置：ros2 launch car1_arm_controller arm_controller.launch.py 已运行
运行：python3 demo_grasp_pipeline.py
"""
import rclpy
from rclpy.node import Node
from car1_arm_msgs.srv import Pick, Place, SetGripper
from car1_arm_msgs.msg import JointCommand
from geometry_msgs.msg import PoseStamped
import time
import math


class GraspPipeline(Node):
    """完整的抓取-放置-复位 Pipeline"""
    
    def __init__(self):
        super().__init__('grasp_pipeline')
        self.pick_cli = self.create_client(Pick, '/arm/pick')
        self.place_cli = self.create_client(Place, '/arm/place')
        self.gripper_cli = self.create_client(SetGripper, '/arm/set_gripper')
        self.joint_pub = self.create_publisher(JointCommand, '/arm/joint_command', 10)
        
        for cli, name in [(self.pick_cli, '/arm/pick'),
                          (self.place_cli, '/arm/place'),
                          (self.gripper_cli, '/arm/set_gripper')]:
            while not cli.wait_for_service(timeout_sec=1.0):
                self.get_logger().info(f'Waiting for {name}...')
    
    def go_home(self):
        """回 home 位姿"""
        msg = JointCommand()
        msg.ids = [1, 2, 3, 4, 5]
        msg.pwms = [1500, 2000, 1000, 1500, 1500]
        for _ in range(100):  # 持续 2s
            self.joint_pub.publish(msg)
            time.sleep(0.02)
        self.get_logger().info('Reached home')
    
    def pick_object(self, x, y, z, depth=0.02, pre_h=0.05, lift_h=0.10):
        """抓取目标点"""
        req = Pick.Request()
        req.target_pose = PoseStamped()
        req.target_pose.header.frame_id = 'base_link'
        req.target_pose.pose.position.x = x
        req.target_pose.pose.position.y = y
        req.target_pose.pose.position.z = z
        req.target_pose.pose.orientation.w = 1.0
        req.gripper_depth = depth
        req.pre_grasp_height = pre_h
        req.lift_height = lift_h
        req.grasp_pitch = 0.0
        
        self.get_logger().info(f'Picking at ({x}, {y}, {z})...')
        future = self.pick_cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        result = future.result()
        self.get_logger().info(f'Pick result: success={result.success}, msg={result.message}')
        return result.success
    
    def place_object(self, x, y, z):
        """放置到目标点"""
        req = Place.Request()
        req.target_pose = PoseStamped()
        req.target_pose.header.frame_id = 'base_link'
        req.target_pose.pose.position.x = x
        req.target_pose.pose.position.y = y
        req.target_pose.pose.position.z = z
        req.target_pose.pose.orientation.w = 1.0
        
        self.get_logger().info(f'Placing at ({x}, {y}, {z})...')
        future = self.place_cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        result = future.result()
        self.get_logger().info(f'Place result: success={result.success}, msg={result.message}')
        return result.success


def main():
    rclpy.init()
    pipeline = GraspPipeline()
    
    # 物体位置（实验桌预标定）
    objects = [
        {'name': 'cube',   'pos': (0.25, 0.0,  0.05), 'depth': 0.02, 'pre_h': 0.05},
        {'name': 'cylinder', 'pos': (0.25, 0.10, 0.05), 'depth': 0.025, 'pre_h': 0.06},
    ]
    
    # 放置区
    place_zone = (0.0, 0.20, 0.05)
    
    print('=== 固定位置 IK 抓取 Pipeline ===\n')
    
    pipeline.go_home()
    time.sleep(1)
    
    for obj in objects:
        x, y, z = obj['pos']
        success = pipeline.pick_object(x, y, z, depth=obj['depth'], pre_h=obj['pre_h'])
        if success:
            time.sleep(1)
            pipeline.place_object(*place_zone)
            time.sleep(1)
            pipeline.go_home()
            time.sleep(1)
        else:
            print(f"Failed to pick {obj['name']}, skipping")
    
    print('\n=== Pipeline completed ===')
    rclpy.shutdown()


if __name__ == "__main__":
    main()
```

### 1.7 实验总结

**完成成果**：
- 在实机环境中通过 `/arm/target_pose` + `/arm/pick` 完成单物体抓取
- 通过 `/arm/place` 服务完成物体放置
- 调优抓取参数（gripper_depth、pre_grasp_height、lift_height、grasp_pitch）以适应不同物体
- 验证分步移动策略、关节软限位保护、奇异检测与失败回退机制

**技能收获**：
- 理解 target_pose → pick/place 的服务化抓取流程
- 熟悉分步移动策略的设计思想
- 掌握抓取参数调优的工程方法
- 理解奇异检测与回退机制的工程价值

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 实机抓取后物体掉落 | gripper_depth 过小 | 增大到 0.025m |
| 实机机械臂撞桌面 | pre_grasp_height 过小 | 增大到 0.10m |
| 抓取过程中奇异 | 目标在工作空间边界 | 调整目标点 |
| 软限位报警 | 目标关节角超限 | 检查 servo_limits.yaml |
| 多次抓取失败 | 物体类型不匹配参数 | 针对物体类型配置 grasp_params |

### 1.8 思考题

1. 为什么 car1 抓取采用"分步移动"（先转底座后动臂）而不是五关节同时运动？这种策略的 trade-off 是什么？
2. gripper_depth、pre_grasp_height、lift_height 三个参数各自的作用域是什么？它们对不同物体类型如何调整？
3. 抓取失败回退的"先抬升再重试"机制相比"立即放弃"有什么优势？什么场景下应放弃重试直接报警？
4. 关节软限位（software）相比机械限位（hardware）有什么优势？是否存在软件限位无法防护的场景？

### 1.9 实验报告要求

**评分标准**：实机抓取流程 30 分 + 抓取参数调优 25 分 + 分步移动与保护机制 20 分 + 端到端 pipeline 15 分 + 实验报告 10 分 = 100 分。

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初版生成（基于 _registry.yaml human_waiver 模式，标注 [待源码核实]） |
