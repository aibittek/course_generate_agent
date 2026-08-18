## 实验9：ROS2自定义接口消息（传感器接口包）（2h）

### 一、关联知识点

本实验关联以下知识图谱节点：

| 编号 | 知识点名称 | 类型 | 层级路径 |
|------|-----------|------|---------|
| 2.5.1 | 自定义接口（.msg/.srv/.action）定义传感器专用数据结构 | 概念 | 第2章 ROS2核心通信机制 → 2.5 通信接口与参数系统 |
| 2.5.2 | 创建接口包 → 编写定义 → CMakeLists.txt 配置编译 → 使用自定义消息 | 流程 | 第2章 ROS2核心通信机制 → 2.5 通信接口与参数系统 |

### 二、实验目标

通过本实验的学习，学生能够：

1. **原理理解**：阐述 ROS2 三种自定义接口（`.msg` 消息、`.srv` 服务、`.action` 动作）的结构差异与适用场景——`.msg` 单段字段、`.srv` 用 `---` 分隔请求/响应、`.action` 用两个 `---` 分隔 Goal/Result/Feedback 三段
2. **流程掌握**：掌握 `ros_sensor_interfaces` 接口包（ament_cmake）从「编写接口定义 → `rosidl_generate_interfaces` 配置编译 → 生成 Python/C++ 消息类 → 节点 import 使用」的完整链路
3. **独立完成**：独立使用 `ros2 interface list/show` 查看接口定义，理解 `TemperatureHumidity`/`HeartRateSpO2`/`PhotoState` 消息、`VerifyFingerprint`/`TriggerRelay` 服务、`RfidScan` 动作与实验6-8 各传感器节点的对应关系
4. **迁移应用**：能够为一个新传感器自定义接口包（如光照度、加速度计），并正确配置 `CMakeLists.txt` 的 `rosidl_generate_interfaces` 与 `package.xml` 的 `<depend>` 依赖

### 三、实验环境

| 类别 | 配置 |
|------|------|
| 硬件平台 | 具身智能实验箱B2 或 具身智能机器人小车C1（无需额外硬件，编译期实验） |
| 操作系统 | Ubuntu 22.04 + ROS2 Humble |
| 核心依赖 | `rosidl_default_generators`、`std_msgs`、`action_msgs`、`builtin_interfaces` |
| 开发语言 | 接口定义（IDL 风格）+ CMake（编译） |
| 源码位置 | `~/ros2_ws/src/xflz_eai_car1/driver/ros_sensor/ros_sensor_interfaces`（接口包） |

> 说明：本实验不涉及新硬件，而是「回看」实验6-8 已使用过的接口——把分散在三个实验里的 `VerifyFingerprint.srv`、`RfidScan.action`、以及 DHT11/MAX30102/光电传感器对应的 `.msg` 集中起来，系统理解它们的定义与编译机制。

### 四、实验难度

| 维度 | 说明 |
|------|------|
| 难度等级 | ⭐⭐（中等） |
| 实验类型 | 设计性 |
| 建议时长 | 2 学时（90 分钟） |

**重点**：
- 掌握 `.msg`/`.srv`/`.action` 三种接口文件的字段定义语法（分隔符 `---` 的语义）
- 掌握 `rosidl_generate_interfaces` 的配置方法与 `DEPENDENCIES` 声明
- 理解 ament_cmake（接口包）与 ament_python（节点包）的职责分工

**难点**：
- `.action` 文件三段结构（Goal/Result/Feedback）与编译后生成的类（`RfidScan.Goal`/`RfidScan.Result`/`RfidScan.Feedback`）的映射关系
- 接口包与节点包的依赖声明（`package.xml` 的 `<depend>`）如何让节点能 `import` 到自定义消息

### 五、实验现象

#### 5.1 快速验证流程

完成本实验后，你应能观察到以下现象：

1. 编译 `ros_sensor_interfaces` 后，`ros2 interface list | grep ros_sensor_interfaces` 列出全部 6 个接口
2. `ros2 interface show` 能打印出各接口的字段定义，与 `.msg/.srv/.action` 源文件一致
3. 编译产物中生成 Python 消息类，节点包 `ros_sensor` 能 `from ros_sensor_interfaces.srv import VerifyFingerprint` 成功导入
4. 对照实验6-8，`gas_sensor_node` 用的是标准 `Float32`（无需自定义），而指纹/RFID/继电器等用了自定义接口
5. 修改 `.msg` 字段并重新编译后，依赖该消息的节点需重新编译才能生效

#### 5.2 预期效果描述

| 操作 | 预期输出 |
|------|---------|
| `ros2 interface list \| grep ros_sensor_interfaces` | 列出 `msg/HeartRateSpO2`、`msg/PhotoState`、`msg/TemperatureHumidity`、`srv/TriggerRelay`、`srv/VerifyFingerprint`、`action/RfidScan` |
| `ros2 interface show ros_sensor_interfaces/srv/VerifyFingerprint` | 请求空，响应 `bool success / int32 user_id / string message` |
| `ros2 interface show ros_sensor_interfaces/action/RfidScan` | 显示 Goal/Result/Feedback 三段定义 |
| `ros2 interface show ros_sensor_interfaces/msg/TemperatureHumidity` | `float32 temperature / float32 humidity` |

---

### 六、实验步骤

#### 整体流程

```mermaid
graph LR
    A[步骤1：通览接口包结构] --> B[步骤2：理解 .msg 消息定义]
    B --> C[步骤3：理解 .srv 服务定义]
    C --> D[步骤4：理解 .action 动作定义]
    D --> E[步骤5：CMakeLists 编译配置]
    E --> F[步骤6：接口与节点依赖关系]
```

---

#### 步骤 1：通览 `ros_sensor_interfaces` 接口包结构（10 分钟）

**知识点讲解**：

**接口包与节点包分离（知识点 2.5.1）**
- **是什么**：`ros_sensor_interfaces` 是一个**纯接口包**（`ament_cmake` 构建类型），只定义数据类型、不包含可执行节点；`ros_sensor` 是**节点包**（`ament_python`），通过 `<depend>` 依赖前者来使用自定义消息。
- **为什么分离**：把接口独立成包，可以让多个节点包、甚至 C++ 与 Python 混合的节点共享同一套数据类型，避免重复定义导致消息不兼容；接口是「契约」，节点是「实现」，分离后契约稳定、实现可独立演进。
- **怎么用**：接口包目录含 `msg/`、`srv/`、`action/` 三个子目录存放定义文件，`CMakeLists.txt` 负责把它们编译成消息类。

**操作步骤**：

```bash
cd ~/ros2_ws/src/xflz_eai_car1/driver/ros_sensor/ros_sensor_interfaces
ls -R msg srv action          # 查看三个目录下的接口定义文件
```

**易错点**：
- ⚠️ 把接口定义文件放进节点包而非独立接口包 → **解决**：接口必须独立成包（`ament_cmake`），节点包只做 `<depend>` 依赖。

---

#### 步骤 2：理解 `.msg` 消息定义（20 分钟）

**知识点讲解**：

**消息字段与传感器一一对应（知识点 2.5.1）**
- **是什么**：`.msg` 是最简单的接口，只含一段字段列表，每行 `类型 字段名`。`ros_sensor_interfaces` 定义了三个传感器专用消息：`TemperatureHumidity`（DHT11 温湿度）、`HeartRateSpO2`（MAX30102 心率血氧）、`PhotoState`（光电传感器）。
- **为什么自定义而非用标准消息**：标准 `Float32` 只有单值，无法同时表达「温度+湿度」或「心率+血氧+有效性」这类结构化数据；自定义 `.msg` 把多字段打包成一个语义完整的数据结构。
- **怎么用**：`msg/TemperatureHumidity.msg` 定义 `float32 temperature` 与 `float32 humidity`；`msg/HeartRateSpO2.msg` 定义 `float32 heart_rate`、`float32 spo2` 与 `bool valid`（读数是否有效，用于标记传感器未接触时的无效数据）。

**操作步骤**：

```bash
cat msg/TemperatureHumidity.msg
cat msg/HeartRateSpO2.msg
cat msg/PhotoState.msg
```

```text
# 来源：msg/TemperatureHumidity.msg（全文）
float32 temperature   # 温度(摄氏度)
float32 humidity      # 湿度(%)
```

**易错点**：
- ⚠️ 字段类型写成 `int`（C 风格）而非 `int32` → **解决**：ROS2 接口使用定长整型（`int32`/`uint8` 等），不能用 `int`。
- ⚠️ 忘记 `bool valid` 这类「有效性」字段，导致无效读数也被当作正常数据发布 → **解决**：传感器常有「未接触/超量程」状态，应加有效性标志位。

---

#### 步骤 3：理解 `.srv` 服务定义（20 分钟）

**知识点讲解**：

**服务请求/响应分隔符（知识点 2.5.1）**
- **是什么**：`.srv` 用一行 `---` 分隔「请求」与「响应」两段。`VerifyFingerprint.srv` 请求为空（只需触发验证）、响应为 `bool success / int32 user_id / string message`；`TriggerRelay.srv` 请求为 `int32 relay_id / float32 duration`（继电器编号与脉冲时长）、响应为 `bool success / string message`。
- **为什么请求可以为空**：有些服务不需要入参（如「帮我验证当前手指」），空请求用 `---` 直接分隔即可，客户端调用时传 `"{}"`。
- **怎么用**：编译后生成 `VerifyFingerprint.Request`（空）与 `VerifyFingerprint.Response`（三字段），实验7 的 `fingerprint_server`/`fingerprint_client` 正是 `from ros_sensor_interfaces.srv import VerifyFingerprint` 使用它。

**操作步骤**：

```bash
cat srv/VerifyFingerprint.srv
cat srv/TriggerRelay.srv
```

```text
# 来源：srv/VerifyFingerprint.srv（全文）
# 请求：触发一次指纹验证（无参数）
---
bool success
int32 user_id
string message
```

**易错点**：
- ⚠️ 请求与响应之间漏写 `---` 分隔符 → **解决**：`.srv` 必须用单独一行 `---` 分隔请求与响应，缺了会被当作单个消息解析失败。
- ⚠️ 客户端构造请求时写错类名（如 `VerifyFingerprint.Req`）→ **解决**：编译后固定为 `.Request` 与 `.Response` 两个子类。

---

#### 步骤 4：理解 `.action` 动作定义（20 分钟）

**知识点讲解**：

**动作三段结构（知识点 2.5.1、2.4.1）**
- **是什么**：`.action` 用两个 `---` 分隔三段——`Goal`（目标）、`Result`（结果）、`Feedback`（反馈）。`RfidScan.action` 的 Goal 为 `int32 timeout_sec`，Result 为 `bool success / string card_uid / string card_type / string message`，Feedback 为 `string status`。
- **为什么三段**：动作是异步长耗时任务，客户端发 Goal 启动，服务端执行期间用 Feedback 上报进度，完成后返回 Result——三段各自承载不同的通信方向（Goal 客户端→服务端，Feedback/Result 服务端→客户端）。
- **怎么用**：编译后生成 `RfidScan.Goal`、`RfidScan.Result`、`RfidScan.Feedback` 三个类，实验8 的 `rfid_action_server`/`rfid_action_client` 分别通过 `RfidScan.Result()`、`RfidScan.Feedback()`、`RfidScan.Goal()` 使用它们。

**操作步骤**：

```bash
cat action/RfidScan.action
```

```text
# 来源：action/RfidScan.action（全文）
# 目标：执行一次读卡任务
int32 timeout_sec
---
# 结果
bool success
string card_uid
string card_type
string message
---
# 反馈
string status
```

**易错点**：
- ⚠️ 只用了一个 `---` 分隔（把动作当服务）→ **解决**：`.action` 必须有两个 `---`，分隔出三段。
- ⚠️ 混淆 `RfidScan.Result` 与 `RfidScan.Goal` 的字段 → **解决**：Goal 只含 `timeout_sec`，Result 含 `success/card_uid/card_type/message`，Feedback 只含 `status`。

---

#### 步骤 5：CMakeLists 编译配置（15 分钟）

**知识点讲解**：

**rosidl_generate_interfaces 编译（知识点 2.5.2）**
- **是什么**：接口包是 `ament_cmake` 构建，核心语句是 `rosidl_generate_interfaces(${PROJECT_NAME} <接口文件列表> DEPENDENCIES <依赖>)`（源码 `CMakeLists.txt` L14-22），它把 `.msg/.srv/.action` 编译成 Python/C++ 双方可用的消息代码。
- **为什么声明 DEPENDENCIES**：`TemperatureHumidity` 等用到了 `float32` 等基础类型（来自 `std_msgs`），`RfidScan` 的 Goal 用到了 `int32`（来自 `builtin_interfaces`），动作还需要 `action_msgs` 提供 GoalStatus 等基础设施——依赖声明告诉编译器去哪找这些基础类型。
- **怎么用**：把新增接口文件加进 `rosidl_generate_interfaces` 列表，重新 `colcon build` 即可；`ament_package()` 收尾（L24）。

**操作步骤**：

打开 `CMakeLists.txt`，阅读 `rosidl_generate_interfaces`（L14-22）。

```cmake
# 来源：ros_sensor_interfaces/CMakeLists.txt L14-22
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/VerifyFingerprint.srv"
  "srv/TriggerRelay.srv"
  "action/RfidScan.action"
  "msg/TemperatureHumidity.msg"
  "msg/HeartRateSpO2.msg"
  "msg/PhotoState.msg"
  DEPENDENCIES std_msgs action_msgs builtin_interfaces
)
```

**易错点**：
- ⚠️ 新增 `.msg` 文件但忘记加进 `rosidl_generate_interfaces` → **解决**：每个接口文件都必须显式列入列表才会被编译。
- ⚠️ 用了 `string` 却未声明 `builtin_interfaces` 依赖 → **解决**：`string`/`int32` 等基础类型需要 `builtin_interfaces`（或对应包）在 DEPENDENCIES 中。

---

#### 步骤 6：接口与节点的依赖关系（20 分钟）

**知识点讲解**：

**package.xml 依赖与编译产物（知识点 2.5.2）**
- **是什么**：节点包 `ros_sensor` 在 `package.xml` 中声明 `<depend>ros_sensor_interfaces</depend>`，因此编译时能解析到接口包；节点 Python 代码通过 `from ros_sensor_interfaces.srv import VerifyFingerprint` 导入编译生成的消息类。
- **为什么 source 后才能导入**：`rosidl_generate_interfaces` 的产物生成在 `install/` 目录，必须 `source install/setup.bash` 把该路径加入 `PYTHONPATH`，节点才能 `import` 到。
- **怎么用**：`ros2 interface list/show` 可自省已安装接口，`ros2 interface show` 打印定义便于确认编译是否生效。

**操作步骤**：

```bash
# 编译并 source
cd ~/ros2_ws
colcon build --symlink-install --packages-select ros_sensor_interfaces ros_sensor
source install/setup.bash

# 查看接口定义
ros2 interface list | grep ros_sensor_interfaces
ros2 interface show ros_sensor_interfaces/srv/VerifyFingerprint
ros2 interface show ros_sensor_interfaces/action/RfidScan
ros2 interface show ros_sensor_interfaces/msg/TemperatureHumidity
```

**易错点**：
- ⚠️ `import` 报 `ModuleNotFoundError` → **解决**：先 `colcon build` 再 `source install/setup.bash`，二者缺一不可。
- ⚠️ 接口文件改动后节点未重新编译仍用旧消息 → **解决**：接口是契约，改动后需重新 `colcon build` 接口包与依赖它的节点包。

---

### 七、注意事项

| ⚠️ 注意项 | 说明 |
|-----------|------|
| 接口包类型 | `ros_sensor_interfaces` 必须用 `ament_cmake` 构建，不能用 ament_python |
| 分隔符正确 | `.srv` 一个 `---`、`.action` 两个 `---`，缺一即编译失败 |
| 依赖声明 | 使用基础类型（string/int32）需在 DEPENDENCIES 声明 `builtin_interfaces` |
| 编译顺序 | 先编译接口包，再编译依赖它的节点包 |
| 环境加载 | 编译后必须 `source install/setup.bash` 才能 `import` 到自定义消息 |

### 八、实验总结

#### 8.1 完成成果

完成本实验后，你应当能够：
- ✅ 说清 `.msg`/`.srv`/`.action` 三种接口的结构差异与适用场景
- ✅ 读懂 `ros_sensor_interfaces` 包中全部 6 个接口的字段定义
- ✅ 理解 `rosidl_generate_interfaces` 的编译配置与 `DEPENDENCIES` 作用
- ✅ 使用 `ros2 interface list/show` 自省接口定义
- ✅ 对照实验6-8，理清各传感器节点用到的标准接口与自定义接口

#### 8.2 技能收获

| 技能 | 说明 |
|------|------|
| 接口定义 | 掌握 `.msg`/`.srv`/`.action` 的字段语法与分隔符语义 |
| 接口编译 | 掌握 `rosidl_generate_interfaces` 与 `ament_cmake` 构建配置 |
| 包依赖管理 | 理解接口包/节点包分离及 `package.xml` `<depend>` 依赖 |
| 接口自省 | 使用 `ros2 interface list/show` 查看已安装接口 |
| 选型意识 | 理解「标准接口 vs 自定义接口」的取舍（单值用标准，结构化用自定义） |

#### 8.3 常见问题与解答

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| `rosidl_generate_interfaces` 编译失败 | 接口文件语法错误或依赖缺失 | 检查分隔符数量、字段类型、DEPENDENCIES |
| `import ros_sensor_interfaces` 失败 | 未编译或未 source | `colcon build` 后 `source install/setup.bash` |
| `ros2 interface list` 无自定义接口 | 接口包未编译成功 | 检查 CMakeLists 的 `rosidl_generate_interfaces` 列表 |
| 新加字段后节点读不到 | 节点未重新编译 | 接口改动后重编接口包 + 节点包 |
| 字段类型报错 | 使用了 `int` 而非 `int32` | ROS2 接口用定长类型（int32/uint8/float32 等） |

### 九、实验报告要求

#### 9.1 报告内容

完成实验后，提交一份实验报告，包含以下内容：

1. **实验基本信息**：实验名称、实验日期、实验者姓名、实验平台信息
2. **实验过程记录**：截取 `ros2 interface list/show` 打印的 6 个接口定义、`colcon build` 编译成功的终端截图
3. **原理分析**（不少于 400 字）：用自己的语言解释以下三个问题：
   - ① `.msg`、`.srv`、`.action` 三者在文件结构上有何本质区别？各自的 `---` 分隔符把文件分成了哪几段？
   - ② 为什么 `ros_sensor_interfaces` 要独立成一个包，而不是把接口定义直接写在 `ros_sensor` 节点包里？
   - ③ `HeartRateSpO2.msg` 为什么要有 `bool valid` 字段？如果去掉它，MAX30102 未接触皮肤时会发生什么？
4. **思考题**（见下方）

#### 9.2 思考题

**思考题 1**：
`TemperatureHumidity.msg` 用两个 `float32` 表达温湿度。假设 DHT11 还需要上报「传感器在线状态」和「最近一次读数时间戳」，你会如何扩展这个 `.msg`？请给出完整的字段定义，并说明新增字段的类型选择理由。

**思考题 2**：
实验6 的 `gas_sensor_node` 用的是标准消息 `std_msgs/msg/Float32` 发布单个 ppm 值，而其它传感器用了自定义消息。请问：如果将来 MQ5 需要同时发布「ppm 浓度 + 电压 + ADC 原始值」三个量，你会改用标准消息还是自定义消息？请给出你的方案与理由，并与 `ros_sensor_interfaces` 的命名风格保持一致。

#### 9.3 评分标准

| 评分项 | 权重 | 评分标准 |
|-------|------|---------|
| 实验操作完整性 | 25% | 是否成功编译接口包并用 `ros2 interface list/show` 自省 |
| 代码理解 | 20% | 能否准确解释 CMakeLists.txt 与各接口文件的定义 |
| 原理分析 | 25% | 对三种接口结构、接口包/节点包分离、valid 字段的理解深度 |
| 思考题 1 | 15% | 对 msg 字段扩展的类型选择合理性 |
| 思考题 2 | 15% | 对标准/自定义接口选型的论证与命名一致性 |

---
