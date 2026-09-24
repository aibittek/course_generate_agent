# 课程输出根目录规范（training/output）

> 所有课程生成的最终产物一律输出到本目录。临时脚本、草稿等中间产物放在工作临时目录，不要放进来。
>
> **边界约束**：只读取、不修改仓库根目录下已有的 `courses/`、`courses_output/` 等历史目录；所有新建与修改仅限 `training/output/` 内部。

## 一、顶层结构

```
training/output/
├── README.md                  # 本规范文件
├── assets/                    # 跨课程共享资源（全站级，仅放真正通用的）
│   ├── css/                   # 公共样式（如 clean-tech-ui.css 设计系统）
│   ├── js/                    # 公共脚本（如侧边栏、卡片交互）
│   ├── lib/                   # 第三方库（three.js、gsap、echarts 等）
│   ├── img/                   # 公共图片（logo、通用图标）
│   ├── video/                 # 公共视频（片头、通用演示）
│   └── fonts/                 # 公共字体（中文字体子集等）
└── courses/                   # 课程产物根目录
    ├── index.html             # 总首页（分类导航）
    ├── _templates/            # 实验目录模板（用于复制创建新实验）
    │   └── exp-default/ ...
    ├── core/                  # CAT 1 · 具身智能核心课程
    ├── cases/                 # CAT 2 · 具身智能综合案例
    └── industry/              # CAT 3 · 具身智能行业应用
└── products/                  # 产品介绍页（每款产品一个目录）
    ├── b2-box/                # 具身智能实验箱B2旗舰版
    │   ├── index.html            # 图文产品介绍页（clean-tech-ui 浅色风）
    │   ├── images/               # 本产品专属图片（fig- 前缀）
    │   ├── videos/               # 功能介绍视频（mp4 + 同名 -poster.jpg）
    │   └── source/               # 原版 PDF 存档（页面不提供下载入口）
    └── c1-car/                # 具身智能机器人小车 C1
        ├── index.html
        ├── images/
        ├── videos/               # 演示视频（mp4 + 同名 -poster.jpg）
        └── source/               # 原版 PDF 存档（c1-manual.pdf，页面不提供下载）
```

**分类目录与总首页三大分类一一对应**（`core/` ↔ CAT 1、`cases/` ↔ CAT 2、`industry/` ↔ CAT 3）。课程先归类再落盘；分类目录在该分类第一门课程开工时创建，不预先建空目录。

**产品介绍页规范**：顶级 `products/` 目录与 `courses/` 平级，每款产品一个 slug 目录；原版 PDF 放 `source/`（仅存档，页面不提供"下载 PDF"按钮），产品提取图放 `images/`（`fig-` 前缀），产品介绍/演示视频放 `videos/`（mp4 + 同名 `-poster.jpg` 封面，插入方式遵循 embed-video skill：`preload="metadata"` + poster 必带）。总首页 topbar 右上角"产品介绍 ▾"下拉链入；产品页返回总首页路径为 `../../courses/index.html`（总首页在 `courses/` 下），互链另一产品为 `../<另一slug>/index.html`；两产品页结构对齐（hero → 特色 → 参数 → 架构 → 课程 → 演示视频 → 联系方式）。

## 二、课程/实验目录结构（按实验严格分离）

分类目录下每门课程一个目录，每个实验一个子目录，**实验自己的素材只放在自己的实验目录内**：

```
courses/cases/                          # 分类目录：core | cases | industry
└── exp007-intelligent-factory/         # 课程目录：课程编号-课程名（小写、连字符）
    ├── index.html                         # 课程首页（含该课程所有实验的卡片/目录）
    ├── course-spec.yaml                   # 课程元数据
    ├── shared/                            # 课程级共享素材（只在本课程多个实验间共享）
    │   ├── images/
    │   ├── videos/
    │   └── js/
    ├── exp-01-slam-nav/                   # 实验目录：exp-序号-实验名（小写、连字符）
    │   ├── index.html                     # 实验教程页（侧边栏+原理讲解+动画）
    │   ├── images/                        # 本实验的图片
    │   ├── videos/                        # 本实验的视频（mp4/webm，横屏优先）
    │   ├── anim-2d/                        # 2D 动画（原理示意，svg/内嵌html）
    │   ├── anim-3d/                        # 3D 动画（three.js 场景，独立 js）
    │   └── interactive/                    # 交互动画（可操作 demo/模拟器）
    ├── exp-02-vision-grasp/
    │   └── ...（同上结构）
    ├── exp-03-voice-llm/
    │   └── ...
    └── exp-04-full-loop/
        └── ...
```

## 三、命名规则

| 项目 | 规则 | 示例 |
|------|------|------|
| 课程目录 | `课程编号-课程名` 全小写+连字符 | `exp007-intelligent-factory` |
| 实验目录 | `exp-两位序号-短横线实验名` | `exp-01-slam-nav` |
| 实验页面 | 统一 `index.html` | `exp-01-slam-nav/index.html` |
| 图片 | `类型-描述-序号.png/.jpg/.svg/.webp` | `fig-slam-flow-01.png` `icon-lidar.svg` |
| 视频 | `主题-描述.mp4`（H.264, ≤1920×1080） | `demo-nav-mapping.mp4` |
| 2D 动画 | `anim2d-主题.svg` 或 `anim2d-主题.html` | `anim2d-slam-principle.svg` |
| 3D 动画 | `anim3d-主题.js`（含独立 init 函数） | `anim3d-robot-urdf.js` |
| 交互动画 | `ix-主题.html` 或 `ix-主题.js` | `ix-slam-particle-filter.html` |

## 四、资源归属原则（必须遵守）

1. **实验素材放实验目录**：只被一个实验用到的图片/视频/动画，必须放在该实验自己的 `images/ videos/ anim-2d/ anim-3d/ interactive/` 下。
2. **课程共享放 `shared/`**：同一课程多个实验都用到的素材，提升到课程 `shared/`。
3. **全站共享放 `assets/`**：多门课程都用的才进顶层 `assets/`。
4. **相对路径引用**：实验页引用素材一律用相对路径（`./videos/demo.mp4`），禁止绝对路径、禁止 `file:///`。引用共享资源按**页面深度**算清 `../` 层数：

   | 页面位置 | 到根 `assets/` | 到课程 `shared/` |
   |---|---|---|
   | `courses/index.html`（总首页） | `../assets/` | — |
   | `courses/<分类>/<课程>/index.html`（课程首页） | `../../../assets/` | `./shared/` |
   | `courses/<分类>/<课程>/exp-XX/index.html`（实验页） | `../../../../assets/` | `../shared/` |
   | 实验页内嵌 iframe（`interactive/` 等） | `../../../../../assets/` | `../../../../../shared/` |
   | `products/<slug>/index.html`（产品页） | `../../assets/` | — |

   > 注意 1：课程比原来多一层分类目录（`core|cases|industry/`），所有 `../` 层数比旧结构多 1 层。校验方法：上传/预览后打开浏览器 Network 面板，`.js` `.svg` `.mp4` 无 404 才算层数写对（曾两次因少写层数导致 three.js 加载 404）。
   > 注意 2：总首页 → 产品页为 `../products/<slug>/index.html`（首页在 `courses/` 下，跨到平级 `products/`）；产品页 → 总首页为 `../../courses/index.html`（`training/output/` 根目录没有 index.html，勿写 `../../index.html`）。
5. **3D 动画注意**：需要贴图/模型（glTF）的，模型文件放到该实验的 `anim-3d/models/` 子目录。
6. **自包含优先**：如果实验页需要离线单文件分发，可以把小型 svg/交互动画内嵌进 html，大文件（视频、模型）仍外链存放。

## 五、配套 Skill（.trae/skills/ 下的自定义技能）

生成内容时按下列 skill 执行（触发词命中即调用）：

| Skill | 用途 |
|-------|------|
| `course-output-layout` | 一切课程产物的输出目录基准规范（先读它） |
| `embed-video` | 本地视频插入与 videos/ 目录管理 |
| `embed-image` | 图片插入与 images/ 目录管理 |
| `anim-2d` | 2D 原理示意图/动画（anim-2d/） |
| `anim-3d` | 3D 动画（three.js，anim-3d/） |
| `anim-interactive` | 交互动画/可操作 demo（interactive/） |
| `clean-tech-ui` | 网页统一浅色简约科技风样式 |

## 六、创建新实验的标准动作

1. 从 `courses/_templates/exp-default/` 复制到 `courses/<分类>/<课程>/` 下，命名为 `exp-NN-xxx/`；
2. 创建 `index.html`；
3. 素材按第四节归属原则放入对应子目录；
4. 课程首页 `index.html` 中登记该实验卡片。