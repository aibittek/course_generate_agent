---
course_code: EXP005
course_name: 机器人机械臂应用与开发
version: v1.2
generated_at: 2026-08-10
generator: SyllabusAgent
source_spec: courses/sheet1/arm_practice/_meta/course-spec.yaml
csv_sha256: pending
---

# 机器人机械臂应用与开发 教学大纲

> 课程代码: EXP005
> 适用对象: 人工智能/机器人工程/智能科学与技术 本科高年级
> 总学时: 32（理论 0 + 实验 32）
> 课程类型: 专业核心课（实践导向）
> 制定日期: 2026-08-04

---

## 一、课程目标

### 1.1 知识目标
通过本课程的学习，学生能够：
1. 掌握 URDF 机器人模型描述、RViz/MoveIt2 仿真可视化与 Gazebo 物理仿真的工作流程
2. 理解 STM32 板载 PWM 舵机协议、ROS2 topic/service 通信机制与 arm_controller 节点架构
3. 掌握舵机零位校准、交互式动作录制与 YAML 回放的方法
4. 熟悉正运动学（FK）与逆运动学（IK，包括解析法与数值法）的数学原理与实现
5. 了解视觉抓取系统（HSV 检测 + 深度相机 + TF 变换）的核心原理与 look-then-move 策略

### 1.2 能力目标
通过本课程的学习，学生能够：
1. 具备独立配置 car1 5 自由度机械臂的 URDF/MoveIt2/Gazebo 仿真环境的能力
2. 能够通过 ROS2 topic/service 在真实机械臂上实现关节与夹爪的精确控制
3. 能够基于 `test_servo_direct.py`（裸机）录制动作导出 YAML，使用 `bringup.launch.py` + `action_player` 节点回放，处理零位校准与软限位
4. 能够在 Web 3D 仿真器中分析 FK/IK 计算结果，并对工作空间进行扫描
5. 能够将 IK 解算在实机上闭环验证并应用系统偏移补偿
6. 能够基于 visual_grasp.launch.py 一站式启动并完成动态视觉抓取，处理 HSV 调参与服务化流程

### 1.3 素养目标
通过本课程的学习，学生能够：
1. 养成从仿真认知→裸机控制→理论深化→抓取应用的螺旋式工程思维
2. 具备模块化、可复用、可追溯的机器人开发意识（YAML 动作文件、URDF、launch）
3. 树立对实机安全、关节限位、奇异位姿等工程伦理的敬畏意识

---

## 二、教学内容与学时分配

| 序号 | 章节 | 理论(h) | 实验(h) | 合计(h) | 占比 |
|------|------|--------|--------|--------|------|
| 1 | 第1章 URDF建模与仿真认知 | 0 | 4 | 4 | 12.5% |
| 2 | 第2章 底层舵机通信与ROS2控制 | 0 | 4 | 4 | 12.5% |
| 3 | 第3章 零位校准与动作录制回放 | 0 | 4 | 4 | 12.5% |
| 4 | 第4章 运动学原理与Web仿真 | 0 | 4 | 4 | 12.5% |
| 5 | 第5章 IK解算与实机验证 | 0 | 4 | 4 | 12.5% |
| 6 | 第6章 固定位置IK抓取 | 0 | 4 | 4 | 12.5% |
| 7 | 第7章 视觉动态抓取 | 0 | 8 | 8 | 25.0% |
| - | **合计** | **0** | **32** | **32** | **100%** |

> 备注：本课程采用"做中学"模式，32h 全部为实验学时，知识讲授融入实验前置 brief。视觉抓取安排 8h 因涉及 HSV/深度/TF/状态机多个模块的端到端集成。

---

## 三、教学内容

### 第1章 URDF建模与仿真认知

#### 教学内容
- URDF 模型结构（link/joint）与 TF 树自动生成
- RViz 可视化与 joint_state_publisher_gui 交互
- MoveIt2 运动规划插件与 RvizVisualTools GUI
- Gazebo 物理仿真（ODE/Bullet）与 joint_trajectory_controller
- **（v1.1 新增）固定位置抓取演示 grasp_demo 的 8 步流程感性认识（引导性介绍，非本章重点）**

#### 重点难点
- **重点**: URDF→RViz→MoveIt2→Gazebo 完整仿真链路的搭建与使用
- **重点（v1.1 新增）**: 让初学者直观理解"无视觉抓取"的 8 步流程与局限性
- **难点**: MoveIt2 规划组配置与 Gazebo ros2_control 桥接的协同

#### 教学活动
- [x] 案例分析：对比仿真与实机控制的安全/效率差异
- [x] 动手实验：exp01 机械臂URDF仿真运动控制
- [x] **（v1.1 新增）** 演示：grasp_demo 固定位置抓取 8 步流程（铺垫性观察）
- [x] **（v1.1 新增）** 问题引导：方块位置移动后为何抓取失败？→ 引出实验 7 视觉抓取

#### 对应知识点
1.1.1 URDF概念 / 1.1.2 link/joint / 1.1.3 TF树 / 1.2.1 display.launch / 1.2.2 TF渲染 / 1.2.3 MoveIt2插件 / 1.3.1 Gazebo概念 / 1.3.2 gazebo_arm.launch / 1.3.3 joint_trajectory / **1.3.4 抓取流程感性认识（v1.1 新增）**

---

### 第2章 底层舵机通信与裸机控制

#### 教学内容
- STM32 板载总线舵机的 1Mbps 串口协议（单线半双工，5 舵机共享总线）
- 帧格式：0xAA 0x55 + 长度 + 命令 + 参数 + CRC8 校验和（实测帧头 0xAA 0x55）
- PWM 范围（500~2500）、CENTER_PWM=1500、PWM_TO_RAD=0.002356 rad/PWM
- **CRC8 查表校验算法**（检测单比特翻转，避免指令错位）
- Python `pyserial` 裸机打开 `/dev/ttyUSB0`（不依赖 ROS2）
- 串口设备权限（`chmod 666` 或加入 `dialout` 组）
- `test_servo_direct.py` 的 `interactive_mode` 命令（j1~j5/g/s/r/read/save/yaml/home/work/free/load/quit）
- 动作录制与 YAML 导出（`export_yaml` 输出与 exp03 `action_player` 兼容）
- 裸机 vs ROS2 两条开发路线的对比
- 1Mbps 串口带宽分析（5 关节 50Hz 约 14kbps，占总线 1.4%）

#### 重点难点
- **重点**: 通过 1Mbps 串口协议字节级理解、PWM↔rad 公式、CRC8 校验机制
- **难点**: CRC8 查表算法的实现；单线半双工总线的时分复用；串口权限问题排查

#### 教学活动
- [x] 演示：用 cutecom 手动发一帧并观察舵机应答（验证协议）
- [x] 演示：`test_servo_direct` interactive_mode 控制 5 关节 + 夹爪
- [x] 演示：save/yaml 录制抓取动作并导出（供 exp03 消费）
- [x] 动手实验：exp02 机械臂底层协议与控制
- [x] 问题引导：CRC 校验失败为何会丢弃指令？如果没有 CRC 会发生什么？

#### 对应知识点
2.1.1 1Mbps串口 / 2.1.2 PWM公式 / **2.1.3 帧格式 0xAA 0x55** / **2.1.4 CRC8 校验** / **2.2.1 串口权限** / **2.2.2 interactive_mode** / **2.2.3 动作录制/YAML** / **2.3.1 裸机 vs ROS2** / **2.3.2 协议字节级**

> **v1.2 变更**：原 ROS2 topic/service 与 arm_controller 桥接内容迁移至第 3 章；本章节聚焦"裸机协议演示"，新增 CRC8、interactive_mode、动作录制等知识点。

---

### 第3章 ROS2 架构与动作回放

#### 教学内容
- `bringup.launch.py` 启动 7~8 个 ROS2 节点的拓扑结构（base_driver / robot_state_publisher / joint_state_publisher / imu_filter / odom_publisher / ekf_filter_node / servo_controller / init_pose）
- `rqt_graph` 可视化插件观察节点-话题-服务的有向图
- `ros2 node list` / `ros2 topic list` / `ros2 service list` 三大勘察命令
- `/arm_controller/joint_command` 话题（`sensor_msgs/JointState`，position 字段为弧度）
- PWM↔rad 换算公式 `rad = (PWM - 1500) × 0.002356`，由 arm_controller 内部自动完成
- `action_player` 节点（**节点而非 launch**）通过 `console_scripts` 注册
- 4 种回放模式：普通（play 服务）、单步（~/next）、循环（loop:=true）、急停（~/stop）
- YAML 格式兼容（与 exp02 的 `export_yaml` 严格匹配）
- 修改 YAML 后必须 `colcon build` 才能热更新
- 舵机零位校准（软件 offset 方案，不写 EEPROM）
- `servo_calib.launch.py` 校准 GUI 的使用

#### 重点难点
- **重点**: 理解 bringup 启动的节点拓扑；用 joint_command 弧度控制；action_player 节点回放；软件 offset 校准
- **难点**: **严禁使用** `/arm_controller/target_pose`（自动 IK）和 `/arm_controller/pick`/`/arm_controller/place`（完整抓取 pipeline）——这些是 exp05/exp06 的内容；区分 `action_player` 节点 vs `action_player.launch.py`；区分 joint_command 弧度与原始 PWM

#### 教学活动
- [x] 演示：rqt_graph 绘制 7~8 节点的有向图（强调 servo_controller 是软硬件唯一桥接点）
- [x] 演示：用 ros2 topic pub joint_command 发送 5 关节弧度
- [x] 演示：action_player 节点回放 exp02 导出的 pick_and_place.yaml
- [x] 演示：单步/循环/急停三种模式
- [x] 演示：修改 YAML 中 gripper_open 的 PWM 后 colcon build 热更新
- [x] 演示：servo_calib GUI 校准 joint2 写入 offset
- [x] 动手实验：exp03 机械臂 ROS2 架构与动作回放
- [x] 问题引导：为什么不直接用 target_pose 触发 IK？→ 教学顺序隔离（IK 在 exp04/05 才学）

#### 对应知识点
**3.1.1 bringup 拓扑 / 3.1.2 rqt_graph / 3.1.3 node list/topic list** / **3.2.1 joint_command 话题** / **3.2.2 PWM↔rad 换算** / **3.3.1 action_player 节点** / **3.3.2 YAML 格式兼容** / **3.3.3 回放模式** / 3.4.1 软件 offset / 3.4.2 servo_calib GUI

> **v1.2 变更**：标题从"零位校准与动作录制回放"改为"ROS2 架构与动作回放"；原 exp03 的 test_servo_direct 录制迁移至 exp02；新增 bringup 拓扑、rqt_graph、joint_command、action_player 节点等 8 个 ROS2 知识点；零位校准保留为 3.4 节；**严禁 IK 相关接口**。

---

### 第4章 运动学原理与Web仿真

#### 教学内容
- 正运动学 FK 的 4×4 齐次变换链与 DH 参数
- 逆运动学 IK 的概念、解析法（closed-form）与数值法（DLS）
- car1 5 自由度的三段式解析法（q1=atan2+asin、2R余弦定理、PHI补偿）
- car1_web_server 的 Three.js 3D 渲染与 WebSocket 通信
- ik-analytical.js 与 ik-numerical.js 的对比
- auto-pitch 不可达 pitch 自动搜索机制
- PWM↔rad 换算与软限位
- 工作空间扫描与可达云图

#### 重点难点
- **重点**: 在 Web 仿真器中直观理解 FK/IK 的计算过程
- **难点**: car1 三段式解析法 IK 的几何推导与 auto-pitch 机制

#### 教学活动
- [x] 演示：浏览器中实时拖动目标点观察关节变化
- [x] 动手实验：exp04 机械臂运动学控制原理

#### 对应知识点
4.1.1 FK概念 / 4.1.2 齐次变换链 / 4.1.3 DH参数 / 4.2.1 IK概念 / 4.2.2 解析vs数值 / 4.2.3 car1三段式 / 4.3.1 Web仿真器 / 4.3.2 ik-analytical.js / 4.3.3 auto-pitch / 4.4.1 PWM↔rad / 4.4.2 软限位 / 4.4.3 工作空间扫描

---

### 第5章 IK解算与实机验证

#### 教学内容
- ik_analytical.py 的 ik_solve(target_xyz, target_pitch) 接口
- fk.py 的 fk_solve(joint_angles) 接口
- transform.py 的 4×4 矩阵运算基础
- FK/IK 闭环验证（随机采样→IK→FK→误差<1.5mm）
- 已知系统偏移（J2 大臂+4°、J3 小臂+2.3°）与补偿策略
- 直连串口模式（--direct）的底层调试
- 解析法 vs 数值法 IK 的适用场景对比

#### 重点难点
- **重点**: 在真实机械臂上验证 IK 算法的精度
- **难点**: 系统偏移的识别与补偿策略的设计

#### 教学活动
- [x] 演示：FK/IK 闭环验证与系统偏移补偿
- [x] 动手实验：exp05 机械臂IK解算

#### 对应知识点
5.1.1 ik_solve / 5.1.2 fk_solve / 5.1.3 transform / 5.2.1 FK闭环 / 5.2.2 误差<1.5mm / 5.2.3 误差来源 / 5.3.1 系统偏移 / 5.3.2 补偿策略 / 5.3.3 --direct模式 / 5.4.1 DLS数值法 / 5.4.2 阻尼因子 / 5.4.3 解析vs数值

---

### 第6章 固定位置IK抓取

#### 教学内容
- Gazebo 仿真抓取 grasp_demo.launch.py 的 ik/manual/none 三模式
- /arm/target_pose 话题设置目标点
- /arm/pick 与 /arm/place 服务触发抓取与放置
- 抓取参数调优：gripper_depth、pre_grasp_height、lift_height、grasp_pitch
- 分步移动策略（先转底座 J1 再动 J2-J5）
- 关节软限位保护与奇异位姿检测
- 抓取失败回退机制

#### 重点难点
- **重点**: 仿真与实机两套抓取流程的实现
- **难点**: 分步移动策略与奇异位姿回退的设计

#### 教学活动
- [x] 演示：从仿真到实机的完整抓取流程对比
- [x] 动手实验：exp06 机械臂IK固定抓取

#### 对应知识点
6.1.1 grasp_demo / 6.1.2 ik/manual模式 / 6.1.3 接触力反馈 / 6.2.1 target_pose / 6.2.2 /arm/place / 6.2.3 分步移动 / 6.3.1 gripper_depth / 6.3.2 pre_grasp_height / 6.3.3 grasp_pitch / 6.4.1 软限位 / 6.4.2 奇异检测 / 6.4.3 失败回退

---

### 第7章 视觉动态抓取

#### 教学内容
- HSV 颜色空间相比 RGB 的光照鲁棒性
- OpenCV inRange+形态学操作生成二值掩膜
- findContours + minEnclosingCircle 提取目标质心
- 深度相机反投影（像素坐标→相机坐标）与内/外参
- TF 坐标变换（camera_depth_optical_frame→base_link）
- REP-103 坐标系约定（X右/Y下/Z前）
- look-then-move 策略（eye-in-hand 下压失视野）
- IDLE 状态机：observe→detect→confirm→pick→idle
- 服务化控制：/visual_grasp/start、/confirm、/skip、/abort
- rqt 三栏可视化（RGB+Depth+Mask）与 HSV/gripper_depth 调优
- 重复抓取处理与已抓取物体跳过逻辑

#### 重点难点
- **重点**: 端到端视觉抓取系统集成
- **难点**: 多模块协作（HSV+深度+TF+IK+状态机）的时序与服务化封装

#### 教学活动
- [x] 演示：从颜色检测到动态抓取的全过程
- [x] 综合项目：exp07 机械臂基于视觉的动态抓取

#### 对应知识点
7.1.1 HSV / 7.1.2 inRange+形态学 / 7.1.3 findContours / 7.2.1 深度反投影 / 7.2.2 像素→相机 / 7.2.3 内/外参 / 7.3.1 TF树 / 7.3.2 transform / 7.3.3 REP-103 / 7.4.1 eye-in-hand / 7.4.2 look-then-move / 7.4.3 记录再移动 / 7.5.1 IDLE状态机 / 7.5.2 四服务接口 / 7.5.3 解耦设计 / 7.6.1 rqt三栏 / 7.6.2 HSV调参 / 7.6.3 重复抓取

---

## 四、实验项目

| 序号 | 实验名称 | 学时 | 实验类型 | 关联知识点 |
|------|---------|------|---------|----------|
| 1 | 机械臂URDF仿真运动控制实验 | 4h | 验证性 ⭐ | 1.1.1~1.3.4（10 个，v1.1 新增 1.3.4 抓取流程感性认识） |
| 2 | 机械臂底层协议与控制实验 | 4h | 验证性 ⭐⭐ | 2.1.1~2.3.3 |
| 3 | 机械臂零位校准与动作录制实验 | 4h | 设计性 ⭐⭐ | 3.1.1~3.3.3 |
| 4 | 机械臂运动学控制原理实验 | 4h | 验证性 ⭐⭐ | 4.1.1~4.4.3 |
| 5 | 机械臂IK解算实验 | 4h | 综合性 ⭐⭐⭐ | 5.1.1~5.4.3 |
| 6 | 机械臂IK固定抓取实验 | 4h | 综合性 ⭐⭐⭐ | 6.1.1~6.4.3 |
| 7 | 机械臂基于视觉的动态抓取实验 | 8h | 综合性 ⭐⭐⭐ | 7.1.1~7.6.3 |
| - | **合计** | **32h** | - | - |

### 实验类型分布
- 验证性：1 个（14.3%）
- 设计性：0 个
- 综合性：5 个（71.4%）
- 综合（视觉）：1 个（14.3%，8h）

### 难度分布
- ⭐ 基础：1 个
- ⭐⭐ 中等：3 个
- ⭐⭐⭐ 综合：3 个

---

## 五、教学方法

| 方法 | 适用环节 | 占比 |
|------|---------|------|
| 任务驱动 | 实验实训 | 50% |
| 演示法 | 工具/效果展示 | 20% |
| 项目实战 | 综合应用（exp05/06/07） | 20% |
| 小组讨论 | 难点突破（IK 几何推导、视觉抓取调参） | 5% |
| 讲授法 | 实验前 brief 知识铺垫 | 5% |

> 本课程以"做中学"为主，讲授时间被压缩到每个实验的 5-10 分钟前置 brief。螺旋式路径：仿真认知→裸机控制→理论深化→抓取应用。

---

## 六、考核方式

### 6.1 成绩构成

| 考核环节 | 比例 | 考核内容 |
|---------|------|---------|
| 平时表现 | 10% | 出勤 + 实验态度 |
| 实验报告 | 40% | 7 个实验的过程文档与结果 |
| 阶段测试 | 20% | 章节小测（每章 1 次，共 7 次） |
| 综合考核 | 30% | exp07 视觉抓取综合项目答辩 |

### 6.2 考核标准

#### 实验报告评分标准
| 等级 | 分数 | 标准 |
|-----|------|------|
| 优秀 | 36-40 | 步骤完整，结果正确，有创新（如自研系统偏移补偿策略） |
| 良好 | 28-35 | 步骤完整，结果正确 |
| 一般 | 24-27 | 步骤较完整，有小错误 |
| 较差 | <24 | 步骤缺失，错误较多 |

#### 综合项目评分标准
| 等级 | 分数 | 标准 |
|-----|------|------|
| 优秀 | 27-30 | 视觉抓取闭环成功（含HSV检测+深度定位+TF变换+IK抓取） |
| 良好 | 22-26 | 闭环功能完整但成功率偏低 |
| 一般 | 18-21 | 闭环部分功能缺失 |
| 较差 | <18 | 闭环未跑通 |

---

## 七、参考资源

### 7.1 教材
1. 《机器人学导论》（John J. Craig）— 覆盖 FK/IK/DH 参数基础
2. 《ROS2 机器人开发实践》（胡春旭）— ROS2 节点/Launch/参数化基础
3. 《Modern Robotics》（Kevin M. Lynch）— 运动学与现代控制理论

### 7.2 参考资料
1. MoveIt2 官方文档：https://moveit.picknik.ai/main/index.html
2. Gazebo 官方文档：http://gazebosim.org/docs
3. car1 机械臂 URDF 源码：`ros2_ws/src/xflz_eai_car1/simulations/`
4. arm_controller 源码：`ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/`
5. Web 运动学仿真器：`ros2_ws/src/xflz_eai_car1/test/car1_web_server/`
6. 视觉抓取源码：`ros2_ws/src/xflz_eai_car1/app/car1_app/`

### 7.3 工具软件
- Ubuntu 22.04 + ROS2 Humble
- RViz2 + Gazebo 11 + MoveIt2
- Python 3.10 + rclpy + tf_transformations
- Three.js + WebSocket（car1_web_server）
- OpenCV 4.x + cv_bridge
- rqt + rqt_image_view

---

## 八、先修课程

| 课程名称 | 要求程度 |
|---------|---------|
| Python 编程 | 必须 |
| 机器人学/运动学基础 | 必须 |
| 机器人 ROS2 应用与开发 | 必须 |
| 线性代数（矩阵运算） | 建议 |
| 操作系统（Linux） | 建议 |

---

## 九、教学设备

| 设备名称 | 数量/组 | 用途 |
|---------|--------|------|
| 具身智能实验箱 B2（含 5 自由度机械臂 + 深度相机） | 1 台/人 | 机械臂实机控制与视觉抓取 |
| 具身智能机器人小车 C1 | 1 台/组（4 人） | 端到端抓取应用演示 |
| 舵机调试板（带 USB 转串口） | 1 套/人 | 舵机零位校准与 PWM 调试 |
| 工作站（Ubuntu 22.04 + ROS2 Humble） | 1 台/人 | URDF/MoveIt2/Gazebo 仿真与节点开发 |
| 浏览器（Chrome/Edge） | - | car1_web_server 运动学仿真 |

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初始化 7 章 32h，覆盖 car1 5自由度机械臂从URDF到视觉抓取全链路，7 个实验（6×4h + 1×8h） |
| v1.1 | 2026-08-10 | 第 1 章新增知识点 **1.3.4 抓取流程感性认识**（grasp_demo 演示）；新增教学活动"演示：grasp_demo 8 步流程"和"问题引导：方块移位后抓取失败"；同步 course_spec.csv 与 experiment-1.md 中 grasp_demo 相关内容 |
| **v1.2** | 2026-08-10 | **重大重构 exp02/exp03 教学体系**。原因：用户反馈 exp02 主题应为"底层协议与裸机控制"，exp03 主题应为"ROS2 架构认知与动作回放"，**严禁在 exp03 引入 IK 算法**。变更如下：**(1) 第 2 章标题改为"底层舵机通信与裸机控制"**，新增教学活动"cutecom 验证协议 / interactive_mode / save-yaml 导出"，新增知识点 2.1.4 CRC8、2.2.1~2.2.3 串口权限与 interactive_mode、2.3.1~2.3.2 协议层对比；**(2) 第 3 章标题改为"ROS2 架构与动作回放"**，从"设计性"提升为"综合性"，新增教学活动"rqt_graph 拓扑 / joint_command 弧度 / action_player 节点回放 / servo_calib GUI"，新增 8 个 ROS2 知识点（bringup 拓扑、rqt_graph、node list、joint_command、PWM↔rad、action_player 节点、YAML 兼容、回放模式），**严禁** target_pose/pick/place；**(3) 能力目标 3 同步更新**为"test_servo_direct 裸机录制 + bringup+action_player 节点回放"；**(4) 实验项目表格** exp02 知识点范围更新为 2.1.1~2.3.2，exp03 范围更新为 3.1.1~3.4.2（标题改为"机械臂ROS2架构认知与动作回放实验"），实验类型分布同步更新。同步 `experiment-2.md` / `experiment-3.md` / `EXP005_lab_guide.md` / `course-spec.yaml` / `EXP005_knowledge_graph.md` |
