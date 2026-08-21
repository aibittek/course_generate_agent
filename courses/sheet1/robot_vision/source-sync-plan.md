---
course_code: EXP001
course_name: 机器人视觉应用与开发
version: v1.0
generated_at: 2026-08-10
updated_at: 2026-08-19
purpose: 基于 ros2_ws/src/xflz_eai_car1/vision 源码实际修改，同步更新课程文档
---

# EXP001 源码变更 → 课程文档同步修改 Plan

> 依据：`ros2_ws/src/xflz_eai_car1/vision/`（源码真值）vs `courses/sheet1/robot_vision/`（当前文档）
> 原则：文档跟随源码实际（models/config/README 均为源码侧证据；README 与 models 冲突时以 models+config 为准）

---

## 一、差异清单（源码侧证据）

### 🔴 D1. exp2 垃圾分类模型名变更
- **证据**: `02_garbage_classification/config/garbage_config.yaml` L8 `model.path: ../models/garbage_yolov5_20cls.rknn`；`models/` 目录 = `garbage_yolov5_20cls.rknn`
- **现状**: README L3/L57 仍写 `rubbish_2_7.rknn`（README 未同步，以 config/models 为准）
- **影响文档**: lab_guide experiment-2、知识图谱 2.1.1/2.1.2、大纲第2章、题库题5、progress

### 🔴 D2. exp7 DeepSORT ReID 模型重大变更
- **证据**: `07_multi_object_tracking/config/track_config.yaml` L4-6：
  - `det_rknn: models/yolov8n.rknn`（不变）
  - `det_onnx: models/yolov8n_coco.onnx`（新增，可选）
  - `reid_rknn: models/deepsort.rknn`（注释：**用户重导 2026-08-05，[1,3,128,64]->[1,512]**）
- **现状**: README L7 仍写 `models/deep_int8_in_8.rknn`（128-d）；models/ 目录 = `deepsort.rknn` + `deepsort.onnx` + `yolov8n.rknn` + `yolov8n.onnx`
- **变更实质**: ReID 外观特征 **128-d → 512-d**；模型名 `deep_int8_in_8.rknn` → `deepsort.rknn`；新增 onnx 备用
- **影响文档**: lab_guide experiment-7（环境表/步骤5 ReID/易错点/常见问题）、知识图谱 7.4.1（"128-d 特征"→512-d）、大纲第7章、题库题33/38(参考)、progress

### 🟡 D3. exp9 人脸关键点用例数与模块拆分
- **证据**: `09_face_landmarks/README.md` L34 `tests/ ← 109 用例`（文档写 101）；新增 `blaze.py`（L17 AnchorOptions/L70 generate_anchors/L117 decode_boxes/L132 decode_keypoints），`landmark.py` L18 `from .blaze import ...`（检测/锚解码从 landmark.py 拆出）
- **变更实质**: 用例 101→109；锚解码/NMS/ROI 逻辑移至 `blaze.py` 模块
- **影响文档**: lab_guide experiment-9（环境表用例数/步骤1-3 模块描述/易错点）、知识图谱 9.1.x、大纲第9章、progress

### 🟡 D4. exp11 体感控制 actions.py 重构
- **证据**: `11_pose_control/.../actions.py` 全文重构：
  - 旧：5 个独立判定函数（squat/both_up/left_up/right_up/stop）
  - 新：`@dataclass Action(name,label)` + 常量（STOP/FORWARD/BACKWARD/TURN_LEFT/TURN_RIGHT）+ `classify_action(landmarks_px, h, w) -> Action`
  - 输入契约变化：**像素坐标 33×4 + 帧尺寸 (h,w)，内部 `_norm()` 归一化**（旧为归一化坐标直接判定）
  - 规则不变：SQUAT_HIP_Y=0.72、HAND_UP_DELTA=0.08、MIN_VIS=0.5、优先级 squat>both_up>left/right、髋不可见→STOP
- **影响文档**: lab_guide experiment-11（步骤1 模块描述/步骤3-4 函数引用）、知识图谱 11.1.2/11.1.3（"归一化坐标判定"→"内部归一化，输入像素坐标"）、大纲第11章、题库题31

### 🟢 D5. exp12 手势控制新增 pose.py（未接线）
- **证据**: `12_hand_control/.../pose.py`（BlazePose 复用模块：POSE_CONNECTIONS/resize_pad/decode_pose/prepare，INPUT_SIZE=256），**未被 engine.py/camera_demo.py 等引用**（grep 无 import）
- **判断**: 预留/遗留模块，文档可补充一句说明或忽略（不阻塞）

### 🟢 D6. exp1 FPS 表述核实
- **证据**: `01_industrial_defect_detection/README.md` L70 仅"板上 fps ≥ 15 FPS（NPU）"验收线，无 13 实测值；文档"实测约 13 FPS"源自 `course_spec_robot_vision.csv` notes（`板端验证通过13fps`）
- **判断**: 保留 13 FPS（CSV notes 证据），文档已标注"≥15 验收（实测约 13）"，无需修改

---

## 二、修改清单（按文档）

### M1. `_parts/experiment-2.md` + `EXP001_lab_guide.md` 实验2 章节
- [ ] 全文替换模型名 `rubbish_2_7.rknn` → `garbage_yolov5_20cls.rknn`（标题源码核实块、1.1 知识点、1.3 环境表、步骤1、步骤5、常见问题）
- [ ] 环境表模型行更新

### M2. `_parts/experiment-7.md` + `EXP001_lab_guide.md` 实验7 章节
- [ ] 标题源码核实块：模型清单更新（`deepsort.rknn` + `yolov8n.rknn` + `yolov8n.onnx`）
- [ ] 1.1 关联知识点：7.4.1 ReID "128-d" → "512-d（用户重导，[1,3,128,64]→[1,512]）"
- [ ] 1.3 环境表：模型行 `deep_int8_in_8.rknn` → `deepsort.rknn`；新增 det_onnx 说明
- [ ] 步骤5（ReID）："128-d 特征" → "512-d 特征"；模型名更新
- [ ] 步骤1/7、易错点、常见问题：ReID 模型名与维度引用更新

### M3. `_parts/experiment-9.md` + `EXP001_lab_guide.md` 实验9 章节
- [ ] 标题源码核实块：用例 101 → 109
- [ ] 1.1 知识点、1.3 环境表：用例数更新
- [ ] 步骤1/3：新增 `blaze.py` 模块说明（锚解码/NMS/ROI 拆分，landmark.py 引用）
- [ ] 易错点/常见问题：如引用 landmark.py 锚解码位置，更新为 blaze.py

### M4. `_parts/experiment-11.md` + `EXP001_lab_guide.md` 实验11 章节
- [ ] 步骤1：actions.py 描述更新（Action 类 + classify_action(landmarks_px, h, w)，5 个常量）
- [ ] 步骤3/4：判定函数引用更新（classify_action 内部 _norm；规则/阈值/优先级不变）
- [ ] 1.1 知识点、易错点：输入契约说明（像素坐标+帧尺寸，内部归一化）

### M5. `_parts/experiment-12.md` + `EXP001_lab_guide.md` 实验12 章节
- [ ] 模块清单补充 `pose.py`（BlazePose 复用，预留）——可选，低优先级

### M6. `EXP001_knowledge_graph.md`
- [ ] 2.1.1/2.1.2：模型名 `rubbish_2_7.rknn` → `garbage_yolov5_20cls.rknn`（若描述中含模型名）
- [ ] 7.4.1："128-d 特征" → "512-d 特征（deepsort.rknn）"
- [ ] 9.1.2/9.2.x：如描述含模块引用，补 blaze.py
- [ ] 11.1.3："规则用归一化坐标判定" → "classify_action 内部归一化（输入像素坐标）"
- [ ] 更新日志追加 v1.1 条目

### M7. `EXP001_syllabus.md`
- [ ] 第2章教学内容：模型名更新
- [ ] 第7章教学内容：ReID 512-d、deepsort.rknn
- [ ] 第9章：用例 109
- [ ] 第11章：actions.py 描述
- [ ] 更新日志追加

### M8. `EXP001_quiz.md`
- [ ] 题5（exp2 模型 75 通道）：如含模型名则更新
- [ ] 题33/38（exp7 ReID）："128-d" → "512-d"
- [ ] 题31（exp11 下蹲判定）：规则不变可保留，如含函数引用则更新
- [ ] 更新日志追加

### M9. `generation-progress.md` / `content-audit-report.md`
- [ ] 用例数：exp9 101→109
- [ ] 模型清单：exp2/exp7 更新
- [ ] 更新日志追加

---

## 三、派发策略（task）

| Task | 负责文件 | 差异 |
|------|---------|------|
| T1 | _parts/experiment-2.md、experiment-7.md | D1、D2 |
| T2 | _parts/experiment-9.md、experiment-11.md、experiment-12.md | D3、D4、D5 |
| T3 | EXP001_knowledge_graph.md、EXP001_syllabus.md | D1-D4 知识点/大纲 |
| T4 | EXP001_quiz.md、generation-progress.md、content-audit-report.md | D1-D4 题目/数据 |

- 合并版 `EXP001_lab_guide.md` 由主流程在 _parts 修改后重新合并（或各 task 同步修改对应章节——采用"先改 _parts，后重合并"策略，lab_guide 由主流程最后用脚本重新拼接）
- 所有修改不 commit（用户确认后再提交）

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.1 | 2026-08-19 | 源码同步 plan：D1 模型名 / D2 ReID 512-d / D3 用例与 blaze.py / D4 actions 重构 / D5 pose.py / D6 FPS 核实 |
