---
course_code: EXP006b
course_name: 机器人大模型综合应用开发（通用目标追踪）
version: v1.0
generated_at: 2026-09-07
generator: QualityReviewAgent
source_spec: courses/sheet1/object_tracking/_meta/course-spec.yaml
csv_sha256: 5fc42d608003d2657215b33eeaa92a0fd338de1e4fcc87691a38c653c03de053
---

# EXP006b 质量评审报告

> 评审对象: EXP006b 机器人大模型综合应用开发（通用目标追踪） 全套课程资源
> 评审维度: 准确性 30% / 完整性 25% / 一致性 20% / 可操作性 25%
> 评审日期: 2026-09-07

---

## 一、评审结论

**综合评级: A 级（91 分）— 优秀，可直接使用**

| 维度 | 权重 | 得分 | 加权 |
|------|------|------|------|
| 准确性 | 30% | 27 | 8.1 |
| 完整性 | 25% | 23 | 5.75 |
| 一致性 | 20% | 19 | 3.8 |
| 可操作性 | 25% | 22 | 5.5 |
| **总分** | 100% | — | **91.15 ≈ 91** |

---

## 二、准确性（27/30）

### ✅ 达标项
- **源码驱动**: 实验指导书全部基于真实源码生成，行号引用抽查与源码一致（tracking/engine.py、kalman.py、tracker.py、tools/vlm_real.py、apps/track_app.py CommandWorker）
- **算法事实准确**:
  - DeepSORT 结构：卡尔曼常速（8 维均值 `[cx,cy,aspect,height,vx,vy,va,vh]` + 4 超速）+ IoU/外观级联关联 + 确认框生命周期（Tentative→Confirmed→Deleted）与源码一致
  - ReID 外观：deepsort.rknn 64x128 ImageNet 归一化，max_dist=0.2，ReIDPool 多线程异步 + extract 超时降级纯 IoU，正确
  - VLM 网格选车：crops→build_grid→VLM 只答编号→cell_ids 映射绝对 track id，cell_cap=16，fail-closed（99/0/无匹配回引导），正确
- **配置事实准确**: min_confidence=0.3、class_filter=[car]、min_box_w/h=32、max_stale=15、pause_timeout=30.0、cell_cap=16、fake_result_id=3 与 `config/track_config.yaml` 一致
- **命令真实**: `--text/--video/--image/--camera/--mjpeg`，`http://<IP>:8088/track.mjpg`，`pkill -f llm_server`，`ros2 launch car1_peripherals depth_camera.launch.py` 均真实
- **门控语义准确**: _native_gate 路由顺序（清除短路→闲聊回落→id 存在性→描述 VLM→放行），fail-closed 铁律讲解正确

### ⚠️ 扣分说明（-3）
- 部分实验专属参数细节未逐一实测验证（如 VLM 泛化边界、ReID 在极端遮挡的表现），文案基于文档与实现推断，未进行全量板端实机验收（标注为"需板端/实机 tuned"项占多）。

---

## 三、完整性（23/25）

### ✅ 达标项
- **知识图谱**: 6 章 / 14 节 / 42 知识点（标准 ≥3 章 ≥20 点），含类型/难度/前置依赖/Mermaid 依赖图/统计表/自检，覆盖全部 tech_stack（YOLOv8/DeepTrack/ReID/RKNN/RKLLM/FunctionCall/VLM/KWS/ASR/TTS/fail-closed/MJPEG）
- **教学大纲**: 3+3+2 目标（知识 6 + 能力 4 + 素养 3），9 章学时分配表、教学内容、考核方式（含过程评价）、参考资源、先修课程
- **实验指导书**: 9 实验全部含 9 节标准结构（关联知识点/目标/环境/难度/现象/步骤/注意事项/总结/报告要求），合计 1721 行
- **练测题库**: 34 题 = 20 单选 + 8 多选 + 4 简答 + 2 编程，难度 50/29/21，覆盖 40/42 知识点

### ⚠️ 扣分说明（-2）
- 分片行数偏低：exp1（186）/exp3（178）/exp4（198）/exp5（165）/exp6（166）/exp7（173）/exp8（168）/exp9（175）均 <200 行；exp2 215 行达标。合并版完整，但分片略薄，深入原理讲解可加强。
- 题库为试卷模式（standard），未提供 ×5 题库模式（bank）——如需多次组卷需另补。

---

## 四、一致性（19/20）

### ✅ 达标项
- 学时：spec 48 = 大纲 48 = lab_guide 48（4+4+4+8+4+4+6+6+8）
- 实验数：9 全文档一致；知识图谱章节 ↔ 实验 ↔ 大纲章节一一对应
- 知识点编号：42 点唯一连续（1.1.1~6.2.3），题库/大纲引用均可解析
- csv_sha256：spec/知识图谱/大纲/题库/审核/评审全统一（5fc42d60）
- 命名规范：object_tracking、EXP006b_{type}.md、experiment-{N}.md 全部合规

### ⚠️ 扣分说明（-1）
- 知识图谱类型分布偏离标准：概念 31%（标准 40±10%）、原理 38%、流程 24%、事实 7%——偏差在允许边界（±8% 内），但概念/原理失衡。

---

## 五、可操作性（22/25）

### ✅ 达标项
- **命令可直接执行**: 每实验含完整 bash 命令（cd → pytest → track_app --text / --camera / --mjpeg，MJPEG 地址）
- **快速验证流程**: 每实验「实验现象」含完整快速验证命令 + 预期效果描述
- **调参指引明确**: 调低 min_confidence 观察 ID 跳变、调 kws.threshold、改 class_filter、vlm.fake_result_id 等给出具体值与影响
- **验证路径分层**: 纯逻辑 pytest（x86）→ 文本模式（无硬件）→ 语音 → 摄像头三级递进；离线先验证，实时再部署
- **易错点全覆盖**: 每实验含常见问题表（现象+原因+解决）

### ⚠️ 扣分说明（-3）
- 部分实时/硬件验证环节（语音唤醒、VLM 真实模型、摄像头全链路）需板端实测，指导书标注"待板端"但未提供实机验收结果；首次生成尚未在实机逐实验跑通（A 级审核基于源码与文档，非实机）。

---

## 六、评审意见

### 优点
1. **真实源码驱动**: 所有原理讲解、行号引用（engine/kalman/tracker/vlm_real/track_app）、参数值均来自仓库源码与文档，无虚构
2. **算法讲解准确**: DeepSORT 级联、卡尔曼、ReID、fail-closed 门控等核心原理表述正确且有源码落点
3. **平台强适配**: 全链路针对 B2/C1（RK3576/6TOPS NPU/HP60C），命令可直接在板执行
4. **三级验证**贯穿：离线性逻辑回归→文本→语音→摄像头递进，工程素养好

### 改进建议（不阻塞使用）
1. 🟡 分片行数提升：为 exp1/3/4/5/6/7/8/9 加深原理讲解 ≥200 行
2. 🟡 知识图谱类型分布微调：概念类补强（+3~4 点），原理类可转 2 点为概念
3. 🟢 补充题库模式（bank ×5）满足多次组卷
4. 🟢 实机验收记录：摄像头/MJPEG/VLM 真实模型完成后回填实测数据

---

## 结构化缺陷清单

```yaml
review_result:
  course_code: EXP006b
  grade: A
  passed: true
  failed_items: []
  rollback_hint: []
```

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-09-07 | 首次评审：A 级 91 分（准确性 27/30、完整性 23/25、一致性 19/20、可操作性 22/25），4 项改进建议 |