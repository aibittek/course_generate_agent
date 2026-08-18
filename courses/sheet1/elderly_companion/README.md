# 机器人大模型综合应用开发（老人跌倒监护项目）课程资源包

> 版本: v1.0
> 生成日期: 2026-08-18
> 课程编号: EXP006a（独立规格文件 `input/course_spec_elderly_companion.csv`）

## 资源包概述

本资源包包含 **机器人大模型综合应用开发（老人跌倒监护项目）**（EXP006a）的全套教学资源，适用于人工智能/机器人工程/智能科学与技术 本科高年级。

本课程以**老人跌倒监护 elderly_companion** 综合项目为主线，覆盖需求分析 → 架构设计 → 配置与接口设计 → 语音交互 / 视觉检测与姿态估计 / 跌倒判定 / 告警与证据 / LLM对话与VLM复核集成测试 → 全功能快速验证的完整开发闭环。系统基于 YOLOv8 行人检测、BlazePose/RTMPose 姿态估计、六状态机跌倒判定、六麦阵列语音交互与本地大模型（Qwen3.5 RKLLM）构建。

## 资源清单

| 文件 | 说明 | 规模 |
|------|------|------|
| [知识图谱](EXP006a_knowledge_graph.md) | 6 章 13 节三级知识结构 | 39 知识点 |
| [教学大纲](EXP006a_syllabus.md) | 教学目标/学时分配/考核方式 | 48h / 9 实验 |
| [实验指导书](EXP006a_lab_guide.md) | 9 个实验项目完整指导 | 3611 行 |
| [练测题库](EXP006a_quiz.md) | 多种题型配套练习 | 34 题 / 100 分 |
| 审核报告 | `_meta/content-audit-report.md` + `_meta/quality-review-report.md` | A 级 |

## 使用说明

### 1. 知识图谱
- 用于教师备课和学生预习
- 可作为课程内容规划的参考

### 2. 教学大纲
- 包含完整的教学目标、内容、学时、考核
- 需根据实际情况调整

### 3. 实验指导书
- 包含详细的实验步骤和评分标准
- 建议课前发放给学生预习

### 4. 练测题库
- 包含多种题型，覆盖全部 39 个知识点
- 可用于平时练习和期末考试

## 快速上手（全功能验证）

```bash
# 1. 环境自检（依赖/模型/串口/ALSA 完整性）
python3 common/env_check.py --config config/fall_config.yaml

# 2. 文本模式全链路（无需麦克风/扬声器，验证状态机+LLM+告警路由）
python3 apps/fall_video_demo.py --video testdata/fall_slow_x264.mp4 --text

# 3. 离线视频语音全链路（唤醒→对话→跌倒→喊救命/没事）
python3 apps/fall_video_demo.py --video testdata/fall_slow_x264.mp4 --mjpeg

# 4. 实时摄像头（需 ROS 相机节点，另终端先启动）
ros2 launch car1_peripherals depth_camera.launch.py
python3 apps/fall_app.py --mode camera --mjpeg --save

# MJPEG 预览：浏览器打开 http://<板端IP>:8088/fall.mjpg
```

## 关联资源

### 先修课程
- 机器人视觉应用与开发（EXP001）— 必须
- 机器人自然语言交互应用与开发（EXP002）— 必须
- Python 编程、边缘计算基础 — 建议

### 配套设备
- 具身智能实验箱B2 / 具身智能机器人小车C1（RK3576 + STM32F407）
- 深度相机 HP60C、讯飞六麦阵列、STM32 告警硬件（蜂鸣器/LED/OLED）
- 离线测试视频（`testdata/fall_slow_x264.mp4`，gitignore 不入库）

### 源码位置
- `ros2_ws/src/xflz_eai_car1/app/elderly_companion/`（common/vision/fall/speech/llm/config/apps + docs/01-10）

## 反馈渠道

如有问题或建议，请联系课程负责人。

---

**资源包版本**: v1.0
**最后更新**: 2026-08-18
