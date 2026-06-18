---
name: 数据一致性规则
description: 确保课程生成内容的数据一致性
priority: high
---

# 数据一致性规则

本文档定义课程资源生成的数据一致性规则，确保各文档间数据准确对应。

---

## 一、数量一致性

### 1.1 练测题数量一致性

**规则**：
```
统计表总题数 = 实际单选题数 + 实际多选题数 + 实际简答题数 + 实际编程题数
```

**检查项**：
- [ ] 封面/使用说明中的总题数准确
- [ ] 题型分布表数据准确
- [ ] 实际题目数量与统计一致

**示例**：
```markdown
✅ 正确：
使用说明: 总题目数36题
题型分布表: 单选20 + 多选10 + 简答4 + 编程2 = 36题
实际题目: 26道单选 ❌ 不一致！

应修正为:
实际题目: 20道单选 + 10道多选 + 4道简答 + 2道编程 = 36题
```

### 1.2 知识点数量一致性

**规则**：
```
知识点总数 = Σ(各章知识点数)
```

**检查项**：
- [ ] 知识点统计表数据准确
- [ ] 各章节知识点总和一致

### 1.3 实验数量一致性

**规则**：
```
课程规格实验数 = 教学大纲实验数 = 实验指导书实验数
```

**检查项**：
- [ ] course-spec.yaml中的实验数
- [ ] 教学大纲实验项目表数量
- [ ] 实验指导书实验数量

---

## 二、学时一致性

### 2.1 总学时一致性

**规则**：
```
课程规格total_hours = 知识图谱总学时 = 教学大纲总学时 = 实验指导书总学时
```

**检查项**：
- [ ] course-spec.yaml: total_hours
- [ ] 知识图谱元数据: 总学时
- [ ] 教学大纲: 学时分配表合计
- [ ] 实验指导书: 实验项目学时合计

**示例**：
```markdown
✅ 一致：
- course-spec.yaml: total_hours: 48
- 知识图谱: 总学时: 48h
- 教学大纲: 合计48h
- 实验指导书: 实验总学时48h

❌ 不一致：
- course-spec.yaml: total_hours: 48
- 教学大纲: 理论6h + 实验12h = 18h  ← 错误！
```

### 2.2 实验学时一致性

**规则**：
```
Σ(各实验学时) = 总学时
```

**检查项**：
- [ ] 实验项目学时加总正确
- [ ] 大纲学时分配与实验指导书一致

---

## 三、编号唯一性

### 3.1 知识点编号唯一性

**规则**：
```
知识点编号全局唯一，格式: X.X.X（章.节.知识点）
```

**检查项**：
- [ ] 知识图谱中无重复编号
- [ ] 编号连续无跳号
- [ ] 格式统一（X.X.X）

**示例**：
```markdown
✅ 正确：
1.1.1, 1.1.2, 1.1.3
1.2.1, 1.2.2
2.1.1, 2.1.2

❌ 错误：
1.1.1, 1.1.1 （重复）
1.1.1, 1.1.3 （跳号）
1.1.1, 1-1-2 （格式不一致）
```

### 3.2 实验编号唯一性

**规则**：
```
实验编号全局唯一，从1开始连续递增
```

**检查项**：
- [ ] 实验编号无重复
- [ ] 编号连续
- [ ] 各文档编号一致

---

## 四、引用一致性

### 4.1 知识点引用一致性

**规则**：
```
题目/实验标注的知识点编号必须存在于知识图谱中
```

**检查项**：
- [ ] 练测题标注的知识点编号在知识图谱中存在
- [ ] 实验指导书关联的知识点编号正确
- [ ] 教学大纲关联的知识点编号正确

**示例**：
```markdown
✅ 正确：
知识图谱: 1.1.1, 1.1.2, 1.1.3
练测题: [知识点1.1.1] 题目... ✅

❌ 错误：
知识图谱: 1.1.1, 1.1.2
练测题: [知识点3.3.1] 题目... ❌ 编号不存在
```

### 4.2 实验引用一致性

**规则**：
```
实验名称在各文档中必须一致
```

**检查项**：
- [ ] course-spec.yaml中的实验名称
- [ ] 教学大纲实验项目表名称
- [ ] 实验指导书实验标题

---

## 五、交叉校验规则

### 5.1 知识图谱 ↔ 教学大纲

**校验项**：
- [ ] 大纲章节与知识图谱章节对应
- [ ] 大纲教学内容覆盖知识图谱知识点
- [ ] 学时分配合理

### 5.2 知识图谱 ↔ 实验指导书

**校验项**：
- [ ] 每个实验关联≥1个知识点
- [ ] 关联的知识点编号正确
- [ ] 实验覆盖主要知识点

### 5.3 知识图谱 ↔ 练测题库

**校验项**：
- [ ] 知识点覆盖率≥90%
- [ ] 题目标注的知识点编号正确
- [ ] 知识点-题目映射表准确

### 5.4 教学大纲 ↔ 实验指导书

**校验项**：
- [ ] 实验数量一致
- [ ] 实验名称一致
- [ ] 学时分配一致

---

## 六、自动检查脚本（伪代码）

```python
def check_data_consistency(course_id):
    """检查课程数据一致性"""
    
    # 读取所有文档
    spec = read_course_spec(course_id)
    kg = read_knowledge_graph(course_id)
    syllabus = read_syllabus(course_id)
    lab_guide = read_lab_guide(course_id)
    quiz = read_quiz(course_id)
    
    errors = []
    
    # 1. 检查学时一致性
    if spec.total_hours != kg.total_hours:
        errors.append("学时不一致: spec vs kg")
    if spec.total_hours != syllabus.total_hours:
        errors.append("学时不一致: spec vs syllabus")
    if spec.total_hours != lab_guide.total_hours:
        errors.append("学时不一致: spec vs lab_guide")
    
    # 2. 检查实验数量一致性
    if len(spec.experiments) != len(syllabus.experiments):
        errors.append("实验数量不一致: spec vs syllabus")
    if len(spec.experiments) != len(lab_guide.experiments):
        errors.append("实验数量不一致: spec vs lab_guide")
    
    # 3. 检查练测题数量一致性
    actual_count = (len(quiz.single_choice) + len(quiz.multiple_choice) +
                    len(quiz.short_answer) + len(quiz.programming))
    if quiz.stated_total != actual_count:
        errors.append(f"练测题数量不一致: 统计{quiz.stated_total} vs 实际{actual_count}")
    
    # 4. 检查知识点编号唯一性
    kg_ids = [kp.id for kp in kg.knowledge_points]
    if len(kg_ids) != len(set(kg_ids)):
        errors.append("知识点编号有重复")
    
    # 5. 检查知识点引用一致性
    quiz_refs = [q.knowledge_point_id for q in quiz.questions]
    for ref in quiz_refs:
        if ref not in kg_ids:
            errors.append(f"题库引用不存在的知识点: {ref}")
    
    return errors
```

---

## 七、违规处理

### 7.1 数量不一致

| 类型 | 严重程度 | 处理方式 |
|------|---------|---------|
| 练测题数量不一致 | 🔴 高 | 立即修正统计表或实际题目 |
| 学时数量不一致 | 🔴 高 | 回溯检查，以course-spec为准 |
| 实验数量不一致 | 🔴 高 | 补充缺失实验或修正统计 |

### 7.2 编号不一致

| 类型 | 严重程度 | 处理方式 |
|------|---------|---------|
| 知识点编号重复 | 🔴 高 | 重新编号 |
| 知识点引用错误 | 🟡 中 | 修正引用 |
| 格式不统一 | 🟢 低 | 统一格式 |

---

## 八、更新日志

| 日期 | 更新内容 |
|------|---------|
| 2026-06-11 | 初始版本 |
