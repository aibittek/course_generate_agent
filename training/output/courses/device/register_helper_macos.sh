#!/usr/bin/env bash
# =============================================================================
# 一次性注册 eai-helper:// 自定义协议 —— macOS 版
#
# 原理：在 ~/Applications 下生成内置 CFBundleURLTypes 的最小 .app 启动器
# （Info.plist 声明 eai-helper scheme，可执行文件转发到本目录的 start_helper.py），
# 再用系统 lsregister 强制注册进 LaunchServices。无需管理员、无需打包真实 App、
# 本机生成不带隔离属性，可直接运行。
#
# 用法：./register_helper_macos.sh     （可重复执行，覆盖更新）
# 撤销：rm -rf ~/Applications/eai-helper.app
# =============================================================================
set -e
cd "$(dirname "$0")"
DIR="$(pwd)"

PY="$(command -v python3 || command -v python)" || { echo "[x] 未找到 python3，请先安装。"; exit 1; }

APP="${HOME}/Applications/eai-helper.app"
mkdir -p "${HOME}/Applications" "${APP}/Contents/MacOS"

# ---- Info.plist：声明 eai-helper:// URL scheme，LSUIElement 免 Dock 图标 ----
cat > "${APP}/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleIdentifier</key>   <string>edu.eai.course.device-helper</string>
  <key>CFBundleName</key>         <string>EAI Device Helper</string>
  <key>CFBundleExecutable</key>   <string>eai-helper</string>
  <key>CFBundlePackageType</key>  <string>APPL</string>
  <key>CFBundleVersion</key>      <string>1.0</string>
  <key>LSUIElement</key>          <true/>
  <key>CFBundleURLTypes</key>
  <array>
    <dict>
      <key>CFBundleURLName</key>   <string>eai-helper</string>
      <key>CFBundleURLSchemes</key><array><string>eai-helper</string></array>
    </dict>
  </array>
</dict>
</plist>
EOF

# ---- 可执行文件：浏览器唤起时收到 eai-helper://start?port=NNN，
#      原样转发给 start_helper.py（它会解析 port、无窗口日志进 helper.log）----
#      路径在生成时已固化（"unquoted heredoc" 展开），运行时不依赖调用者环境 ----
cat > "${APP}/Contents/MacOS/eai-helper" <<EOF
#!/bin/bash
cd "$DIR" >/dev/null 2>&1
exec "$PY" "$DIR/start_helper.py" --headless "\$1" >> "$DIR/helper.log" 2>&1
EOF
chmod +x "${APP}/Contents/MacOS/eai-helper"

# ---- 强制注册进 LaunchServices（用户域，无需 sudo）----
LSREG="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
if [ -x "$LSREG" ]; then
  "$LSREG" -f "$APP"
else
  # lsregister 缺失时退回 open 触发一次系统扫描
  open "$APP" >/dev/null 2>&1 || true
fi

echo "[+] eai-helper:// 协议注册成功（${APP}）。"
echo "    之后网页点「设备开发 / 启动本机助手」即自动、无窗口地拉起助手。"
echo "    回退方式仍可用：./start_helper.sh"
echo "    撤销：rm -rf ${APP}"