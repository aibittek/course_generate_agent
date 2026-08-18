---
course_code: EXP003
course_name: 机器人ROS2应用与开发
version: v0.2
last_updated: 2026-08-10
updated_by: LabGuideOrchestratorAgent (v2.0)
source_spec: courses/sheet1/ros_practice/_meta/course-spec.yaml
source_knowledge_graph: courses/sheet1/ros_practice/EXP003_knowledge_graph.md
source_syllabus: courses/sheet1/ros_practice/EXP003_syllabus.md
total_hours: 48
experiment_count: 8
hardware: 具身智能实验箱B2 / 具身智能机器人小车C1
tech_stack: [ROS2, DDS, TF2, URDF, Xacro, Gazebo, Rviz2, Launch]
---

# 机器人ROS2应用与开发 实验指导书

> 课程代码: EXP003
> 总学时: 48h（全部为实验学时）
> 实验数量: 8
> 适用平台: 具身智能实验箱B2（XFLZ_EAI_B2_PRO）/ 具身智能机器人小车C1（XFLZ_EAI_CAR1）
> 操作系统: Ubuntu 22.04 + ROS2 Humble Hawksbill
> 版本: v0.2
> 生成日期: 2026-08-10

---

## 使用说明

### 适用对象

本实验指导书适用于人工智能、机器人工程、智能科学与技术等专业的本科高年级学生，要求修读者已具备以下先修知识：

- Python 编程基础（能独立完成类定义、函数回调、异常处理）
- Linux 系统基本操作（文件目录管理、环境变量配置、进程管理）
- 线性代数基础（矩阵乘法、坐标变换）

### 实验体系总览

| 实验编号 | 实验名称 | 学时 | 类型 | 难度 | 核心技能 |
|---------|---------|------|------|------|---------|
| 实验1 | ROS2系统基础与IMU/电机校准实验 | 8h | 验证性 | ⭐ | 环境搭建、命令行工具、传感器校准 |
| 实验2 | ROS2通信节点与话题/服务/动作实验 | 8h | 设计性 | ⭐⭐ | 节点编写、三类通信、自定义接口 |
| 实验3 | ROS2分布式通信与DDS中间件实验 | 8h | 设计性 | ⭐⭐ | 多机组网、DDS发现、QoS策略 |
| 实验4 | ROS2 Launch多节点启动与配置管理实验 | 4h | 设计性 | ⭐⭐ | Launch脚本、参数注入、条件启动 |
| 实验5 | ROS2 TF2坐标变换与电机速度控制实验 | 6h | 设计性 | ⭐⭐ | TF树、Twist控制、里程计融合 |
| 实验6 | ROS2 URDF机器人建模实验 | 4h | 设计性 | ⭐⭐ | URDF编写、Xacro宏、模型验证 |
| 实验7 | Gazebo三维物理仿真与传感器模拟实验 | 6h | 综合性 | ⭐⭐⭐ | 物理仿真、ros2_control、传感器插件 |
| 实验8 | Rviz2可视化工具与传感器数据调试实验 | 4h | 设计性 | ⭐⭐ | Display面板、TF可视化、配置持久化 |

> **总计**: 48h，验证性实验占 16.7%（1个），设计性实验占 70.8%（6个），综合性实验占 12.5%（1个）。

### 实验递进关系

```
实验1（环境+校准）
  └─→ 实验2（核心通信：节点/话题/服务/动作）
        ├─→ 实验3（分布式+DDS）
        │     └─→ 实验4（Launch编排）
        │           └─→ 实验5（TF2+速度控制）
        │                 ├─→ 实验6（URDF建模）
        │                 │     ├─→ 实验7（Gazebo仿真）
        │                 │     └─→ 实验8（Rviz2可视化）
        │                 └─→ 实验8（Rviz2可视化）
        └─→ 实验4（Launch编排）
```

> 建议按编号顺序推进，实验1-2为基础必修，后续实验可依据学生进度适当调整，但实验6→7→8的 "建模→仿真→可视化" 三段在同一个学期项目中宜连续完成。

### 评分规则

每个实验按百分制评分，评分维度参考 `实验报告要求` 节中的评分标准。课程总评 = Σ(实验得分 × 实验学时) / 48，即各实验按学时加权平均。

---

## 实验环境配置

> 本章为**所有实验的通用环境配置**。每个实验的"实验环境"节仅列出该实验额外需要的软件包或硬件组件。首次实验前请完整执行以下配置流程。

### 硬件平台

| 平台 | 型号 | 核心配置 |
|------|------|---------|
| 实验箱B2 | XFLZ_EAI_B2_PRO | RK3576(8核+6TOPS NPU) + STM32F407, 8GB RAM, 64GB ROM, 6DOF机械臂, 6麦阵列 |
| 小车C1 | XFLZ_EAI_CAR1 | 同B2 SoC + 麦克纳姆轮底盘, GP37-520电机×4, 激光雷达COIN-D6, 深度相机hp60c |
| IMU | BMI088 | 3轴加速度计(16位, ±24g) + 3轴陀螺仪(16位, ±2000°/s), I2C/SPI |
| 激光雷达 | 国科光芯COIN-D6 | dToF, 0.05-12m, ±10mm精度, 360°扫描, 10Hz, 角度分辨率0.09° |
| 深度相机 | 安思疆hp60c | 结构光, 0.2-4m, ≤2mm@1m, 640×480@20fps(深度) + 1920×1080@30fps(彩色) |
| 驱动电机 | GP37-520 | 12V, 360±30rpm空载, 1024线AB相编码器, 122880脉冲/圈 |
| 轮组 | 麦克纳姆轮 | 直径97mm×宽度49mm, 全向移动 |

### 操作系统与核心软件

| 组件 | 版本 | 说明 |
|------|------|------|
| Ubuntu | 22.04 LTS (Jammy) | 上位机操作系统 |
| ROS2 | Humble Hawksbill (LTS) | 机器人中间件，支持至2027年5月 |
| Python | 3.10 (系统自带) | ROS2 Humble 默认 Python 版本 |
| colcon | 最新稳定版 | ROS2 构建工具 |
| Gazebo | Classic 11.10 | 三维物理仿真引擎 |
| Rviz2 | Humble 自带 | 三维可视化工具 |

### 基础环境安装（一次性）

**步骤1：安装 ROS2 Humble**

```bash
# 1. 设置 locale 为 UTF-8
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. 添加 ROS2 仓库密钥与源
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 3. 安装 ROS2 Humble 桌面版（含 Rviz2 与 Gazebo 桥接）
sudo apt update
sudo apt install -y ros-humble-desktop

# 4. 安装 colcon 构建工具与常用开发包
sudo apt install -y python3-colcon-common-extensions python3-rosdep2
```

**步骤2：初始化 rosdep 与工作空间**

```bash
# 初始化 rosdep（包依赖管理）
sudo rosdep init
rosdep update

# 创建课程工作空间
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build --symlink-install
```

**步骤3：配置环境变量（推荐写入 ~/.bashrc）**

```bash
# 编辑 ~/.bashrc，追加以下内容
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
source ~/.bashrc
```

> **说明**：`--symlink-install` 让 Python 脚本在 install 目录中以符号链接方式存在，修改源码后无需重新编译即可生效，大幅提升调试效率。

**步骤4：安装 Gazebo 与 ros2_control 相关包**

```bash
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-robot-state-publisher \
  ros-humble-xacro \
  ros-humble-tf2-tools
```

### 环境验证

安装完成后，依次执行以下命令验证环境就绪：

```bash
# 验证1：ROS2 命令行可用
ros2 --version                    # 应输出版本信息

# 验证2：Rviz2 可启动
rviz2 --help                       # 应输出帮助信息（不要实际启动GUI除非有显示器）

# 验证3：Gazebo 可启动
gz sim --version                   # 应输出版本号

# 验证4：colcon 构建工具链可用
colcon --help                      # 应输出帮助信息

# 验证5：Python 环境可导入 rclpy
python3 -c "import rclpy; print('rclpy OK')"

# 验证6：查看硬件设备（以B2平台为例）
ls /dev/ttyUSB* 2>/dev/null        # 串口设备（IMU/电机/机械臂）
ls /dev/video* 2>/dev/null         # 摄像头设备
```

> 如某条验证失败，请检查对应软件包的安装状态（`dpkg -l | grep ros-humble-<包名>`），并确认 `source /opt/ros/humble/setup.bash` 已执行。

### VS Code 开发配置（推荐）

```bash
# 安装 VS Code（如未安装）
sudo snap install code --classic

# 安装推荐扩展
code --install-extension ms-python.python
code --install-extension ms-iot.vscode-ros
code --install-extension twxs.cmake
code --install-extension ms-vscode.cpptools
```

在 VS Code 中打开 `~/ros2_ws`，创建 `.vscode/settings.json`：

```json
{
  "python.autoComplete.extraPaths": [
    "/opt/ros/humble/lib/python3.10/site-packages",
    "~/ros2_ws/install/lib/python3.10/site-packages"
  ],
  "python.analysis.extraPaths": [
    "/opt/ros/humble/lib/python3.10/site-packages",
    "~/ros2_ws/install/lib/python3.10/site-packages"
  ]
}
```

> 以上配置让 VS Code 能够正确解析 `rclpy`、`std_msgs`、`geometry_msgs` 等 ROS2 Python 包的导入路径，提供代码补全与跳转支持。

### 各实验额外依赖速查

| 实验 | 额外需安装的包 | 平台要求 |
|------|-------------|---------|
| 实验1 | `python3-serial`, `python3-numpy` | B2（需IMU硬件） |
| 实验2 | `example_interfaces`(Humble自带) | B2 或 C1 |
| 实验3 | `ros-humble-rmw-cyclonedds-cpp` | B2 + 额外一台机器（或虚拟机） |
| 实验4 | 无额外依赖 | B2 或 C1 |
| 实验5 | `ros-humble-tf2-tools` | C1 推荐（需移动底盘） |
| 实验6 | `ros-humble-xacro`, `liburdfdom-tools` | B2 或 C1 |
| 实验7 | `ros-humble-gazebo-ros2-control`, `ros-humble-ros2-controllers` | B2 或 C1 |
| 实验8 | `ros-humble-rviz2`(桌面版自带) | B2 或 C1（需GUI显示） |

---

> **注意**：本实验指导书中，实验1、3、4、5、6、7、8 的代码示例基于 ROS2 Humble 标准公开 API 与 hardware-platform-spec.md 设备参数设计，标记为 `[待源码核实]`，源码到位后需核实接口与参数。实验2 的代码已与 `source-codes/exp02-05/` 中实际源码对齐。
