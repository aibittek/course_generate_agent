"""
spec-parser-skill: course_spec.csv -> course-spec.yaml

CSV 设计：多课程共存，每行 = 一个实验，课程级字段每行重复（解析时去重）
列表字段使用 ';' 分隔

v2.0 变更：支持 --course 参数，从多课程 CSV 中过滤指定课程
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

LIST_SEP = ";"
DIFFICULTY_MAP = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐"}


def _parse_list(value: str, sep: str = LIST_SEP) -> list[str]:
    """以分号拆分列表字段，过滤空值并去除两端空白。"""
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(sep) if item.strip()]


def _parse_int(value: str, field: str, default: int | None = None) -> int | None:
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(str(value).strip())
    except ValueError as exc:
        raise ValueError(f"字段 `{field}` 必须是整数，实际值: {value!r}") from exc


def _build_course_meta(rows: list[dict]) -> dict[str, Any]:
    """从所有行抽取课程级字段（每行都填，取第一行非空值，校验冲突）。"""
    if not rows:
        raise ValueError("CSV 没有数据行")

    course_keys = [
        "course_id", "course_name", "sheet", "folder",
        "total_hours", "theory_hours", "lab_hours",
        "tech_stack", "prerequisites", "hardware_platform", "course_description",
    ]

    meta: dict[str, Any] = {}
    for key in course_keys:
        first_value = None
        for row in rows:
            v = (row.get(key) or "").strip()
            if not v:
                continue
            if first_value is None:
                first_value = v
            elif v != first_value:
                raise ValueError(
                    f"课程级字段 `{key}` 在多行中不一致: {first_value!r} vs {v!r}"
                )
        meta[key] = first_value or ""

    # 类型转换
    meta["total_hours"] = _parse_int(meta.get("total_hours") or "", "total_hours")
    meta["theory_hours"] = _parse_int(meta.get("theory_hours") or "", "theory_hours", default=0)
    if meta.get("lab_hours"):
        meta["lab_hours"] = _parse_int(meta["lab_hours"], "lab_hours")
    else:
        meta["lab_hours"] = (meta.get("total_hours") or 0) - (meta.get("theory_hours") or 0)

    meta["tech_stack"] = _parse_list(meta.get("tech_stack") or "")
    meta["prerequisites"] = _parse_list(meta.get("prerequisites") or "")

    return meta


def _resolve_source_code_path(experiment_id: int, explicit_path: str) -> str:
    """
    源码路径解析策略：
    1. 显式列优先：source_code_path 字段非空 -> 直接使用
    2. 否则按约定推导：source-codes/exp{NN}/   （NN = 两位数）
    """
    explicit = (explicit_path or "").strip()
    if explicit:
        return explicit.rstrip("/") + "/"
    return f"source-codes/exp{experiment_id:02d}/"


def _parse_experiment(row: dict) -> dict[str, Any]:
    exp_id = _parse_int(row.get("experiment_id") or "", "experiment_id")
    if exp_id is None:
        raise ValueError(f"experiment_id 必填，行内容: {row}")

    name = (row.get("experiment_name") or "").strip()
    if not name:
        raise ValueError(f"experiment_name 必填 (experiment_id={exp_id})")

    hours = _parse_int(row.get("hours") or "", "hours")
    if hours is None:
        raise ValueError(f"hours 必填 (experiment_id={exp_id})")

    difficulty_int = _parse_int(row.get("difficulty") or "", "difficulty", default=2)
    difficulty_stars = DIFFICULTY_MAP.get(difficulty_int, "⭐⭐")

    return {
        "id": f"exp{exp_id:02d}",
        "experiment_id": exp_id,
        "name": name,
        "hours": hours,
        "difficulty": difficulty_int,
        "difficulty_stars": difficulty_stars,
        "experiment_type": (row.get("experiment_type") or "设计性").strip() or "设计性",
        "source_code_path": _resolve_source_code_path(exp_id, row.get("source_code_path") or ""),
        "main_entry": (row.get("main_entry") or "").strip(),
        "knowledge_points": _parse_list(row.get("knowledge_points") or ""),
        "objectives": _parse_list(row.get("objectives") or ""),
        "exp_content": _parse_list(row.get("exp_content") or ""),
        "notes": (row.get("notes") or "").strip(),
    }


def _compute_csv_hash(csv_path: Path) -> str:
    """对 CSV 字节计算 sha256，用作 spec 水印，下游可据此检测 csv 是否已变更。"""
    h = hashlib.sha256()
    with csv_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_csv_to_dict(csv_path: Path, course_id: str | None = None) -> dict[str, Any]:
    """
    读取 csv，返回 course-spec dict（与现有 course-spec.yaml 兼容）。

    Args:
        csv_path: CSV 文件路径
        course_id: 可选，指定课程 ID（如 EXP001）。若为 None，要求 CSV 只包含单一课程
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 文件不存在: {csv_path}")

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        all_rows = [row for row in reader if any((v or "").strip() for v in row.values())]

    if not all_rows:
        raise ValueError(f"CSV 文件为空或仅有表头: {csv_path}")

    # 过滤指定课程的行
    if course_id:
        rows = [row for row in all_rows if (row.get("course_id") or "").strip() == course_id]
        if not rows:
            available = sorted(set((row.get("course_id") or "").strip() for row in all_rows if (row.get("course_id") or "").strip()))
            raise ValueError(f"CSV 中未找到课程 {course_id}，可用课程: {available}")
    else:
        rows = all_rows

    meta = _build_course_meta(rows)

    experiments = [_parse_experiment(row) for row in rows]
    experiments.sort(key=lambda e: e["experiment_id"])

    # 校验 experiment_id 连续唯一
    seen_ids = [e["experiment_id"] for e in experiments]
    if len(set(seen_ids)) != len(seen_ids):
        dups = [i for i in seen_ids if seen_ids.count(i) > 1]
        raise ValueError(f"experiment_id 重复: {sorted(set(dups))}")

    spec = {
        "course_code": meta["course_id"],
        "course_name": meta["course_name"],
        "category": meta["sheet"],
        "folder": meta["folder"],
        "prerequisites": meta["prerequisites"],
        "total_hours": meta["total_hours"],
        "theory_hours": meta["theory_hours"],
        "lab_hours": meta["lab_hours"],
        "experiment_count": len(experiments),
        "tech_stack": meta["tech_stack"],
        "hardware": meta["hardware_platform"],
        "description": meta["course_description"],
        "experiments": experiments,
        # 水印：spec 与 csv 的强一致绑定，供 diff/incremental-update 检测变更
        "_source": {
            "csv_path": str(csv_path).replace("\\", "/"),
            "csv_sha256": _compute_csv_hash(csv_path),
            "parsed_at": datetime.now().isoformat(timespec="seconds"),
            "parser": "spec-parser-skill",
        },
    }
    return spec


# ---------- 极简 yaml 输出（无外部依赖） ----------

def _yaml_escape(s: str) -> str:
    """简单字符串转义：含特殊字符的用双引号。"""
    if s is None:
        return '""'
    s = str(s)
    if any(ch in s for ch in [":", "#", "\n", '"', "'", "[", "]", "{", "}", ","]):
        s = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{s}"'
    return s


def _emit_block_scalar(value: str, indent: int) -> list[str]:
    """多行字符串使用 | 块标量。"""
    pad = " " * (indent + 2)
    lines = ["|"]
    for line in str(value).splitlines() or [""]:
        lines.append(f"{pad}{line}")
    return lines


def dump_yaml(spec: dict[str, Any]) -> str:
    """将 spec dict 序列化为 yaml 字符串，输出格式与现有 course-spec.yaml 对齐。"""
    out: list[str] = []
    out.append(f"course_code: {spec['course_code']}")
    out.append(f"course_name: {spec['course_name']}")
    out.append(f"category: {spec['category']}")
    out.append(f"folder: {spec['folder']}")

    out.append("prerequisites:")
    for p in spec.get("prerequisites") or []:
        out.append(f"  - {p}")

    out.append(f"total_hours: {spec['total_hours']}")
    out.append(f"theory_hours: {spec['theory_hours']}")
    out.append(f"lab_hours: {spec['lab_hours']}")
    out.append(f"experiment_count: {spec['experiment_count']}")

    out.append("tech_stack:")
    for t in spec.get("tech_stack") or []:
        out.append(f"  - {t}")

    out.append(f"hardware: {spec.get('hardware') or ''}")

    desc = spec.get("description") or ""
    if "\n" in desc or len(desc) > 80:
        out.append("description: |")
        for line in desc.splitlines() or [""]:
            out.append(f"  {line}")
    else:
        out.append(f"description: {_yaml_escape(desc)}")

    out.append("experiments:")
    for exp in spec["experiments"]:
        out.append(f"  - id: {exp['id']}")
        out.append(f"    experiment_id: {exp['experiment_id']}")
        out.append(f"    name: {exp['name']}")
        out.append(f"    hours: {exp['hours']}")
        out.append(f"    difficulty: {exp['difficulty']}")
        out.append(f"    difficulty_stars: \"{exp['difficulty_stars']}\"")
        out.append(f"    experiment_type: {exp['experiment_type']}")
        out.append(f"    source_code_path: {exp['source_code_path']}")
        if exp.get("main_entry"):
            out.append(f"    main_entry: {exp['main_entry']}")
        if exp.get("knowledge_points"):
            out.append("    knowledge_points:")
            for kp in exp["knowledge_points"]:
                out.append(f"      - {kp}")
        if exp.get("objectives"):
            out.append("    objectives:")
            for obj in exp["objectives"]:
                out.append(f"      - {obj}")
        out.append("    exp_content:")
        for c in exp.get("exp_content") or []:
            out.append(f"      - {c}")
        if exp.get("notes"):
            out.append(f"    notes: {_yaml_escape(exp['notes'])}")
        out.append("")  # 空行分隔

    src = spec.get("_source")
    if src:
        out.append("_source:")
        out.append(f"  csv_path: {src.get('csv_path', '')}")
        out.append(f"  csv_sha256: {src.get('csv_sha256', '')}")
        out.append(f"  parsed_at: {src.get('parsed_at', '')}")
        out.append(f"  parser: {src.get('parser', 'spec-parser-skill')}")

    return "\n".join(out) + "\n"


# ---------- CLI ----------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="解析 course_spec.csv 为 course-spec.yaml"
    )
    parser.add_argument(
        "csv", type=Path, nargs="?",
        default=Path("input/course_spec.csv"),
        help="CSV 输入路径 (默认: input/course_spec.csv)"
    )
    parser.add_argument(
        "--course", type=str,
        help="课程 ID (如 EXP001)，用于从多课程 CSV 中过滤指定课程"
    )
    parser.add_argument(
        "-o", "--output", type=Path,
        help="输出 yaml 路径 (默认: courses/{sheet}/{folder}/_meta/course-spec.yaml)"
    )
    parser.add_argument(
        "--validate-only", action="store_true",
        help="仅校验，不写文件"
    )
    args = parser.parse_args()

    try:
        spec = parse_csv_to_dict(args.csv, course_id=args.course)
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] 解析失败: {exc}", file=sys.stderr)
        return 1

    yaml_text = dump_yaml(spec)

    if args.validate_only:
        print(f"[OK] 解析成功: {spec['course_code']} / {spec['experiment_count']} 个实验")
        return 0

    if args.output:
        out_path = args.output
    else:
        out_path = Path(
            f"courses/{spec['category']}/{spec['folder']}/_meta/course-spec.yaml"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml_text, encoding="utf-8")
    print(f"[OK] 已写入: {out_path}")
    print(f"     课程: {spec['course_code']} {spec['course_name']}")
    print(f"     实验: {spec['experiment_count']} 个 / 总学时 {spec['total_hours']}h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
