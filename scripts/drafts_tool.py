# -*- coding: utf-8 -*-
"""Build email drafts (HTML + plain text) for a batch and keep a batch log.

  python3 scripts/drafts_tool.py build   --batch 01      # writes output/drafts/batch_01/*.html|.txt + batch_01.json
  python3 scripts/drafts_tool.py record  --batch 01 --id N --draft-id X --url U   # store Gmail draft id
  python3 scripts/drafts_tool.py excel   --batch 01      # output/drafts/batch_01.xlsx (review sheet)
"""
import argparse, hashlib, html, json, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DR = os.path.join(ROOT, "output", "drafts")
CV = {("AR", "Full"): "Amer_AlSaaideh_CV_Arabic.pdf", ("AR", "NoPhD"): "Amer_AlSaaideh_CV_Arabic_S.pdf",
      ("EN", "Full"): "Amer_AlSaaideh_CV_English.pdf", ("EN", "NoPhD"): "Amer_AlSaaideh_CV_English_S.pdf"}
GROUPS = "ABCDE"
# the filename the recipient sees: same for both versions, never reveals the _S (schools/universities) variant
SEND_NAME = {"AR": "Amer_AlSaaideh_CV_Arabic.pdf", "EN": "Amer_AlSaaideh_CV_English.pdf"}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def sig_block(e):
    """closing line + signature: (html, plain-text lines). Shared by Gmail drafts and the sending desk."""
    rtl = e["lang"] == "AR"
    close = "مع خالص التقدير،" if rtl else "Kind regards,"
    S = json.load(open(os.path.join(DR, "signature.json"), encoding="utf-8"))
    L = S["ar" if rtl else "en"]; gulf = e.get("country") not in (None, "Jordan")
    avail = L["avail_gulf"] if gulf else L["avail_local"]
    link = 'style="color:#1f5fa8;text-decoration:none;"'
    rows_ = [(L["lbl"]["phone"], f'<a href="tel:{S["phone"]}" {link}>{S["phone_display"]}</a>', S["phone_display"]),
             (L["lbl"]["wa"], f'<a href="https://wa.me/{S["whatsapp"]}" {link}>{L["wa_text"]}</a>', "https://wa.me/" + S["whatsapp"]),
             (L["lbl"]["email"], f'<a href="mailto:{S["email"]}" {link}>{S["email"]}</a>', S["email"])]
    if S.get("linkedin"):
        rows_.append((L["lbl"]["li"], f'<a href="{S["linkedin"]}" {link}>{L.get("li_text","LinkedIn")}</a>', S["linkedin"]))
    rows_.append((L["lbl"]["orcid"], f'<a href="{S["orcid"]}" {link}>{S["orcid"].replace("https://","")}</a>', S["orcid"]))
    cells = "".join(f'<tr><td style="color:#888;font-size:12px;padding:1px {"0 1px 10px" if rtl else "10px 1px 0"};white-space:nowrap;">{lb}</td>'
                    f'<td style="font-size:13px;padding:1px 0;" dir="ltr">{v}</td></tr>' for lb, v, _ in rows_)
    bar = "border-right:3px solid #1f3a5f;padding-right:12px;" if rtl else "border-left:3px solid #1f3a5f;padding-left:12px;"
    sig_html = (f'<p style="margin:18px 0 10px 0;">{close}</p>'
                f'<div style="{bar}margin-top:4px;">'
                f'<div style="font-weight:bold;color:#1f3a5f;font-size:16px;">{html.escape(L["name"])}</div>'
                f'<div style="color:#444;font-size:13px;margin-top:2px;">{html.escape(L["title"])}</div>'
                f'<div style="color:#666;font-size:12px;margin-top:2px;">{html.escape(L["creds"])}</div>'
                f'<table cellpadding="0" cellspacing="0" style="margin-top:8px;border-collapse:collapse;">{cells}</table>'
                f'<div style="color:#1f7a3f;font-size:12px;font-weight:bold;margin-top:8px;">{html.escape(avail)}</div></div>')
    lines = [close, L["name"], L["title"], L["creds"]] + [f"{lb}: {t}" for lb, _, t in rows_] + [avail]
    return sig_html, lines


def editable_text(e):
    """the part the user edits on the sending desk: paragraphs separated by blank lines, list items as '- ' lines"""
    t = "\n\n".join(e["paras"])
    if e.get("items"): t += "\n\n" + "\n".join("- " + x for x in e["items"])
    if e.get("after"): t += "\n\n" + "\n\n".join(e["after"])
    return t


def render(e, sig=None):
    rtl = e["lang"] == "AR"
    d = 'dir="rtl" ' if rtl else ""
    align = "right" if rtl else "left"
    font = "Tahoma, Arial, sans-serif" if rtl else "Arial, Helvetica, sans-serif"
    p = lambda t: f'<p style="margin:0 0 14px 0;">{html.escape(t)}</p>'
    parts = [p(t) for t in e["paras"]]
    if e.get("items"):
        lis = "".join(f'<li style="margin:0 0 8px 0;">{html.escape(t)}</li>' for t in e["items"])
        pad = "padding:0 22px 0 0;" if rtl else "padding:0 0 0 22px;"
        parts.append(f'<ul style="margin:0 0 14px 0;{pad}">{lis}</ul>')
    parts += [p(t) for t in e.get("after", [])]
    sig_html, lines = sig_block(e)
    body = (f'<div {d}style="font-family:{font};font-size:15px;line-height:1.7;color:#222;text-align:{align};max-width:640px;">'
            + "".join(parts) + sig_html + "</div>")
    text = editable_text(e) + "\n\n" + lines[0] + "\n" + "\n".join(lines[1:])
    return body, text


def build(a):
    sys.path.insert(0, DR)
    mod = __import__(f"batch_{a.batch}_emails")
    sel = {x["id"]: x for x in json.load(open(os.path.join(DR, f"batch_{a.batch}_selection.json"), encoding="utf-8"))}
    out_dir = os.path.join(DR, f"batch_{a.batch}"); os.makedirs(out_dir, exist_ok=True)
    rows = []
    for i, e in enumerate(mod.EMAILS):
        x = sel[e["id"]]; sig = mod.AR_SIG if e["lang"] == "AR" else mod.EN_SIG
        e = dict(e, country=x["country"]); h, t = render(e, sig)
        cvf = os.path.join(ROOT, "cv", CV[(e["lang"], e["cv"])])
        open(os.path.join(out_dir, f"{e['id']:02d}.html"), "w", encoding="utf-8").write(h)
        open(os.path.join(out_dir, f"{e['id']:02d}.txt"), "w", encoding="utf-8").write(f"To: {x['email']}\nSubject: {e['subject']}\nAttachment: {os.path.basename(cvf)}\n\n{t}")
        rows.append({"id": e["id"], "group": GROUPS[i // 30], "country": x["country"], "row": x["row"], "name": x["name"],
                     "type": x["type"], "city": x["city"], "email": x["email"], "lang": e["lang"], "cv": e["cv"],
                     "cv_file": cvf, "cv_sha": sha(cvf), "send_name": SEND_NAME[e["lang"]], "subject": e["subject"], "html": h, "text": t,
                     "draft_id": "", "draft_url": "", "status": "جاهز"})
    p = os.path.join(DR, f"batch_{a.batch}.json")
    old = {r["id"]: r for r in json.load(open(p, encoding="utf-8"))} if os.path.exists(p) else {}
    for r in rows:
        if r["id"] in old and old[r["id"]].get("draft_id"):
            for k in ("draft_id", "draft_url", "status"): r[k] = old[r["id"]][k]
    json.dump(rows, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("built", len(rows))


def record(a):
    p = os.path.join(DR, f"batch_{a.batch}.json"); rows = json.load(open(p, encoding="utf-8"))
    for r in rows:
        if r["id"] == a.id: r.update(draft_id=a.draft_id, draft_url=a.url, status="مسودة في Gmail")
    json.dump(rows, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("recorded", a.id)


def excel(a):
    rows = json.load(open(os.path.join(DR, f"batch_{a.batch}.json"), encoding="utf-8"))
    wb = Workbook(); ws = wb.active; ws.title = "Batch"; ws.sheet_view.rightToLeft = True
    cols = ["#", "المجموعة (يوم الإرسال)", "الدولة", "الجهة", "النوع", "المدينة", "الإيميل", "اللغة", "السيرة المرفقة", "الموضوع", "رابط المسودة", "الحالة"]
    ws.append(cols)
    for i, w in enumerate([5, 12, 10, 40, 16, 12, 34, 7, 34, 50, 40, 16], 1):
        c = ws.cell(1, i); ws.column_dimensions[c.column_letter].width = w
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3A5F"); c.alignment = Alignment(wrap_text=True)
    for r in rows:
        ws.append([r["id"], r["group"], r["country"], r["name"], r["type"], r["city"], r["email"], r["lang"],
                   os.path.basename(r["cv_file"]), r["subject"], r["draft_url"], r["status"]])
    ws.freeze_panes = "A2"; wb.save(os.path.join(DR, f"batch_{a.batch}.xlsx")); print("excel saved")


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("build", "excel"):
        x = sp.add_parser(n); x.add_argument("--batch", required=True)
    y = sp.add_parser("record"); y.add_argument("--batch", required=True); y.add_argument("--id", type=int, required=True)
    y.add_argument("--draft-id", required=True); y.add_argument("--url", default="")
    a = ap.parse_args(); {"build": build, "record": record, "excel": excel}[a.cmd](a)


if __name__ == "__main__":
    main()
