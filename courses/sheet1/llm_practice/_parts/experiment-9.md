# 实验9：具身智能工厂--全功能快速验证（8h）

### 9.1 关联知识点

- 6.3.1 Launch 一键启动（bringup→arm_controller→peripherals→eai_factory 节点分阶段启动；前置依赖 1.2.3, 2.2.1）
- 6.3.2 7 开关模块化（start_base/viz/voice/vision/grasp/conveyor/radar；前置依赖 6.3.1）
- 6.3.3 全链路闭环与停止清理（语音→意图→任务→执行→完成播报闭环 + `stop_eai_factory.sh` 清理；前置依赖 3.2.1, 4.2.2, 5.2.2, 6.2.1）

### 9.2 实验目标

1. 掌握 `ros2 launch eai_factory eai_factory.launch.py` 一键启动机制与 bringup→arm_controller→peripherals→eai_factory 节点的分阶段启动顺序 — 原理理解
2. 掌握 7 个模块开关（start_base/viz/voice/vision/grasp/conveyor/radar）的语义，能按需裁剪启动组合节省内存 — 独立完成
3. 掌握装货/分拣/码垛/急停四大全链路闭环验证方法（语音触发 + 服务触发双通道），理解"完成播报"的闭环反馈 — 独立完成
4. 掌握 `stop_eai_factory.sh` 停止清理与残留排查方法，能独立完成系统级快速验证与故障定位 — 迁移应用

### 9.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱 B2 / 机器人小车 C1（麦克纳姆底盘 + 5DOF 机械臂 + 夹爪 + 激光雷达 + RGB-D 深度相机 + 语音阵列 + 流水线电机 M1 + 光电传感器 GPIO17 + AprilTag 标签 id=3） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10；voice/vision/grasp/conveyor 节点经 `/home/iflytek/ros2_venv/bin/python3` 直接跑 .py（sherpa_onnx、cv2 4.11 仅在 venv）；scheduler/safety 用 console_scripts 入口点 |
| 核心库 | rclpy、std_srvs、std_msgs、sensor_msgs、car1_base_driver_msgs；venv 内 sherpa_onnx / opencv / flask_server（LLM 服务端口 8080） |
| 依赖 | LLM 模型（`Qwen3.5-0.8B_w4a16_g128_rk3576.rkllm`，`llm_server.auto_start=true` 自动拉起）；`scripts/stop_eai_factory.sh`（停止清理） |

### 9.4 实验难度

- 难度: ⭐⭐⭐（综合性）
- 重点: 一键启动编排与 7 开关裁剪；装货/分拣/码垛/急停四链路闭环验证（"任务完成"播报反馈）
- 难点: 多节点分阶段启动的时序观察（venv 进程 vs 入口点节点）；停止清理与残留进程故障排查（flask_server/8080 端口等）

### 9.5 实验现象

**快速验证流程**：

1. 全功能启动：
   ```bash
   source /opt/ros/humble/setup.bash
   source /home/iflytek/ros2_ws/install/setup.bash
   ros2 launch eai_factory eai_factory.launch.py
   ```
2. 装货验证（二选一）：
   ```bash
   # 语音：小飞小飞 → 装货
   ros2 service call /eai_factory/start_load std_srvs/srv/Trigger   # 服务方式
   ```
   观察：视觉检测→抓取→放置→播报"装货完成"
3. 分拣/码垛验证（依次语音"分拣""码垛"，或服务方式），观察完整链路与"分拣完成""码垛完成"播报。
4. 急停验证：任务中在雷达正前方放障碍 ≥0.5s → 观察释放力矩→解除→回 work。
5. 停止清理：
   ```bash
   bash scripts/stop_eai_factory.sh
   ```
   确认输出"已全部清理干净"。

**预期效果描述**：

- 启动日志按序出现：bringup（base_driver/controller）→ arm_controller → peripherals（雷达/相机）→ eai_factory 节点（voice/scheduler/safety/vision/grasp/conveyor），约 5s 后 rqt 调试画面打开
- 语音"装货/分拣/码垛"→ 对应任务执行 → 播报"装货完成/分拣完成/码垛完成"（`/eai_factory/speak` 闭环）
- 任务中触发雷达危险：grasp 停止、流水线停止、舵机力矩释放；移开障碍后恢复力矩并回 work
- `stop_eai_factory.sh` 输出"已全部清理干净"，`ps` 无残留进程、8080 端口空闲

### 9.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：全功能一键启动] --> B[步骤2：装货链路验证]
    B --> C[步骤3：分拣链路验证]
    C --> D[步骤4：码垛链路验证]
    D --> E[步骤5：急停联动验证]
    E --> F[步骤6：停止清理与故障排查]
    F --> G[完成]
```

---

#### 步骤1：全功能一键启动（60min）

**知识点讲解**：

**Launch 一键启动与 7 开关模块化（6.3.1 + 6.3.2）**

- **原理**：`ros2 launch eai_factory eai_factory.launch.py` 一条命令拉起全系统，分两类启动源：**底层系统**（`car1_bringup` 底盘+控制器、`car1_arm_controller` 机械臂、`car1_peripherals` 雷达+相机，条件 `start_base:=true` 时经 IncludeLaunchDescription 包含）；**eai_factory 节点**——voice/vision/grasp/conveyor 四个节点因依赖 venv 的 sherpa_onnx、cv2 4.11、car1_base_driver_msgs，用 `ExecuteProcess` 以 `/home/iflytek/ros2_venv/bin/python3` 直接跑 .py；scheduler/safety 用标准 `Node` 入口点。另有 `start_viz:=true` 时 5s 后拉起 `rqt_image_view` 调试画面。**7 开关** `start_base/start_viz/start_voice/start_vision/start_grasp/start_conveyor/start_radar`（默认全 true，radar 默认 false）使各模块可独立裁剪：`start_voice:=false` 省 ~500MB LLM 内存、`start_radar:=true` 配合 `start_base:=false` 可只测雷达安全。
- **源码对应**：`launch/eai_factory.launch.py` L73-86（7 个 DeclareLaunchArgument 开关）、L89-91（base 三包 IncludeLaunchDescription）、L94（lidar 独立拉）、L99-146（voice/scheduler/safety/vision/grasp/conveyor 节点编排）、L149-160（rqt_image_view 延时 5s）；`README.md` L52-80（常用命令清单）
  ```python
  DeclareLaunchArgument('start_voice', default_value='true',
      description='Start voice node (LLM ~500MB). Set false to save memory...'),
  ...
  DeclareLaunchArgument('start_radar', default_value='false',
      description='Start lidar only (independent of start_base; low-memory testing of safety node)'),
  ```
- **公式/配图说明**（重难点）：
  ```mermaid
  graph LR
      A[launch 入口] --> B[start_base=true: bringup + arm_controller + peripherals]
      A --> C[start_voice: venv python voice_node.py]
      A --> D[scheduler Node 入口点]
      A --> E[safety Node 入口点]
      A --> F[start_vision: venv vision_node.py]
      A --> G[start_grasp: venv grasp_node.py]
      A --> H[start_conveyor: venv conveyor_node.py]
      A --> I[start_viz: 5s 后 rqt_image_view]
  ```

**操作步骤**：

1. 检查环境与依赖（LLM 模型路径存在、venv 就绪）：
   ```bash
   ls /home/iflytek/models/rkllm/Qwen3.5-0.8B_w4a16_g128_rk3576.rkllm
   /home/iflytek/ros2_venv/bin/python3 --version    # 3.10
   ```
2. 全功能启动：
   ```bash
   ros2 launch eai_factory eai_factory.launch.py
   ```
3. 观察分阶段启动日志：bringup 底层 → arm_controller → peripherals → voice（LLM 加载约几十秒）→ scheduler/safety/vision/grasp/conveyor → 约 5s 后 rqt_image_view。
4. 确认节点齐全：
   ```bash
   ros2 node list | grep eai_factory
   ros2 service list | grep -E "start_(load|sort|palletize)"
   ros2 topic echo /eai_factory/safety/status     # 应看到 safe
   ```
5. 练习开关裁剪（省内存演示，完成后 Ctrl+C）：
   ```bash
   ros2 launch eai_factory eai_factory.launch.py start_voice:=false start_viz:=false
   ```

**易错点**：

- ⚠️ 启动失败报 ament 找不到包 → **解决**：先 `source /opt/ros/humble/setup.bash && source /home/iflytek/ros2_ws/install/setup.bash`；确认已 `colcon build --packages-select eai_factory`
- ⚠️ 语音节点启动慢（LLM 加载）误以为卡死 → **解决**：`start_voice:=false` 可跳过；或等待 8080 端口就绪 `ss -tlnp | grep 8080`
- ⚠️ 无显示器环境 rqt 报错 → **解决**：`start_viz:=false` 关闭调试画面

---

#### 步骤2：装货链路验证（90min）

**知识点讲解**：

**装货：视觉抓取全链路（6.3.3 + 4.2.3）**

- **原理**：装货是**视觉自适应抓取**（`grasp.tasks.load.vision=true`）：N-vision 检测 AprilTag（tag id=3，tag36h11）发布目标位姿 → N-grasp 观察位 `[0.16, 0.0, 0.27, 2.5307]` 到位 → 视觉目标经 camera→base_link TF 变换 → 带 `pick_offset` 补偿抓取 → 放置位 `[0.05675, -0.13166, 0.20386, 2.93322]` 放下 → 回 work。任务完成后 N-grasp 发布 `load|done`，N2 调度器 `_grasp_status_cb` 映射为"装货完成"并发布到 `/eai_factory/speak` 由 TTS 播报，形成"语音→意图→任务→执行→完成播报"闭环。语音"装货"与服务 `/eai_factory/start_load` 两路等价（同走 `_run_task('load')`）。
- **源码对应**：`eai_factory/scheduler_node.py` L214-218（`/eai_factory/start_load` 服务）、L195-210（`_grasp_status_cb`：`load→装货完成` 播报）；`eai_factory/grasp_node.py` L53-55（load 任务点位参数）、L246-306（`start_grasp` 视觉路径）；`config/eai_factory.yaml` L79-82（load 段点位）、L51（`load_done: "装货完成"`）、L110-113（intents 映射 load→`/eai_factory/start_load`）
  ```python
  def _start_load_cb(self, request, response):
      self._run_task('load')
      response.success = True
      response.message = 'load task triggered'
      return response
  ```
- **公式/配图说明**（重难点）：视觉抓取链路 `AprilTag 检测 → PnP 位姿(相机系) → TF camera_depth_optical_frame→base_link → pick_offset 补偿 → pick/place`

**操作步骤**：

1. 全功能启动（步骤1 已起；若已停止重新启动）。
2. 在装货区放置贴有 AprilTag(id=3) 的货物，观察 rqt 调试画面中检测框。
3. 触发装货（两路任选其一）：
   ```bash
   # 语音路：小飞小飞 → 装货
   # 服务路：
   ros2 service call /eai_factory/start_load std_srvs/srv/Trigger
   ```
4. 观察完整链路：机械臂移观察位 → 检测到目标 → 抓取（夹爪闭合）→ 抬升 → 移放置位 → 放下 → 回 work → 播报"装货完成"（终端可见 `[SCHEDULER] task load done — announce "装货完成"`）。
5. 记录 grasp status `load|done`。

**易错点**：

- ⚠️ 检测不到 AprilTag（光照/距离/角度） → **解决**：确认标签在相机视野内、tag id=3、`/eai_factory/vision/detected` 话题 `data: true`；用 rqt 调试画面校准
- ⚠️ 抓取偏移偏大（手眼标定误差） → **解决**：`grasp.pick_offset_*`（yaml L75-77）现场微调，如向前补偿 15mm/向上 23mm
- ⚠️ 视觉路径需要 camera 已起（`start_base:=true` 含 peripherals 相机） → **解决**：确认 `/ascamera_hp60c/camera_publisher/rgb0/image` 话题存在

---

#### 步骤3：分拣链路验证（90min）

**知识点讲解**：

**分拣：固定点位抓取（6.3.3 + 5.1.3）**

- **原理**：分拣是**固定点位抓取**（`grasp.tasks.sort.vision=false`）：不依赖视觉，取料点（`observe_pose=[0.0622, -0.1158, 0.1951, 3.0371]`，手动打点）即抓取点，放置点 `[0.1434, -0.1296, 0.2075, 2.7283]`。动作序列为固定抓取八步：**提前开爪→直接到位→闭爪→抬升(0.03)→移放置位→开爪投放→再抬升(0.05)→回 work**。与装货不同，分拣无需相机与 TF，速度更快、对环境依赖更低。任务完成同样经 grasp status → 调度器播报"分拣完成"。
- **源码对应**：`eai_factory/scheduler_node.py` L220-224（`/eai_factory/start_sort` 服务）、L203-204（`sort→分拣完成` 播报映射）；`eai_factory/grasp_node.py` L56-58（sort 点位参数）、L413-485（`_do_fixed_grasp` 八步序列）；`config/eai_factory.yaml` L83-86（sort 段点位）
  ```python
  # grasp_node._do_fixed_grasp 关键序列
  if not self._call_gripper(True):            # ① 提前开爪
      return
  self._move_to_pose(ox, oy, oz, opitch)      # ② 直接到位
  ...
  if not self._call_gripper(False):           # ③ 闭爪抓取
  self._move_to_pose(ox, oy, oz + self.lift_height, opitch)   # ④ 抬升
  self._move_to_pose(px, py, pz, ppitch)      # ⑤ 移放置位
  if not self._call_gripper(True):            # ⑥ 开爪投放
  self._move_to_pose(px, py, pz + self.place_lift, ppitch)    # ⑦ 抬 5cm
  self._call_service(self.work_client, 'go_work')             # ⑧ 回 work
  ```
- **公式/配图说明**（重难点）：固定抓取时序 `开爪→到位→闭爪→抬0.03→放置→开爪→抬0.05→work`；放置后抬升 `place_lift=0.05` 是防拖拽回刮关键

**操作步骤**：

1. 在分拣取料点摆放待分拣物品（与打点位置/高度一致）。
2. 触发分拣：
   ```bash
   ros2 service call /eai_factory/start_sort std_srvs/srv/Trigger
   # 或语音：小飞小飞 → 分拣
   ```
3. 观察：提前开爪 → 到位 → 闭爪 → 抬升 → 放置 → 抬 5cm → 回 work → 播报"分拣完成"。
4. 连续执行 2 次，验证固定点位稳定性。

**易错点**：

- ⚠️ 物品摆放偏离打点位置 → 抓偏/漏抓 → **解决**：物品必须与 `sort.observe_pose` 打点位置一致（yaml L85），或用"先放货再打点"方式校准
- ⚠️ 固定抓取开爪太晚（到位才开） → 夹爪卡住物品边缘 → **解决**：确认"提前开爪"在移动前完成（`_call_gripper(True)` 在 `_move_to_pose` 之前，grasp_node.py L435-441）

---

#### 步骤4：码垛链路验证（90min）

**知识点讲解**：

**码垛：送料+抓取编排（6.3.3 + 1.3.2 + 5.2.2）**

- **原理**：码垛是**跨节点编排**任务：N2 调度器先调 N-conveyor `run_until_sensor` 送料（流水线电机 M1 运转），物品随皮带移动至光电传感器（GPIO17）遮挡定点停（`sensor_blocked`，防抖 3 次确认），调度器收到该状态后再触发 N-grasp 的 palletize 固定点位抓取（`observe_pose=[0.145, 0.0027, 0.185, 3.1381]` 取料、`place_pose=[0.0608, 0.1345, 0.2051, 2.6461]` 放置），完成后播报"码垛完成"。这是本课程**最完整的任务链路**，融合了流水线、光电、固定抓取、跨节点状态同步四大知识点。
- **源码对应**：`eai_factory/scheduler_node.py` L226-230（`/eai_factory/start_palletize` 服务）、L98-110（`_start_palletize_sequence` 先送料）、L121-127（`_conveyor_state_cb` 收到 `sensor_blocked` 触发抓取）、L203-204（`palletize→码垛完成`）；`eai_factory/grasp_node.py` L59-61（palletize 点位）、L273-278（固定抓取路径）；`config/eai_factory.yaml` L87-90（palletize 段）、L35-36（"码垛"等意图提示词）、L53（`palletize_done: "码垛完成"`）
  ```python
  def _start_palletize_sequence(self):
      ...
      self._awaiting_sensor = True
      future = self.conveyor_client.call_async(Trigger.Request())  # run_until_sensor 送料
  ```
- **公式/配图说明**（重难点）：
  ```mermaid
  graph LR
      A[语音码垛/服务触发] --> B[run_until_sensor 送料]
      B --> C[光电遮挡→sensor_blocked]
      C --> D[grasp palletize 固定抓取]
      D --> E[palletize|done]
      E --> F[TTS: 码垛完成]
  ```

**操作步骤**：

1. 把待码垛物品放流水线起始端备用。
2. 触发码垛：
   ```bash
   ros2 service call /eai_factory/start_palletize std_srvs/srv/Trigger
   # 或语音：小飞小飞 → 码垛（触发后立即把物品放到流水线起始端）
   ```
3. 观察：送料（`running`）→ 光电遮挡 → `sensor_blocked` → 机械臂开爪到位抓取 → 抬升 → 放置 → 抬 5cm → 回 work → 播报"码垛完成"。
4. 记录 `/eai_factory/grasp/status` 出现 `palletize|done`。

**易错点**：

- ⚠️ 语音码垛时物品没及时放上流水线 → 送料空跑 30s `timeout` → **解决**：听到"好的"后立即放物品（run_until_sensor 先等清沿再等挡沿）
- ⚠️ 码垛堆叠高度变化导致固定点位抓不到 → **解决**：保持取料点物品与打点高度一致，堆码高度超限时重新打点（yaml L89）

---

#### 步骤5：急停联动验证（80min）

**知识点讲解**：

**安全联锁与打断分层（6.2.1 + 6.2.2 + 6.2.3）**

- **原理**：任务执行中（机械臂运动/流水线送料）若激光雷达检测到前方 60° 扇区内 <20cm 障碍持续 0.5s，N3 发布 `danger=true` 并**释放 6 舵机力矩**（机械臂变软）；N-grasp 收到后立即 `emergency_stop` 中止抓取、N-conveyor 停带并停臂、N2 调度器暂停任务；障碍移开后 N3 发布 `danger=false`、`status=recover`，恢复力矩并调 `go_work` 回 work。**打断分层：雷达打断 > 语音打断**——危险时绝不强行运动，保证人机安全。恢复后任务需人工重新触发（安全策略）。
- **源码对应**：`eai_factory/safety_node.py` L163-190（`_enter_danger`/`_exit_danger`）、L105-120（`_set_arm_torque`）、L122-128（`_go_work`）；`eai_factory/grasp_node.py` L188-202（`_danger_cb` 停止抓取）；`eai_factory/conveyor_node.py` L259-273（`_danger_cb` 停带+停臂）；`eai_factory/scheduler_node.py` L187-193（`_danger_cb` 任务暂停）；`config/eai_factory.yaml` L93-98（safety 参数）
  ```python
  # safety_node._enter_danger
  self._danger = True
  self.danger_pub.publish(Bool(data=True))
  status.data = 'danger'
  self.status_pub.publish(status)
  self._set_arm_torque(False)     # 释放力矩，机械臂变软
  ```
- **公式/配图说明**（重难点）：危险时序 `放障碍 → 0.5s 持续 → danger(释放力矩) → 移开 → recover(恢复力矩+go_work)`；分层表：雷达危险 > 语音打断

**操作步骤**：

1. 全功能启动状态下，触发一个任务（如分拣或码垛），在任务执行中于**雷达正前方** 20cm 内放障碍 ≥0.5s。
2. 观察：grasp 日志 `SAFETY DANGER — stopping grasp`、conveyor 日志 `safety danger detected — belt + arm stopped`、`/car1_base_driver/bus_servo/set_state` 出现 `enable_torque: [0,0,0,0,0,0]`；机械臂变软。
3. 移开障碍：观察 `status=recover`、`enable_torque: [1,1,1,1,1,1]`、机械臂 `go_work` 回 work。
4. 再次触发任务验证恢复后可正常工作；尝试"任务中语音打断"与"任务中雷达危险"同时发生，观察雷达优先（grasp 停止动作而非回 work 继续）。

**易错点**：

- ⚠️ 障碍放错位置（非雷达正前方）不触发 → **解决**：对准雷达 0° 中心 ±30° 扇区（yaml L95-96）
- ⚠️ 危险解除后误以为任务自动继续 → **解决**：安全策略为"人工重新触发"，恢复后重新下达指令
- ⚠️ 释放力矩后机械臂下垂撞击周边 → **解决**：触发前确保机械臂处于安全位、下方无遮挡物

---

#### 步骤6：停止清理与故障排查（70min）

**知识点讲解**：

**停止清理与防残留（6.3.3）**

- **原理**：`ros2 launch` 正常 Ctrl+C 会关闭其管理的子进程，但**异常终止/后台启动**可能残留各节点、底层系统与 LLM 服务（flask_server 端口 8080），残留进程会继续占用总线舵机/串口/麦克风，导致下次启动失败。`stop_eai_factory.sh` 兜底清理：按名 pkill launch 主进程 → 5 个 venv 节点 + 2 个入口点节点 → flask_server → 底层系统（base_driver/controller/robot_state_publisher/joint_state_publisher/arm_controller/ascamera/rqt）→ 兜底清 8080 端口 → 最后自查残留输出"已全部清理干净"。故障排查则结合 `ros2 node list / ros2 topic list / ros2 service list` 与日志逐层定位。
- **源码对应**：`scripts/stop_eai_factory.sh` L18（杀 launch）、L21-26（杀 7 个 eai_factory 节点）、L29（杀 flask_server）、L33-42（杀底层系统）、L45-50（兜底清 8080）、L54-60（残留自查）；`README.md` L79-80（停止命令）
  ```bash
  for f in voice_node vision_node grasp_node conveyor_node; do
      pkill -9 -f "$f.py" ...
  done
  ...
  if ss -tlnp 2>/dev/null | grep -q ":8080 "; then ... kill -9 "$PID" ...
  ```
- **公式/配图说明**（重难点）：排查顺序 `进程是否残留(stop 脚本自查) → 话题/服务是否在(node list) → 日志定位(各节点 screen 输出)`；资源占用表：语音/LLM ~500MB、rqt GUI 依赖显示器

**操作步骤**：

1. 结束本轮验证（Ctrl+C 或直接执行停止脚本）：
   ```bash
   cd ~/ros2_ws/src/xflz_eai_car1/app/eai_factory
   bash scripts/stop_eai_factory.sh
   ```
2. 观察输出：各进程"已终止"或"无进程"，结尾显示"已全部清理干净"（或列出残留）。
3. 若有残留，手动清理：
   ```bash
   ps aux | grep -E "voice_node|flask_server|eai_factory" | grep -v grep
   pkill -9 -f "flask_server.py"
   ss -tlnp | grep 8080
   ```
4. 验证清理结果：`ros2 node list` 无 eai_factory 节点、`ss -tlnp | grep 8080` 无输出。
5. 故障排查演练：人为制造一个故障（如 `start_voice:=false` 启动后调语音指令），用 `ros2 node list` / 话题 / 日志定位原因并记录排查过程。

**易错点**：

- ⚠️ 只 Ctrl+C 不跑停止脚本 → 残留 flask_server/8080 占用 → **解决**：每次实验结束统一执行 `bash scripts/stop_eai_factory.sh`
- ⚠️ 停止脚本误杀同名前缀的其他进程 → **解决**：脚本按精确文件名匹配（`voice_node.py` 等），运行前确认无同名业务进程
- ⚠️ 下次启动报"地址被占用"（串口/麦克风） → **解决**：八成是上次残留，执行停止脚本清干净再启动

### 9.7 注意事项

- ⚠️ 全功能启动会同时拉起语音（LLM ~500MB）、视觉、机械臂、流水线、雷达，**确认内存/供电充足**，必要时用开关裁剪（`start_voice:=false` 等）
- ⚠️ 实机抓取全程**手离抓取区域**；急停验证前确认机械臂处于安全位，释放力矩后防止下垂碰撞
- ⚠️ 雷达危险触发/解除时手不要扶机械臂，让其自主回 work
- ⚠️ 码垛/分拣为固定点位抓取，物品摆放必须与打点一致；堆叠高度变化需重新打点
- ⚠️ 实验结束**必须** `bash scripts/stop_eai_factory.sh` 清理，防止残留进程占用总线舵机/串口/8080

### 9.8 实验总结

**完成成果**: 完成一键启动与 7 开关裁剪演示、装货/分拣/码垛三大任务链路验证（语音+服务双通道）、任务中雷达急停联动验证，以及停止清理与残留排查，达到"一条命令启动、全链路闭环、干净停止"的系统级快速验证目标。

**技能收获**:
- 掌握 launch 一键启动编排（venv ExecuteProcess + Node 入口点混编）与 7 开关模块化裁剪
- 掌握装货（视觉抓取）/分拣（固定抓取）/码垛（送料+抓取编排）三条任务链路与完成播报闭环
- 掌握安全联锁（雷达危险→力矩释放→解除恢复）与停止清理/残留排查方法

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 启动报 ament/找不到包 | 未 source 环境或未 build | `source /opt/ros/humble/setup.bash` + `source /home/iflytek/ros2_ws/install/setup.bash`；`colcon build --packages-select eai_factory` |
| 语音无响应 | LLM 服务未就绪（8080）或麦克风被残留进程占用 | 等 `ss -tlnp \| grep 8080` 出现；先 `bash scripts/stop_eai_factory.sh` 清残留 |
| 视觉装货检测不到标签 | 光照/距离/角度或 tag id 不符 | 用 rqt 调试画面校准；确认 `tag_id: 3`（yaml L58） |
| 分拣/码垛抓偏 | 物品位置偏离打点 | 重摆物品或重新打点更新 observe_pose（yaml L85/L89） |
| 任务中危险不触发 | 障碍不在雷达正前方 ±30° | 对准雷达 0° 中心放置（yaml L95-96） |
| 下次启动串口/麦克风被占用 | 上次残留进程未清理 | `bash scripts/stop_eai_factory.sh` 后再启动 |

### 9.9 实验报告要求

**思考题**:
1. 7 个开关中 `start_radar` 默认 `false`、`start_base` 默认 `true`，请分析这两个默认值的设计意图（低内存测试 vs 完整系统）。
2. 为什么 voice/vision/grasp/conveyor 用 venv 的 python3 直接跑 .py，而 scheduler/safety 用 console_scripts 入口点？从依赖角度分析。
3. 全链路闭环中"完成播报"由哪个节点、基于什么信号触发？若 grasp 失败（`task|failed`）系统如何表现？
4. 停止脚本为何需要按文件名 pkill 与端口兜底清 8080 两道手段？残留进程会造成哪些具体危害？

**评分标准**: 实验报告满分 100 分 = 实验目的与原理阐述 15 分 + 操作步骤完整性（含命令与日志截图）30 分 + 四链路验证现象记录（启动/装货/分拣码垛/急停）35 分 + 停止清理与残留排查记录 10 分 + 思考题与问题分析 10 分。
