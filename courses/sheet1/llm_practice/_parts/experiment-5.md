# 实验5：具身智能工厂--视觉自适应装货集成测试（8h）

> **源码**：`ros2_ws/src/xflz_eai_car1/app/eai_factory/`
> **主命令**：`ros2 launch eai_factory eai_factory.launch.py start_voice:=false`
> **覆盖模块**：N-vision 视觉节点（`vision_node.py`）→ N-grasp 抓取节点（`grasp_node.py`）→ N2 调度器（`scheduler_node.py`）
> **测试用例**：`docs/08_视觉测试用例.md`（TV1~TV3）+ `docs/09_抓取测试用例.md`（TG1~TG5）

### 5.1 关联知识点

- 4.1.1 AprilTag > 概念 > tag36h11 编码图案，tag_id/tag_size/tag_family 可配置
- 4.1.2 PnP 位姿 > 原理 > 2D 角点 → 相机坐标系 6DOF 位姿（solvePnP 解算）
- 4.1.3 TF 变换 > 原理 > camera_depth_optical_frame → base_link 变换链定位到机械臂系
- 4.2.1 双模式抓取 > 概念 > load 视觉抓取（vision=true）/ sort·palletize 固定点位（vision=false）
- 4.2.2 抓取序列 > 流程 > 移观察位→检测→TF→set_pick_target→pick→place→回work
- 4.2.3 pick_offset 补偿 > 原理 > pick_offset_x/y/z 修正手眼标定/定位系统性偏差

### 5.2 实验目标

1. 掌握 AprilTag 检测原理（编码图案、detector 配置、角点提取）与 PnP 位姿解算 — **原理理解**
2. 掌握视觉抓取完整链路：移观察位→检测→TF 变换→set_pick_target→pick→place→回 work — **流程掌握**
3. 理解双模式 confirm 机制（debug 需人工确认 / production 全自动）并独立完成装货抓取测试 — **独立完成**
4. 能够通过调优 pick_offset 与 observe_pose/place_pose 修正抓取定位偏差，验证夹爪到位精度 — **迁移应用**

### 5.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱 B2 / 机器人小车 C1（5DOF 机械臂，总线舵机）+ HP60C 深度相机 + AprilTag 标签（tag36h11，id=3） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10；vision/grasp 节点用 ros2_venv（`/home/iflytek/ros2_venv/bin/python3`，cv2 4.11 新 ArUco API） |
| 核心库 | rclpy、cv2 4.11（aruco 模块）、cv_bridge、numpy、tf2_ros、tf2_geometry_msgs |
| 相机话题 | 订阅 `/ascamera_hp60c/camera_publisher/rgb0/image` 与 depth0/camera_info |
| 主入口 | `eai_factory.launch.py`（start_voice:=false 省内存模式） |

### 5.4 实验难度

- 难度: ⭐⭐⭐
- 重点: AprilTag PnP 位姿解算、TF 变换链、视觉抓取序列与双模式 confirm
- 难点: 手眼标定偏差补偿（pick_offset 调优）；检测-变换-抓取链路的问题定位

### 5.5 实验现象

**快速验证流程**：

1. 省内存启动：`ros2 launch eai_factory eai_factory.launch.py start_voice:=false`，观察 vision/grasp 节点启动日志
2. 将 tag_id=3 的 AprilTag 标签放到装货区相机视野内，`ros2 topic echo /eai_factory/vision/detected` 输出 `data: true`
3. `ros2 run rqt_image_view rqt_image_view /eai_factory/vision/debug_image` 看到标签被绿色框出、角点标红、显示 x/y/z 坐标文字
4. 触发装货：`ros2 service call /eai_factory/start_load std_srvs/srv/Trigger`，观察机械臂 移观察位→检测→TF→set_pick_target→pick→place 完整链路
5. 修改 `grasp.pick_offset_x/y/z` 验证夹爪到位精度变化

**预期效果描述**：

- 相机内参打印 `fx=592.9 fy=593.1 cx=335.4 cy=237.7`（docs/08 L27），标签稳定检测
- target 话题输出相机系 PoseStamped（z 约 0.19 = 19cm），debug 图带绿色轮廓框+红点+坐标文字
- 机械臂自动完成装货抓取；debug 模式下停在"目标已存"等待 confirm
- 偏移调优后夹爪准确覆盖标签中心，重复 5 次抓取成功率 ≥ 4/5

### 5.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：启动视觉与抓取] --> B[步骤2：AprilTag检测]
    B --> C[步骤3：装货抓取链路]
    C --> D[步骤4：pick_offset参数调优]
    D --> E[步骤5：测试用例执行]
```

---

#### 步骤1：启动视觉与抓取（60min）

**知识点讲解**：

**双模式抓取（4.2.1）**
- **原理**：grasp 节点按任务区分两种抓取模式：`vision=true`（load 装货）走视觉抓取——先移观察位、检测 AprilTag、TF 变换、再 pick/place（调用 arm_controller 的 pick/place 服务）；`vision=false`（sort/palletize）走固定点位抓取——直接用配置的抓取点，不依赖相机。任务类型由 yaml `grasp.tasks.<task>.vision` 决定（yaml L80/L84/L88），grasp 节点启动时统一加载到 `task_poses` 字典（`grasp_node.py` L89-94）。视觉抓取链路依赖相机与 TF，固定抓取不依赖。
- **源码对应**：`grasp_node.py` L89-94（task_poses 加载）、L246-306（start_grasp 按 vision 分支）；`eai_factory.yaml` L79-90（三任务配置）

```python
# grasp_node.py L90-94：按任务加载 observe/place 姿态与 vision 标志
for task in ('load', 'sort', 'palletize'):
    ob = self.get_parameter(f'grasp.tasks.{task}.observe_pose').value
    pl = self.get_parameter(f'grasp.tasks.{task}.place_pose').value
    vis = self.get_parameter(f'grasp.tasks.{task}.vision').value
    self.task_poses[task] = (tuple(ob), tuple(pl), bool(vis))
```

**操作步骤**：

1. 省内存启动（跳过语音/LLM，launch L77-78）：
   ```bash
   source /opt/ros/humble/setup.bash
   source /home/iflytek/ros2_ws/install/setup.bash
   ros2 launch eai_factory eai_factory.launch.py start_voice:=false
   ```
2. 确认节点与接口（docs/09 L19-24）：
   ```bash
   ros2 node list          # 应看到 eai_factory_grasp / eai_factory_vision / arm_controller 等
   ros2 service list | grep grasp
   # 应看到 /eai_factory/grasp/start /confirm /abort
   ```
3. 观察 vision 启动日志（docs/08 L25-28）：`AprilTag detector ready (OpenCV 4.11.0)` → `eai_factory_vision started | family=tag36h11 id=3 size=25mm`
4. rqt 调试画面（launch 默认 start_viz:=true 自动拉起，也可手动）：
   ```bash
   ros2 run rqt_image_view rqt_image_view /eai_factory/vision/debug_image
   ```

**易错点**：

- ⚠️ 检测不到 AprilTag → 确认 vision 节点用 venv python 启动（cv2 4.11 新 API，系统 python 4.5.4 旧 API 检测不可靠，docs/08 L30-31）；launch L123-129 已配置 venv python，不要手动替换
- ⚠️ `rqt_image_view` 无图像 → 相机话题未发布或 vision 未订阅到；`ros2 topic list | grep ascamera` 检查相机，确认 `vision.rgb_topic` 配置（yaml L61）

---

#### 步骤2：AprilTag 检测与 PnP 位姿（90min）

**知识点讲解**：

**AprilTag 编码（4.1.1）**
- **原理**：AprilTag 是类 QR 的方形二维码，tag36h11 表示 36bit 编码、最小汉明距离 11（抗误检强）。检测流程：灰度图 → ArucoDetector（DICT_APRILTAG_36h11）提取候选四边形角点 → 按 tag_id 过滤目标标签。`tag_size=0.025`（米）是编码区边长，直接决定 PnP 解算的尺度；`tag_id=3` 用于多标签场景下选目标。OpenCV 4.11 的新 API `cv2.aruco.ArucoDetector` 配合角点亚像素细化（CORNER_REFINE_SUBPIX）检测更稳。
- **源码对应**：`vision_node.py` L65-72（参数声明）、L107-139（_init_detector）、L181-200（_detect）；`eai_factory.yaml` L57-63（vision 段）

```python
# vision_node.py L194-199：按 tag_id 过滤目标标签
for i, tag_id in enumerate(ids.flatten()):
    if int(tag_id) != self._tag_id:
        continue
    corners = corners_list[i].reshape(4, 2).astype(np.float32)
    pose = self._solve_pnp(corners)
    return pose, corners
```

**PnP 位姿解算（4.1.2）**
- **原理**：PnP（Perspective-n-Point）利用"已知 3D 点 + 对应 2D 投影点 + 相机内参"恢复物体位姿。标签四角点在标签坐标系下的 3D 坐标（以 tag_size/2 构造，`vision_node.py` L204-210）与图像上检测到的 2D 角点建立对应，`cv2.solvePnP(..., SOLVEPNP_IPPE_SQUARE)` 解出旋转向量 rvec 与平移向量 tvec（L217-219），再经 Rodrigues 转旋转矩阵、Shepperd 法转四元数（L222-223），得到标签中心在相机光轴系（camera_depth_optical_frame）下的 6DOF 位姿并发布 /eai_factory/vision/target。
- **源码对应**：`vision_node.py` L202-233（_solve_pnp）、L154-179（_rgb_cb 发布 detected/target/debug_image）
- **公式/配图说明**：透视投影模型 s·[u,v,1]ᵀ = K·[R|t]·[X,Y,Z,1]ᵀ，其中 K=[[fx,0,cx],[0,fy,cy],[0,0,1]] 为内参矩阵（fx=592.9 等，`_info_cb` L141-152），[R|t] 即标签坐标系→相机坐标系的位姿；tag_size 是 3D 点的物理尺度，解算距离的精度与标签尺寸、内参标定误差强相关。

**操作步骤**：

1. 终端 2 监听检测状态与位姿（docs/08 TV1）：
   ```bash
   ros2 topic echo /eai_factory/vision/detected
   ros2 topic echo /eai_factory/vision/target
   ```
2. 将 tag_id=3 的标签放在装货区相机视野内（正对相机、距离约 15~25cm），确认 detected 输出 `data: true`、target 输出相机系 PoseStamped（z 约 0.19 = 19cm，docs/08 L60）
3. 在 rqt 调试画面观察绿色轮廓框 + 4 个红点角点 + 左上角坐标文字（`_draw_debug`，L235-251）
4. 无标签验证（docs/08 TV2）：移开标签 → detected 输出 `data: false`，target 不发布，画面显示 "TAG NOT FOUND"
5. 缓慢移动标签，观察 target 坐标实时跟随变化（~25Hz 发布）

**易错点**：

- ⚠️ 检测到但位姿跳变 → 标签被遮挡/反光/角度过斜；IPPE_SQUARE 要求标签近似正对相机；调整标签姿态与光照
- ⚠️ tag_size 设错 → 位姿尺度全错（如 z 距离翻倍），抓取必然失败；标签实际边长 25mm 时保持 `tag_size: 0.025`（yaml L59）
- ⚠️ debug 图一直 "TAG NOT FOUND" → 相机内参未就绪（`_info_cb` 未收到 camera_info）；确认 depth0/camera_info 话题发布（yaml L62）

---

#### 步骤3：装货抓取链路（120min）

**知识点讲解**：

**TF 变换（4.1.3）**
- **原理**：视觉解算出的位姿在相机系（camera_depth_optical_frame），而机械臂运动在 base_link 系，两者必须通过 TF 树连接。`_to_base_link`（`grasp_node.py` L308-327）调用 `lookup_transform(base_link, camera_depth_optical_frame)` 查询两坐标系间变换，再用 `do_transform_pose` 把标签位姿变换到 base_link。TF 树由相机外参标定（相机相对机械臂底座的安装位姿）提供；若手眼标定不准，抓取点会产生系统性偏移——这正是步骤 4 pick_offset 补偿的意义。
- **源码对应**：`grasp_node.py` L97-98（TF Buffer/Listener）、L286-292（TF 调用）、L308-327（_to_base_link）
- **公式/配图说明**：p_base = T_base←camera · p_camera。T 为 4×4 齐次变换矩阵（旋转+平移），TF 库按"相机帧 → 中间帧 → base_link"的链式关系自动累积；链上任一环缺失（如相机外参未发布）都会导致查找失败并中止抓取。

**抓取序列（4.2.2）**
- **原理**：视觉抓取八步序列：① 发布 target_pose 移到 observe_pose（装货区观察位，yaml L81）→ ② 等机械臂到位（move_delay=3.0s）→ ③ 取最新视觉目标 → ④ TF 转到 base_link → ⑤ 按模式处理（debug：set_pick_target 存目标等 confirm；production：直接 pick）→ ⑥ 移到 place_pose → ⑦ place → ⑧ go_work 回 work（`start_grasp` L246-306 + `_do_pick` L382-411）。`set_pick_target`（L352-380）只发布抓取目标不移动机械臂，由 arm_controller 在 pick 时用；视觉路径 pitch 固定 180°（夹爪朝下，L45 GRASP_PITCH）。
- **源码对应**：`grasp_node.py` L267-271（移观察位）、L281-283（检测确认）、L295-306（双模式分支）、L382-411（_do_pick）

```python
# grasp_node.py L295-306：debug / production 双模式分支
if self.mode == 'debug':
    # store target, wait for confirm
    self._set_pick_target(base_pose)
    self._grasp_state = 'awaiting_confirm'
    self._latest_grasp_pose = base_pose
    self.get_logger().info('DEBUG: target stored. Call /eai_factory/grasp/confirm to pick.')
    return False  # wait for confirm service
else:
    # release: pick immediately
    self._grasp_state = 'grasping'
    self._do_pick(base_pose)
    return True
```

**操作步骤**：

1. 确认标签在视野（detected=true），触发装货任务（经 N2 调度器路由）：
   ```bash
   ros2 service call /eai_factory/start_load std_srvs/srv/Trigger
   ```
2. 核对链路日志（docs/09 TG1）：
   ```
   Moved to observe pose, waiting for arm to settle...   ← ①移观察位
   Grasp target in base_link: (x, y, z)                   ← ③④TF
   set_pick_target (no move): (...) pitch=180.0°          ← ⑤存目标（含偏移）
   DEBUG: target stored. Call /eai_factory/grasp/confirm to pick.
   ```
3. debug 模式人工确认（docs/09 TG2）：
   ```bash
   ros2 service call /eai_factory/grasp/confirm std_srvs/srv/Trigger
   ```
4. 核对后续日志：`pick OK` → 移到放置位 → `place OK` → `go_work OK` → `=== grasp-place sequence done ===`
5. 双模式对比：把 `config/eai_factory.yaml` 的 `mode` 改为 `debug`（yaml L7）重启后体验 confirm 停等；改回 `production`（默认）则全自动无需确认

**易错点**：

- ⚠️ `No vision target detected — aborting grasp` → 触发时标签不在视野或 detected 为 false；先移开遮挡物，确认 detected=true 再触发
- ⚠️ `TF camera->base_link failed — aborting` → TF 树缺相机外参帧；`ros2 run tf2_tools view_frames` 检查 camera_depth_optical_frame 到 base_link 的链路
- ⚠️ 触发 start_load 后机械臂不动 → 确认 scheduler 与 grasp 服务就绪（`ros2 service list | grep grasp`）；scheduler 会自动 2s 重试（`scheduler_node.py` L136-144），等待或查 grasp 日志
- ⚠️ confirm 返回 `not awaiting confirm` → 模式是 production 或状态已非 awaiting_confirm（如已超时/被打断）；用 `/eai_factory/grasp/abort` 重置（docs/09 TG3）

---

#### 步骤4：pick_offset 参数调优（120min）

**知识点讲解**：

**pick_offset 补偿（4.2.3）**
- **原理**：手眼标定误差、相机安装偏差、机械臂装配误差会叠加成抓取点的系统性偏移（每次都偏同一方向、同一大小）。`grasp.pick_offset_x/y/z`（base_link 系，米）在 set_pick_target 时直接加到视觉解算的目标坐标上（`_set_pick_target` L360-371），实现一次性修正。base_link 约定：+X 前、+Y 左、+Z 上（yaml L74）。当前实测值 x=+0.015（向前 15mm）、y=-0.010（向右 10mm）、z=+0.023（向上 23mm）（yaml L75-77）。注意偏移只加在视觉抓取路径，固定点位抓取不加偏移（手动打点已含姿态）。
- **源码对应**：`grasp_node.py` L69-71（参数声明）、L80-86（读取+日志）、L352-380（_set_pick_target 加偏移）；`eai_factory.yaml` L75-77
- **公式/配图说明**：p_target = p_vision_base + [pick_offset_x, pick_offset_y, pick_offset_z]ᵀ。调优逻辑：若夹爪实际落点偏左 5mm，则增大 pick_offset_y 5mm（+Y 左）；若偏高则减小 z。判定"偏差方向"以 set_pick_target 日志坐标与实际落点对比。

```python
# grasp_node.py L360-371：视觉抓取目标叠加偏移
if vision:
    off = (self.pick_offset_x, self.pick_offset_y, self.pick_offset_z)
    if pitch is None:
        pitch = self.GRASP_PITCH
...
msg.pose.position.x = base_pose.pose.position.x + off[0]
msg.pose.position.y = base_pose.pose.position.y + off[1]
msg.pose.position.z = base_pose.pose.position.z + off[2]
```

**操作步骤**：

1. 观察当前偏移日志（`抓取偏移补偿已启用: dx=15.0mm, dy=-10.0mm, dz=23.0mm`，L84-86）
2. 动态微调（不重启，docs/09 TG5）：
   ```bash
   ros2 param set /eai_factory_grasp grasp.pick_offset_y -0.015
   ```
3. 用 `ros2 param get /eai_factory_grasp grasp.pick_offset_y` 确认参数生效，重复装货抓取，观察机械臂落点变化
4. 系统性调优流程：固定标签位置，连续抓取 3 次记录落点偏差 → 按偏差反向修正 pick_offset → 再抓 3 次验证 → 直至夹爪准确覆盖标签中心
5. 将最终值写回 `config/eai_factory.yaml` 的 pick_offset_x/y/z，重启确认
6. （进阶）观察位调优：修改 `grasp.tasks.load.observe_pose`（yaml L81）改变观察距离，记录不同距离下的检测稳定性与精度

**易错点**：

- ⚠️ z 方向双重补偿 → 注意 N-grasp `pick_offset_z` 与 arm 控制器 `gripper_depth` 可能叠加（docs/09 L159 已确认的关键认知），抓取偏高需先判断是哪一层补偿
- ⚠️ 动态 param set 只影响运行中的节点，重启后失效 → 最终值必须写回 yaml
- ⚠️ 偏移调大后机械臂撞物 → 每次只改一个方向 5~10mm，先抬升（z）再横向（x/y），小步验证

---

#### 步骤5：测试用例执行（90min）

**知识点讲解**：

**检测-抓取链路综合排障（4.2.2）**
- **原理**：视觉装货是"检测→变换→执行"三段式管线，故障定位必须分段：先验 detected（检测层）→ 再验 target 坐标与 TF（变换层）→ 最后验 pick/place 服务（执行层）。docs/08 与 docs/09 用例覆盖这三层：TV1/TV2 验证检测、TG1/TG2 验证抓取序列、TG3 验证状态重置、TG4 验证任务切换、TG5 验证偏移。任务切换用 `/eai_factory/grasp/set_task` 话题（docs/09 TG4），调度器在路由前也会发 set_task 确保 grasp 用对姿态（`scheduler_node.py` L145-148）。
- **源码对应**：`scheduler_node.py` L129-152（_trigger_grasp 先 set_task 再 start）；`docs/09` TG1~TG5；`docs/08` TV1~TV3

**操作步骤**：

1. 依次执行 docs/08 用例：TV1 AprilTag 检测（记录 detected/target 数据）、TV2 无目标、TV3 调试图像
2. 依次执行 docs/09 用例：TG1 触发抓取、TG2 确认继续、TG3 中止/重置、TG4 任务切换、TG5 抓取偏移补偿
3. 每次抓取记录：目标坐标（相机系+base_link 系）、set_pick_target 坐标、夹爪实际落点偏差、成功率
4. 整理数据表：不同 pick_offset 组合下的抓取偏差与成功率，形成调优结论

**易错点**：

- ⚠️ 用例间状态残留 → 一次抓取未完成就触发下一次会返回 `busy`（`_start_cb` L210-213 串行保护）；等 `=== grasp-place sequence done ===` 或先 `/eai_factory/grasp/abort` 重置
- ⚠️ set_task 与 start 竞态 → 调度器用 DDS 同链路 FIFO 保证 set_task 先于 start 处理（`scheduler_node.py` L133-134）；手动测试时先 `ros2 topic pub -1 /eai_factory/grasp/set_task` 再 start

### 5.7 注意事项

- ⚠️ 实机抓取前先空跑观察位/放置位轨迹，确认路径无干涉；机械臂动作中手远离工作区
- ⚠️ 相机与标签距离保持 15~25cm（z≈0.19m），过近过远都会降低 PnP 精度
- ⚠️ vision 节点必须用 ros2_venv python（cv2 4.11 新 API）；launch 已自动配置（L123-129）
- ⚠️ 标签表面保持清洁平整，反光/脏污会破坏角点提取
- ⚠️ `start_voice:=false` 可省约 500MB 内存（LLM），本实验不需要语音时务必使用（launch L77-78）
- ⚠️ pick_offset 调优遵循小步（5~10mm）单方向原则，防止机械臂碰撞

### 5.8 实验总结

**完成成果**：

- 一键启动 vision/grasp 节点（start_voice:=false），确认 rqt 调试画面
- 完成 AprilTag 检测测试：detected/target/debug_image 三话题验证
- 完成装货抓取链路：移观察位→检测→TF→set_pick_target→pick→place→回 work，含 debug confirm 停等
- 完成 pick_offset 调优实验，验证偏移对落点精度的影响并写回最终配置
- 按 docs/08、docs/09 用例完成 TV1~TV3、TG1~TG5 全部记录

**技能收获**：

- 掌握 AprilTag 检测与 PnP 位姿解算原理（2D 角点→6DOF 位姿）
- 掌握 camera→base_link TF 变换链的查询与故障定位方法
- 掌握视觉抓取八步序列与双模式（debug/production）confirm 机制
- 学会用 param set + 写回 yaml 的方式系统性调优 pick_offset

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 检测不到标签 | venv cv2 4.11 未使用 / 相机未启动 | 确认 launch 用 venv python；`ros2 topic list \| grep ascamera` |
| 位姿跳变 | 标签反光/斜视/遮挡 | 调整姿态光照；保持正对相机 |
| TF 查找失败 | 相机外参帧缺失 | `view_frames` 检查 TF 树；确认相机外参发布 |
| 抓取落点系统性偏移 | 手眼标定偏差 | 按偏差反向调 pick_offset_x/y/z |
| confirm 无效 | 模式为 production 或状态错 | 改 mode: debug 重启；`/eai_factory/grasp/abort` 重置 |
| 触发任务返回 busy | 上次抓取未完成（串行保护） | 等序列 done 日志或 abort 重置后再触发 |

### 5.9 实验报告要求

**思考题**：

1. AprilTag 的 tag_size 参数在 PnP 解算中起什么作用？如果将 tag_size 设成真实值的一半，解算出的 z 距离会如何变化？
2. 为什么检测出的位姿要先做 TF 变换才能用于机械臂抓取？如果相机外参标定误差为 1cm，抓取点会偏多少？为什么 pick_offset 能修正这种误差？
3. debug 模式（awaiting_confirm 停等）与 production 模式（全自动）各自的适用场景是什么？confirm 机制在调试阶段的工程价值是什么？
4. 抓取序列中"移观察位→等待 3s（move_delay）"的作用是什么？move_delay 过小会有什么后果？
5. 如果装货区换了更高/更低的货箱，应调整 observe_pose 还是 pick_offset？为什么？

**评分标准**：启动与节点观察 15 分 + AprilTag 检测与 PnP 验证 20 分 + 装货抓取链路（含 confirm）30 分 + pick_offset 调优实验 20 分 + 用例记录与数据分析 15 分 = 100 分。
