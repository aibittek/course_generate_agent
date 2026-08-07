## 实验2：基于讯飞六麦阵列与sherpa-onnx的本地流式语音识别(ASR)实验（4h）

> 📦 **源码位置**: `ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/asr_test.py`
> 🎯 **主入口命令**: `python3 asr_test.py --mic-array`
> 🔗 **复用实验1**: 串口通信(`uart_device.py`)、AIUI协议解析(`xf_mic_array.py`)、ALSA录音(`audio_test.py`)

### 2.1 关联知识点

- 2.0.1 音频通路与 ALSA 设备 > 原理 > 6 麦阵列在 ALSA 中呈现为 XFM 声卡,16kHz/16bit/mono
- 2.0.2 6 麦唤醒驱动录音 > 流程 > 串口握手→设唤醒词→等待 wakeup→arecord/alsa
- 2.1.1 detect_xfm_devices() 设备自动检测 > 源码 > 解析 arecord -l 输出 grep XFM
- 2.1.2 AudioMixer 增益与 ALC > 原理 > PGA 0~+24dB + 数字 -30~+6dB + ALC 自动电平
- 2.1.3 switch_input_to_mic 输入复用 > 原理 > XFM 6 麦阵列默认 Line 输入需切到 Mic
- 2.2.1 OnlineRecognizer 构造 > 流程 > from_transducer 加载 4 个模型文件
- 2.2.2 Transducer 架构 > 原理 > encoder+joiner+decoder 三件套
- 2.2.3 RKNN NPU 推理 > 概念 > provider=rknn 走 NPU 加速 vs cpu
- 2.3.1 accept_waveform 流式输入 > 流程 > 100ms 块 feed 进 stream
- 2.3.2 decode_stream 增量解码 > 原理 > is_ready 循环解码
- 2.3.3 is_endpoint 内置端点 > 原理 > rule1/rule2/rule3 三规则协同
- 2.3.4 blank_penalty 空符号惩罚 > 调参 > 抑制字重复/漏字
- 2.4.1 hotwords 热词格式 > 概念 > 按 token 空格分隔,需 modified_beam_search
- 2.4.2 greedy vs modified_beam_search > 对比 > 速度/精度的取舍
- 2.5.1 single-stream 复用 > 设计 > reset 而非 create_stream 保留上下文
- 2.5.2 100ms 块节奏 > 实践 > latency/吞吐/CPU 占用的平衡点

### 2.2 实验目标

1. 理解 asr_test.py 启动到识别结束的完整代码执行流 — **原理理解**
2. 掌握 6 麦阵列在 ASR 链路中的角色(唤醒→增益→识别) — **流程掌握**
3. 能够独立调优 rule1/rule2/rule3 端点检测参数 — **调参能力**
4. 能够配置热词文件解决常用词的误识别(如"小飞"→"小飞机") — **实战能力**
5. 能够将 ASR 与命令词解析、状态机集成 — **迁移应用**

### 2.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2（含讯飞 XFM 6 麦阵列） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 |
| 核心库 | sherpa-onnx==1.10.0、numpy、scipy(resample) |
| 推理后端 | RKNN(RK3576 NPU) / CPU fallback |
| 模型 | zipformer-zh-14M(encoder/decoder/joiner.rknn + tokens.txt,~14MB) |
| 主入口 | `tools/asr_test.py` (主) + `tools/audio_test.py`(验证) + `tools/xf_mic_array.py`(唤醒) + `tools/audio_mixer.py`(增益) |

### 2.4 实验难度

- 难度: ⭐⭐⭐ 中偏高
- 重点: asr_test.py 7 个模块的拆分理解;端点检测参数调优;热词配置
- 难点: NPU 推理 provider 配置;blank_penalty 与解码延迟的平衡;长时间会话流式识别的状态管理

### 2.5 实验现象

**快速验证流程**:
1. 确认 6 麦阵列插入 USB(出现 `/dev/ttyACM0` 和 `plughw:4,0/4,1`)
2. 启动:`cd tools && python3 asr_test.py --mic-array`
3. 唤醒:说"小飞小飞" → 终端打印 `✓ 检测到唤醒! 开始语音识别...`
4. 说话:说"你好小飞同学" → 终端实时打印 `0:你好小飞同学` 增量结果
5. 停顿 1.5s → 自动判定端点,打印完整 segment,segment_id 自增
6. Ctrl+C 结束 → 打印 `Done.`

**预期效果**:
- 唤醒响应延迟 < 1.0s(从说唤醒词到终端打印"✓ 检测到唤醒")
- 端点判定 1.5-4.5s(rule2 已有结果后静音;rule1 长时间无结果静音)
- 100 条常用指令 WER < 10%(启用 hotwords 后)
- CPU 占用 < 50%(NPU 推理时)

### 2.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤0:录音验证] --> B[步骤1:设备与唤醒]
    B --> C[步骤2:增益与ALC]
    C --> D[步骤3:ASR引擎构建]
    D --> E[步骤4:流式主循环]
    E --> F[步骤5:端点调优]
    F --> G[步骤6:热词与解码]
    G --> H[步骤7:业务集成]
    H --> I[完成]
```

---

#### 步骤0：录音与播放验证（阶段一：能运行，15min）

> 本步骤对应 `tools/audio_test.py`(已支持讯飞六麦阵列 `--mic-array` 模式),在任何 ASR 实验之前**必须**先验证硬件通路,确保麦克风能录到清晰语音、扬声器能正常播放。

**知识点讲解**：

**音频通路与 ALSA 设备（2.0.1）**
- **原理**：Linux 下音频设备由 ALSA(Advanced Linux Sound Architecture)子系统管理,通过 `arecord -l` 列出所有录音设备,`aplay -l` 列出所有播放设备。**讯飞六麦阵列**在 ALSA 中呈现为 `XFM-DP-V*` 设备,录音子设备为 `plughw:N,0`,播放子设备为 `plughw:N,1`(同一 USB 声卡的 0 号和 1 号 device)。6 麦模块的音频采样率固定 **16kHz、16bit、单声道**(S16_LE 格式),与 ASR 引擎输入完全匹配,可直接送入 sherpa-onnx 识别。
- **源码对应**:`asr_test.py` 的 `detect_xfm_devices()` 解析 `arecord -l` 输出,自动识别 `XFM` 关键字(L84-116)

**6 麦唤醒驱动录音（2.0.2）**
- **原理**：6 麦阵列通过 USB HID/ACM 暴露串口(VID=0x1a86, PID=0x55d4),与音频流是**两条独立通路**:串口传控制命令(握手/设唤醒词/唤醒事件),USB Audio 传 PCM 数据。`--mic-array` 模式先连串口,等待 `wakeup_callback` 触发后**再启动 alsa 识别**,这样能保证识别的是「唤醒后的有效指令」而不是触发前的环境噪声。
- **源码对应**:`asr_test.py` `main()` L417-466  `XfMicArray.start()` → `wakeup_detected.wait()` → `mic_array_instance.stop()` → 进入主循环

**操作步骤**：

1. 确认 6 麦阵列已插入 USB,设备文件已出现:
   ```bash
   # 串口设备
   ls -l /dev/ttyACM*      # 应出现 /dev/ttyACM0
   # 音频设备
   arecord -l | grep -i XFM
   # 期望: card 4: XFMDPV0018 [XFM-DP-V0.0.18], device 0: USB Audio [USB Audio]
   ```

2. **录音测试**(唤醒后录 3 秒):
   ```bash
   cd ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/
   python3 audio_test.py --mic-array --mode record -o test.wav -d 3
   # 流程: 连串口 → 设置唤醒词"小飞同学" → 等待唤醒 → arecord 3 秒
   # 终端输出: ✓ 检测到唤醒! Recording: device=plughw:4,0 ... saving to: test.wav
   #          Done: test.wav (94.0 KB)  (3 秒 16kHz 16bit mono ≈ 94KB)
   ```

3. **播放测试**(用录制的 wav 验证扬声器通路):
   ```bash
   python3 audio_test.py --mic-array --mode play rec.wav
   # 流程: 自动选择播放设备 → mono→stereo 自动转换 → aplay
   # 终端输出: [检测设备] 使用播放设备: plughw:4,1
   #          Playing: rec.wav  ...  Done.
   ```

4. **快速回环验证**(录完立即播,人耳听自己说的话):
   ```bash
   python3 audio_test.py --mic-array --mode record -o rec.wav -d 3 && \
   python3 audio_test.py --mic-array --mode play rec.wav
   # 一句话:唤醒→录3秒→播出来,确认硬件通路完整
   ```

5. **可选:质量分析**(用 audio_analyzer 检查 RMS/峰值/频谱):
   ```bash
   python3 audio_test.py --mic-array --mode record -o rec.wav -d 3 --analyze
   # 输出:RMS=0.123  Peak=0.487  SNR=42.1dB  Duration=3.0s
   # 期望:RMS > 0.01(有声音)、Peak < 0.95(未削波)、SNR > 20dB(噪声不超限)
   ```

**易错点**：
- ⚠️ **未唤醒就开始录音** → **解决**: 确认 `--mic-array` 模式已开启
- ⚠️ **录音全是静音** → **解决**: 检查 `arecord -l` 是否能列出 XFM 设备
- ⚠️ **播放变调/2 倍速** → **解决**: 6 麦播放需用 `--mic-array` 自动 mono→stereo
- ⚠️ **唤醒词不识别** → **解决**: 默认「小飞小飞/小飞同学/芝麻开门」,自定义需到 https://www.xfyun.cn/

---

#### 步骤1：设备检测与串口唤醒（阶段一：能运行，15min）

> 本步骤对应 `asr_test.py` L84-116(`detect_xfm_devices`)与 L417-466(`--mic-array` 唤醒流程)。理解 ASR 在 6 麦阵列上启动时的硬件握手与等待。

**知识点讲解**：

**detect_xfm_devices 设备自动检测（2.1.1）**
- **原理**：`arecord -l` 输出每行形如 `card 4: XFMDPV0018 [XFM-DP-V0.0.18], device 0: USB Audio [USB Audio]`,用正则 `r'card\s+(\d+):\s+\S+\s+\[([^\]]+)\].*device\s+(\d+)'` 提取 card_num、card_name、dev_num,拼出 ALSA 设备名 `plughw:{card_num},{dev_num}`。**与 `audio_test.py` 的实现完全一致**,在 `asr_test.py` 中 L84-116 复用。
- **源码对应**:`asr_test.py` L84-116

**XfMicArray 串口唤醒（实验1已学,本实验复用）**
- **原理**：`asr_test.py --mic-array` 模式调用 `XfMicArray(vendor_id=0x1a86, product_id=0x55d4)`,与实验1的 `xf_mic_array_gui.py` 使用同一套 AIUI 协议帧解析。`set_wake_word("小飞小飞")` 通过串口写入 AIUI 协议包;`wakeup_callback` 触发时,串口接收线程解析 AIUI 唤醒事件帧,设置 `threading.Event`。
- **源码对应**:`asr_test.py` L430-466

**单次唤醒即关闭串口（设计取舍）**
- **原理**：`asr_test.py` 在检测到唤醒后立即 `mic_array_instance.stop()`(L465),这是因为：(1) 串口只负责传唤醒事件,不参与 ASR 音频流;(2) 串口的轮询会占用 CPU,可能干扰 ALSA 音频流;(3) 实验1的 `audio_test.py` 同样在 `record_only()` 唤醒后停止串口(L429)。
- **源码对应**:`asr_test.py` L463-466

**操作步骤**：

1. 查看 `asr_test.py` 的设备检测源码:
   ```bash
   grep -n -A 30 "def detect_xfm_devices" tools/asr_test.py
   # 关注 L84-116,理解 arecord -l 输出解析过程
   ```

2. 查看 `--mic-array` 模式的唤醒流程源码:
   ```bash
   grep -n -A 50 "if args.mic_array:" tools/asr_test.py | head -60
   # 关注 L417-466,理解 XfMicArray.start → wakeup_callback → mic_array.stop
   ```

3. 实际运行(暂不识别,只观察唤醒):
   ```bash
   python3 asr_test.py --mic-array --wakeup-words "小飞小飞"
   # 终端依次打印:
   #   [检测设备] 找到录音设备: plughw:4,0 (XFM-DP-V0.0.18)
   #   [串口] 已连接 (VID:0x1a86 PID:0x55d4)
   #   [唤醒词] 小飞小飞
   #   [等待唤醒] 请说唤醒词(小飞小飞)...
   #   ✓ 检测到唤醒! 开始语音识别...
   #   (之后进入主循环,按 Ctrl+C 退出)
   ```

**易错点**：
- ⚠️ **运行后立刻报"未找到讯飞麦克风阵列"** → **解决**: 重新插拔 USB,确认 `arecord -l | grep -i XFM` 能搜到设备
- ⚠️ **说唤醒词无反应** → **解决**: 距麦克风 30-50cm,正常音量;自定义唤醒词需到 https://www.xfyun.cn/ 定制后用 `--wakeup-words` 指定
- ⚠️ **唤醒后主循环无声音** → **解决**: 6 麦阵列 ALC 默认开启(`--enable-alc` 默认 True),无需手动设增益

---

#### 步骤2：音频增益与 ALC 控制（阶段二：能理解，20min）

> 本步骤对应 `asr_test.py` L123-158(`apply_capture_volume` / `apply_voice_preset`)与 `audio_mixer.py` 的 PGA + ALC 实现。理解 ASR 前的音频预处理与增益控制。

**知识点讲解**：

**XFM 6 麦阵列信号链与 PGA（实验1已学,本实验复用）**
- **原理**：XFM 6 麦阵列的麦克风信号链为 `Mic → PGA(0~+24dB) → ADC → Capture Digital(-30~+6dB) → ALSA PCM`。**PGA**(Programmable Gain Amplifier)是 XFM 内部的硬件模拟增益,SNR 最佳;**Digital** 是数字衰减/增益,会损失 SNR。`audio_mixer.py` 定义了 3 档 PGA 预设:`low=+12dB(75%)`、`normal=+18dB(88%)`、`high=+24dB(100%)`,ASR 场景推荐 `normal` 档。
- **源码对应**:`asr_test.py` L134-151  `apply_capture_volume(card, pct)` 内部调用 `AudioMixer` 拆成 `preamp_db` 与 `digital_db` 两段

**switch_input_to_mic 输入复用切换（2.1.3）**
- **原理**：XFM 6 麦阵列同时支持 Line In 与 Mic In,但**同一时刻只能选一路**。RK3576 默认通过 `amixer` 设置为 Line In,如果不切换,直接录到的是 Line 口的电平(几乎静音)。`asr_test.py` 在 `apply_voice_preset` 之前先调用 `switch_input_to_mic`(L484),把 Left/Right Line Mux 切到 MicL/MicR,才能录到 XFM 6 麦阵列上的麦克风。
- **源码对应**:`asr_test.py` L123-131  `subprocess.run(["amixer", ..., "Left Line Mux", "MicL"])`

**ALC 自动电平控制 + Noise Gate（2.1.2 进阶）**
- **原理**：ALC(Automatic Level Control)根据输入信号强度自动调节 PGA 增益,**目标**是把麦克风信号稳定在 80% 满刻度附近。`asr_test.py` 默认 `--enable-alc` 开启 ALC 并启用 Noise Gate(L501):当信号低于阈值时**静音 PGA**,防止噪声被放大;高于阈值时启用快响应 ALC 跟踪说话人距离变化。`--disable-alc` 改用固定 PGA,简单但对距离敏感。
- **源码对应**:`asr_test.py` L495-502  `mixer.set_alc(True, target_pct=80, max_pga_step=5, noise_gate=True)`

**voice-preset 一键预设**
- **原理**：`--voice-preset` 是 `audio_mixer.py` 提供的快捷配置,一键应用:mic +18dB(88% capture-volume)、ALC on(target=80%)、speaker -3dB(ASR-friendly)。`asr_test.py` 在不指定 `--capture-volume` 时默认 95%(=+22dB PGA,比 normal 更激进,L384)。
- **源码对应**:`asr_test.py` L154-158  `apply_voice_preset()`

**操作步骤**：

1. 查看增益控制源码:
   ```bash
   grep -n -A 5 "def apply_capture_volume" tools/asr_test.py
   grep -n -A 5 "def apply_voice_preset" tools/asr_test.py
   grep -n -A 5 "def switch_input_to_mic" tools/asr_test.py
   ```

2. 对比 4 种增益模式:
   ```bash
   # 模式 A:voice-preset 一键预设(推荐初次)
   python3 asr_test.py --mic-array --voice-preset
   
   # 模式 B:手动 capture-volume(95%=+22dB,默认)
   python3 asr_test.py --mic-array --capture-volume 95
   
   # 模式 C:关闭 ALC,固定 PGA(可预测但距离敏感)
   python3 asr_test.py --mic-array --disable-alc --capture-volume 88
   
   # 模式 D:最大增益(100%=+24dB)
   python3 asr_test.py --mic-array --capture-volume 100
   # 听终端日志 "Capture volume: 100% → PGA +24.0dB, digital +0.0dB"
   ```

3. 验证 ALC 是否生效(边说边看 PGA 变化):
   ```bash
   # 实时观察 PGA 寄存器
   watch -n 0.5 "amixer -c 0 sget 'Left Channel'"
   # 在另一终端启动 asr_test.py,远近移动说话,观察 PGA 是否在变
   ```

**易错点**：
- ⚠️ **录到的是 Line In 静音** → **解决**: 确认 `switch_input_to_mic` 已被调用(默认会调)
- ⚠️ **声音削波失真(爆音)** → **解决**: 调低 `--capture-volume` 到 50-75,或加 `--disable-alc` 关闭自动增益
- ⚠️ **远场(< 1m) 录不上** → **解决**: 用 `--voice-preset` 或加大 `--capture-volume` 到 100
- ⚠️ **静音时噪声被放大** → **解决**: 确认 ALC 的 Noise Gate 开启(`mixer.set_alc(..., noise_gate=True)`,L501)

---

#### 步骤3：ASR 引擎构建（阶段二：能理解，30min）

> 本步骤对应 `asr_test.py` L527-544(`OnlineRecognizer.from_transducer`)。理解 Transducer 架构、模型文件角色与 NPU 推理 provider。

**知识点讲解**：

**Transducer 三件套模型（2.2.2）**
- **原理**：sherpa-onnx 的 Zipformer-Transducer ASR 由 4 个文件组成:
  - `tokens.txt` — 词表(~5000 个 BPE token,中文场景是 CJK 字符),决定能识别的字集合
  - `encoder.rknn` — 声学编码器,把 80 维 FBank 特征转为隐状态
  - `decoder.rknn` — 语言模型解码器,基于历史 token 预测下一个 token
  - `joiner.rknn` — 联合网络,合并 encoder 与 decoder 输出得到 token 概率分布
- **源码对应**:`asr_test.py` L331-338  默认路径 `/home/iflytek/models/zipformer/*`

**OnlineRecognizer.from_transducer 构造（2.2.1）**
- **原理**：`OnlineRecognizer` 是流式识别的核心,`from_transducer` 工厂方法接收上述 4 个模型路径 + 配置参数(线程数、采样率、特征维度、解码方法、端点规则、provider),返回一个 Recognizer 实例。注意 `enable_endpoint_detection=True` 是关键开关,关闭后需外部 VAD。
- **关键参数对比表**:

  | 参数 | 默认值 | 作用 |
  |------|-------|------|
  | `num_threads` | 1 | CPU 模式下为推理线程数;RKNN 模式下为 **NPU 核心掩码**(1=自动、2/3=指定核心) |
  | `provider` | rknn | 推理后端:`rknn` 走 RK3576 NPU;`cpu` 走 CPU 通用(慢但兼容) |
  | `sample_rate` | 16000 | 必须与 wav/音频流采样率一致;`sherpa_onnx.Alsa` 内部会重采样到 16k |
  | `feature_dim` | 80 | FBank 特征维度(80 维是 Zipformer 的标准输入) |
  | `decoding_method` | greedy_search | `greedy_search` 速度快、延迟低;`modified_beam_search` 精度高、需配合热词 |

- **源码对应**:`asr_test.py` L527-544

**RKNN NPU 推理（2.2.3）**
- **原理**：RK3576 板载 6 TOPS NPU,Rockchip 把 ONNX 模型转成 `.rknn` 后可由 `librknn_rt.so` 推理,比 CPU 快 5-10 倍。`provider="rknn"` 时 sherpa-onnx 走 RKNN 后端;`provider="cpu"` 时回退到 ONNX Runtime(慢但任何平台可跑)。RKNN 模式下 `num_threads` 实际是 NPU 核心掩码,设为 0/1 表示自动调度。
- **源码对应**:`asr_test.py` L345-349

**操作步骤**：

1. 查看模型构建源码:
   ```bash
   sed -n '527,545p' tools/asr_test.py
   # 观察 OnlineRecognizer.from_transducer 的所有参数
   ```

2. 验证模型文件存在:
   ```bash
   ls -la /home/iflytek/models/zipformer/
   # 期望:encoder.rknn  decoder.rknn  joiner.rknn  tokens.txt
   # 若不存在,需从 https://k2-fsa.github.io/sherpa/onnx/pretrained_models/index.html 下载
   #   或本地转 RKNN: rknn-toolkit2 convert encoder.onnx → encoder.rknn
   ```

3. 切换 provider 实测:
   ```bash
   # RKNN(NPU,快)
   time python3 asr_test.py --mic-array --provider rknn --audio-file test.wav
   # CPU(慢但兼容)
   time python3 asr_test.py --mic-array --provider cpu --audio-file test.wav
   # 对比:CPU 模式通常慢 3-5 倍
   ```

4. 切换解码方法:
   ```bash
   # greedy(快,但不支持热词)
   python3 asr_test.py --mic-array --decoding-method greedy_search
   # modified_beam_search(支持热词,慢 20-30%)
   python3 asr_test.py --mic-array --decoding-method modified_beam_search --hotwords-file hotwords.txt
   ```

**易错点**：
- ⚠️ **`encoder.rknn not found`** → **解决**: 检查路径,或从 HuggingFace 下载 sherpa-onnx-zipformer-zh-14M 并转 RKNN
- ⚠️ **provider=rknn 报 `librknn_rt.so not found`** → **解决**: 安装 rknn-toolkit2-lite(apt install rknn-toolkit2-lite)
- ⚠️ **CPU 模式太慢卡顿** → **解决**: 用 RKNN NPU 模式;或减小 num_threads(实测 RKNN 设 2 比设 4 快)
- ⚠️ **热词文件不生效** → **解决**: 必须用 `--decoding-method modified_beam_search`,默认 greedy_search 会忽略 hotwords

---

#### 步骤4：流式识别主循环（阶段三：能改造，30min）

> 本步骤对应 `asr_test.py` L578-643(主循环)。理解 ASR 流式识别的核心节奏:`alsa.read → accept_waveform → decode_stream → is_endpoint → reset`。

**知识点讲解**：

**100ms 块读取节奏（2.5.2）**
- **原理**：`samples_per_read = int(0.1 * sample_rate) = 1600` 帧(L578)。**为什么是 100ms?**
  - **延迟**: 100ms 是人耳可接受的"说话-响应"间隔上限;再大会觉得卡顿
  - **吞吐**: 100ms ≈ 1600 帧 × 4byte(float32) = 6.4KB/次,read 系统调用开销可忽略
  - **CPU**: 每次 100ms 块触发一次 decode_stream,在 RKNN 上推理约 20-30ms,有 70ms 空闲给其他任务
- **源码对应**:`asr_test.py` L578-579  `samples_per_read = int(0.1 * sample_rate)`

**accept_waveform + is_ready 循环解码（2.3.1, 2.3.2）**
- **原理**：流式识别的两步组合拳:
  - `stream.accept_waveform(sr, samples)` — 把 100ms 音频块 push 到 stream 的内部 buffer
  - `while recognizer.is_ready(stream): recognizer.decode_stream(stream)` — 当 buffer 累积到能跑一次推理(通常是 1-2 个 chunk),连续 decode 直到不够
- **设计意图**: 不强制每 100ms 触发一次推理,而是按"模型可吃"的最优块大小调度,提升吞吐
- **源码对应**:`asr_test.py` L601-603

**is_endpoint + reset 端点处理（2.3.3）**
- **原理**：`is_endpoint()` 是 sherpa-onnx 内置的端点检测器,综合 3 条规则判断用户是否说完了。**端点触发后必须 reset**:
  - `recognizer.reset(stream)` — 重置 stream 的状态(但不释放底层 buffer)
  - `stream = recognizer.create_stream()` — 重建 stream 实例
  - 设计意图:**保留时序上下文**(reset 不丢历史)但**避免长时状态累积**(create_stream 释放张量)
- **源码对应**:`asr_test.py` L613-629
- **代码片段**:
  ```python
  is_endpoint = recognizer.is_endpoint(stream)
  result = recognizer.get_result(stream)
  if result and (last_result != result):
      last_result = result
      print(f"\r{segment_id}:{result}", end="", flush=True)  # 实时部分结果
  if is_endpoint:
      final = result if result else last_result
      if final:
          print(f"\r{segment_id}:{final}", flush=True)  # 端点时打印完整结果
          segment_id += 1
      last_result = ""
      recognizer.reset(stream)
      stream = recognizer.create_stream()  # 重建 stream
  ```

**single-stream 复用 vs 重建（2.5.1）**
- **原理**：Zipformer 是 RNN-like 模型,内部维护时序状态。如果每次说完都销毁 Recognizer,会丢失历史状态导致**长会话中识别准确率下降**。`asr_test.py` 采用的折中:Recognizer 单例 + 端点时 reset stream + 重建 stream(只丢当前段的历史)。这与 RK3588 版本的 `asr.py` 模式一致(L627-628 注释明确说明)。
- **源码对应**:`asr_test.py` L591-629

**操作步骤**：

1. 查看主循环源码:
   ```bash
   sed -n '578,643p' tools/asr_test.py
   # 重点关注:while running、alsa.read、accept_waveform、decode_stream、is_endpoint、reset
   ```

2. 跑一个完整会话观察日志:
   ```bash
   python3 asr_test.py --mic-array --voice-preset
   # 说"小飞小飞"唤醒 → 看到 "✓ 检测到唤醒"
   # 说"今天天气真好" → 看到 0:今天天气真好(实时)
   # 停顿 1.5s → 看到端点换行,segment_id 变 1
   # 说"我们出去玩吧" → 看到 1:我们出去玩吧
   # Ctrl+C → Done.
   ```

3. **最小可运行 demo:30 行流式识别**(原理验证,无 6 麦阵列):
   ```python
   # demo_asr_minimal.py
   import sherpa_onnx, sounddevice as sd, numpy as np

   rec = sherpa_onnx.OnlineRecognizer.from_transducer(
       tokens="/home/iflytek/models/zipformer/tokens.txt",
       encoder="/home/iflytek/models/zipformer/encoder.rknn",
       decoder="/home/iflytek/models/zipformer/decoder.rknn",
       joiner="/home/iflytek/models/zipformer/joiner.rknn",
       num_threads=1, provider="cpu",  # demo 阶段用 CPU 兼容性最好
   )
   stream = rec.create_stream()
   alsa = sherpa_onnx.Alsa("plughw:1,0")  # 板载麦
   sr = 16000
   print("请说话...")
   while True:
       samples = alsa.read(int(0.1 * sr))  # 100ms 块
       stream.accept_waveform(sr, samples)
       while rec.is_ready(stream):
           rec.decode_stream(stream)
       text = rec.get_result(stream)
       if text:
           print(f"\r实时: {text}", end="", flush=True)
       if rec.is_endpoint(stream):
           print(f"\r端点: {text}")
           rec.reset(stream)
           stream = rec.create_stream()
   ```

4. 修改 demo 测不同块大小对延迟的影响:
   ```python
   # 把 samples_per_read 改成 50ms / 200ms,观察 print 更新频率与 CPU 占用
   for chunk_ms in [50, 100, 200]:
       samples_per_read = int(chunk_ms / 1000 * sr)
       # 测 5 秒,记录 print 次数与平均延迟
   ```

**易错点**：
- ⚠️ **识别文本一直不变** → **解决**: 确认 `last_result != result` 判断,否则部分结果更新被吞掉
- ⚠️ **端点反复触发(空 segment)** → **解决**: 检查 rule2_min_trailing_silence 是否过小(默认 1.5s,调到 2.0-3.0s)
- ⚠️ **长时间运行后识别变差** → **解决**: 端点 reset + create_stream 是必要的(L627-628);不能只 reset 不 create
- ⚠️ **CPU 占用 100%** → **解决**: RKNN 模式 + num_threads=1(默认);避免在主循环加 sleep

---

#### 步骤5：端点检测调优（阶段三：能改造，30min）

> 本步骤对应 `asr_test.py` L361-370(参数定义)与内置端点检测器。理解 3 条端点规则的协同,以及 `blank_penalty` 对尾字的影响。

**知识点讲解**：

**rule1_min_trailing_silence 长时间静音触发（2.3.3）**
- **原理**:`rule1` 是兜底规则:当用户说话**没结果**(尚未识别出任何 token)且持续静音 N 秒,认为用户放弃了说话,触发端点。`asr_test.py` 默认 **4.5s**(L362-364)。**调小**(如 2.0s):响应快,但容易在用户思考停顿时切断;**调大**(如 8.0s):容错好,但用户放弃后等很久。
- **源码对应**:`asr_test.py` L362-364

**rule2_min_trailing_silence 已有结果时静音触发**
- **原理**:`rule2` 是主规则:当用户**已经说出部分内容**(非空 result)且静音 N 秒,认为用户说完了。`asr_test.py` 默认 **1.5s**(L365-367)。**平衡考量**:
  - 1.0s — 响应快,但句尾稍长停顿会被切(如"你好小飞...同学"中间的停顿)
  - 1.5s — 推荐(经验值,适合 90% 中文场景)
  - 2.0-3.0s — 长句、容错,但响应慢
- **源码对应**:`asr_test.py` L365-367

**rule3_min_utterance_length 最小语句长度**
- **原理**:`rule3` 是反误触规则:即使满足 rule1/rule2,如果总语句长度 < N 秒,也不触发端点(避免把"嗯"等语气词当一句话)。`asr_test.py` 默认 **300s**(L368-370),**实际上禁用**了这条规则,仅靠 rule1/rule2 工作。
- **源码对应**:`asr_test.py` L368-370

**blank_penalty 空符号惩罚（2.3.4）**
- **原理**：Transducer 解码时,每一步预测"空符号(blank)"或"实际 token"。`blank_penalty` 调整空符号的偏置:
  - **默认值 0.25**(L357-359):**正向偏置**空符号,模型倾向"不说话",**减少插入错误**
  - **= 0.0**:关闭偏置
  - **< 0**(如 -0.5):负向偏置空符号,模型倾向"说点啥",**减少漏字**(但增加插入)
- **源码对应**:`asr_test.py` L357-359
- **调试经验值**:
  | 现象 | 调整方向 |
  |------|---------|
  | 重复字/插入字多(如"今今今天") | 增大 blank_penalty 到 0.5-1.0 |
  | 尾字丢失(如"小飞同"→"小飞") | 减小 blank_penalty 到 0.0 或 -0.3 |
  | 句子短(识别到一半就出端点) | 调大 rule2_min_trailing_silence |

**操作步骤**：

1. 查看端点参数定义:
   ```bash
   sed -n '361,371p' tools/asr_test.py
   # rule1/rule2/rule3 三个参数的定义
   ```

2. **A/B 测试 rule2**(推荐 1.5s vs 2.5s 对比):
   ```bash
   # 激进端点(响应快)
   python3 asr_test.py --mic-array --rule2-min-trailing-silence 1.0
   # 观察:说"今天天气真好"中间停顿 0.5s,是否被切断
   
   # 保守端点(容错好)
   python3 asr_test.py --mic-array --rule2-min-trailing-silence 3.0
   # 观察:说"今天天气真好"(中间可能停顿),能否完整识别
   ```

3. **A/B 测试 blank_penalty**:
   ```bash
   # 高 blank_penalty(0.5) — 防重复字
   python3 asr_test.py --mic-array --blank-penalty 0.5
   # 故意说"今今天天"重复字,看是否被正确识别为"今天"
   
   # 零 blank_penalty(0.0) — 减少漏字
   python3 asr_test.py --mic-array --blank-penalty 0.0
   # 故意说长句看尾字是否被吞
   ```

4. **绘制 rule1/rule2/blank_penalty 三参数扫描表**:
   ```python
   # 在终端开 3 个 tab,分别跑:
   # tab1: python3 asr_test.py --mic-array --rule1-min-trailing-silence 2.0
   # tab2: python3 asr_test.py --mic-array --rule2-min-trailing-silence 2.5
   # tab3: python3 asr_test.py --mic-array --blank-penalty 0.0
   # 同一句话测试 5 次,记录:响应延迟/尾字完整度/插入字
   ```

**易错点**：
- ⚠️ **每句话都被切成两半** → **解决**: 调大 rule2_min_trailing_silence 到 2.0-3.0s
- ⚠️ **说"小飞小飞"唤醒词也被当 ASR 识别** → **解决**: rule1_min_trailing_silence 调到 3.0-5.0s,或启用 hotwords
- ⚠️ **尾字"同学"被识别成"同"** → **解决**: 减小 blank_penalty 到 0.0(默认 0.25 对长句尾字有损失)

---

#### 步骤6：热词与解码策略（阶段三：能改造，20min）

> 本步骤对应 `asr_test.py` L376-380(热词参数)与 `hotwords.txt`。理解热词文件格式、解码方法选择与"小飞"→"小飞机"类误识别的解决方案。

**知识点讲解**：

**hotwords.txt 格式（2.4.1）**
- **原理**：每行一个热词短语,token 之间用空格分隔。中文 token 来自 tokens.txt(CJK 单字),所以"小飞"对应"小 飞"。`hotwords.txt` 示例(项目根目录):
  ```
  小 飞
  小 飞 同 学
  你 好 小 飞
  请 把 东 西 搬 运 到 停 放 点
  停 放 点
  搬 运
  ```
- **源码对应**:`asr_test.py` L376-380  `parser.add_argument("--hotwords-file", ...)`

**hotwords_score 热词偏置强度**
- **原理**:`hotwords_score` 是热词在 beam search 中的额外加分(per token):
  - **= 0**:关闭热词(等同于不传 hotwords-file)
  - **= 1.0**:温和偏置(推荐)
  - **= 2.0**(默认 L379):强偏置,几乎"必识别"
  - **= 5.0+**:过度偏置,可能把非热词也识别成热词
- **源码对应**:`asr_test.py` L379-380

**decoding_method 与热词的关系（2.4.2, 2.4.3）**
- **原理**:**热词只在 `modified_beam_search` 下生效**;`greedy_search` 没有 beam 概念,热词文件被忽略(L354-356 注释明确说明)。如果必须用热词,必须切换解码方法,代价是推理慢 20-30%。
- **对比表**:
  | 解码方法 | 速度 | 精度 | 支持热词 | 支持 partial result |
  |---------|------|------|---------|------------------|
  | `greedy_search` | ⭐⭐⭐ | ⭐⭐ | ❌ | 部分 |
  | `modified_beam_search` | ⭐⭐ | ⭐⭐⭐ | ✅ | 频繁(每步都更新) |

- **源码对应**:`asr_test.py` L353-356

**"小飞" → "小飞机" 类误识别的解决**
- **现象**：ASR 模型训练语料中"小飞同学"出现频次低于"小飞机",模型倾向把"小飞同..."识别为"小飞机..."
- **解决方案**:
  1. **加 hotword**:`hotwords.txt` 写入"小 飞 同 学" + `hotwords_score=2.0`
  2. **切换 decoding_method**:`--decoding-method modified_beam_search`(必做,否则热词不生效)
  3. **小调 blank_penalty**:对"小飞同"这种短音节,适当减小到 0.0 可减少尾字丢失

**操作步骤**：

1. 查看默认 hotwords.txt:
   ```bash
   cat tools/hotwords.txt
   # 6 行:小 飞 / 小 飞 同 学 / 你 好 小 飞 / 请 把 东 西 搬 运 到 停 放 点 / 停 放 点 / 搬 运
   ```

2. 跑无热词基线:
   ```bash
   # 用 --hotwords-file "" 关闭热词
   python3 asr_test.py --mic-array --hotwords-file ""
   # 故意说"小飞同学",听是否被识别成"小飞机"
   ```

3. 启用热词+modified_beam_search:
   ```bash
   python3 asr_test.py --mic-array \
     --decoding-method modified_beam_search \
     --hotwords-file tools/hotwords.txt \
     --hotwords-score 2.0
   # 同样说"小飞同学",听是否被正确识别
   ```

4. 自定义热词(增加"前进/后退/左转"等机器人命令):
   ```bash
   cat > my_hotwords.txt <<EOF
   前 进
   后 退
   左 转
   右 转
   停 下
   打 开 灯
   关 闭 灯
   EOF
   
   python3 asr_test.py --mic-array \
     --decoding-method modified_beam_search \
     --hotwords-file my_hotwords.txt
   # 测试"前进一米"是否被准确识别
   ```

**易错点**：
- ⚠️ **加了 hotwords.txt 但没生效** → **解决**: 检查 `decoding_method` 是否是 `modified_beam_search`,默认是 `greedy_search` 会忽略
- ⚠️ **热词过度偏置,所有都识别成热词** → **解决**: 调低 `hotwords_score` 到 1.0
- ⚠️ **hotwords.txt 格式错(用了中文逗号)** → **解决**: 每行 token 间用**半角空格**分隔,**不能**用中文逗号
- ⚠️ **modified_beam_search 太慢** → **解决**: 减小 num_threads=1(默认);或回到 greedy_search + 不用热词

---

#### 步骤7：业务集成与命令词解析（阶段三：能改造，20min）

> 本步骤对应将 asr_test.py 识别结果集成到机器人命令解析。理解 ASR 输出文本 → 意图识别 → 动作映射的完整链路。

**知识点讲解**：

**ASR 输出结构**
- **原理**:`stream.result.text` 返回的是已识别的字符串(已去除前后空白)。每个端点触发时,**当前 segment 的完整文本**可通过 `recognizer.get_result(stream)` 取出,然后调用 `reset()` 准备下一个 segment。
- **源码对应**:`asr_test.py` L606  `result = recognizer.get_result(stream)`

**命令词解析（Command Parsing）**
- **原理**：将 ASR 文本映射到机器人动作有两种典型方法:
  - **关键词匹配**(简单场景):`if "前进" in text: move_forward()` — 适合固定命令集
  - **意图分类**(复杂场景):用小模型/NLU 分类"前进/后退/左转/..."意图 — 适合开放指令
- **设计模式**:用状态机控制互斥(详见实验5端到端对话),ASR 节点只在 `LISTENING` 状态下激活

**与 ROS2 集成(扩展任务)**
- **原理**:`asr_test.py` 当前是独立 CLI 工具,要集成到 ROS2 需:
  1. 改为 ROS2 节点(`rclpy.Node` 子类)
  2. 订阅 `/interaction/wake_word/detected`(Bool)触发识别
  3. 发布 `/interaction/asr/text`(String)到下游命令解析
- **当前状态**:`car1_speech/asr_node.py` 是 TODO 占位,实验2 demo 直接调用 `asr_test.py` 的 API,集成封装留作实验5

**操作步骤**：

1. 命令词映射 demo:
   ```python
   # demo_command_parser.py
   COMMAND_MAP = {
       "前进": "move_forward",
       "后退": "move_backward",
       "左转": "turn_left",
       "右转": "turn_right",
       "停下": "stop",
       "打开灯": "light_on",
       "关闭灯": "light_off",
   }
   
   def parse_command(text: str) -> str | None:
       for cmd, action in COMMAND_MAP.items():
           if cmd in text:
               return action
       return None
   
   # 集成到 asr_test.py:在端点处理处加一行
   # if is_endpoint:
   #     final = result if result else last_result
   #     action = parse_command(final) if final else None
   #     print(f"\r{segment_id}:{final} → action={action}", flush=True)
   ```

2. 端到端测试(语音→动作):
   ```bash
   # 启动 asr_test.py(假设已集成命令词解析)
   python3 asr_test.py --mic-array --hotwords-file my_hotwords.txt
   # 唤醒:小飞小飞
   # 说话:前进一米
   # 终端打印:0:前进一米 → action=move_forward
   # (实际机器人动作由实验5的状态机驱动)
   ```

3. **完整 demo_asr_segment.py:批量评估(20 条命令 WER)**:
   ```python
   # -*- coding: utf-8 -*-
   """
   实验2 完整 demo:用 asr_test.py 的 API 批量评估 20 条中文命令的 WER
   """
   import sherpa_onnx, soundfile as sf, csv
   from pathlib import Path
   
   def load_recognizer():
       return sherpa_onnx.OnlineRecognizer.from_transducer(
           tokens="/home/iflytek/models/zipformer/tokens.txt",
           encoder="/home/iflytek/models/zipformer/encoder.rknn",
           decoder="/home/iflytek/models/zipformer/decoder.rknn",
           joiner="/home/iflytek/models/zipformer/joiner.rknn",
           num_threads=1, provider="rknn",
       )
   
   def recognize_file(rec, wav_path):
       audio, sr = sf.read(str(wav_path), dtype="float32")
       stream = rec.create_stream()
       chunk = int(0.1 * sr)
       for i in range(0, len(audio), chunk):
           stream.accept_waveform(sr, audio[i:i+chunk])
           while rec.is_ready(stream):
               rec.decode_stream(stream)
       # 尾静音
       stream.accept_waveform(sr, [0.0] * int(0.5 * sr))
       stream.input_finished()
       while rec.is_ready(stream):
           rec.decode_stream(stream)
       return stream.result.text.strip()
   
   def compute_wer(ref: str, hyp: str) -> tuple:
       """简单字级编辑距离:返回 (S, D, I, N)"""
       ref_chars = list(ref.replace(" ", ""))
       hyp_chars = list(hyp.replace(" ", ""))
       n = len(ref_chars)
       if n == 0:
           return (0, 0, len(hyp_chars), 0)
       dp = [[0] * (len(hyp_chars) + 1) for _ in range(n + 1)]
       for i in range(n + 1): dp[i][0] = i
       for j in range(len(hyp_chars) + 1): dp[0][j] = j
       for i in range(1, n + 1):
           for j in range(1, len(hyp_chars) + 1):
               if ref_chars[i-1] == hyp_chars[j-1]:
                   dp[i][j] = dp[i-1][j-1]
               else:
                   dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
       # 简化:S+D+I = dp[n][m]
       return (0, 0, dp[n][len(hyp_chars)], n)
   
   if __name__ == "__main__":
       rec = load_recognizer()
       corpus = Path("test_corpus")
       results = []
       with open(corpus / "ref.txt", encoding="utf-8") as f:
           refs = [line.strip().split(maxsplit=1) for line in f if line.strip()]
       for wav_name, ref_text in refs:
           hyp = recognize_file(rec, corpus / wav_name)
           s, d, i, n = compute_wer(ref_text, hyp)
           wer = (s + d + i) / n if n else 0
           results.append((wav_name, ref_text, hyp, wer))
           print(f"[{wav_name}] ref={ref_text!r} hyp={hyp!r} WER={wer:.2%}")
       with open(corpus / "result.csv", "w", newline="", encoding="utf-8") as f:
           w = csv.writer(f)
           w.writerow(["wav", "ref", "hyp", "wer"])
           w.writerows(results)
       avg_wer = sum(r[3] for r in results) / len(results)
       print(f"\n[OK] 平均 WER = {avg_wer:.2%}  共 {len(results)} 条")
   ```

**易错点**：
- ⚠️ **命令词没匹配上** → **解决**: 在 `parse_command` 中打印 `text`,确认是 ASR 识别错误还是命令词不全
- ⚠️ **唤醒词也被解析成命令** → **解决**: 在 parse 前过滤掉"小飞小飞/小飞同学"等唤醒词
- ⚠️ **ASR 与 TTS 同时占用音频设备** → **解决**: 状态机控制互斥(详见实验5)

### 2.7 注意事项

- ⚠️ **asr_test.py 是 CLI 工具,非 ROS2 节点** → 业务集成需自行封装为 `rclpy.Node` 子类
- ⚠️ **6 麦阵列唤醒后必须关闭串口** → 否则串口轮询会干扰 ALSA 音频流(L465)
- ⚠️ **端点检测参数需根据场景调优** → 命令词 1.0-1.5s,对话 2.0-3.0s
- ⚠️ **热词必须配合 modified_beam_search** → 默认 greedy_search 会忽略 hotwords 文件
- ⚠️ **长时间运行需 reset stream** → 否则状态累积导致识别变差(L627-628)
- ⚠️ **RKNN 模式下 num_threads 是 NPU 核心掩码** → 与 CPU 模式语义不同(L349)

### 2.8 实验总结

**完成成果**:
- 拆解 asr_test.py 7 个核心模块(设备检测/唤醒/增益/引擎/流式循环/端点/热词)
- 跑通 `python3 asr_test.py --mic-array` 完整流程
- 调优 rule1/rule2/rule3 端点检测参数
- 配置 hotwords.txt 解决"小飞"→"小飞机"类误识别
- 集成命令词解析实现语音→动作链路

**技能收获**:
- 掌握 sherpa-onnx 流式 ASR 的代码结构(Transducer/OnlineRecognizer/Alsa)
- 理解 6 麦阵列在 ASR 中的角色(唤醒+增益)
- 学会 A/B 测试调优端点参数与热词偏置
- 掌握"reset+create_stream"模式保留时序上下文

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 唤醒词不识别 | 距麦太远/发音不准 | 30-50cm,正常音量;自定义到 xfyun.cn 定制 |
| 端点反复触发(空 segment) | rule2 太小 | 调到 2.0-3.0s |
| 尾字丢失 | blank_penalty 偏置过强 | 调到 0.0 或 -0.3 |
| 重复字/插入字 | blank_penalty 不足 | 调到 0.5-1.0 |
| 热词不生效 | decoding_method=greedy | 改 modified_beam_search |
| 长时间识别变差 | 未 reset stream | 端点时 reset + create_stream |
| 录音全静音 | Line/Mic 输入未切换 | 确认 switch_input_to_mic 已被调用 |

### 2.9 实验报告要求

**思考题**:
1. sherpa-onnx 的 Transducer 架构中,encoder/decoder/joiner 各自的输入输出是什么?为什么要分三件套而不是一个端到端模型?
2. rule1/rule2/rule3 三条端点规则分别解决什么场景?为什么默认 rule3_min_utterance_length 设到 300s(几乎禁用)?
3. blank_penalty 是如何影响解码结果的?对"小飞"和"小飞机"两个候选 token,blank_penalty=0.25 与 =0.0 时的概率分布有什么不同?
4. 为什么 RKNN 模式下 num_threads=1 是 NPU 核心掩码,而不是 CPU 模式下的线程数?RK3576 有几个 NPU 核心?
5. 长时间运行(>30 分钟)的 ASR 会话中,为什么"reset+create_stream"比"只 reset"或"只 create_stream"都好?

**评分标准**: 设备检测与唤醒 15 分 + 增益与 ALC 15 分 + 引擎构建 20 分 + 流式主循环 20 分 + 端点调优 15 分 + 热词配置 10 分 + 实验报告 5 分 = 100 分。
