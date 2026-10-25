#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本机助手启动器 start_helper.py（具身智能课程 · 设备开发工作台）

作用：在**本地电脑**上把桥接服务跑起来，浏览器只连 127.0.0.1，
再由本机助手 SSH 登录设备。设备端**不需要安装任何服务**。

链路：浏览器 → http://127.0.0.1:8100（本机助手） → 设备IP:22（sshd）

本文件只是薄薄一层启动器，真正的服务逻辑在同目录的 device_bridge.py，
启动时强制以下本地模式参数：

  --host 127.0.0.1        只监听本机回环地址，局域网内其他机器访问不到，安全
  --allow-remote-host     允许助手去登录“其它主机”（即设备 IP）
  --static <本文件所在目录> 顺带把 workspace.html 等前端也托管出去

双击 start_helper.bat 即可运行；Ctrl+C 或关窗口即停止。
首次运行会自动安装缺失依赖（aiohttp / paramiko / pyserial，清华源）。

无窗口模式（--headless / pythonw 启动）：打开同一目录的 helper.log 查看日志。
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

SERVICE_NAME = "eai-device-bridge"
DEFAULT_PORT = 8100


def setup_headless_log(here: Path) -> None:
    """无窗口模式：把 stdout/stderr 重定向到 helper.log（追加写入）。"""
    log_path = here / "helper.log"
    try:
        fh = open(log_path, "a", encoding="utf-8", buffering=1)
    except OSError:
        return
    sys.stdout = fh
    sys.stderr = fh


def datetime_now() -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def find_bridge_script() -> Path:
    """定位 device_bridge.py：它必须与 start_helper.py 放在同一目录。"""
    bridge = Path(__file__).resolve().parent / "device_bridge.py"
    if bridge.is_file():
        return bridge
    raise FileNotFoundError(
        "未找到 device_bridge.py。\n"
        "请确认它与 start_helper.py 在同一个目录（courses/device/）。"
    )


def probe(port: int) -> bool:
    """探测本机 port 上是否已经有助手在跑。"""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/ping", timeout=0.8
        ) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        return data.get("service") == SERVICE_NAME
    except Exception:
        return False


def pick_port(argv: list) -> int:
    for i, a in enumerate(argv):
        if a == "--port" and i + 1 < len(argv):
            try:
                return int(argv[i + 1])
            except ValueError:
                pass
        if a.startswith("--port="):
            try:
                return int(a.split("=", 1)[1])
            except ValueError:
                pass
        # eai-helper://start?port=NNN —— 协议唤起时浏览器把整个 URL 作为参数传来
        if a.startswith("eai-helper:"):
            import re
            m = re.search(r"[?&]port=(\d+)", a)
            if m:
                return int(m.group(1))
    return DEFAULT_PORT


def clean_extra(argv: list) -> list:
    """去掉协议唤起带进来的 eai-helper:// 参数，只留真正的启动参数。"""
    return [a for a in argv if not a.startswith("eai-helper:")]


def main() -> int:
    extra = clean_extra(sys.argv[1:])
    port = pick_port(sys.argv[1:])
    here = Path(__file__).resolve().parent

    # 无窗口模式：显式 --headless，或被 pythonw 启动（sys.stdout 为 None）时，
    # 把全部控制台输出转写到 helper.log，便于事后排查
    headless = "--headless" in extra or sys.stdout is None
    if headless:
        extra = [a for a in extra if a != "--headless"]
        setup_headless_log(here)

    # 已经在跑：直接退出（供 eai-helper:// 协议、重复点击等场景幂等使用）
    if probe(port):
        print(f"[+] 本机助手已在运行：http://127.0.0.1:{port} （无需重复启动）", flush=True)
        return 0

    if "--host" in extra or any(a.startswith("--host=") for a in extra):
        print("[!] 注意：手动指定了 --host。若改成 0.0.0.0，局域网内任何人都能"
              "通过本机助手登录设备，仅教学沙箱环境可接受。", flush=True)

    bridge = find_bridge_script()
    sys.path.insert(0, str(bridge.parent))

    # 避免重复 import 名冲突
    sys.modules.pop("device_bridge", None)
    import device_bridge  # noqa: E402  （import 时会自动 ensure_deps 安装缺失依赖）

    # 组装参数：本地模式默认值在前，用户参数在后（argparse 同名取最后一个）
    flags = ["--host", "127.0.0.1", "--allow-remote-host"]
    # 端口统一：协议唤起（eai-helper://...?port=NNN）时 extra 里没有 --port，
    # 必须显式补上，保证 probe/banner 与 device_bridge 实际监听端口一致
    has_port = any(
        a == "--port" or a.startswith("--port=") for a in extra
    )
    if not has_port:
        flags += ["--port", str(port)]
    if not ("--static" in extra or any(a.startswith("--static=") for a in extra)):
        flags += ["--static", str(here)]      # 顺带托管 workspace.html
    sys.argv = [str(bridge)] + flags + extra

    print("=" * 56, flush=True)
    print("  具身智能课程 · 设备开发本机助手", flush=True)
    print(f"  启动    {datetime_now()}", flush=True)
    print(f"  链路    浏览器 → 127.0.0.1:{port} → 设备 SSH", flush=True)
    print(f"  工作台  http://127.0.0.1:{port}/workspace.html", flush=True)
    if headless:
        print(f"  日志    {here / 'helper.log'}（无窗口模式，日志转写到文件）", flush=True)
        print("  停止    页面点不动时可重启本脚本；或 taskkill 见 helper.log 头部提示", flush=True)
    else:
        print("  仅监听本机回环地址；Ctrl+C 或关掉本窗口即停止", flush=True)
    print("=" * 56, flush=True)

    try:
        device_bridge.main()
    except KeyboardInterrupt:
        print("\n[+] 助手已停止。", flush=True)
    except OSError as exc:
        print(f"[x] 启动失败：{exc}", flush=True)
        reason = "端口可能被占用" if getattr(exc, "errno", None) in (98, 48, 10048) else "请检查上方错误信息"
        print(f"    排查：{reason}；或换端口启动 start_helper.bat --port 8101", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())