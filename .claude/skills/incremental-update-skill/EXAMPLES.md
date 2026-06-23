# 增量更新使用示例

本文档提供增量更新功能的详细使用示例和测试场景。

---

## 场景1: 实验源码修改后重新生成

### 背景
EXP001（计算机视觉实践）的实验5源码已更新，使用了新的YOLOv8 API，需要重新生成实验指导内容。

### 操作步骤

#### 步骤1: 准备源码
```bash
# 源码路径
courses/sheet1/cv_practice/source-codes/exp05/
├── demo_yolo.py          # 已修改
├── utils/
│   └── detector.py       # 已修改
└── requirements.txt
```

#### 步骤2: 触发增量更新
```
指令: 更新 EXP001 实验5
```

Claude Code 会：
1. 检查 `source-codes/exp05/code-analysis/analysis-status.yaml`
2. 发现 `analysis_status: pending`，触发 `SourceCodeAnalysisAgent`
3. 分析完成后，调用 `LabGuideExperimentAgent` 生成新内容
4. 定位 `cv_practice_lab_guide.md` 中实验5的位置
5. 替换内容
6. 更新版本号 v0.2 → v0.3
7. 检查一致性

#### 步骤3: 验证结果
```bash
# 检查生成的文件
cat courses/sheet1/cv_practice/_parts/experiment-5.md

# 检查更新后的 lab_guide.md
git diff courses/sheet1/cv_practice/cv_practice_lab_guide.md

# 检查备份
ls courses/sheet1/cv_practice/cv_practice_lab_guide.md.bak
```

#### 预期输出
```yaml
✅ 增量更新完成

更新摘要:
  课程: EXP001 (计算机视觉实践)
  类型: 实验更新
  目标: 实验5 - YOLOv8目标检测实验
  
  执行流程:
    1. ✅ 源码分析完成 (exp05)
    2. ✅ 实验内容生成完成
    3. ✅ 文档定位成功 (L301-L450)
    4. ✅ 内容替换完成
    5. ✅ 版本更新 (v0.2 → v0.3)
    6. ✅ 一致性检查通过
  
  变更文件:
    - cv_practice_lab_guide.md (v0.2 → v0.3)
      替换范围: L301-L450
      备份路径: cv_practice_lab_guide.md.bak
    
  一致性检查:
    ✅ 学时总和: 52h (一致)
    ✅ 实验数量: 14个 (一致)
    ✅ 知识点引用: 正常
  
  建议操作:
    ⚠️ quiz.md 中有2道编程题引用了实验5，请检查是否需要更新:
       - 题目32: YOLOv8模型推理
       - 题目34: 目标检测结果可视化
```

---

## 场景2: 实验学时调整

### 背景
实验3原定4学时，根据实际教学反馈调整为6学时。

### 操作步骤

#### 步骤1: 修改 course-spec.yaml
```yaml
experiments:
  - id: 3
    name: "特征提取与匹配实验"
    hours: 6  # 原来是 4
    objectives: [...]
```

#### 步骤2: 触发增量更新
```
指令: 更新 EXP001 实验3，学时调整为6h
```

Claude Code 会：
1. 重新生成实验3内容（如需要）
2. 更新 `lab_guide.md` 中实验3的学时标注
3. 同步更新 `syllabus.md` 的学时分配表
4. 检查总学时是否一致（52h → 54h）

#### 步骤3: 检查连锁影响
```bash
# 检查总学时
grep "总学时" courses/sheet1/cv_practice/*.md

# 检查大纲中的学时分配
grep -A 20 "学时分配" courses/sheet1/cv_practice/cv_practice_syllabus.md
```

#### 预期输出
```yaml
✅ 增量更新完成

更新摘要:
  课程: EXP001
  类型: 实验学时调整
  目标: 实验3
  
  变更:
    - course-spec.yaml: 实验3学时 4h → 6h
    - lab_guide.md: 更新实验3学时标注
    - syllabus.md: 更新学时分配表
  
  一致性检查:
    ⚠️ 总学时变化: 52h → 54h
       需要同步更新:
       - knowledge_graph.md 的总学时标注
       - README.md 的课程信息
    
  建议操作:
    1. 确认总学时变化是否合理
    2. 更新所有文档的总学时标注
    3. 通知教学管理部门学时变更
```

---

## 场景3: 章节知识点补充

### 背景
EXP003（ROS机器人实践）第2章需要补充"ROS2 DDS通信原理"知识点。

### 操作步骤

#### 步骤1: 触发增量更新
```
指令: 修改 EXP003 第2章，补充 DDS 通信原理
```

#### 步骤2: Agent 执行
Claude Code 会：
1. 调用 `KnowledgeGraphAgent`（增量模式）
2. 在第2章插入新知识点 2.3.5（假设2.3.4是最后一个）
3. 更新 `knowledge_graph.md`
4. 检查关联的实验和题目
5. 提示用户同步更新

#### 预期输出
```yaml
✅ 增量更新完成

更新摘要:
  课程: EXP003
  类型: 章节知识点补充
  目标: 第2章 - ROS2通信机制
  
  新增知识点:
    - 2.3.5 DDS通信原理
      类型: 原理
      描述: 理解ROS2底层DDS通信协议的工作机制
      难度: 理解
  
  变更文件:
    - ros_practice_knowledge_graph.md (v0.3 → v0.4)
  
  影响分析:
    ⚠️ 建议同步更新:
       - 实验2: ROS2话题通信实验（可补充DDS原理讲解）
       - 实验3: ROS2服务通信实验（可补充DDS原理讲解）
       - quiz.md: 可新增相关选择题
```

---

## 场景4: 修正实验内容错误

### 背景
发现实验7的步骤3中，代码示例使用了错误的API（ROS1的 `rospy.Subscriber` 而非ROS2的 `create_subscription`）。

### 操作步骤

#### 步骤1: 触发增量更新
```
指令: 更新 EXP003 实验7，修正步骤3的API错误
```

#### 步骤2: 手动修改（如需要）
如果错误较小，可以：
```bash
# 使用文档替换工具
python .claude/skills/incremental-update-skill/document_replacer.py \
  courses/sheet1/ros_practice/ros_practice_lab_guide.md \
  experiment 7 \
  corrected_exp7_step3.md
```

#### 步骤3: 验证修复
```bash
# 检查修正后的内容
grep -A 10 "create_subscription" courses/sheet1/ros_practice/ros_practice_lab_guide.md
```

---

## 场景5: 批量更新多个实验

### 背景
实验2、3、4的源码都做了API升级，需要批量重新生成。

### 操作步骤

#### 方法1: 逐个更新（推荐）
```
更新 EXP001 实验2
更新 EXP001 实验3
更新 EXP001 实验4
```

#### 方法2: 批量命令（需要脚本支持）
```bash
for exp_id in 2 3 4; do
  echo "更新实验 $exp_id"
  # 触发增量更新...
done
```

---

## 使用 Python 工具进行文档替换

### 示例: 替换实验5

```bash
# 1. 生成新内容
# （由 LabGuideExperimentAgent 生成到 _parts/experiment-5.md）

# 2. 使用工具替换
python .claude/skills/incremental-update-skill/document_replacer.py \
  courses/sheet1/cv_practice/cv_practice_lab_guide.md \
  experiment \
  5 \
  courses/sheet1/cv_practice/_parts/experiment-5.md

# 输出:
# ✅ 定位成功: ## 实验5 YOLOv8目标检测实验
#    范围: L301-L450
# ✅ 已替换: ## 实验5 YOLOv8目标检测实验
#    范围: L301-L450
#    新内容: 8563 字符
# ✅ 版本更新: v0.2 → v0.3
# ✅ 已追加更新日志: v0.3 - 更新experiment 5
# ✅ 备份已保存: cv_practice_lab_guide.md.bak
# ✅ 文档已更新: cv_practice_lab_guide.md
```

### 示例: 替换章节

```bash
python .claude/skills/incremental-update-skill/document_replacer.py \
  courses/sheet1/cv_practice/cv_practice_knowledge_graph.md \
  chapter \
  2 \
  new_chapter2.md
```

---

## 测试清单

### 功能测试

- [ ] 单实验更新（有源码分析）
- [ ] 单实验更新（无源码分析，需触发分析）
- [ ] 单章节更新
- [ ] 单节更新
- [ ] 知识点微调
- [ ] 学时调整 + 连锁更新
- [ ] 版本号自动更新
- [ ] 更新日志自动追加
- [ ] 备份文件生成

### 边界测试

- [ ] 实验编号不存在
- [ ] 章节编号不存在
- [ ] 文档格式不规范
- [ ] 源码分析失败
- [ ] 学时总和不一致
- [ ] 知识点引用冲突

### 一致性测试

- [ ] 学时总和检查
- [ ] 实验数量检查
- [ ] 知识点编号唯一性
- [ ] 知识点引用完整性
- [ ] 题目关联检查

---

## 故障排查

### 问题1: 实验边界未找到

**错误信息**:
```
❌ 未找到: experiment 5
```

**原因**:
- 文档中没有 "## 实验5" 标记
- 标题格式不标准（如 "##实验5" 缺少空格）
- 实验编号不连续

**解决**:
```bash
# 检查文档结构
grep "## 实验" courses/sheet1/cv_practice/cv_practice_lab_guide.md

# 修正标题格式
```

### 问题2: 源码分析超时

**错误信息**:
```
❌ 源码分析超时
```

**原因**:
- 源码文件过大
- 源码包含语法错误
- 源码路径不正确

**解决**:
```bash
# 检查源码路径
ls -la courses/sheet1/cv_practice/source-codes/exp05/

# 手动触发分析
# (调用 SourceCodeAnalysisAgent)
```

### 问题3: 一致性检查失败

**错误信息**:
```
❌ 学时总和不一致: 52h (期望) vs 54h (实际)
```

**原因**:
- 修改了某个实验的学时但未同步更新总学时
- 学时分配表计算错误

**解决**:
```bash
# 检查所有实验的学时
grep "学时:" courses/sheet1/cv_practice/cv_practice_lab_guide.md

# 重新计算总和
# 同步更新 course-spec.yaml, syllabus.md, knowledge_graph.md
```

---

## 最佳实践

### 1. 更新前备份
```bash
# 手动备份
cp courses/sheet1/cv_practice/cv_practice_lab_guide.md \
   courses/sheet1/cv_practice/cv_practice_lab_guide.md.backup
```

### 2. 小步迭代
- 每次只更新一个实验或章节
- 更新后立即验证
- 确认无误后再继续下一个

### 3. 使用版本控制
```bash
# 每次更新后提交
git add courses/sheet1/cv_practice/
git commit -m "更新实验5: YOLOv8 API升级"
```

### 4. 定期全量验证
```bash
# 每5次增量更新后，运行全量检查
# (调用 ContentAuditAgent)
```

---

## 更新日志

| 日期 | 更新内容 |
|------|---------|
| 2026-06-22 | 初始版本，包含5个场景示例 |
