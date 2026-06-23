#!/usr/bin/env bash
# .githooks/_lib_csv_drift.sh
#
# 共享库：检测 input/course_spec.csv 与课程 spec.yaml 的漂移。
# 被 post-checkout / post-merge / pre-commit 复用。
#
# 行为：
#   1. 若 csv 不存在 → 静默退出 0
#   2. 若所有 course-spec.yaml 都不存在 → 提示 "首次生成"
#   3. 否则对每个 course-spec.yaml 调 diff.py，将 exit 1 的项汇总并打印指引
#
# 退出码：
#   0 = 一致 / 跳过
#   1 = 检测到漂移（hook 上下文按需决定阻塞与否）
#   2 = 工具不可用（缺 python / diff.py）

set -u

CSV_PATH="input/course_spec.csv"
DIFF_TOOL=".claude/skills/spec-parser-skill/diff.py"

# 颜色（仅 TTY）
if [ -t 1 ]; then
  C_RED=$'\033[31m'; C_YELLOW=$'\033[33m'; C_GREEN=$'\033[32m'
  C_CYAN=$'\033[36m'; C_BOLD=$'\033[1m'; C_RESET=$'\033[0m'
else
  C_RED=""; C_YELLOW=""; C_GREEN=""; C_CYAN=""; C_BOLD=""; C_RESET=""
fi

log_info()    { printf "%s[csv-drift]%s %s\n" "$C_CYAN" "$C_RESET" "$1"; }
log_warn()    { printf "%s[csv-drift]%s %s\n" "$C_YELLOW" "$C_RESET" "$1"; }
log_block()   { printf "%s[csv-drift]%s %s%s%s\n" "$C_RED" "$C_RESET" "$C_BOLD" "$1" "$C_RESET"; }
log_ok()      { printf "%s[csv-drift]%s %s\n" "$C_GREEN" "$C_RESET" "$1"; }

# 主入口
csv_drift_check() {
  local context="${1:-}"  # "post-checkout" / "post-merge" / "pre-commit"

  if [ ! -f "$CSV_PATH" ]; then
    return 0  # 没有 csv，跳过
  fi

  if [ ! -f "$DIFF_TOOL" ]; then
    log_warn "diff 工具未安装: $DIFF_TOOL — 跳过"
    return 2
  fi

  if ! command -v python >/dev/null 2>&1; then
    log_warn "未找到 python — 跳过 csv 漂移检测"
    return 2
  fi

  local yaml_files
  yaml_files=$(find courses -type f -name "course-spec.yaml" 2>/dev/null || true)

  if [ -z "$yaml_files" ]; then
    log_info "尚无 course-spec.yaml — 视为首次生成，无需 diff"
    log_info "→ 运行 \`python $DIFF_TOOL\` 或对话框输入 \`生成课程\`"
    return 0
  fi

  local drifted=()
  local errored=()

  while IFS= read -r yml; do
    [ -z "$yml" ] && continue

    # 从 yaml 路径反推 course_id
    # yaml 路径格式：courses/{sheet}/{folder}/_meta/course-spec.yaml
    # 读取 yaml 第一行 "course_code: EXPNNN" 提取 course_id
    local course_id
    course_id=$(grep -m1 '^course_code:' "$yml" 2>/dev/null | sed 's/^course_code:[[:space:]]*//')
    if [ -z "$course_id" ]; then
      errored+=("$yml (无法读取 course_code)")
      continue
    fi

    # 多课程 CSV 必须传 --course 参数
    PYTHONIOENCODING=utf-8 python "$DIFF_TOOL" --course "$course_id" "$CSV_PATH" -y "$yml" --format json \
      >/dev/null 2>&1
    local rc=$?
    case "$rc" in
      0) ;;
      1) drifted+=("$yml ($course_id)") ;;
      2) errored+=("$yml ($course_id)") ;;
      *) errored+=("$yml ($course_id)") ;;
    esac
  done <<< "$yaml_files"

  if [ ${#errored[@]} -gt 0 ]; then
    log_warn "csv 解析失败，无法 diff —— 检查 $CSV_PATH 字段格式"
    for f in "${errored[@]}"; do
      log_warn "  vs $f"
    done
  fi

  if [ ${#drifted[@]} -eq 0 ] && [ ${#errored[@]} -eq 0 ]; then
    log_ok "csv 与所有 course-spec.yaml 一致"
    return 0
  fi

  if [ ${#drifted[@]} -gt 0 ]; then
    log_block "检测到 ${#drifted[@]} 份课程的 spec 与 csv 不一致："
    for f in "${drifted[@]}"; do
      printf "  - %s\n" "$f"
    done
    echo
    case "$context" in
      pre-commit)
        log_warn "建议提交前先同步 spec 与下游文档："
        ;;
      post-checkout|post-merge|*)
        log_warn "csv 已变更，下游文档与 spec 已陈旧。建议执行："
        ;;
    esac
    cat <<EOF

  ${C_BOLD}方案 A — 仅重新生成 spec.yaml（轻，逐课程）${C_RESET}
    # 替换 <COURSE_ID> 为上方列出的课程 ID（如 EXP001）
    python $DIFF_TOOL --course <COURSE_ID> --format text   # 查看变更摘要
    python .claude/skills/spec-parser-skill/parser.py --course <COURSE_ID>
    python .claude/skills/spec-parser-skill/validator.py --course <COURSE_ID>

  ${C_BOLD}方案 B — 同步下游文档（推荐）${C_RESET}
    在 Claude Code 对话中运行：
      /incremental-update --course <COURSE_ID> --from-csv
    或自然语言：
      我改了 csv，请同步 <课程名>

EOF
    return 1
  fi

  return 2
}
