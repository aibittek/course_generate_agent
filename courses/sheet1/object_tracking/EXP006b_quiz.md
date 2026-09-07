---
course_code: EXP006b
course_name: 机器人大模型综合应用开发（通用目标追踪）
version: v1.0
generated_at: 2026-09-07
generator: QuizAgent
mode: standard
source_spec: courses/sheet1/object_tracking/_meta/course-spec.yaml
source_knowledge_graph: courses/sheet1/object_tracking/EXP006b_knowledge_graph.md
source_syllabus: courses/sheet1/object_tracking/EXP006b_syllabus.md
source_lab_guide: courses/sheet1/object_tracking/EXP006b_lab_guide.md
csv_sha256: 5fc42d608003d2657215b33eeaa92a0fd338de1e4fcc87691a38c653c03de053
---

# 机器人大模型综合应用开发（通用目标追踪）练测题库

> 适用对象: 本科高年级
> 总题目数: 34
> 预计考试时长: 120 分钟
> 模式: 试卷模式（standard）
> 版本: v1.0
> 制定日期: 2026-09-07

---

## 使用说明

### 题型分布

| 题型 | 题数 | 单题分值 | 总分 |
|------|------|---------|------|
| 单项选择题 | 20 | 2 分 | 40 分 |
| 多项选择题 | 8 | 4 分 | 32 分 |
| 简答题 | 4 | 5 分 | 20 分 |
| 编程题 | 2 | 4 分 | 8 分 |
| **合计** | **34** | - | **100 分** |

### 难度分布

| 难度 | 题数 | 比例 | 说明 |
|------|------|------|------|
| 容易 | 17 | 50% | 基础概念、参数识记、术语理解 |
| 中等 | 10 | 29% | 流程应用、机制理解、参数调优 |
| 困难 | 7 | 21% | 综合设计、跨节点编排、门控安全分析 |

### 知识点覆盖率

- 知识图谱总知识点数: 42（6 章 14 节，编号 1.1.1 ~ 6.2.3，详见 `EXP006b_knowledge_graph.md`）
- 本套题显式覆盖知识点数: 40（95%）
- 涉及源码事实（参数值、接口名、命令）均与 `config/track_config.yaml` 及实验指导书一致：min_box_w/h=32、max_stale=15、min_confidence=0.3、class_filter=[car]、pause_timeout=30.0、cell_cap=16、fake_result_id=3、`http://<IP>:8088/track.mjpg` 等

### 章节-知识点-题目覆盖一览

| 章节 | 知识点 | 对应题号 |
|------|--------|----------|
| 第1章 项目需求与系统架构 | 1.1.1 / 1.1.2 / 1.1.3 / 1.2.1 / 1.2.2 / 1.2.3 / 1.3.1 / 1.3.2 / 1.3.3 | 单选 1-4、多选 1 |
| 第2章 配置与调试体系 | 2.1.1 / 2.1.2 / 2.1.3 / 2.2.1 / 2.2.2 / 2.2.3 | 单选 5-7、多选 2 |
| 第3章 多目标追踪底座 | 3.1.1 / 3.1.2 / 3.1.3 / 3.2.1 / 3.2.2 / 3.2.3 / 3.3.1 / 3.3.2 / 3.3.3 | 单选 8-10、多选 3-4 |
| 第4章 LLM指令与门控 | 4.1.1 / 4.1.2 / 4.1.3 / 4.2.1 / 4.2.2 / 4.2.3 / 4.3.1 / 4.3.2 / 4.3.3 | 单选 11-13、多选 5-6 |
| 第5章 语音交互 | 5.1.1 / 5.1.2 / 5.1.3 | 单选 14-16、多选 7 |
| 第6章 事件日志与故障降级 | 6.1.1 / 6.1.2 / 6.1.3 / 6.2.1 / 6.2.2 / 6.2.3 | 单选 17-20、多选 8 |
| 简答题 | 1.3.1 / 4.3.2 / 5.1.3 / 6.2.3 | 简答 1-4 |
| 编程题 | 2.1.3 / 4.3.1 / 5.1.2 / 6.2.1 | 编程 1-2 |

---

## 第 1 章 项目需求与系统架构

### 一、单项选择题（每题 2 分）

**1. [知识点 1.1.1]** 通用目标追踪 R1-R13 需求中，R3 多目标追踪的算法结构是（　）。R3 实现文件在哪个模块？

A. 光流法跟踪
B. DeepSORT（卡尔曼预测 + IoU/外观级联关联 + 确认框），`tracking/tracker.py` 维护稳定 track id
C. 模板匹配 + 面积阈值
D. 粒子滤波

**答案**: B
**解析**: R3 明确使用 DeepSORT 结构（卡尔曼预测 + IoU/外观关联 + 确认框）由 `tracking/tracker.py` 生成维护稳定 track id。

**2. [知识点 1.1.2]** 检测→追踪ID→LLM指令锁定→描述选车→清除→日志的完整流程中，VLM 描述选车（R7）在什么条件下介入？

A. 任何「追踪」指令都先走 VLM
B. 用户给出目标描述且无 id（如"追踪红色皮卡"）时；有 id 的按 id 直锁（存在性优先）
C. 有 id 的同时也先 VLM
D. 只有清除后 VLM

**答案**: B
**解析**: `_native_gate` 顺序：存在 id 直接锁定（绝不 VLM 猜车带 id）；只有在无 id 且带描述（desc_words/color_words）时才 VLM，fall-closed。

**3. [知识点 1.1.3]** R1 多源输入统一（视频/静态图/摄像头）的实现方式是？
A. 每种输入写独立业务逻辑
B. config 或 CLI 切换 `source.mode`，业务代码零改动（`common/source.py` + `track_app --video/--image/--camera`）
C. 仅支持 video
D. 硬编码摄像头

**答案**: B
**解析**: R1 由 `common/source.py` 的 FrameSource + CLI 切换 source.mode 实现，业务代码零改动。

**4. [知识点 1.2.1]** 七层模块架构依赖方向正确的是（　）
A. tools → tracking → apps（servits）
B. `common ← vision/tracking ← tools ← apps`，且 speech/llm 独立
C. apps → tracking → tools
D. speech/llm 依赖 tracking

**答案**: B
**解析**: 依赖单向 `common ← (vision/tracking) ← tools ← apps`，speech/llm 独立（复用 elderly，接口对接在 apps 装配层）。

---

## 第 2 章 配置与调试体系

### 一、单项选择题（续）

**5. [知识点 2.1.1]** track_config.yaml 中 `detect.class_filter` 实机 tuned 值是（　）
A. person
B. [car]（只跟踪车，避免跨类外观混淆降 ID 稳定）
C. 全部 80 类
D. [truck]

**答案**: B
**解析**: 实机 `class_filter=[car]` 只留车防跨类外观混淆；COCO 80 类通用，改需重测。

**6. [知识点 2.1.2]** config_schema（`config/config_schema.py`）的主要作用是（　）
A. 性能优化
B. 强制 REQUIRED 键校验与类型检查，拦截键名拼写错误
C. 画图
D. 压缩配置

**答案**: B
**解析**: `config_schema.py` 的 REQUIRED 校验兜住键拼写错误，是配置合法性硬约束。

**7. [知识点 2.1.3]** CLI 传参与配置覆盖优先级是（　）
A. 文件 > CLI
B. CLI 显式参数 > yaml 文件
C. 默认 > CLI
D. 云配置 > CLI

**答案**: B
**解析**: `_merge_args` 只覆盖 CLI 显式给的键，未给的保留文件值；`--camera` 只改 mode 不重置 video_path。

---

## 第 3 章 多目标追踪底座

**8. [知识点 3.1.1]** DeepSORT 「级联关联」的核心是（　）
A. 随机分配
B. 按 `time_since_update` 排序，优先给最近更新的 track，再 IoU/外观匹配
C. 全连接

**答案**: B
**解析**: 级联匹配先按最近命中时间排序，避免长期遮挡 track 抢占新目标匹配；`tracking/tracker.py`。

**9. [知识点 3.1.2]** 卡尔曼常速模型的 8 维状态向量是（　）
A. [x, y, w, h]
B. [cx, cy, aspect, height, vx, vy, va, vh]
C. [cx]、[cy]
D. 4 维位置+角度

**答案**: B
**解析**: `kalman.py initiate` 均值 `np.r_[measurement, zeros(4)]`，8 维含位置(cx,cy,aspect,height)与速度(vx,vy,va,vh)。

**10. [知识点 3.3.1]** class_filter=[car] 的用途是（　）
A. 只输出轿车
B. 过滤 YOLO 输出保留车类，避免跨类外观混淆降低 ID 稳定
C. 忽略全检测

**答案**: B
**解析**: `class_filter` 在 detect 段过滤类别；只留 car 防 ReID 跨类混淆；COCO 广义目标 class_filter 可任意指定。

---

## 第 4 章 LLM 指令与门控

**11. [知识点 4.1.1]** LLM FunctionCall 工具注册集合（NATIVE_TOOLS 与 registry）是（　）
A. 仅 track_ids
B. track_ids / clear_track / track_vlm
C. track_ids / clear_track / save_snapshot
D. 仅 clear_track

**答案**: C
**解析**: `NATIVE_TOOLS`（track_app）对齐 registry 含 track_ids / clear_track / save_snapshot。

**12. [知识点 4.2.2]** clear_words 命中后 CommandWorker 执行（R9）（　）
A. 只解锁当前 id
B. 强制 clear_track，解除全部锁定，忽略模型 tool 输出
C. 回引导
D. 重置模型

**答案**: B
**解析**: 清除/解除/取消/停/不追/恢复全/不跟 → 强制 `clear_track` 并播「好的，已解除全部锁定」，忽略模型 tool，绝不解错。

**13. [知识点 4.3.2]** VLM fail-closed 描述选车「确定不了锁谁」（返 99/无匹配）的行为是（　）
A. 锁第一个候选
B. 回引导语不锁定，绝不 submit 空/错误 id 清锁
C. 随机锁
D. 清空所有锁定

**答案**: B
**解析**: 不确定(99/0/无匹配) → `_vlm_none` 回引导不锁，绝不 submit 空/错 id，防误锁（R8）。

---

## 第 5 章 语音交互

**14. [知识点 5.1.1]** 录音线程在什么条件下启动（XFM 时序）（　）
A. 系统启动即常驻上送
B. 硬件唤醒（XFM 串口事件 notify_wake）后启动（plughw:4,0）
C. 永不启动
D. 按需手动

**答案**: B
**解析**: 唤醒前录音线程待命（监听态不持续上送），XFM 唤醒事件 → 录音线程启动（ALSA plughw:4,0）。

**15. [知识点 5.1.2]** 流式 ASR（zipformer_onnx）增量解码的产物是（　）
A. 一次性整句
B. 流式 partial → 端点检测（如 4.5s 静音）→ final 整句
C. 只返回数字
D. 无中间态

**答案**: B
**解析**: `speech/asr.py` 实时产出 partial，端点规则触发后产生 final；`--text` 与音频同一状态机。

**16. [知识点 5.1.3]** 流式 TTS「打断丢弃」机制是（　）
A. 直接断电
B. 新唤醒/新指令在 SPEAKING 中 → epoch+1 → LLM worker 完成发现 epoch 变化即丢弃旧回复
C. 全部静音
D. 播完才处理新指令

**答案**: B
**解析**: 打断丢弃用 epoch 计数：发言人后迟到旧回复被丢弃，避免过期播报。

---

## 第 6 章 事件日志与故障降级

**17. [知识点 6.1.1]** events.jsonl 事件 `lost` 表示（　）
A. 系统重启
B. follow 目标从 confirmed 消失 `{"ids":[...]}` → TTS「idX 已消失」
C. 命令入队
D. 相机异常

**答案**: B
**解析**: `lost` 在锁定目标消失时写 ids，TTS 播报；command 是命令入队、unlock_all 是全解锁、camera_stall 相机断流。

**18. [知识点 6.1.2]** fail-closed 降级原则的核心（　）
A. 尽量猜锁
B. 任何「不确定锁谁」分支（submit_effect）不入队，只回引导/兜底，不崩线程
C. 关闭整个系统
D. 跳过门控

**答案**: B
**解析**: fail-closed：id 不对齐/VLM 无果/工具解析失败都只引导不产副作用，主循环不崩，是可恢复一致性。

**19. [知识点 6.2.1]** 三模式入口命令（track_app）是（　）
A. `--mode camera/image/video`
B. `--video / --image / --camera`
C. `--text` 仅
D. `--input`

**答案**: B
**解析**: track_app `_build_args` 提供 --video/--image/--camera 三源；--text 是文本调试开关。

**20. [知识点 6.2.2]** MJPEG 实时推流地址是（　）
A. `http://<IP>:8080/track.mjpg`
B. `http://<IP>:8088/track.mjpg`
C. `http://<IP>:8088/fall.mjpg`
D. `ws://<IP>:8088`

**答案**: B
**解析**: `server.port=8088` + `stream_name=track.mjpg` → `http://<IP>:8088/track.mjpg`。

---

## 二、多项选择题（每题 4 分）

**1. [1.2.3, 1.3.1]** CommandWorker 独立线程不卡帧的设计包含（　）
A. 有界队列 maxsize=8，put_nowait 满丢新命令不阻塞
B. LLM 推理主循环原位执行
C. submit_effect 入队回填主循环，registry.call 消费改 session
D. 指令处理期 engine.pending 暂停读帧，pause_timeout 看门狗

**答案**: ACD  （B 错误：LLM 在独立线程）

**2. [2.2.1, 2.2.3]** 文本—语音—摄像头三级开发模式的意义/容错（　）
A. --text 与音频同一状态机，逻辑先离线验证
B. ReID 失败降级纯 IoU
C. TTS 失败降级文本输出
D. 必须全硬件才能启动

**答案**: ABC  （D 错：文本模式无硬件可跑）

**3. [3.2.1, 3.2.3]** ReID 外观与 ID 稳定性关系（　）
A. deepsort.rknn 提取 64x128 ImageNet 特征消除单帧漏检换 ID
B. min_confidence 过低引入低置信噪声 → ID 跳变
C. class_filter=[car] 避免跨类外观混淆
D. ReID 与追踪完全无关

**答案**: ABC  （D 错误）

**4. [3.1.3, 3.3.3]** min_box/max_stale 剔除与遮挡恢复（　）
A. min_box_w/h=32 以下视为噪点不跟踪
B. max_stale=15 连续未命中剔除只剩预测框目标
C. 遮挡后 ReID 保持同 ID（unlock_on_loss 全丢恢复全显示）
D. ReID 与剔除无关

**答案**: ABC  （D 错误）

**5. [4.1.2, 4.1.3]** LLM 指令双解析路径与规则兜底（　）
A. 原生 rkllm 原生 FunctionCall（native_client/native_parser）
B. 非 native 结构化 JSON + tool_dispatch.dispatch
C. parse_instruction 正则规则兜底（无 LLM 也能追踪/清除）
D. 必须 LLM 才能动作

**答案**: ABC  （D 错误：rules 兜底生效）

**6. [4.3.1, 4.3.3]** VLM 网格选车机制（　）
A. crops 按 id 升序排成标准化 grid
B. VLM 只答编号，cell_ids[k-1] 映射绝对 track id
C. cell_cap=16 候选上限超则不锁
D. VLM 直接返回索引当 id

**答案**: ABC  （D 错误：VLM 返回编号映射，非索引直接当 id）

**7. [5.1.x]** 语音链路正确行为（　）
A. 唤醒后录音线程启动，唤醒前不持续上送
B. 播报互斥 playback_event 防回声入 ASR
C. 流式TTS 按句 + 打断丢弃 epoch
D. greedy 解码支持热词

**答案**: ABC  （D 错误：greedy 不支持热词，需 beam_search）

**8. [6.x]** 事件日志与故障降级正确（　）
A. lost/unlock_all/command/camera_stall/pause_timeout 均写 events.jsonl
B. 相机断流 30 次 → camera_stall + 暂停重试
C. aplay 被杀 → 播放线程重启或降级文本
D. LLM 断网时追踪/清除仍可（rules 兜底）

**答案**: ABCD（全对）

---

## 三、简答题（每题 5 分）

**1. [1.3.1]** 简述 CommandWorker 独立线程 + submit_effect 如何实现「LLM 慢不卡帧、不改帧率」，以及 pending 暂停 + pause_timeout 看门狗的作用。
参考答案: CommandWorker 是独立 daemon 线程，经有界队列（maxsize=8）消费用户指令，在独立线程调 LLM 做工具解析与门控，不经帧；副作用经 engine.submit_effect(ids,text) 入队回填主循环，主循环消费改 session，故 LLM 慢不阻塞读帧。处理指令时 engine.pending.set() 让主循环暂停读帧（停最后标注帧），pause_timeout（默认 30s）看门狗在 LLM 挂死时强制解暂停防冻结，保证帧率稳定。

**2. [4.3.2]** 通用目标追踪中描述选车 VLM 的 fail-closed 是什么？至少举两个基于 fail-closed 的节点。
参考答案: fail-closed 指「无法确定锁哪个目标」的分支都不产副作用，只回引导。两个节点：① `_native_gate` 中原文 id 集与模型 `args[ids]` 数值不对齐（如模型对「清除」误吐 track_ids、或「追踪一百号」解析 {100} 而场景 {113}）→ 回「未找到该 ID 目标」，绝不 VLM 猜车；② `_vlm_none`（VLM 不可用/返回 99/无匹配）→ 回引导，不锁，绝不 submit 空/错 id 清锁。二者共同保证不误导、不误锁。

**3. [5.1.3]** 流式 TTS「按句播报 + 打断丢弃」如何避免播报被 ASR 当回声 & 旧回复迟到？
参考答案: 播放期间用 playback_event 互斥，播报时段内不开 ASR 窗口（防 ASR 把播报内容识别进用户话）；LLM 流式输出按句实时合成并播放（首句即出声）。触发打断/新唤醒时 epoch+1，LLM worker 完成后发现 epoch 变化即丢弃旧回复，避免打断后迟到的过期播报。

**4. [6.2.3]** 简述从 exp01 到 exp09 全功能验证中「fail-closed 降级 + 事件日志完整性」如何共同保障系统不致误导误锁并可持续运行。
参考答案: 事件日志（lost/unlock_all/command/camera_stall/pause_timeout）与 fail-closed 互为表里：任何一时锁不定的分支不产副作用（不误导）、蓝关后事件准确落 events.jsonl 供事后追责；故障（断网/相机云/aplay/无 VLM）经降级不崩线程、不误锁。全链路（唤醒→追踪→指令→选车→清除→日志）闭环验证 + 事件完整性确认 + 资源清理（pkill），保证系统长期可控可运维。

---

## 四、编程题（每题 4 分）

**编程1. [6.2.1 & 4.3.1]** 补全以下伪代码：用 track_app 三模式之一（--video / --camera）做描述选车，并写出 VLM 网格构图→绝对 id 锁定 的关键步骤（含 cell_cap 上限）。
**参考答案**: 
① 候选 = scene_confirmed，每个 track 用 to_xyah() 取框并扩散 ±8px 裁帧，记录 (crops, crop_ids)；
② `build_grid` 按 id 比例排成标准化 grid + cell_ids（行优先对应格），候选上限 cell_cap=16 超则不锁；
③ `grid_select_prompt` 把「编号 i+1={cell_ids[i]}」布局表给 VLM，VLM 只答编号数字；
④ `_parse_tile` 1..n 返回 int（0/99→None），`select_crops` 用 cell_ids[k-1] 映回绝对 track id 并锁定；
⑤ 启动：视频 `python3 apps/track_app.py --video f.mp4 --text`；摄像头 `python3 apps/track_app.py --camera --mjpeg`。

**编程2（[3.2.3 & 5.1.2]）** 给定目标 id3 场景，写出「唤醒 → 说追踪 id3 → 遮挡丢失 → ReID 恢复 → 清除」并发日志，并简要故障排查思路。
**参考答案**: ① `printf '小飞小飞\n追踪 id3\n' | python3 apps/track_app.py --video test.mp4 --text`：首行唤醒 → 进入 DIALOG → `[cmd] track_ids {3}` → 锁 id3 → "好的，只追踪 id3"；② 遮挡 → use_reid=true 外观维持同 ID；持续消失 → lost 事件（TTS "id3 已消失"）→ unlock_on_loss 恢复全显示；③ `清除` → `[cmd] 清除语义指令 → clear_track` → 解锁；④ 排查：看 `[cmd]` 逐分支日志、events.jsonl 的 lost/unlock_all、调 min_confidence 或确认 ReID 未降级纯 IoU（若 use_reid 失效外观降级）。

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-09-07 | 初始版本，基于 EXP006b 知识图谱生成 34 题（单选 20 + 多选 8 + 简答 4 + 编程 2），知识点覆盖率 40/42，难度容易50%/中等29%/困难21% |