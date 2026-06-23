#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量更新功能快速验证脚本（无emoji版本，兼容Windows GBK）
"""

import sys
import os
from pathlib import Path

# 设置UTF-8输出（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from document_replacer import DocumentReplacer


def test_locate_experiment():
    """测试实验定位功能"""
    print("\n" + "="*50)
    print("Test 1: Locate Experiment")
    print("="*50)

    test_doc = """# Test Course Lab Guide

## 实验1 Basic

Content 1...

## 实验2 Advanced

Content 2...

## 实验3 Comprehensive

Content 3...

## 附录

Appendix...
"""

    test_path = Path("test_lab_guide.md")
    test_path.write_text(test_doc, encoding='utf-8')

    try:
        replacer = DocumentReplacer(str(test_path))
        boundary = replacer.locate_experiment(2)

        if boundary:
            print(f"[PASS] Located: {boundary.title}")
            print(f"       Start: {boundary.start_line}, End: {boundary.end_line}")
            return True
        else:
            print("[FAIL] Not located")
            return False
    finally:
        if test_path.exists():
            test_path.unlink()


def test_locate_chapter():
    """测试章节定位功能"""
    print("\n" + "="*50)
    print("Test 2: Locate Chapter")
    print("="*50)

    test_doc = """# Knowledge Graph

## 第1章 Foundation

### 1.1 Concept

...

## 第2章 Advanced

### 2.1 Principle

...
"""

    test_path = Path("test_kg.md")
    test_path.write_text(test_doc, encoding='utf-8')

    try:
        replacer = DocumentReplacer(str(test_path))
        boundary = replacer.locate_chapter(2)

        if boundary:
            print(f"[PASS] Located: {boundary.title}")
            return True
        else:
            print("[FAIL] Not located")
            return False
    finally:
        if test_path.exists():
            test_path.unlink()


def test_replace_section():
    """测试内容替换功能"""
    print("\n" + "="*50)
    print("Test 3: Replace Section")
    print("="*50)

    test_doc = """# Test

## 实验1 Old Content

Old text...

## 实验2 Keep

Keep this...
"""

    new_content = """## 实验1 New Content

New text...
"""

    test_path = Path("test_replace.md")
    test_path.write_text(test_doc, encoding='utf-8')

    try:
        replacer = DocumentReplacer(str(test_path))
        boundary = replacer.locate_experiment(1)

        if boundary:
            replacer.replace_section(boundary, new_content)
            replacer.save_document(backup=False)

            updated = test_path.read_text(encoding='utf-8')
            if "New text" in updated and "Old text" not in updated:
                print("[PASS] Section replaced")
                return True
            else:
                print("[FAIL] Section not replaced correctly")
                return False
        else:
            print("[FAIL] Cannot locate section")
            return False
    finally:
        if test_path.exists():
            test_path.unlink()
        backup = test_path.with_suffix('.md.bak')
        if backup.exists():
            backup.unlink()


def test_version_update():
    """测试版本号更新功能"""
    print("\n" + "="*50)
    print("Test 4: Version Update")
    print("="*50)

    test_doc = """---
version: v0.2
---

# Test

> 版本: v0.2

Content...
"""

    test_path = Path("test_version.md")
    test_path.write_text(test_doc, encoding='utf-8')

    try:
        replacer = DocumentReplacer(str(test_path))
        old, new = replacer.update_version('minor')

        if old == "v0.2" and new == "v0.3":
            print(f"[PASS] Version updated: {old} -> {new}")
            return True
        else:
            print(f"[FAIL] Version not updated: {old} -> {new}")
            return False
    finally:
        if test_path.exists():
            test_path.unlink()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print(" Incremental Update Function Tests")
    print("="*60)

    tests = [
        ("Locate Experiment", test_locate_experiment),
        ("Locate Chapter", test_locate_chapter),
        ("Replace Section", test_replace_section),
        ("Version Update", test_version_update),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n[ERROR] {name} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print("Test Results")
    print("="*60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[WARNING] Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
