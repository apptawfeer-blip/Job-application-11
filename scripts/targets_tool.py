# -*- coding: utf-8 -*-
"""ملفات الجهات المستهدفة لكل دولة: output/targets/Targets_<Country>.xlsx
ورقتان: "الجهات" و "تعذر الوصول".

  python3 scripts/targets_tool.py import --country Jordan --file data.json
    data.json = {"targets": [{...}], "unreachable": [{...}]}
    مفاتيح الجهة: name, type, phone, whatsapp, email, city, website, careers, source, notes
    مفاتيح تعذر الوصول: name, type, city, website, reason
  python3 scripts/targets_tool.py stats

يمنع تكرار الجهة داخل الملف (نفس الإيميل أو نفس الاسم بعد التوحيد)، ويحدد تلقائياً
لغة التقديم ونسخة السيرة المقترحة حسب نوع الجهة، ويعلّم "تم التواصل؟" من سجل التقديمات.
"""
import argparse, json, os, re, sys, glob
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import log_tool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "output", "targets")
COUNTRY_AR = {"Jordan": "الأردن", "Qatar": "قطر", "Saudi": "السعودية", "UAE": "الإمارات",
              "Kuwait": "الكويت", "Oman": "عُمان", "Bahrain": "البحرين"}
T_COLS = ["#", "الاسم", "نوع الجهة", "رقم الموبايل/الهاتف", "واتساب", "الإيميل", "الدولة", "المدينة",
          "الموقع الإلكتروني", "صفحة التوظيف", "مصدر المعلومة", "لغة التقديم المقترحة",
          "نسخة السيرة المقترحة", "تم التواصل؟", "ملاحظات"]
T_W = [5, 40, 18, 20, 18, 32, 10, 14, 32, 32, 40, 12, 12, 12, 34]
U_COLS = ["#", "الاسم/المصدر", "نوع الجهة", "المدينة", "الموقع/الرابط", "سبب التعذر"]
U_W = [5, 40, 18, 14, 40, 50]
TYPES_NOPHD = ("جامعة", "مدرسة", "كلية")
INTL_HINTS = ("international", "british", "american", "dolia", "unicef", "unrwa", "unesco", "save the children",
              "humanity", "ngo", "منظمة", "دولية", "الدولية", "academy", "school", "university", "college")


def header(ws, cols, widths):
    ws.sheet_view.rightToLeft = True
    ws.append(cols)
    for i, w in enumerate(widths, 1):
        c = ws.cell(1, i); ws.column_dimensions[c.column_letter].width = w
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3A5F")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"; ws.auto_filter.ref = f"A1:{ws.cell(1, len(cols)).column_letter}1"


def path(country):
    return os.path.join(DIR, f"Targets_{country}.xlsx")


def open_wb(country):
    p = path(country)
    if os.path.exists(p):
        return load_workbook(p)
    os.makedirs(DIR, exist_ok=True)
    wb = Workbook(); ws = wb.active; ws.title = "الجهات"; header(ws, T_COLS, T_W)
    header(wb.create_sheet("تعذر الوصول"), U_COLS, U_W)
    return wb


def suggest(t):
    typ = t.get("type", "") or ""
    name = (t.get("name", "") or "").lower()
    cv = "NoPhD" if any(k in typ for k in TYPES_NOPHD) else "Full"
    has_latin = bool(re.search(r"[a-z]", name))
    lang = "EN" if (has_latin and any(h in name for h in INTL_HINTS)) or "منظمة" in typ else "AR"
    return t.get("lang") or lang, t.get("cv") or cv


def do_import(a):
    data = json.load(open(a.file, encoding="utf-8"))
    wb = open_wb(a.country); ws = wb["الجهات"]; wu = wb["تعذر الوصول"]
    seen_e, seen_n = set(), set()
    for r in range(2, ws.max_row + 1):
        seen_e.add(log_tool.norm_email(ws.cell(r, 6).value)); seen_n.add(log_tool.norm_name(ws.cell(r, 2).value))
    seen_e.discard("")
    added = skipped = 0
    for t in data.get("targets", []):
        e = log_tool.norm_email(t.get("email")); n = log_tool.norm_name(t.get("name"))
        if not n or n in seen_n or (e and e in seen_e):
            skipped += 1; continue
        lang, cv = suggest(t)
        n_rows = ws.max_row
        ws.append([n_rows, t.get("name"), t.get("type"), t.get("phone"), t.get("whatsapp"), t.get("email"),
                   COUNTRY_AR.get(a.country, a.country), t.get("city"), t.get("website"), t.get("careers"),
                   t.get("source"), lang, cv, "", t.get("notes")])
        seen_n.add(n); e and seen_e.add(e); added += 1
    useen = {log_tool.norm_name(wu.cell(r, 2).value) for r in range(2, wu.max_row + 1)}
    for u in data.get("unreachable", []):
        if log_tool.norm_name(u.get("name")) in useen: continue
        wu.append([wu.max_row, u.get("name"), u.get("type"), u.get("city"), u.get("website"), u.get("reason")])
    sync_contacted(wb)
    wb.save(path(a.country))
    print(f"{a.country}: added {added}, skipped duplicates {skipped}, total {ws.max_row - 1}, unreachable {wu.max_row - 1}")


def sync_contacted(wb):
    if not os.path.exists(log_tool.LOG): return
    lw = load_workbook(log_tool.LOG)["Applications"]
    ws = wb["الجهات"]
    for r in range(2, ws.max_row + 1):
        hits = log_tool.find(lw, ws.cell(r, 6).value, str(ws.cell(r, 4).value or ws.cell(r, 5).value or ""),
                             ws.cell(r, 2).value)
        hits = [h for h in hits if h[1] != ["اسم مشابه"]]
        ws.cell(r, 14).value = ("نعم – " + str(lw.cell(hits[0][0], log_tool.C["طريقة الإرسال"]).value)) if hits else ""


def stats(_):
    for p in sorted(glob.glob(os.path.join(DIR, "Targets_*.xlsx"))):
        wb = load_workbook(p); sync_contacted(wb); wb.save(p)
        ws = wb["الجهات"]; total = ws.max_row - 1
        we = sum(1 for r in range(2, ws.max_row + 1) if ws.cell(r, 6).value)
        wp = sum(1 for r in range(2, ws.max_row + 1) if ws.cell(r, 4).value or ws.cell(r, 5).value)
        print(f"{os.path.basename(p)}: {total} جهة | بإيميل {we} | برقم {wp} | تعذر الوصول {wb['تعذر الوصول'].max_row - 1}")


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    i = sp.add_parser("import"); i.add_argument("--country", required=True, choices=list(COUNTRY_AR))
    i.add_argument("--file", required=True)
    sp.add_parser("stats")
    a = ap.parse_args()
    {"import": do_import, "stats": stats}[a.cmd](a)


if __name__ == "__main__":
    main()
