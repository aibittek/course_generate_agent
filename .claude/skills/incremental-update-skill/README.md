# 增量更新系统使用指南

本文档介绍如何使用课程资源增量更新系统进行单章节/单实验的定向修改。

---

## 系统组成

### 1. 核心组件

| 组件 | 路径 | 功能 |
|------|------|------|
| IncrementalUpdateAgent | `.claude/agents/incremental-update-agent.md` | 增量更新管理器 |
| incremental-update-skill | `.claude/skills/incremental-update-skill/` | 用户接口技能 |
| document_replacer.py | `.claude/skills/incremental-update-skill/document_replacer.py` | 文档替换工具 |
| test_simple.py | `.claude/skills/incremental-update-skill/test_simple.py` | 功能验证脚本 |

### 2. 功能验证

```bash
# 运行测试验证所有功能正常
cd .claude/skills/incremental-update-skill
python test_simple.py
```

预期输出：
```
[SUCCESS] All tests passed!
Passed: 4/4
```

---

## 使用场景

### 场景1: 实验源码更新后重新生成

**问题**: 实验5的源码使用了新的API，需要重新生成实验内容

**解决方案**:
```
指令: 更新 EXP001 实验5
```

系统自动：
1. 检查源码分析状态
2. 如需要，触发 SourceCodeAnalysisAgent
3. 调用 LabGuideExperimentAgent 生成新内容
4. 定位并替换 lab_guide.md 中的实验5段落
5. 更新版本号
6. 运行一致性检查

### 场景2: 实验学时调整

**问题**: 实验3学时从4h调整为6h

**解决方案**:
```
指令: 更新 EXP001 实验3，学时调整为6h
```

系统自动：
1. 更新 course-spec.yaml
2. 重新生成实验3内容（如需要）
3. 同步更新 syllabus.md 的学时分配表
4. 检查总学时一致性
5. 提示连锁影响

### 场景3: 章节知识点补充

**问题**: 第2章需要补充新知识点

**解决方案**:
```
指令: 修改 EXP003 第2章，补充 DDS 通信原理
```

系统自动：
1. 调用 KnowledgeGraphAgent（增量模式）
2. 在第2章插入新知识点
3. 更新 knowledge_graph.md
4. 检查关联实验和题目
5. 提示同步更新建议

---

## 两种使用方式

### 方式1: 自然语言（推荐）

直接告诉 Claude Code 你想做什么：

```
更新 EXP001 实验5
重新生成 机器人ROS2应用与开发 实验3
修改 机器人视觉应用与开发 第2章
```

Claude Code 会：
- 解析你的意图
- 调用 IncrementalUpdateAgent
- 自动执行完整流程
- 输出更新摘要

### 方式2: 直接使用工具（高级）

如果只需要替换文档，可以直接使用 Python 工具：

```bash
python .claude/skills/incremental-update-skill/document_replacer.py \
  courses/sheet1/cv_practice/cv_practice_lab_guide.md \
  experiment \
  5 \
  courses/sheet1/cv_practice/_parts/experiment-5.md
```

这会：
- 定位实验5边界
- 替换内容
- 更新版本号
- 追加更新日志
- 创建备份

---

## 输出说明

### 成功输出示例

```yaml
[IncrementalUpdateAgent] 增量更新完成

更新摘要:
  课程: EXP001 (机器人视觉应用与开发)
  类型: 实验更新
  目标: 实验5 - YOLOv8目标检测实验
  
  变更文件:
    - cv_practice_lab_guide.md (v0.2 → v0.3)
      替换范围: L301-L450
      备份路径: cv_practice_lab_guide.md.bak
    
  一致性检查:
    学时总和: 52h (一致)
    实验数量: 14个 (一致)
    知识点引用: 正常
  
  建议操作:
    [WARN] quiz.md 中有2道编程题引用了实验5
           建议检查题目是否需要更新
```

### 错误输出示例

```yaml
[IncrementalUpdateAgent] 增量更新失败

错误: 实验5边界未找到
原因: cv_practice_lab_guide.md 中未找到 "## 实验5" 标记

建议:
  1. 检查文档格式是否正确
  2. 确认实验编号是否正确
  3. 如文档损坏，建议全量重新生成
```

---

## 与全量生成的对比

| 对比项 | 增量更新 | 全量生成 |
|-------|---------|---------|
| 适用场景 | 单实验/章节修改 | 新课程、大范围调整 |
| 执行时间 | 1-5分钟 | 10-30分钟 |
| 影响范围 | 局部 | 全部文档 |
| 版本号变化 | 次版本+1 (v0.2→v0.3) | 可能主版本变化 |
| 一致性保证 | 需人工确认连锁影响 | 自动保证 |
| 源码分析 | 仅更新的实验 | 所有实验 |

**选择建议**:
- 修改≤3个实验 → 增量更新
- 修改章节结构、实验编号 → 全量重新生成
- 新增/删除章节 → 全量重新生成
- 定期全量验证（每5次增量更新后）

---

## 限制与注意事项

### 当前限制

1. **实验编号不可变更**  
   实验编号一旦确定不建议修改，否则需要全量重新生成

2. **章节删除需全量重跑**  
   删除章节会影响编号，必须全量重新生成

3. **知识点自动同步有限**  
   修改知识点后，系统只提示哪些内容需要同步，不会自动更新所有引用

### 最佳实践

1. **更新前备份**
   ```bash
   cp lab_guide.md lab_guide.md.backup
   ```

2. **小步迭代**
   - 每次只更新一个实验或章节
   - 更新后立即验证
   - 确认无误后再继续

3. **使用版本控制**
   ```bash
   git add courses/sheet1/cv_practice/
   git commit -m "更新实验5: YOLOv8 API升级"
   ```

4. **定期全量验证**
   ```
   # 每5次增量更新后，运行全量一致性检查
   调用 ContentAuditAgent
   ```

---

## 故障排查

### 问题1: 实验边界未找到

**症状**: `[FAIL] 实验5边界未找到`

**原因**:
- 文档中没有 "## 实验5" 标记
- 标题格式不标准（如缺少空格）
- 实验编号不连续

**解决**:
```bash
# 检查文档结构
grep "## 实验" courses/sheet1/cv_practice/cv_practice_lab_guide.md

# 手动修正标题格式，确保:
# - "##" 后有空格
# - 实验编号连续
```

### 问题2: 源码分析超时

**症状**: `[ERROR] 源码分析超时`

**原因**:
- 源码文件过大
- 源码包含语法错误
- 源码路径不正确

**解决**:
```bash
# 检查源码路径
ls -la courses/sheet1/cv_practice/source-codes/exp05/

# 检查分析状态
cat courses/sheet1/cv_practice/source-codes/exp05/code-analysis/analysis-status.yaml

# 如果状态异常，手动重置
```

### 问题3: 一致性检查失败

**症状**: `[WARN] 学时总和不一致: 52h (期望) vs 54h (实际)`

**原因**:
- 修改了实验学时但未同步更新其他文档
- 学时分配表计算错误

**解决**:
```bash
# 检查所有实验的学时
grep "学时:" courses/sheet1/cv_practice/cv_practice_lab_guide.md | awk -F: '{sum+=$2} END {print sum "h"}'

# 同步更新所有文档中的总学时标注
# - course-spec.yaml
# - syllabus.md
# - knowledge_graph.md
# - README.md
```

---

## 技术架构

### 执行流程

```
用户指令
    ↓
IncrementalUpdateAgent 解析
    ↓
检查源码状态
    ↓
调用生成 Agent
  ├─ LabGuideExperimentAgent (实验)
  ├─ KnowledgeGraphAgent (章节)
  └─ SyllabusAgent (大纲)
    ↓
document_replacer.py 定位替换
    ↓
一致性检查 (ContentAuditAgent)
    ↓
输出更新摘要
```

### 文档定位算法

**实验定位**:
- 起始: `## 实验{N}`
- 结束: `## 实验{N+1}` 或 `## 附录` 或文档末尾

**章节定位**:
- 起始: `## 第{N}章`
- 结束: `## 第{N+1}章` 或文档末尾

**版本更新规则**:
- 实验内容修改 → 次版本+1 (v0.2 → v0.3)
- 章节结构调整 → 主版本+1 (v0.9 → v1.0)

---

## 快速参考

### 常用指令

```bash
# 更新单个实验
更新 EXP001 实验5

# 更新章节
修改 EXP003 第2章

# 调整学时
更新 EXP001 实验3，学时调整为6h

# 直接使用工具
python .claude/skills/incremental-update-skill/document_replacer.py \
  <doc_path> experiment <id> <new_content_path>

# 运行测试
cd .claude/skills/incremental-update-skill
python test_simple.py
```

### 文件路径约定

```
courses/sheet1/{course_id}/
├── {course_id}_lab_guide.md          # 实验指导书（替换目标）
├── {course_id}_knowledge_graph.md    # 知识图谱（替换目标）
├── {course_id}_syllabus.md           # 教学大纲（替换目标）
├── {course_id}_quiz.md               # 练测题库（检查引用）
├── _parts/                            # 生成的部分内容
│   └── experiment-{N}.md
└── source-codes/
    └── exp{NN}/
        └── code-analysis/
            ├── code-analysis-report.md
            └── analysis-status.yaml
```

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-06-22 | v1.0 | 初始版本，支持实验/章节/知识点增量更新 |
| 2026-06-22 | v1.0 | 功能测试通过，文档定位/替换/版本更新正常 |

---

## 相关文档

- `.claude/agents/incremental-update-agent.md` - Agent 详细说明
- `.claude/skills/incremental-update-skill/SKILL.md` - Skill 使用说明
- `.claude/skills/incremental-update-skill/EXAMPLES.md` - 使用场景示例
- `.claude/workflows/course-generation-workflow.md` - 全量生成流程
