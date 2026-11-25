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
          "نسخة السيرة المقترحة", "تم التواصل؟", "ملاحظات", "درجة الصلة"]
T_W = [5, 40, 18, 20, 18, 32, 10, 14, 32, 32, 40, 12, 12, 12, 34, 11]
HIGH = ("تربية خاصة", "توحد", "autism", "special", "sen", "inclusion", "دمج", "تأهيل", "rehab", "إعاقة", "disab",
        "determination", "همم", "learning difficult", "صعوبات", "deaf", "blind", "صم", "مكفوفين", "down syndrome")


def relevance(t):
    s = ((t.get("name") or "") + " " + (t.get("type") or "")).lower()
    if any(k in s for k in HIGH) or (t.get("type") in ("مركز تربية خاصة", "جمعية", "منظمة")): return "عالية"
    if t.get("type") in ("مدرسة", "جامعة", "جهة حكومية"): return "متوسطة"
    return "منخفضة"
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
    if ws.max_column < len(T_COLS):  # upgrade older files with the new column
        c = ws.cell(1, len(T_COLS)); c.value = T_COLS[-1]
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3A5F")
        ws.column_dimensions[c.column_letter].width = T_W[-1]
        for r in range(2, ws.max_row + 1):
            ws.cell(r, len(T_COLS)).value = relevance({"name": ws.cell(r, 2).value, "type": ws.cell(r, 3).value})
    by_e, by_n = {}, {}
    for r in range(2, ws.max_row + 1):
        for e in str(ws.cell(r, 6).value or "").split(","):
            e = log_tool.norm_email(e)
            if e: by_e[e] = r
        by_n[log_tool.norm_name(ws.cell(r, 2).value)] = r
    added = skipped = enriched = 0
    FILL = {4: "phone", 5: "whatsapp", 6: "email", 9: "website", 10: "careers"}
    for t in data.get("targets", []):
        es = [log_tool.norm_email(x) for x in str(t.get("email") or "").split(",") if x.strip()]
        n = log_tool.norm_name(t.get("name"))
        if not n: skipped += 1; continue
        row = by_n.get(n) or next((by_e[e] for e in es if e in by_e), None)
        if row:
            changed = False
            for col, key in FILL.items():
                if not ws.cell(row, col).value and t.get(key):
                    ws.cell(row, col).value = t.get(key); changed = True
            enriched += changed; skipped += (not changed); continue
        e = es[0] if es else ""
        lang, cv = suggest(t)
        n_rows = ws.max_row
        ws.append([n_rows, t.get("name"), t.get("type"), t.get("phone"), t.get("whatsapp"), t.get("email"),
                   COUNTRY_AR.get(a.country, a.country), t.get("city"), t.get("website"), t.get("careers"),
                   t.get("source"), lang, cv, "", t.get("notes"), relevance(t)])
        by_n[n] = ws.max_row
        for x in es: by_e[x] = ws.max_row
        added += 1
    useen = {log_tool.norm_name(wu.cell(r, 2).value) for r in range(2, wu.max_row + 1)}
    for u in data.get("unreachable", []):
        if log_tool.norm_name(u.get("name")) in useen: continue
        wu.append([wu.max_row, u.get("name"), u.get("type"), u.get("city"), u.get("website"), u.get("reason")])
    sync_contacted(wb)
    wb.save(path(a.country))
    print(f"{a.country}: added {added}, enriched {enriched}, skipped duplicates {skipped}, total {ws.max_row - 1}, unreachable {wu.max_row - 1}")


def sync_contacted(wb):
    if not os.path.exists(log_tool.LOG): return
    lw = load_workbook(log_tool.LOG)["Applications"]
    ws = wb["الجهات"]
    for r in range(2, ws.max_row + 1):
        hits = log_tool.find(lw, ws.cell(r, 6).value, str(ws.cell(r, 4).value or ws.cell(r, 5).value or ""),
                             ws.cell(r, 2).value)
        hits = [h for h in hits if h[1] != ["اسم مشابه"]]
        ws.cell(r, 14).value = ("نعم – " + str(lw.cell(hits[0][0], log_tool.C["طريقة الإرسال"]).value)) if hits else ""


CC = {"Jordan": "962", "Saudi": "966", "UAE": "971", "Qatar": "974", "Kuwait": "965", "Oman": "968", "Bahrain": "973"}
MOBILE = {"Jordan": r"9627[789]\d{7}", "Saudi": r"9665\d{8}", "UAE": r"9715[0-8]\d{7}", "Qatar": r"974[3567]\d{7}",
          "Kuwait": r"965[569]\d{7}", "Oman": r"968[79]\d{7}", "Bahrain": r"973(?:3\d{7}|66\d{6})"}
WA_COL, WA_HEAD = 17, "حالة الواتساب"


def to_intl(raw, country):
    """normalize one phone string to international digits (no +) for the given country"""
    d = re.sub(r"\D", "", raw or "")
    if not d: return ""
    if d.startswith("00"): d = d[2:]
    cc = CC[country]
    if d.startswith(cc): return d
    if any(d.startswith(c) for c in CC.values()) and len(d) >= 11: return d  # another GCC/JO number
    if d.startswith("0"): d = d[1:]
    return cc + d


def numbers(cell, country):
    return [to_intl(x, country) for x in re.split(r"[,/;|–]| - ", str(cell or "")) if re.search(r"\d{6}", x)]


def is_mobile(n, country):
    return any(re.fullmatch(MOBILE[c], n) for c in MOBILE) if n else False


def whatsapp(a):
    """fill WhatsApp column from mobile numbers and set a status column"""
    p = path(a.country); wb = load_workbook(p); ws = wb["الجهات"]
    c = ws.cell(1, WA_COL)
    if c.value != WA_HEAD:
        c.value = WA_HEAD; c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3A5F")
        ws.column_dimensions[c.column_letter].width = 22
    stats = {"مؤكد": 0, "جوال": 0, "لا": 0}
    for r in range(2, ws.max_row + 1):
        status = ws.cell(r, WA_COL).value or ""
        wa = ws.cell(r, 5).value
        if wa and not status.startswith("جوال"):
            nums = numbers(wa, a.country)
            ws.cell(r, 5).value = ", ".join("+" + n for n in nums) or wa
            ws.cell(r, WA_COL).value = status or "مؤكد – رابط واتساب"; stats["مؤكد"] += 1; continue
        mob = [n for n in numbers(ws.cell(r, 4).value, a.country) if is_mobile(n, a.country)]
        if mob:
            ws.cell(r, 5).value = ", ".join("+" + n for n in dict.fromkeys(mob))
            ws.cell(r, WA_COL).value = status if status.startswith("جوال") and "–" in status else "جوال – غالباً واتساب"
            stats["جوال"] += 1
        else:
            if not wa: ws.cell(r, WA_COL).value = "لا يوجد رقم جوال"
            stats["لا"] += 1
    wb.save(p)
    print(f"{a.country}: واتساب مؤكد {stats['مؤكد']} | جوال (غالباً واتساب) {stats['جوال']} | بدون جوال {stats['لا']}")


SOC_COL, SOC_HEAD = 18, "صفحات التواصل الاجتماعي"


def export_web(a):
    """all rows that have a website (for wa_scan.py); --only-high limits to high relevance"""
    ws = open_wb(a.country)["الجهات"]; out = []
    for r in range(2, ws.max_row + 1):
        if not ws.cell(r, 9).value: continue
        if a.only_no_mobile and (ws.cell(r, WA_COL).value or "") not in ("", "لا يوجد رقم جوال"): continue
        out.append({"row": r, "name": ws.cell(r, 2).value, "website": ws.cell(r, 9).value})
    json.dump({"targets": out}, open(a.file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(a.country, "rows:", len(out))


def apply_scan(a):
    """apply wa_scan / search results: whatsapp, mobile, wa_status, social, source_note (matched by row+name)"""
    p = path(a.country); wb = load_workbook(p); ws = wb["الجهات"]
    for col, head in ((WA_COL, WA_HEAD), (SOC_COL, SOC_HEAD)):
        c = ws.cell(1, col)
        if c.value != head:
            c.value = head; c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3A5F")
            ws.column_dimensions[c.column_letter].width = 26
    by_n = {log_tool.norm_name(ws.cell(r, 2).value): r for r in range(2, ws.max_row + 1)}
    n_wa = n_mob = n_soc = 0
    for t in json.load(open(a.file, encoding="utf-8"))["targets"]:
        r = t.get("row") if t.get("row") and log_tool.norm_name(ws.cell(t["row"], 2).value) == log_tool.norm_name(t.get("name")) \
            else by_n.get(log_tool.norm_name(t.get("name")))
        if not r: continue
        status = ws.cell(r, WA_COL).value or ""
        if t.get("whatsapp") and not status.startswith("مؤكد"):
            ws.cell(r, 5).value = t["whatsapp"]; ws.cell(r, WA_COL).value = t.get("wa_status", "مؤكد"); n_wa += 1
        elif t.get("mobile") and status in ("", "لا يوجد رقم جوال"):
            ws.cell(r, 5).value = t["mobile"]; ws.cell(r, WA_COL).value = t.get("wa_status", "جوال – غالباً واتساب"); n_mob += 1
            if not ws.cell(r, 4).value: ws.cell(r, 4).value = t["mobile"]
        if t.get("social") and not ws.cell(r, SOC_COL).value:
            ws.cell(r, SOC_COL).value = t["social"]; n_soc += 1
        if t.get("source_note"):
            old = ws.cell(r, 15).value or ""
            if t["source_note"] not in old: ws.cell(r, 15).value = (old + " | " + t["source_note"]).strip(" |")
    wb.save(p)
    print(f"{a.country}: واتساب مؤكد جديد {n_wa} | جوال جديد {n_mob} | صفحات تواصل {n_soc}")


def export_missing(a):
    """rows that have a website but miss email or phone -> JSON for enrichment"""
    ws = open_wb(a.country)["الجهات"]; out = []
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 9).value and not (ws.cell(r, 6).value and ws.cell(r, 4).value):
            out.append({"name": ws.cell(r, 2).value, "type": ws.cell(r, 3).value, "phone": ws.cell(r, 4).value or "",
                        "whatsapp": ws.cell(r, 5).value or "", "email": ws.cell(r, 6).value or "",
                        "website": ws.cell(r, 9).value})
    json.dump({"targets": out}, open(a.file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(a.country, "rows to enrich:", len(out))


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
    x = sp.add_parser("export-missing"); x.add_argument("--country", required=True, choices=list(COUNTRY_AR))
    x.add_argument("--file", required=True)
    e = sp.add_parser("export-web"); e.add_argument("--country", required=True, choices=list(COUNTRY_AR))
    e.add_argument("--file", required=True); e.add_argument("--only-no-mobile", action="store_true")
    ap2 = sp.add_parser("apply-scan"); ap2.add_argument("--country", required=True, choices=list(COUNTRY_AR))
    ap2.add_argument("--file", required=True)
    w = sp.add_parser("whatsapp"); w.add_argument("--country", required=True, choices=list(COUNTRY_AR))
    sp.add_parser("stats")
    a = ap.parse_args()
    {"import": do_import, "stats": stats, "export-missing": export_missing, "whatsapp": whatsapp,
     "export-web": export_web, "apply-scan": apply_scan}[a.cmd](a)


if __name__ == "__main__":
    main()
