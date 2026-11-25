"""Crawl gludo.org education listings for one country: python3 -I gludo.py <gludo-country> out.json"""
import re, sys, json, html, subprocess
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
KEEP = re.compile(r"educat|school|train|universit|college|kinder|nurser|special|disab|autism|tutor|institut|academ|charit|associat|nonprofit|ngo|rehab", re.I)
def get(u):
    r = subprocess.run(["curl", "-s", "-m", "30", "-L", "-A", UA, u], capture_output=True); return r.stdout.decode("utf-8", "ignore")
c = sys.argv[1]; base = "https://gludo.org/en/business-directory/"
start = f"{base}country/{c}/"
seen, queue, details = set(), [start], set()
while queue and len(seen) < 400:
    u = queue.pop(0)
    if u in seen: continue
    seen.add(u); t = get(u)
    for d in re.findall(r'href="(https://gludo\.org/en/business-directory/\d+-[^"]+)"', t): details.add(d)
    for l in re.findall(r'href="(https://gludo\.org/en/business-directory/(?:country|city)/[^"]+)"', t):
        l = html.unescape(l)
        if l in seen: continue
        if u == start or KEEP.search(l): queue.append(l)
    for p in re.findall(r'href="([^"]*[?&]page=\d+[^"]*)"', t):
        p = html.unescape(p); p = p if p.startswith("http") else u.split("?")[0] + p[p.find("?"):]
        if p not in seen: queue.append(p)
print(c, "pages", len(seen), "details", len(details), file=sys.stderr)
def det(u):
    t = get(u)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S); name = html.unescape(re.sub(r"<[^>]+>", "", h1.group(1))).strip() if h1 else ""
    cat = " ".join(re.findall(r'href="https://gludo\.org/en/business-directory/country/[^/]+/([^/"]+)/"', t))
    if not KEEP.search(cat + " " + name): return None
    tel = list(dict.fromkeys(re.sub(r"[^\d+]", "", x) for x in re.findall(r'href="tel:([^"]+)"', t)))
    em = [e for e in dict.fromkeys(re.findall(r"mailto:([^\"?]+)", t)) if "gludo" not in e]
    wa = [w for w in re.findall(r"wa\.me/\+?(\d{8,15})", t)]
    web = [w for w in re.findall(r'href="(https?://[^"]+)"[^>]*rel="[^"]*nofollow', t) if "gludo" not in w and "google" not in w]
    city = re.findall(r'href="https://gludo\.org/en/business-directory/city/([^/"]+)/', t)
    return {"name": name, "cat": cat, "phone": ", ".join(tel[:2]), "email": ", ".join(em[:2]), "whatsapp": wa[0] if wa else "",
            "website": web[0] if web else "", "city": city[0].replace("-", " ") if city else "", "source": u}
with ThreadPoolExecutor(8) as ex: res = [r for r in ex.map(det, sorted(details)) if r and r["name"] and (r["phone"] or r["email"] or r["whatsapp"])]
json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(c, "kept", len(res), file=sys.stderr)
