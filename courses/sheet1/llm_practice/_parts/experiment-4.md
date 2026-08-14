# 实验4：具身智能工厂--语音交互集成测试（6h）

> **源码**：`ros2_ws/src/xflz_eai_car1/app/eai_factory/`
> **主命令**：`ros2 launch eai_factory eai_factory.launch.py`
> **覆盖模块**：N1 语音节点（`voice_node.py`）→ N2 调度器（`scheduler_node.py`）
> **测试用例**：`docs/07_语音测试用例.md`（TC1~TC6）

### 4.1 关联知识点

- 3.1.1 KWS 唤醒词 > 原理 > 本地关键词检测（小飞小飞/小飞同学/芝麻开门），唤醒后进入识别态
- 3.1.2 ASR 热词 > 原理 > modified_beam_search + 热词文件提升"开始装货"等专有词识别率
- 3.1.3 TTS 播报 > 概念 > 固定播报文案（装货完成/分拣完成/码垛完成）离线合成播放
- 3.2.1 意图三分类 > 流程 > LLM 将指令分为 load/sort/palletize/none 并发布 /eai_factory/intent
- 3.2.2 intent_hints > 原理 > 配置驱动意图提示词，收录 ASR 误识别词（马舵/封建）无需改代码
- 3.2.3 语音打断 > 原理 > SPEAKING 态唤醒词打断 → interrupt 信号 → N2 中止当前任务

### 4.2 实验目标

1. 理解语音链路 KWS→ASR→LLM→TTS 的完整流程与状态机（IDLE→LISTENING→PROCESSING/SPEAKING→IDLE）— **原理理解**
2. 掌握唤醒词、ASR 热词、意图提示词（intent_hints）的配置方法并实测验证效果 — **流程掌握**
3. 独立完成"语音→意图→任务→完成播报"闭环测试，并能解读 voice/scheduler 各节点日志 — **独立完成**
4. 理解语音打断（R8）机制与 interrupt 信号的传播路径（N1→N2→N-grasp）— **原理理解**
5. 能够将"意图三分类 + 配置驱动"模式迁移到其他任务场景（新增任务意图、新增误识别词）— **迁移应用**

### 4.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱 B2 / 机器人小车 C1（5DOF 机械臂，总线舵机）+ XFM 麦克风阵列（未检测到自动回退板载 mic） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10；语音节点须用 ros2_venv（`/home/iflytek/ros2_venv/bin/python3`，sherpa_onnx 仅在 venv 中） |
| 核心库 | rclpy、sherpa_onnx（KWS/ASR/TTS 离线推理）、requests（OpenAI 兼容 LLM 客户端） |
| 模型 | KWS/ASR/TTS 模型（`/home/iflytek/models/`）+ Qwen3.5-0.8B w4a16（RKLLM，内嵌服务端口 8080） |
| 依赖 | 需 ROS2 Humble 环境变量（`source /opt/ros/humble/setup.bash` + `source /home/iflytek/ros2_ws/install/setup.bash`） |

### 4.4 实验难度

- 难度: ⭐⭐
- 重点: 语音链路四段（KWS→ASR→LLM→TTS）与意图路由（intent → start_load/start_sort/start_palletize）
- 难点: 热词与意图提示词调优（ASR 误识别词的收录与验证）；打断机制与任务中止的跨节点联动

### 4.5 实验现象

**快速验证流程**：

1. 一键启动系统：`ros2 launch eai_factory eai_factory.launch.py`，观察 voice/scheduler 节点日志
2. 对麦克风说「小飞小飞」→ 听到 KWS 提示音，日志出现 `IDLE → LISTENING`
3. 接着说「开始装货」→ 日志出现 `[LLM] LLM 分类: "load"`，终端 2 的 `ros2 topic echo /eai_factory/intent` 输出 `data: 'load'`
4. 扬声器播报"好的，开始装货"；任务执行完成后调度器经 /eai_factory/speak 请求播报"装货完成"
5. 播报"好的…"尚未结束再说「小飞小飞」→ 播报被打断，`/eai_factory/interrupt` 输出 `data: true`

**预期效果描述**：

- 三个唤醒词（小飞小飞/小飞同学/芝麻开门）均可唤醒，每次唤醒都能听到提示音
- 三条任务指令（开始装货/开始分拣/开始码垛）均被正确分类并路由到对应任务服务；无关指令（如"讲个笑话"）播报"未识别指令，请重新唤醒"且不发布 intent
- 热词启用后"开始分拣"等词条识别更稳（可与关闭热词 A/B 对比）
- 打断后回到监听态，可继续说新指令；机械臂动作中打断会停止动作并回 work

### 4.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：一键启动与节点观察] --> B[步骤2：唤醒词测试]
    B --> C[步骤3：意图识别测试]
    C --> D[步骤4：语音打断测试]
    D --> E[步骤5：全链路闭环与测试用例]
```

---

#### 步骤1：一键启动与节点观察（50min）

**知识点讲解**：

**KWS 唤醒（3.1.1）**
- **原理**：语音链路第一段是 KWS（Keyword Spotting）本地关键词检测。节点上电后处于 IDLE 态，只对唤醒词做持续监听（不识别其他语音、省算力）；检测到唤醒词后播放提示音（kws.wav）并进入 LISTENING 态开始 ASR。KWS 是整条链路的"门禁"——它决定"什么时候开始听指令"，且每轮对话结束后回到 IDLE，下一次交互必须重新唤醒。
- **源码对应**：`voice_node.py` L836-875（run 主循环）与 L574-591（_handle_idle KWS 检测）；唤醒词通过 yaml 声明（`eai_factory.yaml` L13）并在启动时下发麦克风阵列（`voice_node.py` L844-846）

```python
# voice_node.py L586-591：IDLE 态 KWS 唤醒检测
result = self.kws.get_result(self.kws_stream)
if result:
    kw = result.split("@")[-1].strip() if "@" in result else result.strip()
    self.kws.reset_stream(self.kws_stream)
    log_kws.info(f"唤醒: {kw}")
    self._play_prompt_then_start_asr()
    log.info("IDLE → LISTENING")
```

**操作步骤**：

1. 终端 1 一键启动系统：
   ```bash
   source /opt/ros/humble/setup.bash
   source /home/iflytek/ros2_ws/install/setup.bash
   ros2 launch eai_factory eai_factory.launch.py
   ```
2. 观察启动日志（docs/07 L19-33）：`eai_factory_voice`（N1）与 `eai_factory_scheduler`（N2）进程启动；voice 日志依次出现"使用麦克风阵列: 录音=plughw:x,0" → "启动 LLM: Qwen3.5-0.8B… (端口 8080)" → "LLM 服务就绪" → "N1 voice node 初始化完成" → "N1 voice 就绪 — 说唤醒词开始"
3. 终端 2 验证节点与 LLM 服务：
   ```bash
   ros2 node list        # 应看到 /eai_factory_voice /eai_factory_scheduler 等
   curl -s http://127.0.0.1:8080/v1/models   # LLM 服务，返回模型 JSON
   ```

**易错点**：

- ⚠️ 日志卡在"启动 LLM"或"LLM 启动超时" → LLM 服务占用约 500MB 内存、首次加载慢；内存不足时可用 `start_voice:=false` 跳过（launch L77-78），但本实验必须语音，需保证内存充足
- ⚠️ 看不到"使用麦克风阵列"日志 → 麦克风阵列未识别自动回退板载 mic（`voice_node.py` L259-269），唤醒灵敏度会下降；重新插拔阵列后重启

---

#### 步骤2：唤醒词测试（70min）

**知识点讲解**：

**KWS 唤醒词配置（3.1.1）**
- **原理**：唤醒词由 yaml 的 `voice.wakeup_words` 配置（默认 ["小飞小飞", "小飞同学", "芝麻开门"]），节点启动时逐个下发到麦克风阵列的硬件唤醒（`voice_node.py` L844-846：`for word in self.wakeup_words[:3]: self.mic_array.set_wake_word(word)`）。板载 mic 回退路径则用 sherpa_onnx KeywordSpotter 软件检测（`_init_kws`，L338-355）。检测到唤醒词后 `_play_prompt_then_start_asr`（L593-612）先播放预加载的提示音 PCM，再清空音频队列（排掉提示音回声）进入 LISTENING。
- **源码对应**：`voice_node.py` L844-846（下发唤醒词）、L593-612（提示音与进入 LISTENING）；`eai_factory.yaml` L13（唤醒词配置）

```python
# voice_node.py L593-599：唤醒后播放提示音
def _play_prompt_then_start_asr(self):
    if self._prompt_pcm:
        prompt_dur = len(self._prompt_pcm) / (2 * 2 * self.sample_rate)
        self.playback.write(self._prompt_pcm)
        wait_time = prompt_dur + 0.4   # 压缩等待，提升唤醒响应
        time.sleep(wait_time)
```

**操作步骤**：

1. 终端 2 保持监听（可选）：
   ```bash
   ros2 topic echo /eai_factory/interrupt
   ```
2. 对麦克风依次说「小飞小飞」「小飞同学」「芝麻开门」，每次等待提示音结束
3. 对照 docs/07 TC1（L50-62）核对日志：每个唤醒词都应出现 `[KWS] 硬件唤醒检测` + `[Main] IDLE → LISTENING`
4. 修改唤醒词实验：编辑 `config/eai_factory.yaml` 的 `voice.wakeup_words`，例如仅保留 ["小飞同学"]，重启后确认其余唤醒词不再生效

**易错点**：

- ⚠️ 唤醒后提示音未播放或很小 → 检查 aplay 设备（`playback_device`）是否被占用；`Playback.interrupt()`（L94-102）会在打断时 kill 并重开 aplay 管道
- ⚠️ 修改 wakeup_words 后不生效 → 参数在节点启动时一次性读取（`voice_node.py` L239），需重启 launch；不要在运行时 `ros2 param set`

---

#### 步骤3：意图识别测试（90min）

**知识点讲解**：

**LLM 意图三分类（3.2.1）**
- **原理**：ASR 识别出指令文本后，voice 节点把文本交给本地 LLM（Qwen3.5-0.8B）做三分类。`_llm_intent_worker`（L688-767）将提示词与用户指令拼成一条 user 消息（flask_server 忽略 system 角色，只取最后一条 user 消息），LLM 流式输出后解析出 load/sort/palletize 之一；为兜底小模型误判，还叠加了基于 ASR 原文的关键字纠正（`_keyword_fallback`，L769-786，如"马舵→码垛"）与 LLM 结果做仲裁。识别成功后 `_publish_intent`（L816-820）发布 /eai_factory/intent，scheduler 的 `_intent_cb`（L75-78）收到后 `_run_task`（L80-94）路由到对应任务服务。
- **源码对应**：`voice_node.py` L688-767（意图分类 worker）、L769-786（关键字兜底）、L816-820（发布 intent）；`scheduler_node.py` L75-94（intent 路由）

```python
# voice_node.py L746-754：关键字校验/纠正 LLM 结果
kw_intent = self._keyword_fallback(user_text)
if kw_intent is not None:
    intent = kw_intent
    if kw_intent != llm_intent:
        log_llm.info(f"关键字纠正: LLM={llm_intent} → 关键字={kw_intent} ({user_text})")
else:
    intent = llm_intent
```

**ASR 热词（3.1.2）**
- **原理**：`voice.asr.hotwords_enable: true` 时 ASR 解码方式从 greedy_search 切换为 modified_beam_search 并加载热词文件（`config/hotwords.txt`，6 个词条：开始装货/开始分拣/开始码垛/装货/分拣/码垛），score=2.0 提升这些专有词的识别权重（`_init_asr`，L363-385）。热词对"开始分拣"这类专有指令的识别稳定性至关重要——不开热词时 beam 解码容易把"分拣"识别成"风景"。
- **源码对应**：`voice_node.py` L363-385（热词分支）、L407（热词状态日志）；`eai_factory.yaml` L20-23（热词配置）；`config/hotwords.txt` L1-6

**intent_hints 配置（3.2.2）**
- **原理**：`voice.llm.intent_hints` 是配置驱动的意图提示词，每意图一组 hints（标准词 + ASR 常见误识别词）。`_llm_intent_worker`（L699-714）把 hints 拼进 LLM 提示词："- load：装货、开始装货…"，并追加 "- none：与上述无关"。新发现误识别词（如"马舵"→码垛、"封建"→分拣）只需在 yaml 补充，不用改代码——这是配置驱动设计的核心价值。
- **源码对应**：`eai_factory.yaml` L30-36（intent_hints 配置）；`voice_node.py` L699-714（hints 拼装 prompt）

```python
# voice_node.py L707-714：LLM 意图分类提示词
user_prompt = (
    "请判断下面这句话属于哪种任务，只回答一个英文单词"
    "（load/sort/palletize/none），不要解释：\n"
    + "\n".join(lines)
    + "\n"
    f"用户指令：{user_text}\n"
    "答案："
)
```

**操作步骤**：

1. 终端 2 监听 intent 话题：`ros2 topic echo /eai_factory/intent`
2. 依次唤醒后说「开始装货」「开始分拣」「开始码垛」，对照 docs/07 TC2（L69-97）核对：终端 2 依次输出 `data: 'load' / 'sort' / 'palletize'`，扬声器播报"好的，开始装货"等
3. 观察 N2 路由日志：`[SCHEDULER] intent: load` → `[SCHEDULER] set grasp task -> load` → `[SCHEDULER] triggering grasp for task: load`（scheduler L148-150）
4. 无关指令测试（docs/07 TC3）：说「讲个笑话」→ 播报"未识别指令，请重新唤醒"，intent 无输出，日志 `LLM 分类: "none"`
5. 热词 A/B 对比：把 `hotwords_enable` 改为 false 重启，多次说「开始分拣」，观察 ASR 是否出现"风景/封建"等误识别；再改回 true 对比

**易错点**：

- ⚠️ ASR 输出"风景/封建"而非"分拣" → 热词未生效。检查 yaml `hotwords_enable: true` 且启动日志含 `ASR 热词启用: .../hotwords.txt (score=2.0)`（L380-381）；热词只在初始化时读取，改配置需重启
- ⚠️ LLM 分类为 none 但指令正确 → 小模型对生僻表述误判。通过关键字兜底仍可纠正（L746-754），若频繁失败应在 intent_hints 中补充该表述
- ⚠️ 播报"好的，装货完成"与源码不符（docs TC2 表格中的旧文案） → 源码实际行为是识别后播"好的，开始装货"（`phrase_recognize_ok + phrases_task_start`，L759），"装货完成"由任务真正完成后 scheduler 播报，勿混淆

---

#### 步骤4：语音打断测试（60min）

**知识点讲解**：

**语音打断（3.2.3）**
- **原理**：打断是 R8 需求的实现。TTS 播报（SPEAKING 态）或任务执行期间，用户再说唤醒词即可中止当前流程：voice 节点的 `_handle_speaking`（L636-661）在 SPEAKING 态继续跑 KWS，检测到唤醒词后 `interrupt_event.set()`、`playback.interrupt()`（kill 掉 aplay 停止当前播报）、发布 /eai_factory/interrupt=true，然后回到 LISTENING 听新指令。scheduler 收到 interrupt 后记录任务中止（`_interrupt_cb`，L181-185）；N-grasp 收到 interrupt 会停止机械臂动作并回 work（grasp_node.py L179-186）。注意 `interrupt_event` 只置位一次，`_start_speaking`（L796）在开播前会 clear，避免陈旧信号压制新播报。
- **源码对应**：`voice_node.py` L636-661（SPEAKING 态打断检测）、L822-825（发布 interrupt）；`scheduler_node.py` L181-185（中断日志）；`grasp_node.py` L179-186（中止动作回 work）

```python
# voice_node.py L653-661：打断分支
if result:
    kw = result.split("@")[-1].strip() if "@" in result else result.strip()
    self.kws.reset_stream(self.kws_stream)
    log_kws.info(f"打断: {kw}")
    self.interrupt_event.set()
    self.playback.interrupt()
    self._publish_interrupt(True)
    self._play_prompt_then_start_asr()
    log.info("SPEAKING → LISTENING (打断)")
```

**操作步骤**：

1. 终端 2 监听 interrupt：`ros2 topic echo /eai_factory/interrupt`
2. 唤醒后说「开始装货」，在"好的…"还没播完时立刻说「小飞小飞」（docs/07 TC4，L117-133）
3. 核对现象：播报被中途掐断；终端 2 输出 `data: true`；日志 `[KWS] 打断: 硬件唤醒` + `[Main] SPEAKING → LISTENING (打断)`
4. 打断后继续说「开始分拣」，确认能正常重新识别（回到监听态）
5. 扩展实验（结合机械臂）：触发装货任务后，在机械臂动作中发 interrupt，观察 grasp 日志 `VOICE INTERRUPT — stopping grasp, going work` 与机械臂停止动作回 work（docs/09 TG7）

**易错点**：

- ⚠️ 打断后播报继续响 → 提示音播放采用常驻 aplay 管道（`Playback`，L59-121），打断通过 kill 管道进程实现；若杀不干净会残留回声，`_play_prompt_then_start_asr` 里的两次队列排空（L603-609）用于清掉提示音回声
- ⚠️ interrupt 只在 SPEAKING 态生效 → 任务执行中（PROCESSING 已完成、已播"开始装货"进入 SPEAKING）打断才有效；IDLE 态唤醒词走正常唤醒路径，不会发 interrupt

---

#### 步骤5：全链路闭环与测试用例（90min）

**知识点讲解**：

**TTS 固定播报（3.1.3）**
- **原理**：播报文案分两段：(1) 识别确认段——`phrase_recognize_ok`（"好的，"）+ `phrases_task_start`（"开始装货/开始分拣/开始码垛"），由 voice 节点在意图发布后立即 TTS（L759）；(2) 任务完成段——`phrases_task_done`（"装货完成/分拣完成/码垛完成"），由 scheduler 收到 grasp 完成状态后经 /eai_factory/speak 请求 voice 播报。TTS 用 sherpa_onnx OfflineTts（Matcha 声学模型 + vocos 声码器，L409-432）离线合成 PCM，通过常驻 aplay 管道播放，无网络依赖。
- **源码对应**：`voice_node.py` L302-307（固定文案）、L409-432（TTS 初始化）、L827-830（_speak_cb）；`scheduler_node.py` L195-210（grasp 完成→播报）

```python
# scheduler_node.py L202-208：任务完成 → speak 播报
if status == 'done':
    phrase = {'load': '装货完成', 'sort': '分拣完成',
              'palletize': '码垛完成'}.get(task, '任务完成')
    self.get_logger().info(f'[SCHEDULER] task {task} done — announce "{phrase}"')
    speak = String()
    speak.data = phrase
    self.speak_pub.publish(speak)
```

**操作步骤**：

1. 终端 2 同时监听三个话题（docs/07 TC6）：
   ```bash
   ros2 topic echo /eai_factory/intent
   ros2 topic echo /eai_factory/grasp/status
   ros2 topic echo /eai_factory/speak
   ```
2. 唤醒后说「开始分拣」，对照 docs/07 L163-173 核对全链路时序：`[VOICE] intent: sort` → `[SCHEDULER] set grasp task -> sort` → grasp 固定抓取序列执行 → `grasp: status: sort|done` → `[SCHEDULER] task sort done — announce "分拣完成"` → `[VOICE] speak request: "分拣完成"` → 扬声器播出"分拣完成"
3. N2 播报请求直测（docs/07 TC5）：终端 2 发布 `ros2 topic pub -1 /eai_factory/speak std_msgs/msg/String "data: '装货完成'"`
4. 依次执行 docs/07 全部用例 TC1~TC6，记录每条用例的操作、日志摘录与结果

**易错点**：

- ⚠️ 完成播报缺失 → grasp 未发 status（检查 `grasp: status: task|done` 日志）或 scheduler 未订阅（`grasp_status_sub`，L50-51）；全链路要求 grasp 节点在跑
- ⚠️ 全链路时机械臂不动但播报正常 → 语音闭环（N1↔N2）正常但 N-grasp/arm_controller 未就绪；scheduler 有 2s 定时器自动重试（L136-144），确认 `ros2 service list | grep grasp`
- ⚠️ 终端 2 echo 三个话题时命令串行阻塞 → 分三个终端分别 echo，或用 `tmux` 分窗

### 4.7 注意事项

- ⚠️ 语音节点必须用 ros2_venv python 启动（sherpa_onnx 仅 venv 有），launch 已自动配置（`eai_factory.launch.py` L99-105）；不要手动用系统 python 跑 voice_node.py
- ⚠️ LLM 服务占用约 500MB 内存并自动拉起（端口 8080）；内存不足时 `start_voice:=false` 跳过（launch L77-78）
- ⚠️ 实机联调时确保机械臂周围无人员/障碍，打断与急停测试遵循"先预演、后实机"原则
- ⚠️ 唤醒/识别对安静环境敏感，测试时避免空调风噪与多人同时说话
- ⚠️ 每次交互结束需重新唤醒；长时间未操作自动回 IDLE

### 4.8 实验总结

**完成成果**：

- 一键启动 eai_factory 并定位 N1 voice / N2 scheduler 节点与 LLM 服务
- 完成三个唤醒词的唤醒测试，验证提示音与 IDLE→LISTENING 状态迁移
- 完成三条任务指令的意图识别与路由测试，验证 LLM 分类 + 关键字兜底双保险
- 完成热词 A/B 对比与 intent_hints 误识别词补充，理解配置驱动价值
- 完成语音打断测试与全链路闭环（语音→意图→任务→完成播报）
- 按 docs/07 用例表完成 TC1~TC6 全部记录

**技能收获**：

- 掌握 KWS→ASR→LLM→TTS 四段语音链路的实现与状态机
- 学会通过 yaml 配置唤醒词、ASR 热词与意图提示词
- 学会用 `ros2 topic echo / service call` 验证跨节点通信并解读日志
- 理解 interrupt 打断信号的传播路径与任务中止机制

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| LLM 启动超时/服务未就绪 | 内存不足或加载慢 | 关其他进程；等待 120s；`start_voice:=false` 排查其余模块 |
| ASR 识别"风景/封建" | 热词未启用或配置未生效 | 置 `hotwords_enable: true` 重启；核对启动日志热词提示 |
| 唤醒词修改不生效 | 参数启动时一次性读取 | 修改 yaml 后重启 launch |
| LLM 意图误判 | 小模型（0.8B）对生僻词不稳 | 依赖关键字兜底；在 intent_hints 补充误识别词 |
| 打断无 interrupt 输出 | 不在 SPEAKING 态 | 在播报"好的…"期间打断；确认麦克风阵列唤醒正常 |
| 完成播报缺失 | grasp 未发 status | 确认 grasp 节点运行与 `grasp: status: task\|done` 日志 |

### 4.9 实验报告要求

**思考题**：

1. 为什么系统采用"先唤醒、再识别"的两段式交互，而不是持续全量 ASR？KWS 模式在功耗与算力上有什么优势？
2. ASR 热词为什么必须切换到 modified_beam_search 解码才生效？greedy_search 与 beam_search 解码在热词机制上的本质区别是什么？
3. intent_hints 中收录的"马舵、封建"等误识别词起什么作用？LLM 分类之外为什么还要保留关键字兜底（_keyword_fallback）？
4. 语音打断（R8）通过 interrupt 话题传播，如果打断发生在 N-grasp 机械臂动作中，任务状态如何恢复？结合 grasp_node.py 的 _interrupt_cb 说明。
5. 若要把任务从三类扩展到四类（例如新增"巡检"），需要修改哪些配置与代码？哪些环节可以不动代码完成？

**评分标准**：一键启动与节点观察 15 分 + 唤醒词测试 20 分 + 意图识别与热词对比 25 分 + 语音打断测试 15 分 + 全链路闭环与用例记录 25 分 = 100 分。
