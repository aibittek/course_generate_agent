"""
apply_updates.py — 应用 CSV 更新

读取 suggest_csv_update.py 生成的建议，按用户授权字段白名单写回 input/course_spec.csv。
保证：
  1. 每次写入前自动备份 → input/course_spec.csv.bak.{timestamp}
  2. 字段白名单：必须显式 --apply-fields，不接受 --all
  3. 变更记录：写入 _meta/csv-sync-log.md
  4. 课程级字段（tech_stack 等）会同步更新该课程所有行

Usage:
  python apply_updates.py --course EXP001 --exp 4 \\
    --suggestions /tmp/exp04_suggestions.yaml \\
    --apply-fields experiment_name,tech_stack,hours

  # 用 JSON 格式的建议（推荐，避免 YAML 解析复杂）
  python apply_updates.py --course EXP001 --exp 4 \\
    --suggestions-json /tmp/exp04_suggestions.json \\
    --apply-fields experiment_name,tech_stack
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# 课程级字段（更新时需要同步该课程所有行）
COURSE_LEVEL_FIELDS = {
    "course_id", "course_name", "sheet", "folder",
    "total_hours", "theory_hours", "lab_hours",
    "tech_stack", "prerequisites", "hardware_platform", "course_description",
}

# 实验级字段（仅更新单行）
EXPERIMENT_LEVEL_FIELDS = {
    "experiment_id", "experiment_name", "hours", "difficulty",
    "experiment_type", "source_code_path", "main_entry",
    "knowledge_points", "objectives", "exp_content", "notes",
}


def backup_csv(csv_path: Path) -> Path:
    """备份 CSV，返回备份路径。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_path = csv_path.with_name(f"{csv_path.name}.bak.{timestamp}")
    shutil.copy2(csv_path, bak_path)
    return bak_path


def apply_to_csv(
    csv_path: Path,
    course_id: str,
    exp_id: int,
    field_updates: dict[str, str],
) -> dict[str, Any]:
    """把字段更新写入 CSV。返回应用摘要。"""
    # 读全部行
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # 验证字段名都在 schema 中
    invalid = [f for f in field_updates if f not in fieldnames]
    if invalid:
        raise ValueError(f"字段不在 CSV schema 中: {invalid}")

    # 分类：课程级 / 实验级
    course_level_updates = {k: v for k, v in field_updates.items() if k in COURSE_LEVEL_FIELDS}
    exp_level_updates = {k: v for k, v in field_updates.items() if k in EXPERIMENT_LEVEL_FIELDS}

    affected_rows = 0
    target_row_found = False

    for row in rows:
        if row.get("course_id") != course_id:
            continue

        # 课程级字段：所有行都更新
        if course_level_updates:
            for k, v in course_level_updates.items():
                row[k] = str(v)
            affected_rows += 1

        # 实验级字段：仅匹配 exp_id 的行
        if str(row.get("experiment_id", "")).strip() == str(exp_id):
            target_row_found = True
            for k, v in exp_level_updates.items():
                row[k] = str(v)
            if not course_level_updates:  # 避免重复计数
                affected_rows += 1

    if not target_row_found:
        raise ValueError(f"未找到 {course_id} exp{exp_id} 的行")

    # 写回
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "course_level_fields": list(course_level_updates.keys()),
        "experiment_level_fields": list(exp_level_updates.keys()),
        "affected_rows": affected_rows,
    }


def write_sync_log(
    course_folder: str,
    course_id: str,
    exp_id: int,
    applied: dict,
    backup_path: Path,
):
    """写入 csv-sync-log.md（追加模式）。"""
    log_dir = Path("courses") / course_folder / "_meta"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "csv-sync-log.md"

    entry = []
    if not log_path.exists():
        entry.append(f"# CSV 反向同步日志 - {course_id}\n")
        entry.append(
            "记录每次由 source-code-sync-skill 触发的 CSV 写回操作，"
            "便于审计、回滚与一致性追溯。\n\n"
        )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry.append(f"## {timestamp} — exp{exp_id}\n")
    entry.append(f"- **备份文件**: `{backup_path}`\n")
    entry.append(f"- **课程级字段**: {applied['course_level_fields'] or '无'}\n")
    entry.append(f"- **实验级字段**: {applied['experiment_level_fields'] or '无'}\n")
    entry.append(f"- **影响行数**: {applied['affected_rows']}\n")
    entry.append(f"- **变更内容**:\n")
    for k, v in applied.get("field_updates", {}).items():
        v_short = str(v)[:80] + ("..." if len(str(v)) > 80 else "")
        entry.append(f"  - `{k}` = `{v_short}`\n")
    entry.append("\n")

    with log_path.open("a", encoding="utf-8") as f:
        f.writelines(entry)

    return log_path


def parse_suggestions_json(path: Path) -> list[dict]:
    """从 JSON 建议文件提取 suggestions 列表。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("suggestions", [])


def find_course_folder(csv_path: Path, course_id: str) -> str:
    """从 CSV 中查找 course_id 对应的 sheet/folder。"""
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("course_id") == course_id:
                sheet = row.get("sheet", "")
                folder = row.get("folder", "")
                return f"{sheet}/{folder}"
    raise ValueError(f"CSV 中未找到课程 {course_id}")


def main():
    parser = argparse.ArgumentParser(description="应用 CSV 更新建议（写回 CSV）")
    parser.add_argument("--course", required=True)
    parser.add_argument("--exp", type=int, required=True)
    parser.add_argument(
        "--suggestions-json", required=True,
        help="suggest_csv_update.py 的 JSON 输出（推荐 --format json）",
    )
    parser.add_argument(
        "--apply-fields", required=True,
        help="逗号分隔的字段名白名单，例如 experiment_name,tech_stack,hours",
    )
    parser.add_argument("--csv", default="input/course_spec.csv")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不写入")
    parser.add_argument("--no-backup", action="store_true", help="跳过备份（不推荐）")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV 不存在: {csv_path}", file=sys.stderr)
        sys.exit(2)

    suggestions = parse_suggestions_json(Path(args.suggestions_json))
    apply_field_set = set(s.strip() for s in args.apply_fields.split(",") if s.strip())

    # 收集要应用的字段值
    field_updates: dict[str, str] = {}
    skipped = []
    not_found = []

    for sug in suggestions:
        field = sug.get("field")
        if not field:
            continue
        if field not in apply_field_set:
            skipped.append(field)
            continue
        if sug.get("action") == "manual_review":
            print(
                f"[apply_updates] WARN: {field} 标记为 manual_review，跳过自动应用。"
                f"请由 Claude 在对话中调用 LLM 重写后再应用。",
                file=sys.stderr,
            )
            continue
        field_updates[field] = sug.get("code_new")

    missing = apply_field_set - set(field_updates.keys()) - {f for f in apply_field_set if any(s.get("field") == f and s.get("action") == "manual_review" for s in suggestions)}
    if missing:
        not_found = sorted(missing)

    print(f"[apply_updates] 计划应用 {len(field_updates)} 个字段:", file=sys.stderr)
    for k, v in field_updates.items():
        v_short = str(v)[:60] + ("..." if len(str(v)) > 60 else "")
        print(f"    {k} = {v_short}", file=sys.stderr)

    if not_found:
        print(f"[apply_updates] WARN: 在建议中未找到这些字段: {not_found}", file=sys.stderr)

    if args.dry_run:
        print("[apply_updates] DRY RUN — 未实际写入", file=sys.stderr)
        sys.exit(0)

    if not field_updates:
        print("[apply_updates] 无字段需要应用，退出。", file=sys.stderr)
        sys.exit(0)

    # 备份
    if not args.no_backup:
        bak = backup_csv(csv_path)
        print(f"[apply_updates] 已备份: {bak}", file=sys.stderr)
    else:
        bak = Path("(skipped)")

    # 写入
    try:
        applied = apply_to_csv(csv_path, args.course, args.exp, field_updates)
        applied["field_updates"] = field_updates
    except Exception as e:
        print(f"[apply_updates] ERROR: {e}", file=sys.stderr)
        if not args.no_backup:
            print(f"[apply_updates] 可从备份恢复: cp {bak} {csv_path}", file=sys.stderr)
        sys.exit(2)

    # 写日志
    try:
        course_folder = find_course_folder(csv_path, args.course)
        log_path = write_sync_log(course_folder, args.course, args.exp, applied, bak)
        print(f"[apply_updates] 日志已写入: {log_path}", file=sys.stderr)
    except Exception as e:
        print(f"[apply_updates] WARN: 写日志失败（不影响 CSV 已写入）: {e}", file=sys.stderr)

    # 输出摘要
    summary = {
        "status": "applied",
        "course_id": args.course,
        "experiment_id": args.exp,
        "backup": str(bak),
        "applied": applied,
        "next_step": (
            "运行 `python .claude/skills/spec-parser-skill/diff.py --course "
            f"{args.course}` 检测变更，然后调用 IncrementalUpdateAgent 模式0 "
            "同步下游文档"
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
