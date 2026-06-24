"""
suggest_csv_update.py — CSV 更新建议生成器

读取 extract_capabilities.py 的输出 + CSV 现值，生成字段级更新建议。
建议含 old/new/confidence/reason/cascade_impact，由 Claude 在对话中展示给用户确认。

Usage:
  python suggest_csv_update.py --course EXP001 --exp 4 \\
    --capabilities /tmp/exp04_capabilities.json \\
    [--csv input/course_spec.csv] [--output suggestions.yaml]

不写回 CSV，只生成建议（写回由 apply_updates.py 负责）。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


LIST_SEP = ";"


def read_csv_row(csv_path: Path, course_id: str, exp_id: int) -> dict | None:
    """读取 CSV 中指定 course_id + experiment_id 的行。"""
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("course_id") == course_id and str(row.get("experiment_id", "")).strip() == str(exp_id):
                return row
    return None


def list_field_diff(old_str: str, new_list: list[str]) -> tuple[bool, list[str], list[str]]:
    """对列表字段做 diff，返回（是否变化，新增项，移除项）。"""
    old_set = set(s.strip() for s in (old_str or "").split(LIST_SEP) if s.strip())
    new_set = set(new_list)
    if old_set == new_set:
        return False, [], []
    return True, sorted(new_set - old_set), sorted(old_set - new_set)


def cascade_impact_for_field(field: str) -> list[str]:
    """字段变更对下游文档的影响清单（用于提醒用户）。"""
    table = {
        "experiment_name": [
            "knowledge_graph 章节标题需更新",
            "lab_guide 实验标题需更新",
            "syllabus 实验项目表需更新",
        ],
        "tech_stack": [
            "knowledge_graph 需调整技术节点",
            "syllabus 教学内容需对齐新技术",
            "lab_guide 实验环境章节需更新",
        ],
        "objectives": [
            "lab_guide 实验目标段需重写",
            "syllabus 教学目标需对齐",
            "quiz 简答题可能失效（建议重新生成）",
        ],
        "exp_content": [
            "lab_guide 实验步骤需全量重写",
            "quiz 编程题必失效（必须重新生成）",
            "knowledge_graph 知识点关联需复核",
        ],
        "hours": [
            "syllabus 学时分配表需同步",
            "lab_guide 实验头部学时需更新",
            "course-spec.yaml total_hours 需复核",
        ],
        "difficulty": [
            "syllabus 实验项目表难度列需更新",
            "quiz 题目难度分布需复核",
        ],
        "experiment_type": [
            "syllabus 实验类型分布需更新",
            "quality-standard 中验证/设计/综合性比例校验",
        ],
        "source_code_path": [
            "源码HOOK会重新触发分析（如 code_status 改变）",
            "lab_guide 源码引用 file:line 需失效重新生成",
        ],
        "main_entry": [
            "lab_guide 实验步骤中的运行命令需更新",
        ],
    }
    return table.get(field, [])


def suggest(course_id: str, exp_id: int, capabilities: dict, csv_row: dict) -> dict:
    """对比 CSV 现值 vs 提取的能力，生成建议清单。"""
    suggestions = []

    if capabilities.get("status") == "no_python_files":
        return {
            "course_id": course_id,
            "experiment_id": exp_id,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "warning": "源码目录中没有 .py 文件，无法生成有效建议",
            "suggestions": [],
        }

    # === 1. experiment_name ===
    candidates = capabilities.get("experiment_name_candidates", [])
    if candidates:
        best = max(candidates, key=lambda c: c["confidence"])
        old = (csv_row.get("experiment_name") or "").strip()
        if old != best["value"]:
            suggestions.append({
                "field": "experiment_name",
                "csv_old": old,
                "code_new": best["value"],
                "confidence": best["confidence"],
                "reason": f"源码 {best['source']} 显示名称为 \"{best['value']}\"",
                "alternatives": [c for c in candidates if c["value"] != best["value"]],
                "cascade_impact": cascade_impact_for_field("experiment_name"),
            })

    # === 2. tech_stack ===
    new_tech = capabilities.get("tech_stack", [])
    if new_tech:
        old_tech_str = csv_row.get("tech_stack") or ""
        # tech_stack 是课程级字段，每行重复。这里只比对当前行的值
        # 但更新建议应在课程层面（提示用户）
        changed, added, removed = list_field_diff(old_tech_str, new_tech)
        if changed:
            suggestions.append({
                "field": "tech_stack",
                "csv_old": old_tech_str,
                "code_new": LIST_SEP.join(new_tech),
                "added": added,
                "removed": removed,
                "confidence": 0.9 if removed else 0.95,
                "reason": (
                    f"requirements.txt + import 检测到{'新增' if added else ''}{'/' if added and removed else ''}"
                    f"{'移除' if removed else ''}领域库: "
                    f"+{added} -{removed}"
                ),
                "cascade_impact": cascade_impact_for_field("tech_stack"),
                "note": "tech_stack 是课程级字段，更新会影响该课程所有实验行",
            })

    # === 3. hours ===
    estimated_hours = capabilities.get("estimated_hours")
    if estimated_hours is not None:
        try:
            csv_hours = int(csv_row.get("hours", 0))
        except (ValueError, TypeError):
            csv_hours = 0
        if abs(csv_hours - estimated_hours) >= 2:  # 差异 ≥ 2h 才建议
            suggestions.append({
                "field": "hours",
                "csv_old": csv_hours,
                "code_new": estimated_hours,
                "confidence": 0.6,  # 估算值置信度低
                "reason": (
                    f"基于代码量 {capabilities['metrics']['total_lines']} 行 + "
                    f"依赖 {capabilities['metrics']['dep_count']} 个估算"
                ),
                "cascade_impact": cascade_impact_for_field("hours"),
                "warning": "学时是教学决策，建议人工最终确认（启发式估算仅供参考）",
            })

    # === 4. difficulty ===
    est_difficulty = capabilities.get("estimated_difficulty")
    if est_difficulty is not None:
        try:
            csv_difficulty = int(csv_row.get("difficulty", 0))
        except (ValueError, TypeError):
            csv_difficulty = 0
        if csv_difficulty != est_difficulty:
            suggestions.append({
                "field": "difficulty",
                "csv_old": csv_difficulty,
                "code_new": est_difficulty,
                "confidence": 0.65,
                "reason": (
                    f"代码特征: 行数={capabilities['metrics']['total_lines']}, "
                    f"含训练={capabilities['metrics']['has_training_keyword']}, "
                    f"含类={capabilities['metrics']['has_class']}"
                ),
                "cascade_impact": cascade_impact_for_field("difficulty"),
            })

    # === 5. experiment_type ===
    est_type = capabilities.get("estimated_experiment_type")
    if est_type:
        csv_type = (csv_row.get("experiment_type") or "").strip()
        if csv_type != est_type:
            suggestions.append({
                "field": "experiment_type",
                "csv_old": csv_type,
                "code_new": est_type,
                "confidence": 0.7,
                "reason": "基于难度和代码复杂度推断",
                "cascade_impact": cascade_impact_for_field("experiment_type"),
            })

    # === 6. main_entry ===
    new_entry = capabilities.get("main_entry")
    if new_entry:
        csv_entry = (csv_row.get("main_entry") or "").strip()
        if csv_entry != new_entry:
            suggestions.append({
                "field": "main_entry",
                "csv_old": csv_entry,
                "code_new": new_entry,
                "confidence": 0.95,
                "reason": f"源码目录中找到主入口文件: {new_entry}",
                "cascade_impact": cascade_impact_for_field("main_entry"),
            })

    # === 7. objectives / exp_content（只标记，不自动生成）===
    # 如果 experiment_name 或核心函数变了，提示 objectives 可能也要重写
    needs_objective_review = any(
        s["field"] in ("experiment_name", "tech_stack") and s["confidence"] >= 0.8
        for s in suggestions
    )
    if needs_objective_review:
        suggestions.append({
            "field": "objectives",
            "csv_old": (csv_row.get("objectives") or "").strip()[:120] + "...",
            "code_new": "[需 LLM 重写] 源码核心功能已变化",
            "confidence": 0.4,
            "reason": "experiment_name 或 tech_stack 已变化，建议 Claude 在对话中调用 LLM 基于源码重写 objectives",
            "cascade_impact": cascade_impact_for_field("objectives"),
            "action": "manual_review",  # 标记为手动处理
            "key_functions": capabilities.get("key_functions", []),  # 给 LLM 重写时用
        })
        suggestions.append({
            "field": "exp_content",
            "csv_old": (csv_row.get("exp_content") or "").strip()[:120] + "...",
            "code_new": "[需 LLM 重写] 实验步骤需根据新源码逻辑生成",
            "confidence": 0.4,
            "reason": "实验核心功能已变化，exp_content 必须随之重写",
            "cascade_impact": cascade_impact_for_field("exp_content"),
            "action": "manual_review",
            "key_functions": capabilities.get("key_functions", []),
        })

    return {
        "course_id": course_id,
        "experiment_id": exp_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "capabilities_source": capabilities.get("source_path"),
        "csv_row_summary": {
            "experiment_name": csv_row.get("experiment_name"),
            "hours": csv_row.get("hours"),
            "difficulty": csv_row.get("difficulty"),
            "experiment_type": csv_row.get("experiment_type"),
        },
        "total_suggestions": len(suggestions),
        "high_confidence_count": sum(1 for s in suggestions if s.get("confidence", 0) >= 0.8),
        "manual_review_count": sum(1 for s in suggestions if s.get("action") == "manual_review"),
        "suggestions": suggestions,
    }


def to_yaml_lite(data: dict, indent: int = 0) -> str:
    """轻量 YAML 序列化（避免引入 PyYAML 依赖）。"""
    lines = []
    pad = "  " * indent
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{pad}{k}:")
                lines.append(to_yaml_lite(v, indent + 1))
            elif v is None:
                lines.append(f"{pad}{k}: null")
            elif isinstance(v, bool):
                lines.append(f"{pad}{k}: {str(v).lower()}")
            elif isinstance(v, (int, float)):
                lines.append(f"{pad}{k}: {v}")
            else:
                # 字符串：含特殊字符就加引号
                s = str(v)
                if any(c in s for c in ":#\n\"'") or s.strip() != s:
                    s = '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
                lines.append(f"{pad}{k}: {s}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{pad}-")
                lines.append(to_yaml_lite(item, indent + 1))
            else:
                lines.append(f"{pad}- {item}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="生成 CSV 更新建议")
    parser.add_argument("--course", required=True)
    parser.add_argument("--exp", type=int, required=True)
    parser.add_argument("--capabilities", required=True, help="extract_capabilities.py 输出的 JSON")
    parser.add_argument("--csv", default="input/course_spec.csv")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
    parser.add_argument("--output")
    args = parser.parse_args()

    cap = json.loads(Path(args.capabilities).read_text(encoding="utf-8"))
    csv_row = read_csv_row(Path(args.csv), args.course, args.exp)

    if csv_row is None:
        print(f"ERROR: CSV 中未找到 {args.course} exp{args.exp}", file=sys.stderr)
        sys.exit(2)

    result = suggest(args.course, args.exp, cap, csv_row)

    if args.format == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = to_yaml_lite(result)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(
            f"[suggest_csv_update] {result['total_suggestions']} suggestions "
            f"({result['high_confidence_count']} high-conf, "
            f"{result['manual_review_count']} need manual review) → {args.output}",
            file=sys.stderr,
        )
    else:
        print(output)


if __name__ == "__main__":
    main()
