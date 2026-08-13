# 实验6：具身智能工厂--分拣集成测试（4h）

> **源码**：`ros2_ws/src/xflz_eai_car1/app/eai_factory/`
> **主命令**：`ros2 service call /eai_factory/start_sort std_srvs/srv/Trigger`
> **覆盖模块**：N-grasp 抓取节点（`grasp_node.py` _do_fixed_grasp）→ N2 调度器（`scheduler_node.py` _trigger_grasp）
> **测试用例**：`docs/09_抓取测试用例.md`（TG6 固定点位抓取）

### 6.1 关联知识点

- 5.1.1 固定点位抓取 > 概念 > vision=false，依赖 observe_pose/place_pose 配置，无视觉无 TF
- 5.1.2 手动打点 > 流程 > 手动调机械臂到位→记录姿态→写入 yaml 配置
- 5.1.3 sort 动作原语 > 流程 > 提前开爪→移到抓取点→闭爪抓取→抬升→放置→回 work

### 6.2 实验目标

1. 理解固定点位抓取（vision=false）的原理与适用场景，与视觉抓取（vision=true）对比差异 — **原理理解**
2. 掌握手动打点方法：调整机械臂到位、读取姿态、写入 `grasp.tasks.sort` 配置 — **流程掌握**
3. 独立完成分拣任务集成测试，观察"提前开爪→抓取→抬升→放置"完整序列并解读日志 — **独立完成**
4. 能够通过调优 sort 的 place_pose/lift_height 参数修正放置精度，并完成语音联动闭环验证 — **迁移应用**

### 6.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱 B2 / 机器人小车 C1（5DOF 机械臂，总线舵机，含夹爪） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10；grasp 节点用 ros2_venv（`/home/iflytek/ros2_venv/bin/python3`） |
| 核心库 | rclpy、tf2_ros、std_srvs（Trigger/SetBool） |
| 依赖 | arm_controller 提供 `/arm_controller/set_gripper`、`/arm_controller/go_work` 服务（由 launch start_base 拉起） |
| 主入口 | `eai_factory.launch.py`（单测可 `start_voice:=false`；语音联动需 `start_voice:=true`） |

### 6.4 实验难度

- 难度: ⭐⭐⭐
- 重点: 固定抓取八步序列（提前开爪是关键）、手动打点方法与配置写入
- 难点: 打点姿态的精确记录与放置位调优（place_pose/lift_height）；与视觉抓取序列的差异理解

### 6.5 实验现象

**快速验证流程**：

1. 省内存启动：`ros2 launch eai_factory eai_factory.launch.py start_voice:=false`
2. 分拣取料区放置物料，触发分拣：
   ```bash
   ros2 service call /eai_factory/start_sort std_srvs/srv/Trigger
   ```
3. 观察机械臂序列：提前开爪（set_gripper open OK）→ 带张开夹爪移到抓取点（0.062, -0.116, 0.195）→ 闭爪（set_gripper close OK）→ 抬升 → 移到放置点 → 开爪放置 → 放置后抬升 5cm → go_work 回 work
4. 日志出现 `=== fixed grasp-place sequence done ===`，随后 `grasp: status: sort|done`
5. 语音联动（带语音启动）：说「分拣」→ 扬声器播报"好的，开始分拣"→ 任务完成后播报"分拣完成"

**预期效果描述**：

- 固定抓取全程不依赖相机/视觉/TF（无需 AprilTag）
- 夹爪在机械臂移动前已完全张开（提前开爪），到位立即闭爪抓取
- 分拣完成物料准确放置到放置位；`/eai_factory/grasp/status` 输出 `sort|done`
- 语音联动时 scheduler 收到 done 后经 /eai_factory/speak 播报"分拣完成"

### 6.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：手动打点配置] --> B[步骤2：启动分拣任务]
    B --> C[步骤3：放置位与抬升参数调优]
    C --> D[步骤4：语音联动闭环]
    D --> E[步骤5：测试用例执行]
```

---

#### 步骤1：手动打点配置（60min）

**知识点讲解**：

**手动打点（5.1.2）**
- **原理**：固定点位抓取的取料位（observe_pose）与放置位（place_pose）不是视觉解算的，而是人工"打点"得到——通过 arm_controller 手动把机械臂移动到目标姿态，读取当前末端位姿（x, y, z, pitch，单位米/弧度），写成 [x, y, z, pitch] 四元组写入 yaml 的 `grasp.tasks.sort`。pitch 是末端俯仰角（sort 当前 3.0371 rad ≈ 174°，几乎垂直向下），打点时需用夹爪实际抓取姿态校准。打点质量直接决定固定抓取成功率——点打偏 1cm，抓取就偏 1cm，且没有视觉兜底。
- **源码对应**：`eai_factory.yaml` L83-86（sort 任务配置）；`grasp_node.py` L56-58（参数声明）与 L89-94（task_poses 加载）

```python
# grasp_node.py L56-58：sort 任务姿态参数声明
self.declare_parameter('grasp.tasks.sort.observe_pose', [0.0622, -0.1158, 0.1951, 3.0371])
self.declare_parameter('grasp.tasks.sort.place_pose', [0.1434, -0.1296, 0.2075, 2.7283])
self.declare_parameter('grasp.tasks.sort.vision', False)
```

**固定点位抓取（5.1.1）**
- **原理**：`vision=false` 时 grasp 不订阅视觉、不做 TF，observe_pose 就是精确抓取点，序列直接走 `_do_fixed_grasp`（`start_grasp` L273-278 分支）。它不调用 arm_controller 的 pick/place 服务，而是 grasp 自己编排 `set_gripper`（开合夹爪）与 `target_pose`（移动）服务完成整个抓放——这是与视觉抓取（load，走 pick/place 服务）最大的结构差异。好处是少依赖两个服务、时序完全可控。
- **源码对应**：`grasp_node.py` L273-278（vision=false 分支）；`eai_factory.yaml` L83-86（vision: false）

**操作步骤**：

1. 启动系统：`ros2 launch eai_factory eai_factory.launch.py start_voice:=false`
2. 通过 arm_controller 手动控制（话题/服务）把机械臂末端移到分拣取料位，姿态为夹爪垂直向下（pitch≈π）、能直接罩住物料
3. 读取当前末端位姿 (x, y, z, pitch)，记录到工作笔记（参考当前值 [0.0622, -0.1158, 0.1951, 3.0371]）
4. 编辑 `config/eai_factory.yaml` 的 `grasp.tasks.sort.observe_pose`，写入新打点值（如微调为 [0.062, -0.116, 0.195, 3.037]），保存并重启 launch 生效
5. 同样方法校准放置位 place_pose（当前 [0.1434, -0.1296, 0.2075, 2.7283]）

**易错点**：

- ⚠️ 打点姿态与抓取时姿态不一致（夹爪角度不同）→ 固定抓取用打点的 pitch（`_set_pick_target` L366-367 手动打点 pitch），必须用实际抓取姿态打点，不要用随意姿态
- ⚠️ 改 yaml 后不生效 → grasp 节点启动时一次性加载 task_poses（L89-94），必须重启；运行时改 `ros2 param set` 只影响运行中的节点
- ⚠️ 分拣/码垛共用 grasp 节点，打点时确认当前任务为 sort（日志 `Current task set to: sort`）

---

#### 步骤2：启动分拣任务（60min）

**知识点讲解**：

**sort 动作原语（5.1.3）**
- **原理**：固定抓取八步序列（`_do_fixed_grasp`，L413-485）：① `set_gripper open` 提前开爪并等待完全张开（gripper_duration+0.2s）→ ② 带张开的夹爪直接 `target_pose` 移到抓取点（不加偏移，用打点 pitch）→ ③ `set_gripper close` 闭爪抓取 → ④ 抬升到 (x, y, z+lift_height=0.03) 防碰撞 → ⑤ 移到放置点 → ⑥ 开爪放置 → ⑦ 放置后抬升 5cm（place_lift=0.05）→ ⑧ `go_work` 回 work。与视觉抓取序列不同：固定抓取**先开爪再移动**，保证机械臂到达时夹爪已完全张开、呈"骑跨"姿态罩住物料；全程用 `_call_gripper`（L494-515）同步等待夹爪动作完成再移动，避免"到位时夹爪还在张"。
- **源码对应**：`grasp_node.py` L413-485（_do_fixed_grasp）；L62-64（move_delay/lift_height/gripper_duration）；`eai_factory.yaml` L66-70
- **公式/配图说明**：抬升点 = (ox, oy, oz + lift_height)，放置后抬升点 = (px, py, pz + place_lift)。lift_height 是"抓取后抬升高度"（默认 0.03m，防碰撞），place_lift 是"放置后抬升高度"（默认 0.05m）。两个参数都只在 z 方向叠加。

```python
# grasp_node.py L433-442：①提前开爪 → ②移到抓取点
if not self._call_gripper(True):      # ① open + 等待完全张开
    return
...
self._move_to_pose(ox, oy, oz, opitch)   # ② 带张开夹爪直接到抓取点
time.sleep(self.move_delay)
```

**操作步骤**：

1. 确认 grasp 节点运行、分拣物料已在取料区，触发分拣（经 N2 调度器 /eai_factory/start_sort 服务，scheduler L64-65/L220-224）：
   ```bash
   ros2 service call /eai_factory/start_sort std_srvs/srv/Trigger
   ```
2. 核对日志（docs/09 TG6 期望日志 L109-116）：
   ```
   set_gripper open OK                      ← ①提前开爪并等待张开完成
   target_pose: (0.062, -0.116, 0.195), pitch=174°  ← ②直接到抓取点（打点姿态）
   set_gripper close OK                     ← ③到位闭爪抓取
   target_pose 抬升 → target_pose 放置点    ← ④⑤
   set_gripper open OK（放置）              ← ⑥开爪放置
   target_pose 放置点上方5cm                ← ⑦放置后抬升
   go_work OK → === fixed grasp-place sequence done ===
   ```
3. 观察机械臂动作：移动时夹爪保持张开"骑跨"物料，到位闭爪，抬升平移，放置后先抬 5cm 再回 work
4. 检查完成状态：`ros2 topic echo /eai_factory/grasp/status`（一次性）应输出 `sort|done`（`_publish_status` L487-492）
5. 串行保护验证：分拣执行中再次触发 start_sort 会返回 `busy`（`_start_cb` L210-213），等 done 后再触发

**易错点**：

- ⚠️ 机械臂到位时夹爪还在张开动作中 → 确认 `_call_gripper` 等待逻辑（L511 `time.sleep(self.gripper_duration + 0.2)`）；不要人为调小 gripper_duration 后不重启
- ⚠️ 触发 start_sort 无反应 → scheduler 的 grasp 服务未就绪会自动 2s 重试（`scheduler_node.py` L136-144）；`ros2 service list | grep grasp` 确认服务存在
- ⚠️ 分拣执行中触发码垛/装货返回 busy → 这是串行保护正常行为（docs/09 L124），等 `=== fixed grasp-place sequence done ===` 再触发

---

#### 步骤3：放置位与抬升参数调优（45min）

**知识点讲解**：

**固定点位抓取调优（5.1.1）**
- **原理**：分拣精度由两个来源决定：取料打点（observe_pose）与放置配置（place_pose + lift_height/place_lift）。放置偏了调 place_pose（x/y 水平、z 高度、pitch 角度四元组）；夹取后上升不够会蹭到物料/相邻物体，调 `grasp.lift_height`；放置后抬升不够可能压到已放物料，调 `grasp.place_lift`。这些参数都是 base_link 系的米/弧度，与视觉抓取的 pick_offset 不同——固定抓取本身**不加任何偏移**（打点已含姿态，`_set_pick_target` L364-367）。
- **源码对应**：`grasp_node.py` L62-64（lift_height/place_lift 声明）；`eai_factory.yaml` L66-70（grasp 段）、L83-86（sort 姿态）；docs/09 L161（固定抓取不加偏移）

**操作步骤**：

1. 动态微调放置高度（不重启）：
   ```bash
   ros2 param set /eai_factory_grasp grasp.lift_height 0.05
   ros2 param get /eai_factory_grasp grasp.lift_height
   ```
2. 再次触发分拣，观察抬升高度变化（日志 target_pose 的 z 值）
3. 放置位调优：若物料放置偏左 5mm，把 yaml sort 的 place_pose y 值调 +0.005（+Y 左），重启后再测
4. 记录参数→结果对照表：至少 3 组（lift_height × place_pose 组合）的放置偏差与成功率
5. 将最优值写回 `config/eai_factory.yaml`（注意 lift_height/place_lift 是 grasp 全局参数，影响 sort/palletize 两个固定抓取任务）

**易错点**：

- ⚠️ 参数只改了一半（只改 yaml 未重启，或只 param set 未写回）→ 最终验证以重启后 yaml 值为准；param set 只用于快速试参
- ⚠️ place_lift 与 lift_height 混淆 → lift_height 是"抓取后抬升"（取料侧），place_lift 是"放置后抬升"（放料侧），调错方向现象完全不同
- ⚠️ 抬升过大导致机械臂最高点超限 → z 值控制在机械臂工作空间内，逐步 ±1cm 试探

---

#### 步骤4：语音联动闭环（45min）

**知识点讲解**：

**分拣完成播报链路（5.1.3）**
- **原理**：分拣任务完成后 N-grasp 发布 `grasp/status`（"sort|done"），scheduler 的 `_grasp_status_cb`（L195-210）解析出任务与状态，命中 done 后把 `sort → 分拣完成` 的固定文案发布到 /eai_factory/speak，voice 节点 `_speak_cb`（L827-830）收到后 TTS 播报。整条链路就是"任务完成 → 状态发布 → 调度器翻译 → 语音播报"，完成语音→意图→任务→播报的闭环。
- **源码对应**：`scheduler_node.py` L195-210（_grasp_status_cb）；`voice_node.py` L827-830（_speak_cb）、L306（phrases_task_done）；`eai_factory.yaml` L52（sort_done: "分拣完成"）

```python
# scheduler_node.py L198-204：解析 grasp 状态并映射播报文案
task, status = msg.data.split('|')
...
if status == 'done':
    phrase = {'load': '装货完成', 'sort': '分拣完成',
              'palletize': '码垛完成'}.get(task, '任务完成')
```

**操作步骤**：

1. 带语音重启系统（分拣已完成打点，此时才需要语音）：`ros2 launch eai_factory eai_factory.launch.py`
2. 终端 2 监听闭环话题：
   ```bash
   ros2 topic echo /eai_factory/intent
   ros2 topic echo /eai_factory/grasp/status
   ros2 topic echo /eai_factory/speak
   ```
3. 唤醒后说「分拣」→ 扬声器播报"好的，开始分拣"（voice L759），scheduler 路由 `[SCHEDULER] set grasp task -> sort`（L148）
4. 机械臂执行固定抓取序列，完成后核对播报链路：`grasp: status: sort|done` → `[SCHEDULER] task sort done — announce "分拣完成"` → `[VOICE] speak request: "分拣完成"` → 扬声器播出"分拣完成"
5. 对照 docs/07 TC6 全链路时序（L163-173）核对完整闭环

**易错点**：

- ⚠️ 播报"好的，开始分拣"后机械臂不动 → 语音闭环正常但 grasp 服务未就绪；scheduler 自动重试（L136-144），确认 `ros2 service list | grep grasp`
- ⚠️ 完成播报缺失但分拣正常完成 → grasp 未发布 status（检查 `grasp: status: sort|done`）或 scheduler 未订阅（L50-51）；先手动 `ros2 topic pub -1 /eai_factory/speak` 验证 TTS 链路
- ⚠️ 说「分拣」被识别成"风景/封建" → ASR 热词未生效（hotwords.txt 含"分拣"词条）；确认 `hotwords_enable: true` 并重启（见实验4）

---

#### 步骤5：测试用例执行（30min）

**知识点讲解**：

**固定抓取用例验证（5.1.3）**
- **原理**：docs/09 TG6 是分拣的标准用例，覆盖固定抓取八步序列的完整验证；TG7（语音打断复位）验证任务执行中 interrupt 的停止动作与回 work（grasp `_interrupt_cb` L179-186）；TG8（雷达危险中断）验证 danger 信号立即停止抓取。本实验至少完成 TG6 与 TG7 的实机记录，TG8 属于安全联锁实验（exp08）范围可顺带观察。
- **源码对应**：docs/09 TG6（L90-124）、TG7（L126-138）；`grasp_node.py` L179-186（interrupt）、L188-202（danger）

**操作步骤**：

1. 按 docs/09 TG6 完成分拣用例：连续执行 3 次 start_sort，记录每次的八步日志与放置结果
2. 按 TG7 做打断复位：触发 start_sort 后，机械臂动作中发布
   ```bash
   ros2 topic pub -1 /eai_factory/interrupt std_msgs/msg/Bool "{data: true}"
   ```
   观察 `VOICE INTERRUPT — stopping grasp, going work` 与机械臂停止动作回 work（docs/09 L135-138）
3. 整理实验数据：打点值、调优参数、放置偏差、成功率，形成调优结论

**易错点**：

- ⚠️ 打断测试后 grasp 状态未回 idle → `_interrupt_cb` 已置位并回 work（L179-186），必要时 `/eai_factory/grasp/abort` 重置再测
- ⚠️ 连续触发时上一次未完成 → 出现 `busy`；严格遵守"等 done 再触发下一个"（docs/09 L124）

### 6.7 注意事项

- ⚠️ 固定抓取无视觉兜底，取料区物料位置每次必须与打点一致，物料挪动后重新打点
- ⚠️ 实机测试前确认机械臂工作空间无干涉；打点与调优时手远离夹爪与机械臂
- ⚠️ 总线舵机在夹爪堵转/过载时可能发热，物料尺寸过大不要强行闭爪
- ⚠️ lift_height/place_lift 是 grasp 全局参数，调优会影响 palletize（码垛），改后两任务都需复测
- ⚠️ 语音联动需要启动 voice（LLM 约 500MB 内存）；仅测分拣用 `start_voice:=false` 省内存
- ⚠️ 一次只能执行一个任务（串行保护），多任务触发前确认上一任务已完成

### 6.8 实验总结

**完成成果**：

- 完成分拣取料位/放置位手动打点并写入 grasp.tasks.sort 配置
- 跑通固定抓取八步序列（提前开爪→到点→闭爪→抬升→放置→回 work），记录完整日志
- 完成 place_pose/lift_height 参数调优，形成参数→结果对照数据
- 完成语音联动闭环："分拣"→ 开始分拣播报 → 任务完成 →"分拣完成"播报
- 按 docs/09 TG6/TG7 完成分拣与打断用例记录

**技能收获**：

- 掌握固定点位抓取（vision=false）的原理与配置方法
- 掌握手动打点流程（到位→读姿→写 yaml→验证）
- 掌握固定抓取八步序列与"提前开爪"的时序关键点
- 理解 grasp/status → speak 的完成播报链路与闭环验证方法

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 抓取点偏位 | 打点不准或物料挪动 | 重新打点写入 observe_pose；固定物料位置 |
| 到位时夹爪未张开 | gripper_duration 过小/未重启 | 等 _call_gripper 的等待完成；确认参数生效 |
| 放置压到物料 | place_lift 不够 | 调大 grasp.place_lift（默认 0.05） |
| 触发返回 busy | 上一任务未完成（串行保护） | 等 `=== fixed grasp-place sequence done ===` |
| 无"分拣完成"播报 | grasp 未发 status 或语音未启 | 检查 `grasp: status: sort\|done`；用 start_voice:=true |
| 语音识别"风景/封建" | ASR 热词未生效 | 确认 hotwords_enable: true 并重启 |

### 6.9 实验报告要求

**思考题**：

1. 固定点位抓取与视觉抓取（load）在序列结构上有哪些差异？为什么固定抓取要"提前开爪"而视觉抓取不需要？
2. 手动打点的四元组 (x, y, z, pitch) 中 pitch 的含义是什么？如果打点时夹爪不是垂直向下，抓取会出现什么问题？
3. lift_height 与 place_lift 分别在序列的哪个环节生效？它们的作用分别是什么？调大/调小各有什么风险？
4. 固定抓取为什么不加 pick_offset 偏移？它与视觉抓取的 pick_offset 补偿在定位误差来源上有什么本质区别？
5. 分拣任务完成后"分拣完成"播报是如何触发的？结合 grasp/status 与 scheduler 的 _grasp_status_cb 描述完整链路。

**评分标准**：手动打点与配置 25 分 + 分拣任务执行与序列观察 30 分 + 参数调优实验 20 分 + 语音联动闭环 15 分 + 用例记录与数据分析 10 分 = 100 分。
