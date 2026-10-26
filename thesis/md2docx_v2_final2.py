"""开题报告 md -> docx 转换（宋体正文/黑体标题/表格/图片/占位符）。"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

SRC = Path(__file__).resolve().parent / "开题报告_v2_提交版.md"
DST = Path(__file__).resolve().parent / "开题报告_v2_终稿2.docx"

doc = Document()

# 基础样式：正文宋体小四，西文 Times New Roman
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def set_cn(run, font="宋体", size=12, bold=False, color=None):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = color


def add_runs(p, text, size=12, cn_font="宋体", bold=False, sup=False):
    """解析 **粗体** 与 <sup>上标</sup>，逐段添加 run。"""
    # 先按上标标签切分
    for seg in re.split(r"(<sup>.*?</sup>)", text):
        if not seg:
            continue
        if seg.startswith("<sup>") and seg.endswith("</sup>"):
            inner = seg[5:-6]
            # 上标内部仍可能有粗体
            for j, sub in enumerate(re.split(r"\*\*", inner)):
                if sub:
                    r = p.add_run(sub)
                    set_cn(r, font=cn_font, size=size, bold=bold or (j % 2 == 1))
                    r.font.superscript = True
        else:
            for j, sub in enumerate(re.split(r"\*\*", seg)):
                if sub:
                    set_cn(p.add_run(sub), font=cn_font, size=size, bold=bold or (j % 2 == 1))


lines = SRC.read_text(encoding="utf-8").splitlines()
i = 0
while i < len(lines):
    line = lines[i].rstrip()

    if not line or line == "---":
        i += 1
        continue

    # 表格
    if line.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                rows.append(cells)
            i += 1
        if rows:
            tbl = doc.add_table(rows=len(rows), cols=len(rows[0]))
            tbl.style = "Table Grid"
            for r, row in enumerate(rows):
                for c, cell in enumerate(row):
                    para = tbl.cell(r, c).paragraphs[0]
                    add_runs(para, cell, size=10.5)
                    if r == 0:
                        for run in para.runs:
                            run.bold = True
        continue

    # 图片
    m = re.match(r"!\[(.*?)\]\((.*?)\)", line.strip())
    if m:
        img = SRC.parent / m.group(2)
        if img.exists():
            doc.add_picture(str(img), width=Inches(6.2))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        i += 1
        continue

    # 标题
    if line.startswith("# "):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cn(p.add_run(line[2:]), font="黑体", size=16, bold=True)
        i += 1
        continue
    if line.startswith("## "):
        p = doc.add_paragraph()
        set_cn(p.add_run(line[3:]), font="黑体", size=14, bold=True)
        i += 1
        continue
    if line.startswith("### "):
        p = doc.add_paragraph()
        set_cn(p.add_run(line[4:]), font="黑体", size=12.5, bold=True)
        i += 1
        continue

    # 引用块（说明/占位）-> 灰色斜体小字
    if line.startswith(">"):
        text = line.lstrip("> ").strip()
        if text:
            p = doc.add_paragraph()
            set_cn(p.add_run(text), size=10.5)
            for run in p.runs:
                run.font.color.rgb = None
                run.italic = True
        i += 1
        continue

    # 普通段落
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(24)  # 首行缩进两字符
    add_runs(p, line)
    i += 1

doc.save(DST)
print(f"saved {DST}")
