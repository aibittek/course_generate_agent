---
name: "anim-2d"
description: "Creates lightweight 2D principle animations and SVG animated diagrams (loops, data-flow, state transitions) for course tutorials, stored in the experiment's anim-2d/ directory. Invoke when user wants 2D animated explainers, motion diagrams, or principle schematics in course content."
---

# 2D 动画（anim-2d）

用于"不好理解的原理用动画讲"：激光怎么扫出地图、粒子滤波如何收敛、数据流经过哪些模块等。**轻量、循环、离线可用**。

## 存放位置

遵循 `course-output-layout` skill：默认放当前实验 `training/output/courses/<课程>/exp-<NN>-<短名>/anim-2d/`；跨实验共享才提升到 `shared/anim-2d/` 或 `assets/`。

命名：`anim2d-主题.svg` 或 `anim2d-主题.html`（独立片段页另存 index 引用）。

## 技术选型（按优先级）

| 场景 | 方案 |
|------|------|
| 线条图、路径运动、简单循环 | **纯 SVG + CSS animation**（首选，零依赖，可内嵌 html） |
| 多阶段时序/叙事动画 | SVG + **GSAP timeline**（lib 已在 `assets/lib/`，用 gsap skill 查 API） |
| 复杂逻辑、与交互结合 | 独立 `anim2d-主题.html` 片段（原生 JS + canvas） |
| 数据图表动画 | ECharts（`assets/lib/echarts.min.js`） |

克制原则：科普原理动画一般 **3~10 秒一个循环**，元素 ≤15 个，颜色只用 clean-tech-ui 调色板（蓝 #2563eb / 青 #0891b2 / 绿松 #0d9488 等）。

## 标准 SVG 动画示例（可直接复用骨架）

```html
<figure class="anim2d-block reveal">
  <svg class="anim2d" viewBox="0 0 640 320" role="img"
       aria-label="激光雷达扫描建图原理动画">
    <rect x="0" y="0" width="640" height="320" fill="#f8fafc" rx="10"/>
    <!-- 机器人 -->
    <rect x="300" y="240" width="40" height="24" rx="5" fill="#2563eb"/>
    <!-- 扫描线：以机器人为中心旋转 -->
    <g class="sweep" style="transform-origin:320px 240px">
      <line x1="320" y1="240" x2="320" y2="60" stroke="#0891b2" stroke-width="2" opacity=".8"/>
      <path d="M320 240 L200 80 A190 190 0 0 1 320 60 Z" fill="#0891b2" opacity=".12"/>
    </g>
    <!-- 障碍物轮廓随扫描逐步显现（stroke-dashoffset） -->
    <path class="draw" d="M120 200 L120 120 L200 120" stroke="#0d9488"
          stroke-width="3" fill="none" stroke-dasharray="220" stroke-dashoffset="220"/>
    <text x="16" y="28" font-size="14" fill="#64748b"
          font-family="'Noto Sans CJK SC','WenQuanYi Micro Hei',sans-serif">
      激光雷达扫描建图
    </text>
  </svg>
  <figcaption>动画 1-1｜激光逐束扫描，命中点累积成地图轮廓</figcaption>
</figure>
```

```css
/* 配套样式 —— 放入页面 CSS */
.anim2d-block{margin:28px 0;text-align:center}
.anim2d-block .anim2d{width:100%;max-width:680px;height:auto;
  border:1px solid var(--border);border-radius:14px;
  box-shadow:0 6px 24px rgba(15,23,42,.07)}
.anim2d .sweep{animation:rot 4s linear infinite}
@keyframes rot{to{transform:rotate(360deg)}}
.anim2d .draw{animation:draw 4s ease-in-out infinite}
@keyframes draw{40%,100%{stroke-dashoffset:0}}
@media (prefers-reduced-motion: reduce){.anim2d .sweep,.anim2d .draw{animation:none}}
```

## 图注与编号

- `figcaption` 格式：`动画 N-M｜说明`（与图片"图 N-M"同级体系）。
- 动画上方先用 1~2 句正文点出"它在演示什么"。

## 工程规则

1. **优先 CSS/SMIL 驱动**，不引入框架；需要复杂时序再用 `assets/lib/` 的 GSAP（相对路径引用）。
2. 所有中文文本节点字体显式设置 `"Noto Sans CJK SC","WenQuanYi Micro Hei"`。
3. 必须加 `prefers-reduced-motion` 降级；长列表内部动画必须 `pause when off-screen`（可用 IntersectionObserver 兜底）。
4. 尺寸用 `viewBox` 自适应，禁止固定 px 宽度写死在 svg 上。
5. 单文件动画总量（内嵌进实验页时）保持<40KB；更大做成独立 `anim2d-主题.html`，用 iframe 或新窗链接挂入。
6. 2D **教学操作演示**（步骤点击类）不属于本 skill → 用 `anim-interactive`。