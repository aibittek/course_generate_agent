---
course_code: EXP006
course_name: 机器人大模型综合应用开发
version: v4.0
generated_at: 2026-08-14
generator: QuizAgent
mode: standard
source_spec: courses/sheet1/llm_practice/_meta/course-spec.yaml
source_knowledge_graph: courses/sheet1/llm_practice/EXP006_knowledge_graph.md
source_syllabus: courses/sheet1/llm_practice/EXP006_syllabus.md
source_lab_guide: courses/sheet1/llm_practice/EXP006_lab_guide.md
csv_sha256: a6d970fa8548324c08d2b6a4724342d2d80cb2579ae99ccf8c35c5be82408139
---

# 机器人大模型综合应用开发 练测题库

> 适用对象: 人工智能/机器人工程/智能科学与技术 本科高年级
> 总题目数: 34
> 预计考试时长: 120 分钟
> 模式: 试卷模式（standard）
> 版本: v4.0
> 制定日期: 2026-08-14

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

- 知识图谱总知识点数: 42（6 章 14 节，知识点编号 1.1.1 ~ 6.3.3，详见 `EXP006_knowledge_graph.md`）
- 本套题显式覆盖知识点数: 42（100%，即 42/42）
- 题型设计原则：知识点编号严格取自知识图谱；单选/多选按章节组织（第 1~6 章），简答题 4 道与编程题 2 道统一置于卷末
- 涉及源码事实（参数值、接口名、命令）均与 `EXP006_lab_guide.md` 及 `config/eai_factory.yaml` 一致，如 mode: debug/production、tag_id=3、danger_dist=0.20、persist_time=0.5、pick_offset_x=0.015 等

### 章节-知识点-题目覆盖一览

| 章节 | 知识点编号 | 对应题号 |
|------|-----------|----------|
| 第 1 章 项目需求与系统架构 | 1.1.1 / 1.1.2 / 1.1.3 / 1.2.1 / 1.2.2 / 1.2.3 / 1.3.1 / 1.3.2 / 1.3.3 | 单选 1-4、多选 1 |
| 第 2 章 接口与配置设计 | 2.1.1 / 2.1.2 / 2.1.3 / 2.2.1 / 2.2.2 / 2.2.3 | 单选 1-3、多选 1-2 |
| 第 3 章 语音交互 | 3.1.1 / 3.1.2 / 3.1.3 / 3.2.1 / 3.2.2 / 3.2.3 | 单选 1-3、多选 1 |
| 第 4 章 视觉感知与装货抓取 | 4.1.1 / 4.1.2 / 4.1.3 / 4.2.1 / 4.2.2 / 4.2.3 | 单选 1-3、多选 1-2 |
| 第 5 章 分拣码垛与流水线 | 5.1.1 / 5.1.2 / 5.1.3 / 5.2.1 / 5.2.2 / 5.2.3 | 单选 1-3、多选 1 |
| 第 6 章 安全联锁与系统验证 | 6.1.1 / 6.1.2 / 6.1.3 / 6.2.1 / 6.2.2 / 6.2.3 / 6.3.1 / 6.3.2 / 6.3.3 | 单选 1-4、多选 1、编程 1 |

---

## 第 1 章 项目需求与系统架构

### 一、单项选择题（每题 2 分）

**1. [知识点 1.1.1]** 在 eai_factory 的 R1-R10 需求体系中，R1-R3 定义了系统的哪类需求？

A. 三大任务流程（装货/分拣/码垛）
B. 交互方式（语音 + 大模型、唤醒、指令识别）
C. 安全联锁与打断优先级
D. 工程组织与一键启动

**答案**: B
**解析**: R1-R3 定义交互方式：R1 语音 + 大模型（单轮、无多轮追问）、R2 唤醒、R3 指令识别"一律走大模型意图解析，不用关键词匹配"；R4-R6 定义三大任务，R7-R8 定义播报与打断复位，R9-R9.1 定义安全联锁与打断优先级，R10 定义工程组织。

---

**2. [知识点 1.1.3]** R9 安全联锁需求的检测条件是雷达前方多大范围内存在持续障碍？

A. 前方 30° 范围内、距离 10cm 内、持续 0.2s
B. 前方 60° 范围内（0° 为中心 ±30°，跨 0° 环绕）、距离 20cm 内、持续 0.5s
C. 前方 90° 范围内、距离 50cm 内、持续 1s
D. 前方 180° 范围内、距离 20cm 内、持续 0.5s

**答案**: B
**解析**: R9 的三个量化条件是：雷达前方 60° 范围（0° 为中心 ±30° 跨 0° 环绕）、距离 20cm 内、障碍持续超过 0.5s；触发动作是释放机械臂全部 6 个总线舵机力矩并发布 /eai_factory/safety/danger=true。

---

**3. [知识点 1.2.1, 1.2.3]** eai_factory 系统按"职责单一"拆分为五节点，其中负责任务编排、唯一做决策的节点是？

A. N1 语音节点（eai_factory_voice）
B. N2 调度器（eai_factory_scheduler）
C. N3 安全节点（eai_factory_safety）
D. N-conveyor 流水线节点

**答案**: B
**解析**: N1 只做交互（KWS→ASR→LLM→TTS），N2 调度器是"决策中枢"（任务状态机），N-grasp 只做"抓取-放置"原语，N3 安全常驻监听雷达，N-conveyor 只管流水线；底层能力（底盘、机械臂、传感器）来自复用节点 car1_bringup / car1_arm_controller / car1_peripherals，遵循"复用不改"原则。

---

**4. [知识点 1.3.3]** 若 N-grasp / N-conveyor 服务启动较慢、未就绪时，N2 调度器的兜底机制是？

A. 直接放弃任务并播报失败
B. 保存 _pending_task 并创建 2s 定时器 _retry_grasp 自动重试，服务就绪后重放任务
C. 阻塞等待服务就绪后再继续
D. 立即重启 grasp 节点

**答案**: B
**解析**: 调度器不依赖 launch 启动顺序：grasp/conveyor 服务未就绪时保存 _pending_task 并创建 2s 定时器，_retry_grasp 先判 _pending_task is None 早退，成功重放后置 None 并取消定时器，保证启动顺序容错（对应 scheduler_node.py L154-L169）。

---

### 二、多项选择题（每题 4 分）

**1. [知识点 1.1.2, 1.2.2, 1.3.1, 1.3.2]** 下列关于三大任务流程与调度编排的描述，正确的有？

A. 装货（R4）是"装货区视觉抓取 AprilTag → 放到固定位置"；分拣（R5）含"放到流水线→流水线自动送料→定点停靠"环节
B. 码垛（R6）由调度器先调 run_until_sensor 送料，订阅 /eai_factory/conveyor/state 收到 sensor_blocked 后再触发抓取
C. 意图/打断/危险等状态信号用话题广播，机械臂动作完成用服务返回 success 确认，属于"话题异步 + 服务同步"混合拓扑
D. 按 R4.1 约定，每次机械臂操作完成后必须先回 work 姿态，才能进行下一步或等待下一条指令

**答案**: ABCD
**解析**: A 对应三大任务物流走向差异（1.1.2）；B 对应 palletize"先送料后抓取"编排（1.3.2）；C 对应通信拓扑选择原因：秒级机械臂动作用服务拿确认，状态信号用话题保证不被服务占用卡死（1.2.2）；D 对应 R4.1 回 work 安全约定（1.1.2）。

---

## 第 2 章 接口与配置设计

### 一、单项选择题（每题 2 分）

**1. [知识点 2.1.1]** A 系列接口中，语音节点发布给调度器的意图话题是？

A. /eai_factory/speak（std_msgs/String）
B. /eai_factory/intent（std_msgs/String）
C. /eai_factory/interrupt（std_msgs/Bool）
D. /eai_factory/safety/danger（std_msgs/Bool）

**答案**: B
**解析**: A1 = /eai_factory/intent（N1→N2，String，值为 "load"/"sort"/"palletize" 英文枚举）；A2 = /eai_factory/speak（播报）；A3 = /eai_factory/interrupt（Bool）；C1 才是 N3 发布的 danger 话题。

---

**2. [知识点 2.1.3]** E 系列三个任务服务（start_load / start_sort / start_palletize）使用的消息类型是？

A. std_msgs/String
B. std_srvs/srv/Trigger（success + message）
C. geometry_msgs/PoseStamped
D. std_msgs/Bool

**答案**: B
**解析**: E1-E3 全部为 std_srvs/Trigger 触发型服务，请求体为空结构 "{}"，返回 success 与 message；位姿类话题（vision/target、target_pose、set_pick_target）才用 geometry_msgs/PoseStamped。

---

**3. [知识点 2.2.1]** config/eai_factory.yaml 顶层结构中 mode 参数的两个取值是？

A. true / false
B. debug / production
C. auto / manual
D. load / sort

**答案**: B
**解析**: mode 在 yaml L7 定义、由 grasp 节点读取：debug 模式视觉抓取时"检测到目标→存目标→等 /eai_factory/grasp/confirm 服务"人工确认；production 全自动直接 pick；修改 mode 需重启节点生效。

---

### 二、多项选择题（每题 4 分）

**1. [知识点 2.1.1, 2.1.2, 2.1.3]** 关于接口"触发语义 vs 完成语义"的区分，正确的有？

A. /eai_factory/grasp/start 服务立即返回表示"已触发"，机械臂是否完成靠 /eai_factory/grasp/status 话题（task|done）通知
B. /eai_factory/conveyor/run_until_sensor 是异步服务，运转直到光电遮挡定点停，完成走 /eai_factory/conveyor/state 话题
C. /eai_factory/conveyor/emergency_stop 是同步立即生效的服务，调用后流水线马上停带
D. D 系列复用接口（pick/place/go_work/set_pick_target）实现在 car1_arm_controller 等复用包中，eai_factory 只调用不改

**答案**: ABCD
**解析**: A/B/C 对应"触发语义（start 类立即返回）与完成语义（status/state 话题通知）"两类接口的区分（2.1.1、2.1.3）；D 对应 D 系列复用接口特性（2.1.2）。

---

**2. [知识点 2.2.2, 2.2.3]** 关于双模式与意图映射，下列说法正确的有？

A. 将 yaml 中 mode 改为 debug 后，视觉装货会停在"目标已存"状态，需调 /eai_factory/grasp/confirm 服务人工确认后继续
B. intents 段是"意图 ↔ 服务名"表驱动映射，新增意图只需改 yaml 不用改代码
C. 意图映射的消费端包括 voice 节点读 intent_hints 拼 LLM 提示词，以及调度器按意图路由任务服务
D. 修改 yaml 后无需重启即可在运行中的节点上生效

**答案**: ABC
**解析**: A 是双模式 debug 行为（2.2.2）；B/C 是意图映射表驱动原理：load→/eai_factory/start_load 等（2.2.3）；D 错误——参数在节点启动时一次性读取，修改 yaml 后必须重启对应节点生效（2.2.1）。

---

## 第 3 章 语音交互

### 一、单项选择题（每题 2 分）

**1. [知识点 3.1.1]** eai_factory 默认配置的 KWS 唤醒词集合是？

A. 小飞小飞 / 小飞同学 / 芝麻开门
B. 开始装货 / 开始分拣 / 开始码垛
C. 你好机器人 / 开始任务
D. 仅"小飞小飞"一个

**答案**: A
**解析**: voice.wakeup_words 默认三个唤醒词，节点启动时逐个下发麦克风阵列硬件唤醒；检测到唤醒词后播放提示音并进入 LISTENING 态开始 ASR，每轮交互结束后回到 IDLE，下一次必须重新唤醒。

---

**2. [知识点 3.1.2]** ASR 热词（config/hotwords.txt）要生效，解码方式必须切换到？

A. greedy_search
B. modified_beam_search
C. 逐帧 VAD
D. 大模型解码

**答案**: B
**解析**: voice.asr.hotwords_enable=true 时解码从 greedy_search 切换为 modified_beam_search 并加载热词文件（6 个词条：开始装货/开始分拣/开始码垛/装货/分拣/码垛，score=2.0）提升专有词识别权重；不开热词时"分拣"容易被识别成"风景/封建"。

---

**3. [知识点 3.2.1]** LLM 意图三分类的输出枚举是？

A. load / sort / palletize / none
B. start / stop / pause / resume
C. left / right / up / down
D. true / false

**答案**: A
**解析**: voice 节点把 ASR 文本交给本地 LLM 做三分类，输出 load（装货）/sort（分拣）/palletize（码垛）/none（无关）；识别成功发布 /eai_factory/intent，识别为 none 时播报"未识别指令，请重新唤醒"且不发布 intent。

---

### 二、多项选择题（每题 4 分）

**1. [知识点 3.1.3, 3.2.2, 3.2.3]** 关于 TTS 播报、intent_hints 与语音打断，正确的有？

A. 播报文案分两段：识别确认段"好的，开始装货"由 voice 节点发布意图后立即 TTS；完成段"装货完成"由调度器收到 grasp 完成状态后经 /eai_factory/speak 请求播报
B. intent_hints 收录"马舵""封建"等 ASR 误识别词，只需在 yaml 中补充，无需改代码
C. SPEAKING 态检测到唤醒词会置 interrupt_event、中断当前播报并发布 /eai_factory/interrupt=true
D. 语音打断（R8）的四步复位流程是：中断动作 → 回 work → 流水线停止 → 取消任务

**答案**: ABCD
**解析**: A 对应固定文案两段播报（3.1.3）；B 对应配置驱动意图提示词，这是"配置驱动设计"的核心价值（3.2.2）；C 对应打断实现：interrupt_event 只置位一次、开播前 clear 避免陈旧信号（3.2.3）；D 对应 R8 需求定义的复位流程（3.2.3，关联 1.1.2）。

---

## 第 4 章 视觉感知与装货抓取

### 一、单项选择题（每题 2 分）

**1. [知识点 4.1.1]** vision 段默认配置的 AprilTag 编码家族、标签 ID 与边长分别是？

A. tag36h11、tag_id=3、tag_size=0.025（25mm）
B. tag25h9、tag_id=1、tag_size=0.05
C. ArUco 4x4_50、tag_id=0、tag_size=0.1
D. tag36h10、tag_id=3、tag_size=0.2

**答案**: A
**解析**: yaml vision 段配置 tag_family=tag36h11、tag_id=3、tag_size=0.025 米；tag36h11 表示 36bit 编码、最小汉明距离 11，抗误检强；tag_size 是编码区物理边长，直接决定 PnP 解算的尺度。

---

**2. [知识点 4.1.2]** PnP 位姿解算（cv2.solvePnP）需要哪些输入才能求出标签的 6DOF 位姿？

A. 灰度图像 + 相机内参
B. 已知 3D 点（标签四角点坐标）+ 对应 2D 图像角点 + 相机内参
C. 标签图像 + 深度图
D. 机械臂关节角 + TF 树

**答案**: B
**解析**: PnP 利用"已知 3D 点 + 对应 2D 投影点 + 相机内参 K"恢复 [R|t]：标签四角点 3D 坐标以 tag_size/2 构造，与图像检测到的 2D 角点建立对应，SOLVEPNP_IPPE_SQUARE 解出 rvec/tvec，再经 Rodrigues 与 Shepperd 法得四元数，输出相机坐标系下位姿。

---

**3. [知识点 4.2.3]** grasp.pick_offset_x/y/z 的作用是？

A. 修正手眼标定/相机安装/机械臂装配造成的抓取点系统性偏差，只叠加在视觉抓取路径
B. 修改固定点位抓取的取料坐标
C. 调整流水线电机速度
D. 控制 TTS 音量

**答案**: A
**解析**: pick_offset 在 set_pick_target 时直接加到视觉解算的目标坐标上（p_target = p_vision_base + offset），实现一次性修正，实测值 x=+0.015、y=-0.010、z=+0.023；固定点位抓取不加偏移（手动打点已含姿态）。

---

### 二、多项选择题（每题 4 分）

**1. [知识点 4.1.3, 4.2.2]** 关于视觉装货抓取链路，正确的描述有？

A. 完整序列为：移观察位 → 检测 AprilTag → TF 变换 → set_pick_target → pick → place → 回 work
B. 视觉解算位姿在 camera_depth_optical_frame 系，需 lookup_transform(base_link, camera_depth_optical_frame) 经 TF 变换到 base_link 才能用于机械臂运动
C. debug 模式下视觉抓取停在 awaiting_confirm，需调 /eai_factory/grasp/confirm 服务继续
D. TF 树任一环节缺失（如相机外参未发布）会导致查找失败并中止抓取

**答案**: ABCD
**解析**: A 对应抓取序列八步（4.2.2）；B 对应 TF 变换原理 p_base = T_base←camera · p_camera（4.1.3）；C 对应 debug 模式 confirm 停等机制（4.2.2）；D 对应 TF 链缺失的故障表现（4.1.3）。

---

**2. [知识点 4.2.1, 4.2.3]** 关于双模式抓取，正确的有？

A. grasp.tasks.load.vision=true 走视觉抓取（依赖相机与 TF）
B. grasp.tasks.sort 与 palletize 的 vision=false 走固定点位抓取（不依赖相机）
C. 固定点位抓取不加 pick_offset 偏移，只有视觉抓取路径加偏移
D. 任务类型由 yaml 中 grasp.tasks.<task>.vision 决定，节点启动时统一加载到 task_poses 字典

**答案**: ABCD
**解析**: 对应双模式抓取概念（4.2.1）：vision=true 视觉抓取、vision=false 固定点位；偏移只加在视觉路径、固定抓取打点已含姿态（4.2.3）；grasp 节点启动时按任务加载 observe/place 姿态与 vision 标志（对应 grasp_node.py L89-L94）。

---

## 第 5 章 分拣码垛与流水线

### 一、单项选择题（每题 2 分）

**1. [知识点 5.1.1]** 固定点位抓取（vision=false）的取料/放置坐标来源是？

A. 视觉实时解算
B. 手动打点写入 yaml 的 observe_pose/place_pose（[x, y, z, pitch] 四元组）
C. 激光雷达扫描
D. 神经网络预测

**答案**: B
**解析**: 固定点位抓取不订阅视觉、不做 TF，observe_pose 即精确抓取点、place_pose 即放置点，均为人工打点后写入 grasp.tasks 配置（如 sort: [0.0622, -0.1158, 0.1951, 3.0371]）。

---

**2. [知识点 5.2.2]** run_until_sensor 光电定点停的两段式流程是？

A. 直接运转直到超时
B. 先等待"清沿"（光电无遮挡）再等待"挡沿"（光电被遮挡），防抖确认后定点停
C. 先抓取再送料
D. 依赖视觉检测停止

**答案**: B
**解析**: _run_until_sensor_worker 先等 clear 沿、再等 blocked 沿（防抖 debounce_reads=3）；若物品一开始就在光电位，清沿条件不满足会直接超时（sensor_timeout=30s 后 state=timeout），所以必须先触发服务再放物品。

---

**3. [知识点 5.2.3]** 流水线急停（emergency_stop）后的安全语义是？

A. 急停后自动恢复运转
B. 急停置位持续有效，期间 run / run_until_sensor 被拒绝，必须显式调 reset_emergency 复位
C. 急停只发话题、不停电机
D. 急停后必须重启 launch 才能恢复

**答案**: B
**解析**: emergency_stop 置位 _emergency_stop=True 并立即发 rps=0 停带；该标志持续有效，期间 run/run_until_sensor 均检查前置条件并返回 "emergency active — call reset_emergency first"，保证"急停后不自动复跑"的安全语义，须显式调 reset_emergency 复位回 idle。

---

### 二、多项选择题（每题 4 分）

**1. [知识点 5.1.2, 5.1.3, 5.2.1]** 关于手动打点、分拣动作原语与流水线电机，正确的有？

A. 手动打点流程是：调机械臂到位 → 读取末端位姿 (x, y, z, pitch) → 写入 yaml 的 grasp.tasks.sort
B. 固定抓取八步序列的关键是"提前开爪"：机械臂移动前夹爪已完全张开，到位立即闭爪抓取
C. 流水线电机复用底盘电机通道 M1，通过发布 /car1_base_driver/set_motor（id=1, rps）驱动，发 rps=0 即停
D. 打点姿态与抓取时姿态不一致（夹爪角度不同）会导致固定抓取失败，必须用实际抓取姿态打点

**答案**: ABCD
**解析**: A 对应手动打点流程（5.1.2）；B 对应 sort 动作原语：提前开爪保证"骑跨"姿态罩住物料（5.1.3）；C 对应流水线复用底盘电机 M1，STM32 保持最后速度、置 0 即停（5.2.1）；D 为打点易错点（5.1.2）。

---

## 第 6 章 安全联锁与系统验证

### 一、单项选择题（每题 2 分）

**1. [知识点 6.1.1]** N3 安全节点的雷达扇区检测范围与危险距离是？

A. 雷达前方 60°（0° 为中心 ±30°）、危险距离 20cm
B. 雷达后方 60°、危险距离 20cm
C. 全向 360°、危险距离 50cm
D. 前方 10°、危险距离 1m

**答案**: A
**解析**: safety 段 front_start_deg=-30、front_end_deg=30（共 60°，跨 0° 环绕）、danger_dist=0.20；检测基于雷达自身坐标系（laser_link），不依赖车身 TF，障碍必须放在雷达正前方。

---

**2. [知识点 6.1.2]** 障碍物需要持续多久才判定为危险（persist_time）？

A. 0.1s
B. 0.5s
C. 5s
D. 立即判定

**答案**: B
**解析**: _scan_cb 中 obstacle_close 为真时记录 _danger_since，仅当 now - _danger_since >= persist_time(0.5s) 才进入危险状态；障碍消失立即清零计时，用于过滤瞬时误报（如飞过的纸屑、短暂扫过的手）。

---

**3. [知识点 6.2.2]** 关于打断分层，正确的说法是？

A. 语音打断优先级高于雷达危险打断
B. 雷达危险打断优先级高于语音打断，危险期间语音打断的"回 work"动作被抑制
C. 两类打断互不相关
D. 危险解除后任务自动继续执行

**答案**: B
**解析**: R9.1 定义雷达打断 > 语音打断；危险时释放力矩不强行运动，语音打断在危险期间被抑制；危险解除进入 work 后需重新唤醒/重新触发任务，不会自动续跑。

---

**4. [知识点 6.3.2]** launch 文件 7 个模块开关中默认值为 false 的是？

A. start_base
B. start_voice
C. start_radar
D. start_grasp

**答案**: C
**解析**: 7 个开关 start_base / start_viz / start_voice / start_vision / start_grasp / start_conveyor / start_radar 默认全 true，仅 start_radar 默认 false；低内存测试安全节点时可组合 start_base:=false start_voice:=false ... start_radar:=true 只起雷达 + safety。

---

### 二、多项选择题（每题 4 分）

**1. [知识点 6.1.3, 6.2.1, 6.2.3]** 关于雷达危险触发与解除的完整链路，正确的有？

A. 危险触发时在 scan 回调内直接发布 /eai_factory/safety/danger=true，并通过 /car1_base_driver/bus_servo/set_state 发布 enable_torque=[0]*6 释放 6 个总线舵机力矩
B. N-grasp 订阅 danger 收到 true 立即 emergency_stop 中止抓取并回 idle；N-conveyor 收到 danger 停带并调 /arm_controller/emergency_stop 停机械臂
C. 危险解除时发布 danger=false、status=recover，先恢复 6 舵机力矩（enable_torque=[1]*6）再调 /arm_controller/go_work 回 work
D. 力矩释放走"一次 DDS 发布、无服务往返"，响应最快（雷达 10Hz 最坏 100ms 检测、舵机释放约 150-220ms）

**答案**: ABCD
**解析**: A 对应力矩释放机制（6.1.3）；B 对应 N-grasp/N-conveyor 对 danger 的联动（6.2.3）；C 对应恢复流程：恢复力矩必须先于 go_work 执行（6.2.1）；D 对应话题直发、无服务往返的响应设计（6.1.3）。

---

### 三、简答题（每题 5 分）

**1. [知识点 3.2.3, 6.2.2]** R8 语音打断与 R9 雷达危险打断的区别是什么？为什么雷达打断优先级高于语音打断？

**参考答案**:
1. 触发源不同：R8 由用户再次说唤醒词触发（SPEAKING 态或任务执行中）；R9 由雷达检测到前方 60° 扇区、20cm 内、持续 0.5s 的障碍触发。
2. 动作不同：R8 是四步复位——中断动作 → 回 work → 流水线停止 → 取消任务；R9 是释放全部 6 个总线舵机力矩（机械臂变软、可被外力推开）+ 发布 danger=true，不强行运动。
3. 解除条件不同：R8 打断后回到监听态、可继续说新指令；R9 需障碍移开后恢复力矩并调 go_work 回 work，且危险解除后需重新唤醒/重新触发任务。
4. 分层原因：危险期间机械臂"软"是保护人的安全底线，若此时执行语音打断的"回 work"动作，反而可能与操作者对抗造成伤害，故雷达打断 > 语音打断，危险期间语音打断的"回 work"被抑制。

**评分标准**: 要点完整 5 分 / 较完整 3-4 分 / 部分 1-2 分 / 错误 0 分（触发源、动作、解除条件三要素各 1 分，分层原因 2 分）。

---

**2. [知识点 4.2.3, 5.1.2]** 为什么视觉抓取需要 pick_offset 补偿，而固定点位抓取不需要？请简述 pick_offset 的调优流程。

**参考答案**:
1. 误差来源不同：视觉抓取的目标位姿来自相机检测 + TF 变换，手眼标定误差、相机安装偏差、机械臂装配误差会叠加成系统性偏移（每次偏同一方向、同一大小）；固定抓取坐标是人工打点得到，误差在打点时已被手动校准，无视觉误差源。
2. 补偿方式：pick_offset_x/y/z（base_link 系，+X 前、+Y 左、+Z 上）在 set_pick_target 时直接加到视觉解算坐标上（p_target = p_vision_base + offset）实现一次性修正；固定抓取不加偏移（打点已含姿态）。
3. 调优流程：①固定标签位置，连续抓取 3 次记录夹爪落点偏差；②按"落点偏左 5mm → pick_offset_y 增大 5mm"等反向修正，每次只改一个方向 5~10mm（先抬升 z 再横向 x/y，防止碰撞）；③再抓 3 次验证，直至夹爪准确覆盖标签中心（重复 5 次成功率 ≥ 4/5）；④将最终值写回 yaml 并重启节点（ros2 param set 只影响运行中的节点）。
4. 注意事项：z 方向注意与 arm 控制器的 gripper_depth 是否叠加（双重补偿），抓取偏高需先判断是哪一层补偿。

**评分标准**: 要点完整 5 分 / 较完整 3-4 分 / 部分 1-2 分 / 错误 0 分（误差来源差异 2 分，补偿原理 1 分，调优流程 2 分）。

---

**3. [知识点 1.3.2, 5.2.2]** palletize 码垛编排为什么采用"run_until_sensor 立即返回 + 订阅 conveyor/state 感知完成"的异步方案，而不是同步阻塞等待送料完成？

**参考答案**:
1. 异步服务语义：run_until_sensor 调用后立即返回 started，流水线在内部线程运转，完成走 /eai_factory/conveyor/state 话题（sensor_blocked），并非阻塞等待。
2. 阻塞风险：若同步阻塞等待送料完成（秒级到数十秒），N2 的单线程 executor 会被占死，无法及时响应 /eai_factory/interrupt（语音打断）与 /eai_factory/safety/danger（雷达危险），安全与交互都会失效。
3. 实现机制：N2 置 _awaiting_sensor=True 后回到主循环，_conveyor_state_cb 收到 state=sensor_blocked 时再 _trigger_grasp('palletize')，等待期间可正常响应其他信号。
4. 超时兜底：若物品未及时放上流水线（先清沿不满足），sensor_timeout=30s 后 state=timeout，N2 复位 _awaiting_sensor，避免死等。

**评分标准**: 要点完整 5 分 / 较完整 3-4 分 / 部分 1-2 分 / 错误 0 分（异步语义 1 分，阻塞风险分析 2 分，实现机制 1 分，超时兜底 1 分）。

---

**4. [知识点 6.1.2, 6.1.3]** 危险判定为什么要加 0.5s 持续计时？为什么"危险时不强行运动（释放力矩）"比"立即刹车保持姿态"更安全？

**参考答案**:
1. 持续计时作用：过滤瞬时误报（飞过的纸屑、短暂扫过的手），_scan_cb 记录 _danger_since，仅当持续 ≥ persist_time(0.5s) 才进入 danger，障碍消失立即清零计时，避免机械臂被高频误触干扰。
2. 释放力矩更安全的原因：①机械臂变软后可被操作者轻松推开，避免与机械臂"较劲"造成挤压伤害；②不强行运动就不会在危险方向上继续施加力/速度，从根源消除伤害能量；③保持姿态的"刹车"只解决了"运动"问题，解决不了"被撞时依然刚性对抗"的问题。
3. 安全闭环：障碍移开后先恢复力矩、再 go_work 回 work 安全位，危险期间不执行任何强行运动指令，实现"检测→释放→恢复"完整闭环。

**评分标准**: 要点完整 5 分 / 较完整 3-4 分 / 部分 1-2 分 / 错误 0 分（持续计时作用 2 分，人机安全分析 2 分，恢复闭环 1 分）。

---

### 四、编程题（每题 4 分）

**1. [知识点 6.3.1, 6.3.3, 1.3.1] 关联实验 9**

**题目描述**:

基于实验 9"具身智能工厂--全功能快速验证"的内容，编写一个 Bash 脚本 `verify_eai_factory.sh`，要求：
1. 一键启动 eai_factory 全系统（`ros2 launch eai_factory eai_factory.launch.py`），后台运行并把日志写入文件；
2. 等待系统就绪（轮询 /eai_factory/start_load 服务出现）后，依次通过服务方式触发装货、分拣两个任务（`ros2 service call /eai_factory/start_load` 与 `/eai_factory/start_sort`，std_srvs/srv/Trigger），每次触发后监听 /eai_factory/grasp/status 话题，等待出现对应 "load|done" / "sort|done" 再触发下一个（体现串行保护语义，一次只能执行一个任务）；
3. 两个任务都完成后调用 `bash scripts/stop_eai_factory.sh` 停止清理，防止残留进程占用总线舵机/串口/8080 端口。

**参考代码框架**:

```bash
#!/usr/bin/env bash
# verify_eai_factory.sh - 装货/分拣任务链路验证（关联实验9）
# 依赖: ROS 2 Humble + eai_factory 包已构建（colcon build --packages-select eai_factory）
set -u

LOG=verify_eai_factory.log
: > "$LOG"

source /opt/ros/humble/setup.bash
source /home/iflytek/ros2_ws/install/setup.bash

# 1) 一键启动（后台运行，日志落盘）
ros2 launch eai_factory eai_factory.launch.py start_viz:=false >>"$LOG" 2>&1 &
LAUNCH_PID=$!
echo "[INFO] launch started, pid=$LAUNCH_PID"

# 2) 等待装货服务就绪（调度器提供，最多重试 30 次 × 2s）
for i in $(seq 1 30); do
    if ros2 service list 2>/dev/null | grep -q "/eai_factory/start_load"; then
        echo "[INFO] start_load service ready"; break
    fi
    sleep 2
done

wait_task_done() {   # $1=任务名  $2=期望状态
    local task="$1" expect="$2"
    echo "[INFO] trigger task: $task"
    ros2 service call "/eai_factory/start_$task" std_srvs/srv/Trigger "{}" | tail -2
    echo "[INFO] waiting for $task|$expect ..."
    timeout 60 ros2 topic echo /eai_factory/grasp/status --once \
      | grep -q "$task|$expect" && echo "[INFO] $task done" || echo "[WARN] $task timeout"
}

# 3) 串行触发：装货(视觉抓取) → 分拣(固定点位)，完成播报由调度器经 /eai_factory/speak 请求 TTS
wait_task_done load done
wait_task_done sort done

# 4) 停止清理（防残留，勿只 Ctrl+C）
bash scripts/stop_eai_factory.sh
echo "[INFO] finished, check $LOG"
```

**评分标准**:

| 等级 | 分数 | 标准 |
|------|------|------|
| 优秀 | 4 | 一键启动 + 服务就绪等待 + 串行触发与完成状态监听 + 停止清理全流程正确，命令与真实接口（start_load/start_sort/grasp/status/stop_eai_factory.sh）一致 |
| 良好 | 3 | 主体流程正确，能触发任务并等待完成状态，就绪等待或停止清理略简 |
| 中等 | 2 | 能启动并触发任务，但缺少完成状态监听，或未串行（并发触发违背串行保护语义） |
| 及格 | 1 | 仅有启动或仅能触发单个任务，链路不完整 |
| 不及格 | 0 | 命令错误、与 eai_factory 无关或无法运行 |

---

**2. [知识点 2.2.1, 2.2.3, 4.2.3] 关联实验 3、实验 5**

**题目描述**:

eai_factory 采用"配置驱动"设计（改配置不动代码）。编写一个 Python 脚本 `task_config.py`，要求：
1. 解析 config/eai_factory.yaml 的 grasp.tasks 段，输出每个任务（load/sort/palletize）的 vision 标志与 observe_pose/place_pose（体现双模式配置）；
2. 解析 intents 段，打印"意图 → 服务"映射表（体现表驱动意图映射，新增意图只需改 yaml）；
3. 提供 update_pick_offset(dx, dy, dz) 函数，把 grasp.pick_offset_x/y/z 修改为指定值并写回 yaml，同时打印"参数在节点启动时一次性读取，需重启 eai_factory 节点生效"的提示（pick_offset 用于修正视觉抓取的系统性偏差）。

**参考代码框架**:

```python
#!/usr/bin/env python3
"""
task_config.py - eai_factory 配置驱动解析与抓取偏移调优
关联实验: 实验3 接口功能设计 / 实验5 视觉自适应装货
依赖: PyYAML（python3 -m pip install pyyaml 或系统自带）
"""
import sys
import yaml

CONFIG = "config/eai_factory.yaml"


def load_config(path=CONFIG):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def show_tasks(cfg):
    # ① grasp.tasks 双模式：vision 标志决定走视觉抓取还是固定点位抓取
    print("== grasp.tasks (双模式配置) ==")
    for task, conf in cfg["grasp"]["tasks"].items():
        print(f"  {task:9s} vision={conf['vision']}  "
              f"observe={conf.get('observe_pose')}  place={conf.get('place_pose')}")


def show_intents(cfg):
    # ② intents 表驱动意图映射：load → /eai_factory/start_load
    print("== intents (意图→服务映射) ==")
    for intent, m in cfg["intents"].items():
        print(f"  {intent:9s} -> {m['action']}")


def update_pick_offset(dx, dy, dz, path=CONFIG):
    # ③ 修改视觉抓取偏移并写回 yaml（重启节点后生效）
    cfg = load_config(path)
    cfg["grasp"]["pick_offset_x"] = dx
    cfg["grasp"]["pick_offset_y"] = dy
    cfg["grasp"]["pick_offset_z"] = dz
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
    print(f"[INFO] pick_offset 已更新: ({dx}, {dy}, {dz})")
    print("[INFO] 参数在节点启动时一次性读取，请重启 eai_factory 节点后验证抓取落点")


if __name__ == "__main__":
    cfg = load_config()
    show_tasks(cfg)
    show_intents(cfg)
    if len(sys.argv) == 4:  # 用法: python3 task_config.py 0.015 -0.010 0.023
        update_pick_offset(float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]))
```

**评分标准**:

| 等级 | 分数 | 标准 |
|------|------|------|
| 优秀 | 4 | yaml 解析、双模式任务表、意图映射表、偏移写回四部分全部正确，输出与真实配置（vision 标志、start_load 等服务名）一致，并提示重启生效 |
| 良好 | 3 | 主体功能正确（解析 + 映射表），偏移写回或重启提示略简 |
| 中等 | 2 | 能解析 yaml 并打印任务/意图，但缺少偏移修改，或修改后未写回 yaml |
| 及格 | 1 | 仅能读取 yaml，功能不完整 |
| 不及格 | 0 | 无法解析配置或与 eai_factory 无关 |
