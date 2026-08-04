## 实验3：机械臂零位校准与动作录制实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/calibration/` 与 `ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/`，未复制到 `source-codes/EXP005/exp03/`。已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。后续补充源码后需触发 SourceCodeAnalysisAgent 并移除豁免。本指导书内容基于 `calibration/launch/servo_calib.launch.py`、`arm/car1_arm_controller/test/test_servo_direct.py`、`arm/car1_arm_controller/launch/action_player.launch.py` 等节点源码。

### 1.1 关联知识点

本实验对应第 3 章"零位校准与动作录制回放"，覆盖以下 9 个知识点：

- 3.1.1 零位校准 > 概念 > 零位校准指将舵机机械中位对齐到软件坐标系原点，避免关节角累积漂移
- 3.1.2 软件offset > 原理 > 软件层 offset 补偿（写入 servo_offsets.yaml）相比 EEPROM 写入更安全、可热更新
- 3.1.3 servo_calib > 流程 > `servo_calib.launch.py` 启动校准 GUI，逐关节发送测试 PWM 并记录补偿值
- 3.2.1 test_servo_direct > 概念 > `test_servo_direct.py` 提供键盘/菜单驱动的单舵机调试界面
- 3.2.2 键盘调试 > 流程 > 通过 `+/-/[/]` 键实时调整单关节 PWM 并观察响应，验证限位与零位
- 3.2.3 命名快照 > 概念 > 调试过程中将关键位姿（home/work/pick/place）记录为命名快照便于复用
- 3.3.1 YAML格式 > 概念 > 动作文件采用 YAML 列表结构，每项包含 joints/gripper/duration_ms 三个字段
- 3.3.2 action_player > 流程 > `action_player.launch.py` 支持普通/单步/循环三种回放模式，可设置紧急停止
- 3.3.3 单步/循环/急停 > 原理 > 单步模式逐动作暂停等待 Enter，循环模式按指定次数重复，紧急停止中断串口写

### 1.2 实验目标

1. 理解舵机零位校准的必要性（消除装配公差，避免角度累积漂移）— 原理理解
2. 掌握 servo_calib.launch.py 校准 GUI 的使用方法 — 流程掌握
3. 独立使用 test_servo_direct.py 完成抓取放置动作的交互式录制 — 独立完成
4. 能够将动作导出为 YAML 文件并通过 action_player 回放 — 独立完成
5. 能够在循环/单步/急停模式下验证动作的鲁棒性 — 迁移应用

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 具身智能实验箱B2 / 机器人小车C1（含 5 自由度机械臂、工作桌面、待抓取物体） |
| OS | Ubuntu 22.04 + ROS2 Humble |
| Python | 3.10 |
| 核心库 | rclpy、pyserial、yaml、pynput（键盘监听） |
| 校准工具 | servo_calib（图形化 GUI）、test_servo_direct.py（终端交互） |
| 动作文件 | `arm/car1_arm_controller/config/actions/home.yaml`、`pick.yaml`、`place.yaml` |
| 主入口 | `calibration/launch/servo_calib.launch.py`（零位校准 GUI）<br>`arm/car1_arm_controller/test/test_servo_direct.py`（交互式录制）<br>`arm/car1_arm_controller/launch/action_player.launch.py`（回放器） |

### 1.4 实验难度

- 难度: ⭐⭐ 中
- 重点: 舵机零位校准；test_servo_direct.py 交互式调试；YAML 动作文件结构
- 难点: 软件 offset 与 EEPROM 写入的取舍；回放过程中紧急停止的可靠性

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：

1. 连接硬件：确保机械臂通电、串口连接到工作站
2. 进入工作空间根目录：`cd ~/ros2_ws`
3. source 环境：`source /opt/ros/humble/setup.bash && source install/setup.bash`
4. 启动 arm_controller：`ros2 launch car1_arm_controller arm_controller.launch.py`
5. 启动交互式调试（新终端）：`python3 src/xflz_eai_car1/arm/car1_arm_controller/test/test_servo_direct.py`
6. 在终端中按数字键选择关节，按 +/- 微调 PWM，观察机械臂响应
7. 录制完成后回放：`ros2 launch car1_arm_controller action_player.launch.py yaml_file:=pick_place.yaml mode:=normal`

**预期效果描述**：
- **校准阶段**：servo_calib GUI 弹出后，5 个滑块分别控制 5 个关节，用户拖动滑块找到"机械中位"，点击"Save" 后写入 `servo_offsets.yaml`
- **调试阶段**：test_servo_direct.py 在终端打印菜单，提示 `[1-5] select joint, [+] increase, [-] decrease, [space] snapshot, [q] quit`
- **回放阶段**：action_player 按 YAML 中的动作列表依次执行，机械臂在 2-3 秒内完成 home→pick→place→home 的完整循环
- **循环模式**：设置 `loop_count:=3` 后动作循环 3 次后自动停止
- **急停模式**：回放过程中按 Ctrl+C 立即中断串口写，机械臂停在当前位置

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：舵机零位校准] --> B[步骤2：servo_calib GUI使用]
    B --> C[步骤3：test_servo_direct交互调试]
    C --> D[步骤4：命名快照保存]
    D --> E[步骤5：YAML动作文件生成]
    E --> F[步骤6：action_player普通回放]
    F --> G[步骤7：单步/循环/急停模式]
    G --> H[完成]
```

---

#### 步骤1：舵机零位校准原理（阶段一：能运行，20min）

> ⚠️ 本步骤对应 src 目录源码：`calibration/servo_offsets.yaml`、`arm/car1_arm_controller/config/servo_offsets.yaml`

**知识点讲解**：

**零位校准的必要性（3.1.1）**
- **原理**：每个舵机的"机械中位"（齿轮对齐的位置）与"软件零位"（URDF 中 0 rad 对应的 PWM）之间存在制造公差。car1 5 个舵机的典型偏差是 ±10 PWM 单位（约 ±2.4°）。如果不校准：(1) 不同舵机的"home"位姿视觉上不水平；(2) 多次运动后误差累积导致动作"漂移"；(3) MoveIt2 规划时坐标系不对齐。校准的目标是让每个舵机的"机械中位 = 软件 0 rad"。
- **源码对应**：`servo_offsets.yaml` 中 `joint_offsets: [0, 22, 13, 0, 0]` 字段

**软件 offset vs EEPROM 写入（3.1.2）**
- **原理**：car1 采用"软件层 offset"方案：(1) **不修改舵机 EEPROM**：原始中位 1500 保持不变；(2) **在 arm_controller 中应用 offset**：实际发送的 PWM = 目标 PWM + offset。例如机械中位实际在 PWM=1522，则 offset=22，所有目标 PWM 加上 22 才是"软件 0 rad"。这种方案的优势是：(1) 损坏时容易恢复（删除 offset 文件即可）；(2) 可热更新（修改 yaml 后重启节点即可）；(3) 不影响其他使用相同舵机的项目。
- **源码对应**：`arm_controller.py` 中 `self.current_pwms[i] += self.offsets[i]`

**操作步骤**：

1. 查看当前 servo_offsets.yaml：
   ```bash
   cat ~/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/config/servo_offsets.yaml
   # 预期：
   # # 5 关节 PWM 偏移（相对舵机出厂中位 1500）
   # joint_offsets:
   #   joint1: 0     # 底座
   #   joint2: 22    # 大臂（已校准）
   #   joint3: 13    # 小臂
   #   joint4: 0     # 腕部旋转
   #   joint5: 0     # 腕部俯仰
   ```

2. 计算 offset：
   - 假设关节 2 的机械中位在 PWM=1522（即发送 1500 时机械臂略偏离水平）
   - offset = 1522 - 1500 = +22
   - 写入 yaml：`joint2: 22`

3. 备份原始配置：
   ```bash
   cp servo_offsets.yaml servo_offsets.yaml.bak
   ```

**易错点**：
- ⚠️ **修改后机械臂动作异常** → **解决**：用 `.bak` 备份恢复，重新校准
- ⚠️ **不同关节的 offset 互相干扰** → **解决**：每次只修改一个关节，观察后再调下一个

---

#### 步骤2：servo_calib 校准 GUI 使用（阶段一：能运行，45min）

> ⚠️ 本步骤对应 src 目录源码：`calibration/launch/servo_calib.launch.py`、`calibration/servo_calib_node.py`

**知识点讲解**：

**servo_calib 校准工具（3.1.3）**
- **原理**：`servo_calib.launch.py` 启动一个图形化 GUI 工具（基于 PyQt 或 rqt），提供 5 个关节的独立控制面板。界面包括：(1) 关节选择标签（joint1~joint5）；(2) PWM 滑块（500-2500）；(3) 实时位置显示（rad/deg）；(4) "Save" 按钮（写入 servo_offsets.yaml）。校准流程为：选择关节 → 缓慢移动滑块 → 找到机械中位 → 记录偏差 → 保存。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/calibration/launch/servo_calib.launch.py`

**机械中位的视觉判断**
- **原理**：判断舵机"机械中位"的最直接方法是看机械结构。例如 joint2（大臂）的机械中位是"大臂水平向前"，此时 URDF 中 joint2=0 rad 对应大臂水平。但实际舵机中位可能偏差 ±10 PWM，因此需要微调至大臂绝对水平（与地面平行，可用水平仪辅助）。
- **源码对应**：人工观察

**操作步骤**：

1. 编译校准包：
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select calibration
   source install/setup.bash
   ```

2. 启动 arm_controller（必须先运行）：
   ```bash
   ros2 launch car1_arm_controller arm_controller.launch.py
   ```

3. 启动 servo_calib（新终端）：
   ```bash
   ros2 launch calibration servo_calib.launch.py
   # 预期：弹出 GUI 窗口，包含 5 个关节的控制面板
   ```

4. 校准 joint2（大臂）：
   - 在 GUI 中选择"Joint 2"
   - 缓慢拖动 PWM 滑块从 1400 到 1600
   - 观察大臂姿态，找到"大臂水平向前"的位置
   - 读取该位置的 PWM 值（例如 1522）
   - 在 "Offset" 输入框填入 22
   - 点击 "Apply"

5. 校准 joint3（小臂）：
   - 类似方法找到"小臂水平"的 PWM 值（例如 1513）
   - offset = 1513 - 1500 = 13
   - 填入 13 并 Apply

6. 校准剩余关节（可选）：
   - joint1（底座）：offset 通常为 0（旋转对称）
   - joint4/5（腕部）：offset 视具体装配而定

7. 保存配置：
   - 点击 "Save All" 按钮
   - 检查 `servo_offsets.yaml` 已更新

8. 验证校准结果：
   ```bash
   ros2 service call /arm/go_home car1_arm_msgs/srv/GoHome
   # 预期：机械臂回到 home 时各关节视觉上对齐（水平、垂直）
   ```

**易错点**：
- ⚠️ **校准后机械臂仍不齐** → **解决**：校准是渐进过程，可能需要"先粗调后精调"多轮迭代
- ⚠️ **GUI 启动报"display not found"** → **解决**：在工作站本地终端运行，不要通过 SSH 远程
- ⚠️ **Apply 后无响应** → **解决**：检查 arm_controller 是否运行，servo_calib 需要订阅 `/arm/joint_states`

---

#### 步骤3：test_servo_direct 交互式调试（阶段二：能理解，45min）

> ⚠️ 本步骤对应 src 目录源码：`arm/car1_arm_controller/test/test_servo_direct.py`

**知识点讲解**：

**test_servo_direct 调试工具（3.2.1）**
- **原理**：`test_servo_direct.py` 是一个终端交互式脚本，绕过 ROS2 直接通过串口控制单个舵机（也可通过 ROS2 模式）。优势是启动快、调试直观。交互菜单包括：(1) 选择关节（1-5）；(2) +/- 调整 PWM（步长 10）；(3) [/] 步长切换（1/10/50）；(4) 空格 记录当前位姿为命名快照；(5) q 退出。
- **源码对应**：`ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/test/test_servo_direct.py`

**键盘单舵机调试（3.2.2）**
- **原理**：通过键盘事件实时调整单个关节 PWM 是最直观的调试方式。+/- 按步长增加/减少 PWM，每按一次舵机立即响应，调试者可以"边看边调"找到最佳位置。相比 GUI，键盘调试更适合"盲调"场景（如机械臂已伸出，视线无法同时看屏幕和机械臂）。
- **源码对应**：`pynput.keyboard.Listener` 监听键盘事件

**操作步骤**：

1. 查看脚本帮助：
   ```bash
   python3 ~/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/test/test_servo_direct.py --help
   # 预期输出 usage
   ```

2. 启动直连串口模式（绕过 ROS2）：
   ```bash
   python3 test_servo_direct.py --direct --port /dev/ttyUSB0
   # 预期打印菜单：
   # === Servo Direct Test ===
   # Current joint: 1
   # Current PWM: 1500
   # Commands:
   #   1-5: select joint
   #   +/-: increase/decrease PWM
   #   [/]: step size (1/10/50)
   #   s: save snapshot
   #   q: quit
   ```

3. 启动 ROS2 模式（推荐，便于和 arm_controller 协作）：
   ```bash
   # 先启动 arm_controller
   ros2 launch car1_arm_controller arm_controller.launch.py
   
   # 新终端启动 test_servo_direct
   python3 test_servo_direct.py
   ```

4. 调试单个关节（以 joint2 大臂为例）：
   - 按 `2` 选中 joint2
   - 按 `+` 几次（每次 PWM+10），观察大臂上抬
   - 按 `]` 切换步长到 50，加快调节
   - 找到"大臂水平"的 PWM（例如 1522）
   - 按 `s` 保存快照（输入名称 "home"）

5. 调试所有关节：
   - 依次调试 joint1~joint5，每个都找到合适的 home 位置
   - 所有 home 位置的 PWM 应该接近 1500（已校准）或带有已知 offset

6. 观察响应延迟：
   - 按一次 `+`，看机械臂多久开始运动
   - 预期：< 50ms（直连串口）或 < 100ms（ROS2 模式）

**易错点**：
- ⚠️ **按键无响应** → **解决**：检查终端是否获得焦点（点击终端窗口后按键）
- ⚠️ **直连串口模式与 arm_controller 冲突** → **解决**：关闭 arm_controller 再用 --direct 模式，或单独使用
- ⚠️ **舵机响应与按键不同步** → **解决**：降低按键速度，等待舵机完成当前动作

---

#### 步骤4：命名快照保存与位姿复用（阶段二：能理解，30min）

> ⚠️ 本步骤对应 src 目录源码：`test_servo_direct.py` 中 `snapshot_manager.py`

**知识点讲解**：

**命名快照（3.2.3）**
- **原理**：调试过程中经常需要在多个关键位姿间快速切换（如 home、work、pick、place）。命名快照机制允许用户：(1) 将当前 5 关节 PWM 加上名称保存为 YAML 格式；(2) 通过名称调用快速回放。快照文件 `named_snapshots.yaml` 与动作文件分开保存，前者是"原子位姿"，后者是"位姿序列"。
- **源码对应**：`arm/car1_arm_controller/config/named_snapshots.yaml`

**位姿 vs 动作的区分**
- **原理**：**位姿（snapshot）** 是某一时刻 5 关节的 PWM 状态，是一个"点"；**动作（action）** 是一系列位姿按时间顺序排列，是一条"轨迹"。例如 "home" 是位姿，"home→pick→place→home" 是动作。两者都使用 YAML 格式存储但结构不同。
- **源码对应**：`named_snapshots.yaml`（位姿） vs `actions/home.yaml`（动作）

**操作步骤**：

1. 在 test_servo_direct 中保存 home 快照：
   - 调整机械臂到 home 位姿（5 关节都在中位）
   - 按 `s`，输入名称 "home"
   - 预期：`Snapshot 'home' saved: [1500, 1500, 1500, 1500, 1500]`

2. 保存 work 快照：
   - 调整到 work 位姿（大臂水平、小臂伸出）
   - 保存为 "work"

3. 保存 pick 快照：
   - 调整到 pick 位姿（夹爪朝下、距目标 5cm）
   - 保存为 "pick"

4. 保存 place 快照：
   - 调整到 place 位姿（夹爪在放置点上方）
   - 保存为 "place"

5. 查看保存的快照：
   ```bash
   cat named_snapshots.yaml
   # 预期：
   # snapshots:
   #   home:
   #     pwms: [1500, 1500, 1500, 1500, 1500]
   #   work:
   #     pwms: [1500, 1500, 1800, 1500, 1500]
   #   pick:
   #     pwms: [2000, 1700, 1500, 1500, 1500]
   #   place:
   #     pwms: [1500, 1700, 1500, 1500, 1500]
   ```

6. 通过快照快速回放：
   ```bash
   # 在 test_servo_direct 中按 'l' 加载快照
   # 输入 "home"，立即跳转
   ```

**易错点**：
- ⚠️ **快照名称重复** → **解决**：脚本会询问是否覆盖，输入 y 覆盖或 n 取消
- ⚠️ **加载快照后机械臂不响应** → **解决**：检查 ROS2 模式 arm_controller 是否运行

---

#### 步骤5：YAML 动作文件生成（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`arm/car1_arm_controller/config/actions/pick.yaml`、`place.yaml`、`home.yaml`

**知识点讲解**：

**YAML 动作文件结构（3.3.1）**
- **原理**：car1 的动作文件采用 YAML 列表结构，每一项（一个 action）包含三个字段：(1) `joints`：5 关节目标 PWM 列表；(2) `gripper`：夹爪目标（"open" / "close" / "stop"）；(3) `duration_ms`：从当前位姿到此位姿的运动时间（毫秒）。多个 action 顺序排列形成完整动作序列。
- **源码对应**：`arm/car1_arm_controller/config/actions/pick_place.yaml`（完整抓取放置动作）

**动作 vs 轨迹**
- **原理**：car1 的"动作"是离散的位姿序列（每个 action 之间通过梯形插值过渡），与 MoveIt2 的"轨迹"（连续关节空间曲线）不同。动作文件的优势是：(1) 简单直观；(2) 易于手工编辑；(3) 不需要规划器。劣势是：(1) 路径不最优；(2) 不做碰撞检测。
- **源码对应**：action_player.py 中 `parse_yaml()` 函数

**操作步骤**：

1. 查看示例动作文件：
   ```bash
   cat ~/ros2_ws/src/xflz_eai_car1/arm/car1_arm_controller/config/actions/pick_place.yaml
   # 预期：
   # - name: "go_pick"
   #   joints: [2000, 1700, 1500, 1500, 1500]
   #   gripper: "open"
   #   duration_ms: 2000
   # - name: "descend"
   #   joints: [2000, 1900, 1300, 1500, 1500]
   #   gripper: "open"
   #   duration_ms: 1500
   # - name: "grasp"
   #   joints: [2000, 1900, 1300, 1500, 1500]
   #   gripper: "close"
   #   duration_ms: 1000
   # - name: "lift"
   #   joints: [2000, 1700, 1500, 1500, 1500]
   #   gripper: "close"
   #   duration_ms: 1500
   # - name: "go_place"
   #   joints: [1500, 1700, 1500, 1500, 1500]
   #   gripper: "close"
   #   duration_ms: 2000
   # - name: "release"
   #   joints: [1500, 1700, 1500, 1500, 1500]
   #   gripper: "open"
   #   duration_ms: 1000
   # - name: "go_home"
   #   joints: [1500, 1500, 1500, 1500, 1500]
   #   gripper: "open"
   #   duration_ms: 2000
   ```

2. 创建自定义动作文件（实验报告必填）：
   ```bash
   cat > /tmp/my_pick_place.yaml << 'EOF'
   # 自定义抓取放置动作（4 个步骤）
   - name: "approach"
     joints: [2000, 1700, 1500, 1500, 1500]
     gripper: "open"
     duration_ms: 2000
   
   - name: "grasp"
     joints: [2000, 1900, 1300, 1500, 1500]
     gripper: "close"
     duration_ms: 1500
   
   - name: "lift"
     joints: [2000, 1700, 1500, 1500, 1500]
     gripper: "close"
     duration_ms: 1500
   
   - name: "home"
     joints: [1500, 1500, 1500, 1500, 1500]
     gripper: "open"
     duration_ms: 2000
   EOF
   ```

3. 验证 YAML 语法：
   ```bash
   python3 -c "import yaml; d = yaml.safe_load(open('/tmp/my_pick_place.yaml')); print(f'OK, {len(d)} actions')"
   # 预期：OK, 4 actions
   ```

4. 动作设计原则：
   - 起点 home：所有关节 1500
   - 接近目标：移动到目标上方 5-10cm
   - 下压：仅降低 joint2/joint3，避免横向移动
   - 抓取：夹爪 close
   - 抬升：回升到接近高度
   - 移动到放置点：旋转 joint1（底座）
   - 下放到放置高度
   - 释放：夹爪 open
   - 归位：回 home

**易错点**：
- ⚠️ **YAML 缩进错误** → **解决**：使用空格（不用 tab），统一缩进 2 空格
- ⚠️ **duration_ms 设为 0** → **解决**：至少 500ms，否则舵机来不及响应
- ⚠️ **joints 数组长度不是 5** → **解决**：严格保持 5 个元素

---

#### 步骤6：action_player 普通回放（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`arm/car1_arm_controller/launch/action_player.launch.py`

**知识点讲解**：

**action_player 回放器（3.3.2）**
- **原理**：`action_player.launch.py` 启动一个节点，订阅 YAML 动作文件并按顺序执行。每次执行包含三个阶段：(1) 发送 joint_command（5 关节目标 PWM）；(2) 等待 `duration_ms` 毫秒；(3) 发送 gripper 指令。完成后自动加载下一动作。支持三种模式：`normal`（普通）、`step`（单步）、`loop`（循环）。
- **源码对应**：`arm/car1_arm_controller/action_player.py` 中 `play()` 函数

**action_player 与 arm_controller 的协作**
- **原理**：action_player 不直接控制舵机，而是通过 `joint_command` 话题向 arm_controller 发送目标。arm_controller 收到后做软限位检查并通过串口执行。这种"动作播放器 + 控制器"分离的设计使得：(1) 动作可被多个上层应用复用；(2) 控制器独立升级不影响动作文件。
- **源码对应**：`action_player.py` 中 `self.joint_pub = create_publisher(JointCommand, '/arm/joint_command', 10)`

**操作步骤**：

1. 启动 arm_controller（必须）：
   ```bash
   ros2 launch car1_arm_controller arm_controller.launch.py
   ```

2. 启动 action_player 普通回放：
   ```bash
   ros2 launch car1_arm_controller action_player.launch.py \
     yaml_file:=/tmp/my_pick_place.yaml \
     mode:=normal
   # 预期：机械臂按 4 个动作顺序执行，约 7 秒完成整个抓放循环
   ```

3. 监控执行进度：
   ```bash
   ros2 topic echo /action_player/progress
   # 字段：current_index, total_count, current_action_name, status
   ```

4. 回放预定义动作：
   ```bash
   ros2 launch car1_arm_controller action_player.launch.py \
     yaml_file:=$(ros2 pkg prefix car1_arm_controller)/share/car1_arm_controller/config/actions/pick_place.yaml \
     mode:=normal
   ```

5. 回放结束后自动停止：
   - 普通模式下执行完所有动作后 action_player 自动退出
   - 终端打印 "All actions completed, exiting"

**易错点**：
- ⚠️ **回放时机械臂动作与预期不符** → **解决**：检查 YAML 中 joints/gripper 字段，确认与期望动作一致
- ⚠️ **回放过程中关节不动** → **解决**：检查 arm_controller 是否运行，`/arm/joint_command` 话题是否被订阅
- ⚠️ **YAML 文件找不到** → **解决**：使用绝对路径或 `$(ros2 pkg prefix xxx)/share/...` 形式

---

#### 步骤7：单步 / 循环 / 急停模式（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`action_player.py` 中 mode 参数处理

**知识点讲解**：

**单步模式（3.3.3）**
- **原理**：单步（step）模式下，每执行一个 action 后暂停并等待用户在终端按 Enter 才继续。这种"人工确认"模式适合：(1) 初次调试新动作时逐步观察；(2) 抓取失败时人工干预；(3) 教学演示时讲解每一步。实现方式是 action_player 阻塞在 `input()` 调用上。
- **源码对应**：`action_player.py` 中 `if self.mode == 'step': input('Press Enter for next action...')`

**循环模式**
- **原理**：循环（loop）模式下，整个动作序列按 `loop_count` 次重复执行，间隔 `loop_interval_sec` 秒。这种模式适合：(1) 重复抓取演示；(2) 老化测试；(3) 教学反复演示。循环计数为 0 表示无限循环，需用 Ctrl+C 退出。
- **源码对应**：`action_player.py` 中 `for i in range(loop_count)` 循环

**紧急停止**
- **原理**：紧急停止通过监听 SIGINT（Ctrl+C）实现。action_player 在收到信号时立即停止向 arm_controller 发布新指令，但允许"当前 action"完成。急停后舵机保持在最后位置（不会自动回 home）。这种"软急停"设计避免突然断电导致的机械冲击。
- **源码对应**：`action_player.py` 中 `signal_handler()` 函数

**操作步骤**：

1. 单步模式：
   ```bash
   ros2 launch car1_arm_controller action_player.launch.py \
     yaml_file:=/tmp/my_pick_place.yaml \
     mode:=step
   # 预期：执行 1 个 action 后打印 "Press Enter for next action..."，等待输入
   # 反复按 Enter 逐步完成
   ```

2. 循环模式（3 次循环）：
   ```bash
   ros2 launch car1_arm_controller action_player.launch.py \
     yaml_file:=/tmp/my_pick_place.yaml \
     mode:=loop \
     loop_count:=3 \
     loop_interval_sec:=2.0
   # 预期：动作执行 3 次后停止，总耗时 ≈ 3 × (7+2) = 27 秒
   ```

3. 无限循环（演示用）：
   ```bash
   ros2 launch car1_arm_controller action_player.launch.py \
     yaml_file:=/tmp/my_pick_place.yaml \
     mode:=loop \
     loop_count:=0
   # 预期：无限循环，按 Ctrl+C 停止
   ```

4. 紧急停止测试：
   - 启动循环模式（loop_count=5）
   - 在机械臂运动过程中按 Ctrl+C
   - 预期：机械臂停在当前位置，终端打印 "Emergency stop triggered"

5. 急停后恢复：
   ```bash
   ros2 service call /arm/go_home car1_arm_msgs/srv/GoHome
   # 手动复位
   ```

6. 性能基线（实验报告必填）：

   | 指标 | 期望值 | 实测值 |
   |------|-------|-------|
   | 校准 GUI 启动时间 | < 5s |  |
   | 单关节步进响应延迟 | < 50ms |  |
   | 单个 action 执行误差 | < 5 PWM |  |
   | 单步模式间隔 | 人工确认 |  |
   | 循环模式间隔精度 | ±0.1s |  |
   | 急停响应时间 | < 100ms |  |

**易错点**：
- ⚠️ **单步模式按 Enter 无响应** → **解决**：检查 action_player 终端是否在前台（SSH 时需注意会话）
- ⚠️ **循环模式停不下来** → **解决**：Ctrl+C 不响应时使用 `kill -9 $(pgrep -f action_player)`
- ⚠️ **急停后机械臂缓慢下垂** → **解决**：急停后舵机无主动维持，5V 电源断开后机械臂会因重力下垂

---

#### 完整可运行代码 demo_calibration_and_recording.py

> 独立 demo 脚本：完整的校准 + 录制 + 回放流程（依赖 arm_controller 运行）

```python
# -*- coding: utf-8 -*-
"""
实验3 demo：零位校准与动作录制回放一体化
平台：B2 / C1
前置：ros2 launch car1_arm_controller arm_controller.launch.py 已运行
运行：python3 demo_calibration_and_recording.py
"""
import rclpy
from rclpy.node import Node
from car1_arm_msgs.msg import JointCommand
from car1_arm_msgs.srv import SetGripper
import time
import yaml


class CalibratorAndRecorder(Node):
    """零位校准 + 抓取动作录制"""
    
    def __init__(self):
        super().__init__('calibrator_and_recorder')
        self.pub = self.create_publisher(JointCommand, '/arm/joint_command', 50)
        self.gripper_cli = self.create_client(SetGripper, '/arm/set_gripper')
        while not self.gripper_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /arm/set_gripper...')
    
    def move_to_pwm(self, pwms, duration_sec=2.0):
        """梯形插值运动到目标 PWM"""
        start_pwms = [1500] * 5  # 假设从 home 出发
        steps = max(1, int(duration_sec / 0.02))
        for i in range(steps + 1):
            alpha = i / steps
            cur = [int(start_pwms[j] + (pwms[j] - start_pwms[j]) * alpha) for j in range(5)]
            msg = JointCommand()
            msg.ids = [1, 2, 3, 4, 5]
            msg.pwms = cur
            self.pub.publish(msg)
            time.sleep(0.02)
    
    def set_gripper(self, command):
        """0=open, 1=close, 2=stop"""
        req = SetGripper.Request()
        req.command = command
        future = self.gripper_cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()
    
    def record_pick_place(self, output_file):
        """录制抓取放置动作"""
        actions = []
        
        # 步骤 1：home
        self.move_to_pwm([1500, 1500, 1500, 1500, 1500], 2.0)
        actions.append({'name': 'home', 'joints': [1500, 1500, 1500, 1500, 1500],
                        'gripper': 'open', 'duration_ms': 500})
        
        # 步骤 2：接近 pick 点
        self.get_logger().info('Adjust to pick position, then press Enter...')
        input('Press Enter to record pick approach...')
        actions.append({'name': 'pick_approach', 'joints': [2000, 1700, 1500, 1500, 1500],
                        'gripper': 'open', 'duration_ms': 2000})
        
        # 步骤 3：下压
        self.get_logger().info('Lower to grasp height, then press Enter...')
        input('Press Enter to record descend...')
        actions.append({'name': 'descend', 'joints': [2000, 1900, 1300, 1500, 1500],
                        'gripper': 'open', 'duration_ms': 1500})
        
        # 步骤 4：抓取
        self.set_gripper(1)  # close
        actions.append({'name': 'grasp', 'joints': [2000, 1900, 1300, 1500, 1500],
                        'gripper': 'close', 'duration_ms': 1000})
        
        # 步骤 5：抬升
        actions.append({'name': 'lift', 'joints': [2000, 1700, 1500, 1500, 1500],
                        'gripper': 'close', 'duration_ms': 1500})
        
        # 步骤 6：移动到 place
        actions.append({'name': 'go_place', 'joints': [1500, 1700, 1500, 1500, 1500],
                        'gripper': 'close', 'duration_ms': 2000})
        
        # 步骤 7：释放
        self.set_gripper(0)  # open
        actions.append({'name': 'release', 'joints': [1500, 1700, 1500, 1500, 1500],
                        'gripper': 'open', 'duration_ms': 1000})
        
        # 步骤 8：回 home
        actions.append({'name': 'home', 'joints': [1500, 1500, 1500, 1500, 1500],
                        'gripper': 'open', 'duration_ms': 2000})
        
        # 写入 YAML
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(actions, f, default_flow_style=False, allow_unicode=True)
        self.get_logger().info(f'Saved {len(actions)} actions to {output_file}')


def main():
    rclpy.init()
    node = CalibratorAndRecorder()
    
    print('=== 零位校准与动作录制 Demo ===')
    print('1. 运行校准（请确保机械臂已在中位）')
    print('2. 录制抓取放置动作')
    
    choice = input('请选择 (1=校准 2=录制 3=退出): ')
    
    if choice == '1':
        print('请使用 servo_calib.launch.py 进行图形化校准')
    elif choice == '2':
        node.record_pick_place('/tmp/demo_pick_place.yaml')
    else:
        print('Bye')
    
    rclpy.shutdown()


if __name__ == "__main__":
    main()
```

### 1.7 实验总结

**完成成果**：
- 理解舵机零位校准原理与软件 offset 方案
- 使用 servo_calib 校准 GUI 完成至少 2 个关节的零位校准
- 使用 test_servo_direct.py 完成抓取放置动作的交互式录制
- 掌握 YAML 动作文件结构并编写了自定义动作
- 通过 action_player 在 normal/step/loop 模式下验证动作

**技能收获**：
- 掌握舵机校准的工程方法（视觉判断 + 水平仪辅助）
- 理解软件 offset 相比 EEPROM 写入的优势
- 熟悉 YAML 动作文件的设计原则（离散位姿序列）
- 掌握 action_player 多种回放模式与急停机制

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 校准后机械臂仍不齐 | 渐进式校准未完成 | 多轮迭代粗调+精调 |
| 录制时按键无响应 | 终端未获焦点 | 点击终端窗口后按键 |
| 回放时机械臂动作跳跃 | duration_ms 过小 | 至少 500ms/步 |
| 急停不响应 | 进程僵死 | `kill -9 $(pgrep -f action_player)` |
| YAML 解析失败 | 缩进错误 | 使用 2 空格缩进，不用 tab |

### 1.8 思考题

1. 软件 offset 方案相比直接写入舵机 EEPROM 有什么优缺点？在什么场景下必须使用 EEPROM 写入？
2. 命名快照（snapshot）与动作文件（action）的本质区别是什么？能否将两者合并为同一数据结构？
3. 单步模式适合哪些调试场景？为什么自动化测试通常不采用单步模式？
4. 急停后机械臂缓慢下垂的物理原因是什么？工业机械臂如何避免这个问题？
5. 如果录制的动作在第 3 次回放时失败，可能的原因有哪些？如何设计"自愈"机制？

### 1.9 实验报告要求

**评分标准**：校准原理与操作 20 分 + test_servo_direct 交互调试 20 分 + YAML 动作文件设计 25 分 + action_player 三种模式验证 20 分 + 实验报告 15 分 = 100 分。

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初版生成（基于 _registry.yaml human_waiver 模式，标注 [待源码核实]） |
