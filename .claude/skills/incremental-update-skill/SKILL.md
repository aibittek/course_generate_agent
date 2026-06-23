---
name: incremental-update
description: 课程增量更新技能 - 支持 csv 差异同步 / 单实验 / 单章节的定向修改
trigger: /incremental-update, /update, --from-csv, 同步 csv, 更新实验, 重新生成实验, 修改章节
version: 1.1
---

# 课程增量更新技能

## 功能说明

支持在已生成课程资源的基础上，按以下任一粒度做定向修改和重新生成，无需全流程重跑：

1. **csv 差异驱动**（推荐入口，Phase 2 起）
2. 单个实验
3. 单个章节 / 小节
4. 单个知识点

底层依赖：

- `.claude/skills/spec-parser-skill/diff.py` — 计算 csv ↔ yaml 字段级 delta + 联动提示
- `.claude/skills/spec-parser-skill/parser.py` — 重新生成 spec.yaml
- `.claude/agents/incremental-update-agent.md` — 模式 0–3 的执行 Agent

## 使用场景

1. **csv 改动后同步课程**（最常见）：用户/team 编辑 `input/course_spec.csv`（增删实验、调学时、改技术栈），让所有下游文档自动跟进
2. **实验源码更新**：源码修改后重新生成实验内容
3. **实验内容调整**：优化实验步骤、补充原理讲解
4. **章节知识点调整**：补充或修改章节的知识点
5. **学时重新分配**：调整实验学时后同步更新文档

## 触发方式

### 方式1: 自然语言（推荐）

```
我改了 csv，请同步课程               # 走模式0（csv 差异驱动）
更新 EXP001 实验5                    # 走模式1（单实验）
重新生成 ROS机器人实践 实验3
修改 计算机视觉实践 第2章
```

### 方式2: 命令行

```bash
/incremental-update --from-csv                              # 模式0：csv 差异驱动
/incremental-update --course EXP001 --from-csv              # 模式0，限定一门课
/incremental-update --course EXP001 --experiment 5          # 模式1：单实验
/incremental-update --course EXP003 --chapter 2             # 模式2：单章节
```

### 方式3: Git Hook 自动触发

仓库根目录的 `.githooks/`（启用方式：`bash .githooks/install.sh`）会在 `git checkout` / `git pull` / `git commit` 时自动检测 csv 漂移并打印 `/incremental-update --from-csv` 指引。详见 `.githooks/README.md`。

## 执行流程

### 模式0：csv 差异驱动（v1.1 新增）

```
csv 修改 → diff.py 计算变更 → IncrementalUpdateAgent 按 cascade_hints 派发 →
  ├─ added[]    → 新增实验段（强制走源码HOOK）
  ├─ removed[]  → 删除实验段 + 修剪表项 + 清失效题
  ├─ modified[] → 字段级回放：
  │   ├─ source_code_path/objectives/exp_content 变 → 重跑源码分析 + 重写实验段
  │   ├─ hours 变 → 只同步 syllabus 学时表 + lab_guide 实验头
  │   └─ difficulty/experiment_type 变 → 只更 syllabus 项目表元数据
  └─ course-level → total_hours / tech_stack / prerequisites 等：
      重跑 syllabus / knowledge_graph 对应段落
→ ContentAuditAgent 一致性校验 → 输出更新摘要
```

## 支持的更新类型

| 更新类型 | 示例指令 | 说明 |
|---------|---------|------|
| 单实验更新 | `更新 EXP001 实验3` | 重新生成指定实验的内容 |
| 单章节更新 | `修改 EXP003 第2章` | 重新生成指定章节的知识点 |
| 单节更新 | `更新 EXP001 第1章第2节` | 重新生成指定小节 |
| 知识点微调 | `修改知识点 1.2.3` | 微调知识点描述 |

## 参数说明

### 必需参数

- `course_id`: 课程ID（EXP001-EXP007 或 IND001-IND004）
- `update_type`: 更新类型（experiment | chapter | section | knowledge_point）
- `target`: 目标标识（实验编号、章节编号等）

### 可选参数

- `reason`: 更新原因（用于更新日志）
- `skip_audit`: 跳过一致性检查（不推荐）

## 示例

### 示例1: 源码修改后重新生成实验

```
场景：修改了 EXP001 实验5的源码，需要重新生成实验指导内容

指令：更新 EXP001 实验5

执行步骤：
1. 检查 source-codes/exp05/ 的分析状态
2. 如未分析，触发 SourceCodeAnalysisAgent
3. 调用 LabGuideExperimentAgent 生成新内容
4. 定位 cv_practice_lab_guide.md 中实验5的位置
5. 替换内容，更新版本号 v0.2 → v0.3
6. 检查学时、知识点引用是否一致
7. 输出更新摘要
```

### 示例2: 调整实验学时

```
场景：实验3原定4学时，现调整为6学时

指令：更新 EXP001 实验3，学时调整为6h

执行步骤：
1. 更新 course-spec.yaml 中实验3的学时
2. 重新生成实验3内容（如需要）
3. 同步更新 syllabus.md 的学时分配表
4. 检查总学时是否一致
5. 输出更新摘要
```

### 示例3: 补充章节知识点

```
场景：第2章需要补充"ROS2 DDS通信原理"

指令：修改 EXP003 第2章，补充 DDS 通信原理

执行步骤：
1. 调用 KnowledgeGraphAgent（增量模式）
2. 在第2章插入新知识点 2.X.X
3. 更新 knowledge_graph.md
4. 检查关联的实验和题目
5. 提示用户同步更新相关内容
```

## 输出说明

### 成功输出

```yaml
✅ 增量更新完成

更新摘要:
  课程: EXP001 (计算机视觉实践)
  类型: 实验更新
  目标: 实验5
  
  变更文件:
    - cv_practice_lab_guide.md (v0.2 → v0.3)
      替换范围: L301-L450
    
  一致性检查:
    ✅ 学时总和: 52h (一致)
    ✅ 实验数量: 14个 (一致)
    ✅ 知识点引用: 无冲突
  
  建议操作:
    - quiz.md 中有2道题引用了实验5，建议检查题目是否需要更新
```

### 错误输出

```yaml
❌ 增量更新失败

错误: 实验5边界未找到
原因: cv_practice_lab_guide.md 中未找到 "## 实验5" 标记

建议:
  1. 检查文档格式是否正确
  2. 确认实验编号是否正确
  3. 如文档损坏，建议全量重新生成
```

## 注意事项

### ⚠️ 使用限制

1. **实验编号不可变更**：实验编号一旦确定不建议修改
2. **章节删除需全量重跑**：删除章节会影响编号，需全量重新生成
3. **大范围修改建议全量生成**：如修改超过3个章节，建议使用全量生成流程

### ✅ 最佳实践

1. **每次修改后运行一致性检查**
2. **定期全量验证**（建议每5次增量更新后）
3. **保持更新日志完整**
4. **源码修改前做好备份**

## 与全量生成的对比

| 对比项 | 增量更新 | 全量生成 |
|-------|---------|---------|
| 适用场景 | 小范围修改 | 新课程生成、大范围调整 |
| 执行时间 | 快（1-5分钟） | 慢（10-30分钟） |
| 影响范围 | 局部 | 全部 |
| 版本号变化 | 次版本+1 | 主版本可能变化 |
| 一致性保证 | 需人工确认 | 自动保证 |

## 技术实现

本 skill 调用 `IncrementalUpdateAgent`，该 agent 负责：

1. 解析更新范围
2. 调用对应的生成 agent（LabGuideExperimentAgent / KnowledgeGraphAgent 等）
3. 使用文档定位算法替换内容
4. 触发一致性检查
5. 更新版本号和日志

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-06-22 | 初始版本 |
