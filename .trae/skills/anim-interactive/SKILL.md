---
name: "anim-interactive"
description: "Builds interactive, user-operable demos and simulations for course pages (parameter sliders, state-machine steppers, particle-filter sandbox, simulators), stored in the experiment's interactive/ directory. Invoke when user asks for interactive animation, playable demo, hands-on widget, or simulated experiment in course content."
---

# 交互动画（anim-interactive）

**"可操作"是与 anim-2d 的分界线**：用户拖参数、点步骤、改输入立刻看到反馈的 demo —— 例：调 A* 代价权重看路径变化、点按钮走状态机、拖粒子滤波粒子数看收敛、模拟抓取占位判断。

## 存放位置

遵循 `course-output-layout` skill：默认放当前实验 `training/output/courses/<课程>/exp-<NN>-<短名>/interactive/`：

```
interactive/
├── ix-astar-weight.html        # 单文件片段（含 id="ix-astar-weight-root"）
├── ix-state-machine.html
└── ix-particle-filter.html
```

命名前缀 `ix-`；跨实验共享才提升到 `shared/interactive/` 或 `assets/`。

## 挂载方式（二选一）

**内嵌（默认，推荐 <30KB 的 demo）：**

```html
<div class="ix-block reveal">
  <div class="ix-frame" id="ix-astar-weight-root"></div>
  <p class="ix-caption">互动 1-1｜拖动滑杆调整代价权重，观察路径如何绕开障碍</p>
</div>
<script src="./interactive/js/ix-astar-weight.js" defer></script>
<!-- 目录结构相应为 interactive/js/ix-*.js，html 模式则用 iframe 或直接摘入页面 -->
```

**iframe 载入完整片段页（复杂 demo、防样式污染）：**

```html
<iframe class="ix-iframe" src="./interactive/ix-astar-weight.html"
        title="A* 代价权重交互演示" loading="lazy"
        style="width:100%;height:460px;border:1px solid var(--border);
               border-radius:14px;background:#fff"></iframe>
```

## 交互设计规范（科普教程语境）

1. **一个 demo 一个知识点**，控件 ≤3 个（滑杆/按钮/下拉），首屏 2 秒内看懂怎么玩。
2. 必须有**内联操作提示**（如"① 拖动滑杆 → ② 观察虚线路径"），放在控件旁，不写在图注里。
3. **实时反馈 <100ms**；重计算（寻路、粒子）放 `requestAnimationFrame` 分片或 Web Worker（>50ms 的计算）。
4. 提供"重置"按钮；有演示值的场景给"自动演示"开关（3 步循环播放）。
5. 图注编号：`互动 N-M｜说明`（与"图/动画 N-M"同级体系）。
6. 触屏可用：滑杆原生 `<input type="range">`，点击目标 ≥40px；`prefers-reduced-motion` 时关闭自动演示。

## 标准骨架（原生 JS + canvas，无框架）

```html
<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--accent:#2563eb;--border:#e2e8f0;--text:#334155}
body{margin:0;font-family:'Noto Sans CJK SC','WenQuanYi Micro Hei',sans-serif;
     background:#fff;color:var(--text)}
.ix-panel{max-width:720px;margin:0 auto;padding:20px}
.ix-ctrl{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:14px;font-size:14px}
.ix-ctrl label{display:flex;gap:8px;align-items:center}
canvas{width:100%;border:1px solid var(--border);border-radius:12px;background:#f8fafc}
</style></head><body>
<div class="ix-panel">
  <div class="ix-ctrl">
    <label>代价权重 <input type="range" id="w" min="1" max="10" step="0.5" value="3"><b id="wv">3.0</b></label>
    <button id="reset">重置</button>
  </div>
  <canvas id="cv" width="720" height="360"></canvas>
</div>
<script>
const root = document.getElementById('ix-astar-weight-root'); // 容器 id 与文件同名
const w = document.getElementById('w'), wv = document.getElementById('wv'),
      cv = document.getElementById('cv'), ctx = cv.getContext('2d');
function draw(){ wv.textContent = (+w.value).toFixed(1); /* 此处画路径随之变化 */ }
w.addEventListener('input', draw);
document.getElementById('reset').onclick = () => { w.value = 3; draw(); };
draw();
</script></body></html>
```

## 复用与隔离

- 同一实验多个 demo 各自独立文件+独立根节点 id（`ix-<slug>-root`），互不共享全局状态。
- 引用共享库按所在页面深度算 `../` 层数（课程多一层分类目录 `core|cases|industry/`）：实验页 `index.html` 是 `../../../../assets/lib/`；实验页内嵌的 iframe（本 demo 自身在 `interactive/` 下）是 `../../../../../assets/lib/`。层数必须实测（浏览器 Network 面板无 404 才算对），禁止凭感觉写。
- 与 2D 原理动画的分工：**单向展示 → anim-2d；可操作 → 本 skill**。
- demo 结果需要"截图留档"到 `images/` 时正常按 `embed-image` 规则放 `fig-` 图，不用循环录成视频。

## 禁止事项

- 不引入 React/Vue 等需要构建的框架（保持纯 html/js，离线双击可开或 `http.server` 可开）。
- 不引 CDN 网络脚本（离线优先）；库放 `assets/lib/`。
- 不把 demo 写成只有开发者懂的裸控件 —— 每个控件必配中文 label 与单位。