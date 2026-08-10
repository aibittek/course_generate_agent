## 实验2：机械臂底层协议与控制实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/`，未复制到 `source-codes/EXP005/exp02/`。已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。后续补充源码后需触发 SourceCodeAnalysisAgent 并移除豁免。本指导书 v1.2 改用 `test_servo_direct.py` 裸机协议演示路线（原 v1.1 的 `bringup.launch.py` 路线迁移至 exp03），内容基于 `arm/car1_arm_controller/test/test_servo_direct.py` 与 `driver/car1_base_driver/car1_base_driver/board_sdk.py`（CRC8 查表参考）。

### 1.1 关联知识点

本实验对应第 2 章"总线舵机串口协议与裸机控制"，覆盖以下 9 个知识点：

- 2.1.1 1Mbps串口 > 事实 > car1 机械臂使用总线舵机（单线半双工串口协议），STM32 板以 1Mbps 波特率通信，5 个舵机共享同一总线
- 2.1.2 PWM公式 > 原理 > PWM 范围 500~2500，中位 1500，PWM_TO_RAD = 0.002356 rad/PWM
- 2.1.3 帧格式 > 概念 > 帧格式：0xAA 0x55 + 长度 + 命令 + 参数 + CRC8 校验（注意：实测串口帧头为 `0xAA 0x55`，与文档中"0x55 0x55"略有差异，以源码 board_sdk.py 为准）
- 2.1.4 CRC8校验 > 原理 > CRC8 查表校验算法，避免单比特翻转导致指令错位
- 2.2.1 串口设备 > 流程 > 串口设备识别（/dev/ttyUSB0）与权限授权（chmod 666 或加入 dialout 组）
- 2.2.2 interactive_mode > 流程 > `test_servo_direct.py` 的 interactive_mode 提供菜单驱动单舵机调试界面
- 2.2.3 动作录制 > 概念 > 通过 `save` 命令将关键位姿保存为内存中的动作列表，通过 `yaml` 命令导出为 action_player 兼容的 YAML 文件
- 2.3.1 裸机 vs ROS2 > 概念 > 裸机直接打开 /dev/ttyUSB0（不依赖 ROS2）与 ROS2 节点间接收发的对比
- 2.3.2 协议字节级 > 原理 > 1Mbps 串口下 5 关节 50Hz 控制的带宽计算（5×7=35 字节/周期，3500 字节/秒，远低于 1Mbps）

### 1.2 实验目标

1. 理解 1Mbps 串口协议的字节级细节（0xAA 0x55 帧头、CRC8 校验和、命令/参数结构） — 原理理解
2. 掌握用 Python `pyserial` 裸机打开 `/dev/ttyUSB0` 与总线舵机通信的方法 — 流程掌握
3. 独立使用 `test_servo_direct.py` 的 `interactive_mode` 交互式控制 5 个关节 + 夹爪 — 独立完成
4. 能够用 `save` / `yaml` 命令录制抓取放置动作并导出 YAML 文件（**供 exp03 的 `action_player` 消费**） — 独立完成
5. 理解为什么需要 CRC8 校验、单线半双工总线的时分复用机制 — 原理理解

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 机器人小车C1（含 STM32 板载总线舵机 ×5、1Mbps 串口、5V 电源） |
| OS | Ubuntu 22.04 + ROS2 Humble（**仅需 Python 环境，不依赖 ROS2 启动**） |
| Python | 3.10 + pyserial + pyyaml |
| 核心库 | `pyserial`（裸机串口）、`pyyaml`（YAML 导出）、`crc8`（内嵌查表） |
| 通信接口 | USB 转 TTL 串口（/dev/ttyUSB0，1Mbps 8N1） |
| 协议参数 | PWM 500-2500（μs），CENTER_PWM=1500，PWM_TO_RAD=0.002356 rad/PWM |
| **主入口** | `arm/car1_arm_controller/test/test_servo_direct.py`（**裸机协议演示**）<br>`driver/car1_base_driver/car1_base_driver/board_sdk.py`（**CRC8 查表参考**） |

> ⚠️ **不要启动 bringup**！`test_servo_direct.py` 直接占用 `/dev/ttyUSB0`，与 `bringup` 的 `base_driver` 节点互斥。运行前先 `Ctrl+C` 停掉 `bringup`。

### 1.4 实验难度

- 难度: ⭐⭐ 中
- 重点: 1Mbps 串口协议字节级理解；`interactive_mode` 交互调试；动作 YAML 录制与导出
- 难点: CRC8 查表校验算法；单线半双工总线的时分复用；串口权限问题排查

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：

1. 进入工作空间根目录：`cd ~/ros2_ws`
2. 清理可能占用串口的应用：`bash cleanup_ros.sh`（一键停止所有 ROS 节点，避免 `/dev/ttyUSB0` 冲突）
3. 进入测试脚本目录：`cd src/xflz_eai_car1/arm/car1_arm_controller/test/`
4. 启动裸机调试：`python3 test_servo_direct.py`
5. 选择模式 1（交互模式）
6. 在终端中输入 `1500 1100 2200 1850 1500`，观察 5 个关节转到工作位姿
7. 输入 `g 1000`，观察夹爪张开
8. 输入 `read`，观察终端打印 5 个舵机当前 PWM 值
9. 输入 `save`，输入名称 `pre_grasp`，将当前位姿保存为命名动作
10. 输入 `yaml`，按提示导出为 `pick_and_place.yaml`（**供 exp03 消费**）

**预期效果描述**：
- **终端打印**：交互模式启动后打印菜单，提示可用命令（`j1 j2 j3 j4 j5` / `g` / `s` / `r` / `read` / `save` / `yaml` / `home` / `work` / `play` / `free` / `load` / `quit`）
- **关节响应**：输入 5 个 PWM 值（500~2500）后，舵机立即平滑转动到目标位置
- **夹爪响应**：`g 1000` 张开、`g 1500` 闭合，夹爪按指令动作
- **读取反馈**：`read` 命令通过 0xAA 0x55 协议读取所有舵机位置，验证通信是否正常
- **YAML 导出**：`yaml` 命令生成 `arm/car1_arm_controller/config/actions/<name>.yaml`，格式与 exp03 的 `action_player` 兼容
- **示波器（可选）**：在 PWM 信号线上用示波器可看到 50Hz 控制信号、占空比 5%-10%

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：硬件连接与串口授权] --> B[步骤2：1Mbps串口验证]
    B --> C[步骤3：test_servo_direct交互模式]
    C --> D[步骤4：5关节+夹爪控制]
    D --> E[步骤5：CRC8帧格式验证]
    E --> F[步骤6：动作录制与命名]
    F --> G[步骤7：YAML导出供exp03]
    G --> H[完成]
```

---

#### 步骤1：硬件连接与串口授权（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`test_servo_direct.py` 中 `SERIAL_PORT = '/dev/ttyUSB0'` 与 `BAUDRATE = 1000000`

**知识点讲解**：

**1Mbps 串口协议物理层（2.1.1）**
- **原理**：car1 机械臂使用总线舵机（单线半双工串口协议），舵机与 STM32 板之间通过单线半双工串口（实际物理上 1 根信号线 + 1 根地线）以 1Mbps 波特率通信。所有 5 个舵机共享同一总线，通过 ID 区分（机械臂 5 关节 ID 0~4 + 夹爪 ID 5）。这种总线架构的优势是节省 IO 引脚（仅需 1 个 UART），缺点是任意时刻只能有 1 个舵机独占总线（时分复用）。
- **源码对应**：`test_servo_direct.py` 中 `SERIAL_PORT = '/dev/ttyUSB0'` 与 `BAUDRATE = 1000000`

**串口设备与权限（2.2.1）**
- **原理**：Linux 下串口设备节点位于 `/dev/ttyUSB*`（CH340/CP2102/FT232 驱动名），普通用户无读写权限。两种解决方案：(1) 临时授权 `sudo chmod 666 /dev/ttyUSB0`；(2) 加入 `dialout` 组 `sudo usermod -a -G dialout $USER`，重新登录后永久生效。
- **源码对应**：`test_servo_direct.py` 中 `try: ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)`

**操作步骤**：

1. 连接硬件：
   - 确认 STM32 控制板通过 USB-TTL 连接到工作站
   - 5 个舵机电源线（红黑）独立接到 5V/3A 电源
   - 舵机信号线（黄/白）已连接到 STM32 的 UART 引脚

2. **停止任何正在运行的 bringup**（避免 `/dev/ttyUSB0` 冲突）：
   ```bash
   # 在运行 bringup 的终端按 Ctrl+C
   # 或新终端执行：
   pkill -f bringup
   pkill -f car1_arm_controller
   ```

3. 查看串口设备：
   ```bash
   ls -l /dev/ttyUSB*
   # 预期：crw-rw---- 1 root dialout /dev/ttyUSB0
   ```

4. 临时授权串口：
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   # 验证：ls -l /dev/ttyUSB0
   # 预期：crw-rw-rw- 1 root dialout /dev/ttyUSB0
   ```

5. 永久授权（推荐）：
   ```bash
   sudo usermod -a -G dialout $USER
   # 重新登录后生效
   ```

6. 验证 1Mbps 串口通信（用 cutecom 手动发 1 字节）：
   ```bash
   sudo apt install cutecom
   cutecom --device /dev/ttyUSB0 --baud 1000000
   # 在 cutecom 中切换到 Hex 模式，发送: AA 55 05 05 00 00 00 00 CRC
   # 预期：收到舵机 0 的位置应答包（也以 AA 55 开头）
   ```

**易错点**：
- ⚠️ **串口打开失败 (Permission denied)** → **解决**：`sudo chmod 666 /dev/ttyUSB0` 或加入 dialout 组
- ⚠️ **1Mbps 通信乱码** → **解决**：检查 USB-TTL 芯片是否支持 1Mbps（CH340/CP2102/FT232 均可，PL2303 部分型号不支持）
- ⚠️ **bringup 未停止导致冲突** → **解决**：`pkill -f bringup` 后再启动 test_servo_direct
- ⚠️ **发送指令舵机无响应** → **解决**：检查 5V 电源是否独立供电（USB 通常无法驱动 5 个舵机）

---

#### 步骤2：1Mbps 串口通信验证（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`test_servo_direct.py` 中 `serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)`

**知识点讲解**：

**裸机 vs ROS2 路线对比（2.3.1）**
- **原理**：本实验采用"裸机"路线：直接用 Python `pyserial` 库打开 `/dev/ttyUSB0`，自行按协议组包发送、自行解析应答。**不依赖 ROS2 启动任何节点**。这种路线适合：(1) 协议层调试（验证 1Mbps 字节级通信）；(2) 快速验证单舵机响应；(3) 不希望 ROS2 复杂架构干扰的场景。**对比**：exp03 将采用 ROS2 路线（`bringup` + `arm_controller` 节点桥接），学生可对比两种路线的开发体验差异。
- **源码对应**：`test_servo_direct.py` 整个文件（无 ROS2 import）

**协议字节级理解（2.1.3）**
- **原理**：总线舵机的指令帧格式为（**实测以 `test_servo_direct.py` 的 `send_packet` 函数为准**）：
  ```
  帧头:   0xAA 0x55
  功能字: func (1字节, 0x05=多舵机控制/0x0B=释放扭力等)
  长度:   len(data) (1字节)
  数据:   data (N字节, 子命令+舵机ID+参数)
  校验:   CRC8 (1字节, 查表算法)
  ```
  例如让 ID=0 的舵机转到 PWM=2000、duration=2000ms 的多舵机控制帧为：
  ```
  AA 55 05 01 D0 07 01 00 E0 07 03 E0 0C XX
  ```
  （功能字 0x05 + 子命令 0x01 + duration_low + duration_high + 舵机数 0x01 + 舵机ID 0x00 + PWM_low + PWM_high + 子 duration + 校验）
- **源码对应**：`test_servo_direct.py` 中 `def send_packet(ser, func, data)` 函数（L57-61）

**操作步骤**：

1. 进入测试脚本目录：
   ```bash
   cd ~/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/test/
   ls -l test_servo_direct.py
   # 预期：存在此文件
   ```

2. 启动 `test_servo_direct.py`：
   ```bash
   python3 test_servo_direct.py
   # 预期输出：
   # 打开串口 /dev/ttyUSB0 @ 1000000...
   # 串口已打开
   #
   # 选择模式:
   #   1. 交互模式 - 手动输入PWM值调试
   #   2. 回放模式 - 执行 ACTIONS 列表
   # 输入 1 或 2:
   ```

3. 选择模式 `1`（交互模式），按 Enter：
   ```
   输入 1 或 2: 1
   # 预期：打印详细菜单
   # === 交互调试模式 ===
   # 命令:
   #   j1 j2 j3 j4 j5   - 5个关节PWM值(500~2500)
   #   g <pwm>           - 夹爪PWM值
   #   s <id> <pwm>      - 单个舵机控制
   #   r <id>            - 读取单个舵机位置
   #   read              - 读取所有舵机位置
   #   save              - 读取当前姿态并保存
   #   ...
   ```

4. 输入 `read` 测试读取：
   ```
   > read
   # 预期输出：
   # 读取舵机位置...
   #   ID    PWM
   #   ---------
   #   0    1500
   #   1    1500
   #   2    1500
   #   3    1500
   #   4    1500
   # （若通信失败，会显示"失败"）
   ```

5. 验证通信成功标准：5 个舵机均能读出 1500 附近的 PWM 值（误差 ±20 内）

**易错点**：
- ⚠️ **read 命令一直显示"失败"** → **解决**：检查 5V 电源、信号线、舵机 ID 拨码
- ⚠️ **read 返回 0 或异常值** → **解决**：可能是 CRC 校验失败，确认 baud=1000000 无误
- ⚠️ **找不到 `/dev/ttyUSB0`** → **解决**：`dmesg | grep tty` 查看插入的设备名

---

#### 步骤3：test_servo_direct interactive_mode 命令详解（阶段二：能理解，30min）

> ⚠️ 本步骤对应 src 目录源码：`test_servo_direct.py` 中 `def interactive_mode(ser)` 函数

**知识点讲解**：

**interactive_mode 设计（2.2.2）**
- **原理**：`interactive_mode` 是 `test_servo_direct.py` 提供的菜单驱动调试界面，相比 ROS2 topic 更直接、响应更快。核心命令分 5 类：(1) **位姿控制**（5 关节 PWM 一次发送 / 单舵机 / 夹爪）；(2) **状态读取**（单舵机 / 全部 / 调试模式）；(3) **动作管理**（save 命名保存 / yaml 导出 / play 回放 / list 列表 / del 删除）；(4) **力矩控制**（free 释放 / load 恢复）；(5) **快速动作**（home / work）。所有命令设计为"看到就懂"，无需文档。
- **源码对应**：`test_servo_direct.py` 中 `def interactive_mode(ser)` 函数（L308-482）

**单舵机控制 vs 5 关节协同（2.1.2）**
- **原理**：单舵机控制（`s <id> <pwm>`）用于精确调试单个关节（如找机械零位）；5 关节协同（`j1 j2 j3 j4 j5`）用于发送完整位姿。两者底层都调用 `move_servos(ser, positions, duration)` 函数，但单舵机版本会"小步快跑"（duration=1.0s），5 关节版本会"平滑过渡"（duration=2.0s）。
- **源码对应**：`test_servo_direct.py` 中 `def move_servos(ser, positions, duration)` 函数（L132-152）

**操作步骤**：

1. 测试 5 关节控制（输入工作位姿）：
   ```
   > 1500 1100 2200 1850 1500
   # 预期：5 个舵机按 2 秒时长平滑转到工作位姿
   # 终端打印：
   #   ID    PWM
   #   ---------
   #   0    1500
   #   1    1100
   #   2    2200
   #   3    1850
   #   4    1500
   ```

2. 测试夹爪控制：
   ```
   > g 1000
   # 预期：夹爪张开（1.0s 时长）
   > g 1500
   # 预期：夹爪闭合到中位
   > g 2000
   # 预期：夹爪完全闭合
   ```

3. 测试单舵机控制（找零位用）：
   ```
   > s 1 1520
   # 预期：仅关节 1（ID=1，即 J2 大臂）转到 1520，其他关节保持不动
   > s 1 1500
   # 预期：关节 1 转回 1500
   ```

4. 测试读取（debug 模式）：
   ```
   > r 1
   # 预期：舵机 1 当前位置: 1500
   > r 1 -d
   # 预期：带调试信息（已发送命令、缓冲区字节数、接收包解析）
   > read
   # 预期：一次性读 0~4 号舵机（5 个机械臂关节，跳过 ID=5 夹爪）
   ```

5. 测试 home / work 快速动作：
   ```
   > home
   # 预期：所有关节回中位 [1500,1500,1500,1500,1500]
   > work
   # 预期：进入默认工作位姿 [1500,1100,2200,1850,1500,1500]
   ```

6. 测试力矩释放（用于手动掰动找机械零位）：
   ```
   > free 1
   # 预期：舵机 1 释放扭力，可手动掰动
   > load 1
   # 预期：舵机 1 读取当前位置并锁死（恢复力矩）
   > free
   # 预期：所有 6 个舵机（含夹爪）释放扭力
   ```

**易错点**：
- ⚠️ **单舵机命令格式错误** → **解决**：注意是 `s <id> <pwm>` 不是 `s <pwm> <id>`
- ⚠️ **g 命令无响应** → **解决**：检查夹爪舵机 ID=5 是否正确连接
- ⚠️ **free 后舵机不响应任何命令** → **解决**：必须先 `load` 恢复力矩才能继续控制

---

#### 步骤4：CRC8 校验与帧格式验证（阶段二：能理解，30min）

> ⚠️ 本步骤对应 src 目录源码：`test_servo_direct.py` 中 `_CRC8_TABLE` (L29-47) 与 `crc8(data)` 函数 (L50-54)；对照参考 `driver/car1_base_driver/car1_base_driver/board_sdk.py`

**知识点讲解**：

**CRC8 查表校验算法（2.1.4）**
- **原理**：CRC8 是一种 8 位循环冗余校验，用于检测串口通信中的单比特翻转。每次发送数据帧前，先对"功能字+长度+数据"部分按 256 字节查表计算 CRC8 校验和，附加在帧尾。接收方按同样算法重算，若与接收的校验和不一致则丢弃该帧。`test_servo_direct.py` 的 CRC8 表与 `board_sdk.py` 完全一致（256 字节硬编码表）。
- **源码对应**：`test_servo_direct.py` 中 `_CRC8_TABLE` 常量（L29-47）与 `crc8(data)` 函数（L50-54）

**为什么需要 CRC8（2.3.2）**
- **原理**：1Mbps 串口在长距离或电磁干扰下可能出现单比特翻转（位错误）。没有校验时，错误数据被误执行可能导致：(1) 舵机转到错误角度（撞机械结构）；(2) 控制错位（ID 错乱）；(3) 通信死锁。CRC8 可以 100% 检测单比特错误和大多数多位错误。
- **源码对应**：`test_servo_direct.py` 中 `send_packet` 函数（L57-61）的 `crc8(bytes(buf[2:]))` 调用

**操作步骤**：

1. 查看 CRC8 查表算法源码：
   ```bash
   grep -A 30 "_CRC8_TABLE" test_servo_direct.py | head -40
   # 预期：256 字节硬编码表
   ```

2. 查看 `crc8()` 函数实现：
   ```bash
   grep -A 5 "def crc8" test_servo_direct.py
   # 预期：
   # def crc8(data):
   #     check = 0
   #     for b in data:
   #         check = _CRC8_TABLE[check ^ b]
   #     return check & 0xFF
   ```

3. 对照 board_sdk.py 验证一致性：
   ```bash
   grep -A 5 "def crc8" ~/ros2_ws/src/xflz_eai_car1/driver/car1_base_driver/car1_base_driver/board_sdk.py
   # 预期：完全相同的算法（保证协议兼容）
   ```

4. 用 Python REPL 手动计算 CRC8：
   ```python
   import sys
   sys.path.insert(0, '/path/to/test_servo_direct.py')
   from test_servo_direct import crc8, _CRC8_TABLE
   # 验证：crc8(bytes([0x05, 0x01, 0xD0, 0x07, 0x01, 0x00, 0xE0, 0x07])) 
   # 应返回正确的 CRC8 值
   ```

5. 用 cutecom 手动发一帧并观察应答：
   ```bash
   cutecom --device /dev/ttyUSB0 --baud 1000000
   # Hex 发送: AA 55 05 05 00 00 00 00 CRC
   # （CRC 由 crc8(bytes([0x05, 0x05, 0x00, 0x00, 0x00])) 计算）
   # 预期：收到舵机 0 位置应答包
   ```

6. 故意发错 CRC，观察现象：
   ```python
   # 在 Python REPL 中
   buf = [0xAA, 0x55, 0x05, 0x05, 0x00, 0x00, 0x00, 0xFF]  # 故意写错 CRC
   import serial
   ser = serial.Serial('/dev/ttyUSB0', 1000000)
   ser.write(bytes(buf))
   # 预期：舵机无响应（CRC 错误被丢弃）
   ```

**易错点**：
- ⚠️ **手动发帧无响应** → **解决**：检查帧头是否为 0xAA 0x55（不是 0x55 0x55），检查 CRC 计算是否正确
- ⚠️ **手动发帧舵机乱动** → **解决**：检查功能字 func 是否正确（多舵机控制=0x05，释放扭力=0x0B）

---

#### 步骤5：动作录制与命名快照（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`test_servo_direct.py` 中 `interactive_mode` 的 `save`/`list`/`del`/`play` 分支

**知识点讲解**：

**动作列表的内存数据结构（2.2.3）**
- **原理**：`interactive_mode` 用一个 Python 列表 `actions` 临时保存动作，每项是 3 元组 `(type, data, name)`：type 是 `'arm'` / `'gripper'` / `'home'`；data 是 PWM 列表或单值；name 是用户起的名字。内存中的动作仅在 `interactive_mode` 期间有效，**退出后丢失**（除非用 `yaml` 导出到文件）。
- **源码对应**：`test_servo_direct.py` 中 `actions = []` 与各种 `actions.append(...)` 调用

**位姿（snapshot）vs 动作（action）的区分（2.2.3 补充）**
- **原理**：**位姿（snapshot）** 是某一时刻 5 关节的 PWM 状态，是一个"点"；**动作（action）** 是一系列位姿按时间顺序排列，是一条"轨迹"。例如 "home" 是位姿，"home→pick→place→home" 是动作。本实验的 `save` 命令保存的是**位姿列表中的离散位姿**（每个都通过 `read_servo_position` 读取当前实际位置），最终由 `yaml` 命令打包成动作文件。
- **源码对应**：`test_servo_direct.py` 中 `def save_current_pose(ser, include_gripper=False)` 函数（L251-285）

**操作步骤**：

1. 录制第一个动作（`work` 命名 `pre_grasp`）：
   ```
   > work
   # 预期：进入工作位姿
   # 等待 2.5 秒
   > save
   # 预期：读取当前姿态（5 关节 PWM），提示输入名称
   # 保存? 输入名称(回车跳过): pre_grasp
   # 预期：已保存: pre_grasp
   ```

2. 录制夹爪张开动作：
   ```
   > g 1000
   # 预期：夹爪张开
   # 等待 1.5 秒
   > save
   # 提示：保存? 输入名称(回车跳过): gripper_open
   ```

3. 录制下降到位姿（命名 `grasp_down`）：
   ```
   > 1500 2000 1800 2020 1500
   # 预期：5 关节转到下降位姿
   # 等待 2.5 秒
   > save
   # 提示：保存? 输入名称(回车跳过): grasp_down
   ```

4. 录制夹爪闭合动作：
   ```
   > g 1500
   > save
   # 提示：保存? 输入名称(回车跳过): gripper_close
   ```

5. 录制抬升位姿（命名 `lift`）：
   ```
   > 2000 1800 2000 2000 1500
   > save
   # 提示：保存? 输入名称(回车跳过): lift
   ```

6. 录制返回工作位姿：
   ```
   > 1500 1100 2200 1850 1500
   > save
   # 提示：保存? 输入名称(回车跳过): back_work
   ```

7. 查看已保存动作：
   ```
   > list
   # 预期打印：
   #   1. [pre_grasp] arm: [1500, 1100, 2200, 1850, 1500]
   #   2. [gripper_open] gripper: 1000
   #   3. [grasp_down] arm: [1500, 2000, 1800, 2020, 1500]
   #   4. [gripper_close] gripper: 1500
   #   5. [lift] arm: [2000, 1800, 2000, 2000, 1500]
   #   6. [back_work] arm: [1500, 1100, 2200, 1850, 1500]
   ```

8. 试播验证：
   ```
   > play
   # 预期：依次回放 6 个动作（每个 2~3 秒）
   ```

9. 删除错误动作（如果录错）：
   ```
   > del 3
   # 预期：已删除: grasp_down
   ```

**易错点**：
- ⚠️ **保存时没等待舵机到位** → **解决**：`save` 命令会自动 `read_servo_position` 读当前位置，但建议手动等待 2-3 秒
- ⚠️ **动作列表在 quit 后丢失** → **解决**：必须用 `yaml` 导出到文件，否则下次启动要从头录
- ⚠️ **play 时机械臂乱动** → **解决**：检查动作顺序与命名（错误的位姿会损坏机械结构）

---

#### 步骤6：YAML 文件导出（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`test_servo_direct.py` 中 `def export_yaml(actions, output_path=None)` 函数（L504-547）

**知识点讲解**：

**action_player 兼容的 YAML 格式（2.2.3）**
- **原理**：`export_yaml` 导出的 YAML 文件格式与 `action_player.py` 严格兼容，结构为：
  ```yaml
  name: <动作组名>
  description: <描述>
  actions:
    - name: <步名>
      duration: <秒>
      servos: {<id>: <pwm>, ...}
    - ...
  ```
  文件默认输出到 `arm/car1_arm_controller/config/actions/<name>.yaml`（`get_package_share_directory` 路径）。
- **源码对应**：`test_servo_direct.py` 中 `def export_yaml` (L504-547) 与 `action_player.py` 中 `def _load_action` (L90-120)

**colcon build 后 YAML 才生效（2.2.3 补充）**
- **原理**：YAML 文件位于 ROS2 包的 `share/<pkg>/config/actions/` 目录，必须 `colcon build --packages-select car1_arm_controller` 重新安装到 `install/` 目录，exp03 的 `action_player` 节点才能通过 `get_package_share_directory` 找到。这是 ROS2 包内资源访问的标准机制。
- **源码对应**：`action_player.py` L48 `pkg_share = get_package_share_directory('car1_arm_controller')`

**操作步骤**：

1. 在 interactive_mode 中输入 `yaml`：
   ```
   > yaml
   # 预期：依次询问参数组名与描述
   # 动作组名称 (如 pick_front): pick_and_place
   # 描述 (回车跳过): pick and place demo
   ```

2. 确认导出路径：
   ```
   # 预期打印：
   #   已导出到: /home/<user>/ros2_ws/install/car1_arm_controller/share/car1_arm_controller/config/actions/pick_and_place.yaml
   #   动作步数: 6
   #   使用方法:
   #     ros2 run car1_arm_controller action_player --ros-args -p action_file:=pick_and_place
   ```

3. 重新编译 ROS2 包（让 install 目录更新）：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select car1_arm_controller
   source install/setup.bash
   ```

4. 查看导出的 YAML 文件：
   ```bash
   cat ~/ros2_ws/install/car1_arm_controller/share/car1_arm_controller/config/actions/pick_and_place.yaml
   # 预期：6 个 action 步骤，每步包含 name/duration/servos
   ```

5. （**为 exp03 准备**）保持 YAML 文件存在，下一个实验（exp03）将用 `action_player` 节点回放

6. 退出 interactive_mode：
   ```
   > quit
   # 预期：串口已关闭
   ```

**易错点**：
- ⚠️ **yaml 命令后找不到文件** → **解决**：检查 `install/` 目录是否存在，必须 `colcon build` 才会复制
- ⚠️ **YAML 字段名错误** → **解决**：必须是 `name` / `description` / `actions`（小写），与 `action_player.py` 严格匹配
- ⚠️ **duration 单位混淆** → **解决**：YAML 中 duration 单位是**秒**（不是毫秒），`action_player` 会自动转换

---

#### 步骤7：综合练习与带宽分析（阶段三：能改造，30min）

> ⚠️ 本步骤综合应用本实验全部知识点，含协议分析、带宽计算、错误排查

**操作步骤**：

1. **带宽计算练习**（用 2.1.2 知识点）：
   ```
   # 5 关节 50Hz 控制，每周期发 5 舵机 × 7 字节 = 35 字节
   # 每秒 50 × 35 = 1750 字节/秒 ≈ 14 kbps
   # 1Mbps = 1000 kbps，使用率仅 1.4%
   # 留出 98.6% 带宽给其他通信（如 IMU 反馈、舵机状态查询）
   ```

2. **多关节协同运动**（写一个 Python 脚本调用 `move_servos`）：
   ```python
   # arm_sine_wave.py
   import serial
   import struct
   import time
   import math
   from test_servo_direct import move_servos, SERIAL_PORT, BAUDRATE
   
   ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
   ser.rts = False
   ser.dtr = False
   time.sleep(0.2)
   
   t = 0.0
   while True:
       try:
           pwm_center = 1500
           amp = 100
           pwms = [[i, int(pwm_center + amp * math.sin(t + i * 0.5))] for i in range(5)]
           move_servos(ser, pwms, duration=0.05)
           t += 0.05
       except KeyboardInterrupt:
           # 回到 home
           move_servos(ser, [[i, 1500] for i in range(5)], duration=2.0)
           break
   
   ser.close()
   ```
   预期：5 个关节以正弦曲线缓慢摆动，按 Ctrl+C 回到 home

3. **软限位保护验证**（尝试超出范围）：
   ```python
   # 在 Python REPL
   move_servos(ser, [[0, 300], [1, 2700], [2, 1500], [3, 1500], [4, 1500]], duration=1.0)
   # 预期：move_servos 函数内部 clamp 到 [500, 2500]，舵机不会超出物理范围
   ```

4. **通信稳定性测试**（连续 100 次 read）：
   ```python
   from test_servo_direct import read_servo_position
   success_count = 0
   for i in range(100):
       pos = read_servo_position(ser, 0)
       if pos is not None:
           success_count += 1
   print(f'成功率: {success_count}/100 = {success_count}%')
   # 预期：成功率 ≥ 99%（CRC 校验保证偶尔的错误会被丢弃）
   ```

5. **性能基线（实验报告必填）**：

   | 指标 | 期望值 | 实测值 |
   |------|-------|-------|
   | interactive_mode 启动时间 | < 2s |  |
   | 5 关节指令响应延迟 | < 50ms |  |
   | 单舵机 read 响应时间 | < 20ms |  |
   | CRC 校验 100 次成功率 | ≥ 99% |  |
   | 1Mbps 串口实际带宽利用率 | ~1.4% |  |

**易错点**：
- ⚠️ **多关节运动不同步** → **解决**：检查 `move_servos` 是否在同一次 `send_packet` 中发送 5 舵机
- ⚠️ **Ctrl+C 后舵机停在奇怪角度** → **解决**：在 except 块中发送 home 位姿
- ⚠️ **CRC 校验失败率过高（>5%）** → **解决**：检查 USB-TTL 芯片质量、串口线长度、波特率误差

---

#### 完整可运行代码 demo_bare_metal_arm.py

> 独立 demo 脚本：纯 Python 裸机控制舵机做往返运动（不依赖 bringup、不依赖 ROS2）

```python
# -*- coding: utf-8 -*-
"""
实验2 demo：纯 Python 裸机控制机械臂（不通过 ROS2）
平台：B2 / C1
前置：test_servo_direct.py 可正常 import
运行：python3 demo_bare_metal_arm.py
"""
import sys
import os
import time
import math

# 把 test_servo_direct.py 所在目录加入 path
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__),
    '../../ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/test'
))

from test_servo_direct import (
    SERIAL_PORT, BAUDRATE, move_servos, read_all_servos
)
import serial


def main():
    print(f"打开串口 {SERIAL_PORT} @ {BAUDRATE}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
        ser.rts = False
        ser.dtr = False
    except Exception as e:
        print(f"串口打开失败: {e}")
        return

    print("串口已打开")
    time.sleep(0.2)

    # 1. 读取初始位置
    print("\n[1] 读取初始位置:")
    read_all_servos(ser)

    # 2. 转到工作位姿
    print("\n[2] 转到工作位姿 [1500, 1100, 2200, 1850, 1500]")
    work_pwms = [[i, pwm] for i, pwm in enumerate([1500, 1100, 2200, 1850, 1500])]
    move_servos(ser, work_pwms, duration=2.0)
    time.sleep(2.5)

    # 3. 正弦摆动 10 秒
    print("\n[3] 正弦摆动 10 秒（按 Ctrl+C 中断）")
    t = 0.0
    pwm_center = 1500
    amp = 100
    try:
        while t < 10.0:
            pwms = [[i, int(pwm_center + amp * math.sin(t + i * 0.5))] for i in range(5)]
            move_servos(ser, pwms, duration=0.05)
            t += 0.05
    except KeyboardInterrupt:
        print("中断")

    # 4. 回到 home
    print("\n[4] 回到 home [1500, 1500, 1500, 1500, 1500]")
    home_pwms = [[i, 1500] for i in range(5)]
    move_servos(ser, home_pwms, duration=2.0)
    time.sleep(2.5)

    # 5. 最终位置确认
    print("\n[5] 最终位置:")
    read_all_servos(ser)

    ser.close()
    print("\n串口已关闭")


if __name__ == '__main__':
    main()
```

### 1.7 实验总结

**完成成果**：
- 理解 1Mbps 串口协议的字节级细节（0xAA 0x55 帧头、CRC8 校验和、命令/参数结构）
- 掌握 Python `pyserial` 裸机打开 `/dev/ttyUSB0` 与总线舵机通信的方法
- 独立使用 `test_servo_direct.py` 的 `interactive_mode` 交互式控制 5 关节 + 夹爪
- 验证 `save` / `yaml` 命令录制动作并导出与 `action_player` 兼容的 YAML 文件（**供 exp03 消费**）
- 理解 CRC8 查表校验算法和单线半双工总线的时分复用机制

**技能收获**：
- 掌握 1Mbps 串口协议（0xAA 0x55 + 长度 + 命令 + 参数 + CRC8 校验和）
- 理解"裸机 vs ROS2"两条开发路线的对比（裸机直接 / ROS2 间接）
- 熟悉 `interactive_mode` 全部命令（位姿/读取/动作/力矩/快速动作）
- 掌握动作 YAML 录制与导出（为 exp03 的 `action_player` 做准备）

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 串口打开失败 | 权限不足 | `sudo chmod 666 /dev/ttyUSB0` 或加入 dialout 组 |
| 1Mbps 通信乱码 | USB-TTL 芯片不支持 | 改用 CH340/CP2102/FT232 |
| CRC 校验失败率高 | 电磁干扰 / 串口线过长 | 缩短串口线、远离干扰源 |
| bringup 串口冲突 | 两者都占用 /dev/ttyUSB0 | `pkill -f bringup` 后再启动 test_servo_direct |
| 找不到导出的 YAML | 未 colcon build | `cd ~/ros2_ws && colcon build --packages-select car1_arm_controller` |

### 1.8 思考题

1. 为什么 car1 选择 1Mbps 串口而不是更常见的 115200？分析 5 关节 50Hz 控制对串口带宽的最低要求。
2. PWM_TO_RAD = 0.002356 这个系数是怎么来的？如果换不同型号舵机，这个值需要重新标定吗？为什么？
3. 串口帧格式中"功能字 func"的设计有什么好处？与 ROS2 topic 消息类型相比有什么异同？
4. CRC8 校验能 100% 检测单比特错误和大多数多位错误，但是否存在 CRC8 也检测不到的错误模式？如果存在该如何增强？
5. 单线半双工总线的"时分复用"是如何保证 5 个舵机不会同时响应的？硬件层和协议层各做了什么？
6. 为什么本实验不通过 ROS2 启动 arm_controller 节点而是直接用 `test_servo_direct.py`？对比两条开发路线的优缺点。

### 1.9 实验报告要求

**评分标准**：硬件连接与串口授权 10 分 + 1Mbps 协议验证 15 分 + interactive_mode 交互调试 25 分 + CRC8 与帧格式 15 分 + 动作录制与 YAML 导出 15 分 + 实验报告 20 分 = 100 分。

**实验报告必含项**：
- [ ] `cutecom` 手动发送一帧并截图（验证协议）
- [ ] `interactive_mode` 5 关节 + 夹爪控制演示截图或视频
- [ ] 录制的 `pick_and_place.yaml` 文件内容（将作为 exp03 的输入）
- [ ] CRC8 校验 100 次成功率的实测数据
- [ ] 思考题 6 题全部作答

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初版生成（基于 _registry.yaml human_waiver 模式，标注 [待源码核实]） |
| v1.1 | 2026-08-10 | （保留原 v1.1 记录：删除 LewanSoul/Hiwonder 品牌信息，替换为"总线舵机"） |
| **v1.2** | 2026-08-10 | **重大重构：放弃 `bringup.launch.py` + `arm_controller` 节点路线，改为 `test_servo_direct.py` 裸机协议演示**。原因：用户反馈 exp02 主题是"底层协议"，应直接演示 1Mbps 串口与 CRC8 校验字节级细节，而非 ROS2 高级封装；新方案让 exp02 真正"裸机"（不依赖 ROS2），输出 `pick_and_place.yaml` 供 exp03 消费；1.1 知识点扩展为 9 个（新增 2.1.4 CRC8、2.2.1 串口设备、2.2.2 interactive_mode、2.2.3 动作录制、2.3.1 裸机 vs ROS2、2.3.2 协议字节级），1.6 重写为 7 步裸机协议演示流程（硬件连接→1Mbps 验证→interactive_mode 命令→CRC8 验证→动作录制→YAML 导出→综合练习） |
