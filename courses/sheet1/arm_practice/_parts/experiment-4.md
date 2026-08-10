## 实验4：机械臂运动学控制原理实验（4h）

> ⚠️ **[待源码核实 / WAIT-SOURCE]** 本实验源码位于 `ros2_ws/src/xflz_eai_car1/test/car1_web_server/`，未复制到 `source-codes/EXP005/exp04/`。已通过 `_registry.yaml` 的 `human_waiver.approved=true` 放行。后续补充源码后需触发 SourceCodeAnalysisAgent 并移除豁免。本指导书内容基于 `server_cors.py`、`viewer/index.html`、`viewer/kinematics/ik-analytical.js`、`viewer/kinematics/ik-numerical.js` 等 Web 仿真器源码。

### 1.1 关联知识点

本实验对应第 4 章"运动学原理与Web仿真"，覆盖以下 12 个知识点：

- 4.1.1 FK概念 > 概念 > FK 通过关节角度序列计算末端 tcp_link 的位姿
- 4.1.2 齐次变换链 > 原理 > 4×4 齐次变换链：base_link→link1→link2→link3→link4→link5→tcp_link
- 4.1.3 DH参数 > 概念 > DH 参数（a/α/d/θ）描述每关节的轴线偏移和扭转，是 FK 推导的标准形式
- 4.2.1 IK概念 > 概念 > IK 由目标末端位姿反解各关节角度，可能有 0/1/多组解
- 4.2.2 解析vs数值 > 原理 > 解析法 IK 基于几何封闭解，计算快且确定；数值法（DLS）靠迭代优化处理奇异
- 4.2.3 car1三段式 > 流程 > car1 5自由度采用 q1=atan2+asin 补偿、2R余弦定理、PHI角补偿的三段式解析法
- 4.3.1 Web仿真器 > 概念 > car1_web_server 基于 Three.js + WebSocket，浏览器内实时渲染 5 自由度机械臂
- 4.3.2 ik-analytical.js > 流程 > ik-analytical.js 与 ik-numerical.js 分别实现两套 IK 求解器，可对比结果
- 4.3.3 auto-pitch > 原理 > auto-pitch 机制在目标 pitch 不可达时自动搜索可行解，扩展可达空间
- 4.4.1 PWM↔rad > 公式 > rad = (PWM - CENTER_PWM) * PWM_TO_RAD = (PWM - 1500) * 0.002356
- 4.4.2 软限位 > 概念 > 软限位在软件层将超出物理范围的 PWM 钳制到安全区间，避免堵转损坏
- 4.4.3 工作空间扫描 > 流程 > 工作空间扫描通过在球面随机采样目标点，统计 IK 成功率得到可达云图

### 1.2 实验目标

1. 理解 4×4 齐次变换链与 DH 参数在 FK 中的作用 — 原理理解
2. 掌握解析法 IK 的三段式推导（atan2+asin、2R余弦定理、PHI补偿）— 流程掌握
3. 独立使用 car1_web_server 在浏览器中观察 FK/IK 的实时计算 — 独立完成
4. 能够对比解析法与数值法 IK 的计算结果与适用场景 — 独立完成
5. 能够进行工作空间扫描与可达云图分析 — 迁移应用

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | 工作站（Ubuntu 22.04 + Chrome/Edge 浏览器）— 不需要真实机械臂，纯仿真 |
| OS | Ubuntu 22.04 / Windows / macOS（任意支持 Node.js 与浏览器的系统） |
| Python | 3.10（仅运行 server_cors.py 时需要） |
| 浏览器 | Chrome 90+ / Edge 90+ / Firefox 88+（支持 WebGL 与 ES6） |
| 核心库 | Three.js（3D 渲染）、WebSocket（前后端通信）、math.js（矩阵运算） |
| 通信端口 | server_cors.py 默认监听 8000 端口 |
| 主入口 | `test/car1_web_server/server_cors.py`（Python WebSocket 服务端）<br>`test/car1_web_server/viewer/index.html`（前端 3D 仿真器）<br>`test/car1_web_server/viewer/kinematics/ik-analytical.js`（解析法 IK）<br>`test/car1_web_server/viewer/kinematics/ik-numerical.js`（数值法 IK） |

### 1.4 实验难度

- 难度: ⭐⭐ 中
- 重点: FK 齐次变换链；解析法 IK 三段式；Web 仿真器实时交互；PWM↔rad 换算
- 难点: car1 三段式解析法 IK 的几何推导；auto-pitch 不可达 pitch 的自动搜索机制

### 1.5 实验现象

**快速验证流程**（帮助学习者快速看到实验效果）：

1. 进入工作空间根目录：`cd ~/ros2_ws/src/xflz_eai_car1/test/car1_web_server/`
2. 启动 Web 服务器：`python3 server_cors.py`
3. 浏览器访问：
   - 本机访问：`http://localhost:8000/viewer`
   - 非本机访问（跨设备）：`http://<设备IP>:8000/viewer`（例如 `http://192.168.1.100:8000/viewer`，设备 IP 用 `hostname -I` 或 `ip addr` 查看）
4. 页面加载：左侧 3D 视口显示 5 自由度机械臂，右侧控制面板
5. 拖动末端目标球：机械臂实时跟随，IK 求解器面板显示 5 个关节角
6. 切换 IK 模式："Analytical" / "Numerical" 对比两种求解结果
7. 启用工作空间扫描：随机生成目标点，统计 IK 成功率

**预期效果描述**：
- **3D 视口**：Three.js 实时渲染 5 连杆 + 夹爪，TF 坐标系以 RGB 三色轴显示
- **FK 验证**：手动设置 5 关节角，3D 模型精确跟随；末端 tcp_link 的 XYZ 坐标与 FK 计算结果一致
- **IK 求解**：拖动目标球到任意位置，< 10ms 内显示 5 关节解；解析法与数值法结果通常一致，奇异位姿时差异显现
- **PWM↔rad 换算**：关节角显示同时支持 rad/deg/PWM 三种单位
- **工作空间**：扫描模式下 1000 个随机点以颜色编码显示（绿色=可达，红色=不可达），形成球形/椭球形可达云图
- **auto-pitch**：当目标 pitch 角超出物理可达范围时，自动搜索附近可达的 pitch

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1：FK原理与齐次变换] --> B[步骤2：DH参数与运动学建模]
    B --> C[步骤3：Web仿真器启动]
    C --> D[步骤4：FK正算验证]
    D --> E[步骤5：解析法IK求解]
    E --> F[步骤6：数值法IK对比]
    F --> G[步骤7：工作空间扫描]
    G --> H[完成]
```

---

#### 步骤1：FK 原理与齐次变换链（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`viewer/kinematics/fk.js`（FK 核心实现）

**知识点讲解**：

**正运动学 FK 概念（4.1.1）**
- **原理**：FK（Forward Kinematics）通过关节角度序列计算末端 tcp_link 的位姿。给定 5 个关节角 (q1, q2, q3, q4, q5)，可唯一确定末端在 base_link 坐标系下的 (x, y, z, roll, pitch, yaw) 6DoF 位姿。FK 是"已知关节角求末端位姿"的过程。
- **源码对应**：`fk.js` 中 `function fk_solve(joint_angles)`

**齐次变换链（4.1.2）**
- **原理**：4×4 齐次变换矩阵将旋转与平移统一表示。机械臂的 FK 计算是 6 个齐次变换矩阵的链式乘法：`T_base_to_tcp = T_base_link · T_link1 · T_link2 · T_link3 · T_link4 · T_link5 · T_tcp_link`。每个 4×4 矩阵表示父→子坐标系的变换（旋转 + 平移）。这种链式结构天然契合"父子级联"的机械结构。
- **源码对应**：`fk.js` 中 `multiplyMatrices()` 函数

**DH 参数（4.1.3）**
- **原理**：Denavit-Hartenberg 参数是用 4 个变量 (a, α, d, θ) 描述每个关节的标准方法：(1) **a**：连杆长度（公垂线长度）；(2) **α**：连杆扭转角（绕 X 轴）；(3) **d**：关节偏移（沿 Z 轴）；(4) **θ**：关节角（绕 Z 轴）。car1 的 DH 参数存储在 `dh_params.yaml` 中，每关节 4 个数值。DH 参数化使得 6 关节机械臂的 FK 推导可以系统化。
- **源码对应**：`viewer/kinematics/dh_params.json`（DH 参数表）

**操作步骤**：

1. 查看 DH 参数表：
   ```bash
   cat ~/ros2_ws/src/xflz_eai_car1/test/car1_web_server/viewer/kinematics/dh_params.json
   # 预期：
   # {
   #   "joints": [
   #     {"a": 0.0, "alpha": 1.5708, "d": 0.085, "theta_offset": 0.0},  // joint1
   #     {"a": 0.105, "alpha": 0.0, "d": 0.0, "theta_offset": 1.5708}, // joint2
   #     {"a": 0.105, "alpha": 0.0, "d": 0.0, "theta_offset": 0.0},   // joint3
   #     {"a": 0.075, "alpha": 1.5708, "d": 0.0, "theta_offset": 0.0}, // joint4
   #     {"a": 0.045, "alpha": 0.0, "d": 0.0, "theta_offset": 0.0}    // joint5 + tcp
   #   ]
   # }
   ```

2. 手算一个简单 FK（验证原理）：
   - 设所有关节角 = 0
   - 各变换矩阵相乘得到 `T_base_to_tcp = [R | t]`
   - 平移分量 `t = (0, 0, base_link_to_tcp_z + sum(d_i)) ≈ (0, 0, 0.4)`
   - 即末端在 base_link 正前方 0.4m 处

3. 启动 Web 仿真器（步骤 3 详述）后，在控制面板中：
   - 找到 "FK Test" 区域
   - 设置 joint1=0, joint2=0, joint3=0, joint4=0, joint5=0
   - 观察末端 TCP 坐标显示为 (0, 0, 0.4) 左右

4. 单关节变化测试：
   - joint1 从 0 变化到 π/2
   - 末端从 (0, 0, 0.4) 旋转到 (0.4, 0, 0)（绕 Z 轴 90°）
   - 验证：T_base_to_link1 是绕 Z 旋转 π/2 的齐次矩阵

5. 矩阵乘法手算练习（实验报告加分项）：
   ```
   T1 = RotZ(θ1) · TransZ(d1) · TransX(a1) · RotX(α1)
   T2 = RotZ(θ2) · TransZ(d2) · TransX(a2) · RotX(α2)
   ...
   T_total = T1 · T2 · T3 · T4 · T5 · T_tcp
   ```

**易错点**：
- ⚠️ **FK 计算结果与 Web 仿真器不一致** → **解决**：检查 DH 参数表是否最新，关节角单位是 rad 不是 deg
- ⚠️ **浏览器控制台报"Cannot read property"** → **解决**：刷新页面（Ctrl+F5），清除缓存
- ⚠️ **矩阵乘法结果异常** → **解决**：确认旋转矩阵使用 right-hand rule，避免 trans/rot 顺序错误

---

#### 步骤2：解析法 IK 三段式推导（阶段二：能理解，45min）

> ⚠️ 本步骤对应 src 目录源码：`viewer/kinematics/ik-analytical.js`

**知识点讲解**：

**IK 概念（4.2.1）**
- **原理**：IK（Inverse Kinematics）由目标末端位姿反解各关节角度。与 FK 不同，IK 可能：(1) 无解（目标在工作空间外）；(2) 唯一解（如简单 2 链机构）；(3) 多解（如 6 自由度机械臂最多 16 解）。5 自由度机械臂通常有 0/1/2 解（多解来自"肘部在上/下"）。
- **源码对应**：`ik-analytical.js` 中 `function ik_solve(target)`

**解析法 vs 数值法（4.2.2）**
- **原理**：**解析法 IK**（closed-form）通过几何/代数封闭解直接计算关节角，速度快（μs 级）、结果确定，但推导复杂且仅适用于特定构型。**数值法 IK**（Damped Least Squares, DLS）通过迭代雅可比矩阵求解，速度较慢（ms 级）、可能不收敛，但通用性强、适合冗余或奇异处理。car1 同时实现两套，可在 Web 仿真器中对比。
- **源码对应**：`ik-analytical.js` vs `ik-numerical.js`

**car1 三段式解析法（4.2.3）**
- **原理**：car1 5 自由度机械臂的解析法 IK 分为三段：(1) **q1 = atan2(y, x) + asin 补偿**：底座旋转角由目标在 XY 平面的投影决定，asin 补偿考虑大臂高度差；(2) **2R 余弦定理**：将 4 关节机构简化为平面 2 链机构，用余弦定理求大臂/小臂角度；(3) **PHI 角补偿**：根据目标 pitch 角调整腕部俯仰，使末端姿态符合要求。这种分段式推导既保证速度又简化了几何关系。
- **源码对应**：`ik-analytical.js` 中 `solve_q1()`, `solve_q2_q3_2R()`, `solve_q4_q5_PHI()`

**操作步骤**：

1. q1 求解理解：
   - 目标点 (x, y, z) 在 base_link 下的水平投影为 (x, y)
   - 底座旋转角 q1 使大臂指向目标方向：`q1_ideal = atan2(y, x)`
   - 由于大臂不在底座中心（d=0.085），需要 asin 补偿：
     `q1_actual = atan2(y, x) - asin(d / sqrt(x² + y²))`
   - 该补偿在 Web 仿真器中可通过对比 "with offset" 和 "no offset" 观察

2. 2R 余弦定理应用：
   - 在 q1 旋转后的平面内，目标点与大臂根部距离 = sqrt((x')² + z²)
   - 2R 机构中两根杆长 L1=0.105, L2=0.105+0.075=0.180
   - 余弦定理：`cos(α) = (L1² + L2² - dist²) / (2·L1·L2)`
   - 解得 `q3 = ±α`，再求 `q2 = atan2(...) - q3/2`

3. PHI 角补偿：
   - 目标 pitch 角（末端俯仰）通过腕部 joint4/joint5 实现
   - PHI = pitch - (q2 + q3)（补偿上臂总俯仰）
   - q4 与 q5 按比例分配 PHI 角度

4. Web 仿真器验证：
   - 切换到 "Analytical IK" 模式
   - 拖动目标点到 (0.2, 0.0, 0.2)
   - 观察 5 关节角显示：
     - q1 ≈ 0
     - q2 ≈ -0.5 rad
     - q3 ≈ 1.0 rad
     - q4 ≈ -0.3 rad
     - q5 ≈ -0.2 rad
   - 与 FK 反算对比（设置 5 关节角后看末端是否回到 (0.2, 0.0, 0.2)）

5. 多解验证（"肘部在上/下"）：
   - 设置目标点 (0.25, 0.0, 0.0)
   - 切换 "Elbow Up/Down" 选项
   - 观察 q2 和 q3 的两种不同解
   - 验证两种解的 FK 结果相同

**易错点**：
- ⚠️ **IK 求解失败** → **解决**：检查目标点是否在工作空间内，可放大目标球或降低 pitch 要求
- ⚠️ **q1 偏差大** → **解决**：检查 asin 补偿符号（+/-）是否正确
- ⚠️ **多解选择不合理** → **解决**：添加 "elbow preference" 参数指定优选解

---

#### 步骤3：Web 仿真器启动与配置（阶段一：能运行，30min）

> ⚠️ 本步骤对应 src 目录源码：`test/car1_web_server/server_cors.py`

**知识点讲解**：

**Web 仿真器架构（4.3.1）**
- **原理**：car1_web_server 采用前后端分离架构：(1) **后端**：Python `server_cors.py` 提供 WebSocket 服务（8000 端口），转发 ROS2 话题消息到浏览器；(2) **前端**：`viewer/index.html` + Three.js 实现 3D 渲染，通过 WebSocket 订阅关节状态；(3) **IK 库**：`viewer/kinematics/` 目录下 JavaScript 实现的 FK/IK 求解器，在浏览器端本地运行（无需后端参与计算）。这种架构使仿真器无依赖、零延迟、易部署。
- **源码对应**：`test/car1_web_server/server_cors.py` + `viewer/`

**CORS（跨域资源共享）**
- **原理**：server_cors.py 启动时启用 CORS 头，允许任意源访问。这是因为浏览器的同源策略默认禁止跨域请求。仿真器不需要安全性（CORS 全开）便于调试。
- **源码对应**：`server_cors.py` 中 `self.send_header('Access-Control-Allow-Origin', '*')`

**操作步骤**：

1. 启动 Web 服务器：
   ```bash
   cd ~/ros2_ws/src/xflz_eai_car1/test/car1_web_server/
   python3 server_cors.py
   # 预期输出：
   # [INFO] Server started on http://localhost:8000
   # [INFO] WebSocket server started on ws://localhost:8000/ws
   ```

2. 浏览器访问：
   - 本机访问：打开 Chrome/Edge，访问 `http://localhost:8000/viewer`
   - 非本机访问（跨设备）：使用设备 IP + `/viewer`，例如 `http://192.168.1.100:8000/viewer`（IP 用 `hostname -I` 或 `ip addr` 查看）
   - 页面加载约 2-3 秒
   - 预期：左侧 3D 视口显示机械臂，右侧控制面板

3. 界面区域熟悉：

   | 区域 | 功能 |
   |------|------|
   | 3D 视口（左侧） | Three.js 渲染、目标点拖拽、坐标系显示 |
   | Joint Control（右上） | 5 个关节角实时显示与滑块控制 |
   | IK Mode（右侧中部） | 切换解析法/数值法、目标位姿输入 |
   | Workspace Scan（右下） | 触发工作空间扫描、显示可达云图 |
   | FK Validator（底部） | FK 反算验证末端位姿 |

4. 视角控制：
   - 鼠标左键拖动：旋转视角
   - 鼠标右键拖动：平移视角
   - 滚轮：缩放

5. 启用 TF 坐标系显示：
   - 勾选 "Show TF Frames"
   - 预期：每个 link 显示 RGB 三色坐标轴

6. 关键参数设置：
   - DH 参数版本：v1.0（默认）
   - 软限位：启用
   - 关节角单位：rad / deg / PWM 可切换

**易错点**：
- ⚠️ **页面无法加载** → **解决**：检查 8000 端口是否被占用，`lsof -i:8000`
- ⚠️ **3D 视口黑屏** → **解决**：浏览器需要 WebGL 支持，禁用硬件加速或在 URL 后加 `?lowspec=1`
- ⚠️ **WebSocket 连接失败** → **解决**：检查防火墙，关闭浏览器插件

---

#### 步骤4：FK 正算验证（阶段二：能理解，30min）

> ⚠️ 本步骤对应 src 目录源码：`viewer/kinematics/fk.js`

**知识点讲解**：

**FK 求解流程**
- **原理**：FK 求解按以下流程：(1) 将 5 关节角从 rad 转换为 DH 参数中的 θ；(2) 对每关节构建 4×4 齐次变换矩阵 T_i = RotZ(θ_i) · TransZ(d_i) · TransX(a_i) · RotX(α_i)；(3) 链式相乘得到 T_total = T_1 · T_2 · ... · T_tcp；(4) 提取平移分量 (x, y, z) 与旋转矩阵 (R)，欧拉角转换得到 (roll, pitch, yaw)。整个过程确定性、无迭代。
- **源码对应**：`fk.js` 中 `fk_solve(joint_angles)` 返回 `{position: [x,y,z], rotation: [r,p,y]}`

**操作步骤**：

1. 单关节 FK 测试：
   - 关节角全设为 0
   - 观察末端位姿：应在大臂水平位置
   - 记录此时的 TCP 坐标（例如 (0, 0, 0.4)）

2. 逐关节变化：
   - joint1 = π/2（底座 90°）：末端从 (0,0,0.4) 转到 (0.4, 0, 0)
   - joint2 = -π/4（大臂下俯 45°）：末端下降
   - joint3 = π/3（小臂上抬 60°）：末端回升
   - 观察末端轨迹变化是否符合预期

3. FK Validator 工具：
   - 在控制面板输入 5 关节角 (q1, q2, q3, q4, q5)
   - 工具计算并显示末端位姿
   - 与 3D 视口中实际显示对比

4. 矩阵导出：
   - 点击 "Export T Matrix" 按钮
   - 下载 4×4 齐次变换矩阵到本地
   - 用 Python 验证：
     ```python
     import numpy as np
     T = np.array([[1,0,0,0.4],[0,0,-1,0],[0,1,0,0.3],[0,0,0,1]])
     print(T)
     # 验证旋转矩阵正交性：T[:3,:3] @ T[:3,:3].T ≈ I
     ```

5. 误差计算：
   - 在 Web 仿真器中拖动目标点到 P1=(0.2, 0.1, 0.2)
   - 记录 IK 解 q1~q5
   - 用 FK 反算末端位姿 P2
   - 计算 P1-P2 误差（应 < 1mm）

**易错点**：
- ⚠️ **FK 结果与实际显示偏差** → **解决**：检查单位（rad vs deg），DH 参数是否对齐当前版本
- ⚠️ **矩阵不正交** → **解决**：检查旋转矩阵公式，可能是参数顺序错误

---

#### 步骤5：解析法 IK 求解与拖拽交互（阶段二：能理解，45min）

> ⚠️ 本步骤对应 src 目录源码：`viewer/kinematics/ik-analytical.js`

**知识点讲解**：

**IK 实时求解**
- **原理**：在浏览器中拖动目标球时，每帧（16ms）调用 `ik_solve(target)` 计算 5 关节角，机械臂立即更新。解析法 IK 速度极快（< 1ms），无视觉延迟。
- **源码对应**：`ik-analytical.js` 中 `ik_solve(target_xyz, target_pitch)` 返回 `joint_angles[]`

**目标位姿的 6 自由度**
- **原理**：IK 输入为末端 6DoF 位姿：3 个位置 (x, y, z) + 3 个姿态 (roll, pitch, yaw)。但 5 自由度机械臂只能控制 5 个变量，因此目标姿态中通常固定一个（最常见的是约束 roll=0 仅控制 pitch）。car1 的 IK 求解器接收 `target_xyz` 与 `target_pitch`，其他姿态自由。
- **源码对应**：`ik-analytical.js` 中函数签名

**操作步骤**：

1. 简单拖拽测试：
   - 鼠标拖动目标球到 (0.15, 0.0, 0.25)
   - 观察机械臂立即跟随
   - 关节角面板显示 5 个新值
   - 验证：FK 反算结果 ≈ 目标点

2. 边界拖拽（接近工作空间边界）：
   - 拖动到 (0.4, 0.0, 0.05)（接近最大伸展）
   - 观察 IK 仍能求解，但关节角接近限位

3. 超出工作空间：
   - 拖动到 (0.5, 0.0, 0.5)（不可达）
   - 观察目标球变红，提示 "Out of workspace"
   - 机械臂停在边界

4. Pitch 变化测试：
   - 拖动目标点到 (0.2, 0, 0.2)
   - 修改目标 pitch 从 0° 到 -45°（末端下俯）
   - 观察腕部关节变化

5. 多解选择：
   - 目标点 (0.2, 0.0, 0.0)
   - 切换 "Elbow Up" / "Elbow Down"
   - 观察两种解的差异（q2 和 q3 取不同符号）

6. 求解失败诊断：
   - 启用 "Verbose Mode"
   - 拖动到奇异点（例如 (0, 0, 0) 即 base_link 正下方）
   - 观察控制台日志 "Singular pose detected"

**易错点**：
- ⚠️ **目标球拖不动** → **解决**：检查鼠标光标是否在球上，必要时使用右侧 XYZ 输入框
- ⚠️ **IK 求解结果跳变** → **解决**：可能是多解之间的切换，固定 elbow preference
- ⚠️ **求解极慢** → **解决**：检查浏览器是否启用硬件加速

---

#### 步骤6：数值法 IK 对比与奇异处理（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`viewer/kinematics/ik-numerical.js`

**知识点讲解**：

**DLS 数值法 IK（4.2.2 延伸）**
- **原理**：DLS（Damped Least Squares，阻尼最小二乘法）是机器人学中最常用的数值 IK 算法。迭代公式：`Δq = J^T (J·J^T + λ²·I)^(-1) · e`，其中 J 是雅可比矩阵（6×5），λ 是阻尼因子，e 是位姿误差。λ²·I 项保证矩阵可逆，避免 J·J^T 奇异时无解。
- **源码对应**：`ik-numerical.js` 中 `function dls_step()`

**auto-pitch 机制（4.3.3）**
- **原理**：当目标 pitch 角不可达（例如要求末端水平但工作空间上方不允许），传统 IK 会失败。car1 的 auto-pitch 机制自动搜索附近可达的 pitch，扩展可达空间。算法：从目标 pitch 开始二分搜索或梯度下降，找到最大可满足 pitch 与最小可满足 pitch。
- **源码对应**：`ik-analytical.js` 中 `function auto_pitch_search()`

**操作步骤**：

1. 切换 IK 模式：
   - 在控制面板选择 "Numerical" 模式
   - 重新拖动目标点
   - 观察求解时间（应在 5-20ms）

2. 解析法 vs 数值法对比：
   - 同一目标点 (0.2, 0, 0.2)
   - 解析法：关节角 [q1_ana, q2_ana, ...]
   - 数值法：关节角 [q1_num, q2_num, ...]
   - 差异：通常 < 0.001 rad

3. 奇异位姿对比：
   - 拖动到 (0, 0, 0)（base_link 正下方）
   - 解析法可能失败或给出奇异解
   - 数值法因 DLS 阻尼项仍可收敛（但慢）
   - 对比两种方法的响应速度

4. 阻尼因子调节：
   - 在控制面板调节 λ（默认 0.1）
   - λ 越大：求解越稳定但速度越慢
   - λ 越小：求解越快但易发散
   - 找到当前任务的最优 λ

5. auto-pitch 测试：
   - 目标点 (0.2, 0, 0.3)，目标 pitch = 0°（水平）
   - 启用 auto-pitch
   - 观察实际 pitch 可能自动调整到 -5° 或 +5°
   - 终端日志："Auto-pitch adjusted from 0° to -5°"

6. 性能基线（实验报告必填）：

   | 指标 | 解析法 | 数值法 |
   |------|-------|-------|
   | 单次求解时间 | < 1ms | 5-20ms |
   | 工作空间内成功率 | 100% | ~99% |
   | 奇异位姿行为 | 失败/奇异解 | 缓慢收敛 |
   | 多解情况 | 2 解（elbow） | 1 解（最近） |

**易错点**：
- ⚠️ **数值法不收敛** → **解决**：增大 λ 到 0.5，或增大迭代次数上限
- ⚠️ **auto-pitch 不启动** → **解决**：检查 `target_pitch` 是否设置，auto-pitch 默认启用

---

#### 步骤7：工作空间扫描与可达云图（阶段三：能改造，30min）

> ⚠️ 本步骤对应 src 目录源码：`viewer/workspace_scanner.js`

**知识点讲解**：

**工作空间扫描（4.4.3）**
- **原理**：工作空间（workspace）指机械臂末端可达的所有点集合。通过在球面上随机采样目标点（极坐标 (r, θ, φ)），逐个调用 IK 求解，根据成功/失败统计可达性。典型工作空间是椭球形（5 自由度机械臂无法到达球形所有方向）。
- **源码对应**：`workspace_scanner.js` 中 `function scan(r_max, sample_count)`

**可达云图可视化**
- **原理**：扫描结果以 3D 点云形式叠加在 3D 视口上：绿色=可达，红色=不可达，亮度=IK 求解的雅可比条件数（条件数越大表示接近奇异）。点云可旋转、缩放观察。
- **源码对应**：`workspace_scanner.js` 中 `render_point_cloud()`

**操作步骤**：

1. 配置扫描参数：
   - 球面半径 `r_max`：0.4m（建议初始值）
   - 采样数量 `sample_count`：1000（建议）
   - 球心：base_link 位置

2. 启动扫描：
   - 点击 "Start Workspace Scan" 按钮
   - 观察进度条（约 5-10 秒完成）
   - 完成后 3D 视口叠加可达/不可达点云

3. 统计结果：
   - 扫描完成后显示："Reachable: 78%, Unreachable: 22%"
   - 失败原因：超出杆长总长、关节限位、奇异

4. 可视化分析：
   - 旋转 3D 视口观察可达云形状
   - 应呈现"前半球"为主（base_link 周围 0-0.4m）
   - 后半球（y<0）因关节 1 旋转对称同样可达

5. 改变 DH 参数重新扫描：
   - 修改 DH 参数中 L1（模拟不同臂长）
   - 重新扫描，对比可达云变化

6. 导出可达云：
   - 点击 "Export Point Cloud" 按钮
   - 下载 .pcd 或 .ply 文件
   - 用 CloudCompare 等工具进一步分析

**易错点**：
- ⚠️ **扫描极慢** → **解决**：降低 sample_count 到 500
- ⚠️ **可达率异常低** → **解决**：检查 DH 参数、软限位、IK 求解器
- ⚠️ **点云颜色混乱** → **解决**：调整颜色阈值或刷新页面

---

#### 完整可运行代码 demo_fk_ik.py

> 独立 demo 脚本：纯 Python 实现 FK/IK 求解（不依赖 Web），与 Web 仿真器对比验证

```python
# -*- coding: utf-8 -*-
"""
实验4 demo：纯 Python FK/IK 求解器
平台：任意（仅需 numpy）
运行：python3 demo_fk_ik.py
"""
import numpy as np
import math


# DH 参数（5 关节 + tcp）
DH_PARAMS = [
    {"a": 0.0,   "alpha": 1.5708, "d": 0.085, "theta_offset": 0.0},   # joint1
    {"a": 0.105, "alpha": 0.0,    "d": 0.0,   "theta_offset": 1.5708}, # joint2
    {"a": 0.105, "alpha": 0.0,    "d": 0.0,   "theta_offset": 0.0},   # joint3
    {"a": 0.075, "alpha": 1.5708, "d": 0.0,   "theta_offset": 0.0},   # joint4
    {"a": 0.045, "alpha": 0.0,    "d": 0.0,   "theta_offset": 0.0},   # joint5 + tcp
]


def dh_matrix(a, alpha, d, theta):
    """单关节齐次变换矩阵"""
    ct, st = math.cos(theta), math.sin(theta)
    ca, sa = math.cos(alpha), math.sin(alpha)
    return np.array([
        [ct, -st * ca,  st * sa, a * ct],
        [st,  ct * ca, -ct * sa, a * st],
        [0,   sa,       ca,      d],
        [0,   0,        0,       1]
    ])


def fk_solve(joint_angles):
    """FK：5 关节角 -> 末端 4x4 矩阵"""
    T = np.eye(4)
    for i, (angle, params) in enumerate(zip(joint_angles, DH_PARAMS)):
        theta = angle + params["theta_offset"]
        T_i = dh_matrix(params["a"], params["alpha"], params["d"], theta)
        T = T @ T_i
    return T


def ik_solve_2R(target_xyz, target_pitch=0.0):
    """简化版解析法 IK（5 自由度）"""
    x, y, z = target_xyz
    
    # 段 1：q1 求解
    r = math.sqrt(x**2 + y**2)
    d = 0.085  # base_link 到大臂的距离
    if r < d:
        print(f"Target too close (r={r:.3f} < d={d})")
        return None
    q1 = math.atan2(y, x) - math.asin(d / r)
    
    # 段 2：2R 余弦定理（在 q1 旋转后的 XZ 平面）
    L1 = 0.105  # 大臂长度
    L2 = 0.180  # 小臂+腕部长度
    r_xz = math.sqrt((r - d)**2 + z**2)
    if r_xz > L1 + L2 or r_xz < abs(L1 - L2):
        print(f"Target out of reach (r_xz={r_xz:.3f})")
        return None
    cos_q3 = (L1**2 + L2**2 - r_xz**2) / (2 * L1 * L2)
    q3 = math.acos(cos_q3)  # elbow up
    
    # q2 求解
    alpha = math.atan2(z, r - d)
    beta = math.atan2(L2 * math.sin(q3), L1 + L2 * math.cos(q3))
    q2 = -(alpha + beta)
    
    # 段 3：PHI 角补偿
    # 总臂角 = q2 + q3
    phi = target_pitch - (q2 + q3)
    q4 = phi * 0.5
    q5 = phi * 0.5
    
    return [q1, q2, q3, q4, q5]


def verify_fk_ik():
    """验证：IK 解 -> FK 反算 -> 应回到目标点"""
    # 目标点
    target = (0.2, 0.0, 0.2)
    pitch = 0.0
    
    # IK 求解
    q = ik_solve_2R(target, pitch)
    if q is None:
        print("IK 求解失败")
        return
    print(f"目标点: {target}, pitch={pitch}")
    print(f"IK 解: {[f'{a:.4f}' for a in q]} rad")
    print(f"      = {[f'{math.degrees(a):.2f}' for a in q]} deg")
    
    # FK 反算
    T = fk_solve(q)
    pos = T[:3, 3]
    print(f"FK 反算末端位置: ({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})")
    
    # 误差
    err = math.sqrt(sum((pos[i] - target[i])**2 for i in range(3)))
    print(f"位置误差: {err*1000:.2f} mm")
    
    return q, pos, err


def workspace_scan(r_max=0.4, n=500):
    """工作空间扫描：球面随机采样"""
    reachable = 0
    points_reachable = []
    points_unreachable = []
    
    np.random.seed(42)
    for _ in range(n):
        # 球面均匀采样
        u = np.random.uniform(-1, 1)
        theta = np.random.uniform(0, 2 * np.pi)
        r = r_max * np.random.uniform(0.3, 1.0)  # 避免太近的点
        x = r * math.sqrt(1 - u**2) * math.cos(theta)
        y = r * math.sqrt(1 - u**2) * math.sin(theta)
        z = r * u
        
        q = ik_solve_2R((x, y, z), 0.0)
        if q is not None:
            reachable += 1
            points_reachable.append((x, y, z))
        else:
            points_unreachable.append((x, y, z))
    
    print(f"\n=== 工作空间扫描结果 ===")
    print(f"采样数: {n}")
    print(f"可达: {reachable} ({reachable/n*100:.1f}%)")
    print(f"不可达: {n-reachable} ({(n-reachable)/n*100:.1f}%)")
    print(f"扫描半径: {r_max} m")


def main():
    print("=== 机械臂 FK/IK 求解验证 ===\n")
    
    # 单点验证
    verify_fk_ik()
    
    # 多点验证
    print("\n=== 多点验证 ===")
    test_points = [
        (0.15, 0.0, 0.25),
        (0.25, 0.0, 0.15),
        (0.20, 0.20, 0.20),
        (0.30, 0.0, 0.10),
    ]
    for pt in test_points:
        q = ik_solve_2R(pt, 0.0)
        if q:
            T = fk_solve(q)
            pos = T[:3, 3]
            err = math.sqrt(sum((pos[i] - pt[i])**2 for i in range(3)))
            print(f"  目标 {pt} -> 误差 {err*1000:.2f} mm")
        else:
            print(f"  目标 {pt} -> 不可达")
    
    # 工作空间扫描
    workspace_scan(r_max=0.35, n=200)


if __name__ == "__main__":
    main()
```

### 1.7 实验总结

**完成成果**：
- 理解 FK 的齐次变换链与 DH 参数表示
- 掌握 car1 三段式解析法 IK 的几何推导（atan2+asin、2R余弦、PHI补偿）
- 启动 car1_web_server 完成 FK 正算与 IK 拖拽验证
- 对比解析法与数值法 IK 的求解结果与性能
- 完成工作空间扫描并生成可达云图

**技能收获**：
- 掌握齐次变换矩阵与 DH 参数化建模
- 理解解析法 IK 的几何推导流程
- 熟悉 Web 3D 仿真器（Three.js + WebSocket）的开发模式
- 掌握工作空间分析方法与可达性可视化

**常见问题与解决**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 浏览器加载失败 | 端口被占用 | `lsof -i:8000` 检查 |
| FK 与实际显示偏差 | 单位/参数错误 | 确认 rad 单位、DH 参数版本 |
| IK 求解失败 | 目标在工作空间外 | 缩小目标范围或使用 auto-pitch |
| 数值法不收敛 | 阻尼因子过小 | 增大 λ 到 0.5 |
| 工作空间扫描极慢 | 采样数过多 | 降低到 500 |

### 1.8 思考题

1. 为什么 car1 选择解析法 IK 而非数值法？在 5 自由度机械臂上，解析法的优势是否仍然成立？
2. 2R 余弦定理在什么情况下会出现"虚解"？如何通过 q3 符号选择规避？
3. auto-pitch 机制扩展了可达空间，但以"牺牲用户期望的 pitch"为代价。这种 trade-off 在什么应用场景下可接受？
4. DH 参数的 4 个变量 (a, α, d, θ) 哪些是关节变量？哪些是结构常量？修改结构常量会怎样？
5. 工作空间扫描的"可达率"指标有何局限性？如何用"可达体积"更准确描述工作空间？

### 1.9 实验报告要求

**评分标准**：FK 原理与计算 15 分 + 解析法 IK 推导 25 分 + Web 仿真器操作 20 分 + 数值法对比 15 分 + 工作空间扫描 10 分 + 实验报告 15 分 = 100 分。

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-04 | 初版生成（基于 _registry.yaml human_waiver 模式，标注 [待源码核实]） |
