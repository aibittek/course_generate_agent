# vnc_setup · 远程桌面（noVNC）设备端一键部署

新设备在终端里执行：

```bash
cd /home/iflytek/ros2_ws/fw/vnc_setup
./install_vnc.sh
```

装完后浏览器打开 `http://<设备IP>:6080/vnc.html?autoconnect=1&resize=scale` 即可看到设备桌面
（课程工作台「远程桌面」会话里填的也是这个地址）。脚本可重复执行（幂等）。

安装方式为 **apt 联网安装**（x11vnc、novnc、websockify 及依赖体积很小）。日志里出现
`Failed to fetch packages.ros.org` 之类的告警可以忽略——那是 ROS 官方源不可达时 apt
刷新索引的常规提示，不影响安装结果。

## 装了什么

| 软件包 | 作用 |
|---|---|
| `x11vnc` | 共享设备物理桌面（X 会话），监听 `127.0.0.1:5900`，仅本机可访问 |
| `novnc` | 浏览器端 VNC 客户端页面（`/usr/share/novnc/vnc.html`） |
| `websockify` | WebSocket ↔ VNC 桥接，监听 `0.0.0.0:6080`，把网页连到 5900 |

另外安装两个 systemd 服务（开机自启）：

| 服务 | 作用 |
|---|---|
| `x11vnc.service` | 调用 `/usr/local/bin/x11vnc-start.sh`：自动探测当前 display 编号和 Xorg 授权文件后启动 x11vnc；X 会话重启后 3 秒内自动重连；同时关闭屏保/息屏（DPMS） |
| `novnc-websockify.service` | `websockify --web=/usr/share/novnc 0.0.0.0:6080 localhost:5900` |

均会修改 `/etc/gdm3/custom.conf` 强制 `WaylandEnable=false`（x11vnc 不支持 Wayland，需重启生效）。

## 脚本内置的经验修正（踩过的坑）

1. **display 不一定是 `:0`**：gdm 登录/重登后 X 可能跑在 `:1`，脚本从 `/tmp/.X11-unix/X*` 自动取编号，不再硬编码 `:0`。
2. **授权文件位置不固定**：解析 `/proc/<pid>/cmdline` 里的 `-auth` 参数，取不到再回退 `/run/user/*/gdm/Xauthority`。
3. **Mali 驱动黑屏**：`libGL error: failed to load driver: rockchip` 时硬件渲染失败画面全黑，脚本固定 `LIBGL_ALWAYS_SOFTWARE=1` 走软件渲染。
4. **屏幕自动息屏**：启动时执行 `xset s off -dpms`，防止 VNC 连上后画面变黑。

## 常用排查命令

```bash
systemctl status x11vnc novnc-websockify   # 服务状态
journalctl -u x11vnc -f                    # 服务日志
tail -f /var/log/x11vnc.log                # x11vnc 详细日志（看 display/auth 探测结果）
ss -tlnp | grep -E '5900|6080'             # 端口是否监听
curl -sI http://127.0.0.1:6080/vnc.html    # noVNC 页面是否可访问
```

常见问题：

- **网页提示「无法连到服务器」** → 5900 没监听，看 `x11vnc.log` 尾部的 `start display=? auth=?` 与报错。
- **连上了但全黑** → 确认 `LIBGL_ALWAYS_SOFTWARE=1` 生效，或设备是否息屏（`xset q` 查看_DPMS 状态）。
- **改了 gdm 配置没生效** → `WaylandEnable=false` 需要重启设备。

## 卸载

```bash
./uninstall_vnc.sh            # 只删服务与脚本
./uninstall_vnc.sh --purge    # 连软件包一起卸载
```