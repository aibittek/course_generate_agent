---
course_code: EXP005
course_name: 机器人机械臂应用与开发
version: v1.0
generated_at: 2026-08-04
generator: SyllabusAgent
source_spec: courses/sheet1/arm_practice/_meta/course-spec.yaml
csv_sha256: da0440a5b4b86f14717a1de1891e48fec13344483f8bf6fab7b0c97b31a420f9
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
3. 能够基于 test_servo_direct.py 录制并回放抓取放置动作，处理零位校准与软限位
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

#### 重点难点
- **重点**: URDF→RViz→MoveIt2→Gazebo 完整仿真链路的搭建与使用
- **难点**: MoveIt2 规划组配置与 Gazebo ros2_control 桥接的协同

#### 教学活动
- [x] 案例分析：对比仿真与实机控制的安全/效率差异
- [x] 动手实验：exp01 机械臂URDF仿真运动控制

#### 对应知识点
1.1.1 URDF概念 / 1.1.2 link/joint / 1.1.3 TF树 / 1.2.1 display.launch / 1.2.2 TF渲染 / 1.2.3 MoveIt2插件 / 1.3.1 Gazebo概念 / 1.3.2 gazebo_arm.launch / 1.3.3 joint_trajectory

---

### 第2章 底层舵机通信与ROS2控制

#### 教学内容
- STM32 板载总线舵机的 1Mbps 串口协议与帧格式
- PWM 范围（500~2500）与 PWM↔弧度换算（1500+rad/0.002356）
- ROS2 topic（/arm/joint_command）与 service（/arm/set_gripper, /arm/go_home）
- arm_controller 节点的桥接架构与 50Hz 控制循环
- bringup.launch.py 一键启动

#### 重点难点
- **重点**: 通过 ROS2 接口直接控制真实舵机
- **难点**: 50Hz 控制循环的时序保证与 STM32 串口帧的实时性

#### 教学活动
- [x] 演示：通过 ros2 topic pub 实时摆动机械臂
- [x] 动手实验：exp02 机械臂底层协议与控制

#### 对应知识点
2.1.1 1Mbps串口 / 2.1.2 PWM公式 / 2.1.3 帧格式 / 2.2.1 joint_command / 2.2.2 set_gripper / 2.2.3 go_home/work / 2.3.1 arm_controller / 2.3.2 50Hz循环 / 2.3.3 bringup.launch

---

### 第3章 零位校准与动作录制回放

#### 教学内容
- 舵机零位校准的概念与软件层 offset 补偿（不写EEPROM）
- servo_calib.launch.py 校准 GUI 的使用
- test_servo_direct.py 交互式 PWM 调试（+/-/[/] 键）
- 命名快照（home/work/pick/place）与 YAML 动作文件结构
- action_player.launch.py 的普通/单步/循环/急停模式

#### 重点难点
- **重点**: 通过录制+回放实现动作的快速复用
- **难点**: 软限位在录制过程中的保护机制与回放急停的可靠性

#### 教学活动
- [x] 演示：从零位校准到录制抓取放置全过程
- [x] 动手实验：exp03 机械臂零位校准与动作录制

#### 对应知识点
3.1.1 零位校准 / 3.1.2 软件offset / 3.1.3 servo_calib / 3.2.1 test_servo_direct / 3.2.2 键盘调试 / 3.2.3 命名快照 / 3.3.1 YAML格式 / 3.3.2 action_player / 3.3.3 单步/循环/急停

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
| 1 | 机械臂URDF仿真运动控制实验 | 4h | 验证性 ⭐ | 1.1.1~1.3.3 |
| 2 | 机械臂底层协议与控制实验 | 4h | 验证性 ⭐⭐ | 2.1.1~2.3.3 |
| 3 | 机械臂零位校准与动作录制实验 | 4h | 设计性 ⭐⭐ | 3.1.1~3.3.3 |
| 4 | 机械臂运动学控制原理实验 | 4h | 验证性 ⭐⭐ | 4.1.1~4.4.3 |
| 5 | 机械臂IK解算实验 | 4h | 综合性 ⭐⭐⭐ | 5.1.1~5.4.3 |
| 6 | 机械臂IK固定抓取实验 | 4h | 综合性 ⭐⭐⭐ | 6.1.1~6.4.3 |
| 7 | 机械臂基于视觉的动态抓取实验 | 8h | 综合性 ⭐⭐⭐ | 7.1.1~7.6.3 |
| - | **合计** | **32h** | - | - |

### 实验类型分布
- 验证性：2 个（28.6%）
- 设计性：1 个（14.3%）
- 综合性：3 个（42.9%）
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
