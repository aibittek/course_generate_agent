## 实验4：机器人语音控制导航抓取综合应用（8h）

> ✅ **源码已核实** 本实验是"智能工厂综合项目"的收官闭环，把实验 1（建图导航）、实验 2（视觉抓取）、实验 3（离线语音大模型）通过 `navigation_grasp_transport.py` 的**任务状态机**串成"语音指令 → 意图识别 → 建图导航 → 视觉抓取 → 运输放置"的一体化流程。任务入口为 `/navigation_grasp_transport/start`（`nav2_params`/`skills.yaml` 中 transport 技能即调用它），一键 launch 见 `navigation_grasp_transport.launch.py`。

### 4.1 关联知识点

本实验对应"智能工厂综合项目"第 4 章"语音控制导航抓取综合应用"，覆盖知识点：

- 4.1.1 任务状态机设计 > 原理 > `State` 枚举（IDLE→SET_INITIAL_POSE→WAIT_LOCALIZATION→NAV_TO_PICK→MOVE_TO_OBSERVE→WAIT_ARM_STABLE→ROTATE_SEARCH→DETECT_AND_GRASP→CALL_PICK→WAIT_GRASP→NAV_TO_PLACE→PLACE_OBJECT→DONE），单状态机调度所有模块
- 4.1.2 回调组与并发 > 原理 > ReentrantCallbackGroup（服务/客户端）与 MutuallyExclusiveCallbackGroup（定时器）+ MultiThreadedExecutor(4线程)
- 4.2.1 原地旋转搜索 > 流程 > `ROTATE_SEARCH` 从 `map→base_footprint` 读航向，对 `search_angles_deg`（±15/30/45°）逐一以 P 控制器转到位、检测红色像素
- 4.2.2 检测→抓取的分拍调用 > 流程 > 发布 `set_pick_target` 后独立进 `CALL_PICK` 再调 pick，保证 arm 回调已消费目标
- 4.2.3 等待与超时管理 > 流程 > localization/detection/grasp/nav 四类超时与 FAILED 兜底、DONE 5s 复位 IDLE
- 4.3.1 语音→任务桥接 > 流程 > 实验 3 的 `start` 意图调用 `/mission_orchestrator/start` → navigation_grasp_transport 的 `~/start`；任务运行中 `Running` 暂停唤醒
- 4.3.2 端到端联调与故障分析 > 综合 > 定位漂移 / 检不到目标 / 抓取失败 的排查方法

### 4.2 实验目标

1. 掌握以状态机为核心的复杂任务编排，理解"事件驱动 + 超时兜底 + 状态隔离" — 原理理解
2. 掌握旋转搜索、深度定位、抓取/放置、导航运输多模块在一个状态机下的协同 — 独立完成
3. 掌握"语音指令 → 意图识别 → 建图导航 → 视觉抓取 → 运输放置"全流程闭环，实现一次完整抓取任务 — 独立完成

### 4.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能机器人小车 C1（5DOF 机械臂 + HP60C RGB-D + COIN-D6 激光 + RK3576 NPU）；具身智能实验箱 B2 |
| 一键启动 | `ros2 launch car1_app navigation_grasp_transport.launch.py map:=slam_map` |
| 任务入口 | 服务 `/navigation_grasp_transport/start`（Trigger） |
| 运行话题 | `~/status`（String，当前状态名）、`~/error_reason`（String） |
| 依赖 | 实验 1 地图 + 实验 2 视觉/抓取 + 实验 3 语音意图 |
| 技能映射 | `car1_llm/config/skills.yaml`：`transport` 技能 → `/navigation_grasp_transport/start` |

### 4.4 实验难度

- 难度: ⭐⭐⭐ 综合性（capstone）
- 重点: 复杂任务状态机设计与全链路集成；用日志/话题观测定位各模块偶发故障
- 难点: 多模块时序耦合（导航到位时机、机械臂微调、检测取末次、抓取超时）；语音闸门与任务状态的同步

### 4.5 实验现象

**快速验证流程**：

1. 一键启动全栈（含 bringup/导航/机械臂/相机/主节点，Timing 依 launch 注释 t+0/8/10/15s）：
   ```bash
   ros2 launch car1_app navigation_grasp_transport.launch.py map:=slam_map
   ```
2. 另开终端触发任务：
   ```bash
   ros2 service call /navigation_grasp_transport/start std_srvs/srv/Trigger
   ```
3. 观察日志状态流转，应依次出现：
   ```
   STATE: IDLE -> SET_INITIAL_POSE
   Sent initial pose (...) to AMCL
   STATE: SET_INITIAL_POSE -> WAIT_LOCALIZATION
   Localization settle done
   STATE: WAIT_LOCALIZATION -> NAV_TO_PICK
   Nav2 goToPose[pick]: (0.756, 0.872, 3.071)
   Nav2 [pick] SUCCEEDED
   STATE: NAV_TO_PICK -> MOVE_TO_OBSERVE
   Moving arm to observation pose: x=0.20 y=0.00 z=0.22 pitch=180.0°
   STATE: MOVE_TO_OBSERVE -> WAIT_ARM_STABLE
   Arm stable, camera ready
   STATE: WAIT_ARM_STABLE -> ROTATE_SEARCH
   Search angle +0.0 deg (idx 0): red_pixels=...
   STATE: ROTATE_SEARCH -> DETECT_AND_GRASP
   Detect [1/5]: (...)
   ...
   FINAL target (from last of N detections): (x, y, z)
   Published set_pick_target: [..]
   STATE: DETECT_AND_GRASP -> CALL_PICK
   Calling /arm_controller/pick...
   STATE: CALL_PICK -> WAIT_GRASP
   Pick succeeded: ...
   STATE: WAIT_GRASP -> NAV_TO_PLACE
   Nav2 goToPose[place]: (-0.059, -0.103, 0.020)
   Nav2 [place] SUCCEEDED
   STATE: NAV_TO_PLACE -> PLACE_OBJECT
   Place succeeded / go_work done / Gripper closed. Task complete -> DONE
   STATE: PLACE_OBJECT -> DONE   (5s 后 -> IDLE)
   ```
4. 语音闭环：实验 3 链路就绪后，说"出发执行任务"，大模型命中 `start` → 触发本任务 → 复现步骤 3 全流程，且任务运行中唤醒被闸门暂停

**预期效果描述**：

- **导航**：小车从起始区 AMCL 收敛后，ThetaStar 全局 + DWB 局部规划到 `pick_pose`（桌面前方），停车朝向使相机可观测桌面
- **观察**：机械臂移到 `observe_pose=[0.20,0,0.22,π]`（相机下视桌面），等 `observe_settle_sec=5` 稳定
- **搜索**：`ROTATE_SEARCH` 依次转 ±15/30/45°，每角停 1.5s 检测红色像素，首个超过 `red_pixel_threshold=1000` 即切入抓取
- **抓取**：连续重复检测 5 次取末次得到稳定 `base_link` 目标，发布 `set_pick_target`，下一拍调 `pick`，夹爪抓到红色方块
- **运输放置**：导航回 `place_pose`，place 服务在 `place_target_arm=[0.26,0,0.08,π]` 释放方块，go_work 回位、夹爪闭合 → DONE → 5s 后回 IDLE 可再次触发
- **语音**：运行中 `Running` 状态暂停唤醒，任务结束恢复，实现"一次语音、全程自动"

### 4.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：状态机整体认知] --> B[步骤2：回调组与并发模型]
    B --> C[步骤3：导航与初始位姿状态]
    C --> D[步骤4：原地旋转搜索]
    D --> E[步骤5：检测-抓取-超时管理]
    E --> F[步骤6：运输放置与状态复位]
    F --> G[步骤7：语音闭环联调]
    G --> H[完成]
```

---

#### 步骤1：任务状态机整体认知（阶段二：能理解，50min）

> 📌 本步骤对应源码：`navigation_grasp_transport.py` `State` 枚举（L57-71）、`_enter`/`_tick_body`/`_elapsed_in_state`（L421-467）

**知识点讲解**：

**单一状态机编排（4.1.1）**

- **原理**：任务用**一个状态枚举**（13 个状态）把所有模块纳入单一调度：
  `IDLE→SET_INITIAL_POSE→WAIT_LOCALIZATION→NAV_TO_PICK→MOVE_TO_OBSERVE→WAIT_ARM_STABLE→ROTATE_SEARCH→DETECT_AND_GRASP→CALL_PICK→WAIT_GRASP→NAV_TO_PLACE→PLACE_OBJECT→DONE`（`FAILED` 兜底）。
  `_tick`（L421）以 0.1s 定时器周期执行，按当前状态派发到对应 handler；`_enter`（L383）记录进入时刻并按状态做一次性清理（如进 ROTATE_SEARCH 时记录基准航向、进 DETECT 时清空目标）；`_elapsed_in_state`（L418）做状态内超时判定。**关键设计**：每个状态只做一件确定的事，状态之间通过 `_enter()` 转移，状态内用 `_elapsed_in_state()` 守卫超时，避免状态卡死。

**操作步骤**：

1. 读 `State` 枚举与 `_tick_body`，画出状态转移表（当前态 → 触发条件 → 下一态）
2. 重点标注三处特殊拆分：`CALL_PICK` 独立于 `DETECT_AND_GRASP`；`ROTATE_SEARCH` 与 `DETECT_AND_GRASP` 分开；`PLACE_OBJECT` 内含多段 future
3. 用 `ros2 topic echo /navigation_grasp_transport/status` 实时观测状态名随任务推进

**易错点**：

- ⚠️ 状态转移都经 `_enter()` 完成初始化，不要直接改 `self.state`，否则状态内清理条件不生效

---

#### 步骤2：回调组与并发模型（阶段三：能改造，40min）

> 📌 本步骤对应源码：`navigation_grasp_transport.py` `__init__` L200-209、`main` L1119-1131

**知识点讲解**：

**并发与阻塞（4.1.2）**

- **原理**：节点启动 0.1s 定时器、多个订阅/服务客户端。为避免"阻塞性同步等待"（如 `_detect_and_project` 内 `time.sleep` 与 `_refresh_joints_sync` 的 1.5s 同步轮询）卡住其它回调，代码用：
  - `ReentrantCallbackGroup`（`_srv_cbg`/`_client_cbg`）给服务与客户端——允许并发回调；
  - `MutuallyExclusiveCallbackGroup`（`_timer_cbg`）给 tick 定时器——同一时刻只跑一个 tick，天然防并发改状态；
  - `MultiThreadedExecutor(num_threads=4)` 提供多线程，让 timer 与 service callback 并行。
- 若全用默认单线程、或把服务回调与 timer 放同一互斥组，同步等待会阻塞 tick 导致卡死。

**操作步骤**：

1. 读 `__init__` L200-209 与 `main` L1119-1131，理解三组回调组与 4 线程 executor 的关系
2. 思考题：把 `tick_timer` 改成 Reentrant 会引入什么风险？（并发 tick 可能同时改状态）
3. （可选）把线程数降到 1 复测，观察是否出现与服务回调互等

**易错点**：

- ⚠️ 状态机字段（self.state 等）由 timer 单线程访问，服务回调只触发 `_enter` 而不直接改字段并发——改动时保持此隔离

---

#### 步骤3：导航与初始位姿状态（阶段一：能运行，60min）

> 📌 本步骤对应源码：`_handle_set_initial_pose` L471-490、`_handle_wait_localization` L492-497、`_handle_navigate` L538-602

**知识点讲解**：

**初始位姿与连线导航（4.2.1 前置）**

- **原理**：
  - `SET_INITIAL_POSE`：构造 `PoseWithCovarianceStamped` 发到 `/initialpose`，把 `initial_pose=[-0.059,-0.103,0.020]` 给 AMCL；协方差设 `x/y=0.25、yaw=0.068`，表示"信任初值但允许 AMCL 微调"。
  - `WAIT_LOCALIZATION`：等 `localization_settle_sec=3` 后确保 nav2 `BasicNavigator` 就绪再进导航。
  - `NAV_TO_PICK/NAV_TO_PLACE`：`_handle_navigate(target,next,tag)` 用 `BasicNavigator.goToPose` 发起，`_nav_started` 防重复发起，轮询 `isTaskComplete`/`getResult`；失败时**重试一次**（`_nav_retry_used`）再 FAILED；`nav_timeout_sec=300` 超时兜底。

**操作步骤**：

1. 单独跑一次只到 NAV_TO_PICK 的流程，确认 AMCL 收敛与导航目标 `(0.756,0.872,3.071)` 命中
2. 故意在路径上放障，观察多目标重试与超时 FAILED 表现
3. 用 `ros2 topic echo /initialpose` 验证初始位姿/协方差已发布

**易错点**：

- ⚠️ 初始位姿误差过大会让 AMCL 收敛到错误点，后续 ROTATE_SEARCH 基准航向 `_search_base_yaw` 也错——先手工 `2D Pose Estimate` 校正再跑任务

---

#### 步骤4：原地旋转搜索（阶段二：能理解，60min）

> 📌 本步骤对应源码：`_handle_rotate_search` L604-658、`_get_current_yaw` L1089-1096

**知识点讲解**：

**闭环旋转搜索（4.2.1）**

- **原理**：机械臂到位后相机可能没正对桌面，`ROTATE_SEARCH` 让小车原地转搜：
  - 进状态时记录基准航向 `_search_base_yaw=_get_current_yaw()`（读 `map→base_footprint` TF 的 yaw）；
  - 对 `search_angles_deg=[0,±15,±30,±45]` 逐角计算目标 `target_yaw=_wrap_pi(base+angle)`；
  - 用 P 控制器闭环：`err=wrap_pi(target-current)`，`tw.angular.z=clamp(1.5*err, ±search_speed)` 发 `/cmd_vel`，`|err|≤search_yaw_tol=0.05` 才停；
  - 停定后 `search_settle_sec=1.5` 让图像稳定，再 `_count_red_pixels` 判红，`≥red_threshold=1000` 则进抓取，否则下一角；**所有角度耗尽**仍未见目标 → FAILED。
- 出主意：`search_speed=0.4`（rad/s）小于 `/cmd_vel` 上限 ±1.0，且靠角度误差驱动，故不会超速。

**操作步骤**：

1. 在机械臂观察位让小车偏离桌面，触发搜索，观察每角的 `current_search_angle` 话题与旋转到位
2. 把方块放在相机视野外某方向，验证多角搜索能转到"看见"并切换 DETECT
3. 记录每角 `red_pixels` 的变化曲线，理解阈值 1000 的设定依据

**易错点**：

- ⚠️ `_search_base_yaw` 是进状态那一刻读的基准；若导航到位后还被人推动，基准即失真
- ⚠️ 旋转中别停导航/碰撞脚边，防止 TF 基准漂移

---

#### 步骤5：检测-抓取-超时管理（阶段三：能改造，70min）

> 📌 本步骤对应源码：`_handle_detect_and_grasp` L660-747、`_handle_call_pick` L749-762、`_handle_wait_grasp` L764-791

**知识点讲解**：

**重复检测与分拍（4.2.2、4.2.3）**

- **原理**（承接实验 2）：`DETECT_AND_GRASP` 连续重复检测 `detection_repeat_count=5` 次、间隔 0.3s，**取最后一次**成功结果做目标（机械臂微调期瞬态不稳）；需至少 2 次成功才可信。随后发布 `set_pick_target` 并**独立进 `CALL_PICK`**（下一 tick 才调 pick），保证 arm 订阅回调已消费目标。`WAIT_GRASP` 轮询 pick future，`grasp_timeout_sec=60` 兜底；`detection_timeout_sec=30` 兜底检测。
- 所有"外部等待"（pick/place/go_work/gripper 的 future、导航 isTaskComplete）都以**非阻塞轮询 + 超时**处理，不阻塞 executor。

**操作步骤**：

1. 回顾实验 2 视觉链路；在本实验中用一个 `dry_run: true` 先验证 `FINAL target` 正确且机械臂不动
2. 触发一次真实抓取，观察 `<DETECT_AND_GRASP>` 打印的 5 次 Detect 与末次 target
3. 把 `detection_repeat_count` 改成 1 复测，对比目标稳定性（应看到 x 偏移隐患），理解"取末次"的价值
4. 人为把 `grasp_timeout` 调小，验证 FAILED 兜底（抓不到时不僵死）

**易错点**：

- ⚠️ 抓不到目标时不要反复触发——先看 `~/error_reason` 与 `[TF]`/`[DETECT]` 日志定位是"没检到"还是"检到但偏移"
- ⚠️ 紫色边框：`FINAL target` 与 `Published set_pick_target` 用的是最后检测结果，日志里前面的 Detect 只是过程，别被误导

---

#### 步骤6：运输放置与状态复位（阶段二：能理解，60min）

> 📌 本步骤对应源码：`_handle_place_object` L793-900、`_tick_body` DONE/FAILED 分支 L461-467

**知识点讲解**：

**多段放置与复位（4.2.3）**

- **原理**：`PLACE_OBJECT` 用三个 future 编排多段动作：
  1. 发 `place_target_arm=[0.26,0,0.08,π]` 到 `set_pick_target`（只存不移动）；
  2. 等 0.3s 后调 `/arm_controller/place`（下探→开夹→释放→上缩），`_place_future` 等待；
  3. place 成功后调 `/arm_controller/go_work`（回工作位），`_work_future` 等待；
  4. 回位后调 `set_gripper(False)`（闭合待命），`_gripper_future` 等待 → `_enter(DONE)`。
  三个 future 的"不全 None"判定（L806-807）防止末阶段重复触发 step1 造成"抓-放-抓-放"。`DONE` 保持 5s 后自动回 `IDLE`（可再次 `~/start`）；`FAILED` 也 5s 后回 IDLE。

**操作步骤**：

1. 观察放置：方块落在 `place_target_arm` 附近，机械臂回工作位、夹爪闭合
2. 复测第二趟：任务完成回 IDLE 后再次 `ros2 service call /navigation_grasp_transport/start`，验证可重复执行
3. 记录 3 趟的 "鼠标→放" 成功率与放置偏差

**易错点**：

- ⚠️ 改了 place 段 future 逻辑时，务必保持"三态合计"防重复触发
- ⚠️ 连续跑任务前确认方块/场地复位，避免重复抓同一物失败

---

#### 步骤7：语音闭环联调（阶段三：能改造，100min）

> 📌 本步骤对应源码：`car1_llm/config/skills.yaml`（transport 技能）、实验 3 的 wake_word.yaml；`navigation_grasp_transport.launch.py`

**知识点讲解**：

**语音→任务闭环、闸门同步（4.3.1、4.3.2）**

- **原理**：闭环分两线——**执行线**：语音唤醒 → ASR → RKLLM 大模型意图，命中 `start` 调用 `mission_orchestrator/start`；**任务线**：navigation_grasp_transport 提供 `~/start` 供上层触发，运行时把 `Running` 写到 `mission_state_topic` 的 `running=true` 暂停唤醒，任务结束恢复。`skills.yaml` 里已声明 `transport` 技能 → `/navigation_grasp_transport/start`，便于 LLM 侧直接按技能调用。
- 联调要点是**两条时序对齐**：语音触发的那一刻，导航/机械臂/相机都已由 `navigation_grasp_transport.launch.py` 的 TimerAction 就绪（t+0 nav、+8 arm、+10 camera、+15 主节点）。

**操作步骤**：

1. 分两条 main 栈起步：终端 1 起 `navigation_grasp_transport.launch.py`；终端 2 起 `full_interaction.launch.py`（语音）
2. 确认 `/navigation_grasp_transport/start` 与 `mission_orchestrator/start` 的关系（本课程以主节点 `~/start` 为任务入口；mission_orchestrator 为整场编排壳）
3. 完整一次：说"出发执行任务" → 意图 `start` → 触发任务 → 复现步骤 3-6 全流程 → 任务运行中再唤醒被闸门拦截 → 结束恢复唤醒
4. 故障演练：故意把初始位姿摆偏诱发"检不到目标"或"抓空"，用 `~/error_reason` + 日志定位并修复

**易错点**：

- ⚠️ 语音与任务串起来后，"导航还没就绪就被触发"的时序问题要靠 15s 延迟与内部 wait 兜住；实测失败多源于初始位姿与地图坐标不对齐
- ⚠️ `mission_state_topic` 的 `running` 必须由任务侧及时置位/复位，否则唤醒闸门失效或过早失效

---

### 4.7 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 启动后任务不响应触发 | 时序未就绪或服务未 up | 等 ≥15s；`ros2 service list` 确认真有 `/navigation_grasp_transport/start` |
| 导航到位搜不到目标 | 车位姿/搜索角未覆盖目标 | 校正初始位姿；加密/加宽 `search_angles_deg`；调 `red_pixel_threshold` |
| 抓取 MISS | 机械臂微调期定目标 | 保持 `detection_repeat_count=5` 取末次；调大 `observe_settle_sec` |
| 语音触发不了任务 | 意图未命中 start 或服务未转 | 补 `intent_hints.start.hints` 误识别词；核对 launch 时序 |
| 任务中能被唤醒打断 | 闸门未置位 | 检查任务侧发布 `mission_state_topic` running=true |
| 状态卡住不进下一步 | 状态内超时缺失或 future 未完成 | 查 `_elapsed_in_state` 与 future.done；看 `~/status` 卡在哪态 |
| place 反复抓-放 | place 段 future 三态判定被破坏 | 恢复 `_place/_work/_gripper_future` 合计判空逻辑 |

### 4.8 扩展实验

**扩展方向 1：多轮/多台车调度**
- 在 `mission_orchestrator` 层维护任务队列，支持"连续两趟抓不同目标点"，用状态话题 `queue_len` 让语音播报进度，验证编排层对单机多任务的调度

**扩展方向 2：异常恢复（重试升级）**
- 给 `WAIT_GRASP` 失败增加"重定位后重试"分支，替代直接 FAILED；评估重试对成功率与安全的影响

### 4.9 实验报告要求

**评分标准**：状态机设计与状态转移 20 分 + 回调组/并发 10 分 + 旋转搜索 15 分 + 检测-抓取-超时 20 分 + 运输放置与复位 15 分 + 语音闭环联调 20 分 = 100 分。

**报告必含内容**：
1. 完整状态转移表，标注触发条件与超时
2. 一次成功任务的日志时间线（导航→观察→搜索→抓取→放置→复位）
3. 语音闭环一次完整操作记录（唤醒词/指令/意图/任务状态）
4. 故障演练记录（现象/定位/修复）
5. 回答思考题：为什么状态机用一个 tick 定时器而非事件回调堆叠？CALL_PICK 独立状态解决了什么？运行闸门为什么按 running 字段暂停唤醒？
6. 综合心得：从单模块到全闭环，最大的集成难点是什么？如何改进？

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-09-23 | 初版生成（基于 navigation_grasp_transport.py 完整状态机与 navigation_grasp_transport.launch.py，params 取自 config/navigation_grasp_transport.yaml；语音桥接参考 skills.yaml transport 技能与 car1_speech/wake_word.yaml 的 start_service/running 闸门参数） |