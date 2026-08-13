# 实验3：具身智能工厂--接口功能设计（4h）

### 3.1 关联知识点

- 2.1.1 A/C 系列接口（前置：实验 2 的五节点拓扑、ROS 2 话题/服务消息类型概念）
- 2.1.2 D 系列复用接口（前置：2.1.1，需了解复用包 car1_arm_controller / car1_base_driver）
- 2.1.3 E/F 系列接口（前置：2.1.1，需先理清 N2 对外服务与 N-conveyor 服务）
- 2.2.1 YAML 参数化（前置：ROS 2 参数机制，需理解 /** ros__parameters 结构）
- 2.2.2 双模式（前置：2.2.1，需先理解 grasp 双模式含义）
- 2.2.3 意图映射（前置：2.2.1，需先理解 D2 意图映射层设计）

### 3.2 实验目标

1. **掌握**A/C/D/E/F 五大系列接口的定义位置、消息类型与方向（谁发布、谁订阅、谁调用）。
2. **理解**"意图 → 任务 → 执行"的接口调用链（intent 话题 → start_load 服务 → grasp/start 服务 → grasp/status 话题 → speak 话题），能画出完整闭环。
3. **掌握**`config/eai_factory.yaml` 的参数配置方法（mode / grasp.tasks / safety / conveyor / intents），会解释意图映射（load → /eai_factory/start_load）的配置驱动原理。
4. **独立完成**一份接口清单表（接口编号/名称/类型/方向/消息/实现位置/行号），并能用 ros2 命令验证（可选）。
5. **迁移**：能对任意 ROS 2 项目快速产出"接口清单 + 消息类型 + 实现位置"对照表。

### 3.3 实验环境

| 类别 | 内容 |
|------|------|
| 硬件 | B2 麦克纳姆底盘、C1 五自由度机械臂 + 夹爪（本实验可纯文档阅读，也可在已启动的系统中验证）；文档涉及的传感器：激光雷达、RGB-D 深度相机、光电传感器、AprilTag 标签（tag_id=3） |
| OS | Ubuntu 22.04 + ROS 2 Humble |
| Python | 3.10（voice/vision/grasp/conveyor 节点运行时使用 /home/iflytek/ros2_venv/bin/python3） |
| 核心库 | rclpy、std_msgs、std_srvs、geometry_msgs、sensor_msgs、car1_base_driver_msgs（SetBusServoState / MotorsState）、tf2_ros |
| 依赖 | 阅读对象：`docs/02_架构设计.md`（接口定义 v1 章节）、`config/eai_factory.yaml`、`eai_factory/scheduler_node.py`、`eai_factory/grasp_node.py`、`eai_factory/conveyor_node.py`、`eai_factory/voice_node.py`、`eai_factory/safety_node.py` |

### 3.4 实验难度

- 难度: ⭐⭐（设计性）
- 重点：A/C/D/E/F 系列接口与消息类型的对应关系；意图→任务→执行的接口调用链；yaml 参数化与意图映射配置。
- 难点：区分"触发语义"（start 类服务立即返回）与"完成语义"（status/state 话题通知）两类接口；双模式（vision=true/false）下同一接口在不同任务中的不同用法；F10 danger 接口"双停"（流水线急停 + 机械臂 emergency_stop）的联锁链。

### 3.5 实验现象

**快速验证流程**（本实验可选起环境验证，以下为命令类验证流程；若不满足起环境条件可只做文档梳理）：

```bash
# 方式一：完整启动（需实机，耗时较长）
ros2 launch eai_factory eai_factory.launch.py start_voice:=false

# 方式二：验证节点与接口（系统已启动后）
ros2 node list | grep eai_factory                     # 应看到 5 个节点
ros2 topic list | grep eai_factory                    # 应看到 intent/speak/interrupt/danger/...
ros2 service list | grep eai_factory                  # 应看到 start_load/start_sort/start_palletize/grasp/start/...
ros2 interface show std_srvs/srv/Trigger              # 查看 Trigger 消息结构（success + message）
ros2 interface show geometry_msgs/msg/PoseStamped     # 查看位姿消息结构
ros2 service call /eai_factory/start_load std_srvs/srv/Trigger "{}"   # 手动触发装货（需安全环境）
```

**预期效果描述**：

- 能默写出 A1-A3、C1-C4、D1-D7、E1-E3、F1-F10 每个接口的名称、类型、方向与消息类型。
- 能画出"语音→intent→start_load→grasp/start→grasp/status→speak"的闭环调用链。
- 能指出 yaml 中 mode/grasp.tasks/safety/conveyor/intents 各段的配置项与作用，并解释意图映射为何"改 yaml 不改代码"。

### 3.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：阅读接口定义 v1 记录 A/C/D/E/F 系列] --> B[步骤2：阅读 yaml 理解参数化与意图映射]
    B --> C[步骤3：源码联查各 node.py 核对接口实现]
    C --> D[步骤4：用 ros2 命令验证接口（可选）]
    D --> E[步骤5：完成接口清单表]
```

#### 步骤1：阅读接口定义 v1，记录 A/C/D/E/F 系列接口（60min）

**知识点讲解**：

**2.1.1 A/C 系列接口 + 2.1.2 D 系列复用接口 + 2.1.3 E/F 系列接口**

- **原理**：接口定义按"归属系列"组织：A 系列是 N1↔N2 的意图/播报/打断话题（A1 intent、A2 speak、A3 interrupt，全 std_msgs 基础类型）；C 系列是 N3 安全接口（C1 danger 话题、C2 status 话题、C3 舵机力矩话题 SetBusServoState、C4 go_work 服务）；D 系列是 N2 对复用节点的调用（D1-D7，含 /visual_grasp/start 服务与 /visual_grasp/status 话题、arm_controller 服务组、set_motor 话题、set_pick_target 话题）；E 系列是 N2 对外暴露的三个任务服务（E1-E3 start_load/start_sort/start_palletize，全 std_srvs/Trigger）；F 系列是 N-conveyor 的流水线接口（F1-F9 服务与话题、F10 是 N3→conveyor 的 danger 联锁）。消息类型选择规律：状态类用 std_msgs/String 枚举（conveyor/state 的 idle/running/sensor_blocked/...、safety/status 的 safe/danger/recover、grasp/status 的 task|done/failed），触发类用 std_srvs/Trigger（success+message），位姿类用 geometry_msgs/PoseStamped。理解这套规律后，看到任何新接口都能先猜出类型。
- **源码对应**：`docs/02_架构设计.md L30-L34（A1-A3）、L38-L43（C1-C4）、L47-L56（D1-D7）、L62-L66（E1-E3）、L70-L81（F1-F10）`

| # | 接口 | 类型 | 方向 | 消息 | 说明 |
|---|------|------|------|------|------|
| A1 | `/eai_factory/intent` | 话题 | N1→N2 | `std_msgs/String` | 意图："load"/"sort"/"palletize"（英文枚举） |
| C1 | `/eai_factory/safety/danger` | 话题 | N3→N2,N1 | `std_msgs/Bool` | true=危险(释放力矩)，false=解除(恢复+回work) |
| D3 | `/arm_controller/pick` | 服务 | N2→ | `std_srvs/Trigger` | 抓取 |
| E1 | `/eai_factory/start_load` | 服务 | →N2 | `std_srvs/Trigger` | 装货任务（视觉抓取） |
| F3 | `/eai_factory/conveyor/run_until_sensor` | 服务 | →N-conveyor | `std_srvs/Trigger` | **异步**：运转直到光电遮挡→定点停；完成走 state 话题 |

- **配图说明**（重点）：配一张"接口五系列分布图"：以 N2 为中心，左侧挂 A 系列（与 N1）、下侧挂 E 系列（对外服务）、右侧挂 D 系列（复用调用）、上侧挂 C 系列（N3）、右下挂 F 系列（N-conveyor），每个接口标类型图标（话题=圆点、服务=方括号）。

**操作步骤**：

1. 通读 `docs/02_架构设计.md` 的"接口定义（v1，已确认）"章节（`L26-L81`）。
2. 按系列抄录接口清单：编号、接口名、类型、方向、消息、说明六列，逐条填写。
3. 特别标注"触发语义 vs 完成语义"两类接口（如 E1 是触发、grasp/status 与 conveyor/state 是完成），在清单表加一列"语义"。

**易错点**：

- ⚠️ 把 D 系列（复用接口）误记为 eai_factory 自定义接口 → **解决**：`docs/02_架构设计.md L58` 注明"D 系列为复用现有接口"，接口实现在 car1_arm_controller / car1_base_driver / visual_grasp 等复用包中，eai_factory 只调用不改。

#### 步骤2：阅读 yaml，理解参数化与意图映射（50min）

**知识点讲解**：

**2.2.1 YAML 参数化 + 2.2.2 双模式 + 2.2.3 意图映射**

- **原理**：`config/eai_factory.yaml` 用 `/**: ros__parameters:` 顶层结构向所有节点下发参数：mode（debug/production 双模式）在 `L7`；voice 段（唤醒词/热词/LLM intent_hints/固定播报文案）在 `L10-L54`；vision 段（tag_id=3/tag_size=0.025/tag_family=tag36h11）在 `L56-L63`；grasp 段（move_delay/lift_height/pick_offset 三轴补偿/tasks 三任务 pose 与 vision 标志）在 `L65-L90`；safety 段（enabled/front_start_deg=-30/front_end_deg=30/danger_dist=0.20/persist_time=0.5）在 `L92-L98`；conveyor 段（motor_id=1/run_speed/photo_gpio_file/sensor_timeout/debounce_reads/poll_period）在 `L100-L108`；intents 意图映射（load→/eai_factory/start_load 等）在 `L110-L117`。参数化带来的收益是"改坐标/改阈值不动代码"：grasp.tasks 里每个任务的 observe_pose/place_pose 是 [x,y,z,pitch] 四元组，vision 标志决定走视觉抓取还是固定点位抓取（双模式）；intents 段是"意图 ↔ 服务名"的表驱动映射，新增意图只需改 yaml。意图映射的实现消费端是 voice 节点（`voice_node.py L228` 读取 intent_hints 做 LLM 提示词、`L748` 关键字兜底）与调度器（服务路由）。
- **源码对应**：`config/eai_factory.yaml L7（mode）、L78-L90（grasp.tasks 双模式）、L92-L98（safety 段）、L110-L117（intents 映射）`

```yaml
mode: production
grasp:
  tasks:
    load:      # 装货（视觉抓取）
      vision: true
      observe_pose: [0.16, 0.0, 0.27, 2.5307]
      place_pose:   [0.05675, -0.13166, 0.20386, 2.93322]
    sort:      # 分拣（固定点位抓取，无视觉）
      vision: false
      observe_pose: [0.0622, -0.1158, 0.1951, 3.0371]
    palletize: # 码垛（固定点位抓取，无视觉）
      vision: false
      observe_pose: [0.145, 0.0027, 0.1850, 3.1381]
intents:
  load:      { action: "/eai_factory/start_load" }
  sort:      { action: "/eai_factory/start_sort" }
  palletize: { action: "/eai_factory/start_palletize" }
```

- **配图说明**（重难点）：配一张"参数驱动链图"：yaml 文件 → 各节点 declare_parameter/get_parameter → 运行行为（mode 决定 debug 是否等 confirm；vision 标志决定抓取模式；intents 决定意图到服务的映射），用颜色区分"坐标类/开关类/映射类"参数。

**操作步骤**：

1. 通读 `config/eai_factory.yaml` 全文（117 行），按段记录参数名、默认值、作用。
2. 对比 `docs/02_架构设计.md L161-L175`（D9 配置示例）与 yaml 实际值，找出差异（如 sort.place_pose 从 [0.1334,-0.1396,0.1975,2.7283] 调整为 [0.1434,-0.1296,0.2075,2.7283]），理解"配置驱动、改配置不动代码"。
3. 在笔记中写出意图映射表的两种消费方式：voice 侧读 intent_hints 提示词（`voice_node.py L228、L699-L705`）、调度器侧路由服务（`scheduler_node.py L62-L67`）。

**易错点**：

- ⚠️ 以为 mode 只影响抓取 → **解决**：mode 在 `config/eai_factory.yaml L7` 定义、由 grasp 节点读取（`grasp_node.py L50、L73`），debug 模式在视觉抓取时"检测到目标→存目标→等 /eai_factory/grasp/confirm 服务"（`grasp_node.py L295-L301`），production 直接 pick；改 mode 需重启节点生效。

#### 步骤3：源码联查各 node.py，核对接口实现（50min）

**知识点讲解**：

**2.1.1/2.1.2/2.1.3 接口实现核对**

- **原理**：接口定义（文档）与接口实现（代码）必须一一对应。核对方法是抓三个点：①create_publisher/create_subscription 对应话题接口；②create_service/create_client 对应服务接口；③节点 docstring 头部通常自带接口清单（如 grasp_node.py 与 conveyor_node.py 的模块 docstring）。核对重点是消息类型一致性：例如 A1 用 std_msgs/String、A3 用 std_msgs/Bool（`voice_node.py L250-L253` 与 `scheduler_node.py L37-L42` 对得上）；F3 服务端是 Trigger（`conveyor_node.py L109-L111`）、客户端也在 Trigger（`scheduler_node.py L57-L59` 调用同一名字）；E1-E3 服务端注册在 `scheduler_node.py L62-L67`。联查时要特别核对"文档写的接口是否真的存在"，如文档 D1 提到 /visual_grasp/start，但 eai_factory 当前实现实际走 /eai_factory/grasp/start（N-grasp 自提供服务），这是版本演进留下的差异，需要在清单表里标注。
- **源码对应**：`grasp_node.py L2-L30（docstring 接口清单）、L104-L148（订阅/发布/服务实现）`；`conveyor_node.py L2-L35（docstring 服务/话题清单）、L83-L117（发布/服务实现）`；`voice_node.py L250-L253（A1/A3/A2 三接口实现）`；`safety_node.py L56-L63（C1/C2/C3 发布与 C4 客户端）`

```python
# voice_node.py — A 系列接口实现
self.intent_pub = self.create_publisher(String, '/eai_factory/intent', 10)      # A1
self.interrupt_pub = self.create_publisher(Bool, '/eai_factory/interrupt', 10)  # A3
self.speak_sub = self.create_subscription(String, '/eai_factory/speak', self._speak_cb, 10)  # A2

# conveyor_node.py — F 系列服务实现（节选）
self.run_until_sensor_srv = self.create_service(
    Trigger, '/eai_factory/conveyor/run_until_sensor',
    self._run_until_sensor_cb, callback_group=self._cbg)                        # F3
```

- **配图说明**：配一张"文档接口 ↔ 代码实现对照抽查表图"，列 5 个抽查点（A1/A3、C1/C3、E1、F3、D3/D4）分别给出"文档行号 → 实现文件行号 → 一致性结论"。

**操作步骤**：

1. 用 Grep 抽查五组接口的实现位置：`grep -n "create_publisher\|create_subscription\|create_service\|create_client" eai_factory/*.py`。
2. 核对消息类型：重点看 A1/A3（voice_node.py L250-L253 vs scheduler_node.py L37-L42）、C1/C3（safety_node.py L58-L61 vs conveyor_node.py L94-L96）、F3（conveyor_node.py L109-L111 vs scheduler_node.py L57-L59）。
3. 在接口清单表中为每个接口标注"实现位置（文件+行号）"与"一致性结论（一致/差异说明）"。

**易错点**：

- ⚠️ 直接照抄文档接口不核对代码 → **解决**：以代码为准。例如文档 D1 写 /visual_grasp/start，而 grasp_node.py 实际提供 /eai_factory/grasp/start（`L140-L142`）、scheduler 也调用后者（`scheduler_node.py L55-L56`），清单表应标注差异并说明"当前实现自包含，未使用 visual_grasp 原节点"。

#### 步骤4：用 ros2 命令验证接口（可选，30min）

**知识点讲解**：

**2.1.x 接口运行时验证**

- **原理**：接口的"运行时真值"是节点启动后由 ROS 2 图（graph）暴露的。`ros2 node list / topic list / service list / interface show` 四件套可以无侵入地核对"文档接口是否存在、消息类型是什么"：`interface show` 能直接打印消息/服务结构的字段定义；`service call` 能手工触发服务（如 start_load）观察返回的 success/message。验证注意：Trigger 请求体是空结构 `{}`，服务调用是阻塞式等响应的；在实机上触发任务类服务前必须确认安全环境（机械臂活动范围无人、无遮挡）。本步骤为**可选**：无法起环境时，直接跳过，不影响实验成果（接口清单表基于文档+源码完成）。
- **源码对应**：`std_srvs/srv/Trigger`（success: bool + message: string）被 E1-E3/F1-F5/grasp start 等所有 Trigger 服务共用；`PoseStamped`（header + pose.position + pose.orientation）被 A 系列外的位姿话题（vision/target、target_pose、set_pick_target）共用。

**操作步骤**：

1. （环境允许时）启动系统或仅启动 eai_factory 节点后，依次执行 `ros2 node list`、`ros2 topic list | grep eai_factory`、`ros2 service list | grep eai_factory`，与清单表比对。
2. 执行 `ros2 interface show std_srvs/srv/Trigger` 与 `ros2 interface show geometry_msgs/msg/PoseStamped`，记录字段结构。
3. （安全环境确认后）执行 `ros2 service call /eai_factory/start_load std_srvs/srv/Trigger "{}"`，观察返回 `success: True / message: 'load task triggered'`（对应 `scheduler_node.py L214-L218`）。

**易错点**：

- ⚠️ 在未启动对应节点时调用服务报 "service not available" → **解决**：先 `ros2 service list | grep start_load` 确认服务存在；eai_factory 各服务由调度器提供（`scheduler_node.py L62-L67`），需先启动 eai_factory 节点。

#### 步骤5：完成接口清单表（20min）

**操作步骤**：

1. 汇总前四步产出，整理一张完整接口清单表：编号 / 接口名 / 类型 / 方向 / 消息 / 语义（触发 or 完成）/ 实现位置（文件+行号）/ 一致性结论。
2. 补画"意图→任务→执行"调用链图：语音 → A1 intent("load") → N2 _run_task → E1 start_load（或直接内部路由）→ set_task + grasp/start 服务 → 执行 → grasp/status("load|done") → speak("装货完成")。
3. 自检清单：A/C/D/E/F 五系列是否齐全；每个接口是否都有实现行号；"触发/完成"语义是否标注。

**易错点**：

- ⚠️ 清单表漏掉"完成语义"接口（grasp/status、conveyor/state） → **解决**：全链路闭环的最后一环正是 grasp/status → speak（`scheduler_node.py L195-L208`），漏掉它就无法解释"装货完成"播报从哪来。

### 3.7 注意事项

- ⚠️ 本实验可**纯文档阅读**（步骤 4 可选）；若实机验证，触发 `ros2 service call /eai_factory/start_load` 前必须确认机械臂活动范围内无人员与障碍物，建议在 debug 模式下验证（yaml `mode: debug`，视觉抓取会停在 await confirm 等待人工确认）。
- ⚠️ 涉及 launch 的命令注意顺序依赖：`ros2 launch eai_factory eai_factory.launch.py start_voice:=false` 会拉起底层系统（bringup/arm/peripherals），若底层已在跑需加 `start_base:=false`。
- ⚠️ `grasp.tasks` 中 observe_pose/place_pose 的 [x,y,z,pitch] 为 base_link 系四元组，修改配置需同步重启 grasp 节点生效；切勿在机械臂运动过程中改 yaml。

### 3.8 实验总结

**完成成果**: 一份覆盖 A/C/D/E/F 五系列的接口清单表（含消息类型、语义、实现行号、一致性结论）；一张"意图→任务→执行→完成播报"调用链图；一份 yaml 参数配置解读（mode/grasp.tasks/safety/conveyor/intents 各段）；（可选）ros2 命令验证记录。

**技能收获**:

- 技能1：接口清单化整理方法（编号/类型/方向/消息/语义/实现位置六要素）
- 技能2：文档接口与代码实现的一致性核对方法
- 技能3：ros2 topic/service/interface 四件套的运行时验证
- 技能4：yaml 参数化与表驱动（意图映射）配置思维

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| 接口消息类型记混（String vs Bool） | 未按"语义定类型"规律记忆 | 状态枚举用 String（intent/state/status）、布尔信号用 Bool（interrupt/danger/detected）、触发类服务用 Trigger（`docs/02_架构设计.md L30-L81`） |
| 文档接口与代码不一致 | 版本演进（如原计划复用 visual_grasp/start，后改为自包含 grasp/start） | 以代码为准：grasp_node.py L140-L142 提供 /eai_factory/grasp/start，scheduler_node.py L55-L56 调用同名单，清单表标注差异 |
| service call 报 not available | 对应节点未启动或服务名拼错 | `ros2 service list` 先查存在性；服务由调度器提供（E1-E3）、由 grasp/conveyor 提供（grasp/start、F1-F5） |
| 改了 yaml 坐标不生效 | 参数在节点启动时读取一次 | 修改 yaml 后重启对应节点；运行中可用 `ros2 param get /eai_factory_grasp grasp.tasks.load.observe_pose` 检查当前值 |

### 3.9 实验报告要求

**思考题**:

1. 对比 A1（intent 话题）与 E1（start_load 服务）：为什么意图用话题广播、而任务触发同时提供服务？两种方式各自的适用场景是什么？
2. F3（run_until_sensor）与 F4（emergency_stop）同为 Trigger 服务，为什么一个是"异步完成走 state 话题"、一个是"同步立即生效"？请结合单线程 executor 的阻塞风险分析。
3. 如果要把"start_load 的调用改为不再经过调度器服务，而是由 intent 话题直接驱动"，需要改动哪些接口？请从 E 系列与 A 系列接口的设计角度分析利弊。

**评分标准**:

- 接口清单表完整准确（40 分）：A/C/D/E/F 五系列齐全、类型/方向/消息正确、语义标注清晰
- 调用链与实现核对（30 分）：意图→任务→执行闭环正确、实现行号真实、差异标注合理
- yaml 参数化解读（20 分）：mode/grasp.tasks/safety/conveyor/intents 各段作用正确、意图映射原理清楚
- 验证记录与报告规范（10 分）：（可选）ros2 命令验证记录完整、行号引用真实 = 100 分。
