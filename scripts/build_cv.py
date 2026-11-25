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


LATIN = "Noto Sans"
AR_BODY, AR_HEAD = "Noto Naskh Arabic", "Noto Kufi Arabic"


def set_run_font(run, font, size, bold=False, color=None, rtl=False):
    """font = complex-script (Arabic) font for RTL text; Latin runs always use LATIN in Arabic docs"""
    latin = LATIN if rtl else font
    run.font.name = latin
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); rpr.insert(0, rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia"):
        rfonts.set(qn(a), latin)
    rfonts.set(qn("w:cs"), font)
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
    pf.line_spacing = 1.2 if rtl else 1.25
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
    body = AR_BODY if rtl else LATIN
    head = AR_HEAD if rtl else LATIN
    BODY, SMALL = (12.5, 11) if rtl else (11, 10)
    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(1.8)
        s.left_margin = s.right_margin = Cm(2.0)
        if rtl:
            s._sectPr.append(OxmlElement("w:bidi"))
    para(doc, data["name"], head, 22, rtl, bold=True, color=ACCENT, space_after=2)
    para(doc, data["title"], head if rtl else body, 12.5, rtl, bold=True, color=GREY, space_after=4)
    para(doc, data["contact"], body, SMALL + 0.5, rtl, space_after=0)
    para(doc, data["orcid"], body, SMALL + 0.5, rtl, space_after=8)
    for heading, items in data["sections"]:
        h = para(doc, heading, head, 14, rtl, bold=True, color=ACCENT, space_before=12, space_after=6)
        bottom_border(h)
        h.paragraph_format.keep_with_next = True
        for it in items:
            if no_phd and it.get("phd"):
                continue
            if "p" in it:
                para(doc, it["p"], body, BODY, rtl, space_after=5)
            if "h" in it:
                para(doc, it["h"], body, BODY + 0.5, rtl, bold=True, space_before=6,
                     space_after=1).paragraph_format.keep_with_next = True
            if "sub" in it:
                para(doc, it["sub"], body, SMALL, rtl, color=GREY, space_after=4).paragraph_format.keep_with_next = True
            for b in it.get("bullets", []):
                if rtl and not it.get("ltr"):
                    p = para(doc, "\u2022  " + b, body, BODY, True, space_after=3)
                    p.paragraph_format.first_line_indent = Cm(-0.5)
                    p.paragraph_format.left_indent = Cm(0.5)
                else:
                    p = para(doc, b, LATIN, BODY - (1 if rtl else 0), False, space_after=3, style="List Bullet")
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
