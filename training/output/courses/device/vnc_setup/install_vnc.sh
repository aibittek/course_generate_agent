#!/bin/bash
# ============================================================================
# 远程桌面（noVNC）一键安装脚本
# 设备端: Ubuntu 22.04 (aarch64) / 已实测 RK3576
# 用法:   cd /home/iflytek/ros2_ws/fw/vnc_setup && ./install_vnc.sh
# 作用:   安装 x11vnc + novnc + websockify，配置两个 systemd 服务开机自启，
#         网页通过 http://<设备IP>:6080/vnc.html 直接访问设备物理桌面
# 联网:   通过 apt 联网安装（软件包很小，装完即可删；日志中的
#         packages.ros.org 告警是 ROS 源不可达的常规提示，不影响安装）
# 可重复执行（幂等）
# ============================================================================
set -e

if [ "$(id -u)" -ne 0 ]; then
  # 普通用户执行时自动提权（iflytek 免密 sudo）
  exec sudo -n bash "$0" "$@"
fi

echo "==> [1/6] 安装软件包 (x11vnc + novnc + websockify)"
export DEBIAN_FRONTEND=noninteractive

# 先不更新源直接安装（索引已有时最快）；失败才刷新索引重试，避免每次白等超时
if ! apt-get install -y -qq x11vnc novnc websockify; then
  echo "  直接安装失败 → 刷新软件源索引后重试"
  apt-get update -qq || true
  apt-get install -y -qq x11vnc novnc websockify
fi

echo "==> [2/6] 确保 gdm 使用 Xorg (WaylandEnable=false)"
CUSTOM=/etc/gdm3/custom.conf
if [ -f "$CUSTOM" ]; then
  if grep -qE '^\s*WaylandEnable=' "$CUSTOM"; then
    sed -i 's/^\s*WaylandEnable=.*/WaylandEnable=false/' "$CUSTOM"
  elif grep -q '^\[daemon\]' "$CUSTOM"; then
    sed -i 's/^\[daemon\]/[daemon]\nWaylandEnable=false/' "$CUSTOM"
  else
    printf '\n[daemon]\nWaylandEnable=false\n' >> "$CUSTOM"
  fi
fi

echo "==> [3/6] 安装启动包装脚本 /usr/local/bin/x11vnc-start.sh"
# 自动探测 display 编号（X0/X1...）与 Xorg 授权文件，X 会话重启后自动重连
cat > /usr/local/bin/x11vnc-start.sh <<'EOF'
#!/bin/bash
discover_display() {
  local s
  # socket 名即 display 编号；取编号最大的（最新启动的 X 会话）
  s=$(ls -t /tmp/.X11-unix/ 2>/dev/null | sed -n 's/^X\([0-9][0-9]*\)$/\1/p' | sort -rn | head -1)
  [ -n "$s" ] && { printf ':%s' "$s"; return; }
  printf ':0'
}
discover_auth() {
  local pid args cand
  for pid in $(pgrep -x Xorg 2>/dev/null); do
    args=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null)
    cand=$(printf '%s' "$args" | sed -n 's/.*-auth \([^ ]*\).*/\1/p')
    [ -n "$cand" ] && [ -r "$cand" ] && { printf '%s' "$cand"; return; }
  done
  for cand in /run/user/*/gdm/Xauthority; do
    [ -r "$cand" ] && { printf '%s' "$cand"; return; }
  done
  printf 'guess'
}
while true; do
  DISPLAY_NUM=$(discover_display)
  AUTH=$(discover_auth)
  if [ -n "$AUTH" ] && [ -r "$AUTH" ]; then
    DISPLAY="$DISPLAY_NUM" XAUTHORITY="$AUTH" xset s off -dpms   >/dev/null 2>&1
    DISPLAY="$DISPLAY_NUM" XAUTHORITY="$AUTH" xset -dpms         >/dev/null 2>&1
    DISPLAY="$DISPLAY_NUM" XAUTHORITY="$AUTH" xset s noblank     >/dev/null 2>&1
  fi
  echo "$(date '+%F %T') start display=$DISPLAY_NUM auth=$AUTH"
  # LIBGL_ALWAYS_SOFTWARE: Rockchip Mali 驱动加载失败时退回软件渲染，避免黑屏
  LIBGL_ALWAYS_SOFTWARE=1 /usr/bin/x11vnc -display "$DISPLAY_NUM" -auth "$AUTH" \
       -forever -shared -repeat -noxdamage -rfbport 5900 -localhost -nopw \
       -o /var/log/x11vnc.log
  echo "$(date '+%F %T') x11vnc exit, retry in 3s"
  sleep 3
done
EOF
chmod 755 /usr/local/bin/x11vnc-start.sh

echo "==> [4/6] 写入 systemd 服务"
# x11vnc: 共享物理桌面，监听 127.0.0.1:5900（仅本机，外部只能走 6080 网页入口）
cat > /etc/systemd/system/x11vnc.service <<'EOF'
[Unit]
Description=x11vnc - share physical display (auto-detect display/auth)
After=display-manager.service graphical.target
Wants=display-manager.service

[Service]
Type=simple
ExecStart=/usr/local/bin/x11vnc-start.sh
Restart=always
RestartSec=3
User=root

[Install]
WantedBy=graphical.target
EOF

# websockify: 6080 -> 5900 桥接 + noVNC 网页，供网页端直接访问
cat > /etc/systemd/system/novnc-websockify.service <<'EOF'
[Unit]
Description=noVNC websockify bridge (6080 -> 5900)
After=network.target x11vnc.service
Wants=x11vnc.service

[Service]
Type=simple
ExecStart=/usr/bin/websockify --web=/usr/share/novnc 0.0.0.0:6080 localhost:5900
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "==> [5/6] 启动并设为开机自启"
systemctl daemon-reload
systemctl enable --now x11vnc.service novnc-websockify.service
systemctl restart x11vnc.service novnc-websockify.service

echo "==> [6/6] 验证"
sleep 5
echo -n "  x11vnc        : "; systemctl is-active x11vnc
echo -n "  novnc-websockify: "; systemctl is-active novnc-websockify
echo "  监听端口:"
ss -tlnp | grep -E '5900|6080' || true

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo ""
echo "=========================================================="
echo " 安装完成。浏览器访问："
echo "   http://${IP:-<设备IP>}:6080/vnc.html?autoconnect=1&resize=scale"
echo ""
echo "  排查: journalctl -u x11vnc -f ;  tail -f /var/log/x11vnc.log"
echo "=========================================================="