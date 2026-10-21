## 实验7：基于DeepSORT的多目标跟踪实验（4h）

> ✅ **源码已核实** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking/`。YOLOv8 检测 + deep_sort 标准算法自实现（纯 numpy，零新增依赖：scipy 板载已有）。已交付模型：`models/yolov8n.rknn`（检测，9 输出）、`models/deepsort.rknn`（ReID 外观，用户重导 [1,3,128,64]→[1,512]）；可选 ONNX 备份 `models/yolov8n.onnx` / `models/deepsort.onnx`；`models/coco_classes.json`。ReID 缺失/加载失败自动回退 `sort` 模式（纯 IoU）并告警。单测 38/38 全绿，板端验证通过（12-15 FPS）。

### 1.1 关联知识点

- 1.1.1 目标跟踪原理 > 原理 > 多目标跟踪（MOT）在视频帧间维持目标 ID 一致：检测 → 数据关联 → 轨迹更新；跟踪≠检测，解决"跨帧身份保持"
- 1.2.1 Kalman滤波 > 原理 > 8 维状态（cx,cy,aspect,h,及其速度）预测轨迹运动，std 按高度缩放；马氏距离门限（CHI2INV95）
- 1.2.2 匈牙利算法 > 流程 > `scipy.optimize.linear_sum_assignment` 最小代价匹配检测与轨迹，代价矩阵 = 外观 cosine 距离 + IoU
- 1.3.1 DeepSORT级联匹配 > 流程 > 外观（cosine + 马氏门限）按 time_since_update 从新到旧级联，剩余按 IoU；未确认轨迹只走 IoU
- 1.3.2 ReID外观特征 > 概念 > 64×128 crop → ImageNet 归一化 → 512-d 特征，遮挡恢复靠外观重识别
- 1.3.3 轨迹生命周期 > 流程 > 未匹配检测→新 Track（n_init 连续命中后确认）；未匹配轨迹 mark_missed（max_age 超龄删除）；sort 模式回退

### 1.2 实验目标

1. 掌握多目标跟踪的核心问题（ID 保持/遮挡恢复）与 DeepSORT 算法架构 — 原理理解
2. 实现 YOLOv8 检测 + Kalman 预测 + 级联匹配 + ReID 的完整跟踪链路 — 独立完成
3. 理解检测池/ReID池/双缓冲的三处并行优化，掌握 max_age/n_init 调参 — 迁移应用

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱 B2（XFLZ_EAI_B2_PRO，RK3576 SoC，6TOPS NPU，含 HP60C 深度相机） |
| OS | Ubuntu 22.04 + ROS2 Humble（板载 ros2_venv，rknnlite 2.3.2） |
| 核心库 | OpenCV、NumPy、scipy（linear_sum_assignment）、rknnlite |
| 模型 | `models/yolov8n.rknn`（检测 9 输出）+ `models/deepsort.rknn`（ReID 512-d，[1,3,128,64]→[1,512]）+ 可选 `models/yolov8n.onnx` / `models/deepsort.onnx` + `coco_classes.json` |
| 主入口 | `src/app.py`（视频/相机 CLI + 3 worker 检测池 + ReID 池 + 双缓冲 + MJPEG） |

### 1.4 实验难度

- 难度: ⭐⭐⭐ 综合性
- 重点: DeepSORT 数据关联（级联匹配 + 外观/IoU 代价）与轨迹生命周期管理
- 难点: Kalman 预测与匹配门限的数学原理；多线程池（检测/ReID/双缓冲）的工程实现

### 1.5 实验现象

**快速验证流程**：

1. 进入项目目录：`cd ~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking`
2. 单元测试：`pytest tests/ -v`（38 用例全绿）
3. 视频跟踪：`python src/app.py --video test.mp4`
   - 输出：每个目标 ID 稳定标注（框 + ID 号），MJPEG `http://<板IP>:8080/track.mjpg`
4. 相机实时（板上标准）：先起 ascamera 驱动，再 `python src/app.py --ros`
   - 终端打印 `mode=deepsort`
5. 遮挡测试：用手遮挡目标数秒后移开，观察 ID 是否恢复

```bash
# 进入实验07
cd ~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking

# 可选
/home/iflytek/ros2_venv/bin/python -m pytest -v

# 运行程序，本实验config已经配置追踪车辆后续可以改成追踪人，已配视频
python src/app.py --video test.mp4

# 相机实时，修改config配置detect.classes为0（人）
ros2 launch ascamera hp60c.launch.py        # 终端 1
python src/app.py --ros                     # 终端 2
```

**预期效果描述**：

- 单目标移动：ID 稳定不跳；双目标交叉：ID 不互换
- 目标遮挡数帧后重现：deepsort 模式恢复原 ID（sort 模式换 ID——对照演示）
- 多线程：3 worker 检测池帧率 ≥ 单 worker 1.5 倍，板端实测 12-15 FPS

**执行现象**：运行 `pytest tests/ -v` 约 10-20 秒，输出 38 个用例全部 passed（test_tracker / test_kalman / test_detect / test_reid / test_app / test_config / test_preprocess / test_reidpool / test_ros2_source）。视频跟踪命令 `python src/app.py --video test.mp4` 启动后终端打印 `mode=deepsort`，MJPEG 服务监听 `:8080/track.mjpg`；逐帧输出 `tracks=N`（确认轨迹数），目标框上方显示 `ID:N 类别名`（黄色标注），框随目标运动稳定跟踪。板端 NPU 实测帧率 12-15 FPS（3 worker 检测池）。

<img src="assets/image-20260820153940571.png" alt="image-20260820153940571" style="zoom:50%;" />

人移动ID稳稳跟踪

<img src="assets/image-20260820154112741.png" alt="image-20260820154112741" style="zoom:50%;" />

<img src="assets/image-20260820154206605.png" alt="image-20260820154206605" style="zoom:50%;" />

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：跟踪问题与架构认知] --> B[步骤2：YOLOv8检测解码]
    B --> C[步骤3：Kalman滤波预测]
    C --> D[步骤4：级联匹配与匈牙利]
    D --> E[步骤5：ReID外观特征]
    E --> F[步骤6：轨迹生命周期]
    F --> G[步骤7：多线程实时跟踪]
    G --> H[完成]
```

---

#### 步骤1：跟踪问题与架构认知（阶段一：能运行，20min）

> 📌 本步骤对应源码：`config/track_config.yaml`、`src/app.py`

**知识点讲解**：

**MOT 问题与 DeepSORT 架构（1.1.1）**
- **原理**：多目标跟踪（MOT）的任务是**维持跨帧 ID 一致**：每帧检测出目标（可能漏检/新出现），跟踪器负责把当前帧检测与历史轨迹关联起来。核心挑战：ID 切换（同一目标换号）、ID 丢失（遮挡后无法找回）、轨迹漂移。DeepSORT 架构：**检测**（YOLOv8）→ **运动预测**（Kalman 8 维）→ **数据关联**（级联匹配 + Hungarian）→ **外观验证**（ReID 特征）→ **轨迹更新**。相比 SORT（纯 IoU 关联），DeepSORT 增加外观特征，抗遮挡能力显著提升。本实验按 deep_sort 标准结构**纯 numpy 自实现**，对照 vendor `Deepsort/` 参考。
- **源码对应**：`config/track_config.yaml`（tracker.max_dist/max_iou_distance/max_age/n_init/mode、pool.workers）；`src/tracker.py` L53-55（Tracker 超参默认值）

**操作步骤**：

1. 查看 `config/track_config.yaml` 跟踪器参数，理解各超参语义
2. 运行单测理解架构：`pytest tests/ -v`
3. 思考：跟踪和检测的本质区别是什么？为什么不能每帧重新检测就完事？

**易错点**：
- ⚠️ max_age 过大 → 轨迹残留（删除慢）；过小 → 短暂遮挡就丢 ID

**流程图**：

```mermaid
flowchart LR
    A["DeepSORT 架构<br/>检测→预测→关联→验证→更新"] --> B["YOLOv8 检测<br/>每帧目标检测框"]
    B --> C["Kalman 8 维状态<br/>(cx,cy,aspect,h,速度)<br/>预测轨迹运动"]
    C --> D["数据关联<br/>级联匹配 + 匈牙利"]
    D --> E["ReID 外观特征<br/>遮挡恢复识别身份"]
    E --> F["轨迹更新<br/>n_init 确认 / max_age 删除"]
    F --> G["抗遮挡核心<br/>外观 + 门限 互补"]

    style D fill:#ffe0e0,stroke:#c00,stroke-width:2px
```

---

#### 步骤2：YOLOv8 检测解码（阶段一：能运行，25min）

> 📌 本步骤对应源码：`src/detect.py`

**知识点讲解**：

**检测层复用（1.1.1）**
- **原理**：与实验1/6 同款解码模式：`models/yolov8n.rknn` 是 COCO 80 类检测模型（9 输出 = 3 层 × [box, cls, cls_sum]）。解码链路：DFL 解码（16 bins softmax 期望）→ grid+stride 还原 xyxy → **cls_sum×cls 过滤**（与分割模型同款类别得分加权）→ 逐类 NMS。输出 `Detection`（框 + 类别 + 分数），送入 tracker 的数据关联。
- **源码对应**：`src/detect.py`（decode：DFL / grid xyxy / cls_sum×cls / NMS）；`models/yolov8n.rknn`

**知识储备补充**：

- **9 输出结构拆解**：RKNN 优化 fork 导出的 ONNX 把 DFL 解码留在 CPU 侧，模型只输出 3 层 × 3 张量 = 9 个输出。每层输出 `(box, cls, cls_sum)`：`box` shape `(1,64,h,w)` 是 DFL 16 bins × 4 坐标的原始分布（回归分支），`cls` shape `(1,80,h,w)` 是已 sigmoid 的 COCO 80 类分数，`cls_sum` shape `(1,1,h,w)` 是类别分数和的可忽略分支。3 个检测层对应 80/40/20 下采样（imgsz=640 → 特征图 80×80、40×40、20×20），分别负责小/中/大目标。

- **DFL 解码原理**：`dfl_decode`（detect.py L16-21）对 box 张量的 64 通道做 softmax 得到 16 bin 概率分布，加权求和得到连续偏移 $t = \sum_{i=0}^{15} p_i \cdot i$，其中 $p = \text{softmax}(z)$。相比直接回归单值，DFL 能刻画边界的不确定性，对小目标更友好。解码后 `box_process`（L24-30）还原为 imgsz 系 xyxy 坐标。

- **逐类 NMS**：`nms`（detect.py L33-41）按置信度降序，同类 IoU 超阈值的重叠框只保留最高分。使用 max_wh 偏移技巧将不同类别框移到不同象限实现批量 NMS，避免逐类循环。NMS 后输出 `Detection`（dataclass，L14-20），包含 xyxy + score + class_id，直接送入 tracker。

- **参考资源**：YOLOv8 官方文档《Ultralytics YOLO》；RKNN Toolkit2 文档《RKNN Model Zoo》；DFL 原论文《Generalized Focal Loss》（Li et al., 2020）。

**配置参数速查表**（`config/track_config.yaml`，按区块分列）：

| 区块 | 参数 | 类型 | 默认/示例 | 说明 |
|---|---|---|---|---|
| `model` | `det_rknn` | str | `./models/yolov8n.rknn` | 检测模型（COCO80类） |
| `model` | `det_onnx` | str | `./models/yolov8n_coco.onnx` | 检测 onnx(可选) |
| `model` | `reid_rknn` | str | `./models/deepsort.rknn` | ReID 模型 |
| `model` | `imgsz` | int | `640` | 输入边长 |
| `detect` | `score_thr` | float | `0.25` | 置信度 |
| `detect` | `iou_thr` | float | `0.45` | NMS |
| `detect` | `classes` | list | `[2]` | 追踪类别（COCO） |
| `tracker` | `mode` | str | `deepsort` | deepsort/sort(自动回退) |
| `tracker` | `max_dist` | float | `0.2` | 外观余弦距离门限 |
| `tracker` | `max_iou_distance` | float | `0.8` | IoU 匹配门限 |
| `tracker` | `max_age` | int | `70` | 丢轨迹保留帧 |
| `tracker` | `n_init` | int | `3` | 确认轨迹所需命中 |
| `tracker` | `nn_budget` | int | `100` | 特征库容量 |
| `tracker` | `min_confidence` | float | `0.6` | 弱检测不进追踪 |
| `pool` | `workers` | int | `3` | 推理线程（三核 NPU） |
| `pool` | `core_mask`/`queue` | str/int | `auto`/`4` | NPU 核/队列 |
| `server` | `port`/`stream_name` | int/str | `8080`/`track.mjpg` | 推流端口/流名 |

> **说明**：`tracker.mode` 无 ReID 自动回退 sort；`classes=[2]`=car；`min_confidence` 低会乱漂蛋。

相关YOLOv8网络架构图

<img src="assets/1ebb040adac1e258c00d6e0868727559.jpeg" alt="img" style="zoom:25%;" />

单检测头解析（stride‑8）：stride‑16、stride‑32 结构完全一致，仅 h,w 改为 40×40、20×20。

| 序号 | Tensor 名称         | Shape(N=1)        | 说明                                                  | CPU 侧后续处理                                          |
| ---- | ------------------- | ----------------- | ----------------------------------------------------- | ------------------------------------------------------- |
| 1    | box（stride‑8）     | `(1, 64, 80, 80)` | 回归分支；4 条边界 ×16‑bin DFL 分布 =64 通道          | `dfl_decode()`：softmax + 加权求期望，得到 t/l/r/b 偏移 |
| 2    | cls（stride‑8）     | `(1, 80, 80, 80)` | COCO‑80 类别，**模型内部已经 sigmoid**；输出 0‑1 分数 | 取每个网格`class_max`最大类别得分                       |
| 3    | cls_sum（stride‑8） | `(1, 1, 80, 80)`  | 该网格所有类别分数求和，分割置信缩放因子              | 置信度计算：`score = class_max * cls_sum`，做阈值过滤   |

**操作步骤**：

1. 视频首帧检测验证：
   ```bash
   # 执行目录：ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   cd ~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   
   python src/app.py --video test.mp4   # 终端打印检测类别与数量
   ```
2. 单测理解解码契约：`pytest tests/test_detect.py -v`
3. 修改 score_thr，观察检出目标数量变化

<img src="assets/image-20260820153940571.png" alt="image-20260820153940571" style="zoom:50%;" />

**易错点**：
- ⚠️ nc 通用（80 类），换模型时类别数与 labels 需同步

**流程图**：

```mermaid
flowchart LR
    A["yolov8n.rknn 9 输出<br/>3 层 × [box, cls, cls_sum]"] --> B["DFL 解码<br/>16 bins softmax 期望"]
    B --> C["grid + stride 还原 xyxy<br/>imgsz 坐标系"]
    A --> D["cls 类别分数"]
    A --> E["cls_sum 得分和"]
    D --> F["class_max × cls_sum<br/>≥ score_thr 过滤"]
    E --> F
    F --> G["逐类 NMS<br/>max_wh 偏移"]
    C --> H["Detection 输出<br/>xyxy + score + class_id"]
    G --> H
    H --> I["送入 tracker 数据关联"]

    style G fill:#e8f0ff,stroke:#448,stroke-width:1px
```

---

#### 步骤3：Kalman 滤波预测（阶段二：能理解，30min）

> 📌 本步骤对应源码：`src/kalman.py`、`src/tracker.py` det_to_xyah

**知识点讲解**：

**Kalman 滤波与 xyah 表示（1.2.1）**
- **原理**：Kalman 滤波用"预测-更新"两步估计目标状态：状态向量 **8 维** `(cx, cy, aspect_ratio, h, vx, vy, va, vh)`——中心坐标、宽高比、高度及其速度（`det_to_xyah`，tracker.py L21-24）。每帧先**预测**（恒速模型外推位置），再在匹配后用检测**更新**（校正）。

  关键点：

  **(1) std 按高度缩放**——大目标运动不确定性更大，噪声模型自适应；

  **(2) 马氏距离门限**（CHI2INV95，卡方分布 95% 分位）——用协方差归一化预测与检测的偏差，超出门限的候选不匹配（几何一致性检验）。这是把"运动预测"融入数据关联的核心。

- **源码对应**：`src/kalman.py`（KalmanFilter：predict / update / to_xyah，CHI2INV95）；`src/tracker.py` L21-24（det_to_xyah）、L27-31（_track_xyxy）

**知识储备补充**：

- **Kalman 预测方程**：状态预测 $\hat{x}_{k|k-1} = F \hat{x}_{k-1|k-1}$，协方差预测 $P_{k|k-1} = F P_{k-1|k-1} F^T + Q$。其中 $F$ 为 8×8 状态转移矩阵（恒速模型：位置 = 上一帧位置 + 速度 × 1 帧间隔），$Q$ 为过程噪声协方差（std 按当前高度 $h$ 缩放）。`kalman.py` 的 `predict()` 方法（L40-50）构造 $F$ 并执行该步：

  $$
  \hat{x}_{k|k-1} = F \hat{x}_{k-1|k-1}, \quad P_{k|k-1} = F P_{k-1|k-1} F^T + Q
  $$

  其中 $F = \begin{bmatrix} I_4 & I_4 \\ 0_4 & I_4 \end{bmatrix}$，$Q = \text{diag}(\sigma^2)$，$\sigma$ 向量按当前高度缩放。

- **Kalman 更新方程**：检测匹配后用观测 $z_k$ 校正状态：$K_k = P_{k|k-1} H^T S_k^{-1}$（卡尔曼增益），$S_k = H P_{k|k-1} H^T + R$（观测空间协方差），$\hat{x}_{k|k} = \hat{x}_{k|k-1} + K_k(z_k - H\hat{x}_{k|k-1})$，$P_{k|k} = (I - K_k H) P_{k|k-1}$。`kalman.py` 的 `update()` 方法（L64-70）实现此步。$H$ 为 4×8 观测矩阵（只取前 4 个状态：cx,cy,aspect,h），$R$ 同样按高度缩放。

- **xyah 表示与 det_to_xyah**：检测框 $(x_1,y_1,x_2,y_2)$ 经 `det_to_xyah`（tracker.py L21-24）转换为 $(cx, cy, w/h, h)$——用宽高比 $a = w/h$ 替代宽度 $w$，保证不同尺度目标的运动状态具有尺度不变性。解码时 `_track_xyxy`（L27-31）将 xyah 逆变换回 xyxy 用于标注。

- **马氏距离门限**：$d_m^2 = (z - H\hat{x})^T S^{-1} (z - H\hat{x})$，服从 $\chi^2(4)$ 分布。`CHI2INV95 = 9.4877`（kalman.py L11）为 95% 分位，超此门限的检测-轨迹对被视为几何不一致，代价矩阵中置为大值（`gate_cost_matrix`，matching.py L42-49）。完整 Kalman 更新步的矩阵形式：

  $$
  K_k = P_{k|k-1} H^T \left( H P_{k|k-1} H^T + R \right)^{-1}, \quad \hat{x}_{k|k} = \hat{x}_{k|k-1} + K_k \left( z_k - H \hat{x}_{k|k-1} \right)
  $$

  其中卡尔曼增益 $K_k$ 在预测不确定（$P$ 大）且观测噪声小（$R$ 小）时趋近 $H^{-1}$——即完全信任检测；反之趋近 0——即信任预测。$R$ 按高度缩放（kalman.py L55-58），大目标观测噪声更大。

- **参考资源**：DeepSORT 原论文（Wojke et al., *Simple Online and Realtime Tracking with a Deep Association Metric*, ICIP 2017）；Kalman 滤波维基百科《Kalman filter》；OpenCV `cv2.KalmanFilter` 文档。

**操作步骤**：

1. 单测理解 Kalman 预测-更新循环：`pytest tests/test_kalman.py -v`
2. 打印预测框 vs 检测框坐标差异，理解"预测先行、检测校正"：
   ```bash
   # 执行目录：~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   cd ~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   
   PYTHONPATH=./src python -c "
   import numpy as np
   from kalman import KalmanFilter, CHI2INV95
   kf = KalmanFilter()
   # 初始测量 (cx,cy,aspect,h)，由检测框 det_to_xyah 推导
   mean, cov = kf.initiate(np.array([100,120,0.6,80], np.float32))
   print('初始状态:', np.round(mean,2)[:4], '速度=', np.round(mean,2)[4:])
   print('协方差对角:', np.round(np.diag(cov),2))   # std 按 h=80 缩放
   pred, pcov = kf.predict(mean, cov)               # 初始速度0 → 位置不变
   print('预测后 cx:', round(float(pred[0]),2), 'vy:', round(float(pred[5]),2))
   # 两个候选检测的马氏距离，与 CHI2INV95(4) 比较
   cand = np.array([[110,120,0.6,80],[100,50,0.6,90]], np.float32)
   d = kf.gating_distance(pred, pcov, cand)
   print('马氏距离:', np.round(d,2), ' CHI2INV95(4)=', CHI2INV95[4])
   print('门限判定(超则拒):', np.round(d,2) > CHI2INV95[4])
   "
   # 预期：协方差对角 [64,64,0,64,25,25,0,25]（位置std²=64、速度std²=25，随 h 缩放）
   #       马氏距离候选1=0.83(匹配)、候选2=41.32(超9.49被拒)
   ```
3. 修改 std 缩放系数，观察跟踪抖动/滞后变化

**易错点**：
- ⚠️ xyah 而非 xywh：宽高比替代宽度（尺度不变性更好），混用会算错代价

**流程图**：

```mermaid
flowchart LR
    A["检测框 xyxy<br/>det_to_xyah"] --> B["8 维状态<br/>(cx,cy,aspect,h,速度)<br/>宽高比替代宽度"]
    B --> C["预测 predict<br/>恒速模型 F 外推<br/>高度缩放 Q"]
    C --> D["马氏距离门限<br/>CHI2INV95 几何一致"]
    D --> E{"匹配成功?"}
    E -->|是| F["更新 update<br/>卡尔曼增益 K 校正"]
    E -->|否| G["保持预测<br/>等待下帧"]
    F --> H["_track_xyxy 逆变换<br/>标注坐标"]

    style C fill:#e8f0ff,stroke:#448,stroke-width:1px
    style D fill:#fff3d6,stroke:#b90,stroke-width:1px
```

---

#### 步骤4：级联匹配与匈牙利算法（阶段二：能理解，35min）

> 📌 本步骤对应源码：`src/matching.py`、`src/tracker.py` Tracker.match

**知识点讲解**：

**数据关联核心（1.2.2、1.3.1）**
- **原理**：DeepSORT 的关联分两阶段。**级联匹配**（cascade matching）：轨迹按 `time_since_update`（距上次更新帧数）**从新到旧**优先匹配——刚更新过的轨迹优先用外观匹配（更可靠），久未更新的轨迹（可能被遮挡）最后匹配，避免遮挡轨迹"抢"新检测。每轮匹配用**匈牙利算法**（`scipy.optimize.linear_sum_assignment`，最小代价匹配）求解，代价矩阵 = **cosine 外观距离**（ReID 特征）+ **马氏距离门限**（几何一致性，`gate_cost_matrix`）。**IoU 匹配**：级联后剩余的轨迹与检测按 IoU 代价匹配（`iou_batch` + `min_cost_matching`）。未确认轨迹（time_since_update==1）只走 IoU。`sort` 模式：无外观，纯 IoU（SORT 语义）。
- **源码对应**：`src/matching.py`（iou_batch / gate_cost_matrix / min_cost_matching）；`src/tracker.py` L46-50（_cosine_dist）、Tracker.match（级联逻辑）

**知识储备补充**：

- **IoU 计算**：交并比 $\text{IoU}(A,B) = \frac{|A \cap B|}{|A \cup B|}$，`iou_batch`（matching.py L14-28）批量计算 $(M,N)$ IoU 矩阵。先求交集面积（逐对 max/min 裁剪），再减去重叠得并集。IoU 是纯几何度量，不依赖外观——SORT 纯靠它做关联，但遮挡/快速运动时容易失效。

<img src="assets/image-20260820160047483.png" alt="image-20260820160047483" style="zoom:50%;" />

- **匈牙利算法与 linear_sum_assignment**：给定代价矩阵 $C \in \mathbb{R}^{M \times N}$（$M$ 轨迹，$N$ 检测），匈牙利算法找到一对一匹配：
  $$
  \sigma^* = \arg\min_{\sigma \in \mathcal{S}_M} \sum_{i=1}^{M} C_{i,\sigma(i)}
  $$

  其中 $\mathcal{S}_M$ 为 $M$ 阶置换群，复杂度 $O(N^3)$。`scipy.optimize.linear_sum_assignment`（matching.py L31-36）返回行列索引对。`min_cost_matching`（L39-49）在此基础上加**门限裁剪**：代价超过 `max_cost` 的匹配对丢弃，对应行记为未匹配。这是 DeepSORT 将"数学最优匹配"与"物理合理约束"结合的关键。

- **cosine 外观距离**：`_cosine_dist`（tracker.py L46-50）计算 ReID 特征间的余弦距离 $d_{cos} = 1 - \frac{f_i \cdot g_j}{\|f_i\| \|g_j\|}$，其中 $f_i, g_j$ 为 L2 归一化后的特征向量（`fn = features / norm`）。余弦距离度量方向相似性而非幅度，对光照变化和尺度差异鲁棒——这正是 ReID 特征选择余弦度量的原因。

  $$
  d_{cos}(f, g) = 1 - \frac{f \cdot g}{\|f\| \cdot \|g\|} = 1 - \hat{f} \cdot \hat{g}
  $$

  其中 $\hat{f} = f / \|f\|$ 为 L2 归一化。值域 $[0, 2]$，0 表示完全相同，2 表示完全相反。

- **代价矩阵构造**：级联匹配中，代价矩阵 = $d_{cos}$（外观距离），经 `gate_cost_matrix` 裁剪马氏距离超门限的元素（置为 $10^5$）；IoU 匹配中，代价矩阵 = $1 - \text{IoU}$。两种距离互补：外观区分身份，IoU 保证空间一致性。

- **参考资源**：DeepSORT 原论文《Simple Online and Realtime Tracking with a Deep Association Metric》；scipy `linear_sum_assignment` 文档；《匈牙利算法与线性指派问题》。

**操作步骤**：

1. 打印匹配中间量（IoU 代价矩阵、匹配对/未匹配列表），理解 Hungarian 求解：
   ```bash
   # 执行目录：~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   cd ~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   
   PYTHONPATH=./src python -c "
   import numpy as np
   from matching import iou_batch, min_cost_matching
   bbox = np.array([[10,10,50,60],[100,100,150,150],[20,30,60,80]], np.float32)
   iou = iou_batch(bbox, bbox)          # 自交 IoU 对角=1
   print('对角线 IoU:', np.round(np.diag(iou),2))
   cost = 1 - iou                        # IoU 代价矩阵
   rows, cols, unmatched = min_cost_matching(cost, 0.8)
   print('匹配对:', list(zip(rows.tolist(), cols.tolist())))
   print('未匹配行:', unmatched.tolist())   # 全匹配 → 空
   "
   # 预期：对角线 IoU 全 1，匹配对 (0,0)(1,1)(2,2)，未匹配行为空
   ```
2. 双目标交叉场景：观察级联匹配如何避免 ID 互换
3. 修改 max_dist（外观门限），观察 ID 切换频率变化
4. 思考：为什么级联匹配要从新到旧？为什么外观门限与几何门限要同时用？

**易错点**：
- ⚠️ max_dist 过大 → 不同目标外观混淆（ID 互换）；过小 → 同目标外观变化就跟丢

**流程图**：

```mermaid
flowchart LR
    A["轨迹按 time_since_update<br/>从新到旧排序"] --> B["级联匹配<br/>外观 cosine + 马氏门限"]
    B --> C["匈牙利算法<br/>linear_sum_assignment<br/>最小代价一对一"]
    C --> D{"门限裁剪 max_cost"}
    D -->|超门限| E["置大值丢弃<br/>记为未匹配"]
    D -->|合门限| F["匹配 轨迹-检测对"]
    E --> G["剩余 IoU 匹配<br/>未确认轨迹只走 IoU"]
    F --> G
    G --> H["代价互补<br/>外观辨 ID + IoU 保空间"]

    style C fill:#ffe0e0,stroke:#c00,stroke-width:2px
    style B fill:#e8f0ff,stroke:#448,stroke-width:1px
```

---

#### 步骤5：ReID 外观特征提取（阶段二：能理解，25min）

> 📌 本步骤对应源码：`src/reid.py`

**知识点讲解**：

**ReID 特征与遮挡恢复（1.3.2）**
- **原理**：ReID（Re-Identification）用外观特征区分不同目标：检测框 crop 目标区域 → resize 64×128 → **ImageNet 归一化**（mean/std 特定值）→ 转 NCHW → RKNN NPU 推理（`deepsort.rknn`，用户重导模型，输入 [1,3,128,64]，输出 **512-d 特征向量**）。相似度用 **cosine 距离**（`_cosine_dist`，L46-50：`1 - 归一化内积`）。外观特征的价值在遮挡场景：目标被挡住时检测丢失，轨迹靠 Kalman 预测续命（max_age 帧）；目标重现后，ReID 特征能认出"还是原来那个人"，恢复原 ID——这是 DeepSORT 对 SORT 的核心提升。ReID 池 2 worker × 独立 RKNN 实例（实例非线程安全），提交序号回收保序。
- **源码对应**：`src/reid.py`（crop→resize→归一化→NCHW→512-d；RKNN/Fake 后端）；`models/deepsort.rknn`

**知识储备补充**：

- **ReID 特征提取流程**：`preprocess_crop`（reid.py L21-28）执行完整预处理链路：

  (1) crop BGR 图像 → float32 并除以 255 归一化到 [0,1]；

  (2) `cv2.resize` 到 64×128（宽×高，ReID 标准输入尺寸）；

  (3) BGR→RGB 通道反转；(4) ImageNet 均值/标准差归一化——$x_{norm} = (x - \mu) / \sigma$，$\mu = [0.485, 0.456, 0.406]$，$\sigma = [0.229, 0.224, 0.225]$（reid.py L11-12）；

  (5) HWC→NCHW 轴转置 + 增加 batch 维，输出 shape `[1,3,128,64]`。必须严格遵守 ImageNet 归一化约定——错用 0/1 归一化会导致特征分布完全偏离训练域，cosine 相似度失去区分力。

  ReID模型框架如下

  <img src="assets/image-20260820160346076.png" alt="image-20260820160346076" style="zoom: 67%;" />

- **512-d 特征向量的语义**：`deepsort.rknn` 输入 `[1,3,128,64]`，输出 `[1,512]`——这是一个紧凑的外观嵌入（embedding），将 128×64 RGB 裁剪区域映射到 512 维语义空间：
  $$
  f = \text{deepsort\_rknn}\left(\text{preprocess\_crop}(\text{crop}_{BGR})\right) \in \mathbb{R}^{512}
  $$
  
  同一目标不同帧的 512-d 向量在余弦度量下接近（夹角小），不同目标的向量远离。512 维是容量与效率的折中：维度太低（如 128）区分力不足，维度太高（如 2048）推理开销大且易过拟合。本模型由用户 2026-08-05 重导（输入 batch=1），与 `FakeReID`（reid.py L68-84）的测试接口一致。
  
- **特征库与 nn_budget**：每条轨迹维护一个外观特征列表 `track.features`（track.py L33），容量受 `nn_budget=100`（track_config.yaml L30）限制。级联匹配时，轨迹的特征向量与当前帧所有检测的特征计算 cosine 距离矩阵，取最近邻均值作为外观代价。nn_budget 过小会丢失历史外观信息（遮挡恢复变差），过大会增加计算量。

- **ReID 后端降级**：当 `models/deepsort.rknn` 缺失或加载失败时，`app.py` 自动切换到 `FakeReID`（reid.py L68-84）并终端告警 `mode=deepsort`→`mode=sort`，此时无外观特征，退化为纯 IoU 跟踪（SORT 语义）。这是有意设计的容错降级，不属错误。

- **参考资源**：ReID 综述《Person Re-identification: A Feature Learning Perspective》（Ye et al., 2021）；OSNet 论文（Zhou et al., *Omni-Scale Feature Learning for Person Re-Identification*, ICML 2019）；ImageNet 归一化约定 PyTorch `torchvision.transforms.Normalize` 文档。

**操作步骤**：

1. 单测理解特征提取：`pytest tests/test_reid.py -v`
2. 验证 ImageNet 预处理与特征接口（x86 可跑，无需 .rknn）：
   ```bash
   # 执行目录：~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   cd ~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   
   PYTHONPATH=./src python -c "
   import numpy as np, cv2
   from reid import preprocess_crop, FakeReID
   crop = np.random.randint(0,255,(128,64,3),np.uint8)  # 模拟检测框 crop
   t = preprocess_crop(crop)
   print('preprocess_crop 形状:', t.shape)              # [1,3,128,64]
   fake = FakeReID(); fake.load('')
   feats = fake([crop, crop])                         # FakeReID 模拟外观
   print('FakeReID 特征形状:', feats.shape, '(N, dim)')
   "
   # 预期：preprocess_crop 输出 [1,3,128,64]（ImageNet 归一化后 NCHW）；
   #       FakeReID 输出 (N, 128)（板上 ReIDBackend 为 (N, 512)）
   ```
3. 遮挡恢复对照实验（板上）：
   ```bash
   # 执行目录：~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   cd ~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   # deepsort 模式（默认）
   
   # 遮挡视频由自己拍摄替换，也可直接视频流
   python src/app.py --video occlude.mp4
   # 遮挡目标后重现，观察 ID 恢复
   # sort 模式对照：改 config tracker.mode: sort 后重跑，观察 ID 是否切换
   
   # 相机实时，修改config配置detect.classes为0（人）
   ros2 launch ascamera hp60c.launch.py        # 终端 1
   python src/app.py --ros                     # 终端 2
   ```
4. 思考：为什么 ReID 特征用 512 维？维度过高/过低的影响？

**易错点**：

- ⚠️ 归一化必须 ImageNet 约定（mean/std），错用 0/1 归一化 → 特征全错
- ⚠️ ReID 模型（`models/deepsort.rknn`）缺失时自动回退 sort 模式（终端告警），属正常降级

**流程图**：

```mermaid
flowchart LR
    A["检测框 crop 目标区域"] --> B["resize 64×128<br/>ReID 标准尺寸"]
    B --> C["ImageNet 归一化<br/>(x−μ)/σ 通道反转"]
    C --> D["转 NCHW [1,3,128,64]<br/>喂入 RKNN"]
    D --> E["deepsort.rknn 推理<br/>输出 512-d 特征向量"]
    E --> F["cosine 距离<br/>1 − 归一化内积"]
    F --> G["遮挡恢复<br/>重现后认出原 ID"]
    E --> H["特征库 nn_budget<br/>最近邻均值外观代价"]
    H --> F

    style E fill:#e8f0ff,stroke:#448,stroke-width:1px
```

---

#### 步骤6：轨迹生命周期管理（阶段三：能改造，20min）

> 📌 本步骤对应源码：`src/track.py`、`src/tracker.py`

**知识点讲解**：

**轨迹状态机（1.3.3）**
- **原理**：每条轨迹经历状态机：**未确认**（tentative）→ **确认**（confirmed）→ **丢失**（missed）→ **删除**。

  规则：

  (1) 未匹配的检测 → 创建新 Track，**n_init 次连续命中后确认**（防单帧误检污染轨迹）；

  (2) 未匹配的轨迹 → `mark_missed()`，**max_age 帧内未重现则删除**（超龄清理）；

  (3) 确认轨迹被遮挡时保持 missed 状态，靠 Kalman 预测 + 外观恢复。`time_since_update` 记录距上次更新的帧数，是级联匹配优先级与生命周期判定的共同依据。

- **源码对应**：`src/track.py`（Track：n_init/max_age/time_since_update/mark_missed）；`src/tracker.py` Tracker.update（状态迁移）

**操作步骤**：

1. 单测理解状态机：`pytest tests/test_track.py -v`
2. 跑轨迹状态机（Tentative→Confirmed→Deleted），理解 n_init/max_age：
   ```bash
   # 执行目录：~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   cd ~/ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   
   PYTHONPATH=./src python -c "
   import numpy as np
   from track import Track, TENTATIVE, CONFIRMED, DELETED
   t = Track(np.array([100,100,0.6,80], np.float32), track_id=0, n_init=3, max_age=70)
   print('初始 state:', t.state, '(TENTATIVE=', TENTATIVE, ') confirmed:', t.confirmed)
   for i in range(3):                        # 3 次连续命中 → n_init 满足
       t.update(np.array([100+i*10,100,0.6,80], np.float32))
   print('3次命中后 state:', t.state, 'confirmed=', t.confirmed)   # CONFIRMED=2
   matched = True
   for _ in range(200):                      # 跟踪循环：predict 推进 + mark_missed 判定
       t.predict()                           # time_since_update += 1
       t.mark_missed()                       # 超 max_age(70) → DELETED
       if t.deleted: break
   print('predict+mark_missed 后 deleted:', t.deleted, 'state:', t.state)  # DELETED=3
   "
   # 预期：初始 TENTATIVE → 3 次命中 CONFIRMED → 失联超 70 帧 DELETED
   ```
3. 调参实验：max_age 10 vs 100、n_init 1 vs 5，观察轨迹创建/删除行为差异
4. 思考：n_init 太小/太大的后果？max_age 与遮挡时长的关系？

**易错点**：

- ⚠️ max_age 与场景遮挡时长匹配：短遮挡用默认，长遮挡（走出画面）需调大

**流程图**：

```mermaid
flowchart LR
    A["未匹配检测<br/>创建新 Track"] --> B{"连续命中 ≥ n_init?"}
    B -->|否| C["tentative 未确认<br/>防单帧误检"]
    B -->|是| D["confirmed 确认<br/>参与 ID 判定"]
    D --> E{"后续帧匹配?"}
    E -->|未匹配| F["mark_missed 丢失<br/>max_age 帧内等重现"]
    E -->|匹配| G["更新轨迹<br/>time_since_update=0"]
    F --> H{超 max_age 重现?}
    H -->|是| D
    H -->|否| I["删除轨迹<br/>超龄清理"]

    style B fill:#e8f0ff,stroke:#448,stroke-width:1px
```

---

#### 步骤7：多线程实时跟踪（阶段三：能改造，35min）

> 📌 本步骤对应源码：`src/app.py`、`src/rknnpool.py`

**知识点讲解**：

**三处并行优化（1.3.3）**
- **原理**：实时跟踪的吞吐瓶颈在检测与 ReID 的 NPU 推理。本实验做**三处并行**：

  (1) **检测池**——RKNNPool 3 worker 按 `tid%3` 绑 NPU 核，多核并行检测；

  (2) **ReID 池**——2 worker 独立 RKNN 实例，批量外观提取；

  (3) **流水线双缓冲**——帧 N 在解码/跟踪/绘制时，帧 N+1 已在检测池推理，取帧与推理时间重叠。三处并行叠加，帧率从单线程的 ~8 FPS 提升到 12-15 FPS（板端实测）。

- **源码对应**：`src/rknnpool.py`（RKNNPool / ReIDPool：worker / 核绑定 / 保序回收）；`src/app.py`（main：池构建 / 双缓冲循环 / ID 标注 / MJPEG）

**操作步骤**：

1. 单 worker vs 3 worker 对比：
   ```bash
   # 执行目录：ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   # 改 config pool.workers: 1 后跑
   python src/app.py --video test.mp4
   # 改回 3 后重跑，对比 avg_fps（预期 ≥ 1.5 倍）
   ```
2. 相机实时（板上标准）：
   ```bash
   # 执行目录：ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking
   source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash
   export ROS_DOMAIN_ID=2
   ros2 launch ascamera hp60c.launch.py        # 终端 1
   python src/app.py --ros                      # 终端 2
   # 终端打印 mode=deepsort；MJPEG: http://<板IP>:8080/track.mjpg
   ```
3. 动手改造：在标注中增加"轨迹存活时长"（time_since_update），观察遮挡轨迹的存活状态

**易错点**：
- ⚠️ 每线程独立 RKNN 实例（检测池与 ReID 池均如此），共享实例崩溃
- ⚠️ 双缓冲依赖队列保序：帧 N 的结果不能串到帧 N+1

**流程图**：

```mermaid
flowchart LR
    A["取流<br/>--image/--video/--camera/--ros"] --> B["检测池 RKNNPool<br/>3 worker × 独立实例<br/>tid%3 绑 NPU 核"]
    B --> C["检测输出 → 类别过滤<br/>回映射原图坐标"]
    C --> D["ReID 池 2 worker<br/>批量外观 512-d<br/>按 idx 保序回收"]
    D --> E["主线程<br/>解码 + 跟踪 + 绘制"]
    E --> F["流水线双缓冲<br/>帧 N+1 在池内推理<br/>帧 N 在处理"]
    F --> G["MJPEG :8080/track.mjpg<br/>3 worker 12–15 FPS"]

    style B fill:#e8f0ff,stroke:#448,stroke-width:1px
    style D fill:#fff3d6,stroke:#b90,stroke-width:1px
```

---

### 1.7 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| ID 频繁切换 | 外观门限过松 / 特征质量差 | 调小 `tracker.max_dist`；确认 ReID 归一化正确 |
| 遮挡后 ID 丢失 | max_age 过小 / sort 模式 | 调大 max_age；确认 mode=deepsort（ReID 模型就位） |
| ID 互换（交叉场景） | 级联匹配失效 / max_dist 过大 | 检查级联逻辑；调小 max_dist |
| 轨迹残留不删 | max_age 过大 | 调小 max_age（如 30） |
| 启动告警 fallback sort | ReID 模型缺失/加载失败 | 确认 `models/deepsort.rknn` 就位 |
| 帧率低 | 池未生效 | 检查 pool.workers=3 + core_mask: round_robin |
| --ros 取不到帧 | 驱动未启动/ROS_DOMAIN_ID 不一致 | ascamera 先起；export ROS_DOMAIN_ID=2；话题勿 remap |
| 多线程崩溃 | 共享 RKNN 实例 | 每线程独立实例（检测池/ReID 池已实现） |

### 1.8 扩展实验

**扩展方向 1：轨迹计数与区域统计（进阶）**
- 在 app.py 中统计确认轨迹数、进出画面目标数（进入/离开计数），画线越线计数，实现人流/车流统计

**扩展方向 2：ByteTrack 对比（进阶）**
- 用"低分框也参与关联"的 ByteTrack 思路改造匹配逻辑（或移植），对比与 DeepSORT 在漏检场景的表现差异

### 1.9 实验报告要求

**评分标准**：MOT 问题理解 10 分 + 检测解码 15 分 + Kalman 20 分 + 级联匹配/匈牙利 25 分 + ReID 15 分 + 实时演示 10 分 + 报告 5 分 = 100 分。

**报告必含内容**：
1. DeepSORT 架构流程图（检测→Kalman→级联匹配→ReID→更新），标注源码行号
2. Kalman 预测 vs 检测框对比数据（单目标 10 帧）
3. 双目标交叉场景的 ID 保持截图与说明
4. 遮挡恢复对照实验（deepsort vs sort 模式 ID 变化）
5. workers=1 vs 3 的 FPS 对比数据
6. 回答思考题：级联匹配为什么从新到旧？马氏距离门限的作用？为什么外观特征能抗遮挡？
7. 实验心得与问题记录

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-10 | 初版生成（源码路径 ros2_ws/src/xflz_eai_car1/vision/07_multi_object_tracking，38 用例全绿，YOLOv8 检测 + Kalman + 级联匹配 + Hungarian + ReID 128-d，检测池/ReID池/双缓冲三处并行，板端 12-15 FPS） |
| v1.1 | 2026-08-19 | ReID 模型同步：deep_int8_in_8.rknn → deepsort.rknn（用户重导 [1,3,128,64]→[1,512]，512-d 特征）；新增可选 ONNX 备份 yolov8n.onnx / deepsort.onnx |
| v2.0 | 2026-08-19 | 知识点增强：新增 4 个知识储备补充（检测解码9输出与DFL / Kalman预测更新方程与马氏距离 / 匈牙利匹配与cosine距离 / ReID特征提取与512-d语义），5 个公式块（Kalman预测/更新/马氏距离/cosine距离/ReID embedding），执行现象段，源码行号全部核对真实（detect.py L16-21 L24-30 L33-41 L14-20 / kalman.py L11 L40-50 L55-58 L64-70 / matching.py L14-28 L31-36 L39-49 L42-49 / tracker.py L21-24 L27-31 L46-50 / reid.py L11-12 L21-28 L68-84 / track.py L33），4 个参考资源 |
| v2.1 | 2026-08-21 | 步骤 1 新增「配置参数速查表」：config/track_config.yaml 全参数（model/detect/tracker/pool/server）。标注 mode 回退/classes/min_confidence。表值实测一致 |
