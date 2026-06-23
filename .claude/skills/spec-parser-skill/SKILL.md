---
name: spec-parser-skill
description: course_spec.csv → course-spec.yaml 的固定解析器。所有需要将唯一可信源（CSV）转为标准 spec 时调用此技能。提供字段校验、源码路径解析、列表字段拆分等能力。
trigger: 解析课程规格、parse course spec、生成 course-spec.yaml、校验 course_spec.csv
---

# 课程规格解析技能

将 `input/course_spec.csv` 解析为 `courses/{sheet}/{folder}/_meta/course-spec.yaml`，作为后续所有 Agent 的唯一可信输入。

---

## 一、为什么是固定解析器（不是 LLM 解析）

| 维度 | LLM 解析（旧） | 固定 Python 解析（新） |
|-----|--------------|----------------------|
| 一致性 | 每次结果可能漂移 | 同输入永远同输出 |
| 速度 | 秒级 | 毫秒级 |
| 可调试 | 黑盒 | 抛出明确异常 |
| 字段校验 | 易遗漏 | 强制规则约束 |
| Token 消耗 | 高 | 0 |

CSV → YAML 是**确定性映射**，不应该让模型"理解"，应该让代码"翻译"。

---

## 二、文件清单

| 文件 | 作用 |
|------|------|
| `parser.py` | CSV → YAML 主解析器，CLI 可执行；输出含 `_source` 水印（csv 路径 + sha256 + parsed_at） |
| `validator.py` | spec 字段校验，输出 errors/warnings |
| `diff.py` | 比较 csv 新解析结果 vs 现有 yaml，输出实验级 add/remove/modify + 课程级字段 diff + 下游联动提示 |
| `schema.yaml` | 字段定义（required/type/pattern/enum） |
| `SKILL.md` | 本文档 |

---

## 三、CSV 设计

### 3.1 多课程共存（v2.0）

```
course_id, course_name, sheet, folder, total_hours, ...,
experiment_id, experiment_name, hours, difficulty, source_code_path, ...
```

`input/course_spec.csv` 包含全部 11 门课程（EXP001-EXP007, IND001-IND004），共 61 个实验。每行 = 一个实验。课程级字段在每行重复（解析时去重并校验冲突）。

**⚠️ 多课程 CSV 约定**：调用 parser/validator/diff 时**必须传 `--course <course_id>` 参数**，否则会因 `course_id` 不一致而报错。

### 3.2 列表字段约定

CSV 单元格内的列表用 `;`（半角分号）分隔：

```csv
tech_stack: "OpenCV;MediaPipe;YOLOv8"
exp_content: "采集图像;转换Lab;阈值分割;形态学运算"
```

### 3.3 源码路径解析策略（核心）

`source_code_path` 列：

1. **显式优先**：列非空 → 直接使用（如 `source-codes/exp04/`）
2. **约定推导**：列为空 → 自动按 `source-codes/exp{NN}/` 生成（NN 为两位数）

这种"显式 + 约定"混合策略让常规情况零配置，特殊情况可覆盖。

---

## 四、调用方式

### 4.1 命令行

```bash
# 解析（v2.0 必须指定课程）
python .claude/skills/spec-parser-skill/parser.py --course EXP001
python .claude/skills/spec-parser-skill/parser.py --course IND001

# 指定输入输出
python .claude/skills/spec-parser-skill/parser.py --course EXP001 \
  input/course_spec.csv -o output/spec.yaml

# 仅校验（不写文件）
python .claude/skills/spec-parser-skill/parser.py --course EXP001 --validate-only

# 字段校验（含源码路径存在性）
python .claude/skills/spec-parser-skill/validator.py --course EXP001
python .claude/skills/spec-parser-skill/validator.py --course EXP001 --no-path-check

# csv 与现有 yaml 的 diff（增量更新触发器，exit 1 = 有变化）
python .claude/skills/spec-parser-skill/diff.py --course EXP001
python .claude/skills/spec-parser-skill/diff.py --course EXP001 --format json
python .claude/skills/spec-parser-skill/diff.py --course EXP001 \
  -y path/to/old.yaml --format json
```

### 4.2 Python 调用

```python
import sys
from pathlib import Path

sys.path.insert(0, ".claude/skills/spec-parser-skill")
from parser import parse_csv_to_dict, dump_yaml
from validator import validate_spec

# v2.0: 必须传 course_id 参数
spec = parse_csv_to_dict(Path("input/course_spec.csv"), course_id="EXP001")
errors, warnings = validate_spec(spec)
if errors:
    raise RuntimeError(f"校验失败: {errors}")

yaml_text = dump_yaml(spec)
Path("courses/sheet1/cv_practice/_meta/course-spec.yaml").write_text(
    yaml_text, encoding="utf-8"
)
```

---

## 五、输出格式

与现有 `course-spec.yaml` 字段保持兼容，新增以下字段：

- 实验级新增：`experiment_id`（数字）、`difficulty`、`difficulty_stars`、
  `experiment_type`、`source_code_path`、`main_entry`、
  `knowledge_points`、`objectives`、`exp_content`、`notes`
- 课程级新增：`folder`、`theory_hours`、`lab_hours`

旧字段保留：`course_code`、`course_name`、`category`、
`prerequisites`、`total_hours`、`experiment_count`、`tech_stack`、
`hardware`、`description`、`experiments[]`。

---

## 六、何时调用

| 场景 | 调用者 | 工具 |
|------|-------|------|
| 全量课程生成 Step 1 | ResourceParserAgent | parser.py + validator.py |
| 仅修改 CSV 后重生成 spec | 用户手动 / Git Hook | parser.py |
| **增量更新前的差异分析** | **IncrementalUpdateAgent** | **diff.py** |
| CI 校验 | 自动化脚本 | validator.py / diff.py |

---

## 六-A、diff.py 详解（Phase 2 新增）

### 用途

让"csv 改了什么 → 哪些下游文档需要重做"成为**可检测、可机器读**的判定，而非依靠人工记忆或全量重跑。

### 输出 schema

```jsonc
{
  "course_changed": true,
  "course_changes": {
    "total_hours": {"old": 52, "new": 56}
  },
  "experiments": {
    "added":    [{"experiment_id": 15, "name": "新增实验"}],
    "removed":  [{"experiment_id": 7,  "name": "已删除的实验"}],
    "modified": [
      {
        "experiment_id": 4,
        "fields": {
          "hours":      {"old": 4, "new": 6},
          "objectives": {"old": [...], "new": [...]}
        }
      }
    ]
  },
  "cascade_hints": {
    "lab_guide":       ["实验15 新增 → 触发源码HOOK + LabGuideExperimentAgent", ...],
    "syllabus":        ["实验15 新增 → 补入实验项目表", ...],
    "quiz":            ["实验15 新增 → 编程题取材域扩展，需补题", ...],
    "knowledge_graph": [...]
  },
  "summary": {
    "course_field_count": 1,
    "added_count": 1, "removed_count": 1, "modified_count": 1,
    "total_changed_experiments": 3
  }
}
```

### 字段级 diff 粒度（让 IncrementalUpdateAgent 决定回放范围）

| 字段类别 | 字段 | 比较语义 |
|---------|------|---------|
| 实验标量 | `name` `hours` `difficulty` `difficulty_stars` `experiment_type` `source_code_path` `main_entry` `notes` | 等值；`""` 与 None 等价 |
| 实验列表 | `objectives` `exp_content` `knowledge_points` | 集合相等（顺序无关） |
| 课程标量 | `course_code` `course_name` `category` `folder` `total_hours` `theory_hours` `lab_hours` `hardware` `description` `experiment_count` | 等值；`""` 与 None 等价 |
| 课程列表 | `tech_stack` `prerequisites` | 集合相等 |
| **忽略** | `_source.*`（水印） | diff 时跳过 |

### 联动规则（cascade_hints 推导逻辑）

| diff 信号 | 触发的文档 | 原因 |
|----------|-----------|------|
| `course.total_hours/lab_hours/theory_hours` | syllabus | 学时分配表需重排 |
| `course.tech_stack` | knowledge_graph / quiz | 知识点覆盖与题库覆盖 |
| `course.prerequisites` | syllabus | 先修说明 |
| `course.experiment_count` | lab_guide / syllabus | 实验数变化 |
| 实验 added | lab_guide / syllabus / quiz | 需新建段落、表项、补题 |
| 实验 removed | lab_guide / syllabus / quiz | 需删段、修剪、清失效题 |
| 实验 modified: `objectives/exp_content/name` | lab_guide | 该实验段落重写（**强制走源码HOOK**） |
| 实验 modified: `hours` | syllabus / lab_guide 头部 | 学时同步 |
| 实验 modified: `source_code_path/main_entry` | lab_guide | **必须重跑源码分析**（HOOK强制） |
| 实验 modified: `experiment_type/difficulty` | syllabus | 项目表元数据更新 |

### 退出码（CI/Hook 友好）

| 退出码 | 含义 |
|-------|------|
| 0 | 无变化（spec 与 csv 一致） |
| 1 | 有变化（推荐配合 `--format json` 喂给 IncrementalUpdateAgent） |
| 2 | csv 解析失败 |

### Python 调用

```python
import sys
from pathlib import Path
sys.path.insert(0, ".claude/skills/spec-parser-skill")
from diff import diff_csv_against_yaml

# v2.0: 必须传 course_id 参数
d = diff_csv_against_yaml(
    Path("input/course_spec.csv"),
    Path("courses/sheet1/cv_practice/_meta/course-spec.yaml"),
    course_id="EXP001"
)
if d["summary"]["total_changed_experiments"] > 0:
    print("需走增量更新流程")
```

---

## 七、错误处理

| 错误类型 | 解析器行为 |
|---------|-----------|
| CSV 不存在 | `FileNotFoundError` |
| 课程级字段在多行不一致 | `ValueError("course_id 在多行中不一致")` |
| `experiment_id` 重复 | `ValueError("experiment_id 重复: [...]")` |
| 必填字段缺失 | `ValueError("...必填")` |
| 类型转换失败 | `ValueError("...必须是整数")` |

校验器（`validator.py`）输出 `errors` / `warnings`：
- **errors**：阻塞，必须修复
- **warnings**：提示，可继续

---

## 八、扩展指引

### 8.1 新增字段

1. 在 `schema.yaml` 中声明字段
2. 在 `parser.py::_parse_experiment` 或 `_build_course_meta` 加映射
3. 在 `parser.py::dump_yaml` 添加输出
4. 在 `validator.py` 加校验规则

### 8.2 多课程批量生成

v2.0 已支持多课程 CSV。批量生成所有课程：

```bash
for course_id in EXP001 EXP002 EXP003 EXP004 EXP005 EXP006 EXP007 IND001 IND002 IND003 IND004; do
  python .claude/skills/spec-parser-skill/parser.py --course $course_id
done
```

或通过主控 Agent（CourseResourceOrchestrator）循环调用。

---

## 九、与其他规则的关系

- 服从 `.claude/rules/source-constraint-rule.md` ── CSV 是唯一可信源
- 服从 `.claude/rules/data-consistency-rule.md` ── 校验学时/数量一致性
- 与 `.claude/skills/source-code-hook-skill/` 协作：本技能产出 `source_code_path`，HOOK 校验路径下的源码分析状态
