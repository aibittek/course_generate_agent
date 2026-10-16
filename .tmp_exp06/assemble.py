# -*- coding: utf-8 -*-
"""把 EXP-06 话题章节的重写片段原子拼接进 index.html"""
import io, re, os, shutil, sys

BASE = r"D:/实验资源验证/course_generate_agent/training/output/courses/core/exp003-ros2-application/exp-06-topic/index.html"
TMP  = r"D:/实验资源验证/course_generate_agent/.tmp_exp06/"

s = io.open(BASE, encoding="utf-8").read()
before_len = len(s)
shutil.copyfile(BASE, BASE + ".bak")

def frag(name):
    t = io.open(TMP + name, encoding="utf-8").read()
    return t.rstrip("\n")

def rep_section(marker, fname):
    global s
    pat = re.compile(re.escape(marker) + r".*?</section>", re.S)
    new, n = pat.subn(lambda m: frag(fname), s, count=1)
    if n != 1:
        raise SystemExit("MARKER FAIL: " + marker)
    s = new
    print("  ok section:", marker, "->", fname)

print("== 1. 替换章节 ==")
rep_section("<!-- 01 问题 -->",   "s1.html")
rep_section("<!-- 02 原理 -->",   "s2.html")
rep_section("<!-- 04 QoS -->",    "s4.html")
rep_section("<!-- 05 交互 -->",   "s5.html")
rep_section("<!-- 06 MQ5 -->",    "s6.html")
rep_section("<!-- 07 代码 -->",   "s7.html")
rep_section("<!-- 08 实操 -->",   "s8.html")

print("== 2. 注入 CSS ==")
css = io.open(TMP + "css-add.txt", encoding="utf-8").read()
assert s.count("</style>") == 1
s = s.replace("</style>", css + "</style>", 1)

print("== 3. 替换 QoS 脚本 ==")
i = s.index("// QoS 兼容性检查")
j = s.index("// MQ5 换算计算器")
assert i < j
js = io.open(TMP + "js-add.txt", encoding="utf-8").read()
s = s[:i] + js + "\n" + s[j:]

print("== 4. 同步侧边栏 ==")
navs = [
    ('<span class="n">01</span>为什么需要话题：持续数据流的协作难题',
     '<span class="n">01</span>为什么需要话题：一份数据，四个听众'),
    ('<span class="n">02</span>核心原理：发布/订阅是如何解耦的',
     '<span class="n">02</span>核心原理：消息如何走到回调里'),
    ('<span class="n">04</span>QoS 三要素：通信行为的"合同条款"',
     '<span class="n">04</span>QoS：给话题签一份传输合同'),
    ('<span class="n">05</span>互动沙盒：亲手配对 QoS',
     '<span class="n">05</span>QoS 实验台：改档位看效果'),
    ('<span class="n">06</span>专题：MQ5 从电压到 ppm 的对数换算',
     '<span class="n">06</span>先看现象：跑出 MQ5 浓度流'),
    ('<span class="n">07</span>代码精讲与数据流',
     '<span class="n">07</span>代码精讲：三份源码逐行读懂'),
    ('<span class="n">08</span>实操流程',
     '<span class="n">08</span>动手任务：把现象变成证据'),
]
for old, new in navs:
    if old not in s:
        raise SystemExit("NAV FAIL: " + old)
    s = s.replace(old, new, 1)
    print("  nav:", new[new.index('</span>')+7:][:34])

io.open(BASE, "w", encoding="utf-8").write(s)
print("== done ==")
print("chars: %d -> %d  (+%d)" % (before_len, len(s), len(s) - before_len))
print("sections:", s.count('<section class="blk reveal"'))
for sid in ["s1","s2","s3","s4","s5","s6","s7","s8","s9","s10"]:
    assert 'id="%s"' % sid in s, sid
print("all section ids present")
