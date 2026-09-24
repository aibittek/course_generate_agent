## 实验3：机器人离线大模型语音交互（8h）

> ✅ **源码已核实** 本实验对应 `interaction/car1_speech`（离线唤醒/识别/合成）与 `interaction/car1_llm`（离线大模型意图识别）两功能包。语音链路完全离线：sherpa-onnx 的 KWS（唤醒词）+ ASR（识别）+ 本地 TTS（合成），加上 RKLLM 内嵌跑 Qwen 大模型做意图分类，全程不依赖公网。

### 3.1 关联知识点

本实验对应"智能工厂综合项目"第 3 章"离线大模型语音交互"，覆盖知识点：

- 3.1.1 离线语音链路架构 > 概念 > 唤醒→识别→意图→回复 的模块化流水线：KWS 唤醒 → ASR 语音转文字 → 大模型意图分类 → TTS 播报
- 3.1.2 sherpa-onnx KWS 唤醒 > 原理 > zipformer_kws 模型实时检测唤醒词（"小飞小飞"），sensitivity 调灵敏度（越低越灵但易误触发）
- 3.1.3 sherpa-onnx 离线 ASR > 流程 > zipformer_onnx 模型 greedy_search 将语音转文字；hotword 热词纠约定制词
- 3.1.4 GTCRN 神经网络降噪 > 原理 > 流式语音增强（onnx 模型），仅对 KWS 唤醒生效，抗风扇/电机/空调稳态噪声
- 3.2.1 本地 TTS 合成 > 流程 > tts_node 离线合成回复语音与提示音，支持播报打断
- 3.3.1 RKLLM 离线大模型意图识别 > 原理 > rkllm（Qwen3.5-0.8B 量化模型）在 NPU 上做意图分类，命中 `start` 意图 → 调用任务启动服务
- 3.3.2 运行态唤醒闸门 > 流程 > 任务运行中 `running=true` 暂停唤醒，任务结束恢复，防任务中误唤醒打断

### 3.2 实验目标

1. 掌握 sherpa-onnx 的离线唤醒（KWS）与识别（ASR）部署与参数调优 — 独立完成
2. 掌握本地 TTS 语音合成与播报打断 — 独立完成
3. 掌握 RKLLM 内嵌大模型（Qwen3.5-0.8B）的离线意图识别，并把"出发/开始任务/开始干活"等人类指令分类为 `start` 意图 — 原理理解

### 3.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能机器人小车 C1（板载瑞芯微 RK3576，6TOPS NPU）；具身智能实验箱 B2（六麦阵列/麦克风） |
| OS | Ubuntu 22.04 + ROS2 Humble（板载 ros2_venv，含 sherpa-onnx / rknnlite / rkllm） |
| 语音模型 | `/home/iflytek/models/zipformer_kws`（KWS 唤醒，zipformer_kws）<br>`/home/iflytek/models/zipformer_onnx`（ASR 识别）<br>`/home/iflytek/models/ns/gtcrn_simple.onnx`（GTCRN 降噪） |
| 大模型 | `/home/iflytek/models/rkllm/Qwen3.5-0.8B_w4a16_g128_rk3576.rkllm`（RKLLM 量化意图模型） |
| 触发服务 | `start_service: /mission_orchestrator/start`（LLM 命中 start 意图后调用） |
| 状态话题 | `mission_state_topic: /car1_brics_task/state`（running 字段：true 暂停唤醒 / false 恢复） |
| 主入口 | `ros2 launch car1_interaction full_interaction.launch.py`<br>（内含 `speech.launch.py`：wake_word_node + tts_node；`llm.launch.py`：大模型相关节点） |

### 3.4 实验难度

- 难度: ⭐⭐⭐ 综合性
- 重点: 本地化离线语音 + 边缘大模型意图识别的完整部署，理解"唤醒-识别-意图"三级门槛
- 难点: 唤醒灵敏度与误触发的平衡；汽车风扇/电机噪声下的识别鲁棒性；RKLLM 意图提示词（含 ASR 常见误识别词）的配置驱动

### 3.5 实验现象

**快速验证流程**（全程板载离线执行）：

1. 启动完整交互：`ros2 launch car1_interaction full_interaction.launch.py`
2. 唤醒：对麦克风说"小飞小飞"，板端播放"在呢"（提示音 `prompt_zainei.wav` 或 TTS 合成），进入听指令状态
3. 指令：说"出发"/"开始任务"/"开始干活"，ASR 转文字后送入大模型意图分类，命中 `start` 意图，随后触发任务启动服务（如在综合任务里就启动建图导航抓取闭环）
4. 无关闲聊：说"今天天气如何"，大模型回复闲聊语（不触发任务动作）
5. 运行闸门：任务运行中（`/car1_brics_task/state` 中 running=true）再说"小飞小飞"无效，任务完成恢复唤醒

**预期效果描述**：

- **唤醒**：`wake_word_node` 在灵敏度 `sensitivity=0.25` 下对"小飞小飞"稳定唤醒；唤醒词命中即播提示音，避免用户不知是否已唤醒
- **识别+意图**：ASR 把"出发吧/开始干活"等口语转为文字，大模型按 `intent_hints`（`wake_word.yaml` L22-26 的 start 组）把动词命中的都归类为 `start`，从而鲁棒触发任务
- **降噪**：风声/风扇噪声下仍能唤醒；GTCRN 仅对 KWS 生效，ASR 走原始音频（降噪会损害 ASR）
- **完全离线**：全程无外网调用，符合工厂车间内网/无网部署要求，延迟本地可控

### 3.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：离线语音链路架构] --> B[步骤2：KWS 唤醒词与灵敏度]
    B --> C[步骤3：离线 ASR 与热词]
    C --> D[步骤4：GTCRN 降噪]
    D --> E[步骤5：本地 TTS 合成]
    E --> F[步骤6：RKLLM 意图识别]
    F --> G[步骤7：意图驱动与运行闸门]
    G --> H[完成]
```

---

#### 步骤1：离线语音链路架构认知（阶段二：能理解，30min）

> 📌 本步骤对应源码：`interaction/car1_interaction/launch/full_interaction.launch.py`

**知识点讲解**：

**语音链路模块化（3.1.1）**

- **原理**：`full_interaction.launch.py` 把 `car1_speech`（语音）和 `car1_llm`（意图）两个 launch **include 进来一起起**，形成"麦克风 → 唤醒/识别 → 大模型 → TTS/扬声器"链路。`car1_speech` 的 `speech.launch.py` 只起 `wake_word_node` 与 `tts_node` 两个节点——注意真实 ASR 已**内含在 wake_word_node 内部**（唤醒后接着就识别命令），旧独立 asr_node 是 stub 假识别已从 launch 移除。
- 设计要点是**三级门槛**：先 KWS 唤醒（低计算、常开），唤醒后短窗口才做 ASR（省算力），再送大模型分类意图——避免大模型常开推理造成功耗与发热。

**操作步骤**：

1. 读 `full_interaction.launch.py` 与 `speech.launch.py`，画出节点/话题拓扑（wake_word_node、tts_node、LLM 相关节点）
2. 确认 `wake_word_node` 内含"唤醒→识别"的状态机（IDLE 监听 KWS → 命中唤醒 → 播提示音 + 进入 ASR 采集 → 出文字 → 回 IDLE）

**易错点**：

- ⚠️ 别用旧 asr_node（stub）；真实识别在 wake_word_node 内部，避免误接旧话题污染结果

---

#### 步骤2：KWS 唤醒词与灵敏度（阶段一：能运行，50min）

> 📌 本步骤对应源码：`car1_speech/config/wake_word.yaml`（wake_word/sensitivity/kws_model_dir/keywords_file）

**知识点讲解**：

**sherpa-onnx 唤醒（3.1.2）**

- **原理**：`wake_word: "小飞小飞"` 用 sherpa-onnx 的 `zipformer_kws` 模型做实时关键词检测，`sensitivity: 0.25` 是置信度门限——数值越小越灵敏（更易唤醒，也更多误触发），越大越钝（更不易误唤醒）。`keywords_file` 为空时用 `car1_interaction/tools/keywords.txt`（含 小飞小飞/小飞同学/你好小飞 等热词）的 pinyin。唤醒后 `prompt_wav`（`prompt_zainei.wav`）播"在呢"提示音提示继续说指令。

**操作步骤**：

1. 读 `wake_word.yaml`，确认唤醒词、`sensitivity`、模型路径
2. 在安静环境对麦克风说"小飞小飞"，观察唤醒命中与提示音
3. 逐一调节 `sensitivity`（0.1/0.25/0.5），记录"唤醒率 vs 误触发率"：

   | sensitivity | 唤醒率（10 次） | 误触发（10 分钟） |
   |------|------|------|
   | 0.1 |  |  |
   | 0.25（默认） |  |  |
   | 0.5 |  |  |

4. 答问：现场有风扇/电机时如何取舍？为什么要"唤醒后才能说指令"而不是一直开着识别？

**易错点**：

- ⚠️ 唤醒词是四字"小飞小飞"，两字或多音词识别不稳；改词需同步改 `wake_word` 与 `keywords_file`
- ⚠️ `sensitivity` 太低会频繁被环境声触发，指令还没说就进入 ASR 短窗

---

#### 步骤3：离线 ASR 与热词（阶段二：能理解，50min）

> 📌 本步骤对应源码：`car1_speech/config/wake_word.yaml`（asr_model_dir）；`car1_speech/tools/*.py`（asr_test/offline_stt）

**知识点讲解**：

**sherpa-onnx 识别（3.1.3）**

- **原理**：`asr_model_dir` 指向 `zipformer_onnx` 模型，`greedy_search` 解码做无热词的流式识别。ASR 在唤醒后的短窗口收集语音，输出文字。因为现场指令词汇有限，常用**热词/意图提示词**（`intent_hints`）兜底：即使识别出形近（如"出 发"被识别成带空格），提示词也能帮助意图分类匹配。

**操作步骤**：

1. 唤醒后依次说"出发""开始任务""开始干活"，查看 ASR 输出的文字（日志），记录形近误识别（如"出 发"）
2. 在 `wake_word.yaml` 的 `intent_hints.start.hints` 里补充你发现的新误识别词，实现"配置驱动"改词不改代码
3. 对比有无热词配置时 `start` 意图的命中率

**易错点**：

- ⚠️ 识别结果是意图分类的输入，误识别词若未列入 hints 会导致 `start` 漏触发——务必在实验中发现词就补进配置

---

#### 步骤4：GTCRN 神经网络降噪（阶段三：能改造，40min）

> 📌 本步骤对应源码：`car1_speech/config/wake_word.yaml`（onnx_denose / onnx_denoise_model）

**知识点讲解**：

**降噪为何只作用 KWS（3.1.4）**

- **原理**：`onnx_denoise: true` 启用 `gtcrn_simple.onnx` 流式语音增强，采集线程只收原始音频，`_handle_idle(KWS)` 阶段先降噪再喂 KWS——去稳态背景噪声（风扇/电机/空调）让唤醒更灵敏。**ASR 走原始音频不降噪**：因为降噪可能把说话人语音细节一并削掉，反而更难识别。这是"降噪只帮唤醒、不帮识别"的工程取舍。

**操作步骤**：

1. 打开 `onnx_denoise: false`，在风机旁测试唤醒率
2. 打开 `onnx_denoise: true`，`onnx_denoise_threads: 2`，重测唤醒率对比，记录降噪前后差异
3. 验证：降噪开关不影响 ASR 识别表现（走原始音频）

**易错点**：

- ⚠️ 不要为提升识别而把降噪套到 ASR 上——通常反而变差（特征被削）

---

#### 步骤5：本地 TTS 语音合成（阶段一：能运行，40min）

> 📌 本步骤对应源码：`car1_speech/car1_speech/tts_node.py`、`config/tts.yaml`、`config/prompt_zainei.wav`

**知识点讲解**：

**离线合成与播报（3.2.1）**

- **原理**：`tts_node`（`speech.launch.py` 注入 tts.yaml）监听 `/interaction/tts/speak` 话题（String），离线合成语音播放；`prompt_zainei.wav` 是预置提示音（也可 TTS 合成"在呢"）。TTS 支持"播报打断"：新的 speak 请求到达时停止当前播放播新的，保证回复紧跟前一次交互。

**操作步骤**：

1. 发布一条测试播报：`ros2 topic pub /interaction/tts/speak std_msgs/msg/String "data: '好的，我开始执行任务'" -1`
2. 连续发两条不同音频，观察后一条是否打断前一条
3. 对比用 `prompt_wav=prompt_zainei.wav` 与换空串时唤醒提示音的表现

**易错点**：

- ⚠️ 音频设备索引 `audio_device_index: -1` 自动检测 ES8388；换声卡需重设

---

#### 步骤6：RKLLM 离线大模型意图识别（阶段二：能理解，60min）

> 📌 本步骤对应源码：`car1_speech/config/wake_word.yaml`（llm / llm_server 段）；`car1_llm/launch/llm.launch.py`

**知识点讲解**：

**RKLLM 边缘意图（3.3.1）**

- **原理**：`llm_server` 段配置内嵌启动一个 flask_server，用 RKLLM 加载 `Qwen3.5-0.8B_w4a16_g128_rk3576.rkllm` 量化模型（4bit 权重/128 group size，专为 RK3576 NPU），`lib_path=/usr/lib/librkllmrt.so`，`venv_python=/home/iflytek/ros2_venv/bin/python3`，服务地址 `http://127.0.0.1:8080`。意图分类由提示词驱动：把 ASR 文字交给大模型，参照 `intent_hints` 判断是否属于 `start`（出发/开始/执行任务……）。命中后 `start_service: /mission_orchestrator/start` 被调用，进入任务执行。
- 因为它是"分类而非自由对话"，提示词把**标准词 + ASR 常见误识别词**都 fold 进 `intent_hints`，新发现误识别词直接补配置不用改代码。

**操作步骤**：

1. 读 `wake_word.yaml` 的 `llm_server` 段，确认模型路径/平台/服务端口
2. 验证意图服务可访问：`curl http://127.0.0.1:8080/...` 或运行 `car1_llm/tools/llm_test.py` 喂入"出发去做任务"，观察返回 `start`
3. 喂入闲聊"今天天气如何"，观察不命中 `start`
4. 在 `intent_hints.start.hints` 新增你发现的误识别词，重启服务验证命中

**易错点**：

- ⚠️ 大模型是"意图分类"工具，不要期望它对任意指令都动手；它只把命中 start 的任务词挑出来
- ⚠️ `wake_word.yaml` 里 `llm.server_url`/`llm_server.*` 端口被占时复用现有服务，确保端口不与其它 demo 冲突

---

#### 步骤7：意图驱动与运行态唤醒闸门（阶段三：能改造，60min）

> 📌 本步骤对应源码：`car1_speech/config/wake_word.yaml`（start_service / mission_state_topic）

**知识点讲解**：

**从"识别"到"任务"的桥接（3.3.2）**

- **原理**：LLM 命中 `start` 意图后调用 `start_service: /mission_orchestrator/start`，把语音意图接到上层任务编排。同时订阅 `mission_state_topic: /car1_brics_task/state`：当其中 `running=true`（任务正在执行）时**暂停唤醒**，避免任务中途被"小飞小飞"打断；任务完成 `running=false` 恢复唤醒。这就完成了"语音"与"机器人执行"之间的双向节流。

**操作步骤**：

1. 把语音链路接到一个轻量任务（先接一个打印/亮灯的 Trigger 服务或直连下层任务，见 exp04 的端到端）
2. 说"出发执行任务"，观察 `start` 触发任务启动、`/car1_brics_task/state` 变 running=true
3. 任务运行中再说"小飞小飞"，确认不再唤醒（闸门生效）；任务完成后再唤醒恢复
4. 填性能表：从唤醒到任务启动的总延迟（应本地可控、毫秒级推理 + 传输）

**易错点**：

- ⚠️ 闸门依赖 `mission_state_topic` 的 running 字段由任务侧正确发布——综合任务状态机需同步维护该话题（见 exp04）

---

### 3.7 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 唤醒词不响应 | sensitivity 太高或环境噪声大 | 调低 `sensitivity`（0.25→0.1），开 GTCRN 降噪 |
| 频繁误唤醒 | sensitivity 太低 | 调高；确保 hotword 准确 |
| "出发"未触发任务 | ASR 误识别词未列入 hints | 往 `intent_hints.start.hints` 补词（配置驱动） |
| 闲聊也触发 start | 提示词意图边界太宽 | 收紧 hints，只保留明确任务动词 |
| 任务中还能被唤醒打断 | 闸门未生效 | 检查任务侧是否发布 `/car1_brics_task/state` 且 running=true |
| 大模型服务起不来 | 端口占用或模型路径错 | 复用已有服务；核对 rkllm 模型路径与 lib_path |
| 播报不打断 | TTS 打断逻辑被跳过 | 确认 tts_node 订阅 `/interaction/tts/speak` 且实现打断 |

### 3.8 扩展实验

**扩展方向 1：多意图扩展（停车/避障/供料）**
- 在 `intent_hints` 增加 `stop`（停止）、`pause`（暂停）等意图，映射到 `/arm_controller/go_home` 或 `/cmd_vel` 零速话题，形成更完整的产线指令集

**扩展方向 2：唤醒语料鲁棒性评测**
- 采集多人/不同音量/不同距离下"小飞小飞"唤醒样本，绘制 sensitivity 的 ROC，确定本机最优工作点

### 3.9 实验报告要求

**评分标准**：链路架构 10 分 + KWS 唤醒灵敏度调优 20 分 + ASR 与热词 20 分 + GTCRN 降噪对比 10 分 + TTS 合成/打断 10 分 + RKLLM 意图识别 20 分 + 闸门与延迟 10 分 = 100 分。

**报告必含内容**：
1. 离线语音链路框图（麦克风→KWS→ASR→大模型→TTS），标注各节点与话题
2. sensitivity 灵敏度对比表（3.6 步骤 2 表）
3. 误识别词补充记录与 `intent_hints` 配置片段
4. GTCRN 开/关唤醒率对比
5. 回答思考题：为什么降噪只作用 KWS 不作用 ASR？为什么用大模型做意图分类而不是十几个 if/else？运行闸门的作用？
6. 实验心得与问题记录

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-09-23 | 初版生成（基于 interaction/car1_speech 与 car1_llm 源码与配置：wake_word.yaml（wake_word/sensitivity/kws/asr/llm_server/prompt_wav/onnx_denoise）、speech.launch.py、full_interaction.launch.py、llm.launch.py；意图提示词与任务闸门取自 wake_word.yaml 实测值） |