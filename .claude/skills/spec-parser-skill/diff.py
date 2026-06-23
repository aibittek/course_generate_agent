"""
spec-parser-skill: diff

比较 csv 解析得到的新 spec 与磁盘上现有 course-spec.yaml，输出结构化变更：
  - course_changed: 课程级字段是否变化
  - experiments.added / removed / modified

被 IncrementalUpdateAgent 用作 "csv 改了哪些 → 哪些下游需要重做" 的判定依据。

设计要点：
  - 不依赖外部库；自带极简 yaml 读取（只支持本 skill 输出的格式）
  - 比较时忽略 _source 水印（那是 parser 自己加的，不是用户编辑的内容）
  - 字段级 diff 让下游能按字段力度做最小更新（如只学时变了 → 只重排 syllabus）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 实验级字段中，列表类（顺序无关）
LIST_FIELDS = {"objectives", "exp_content", "knowledge_points"}
# 实验级字段中，标量类
SCALAR_FIELDS = {
    "name", "hours", "difficulty", "difficulty_stars",
    "experiment_type", "source_code_path", "main_entry", "notes",
}
# 课程级需要 diff 的字段
COURSE_FIELDS = {
    "course_code", "course_name", "category", "folder",
    "total_hours", "theory_hours", "lab_hours",
    "tech_stack", "prerequisites", "hardware", "description",
    "experiment_count",
}
# 列表类的课程级字段（顺序无关）
COURSE_LIST_FIELDS = {"tech_stack", "prerequisites"}


# ---------- 极简 YAML 反序列化（仅识别本 skill 自身输出的结构） ----------

def _strip_quotes(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        return v[1:-1]
    return v


def _coerce(v: str) -> Any:
    s = _strip_quotes(v)
    if s == "":
        return ""
    if s.lstrip("-").isdigit():
        try:
            return int(s)
        except ValueError:
            return s
    return s


def load_yaml(path: Path) -> dict[str, Any]:
    """
    极简 yaml 解析，仅满足本 skill 自身写出的格式：
      - indent=0: 顶层 key 或 顶层列表 key
      - indent=2: 顶层列表项（"  - x"）或 experiments 项首行（"  - id: expNN"）
      - indent=4: experiments[] 内字段
      - indent=6: experiments[] 内列表项
      - 块标量 description: |
    为避免引入 PyYAML 依赖。
    """
    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    root: dict[str, Any] = {}
    experiments: list[dict[str, Any]] = []
    current_exp: dict[str, Any] | None = None
    current_exp_list_key: str | None = None
    current_top_list_key: str | None = None
    in_description_block = False
    description_lines: list[str] = []

    def _commit_description():
        nonlocal in_description_block, description_lines
        if in_description_block:
            root["description"] = "\n".join(description_lines).rstrip("\n")
            in_description_block = False
            description_lines = []

    for raw in lines:
        if not raw.strip():
            _commit_description()
            continue

        # 块标量正文
        if in_description_block and raw.startswith("  "):
            description_lines.append(raw[2:])
            continue
        elif in_description_block:
            _commit_description()

        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        # _source 段：跳过水印
        if indent == 0 and line.startswith("_source:"):
            if current_exp is not None:
                experiments.append(current_exp)
                current_exp = None
            current_exp_list_key = None
            current_top_list_key = None
            root["__skip_source__"] = True
            continue
        if root.get("__skip_source__") and indent > 0:
            continue
        if root.get("__skip_source__") and indent == 0:
            root.pop("__skip_source__")

        # ---------- indent 0: 顶层 ----------
        if indent == 0:
            current_exp = None
            current_exp_list_key = None
            if line == "experiments:":
                current_top_list_key = "__experiments__"
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                k = k.strip()
                v_stripped = v.strip()
                if v_stripped == "":
                    current_top_list_key = k
                    root[k] = []
                elif v_stripped == "|":
                    in_description_block = True
                    description_lines = []
                    current_top_list_key = None
                else:
                    root[k] = _coerce(v)
                    current_top_list_key = None
            continue

        # ---------- indent 2: 顶层列表项 / experiments[] 首行 ----------
        if indent == 2 and line.startswith("- "):
            payload = line[2:]
            if current_top_list_key == "__experiments__":
                if current_exp is not None:
                    experiments.append(current_exp)
                current_exp = {}
                current_exp_list_key = None
                if ":" in payload:
                    k, _, v = payload.partition(":")
                    current_exp[k.strip()] = _coerce(v)
            elif current_top_list_key:
                root[current_top_list_key].append(_strip_quotes(payload))
            continue

        # ---------- indent 4: experiments[] 内字段 ----------
        if indent == 4 and current_exp is not None and ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v_stripped = v.strip()
            if v_stripped == "":
                current_exp_list_key = k
                current_exp[k] = []
            else:
                current_exp[k] = _coerce(v)
                current_exp_list_key = None
            continue

        # ---------- indent 6: experiments[] 列表项 ----------
        if indent == 6 and current_exp is not None \
                and current_exp_list_key and line.startswith("- "):
            current_exp[current_exp_list_key].append(_strip_quotes(line[2:]))
            continue

    _commit_description()
    if current_exp is not None:
        experiments.append(current_exp)

    if experiments:
        root["experiments"] = experiments

    root.pop("__skip_source__", None)
    return root


# ---------- diff 主体 ----------

def _index_by_id(experiments: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    idx: dict[int, dict[str, Any]] = {}
    for exp in experiments or []:
        eid = exp.get("experiment_id")
        if isinstance(eid, str) and eid.isdigit():
            eid = int(eid)
        if isinstance(eid, int):
            idx[eid] = exp
    return idx


def _norm_scalar(v: Any) -> Any:
    """空字符串、None、缺失 → 统一为 None；用于 diff 时忽略 'optional 字段未填' 与 'optional 字段填空' 的差异。"""
    if v is None or v == "":
        return None
    return v


def _list_eq(a: Any, b: Any) -> bool:
    """列表字段：顺序无关比较；其他保持等值比较。"""
    if isinstance(a, list) and isinstance(b, list):
        return sorted(map(str, a)) == sorted(map(str, b))
    return a == b


def _diff_experiment(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    field_changes: dict[str, dict[str, Any]] = {}

    for f in SCALAR_FIELDS:
        ov, nv = _norm_scalar(old.get(f)), _norm_scalar(new.get(f))
        if ov != nv:
            field_changes[f] = {"old": ov, "new": nv}

    for f in LIST_FIELDS:
        ov, nv = old.get(f) or [], new.get(f) or []
        if not _list_eq(ov, nv):
            field_changes[f] = {"old": ov, "new": nv}

    return field_changes


def _diff_course(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    changes: dict[str, dict[str, Any]] = {}
    for f in COURSE_FIELDS:
        ov, nv = old.get(f), new.get(f)
        if f in COURSE_LIST_FIELDS:
            if not _list_eq(ov or [], nv or []):
                changes[f] = {"old": ov, "new": nv}
        else:
            if _norm_scalar(ov) != _norm_scalar(nv):
                changes[f] = {"old": ov, "new": nv}
    return changes


def diff_specs(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """计算 old → new 的结构化 diff。"""
    course_changes = _diff_course(old, new)

    old_idx = _index_by_id(old.get("experiments") or [])
    new_idx = _index_by_id(new.get("experiments") or [])

    added = sorted(set(new_idx) - set(old_idx))
    removed = sorted(set(old_idx) - set(new_idx))
    modified: dict[int, dict[str, Any]] = {}

    for eid in sorted(set(old_idx) & set(new_idx)):
        delta = _diff_experiment(old_idx[eid], new_idx[eid])
        if delta:
            modified[eid] = delta

    cascade = _infer_cascade(course_changes, added, removed, modified)

    return {
        "course_changed": bool(course_changes),
        "course_changes": course_changes,
        "experiments": {
            "added": [
                {"experiment_id": eid, "name": new_idx[eid].get("name")} for eid in added
            ],
            "removed": [
                {"experiment_id": eid, "name": old_idx[eid].get("name")} for eid in removed
            ],
            "modified": [
                {"experiment_id": eid, "fields": delta} for eid, delta in modified.items()
            ],
        },
        "cascade_hints": cascade,
        "summary": {
            "course_field_count": len(course_changes),
            "added_count": len(added),
            "removed_count": len(removed),
            "modified_count": len(modified),
            "total_changed_experiments": len(added) + len(removed) + len(modified),
        },
    }


def _infer_cascade(
    course_changes: dict[str, Any],
    added: list[int],
    removed: list[int],
    modified: dict[int, dict[str, Any]],
) -> dict[str, list[str]]:
    """
    根据 diff 结果，提示哪些下游文档需要联动重做。
    粒度：文档级（lab_guide / syllabus / knowledge_graph / quiz）。
    """
    affected: dict[str, set[str]] = {
        "lab_guide": set(),
        "syllabus": set(),
        "knowledge_graph": set(),
        "quiz": set(),
    }

    # 课程级字段
    if "total_hours" in course_changes or "lab_hours" in course_changes \
            or "theory_hours" in course_changes:
        affected["syllabus"].add("课程总学时变化，需重排学时分配表")
    if "tech_stack" in course_changes:
        affected["knowledge_graph"].add("技术栈调整，知识图谱可能需补充/删减知识点")
        affected["quiz"].add("技术栈调整，题库覆盖范围需要复核")
    if "prerequisites" in course_changes:
        affected["syllabus"].add("先修课程变化，需更新大纲先修说明")
    if "experiment_count" in course_changes:
        affected["lab_guide"].add("实验数变化，需新增/删减实验段落")
        affected["syllabus"].add("实验数变化，需重排实验项目表")

    # 实验增删
    for eid in added:
        affected["lab_guide"].add(f"实验{eid} 新增 → 触发源码HOOK + LabGuideExperimentAgent")
        affected["syllabus"].add(f"实验{eid} 新增 → 补入实验项目表")
        affected["quiz"].add(f"实验{eid} 新增 → 编程题取材域扩展，需补题")
    for eid in removed:
        affected["lab_guide"].add(f"实验{eid} 删除 → 移除对应段落")
        affected["syllabus"].add(f"实验{eid} 删除 → 修剪实验项目表")
        affected["quiz"].add(f"实验{eid} 删除 → 复核引用该实验的题目")

    # 实验内字段修改
    for eid, fields in modified.items():
        f_names = set(fields.keys())
        if f_names & {"objectives", "exp_content", "name"}:
            affected["lab_guide"].add(
                f"实验{eid} 内容/目标变化 → 触发源码HOOK + 重排该实验段落"
            )
        if "hours" in f_names:
            affected["syllabus"].add(f"实验{eid} 学时变化 → 重排学时分配")
            affected["lab_guide"].add(f"实验{eid} 学时变化 → 实验头部学时字段同步")
        if "source_code_path" in f_names or "main_entry" in f_names:
            affected["lab_guide"].add(
                f"实验{eid} 源码路径变化 → 必须重跑源码分析（HOOK 强制）"
            )
        if "experiment_type" in f_names or "difficulty" in f_names:
            affected["syllabus"].add(f"实验{eid} 类型/难度变化 → 项目表元数据更新")

    return {k: sorted(v) for k, v in affected.items() if v}


# ---------- 主入口 / CLI ----------

def diff_csv_against_yaml(csv_path: Path, yaml_path: Path, course_id: str | None = None) -> dict[str, Any]:
    from parser import parse_csv_to_dict
    new_spec = parse_csv_to_dict(csv_path, course_id=course_id)
    old_spec = load_yaml(yaml_path)
    return diff_specs(old_spec, new_spec)


def _format_text_summary(diff: dict[str, Any]) -> str:
    lines = []
    s = diff["summary"]
    lines.append(
        f"[DIFF] 课程字段变更 {s['course_field_count']} 项 / "
        f"实验 +{s['added_count']} -{s['removed_count']} ~{s['modified_count']}"
    )
    if diff["course_changes"]:
        lines.append("--- 课程级 ---")
        for f, ch in diff["course_changes"].items():
            lines.append(f"  {f}: {ch['old']!r} → {ch['new']!r}")
    if diff["experiments"]["added"]:
        lines.append("--- 新增实验 ---")
        for e in diff["experiments"]["added"]:
            lines.append(f"  +{e['experiment_id']}: {e['name']}")
    if diff["experiments"]["removed"]:
        lines.append("--- 删除实验 ---")
        for e in diff["experiments"]["removed"]:
            lines.append(f"  -{e['experiment_id']}: {e['name']}")
    if diff["experiments"]["modified"]:
        lines.append("--- 修改实验 ---")
        for e in diff["experiments"]["modified"]:
            fnames = ", ".join(e["fields"].keys())
            lines.append(f"  ~{e['experiment_id']}: 变更字段 [{fnames}]")
    if diff["cascade_hints"]:
        lines.append("--- 联动提示（下游文档） ---")
        for doc, hints in diff["cascade_hints"].items():
            lines.append(f"  {doc}:")
            for h in hints:
                lines.append(f"    - {h}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="比较 csv 新解析结果 vs 现有 course-spec.yaml，输出结构化 diff"
    )
    ap.add_argument("csv", type=Path, nargs="?", default=Path("input/course_spec.csv"))
    ap.add_argument("--course", type=str,
                    help="课程 ID (如 EXP001)，用于从多课程 CSV 中过滤指定课程")
    ap.add_argument(
        "-y", "--yaml", type=Path,
        help="现有 course-spec.yaml 路径（默认按解析结果的 sheet/folder 推导）"
    )
    ap.add_argument(
        "--format", choices=["json", "text"], default="text",
        help="输出格式（默认 text；CI / 上层 Agent 建议用 json）"
    )
    args = ap.parse_args()

    try:
        from parser import parse_csv_to_dict
        new_spec = parse_csv_to_dict(args.csv, course_id=args.course)
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] csv 解析失败: {exc}", file=sys.stderr)
        return 2

    if args.yaml:
        yaml_path = args.yaml
    else:
        yaml_path = Path(
            f"courses/{new_spec['category']}/{new_spec['folder']}/_meta/course-spec.yaml"
        )

    if not yaml_path.exists():
        print(
            f"[INFO] 现有 yaml 不存在 ({yaml_path})，视为全新生成，无 diff",
            file=sys.stderr,
        )
        # 全部当作 added
        diff = {
            "course_changed": True,
            "course_changes": {},
            "experiments": {
                "added": [
                    {"experiment_id": e["experiment_id"], "name": e["name"]}
                    for e in new_spec["experiments"]
                ],
                "removed": [],
                "modified": [],
            },
            "cascade_hints": {
                "lab_guide": ["首次生成全部实验段落"],
                "syllabus": ["首次生成实验项目表"],
                "knowledge_graph": ["首次生成知识图谱"],
                "quiz": ["首次生成题库"],
            },
            "summary": {
                "course_field_count": 0,
                "added_count": len(new_spec["experiments"]),
                "removed_count": 0,
                "modified_count": 0,
                "total_changed_experiments": len(new_spec["experiments"]),
            },
        }
    else:
        old_spec = load_yaml(yaml_path)
        diff = diff_specs(old_spec, new_spec)

    if args.format == "json":
        print(json.dumps(diff, ensure_ascii=False, indent=2))
    else:
        print(_format_text_summary(diff))

    # 退出码：有变更 → 1（CI 友好），无变更 → 0
    has_change = (
        diff["course_changed"]
        or diff["summary"]["total_changed_experiments"] > 0
    )
    return 1 if has_change else 0


if __name__ == "__main__":
    raise SystemExit(main())
