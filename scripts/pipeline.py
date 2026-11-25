# -*- coding: utf-8 -*-
"""أداة الحالة الموحّدة لروتين "تقديم" (إيميل / واتساب).

السجل الدائم: output/pipeline_ledger.json  (حدث لكل جهة/قناة: drafted|queued|sent|bounced|replied)
مجلد كل تشغيل: output/runs/<YYYY-MM-DD_HHMM>_<channel>/

  quota       --channel email|whatsapp                     الحصة المسموحة اليوم حسب config/sending_policy.json
  select      --channel X --count N [--countries a,b]      اختيار جهات من دول مختلفة -> run/selection.json
  build       --run DIR                                    (إيميل) يبني HTML/نص لكل رسالة من run/texts.json -> run/drafts.json
  record      --run DIR --id N --draft-id X                تسجيل draft id بعد create_draft
  wa-queue    --run DIR                                    (واتساب) يكتب output/whatsapp/queue_<date>.json/.csv من run/texts.json
  mark        --run DIR                                    تحديث ملفات الدول (عمود 14) + السجل الدائم
  sync-sent   --file sent.json                             [{"to":..,"date":..,"subject":..}] من Gmail in:sent
  sync-wa                                                  يقرأ output/whatsapp/sent_*.json (من الإضافة)
  sync-bounces --file bounces.json                         ["email", ...]
  sync-replies --file replies.json                         [{"from":..,"date":..,"subject":..}]
  stats                                                    output/dashboard/data.json + output/dashboard.xlsx
  migrate-batch01                                          إدخال مسودات batch_01 في السجل الدائم
"""
import argparse, sys, csv, datetime, glob, json, os, random, re, sys
from zoneinfo import ZoneInfo
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import log_tool, targets_tool, issues_tool  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY = json.load(open(os.path.join(ROOT, "config", "sending_policy.json"), encoding="utf-8"))
LEDGER = os.path.join(ROOT, "output", "pipeline_ledger.json")
RUNS = os.path.join(ROOT, "output", "runs")
WA_DIR = os.path.join(ROOT, "output", "whatsapp")
DASH = os.path.join(ROOT, "output", "dashboard")
TZ = ZoneInfo(POLICY.get("timezone", "Asia/Amman"))
COUNTRIES = list(targets_tool.COUNTRY_AR)
TYPE_ORDER = {"مركز تربية خاصة": 0, "جمعية": 1, "منظمة": 1, "مدرسة": 2, "جامعة": 3, "جهة حكومية": 4}
PLACEHOLDER = re.compile(r"^(info|test|example|admin)?@|^[a-z]{1,4}@(gmail|hotmail|yahoo)\.", re.I)


INTL = re.compile(r"international|british|american|\bIB\b|cambridge|canadian|french|german|indian|pakistani|filipino|"
                  r"montessori international|embassy|unicef|unesco|unhcr|unrwa|\bUN\b|united nations|save the children|"
                  r"handicap international|humanity|world vision|qatar foundation|\bQF\b|دولي|بريطاني|أمريكي|امريكي|البكالوريا الدولية", re.I)


def lang_for(name, typ, website="", source=""):
    """user's rule: Arabic for everyone except international bodies (international schools, international organizations)"""
    return "EN" if INTL.search(" ".join(str(x or "") for x in (name, typ, website))) else "AR"


def today():
    return datetime.datetime.now(TZ).date()


def load_ledger():
    return json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else []


def save_ledger(L):
    json.dump(L, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def key(country, row):
    return f"{country}:{row}"


# ---------------- quota ----------------
def allowed_today(channel, d=None):
    p = POLICY[channel]; d = d or today()
    start = datetime.date.fromisoformat(p["start_date"])
    if d < start:
        week = 1
    else:
        week = (d - start).days // 7 + 1
    table = {int(k): v for k, v in p["daily_by_week"].items()}
    n = table.get(week, table[max(table)])
    return min(n, p["absolute_max_per_day"]), week


def used_today(channel, L=None):
    L = L if L is not None else load_ledger(); t = today().isoformat()
    st = {"email": ("drafted", "sent"), "whatsapp": ("queued", "sent")}[channel]
    return sum(1 for e in L if e["channel"] == channel and e["status"] in st and e.get("date") == t and not e.get("migrated"))


def backlog(channel, L=None):
    """prepared but not yet sent by the user (drafts in Gmail / ready WhatsApp messages)"""
    L = L if L is not None else load_ledger()
    st = {"email": "drafted", "whatsapp": "queued"}[channel]
    return sum(1 for e in L if e["channel"] == channel and e["status"] == st)


def quota(a):
    allowed, week = allowed_today(a.channel); used = used_today(a.channel); bl = backlog(a.channel)
    alerts = blocked(a.channel)
    days = round(bl / allowed, 1) if allowed else 0
    if days >= 3:
        alerts.append(f"لديك {bl} رسالة جاهزة لم تُرسل بعد (≈ {days} يوم إرسال) – الأفضل إرسالها قبل تجهيز المزيد")
    out = {"channel": a.channel, "week": week, "allowed_today": allowed, "used_today": used,
           "remaining_today": max(0, allowed - used), "backlog_unsent": bl, "backlog_days": days, "gap_minutes": POLICY[a.channel]["gap_minutes"],
           "stop": any("أوقف" in x or "خفّف" in x for x in alerts), "alerts": alerts}
    print(json.dumps(out, ensure_ascii=False, indent=1)); return out


def blocked(channel):
    L = load_ledger(); alerts = []
    if channel == "email":
        p = POLICY["email"]; last = [e for e in L if e["channel"] == "email" and e["status"] in ("sent", "bounced")][-p["bounce_window"]:]
        if len(last) >= 10:
            rate = sum(1 for e in last if e["status"] == "bounced") / len(last)
            if rate > p["stop_if_bounce_rate_over"]:
                alerts.append(f"نسبة الارتداد {rate:.0%} أعلى من {p['stop_if_bounce_rate_over']:.0%} – أوقف الإرسال ونظّف القوائم")
    else:
        p = POLICY["whatsapp"]; sent = [e for e in L if e["channel"] == "whatsapp" and e["status"] in ("sent", "replied")]
        if len(sent) >= 50:
            rate = sum(1 for e in sent if e["status"] == "replied") / len(sent)
            if rate < p["min_reply_rate_after_50"]:
                alerts.append(f"نسبة الردود على واتساب {rate:.0%} منخفضة – خطر السقف الشهري، خفّف الإرسال")
    return alerts


# ---------------- select ----------------
def contacted_keys(L):
    return {key(e["country"], e["row"]) for e in L}


def select(a):
    L = load_ledger(); taken = contacted_keys(L)
    lw = load_workbook(log_tool.LOG)["Applications"] if os.path.exists(log_tool.LOG) else None
    countries = a.countries.split(",") if a.countries else COUNTRIES
    pools = {}
    for c in countries:
        ws = load_workbook(targets_tool.path(c), read_only=True)["الجهات"]; pool = []
        for r, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            row = list(row) + [None] * 20
            name, typ, phone, wa, email = row[1], row[2], row[3], row[4], row[5]
            status14, rel, wast = str(row[13] or ""), row[15], str(row[16] or "")
            if not name or status14 or key(c, r) in taken: continue
            if a.channel == "email":
                em = str(email or "").split(",")[0].strip()
                if not re.match(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$", em) or PLACEHOLDER.search(em): continue
                contact = em
            else:
                if not (wast.startswith("مؤكد") or wast.startswith("جوال")): continue
                contact = str(wa).split(",")[0].strip()
            if lw is not None and log_tool.find(lw, contact if "@" in contact else None, None if "@" in contact else contact, None):
                continue
            score = (0 if rel == "عالية" else 1 if rel == "متوسطة" else 2, TYPE_ORDER.get(typ, 5),
                     0 if (a.channel == "email" or wast.startswith("مؤكد")) else 1)
            pool.append((score, r, {"country": c, "row": r, "name": name, "type": typ, "email": email if a.channel == "email" else "",
                                     "whatsapp": contact if a.channel == "whatsapp" else "", "phone": phone, "city": row[7],
                                     "website": row[8], "source": row[10], "lang": lang_for(name, typ, row[8]), "cv": row[12], "relevance": rel}))
        pool.sort(key=lambda x: (x[0], x[1])); pools[c] = [p[2] for p in pool]
    picked, i = [], 0
    while len(picked) < a.count and any(pools.values()):
        c = countries[i % len(countries)]; i += 1
        if pools.get(c): picked.append(pools[c].pop(0))
    stamp = datetime.datetime.now(TZ).strftime("%Y-%m-%d_%H%M")
    run = os.path.join(RUNS, f"{stamp}_{a.channel}"); os.makedirs(run, exist_ok=True)
    for n, p in enumerate(picked, 1): p["id"] = n
    json.dump({"channel": a.channel, "created": stamp, "targets": picked}, open(os.path.join(run, "selection.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(run); print(f"selected {len(picked)}:", {c: sum(1 for p in picked if p['country'] == c) for c in countries})
    return run


# ---------------- email build ----------------
def build(a):
    import drafts_tool
    sel = {t["id"]: t for t in json.load(open(os.path.join(a.run, "selection.json"), encoding="utf-8"))["targets"]}
    texts = json.load(open(os.path.join(a.run, "texts.json"), encoding="utf-8"))
    sig = None; out = []
    allowed, _ = allowed_today("email"); gmin, gmax = POLICY["email"]["gap_minutes"]
    for i, e in enumerate(texts):
        t = sel[e["id"]]; e = dict(e, country=t["country"])
        h, txt = drafts_tool.render(e, sig)
        cvf = os.path.join(ROOT, "cv", drafts_tool.CV[(e["lang"], e["cv"])])
        out.append({"id": e["id"], "country": t["country"], "row": t["row"], "name": t["name"], "type": t["type"],
                    "to": str(t["email"]).split(",")[0].strip(), "subject": e["subject"], "html": h, "text": txt,
                    "lang": e["lang"], "cv": e["cv"], "cv_file": cvf, "cv_sha": drafts_tool.sha(cvf),
                    "send_name": drafts_tool.SEND_NAME[e["lang"]], "send_day": i // max(1, allowed) + 1,
                    "gap_minutes": random.randint(gmin, gmax), "draft_id": ""})
    json.dump(out, open(os.path.join(a.run, "drafts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in out:
        open(os.path.join(a.run, f"{r['id']:02d}.txt"), "w", encoding="utf-8").write(
            f"To: {r['to']}\nSubject: {r['subject']}\nAttachment: {r['send_name']}  (file: {os.path.basename(r['cv_file'])})\n\n{r['text']}")
    print("built", len(out))


def record(a):
    p = os.path.join(a.run, "drafts.json"); rows = json.load(open(p, encoding="utf-8"))
    for r in rows:
        if r["id"] == a.id: r["draft_id"] = a.draft_id
    json.dump(rows, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("recorded", a.id)


# ---------------- whatsapp queue ----------------
def wa_queue(a):
    sel = {t["id"]: t for t in json.load(open(os.path.join(a.run, "selection.json"), encoding="utf-8"))["targets"]}
    texts = json.load(open(os.path.join(a.run, "texts.json"), encoding="utf-8"))
    import drafts_tool
    gmin, gmax = POLICY["whatsapp"]["gap_minutes"]; start = POLICY["whatsapp"]["send_window_local"][0]
    t0 = datetime.datetime.combine(today(), datetime.time.fromisoformat(start)); items = []
    for e in texts:
        t = sel[e["id"]]; phone = re.sub(r"\D", "", t["whatsapp"])
        cvf = os.path.join(ROOT, "cv", drafts_tool.CV[(e["lang"], e["cv"])])
        items.append({"id": e["id"], "name": t["name"], "country": t["country"], "row": t["row"], "phone": phone,
                      "wa_link": f"https://wa.me/{phone}", "text": e["text"], "lang": e["lang"], "cv": e["cv"], "type": t.get("type", ""),
                      "cv_path": os.path.relpath(cvf, ROOT).replace("\\", "/"), "cv_send_name": drafts_tool.SEND_NAME[e["lang"]],
                      "suggested_time": t0.strftime("%H:%M"), "status": "ready", "sent_at": ""})
        t0 += datetime.timedelta(minutes=random.randint(gmin, gmax))
    d = today().isoformat(); base = os.path.join(WA_DIR, f"queue_{d}_{os.path.basename(a.run)}")
    json.dump({"date": d, "run": os.path.basename(a.run), "items": items}, open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(base + ".csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(items[0].keys()) if items else ["id"]); w.writeheader(); w.writerows(items)
    json.dump(items, open(os.path.join(a.run, "queue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(base + ".json", len(items))


# ---------------- mark ----------------
def set_col14(country, row, value):
    p = targets_tool.path(country); wb = load_workbook(p); ws = wb["الجهات"]; ws.cell(row, 14).value = value; wb.save(p)


def mark(a):
    run = os.path.basename(a.run); L = load_ledger(); d = today().isoformat()
    ch = "email" if run.endswith("_email") else "whatsapp"
    if ch == "email":
        dp = os.path.join(a.run, "drafts.json")
        if os.path.exists(dp):  # legacy: drafts created by Claude in Gmail
            items = [r for r in json.load(open(dp, encoding="utf-8")) if r.get("draft_id")]
        else:  # sending desk: queued on the desk, the draft is created from the desk when the user opens it
            sel = {t["id"]: t for t in json.load(open(os.path.join(a.run, "selection.json"), encoding="utf-8"))["targets"]}
            items = [dict(sel[e["id"]], to=str(sel[e["id"]]["email"]).split(",")[0].strip(), subject=e["subject"], lang=e["lang"], cv=e["cv"])
                     for e in json.load(open(os.path.join(a.run, "texts.json"), encoding="utf-8"))]
    else:
        items = json.load(open(os.path.join(a.run, "queue.json"), encoding="utf-8"))
    by_country = {}
    for r in items:
        st = "drafted" if ch == "email" else "queued"
        L.append({"date": d, "run": run, "channel": ch, "status": st, "country": r["country"], "row": r["row"], "name": r["name"],
                  "email": r.get("to", ""), "phone": r.get("phone", ""), "subject": r.get("subject", ""), "draft_id": r.get("draft_id", ""),
                  "lang": r["lang"], "cv": r.get("cv", ""), "type": r.get("type", ""), "send_day": r.get("send_day", 1)})
        by_country.setdefault(r["country"], []).append(r)
    for c, rs in by_country.items():
        p = targets_tool.path(c); wb = load_workbook(p); ws = wb["الجهات"]
        for r in rs:
            ws.cell(r["row"], 14).value = (f"مكتب الإرسال – {run}" if ch == "email" else f"واتساب جاهز – {run}")
        wb.save(p)
    save_ledger(L); print("marked", len(items))


# ---------------- sync ----------------
def _log_send(e, method, date):
    ns = argparse.Namespace(name=e["name"], country=targets_tool.COUNTRY_AR.get(e["country"], e["country"]), method=method,
                            city=None, type=e.get("type"), position=None, email=e.get("email") or None, phone=e.get("phone") or None,
                            subject=e.get("subject"), source=e.get("run"), notes=f"sent {date}", lang=e.get("lang"),
                            cv=("NoPhD" if e.get("cv") == "NoPhD" else "Full") if e.get("cv") else None)
    log_tool.add(ns)


def sync_sent(a):
    sent = json.load(open(a.file, encoding="utf-8")); L = load_ledger(); n = 0
    for s in sent:
        to = log_tool.norm_email(s.get("to"))
        for e in L:
            if e["channel"] == "email" and e["status"] == "drafted" and log_tool.norm_email(e["email"]) == to:
                e["status"] = "sent"; e["sent_date"] = (s.get("date") or today().isoformat())[:10]
                _log_send(e, "Email", e["sent_date"]); set_col14(e["country"], e["row"], "أُرسل إيميل"); n += 1
    save_ledger(L); print("synced sent:", n)


def sync_wa(a):
    L = load_ledger(); n = 0
    for f in glob.glob(os.path.join(WA_DIR, "sent_*.json")) + glob.glob(os.path.join(WA_DIR, "queue_*.json")):
        data = json.load(open(f, encoding="utf-8")); items = data["items"] if isinstance(data, dict) else data
        for it in items:
            if it.get("status") != "sent": continue
            ph = log_tool.norm_phone(it.get("phone"))
            for e in L:
                if e["channel"] == "whatsapp" and e["status"] == "queued" and log_tool.norm_phone(e["phone"]) == ph:
                    e["status"] = "sent"; e["sent_date"] = (it.get("sent_at") or today().isoformat())[:10]
                    _log_send(e, "WhatsApp", e["sent_date"]); set_col14(e["country"], e["row"], "أُرسل واتساب"); n += 1
    save_ledger(L); print("synced whatsapp:", n)


def sync_bounces(a):
    bad = {log_tool.norm_email(x) for x in json.load(open(a.file, encoding="utf-8"))}; L = load_ledger(); n = 0
    for e in L:
        if e["channel"] == "email" and log_tool.norm_email(e["email"]) in bad and e["status"] != "bounced":
            e["status"] = "bounced"; set_col14(e["country"], e["row"], "ارتد – إيميل غير صالح"); n += 1
            issues_tool.add(argparse.Namespace(op=f"ارتداد إيميل: {e['name']} ({e['email']})", reason="Mail Delivery Subsystem",
                                               need="لا شيء – استُبعد الإيميل؛ جرّب الواتساب لهذه الجهة إن وُجد", kind="خطأ"))
    save_ledger(L); print("bounced:", n)


def sync_replies(a):
    rep = json.load(open(a.file, encoding="utf-8")); L = load_ledger(); n = 0
    for r in rep:
        fr = log_tool.norm_email(r.get("from"))
        for e in L:
            if e["channel"] == "email" and log_tool.norm_email(e["email"]) == fr and e["status"] in ("sent", "drafted"):
                e["status"] = "replied"; e["reply_date"] = (r.get("date") or "")[:10]; e["reply_subject"] = r.get("subject", ""); n += 1
                set_col14(e["country"], e["row"], "ردّت الجهة")
    save_ledger(L); print("replies:", n)


# ---------------- stats / dashboard ----------------
def remaining_by_country():
    L = load_ledger(); taken = contacted_keys(L); res = {}
    for c in COUNTRIES:
        ws = load_workbook(targets_tool.path(c), read_only=True)["الجهات"]; em = wa = tot = 0
        for r, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            row = list(row) + [None] * 20
            if not row[1] or str(row[13] or "") or key(c, r) in taken: continue
            tot += 1
            if re.match(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+", str(row[5] or "")): em += 1
            if str(row[16] or "").startswith(("مؤكد", "جوال")): wa += 1
        res[c] = {"remaining": tot, "email_ready": em, "whatsapp_ready": wa}
    return res


def weeks_needed(channel, n):
    p = POLICY[channel]; start = datetime.date.fromisoformat(p["start_date"]); d = max(today(), start)
    work = set(POLICY["workdays"]); days = 0; left = n
    while left > 0 and days < 3650:
        if d.strftime("%a") in work:
            left -= allowed_today(channel, d)[0]
        d += datetime.timedelta(days=1); days += 1
    return round(days / 7, 1)


def stats(_=None):
    L = load_ledger(); t = today(); wk0 = t - datetime.timedelta(days=t.weekday() + 1 if t.weekday() != 6 else 0)
    def count(ch, st, since=None, field="date"):
        return sum(1 for e in L if e["channel"] == ch and e["status"] in st and (since is None or (e.get(field) or e.get("date", "")) >= since))
    rem = remaining_by_country()
    daily = {}
    z = lambda: {"email_prepared": 0, "email_sent": 0, "whatsapp_prepared": 0, "whatsapp_sent": 0}
    for e in L:
        daily.setdefault(e["date"], z())[e["channel"] + "_prepared"] += 1
        if e.get("sent_date"):
            daily.setdefault(e["sent_date"], z())[e["channel"] + "_sent"] += 1
    issues = []
    if os.path.exists(issues_tool.LOG):
        ws = load_workbook(issues_tool.LOG).active
        issues = [{"row": r, "kind": ws.cell(r, 3).value, "op": ws.cell(r, 4).value, "need": ws.cell(r, 6).value}
                  for r in range(2, ws.max_row + 1) if ws.cell(r, 7).value == "مفتوح"]
    q = {ch: dict(zip(("allowed", "week"), allowed_today(ch)), used=used_today(ch, L)) for ch in ("email", "whatsapp")}
    pending = {"drafts_waiting_send": count("email", ("drafted",)), "whatsapp_ready": count("whatsapp", ("queued",)),
               "replies": [e for e in L if e["status"] == "replied"][-20:]}
    alerts = blocked("email") + blocked("whatsapp")
    for ch, lbl in (("email", "مسودة إيميل"), ("whatsapp", "رسالة واتساب")):
        bl = backlog(ch, L); al = q[ch]["allowed"]
        if al and bl / al >= 3:
            alerts.append(f"{bl} {lbl} جاهزة لم تُرسل بعد (≈ {bl / al:.1f} يوم إرسال بالحصة الحالية)")
    data = {"generated": datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M"), "quota": q,
            "today": {"email_drafted": count("email", ("drafted", "sent", "bounced", "replied"), t.isoformat()),
                      "email_sent": count("email", ("sent", "replied", "bounced"), t.isoformat(), "sent_date"),
                      "whatsapp_queued": count("whatsapp", ("queued", "sent", "replied"), t.isoformat()),
                      "whatsapp_sent": count("whatsapp", ("sent", "replied"), t.isoformat(), "sent_date")},
            "week": {"email_sent": count("email", ("sent", "replied", "bounced"), wk0.isoformat(), "sent_date"),
                     "whatsapp_sent": count("whatsapp", ("sent", "replied"), wk0.isoformat(), "sent_date")},
            "totals": {s: sum(1 for e in L if e["status"] == s) for s in ("drafted", "queued", "sent", "replied", "bounced")},
            "remaining": rem,
            "weeks_left": {"email": weeks_needed("email", sum(v["email_ready"] for v in rem.values())),
                           "whatsapp": weeks_needed("whatsapp", sum(v["whatsapp_ready"] for v in rem.values()))},
            "daily": [{"date": k, **v} for k, v in sorted(daily.items())][-30:],
            "pending": pending, "alerts": alerts, "open_issues": issues}
    os.makedirs(DASH, exist_ok=True)
    json.dump(data, open(os.path.join(DASH, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_xlsx(data); write_flat(data); print(json.dumps({k: data[k] for k in ("quota", "today", "week", "totals", "weeks_left")}, ensure_ascii=False))
    return data


AR_C = {"Jordan": "الأردن", "Qatar": "قطر", "Saudi": "السعودية", "UAE": "الإمارات", "Kuwait": "الكويت", "Oman": "عُمان", "Bahrain": "البحرين"}


def streak(daily):
    """consecutive days (ending today or yesterday) with at least one message actually sent"""
    sent = {r["date"] for r in daily if r.get("email_sent", 0) + r.get("whatsapp_sent", 0) > 0}
    d = today(); n = 0
    if d.isoformat() not in sent: d -= datetime.timedelta(days=1)
    while d.isoformat() in sent:
        n += 1; d -= datetime.timedelta(days=1)
    return n


def write_flat(d):
    """flat row files for the web dashboard (one JSON array per dataset)"""
    q, tt, wk = d["quota"], d["totals"], d["week"]
    summary = [{"generated": d["generated"],
                "email_allowed": q["email"]["allowed"], "email_used": q["email"]["used"], "email_week": q["email"]["week"],
                "wa_allowed": q["whatsapp"]["allowed"], "wa_used": q["whatsapp"]["used"], "wa_week": q["whatsapp"]["week"],
                "drafts_waiting": d["pending"]["drafts_waiting_send"], "wa_waiting": d["pending"]["whatsapp_ready"],
                "sent_total": tt["sent"] + tt["replied"], "replied": tt["replied"], "bounced": tt["bounced"],
                "week_email_sent": wk["email_sent"], "week_wa_sent": wk["whatsapp_sent"],
                "weeks_left_email": d["weeks_left"]["email"], "weeks_left_wa": d["weeks_left"]["whatsapp"],
                "remaining_total": sum(v["remaining"] for v in d["remaining"].values()),
                "alerts": len(d["alerts"]), "open_issues": len(d["open_issues"]),
                "today_email_sent": d["today"]["email_sent"], "today_wa_sent": d["today"]["whatsapp_sent"],
                "contacted_total": sum(tt.values()),
                "all_total": sum(tt.values()) + sum(v["remaining"] for v in d["remaining"].values()),
                "streak": streak(d["daily"])}]
    countries = [{"country": AR_C.get(c, c), **v} for c, v in d["remaining"].items()]
    alerts = [{"kind": "تنبيه", "text": a, "need": ""} for a in d["alerts"]] + \
             [{"kind": i["kind"] or "", "text": i["op"] or "", "need": i["need"] or ""} for i in d["open_issues"]]
    for name, rows in (("summary", summary), ("countries", countries), ("daily", d["daily"]), ("alerts", alerts)):
        json.dump(rows, open(os.path.join(DASH, f"{name}.json"), "w", encoding="utf-8"), ensure_ascii=False)


def write_xlsx(d):
    wb = Workbook(); ws = wb.active; ws.title = "ملخص"; ws.sheet_view.rightToLeft = True
    hdr = lambda ws_: [setattr(c, "font", Font(bold=True, color="FFFFFF")) or setattr(c, "fill", PatternFill("solid", fgColor="1F3A5F")) for c in ws_[1]]
    rows = [("آخر تحديث", d["generated"]),
            ("حصة الإيميل اليوم", f'{d["quota"]["email"]["used"]} / {d["quota"]["email"]["allowed"]} (أسبوع {d["quota"]["email"]["week"]})'),
            ("حصة الواتساب اليوم", f'{d["quota"]["whatsapp"]["used"]} / {d["quota"]["whatsapp"]["allowed"]} (أسبوع {d["quota"]["whatsapp"]["week"]})'),
            ("إيميلات أُرسلت هذا الأسبوع", d["week"]["email_sent"]), ("واتساب أُرسل هذا الأسبوع", d["week"]["whatsapp_sent"]),
            ("مسودات تنتظر إرسالك", d["pending"]["drafts_waiting_send"]), ("رسائل واتساب جاهزة", d["pending"]["whatsapp_ready"]),
            ("ردود", d["totals"]["replied"]), ("ارتدادات", d["totals"]["bounced"]),
            ("أسابيع متبقية للإيميل", d["weeks_left"]["email"]), ("أسابيع متبقية للواتساب", d["weeks_left"]["whatsapp"])]
    ws.append(["البند", "القيمة"]); [ws.append(list(r)) for r in rows]; hdr(ws); ws.column_dimensions["A"].width = 32; ws.column_dimensions["B"].width = 28
    w2 = wb.create_sheet("المتبقي حسب الدولة"); w2.sheet_view.rightToLeft = True; w2.append(["الدولة", "متبقي", "جاهز للإيميل", "جاهز للواتساب"])
    for c, v in d["remaining"].items(): w2.append([targets_tool.COUNTRY_AR[c], v["remaining"], v["email_ready"], v["whatsapp_ready"]])
    hdr(w2)
    w3 = wb.create_sheet("يومي"); w3.sheet_view.rightToLeft = True; w3.append(["التاريخ", "إيميل – جُهّز", "إيميل – أُرسل", "واتساب – جُهّز", "واتساب – أُرسل"])
    for r in d["daily"]: w3.append([r["date"], r["email_prepared"], r["email_sent"], r["whatsapp_prepared"], r["whatsapp_sent"]])
    hdr(w3)
    w4 = wb.create_sheet("تنبيهات وما يحتاج تدخلك"); w4.sheet_view.rightToLeft = True; w4.append(["النوع", "التفاصيل", "المطلوب منك"])
    for al in d["alerts"]: w4.append(["تنبيه", al, "راجع الإرسال"])
    for i in d["open_issues"]: w4.append([i["kind"], i["op"], i["need"]])
    hdr(w4); w4.column_dimensions["B"].width = 60; w4.column_dimensions["C"].width = 60
    wb.save(os.path.join(ROOT, "output", "dashboard.xlsx"))


# ---------------- sending desk ----------------
DESK = os.path.join(ROOT, "output", "desk")


def _about_fields(ab, it):
    a = ab.get(it["id"], {})
    return {"about": a.get("about", ""), "about_facts": a.get("facts", []), "about_url": a.get("url", ""),
            "city": it.get("city") or "", "website": it.get("website") or "", "warn": a.get("warn", ""),
            "about_limited": bool(a.get("limited"))}


def _desk_rows(items, emails, prefix, start_n, about=None):
    """items: dicts with country,row,name,type,email/to,lang,cv,subject,draft_id,view_url; emails: id -> {paras,items,after,...}"""
    import drafts_tool
    A = json.load(open(os.path.join(DESK, "assets.json"), encoding="utf-8"))["cv"]
    out = []
    for k, it in enumerate(items):
        e = dict(emails[it["id"]], country=it["country"], lang=it["lang"])
        sig_html, lines = drafts_tool.sig_block(e)
        cvf = drafts_tool.CV[(it["lang"], it["cv"])]
        out.append({"doc_id": f"{prefix}-{it['id']:02d}", "data": {
            "n": start_n + k, "run": prefix, "country": it["country"], "row": it["row"], "name": it["name"], "type": it.get("type") or "",
            "to": (it.get("to") or str(it.get("email", "")).split(",")[0]).strip(), "subject": it["subject"], "lang": it["lang"], "cv": it["cv"],
            "body": drafts_tool.editable_text(e), "sig_html": sig_html, "sig_text": lines[0] + "\n" + "\n".join(lines[1:]),
            "cv_url": A[cvf], "send_name": drafts_tool.SEND_NAME[it["lang"]],
            "draft_id": it.get("draft_id", ""), "view_url": it.get("draft_url") or it.get("view_url") or "",
            "status": "ready", "sent_at": "", "edited": False, **_about_fields(about or {}, it),
            "subject_ar": e.get("subject_ar", ""), "body_ar": e.get("body_ar", "")}})
    return out


def desk_export(a):
    """write one JSON file per queue doc for ArtifactData batch (output/desk/export/<doc_id>.json) + an index"""
    exp = os.path.join(DESK, "export"); os.makedirs(exp, exist_ok=True)
    for f in glob.glob(os.path.join(exp, "*.json")): os.remove(f)
    if a.batch:
        sys.path.insert(0, os.path.join(ROOT, "output", "drafts"))
        mod = __import__(f"batch_{a.batch}_emails"); emails = {e["id"]: e for e in mod.EMAILS}
        trp = os.path.join(ROOT, "output", "drafts", f"batch_{a.batch}_body_ar.json")
        if os.path.exists(trp):
            for x in json.load(open(trp, encoding="utf-8")):
                emails[x["id"]] = dict(emails[x["id"]], subject_ar=x["subject_ar"], body_ar=x["body_ar"])
        items = json.load(open(os.path.join(ROOT, "output", "drafts", f"batch_{a.batch}.json"), encoding="utf-8"))
        abp = os.path.join(ROOT, "output", "drafts", f"batch_{a.batch}_about.json")
        about = {x["id"]: x for x in json.load(open(abp, encoding="utf-8"))} if os.path.exists(abp) else {}
        rows = _desk_rows(items, emails, f"b{a.batch}", a.start, about)
    else:
        sel = {t["id"]: t for t in json.load(open(os.path.join(a.run, "selection.json"), encoding="utf-8"))["targets"]}
        texts = json.load(open(os.path.join(a.run, "texts.json"), encoding="utf-8"))
        items = [dict(sel[e["id"]], id=e["id"], lang=e["lang"], cv=e["cv"], subject=e["subject"]) for e in texts]
        rp = os.path.join(a.run, "research.json")
        about = {x["id"]: x for x in json.load(open(rp, encoding="utf-8"))} if os.path.exists(rp) else {}
        rows = _desk_rows(items, {e["id"]: e for e in texts}, os.path.basename(a.run).replace("_", "-"), a.start, about)
    idx = []
    for r in rows:
        f = os.path.join(exp, r["doc_id"] + ".json")
        json.dump(r["data"], open(f, "w", encoding="utf-8"), ensure_ascii=False); idx.append({"doc_id": r["doc_id"], "file_path": f})
    json.dump(idx, open(os.path.join(exp, "_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("exported", len(rows), "->", exp)


def sync_desk(a):
    """a.dir: folder from ArtifactData list(out_dir) of collection 'queue' (…/queue/<doc>.json). Marks sent rows."""
    L = load_ledger(); n = 0
    for f in glob.glob(os.path.join(a.dir, "**", "*.json"), recursive=True):
        d = json.load(open(f, encoding="utf-8")); d = d.get("data", d)
        if not isinstance(d, dict) or "country" not in d: continue
        for e in L:
            if e["channel"] == "email" and e["country"] == d["country"] and e["row"] == d["row"]:
                if d.get("draft_id"): e["draft_id"] = d["draft_id"]
                if d.get("status") == "sent" and e["status"] == "drafted":
                    e["status"] = "sent"; e["sent_date"] = (d.get("sent_at") or today().isoformat())[:10]
                    if d.get("subject"): e["subject"] = d["subject"]
                    _log_send(e, "Email", e["sent_date"]); set_col14(e["country"], e["row"], "أُرسل إيميل"); n += 1
    save_ledger(L); print("synced desk:", n)


def _email_from_text(lang, body, sig_html, sig_text):
    """same rules as the desk page: blank line = paragraph, a block of '- ' lines = bullet list"""
    import html as H
    rtl = lang == "AR"; parts = []; blocks = [b.strip() for b in re.split(r"\n\s*\n", body.replace("\r", "")) if b.strip()]
    for b in blocks:
        lines = [l.strip() for l in b.split("\n") if l.strip()]
        if all(l.startswith("- ") for l in lines):
            pad = "padding:0 22px 0 0;" if rtl else "padding:0 0 0 22px;"
            parts.append(f'<ul style="margin:0 0 14px 0;{pad}">' + "".join(f'<li style="margin:0 0 8px 0;">{H.escape(l[2:])}</li>' for l in lines) + "</ul>")
        else:
            parts.append(f'<p style="margin:0 0 14px 0;">{H.escape(" ".join(lines))}</p>')
    font = "Tahoma, Arial, sans-serif" if rtl else "Arial, Helvetica, sans-serif"
    html = (f'<div {"dir=\"rtl\" " if rtl else ""}style="font-family:{font};font-size:15px;line-height:1.7;color:#222;'
            f'text-align:{"right" if rtl else "left"};max-width:640px;">' + "".join(parts) + sig_html + "</div>")
    return html, "\n\n".join(blocks) + "\n\n" + sig_text


def send_plan(a):
    """read a desk dump (ArtifactData list out_dir of 'queue' + 'config'), decide what to send NOW, write ready-to-send payloads"""
    import drafts_tool, hashlib
    docs = []
    for f in glob.glob(os.path.join(a.dir, "queue", "*.json")):
        d = json.load(open(f, encoding="utf-8")); d = d.get("data", d); d["_id"] = os.path.basename(f)[:-5]; docs.append(d)
    cfgf = os.path.join(a.dir, "config", "settings.json")
    cfg = json.load(open(cfgf, encoding="utf-8")) if os.path.exists(cfgf) else {}
    cfg = cfg.get("data", cfg)
    now = datetime.datetime.now(TZ); t = now.date().isoformat()
    daily_max = int(cfg.get("daily_max", POLICY["email"]["absolute_max_per_day"]))
    sent_today = sum(1 for d in docs if d.get("status") == "sent" and str(d.get("sent_at", ""))[:10] == t)
    approved = sorted([d for d in docs if d.get("status") == "approved"], key=lambda d: (str(d.get("approved_at", "")), d.get("n", 0)))
    remaining = max(0, daily_max - sent_today); runs_left = max(1, 24 - now.hour)
    k = 0 if cfg.get("paused") or not approved or remaining == 0 else min(2, len(approved), remaining, max(1, -(-remaining // runs_left)))
    A = json.load(open(os.path.join(DESK, "assets.json"), encoding="utf-8"))["cv"]; rev = {v: k_ for k_, v in A.items()}
    out = []
    for d in approved[:k]:
        html_, text = _email_from_text(d["lang"], d["body"], d["sig_html"], d["sig_text"])
        cvf = os.path.join(ROOT, "cv", rev[d["cv_url"]]); sha = hashlib.sha256(open(cvf, "rb").read()).hexdigest()
        out.append({"doc_id": d["_id"], "to": d["to"], "subject": d["subject"], "htmlBody": html_, "body": text,
                    "attachment": f"sha256:{sha}:{cvf}", "filename": d["send_name"], "old_draft_id": d.get("draft_id", ""),
                    "name": d["name"], "country": d["country"]})
    plan = {"now": now.strftime("%Y-%m-%d %H:%M"), "paused": bool(cfg.get("paused")), "daily_max": daily_max, "sent_today": sent_today,
            "approved_waiting": len(approved), "send_now": len(out), "gap_minutes": [cfg.get("gap_min", 2), cfg.get("gap_max", 5)], "items": out}
    os.makedirs(os.path.join(DESK, "outbox"), exist_ok=True)
    json.dump(plan, open(os.path.join(DESK, "outbox", "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k_: v for k_, v in plan.items() if k_ != "items"}, ensure_ascii=False))
    for it in out: print("SEND", it["doc_id"], it["to"], it["filename"])


def desk_saved(a):
    """output/saved_for_later.xlsx from a desk dump: every message the user saved for later (status 'saved')"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    docs = []
    for f in glob.glob(os.path.join(a.dir, "queue", "*.json")):
        d = json.load(open(f, encoding="utf-8")); d = d.get("data", d)
        if d.get("status") == "saved": docs.append(d)
    cols = [("n", "#", 5), ("name", "الجهة", 34), ("country", "الدولة", 10), ("city", "المدينة", 12), ("type", "النوع", 16),
            ("to", "الإيميل", 32), ("website", "الموقع", 30), ("about_url", "رابط المصدر", 30), ("about", "نبذة", 60),
            ("about_facts", "نقاط", 50), ("warn", "تنبيه", 30), ("lang", "اللغة", 7), ("send_name", "السيرة", 30),
            ("subject", "الموضوع", 45), ("body", "نص الرسالة", 70), ("saved_at", "تاريخ الحفظ", 18)]
    wb = Workbook(); ws = wb.active; ws.title = "محفوظة للرجوع"; ws.sheet_view.rightToLeft = True
    ws.append([c[1] for c in cols])
    for i, (_, _, w) in enumerate(cols, 1):
        c = ws.cell(1, i); ws.column_dimensions[c.column_letter].width = w
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="2A9D8F")
    for d in sorted(docs, key=lambda d: d.get("n", 0)):
        ws.append([" | ".join(d.get(k) or []) if k == "about_facts" else (AR_C.get(d.get(k), d.get(k)) if k == "country" else d.get(k, ""))
                   for k, _, _ in cols])
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "B2"; ws.auto_filter.ref = ws.dimensions
    out = os.path.join(ROOT, "output", "saved_for_later.xlsx"); wb.save(out); print("saved_for_later:", len(docs), "->", out)
    for d in docs:
        try: set_col14(d["country"], d["row"], "محفوظة للرجوع (مكتب الإرسال)")
        except Exception: pass


# ---------------- migrate ----------------
def migrate_batch01(_):
    rows = json.load(open(os.path.join(ROOT, "output", "drafts", "batch_01.json"), encoding="utf-8")); L = load_ledger()
    have = {(e["country"], e["row"]) for e in L}; n = 0
    for r in rows:
        if (r["country"], r["row"]) in have: continue
        L.append({"date": "2026-11-25", "run": "batch_01", "channel": "email", "status": "drafted", "country": r["country"],
                  "row": r["row"], "name": r["name"], "email": r["email"], "phone": "", "subject": r["subject"],
                  "draft_id": r.get("draft_id", ""), "lang": r["lang"], "cv": r["cv"], "type": r["type"],
                  "send_day": "ABCDE".index(r["group"]) + 1, "migrated": True})
        n += 1
    save_ledger(L); print("migrated", n)


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    x = sp.add_parser("quota"); x.add_argument("--channel", required=True, choices=["email", "whatsapp"])
    x = sp.add_parser("select"); x.add_argument("--channel", required=True, choices=["email", "whatsapp"]); x.add_argument("--count", type=int, required=True); x.add_argument("--countries")
    for n in ("build", "wa-queue", "mark"):
        x = sp.add_parser(n); x.add_argument("--run", required=True)
    x = sp.add_parser("record"); x.add_argument("--run", required=True); x.add_argument("--id", type=int, required=True); x.add_argument("--draft-id", required=True)
    for n in ("sync-sent", "sync-bounces", "sync-replies"):
        x = sp.add_parser(n); x.add_argument("--file", required=True)
    x = sp.add_parser("desk-export"); x.add_argument("--batch"); x.add_argument("--run"); x.add_argument("--start", type=int, default=1)
    x = sp.add_parser("sync-desk"); x.add_argument("--dir", required=True)
    x = sp.add_parser("send-plan"); x.add_argument("--dir", required=True)
    x = sp.add_parser("desk-saved"); x.add_argument("--dir", required=True)
    for n in ("sync-wa", "stats", "migrate-batch01"):
        sp.add_parser(n)
    a = ap.parse_args()
    {"quota": quota, "select": select, "build": build, "record": record, "wa-queue": wa_queue, "mark": mark,
     "sync-sent": sync_sent, "sync-wa": sync_wa, "sync-bounces": sync_bounces, "sync-replies": sync_replies,
     "stats": stats, "migrate-batch01": migrate_batch01, "desk-export": desk_export, "sync-desk": sync_desk, "send-plan": send_plan, "desk-saved": desk_saved}[a.cmd](a)


if __name__ == "__main__":
    main()
