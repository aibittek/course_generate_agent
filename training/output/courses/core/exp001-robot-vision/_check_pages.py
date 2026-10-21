# -*- coding: utf-8 -*-
"""课程页面结构校验：标签配对、链接可达、关键组件存在、无未替换占位符。"""
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.abspath(__file__))

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = set()
        self.hrefs = []
        self.classes = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            if a['id'] in self.ids:
                self.errors.append('重复 id: %s' % a['id'])
            self.ids.add(a['id'])
        if 'class' in a:
            for c in a['class'].split():
                self.classes.add(c)
        if tag == 'a' and 'href' in a:
            self.hrefs.append(a['href'])
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append('多余闭合 </%s> 行 %d' % (tag, self.getpos()[0]))
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            # 尝试向上找
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    for j in range(len(self.stack) - 1, i - 1, -1):
                        self.errors.append('未闭合 <%s> 行 %d' %
                                           (self.stack[j][0], self.stack[j][1]))
                    del self.stack[i:]
                    return
            self.errors.append('孤立闭合 </%s> 行 %d' % (tag, self.getpos()[0]))


def check(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    c = Checker()
    c.feed(html)
    errs = list(c.errors)
    for tag, line in c.stack:
        errs.append('未闭合 <%s> 行 %d' % (tag, line))

    # 占位符检查
    for ph in ('{', 'TODO', 'FIXME', 'XXX'):
        if ph in ('{',):
            # 只检查形如 {name} 的模板占位
            if re.search(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', html):
                errs.append('发现未替换占位符 %s' % ph)
        elif ph in html:
            errs.append('发现标记 %s' % ph)

    # 相对链接可达性
    base = os.path.dirname(path)
    for h in c.hrefs:
        if h.startswith(('#', 'http', 'mailto:', 'javascript:')):
            continue
        target = os.path.normpath(os.path.join(base, h.split('#')[0]))
        if not os.path.exists(target):
            errs.append('链接目标不存在: %s' % h)

    return errs, c, html


def main():
    pages = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if '_build_archive' in dirpath:
            continue
        for fn in filenames:
            if fn.endswith('.html'):
                pages.append(os.path.join(dirpath, fn))
    pages.sort()

    total_bad = 0
    for p in pages:
        rel = os.path.relpath(p, ROOT)
        errs, c, html = check(p)
        size = len(html.encode('utf-8'))
        n_section = len(re.findall(r'<section\b', html))
        status = 'OK  ' if not errs else 'FAIL'
        print('%s %-46s %6dB  sec=%-3d cls=%-3d' %
              (status, rel, size, n_section, len(c.classes)))
        for e in errs[:12]:
            print('       - ' + e)
        if len(errs) > 12:
            print('       ... 另有 %d 条' % (len(errs) - 12))
        total_bad += len(errs)

    print('\n页面数 = %d，问题总数 = %d' % (len(pages), total_bad))
    return 0 if total_bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
