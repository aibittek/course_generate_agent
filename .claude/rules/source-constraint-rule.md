---
name: 源数据约束规则
description: 确保所有课程内容生成必须基于 input/course_spec.csv
priority: critical
---

# 源数据约束规则

本文档定义课程内容生成的源数据约束规则，是**最高优先级**的强制性要求。

---

## 一、核心约束

### 1.1 唯一可信源

⚠️ **input/course_spec.csv 是课程内容的唯一可信源**

> 解析器：`.claude/skills/spec-parser-skill/`（固定 Python，非 LLM）
> 入口：`ResourceParserAgent`（仅作触发与校验，不自己解析）
> 产物：`courses/{sheet}/{folder}/_meta/course-spec.yaml`

所有Agent生成课程内容时，必须：
1. 首先通过 ResourceParserAgent 触发 spec-parser-skill 解析 `input/course_spec.csv`
2. 基于解析后的课程规格（`course-spec.yaml`）生成内容
3. 不得仅凭通识知识或"想象"生成内容
4. 不得绕过 spec-parser-skill 直接读 csv 或手工编辑 `course-spec.yaml`

### 1.2 强制性要求

| 要求项 | 标准 | 检查方式 |
|-------|------|---------|
| 实验数量 | 必须≥资源列表要求 | ContentAuditAgent检查 |
| 总学时 | 必须=资源列表要求 | ContentAuditAgent检查 |
| 技术栈 | 必须覆盖资源列表要求 | ContentAuditAgent检查 |
| 实验内容 | 必须来自资源列表 | ResourceParserAgent解析 |

---

## 二、必须遵守的规则

### 2.1 禁止行为

❌ **严格禁止以下行为**：

1. **未读取资源列表就直接生成**
2. **随意减少实验数量或学时**
3. **忽略资源列表中的技术栈要求**
4. **自行臆造实验内容**

### 2.2 正确做法

✅ **正确的工作流程**：

```
1. 用户请求生成课程
   ↓
2. ResourceParserAgent读取资源列表.xlsx
   ↓
3. 生成course-spec.yaml（包含所有实验项目）
   ↓
4. KnowledgeGraphAgent基于course-spec生成知识图谱
   ↓
5. 其他Agent基于course-spec生成对应内容
   ↓
6. ContentAuditAgent审核是否符合资源列表
```

---

## 三、允许的扩展行为

### 3.1 专家级补充

✅ **允许基于专业判断补充前沿内容**

条件：
1. 资源列表中的内容已全部覆盖
2. 补充内容与课程主题相关
3. 补充内容有明确的行业价值
4. 必须标注为"专家建议"并说明理由

---

## 四、各Agent的执行约束

### 4.1 ResourceParserAgent
- 必须完整读取所有实验项目
- 必须准确解析实验名称、学时、内容
- 必须识别技术栈

### 4.2 KnowledgeGraphAgent
- 必须基于course-spec.yaml
- 每个实验至少对应1-2个知识点
- 知识图谱必须覆盖所有技术栈

### 4.3 SyllabusAgent
- 必须基于course-spec.yaml
- 总学时=course-spec中的total_hours
- 实验项目数≥course-spec中的实验数

### 4.4 LabGuideAgent
- 必须基于course-spec.yaml
- 每个实验必须来自course-spec
- 实验内容必须匹配objectives和contents

### 4.5 QuizAgent
- 必须基于knowledge-graph
- 知识点编号必须与知识图谱一致
- 必须读取实验指导书（lab_guide.md）：
  - **编程题强制**取材于实验指导书中的实际实验任务，使用相同 API/硬件接口，并标注关联实验编号
  - 单选/多选/简答题**可**参考实验指导书中的原理解释、操作要点作为素材
  - 禁止臆造与实验脱节的题目（如 ROS2 课程出 ROS1 API 题）
- 因依赖实验指导书，必须在 LabGuideAgent 之后执行

---

## 五、违规检测机制

### 5.1 ContentAuditAgent检查项
- [ ] 实验数量是否≥资源列表
- [ ] 总学时是否=资源列表
- [ ] 技术栈是否覆盖资源列表
- [ ] 实验内容是否来自资源列表

### 5.2 违规处理
| 违规级别 | 处理方式 |
|---------|---------|
| 🔴 严重违规 | 标记"不通过"，必须重做 |
| 🟡 一般违规 | 标记"待修改"，补充缺失内容 |
| 🟢 轻微违规 | 标记提示，允许继续 |

---

## 六、更新日志
| 日期 | 更新内容 |
|------|---------|
| 2026-06-11 | 初始版本 |
