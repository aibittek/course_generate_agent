---
name: "course-output-layout"
description: "Defines the canonical output directory layout for all generated course content under training/output (per-experiment separation of images, videos, 2D/3D animations, interactive demos). Invoke FIRST whenever generating, modifying, or adding any course HTML, media, or asset, before writing any file."
---

# 课程输出目录基准规范（course-output-layout）

**所有课程类产物的唯一输出根目录：**

```
e:\Source\xflz_eai_car1\course_generate_agent\training\output\
```

生成任何课程页面、素材、动画之前，必须先按本规范决定文件落盘位置。完整规范见根目录 `README.md`。

**范围边界**：仓库根目录下已有的 `courses/`、`courses_output/` 等历史目录**只读参考、绝不修改**；一切新建、编辑、素材落盘仅发生在 `training\output\` 内。

## 目录树（必须遵守）

```
training/output/
├── assets/                  # 跨课程共享：css/ js/ lib/ img/ video/ fonts/
├── products/                # 产品介绍页（每款产品一个 slug 目录）
│   ├── b2-box/              # B2 实验箱：index.html + images/ + videos/ + source/*.pdf
│   └── c1-car/              # C1 小车：index.html + images/ + videos/ + source/*.pdf
└── courses/
    ├── index.html           # 总首页（分类导航，对应首页 CAT 1/2/3；右上角"产品介绍 ▾"下拉）
    ├── _templates/          # 实验目录模板 exp-default/
    ├── core/                # CAT 1 · 具身智能核心课程
    ├── cases/               # CAT 2 · 具身智能综合案例（如 exp007-intelligent-factory）
    └── industry/            # CAT 3 · 具身智能行业应用
        └── <课程编号-课程名>/     # 例：cases/exp007-intelligent-factory
            ├── index.html        # 课程首页（实验卡片）
            ├── shared/           # 本课程多实验共享的 images/videos（内部再分）
            └── exp-<NN>-<短名>/   # 每个实验一个目录，严格分离
                ├── index.html    # 实验教程页
                ├── images/       # 图片 → embed-image skill
                ├── videos/       # 视频 → embed-video skill
                ├── anim-2d/      # 2D 动画 → anim-2d skill
                ├── anim-3d/      # 3D 动画 → anim-3d skill（可含 models/）
                └── interactive/  # 交互动画 → anim-interactive skill
```

**分类目录与总首页一致**：`core/` 对应 CAT 1、`cases/` 对应 CAT 2、`industry/` 对应 CAT 3。新建课程必须放进对应分类目录；分类目录在该分类第一门课程开工时再创建（不预先建空目录）。课程编号与总首页卡片编号保持一致（如 CASE-02 → `cases/`）。

**产品介绍页**：顶级 `products/<slug>/` 每款产品一个目录；原版 PDF → `source/`（仅存档，页面不提供"下载 PDF"按钮），产品图 → `images/`（`fig-` 前缀），介绍/演示视频 → `videos/`（mp4 + `-poster.jpg` 封面，按 embed-video skill 插入），页面固定 `index.html`（clean-tech-ui 浅色风）。产品页返回总首页 `../../courses/index.html`（`training/output/` 根目录无 index.html，勿写 `../../index.html`）；总首页链产品页 `../products/<slug>/index.html`；产品页互链 `../<另一slug>/index.html`；两产品页结构对齐（hero → 特色 → 参数 → 架构 → 课程 → 演示视频 → 联系方式）。

## 归属三定律

1. **单实验使用** → 放该实验自己的子目录（images/videos/anim-2d/anim-3d/interactive）。
2. **同课程多实验使用** → 放课程级 `shared/` 下对应类型目录。
3. **多课程使用** → 才放顶层 `assets/`。

## 命名与路径规则

- 目录名全小写+连字符；实验目录固定格式 `exp-01-slam-nav`。
- 实验入口页固定命名 `index.html`。
- 文件名前缀：图片 `fig-`/`icon-`，2D 动画 `anim2d-`，3D 动画 `anim3d-`，交互动画 `ix-`，视频用主题名。
- 页面内引用一律相对路径（`./videos/demo.mp4`），禁止绝对路径与 `file:///`。引用共享资源按**页面深度算清 `../` 层数**（注意课程多一层分类目录 `core|cases|industry/`）：
  | 页面位置 | 到根 `assets/` |
  |---|---|
  | `courses/index.html` | `../assets/` |
  | `courses/<分类>/<课程>/index.html` | `../../../assets/` |
  | `courses/<分类>/<课程>/exp-XX/index.html` | `../../../../assets/` |
  | 实验页内嵌 iframe（`interactive/`、`anim-2d/` 内页） | `../../../../../assets/` |
  | `products/<slug>/index.html` | `../../assets/` |
  | 总首页 → 产品页 | `../products/<slug>/index.html`（跨到与 courses/ 平级的 products/） |
- 中文内容必须设置字体 `font-family: "Noto Sans CJK SC","WenQuanYi Micro Hei",...`（图表画布同理）。
- 网格/试用素材、临时脚本不得写入本目录（放工作临时目录）。

## 创建新实验的流程

1. 复制 `courses/_templates/exp-default/` → `courses/<分类>/<课程>/exp-<NN>-<短名>/`（内含 images/ videos/ anim-2d/ anim-3d/ interactive/ 五个空目录）。
2. 在该目录写 `index.html`（页面样式遵循 `clean-tech-ui` skill）。
3. 素材按归属三定律存放，并用对应媒体 skill 插入。
4. 更新课程首页与总首页 `courses/index.html`，登记新实验卡片与链接。

## 与其他 skill 的配合

- 样式 → `clean-tech-ui`
- 视频插入 → `embed-video`；图片 → `embed-image`
- 2D 动画 → `anim-2d`；3D → `anim-3d`；交互 → `anim-interactive`
- HTML 视频合成/字幕配音 → hyperframes 系列（hyperframes / hyperframes-media）
- React 组件动画 → electronic-component-library；GSAP 动效 → gsap skill