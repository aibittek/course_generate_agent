## 实验2：基于SLAM_Toolbox的二维激光建图实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/slam/car1_slam/`，未复制到 `source-codes/EXP004/exp02/`。已通过 human_waiver 放行，内容基于 `launch/slam.launch.py`、`config/slam.yaml`、`car1_slam/map_save.py`、`car1_slam/slam_teleop.py`、`maps/slam_map.yaml`、`doc/slam_toobox_tutorial.md` 等真实源码撰写。

**一句话读懂**：这节课是整门课的第一个"高光时刻"——你将用键盘遥控小车在房间里逛一圈，然后得到一张跟户型图一样的二维地图。全程只做三件事：**启动建图 → 遥控逛圈 → 保存地图**。

### 2.1 关联知识点

- 2.1.1 slam_toolbox框架 > 概念 > Karto 图优化 SLAM：前端 Scan Match + 位姿图 + 后端 Ceres
- 2.1.2 前端ScanMatch > 原理 > 在里程计预测位姿附近搜候选，取匹配得分最高
- 2.1.3 后端图优化 > 原理 > 节点=关键帧，边=约束，Ceres 最小化残差
- 2.1.4 回环检测 > 流程 > 回到已访问区域 → 一次大修正
- 2.2.1 resolution > 概念 > 0.05 = 每格 5cm
- 2.2.2 关键帧阈值 > 流程 > minimum_travel_distance/heading 控制更新频率
- 2.2.3 mode/loop_closing > 流程 > mapping 模式 + 开启回环
- 2.3.1 slam.launch分层 > 流程 > bringup → 雷达 → [10s] slam_toolbox → RViz
- 2.3.2 键盘遥控 > 流程 > slam_teleop：w/s/a/d/空格
- 2.3.3 建图手法 > 原理 > 慢速、闭环、拐角减速
- 2.4.1 保存地图 > 流程 > map_saver_cli 产出 pgm+yaml
- 2.4.2 pgm/yaml格式 > 概念 > 255 空闲 / 0 占据 / 205 未知
- 2.5.1 验收四指标 > 流程 > 墙厚/尺寸/直角/闭环

### 2.2 实验目标

1. 理解 slam_toolbox 的图优化框架（前端匹配 + 后端优化 + 回环）— **原理理解**
2. 掌握 slam.yaml 关键参数（分辨率/关键帧阈值/回环开关）的配置方法 — **流程掌握**
3. 独立完成"启动建图 → 键盘遥控 → 保存地图 → 质量评估"全流程 — **独立完成**
4. 能够分析地图重影/旋转等常见问题并给出修正方向 — **迁移应用**

### 2.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 小车C1 + COIN-D6 激光雷达（/dev/ttyUSB1） |
| OS | Ubuntu 22.04 + ROS 2 Humble |
| 核心库 | slam_toolbox、robot_localization、nav2_map_server（保存地图用） |
| 依赖 | `source /opt/ros/humble/setup.bash` + `source ~/ros2_ws/install/setup.bash`；`colcon build --packages-select car1_slam car1_bringup car1_peripherals` |
| 主入口 | `slam/car1_slam/launch/slam.launch.py`（建图）、`car1_slam/slam_teleop.py`（遥控）、`car1_slam/map_save.py`（保存） |

### 2.4 实验难度

- 难度: ⭐⭐（设计性）
- 重点: 建图全流程；关键参数对地图质量的影响
- 难点: 参数与建图手法的配合（阈值大小、遥控速度）

### 2.5 实验现象

**快速验证流程**（建议在 2m×2m 以上空旷室内）：

1. 启动建图：`ros2 launch car1_slam slam.launch.py`（自动带起底盘 + 雷达 + slam_toolbox + RViz）
2. 新终端启动遥控：`ros2 run car1_slam slam_teleop`（或 `python3 src/xflz_eai_car1/slam/car1_slam/car1_slam/slam_teleop.py`）
3. 用 w/a/s/d 缓慢遥控小车沿墙走一圈，回到起点
4. RViz 中看到地图随移动逐渐"长"出来：墙成单线、房间轮廓闭合
5. 保存地图：`ros2 run car1_slam map_save map_01`，在 `slam/car1_slam/maps/` 下看到 map_01.pgm + map_01.yaml

**预期效果描述**：

- RViz 左侧 Map 显示实时占据栅格（白色=空闲、黑色=墙、灰色=未知）
- 小车位置显示绿色箭头，跟随地图一起走
- 地图质量：墙为单线、房间角度接近直角、绕一圈后回到起点墙线不错开
- 保存的 map_01.pgm 用图片查看器打开就是一张清晰的"户型图"

### 2.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：理解slam_toolbox框架] --> B[步骤2：解读slam.yaml参数]
    B --> C[步骤3：启动建图与遥控]
    C --> D[步骤4：保存与加载地图]
    D --> E[步骤5：建图质量评估]
```

---

#### 步骤1：理解 slam_toolbox 框架（40min）

**知识点讲解**：

**图优化 SLAM（2.1.1 + 2.1.2 + 2.1.3）**
- **原理**：slam_toolbox 把建图拆成"前端"和"后端"两部分：
  - **前端（Scan Matching）**：每来一帧激光扫描，都在"里程计预测的位置附近"（一个搜索窗口）试着把扫描往各个方向放一放，看哪个位置与已有地图最吻合，就认为机器人在这里。对应参数：`correlation_search_space_dimension: 0.5`（搜索窗 ±0.5m）、`correlation_search_space_resolution: 0.01`（步进 1cm）。
  - **位姿图（Pose Graph）**：把每个"关键帧"（关键位置的扫描+位姿）记成一个**节点**，相邻关键帧之间的相对运动记成**边**（约束）。
  - **后端（图优化）**：攒了一批节点和边之后，用 Ceres 求解器（`ceres_trust_strategy: LEVENBERG_MARQUARDT`）把所有节点的位置重新调一调，让所有约束都尽量满足——把累积的小误差"摊平"。
- **白话类比**：前端=每走一步都"对对齐"（局部对正）；后端=走累了回头"重新排排站"（全局优化）；回环=绕了一圈发现"这墙我画过"（见 2.1.4）。
- **源码对应**：`config/slam.yaml` L5-10 是后端求解器配置；L48-52 是前端搜索窗口；L30-43 是关键帧与 scan 接收配置。

**回环检测（2.1.4）**
- **原理**：机器人走了一圈回到出发点时，系统在**历史关键帧**里搜索"有没有和现在这帧长得像的"（分支定界搜索，`loop_search_space_dimension: 8.0`）。找到了（匹配响应超过阈值，`loop_match_minimum_response_fine: 0.45`）就建立一条"回环约束"，然后触发一次全局优化——这一次优化能把整条轨迹的累积漂移一次性抹掉。**所以建图一定要走闭环路径**。
- **源码对应**：`slam.yaml` L54-64 回环检测参数（`do_loop_closing: true`）。

**操作步骤**：

1. 打开 `slam.yaml`，分别找到：前端搜索窗口、后端求解器、回环检测、关键帧阈值 四组参数，抄到笔记。
2. 画出 slam_toolbox 数据流图：/scan + odom TF → 前端匹配 → 位姿图 → 后端优化 → /map。
3. 用一句话向同桌解释：为什么"绕一圈回到起点"能让地图突然变准？

**易错点**：

- ⚠️ 以为 SLAM 只靠雷达 → **解决**：还要吃里程计 TF（odom→base_footprint），由 bringup 的 EKF 提供；雷达和里程计都准，地图才准。
- ⚠️ 回环检测不是必然触发 → **解决**：触发需要"现在这帧"和"历史某帧"足够像，路径重叠太少就检测不到。

---

#### 步骤2：解读 slam.yaml 关键参数（40min）

**知识点讲解**：

**分辨率（2.2.1）**
- **原理**：`resolution: 0.05` 表示地图每格 5cm。格子越小地图越精细（细节多），但地图文件越大、每次更新计算越重。室内导航 0.05 是黄金值。
- **源码对应**：`slam.yaml` L23。

**关键帧阈值（2.2.2）**
- **原理**：不是每帧扫描都存成关键帧，而是"走得够远了才存"。`minimum_travel_distance: 0.01`（走了 1cm）或 `minimum_travel_heading: 0.02`（转了 0.02rad）才触发新关键帧。**阈值太大**→关键帧太少→地图粗糙、回环失败；**阈值太小**→关键帧太多→算力浪费。
- **源码对应**：`slam.yaml` L40-41。文档中特别注释：没有这两个阈值 slam_toolbox 会退回 0.5m/0.5rad 默认值，地图只有大动作才更新。

**模式与回环开关（2.2.3）**
- **原理**：`mode: mapping` 表示建图模式（导航定位时改为 localization）；`map_update_interval: 0.1` 表示地图每 0.1s 刷新一次；`do_loop_closing: true` 开启回环检测。
- **源码对应**：`slam.yaml` L19、L22、L58。

**操作步骤**：

1. 把下面参数抄入笔记并标注含义：

| 参数 | 值 | 含义 |
|------|-----|------|
| resolution | 0.05 | 每格 5cm |
| mode | mapping | 建图模式 |
| map_update_interval | 0.1 | 地图刷新周期 0.1s |
| minimum_travel_distance | 0.01 | 位移 1cm 触发新关键帧 |
| minimum_travel_heading | 0.02 | 转角 0.02rad 触发新关键帧 |
| do_loop_closing | true | 开启回环检测 |
| max_laser_range | 12.0 | 激光截断到 12m |

2. 思考（记录）：若把 minimum_travel_distance 改成 0.5，建图会怎样？（提示：地图只在走够 0.5m 才更新，细节全丢）

**易错点**：

- ⚠️ 改参数后不生效 → **解决**：参数在节点启动时读取，改 slam.yaml 后**重启 slam.launch**；不要在运行时 `ros2 param set` 期望地图立刻变。

---

#### 步骤3：启动建图与遥控（60min）

**知识点讲解**：

**slam.launch.py 分层启动（2.3.1）**
- **原理**：一行命令按顺序拉起：① `bringup.launch.py`（底盘驱动 + robot_state_publisher + EKF 里程计）→ ② `lidar.launch.py`（COIN-D6 雷达 /scan）→ ③ **延迟 10s** 才启动 slam_toolbox（等 odom/TF/scan 稳定，避免刚上电数据抖动）→ ④ RViz。
- **源码对应**：`launch/slam.launch.py` L36-59：

```python
# 3. slam_toolbox, delayed 10s to let odom / TF / scan stabilize.
slam_node = TimerAction(
    period=10.0,
    actions=[Node(package='slam_toolbox', executable='sync_slam_toolbox_node',
                  name='slam_toolbox', parameters=[slam_config], output='screen')])
```

**键盘遥控（2.3.2）**
- **原理**：`slam_teleop.py` 把键盘按键转成 `/cmd_vel` 速度话题：w=前进 0.2m/s、s=后退、a=左转 0.5rad/s、d=右转、空格=停止。它用 termios 读取原始按键，**必须在终端里直接运行**（不能在后台）。
- **源码对应**：`car1_slam/slam_teleop.py` L16-34（按键映射）、L79-99（发布 Twist）。

**建图手法（2.3.3）**
- **原理**：地图质量 = 算法 × **手法**。规范：线速度 ≤0.3m/s、角速度 ≤1.0rad/s（太快会运动畸变）、拐角处减速、**尽量走闭环**、避免长走廊无特征区域快速直行。
- **白话类比**：就像用手机全景拍照——转太快、走得晃，拍出来就是糊的、断的。

**操作步骤**：

1. 终端 1 启动建图：
   ```bash
   source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash
   ros2 launch car1_slam slam.launch.py
   ```
   观察日志：先看到 bringup 各节点，约 10s 后出现 `slam_toolbox` 启动日志（`Registering sensor`、`SLAM ... started`）。
2. 终端 2 启动遥控（**必须真终端**，非 IDE 内嵌）：
   ```bash
   ros2 run car1_slam slam_teleop
   ```
   或源码直跑：`python3 ~/ros2_ws/src/xflz_eai_car1/slam/car1_slam/car1_slam/slam_teleop.py`
3. RViz 确认：Map 显示、LaserScan 显示（Reliability 设为 Best Effort，见易错点）。
4. 遥控小车**低速**沿房间四周走一圈，回到起点。中途在墙角停留 1-2s 让扫描充分重叠。
5. 监控数据：
   ```bash
   ros2 topic hz /scan          # ~10Hz
   ros2 run tf2_ros tf2_echo odom base_footprint   # 观察里程计
   ```

**易错点**：

- ⚠️ RViz 不显示激光点 → **解决**：LaserScan Display 的 Reliability Policy 改为 **Best Effort**（雷达 QoS 是 Best Effort）。
- ⚠️ 遥控无反应 → **解决**：确认 slam_teleop 在真终端运行；先按一下任意方向键激活，再操作。
- ⚠️ 启动 10s 内地图不动 → **解决**：正常！slam_toolbox 延迟 10s 启动，等日志出现再开始动。
- ⚠️ 走太快地图扭曲 → **解决**：降速，角速度控制在 1.0rad/s 以内（遥控 a/d 自带 0.5rad/s 很安全）。

---

#### 步骤4：保存与加载地图（40min）

**知识点讲解**：

**保存地图（2.4.1）**
- **原理**：slam_toolbox 建完图后，地图在内存里（话题 /map）。`map_save.py` 节点本质是调用 `nav2_map_server` 的 `map_saver_cli` 把 /map 写成文件。产出两个文件：`.pgm`（灰度位图）+ `.yaml`（元数据）。
- **源码对应**：`car1_slam/map_save.py` L27-31（调用 map_saver_cli）；`maps/slam_map.yaml` 是已保存的示例元数据。

**地图文件格式（2.4.2）**
- **原理**：`.pgm` 中 **255=空闲（白）**、**0=占据（黑）**、**205=未知（灰）**。`.yaml` 记录：image 文件名、resolution（每格米数）、origin（地图左下角在 map 系的位置）、occupied_thresh/free_thresh（灰度转占据/空闲的阈值）。
- **源码对应**：`maps/slam_map.yaml`：

```yaml
image: slam_map.pgm
mode: trinary
resolution: 0.05
origin: [-0.381, -0.482, 0]
occupied_thresh: 0.65
free_thresh: 0.25
```

**操作步骤**：

1. 保存地图：
   ```bash
   ros2 run car1_slam map_save map_01
   # 或手动：
   ros2 run nav2_map_server map_saver_cli -f map_01 --ros-args -p map_subscribe_transient_local:=true
   ```
2. 确认产物：`ls ~/ros2_ws/src/xflz_eai_car1/slam/car1_slam/maps/map_01.*`
3. 用图片查看器打开 map_01.pgm，对照实际房间检查：墙是否单线、房间形状对不对。
4. 查看 map_01.yaml，记录 resolution 和 origin。
5. 检查地图是否能被导航加载（为实验 3 准备）：`ros2 launch car1_navigation navigation.launch.py map:=map_01`（可先不展开，下一实验详解）。

**易错点**：

- ⚠️ map_save 报"没有话题" → **解决**：保存前确认 slam_toolbox 在运行且 /map 在发布；`ros2 topic hz /map` 检查。
- ⚠️ 地图没建完就保存 → **解决**：保存前先让小车绕完整一圈并回到起点，触发一次回环优化再保存。

---

#### 步骤5：建图质量评估（40min）

**知识点讲解**：

**验收四指标（2.5.1）**
- **原理**：用尺子和地图工具实测（文档 `slam_toobox_tutorial.md` 第 8 节）：

| 指标 | 方法 | 合格标准 |
|------|------|---------|
| 墙体厚度 | 地图上量同面墙的双线间距 | < 0.1m（接近真实墙厚） |
| 尺寸误差 | 地图测距 vs 卷尺实测 | < 2% |
| 直角度 | 地图量墙角夹角 | 90° ± 2° |
| 闭环误差 | 回起点时位置/航向误差 | 位置 < 0.1m、航向 < 5° |

**操作步骤**：

1. 用卷尺量房间长宽（比如 3m × 2m），再在地图（RViz 的 Measure 工具或图片缩放比）量同一尺寸，算误差百分比。
2. 观察墙线：用图片查看器放大 map_01.pgm，检查是否有"双墙/重影"。
3. 分析报告：若出现重影，从下面"常见问题"中定位原因并写修正方案（不要求本次全部修复）。
4. 结论写入实验报告，附地图截图。

**易错点**：

- ⚠️ 地图旋转/双墙 → **解决**：多为里程计航向不准（IMU scale 错、打滑）。检查 `slam_toobox_tutorial.md` 3.4 节的历史问题表。
- ⚠️ 墙特别厚（>0.1m）→ **解决**：多为遥控太快/转弯太猛，重跑时降速。
- ⚠️ 长走廊地图"发飘" → **解决**：走廊无特征，前端匹配易退化；放慢速度或贴墙走，保持更多重叠。

### 2.7 注意事项

- ⚠️ **建图前检查电量**，避免半路断电地图丢失。
- ⚠️ 遥控全程低速（角速度 ≤1.0rad/s），防止运动畸变与撞墙。
- ⚠️ 建图完成立即保存地图，再停止 launch。
- ⚠️ 停止顺序：先 Ctrl+C 遥控，再 Ctrl+C slam.launch；异常退出可用 `pkill -f slam_teleop` 兜底。
- ⚠️ 地图文件命名别用中文，导航加载路径是硬编码拼接的（`map_name + '.yaml'`）。

### 2.8 实验总结

**完成成果**：

- 理解 slam_toolbox 前端匹配 / 后端图优化 / 回环检测三层机制
- 掌握 slam.yaml 关键参数（分辨率/关键帧阈值/回环）的配置
- 独立完成"启动 → 遥控逛圈 → 保存地图"全流程，得到一张可用地图
- 学会用四指标评估地图质量并定位常见问题

**技能收获**：

- 技能1：一键启动建图系统（slam.launch.py）
- 技能2：键盘遥控与建图手法（慢速+闭环）
- 技能3：地图保存（pgm/yaml）与质量评估

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| RViz 无激光 | QoS 不匹配 | LaserScan Display → Reliability = Best Effort |
| 地图不更新 | 参数未生效/速度太快 | 改 slam.yaml 后重启；降速重跑 |
| 地图双墙 | 里程计航向漂移 | 检查 IMU/EKF（见技术文档 3.4） |
| 回环不触发 | 路径不闭合/阈值严 | 走闭环；调低 response 阈值 |
| 保存失败 | /map 未发布 | 确认 slam 在跑，`ros2 topic hz /map` |

### 2.9 实验报告要求

**思考题**：

1. 前端 Scan Matching、后端图优化、回环检测三者各解决什么问题？为什么说"回环检测"是消除累积漂移的关键？
2. `minimum_travel_distance: 0.01` 的作用是什么？把它改成 0.5 会带来什么后果？
3. 为什么建图要求"慢速 + 闭环路径"？结合激光运动畸变与回环触发条件分析。
4. map_01.yaml 中 `resolution: 0.05` 与 `origin` 的含义是什么？导航加载时如何被使用？

**评分标准**：slam_toolbox 框架理解 20 分 + 参数解读 20 分 + 建图全流程操作 30 分 + 地图保存与质量评估 20 分 + 报告与思考题 10 分 = 100 分。
