# -*- coding: utf-8 -*-
"""按新学习顺序重排 course-spec.yaml 的 experiments 列表（幂等）。"""
import io
import os
import re

SPEC = r"E:\Source\xflz_eai_car1\course_generate_agent\courses\sheet1\robot_vision\_meta\course-spec.yaml"

# 源码目录号 -> 新学习序号
DIR2NEW = {
    "03_lab_color_recognition": 1,
    "04_qrcode": 2,
    "05_line_following": 3,
    "01_industrial_defect_detection": 4,
    "02_garbage_classification": 5,
    "06_semantic_segmentation": 6,
    "07_multi_object_tracking": 7,
    "09_face_landmarks": 8,
    "10_pose_landmark": 9,
    "08_depth_3d_detection": 10,
    "11_pose_control": 11,
    "12_hand_control": 12,
}


def main():
    with io.open(SPEC, "r", encoding="utf-8") as f:
        t = f.read()

    # 切出 experiments 块
    m = re.search(r"^experiments:\n(.*?)(?=^_source:)", t, flags=re.M | re.S)
    if not m:
        raise SystemExit("找不到 experiments 块")
    head, body, tail = t[:m.start()], m.group(1), t[m.end():]

    # 按 "- id: expNN" 切分条目
    parts = re.split(r"(?m)^(?=  - id: exp)", body)
    pre = parts[0]
    blocks = [p for p in parts[1:] if p.strip()]
    if len(blocks) != 12:
        raise SystemExit("条目数不是 12，实际 %d" % len(blocks))

    # 每条找出源码目录并计算新序号
    items = []
    for b in blocks:
        mm = re.search(r"source_code_path: \S*?vision/(\d{2}_[a-z0-9_]+)/", b)
        if not mm:
            raise SystemExit("条目不包含 vision 路径：%s" % b[:80])
        d = mm.group(1)
        if d not in DIR2NEW:
            raise SystemExit("未知目录 %s" % d)
        items.append((DIR2NEW[d], d, b))

    items.sort(key=lambda x: x[0])

    out = []
    for new, d, b in items:
        # 重写 id / experiment_id / source_dir_number
        b = re.sub(r"  - id: exp\d+", "  - id: exp%02d" % new, b, count=1)
        b = re.sub(r"^    experiment_id: \d+", "    experiment_id: %d" % new, b, count=1, flags=re.M)
        if "source_dir_number" in b:
            b = re.sub(r"^    source_dir_number: \d+", "    source_dir_number: %d" % int(d[:2]), b, count=1, flags=re.M)
        else:
            b = re.sub(r"(source_code_path: [^\n]*\n)",
                       r"\1    source_dir_number: %d\n" % int(d[:2]), b, count=1)
        out.append(b.rstrip("\n") + "\n")

    new_body = pre + "".join(out) + "\n"
    with io.open(SPEC, "w", encoding="utf-8", newline="\n") as f:
        f.write(head + "experiments:\n" + new_body + tail)

    print("=== experiments 新顺序 ===")
    for new, d, b in items:
        name = re.search(r"^    name: (.+)$", b, re.M)
        print("  exp%02d  %-12s  %s" % (new, d, name.group(1) if name else "?"))


if __name__ == "__main__":
    main()
