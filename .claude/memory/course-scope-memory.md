---
name: 课程规格数据存储
description: 存储所有课程的规格数据，作为唯一可信源的索引
type: memory
version: 1.0
last_updated: 2026-06-11
---

# 课程规格数据（唯一可信源索引）

本文档记录所有课程的规格数据生成进度和状态。

---

## 课程列表

### Sheet1: 核心实验室课程（7门）

| 课程代码 | 课程名称 | 实验数 | 总学时 | 规格状态 | 生成状态 | 最后更新 |
|---------|---------|-------|-------|---------|---------|---------|
| EXP001 | 机器人视觉应用与开发 | 13 | 48h | ⏳ 待生成 | ⏳ 待生成 | - |
| EXP002 | 机器人自然语言交互应用与开发 | 7 | 32h | ⏳ 待生成 | ⏳ 待生成 | - |
| EXP003 | 机器人ROS2应用与开发 | 8 | 48h | ⏳ 待生成 | ⏳ 待生成 | - |
| EXP004 | 机器人SLAM与Nav应用开发 | 7 | 48h | ⏳ 待生成 | ⏳ 待生成 | - |
| EXP005 | 机器人机械臂应用与开发 | 8 | 32h | ⏳ 待生成 | ⏳ 待生成 | - |
| EXP006 | 机器人大模型综合应用开发 | 11 | 48h | ⏳ 待生成 | ⏳ 待生成 | - |
| EXP007 | 综合实训实践 | 3 | 96h | ⏳ 待生成 | ⏳ 待生成 | - |

### Sheet2: 行业创新应用课程（4门）

| 课程代码 | 课程名称 | 总学时 | 规格状态 | 生成状态 | 最后更新 |
|---------|---------|-------|---------|---------|---------|
| IND001 | 物料分拣应用场景 | 32h | ⏳ 待生成 | ⏳ 待生成 | - |
| IND002 | 柔性制造应用场景 | 32h | ⏳ 待生成 | ⏳ 待生成 | - |
| IND003 | 家庭整理应用场景 | 32h | ⏳ 待生成 | ⏳ 待生成 | - |
| IND004 | 室内巡检应用场景 | 32h | ⏳ 待生成 | ⏳ 待生成 | - |

**状态图标说明**：
- ⏳ 待生成
- 🔄 生成中
- ✅ 已完成
- ❌ 生成失败

---

## 课程规格文件路径

所有课程规格文件统一存储在：
```
courses/{sheet}/{course_id}/_meta/course-spec.yaml
```

示例：
- `courses/sheet1/cv_practice/_meta/course-spec.yaml`
- `courses/sheet2/sorting_scene/_meta/course-spec.yaml`
- `.claude/memory/hardware-platform-spec.md` - 硬件平台规格（新增）

---

## 课程规格模板

### Sheet1课程规格示例

```yaml
# 课程规格（唯一可信源）
course_code: EXP001
course_name: 机器人视觉应用与开发
category: sheet1

# 前置依赖
prerequisites:
  - OpenCV基础
  - Python编程
  - 边缘计算基础

# 学时信息
total_hours: 48
theory_hours: 0
lab_hours: 48

# 技术栈
tech_stack:
  - OpenCV
  - MediaPipe
  - 深度学习

# 实验项目列表（13个）
experiments:
  - id: 1
    name: 基于Lab色彩空间的颜色识别实验
    hours: 2
    tech_stack: [OpenCV]
    objectives: [...]
    contents: [...]
  # ... 其余12个实验

# 元数据
generated_at: 2026-06-11T10:00:00
source_file: input/course_spec.xlsx
source_sheet: Sheet1
```

### Sheet2课程规格示例

```yaml
# 课程规格（唯一可信源）
course_code: IND001
course_name: 物料分拣应用场景
category: sheet2

# 前置依赖
prerequisites:
  - 机器人视觉应用与开发
  - 机器人ROS2应用与开发
  - 机器人机械臂应用与开发

# 学时信息
total_hours: 32
theory_hours: 0
lab_hours: 32

# 技术栈
tech_stack:
  - 主从臂控制
  - 多模态数据采集
  - VLA模型

# 模块列表
modules:
  - id: 1
    name: 场景认知与需求分析
    hours: 4
    type: 验证性
  - id: 2
    name: 硬件平台熟悉
    hours: 4
    type: 验证性
  - id: 3
    name: 核心功能开发
    hours: 12
    type: 设计性
  - id: 4
    name: 系统集成测试
    hours: 8
    type: 综合性
  - id: 5
    name: 成果展示与答辩
    hours: 4
    type: 综合性

# 元数据
generated_at: 2026-06-11T10:00:00
source_file: input/course_spec.xlsx
source_sheet: Sheet2
```

---

## 使用说明

### 1. 生成课程规格

当需要生成课程资源时：
1. ResourceParserAgent读取资源列表
2. 生成course-spec.yaml并保存
3. 更新本文档的状态为"✅ 已完成"

### 2. 读取课程规格

所有后续Agent必须：
1. 读取对应的course-spec.yaml
2. 基于规格数据生成内容
3. 不得凭通识知识生成

### 3. 验证课程规格

ContentAuditAgent审核时：
1. 读取course-spec.yaml作为基准
2. 对比生成内容是否符合规格
3. 标注不一致的地方

---

## 更新日志

| 日期 | 更新内容 |
|------|---------|
| 2026-06-11 | 初始版本，定义11门课程基础信息 |
