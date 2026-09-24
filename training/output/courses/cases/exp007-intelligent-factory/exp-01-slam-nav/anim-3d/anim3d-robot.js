// anim3d-robot.js —— 小车 C1 底盘 + 激光雷达 3D 展示（程序化建模，零外部模型依赖）
// 引用：页面 importmap 提供 "three" 与 "three/addons/"
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export function init(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf8fafc);

  const camera = new THREE.PerspectiveCamera(45,
    container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(1.6, 1.1, 2.0);

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true });
  } catch (e) {
    container.innerHTML = '<p style="padding:24px;color:#64748b">当前环境不支持 WebGL，已降级为静态说明。</p>';
    return null;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.shadowMap.enabled = true;
  container.appendChild(renderer.domElement);

  // 灯光
  scene.add(new THREE.HemisphereLight(0xffffff, 0xdbe4ef, 1.0));
  const dir = new THREE.DirectionalLight(0xffffff, 1.1);
  dir.position.set(2, 4, 2); dir.castShadow = true;
  scene.add(dir);

  // 地面网格
  const grid = new THREE.GridHelper(6, 30, 0xcbd5e1, 0xe2e8f0);
  scene.add(grid);

  const robot = new THREE.Group();
  const isReduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 底盘
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(0.50, 0.10, 0.34),
    new THREE.MeshStandardMaterial({ color: 0x2563eb, roughness: 0.45 }));
  body.position.y = 0.11; body.castShadow = true;
  robot.add(body);

  // 上层板
  const top = new THREE.Mesh(
    new THREE.BoxGeometry(0.36, 0.04, 0.26),
    new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.6 }));
  top.position.y = 0.19; top.castShadow = true;
  robot.add(top);

  // 四轮
  const wheelGeo = new THREE.CylinderGeometry(0.07, 0.07, 0.05, 24);
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.9 });
  [[0.17, 0.18], [0.17, -0.18], [-0.17, 0.18], [-0.17, -0.18]].forEach(([x, z]) => {
    const w = new THREE.Mesh(wheelGeo, wheelMat);
    w.rotation.x = Math.PI / 2;
    w.position.set(x, 0.07, z);
    robot.add(w);
  });

  // 激光雷达（旋转示意）
  const lidar = new THREE.Group();
  const base = new THREE.Mesh(
    new THREE.CylinderGeometry(0.055, 0.06, 0.05, 28),
    new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.5 }));
  const head = new THREE.Mesh(
    new THREE.CylinderGeometry(0.05, 0.05, 0.06, 28),
    new THREE.MeshStandardMaterial({ color: 0x0891b2, roughness: 0.35, metalness: 0.3 }));
  head.position.y = 0.055;
  lidar.add(base, head);
  lidar.position.set(0, 0.23, 0);
  robot.add(lidar);

  // 扫描示意环
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.10, 0.60, 48, 1, 0, Math.PI / 3),
    new THREE.MeshBasicMaterial({ color: 0x0891b2, transparent: true, opacity: 0.16, side: THREE.DoubleSide }));
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = 0.26;
  robot.add(ring);

  scene.add(robot);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 0.15, 0);
  controls.autoRotate = !isReduced;
  controls.autoRotateSpeed = 1.6;
  controls.minDistance = 0.8;
  controls.maxDistance = 6;

  // 离屏暂停渲染
  let visible = true;
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; },
    { threshold: 0.05 }).observe(container);

  let raf;
  (function loop() {
    raf = requestAnimationFrame(loop);
    if (!visible) return;
    const t = performance.now() * 0.001;
    head.rotation.y = t * 2.5;                 // 雷达自转
    ring.rotation.z = -t * 1.5;                 // 扫描环旋转
    controls.update();
    renderer.render(scene, camera);
  })();

  const onResize = () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  };
  addEventListener('resize', onResize);

  return {
    dispose() {
      cancelAnimationFrame(raf);
      removeEventListener('resize', onResize);
      renderer.dispose();
    }
  };
}