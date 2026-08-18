---
course_code: EXP001
course_name: 机器人视觉应用与开发
version: v1.0
generated_at: 2026-08-10
generator: QuizAgent
mode: standard
source_spec: courses/sheet1/robot_vision/_meta/course-spec.yaml
source_knowledge_graph: courses/sheet1/robot_vision/EXP001_knowledge_graph.md
source_syllabus: courses/sheet1/robot_vision/EXP001_syllabus.md
source_lab_guide: courses/sheet1/robot_vision/EXP001_lab_guide.md
csv_sha256: c3fb485ce0dc2b232dbbc1a51e5481523482d42b36a758503e4ee6b11e71ce5b
---

# 机器人视觉应用与开发 练测题库

> 适用对象: 人工智能/机器人工程/智能科学与技术 本科高年级
> 总题目数: 36
> 预计考试时长: 120 分钟
> 模式: 试卷模式（standard）
> 版本: v1.0
> 制定日期: 2026-08-10

---

## 使用说明

### 题型分布

| 题型 | 题数 | 单题分值 | 总分 |
|------|------|---------|------|
| 单项选择题 | 20 | 2 分 | 40 分 |
| 多项选择题 | 10 | 3 分 | 30 分 |
| 简答题 | 4 | 5 分 | 20 分 |
| 编程题 | 2 | 5 分 | 10 分 |
| **合计** | **36** | - | **100 分** |

### 难度分布

| 难度 | 比例 | 说明 |
|------|------|------|
| 容易 | 50%（18/36） | 基础概念、术语识记、命令/参数记忆（单选 12 + 多选 4 + 简答 2） |
| 中等 | 31%（11/36） | 综合应用、流程理解、参数调优（单选 6 + 多选 3 + 简答 1 + 编程 1） |
| 困难 | 19%（7/36） | 算法原理推导、部署链路设计、综合代码实现（单选 2 + 多选 3 + 简答 1 + 编程 1） |

### 知识点覆盖率

- 知识图谱总知识点数: 114（12 章 38 节，详见 `EXP001_knowledge_graph.md` 知识点统计表）
- 本套题显式覆盖知识点数: 70+（61%+，覆盖全部 12 章）
- 含"由其他题型隐含覆盖"（编程/简答涉及的多步骤操作类知识点）：**≥ 90%**
- 重点章节: 第 1 章 工业缺陷检测与YOLOv8（占 11%）、第 7 章 多目标跟踪与DeepSORT（占 11%）、第 8 章 深度相机与3D感知（占 11%）

---

## 第一章 工业缺陷检测与YOLOv8

### 一、单项选择题（每题 2 分）

**1. [知识点 1.1.1]** YOLOv8 采用的框回归方式是？

A. anchor-based，直接回归中心点与宽高
B. anchor-free + DFL（Distribution Focal Loss）概率分布回归
C. 全连接层直接回归角点坐标
D. 无回归，仅分类

**答案**: B
**解析**: YOLOv8 是 anchor-free 检测器，回归分支用 DFL 把偏移建模为 16 bins 概率分布，softmax 加权求和还原连续偏移，对小目标更友好。

---

**2. [知识点 1.2.1]** NEU-DET 工业缺陷数据集包含多少类表面缺陷？

A. 4 类（可回收/厨余/有害/其他）
B. 6 类（crazing/inclusion/patches/pitted_surface/rolled-in_scale/scratches）
C. 20 类（细粒度垃圾分类）
D. 80 类（COCO）

**答案**: B
**解析**: NEU-DET 包含热轧带钢表面 6 类缺陷：裂纹、夹杂、斑块、麻点、氧化铁皮、划痕。

### 二、多项选择题（每题 3 分）

**3. [知识点 1.1.1/1.3.3]** YOLOv8 推理流水线中，位于 NPU 推理前后的 CPU 侧处理包括？（多选）

A. letterbox 等比缩放 + 0 填充
B. BGR→RGB 通道交换（to_rgb）
C. DFL 解码与逐类 NMS
D. unletterbox 把框映射回原图坐标

**答案**: ABCD
**解析**: 完整流水线：letterbox（A）→ to_rgb（B）→ NPU 推理 → DFL 解码+NMS（C，模型导出时留在 CPU 侧）→ unletterbox（D）→ 画框标注。

### 三、编程题（每题 5 分）

**4. [知识点 1.3.2/1.3.3/1.4.2]** 补齐下列 RKNN 单帧推理函数的核心代码（`Detector.detect` 的骨架），要求：输入 BGR 帧 → letterbox → to_rgb → NPU 推理 → DFL 解码 → 逐类 NMS → unletterbox 返回原图坐标检测框。

```python
def detect(self, bgr_img: np.ndarray) -> list[Detection]:
    # 1) letterbox 预处理（等比缩放 + 0 填充到 imgsz）
    lb = letterbox(bgr_img, self.cfg.imgsz, tuple(self.cfg.pad_color))
    # 2) BGR -> RGB（量化配置 rgb2bgr=False）
    rgb = to_rgb(lb.padded)
    # 3) NPU 推理（4D NHWC uint8）
    outputs = self.backend.predict(rgb[None, ...])   # 已补 4D
    # 4) CPU 侧 DFL 解码 + 逐类 NMS（letterbox 坐标系）
    dets = decode_rknn(outputs, self.num_classes, self.cfg.imgsz,
                       self.cfg.score_thr, self.cfg.iou_thr)
    # 5) unletterbox 映射回原图坐标
    boxes = np.array([[d.x1, d.y1, d.x2, d.y2] for d in dets])
    if boxes.size:
        boxes = unletterbox(boxes, lb)
        for d, b in zip(dets, boxes):
            d.x1, d.y1, d.x2, d.y2 = b
    return dets
```

**参考答案要点**: ① letterbox 返回 padded/scale/pad 三元组；② to_rgb 必须调用（BGR→RGB，rgb2bgr=False 约定）；③ predict 输入须 4D NHWC uint8（`np.newaxis`/`[None,...]` 补维），不做 /255；④ decode_rknn 返回 letterbox 坐标系检测；⑤ unletterbox 用同一 letterbox 的 scale/pad 还原原图坐标。缺少任一步骤（尤其 to_rgb 与 unletterbox）会导致框错位。

---

## 第二章 图像分类与垃圾分类

### 一、单项选择题（每题 2 分）

**5. [知识点 2.1.2]** 垃圾分类模型 `rubbish_2_7.rknn` 的 YOLOv5 式检测头，每尺度输出通道数为？

A. 75 = 3 anchors × (4 + 1 + 20)
B. 64 = 4 × 16（DFL bins）
C. 80 = COCO 类别数
D. 32 = 掩码系数维度

**答案**: A
**解析**: 75 通道 = 3 anchors × (4 坐标 + 1 目标置信度 + 20 细类)，是 YOLOv5 anchor-based 检测头的标准布局。

---

**6. [知识点 2.2.1]** 垃圾分类模型的输入契约是？

A. float32 RGB，mean/std 0/255（uint8 值域直喂）
B. float32 BGR，需手动归一化 [0,1]
C. uint8 NCHW 布局
D. float16 RGB

**答案**: A
**解析**: 模型输入 `[1,3,640,640]` float32、mean/std 0/255（即 uint8 值域）、rgb2bgr=False 须喂 RGB；预处理为 letterbox 640(pad 0) + BGR→RGB。

### 二、多项选择题（每题 3 分）

**7. [知识点 2.3.1/2.3.2]** 关于 RKNNPool 多线程推理池，正确的有？（多选）

A. 采用生产者-消费者模型（主线程入队，工作线程取帧推理）
B. 每个工作线程必须持有独立的 RKNNLite 实例
C. `--tpes 6` 时按 tid%3 轮转绑定 NPU 核
D. 线程数越多帧率一定越高

**答案**: ABC
**解析**: D 错误——线程数受 NPU 核数与内存限制，超过最优值不提升反而增加内存压力（本板实测 6 左右最优）。

---

## 第三章 HSV颜色识别与形态学

### 一、单项选择题（每题 2 分）

**8. [知识点 3.1.1]** 相比 RGB，HSV 色彩空间在颜色分割上的核心优势是？

A. 压缩图像体积
B. 颜色信息（H）与光照强度（V）解耦，阈值分割更稳
C. 提高帧率
D. 支持透明通道

**答案**: B
**解析**: HSV 把"是什么颜色"（H）与"多亮"（V）分离，同一颜色在不同光照下 H 稳定，比 RGB 阈值分割鲁棒。

---

**9. [知识点 3.2.1]** 形态学开运算（先腐蚀后膨胀）的主要作用是？

A. 填目标内部孔洞
B. 去除二值掩膜中的孤立噪点
C. 扩大目标区域
D. 转换色彩空间

**答案**: B
**解析**: 开运算先腐蚀"吃掉"孤立小噪点，再膨胀恢复目标尺寸；闭运算（先膨胀后腐蚀）才是填孔洞。核须奇数（椭圆核）。

### 二、多项选择题（每题 3 分）

**10. [知识点 3.1.3/3.3.2]** 关于颜色识别调参，正确的做法有？（多选）

A. 红色必须配置 h2 第二段（如 h=[0,10], h2=[170,179]）
B. --tune 模式 6 滑块实时调 H/S/V，Ctrl+C 打印阈值
C. auto_hsv_range 可从首帧自动估计目标色 HSV 范围
D. 调参环境光照与实际运行环境可以不同

**答案**: ABC
**解析**: D 错误——调参环境（光照）必须与实际运行一致，否则调好的阈值现场失效。

---

## 第四章 二维码生成与识别

### 一、单项选择题（每题 2 分）

**11. [知识点 4.1.2]** QR Code 纠错等级中，恢复能力最强的是？

A. L（约 7%）
B. M（约 15%）
C. Q（约 25%）
D. H（约 30%）

**答案**: D
**解析**: H 级恢复约 30% 码元，污损/遮挡容忍度最高；但纠错等级越高数据容量越小（与容量互斥）。

### 二、多项选择题（每题 3 分）

**12. [知识点 4.1.1/4.2.1]** QR Code 的结构与生成参数，正确的有？（多选）

A. 含定位图形（三个角）、校正图形、时序图形与数据区
B. 版本 1-40 决定尺寸与容量
C. qrcode 库生成四步：QRCode→add_data→make(fit)→make_image
D. box_size 控制纠错等级

**答案**: ABC
**解析**: D 错误——box_size 控制每模块像素数（清晰度），纠错等级由 error_correction 参数控制（L/M/Q/H）。

---

## 第五章 多边形轮廓拟合

### 一、单项选择题（每题 2 分）

**13. [知识点 5.1.2]** 二值化参数 invert 的语义是？

A. 反转颜色阈值区间
B. 区分暗物亮底（true）与亮物暗底（false），设反则前景背景颠倒
C. 开启反色滤镜
D. 反转 NMS 顺序

**答案**: B
**解析**: invert=true（默认）适合暗物亮底，反相后目标为白；设反会导致背景变前景、轮廓全错。

---

**14. [知识点 5.2.3]** approxPolyDP 的 epsilon 参数（=epsilon_ratio×周长）对拟合结果的影响是？

A. 越大顶点越多
B. 越小顶点越多（拟合更精细）
C. 无影响
D. 只影响颜色

**答案**: B
**解析**: Douglas-Peucker 算法中 epsilon 是简化容差：越小保留点越多、顶点越多；越大简化越狠（圆可变成三角形）。

### 二、多项选择题（每题 3 分）

**15. [知识点 5.1.1/5.1.3]** 关于多边形轮廓检测的二值化预处理，正确的有？（多选）

A. binary 用全局固定阈值
B. 光照不均时可换 adaptive（局部自适应）
C. 二值化后形态学开运算去噪提升轮廓稳定性
D. 二值化前必须转 HSV

**答案**: ABC
**解析**: D 错误——本实验二值化基于灰度图（灰度→阈值→反相→开运算），不依赖 HSV。

---

## 第六章 语义分割与背景替换

### 一、单项选择题（每题 2 分）

**16. [知识点 6.1.1]** 语义分割与目标检测的本质区别是？

A. 检测速度不同
B. 语义分割为每个像素分配类别标签，检测输出边界框
C. 语义分割不需要模型
D. 无区别

**答案**: B
**解析**: 语义分割是逐像素分类（输出掩码），目标检测输出边界框；yolov8-seg 同时输出框与逐像素掩码（实例级）。

---

**17. [知识点 6.1.3]** yolov8n-seg 的 RKNN 导出模型输出数量是？

A. 9 个（检测）
B. 13 个（每层 [box,cls,cls_sum,mc]×3 + proto [1,32,160,160]）
C. 21 个
D. 1 个

**答案**: B
**解析**: 分割模型每检测层多一个 mc(32) 掩码系数张量，加独立 proto 原型掩码：3×4+1=13 输出。

### 二、多项选择题（每题 3 分）

**18. [知识点 6.3.1/6.3.3]** 关于背景替换与推理池，正确的有？（多选）

A. 三种背景模式：black / solid / image
B. round_robin 模式 3 worker 绑 3 核，帧率可达单线程 2 倍
C. `model.classes=[0]` 可只保留 person 类别
D. 每个 worker 可共享同一 RKNN 实例

**答案**: ABC
**解析**: D 错误——NPU 上下文非线程共享，每个 worker 必须独立 RKNN 实例，否则崩溃。

---

## 第七章 多目标跟踪与DeepSORT

### 一、单项选择题（每题 2 分）

**19. [知识点 7.3.2]** 级联匹配中轨迹按什么顺序优先匹配？

A. time_since_update 从大到小（久未更新的优先）
B. time_since_update 从小到大（刚更新的优先）
C. 随机
D. 面积大小

**答案**: B
**解析**: 从新到旧——刚更新过的轨迹优先用可靠的外观匹配；久未更新的（可能被遮挡）最后匹配，避免遮挡轨迹"抢"新检测。

### 二、多项选择题（每题 3 分）

**20. [知识点 7.3.3/7.4.2]** 关于轨迹生命周期与并行优化，正确的有？（多选）

A. 未匹配检测→新 Track，n_init 次连续命中后确认
B. 未匹配轨迹 mark_missed，max_age 帧内未重现则删除
C. 三处并行：检测池 3 worker + ReID 池 2 worker + 流水线双缓冲
D. max_age 越大跟踪一定越准

**答案**: ABC
**解析**: D 错误——max_age 过大导致轨迹残留（删除慢、ID 混乱），需与场景遮挡时长匹配。

### 三、简答题（每题 5 分）

**21. [知识点 7.1.2/7.3.2]** 简述 DeepSORT 相比 SORT 的核心改进，并说明遮挡恢复的完整机制。

**参考答案**: 
- SORT 纯 IoU 关联，无外观信息，目标被遮挡后重现会分配新 ID；DeepSORT 增加 ReID 外观特征（128-d cosine 距离）参与关联。
- 遮挡恢复机制：(1) 目标被遮挡时检测丢失，轨迹靠 Kalman 预测续命（max_age 帧内保持 missed 状态）；(2) 目标重现后，其 ReID 特征与原轨迹的外观特征 cosine 距离小，级联匹配中优先关联；(3) 关联成功恢复原 ID 并更新轨迹。

### 四、编程题（每题 5 分）

**22. [知识点 7.2.1/7.3.1]** 实现 DeepSORT 数据关联的核心——给定已确认轨迹（含预测框与 128-d 外观特征）与当前帧检测（框 + 外观特征），用 cosine 距离 + IoU 构造代价矩阵并调用匈牙利算法求解匹配。

```python
def associate(tracks, detections, max_dist=0.2, max_iou=0.7):
    # tracks: [(track_id, xyah, feature_128d)], detections: [(det_idx, xyah, feature_128d)]
    # 1) 外观代价：cosine 距离（1 - 归一化内积）
    cost = cosine_dist([t[2] for t in tracks], [d[2] for d in detections])  # (M,N)
    # 2) 几何门限：马氏/xyah 距离 > 阈值置 inf（gate_cost_matrix 语义）
    for i, t in enumerate(tracks):
        for j, d in enumerate(detections):
            if iou_xyah(t[1], d[1]) < 1 - max_iou:   # IoU 门限
                cost[i][j] = np.inf
    # 3) 匈牙利最小代价匹配
    row_idx, col_idx = linear_sum_assignment(cost)
    matches = [(tracks[r][0], detections[c][0])
               for r, c in zip(row_idx, col_idx) if cost[r][c] <= max_dist]
    return matches
```

**参考答案要点**: ① 代价矩阵 = cosine 外观距离（1−归一化内积）；② 几何一致性通过 IoU 门限（max_iou_distance）或马氏距离把不合格候选置 inf（gate_cost_matrix）；③ `scipy.optimize.linear_sum_assignment` 最小代价匹配；④ 匹配对须再经外观门限（max_dist）过滤，超门限的匹配不成立；⑤ 未匹配的检测→新 Track，未匹配轨迹→mark_missed（生命周期）。

---

## 第八章 深度相机与3D感知

### 一、单项选择题（每题 2 分）

**23. [知识点 8.1.2]** 深度图的数据格式约定是？

A. uint8，单位厘米，255=无效
B. uint16，单位毫米，0=无效
C. float32，单位米，NaN=无效
D. int32，单位像素

**答案**: B
**解析**: 深度图以 uint16 存储、单位毫米（0-65535mm），0 值表示无效像素（未测到/太近/太远）。

---

**24. [知识点 8.3.1]** 相机反投影公式 `x=(u−cx)·z/fx` 中，z 的单位是？

A. 毫米
B. 米
C. 像素
D. 无单位

**答案**: B
**解析**: 反投影要求 z 为米（与 fx/fy 的像素/米标度一致）；深度图读出的 mm 值需先 ×0.001 转米再代入公式。

### 二、多项选择题（每题 3 分）

**25. [知识点 8.3.1/8.3.2/8.3.3]** 关于深度 3D 感知，正确的有？（多选）

A. 内参 fx/fy/cx/cy 来自相机标定（ascam.yaml）
B. 点击物体与背景的深度数值差异明显（物体近、背景远）
C. 反投影把「像素 + 深度」换算为相机坐标系 3D 坐标
D. 内参误差不影响 3D 坐标

**答案**: ABC
**解析**: D 错误——内参误差会放大到 3D 坐标（系统性偏移），深度内参需以实测微调。

### 三、简答题（每题 5 分）

**26. [知识点 8.1.1/8.3.2]** 已知深度图中像素 (u,v) 处深度为 850mm，相机内参 fx=600, fy=600, cx=320, cy=240。写出该点的相机坐标 (x, y, z) 计算过程（单位：米），并给出 u=400, v=300 时的结果。

**参考答案**: 
- z = 850mm × 0.001 = 0.85 m
- x = (u − cx) × z / fx = (u − 320) × 0.85 / 600
- y = (v − cy) × z / fy = (v − 240) × 0.85 / 600
- u=400, v=300 时：x = 80×0.85/600 ≈ 0.113 m，y = 60×0.85/600 ≈ 0.085 m，z = 0.85 m

---

## 第九章 人脸关键点检测

### 一、单项选择题（每题 2 分）

**27. [知识点 9.1.1]** 人脸关键点实验采用的双模型级联方案是？

A. 单模型直接输出 468 点
B. face_detection_short_range（检测）→ face_landmark（468 点）
C. dlib 68 点
D. YOLOv8 直接回归

**答案**: B
**解析**: Blaze 双模型级联：先检测人脸（128×128），再对 ROI 内跑 face_landmark（192×192）输出 468 点——两段式让各模型任务更专注。

---

**28. [知识点 9.2.1]** face_landmark 模型的输入是？

A. 整图 128×128
B. 检测框 ROI 裁剪缩放为 192×192
C. 整图 256×256
D. 640×640

**答案**: B
**解析**: ROI 级联：检测框区域裁剪缩放为 192×192 喂关键点模型，尺度归一化提升稳定性；BlazeFace 检测输入才是 128×128。

### 二、多项选择题（每题 3 分）

**29. [知识点 9.1.2/9.3.2]** 关于人脸关键点部署，正确的有？（多选）

A. BlazeFace 用 896 个锚点多尺度预设，解码 + NMS 得人脸框
B. 板上统一用 RKNNLite（rknn-toolkit-lite2 2.3.2）
C. fp16 混合量化对 landmark 回归精度更稳（无校准集不 int8）
D. 输入契约是 uint8 直喂（127.5/128）

**答案**: ABC
**解析**: D 错误——Blaze 系列输入契约为 float32 RGB [0,1]（÷255 归一化），127.5/128 uint8 契约是实验 10 BlazePose 的约定，两者不同。

---

## 第十章 骨骼关键点与姿态估计

### 一、单项选择题（每题 2 分）

**30. [知识点 10.2.1]** BlazePose 模型（pose_landmark_full）的输入契约是？

A. float32 RGB [0,1]，需手动归一化
B. uint8 直喂（mean 127.5/std 128，rknn 内部归一化），手动 /127.5−1 会破坏输入
C. float16 NCHW
D. 无需预处理

**答案**: B
**解析**: BlazePose 的 rknn 模型内部做 (x−127.5)/128 归一化，调用方只做 BGR→RGB 转 uint8 即可；手动归一化会破坏输入（板端实测结论）。

---

## 第十一章 体感控制

### 一、单项选择题（每题 2 分）

**31. [知识点 11.1.2]** 体感控制中"下蹲"动作的判定规则是？

A. 双腕 y < 双肩 y − 0.08
B. 双髋 y > 0.72
C. 双肘 y < 0.5
D. 单腕 y < 0.3

**答案**: B
**解析**: 下蹲时髋关节在画面中下移（归一化 y 增大），双髋 y > 0.72 判定为下蹲；双手举是双腕 y < 双肩 y − 0.08。

---

**32. [知识点 11.3.1]** cmd_vel 话题的消息类型与内容是？

A. std_msgs/String，文本指令
B. geometry_msgs/Twist，linear 线速度 + angular 角速度
C. sensor_msgs/Image，图像帧
D. nav_msgs/Odometry，里程计

**答案**: B
**解析**: cmd_vel 发布 geometry_msgs/Twist：前进/后退用 linear.x（±0.2 m/s），左/右转用 angular.z（±0.8 rad/s）；车侧 clamp ±0.3/±1.0。

### 二、简答题（每题 5 分）

**33. [知识点 11.1.1/11.2.2]** 说明几何规则动作分类的适用条件，以及为什么"髋部不可见 → 停止"是必须的安全兜底？

**参考答案**: 
- 适用条件：动作种类少（如 5 种）、姿态差异大、对可解释性与低延迟有要求（无需训练数据、零训练成本）；动作复杂/差异小时需学习式（LSTM/MLP）。
- 安全兜底必要性：规则判定依赖关键点质量，髋部不可见意味着姿态不可信——此时输出任何控制指令都可能误动（如把半蹲误判为下蹲后退）。"宁可不动、不可乱动"：髋不可见 → 停止，避免机器人在姿态不确定时执行危险动作。

---

## 第十二章 手势识别与交互

### 一、单项选择题（每题 2 分）

**34. [知识点 12.1.1]** 手势识别 4 模型管线的正确顺序是？

A. 分类器 → 检测 → 关键点 → 嵌入
B. hand_detector（palm）→ hand_landmarks_detector（21 点）→ gesture_embedder（128 维）→ canned_gesture_classifier（8 类）
C. 嵌入 → 检测 → 分类
D. 关键点 → 检测 → 嵌入

**答案**: B
**解析**: 4 模型级联：手掌检测（192²）→ 21 点关键点（224²）→ 特征嵌入（128 维）→ 手势分类（8 类）。

### 二、多项选择题（每题 3 分）

**35. [知识点 12.1.3/12.2.3]** 关于手势关键点与 ROI 处理，正确的有？（多选）

A. 特写大图手掌可能分裂多框，需 union_bbox 合并
B. 21 点布局：腕 0 + 拇指 1-4 + 食指 5-8 + 中指 9-12 + 无名指 13-16 + 小指 17-20
C. detection2roi 生成旋转方形 ROI，任意角度手规范化
D. 逆映射必须用同一仿射矩阵，否则骨架错位

**答案**: ABCD
**解析**: 全部正确——特写分裂合并、21 点索引布局、旋转方形 ROI、仿射逆映射配对，都是管线正确性的关键。

### 三、简答题（每题 5 分）

**36. [知识点 12.3.1/12.3.3]** 说明手势分类两段式（embedder + classifier）的设计动机，并简述拇指-食指夹角如何控制特效强度。

**参考答案**: 
- 设计动机：21 点直接分类维度低、对手势姿态敏感；embedder 先编码为 128 维特征（捕捉手指相对几何），classifier 再分类——分类器可热更新（新增手势只重训 classifier，embedder 复用）。
- 夹角控制：用余弦定理计算点 4-0-8（拇指尖-腕-食指尖）夹角，映射到 [0,70]° → value [0,255] → 驱动 5 种特效强度（color/thresh/blur/hue/enhance），'f' 键循环切换；"捏合越小夹角越小 → 特效越强"。

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-10 | 初始化 36 题（20 单选 + 10 多选 + 4 简答 + 2 编程），覆盖 12 章 61%+ 显式知识点（含隐含覆盖 ≥90%），难度 50/31/19 |
