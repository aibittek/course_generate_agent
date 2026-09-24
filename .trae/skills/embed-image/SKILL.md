---
name: "embed-image"
description: "Inserts local images, diagrams, icons and screenshots into course HTML with responsive styling, captions and figure numbering, and manages the images/ directory per experiment. Invoke when user asks to insert, place, organize or optimize pictures/photos/diagrams in course content."
---

# 图片插入（embed-image）

## 存放位置（先定位再插入）

遵循 `course-output-layout` skill：

- 全站通用（logo、通用图标）：`training/output/assets/img/`
- 同课程多实验共享：`training/output/courses/<课程>/shared/images/`
- **仅单实验使用（默认）：`training/output/courses/<课程>/exp-<NN>-<短名>/images/`**

命名：

| 类型 | 前缀 | 示例 |
|------|------|------|
| 原理图/流程图/框图 | `fig-` | `fig-slam-pipeline-01.png` |
| 图标 | `icon-` | `icon-lidar.svg` |
| 硬件实物照/截图 | `photo-`/`shot-` | `shot-nav2-rviz-01.png` |
| 封面 | `cover-` | `cover-exp01.png` |

格式：**优先 SVG**（图标、线条图），照片/截图用 PNG/WebP；截图先压缩（WebP 质量 ≥80）。

## 标准插入片段

```html
<figure class="img-block reveal">
  <img src="./images/fig-slam-pipeline-01.svg" alt="SLAM 建图流程图"
       loading="lazy" decoding="async">
  <figcaption>图 1-2｜SLAM 建图数据流：激光雷达 → 里程计 → 地图优化</figcaption>
</figure>
```

要点：

1. **相对路径**（均相对实验页 `index.html` 所在目录）：同实验 `./images/xxx.svg`；课程共享 `../shared/images/...`（shared 与实验目录同级）；全站 `../../../../assets/img/...`（实验页深 4 层，含分类目录）。
2. **必写 `alt`**（无障碍+加载失败可读）；`loading="lazy"` + `decoding="async"`。
3. **figcaption 必填**，编号"图 N-M｜说明"，与正文"如图 N-M 所示"对应。
4. **巨幅图**（>900px 视觉宽）直接 `width:100%` 自适应；需要看细节的截图可加点击放大：
   ```html
   <a href="./images/shot-nav2-rviz-01.png" target="_blank" class="img-zoom">
   ```
5. **行内小图**（与文字同段的 24~40px 图标）用 `<img class="inline-icon">`，不出 figure/编号：
   ```css
   .inline-icon{height:1em;vertical-align:-.15em;margin:0 .2em}
   ```

## 组合图 / 对比图

两图对比（前后、A/B）：

```html
<div class="img-pair"> <!-- .img-pair{display:grid;grid-template-columns:1fr 1fr;gap:16px} -->
  <figure class="img-block">…<figcaption>(a) 未启用滤波</figcaption></figure>
  <figure class="img-block">…<figcaption>(b) 粒子滤波后</figcaption></figure>
</div>
```

## 配套样式（clean-tech-ui）

```css
.img-block{margin:26px 0;text-align:center}
.img-block img{max-width:100%;height:auto;border:1px solid var(--border);
  border-radius:12px;background:#fff;box-shadow:0 4px 18px rgba(15,23,42,.07)}
.img-block figcaption{margin-top:10px;font-size:13.5px;color:var(--text-secondary)}
```

## 禁止事项

- 不引用外部网络图片 URL 作为正文图片（离线可用）；确需网络图先下载入 images/。
- 不把只属于某实验的图放 `assets/img/`（归属三定律）。
- 中文标注的图表/统计图，画布与 CSS 字体显式设置 `Noto Sans CJK SC, WenQuanYi Micro Hei`。