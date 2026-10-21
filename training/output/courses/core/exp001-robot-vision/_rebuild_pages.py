# -*- coding: utf-8 -*-
"""
按新学习顺序生成 12 个实验页面（幂等）。

关键：编号只做【一次】全局映射，之后再写标题/面包屑/导航都直接写目标值，
      避免"新编号被当旧编号再映射一遍"这类链式错误。

归档页面的 EXP 编号 == 其旧目录序号（已核实 1:1），因此：
    old_no -> new_no 使用 OLD2NEW
"""
import io
import os
import re

W = r"E:\Source\xflz_eai_car1\course_generate_agent\training\output\courses\core\exp001-robot-vision"
OLD = os.path.join(W, "_build_archive", "v2_before_reorder")

# 新序号 -> (新目录, 旧目录, 短标题, 主题色四元组)
PLAN = [
    (1,  "exp-01-color-hsv",             "exp-03-lab-color-recognition",  "颜色识别",     ("#d97706", "#b45309", "#fef3c7", "#fde68a")),
    (2,  "exp-02-qrcode",                "exp-04-qrcode",                 "二维码",       ("#7c3aed", "#6d28d9", "#ede9fe", "#ddd6fe")),
    (3,  "exp-03-contour-polygon",       "exp-05-line-following",         "多边形轮廓",   ("#059669", "#047857", "#d1fae5", "#a7f3d0")),
    (4,  "exp-04-industrial-defect",     "exp-01-industrial-defect",      "工业缺陷检测", ("#0d9488", "#0f766e", "#ccfbf1", "#99f6e4")),
    (5,  "exp-05-garbage-classification","exp-02-garbage-classification", "垃圾分类",     ("#2563eb", "#1d4ed8", "#dbeafe", "#bfdbfe")),
    (6,  "exp-06-semantic-segmentation", "exp-06-semantic-segmentation",  "语义分割",     ("#7c3aed", "#6d28d9", "#ede9fe", "#ddd6fe")),
    (7,  "exp-07-deepsort-tracking",     "exp-07-deepsort-tracking",      "多目标跟踪",   ("#e11d48", "#be123c", "#ffe4e6", "#fecdd3")),
    (8,  "exp-08-face-landmarks",        "exp-09-face-landmarks",         "人脸关键点",   ("#db2777", "#be185d", "#fce7f3", "#fbcfe8")),
    (9,  "exp-09-pose-landmark",         "exp-10-pose-landmark",          "骨骼关键点",   ("#4f46e5", "#4338ca", "#e0e7ff", "#c7d2fe")),
    (10, "exp-10-depth-3d",              "exp-08-depth-3d-detection",     "深度 3D",      ("#0891b2", "#0e7490", "#cffafe", "#a5f3fc")),
    (11, "exp-11-pose-control",          "exp-11-pose-control",           "体感控制",     ("#ea580c", "#c2410c", "#ffedd5", "#fed7aa")),
    (12, "exp-12-hand-control",          "exp-12-hand-control",           "手势识别",     ("#0f766e", "#115e59", "#ccfbf1", "#99f6e4")),
]

# 旧序号 -> 新序号
OLD2NEW = {3: 1, 4: 2, 5: 3, 1: 4, 2: 5, 6: 6, 7: 7, 9: 8, 10: 9, 8: 10, 11: 11, 12: 12}
OLDDIR2NEW = {p[2]: p[1] for p in PLAN}
NEWDIR_INFO = {p[0]: p for p in PLAN}


def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def build_sidebar(cur):
    out = ["  <h4>本课程实验</h4>"]
    for n, d, _o, short, _c in PLAN:
        style = ' style="color:#0f766e;font-weight:700"' if n == cur else ""
        out.append('  <a href="../%s/index.html"%s>EXP-%02d %s</a>' % (d, style, n, short))
    return "\n".join(out)


def main():
    for new_no, newdir, olddir, short, colors in PLAN:
        src = os.path.join(OLD, olddir, "index.html")
        if not os.path.exists(src):
            raise SystemExit("归档缺失: " + src)
        html = read(src)

        # ========== 第 1 步：全局一次性重编号（唯一一次） ==========
        # 先占位，再还原，确保新号不会被二次映射
        html = re.sub(
            r'EXP-(\d{2})\b',
            lambda m: ("\x01N%02d\x01" % OLD2NEW[int(m.group(1))])
            if int(m.group(1)) in OLD2NEW else m.group(0),
            html)
        html = re.sub(r'\x01N(\d{2})\x01', lambda m: "EXP-" + m.group(1), html)

        # ========== 第 2 步：链接改到新目录 ==========
        html = re.sub(
            r'\.\./(exp-[a-z0-9-]+)/index\.html',
            lambda m: "../%s/index.html" % OLDDIR2NEW[m.group(1)]
            if m.group(1) in OLDDIR2NEW else m.group(0),
            html)

        # ========== 第 3 步：标题 / code / 面包屑 强制写成目标值 ==========
        html = re.sub(r'<title>EXP-\d+ ', '<title>EXP-%02d ' % new_no, html, count=1)
        html = re.sub(r'(<span class="code">)EXP-\d+', r'\g<1>EXP-%02d' % new_no, html, count=1)
        html = re.sub(r'(/ <a href="\.\./index\.html">[^<]*</a> / )EXP-\d+',
                      r'\g<1>EXP-%02d' % new_no, html, count=1)

        # ========== 第 4 步：侧栏整块重建 ==========
        html = re.sub(r'  <h4>(?:全部实验|本课程实验)</h4>\n(?:  <a [^\n]*\n)+',
                      build_sidebar(new_no) + "\n", html, count=1)

        # ========== 第 5 步：主题色 ==========
        c1, c2, c3, c4 = colors
        html = re.sub(
            r':root\{--theme:#[0-9a-fA-F]{6};--theme-deep:#[0-9a-fA-F]{6};'
            r'--theme-bg:#[0-9a-fA-F]{6};--theme-bd:#[0-9a-fA-F]{6}\}',
            ':root{--theme:%s;--theme-deep:%s;--theme-bg:%s;--theme-bd:%s}' % (c1, c2, c3, c4),
            html, count=1)

        # ========== 第 6 步：上下页导航 ==========
        if new_no > 1:
            p = NEWDIR_INFO[new_no - 1]
            prev = ('  <a href="../%s/index.html"><span class="lb">← 上一个</span>'
                    'EXP-%02d %s</a>' % (p[1], p[0], p[3]))
        else:
            prev = ('  <a href="../index.html"><span class="lb">← 返回</span>'
                    '课程目录 · 视觉应用与开发</a>')
        if new_no < 12:
            n = NEWDIR_INFO[new_no + 1]
            nxt = ('  <a class="next" href="../%s/index.html"><span class="lb">下一个实验 →</span>'
                   'EXP-%02d %s</a>' % (n[1], n[0], n[3]))
        else:
            nxt = ('  <a class="next" href="../index.html"><span class="lb">已完成 12/12 →</span>'
                   '返回课程目录</a>')
        html, n_nav = re.subn(r'<nav class="expnav">.*?</nav>',
                              '<nav class="expnav">\n%s\n%s\n</nav>' % (prev, nxt),
                              html, count=1, flags=re.S)
        if n_nav != 1:
            print("    ! 导航未匹配: " + newdir)

        # ========== 第 7 步：页脚编号 ==========
        html = re.sub(r'(· )EXP-\d+( )', r'\g<1>EXP-%02d\g<2>' % new_no, html, count=1)

        outdir = os.path.join(W, newdir)
        os.makedirs(outdir, exist_ok=True)
        write(os.path.join(outdir, "index.html"), html)
        print("  EXP-%02d  %-30s <- %s" % (new_no, newdir, olddir))


if __name__ == "__main__":
    main()
