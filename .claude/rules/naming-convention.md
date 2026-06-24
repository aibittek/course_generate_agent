---
name: 命名规范
description: 课程资源的文件命名和目录规范
priority: high
---

# 命名规范规则

本文档定义课程资源生成过程中的命名规范。

---

## 一、目录命名

### 1. 顶层目录
```
courses/
```

### 2. 分类目录
| 分类 | 目录名 | 说明 |
|------|-------|------|
| 核心实验室 | `sheet1/` | Sheet1的7门课程 |
| 行业创新应用 | `sheet2/` | Sheet2的4门课程 |

### 3. 课程目录
- **格式**: `{课程英文标识}/`
- **示例**: `cv_practice/`, `ros_practice/`

---

## 二、课程英文标识

### Sheet1: 核心实验室课程
| 课程名称 | 英文标识 |
|---------|---------|
| 计算机视觉实践 | `cv_practice` |
| 语音交互实践 | `speech_practice` |
| ROS机器人实践 | `ros_practice` |
| SLAM机器人实践 | `slam_practice` |
| 机械臂应用开发实践 | `arm_practice` |
| 大模型交互实践 | `llm_practice` |
| 综合实训实践 | `training` |

### Sheet2: 行业创新应用实验室课程
| 课程名称 | 英文标识 |
|---------|---------|
| 物料分拣应用场景 | `sorting_scene` |
| 柔性制造应用场景 | `manufacturing_scene` |
| 家庭整理应用场景 | `home_scene` |
| 室内巡检应用场景 | `inspection_scene` |

---

## 三、文档文件命名

### 3.1 命名格式
```
{课程英文标识}_{文档类型}.md
```

### 3.2 文档类型编码
| 类型 | 编码 | 说明 |
|------|------|------|
| 知识图谱 | `knowledge_graph` | 三级知识结构 |
| 教学大纲 | `syllabus` | 教学设计文档 |
| 实验指导书 | `lab_guide` | 实验项目指导 |
| 练测题库 | `quiz` | 练习测试题 |

### 3.3 元数据文件
| 文件 | 命名 | 说明 |
|------|------|------|
| 课程规格 | `course-spec.yaml` | 固定名称，解析自 CSV |
| 生成日志 | `generation-log.md` | 固定名称 |
| 使用说明 | `README.md` | 固定名称 |

---

## 四、完整目录结构示例

```
courses/
├── sheet1/
│   ├── cv_practice/
│   │   ├── _meta/
│   │   │   ├── course-spec.yaml
│   │   │   └── generation-log.md
│   │   ├── cv_practice_knowledge_graph.md
│   │   ├── cv_practice_syllabus.md
│   │   ├── cv_practice_lab_guide.md
│   │   ├── cv_practice_quiz.md
│   │   └── README.md
│   ├── speech_practice/
│   │   └── ...
│   └── ...
└── sheet2/
    ├── sorting_scene/
    │   ├── _meta/
    │   └── ...
    └── ...
```

---

## 五、命名禁止规则

### ❌ 禁止的命名方式
1. **中文文件名**: `计算机视觉实践_知识图谱.md`
2. **包含空格**: `cv practice_knowledge_graph.md`
3. **特殊字符**: `cv@practice.md`, `cv#practice.md`
4. **超长名称**: 课程英文标识不超过20字符
5. **大小写混乱**: `CV_Practice.md`（应全小写）

### ✅ 正确的命名方式
1. **全小写**: `cv_practice_knowledge_graph.md`
2. **下划线分隔**: `arm_practice_lab_guide.md`
3. **固定编码**: `ros_practice_syllabus.md`

---

## 六、版本文件命名

### 格式
```
{原文件名}_v{版本号}.md
```

### 示例
```
cv_practice_knowledge_graph_v0.1.md
cv_practice_knowledge_graph_v0.2.md
```

---

## 七、更新日志
| 日期 | 更新内容 |
|------|---------|
| 2026-06-11 | 初始版本 |
