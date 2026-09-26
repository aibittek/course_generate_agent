#!/bin/bash
# 卸载远程桌面（noVNC）：停止并删除两个 systemd 服务与启动脚本
# 用法: ./uninstall_vnc.sh   （可选加 --purge 连软件包一起卸载）
set -e
if [ "$(id -u)" -ne 0 ]; then exec sudo -n bash "$0" "$@"; fi

systemctl disable --now x11vnc.service novnc-websockify.service 2>/dev/null || true
rm -f /etc/systemd/system/x11vnc.service /etc/systemd/system/novnc-websockify.service
rm -f /usr/local/bin/x11vnc-start.sh
systemctl daemon-reload
echo "服务与启动脚本已删除。"

if [ "$1" = "--purge" ]; then
  DEBIAN_FRONTEND=noninteractive apt-get purge -y x11vnc novnc websockify
  echo "软件包已卸载。"
fi