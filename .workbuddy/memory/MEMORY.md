﻿﻿﻿# MEMORY.md — 项目长期笔记

## 课程文案风格（唯一事实源：`.workbuddy/skills/course-copy-spec/SKILL.md`）

- **硬规则：凡生成或修改 `training/output/` 目录下的课程讲义、教程文案、练习题、目录卡片简介前，必须先加载 `course-copy-spec` 技能并全程遵循**——初学者定位、去 AI 味禁止清单、原理/操作/演示/代码逻辑/练习的分区输出形态、架构图与流程图硬要求、生成后自检清单，全部以该 SKILL.md 为准。**生效范围仅限 `training/output/`**：该目录之外（courses/ 源讲义、ros2_ws 源码等）不适用。
- 此处不留规范副本。要调整规范：直接改 SKILL.md 并在其"修订记录"加一行，或在对话里说明让 agent 代改；MEMORY 与此冲突时以 SKILL.md 为准。

## 课程结构约定

- exp003-ros2-application 页面 = 每实验 9~10 节（引入→原理→…→验收→总结）；总览与深潜分开放（如三大支柱总览在 02，互动深挖另起 04）。
- 章节号变更只改**显示编号**，section 的 `id="sN"` 与目录 href 保持不动，避免锚点失效；`#sN` 的 N 无前导零。
- 素材目录边界：只读 `courses/` 等历史目录，新素材复制进本实验 `images/` 再引用。
- 优化五条标准：先疼后药 / 类比贯穿（普通话·微信群·工具箱）/ 每节一句话可复述 / 交叉引用必须真实 / 标签与内容一致。
- 定稿用词（2026-10-08，exp003 确立）："架构发展变化"（不用"架构跃迁"）；"跑通第一个 ROS2 的 HelloWorld 程序"。
- 问题引入组件固定为"编号标题条 + 动画 + 本幕字幕"的**同页纵向全展开**面板，不做标签轮播。
- 技术底座：单文件 HTML、无 CDN 依赖；编辑前先 grep 当前实际文本（文件可能已被人工改过），勿凭记忆写匹配串。唯一例外口径：exp005 `principles/` 原理实验室页配**本地** three.min.js(r128)/OrbitControls.js（仍非 CDN）。
- **目录页 ↔ 实验页 同步核对法（2026-10-09 确立）**：改动实验页小节结构后必须三处同步——①实验页侧栏目录、②目录页对应卡片 explist、③节间过渡语（"下一节/下面"指向必须是真实下一节）；锚点用 `grep 'id="sN"'` 列全量再逐条对。
- **卡片简介防编造**：目录页卡片里的术语/算法/型号必须先在讲义 `ros_practice_lab_guide.md` grep 到出处；难度星级、学时以讲义"四、实验难度"表为准。
- 实操类内容可合并为**同一 section 内的多关卡 tab**（gtab/gpane + gate() 切换，样式自包含在页内 `<style>`），显示编号顺移但 `id` 不动。
- **串口设备名口径（2026-10-16 定）**：课程页面/文案一律写 实验箱 `/dev/stm32`、小车 `/dev/car1_stm32`；`/dev/ttyUSB0` 禁再出现（源码 test_servo_direct.py 即 /dev/stm32）。
- **exp-02 改版约定（2026-10-16 定）**：10 节新结构（s1 关节怎么动 archify 框架图 / s2 舵机伺服系统 3D 含脉宽 / s3 协议表↔3D 动作 / s4 安全+环境 / s5 实操全景 / s6~s8 功能由简到繁 / s9 排障 / s10 验收）；3D 走**可复用模块** `assets/modules/servo-lab/`（本地 three.js，iframe 嵌首页，多页共用，不破坏主页单文件约定）；安全=页首红条警示（锚点跳 s4）+ s4 三条铁律 checklist。
- **archify 技能**（`~/.workbuddy/skills/archify`，SkillHub WorkBuddy 移植版，装前已过手动安全审计）：画架构/流程/时序图，`validate`→`deliver`→`visual-check` 三步验收。Windows 要点：node 传 `C:/...` 风格路径 + `ARCHIFY_UPDATE_CHECK_DISABLED=1`。坑：workflow v2 勿手动指定 drop 路由（交自动）；phase 区间不可共列；label 超宽需显式加 `width`；每轮只改被诊断的那一处；solver budget-exhausted → 简化拓巷（砍节点/加泳道）不加手工路由；desktop-readability 差零点几 px → 收窄列宽+短标题；visual-check 以 `*.visual-check.json` 回执为最终事实（可能拿到中间超时轮的残留输出）。
- **servo-lab 共享模块**（2026-10-16 建）：`training/output/assets/modules/servo-lab/servo-lab.html`，双模式 `?mode=lab|proto`，本地 three.js，嵌入方式相对路径 `../../../../assets/modules/servo-lab/servo-lab.html`（iframe + 显式 height）。后续 exp-03/principles 讲舵机直接复用，勿重画。
- **实验页统一样式约束（2026-10-20 定，用户问责后补）**：机械臂课程 7 个实验页共用 `shared/tutorial.css` + `shared/tutorial.js`，但**光有公共 CSS 不够**——页面骨架/顶栏/侧栏必须照 `shared/_page-template.html` 复制，规则写在 `shared/README.md`。**硬性三条**：①顶栏逐字照抄，只有 `EXP-0X` 可变，面包屑必须 `<div class="crumb">`（用 `<p>` 会撑高顶栏）；②侧栏分组标题必须 `<h4>`，禁止自造 `.stitle`；③页面内 `<style>` 禁止覆盖 `.topbar/.side/.crumb/.blk/.tip/table/.expnav` 等公共选择器，新组件用本页前缀（`.fk-` / `.pwm-`）。主题色只改 4 个变量。自查：`Select-String` 搜 `class="stitle"` / `<p class="crumb"` / `class="sep"|class="links"`，三条都得 0 输出；批量修复用 `tools/normalize_exp_pages.py`。
- **3D 教学模型：一律"先写简易 URDF，再加载渲染"（2026-10-20 定，用户明确要求）**：唯一事实源 = `training/output/assets/modules/urdf-arm/simple-arm.urdf`（只用 box/cylinder/sphere 基本体，约 10 KB）。加载链 = `urdf-arm.js`（迷你 URDF 解析器，只依赖全局 THREE，不支持 mesh）+ `tools/urdf_to_js.py` 把 .urdf 包成 `window.URDF_ARM_TEXT` 的 .js（**file:// 下不能 fetch，这一步必需**）。页面只管 UI。**禁止**：①拿真机 car1.urdf + STL 网格塞进课件（用户否决过，太杂）；②在 HTML 里手写 three.js 几何（改起来一团乱）。**URDF 三条硬规则**：所有转动关节轴线过同一条竖直线、横向偏置全 0、每段连杆居中在关节中心；`arm_linkN` 原点 = 第 N 个关节转轴中心（关节壳以该原点为中心）；零位必须立成一根笔直的柱子（`?pose=zero&mode=side` 验收）。真机的底座偏装 56.6mm / J2 +25mm / J5 −25.3mm 教学版一律归零。**夹爪默认左右开合**（两指沿 ±Y 偏置、指板在 X 方向薄，默认朝 +X 伸出）；J5 只负责绕自身轴转朝向。
- **坐标帧显示的坑（2026-10-20，已全部踩过并修好）**：①标签画布宽度按 `measureText` 算，固定宽度会裁掉 `arm_base_link` 这类长名；②先 `strokeText` 白描边（lineWidth 12）再 `fillText`，压在彩色连杆上也读得清；③轴长 38 mm、标签 17px（小了用户会说"字太小、坐标系太短"）；④正交取景纵向尺寸两种模式不同（侧视用高度 MODEL.y、俯视用进深 MODEL.z）；侧视只扩上边界 10%，整体平移会把底盘挤出画面；正交缩放写成 `* ZOOM`（ZOOM<1 放大），写成 `/ZOOM` 滚轮方向会反。
- **标签排布三种视图必须分别处理**：3D 用 `LABEL_OFF` 逐 link 定制（底座两个只差 20 mm，必须一左下/一右上；J3/J4 只差 43 mm，`arm_link4` 摆到 +X 侧）；侧视统一 `x=−0.105` + 逐 link 的 z（`SIDE_HEIGHT` 固定刻度表，直接赋 Sprite 的局部 z，不要每帧读世界坐标）；俯视关掉贴 link 的标签，改用挂在 `base_link` 的固定图例列（`legendGroup`）。排布循环里只处理 `userData.isLinkLabel`，轴字母（`isAxisLabel`）永远跟着轴尖走。
- **3D 交互标配（2026-10-20 定）**：默认相机 `theta=+0.883, phi=1.16`（右前侧看，+X 指向画面左下）；右下角世界坐标小视窗（`drawGizmo()`，必须 `cam.updateMatrixWorld(true)` 后再求逆矩阵，否则三轴叠成团）；平移 `PAN` + `panBy()`（右键/中键/Shift+拖动），滚轮缩放、双击复位、2D 视图左键拖动即平移。**JS 注释里绝不能出现 ASCII 双引号**，会把 `/* */` 提前截断导致整页白屏；排查用 `node --check` 检查抽出的内联脚本。
- **改完必跑三张验收图**：`?pose=zero&mode=side&axes=0`（必须一根笔直柱子、读数 x 0 y 0 z 0.592）/ `?mode=side`（标签不压连杆）/ `?mode=top`（左侧图例、模型居中）。超大会话里 Bash 工具会整体失效（Exit 127），改用 **PowerShell 工具**跑 `agent-browser open/screenshot/eval`。
- **课程页文案与模型必须同源**：改了 URDF 就要同步 02 节坐标树图的偏移数字、03 节读数表与"和 3D 模型对得上吗"那段——读数用 Python 独立验算一遍再写进文案，别用页面读数反填。
- **旧注（2026-10-19，手写几何时代，已被上条取代，仅留作坑记录）**：URDF 的 joint origin 是**子节点（关节）**在父节点系的位置，不等于"这一段几何"的起点——装饰几何（立柱/法兰/转台/夹爪）必须自己算 `世界 z = 父链累加 + 局部偏移`，让相邻件**重叠 1~2mm**，否则悬空。浅灰件放白底上会读成"缝"，关节过渡段一律用深色同色系。坐标帧这类"要整体开关"的东西，必须收进一个数组统一显隐（挂在各 link 下时 `group.visible` 管不到）。**连杆一律严格竖直，横向偏置用方料拼直角，绝不用 `rod(A→B)` 拉斜线；短横杆长度小于直径会变成胖碟。相机 `TGT` 要对准机械臂轴线、fov 取 24 左右的弱透视，否则竖杆会被透视压歪。** 自检：`agent-browser` 开 `_build/*.html` → eval 设滑杆值复现姿态 → 截图逐段看。
- **课程网页文案：一律"对学生说话"的口吻，禁止 AI 套路（2026-10-20 用户明确指出）**：用户原话「你的这个 AI 味道好浓」。**必删的六种句式**：①"一句话目标："、"先把三件事说清楚"这类标签式开头；②破折号"——"（本页曾出现 32 处，全部删掉）；③"先…再…最后"三段式排比；④"不是 X，而是 Y"对偶（真需要时改成口语叙述）；⑤"到这里你学到/这一步你学到"的总结腔；⑥整段无加粗（关键句没有视觉落点）。**加粗规则（2026-10-20 补）**：每段最多一处，加在该段最需要读者记住的那句话上；术语名不加粗（Forward Kinematics / FK 不加），加的是定义和结论；整页加粗密度控制在「一段一处」左右。**应该写成**：先抛一个具体问题或场景，再讲人话解释，公式和结论排在后面；允许"你会发现""这个坑八成错在这儿""不放心可以对照算"这种口语；每段只讲一件事，段落短。改写稿见 exp-03 index.html（s0~s10）。


- **iframe 里的 SVG 图，字号小是因为"画布太宽被等比缩小"，不是字号设小了（2026-10-20 用户："文字还是比较小"）**：`svg{width:100%}` + 宽 viewBox（如 1180）在 1180px 容器里是 1:1，但 iframe 内边距一大就会被压。**判断方法**：`容器实际宽度 ÷ viewBox 宽度 = 显示缩放比`，字号 ÷ 缩放比才是肉眼看到的。**修法**：①保结构不变，只把字号往上提 2~4px（8.5→12、9→12、11→15）；②框的高度同步加 8~20px 给行高腾位置；③iframe 高度跟着加。**别用"缩小 viewBox"的办法**——那会让框一起缩小，字并没有变大。

- **`<pre><code>` 在深色代码块里会糊成一片（2026-10-20 用户："里面的内容看不清楚"）**：`shared/tutorial.css` 的 `code{}` 给**所有**行内 code 加了浅灰底 `--bg-soft` + 边框，包在深色 `<pre>` 里就变成"浅灰底 + 浅灰字"，几乎看不见。**修法**：`tutorial.css` 里补一条 `pre code{background:none;border:0;border-radius:0;padding:0;color:inherit}`。写公式块一律用 `<pre><code>...</code></pre>`，别只写 `<pre>` 再手动加颜色。

- **写手册/文档类页面，配图绝不能省（2026-10-20 用户："你这个很严重啊，需要按照文档的来啊，配图也不能丢失啊"）**：用户给了 PDF 和 md 两个来源时，**优先用 md + 同目录 assets**——md 里的图是原始高清图，PDF 抽出来的是压缩版。做之前先把 `assets/` 全部列一遍、逐张 `Read` 看内容，建立"图片 → 章节"映射再动笔。抓到图后：①用 MD5 查重（md 里常有同一张图出现两次）；②同一内容有高清和缩略版时留高清。**禁止用表格/文字描述替代实拍图**，尤其是"接口位置""按键位置""ID 编号""对齐检查"这类必须看图才能操作的内容。校验时统计"引用数 / assets 文件数 / 未被引用数"，要求引用全覆盖、0 冗余。
