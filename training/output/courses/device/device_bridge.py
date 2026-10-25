"""
设备开发桥接服务 device_bridge.py

浏览器没有裸 TCP 能力，无法自己说 SSH / SFTP 协议，所以由设备上这个常驻服务补齐：

  WebSocket  /ws/ssh        一个连接 = 一个 SSH shell 通道（多开即多标签）
  WebSocket  /ws/serial     一个连接 = 独占一个本地串口
  HTTP       /api/login     用 SSH 账号登录，成功后发放 token
  HTTP       /api/fs/*      基于同一条 SSH 连接做 SFTP：列目录 / 读 / 写 / 上传 / 下载 / 改名 / 删除
  HTTP       /api/sys/info  系统信息（uname / 磁盘 / CPU）
  HTTP       /              （可选）托管前端工作台页面

安全模型：浏览器只发送设备自己的 SSH 账号密码，密码仅用于登录本机 sshd，
不落盘、不回传；登录成功后 token 与一条 SSH 连接绑定，文件与串口操作都凭 token 复用。

依赖：aiohttp / paramiko / pyserial（缺失时自动从清华源安装）
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import functools
import json
import logging
import os
import posixpath
import socket
import stat as statmod
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

VERSION = '1.0.0'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8100
DEFAULT_SERIAL_PORT = '/dev/ttyACM0'
DEFAULT_BAUD = 115200
DEFAULT_SESSION_TTL = 28800
MAX_READ_BYTES = 2097152
LOGIN_MAX_FAILS = 8
LOGIN_FAIL_WINDOW = 60.0


class C:
    GREEN = '\x1b[92m'
    YELLOW = '\x1b[93m'
    RED = '\x1b[91m'
    CYAN = '\x1b[96m'
    DIM = '\x1b[2m'
    END = '\x1b[0m'


def info(msg: str) -> None:
    print(f'{C.CYAN}[i]{C.END} {msg}', flush=True)


def ok(msg: str) -> None:
    print(f'{C.GREEN}[+]{C.END} {msg}', flush=True)


def warn(msg: str) -> None:
    print(f'{C.YELLOW}[!]{C.END} {msg}', flush=True)


def err(msg: str) -> None:
    print(f'{C.RED}[x]{C.END} {msg}', flush=True)


def ensure_deps() -> None:
    """缺少 aiohttp / paramiko / pyserial 时自动用清华源安装。"""
    missing = []
    for mod, pkg in (('aiohttp', 'aiohttp'), ('paramiko', 'paramiko'), ('serial', 'pyserial')):
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if not missing:
        return
    warn(f"缺少依赖 {', '.join(missing)}，正在从清华源安装…")
    cmd = [sys.executable, '-m', 'pip', 'install', *missing,
           '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple']
    try:
        subprocess.run(cmd, check=True)
        ok('依赖安装完成')
    except subprocess.CalledProcessError as exc:
        err(f'依赖安装失败：{exc}')
        sys.exit(1)


ensure_deps()

import aiohttp
import paramiko
import serial
import serial.tools.list_ports
from aiohttp import WSMsgType, web

logging.getLogger('paramiko').setLevel(logging.CRITICAL)


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')


def b64d(text: str) -> bytes:
    return base64.b64decode(text.encode('ascii'))


def mode_str(mode: int) -> str:
    kind = 'd' if statmod.S_ISDIR(mode) else ('l' if statmod.S_ISLNK(mode) else '-')
    bits = ((statmod.S_IRUSR, 'r'), (statmod.S_IWUSR, 'w'), (statmod.S_IXUSR, 'x'),
            (statmod.S_IRGRP, 'r'), (statmod.S_IWGRP, 'w'), (statmod.S_IXGRP, 'x'),
            (statmod.S_IROTH, 'r'), (statmod.S_IWOTH, 'w'), (statmod.S_IXOTH, 'x'))
    return kind + ''.join(ch if mode & bit else '-' for bit, ch in bits)


def friendly_error(exc: BaseException) -> str:
    text = str(exc) or exc.__class__.__name__
    if isinstance(exc, paramiko.AuthenticationException):
        return '用户名或密码错误'
    if isinstance(exc, paramiko.ssh_exception.NoValidConnectionsError):
        return '无法连接 SSH 端口，请确认设备已启动 SSHD'
    if isinstance(exc, paramiko.ssh_exception.SSHException):
        return f'SSH 协议错误：{text}'
    if isinstance(exc, ConnectionRefusedError):
        return '连接被拒绝，SSH 服务未启动'
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return '连接超时，请检查网络与地址'
    if isinstance(exc, OSError) and getattr(exc, 'errno', None) == 113:
        return '目标不可达，请检查网络'
    return text


async def run_blocking(fn, *args, **kwargs):
    """在线程池里执行阻塞的 paramiko / serial 调用，避免卡住事件循环。"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(fn, *args, **kwargs))


class SshSession:
    """一次登录 = 一条 paramiko SSH 连接；多个标签复用同一条连接的多个 channel。"""

    def __init__(self, token: str, client: paramiko.SSHClient, user: str, host: str,
                 port: int, homedir: str) -> None:
        self.token = token
        self.client = client
        self.user = user
        self.host = host
        self.port = port
        self.homedir = homedir
        self.created = time.time()
        self.last_seen = time.time()
        self.channels = 0

    @property
    def alive(self) -> bool:
        try:
            transport = self.client.get_transport()
            return transport is not None and transport.is_active()
        except Exception:
            return False

    def touch(self) -> None:
        self.last_seen = time.time()

    def open_sftp(self) -> paramiko.SFTPClient:
        return self.client.open_sftp()

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass


SESSIONS: Dict[str, SshSession] = {}
LOGIN_FAILS: Dict[str, Tuple[int, float]] = {}
SERIAL_OWNERS: Dict[str, str] = {}


def rate_limited(ip: str) -> bool:
    rec = LOGIN_FAILS.get(ip)
    if not rec:
        return False
    count, first = rec
    if time.time() - first > LOGIN_FAIL_WINDOW:
        LOGIN_FAILS.pop(ip, None)
        return False
    return count >= LOGIN_MAX_FAILS


def note_fail(ip: str) -> None:
    count, first = LOGIN_FAILS.get(ip, (0, time.time()))
    if time.time() - first > LOGIN_FAIL_WINDOW:
        count, first = 0, time.time()
    LOGIN_FAILS[ip] = (count + 1, first)


def get_session(request: web.Request) -> Optional[SshSession]:
    token = request.query.get('token') or request.headers.get('X-Session-Token') or ''
    sess = SESSIONS.get(token)
    if sess and sess.alive:
        sess.touch()
        return sess
    if sess:
        SESSIONS.pop(token, None)
        sess.close()
    return None


def need_session(request: web.Request) -> SshSession:
    sess = get_session(request)
    if sess is None:
        raise web.HTTPUnauthorized(
            text=json.dumps({'ok': False, 'error': '会话已失效，请重新登录', 'relogin': True}),
            content_type='application/json')
    return sess


def connect_ssh(host: str, port: int, user: str, password: str,
                timeout: float = 12.0) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=user, password=password,
                   timeout=timeout, banner_timeout=timeout, auth_timeout=timeout,
                   look_for_keys=False, allow_agent=False)
    transport = client.get_transport()
    if transport is not None:
        transport.set_keepalive(30)
    return client


def sftp_home(sess: SshSession) -> str:
    with sess.open_sftp() as sftp:
        return sftp.normalize('.')


def sftp_resolve(sess: SshSession, path: str) -> str:
    with sess.open_sftp() as sftp:
        return sftp.normalize(path)


def sftp_list(sess: SshSession, path: str) -> Tuple[str, List[Dict[str, Any]]]:
    with sess.open_sftp() as sftp:
        base = sftp.normalize(path)
        entries = []
        for attr in sftp.listdir_attr(base):
            mode = attr.st_mode or 0
            is_dir = statmod.S_ISDIR(mode)
            is_link = statmod.S_ISLNK(mode)
            target = None
            if is_link:
                try:
                    target = sftp.readlink(posixpath.join(base, attr.filename))
                except Exception:
                    target = None
            entries.append({
                'name': attr.filename,
                'dir': bool(is_dir),
                'link': bool(is_link),
                'size': int(attr.st_size or 0),
                'mtime': int(attr.st_mtime or 0),
                'mode': mode_str(mode),
                'target': target,
            })
        entries.sort(key=lambda e: (not e['dir'], e['name'].lower()))
        return base, entries


def sftp_read(sess: SshSession, path: str) -> Dict[str, Any]:
    with sess.open_sftp() as sftp:
        full = sftp.normalize(path)
        st = sftp.stat(full)
        if statmod.S_ISDIR(st.st_mode or 0):
            raise ValueError('这是一个目录，不能当文件打开')
        size = int(st.st_size or 0)
        with sftp.open(full, 'rb') as fh:
            raw = fh.read(MAX_READ_BYTES)
        truncated = size > len(raw)
        binary = b'\x00' in raw
        content = ''
        encoding = 'utf-8'
        if not binary:
            try:
                content = raw.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = raw.decode('gbk')
                    encoding = 'gbk'
                except UnicodeDecodeError:
                    binary = True
        return {
            'path': full,
            'size': size,
            'mode': mode_str(st.st_mode or 0),
            'mtime': int(st.st_mtime or 0),
            'binary': binary,
            'encoding': encoding,
            'truncated': truncated,
            'content': content,
        }


def sftp_write(sess: SshSession, path: str, content: str, encoding: str = 'utf-8') -> str:
    with sess.open_sftp() as sftp:
        # 目标文件所在目录先规范化，再拼上文件名，保证相对路径也能定位
        parent = sftp.normalize(posixpath.dirname(path) or '.')
        full = posixpath.join(parent, posixpath.basename(path))
        with sftp.open(full, 'wb') as fh:
            fh.write(content.encode(encoding, errors='replace'))
        return full


def sftp_mkdir(sess: SshSession, path: str) -> str:
    with sess.open_sftp() as sftp:
        full = sftp.normalize(posixpath.dirname(path)) + '/' + posixpath.basename(path)
        sftp.mkdir(full)
        return full


def sftp_rename(sess: SshSession, path: str, target: str) -> None:
    with sess.open_sftp() as sftp:
        sftp.rename(sftp.normalize(path),
                    target if target.startswith('/') else sftp.normalize(target))


def sftp_delete(sess: SshSession, path: str) -> None:
    with sess.open_sftp() as sftp:
        full = sftp.normalize(path)

        def rm(p: str) -> None:
            st = sftp.stat(p)
            if statmod.S_ISDIR(st.st_mode or 0):
                for child in sftp.listdir_attr(p):
                    rm(posixpath.join(p, child.filename))
                sftp.rmdir(p)
                return
            sftp.remove(p)

        rm(full)


def sftp_put_file(sess: SshSession, local_path: str, remote_dir: str,
                  remote_name: str = '') -> str:
    with sess.open_sftp() as sftp:
        base = sftp.normalize(remote_dir)
        # 浏览器传来的文件名只取最后一段，避免路径穿越
        name = remote_name or posixpath.basename(local_path)
        full = posixpath.join(base, posixpath.basename(name))
        sftp.put(local_path, full)
        return full


def sftp_open_read(sess: SshSession, path: str):
    """返回 (sftp, fileobj, size, name)，调用方负责关闭。"""
    sftp = sess.open_sftp()
    full = sftp.normalize(path)
    st = sftp.stat(full)
    if statmod.S_ISDIR(st.st_mode or 0):
        sftp.close()
        raise ValueError('这是一个目录，不能下载')
    return (sftp, sftp.open(full, 'rb'), int(st.st_size or 0), posixpath.basename(full))


def exec_capture(sess: SshSession, cmd: str, timeout: float = 6.0) -> str:
    _, stdout, _ = sess.client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', 'replace').strip()


def list_serial_ports() -> List[Dict[str, str]]:
    ports = []
    try:
        for item in serial.tools.list_ports.comports():
            ports.append({'device': item.device, 'desc': item.description or ''})
    except Exception:
        pass
    if not ports:
        import glob as _glob
        for dev in sorted(set(_glob.glob('/dev/ttyACM*') + _glob.glob('/dev/ttyUSB*'))):
            ports.append({'device': dev, 'desc': ''})
    ports.sort(key=lambda p: p['device'])
    return ports


def open_serial(device: str, baud: int, data_bits: int, stop_bits: int,
                parity: str, flow: str) -> serial.Serial:
    parity_map = {'none': serial.PARITY_NONE,
                  'even': serial.PARITY_EVEN,
                  'odd': serial.PARITY_ODD}
    return serial.Serial(port=device, baudrate=baud, bytesize=data_bits, stopbits=stop_bits,
                         parity=parity_map.get(parity, serial.PARITY_NONE),
                         rtscts=(flow == 'hardware'),
                         timeout=0.05, write_timeout=2.0)


def pump_channel(chan: paramiko.Channel, loop: asyncio.AbstractEventLoop,
                 queue: 'asyncio.Queue', stop: threading.Event) -> None:
    """后台线程：把 SSH channel 的输出搬到 asyncio 队列，收尾时补一个 eof。"""
    try:
        try:
            while not stop.is_set():
                if chan.recv_ready():
                    data = chan.recv(65536)
                    if not data:
                        break
                    loop.call_soon_threadsafe(queue.put_nowait, ('out', data))
                    continue
                if chan.exit_status_ready():
                    while chan.recv_ready():
                        tail = chan.recv(65536)
                        if not tail:
                            break
                        loop.call_soon_threadsafe(queue.put_nowait, ('out', tail))
                    break
                time.sleep(0.02)
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, ('err', str(exc)))
    finally:
        loop.call_soon_threadsafe(queue.put_nowait, ('eof', None))


def pump_serial(ser: serial.Serial, loop: asyncio.AbstractEventLoop,
                queue: 'asyncio.Queue', stop: threading.Event) -> None:
    """后台线程：把串口数据搬到 asyncio 队列，收尾时补一个 eof。"""
    try:
        try:
            while not stop.is_set():
                waiting = ser.in_waiting
                data = ser.read(waiting or 1)
                if data:
                    loop.call_soon_threadsafe(queue.put_nowait, ('out', data))
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, ('err', str(exc)))
    finally:
        loop.call_soon_threadsafe(queue.put_nowait, ('eof', None))


# ---------------------------------------------------------------- HTTP 接口

async def h_ping(request: web.Request) -> web.Response:
    return web.json_response({
        'ok': True,
        'service': 'eai-device-bridge',
        'version': VERSION,
        'serial_default': request.app['cfg'].serial_port,
        'allow_remote_host': request.app['cfg'].allow_remote_host,
    })


async def h_login(request: web.Request) -> web.Response:
    cfg = request.app['cfg']
    ip = request.remote or '?'
    if rate_limited(ip):
        return web.json_response({'ok': False, 'error': '登录失败次数过多，请稍后再试'}, status=429)
    try:
        body = await request.json()
    except Exception:
        return web.json_response({'ok': False, 'error': '请求格式错误'}, status=400)
    user = str(body.get('user') or '').strip()
    password = str(body.get('password') or '')
    host = str(body.get('host') or '127.0.0.1').strip() or '127.0.0.1'
    try:
        port = int(body.get('port') or 22)
    except (TypeError, ValueError):
        port = 22

    if not user:
        return web.json_response({'ok': False, 'error': '请填写用户名'})
    if not cfg.allow_remote_host and host not in ('127.0.0.1', 'localhost', '::1', ''):
        return web.json_response({'ok': False, 'error': '该服务只允许登录本机（127.0.0.1）。'
                                                       '如需登录其它主机，请在设备上以 --allow-remote-host 参数重启服务'})

    # 真正建立 SSH 连接；失败要计入该 IP 的失败次数
    try:
        client = await run_blocking(connect_ssh, host, port, user, password)
    except Exception as exc:
        note_fail(ip)
        return web.json_response({'ok': False, 'error': friendly_error(exc)})

    token = uuid.uuid4().hex
    sess = SshSession(token, client, user, host, port, '/')
    try:
        sess.homedir = await run_blocking(sftp_home, sess)
    except Exception:
        sess.homedir = f'/home/{user}'
    SESSIONS[token] = sess
    LOGIN_FAILS.pop(ip, None)
    ok(f'登录成功：{user}@{host}:{port}（{ip}）')
    return web.json_response({
        'ok': True,
        'token': token,
        'user': user,
        'host': host,
        'port': port,
        'homedir': sess.homedir,
        'version': VERSION,
    })


async def h_logout(request: web.Request) -> web.Response:
    token = request.query.get('token') or ''
    sess = SESSIONS.pop(token, None)
    if sess:
        await run_blocking(sess.close)
    return web.json_response({'ok': True})


async def h_sysinfo(request: web.Request) -> web.Response:
    sess = need_session(request)
    try:
        data = await run_blocking(_collect_sysinfo, sess)
    except Exception as exc:
        return web.json_response({'ok': False, 'error': friendly_error(exc)})
    data['ok'] = True
    return web.json_response(data)


def _collect_sysinfo(sess: SshSession) -> Dict[str, Any]:
    out: Dict[str, Any] = {'user': sess.user, 'host': sess.host, 'homedir': sess.homedir}
    try:
        out['uname'] = exec_capture(sess, 'uname -srm')
    except Exception:
        out['uname'] = ''
    try:
        out['os'] = exec_capture(sess, "cat /etc/os-release 2>/dev/null | sed -n 's/^PRETTY_NAME=//p' | tr -d '\"'")
    except Exception:
        out['os'] = ''
    try:
        out['cpus'] = exec_capture(sess, 'nproc')
    except Exception:
        out['cpus'] = ''
    try:
        out['uptime'] = exec_capture(sess, 'uptime -p 2>/dev/null || uptime')
    except Exception:
        out['uptime'] = ''
    try:
        out['disk'] = exec_capture(sess, f'df -h --output=size,avail,pcent {sess.homedir} 2>/dev/null | tail -1')
    except Exception:
        out['disk'] = ''
    return out


def _json_error(message: str, status: int = 200) -> web.Response:
    return web.json_response({'ok': False, 'error': message}, status=status)


async def h_fs_list(request: web.Request) -> web.Response:
    sess = need_session(request)
    path = request.query.get('path') or sess.homedir
    try:
        base, entries = await run_blocking(sftp_list, sess, path)
    except Exception as exc:
        return _json_error(friendly_error(exc))
    parent = posixpath.dirname(base.rstrip('/')) or '/'
    return web.json_response({
        'ok': True,
        'path': base,
        'parent': parent,
        'homedir': sess.homedir,
        'entries': entries,
    })


async def h_fs_read(request: web.Request) -> web.Response:
    sess = need_session(request)
    path = request.query.get('path') or ''
    if not path:
        return _json_error('缺少 path 参数', 400)
    try:
        data = await run_blocking(sftp_read, sess, path)
    except Exception as exc:
        return _json_error(friendly_error(exc))
    data['ok'] = True
    return web.json_response(data)


async def h_fs_write(request: web.Request) -> web.Response:
    sess = need_session(request)
    try:
        body = await request.json()
    except Exception:
        return _json_error('请求格式错误', 400)
    path = str(body.get('path') or '')
    if not path:
        return _json_error('缺少 path 参数', 400)
    content = body.get('content')
    if content is None:
        return _json_error('缺少 content 参数', 400)
    encoding = str(body.get('encoding') or 'utf-8')
    try:
        full = await run_blocking(sftp_write, sess, path, str(content), encoding)
    except Exception as exc:
        return _json_error(friendly_error(exc))
    return web.json_response({'ok': True, 'path': full, 'bytes': len(str(content))})


async def h_fs_mkdir(request: web.Request) -> web.Response:
    sess = need_session(request)
    body = await request.json()
    path = str(body.get('path') or '')
    if not path:
        return _json_error('缺少 path 参数', 400)
    try:
        full = await run_blocking(sftp_mkdir, sess, path)
    except Exception as exc:
        return _json_error(friendly_error(exc))
    return web.json_response({'ok': True, 'path': full})


async def h_fs_rename(request: web.Request) -> web.Response:
    sess = need_session(request)
    body = await request.json()
    path, target = (str(body.get('path') or ''), str(body.get('target') or ''))
    if not path or not target:
        return _json_error('缺少 path / target 参数', 400)
    try:
        await run_blocking(sftp_rename, sess, path, target)
    except Exception as exc:
        return _json_error(friendly_error(exc))
    return web.json_response({'ok': True})


async def h_fs_delete(request: web.Request) -> web.Response:
    sess = need_session(request)
    body = await request.json()
    path = str(body.get('path') or '')
    if not path:
        return _json_error('缺少 path 参数', 400)
    if path.rstrip('/') in ('/', ''):
        return _json_error('拒绝删除根目录')
    try:
        await run_blocking(sftp_delete, sess, path)
    except Exception as exc:
        return _json_error(friendly_error(exc))
    return web.json_response({'ok': True})


async def h_fs_download(request: web.Request) -> web.StreamResponse:
    sess = need_session(request)
    path = request.query.get('path') or ''
    if not path:
        raise web.HTTPBadRequest(text='缺少 path 参数')
    try:
        sftp, fh, size, name = await run_blocking(sftp_open_read, sess, path)
    except Exception as exc:
        raise web.HTTPNotFound(text=friendly_error(exc))

    resp = web.StreamResponse(status=200, headers={
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(size),
        'Content-Disposition': f"attachment; filename*=UTF-8''{quote(name)}",
        'Cache-Control': 'no-store',
    })
    await resp.prepare(request)
    try:
        try:
            while True:
                chunk = await run_blocking(fh.read, 262144)
                if not chunk:
                    break
                await resp.write(chunk)
        except Exception:
            pass
    finally:
        try:
            fh.close()
            sftp.close()
        except Exception:
            pass
    return resp


async def h_fs_upload(request: web.Request) -> web.Response:
    sess = need_session(request)
    reader = await request.multipart()
    remote_dir = request.query.get('path') or sess.homedir
    saved = []
    tmp_dir = Path(request.app['cfg'].tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    while True:
        part = await reader.next()
        if part is None:
            break
        if part.name != 'file' or not part.filename:
            continue
        safe = os.path.basename(part.filename)
        local = tmp_dir / f'{uuid.uuid4().hex}_{safe}'
        with open(local, 'wb') as out:
            while True:
                chunk = await part.read_chunk(262144)
                if not chunk:
                    break
                out.write(chunk)
        try:
            try:
                full = await run_blocking(sftp_put_file, sess, str(local), remote_dir, safe)
                saved.append(full)
            except Exception as exc:
                return _json_error(f'上传 {safe} 失败：{friendly_error(exc)}')
        finally:
            try:
                local.unlink()
            except Exception:
                pass
    if not saved:
        return _json_error('没有收到文件')
    return web.json_response({'ok': True, 'saved': saved})


async def h_serial_ports(request: web.Request) -> web.Response:
    need_session(request)
    cfg = request.app['cfg']
    ports = await run_blocking(list_serial_ports)
    known = {p['device'] for p in ports}
    if cfg.serial_port and cfg.serial_port not in known:
        ports.insert(0, {'device': cfg.serial_port, 'desc': '默认串口（来自启动参数）'})
    return web.json_response({'ok': True, 'ports': ports, 'busy': sorted(SERIAL_OWNERS.keys())})


# ---------------------------------------------------------------- WebSocket

async def ws_ssh(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30, max_msg_size=4194304)
    await ws.prepare(request)

    sess = get_session(request)
    if sess is None:
        await ws.send_json({'t': 'err', 'd': '会话已失效，请重新登录', 'relogin': True})
        await ws.close()
        return ws

    try:
        cols = max(20, int(request.query.get('cols') or 80))
        rows = max(5, int(request.query.get('rows') or 24))
    except (TypeError, ValueError):
        cols, rows = 80, 24

    transport = sess.client.get_transport()
    if transport is None or not transport.is_active():
        await ws.send_json({'t': 'err', 'd': 'SSH 连接已断开，请重新登录', 'relogin': True})
        await ws.close()
        return ws

    try:
        chan = await run_blocking(transport.open_session)
        await run_blocking(chan.get_pty, 'xterm-256color', cols, rows, 0, 0)
        await run_blocking(chan.invoke_shell)
    except Exception as exc:
        await ws.send_json({'t': 'err', 'd': f'打开终端失败：{friendly_error(exc)}'})
        await ws.close()
        return ws

    sess.channels += 1
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    stop = threading.Event()
    pump = threading.Thread(target=pump_channel, args=(chan, loop, queue, stop),
                            daemon=True, name='ssh-pump')
    pump.start()
    await ws.send_json({'t': 'ready', 'user': sess.user, 'host': sess.host,
                        'homedir': sess.homedir})

    async def sender() -> None:
        while True:
            kind, payload = await queue.get()
            if kind == 'eof':
                try:
                    await ws.send_json({'t': 'exit'})
                except Exception:
                    pass
                return
            if kind == 'err':
                try:
                    await ws.send_json({'t': 'err', 'd': payload})
                except Exception:
                    pass
                continue
            try:
                await ws.send_json({'t': 'out', 'b': b64e(payload)})
            except Exception:
                return

    send_task = asyncio.ensure_future(sender())
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except Exception:
                    continue
                kind = data.get('t')
                if kind == 'in':
                    payload = b64d(data.get('b') or '')
                    if payload:
                        try:
                            await run_blocking(chan.send, payload)
                        except Exception:
                            break
                elif kind == 'resize':
                    c = max(20, int(data.get('c') or 80))
                    r = max(5, int(data.get('r') or 24))
                    try:
                        await run_blocking(chan.resize_pty, c, r)
                    except Exception:
                        pass
            elif msg.type == WSMsgType.ERROR:
                break
    finally:
        stop.set()
        send_task.cancel()
        try:
            await run_blocking(chan.close)
        except Exception:
            pass
        sess.channels = max(0, sess.channels - 1)
    return ws


async def ws_serial(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30, max_msg_size=4194304)
    await ws.prepare(request)

    sess = get_session(request)
    if sess is None:
        await ws.send_json({'t': 'err', 'd': '会话已失效，请重新登录', 'relogin': True})
        await ws.close()
        return ws

    cfg = request.app['cfg']
    device = request.query.get('port') or cfg.serial_port
    try:
        baud = int(request.query.get('baud') or cfg.baud)
        data_bits = int(request.query.get('dataBits') or 8)
        stop_bits = int(request.query.get('stopBits') or 1)
    except (TypeError, ValueError):
        baud, data_bits, stop_bits = cfg.baud, 8, 1
    parity = request.query.get('parity') or 'none'
    flow = request.query.get('flow') or 'none'

    # 同一个串口只允许一个会话独占
    owner = SERIAL_OWNERS.get(device)
    if owner and owner != sess.token:
        await ws.send_json({'t': 'err', 'd': f'{device} 已被其它会话占用'})
        await ws.close()
        return ws

    try:
        ser = await run_blocking(open_serial, device, baud, data_bits, stop_bits, parity, flow)
    except Exception as exc:
        await ws.send_json({'t': 'err', 'd': f'打开串口失败：{exc}'})
        await ws.close()
        return ws

    SERIAL_OWNERS[device] = sess.token
    info(f'串口已打开：{device} @{baud}（{sess.user}）')

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    stop = threading.Event()
    pump = threading.Thread(target=pump_serial, args=(ser, loop, queue, stop),
                            daemon=True, name='serial-pump')
    pump.start()
    await ws.send_json({'t': 'ready', 'port': device, 'baud': baud})

    async def sender() -> None:
        while True:
            kind, payload = await queue.get()
            if kind == 'eof':
                try:
                    await ws.send_json({'t': 'exit'})
                except Exception:
                    pass
                return
            if kind == 'err':
                try:
                    await ws.send_json({'t': 'err', 'd': payload})
                except Exception:
                    pass
                continue
            try:
                await ws.send_json({'t': 'out', 'b': b64e(payload)})
            except Exception:
                return

    send_task = asyncio.ensure_future(sender())
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except Exception:
                    continue
                if data.get('t') == 'in':
                    payload = b64d(data.get('b') or '')
                    if payload:
                        try:
                            await run_blocking(ser.write, payload)
                        except Exception as exc:
                            await ws.send_json({'t': 'err', 'd': f'写入失败：{exc}'})
            elif msg.type == WSMsgType.ERROR:
                break
    finally:
        stop.set()
        send_task.cancel()
        try:
            await run_blocking(ser.close)
        except Exception:
            pass
        SERIAL_OWNERS.pop(device, None)
        info(f'串口已释放：{device}')
    return ws


# ---------------------------------------------------------------- 应用装配

@web.middleware
async def cors_middleware(request: web.Request, handler):
    """课程站点（GitHub Pages 等）与设备服务不同源，统一放开 CORS。"""
    if request.method == 'OPTIONS':
        resp = web.Response(status=204)
    else:
        try:
            resp = await handler(request)
        except web.HTTPException as exc:
            resp = exc
    if isinstance(resp, web.WebSocketResponse):
        return resp
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Session-Token'
    resp.headers['Access-Control-Max-Age'] = '600'
    return resp


async def h_index(request: web.Request) -> web.Response:
    static_dir = request.app['cfg'].static_dir
    if static_dir and (static_dir / 'workspace.html').is_file():
        return web.FileResponse(static_dir / 'workspace.html')
    return web.Response(
        text='<h2>eai-device-bridge 正在运行</h2><p>本服务只提供接口。前端工作台请从课程站点打开，'
             '或把 courses/device/ 目录同步到设备后用 --static 指向它。</p>',
        content_type='text/html', charset='utf-8')


def make_static_handler(static_dir: Path, name: str):
    async def handler(request: web.Request) -> web.Response:
        target = static_dir / name
        if not target.is_file():
            raise web.HTTPNotFound(text=f'{name} 未同步到设备')
        return web.FileResponse(target)
    return handler


async def on_cleanup(app: web.Application) -> None:
    task = app.get('janitor_task')
    if task is not None:
        task.cancel()
    for sess in list(SESSIONS.values()):
        sess.close()
    SESSIONS.clear()


async def janitor(app: web.Application) -> None:
    """每 5 分钟清理一次失效 / 闲置超时的会话。"""
    ttl = app['cfg'].session_ttl
    while True:
        await asyncio.sleep(300)
        now = time.time()
        for token, sess in list(SESSIONS.items()):
            if not sess.alive or (ttl and now - sess.last_seen > ttl):
                SESSIONS.pop(token, None)
                sess.close()


async def start_janitor(app: web.Application) -> None:
    app['janitor_task'] = asyncio.ensure_future(janitor(app))


def build_app(cfg: argparse.Namespace) -> web.Application:
    app = web.Application(middlewares=[cors_middleware], client_max_size=1073741824)
    app['cfg'] = cfg

    app.router.add_get('/api/ping', h_ping)
    app.router.add_post('/api/login', h_login)
    app.router.add_get('/api/logout', h_logout)
    app.router.add_get('/api/sys/info', h_sysinfo)
    app.router.add_get('/api/fs/list', h_fs_list)
    app.router.add_get('/api/fs/read', h_fs_read)
    app.router.add_post('/api/fs/write', h_fs_write)
    app.router.add_post('/api/fs/mkdir', h_fs_mkdir)
    app.router.add_post('/api/fs/rename', h_fs_rename)
    app.router.add_post('/api/fs/delete', h_fs_delete)
    app.router.add_get('/api/fs/download', h_fs_download)
    app.router.add_post('/api/fs/upload', h_fs_upload)
    app.router.add_get('/api/serial/ports', h_serial_ports)
    app.router.add_get('/ws/ssh', ws_ssh)
    app.router.add_get('/ws/serial', ws_serial)

    app.router.add_get('/', h_index)
    static_dir = cfg.static_dir
    if static_dir and static_dir.is_dir():
        for name in ('workspace.html', 'workspace.css', 'workspace.js',
                     'index.html', 'serial.html'):
            app.router.add_get('/' + name, make_static_handler(static_dir, name))
        vendor = static_dir / 'vendor'
        if vendor.is_dir():
            app.router.add_static('/vendor', vendor, show_index=False)

    app.on_cleanup.append(on_cleanup)
    app.on_startup.append(start_janitor)
    return app


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description='具身智能课程 · 设备开发桥接服务（SSH / SFTP / 串口）')
    ap.add_argument('--host', default=DEFAULT_HOST, help='监听地址，默认 0.0.0.0')
    ap.add_argument('--port', type=int, default=DEFAULT_PORT, help='监听端口，默认 8100')
    ap.add_argument('--static', type=str,
                    default=Path(__file__).resolve().parent / 'web',
                    help='前端工作台目录（含 workspace.html），不存在则只提供接口')
    ap.add_argument('--serial-port', default=DEFAULT_SERIAL_PORT, help='默认串口设备')
    ap.add_argument('--baud', type=int, default=DEFAULT_BAUD, help='默认波特率')
    ap.add_argument('--session-ttl', type=int, default=DEFAULT_SESSION_TTL,
                    help='登录会话闲置超时秒数，0 表示不过期')
    ap.add_argument('--allow-remote-host', action='store_true',
                    help='允许用本服务去登录其它主机（默认只允许 127.0.0.1）')
    ap.add_argument('--tmp-dir', default='/tmp/eai-bridge', help='上传中转目录')
    cfg = ap.parse_args(argv)
    static = Path(cfg.static).expanduser()
    if static.is_dir():
        cfg.static_dir = static
    else:
        cfg.static_dir = None
    return cfg


def main() -> None:
    cfg = parse_args()
    banner = (
        f"\n{C.CYAN}具身智能课程 · 设备开发桥接服务{C.END}  v{VERSION}"
        f"\n  监听      http://{cfg.host}:{cfg.port}"
        f"\n  接口      /api/login  /api/fs/*  /api/sys/info  /ws/ssh  /ws/serial\n  前端目录  "
        f"{cfg.static_dir or '（未找到，仅提供接口）'}"
        f"\n  串口默认  {cfg.serial_port} @{cfg.baud}"
        f"\n  登录范围  {'本机 + 其它主机' if cfg.allow_remote_host else '仅本机 127.0.0.1'}"
        f"\n"
    )
    print(banner, flush=True)
    warn('本服务等同于把设备的 shell / 文件系统开放给能访问该端口的人，请只在教学网段使用。')
    web.run_app(build_app(cfg), host=cfg.host, port=cfg.port, print=None)


if __name__ == '__main__':
    main()
