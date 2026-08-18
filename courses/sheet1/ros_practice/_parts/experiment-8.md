## 实验8：ROS2动作通讯（MFRC522读卡器）（4h）

### 一、关联知识点

本实验关联以下知识图谱节点：

| 编号 | 知识点名称 | 类型 | 层级路径 |
|------|-----------|------|---------|
| 2.4.1 | 动作是异步长耗时任务的 Goal→Feedback→Result 三通道机制 | 概念 | 第2章 ROS2核心通信机制 → 2.4 动作通信 |
| 2.4.2 | 客户端发 Goal、服务端异步执行并通过 Feedback 周期反馈的交互原理 | 原理 | 第2章 ROS2核心通信机制 → 2.4 动作通信 |
| 2.4.3 | ActionServer 实现 goal/feedback/result 回调 → SPI 读取 MFRC522 → 返回 card_uid | 流程 | 第2章 ROS2核心通信机制 → 2.4 动作通信 |

### 二、实验目标

通过本实验的学习，学生能够：

1. **原理理解**：阐述 ROS2 动作通信的三通道（Goal/Feedback/Result）异步模型——客户端发送目标后立即返回，服务端在执行期间周期发送反馈，任务完成后返回结果并可被随时取消，说明它与服务（同步短耗时单次调用）的本质区别
2. **流程掌握**：掌握 `ros_sensor` 包中 `rfid_action_server`（动作服务端）与 `rfid_action_client`（动作客户端）从 `ActionServer`/`ActionClient`、`send_goal_async`、`publish_feedback` 到 `goal_handle.succeed()/abort()/canceled()` 的完整异步链路
3. **独立完成**：独立运行 RFID 动作服务端/客户端，观察「SCANNING → CARD_FOUND → READING_UID → VERIFYING」的状态反馈流转，使用 `ros2 action send_goal --feedback` 命令行调试并实现超时/取消
4. **迁移应用**：能够将「长耗时传感器等待 → 动作封装 → 异步反馈」的模式迁移到其它耗时任务（如导航、机械臂运动、长时间数据采集），并理解 SPI 外设的驱动封装方法

### 三、实验环境

| 类别 | 配置 |
|------|------|
| 硬件平台 | 具身智能实验箱B2 或 具身智能机器人小车C1（集成 MFRC522 射频读卡模组） |
| 操作系统 | Ubuntu 22.04 + ROS2 Humble |
| 核心依赖 | `rclpy`、`ros_sensor_interfaces`（自定义 action）、`python-periphery` |
| 开发语言 | Python 3.10 |
| 源码位置 | `~/ros2_ws/src/xflz_eai_car1/driver/ros_sensor`（节点包 `ros_sensor`） |
| 传感器接口 | MFRC522 射频读卡器，SPI1-m0 + GPIO（CS=114、RST=116，SCK/MOSI/MISO 见下） |

> 说明：MFRC522 通过 SPI 与主控通信，引脚映射见 `rc522_reader.py` L7-15：SDA/CS→GPIO3_C2(114)、SCK→GPIO3_C0(112)、MOSI→GPIO3_C1(113)、MISO→GPIO3_C3(115)、RST→GPIO3_C4(116)。驱动依赖 `python-periphery` 库控制 SPI 与 GPIO。

### 四、实验难度

| 维度 | 说明 |
|------|------|
| 难度等级 | ⭐⭐⭐（较高） |
| 实验类型 | 设计性 |
| 建议时长 | 4 学时（180 分钟） |

**重点**：
- 掌握 Action 动作服务端/客户端的标准编程流程：`ActionServer`（execute/goal/cancel 三个回调）、`ActionClient` + `send_goal_async`、`publish_feedback` 周期反馈、`goal_handle.succeed()/abort()/canceled()` 三种结局
- 理解 MFRC522 的寻卡（REQA）→ 防冲突（AntiCollision）→ 读取 UID 三步流程
- 掌握 `.action` 自定义动作接口（Goal/Result/Feedback 三段）的定义与使用

**难点**：
- 动作「异步执行 + 中间反馈 + 可取消」与服务「同步单次调用」的语义差异
- 服务端 `execute_cb` 异步回调中检查 `is_cancel_requested` 与状态机流转的实现

### 五、实验现象

#### 5.1 快速验证流程

完成本实验后，你应能观察到以下现象：

1. 终端 A 启动 `rfid_action_server` 后，打印 `RFID Action 服务端已启动 (action: /rfid_scan)`
2. 终端 B 运行 `rfid_action_client 30` 后，打印 `Goal 已接受`，随后按频率打印反馈状态
3. 未放卡时，反馈持续显示 `SCANNING`（寻卡中）
4. 将 MIFARE 卡靠近天线，反馈依次变化 `SCANNING → CARD_FOUND → READING_UID → VERIFYING`
5. 读卡成功后打印 `结果: success=True uid=XXXXXXXX type=MIFARE Classic msg=读卡成功`
6. 超过超时时间未放卡，客户端打印 `读卡未成功`，服务端打印 `读卡超时`
7. 用 `ros2 action send_goal ... --feedback` 命令行可独立观察反馈与结果

#### 5.2 预期效果描述

| 操作 | 预期输出 |
|------|---------|
| `ros2 run ros_sensor rfid_action_server` | `RFID Action 服务端已启动 (action: /rfid_scan)` |
| `ros2 run ros_sensor rfid_action_client 30`（另一终端） | `结果: success=True uid=7E1A3B02 type=MIFARE Classic msg=读卡成功` |
| `ros2 action list` | 列表包含 `/rfid_scan` |
| `ros2 action info /rfid_scan` | Action: `ros_sensor_interfaces/action/RfidScan` |
| `ros2 action send_goal /rfid_scan ros_sensor_interfaces/action/RfidScan "{timeout_sec: 30}" --feedback` | 逐条打印 `Feedback: SCANNING` 等状态 |

---

### 六、实验步骤

#### 整体流程

```mermaid
graph LR
    A[步骤1：编译与独立驱动测试] --> B[步骤2：阅读 rc522_reader SPI 驱动]
    B --> C[步骤3：分析 rfid_action_server 服务端]
    C --> D[步骤4：分析 rfid_action_client 客户端]
    D --> E[步骤5：运行与 ros2 action 调试]
    E --> F[步骤6：超时/取消与三机制选型对比]
```

---

#### 步骤 1：编译与独立驱动测试（15 分钟）

**知识点讲解**：

**驱动独立测试（知识点 2.4.3）**
- **是什么**：`rc522_reader.py` 既是一个可导入的驱动类 `MFRC522`，也是一个带 `--test`/`--dump` 选项的命令行工具，可脱离 ROS 单独验证硬件与接线是否正确。
- **为什么先独立测**：SPI 接线、GPIO 引脚、供电问题都会在硬件层暴露，先用驱动自测可把「硬件故障」与「ROS 逻辑故障」分开，避免在 ROS 层盲目排查。
- **怎么用**：先 `colcon build` 编译接口包与节点包，再运行 `python3 rc522_reader.py --test` 做自检（验证版本寄存器与读写回）。

**操作步骤**：

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select ros_sensor ros_sensor_interfaces
source install/setup.bash

# 脱离 ROS 先自检驱动（验证接线与供电）
cd src/xflz_eai_car1/driver/ros_sensor/ros_sensor
python3 rc522_reader.py --test
```

**易错点**：
- ⚠️ 自检 `VersionReg=0x00/0xFF` 表示无响应 → **解决**：检查 SPI 接线（CS=114、RST=116）、3.3V 供电与 `python-periphery` 是否安装。
- ⚠️ 编译后未 source 导致 `ros2 run` 找不到包 → **解决**：`source install/setup.bash`。

---

#### 步骤 2：阅读 `rc522_reader.py` SPI 驱动（25 分钟）

**知识点讲解**：

**MFRC522 寄存器寻卡流程（知识点 2.4.3）**
- **是什么**：MFRC522 是寄存器驱动的 13.56MHz 读卡芯片，主控通过 SPI 读写其寄存器（`REG_COMMAND=0x01`、`REG_FIFO_DATA=0x09`、`REG_VERSION=0x37` 等，见 `rc522_reader.py` L26-49）。寻卡流程封装为：`open()` 打开 SPI/GPIO → `hw_reset()` 硬件复位 → `self_test()` 自检 → `init()` 初始化 → `request_a()` 寻卡（REQA）→ `anticoll()` 防冲突读 UID。
- **为什么防冲突**：ISO14443A 协议下多张卡同时在场会冲突，`anticoll()` 用 `0x93 0x20` 命令帧读取 4 字节 UID 并做异或校验（`rc522_reader.py` L283-294），保证读到唯一卡号。
- **怎么用**：`read_uid()`（L296-305）把「寻卡 + 防冲突」串成一步，返回 `(success, uid_hex_str, uid_bytes)`，动作服务端直接复用。

**操作步骤**：

打开 `rc522_reader.py`，阅读 `MFRC522` 类的 `request_a()`（L270-281）、`anticoll()`（L283-294）、`read_uid()`（L296-305）三个方法。

```python
# 来源：rc522_reader.py L296-305（完整读卡流程）
def read_uid(self) -> tuple:
    ok, atqa = self.request_a()          # REQA 寻卡，返回 ATQA
    if not ok:
        return False, "", b''
    ok, uid = self.anticoll()            # AntiCollision 防冲突读 UID
    if not ok:
        return False, f"ATQA=0x{atqa:04X}", b''
    uid_str = "%02X%02X%02X%02X" % (uid[0], uid[1], uid[2], uid[3])
    return True, uid_str, uid
```

**易错点**：
- ⚠️ 混淆 `request_a()`（返回 ATQA）与 `anticoll()`（返回 UID）→ **解决**：寻卡先拿 ATQA 判断卡是否在场，防冲突再拿 UID，二者顺序不可颠倒。

---

#### 步骤 3：分析 `rfid_action_server` 服务端（40 分钟）

**知识点讲解**：

**ActionServer 三回调模型（知识点 2.4.1、2.4.2）**
- **是什么**：`ActionServer` 需要三个回调（源码 `rfid_action_server.py` L41-48）：`execute_callback`（执行任务主体，异步）、`goal_callback`（收到新 Goal 时决定是否接受）、`cancel_callback`（收到取消请求时决定是否同意）。`execute_cb` 是 `async` 协程，执行期间可多次 `publish_feedback`。
- **为什么三回调**：动作要处理「接受目标 → 执行 + 反馈 → 完成/中止/取消」三种生命周期，比服务的单回调复杂，因此拆分为三个入口。
- **怎么用**：`execute_cb`（L61-149）先读 Goal 的 `timeout_sec`（≤0 则默认 30），初始化 MFRC522（open→hw_reset→self_test→init），然后在 `deadline` 前循环：检查 `is_cancel_requested`、发布 `SCANNING` 反馈、`request_a()` 寻卡、发布 `CARD_FOUND`、`anticoll()` 读 UID、发布 `READING_UID`、`classify_card` 判型、发布 `VERIFYING`，最后 `goal_handle.succeed()` 返回结果。

**操作步骤**：

打开 `rfid_action_server.py`，阅读 `RfidActionServer` 类的 `execute_cb`（L61-149），重点理解反馈状态流转与三种结局。

```python
# 来源：rfid_action_server.py L19-29（卡类型判定，节选）
def classify_card(atqa, uid):
    if atqa == 0x0044 and len(uid) == 7:
        return 'MIFARE Ultralight'
    if atqa == 0x4400:
        return 'MIFARE Ultralight C'
    if atqa == 0x0344:
        return 'MIFARE DESFire'
    if atqa in (0x0002, 0x0003, 0x0004):
        return 'MIFARE Classic'
    return 'Unknown'
```

```python
# 来源：rfid_action_server.py L100-141（读卡循环，节选）
while time.time() < deadline:
    if goal_handle.is_cancel_requested:      # 检查取消
        goal_handle.canceled()
        result.success = False
        result.message = '已取消'
        return result

    feedback.status = 'SCANNING'
    goal_handle.publish_feedback(feedback)

    ok, atqa = rc.request_a()                # 寻卡
    if not ok:
        time.sleep(0.1)
        continue
    feedback.status = 'CARD_FOUND'
    goal_handle.publish_feedback(feedback)
    ok, uid = rc.anticoll()                  # 读 UID
    # ... READING_UID / VERIFYING 反馈后 succeed
```

**易错点**：
- ⚠️ 忘记检查 `is_cancel_requested` 导致无法取消 → **解决**：循环体内必须周期检查，否则取消请求无法生效。
- ⚠️ `execute_cb` 未声明 `async` 却调用异步语义 → **解决**：动作执行回调必须是 `async def`（源码 L61）。

---

#### 步骤 4：分析 `rfid_action_client` 客户端（35 分钟）

**知识点讲解**：

**ActionClient 异步发送模型（知识点 2.4.2）**
- **是什么**：`rfid_action_client` 用 `ActionClient` 发 Goal，通过回调链 `goal_response_cb`（处理接受/拒绝）→ `result_cb`（处理最终结果）与 `feedback_cb`（处理中间反馈）异步处理各阶段，而非阻塞等待。
- **为什么异步回调**：动作耗时未知（等刷卡可能几十秒），客户端不能阻塞主线程，故用 `send_goal_async` + 回调，再用 `spin_once` 让 Executor 处理回调（源码 `rfid_action_client.py` L64-65）。
- **怎么用**：`send(timeout)`（L51-66）先 `wait_for_server`，构造 `RfidScan.Goal()` 并赋值 `timeout_sec`，`send_goal_async(goal, feedback_callback=...)` 发送，随后 `spin_once` 轮转直到完成标志 `_done` 置位。

**操作步骤**：

打开 `rfid_action_client.py`，阅读 `RfidActionClient` 类（L17-66），重点理解三个回调的职责。

```python
# 来源：rfid_action_client.py L51-66（发送 Goal，节选）
def send(self, timeout=30):
    if not self._client.wait_for_server(timeout_sec=3.0):
        self.get_logger().error('RFID Action 服务不可用')
        return False
    goal = RfidScan.Goal()
    goal.timeout_sec = timeout
    future = self._client.send_goal_async(
        goal, feedback_callback=self.feedback_cb
    )
    future.add_done_callback(self.goal_response_cb)
    while rclpy.ok() and not self._done:
        rclpy.spin_once(self, timeout_sec=0.1)
    return self._ok
```

**易错点**：
- ⚠️ 忘记 `spin_once` 导致回调永不执行、程序卡住 → **解决**：发送 Goal 后必须驱动 Executor（`spin_once` 或 `spin_until_future_complete`）。
- ⚠️ 结果状态不是 `STATUS_SUCCEEDED` 时误报成功 → **解决**：源码 L39-49 通过 `GoalStatus.STATUS_SUCCEEDED` 判断，超时/取消对应其它状态码。

---

#### 步骤 5：运行与 `ros2 action` 调试（40 分钟）

**知识点讲解**：

**动作运行态自省（知识点 2.1.2）**
- **是什么**：`ros2 action` 命令族用于自省动作——`list` 列出动作、`info` 查看类型与客户端数、`send_goal` 发送一个目标（可加 `--feedback` 实时打印反馈）。
- **为什么重要**：`--feedback` 能直观展示动作的中间反馈流，是理解「动作 vs 服务」区别最直观的入口——服务没有中间反馈，动作有。
- **怎么用**：`ros2 action send_goal /rfid_scan ros_sensor_interfaces/action/RfidScan "{timeout_sec: 30}" --feedback`，其中 Goal 的 YAML 用 `{timeout_sec: 30}` 表示。

**操作步骤**：

```bash
# 终端 A：启动动作服务端
ros2 run ros_sensor rfid_action_server

# 终端 B：启动动作客户端（30s 超时）
ros2 run ros_sensor rfid_action_client 30

# 终端 C：自省与命令行发 Goal（带 --feedback 实时反馈）
ros2 action list
ros2 action info /rfid_scan
ros2 action send_goal /rfid_scan ros_sensor_interfaces/action/RfidScan "{timeout_sec: 30}" --feedback
```

**易错点**：
- ⚠️ Goal YAML 字段名写错（如 `timeout` 而非 `timeout_sec`）→ **解决**：字段名必须与 `.action` 定义一致，即 `timeout_sec`。
- ⚠️ 终端 C 与 B 同时发 Goal 可能抢卡 → **解决**：一次只让一个客户端发 Goal，避免多个 Goal 同时执行。

---

#### 步骤 6：超时/取消与三机制选型对比（25 分钟）

**知识点讲解**：

**动作三种结局与选型（知识点 2.4.1、2.3.1、2.2.1）**
- **是什么**：一个 Goal 有四种终态：`succeed()`（成功）、`abort()`（执行失败）、`canceled()`（被取消）、超时后 `abort()`。服务端用 `is_cancel_requested` 响应取消，用 `deadline` 响应超时。
- **为什么动作可取消**：读卡是「等待外部事件（刷卡）」的长耗时任务，用户可能在等待期间取消；这是服务（一次性、不可取消）无法胜任的，也是动作存在的意义。
- **怎么用**：下表综合本章三个实验的选型结论。

**操作步骤**：

| 维度 | 话题（实验6） | 服务（实验7） | 动作（实验8） |
|------|-------------|-------------|-------------|
| 调用语义 | 持续数据流，一对多 | 单次请求/响应，一对一 | 长耗时目标+反馈+结果 |
| 异步/同步 | 异步 | 同步 | 异步 |
| 中间反馈 | 无（有值即发） | 无 | 有（Feedback 状态机） |
| 是否可取消 | 否 | 否 | 是 |
| 典型场景 | MQ5 浓度发布 | 指纹验证 | 刷卡检测（等卡） |

**易错点**：
- ⚠️ 用服务实现「等刷卡」导致请求长时间阻塞且无法取消 → **解决**：长耗时、可取消、需反馈的任务用动作。

---

### 七、注意事项

| ⚠️ 注意项 | 说明 |
|-----------|------|
| SPI 接线 | CS=114、SCK=112、MOSI=113、MISO=115、RST=116，接错会导致自检失败 |
| 驱动依赖 | MFRC522 依赖 `python-periphery`，先 `pip install python-periphery` |
| 取消检查 | `execute_cb` 循环内必须周期检查 `is_cancel_requested`，否则无法取消 |
| 单 Goal 执行 | 一次只发一个 Goal，多 Goal 并发会抢卡产生竞争 |
| 安全提示 | MFRC522 工作于 13.56MHz，靠近天线时避免放置金属物；刷卡时轻贴即可，无需用力 |

### 八、实验总结

#### 8.1 完成成果

完成本实验后，你应当能够：
- ✅ 使用 `rc522_reader.py --test` 独立自检 MFRC522 硬件与接线
- ✅ 编译并运行 `rfid_action_server` / `rfid_action_client` 完成刷卡检测
- ✅ 理解寻卡（REQA）→ 防冲突（AntiCollision）→ 读 UID 的三步流程
- ✅ 观察并解释「SCANNING → CARD_FOUND → READING_UID → VERIFYING」反馈状态流转
- ✅ 使用 `ros2 action send_goal --feedback` 调试，并理解动作的 succeed/abort/canceled 三种结局

#### 8.2 技能收获

| 技能 | 说明 |
|------|------|
| 动作编程 | 掌握 ActionServer/ActionClient 标准代码模式（三回调、send_goal_async、publish_feedback） |
| SPI 外设集成 | 理解寄存器驱动的 MFRC522 读卡芯片寻卡/防冲突协议 |
| 自定义 action | 使用 `ros_sensor_interfaces/action/RfidScan`（Goal/Result/Feedback 三段） |
| 异步编程 | 理解 async 执行回调、Future 回调链与 Executor 轮转 |
| 通信选型 | 掌握话题/服务/动作三类机制的全景选型 |

#### 8.3 常见问题与解答

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 自检 VersionReg=0x00/0xFF | SPI 接线错误或供电不足 | 检查 CS/RST/SCK/MOSI/MISO 接线与 3.3V 供电 |
| 客户端「RFID Action 服务不可用」 | 服务端未启动或动作名不一致 | 先启动服务端，`ros2 action list` 确认 `/rfid_scan` |
| 反馈一直 SCANNING | 卡未靠近天线或卡类型不匹配 | 把 MIFARE 卡贴近天线，检查是否 13.56MHz 卡 |
| 读卡超时 | 超时时间内未检测到卡 | 增大 `timeout_sec`，或确认卡已就位 |
| Goal 无法取消 | execute_cb 未检查 `is_cancel_requested` | 确认循环体内有取消检查 |

### 九、实验报告要求

#### 9.1 报告内容

完成实验后，提交一份实验报告，包含以下内容：

1. **实验基本信息**：实验名称、实验日期、实验者姓名、实验平台信息
2. **实验过程记录**：截取服务端启动、客户端读卡成功、`ros2 action send_goal --feedback` 的反馈流终端截图
3. **原理分析**（不少于 400 字）：用自己的语言解释以下三个问题：
   - ① 动作与服务都是「客户端发起、服务端响应」，为什么动作需要 Goal/Feedback/Result 三个独立通道？三通道分别由谁发起、流向如何？
   - ② `execute_cb` 是 `async` 协程，但读卡循环里用 `time.sleep(0.1)` 做轮询等待。请说明 `is_cancel_requested` 检查为什么必须放在循环内，如果放在循环外会怎样？
   - ③ MFRC522 的 `anticoll()` 如何保证多卡场景下读到唯一 UID？防冲突失败的典型表现是什么？
4. **思考题**（见下方）

#### 9.2 思考题

**思考题 1**：
`classify_card()` 通过 ATQA 与 UID 长度判断卡类型。若读到的 ATQA 为 `0x0004` 且 UID 为 4 字节，应判为哪种卡？如果出现 `Unknown`，可能是什么原因？结合 `rfid_action_server.py` L19-29 说明。

**思考题 2**：
当前的读卡 Action 在「读卡成功」后立即 `succeed()` 结束，无法持续检测「卡是否被移走」。假设你要设计一个「门禁持续监控」系统，需要不断检测卡在/离场并实时上报，你会如何设计？请对比「动作 + 长循环反馈」与「话题持续发布」两种方案的优劣，给出你的选择与理由。

#### 9.3 评分标准

| 评分项 | 权重 | 评分标准 |
|-------|------|---------|
| 实验操作完整性 | 25% | 是否成功完成驱动自检 + 服务端/客户端读卡 + `ros2 action` 调试 |
| 代码理解 | 20% | 能否准确指出 rc522_reader.py / rfid_action_server.py / rfid_action_client.py 关键代码位置 |
| 原理分析 | 25% | 对三通道模型、异步执行、防冲突的理解深度 |
| 思考题 1 | 15% | 对卡类型判定与 Unknown 成因的分析 |
| 思考题 2 | 15% | 对持续检测方案的选型分析与论证 |

---
