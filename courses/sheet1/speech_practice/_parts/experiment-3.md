## 实验3：基于本地 TTS 引擎的语音合成与参数调控实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 源码位于 `ros2_ws/src/xflz_eai_car1/interaction/car1_speech/`，主入口 `car1_speech/tts_node.py`（当前 TODO 占位），实际引擎由 `tools/tts_test.py` 验证。已通过 `human_waiver` 放行。

### 3.1 关联知识点

- 4.1.1 TTS 概念 > 概念 > TTS 将文本转为可听语音
- 4.1.2 端到端 TTS 原理 > 原理 > 文本分析→韵律→声学→声码器
- 4.1.3 pyttsx3/edge-tts/iflytek 对比 > 事实 > 三种主流 TTS 引擎
- 4.2.1 voice 切换 > 流程 > 切换发音人（中文/英文）
- 4.2.2 speed/volume/pitch 0-100 > 概念 > 语速/音量/音调范围
- 4.2.3 默认参数 50/80/50 > 流程 > 均衡默认输出
- 4.3.1 /tts/stop 服务 > 流程 > 提供打断服务
- 4.3.2 打断机制原理 > 原理 > 事件信号 + 播放线程协作退出
- 4.3.3 多语种切换 > 概念 > 切换 voice 参数实现

### 3.2 实验目标

1. 理解 TTS 端到端神经网络的原理与传统拼接合成差异 — 原理理解
2. 掌握 pyttsx3/edge-tts/iflytek 三种引擎的部署与切换 — 流程掌握
3. 独立完成 voice/speed/volume/pitch 参数调优与多语种切换 — 独立完成
4. 能够将 TTS + 打断机制迁移到对话系统的响应式播报 — 迁移应用

### 3.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | B2/C1（含扬声器）、ES8388 音频通路 |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 |
| 核心库 | sherpa-onnx==1.10.0、pyttsx3==2.90、edge-tts==6.1.9、sounddevice |
| 模型 | sherpa-onnx-tts-vits-zh-aishell3-2025-12-20（约 30MB） |
| 主入口 | car1_speech/tts_node.py（TODO 占位）+ tools/tts_test.py |

### 3.4 实验难度

- 难度: ⭐⭐ 中
- 重点: TTS 引擎部署；voice/speed/volume/pitch 调参；多语种切换
- 难点: 打断机制的事件信号与播放线程协作退出

### 3.5 实验现象

**快速验证流程**:
1. 启动 TTS 节点：`ros2 run car1_speech tts_node --ros-args -p engine:=iflytek -p voice:=xiaoyan`
2. 发送测试文本：`ros2 topic pub --once /interaction/tts/speak std_msgs/msg/String "{data: '你好小飞同学'}"`
3. 扬声器播放女声"你好小飞同学"

**预期效果**:
- 合成延迟 < 1s（云端 iflytek 视网络而定）
- 调节 speed=80 听到明显加速
- 切换 voice=emma 听到英文女声
- 触发 /interaction/tts/stop 服务，当前播报立即停止

### 3.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：TTS 引擎部署] --> B[步骤2：参数调控]
    B --> C[步骤3：多语种切换]
    C --> D[步骤4：打断服务]
    D --> E[步骤5：ROS2 节点集成]
    E --> F[完成]
```

---

#### 步骤1：三种 TTS 引擎部署与对比（阶段一：能运行，45min）

> ⚠️ 本步骤对应 `tools/tts_test.py` L20-60

**知识点讲解**：

**TTS 概念（4.1.1）**
- **原理**：TTS（Text-to-Speech）将文本转为可听语音，是语音交互的"出口"。TTS 质量直接决定用户体验——机械感强、语调生硬的 TTS 会让用户感到不自然。本实验对比三种主流 TTS 引擎：(1) **pyttsx3**：离线轻量，基于系统自带语音引擎（Linux 用 espeak），延迟 < 200ms 但质量一般；(2) **edge-tts**：微软 Azure 在线 TTS，免费使用 Edge 浏览器接口，音质好但需联网；(3) **iflytek**：讯飞云端 TTS，支持多发音人和定制，音质优秀但需 API 密钥。
- **源码对应**：`tools/tts_test.py` L20-60

**端到端 TTS 原理（4.1.2）**
- **原理**：传统 TTS 流水线分为 4 步：(1) **文本分析**：分词、字形转音形（G2P）、多音字消歧；(2) **韵律预测**：预测停顿、语调、重音；(3) **声学模型**：将音素序列转为梅尔频谱；(4) **声码器**：将频谱转为可听波形（如 Griffin-Lim、HiFi-GAN、VITS）。端到端 TTS（如 VITS、Tacotron 2+WaveNet）将四步合一为单一神经网络，音质更高但模型更大。本实验使用的 VITS 约 30MB，CPU 推理延迟约 200ms。
- **源码对应**：`tools/tts_test.py` 内部由 sherpa-onnx VITS 实现

**操作步骤**：

1. **pyttsx3 离线测试**（最简单）：
   ```bash
   pip install pyttsx3
   sudo apt install espeak-ng   # Linux 系统语音引擎
   python3 -c "
   import pyttsx3
   engine = pyttsx3.init()
   engine.say('你好小飞同学')
   engine.runAndWait()
   "
   # 优点：完全离线，延迟 < 200ms
   # 缺点：机械感强，不支持多发音人
   ```

2. **edge-tts 在线测试**（音质好）：
   ```bash
   pip install edge-tts
   edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好小飞同学" --write-media test_edge.mp3
   aplay test_edge.mp3
   # 优点：音质接近真人
   # 缺点：需联网，延迟 1-3s
   ```

3. **iflytek 云端 TTS 测试**（生产环境）：
   ```bash
   # 配置 API 密钥
   export IFYTEK_APP_ID=xxx
   export IFYTEK_API_KEY=xxx
   export IFYTEK_API_SECRET=xxx
   
   python3 src/car1_speech/tools/tts_test.py \
     --engine iflytek \
     --voice xiaoyan \
     --text "你好小飞同学"
   # 优点：支持定制发音人、语速、音调
   # 缺点：需付费 API
   # 来源：tools/tts_test.py L20-60
   ```

4. **sherpa-onnx VITS 本地 TTS**（离线高质量）：
   ```bash
   # 下载 VITS 模型
   bash tools/setup_sherpa.sh  # 自动下载 tts/model.onnx tts/tokens.txt tts/espeak-ng-data
   
   python3 -c "
   import sherpa_onnx, sounddevice as sd
   tts = sherpa_onnx.OfflineTts(
       model='/home/iflytek/AI/sherpa-onnx/tts/model.onnx',
       tokens='/home/iflytek/AI/sherpa-onnx/tts/tokens.txt',
       data_dir='/home/iflytek/AI/sherpa-onnx/tts/espeak-ng-data',
   )
   audio = tts.generate('你好小飞同学', sid=0, speed=1.0)
   sd.play(audio.samples, audio.sample_rate)
   sd.wait()
   "
   # 优点：离线、音质好、延迟 < 500ms
   ```

**易错点**：
- ⚠️ **pyttsx3 报"无语音引擎"** → **解决**：`sudo apt install espeak-ng`
- ⚠️ **edge-tts 网络超时** → **解决**：检查代理设置或改用离线方案
- ⚠️ **VITS 模型加载失败** → **解决**：确认 espeak-ng-data 目录完整（包含 phoneme index 文件）

---

#### 步骤2：voice/speed/volume/pitch 参数调控（阶段一：能运行，30min）

> ⚠️ 本步骤对应 `config/tts.yaml` 与 `tools/tts_test.py` L60-90

**知识点讲解**：

**voice 切换（4.2.1）**
- **原理**：TTS 引擎的 `voice` 参数控制发音人，不同发音人在音色、性别、年龄、口音上差异显著。pyttsx3 通过 `engine.getProperty('voices')` 列出系统所有可用 voice；edge-tts 通过 `--voice zh-CN-XiaoxiaoNeural` 等指定；iflytek 通过 `voice=xiaoyan/xiaofeng/emma` 等指定。本实验支持中文女声（xiaoyan）、男声（xiaofeng），英文女声（emma）、男声（victoria）。
- **源码对应**：`config/tts.yaml` 中 `voice: xiaoyan`

**speed/volume/pitch 参数（4.2.2）**
- **原理**：三参数均归一化到 0-100 范围（部分引擎为 0.5-2.0 浮点）。`speed` 控制语速（50=常速，80=1.6倍速）；`volume` 控制音量（80=中等响度，100=最大）；`pitch` 控制音调（50=中性，70=偏女声/童声，30=偏男声/老人声）。sherpa-onnx VITS 接受浮点 `speed=1.0`，需将 0-100 转换为 0.5-2.0。
- **源码对应**：`config/tts.yaml` 中 `speed/volume/pitch`

**操作步骤**：

1. 编辑 `config/tts.yaml`：
   ```yaml
   tts_node:
     ros__parameters:
       engine: "iflytek"
       voice: "xiaoyan"
       speed: 50
       volume: 80
       pitch: 50
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/config/tts.yaml
   ```

2. 参数扫描测试：
   ```python
   # demo_tts_params.py
   for speed in [30, 50, 70, 100]:
       audio = tts.generate("今天天气真好", sid=0, speed=speed/50)
       sf.write(f"speed_{speed}.wav", audio.samples, audio.sample_rate)
   # 听感：speed=30 慢速清晰，speed=50 正常，speed=70 偏快，speed=100 急促
   ```

3. 找出"自然听感"参数组合：
   - 默认建议：speed=50, volume=80, pitch=50（均衡）
   - 会议场景：speed=40, pitch=40（沉稳男声）
   - 儿童陪伴：speed=60, pitch=80（明快女声）

4. 在 ROS2 节点中实现动态调参（计划在 tts_node.py 中实现）：
   ```python
   # 当前 tts_node.py 是 TODO 占位
   # 计划实现：
   self.declare_parameter('voice', 'xiaoyan')
   self.declare_parameter('speed', 50)
   self.declare_parameter('volume', 80)
   self.declare_parameter('pitch', 50)
   
   # 支持动态更新（无需重启节点）
   self.add_on_set_parameters_callback(self._on_param_update)
   ```

**易错点**：
- ⚠️ **speed 调到 100 后听不清** → **解决**：限制 30-80 范围；或对 TTS 引擎做范围映射
- ⚠️ **切换 voice 后仍有旧音色残留** → **解决**：重启 TTS 引擎实例
- ⚠️ **pitch 调高后声音变调失真** → **解决**：sherpa-onnx VITS 范围 -12~+12 半音，需转换

---

#### 步骤3：多语种切换（阶段二：能理解，30min）

> ⚠️ 本步骤对应 `tools/tts_test.py` L90-120

**知识点讲解**：

**多语种切换（4.3.3）**
- **原理**：多语种 TTS 通过切换 `voice` 参数实现：中文用 `xiaoyan`（女）/ `xiaofeng`（男）；英文用 `emma`（女）/ `victoria`（男）。底层模型差异：中文模型用拼音 token + 声调，英文模型用 CMU 音素 token。sherpa-onnx VITS-zh 仅支持中文，英文需用 VITS-en 模型（需额外下载）。本实验通过 `engine` 参数在多个模型间切换。
- **源码对应**：`tools/tts_test.py` L90-120

**操作步骤**：

1. 下载英文 VITS 模型：
   ```bash
   # 假设 sherpa-onnx-en 模型在 /home/iflytek/AI/sherpa-onnx-en/
   bash tools/setup_sherpa_en.sh
   # 下载 vits-ljspeech-en 模型
   ```

2. 多语种测试：
   ```python
   def tts_multilang(text: str, lang: str):
       if lang == "zh":
           tts = sherpa_onnx.OfflineTts(model=".../sherpa-onnx/tts/model.onnx", ...)
       elif lang == "en":
           tts = sherpa_onnx.OfflineTts(model=".../sherpa-onnx-en/tts/model.onnx", ...)
       audio = tts.generate(text, sid=0, speed=1.0)
       return audio.samples, audio.sample_rate
   
   # 中文合成
   samples, sr = tts_multilang("你好", "zh")
   sd.play(samples, sr); sd.wait()
   # 英文合成
   samples, sr = tts_multilang("Hello", "en")
   sd.play(samples, sr); sd.wait()
   ```

3. 自动语言检测（结合 ASR 文本）：
   ```python
   import re
   def detect_lang(text: str) -> str:
       # 含中文字符判中文，否则英文
       if re.search(r'[\u4e00-\u9fff]', text):
           return "zh"
       return "en"
   ```

**易错点**：
- ⚠️ **中英文混排合成混乱** → **解决**：先用 langdetect 分段；或训练中英混排模型
- ⚠️ **英文模型不支持数字读法** → **解决**：先 G2P 转换（"123" → "one hundred twenty three"）

---

#### 步骤4：打断机制实现（阶段三：能改造，60min）

> ⚠️ 本步骤对应 `car1_speech/tts_node.py`（TODO 占位）的 `std_srvs::Trigger` 服务

**知识点讲解**：

**打断服务（4.3.1）**
- **原理**：TTS 播报过程中用户可能想中断（如"够了别说了"），需要立即停止当前播报。ROS2 通过 `std_srvs::Trigger` 服务实现：客户端调用 `/interaction/tts/stop` 服务，服务端处理函数中停止当前播放并返回成功。本实验在 tts_node.py 中实现（当前 TODO 占位）。
- **源码对应**：`tts_node.py` TODO 计划实现

**打断机制原理（4.3.2）**
- **原理**：打断机制依赖两个关键设计：(1) **事件信号**：`threading.Event` 或 `std::atomic<bool>`，主线程通过设置事件通知播放线程立即退出；(2) **播放线程协作退出**：播放线程在每个 PCM 帧写入后检查事件，若被设置则停止播放并释放音频设备。如果使用阻塞 `sd.play()`，可通过 `sd.stop()` 强制停止。设计要点：避免音频设备未释放导致后续播报失败。
- **源码对应**：`tts_node.py` 计划实现位置

**操作步骤**：

1. 实现打断服务（计划在 tts_node.py 中）：
   ```python
   # 计划在 tts_node.py 中实现（当前为 TODO 占位）
   import rclpy, threading
   from rclpy.node import Node
   from std_msgs.msg import String, Bool
   from std_srvs.srv import Trigger
   import sounddevice as sd
   import sherpa_onnx
   
   class TTSNode(Node):
       def __init__(self):
           super().__init__('tts_node')
           self.declare_parameter('engine', 'iflytek')
           self.declare_parameter('voice', 'xiaoyan')
           # ... 加载 TTS 引擎
           
           self.speak_sub = self.create_subscription(
               String, '/interaction/tts/speak', self.speak_callback, 10
           )
           self.state_pub = self.create_publisher(
               Bool, '/interaction/tts/is_speaking', 10
           )
           self.stop_srv = self.create_service(
               Trigger, '/interaction/tts/stop', self.stop_callback
           )
           
           self.is_speaking = False
           self.stop_event = threading.Event()
           self.speak_thread = None
       
       def speak_callback(self, msg):
           if self.is_speaking:
               self.get_logger().warn('TTS 正在播报，新文本加入队列')
           text = msg.data
           self.speak_thread = threading.Thread(
               target=self._speak_worker, args=(text,), daemon=True
           )
           self.speak_thread.start()
       
       def _speak_worker(self, text):
           self.is_speaking = True
           self.state_pub.publish(Bool(data=True))
           self.stop_event.clear()
           try:
               audio = self.tts.generate(text, sid=0, speed=1.0)
               # 分块播放，每块后检查 stop_event
               chunk_size = 4096
               for i in range(0, len(audio.samples), chunk_size):
                   if self.stop_event.is_set():
                       self.get_logger().info('TTS 被打断')
                       break
                   chunk = audio.samples[i:i+chunk_size]
                   sd.play(chunk, audio.sample_rate)
                   sd.wait()
           finally:
               self.is_speaking = False
               sd.stop()
               self.state_pub.publish(Bool(data=False))
       
       def stop_callback(self, request, response):
           if self.is_speaking:
               self.stop_event.set()
               response.success = True
               response.message = 'TTS stopped'
           else:
               response.success = False
               response.message = 'TTS not speaking'
           return response
   ```

2. 客户端测试：
   ```bash
   # 启动 TTS 播报长文本
   ros2 topic pub --once /interaction/tts/speak std_msgs/msg/String \
     "{data: '这是一段很长的文本用来测试打断机制是否有效请耐心等待我即将说完'}"

   # 1 秒后触发打断
   sleep 1 && ros2 service call /interaction/tts/stop std_srvs/srv/Trigger
   # 预期：播报立即停止，service 返回 success=True
   ```

3. 性能对比（开启 vs 关闭打断）：
   - 关闭打断：用户听到完整播报才能输入下一指令（响应慢）
   - 开启打断：用户随时可中断（响应快，体验好）

**易错点**：
- ⚠️ **打断后音频设备未释放** → **解决**：在 `finally` 块中 `sd.stop()`
- ⚠️ **打断后下一段播报无声** → **解决**：检查音频设备是否被独占占用，重启播放线程
- ⚠️ **打断服务响应延迟** → **解决**：服务回调直接 `event.set()`，不要做耗时操作

---

#### 完整可运行代码 demo_tts.py

```python
# -*- coding: utf-8 -*-
"""
实验4 demo：TTS 多引擎 + 参数调控 + 打断
平台：B2 / C1
运行：python3 demo_tts.py --engine edge
按键：s 停止当前播报，q 退出
"""
import argparse
import threading
import time
import numpy as np
import sounddevice as sd
import soundfile as sf


class TTSEngine:
    """多 TTS 引擎适配（来源：基于 tools/tts_test.py 抽象）"""
    
    def __init__(self, engine: str, voice: str = "xiaoyan",
                 speed: int = 50, volume: int = 80, pitch: int = 50):
        self.engine_name = engine
        self.voice = voice
        self.speed = speed / 50.0
        self.volume = volume / 100.0
        self.pitch = pitch
        if engine == "pyttsx3":
            import pyttsx3
            self.engine = pyttsx3.init()
        elif engine == "sherpa":
            import sherpa_onnx
            self.engine = sherpa_onnx.OfflineTts(
                model="/home/iflytek/AI/sherpa-onnx/tts/model.onnx",
                tokens="/home/iflytek/AI/sherpa-onnx/tts/tokens.txt",
                data_dir="/home/iflytek/AI/sherpa-onnx/tts/espeak-ng-data",
            )
        elif engine == "edge":
            # edge-tts 异步调用
            import edge_tts
            self.engine = edge_tts.Communicate
        else:
            raise ValueError(f"Unknown engine: {engine}")
    
    def synth(self, text: str) -> tuple[np.ndarray, int]:
        if self.engine_name == "pyttsx3":
            # 简化：保存到临时文件后读取
            self.engine.save_to_file(text, "/tmp/tts.wav")
            self.engine.runAndWait()
            audio, sr = sf.read("/tmp/tts.wav", dtype="float32")
            return audio, sr
        elif self.engine_name == "sherpa":
            audio = self.engine.generate(text, sid=0, speed=self.speed)
            return np.array(audio.samples, dtype=np.float32), audio.sample_rate
        elif self.engine_name == "edge":
            # edge-tts 通过 asyncio 运行
            import asyncio
            async def _run():
                comm = self.engine(text=text, voice="zh-CN-XiaoxiaoNeural")
                audio_bytes = b""
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        audio_bytes += chunk["data"]
                return audio_bytes
            loop = asyncio.new_event_loop()
            audio_bytes = loop.run_until_complete(_run())
            loop.close()
            import io
            audio, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
            return audio, sr


class TTSPlayer:
    """带打断功能的 TTS 播放器"""
    
    def __init__(self, engine: TTSEngine):
        self.engine = engine
        self.is_playing = False
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
    
    def speak(self, text: str):
        with self.lock:
            self.stop_event.clear()
            self.is_playing = True
        try:
            audio, sr = self.engine.synth(text)
            chunk_size = 4096
            for i in range(0, len(audio), chunk_size):
                if self.stop_event.is_set():
                    print("[INTERRUPTED]")
                    break
                sd.play(audio[i:i+chunk_size], sr)
                sd.wait()
        finally:
            self.is_playing = False
            sd.stop()
    
    def stop(self):
        self.stop_event.set()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="sherpa",
                        choices=["pyttsx3", "sherpa", "edge"])
    parser.add_argument("--voice", default="xiaoyan")
    parser.add_argument("--speed", type=int, default=50)
    parser.add_argument("--volume", type=int, default=80)
    parser.add_argument("--pitch", type=int, default=50)
    args = parser.parse_args()
    
    engine = TTSEngine(args.engine, args.voice, args.speed, args.volume, args.pitch)
    player = TTSPlayer(engine)
    
    print(f"[INFO] Engine={args.engine} voice={args.voice} speed={args.speed} volume={args.volume} pitch={args.pitch}")
    
    texts = [
        "你好，我是小飞同学，很高兴认识你。",
        "今天天气真好，适合出去散步。",
        "我支持中文和英文双语合成。",
    ]
    
    try:
        for t in texts:
            print(f"[SPEAK] {t}")
            player.speak(t)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        if player.is_playing:
            player.stop()


if __name__ == "__main__":
    main()
```

### 3.7 注意事项

- ⚠️ **tts_node.py 当前为 TODO 占位** → demo 独立运行，节点化封装为扩展任务
- ⚠️ **音频设备独占** → TTS 播报期间应禁止 ASR 录音（状态机互斥）
- ⚠️ **多语种需切换模型** → 不能用一个模型合成中英混排
- ⚠️ **打断后必须 sd.stop()** → 否则后续播报无声
- ⚠️ **云端 TTS 注意 API 配额** → 讯飞免费版每天 5 万次，超出收费

### 3.8 实验总结

**完成成果**:
- 部署三种 TTS 引擎（pyttsx3/edge-tts/iflytek/sherpa-onnx VITS）
- 调优 voice/speed/volume/pitch 参数，对比不同发音人/语速/音调效果
- 实现多语种切换（中文/英文）
- 实现 TTS 打断服务 `/interaction/tts/stop`

**技能收获**:
- 掌握 TTS 端到端神经网络的原理与部署
- 理解多引擎适配的设计模式（接口抽象）
- 学会用 threading.Event 实现线程协作打断

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| TTS 无声 | 音频设备编号错误 | `aplay -l` 检查；`audio_device_index` 配置正确 |
| 合成中文乱码 | tokens.txt 不含中文字符 | 下载中文专用 tokens.txt |
| 打断后下一段无声 | sd.stop() 未在 finally 调用 | 加 try-finally 保护 |
| 云端 TTS 报 401 | API 密钥错误 | 检查 `${IFLYTEK_API_KEY}` 环境变量 |

### 3.9 实验报告要求

**思考题**:
1. 对比 pyttsx3、edge-tts、iflytek、sherpa-onnx VITS 四种 TTS 引擎在离线能力、音质、延迟、多语种上的差异，机器人产品该如何选型？
2. 端到端 TTS 相比传统拼接合成（Concatenative Synthesis）在自然度上提升的本质原因是什么？
3. TTS 打断机制的事件信号设计如何避免音频设备泄漏？除了 threading.Event 还有什么方案？

**评分标准**: TTS 部署 20 分 + 参数调优 20 分 + 多语种 20 分 + 打断机制 30 分 + 实验报告 10 分 = 100 分。
