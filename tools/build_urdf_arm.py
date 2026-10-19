# -*- coding: utf-8 -*-
"""
从真机 URDF 生成课程用的"臂链精简 URDF + 减面网格 + 离线数据包"

为什么要这个脚本：
  课程页面用 file:// 直接双击打开，浏览器禁止 fetch/XHR 读本地文件，
  所以 URDF 文本和 STL 必须打进一个 <script src> 能加载的 .js 里。
  这个脚本负责把三件事一次做完，改 URDF 或换网格后重跑即可：

    1. car1.urdf  →  car1_arm.urdf   只保留"底盘 + 四轮 + 机械臂 + 夹爪"这条链
    2. meshes/*.STL → meshes/*.STL    顶点聚类减面（教学用，肉眼无差）
    3. car1_arm.urdf + 网格  →  urdf-bundle.js   （base64 内联，供页面离线加载）

用法：
  python tools/build_urdf_arm.py
"""
import base64
import os
import re
import struct
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_URDF = os.path.join(
    ROOT, "ros2_ws", "src", "xflz_eai_car1", "test", "car1_web_server", "urdf", "car1.urdf")
SRC_MESH = os.path.join(
    ROOT, "ros2_ws", "src", "xflz_eai_car1", "test", "car1_web_server", "meshes")
OUT_DIR = os.path.join(ROOT, "training", "output", "assets", "modules", "urdf-arm")
OUT_MESH = os.path.join(OUT_DIR, "meshes")

# 只保留这条链：底盘 + 四轮 + 臂（含夹爪）
KEEP_LINKS = [
    "base_footprint", "base_link",
    "wheel_lf_link", "wheel_rf_link", "wheel_lb_link", "wheel_rb_link",
    "arm_base_link",
    "arm_link1", "arm_link2", "arm_link3", "arm_link4", "arm_link5", "arm_link6",
    "r_link", "l_link", "r_in_link", "r_out_link", "l_in_link", "l_out_link",
    "tcp_link",
]

# 每个网格减面目标（三角面数）。空 = 原样保留
TARGET_TRIS = {
    "base_link": 6000,
    "wheel_lf_link": 900, "wheel_rf_link": 900,
    "wheel_lb_link": 900, "wheel_rb_link": 900,
    "arm_base_link": 3000,
    "arm_link1": 3000,
    "arm_link2": 3500, "arm_link3": 3500, "arm_link4": 3500,
    # arm_link5 / arm_link6 / 夹爪四件本来就轻，原样保留
}


# ---------------------------------------------------------------- STL 读写
def read_stl(path):
    with open(path, "rb") as f:
        head = f.read(84)
        if len(head) < 84:
            return np.zeros((0, 3, 3), dtype=np.float32)
        n = struct.unpack("<I", head[80:84])[0]
        if n == 0 or n > 5_000_000:
            return np.zeros((0, 3, 3), dtype=np.float32)
        raw = f.read(n * 50)
    tri = np.frombuffer(raw, dtype=np.uint8).reshape(n, 50)[:, 12:48].copy()
    return tri.view("<f4").reshape(n, 3, 3)


def write_stl(path, tris):
    tris = np.asarray(tris, dtype=np.float32)
    n = len(tris)
    v1 = tris[:, 1] - tris[:, 0]
    v2 = tris[:, 2] - tris[:, 0]
    nor = np.cross(v1, v2)
    ln = np.linalg.norm(nor, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    nor = nor / ln
    rec = np.zeros((n, 12), dtype=np.float32)
    rec[:, 0:3] = nor
    rec[:, 3:6] = tris[:, 0]
    rec[:, 6:9] = tris[:, 1]
    rec[:, 9:12] = tris[:, 2]
    body = np.zeros((n, 50), dtype=np.uint8)          # 每面 50 字节：法线3+顶点9+属性2
    body[:, 0:48] = rec.view(np.uint8).reshape(n, 48)
    with open(path, "wb") as f:
        f.write(b"binary STL - decimated by build_urdf_arm.py".ljust(80, b" "))
        f.write(struct.pack("<I", n))
        f.write(body.tobytes())


def cluster(tris, cell):
    """顶点聚类：把落在同一格子的顶点合并成一个代表点（格子内均值）"""
    pts = tris.reshape(-1, 3)
    lo = pts.min(axis=0)
    key = np.floor((pts - lo) / cell).astype(np.int64)
    # 用三列整数做精确去重（不能把三列哈希成一个整数：int64 会溢出，碰撞会把
    # 相距很远的顶点并到一起，减面结果直接变成几块大斜板 —— 踩过这个坑）
    _, inv = np.unique(key, axis=0, return_inverse=True)
    reps = np.zeros((inv.max() + 1, 3), dtype=np.float64)
    cnt = np.zeros(inv.max() + 1, dtype=np.float64)
    np.add.at(reps, inv, pts.astype(np.float64))
    np.add.at(cnt, inv, 1.0)
    reps /= cnt[:, None]
    out = reps[inv].reshape(-1, 3, 3).astype(np.float32)
    # 丢掉退化三角形（三个角落进同一格）
    i = inv.reshape(-1, 3)
    good = (i[:, 0] != i[:, 1]) & (i[:, 1] != i[:, 2]) & (i[:, 0] != i[:, 2])
    return out[good]


def decimate(tris, target):
    """二分格子尺寸，逼近目标面数"""
    if target is None or len(tris) <= target:
        return tris
    lo = tris.reshape(-1, 3).min(axis=0)
    hi = tris.reshape(-1, 3).max(axis=0)
    diag = float(np.linalg.norm(hi - lo))
    a, b = diag / 1500.0, diag / 2.0
    best = tris
    for _ in range(22):
        mid = (a + b) / 2
        d = cluster(tris, mid)
        if len(d) > target:
            a = mid
        else:
            b = mid
            best = d
        if abs(len(d) - target) < target * 0.05:
            best = d
            break
    return best


# ---------------------------------------------------------------- URDF 处理
def parse_joints(s):
    out = []
    for m in re.finditer(r"<joint\s+name=\"([^\"]+)\"\s+type=\"([^\"]+)\">(.*?)</joint>", s, re.S):
        name, typ, body = m.group(1), m.group(2), m.group(3)
        g = lambda k, a="([^\"]*)": (re.search(r"<%s\s+%s=\"%s\"" % (k, a, a) if False else
                                              r"<%s\s+%s=\"([^\"]*)\"" % (k, a), body) or [None, None])[1]
        par = re.search(r"<parent\s+link=\"([^\"]+)\"", body)
        chi = re.search(r"<child\s+link=\"([^\"]+)\"", body)
        org = re.search(r"<origin\s+xyz=\"([^\"]*)\"\s*rpy=\"([^\"]*)\"", body)
        ax = re.search(r"<axis\s+xyz=\"([^\"]*)\"", body)
        lim = re.search(r"<limit\s+lower=\"([^\"]*)\"\s+upper=\"([^\"]*)\"", body)
        out.append(dict(
            name=name, type=typ,
            parent=par.group(1) if par else None,
            child=chi.group(1) if chi else None,
            xyz=org.group(1) if org else "0 0 0",
            rpy=org.group(2) if org else "0 0 0",
            axis=ax.group(1) if ax else "0 0 0",
            limit=(float(lim.group(1)), float(lim.group(2))) if lim else None,
        ))
    return out


# ---------------------------------------------------------------- 离线网格打包
# 为什么不直接塞 STL：50 字节/面，base64 后翻 1.37 倍，2MB 起步。
# 这里量化成 uint16 三角面（18 字节/面，法线由浏览器现算），体积降到 1/3。
#   头： u8 版本 | 3×u8 保留 | u32 面数 | 3×f32 原点 | f32 量化步长 | u16 坐标×9
# 注意必须是 uint16 而不是 int16：量化值是 (p-lo)/step，范围 0~65534，
# 塞进 int16 会溢出成负数，几何直接被折成几块大平板（踩过这个坑）。
def pack_mesh(tris):
    tris = np.asarray(tris, dtype=np.float64)
    n = len(tris)
    pts = tris.reshape(-1, 3)
    lo = pts.min(axis=0)
    extent = float((pts.max(axis=0) - lo).max())
    scale = extent / 65534.0 if extent > 0 else 1e-9
    q = np.round((pts - lo) / scale).astype(np.int64)
    q = np.clip(q, 0, 65535).astype("<u2")
    head = struct.pack("<B3xI3ff", 1, n, float(lo[0]), float(lo[1]), float(lo[2]), scale)
    return head + q.reshape(-1).tobytes()


def main():
    if not os.path.exists(SRC_URDF):
        sys.exit("找不到源 URDF: " + SRC_URDF)
    os.makedirs(OUT_MESH, exist_ok=True)

    src = open(SRC_URDF, encoding="utf-8").read()
    joints = [j for j in parse_joints(src)
              if j["parent"] in KEEP_LINKS and j["child"] in KEEP_LINKS]

    # ---- 1. 每个 link 的 visual（网格 + 局部 origin）
    visuals = {}
    for lm in re.finditer(r"<link\s+name=\"([^\"]+)\"\s*>(.*?)</link>", src, re.S):
        name, body = lm.group(1), lm.group(2)
        if name not in KEEP_LINKS:
            continue
        vm = re.search(r"<visual>(.*?)</visual>", body, re.S)
        if not vm:
            continue
        v = vm.group(1)
        org = re.search(r"<origin\s*xyz=\"([^\"]*)\"\s*rpy=\"([^\"]*)\"", v)
        mesh = re.search(r'filename="([^"]+)"', v)
        if not mesh:
            continue
        visuals[name] = dict(
            xyz=org.group(1) if org else "0 0 0",
            rpy=org.group(2) if org else "0 0 0",
            stl=os.path.basename(mesh.group(1)),
        )

    # ---- 2. 减面 + 复制网格
    total_raw = total_new = 0
    print("%-18s %8s %8s %9s" % ("mesh", "tris_in", "tris_out", "KB"))
    for link, v in sorted(visuals.items()):
        sname = v["stl"]
        src_path = os.path.join(SRC_MESH, sname)
        if not os.path.exists(src_path):
            print("  ! 缺网格", sname)
            continue
        tris = read_stl(src_path)
        raw_n = len(tris)
        out = decimate(tris, TARGET_TRIS.get(link))
        dst = os.path.join(OUT_MESH, sname)
        write_stl(dst, out)
        total_raw += raw_n
        total_new += len(out)
        print("%-18s %8d %8d %9.0f" % (link, raw_n, len(out), os.path.getsize(dst) / 1024))
    print("合计三角面 %d → %d（%.1f%%）" % (total_raw, total_new, 100.0 * total_new / max(total_raw, 1)))

    # ---- 3. 写精简 URDF（视觉专用，去掉 inertial/collision）
    L = []
    L.append('<?xml version="1.0" encoding="utf-8"?>')
    L.append('<!--')
    L.append('  car1 机械臂 · 课件显示专用 URDF')
    L.append('')
    L.append('  来源：ros2_ws/src/xflz_eai_car1/test/car1_web_server/urdf/car1.urdf')
    L.append('  裁剪：只保留 底盘 + 四轮 + 机械臂 + 夹爪 这条链；去掉 inertial / collision /')
    L.append('        相机 / 雷达 / IMU 等与运动学无关的部分。所有关节 origin、axis、limit')
    L.append('        与真机 URDF 完全一致，未做任何改动。')
    L.append('  网格：meshes/*.STL 由 tools/build_urdf_arm.py 顶点聚类减面（仅显示用）。')
    L.append('')
    L.append('  改完这里请重跑：python tools/build_urdf_arm.py')
    L.append('-->')
    L.append('<robot name="car1_arm">')
    for name in KEEP_LINKS:
        v = visuals.get(name)
        if not v:
            L.append('  <link name="%s" />' % name)
            continue
        L.append('  <link name="%s">' % name)
        L.append('    <visual>')
        L.append('      <origin xyz="%s" rpy="%s" />' % (v["xyz"], v["rpy"]))
        L.append('      <geometry>')
        L.append('        <mesh filename="./meshes/%s" />' % v["stl"])
        L.append('      </geometry>')
        L.append('    </visual>')
        L.append('  </link>')
    for j in joints:
        L.append('  <joint name="%s" type="%s">' % (j["name"], j["type"]))
        L.append('    <origin xyz="%s" rpy="%s" />' % (j["xyz"], j["rpy"]))
        L.append('    <parent link="%s" />' % j["parent"])
        L.append('    <child link="%s" />' % j["child"])
        if j["axis"] != "0 0 0":
            L.append('    <axis xyz="%s" />' % j["axis"])
        if j["limit"]:
            L.append('    <limit lower="%s" upper="%s" effort="100" velocity="1" />'
                     % (j["limit"][0], j["limit"][1]))
        L.append('  </joint>')
    L.append('</robot>')
    urdf = "\n".join(L) + "\n"
    open(os.path.join(OUT_DIR, "car1_arm.urdf"), "w", encoding="utf-8").write(urdf)

    # ---- 4. 打离线数据包（file:// 下只能靠 <script src> 读文件）
    meshes = {}
    for v in visuals.values():
        p = os.path.join(OUT_MESH, v["stl"])
        meshes[v["stl"]] = base64.b64encode(pack_mesh(read_stl(p))).decode("ascii")
    parts = ['/* 自动生成，勿手改 —— 由 tools/build_urdf_arm.py 生成 */',
             'window.URDF_ARM_BUNDLE = {',
             '  urdf: %s,' % repr(urdf),
             '  meshes: {']
    for k, b64 in sorted(meshes.items()):
        parts.append("    %s: '%s'," % (repr(k), b64))
    parts.append('  }')
    parts.append('};')
    bundle = "\n".join(parts) + "\n"
    open(os.path.join(OUT_DIR, "urdf-bundle.js"), "w", encoding="utf-8").write(bundle)

    print("URDF  ->", os.path.join(OUT_DIR, "car1_arm.urdf"), "(%.1f KB)" % (len(urdf) / 1024))
    print("bundle->", os.path.join(OUT_DIR, "urdf-bundle.js"), "(%.1f KB)" % (len(bundle) / 1024))


if __name__ == "__main__":
    main()
