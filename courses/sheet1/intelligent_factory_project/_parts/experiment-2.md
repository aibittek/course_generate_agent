## 实验2：机器人视觉与抓取（8h）

> ✅ **源码已核实** 本实验核心实现位于 `app/car1_app/car1_app/navigation_grasp_transport.py` 的视觉与抓取模块（`_detect_and_project` / `_count_red_pixels` / `_refresh_joints_sync` / `_handle_detect_and_grasp` / `_handle_call_pick`），配置见 `config/navigation_grasp_transport.yaml`。任务要求：机器人导航到位后，移动机械臂使装在前端的 HP60C 深度相机下视桌面，识别并三维定位红色方块，通过 `arm_controller` 服务完成抓取与放置。

### 2.1 关联知识点

本实验对应"智能工厂综合项目"第 2 章"视觉与抓取"，覆盖知识点：

- 2.1.1 HSV 颜色空间 > 原理 > HSV（色相/饱和度/明度）比 RGB 对光照更鲁棒；红色色相绕 0/180 回绕，需双阈值区间（lower `[0,100,80]`-`[15,255,255]` 与 lower2 `[160,100,80]`-`[180,255,255]`）
- 2.1.2 形态学去噪与轮廓提取 > 流程 > `cv2.inRange` → 椭圆核 `MORPH_OPEN`/`MORPH_CLOSE` → `findContours`+判面积 → 取质心 `(u,v)`
- 2.2.1 深度反投影 > 原理 > 用相机内参把像素坐标投影为相机三维坐标：$x_{cam}=(u-c_x)z/f_x,\ y_{cam}=(v-c_y)z/f_y$；HP60C 深度为 uint16 毫米，需 `/1000` 转米
- 2.2.2 深度采样鲁棒化 > 流程 > 在物体轮廓掩膜内取有效深度做中位数 + MAD 离群剔除，抗空洞与边缘噪声
- 2.2.3 TF 坐标变换 > 原理 > `camera_depth_optical_frame` → `base_link` 变换把相机坐标转到机器人 base 系，供 `set_pick_target` 使用
- 2.2.4 舵机姿态刷新 > 流程 > `refresh_positions` 同步刷新 bus 舵机实际角度，防止 TF 依据"指令位置"而非"实际位置"导致抓取偏移
- 2.3.1 arm_controller 服务 API > 流程 > `set_pick_target`（只存目标不移动）/ `pick`（执行抓取）/ `place`（执行放置）/ `set_gripper` / `go_home` / `go_work`
- 2.3.2 观察位姿与放置目标整定 > 流程 > `observe_pose`（相机下视桌面）与 `place_target_arm`（放置点相对 base）参数

### 2.2 实验目标

1. 掌握 HSV 颜色阈值识别红色方块，并用形态学与轮廓处理稳定提取质心 — 独立完成
2. 掌握深度相机反投影 + TF 坐标变换，把图像上的目标换算成 `base_link` 下的三维坐标 — 原理理解
3. 掌握 arm_controller 抓取/放置服务调用，成功抓取红色方块并放到指定位置 — 独立完成

### 2.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能机器人小车 C1（含 5DOF 机械臂 + HP60C 深度相机 + bus 舵机）；具身智能实验箱 B2 |
| 相机话题 | RGB：`/ascamera_hp60c/camera_publisher/rgb0/image`；深度：`.../depth0/image_raw`；内参：`.../depth0/camera_info` |
| 相机帧 | `camera_depth_optical_frame`（光学坐标系），机器人基座帧 `base_link` |
| 核心库 | cv2、numpy、cv_bridge、tf2_ros、tf2_geometry_msgs |
| 服务 API | `/arm_controller/set_pick_target`(PoseStamped)、`/arm_controller/pick`(Trigger)、`/arm_controller/place`(Trigger)、`/arm_controller/set_gripper`(SetBool)、`/arm_controller/go_home`、`/arm_controller/go_work`、`/servo_controller/refresh_positions`(Trigger) |
| 主入口 | `navigation_grasp_transport.py`（`_detect_and_project` / `_handle_detect_and_grasp`） |

### 2.4 实验难度

- 难度: ⭐⭐⭐ 综合性
- 重点: "像素 → 相机坐标 → 机器人 base 坐标"的整条三维定位链路，及 arm_controller 服务化抓取
- 难点: 相机与 base 之间的 TF 链；bus 舵机"指令/实际"位置不一致导致的定位漂移；深度相机的近盲区（HP60C 约 0.5m）

### 2.5 实验现象

**快速验证流程**（综合任务已跑通状态，实机验证前务必先做 PWM 安全检查）：

1. 前置：`ros2 launch car1_bringup bringup.launch.py` + `ros2 launch car1_arm_controller arm_controller.launch.py`（需先 bringup，顺序反了会导致 arm 无响应）
2. 让机器人导航到位，服务端触发抓取（或直接单独测试视觉模块）
3. 观察日志输出 `_detect_and_project` 的三段关键打印：
   - `[DETECT] centroid=(ux,vy) area=... z_cam=... | cam_frame=(x,y,z)`
   - `[TF] cam_frame=... → base_link=[xv,yv,zv]`
   - `Published set_pick_target: [x, y, z]`
4. 终端看到 `FINAL target` 后，机械臂自动下探沿相机反投影方向抓取，随后夹爪闭合提起
5. 调用 `/arm_controller/place` 放置，夹爪张开、机械臂缩回工作位

**预期效果描述**：

- **HSV 检测**：红色方块在掩膜中呈现为高亮连通区域，阈值过滤掉非红背景；面积小于 100px 的噪声被过滤
- **深度反投影**：`_detect_and_project` 打印的 `z_cam` 是轮廓内深度中位数（米），`cam_frame` 为相机系坐标，`base_link` 为经 TF 变换后的抓取目标
- **抓取精度**：`camera_depth_optical_frame→base_link` 变换正确 + `refresh_positions` 刷新实际角度时，抓取目标与方块中心误差在 1-2cm 内；若不刷新舵机实际角度，x 方向可能偏移约 2cm 而抓空
- **放置结果**：机械臂把方块放到 `place_target_arm=[0.26, 0.0, 0.08, 3.14159]`（base 系正前方 26cm、高 8cm、夹爪朝下），随后 `go_work` 回工作位、夹爪闭合进入待命

### 2.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：HSV目标检测] --> B[步骤2：形态学与轮廓质心]
    B --> C[步骤3：深度采样与反投影]
    C --> D[步骤4：refresh_positions 刷新关节]
    D --> E[步骤5：TF 变换到 base_link]
    E --> F[步骤6：set_pick_target + pick]
    F --> G[步骤7：place 放置与回位]
    G --> H[完成]
```

---

#### 步骤1：HSV 颜色阈值识别红色方块（阶段二：能理解，40min）

> 📌 本步骤对应源码：`navigation_grasp_transport.py` `_count_red_pixels`（L952-958）、`_detect_and_project`（L987-993）；配置 `navigation_grasp_transport.yaml` L58-63

**知识点讲解**：

**HSV 与红色双阈值（2.1.1）**

- **原理**：HSV 把颜色拆成色相 H（0-180）、饱和度 S、明度 V，天然把"颜色"与"光照/亮度"解耦。红色特殊在它横跨色相环的 0° 与 180°（品红/红/橙连续），单区间覆盖不全，因此用两个区间**取或**：
  - `lower=[0,100,80]` ~ `upper=[15,255,255]`（偏红的暖色带）
  - `lower2=[160,100,80]` ~ `upper2=[180,255,255]`（偏品红的高色相端）
  阈值越低越容易把肤色、橙色误识别为红；阈值越高越抗干扰但可能漏检暗红。

**操作步骤**：

1. 读 `navigation_grasp_transport.yaml` L58-63，确认两套阈值与默认值
2. 单独跑一个临时脚本，用一个静态拍摄的红色方块图验证掩膜：
   ```python
   import cv2, numpy as np
   img = cv2.imread('red_cube.jpg')
   hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
   m = cv2.bitwise_or(
       cv2.inRange(hsv, np.array([0,100,80]), np.array([15,255,255])),
       cv2.inRange(hsv, np.array([160,100,80]), np.array([180,255,255])))
   print('red_pixels =', int(m.sum()//255))
   ```
   （浅色方块/加灯后如漏检，可适当降 S/V 下界或扩 H 上界）
3. 记录光照变化（开灯/关灯）下 red_pixels 数量变化，体会 HSV 对比 RGB 的稳健性

**易错点**：

- ⚠️ OpenCV 的 HSV 用 `H∈[0,180]`，不是教科书 0-360；写 `[160,100,80]` 不要误会
- ⚠️ 红色双阈值必须 `bitwise_or`，缺 2 区间会在 0/180 边界漏检

---

#### 步骤2：形态学去噪与轮廓质心提取（阶段一：能运行，40min）

> 📌 本步骤对应源码：`navigation_grasp_transport.py` L992-1010

**知识点讲解**：

**形态学与质心（2.1.2）**

- **原理**：`getStructuringElement(MORPH_ELLIPSE,(5,5))` 生成椭圆核；`MORPH_OPEN`（先腐蚀后膨胀）去掉小椒盐噪声，`MORPH_CLOSE`（先膨胀后腐蚀）填补方块内部小空洞。随后 `findContours(RETR_EXTERNAL)` 取外轮廓，`contourArea` 过滤面积 <100 的噪点，取最大轮廓，用图像矩 `M['m10']/M['m00'], M['m01']/M['m00']` 求质心像素 `(u,v)`。

**操作步骤**：

1. 在步骤 1 脚本基础上补形态开/闭 + 取最大轮廓 + 质心，复现在红框标注质心
2. 记录按摩托后 `mask` 的噪声减少、方块区域更完整
3. 思考并回答：为什么用最大轮廓而不是所有轮廓？桌面反光误检到较大非红区域时如何规避？

**易错点**：

- ⚠️ 质心是 `(u,v)=(x,y)` 像素坐标，颜色是 BGR 下反投影输入，注意后续公式里 u 对应列、v 对应行

---

#### 步骤3：深度采样与反投影（阶段二：能理解，60min）

> 📌 本步骤对应源码：`navigation_grasp_transport.py` `_detect_and_project` L1012-1049；相机内参来自 CameraInfo

**知识点讲解**：

**深度采样鲁棒化与反投影（2.2.1、2.2.2）**

- **原理**：HP60C 深度图是 uint16 毫米。`_detect_and_project` 用轮廓掩膜选有效深度（`valid=(contour_mask>0)&(depth>0)`），取中位数并做 MAD 离群剔除：`inliers = depths[|depths-med| <= 2.5*MAD]`，再用中位数作为该点深度 `z_raw`。`depth` 是整数类型时 `/1000` 转米得 `z_cam`。最后反投影：

  $$
  x_{cam}=\frac{(u-c_x)\cdot z_{cam}}{f_x},\quad
  y_{cam}=\frac{(v-c_y)\cdot z_{cam}}{f_y}
  $$

  其中 $(c_x,c_y)$ 为主点、$f_x,f_y$ 为焦距（来自 `camera_info_topic`）。

- **为什么不用单点深度**：单点可能踩到空洞/条带；用轮廓内中位数 + MAD 剔除能同时抗"深度空洞"与"前景干扰"，得到稳定一致的深度。

**操作步骤**：

1. 读 `_detect_and_project` L1012-1049，标注深度采样、单位换算、反投影三处
2. 用相机原地观测方块 10 次，记录每次 `z_cam`/`cam_frame`，统计离散度（应 <2cm，若大则是深度噪声或方块太小采样不足）
3. 回答问题：`MIN_DEPTH_SAMPLES=30`（L1019）的意义；深度近盲区（<0.5m）为何会让反投影失效或跳变

**易错点**：

- ⚠️ 深度单位是毫米，必须 `/1000`；忘了会在 z 上差 1000 倍
- ⚠️ `camera_info` 对应 depth 相机，务必订阅 `depth0/camera_info`

---

#### 步骤4：refresh_positions 刷新实际关节角（阶段三：能改造，40min）

> 📌 本步骤对应源码：`navigation_grasp_transport.py` `_refresh_joints_sync`（L904-950）

**知识点讲解**：

**bus 舵机"指令 vs 实际"位置（2.2.4）**

- **原理**：`/joint_states` 默认发布的是**指令（commanded）关节角**，而 TF 树（`camera_depth_optical_frame→base_link`）由 robot_state_publisher 依据 joint_states 生成。若机械臂还有残差未到位，指令位置 ≠ 物理实际位置，则 TF 会给出错误的相机位姿，导致 detected 目标的 base 坐标整体偏移（实测 x 偏约 2cm 就足以抓空）。`_refresh_joints_sync`（L904）同步调用 `/servo_controller/refresh_positions`，强制 bus 控制器回读实际角度并更新 TF，超时 1.5s 则退化用旧 TF。
- **为什么放在 TF 查询前**：只有在读取实际角度之后再去查 `camera_depth_optical_frame→base_link`，变换矩阵才基于真实的机械臂姿态。

**操作步骤**：

1. 读 `_refresh_joints_sync` L904-950，理解 `call_async` 后 1.5s 内轮询 `future.done()` 的同步等待
2. 分别注解掉/保留 refresh 调用各跑一次抓取，对比 base 坐标打印与抓取成败，体会该步的"关键性"
3. 记录：不 refresh 时 `base_link` 目标与 refresh 时的差值（理论上接近一个固定的 TF 位姿误差）

**易错点**：

- ⚠️ 该步骤是"抓空"的头号隐性原因——务必保留在 TF 查询前
- ⚠️ 机械臂仍在运动时 refresh 读到的仍是过渡位姿，因此上层会等 `observe_settle_sec=5.0` 让机械臂稳定后再检测（见 exp04）

---

#### 步骤5：TF 坐标变换到 base_link（阶段二：能理解，50min）

> 📌 本步骤对应源码：`navigation_grasp_transport.py` L1056-1085；`do_transform_point`（tf2_geometry_msgs）

**知识点讲解**：

**像素→base 坐标（2.2.3）**

- **原理**：相机光学系得到的是相机坐标 $(x_{cam},y_{cam},z_{cam})$，但机械臂/导航都在 `base_link` 系工作。`tf_buffer.lookup_transform(base_link, camera_depth_optical_frame, Time())` 取变换（含平移+旋转），构造 `PointStamped` 在相机系，用 `do_transform_point(point_optical, tf)` 变换到 base：
  $$
  \begin{bmatrix} x \\ y \\ z \end{bmatrix}_{base}
  = R_{cam}^{base}\cdot \begin{bmatrix} x_{cam}\\y_{cam}\\z_{cam}\end{bmatrix}
  +\ t_{cam}^{base}
  $$
  得到的 `(x_base,y_base,z_base)` 即方块相对机器人 collinear 的三维位置，直接喂给 `set_pick_target`。

**操作步骤**：

1. 读 `_detect_and_project` L1056-1085，确认 TF 查询、`PointStamped` 帧设置与 do_transform 链路
2. 用 `ros2 run tf2_ros tf2_echo camera_depth_optical_frame base_link` 观察当前变换（平移旋转）
3. 验证：把方块放桌面，对比打印的 `[TF]` 行 `(x_base,y_base,z_base)` 与方块在 base 系的大致位置（应为正前方、桌面高度附近）

**易错点**：

- ⚠️ `header.frame_id` 必须设为 `camera_depth_optical_frame`，否则变换坐标系错误
- ⚠️ TF 查找超时 0.5s；机械臂抖动期间 TF 更新临时中断是正常的，重试即可

---

#### 步骤6：set_pick_target + pick 服务调用（阶段三：能改造，50min）

> 📌 本步骤对应源码：`navigation_grasp_transport.py` `_handle_detect_and_grasp`（L660-747）、`_handle_call_pick`（L749-762）

**知识点讲解**：

**"先存目标、下一拍再抓"（2.3.1）**

- **原理**：`/arm_controller/set_pick_target`（PoseStamped）只把抓取目标**存进 arm_controller**、不立即动作；真正执行是 `/arm_controller/pick`（Trigger）。设计上二者**分在两个状态（DETECT_AND_GRASP → CALL_PICK）而非同一 tick 连续调用**：给 arm_controller 的订阅回调留一个执行周期去消费 `set_pick_target`，再调用 `pick` 时才能读到刚写入的目标。`pitch=π` 表示夹爪朝下（ik_analytical 约定 0=上、π=下）。
- `_handle_detect_and_grasp` 里先**连续重复检测 N 次（`detection_repeat_count=5`）取最后一次成功结果**——机械臂到观察位后前 ~1s 仍在微调，单次瞬态读数会偏，连续检测取末次能让位姿稳定后再定目标（模拟 visual_grasp 的 WAIT_CONFIRMATION）。

**操作步骤**：

1. 读 `_handle_detect_and_grasp` L660-747，标注"重复检测取末次"与"发布 set_pick_target"两段
2. 读 `_handle_call_pick` L749-762，理解它如何 `service_is_ready()` 后 `call_async` 并立刻转入 WAIT_GRASP
3. 用 `dry_run: true` 先跑一趟，确认目标发布正确但机械臂不动（安全验证投影与定位链路）
4. 关闭 dry_run，观察夹爪闭合、机械臂按目标下探抓取

**易错点**：

- ⚠️ 若在同一个 tick 里"发布目标再调 pick"，可能 pick 读到旧目标而抓错位置——这是 CALL_PICK 独立状态的动机
- ⚠️ `dry_run` 下只验证到发布目标为止，务必先 dry_run 再上 real pick，防误触

---

#### 步骤7：place 放置与回工作位（阶段三：能改造，50min）

> 📌 本步骤对应源码：`navigation_grasp_transport.py` `_handle_place_object`（L793-900）

**知识点讲解**：

**多阶段放置序列（2.3.2）**

- **原理**：放置不是一次服务调用：
  1. 发布放置目标 `place_target_arm=[0.26,0,0.08,π]` 到 `set_pick_target`（不移动）；
  2. 调用 `/arm_controller/place`——arm_controller 内部完成"升到 pre_grasp 高度→下探→张开夹爪释放→上缩"；
  3. 调用 `/arm_controller/go_work` 把机械臂移回工作观察位，为下次导航/抓取准备；
  4. 调用 `/arm_controller/set_gripper(False)` 夹爪闭合进入待命。
  `_handle_place_object` 用多个 future（`_place_future`/`_work_future`/`_gripper_future`）逐个等待，前三者任一非 None 时不再重发 step1，避免"抓-放-抓-放"无限循环。

**操作步骤**：

1. 读 `_handle_place_object` L793-900，梳理 place → go_work → set_gripper 三步与 future 编排
2. 观察放置点：方块放置位置是否与 `place_target_arm` 吻合；若偏离，微调该参数
3. 全程观察日志 `Place succeeded` → `go_work done` → `Gripper closed. Task complete -> DONE`

**易错点**：

- ⚠️ 三个 future 的状态合计决定是否会重发 step1——改动时别破坏"三态判断"逻辑
- ⚠️ go_work 后再关夹爪，是为了"运输途中夹爪不夹物也不松乱"，符合现场待命习惯

---

### 2.7 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 检测不到红方块 | HSV 阈值不适配当前光照/方块颜色 | 调 `target_color_hsv_*` 阈值；确认双区间 OR |
| `z_cam` 抖动大于 >2cm | 深度空洞或轮廓含非方块区域 | 增大 `MIN_DEPTH_SAMPLES`、加强 MAD 剔除；重拍深度验证 |
| 抓空 | TF 用了指令关节角未刷新 | 正确放置 `_refresh_joints_sync()` 在 TF 查询前 |
| 抓偏 2cm 左右（x 方向） | 机械臂仍在微调就定了目标 | 调大 `observe_settle_sec`，或重开 `detection_repeat_count` 取末次 |
| pick 抓到旧位置 | 发布目标后立刻 pick | 确保走 CALL_PICK 独立状态（隔一个 tick） |
| 实机抓取可能堵转 | PWM 异常或机械干涉 | 实机前先跑 `test_servo_direct.py` 验证 PWM，遵循项目安全红线 |
| base 坐标明显不对 | camera_info/内参或帧设置错误 | 订阅 `depth0/camera_info`；`header.frame_id=camera_depth_optical_frame` |

### 2.8 扩展实验

**扩展方向 1：多颜色/多目标分拣**
- 扩展 HSV 到蓝/绿多区间，定义"颜色→放置槽"映射，让机器人在同一桌面对多种颜色方块做分类抓放，贴近真实产线分拣

**扩展方向 2：目标丢视野恢复**
- 观察 `ROTATE_SEARCH`（exp04 引入）在一组搜索角内遍历后仍找不到目标的处理（`All search angles exhausted` → FAILED），试试增加/加密搜索角序列提升容错

### 2.9 实验报告要求

**评分标准**：HSV 阈值调优 15 分 + 形态学/轮廓 15 分 + 深度采样与反投影 25 分 + TF 变换与 refresh 25 分 + 抓取/放置服务调用 20 分 = 100 分。

**报告必含内容**：
1. 视觉定位链路图（像素→深度→相机反投影→TF→base），标注每步源码与行号
2. 3 次抓取的 `base_link` 目标坐标打印与最终误差记录
3. "refresh vs 不 refresh"的 base 坐标/抓取结果对比
4. `place_target_arm` 整定前后放置位置说明
5. 回答思考题：为什么用中位数+深度采样而非单点深度？为什么 pick 要独立状态与 set_pick_target 分开拍？
6. 实验心得与问题记录

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-09-23 | 初版生成（基于 navigation_grasp_transport.py：HSV 双区间/形态学/深度反投影/MAD 离群/refresh_positions/TF 变换/arm_controller 服务 API；参数取自 navigation_grasp_transport.yaml 实测值） |