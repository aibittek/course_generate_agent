# 实验7：具身智能工厂--码垛集成测试（6h）

### 7.1 关联知识点

- 5.2.1 流水线电机（复用底盘电机通道 M1，`conveyor.motor_id` 现场配置；前置依赖 1.2.3）
- 5.2.2 光电定点停（`run_until_sensor` 运转直到光电遮挡→定点停，防抖确认；前置依赖 5.2.1）
- 5.2.3 流水线状态机与急停（idle/running/sensor_blocked/emergency 与急停复位；前置依赖 5.2.2）
- 1.3.2 palletize 编排（先 `run_until_sensor` 送料→`sensor_blocked`→再抓取；前置依赖 1.3.1）

### 7.2 实验目标

1. 理解流水线复用底盘电机（M1）的驱动原理（发布速度→STM32 保持→发 0 即停）与光电传感器电平约定 — 原理理解
2. 掌握 `run_until_sensor` 光电定点停流程（先清沿后挡沿、防抖确认、超时保护）与流水线状态机转换关系 — 独立完成
3. 掌握 N2 调度器 palletize"先送料后抓取"跨节点编排，能独立通过服务/语音触发并观察完整码垛链路 — 独立完成
4. 掌握急停置位与复位机制，并能依据 `docs/10_流水线测试用例.md` 迁移到其他流水线场景（如分拣送料改造）完成用例验收 — 迁移应用

### 7.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱 B2 / 机器人小车 C1（5DOF 机械臂 + 夹爪）；流水线电机（复用底盘电机 M1 前左轮通道）；光电传感器（GPIO0_C1=17）；AprilTag 标签（本实验码垛为固定点位抓取，不使用视觉） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10；conveyor / grasp / scheduler 节点经 `/home/iflytek/ros2_venv/bin/python3` 运行（launch 直接跑 .py） |
| 核心库 | rclpy、std_srvs、std_msgs、car1_base_driver_msgs（MotorsState/MotorState，复用底盘电机协议） |
| 依赖 | `scripts/setup_conveyor_gpio.sh`（导出 GPIO17 + 上拉输入）；`/sys/class/gpio/gpio17/value` 可读；机械臂 `arm_controller` 在跑（码垛抓取/放置/回 work 依赖） |

### 7.4 实验难度

- 难度: ⭐⭐⭐（综合性）
- 重点: `run_until_sensor` 光电定点停流程（清沿→挡沿→防抖→停）；palletize 跨节点编排（conveyor→grasp 状态同步）
- 难点: 状态机急停置位/复位语义（emergency 期间拒绝 run）；固定点位抓取"提前开爪"动作时序（开爪→到位→闭爪→抬升→放置→再抬升→回 work）

### 7.5 实验现象

**快速验证流程**：

1. 环境准备（导出 GPIO）与省内存启动：
   ```bash
   source /opt/ros/humble/setup.bash
   source /home/iflytek/ros2_ws/install/setup.bash
   sudo bash scripts/setup_conveyor_gpio.sh
   cat /sys/class/gpio/gpio17/value     # 应输出 0 或 1
   ros2 launch eai_factory eai_factory.launch.py start_voice:=false start_vision:=false start_grasp:=true start_viz:=false
   ```
2. 流水线单测（观察 电机运转→光电遮挡→定点停）：
   ```bash
   ros2 topic echo /eai_factory/conveyor/state
   ros2 service call /eai_factory/conveyor/run_until_sensor std_srvs/srv/Trigger
   # 把物品放到流水线起始端，随流水线移动
   ```
3. 码垛任务（观察 送料→sensor_blocked→抓取→放置→回 work）：
   ```bash
   ros2 topic echo /eai_factory/grasp/status
   ros2 service call /eai_factory/start_palletize std_srvs/srv/Trigger
   ```
4. 急停测试（观察 急停与恢复）：
   ```bash
   ros2 service call /eai_factory/conveyor/emergency_stop std_srvs/srv/Trigger
   ros2 service call /eai_factory/conveyor/run std_srvs/srv/Trigger        # 应被拒绝
   ros2 service call /eai_factory/conveyor/reset_emergency std_srvs/srv/Trigger
   ```
5. 语音联动（说"码垛"，观察完成播报"码垛完成"）。

**预期效果描述**：

- `run_until_sensor` 服务立即返回 started；流水线电机转动（`/car1_base_driver/set_motor` 出现 `id: 1, rps: 0.1`）；物品到达光电位置后自动停（`rps: 0.0`），state 话题出现 `sensor_blocked`
- `start_palletize` 后：先送料（`running`）→ `sensor_blocked` → 机械臂开始固定点位抓取（提前开爪→到位→闭爪→抬升→放置→抬 5cm→回 work）→ grasp status `palletize|done`
- 急停后 state → `emergency`、`/eai_factory/conveyor/emergency` 话题 `data: true`，run 被拒绝；`reset_emergency` 后 emergency `data: false`，可再次 run
- 语音说"码垛"：完成码垛后播报"码垛完成"

### 7.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：环境准备与流水线单测] --> B[步骤2：码垛任务全流程验证]
    B --> C[步骤3：急停与复位测试]
    C --> D[步骤4：语音联动码垛]
    D --> E[步骤5：流水线测试用例验收]
    E --> F[完成]
```

---

#### 步骤1：环境准备与流水线单测（70min）

**知识点讲解**：

**流水线电机复用底盘电机通道（5.2.1）**

- **原理**：智慧工厂流水线不再单独购买电机驱动，而是**复用底盘电机通道 M1（前左轮）**。N-conveyor 通过发布 `/car1_base_driver/set_motor`（`MotorsState`，含 `MotorState{id, rps}`）驱动流水线：STM32 会**保持最后收到的速度持续运转**，因此"停止"只需发布 `rps=0`（立即且可靠）。电机通道号通过 `conveyor.motor_id` 现场配置（本项目为 1），速度 `run_speed=0.1 m/s`。光电传感器接 GPIO0_C1=17，读 `/sys/class/gpio/gpio17/value`，电平约定 **HIGH(1)=无遮挡、LOW(0)=遮挡**；GPIO 必须先导出（sysfs 导出 + 内部上拉，需 root），N-conveyor 启动时检测未导出会自动 `sudo` 调 `setup_conveyor_gpio.sh`（幂等）。
- **源码对应**：`eai_factory/conveyor_node.py` L53-60（conveyor.* 参数声明）、L127-133（`_set_motor` 发布速度）、L135-165（`_ensure_gpio_exported` 自动导出）；`scripts/setup_conveyor_gpio.sh` L13-24（已导出跳过）、L47-49（sysfs 导出 + direction=in）；`config/eai_factory.yaml` L100-108（conveyor 段）
  ```python
  def _set_motor(self, rps):
      msg = MotorsState()
      m = MotorState()
      m.id = self.motor_id
      m.rps = float(rps)
      msg.data = [m]
      self.motor_pub.publish(msg)
  ```
- **公式/配图说明**（重难点）：
  - 电平约定：`value==sensor_blocked_level(0)` → 遮挡；`value==1` → 无遮挡
  - 参数表：`motor_id=1`、`run_speed=0.1`、`sensor_timeout=30.0s`、`debounce_reads=3`、`poll_period=0.05s`（`eai_factory.yaml` L100-108）

**操作步骤**：

1. 进入工程目录并导出 GPIO（若已导出会提示跳过）：
   ```bash
   cd ~/ros2_ws/src/xflz_eai_car1/app/eai_factory
   sudo bash scripts/setup_conveyor_gpio.sh
   cat /sys/class/gpio/gpio17/value   # 0 或 1，可读即成功
   ```
2. 省内存启动（保留流水线 + 机械臂，关闭语音/视觉/调试画面）：
   ```bash
   source /opt/ros/humble/setup.bash
   source /home/iflytek/ros2_ws/install/setup.bash
   ros2 launch eai_factory eai_factory.launch.py \
     start_voice:=false start_vision:=false start_viz:=false
   ```
3. 确认节点与服务：
   ```bash
   ros2 node list                  # 应看到 eai_factory_conveyor / eai_factory_grasp / eai_factory_scheduler
   ros2 service list | grep conveyor   # run / stop / run_until_sensor / emergency_stop / reset_emergency
   ```
4. 流水线启动/停止单测：
   ```bash
   ros2 topic echo /car1_base_driver/set_motor     # 终端2
   ros2 service call /eai_factory/conveyor/run std_srvs/srv/Trigger
   ros2 service call /eai_factory/conveyor/stop std_srvs/srv/Trigger
   ```

**易错点**：

- ⚠️ GPIO 未导出 → `_read_photo_level` 报 `photo gpio read failed`，state 置 `error` → **解决**：先手动 `sudo bash scripts/setup_conveyor_gpio.sh` 一次（节点仅能免密 sudo 自动导出，若 sudo 配置失效需手动）
- ⚠️ 手动遮挡光电测试时方向拿反 → 电平结果与预期相反 → **解决**：确认约定 `1=无遮挡、0=遮挡`（与参考 app.py 一致）

---

#### 步骤2：码垛任务全流程验证（90min）

**知识点讲解**：

**palletize 编排：先送料后抓取（1.3.2）**

- **原理**：码垛任务不是直接抓取，而是**跨节点编排**：N2 调度器先调用 N-conveyor 的 `run_until_sensor` 让流水线送料（物品随皮带移动直到光电遮挡定点停），**等待** `/eai_factory/conveyor/state` 变为 `sensor_blocked` 后才触发 N-grasp 执行码垛抓取。该等待通过订阅 `_conveyor_state_cb` 实现（`_awaiting_sensor` 标志置位期间收到 `sensor_blocked` 即启动抓取）。N-grasp 的 palletize 任务是**固定点位抓取**（`vision=false`）：`observe_pose=[0.145, 0.0027, 0.185, 3.1381]` 即取料点、`place_pose=[0.0608, 0.1345, 0.2051, 2.6461]` 即放置点，动作序列为**提前开爪→直接到位→闭爪→抬升(lift_height=0.03)→移放置位→开爪投放→再抬升(place_lift=0.05)→回 work**。
- **源码对应**：`eai_factory/scheduler_node.py` L98-110（`_start_palletize_sequence` 送料）、L121-127（`_conveyor_state_cb` 收到 sensor_blocked 触发抓取）、L129-152（`_trigger_grasp` 先 set_task 再 start）、L226-230（`/eai_factory/start_palletize` 服务）；`eai_factory/grasp_node.py` L59-61（palletize 固定点位参数）、L273-278（vision=false 走固定抓取）、L413-485（`_do_fixed_grasp` 八步动作序列）；`config/eai_factory.yaml` L87-90（palletize 段）
  ```python
  def _conveyor_state_cb(self, msg):
      if self._awaiting_sensor and msg.data == 'sensor_blocked':
          self._awaiting_sensor = False
          self.get_logger().info('[SCHEDULER] palletize: item at sensor — starting grasp')
          self._trigger_grasp('palletize')
  ```
- **公式/配图说明**（重难点）：
  ```mermaid
  graph LR
      A[调度器 start_palletize] --> B[conveyor run_until_sensor 送料]
      B --> C[state=sensor_blocked]
      C --> D[set_task=palletize + grasp/start]
      D --> E[固定抓取 八步序列]
      E --> F[grasp/status: palletize|done]
  ```

**操作步骤**：

1. 监听状态与抓取反馈：
   ```bash
   ros2 topic echo /eai_factory/conveyor/state
   ros2 topic echo /eai_factory/grasp/status
   ros2 topic echo /eai_factory/conveyor/photo
   ```
2. 触发码垛任务：
   ```bash
   ros2 service call /eai_factory/start_palletize std_srvs/srv/Trigger
   ```
3. 观察完整链路：送料（物品放流水线起始端）→ `running` → 光电遮挡 → `sensor_blocked` → 机械臂开爪到位抓取 → 抬升 → 放置 → 抬 5cm → 回 work → grasp status `palletize|done`
4. 全程关注机械臂动作，确认放置点在码垛区（托盘位置）。

**易错点**：

- ⚠️ 先触发任务再放物品，或物品还没到流水线上 → 送料阶段空跑 30s 后 state=`timeout` → **解决**：触发后尽快把物品放到流水线起始端（`run_until_sensor` 会先等"清沿"再等"挡沿"）
- ⚠️ 码垛时物品堆叠高度与固定点位不匹配 → 夹爪撞货/漏抓 → **解决**：保持取料点物品高度与打点一致；`grasp.lift_height=0.03` 抬升防碰撞，不要中途手扶

---

#### 步骤3：急停与复位测试（60min）

**知识点讲解**：

**流水线状态机与急停复位（5.2.3）**

- **原理**：N-conveyor 内部状态机：`idle`（空闲）→ `running`（运转）→ `sensor_blocked`（定点停）→ `emergency`（急停置位）/ `timeout`（超时）/ `error`（GPIO 读取失败）。`emergency_stop` 会**置位** `_emergency_stop=True` 并立即发 `rps=0` 停带；该标志**持续有效**，期间 `run` / `run_until_sensor` 服务都会被拒绝（返回 `emergency active — call reset_emergency first`），保证"急停后不自动复跑"的安全语义；必须显式调 `reset_emergency` 才复位回 `idle`。状态变化通过 `/eai_factory/conveyor/state`、`/eai_factory/conveyor/emergency` 发布。
- **源码对应**：`eai_factory/conveyor_node.py` L240-248（`_emergency_cb` 置位+停带+state=emergency）、L250-257（`_reset_emergency_cb` 复位）、L176-183（`_set_state` 只发布变化的状态）、L203-207（run 拒绝逻辑）、L223-227（run_until_sensor 拒绝逻辑）；`docs/10_流水线测试用例.md` L106-123（TC6 手动急停用例）
  ```python
  def _emergency_cb(self, request, response):
      self._emergency_stop = True
      self._set_motor(0.0)
      self._set_state('emergency')
      self._publish_emergency()
      ...
      response.message = 'emergency stopped'
  ```
- **公式/配图说明**（重难点）：
  - 状态转换：`idle --run--> running --stop--> idle`；`running --sensor_blocked--> idle(实为 sensor_blocked)`；任意状态 `--emergency_stop--> emergency --reset_emergency--> idle`
  - 急停保持语义：`run/run_until_sensor 均检查 self._emergency_stop 前置条件`（L204、L224）

**操作步骤**：

1. 先启动流水线：
   ```bash
   ros2 service call /eai_factory/conveyor/run std_srvs/srv/Trigger
   ```
2. 急停：
   ```bash
   ros2 service call /eai_factory/conveyor/emergency_stop std_srvs/srv/Trigger
   ```
   观察：流水线立即停、`/eai_factory/conveyor/emergency` `data: true`、日志 `EMERGENCY STOP — conveyor belt stopped`
3. 验证急停保持（应被拒绝）：
   ```bash
   ros2 service call /eai_factory/conveyor/run std_srvs/srv/Trigger
   ```
   预期返回 `success: False, message: "emergency active — call reset_emergency first"`
4. 复位并恢复运转：
   ```bash
   ros2 service call /eai_factory/conveyor/reset_emergency std_srvs/srv/Trigger
   ros2 service call /eai_factory/conveyor/run std_srvs/srv/Trigger   # 恢复成功
   ```

**易错点**：

- ⚠️ 急停后忘记 reset 直接再次触发任务 → 服务一直拒绝 → **解决**：`reset_emergency` 是显式恢复动作，属于安全设计（防误启动），必须走完"复位"再重启任务
- ⚠️ 急停后机械臂仍在原位置 → **解决**：本实验急停只停流水线；机械臂的停止由 N3 雷达 danger 信号触发（见实验8）

---

#### 步骤4：语音联动码垛（70min）

**知识点讲解**：

**语音→意图→任务→执行→完成播报闭环（1.3.2 + 3.1.1）**

- **原理**：说"码垛"后，N1 语音节点经 KWS 唤醒 → ASR 识别 → LLM 意图分类，命中 `intent_hints` 中的 palletize 提示词（"码垛/开始码垛/堆码/马舵"等误识别词），发布 intent 到 `/eai_factory/intent`；N2 调度器 `_intent_cb` 收到 `palletize` 后走与步骤2 完全相同的 `_start_palletize_sequence` 编排。任务完成后 N-grasp 发布 `palletize|done`，调度器 `_grasp_status_cb` 查表映射为中文播报词（load→装货完成/sort→分拣完成/palletize→码垛完成）并发布到 `/eai_factory/speak`，由 N1 TTS 播出"码垛完成"——形成全链路闭环。
- **源码对应**：`eai_factory/scheduler_node.py` L75-78（`_intent_cb` 路由意图）、L195-210（`_grasp_status_cb` 完成播报映射，`palletize→码垛完成`）；`config/eai_factory.yaml` L35-36（palletize 意图提示词）、L53（`palletize_done: "码垛完成"` 播报文案）、L110-117（intents 意图→接口映射表）
  ```python
  if status == 'done':
      phrase = {'load': '装货完成', 'sort': '分拣完成',
                'palletize': '码垛完成'}.get(task, '任务完成')
      ...
      speak.data = phrase
      self.speak_pub.publish(speak)
  ```
- **公式/配图说明**（重难点）：闭环链路 `唤醒词(小飞小飞) → ASR → LLM 意图(palletize) → /eai_factory/intent → 调度器编排(送料+抓取) → grasp/status(palletize|done) → speak(码垛完成) → TTS 播报`

**操作步骤**：

1. 本次启动需开启语音（全功能启动）：
   ```bash
   ros2 launch eai_factory eai_factory.launch.py start_vision:=false start_viz:=false
   ```
   （等待 LLM flask_server 就绪，端口 8080，启动日志约几十秒）
2. 唤醒并下达指令：正对麦克风说 **"小飞小飞"**（听到唤醒提示音后）再说 **"码垛"**。
3. 观察：先放物品到流水线起始端 → 流水线送料 → `sensor_blocked` → 机械臂码垛 → 播报"码垛完成"。
4. 终端同步观察调度器日志 `[SCHEDULER] palletize: feeding belt...`、`task palletize done — announce "码垛完成"`。

**易错点**：

- ⚠️ 语音听成"马舵/码舵"等 → **解决**：`intent_hints` 已内置大量误识别词（`eai_factory.yaml` L36），仍不中可现场追加；可先用 `ros2 topic echo /eai_factory/intent` 看识别结果
- ⚠️ 唤醒后 10s 内不说话导致指令丢失 → **解决**：唤醒后立即下达指令；或直接调服务 `/eai_factory/start_palletize` 对照验证（语音与服务两路等价）

---

#### 步骤5：流水线测试用例验收（70min）

**知识点讲解**：

**测试用例方法论（5.2.1-5.2.3 综合）**

- **原理**：验收需覆盖功能正确性与边界条件：`run`/`stop` 基础启停（TC1/TC2）、光电话题实时性（TC3）、`run_until_sensor` 定点停与超时（TC4/TC5）、手动急停置位/复位（TC6）、N3 安全信号联动急停（TC7）、GPIO 已导出/未导出两种场景（TC8/TC9）。重点理解"急停后任务被拒绝"这一安全语义与"未导出自动补导出"的容错设计。
- **源码对应**：`docs/10_流水线测试用例.md` L42-55（TC1 run）、L57-64（TC2 stop）、L66-76（TC3 photo 话题）、L78-93（TC4 定点停）、L95-104（TC5 超时）、L106-123（TC6 手动急停）、L125-140（TC7 N3 联动）、L142-166（TC8/TC9 GPIO 场景）
- **公式/配图说明**：验收矩阵：每个用例 = 功能 + 命令 + 结果现象三要素，逐条勾选打勾

**操作步骤**：

1. 按 `docs/10_流水线测试用例.md` 逐条执行 TC1~TC9，记录现象与截图：
   ```bash
   # TC3 光电话题
   ros2 topic echo /eai_factory/conveyor/photo        # 遮挡→true，移开→false
   # TC7 手动模拟安全信号（N3 未开时）
   ros2 topic pub -1 /eai_factory/safety/danger std_msgs/msg/Bool "{data: true}"
   ros2 topic echo /eai_factory/conveyor/emergency
   ros2 topic pub -1 /eai_factory/safety/danger std_msgs/msg/Bool "{data: false}"
   ```
2. 至少完成 TC1、TC2、TC4、TC6 四条必测项，并尝试 TC5（不放物品等 30s 看 `timeout`）。
3. 将每条用例的结果（成功/失败、实际现象、日志截图）填入实验报告表格。

**易错点**：

- ⚠️ TC7 用 `-1` 发一次性话题后状态停留在 `emergency` → **解决**：必须再发 `{data: false}` 恢复（N3 节点在跑时用真实雷达触发，见实验8 TS4）
- ⚠️ 验收时开启无关模块浪费内存（语音/视觉） → **解决**：本步骤可 `start_voice:=false start_vision:=false` 省内存，只保留 conveyor + scheduler + grasp

### 7.7 注意事项

- ⚠️ 流水线电机复用底盘电机 M1，**启动前确认机械臂处于 work 安全位、车身固定不动**，避免电机带动平台偏移
- ⚠️ 码垛为实机抓取，**全程保持手离抓取区域**；物品堆叠高度必须与固定打点一致
- ⚠️ 先执行 `run_until_sensor` 再放物品（先清沿后挡沿），否则物品已在传感器位会直接超时
- ⚠️ 急停是安全机制，**验证后必须 reset_emergency 复位**，避免后续任务被拒绝造成困惑
- ⚠️ 实验结束后 `bash scripts/stop_eai_factory.sh` 清理进程，防止残留

### 7.8 实验总结

**完成成果**: 完成流水线电机启停、光电定点停（含防抖/超时）、急停置位/复位、palletize 先送料后抓取编排及语音联动码垛的全流程验证，并按 docs/10 完成测试用例验收。

**技能收获**:
- 掌握复用底盘电机驱动流水线（set_motor 速度发布/置 0 即停）与 GPIO sysfs 导出流程
- 掌握 run_until_sensor 清沿/挡沿/防抖/超时四段式定点停与状态机转换
- 掌握 N2 调度器跨节点编排（订阅 conveyor/state 同步后再触发 grasp）与固定点位抓取八步动作序列

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 流水线不转 | GPIO 未导出或电机通道接错 | `sudo bash scripts/setup_conveyor_gpio.sh`；确认 `conveyor.motor_id=1`（yaml L102） |
| run_until_sensor 立即 timeout | 物品已停在光电位（先清沿逻辑不满足） | 先移开物品再触发；或先 `run` 手动清位再 `stop` |
| 码垛触发后只送料不抓取 | 光电被物品稳定遮挡但 state 非 sensor_blocked（或防抖不满足） | 确认 `sensor_blocked_level=0`、`debounce_reads=3`；观察 `/eai_factory/conveyor/photo` 是否 `true` |
| 抓取位置偏 | 物品堆叠高度/位置与打点不一致 | 重新打点更新 `grasp.tasks.palletize.observe_pose`（yaml L89） |
| 服务拒绝 "emergency active" | 上次急停未复位 | `ros2 service call /eai_factory/conveyor/reset_emergency std_srvs/srv/Trigger` |

### 7.9 实验报告要求

**思考题**:
1. 为什么 `run_until_sensor` 要先等待"清沿"再等待"挡沿"？如果物品一开始就在光电传感器处会发生什么？
2. 急停采用"置位保持、显式复位"而非"急停后自动恢复"，请从安全工程角度分析该设计的好处。
3. palletize 编排中，调度器为何通过订阅 `/eai_factory/conveyor/state` 同步而不是直接 sleep 固定时长？若抓取服务未就绪会发生什么（结合 `_pending_task` 重试机制）？

**评分标准**: 实验报告满分 100 分 = 实验目的与原理阐述 15 分 + 操作步骤完整性（含命令与日志截图）30 分 + 四步验证现象记录（单测/码垛/急停/语音）35 分 + 测试用例验收表（TC1-TC9）10 分 + 思考题与问题分析 10 分。
