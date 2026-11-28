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
    if channel == "email" and p.get("ramp"):
        start = datetime.date.fromisoformat(p["start_date"]); return ramp_state(update=False)["cap"], max(1, (d - start).days // 7 + 1)
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
                alerts.append(f"نسبة الارتداد {rate:.0%} أعلى من {p['stop_if_bounce_rate_over']:.0%} – الحد اليومي لا يرتفع (وينزل درجة إن كان أعلى من 30)؛ شغّل verify-emails ونظّف القوائم. لا إيقاف")
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


# ---- hiring-likelihood ranking (user request 26/11: country first, then likelihood of hiring) ----
JUNK = re.compile(r"trading|contracting|sanitary|curtain|blinds|consulate|embassy|museum|hotel|restaurant|computer|driving|"
                  r"real estate|cars?\b|shipping|businessmen|technology park|public works|"
                  r"تجار|مقاولات|قنصلية|سفارة|متحف|فندق|مطعم|عقار", re.I)
WEBMAIL = re.compile(r"@(gmail|yahoo|hotmail|outlook|live|msn|aol|icloud)\.", re.I)
SPECIAL = re.compile(r"autis|special (?:needs|education|ed\b)|needs\b|learning (?:difficult|disab|support|challeng|development)|"
                     r"rehab|therap|speech|hearing|deaf|blind|down syndrome|disab|inclusi|determination|"
                     r"توحد|ذوي الاحتياجات|تربية خاصة|التربية الخاصة|تأهيل|إعاقة|اعاقة|نطق|سمع|صم|مكفوف|صعوبات|دمج|الهمم", re.I)
def _domain(u):
    m = re.search(r"(?:https?://)?(?:www\.)?([^/\s]+)", str(u or "")); return (m.group(1).lower() if m else "")
def hire_score(name, typ, rel, email, website, careers, wa_rank=0):
    """Lower = more likely to hire. Order: org kind, relevance, careers page, email quality, website, whatsapp."""
    rel_r = 0 if rel == "عالية" else 1 if rel == "متوسطة" else 2
    nm = str(name or "")
    if typ in ("مركز تربية خاصة",) or SPECIAL.search(nm): kind = 0          # specialised centres/schools hire specialists
    elif typ == "مدرسة" and INTL.search(nm): kind = 1                        # international schools: learning-support teams
    elif typ == "مدرسة": kind = 2                                             # local schools: resource rooms
    elif typ in ("جمعية", "منظمة"): kind = 3                                  # generic associations (no disability focus)
    elif typ == "جامعة": kind = 5                                             # usually need PhD
    elif typ == "جهة حكومية": kind = 6                                        # citizens first
    else: kind = 4
    car = 0 if str(careers or "").strip() else 1
    em = str(email or "").lower()
    if not em: eq = 1
    elif WEBMAIL.search(em): eq = 2                                           # highest bounce rate so far
    elif _domain(website) and em.split("@")[-1].endswith(_domain(website).split(":")[0].replace("www.", "")): eq = 0
    else: eq = 1
    web = 0 if str(website or "").strip() else 1
    return (kind, rel_r, car, eq, web, wa_rank)


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
            if JUNK.search(str(name)): continue
            score = hire_score(name, typ, rel, contact if a.channel == "email" else "", row[8], row[9],
                               0 if (a.channel == "email" or wast.startswith("مؤكد")) else 1)
            pool.append((score, r, {"country": c, "row": r, "name": name, "type": typ, "email": email if a.channel == "email" else "",
                                     "whatsapp": contact if a.channel == "whatsapp" else "", "phone": phone, "city": row[7],
                                     "website": row[8], "careers": row[9] or "", "source": row[10], "lang": lang_for(name, typ, row[8]), "cv": row[12], "relevance": rel}))
        pool.sort(key=lambda x: (x[0], x[1])); pools[c] = [p[2] for p in pool]
    # weighted spread across countries (smooth weighted round-robin); user priority: Qatar ~50%
    W = POLICY.get("country_weights", {})
    w = {c: float(W.get(c, 1)) for c in countries}; cur = {c: 0.0 for c in countries}; picked = []
    while len(picked) < a.count and any(pools.values()):
        live = [c for c in countries if pools.get(c)]
        tot = sum(w[c] for c in live)
        for c in live: cur[c] += w[c]
        c = max(live, key=lambda x: cur[x]); cur[c] -= tot
        picked.append(pools[c].pop(0))
    # user priority 26/11: country first (Qatar first), then hiring likelihood within each country
    order = {c: i for i, c in enumerate(sorted(countries, key=lambda c: -w[c]))}
    picked.sort(key=lambda p: order[p["country"]])
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
                      "suggested_time": t0.strftime("%H:%M"), "status": "pending_approval", "approved_at": "", "sent_at": ""})  # user must approve each message before the extension sends it
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
                **{"ramp_" + k_: v_ for k_, v_ in ramp_state(update=False).items() if k_ != "changed_now"},
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
            "careers_url": a.get("careers_url") or it.get("careers") or "",
            "about_limited": bool(a.get("limited")),
            # job opportunity (announced vacancy that fits, or an org reply asking for something) -> top of review and send order
            "priority": bool(a.get("vacancy") or a.get("priority") or it.get("vacancy")), "vacancy": a.get("vacancy") or it.get("vacancy") or ""}


def _desk_rows(items, emails, prefix, start_n, about=None, status="ready"):
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
            "body": drafts_tool.editable_text(e), "body_orig": drafts_tool.editable_text(e), "subject_orig": it["subject"], "sig_html": sig_html, "sig_text": lines[0] + "\n" + "\n".join(lines[1:]),
            "cv_url": A[cvf], "send_name": drafts_tool.SEND_NAME[it["lang"]],
            "draft_id": it.get("draft_id", ""), "view_url": it.get("draft_url") or it.get("view_url") or "",
            "status": status, "sent_at": "", "edited": False, **_about_fields(about or {}, it),
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
        rows = _desk_rows(items, {e["id"]: e for e in texts}, os.path.basename(a.run).replace("_", "-"), a.start, about, a.status)
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
        to = str(d.get("to") or "").strip().lower()
        # a follow-up to a reply (e.g. HR address) shares country/row with the first message: match by recipient too, and
        # add a ledger entry for a sent doc whose recipient is not in the ledger yet, so every send is logged
        if d.get("status") == "sent" and to and not any(e["channel"] == "email" and str(e.get("email", "")).strip().lower() == to for e in L):
            L.append({"date": (d.get("sent_at") or today().isoformat())[:10], "run": d.get("run", ""), "channel": "email", "status": "drafted",
                      "country": d["country"], "row": d.get("row"), "name": d.get("name", ""), "email": d.get("to", ""), "phone": "",
                      "subject": d.get("subject", ""), "draft_id": "", "lang": d.get("lang"), "cv": d.get("cv"), "type": d.get("type", ""), "send_day": 0})
        for e in L:
            if e["channel"] == "email" and e["country"] == d["country"] and e["row"] == d["row"] and (not to or str(e.get("email", "")).strip().lower() in ("", to)):
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
            parts.append('<p style="margin:0 0 14px 0;">' + "<br>".join(H.escape(l) for l in lines) + "</p>")  # keep the user's line breaks
    font = "Tahoma, Arial, sans-serif" if rtl else "Arial, Helvetica, sans-serif"
    html = (f'<div {"dir=\"rtl\" " if rtl else ""}style="font-family:{font};font-size:15px;line-height:1.7;color:#222;'
            f'text-align:{"right" if rtl else "left"};max-width:640px;">' + "".join(parts) + sig_html + "</div>")
    return html, "\n\n".join(blocks) + "\n\n" + sig_text



def ramp_state(update=True, gmail_error=False):
    """gradual, metric-gated daily email cap (config email.ramp). State in output/email_ramp.json: {stage, since, changed, history}.
    Up one stage after hold_days sending days at the stage with bounce < up_if_bounce_under (and reply rate gate from stage 2);
    down one stage (never below 0, never a pause) if bounce > step_down_if_bounce_over or Gmail reported a limit/suspicious error."""
    R = POLICY["email"].get("ramp") or {"stages": [POLICY["email"]["absolute_max_per_day"]], "hold_days": []}
    f = os.path.join(ROOT, "output", "email_ramp.json"); t = today().isoformat()
    st = json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {"stage": 0, "since": t, "changed": "", "history": []}
    L = [e for e in load_ledger() if e.get("channel") == "email" and e.get("status") in ("sent", "bounced", "replied") and e.get("sent_date")]
    L.sort(key=lambda e: e["sent_date"]); win = L[-int(R.get("bounce_window", 100)):]
    bounce = (sum(1 for e in win if e["status"] == "bounced") / len(win)) if win else 0.0
    replies = (sum(1 for e in win if e["status"] == "replied") / len(win)) if win else 0.0
    days = len({e["sent_date"][:10] for e in L if e["sent_date"][:10] >= st["since"]})
    stg = st["stage"]; why = ""
    if update and st.get("changed") != t:
        if (bounce > R.get("step_down_if_bounce_over", 0.05) or gmail_error) and stg > 0:
            stg -= 1; why = f"down: bounce {bounce:.0%}" + (" + Gmail error" if gmail_error else "")
        elif stg < len(R["stages"]) - 1 and days >= R["hold_days"][stg] and bounce < R.get("up_if_bounce_under", 0.03) and not gmail_error:
            need = float((R.get("min_reply_rate_from_stage") or {}).get(str(stg + 1), 0))
            if replies >= need: stg += 1; why = f"up: {days} days, bounce {bounce:.0%}, replies {replies:.0%}"
        if why:
            st.update(stage=stg, since=t, changed=t); st.setdefault("history", []).append({"date": t, "stage": stg, "cap": R["stages"][stg], "why": why})
            json.dump(st, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        elif not os.path.exists(f):
            json.dump(st, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cap = min(R["stages"][stg], int(R.get("ceiling", 75)))
    nxt = R["stages"][stg + 1] if stg < len(R["stages"]) - 1 else None
    return {"stage": stg + 1, "cap": cap, "bounce_rate": round(bounce, 3), "reply_rate": round(replies, 3), "days_at_stage": days,
            "next_cap": nxt, "days_needed": (R["hold_days"][stg] if nxt else None), "changed_now": why}


FREEMAIL = re.compile(r"@(gmail|googlemail|yahoo|ymail|hotmail|outlook|live|msn|aol|icloud)\.", re.I)


def _mx_ok(domain, cache={}):
    """MX (or A fallback) via DNS-over-HTTPS; True / False / None (lookup failed)"""
    if domain in cache: return cache[domain]
    import urllib.request
    res = None
    try:
        for typ in ("MX", "A"):
            j = json.load(urllib.request.urlopen(f"https://dns.google/resolve?name={domain}&type={typ}", timeout=10))
            if j.get("Status") == 3: res = False; break          # NXDOMAIN: domain does not exist
            if any(a.get("type") in (15, 1) for a in j.get("Answer", [])): res = True; break
            res = False
    except Exception:
        res = None
    cache[domain] = res; return res


def _on_site(email, website):
    """True if the address appears on the org's own site (home + common contact pages)"""
    import urllib.request
    if not website or not str(website).startswith("http"): return False
    base = website.rstrip("/"); e = email.lower()
    for path in ("", "/contact", "/contact-us", "/ar/contact", "/en/contact"):
        try:
            req = urllib.request.Request(base + path, headers={"User-Agent": "Mozilla/5.0"})
            html_ = urllib.request.urlopen(req, timeout=10).read(600000).decode("utf-8", "ignore").lower()
            if e in html_ or e.replace("@", "&#64;") in html_: return True
        except Exception:
            continue
    return False


def verify_emails(a):
    """flag risky recipients before sending (bounces hurt Gmail reputation most).
    --dir: desk dump (queue/*.json) -> checks docs with --status (default approved); or --run: a run folder's selection.json.
    risky = domain without mail server / non-existent, or a free-mail address (gmail/yahoo/...) not found on the org's website.
    Writes <dir>/verify.json: [{doc_id, to, verdict: ok|risky, reason}]"""
    items = []
    if a.dir:
        for f in glob.glob(os.path.join(a.dir, "queue", "*.json")):
            d = json.load(open(f, encoding="utf-8")); d = d.get("data", d)
            if d.get("status") == "approved" and d.get("verify") == "risky": continue   # user re-approved after the warning: respect it
            if d.get("status") in a.status.split(","): items.append((os.path.basename(f)[:-5], d.get("to", ""), d.get("website") or d.get("about_url") or "", d.get("name", "")))
        out_path = os.path.join(a.dir, "verify.json")
    else:
        sel = json.load(open(os.path.join(a.run, "selection.json"), encoding="utf-8"))
        for t in sel["targets"]: items.append((t["id"], str(t.get("email", "")).split(",")[0].strip(), t.get("website") or "", t.get("name", "")))
        out_path = os.path.join(a.run, "verify.json")
    bounced = {str(e.get("email", "")).lower() for e in load_ledger() if e.get("status") == "bounced"}
    res = []
    for did, to, web, name in items:
        to_l = to.lower().strip(); dom = to_l.split("@")[-1] if "@" in to_l else ""
        if not dom: v, why = "risky", "عنوان إيميل غير صالح"
        elif to_l in bounced: v, why = "risky", "هذا الإيميل ارتد سابقاً"
        else:
            mx = _mx_ok(dom)
            if mx is False: v, why = "risky", f"النطاق {dom} لا يستقبل بريداً (لا يوجد خادم بريد)"
            elif FREEMAIL.search(to_l) and not _on_site(to_l, web):
                v, why = "risky", "قد لا يكون هذا الإيميل موجوداً: إيميل مجاني (gmail/yahoo/hotmail) وجدناه في دليل فقط وليس في موقع الجهة"
            else: v, why = "ok", ("" if mx else "تعذر فحص النطاق الآن")
        res.append({"doc_id": did, "to": to, "name": name, "verdict": v, "reason": why})
    json.dump(res, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"verify: {len(res)} checked, {sum(r['verdict'] == 'risky' for r in res)} risky -> {out_path}")
    for r in res:
        if r["verdict"] == "risky": print("RISKY", r["doc_id"], r["to"], "|", r["reason"])

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
    RS = ramp_state(update=True, gmail_error=bool(getattr(a, "gmail_error", False))); daily_max = RS["cap"]
    sent_today = sum(1 for d in docs if d.get("status") == "sent" and str(d.get("sent_at", ""))[:10] == t)
    # the daily cap covers every email sent today, including ones sent outside the desk (other sessions, careers emails): use the ledger too
    led = sum(1 for e in load_ledger() if e.get("channel") == "email" and e.get("status") in ("sent", "bounced", "replied") and str(e.get("sent_date", ""))[:10] == t)
    sent_today = max(sent_today, led)
    approved = sorted([d for d in docs if d.get("status") == "approved"], key=lambda d: (0 if d.get("priority") else 1, str(d.get("approved_at", "")), d.get("n", 0)))
    remaining = max(0, daily_max - sent_today); runs_left = max(1, 24 - now.hour)
    per_run = 2 if daily_max <= 48 else 3   # 50+/day needs up to 3 per hourly round (still 2-5 min apart)
    # spread the day's quota evenly until the last round (user 27/11): send round(remaining / rounds left), halves rounded down,
    # so rounds alternate 1 and 2 (or skip when ahead) and the last message goes out near 23:58 instead of early evening
    pace = int(remaining / runs_left + 0.5 - 1e-9)
    k = 0 if cfg.get("paused") or not approved or remaining == 0 else min(per_run, len(approved), remaining, pace)
    AJ = json.load(open(os.path.join(DESK, "assets.json"), encoding="utf-8")); A = AJ["cv"]; rev = {v: k_ for k_, v in A.items()}; rev.update(AJ.get("cv_aliases", {}))
    out = []
    for d in approved[:k]:
        # always the current signature (one link; phone/WhatsApp plain text), even for messages approved before the change
        sh, sl = drafts_tool.sig_block({"lang": d["lang"], "country": d.get("country")})
        html_, text = _email_from_text(d["lang"], d["body"], sh, sl[0] + "\n" + "\n".join(sl[1:]))
        cvf = os.path.join(ROOT, "cv", rev[d["cv_url"]]); sha = hashlib.sha256(open(cvf, "rb").read()).hexdigest()
        atts = [{"content": f"sha256:{sha}:{cvf}", "filename": d["send_name"], "mimeType": "application/pdf"}]
        # optional extra CVs (e.g. English as well, when the organization replied in English)
        for u, nm in zip(d.get("extra_cv_urls") or [], d.get("extra_send_names") or []):
            ef = os.path.join(ROOT, "cv", rev[u]); atts.append({"content": f"sha256:{hashlib.sha256(open(ef, 'rb').read()).hexdigest()}:{ef}", "filename": nm, "mimeType": "application/pdf"})
        out.append({"doc_id": d["_id"], "to": d["to"], "subject": d["subject"], "htmlBody": html_, "body": text,
                    "attachment": f"sha256:{sha}:{cvf}", "filename": d["send_name"], "attachments": atts, "old_draft_id": d.get("draft_id", ""),
                    "name": d["name"], "country": d["country"]})
    plan = {"now": now.strftime("%Y-%m-%d %H:%M"), "paused": bool(cfg.get("paused")), "daily_max": daily_max, "sent_today": sent_today,
            "approved_waiting": len(approved), "send_now": len(out), "ramp": RS, "gap_minutes": [cfg.get("gap_min", 2), cfg.get("gap_max", 5)], "items": out}
    os.makedirs(os.path.join(DESK, "outbox"), exist_ok=True)
    json.dump(plan, open(os.path.join(DESK, "outbox", "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k_: v for k_, v in plan.items() if k_ != "items"}, ensure_ascii=False))
    for it in out: print("SEND", it["doc_id"], it["to"], " + ".join(a["filename"] for a in it["attachments"]))


CAREERS_RE = re.compile(r"career|vacanc|/jobs?\b|job-board|recruit|work-with-us|workwithus|join-us|joinus|employment|workday|"
                        r"rejoindre|hiring|توظيف|وظائف", re.I)


def careers(a):
    """Careers pages (user request 26/11: apply later through the web).
    Sources: Targets col 10 'صفحة التوظيف' + careers links found by research (research*.json in runs).
    Research links are written back to col 10. Output (append-only, user edits freely, matched by country+name):
    output/careers_pages.xlsx  +  output/desk/careers/*.json (desk collection 'careers', with _index.json)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    url_re = re.compile(r"https?://[^\s\"'،)<>]+")
    found = {}  # (country,row) -> url
    for f in glob.glob(os.path.join(RUNS, "*", "research*.json")):
        run = os.path.dirname(f)
        try:
            R = json.load(open(f, encoding="utf-8")); sel = {t["id"]: t for t in json.load(open(os.path.join(run, "selection.json"), encoding="utf-8"))["targets"]}
        except Exception: continue
        for x in R if isinstance(R, list) else []:
            t = sel.get(x.get("id")) if isinstance(x, dict) else None
            if not t: continue
            us = [u.rstrip(".,;") for u in url_re.findall(json.dumps(x, ensure_ascii=False)) if CAREERS_RE.search(u)]
            if x.get("careers_url"): us.insert(0, x["careers_url"])
            if us: found[(t["country"], t["row"])] = us[0]
    rows = []
    for c in COUNTRIES:
        p = targets_tool.path(c); wb = load_workbook(p); ws = wb["الجهات"]; changed = False
        for r in range(2, ws.max_row + 1):
            name = ws.cell(r, 2).value
            if not name: continue
            u = str(ws.cell(r, 10).value or "").strip()
            if not u and (c, r) in found: u = found[(c, r)]; ws.cell(r, 10).value = u; changed = True
            if not re.match(r"^https?://", u): continue
            st = str(ws.cell(r, 14).value or "")
            if st.startswith("مكرر") or st.startswith("مستبعد"): continue
            rows.append({"country": c, "row": r, "name": str(name), "type": str(ws.cell(r, 3).value or ""), "city": str(ws.cell(r, 8).value or ""),
                         "url": u, "website": str(ws.cell(r, 9).value or ""), "email": str(ws.cell(r, 6).value or "").split(",")[0].strip(),
                         "email_status": st, "score": list(hire_score(name, ws.cell(r, 3).value, ws.cell(r, 16).value, ws.cell(r, 6).value, ws.cell(r, 9).value, u))})
        if changed: wb.save(p)
    rows.sort(key=lambda x: (COUNTRIES.index(x["country"]) if x["country"] != "Qatar" else -1, x["score"], x["name"]))
    cols = [("name", "الجهة", 36), ("country", "الدولة", 10), ("type", "النوع", 16), ("city", "المدينة", 12), ("url", "رابط صفحة التوظيف", 50),
            ("website", "الموقع", 34), ("email", "الإيميل", 32), ("email_status", "حالة التواصل بالإيميل", 30),
            ("applied", "قدّمت عبر الموقع؟", 16), ("applied_at", "تاريخ التقديم", 14), ("notes", "ملاحظاتي", 40)]
    out = os.path.join(ROOT, "output", "careers_pages.xlsx")
    if os.path.exists(out):
        wb = load_workbook(out); ws = wb.worksheets[0]
    else:
        wb = Workbook(); ws = wb.active; ws.title = "صفحات التوظيف"; ws.sheet_view.rightToLeft = True
        ws.append([c[1] for c in cols])
        for i, (_, _, w) in enumerate(cols, 1):
            cc = ws.cell(1, i); ws.column_dimensions[cc.column_letter].width = w
            cc.font = Font(bold=True, color="FFFFFF"); cc.fill = PatternFill("solid", fgColor="2A9D8F")
        ws.freeze_panes = "B2"
    head = {str(ws.cell(1, j).value or "").strip(): j for j in range(1, ws.max_column + 1)}
    jn, jc = head.get("الجهة"), head.get("الدولة")
    # desk state (button "قدّمت عبر الموقع") -> Excel, only into empty cells (the user's own edits win)
    st = {}
    if getattr(a, "dir", None):
        for f in glob.glob(os.path.join(a.dir, "careers", "*.json")):
            dd = json.load(open(f, encoding="utf-8")); dd = dd.get("data", dd)
            if dd.get("applied"): st[(AR_C.get(dd.get("country"), dd.get("country")), dd.get("name"))] = dd.get("applied_at", "")
    ja, jt = head.get("قدّمت عبر الموقع؟"), head.get("تاريخ التقديم")
    if st and jn and jc and ja:
        for r in range(2, ws.max_row + 1):
            k = (str(ws.cell(r, jc).value or ""), str(ws.cell(r, jn).value or ""))
            if k in st and not ws.cell(r, ja).value:
                ws.cell(r, ja).value = "نعم"
                if jt and not ws.cell(r, jt).value: ws.cell(r, jt).value = str(st[k])[:10]
    have = {(str(ws.cell(r, jc).value or ""), str(ws.cell(r, jn).value or "")) for r in range(2, ws.max_row + 1)} if jn and jc else set()
    added = 0
    for x in rows:
        k = (AR_C.get(x["country"], x["country"]), x["name"])
        if k in have: continue
        r = ws.max_row + 1
        for key, label, _ in cols:
            j = head.get(label)
            if not j: continue
            v = AR_C.get(x["country"], x["country"]) if key == "country" else x.get(key, "")
            cc = ws.cell(r, j, v); cc.alignment = Alignment(wrap_text=True, vertical="top")
            if key == "url" and v: cc.hyperlink = v; cc.font = Font(color="1F5FA8", underline="single")
        have.add(k); added += 1
    wb.save(out)
    A = json.load(open(os.path.join(DESK, "assets.json"), encoding="utf-8"))["cv"]
    SCH = re.compile(r"school|academy|college|university|lyc[eé]e|kindergarten|nursery|مدرسة|أكاديمية|اكاديمية|جامعة|كلية|روضة", re.I)
    for x in rows:
        lang = lang_for(x["name"], x["type"], x["website"])
        nophd = x["type"] in ("مدرسة", "جامعة") or bool(SCH.search(x["name"])) or "qf.org.qa" in x["url"] + x["website"]
        school = x["type"] == "مدرسة" or bool(SCH.search(x["name"]))
        fn = f"Amer_AlSaaideh_CV_{'English' if lang == 'EN' else 'Arabic'}{'_S' if nophd else ''}.pdf"
        x["lang"], x["cv_url"], x["send_name"] = lang, A[fn], fn.replace("_S.pdf", ".pdf")
        if lang == "EN":
            role = "a Learning Support / Special Education Teacher or Inclusion Coordinator" if school else "a Special Education Specialist"
            x["note"] = (f"I am Amer Abdeljalil, a special education specialist with an MA in Special Education (Excellent) and over five years "
                         f"in Jordanian Ministry of Education schools. I have also worked in Qatar as a special education specialist.\n"
                         f"I managed resource rooms and built an IEP for every student, led teacher training in inclusive education, and achieved "
                         f"full inclusion of students with disabilities for the first time in a public school.\n"
                         f"I am applying for {role} position. My CV is attached.")
        else:
            role = "معلم تربية خاصة أو معلم غرفة مصادر أو منسق تعليم دامج" if school else "أخصائي تربية خاصة أو مشرف برامج"
            x["note"] = ("أنا عامر عبد الجليل، أخصائي تربية خاصة أحمل ماجستير التربية الخاصة بتقدير امتياز، ولي أكثر من خمس سنوات في مدارس "
                         "وزارة التربية والتعليم الأردنية، وعملت في قطر أخصائياً للتربية الخاصة.\n"
                         "أدرت غرف المصادر وبنيت خطة تربوية فردية (IEP) لكل طالب، وقدت تدريب المعلمين على التعليم الدامج، وحققت الدمج الكلي "
                         "للطلبة ذوي الإعاقة لأول مرة في مدرسة حكومية.\n"
                         f"أتقدم للعمل لديكم {role}. سيرتي الذاتية مرفقة.")
    d = os.path.join(DESK, "careers"); os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(d, "*.json")): os.remove(f)
    idx = []
    for i, x in enumerate(rows, 1):
        doc = f"{x['country'].lower()}-{x['row']}"
        json.dump({k: x[k] for k in ("country", "row", "name", "type", "city", "url", "website", "email", "email_status",
                                     "lang", "cv_url", "send_name", "note")} | {"rank": i},
                  open(os.path.join(d, doc + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        idx.append({"doc_id": doc, "file_path": os.path.join(d, doc + ".json")})
    json.dump(idx, open(os.path.join(d, "_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"careers: {len(rows)} pages ({len(found)} from research), +{added} new rows -> {out}")


def desk_saved(a):
    """output/saved_for_later.xlsx (kept on GitHub, the user edits it freely).
    Append-only: rows already in the file are never rewritten or removed, extra columns/notes the user adds are kept.
    New messages the user saved on the desk (status 'saved') are appended at the bottom, matched by email + name."""
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    cols = [("n", "#", 5), ("name", "الجهة", 34), ("country", "الدولة", 10), ("city", "المدينة", 12), ("type", "النوع", 16),
            ("to", "الإيميل", 32), ("website", "الموقع", 30), ("about_url", "رابط المصدر", 30), ("about", "نبذة", 60),
            ("about_facts", "نقاط", 50), ("warn", "تنبيه", 30), ("lang", "اللغة", 7), ("send_name", "السيرة", 30),
            ("subject", "الموضوع", 45), ("body", "نص الرسالة", 70), ("saved_at", "تاريخ الحفظ", 18), ("notes", "ملاحظاتي", 40)]
    out = os.path.join(ROOT, "output", "saved_for_later.xlsx")
    if os.path.exists(out):
        wb = load_workbook(out); ws = wb.worksheets[0]
    else:
        wb = Workbook(); ws = wb.active; ws.title = "محفوظة للرجوع"; ws.sheet_view.rightToLeft = True
        ws.append([c[1] for c in cols])
        for i, (_, _, w) in enumerate(cols, 1):
            c = ws.cell(1, i); ws.column_dimensions[c.column_letter].width = w
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="2A9D8F")
        ws.freeze_panes = "B2"
    head = {str(ws.cell(1, j).value or "").strip(): j for j in range(1, ws.max_column + 1)}
    je, jn = head.get("الإيميل"), head.get("الجهة")
    have = {(str(ws.cell(r, je).value or "").strip().lower() if je else "", str(ws.cell(r, jn).value or "").strip() if jn else "")
            for r in range(2, ws.max_row + 1)}
    docs = []
    for f in glob.glob(os.path.join(a.dir, "queue", "*.json")):
        d = json.load(open(f, encoding="utf-8")); d = d.get("data", d)
        if d.get("status") == "saved": docs.append(d)
    added = 0
    for d in sorted(docs, key=lambda d: (str(d.get("saved_at", "")), d.get("n", 0))):
        k = (str(d.get("to", "")).strip().lower(), str(d.get("name", "")).strip())
        if k in have: continue
        r = ws.max_row + 1
        for key, label, _ in cols:
            j = head.get(label)
            if not j: continue  # the user removed that column: respect it
            v = " | ".join(d.get(key) or []) if key == "about_facts" else (AR_C.get(d.get(key), d.get(key)) if key == "country" else d.get(key, ""))
            c = ws.cell(r, j, v if v is not None else ""); c.alignment = Alignment(wrap_text=True, vertical="top")
        have.add(k); added += 1
        try: set_col14(d["country"], d["row"], "محفوظة للرجوع (مكتب الإرسال)")
        except Exception: pass
    ws.auto_filter.ref = ws.dimensions
    wb.save(out); print(f"saved_for_later: +{added} new, {ws.max_row - 1} rows total -> {out}")


def desk_edits(a):
    """learn from the user: list every message whose text the user changed on the desk (body vs body_orig).
    Appends new diffs to docs/style_edits_log.md (once per doc+version) so the writing rules in SKILL.md can be updated."""
    import difflib
    orig = {}
    rwp = os.path.join(ROOT, "output", "drafts", "batch_01_ar_rewrite.json")
    if os.path.exists(rwp):  # batch_01 predates body_orig
        sys.path.insert(0, os.path.join(ROOT, "output", "drafts")); import drafts_tool
        rw = {x["id"]: x for x in json.load(open(rwp, encoding="utf-8"))}
        for e in __import__("batch_01_emails").EMAILS:
            orig[f"b01-{e['id']:02d}"] = (rw[e["id"]]["subject"], rw[e["id"]]["body"]) if e["id"] in rw else (e["subject"], drafts_tool.editable_text(e))
    logp = os.path.join(ROOT, "docs", "style_edits_log.md"); seen = open(logp, encoding="utf-8").read() if os.path.exists(logp) else ""
    out = []
    for f in sorted(glob.glob(os.path.join(a.dir, "queue", "*.json"))):
        raw = json.load(open(f, encoding="utf-8")); d = raw.get("data", raw); did = os.path.basename(f)[:-5]
        osub, obody = (d.get("subject_orig"), d.get("body_orig")) if d.get("body_orig") else orig.get(did, (None, None))
        if obody is None: continue
        if d["body"].strip() == obody.strip() and (osub is None or d["subject"] == osub): continue
        tag = f"<!-- {did} -->"
        if tag in seen: continue
        lines = [tag, f"### {d['name']} ({d.get('country','')}, {d.get('type','')})"]
        if osub and d["subject"] != osub: lines += [f"- الموضوع قبل: {osub}", f"- الموضوع بعد: {d['subject']}"]
        for l in difflib.unified_diff(obody.strip().split("\n"), d["body"].strip().split("\n"), lineterm="", n=0):
            if l.startswith(("---", "+++", "@@")): continue
            if l.strip() in ("-", "+"): continue
            lines.append(("- حُذف: " if l.startswith("-") else "- أصبح: ") + l[1:])
        out.append("\n".join(lines))
    if out:
        os.makedirs(os.path.dirname(logp), exist_ok=True)
        with open(logp, "a", encoding="utf-8") as fh:
            if not seen: fh.write("# سجل تعديلات المستخدم على الرسائل\nكل تعديل يجريه المستخدم في مكتب الإرسال يُسجَّل هنا، ومنه تُستخرج قواعد \"أسلوب عامر\" في SKILL.md.\n\n")
            fh.write("\n\n".join(out) + "\n\n")
    print("new edits:", len(out)); [print(x) for x in out]


FREE_MAIL = {"gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "live.com", "icloud.com", "maktoob.com", "msn.com", "aol.com"}


def reply_query(a):
    """Gmail search query for replies from organizations we emailed (exact address, or the org's own domain)."""
    terms, seen = [], set()
    for f in glob.glob(os.path.join(a.dir, "queue", "*.json")):
        d = json.load(open(f, encoding="utf-8")); d = d.get("data", d)
        if d.get("status") not in ("sent",) and not d.get("replied"): continue
        em = str(d.get("to", "")).strip().lower()
        if "@" not in em: continue
        dom = em.split("@")[1]
        t = f"from:{em}" if dom in FREE_MAIL else f"from:{dom}"
        if t not in seen: seen.add(t); terms.append(t)
    q = (f"in:inbox newer_than:{a.days}d -from:mailer-daemon -from:postmaster -subject:Undeliverable -subject:\"Delivery Status\" "
         f"({' OR '.join(terms)})") if terms else ""
    open(os.path.join(DESK, "reply_query.txt"), "w", encoding="utf-8").write(q); print(q)


def replies_export(a):
    """a.file: [{thread_id, message_id, from, date, subject, text}] from Gmail -> desk 'replies' docs + logs.
    Matches each reply to the sent desk message by sender address or domain."""
    found = json.load(open(a.file, encoding="utf-8"))
    sent = {}
    for f in glob.glob(os.path.join(a.dir, "queue", "*.json")):
        d = json.load(open(f, encoding="utf-8")); d = d.get("data", d); d["_id"] = os.path.basename(f)[:-5]
        if d.get("status") == "sent" or d.get("replied"):
            em = str(d.get("to", "")).strip().lower(); sent[em] = d
            dom = em.split("@")[-1]
            if dom not in FREE_MAIL: sent.setdefault("@" + dom, d)
    out_dir = os.path.join(DESK, "replies"); os.makedirs(out_dir, exist_ok=True)
    for x in glob.glob(os.path.join(out_dir, "*.json")): os.remove(x)
    idx, matched = [], []
    for r in found:
        fr = log_tool.norm_email(re.sub(r".*<([^>]+)>.*", r"\1", str(r.get("from", ""))))
        d = sent.get(fr) or sent.get("@" + fr.split("@")[-1])
        if not d: continue
        doc = {"thread_id": r.get("thread_id"), "message_id": r.get("message_id"), "from": r.get("from"), "date": r.get("date", ""),
               "subject": r.get("subject", ""), "text": str(r.get("text", ""))[:4000], "queue_id": d["_id"], "name": d.get("name"),
               "country": d.get("country"), "sent_at": d.get("sent_at", ""),
               "gmail_url": f"https://mail.google.com/mail/u/0/#all/{r.get('thread_id')}", "read": False}
        did = "r-" + str(r.get("message_id") or r.get("thread_id"))
        fp = os.path.join(out_dir, did + ".json"); json.dump(doc, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
        idx.append({"doc_id": did, "file_path": fp, "queue_id": d["_id"]}); matched.append({"from": d.get("to"), "date": doc["date"], "subject": doc["subject"]})
    json.dump(idx, open(os.path.join(out_dir, "_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # logs: ledger + country file + applications_log status "Replied"
    if matched:
        mf = os.path.join(out_dir, "_matched.json"); json.dump(matched, open(mf, "w", encoding="utf-8"), ensure_ascii=False)
        sync_replies(argparse.Namespace(file=mf))
        from openpyxl import load_workbook as _lw
        wb = _lw(log_tool.LOG); ws = wb["Applications"]
        for m in matched:
            for r_ in log_tool.find(ws, m["from"], None, None) or []:
                row = r_[0] if isinstance(r_, (list, tuple)) else r_
                try:
                    ws.cell(row, log_tool.C["الحالة"]).value = "Replied"
                    ws.cell(row, log_tool.C["تاريخ آخر تحديث"]).value = today().isoformat()
                except Exception: pass
        wb.save(log_tool.LOG)
    print("replies matched:", len(idx))


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
    x.add_argument("--status", default="ready", choices=["ready", "reserve"], help="reserve = hidden replacements promoted when the user postpones/excludes")
    x = sp.add_parser("sync-desk"); x.add_argument("--dir", required=True)
    x = sp.add_parser("send-plan"); x.add_argument("--dir", required=True); x.add_argument("--gmail-error", action="store_true", help="Gmail returned a sending-limit / suspicious-activity error: step the ramp down one stage")
    x = sp.add_parser("verify-emails"); x.add_argument("--dir"); x.add_argument("--run"); x.add_argument("--status", default="approved")
    x = sp.add_parser("ramp"); x.add_argument("--no-update", action="store_true")
    x = sp.add_parser("desk-saved"); x.add_argument("--dir", required=True)
    x = sp.add_parser("careers"); x.add_argument("--dir", help="desk copy (ArtifactData list careers out_dir) to read the applied flags")
    x = sp.add_parser("desk-edits"); x.add_argument("--dir", required=True)
    x = sp.add_parser("reply-query"); x.add_argument("--dir", required=True); x.add_argument("--days", type=int, default=14)
    x = sp.add_parser("replies-export"); x.add_argument("--dir", required=True); x.add_argument("--file", required=True)
    for n in ("sync-wa", "stats", "migrate-batch01"):
        sp.add_parser(n)
    a = ap.parse_args()
    {"quota": quota, "select": select, "build": build, "record": record, "wa-queue": wa_queue, "mark": mark,
     "sync-sent": sync_sent, "sync-wa": sync_wa, "sync-bounces": sync_bounces, "sync-replies": sync_replies,
     "stats": stats, "migrate-batch01": migrate_batch01, "desk-export": desk_export, "sync-desk": sync_desk, "send-plan": send_plan, "verify-emails": verify_emails, "ramp": lambda a: print(json.dumps(ramp_state(update=not a.no_update), ensure_ascii=False)), "desk-saved": desk_saved, "careers": careers, "desk-edits": desk_edits, "reply-query": reply_query, "replies-export": replies_export}[a.cmd](a)


if __name__ == "__main__":
    main()
