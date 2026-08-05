## 实验1：基于讯飞六麦阵列的串口通信与唤醒事件实验（4h）

> **本实验源码**：
> - `ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/uart_device.py` — 串口通信封装（pyserial）
> - `ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/xf_mic_array.py` — AIUI 协议解析、帧拆装、唤醒事件
> - `ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/xf_mic_array_gui.py` — Tkinter 演示 GUI（直接运行）
>
> **学习路径**：由浅入深分为 5 节，依次为：串口通信 → 麦克风阵列原理 → AIUI 协议 → 唤醒事件防抖 → GUI 可视化。

### 1.1 关联知识点

#### 1.1.1 串口通信与设备识别
- 1.1.1 串口通信概念 > 概念 > UART 是一种异步串行通信协议，通过 TX/RX 两根线按位收发字节
- 1.1.2 pyserial 库基础 > 原理 > `serial.Serial` 封装 open/read/write/close，timeout 控制阻塞行为
- 1.1.3 VID/PID 自动识别 > 流程 > USB 设备的硬件指纹 VID(0x1a86)+PID(0x55d4) 用于无串口名称时自动查找

#### 1.1.2 麦克风阵列与声源定位
- 1.2.1 麦克风阵列原理 > 概念 > 6 个麦克风均布圆周，通过到达时间差(TDOA)实现声源定位
- 1.2.2 声源定位 beam/angle > 原理 > beam(0~5) 指向能量最大的麦克风,angle(0~360°) 为顺时针方向角
- 1.2.3 AIUI 协议框架 > 事实 > 讯飞私有协议,以 0xA5 为同步头,JSON payload 描述唤醒事件

#### 1.1.3 AIUI 串口协议与帧解析
- 1.3.1 字节序与校验和 > 原理 > 小端序存储多字节字段,校验和 = (~sum + 1) & 0xFF
- 1.3.2 帧结构组成 > 流程 > 同步头(1)+用户ID(1)+类型(1)+长度(2)+ID(2)+payload(n)+校验(1) = 7+n+1 字节
- 1.3.3 接收缓冲与拆帧 > 分析 > 跨 read 累积到 rx_buffer,搜索 0xA5 定位帧头,处理伪同步头与校验失败

#### 1.1.4 唤醒事件与防抖机制
- 1.4.1 唤醒事件字段 > 流程 > 从 ivw JSON 提取 beam/angle/keyword/score/power/start_ms/end_ms
- 1.4.2 时间窗口防抖 > 原理 > last_wakeup_time + 3 秒窗口,防止噪声连续触发
- 1.4.3 回调与线程锁 > 分析 > wakeup_callback + wakeup_lock 保证事件处理并发安全

#### 1.1.5 Tkinter GUI 可视化监控
- 1.5.1 Tkinter Canvas 基础 > 概念 > create_oval/line/text 在画布上绘制几何与文字
- 1.5.2 环形阵列绘制 > 流程 > 极坐标 0° 在正下方,顺时针 60° 间隔布 6 个麦克风
- 1.5.3 线程安全事件刷新 > 应用 > 接收线程 put 事件到 queue,主线程 after(50ms) 循环消费

### 1.2 实验目标

1. **理解串口通信本质** — 知道 UART、波特率、设备文件 /dev/ttyACM* 的概念
2. **掌握 pyserial 基础调用** — 能用 open/read/write/close 与设备通信
3. **理解 6 麦阵列的声源定位原理** — 知道 beam 编号与 angle 角度的物理意义
4. **掌握 AIUI 协议帧结构** — 能从 16 进制字节流手算帧边界与校验和
5. **理解唤醒事件的防抖机制** — 知道 3 秒时间窗 + Lock 是如何防止重复触发的
6. **能运行 GUI 演示并定制** — 跑通 xf_mic_array_gui.py,扩展 PINYIN_MAP 加入新词

### 1.3 实验环境

| 类别 | 配置 |
|------|------|
| 硬件 | B2/C1（含讯飞 6 麦阵列模块，VID=0x1a86, PID=0x55d4）|
| OS | Ubuntu 22.04 + USB ACM 内核模块 |
| Python | 3.10 |
| 核心库 | pyserial==3.5, tkinter（系统自带）|
| 串口 | /dev/ttyACM0, 波特率 115200, 8N1 |
| 源码 | ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/ |

### 1.4 实验难度

- 难度: ⭐ 入门
- 重点: 串口通信基础；AIUI 帧结构；唤醒回调机制
- 难点: 字节级帧解析；伪同步头与校验和失败处理

### 1.5 实验现象

**快速验证流程**:
```bash
# 1. 插上 6 麦阵列 USB，确认设备出现
ls -l /dev/ttyACM*
# 期望输出: crw-rw---- 1 root dialout 166, 0  ... /dev/ttyACM0

# 2. 授权普通用户访问
sudo chmod 666 /dev/ttyACM0

# 3. 直接跑 GUI 演示（推荐先用这个看效果）
cd ros2_ws/src/xflz_eai_car1/interaction/car1_speech/tools/
python3 xf_mic_array_gui.py

# 4. GUI 弹出后，对着麦克风说"小飞同学"
#    - 看到 6 个麦克风圆点中对应 beam 的变红
#    - 从中心画出一支红色箭头指向声源方向
#    - 右侧"当前唤醒词"显示拼音,中文显示"小飞同学"
#    - score/power 进度条更新
#    - 底部"事件历史"列表新增一行

# 5. 无显示器/无 GUI 场景：仅终端模式
python3 xf_mic_array_gui.py --headless
# 终端输出: 检测到唤醒! Beam: 2, Angle: 120.5, Keyword: xiao3 fei1 tong2 xue2

# 6. Ctrl+C 退出
```

**预期效果**:
- GUI 启动 1 秒内状态栏从"● 未连接"变为"● 已连接 /dev/ttyACM0"
- 朗读"小飞同学"后立即触发，箭头指向声源方向
- 同一方向 3 秒内重复唤醒只触发 1 次（防抖窗口）
- 60 次真实唤醒测试中,score > 1500 命中率达 95% 以上

### 1.6 实验步骤

#### 整体流程图

```mermaid
graph LR
    A[步骤1: 串口设备识别] --> B[步骤2: 麦克风阵列原理]
    B --> C[步骤3: AIUI 帧解析]
    C --> D[步骤4: 唤醒事件防抖]
    D --> E[步骤5: GUI 可视化定制]
    E --> F[完成]
```

---

#### 步骤1：串口设备识别与 pyserial 入门（阶段一：能运行，30min）

> 本步骤对应 `tools/uart_device.py` 全文（约 100 行）

**知识点讲解**：

**串口通信概念（1.1.1）**
- **原理**：UART（Universal Asynchronous Receiver/Transmitter）是一种**异步串行通信协议**，通信双方各用一根线（TX 发 / RX 收），按预先约定的**波特率（bits per second）**逐位传输字节。本实验 6 麦阵列采用 **115200 波特率、8 数据位、无校验、1 停止位**（简称 8N1）。与并行通信不同，串口只需要 2~4 根线就能通信，但速度受限于波特率。常见的 USB 转串口芯片（CH340、CP2102）会在 Linux 下呈现为 `/dev/ttyUSB*` 或 `/dev/ttyACM*` 设备文件。普通程序通过读写这个文件就能与硬件通信。
- **源码对应**：`uart_device.py` 第 7-19 行 `__init__` 中的 baudrate=115200, bytesize=8, parity=N, stopbits=1

**pyserial 库基础（1.1.2）**
- **原理**：`pyserial` 是 Python 最常用的串口库，核心类是 `serial.Serial`。使用流程是：(1) `Serial(port, baudrate, ...)` 打开设备；(2) `read(size)` / `write(data)` 收发数据；(3) `close()` 关闭。`timeout` 参数控制 `read` 的阻塞行为，设为 1 表示最多等 1 秒就返回（避免线程死等）。如果用上下文管理器 `with Serial(...) as s:`，退出时会自动关闭。
- **源码对应**：`uart_device.py` 第 40-65 行 `open()` 方法

**VID/PID 自动识别（1.1.3）**
- **原理**：每个 USB 设备都有全球唯一的 **VID（Vendor ID）** 和 **PID（Product ID）** 标识，存放在设备硬件中。Linux 下可通过 `lsusb` 命令查看，VID:PID 形式如 `1a86:55d4`。当同时插入多个同类设备时，光看 `/dev/ttyACM0` 无法确定哪个是目标设备，必须用 VID/PID 过滤。`pyserial.tools.list_ports` 提供 `comports()` 返回所有串口，每个 `port.hwid` 字符串包含 VID:PID，可直接做子串匹配。
- **源码对应**：`uart_device.py` 第 21-38 行 `find_device()` 方法

**操作步骤**：

1. 物理确认设备已连接：
   ```bash
   # 查看 USB 设备列表（关注 1a86:55d4 那行）
   lsusb
   # 期望: Bus 001 Device 005: ID 1a86:55d4 QinHeng Electronics ...
   
   # 查看生成的设备文件
   ls -l /dev/ttyACM*
   # 期望: crw-rw---- 1 root dialout 166, 0 ... /dev/ttyACM0
   ```

2. 枚举系统所有串口：
   ```bash
   python3 -c "
   import serial.tools.list_ports as lp
   for p in lp.comports():
       print(f'{p.device}  VID:PID={p.hwid}  描述={p.description}')
   "
   # 期望: /dev/ttyACM0  USB VID:PID=1A86:55D4  ...
   ```

3. 用最小代码测试串口收发：
   ```python
   import serial, time
   s = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=1)
   print(f"打开 {s.port} 成功")
   # 6 麦阵列持续输出数据,只读取不发送
   for i in range(5):
       data = s.read(64)
       print(f"读 #{i}: {len(data)} 字节  hex={data.hex(' ')[:60]}")
       time.sleep(0.2)
   s.close()
   # 观察：每秒有大量 16 进制字节,这就是 AIUI 协议帧
   ```

4. 阅读 `uart_device.py` 全文（仅 100 行），重点理解：
   - `__init__` 默认参数（VID=0x1a86, PID=0x55d4, baud=115200）
   - `find_device` 用 `comports()` 枚举并匹配 VID:PID 子串
   - `open` / `close` / `send` / `receive` 4 个方法均为薄封装
   - `send` 返回发送字节数,`receive` 默认 size=64

**易错点**：
- ⚠️ **Permission denied: '/dev/ttyACM0'** → **解决**：`sudo chmod 666 /dev/ttyACM0` 或加入 dialout 用户组
- ⚠️ **设备名不是 /dev/ttyACM0** → **解决**：用 VID/PID 自动查找模式不传 `--port`
- ⚠️ **read() 永远返回空** → **解决**：检查 USB 是否插紧,波特率是否匹配（阵列固定 115200）

---

#### 步骤2：麦克风阵列原理与硬件组成（阶段一：能理解，30min）

> 本步骤不写代码,先理解硬件

**知识点讲解**：

**麦克风阵列原理（1.2.1）**
- **原理**：单个麦克风只能"听声音",多个麦克风按几何规则排列组成"阵列"后,通过**到达时间差（Time Difference Of Arrival, TDOA）**就能反推声源方向。想象 6 个人围坐一圈,有人在桌子南侧说话,南侧两个麦克风先听到、北侧最后听到,时间差反推方向。**6 麦环形阵列**是常见布局,360° 范围内定位精度可达 ±5°。
- **关键参数**:
  - 麦克风间距: 本模块约 35mm,既要避免间距过小导致分辨率差,也要避免过大引入混响
  - 采样率: 通常 16kHz,人声覆盖到 8kHz 足够
  - 输出: 不仅输出混合音频,还输出**每个麦克风的原始 PCM** + **波束(beam) 编号** + **角度(angle) 数值**

**声源定位 beam/angle（1.2.2）**
- **原理**：
  - `beam` 编号 0~5 表示 6 个麦克风中的能量最大者,等价于"离声源最近的那只"
  - `angle` 角度 0~360° 是顺时针方向角,本模块约定 **0° 在正下方 (M0)**、顺时针递增
  - 两者关系: `angle ≈ beam × 60°`,但实际会有 ±10° 浮动,因为是 6 麦之间的能量插值
  - 唤醒触发时,模块同时返回 score（0~2000 置信度）和 power（0~2,000,000 能量值）
- **可视化对应**: GUI 中红色箭头从中心画出指向 `angle` 度,对应 beam 的圆点变红

**AIUI 协议框架（1.2.3）**
- **原理**：AIUI（Artificial Intelligence User Interface）是科大讯飞的设备协议,定义了 PC 与 6 麦阵列模块之间的通信格式。其核心特点:
  - **二进制帧 + JSON payload 混合**: 帧头是二进制（便于机器解析），payload 是 JSON（便于人类阅读）
  - **多消息类型**: 0x01 握手 / 0x04 设备事件 / 0x05 设置命令 / 0xFF 握手响应
  - **同步字节 0xA5**: 用于帧对齐,类似 TCP 的起始位
  - **校验和**: 求和取反加一,简单的 8 位校验
- **实际工作流程**: 模块上电后,PC 发送握手 → 模块应答 → PC 可发送设置命令（如设置唤醒词） → 模块持续推送事件（唤醒、波束变化等）

**操作步骤**：

1. 物理观察 6 麦阵列模块（圆形 PCB，6 个小孔对应 6 个 MEMS 麦克风，M0~M5 顺时针编号）

2. 用 `arecord` 录制 5 秒音频并播放,验证硬件能正常拾音：
   ```bash
   # 注意：6 麦阵列默认输出数字音频,需用 ALSA 的 plughw
   arecord -D plughw:1,0 -d 5 -f S16_LE -r 16000 -c 1 test.wav
   aplay test.wav  # 听到自己说的话即正常
   ```

3. 观察不同方向的 score/angle 关系（用 GUI 演示）：
   - 站在模块正前方（0°）说话 → GUI 箭头指向正下方
   - 站在右侧（90°）说话 → 箭头指向右边
   - 站在后方（180°）说话 → 箭头指向上方
   - **观察规律**: arrow 角度 ≈ 你站的方向

**易错点**：
- ⚠️ **6 麦模块方向约定反了** → **解决**：以 0° 在正下方为基准,自己站的方向不一定是 0°
- ⚠️ **只录到一片噪声** → **解决**：检查 ALSA 设备编号（`arecord -l` 查看）
- ⚠️ **angle 总是 0** → **解决**：模块需要先唤醒一次,后续才会持续输出 angle 更新

---

#### 步骤3：AIUI 协议帧解析（阶段二：能理解，60min）

> 本步骤对应 `tools/xf_mic_array.py` 第 106-158 行 `_process_buffer()` 与第 160-213 行 `_handle_frame()`

**知识点讲解**：

**字节序与校验和（1.3.1）**
- **原理**：**字节序（Endianness）**是多字节数据在内存中的存储顺序:
  - **大端（Big Endian）**：高位字节在前,人类阅读习惯（网络协议常用）
  - **小端（Little Endian）**：低位字节在前,PC 处理器常用
- **AIUI 协议使用小端**: 例如消息长度 300 编码为 `0x2C 0x01`（300 = 0x012C,低位 0x2C 在前）
- **校验和算法**: `checksum = (~sum(data) + 1) & 0xFF`,等价于"求和取负的低 8 位"
  - 例如数据 `[0xA5, 0x01, 0x04, 0x05, 0x00, 0x01, 0x00, 0x7B]` 的校验和 = `(0xA5+0x01+0x04+0x05+0x01+0x7B) & 0xFF` 的取反加一
- **源码对应**：`xf_mic_array.py` 第 29-31 行 `checksum()` 方法

**帧结构组成（1.3.2）**
- **原理**：AIUI 协议帧 = 7 字节头部 + N 字节 payload + 1 字节校验,共 8+N 字节:
  ```
  偏移  长度  字段       说明
  0     1     sync       固定 0xA5,用于定位帧起始
  1     1     user_id    用户 ID,通常 0x01
  2     1     msg_type   消息类型 0x01 握手 / 0x04 事件 / 0x05 设置 / 0xFF 响应
  3~4   2     msg_len    payload 长度（小端）
  5~6   2     msg_id     消息 ID（小端,用于配对请求和响应）
  7~    N     payload    数据,通常为 JSON 字符串
  最后  1     checksum   帧校验和
  ```
- **示例**: 完整帧 `A5 01 04 2C 01 01 00 7B 22 74 79 70 65 ... 9F`
  - sync=0xA5, user_id=0x01, msg_type=0x04 (事件)
  - msg_len=0x012C=300 字节
  - msg_id=0x0001
  - payload 是 300 字节 JSON
  - 校验和为最后 1 字节
- **源码对应**：`xf_mic_array.py` 第 160-167 行 `_handle_frame()` 的开头部分

**接收缓冲与拆帧（1.3.3）**
- **原理**：串口 `read(64)` 不一定恰好返回一个完整帧,可能:
  - 返回半个帧（头部还没收齐）
  - 返回 1.5 个帧（第一个完整 + 第二个头部）
  - 返回恰好 1 个完整帧
  - 包含**伪同步头**: 帧中其他位置意外出现 0xA5,被误识别为新帧头
- **解决方案（双缓冲 + 容错）**:
  1. 用 `rx_buffer` 累积所有 read 结果
  2. 每次 read 后从 buffer 头部搜索 0xA5
  3. 找到后读 msg_len,计算 total_len = 7 + msg_len + 1
  4. **整帧未到齐就退出循环**,等下次 read 继续累积
  5. **校验和失败**: 只跳过当前 0xA5,继续从下一个字节搜索（不要清空 buffer,可能错过后面的真帧头）
  6. **msg_len 异常大（如 > 8192）**: 几乎肯定是伪同步头,跳过当前 0xA5
- **源码对应**：`xf_mic_array.py` 第 106-158 行 `_process_buffer()` 的完整实现

**操作步骤**：

1. 用十六进制查看器观察实际帧（先运行 GUI,然后另开终端）:
   ```bash
   sudo cat /dev/ttyACM0 | xxd | head -50
   # 看到大量以 a5 01 04 开头的 16 进制行
   # 找到任意一行,数到第 4-5 字节就是 msg_len（小端）
   ```

2. 手算一个真实帧的校验和（用 Python 验证）:
   ```python
   # 假设观察到一帧: A5 01 04 05 00 01 00 7B 22 41 22 7D 4E
   frame = bytes.fromhex('A5 01 04 05 00 01 00 7B 22 41 22 7D')
   expected = (~sum(frame) + 1) & 0xFF
   actual = 0x4E
   print(f"期望校验: 0x{expected:02X}, 实际校验: 0x{actual:02X}, {'✓' if expected == actual else '✗'}")
   # 验证: 期望=0x4E, 实际=0x4E → 通过
   ```

3. 故意构造一个错误校验和的帧,观察程序如何处理:
   ```python
   import serial, time
   s = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
   # 写一个校验错误的帧（实际不会触发任何业务,但能被 _process_buffer 处理）
   bad_frame = bytes.fromhex('A5 01 04 05 00 01 00 7B 22 41 22 7D FF')  # 校验和故意错
   s.write(bad_frame)
   time.sleep(0.5)
   # 观察终端输出: "校验和错误 got=0xff expected=0x4e，跳过该 0xA5"
   s.close()
   ```

4. 阅读 `_process_buffer` 时重点关注三处容错:
   - 第 121-122 行: 丢弃同步头之前的垃圾
   - 第 133-136 行: msg_len 异常大时跳过当前 0xA5
   - 第 146-149 行: 校验和失败时只跳过当前 0xA5

**易错点**：
- ⚠️ **看到 `丢弃同步头之前的 N 字节`** → 这是正常现象,串口可能残留上次未读完的数据
- ⚠️ **校验和频繁失败** → 检查 USB 线缆质量,或换一根线（电磁干扰会破坏字节）
- ⚠️ **msg_len 显示 0** → 收到的可能是空 payload 的握手响应（0xFF）,正常

---

#### 步骤4：唤醒事件处理与防抖机制（阶段二：能改造，60min）

> 本步骤对应 `xf_mic_array.py` 第 90-96 行 `handle_handshake()`、第 175-213 行 `_handle_frame()` 中 AIUI 事件分支、第 90-97 行 `_handle_frame()` 子类

**知识点讲解**：

**唤醒事件字段提取（1.4.1）**
- **原理**：当 6 麦模块检测到唤醒词,会通过 0x04 消息类型推送 AIUI 事件, payload 是这样的 JSON:
  ```json
  {
    "type": "aiui_event",
    "content": {
      "eventType": 4,
      "info": "{\"ivw\":{\"beam\":2,\"angle\":120.5,\"keyword\":\"xiao3 fei1 tong2 xue2\",\"score\":1850,\"power\":125000,\"start_ms\":1234,\"end_ms\":2567}}"
    }
  }
  ```
  - 注意 `info` 字段是**字符串化的 JSON**,需要 `json.loads` 二次解析
  - 关键字段: `beam`(0~5), `angle`(0~360°), `keyword`(拼音), `score`(0~2000), `power`(0~2,000,000)
- **源码对应**：`xf_mic_array.py` 第 183-194 行

**时间窗口防抖（1.4.2）**
- **原理**：6 麦模块对同一个唤醒词可能短时间内推送多次（噪声、用户重复说、算法回声触发）。直接处理会引发"反复唤醒 → 反复打断 ASR/TTS"的问题。**3 秒防抖**的逻辑:
  ```python
  current_time = time.time()
  if current_time - self.last_wakeup_time > 3.0:  # 3 秒窗口
      # 触发唤醒
      self.last_wakeup_time = current_time
  else:
      # 在窗口内,忽略本次唤醒
      pass
  ```
- **可调参数**: 3 秒是一个折中值,过短会导致重复触发,过长会让用户觉得不灵敏
- **源码对应**：`xf_mic_array.py` 第 196-201 行

**回调与线程锁（1.4.3）**
- **原理**：唤醒事件在 **接收线程** 中产生,但回调函数（如 GUI 更新、ROS2 发布）通常需要在**主线程**执行。这涉及两个并发问题:
  - **同一唤醒被多次处理**: 用 `wakeup_lock` 保护
  - **回调执行时被新唤醒打断**: 锁 + 时间窗口共同保证
- **设计模式**:
  - 用户注册 `wakeup_callback = func`
  - 模块内部在防抖+锁内调用 `self.wakeup_callback()`
  - 子类（如 `XfMicArrayWithEvents`）可重写 `_handle_frame`,在调用父类前预解析 JSON 暂存,父类触发回调时再读出来
- **源码对应**：
  - `xf_mic_array.py` 第 16-18 行 `wakeup_callback`/`wakeup_lock`/`last_wakeup_time` 三件套
  - `xf_mic_array_gui.py` 第 37-97 行 `XfMicArrayWithEvents` 子类

**操作步骤**：

1. 重现防抖效果（用 `--headless` 模式最快）:
   ```bash
   python3 xf_mic_array_gui.py --headless
   # 连续说 3 次"小飞同学",每次间隔 0.5 秒
   # 期望: 终端只打印 1 次 "检测到唤醒! Beam: ..., Angle: ..., Keyword: ..."
   # 3 秒后再说,才会再打印 1 次
   ```

2. 修改防抖窗口为 0.5 秒,观察差异:
   ```python
   # 编辑 xf_mic_array.py 第 198 行
   # if current_time - self.last_wakeup_time > 3.0:  # 改前
   if current_time - self.last_wakeup_time > 0.5:  # 改后
   ```
   ```bash
   python3 xf_mic_array_gui.py --headless
   # 连续说 3 次,现在会打印 2~3 次（0.5 秒后就能再次触发）
   ```
   改回 3.0 秒

3. 用线程模拟并发唤醒,验证锁保护:
   ```python
   import threading, time
   from xf_mic_array import XfMicArray
   
   triggered = []
   comm = XfMicArray(port='/dev/ttyACM0')
   comm.wakeup_callback = lambda: triggered.append(time.time())
   comm.start()
   
   # 启动 5 个线程,每个尝试触发回调 10 次
   def stress():
       for _ in range(10):
           comm.wakeup_callback()  # 直接调用,模拟异常并发
           time.sleep(0.1)
   
   threads = [threading.Thread(target=stress) for _ in range(5)]
   for t in threads: t.start()
   for t in threads: t.join()
   
   # 期望: 50 次调用中,只有 1 次真正进入回调（因为防抖 3 秒）
   # 实际上 5 个线程在 0~1 秒内并发调用,只有 1 次能通过 3 秒窗口
   print(f"实际触发次数: {len(triggered)}")  # 应该是 1
   comm.stop()
   ```

4. 阅读 `XfMicArrayWithEvents` 子类（`xf_mic_array_gui.py` 第 37-97 行）,理解:
   - 如何在**不修改父类**的前提下,通过继承重写 `_handle_frame` 来获取完整事件字段
   - `_pending_event` 暂存字段 → 父类回调 → 读出字段 → 传给用户的 `event_callback`
   - 这是**模板方法模式**的典型应用

**易错点**：
- ⚠️ **回调里做耗时操作导致接收线程卡顿** → **解决**：回调里只做"快速转发"（塞 queue）,真正的工作在主线程做
- ⚠️ **防抖 3 秒太长** → **解决**：可在子类化时改为实例变量,通过参数传入
- ⚠️ **多个回调都被触发** → 检查 `_pending_event` 是否被多线程读写（应仅接收线程写）

---

#### 步骤5：GUI 可视化定制（阶段三：能改造，30min）

> 本步骤对应 `xf_mic_array_gui.py` 第 100-318 行 `XfMicArrayGUI` 类

**知识点讲解**：

**Tkinter Canvas 基础（1.5.1）**
- **原理**：Tkinter 是 Python 内置的 GUI 库,`Canvas` 组件提供画布,常用方法:
  - `create_oval(x1, y1, x2, y2, ...)` 画圆/椭圆
  - `create_line(x1, y1, x2, y2, ...)` 画线
  - `create_text(x, y, text=...)` 写字
  - `itemconfig(item, **kwargs)` 动态修改（颜色、文本）
  - `delete(tag)` 删除指定 tag 的所有元素
- **坐标系**: 原点在左上角,Y 轴**向下**增加(与数学相反),这在画环形阵列时需要小心

**环形阵列绘制（1.5.2）**
- **原理**：6 个麦克风均布在半径 140 像素的圆上,**0° 在正下方**,顺时针每 60° 一个:
  ```python
  for i in range(6):
      theta = math.radians(90 - i * 60)  # 90° 是因为 Y 轴向下
      x = cx + r * math.cos(theta)
      y = cy + r * math.sin(theta)
      # i=0: 0° (正下方)  → x=cx, y=cy+r
      # i=1: 60° (右)    → x=cx+r*0.866, y=cy+r*0.5
      # ...
  ```
  - 关键技巧: `90 - i * 60` 是因为数学的 0° 在 X 正方向,而我们要 0° 在 Y 正方向(下方)
- **箭头绘制**: 同样用极坐标换算,从中心 (cx, cy) 画到目标方向

**线程安全事件刷新（1.5.3）**
- **原理**：Tkinter **只能在主线程**更新 UI,但唤醒事件在接收线程产生。解决方案是经典的"生产者-消费者"模式:
  ```python
  # 接收线程: 收到事件就塞进 queue
  def _enqueue_event(self, event):
      self.event_queue.put(event)
  
  # 主线程: 每 50ms 轮询 queue,有事件就处理
  def _poll_queue(self):
      try:
          while True:
              event = self.event_queue.get_nowait()
              self._handle_event(event)  # 真正的 UI 更新
      except queue.Empty:
          pass
      self.root.after(50, self._poll_queue)  # 50ms 后再轮询
  ```
- **为什么是 50ms**: 太快浪费 CPU(20Hz 轮询),太慢会感觉卡顿,50ms = 20Hz 是 GUI 常用频率
- **源码对应**：`xf_mic_array_gui.py` 第 110-126, 264-298 行

**操作步骤**：

1. 修改 PINYIN_MAP,加入自定义唤醒词:
   ```python
   # 编辑 xf_mic_array_gui.py 第 29-34 行
   PINYIN_MAP = {
       'xiao3 fei1 tong2 xue2': '小飞同学',
       'ni3 hao3 xiao3 fei1': '你好小飞',
       'xiao3 fei1 xiao3 fei1': '小飞小飞',
       'zhi1 ma2 kai1 men2': '芝麻开门',
       'ke1 ji4 da4 xue2': '科技大学',  # 新增
       'ni3 zai4 na3 li3': '你在哪里',  # 新增
   }
   ```
   重新运行 GUI,说新词验证显示

2. 改变画布颜色（演示 Canvas 实时修改）:
   ```python
   # 编辑 xf_mic_array_gui.py 第 217 行
   c.create_oval(cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30,
                 outline='#e74c3c', width=2)  # 改 dfe6e9 → e74c3c（红）
   # 外圈变红
   ```

3. 添加分数告警（score < 500 时高亮）:
   ```python
   # 编辑 _handle_event,加入:
   if score < 500:
       self.score_bar.configure(style='red.Horizontal.TProgressbar')
   else:
       self.score_bar.configure(style='blue.Horizontal.TProgressbar')
   ```

4. 观察 `_poll_queue` 的轮询频率:
   ```python
   # 在 _poll_queue 头部加入:
   print(f"poll at {time.time():.3f}")
   ```
   重新运行,会看到每 50ms 打印一次（即使没有新事件）

5. 用 `top` 命令观察 CPU 占用:
   ```bash
   # 另开终端
   top -p $(pgrep -f xf_mic_array_gui)
   # 期望: 常驻监听 CPU < 5% 单核
   ```

**易错点**：
- ⚠️ **GUI 启动报 "no display"** → **解决**：用 X forwarding（`ssh -X`）或 `xvfb-run python3 xf_mic_array_gui.py`
- ⚠️ **Canvas 元素不更新** → **解决**：必须用 `itemconfig` / `coords`,直接改 Python 变量不会重绘
- ⚠️ **Tkinter 线程报错 "main thread is not in main loop"** → **解决**：所有 UI 更新必须通过 queue + after 转发

---

#### 完整可运行代码 demo_mic_array.py

> 完整可独立运行的最小演示,串联三步骤的核心逻辑

```python
# -*- coding: utf-8 -*-
"""
实验1 demo：讯飞六麦阵列的串口通信与唤醒事件
平台：B2 / C1
运行：python3 demo_mic_array.py
按键：Ctrl+C 退出
"""
import time
import threading
import serial
import serial.tools.list_ports


def find_xf_mic_array(vid=0x1a86, pid=0x55d4):
    """通过 VID/PID 查找六麦阵列串口（对应 uart_device.find_device）"""
    target = f"{vid:04x}:{pid:04x}"
    for p in serial.tools.list_ports.comports():
        if target.lower() in p.hwid.lower():
            return p.device
    return None


def parse_aiui_frame(data):
    """从字节流解析一个完整 AIUI 帧（对应 xf_mic_array._process_buffer）"""
    HEADER = 7
    sync_idx = data.find(0xA5)
    if sync_idx < 0 or len(data) < sync_idx + HEADER:
        return None, data[sync_idx + 1:] if sync_idx >= 0 else data
    start = sync_idx
    msg_type = data[start + 2]
    msg_len = data[start + 3] | (data[start + 4] << 8)  # 小端
    total = HEADER + msg_len + 1
    if len(data) < start + total:
        return None, data[start:]  # 帧不完整
    frame = data[start:start + total]
    expected = (~sum(frame[:-1]) + 1) & 0xFF
    if frame[-1] != expected:
        return None, data[start + 1:]  # 校验失败,跳过当前 0xA5
    payload = frame[HEADER:HEADER + msg_len]
    return {
        'type': msg_type,
        'id': data[start + 5] | (data[start + 6] << 8),
        'payload': payload,
    }, data[start + total:]


def main():
    # 1. 串口识别（知识点 1.1.3）
    port = find_xf_mic_array()
    if not port:
        print("未找到六麦阵列 (1a86:55d4)")
        return
    print(f"[OK] 找到设备: {port}")

    # 2. 打开串口（知识点 1.1.2）
    ser = serial.Serial(port, baudrate=115200, timeout=1)
    print(f"[OK] 串口已打开: 115200 8N1")

    # 3. 读取并解析帧（知识点 1.1.3 帧解析）
    rx_buffer = bytearray()
    last_wakeup = 0
    print("[INFO] 等待唤醒事件,说 '小飞同学' 试试 (Ctrl+C 退出)...")

    try:
        while True:
            data = ser.read(128)
            if data:
                rx_buffer.extend(data)
                # 持续拆帧
                while True:
                    frame, rx_buffer = parse_aiui_frame(bytes(rx_buffer))
                    if frame is None:
                        break
                    # 4. 唤醒事件处理（知识点 1.1.4）
                    if frame['type'] == 0x04:
                        try:
                            import json
                            msg = json.loads(frame['payload'])
                            if msg.get('type') == 'aiui_event':
                                info = json.loads(msg['content'].get('info', '{}'))
                                ivw = info.get('ivw', {})
                                if ivw:
                                    now = time.time()
                                    # 3 秒防抖
                                    if now - last_wakeup > 3.0:
                                        last_wakeup = now
                                        print(f"[WAKE] beam={ivw.get('beam')} "
                                              f"angle={ivw.get('angle', 0):.1f}° "
                                              f"kw={ivw.get('keyword')} "
                                              f"score={ivw.get('score', 0):.0f}")
                        except Exception as e:
                            print(f"解析失败: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        print("\n[BYE] 串口已关闭")


if __name__ == "__main__":
    main()
```

### 1.7 注意事项

- ⚠️ **USB 串口权限** → 普通用户需 `sudo chmod 666 /dev/ttyACM0` 或加入 `dialout` 用户组
- ⚠️ **校验和失败频繁** → 检查 USB 线缆质量；过长（>3m）易受电磁干扰
- ⚠️ **GUI 启动报 no display** → 远程环境用 `xvfb-run` 或 `ssh -X`；本地无显示器用 `--headless`
- ⚠️ **唤醒频繁触发** → 防抖窗口 3 秒可调,过短(<1s) 会误触,过长(>10s) 会漏触发
- ⚠️ **6 麦模块供电不足** → USB 2.0 端口供电可能不足,优先用 USB 3.0 或带外接电源的 HUB
- ⚠️ **Python 2/3 兼容** → 本实验代码仅支持 Python 3.10+,因 `def __init__(self, *args, event_callback=None, **kwargs)` 用了 PEP 3102 关键字-only 语法

### 1.8 实验总结

**完成成果**:
- 掌握串口通信基础概念（UART/波特率/设备文件）
- 掌握 pyserial 库 open/read/write/close 调用
- 掌握 VID/PID 自动识别 USB 设备
- 理解 6 麦环形阵列的声源定位原理（beam/angle）
- 掌握 AIUI 协议帧结构（sync/type/len/id/payload/checksum）
- 理解双缓冲拆帧 + 校验和容错的工业实践
- 掌握 3 秒时间窗 + Lock 唤醒防抖机制
- 跑通 xf_mic_array_gui.py,扩展 PINYIN_MAP 加入自定义唤醒词

**技能收获**:
- 能够独立排查串口通信问题（权限/线缆/波特率）
- 能够从 16 进制字节流反推协议帧结构
- 能够用 Tkinter Canvas 绘制极坐标图形
- 能够用 queue + after 实现线程安全的事件刷新
- 理解嵌入式设备通信的典型模式（同步头+校验+payload）

**常见问题与解决**:

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| Permission denied | 普通用户无串口权限 | `sudo chmod 666 /dev/ttyACM0` |
| 找不到设备 (1a86:55d4) | USB 未插紧 / 驱动异常 | 重新插拔,`dmesg \| tail` 查看 |
| read() 一直空 | 波特率不匹配 | 确认使用 115200 |
| 唤醒无反应 | 唤醒词不在 PINYIN_MAP | 添加映射或检查模块固件 |
| GUI 报 no display | 无 X server | 用 `--headless` 或 `xvfb-run` |
| 校验和频繁失败 | 线缆干扰/过长 | 换短一点的 USB 线 |
| CPU 占用 > 30% | 轮询频率过高 | 调整 after 间隔到 100ms |

### 1.9 实验报告要求

**思考题**:
1. 串口通信为什么需要"起始位"和"停止位"？如果去掉会发生什么？
2. 为什么 AIUI 协议用小端序而不是大端序？这与 PC 的 CPU 架构有什么关系？
3. 6 麦环形阵列的"波束形成"算法是怎么从 6 路麦克风信号反推声源方向的？请用到达时间差(TDOA)原理解释。
4. 3 秒防抖窗口如果改成 0.1 秒会怎样？如果改成 30 秒又会怎样？各举一个应用场景。
5. 校验和 `(~sum + 1) & 0xFF` 为什么能检测出大部分传输错误？什么情况下它检测不出？

**评分标准**: 串口通信基础 15 分 + pyserial 调用 15 分 + AIUI 帧解析 25 分 + 唤醒防抖 15 分 + GUI 定制 20 分 + 实验报告 10 分 = 100 分。
