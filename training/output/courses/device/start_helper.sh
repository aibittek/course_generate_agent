#!/usr/bin/env bash
# =============================================================================
# 具身智能课程 · 设备开发本机助手 —— Linux / macOS 统一启动脚本
#
# 用法：
#   ./start_helper.sh                # 默认 127.0.0.1:8100
#   ./start_helper.sh --port 9000    # 换端口
#
# 首次运行会自动创建独立虚拟环境并从清华源安装依赖（aiohttp/paramiko/pyserial）。
# Windows 请双击 start_helper.bat；三平台最终执行的都是同一个 start_helper.py。
# =============================================================================
set -e
cd "$(dirname "$0")"

# ---- 找 Python 3 ----
PY=""
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys; sys.exit(0 if sys.version_info>=(3,8) else 1)' 2>/dev/null; then
  PY=python
fi

if [ -z "$PY" ]; then
  echo "[x] 未找到 Python 3。"
  echo "    Ubuntu/Debian:  sudo apt install python3 python3-venv python3-pip"
  echo "    macOS:          brew install python3  （或从 python.org 安装）"
  exit 1
fi

# ---- 一次性协议注册（幂等、静默失败，重复执行覆盖）：之后网页点「设备开发」即可自动拉起 ----
# 前提是本机浏览器能通过系统 URL scheme 调回本机（本地 file:// 页面发起通常允许；
#  经 http(s):// 网站发起时部分浏览器会静默拦截，此时回退弹窗内的手动启动引导）。
if [ "$(uname)" = "Darwin" ]; then
  bash ./register_helper_macos.sh >/dev/null 2>&1 || true
else
  bash ./register_helper.sh >/dev/null 2>&1 || true
fi

echo "[i] 启动本机助手（首次运行会自动安装依赖，约需 1~2 分钟）…"
exec "$PY" ./start_helper.py "$@"