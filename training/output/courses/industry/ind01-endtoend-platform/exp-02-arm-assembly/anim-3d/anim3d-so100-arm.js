import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export function init(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x111827);
  scene.fog = new THREE.Fog(0x111827, 8, 20);

  const cam = new THREE.PerspectiveCamera(40, container.clientWidth / container.clientHeight, 0.1, 100);
  cam.position.set(4, 3.5, 5);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);
  container.style.position = 'relative';

  // ── 灯光 ──
  scene.add(new THREE.HemisphereLight(0xffffff, 0x1e293b, 0.7));
  const dir = new THREE.DirectionalLight(0xffffff, 1.4);
  dir.position.set(5, 8, 4);
  dir.castShadow = true;
  dir.shadow.mapSize.set(1024, 1024);
  dir.shadow.camera.left = -5; dir.shadow.camera.right = 5;
  dir.shadow.camera.top = 5; dir.shadow.camera.bottom = -5;
  scene.add(dir);
  const fill = new THREE.DirectionalLight(0x5eead4, 0.3);
  fill.position.set(-4, 3, -3); scene.add(fill);

  // ── 地面 ──
  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(5, 48),
    new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: .2, roughness: .9 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.01;
  ground.receiveShadow = true;
  scene.add(ground);
  const grid = new THREE.GridHelper(8, 16, 0x334155, 0x1e293b);
  grid.material.opacity = .4; grid.material.transparent = true;
  scene.add(grid);

  // ── 材质工厂 ──
  const mat = (c, m = .4, r = .5) => new THREE.MeshStandardMaterial({ color: c, metalness: m, roughness: r });
  const colors = { j1: 0x0d9488, j2: 0x38bdf8, j3: 0xa78bfa, j4: 0xfbbf24, j5: 0xf472b6, grip: 0x34d399, link: 0x475569, dark: 0x1e293b };

  // ── 构建铰接臂 ──
  // 层级: root → J1(yaw) → J2(pitch) → upperArm → J3(pitch) → forearm → J4(pitch) → wrist → J5(roll) → gripperBase → fingers

  const root = new THREE.Group();
  scene.add(root);

  // 底座圆盘
  const baseDisk = new THREE.Mesh(new THREE.CylinderGeometry(.5, .6, .12, 32), mat(colors.dark, .6, .3));
  baseDisk.position.y = .06;
  baseDisk.castShadow = true; baseDisk.receiveShadow = true;
  root.add(baseDisk);

  // ── J1: 底座旋转 (yaw, Y轴) ──
  const j1 = new THREE.Group();
  j1.position.y = .12;
  root.add(j1);
  // J1 电机柱
  const j1Motor = new THREE.Mesh(new THREE.CylinderGeometry(.22, .26, .3, 24), mat(colors.j1));
  j1Motor.position.y = .15;
  j1Motor.castShadow = true;
  j1.add(j1Motor);
  // J1 标识环
  const j1Ring = new THREE.Mesh(new THREE.TorusGeometry(.27, .03, 8, 24), mat(colors.j1, .5, .3));
  j1Ring.rotation.x = Math.PI / 2; j1Ring.position.y = .15;
  j1.add(j1Ring);

  // ── J2: 肩俯仰 (pitch, Z轴) ──
  const j2 = new THREE.Group();
  j2.position.y = .3;
  j1.add(j2);
  // J2 电机
  const j2Motor = new THREE.Mesh(new THREE.CylinderGeometry(.18, .2, .26, 24), mat(colors.j2));
  j2Motor.rotation.z = Math.PI / 2;
  j2Motor.castShadow = true;
  j2.add(j2Motor);
  // 大臂连杆
  const upperArm = new THREE.Mesh(new THREE.BoxGeometry(.14, 1.2, .14), mat(colors.link, .5, .4));
  upperArm.position.y = .65;
  upperArm.castShadow = true;
  j2.add(upperArm);
  // 大臂装饰条
  const upperStripe = new THREE.Mesh(new THREE.BoxGeometry(.16, .02, .02), mat(colors.j2));
  upperStripe.position.y = .65;
  j2.add(upperStripe);

  // ── J3: 肘俯仰 (pitch, Z轴) ──
  const j3 = new THREE.Group();
  j3.position.y = 1.3;
  j2.add(j3);
  const j3Motor = new THREE.Mesh(new THREE.CylinderGeometry(.16, .18, .22, 24), mat(colors.j3));
  j3Motor.rotation.z = Math.PI / 2;
  j3Motor.castShadow = true;
  j3.add(j3Motor);
  // 小臂连杆
  const forearm = new THREE.Mesh(new THREE.BoxGeometry(.12, 1.0, .12), mat(colors.link, .5, .4));
  forearm.position.y = .55;
  forearm.castShadow = true;
  j3.add(forearm);

  // ── J4: 腕俯仰 (pitch, Z轴) ──
  const j4 = new THREE.Group();
  j4.position.y = 1.1;
  j3.add(j4);
  const j4Motor = new THREE.Mesh(new THREE.CylinderGeometry(.14, .16, .2, 24), mat(colors.j4));
  j4Motor.rotation.z = Math.PI / 2;
  j4Motor.castShadow = true;
  j4.add(j4Motor);
  // 腕段
  const wristSeg = new THREE.Mesh(new THREE.BoxGeometry(.1, .4, .1), mat(colors.link, .5, .4));
  wristSeg.position.y = .25;
  wristSeg.castShadow = true;
  j4.add(wristSeg);

  // ── J5: 腕滚转 (roll, Y轴) ──
  const j5 = new THREE.Group();
  j5.position.y = .5;
  j4.add(j5);
  const j5Motor = new THREE.Mesh(new THREE.CylinderGeometry(.12, .14, .18, 24), mat(colors.j5));
  j5Motor.castShadow = true;
  j5.add(j5Motor);
  // 夹爪基座
  const gripBase = new THREE.Mesh(new THREE.BoxGeometry(.16, .06, .16), mat(colors.grip));
  gripBase.position.y = .14;
  gripBase.castShadow = true;
  j5.add(gripBase);
  // 夹爪左指
  const fingerL = new THREE.Mesh(new THREE.BoxGeometry(.04, .2, .06), mat(colors.grip));
  fingerL.position.set(-.06, .28, 0);
  fingerL.castShadow = true;
  j5.add(fingerL);
  // 夹爪右指
  const fingerR = new THREE.Mesh(new THREE.BoxGeometry(.04, .2, .06), mat(colors.grip));
  fingerR.position.set(.06, .28, 0);
  fingerR.castShadow = true;
  j5.add(fingerR);

  // ── OrbitControls ──
  const controls = new OrbitControls(cam, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = .08;
  controls.target.set(0, 1.5, 0);
  controls.minDistance = 3;
  controls.maxDistance = 12;
  controls.maxPolarAngle = Math.PI * .85;

  // ── 关节角控制 ──
  const jointAngles = { j1: 0, j2: 0, j3: 0, j4: 0, j5: 0, grip: .06 };
  const jointRanges = {
    j1: { min: -180, max: 180, label: 'J1 底座旋转', en: 'shoulder_pan' },
    j2: { min: -90, max: 90, label: 'J2 肩俯仰', en: 'shoulder_lift' },
    j3: { min: -135, max: 135, label: 'J3 肘俯仰', en: 'elbow_flex' },
    j4: { min: -90, max: 90, label: 'J4 腕俯仰', en: 'wrist_flex' },
    j5: { min: -180, max: 180, label: 'J5 腕滚转', en: 'wrist_roll' },
    grip: { min: 0, max: 15, label: '夹爪开合', en: 'gripper' }
  };

  function applyAngles() {
    j1.rotation.y = jointAngles.j1 * Math.PI / 180;
    j2.rotation.z = jointAngles.j2 * Math.PI / 180;
    j3.rotation.z = jointAngles.j3 * Math.PI / 180;
    j4.rotation.z = jointAngles.j4 * Math.PI / 180;
    j5.rotation.y = jointAngles.j5 * Math.PI / 180;
    fingerL.position.x = -jointAngles.grip / 100 - .01;
    fingerR.position.x = jointAngles.grip / 100 + .01;
  }

  // ── UI 控件层 ──
  const ui = document.createElement('div');
  ui.style.cssText = 'position:absolute;left:8px;top:8px;right:8px;display:flex;flex-direction:column;gap:6px;pointer-events:none;font-family:sans-serif';
  container.appendChild(ui);

  const sliders = {};
  Object.keys(jointRanges).forEach(k => {
    const r = jointRanges[k];
    const row = document.createElement('div');
    row.style.cssText = 'display:flex;align-items:center;gap:8px;pointer-events:auto;background:rgba(17,24,39,.82);border:1px solid #334155;border-radius:8px;padding:5px 10px';
    const lab = document.createElement('span');
    lab.textContent = r.label;
    lab.style.cssText = 'font-size:11px;color:#5eead4;font-weight:700;min-width:80px;white-space:nowrap';
    const sl = document.createElement('input');
    sl.type = 'range'; sl.min = r.min; sl.max = r.max; sl.value = jointAngles[k];
    sl.step = k === 'grip' ? .5 : 1;
    sl.style.cssText = 'flex:1;accent-color:#5eead4;width:120px';
    const val = document.createElement('span');
    val.textContent = jointAngles[k] + (k === 'grip' ? 'mm' : '°');
    val.style.cssText = 'font-size:10px;color:#94a3b8;font-family:monospace;min-width:42px;text-align:right';
    sl.addEventListener('input', () => {
      jointAngles[k] = parseFloat(sl.value);
      val.textContent = sl.value + (k === 'grip' ? 'mm' : '°');
      applyAngles();
    });
    row.appendChild(lab); row.appendChild(sl); row.appendChild(val);
    ui.appendChild(row);
    sliders[k] = sl;
  });

  // 按钮行
  const btnRow = document.createElement('div');
  btnRow.style.cssText = 'display:flex;gap:6px;pointer-events:auto;flex-wrap:wrap';
  ui.appendChild(btnRow);

  const btnReset = document.createElement('button');
  btnReset.textContent = '⟲ 归零';
  btnReset.style.cssText = 'padding:4px 12px;border:1px solid #475569;border-radius:6px;background:rgba(71,85,105,.3);color:#94a3b8;font-size:11px;cursor:pointer';
  btnReset.addEventListener('click', () => {
    Object.keys(jointAngles).forEach(k => { jointAngles[k] = 0; sliders[k].value = 0; });
    jointAngles.grip = .06; sliders.grip.value = .06;
    applyAngles();
    // 更新值显示
    Object.keys(sliders).forEach(k => {
      const valEl = sliders[k].parentElement.querySelector('span:last-child');
      valEl.textContent = sliders[k].value + (k === 'grip' ? 'mm' : '°');
    });
  });
  btnRow.appendChild(btnReset);

  // 预设姿态
  const btnWave = document.createElement('button');
  btnWave.textContent = '👋 挥手';
  btnWave.style.cssText = 'padding:4px 12px;border:1px solid #a78bfa;border-radius:6px;background:rgba(167,139,250,.15);color:#c4b5fd;font-size:11px;cursor:pointer';
  btnRow.appendChild(btnWave);

  // 挥手动画
  let waving = false, waveT = 0;
  btnWave.addEventListener('click', () => {
    waving = !waving;
    btnWave.textContent = waving ? '⏸ 停止' : '👋 挥手';
  });

  // ── 信息提示 ──
  const hint = document.createElement('div');
  hint.style.cssText = 'position:absolute;bottom:6px;left:50%;transform:translateX(-50%);font-size:11px;color:#64748b;background:rgba(17,24,39,.7);padding:3px 12px;border-radius:6px;pointer-events:none;white-space:nowrap';
  hint.textContent = '🖱 拖拽旋转 · 滚轮缩放 · 滑杆控制各关节 · 右键平移';
  container.appendChild(hint);

  // ── 离屏暂停 ──
  let visible = true;
  new IntersectionObserver(([e]) => visible = e.isIntersecting, { threshold: .05 }).observe(container);

  // ── 主循环 ──
  function loop() {
    requestAnimationFrame(loop);
    if (!visible) return;

    if (waving) {
      waveT += 0.04;
      jointAngles.j1 = Math.sin(waveT * .5) * 30;
      jointAngles.j2 = -30 + Math.sin(waveT * 1.5) * 15;
      jointAngles.j3 = -60;
      jointAngles.j4 = Math.sin(waveT * 2) * 25;
      jointAngles.j5 = Math.sin(waveT * 1.5) * 45;
      jointAngles.grip = 8;
      Object.keys(jointAngles).forEach(k => sliders[k].value = jointAngles[k]);
      // 更新值显示
      const labels = ui.querySelectorAll('span:last-child');
      Object.keys(jointRanges).forEach((k, i) => {
        if (labels[i]) labels[i].textContent = Math.round(jointAngles[k] * 10) / 10 + (k === 'grip' ? 'mm' : '°');
      });
      applyAngles();
    }

    controls.update();
    renderer.render(scene, cam);
  }

  applyAngles();
  loop();

  // ── 自适应 ──
  addEventListener('resize', () => {
    cam.aspect = container.clientWidth / container.clientHeight;
    cam.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });

  return { scene, renderer, cam, controls };
}
