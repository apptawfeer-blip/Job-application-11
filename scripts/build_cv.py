# -*- coding: utf-8 -*-
"""يبني 4 نسخ من السيرة (docx + pdf) في مجلد cv/:
  Amer_AlSaaideh_CV_Arabic / _English          (كاملة: للمراكز والمنظمات وغيرها)
  Amer_AlSaaideh_CV_Arabic_NoPhD / _English_NoPhD (بدون الدكتوراه: للمدارس والجامعات)
الاستخدام: python3 scripts/build_cv.py
"""
import os, subprocess, sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cv_content import AR, EN

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "cv")
ACCENT = RGBColor(0x1F, 0x3A, 0x5F)
GREY = RGBColor(0x44, 0x44, 0x44)


def set_run_font(run, font, size, bold=False, color=None, rtl=False):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); rpr.insert(0, rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(a), font)
    for tag in ("w:szCs",):
        el = OxmlElement(tag); el.set(qn("w:val"), str(int(size * 2))); rpr.append(el)
    if bold:
        rpr.append(OxmlElement("w:bCs"))
    if rtl:
        rpr.append(OxmlElement("w:rtl"))


def para(doc, text, font, size, rtl, bold=False, color=None, space_after=2,
         space_before=0, style=None, align=None):
    p = doc.add_paragraph(style=style)
    pf = p.paragraph_format
    pf.space_after = Pt(space_after); pf.space_before = Pt(space_before)
    pf.line_spacing = 1.0 if rtl else 1.1
    if rtl:
        ppr = p._element.get_or_add_pPr()
        ppr.insert(0, OxmlElement("w:bidi"))
        # في الفقرات RTL تُفسَّر "left" على أنها بداية السطر (اليمين)
        p.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.LEFT
    elif align is not None:
        p.alignment = align
    r = p.add_run(text)
    set_run_font(r, font, size, bold, color, rtl)
    return p


def bottom_border(p):
    ppr = p._element.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr"); b = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", "1F3A5F")):
        b.set(qn(k), v)
    bdr.append(b); ppr.append(bdr)


def build(data, no_phd, path):
    rtl = data["lang"] == "ar"
    font = "Noto Sans Arabic" if rtl else "Calibri"
    if not rtl:
        font = "Carlito"  # metric-compatible with Calibri, embedded in PDF
    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(1.6)
        s.left_margin = s.right_margin = Cm(1.8)
        if rtl:
            s._sectPr.append(OxmlElement("w:bidi"))
    para(doc, data["name"], font, 20, rtl, bold=True, color=ACCENT, space_after=0)
    para(doc, data["title"], font, 11.5, rtl, bold=True, color=GREY, space_after=2)
    para(doc, data["contact"], font, 10, rtl, space_after=0)
    para(doc, data["orcid"], font, 10, rtl, space_after=6)
    for heading, items in data["sections"]:
        h = para(doc, heading, font, 13, rtl, bold=True, color=ACCENT, space_before=8, space_after=4)
        bottom_border(h)
        h.paragraph_format.keep_with_next = True
        for it in items:
            if no_phd and it.get("phd"):
                continue
            if "p" in it:
                para(doc, it["p"], font, 10, rtl, space_after=3, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
            if "h" in it:
                para(doc, it["h"], font, 10.5, rtl, bold=True, space_before=3,
                     space_after=0).paragraph_format.keep_with_next = True
            if "sub" in it:
                para(doc, it["sub"], font, 9.5, rtl, color=GREY, space_after=2)
            for b in it.get("bullets", []):
                if rtl and not it.get("ltr"):
                    p = para(doc, "•  " + b, font, 10, True, space_after=1)
                    p.paragraph_format.right_indent = Cm(0)
                    p.paragraph_format.first_line_indent = Cm(-0.4)
                    p.paragraph_format.left_indent = Cm(0.4)
                else:
                    p = para(doc, b, "Carlito" if rtl else font, 10, False, space_after=1,
                             style="List Bullet")
    doc.save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [(AR, False, "Amer_AlSaaideh_CV_Arabic"), (AR, True, "Amer_AlSaaideh_CV_Arabic_NoPhD"),
            (EN, False, "Amer_AlSaaideh_CV_English"), (EN, True, "Amer_AlSaaideh_CV_English_NoPhD")]
    for data, nophd, name in jobs:
        p = os.path.join(OUT, name + ".docx")
        build(data, nophd, p)
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUT, p],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("built", name)


if __name__ == "__main__":
    main()
