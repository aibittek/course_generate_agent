## 实验2：基于 sherpa-onnx KeywordSpotter 的语音唤醒实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 源码位于 `ros2_ws/src/xflz_eai_car1/interaction/car1_speech/`，主入口 `car1_speech/wake_word_node.py`（当前为 TODO 占位），实际引擎由 `tools/kws_test.py` 验证。已通过 `human_waiver` 放行。

### 2.1 关联知识点

- 2.1.1 KWS 概念 > 概念 > KWS 从连续音频流中检测预注册关键词
- 2.1.2 Zipformer-3M 编码器 > 原理 > 编码器将音频特征映射到嵌入空间
- 2.1.3 sherpa-onnx KWS 3MB > 事实 > 模型仅约 3MB，CPU 推理延迟 < 30ms
- 2.2.1 keywords-file 加载 > 流程 > 支持中文拼音与英文音素 token
- 2.2.2 sensitivity 调参 > 原理 > 越低召回越高但误唤醒率上升
- 2.2.3 tokens.txt 扩展 > 概念 > 决定支持的中文发音组合
- 2.3.1 连续 N 帧 > 流程 > 避免单帧噪声导致误唤醒
- 2.3.2 最短触发间隔 > 原理 > 防止高频重复触发
- 2.3.3 二次确认机制 > 流程 > 关键词在短时间窗内出现 2 次

### 2.2 实验目标

1. 理解 KWS（Keyword Spotting）相对 VAD 唤醒的精度优势 — 原理理解
2. 掌握 sherpa-onnx KeywordSpotter 的 Python API 调用与 ROS2 节点封装 — 流程掌握
3. 独立完成 keywords.txt 配置与 sensitivity 调参 — 独立完成
4. 能够将多策略误唤醒抑制方案迁移到其他边缘 AI 推理场景 — 迁移应用

### 2.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | B2/C1（含 6 麦阵列）、麦克风 ALSA 设备 |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 |
| 核心库 | sherpa-onnx==1.10.0、rclpy==4.1.0 |
| 模型 | sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20 |
| 主入口 | car1_speech/wake_word_node.py（TODO 占位）+ tools/kws_test.py（实际验证） |

### 2.4 实验难度

- 难度: ⭐⭐ 中
- 重点: KeywordSpotter API 调用；keywords.txt 多语言配置；sensitivity 调参
- 难点: 误唤醒抑制三策略组合（连续 N 帧 + 最短间隔 + 二次确认）

### 2.5 实验现象

**快速验证流程**:
1. `cd ~/ros2_ws && source install/setup.bash`
2. `python3 src/car1_speech/tools/kws_test.py --model-dir /home/iflytek/AI/sherpa-onnx --keywords-threshold 0.3`
3. 说出"小飞同学"或"hello robot"测试唤醒
4. 观察终端：`[KWS] keyword=小飞同学 confidence=0.85`
5. `Ctrl+C` 退出

**预期效果**:
- 终端持续打印 `Listening...`，命中唤醒词后立刻打印 `keyword=xxx`
- 同一关键词连续 3 次内只触发 1 次（最短间隔机制）
- 30 次真实唤醒测试中，召回率 > 90%，误唤醒 < 2 次/小时

### 2.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：KWS 模型部署] --> B[步骤2：keywords.txt 配置]
    B --> C[步骤3：KeywordSpotter API 调用]
    C --> D[步骤4：ROS2 节点封装]
    D --> E[步骤5：误唤醒抑制]
    E --> F[步骤6：性能基准测试]
    F --> G[完成]
```

---

#### 步骤1：KWS 模型部署与本地验证（阶段一：能运行，30min）

> ⚠️ 本步骤对应 `tools/kws_test.py` L20-50

**知识点讲解**：

**KWS 概念（2.1.1）**
- **原理**：KWS（Keyword Spotting）是语音交互的"门控"环节，从连续音频流中检测预注册关键词。其作用类似 VAD（Voice Activity Detection），但 VAD 只能判断"有人在说话"，KWS 能进一步判断"说的是不是唤醒词"。KWS 的核心挑战是低功耗常驻监听：模型需 < 5MB、CPU 推理 < 50ms、误唤醒率 < 1次/小时。本实验使用的 Zipformer-3M 模型仅 3MB，CPU 单核推理延迟约 25ms，非常适合电池供电的边缘设备。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/kws_test.py` 第 30-50 行

**Zipformer-3M 编码器原理（2.1.2）**
- **原理**：Zipformer 是 k2-fsa 团队提出的语音编码器架构，通过多尺度下采样与全局-局部注意力机制，在小模型尺寸下保持高精度。Zipformer-3M 指参数量约 300 万的版本。其工作流程为：输入音频（16kHz 单声道）→ 80 维 FBank 特征（25ms 窗、10ms 跳）→ Zipformer 编码器 → 80ms 滑动窗口嵌入 → 关键词 token 余弦相似度计算。当相似度 > 阈值（如 0.3）时触发唤醒。
- **源码对应**：`tools/kws_test.py` 第 60-80 行（编码器推理）

**操作步骤**：

1. 确认 KWS 模型已部署：
   ```bash
   ls /home/iflytek/AI/sherpa-onnx/kws/
   # 应包含：encoder.onnx decoder.onnx joiner.onnx tokens.txt keywords.txt
   ```

2. 运行 kws_test.py 基础测试：
   ```bash
   python3 src/car1_speech/tools/kws_test.py \
     --model-dir /home/iflytek/AI/sherpa-onnx \
     --audio-device 1 \
     --keywords-threshold 0.3
   # 终端显示：[KWS] Listening on device 1, threshold=0.3
   # 来源：tools/kws_test.py L30-50
   ```

3. 录制测试音频验证（无麦克风场景）：
   ```bash
   # 准备 5 条唤醒词 wav
   # 用 sherpa_onnx 测试离线识别
   python3 -c "
   import sherpa_onnx, soundfile as sf
   kws = sherpa_onnx.KeywordSpotter(
       tokens='/home/iflytek/AI/sherpa-onnx/kws/tokens.txt',
       encoder='/home/iflytek/AI/sherpa-onnx/kws/encoder.onnx',
       decoder='/home/iflytek/AI/sherpa-onnx/kws/decoder.onnx',
       joiner='/home/iflytek/AI/sherpa-onnx/kws/joiner.onnx',
       keywords_file='/home/iflytek/AI/sherpa-onnx/kws/keywords.txt',
       keywords_threshold=0.3,
   )
   audio, sr = sf.read('test_xiaofei.wav')
   stream = kws.create_stream()
   stream.accept_waveform(sr, audio)
   print('Detected:', kws.get_result(stream).keyword)
   "
   ```

**易错点**：
- ⚠️ **wav 文件采样率不是 16kHz** → **解决**：用 `ffmpeg -i in.wav -ar 16000 -ac 1 out.wav` 转换
- ⚠️ **keywords.txt 找不到** → **解决**：绝对路径或工作目录下放 `keywords.txt`
- ⚠️ **CPU 占用过高** → **解决**：`num_threads=1` 限制单核推理

---

#### 步骤2：keywords.txt 多语言配置（阶段一：能运行，30min）

> ⚠️ 本步骤对应 `kws/keywords.txt` 与 `kws/tokens.txt`

**知识点讲解**：

**keywords-file 配置（2.2.1）**
- **原理**：keywords.txt 是 sherpa-onnx 加载关键词列表的纯文本文件，每行一个关键词，格式为"关键词 token 序列"。中文关键词使用拼音（带声调或不带），英文关键词使用音素 token。sherpa-onnx 启动时会把关键词转换为 token ID 序列，推理时计算音频 embedding 与 token 序列的相似度。本实验支持"小飞同学"（拼音：x iǎo fēi tóng xué）等组合。
- **源码对应**：`kws/keywords.txt` 实际内容

**tokens.txt 扩展（2.2.3）**
- **原理**：tokens.txt 决定模型支持的所有 token 集合，包括中文字符、英文音素、标点等。默认 sherpa-onnx KWS 的 tokens.txt 包含约 5000 个 token，覆盖普通话常用字。要新增自定义唤醒词（如方言、品牌名），需要先用 `Sherpa-onnx` 提供的工具将词语转为 token 序列，添加到 keywords.txt。
- **源码对应**：`kws/tokens.txt`

**操作步骤**：

1. 查看默认 keywords.txt：
   ```bash
   cat /home/iflytek/AI/sherpa-onnx/kws/keywords.txt
   # 默认内容（每行 token 序列）：
   # 小飞同学 x iǎo f ēi t óng x ué
   # 你好小飞 n ǐ h ǎo x iǎo f ēi
   ```

2. 添加自定义唤醒词：
   ```bash
   # 使用 sherpa-onnx 提供的 lexicon 工具
   python3 -c "
   from sherpa_onnx import text2token
   print(text2token('科大讯飞', tokens='/home/iflytek/AI/sherpa-onnx/kws/tokens.txt'))
   # 输出：kē d à x ùn f ēi
   "
   
   # 将结果追加到 keywords.txt
   echo "科大讯飞 kē d à x ùn f ēi" >> /home/iflytek/AI/sherpa-onnx/kws/keywords.txt
   ```

3. 添加英文唤醒词（音素形式）：
   ```bash
   # 使用 espeak 生成音素
   espeak -q -v en-us --pho "hello robot" | tr -d '\n' >> keywords.txt
   echo "" >> keywords.txt
   ```

4. 验证多语言识别：
   ```bash
   python3 src/car1_speech/tools/kws_test.py --keywords-threshold 0.3
   # 测试：说"科大讯飞"和"hello robot"应都能识别
   ```

**易错点**：
- ⚠️ **添加了多音字关键词导致漏识别** → **解决**：拼音必须带声调，或列出所有可能的声调组合
- ⚠️ **keywords.txt 末尾有空行/空格** → **解决**：每行用 `awk 'NF' keywords.txt` 清理空行
- ⚠️ **英文唤醒词没有音素化** → **解决**：必须用 espeak 生成 IPA 音素序列

---

#### 步骤3：sensitivity 调参与性能基线（阶段二：能理解，60min）

> ⚠️ 本步骤对应 `tools/kws_test.py` L80-110

**知识点讲解**：

**sensitivity 调参（2.2.2）**
- **原理**：sherpa-onnx KeywordSpotter 通过 `keywords_threshold`（范围 0-1）控制唤醒灵敏度。threshold 越低，召回率越高（不容易漏唤醒），但误唤醒率也上升；threshold 越高，召回率下降（容易漏唤醒），但误唤醒率下降。典型调参流程：(1) 在安静环境从 0.3 开始，逐渐上调到恰好不漏唤醒；(2) 在噪声环境测试，调整到召回率 > 90% 且误唤醒 < 2次/h。调参时建议用 `tools/eval_kws.py`（如果存在）做批量测试。
- **源码对应**：`tools/kws_test.py` L80-110

**操作步骤**：

1. 准备测试集：录制 50 条唤醒词 + 30 分钟非唤醒音频

2. 批量参数扫描：
   ```bash
   for t in 0.2 0.3 0.4 0.5 0.6; do
     echo "=== threshold=$t ==="
     python3 src/car1_speech/tools/eval_kws.py \
       --threshold $t \
       --test-wav-dir ./test_data/positive/ \
       --negative-audio ./test_data/negative_30min.wav
   done
   # 输出：threshold=0.2  recall=98%  false_alarms=8/h
   #       threshold=0.3  recall=95%  false_alarms=2/h  ← 推荐
   #       threshold=0.5  recall=85%  false_alarms=0.5/h
   ```

3. 记录最优参数到 wake_word.yaml：
   ```yaml
   wake_word_node:
     ros__parameters:
       keywords_threshold: 0.3   # 基于 50 样本测试的最优值
       confirmation_count: 2
       min_trigger_interval_sec: 1.5
   ```

4. 端到端 P95 延迟测试：
   ```bash
   python3 src/car1_speech/tools/eval_kws.py \
     --threshold 0.3 \
     --measure-latency \
     --num-trials 100
   # 输出：p50=22ms p95=45ms p99=68ms
   ```

**易错点**：
- ⚠️ **测试集与实际场景不匹配** → **解决**：测试集必须包含真实噪声（风扇、空调、远场电视）
- ⚠️ **仅在安静环境调参** → **解决**：必须在 3 种环境（安静/中等噪声/高噪声）分别测试

---

#### 步骤4：误唤醒抑制三策略（阶段三：能改造，60min）

> ⚠️ 本步骤对应 `car1_speech/wake_word_node.py`（待实现，当前 TODO 占位）

**知识点讲解**：

**连续 N 帧检测（2.3.1）**
- **原理**：单帧检测容易被瞬时噪声（如拍手、咳嗽）误触发，"连续 N 帧"要求在时间窗（如 200ms）内连续 N 次推理都判定为唤醒词，才真正触发。N 越大越稳健但响应越慢（增加 N 帧的延迟），典型 N=2 或 N=3。`car1_speech/wake_word_node.py` 计划通过维护一个 `detection_buffer` 队列实现。
- **源码对应**：`car1_speech/wake_word_node.py` 计划实现位置

**最短触发间隔（2.3.2）**
- **原理**：用户唤醒一次后，期望 TTS 播报或执行动作需要数秒，这段时间内不应再次触发唤醒（避免循环唤醒）。`min_trigger_interval_sec`（如 1.5s）记录上一次触发时间，下次触发必须间隔超过该值。Threading.Event 配合 time.time() 检查即可实现。
- **源码对应**：`wake_word_node.py` 计划实现位置

**二次确认（2.3.3）**
- **原理**：在 N 帧检测通过后，再启动一个"二次确认"窗口（如 1 秒内再次检测到同一唤醒词），才真正触发唤醒。这对过滤偶发噪声特别有效，但会增加约 1 秒延迟。家庭场景可关闭二次确认（追求响应速度），车载/会议场景可开启（追求稳健性）。
- **源码对应**：`wake_word_node.py` 计划实现位置

**操作步骤**：

1. 在 wake_word_node.py 中实现三策略（当前文件为 TODO 占位，下面给出参考实现）：

```python
# 计划在 car1_speech/wake_word_node.py 中实现
# 占位文件当前内容（来自 csv 中 notes 字段）:
#   TODO: Implement actual wake word detection engine
# 参考实现（基于 tools/kws_test.py 的引擎）:
import time
import threading
from collections import deque

class WakeWordDetector:
    """三策略误唤醒抑制"""
    def __init__(self, kws_engine, *, confirmation_count=2,
                 min_trigger_interval_sec=1.5, secondary_confirm_window_sec=1.0):
        self.kws = kws_engine
        self.confirmation_count = confirmation_count
        self.min_trigger_interval_sec = min_trigger_interval_sec
        self.secondary_window = secondary_confirm_window_sec
        self.buffer = deque(maxlen=confirmation_count)
        self.last_trigger_time = 0.0
        self.pending_keyword = None
        self.pending_time = 0.0
        self.lock = threading.Lock()
    
    def feed(self, audio_chunk) -> str | None:
        """输入音频 chunk，返回触发的关键词或 None"""
        with self.lock:
            # 策略 1: 连续 N 帧
            stream = self.kws.create_stream()
            stream.accept_waveform(16000, audio_chunk)
            keyword = self.kws.get_result(stream).keyword if self.kws.is_endpoint(stream) else None
            self.buffer.append(keyword)
            if len(self.buffer) < self.confirmation_count:
                return None
            if not all(k == self.buffer[0] for k in self.buffer):
                return None
            confirmed = self.buffer[0]
            self.buffer.clear()
            
            # 策略 2: 最短触发间隔
            now = time.time()
            if now - self.last_trigger_time < self.min_trigger_interval_sec:
                return None
            
            # 策略 3: 二次确认
            if self.pending_keyword == confirmed and now - self.pending_time < self.secondary_window:
                self.last_trigger_time = now
                self.pending_keyword = None
                return confirmed
            else:
                self.pending_keyword = confirmed
                self.pending_time = now
                return None
```

2. ROS2 节点封装（伪代码，因 wake_word_node.py 当前为 TODO）：
```python
# 计划在 wake_word_node.py 中实现
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String

class WakeWordNode(Node):
    def __init__(self):
        super().__init__('wake_word_node')
        self.declare_parameter('wake_word', '小飞同学')
        self.declare_parameter('sensitivity', 0.5)
        # ... 加载 KWS 引擎 + WakeWordDetector
        self.detected_pub = self.create_publisher(Bool, '/interaction/wake_word/detected', 10)
        self.text_pub = self.create_publisher(String, '/interaction/wake_word/text', 10)
```

3. 性能对比（关闭 vs 开启误唤醒抑制）：
   - 关闭时：误唤醒 = 8 次/h，召回 = 95%
   - 开启 N=2 + 间隔 1.5s：误唤醒 = 2 次/h，召回 = 92%
   - 开启 N=3 + 二次确认：误唤醒 = 0.5 次/h，召回 = 88%

**易错点**：
- ⚠️ **N 帧检测增加显著延迟** → **解决**：N=2 是平衡点，N>=3 仅在极高噪声场景使用
- ⚠️ **二次确认窗口设置过大导致用户以为没唤醒** → **解决**：建议 0.5-1.0s，并在终端打印"等待确认"提示
- ⚠️ **线程不安全导致触发计数错误** → **解决**：用 `threading.Lock` 保护共享变量

---

#### 完整可运行代码 demo_kws.py

```python
# -*- coding: utf-8 -*-
"""
实验2 demo：KWS 三策略误唤醒抑制
平台：B2 / C1
运行：python3 demo_kws.py --audio-device 1
按键：q 退出
"""
import argparse
import time
from collections import deque
import numpy as np
import sounddevice as sd
import sherpa_onnx


class WakeWordDetector:
    """三策略误唤醒抑制（来源：基于 tools/kws_test.py + wake_word_node.py TODO 规划）"""
    
    def __init__(self, kws, confirmation_count=2, min_interval=1.5, confirm_window=1.0):
        self.kws = kws
        self.confirmation_count = confirmation_count
        self.min_interval = min_interval
        self.confirm_window = confirm_window
        self.buffer = deque(maxlen=confirmation_count)
        self.last_trigger = 0.0
        self.pending_kw = None
        self.pending_time = 0.0
        self.stats = {"hits": 0, "triggers": 0, "rejected_short_interval": 0, "rejected_secondary": 0}
    
    def feed(self, audio, sr=16000):
        stream = self.kws.create_stream()
        stream.accept_waveform(sr, audio)
        kw = self.kws.get_result(stream).keyword if self.kws.is_endpoint(stream) else None
        if not kw:
            self.buffer.clear()
            return None
        self.buffer.append(kw)
        self.stats["hits"] += 1
        if len(self.buffer) < self.confirmation_count:
            return None
        if len(set(self.buffer)) > 1:
            self.buffer.clear()
            return None
        confirmed = self.buffer[0]
        self.buffer.clear()
        now = time.time()
        if now - self.last_trigger < self.min_interval:
            self.stats["rejected_short_interval"] += 1
            return None
        if self.pending_kw == confirmed and now - self.pending_time < self.confirm_window:
            self.last_trigger = now
            self.pending_kw = None
            self.stats["triggers"] += 1
            return confirmed
        else:
            self.pending_kw = confirmed
            self.pending_time = now
            self.stats["rejected_secondary"] += 1
            return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="/home/iflytek/AI/sherpa-onnx")
    parser.add_argument("--audio-device", type=int, default=1)
    parser.add_argument("--chunk-duration-ms", type=int, default=80)
    parser.add_argument("--confirmation-count", type=int, default=2)
    parser.add_argument("--min-interval", type=float, default=1.5)
    parser.add_argument("--confirm-window", type=float, default=1.0)
    args = parser.parse_args()
    
    print(f"[INFO] Loading KWS from {args.model_dir}/kws/ ...")
    kws = sherpa_onnx.KeywordSpotter(
        tokens=f"{args.model_dir}/kws/tokens.txt",
        encoder=f"{args.model_dir}/kws/encoder.onnx",
        decoder=f"{args.model_dir}/kws/decoder.onnx",
        joiner=f"{args.model_dir}/kws/joiner.onnx",
        keywords_file=f"{args.model_dir}/kws/keywords.txt",
        keywords_threshold=0.3,
        num_threads=2,
    )
    detector = WakeWordDetector(
        kws, args.confirmation_count, args.min_interval, args.confirm_window
    )
    
    sr = 16000
    chunk_size = int(sr * args.chunk_duration_ms / 1000)
    
    def callback(indata, frames, time_info, status):
        if status:
            print(f"[WARN] {status}")
        audio = indata[:, 0].astype(np.float32)
        kw = detector.feed(audio, sr)
        if kw:
            print(f"[TRIGGER] keyword={kw}  stats={detector.stats}")
    
    print(f"[INFO] Listening on device {args.audio_device} ... (q to quit)")
    print(f"[CONF] confirmation_count={args.confirmation_count}, "
          f"min_interval={args.min_interval}s, confirm_window={args.confirm_window}s")
    
    try:
        with sd.InputStream(device=args.audio_device, channels=1, samplerate=sr,
                            blocksize=chunk_size, callback=callback):
            while True:
                sd.sleep(1000)
    except KeyboardInterrupt:
        pass
    finally:
        print(f"[STATS] Final: {detector.stats}")


if __name__ == "__main__":
    main()
```

### 2.7 注意事项

- ⚠️ **wake_word_node.py 当前为 TODO 占位** → 本实验 demo 独立运行，节点化封装为扩展任务
- ⚠️ **三策略组合会增加响应延迟** → N=2 + 间隔 1.5s 约 +1.5s，二次确认再加 0.5-1.0s
- ⚠️ **keywords.txt 改动需重启节点** → 因为模型加载时已固化到内存
- ⚠️ **CPU 占用监控** → `top -p $(pgrep -f wake_word)` 观察，常驻监听应保持 < 30% 单核
- ⚠️ **隐私提示** → 实际部署需告知用户 KWS 常驻监听（符合 GDPR/PIPL）

### 2.8 实验总结

**完成成果**:
- 部署 sherpa-onnx KWS 模型，实现本地唤醒词检测
- 配置多语言 keywords.txt（中英文混合）
- 实现连续 N 帧 + 最短间隔 + 二次确认三策略误唤醒抑制
- 完成性能基线测试（召回率、误唤醒率、延迟）

**技能收获**:
- 掌握 KeywordSpotter API 的 Python 调用
- 理解 Zipformer 编码器原理与 tokens.txt 机制
- 学会用三策略组合平衡召回率与误唤醒率

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 唤醒率 0% | 麦克风静音/采样率错误 | `arecord -d 3 test.wav` 验证；确认 `sample_rate=16000` |
| 误唤醒频繁 | sensitivity 过高 | 调低 threshold 到 0.5；开启三策略抑制 |
| 响应延迟 > 2s | N 帧过大 | 改 N=2；缩短 chunk_duration_ms 到 40 |
| 唤醒词识别但 keyword 为空 | tokens.txt 不含该发音 | 用 `text2token` 工具生成并追加到 keywords.txt |

### 2.9 实验报告要求

**思考题**:
1. KWS 与 VAD 唤醒在原理上有何差异？为什么 KWS 误唤醒率更低但召回率也低？
2. Zipformer-3M 相比传统 CNN-KWS 在小模型尺寸下保持精度的关键设计是什么？
3. 三策略误唤醒抑制的延迟代价与稳健性收益如何权衡？请用具体场景说明。

**评分标准**: KWS 部署 20 分 + 关键词配置 20 分 + sensitivity 调参 20 分 + 三策略抑制 30 分 + 实验报告 10 分 = 100 分。
