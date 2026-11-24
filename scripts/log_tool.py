# -*- coding: utf-8 -*-
"""سجل التقديمات: output/applications_log.xlsx

  python3 scripts/log_tool.py init
  python3 scripts/log_tool.py check --email X --phone Y --name "اسم الجهة"
  python3 scripts/log_tool.py add --name ... --country ... --method Email|WhatsApp \
        [--city --type --position --email --phone --lang AR|EN --cv Full|NoPhD \
         --subject --source --notes]
  python3 scripts/log_tool.py status --row N --status Replied|Interview|Rejected|Hired [--notes]

check يعيد كود خروج 1 عند وجود تطابق (تم الإرسال سابقاً).
add: إذا كانت الجهة موجودة وأُرسل لها بطريقة أخرى، يتم تحديث الطريقة إلى Both بدلاً من إضافة صف جديد.
"""
import argparse, datetime, os, re, sys
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.environ.get("APPLICATIONS_LOG", os.path.join(ROOT, "output", "applications_log.xlsx"))

COLS = ["#", "التاريخ", "اسم الجهة", "الدولة", "المدينة", "نوع الجهة", "الوظيفة",
        "الإيميل", "رقم الواتساب", "طريقة الإرسال", "لغة السيرة", "نسخة السيرة",
        "موضوع الإيميل", "المصدر/الرابط", "الحالة", "تاريخ آخر تحديث", "ملاحظات"]
WIDTHS = [5, 12, 34, 12, 14, 18, 22, 32, 18, 14, 10, 11, 36, 34, 12, 14, 30]
C = {n: i + 1 for i, n in enumerate(COLS)}


def norm_phone(p):
    d = re.sub(r"\D", "", p or "")
    if d.startswith("00"):
        d = d[2:]
    return d.lstrip("0")


def norm_email(e):
    return (e or "").strip().lower()


def norm_name(n):
    n = (n or "").strip().lower()
    n = re.sub(r"[إأآ]", "ا", n).replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"\s+", " ", n)


def init():
    if os.path.exists(LOG):
        print("exists:", LOG); return
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    wb = Workbook(); ws = wb.active; ws.title = "Applications"
    ws.sheet_view.rightToLeft = True
    ws.append(COLS)
    for i, w in enumerate(WIDTHS, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
        c = ws.cell(1, i)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3A5F")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{ws.cell(1, len(COLS)).column_letter}1"
    for col, vals in (("طريقة الإرسال", "Email,WhatsApp,Both"), ("لغة السيرة", "AR,EN"),
                      ("نسخة السيرة", "Full,NoPhD"),
                      ("الحالة", "Sent,Replied,Interview,Rejected,Hired")):
        dv = DataValidation(type="list", formula1=f'"{vals}"', allow_blank=True)
        L = ws.cell(1, C[col]).column_letter
        dv.add(f"{L}2:{L}5000"); ws.add_data_validation(dv)
    wb.save(LOG); print("created:", LOG)


def rows(ws):
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, C["اسم الجهة"]).value:
            yield r


def find(ws, email=None, phone=None, name=None):
    e, p, n = norm_email(email), norm_phone(phone), norm_name(name)
    hits = []
    for r in rows(ws):
        why = []
        re_ = norm_email(ws.cell(r, C["الإيميل"]).value)
        rp = norm_phone(str(ws.cell(r, C["رقم الواتساب"]).value or ""))
        rn = norm_name(ws.cell(r, C["اسم الجهة"]).value)
        if e and re_ and e == re_: why.append("نفس الإيميل")
        if p and rp and (p == rp or (len(p) >= 8 and len(rp) >= 8 and (p.endswith(rp[-8:]) or rp.endswith(p[-8:])))):
            why.append("نفس الرقم")
        if n and rn and n == rn: why.append("نفس الاسم")
        elif n and rn and len(n) > 6 and (n in rn or rn in n): why.append("اسم مشابه")
        if why: hits.append((r, why))
    return hits


def show(ws, r, why):
    g = lambda k: ws.cell(r, C[k]).value or ""
    print(f"  صف {r}: {g('اسم الجهة')} | {g('الدولة')} | {g('الإيميل')} | {g('رقم الواتساب')} | "
          f"أُرسل بتاريخ {g('التاريخ')} عبر {g('طريقة الإرسال')} | الحالة {g('الحالة')}  ← {'، '.join(why)}")


def check(a):
    init() if not os.path.exists(LOG) else None
    ws = load_workbook(LOG)["Applications"]
    hits = find(ws, a.email, a.phone, a.name)
    if not hits:
        print("لا يوجد تطابق — لم يتم الإرسال لهذه الجهة سابقاً."); return 0
    print("⚠ تم الإرسال سابقاً لجهة مطابقة:")
    for r, why in hits: show(ws, r, why)
    return 1


def add(a):
    if not os.path.exists(LOG): init()
    wb = load_workbook(LOG); ws = wb["Applications"]
    today = datetime.date.today().isoformat()
    strong = [(r, w) for r, w in find(ws, a.email, a.phone, a.name) if w != ["اسم مشابه"]]
    if strong:
        r = strong[0][0]
        old = ws.cell(r, C["طريقة الإرسال"]).value
        if old and old != a.method and old != "Both":
            ws.cell(r, C["طريقة الإرسال"]).value = "Both"
            if a.email and not ws.cell(r, C["الإيميل"]).value: ws.cell(r, C["الإيميل"]).value = a.email
            if a.phone and not ws.cell(r, C["رقم الواتساب"]).value: ws.cell(r, C["رقم الواتساب"]).value = a.phone
            ws.cell(r, C["تاريخ آخر تحديث"]).value = today
            note = ws.cell(r, C["ملاحظات"]).value or ""
            ws.cell(r, C["ملاحظات"]).value = (note + f" | {a.method} بتاريخ {today}").strip(" |")
            wb.save(LOG); print(f"تم تحديث الصف {r} إلى Both"); return 0
        print("⚠ الجهة مسجلة مسبقاً بنفس الطريقة — لم تتم الإضافة:")
        show(ws, r, strong[0][1]); return 1
    n = sum(1 for _ in rows(ws)) + 1
    vals = {"#": n, "التاريخ": today, "اسم الجهة": a.name, "الدولة": a.country, "المدينة": a.city,
            "نوع الجهة": a.type, "الوظيفة": a.position or "طلب مفتوح", "الإيميل": a.email,
            "رقم الواتساب": a.phone, "طريقة الإرسال": a.method, "لغة السيرة": a.lang,
            "نسخة السيرة": a.cv, "موضوع الإيميل": a.subject, "المصدر/الرابط": a.source,
            "الحالة": "Sent", "تاريخ آخر تحديث": today, "ملاحظات": a.notes}
    r = ws.max_row + 1
    for k, v in vals.items(): ws.cell(r, C[k]).value = v
    wb.save(LOG); print(f"تمت إضافة الصف {r}: {a.name}"); return 0


def status(a):
    wb = load_workbook(LOG); ws = wb["Applications"]
    ws.cell(a.row, C["الحالة"]).value = a.status
    ws.cell(a.row, C["تاريخ آخر تحديث"]).value = datetime.date.today().isoformat()
    if a.notes:
        old = ws.cell(a.row, C["ملاحظات"]).value or ""
        ws.cell(a.row, C["ملاحظات"]).value = (old + " | " + a.notes).strip(" |")
    wb.save(LOG); print("updated row", a.row); return 0


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("init")
    c = sp.add_parser("check")
    for f in ("--email", "--phone", "--name"): c.add_argument(f)
    d = sp.add_parser("add")
    d.add_argument("--name", required=True); d.add_argument("--country", required=True)
    d.add_argument("--method", required=True, choices=["Email", "WhatsApp"])
    for f in ("--city", "--type", "--position", "--email", "--phone", "--subject", "--source", "--notes"):
        d.add_argument(f)
    d.add_argument("--lang", choices=["AR", "EN"]); d.add_argument("--cv", choices=["Full", "NoPhD"])
    s = sp.add_parser("status")
    s.add_argument("--row", type=int, required=True); s.add_argument("--status", required=True)
    s.add_argument("--notes")
    a = ap.parse_args()
    if a.cmd == "init": init(); return 0
    return {"check": check, "add": add, "status": status}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
