## 实验6：基于激光雷达的单点与多点导航避障实验（8h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/navigation/car1_navigation/`，未复制到 `source-codes/EXP004/exp06/`。已通过 human_waiver 放行，内容基于 `config/nav2_params.yaml`（bt_navigator / behavior_server / progress_checker 段）与 `launch/navigation.launch.py` 撰写。

**一句话读懂**：前面我们"点一个目标，到一处"。真实任务往往是"**先去 A 放货，再去 B 取货，最后回 C**"。这节课用两个 Nav2 导航器（NavigateToPose / NavigateThroughPoses），让小车**连续完成多个目标**，而且中途有障碍也能一路安全走完。

### 6.1 关联知识点

- 6.1.1 导航Action > 概念 > /navigate_to_pose 单目标、/navigate_through_poses 多点
- 6.1.2 单点导航 > 流程 > ros2 action send_goal 命令
- 6.2.1 多点导航 > 流程 > 一次下发多个途经点顺序经过
- 6.2.2 任务调度 > 原理 > 目标序列 + 到达判定 + 失败重试
- 6.3.1 评估指标 > 流程 > 到达率/平滑度/避障响应/停车次数
- 6.3.2 安全兜底 > 原理 > 进度检查 + 行为服务器恢复

### 6.2 实验目标

1. 理解 ROS2 Action 通信机制与两个导航器的区别 — **原理理解**
2. 掌握单点导航与多点连续导航的命令行操作 — **流程掌握**
3. 掌握导航任务调度与失败重试的基本方法 — **流程掌握**
4. 能够评估多点导航的鲁棒性并处理异常（卡住/超时）— **迁移应用**

### 6.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 小车C1 + COIN-D6 雷达；地图 + 定位可用 |
| OS | Ubuntu 22.04 + ROS 2 Humble |
| 核心库 | Nav2 bt_navigator、nav2_msgs（NavigateToPose/NavigateThroughPoses action） |
| 依赖 | 完成实验 3/4；导航 launch 正常运行 |
| 主入口 | `navigation/car1_navigation/launch/navigation.launch.py`、`config/nav2_params.yaml` |

### 6.4 实验难度

- 难度: ⭐⭐⭐（综合性）
- 重点: Action 下发与多点连续导航
- 难点: 连续导航的调度与异常恢复

### 6.5 实验现象

**快速验证流程**：

1. 启动导航：`ros2 launch car1_navigation navigation.launch.py map:=slam_map`，完成定位
2. 单点导航：`ros2 action send_goal /navigate_to_pose ...`（或 RViz Nav2 Goal），观察小车到达
3. 多点导航：先启动客户端脚本，再同时发布 A/B/C 三个途经点，观察小车**依次经过**三个点最终停下
4. 途中放纸箱：多点导航时小车在点与点之间自动避障
5. 堵死通道测试：观察小车卡住 → 行为服务器 spin/backup 恢复 → 重试

**预期效果描述**：

- 单点：小车从起点直线/绕行到达目标，`ros2 action send_goal` 返回 SUCCEEDED
- 多点：小车轨迹依次经过 A→B→C（可用 RViz 的 Path 或记录 /amcl_pose 验证）
- 避障：途经点之间遇到障碍自动绕行，不中断任务
- 异常：通道被堵死时小车尝试恢复动作（原地转/后退），恢复失败则任务失败（ABORTED），不会盲目硬闯

### 6.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：理解Action接口] --> B[步骤2：单点导航]
    B --> C[步骤3：多点导航]
    C --> D[步骤4：避障与调度]
    D --> E[步骤5：鲁棒性评估]
```

---

#### 步骤1：理解 ROS2 Action 与导航器（60min）

**知识点讲解**：

**Action 通信机制（6.1.1）**
- **原理**：ROS2 的 **Action** 是"话题+服务"的组合升级：请求方发**目标（goal）**→ 执行方持续回报**反馈（feedback）**→ 完成后返回**结果（result）**。对导航这种"要跑很久、要随时看进度"的任务非常合适。
- **白话类比**：Topic 像"对讲机广播"（单向）、Service 像"打电话"（一问一答）、Action 像"派快递"（下单→物流跟踪→签收确认）。
- **源码对应**：`nav2_params.yaml` bt_navigator `navigators: ["navigate_to_pose", "navigate_through_poses"]`（L62）注册了两个导航器；`nav2_msgs/action/NavigateToPose`、`NavigateThroughPoses` 是动作定义。

**两个导航器（6.1.2 + 6.2.1）**
- **原理**：
  - `navigate_to_pose`：只有一个最终目标点（位置+朝向），行为树流程：计算路径 → 跟踪 → 到达
  - `navigate_through_poses`：有一串**途经点**（intermediate poses），机器人**必须依次经过每个点**，最后停在最后一个点；常用于"巡检路线"等任务
- **源码对应**：`nav2_params.yaml` L63-66（NavigateToPoseNavigator / NavigateThroughPosesNavigator plugin）。

**操作步骤**：

1. 查看 action 定义：
   ```bash
   ros2 interface show nav2_msgs/action/NavigateToPose
   # 看 goal（pose）/ feedback（distance_remaining）/ result（result）
   ```
2. 对比两个 action 的 goal 结构（NavigateThroughPoses 是 `poses[]` 数组）。
3. 画图：Action 三部分（goal/feedback/result）在导航中的语义。

**易错点**：

- ⚠️ 混淆 service 与 action → **解决**：导航是"长时间+可取消+有反馈"的任务，用 action 而非 service。
- ⚠️ 以为 send_goal 是阻塞的 → **解决**：`ros2 action send_goal` 默认等待完成（--feedback 可看进度）；`&` 后台执行需自测。

---

#### 步骤2：单点导航（60min）

**知识点讲解**：

**单点导航命令（6.1.2）**
- **原理**：命令行下发一个 PoseStamped 目标，bt_navigator 自动完成规划+执行。frame_id 必须为 **map**（全局坐标系），位置单位米，朝向用四元数（w=1 表示朝向 map 的 +X 方向）。
- **源码对应**：目标经过行为树 `nav2_compute_path_to_pose_action_bt_node` → `nav2_follow_path_action_bt_node`（plugin_lib_names 已注册，nav2_params.yaml L69-112）。

**操作步骤**：

1. 启动导航并定位（实验 3/4 的完整环境）。
2. 单点导航（目标 map 系 (1.0, 0.5)）：
   ```bash
   ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
     "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 0.5}, orientation: {w: 1.0}}}}"
   ```
3. 加 --feedback 观察实时进度：
   ```bash
   ros2 action send_goal --feedback /navigate_to_pose ... 
   # feedback.distance_remaining 逐渐减小
   ```
4. 连续下发 5 个不同目标点，记录每个：到达用时、最终位置误差（`ros2 topic echo /amcl_pose` 对比）。
5. 目标点放在墙内测试：观察 action 返回 ABORTED（规划失败），理解"目标不可达"。

**易错点**：

- ⚠️ frame_id 写错（如写 odom）→ **解决**：目标必须是 `map` 系，否则机器人会去错误位置。
- ⚠️ 目标在墙内仍返回 SUCCEEDED？→ **解决**：不会，规划失败会 ABORTED；若在墙边，xy_goal_tolerance 内可能"够到"。
- ⚠️ 朝向四元数写错 → **解决**：想朝 +X 用 w=1；朝 -Y 用 (0,0,-0.707,0.707)；可用 `ros2 run tf2_ros tf2_echo` 验证。

---

#### 步骤3：多点连续导航（90min）

**知识点讲解**：

**navigate_through_poses（6.2.1）**
- **原理**：一次下发多个途经点 `poses[]`，机器人必须**依次经过**每个点（点与点之间也避障），最后停在最后一个点。适合"巡检、送货路线"。
- **源码对应**：`nav2_params.yaml` L66（NavigateThroughPosesNavigator）；行为树 `nav2_compute_path_through_poses_action_bt_node`（L71）。

**操作步骤**：

1. 下发 3 个途经点（A(0,0.5) → B(1,1) → C(1.5,0.5)）：
   ```bash
   ros2 action send_goal /navigate_through_poses nav2_msgs/action/NavigateThroughPoses \
     "{poses: [{header: {frame_id: 'map'}, pose: {position: {x: 0.0, y: 0.5}, orientation: {w: 1.0}}},
               {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 1.0}, orientation: {w: 1.0}}},
               {header: {frame_id: 'map'}, pose: {position: {x: 1.5, y: 0.5}, orientation: {w: 1.0}}}]"
   ```
2. 观察小车轨迹是否**依次经过三点**（记录 /amcl_pose 时间序列，绘制轨迹）。
3. 对比测试：改用三个**单点** navigate_to_pose 连续下发，对比：
   - 总耗时 vs 多点导航
   - 轨迹差异（多点会强制经过中间点，单点可能"抄近路"）
4. 验证"必须经过"语义：把 B 点放到障碍区，观察多点导航卡住或绕行，而单点导航不受影响。

**易错点**：

- ⚠️ 以为多点 = 只去终点 → **解决**：中间点是**必经点**，机器人会刻意经过（这正是它与单点的本质区别）。
- ⚠️ 途经点间距太小（<0.3m）→ **解决**：相邻点太近会导致行为树到达判定混乱，保持间距 >0.5m。

---

#### 步骤4：任务调度与避障（90min）

**知识点讲解**：

**任务调度（6.2.2）**
- **原理**：连续任务 = "目标序列管理 + 逐个执行 + 异常处理"。每段导航看 **action 返回结果**：SUCCEEDED→下一个目标；ABORTED→记录失败并重试或跳过。到达判定由 `general_goal_checker` 完成（xy_goal_tolerance 0.10m / yaw_goal_tolerance 0.1rad）。
- **源码对应**：`nav2_params.yaml` L128-132（general_goal_checker）。

**安全兜底（6.3.2）**
- **原理**：导航过程中如果机器人"长时间没挪窝"，`progress_checker` 判定卡住（`required_movement_radius: 0.1` / `movement_time_allowance: 10.0`，10 秒没动 10cm 算卡住）→ behavior_server 介入执行恢复动作：**spin**（原地转一圈重新找路）、**backup**（后退）、**drive_on_heading**（沿朝向直行）→ 恢复后重试路径。恢复无效则任务 ABORTED。
- **白话类比**：导航像送外卖——骑手迷路了先原地转圈看看（spin），不行倒车出来（backup），还不行就报告"这单送不了"（ABORTED），而不是硬闯。
- **源码对应**：`nav2_params.yaml` L121-127（progress_checker）、L185-212（behavior_server：spin/backup/drive_on_heading/assisted_teleop/wait）。

**操作步骤**：

1. 写一个简单的 Python 调度脚本（伪代码，改造成可运行的）：
   ```python
   # 依次导航到目标列表，失败自动重试 1 次
   goals = [g1, g2, g3]
   for g in goals:
       result = send_navigate_to_pose(g)   # 阻塞等待完成
       if result == SUCCEEDED:
           print(f"目标 {g} 完成")
       else:
           print(f"目标 {g} 失败，重试")
           result = send_navigate_to_pose(g)
   ```
2. 通道堵死测试：把 3 个纸箱堵住必经通道 → 下发目标 → 观察：
   - progress_checker 卡住判定（日志 `Failed to make progress`）
   - behavior_server 执行 spin/backup
   - 尝试恢复失败 → ABORTED
3. 记录完整时间线：卡住时刻 → 恢复动作 → 结果。
4. 对比验证：只堵一半（留 60cm 通道），观察能否绕过继续（避障生效，无需恢复动作）。

**易错点**：

- ⚠️ 误以为卡住后无限重试 → **解决**：恢复动作有限次，无效则 ABORTED，这是安全设计。
- ⚠️ 调度脚本忘处理 ABORTED → **解决**：真实任务必须检查 action 结果，失败要记录与重试，否则任务"静默失败"。

---

#### 步骤5：鲁棒性评估（90min）

**知识点讲解**：

**评估指标体系（6.3.1）**
- **原理**：导航系统"好不好"用四个指标量化：

| 指标 | 定义 | 本项目合格线（参考） |
|------|------|---------------------|
| 到达率 | 成功到达目标的任务占比 | ≥ 80% |
| 路径平滑度 | 路径转弯次数/轨迹抖动 | 无急转、无明显抖动 |
| 避障响应 | 从障碍出现到开始绕行的时间 | < 2s |
| 中途停车 | 非终点停车次数（卡住触发） | ≤ 1 次/任务 |

- **源码对应**：progress_checker（卡住检测）与 goal_checker（到达判定）共同决定这些指标。

**操作步骤**：

1. 设计一条 3 点巡检路线（A→B→C），连续跑 5 遍，记录：
   - 到达率（成功/总数）
   - 每段平均耗时
   - 中途停车次数
   - 是否有 recovery 动作触发
2. 加入 1 个移动障碍（人走动），再跑 5 遍，对比到达率与避障响应。
3. 数据汇总表：

| 组别 | 到达率 | 平均耗时 | 停车次数 | 避障响应 |
|------|--------|---------|---------|---------|
| 无障碍 5 次 | | | | - |
| 有动障 5 次 | | | | |

4. 写鲁棒性小结：这套小车+Nav2 配置在什么条件下可靠，什么条件下会失效（如对称大厅、超窄通道）。

**易错点**：

- ⚠️ 只测一次就下结论 → **解决**：至少 5 次取统计，导航是有随机性的。
- ⚠️ 动障测试时人挡住传感器 → **解决**：人不要在雷达正前方静止超过 0.5s，保持走动，否则会被当成静态障碍。

### 6.7 注意事项

- ⚠️ 多点导航测试场地至少 3m×4m，多点间留出转弯空间。
- ⚠️ 调度脚本注意加"目标可达"预检查（用 costmap 判断），避免明知不可达还发。
- ⚠️ 恢复动作测试时人远离小车，spin 旋转半径内不要站人。
- ⚠️ 每次评估跑多遍取统计，单次现象不做结论。

### 6.8 实验总结

**完成成果**：

- 理解 ROS2 Action 机制与两个导航器的语义差异
- 掌握单点（navigate_to_pose）与多点（navigate_through_poses）导航命令
- 完成任务调度（目标序列 + 失败重试）与避障测试
- 完成卡住恢复（progress_checker + behavior_server）观察与鲁棒性评估

**技能收获**：

- 技能1：ros2 action 下发与反馈查看
- 技能2：多点导航调度脚本编写
- 技能3：导航鲁棒性量化评估（到达率/停车/避障响应）

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 多点导航不按顺序 | 途经点配置错误 | 检查 poses[] 顺序与 frame_id |
| 中间点被跳过 | 到达判定容差过大 | 调小 xy_goal_tolerance |
| 一直卡住不恢复 | progress_checker 未触发 | 检查 movement_time_allowance |
| 恢复后仍失败 | 通道真堵死 | 属正常 ABORTED，勿盲目重试 |
| 调度脚本无响应 | 未检查 action 结果 | 加 result 检查与日志 |

### 6.9 实验报告要求

**思考题**：

1. Action 相比 Topic/Service 有什么优势？导航为什么必须用 Action？
2. navigate_to_pose 与 navigate_through_poses 的语义差异是什么？各自适合什么任务场景？
3. progress_checker（10s/10cm）如何判断"卡住"？为什么需要这个机制？
4. 多点导航中某个点失败，你的调度策略是什么？（重试/跳过/终止）请说明权衡。
5. 结合鲁棒性数据，分析这套系统在什么场景下会失效？如何改进？

**评分标准**：Action 与导航器理解 15 分 + 单点导航 20 分 + 多点导航 25 分 + 调度与避障 25 分 + 鲁棒性评估 15 分 = 100 分。
