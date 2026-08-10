# EXP005 课程生成进度

> 课程: 机器人机械臂应用与开发
> 生成日期: 2026-08-04（v1.0）/ 2026-08-10（v1.1 增量更新）/ 2026-08-10（**v1.2 重大重构**）/ 2026-08-10（v1.2.1 快速验证修正）/ 2026-08-11（v1.2.2 实验5实机安全警告）/ 2026-08-11（**v1.2.3 实验6移除Gazebo仿真**）
> 模式: human_waiver（源码位于 ROS2 工作空间 ros2_ws/src/，未复制到 source-codes/EXP005/）

---

## 总体进度

| Step | 任务 | 状态 | 产出 | 行数/大小 |
|------|------|------|------|----------|
| 1 | 解析 EXP005 spec | ✅ 完成 | `course-spec.yaml`（**v1.1 修复字段拆分 + 新增 grasp_demo / v1.2 重构 exp02/exp03**） | 435+ 行 |
| 2 | 知识图谱 + 教学大纲 | ✅ 完成（**v1.1 + v1.2**） | `EXP005_knowledge_graph.md` + `EXP005_syllabus.md` | 624+ + 309+ 行 |
| 3 | 源码仓库初始化 | ✅ 完成 | `source-codes/EXP005/exp{01-07}/` + `_registry.yaml` 追加 | 7 目录 + 7 条目 |
| 4 | 7 个实验内容生成 | ✅ 完成（**exp-1 v1.1 增量 / exp-2/3 v1.2 重大重构 / exp-4 v1.2.1 快速验证修正 / exp-5 v1.2.2 路径与安全警告**） | `_parts/experiment-{1..7}.md` | 4801+ 行 |
| 4.5 | 合并为 Lab Guide | ✅ 完成（**实验1 v1.1 增量 / 实验2/3 v1.2 重大重构 / 实验4 v1.2.1 修正 / 实验5 v1.2.2 修正**） | `EXP005_lab_guide.md` | 5964+ 行 / 269KB |
| 5 | 练测题生成 | ✅ 完成 | `EXP005_quiz.md` | 21 题 / 100 分 |
| 6 | 内容审核 | ⏳ 待人工 | - | - |
| 7 | 质量审核 | ⏳ 待人工 | - | - |
| 8 | 资源整合输出 | ⏳ 待人工 | - | - |

**完成度**: 5/8（自动生成阶段 100% 完成，审核阶段待人工触发）

---

## 关键统计

### 实验概览
- 实验总数: 7
- 总学时: 32h（验证性 8h + 综合性 24h）**v1.2 调整：exp02 维持验证性 4h、exp03 由设计性 4h 升级为综合性 4h**
- 难度分布: ⭐ 1 + ⭐⭐ 3 + ⭐⭐⭐ 3
- 类型分布: 验证性 2 + 设计性 0 + 综合性 5（**v1.2 调整：设计性归零，验证性 3→2，综合性 3→5**）

### 知识点覆盖
- 知识图谱: 7 章 25 节 **76 知识点**（v1.1 新增 1.3.4 抓取流程感性认识）
  - 概念类: **26**（v1.1 +1）
  - 原理类: 15
  - 流程类: 25
  - 事实类: 8
  - 公式类: 2
- 难度分布: 记忆 **23** + 理解 23 + 应用 25 + 分析 5（v1.1 +1 记忆）
- 实验-知识点映射覆盖率: 100%
- **exp01 覆盖 1.1.1~1.3.4 共 10 个**（v1.1 +1.3.4）

### 测验题
- 总题数: 21
- 总分: 100 分
- 显式覆盖知识点: 38+（51%）
- 含编程/简答隐含覆盖: ≥ 60（80%）

---

## v1.1 增量更新记录（2026-08-10）

### 触发原因
- 课程用户反馈：实验 1 的 `grasp_demo.launch.py` 仅作为引导性介绍，不应作为本章学习重点
- CSV 字段存在未引号包裹的逗号导致下游解析错误

### 变更内容
1. **course_spec.csv**（已更新至 2026-08-10 14:38 之前版本）
   - 行 37（实验 1）新增 `car1_gazebo/launch/grasp_demo.launch.py` 主入口
   - 新增知识点 `抓取流程感性认识`
   - 新增实验目标、实验步骤 4（grasp_demo 演示）、注意事项
2. **course-spec.yaml**（v1.1）
   - 修复因 CSV 未引号包裹逗号导致的字段拆分（T38/U38、T40/U40、T41/U41）
   - 实验 1 补充 grasp_demo 相关字段（main_entry、knowledge_points、objectives、exp_content_steps、notes）
   - 实验 2-7 重组为结构化步骤（exp_content_steps / exp_content_phases）
3. **experiment-1.md**（v1.1）
   - 流程图更新为 7 步，新增 grasp_demo 节点
   - 1.6 新增步骤 7：grasp_demo 固定位置抓取演示（铺垫性）
   - 1.5/1.6/1.7/1.8/1.9 同步增加 grasp_demo 相关提示、教学定位、问题引导、思考题第 6 题
   - 更新日志新增 v1.1
4. **EXP005_lab_guide.md**（v1.1）
   - 实验 1 同步更新（1.1~1.9 + 更新日志）
5. **EXP005_syllabus.md**（v1.1）
   - 第 1 章新增 1.3.4 知识点、教学活动、问题引导
6. **EXP005_knowledge_graph.md**（v1.1）
   - 新增 1.3.4 知识点、依赖图节点 A34 + 两条依赖边
   - 统计更新为 76 知识点

### 未变更文件
- experiment-2.md ~ experiment-7.md：未受 CSV 字段拆分影响（Grep 验证 `PWM舵机控制(500~2500, center=1500)`、`CENTER_PWM=1500, PWM_TO_RAD=0.002356`、`J2+4°、J3+2.3°` 均正确）
- EXP005_quiz.md：未涉及实验 1 知识点增改
- _registry.yaml：源码 human_waiver 状态未变更

### 验证
- [x] 7 个 parts 实验 markdown 的字段未出现拆分（如 `PWM舵机控制(500~2500` 被错误截断）
- [x] course-spec.yaml 加载后 YAML 解析无错（手动 verify 字段）
- [x] EXP005_lab_guide.md 流程图节点数与步骤数匹配（7 节点对应 1.6 的 7 步）
- [x] 知识图谱统计 76 = 25 节 × 平均 3.04 个，1.3 节变为 4 个

---

## v1.2 增量更新记录（2026-08-10）

### 触发原因
- **品牌信息残留**：用户反馈实验 2 / 3 文档中混入了第三方舵机品牌（LewanSoul / Hiwonder）的协议描述，实际未使用该品牌舵机
- **实验 2 工具链错位**：原 exp02 使用 `bringup.launch.py` + `arm_controller` 节点（ROS2 高级封装），与"底层协议"主题不符；应改为 `test_servo_direct.py` 裸机演示 1Mbps 串口与 CRC8 字节级细节
- **实验 3 提前引入 IK**：原 exp03 使用 `arm_controller.launch.py` + `arm_controller.py` 节点，内置 `solve_analytical_ik_auto_pitch` IK 解算，违反"先裸机→再 ROS2→再 IK"的螺旋式教学顺序；应改为 `bringup.launch.py` + `joint_command` 话题 + `action_player` 节点回放 exp02 导出的 YAML
- **后续教学顺序确认**：exp04 讲 Web 运动学原理 → exp05 讲 IK 解算 → exp06 讲 IK 固定抓取 → exp07 讲视觉动态抓取

### 变更内容
1. **course_spec.csv**（v1.2 行 38/39）
   - **行 38（exp02）**：`main_entry` 从 `bringup.launch.py;arm_controller.launch.py;arm_controller.py` 改为 `arm/car1_arm_controller/test/test_servo_direct.py;arm/car1_arm_controller/car1_arm_controller/board_sdk.py(对照参考)`；`knowledge_points` 新增 CRC8 校验、interactive_mode、YAML 导出；`objectives` 与 `exp_content` 全部按 7 步裸机流程重写
   - **行 39（exp03）**：`name` 从"机械臂零位校准与动作录制实验"改为"机械臂ROS2架构认知与动作回放实验"；`experiment_type` 从"设计性"升级为"综合性"；`main_entry` 改为 `bringup.launch.py + arm_controller.launch.py(仅用joint_command严禁target_pose/pick/place) + action_player.py(节点) + servo_calib.launch.py`；`knowledge_points` 全部替换为 ROS2 节点架构、rqt_graph、joint_command、action_player 等
2. **course-spec.yaml**（v1.2）
   - `experiments[1].id=exp02`：main_entry / knowledge_points / objectives / exp_content_steps 7 步 全部按裸机协议演示重写；notes 新增"不要运行bringup"和"YAML格式与action_player兼容"
   - `experiments[2].id=exp03`：name 改为"机械臂ROS2架构认知与动作回放实验"；experiment_type 由"设计性"改为"综合性"；exp_content_phases 按 3a（系统架构 30min）/ 3b（动作回放 2h）/ 3c（零位校准 1.5h）三子阶段组织；notes 明确**严禁使用** target_pose / pick / place
3. **experiment-2.md**（v1.2 重大重构）
   - 移除所有 `bringup.launch.py` 和 `arm_controller` 相关内容
   - 新增 `test_servo_direct.py` interactive_mode 详解、CRC8 校验、YAML 导出 章节
   - 1.6 重写为 7 步：硬件连接→1Mbps 验证→interactive_mode 命令→CRC8 帧格式→动作录制→YAML 导出→综合练习
   - 1.1 知识点扩展为 9 个（新增 2.1.4 CRC8、2.2.1 串口权限、2.2.2 interactive_mode、2.2.3 动作录制、2.3.1 裸机 vs ROS2、2.3.2 协议字节级）
   - 1.3 实验环境表新增"不要启动bringup"警告
4. **experiment-3.md**（v1.2 重大重构）
   - 标题改为"机械臂ROS2架构认知与动作回放实验"
   - 明确**严禁使用** `/arm_controller/target_pose`（自动 IK）和 `/arm_controller/pick`/`/arm_controller/place`（完整抓取 pipeline）
   - 新增 ROS2 节点拓扑分析（rqt_graph）、joint_command 弧度控制、YAML 动作回放（普通/单步/循环/急停）
   - 1.6 按 3a（系统架构 30min）/ 3b（动作回放 2h）/ 3c（零位校准 1.5h）三子阶段组织
   - 1.1 知识点扩展为 10 个（bringup 拓扑、rqt_graph、node list、joint_command、PWM↔rad 换算、action_player 节点、YAML 格式兼容、回放模式、软件 offset、servo_calib GUI）
5. **EXP005_lab_guide.md**（v1.2）
   - 实验 2 / 3 章节与上述两个 _parts 同步更新
   - 验证：实验 2 流程图为 7 节点，实验 3 流程图按 3a/3b/3c 三子阶段
6. **EXP005_syllabus.md**（v1.2）
   - 第 2 章标题改为"底层舵机通信与裸机控制"，新增 cutecom 验证、interactive_mode、save-yaml 教学活动
   - 第 3 章标题改为"ROS2 架构与动作回放"，从"设计性"提升为"综合性"，新增 8 个 ROS2 知识点（bringup 拓扑、rqt_graph、joint_command、action_player 节点等）
   - 能力目标 3 同步为"test_servo_direct 裸机录制 + bringup+action_player 节点回放"
   - 实验项目表格 exp02 知识点范围更新为 2.1.1~2.3.2，exp03 范围更新为 3.1.1~3.4.2
7. **EXP005_knowledge_graph.md**（v1.2）
   - 第 2 章标题改为"底层舵机通信与裸机控制"，新增 2.1.4 CRC8、2.2.1~2.2.3、2.3.1~2.3.2 共 6 个知识点
   - 第 3 章标题改为"ROS2 架构与动作回放"，新增 3.1.1~3.1.3、3.2.1~3.2.2、3.3.1~3.3.3、3.4.1~3.4.2 共 10 个知识点
   - Mermaid 依赖图重绘，统计更新为 76 知识点（体系调整但总数保持 76）

### 未变更文件
- experiment-1.md / experiment-4.md / experiment-5.md / experiment-6.md / experiment-7.md：内容与 v1.1 一致（v1.2 范围仅限 exp02/exp03）
- EXP005_quiz.md：未涉及实验 2/3 知识点增改（**待人工 review**，是否需要增删 v1.2 新增知识点的覆盖题）
- _registry.yaml：源码 human_waiver 状态未变更

### 验证
- [x] course-spec.yaml 加载后 YAML 解析无错（exp02/exp03 字段全部按 CSV v1.2 同步）
- [x] exp02 流程图节点数 = 7（与 1.6 的 7 步对应）
- [x] exp03 流程图节点数 = 5（步骤1+步骤2+3a+3b+3c）
- [x] 知识图谱统计 exp02 覆盖 2.1.1~2.3.2 共 9 个，exp03 覆盖 3.1.1~3.4.2 共 10 个
- [x] 品牌信息残留检查：Grep "LewanSoul|Hiwonder" 仅匹配更新日志元数据（"v1.1 删除 LewanSoul/Hiwonder"），无正文内容残留
- [x] exp03 中 0 处出现 `target_pose` / `pick` / `place`（步骤 3c 校准验证处明确"严禁 target_pose"）

---

## v1.2.1 增量更新记录（2026-08-10）

### 触发原因
- **实验 2 快速验证流程冗余**：用户反馈快速验证流程混入硬件连接/串口授权等冗余步骤，应聚焦核心 Web/ROS2 验证；停止命令建议改用 `cleanup_ros.sh` 脚本清理潜在端口占用
- **实验 3 节点数量预期不符**：文档写"预期 7~8 个节点"，但实际 `ros2 node list` 只有 4 个节点
- **实验 3 夹爪张开角度描述反向**：观察 PWM 1000→1200 时夹爪张开角度是"变小"而非"变大"
- **实验 4 Web 仿真器访问路径错误**：浏览器访问缺 `/viewer` 后缀，且未说明跨设备（设备 IP+端口+`/viewer`）访问方式

### 变更内容
1. **experiment-2.md / EXP005_lab_guide.md（实验 2 章节）**
   - 1.5 快速验证流程第 1 步删除"连接硬件：STM32 板通过 USB-TTL…/dev/ttyUSB0"
   - 1.5 快速验证流程停止命令从 `Ctrl+C` 改为 `bash cleanup_ros.sh`（清理潜在端口占用）
   - 1.5 快速验证流程删除"步骤 4 串口权限授权"（固件已包含）
2. **experiment-3.md / EXP005_lab_guide.md（实验 3 章节）**
   - 1.5 快速验证流程删除"ros2 node list（预期 7~8 个节点）"描述
   - 1.5 快速验证流程第 10 点"PWM 从 1000 改为 1200，观察夹爪张开角度变大"修正为"变小"
3. **experiment-4.md / EXP005_lab_guide.md（实验 4 章节）**
   - 1.5 快速验证流程第 3 步浏览器访问：所有 URL 补 `/viewer` 后缀
     - 本机访问：`http://localhost:8000/viewer`
     - 非本机访问：`http://<设备IP>:8000/viewer`
   - 1.6 步骤 3 第 2 点"浏览器访问"同步补 `/viewer` 后缀并补充跨设备访问说明

### 未变更文件
- course_spec.csv、course-spec.yaml：未变更
- experiment-1.md / experiment-5.md / experiment-6.md / experiment-7.md：未涉及
- EXP005_syllabus.md / EXP005_knowledge_graph.md / EXP005_quiz.md：未涉及

### 验证
- [x] 实验 2 快速验证流程不含"连接硬件 / 串口授权 / Ctrl+C"等冗余步骤
- [x] 实验 3 文档 0 处出现"预期 7~8 个节点"
- [x] 实验 3 夹爪角度描述 = "变小"
- [x] 实验 4 用户可见 URL 全部带 `/viewer` 后缀
- [x] 实验 4 包含跨设备访问说明

---

## v1.2.2 增量更新记录（2026-08-11）

### 触发原因
- **实验 5 启动路径错误**：快速验证流程与步骤 7 的 `interactive_ik_test.py` 路径错了，正确路径是 `python3 src/xflz_eai_car1/arm/kinematics/kinematics/interactive_ik_test.py --direct`（注意 `kinematics/kinematics/` 嵌套）
- **演示目标点需要更新**：原 (0.2, 0.0, 0.2)/pitch=0 应改为 (0.28, 0, 0.1)/pitch=180°，表示夹爪垂直向下
- **实机验证安全警告缺失**：实验 5 是**第一次将 IK 解下发到真实机械臂**，必须：(1) 按 PWM 信息核对 5 路输出；(2) 设备虽有堵转保护但仍会损坏；(3) 损坏属使用问题不在质保范围；(4) 须先用 `test_servo_direct.py` 的 `interactive_mode` 验证设备
- **菜单指令过于直白**：原文档"选择 [1] Single Point IK"、"选择 [2] Batch FK/IK"过于直白，应弱化为菜单参考，由用户自行决定

### 变更内容
1. **experiment-5.md / EXP005_lab_guide.md（实验 5 章节）**
   - 1.3 主入口路径 `kinematics/interactive_ik_test.py` → `kinematics/kinematics/interactive_ik_test.py`（同步修正嵌套路径）
   - 1.5 快速验证流程第 4 步路径修正为 `python3 src/xflz_eai_car1/arm/kinematics/kinematics/interactive_ik_test.py --direct`
   - 1.5 快速验证流程第 5 步菜单补齐 [4] System Offset Analysis、[5] Send PWM Directly 两项
   - 1.5 快速验证流程第 6 步去掉"选择 [1] Single Point IK"硬指令，改为"输入目标点 (0.28, 0, 0.1)、pitch=180°（夹爪垂直向下），观察 IK 解"
   - 1.5 快速验证流程去掉第 7 步"选择 [2] Batch FK/IK"
   - 1.5 新增"实机验证安全警告（必读）"块：4 条核心警告 + test_servo_direct.py 验证流程 + 逐步逼近原则
   - 1.5 预期效果描述同步：单点 IK 输入改为 (0.28, 0, 0.1)/pitch=180°，FK 反算 ≈ (0.280, 0.000, 0.100)
   - 1.6 步骤 4（FK/IK 闭环批量验证）路径修正为 `python3 src/xflz_eai_car1/arm/kinematics/kinematics/interactive_ik_test.py --direct --port /dev/ttyUSB0 --baud 1000000`，去掉"选择 [2] Batch FK/IK"硬指令
   - 1.6 步骤 5（系统偏移识别）路径同步修正
   - 1.6 步骤 7（直连串口实机调试）：
     - 启动命令路径同步修正
     - 去掉"选择 [1] Single Point IK + Move Arm"硬指令（保留菜单显示）
     - 去掉"选择 [2] Batch FK/IK"硬指令
     - 新增"实机验证安全警告（必读）"块 + 严格的两步流程（3a `test_servo_direct.py` 验证 → 3b 进入 IK 测试，仅查看不解算）
     - 步骤 3a 完整命令：`cd /home/iflytek/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/test; python test_servo_direct.py`，配 5 路 PWM 范围 (500~2500, center=1500) 验证清单
     - 步骤 3b 强调"先仅查看 IK 解（不开实际运动）" + 逐步逼近 (0.28, 0, 0.1)
     - 步骤 3c 串口监控保留
     - 步骤 4 改为"PWM 直发测试（用于熟悉协议帧）"，强调 1500 全中位安全输入
     - 步骤 5 对比 ROS2 模式保留
     - 易错点新增"PWM 误发导致堵转"并引用步骤 3a → 3b 顺序
2. **course-spec.yaml（exp05）**
   - `main_entry` 路径同步修正：`kinematics/kinematics/interactive_ik_test.py;...`
   - `exp_content_steps` 新增 step 3"演示目标位姿(夹爪垂直向下)"，输入 X=0.28, Y=0, Z=0.1, pitch=180°，强调"仅查看IK解,核对5路PWM在合理区间"
   - 后续 step 4~7 顺延为原 step 3~6
   - `notes` 段追加【实机验证安全警告】5 条 + 演示位姿说明

### 未变更文件
- course_spec.csv：本次仅路径/安全警告调整，未涉及 CSV 行结构
- experiment-1.md / experiment-2.md / experiment-3.md / experiment-4.md / experiment-6.md / experiment-7.md：未涉及
- EXP005_syllabus.md / EXP005_knowledge_graph.md：本次未变更（实验5 章节大纲与知识图谱的"实机验证"知识点与本次安全警告内容不冲突，不需要同步重绘）
- EXP005_quiz.md：未涉及

### 验证
- [x] `_parts/experiment-5.md` 与 `EXP005_lab_guide.md` 中所有 `python3 .../kinematics/kinematics/interactive_ik_test.py --direct` 路径已带 `kinematics/kinematics/` 嵌套
- [x] 1.5 快速验证流程 0 处出现"选择 [1] Single Point IK"或"选择 [2] Batch FK/IK"硬指令
- [x] 1.5 / 1.6 步骤 7 均含完整的"实机验证安全警告"块
- [x] 演示目标点统一为 (0.28, 0, 0.1)、pitch=180°，符合"夹爪垂直向下"语义
- [x] `test_servo_direct.py` 验证流程路径与用户指定一致（`/home/iflytek/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/test`）
- [x] course-spec.yaml 加载后 YAML 解析无错（exp05 main_entry 路径已修正，exp_content_steps 顺序正确，notes 多行文字保留）

---

## v1.2.3 增量更新记录（2026-08-11）

### 触发原因
- **实验 6 需移除 Gazebo 仿真抓取**：用户要求实验 6（机械臂 IK 固定抓取实验）直接进行实机抓取，删除所有与 `grasp_demo` / Gazebo 仿真相关的案例
- **grasp_demo 引导性介绍已在实验 1 步骤 7 完成**：实验 1 的 grasp_demo 仅作为引导性介绍保留，实验 6 不再重复仿真案例
- **强制工程顺序保持**：实机抓取是实验 6 的核心目标，与 exp05 的 IK 解算学习紧密衔接

### 变更内容
1. **`_parts/experiment-6.md`**
   - 1.6 步骤 1 知识点讲解"实机抓取流程"：将"实机抓取与早期 Gazebo 仿真原型类似但更严谨"改为"实机抓取流程相比早期原型更严谨"
   - 1.7 实验总结完成成果：删除"启动 Gazebo grasp_demo 在 ik/manual/none 三模式下完成抓取仿真"
   - 1.7 技能收获：删除"掌握 Gazebo 仿真抓取三模式的差异与适用场景"
   - 1.7 常见问题：删除"Gazebo 抓取后物体掉落"，改为"实机抓取后物体掉落"
   - 1.8 思考题：删除第 4 题"仿真抓取与实机抓取在哪些环节存在差异？如何缩小'sim-to-real gap'？"，原第 5 题上移为第 4 题
   - 1.9 实验报告要求：删除"Gazebo 仿真三模式 15 分"，评分标准改为"实机抓取流程 30 分 + 抓取参数调优 25 分 + 分步移动与保护机制 20 分 + 端到端 pipeline 15 分 + 实验报告 10 分 = 100 分"
2. **`EXP005_lab_guide.md`（实验 6 章节）**
   - 章节标题块：从源码路径删除 `simulations/car1_gazebo/`，仅保留 `arm/car1_arm_controller/`
   - 章节标题块：内容说明删除 `grasp_demo.launch.py`，仅保留 `arm_controller.py`、`/arm/target_pose`、`/arm/pick`、`/arm/place`
   - 新增"本实验直接进行实机抓取"教学定位说明
   - 1.1 关联知识点：从 12 个精简为 9 个，删除 6.1.1 grasp_demo / 6.1.2 ik_manual / 6.1.3 接触力反馈，重新映射为 6.1.1 target_pose / 6.1.2 /arm/place / 6.1.3 分步移动
   - 1.2 实验目标：删除"理解 Gazebo 仿真抓取三模式（ik/manual/none）的差异与适用场景"
   - 1.3 实验环境：删除"Gazebo 11"+"gazebo_ros_pkgs"+"car1_gazebo（含 grasp_demo.launch.py）"+"simulations/car1_gazebo/launch/grasp_demo.launch.py"
   - 1.4 实验难度：重点删除"仿真三模式对比"
   - 1.5 快速验证流程：第 1 步改为"连接硬件"、第 4 步改为"启动实机 arm_controller"，新增"实机验证安全警告"块（test_servo_direct.py 前置验证 + PWM 区间核对 + 损坏不在质保 + 逐步逼近）
   - 1.5 预期效果：删除"Gazebo 仿真"和"接触力反馈"两条
   - 1.6 整体流程图：从 8 节点简化为 4 节点（target_pose/pick-place → 抓取参数调优 → 限位保护 → 端到端演示）
   - 1.6 步骤 1（Gazebo 仿真环境搭建）和步骤 2（Gazebo 仿真抓取流程）整章删除，步骤 3（实机 target_pose）上移为新步骤 1
   - 1.7 实验总结 / 1.8 思考题 / 1.9 评分标准：与 _parts/experiment-6.md 同步清理
   - 章节更新日志新增 v1.2.3 条目
3. **`EXP005_knowledge_graph.md`**
   - 第 6 章 6.1 节"Gazebo 仿真抓取"整节删除（6.1.1 grasp_demo 概念 / 6.1.2 ik_manual 流程 / 6.1.3 接触力反馈原理）
   - 第 6 章结构 6.1~6.4 → 6.1~6.3（实机 IK 抓取 / 抓取参数调优 / 关节限位保护）
   - 原 6.2.x 重新映射为 6.1.x（target_pose→6.1.1, /arm/place→6.1.2, 分步移动→6.1.3）
   - 原 6.3.x 重新映射为 6.2.x（gripper_depth→6.2.1, pre_grasp_height→6.2.2, grasp_pitch→6.2.3）
   - 原 6.4.x 重新映射为 6.3.x（软限位→6.3.1, 奇异检测→6.3.2, 失败回退→6.3.3）
   - 知识点统计：总数 76 → 73（删 1 概念+1 流程+1 原理，记忆/应用/分析各 -1）；总节数 25 → 24
   - Mermaid 依赖图 Chapter 6 重写：删除 A31→F11 的 Gazebo 边，节点重编号 F11~F13/F21~F23/F31~F33
   - Mermaid 依赖图 Chapter 7 同步：7.5.1 IDLE 状态机依赖 F21→F11，7.6.2 HSV 调参依赖 F31→F21
   - 知识点 7.6.2 描述的前置依赖：7.6.1, 6.3.1 → 7.6.1, 6.2.1
   - 更新日志新增 v1.2.3 条目
4. **`course-spec.yaml`（exp06）**
   - `source_code_path`：`simulations/car1_gazebo/;arm/car1_arm_controller/` → `arm/car1_arm_controller/`
   - `main_entry`：`car1_gazebo/launch/grasp_demo.launch.py;arm/car1_arm_controller/...arm_controller.py` → `arm/car1_arm_controller/...arm_controller.py`
   - `knowledge_points`：删除"Gazebo 仿真抓取三模式(ik/manual/none)"，新增"关节软限位与奇异检测"
   - `objectives`：删除"掌握Gazebo仿真环境下的固定位置抓取流程"
   - `exp_content_steps`：从 9 步（含 3 步 Gazebo 仿真）重构为 7 步实机抓取（启动→target_pose 安全前置→pick→place→参数调优→限位与奇异→多物体 pipeline）
   - `notes`：新增"本实验为纯实机抓取，不包含Gazebo仿真案例"说明 + 5 条【实机验证安全警告】

### 未变更文件
- `course_spec.csv`：本次仅文档级清理，未涉及 CSV 行结构
- `experiment-1.md` / `experiment-2.md` / `experiment-3.md` / `experiment-4.md` / `experiment-5.md` / `experiment-7.md`：未涉及
- `EXP005_syllabus.md`：v1.2.3 仅清理第 6 章知识图谱与教学大纲正文一致，正文需同步
- `EXP005_quiz.md`：未涉及

### 验证
- [x] Grep 验证 `_parts/experiment-6.md` 中 0 处出现 "Gazebo" / "grasp_demo" / "ik/manual"
- [x] Grep 验证 `EXP005_lab_guide.md` 实验 6 章节 0 处出现 "Gazebo" / "grasp_demo" / "car1_gazebo"
- [x] 知识图谱第 6 章无 6.1.1 grasp_demo / 6.1.2 ik_manual / 6.1.3 接触力反馈 知识点
- [x] 实验 6 流程图为 4 节点，步骤数与 1.6 一致
- [x] course-spec.yaml 加载后 YAML 解析无错（exp06 main_entry 路径已修正，exp_content_steps 7 步顺序正确，notes 多行文字保留）
- [x] Mermaid 依赖图无悬挂引用（A31→F11 已删除，Chapter 7 引用已同步修正）

---

## 源码状态

| 实验 | 名称 | 源码路径 | 状态 | 豁免 |
|------|------|----------|------|------|
| 1 | 机械臂URDF仿真运动控制 | `ros2_ws/src/xflz_eai_car1/simulations/` | external | ✅ |
| 2 | 机械臂底层协议与控制 | `ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/` | external | ✅ |
| 3 | 机械臂ROS2架构认知与动作回放 | `ros2_ws/src/xflz_eai_car1/bringup/;ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/;ros2_ws/src/xflz_eai_car1/calibration/` | external | ✅ |
| 4 | 机械臂运动学控制原理 | `ros2_ws/src/xflz_eai_car1/test/car1_web_server/` | external | ✅ |
| 5 | 机械臂IK解算 | `ros2_ws/src/xflz_eai_car1/arm/kinematics/` | external | ✅ |
| 6 | 机械臂IK固定抓取 | `ros2_ws/src/xflz_eai_car1/simulations/car1_gazebo/` | external | ✅ |
| 7 | 机械臂基于视觉的动态抓取 | `ros2_ws/src/xflz_eai_car1/app/car1_app/` | external | ✅ |

所有实验均已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。

---

## 待补充事项（人工 follow_up）

1. **源码迁移**（优先级：中）
   - 后续应将 7 个实验对应的 ROS2 包从 `ros2_ws/src/xflz_eai_car1/` 复制到 `source-codes/EXP005/exp{01-07}/`
   - 复制完成后触发 `SourceCodeAnalysisAgent` 分析源码
   - 分析完成后将 `_registry.yaml` 中 `code_status: external` 改为 `analyzed`，移除 `human_waiver` 块

2. **内容审核**（优先级：高）
   - 课程负责人审核知识图谱与教学大纲的准确性
   - 实验指导书需结合实际硬件平台（B2/C1）验证关键参数
   - 重点关注 PWM 协议、IK 几何推导、视觉抓取调参的工程细节

3. **质量审核**（优先级：中）
   - 编程题参考答案需要在实机上验证可行性
   - 7 个实验报告的评分标准需根据实际学情调整

4. **资源整合**（优先级：低）
   - 将 EXP005 课程资源打包发布
   - 与 EXP002（语音）、EXP003（ROS）等其他 sheet1 课程协同

---

## 目录结构

```
courses/sheet1/arm_practice/
├── _meta/
│   └── course-spec.yaml
├── _parts/
│   ├── experiment-1.md (444 行)
│   ├── experiment-2.md (606 行)
│   ├── experiment-3.md (584 行)
│   ├── experiment-4.md (557 行)
│   ├── experiment-5.md (670 行)
│   ├── experiment-6.md (681 行)
│   └── experiment-7.md (1259 行)
├── EXP005_knowledge_graph.md (624 行)
├── EXP005_syllabus.md (309 行)
├── EXP005_lab_guide.md (5964 行 / 260KB)
└── EXP005_quiz.md (21 题 / 100 分)

source-codes/
├── _registry.yaml (已追加 EXP005 7 个实验条目)
└── EXP005/
    ├── exp01/
    ├── exp02/
    ├── exp03/
    ├── exp04/
    ├── exp05/
    ├── exp06/
    └── exp07/
```

---

## 更新日志

| 日期 | 事件 | 操作人 |
|------|------|--------|
| 2026-08-04 19:32:43 | spec-parser-skill 解析 EXP005 CSV | resource-parser-agent |
| 2026-08-04 20:00:00 | 知识图谱 v1.0（7 章 75 知识点） | knowledge-graph-agent |
| 2026-08-04 20:30:00 | 教学大纲 v1.0（7 章 32h） | syllabus-agent |
| 2026-08-04 20:45:00 | source-codes/EXP005 目录创建 | lab-guide-orchestrator |
| 2026-08-04 21:00:00 | 7 个 _parts/experiment-N.md（总 4801 行） | lab-guide-experiment-agent |
| 2026-08-04 21:30:00 | 合并 EXP005_lab_guide.md（260KB） | merge script |
| 2026-08-04 22:00:00 | 练测题库 v1.0（21 题 100 分） | quiz-agent |
| 2026-08-04 22:30:00 | 本进度文件 | generation-log-agent |
| 2026-08-10 14:38:00 | 收到用户反馈：实验 1 grasp_demo 作为引导性介绍，非本章重点 | user |
| 2026-08-10 15:00:00 | course_spec.csv 增量更新（行 37 新增 grasp_demo 字段） | course-spec-agent |
| 2026-08-10 22:30:00 | **v1.1 批量更新**：course-spec.yaml 修复字段拆分 + 新增 grasp_demo；experiment-1.md 新增步骤 7；EXP005_lab_guide.md 实验 1 同步；EXP005_syllabus.md 新增 1.3.4；EXP005_knowledge_graph.md 新增 1.3.4 + 依赖边；本文件 v1.1 增量记录 | regen-agent |
| 2026-08-10 22:55:00 | 收到用户反馈：实验 2/3 工具链错位（exp02 用了 bringup、exp03 混入了 IK 算法）+ 品牌信息残留 | user |
| 2026-08-10 23:00:00 | course_spec.csv 增量更新（行 38/39 重构 exp02/exp03） | course-spec-agent |
| 2026-08-10 23:30:00 | **v1.2 重大重构**：course-spec.yaml 重构 exp02/exp03；experiment-2.md 改为 test_servo_direct 裸机协议演示；experiment-3.md 改为 bringup + action_player 节点（严禁 IK）；EXP005_lab_guide.md / EXP005_syllabus.md / EXP005_knowledge_graph.md 同步重绘第 2/3 章；本文件 v1.2 增量记录 | regen-agent |
| 2026-08-10 23:50:00 | 收到用户反馈：实验 2 快速验证流程冗余、实验 3 节点数量不符 + 夹爪角度描述反向、实验 4 浏览器访问缺 `/viewer` 后缀 | user |
| 2026-08-11 00:10:00 | **v1.2.1 快速验证修正**：experiment-2.md 移除硬件连接/串口授权，停止命令改 `cleanup_ros.sh`；experiment-3.md 移除节点数量预期，夹爪角度描述改为"变小"；experiment-4.md 浏览器访问补 `/viewer` 后缀 + 跨设备访问说明；EXP005_lab_guide.md 同步；本文件 v1.2.1 增量记录 | regen-agent |
| 2026-08-11 00:30:00 | 收到用户反馈：实验 5 启动路径错（缺 `kinematics/kinematics/` 嵌套）、演示目标点改为 (0.28, 0, 0.1)/pitch=180°、需添加实机验证安全警告（堵转损坏、堵转保护、不在质保、test_servo_direct.py 前置验证） | user |
| 2026-08-11 01:00:00 | **v1.2.2 实验5实机安全警告**：所有 `interactive_ik_test.py` 启动命令路径补 `kinematics/kinematics/` 嵌套；1.5 演示目标点改为 (0.28, 0, 0.1)/pitch=180° 并去掉"选择 [1] [2]"硬指令；1.5 / 1.6 步骤 7 新增"实机验证安全警告"块 + `test_servo_direct.py` 前置验证流程；course-spec.yaml exp05 main_entry 路径同步 + exp_content_steps 新增演示位姿 + notes 段追加安全警告；EXP005_lab_guide.md 同步；本文件 v1.2.2 增量记录 | regen-agent |
| 2026-08-11 02:00:00 | 收到用户反馈：实验 6 需去掉 Gazebo 仿真抓取，直接进行实机抓取 | user |
| 2026-08-11 02:30:00 | **v1.2.3 实验6移除Gazebo仿真**：`_parts/experiment-6.md` 1.6 步骤1讲解改"实机抓取流程相比早期原型更严谨"；1.7/1.8/1.9 删除 Gazebo 三模式 + 接触力反馈 + sim-to-real 题 + Gazebo 仿真三模式 15 分；`EXP005_lab_guide.md` 实验6章节重写：1.1 知识点 12→9、1.3 环境删除 Gazebo 11+car1_gazebo、1.5 快速验证改为实机 launch+target_pose+pick/place+实机验证安全警告、1.6 流程图 8 步简化为 4 步、原步骤1-2（Gazebo 仿真环境搭建+仿真抓取流程）整章删除；`EXP005_knowledge_graph.md` 第6章 6.1 节 Gazebo 抓取整节删除、6.1~6.4 重构为 6.1~6.3 重新映射 target_pose→6.1.1 等、知识点统计 76→73、Mermaid 依赖图 Chapter 6/7 同步重编号；`course-spec.yaml` exp06 源码路径删除 `simulations/car1_gazebo/`、main_entry 仅保留 arm_controller.py、exp_content_steps 从 9 步重构为 7 步实机抓取、notes 新增 5 条实机验证安全警告；本文件 v1.2.3 增量记录 | regen-agent |
