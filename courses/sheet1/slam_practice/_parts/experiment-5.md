## 实验5：局部路径规划与动态避障实验（8h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/navigation/car1_navigation/config/nav2_params.yaml`（controller_server / local_costmap / behavior_server 段），未复制到 `source-codes/EXP004/exp05/`。已通过 human_waiver 放行，内容基于真实配置撰写。

**一句话读懂**：实验 3 里小车会"看地图走大路"，但路上突然滚来一个球、放下一只箱子怎么办？这节课专门练"**开车时的随机应变**"——用 DWB 局部规划器，让小车在行驶中实时躲开动态障碍，绕不过去还会自己转圈、后退重新想办法。

### 5.1 关联知识点

- 5.1.1 DWA速度窗口 > 概念 > 只考虑当前刹得住的速度组合
- 5.1.2 DWB评价函数 > 原理 > PathDist/GoalDist/BaseObstacle/RotateToGoal 加权
- 5.1.3 DWB参数 > 流程 > vx_samples/vtheta_samples/sim_time/max_vel
- 5.2.1 TEB弹性带 > 概念 > 把路径当弹性带用图优化调整
- 5.2.2 DWA vs TEB > 原理 > DWA 快而糙 / TEB 平滑可调时间
- 5.3.1 局部代价地图 > 流程 > 滚动窗口 + voxel + inflation
- 5.3.2 动态避障实验 > 流程 > 放障碍→绕行→移开→恢复
- 5.3.3 调优方向 > 原理 > 绕不过→调权重；抖→降速

### 5.2 实验目标

1. 理解 DWA/DWB 速度窗口思想与评价函数（critics）— **原理理解**
2. 理解 TEB 时间弹性带原理及其与 DWA 的差异 — **原理理解**
3. 掌握 local_costmap（滚动窗口/voxel/inflation）配置 — **流程掌握**
4. 独立完成动态避障实验并能够通过参数调优改善避障表现 — **独立完成**

### 5.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 小车C1 + COIN-D6 雷达；地图（实验 2）+ 定位（实验 4）可用 |
| OS | Ubuntu 22.04 + ROS 2 Humble |
| 核心库 | Nav2 dwb_controller、nav2_costmap_2d |
| 障碍物 | 纸箱/泡沫块（低矮安全，便于测试） |
| 主入口 | `navigation/car1_navigation/config/nav2_params.yaml`（controller_server / local_costmap 段） |

### 5.4 实验难度

- 难度: ⭐⭐⭐（综合性）
- 重点: DWB 评价函数；动态避障实验；参数调优
- 难点: 调优方向判断（绕不过/抖动/贴障碍）

### 5.5 实验现象

**快速验证流程**：

1. 启动导航：`ros2 launch car1_navigation navigation.launch.py map:=slam_map`，并用 "2D Pose Estimate" 定位
2. 下发一个**穿过房间中部**的目标点，让小车开始行驶
3. 小车行驶途中，把一个纸箱放到它正前方 1m 处
4. 观察：小车**减速 → 绕行**（离开全局路径走一段弧线）→ 绕过箱子 → 回到原路径 → 继续到达目标
5. 移开箱子再测一次：小车恢复走直线

**预期效果描述**：

- 避障时小车的速度曲线先降后升（voxel_layer 感知到障碍 → controller 减速）
- 绕行轨迹平滑（无急转弯），绕过后能重新贴合全局路径
- `ros2 topic echo /local_costmap/costmap_raw` 能看到障碍附近的代价从 0 升到 254（黑圈）
- 若障碍堵死通道，小车会停在原地转圈尝试（行为服务器介入）

### 5.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：理解DWA思想] --> B[步骤2：理解DWB评价函数]
    B --> C[步骤3：解读local_costmap]
    C --> D[步骤4：动态避障实验]
    D --> E[步骤5：参数调优]
```

---

#### 步骤1：理解 DWA 速度窗口（60min）

**知识点讲解**：

**动态窗口法（5.1.1）**
- **原理**：DWA（Dynamic Window Approach）的核心思想：**不要考虑所有可能速度，只看"当前能刹得住"的速度**。对每对 (vx, ω) 组合：
  1. 先判断它是否满足加速度限制（acc_lim）
  2. 再判断用它刹车能否在障碍前停下
  3. 通过这两关的速度组成"**动态窗口**"，在窗口内采样生成模拟轨迹
  4. 用评价函数给每条轨迹打分，选最优执行
- **白话类比**：开车时你不会考虑"200km/h 冲过去"——先看能不能刹住（动态窗口），再从敢踩的速度里挑一条最好的路线。
- **源码对应**：`nav2_params.yaml` controller_server FollowPath（L133-171）：`acc_lim_x: 1.0`、`acc_lim_theta: 1.5`（加速度限制）、`vx_samples: 20`、`vtheta_samples: 40`（窗口内采样数）。

**DWB = DWA 的 Nav2 实现**
- **原理**：本项目局部规划器 plugin 是 `dwb_core::DWBLocalPlanner`，它把 DWA 思想模块化为多个可插拔的 **critics（评价器）**，每条候选轨迹由一组 critics 加权打分。
- **源码对应**：`nav2_params.yaml` L134（plugin）与 L161（critics 列表）。

**操作步骤**：

1. 抄录 FollowPath 的速度/加速度限制参数：max_vel_x/max_vel_theta/acc_lim_x/acc_lim_theta。
2. 理解"动态窗口"：用文字描述为什么 acc_lim 决定窗口大小。
3. 思考（记录）：max_vel_x=0.3（m/s）对室内小车意味着什么？（提示：3 秒走 1 米，安全优先）

**易错点**：

- ⚠️ 以为 DWA 会考虑所有速度 → **解决**：只考虑"刹得住"的速度，这是它"安全"的根本。
- ⚠️ 混淆全局路径与局部轨迹 → **解决**：全局路径是"目标线路"（长），局部轨迹是"接下来 1.5 秒怎么走"（短，sim_time: 1.5）。

---

#### 步骤2：理解 DWB 评价函数（90min）

**知识点讲解**：

**critics 评分（5.1.2）**
- **原理**：每条候选轨迹由以下 critics 加权打分，得分越高越优先：

| critic | 作用 | 本项目权重(scale) |
|--------|------|------------------|
| PathDist | 离全局路径的横向偏差 | 32.0 |
| PathAlign | 轨迹方向与全局路径对齐程度 | 32.0 |
| GoalDist | 离目标点的距离 | 24.0 |
| GoalAlign | 轨迹方向与目标朝向对齐 | 24.0 |
| BaseObstacle | 轨迹是否撞障碍（cost 采样） | 0.02 |
| RotateToGoal | 到目标时转正的效率 | 32.0 |
| Oscillation | 惩罚来回震荡（防抖动） | - |

- **白话类比**：教练给每个候选动作打分：走偏扣分（PathDist）、太远扣分（GoalDist）、会撞墙重扣（BaseObstacle）、来回磨蹭扣分（Oscillation）——总分最高的动作被选中。
- **源码对应**：`nav2_params.yaml` L161-171（critics 列表与 scale）。

**采样与模拟（5.1.3）**
- **原理**：`vx_samples: 20`（20 个线速度采样）× `vtheta_samples: 40`（40 个角速度采样）= 最多 800 条候选轨迹；每条用 `sim_time: 1.5`（模拟未来 1.5 秒）推演是否安全。
- **源码对应**：`nav2_params.yaml` L150-154（vx_samples/vtheta_samples/sim_time）。

**操作步骤**：

1. 抄录 critics 表并标注每个权重的含义。
2. 思考题（记录）：为什么 PathDist 权重 32 远大于 BaseObstacle 的 0.02？（提示：障碍惩罚靠"撞到就算失效"的硬约束，权重只需区分"远/近"）
3. 观察：启动导航后，`ros2 topic echo /local_plan`（若发布）查看规划出的局部轨迹。

**易错点**：

- ⚠️ 权重越大越好？→ **解决**：权重是**相对关系**。PathDist 大 = 更贴全局路径；BaseObstacle 的 0.02 与 cost 值相乘后仍能否决撞墙轨迹，因为撞墙轨迹的 BaseObstacle cost 是天文数字。
- ⚠️ Oscillation critic 让人困惑 → **解决**：它专门惩罚"左一下右一下"的摆动，防止小车在障碍前原地抖。

---

#### 步骤3：解读 local_costmap（60min）

**知识点讲解**：

**局部代价地图构成（5.3.1）**
- **原理**：`local_costmap` 是跟着机器人走的 3m×3m 滚动窗口（`rolling_window: true`），只关心身边 3 米的障碍，更新频率 5Hz（比全局快，动态避障靠它）。两层：
  - **voxel_layer**：把雷达点云投成 3D 体素（`z_voxels: 16`、`max_obstacle_height: 2.0`），能在三维空间区分障碍高度
  - **inflation_layer**：把障碍向外膨胀 `inflation_radius: 0.18`，让轨迹自动与障碍保持距离
- **源码对应**：`nav2_params.yaml` L228-266（local_costmap：rolling_window、voxel_layer、inflation_layer）。

**代价地图可视化**
- **原理**：代价地图中：0=完全空闲、1-252=离障碍越近代价越高、254=障碍物、255=致命（不可入）。机器人轨迹会自动避开高代价区。
- **源码对应**：`publish_frequency: 2.0` 定期发布 costmap 话题供 RViz 显示。

**操作步骤**：

1. 抄录 local_costmap 关键参数：width/height 3、resolution 0.05、rolling_window true、inflation_radius 0.18。
2. RViz 添加 Display → By topic → /local_costmap/costmap_raw（Color 显示），观察行驶中代价地图如何跟随。
3. 在机器人旁 1m 放纸箱，观察代价地图中纸箱处出现"黑圈"（254）及周围渐变。
4. 思考（记录）：为什么局部地图窗口是 3×3 而不是整个房间？（提示：算力 + 只关心当前路况）

**易错点**：

- ⚠️ 代价地图不显示 → **解决**：确认 `always_send_full_costmap: true`（nav2_params.yaml 已设）且 RViz 话题正确。
- ⚠️ inflation 过大挡路 → **解决**：inflation_radius 0.18 已经考虑了小车半宽 0.18；调大后窄通道会判为不可行。

---

#### 步骤4：动态避障实验（90min）

**知识点讲解**：

**动态避障闭环（5.3.2）**
- **原理**：完整避障链路：雷达 → voxel_layer 标记障碍 → costmap 更新（5Hz）→ controller 发现"当前轨迹撞了"→ 重采样生成绕行轨迹 → 绕过后按 PathDist 重新贴合全局路径。全程**无需重新规划全局路径**（除非绕行太远）。
- **白话类比**：高速上遇到前方事故——你不必重新查导航（全局路径），而是现场变道绕过，再回到原车道。

**操作步骤**：

1. 启动导航并定位，下发一个长距离目标（穿过房间）。
2. 小车行驶中，把纸箱放到其**正前方约 1m**处，保持不动。记录：
   - 避障开始时机（距障碍多远减速）
   - 绕行轨迹（离开全局路径的最大横向距离）
   - 绕过后是否回到原路径
3. 重复 3 次，记录避障成功率与每次的"最小安全距离"。
4. 挑战测试：
   - **窄通道**：把两个纸箱摆成 50cm 宽通道，看能否通过（footprint 宽 36cm）
   - **突然出现**：小车直线行驶时把箱子直接放到它面前 0.5m，观察急刹与绕行
5. 全程监控：`ros2 topic echo /cmd_vel` 观察速度变化曲线。

**易错点**：

- ⚠️ 避障时撞上箱子 → **解决**：箱子离机器人太近（< 局部窗口），或速度太快刹不住；放远一点 / 降 max_vel_x。
- ⚠️ 绕过障碍后"迷路"乱转 → **解决**：PathDist 权重不足，绕行后难以回贴全局路径；调大 PathDist.scale。
- ⚠️ 箱子 0.5m 突然出现急刹 → **解决**：机器人不是无限刹车性能；`acc_lim_x` 决定了减速能力，测试时保持合理距离。

---

#### 步骤5：参数调优与 TEB 对比（90min）

**知识点讲解**：

**调优方向（5.3.3）**
- **原理**：遇到不同现象，改不同参数（每改必重启）：

| 现象 | 调优方向 |
|------|---------|
| 绕不过障碍/撞障碍 | 调大 BaseObstacle.scale 或 inflation_radius；降低 max_vel_x |
| 抖动/左右摆 | 调大 Oscillation 惩罚；降低 sim_time；降速 |
| 绕行后回不来 | 调大 PathDist.scale / PathAlign.scale |
| 贴障碍太近 | 调大 inflation_radius；调大 BaseObstacle.scale |
| 到目标不转正 | 调大 RotateToGoal.scale / GoalAlign.scale |

- **源码对应**：`nav2_params.yaml` L161-171（critics scale 调整处）。

**TEB 时间弹性带（5.2.1 + 5.2.2）**
- **原理**：TEB（Time Elastic Band）把"路径"看成一根**弹性带**，用图优化同时调整**轨迹点位置**和**到达时间**，目标函数包括：贴路径、避障碍、时间最短、速度平滑。与 DWA 差异：DWA 只模拟"眼前 1.5 秒"的轨迹（快、低算力）；TEB 优化整条局部路径（平滑、可加时间约束）。本项目默认用 DWB，TEB 是可选替代（了解原理即可）。
- **源码对应**：本项目 nav2_params.yaml 未启用 TEB（`controller_plugins: ["FollowPath"]` → DWB）；TEB 为知识扩展。

**操作步骤**：

1. 调优实验 A：把 `BaseObstacle.scale` 从 0.02 调到 0.1，重启，重复"正前方放箱"测试，记录最小安全距离变化。
2. 调优实验 B：把 `max_vel_x` 从 0.3 调到 0.2，重复测试，对比避障成功率与到达耗时。
3. 把最优参数写回 nav2_params.yaml，记录"参数 → 现象"对照表（至少 3 组）。
4. 画一张 DWA vs TEB 对比表（原理/速度/平滑度/适用场景），并说明本项目为何选 DWB。
5. 写小结：给你的小车调出一组"又快又稳"的参数，附实验数据。

**易错点**：

- ⚠️ 一次只改一个参数 → **解决**：同时改多个无法定位是哪个起了作用；每次单变量对比。
- ⚠️ 参数越"激进"越好 → **解决**：权重拉满会导致路径僵化/无法变通；调参目标是"够用且稳健"。
- ⚠️ 忘记重启 → **解决**：controller_server 参数在启动时读取，改后必须重启 navigation.launch。

### 5.7 注意事项

- ⚠️ 障碍物用**低矮纸箱/泡沫**，不要用易碎或沉重物体。
- ⚠️ 动态避障测试时**手远离小车路径**，人站在开阔侧随时准备按急停。
- ⚠️ 每次调参前记录"当前参数 → 当前现象"，便于对比与回退。
- ⚠️ 窄通道测试前确认 footprint（0.18 半宽）能通过，否则属于正常不可行。

### 5.8 实验总结

**完成成果**：

- 理解 DWA 动态窗口思想与 DWB 七大 critics 评价函数
- 理解 TEB 时间弹性带原理及与 DWA 的差异
- 掌握 local_costmap（滚动窗口/voxel/inflation）配置与可视化
- 完成动态避障实验（正前方/窄通道/突然出现）与参数调优

**技能收获**：

- 技能1：DWB critics 权重调优方法
- 技能2：代价地图可视化解读（0/254 代价分布）
- 技能3：避障实验设计（单变量对比）

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 避障撞箱 | 速度太快/距障太近 | 降 max_vel_x；放远障碍 |
| 绕行后回不来 | PathDist 权重低 | 调大 PathDist.scale |
| 行驶抖动 | Oscillation 惩罚不足 | 调大振荡惩罚；降速 |
| 贴障碍走 | inflation 太小 | 调大 inflation_radius |
| 窄通道过不去 | footprint 宽于通道 | 属正常；换宽通道 |

### 5.9 实验报告要求

**思考题**：

1. 用一句话解释"DWA 为什么只考虑刹得住的速度"？acc_lim_x 在这个判断中起什么作用？
2. 列举 DWB 的 4 个 critics 并说明各自作用；为什么 BaseObstacle 权重那么小却仍能阻止撞墙轨迹？
3. local_costmap 为什么用 3×3 滚动窗口而不是全图？voxel_layer 相比二维层有什么优势？
4. 对比 DWA/DWB 与 TEB：各自适用什么场景？本项目为什么默认选择 DWB？
5. 你调优实验中"现象→参数"的对应关系是什么？请列出至少 2 组并解释原因。

**评分标准**：DWA 原理 15 分 + DWB 评价函数 20 分 + local_costmap 配置 15 分 + 动态避障实验 30 分 + 参数调优与对比 20 分 = 100 分。
