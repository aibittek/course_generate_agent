#!/usr/bin/env python3
"""
增量更新功能快速验证脚本
用于测试文档定位、替换、版本更新等核心功能
"""

import sys
from pathlib import Path

# 添加 skill 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from document_replacer import DocumentReplacer


def test_locate_experiment():
    """测试实验定位功能"""
    print("\n" + "="*50)
    print("测试1: 实验定位功能")
    print("="*50)

    # 创建测试文档
    test_doc = """# 测试课程 实验指导书

## 实验1 基础实验

内容1...

## 实验2 进阶实验

内容2...

## 实验3 综合实验

内容3...

## 附录

附录内容...
"""

    test_path = Path("test_lab_guide.md")
    test_path.write_text(test_doc, encoding='utf-8')

    try:
        replacer = DocumentReplacer(str(test_path))

        # 测试定位实验2
        boundary = replacer.locate_experiment(2)
        if boundary:
            print(f"✅ 定位成功: {boundary.title}")
            print(f"   起始行: {boundary.start_line}")
            print(f"   结束行: {boundary.end_line}")
            content = ''.join(replacer.lines[boundary.start_line:boundary.end_line])
            print(f"   内容预览:\n{content[:100]}...")
        else:
            print("❌ 定位失败")

        # 测试定位不存在的实验
        boundary = replacer.locate_experiment(99)
        if boundary is None:
            print("✅ 正确识别不存在的实验")
        else:
            print("❌ 错误识别了不存在的实验")

    finally:
        test_path.unlink()


def test_locate_chapter():
    """测试章节定位功能"""
    print("\n" + "="*50)
    print("测试2: 章节定位功能")
    print("="*50)

    test_doc = """# 测试课程 知识图谱

## 第1章 基础知识

### 1.1 概念

内容...

## 第2章 进阶知识

### 2.1 原理

内容...

## 第3章 应用

### 3.1 实践

内容...
"""

    test_path = Path("test_knowledge_graph.md")
    test_path.write_text(test_doc, encoding='utf-8')

    try:
        replacer = DocumentReplacer(str(test_path))

        boundary = replacer.locate_chapter(2)
        if boundary:
            print(f"✅ 定位成功: {boundary.title}")
            print(f"   起始行: {boundary.start_line}")
            print(f"   结束行: {boundary.end_line}")
        else:
            print("❌ 定位失败")

    finally:
        test_path.unlink()


def test_replace_section():
    """测试内容替换功能"""
    print("\n" + "="*50)
    print("测试3: 内容替换功能")
    print("="*50)

    test_doc = """# 测试课程

## 实验1 旧内容

这是旧的实验1内容。

## 实验2 保持不变

这是实验2内容。
"""

    new_content = """## 实验1 新内容

这是新的实验1内容。
包含更多细节。
"""

    test_path = Path("test_replace.md")
    test_path.write_text(test_doc, encoding='utf-8')

    try:
        replacer = DocumentReplacer(str(test_path))
        boundary = replacer.locate_experiment(1)

        if boundary:
            replacer.replace_section(boundary, new_content)
            replacer.save_document(backup=False)

            # 验证替换结果
            updated_content = test_path.read_text(encoding='utf-8')
            if "新的实验1内容" in updated_content and "旧的实验1内容" not in updated_content:
                print("✅ 内容替换成功")
                print(f"   更新后内容:\n{updated_content}")
            else:
                print("❌ 内容替换失败")
        else:
            print("❌ 定位失败")

    finally:
        test_path.unlink()
        backup_path = test_path.with_suffix('.md.bak')
        if backup_path.exists():
            backup_path.unlink()


def test_version_update():
    """测试版本号更新功能"""
    print("\n" + "="*50)
    print("测试4: 版本号更新功能")
    print("="*50)

    test_doc = """---
title: 测试课程
version: v0.2
---

# 测试课程

> 版本: v0.2
> 更新日期: 2026-06-22

## 内容

...
"""

    test_path = Path("test_version.md")
    test_path.write_text(test_doc, encoding='utf-8')

    try:
        replacer = DocumentReplacer(str(test_path))
        old_ver, new_ver = replacer.update_version('minor')

        if old_ver == "v0.2" and new_ver == "v0.3":
            print("✅ 版本更新成功")
            print(f"   {old_ver} → {new_ver}")

            # 验证两处版本号都更新了
            content = ''.join(replacer.lines)
            if content.count("v0.3") == 2 and content.count("v0.2") == 0:
                print("✅ 所有版本号都已更新")
            else:
                print("⚠️ 部分版本号未更新")
        else:
            print("❌ 版本更新失败")

    finally:
        test_path.unlink()


def test_changelog_append():
    """测试更新日志追加功能"""
    print("\n" + "="*50)
    print("测试5: 更新日志追加功能")
    print("="*50)

    test_doc = """# 测试课程

## 更新日志
| 版本 | 日期 | 更新内容 | 更新人 |
|------|------|---------|-------|
| v0.1 | 2026-06-21 | 初始版本 | Agent |
"""

    test_path = Path("test_changelog.md")
    test_path.write_text(test_doc, encoding='utf-8')

    try:
        replacer = DocumentReplacer(str(test_path))
        replacer.append_changelog("v0.2", "更新实验3")

        content = ''.join(replacer.lines)
        if "v0.2" in content and "更新实验3" in content:
            print("✅ 更新日志追加成功")
            print(f"   新日志:\n{content}")
        else:
            print("❌ 更新日志追加失败")

    finally:
        test_path.unlink()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*50)
    print("开始增量更新功能验证")
    print("="*50)

    tests = [
        test_locate_experiment,
        test_locate_chapter,
        test_replace_section,
        test_version_update,
        test_changelog_append,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            failed += 1

    print("\n" + "="*50)
    print("测试结果")
    print("="*50)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"总计: {passed + failed}")

    if failed == 0:
        print("\n[SUCCESS] 所有测试通过！增量更新功能就绪。")
        return 0
    else:
        print("\n[WARNING] 部分测试失败，请检查。")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
