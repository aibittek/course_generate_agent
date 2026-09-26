#!/usr/bin/env bash
# =============================================================================
# 一次性注册 eai-helper:// 自定义协议 —— Linux 版
#
# 原理：向 ~/.local/share/applications 写入 .desktop 条目并用
# xdg-settings 设为默认处理器（无需 root）。之后网页点「连接」发现助手
# 未启动时，浏览器会通过 eai-helper://start?port=8100 拉起 start_helper.py。
#
# 撤销：rm ~/.local/share/applications/eai-helper.desktop && xdg-mime default ...
# Windows 请运行 register_helper.bat。
# =============================================================================
set -e
cd "$(dirname "$0")"

PY="$(command -v python3 || command -v python)" || {
  echo "[x] 未找到 Python，请先安装 python3 再运行本脚本。"; exit 1; }

DIR="$(pwd)"
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DIR"

# 把 %1 形式的 URL 交给 start_helper.py（它会解析出端口）
cat > "$APP_DIR/eai-helper.desktop" <<EOF
[Desktop Entry]
Name=EAI Device Helper
Comment=具身智能课程 · 设备开发本机助手
Exec=$PY $DIR/start_helper.py %u
Type=Application
NoDisplay=true
MimeType=x-scheme-handler/eai-helper;
EOF

update-desktop-database "$APP_DIR" 2>/dev/null || true
xdg-mime default eai-helper.desktop x-scheme-handler/eai-helper

echo "[+] eai-helper:// 协议注册成功（$APP_DIR/eai-helper.desktop）。"
echo "    回到工作台点连接即可自动唤起助手。"
echo "    若浏览器仍不唤起，确认它不是以 snap/flatpak 沙箱方式安装的。"