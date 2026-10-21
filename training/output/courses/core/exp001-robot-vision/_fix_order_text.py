# -*- coding: utf-8 -*-
"""
修正 12 页里与"顺序"相关的文案：
  1. pathline 进度条：按新顺序重排，高亮当前
  2. exp-head 里的"篇/章"描述：第 N 章 → 对应阶段
  3. 页脚"基于 vision/NN_*"字样：核对源码目录号
"""
import io
import os
import re

W = r"E:\Source\xflz_eai_car1\course_generate_agent\training\output\courses\core\exp001-robot-vision"

# 新序号 -> (目录, 短名, 源码目录号)
PLAN = [
    (1,  "exp-01-color-hsv",             "颜色",     "03"),
    (2,  "exp-02-qrcode",                "二维码",   "04"),
    (3,  "exp-03-contour-polygon",       "轮廓",     "05"),
    (4,  "exp-04-industrial-defect",     "检测",     "01"),
    (5,  "exp-05-garbage-classification","分类",     "02"),
    (6,  "exp-06-semantic-segmentation", "分割",     "06"),
    (7,  "exp-07-deepsort-tracking",     "跟踪",     "07"),
    (8,  "exp-08-face-landmarks",        "人脸",     "09"),
    (9,  "exp-09-pose-landmark",         "骨骼",     "10"),
    (10, "exp-10-depth-3d",              "3D",       "08"),
    (11, "exp-11-pose-control",          "体感",     "11"),
    (12, "exp-12-hand-control",          "手势",     "12"),
]

# 阶段归属（用于 exp-head 里的"第 N 章"）
STAGE = {
    1: "第 1 阶段 · 传统视觉",
    2: "第 1 阶段 · 传统视觉",
    3: "第 1 阶段 · 传统视觉",
    4: "第 2 阶段 · 目标检测与分类",
    5: "第 2 阶段 · 目标检测与分类",
    6: "第 3 阶段 · 语义分割",
    7: "第 3 阶段 · 多目标跟踪",
    8: "第 4 阶段 · 人体感知",
    9: "第 4 阶段 · 人体感知",
    10: "第 4 阶段 · 人体感知",
    11: "第 5 阶段 · 视觉控制",
    12: "第 5 阶段 · 视觉控制",
}


def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def build_pathline(cur):
    parts = []
    for n, _d, short, _s in PLAN:
        if n == cur:
            parts.append('<span class="cur">%02d %s</span>' % (n, short))
        else:
            parts.append("<span>%02d %s</span>" % (n, short))
    return '<div class="pathline">\n  ' + "".join(parts) + "\n</div>"


def main():
    for new_no, d, short, srcno in PLAN:
        p = os.path.join(W, d, "index.html")
        html = read(p)
        orig = html

        # ---- 1. pathline 重建 ----
        html = re.sub(r'<div class="pathline">.*?</div>',
                      build_pathline(new_no), html, count=1, flags=re.S)

        # ---- 2. exp-head 的 code 行：把"第 N 篇/章"换成阶段名 ----
        def fix_code(m):
            inner = m.group(1)
            # 去掉已有的"第 x 篇/章 ..."片段
            inner = re.sub(r'第\s*\d+\s*[篇章][^·]*·\s*', '', inner)
            return '<span class="code">%s · %s</span>' % (
                inner.split(" · ")[0], STAGE[new_no]) + ""
        # 更稳妥：直接重构 code 行
        cm = re.search(r'<span class="code">EXP-\d+ · (.*?)</span>', html)
        if cm:
            rest = cm.group(1)
            rest = re.sub(r'^第\s*\d+\s*[篇章][^·]*·\s*', '', rest)
            html = re.sub(r'<span class="code">EXP-\d+ · .*?</span>',
                          '<span class="code">EXP-%02d · %s · %s</span>'
                          % (new_no, STAGE[new_no], rest), html, count=1)

        # ---- 3. 页脚源码目录号核对 ----
        html = re.sub(r'vision/(\d{2}_[a-z0-9_]+)', 'vision/\\1', html)

        if html != orig:
            write(p, html)
            print("  已更新 EXP-%02d %s" % (new_no, d))
        else:
            print("  无变化 EXP-%02d %s" % (new_no, d))


if __name__ == "__main__":
    main()
