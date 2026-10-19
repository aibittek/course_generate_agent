# -*- coding: utf-8 -*-
"""Dump paragraphs+tables from 05-LZ-XL01主从臂校准.docx"""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC = r"D:\项目资料\lerobot\LZ-XL01课程\指导文件\WORD\05-LZ-XL01主从臂校准.docx"
from docx import Document
from docx.oxml.ns import qn

doc = Document(SRC)
body = doc.element.body

def ptext(p):
    return "".join(n.text or "" for n in p.iter(qn('w:t')))

print("=== 05-LZ-XL01主从臂校准.docx ===")
for i, child in enumerate(body.iterchildren()):
    tag = child.tag.split('}')[-1]
    if tag == 'p':
        txt = ptext(child).strip()
        imgs = len(list(child.iter(qn('a:blip'))))
        if txt or imgs:
            print(f"{i:>4} |P| {'[图x'+str(imgs)+'] ' if imgs else ''}{txt}")
    elif tag == 'tbl':
        print(f"{i:>4} |T| [表格]")
        for tr in child.iter(qn('w:tr')):
            cells = []
            for tc in tr.iter(qn('w:tc')):
                ct = "".join(n.text or "" for n in tc.iter(qn('w:t')))
                cells.append(ct.strip())
            line = " | ".join(cells)
            if line.strip(" |"):
                print(f"        {line}")
print("\nDONE")