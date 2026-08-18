## 实验6：ROS2话题通讯（MQ5气体传感器）（4h）

### 一、关联知识点

本实验关联以下知识图谱节点：

| 编号 | 知识点名称 | 类型 | 层级路径 |
|------|-----------|------|---------|
| 2.2.1 | 话题通信异步发布/订阅一对多模型 | 概念 | 第2章 ROS2核心通信机制 → 2.2 话题通信 |
| 2.2.2 | DDS 全局数据空间与 QoS 传输策略原理 | 原理 | 第2章 ROS2核心通信机制 → 2.2 话题通信 |
| 2.2.3 | create_publisher/create_subscription 编程流程 | 流程 | 第2章 ROS2核心通信机制 → 2.2 话题通信 |
| 2.2.4 | MQ5 传感器 ADC 采集 → Float32 消息发布全链路 | 流程 | 第2章 ROS2核心通信机制 → 2.2 话题通信 |

### 二、实验目标

通过本实验的学习，学生能够：

1. **原理理解**：阐述 ROS2 话题通信的异步发布/订阅模型——Publisher 与 Subscriber 通过话题名称解耦，DDS 自动完成发现、连接与消息分发，并说明 QoS 三要素（Reliability、Durability、History Depth）对通信行为的影响
2. **流程掌握**：掌握 `ros_sensor` 包中 `gas_sensor_node`（发布）与 `gas_monitor`（订阅）两个节点从参数声明、QoS 配置到消息收发回调的完整编程链路
3. **独立完成**：独立运行 MQ5 发布/订阅节点，使用 `ros2 topic echo/hz/info` 观察实时浓度、发布频率与话题类型，并通过 `--ros-args -p` 动态调整 `publish_period` 与 `alarm_threshold` 参数
4. **迁移应用**：能够将「ADC 采集 → 物理量换算 → Float32 消息发布」的话题通信模型迁移到其它持续数据流场景（如 DHT11 温湿度、MAX30102 心率血氧等传感器节点）

### 三、实验环境

| 类别 | 配置 |
|------|------|
| 硬件平台 | 具身智能实验箱B2 或 具身智能机器人小车C1（集成 MQ5 可燃气体传感器） |
| 操作系统 | Ubuntu 22.04 + ROS2 Humble |
| 核心依赖 | `rclpy`、`std_msgs` |
| 开发语言 | Python 3.10 |
| 源码位置 | `~/ros2_ws/src/xflz_eai_car1/driver/ros_sensor`（节点包 `ros_sensor`） |
| 传感器接口 | MQ5 可燃气体传感器，ADC 模拟量采集（sysfs IIO 设备，默认 `/sys/bus/iio/devices/iio:device0` 通道 7） |

> 说明：本实验的 MQ5 读取逻辑封装在 `common.py` 的 `read_mq5_once()` 中，通过 Linux IIO sysfs 接口读取 ADC 原始值。无需 `sudo` 权限。

### 四、实验难度

| 维度 | 说明 |
|------|------|
| 难度等级 | ⭐⭐（中等） |
| 实验类型 | 设计性 |
| 建议时长 | 4 学时（180 分钟） |

**重点**：
- 掌握 Publisher/Subscriber 的标准编程流程：`create_publisher` → 构造消息 → `publish`；`create_subscription` → 注册回调 → 处理数据
- 理解 `Float32` 标准消息类型与 QoS `Reliable + KeepLast(10)` 的配置方法
- 掌握 MQ5 传感器从 ADC 原始值到电压、再到 ppm 浓度的对数换算原理

**难点**：
- MQ5 灵敏特性曲线（对数坐标）下 `voltage_to_ppm` 的换算推导
- QoS 三种核心策略（Reliability、Durability、History Depth）对通信行为的实际影响

### 五、实验现象

#### 5.1 快速验证流程

完成本实验后，你应能观察到以下现象：

1. 终端 A 启动 `gas_sensor_node` 后，持续输出 `raw`（ADC 原始值）、`voltage`（电压）和 `ppm`（浓度）
2. 终端 B 启动 `gas_monitor` 后，同步打印接收到的浓度值，与发布端完全一致
3. `ros2 node list` 同时显示 `/gas_sensor_node` 和 `/gas_monitor` 两个节点
4. `ros2 topic info /gas_sensor` 显示 Type: `std_msgs/msg/Float32`，Publisher count: 1，Subscription count: 1
5. `ros2 topic hz /gas_sensor` 显示发布频率约 1Hz（由 `publish_period` 决定）
6. 使用 `ros2 topic echo /gas_sensor` 作为第三方订阅者，可同时接收数据
7. 关闭发布节点后，订阅节点静默等待（不报错，只是无新数据到达）

#### 5.2 预期效果描述

| 操作 | 预期输出 |
|------|---------|
| `ros2 run ros_sensor gas_sensor_node` | 每秒输出 `raw=1234 voltage=1.20V ppm=312.45` |
| `ros2 run ros_sensor gas_monitor`（另一终端） | 每秒输出 `浓度正常: 312.45 ppm` |
| `ros2 topic info /gas_sensor` | Type: `std_msgs/msg/Float32`, Publishers: 1, Subscribers: 2（含 echo） |
| `ros2 topic hz /gas_sensor` | average rate: 1.000 Hz |
| 调低阈值：`gas_monitor --ros-args -p alarm_threshold:=100.0` | 输出 `[报警] 气体浓度超标: 312.45 ppm >= 100.0 ppm` |
| 调快周期：`gas_sensor_node --ros-args -p publish_period:=0.5` | `ros2 topic hz` 变为 average rate: 2.000 Hz |

---

### 六、实验步骤

#### 整体流程

```mermaid
graph LR
    A[步骤1：编译 ros_sensor 包] --> B[步骤2：阅读 common.py 的 MQ5 换算]
    B --> C[步骤3：分析 gas_sensor_node 发布节点]
    C --> D[步骤4：分析 gas_monitor 订阅节点]
    D --> E[步骤5：运行与 CLI 观察]
    E --> F[步骤6：动态调参与多订阅者验证]
```

---

#### 步骤 1：编译 `ros_sensor` 包（10 分钟）

**知识点讲解**：

**功能包与工作空间（知识点 1.3.3、1.4.2）**
- **是什么**：`ros_sensor` 是一个 ament_python 功能包，把所有传感器驱动节点（MQ5/指纹/RFID/DHT11/MAX30102/继电器/光电）打包在一起，通过 `setup.py` 的 `entry_points` 注册为 `ros2 run` 可执行程序。它依赖自定义接口包 `ros_sensor_interfaces`。
- **为什么**：把节点统一放入一个包，可以一次性 `colcon build` 编译、`ros2 launch` 批量启动，避免每个传感器一个独立包导致的编译与依赖管理碎片化。
- **怎么用**：先在工作空间根目录编译，再 source 环境。

**操作步骤**：

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash

# 首次或改代码后构建（--symlink-install 使 Python 源码修改无需重新编译）
colcon build --symlink-install --packages-select ros_sensor ros_sensor_interfaces

# 构建后必须重新 source
source install/setup.bash
```

**易错点**：
- ⚠️ 编译后忘记 `source install/setup.bash`，导致 `ros2 run ros_sensor ...` 报 `package not found` → **解决**：每次新开终端都要重新 source。

---

#### 步骤 2：阅读 MQ5 浓度换算逻辑（20 分钟）

**知识点讲解**：

**MQ5 电阻-浓度对数曲线换算（知识点 2.2.4）**
- **是什么**：MQ5 是半导体气敏元件，其内阻随可燃气体浓度升高而下降。本实验通过分压电路把「电阻变化」转为「ADC 电压」，再通过 MQ5 的灵敏特性曲线（对数坐标下近似直线）反推 ppm 浓度。
- **为什么**：气敏元件的 `Rs/R0`（当前电阻/标定电阻）与浓度之间呈幂律关系，直接线性读取电压无法得到正确浓度，必须在对数域做线性插值。
- **怎么用**：`common.py` 中 `voltage_to_ppm()` 完成换算，公式如下（源码对应 `common.py` L25-33）：

```text
rs    = RL * (V_REF - v) / v         # 分压电阻反推 Rs
ratio = rs / R0                       # 与标定电阻的比值
ppm   = 10 ** ((log10(ratio) - CURVE_B) / CURVE_M)
```

其中常量（源码 `common.py` L13-17）：`V_REF = 5.0`、`RL = 1.0`（负载电阻 kΩ）、`R0 = 10.0`（标定电阻 kΩ）、`CURVE_B = 0.186`、`CURVE_M = -0.362`（特性曲线截距与斜率）。

**操作步骤**：

打开 `common.py`，重点阅读 `read_mq5_once()` 与 `voltage_to_ppm()` 两个函数（`common.py` L25-47），理解「ADC 原始值 → 电压 → 电阻比值 → ppm」的四步链路。

```python
# 来源：ros_sensor/common.py L36-47（read_mq5_once）
def read_mq5_once():
    try:
        scale = float(read_adc_attr("in_voltage_scale"))
        raw   = int(read_adc_attr(f"in_voltage{MQ5_CH}_raw"))
        v = raw * scale / 1000.0          # 原始值 × 量程 → 电压(V)
        return raw, v, voltage_to_ppm(v), ""
    except Exception as e:
        return None, None, None, f"{type(e).__name__}: {e}"
```

**易错点**：
- ⚠️ 误以为 ADC 原始值就是电压 → **解决**：必须先乘 `in_voltage_scale` 再除以 1000 才是伏特。
- ⚠️ 电压接近 0 或满量程时 `voltage_to_ppm` 返回 0.0（除零保护）→ **解决**：检查 `v <= 0 or v >= V_REF` 分支。

---

#### 步骤 3：分析 `gas_sensor_node` 发布节点（30 分钟）

**知识点讲解**：

**Publisher 节点编程模型（知识点 2.2.1、2.2.3）**
- **是什么**：`gas_sensor_node` 是数据的「生产者」，继承 `rclpy.node.Node`，通过 `create_publisher` 声明「在 `/gas_sensor` 话题上发布 `Float32` 类型消息」，再用 `create_timer` 周期触发回调完成采样与发布。
- **为什么异步**：`publish()` 只把消息放入 DDS 内部队列即返回，不等待订阅者处理——因此即使没有订阅者在线也能正常运行，订阅者处理慢也不会阻塞发布者，实现生产/消费速率解耦。
- **怎么用**：`create_publisher(msg_type, topic, qos)` → 构造消息并赋值 → `publish(msg)`。QoS 使用 `Reliable + KeepLast(10)`，保证可靠传输并缓存最近 10 条历史消息（源码 `gas_sensor_node.py` L21-26）。

**操作步骤**：

打开 `gas_sensor_node.py`，完整阅读 `GasSensorNode` 类（L16-44），重点理解参数声明、QoS 配置与定时器回调三个环节。

```python
# 来源：ros_sensor/gas_sensor_node.py L16-44（节选）
class GasSensorNode(Node):
    def __init__(self):
        super().__init__('gas_sensor_node')
        self.declare_parameter('publish_period', 1.0)          # L19 声明发布周期

        qos = QoSProfile(                                      # L21-25 QoS 配置
            history=HistoryPolicy.KEEP_LAST, depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self.pub = self.create_publisher(Float32, '/gas_sensor', qos)  # L26

        period = float(self.get_parameter('publish_period').value)
        self.timer = self.create_timer(period, self.timer_cb)  # L29

    def timer_cb(self):                                        # L34-44 定时回调
        raw, v, ppm, err = read_mq5_once()
        if err:
            self.get_logger().error(f'读取 ADC 失败: {err}')
            return
        msg = Float32()
        msg.data = float(ppm)
        self.pub.publish(msg)
        self.get_logger().info(f'raw={raw} voltage={v:.3f}V ppm={ppm:.2f}')
```

**易错点**：
- ⚠️ 忘记 `declare_parameter` 就 `get_parameter`，运行时报参数未声明错误 → **解决**：声明在前、读取在后。
- ⚠️ `Float32` 消息只有 `data` 一个字段，误用 `msg.value` → **解决**：确认 `std_msgs/msg/Float32` 的字段名是 `data`。

---

#### 步骤 4：分析 `gas_monitor` 订阅节点（30 分钟）

**知识点讲解**：

**Subscriber 节点编程模型（知识点 2.2.3）**
- **是什么**：`gas_monitor` 是数据的「消费者」，通过 `create_subscription` 注册「监听 `/gas_sensor` 话题的 `Float32` 消息」，当有新消息到达时由 DDS 回调 `callback()`。
- **为什么用回调**：订阅者不主动轮询，而是被动等待——消息到达后由 ROS2 的 Executor 调度回调函数执行，这是事件驱动模型的体现，避免空转浪费 CPU。
- **怎么用**：`create_subscription(msg_type, topic, callback, qos)`，在回调内完成业务逻辑。本节点在回调中把 `msg.data` 与 `alarm_threshold` 比较，超阈值时用 `log_warn` 报警（源码 `gas_monitor.py` L29-36）。

**操作步骤**：

打开 `gas_monitor.py`，完整阅读 `GasMonitor` 类（L13-36）。

```python
# 来源：ros_sensor/gas_monitor.py L13-36（节选）
class GasMonitor(Node):
    def __init__(self):
        super().__init__('gas_monitor')
        self.declare_parameter('alarm_threshold', 500.0)       # L16 声明报警阈值
        self.threshold = float(self.get_parameter('alarm_threshold').value)

        qos = QoSProfile(                                      # L19-23 QoS 须与发布端一致
            history=HistoryPolicy.KEEP_LAST, depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self.sub = self.create_subscription(                   # L24-26
            Float32, '/gas_sensor', self.callback, qos)

    def callback(self, msg):                                   # L29-36
        ppm = msg.data
        if ppm >= self.threshold:
            self.get_logger().warn(f'[报警] 气体浓度超标: {ppm:.2f} ppm >= {self.threshold} ppm')
        else:
            self.get_logger().info(f'浓度正常: {ppm:.2f} ppm')
```

**易错点**：
- ⚠️ 订阅端 QoS 与发布端不兼容（如一端 RELIABLE、一端 BEST_EFFORT）导致收不到消息 → **解决**：两端 QoS 保持 `Reliable + KeepLast(10)` 一致。

---

#### 步骤 5：运行节点与 CLI 观察（40 分钟）

**知识点讲解**：

**话题运行态自省（知识点 1.2.2）**
- **是什么**：ROS2 提供 `ros2 topic` 命令族对运行中的话题做「自省」——`list` 列出话题、`info` 查看类型与收发端数量、`echo` 打印消息内容、`hz` 统计发布频率。
- **为什么重要**：这些命令不需要改动代码即可验证「谁在发、谁在收、发的什么、多快」，是排查话题通信问题的第一工具。
- **怎么用**：先在两个终端分别启动发布与订阅节点，再用第三个终端执行 `ros2 topic` 命令观察。

**操作步骤**：

```bash
# 终端 A：启动发布节点（不需要 sudo）
ros2 run ros_sensor gas_sensor_node
# 终端 B：启动订阅节点（不需要 sudo）
ros2 run ros_sensor gas_monitor

# 终端 C：观察
ros2 node list                       # 应显示 /gas_sensor_node 和 /gas_monitor
ros2 topic list                      # 应包含 /gas_sensor
ros2 topic info /gas_sensor          # Type: std_msgs/msg/Float32
ros2 topic echo /gas_sensor          # 实时打印 data: 312.45
ros2 topic hz /gas_sensor            # average rate: 1.000 Hz
```

**易错点**：
- ⚠️ `ros2 topic hz` 打印 `no messages received` → **解决**：确认发布节点已启动且无报错，检查 `ROS_DOMAIN_ID` 是否一致。

---

#### 步骤 6：动态调参与多订阅者验证（30 分钟）

**知识点讲解**：

**参数化设计与一对多特性（知识点 2.2.1、2.5.3）**
- **是什么**：把发布周期、报警阈值等做成 `declare_parameter` 参数，运行时用 `--ros-args -p 参数名:=值` 覆盖默认值，无需改代码。
- **为什么**：话题通信天然支持一对多——一个 Publisher 可同时服务多个 Subscriber，这是它与服务（一对一）的本质区别，也是选择话题承载持续数据流的根本原因。
- **怎么用**：`ros2 run ros_sensor gas_sensor_node --ros-args -p publish_period:=0.5` 调整发布频率；`ros2 run ros_sensor gas_monitor --ros-args -p alarm_threshold:=100.0` 降低报警阈值；同时打开 `ros2 topic echo` 观察多订阅者同时接收。

**操作步骤**：

```bash
# 调整发布周期为 0.5s，观察频率翻倍
ros2 run ros_sensor gas_sensor_node --ros-args -p publish_period:=0.5

# 降低报警阈值到 100ppm，观察 log_warn 报警
ros2 run ros_sensor gas_monitor --ros-args -p alarm_threshold:=100.0
```

预期现象：`ros2 topic hz /gas_sensor` 变为约 2Hz；`gas_monitor` 终端由「浓度正常」切换为「[报警] 气体浓度超标」。

**易错点**：
- ⚠️ 参数写错（如 `publish_period=0.5` 用等号）导致参数未被识别 → **解决**：ROS2 覆盖参数必须用 `:=`，即 `-p publish_period:=0.5`。

---

### 七、注意事项

| ⚠️ 注意项 | 说明 |
|-----------|------|
| QoS 一致性 | 发布端与订阅端须同为 `Reliable + KeepLast(10)`，否则可能收不到消息 |
| 环境加载 | 每次新开终端都要 `source install/setup.bash`，否则 `ros2 run` 找不到 `ros_sensor` 包 |
| 话题命名 | 话题名以 `/` 开头表示全局命名空间，本实验统一使用 `/gas_sensor` |
| 安全提示 | MQ5 传感器通电后会产生一定热量，避免用手直接接触传感器表面；本实验对象为低浓度演示环境，无爆炸风险 |

### 八、实验总结

#### 8.1 完成成果

完成本实验后，你应当能够：
- ✅ 编译并运行 `ros_sensor` 包中的 `gas_sensor_node` / `gas_monitor` 两个节点
- ✅ 理解 MQ5 传感器「ADC 原始值 → 电压 → 电阻比值 → ppm」的对数换算全链路
- ✅ 使用 `ros2 topic echo/hz/info` 观察话题的类型、频率与多订阅者收发
- ✅ 通过 `--ros-args -p` 动态调整 `publish_period` 与 `alarm_threshold` 参数
- ✅ 理解话题通信的一对多异步特性及其与服务/动作的适用场景边界

#### 8.2 技能收获

| 技能 | 说明 |
|------|------|
| 话题编程 | 掌握 Publisher/Subscriber 的标准代码模式（声明参数、QoS 配置、消息收发回调） |
| 传感器数据处理 | 理解 ADC 采集 → 物理量换算的完整信号处理链路 |
| QoS 配置 | 能根据场景选择可靠性/持久性/历史策略 |
| 系统调试 | 能用 `ros2 topic` 命令族和 `--ros-args -p` 动态调试通信系统 |
| 参数化设计 | 使用 `declare_parameter` 将关键参数暴露为运行时可配置项 |

#### 8.3 常见问题与解答

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 订阅节点无输出 | ① 话题名不匹配 ② QoS 不兼容 ③ ROS_DOMAIN_ID 不一致 | 用 `ros2 topic info` 确认话题信息，检查 `echo $ROS_DOMAIN_ID` |
| 浓度值始终为 0 | 电压接近 0 或满量程触发除零保护 | 检查 ADC 硬件连接与 `in_voltage_scale` 读数 |
| 浓度值跳跃很大 | 真实传感器的噪声 | 在回调中添加滑动平均滤波（移动窗口均值） |
| `ros2 run` 报 package not found | 未 source install/setup.bash | 重新 `source install/setup.bash` |
| 调整参数不生效 | 参数覆盖语法错误 | 使用 `:=` 而非 `=`，即 `-p publish_period:=0.5` |

### 九、实验报告要求

#### 9.1 报告内容

完成实验后，提交一份实验报告，包含以下内容：

1. **实验基本信息**：实验名称、实验日期、实验者姓名、实验平台信息
2. **实验过程记录**：截取发布节点终端输出、订阅节点终端输出、`ros2 topic info` 和 `ros2 topic hz` 的终端截图
3. **原理分析**（不少于 400 字）：用自己的语言解释以下三个问题：
   - ① 为什么 Publisher 和 Subscriber 通过话题名称和消息类型即可通信，而无需知道对方 IP 或进程 ID？DDS 在其中做了什么？
   - ② MQ5 从 ADC 原始值到 ppm 浓度经历了哪些换算步骤？每一步的物理意义是什么？
   - ③ 若收到的浓度数据存在大量噪声毛刺，你会如何处理？
4. **思考题**（见下方）

#### 9.2 思考题

**思考题 1**：
`voltage_to_ppm()` 中 `CURVE_M = -0.362` 为负值，说明 ppm 与 `Rs/R0` 的比值是什么单调关系？请结合 MQ5 气敏元件的物理特性解释「为什么可燃气体浓度越高、传感器内阻越低」。

**思考题 2**：
MQ5 对甲烷、液化气、酒精蒸气等多种可燃气体都敏感但无法区分种类。假设你在设计智能厨房安全监控系统，需要区分「炒菜的酒精蒸气」与「燃气泄漏的天然气」，请设计一种多传感器 + ROS2 话题通信的方案，简述架构。

#### 9.3 评分标准

| 评分项 | 权重 | 评分标准 |
|-------|------|---------|
| 实验操作完整性 | 25% | 是否成功运行 gas_sensor_node + gas_monitor + CLI 验证 |
| 代码理解 | 20% | 能否准确指出 common.py/gas_sensor_node.py/gas_monitor.py 关键代码位置 |
| 原理分析 | 25% | 对话题通信机制、浓度换算原理、QoS 的理解深度 |
| 思考题 1 | 15% | 对 MQ5 对数特性曲线与物理机制的阐释 |
| 思考题 2 | 15% | 多传感器融合方案的创新性与可行性 |

---
