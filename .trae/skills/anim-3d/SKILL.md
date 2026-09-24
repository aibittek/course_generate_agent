---
name: "anim-3d"
description: "Creates three.js-based 3D animations for courses (robot models, URDF/gltf viewers, exploded views, orbit demos), stored in the experiment's anim-3d/ directory. Invoke when user wants 3D animation, 3D model display, or 3D scene rendering inside generated course content."
---

# 3D 动画（anim-3d）

用于机器人结构、传感器布局、URDF 模型查看、装配爆炸图等**空间感原理**演示。基于 three.js（放在 `assets/lib/`，离线引用）。

## 存放位置

遵循 `course-output-layout` skill：默认放当前实验 `training/output/courses/<课程>/exp-<NN>-<短名>/anim-3d/`：

```
anim-3d/
├── anim3d-robot-urdf.js      # 场景脚本（命名前缀 anim3d-）
├── anim3d-sensor-layout.js
└── models/                   # 该实验的模型/贴图（gltf、fbx、hdr、纹理）
    ├── robot_base.glb
    └── textures/
```

跨实验共享才提升到 `shared/anim-3d/` 或顶级 `assets/`（three.js 库本身在 `assets/lib/three.module.js`，多实验共用同版本，复制路径 `--，禁止换版本重复拷贝`）。

## 标准接线（实验页 index.html）

```html
<div class="anim3d-block reveal">
  <div id="scene-urdf" class="anim3d-canvas"
       data-src="./anim-3d/anim3d-robot-urdf.js"
       style="height:420px"></div>
  <p class="anim3d-hint">拖动旋转 · 滚轮缩放 · 右键平移</p>
  <p class="anim3d-caption">动画 2-1｜小车 C1 底盘与激光雷达安装位姿</p>
</div>

<script type="importmap">
{ "imports": { "three": "../../../../assets/lib/three.module.js",
               "three/addons/": "../../../../assets/lib/addons/" } }
</script>
<script type="module">
  document.querySelectorAll('.anim3d-canvas[data-src]').forEach(async el => {
    const mod = await import(el.dataset.src);
    mod.init(el);              // 每个 anim3d-*.js 导出 init(container)
  });
</script>
```

## anim3d-*.js 模板（导出 init）

```js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export function init(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf8fafc);

  const camera = new THREE.PerspectiveCamera(45,
    container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(2.2, 1.6, 2.8);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  scene.add(new THREE.HemisphereLight(0xffffff, 0xdbe4ef, 1.0));
  const dir = new THREE.DirectionalLight(0xffffff, 1.2);
  dir.position.set(3, 5, 2); scene.add(dir);

  // 模型加载：GLTFLoader（import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'）
  // new GLTFLoader().load('./models/robot_base.glb', g => scene.add(g.scene));

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  // 自动旋转 + 离屏暂停
  let visible = true;
  new IntersectionObserver(([e]) => visible = e.isIntersecting,
    { threshold: 0.05 }).observe(container);

  (function loop() {
    requestAnimationFrame(loop);
    if (!visible) return;               // 离屏不渲染，省电
    controls.update();
    renderer.render(scene, camera);
  })();

  addEventListener('resize', () => {    // 自适应容器宽度
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });

  return { scene, renderer, camera, controls };
}
```

## 配套样式

```css
.anim3d-block{margin:30px 0;text-align:center}
.anim3d-canvas{width:100%;border:1px solid var(--border);border-radius:14px;
  overflow:hidden;background:#f8fafc;box-shadow:0 8px 28px rgba(15,23,42,.08);cursor:grab}
.anim3d-hint{font-size:12.5px;color:var(--text-muted);margin-top:8px}
.anim3d-caption{font-size:13.5px;color:var(--text-secondary)}
```

## 工程规则

1. **模型必须放本实验 `anim-3d/models/`**，`fetch` 一律相对路径（`file://` 直开会有 CORS 限制 → 页脚提示"建议用本地 http 服务打开"或在课程首页提供启动命令 `python -m http.server` 说明）。
2. 首选 **glTF(.glb)** 格式；单模型压到 <5MB，贴图 ≤2048。
3. 每个 `anim3d-*.js` **只导出 `init(container)`**，禁止全局变量泄漏；场景资源在容器卸载时 `renderer.dispose()`。

4. 一个实验多个 3D 场景分别建独立 js 文件，按 id/`data-src` 挂载，互不耦合。
5. 降级：WebGL 不可用时显示静态 `images/` 截图占位（在 init 前 `try{}catch{}` 换图）。
6. 中文 HUD 文字（提示、标注 sprite）字体设置 `Noto Sans CJK SC, WenQuanYi Micro Hei`。
7. 需要**整段 3D 渲染成视频**后插入 → 先产 mp4 入 `videos/`，再按 `embed-video` 插入（不是本 skill 场景）。