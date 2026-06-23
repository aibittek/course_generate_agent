#!/usr/bin/env bash
# .githooks/install.sh
# 一键启用本仓库内的 git hooks（设置 core.hooksPath）。
# 用法：bash .githooks/install.sh
set -e

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[install] 当前不在 git 仓库内" >&2
  exit 1
fi

git config core.hooksPath .githooks
echo "[install] core.hooksPath = .githooks"

# 给 hooks 加可执行位（Windows 上 git 不依赖文件权限，但 Linux/Mac 需要）
chmod +x .githooks/post-checkout .githooks/post-merge .githooks/pre-commit \
         .githooks/_lib_csv_drift.sh 2>/dev/null || true

echo "[install] 已启用 csv 漂移检测 hooks："
echo "  - post-checkout : 切分支时检测 csv 变更"
echo "  - post-merge    : pull/merge 后检测 csv 变更"
echo "  - pre-commit    : 提交前检测 csv 与 spec 不同步（默认非阻塞）"
echo
echo "[install] 卸载: git config --unset core.hooksPath"
echo "[install] 阻塞模式: STRICT_CSV_DRIFT=1 git commit ..."
