"""
spec-parser-skill: validator

校验 course_spec.csv 解析出的 spec dict，输出 errors / warnings 列表。
不依赖外部库，纯 stdlib。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# ---------- 校验规则常量 ----------

COURSE_ID_PATTERN = re.compile(r"^(EXP|IND)\d{3}$")
FOLDER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,19}$")
SHEET_VALUES = {"sheet1", "sheet2"}
DIFFICULTY_VALUES = {1, 2, 3}
EXPERIMENT_TYPE_VALUES = {"验证性", "设计性", "综合性"}

HOURS_RANGE = (16, 96)
EXP_HOURS_RANGE = (1, 16)


class SpecValidator:
    """对 parse_csv_to_dict 返回的 spec 执行校验。"""

    def __init__(self, spec: dict[str, Any], project_root: Path | None = None):
        self.spec = spec
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.errors: list[str] = []
        self.warnings: list[str] = []

    # ---------- 主入口 ----------

    def validate_all(self, check_paths: bool = True) -> tuple[list[str], list[str]]:
        self._check_course_id()
        self._check_folder()
        self._check_sheet()
        self._check_total_hours()
        self._check_experiment_count()
        self._check_unique_experiment_ids()
        self._check_continuous_experiment_ids()
        self._check_each_experiment()
        self._check_hours_sum()
        if check_paths:
            self._check_source_paths_exist()
        return self.errors, self.warnings

    # ---------- 课程级 ----------

    def _check_course_id(self):
        cid = self.spec.get("course_code", "")
        if not COURSE_ID_PATTERN.match(cid):
            self.errors.append(
                f"course_id 格式错误: {cid!r}（应匹配 EXP\\d{{3}} 或 IND\\d{{3}}）"
            )

    def _check_folder(self):
        folder = self.spec.get("folder", "")
        if not FOLDER_PATTERN.match(folder):
            self.errors.append(
                f"folder 格式错误: {folder!r}（小写下划线，≤20字符）"
            )

    def _check_sheet(self):
        sheet = self.spec.get("category", "")
        if sheet not in SHEET_VALUES:
            self.errors.append(f"sheet 必须是 sheet1/sheet2: {sheet!r}")

    def _check_total_hours(self):
        h = self.spec.get("total_hours")
        if not isinstance(h, int):
            self.errors.append(f"total_hours 必须是整数: {h!r}")
            return
        lo, hi = HOURS_RANGE
        if not (lo <= h <= hi):
            self.warnings.append(f"total_hours={h} 超出常规范围 [{lo}, {hi}]")

    def _check_experiment_count(self):
        exps = self.spec.get("experiments") or []
        declared = self.spec.get("experiment_count")
        if declared != len(exps):
            self.errors.append(
                f"experiment_count={declared} 与实际数量 {len(exps)} 不一致"
            )
        if len(exps) == 0:
            self.errors.append("至少需要 1 个实验")

    # ---------- 实验级 ----------

    def _check_unique_experiment_ids(self):
        ids = [e["experiment_id"] for e in self.spec.get("experiments") or []]
        dups = {i for i in ids if ids.count(i) > 1}
        if dups:
            self.errors.append(f"experiment_id 重复: {sorted(dups)}")

    def _check_continuous_experiment_ids(self):
        ids = sorted(e["experiment_id"] for e in self.spec.get("experiments") or [])
        if not ids:
            return
        expected = list(range(1, len(ids) + 1))
        if ids != expected:
            self.warnings.append(
                f"experiment_id 不连续: {ids}，建议从 1 开始连续递增"
            )

    def _check_each_experiment(self):
        for exp in self.spec.get("experiments") or []:
            eid = exp.get("experiment_id")
            label = f"实验{eid}"

            # difficulty
            diff = exp.get("difficulty")
            if diff not in DIFFICULTY_VALUES:
                self.errors.append(f"{label} difficulty 必须是 1/2/3: {diff!r}")

            # experiment_type
            etype = exp.get("experiment_type")
            if etype and etype not in EXPERIMENT_TYPE_VALUES:
                self.warnings.append(
                    f"{label} experiment_type={etype!r} 非标准值（验证性/设计性/综合性）"
                )

            # hours range
            hours = exp.get("hours")
            lo, hi = EXP_HOURS_RANGE
            if isinstance(hours, int) and not (lo <= hours <= hi):
                self.warnings.append(f"{label} hours={hours} 超出常规范围 [{lo}, {hi}]")

            # exp_content non-empty
            if not exp.get("exp_content"):
                self.errors.append(f"{label} exp_content 不能为空")

            # name length
            name = exp.get("name", "")
            if len(name) > 50:
                self.warnings.append(f"{label} 实验名超过 50 字: {name!r}")

    def _check_hours_sum(self):
        total = self.spec.get("total_hours") or 0
        sum_hours = sum(e.get("hours") or 0 for e in self.spec.get("experiments") or [])
        if total and sum_hours and total != sum_hours:
            # 实验学时之和应等于 lab_hours，不一定等于 total_hours
            lab = self.spec.get("lab_hours") or 0
            if lab and sum_hours != lab:
                self.errors.append(
                    f"实验学时之和 {sum_hours}h 与 lab_hours={lab}h 不一致"
                )

    # ---------- 源码路径 ----------

    def _check_source_paths_exist(self):
        category = self.spec.get("category", "")
        folder = self.spec.get("folder", "")
        course_dir = self.project_root / "courses" / category / folder
        for exp in self.spec.get("experiments") or []:
            scp = exp.get("source_code_path") or ""
            if not scp:
                continue
            full = course_dir / scp.rstrip("/")
            if not full.exists():
                self.warnings.append(
                    f"实验{exp['experiment_id']} source_code_path 不存在: "
                    f"{full.relative_to(self.project_root) if full.is_absolute() else full}"
                )


def validate_spec(spec: dict[str, Any], project_root: Path | None = None,
                  check_paths: bool = True) -> tuple[list[str], list[str]]:
    """便捷函数。返回 (errors, warnings)。"""
    return SpecValidator(spec, project_root).validate_all(check_paths=check_paths)


# ---------- CLI ----------

def main() -> int:
    import argparse
    import sys

    from parser import parse_csv_to_dict

    ap = argparse.ArgumentParser(description="校验 course_spec.csv")
    ap.add_argument("csv", type=Path, nargs="?",
                    default=Path("input/course_spec.csv"))
    ap.add_argument("--course", type=str,
                    help="课程 ID (如 EXP001)，用于从多课程 CSV 中过滤指定课程")
    ap.add_argument("--no-path-check", action="store_true",
                    help="跳过源码路径存在性检查")
    args = ap.parse_args()

    try:
        spec = parse_csv_to_dict(args.csv, course_id=args.course)
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] 解析失败: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate_spec(
        spec, project_root=Path.cwd(), check_paths=not args.no_path_check
    )

    if warnings:
        print(f"[WARN] {len(warnings)} 项警告:")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print(f"[ERROR] {len(errors)} 项错误:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"[OK] 校验通过: {spec['course_code']} ({spec['experiment_count']} 个实验)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
