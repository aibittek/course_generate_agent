# 讯飞聆智 网页课件模板 v0.2

用网页替代 PPT 的课件模板。**单文件 HTML + assets 素材目录 + 可换肤主题**，无任何依赖、无构建工具，双击 `template.html` 即可离线运行（可用浏览器全屏投影授课）。

## 目录约定（每门课一个文件夹）

```
courses-web/
└── 01-ros2-overview/          # 一节课 = 一个文件夹
    ├── index.html             # 由 template.html 复制并填充内容
    ├── themes/                # 主题文件（复制模板的 themes 目录）
    └── assets/
        ├── logo.png           # 公司 LOGO（可全局共享，用相对/绝对路径）
        ├── fig-arch.png       # 架构图、实物图
        ├── demo.mp4           # 实验演示视频
        └── narration-06.mp3   # 教师讲解音频（可选）
```

## 页面布局类型（data-layout）

| 布局 | 用途 | 关键元素 |
|---|---|---|
| `cover` | 封面 | kicker + 大标题 + 标签（课时/设备/方案） |
| `cards` | 学习目标/要点 | grid2/grid3 + .card |
| `stats` | 行业数据/参数 | .bignum 渐变大字 |
| `image-text` | 架构图/图文讲解 | .fig（点击放大 lightbox） |
| `video` | 实验演示视频 | `<video controls>` |
| `code` | 代码讲解 | .codeblock + 讲解音频（可选） |
| `quiz` | 课堂测验 | data-answer，自动判分 + 解析 |
| `flip` | 概念自测 | 点击翻面卡片 |
| `steps` | 实验/开发流程 | 横向时间线 |
| `summary` | 小结与预告 | 已掌握 + 预告 |

## 操作方式

- 键盘：`←` `→` 翻页，`F` 全屏，`G` 目录，`C` 切换主题
- 鼠标/触屏：底部按钮、触摸滑动、LOGO 点开目录
- 测验每题仅判一次，自动高亮正确项并展开解析

## 主题（v0.2）

颜色全部抽成 CSS 变量，皮肤独立为 `themes/*.css`，**改一行 `<link>` 或点顶栏 🎨 即可整体换肤**：

| 文件 | 风格 | 适用 |
|------|------|------|
| `themes/light.css` | 浅色科技白（蓝+青） | **默认**，投影/明亮教室 |
| `themes/ocean.css` | 浅蓝渐变教育风 | 柔和、长时间授课 |
| `themes/paper.css` | 米白学术（墨绿+赭石） | 长文讲义、需打印 |
| `themes/dark.css` | 深色科技（荧光青） | 弱光环境、大屏演示 |

顶栏 🎨 或按 `C` 可实时切换预览，选择记录在 localStorage；确定主色后，把 `<link id="theme">` 固定为对应文件并删掉切换按钮即可。
新增主题：复制任一 themes 文件改变量，并在 `template.html` 的 `THEMES` 数组中登记。

> LOGO：浅色主题直接用黑色 LOGO；深色主题由 `html[data-dark="1"]` 自动反白，拿到白色版 LOGO 后删掉该 CSS 规则。

## 后续扩展点（v0.3 候选）

1. **内容与模板分离**：slide 内容抽成 `content.json`，模板 JS 动态渲染 → 便于批量生成几十节课
2. 学习进度 localStorage 记忆、课后测验成绩导出（对接班级管理）
3. 白板批注、双栏对比布局、iframe 嵌入仿真（Gazebo/RViz Web）
