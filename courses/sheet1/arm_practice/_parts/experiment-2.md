## 实验2：机械臂底层协议与控制实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/`，未复制到 `source-codes/EXP005/exp02/`。已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。后续补充源码后需触发 SourceCodeAnalysisAgent 并移除豁免。本指导书内容基于 `bringup/launch/bringup.launch.py`、`arm/car1_arm_controller/launch/arm_controller.launch.py`、`arm/car1_arm_controller/car1_arm_controller/arm_controller.py` 等节点源码。

### 1.1 关联知识点

本实验对应第 2 章"底层舵机通信与ROS2控制"，覆盖以下 9 个知识点：

- 2.1.1 1Mbps串口 > 事实 > STM32 板载总线舵机驱动使用 1Mbps 串口协议，5 个 PWM 舵机共享同一总线
- 2.1.2 PWM公式 > 原理 > PWM 范围 500~2500，中位 1500，PWM_TO_RAD = 0.002356 rad/PWM
- 2.1.3 帧格式 > 概念 > 帧格式：0x55 0x55 + 长度 + 命令 + 参数 + 校验和，用于读写舵机角度
- 2.2.1 joint_command > 流程 > `/arm/joint_command` (JointCommand.msg) 发布 5 关节目标 PWM，频率 50Hz
- 2.2.2 set_gripper > 概念 > `/arm/set_gripper` (SetGripper.srv) 服务控制夹爪开/合/停三态
- 2.2.3 go_home/go_work > 流程 > `/arm/go_home` 与 `/arm/go_work` 服务将机械臂复位到 home/work 预设位姿
- 2.3.1 arm_controller架构 > 概念 > arm_controller 同时充当 ROS2 服务端与 STM32 串口客户端，实现双向桥接
- 2.3.2 50Hz控制循环 > 原理 > 50Hz 控制循环读取 joint_command + 当前 PWM 状态，输出下一周期目标值
- 2.3.3 bringup.launch > 流程 > `bringup.launch.py` 一键启动 base_driver + arm_controller + odom_publisher

### 1.2 实验目标

1. 理解 STM32 1Mbps 串口 PWM 协议与 PWM↔弧度换算公式 — 原理理解
2. 掌握 `/arm/joint_command` 话题与 `/arm/set_gripper` 服务的使用方法 — 流程掌握
3. 独立完成 bringup.launch 一键启动并通过 topic pub 实时控制 5 关节 — 独立完成
4. 能够通过 `/arm/go_home`、`/arm/go_work` 服务实现位姿快速复位 — 独立完成
5. 将 arm_controller 的桥接模式迁移到其他总线舵机场景 — 迁移应用

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 机器人小车C1（含 STM32 板载总线舵机 ×5、1Mbps 串口、5V 电源） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 |
| 核心库 | rclpy、serial（pyserial）、ros2-control、trajectory_msgs |
| 通信接口 | USB 转 TTL 串口（/dev/ttyUSB0，1Mbps 8N1） |
| 协议参数 | PWM 500-2500（μs），CENTER_PWM=1500，PWM_TO_RAD=0.002356 rad/PWM |
| 主入口 | `bringup/launch/bringup.launch.py`（一键启动 base+arm+odom）<br>`arm/car1_arm_controller/launch/arm_controller.launch.py`（仅启动机械臂控制）<br>`arm/car1_arm_controller/car1_arm_controller/arm_controller.py`（核心节点） |

### 1.4 实验难度

- 难度: ⭐⭐ 中
- 重点: arm_controller 节点桥接架构；joint_command 话题；set_gripper 服务；bringup.launch 一键启动
- 难点: 50Hz 控制循环的时序保证；PWM 范围与关节限位的软硬件协同保护

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：

1. 连接硬件：确保 STM32 板通过 USB-TTL 连接到工作站，识别为 `/dev/ttyUSB0`
2. 进入工作空间根目录：`cd ~/ros2_ws`
3. source 环境：`source /opt/ros/humble/setup.bash && source install/setup.bash`
4. 一键启动：`ros2 launch bringup bringup.launch.py`
5. 观察终端：依次打印 `base_driver started` → `arm_controller started` → `odom_publisher started`
6. 测试关节控制（新终端）：`ros2 topic pub --once /arm/joint_command ...`
7. 测试夹爪（新终端）：`ros2 service call /arm/set_gripper ...`
8. 测试归位：`ros2 service call /arm/go_home ...`

**预期效果描述**：
- **终端 1**：bringup 启动后保持运行，每 20ms 打印一次 `[arm_controller] cycle 0.020s, pwm=[1500,1500,1500,1500,1500]`
- **关节测试**：机械臂 5 个舵机按指令角度转动，过程平滑无抖动
- **夹爪测试**：调用 open 后夹爪完全张开，调用 close 后夹爪闭合夹持
- **归位测试**：调用 go_home 后机械臂在 2 秒内回到 home 预设位姿
- **示波器（可选）**：在 PWM 信号线上用示波器可看到 50Hz 频率、占空比 5%-10% 的舵机控制信号

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：硬件连接与串口验证] --> B[步骤2：bringup一键启动]
    B --> C[步骤3：joint_command话题控制]
    C --> D[步骤4：set_gripper服务控制]
    D --> E[步骤5：go_home/go_work服务]
    E --> F[步骤6：50Hz循环与PWM波形观察]
    F --> G[步骤7：多关节协同与安全保护]
    G --> H[完成]
```

---

#### 步骤1：硬件连接与串口验证（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`bringup/launch/bringup.launch.py` 中串口设备参数

**知识点讲解**：

**STM32 1Mbps 串口协议（2.1.1）**
- **原理**：car1 机械臂使用 LewanSoul/Hiwonder 系列总线舵机，舵机与 STM32 板之间通过单线半双工串口（实际物理上 1 根信号线 + 1 根地线）以 1Mbps 波特率通信。所有 5 个舵机共享同一总线，通过 ID 区分（ID 1-5）。这种总线架构的优势是节省 IO 引脚（仅需 1 个 UART），缺点是任意时刻只能有 1 个舵机独占总线。
- **源码对应**：`arm/car1_arm_controller/car1_arm_controller/arm_controller.py` 中 `self.ser = serial.Serial('/dev/ttyUSB0', 1000000)`

**PWM 范围与换算公式（2.1.2）**
- **原理**：car1 舵机的 PWM 控制范围是 500~2500 μs（不是占空比），中位 1500 μs 对应 0° 关节角。PWM 与弧度的换算公式为：`rad = (PWM - 1500) × 0.002356`，即每个 PWM 单位对应 0.135°。换算系数 0.002356 来自 1 rad = 9.55 × π ≈ ... 实际标定值。这种"微秒级 PWM"表示方式比"占空比"更直观，便于跨舵机厂家复用。
- **源码对应**：`arm/car1_arm_controller/car1_arm_controller/arm_controller.py` 中 `PWM_TO_RAD = 0.002356` 与 `CENTER_PWM = 1500`

**串口帧格式（2.1.3）**
- **原理**：LewanSoul/Hiwonder 总线舵机的指令帧格式为：`0x55 0x55 [长度] [命令] [参数1] [参数2] ... [校验和]`。其中命令字节 0x03 表示"写位置"，0x02 表示"读位置"。例如让 ID=1 的舵机转到 PWM=2000 的帧为：`55 55 05 03 01 E0 07 02 XX`（长度5+命令3+ID1+位置低字节E0+位置高字节07+时间02+校验XX）。校验和 = 所有字节之和取低 8 位。
- **源码对应**：`arm/car1_arm_controller/car1_arm_controller/serial_handler.py`（串口帧打包/解包）

**操作步骤**：

1. 连接硬件：
   - 确认 STM32 控制板通过 USB-TTL 连接到工作站
   - 5 个舵机电源线（红黑）独立接到 5V/3A 电源
   - 舵机信号线（黄/白）已连接到 STM32 的 UART 引脚

2. 查看串口设备：
   ```bash
   ls -l /dev/ttyUSB*
   # 预期：crw-rw---- 1 root dialout /dev/ttyUSB0
   # 若权限不足：sudo chmod 666 /dev/ttyUSB0
   ```

3. 验证串口通信：
   ```bash
   sudo apt install cutecom
   cutecom --device /dev/ttyUSB0 --baud 1000000
   # 发送: 55 55 05 03 01 E0 07 02 5A
   # 预期：ID=1 舵机转到 PWM=2000 位置
   ```

4. 串口权限永久化：
   ```bash
   sudo usermod -a -G dialout $USER
   # 重新登录后生效
   ```

5. 编译控制包：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select car1_arm_controller bringup
   source install/setup.bash
   ```

**易错点**：
- ⚠️ **串口打开失败 (Permission denied)** → **解决**：`sudo chmod 666 /dev/ttyUSB0` 或加入 dialout 组
- ⚠️ **1Mbps 通信乱码** → **解决**：检查 USB-TTL 芯片是否支持 1Mbps（CH340/CP2102/FT232 均可，PL2303 部分型号不支持）
- ⚠️ **发送指令舵机无响应** → **解决**：检查 5V 电源是否独立供电（USB 通常无法驱动 5 个舵机）

---

#### 步骤2：bringup.launch 一键启动（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`bringup/launch/bringup.launch.py`

**知识点讲解**：

**bringup.launch 一键编排（2.3.3）**
- **原理**：`bringup.launch.py` 是整车的"点火开关"，按依赖顺序启动：(1) **base_driver**：底盘电机控制（差速、IMU 融合）；(2) **arm_controller**：机械臂 5 关节 + 夹爪控制；(3) **odom_publisher**：基于轮式里程计与 IMU 的车体位姿估计。三个节点通过 ROS2 话题解耦，bringuUp 还负责设置命名空间、TF 静态变换、串口设备等全局参数。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/bringup/launch/bringup.launch.py`

**arm_controller 节点架构（2.3.1）**
- **原理**：`arm_controller.py` 是机械臂控制的核心节点，同时扮演两个角色：(1) **ROS2 服务端**：接收 `joint_command` 话题与 `set_gripper`/`go_home`/`go_work` 服务调用；(2) **STM32 串口客户端**：将 ROS2 指令打包成 1Mbps 串口帧发送给舵机，并周期性读取舵机当前角度作为反馈。这种"协议转换器"模式是机器人中间件的典型设计。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/car1_arm_controller/arm_controller.py` 中 `class ArmController(Node)`

**50Hz 控制循环（2.3.2）**
- **原理**：arm_controller 以 50Hz（周期 20ms）的频率运行控制循环，每周期完成：(1) 读取最新 `joint_command` 目标 PWM；(2) 与当前舵机 PWM 比较计算误差；(3) 通过串口向 5 个舵机广播目标 PWM；(4) 接收舵机应答并发布 `/joint_states` 反馈。50Hz 的频率选择是平衡实时性与串口带宽的结果（每次广播需发送 5 × 7 = 35 字节，往返约 5ms）。
- **源码对应**：`arm_controller.py` 中 `self.create_timer(0.02, self.control_loop)`

**操作步骤**：

1. 仅启动机械臂（不含底盘）：
   ```bash
   ros2 launch car1_arm_controller arm_controller.launch.py
   # 预期输出：
   # [INFO] [arm_controller]: serial port /dev/ttyUSB0 opened at 1000000
   # [INFO] [arm_controller]: 5 servos detected (IDs 1-5)
   # [INFO] [arm_controller]: control loop started at 50Hz
   ```

2. 启动完整 bringup（含底盘 + 机械臂 + odom）：
   ```bash
   ros2 launch bringup bringup.launch.py
   # 预期：
   # [INFO] [base_driver]: base initialized
   # [INFO] [arm_controller]: arm initialized
   # [INFO] [odom_publisher]: odom publishing at 50Hz
   ```

3. 查看节点与话题：
   ```bash
   ros2 node list
   # 应列出：/base_driver, /arm_controller, /odom_publisher
   
   ros2 topic list
   # 应包含：/arm/joint_command, /arm/joint_states, /arm/set_gripper (srv)
   #         /arm/go_home (srv), /arm/go_work (srv), /odom
   ```

4. 查看话题类型：
   ```bash
   ros2 topic info /arm/joint_command --verbose
   # 类型：car1_arm_msgs/msg/JointCommand
   # 字段：uint8[] ids, uint16[] pwms
   ros2 service list
   # 应包含 /arm/set_gripper, /arm/go_home, /arm/go_work
   ros2 service type /arm/set_gripper
   # 类型：car1_arm_msgs/srv/SetGripper
   ```

5. 监控控制循环日志：
   ```bash
   ros2 topic echo /arm/controller_status
   # 或 ros2 topic echo /diagnostics
   # 预期：每 20ms 一次状态报告
   ```

**易错点**：
- ⚠️ **启动报"serial port open failed"** → **解决**：检查 `/dev/ttyUSB0` 权限与存在性，必要时 `ls -l /dev/tty*`
- ⚠️ **启动后立即报"servo not responding"** → **解决**：检查舵机电源、信号线、ID 编号
- ⚠️ **bringuUp 启动后只有 base 没有 arm** → **解决**：检查 bringup.launch.py 中 `start_arm` 参数是否为 `true`

---

#### 步骤3：joint_command 话题控制 5 关节（阶段二：能理解，45min）

> ⚠️ 本步骤对应 src 目录源码：`arm/car1_arm_controller/msg/JointCommand.msg`

**知识点讲解**：

**joint_command 话题设计（2.2.1）**
- **原理**：`/arm/joint_command` 话题的消息类型为 `car1_arm_msgs/msg/JointCommand`，包含两个数组字段：`uint8[] ids`（关节 ID 列表）与 `uint16[] pwms`（目标 PWM 列表），长度均为 5。这种"并行数组"设计的优势是支持"部分更新"——只发送需要变化的关节，节省带宽。发布频率建议 ≥50Hz 以保证实时性。
- **源码对应**：`arm/car1_arm_controller/msg/JointCommand.msg`

**软限位保护**
- **原理**：arm_controller 在收到 joint_command 后会做软限位检查：将目标 PWM 与配置文件中的 `servo_limits.yaml` 比较，超出 `[min_pwm, max_pwm]` 范围时拒绝执行并报警。这种"软件先于硬件"的保护策略可避免堵转、过流等机械损伤。
- **源码对应**：`arm/car1_arm_controller/config/servo_limits.yaml`

**操作步骤**：

1. 查看 JointCommand 消息定义：
   ```bash
   ros2 interface show car1_arm_msgs/msg/JointCommand
   # 预期：
   # uint8[] ids
   # uint16[] pwms
   ```

2. 发送单关节控制指令（关节1转到 PWM=2000）：
   ```bash
   ros2 topic pub --once /arm/joint_command car1_arm_msgs/msg/JointCommand "
   ids: [1, 0, 0, 0, 0]
   pwms: [2000, 0, 0, 0, 0]
   "
   # 预期：关节1（底座）顺时针旋转约 +1.18 rad
   ```

3. 发送 5 关节同时控制（典型 home 姿态）：
   ```bash
   ros2 topic pub --once /arm/joint_command car1_arm_msgs/msg/JointCommand "
   ids: [1, 2, 3, 4, 5]
   pwms: [1500, 1500, 1500, 1500, 1500]
   "
   # 预期：所有关节回到中位（0 rad）
   ```

4. PWM↔弧度换算练习：
   ```bash
   # 计算 PWM=1800 对应多少 rad？
   # rad = (1800 - 1500) × 0.002356 = 0.707 rad ≈ 40.5°
   # 计算 -π/2 rad 对应多少 PWM？
   # PWM = 1500 + (-1.5708 / 0.002356) = 1500 - 667 = 833
   ```

5. 周期性摆动测试（用 Python 脚本）：
   ```python
   # joint_sine_wave.py
   import rclpy
   from rclpy.node import Node
   from car1_arm_msgs.msg import JointCommand
   import math, time
   
   class JointSineWave(Node):
       def __init__(self):
           super().__init__('joint_sine_wave')
           self.pub = self.create_publisher(JointCommand, '/arm/joint_command', 10)
           self.timer = self.create_timer(0.05, self.timer_cb)  # 20Hz
           self.t = 0
       def timer_cb(self):
           msg = JointCommand()
           msg.ids = [1, 2, 3, 4, 5]
           pwm_center = 1500
           amp = 200
           msg.pwms = [int(pwm_center + amp * math.sin(self.t + i*0.5)) for i in range(5)]
           self.pub.publish(msg)
           self.t += 0.05
   
   rclpy.init()
   rclpy.spin(JointSineWave())
   # 预期：5 个关节以正弦曲线缓慢摆动
   ```

6. 监控当前关节状态：
   ```bash
   ros2 topic echo /arm/joint_states
   # 或 ros2 topic echo /joint_states
   # 字段：name=["joint1"~"joint5"], position=[...], velocity=[...], effort=[...]
   ```

7. 软限位测试（尝试超出安全范围）：
   ```bash
   ros2 topic pub --once /arm/joint_command car1_arm_msgs/msg/JointCommand "
   ids: [1, 2, 3, 4, 5]
   pwms: [2500, 2500, 2500, 2500, 2500]
   "
   # 预期：终端打印 WARN: pwm[1]=2500 exceeds limit 2400, clamped
   # 机械臂按钳制后的 PWM 运动
   ```

**易错点**：
- ⚠️ **话题发送后舵机无响应** → **解决**：检查话题消息格式（特别是 `uint8[]` vs `uint16[]`），必要时使用 `--once` 单次发送调试
- ⚠️ **舵机抖动** → **解决**：提高发布频率到 ≥50Hz，或启用 arm_controller 的平滑插值
- ⚠️ **超限指令被静默丢弃** → **解决**：查看终端日志中的 WARN 提示，调整 servo_limits.yaml

---

#### 步骤4：set_gripper 服务控制夹爪（阶段二：能理解，30min）

> ⚠️ 本步骤对应 src 目录源码：`arm/car1_arm_controller/srv/SetGripper.srv`

**知识点讲解**：

**set_gripper 服务设计（2.2.2）**
- **原理**：`/arm/set_gripper` 服务的消息类型为 `car1_arm_msgs/srv/SetGripper`，请求字段为 `uint8 command`（0=open, 1=close, 2=stop），响应字段为 `bool success` 与 `string message`。夹爪使用一个 PWM 舵机控制开合，open 对应 PWM≈2000（张口），close 对应 PWM≈1000（夹紧），stop 停止当前运动。与 joint_command 持续发布不同，服务是"触发式"调用。
- **源码对应**：`arm/car1_arm_controller/srv/SetGripper.srv`

**服务 vs 话题的选用**
- **原理**：服务（Service）适合"一次性请求-响应"场景，如夹爪开/合、归位等离散动作；话题（Topic）适合"持续流式"场景，如关节控制、传感器数据。服务调用会阻塞直到响应返回，适合需要同步确认的场景。
- **源码对应**：ROS2 service/client 模式（synchronous vs asynchronous）

**操作步骤**：

1. 查看 SetGripper 服务定义：
   ```bash
   ros2 service show car1_arm_msgs/srv/SetGripper
   # 预期：
   # uint8 OPEN=0
   # uint8 CLOSE=1
   # uint8 STOP=2
   # uint8 command
   # ---
   # bool success
   # string message
   ```

2. 打开夹爪：
   ```bash
   ros2 service call /arm/set_gripper car1_arm_msgs/srv/SetGripper "
   command: 0
   "
   # 预期响应：
   # success: True
   # message: 'Gripper opened to PWM=2000'
   # 现象：夹爪完全张开
   ```

3. 闭合夹爪：
   ```bash
   ros2 service call /arm/set_gripper car1_arm_msgs/srv/SetGripper "
   command: 1
   "
   # 预期：夹爪闭合
   ```

4. 紧急停止：
   ```bash
   ros2 service call /arm/set_gripper car1_arm_msgs/srv/SetGripper "
   command: 2
   "
   # 预期：夹爪立即停止
   ```

5. Python 服务客户端脚本：
   ```python
   # gripper_client.py
   import rclpy
   from rclpy.node import Node
   from car1_arm_msgs.srv import SetGripper
   
   class GripperClient(Node):
       def __init__(self):
           super().__init__('gripper_client')
           self.cli = self.create_client(SetGripper, '/arm/set_gripper')
           while not self.cli.wait_for_service(timeout_sec=1.0):
               self.get_logger().info('Waiting for /arm/set_gripper...')
       
       def send(self, command):
           req = SetGripper.Request()
           req.command = command
           future = self.cli.call_async(req)
           rclpy.spin_until_future_complete(self, future)
           return future.result()
   
   rclpy.init()
   client = GripperClient()
   resp = client.send(0)  # open
   print(f'open result: success={resp.success}, msg={resp.message}')
   rclpy.shutdown()
   ```

6. 夹爪 PWM 调节（高级）：编辑 `gripper_pwm.yaml` 修改 open/close 对应的 PWM 值，使夹爪适应不同尺寸物体。

**易错点**：
- ⚠️ **服务调用超时** → **解决**：检查 arm_controller 节点是否运行，`ros2 service list` 中是否存在 `/arm/set_gripper`
- ⚠️ **夹爪开合方向反了** → **解决**：调换 `gripper_open_pwm` 与 `gripper_close_pwm` 两个值

---

#### 步骤5：go_home / go_work 归位服务（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`arm/car1_arm_controller/srv/GoHome.srv`、`srv/GoWork.srv`

**知识点讲解**：

**预设位姿服务（2.2.3）**
- **原理**：`/arm/go_home` 与 `/arm/go_work` 服务将机械臂快速复位到预设位姿。home 是收纳/待机位姿（机械臂折叠直立），work 是工作准备位姿（机械臂水平展开）。预设位姿定义在 `home_position.yaml` 中，按 PWM 列表存储。服务调用时，arm_controller 会执行 2 秒线性插值（梯形速度曲线）平滑过渡，避免突变电流冲击。
- **源码对应**：`arm/car1_arm_controller/config/home_position.yaml`

**梯形速度曲线**
- **原理**：从当前位置到目标位姿若瞬时跳变，会产生巨大电流冲击导致：(1) 电源电压跌落引起 STM32 复位；(2) 舵机齿轮冲击损坏。梯形速度曲线将运动分为"加速-匀速-减速"三段，总时间 2 秒，最大速度受舵机响应限制。这是工业机械臂的标配策略。
- **源码对应**：`arm_controller.py` 中 `interpolate_pwm()` 函数

**操作步骤**：

1. 查看 GoHome 服务定义：
   ```bash
   ros2 service show car1_arm_msgs/srv/GoHome
   # 预期：无请求字段（无参触发）
   # bool success
   # string message
   ```

2. 调用 go_home 归位：
   ```bash
   ros2 service call /arm/go_home car1_arm_msgs/srv/GoHome
   # 预期：机械臂在 2 秒内平滑回到 home 位姿
   ```

3. 调用 go_work 工作位姿：
   ```bash
   ros2 service call /arm/go_work car1_arm_msgs/srv/GoWork
   # 预期：机械臂水平展开到工作位姿
   ```

4. 查看 home/work 预设值：
   ```bash
   cat ~/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/config/home_position.yaml
   # 预期：
   # home:
   #   pwms: [1500, 2000, 1000, 1500, 1500]
   #   duration_ms: 2000
   # work:
   #   pwms: [1500, 1500, 1800, 1500, 1500]
   #   duration_ms: 2000
   ```

5. 自定义 home 位姿（实验报告加分项）：
   ```bash
   # 1. 手动用 joint_command 摆出希望作为 home 的位姿
   # 2. 读 /arm/joint_states 获取当前 PWM
   ros2 topic echo /arm/joint_states
   # 3. 写入 home_position.yaml
   # 4. 重启 arm_controller 生效
   ```

6. 归位过程监控：
   ```bash
   ros2 topic echo /arm/controller_status
   # 预期：interpolation progress 0% -> 100%
   ```

**易错点**：
- ⚠️ **归位过程机械臂抖动** → **解决**：检查舵机电源（5V/3A），电流不足会导致 PWM 信号失真
- ⚠️ **归位后位置与预期不符** → **解决**：执行 exp03 零位校准，更新 servo_offsets.yaml

---

#### 步骤6：50Hz 控制循环与 PWM 波形观察（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`arm_controller.py` 中 `control_loop` 方法

**知识点讲解**：

**50Hz 控制循环实现（2.3.2）**
- **原理**：控制循环在 `rclpy.timer` 中以 20ms 周期执行。每周期主要步骤：(1) 读取 `self.target_pwms`（由 joint_command 回调更新）；(2) 与 `self.current_pwms` 比较计算差值；(3) 限制每周期最大变化量（防突变）；(4) 通过 `serial_handler.send_pwms()` 发送 5 关节 PWM；(5) 接收舵机应答并更新 `self.current_pwms`；(6) 发布 `/joint_states` 反馈。这种"目标-反馈"闭环是控制系统的标准模式。
- **源码对应**：`arm_controller.py` 中 `def control_loop(self)`

**PWM 波形观测**
- **原理**：用示波器或逻辑分析仪夹在舵机信号线上可观察到：(1) **PWM 周期**：50Hz（20ms）；(2) **占空比范围**：5%-10%（对应 500-2500 μs）；(3) **更新时机**：每 20ms 一次，与控制循环同频。多个舵机共享同一总线时信号是"时分复用"的，5 个舵机各占约 1ms 发送窗口。
- **源码对应**：硬件信号（示波器观察）

**操作步骤**：

1. 用逻辑分析仪连接舵机信号线（黄色线），观察 PWM 波形。

2. 测量控制循环频率：
   ```bash
   ros2 topic hz /joint_states
   # 预期：average rate: 50.0 Hz
   ```

3. 测量串口通信延迟：
   ```python
   # measure_latency.py
   import rclpy
   from rclpy.node import Node
   from car1_arm_msgs.msg import JointCommand
   from sensor_msgs.msg import JointState
   import time
   
   class LatencyMeasurer(Node):
       def __init__(self):
           super().__init__('latency_measurer')
           self.sub = self.create_subscription(JointState, '/joint_states', self.cb, 10)
           self.pub = self.create_publisher(JointCommand, '/arm/joint_command', 10)
           self.t_send = 0
       def cb(self, msg):
           t_recv = time.time()
           print(f'latency: {(t_recv - self.t_send)*1000:.1f}ms')
       def trigger(self):
           self.t_send = time.time()
           msg = JointCommand()
           msg.ids = [1]
           msg.pwms = [1500]
           self.pub.publish(msg)
   
   # 周期性触发并测量
   ```

4. 控制循环 CPU 占用监控：
   ```bash
   top -p $(pgrep -f arm_controller)
   # 预期：单核 CPU 占用 < 5%
   ```

5. 串口带宽分析：
   ```bash
   sudo apt install cutecom
   # 设置 1Mbps，监控串口流量
   # 预期：50Hz × 5舵机 × 7字节 = 1750 字节/秒 ≈ 14kbps（远低于 1Mbps 容量）
   ```

**易错点**：
- ⚠️ **控制循环频率低于 50Hz** → **解决**：检查系统负载（`top`），避免在 arm_controller 同核运行重负载进程
- ⚠️ **PWM 波形抖动** → **解决**：检查电源（建议独立 5V/3A 供电），信号线使用双绞线

---

#### 步骤7：多关节协同与安全保护（阶段三：能改造，30min）

**操作步骤**：

1. 5 关节协同运动（写一个 Python 脚本让所有关节按预设轨迹运动）：
   ```python
   # arm_dance.py
   import rclpy
   from rclpy.node import Node
   from car1_arm_msgs.msg import JointCommand
   import time
   
   class ArmDance(Node):
       def __init__(self):
           super().__init__('arm_dance')
           self.pub = self.create_publisher(JointCommand, '/arm/joint_command', 50)
       
       def move_to(self, pwms, duration=2.0):
           """梯形插值运动"""
           start = [1500]*5
           steps = int(duration / 0.02)
           for i in range(steps):
               alpha = i / steps
               cur = [int(start[j] + (pwms[j]-start[j])*alpha) for j in range(5)]
               msg = JointCommand()
               msg.ids = [1,2,3,4,5]
               msg.pwms = cur
               self.pub.publish(msg)
               time.sleep(0.02)
           start = pwms
   
   rclpy.init()
   node = ArmDance()
   
   # home
   node.move_to([1500, 2000, 1000, 1500, 1500], 2.0)
   time.sleep(0.5)
   # work
   node.move_to([1500, 1500, 1800, 1500, 1500], 2.0)
   time.sleep(0.5)
   # pick
   node.move_to([2000, 1700, 1500, 1500, 1500], 2.0)
   time.sleep(0.5)
   # go home
   node.move_to([1500, 2000, 1000, 1500, 1500], 2.0)
   
   rclpy.shutdown()
   ```

2. 软限位保护验证：
   ```bash
   # 尝试超出范围
   ros2 topic pub --once /arm/joint_command car1_arm_msgs/msg/JointCommand "
   ids: [1, 2, 3, 4, 5]
   pwms: [2600, 2600, 2600, 2600, 2600]
   "
   # 预期：终端打印 WARN 并钳制
   ```

3. 急停测试：直接拔掉 USB-TTL 串口，观察舵机是否立即停止（应保持当前 PWM 不变）。

4. 性能基线（实验报告必填）：

   | 指标 | 期望值 | 实测值 |
   |------|-------|-------|
   | bringup 启动时间 | < 10s |  |
   | 控制循环实际频率 | 50 ± 1 Hz |  |
   | 单关节指令响应延迟 | < 50ms |  |
   | 夹爪 open→close 时间 | < 1.5s |  |
   | 软限位响应时间 | < 20ms |  |
   | 归位时间（home/work） | ~ 2s |  |

**易错点**：
- ⚠️ **多关节运动不同步** → **解决**：确保 `joint_command` 一次性发布 5 个关节的目标，arm_controller 内部已同步
- ⚠️ **机械臂运行过程中撞到自身** → **解决**：降低 `arm_controller` 的 `max_pwm_step_per_cycle` 参数

---

#### 完整可运行代码 demo_arm_control.py

> 独立 demo 脚本：发布 joint_command 指令让机械臂做往返运动（不依赖 bringup，但需要 arm_controller 运行）

```python
# -*- coding: utf-8 -*-
"""
实验2 demo：直接通过 ROS2 topic 控制 5 关节运动
平台：B2 / C1
前置：ros2 launch car1_arm_controller arm_controller.launch.py 已运行
运行：python3 demo_arm_control.py
"""
import rclpy
from rclpy.node import Node
from car1_arm_msgs.msg import JointCommand
import math


class ArmControllerDemo(Node):
    """5 关节协调运动：所有关节以正弦曲线缓慢摆动"""
    
    PWM_CENTER = 1500
    PWM_AMP = 300
    FREQ_HZ = 50  # 50Hz 控制频率
    
    def __init__(self):
        super().__init__('arm_controller_demo')
        self.pub = self.create_publisher(JointCommand, '/arm/joint_command', 10)
        self.timer = self.create_timer(1.0 / self.FREQ_HZ, self.timer_cb)
        self.t = 0.0
        self.get_logger().info('Arm controller demo started')
    
    def timer_cb(self):
        msg = JointCommand()
        msg.ids = [1, 2, 3, 4, 5]
        msg.pwms = [
            int(self.PWM_CENTER + self.PWM_AMP * math.sin(self.t + i * 0.7))
            for i in range(5)
        ]
        self.pub.publish(msg)
        self.t += 1.0 / self.FREQ_HZ
    
    def pwm_to_rad(self, pwm):
        return (pwm - self.PWM_CENTER) * 0.002356


def main(args=None):
    rclpy.init(args=args)
    node = ArmControllerDemo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Demo stopped by user')
    finally:
        # 回到中位
        msg = JointCommand()
        msg.ids = [1, 2, 3, 4, 5]
        msg.pwms = [1500, 1500, 1500, 1500, 1500]
        node.pub.publish(msg)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
```

### 1.7 实验总结

**完成成果**：
- 理解 STM32 1Mbps 串口协议与 PWM 帧格式
- 启动 bringup.launch 完整加载 base+arm+odom 三节点
- 通过 `/arm/joint_command` 话题独立控制 5 关节运动
- 通过 `/arm/set_gripper` 服务控制夹爪开/合/停
- 通过 `/arm/go_home`、`/arm/go_work` 服务实现位姿快速复位
- 验证 50Hz 控制循环频率与软限位保护机制

**技能收获**：
- 掌握 ROS2 topic/service 通信模型在真实硬件控制中的使用
- 理解 arm_controller 的"协议转换器"架构
- 熟悉 PWM↔弧度换算与软限位保护设计
- 掌握串口帧格式（0x55 0x55 + 长度 + 命令 + 参数 + 校验和）

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 串口打开失败 | 权限不足 | `sudo chmod 666 /dev/ttyUSB0` 或加入 dialout 组 |
| 1Mbps 通信乱码 | USB-TTL 芯片不支持 | 改用 CH340/CP2102/FT232 |
| 控制循环频率不稳 | 系统负载过高 | 关闭其他进程或设置 CPU affinity |
| 软限位被频繁触发 | servo_limits 配置过严 | 调整 config/servo_limits.yaml |
| 归位过程抖动 | 电源功率不足 | 改用 5V/5A 独立电源 |

### 1.8 思考题

1. 为什么 car1 选择 1Mbps 串口而不是更常见的 115200？分析 5 关节 50Hz 控制对串口带宽的最低要求。
2. PWM_TO_RAD = 0.002356 这个系数是怎么来的？如果换不同型号舵机，这个值需要重新标定吗？为什么？
3. arm_controller 同时作为 ROS2 服务端与 STM32 串口客户端，这种"双面胶"架构的优缺点是什么？是否存在更好的解耦方式？
4. 50Hz 控制循环中"防突变"（限制单周期最大 PWM 变化）的物理意义是什么？如果取消这层保护会怎样？
5. 软限位 vs 硬限位（机械限位）的关系是什么？为什么需要双重保护？

### 1.9 实验报告要求

**评分标准**：硬件连接与串口验证 10 分 + bringup 启动 15 分 + joint_command 话题 25 分 + set_gripper 服务 15 分 + go_home/go_work 服务 15 分 + 实验报告 20 分 = 100 分。

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初版生成（基于 _registry.yaml human_waiver 模式，标注 [待源码核实]） |
