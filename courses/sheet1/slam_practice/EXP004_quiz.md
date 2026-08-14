---
course_code: EXP004
course_name: 机器人SLAM与Nav应用开发
version: v1.1
generated_at: 2026-08-14
generator: QuizAgent
mode: standard
source_spec: courses/sheet1/slam_practice/_meta/course-spec.yaml
source_knowledge_graph: courses/sheet1/slam_practice/EXP004_knowledge_graph.md
source_syllabus: courses/sheet1/slam_practice/EXP004_syllabus.md
source_lab_guide: courses/sheet1/slam_practice/_parts/experiment-*.md
csv_sha256: 7a19e14a1973c42831ff6ade5dc99fa2351aa238d05742e2383af845c14a7641
---

# 机器人SLAM与Nav应用开发 练测题库

> 适用对象: 人工智能/机器人工程/智能科学与技术 本科高年级
> 总题目数: 44
> 预计考试时长: 120 分钟
> 模式: 试卷模式（standard）
> 版本: v1.1（扩充至 100% 知识点覆盖）
> 制定日期: 2026-08-14

---

## 使用说明

### 题型分布

| 题型 | 题数 | 单题分值 | 总分 |
|------|------|---------|------|
| 单项选择题 | 27 | 2 分 | 54 分 |
| 多项选择题 | 11 | 2 分 | 22 分 |
| 简答题 | 5 | 3 分 | 15 分 |
| 编程/操作题 | 1 | 9 分 | 9 分 |
| **合计** | **44** | - | **100 分** |

### 难度分布

| 难度 | 比例 | 说明 |
|------|------|------|
| 容易 | 43%（19/44） | 基础概念、术语识记、原理理解 |
| 中等 | 36%（16/44） | 参数作用、流程操作、对比分析 |
| 困难 | 16%（7/44） | 参数调优、多点导航调度、三维SLAM综合 |

### 知识点覆盖率

- 知识图谱总知识点数: 65（7 章 27 节，详见 `EXP004_knowledge_graph.md` 知识点统计表）
- 本套题显式覆盖知识点数: **65/65（100%）**（每题均标注 [知识点 ID]，去重统计）
- 章节覆盖: 7/7 章全覆盖（第1章 11/11、第2章 13/13、第3章 11/11、第4章 9/9、第5章 8/8、第6章 6/6、第7章 7/7）
- 重点章节: 第 2 章 二维激光建图（占 17%）、第 4 章 AMCL 定位（占 14%）、第 3 章 Nav2 导航（占 17%）

---

## 一、单项选择题（每题 2 分，共 54 分）

### 第一章 建图原理与URDF建模

**1. [知识点 1.4.1]** SLAM 的核心矛盾是"鸡生蛋蛋生鸡"问题，指的是？

A. 定位需要地图，建图需要知道自己位置
B. 激光雷达既要做定位又要做建图，算力不够
C. 里程计和 IMU 数据互相矛盾
D. 地图太大无法实时传输

**答案**: A
**解析**: SLAM 的两大子任务互相依赖：定位（我在哪）需要地图，建图（地图什么样）需要先知道位置，因此必须"一边猜一边画"循环求解。

---

**2. [知识点 1.1.2]** car1 机器人中，机械臂关节应使用的 `<joint type>` 是？

A. `fixed`
B. `continuous`
C. `revolute`
D. `planar`

**答案**: C
**解析**: 机械臂舵机关节有角度上下限，用 `revolute`（有限旋转）；`continuous` 用于无限制旋转的车轮；`fixed` 用于固定连接。

---

**3. [知识点 1.4.3]** 占据栅格地图中，数值 -1 / 0 / 100 分别代表？

A. 空闲 / 占据 / 未知
B. 未知 / 空闲 / 占据
C. 占据 / 未知 / 空闲
D. 未知 / 占据 / 空闲

**答案**: B
**解析**: -1 未知（没扫过）、0 空闲（确定无物）、100 占据（确定有墙）。

---

**4. [知识点 1.3.2]** `display.launch.py` 一键启动的三件套是？

A. robot_state_publisher + joint_state_publisher_gui + rviz2
B. base_driver + lidar + slam_toolbox
C. map_server + amcl + bt_navigator
D. rviz2 + gazebo + moveit

**答案**: A
**解析**: display.launch.py 依次启动 joint_state_publisher_gui（关节滑块）、robot_state_publisher（TF）、rviz2（显示）。

---

**5. [知识点 1.1.1]** URDF 中 `<link>` 标签表示机器人的？

A. 身体部件（连杆）
B. 关节连接
C. 传感器配置
D. 坐标变换规则

**答案**: A
**解析**: `<link>` 描述机器人一个身体部件（尺寸/颜色/惯性）；连接两个 link 的是 `<joint>`；TF 由 URDF 自动生成。

---

**6. [知识点 1.4.2]** 一次建图循环的三个要素按正确顺序排列是？

A. 感知 → 定位 → 构图
B. 定位 → 构图 → 感知
C. 构图 → 感知 → 定位
D. 感知 → 构图 → 定位

**答案**: A
**解析**: ①感知（雷达扫描得到距离）→ ②定位（结合上一帧猜自己在哪）→ ③构图（把墙写进地图），循环往复。

---

**7. [知识点 1.2.1]** Xacro 宏的主要作用是？

A. 复用部件模板，避免重复代码
B. 加密机器人模型文件
C. 加速 RViz 渲染
D. 替代 URDF 语法

**答案**: A
**解析**: Xacro 用 `<xacro:macro>` 定义可复用模板（如 4 个相同车轮），改一处参数全部生效。

---

### 第二章 基于SLAM_Toolbox的二维激光建图

**8. [知识点 2.2.2]** `minimum_travel_distance: 0.01` 的作用是？

A. 机器人每次移动 1cm 就触发一次新关键帧
B. 雷达扫描距离上限为 1cm
C. 地图每 1cm 更新一次
D. 回环检测的搜索距离

**答案**: A
**解析**: 该参数是"关键帧触发阈值"——位移超过 0.01m（或转角超过 0.02rad）才存新关键帧，避免每帧都存造成算力浪费。

---

**9. [知识点 2.1.4]** 为什么建图时必须"走闭环路径"（绕一圈回到起点）？

A. 触发回环检测，一次性消除累积漂移
B. 让地图文件更小
C. 提高激光雷达扫描频率
D. 让里程计误差归零

**答案**: A
**解析**: 回环检测识别出"回到已访问区域"后建立回环约束并触发全局优化，一次大修正把整条轨迹的累积漂移抹平。

---

**10. [知识点 2.4.1]** 保存地图后生成的 `.pgm` 文件中，像素值 255 表示？

A. 未知区域
B. 占据（墙）
C. 空闲（可通行）
D. 雷达盲区

**答案**: C
**解析**: `.pgm` 灰度图约定：255=空闲（白）、0=占据（黑）、205=未知（灰）。

---

**11. [知识点 2.1.1]** slam_toolbox 属于哪类 2D SLAM 框架？

A. 基于 Karto 的图优化 SLAM
B. 扩展卡尔曼滤波 SLAM
C. 粒子滤波 SLAM
D. 无回环检测的扫描匹配 SLAM

**答案**: A
**解析**: slam_toolbox 由前端 Scan Matching + 位姿图 + 后端 Ceres 图优化组成，是基于 Karto 的图优化 2D SLAM。

---

**12. [知识点 2.3.1]** `slam.launch.py` 中 slam_toolbox 延迟约多少秒启动？

A. 1s
B. 10s
C. 30s
D. 60s

**答案**: B
**解析**: launch 用 TimerAction(period=10.0) 延迟 10s，等 bringup 的 odom/TF 和雷达 /scan 稳定后再启动，避免刚上电数据抖动导致建图错乱。

---

**13. [知识点 2.4.2]** `.pgm` 地图文件中像素值 205 表示？

A. 未知区域
B. 空闲
C. 占据
D. 雷达盲区

**答案**: A
**解析**: 205=未知（灰）；255=空闲（白）、0=占据（黑）。`.yaml` 中 occupied_thresh/free_thresh 决定灰度到占据/空闲的转换阈值。

---

### 第三章 基于Nav2的机器人自主导航

**14. [知识点 3.1.1]** Nav2 中负责"在 map 坐标系找无碰撞全局路径"的服务器是？

A. controller_server
B. planner_server
C. bt_navigator
D. behavior_server

**答案**: B
**解析**: planner_server 规划全局路径（走哪条路），controller_server 局部跟踪（怎么走），bt_navigator 是总指挥，behavior_server 做异常恢复。

---

**15. [知识点 3.2.2]** global_costmap 的 static_layer 作用是什么？

A. 实时标记动态障碍
B. 把障碍向外膨胀出安全区
C. 加载预先建好的静态地图
D. 压缩地图减少占用

**答案**: C
**解析**: static_layer 订阅 /map 加载实验 2 建好的静态地图；obstacle_layer 标记动态障碍；inflation_layer 做膨胀。

---

**16. [知识点 3.5.2]** 命令行下发单目标导航应使用哪个命令？

A. `ros2 topic pub /cmd_vel`
B. `ros2 service call /navigate_to_pose`
C. `ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose ...`
D. `ros2 param set /amcl`

**答案**: C
**解析**: 导航是"长时间+反馈+可取消"的任务，必须用 Action 通信；`ros2 action send_goal` 是标准下发命令。

---

**17. [知识点 3.2.1]** 本项目 planner_server 使用的全局规划 plugin 是？

A. DWB FollowPath
B. NavFn
C. ThetaStarPlanner
D. SmacPlanner

**答案**: C
**解析**: nav2_params.yaml 中 `planner_plugins: ["GridBased"]` 的 plugin 为 `nav2_theta_star_planner/ThetaStarPlanner`（带视线检查的 A* 变体，路径更直）。

---

**18. [知识点 3.1.2]** 关于 Nav2 服务器的 Lifecycle 生命周期，正确的说法是？

A. 节点启动即 active 可直接工作
B. 节点先 inactive 配置，再激活为 active 才工作
C. 生命周期只对 bt_navigator 生效
D. 激活状态无需 lifecycle_manager 管理

**答案**: B
**解析**: Nav2 服务器启动后先 inactive（配置好但不出力），由 lifecycle_manager 统一激活（autostart: true 自动完成），激活后才开始工作。

---

**19. [知识点 3.4.2]** `navigate_through_poses` 导航器的特点是？

A. 机器人必须依次经过每个途经点
B. 只关心最终目标点
C. 不支持多点任务
D. 仅用于建图

**答案**: A
**解析**: NavigateThroughPoses 要求机器人依次经过 poses[] 中的每个点，最后停在最后一个点，适合巡检/送货路线。

---

### 第四章 基于AMCL的自适应蒙特卡罗定位

**20. [知识点 4.2.2]** 粒子滤波三步循环的顺序是？

A. 更新 → 预测 → 重采样
B. 预测 → 更新 → 重采样
C. 重采样 → 预测 → 更新
D. 预测 → 重采样 → 更新

**答案**: B
**解析**: 先按里程计预测（推粒子），再用雷达匹配更新（打分），最后重采样（优胜劣汰）。

---

**21. [知识点 4.2.3]** AMCL 的"自适应"体现在？

A. 定位不确定时自动增加粒子数加速收敛
B. 地图自动更新
C. 雷达频率自适应
D. 里程计误差自动归零

**答案**: A
**解析**: KLD 采样机制：不确定时粒子增多（加速收敛），确定时粒子减少（省算力），在 min/max_particles（500/2000）之间自适应。

---

**22. [知识点 4.1.1]** 关于里程计（odom）误差，正确的说法是？

A. 误差会随行驶距离累积
B. 误差恒为零
C. 打滑不会产生误差
D. 误差与地面摩擦无关

**答案**: A
**解析**: 轮子打滑、磨损、地面差异都会产生误差，且随行驶**累积**——跑得越远越不知道自己在哪，因此需要 AMCL 全局定位纠正。

---

**23. [知识点 4.3.2]** 给机器人设定初始位姿（手动精确定位）的推荐方式是？

A. RViz 工具栏 "2D Pose Estimate" 点击设定
B. 重启计算机
C. 用力摇晃小车
D. 修改地图文件

**答案**: A
**解析**: "2D Pose Estimate" 会发布 /initialpose 话题，告诉 AMCL"我大概在哪+朝向"，比默认 set_initial_pose(0,0,0) 更准确。

---

### 第五章 局部路径规划与动态避障

**24. [知识点 5.1.1]** DWA 的"动态窗口"指的是？

A. 当前能刹得住的速度组合集合
B. 全部可能的速度组合
C. 全局路径上的离散点
D. 地图中的可通行区域

**答案**: A
**解析**: DWA 只考虑满足加速度限制且能在障碍前刹停的速度组合（动态窗口），在窗口内采样轨迹并评价，这是它"安全"的根本。

---

**25. [知识点 5.2.1]** 关于 TEB（Time Elastic Band），正确的说法是？

A. 把路径看成弹性带，用图优化同时调整轨迹点位置与到达时间
B. 只模拟眼前 1.5 秒的轨迹
C. 不能处理动态障碍
D. 与 DWA 的实现完全相同

**答案**: A
**解析**: TEB 把整段局部路径当"弹性带"，目标函数包含贴路径/避障/时间最短/速度平滑，比 DWA 平滑但算力更高。

---

### 第六章 基于激光雷达的单点与多点导航避障

**26. [知识点 6.2.2]** 多点连续导航中，一段子任务导航失败（ABORTED）后，合理的调度策略是？

A. 记录失败并重试或跳过，而不是盲目重复
B. 无限循环重试直到成功
C. 直接忽略继续下一个目标
D. 关闭导航系统

**答案**: A
**解析**: 工程调度必须检查 action 结果：SUCCEEDED→下一个；ABORTED→记录并有限重试或跳过，避免"静默失败"或死循环。

---

### 第七章 基于RTAB-Map的三维视觉SLAM导航

**27. [知识点 7.2.1]** RGB-D 深度相机（HP60C）同时输出？

A. 彩色图 + 深度图
B. 仅深度图
C. 仅彩色图
D. 已生成的 3D 模型

**答案**: A
**解析**: RGB-D 相机同时输出彩色图与深度图，配合内参 (fx,fy,cx,cy)，每个像素 (u,v) 可反投影为 3D 点 (X,Y,Z)。

---

## 二、多项选择题（每题 2 分，共 22 分）

**1. [知识点 2.2.1, 2.2.3, 2.5.1]** 关于 slam.yaml 参数与地图质量的关系，正确的有？

A. `resolution: 0.05` 表示每格 5cm，越小地图越精细但文件越大
B. `do_loop_closing: true` 开启回环检测，能消除累积漂移
C. `minimum_travel_distance` 改大（如 0.5）会导致地图更新变稀疏
D. 验收时墙厚 >0.1m 说明地图质量优秀

**答案**: ABC
**解析**: D 错误——墙厚应 <0.1m（双墙/重影是不好的），>0.1m 说明有重影或误差。

---

**2. [知识点 3.1.1, 3.3.1, 3.4.1]** 关于 Nav2 架构，正确的说法有？

A. 五大服务器都实现了 Lifecycle 生命周期
B. controller_server 用 DWB 在 odom 系实时跟踪全局路径
C. bt_navigator 用行为树编排导航流程
D. velocity_smoother 负责全局路径规划

**答案**: ABC
**解析**: D 错误——velocity_smoother 是速度平滑器（防止急停急启），全局规划由 planner_server 负责。

---

**3. [知识点 4.1.2, 4.2.1, 4.4.1, 4.4.2]** 关于 AMCL 定位，正确的有？

A. 粒子代表对"我可能在哪"的假设
B. AMCL 用雷达扫描与地图比对来更新粒子权重
C. 机器人被搬走后（kidnapped）AMCL 会自动重新全局定位
D. RViz 中粒子聚成一团表示定位失败

**答案**: ABC
**解析**: D 错误——RViz 中粒子（绿箭头）聚成一团表示定位成功（收敛）；散落各处才表示定位失败。

---

**4. [知识点 5.1.2, 5.1.3, 5.3.1]** 关于 DWB 局部规划与避障，正确的有？

A. DWB 在速度窗口内采样生成候选轨迹，用 critics 打分
B. BaseObstacle critic 直接否决撞墙轨迹
C. local_costmap 是 3m×3m 滚动窗口，跟随机器人移动
D. inflation_radius 调大可以让机器人更贴障碍走

**答案**: ABC
**解析**: D 错误——inflation_radius 调大是让机器人**远离**障碍（膨胀区更大），更贴障碍应调小。

---

**5. [知识点 6.1.1, 6.2.1, 6.3.2]** 关于单点/多点导航，正确的有？

A. `navigate_through_poses` 要求机器人依次经过每个途经点
B. Action 通信包含 goal/feedback/result 三部分
C. progress_checker 检测到长时间无进展会触发行为恢复
D. 多点导航的途经点间距越近越好

**答案**: ABC
**解析**: D 错误——途经点太近会导致到达判定混乱，一般保持间距 >0.5m。

---

**6. [知识点 7.1.1, 7.2.2, 7.4.1]** 关于三维 SLAM（RTAB-Map），正确的有？

A. RTAB-Map 是基于外观实时建图的 RGB-D SLAM 框架
B. OctoMap 用体素表示地图，可压缩可更新
C. 三维 SLAM 相比二维能感知高度与悬空障碍
D. 三维 SLAM 算力要求比二维低

**答案**: ABC
**解析**: D 错误——三维 SLAM 比二维算力要求高得多，这是选型时的重要考量。

---

**7. [知识点 1.1.3, 1.3.1, 1.5.1]** 关于 car1 模型与建图环境，正确的有？

A. URDF 加载后自动生成 TF 树，根节点为 base_footprint
B. car1 由主体、机械臂、爪子三大部分组成
C. 建图环境由驱动层、雷达层、SLAM 算法层、可视化层组成
D. display.launch.py 会驱动底盘电机运动

**答案**: ABC
**解析**: D 错误——display.launch.py 只加载模型并可视化，**不驱动任何电机**，安全无风险。

---

**8. [知识点 2.3.2, 2.3.3]** 关于建图遥控与建图手法，正确的有？

A. slam_teleop 中 w 键前进、a 键左转
B. 建图要求低速，角速度控制在 1.0rad/s 以内
C. 尽量走闭环路径，拐角处减速停留
D. 可以全速快速跑完整个房间

**答案**: ABC
**解析**: D 错误——运动太快会导致激光运动畸变、地图扭曲；必须慢速（线速 ≤0.3m/s、角速 ≤1.0rad/s）。

---

**9. [知识点 3.3.2, 3.5.1, 3.5.3]** 关于局部代价地图与导航启动，正确的有？

A. local_costmap 是 3m×3m 跟随机器人的滚动窗口，实时感知身边障碍
B. navigation.launch.py 一键启动 bringup、雷达、localization、navigation、RViz
C. 导航成功三要素：地图质量好、定位准确、速度约束合理
D. local_costmap 覆盖整个房间，静态障碍提前全部标记

**答案**: ABC
**解析**: D 错误——local_costmap 只关心身边 3 米（滚动窗口），静态障碍由 global_costmap 的 static_layer 全图标记。

---

**10. [知识点 5.2.1, 5.3.2, 5.3.3]** 关于 TEB 与动态避障，正确的有？

A. TEB 用图优化调整弹性带，可加时间/速度约束
B. 动态避障由 local_costmap（voxel_layer）感知 + controller 实时绕行完成
C. 绕不过障碍时可调大 inflation_radius 或降低 max_vel_x
D. TEB 的算力需求比 DWA/DWB 更低

**答案**: ABC
**解析**: D 错误——TEB 需图优化整段路径，算力高于 DWA/DWB，这是本项目默认选 DWB 的原因之一。

---

**11. [知识点 7.1.2, 7.3.1, 7.3.2]** 关于 RTAB-Map 回环检测与三维建图流程，正确的有？

A. RTAB-Map 用图像词袋模型做回环检测
B. 三维建图流程：启动相机 → 启动 RTAB-Map → 操控走遍场景 → 保存地图
C. 三维导航需将 OctoMap 转换后交给 Nav2 消费
D. RGB-D 相机在强光下仍能稳定输出深度

**答案**: ABC
**解析**: D 错误——RGB-D 相机对强光/反光/远距离敏感（深度失效），这是三维 SLAM 的工程局限。

---

## 三、简答题（每题 3 分，共 15 分）

**1. [知识点 2.1.2, 2.1.3, 2.1.4]** 请分别说明 slam_toolbox 的"前端 Scan Matching、后端图优化、回环检测"各解决什么问题，并解释为什么"回环检测"是消除累积漂移的关键。

**参考答案**: 前端 Scan Matching 解决"局部对正"——在里程计预测位姿附近搜索与局部地图匹配得分最高的位姿，消除小步累积的随机误差；后端图优化解决"全局摊平"——把位姿图所有节点与约束统一用 Ceres 最小化残差，让全局轨迹自洽；回环检测解决"累积漂移"——当机器人回到已访问区域时，识别出"这帧和某历史帧相同"，建立一条"长距离约束"，一次全局优化就能把整条轨迹的漂移一次性消除。因为普通前后端只能修正"相邻帧之间"的误差，而回环提供的是"相距很远的帧之间"的约束，是唯一能修正长时间累积漂移的手段。

---

**2. [知识点 4.2.2, 4.3.1]** 用你自己的话描述粒子滤波"预测/更新/重采样"三步分别用了什么数据、做了什么，并解释 `update_min_a: 0.15` 的作用。

**参考答案**: ①预测：按里程计（odom）给出的运动增量，把每个粒子的位置"推着走"一步，用的是轮速/IMU 融合数据；②更新：拿一帧激光扫描与地图比对，给每个粒子打分（扫描吻合的打高分），用的是激光雷达数据；③重采样：淘汰低分粒子、复制高分粒子，使粒子逐步集中到真实位置。`update_min_a: 0.15` 表示"机器人转动 0.15rad 才做一次更新循环"——避免每帧激光都更新，降低算力消耗，同时保证粒子在机器人停止时不会被频繁重采样。

---

**3. [知识点 5.2.2, 7.4.1]** 对比 DWA/DWB 与 TEB 的差异；再对比二维 SLAM 与三维 SLAM（RTAB-Map）的适用场景，说明各自选型依据。

**参考答案**: DWA/DWB 只模拟"眼前 1.5 秒"的短轨迹，在速度窗口内采样打分，计算快、适合低算力平台，但路径较"糙"；TEB 把整段局部路径当"弹性带"用图优化调整位置与时间，更平滑、可加时间/速度约束，但算力高。二维 SLAM 用激光雷达、地图为俯视栅格、算力低、Nav2 直接消费，适合地面平坦巡检/送货；三维 SLAM 用 RGB-D 相机、地图为点云/OctoMap（含高度信息）、算力高、需转换才能喂给 Nav2，适合出现悬空障碍、高度分层、抓取定位需求的场景。选型依据：任务是否需要"高度"这一维信息，以及算力是否承受得起。

---

**4. [知识点 1.5.1, 1.5.2]** 建图环境由哪几层组成？一张"好地图"有哪些验收标准？

**参考答案**: 建图环境四层：①驱动层（bringup：底盘驱动+robot_state_publisher+EKF 里程计）；②雷达层（lidar：发布 /scan）；③SLAM 算法层（slam_toolbox）；④可视化层（RViz）。好地图验收四指标：墙体厚度 <0.1m（无重影）、尺寸误差 <2%（地图量测 vs 卷尺）、墙角直角 90°±2°、闭环位置误差 <0.1m 且航向误差 <5°。

---

**5. [知识点 6.2.2, 6.3.1]** 多点导航中一段子任务失败后如何处理？评估导航系统鲁棒性常用哪些指标？

**参考答案**: 处理策略：检查 Action 返回结果——SUCCEEDED 则执行下一个目标；ABORTED 则记录失败原因并**有限重试 1 次**或跳过，避免死循环；全程打印每段结果便于定位问题。鲁棒性评估指标：到达率（成功到达占比，≥80%）、路径平滑度（无急转/抖动）、避障响应时间（障碍出现到开始绕行 <2s）、中途停车次数（非终点停车 ≤1 次/任务）、恢复动作触发频率。

---

## 四、编程/操作题（9 分）

**1. [知识点 3.5.2, 6.1.2, 6.2.1, 6.2.2]** 完成下面的 Python 调度函数：给定 `goals` 列表（每个元素是 `(x, y, yaw)` 目标点），依次调用 Nav2 的 `navigate_to_pose` 动作导航到每个目标；每个目标失败时自动重试 1 次；全程打印每个目标的执行结果；导航前先检查目标点是否在地图范围内（可用 costmap 查询或简单边界判断）。

```python
import rclpy
from rclpy.node import Node
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient


class NavScheduler(Node):
    def __init__(self):
        super().__init__('nav_scheduler')
        self.client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

    def navigate(self, x, y, yaw):
        """阻塞等待单个目标完成，返回 True/False。"""
        if not self.client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn('navigate_to_pose 服务不可用')
            return False
        # 构造目标（frame_id 必须为 map；yaw 转四元数，仅绕 Z 轴）
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.z = ...
        # TODO: 将 yaw 转换为四元数 (0,0,sin(yaw/2),cos(yaw/2))
        send_future = self.client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        if not goal_handle.accepted:
            return False
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        return result_future.result().status == 4  # SUCCEEDED

    def run_goals(self, goals):
        # TODO: 遍历 goals，逐目标导航；失败重试 1 次；打印结果
        pass


def main():
    rclpy.init()
    node = NavScheduler()
    node.run_goals([(1.0, 0.5, 0.0), (1.5, 1.5, 1.57), (0.5, 1.0, 3.14)])
    node.destroy_node()
    rclpy.shutdown()
```

**评分要点**（共 9 分）:
- 目标构造与 frame_id 正确（2 分）：PoseStamped 使用 `map` 系、位置/四元数正确
- Action 异步调用与结果解析正确（2 分）：send_goal_async / get_result_async / status==4 判断
- 失败重试逻辑（2 分）：失败重试 1 次，避免死循环（对应知识点 6.2.2 调度策略）
- 可达性预检 + 结果打印（3 分）：目标在地图范围内/代价地图中非致命代价，不可达跳过并记录；打印每步结果

---

## 附：知识点覆盖对照（65/65 = 100%）

| 章节 | 单选 | 多选 | 简答/编程 | 覆盖/总数 |
|------|------|------|----------|-----------|
| 第1章 建图原理与URDF | Q1~Q7 | Q7 | 简答4 | 11/11 |
| 第2章 SLAM_Toolbox建图 | Q8~Q13 | Q1, Q8 | 简答1 | 13/13 |
| 第3章 Nav2自主导航 | Q14~Q19 | Q2, Q9 | 编程1 | 11/11 |
| 第4章 AMCL定位 | Q20~Q23 | Q3 | 简答2 | 9/9 |
| 第5章 局部规划与避障 | Q24, Q25 | Q4, Q10 | 简答3 | 8/8 |
| 第6章 单点/多点导航 | Q26 | Q5 | 编程1, 简答5 | 6/6 |
| 第7章 RTAB-Map三维SLAM | Q27 | Q6, Q11 | 简答3, 简答5 | 7/7 |
| **合计** | **27** | **11** | **6** | **65/65（100%）** |

### 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-14 | 初版（22 题，显式覆盖 34/65） |
| v1.1 | 2026-08-14 | 扩充至 44 题，显式覆盖 65/65（100%）；题型分值与难度分布同步调整 |
