"""Scan each target's website (home + contact pages) for WhatsApp links, mobile numbers and social-media links.
usage: python3 -I wa_scan.py <Country> in.json out.json      (in.json from targets_tool.py export-web)
Output rows keep name/website and add: whatsapp (confirmed wa links), mobiles (mobile numbers seen on the site),
social (facebook/instagram/... links) -> import with targets_tool.py import (fills empty columns) + whatsapp."""
import re, sys, json, os, html, urllib.parse
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich import get, contact_links, norm_site
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from targets_tool import to_intl, is_mobile

SOC = re.compile(r'href=["\'](https?://(?:www\.|m\.|web\.)?(?:facebook\.com|fb\.com|instagram\.com|linkedin\.com|x\.com|twitter\.com|tiktok\.com|snapchat\.com)/[^"\'#?\s]+)', re.I)
WA = re.compile(r'(?:wa\.me/|api\.whatsapp\.com/send/?\?phone=|whatsapp\.com/send\?phone=|whatsapp://send\?phone=)\+?(\d{8,15})', re.I)
NUM = re.compile(r'(?<!\d)(?:\+|00)?\d[\d\s().-]{7,16}\d(?!\d)')


def scan(country, x):
    site = norm_site(x.get("website"))
    if not site: return x
    t = get(site); pages = [t] + [get(l) for l in contact_links(site, t)]
    if not any(pages): return x
    wa, mob, soc = [], [], []
    for p in pages:
        wa += WA.findall(p)
        soc += [s for s in SOC.findall(p) if not re.search(r"/(sharer|share|intent|plugins|dialog)", s)]
        txt = html.unescape(re.sub(r"<[^>]+>", " ", p))
        cands = re.findall(r'href=["\']tel:([^"\']+)', p) + NUM.findall(txt)
        for c in cands:
            n = to_intl(c, country)
            if is_mobile(n, country): mob.append(n)
    wa = list(dict.fromkeys(to_intl(w, country) for w in wa))
    mob = list(dict.fromkeys(mob))
    if wa: x["whatsapp"] = ", ".join("+" + w for w in wa[:2]); x["wa_status"] = "مؤكد – رابط واتساب في موقع الجهة"
    elif mob: x["mobile"] = ", ".join("+" + m for m in mob[:2]); x["wa_status"] = "جوال من موقع الجهة – غالباً واتساب"
    if soc: x["social"] = ", ".join(list(dict.fromkeys(soc))[:3])
    return x


if __name__ == "__main__":
    country, src, out = sys.argv[1:4]
    d = json.load(open(src, encoding="utf-8"))
    with ThreadPoolExecutor(int(os.environ.get("ENRICH_THREADS", "8"))) as ex:
        d["targets"] = list(ex.map(lambda x: scan(country, x), d["targets"]))
    json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ts = d["targets"]
    print(country, len(ts), "wa", sum(1 for x in ts if x.get("whatsapp")), "mobile", sum(1 for x in ts if x.get("mobile")),
          "social", sum(1 for x in ts if x.get("social")))
