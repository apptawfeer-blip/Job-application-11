# -*- coding: utf-8 -*-
"""سجل مصادر البحث: output/sources_registry.xlsx

  python3 scripts/sources_tool.py add --name "..." --url "..." --countries "Jordan,UAE" --kind "دليل مدارس" \
        --status "تم السحب|تعذر|جزئي|قيد العمل" [--count N] [--notes "..."]
  python3 scripts/sources_tool.py sync      # يحدّث عدد الجهات لكل نطاق من ملفات الدول
  python3 scripts/sources_tool.py summary
"""
import argparse, datetime, glob, os, urllib.parse, collections
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "output", "sources_registry.xlsx")
COLS = ["#", "المصدر", "الرابط", "الدول", "النوع", "الحالة", "عدد الجهات المضافة", "تاريخ", "ملاحظات"]
W = [5, 40, 50, 22, 20, 12, 12, 12, 40]


def dom(u):
    u = str(u or "")
    return urllib.parse.urlparse(u if u.startswith("http") else "http://" + u).netloc.replace("www.", "").lower()


def wb_open():
    if os.path.exists(REG): return load_workbook(REG)
    wb = Workbook(); ws = wb.active; ws.title = "Sources"; ws.sheet_view.rightToLeft = True; ws.append(COLS)
    for i, w in enumerate(W, 1):
        c = ws.cell(1, i); ws.column_dimensions[c.column_letter].width = w
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F5F3A")
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.freeze_panes = "A2"; return wb


def add(a):
    wb = wb_open(); ws = wb.active
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 3).value == a.url:
            for col, v in ((2, a.name), (4, a.countries), (5, a.kind), (6, a.status), (7, a.count), (9, a.notes)):
                if v not in (None, ""): ws.cell(r, col).value = v
            ws.cell(r, 8).value = datetime.date.today().isoformat(); wb.save(REG); print("updated", r); return
    ws.append([ws.max_row, a.name, a.url, a.countries, a.kind, a.status, a.count, datetime.date.today().isoformat(), a.notes])
    wb.save(REG); print("added", ws.max_row)


def sync(_):
    cnt = collections.Counter()
    for p in glob.glob(os.path.join(ROOT, "output", "targets", "Targets_*.xlsx")):
        for row in load_workbook(p, read_only=True)["الجهات"].iter_rows(min_row=2, values_only=True):
            cnt[dom(row[10])] += 1
    wb = wb_open(); ws = wb.active
    for r in range(2, ws.max_row + 1):
        d = dom(ws.cell(r, 3).value)
        if d in cnt: ws.cell(r, 7).value = cnt[d]
    wb.save(REG); print("synced")


def summary(_):
    ws = wb_open().active; st = collections.Counter(ws.cell(r, 6).value for r in range(2, ws.max_row + 1))
    print("عدد المصادر:", ws.max_row - 1, dict(st))


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    x = sp.add_parser("add")
    for f in ("--name", "--url", "--countries", "--kind", "--status", "--notes"): x.add_argument(f, default="")
    x.add_argument("--count", type=int)
    sp.add_parser("sync"); sp.add_parser("summary")
    a = ap.parse_args(); {"add": add, "sync": sync, "summary": summary}[a.cmd](a)


if __name__ == "__main__":
    main()
