# -*- coding: utf-8 -*-
"""
课程重排脚本（幂等，可重复运行）。

新学习顺序（方案A：OpenCV 先行，由易到难）：
  旧 -> 新
  3 颜色识别      ->  1
  4 二维码        ->  2
  5 多边形轮廓    ->  3
  1 缺陷检测      ->  4
  2 垃圾分类      ->  5
  6 语义分割      ->  6
  7 多目标跟踪    ->  7
  9 人脸关键点    ->  8
  10 骨骼关键点   ->  9
  8 深度3D        ->  10
  11 体感控制     ->  11
  12 手势识别     ->  12

源码目录 vision/NN_* 保持仓库交付号不变，课程里的"实验N"是学习序号。
"""
import io
import os
import re
import shutil

ROOT = r"E:\Source\xflz_eai_car1\course_generate_agent\courses\sheet1\robot_vision"
PARTS = os.path.join(ROOT, "_parts")
BACKUP = os.path.join(ROOT, "_parts_backup_before_reorder")

OLD2NEW = {3: 1, 4: 2, 5: 3, 1: 4, 2: 5, 6: 6, 7: 7, 9: 8, 10: 9, 8: 10, 11: 11, 12: 12}
NEW2OLD = {v: k for k, v in OLD2NEW.items()}

SRC = {
    1: "01_industrial_defect_detection",
    2: "02_garbage_classification",
    3: "03_lab_color_recognition",
    4: "04_qrcode",
    5: "05_line_following",
    6: "06_semantic_segmentation",
    7: "07_multi_object_tracking",
    8: "08_depth_3d_detection",
    9: "09_face_landmarks",
    10: "10_pose_landmark",
    11: "11_pose_control",
    12: "12_hand_control",
}

# 新序号 -> (标题, 难度, 类型)
META = {
    1: ("基于HSV色彩空间的颜色识别实验", "⭐", "验证性"),
    2: ("二维码生成与识别检测实验", "⭐", "验证性"),
    3: ("基于OpenCV的多边形轮廓拟合实验", "⭐⭐", "设计性"),
    4: ("基于YOLOv8的工业表面缺陷检测实验", "⭐⭐", "综合性"),
    5: ("基于图像分类的垃圾分类实验", "⭐⭐", "设计性"),
    6: ("基于语义分割的背景分割实验", "⭐⭐", "设计性"),
    7: ("基于DeepSORT的多目标跟踪实验", "⭐⭐⭐", "综合性"),
    8: ("基于人脸关键点特征检测实验", "⭐⭐", "设计性"),
    9: ("基于骨骼关键点的肢体检测实验", "⭐⭐", "设计性"),
    10: ("基于深度信息的3D物体检测实验", "⭐⭐", "设计性"),
    11: ("基于肢体动作的体感控制实验", "⭐⭐⭐", "综合性"),
    12: ("基于手指动作的控制实验", "⭐⭐", "设计性"),
}

PATH_RE = re.compile(
    r"(?:vision/)?\d{2}_(?:industrial_defect_detection|garbage_classification|"
    r"lab_color_recognition|qrcode|line_following|semantic_segmentation|"
    r"multi_object_tracking|depth_3d_detection|face_landmarks|pose_landmark|"
    r"pose_control|hand_control)"
)


def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def protect(text):
    """把源码路径换成占位符，返回 (新文本, 原路径列表)。"""
    store = []

    def sub(m):
        store.append(m.group(0))
        return "\x02P%d\x02" % (len(store) - 1)

    return PATH_RE.sub(sub, text), store


def unprotect(text, store):
    return re.sub(r"\x02P(\d+)\x02", lambda m: store[int(m.group(1))], text)


def renum(text):
    """把文本里所有 '实验N' 按 OLD2NEW 重编号，路径受保护。"""
    t, store = protect(text)

    def to_ph(m):
        num = int(m.group(1))
        if num in OLD2NEW:
            return "\x00X%d\x00" % OLD2NEW[num]
        return m.group(0)

    t = re.sub(r"实验0?(\d{1,2})(?!\d)", to_ph, t)
    t = re.sub(r"\x00X(\d+)\x00", lambda m: "实验" + str(int(m.group(1))), t)
    return unprotect(t, store)


def main():
    # ---------- 0. 备份（仅在首次运行时做） ----------
    if not os.path.exists(BACKUP):
        shutil.copytree(PARTS, BACKUP)
        print("[0] 已备份 _parts -> _parts_backup_before_reorder")
    else:
        shutil.rmtree(PARTS)
        shutil.copytree(BACKUP, PARTS)
        print("[0] 已从备份还原 _parts，重新执行")

    # ---------- 1. 读旧 part ----------
    texts = {}
    for old in range(1, 13):
        texts[old] = read(os.path.join(PARTS, "experiment-%d.md" % old))

    # ---------- 2. 重编号（正文引用） ----------
    for old in texts:
        texts[old] = renum(texts[old])

    # ---------- 3. 改写标题行 + 写回新文件名 ----------
    for old, txt in texts.items():
        new = OLD2NEW[old]
        title = META[new][0]
        nl = txt.find("\n")
        head, body = txt[:nl], txt[nl:]
        newhead = "## 实验%d：%s（4h）" % (new, title)
        write(os.path.join(PARTS, "experiment-%d.md" % new), newhead + body)
    print("[3] 已按新序号重写 _parts/experiment-1..12.md（含标题与内部引用）")

    # ---------- 4. 重构主指导书 ----------
    #      做法：用新顺序拼接 == 头部(到"实验总览"之前) + 总览表 + 12 篇正文
    guide_path = os.path.join(ROOT, "EXP001_lab_guide.md")
    g = read(guide_path)

    # 头部：到 "## 实验总览" 为止（不含）
    m = re.search(r"^## 实验总览", g, flags=re.M)
    if not m:
        raise SystemExit("找不到 '## 实验总览'")
    header = g[:m.start()]

    # 重建目录（原目录按旧序、锚点也是旧号，必须整体重写）
    def anchor(title):
        s = title.lower()
        s = re.sub(r"[^\w\u4e00-\u9fff]+", "", s)
        return "#" + s

    toc_lines = []
    for new in range(1, 13):
        title = META[new][0]
        toc_lines.append("- [实验%d：%s](%s)" % (new, title, anchor("实验%d%s" % (new, title))))
    toc = "## 目录\n\n" + "\n".join(toc_lines) + "\n\n---\n\n"

    # 用新目录替换旧目录块：从 "## 目录" 起，到 "## 实验总览" 之前，整段重写
    i_toc = header.find("## 目录")
    i_ov = header.find("## 实验总览")
    if i_toc == -1:
        raise SystemExit("找不到 '## 目录'")
    if i_ov != -1 and i_ov < i_toc:
        raise SystemExit("'## 实验总览' 出现在 '## 目录' 之前，结构异常")
    header = header[:i_toc] + toc + header[i_ov if i_ov != -1 else len(header):]
    print("[4a] 已重建目录（新顺序 + 正确锚点）")

    # 尾部：每篇末尾可能带 "## 更新日志" 块，原文件最后一个更新日志之后的内容保留
    tail = ""
    last_log = g.rfind("\n## 更新日志")
    if last_log != -1:
        # 取最后一个更新日志之后的内容（通常是空或文件尾注）
        seg = g[last_log:]
        lines = seg.split("\n")
        # 找该更新日志表格结束后的第一行非表格内容
        idx = 0
        for i, ln in enumerate(lines):
            if i > 2 and ln.strip() and not ln.strip().startswith("|") and not ln.startswith("#"):
                idx = i
                break
        if idx:
            tail = "\n".join(lines[idx:])

    # 总览表
    rows = []
    for new in range(1, 13):
        old = NEW2OLD[new]
        title, star, typ = META[new]
        rows.append(
            "| 实验%d | %s | 4h | %s | %s | `ros2_ws/src/xflz_eai_car1/vision/%s` |"
            % (new, title, typ, star, SRC[old])
        )

    overview = (
        "## 实验总览\n\n"
        "> **学习顺序说明**：下表按「由易到难」重排——先 OpenCV 传统视觉（免训练、可解释、帧率高），"
        "再 YOLO 系列（检测/分类/分割），接着 DeepSORT 跟踪，最后 MediaPipe 人体感知与控制。\n"
        "> `源码路径` 中的目录号是仓库交付号，与左侧学习序号不再一一对应，请以下表为准。\n\n"
        "| 编号 | 实验名称 | 学时 | 类型 | 难度 | 源码路径 |\n"
        "|------|---------|------|------|------|---------|\n"
        + "\n".join(rows)
        + "\n\n**学时合计：48h**（12 个实验，对应 course-spec total_hours=48 中实验学时部分）\n\n"
        "**技术栈递进**：\n\n"
        "| 阶段 | 实验 | 技术栈 | 是否需要训练 | 板端帧率 |\n"
        "|------|------|--------|-------------|---------|\n"
        "| ① 传统视觉 | 实验1~3 | OpenCV（HSV / QRCode / 轮廓） | 否 | 30~50 FPS |\n"
        "| ② 目标检测与分类 | 实验4~5 | YOLOv8 / YOLOv5 检测头 + RKNN | 是（已交付权重） | 13~18 FPS |\n"
        "| ③ 语义分割 | 实验6 | yolov8n-seg + 多线程推理池 | 是（已交付权重） | 40~60 FPS |\n"
        "| ④ 多目标跟踪 | 实验7 | YOLOv8 + DeepSORT + ReID | 是（已交付权重） | 12~15 FPS |\n"
        "| ⑤ 人体感知 | 实验8~10 | MediaPipe Blaze + 深度相机 | 是（已交付权重） | 10~28 FPS |\n"
        "| ⑥ 视觉控制闭环 | 实验11~12 | 关键点 + cmd_vel / 手势分类 | 是（已交付权重） | 10~12 FPS |\n\n"
        "---\n\n"
    )

    # 正文：按新顺序拼各篇
    bodies = []
    for new in range(1, 13):
        bodies.append(read(os.path.join(PARTS, "experiment-%d.md" % new)).rstrip() + "\n")
    # 每篇之间加分隔符（原文末尾可能已带 ---）
    joined = ""
    for b in bodies:
        joined += b.rstrip()
        if not joined.endswith("---"):
            joined += "\n\n---\n\n"
        else:
            joined += "\n\n"

    write(guide_path, header + overview + joined + (tail if tail else ""))
    print("[4] 已重构 EXP001_lab_guide.md（头部 + 新总览 + 12 篇新序 + 尾注）")

    # ---------- 5. course-spec.yaml ----------
    spec_path = os.path.join(ROOT, "_meta", "course-spec.yaml")
    y = read(spec_path)
    # 先删旧的 source_dir_number / learning_order_note，保证幂等
    y = re.sub(r"^source_dir_number: \d+\n", "", y, flags=re.M)
    y = re.sub(r"(?:#[^\n]*\n)*learning_order_note: [^\n]*\n", "", y)
    y = y.replace("# 学习序号说明（2026 重排）：\n", "")
    y = re.sub(r"^#   [^\n]*\n", "", y, flags=re.M)

    note = (
        "# ===== 学习序号说明（2026 重排，方案A：OpenCV 先行）=====\n"
        "# experiments[].id 的 exp01..exp12 = 学习顺序，按由易到难排列：\n"
        "#   OpenCV（免训练、可解释） -> YOLO 检测/分类 -> 语义分割 -> DeepSORT -> MediaPipe -> 视觉控制\n"
        "# source_code_path 里的 vision/NN_* 是仓库交付目录号，重排后不再与学习序号一致。\n"
        "# 每个实验的 source_dir_number 字段给出对应的源码目录号。\n"
        "learning_order_note: 学习序号 exp01..exp12 由易到难重排；source_dir_number 为源码目录号\n"
    )
    y = y.replace("experiments:\n", note + "experiments:\n", 1)

    # 重新计算每个实验的 source_dir_number（按路径反查）
    def add_num(m):
        block = m.group(0)
        mm = re.search(r"source_code_path: (\S+)", block)
        if not mm:
            return block
        num = None
        for k, v in SRC.items():
            if v in mm.group(1):
                num = k
                break
        if num is None:
            return block
        return re.sub(r"(source_code_path: [^\n]*)", r"\1\nsource_dir_number: %d" % num, block, count=1)

    y = re.sub(r"  - id: exp\d+.*?(?=\n  - id: exp|\n_source:)", add_num, y, flags=re.S)
    write(spec_path, y)
    print("[5] 已更新 _meta/course-spec.yaml")

    # ---------- 6. 核对输出 ----------
    print("\n=== 新学习序号 -> 源码目录 ===")
    for new in range(1, 13):
        print("  EXP-%02d  %-34s  <- vision/%s"
              % (new, META[new][0], SRC[NEW2OLD[new]]))


if __name__ == "__main__":
    main()
