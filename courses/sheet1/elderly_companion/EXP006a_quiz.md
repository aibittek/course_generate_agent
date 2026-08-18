---
course_code: EXP006a
course_name: 机器人大模型综合应用开发（老人跌倒监护项目）
version: v1.0
generated_at: 2026-08-18
generator: QuizAgent
mode: standard
source_spec: courses/sheet1/elderly_companion/_meta/course-spec.yaml
source_knowledge_graph: courses/sheet1/elderly_companion/EXP006a_knowledge_graph.md
source_syllabus: courses/sheet1/elderly_companion/EXP006a_syllabus.md
source_lab_guide: courses/sheet1/elderly_companion/EXP006a_lab_guide.md
csv_sha256: 25bbf32ee1338458fb35907cc9fd3786a6b833d8cb75b5f9f163ad0a87ccdbc4
---

# 机器人大模型综合应用开发（老人跌倒监护项目）练测题库

> 适用对象: 本科高年级
> 总题目数: 34
> 预计考试时长: 120 分钟
> 模式: 试卷模式（standard）
> 版本: v1.0
> 制定日期: 2026-08-18

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
| 困难 | 7 | 21% | 综合设计、跨节点编排、安全机制分析 |

### 知识点覆盖率

- 知识图谱总知识点数: 39（6 章 13 节，知识点编号 1.1.1 ~ 6.2.3，详见 `EXP006a_knowledge_graph.md`）
- 本套题显式覆盖知识点数: 39（100%，即 39/39）
- 题型设计原则：知识点编号严格取自知识图谱；单选/多选按章节组织（第 1~6 章），简答题 4 道与编程题 2 道统一置于卷末
- 涉及源码事实（参数值、接口名、命令）均与 `EXP006a_lab_guide.md` 及 `config/fall_config.yaml` 一致，如躯干角>50°、宽高比<0.5、12s超时、cooldown 60s、0xAA 0x55 CRC8、model.vlm.enabled、`python3 apps/fall_video_demo.py --video testdata/fall_slow_x264.mp4 --text` 等

### 章节-知识点-题目覆盖一览

| 章节 | 知识点编号（标签显式） | 解析引用 | 对应题号 |
|------|----------------------|---------|----------|
| 第 1 章 项目需求与系统架构 | 1.1.1 / 1.1.2 / 1.1.3 / 1.2.1 / 1.2.2 / 1.2.3 / 1.3.1 / 1.3.2 / 1.3.3 | — | 单选 1-4、多选 1 |
| 第 2 章 配置与调试体系 | 2.1.1 / 2.1.2 / 2.1.3 / 2.2.1 / 2.2.2 / 2.2.3 | — | 单选 5-7、多选 2 |
| 第 3 章 语音交互 | 3.1.1 / 3.1.2 / 3.1.3 / 3.2.1 / 3.2.2 / 3.2.3 | — | 单选 8-10、多选 3-4 |
| 第 4 章 视觉检测与姿态估计 | 4.1.1 / 4.1.2 / 4.1.3 / 4.2.1 / 4.2.2 / 4.2.3 | — | 单选 11-13、多选 5-6 |
| 第 5 章 跌倒判定与告警证据 | 5.1.1 / 5.1.2 / 5.1.3 / 5.2.1 / 5.2.2 / 5.2.3 | — | 单选 14-16、多选 7（另 5.2.2 由第6章单选 20 覆盖） |
| 第 6 章 大模型与系统验证 | 6.1.1 / 6.1.2 / 6.1.3 / 6.2.1 / 6.2.2 / 6.2.3 | — | 单选 17-20、多选 8 |
| 简答题 | 1.1.3 / 1.3.1 / 3.1.1 / 3.1.2 / 3.2.2 / 5.1.2 / 5.1.3 / 6.2.1 / 6.2.2 | — | 简答 1-4 |
| 编程题 | 2.2.1 / 2.2.3 / 5.1.2 / 6.2.3 | — | 编程 1-2 |

---

## 第 1 章 项目需求与系统架构

### 一、单项选择题（每题 2 分）

**1. [知识点 1.1.1, 1.1.2, 1.2.2]** 老人跌倒监护系统 R1-R12 需求体系中，R4 跌倒判定的三个几何特征阈值分别是？

A. 躯干角 > 30°、宽高比 < 0.8、髋部速度 > 0.1 倍框高
B. 躯干角 > 50°、宽高比 < 0.5、髋部速度尖峰（> 0.25 倍框高）
C. 躯干角 > 60°、宽高比 < 0.4、肩部速度 > 0.3 倍框高
D. 躯干角 > 45°、宽高比 < 0.6、重心速度 > 0.2 倍框高

**答案**: B
**解析**: R4 定义三个可量化判定条件：躯干角 > 50°（肩中点到髋中点连线与竖直方向夹角）、检测框宽高比 < 0.5（框宽是高两倍以上才算"躺"）、髋部速度尖峰（髋中点帧间像素位移 > 0.25 × bbox_h）。三个信号中"躺姿形态"（角+宽高比）是必要条件，"速度尖峰"是触发条件——避免弯腰捡物等静止低姿态误报（1.1.2 跌倒→ASK→ALERT 流程）。该判定处于视觉流水线末端（1.2.2 YOLO→IoU→姿态→特征→状态机），对应 `fall/state_machine.py L100-L115`。

---

**2. [知识点 1.1.2]** 跌倒检测触发 ASK 询问后，用户回复"没事/不用"会导致状态机进入哪个状态？

A. FALLING
B. IDLE
C. CANCELLED
D. LYING

**答案**: C
**解析**: ASK 窗口中，`classify_response`（`fall/interaction.py L12-L22`）先匹配 `confirm_words`（救命/帮/疼等）→ ALERT，再匹配 `cancel_words`（没事/不用/还好等）→ CANCELLED。CANCELLED 后 TTS 播报"好的，请注意安全"，蜂鸣器停止，进入 cooldown 60s。

---

**3. [知识点 1.1.3]** ASK 会话超时兜底的时间阈值是多少？超时后系统如何处理？

A. 8s，静默重播 ask
B. 10s，回到 IDLE
C. 12s，自动升级为 ALERT
D. 15s，关闭 ASK 窗口

**答案**: C
**解析**: ASK 会话超时阈值为 12s（`config/fall_config.yaml state.ask_timeout`）。若 12s 内无语音应答，`state_machine.py` 的 `_is_ask_timeout` 判定为真，自动从 ASK 转为 ALERT，确保老人跌倒后即使无法应答也能触发告警。与"重问 8s"（`ask_retry_interval`）是两类独立机制。

---

**4. [知识点 1.2.1, 1.2.2, 1.2.3, 1.3.2]** 关于五层模块架构与核心流水线，下列描述正确的是？

A. vision 层负责 YOLO→IoU→姿态估计→几何特征的视觉流水线，fall 层负责六状态机判定与告警
B. speech 层使用三状态机（IDLE/LISTENING/SPEAKING）+ 单录音线程 + 消息队列架构
C. common 层的 FrameSource 抽象统一了 image/video/ROS camera 三种输入源，业务代码零改动
D. 以上三项都正确

**答案**: D
**解析**: A 对应视觉流水线（1.2.2：YOLO 检测→IoU 跨帧关联→姿态估计→几何特征→状态机判定）；B 对应语音架构（1.2.3：单状态机 IDLE/LISTENING/SPEAKING + 单录音线程 + 消息队列路由）；C 对应 FrameSource 多输入源抽象（1.3.2：image/video/ROS camera 三种数据源统一，config 或 CLI 切换，业务代码零改动）。五层模块（1.2.1）为 apps/common/vision/fall/speech + llm。

---

### 二、多项选择题（每题 4 分）

**1. [知识点 1.3.1, 1.3.3]** 关于 monitor 与 VoiceLoop 三接口解耦及文本模式，正确的描述有？

A. 三个接口为 on_kws、on_asr、has_ask_session，monitor 通过它们与语音层交互而非直接调用语音内部函数
B. 文本模式（--text）与音频模式走完全相同的状态机与回调链，因此文本模式验证过的状态迁移在音频模式必然成立
C. 三接口解耦使得视觉判定（fall 层）和语音交互（speech 层）可以独立开发、独立测试
D. 文本模式下所有音频组件（KWS、ASR、TTS）被完全禁用，stdin 文本直接喂入状态机

**答案**: ABCD
**解析**: A 对应三接口解耦设计（`monitor` 通过 `on_kws/on_asr/has_ask_session` 与 VoiceLoop 交互）；B 对应 `voice_loop.py feed_text` 方法设计——文本模式与音频模式同一路由（`voice_loop.py L85-L103`）；C 对应解耦收益——fall 层和 speech 层并行独立；D 对应文本模式实现——KWS/ASR/TTS 被禁用，stdin 替代麦克风。

---

## 第 2 章 配置与调试体系

### 一、单项选择题（每题 2 分）

**5. [知识点 2.1.1, 2.1.2]** config_schema 在系统启动时执行什么操作？

A. 运行时动态监听配置变更
B. 对 fall_config.yaml 执行强制键校验与类型检查，不合法则启动失败
C. 自动修复缺失的配置项并写回 yaml 文件
D. 将 yaml 配置同步到 ROS2 参数服务器

**答案**: B
**解析**: `config_schema.py` 的 `REQUIRED` 字典定义了所有必需键及其类型。启动时 `env_check.py`（`L25`）调用 schema 校验——缺少必需键或类型不匹配时打印 `[env] FAIL config_schema` 并以 `exit 2` 退出，防止在残缺配置下启动导致运行时崩溃。设计原则是"绝不自动修复"，由用户解决。

---

**6. [知识点 2.1.3]** CLI 传参与配置文件同时指定时，优先级从高到低的正确顺序是？

A. 默认值 > yaml 文件 > 命令行参数
B. yaml 文件 > 命令行参数 > 默认值
C. 命令行参数 > yaml 文件 > 默认值
D. 命令行参数 > 默认值 > yaml 文件

**答案**: C
**解析**: 配置覆盖规则：命令行参数（CLI）> yaml 文件 > 默认值。例如 `--video test.mp4 --text` 会覆盖 yaml 中的 source 和 speech.text_mode 设置。CLI 参数在 `apps/` 入口的 `_merge_args` 中合并到 `cfg` dict，yaml 文件的值被覆盖。

---

**7. [知识点 2.2.1, 2.2.2, 2.2.3]** 关于三级开发模式与环境自检，下列描述正确的是？

A. 文本→音频→摄像头三级递进验证降低了硬件依赖（2.2.1），文本模式无需任何硬件即可验证状态机
B. env_check.py 检查三类资源：Python 依赖库、模型/资源文件、config_schema 键校验（2.2.2）
C. 运行产物（runs/ 下截图、.avi、events.jsonl、日志）均不入库，实验结束后需资源清理（2.2.3）
D. 以上三项都正确

**答案**: D
**解析**: A 对应三级开发模式（2.2.1：文本→音频→摄像头递进验证，`docs/03_开发模式与验证.md L5-L14`）；B 对应 env_check 三类资源检查（2.2.2：`env_check.py L32-L112`，"绝不自动安装"原则）；C 对应运行产物管理（2.2.3：runs/ gitignore 不入库，pkill 清理残留进程）。

---

### 二、多项选择题（每题 4 分）

**2. [知识点 2.2.1, 2.2.3]** 关于三级开发模式与运行产物管理，正确的有？

A. 文本→音频→摄像头三级递进验证降低了硬件依赖，文本模式可完全离线验证状态机逻辑
B. 运行产物（runs/ 目录下的截图、.avi 视频、events.jsonl、日志）均不入库，需定期清理释放磁盘
C. 摄像头实时模式需先启动 ROS2 相机节点，再启动 fall_app.py --mode camera
D. 音频模式启动前必须 pkill -9 aplay 清理残留播放进程，否则播报无声

**答案**: ABCD
**解析**: A 对应三级开发模式设计（`docs/03_开发模式与验证.md L5-L14`）；B 对应 runs/ 目录 gitignore 规则与证据视频快速增长的清理需求；C 对应实时模式时序（`docs/06_环境依赖.md L69-L70`：先 `ros2 launch depth_camera`，再 `fall_app`）；D 对应音频设备冲突预防（`plughw:3,0` 被残留 aplay 进程占用会导致新播报无声）。

---

## 第 3 章 语音交互

### 一、单项选择题（每题 2 分）

**8. [知识点 3.1.1, 3.1.2]** XFM 六麦阵列硬件唤醒通过什么协议输出唤醒事件信息？

A. ROS2 话题发布，消息类型 std_msgs/String
B. USB 串口 AIUI 事件（msg_type=0x04），提取 beam/angle/keyword
C. HTTP Webhook 回调
D. 蓝牙 BLE 广播

**答案**: B
**解析**: XFM 六麦通过串口（`/dev/ttyACM0`）使用 AIUI 协议通信（3.1.1 硬件唤醒）：`receive_loop()` 按 `0xA5` 同步头拆帧，`msg_type=0x04` 的设备消息中 JSON payload 含 `type=aiui_event` 且 `eventType=4` 时即为唤醒事件，提取 `ivw.beam`（声束方向）、`ivw.angle`（角度）、`ivw.keyword`（唤醒词）。软件 KWS（3.1.2）基于 sherpa-onnx KeywordSpotter 引擎本地离线运行，作为硬件唤醒的降级备份。

---

**9. [知识点 3.1.3]** 流式 ASR 的端点检测 rule1 静音阈值是多少？rule2 又是多少？

A. rule1 = 2s 静音、rule2 = 1s 静音
B. rule1 = 4.5s 静音、rule2 = 1.5s 短静音
C. rule1 = 3s 静音、rule2 = 2s 短静音
D. rule1 = 6s 静音、rule2 = 3s 短静音

**答案**: B
**解析**: ASR 基于 sherpa_onnx.OnlineRecognizer 的三规则端点检测：rule1=4.5s 静音（长静音判终止）、rule2=1.5s 短静音（短句终止）、rule3=300ms 极短持续（单字终止）。VoiceLoop 在 LISTENING 态每帧调用 `asr.feed(stream, chunk)` 返回 `(partial, final)`，final 在端点检测命中时非 None。对应 `speech/asr.py L48-L62`。

---

**10. [知识点 3.2.1]** TTS 预合成缓存的设计目的是什么？如何实现零合成延迟？

A. 运行时实时合成所有文本，缓存仅用于网络传输加速
B. 固定提示语在启动前预合成并缓存到内存（和磁盘），运行时查缓存直接播放，省去约 1s/句合成耗时
C. 用云端 TTS 服务预下载音频文件
D. 通过 ROS2 参数服务器预注册音频片段

**答案**: B
**解析**: Matcha-TTS + Vocos 固定提示语（如"您还好吗？需要帮助吗？"）在启动时通过 `pre_synthesize()` 预合成 PCM 并缓存到 `_pcm_cache` 字典（内存）和 MD5 索引的 `.raw` 文件（磁盘），运行时 `say()` 先查缓存命中直接播放，实现零合成延迟输出。动态文本（LLM 回复）仍实时合成。对应 `speech/tts.py L204-L255`。

---

### 二、多项选择题（每题 4 分）

**3. [知识点 3.2.2]** 关于唤醒后启动录音与双次排空防回声，正确的描述有？

A. XFM 硬件唤醒场景下，提前打开 ALSA 设备会导致设备停在监听态输出稀疏帧，唤醒后也不恢复
B. 录音线程在 `notify_wake()` 被调用后才真正启动（`_cap_started` 幂等保护）
C. 双次排空是在 TTS 播报结束后连续执行两次 `_drain_q()`（中间 sleep 0.2s），确保残留帧被清空
D. 软件 KWS 场景下录音线程在 `run()` 中常开，不需要唤醒后才启动

**答案**: ABCD
**解析**: A 对应 XFM 时序约束（`voice_loop.py L125-L143` 文档注释）；B 对应 `_ensure_capture()` 幂等设计——仅在 `notify_wake()` 后才真正启动录音线程；C 对应双次排空实现（`voice_loop.py L262-L275`：两次 `_drain_q()` + sleep 0.2s + reset KWS 流）；D 对应软件 KWS 场景差异——录音线程在 `run()` 中常开。

---

**4. [知识点 3.1.3, 3.2.3]** 关于 ASK 应答窗口管控，正确的描述有？

A. ASK 端点检测使用 4.5s 静音规则作为长静音终止条件
B. 当 partial 非空且 2s 无变化时，系统强制提交 ASR 结果（2s 快答兜底）
C. on_asr 中对首个响应 break，确保一次应答只作用于一个 ASK 会话，防重复告警
D. ASK 超时 12s 后自动升级 ALERT，用户在超时后仍可输入"没事"取消告警

**答案**: ABC
**解析**: A 对应 ASR 端点检测 rule1=4.5s（`speech/asr.py L54`）；B 对应 2s 快答兜底机制——partial 非空且 2s 无变化则强制提交（`docs/05_流程与安全.md` 时序防护第 3 条）；C 对应单次应答防重复（`monitor.py L206-L208`：break 后不再遍历）；D 错误——12s 超时后自动进入 ALERT，超时后再输入"没事"是在 ALERT 态的窄表取消（仅匹配"没事/不用"），而非取消 ASK。

---

## 第 4 章 视觉检测与姿态估计

### 一、单项选择题（每题 2 分）

**11. [知识点 4.1.1]** YOLOv8n 行人检测模型的输入分辨率和数据集类别分别是？

A. 320×320，VOC 20 类
B. 640×640，COCO person 类（class_id=0）
C. 416×416，ImageNet 1000 类
D. 1280×1280，自定义老人数据集

**答案**: B
**解析**: 本项目使用 yolov8n（nano 版本），经 RKNN 工具链转换为 .rknn 格式，输入为 640×640 RGB 图像，仅保留 COCO 数据集的 person 类（class_id=0）。nano 版本选择原因：RK3576 仅 6TOPS 算力，nano 推理延迟约 30-50ms 满足实时性要求。

---

**12. [知识点 4.1.3]** RKNN NPU 推理中，core_mask 参数设置为 0 代表什么含义？

A. 使用 CPU 推理，不启用 NPU
B. NPU_CORE_AUTO，自动分配 NPU 核
C. 仅使用 CORE_0
D. 使用双核 CORE_0_1

**答案**: B
**解析**: `RKNNLiteBackend` 封装了 rknnlite2.3.2 板端推理 API，core_mask 控制 NPU 核分配：0=NPU_CORE_AUTO（自动，推荐）、1=CORE_0、2=CORE_1、3=CORE_0_1（双核）。RK3576 仅 2 个 NPU 核，多核轮转意义有限，实测 core_mask=None 会报错，因此默认使用 0。对应 `vision/yolo/backend.py L19-33`。

---

**13. [知识点 4.2.2]** RTMPose 17 关键点使用什么解码方式输出像素坐标？

A. 直接回归 x/y/z 三轴坐标值
B. SimCC 双头 argmax 除以 split_ratio（2.0）得到像素坐标
C. 关键点热力图峰值检测 + 亚像素插值
D. 角度回归 + 正向运动学解算

**答案**: B
**解析**: RTMPose-s 采用 SimCC（Simulated Coordinate Classification）双头解码：输出 simcc_x shape (1,17,384) + simcc_y shape (1,17,512)，384=W(192)×2、512=H(256)×2，split_ratio=2.0。解码时对每个关键点取 x/y 头的 argmax 索引除以 2.0 得到输入图像素坐标。visibility 计算为双头响应峰值均值。对应 `vision/pose_rtm/simcc.py L17-63`。

---

### 二、多项选择题（每题 4 分）

**5. [知识点 4.1.2]** 关于 letterbox 预处理与 NMS 后处理，正确的描述有？

A. letterbox 将原图等比缩放至 640×640 并居中补黑边，返回缩放比 scale 和补边像素
B. NMS（非极大值抑制）使用逐类处理方式，IoU 阈值默认 0.45 去除重叠框
C. unletterbox 通过 `(xyxy - pad) / scale` 逆映射回原图空间
D. DFL 解码对 64-bin logits 做 softmax 加权得到精确偏移

**答案**: ABCD
**解析**: A 对应 letterbox 预处理（`vision/yolo/preprocess.py L18-29`）；B 对应逐类 NMS（`postprocess_detect.py L63-75`：classwise_nms，IoU 阈值默认 0.45）；C 对应 unletterbox 逆映射（`preprocess.py L41-53`）；D 对应 DFL 解码（`postprocess_detect.py L38-45`：softmax@16 bins）。四个描述均为 YOLO 推理链路的真实步骤。

---

**6. [知识点 4.2.1, 4.2.3]** 关于检测/姿态双后端切换与 MJPEG 推流，正确的描述有？

A. pose_type 配置切换 blazepose（33pt）或 rtmpose（17pt），切换只需改 YAML 不需改代码
B. MJPEG 推流通过 MjpegServer 封装 mjpeg_streamer 库，流地址为 http://<IP>:8088/fall.mjpg
C. MJPEG 启动时会预检端口是否已被占用，避免静默 404
D. 两个姿态引擎接口对齐——process(frame_bgr) -> PoseResult，PoseResult 均包含 .landmarks 和 .score

**答案**: ABCD
**解析**: A 对应 YAML 配置切换（`apps/pose_demo.py L54-59`：build_pose_engine 按 pose_type 创建）；B 对应 MJPEG 推流地址（`vision/yolo/mjpeg_server.py`）；C 对应端口预检（`mjpeg_server.py L74-87`：start() 中 socket 连接预检）；D 对应双引擎接口对齐（PoseResult 统一结构）。

---

## 第 5 章 跌倒判定与告警证据

### 一、单项选择题（每题 2 分）

**14. [知识点 5.1.1]** 跌倒判定中"髋部速度尖峰"的触发阈值是？

A. 髋中点帧间位移 > 0.1 × bbox_h
B. 髋中点帧间位移 > 0.25 × bbox_h
C. 重心帧间位移 > 0.5 × bbox_h
D. 肩部帧间位移 > 0.3 × bbox_h

**答案**: B
**解析**: 髋部速度尖峰（hip_speed）= 髋中点帧间像素位移，阈值为 0.25 × bbox_h（框高的 25%）。判定逻辑在 `_speed_ok`（`state_machine.py L117-L125`）中实现：`hip_speed > factor × bh` 或 `center_y_speed > factor × bh`，其中 `speed_factor` 默认 0.25。

---

**15. [知识点 5.1.2]** 六状态机中 FALLING→LYING 的转移条件是什么？

A. 持续满足躺姿判定超过 3.0s
B. 持续满足 `_is_lying(f)` 超过 falling_window（默认 1.5s）
C. 用户语音确认"摔倒了"
D. 躯干角连续 3 帧超过 50°

**答案**: B
**解析**: FALLING→LYING 转移条件：持续满足 `_is_lying(f)` 超过 `falling_window`（默认 1.5s），即"确实躺了"。若 1.5s+2s 内未满足则回 IDLE（误触发），对应 `state_machine.py L176-L178`。LYING→ASK 还需再等 `lying_time`（默认 3.0s）。

---

**16. [知识点 5.2.3]** MJPEG 实时推流默认端口是？如何访问推流画面？

A. 端口 8080，浏览器访问 http://<IP>:8080/stream
B. 端口 8088，浏览器访问 http://<IP>:8088/fall.mjpg
C. 端口 3000，浏览器访问 http://<IP>:3000/video
D. 端口 5000，浏览器访问 http://<IP>:5000/mjpeg

**答案**: B
**解析**: MJPEG 推流默认端口 8088（`config/fall_config.yaml server.port`），流地址 `http://<IP>:8088/fall.mjpg`。MjpegServer 封装 mjpeg_streamer 库，使用 daemon 线程运行 aiohttp 服务，stop() 时吞掉 GracefulExit 异常避免崩溃。端口 8088 与 LLM 服务端口 8080 不能冲突。

---

### 二、多项选择题（每题 4 分）

**7. [知识点 5.1.3, 5.2.1]** 关于 IoU 跨帧关联与 STM32 告警协议，正确的描述有？

A. IoU 关联使用贪心匹配算法，IoU ≥ 0.3 才关联同一 person_id，丢失超过 3s 的轨迹释放 ID
B. cooldown 60s 在 ALERT 触发后生效，期间同一 person 不会重复触发 ASK
C. STM32 串口告警帧格式为 0xAA 0x55 帧头 + Func + Len + Data + CRC8，CRC8 范围从帧头开始校验
D. 蜂鸣器帧 Data 为 4 个 uint16（频率Hz、响时ms、停时ms、重复次数），波特率 1Mbps

**答案**: ABD
**解析**: A 对应 IoU 贪心关联（`fall/assoc.py L48-L70`：IoU ≥ 0.3 关联、max_age=3s 释放）；B 对应 cooldown 设计（`state_machine.py L189-L190`：LYING→ASK 前检查 `_cooldown_until`）；C 错误——CRC8 校验范围从 Func 开始到 Data 末尾，**不包含**帧头 `0xAA 0x55`（`build_frame L44-47`：`checksum_crc8(payload)` 中 `payload = bytes([func, len(data)]) + data`）；D 对应蜂鸣器帧结构（`stm32_protocol.py L50-56`：`struct.pack("<HHHH", freq, on_ms, off_ms, repeat)`）。

---

## 第 6 章 大模型与系统验证

### 一、单项选择题（每题 2 分）

**17. [知识点 6.1.1]** RKLLM 本地推理使用什么动态库加载方式？

A. importlib 动态导入 Python 模块
B. ctypes.CDLL 加载 /usr/lib/librkllmrt.so
C. subprocess.Popen 调用外部命令行工具
D. ROS2 pluginlib 插件加载机制

**答案**: B
**解析**: RKLLM 通过 `ctypes.CDLL('/usr/lib/librkllmrt.so')` 加载 C++ 动态库（`llm/llm_server.py L15-L16`），在 RK3576 的 6TOPS NPU 上运行量化后的 Qwen3.5-0.8B 模型。推理采用回调机制：C++ 侧逐 token 触发 `callback_impl`，Python 侧累积输出。

---

**18. [知识点 6.1.2, 6.1.3]** server_manager 的端口预检策略是从哪个端口开始递增尝试？

A. 从端口 3000 开始
B. 从端口 8080 开始，递增 20 个端口
C. 从端口 5000 开始
D. 随机端口

**答案**: B
**解析**: `LLMServerManager.pick_free_port(start=8080, tries=20)` 从 8080 端口递增尝试绑定（`llm/server_manager.py L33-L40`），找空闲端口。若端口已有服务，还会验证是否为兼容的 RKLLM 服务（GET `/v1/models`）。退出清理（`stop()`）仅终止自己拉起的子进程。

---

**19. [知识点 6.2.1]** VLM 视觉复核默认为什么状态？主要原因是什么？

A. 默认开启，因为需要实时复核所有跌倒检测结果
B. 默认关闭（vlm.enabled: false），因为 VLM 模型额外占用约 1.3G 内存，RK3576 板端内存紧张
C. 默认关闭，因为 VLM 推理速度太慢无法满足实时要求
D. 默认开启，但仅在多人场景下使用

**答案**: B
**解析**: VLM 视觉复核（`vision_judge`）默认关闭（`config/fall_config.yaml model.vlm.enabled: false`），因为 VLM 模型额外占用约 1.3G 内存，LLM 约 1.5G，总计约 3.0G+，RK3576 板端 RAM 有限（2G/4G），开启后可能导致 OOM。关闭时使用 `FakeVisionJudge` 返回 `uncertain`，不改变主流程。

---

**20. [知识点 5.2.2, 6.2.3]** 全链路闭环验证的六个阶段顺序正确的是？

A. 对话→唤醒→跌倒→告警→询问→存档
B. 唤醒→对话→跌倒→询问→应答→告警+存档
C. 唤醒→跌倒→对话→存档→应答→告警
D. 跌倒→唤醒→询问→对话→存档→应答

**答案**: B
**解析**: 全链路闭环验证（`docs/03_开发模式与验证.md`）六个阶段：① 唤醒（小飞小飞）→ ② 对话（你好→LLM回复）→ ③ 跌倒（视频自动触发 FALLING→LYING→ASK）→ ④ 询问（播"您还好吗？"→开听）→ ⑤ 应答（救命→ALERT / 没事→CANCELLED）→ ⑥ 告警+存档（STM32 声光 + runs/evidence/）。

---

### 二、多项选择题（每题 4 分）

**8. [知识点 6.1.3, 6.2.2, 6.2.3]** 关于 server_manager 子进程管理与跌倒判定/LLM 并存路由，正确的描述有？

A. server_manager 退出清理仅终止自己拉起的子进程（stop()），不干扰外部复用的服务
B. 跌倒判定与 LLM 对话通过 monitor 的三接口（on_kws/on_asr/has_ask_session）实现路由分离
C. ALERT 态下告警 TTS 循环播报（默认 10s 间隔），LLM 对话请求被排队等待——告警优先级高于闲聊
D. 全链路验证中，文本模式（--text）与音频模式走完全相同的状态机，因此文本模式验证的闭环在音频模式必然成立

**答案**: ABCD
**解析**: A 对应 server_manager 清理设计（`server_manager.py L113-125`：terminate→wait→kill 三级清理，仅终止 `self._proc`）；B 对应三接口路由分离（fall 层通过 on_kws/on_asr/has_ask_session 与 speech 层交互）；C 对应告警优先级——ALERT 时 TTS 循环播报（`alert_tts_interval=10s`），LLM 回复被 TTS 设备（plughw:3,0）串行化；D 对应文本模式等价性——同一状态机与回调链。

---

## 三、简答题（每题 5 分）

**1. [知识点 1.1.3, 1.3.1, 3.2.2]** 时序防护中"ASK 开听晚于 ask 播完"与"双次排空防回声"分别解决什么问题？如果省去任一防护，会导致什么具体故障？

**参考答案**:
1. "ASK 开听晚于 ask 播完"：`trigger_ask` 在 TTS 播报"您还好吗？"完成后才将 ASR 流打开（`trigger_ask` 等 `playback_event` set→clear），防止 ASR 把 ask 播报的回声误判为用户应答。若省去，ASR 会在 ask 播报期间就开始监听，TTS 输出经扬声器反射回麦克风被识别为"救命"等词，导致误触发 ALERT 告警。
2. "双次排空防回声"：TTS 播报结束后，`_handle_speaking` 连续执行两次 `_drain_q()`（中间 sleep 0.2s），确保录音队列中残留的 TTS 音频帧被完全清空，并 reset KWS 流。若省去，残留帧会被 KWS 引擎处理，可能误判为唤醒词（如将 TTS 音频误识为"小飞小飞"），导致在 SPEAKING 态下错误触发新唤醒。

**评分标准**: 要点完整 5 分 / 较完整 3-4 分 / 部分 1-2 分 / 错误 0 分（两个防护各解决什么问题 2 分，省去后具体故障 2 分，源码机制描述 1 分）。

---

**2. [知识点 5.1.2, 5.1.3]** 跌倒判定六状态机中 FALLING→LYING→ASK 的流转时间窗口分别是多少？cooldown 60s 的作用是什么？冷却期内如果用户再次跌倒，系统如何处理？

**参考答案**:
1. 流转时间窗口：IDLE→FALLING（形态+速度双条件同时满足，`_is_lying` 且 `_speed_ok`）→ 持续满足 `_is_lying` 超过 falling_window（默认 1.5s）→ LYING → 持续躺地超过 lying_time（默认 3.0s）→ ASK。总确认时间约 4.5s（1.5s+3s），防止短暂弯腰/蹲姿误报。若 1.5s+2s 内未持续满足则回 IDLE。
2. cooldown 60s 作用：ASK 触发后进入冷却期，期间同一 person_id 不会再次触发 ASK（`state_machine.py L189-190`：`if now < self._cooldown_until: return None`），避免同一跌倒事件重复告警。
3. 冷却期只挡 ASK，不挡新跌倒——若 60s 内用户再次跌倒（形态+速度双条件满足），可重新进入 FALLING→LYING→ASK 全流程（`state_machine.py L215-L220`），确保真正的二次跌倒不被忽略。

**评分标准**: 要点完整 5 分 / 较完整 3-4 分 / 部分 1-2 分 / 错误 0 分（时间窗口 2 分，cooldown 作用 1 分，冷却期与新跌倒关系 2 分）。

---

**3. [知识点 6.2.1, 6.2.2]** VLM 视觉复核在跌倒判定中扮演什么角色？为什么默认关闭？开启后对系统有什么影响？

**参考答案**:
1. 角色：VLM（Vision-Language Model）是跌倒判定的"二审"机制。当几何特征（躯干角>50°/宽高比<0.5）判定跌倒后，VLM 通过多模态大模型对裁剪帧进行"是/否摔倒"的语义判断，输出 label=fall/not_fall/uncertain + confidence + reason，用于降低误报率。
2. 默认关闭原因：VLM 模型额外占用约 1.3G 内存，LLM 约 1.5G，总计约 3.0G+，RK3576 板端 RAM 有限（2G/4G），开启后可能导致 OOM。关闭时使用 `FakeVisionJudge` 返回 `uncertain`，不改变主流程。
3. 开启后影响：首次 judge 时懒加载约 10-60s（`RKLLMVisionJudge._load()`），之后复用已加载模型。需要修改 `config/fall_config.yaml` 中 `model.vlm.enabled: true`，测试完成后必须改回 `false`。

**评分标准**: 要点完整 5 分 / 较完整 3-4 分 / 部分 1-2 分 / 错误 0 分（二审角色 2 分，内存原因 2 分，懒加载与开关操作 1 分）。

---

**4. [知识点 3.1.1, 3.1.2, 3.2.2]** 请简述从 XFM 硬件唤醒到 TTS 播报"您还好吗？"的完整语音链路，以及其中"唤醒后启动录音"和"双次排空防回声"两个关键时序约束的设计原因。

**参考答案**:
1. 完整语音链路：XFM 六麦阵列检测到唤醒词 → AIUI 串口事件（msg_type=0x04）触发 → `notify_wake()` 启动录音线程（ALSA plughw:4,0）→ 提示音播放 → ASR 流式识别（zipformer 增量解码）→ 文本送入 LLM 或状态机 → TTS 播报（Matcha-TTS + Vocos 预合成缓存零延迟）。
2. "唤醒后启动录音"原因：XFM 硬件在监听态不上送音频流——提前打开 ALSA 设备会导致设备停在监听态输出稀疏帧，唤醒后也不恢复。因此 `_ensure_capture()` 仅在 `notify_wake()` 被调用后才真正启动录音线程（`_cap_started` 幂等保护）。软件 KWS 场景下录音线程在 `run()` 中常开，无需此约束。
3. "双次排空防回声"原因：TTS 播报结束后，录音队列中残留 TTS 音频帧可能被 KWS 引擎误判为唤醒词。`_handle_speaking` 连续执行两次 `_drain_q()`（中间 sleep 0.2s）确保残留帧被完全清空，并 reset KWS 流，避免 SPEAKING 态下错误触发新唤醒。

**评分标准**: 要点完整 5 分 / 较完整 3-4 分 / 部分 1-2 分 / 错误 0 分（完整链路 2 分，唤醒后启动录音原因 2 分，双次排空原因 1 分）。

---

## 四、编程题（每题 4 分）

**1. [知识点 5.1.2, 6.2.3] 关联实验 6、实验 9**

**题目描述**:

基于实验 6"跌倒判定集成测试"与实验 9"全功能快速验证"的内容，编写一个 Bash 脚本 `verify_fall_chain.sh`，要求：
1. 启动 fall_video_demo 文本模式全链路（`python3 apps/fall_video_demo.py --video testdata/fall_slow_x264.mp4 --text`），后台运行并将日志写入文件；
2. 等待系统就绪后，通过 stdin 依次发送"小飞小飞"（唤醒）→ 等待视频自动触发跌倒 ASK → 发送"救命"（确认告警）→ 等待 ALERT 状态；
3. 检查 `runs/evidence/` 下是否生成了截图(.jpg)和事件日志(events.jsonl)，验证证据存档完整性；
4. 结束后清理残留进程（pkill -9 aplay 等）。

**参考代码框架**:

```bash
#!/usr/bin/env bash
# verify_fall_chain.sh - 跌倒判定→告警→证据全链路验证（关联实验6/9）
set -u

LOG=verify_fall.log
: > "$LOG"

cd /home/iflytek/ros2_ws/src/xflz_eai_car1/app/elderly_companion

# 1) 启动文本模式全链路（后台运行，日志落盘）
python3 apps/fall_video_demo.py --video testdata/fall_slow_x264.mp4 --text >>"$LOG" 2>&1 &
DEMO_PID=$!
echo "[INFO] fall_video_demo started, pid=$DEMO_PID"

# 2) 等待系统就绪（轮询日志中"全部设备就绪"）
for i in $(seq 1 30); do
    if grep -q "全部设备就绪" "$LOG" 2>/dev/null; then
        echo "[INFO] system ready"; break
    fi
    sleep 2
done

# 3) 模拟交互：唤醒 → 等 ASK → 告警
echo "小飞小飞" > /proc/$DEMO_PID/fd/0 2>/dev/null || true
sleep 3   # 等待视频触发跌倒
echo "救命" > /proc/$DEMO_PID/fd/0 2>/dev/null || true
sleep 5   # 等待证据落盘

# 4) 验证证据完整性
if ls runs/evidence/*.jpg >/dev/null 2>&1 && \
   grep -q "ALERT" runs/evidence/events.jsonl 2>/dev/null; then
    echo "[PASS] evidence files generated"
else
    echo "[FAIL] evidence incomplete"
fi

# 5) 清理残留
kill $DEMO_PID 2>/dev/null
pkill -9 aplay 2>/dev/null
echo "[INFO] finished, check $LOG"
```

**评分标准**:

| 等级 | 分数 | 标准 |
|------|------|------|
| 优秀 | 4 | 启动命令正确、stdin 交互时序合理、证据检查完整（jpg+events.jsonl）、进程清理齐全 |
| 良好 | 3 | 主体流程正确，证据检查或清理略简 |
| 中等 | 2 | 能启动并模拟交互，但缺少证据检查或清理 |
| 及格 | 1 | 仅能启动 fall_video_demo，无交互与验证 |
| 不及格 | 0 | 命令错误或与跌倒监护项目无关 |

---

**2. [知识点 2.2.1, 2.2.3] 关联实验 3、实验 9**

**题目描述**:

基于实验 3"配置与接口设计"的内容，编写一个 Python 脚本 `config_audit.py`，要求：
1. 解析 `config/fall_config.yaml`，列出所有十四段配置键（model/detect/source/speech/state/interaction/alert/evidence/llm/server/vlm/save/text_mode 等），输出每段的键名与默认值；
2. 检查关键阈值是否在合理范围内：state.angle_thr 应在 30-70 之间、state.aspect_thr 应在 0.3-0.8 之间、state.cooldown 应在 30-120 之间，不合规则输出警告；
3. 调用 `python3 common/env_check.py --config config/fall_config.yaml` 验证环境自检是否通过，并打印结果。

**参考代码框架**:

```python
#!/usr/bin/env python3
"""
config_audit.py - 配置审计与环境自检验证（关联实验3/9）
依赖: PyYAML（python3 -m pip install pyyaml 或系统自带）
"""
import sys
import subprocess
import yaml

CONFIG = "config/fall_config.yaml"


def load_config(path=CONFIG):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def audit_config(cfg):
    """列出十四段配置并检查关键阈值范围"""
    print("== 配置段总览 ==")
    for key in sorted(cfg.keys()):
        val = cfg[key]
        if isinstance(val, dict):
            print(f"  {key}: ({len(val)} 项)")
        else:
            print(f"  {key}: {val}")

    # 关键阈值检查
    print("\n== 阈值范围检查 ==")
    state = cfg.get("state", {})
    checks = [
        ("angle_thr", state.get("angle_thr"), 30, 70),
        ("aspect_thr", state.get("aspect_thr"), 0.3, 0.8),
        ("cooldown", state.get("cooldown"), 30, 120),
    ]
    for name, val, lo, hi in checks:
        if val is not None and not (lo <= val <= hi):
            print(f"  [WARN] state.{name}={val} 不在推荐范围 [{lo}, {hi}]")
        else:
            print(f"  [OK] state.{name}={val}")


def run_env_check():
    """调用 env_check.py 验证环境"""
    print("\n== 环境自检 ==")
    result = subprocess.run(
        [sys.executable, "common/env_check.py", "--config", CONFIG],
        capture_output=True, text=True
    )
    print(result.stdout[-500:] if result.stdout else "(无输出)")
    if result.returncode != 0:
        print(f"[FAIL] env_check 退出码: {result.returncode}")


if __name__ == "__main__":
    cfg = load_config()
    audit_config(cfg)
    run_env_check()
```

**评分标准**:

| 等级 | 分数 | 标准 |
|------|------|------|
| 优秀 | 4 | yaml 解析正确、十四段键值完整输出、阈值范围检查含警告、env_check 调用成功且结果正确 |
| 良好 | 3 | 主体功能正确（解析+检查），env_check 调用或阈值检查略简 |
| 中等 | 2 | 能解析 yaml 并打印配置，但缺少阈值检查或 env_check |
| 及格 | 1 | 仅能读取 yaml，功能不完整 |
| 不及格 | 0 | 无法解析配置或与课程项目无关 |

---

## 更新日志

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2026-08-18 | 初始版本，基于 EXP006a 知识图谱 39 点生成 34 题（单选 20 + 多选 8 + 简答 4 + 编程 2），覆盖率 100%（39/39），难度分布 容易 50%/中等 29%/困难 21% |
