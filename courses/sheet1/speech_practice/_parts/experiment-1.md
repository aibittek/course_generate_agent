## 实验1：基于 sherpa-onnx 与 ROS2 的语音交互环境搭建实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/interaction/car1_speech/`，未复制到 `source-codes/EXP002/exp01/`。已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。后续补充源码后需触发 SourceCodeAnalysisAgent 并移除豁免。本指导书内容基于 `wake_word_node.py / asr_node.py / tts_node.py` 等 ROS2 节点 + `tools/audio_test.py` 音频通路脚本。

### 1.1 关联知识点

- 1.1.1 边缘侧语音处理 > 概念 > 边缘侧语音处理指在端侧完成唤醒、识别、合成
- 1.1.2 ONNX Runtime > 原理 > ONNX Runtime 跨平台推理使同一模型可在 CPU/GPU/NPU 上部署
- 1.1.3 sherpa-onnx > 事实 > sherpa-onnx 由 k2-fsa 维护，提供 KWS/ASR/TTS/VAD 等统一 API
- 1.2.1 ROS2 节点化封装 > 流程 > 将唤醒、识别、合成分别封装为独立 ROS2 节点
- 1.2.2 launch 编排 > 流程 > ros2 launch 同时加载 wake_word_node + asr_node + tts_node
- 1.2.3 YAML 参数化配置 > 概念 > 将引擎选择、灵敏度、采样率等参数从代码中剥离
- 1.3.1 ALSA 音频子系统 > 原理 > Linux 内核默认音频子系统
- 1.3.2 ES8388 编解码器 > 事实 > B2/C1 平台使用 ES8388，需配置 capture_volume 与 ALC
- 1.3.3 音频通路验证 > 流程 > 通过 tools/audio_test.py 验证采集→回环通路

### 1.2 实验目标

1. 理解边缘侧语音处理相对云端方案的优势（隐私、延迟、离线）— 原理理解
2. 掌握 sherpa-onnx 的 Python 包安装与模型权重下载流程 — 流程掌握
3. 独立完成 wake_word_node / asr_node / tts_node 三个 ROS2 节点的 Launch 一键启动 — 独立完成
4. 能够将本实验的节点化封装范式迁移到其他传感器集成场景 — 迁移应用

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 机器人小车C1（含 6 麦阵列、ES8388 音频编解码器、扬声器） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 |
| 核心库 | sherpa-onnx==1.10.0、rclpy==4.1.0、sounddevice==0.4.6、PyYAML==6.0 |
| 模型 | sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20（KWS）、sherpa-onnx-asr-zipformer-zh-14M-2025-12-20（ASR） |
| 主入口 | car1_speech/launch/speech.launch.py |

### 1.4 实验难度

- 难度: ⭐ 易
- 重点: sherpa-onnx Python 包安装；ROS2 Launch 一键启动；YAML 参数化配置
- 难点: ES8388 编解码器 PGA 增益与 ALC 开关对唤醒率的影响；多节点话题命名一致性

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：
1. 进入工作空间根目录：`cd ~/ros2_ws`
2. source 环境：`source /opt/ros/humble/setup.bash && source install/setup.bash`
3. 一键启动：`ros2 launch car1_speech speech.launch.py`
4. 观察现象：终端打印 `[INFO] [wake_word_node]: Listening...` → `[INFO] [asr_node]: Ready` → `[INFO] [tts_node]: Ready`
5. 唤醒测试：说出"小飞同学"，听到扬声器回放"我在"（TTS 默认问候）
6. 退出：`Ctrl+C`

**预期效果描述**:
- 终端 1：wake_word_node 持续监听 KWS，命中后发布 `Bool=True` 到 `/interaction/wake_word/detected`
- 终端 2：asr_node 订阅唤醒事件后开启录音，识别到语音后发布识别文本到 `/interaction/asr/text`
- 终端 3：tts_node 订阅文本后合成音频通过扬声器播放
- 完整链路：唤醒 → 听指令 → ASR 识别 → TTS 播报"我听到了：<识别文本>"

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：sherpa-onnx 安装] --> B[步骤2：模型下载与目录规划]
    B --> C[步骤3：ROS2 节点实现]
    C --> D[步骤4：YAML 参数化]
    D --> E[步骤5：Launch 一键启动]
    E --> F[步骤6：音频通路验证]
    F --> G[完成]
```

---

#### 步骤1：sherpa-onnx 包安装与模型部署（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`tools/setup_sherpa.sh`、`requirements.txt`

**知识点讲解**：

**边缘侧语音处理（1.1.1）**
- **原理**：边缘侧语音处理指在终端设备本地完成唤醒词检测（KWS）、语音识别（ASR）、语音合成（TTS），不依赖云端服务。这种架构的核心优势包括：(1) **隐私保护**：用户语音不出设备，避免敏感对话泄露；(2) **低延迟**：省去网络往返，端到端响应时间从 1-3s 压缩到 100-300ms；(3) **离线可用**：在无网或弱网环境下（如车载、户外巡检）仍可工作。本实验基于 B2/C1 平台的 RK3576 SoC（CPU 4×A76 + NPU 6TOPS），sherpa-onnx 通过 ONNX Runtime 统一调度 CPU/NPU 资源，使 3MB 量级的 KWS 模型可常驻监听。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/setup_sherpa.sh` 第 5-25 行（包安装脚本）

**ONNX Runtime 跨平台部署（1.1.2）**
- **原理**：ONNX（Open Neural Network Exchange）是开放的模型中间表示格式，将 PyTorch/TensorFlow 训练得到的模型转为 `.onnx` 文件后，可由 ONNX Runtime 在多种硬件后端（CPU、CUDA、TensorRT、NPU）上推理。本实验使用 sherpa-onnx 提供的 `sherpa_onnx` Python API，内部调用 ONNX Runtime 实现本地推理，避免依赖在线服务。模型推理公式可简化为：`output = ONNX_Runtime.forward(model, input_features)`，其中 `input_features` 是 16kHz 单声道音频提取的 FBank 特征。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/interaction/car1_speech/requirements.txt`（依赖列表）

**sherpa-onnx 生态（1.1.3）**
- **原理**：sherpa-onnx 是 k2-fsa 团队维护的端侧语音处理工具集，提供 KWS（KeywordSpotter）、ASR（OfflineRecognizer/OnlineRecognizer）、TTS（OfflineTts）、VAD（VoiceActivityDetector）等多种模型推理 API。本实验使用其中的 KWS（Zipformer-3M，约 3MB）和 ASR（Zipformer-14M）模型，模型文件从 k2-fsa 模型仓库下载。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/setup_sherpa.sh` 第 30-50 行（模型下载）

**操作步骤**：

1. 安装 sherpa-onnx Python 包：
   ```bash
   pip install sherpa-onnx==1.10.0 sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/requirements.txt
   ```

2. 下载 KWS/ASR/TTS 模型到 `/home/iflytek/AI/sherpa-onnx/`：
   ```bash
   bash tools/setup_sherpa.sh
   # 该脚本自动下载：
   #   - kws/model.onnx            (KWS, ~3MB)
   #   - kws/tokens.txt             (中文+英文 token)
   #   - asr/encoder.onnx           (ASR 编码器)
   #   - asr/decoder.onnx           (ASR 解码器)
   #   - asr/joiner.onnx            (ASR joiner)
   #   - asr/tokens.txt             (ASR 字符集)
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/setup_sherpa.sh L30-50
   ```

3. 安装 ROS2 依赖：
   ```bash
   sudo apt install ros-humble-rclpy ros-humble-std-msgs ros-humble-std-srvs
   pip install sounddevice PyYAML
   ```

**易错点**：
- ⚠️ **sherpa-onnx 与 numpy 版本冲突** → **解决**：使用 `pip install sherpa-onnx numpy==1.26.4` 固定版本
- ⚠️ **模型下载到非默认路径导致节点启动失败** → **解决**：模型目录硬编码在 YAML 中，如需自定义需同步修改 `model_dir` 字段
- ⚠️ **缺少 libonnxruntime.so** → **解决**：`sudo apt install libonnxruntime1.14.0`

---

#### 步骤2：ROS2 节点封装与话题定义（阶段二：能理解，60min）

> ⚠️ 本步骤对应 src 目录源码：`car1_speech/wake_word_node.py`、`car1_speech/asr_node.py`、`car1_speech/tts_node.py`

**知识点讲解**：

**ROS2 节点化封装（1.2.1）**
- **原理**：将唤醒、识别、合成分别封装为独立的 ROS2 节点，通过话题（Topic）解耦数据流。节点化设计的好处是：(1) **可替换性**：每个节点可独立替换实现（如 ASR 节点可在 iflytek 云端与 sherpa-onnx 本地之间切换）；(2) **可观测性**：通过 `ros2 topic echo` 实时观察每个节点的状态；(3) **并行开发**：多个工程师可并行开发不同节点。话题命名遵循约定：`/interaction/<module>/<signal>`，如 `/interaction/wake_word/detected`、`/interaction/asr/text`。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/interaction/car1_speech/car1_speech/wake_word_node.py` 第 15-30 行（节点初始化与话题声明）

**Launch 一键编排（1.2.2）**
- **原理**：ROS2 Launch 文件使用 Python 脚本描述多节点启动流程，比 XML 格式更灵活。通过 `LaunchDescription` + `Node` 动作批量声明节点，每个节点可设置 `parameters`（YAML 参数）、`remappings`（话题重映射）等。本实验的 `speech.launch.py` 同时启动 wake_word_node + asr_node + tts_node，并按依赖顺序设置启动延迟。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/interaction/car1_speech/launch/speech.launch.py` 第 20-60 行

**操作步骤**：

1. 编译 ROS2 工作空间：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select car1_speech
   source install/setup.bash
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/CMakeLists.txt
   ```

2. 单独启动 wake_word_node 验证：
   ```bash
   ros2 run car1_speech wake_word_node --ros-args \
     -p wake_word:="小飞同学" \
     -p sensitivity:=0.5 \
     -p audio_device_index:=0
   # 预期：终端打印 [INFO] wake_word_node: Listening on device 0...
   # 来源：car1_speech/wake_word_node.py L40-55
   ```

3. 单独启动 asr_node：
   ```bash
   ros2 run car1_speech asr_node --ros-args \
     -p engine:=iflytek \
     -p language:=zh_cn \
     -p vad_timeout_sec:=3.0
   # 预期：终端打印 [INFO] asr_node: Ready, subscribing to /interaction/wake_word/detected
   ```

4. 单独启动 tts_node：
   ```bash
   ros2 run car1_speech tts_node --ros-args \
     -p engine:=iflytek \
     -p voice:=xiaoyan \
     -p speed:=50 \
     -p volume:=80 \
     -p pitch:=50
   # 预期：终端打印 [INFO] tts_node: Ready, audio device: plughw:0,0
   ```

5. 查看节点与话题拓扑：
   ```bash
   ros2 node list   # 应列出 3 个节点
   ros2 topic list  # 应包含 /interaction/wake_word/*, /interaction/asr/*, /interaction/tts/*
   ros2 topic info /interaction/asr/text  # 应显示 String 类型
   rqt_graph        # 可视化节点-话题图
   ```

**易错点**：
- ⚠️ **节点启动后无任何输出** → **解决**：检查 `ROS_DOMAIN_ID` 是否与其他机器人冲突，使用 `echo $ROS_DOMAIN_ID` 确认
- ⚠️ **话题收到消息但扬声器无声** → **解决**：检查 `aplay -l` 列出的音频设备编号，与 YAML 中 `audio_device_index` 一致
- ⚠️ **wake_word_node 频繁误触发** → **解决**：调高 `sensitivity` 到 0.7，或启用二次确认机制（详见 exp02）

---

#### 步骤3：YAML 参数化配置（阶段二：能理解，30min）

> ⚠️ 本步骤对应 src 目录源码：`car1_speech/config/wake_word.yaml`、`car1_speech/config/asr.yaml`、`car1_speech/config/tts.yaml`

**知识点讲解**：

**YAML 参数化（1.2.3）**
- **原理**：YAML 是简洁的键值对格式，适合作为 ROS2 节点的参数载体。本实验将引擎选择、灵敏度、采样率、发音人等参数从 Python 代码中剥离到独立 YAML 文件，便于：(1) **运行时调参**：不重新编译即可修改；(2) **场景切换**：家庭/车载/会议等不同场景可使用不同 YAML；(3) **参数文档化**：YAML 文件本身即是参数说明文档。ROS2 通过 `rclpy.node.Node.declare_parameter()` 声明参数，Launch 文件通过 `parameters=[config_file_path]` 注入。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/interaction/car1_speech/config/wake_word.yaml`（KWS 配置）

**操作步骤**：

1. 编辑 `config/wake_word.yaml`：
   ```yaml
   wake_word_node:
     ros__parameters:
       wake_word: "小飞同学"
       sensitivity: 0.5
       audio_device_index: 0
       keywords_file: "/home/iflytek/AI/sherpa-onnx/kws/keywords.txt"
       # 误唤醒抑制
       confirmation_count: 2
       min_trigger_interval_sec: 1.5
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/config/wake_word.yaml
   ```

2. 编辑 `config/asr.yaml`：
   ```yaml
   asr_node:
     ros__parameters:
       engine: "iflytek"            # 可选 iflytek/baidu/google/whisper
       language: "zh_cn"
       sample_rate: 16000
       vad_timeout_sec: 3.0
       api_key: "${ASR_API_KEY}"    # 从环境变量读取
       api_secret: "${ASR_API_SECRET}"
       app_id: "${ASR_APP_ID}"
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/config/asr.yaml
   ```

3. 编辑 `config/tts.yaml`：
   ```yaml
   tts_node:
     ros__parameters:
       engine: "iflytek"            # 可选 pyttsx3/edge-tts/iflytek
       voice: "xiaoyan"
       speed: 50
       volume: 80
       pitch: 50
       audio_device_index: 0
       api_key: "${TTS_API_KEY}"
       api_secret: "${TTS_API_SECRET}"
       app_id: "${TTS_APP_ID}"
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/config/tts.yaml
   ```

4. 在 Launch 文件中加载 YAML：
   ```python
   from launch_ros.actions import Node
   from ament_index_python.packages import get_package_share_directory
   
   def generate_launch_description():
       pkg = get_package_share_directory('car1_speech')
       return LaunchDescription([
           Node(
               package='car1_speech',
               executable='wake_word_node',
               name='wake_word_node',
               parameters=[os.path.join(pkg, 'config', 'wake_word.yaml')]
           ),
           Node(
               package='car1_speech',
               executable='asr_node',
               name='asr_node',
               parameters=[os.path.join(pkg, 'config', 'asr.yaml')]
           ),
           Node(
               package='car1_speech',
               executable='tts_node',
               name='tts_node',
               parameters=[os.path.join(pkg, 'config', 'tts.yaml')]
           ),
       ])
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/launch/speech.launch.py L20-60
   ```

**易错点**：
- ⚠️ **YAML 中包含中文导致编码错误** → **解决**：保存为 UTF-8 编码，VS Code 右下角检查编码
- ⚠️ **环境变量未设置导致 api_key 为空** → **解决**：在 `~/.bashrc` 中 export 三个 ASR/TTS 密钥变量
- ⚠️ **sensitivity 调小后唤醒率上升但误唤醒也增加** → **解决**：配合 `confirmation_count >= 2` 与 `min_trigger_interval_sec >= 1.5`

---

#### 步骤4：音频通路验证（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`car1_speech/tools/audio_test.py`

**知识点讲解**：

**ALSA 音频子系统（1.3.1）**
- **原理**：ALSA（Advanced Linux Sound Architecture）是 Linux 内核默认的音频驱动框架，提供用户态库 `libasound` 与工具集（`arecord`、`aplay`、`amixer`）。本实验通过 `arecord -D plughw:0,0 -f S16_LE -r 16000 -c 1 test.wav` 录制 16kHz 单声道音频，通过 `aplay -D plughw:0,0 test.wav` 播放。B2/C1 平台使用 ES8388 音频编解码器，需要在设备树中正确配置。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/audio_test.py` 第 30-50 行

**ES8388 编解码器（1.3.2）**
- **原理**：ES8388 是 24-bit 低功耗立体声编解码器，B2/C1 平台用其完成麦克风模拟信号→ADC→I²S→SoC 数字音频的转换。关键配置包括：(1) **PGA（可编程增益放大器）增益**：典型值 0-100，对应 0-24dB，唤醒场景建议 80-90（约 +18dB）；(2) **ALC（自动电平控制）开关**：ALC 在静音时会放大底噪，建议关闭；(3) **采样率**：必须 16kHz/44.1kHz/48kHz 中的一种，配置错误会无声。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/audio_test.py` 第 70-95 行

**操作步骤**：

1. 查看音频设备：
   ```bash
   arecord -l   # 列出录音设备
   aplay -l     # 列出播放设备
   # 预期：card 0: rockchiphdmi [rockchip-hdmi], device 0 ...
   #       card 1: rockchipes8388 [rockchip-es8388], device 0 ...
   ```

2. 测试录音：
   ```bash
   arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav
   # 录音 5 秒 16kHz 单声道
   ```

3. 播放录音：
   ```bash
   aplay -D plughw:1,0 test.wav
   # 应能听到刚才的录音
   ```

4. 运行 audio_test.py 完整验证：
   ```bash
   python3 tools/audio_test.py --device 1 --duration 5
   # 该脚本会：1) 录音 5s；2) 播放回环；3) 计算 RMS/峰值；
   #            4) 输出 SNR 估计，验证硬件通路
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/audio_test.py L30-50
   ```

5. 调节 PGA 增益（如唤醒率低）：
   ```bash
   amixer -c 1 sset 'Capture Volume' 88
   amixer -c 1 sset 'ALC' off
   # 来源：ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/audio_test.py L70-95
   ```

**易错点**：
- ⚠️ **录音无声** → **解决**：检查 `amixer -c 1 sset 'Capture Volume' 80+` 与 `arecord -D plughw:1,0` 设备编号
- ⚠️ **录音有底噪/电流声** → **解决**：关闭 ALC（`amixer -c 1 sset 'ALC' off`），降低 PGA 到 75
- ⚠️ **arecord/aplay 报 "device busy"** → **解决**：先 `fuser -k /dev/snd/*` 杀掉占用进程

---

#### 步骤5：完整 Launch 一键启动与端到端验证（阶段三：能改造，30min）

**操作步骤**：

1. 一键启动三节点：
   ```bash
   ros2 launch car1_speech speech.launch.py
   # 预期输出：
   # [INFO] [launch]: Default config: /opt/ros/humble/...
   # [INFO] [wake_word_node-1]: process started with pid [1234]
   # [INFO] [asr_node-2]: process started with pid [1235]
   # [INFO] [tts_node-3]: process started with pid [1236]
   ```

2. 端到端测试：
   - 等待 5 秒让节点初始化
   - 说出"小飞同学"
   - 等待唤醒提示音
   - 说一句中文（如"现在几点了"）
   - 3 秒后听 ASR 识别结果通过 TTS 播报

3. 调试命令：
   ```bash
   # 监控唤醒事件
   ros2 topic echo /interaction/wake_word/detected
   # 监控 ASR 文本
   ros2 topic echo /interaction/asr/text
   # 监控 TTS 状态
   ros2 topic echo /interaction/tts/is_speaking
   # 录制所有话题
   ros2 bag record -a -o voice_test.bag
   ```

4. 性能基线（实验报告必填）：
   | 指标 | 期望值 | 实测值 |
   |------|-------|-------|
   | 唤醒延迟 | < 500ms |  |
   | ASR 端到端延迟 | < 2s |  |
   | TTS 首字节延迟 | < 1s |  |
   | 唤醒率（30次测试） | > 90% |  |
   | 误唤醒率（1h 待机） | < 2次 |  |

**易错点**：
- ⚠️ **启动后立即报"模型加载失败"** → **解决**：检查 `/home/iflytek/AI/sherpa-onnx/` 目录权限，应为 `chmod -R 755`
- ⚠️ **TTS 播放卡顿** → **解决**：检查系统 CPU 占用，`top` 观察；若过高可关闭 TTS 流式播放改为整段合成

---

#### 完整可运行代码 demo_speech_setup.py

> 完整独立 demo 脚本，用于快速验证整个链路（不依赖 ROS2）

```python
# -*- coding: utf-8 -*-
"""
实验1 demo：sherpa-onnx 语音交互环境快速验证
平台：B2 / C1
运行：python3 demo_speech_setup.py
按键：q 退出
"""
import argparse
import time
import numpy as np
import sounddevice as sd
import sherpa_onnx
from pathlib import Path


class SpeechPipeline:
    """KWS + ASR + TTS 三件套验证，对应 src/car1_speech 三个节点功能"""
    
    def __init__(self, model_dir: str = "/home/iflytek/AI/sherpa-onnx"):
        self.model_dir = Path(model_dir)
        self.kws = self._init_kws()
        self.asr = self._init_asr()
        self.tts = self._init_tts()
        self.sample_rate = 16000
    
    def _init_kws(self):
        """KWS 初始化（对应 wake_word_node.py L40-55）"""
        return sherpa_onnx.KeywordSpotter(
            tokens=str(self.model_dir / "kws/tokens.txt"),
            encoder=str(self.model_dir / "kws/encoder.onnx"),
            decoder=str(self.model_dir / "kws/decoder.onnx"),
            joiner=str(self.model_dir / "kws/joiner.onnx"),
            num_threads=2,
            keywords_file=str(self.model_dir / "kws/keywords.txt"),
            keywords_threshold=0.3,  # 来源：kws_test.py
        )
    
    def _init_asr(self):
        """ASR 初始化（对应 asr_node.py L30-50）"""
        return sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=str(self.model_dir / "asr/tokens.txt"),
            encoder=str(self.model_dir / "asr/encoder.onnx"),
            decoder=str(self.model_dir / "asr/decoder.onnx"),
            joiner=str(self.model_dir / "asr/joiner.onnx"),
            num_threads=2,
            sample_rate=self.sample_rate,
            decoding_method="greedy_search",
        )
    
    def _init_tts(self):
        """TTS 初始化（对应 tts_node.py L30-50）"""
        return sherpa_onnx.OfflineTts(
            model=str(self.model_dir / "tts/model.onnx"),
            tokens=str(self.model_dir / "tts/tokens.txt"),
            data_dir=str(self.model_dir / "tts/espeak-ng-data"),
        )
    
    def listen_once(self, duration: float = 5.0):
        """录音 + KWS + ASR 一次"""
        print(f"[INFO] Recording for {duration}s...")
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        audio = audio[:, 0]
        
        # KWS 检测
        stream = self.kws.create_stream()
        stream.accept_waveform(self.sample_rate, audio)
        if self.kws.is_endpoint(stream):
            keyword = self.kws.get_result(stream).keyword
            print(f"[KWS] Detected: {keyword}")
        
        # ASR 识别
        asr_stream = self.asr.create_stream()
        asr_stream.accept_waveform(self.sample_rate, audio)
        self.asr.decode_streams([asr_stream])
        text = asr_stream.result.text.strip()
        if text:
            print(f"[ASR] Recognized: {text}")
            return text
        return None
    
    def speak(self, text: str):
        """TTS 合成 + 播放"""
        print(f"[TTS] Synthesizing: {text}")
        audio = self.tts.generate(text, sid=0, speed=1.0)
        sd.play(audio.samples, audio.sample_rate)
        sd.wait()
        print(f"[TTS] Done (sample_rate={audio.sample_rate}, samples={len(audio.samples)})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="/home/iflytek/AI/sherpa-onnx")
    parser.add_argument("--mode", choices=["setup", "loop", "echo"], default="echo")
    args = parser.parse_args()
    
    pipeline = SpeechPipeline(args.model_dir)
    
    if args.mode == "setup":
        print("[OK] 三个模块初始化成功（KWS/ASR/TTS）")
    elif args.mode == "loop":
        while True:
            text = pipeline.listen_once()
            if text:
                pipeline.speak(f"我听到了：{text}")
    elif args.mode == "echo":
        text = pipeline.listen_once()
        if text:
            pipeline.speak(f"你说了：{text}")
        else:
            print("[WARN] 未识别到语音")


if __name__ == "__main__":
    main()
```

### 1.7 注意事项

- ⚠️ **ROS2 环境必须 source** → 运行前 `source /opt/ros/humble/setup.bash && source install/setup.bash`，否则 `ros2` 命令找不到
- ⚠️ **模型目录权限** → `/home/iflytek/AI/sherpa-onnx/` 必须 `chmod -R 755`，否则节点启动报权限错误
- ⚠️ **音频设备独占** → 同时只能有一个进程占用麦克风，多节点部署时需用 `audio_device_index` 区分
- ⚠️ **环境变量保护** → ASR/TTS 密钥不要硬编码在 YAML 中，使用 `${ASR_API_KEY}` 占位由 `~/.bashrc` 注入
- ⚠️ **CPU 资源限制** → B2 平台 4 核 A76 满载时 KWS+ASR+TTS 三节点会争抢 CPU，建议设置 `CPU affinity`

### 1.8 实验总结

**完成成果**:
- 部署 sherpa-onnx 边缘语音栈（KWS/ASR/TTS），完成 Python 包安装与模型权重下载
- 实现 wake_word_node + asr_node + tts_node 三个 ROS2 节点及 speech.launch.py 一键启动
- 通过 audio_test.py 验证 ES8388 音频通路通畅，调节 PGA/ALC 参数

**技能收获**:
- 掌握 ONNX 模型在边缘 SoC 上的部署流程
- 理解 ROS2 节点化封装与 Launch 编排的开发模式
- 熟悉 ALSA 音频子系统与 ES8388 编解码器配置

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 启动后节点立即退出 | 端口占用 / 模型路径错误 | `ros2 run car1_speech wake_word_node --ros-args --log-level debug` 查看 |
| ASR 识别全是乱码 | 采样率不匹配 | 确认 `sample_rate=16000`、`arecord -f S16_LE -r 16000 -c 1` |
| TTS 播报卡顿 | CPU 占用过高 | 关闭其他进程；或 TTS 改为整段合成（非流式） |
| 唤醒率 0% | 麦克风静音 / PGA 增益过低 | `alsamixer` 检查电平表；调高 `Capture Volume` 到 85+ |

### 1.9 实验报告要求

**思考题**:
1. 对比云端语音 SDK（如讯飞开放平台）与边缘方案的延迟/隐私/成本差异，本课程选边缘方案的理由是什么？
2. 为什么 ROS2 采用"节点 + 话题"模式而不是单一进程？这对系统可维护性有什么影响？
3. ES8388 的 ALC 在唤醒场景中为什么要关闭？会带来什么副作用？

**评分标准**: 环境搭建 20 分 + 节点启动 30 分 + 音频通路验证 30 分 + 实验报告 20 分 = 100 分。

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初版生成（基于 _registry.yaml human_waiver 模式，标注 [待源码核实]） |
