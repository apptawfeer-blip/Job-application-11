"""Collect institutions + official websites from Wikipedia list pages.
usage: python3 -I wiki_lists.py <Country> out.json "Page_Title_1" "Page_Title_2" ...
Uses the Wikipedia API (parse) and keeps list items/table rows that contain an external link."""
import re, sys, json, html, subprocess, urllib.parse
UA = "job-research-script/1.0"
def api(title):
    u = "https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=text&redirects=1&page=" + urllib.parse.quote(title)
    import time
    for i in range(4):
        r = subprocess.run(["curl", "-s", "-m", "40", "-A", UA, u], capture_output=True)
        try: return json.loads(r.stdout)["parse"]["text"]["*"]
        except Exception: time.sleep(8 * (i + 1))
    print("failed:", title, file=sys.stderr); return ""
SKIP = re.compile(r"wikipedia|wikimedia|wikidata|archive\.org|doi\.org|google\.|facebook|twitter|youtube|instagram|geohack|worldcat|jstor|bbc\.|reuters|gulfnews|thenational|arabnews|aljazeera|zawya|khaleejtimes", re.I)
country, out = sys.argv[1], sys.argv[2]; res = {}
for title in sys.argv[3:]:
    t = api(title)
    for blk in re.findall(r"<(?:li|tr)[^>]*>(.*?)</(?:li|tr)>", t, re.S):
        ext = [l for l in re.findall(r'<a[^>]*class="external[^"]*"[^>]*href="(https?://[^"]+)"|<a[^>]*href="(https?://[^"]+)"[^>]*class="external', blk) for l in l if l]
        ext = [l for l in ext if not SKIP.search(l)]
        if not ext: continue
        txt = html.unescape(re.sub(r"<[^>]+>", " | ", blk)); parts = [p.strip() for p in txt.split("|") if p.strip() and not p.strip().startswith("[")]
        name = parts[0] if parts else ""
        if not name or len(name) > 90: continue
        dom = urllib.parse.urlparse(ext[0]).netloc.replace("www.", "")
        typ = "جامعة" if re.search(r"universit|college|institute of tech", name, re.I) or "universit" in title.lower() else "مدرسة"
        res.setdefault(dom, {"name": name, "type": typ, "website": ext[0], "source": "https://en.wikipedia.org/wiki/" + title, "city": ""})
json.dump({"targets": list(res.values())}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(country, len(res))
