# 实验8：具身智能工厂--危险急停集成测试（4h）

### 8.1 关联知识点

- 6.1.1 雷达扇区检测（激光雷达前方 60° 扇区(±30°)，danger_dist=20cm 判定危险；前置依赖 1.1.3）
- 6.1.2 危险判定（障碍持续 0.5s(persist_time) 才判危险，防瞬时误报；前置依赖 6.1.1）
- 6.1.3 力矩释放（危险时通过 `/car1_base_driver/bus_servo/set_state` 释放 6 舵机力矩；前置依赖 6.1.2）
- 6.2.1 恢复回 work（危险解除→恢复力矩→`/arm_controller/go_work` 回 work；前置依赖 6.1.3）
- 6.2.2 打断分层（雷达危险打断 > 语音打断，危险时不强行运动；前置依赖 3.2.3, 6.1.3）

### 8.2 实验目标

1. 理解激光雷达危险检测原理：前方 60° 扇区（±30°）、20cm 距离阈值、0.5s 持续判定 — 原理理解
2. 掌握危险触发时通过总线舵机 `set_state` 释放 6 舵机力矩的机制（机械臂变软、可手推）— 独立完成
3. 掌握危险解除后的恢复流程（恢复力矩 + `go_work` 回 work），理解"雷达打断 > 语音打断"的分层设计 — 理解
4. 掌握 N-grasp / N-conveyor 订阅 danger 立即停止动作的联动机制，能独立完成安全联锁集成测试并按 `docs/11_安全测试用例.md` 验收 — 迁移应用

### 8.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱 B2 / 机器人小车 C1（5DOF 机械臂 + 夹爪）；激光雷达（`/dev/lidar` → ttyUSB1，发布 `/scan` 约 10Hz）；障碍物（书本/纸盒，安全测试用） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10；safety / scheduler 节点用 console_scripts 入口点运行；grasp / conveyor 经 `/home/iflytek/ros2_venv/bin/python3` 运行 |
| 核心库 | rclpy、sensor_msgs（LaserScan，Best Effort QoS）、std_msgs、car1_base_driver_msgs（SetBusServoState/BusServoState）、std_srvs |
| 依赖 | `car1_base_driver` 在跑（总线舵机力矩释放/恢复真正生效的前提）；`arm_controller` 在跑（`go_work` 回 work 依赖） |

### 8.4 实验难度

- 难度: ⭐⭐⭐（综合性）
- 重点: 扇区检测算法（跨 0° 环绕的扇区判定）+ 持续判定（persist_time 防误报）+ 力矩释放/恢复链路
- 难点: 打断分层（雷达打断 > 语音打断）与 N-grasp / N-conveyor 对 danger 的响应时序；"危险时不强行运动"的安全哲学

### 8.5 实验现象

**快速验证流程**：

1. 低内存只起雷达安全：
   ```bash
   source /opt/ros/humble/setup.bash
   source /home/iflytek/ros2_ws/install/setup.bash
   ros2 launch eai_factory eai_factory.launch.py \
     start_base:=false start_voice:=false start_vision:=false start_grasp:=false \
     start_conveyor:=false start_radar:=true
   ```
2. 观察接口：
   ```bash
   ros2 node list
   ros2 topic hz /scan
   ros2 topic echo /eai_factory/safety/status
   ros2 topic echo /eai_factory/safety/danger
   ros2 topic echo /car1_base_driver/bus_servo/set_state
   ```
3. 危险触发：在雷达正前方 **20cm 内**放置障碍物并保持 **0.5s 以上** → 观察 `danger=true`、`status=danger`、6 舵机力矩释放（机械臂变软可手推）
4. 危险解除：移开障碍物 → 观察 `danger=false`、`status=recover`、力矩恢复、机械臂 `go_work` 回 work
5. 任务中急停联动：执行装货/分拣/码垛任务中触发雷达危险 → 观察 N-grasp/conveyor 立即停止动作。

**预期效果描述**：

- `/eai_factory/safety/status`：`safe` → 放障碍 0.5s 后 `danger` → 移开后 `recover`
- `/car1_base_driver/bus_servo/set_state` 出现 `enable_torque: [0,0,0,0,0,0]`（释放）与 `[1,1,1,1,1,1]`（恢复）
- 机械臂：危险时所有关节可被外力推动（力矩释放生效）；恢复后锁死并回 work 姿态
- 任务中触发：grasp 日志 `SAFETY DANGER — stopping grasp`；conveyor 日志 `safety danger detected — belt + arm stopped`

### 8.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：低内存启动雷达安全] --> B[步骤2：危险触发与力矩释放]
    B --> C[步骤3：危险解除与恢复回 work]
    C --> D[步骤4：任务中急停联动]
    D --> E[步骤5：安全测试用例验收]
    E --> F[完成]
```

---

#### 步骤1：低内存启动雷达安全（50min）

**知识点讲解**：

**雷达扇区检测（6.1.1）**

- **原理**：N3 安全节点只订阅激光雷达 `/scan`（LaserScan，Best Effort QoS），**检测基于雷达自身坐标系（laser_link）**，不依赖车身 TF 与机械臂位置关系——障碍必须放在**雷达正前方**。扇区参数：`front_start_deg=-30°`、`front_end_deg=+30°`（共 60°，以雷达 0° 为中心跨 0° 环绕）、`danger_dist=0.20m`。扇区最小距离算法遍历所有扫描点，将角度归一化到 [0, 2π) 后判断是否落在扇区内（含跨 0° 环绕分支），过滤 inf/nan 与 <0.01m 的无效点，取最小距离；`min_range < danger_dist` 即"有障碍接近"。低内存模式 `start_radar:=true` 只拉 `car1_peripherals/lidar.launch.py` 与 safety 节点，不启动底盘/相机（`start_base:=false`），便于安全模块独立调试。
- **源码对应**：`eai_factory/safety_node.py` L41-51（参数声明）、L56-59（`/scan` 订阅 + danger/status 发布）、L78-99（`_get_sector_min_range` 扇区最小距离）、L142-161（`_scan_cb` 扫描回调判定）；`launch/eai_factory.launch.py` L85-86（`start_radar` 默认 false，可开）、L94（`lidar.launch.py` 单独拉起）；`config/eai_factory.yaml` L93-98（safety 段）
  ```python
  for i in range(num_readings):
      angle = angle_min + i * angle_increment
      angle_norm = angle % (2 * math.pi)
      if start_norm <= end_norm:
          in_sector = start_norm <= angle_norm <= end_norm
      else:
          # sector wraps around 0
          in_sector = angle_norm >= start_norm or angle_norm <= end_norm
  ```
- **公式/配图说明**（重难点）：
  - 扇区定义：`θ ∈ [θ_start, θ_end]`，θ_start=-30°、θ_end=30°；跨 0° 时用"或"判定（`angle_norm >= start_norm or angle_norm <= end_norm`）
  - 危险判据：`min_range(θ∈扇区) < danger_dist(0.20m)`
  - 启动组合表：`start_base:=false` + `start_radar:=true` → 只起雷达 + safety（低内存）；完整联动时保持 `start_base:=true`

**操作步骤**：

1. 关闭机器人电源前先确认雷达 USB 已接（ttyUSB1），上电。
2. 低内存启动：
   ```bash
   ros2 launch eai_factory eai_factory.launch.py \
     start_base:=false start_voice:=false start_vision:=false start_grasp:=false \
     start_conveyor:=false start_radar:=true
   ```
3. 确认接口与数据：
   ```bash
   ros2 node list              # 应看到 eai_factory_safety
   ros2 topic hz /scan         # 约 10Hz
   ros2 topic echo /eai_factory/safety/status    # 初始 safe
   ```
4. 查看启动日志：`eai_factory_safety started | front=-30°..30° dist=0.20m persist=0.5s`

**易错点**：

- ⚠️ 雷达没转/`/scan` 无数据 → `safety` 无任何输出 → **解决**：检查 `/dev/lidar` 设备节点与 ttyUSB1 接线；`start_radar:=true` 会单独拉起 lidar launch
- ⚠️ 障碍放在机械臂前方而非雷达正前方 → 不触发 → **解决**：扇区以**雷达自身坐标系**为基准，障碍对准雷达正前方（0° ±30°）才有效

---

#### 步骤2：危险触发与力矩释放（55min）

**知识点讲解**：

**危险判定与力矩释放（6.1.2 + 6.1.3）**

- **原理**：为避免瞬时误报（如飞过的纸屑、扫过的手），危险判定加入**持续计时**：`_scan_cb` 中若 `obstacle_close` 为真，记录 `_danger_since`（首次检测时间），仅当 `now - _danger_since >= persist_time(0.5s)` 才进入危险状态 `_enter_danger()`；障碍消失则清零计时。进入危险时在**同一个 scan 回调内直接发布** `/eai_factory/safety/danger=true`、`/eai_factory/safety/status=danger`，并立即通过 `/car1_base_driver/bus_servo/set_state` 发布 `enable_torque=[0]*6`（ID 0-5：5 个关节 + 1 个夹爪）**释放全部总线舵机力矩**——机械臂变软，可被外力推离，避免与操作者"较劲"造成伤害。释放走"一次 DDS 发布、无服务往返"，雷达 10Hz 最坏 100ms 检测、舵机释放约 150-220ms，响应最快。
- **源码对应**：`eai_factory/safety_node.py` L150-157（`obstacle_close` + persist 计时）、L163-177（`_enter_danger` 发 danger + status + 释放力矩）、L105-120（`_set_arm_torque` 发布 set_state）、L34（`ARM_SERVO_IDS = list(range(6))`）；`docs/11_安全测试用例.md` L40-56（TS1 扇区检测、TS2 力矩释放）
  ```python
  if obstacle_close:
      if self._danger_since is None:
          self._danger_since = now
      if now - self._danger_since >= self.persist_time:
          self._enter_danger()
  ```
  ```python
  s.target_id = list(ARM_SERVO_IDS)
  s.enable_torque = [int(enabled)] * len(ARM_SERVO_IDS)
  msg.state = [s]
  msg.duration = 0.2
  ```
- **公式/配图说明**（重难点）：
  - 危险判定时序：`检测到障碍(t0) → 持续 ≥0.5s(t0+0.5) → 进入 danger`；中途移开 → 计时清零
  - 力矩释放语义：`enable_torque=0` → 舵机输出关闭（0x0B）；`enable_torque=1` → 恢复使能（0x0C）

**操作步骤**：

1. 将实验箱切到**完整模式**（本步骤需 base_driver 驱动总线舵机）：Ctrl+C 停掉低内存模式，改用完整启动：
   ```bash
   ros2 launch eai_factory eai_factory.launch.py \
     start_voice:=false start_vision:=false start_grasp:=false start_viz:=false
   ```
2. 确认机械臂处于**安全位置**（远离雷达正前方扇区，如 work 姿态）后，在雷达正前方 20cm 内放障碍物并保持 ≥0.5s：
   ```bash
   ros2 topic echo /eai_factory/safety/danger
   ros2 topic echo /eai_factory/safety/status
   ros2 topic echo /car1_base_driver/bus_servo/set_state
   ```
3. 观察：`danger: true`、`status: danger`、`enable_torque: [0,0,0,0,0,0]`、日志 `DANGER: obstacle 0.20m in front sector`。
4. 用手轻轻推机械臂各关节，确认**可被外力推动**（释放生效）。

**易错点**：

- ⚠️ 障碍物放得太近（<10cm 盲区）或角度超出 ±30° → 不触发 → **解决**：障碍放在雷达正前方 10-20cm，保持稳定
- ⚠️ 机械臂在危险触发瞬间仍保持原姿态被"硬掰" → **解决**：触发前确认机械臂处于安全位置；释放后先观察再触碰
- ⚠️ 只触发 <0.5s → 不判危险（误报过滤） → **解决**：保持障碍 ≥0.5s 观察危险状态变化

---

#### 步骤3：危险解除与恢复回 work（50min）

**知识点讲解**：

**危险解除恢复流程（6.2.1）**

- **原理**：障碍移开后，`_scan_cb` 中 `obstacle_close` 为假，清空 `_danger_since` 计时并调用 `_exit_danger()`：发布 `danger=false`、`status=recover`，**恢复 6 舵机力矩**（`enable_torque=[1]*6`），再调用 `/arm_controller/go_work` 服务让机械臂**回到 work 安全姿态**（fire-and-forget 异步调用）。恢复后机械臂关节锁死、无法手推。该流程是"安全联锁闭环"的关键：危险解除后系统能自行复位到安全位，而不是停在危险位置。
- **源码对应**：`eai_factory/safety_node.py` L158-161（清计时 + `_exit_danger`）、L179-190（`_exit_danger` 发 danger=false + status=recover + 恢复力矩 + go_work）、L122-128（`_go_work` 异步调 go_work 服务）；`docs/11_安全测试用例.md` L58-66（TS3 恢复用例）
  ```python
  def _exit_danger(self):
      self._danger = False
      ...
      status.data = 'recover'
      self.status_pub.publish(status)
      self._set_arm_torque(True)     # 恢复力矩
      self._go_work()                # 回 work
  ```
- **公式/配图说明**（重难点）：
  - 状态序列：`safe → danger(释放力矩) → recover(恢复力矩+go_work) → safe`
  - 依赖链：恢复力矩必须先于 `go_work` 执行，否则机械臂无力无法运动

**操作步骤**：

1. 保持步骤2 的监听终端，缓慢移开雷达前方障碍物。
2. 观察：`danger: false`、`status: recover`、`enable_torque: [1,1,1,1,1,1]`、日志 `SAFE: front sector clear — torque restored, go_work`。
3. 观察机械臂自动回到 work 姿态，然后尝试用手推关节，确认**已锁死**。
4. 再次放障碍 0.5s → 再移开，验证"触发→解除"循环可重复执行。

**易错点**：

- ⚠️ `go_work` 服务未就绪 → 恢复时只恢复力矩不回 work（日志 warn） → **解决**：保证 `arm_controller` 随 launch 启动；`ros2 service list | grep go_work` 确认
- ⚠️ 危险解除瞬间手扶机械臂 → go_work 过程中阻力 → **解决**：恢复期间手离开机械臂，让其自主回位

---

#### 步骤4：任务中急停联动（50min）

**知识点讲解**：

**打断分层与 danger 响应（6.2.2 + 6.2.3）**

- **原理**：系统打断分两层：**雷达危险打断 > 语音打断**。危险时**不强行运动**（释放力矩让臂软），避免与操作者对抗；N-grasp 订阅 `/eai_factory/safety/danger`，收到 `true` 时立即停止当前抓取动作（调 `/arm_controller/emergency_stop` 中止运动、状态回 idle，恢复后需重新触发任务）；N-conveyor 订阅 danger 后同样急停流水线**并**调 arm emergency_stop 停机械臂；N2 调度器记录任务暂停，恢复后由操作者重新下达指令。实测任务中触发雷达危险：装货/分拣/码垛的抓取序列与流水线送料均会立即停止。
- **源码对应**：`eai_factory/grasp_node.py` L113-114（danger 订阅）、L188-202（`_danger_cb` 停止抓取+状态回 idle）、L532-538（`_stop_arm_action` 调 emergency_stop）；`eai_factory/conveyor_node.py` L94-96（danger 订阅）、L259-273（`_danger_cb` 停带+停臂）、L275-283（`_stop_arm_on_danger`）；`eai_factory/scheduler_node.py` L187-193（`_danger_cb` 任务暂停）；`docs/11_安全测试用例.md` L68-76（TS4 流水线联动）
  ```python
  # grasp_node._danger_cb
  if msg.data:
      self._interrupted = True
      self._grasp_state = 'idle'
      self.get_logger().warn('SAFETY DANGER — stopping grasp')
      self._stop_arm_action()
  ```
- **公式/配图说明**（重难点）：
  ```mermaid
  graph LR
      A[N3 雷达 danger=true] --> B[grasp: emergency_stop 停臂]
      A --> C[conveyor: 停带 + 停臂]
      A --> D[scheduler: 任务暂停]
      B --> E[危险解除后需重新触发任务]
  ```

**操作步骤**：

1. 完整启动（开任务所需模块）：
   ```bash
   ros2 launch eai_factory eai_factory.launch.py start_viz:=false
   ```
2. 触发一个任务（如分拣，用服务方式便于控制）：
   ```bash
   ros2 service call /eai_factory/start_sort std_srvs/srv/Trigger
   ```
3. 在任务执行（机械臂运动或流水线运转）中，于雷达正前方放障碍 ≥0.5s。
4. 观察：grasp 日志 `SAFETY DANGER — stopping grasp`；conveyor 日志 `safety danger detected — belt + arm stopped`；机械臂当前动作中止、`/eai_factory/conveyor/emergency` 话题 `data: true`。
5. 移开障碍，确认恢复（conveyor 回 idle；机械臂恢复由 N3 `go_work` 处理；任务需重新触发）。
6. 分别对装货（`/eai_factory/start_load`）与码垛（`/eai_factory/start_palletize`）重复 2-5 步。

**易错点**：

- ⚠️ 危险触发时机不对（任务已结束才放障碍）→ 观察不到联动 → **解决**：任务执行中（机械臂运动/送料中）触发
- ⚠️ 危险解除后任务不自动继续（符合"人工确认后重新触发"安全策略） → **解决**：恢复后由操作者重新下达指令，不是缺陷
- ⚠️ 抓取中 danger 后 grasp 状态卡 busy → `_danger_cb` 已置 idle，若仍 busy 可调 `/eai_factory/grasp/abort` 复位

---

#### 步骤5：安全测试用例验收（35min）

**知识点讲解**：

**测试用例方法论（6.1.1-6.2.3 综合）**

- **原理**：验收覆盖五类场景：扇区检测发 danger（TS1）、危险释放力矩（TS2）、危险解除恢复（TS3）、流水线联动（TS4）、手动验证释放/恢复（TS5，不依赖雷达直接发 `set_state` 验证驱动 cmd 修复：释放=0x0B、使能=0x0C）。重点验证"检测→释放→恢复"完整闭环与"雷达打断 > 语音打断"分层。
- **源码对应**：`docs/11_安全测试用例.md` L40-47（TS1）、L49-56（TS2）、L58-66（TS3）、L68-76（TS4）、L78-92（TS5 手动验证命令）；`eai_factory/safety_node.py` L105-120（`_set_arm_torque` 释放/恢复共用）
- **公式/配图说明**：TS5 手动命令与 N3 自动路径等价（同一话题同一消息格式），用于不依赖雷达的快速回归

**操作步骤**：

1. 按 `docs/11_安全测试用例.md` 逐条执行 TS1~TS5，记录现象与日志截图。
2. TS5 手动验证（不依赖雷达）：
   ```bash
   # 释放（ID 0-5）
   ros2 topic pub -1 /car1_base_driver/bus_servo/set_state car1_base_driver_msgs/msg/SetBusServoState \
     "{state: [{target_id: [0,1,2,3,4,5], enable_torque: [0,0,0,0,0,0]}], duration: 0.2}"
   # 恢复
   ros2 topic pub -1 /car1_base_driver/bus_servo/set_state car1_base_driver_msgs/msg/SetBusServoState \
     "{state: [{target_id: [0,1,2,3,4,5], enable_torque: [1,1,1,1,1,1]}], duration: 0.2}"
   ```
3. 将 TS1-TS5 结果填入实验报告（现象 + 判断通过/失败）。

**易错点**：

- ⚠️ TS5 手动释放后忘记恢复 → 机械臂保持软连接，后续任务异常 → **解决**：测试完立即恢复 `[1,1,1,1,1,1]`
- ⚠️ 释放/恢复命令的 `target_id` 与 `enable_torque` 数组长度不一致 → 底层驱动映射失败 → **解决**：两数组必须同为 6 元素（见 safety_node.py L113-114 注释）

### 8.7 注意事项

- ⚠️ **务必确认机械臂处于安全位置再释放力矩**（work 姿态或远离雷达扇区），释放后关节可被外力推动，防止坠落/碰撞
- ⚠️ 危险触发/解除时手离开机械臂，让 `go_work` 自主回位；恢复前不要扶臂
- ⚠️ 障碍物对准**雷达正前方**（0° 中心 ±30°），保持 ≥0.5s 才能判危险
- ⚠️ 任务中急停后需人工重新触发任务（安全策略，非缺陷）
- ⚠️ 实验结束用 `bash scripts/stop_eai_factory.sh` 清理进程，避免残留进程占用总线舵机

### 8.8 实验总结

**完成成果**: 完成低内存雷达安全单测、危险触发（扇区检测 + 0.5s 持续判定 + 6 舵机力矩释放）、危险解除（恢复力矩 + go_work 回 work）、任务中急停联动（grasp/conveyor 响应 danger）四大验证，并按 docs/11 完成 TS1-TS5 用例验收。

**技能收获**:
- 掌握激光雷达扇区最小距离算法（含跨 0° 环绕）与 persist_time 防误报判定
- 掌握总线舵机力矩释放/恢复的发布机制（`/car1_base_driver/bus_servo/set_state`）
- 掌握"雷达打断 > 语音打断"分层设计与 N-grasp / N-conveyor 的 danger 订阅联动

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 放障碍不触发 danger | 障碍超出 ±30° 扇区或 <10cm 盲区/持续 <0.5s | 放在雷达正前方 10-20cm 保持 ≥0.5s（yaml L95-98） |
| 机械臂释放后无法手推 | 力矩释放未生效（驱动 cmd 修复缺失） | TS5 手动发 `enable_torque:[0]*6` 验证；确认 board_sdk 释放=0x0B |
| 危险解除后不回 work | `go_work` 服务未就绪 | `ros2 service list \| grep go_work`；保证 arm_controller 在跑 |
| 任务中危险后任务不继续 | 安全策略：人工确认后重新触发 | 恢复后重新调 `/eai_factory/start_xxx` 触发任务 |
| status 一直 safe | safety 节点未启动或 `/scan` 无数据 | 确认 `eai_factory_safety` 在 node list；`ros2 topic hz /scan` |

### 8.9 实验报告要求

**思考题**:
1. 危险判定为什么要加 0.5s 持续计时？去掉它可能出现什么误报场景？
2. 为什么"危险时不强行运动"（释放力矩）比"立即刹车保持姿态"更安全？结合人机协作场景分析。
3. 打断分层为什么"雷达打断 > 语音打断"？若机械臂抓取中同时收到语音打断与雷达危险，应按哪个执行，为什么？

**评分标准**: 实验报告满分 100 分 = 实验目的与原理阐述 15 分 + 操作步骤完整性（含命令与日志截图）30 分 + 四步验证现象记录（低内存检测/危险触发/解除恢复/任务联动）35 分 + 测试用例验收表（TS1-TS5）10 分 + 思考题与问题分析 10 分。
