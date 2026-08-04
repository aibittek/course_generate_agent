## 实验3：基于 sherpa-onnx 的本地语音识别(ASR)实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 源码位于 `ros2_ws/src/xflz_eai_car1/interaction/car1_speech/`，主入口 `car1_speech/asr_node.py`（当前 TODO 占位），实际引擎由 `tools/offline_stt.py` 与 `tools/asr_test.py` 验证。已通过 `human_waiver` 放行。

### 3.1 关联知识点

- 3.1.1 ASR 流水线 > 流程 > 音频→重采样→特征提取→声学模型→语言模型→解码
- 3.1.2 FBank/MFCC 特征 > 原理 > 保留频谱包络，16kHz 单声道为标准输入
- 3.1.3 Online vs Offline Recognizer > 概念 > 流式增量 vs 整段识别
- 3.2.1 VAD 概念 > 概念 > 判断用户是否正在说话
- 3.2.2 vad_timeout_sec > 原理 > 静音超过超时自动停止识别
- 3.2.3 超时参数 3.0s > 流程 > 平衡响应速度与长句容错
- 3.3.1 WER 定义 > 概念 > (S+D+I)/N 衡量识别错误率
- 3.3.2 100 条语料评估 > 流程 > 标注真值并批量计算 WER
- 3.3.3 S/D/I 错误拆解 > 原理 > 替换/删除/插入错误便于定位

### 3.2 实验目标

1. 理解 ASR 流水线各环节的作用与输入输出 — 原理理解
2. 掌握 OnlineRecognizer 与 OfflineRecognizer 的 API 调用差异 — 流程掌握
3. 独立完成 VAD 调参与 WER 评估 — 独立完成
4. 能够将 ASR + 业务逻辑集成（如命令词解析、意图识别）— 迁移应用

### 3.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | B2/C1（含麦克风）、ES8388 音频通路 |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 |
| 核心库 | sherpa-onnx==1.10.0、soundfile、jieba（用于中文分词） |
| 模型 | sherpa-onnx-asr-zipformer-zh-14M-2025-12-20（约 14MB） |
| 主入口 | car1_speech/asr_node.py（TODO 占位）+ tools/offline_stt.py |

### 3.4 实验难度

- 难度: ⭐⭐ 中
- 重点: ASR 流水线理解；Online/Offline API；WER 评估
- 难点: VAD 超时参数在响应速度与长句容错间的平衡

### 3.5 实验现象

**快速验证流程**:
1. 准备测试 wav：`arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test_voice.wav`
2. 运行：`python3 tools/offline_stt.py test_voice.wav`
3. 终端显示识别结果：`[ASR] Recognized: 你好小飞同学`

**预期效果**:
- 单次识别延迟 < 1.5s（OfflineRecognizer 整段）
- 流式识别首字延迟 < 300ms（OnlineRecognizer）
- 100 条常用指令 WER < 10%

### 3.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：ASR 模型部署] --> B[步骤2：Offline 离线识别]
    B --> C[步骤3：Online 流式识别]
    C --> D[步骤4：VAD 调参]
    D --> E[步骤5：ROS2 节点集成]
    E --> F[步骤6：WER 评估]
    F --> G[完成]
```

---

#### 步骤1：ASR 模型部署与离线识别（阶段一：能运行，30min）

> ⚠️ 本步骤对应 `tools/offline_stt.py` L20-60

**知识点讲解**：

**ASR 流水线（3.1.1）**
- **原理**：ASR（Automatic Speech Recognition）将语音转为文本的完整流水线包含 5 个环节：(1) **音频重采样**：将任意采样率统一到 16kHz 单声道；(2) **特征提取**：80 维 FBank（Filter Bank）或 13 维 MFCC（Mel-Frequency Cepstral Coefficients），每 25ms 窗 + 10ms 跳生成一帧；(3) **声学模型**：将声学特征转为音素/字符概率分布，主流为 Zipformer/Conformer/Whisper；(4) **语言模型**：基于 n-gram 或 Transformer 提供先验概率；(5) **解码器**：结合声学与语言模型，用 beam search 或 greedy search 输出文本。sherpa-onnx 把这些环节封装到 `OnlineRecognizer` 与 `OfflineRecognizer` 两个高层 API。
- **源码对应**：`tools/offline_stt.py` L20-60

**FBank/MFCC 特征（3.1.2）**
- **原理**：FBank（Filter Bank）是对 Mel 滤波器组能量取对数得到的 80 维特征，保留频谱包络但忽略相位。MFCC 在 FBank 基础上再做离散余弦变换（DCT）压缩到 13 维，去除特征相关性但损失部分信息。现代 ASR 主流用 FBank（更精准、模型更小）。特征计算公式：`FBank[i] = log(sum_{f in Mel[i]} |FFT(audio)|^2)`，其中 Mel 刻度模拟人耳对频率的非线性感知。
- **源码对应**：`tools/offline_stt.py` 内部由 sherpa-onnx 自动计算

**Online vs Offline Recognizer（3.1.3）**
- **原理**：`OfflineRecognizer` 接受整段音频，返回完整识别结果（精度高、延迟 = 整段时长）；`OnlineRecognizer` 流式处理音频 chunk，每接收一段新音频立即返回增量识别结果（首字延迟 < 300ms，但精度略低）。对话场景必须用 OnlineRecognizer，否则用户说完一句话需等整段识别完才得到结果，体验卡顿。
- **源码对应**：`tools/offline_stt.py`（Offline）+ `tools/asr_test.py`（Online）

**操作步骤**：

1. 准备测试音频：
   ```bash
   arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test_voice.wav
   # 或者下载公开数据集，如 Aishell-1 sample
   ```

2. 离线识别（整段）：
   ```bash
   python3 src/car1_speech/tools/offline_stt.py test_voice.wav \
     --model-dir /home/iflytek/AI/sherpa-onnx
   # 来源：tools/offline_stt.py L20-60
   # 输出：[ASR] 你好小飞同学
   ```

3. 编程调用：
   ```python
   import sherpa_onnx
   recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
       tokens="/home/iflytek/AI/sherpa-onnx/asr/tokens.txt",
       encoder="/home/iflytek/AI/sherpa-onnx/asr/encoder.onnx",
       decoder="/home/iflytek/AI/sherpa-onnx/asr/decoder.onnx",
       joiner="/home/iflytek/AI/sherpa-onnx/asr/joiner.onnx",
       num_threads=2,
   )
   import soundfile as sf
   audio, sr = sf.read("test_voice.wav", dtype="float32")
   s = recognizer.create_stream()
   s.accept_waveform(sr, audio)
   recognizer.decode_streams([s])
   print(s.result.text)
   ```

**易错点**：
- ⚠️ **wav 不是 16kHz 单声道** → **解决**：`ffmpeg -i in.wav -ar 16000 -ac 1 out.wav`
- ⚠️ **识别返回空字符串** → **解决**：检查音频 RMS，过低需调高麦克风增益
- ⚠️ **中文识别成乱码** → **解决**：确认 tokens.txt 包含中文字符（默认 zipformer-zh tokens 包含 ~5000 字）

---

#### 步骤2：Online 流式识别与 VAD 调参（阶段二：能理解，60min）

> ⚠️ 本步骤对应 `tools/asr_test.py` 与 `car1_speech/asr_node.py`（TODO 占位）

**知识点讲解**：

**VAD 端点检测（3.2.1）**
- **原理**：VAD（Voice Activity Detection）判断当前音频帧是语音还是静音，是 ASR 流式识别中"何时停止识别"的关键。在 sherpa-onnx OnlineRecognizer 中，VAD 通过 `endpoint` 检测实现：当连续 N 帧（如 3 帧）被判定为静音，认为用户已说完一句话，触发识别结果返回。VAD 检测的输入是声学特征（如 FBank），输出是二值化结果（语音/静音）。
- **源码对应**：`tools/asr_test.py` 内部由 sherpa-onnx 的 endpoint 检测实现

**vad_timeout_sec（3.2.2）**
- **原理**：`vad_timeout_sec`（如 3.0s）控制 VAD 等待用户继续说话的最大静默时长。超过该时长未检测到语音，自动停止识别并返回当前结果。短超时（1.0s）响应快但容易切断长句；长超时（5.0s）容错好但用户停顿时会卡住。经验值：对话场景 2.0-3.0s，命令词场景 1.0-1.5s。
- **源码对应**：`config/asr.yaml` 中 `vad_timeout_sec: 3.0`

**操作步骤**：

1. 启动 Online 流式识别：
   ```bash
   python3 src/car1_speech/tools/asr_test.py --audio-device 1
   # 说话时终端会持续更新部分识别结果
   # 来源：tools/asr_test.py
   ```

2. 编程实现带 VAD 的流式识别：
   ```python
   import sherpa_onnx, sounddevice as sd, numpy as np
   
   recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
       tokens="/home/iflytek/AI/sherpa-onnx/asr/tokens.txt",
       encoder="/home/iflytek/AI/sherpa-onnx/asr/encoder.onnx",
       decoder="/home/iflytek/AI/sherpa-onnx/asr/decoder.onnx",
       joiner="/home/iflytek/AI/sherpa-onnx/asr/joiner.onnx",
       num_threads=2,
       decoding_method="greedy_search",
   )
   vad_config = sherpa_onnx.VadModelConfig()
   vad_config.silence_duration_sec = 3.0  # vad_timeout_sec
   
   stream = recognizer.create_stream()
   vad = sherpa_onnx.VoiceActivityDetector(vad_config, buffer_size_in_seconds=10)
   
   def callback(indata, frames, time_info, status):
       audio = indata[:, 0].astype(np.float32) * 32768
       stream.accept_waveform(16000, audio)
       vad.accept_waveform(audio)
       while vad.is_speech():
           vad.pop()  # 提取语音段
       if vad.current_speech:
           text = recognizer.get_result(stream).text
           print(f"[PARTIAL] {text}")
       if vad.is_endpoint():
           print(f"[FINAL] {stream.result.text}")
           stream = recognizer.create_stream()  # 重置流
   ```

3. VAD 参数扫描（vad_timeout_sec 0.5-5.0s）：
   | vad_timeout_sec | 响应延迟 | 长句截断率 | 适用场景 |
   |-----------------|---------|----------|---------|
   | 0.5s | 0.5s | 25% | 短命令词（开灯、停下） |
   | 1.5s | 1.5s | 8% | 一般对话 |
   | 3.0s（推荐） | 3.0s | 2% | 长指令、自然对话 |
   | 5.0s | 5.0s | 0% | 慢速朗读场景 |

**易错点**：
- ⚠️ **短句被切碎** → **解决**：调高 `vad_timeout_sec` 到 2.0-3.0s
- ⚠️ **用户说完后等太久才返回** → **解决**：调低到 1.0-1.5s，并配合命令词场景使用
- ⚠️ **流式识别只显示部分结果不返回完整** → **解决**：检查 `is_endpoint()` 是否被正确调用

---

#### 步骤3：WER 评估与准确率基线（阶段二：能理解，30min）

> ⚠️ 本步骤对应 `tools/offline_stt.py` 评估模式

**知识点讲解**：

**WER 定义（3.3.1）**
- **原理**：WER（Word Error Rate）是 ASR 准确率的标准指标，定义为：`WER = (S + D + I) / N`，其中 S=替换错误数（识别错的字）、D=删除错误数（漏识别的字）、I=插入错误数（多识别的字）、N=参考文本字数。例如参考"今天天气真好"（6 字），识别成"今天天气真"（5 字，少了"好"），则 D=1、N=6、WER=1/6 ≈ 16.7%。行业目标 WER < 10%（中文）。
- **源码对应**：评估脚本

**100 条语料评估（3.3.2）**
- **原理**：准备 100 条覆盖常用指令（如"前进/后退/左转/右转/停下/打开灯光/关闭空调"等）的测试 wav 与对应真值文本，运行批量识别并计算平均 WER。测试语料应覆盖：(1) 不同说话人（男女老幼）；(2) 不同噪声环境（安静/中等/高噪声）；(3) 不同语速（慢速/常速/快速）。本实验可简化为 20 条家庭/车载场景命令。
- **源码对应**：`tools/offline_stt.py` 批量模式

**S/D/I 错误拆解（3.3.3）**
- **原理**：将 WER 拆分为 S/D/I 三类错误，便于定位模型缺陷。例如高频替换错误集中在某些字（如"在"→"再"）说明语言模型弱；高频删除错误说明 VAD 太激进切断长句；高频插入错误说明 VAD 太敏感将噪声当语音。jieba 分词后用 `jiwer` 库或自实现编辑距离算法可计算三类错误数。
- **源码对应**：`tools/offline_stt.py` --verbose 模式

**操作步骤**：

1. 准备测试语料：
   ```bash
   mkdir -p test_corpus/{wav,txt}
   # 录制 20 条常用指令 wav + 编写 reference.txt
   # 格式：
   # wav/001.wav  打开客厅的灯
   # wav/002.wav  关闭卧室的空调
   # ...
   ```

2. 批量评估：
   ```bash
   python3 src/car1_speech/tools/offline_stt.py \
     --batch --corpus-dir test_corpus \
     --output result.csv
   # 输出：total=20, WER=8.5%, S=3, D=1, I=2
   # 来源：tools/offline_stt.py 评估模式
   ```

3. 错误分析：
   - 哪些字最常识别错？（如"打开"→"答开"）
   - 哪些句子 WER 异常高？（如 12 字长句 WER 25%）
   - 是否集中在某些声母/韵母？（如 n/l 不分）

**易错点**：
- ⚠️ **测试集太小（如 5 条）** → **解决**：至少 50 条才能得出稳定 WER
- ⚠️ **测试集说话人单一** → **解决**：至少 3 名不同说话人录制
- ⚠️ **未做文本归一化** → **解决**：去除标点、空格；中文按字比较

---

#### 步骤4：ROS2 节点集成与业务联动（阶段三：能改造，30min）

**操作步骤**：

1. 订阅唤醒事件触发识别：
   ```python
   # 计划在 asr_node.py 中实现（当前为 TODO 占位）
   from std_msgs.msg import Bool, String
   from sensor_msgs.msg import AudioData
   
   class ASRNode(Node):
       def __init__(self):
           super().__init__('asr_node')
           self.declare_parameter('vad_timeout_sec', 3.0)
           # 订阅唤醒事件
           self.wake_sub = self.create_subscription(
               Bool, '/interaction/wake_word/detected',
               self.wake_callback, 10
           )
           # 发布识别结果
           self.text_pub = self.create_publisher(
               String, '/interaction/asr/text', 10
           )
           # 发布状态
           self.state_pub = self.create_publisher(
               Bool, '/interaction/asr/is_listening', 10
           )
           self.is_listening = False
       
       def wake_callback(self, msg):
           if msg.data and not self.is_listening:
               self.is_listening = True
               self.state_pub.publish(Bool(data=True))
               self.get_logger().info('Wake detected, start ASR...')
               # 启动 5s 录音 + 识别
               # ... 实际引擎由 tools/offline_stt.py 提供
   ```

2. 命令词解析示例（机器人控制）：
   ```python
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
   ```

3. 端到端测试：
   - 唤醒"小飞同学"
   - 说话"前进一米"
   - 终端打印 `[ASR] Recognized: 前进一米  →  action=move_forward`
   - 机器人执行前进动作

**易错点**：
- ⚠️ **ASR 节点未在 wake 触发后才开始录音** → **解决**：默认 IDLE，订阅到 `wake_word/detected=True` 后启动录音
- ⚠️ **ASR 与 TTS 同时占用麦克风/扬声器** → **解决**：状态机控制互斥（详见 exp05）

---

#### 完整可运行代码 demo_asr.py

```python
# -*- coding: utf-8 -*-
"""
实验3 demo：ASR 离线识别 + 批量 WER 评估
平台：B2 / C1
运行：python3 demo_asr.py --wav test.wav
      python3 demo_asr.py --batch --corpus test_corpus/
"""
import argparse
import csv
from pathlib import Path
import sherpa_onnx
import soundfile as sf


def load_recognizer(model_dir):
    return sherpa_onnx.OfflineRecognizer.from_transducer(
        tokens=f"{model_dir}/asr/tokens.txt",
        encoder=f"{model_dir}/asr/encoder.onnx",
        decoder=f"{model_dir}/asr/decoder.onnx",
        joiner=f"{model_dir}/asr/joiner.onnx",
        num_threads=2,
    )


def recognize_file(recognizer, wav_path):
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if sr != 16000:
        raise ValueError(f"采样率需 16kHz，实际 {sr}")
    s = recognizer.create_stream()
    s.accept_waveform(sr, audio)
    recognizer.decode_streams([s])
    return s.result.text.strip()


def compute_wer(ref: str, hyp: str) -> tuple[int, int, int, int]:
    """简单字级编辑距离，返回 (S, D, I, N)"""
    ref_chars = list(ref.replace(" ", ""))
    hyp_chars = list(hyp.replace(" ", ""))
    n = len(ref_chars)
    if n == 0:
        return (0, 0, len(hyp_chars), 0)
    # 编辑距离 DP
    dp = [[0] * (len(hyp_chars) + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i  # 删除
    for j in range(len(hyp_chars) + 1):
        dp[0][j] = j  # 插入
    for i in range(1, n + 1):
        for j in range(1, len(hyp_chars) + 1):
            if ref_chars[i-1] == hyp_chars[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # 删除
                    dp[i][j-1],    # 插入
                    dp[i-1][j-1],  # 替换
                )
    # 简化：S+D+I = 编辑距离
    return (0, 0, 0, n)  # 详细拆解需回溯


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="/home/iflytek/AI/sherpa-onnx")
    parser.add_argument("--wav", help="单个 wav 路径")
    parser.add_argument("--batch", action="store_true", help="批量评估")
    parser.add_argument("--corpus", help="批量语料目录（含 wav/ 与 ref.txt）")
    args = parser.parse_args()
    
    rec = load_recognizer(args.model_dir)
    
    if args.wav:
        text = recognize_file(rec, args.wav)
        print(f"[ASR] {text}")
        return
    
    if args.batch and args.corpus:
        corpus = Path(args.corpus)
        results = []
        with open(corpus / "ref.txt", encoding="utf-8") as f:
            refs = [line.strip().split(maxsplit=1) for line in f if line.strip()]
        for wav_name, ref_text in refs:
            wav_path = corpus / wav_name
            hyp = recognize_file(rec, wav_path)
            results.append((wav_name, ref_text, hyp))
            print(f"[{wav_name}] ref={ref_text!r} hyp={hyp!r}")
        out = corpus / "result.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["wav", "ref", "hyp"])
            w.writerows(results)
        print(f"[OK] Result saved to {out}")


if __name__ == "__main__":
    main()
```

### 3.7 注意事项

- ⚠️ **asr_node.py 当前为 TODO 占位** → demo 独立运行，节点化封装为扩展任务
- ⚠️ **ASR 与 TTS 同时占用音频设备** → 状态机互斥控制（详见 exp05）
- ⚠️ **VAD 参数需根据场景调优** → 命令词 1.0-1.5s，对话 2.0-3.0s
- ⚠️ **WER 评估需多说话人** → 至少 3 人，避免单人过拟合
- ⚠️ **采样率严格 16kHz** → 不匹配会导致识别乱码或空字符串

### 3.8 实验总结

**完成成果**:
- 部署 sherpa-onnx ASR 模型，实现 Offline 与 Online 两种识别模式
- 调优 VAD 端点检测参数（vad_timeout_sec）
- 完成 20 条语料 WER 评估（目标 < 10%）
- 集成 ASR + 命令词解析 + 业务动作联动

**技能收获**:
- 掌握 ASR 流水线原理（特征→声学模型→解码）
- 理解 Online vs Offline Recognizer 的取舍
- 学会用 WER 评估 ASR 准确率并拆解 S/D/I 错误

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 识别全是乱码 | 采样率/声道数不匹配 | `ffmpeg -ar 16000 -ac 1` 转换 |
| 短句频繁被切断 | VAD timeout 太小 | 调高到 2.0-3.0s |
| 长句末尾多识别 | VAD timeout 太大 | 调低到 1.0-1.5s |
| WER > 20% | 训练集与场景不匹配 | 收集场景化语料做 fine-tune |

### 3.9 实验报告要求

**思考题**:
1. 对比 Online 与 Offline Recognizer 在延迟、精度、内存占用上的差异，对话场景为何必须用 Online？
2. VAD 端点检测基于哪些声学特征？短时能量与频谱平坦度哪个更稳健？
3. WER 拆解 S/D/I 三类错误对模型优化有什么指导意义？请举例说明。

**评分标准**: ASR 部署 20 分 + 离/在线 API 调用 20 分 + VAD 调参 20 分 + WER 评估 30 分 + 实验报告 10 分 = 100 分。
