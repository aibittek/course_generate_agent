# -*- coding: utf-8 -*-
"""Extract text/table/image from all 聆动 Word docs to readable text files."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC = r"D:\项目资料\聆动机械臂\聆动课程\指导文档\WORD"
OUT = r"d:\Code\aiot_course\course_generate_agent\_word_extract"
os.makedirs(OUT, exist_ok=True)

import docx
from docx import Document

def extract_paragraphs_and_tables(doc_path):
    """Iterate document body in order (paragraphs + tables), keeping structure."""
    doc = Document(doc_path)
    body = doc.element.body
    lines = []
    # Map element index to position in body by iterating body children.
    from docx.oxml.ns import qn
    for child in body.iterchildren():
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            # find matching paragraph
            # resolve text including runs
            texts = child.itertext() if False else None
            # Simpler: collect paragraph text
            t = []
            for node in child.iter():
                if node.tag == qn('w:t') and node.text:
                    t.append(node.text)
            txt = "".join(t)
            # Detect heading style
            pPr = child.find(qn('w:pPr'))
            style = ""
            if pPr is not None:
                sty = pPr.find(qn('w:pStyle'))
                if sty is not None:
                    style = sty.get(qn('w:val'))
            if txt.strip():
                lines.append((style, txt))
        elif tag == 'tbl':
            # Table
            lines.append(("__TABLE__", ""))
            # iterate rows
            for tr in child.iter(qn('w:tr')):
                cells = []
                for tc in tr.iter(qn('w:tc')):
                    ct = []
                    for node in tc.iter(qn('w:t')):
                        if node.text:
                            ct.append(node.text)
                    cells.append("".join(ct))
                lines.append(("__CELL__", " | ".join(cells)))
    return lines

def dump(name, path):
    print(f"### {name}")
    try:
        lines = extract_paragraphs_and_tables(path)
        out = []
        for style, txt in lines:
            if style == "__TABLE__":
                out.append("")
                out.append("[表格]")
            elif style == "__CELL__":
                out.append("  " + txt)
            elif style.startswith("Heading") or style.startswith("标题"):
                out.append("")
                out.append("# " + txt)
            else:
                out.append(txt)
        txtfile = os.path.join(OUT, name + ".txt")
        with open(txtfile, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        print(f"  -> wrote {len(out)} lines, chars={sum(len(x) for x in out)} : {txtfile}")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()

for f in sorted(os.listdir(SRC)):
    if f.endswith(".docx"):
        base = os.path.splitext(f)[0]
        dump(base, os.path.join(SRC, f))
print("DONE")