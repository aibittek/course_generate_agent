# .githooks — CSV 漂移检测 hooks（Phase 3）

`input/course_spec.csv` 是课程内容的唯一可信源。当它发生变更，下游的 `course-spec.yaml` 与 4 份课程文档可能进入陈旧状态。本目录的 git hooks 在常见 git 操作时自动检测这种漂移并打印同步指引。

## 一键启用

```bash
# Linux / Mac / Git Bash on Windows
bash .githooks/install.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .githooks\install.ps1
```

启用后 `git config core.hooksPath` 被指向 `.githooks/`，仓库内的 hooks 即生效。

## hook 触发场景

| Hook | 触发时机 | 行为 |
|------|---------|------|
| `post-checkout` | `git checkout` / `git switch` 分支切换 | 若 csv 在两个分支间不同 → 打印 diff 摘要与同步指引（不阻塞） |
| `post-merge` | `git merge` / `git pull` | 若本次 merge 改了 csv → 打印同步指引（不阻塞） |
| `pre-commit` | `git commit` | 若暂存区动了 csv 但没同步 spec.yaml → 警告（默认不阻塞） |

## 模式开关

| 环境变量 | 作用 |
|---------|------|
| `STRICT_CSV_DRIFT=1` | pre-commit 检测到漂移时**拒绝提交**（默认仅警告） |

## 检测到漂移后的指引

hook 会输出两条候选路径：

**方案 A — 仅重生成 spec.yaml（轻）**

```bash
python .claude/skills/spec-parser-skill/diff.py --format text     # 看变更
python .claude/skills/spec-parser-skill/parser.py                  # 重写 spec
python .claude/skills/spec-parser-skill/validator.py               # 校验
```

**方案 B — 同步下游 4 份文档（推荐）**

在 Claude Code 对话中：

```
/incremental-update --from-csv
```

或自然语言：`我改了 csv，请同步课程`

底层走 `IncrementalUpdateAgent` 的模式 0：基于 `diff.py` 的字段级 delta 决定回放范围（仅 `hours` 变 → 只更 syllabus；`source_code_path` 变 → 强制重跑源码 HOOK）。

## 卸载

```bash
git config --unset core.hooksPath
```

## 文件清单

| 文件 | 作用 |
|------|------|
| `_lib_csv_drift.sh` | 共享检测库（被 3 个 hook 复用） |
| `post-checkout` | 分支切换检测 |
| `post-merge` | merge / pull 检测 |
| `pre-commit` | 提交时检测 |
| `install.sh` / `install.ps1` | 一键启用 |
| `README.md` | 本文档 |

## 设计原则

1. **hooks 自身不修改文件**——只检测、提示。所有写操作必须经 IncrementalUpdateAgent 路径。
2. **不依赖外部包**——shell + 项目内 python 工具即可运行。
3. **跨平台**——POSIX sh 兼容 Git Bash on Windows / Linux / Mac。
4. **默认非阻塞**——避免对常规 git 操作产生阻碍；阻塞模式 opt-in。
5. **快速短路**——若 csv 未变 / yaml 不存在 / 工具缺失，立即静默返回 0。
