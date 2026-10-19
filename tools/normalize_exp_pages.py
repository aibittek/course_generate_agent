# -*- coding: utf-8 -*-
"""把实验页的顶栏 / 侧栏标题统一到 shared/tutorial.css 的规范。

只做三件确定的事，其余内容一律不动：
  1. 顶栏整块替换成规范版本（只保留 EXP 编号不同）
  2. <p class="crumb"> → 合并进顶栏后删除
  3. <div class="stitle">...</div> → <h4>...</h4>

用法：python tools/normalize_exp_pages.py [--dry]
"""
import io
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "training", "output", "courses", "core", "exp005-robot-arm")

TOPBAR = """<div class="topbar">
  <a class="logo" href="../../../index.html" style="text-decoration:none;color:inherit" title="返回课程首页">🤖 具身智能课程 · <i>教程首页</i></a>
  <div class="crumb"><a href="../../../index.html#core">核心课程</a> / <a href="../index.html">机械臂应用与开发</a> / {exp}</div>
</div>"""


def main():
    dry = "--dry" in sys.argv
    changed = []
    for name in sorted(os.listdir(ROOT)):
        if not name.startswith("exp-"):
            continue
        path = os.path.join(ROOT, name, "index.html")
        if not os.path.exists(path):
            continue
        src = io.open(path, encoding="utf-8").read()
        exp = name[:6].upper().replace("-", "-")   # exp-04 → EXP-04
        exp = "EXP-" + name.split("-")[1]
        out = src
        notes = []

        # 1. 顶栏整块替换
        m = re.search(r'<div class="topbar">.*?</div>\s*(?=<p class="crumb"|<div class="wrap"|<div class="crumb")',
                      out, re.S)
        if m:
            out = out[:m.start()] + TOPBAR.format(exp=exp) + "\n\n" + out[m.end():]
            notes.append("topbar")
        # 2. 独立的面包屑段落
        m2 = re.search(r'<p class="crumb">.*?</p>\s*', out, re.S)
        if m2:
            out = out[:m2.start()] + out[m2.end():]
            notes.append("p.crumb")
        # 3. 侧栏标题
        n3 = len(re.findall(r'<div class="stitle">(.*?)</div>', out, re.S))
        if n3:
            out = re.sub(r'<div class="stitle">(.*?)</div>', r"<h4>\1</h4>", out, flags=re.S)
            notes.append("stitle x%d" % n3)

        if out != src:
            changed.append((name, notes))
            if not dry:
                io.open(path, "w", encoding="utf-8").write(out)

    for name, notes in changed:
        print("%-24s %s" % (name, ", ".join(notes)))
    print("共 %d 个页面%s" % (len(changed), "（dry run，未写入）" if dry else "已更新"))
    return changed


if __name__ == "__main__":
    main()
