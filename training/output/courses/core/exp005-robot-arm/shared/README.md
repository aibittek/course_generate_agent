# 实验页统一样式规范（机械臂应用与开发 · exp-01 ~ exp-07）

> **为什么要这份文件**：之前只共享了 `shared/tutorial.css`，但**页面骨架、顶栏 HTML、侧栏写法**
> 都是每个页面各自手写的，于是越写越不像。exp-03 曾经自己造了 `.stitle` 侧栏标题、
> 用 `<p class="crumb">` 做面包屑、顶栏塞了 3 个导航链接，和 exp-02 完全两个样子。
> 从现在起，新建或重构页面一律按本文档 + `shared/_page-template.html` 来。

---

## 一、三层约束（缺一层就会走样）

| 层 | 文件 | 管什么 | 谁能改 |
|---|---|---|---|
| **公共样式** | `shared/tutorial.css` | 顶栏、侧栏、卡片、表格、提示条、流程图、页尾导航 | **只改这里**，一次改全章生效 |
| **页面骨架** | `shared/_page-template.html` | DOM 结构顺序、类名、层级 | 复制后只替换文字 |
| **本页专属** | 页面内 `<style>` | 仅本页独有的新组件（如 3D 卡片、PWM 波形） | 允许，但见下方禁令 |

---

## 二、顶栏（最容易走样的地方，逐字禁止改动）

```html
<div class="topbar">
  <a class="logo" href="../../../index.html" style="text-decoration:none;color:inherit" title="返回课程首页">🤖 具身智能课程 · <i>教程首页</i></a>
  <div class="crumb"><a href="../../../index.html#core">核心课程</a> / <a href="../index.html">机械臂应用与开发</a> / EXP-0X</div>
</div>
```

- 只有 **EXP-0X** 这一处可变
- 面包屑必须是 `<div class="crumb">`，**不是 `<p>`**（`<p>` 会带段落边距，顶栏会被撑高）
- 不要在顶栏里加第二组导航链接（曾经加过 `课程目录 / 核心课程 / 总首页`，和面包屑重复且挤）

## 三、侧栏

- 分组标题一律 `<h4>`（公共样式写的就是 `.side h4`），**不要自造 `.stitle` 之类的类名**
- 当前章节链接加 `class="now"`
- 顺序固定：**本页目录 → 本课程实验**

## 四、正文与页尾

- 每个二级章节：`<section class="blk" id="sN">` + `<h2><span class="no">01</span>标题</h2>`
- 页尾：`<nav class="expnav">`（左上一节 / 右下一节） + `<footer>`
- 代码块直接用 `<pre>`，`tutorial.js` 会自动加复制按钮，**不要自己再写一套**

## 五、主题色

每章一个色调，**只覆盖 4 个变量**，不要直接给组件写死颜色：

```css
:root{--theme:#dc2626;--theme-deep:#b91c1c;--theme-bg:#fee2e2;--theme-bd:#fecaca}
```

现有取值：exp-01 蓝 `#2563eb`、exp-02/03 红 `#dc2626`、exp-04 紫 `#7c3aed`、
exp-05 青 `#0891b2`、exp-06 绿 `#0d9488`、exp-07 琥珀 `#d97706`。

## 六、页面内 `<style>` 的禁令

❌ 禁止覆盖这些选择器（它们属于公共层，覆盖就会全章不一致）：
`.topbar` `.logo` `.crumb` `.side` `.side h4` `.side a` `.wrap` `.content`
`.blk` `.exp-head` `.tip` `table` `th` `td` `.flow` `.kcard` `.expnav` `footer`

✅ 允许新增本页组件，但必须用**本页前缀**命名，例如：
`.fk-embed`（运动学 3D）、`.pwm-wave`（波形）、`.ik-panel`（IK 演示）。
组件内部要复用公共变量（`var(--theme)`、`var(--border)`…），不要写死颜色。

## 七、嵌入式互动卡片（3D / SVG 动画）

- 外框用 `<div class="frame-embed">` + `iframe`，**高度显式给**（通常 640）
- 图注用 `<p class="embed-cap">`
- 互动内容本身是独立文件，放在本实验目录的 `_build/` 下，**页面不内联大段 JS**

## 八、验收清单（每次改完跑一遍）

1. 和 `exp-02` 并排打开，**顶栏高度、面包屑位置、侧栏字号、卡片圆角**应完全一致
2. 侧栏标题是 `h4` 样式（小号、字距拉开、灰色），不是大黑字
3. 页面滚动时侧栏高亮跟着走、代码块有"复制"按钮
4. 宽度收到 960px 以下，侧栏自动隐藏、内容单列
5. `node --check` 检查页面内联脚本（有 JS 的页面）

---

## 附：自查命令（PowerShell）

```powershell
$base = "training\output\courses\core\exp005-robot-arm"
# 找出自己造侧栏标题的页面
Select-String -Path "$base\exp-*\index.html" -Pattern 'class="stitle"'
# 找出把面包屑写成 <p> 的页面
Select-String -Path "$base\exp-*\index.html" -Pattern '<p class="crumb"'
# 找出顶栏里多加导航的页面
Select-String -Path "$base\exp-*\index.html" -Pattern 'class="sep"|class="links"'
```
三条命令都无输出，才算顶栏/侧栏合规。
