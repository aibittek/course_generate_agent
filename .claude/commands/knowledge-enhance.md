# 知识点增强命令

将实验指导书中的知识点讲解升级为四层增强版（白话类比→是什么→为什么→怎么用），补充公式（Typora LaTeX）、Mermaid 流程图与图片占位符指引。输出到独立 v2 目录，**不修改原文件**。

## 使用方式

```
/knowledge-enhance --course EXP001 --experiment 3
/knowledge-enhance --course EXP001 --experiment 3 --source-doc <path> --source-root <path>
/knowledge-enhance --align --experiment 3     # 直接对齐既有 _parts 文档（不生成 v2，就地改）
```

## 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--course` | ✅ | 课程编号（如 EXP001） |
| `--experiment` | ✅ | 实验编号（如 3，对应 `_parts/experiment-3.md`） |
| `--source-doc` | 可选 | 原文档路径（默认 `courses/sheet1/{course_folder}/_parts/experiment-{N}.md`） |
| `--source-root` | 可选 | 源码根路径（默认 `ros2_ws/src/xflz_eai_car1/vision/` 自动匹配实验目录） |
| `--align` | 可选 | 切到「直接对齐编辑」模式（skill 七.c）：就地改 `_parts` 原文件，不做 v2 增强；加 Mermaid 流程图 + 路径 `~`/PYTHONPATH 统一 + 合成命令 + 配置参数速查表 |

## 命令逻辑

1. **加载技能**：读取 `.claude/skills/knowledge-point-enhancement/SKILL.md`（方法论）
2. **加载 agent**：读取 `.claude/agents/knowledge-point-enhancer.md`（执行者）
3. **解析课程目录**：从 `_meta/course-spec.yaml` 或知识图谱 front matter 获取 `course_folder`（如 `robot_vision`）
4. **定位源码**：从 `_meta/course-spec.yaml` 的 `experiments[]` 中按 `experiment_id` 取 `source_code_path`
5. **派发执行**：按 agent 的 Step1-4 流程——读原文档/知识图谱/源码 → 生成增强版 → 自检 → 汇报
6. **命令可执行性验证（必做）**：生成后核对原文档每条 CLI 命令/Flag 对照 `src/app.py` argparse 真实存在；本地 x86 可跑的命令已实跑确认；虚构/失效命令（如 exp05 `--dark`、exp04 整图多码）已修正为真实 API 用法；单测覆盖描述与 `tests/*.py` 一致
7. **输出位置**：`courses/sheet1/{course_folder}_v2/_parts/experiment-{N}.md`（目录不存在则创建，含 `assets/`）
8. **汇报**：输出文件路径、增强点清单、图片占位符清单（待用户补充截图）、发现的命令修正项

**`--align` 模式流程**（直接对齐，调 skill 七.c + agent 模式B）：
1. 加载 skill + agent，定位 `_parts/experiment-{N}.md`
2. 按七.c 对齐清单：每步补 Mermaid 图 → 路径 `~`/`PYTHONPATH:$PYTHONPATH` → 合成命令（`rknn23` 实跑）→ 步骤1 配置参数速查表（`load_config()` 实跑核对）→ 更新日志追加 v2.1
3. **就地写回原文件**（此模式允许；非 `--align` 走 v2 目录）

## 示例

```
/knowledge-enhance --course EXP001 --experiment 3
```

预期输出：
```
✅ 已生成增强版: courses/sheet1/robot_vision_v2/_parts/experiment-3.md (xxx 行)

增强点:
- 新增 4 个公式（HSV转换/inRange掩膜/开闭运算/最小外接圆）
- 新增 2 个 Mermaid 流程图
- 新增 5 个图片占位符（含截图指引）

图片占位符清单（待补充）:
1. assets/exp03-red-detect.png  — 红色检测双栏效果图
2. assets/exp03-h2-compare.png  — h2 双段掩膜对比图
...
```

## 注意

- 命令需用户显式触发（非默认加载）
- 原文件 `_parts/experiment-{N}.md` 只读，任何情况下不修改
- **命令验证不可省**：文档里每条 CLI 命令都先对照源码 argparse 核实、本地可跑的先实跑，禁止照抄可能已失效的旧命令（历史教训：`--dark` 不存在、整图多码不可行、单测无多码用例）
- **路径规范**：`cd ~/ros2_ws/...`（带 `~`）、`python -c` 前加 `PYTHONPATH=./src`
- **Mermaid 可读性**：横向节点 ≤6；串行管线多节点改 `TD`，防字体过小
- 生成后请运行自检清单（skill 第八节）确认公式/图/占位符完整
