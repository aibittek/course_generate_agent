---
course_code: EXP002
course_name: 机器人自然语言交互应用与开发
version: v3.2
generated_at: 2026-08-04
generator: SyllabusAgent
source_spec: courses/sheet1/speech_practice/_meta/course-spec.yaml
csv_sha256: d89f7c2f6e84977519fccca3ad5325dbade2216274b2b0d5f41bd275efd91175
---

# 机器人自然语言交互应用与开发 教学大纲

> 课程代码: EXP002
> 适用对象: 人工智能/机器人工程/智能科学与技术 本科高年级
> 总学时: 32（理论 0 + 实验 32）
> 课程类型: 专业核心课（实践导向）
> 制定日期: 2026-08-04

---

## 一、课程目标

### 1.1 知识目标
通过本课程的学习，学生能够：
1. 掌握基于讯飞六麦阵列(AIUI 协议)与本地语音模型(ASR/TTS)的部署与配置方法
2. 理解 ASR、TTS、VAD 的基本原理与端到端对话系统的状态机设计
3. 了解大模型 Function Calling 与多模态 VLM 在机器人交互中的工作原理
4. 熟悉 ROS2 节点化封装、YAML 参数化与 Launch 一键启动的开发模式

### 1.2 能力目标
通过本课程的学习，学生能够：
1. 具备在 B2/C1 平台上独立部署并调优本地语音模型的能力
2. 能够基于状态机构建 KWS+ASR+LLM(streaming)+TTS 端到端语音对话系统
3. 能够基于 RKLLM 部署 Function Calling 工具调用与多模态 VLM 推理
4. 能够运用 ROS2 通信机制实现多节点语音交互链路，处理打断、超时与多轮上下文

### 1.3 素养目标
通过本课程的学习，学生能够：
1. 养成离线优先、隐私敏感、低延迟的工程设计意识
2. 具备多模块协作的团队开发精神（语音/对话/大模型三方集成）
3. 树立对模型量化、NPU 部署、显存管理等资源约束的工程伦理意识

---

## 二、教学内容与学时分配

| 序号 | 章节 | 理论(h) | 实验(h) | 合计(h) | 占比 |
|------|------|--------|--------|--------|------|
| 1 | 第1章 串口通信与麦克风阵列 | 0 | 4 | 4 | 14.3% |
| 2 | 第2章 语音识别 ASR | 0 | 4 | 4 | 14.3% |
| 3 | 第3章 语音合成 TTS | 0 | 4 | 4 | 14.3% |
| 4 | 第4章 端到端对话与大模型集成 | 0 | 20 | 20 | 62.5% |
| - | **合计** | **0** | **32** | **32** | **100%** |

> 备注：本课程采用"做中学"模式，32h 全部为实验学时，知识讲授融入实验前置 brief。

---

## 三、教学内容

### 第1章 串口通信与麦克风阵列

#### 教学内容
- 串口通信 UART 原理与 pyserial 库基础（open/read/write/close）
- VID(0x1a86)/PID(0x55d4) 自动识别 USB 麦克风阵列
- 6 麦环形阵列的声源定位原理（beam 编号 + angle 方向角）
- AIUI 协议帧结构（同步头 0xA5 + 类型 + 小端长度 + 小端ID + JSON payload + 校验和）
- 接收缓冲拆帧与校验和容错、伪同步头处理
- 唤醒事件字段提取与 3 秒时间窗防抖、Lock 线程安全
- Tkinter Canvas 环形阵列可视化与 queue+after 事件刷新

#### 重点难点
- **重点**: 串口通信基础；AIUI 帧结构；唤醒回调与防抖
- **难点**: 字节级帧解析；伪同步头与校验和失败处理；多线程事件传递

#### 教学活动
- [x] 演示：xf_mic_array_gui.py 实时唤醒效果（环形阵列高亮 + 方向箭头）
- [x] 动手实验：exp01 讯飞六麦阵列的串口通信与唤醒事件

#### 对应知识点
1.1.1 串口通信概念 / 1.1.2 pyserial 库基础 / 1.1.3 VID/PID 自动识别 / 1.2.1 麦克风阵列原理 / 1.2.2 声源定位 beam/angle / 1.2.3 AIUI 协议框架 / 1.3.1 字节序与校验和 / 1.3.2 帧结构组成 / 1.3.3 接收缓冲与拆帧 / 1.4.1 唤醒事件字段 / 1.4.2 时间窗口防抖 / 1.4.3 回调与线程锁 / 1.5.1 Tkinter Canvas 基础 / 1.5.2 环形阵列绘制 / 1.5.3 线程安全事件刷新

---

### 第2章 语音识别 ASR

#### 教学内容
- 6 麦阵列 ALSA 设备识别与 audio_test.py 录音/播放验证(硬件通路)
- 讯飞 6 麦阵列+本地 sherpa-onnx 流式 ASR 完整代码执行流(asr_test.py --mic-array)
- 设备自动检测 detect_xfm_devices() 与 XfMicArray 串口唤醒
- AudioMixer 增益控制与 switch_input_to_mic 输入复用切换
- ALC(Automatic Level Control)+ Noise Gate 自动电平
- Transducer 三件套模型(tokens/encoder/decoder/joiner)与 RKNN NPU 推理
- OnlineRecognizer.from_transducer 工厂方法
- 流式识别主循环(accept_waveform → decode_stream → is_endpoint → reset)
- 100ms 块读取节奏与 single-stream 复用
- 端点检测 rule1/rule2/rule3 三规则协同
- blank_penalty 空符号惩罚
- hotwords 热词文件与 modified_beam_search 解码
- 命令词解析与 ASR 业务集成
- WER(词错误率)评估方法

#### 重点难点
- **重点**: asr_test.py 7 个模块的拆分理解(设备检测/唤醒/增益/引擎/流式循环/端点/热词);端点检测参数调优;热词配置
- **难点**: NPU 推理 provider 配置;blank_penalty 与解码延迟的平衡;长时间会话流式识别的状态管理

#### 教学活动
- [x] 演示：audio_test.py --mic-array 唤醒录音与播放验证(6 麦硬件通路)
- [x] 演示：asr_test.py --mic-array 完整流式识别流程
- [x] 演示：rule1/rule2/rule3 + blank_penalty 端点调优 A/B 对比
- [x] 演示：hotwords.txt + modified_beam_search 解决"小飞→小飞机"误识别
- [x] 动手实验：exp02 讯飞六麦阵列与sherpa-onnx的本地流式语音识别(ASR)实验

#### 对应知识点
2.0.1 音频通路与 ALSA 设备 / 2.0.2 6 麦唤醒驱动录音 / 2.1.1 detect_xfm_devices 设备自动检测 / 2.1.2 AudioMixer 增益与 ALC / 2.1.3 switch_input_to_mic 输入复用 / 2.2.1 OnlineRecognizer 构造 / 2.2.2 Transducer 架构 / 2.2.3 RKNN NPU 推理 / 2.3.1 accept_waveform 流式输入 / 2.3.2 decode_stream 增量解码 / 2.3.3 is_endpoint 内置端点 / 2.3.4 blank_penalty 空符号惩罚 / 2.4.1 hotwords 热词格式 / 2.4.2 greedy vs modified_beam_search / 2.5.1 single-stream 复用 / 2.5.2 100ms 块节奏

#### 源码入口
- **主入口**: `ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/asr_test.py`
- **主命令**: `python3 asr_test.py --mic-array`
- **复用实验1**: 串口通信(`uart_device.py`)、AIUI协议解析(`xf_mic_array.py`)、ALSA录音(`audio_test.py`)

---

### 第3章 语音合成 TTS

#### 教学内容
- TTS 原理（文本分析→韵律→声学模型→声码器）
- 主流 TTS 引擎对比（pyttsx3 / edge-tts / 讯飞）
- voice/speed/volume/pitch 参数调控
- /tts/stop 打断服务与多语种切换

#### 重点难点
- **重点**: 本地 TTS 部署与参数调优
- **难点**: 打断机制的事件信号与播放线程协作退出

#### 教学活动
- [x] 演示：不同 voice/speed/pitch 下的合成效果对比
- [x] 动手实验：exp04 本地 TTS 引擎与参数调控

#### 对应知识点
4.1.1 TTS 概念 / 4.1.2 端到端原理 / 4.1.3 pyttsx3/edge-tts/iflytek / 4.2.1 voice 切换 / 4.2.2 speed/volume/pitch 0-100 / 4.2.3 默认参数 50/80/50 / 4.3.1 /tts/stop 服务 / 4.3.2 打断机制原理 / 4.3.3 多语种切换

---

### 第4章 端到端对话与大模型集成

#### 教学内容
- 状态机式语音交互（IDLE/LISTENING/SPEAKING）
- Capture 线程常驻与 audio_queue 缓冲
- OpenAI 兼容 HTTP API 与流式 SSE
- RKLLM 本地推理引擎
- Function Calling 工具调用与三步注册
- 多模态大模型 VLM 原理
- RKLLM_INPUT_MULTIMODAL 接口
- 多模态交互闭环（ASR→VLM→TTS）

#### 重点难点
- **重点**: 端到端语音对话系统集成 + Function Calling + VLM
- **难点**: 流式响应按句分割送 TTS + 多模态 < 3s 延迟控制

#### 教学活动
- [x] 项目实战：exp05 端到端语音对话交互
- [x] 项目实战：exp06 Function Calling 工具调用
- [x] 综合项目：exp07 多模态大模型 VLM

#### 对应知识点
5.1.1 状态机 / 5.1.2 状态流转 / 5.1.3 Capture 线程常驻 / 5.2.1 OpenAI 兼容 API / 5.2.2 流式 SSE / 5.2.3 RKLLM 推理 / 5.3.1 Function Calling / 5.3.2 tools_config 三步注册 / 5.3.3 嵌套结构解析 / 5.4.1 VLM 概念 / 5.4.2 图像预处理 / 5.4.3 RKLLM_INPUT_MULTIMODAL / 5.5.1 多模态闭环 / 5.5.2 <3s 延迟要求 / 5.5.3 性能指标

---

## 四、实验项目

| 序号 | 实验名称 | 学时 | 实验类型 | 关联知识点 |
|------|---------|------|---------|----------|
| 1 | 基于讯飞六麦阵列的串口通信与唤醒事件实验 | 4h | 设计性 ⭐⭐ | 1.1.1~1.5.3 |
| 2 | 基于讯飞六麦阵列与sherpa-onnx的本地流式语音识别(ASR)实验 | 4h | 设计性 ⭐⭐⭐ | 2.0.1~2.5.2 |
| 3 | 基于本地 TTS 引擎的语音合成与参数调控实验 | 4h | 设计性 ⭐⭐ | 3.1.1~3.3.3 |
| 4 | 基于状态机的端到端语音对话交互实验 | 8h | 设计性 ⭐⭐ | 4.1.1~4.1.3 |
| 5 | 基于 Function Calling 的大模型工具调用实验 | 4h | 设计性 ⭐⭐ | 4.2.1~4.3.3 |
| 6 | 基于多模态大模型的视觉语言理解(VLM)实验 | 8h | 综合性 ⭐⭐⭐ | 4.4.1~4.5.3 |
| - | **合计** | **32h** | - | - |

### 实验类型分布
- 设计性：5 个（83.3%）
- 综合性：1 个（16.7%）

### 难度分布
- ⭐⭐ 中等：5 个
- ⭐⭐⭐ 综合：1 个

---

## 五、教学方法

| 方法 | 适用环节 | 占比 |
|------|---------|------|
| 任务驱动 | 实验实训 | 50% |
| 演示法 | 工具/效果展示 | 20% |
| 项目实战 | 综合应用（exp05/06） | 20% |
| 小组讨论 | 难点突破（VAD 调参、Function Calling 解析） | 5% |
| 讲授法 | 实验前 brief 知识铺垫 | 5% |

> 本课程以"做中学"为主，讲授时间被压缩到每个实验的 5-10 分钟前置 brief。

---

## 六、考核方式

### 6.1 成绩构成

| 考核环节 | 比例 | 考核内容 |
|---------|------|---------|
| 平时表现 | 10% | 出勤 + 实验态度 |
| 实验报告 | 40% | 6 个实验的过程文档与结果 |
| 阶段测试 | 20% | 章节小测（每章 1 次，共 5 次） |
| 综合考核 | 30% | exp06 多模态 VLM 综合项目答辩 |

### 6.2 考核标准

#### 实验报告评分标准
| 等级 | 分数 | 标准 |
|-----|------|------|
| 优秀 | 36-40 | 步骤完整，结果正确，有创新（如自研误唤醒抑制策略） |
| 良好 | 28-35 | 步骤完整，结果正确 |
| 一般 | 24-27 | 步骤较完整，有小错误 |
| 较差 | <24 | 步骤缺失，错误较多 |

#### 综合项目评分标准
| 等级 | 分数 | 标准 |
|-----|------|------|
| 优秀 | 27-30 | 多模态闭环 < 3s 延迟（VLM），含语音提问+图像理解+TTS 播报完整链路 |
| 良好 | 22-26 | 闭环功能完整但延迟偏高 |
| 一般 | 18-21 | 闭环部分功能缺失 |
| 较差 | <18 | 闭环未跑通 |

---

## 七、参考资源

### 7.1 教材
1. 《Speech and Language Processing》（第 3 版，Jurafsky & Martin）— 覆盖 ASR/TTS/NLP 原理
2. 《ROS2 机器人开发实践》（胡春旭）— ROS2 节点/Launch/参数化基础

### 7.2 参考资料
1. sherpa-onnx 官方文档：https://k2-fsa.github.io/sherpa/onnx/
2. k2-fsa GitHub：https://github.com/k2-fsa/sherpa-onnx
3. OpenAI Chat Completions API 文档
4. RKLLM 工具链手册（瑞芯微官方）

### 7.3 工具软件
- Ubuntu 22.04 + ROS2 Humble
- sherpa-onnx Python 包（v1.10+）
- Python 3.10 + rclpy
- librkllmrt.so + RKLLM Runtime

---

## 八、先修课程

| 课程名称 | 要求程度 |
|---------|---------|
| Python 编程 | 必须 |
| 深度学习基础 | 必须 |
| 边缘计算基础 | 必须 |
| 机器人 ROS2 应用与开发（建议） | 建议 |
| 操作系统（Linux） | 建议 |

---

## 九、教学设备

| 设备名称 | 数量/组 | 用途 |
|---------|--------|------|
| 具身智能实验箱 B2（含 6 麦阵列 + 摄像头） | 1 台/人 | 语音采集、播放、视觉输入 |
| 具身智能机器人小车 C1 | 1 台/组（4 人） | 端到端语音交互演示 |
| 麦克风阵列开发板 | 1 套/人 | KWS 调参实验 |
| 工作站（Ubuntu 22.04 + ROS2 Humble） | 1 台/人 | 节点开发与部署 |
| RKLLM NPU 推理服务器 | 1 台/组 | 大模型 Function Calling + VLM |

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-06-11 | 初始化 |
| v3.0 | 2026-06-21 | 完成全部 7 实验覆盖 |
| v3.1 | 2026-08-04 | 对齐 CSV 中 EXP002 更新（sherpa-onnx + Function Calling + VLM 三栈合一），扩 5 章 32h 全实验设计
| v3.2 | 2026-08-05 | 移除第1章（环境搭建），重命名 2-5→1-4，实验 1-7→1-6，总学时 32h→28h |
v3.3 | 2026-08-05 | 第2章重构:教学内容/重点难点/教学活动/对应知识点全量替换为asr_test.py 7模块拆解;实验2关联知识点 2.0.1~2.5.2 与 experiment-2.md 同步 |