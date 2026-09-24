---
name: "embed-video"
description: "Embeds local video files into course HTML pages with responsive players, poster frames, captions and controls, and manages the videos/ directory per experiment. Invoke when user asks to insert, place, organize or troubleshoot local videos or mp4 assets in course content."
---

# 本地视频插入（embed-video）

## 存放位置（先定位再插入）

遵循 `course-output-layout` skill 的目录规范：

- 课程首页/产品级通用演示：`training/output/assets/video/`
- 同课程多实验共享：`training/output/courses/<课程>/shared/videos/`
- **仅单实验使用（默认）：`training/output/courses/<课程>/exp-<NN>-<短名>/videos/`**

命名：`主题-描述.mp4`（如 `demo-nav-mapping.mp4`）。参数见 `video_meeting_system_params.jsonl` 采集标准。

## 视频规格

- 编码 H.264 + AAC，容器 MP4（浏览器兼容最好），≤1920×1080，30fps，CRF 20~23
- 优先横屏 16:9；片长建议单段 ≤90 秒（科普教程场景）
- 提供封面帧 `poster`（同目录 `主题.jpg` 或 `主题-poster.jpg`）

## 标准插入片段

```html
<figure class="video-block reveal">
  <div class="video-frame">
    <video controls preload="metadata" playsinline
           poster="./videos/demo-nav-mapping-poster.jpg"
           width="1920" height="1080">
      <source src="./videos/demo-nav-mapping.mp4" type="video/mp4">
      你的浏览器不支持视频播放，请下载
      <a href="./videos/demo-nav-mapping.mp4">demo-nav-mapping.mp4</a> 观看。
    </video>
  </div>
  <figcaption>图 3-1｜建图导航实际运行演示（小车 C1）</figcaption>
</figure>
```

要点：

1. **路径**（均相对实验页 `index.html` 所在目录）：同实验 `./videos/xxx.mp4`；课程共享 `../shared/videos/...`（shared 与实验目录同级）；全站 `../../../../assets/video/...`（实验页深 4 层，含分类目录）。绝不写绝对路径。
2. **必须有 poster** 与 `preload="metadata"`，避免页面一打开就加载整段视频。
3. **带字幕**时加 track（字幕放同实验 `videos/` 下，WebVTT）：
   ```html
   <track kind="captions" src="./videos/demo-nav-mapping.vtt" srclang="zh" label="中文" default>
   ```
4. **自动播放**仅允许静音循环：`autoplay muted loop playsinline`（背景演示场景），教学视频一律用户手动播放。
5. `figcaption` 必填，编号规则"图 N-M｜说明"。

## 配套样式（并入页面 clean-tech-ui 风格 CSS）

```css
.video-block{margin:28px 0}
.video-frame{border:1px solid var(--border);border-radius:14px;overflow:hidden;
  background:#0f172a;box-shadow:0 8px 30px rgba(15,23,42,.10)}
.video-frame video{display:block;width:100%;height:auto}
.video-block figcaption{margin-top:10px;font-size:13.5px;color:var(--text-secondary);text-align:center}
```

## 多视频组织

- 一屏多个相关短视频（步骤演示）用 2 列网格：
  ```html
  <div class="video-grid"> <!-- .video-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px} -->
  ```
- 实验页建议视频出现顺序：原理动画(2D) → 实拍视频 → 交互动画，放在对应讲解段落之后。

## 禁止事项

- 不引用网络在线视频链接做课程主体内容（离线可用性优先）。
- 不把大视频复制进 `assets/`（只放全站通用的）。
- 不生成中间产物/重编码脚本到 output 目录；重编码脚本放工作临时目录，只把最终 mp4 + poster 写入 videos/。