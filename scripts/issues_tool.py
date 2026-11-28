# -*- coding: utf-8 -*-
"""سجل الأخطاء والعمليات المتعثرة: output/issues_log.xlsx

  python3 scripts/issues_tool.py add --op "..." --reason "..." --need "ما المطلوب من المستخدم" [--kind خطأ|موافقة]
  python3 scripts/issues_tool.py resolve --row N [--notes "..."]
  python3 scripts/issues_tool.py list            # يعرض المفتوح فقط
"""
import argparse, datetime, os, sys
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "output", "issues_log.xlsx")
COLS = ["#", "التاريخ", "النوع", "العملية", "السبب / رسالة الخطأ", "المطلوب من المستخدم", "الحالة", "تاريخ الحل", "ملاحظات"]
W = [5, 12, 10, 45, 60, 50, 10, 12, 30]


def wb_open():
    if os.path.exists(LOG):
        return load_workbook(LOG)
    wb = Workbook(); ws = wb.active; ws.title = "Issues"; ws.sheet_view.rightToLeft = True
    ws.append(COLS)
    for i, w in enumerate(W, 1):
        c = ws.cell(1, i); ws.column_dimensions[c.column_letter].width = w
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="8B1E1E")
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.freeze_panes = "A2"
    return wb


def add(a):
    wb = wb_open(); ws = wb.active
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 4).value == a.op and ws.cell(r, 7).value == "مفتوح":
            print("موجود مسبقاً (مفتوح) في الصف", r); return
    ws.append([ws.max_row, datetime.date.today().isoformat(), a.kind, a.op, a.reason, a.need, "مفتوح", "", ""])
    for c in range(1, len(COLS) + 1):
        ws.cell(ws.max_row, c).alignment = Alignment(wrap_text=True, vertical="top")
    wb.save(LOG); print("أُضيف الصف", ws.max_row)


def resolve(a):
    wb = wb_open(); ws = wb.active
    ws.cell(a.row, 7).value = "تم الحل"; ws.cell(a.row, 8).value = datetime.date.today().isoformat()
    if a.notes: ws.cell(a.row, 9).value = a.notes
    wb.save(LOG); print("تم تحديث الصف", a.row)


def list_open(_):
    wb = wb_open(); ws = wb.active; n = 0
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 7).value == "مفتوح":
            n += 1
            print(f"[{r}] ({ws.cell(r,3).value}) {ws.cell(r,4).value}\n     السبب: {ws.cell(r,5).value}\n     المطلوب: {ws.cell(r,6).value}")
    print("عدد المفتوح:", n)


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    x = sp.add_parser("add"); x.add_argument("--op", required=True); x.add_argument("--reason", required=True)
    x.add_argument("--need", default=""); x.add_argument("--kind", default="خطأ", choices=["خطأ", "موافقة"])
    y = sp.add_parser("resolve"); y.add_argument("--row", type=int, required=True); y.add_argument("--notes")
    sp.add_parser("list")
    a = ap.parse_args(); {"add": add, "resolve": resolve, "list": list_open}[a.cmd](a)


if __name__ == "__main__":
    main()
