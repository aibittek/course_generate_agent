# EXP006 课程生成进度

> 课程: 机器人大模型综合应用开发
> 生成日期: 2026-08-14（**v4.0 全量重新生成**）
> 模式: human_waiver（源码位于 ROS2 工作空间 ros2_ws/src/xflz_eai_car1/app/eai_factory/，未复制到 source-codes/EXP006/）

---

## 总体进度

| Step | 任务 | 状态 | 产出 | 行数/大小 |
|------|------|------|------|----------|
| 1 | 解析 EXP006 spec | ✅ 完成 | `_meta/course-spec.yaml`（eai_factory 智慧工厂，9 实验/48h） | 285 行 |
| 2 | 知识图谱 + 教学大纲 | ✅ 完成 | `EXP006_knowledge_graph.md` + `EXP006_syllabus.md` | 367 + 262 行 |
| 3 | 源码仓库初始化 | ✅ 完成 | 源码位于 `ros2_ws/src/xflz_eai_car1/app/eai_factory/`（human_waiver 放行） | - |
| 4 | 9 个实验内容生成 | ✅ 完成 | `_parts/experiment-{1..9}.md` | 2662+ 行 |
| 4.5 | 合并为 Lab Guide | ✅ 完成 | `EXP006_lab_guide.md` | 190.3 KB |
| 5 | 练测题生成 | ✅ 完成 | `EXP006_quiz.md` | 34 题 / 100 分 |
| 6 | 内容审核 | ✅ 完成（A 级 97/100） | `_meta/content-audit-report.md` | 2 页 |
| 7 | 质量审核 | ✅ 完成（A 级，用户确认签字） | `_meta/quality-review-report.md` | 3 页 |
| 8 | 资源整合输出 | ✅ 完成 | `README.md` + `_meta/generation-log.md` | 2 文件 |

**完成度**: 8/8（全部完成，资源包可直接使用）

---

## 关键统计

### 实验概览
- 实验总数: 9
- 总学时: 48h（验证性 4h + 设计性 8h + 综合性 36h）
- 难度分布: ⭐ 1 + ⭐⭐ 3 + ⭐⭐⭐ 5
- 类型分布: 验证性 1 + 设计性 2 + 综合性 6

### 实验列表
| 编号 | 名称 | 学时 | 类型 | 难度 |
|------|------|------|------|------|
| exp01 | 具身智能工厂--项目需求分析 | 4h | 验证性 | ⭐ |
| exp02 | 具身智能工厂--系统架构设计 | 4h | 设计性 | ⭐⭐ |
| exp03 | 具身智能工厂--接口功能设计 | 4h | 设计性 | ⭐⭐ |
| exp04 | 具身智能工厂--语音交互集成测试 | 6h | 综合性 | ⭐⭐ |
| exp05 | 具身智能工厂--视觉自适应装货集成测试 | 8h | 综合性 | ⭐⭐⭐ |
| exp06 | 具身智能工厂--分拣集成测试 | 4h | 综合性 | ⭐⭐⭐ |
| exp07 | 具身智能工厂--码垛集成测试 | 6h | 综合性 | ⭐⭐⭐ |
| exp08 | 具身智能工厂--危险急停集成测试 | 4h | 综合性 | ⭐⭐⭐ |
| exp09 | 具身智能工厂--全功能快速验证 | 8h | 综合性 | ⭐⭐⭐ |

### 知识点覆盖
- 知识图谱: 6 章 16 节 **42 知识点**
  - 概念类: 10
  - 原理类: 17
  - 流程类: 12
  - 事实类: 3
- 难度分布: 记忆 11 + 理解 18 + 应用 13 + 分析 0
- 实验-知识点映射覆盖率: 100%（每实验均关联对应章节知识点）

### 测验题
- 总题数: 34（单选 20 × 2分 + 多选 8 × 4分 + 简答 4 × 5分 + 编程 2 × 4分 = 100 分）
- 显式覆盖知识点: 42/42（100%）
- 难度分布: 容易 17 + 中等 10 + 困难 7

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v4.0 | 2026-08-14 | **全量重新生成**：EXP006 由旧"机器人大模型"11 实验重构为 eai_factory 具身智能工厂（装货/分拣/码垛/安全生产）综合项目 9 章节；course-spec.csv EXP006 区域重写（需求分析→架构设计→接口设计→语音/视觉装货/分拣/码垛/急停集成测试→全功能快速验证），行结构对齐 EXP005（22 列表头 S=knowledge_points/T=objectives/U=exp_content/V=notes） |
| v4.0.1 | 2026-08-14 | 实验名统一加"具身智能工厂--"前缀（CSV+全部文档）；**实验4(语音交互)改为纯语音链路**：launch 新增 start_scheduler/start_safety 开关（现共 9 开关），快速验证用最小化启动命令（start_base/start_vision/start_grasp/start_conveyor/start_safety:=false），去除机械臂/视觉相关内容，任务执行与完成播报留待 exp09 |

## 关键事实锚点（源码）

- 一键启动: `ros2 launch eai_factory eai_factory.launch.py`（7 开关: start_base/viz/voice/vision/grasp/conveyor/radar）
- 任务服务: `/eai_factory/start_load|start_sort|start_palletize`（std_srvs/srv/Trigger）
- 抓取 confirm: `/eai_factory/grasp/confirm`（debug 模式）
- 流水线: `/eai_factory/conveyor/run_until_sensor|emergency_stop|reset_emergency`
- 安全: `/eai_factory/safety/danger`、`/eai_factory/safety/status`（扇区 ±30°/20cm/0.5s，危险释放 6 舵机力矩）
- 停止: `bash scripts/stop_eai_factory.sh`
