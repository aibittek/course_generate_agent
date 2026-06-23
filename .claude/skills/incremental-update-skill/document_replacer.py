#!/usr/bin/env python3
"""
文档局部替换工具
用于增量更新流程中的精确定位和内容替换
"""

import re
import yaml
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class SectionBoundary:
    """章节边界"""
    start_line: int
    end_line: int
    title: str


class DocumentReplacer:
    """文档替换器"""

    def __init__(self, doc_path: str):
        self.doc_path = Path(doc_path)
        self.lines = []
        self.load_document()

    def load_document(self):
        """加载文档"""
        if not self.doc_path.exists():
            raise FileNotFoundError(f"文档不存在: {self.doc_path}")

        with open(self.doc_path, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

    def save_document(self, backup=True):
        """保存文档"""
        if backup:
            backup_path = self.doc_path.with_suffix('.md.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.writelines(self.lines)
            print(f"✅ 备份已保存: {backup_path}")

        with open(self.doc_path, 'w', encoding='utf-8') as f:
            f.writelines(self.lines)
        print(f"✅ 文档已更新: {self.doc_path}")

    def locate_experiment(self, exp_id: int) -> Optional[SectionBoundary]:
        """
        定位实验章节边界

        查找模式:
        - 起始: ## 实验{exp_id}
        - 结束: ## 实验{exp_id+1} 或 ## 附录 或文档末尾
        """
        start_pattern = f"## 实验{exp_id}"
        end_patterns = [
            f"## 实验{exp_id + 1}",
            "## 附录",
            "## 更新日志",
        ]

        start_line = None
        title = ""

        # 查找起始
        for i, line in enumerate(self.lines):
            if line.strip().startswith(start_pattern):
                start_line = i
                title = line.strip()
                break

        if start_line is None:
            return None

        # 查找结束
        end_line = len(self.lines)
        for i in range(start_line + 1, len(self.lines)):
            for pattern in end_patterns:
                if self.lines[i].strip().startswith(pattern):
                    end_line = i
                    break
            if end_line < len(self.lines):
                break

        return SectionBoundary(start_line, end_line, title)

    def locate_chapter(self, chapter: int) -> Optional[SectionBoundary]:
        """
        定位章节边界

        查找模式:
        - 起始: ## 第{chapter}章
        - 结束: ## 第{chapter+1}章 或文档末尾
        """
        start_pattern = f"## 第{chapter}章"
        end_pattern = f"## 第{chapter + 1}章"

        start_line = None
        title = ""

        for i, line in enumerate(self.lines):
            if line.strip().startswith(start_pattern):
                start_line = i
                title = line.strip()
                break

        if start_line is None:
            return None

        end_line = len(self.lines)
        for i in range(start_line + 1, len(self.lines)):
            if self.lines[i].strip().startswith(end_pattern):
                end_line = i
                break

        return SectionBoundary(start_line, end_line, title)

    def replace_section(self, boundary: SectionBoundary, new_content: str):
        """
        替换章节内容

        保留:
        - 章节标题（第一行）
        - 确保内容以换行结尾
        """
        if not new_content.endswith('\n'):
            new_content += '\n'

        # 确保新内容以标题开始（如果没有则添加）
        new_lines = new_content.split('\n')
        if not new_lines[0].strip().startswith('#'):
            new_lines.insert(0, boundary.title)
            new_content = '\n'.join(new_lines)

        # 替换内容
        self.lines = (
            self.lines[:boundary.start_line] +
            [new_content + '\n'] +
            self.lines[boundary.end_line:]
        )

        print(f"✅ 已替换: {boundary.title}")
        print(f"   范围: L{boundary.start_line + 1}-L{boundary.end_line}")
        print(f"   新内容: {len(new_content)} 字符")

    def update_version(self, update_type: str = 'minor') -> Tuple[str, str]:
        """
        更新文档版本号

        查找模式:
        - YAML frontmatter: version: v0.2
        - Markdown 元数据: > 版本: v0.2

        返回: (旧版本, 新版本)
        """
        old_version = None
        new_version = None

        # 查找 YAML frontmatter
        in_frontmatter = False
        for i, line in enumerate(self.lines):
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                continue

            if in_frontmatter:
                match = re.match(r'version:\s*v?(\d+)\.(\d+)', line)
                if match:
                    major, minor = int(match.group(1)), int(match.group(2))
                    old_version = f"v{major}.{minor}"

                    if update_type == 'major':
                        new_version = f"v{major + 1}.0"
                    else:
                        new_version = f"v{major}.{minor + 1}"

                    self.lines[i] = f"version: {new_version}\n"
                    break

        # 如果没找到 frontmatter，查找 Markdown 元数据
        if old_version is None:
            for i, line in enumerate(self.lines):
                match = re.match(r'>\s*版本:\s*v?(\d+)\.(\d+)', line)
                if match:
                    major, minor = int(match.group(1)), int(match.group(2))
                    old_version = f"v{major}.{minor}"

                    if update_type == 'major':
                        new_version = f"v{major + 1}.0"
                    else:
                        new_version = f"v{major}.{minor + 1}"

                    self.lines[i] = f"> 版本: {new_version}\n"
                    break

        if old_version:
            print(f"✅ 版本更新: {old_version} → {new_version}")
        else:
            print(f"⚠️ 未找到版本号，建议手动更新")

        return old_version, new_version

    def append_changelog(self, version: str, change_desc: str):
        """
        追加更新日志

        查找 "## 更新日志" 章节，在表格中插入新行
        """
        changelog_start = None
        table_start = None

        # 查找更新日志章节
        for i, line in enumerate(self.lines):
            if line.strip() == "## 更新日志":
                changelog_start = i
                break

        if changelog_start is None:
            print("⚠️ 未找到更新日志章节")
            return

        # 查找表格起始（表头下一行）
        for i in range(changelog_start, len(self.lines)):
            if re.match(r'\|\s*版本\s*\|', self.lines[i]):
                table_start = i + 2  # 跳过表头和分隔线
                break

        if table_start is None:
            print("⚠️ 未找到更新日志表格")
            return

        # 插入新行
        from datetime import datetime
        date = datetime.now().strftime('%Y-%m-%d')
        new_row = f"| {version} | {date} | {change_desc} | Agent |\n"
        self.lines.insert(table_start, new_row)

        print(f"✅ 已追加更新日志: {version} - {change_desc}")


def main():
    """测试函数"""
    import sys

    if len(sys.argv) < 4:
        print("用法: python document_replacer.py <doc_path> <type> <id> <new_content_path>")
        print("示例: python document_replacer.py lab_guide.md experiment 5 new_exp5.md")
        sys.exit(1)

    doc_path = sys.argv[1]
    section_type = sys.argv[2]  # experiment | chapter
    section_id = int(sys.argv[3])
    new_content_path = sys.argv[4] if len(sys.argv) > 4 else None

    replacer = DocumentReplacer(doc_path)

    if section_type == 'experiment':
        boundary = replacer.locate_experiment(section_id)
    elif section_type == 'chapter':
        boundary = replacer.locate_chapter(section_id)
    else:
        print(f"❌ 不支持的类型: {section_type}")
        sys.exit(1)

    if boundary is None:
        print(f"❌ 未找到: {section_type} {section_id}")
        sys.exit(1)

    print(f"✅ 定位成功: {boundary.title}")
    print(f"   范围: L{boundary.start_line + 1}-L{boundary.end_line}")

    if new_content_path:
        with open(new_content_path, 'r', encoding='utf-8') as f:
            new_content = f.read()

        replacer.replace_section(boundary, new_content)
        old_ver, new_ver = replacer.update_version('minor')
        replacer.append_changelog(new_ver, f"更新{section_type} {section_id}")
        replacer.save_document(backup=True)


if __name__ == '__main__':
    main()
