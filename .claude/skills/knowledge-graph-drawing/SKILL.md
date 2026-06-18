---
name: knowledge-graph-drawing
description: 知识图谱绘制技能 - 将三级知识结构可视化为图形
trigger: 知识图谱、可视化、知识点关系图
---

# 知识图谱绘制技能

本技能提供知识图谱的可视化绘制方法，用于生成知识结构图形。

---

## 一、Mermaid语法基础

### 1.1 图形类型
| 类型 | 语法 | 用途 |
|-----|-----|-----|
| flowchart | `graph LR/TB` | 流程图 |
| sequenceDiagram | `sequenceDiagram` | 时序图 |
| classDiagram | `classDiagram` | 类图 |
| stateDiagram | `stateDiagram` | 状态图 |

### 1.2 节点形状
```mermaid
graph LR
    A[矩形节点]
    B(圆角矩形)
    C((圆形))
    D{菱形}
    E[[子程序]]
    F[(圆柱体)]
```

### 1.3 连线样式
```mermaid
graph LR
    A --> B        <!-- 箭头线 -->
    C --> D        <!-- 实线 -->
    E -.-> F       <!-- 虚线 -->
    G ==> H        <!-- 加粗线 -->
    I --- J        <!-- 无箭头 -->
```

---

## 二、知识图谱图形模板

### 2.1 三级结构图
```mermaid
graph TB
    subgraph 第1章[第1章 感知技术]
        A1[1.1 视觉感知]
        A2[1.2 听觉感知]
        A3[1.3 触觉感知]
    end

    subgraph 第2章[第2章 决策规划]
        B1[2.1 运动规划]
        B2[2.2 任务规划]
    end

    subgraph 第3章[第3章 控制执行]
        C1[3.1 运动控制]
        C2[3.2 力控]
    end

    A1 --> B1
    A2 --> B2
    B1 --> C1
    B2 --> C2
```

### 2.2 知识点依赖图
```mermaid
graph LR
    A[基础概念] --> B[核心原理]
    B --> C[应用技能]
    C --> D[综合实践]

    style A fill:#e1f5fe
    style B fill:#b3e5fc
    style C fill:#81d4fa
    style D fill:#03a9f4
```

### 2.3 课程依赖图
```mermaid
graph LR
    A[Python编程] --> B[ROS机器人]
    A --> C[计算机视觉]
    B --> D[SLAM]
    B --> E[机械臂]
    C --> F[大模型]
    D --> F
    E --> F
    F --> G[综合实训]
```

---

## 三、样式设置

### 3.1 节点样式
```mermaid
graph TB
    A[节点]:::style1
    B((圆形)):::style2
    C{条件}:::style3

    classDef style1 fill:#f9f,stroke:#333,stroke-width:4px
    classDef style2 fill:#ff9,stroke:#f90,stroke-width:2px
    classDef style3 fill:#9f9,stroke:#090,stroke-width:2px
```

### 3.2 颜色语义
| 颜色 | 语义 | 适用场景 |
|-----|------|---------|
| #e1f5fe | 浅蓝 | 基础层级 |
| #b3e5fc | 中蓝 | 中间层级 |
| #81d4fa | 深蓝 | 核心层级 |
| #03a9f4 | 主蓝 | 重点内容 |
| #ffecb3 | 浅黄 | 注意提醒 |
| #ffcdd2 | 浅红 | 难点警示 |

### 3.3 布局方向
| 方向 | 说明 |
|-----|------|
| TB | 从上到下 |
| TD | 从上到下（等同于TB） |
| BT | 从下到上 |
| LR | 从左到右 |
| RL | 从右到左 |

---

## 四、导出选项

### 4.1 Mermaid源码
直接输出Mermaid语法代码，便于嵌入Markdown。

### 4.2 HTML渲染
```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<div class="mermaid">
graph TB
    A[知识图谱]
</div>
```

---

## 五、实用模板

### 5.1 知识点类型分布图
```mermaid
pie title 知识点类型分布
    "概念类" : 40
    "原理类" : 30
    "流程类" : 20
    "事实类" : 10
```

### 5.2 学习路径图
```mermaid
graph LR
    A[入门] --> B[基础]
    B --> C[进阶]
    C --> D[应用]
    D --> E[综合]

    A -->|"易"| A1[知识点1]
    B -->|"中"| B1[知识点2]
    C -->|"中"| C1[知识点3]
    D -->|"难"| D1[知识点4]
    E -->|"难"| E1[知识点5]
```

---

## 六、使用场景

### 6.1 知识图谱文档
在知识图谱Markdown文档末尾添加可视化图形。

### 6.2 教学大纲
在学时分配表格后添加知识依赖图。

### 6.3 实验指导书
在实验项目列表后添加技能递进图。

---

## 七、更新日志
| 日期 | 更新内容 |
|------|---------|
| 2026-06-11 | 初始版本 |
