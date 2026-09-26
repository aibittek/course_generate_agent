# 设备开发工作台 · 本机助手部署文档（设备端免安装）

本文档说明如何在**打开网页的这台电脑**上准备「设备开发」能力：一体化工作台（`workspace.html`）的
SSH 终端与文件管理由**本机助手**代连，**设备上不需要安装、部署任何服务**，只要 sshd 在监听即可。

> 数据流：`浏览器 → http://127.0.0.1:8100（本机助手） → 设备IP:22（sshd）`
> 串口为本机 USB 直连（Web Serial），不经网络；远程桌面 iframe 直连设备 `:6080`（需设备已有 VNC 服务）。

---

## 0. 文件一览

| 文件 | 作用 |
|---|---|
| `start_helper.py` | 本机助手入口：定位并装载 `device_bridge.py`，强制 `--host 127.0.0.1 --allow-remote-host`，静态目录指向本目录 |
| `start_helper.bat` | Windows 一键启动（自动找 `py -3` / `python`；**首次运行顺带自动注册**协议） |
| `start_helper.sh` | Linux/macOS 一键启动（自动找 `python3`；**首次运行顺带自动注册**协议） |
| `register_helper.bat` | **一次性**注册 `eai-helper://` 协议到 HKCU 注册表（Windows，无需管理员） |
| `register_helper.sh` | **一次性**注册 `eai-helper://` 协议（Linux，.desktop + xdg-mime，无需 root） |
| `register_helper_macos.sh` | **一次性**注册 `eai-helper://` 协议（macOS，生成 `~/Applications/eai-helper.app` 并 lsregister，无需管理员） |
| `workspace.html/css/js` | 一体化工作台前端 |
| `index.html` / `serial.html` | 落地页 / 独立串口页 |
| `device_bridge.py`（同仓库 `ros2_ws/fw/device_dev/`） | 实际服务实现，由 `start_helper.py` 自动装载，无需拷贝 |
| `vnc_setup/` | 远程桌面（noVNC）一键部署包：`install_vnc.sh` 联网安装 + 服务配置（也安装到设备 `/home/iflytek/ros2_ws/fw/vnc_setup`） |

---

## 1. 首次使用（启动助手）

三平台**核心统一**：最终执行的都是同一个 `start_helper.py`，只是各平台用对应的启动包装进入：

| 平台 | 启动方式 |
|---|---|
| Windows | 双击 `start_helper.bat` |
| Linux | `./start_helper.sh` |
| macOS | `./start_helper.sh` |

**方式一：平台启动脚本**

Windows 双击 `start_helper.bat`；Linux/macOS 执行 `./start_helper.sh`（首次若提示无执行权限先
`chmod +x start_helper.sh`）。首次运行会自动从清华源安装 `aiohttp / paramiko / pyserial`
（约十几秒），随后打印：

```
具身智能课程 · 设备开发本机助手
  链路    浏览器 → 127.0.0.1:8100 → 设备 SSH
  工作台  http://127.0.0.1:8100/workspace.html
```

**方式二：在工作台里点按钮**

打开工作台 → 「＋ 新建连接」→ SSH → 展开高级区域，点「**启动本机助手**」，
页面会探测 `127.0.0.1:8100`，未启动时引导拉起（依赖方式三的协议注册才会自动生效）。

**方式三（推荐，一次性注册后全自动）：注册 `eai-helper://` 协议**

注册动作**已内置在两个启动脚本里**（幂等，重复执行覆盖）——新电脑只要跑过一次入口脚本即完成注册，
之后点首页「设备开发」/ 弹窗「启动本机助手」都会无窗口自动拉起助手。也可手动单独执行：

- Windows：双击 `register_helper.bat`（写入 `HKCU\Software\Classes\eai-helper`）
- Linux：执行 `./register_helper.sh`（写入 `~/.local/share/applications/eai-helper.desktop`，
  通过 xdg-mime 注册；snap/flatpak 沙箱版浏览器可能不生效）
- macOS：执行 `./register_helper_macos.sh`（生成内置 URL scheme 的
  `~/Applications/eai-helper.app` 并用 lsregister 注册，无需管理员；撤销 `rm -rf ~/Applications/eai-helper.app`）

之后网页点「连接」发现助手未启动时，会通过 `eai-helper://start?port=8100` 静默拉起
`start_helper.py`（无窗口，日志入 `helper.log`），页面轮询等待就绪再继续登录。
浏览器首次可能弹一次「允许打开外部应用」确认，勾选"始终允许"后不再询问。

命令行启动（三平台通用，可改端口）：

```bash
python3 start_helper.py            # 默认 127.0.0.1:8100（Windows 下用 python）
python3 start_helper.py --port 9000
```

> 助手**只监听回环地址 127.0.0.1**，局域网内其他人访问不到；关掉窗口或 `Ctrl+C` 即停止。
> 端口存放在浏览器 `localStorage`（`eai_helper_port`），改端口后页面弹窗里的「助手端口」也要对应修改。

---

## 2. 连接设备

打开工作台 → 「＋ 新建连接」→ 选择类型后填写：

- **SSH 终端 / 文件管理**：填**设备 IP**（如 `192.168.1.100`）、SSH 端口（默认 `22`，如测试机改过则
  填实际值，例如 `2222`）、用户名/密码（设备 SSH 账号）；助手指的就是「用这个账号从本机 SSH 登录设备」。
- **远程桌面**：填 noVNC 地址，如 `http://<设备IP>:6080/vnc.html?autoconnect=1&resize=scale`（需设备已
  运行 websockify + VNC，见 `ros2_ws/fw/device_dev/README.md` 第 1.6 节）。
- **串口**：不填 IP，选择本机 COM 口 + 波特率（下拉或手输），数据线插在**这台电脑**上。

连接成功后会话**自动保存到左侧列表**（默认命名 `用户名@IP`），下次双击即可重连；
多台设备可同时在线，各自持有独立的登录 token。

---

## 3. 设备端要求

设备侧**只需**：

1. `sshd` 在线（终端 + 文件管理全部基于真实 SSH/SFTP 登录）；
2. 用到远程桌面时，额外有 VNC server + websockify/noVNC（可选）。

不需要在设备上拷贝任何文件、不需要 systemd 服务、不开放 8100 端口。
历史上的设备端部署方案（`device_bridge.py` 装在设备上）仍可用，但**已非必需**，
对比说明见 `ros2_ws/fw/device_dev/README.md` 顶部提示。

### 3.1 远程桌面（VNC）设备端部署

工作台的「远程桌面」是 iframe 直连 `http://<设备IP>:6080/vnc.html`，**不经本机助手**，
因此设备上必须自己跑 VNC + noVNC。

**一键部署（推荐，已实测 RK3576 + Ubuntu 22.04）**：设备端已内置安装包，新设备上只需两行：

```bash
cd /home/iflytek/ros2_ws/fw/vnc_setup
./install_vnc.sh
```

**联网安装**：脚本经 apt 联网安装三个软件包及其依赖（体积很小）。日志中
`Failed to fetch packages.ros.org` 为 ROS 源不可达的告警，可忽略，不影响安装。

脚本幂等（可重复执行），内容包括：

1. `apt` 安装 `x11vnc + novnc + websockify`；`WaylandEnable=false`（x11vnc 不支持 Wayland，改动重启生效）；
2. 安装 `/usr/local/bin/x11vnc-start.sh`：自动探测当前 display 编号（`/tmp/.X11-unix/X*`，不硬编码 `:0`，
   因 gdm 重登后 X 可能跑在 `:1`）、动态定位 Xorg 授权文件、关闭屏保/息屏、`LIBGL_ALWAYS_SOFTWARE=1`
   软件渲染兜底；X 会话重启后 3 秒内自动重连；
3. 写入两个 systemd 服务并开机自启：`x11vnc.service`（127.0.0.1:5900）+ `novnc-websockify.service`
   （0.0.0.0:6080 → 5900）。

目录内附 `README.md`（安装内容、踩坑说明、排查命令）与 `uninstall_vnc.sh`（卸载，`--purge` 连包卸载）。

**Rockchip（RK3576/RK3588）黑屏补充**：Mali 的 `rockchip` DRI 驱动常加载失败
（`libGL error: failed to load driver: rockchip`），启动脚本已固定 `LIBGL_ALWAYS_SOFTWARE=1` 走软件渲染；
如物理屏也黑屏，可再全局生效并重启 GDM：

```bash
echo 'LIBGL_ALWAYS_SOFTWARE=1' | sudo tee -a /etc/environment
sudo systemctl restart gdm
```

顺手关掉息屏，避免 VNC 看到黑屏：

```bash
# 登录界面
sudo sed -i 's/^\[org\/gnome\/settings-daemon\/plugins\/power\]$/[org\/gnome\/desktop\/session]\nidle-delay=uint32 0\n\n[org\/gnome\/settings-daemon\/plugins\/power]/' /etc/gdm3/greeter.dconf-defaults
printf "\nsleep-inactive-ac-type='nothing'\nsleep-inactive-battery-type='nothing'\n" | sudo tee -a /etc/gdm3/greeter.dconf-defaults
sudo /usr/share/gdm/generate-config && sudo systemctl restart gdm
# 已登录用户会话（示例用户 iflytek）
sudo -u iflytek env HOME=/home/iflytek dbus-run-session -- gsettings set org.gnome.desktop.session idle-delay 0
sudo -u iflytek env HOME=/home/iflytek dbus-run-session -- gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
```

**验证**（在本机执行，`<IP>` 换成设备地址）：

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://<IP>:6080/vnc.html   # 期望 200
# 或直接浏览器打开 http://<IP>:6080/vnc.html?autoconnect=1&resize=scale
```

> 安全说明：`-localhost` 让 5900 只监听回环，外部只能通过 6080 的 noVNC 网页访问；
> `-nopw` 表示无密码，因此**不要**把 6080 暴露到公网。

---

## 4. 原理与安全

- `start_helper.py` 导入 `device_bridge.py` 并固定追加 `--host 127.0.0.1 --allow-remote-host`：
  - `127.0.0.1` 监听 → 只有本机能访问助手；
  - `--allow-remote-host` → 允许助手代连**非本机**的目标（设备 IP），这是本方案的必要开关；
  - 静态目录改为本目录，`http://127.0.0.1:8100/workspace.html` 也能直接打开。
- 密码只在助手进程内存中用于建立 SSH 连接，**不落盘、不回传网页**；登录成功后使用 token 换取会话。
- 同一 IP 1 分钟内登录失败 8 次会临时限流，等待 1 分钟即可。
- `eai-helper://` 注册在 HKCU（当前用户），不写 HKLM，不需要管理员权限。

---

## 5. 故障排查

| 现象 | 排查方向 |
|---|---|
| 点连接提示「未检测到本机助手」 | 手动启动：Windows 双击 `start_helper.bat`，Linux/macOS 执行 `./start_helper.sh`；或先运行对应平台的 register 脚本再重试自动拉起 |
| 弹出「是否允许打开 eai-helper」后没反应 | 浏览器可能记住了"禁止"，在站点设置里允许外部协议；Windows 检查 `register_helper.bat` 是否执行成功（`reg query HKCU\Software\Classes\eai-helper\shell\open\command`），Linux 检查 `xdg-mime query default x-scheme-handler/eai-helper`，macOS 检查 `~/Applications/eai-helper.app` 是否存在（不存在则重跑 `./register_helper_macos.sh`） |
| 启动时报端口占用 | 已有实例在跑（再点连接即可）；或 `python start_helper.py --port 9000` 换端口并同步改弹窗里的助手端口 |
| 首次启动很慢 | 正在从清华源安装依赖，等安装完成；也可手动 `pip install aiohttp paramiko pyserial -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| 登录报「用户名或密码错误」 | 用的是**设备 SSH 账号**；先用 `ssh 用户名@设备IP -p 端口` 验证 |
| 登录报「登录失败次数过多」 | 限流中，等 1 分钟再试 |
| 文件列表打不开 | 设备 SFTP 子系统启用：`grep sftp /etc/ssh/sshd_config` 需有 `Subsystem sftp ...` |
| 本机串口打不开 | 用 `Chrome / Edge` 且页面以 `file://`、`localhost` 或 `https` 打开；数据线插在本机；端口被占用时关闭占用者 |
| 远程桌面连不上 | 设备没装 VNC：`ss -tlnp \| grep 6080` 应能看到监听；没有就按 **3.1 节**装 x11vnc + novnc + websockify |
| 远程桌面能连上但**全黑** | ① 板卡 GL 驱动没起来（`libGL error: failed to load driver: rockchip`）→ 加 `LIBGL_ALWAYS_SOFTWARE=1` 到 `/etc/environment` 并重启 gdm；② 屏幕被 DPMS 息屏 → 见 3.1 节关闭息屏；③ 确认 `xwd -root` 非全黑 |
| 远程桌面登录后卡住/断流 | X 会话重启换了授权文件：`sudo systemctl restart x11vnc`（包装脚本会自动重新定位 `-auth`） |
| https 页面连不上助手 | 页面以 https 打开时会拦截对 `http://127.0.0.1` 的请求（混合内容），改用 http 或 file:// 打开工作台 |
| 终端中文乱码 | 设备 locale 非 UTF-8：`export LANG=C.UTF-8` |

---

## 6. 验证记录（2026-09-25）

| 项 | 结果 |
|---|---|
| 助手启动 | `python start_helper.py` → 监听 `127.0.0.1:8100`，banner 显示「本机 + 其它主机」 |
| 依赖自装 | 缺 `aiohttp / pyserial` 时自动从清华源安装成功 |
| 健康检查 | `GET /api/ping` → `{"ok":true,"service":"eai-device-bridge","allow_remote_host":true}` |
| 静态托管 | `GET /workspace.html` → HTTP 200，正确引用 `workspace.js` |
| 鉴权 | `GET /api/sys/info` 无 token → 401（符合预期） |
| 协议参数 | `eai-helper://start?port=8123` → 解析端口 8123；`--port 9000` → 9000；无参 → 8100 |

---

## 7. 远程桌面验证记录（2026-09-26 · 192.168.2.140）

设备：RK3576 + Ubuntu 22.04.5 LTS (aarch64)，DSI-1 屏 1024×600，gdm3 + GNOME(X11)。

| 项 | 结果 |
|---|---|
| 初始状态 | 设备**完全没装** VNC（`x11vnc/vncserver/websockify` 全无，`/usr/share/novnc` 不存在），5900/6080 未监听 → 工作台必然连不上 |
| 安装 | `x11vnc 0.9.16` + `novnc 1.0.0` + `websockify 0.10.0` |
| 服务 | `x11vnc.service`（enabled/active，`127.0.0.1:5900`）+ `novnc-websockify.service`（enabled/active，`0.0.0.0:6080`） |
| 授权文件 | `-auth guess` 在 gdm 登录界面下失败 → 改为包装脚本从 `Xorg` 命令行动态解析（实测 `/run/user/999/gdm/Xauthority`） |
| RFB 握手 | `RFB 003.008`（本机 5900 直连与经 6080 WebSocket 均通过） |
| noVNC 网页 | `GET http://127.0.0.1:6080/vnc.html` → 200；`core/rfb.js` → 200 |
| 端到端 | WebSocket `101 Switching Protocols` → 收到 `RFB 003.008`（浏览器 → websockify:6080 → x11vnc:5900 → :0） |
| 外部可达 | 本机 `Test-NetConnection 192.168.2.140:6080` → True；5900 → False（符合 `-localhost` 预期） |
| **黑屏问题** | `xwd -root` 全黑（0/614400）→ 根因是 `libGL error: failed to load driver: rockchip` 导致 mutter 无法合成；`LIBGL_ALWAYS_SOFTWARE=1` 后 → **100% 非黑**，抓到真实 GDM 登录界面（iflytek / stu） |
| 息屏 | greeter 与 iflytek 会话均设为 `idle-delay=0` / `sleep-inactive-ac-type='nothing'`，`Monitor is On` |
| 截图取证 | 抓取全屏帧缓冲存为 PNG，肉眼确认显示 Ubuntu 登录界面与鼠标指针 |