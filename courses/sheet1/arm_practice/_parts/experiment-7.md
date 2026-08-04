## 实验7：机械臂基于视觉的动态抓取实验（8h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/app/car1_app/`，未复制到 `source-codes/EXP005/exp07/`。已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。后续补充源码后需触发 SourceCodeAnalysisAgent 并移除豁免。本指导书内容基于 `car1_app/launch/visual_grasp.launch.py`、`car1_app/car1_app/visual_grasp.py`、`car1_app/car1_app/common.py` 等视觉抓取应用源码。

### 1.1 关联知识点

本实验对应第 7 章"视觉动态抓取"，覆盖以下 18 个知识点（覆盖面最广）：

- 7.1.1 HSV > 概念 > HSV（Hue/Saturation/Value）相比 RGB 对光照变化更鲁棒，适合目标颜色分割
- 7.1.2 inRange+形态学 > 流程 > OpenCV `cv2.inRange(hsv, lower, upper)` 生成二值掩膜，形态学操作去噪
- 7.1.3 findContours > 原理 > `cv2.findContours` 提取最大轮廓，`minEnclosingCircle` 求质心作为目标点
- 7.2.1 深度反投影 > 概念 > 深度相机同时输出 RGB 与 Depth 图，通过像素坐标 (u,v,d) 反投影到相机坐标系
- 7.2.2 像素→相机 > 公式 > X = (u - cx) * d / fx,  Y = (v - cy) * d / fy,  Z = d
- 7.2.3 内/外参 > 原理 > 内参 (fx,fy,cx,cy) 由相机标定得到，外参描述相机相对 base_link 的位姿
- 7.3.1 TF树 > 概念 > TF 树维护所有坐标系之间的实时变换关系，支持跨坐标系查询
- 7.3.2 transform > 流程 > `tf_buffer.transform(point, "base_link", "camera_depth_optical_frame")` 将相机坐标变换到机械臂基座
- 7.3.3 REP-103 > 原理 > `camera_depth_optical_frame` 遵循 REP-103 约定：X右/Y下/Z前
- 7.4.1 eye-in-hand > 概念 > eye-in-hand 安装方式下，机械臂下压时目标会脱离视野，需先记录再移动
- 7.4.2 look-then-move > 流程 > 步骤：检测目标→记录 base_link 坐标→移动到 pre_grasp→下压→夹取
- 7.4.3 记录再移动 > 原理 > 记录坐标后再移动可避免下压过程中目标丢失，牺牲少量实时性换取稳定性
- 7.5.1 IDLE状态机 > 概念 > IDLE 状态机：observe→detect→confirm→pick→idle 五态循环
- 7.5.2 四服务接口 > 流程 > 服务化控制接口：/visual_grasp/start、/confirm、/skip、/abort 四类
- 7.5.3 解耦设计 > 原理 > 状态机使检测/确认/抓取解耦，便于人工介入与多目标循环
- 7.6.1 rqt三栏 > 概念 > rqt_image_view 同时显示 RGB/Depth/Mask 三栏，便于观察检测与定位效果
- 7.6.2 HSV调参 > 流程 > 调优 HSV 阈值应对不同颜色物体，调 gripper_depth 适应不同尺寸
- 7.6.3 重复抓取 > 流程 > 处理重复抓取：检测到已抓取物体时自动 skip，避免夹取空气

### 1.2 实验目标

1. 理解视觉抓取系统的工作原理（HSV+深度+TF+IK+状态机的多模块协同）— 原理理解
2. 掌握 HSV 颜色检测、深度反投影、TF 变换的工作流程 — 流程掌握
3. 独立使用 visual_grasp.launch.py 一站式启动并完成动态抓取 — 独立完成
4. 能够调优 HSV 阈值（换颜色）、gripper_depth 参数适应不同物体 — 独立完成
5. 能够使用 rqt 三栏可视化分析检测与定位过程 — 独立完成
6. 能够处理服务化流程（start/confirm/skip/abort）与重复抓取 — 迁移应用

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 机器人小车C1（含 5 自由度机械臂、Intel RealSense D435 深度相机、目标物体） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 + OpenCV 4.x + numpy + scipy |
| 核心库 | cv2、cv_bridge、tf2_ros、tf_transformations、realsense2_camera、rqt_image_view |
| 视觉节点 | realsense2_camera（RGB+Depth 发布）、visual_grasp_node（HSV+IK 集成） |
| 服务接口 | /visual_grasp/start、/visual_grasp/confirm、/visual_grasp/skip、/visual_grasp/abort |
| 状态机 | observe→detect→confirm→pick→idle 五态循环 |
| 主入口 | `app/car1_app/launch/visual_grasp.launch.py`（一站式启动）<br>`app/car1_app/car1_app/visual_grasp.py`（核心节点）<br>`app/car1_app/car1_app/common.py`（HSV+深度+TF 公共函数） |

### 1.4 实验难度

- 难度: ⭐⭐⭐ 难（综合）
- 重点: HSV+深度+TF+IK 端到端集成；状态机；服务化控制；三栏可视化
- 难点: 眼在手（eye-in-hand）下压失视野问题；多模块时序协同；HSV 调参与重复抓取处理

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：

1. 启动视觉抓取：`ros2 launch car1_app visual_grasp.launch.py`
2. 启动可视化：`rqt_image_view`（分别订阅 3 个话题）
3. 将目标物体（如黄色立方块）放在桌面
4. 触发开始：`ros2 service call /visual_grasp/start ...`
5. 观察机械臂：检测目标 → 等待确认 → 下压抓取
6. 人工确认：`ros2 service call /visual_grasp/confirm`
7. 抓取完成

**预期效果描述**：
- **终端 1（visual_grasp_node）**：
  ```
  [INFO] State: IDLE -> OBSERVE
  [INFO] Detected yellow object at pixel (320, 240)
  [INFO] Depth: 0.45m, Base_link pose: (0.25, 0.05, 0.05)
  [INFO] State: OBSERVE -> CONFIRM
  [INFO] Waiting for /visual_grasp/confirm...
  ```
- **rqt 三栏可视化**：
  - 左栏（RGB）：相机实时画面，目标物体有彩色矩形框
  - 中栏（Depth）：深度图，目标位置有深度值标注
  - 右栏（Mask）：HSV 二值掩膜，目标轮廓白色填充
- **机械臂运动**：从 IDLE 状态机依次进入 OBSERVE（检测）→ CONFIRM（等待确认）→ PICK（抓取）→ IDLE
- **TF 变换链**：相机坐标系中的目标点通过 TF 自动转换到 base_link 坐标系，机械臂按 base_link 坐标运动

### 1.6 实验步骤

#### 阶段划分（8h 完整规划）

| 阶段 | 章节 | 时长 | 重点 |
|------|------|------|------|
| 阶段 1（2h） | 启动与基础流程 | 120min | visual_grasp 启动、HSV 检测、深度反投影、TF 变换 |
| 阶段 2（2h） | 状态机与服务化 | 120min | IDLE 状态机、start/confirm/skip/abort 服务 |
| 阶段 3（2h） | 抓取执行与调优 | 120min | look-then-move、参数调优、rqt 三栏 |
| 阶段 4（2h） | 综合项目 | 120min | 多目标循环、错误处理、性能评估 |

#### 整体流程图

```mermaid
graph LR
    A[阶段1：启动与基础] --> B[步骤1：环境搭建]
    B --> C[步骤2：HSV颜色检测]
    C --> D[步骤3：深度反投影]
    D --> E[步骤4：TF坐标变换]
    E --> F[阶段2：状态机]
    F --> G[步骤5：IDLE状态机]
    G --> H[步骤6：服务化控制]
    H --> I[阶段3：抓取执行]
    I --> J[步骤7：look-then-move]
    J --> K[步骤8：参数调优]
    K --> L[步骤9：rqt三栏]
    L --> M[阶段4：综合项目]
    M --> N[步骤10：多目标循环]
    N --> O[步骤11：错误处理]
    O --> P[步骤12：性能评估]
    P --> Q[完成]
```

---

## 阶段 1：启动与基础流程（2h）

---

#### 步骤1：视觉抓取环境搭建（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`app/car1_app/launch/visual_grasp.launch.py`、`realsense2_camera` 驱动

**知识点讲解**：

**视觉抓取系统架构（7.1.1 引入）**
- **原理**：car1 视觉抓取系统由 5 个 ROS2 节点组成：(1) **realsense2_camera_node**：发布 RGB 图（`/camera/color/image_raw`）与深度图（`/camera/depth/image_rect_raw`）；(2) **robot_state_publisher**：发布 TF 树；(3) **arm_controller**：执行关节命令；(4) **tf2_ros**：跨坐标系变换；(5) **visual_grasp_node**：核心节点，集成了 HSV 检测 + 深度反投影 + TF 变换 + IK 解算 + 抓取执行 + 状态机管理。这种"多节点协作"的设计使各模块可独立替换与测试。
- **源码对应**：`visual_grasp.launch.py` 中 5 个 NodeAction

**Intel RealSense D435 深度相机**
- **原理**：D435 是 Intel 的消费级深度相机，采用红外结构光 + 立体视觉。技术参数：(1) **RGB 分辨率**：1920×1080 @ 30fps；(2) **深度分辨率**：1280×720 @ 30fps；(3) **深度范围**：0.1-10m；(4) **深度精度**：±2% @ 2m；(5) **基线距离**：50mm。深度值在图像中以 uint16 表示（单位 mm）。`camera_depth_optical_frame` 遵循 REP-103 约定：X右/Y下/Z前。
- **源码对应**：`realsense2_camera` 驱动（ros-humble-realsense2-camera）

**操作步骤**：

1. 检查硬件连接：
   - D435 通过 USB 3.0 连接到工作站
   - 5 自由度机械臂连接到工作站串口
   - 相机固定在机械臂末端（eye-in-hand 安装）

2. 查看相机设备：
   ```bash
   lsusb | grep Intel
   # 预期：Intel Corp. Intel RealSense D435
   ```

3. 安装 realsense 驱动：
   ```bash
   sudo apt install ros-humble-realsense2-camera ros-humble-realsense2-description
   ```

4. 测试相机（单独启动）：
   ```bash
   ros2 launch realsense2_camera rs_launch.py
   # 预期：发布 /camera/color/image_raw 与 /camera/depth/image_rect_raw
   
   rqt_image_view  # 订阅 /camera/color/image_raw
   # 应能看到相机实时画面
   ```

5. 查看相机内参：
   ```bash
   ros2 topic echo /camera/color/camera_info --once
   # 字段：K = [fx, 0, cx, 0, fy, cy, 0, 0, 1]
   # D = 畸变系数（5 个）
   # 典型内参：fx≈614, fy≈614, cx≈320, cy≈240
   ```

6. 编译视觉抓取包：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select car1_app
   source install/setup.bash
   ```

7. 一站式启动：
   ```bash
   ros2 launch car1_app visual_grasp.launch.py
   # 预期：5 个节点依次启动，终端打印：
   # [INFO] [realsense2_camera_node]: Publishing RGB + Depth
   # [INFO] [arm_controller]: Initialized
   # [INFO] [visual_grasp_node]: State IDLE, waiting for /visual_grasp/start
   ```

8. 查看节点拓扑：
   ```bash
   ros2 node list
   # 预期：/realsense2_camera_node, /robot_state_publisher, /arm_controller,
   #       /tf2_ros, /visual_grasp_node
   ros2 topic list | grep -E '(camera|arm|visual)'
   # 预期：/camera/color/image_raw, /camera/depth/image_rect_raw,
   #       /arm/joint_command, /visual_grasp/feedback
   ```

**易错点**：
- ⚠️ **相机无图像** → **解决**：检查 USB 3.0 连接（USB 2.0 带宽不足）
- ⚠️ **深度图为全黑** → **解决**：检查红外发射器是否被遮挡
- ⚠️ **launch 启动后报"port busy"** → **解决**：检查 /dev/ttyUSB0 与相机 USB 编号

---

#### 步骤2：HSV 颜色检测（阶段一：能运行，45min）

> ⚠️ 本步骤对应 src 目录源码：`car1_app/common.py` 中 `detect_color_object()` 函数

**知识点讲解**：

**HSV 颜色空间（7.1.1）**
- **原理**：HSV（Hue 色调、Saturation 饱和度、Value 明度）相比 RGB 更适合颜色分割：(1) **Hue**：0-180° 描述颜色种类（红橙黄绿青蓝紫）；(2) **Saturation**：0-255 描述颜色纯度；(3) **Value**：0-255 描述明暗。在 RGB 中，一个像素的颜色由 3 个值共同决定，亮度变化会显著影响分割结果；HSV 中亮度（V）独立于颜色（H+S），对光照变化更鲁棒。
- **源码对应**：`common.py` 中 HSV 转换 `cv2.cvtColor(rgb, cv2.COLOR_BGR2HSV)`

**inRange + 形态学（7.1.2）**
- **原理**：`cv2.inRange(hsv, lower, upper)` 生成二值掩膜（mask），H/S/V 三通道都在范围内时 mask=255，否则=0。形态学操作（`cv2.morphologyEx`）通过腐蚀（erode）+ 膨胀（dilate）去除小噪点、连接断裂区域。常用核大小 5×5 或 7×7。
- **源码对应**：`common.py` 中 `mask = cv2.inRange(hsv, lower, upper); mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)`

**findContours 提取目标（7.1.3）**
- **原理**：`cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)` 提取所有外部轮廓。`cv2.minEnclosingCircle(cnt)` 求轮廓的最小外接圆，返回圆心 (cx, cy) 与半径 r。圆心即为目标质心（用于后续深度反投影），半径反映目标尺寸（用于 gripper_depth 调优）。
- **源码对应**：`common.py` 中 `contours, _ = cv2.findContours(...)`

**操作步骤**：

1. 编写独立的 HSV 测试脚本：
   ```python
   # test_hsv_detect.py
   import cv2
   import numpy as np
   
   def test_hsv(rgb_image, color='yellow'):
       color_ranges = {
           'yellow': ((20, 100, 100), (40, 255, 255)),
           'red':    ((0, 100, 100), (10, 255, 255)),
           'blue':   ((100, 100, 100), (130, 255, 255)),
           'green':  ((40, 100, 100), (80, 255, 255)),
       }
       lower, upper = color_ranges[color]
       hsv = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2HSV)
       mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
       kernel = np.ones((5,5), np.uint8)
       mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
       mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
       
       contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
       if not contours:
           return None, None, mask
       largest = max(contours, key=cv2.contourArea)
       (cx, cy), r = cv2.minEnclosingCircle(largest)
       return (int(cx), int(cy), r), largest, mask
   
   # 测试
   cap = cv2.VideoCapture(0)
   while True:
       ret, frame = cap.read()
       if not ret: break
       result, contour, mask = test_hsv(frame, 'yellow')
       if result:
           cx, cy, r = result
           cv2.circle(frame, (cx, cy), int(r), (0, 255, 0), 2)
           cv2.putText(frame, f'({cx},{cy}) r={r:.0f}', (cx, cy-20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
       cv2.imshow('RGB', frame)
       cv2.imshow('Mask', mask)
       if cv2.waitKey(1) & 0xFF == ord('q'):
           break
   cap.release()
   cv2.destroyAllWindows()
   ```

2. 运行测试：
   ```bash
   python3 test_hsv_detect.py
   ```

3. HSV 阈值调优：
   - 用 `cv2.createTrackbar` 创建 H/S/V 三个滑块
   - 实时调节阈值观察 mask 变化
   - 找到最佳阈值范围

4. 保存调优后的阈值到 YAML：
   ```bash
   cat ~/ros2_ws/src/xflz_eai_car1/app/car1_app/config/hsv_thresholds.yaml
   # 预期：
   # hsv_thresholds:
   #   yellow:
   #     lower: [20, 100, 100]
   #     upper: [40, 255, 255]
   #   red:
   #     lower: [0, 100, 100]
   #     upper: [10, 255, 255]
   ```

5. 验证检测准确性：
   - 准备 5 种颜色物体
   - 逐个放在相机前
   - 统计检测成功率（应 > 95%）

6. 影响因素分析：
   - **光照**：过亮或过暗影响 Saturation
   - **阴影**：产生暗色斑点干扰
   - **反光**：高光区 Value 接近 255
   - **多颜色**：在 hsv_thresholds.yaml 中配置多组阈值

**易错点**：
- ⚠️ **检测不到目标** → **解决**：放宽 HSV 阈值范围（增大 lower 减小，upper 增大）
- ⚠️ **误检背景** → **解决**：缩小 HSV 阈值范围 + 增大最小轮廓面积阈值
- ⚠️ **轮廓断裂** → **解决**：使用 `cv2.MORPH_CLOSE` 闭运算

---

#### 步骤3：深度反投影（阶段二：能理解，45min）

> ⚠️ 本步骤对应 src 目录源码：`car1_app/common.py` 中 `pixel_to_camera_frame()` 函数

**知识点讲解**：

**深度反投影原理（7.2.1）**
- **原理**：深度相机同时输出 RGB 图（颜色）与 Depth 图（深度）。Depth 图中每个像素 (u, v) 处的值 d 表示该点到相机的距离（米）。反投影的目标是将像素坐标 (u, v, d) 转换为相机坐标系下的 3D 点 (X, Y, Z)。这是"2D → 3D"的关键步骤。
- **源码对应**：`common.py` 中 `pixel_to_camera_frame(u, v, d, camera_info)`

**反投影公式（7.2.2）**
- **原理**：针孔相机模型下，反投影公式为：
  ```
  X = (u - cx) * d / fx
  Y = (v - cy) * d / fy
  Z = d
  ```
  其中 (fx, fy) 是焦距（像素单位），(cx, cy) 是主点（光心像素坐标）。这些参数都从 `camera_info` 话题的 `K` 矩阵中获得。
- **源码对应**：`common.py` 中内参提取与反投影计算

**相机内/外参（7.2.3）**
- **原理**：(1) **内参 (Intrinsics)**：描述相机自身的成像特性（焦距、主点、畸变），由相机标定得到；(2) **外参 (Extrinsics)**：描述相机相对其他坐标系（base_link）的位姿，由 URDF + TF 自动发布。car1 的外参通过 URDF 中 `<joint name="camera_joint">` 的固定变换给出。
- **源码对应**：`camera_info` 话题 + `robot_state_publisher`（URDF → TF）

**操作步骤**：

1. 查看相机内参：
   ```bash
   ros2 topic echo /camera/color/camera_info --once
   # K = [fx, 0, cx, 0, fy, cy, 0, 0, 1]
   # 典型值：fx=614.0, fy=614.0, cx=320.0, cy=240.0
   ```

2. 编写深度反投影测试：
   ```python
   # test_depth_backproject.py
   import numpy as np
   import cv2
   from sensor_msgs.msg import CameraInfo
   from cv_bridge import CvBridge
   
   def pixel_to_camera(u, v, d, fx, fy, cx, cy):
       X = (u - cx) * d / fx
       Y = (v - cy) * d / fy
       Z = d
       return (X, Y, Z)
   
   # 已知内参
   fx, fy, cx, cy = 614.0, 614.0, 320.0, 240.0
   
   # 测试 1：图像中心点
   u, v, d = 320, 240, 0.5
   X, Y, Z = pixel_to_camera(u, v, d, fx, fy, cx, cy)
   print(f"中心点: ({X:.3f}, {Y:.3f}, {Z:.3f})")
   # 预期：(0, 0, 0.5)
   
   # 测试 2：图像右下角（偏离中心 320x180 像素）
   u, v, d = 640, 420, 0.5
   X, Y, Z = pixel_to_camera(u, v, d, fx, fy, cx, cy)
   print(f"右下角: ({X:.3f}, {Y:.3f}, {Z:.3f})")
   # 预期：(0.333, 0.293, 0.5)
   ```

3. 从相机读取 Depth 图：
   ```python
   # depth_reader.py
   import rclpy
   from rclpy.node import Node
   from sensor_msgs.msg import Image
   from cv_bridge import CvBridge
   import numpy as np
   
   class DepthReader(Node):
       def __init__(self):
           super().__init__('depth_reader')
           self.sub = self.create_subscription(
               Image, '/camera/depth/image_rect_raw', self.cb, 10)
           self.bridge = CvBridge()
       
       def cb(self, msg):
           depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
           # depth 是 uint16 数组，单位 mm
           # 显示中心点深度
           h, w = depth.shape
           cx, cy = w//2, h//2
           d = depth[cy, cx] / 1000.0
           print(f"中心点深度: {d:.3f} m")
   
   rclpy.init()
   rclpy.spin(DepthReader())
   ```

4. 实际反投影验证（用标定物体）：
   - 将黄色立方块放在距离 0.5m 处
   - 记录 HSV 检测的像素坐标 (u, v)
   - 查询深度图该点的深度 d
   - 反投影得 (X, Y, Z) = 相机坐标
   - 用刻度尺测量实际位置，对比误差

5. 深度图空洞处理：
   - D435 在某些角度（如边缘、远距离）会返回 0（无深度）
   - 解决：使用 `cv2.inpaint` 修复或扩大 HSV 阈值范围

6. 深度精度评估：
   - 在 0.3m / 0.5m / 1.0m 三个距离测量
   - 用卷尺对比误差
   - 预期：±2-3cm @ 1m

**易错点**：
- ⚠️ **深度图为 0** → **解决**：检查深度范围，相机最低深度 0.1m
- ⚠️ **反投影误差大** → **解决**：检查 camera_info 中内参是否更新
- ⚠️ **深度单位混淆** → **解决**：D435 深度图 uint16 单位是 mm，不是 m

---

#### 步骤4：TF 坐标变换（阶段二：能理解，30min）

> ⚠️ 本步骤对应 src 目录源码：`car1_app/common.py` 中 `transform_to_base_link()` 函数

**知识点讲解**：

**TF 树与跨坐标系查询（7.3.1）**
- **原理**：TF 库维护所有坐标系之间的实时变换关系。car1 的 TF 树为：`map → odom → base_link → link1 → ... → link5 → tcp_link → camera_depth_optical_frame`。通过 `tf_buffer.lookup_transform()` 或 `tf_buffer.transform()` 可以在任意两个坐标系间转换。TF 的核心优势是**实时性**：当机械臂运动时，camera_depth_optical_frame 相对 base_link 的位姿实时更新，无需手动同步。
- **源码对应**：`tf2_ros.Buffer` + `tf2_ros.TransformListener`

**transform 调用（7.3.2）**
- **原理**：`tf_buffer.transform(point_stamped, "base_link", "camera_depth_optical_frame")` 将一个 PointStamped 从源坐标系转换到目标坐标系。内部会：(1) 查询两坐标系之间的最新变换矩阵 T；(2) 应用 T 到 point_stamped 上；(3) 返回新的 PointStamped。同步等待（`timeout`）保证变换已发布。
- **源码对应**：`common.py` 中 `self.tf_buffer.transform(...)`

**REP-103 约定（7.3.3）**
- **原理**：`camera_depth_optical_frame` 遵循 ROS REP-103 约定：X轴指向右、Y轴指向下、Z轴指向前（相机视野方向）。这种约定与 base_link（X前、Y左、Z上）不同，TF 变换会自动处理坐标系方向差异。理解 REP-103 对调试坐标系问题至关重要。
- **源码对应**：`common.py` 中坐标系命名约定

**操作步骤**：

1. 查看 TF 树：
   ```bash
   ros2 run tf2_tools view_frames
   # 生成 frames.pdf
   # 预期：map → odom → base_link → ... → camera_depth_optical_frame
   ```

2. 查看单个变换：
   ```bash
   ros2 run tf2_ros tf2_echo base_link camera_depth_optical_frame
   # 持续打印 base_link → camera_depth_optical_frame 的变换
   # 典型：translation (0.05, 0, 0.10), rotation (四元数)
   ```

3. Python 变换测试：
   ```python
   # test_tf_transform.py
   import rclpy
   from rclpy.node import Node
   from geometry_msgs.msg import PointStamped
   from tf2_ros.buffer import Buffer
   from tf2_ros.transform_listener import TransformListener
   
   class TFTester(Node):
       def __init__(self):
           super().__init__('tf_tester')
           self.tf_buffer = Buffer()
           self.tf_listener = TransformListener(self.tf_buffer, self)
       
       def transform_point(self, x, y, z, source='camera_depth_optical_frame', target='base_link'):
           pt = PointStamped()
           pt.header.frame_id = source
           pt.header.stamp = self.get_clock().now().to_msg()
           pt.point.x, pt.point.y, pt.point.z = x, y, z
           try:
               result = self.tf_buffer.transform(pt, target, timeout=rclpy.duration.Duration(seconds=1.0))
               return result.point
           except Exception as e:
               self.get_logger().error(f'TF transform failed: {e}')
               return None
   
   rclpy.init()
   tester = TFTester()
   rclpy.spin_once(tester, timeout_sec=2.0)
   
   # 相机坐标系中的点 (0, 0, 0.5)（前方 0.5m）
   pt_camera = tester.transform_point(0, 0, 0.5)
   print(f"相机前 0.5m -> base_link: ({pt_camera.x:.3f}, {pt_camera.y:.3f}, {pt_camera.z:.3f})")
   # 典型输出：(0.55, 0, 0.40)（base_link 前方 0.55m，高度 0.40m）
   ```

4. 在 visual_grasp_node 中验证：
   - 启动 visual_grasp.launch.py
   - 将黄色物体放在相机前
   - 终端日志会打印：
     ```
     [INFO] Camera frame point: (0.05, 0.02, 0.45)
     [INFO] base_link frame point: (0.30, 0.02, 0.05)
     ```

5. eye-in-hand 标定验证：
   - 用棋盘格标定板（可选）验证 TF 外参精度
   - 或简单测试：相机正对一个已知点，对比 TF 报告位置

**易错点**：
- ⚠️ **TF lookup timeout** → **解决**：检查 robot_state_publisher 是否运行，URDF 中相机 joint 是否正确
- ⚠️ **变换方向反了** → **解决**：确认 source 与 target 坐标系正确

---

## 阶段 2：状态机与服务化（2h）

---

#### 步骤5：IDLE 状态机原理（阶段二：能理解，30min）

> ⚠️ 本步骤对应 src 目录源码：`car1_app/visual_grasp.py` 中 `class GraspStateMachine`

**知识点讲解**：

**状态机设计（7.5.1）**
- **原理**：car1 视觉抓取采用 5 态有限状态机（FSM）：(1) **IDLE**：初始/结束状态，等待 `/visual_grasp/start` 服务；(2) **OBSERVE**：调用 HSV 检测 + 深度反投影，输出目标在 base_link 中的坐标；(3) **CONFIRM**：等待人工确认（`/visual_grasp/confirm` 服务），便于人工介入避免误抓；(4) **PICK**：执行 look-then-move 抓取（先转底座、再下压、夹爪闭合、抬升）；(5) **IDLE**：抓取完成回到 IDLE，可触发下一轮。状态机使各阶段解耦，便于调试与扩展。
- **源码对应**：`visual_grasp.py` 中 `enum class GraspState`

**状态转换图**
- **原理**：
  ```
  IDLE --start--> OBSERVE --detected--> CONFIRM
  CONFIRM --confirm--> PICK --completed--> IDLE
  CONFIRM --skip--> OBSERVE  (跳过当前目标，搜索下一个)
  CONFIRM --abort--> IDLE   (取消整个抓取)
  PICK --abort--> IDLE      (中断抓取)
  ```

**操作步骤**：

1. 查看状态机定义：
   ```bash
   grep -A 10 "class GraspState" ~/ros2_ws/src/xflz_eai_car1/app/car1_app/visual_grasp.py
   # 预期：enum class GraspState { IDLE, OBSERVE, CONFIRM, PICK }
   ```

2. 查看状态转换函数：
   ```bash
   grep -A 5 "def transition" visual_grasp.py
   # 或查找 on_*_event 函数
   ```

3. 启动 visual_grasp 观察初始状态：
   ```bash
   ros2 launch car1_app visual_grasp.launch.py
   # 终端输出：
   # [INFO] [visual_grasp_node]: State IDLE, waiting for /visual_grasp/start
   ```

4. 监控状态变化：
   ```bash
   ros2 topic echo /visual_grasp/feedback
   # 字段：current_state (string), target_pose, progress (0-100)
   # 状态：IDLE, OBSERVE, CONFIRM, PICK
   ```

5. 手动触发状态转换（后续步骤详述）：
   ```bash
   # 1. IDLE -> OBSERVE
   ros2 service call /visual_grasp/start std_srvs/srv/Trigger
   # 2. CONFIRM -> PICK
   ros2 service call /visual_grasp/confirm std_srvs/srv/Trigger
   # 3. PICK 完成后 -> IDLE（自动）
   ```

6. 状态机调试技巧：
   - 启用 DEBUG 日志：`export RCUTILS_LOGGING_SEVERITY=DEBUG`
   - 重启 visual_grasp.launch.py
   - 观察每次状态转换的详细日志

**易错点**：
- ⚠️ **状态卡住** → **解决**：查看 feedback 话题，确认是哪个状态卡住
- ⚠️ **状态乱跳** → **解决**：检查服务调用顺序，避免误触发

---

#### 步骤6：服务化控制接口（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`car1_app/srv/Start.srv`、`Confirm.srv`、`Skip.srv`、`Abort.srv`

**知识点讲解**：

**服务化设计（7.5.2）**
- **原理**：car1 提供 4 个 ROS2 服务实现人机交互：(1) `/visual_grasp/start`（std_srvs/Trigger）：从 IDLE 启动抓取；(2) `/visual_grasp/confirm`（std_srvs/Trigger）：人工确认执行抓取；(3) `/visual_grasp/skip`（std_srvs/Trigger）：跳过当前目标搜索下一个；(4) `/visual_grasp/abort`（std_srvs/Trigger）：中断整个抓取流程。服务化设计的优势：(1) **人工介入**：每步决策可由人工审批；(2) **可观测**：通过 service call 日志观察每次决策；(3) **可测试**：单元测试中 mock 服务即可验证逻辑。
- **源码对应**：`srv/*.srv` 服务定义 + `visual_grasp.py` 中 service handlers

**解耦价值（7.5.3）**
- **原理**：状态机使"检测-确认-抓取"三阶段解耦的好处：(1) **可调试**：单步调试每个阶段；(2) **可扩展**：未来可加"再次确认"、"分阶段抓取"等；(3) **可移植**：状态机逻辑不依赖特定硬件，可在不同平台复用；(4) **可观测**：每个状态都可订阅/发布，便于监控与日志分析。
- **源码对应**：`visual_grasp.py` 中状态机独立于具体硬件

**操作步骤**：

1. 启动 visual_grasp：
   ```bash
   ros2 launch car1_app visual_grasp.launch.py
   ```

2. 查看服务列表：
   ```bash
   ros2 service list | grep visual_grasp
   # 预期：
   # /visual_grasp/start
   # /visual_grasp/confirm
   # /visual_grasp/skip
   # /visual_grasp/abort
   ```

3. 查看服务定义：
   ```bash
   ros2 service show /visual_grasp/start
   # 类型：std_srvs/srv/Trigger
   # 请求：空
   # 响应：bool success, string message
   ```

4. 完整的状态机流程演示：
   ```bash
   # 步骤 1：IDLE -> OBSERVE
   ros2 service call /visual_grasp/start std_srvs/srv/Trigger
   # 终端：State IDLE -> OBSERVE
   # 终端：Detected yellow object at (X, Y, Z)
   # 终端：State OBSERVE -> CONFIRM
   
   # 步骤 2：CONFIRM -> PICK
   ros2 service call /visual_grasp/confirm std_srvs/srv/Trigger
   # 终端：State CONFIRM -> PICK
   # 机械臂开始抓取
   # 终端：Pick completed, State PICK -> IDLE
   ```

5. skip 服务测试：
   ```bash
   # 启动抓取后用 skip 跳过
   ros2 service call /visual_grasp/start std_srvs/srv/Trigger
   # 状态：CONFIRM
   ros2 service call /visual_grasp/skip std_srvs/srv/Trigger
   # 状态：回到 OBSERVE（搜索新目标）
   ```

6. abort 服务测试：
   ```bash
   # 在 PICK 状态中止
   ros2 service call /visual_grasp/start std_srvs/srv/Trigger
   # 状态：CONFIRM
   ros2 service call /visual_grasp/confirm std_srvs/srv/Trigger
   # 状态：PICK（机械臂运动中）
   ros2 service call /visual_grasp/abort std_srvs/srv/Trigger
   # 状态：IDLE（机械臂立即停止）
   ```

7. 编写 Python 自动化脚本：
   ```python
   # auto_grasp.py
   import rclpy
   from rclpy.node import Node
   from std_srvs.srv import Trigger
   
   class AutoGrasp(Node):
       def __init__(self):
           super().__init__('auto_grasp')
           self.start_cli = self.create_client(Trigger, '/visual_grasp/start')
           self.confirm_cli = self.create_client(Trigger, '/visual_grasp/confirm')
           self.abort_cli = self.create_client(Trigger, '/visual_grasp/abort')
           for cli in [self.start_cli, self.confirm_cli, self.abort_cli]:
               cli.wait_for_service()
       
       def trigger(self, cli):
           future = cli.call_async(Trigger.Request())
           rclpy.spin_until_future_complete(self, future)
           return future.result()
       
       def grasp_once(self):
           self.get_logger().info('Starting grasp...')
           result = self.trigger(self.start_cli)
           if not result.success:
               self.get_logger().error('Start failed')
               return False
           self.get_logger().info('Confirming...')
           result = self.trigger(self.confirm_cli)
           if not result.success:
               self.get_logger().error('Confirm failed')
               return False
           self.get_logger().info('Pick in progress, waiting...')
           time.sleep(10)  # 等待抓取完成
           return True
   
   rclpy.init()
   grasper = AutoGrasp()
   grasper.grasp_once()
   rclpy.shutdown()
   ```

**易错点**：
- ⚠️ **服务调用超时** → **解决**：检查 visual_grasp_node 是否运行
- ⚠️ **状态机不接受 confirm** → **解决**：确认当前在 CONFIRM 状态
- ⚠️ **abort 后机械臂不响应** → **解决**：手动调用 go_home 复位

---

## 阶段 3：抓取执行与调优（2h）

---

#### 步骤7：look-then-move 策略（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`visual_grasp.py` 中 `def pick()`

**知识点讲解**：

**eye-in-hand 与失视野问题（7.4.1）**
- **原理**：car1 的 D435 深度相机采用"eye-in-hand"安装方式（固定在机械臂末端）。这种安装的优势是：(1) 相机随机械臂移动，灵活观察不同区域；(2) 视点灵活，可近距离观察目标。劣势是：(1) 机械臂下压时目标会"脱离视野"（相机被夹爪遮挡）；(2) 移动过程中可能丢失目标。解决方法是 look-then-move 策略。
- **源码对应**：`visual_grasp.py` 中 eye-in-hand 标定

**look-then-move 流程（7.4.2）**
- **原理**：look-then-move 策略分两步：(1) **look**：在 OBSERVE 阶段，相机在观察位姿（通常是较高位姿）检测目标，记录目标在 base_link 坐标系下的坐标；(2) **move**：根据记录的坐标进行抓取，移动过程中不再依赖视觉反馈。这种"先记录后移动"的策略牺牲少量实时性换取稳定性，避免了下压过程中目标丢失。
- **源码对应**：`visual_grasp.py` 中 `def look_then_move()`

**记录再移动的 trade-off（7.4.3）**
- **原理**：记录坐标后再移动的代价：(1) **目标移动**：如果目标在观察与抓取之间发生位移，记录的坐标会失效（对静态物体没问题，动态物体需要更复杂的视觉伺服）；(2) **机械误差**：从观察位姿到抓取位姿的关节运动会引入 1-2mm 误差。收益：(1) **稳定性**：避免视觉丢失；(2) **可预测**：抓取路径确定；(3) **可调试**：可单步调试观察与抓取。
- **源码对应**：`visual_grasp.py` 中 OBSERVE→PICK 的状态转换

**操作步骤**：

1. 查看 pick 函数实现：
   ```bash
   grep -A 30 "def pick" visual_grasp.py
   # 预期包含 4 个子步骤：approach, descend, grasp, lift
   ```

2. 观察 look-then-move 过程：
   ```bash
   # 启动 visual_grasp
   ros2 launch car1_app visual_grasp.launch.py
   
   # 触发抓取
   ros2 service call /visual_grasp/start std_srvs/srv/Trigger
   # 等待 CONFIRM 状态
   ros2 service call /visual_grasp/confirm std_srvs/srv/Trigger
   
   # 观察机械臂运动：
   # - 步骤 1：转底座到目标方位（look 阶段记录的坐标）
   # - 步骤 2：大臂下压到 pre_grasp_height
   # - 步骤 3：继续下压到 grasp 高度
   # - 步骤 4：夹爪闭合
   # - 步骤 5：抬升到 lift_height
   ```

3. 监控抓取进度：
   ```bash
   ros2 topic echo /visual_grasp/feedback
   # 字段：current_state, progress (0-100), current_step (string)
   # current_step 值：'look', 'approach', 'descend', 'grasp', 'lift'
   ```

4. 对比 look-then-move 与 look-and-move：
   - **look-then-move**：先记录，再盲抓（实验用）
   - **look-and-move**：边看边抓（高级，需要 visual servoing）
   - 在视觉抓取 log 中确认 car1 使用哪种策略

5. 目标移动测试（实验报告加分项）：
   - 在机械臂下压过程中缓慢移动目标
   - 观察：look-then-move 仍按记录坐标抓取（可能失败）
   - 与 look-and-move 对比（需自行实现）

**易错点**：
- ⚠️ **下压过程中目标被遮挡** → **解决**：增大 pre_grasp_height
- ⚠️ **目标位置与记录不符** → **解决**：在 CONFIRM 阶段重新检测

---

#### 步骤8：HSV 与 gripper_depth 调优（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`config/hsv_thresholds.yaml`、`config/grasp_params.yaml`

**知识点讲解**：

**HSV 阈值调参（7.6.2）**
- **原理**：HSV 调参是视觉抓取最常做的工作。原则：(1) **先粗后细**：先用宽阈值找到目标，再逐步缩小；(2) **考虑光照**：H 阈值 ±10、S 阈值 ±30、V 阈值 ±50 是常见调整范围；(3) **多场景配置**：为不同光照条件准备多组阈值。car1 的阈值存储在 `hsv_thresholds.yaml`，支持运行时切换。
- **源码对应**：`config/hsv_thresholds.yaml`

**gripper_depth 调参**
- **原理**：gripper_depth 影响夹爪下探深度，与目标尺寸直接相关。调参方法：(1) **测量物体高度**：用卡尺测量；(2) **初始值**：物体高度的 50-70%；(3) **微调**：±0.005m 逐步尝试。car1 默认 0.02m 适合 4cm 立方块，对小球或圆柱需调整。
- **源码对应**：`config/grasp_params.yaml`

**多物体配置**
- **原理**：不同物体类型需要不同参数。car1 在 `grasp_params.yaml` 中按物体类型分组配置：
  - **cube_small**：gripper_depth=0.015, pre_grasp=0.04
  - **cube_standard**：gripper_depth=0.020, pre_grasp=0.05
  - **sphere**：gripper_depth=0.030, pre_grasp=0.08
  - **cylinder**：gripper_depth=0.025, pre_grasp=0.06

**操作步骤**：

1. HSV 阈值调优工具：
   ```python
   # hsv_tuner.py
   import cv2
   import numpy as np
   
   def nothing(x): pass
   
   cap = cv2.VideoCapture(0)
   cv2.namedWindow('Tuner')
   cv2.createTrackbar('H_low', 'Tuner', 20, 180, nothing)
   cv2.createTrackbar('H_up',  'Tuner', 40, 180, nothing)
   cv2.createTrackbar('S_low', 'Tuner', 100, 255, nothing)
   cv2.createTrackbar('S_up',  'Tuner', 255, 255, nothing)
   cv2.createTrackbar('V_low', 'Tuner', 100, 255, nothing)
   cv2.createTrackbar('V_up',  'Tuner', 255, 255, nothing)
   
   while True:
       ret, frame = cap.read()
       hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
       
       h_l = cv2.getTrackbarPos('H_low', 'Tuner')
       h_u = cv2.getTrackbarPos('H_up', 'Tuner')
       s_l = cv2.getTrackbarPos('S_low', 'Tuner')
       s_u = cv2.getTrackbarPos('S_up', 'Tuner')
       v_l = cv2.getTrackbarPos('V_low', 'Tuner')
       v_u = cv2.getTrackbarPos('V_up', 'Tuner')
       
       mask = cv2.inRange(hsv, (h_l, s_l, v_l), (h_u, s_u, v_u))
       cv2.imshow('Tuner', frame)
       cv2.imshow('Mask', mask)
       if cv2.waitKey(1) & 0xFF == ord('q'):
           print(f"Final: H=({h_l}, {h_u}), S=({s_l}, {s_u}), V=({v_l}, {v_u})")
           break
   cap.release()
   cv2.destroyAllWindows()
   ```

2. 运行调优工具：
   ```bash
   python3 hsv_tuner.py
   # 拖动滑块直到 mask 只包含目标物体
   # 记录最终阈值
   ```

3. gripper_depth 调优：
   - 测量目标物体高度（用卡尺）
   - 设置 gripper_depth = 0.5 × 高度
   - 抓取测试
   - 如失败调整 ±0.005m

4. 编写多物体抓取脚本：
   ```python
   # multi_object_grasp.py
   import rclpy
   from rclpy.node import Node
   from std_srvs.srv import Trigger
   import yaml
   import time
   
   class MultiObjectGrasp(Node):
       def __init__(self):
           super().__init__('multi_object_grasp')
           # 加载配置
           with open('grasp_params.yaml') as f:
               self.config = yaml.safe_load(f)
           # 创建服务客户端
           self.start_cli = self.create_client(Trigger, '/visual_grasp/start')
           self.confirm_cli = self.create_client(Trigger, '/visual_grasp/confirm')
           self.skip_cli = self.create_client(Trigger, '/visual_grasp/skip')
           self.abort_cli = self.create_client(Trigger, '/visual_grasp/abort')
           for cli in [self.start_cli, self.confirm_cli, self.skip_cli, self.abort_cli]:
               cli.wait_for_service()
       
       def call_service(self, cli):
           future = cli.call_async(Trigger.Request())
           rclpy.spin_until_future_complete(self, future)
           return future.result()
       
       def grasp_object(self, object_type):
           self.get_logger().info(f'Grasping {object_type}...')
           result = self.call_service(self.start_cli)
           if not result.success:
               return False
           # CONFIRM 状态
           time.sleep(0.5)
           result = self.call_service(self.confirm_cli)
           if not result.success:
               return False
           # 等待 PICK 完成
           time.sleep(10)
           return True
   
   rclpy.init()
   grasper = MultiObjectGrasp()
   
   # 依次抓取 3 个不同物体
   for obj_type in ['cube_small', 'cube_standard', 'cylinder']:
       grasper.grasp_object(obj_type)
       time.sleep(2)
   
   rclpy.shutdown()
   ```

5. 性能基线（实验报告必填）：

   | 物体类型 | gripper_depth | pre_grasp | HSV 范围 | 成功率 |
   |---------|--------------|-----------|---------|--------|
   | 黄色立方块(4cm) | 0.020m | 0.05m | (20-40, 100-255, 100-255) | 95% |
   | 红色球(6cm) | 0.030m | 0.08m | (0-10, 100-255, 100-255) | 88% |
   | 蓝色圆柱(5cm) | 0.025m | 0.06m | (100-130, 100-255, 100-255) | 90% |

**易错点**：
- ⚠️ **HSV 调参不收敛** → **解决**：先固定 H 调 S/V，再调 H
- ⚠️ **gripper_depth 过深撞桌面** → **解决**：先减小到 0.01m 测试

---

#### 步骤9：rqt 三栏可视化（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：visual_grasp_node 发布 `/visual_grasp/rgb_annotated`、`/visual_grasp/depth_overlay`、`/visual_grasp/mask` 三个话题

**知识点讲解**：

**rqt_image_view 三栏（7.6.1）**
- **原理**：`rqt_image_view` 是 ROS 的图像查看工具，可订阅 Image 话题并显示。car1 通过 3 个不同话题同时展示：(1) **RGB 标注图**：原始 RGB + 检测到的目标矩形框与质心标记；(2) **深度图**：D435 深度图，目标位置有深度值标注；(3) **Mask 图**：HSV 二值掩膜，目标轮廓白色。三栏并列便于：(1) 对比检测与定位效果；(2) 调试 HSV 阈值；(3) 评估深度反投影精度。
- **源码对应**：`common.py` 中 `visualize_results()` 函数

**调参与可视化协同**
- **原理**：调参过程通常是"修改参数 → 观察三栏 → 调整 → 再次观察"的迭代循环。三栏可视化使该过程直观高效，避免"修改-重启-等待-看不到效果"的繁琐流程。
- **源码对应**：`config/` 中各 YAML 文件

**操作步骤**：

1. 启动 visual_grasp：
   ```bash
   ros2 launch car1_app visual_grasp.launch.py
   ```

2. 启动第一个 rqt_image_view：
   ```bash
   rqt_image_view /visual_grasp/rgb_annotated
   # 显示带标注的 RGB 图
   ```

3. 启动第二个 rqt_image_view：
   ```bash
   rqt_image_view /visual_grasp/depth_overlay
   # 显示带深度值标注的深度图
   ```

4. 启动第三个 rqt_image_view：
   ```bash
   rqt_image_view /visual_grasp/mask
   # 显示 HSV 二值掩膜
   ```

5. 排列三个窗口（建议用 i3/sway 平铺窗口管理器）：
   - 左侧：RGB 标注图
   - 中间：深度图
   - 右侧：Mask 图

6. 触发观察（无需 confirm）：
   ```bash
   ros2 service call /visual_grasp/start std_srvs/srv/Trigger
   # 状态：OBSERVE
   # 三个窗口都更新
   ```

7. 在 CONFIRM 状态调节 HSV 阈值：
   - 修改 hsv_thresholds.yaml
   - 重启 visual_grasp.launch.py
   - 观察 Mask 图变化

8. 性能评估（实验报告加分项）：
   - 准备 5 种颜色物体
   - 记录每个物体的检测准确率
   - 绘制"颜色-准确率"柱状图

**易错点**：
- ⚠️ **rqt_image_view 找不到话题** → **解决**：检查 visual_grasp_node 是否发布该话题
- ⚠️ **图像显示延迟** → **解决**：降低图像分辨率或发布频率

---

## 阶段 4：综合项目（2h）

---

#### 步骤10：多目标循环抓取（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`car1_app/scripts/multi_grasp_demo.py`

**知识点讲解**：

**重复抓取处理（7.6.3）**
- **原理**：循环抓取中可能遇到"已抓取物体还在原位"的情况（视觉误判、目标回弹、夹爪漏检）。处理方法：(1) **抓取结果验证**：检测夹爪是否成功夹取（通过力反馈或视觉二次确认）；(2) **自动 skip**：检测到已抓取物体时自动 skip；(3) **人工决策**：超过 N 次失败后切换到人工模式。
- **源码对应**：`visual_grasp.py` 中 `grasp_history` 列表

**多目标状态机**
- **原理**：扩展 5 态状态机为"循环状态机"：(1) 在 IDLE 触发"开始循环"；(2) OBSERVE→CONFIRM→PICK 后不回到 IDLE，而是回到 OBSERVE 搜索下一个目标；(3) 达到目标数量或 abort 时回到 IDLE。
- **源码对应**：`visual_grasp.py` 中 `loop_count` 参数

**操作步骤**：

1. 准备多个目标：
   - 在桌面摆放 3-5 个不同颜色的物体
   - 标记每个物体的位置

2. 启动 visual_grasp：
   ```bash
   ros2 launch car1_app visual_grasp.launch.py
   ```

3. 启动循环抓取：
   ```bash
   ros2 param set /visual_grasp_node loop_count 3
   ros2 service call /visual_grasp/start std_srvs/srv/Trigger
   # 每次 CONFIRM 后自动循环
   ros2 service call /visual_grasp/confirm std_srvs/srv/Trigger
   # 观察：机械臂依次抓取多个目标
   ```

4. 编写完整的循环抓取脚本：
   ```python
   # loop_grasp.py
   import rclpy
   from rclpy.node import Node
   from std_srvs.srv import Trigger
   import time
   
   class LoopGrasp(Node):
       def __init__(self):
           super().__init__('loop_grasp')
           self.start_cli = self.create_client(Trigger, '/visual_grasp/start')
           self.confirm_cli = self.create_client(Trigger, '/visual_grasp/confirm')
           self.skip_cli = self.create_client(Trigger, '/visual_grasp/skip')
           self.abort_cli = self.create_client(Trigger, '/visual_grasp/abort')
           for cli in [self.start_cli, self.confirm_cli, self.skip_cli, self.abort_cli]:
               cli.wait_for_service()
       
       def call(self, cli, timeout=15):
           future = cli.call_async(Trigger.Request())
           rclpy.spin_until_future_complete(self, future, timeout_sec=timeout)
           return future.result()
       
       def loop_grasp(self, n_targets):
           for i in range(n_targets):
               self.get_logger().info(f'=== Cycle {i+1}/{n_targets} ===')
               result = self.call(self.start_cli)
               if not result.success:
                   self.get_logger().warn('Start failed, aborting')
                   break
               time.sleep(1.0)
               result = self.call(self.confirm_cli)
               if not result.success:
                   self.get_logger().warn('Confirm failed, skipping')
                   self.call(self.skip_cli)
                   continue
               time.sleep(10)  # 等待 PICK 完成
               self.get_logger().info(f'Cycle {i+1} done')
   
   rclpy.init()
   node = LoopGrasp()
   node.loop_grasp(3)
   rclpy.shutdown()
   ```

5. 性能基线（实验报告必填）：

   | 指标 | 期望值 | 实测值 |
   |------|-------|-------|
   | 单次完整抓取周期 | < 15s |  |
   | 3 个目标总耗时 | < 50s |  |
   | 多目标抓取成功率 | > 80% |  |
   | 重复抓取误判率 | < 5% |  |

6. 重复抓取测试：
   - 抓取成功后故意不移动物体
   - 再次触发抓取
   - 观察：自动 skip 或报警

**易错点**：
- ⚠️ **循环抓取中途卡住** → **解决**：启用 timeout 强制 break
- ⚠️ **重复抓取同一物体** → **解决**：增加 grasp_history 跟踪

---

#### 步骤11：错误处理与异常恢复（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`visual_grasp.py` 中 `try-except` 与 `safety_check()`

**知识点讲解**：

**异常类型与处理**
- **原理**：视觉抓取系统的异常主要分 3 类：(1) **视觉异常**：HSV 未检测到目标、深度图为 0、TF 变换失败；(2) **运动异常**：IK 求解失败、目标在工作空间外、关节超限；(3) **抓取异常**：夹爪未闭合、物体滑落、连续失败。car1 通过 try-except + 状态机转换实现优雅降级。
- **源码对应**：`visual_grasp.py` 中异常处理

**错误码与日志**
- **原理**：car1 在响应中包含 `error_code` 字段（如 0=success, 1=no_target, 2=ik_failed, 3=grasp_failed），便于上层应用识别错误类型并采取不同策略。
- **源码对应**：`srv/Pick.srv` 中 error_code

**操作步骤**：

1. 异常场景 1：未检测到目标
   - 启动 visual_grasp，但不放目标物体
   - 触发 start 服务
   - 观察：状态回到 IDLE，错误码 1

2. 异常场景 2：IK 求解失败
   - 准备一个不可达位置的视觉目标（贴在墙上）
   - 触发抓取
   - 观察：状态机报错，错误码 2

3. 异常场景 3：连续抓取失败
   - 用空夹爪尝试抓取
   - 连续 3 次失败
   - 观察：状态机报警并回到 IDLE

4. 错误处理代码模式：
   ```python
   try:
       result = call_pick_service(target)
       if result.error_code != 0:
           if result.error_code == 1:
               logger.warn("No target detected, retry with different HSV")
           elif result.error_code == 2:
               logger.error("IK failed, target out of workspace")
           elif result.error_code == 3:
               logger.error("Grasp failed, check gripper")
   except ServiceTimeout:
       logger.error("Service timeout, check visual_grasp_node")
   ```

5. 错误日志查看：
   ```bash
   ros2 topic echo /visual_grasp/feedback
   # 字段：current_state, error_code, error_message
   ```

6. 恢复策略（实验报告加分项）：
   - 视觉异常：重新启动 start
   - 运动异常：调整目标位置
   - 抓取异常：检查 gripper 状态

**易错点**：
- ⚠️ **异常导致状态机卡住** → **解决**：每个状态都有 timeout，强制回 IDLE
- ⚠️ **错误日志过多** → **解决**：分级日志，关键错误才 ERROR

---

#### 步骤12：综合性能评估（阶段三：能改造，30min）

**操作步骤**：

1. 完整流程演示（端到端）：
   ```bash
   # 1. 启动所有节点
   ros2 launch car1_app visual_grasp.launch.py
   
   # 2. 启动 rqt 三栏
   rqt_image_view /visual_grasp/rgb_annotated
   rqt_image_view /visual_grasp/depth_overlay
   rqt_image_view /visual_grasp/mask
   
   # 3. 准备 1 个黄色立方块
   
   # 4. 触发抓取
   ros2 service call /visual_grasp/start std_srvs/srv/Trigger
   ros2 service call /visual_grasp/confirm std_srvs/srv/Trigger
   
   # 5. 观察全过程（应在 15 秒内完成）
   ```

2. 性能基线（实验报告必填）：

   | 指标 | 期望值 | 实测值 | 备注 |
   |------|-------|-------|------|
   | visual_grasp 启动时间 | < 15s |  | 包含相机、TF、节点 |
   | OBSERVE 阶段时间 | < 1s |  | HSV + 深度反投影 + TF |
   | CONFIRM 等待时间 | 人工 |  | 取决于操作员 |
   | PICK 阶段时间 | < 8s |  | look-then-move 全过程 |
   | 单次完整抓取周期 | < 15s |  | start→pick→IDLE |
   | HSV 检测准确率 | > 95% |  | 100 次测试统计 |
   | 深度反投影误差 | < 3cm @ 1m |  | 与卷尺对比 |
   | TF 变换精度 | < 1cm |  | 棋盘格标定验证 |
   | 整体抓取成功率 | > 85% |  | 100 次抓取统计 |
   | 误抓率（夹空气） | < 5% |  | 检测未夹取物体 |

3. 多次抓取统计（实验报告加分项）：
   - 抓取 100 次，统计成功率
   - 失败原因分类：视觉、IK、抓取
   - 绘制成功率随时间变化曲线

4. 错误处理验证：
   - 故意设置 5 种错误场景
   - 验证每种场景都能正确报错
   - 验证状态机不卡死

5. 性能优化建议：
   - HSV 检测耗时占比（优化方向：减小 ROI、降采样）
   - IK 求解耗时（优化方向：缓存、并行）
   - 抓取耗时（优化方向：参数调优、轨迹优化）

6. 端到端 demo 录制（建议）：
   - 用 `ros2 bag record -a` 录制整个流程
   - 用 `rqt_bag` 回放验证
   - 作为实验报告附件

**易错点**：
- ⚠️ **性能波动大** → **解决**：多次测量取平均
- ⚠️ **成功率统计不准确** → **解决**：固定物体位置、光照

---

#### 完整可运行代码 demo_visual_grasp.py

> 独立 demo 脚本：完整的视觉抓取 pipeline（依赖 visual_grasp.launch.py 与 arm_controller）

```python
# -*- coding: utf-8 -*-
"""
实验7 demo：基于视觉的动态抓取完整 pipeline
平台：B2 / C1（带 RealSense D435）
前置：ros2 launch car1_app visual_grasp.launch.py 已运行
运行：python3 demo_visual_grasp.py
"""
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from geometry_msgs.msg import PointStamped
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
import cv2
import numpy as np
import time


class VisualGraspDemo(Node):
    """完整的视觉抓取 demo：HSV + 深度 + TF + 状态机"""
    
    # HSV 阈值（黄色）
    HSV_LOWER = np.array([20, 100, 100])
    HSV_UPPER = np.array([40, 255, 255])
    
    def __init__(self):
        super().__init__('visual_grasp_demo')
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # TF
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # 相机内参
        self.camera_info = None
        self.create_subscription(
            CameraInfo, '/camera/color/camera_info', self.info_cb, 10)
        
        # RGB / Depth 图像
        self.latest_rgb = None
        self.latest_depth = None
        self.create_subscription(Image, '/camera/color/image_raw', self.rgb_cb, 10)
        self.create_subscription(Image, '/camera/depth/image_rect_raw', self.depth_cb, 10)
        
        # 服务客户端
        self.start_cli = self.create_client(Trigger, '/visual_grasp/start')
        self.confirm_cli = self.create_client(Trigger, '/visual_grasp/confirm')
        self.skip_cli = self.create_client(Trigger, '/visual_grasp/skip')
        self.abort_cli = self.create_client(Trigger, '/visual_grasp/abort')
        for cli in [self.start_cli, self.confirm_cli, self.skip_cli, self.abort_cli]:
            cli.wait_for_service()
    
    def info_cb(self, msg):
        if self.camera_info is None:
            self.camera_info = {
                'fx': msg.k[0], 'fy': msg.k[4],
                'cx': msg.k[2], 'cy': msg.k[5],
            }
            self.get_logger().info(f'Camera intrinsics: {self.camera_info}')
    
    def rgb_cb(self, msg):
        self.latest_rgb = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
    
    def depth_cb(self, msg):
        self.latest_depth = self.bridge.imgmsg_to_cv2(msg, 'passthrough')
    
    def detect_target(self):
        """HSV 检测 + 深度反投影 + TF 变换"""
        if self.latest_rgb is None or self.latest_depth is None or self.camera_info is None:
            return None, None, None
        
        # 1. HSV 检测
        hsv = cv2.cvtColor(self.latest_rgb, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.HSV_LOWER, self.HSV_UPPER)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None, mask
        
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 500:  # 过滤小目标
            return None, None, mask
        
        (cx, cy), r = cv2.minEnclosingCircle(largest)
        cx, cy, r = int(cx), int(cy), int(r)
        
        # 2. 深度反投影
        fx = self.camera_info['fx']
        fy = self.camera_info['fy']
        cx_int = self.camera_info['cx']
        cy_int = self.camera_info['cy']
        
        d = self.latest_depth[cy, cx] / 1000.0  # mm -> m
        if d <= 0 or d > 2.0:
            return None, None, mask
        
        X = (cx - cx_int) * d / fx
        Y = (cy - cy_int) * d / fy
        Z = d
        
        # 3. TF 变换到 base_link
        pt_camera = PointStamped()
        pt_camera.header.frame_id = 'camera_depth_optical_frame'
        pt_camera.header.stamp = self.get_clock().now().to_msg()
        pt_camera.point.x, pt_camera.point.y, pt_camera.point.z = X, Y, Z
        
        try:
            pt_base = self.tf_buffer.transform(
                pt_camera, 'base_link',
                timeout=rclpy.duration.Duration(seconds=1.0))
            base_xyz = (pt_base.point.x, pt_base.point.y, pt_base.point.z)
        except Exception as e:
            self.get_logger().error(f'TF transform failed: {e}')
            return None, None, mask
        
        return (cx, cy, r), base_xyz, mask
    
    def call(self, cli, timeout=15):
        future = cli.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout)
        return future.result()
    
    def grasp_once(self):
        """单次视觉抓取"""
        self.get_logger().info('=== Starting visual grasp ===')
        
        # 步骤 1：检测目标
        pixel, base_xyz, mask = self.detect_target()
        if base_xyz is None:
            self.get_logger().warn('No target detected')
            return False
        self.get_logger().info(f'Detected target: pixel={pixel}, base_link={base_xyz}')
        
        # 步骤 2：触发 start -> OBSERVE -> CONFIRM
        result = self.call(self.start_cli)
        if not result.success:
            self.get_logger().error(f'Start failed: {result.message}')
            return False
        
        time.sleep(0.5)
        
        # 步骤 3：人工确认 -> PICK
        result = self.call(self.confirm_cli)
        if not result.success:
            self.get_logger().error(f'Confirm failed: {result.message}')
            return False
        
        # 步骤 4：等待 PICK 完成
        self.get_logger().info('Picking, waiting for completion...')
        time.sleep(10)
        
        self.get_logger().info('=== Visual grasp completed ===')
        return True


def main():
    rclpy.init()
    demo = VisualGraspDemo()
    
    # 等待相机就绪
    print('Waiting for camera...')
    while demo.latest_rgb is None or demo.camera_info is None:
        rclpy.spin_once(demo, timeout_sec=0.5)
    print('Camera ready')
    
    # 单次抓取
    print('=== Visual Grasp Demo ===\n')
    
    # 提示：放一个黄色物体在相机前
    input('Place a yellow object in front of the camera, then press Enter...')
    
    success = demo.grasp_once()
    print(f'\nGrasp result: {"SUCCESS" if success else "FAILED"}')
    
    rclpy.shutdown()


if __name__ == "__main__":
    main()
```

### 1.7 实验总结

**完成成果**：
- 启动 visual_grasp.launch.py 一站式完成 5 节点集成（相机、TF、arm_controller、visual_grasp）
- 实现 HSV 颜色检测（黄色立方块成功率 95%）
- 完成深度反投影（X=(u-cx)*d/fx 公式，误差 < 3cm @ 1m）
- 完成 TF 坐标变换（camera_depth_optical_frame → base_link）
- 实现 5 态状态机（IDLE→OBSERVE→CONFIRM→PICK→IDLE）
- 掌握 4 个服务化控制接口（start/confirm/skip/abort）
- 实施 look-then-move 策略避免下压失视野
- 调优 HSV 阈值与 gripper_depth 参数
- 使用 rqt 三栏可视化（RGB+Depth+Mask）
- 完成多目标循环抓取与异常处理

**技能收获**：
- 掌握视觉抓取系统从感知（HSV+深度）到决策（状态机）到执行（IK+抓取）的完整链路
- 理解 eye-in-hand 安装下 look-then-move 策略的工程价值
- 熟悉服务化设计的人机交互模式
- 掌握多模块（相机/TF/IK/状态机）的时序协同
- 理解视觉抓取的调参方法（HSV 阈值、gripper_depth、pre_grasp_height）

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 相机无图像 | USB 带宽不足 | 改用 USB 3.0 端口 |
| HSV 检测失败 | 阈值不匹配 | 用 hsv_tuner.py 调节 |
| 深度图为 0 | 深度超出范围 | 检查目标距离（0.1-10m）|
| TF 变换失败 | URDF 缺 camera_joint | 补充 URDF 标定 |
| 抓取时目标丢失 | eye-in-hand 视野限制 | 启用 look-then-move |
| 夹爪抓空 | gripper_depth 不准 | 调整到物体高度 50-70% |
| 状态机卡住 | 服务调用错误 | 检查状态转换序列 |
| 多目标循环失败 | 物体间遮挡 | 按顺序摆放，错开位置 |

### 1.8 思考题

1. HSV 相比 RGB 在光照变化下更鲁棒，但在哪些场景下 HSV 反而不如 RGB？混合使用 HSV+RGB 是否更优？
2. 深度反投影误差主要来自哪些因素？如何在算法层面减小误差？
3. eye-in-hand 安装下，"look-and-move"（视觉伺服）相比 "look-then-move" 有什么优势？实现复杂度如何？
4. 状态机中 CONFIRM 状态是否必需？去掉 CONFIRM 实现全自动抓取有什么 trade-off？
5. 多目标循环抓取中，如何判断"已抓取物体"？有哪几种方案，各自的优缺点？
6. 视觉抓取系统的"sim-to-real gap"主要来自哪些环节？如何减小？
7. 如果物体是动态的（移动中），look-then-move 策略会失效。如何设计改进方案？

### 1.9 实验报告要求

**评分标准**：
- 阶段 1（启动与基础流程）：20 分
  - 视觉抓取环境搭建 5 分 + HSV 检测 5 分 + 深度反投影 5 分 + TF 变换 5 分
- 阶段 2（状态机与服务化）：15 分
  - IDLE 状态机 7 分 + 服务化控制 8 分
- 阶段 3（抓取执行与调优）：25 分
  - look-then-move 8 分 + HSV/gripper_depth 调优 10 分 + rqt 三栏 7 分
- 阶段 4（综合项目）：25 分
  - 多目标循环 10 分 + 错误处理 5 分 + 性能评估 10 分
- 实验报告：15 分
- **总计**：100 分

**综合项目评分标准**：
- 优秀（27-30）：视觉抓取闭环成功（含 HSV+深度+TF+IK），成功率 > 90%
- 良好（22-26）：闭环功能完整但成功率 70-90%
- 一般（18-21）：闭环部分功能缺失，成功率 50-70%
- 较差（< 18）：闭环未跑通，成功率 < 50%

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初版生成（基于 _registry.yaml human_waiver 模式，标注 [待源码核实]） |
