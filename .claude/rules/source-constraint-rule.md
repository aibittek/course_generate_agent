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

## 三、无源码豁免协议（受控放行机制）

### 3.1 豁免场景

在以下**受控场景**下，允许在源码缺失的情况下生成课程内容：

1. **课程初创阶段**：源码尚未开发完成，但需要先行设计教学框架
2. **源码替代方案**：基于行业标准能力（如 ROS2 官方 API、OpenCV 标准接口）生成内容
3. **人工审核承诺**：承诺在源码到位后由 IncrementalUpdateAgent 核实并订正

### 3.2 豁免授权方式

⚠️ **豁免必须经过明确授权**，通过以下任一方式：

#### 方式1：对话授权（推荐）
用户在 Claude Code 对话中明确表示：
```
我知道没有源码，允许生成（或：继续、豁免、跳过源码检查）
```

#### 方式2：registry 配置授权
在 `source-codes/_registry.yaml` 中为实验添加 `human_waiver` 块：
```yaml
experiments:
  - experiment_id: 3
    code_status: missing
    human_waiver:
      approved: true
      approved_by: "用户对话确认"  # 或 "项目负责人姓名"
      approved_at: 2026-06-24
      reason: "暂无源码，基于ROS2标准能力生成，内容标注待源码核实"
```

### 3.3 豁免后的强制标注

✅ **豁免放行后，生成的内容必须在醒目位置标注**：

```markdown
> [⚠️ 待源码核实] 本实验代码基于 {技术栈} 标准能力设计，需对照实际源码核实接口与参数。
```

- 标注位置：实验指导书每个实验开头、练测题编程题题干/解析
- 版本标记：文档版本号保持 `v0.x` 草稿状态，待源码核实后升 `v1.0`

### 3.4 豁免的限制与责任

| 限制项 | 要求 |
|-------|------|
| 内容准确性 | 仅能基于公开文档、标准 API 生成，不得臆造私有接口 |
| 硬件能力 | 必须对齐 hardware-platform-spec.md，不得超出设备实际能力 |
| 后续义务 | 源码到位后，必须触发 IncrementalUpdateAgent 核实并移除豁免标注 |

❌ **豁免不等于放弃约束**：
- 仍需遵循 naming-convention、quality-standard 等其他规则
- ContentAuditAgent 仍会校验学时/数量/一致性（只是跳过源码落点检查）
- 豁免记录会保留在 generation-log.md，供人工审计

---

## 四、允许的扩展行为

### 4.1 专家级补充

✅ **允许基于专业判断补充前沿内容**

条件：
1. 资源列表中的内容已全部覆盖
2. 补充内容与课程主题相关
3. 补充内容有明确的行业价值
4. 必须标注为"专家建议"并说明理由

---

## 五、各Agent的执行约束

### 5.1 ResourceParserAgent
- 必须完整读取所有实验项目
- 必须准确解析实验名称、学时、内容
- 必须识别技术栈

### 5.2 KnowledgeGraphAgent
- 必须基于course-spec.yaml
- 每个实验至少对应1-2个知识点
- 知识图谱必须覆盖所有技术栈

### 5.3 SyllabusAgent
- 必须基于course-spec.yaml
- 总学时=course-spec中的total_hours
- 实验项目数≥course-spec中的实验数

### 5.4 LabGuideAgent
- 必须基于course-spec.yaml
- 每个实验必须来自course-spec
- 实验内容必须匹配objectives和contents

### 5.5 QuizAgent
- 必须基于knowledge-graph
- 知识点编号必须与知识图谱一致
- 必须读取实验指导书（lab_guide.md）：
  - **编程题强制**取材于实验指导书中的实际实验任务，使用相同 API/硬件接口，并标注关联实验编号
  - 单选/多选/简答题**可**参考实验指导书中的原理解释、操作要点作为素材
  - 禁止臆造与实验脱节的题目（如 ROS2 课程出 ROS1 API 题）
- 因依赖实验指导书，必须在 LabGuideAgent 之后执行

---

## 六、违规检测机制

### 6.1 ContentAuditAgent检查项
- [ ] 实验数量是否≥资源列表
- [ ] 总学时是否=资源列表
- [ ] 技术栈是否覆盖资源列表
- [ ] 实验内容是否来自资源列表

### 6.2 违规处理
| 违规级别 | 处理方式 |
|---------|---------|
| 🔴 严重违规 | 标记"不通过"，必须重做 |
| 🟡 一般违规 | 标记"待修改"，补充缺失内容 |
| 🟢 轻微违规 | 标记提示，允许继续 |

---

## 七、更新日志
| 日期 | 更新内容 |
|------|---------|
| 2026-06-11 | 初始版本 |
