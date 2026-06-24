"""
extract_capabilities.py — 源码能力提取器

从实验源码目录提取关键信息，用于反向同步 CSV：
  - tech_stack 候选（来自 import + requirements.txt）
  - experiment_name 候选（来自 docstring / README / 文件名）
  - 估算 hours / difficulty / experiment_type
  - 关键函数列表（带 docstring）

输出 JSON，供 suggest_csv_update.py 消费。

Usage:
  python extract_capabilities.py --course EXP001 --exp 4 \\
    [--source-path source-codes/exp04/] [--output capabilities.json]

设计原则：
  1. 纯标准库（ast / json / re / pathlib），不引入第三方依赖
  2. 确定性：相同输入 → 相同输出（不调 LLM）
  3. 候选+置信度：对名称等模糊字段，给候选列表而非单一答案
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# 领域识别词：CSV tech_stack 字段中常见的"领域库"白名单
# import xxx 命中此表才进入 tech_stack（避免把 os/sys/typing 等当技术栈）
# ============================================================
DOMAIN_LIBS = {
    # CV
    "cv2": "OpenCV", "mediapipe": "MediaPipe", "PIL": "Pillow",
    "skimage": "scikit-image",
    # DL
    "torch": "PyTorch", "tensorflow": "TensorFlow", "tf": "TensorFlow",
    "ultralytics": "YOLOv8", "onnxruntime": "ONNX Runtime", "tensorrt": "TensorRT",
    "transformers": "Transformers",
    # ML
    "sklearn": "scikit-learn", "scipy": "SciPy", "numpy": "NumPy",
    "pandas": "Pandas", "xgboost": "XGBoost",
    # Speech
    "speech_recognition": "SpeechRecognition", "pyaudio": "PyAudio",
    "vosk": "Vosk", "whisper": "Whisper", "espnet": "ESPnet",
    # Robotics
    "rclpy": "ROS2", "rclcpp": "ROS2", "rospy": "ROS1",
    "tf2_ros": "TF2", "moveit_commander": "MoveIt2", "moveit_msgs": "MoveIt2",
    "geometry_msgs": "ROS2", "sensor_msgs": "ROS2", "std_msgs": "ROS2",
    # SLAM
    "slam_toolbox": "SLAM_Toolbox", "nav2_msgs": "Nav2", "rtabmap": "RTAB-Map",
    # LLM
    "openai": "OpenAI API", "langchain": "LangChain", "llama_cpp": "LlamaCpp",
    "transformers": "Transformers",
    # OCR
    "pytesseract": "Tesseract OCR", "paddleocr": "PaddleOCR",
    # 其他
    "qrcode": "qrcode", "pyzbar": "pyzbar", "yaml": "PyYAML",
}


# ============================================================
# 工具函数
# ============================================================

def find_python_files(root: Path) -> list[Path]:
    """递归找所有 .py 文件，忽略 __pycache__ 和 code-analysis 目录。"""
    files = []
    for p in root.rglob("*.py"):
        parts = set(p.parts)
        if "__pycache__" in parts or "code-analysis" in parts:
            continue
        files.append(p)
    return sorted(files)


def parse_imports(py_file: Path) -> set[str]:
    """用 ast 解析 .py 文件的 top-level import，提取顶层包名。"""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    pkgs = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                pkgs.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                pkgs.add(node.module.split(".")[0])
    return pkgs


def parse_requirements(req_file: Path) -> list[str]:
    """解析 requirements.txt，返回 [(pkg_name, version), ...] 的简化字符串列表。"""
    if not req_file.exists():
        return []
    deps = []
    for line in req_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 形如 opencv-python==4.8.0.74 或 mediapipe>=0.10
        m = re.match(r"^([a-zA-Z0-9_\-\[\]\.]+)\s*([<>=!~]+\s*\S+)?", line)
        if m:
            deps.append(line)  # 保留完整声明
    return deps


def extract_tech_stack(py_files: list[Path], requirements: list[str]) -> tuple[list[str], list[str]]:
    """合并 import 和 requirements，返回（去重领域库列表，来源说明列表）。"""
    domain_hits: set[str] = set()
    sources = []

    # 来自 import
    all_imports: set[str] = set()
    for f in py_files:
        all_imports |= parse_imports(f)

    for imp in all_imports:
        if imp in DOMAIN_LIBS:
            domain_hits.add(DOMAIN_LIBS[imp])

    if domain_hits:
        sources.append(f"import:{','.join(sorted(all_imports & set(DOMAIN_LIBS.keys())))}")

    # 来自 requirements（更权威，覆盖识别）
    for dep in requirements:
        pkg = re.split(r"[<>=!~]", dep)[0].strip().lower().replace("-", "_")
        # 反查 DOMAIN_LIBS（按 import 名匹配）
        for imp_name, display in DOMAIN_LIBS.items():
            if pkg == imp_name.lower() or pkg == display.lower().replace(" ", "").replace("-", "_"):
                domain_hits.add(display)
                break

    if requirements:
        sources.append(f"requirements.txt:{len(requirements)} packages")

    return sorted(domain_hits), sources


def extract_main_docstring(py_file: Path) -> str | None:
    """提取文件级 docstring 的第一行（用作 experiment_name 候选）。"""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None
    doc = ast.get_docstring(tree)
    if doc:
        return doc.strip().split("\n")[0].strip()
    return None


def extract_key_functions(py_file: Path, max_n: int = 5) -> list[dict]:
    """提取主要函数（带 docstring 的 top-level def），最多 max_n 个。"""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    funcs = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if doc:  # 只要带 docstring 的
                funcs.append({
                    "name": node.name,
                    "doc": doc.strip().split("\n")[0].strip()[:100],
                })
            if len(funcs) >= max_n:
                break
    return funcs


def find_readme_h1(source_path: Path) -> str | None:
    """读 README.md 的第一个 H1 标题作为 experiment_name 候选。"""
    for name in ("README.md", "readme.md", "README"):
        f = source_path / name
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.startswith("# ") and not line.startswith("## "):
                    return line[2:].strip()
            break
    return None


def find_meta_yaml(source_path: Path) -> dict | None:
    """读 _meta.yaml（轻量解析，只取 experiment_name 字段）。"""
    f = source_path / "_meta.yaml"
    if not f.exists():
        return None
    result = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(experiment_name|experiment_id|main_entry):\s*(.+?)\s*$", line)
        if m:
            result[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return result or None


def filename_to_name(py_files: list[Path]) -> str | None:
    """从主入口文件名推断实验名称（demo_xxx.py / main.py → xxx）。"""
    # 优先找 demo_*.py 或 main.py
    for f in py_files:
        if f.name.startswith("demo_") and f.name != "demo_template.py":
            stem = f.stem[5:]  # 去掉 demo_ 前缀
            return stem.replace("_", " ").title()
    return None


def estimate_complexity(py_files: list[Path], requirements: list[str]) -> dict:
    """统计代码量并估算 hours/difficulty。"""
    total_lines = 0
    func_count = 0
    import_count = 0
    has_loops = False
    has_class = False
    has_training_keyword = False

    for f in py_files:
        try:
            content = f.read_text(encoding="utf-8")
            total_lines += content.count("\n") + 1
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_count += 1
                elif isinstance(node, ast.ClassDef):
                    has_class = True
                elif isinstance(node, (ast.For, ast.While)):
                    has_loops = True
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_count += 1
            # 关键词扫描（训练/标注/微调）
            if re.search(r"(train|fit|optimizer|backward|epoch|dataset)", content, re.I):
                has_training_keyword = True
        except (SyntaxError, UnicodeDecodeError):
            continue

    dep_count = len(requirements)

    # 启发式打分
    score = (total_lines / 50) + (dep_count * 0.5)
    if has_class:
        score += 1
    if has_training_keyword:
        score += 2

    hours = max(2, min(8, round(score / 2)))

    # difficulty: 1=验证, 2=设计, 3=综合
    if total_lines < 100 and not has_loops:
        difficulty = 1
        exp_type = "验证性"
    elif total_lines > 300 or has_training_keyword:
        difficulty = 3
        exp_type = "综合性"
    else:
        difficulty = 2
        exp_type = "设计性"

    return {
        "total_lines": total_lines,
        "function_count": func_count,
        "import_count": import_count,
        "dep_count": dep_count,
        "has_class": has_class,
        "has_loops": has_loops,
        "has_training_keyword": has_training_keyword,
        "estimated_hours": hours,
        "estimated_difficulty": difficulty,
        "estimated_experiment_type": exp_type,
    }


# ============================================================
# 主入口
# ============================================================

def extract(course_id: str, exp_id: int, source_path: Path) -> dict[str, Any]:
    """提取一个实验源码目录的能力。"""
    if not source_path.exists():
        raise FileNotFoundError(f"源码目录不存在: {source_path}")

    py_files = find_python_files(source_path)
    if not py_files:
        # 没有 .py 文件，可能完全没源码
        return {
            "course_id": course_id,
            "experiment_id": exp_id,
            "extracted_at": datetime.now().isoformat(timespec="seconds"),
            "source_path": str(source_path),
            "status": "no_python_files",
            "experiment_name_candidates": [],
            "tech_stack": [],
            "metrics": {},
        }

    # === experiment_name 候选 ===
    name_candidates = []

    # 候选1: _meta.yaml
    meta = find_meta_yaml(source_path)
    if meta and "experiment_name" in meta:
        name_candidates.append({
            "value": meta["experiment_name"],
            "source": "_meta.yaml",
            "confidence": 1.0,
        })

    # 候选2: README.md H1
    readme_h1 = find_readme_h1(source_path)
    if readme_h1:
        name_candidates.append({
            "value": readme_h1,
            "source": "README.md H1",
            "confidence": 0.85,
        })

    # 候选3: 主入口文件 docstring
    main_entry = None
    for f in py_files:
        if f.name in ("main.py",) or f.name.startswith("demo_"):
            main_entry = f
            doc = extract_main_docstring(f)
            if doc:
                name_candidates.append({
                    "value": doc,
                    "source": f"{f.name} docstring",
                    "confidence": 0.75,
                })
            break

    # 候选4: 文件名
    if name_candidates == []:
        fn_name = filename_to_name(py_files)
        if fn_name:
            name_candidates.append({
                "value": fn_name,
                "source": "filename",
                "confidence": 0.5,
            })

    # === tech_stack ===
    requirements = parse_requirements(source_path / "requirements.txt")
    tech_stack, tech_sources = extract_tech_stack(py_files, requirements)

    # === 关键函数 ===
    key_functions = []
    if main_entry:
        key_functions = extract_key_functions(main_entry, max_n=5)

    # === 复杂度估算 ===
    metrics = estimate_complexity(py_files, requirements)

    return {
        "course_id": course_id,
        "experiment_id": exp_id,
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "source_path": str(source_path),
        "status": "ok",
        "main_entry": main_entry.name if main_entry else None,
        "experiment_name_candidates": name_candidates,
        "tech_stack": tech_stack,
        "tech_stack_source": tech_sources,
        "requirements": requirements,
        "key_functions": key_functions,
        "metrics": {
            k: v for k, v in metrics.items()
            if not k.startswith("estimated_")
        },
        "estimated_hours": metrics["estimated_hours"],
        "estimated_difficulty": metrics["estimated_difficulty"],
        "estimated_experiment_type": metrics["estimated_experiment_type"],
    }


def main():
    parser = argparse.ArgumentParser(description="从源码目录提取能力，用于反向同步 CSV")
    parser.add_argument("--course", required=True, help="课程 ID（如 EXP001）")
    parser.add_argument("--exp", type=int, required=True, help="实验编号（如 4）")
    parser.add_argument("--source-path", help="源码目录路径（默认从 CSV 推断）")
    parser.add_argument("--csv", default="input/course_spec.csv", help="CSV 路径")
    parser.add_argument("--output", help="输出 JSON 路径（默认 stdout）")
    args = parser.parse_args()

    # 推断 source_path
    if args.source_path:
        sp = Path(args.source_path)
    else:
        # 默认: source-codes/exp{NN}/
        sp = Path(f"source-codes/exp{args.exp:02d}")

    try:
        result = extract(args.course, args.exp, sp)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"[extract_capabilities] wrote {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
