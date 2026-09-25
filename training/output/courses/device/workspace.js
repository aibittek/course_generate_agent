/* ============================================================
   设备开发工作台 · 前端逻辑
   会话列表（SSH 终端 / 文件管理 / 串口 / 远程桌面）+ 多标签 + 分屏 + 独立窗口
   跨不过浏览器边界的协议（SSH / SFTP）统一由设备端 device_bridge.py 转发（设备与电脑在同一局域网）
   串口为本机 USB 直连（浏览器 Web Serial），数据线插在电脑上，不经任何网络服务
   ============================================================ */
(function () {
  'use strict';

  /* ---------------------------------------------------------- 基础工具 */
  var $ = function (id) { return document.getElementById(id); };
  var LS_SESSIONS = 'eai_device_sessions_v2';
  var LS_PREFS = 'eai_device_prefs_v2';

  var ICON = { term: '⌨', sftp: '📁', serial: '📡', vnc: '🖥' };
  var KIND_NAME = { term: 'SSH 终端', sftp: '文件管理', serial: '串口', vnc: '远程桌面' };
  var KINDS = ['term', 'sftp', 'serial', 'vnc'];
  var BAUD_LIST = [1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 76800, 115200,
    128000, 230400, 256000, 460800, 500000, 921600, 1000000, 1500000, 2000000, 3000000];
  var DEF_BRIDGE_PORT = 8100;
  var DEF_SSH_PORT = 22;
  var DEF_VNC_PORT = 6080;
  var uid = 0;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function lsGet(k, dflt) {
    try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : dflt; } catch (e) { return dflt; }
  }
  function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } }

  function b64enc(u8) {
    var s = '', CH = 0x8000;
    for (var i = 0; i < u8.length; i += CH) s += String.fromCharCode.apply(null, u8.subarray(i, i + CH));
    return btoa(s);
  }
  function b64dec(b) {
    var s = atob(b), u8 = new Uint8Array(s.length);
    for (var i = 0; i < s.length; i++) u8[i] = s.charCodeAt(i);
    return u8;
  }
  function enc(text) { return new TextEncoder().encode(text); }

  function fmtSize(n) {
    if (n == null) return '';
    if (n < 1024) return n + ' B';
    var u = ['KB', 'MB', 'GB', 'TB'], i = -1, v = n;
    do { v /= 1024; i++; } while (v >= 1024 && i < u.length - 1);
    return (v < 10 ? v.toFixed(1) : Math.round(v)) + ' ' + u[i];
  }
  function fmtTime(ts) {
    if (!ts) return '';
    var d = new Date(ts * 1000), p = function (x) { return String(x).padStart(2, '0'); };
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
      ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }
  function stamp() {
    var d = new Date(), p = function (n, w) { return String(n).padStart(w || 2, '0'); };
    return '[' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds()) +
      '.' + p(d.getMilliseconds(), 3) + '] ';
  }
  function b64url(str) {
    return btoa(unescape(encodeURIComponent(str))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function unb64url(str) {
    var s = str.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    return decodeURIComponent(escape(atob(s)));
  }
  function joinPath(dir, name) {
    if (!dir) dir = '/';
    return (dir === '/' ? '' : dir.replace(/\/+$/, '')) + '/' + name;
  }
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function newId() { return 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }

  /* ---------------------------------------------------------- 状态 */
  var S = {
    sessions: [],        // 已保存的会话（左侧列表）
    conns: {},           // bridgeKey -> 已登录连接 { token, user, sshHost, sshPort, homedir, base, wsBase }
    prefs: {},           // 上次用过的设备信息，用于新建时预填
    sameOrigin: null,    // 页面由桥接服务自己托管时记录 { addr, port }
    split: false, activePane: 'L',
    panes: { L: { tabs: [], active: null }, R: { tabs: [], active: null } },
    seq: 0, popout: false
  };

  function allTabs() { return S.panes.L.tabs.concat(S.panes.R.tabs); }
  function findTab(id) {
    var t = S.panes.L.tabs.filter(function (x) { return x.id === id; })[0];
    return t || S.panes.R.tabs.filter(function (x) { return x.id === id; })[0];
  }
  function paneOf(id) {
    if (S.panes.L.tabs.some(function (x) { return x.id === id; })) return 'L';
    if (S.panes.R.tabs.some(function (x) { return x.id === id; })) return 'R';
    return null;
  }

  /* ---------------------------------------------------------- 状态栏 / 提示 */
  function setStatus(text, kind) {
    var dot = $('sbDot');
    if (dot) dot.className = 'sdot' + (kind ? ' ' + kind : '');
    if ($('sbText')) $('sbText').textContent = text;
  }
  var toastTimer = null;
  function toast(msg, kind) {
    var box = $('toast');
    box.className = 'toast' + (kind ? ' ' + kind : '');
    box.textContent = msg;
    box.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { box.hidden = true; }, kind === 'bad' ? 7000 : 3600);
  }
  function setDeviceLabel(text) {
    if ($('sbBridge')) $('sbBridge').textContent = text || '';
  }
  function setUserLabel(text) { if ($('wbUser')) $('wbUser').textContent = text || '未连接'; }

  /* ==========================================================
     会话仓库（localStorage）
     ========================================================== */
  function blankSession(kind) {
    return {
      id: newId(), kind: kind || 'term', name: '',
      addr: '', bridgePort: DEF_BRIDGE_PORT,
      user: '', password: '', remember: true,
      sshHost: '127.0.0.1', sshPort: DEF_SSH_PORT, startDir: '',
      serialPort: '', serialLabel: '', baud: 115200, dataBits: 8, stopBits: 1, parity: 'none',
      vncPort: DEF_VNC_PORT, at: 0
    };
  }

  function loadSessions() {
    var list = lsGet(LS_SESSIONS, null);
    if (!Array.isArray(list)) list = [];
    S.sessions = list.filter(function (s) { return s && s.id && KINDS.indexOf(s.kind) >= 0; });
    // 迁移：串口统一为本机直连（Web Serial），清掉历史的设备端串口字段
    S.sessions.forEach(function (s) {
      if (s.kind === 'serial') {
        delete s.target;
        s.addr = ''; s.user = ''; s.password = ''; s.bridgePort = DEF_BRIDGE_PORT;
        if (!s.serialLabel) s.serialLabel = s.serialPort || '';
      }
    });
  }
  function saveSessions() {
    lsSet(LS_SESSIONS, S.sessions.map(function (s) {
      var c = clone(s);
      if (!c.remember) c.password = '';
      return c;
    }));
  }
  function findSession(id) {
    return S.sessions.filter(function (s) { return s.id === id; })[0] || null;
  }
  function upsertSession(sess) {
    var i = S.sessions.findIndex(function (s) { return s.id === sess.id; });
    if (i < 0) S.sessions.push(sess); else S.sessions[i] = sess;
    saveSessions();
  }
  function removeSession(id) {
    S.sessions = S.sessions.filter(function (s) { return s.id !== id; });
    saveSessions();
  }
  function savePrefs(s) {
    S.prefs = { addr: s.addr, bridgePort: s.bridgePort, user: s.user };
    lsSet(LS_PREFS, S.prefs);
  }

  function sessTitle(s) {
    if (s.name) return s.name;
    if (s.kind === 'serial') return '本机串口 @' + (s.baud || 115200);
    if (s.kind === 'vnc') return (s.addr || '?') + ':' + (s.vncPort || DEF_VNC_PORT);
    return (s.user ? s.user + '@' : '') + (s.addr || '?');
  }
  function sessSub(s) {
    if (s.kind === 'serial') {
      return '本机 USB 直连 · ' + (s.serialLabel || s.serialPort || '未选串口') + ' @' + (s.baud || 115200);
    }
    if (s.kind === 'vnc') {
      return 'noVNC · ' + (s.addr || '?') + ':' + (s.vncPort || DEF_VNC_PORT);
    }
    return (s.addr || '?') + ':' + (s.bridgePort || DEF_BRIDGE_PORT) + ' · ' + (s.user || '?');
  }

  /* ==========================================================
     连接：每个会话各自登录，token 按桥接地址缓存
     ========================================================== */
  function bridgeKey(s) { return (s.addr || '') + ':' + (s.bridgePort || DEF_BRIDGE_PORT); }
  function bridgeBase(s) { return 'http://' + s.addr + ':' + (s.bridgePort || DEF_BRIDGE_PORT); }
  function bridgeWs(s) {
    var proto = (location.protocol === 'https:') ? 'wss://' : 'ws://';
    return proto + s.addr + ':' + (s.bridgePort || DEF_BRIDGE_PORT);
  }

  function login(sess) {
    var base = bridgeBase(sess);
    return fetch(base + '/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user: sess.user, password: sess.password || '',
        host: sess.sshHost || '127.0.0.1', port: sess.sshPort || DEF_SSH_PORT
      })
    })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok) throw new Error((j && j.error) || '登录失败');
        var conn = {
          key: bridgeKey(sess), base: base, wsBase: bridgeWs(sess),
          token: j.token, user: j.user, sshHost: j.host, sshPort: j.port,
          homedir: j.homedir || '/', addr: sess.addr, sessionId: sess.id
        };
        S.conns[conn.key] = conn;
        return conn;
      })
      .catch(function (e) {
        if (e instanceof TypeError) throw new Error('无法连接桥接服务 ' + base + '，请确认设备上已运行 device_bridge.py');
        throw e;
      });
  }

  function ensureLogin(sess) {
    var c = S.conns[bridgeKey(sess)];
    if (c && c.token) { c.sessionId = sess.id; return Promise.resolve(c); }
    return login(sess);
  }

  function apiURL(conn, path, params) {
    var q = new URLSearchParams();
    if (conn && conn.token) q.set('token', conn.token);
    Object.keys(params || {}).forEach(function (k) {
      if (params[k] != null) q.set(k, params[k]);
    });
    var qs = q.toString();
    return (conn ? conn.base : '') + path + (qs ? '?' + qs : '');
  }
  function dropConn(conn) {
    if (!conn) return;
    delete S.conns[conn.key];
    setStatus('会话已失效，请重新连接', 'err');
    toast('设备端会话已失效（可能被超时回收或服务重启），请重新打开该会话。', 'bad');
  }
  function apiGet(conn, path, params) {
    return fetch(apiURL(conn, path, params), { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .catch(function (e) { return { ok: false, error: '无法连接桥接服务：' + e.message }; });
  }
  function apiPost(conn, path, body, params) {
    return fetch(apiURL(conn, path, params), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {})
    })
      .then(function (r) { return r.json(); })
      .catch(function (e) { return { ok: false, error: '无法连接桥接服务：' + e.message }; });
  }
  function authCheck(conn, json) {
    if (json && json.relogin) { dropConn(conn); return true; }
    return false;
  }

  function loadSysInfo(conn) {
    if (!conn) { $('sideSys').innerHTML = ''; return; }
    apiGet(conn, '/api/sys/info').then(function (j) {
      if (authCheck(conn, j) || !j || !j.ok) return;
      var rows = [
        ['设备', conn.addr + ':' + (conn.base.split(':').pop())],
        ['用户', j.user + '@' + j.host],
        ['系统', j.os || j.uname || '—'],
        ['内核', j.uname || '—'],
        ['CPU', (j.cpus ? j.cpus + ' 核' : '—')],
        ['家目录', j.homedir || '—'],
        ['磁盘', j.disk || '—'],
        ['运行', j.uptime || '—']
      ];
      $('sideSys').innerHTML = rows.map(function (r) {
        return '<div><span class="k">' + esc(r[0]) + '</span> ' + esc(r[1]) + '</div>';
      }).join('');
    });
  }

  /* ---------------------------------------------------------- 通用右键菜单 */
  function showMenu(x, y, items) {
    var box = $('ctx');
    box.innerHTML = '';
    items.forEach(function (it) {
      if (it.sep) { box.appendChild(document.createElement('hr')); return; }
      var b = document.createElement('button');
      b.textContent = it.label;
      if (it.danger) b.className = 'danger';
      b.addEventListener('click', function () { hideMenu(); it.fn(); });
      box.appendChild(b);
    });
    box.hidden = false;
    var w = box.offsetWidth, h = box.offsetHeight;
    box.style.left = Math.min(x, window.innerWidth - w - 8) + 'px';
    box.style.top = Math.min(y, window.innerHeight - h - 8) + 'px';
  }
  function hideMenu() { $('ctx').hidden = true; }
  document.addEventListener('click', hideMenu);
  document.addEventListener('contextmenu', function (e) {
    var t = e.target;
    if (!t || !t.closest || (!t.closest('.tab') && !t.closest('.files') &&
      !t.closest('.side-item') && !t.closest('.side-group'))) hideMenu();
  });

  /* ==========================================================
     视图：SSH 终端
     ========================================================== */
  function TermView(cfg, conn) {
    var el = document.createElement('div');
    el.className = 'view termview';
    var host = document.createElement('div');
    host.className = 'termhost';
    var bar = document.createElement('div');
    bar.className = 'term-status';
    bar.innerHTML = '<span class="st">正在连接…</span>';
    el.appendChild(host);
    el.appendChild(bar);

    var term = null, fit = null, ws = null, ro = null, closed = false, ready = false;

    function say(text, cls) {
      bar.innerHTML = '<span class="' + (cls || 'st') + '"></span>';
      bar.firstChild.textContent = text;
    }
    function connect() {
      if (!window.Terminal) { say('未找到 xterm.js（vendor/xterm 目录缺失），终端无法工作', 'bad'); return; }
      if (!conn) { say('缺少连接信息', 'bad'); return; }
      if (term) { try { term.dispose(); } catch (e) { } term = null; }
      host.innerHTML = '';
      term = new window.Terminal({
        fontFamily: "'Cascadia Code','JetBrains Mono',Consolas,'Courier New',monospace",
        fontSize: 13, lineHeight: 1.25, cursorBlink: true, scrollback: 8000,
        allowProposedApi: true, convertEol: false,
        theme: {
          background: '#0f172a', foreground: '#e2e8f0', cursor: '#7dd3fc',
          selectionBackground: '#334155', black: '#1e293b', red: '#f87171',
          green: '#5eead4', yellow: '#fbbf24', blue: '#7dd3fc',
          magenta: '#c4b5fd', cyan: '#67e8f9', white: '#e2e8f0'
        }
      });
      fit = new window.FitAddon.FitAddon();
      term.loadAddon(fit);
      if (window.WebLinksAddon) term.loadAddon(new window.WebLinksAddon.WebLinksAddon());
      term.open(host);
      doFit();
      term.onData(function (d) {
        if (ws && ws.readyState === 1) ws.send(JSON.stringify({ t: 'in', b: b64enc(enc(d)) }));
      });
      term.onResize(function (sz) {
        if (ws && ws.readyState === 1) ws.send(JSON.stringify({ t: 'resize', c: sz.cols, r: sz.rows }));
      });
      openWS();
    }
    function doFit() {
      if (!fit || !term) return;
      var r = host.getBoundingClientRect();
      if (r.width < 20 || r.height < 20) return;
      try { fit.fit(); } catch (e) { }
    }
    function openWS() {
      var cols = (term && term.cols) || 80, rows = (term && term.rows) || 24;
      var url = conn.wsBase + '/ws/ssh?token=' + encodeURIComponent(conn.token) +
        '&cols=' + cols + '&rows=' + rows;
      try { ws = new WebSocket(url); } catch (e) {
        say('无法建立 WebSocket：' + e.message, 'bad'); return;
      }
      ws.onopen = function () { say('已连接 · ' + conn.user + '@' + conn.sshHost, 'good'); };
      ws.onmessage = function (ev) {
        var m;
        try { m = JSON.parse(ev.data); } catch (e) { return; }
        if (m.t === 'out') {
          term.write(b64dec(m.b));
        } else if (m.t === 'ready') {
          ready = true;
          say('已连接 · ' + m.user + '@' + m.host + ' · ' + m.homedir, 'good');
          if (cfg.startDir) {
            term.write('\x1b[90m# 进入 ' + cfg.startDir + '\x1b[0m\r');
            ws.send(JSON.stringify({ t: 'in', b: b64enc(enc('cd ' + cfg.startDir + '\n')) }));
          }
        } else if (m.t === 'err') {
          term.write('\r\n\x1b[31m' + m.d + '\x1b[0m\r\n');
          say(m.d, 'bad');
          if (m.relogin) dropConn(conn);
        } else if (m.t === 'exit') {
          term.write('\r\n\x1b[90m[会话已结束]\x1b[0m\r\n');
          say('会话已结束', 'bad');
        }
      };
      ws.onclose = function () {
        if (closed) return;
        if (ready) say('连接已断开 · 关闭标签可释放', 'bad');
        ready = false;
      };
      ws.onerror = function () { say('WebSocket 错误，请检查桥接服务是否在线', 'bad'); };
    }
    function disconnect() {
      closed = true;
      try { if (ws) ws.close(); } catch (e) { }
      ws = null;
      try { if (ro) ro.disconnect(); } catch (e) { }
    }

    return {
      el: el, kind: 'term',
      title: cfg.title || (conn ? conn.user + '@' + conn.addr : 'SSH 终端'),
      mount: function () {
        connect();
        if (window.ResizeObserver) {
          ro = new ResizeObserver(function () { doFit(); });
          ro.observe(host);
        }
      },
      show: function () { doFit(); if (term) term.focus(); },
      hide: function () { },
      refit: doFit,
      close: function () {
        disconnect();
        try { if (term) term.dispose(); } catch (e) { }
        term = null;
      }
    };
  }

  /* ==========================================================
     视图：文件管理（SFTP）
     ========================================================== */
  function SftpView(cfg, conn) {
    var el = document.createElement('div');
    el.className = 'view sftpview';

    el.innerHTML = [
      '<div class="tb">',
      '  <button class="tbbtn" data-a="up" title="上级目录">↑</button>',
      '  <input class="crumb" data-a="path" spellcheck="false" autocomplete="off">',
      '  <button class="tbbtn" data-a="go">跳转</button>',
      '  <button class="tbbtn" data-a="reload">⟳</button>',
      '  <span class="sep"></span>',
      '  <button class="tbbtn" data-a="mkdir">新建文件夹</button>',
      '  <button class="tbbtn primary" data-a="upload">上传文件</button>',
      '  <input type="file" multiple hidden data-a="fileinput">',
      '  <span class="flex"></span>',
      '  <button class="tbbtn" data-a="download" disabled>下载</button>',
      '  <button class="tbbtn" data-a="rename" disabled>重命名</button>',
      '  <button class="tbbtn danger" data-a="delete" disabled>删除</button>',
      '</div>',
      '<div class="sftp-body">',
      '  <div class="files">',
      '    <div class="dropmask">松开即可上传到当前目录</div>',
      '    <table><thead><tr><th>名称</th><th>大小</th><th>权限</th><th>修改时间</th></tr></thead>',
      '    <tbody></tbody></table>',
      '  </div>',
      '  <div class="editor">',
      '    <div class="ed-head">',
      '      <span class="ed-name">未打开文件</span>',
      '      <span class="ed-meta"></span>',
      '      <button class="tbbtn primary" data-a="save" disabled>保存</button>',
      '      <button class="tbbtn" data-a="closefile" disabled>关闭</button>',
      '    </div>',
      '    <div class="ed-body"><div class="ed-gutter">1</div>',
      '      <textarea class="ed-area" spellcheck="false" wrap="off" disabled></textarea></div>',
      '    <div class="ed-hint" data-a="edhint">双击左侧文件即可在此编辑，Ctrl+S 保存。</div>',
      '  </div>',
      '</div>'
    ].join('');

    var tbody = el.querySelector('tbody');
    var filesBox = el.querySelector('.files');
    var crumb = el.querySelector('[data-a="path"]');
    var body = el.querySelector('.sftp-body');
    var edName = el.querySelector('.ed-name');
    var edMeta = el.querySelector('.ed-meta');
    var edArea = el.querySelector('.ed-area');
    var edGutter = el.querySelector('.ed-gutter');
    var edHint = el.querySelector('[data-a="edhint"]');
    var fileInput = el.querySelector('[data-a="fileinput"]');

    var cwd = cfg.startDir || (conn && conn.homedir) || '/';
    var entries = [];
    var selected = null;
    var opened = null;
    var busy = false;

    function btn(a) { return el.querySelector('[data-a="' + a + '"]'); }
    function selActions() {
      var has = !!selected;
      ['download', 'rename', 'delete'].forEach(function (a) { btn(a).disabled = !has; });
    }
    function setHint(html) { edHint.innerHTML = html; }

    function load(path) {
      if (busy) return;
      busy = true;
      setStatus('读取目录 ' + path + ' …', 'busy');
      apiGet(conn, '/api/fs/list', { path: path }).then(function (j) {
        busy = false;
        if (authCheck(conn, j)) return;
        if (!j || !j.ok) { setStatus('读取失败：' + ((j && j.error) || '未知错误'), 'err'); return; }
        cwd = j.path;
        crumb.value = cwd;
        entries = j.entries || [];
        selected = null;
        render();
        selActions();
        setStatus('目录 ' + cwd + ' · ' + entries.length + ' 项', 'on');
      });
    }
    function render() {
      tbody.innerHTML = '';
      if (!entries.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty">空目录</td></tr>';
        return;
      }
      entries.forEach(function (e) {
        var tr = document.createElement('tr');
        var ico = e.dir ? '📁' : (e.link ? '🔗' : fileIcon(e.name));
        tr.innerHTML =
          '<td class="nm"><span class="ico">' + ico + '</span>' +
          '<span class="txt' + (e.link ? ' lnk' : '') + '"></span></td>' +
          '<td class="sz">' + (e.dir ? '—' : fmtSize(e.size)) + '</td>' +
          '<td class="md">' + esc(e.mode) + '</td>' +
          '<td class="mt">' + fmtTime(e.mtime) + '</td>';
        tr.querySelector('.txt').textContent = e.name + (e.link && e.target ? ' → ' + e.target : '');
        tr.addEventListener('click', function () {
          selected = e;
          Array.prototype.forEach.call(tbody.querySelectorAll('tr'), function (x) { x.classList.remove('sel'); });
          tr.classList.add('sel');
          selActions();
        });
        tr.addEventListener('dblclick', function () {
          if (e.dir) load(joinPath(cwd, e.name));
          else openFile(joinPath(cwd, e.name));
        });
        tr.addEventListener('contextmenu', function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          selected = e;
          Array.prototype.forEach.call(tbody.querySelectorAll('tr'), function (x) { x.classList.remove('sel'); });
          tr.classList.add('sel');
          selActions();
          var full = joinPath(cwd, e.name);
          var items = [];
          if (e.dir) items.push({ label: '进入目录', fn: function () { load(full); } });
          else items.push({ label: '编辑', fn: function () { openFile(full); } });
          if (!e.dir) items.push({ label: '下载', fn: function () { download(full); } });
          items.push({ sep: true });
          items.push({ label: '重命名', fn: function () { rename(full, e.name); } });
          items.push({ label: '复制路径', fn: function () { copyText(full); } });
          items.push({ sep: true });
          items.push({ label: '删除', danger: true, fn: function () { del(full, e.name, e.dir); } });
          showMenu(ev.clientX, ev.clientY, items);
        });
        tbody.appendChild(tr);
      });
    }
    function fileIcon(name) {
      var ext = (name.split('.').pop() || '').toLowerCase();
      if (['py', 'js', 'ts', 'json', 'yaml', 'yml', 'cpp', 'c', 'h', 'hpp', 'sh'].indexOf(ext) >= 0) return '📜';
      if (['md', 'txt', 'log', 'csv', 'rst'].indexOf(ext) >= 0) return '📄';
      if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'bmp', 'webp'].indexOf(ext) >= 0) return '🖼';
      if (['zip', 'tar', 'gz', 'xz', 'bz2', '7z'].indexOf(ext) >= 0) return '🗜';
      if (['stl', 'obj', 'urdf', 'dae', 'gltf', 'glb'].indexOf(ext) >= 0) return '🧩';
      return '📄';
    }

    function openFile(path) {
      setStatus('读取文件 ' + path + ' …', 'busy');
      apiGet(conn, '/api/fs/read', { path: path }).then(function (j) {
        if (authCheck(conn, j)) return;
        if (!j || !j.ok) { setStatus('打开失败：' + ((j && j.error) || '未知错误'), 'err'); return; }
        if (j.binary) {
          setStatus('二进制文件，不能在线编辑，已改为下载', 'err');
          download(path);
          return;
        }
        opened = { path: j.path, encoding: j.encoding || 'utf-8', dirty: false };
        body.classList.add('editing');
        edName.textContent = j.path;
        edMeta.textContent = fmtSize(j.size) + ' · ' + (j.encoding || 'utf-8') + ' · ' + j.mode;
        edArea.value = j.content;
        edArea.disabled = false;
        btn('save').disabled = false;
        btn('closefile').disabled = false;
        if (j.truncated) setHint('<span class="warn">文件较大，仅载入前 2 MB；保存会覆盖整个文件，请谨慎。</span>');
        else setHint('Ctrl+S 保存 · Tab 缩进 · 关闭前请先保存');
        updateGutter();
        setStatus('已打开 ' + j.path, 'on');
      });
    }
    function updateGutter() {
      var n = edArea.value.split('\n').length;
      var out = [];
      for (var i = 1; i <= n; i++) out.push(i);
      edGutter.textContent = out.join('\n');
      edGutter.scrollTop = edArea.scrollTop;
    }
    function saveFile() {
      if (!opened) return;
      var content = edArea.value;
      btn('save').disabled = true;
      setStatus('保存中…', 'busy');
      apiPost(conn, '/api/fs/write', { path: opened.path, content: content, encoding: opened.encoding })
        .then(function (j) {
          btn('save').disabled = false;
          if (authCheck(conn, j)) return;
          if (!j || !j.ok) { setStatus('保存失败：' + ((j && j.error) || '未知错误'), 'err'); return; }
          opened.dirty = false;
          setStatus('已保存 ' + j.path + '（' + fmtSize(j.bytes) + '）', 'on');
          setHint('已保存 · Ctrl+S 再次保存');
          load(cwd);
        });
    }
    function closeFile() {
      opened = null;
      body.classList.remove('editing');
      edArea.value = '';
      edArea.disabled = true;
      edName.textContent = '未打开文件';
      edMeta.textContent = '';
      btn('save').disabled = true;
      btn('closefile').disabled = true;
      setHint('双击左侧文件即可在此编辑，Ctrl+S 保存。');
    }

    function mkdir() {
      var name = prompt('新文件夹名称：');
      if (!name) return;
      apiPost(conn, '/api/fs/mkdir', { path: joinPath(cwd, name.trim()) }).then(function (j) {
        if (authCheck(conn, j)) return;
        if (!j.ok) { alert('创建失败：' + j.error); return; }
        load(cwd);
      });
    }
    function rename(path, old) {
      var name = prompt('重命名 / 移动到（可填绝对路径）：', old);
      if (!name || name === old) return;
      var target = name.indexOf('/') === 0 ? name.trim() : joinPath(cwd, name.trim());
      apiPost(conn, '/api/fs/rename', { path: path, target: target }).then(function (j) {
        if (authCheck(conn, j)) return;
        if (!j.ok) { alert('重命名失败：' + j.error); return; }
        load(cwd);
      });
    }
    function del(path, name, isDir) {
      if (!confirm('确定删除 ' + name + (isDir ? '（含其中全部内容）' : '') + ' ？此操作不可撤销。')) return;
      apiPost(conn, '/api/fs/delete', { path: path }).then(function (j) {
        if (authCheck(conn, j)) return;
        if (!j.ok) { alert('删除失败：' + j.error); return; }
        load(cwd);
      });
    }
    function download(path) {
      var a = document.createElement('a');
      a.href = apiURL(conn, '/api/fs/download', { path: path });
      a.download = '';
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
    function copyText(text) {
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(function () {
        setStatus('已复制：' + text, 'on');
      }, function () { prompt('手动复制：', text); });
      else prompt('手动复制：', text);
    }
    function upload(files) {
      if (!files || !files.length) return;
      var fd = new FormData();
      for (var i = 0; i < files.length; i++) fd.append('file', files[i], files[i].name);
      setStatus('上传 ' + files.length + ' 个文件…', 'busy');
      fetch(apiURL(conn, '/api/fs/upload', { path: cwd }), { method: 'POST', body: fd })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (authCheck(conn, j)) return;
          if (!j.ok) { setStatus('上传失败：' + j.error, 'err'); return; }
          setStatus('已上传 ' + j.saved.length + ' 个文件到 ' + cwd, 'on');
          load(cwd);
        })
        .catch(function (e) { setStatus('上传失败：' + e.message, 'err'); });
    }

    el.addEventListener('click', function (e) {
      var a = e.target.getAttribute && e.target.getAttribute('data-a');
      if (!a) return;
      if (a === 'up') {
        var parent = cwd.replace(/\/+$/, '').split('/').slice(0, -1).join('/') || '/';
        load(parent);
      } else if (a === 'go') load(crumb.value.trim() || '/');
      else if (a === 'reload') load(cwd);
      else if (a === 'mkdir') mkdir();
      else if (a === 'upload') fileInput.click();
      else if (a === 'download' && selected) download(joinPath(cwd, selected.name));
      else if (a === 'rename' && selected) rename(joinPath(cwd, selected.name), selected.name);
      else if (a === 'delete' && selected) del(joinPath(cwd, selected.name), selected.name, selected.dir);
      else if (a === 'save') saveFile();
      else if (a === 'closefile') closeFile();
    });
    crumb.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); load(crumb.value.trim() || '/'); }
    });
    fileInput.addEventListener('change', function () { upload(this.files); this.value = ''; });
    edArea.addEventListener('input', function () { updateGutter(); if (opened) opened.dirty = true; });
    edArea.addEventListener('scroll', function () { edGutter.scrollTop = edArea.scrollTop; });
    edArea.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) { e.preventDefault(); saveFile(); return; }
      if (e.key === 'Tab') {
        e.preventDefault();
        var st = this.selectionStart, en = this.selectionEnd;
        this.value = this.value.slice(0, st) + '  ' + this.value.slice(en);
        this.selectionStart = this.selectionEnd = st + 2;
        updateGutter();
      }
    });
    ['dragenter', 'dragover'].forEach(function (t) {
      filesBox.addEventListener(t, function (e) { e.preventDefault(); filesBox.classList.add('drag'); });
    });
    ['dragleave', 'drop'].forEach(function (t) {
      filesBox.addEventListener(t, function (e) { e.preventDefault(); filesBox.classList.remove('drag'); });
    });
    filesBox.addEventListener('drop', function (e) {
      if (e.dataTransfer && e.dataTransfer.files) upload(e.dataTransfer.files);
    });

    return {
      el: el, kind: 'sftp',
      title: cfg.title || ('文件 · ' + (conn ? conn.homedir : '/')),
      mount: function () { load(cwd); },
      show: function () { },
      hide: function () { },
      refit: function () { },
      close: function () { }
    };
  }

  /* ==========================================================
     视图：本机串口（Web Serial，USB 直连，不经过网络）
     ========================================================== */
  function LocalSerialView(cfg) {
    var el = document.createElement('div');
    el.className = 'view serialview';
    var n = ++uid;
    var portListId = 'lp' + n, baudListId = 'lb' + n;

    el.innerHTML = [
      '<div class="tb">',
      '  <div class="f"><label>系统串口</label>',
      '    <input data-a="port" list="' + portListId + '" spellcheck="false" autocomplete="off"',
      '      style="min-width:200px" placeholder="serial:1（连接时选择）">',
      '    <datalist id="' + portListId + '"><option value="serial:1">连接时由系统弹窗选择</option></datalist></div>',
      '  <div class="f"><label>波特率</label>',
      '    <input data-a="baud" list="' + baudListId + '" inputmode="numeric" style="width:110px">',
      '    <datalist id="' + baudListId + '">' +
      BAUD_LIST.map(function (b) { return '<option value="' + b + '"></option>'; }).join('') +
      '</datalist></div>',
      '  <div class="f"><label>数据位</label><select data-a="dataBits"><option selected>8</option><option>7</option></select></div>',
      '  <div class="f"><label>停止位</label><select data-a="stopBits"><option selected>1</option><option>2</option></select></div>',
      '  <div class="f"><label>校验</label><select data-a="parity"><option value="none" selected>无</option><option value="even">偶</option><option value="odd">奇</option></select></div>',
      '  <div class="f"><label>流控</label><select data-a="flow"><option value="none" selected>无</option><option value="hardware">RTS/CTS</option></select></div>',
      '  <span class="sep"></span>',
      '  <button class="tbbtn primary" data-a="connect">打开串口</button>',
      '  <button class="tbbtn" data-a="disconnect" disabled>断开</button>',
      '  <button class="tbbtn" data-a="clear">清空</button>',
      '  <button class="tbbtn" data-a="scan">扫描</button>',
      '  <span class="flex"></span>',
      '  <div class="serial-state"><span class="sdot" data-a="dot"></span><span data-a="state">未连接</span></div>',
      '</div>',
      '<div class="tb">',
      '  <div class="f"><label>行尾符</label><select data-a="eol">',
      '    <option value="crlf" selected>CRLF (\\r\\n)</option><option value="lf">LF (\\n)</option>',
      '    <option value="cr">CR (\\r)</option><option value="">无</option></select></div>',
      '  <div class="f"><label>显示方式</label><select data-a="view"><option value="text" selected>文本</option><option value="hex">十六进制</option></select></div>',
      '  <label class="chk"><input type="checkbox" data-a="ts"> 时间戳</label>',
      '  <label class="chk"><input type="checkbox" data-a="echo"> 本地回显</label>',
      '</div>',
      '<div class="serial-console" data-a="console"></div>',
      '<div class="serial-send">',
      '  <input data-a="input" placeholder="输入要发送的内容，回车发送…" autocomplete="off" spellcheck="false" disabled>',
      '  <button class="tbbtn primary" data-a="send" disabled>发送</button>',
      '</div>'
    ].join('');

    var cons = el.querySelector('[data-a="console"]');
    var input = el.querySelector('[data-a="input"]');
    var port = null, reader = null, writer = null, keepReading = false, closed = false;
    var history = [], hIdx = -1;
    var HAS = ('serial' in navigator);

    function q(a) { return el.querySelector('[data-a="' + a + '"]'); }
    function setState(kind, text) {
      q('dot').className = 'sdot' + (kind ? ' ' + kind : '');
      q('state').textContent = text;
    }
    function lock(on) {
      ['port', 'baud', 'dataBits', 'stopBits', 'parity', 'flow'].forEach(function (a) { q(a).disabled = on; });
      q('connect').disabled = on;
      q('disconnect').disabled = !on;
      input.disabled = !on;
      q('send').disabled = !on;
    }
    function nearBottom() { return cons.scrollHeight - cons.scrollTop - cons.clientHeight < 40; }
    function write(text, cls) {
      var stick = nearBottom();
      if (q('ts').checked && cls !== 'sys') {
        var ts = document.createElement('span');
        ts.className = 'ts'; ts.textContent = stamp(); cons.appendChild(ts);
      }
      var sp = document.createElement('span');
      if (cls) sp.className = cls;
      sp.textContent = text;
      cons.appendChild(sp);
      if (stick) cons.scrollTop = cons.scrollHeight;
    }
    function sys(m) { write(m + '\n', 'sys'); }
    function writeBytes(u8) {
      if (q('view').value === 'hex') {
        var a = [];
        for (var i = 0; i < u8.length; i++) a.push(u8[i].toString(16).padStart(2, '0'));
        write(a.join(' ') + ' ', '');
      } else {
        write(new TextDecoder('utf-8').decode(u8), '');
      }
    }
    function openOpts() {
      return {
        baudRate: parseInt(q('baud').value, 10) || 115200,
        dataBits: parseInt(q('dataBits').value, 10) || 8,
        stopBits: parseInt(q('stopBits').value, 10) || 1,
        parity: q('parity').value,
        flowControl: q('flow').value
      };
    }
    function refreshPorts() {
      if (!HAS || !navigator.serial.getPorts) return;
      Promise.resolve(navigator.serial.getPorts()).then(function (list) {
        var dl = document.getElementById(portListId);
        if (!dl) return;
        var opts = ['<option value="serial:1">连接时由系统弹窗选择</option>'];
        list.forEach(function (p, i) {
          var info = (p.getInfo && p.getInfo()) || {};
          var tag = (info.usbVendorId != null)
            ? ' · VID 0x' + info.usbVendorId.toString(16).padStart(4, '0') : '';
          opts.push('<option value="serial:' + (i + 1) + '">已授权串口 #' + (i + 1) + tag + '</option>');
        });
        dl.innerHTML = opts.join('');
      }).catch(function () { });
    }
    function resolvePort() {
      var v = (q('port').value || '').trim();
      if (!v || v === 'serial:1') return navigator.serial.requestPort();
      var m = v.match(/^serial:(\d+)$/);
      if (m) {
        var idx = parseInt(m[1], 10) - 1;
        return Promise.resolve(navigator.serial.getPorts()).then(function (list) {
          if (!list[idx]) throw new Error('未找到已授权串口 #' + m[1] + '，请选择 serial:1 后重新连接');
          return list[idx];
        });
      }
      return navigator.serial.requestPort();
    }
    async function connect() {
      if (!HAS) {
        setState('err', '不支持');
        sys('当前浏览器不支持 Web Serial：请用 Chrome / Edge，并以 file://、https 或 localhost 打开本页。');
        return;
      }
      try {
        setState('busy', '正在打开串口…');
        port = await resolvePort();
        await port.open(openOpts());
        keepReading = true;
        writer = port.writable.getWriter();
        lock(true);
        setState('on', '已连接 · ' + (q('baud').value || 115200) + 'bps');
        sys('本机串口已打开 · ' + (q('baud').value || 115200) + ' ' +
          q('dataBits').value + q('parity').value.charAt(0).toUpperCase() + q('stopBits').value);
        readLoop();
        refreshPorts();
      } catch (e) {
        port = null;
        setState('err', '打开失败');
        sys('打开串口失败：' + (e && e.message ? e.message : e));
      }
    }
    async function readLoop() {
      while (port && port.readable && keepReading && !closed) {
        reader = port.readable.getReader();
        try {
          while (true) {
            var r = await reader.read();
            if (r.done) break;
            if (r.value && r.value.length) writeBytes(r.value);
          }
        } catch (e) {
          if (keepReading && !closed) sys('\n读取中断：' + (e && e.message ? e.message : e));
        } finally {
          try { reader.releaseLock(); } catch (e) { }
          reader = null;
        }
      }
    }
    async function disconnect(silent) {
      keepReading = false;
      try { if (reader) await reader.cancel(); } catch (e) { }
      try { if (writer) writer.releaseLock(); } catch (e) { }
      writer = null;
      try { if (port && port.readable) await port.close(); } catch (e) { }
      port = null;
      if (closed) return;
      lock(false);
      setState('', '未连接');
      if (!silent) sys('\n串口已断开。');
      refreshPorts();
    }
    async function send() {
      if (!port || !writer) return;
      var t = input.value, eol = q('eol').value;
      var tail = eol === 'crlf' ? '\r\n' : eol === 'lf' ? '\n' : eol === 'cr' ? '\r' : '';
      try {
        await writer.write(enc(t + tail));
        if (q('echo').checked) write('▸ ' + t + '\n', 'tx');
        if (t.trim() && history[0] !== t) { history.unshift(t); if (history.length > 60) history.pop(); }
        hIdx = -1;
        input.value = '';
      } catch (e) {
        sys('\n发送失败：' + (e && e.message ? e.message : e));
      }
    }

    el.addEventListener('click', function (e) {
      var a = e.target.getAttribute && e.target.getAttribute('data-a');
      if (a === 'connect') connect();
      else if (a === 'disconnect') disconnect(false);
      else if (a === 'clear') cons.innerHTML = '';
      else if (a === 'send') send();
      else if (a === 'scan') refreshPorts();
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); send(); return; }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (history.length && hIdx < history.length - 1) { hIdx++; this.value = history[hIdx]; }
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (hIdx > 0) { hIdx--; this.value = history[hIdx]; }
        else { hIdx = -1; this.value = ''; }
      }
    });
    if (HAS && navigator.serial.addEventListener) {
      navigator.serial.addEventListener('disconnect', function (e) {
        if (e.target === port) {
          sys('\n设备已被拔出，连接中断。');
          disconnect(true);
        }
      });
    }

    return {
      el: el, kind: 'serial',
      title: cfg.title || '本机串口',
      mount: function () {
        if (cfg.port) q('port').value = cfg.port;
        q('baud').value = cfg.baud || 115200;
        if (cfg.dataBits) q('dataBits').value = String(cfg.dataBits);
        if (cfg.stopBits) q('stopBits').value = String(cfg.stopBits);
        if (cfg.parity) q('parity').value = cfg.parity;
        if (!HAS) {
          setState('err', '不支持');
          sys('当前浏览器不支持 Web Serial（Firefox / Safari 未实现）：请用 Chrome / Edge 打开。');
          q('connect').disabled = true;
          return;
        }
        sys('提示：本机 USB 直连，数据不经过任何网络服务。首次连接请选 serial:1，由系统弹窗授权端口。');
        refreshPorts();
        if (cfg.autoconnect) connect();
      },
      show: function () { if (!input.disabled) input.focus(); else q('connect').focus(); },
      hide: function () { },
      refit: function () { },
      close: function () {
        closed = true;
        disconnect(true);
      }
    };
  }

  /* ==========================================================
     视图：远程桌面（noVNC，直连设备，不经桥接服务）
     ========================================================== */
  function VncView(cfg) {
    var el = document.createElement('div');
    el.className = 'view vncview';
    var host = cfg.host || '';
    var port = cfg.port || DEF_VNC_PORT;
    var url = 'http://' + host + ':' + port + '/vnc.html?autoconnect=1&resize=scale&reconnect=1';

    el.innerHTML = [
      '<div class="tb">',
      '  <span class="mono" style="font-size:12px;color:#64748b" data-a="url"></span>',
      '  <span class="flex"></span>',
      '  <button class="tbbtn" data-a="reload">重载</button>',
      '  <button class="tbbtn" data-a="open">在新窗口打开</button>',
      '</div>',
      '<iframe class="vnc-frame" data-a="frame" allow="clipboard-read; clipboard-write"></iframe>'
    ].join('');
    el.querySelector('[data-a="url"]').textContent = url;
    var frame = el.querySelector('[data-a="frame"]');
    frame.src = url;

    el.addEventListener('click', function (e) {
      var a = e.target.getAttribute && e.target.getAttribute('data-a');
      if (a === 'reload') frame.src = url;
      else if (a === 'open') window.open(url, '_blank', 'noopener');
    });

    return {
      el: el, kind: 'vnc',
      title: cfg.title || ('桌面 · ' + host + ':' + port),
      mount: function () { },
      show: function () { },
      hide: function () { },
      refit: function () { },
      close: function () { }
    };
  }

  /* ==========================================================
     标签 / 分屏
     ========================================================== */
  function makeView(kind, cfg, conn) {
    if (kind === 'term') return TermView(cfg, conn);
    if (kind === 'sftp') return SftpView(cfg, conn);
    if (kind === 'serial') return LocalSerialView(cfg);
    if (kind === 'vnc') return VncView(cfg);
    throw new Error('未知视图类型：' + kind);
  }

  function openTab(kind, cfg, conn, paneId) {
    cfg = cfg || {};
    paneId = paneId || S.activePane;
    if (paneId === 'R' && !S.split) { S.split = true; applySplit(); }
    var id = 'tab' + (++S.seq);
    var view = makeView(kind, cfg, conn);
    var tab = {
      id: id, kind: kind, title: cfg.title || view.title,
      cfg: cfg, conn: conn, view: view, sessionId: cfg.sessionId || null
    };
    view.el.classList.add('on');
    $('views' + paneId).appendChild(view.el);
    S.panes[paneId].tabs.push(tab);
    S.panes[paneId].active = id;
    S.activePane = paneId;
    try { view.mount(); } catch (e) { console.error(e); }
    renderPane(paneId);
    renderSide();
    setStatus('已打开 ' + KIND_NAME[kind] + ' · ' + tab.title, 'on');
    return tab;
  }

  function renderPane(paneId) {
    var p = S.panes[paneId], bar = $('tabbar' + paneId);
    bar.innerHTML = '';
    if (!p.tabs.length) {
      var ph = document.createElement('div');
      ph.className = 'tab empty';
      ph.textContent = paneId === 'L' ? '还没有标签，从左侧会话列表双击或点「＋ 新建会话」' : '右侧分屏为空';
      bar.appendChild(ph);
    }
    p.tabs.forEach(function (t) {
      var el = document.createElement('div');
      el.className = 'tab' + (p.active === t.id ? ' active' : '');
      el.innerHTML = '<span class="tico"></span><span class="tname"></span><span class="tx" title="关闭">✕</span>';
      el.querySelector('.tico').textContent = ICON[t.kind] || '•';
      el.querySelector('.tname').textContent = t.title;
      el.addEventListener('click', function (e) {
        if (e.target.classList.contains('tx')) { e.stopPropagation(); closeTab(t.id); return; }
        activate(t.id);
      });
      el.addEventListener('dblclick', function () { renameTab(t.id); });
      el.addEventListener('contextmenu', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var pid = paneOf(t.id);
        var items = [
          { label: '重命名', fn: function () { renameTab(t.id); } },
          { label: '弹出为独立窗口', fn: function () { popOut(t); } },
          { label: pid === 'L' ? '移到右侧分屏' : '移到左侧', fn: function () { moveTab(t.id); } },
          { sep: true },
          { label: '关闭', fn: function () { closeTab(t.id); } },
          { label: '关闭其它', fn: function () { closeOthers(t.id); } }
        ];
        showMenu(e.clientX, e.clientY, items);
      });
      bar.appendChild(el);
    });
    var t = p.tabs.filter(function (x) { return x.id === p.active; })[0];
    p.tabs.forEach(function (x) { x.view.el.classList.toggle('on', !!t && x.id === t.id); });
  }

  function activate(id) {
    var paneId = paneOf(id);
    if (!paneId) return;
    S.panes[paneId].active = id;
    S.activePane = paneId;
    renderPane(paneId);
    renderSide();
    var t = findTab(id);
    if (t && t.view.show) { try { t.view.show(); } catch (e) { } }
    if (t && t.view.refit) setTimeout(t.view.refit, 30);
  }

  function closeTab(id) {
    var paneId = paneOf(id);
    if (!paneId) return;
    var p = S.panes[paneId];
    var idx = p.tabs.findIndex(function (x) { return x.id === id; });
    if (idx < 0) return;
    var t = p.tabs[idx];
    try { if (t.view.close) t.view.close(); } catch (e) { }
    try { t.view.el.remove(); } catch (e) { }
    p.tabs.splice(idx, 1);
    if (p.active === id) p.active = p.tabs.length ? p.tabs[Math.max(0, idx - 1)].id : null;
    renderPane(paneId);
    renderSide();
    var nt = p.active && findTab(p.active);
    if (nt && nt.view.refit) setTimeout(nt.view.refit, 30);
    if (!allTabs().length) setStatus('没有打开的标签', '');
  }

  function closeOthers(keepId) {
    var paneId = paneOf(keepId);
    if (!paneId) return;
    S.panes[paneId].tabs.slice().forEach(function (t) {
      if (t.id !== keepId) closeTab(t.id);
    });
  }

  function renameTab(id) {
    var t = findTab(id);
    if (!t) return;
    var name = prompt('标签名称：', t.title);
    if (name == null) return;
    t.title = name.trim() || t.title;
    renderPane(paneOf(id));
    renderSide();
  }

  function moveTab(id) {
    var from = paneOf(id), to = from === 'L' ? 'R' : 'L';
    if (!from) return;
    if (to === 'R' && !S.split) { S.split = true; applySplit(); }
    var t = findTab(id);
    var fp = S.panes[from];
    fp.tabs.splice(fp.tabs.findIndex(function (x) { return x.id === id; }), 1);
    if (fp.active === id) fp.active = fp.tabs.length ? fp.tabs[0].id : null;
    $('views' + to).appendChild(t.view.el);
    S.panes[to].tabs.push(t);
    S.panes[to].active = id;
    renderPane(from);
    renderPane(to);
    renderSide();
    setTimeout(function () { if (t.view.refit) t.view.refit(); }, 30);
  }

  function applySplit() {
    $('split').classList.toggle('two', S.split);
    $('paneR').hidden = !S.split;
    $('btnSplit').classList.toggle('on', S.split);
    $('btnSplit').textContent = S.split ? '取消分屏' : '分屏';
    setTimeout(function () {
      allTabs().forEach(function (t) { if (t.view.refit) t.view.refit(); });
    }, 60);
  }

  function popOut(tab) {
    var payload = {
      kind: tab.kind, title: tab.title, cfg: tab.cfg,
      conn: tab.conn ? {
        key: tab.conn.key, base: tab.conn.base, wsBase: tab.conn.wsBase, token: tab.conn.token,
        user: tab.conn.user, sshHost: tab.conn.sshHost, sshPort: tab.conn.sshPort,
        homedir: tab.conn.homedir, addr: tab.conn.addr, sessionId: tab.conn.sessionId
      } : null
    };
    var url = location.href.split('#')[0] + '?popout=1#pop=' + b64url(JSON.stringify(payload));
    window.open(url, '_blank', 'width=1080,height=720');
  }

  /* ==========================================================
     打开会话
     ========================================================== */
  function touchSession(sess) {
    sess.at = Date.now() / 1000;
    upsertSession(sess);
    renderSide();
  }

  function openSession(sess, paneId) {
    if (!sess) return;
    // 本机串口直连：不走网络，无需 IP / 登录
    if (sess.kind === 'serial') {
      if (!sess.name) sess.name = '本机串口 @' + (sess.baud || 115200);
      openTab('serial', {
        port: sess.serialPort, baud: sess.baud,
        dataBits: sess.dataBits, stopBits: sess.stopBits, parity: sess.parity,
        autoconnect: !!sess.remember,
        title: sessTitle(sess), sessionId: sess.id
      }, null, paneId);
      touchSession(sess);
      return;
    }
    if (sess.kind === 'vnc') {
      if (!sess.addr) { openModal(sess, '请补充设备地址（IP）'); return; }
      if (!sess.name) sess.name = sess.addr;
      openTab('vnc', {
        host: sess.addr, port: sess.vncPort || DEF_VNC_PORT,
        title: sessTitle(sess), sessionId: sess.id
      }, null, paneId);
      touchSession(sess);
      return;
    }
    if (!sess.addr || !sess.user || !sess.password) {
      openModal(sess, sess.password ? '请补充连接信息' : '请输入密码后连接（未记住密码）');
      return;
    }
    var conn = S.conns[bridgeKey(sess)];
    if (conn && conn.token) { startTab(sess, conn, paneId); return; }

    setStatus('正在连接 ' + sessTitle(sess) + ' …', 'busy');
    login(sess).then(function (c) {
      savePrefs(sess);
      startTab(sess, c, paneId);
    }).catch(function (e) {
      setStatus('连接失败：' + e.message, 'err');
      toast('连接 ' + sessTitle(sess) + ' 失败：' + e.message, 'bad');
      openModal(sess, e.message);
    });
  }

  function startTab(sess, conn, paneId) {
    // 连接成功后若未自定义会话名称，默认用 用户名@IP
    if (!sess.name) sess.name = (conn.user ? conn.user + '@' : '') + (conn.addr || sess.addr || '?');
    var cfg = { title: sessTitle(sess), sessionId: sess.id };
    if (sess.kind === 'term') cfg.startDir = sess.startDir || '';
    if (sess.kind === 'sftp') cfg.startDir = sess.startDir || conn.homedir || '/';
    openTab(sess.kind, cfg, conn, paneId);
    touchSession(sess);
    if (conn) {
      setUserLabel(conn.user + '@' + conn.addr);
      setDeviceLabel('桥接：' + conn.base + ' · ' + sessTitle(sess));
      loadSysInfo(conn);
    }
  }

  /* ---------------------------------------------------------- 侧栏：会话列表 */
  function renderSide() {
    var box = $('sideList');
    box.innerHTML = '';
    if (!S.sessions.length) {
      box.innerHTML = '<div class="side-empty">还没有会话。<br>' +
        '点「＋ 新建」填写设备 IP 与端口，连接成功后会自动保存在这里。</div>';
      return;
    }
    var openIds = {};
    allTabs().forEach(function (t) { if (t.sessionId) openIds[t.sessionId] = true; });

    KINDS.forEach(function (k) {
      var list = S.sessions.filter(function (s) { return s.kind === k; })
        .sort(function (a, b) { return (b.at || 0) - (a.at || 0); });
      if (!list.length) return;

      var g = document.createElement('div');
      g.className = 'side-group';
      g.innerHTML = '<span class="sg-ico"></span><span class="sg-name"></span>';
      g.querySelector('.sg-ico').textContent = ICON[k];
      g.querySelector('.sg-name').textContent = KIND_NAME[k];
      box.appendChild(g);

      list.forEach(function (s) {
        var el = document.createElement('div');
        el.className = 'side-item' + (openIds[s.id] ? ' on' : '');
        el.innerHTML = '<span class="si-ico"></span><span class="si-txt">' +
          '<span class="si-name"></span><span class="si-sub"></span></span>';
        el.querySelector('.si-ico').textContent = ICON[s.kind];
        el.querySelector('.si-name').textContent = sessTitle(s);
        el.querySelector('.si-sub').textContent = sessSub(s);
        el.title = sessTitle(s) + '\n' + sessSub(s);
        el.addEventListener('click', function () { openSession(s); });
        el.addEventListener('dblclick', function () { openSession(s, 'R'); });
        el.addEventListener('contextmenu', function (e) {
          e.preventDefault();
          e.stopPropagation();
          showMenu(e.clientX, e.clientY, [
            { label: '打开', fn: function () { openSession(s); } },
            { label: '在右侧分屏打开', fn: function () { openSession(s, 'R'); } },
            { sep: true },
            { label: '编辑', fn: function () { openModal(s); } },
            { label: '复制一份', fn: function () {
              var c = clone(s);
              c.id = newId();
              c.name = (s.name || sessTitle(s)) + ' 副本';
              c.at = Date.now() / 1000;
              upsertSession(c);
              renderSide();
            } },
            { sep: true },
            { label: '删除', danger: true, fn: function () {
              if (!confirm('删除会话「' + sessTitle(s) + '」？')) return;
              removeSession(s.id);
              renderSide();
            } }
          ]);
        });
        box.appendChild(el);
      });
    });
  }

  /* ==========================================================
     会话编辑弹窗
     ========================================================== */
  var draft = null;        // 正在编辑的会话草稿
  var editing = false;     // true = 编辑已有会话

  function defaultDraft(kind) {
    var s = blankSession(kind);
    var p = S.prefs || {};
    if (S.sameOrigin) { s.addr = S.sameOrigin.addr; s.bridgePort = S.sameOrigin.port; }
    else if (p.addr) { s.addr = p.addr; s.bridgePort = p.bridgePort || DEF_BRIDGE_PORT; }
    if (p.user) s.user = p.user;
    return s;
  }

  function openModal(sess, errMsg) {
    if (sess && typeof sess === 'object' && sess.id) {
      editing = true;
      draft = clone(sess);
      if (!draft.password && !draft.remember) draft.remember = true;
    } else {
      editing = false;
      draft = defaultDraft(typeof sess === 'string' ? sess : 'term');
      if (typeof sess === 'string') draft.kind = sess;
    }
    if (typeof sess === 'string' && !editing) draft.kind = sess;
    $('mTitle').textContent = editing ? '编辑会话' : '新建会话';
    $('mOk').textContent = editing ? '保存并连接' : '连接';
    $('mErr').textContent = typeof errMsg === 'string' ? errMsg : '';
    syncTypeCards();
    $('modalNew').hidden = false;
    renderModalBody();
    setTimeout(function () {
      var first = $('mBody').querySelector('[data-m="addr"]') || $('mBody').querySelector('input');
      if (first) first.focus();
    }, 30);
  }
  function closeModal() { $('modalNew').hidden = true; }
  function syncTypeCards() {
    Array.prototype.forEach.call($('mTypes').children, function (b) {
      b.classList.toggle('on', b.dataset.kind === draft.kind);
    });
  }

  function baudOptions(cur) {
    var c = String(cur == null || cur === '' ? 115200 : cur);
    var html = '';
    var found = BAUD_LIST.some(function (b) { return String(b) === c; });
    if (!found && !isNaN(parseInt(c, 10)) && String(parseInt(c, 10)) === c) {
      html += '<option value="' + esc(c) + '" selected>' + esc(c) + '（已保存）</option>';
    }
    html += BAUD_LIST.map(function (b) {
      return '<option value="' + b + '"' + (String(b) === c ? ' selected' : '') + '>' + b + '</option>';
    }).join('');
    return html;
  }

  function renderModalBody() {
    var body = $('mBody');
    var k = draft.kind;
    var html = '';

    if (k === 'term' || k === 'sftp') {
      html += '<div class="fgrid">' +
        '<div class="gf"><label>设备地址（IP）</label>' +
        '<input data-m="addr" value="' + esc(draft.addr) + '" placeholder="192.168.1.100" spellcheck="false" autocomplete="off"></div>' +
        '<div class="gf narrow"><label>SSH 端口</label>' +
        '<input data-m="sshPort" value="' + esc(draft.sshPort || DEF_SSH_PORT) + '" inputmode="numeric" placeholder="22"></div>' +
        '</div>' +
        '<div class="fgrid">' +
        '<div class="gf"><label>用户名</label>' +
        '<input data-m="user" value="' + esc(draft.user) + '" placeholder="iflytek" spellcheck="false" autocomplete="username"></div>' +
        '<div class="gf"><label>密码</label>' +
        '<input data-m="password" type="password" value="' + esc(draft.password) + '" autocomplete="current-password"></div>' +
        '</div>' +
        '<div class="fgrid one">' +
        '<div class="gf"><label>起始目录</label>' +
        '<input data-m="startDir" value="' + esc(draft.startDir) + '" placeholder="留空 = 登录后进入家目录" spellcheck="false"></div>' +
        '</div>' +
        '<label class="chk"><input type="checkbox" data-m="remember"' + (draft.remember ? ' checked' : '') +
        '> 记住密码（保存在本机浏览器，换电脑需重新输入）</label>' +
        '<details class="fadv"><summary>高级：桥接服务端口</summary>' +
        '<div class="fgrid one">' +
        '<div class="gf narrow"><label>桥接服务端口</label>' +
        '<input data-m="bridgePort" value="' + esc(draft.bridgePort || DEF_BRIDGE_PORT) + '" inputmode="numeric" placeholder="8100"></div>' +
        '</div></details>' +
        '<div class="fnote">浏览器先连设备上的桥接服务 <code>device_bridge.py</code>（默认端口 8100，一般不用改），' +
        '再由它登录设备自己的 sshd（上面的 SSH 端口，默认 22）。</div>';
    } else if (k === 'serial') {
      html += '<div class="fgrid">' +
        '<div class="gf"><label>串口设备</label>' +
        '<select data-m="serialPort" id="mPortSel"><option value="">— 点「选择新串口…」选择 —</option></select></div>' +
        '<div class="gf"><label>波特率</label>' +
        '<input data-m="baud" list="mBaudList" inputmode="numeric" value="' + esc(draft.baud || 115200) +
        '" placeholder="115200" spellcheck="false" autocomplete="off">' +
        '<datalist id="mBaudList">' + baudOptions(draft.baud || 115200) + '</datalist></div>' +
        '</div>';
      html += '<div class="frow">' +
        '<button class="btn sm" id="mPickPort" type="button">选择新串口…</button>' +
        '<button class="btn sm" id="mScanPorts" type="button">刷新串口列表</button>' +
        '<span class="fhint" id="mPortHint">首次使用点「选择新串口…」由系统弹窗授权，之后即可在下拉中选择；' +
        '波特率点击输入框清空后可下拉选全部档位，也可直接输入任意数值。</span>' +
        '</div>';
      html += '<label class="chk"><input type="checkbox" data-m="remember"' + (draft.remember ? ' checked' : '') +
        '> 自动连接：打开会话时直接选择上次的系统串口，不再弹窗</label>';
      html += '<div class="fnote">数据线插在<b>本机</b>：浏览器直接读写（Web Serial），仅限 Chrome / Edge；' +
        '<b>不需要</b>设备 IP、端口与账号密码。</div>';
      html += '<details class="fadv"><summary>高级：串口参数</summary>' +
        '<div class="fgrid three">' +
        '<div class="gf narrow"><label>数据位</label><select data-m="dataBits">' +
        '<option' + (String(draft.dataBits) === '8' ? ' selected' : '') + '>8</option>' +
        '<option' + (String(draft.dataBits) === '7' ? ' selected' : '') + '>7</option></select></div>' +
        '<div class="gf narrow"><label>停止位</label><select data-m="stopBits">' +
        '<option' + (String(draft.stopBits) === '1' ? ' selected' : '') + '>1</option>' +
        '<option' + (String(draft.stopBits) === '2' ? ' selected' : '') + '>2</option></select></div>' +
        '<div class="gf narrow"><label>校验</label><select data-m="parity">' +
        '<option value="none"' + (draft.parity === 'none' ? ' selected' : '') + '>无</option>' +
        '<option value="even"' + (draft.parity === 'even' ? ' selected' : '') + '>偶</option>' +
        '<option value="odd"' + (draft.parity === 'odd' ? ' selected' : '') + '>奇</option></select></div>' +
        '</div></details>';
    } else {
      html += '<div class="fgrid one">' +
        '<div class="gf narrow"><label>noVNC 端口</label>' +
        '<input data-m="vncPort" value="' + esc(draft.vncPort || DEF_VNC_PORT) + '" inputmode="numeric" placeholder="6080"></div>' +
        '</div>' +
        '<div class="fgrid one">' +
        '<div class="gf"><label>设备地址（IP）</label>' +
        '<input data-m="addr" value="' + esc(draft.addr) + '" placeholder="192.168.1.100" spellcheck="false" autocomplete="off"></div>' +
        '</div>' +
        '<div class="fnote">远程桌面走设备上已有的 VNC 服务：websockify 把 VNC 的 5900 转成 WebSocket，' +
        '再由 noVNC 网页渲染。它不经过桥接服务，因此不需要账号密码。</div>';
    }
    body.innerHTML = html;
    if (k === 'serial') {
      refreshPortSelect();
      var baudEl = body.querySelector('[data-m="baud"]');
      if (baudEl) {
        // Chrome 的 datalist 会按输入框当前值过滤；聚焦先清空以便展示全部档位
        baudEl.addEventListener('focus', function () {
          this.setAttribute('data-saved', this.value);
          this.value = '';
        });
        baudEl.addEventListener('blur', function () {
          if (!this.value) this.value = this.getAttribute('data-saved') || '115200';
        });
      }
    }
  }

  function readModal() {
    Array.prototype.forEach.call($('mBody').querySelectorAll('[data-m]'), function (el) {
      var k = el.dataset.m;
      draft[k] = el.type === 'checkbox' ? el.checked : el.value.trim();
      if (k === 'serialPort') draft[k] = el.value; // 串口值原样保存，不做 trim 之外处理
    });
    return draft;
  }

  function modalErr(msg) { $('mErr').textContent = msg; return false; }

  function confirmModal() {
    var v = readModal();
    $('mErr').textContent = '';

    if (v.kind === 'serial') {
      var baudRaw = String(v.baud || '').trim();
      if (baudRaw && !/^\d+$/.test(baudRaw)) return modalErr('波特率只能填数字（如 115200）');
      v.baud = parseInt(baudRaw, 10) || 115200;
      v.addr = ''; v.user = ''; v.password = '';
      if (!v.serialPort && !v.remember) return modalErr('请从下拉中选择串口（首次请点「选择新串口…」由系统弹窗授权）');
      // 保存可读的串口显示名（芯片型号 / VID PID），侧栏与之后编辑都用它展示
      var psel = $('mPortSel');
      if (psel && psel.value && psel.selectedIndex >= 0) {
        v.serialLabel = psel.options[psel.selectedIndex].text;
      } else if (!v.serialLabel) {
        v.serialLabel = v.serialPort;
      }
    } else if (v.kind === 'vnc') {
      if (!v.addr) return modalErr('请填写设备地址（IP）');
      v.vncPort = parseInt(v.vncPort, 10) || DEF_VNC_PORT;
      v.password = ''; v.user = '';
    } else {
      if (!v.addr) return modalErr('请填写设备地址（IP）');
      if (!v.user) return modalErr('请填写用户名');
      if (!v.password) return modalErr('请填写密码');
      v.bridgePort = parseInt(v.bridgePort, 10) || DEF_BRIDGE_PORT;
      v.sshPort = parseInt(v.sshPort, 10) || DEF_SSH_PORT;
    }

    var rec;
    if (editing) {
      rec = findSession(draft.id) || blankSession(v.kind);
      KINDS.forEach(function (k) { if (k !== v.kind && k in v) delete v[k]; });
      Object.keys(v).forEach(function (k) { rec[k] = v[k]; });
      rec.kind = v.kind;
    } else {
      rec = v;
      rec.id = rec.id || newId();
    }
    rec.at = Date.now() / 1000;
    upsertSession(rec);
    if (rec.kind !== 'vnc') savePrefs(rec);
    renderSide();
    closeModal();
    openSession(rec);
  }

  // 串口下拉：把已授权串口 + 已保存的选择合并进 #mPortSel
  var mPortErr = {
    nosupport: '当前浏览器不支持 Web Serial，请用 Chrome / Edge。'
  };
  // 浏览器不暴露 COM 口编号（如 COM9），只能拿到 USB VID/PID；按常见芯片给出可读名
  var USB_CHIPS = [
    { v: 0x1a86, p: 0x7523, n: 'CH340' },
    { v: 0x1a86, p: 0x5523, n: 'CH341' },
    { v: 0x10c4, p: 0xea60, n: 'CP2102' },
    { v: 0x0403, p: 0x6001, n: 'FT232' },
    { v: 0x0403, p: 0x6015, n: 'FT231X' },
    { v: 0x0483, p: 0x5740, n: 'STM32 VCP' },
    { v: 0x2e8a, p: 0x000a, n: 'RP2040' },
    { v: 0x2341, n: 'Arduino' },
    { v: 0x303a, n: 'ESP32' }
  ];
  function usbChipName(info) {
    if (info.usbVendorId == null) return '';
    for (var i = 0; i < USB_CHIPS.length; i++) {
      var c = USB_CHIPS[i];
      if (info.usbVendorId === c.v && (c.p == null || info.usbProductId === c.p)) return c.n;
    }
    return '';
  }
  function portLabelText(p, i) {
    var info = (p && p.getInfo && p.getInfo()) || {};
    var chip = usbChipName(info);
    var txt = '串口 serial:' + (i + 1);
    if (chip) txt += ' · ' + chip;
    if (info.usbVendorId != null) {
      txt += ' (VID 0x' + info.usbVendorId.toString(16).padStart(4, '0') +
        ' PID 0x' + (info.usbProductId != null ? info.usbProductId.toString(16).padStart(4, '0') : '----') + ')';
    }
    return txt;
  }
  function portOptionHtml(p, i) {
    return '<option value="serial:' + (i + 1) + '">' + esc(portLabelText(p, i)) + '</option>';
  }
  function ensureCurrentOption(sel) {
    var cur = sel.value || '';
    if (!cur) return;
    var has = false;
    Array.prototype.forEach.call(sel.options, function (o) { if (o.value === cur) has = true; });
    if (!has) {
      var text = (draft && draft.serialLabel && draft.serialPort === cur)
        ? draft.serialLabel
        : cur + '（已保存）';
      sel.insertAdjacentHTML('beforeend',
        '<option value="' + esc(cur) + '">' + esc(text) + '</option>');
      sel.value = cur;
    }
  }
  function renderPortOptions(list) {
    var sel = $('mPortSel');
    if (!sel) return;
    sel.innerHTML = '<option value="">— 点「选择新串口…」选择 —</option>' +
      list.map(portOptionHtml).join('');
    if (draft && draft.serialPort) sel.value = draft.serialPort;
    ensureCurrentOption(sel);
    draft.serialPort = sel.value;
    if (sel.selectedIndex >= 0) draft.serialLabel = sel.options[sel.selectedIndex].text;
  }
  // 刷新浏览器已授权的串口列表（不弹系统选择框）
  function refreshPortSelect() {
    var hint = $('mPortHint');
    if (!hint) return;
    if (!('serial' in navigator)) {
      hint.className = 'fhint bad';
      hint.textContent = mPortErr.nosupport;
      renderPortOptions([]);
      return;
    }
    hint.className = 'fhint';
    hint.textContent = '正在扫描…';
    Promise.resolve(navigator.serial.getPorts ? navigator.serial.getPorts() : []).then(function (list) {
      renderPortOptions(list);
      hint.className = list.length ? 'fhint ok' : 'fhint';
      hint.textContent = list.length
        ? '找到 ' + list.length + ' 个已授权串口，可从下拉中选择。'
        : '暂无已授权串口，点「选择新串口…」由系统弹窗授权后即可下拉选择。';
    }).catch(function (e) {
      hint.className = 'fhint bad';
      hint.textContent = '扫描失败：' + (e && e.message ? e.message : e);
    });
  }

  // 本机 Web Serial：弹出系统端口选择框，授权并选进下拉
  function pickLocalPort() {
    var hint = $('mPortHint');
    if (!hint) return;
    if (!('serial' in navigator) || !navigator.serial.requestPort) {
      hint.className = 'fhint bad';
      hint.textContent = mPortErr.nosupport;
      return;
    }
    var p;
    try { p = navigator.serial.requestPort(); } catch (e) {
      hint.className = 'fhint bad';
      hint.textContent = '无法弹出端口选择框：' + (e && e.message ? e.message : e);
      return;
    }
    p.then(function () {
      return Promise.resolve(navigator.serial.getPorts ? navigator.serial.getPorts() : []);
    }).then(function (list) {
      // 被授权的端口一定排在 getPorts() 结果里，取最后一个当作刚选中的
      var idx = list.length - 1;
      renderPortOptions(list);
      var val = 'serial:' + (idx + 1);
      var sel = $('mPortSel');
      if (sel) sel.value = val;
      if (draft) { draft.serialPort = val; draft.serialLabel = sel && sel.selectedIndex >= 0
        ? sel.options[sel.selectedIndex].text : val; }
      var labelText = (sel && sel.selectedIndex >= 0) ? sel.options[sel.selectedIndex].text : val;
      hint.className = 'fhint ok';
      hint.textContent = '已授权并选中 [' + labelText + ']，直接点「连接」即可。';
    }).catch(function (e) {
      if (e && (e.name === 'NotFoundError' || e.name === 'AbortError')) {
        hint.className = 'fhint';
        hint.textContent = '未选择端口。可再次点击「选择新串口…」重试。';
      } else {
        hint.className = 'fhint bad';
        hint.textContent = '选择失败：' + (e && e.message ? e.message : e);
      }
    });
  }

  $('mTypes').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-kind]');
    if (!b) return;
    readModal();
    draft.kind = b.dataset.kind;
    syncTypeCards();
    $('mErr').textContent = '';
    renderModalBody();
  });
  $('mClose').addEventListener('click', closeModal);
  $('mCancel').addEventListener('click', closeModal);
  $('mOk').addEventListener('click', confirmModal);
  $('modalNew').addEventListener('click', function (e) { if (e.target === this) closeModal(); });
  $('mBody').addEventListener('click', function (e) {
    if (e.target && e.target.id === 'mScanPorts') {
      e.preventDefault(); refreshPortSelect();
    }
    if (e.target && e.target.id === 'mPickPort') {
      e.preventDefault(); pickLocalPort();
    }
  });
  $('modalNew').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target && e.target.tagName === 'INPUT') { e.preventDefault(); confirmModal(); }
    if (e.key === 'Escape') closeModal();
  });

  /* ==========================================================
     断开全部
     ========================================================== */
  function disconnectAll() {
    var keys = Object.keys(S.conns);
    if (!keys.length && !allTabs().length) { toast('当前没有活动连接。'); return; }
    if (!confirm('断开全部连接？设备端会关闭这些 SSH 连接，打开着的本机串口也会一并关闭。')) return;
    keys.forEach(function (k) {
      var c = S.conns[k];
      fetch(c.base + '/api/logout?token=' + encodeURIComponent(c.token)).catch(function () { });
    });
    S.conns = {};
    allTabs().forEach(function (t) { try { t.view.close(); } catch (e) { } });
    S.panes.L.tabs = []; S.panes.L.active = null;
    S.panes.R.tabs = []; S.panes.R.active = null;
    $('viewsL').innerHTML = ''; $('viewsR').innerHTML = '';
    renderPane('L');
    renderPane('R');
    renderSide();
    $('sideSys').innerHTML = '';
    setUserLabel('未连接');
    setDeviceLabel('');
    setStatus('已断开全部连接', '');
  }

  /* ==========================================================
     初始化
     ========================================================== */
  function detectSameOrigin() {
    if (location.protocol.indexOf('http') !== 0) return Promise.resolve(null);
    return fetch('/api/ping', { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.service === 'eai-device-bridge') {
          return {
            addr: location.hostname,
            port: parseInt(location.port, 10) || 80,
            serial: j.serial_default || ''
          };
        }
        return null;
      })
      .catch(function () { return null; });
  }

  function bootPopout() {
    var m = /[#&]pop=([^&]+)/.exec(location.hash || '');
    if (!m) return false;
    var p;
    try { p = JSON.parse(unb64url(m[1])); } catch (e) { return false; }
    if (p.conn) S.conns[p.conn.key || p.conn.base] = p.conn;
    S.popout = true;
    $('app').hidden = false;
    renderSide();
    renderPane('L');
    renderPane('R');
    var cfg = p.cfg || {};
    cfg.title = p.title || '';
    openTab(p.kind, cfg, p.conn || null);
    if (p.conn) {
      setUserLabel(p.conn.user + '@' + p.conn.addr);
      setDeviceLabel('桥接：' + p.conn.base + ' · ' + (p.title || ''));
      loadSysInfo(p.conn);
    }
    document.title = (p.title || KIND_NAME[p.kind] || '会话') + ' · 设备开发工作台';
    return true;
  }

  function boot() {
    loadSessions();
    S.prefs = lsGet(LS_PREFS, {}) || {};
    if (bootPopout()) return;

    $('app').hidden = false;
    renderSide();
    renderPane('L');
    renderPane('R');
    setStatus('就绪 · 从左侧会话列表打开，或点「＋ 新建会话」', '');
    setDeviceLabel(location.protocol.indexOf('http') === 0 ? '桥接：' + location.origin : '');

    detectSameOrigin().then(function (info) {
      if (info) {
        S.sameOrigin = info;
        setDeviceLabel('桥接：' + location.origin + '（本机托管）');
      }
      if (!S.sessions.length) openModal();
    });
  }

  $('btnNew').addEventListener('click', function () { openModal(); });
  $('btnNewTab').addEventListener('click', function () { openModal(); });
  $('btnSplit').addEventListener('click', function () {
    S.split = !S.split;
    if (!S.split && S.panes.R.tabs.length) {
      S.panes.R.tabs.slice().forEach(function (t) { moveTab(t.id); });
    }
    applySplit();
  });
  $('btnLogout').addEventListener('click', disconnectAll);

  document.addEventListener('keydown', function (e) {
    if (!(e.ctrlKey || e.metaKey) || !e.shiftKey) return;
    var k = e.key.toLowerCase();
    if (k === 't') { e.preventDefault(); openModal(); }
    else if (k === 'w') {
      e.preventDefault();
      var pid = S.activePane, p = S.panes[pid];
      if (p.active) closeTab(p.active);
    } else if (k === 'e') { e.preventDefault(); $('btnSplit').click(); }
  });

  window.addEventListener('resize', function () {
    allTabs().forEach(function (t) { if (t.view.refit) t.view.refit(); });
  });

  boot();
})();
