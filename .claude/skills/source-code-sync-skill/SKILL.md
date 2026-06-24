---
name: source-code-sync
description: 源码 → CSV 反向同步技能 — 当案例代码功能改变时，自动分析源码并生成 CSV 行的更新建议（覆盖 experiment_name / tech_stack / objectives / exp_content / hours 等字段），人工确认后写回 input/course_spec.csv，再触发增量更新链路同步下游文档。
trigger: /source-code-sync, 同步源码到csv, 源码同步, 检查源码与csv一致性, 案例代码改了
version: 1.0
last_updated: 2026-06-24
---

# 源码反向同步技能

## 功能说明

本 skill 解决一个关键问题：**当实验源码改变时，CSV 作为唯一可信源也必须更新**，否则下游知识图谱/大纲/实验指导书/题库会基于过时的 CSV 生成错误内容。

**典型场景**：
- 案例代码从"手部拖拽"重写为"手部姿态分类"，但 CSV 还是旧描述
- 源码新增了 scikit-learn 依赖，CSV 的 tech_stack 没跟上
- 源码主入口文件改名，CSV 的 source_code_path / main_entry 失效

## 与现有流程的关系

```
单向链路（已有）:
  CSV → spec.yaml → 知识图谱/大纲 → 实验指导书 → 题库
                       ↑
                   源码分析（只读补充）

闭环链路（本skill补全）:
  源码改变 → extract_capabilities.py 分析能力
          → suggest_csv_update.py 生成更新建议
          → 用户对话确认
          → apply_updates.py 写回 CSV
          → 触发 IncrementalUpdateAgent 模式0（已有）
          → 下游全链路同步
```

## 工具组成

| 文件 | 类型 | 功能 |
|-----|------|------|
| `extract_capabilities.py` | 确定性分析 | 解析源码：import → tech_stack；行数+依赖 → hours/difficulty 估算；主函数注释 → experiment_name 候选 |
| `suggest_csv_update.py` | 对比器 | 读 CSV 现值 vs 提取的能力，生成 old/new/reason/confidence 清单 |
| `apply_updates.py` | 写回器 | 应用确认的变更到 CSV，备份原文件，记录变更日志 |
| `SKILL.md` | 说明 | 本文档 |

## 触发方式

### 方式1：自然语言（推荐）
```
源码改了，检查 EXP001 实验4 的 CSV 是否需要更新
源码同步检查 EXP003 实验2
我改了 exp05 的代码，帮我更新 CSV
```

### 方式2：命令行
```bash
# 单实验同步检查
python .claude/skills/source-code-sync-skill/extract_capabilities.py \
  --course EXP001 --exp 4 \
  --source-path source-codes/exp04/

python .claude/skills/source-code-sync-skill/suggest_csv_update.py \
  --course EXP001 --exp 4 \
  --capabilities /tmp/exp04_capabilities.json \
  --format yaml

# 应用变更（人工确认后）
python .claude/skills/source-code-sync-skill/apply_updates.py \
  --course EXP001 --exp 4 \
  --suggestions /tmp/exp04_suggestions.yaml \
  --apply-fields experiment_name,tech_stack
```

## 执行流程

```
Step 1: 源码能力提取
  python extract_capabilities.py --course EXP001 --exp 4
  ├─ 扫描 source-codes/exp04/ 目录
  ├─ 解析 .py 文件的 import 语句 → tech_stack 候选
  ├─ 解析 requirements.txt → 精确依赖列表
  ├─ 提取主函数 docstring → experiment_name 候选
  ├─ 统计代码行数 + 依赖数 → hours 估算
  └─ 输出: capabilities.json

Step 2: 生成 CSV 更新建议
  python suggest_csv_update.py --capabilities capabilities.json
  ├─ 读取 input/course_spec.csv 对应行
  ├─ 字段级对比 + 置信度评估
  └─ 输出: suggestions.yaml（含 old/new/reason/confidence/cascade_impact）

Step 3: 展示给用户确认（Claude 在对话中）
  显示变更清单 → 用户选择应用哪些字段

Step 4: 应用到 CSV
  python apply_updates.py --apply-fields ...
  ├─ 备份原 CSV → input/course_spec.csv.bak.{timestamp}
  ├─ 写入新值
  └─ 记录到 _meta/csv-sync-log.md

Step 5: 触发增量更新（自动）
  python .claude/skills/spec-parser-skill/diff.py --course EXP001
  → 检测到变更 → 调用 IncrementalUpdateAgent 模式0
  → 同步 spec.yaml + 知识图谱/大纲/实验指导书/题库
```

## 字段提取规则

### experiment_name（实验名称）
优先级：
1. `_meta.yaml` 的 `experiment_name` 字段
2. `README.md` 第一个 H1 标题
3. 主入口文件 docstring 第一行
4. 文件名转换（`hand_gesture_classifier.py` → "手部姿态分类"）

### tech_stack（技术栈）
来源：
1. `requirements.txt`（精确版本）
2. `.py` 文件的 `import` 语句
3. `_meta.yaml` 的 `dependencies` 字段

去重 + 取领域识别词（如 `mediapipe`, `opencv`, `torch` 这类）。

### objectives（实验目标）
**保留 LLM 生成位置**（本 skill 仅生成"建议保持不变 / 需要重写"标记，由 Claude 在对话中调用 LLM 重写）。

### hours（学时）
估算公式：
```python
score = (lines / 50) + (dep_count * 0.5) + (algorithm_complexity * 2)
hours = max(2, min(8, round(score / 2)))  # 映射到 2-8h
```

### difficulty（难度 1-3）
- `1` 验证性：代码 < 100 行，无循环嵌套，仅调用现成 API
- `2` 设计性：100-300 行，含算法实现或参数调优
- `3` 综合性：> 300 行，多模块组合或包含模型训练

### experiment_type
基于 difficulty + 关键词：
- 含 "训练" / "标注" → 综合性
- 含 "调优" / "实现" → 设计性
- 仅"运行" / "演示" → 验证性

## 输出格式

### capabilities.json
```json
{
  "course_id": "EXP001",
  "experiment_id": 4,
  "extracted_at": "2026-06-24T10:00:00",
  "experiment_name_candidates": [
    {"value": "基于MediaPipe的手部姿态分类实验", "source": "main.py docstring", "confidence": 0.9},
    {"value": "手部姿态分类", "source": "filename", "confidence": 0.6}
  ],
  "tech_stack": ["MediaPipe", "OpenCV", "scikit-learn", "NumPy"],
  "tech_stack_source": "requirements.txt + import",
  "main_entry": "main.py",
  "estimated_hours": 4,
  "estimated_difficulty": 2,
  "estimated_experiment_type": "设计性",
  "metrics": {
    "total_lines": 245,
    "function_count": 8,
    "import_count": 12,
    "dep_count": 5
  },
  "key_functions": [
    {"name": "classify_gesture", "doc": "对21个手部关键点进行 SVM 分类"},
    {"name": "extract_features", "doc": "提取手部姿态特征向量"}
  ]
}
```

### suggestions.yaml
```yaml
course_id: EXP001
experiment_id: 4
suggestions:
  - field: experiment_name
    csv_old: "基于MediaPipe的指尖轨迹识别实验"
    code_new: "基于MediaPipe的手部姿态分类实验"
    confidence: 0.9
    reason: "源码主函数从 track_fingertip 改为 classify_gesture"
    cascade_impact:
      - "knowledge_graph 第3章节标题需更新"
      - "lab_guide 实验4标题需更新"
  - field: tech_stack
    csv_old: ["MediaPipe", "OpenCV"]
    code_new: ["MediaPipe", "OpenCV", "scikit-learn", "NumPy"]
    confidence: 0.95
    reason: "requirements.txt 新增 scikit-learn==1.3.0, numpy==1.24.3"
    cascade_impact:
      - "knowledge_graph 需补充 scikit-learn 相关节点"
  - field: objectives
    csv_old: "掌握手部关键点检测算法原理;能够实现实时指尖坐标提取..."
    code_new: "[需 LLM 重写] 源码核心功能从轨迹识别变为姿态分类"
    confidence: 0.4
    reason: "objectives 是多句教学目标，建议由 Claude 在对话中调用 LLM 基于源码重写"
```

## 限制与边界

### 当前实现（v1.0）
✅ 可确定性提取：
- tech_stack（来自 requirements.txt + import）
- hours / difficulty / experiment_type（来自代码量+复杂度启发式）
- main_entry / source_code_path（来自目录扫描）

⚠️ 标记需 LLM 协作：
- experiment_name（候选项 + 置信度，由 Claude 选择）
- objectives / exp_content（仅给"需重写"信号，Claude 在对话中调 LLM）

❌ 不支持：
- 跨文件复杂语义分析（如"算法是否变了"）
- 自动修改 prerequisites（前置课程）

### v2.0 规划
- 集成 source-code-analysis-agent，复用其原理提取能力
- objectives 自动重写（Prompt + few-shot）
- 跨实验依赖检测（实验5依赖实验4，实验4变了要提醒）

## 与其他 skill 的协作

| Skill | 协作方式 |
|------|---------|
| spec-parser-skill | 应用 CSV 变更后，复用其 parser.py 重新生成 spec.yaml |
| spec-parser-skill (diff.py) | 应用变更后调用，识别字段级 delta |
| incremental-update-skill | 接收 diff 结果，按 cascade_hints 同步下游文档 |
| source-code-hook-skill | 互补关系：hook 是"源码缺失就阻塞"，本 skill 是"源码变了就同步" |

## 安全保障

1. **CSV 备份**：每次写入前自动备份到 `input/course_spec.csv.bak.{timestamp}`
2. **字段白名单**：`apply_updates.py --apply-fields` 必须显式指定，不接受 `--all`
3. **变更日志**：所有应用的变更记录到 `courses/{folder}/_meta/csv-sync-log.md`
4. **置信度阈值**：confidence < 0.7 的建议在 CLI 输出醒目警告

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-06-24 | 初始版本：实现 extract_capabilities.py + suggest_csv_update.py + apply_updates.py 三件套 |
