# 单实验生成测试

本文档用于测试从工作流中单独生成某一个实验的指导书章节。

---

## 测试目标

验证以下能力：
1. ✅ 根据实验ID，生成单个实验的完整指导书（9个章节）
2. ✅ 基于源码分析报告生成（原理→源码位置对应）
3. ✅ 生成的内容符合质量标准

---

## 测试实验

- **课程**：`cv_practice`（计算机视觉实践）
- **实验编号**：exp06
- **实验名称**：基于MediaPipe的人机交互实验
- **学时**：4小时

---

## 已准备好的输入

### 1. 课程规格
路径：`courses/sheet1/cv_practice/_meta/course-spec.yaml`

```yaml
- id: exp06
  name: 基于MediaPipe的人机交互实验
  hours: 4
  content: |
    【实验目标】掌握MediaPipe框架的多任务检测能力；能够实现人脸、手部、姿态的实时关键点检测与交互控制。
    【实验内容】1. 调用MediaPipe预训练模型完成人脸检测、手部检测、人体姿态检测的实时推理；2. 提取关键点坐标并计算手势特征；3. 基于检测结果设计交互逻辑；4. 实现低延迟、轻量级的实时人机交互系统。
```

### 2. 源码分析报告
路径：`courses/sheet1/cv_practice/source-codes/exp06/code-analysis/code-analysis-report.md`

包含：
- 代码架构（文件结构、核心模块、数据流）
- 原理分析（MediaPipe Hands原理、状态机原理）
- 学习步骤（能运行→能理解→能改造）
- 易错点清单（5个常见错误）
- 源码素材清单

### 3. 源码分析状态
路径：`courses/sheet1/cv_practice/source-codes/exp06/code-analysis/analysis-status.yaml`

```yaml
analysis_status: completed  # ✅ HOOK已通过
```

### 4. 硬件平台规格
路径：`.claude/memory/hardware-platform-spec.md`

主要配置：
- 具身智能实验箱B2 / 具身智能机器人小车C1
- RK3576（6TOPS NPU）
- 结构光深度相机、激光雷达
- Ubuntu 22.04 + Python 3.10

---

## 手动执行命令

### Step 1：确认HOOK通过

```powershell
powershell -File .claude/hooks/enforce-source-hook.ps1 -AgentName "LabGuideExperimentAgent" -ExperimentId "6"
```

预期输出：
```
[PASS] Experiment 6 analysis completed
退出码: 0
```

### Step 2：执行生成

以下是需要传给 `LabGuideExperimentAgent` 的完整Prompt：

```
请基于以下信息，为实验6生成完整的实验指导书内容。

## 实验信息

```yaml
id: exp06
name: 基于MediaPipe的人机交互实验
hours: 4
content: |
  【实验目标】掌握MediaPipe框架的多任务检测能力；能够实现人脸、手部、姿态的实时关键点检测与交互控制。
  【实验内容】1. 调用MediaPipe预训练模型完成人脸检测、手部检测、人体姿态检测的实时推理；2. 提取关键点坐标并计算手势特征；3. 基于检测结果设计交互逻辑；4. 实现低延迟、轻量级的实时人机交互系统。
```

## 源码分析报告

路径：`courses/sheet1/cv_practice/source-codes/exp06/code-analysis/code-analysis-report.md`

关键内容摘要：

### 核心原理
1. **MediaPipe Hands原理**：21个关键点(x,y,z)回归，坐标归一化到[0,1]
   - 关键公式：`distance = sqrt((x2-x1)^2 + (y2-y1)^2 + (z2-z1)^2)`
   - 源码位置：`demo_mediapipe.py L30-35`（calculate_palm_distance函数）

2. **交互状态机原理**：基于距离的三状态切换
   - IDLE → PINCH: distance < threshold (0.1)
   - PINCH → RELEASE: distance > threshold * 1.5
   - 源码位置：`demo_mediapipe.py L50-70`（InteractionStateMachine类）

### 学习步骤
- 阶段一（能运行）：摄像头初始化→运行demo→看到关键点（30分钟）
- 阶段二（能理解）：21点编号→掌心距离计算→状态机原理（60分钟）
- 阶段三（能改造）：改造手势识别逻辑（30分钟）

### 易错点
| 错误 | 原因 | 解决方法 |
|------|------|---------|
| 关键点不显示 | 置信度过高 | 降低MIN_CONFIDENCE从0.8到0.5 |
| 内存持续增长 | MediaPipe实例未复用 | 使用with语句 |
| 坐标范围误用 | 以为是像素值 | 打印landmark[0].x确认范围 |

### 源码素材清单
| 素材 | 位置 |
|------|------|
| 摄像头初始化 | demo_mediapipe.py L156-165 |
| Hands初始化 | HandsTracker.__init__ |
| 关键点绘制 | draw_landmarks函数 |
| 掌心距离计算 | calculate_palm_distance L30-35 |
| 状态机 | InteractionStateMachine L50-70 |
| 主循环 | main() L156-end |

## 输出要求

1. 生成完整的9个章节：
   - 关联知识点
   - 实验目标
   - 实验环境
   - 实验难度
   - 实验现象
   - 实验步骤
   - 注意事项
   - 实验总结
   - 实验报告要求

2. **强制要求**：
   - 每个原理讲解必须引用源码位置（文件名+行号）
   - 原理讲解必须包含：是什么+为什么+怎么用
   - 易错点必须引用common_mistakes清单
   - 学习步骤必须遵循三阶段规划

3. 输出文件：
   `courses/sheet1/cv_practice/_parts/experiment-06.md`
```

---

## 预期结果

- ✅ 源码分析HOOK通过（退出码0）
- ✅ 生成完整9个章节（≥200行）
- ✅ 原理讲解引用源码位置
- ✅ 易错点覆盖5个清单项
- ✅ 学习步骤遵循三阶段

---

## 验证方法

生成完成后，执行以下检查：

```powershell
# 1. 检查文件是否存在
Test-Path "courses/sheet1/cv_practice/_parts/experiment-06.md"

# 2. 检查行数（应≥200）
(Get-Content "courses/sheet1/cv_practice/_parts/experiment-06.md").Count

# 3. 检查是否引用了源码位置
Select-String -Path "courses/sheet1/cv_practice/_parts/experiment-06.md" -Pattern "L\d+-\d+" | Measure-Object

# 4. 检查是否覆盖了所有9个章节
Select-String -Path "courses/sheet1/cv_practice/_parts/experiment-06.md" -Pattern "^## " | Select-Object -First 9
```
