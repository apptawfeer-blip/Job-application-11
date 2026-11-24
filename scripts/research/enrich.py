"""Fill missing email/phone/whatsapp in an import JSON by visiting each target's website.
usage: python3 -I enrich.py in.json out.json [country_code]"""
import re, sys, json, subprocess, html, urllib.parse
from concurrent.futures import ThreadPoolExecutor
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
BAD=re.compile(r"(example|sentry|wixpress|domain\.com|email\.com|yourmail|\.(png|jpe?g|gif|webp|svg|css|js)$|@2x|godaddy|cloudflare|schema\.org|w3\.org|jquery|bootstrap)",re.I)
def get(u):
    # the sandbox only reaches the web through an HTTPS proxy: plain http:// fails DNS, so upgrade
    if u.startswith("http://"): u = "https://" + u[7:]
    try:
        r=subprocess.run(["curl","-s","-m","20","-L","--max-filesize","3000000","-A",UA,u],capture_output=True,timeout=30)
        return r.stdout.decode("utf-8","ignore")
    except Exception: return ""
def extract(t):
    t2=html.unescape(t)
    em=[e for e in dict.fromkeys(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}",t2)) if not BAD.search(e)]
    em+= [urllib.parse.unquote(m) for m in re.findall(r'mailto:([^"\'?>\s]+)',t) if not BAD.search(m)]
    tel=[re.sub(r"[^\d+]","",x) for x in re.findall(r'href=["\']tel:([^"\']+)',t)]
    wa=re.findall(r'(?:wa\.me/|api\.whatsapp\.com/send/?\?phone=|whatsapp\.com/send\?phone=)\+?(\d{8,15})',t)
    return list(dict.fromkeys(em)),list(dict.fromkeys(x for x in tel if len(re.sub(r"\D","",x))>=7)),list(dict.fromkeys(wa))
def contact_links(base,t):
    ls=[]
    for h,txt in re.findall(r'<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>',t,re.S|re.I):
        s=(h+" "+re.sub(r"<[^>]+>","",txt)).lower()
        if any(k in s for k in ("contact","اتصل","تواصل","career","jobs","وظائف","join")):
            ls.append(urllib.parse.urljoin(base,h))
    return list(dict.fromkeys(ls))[:4]
def norm_site(w):
    w=(w or "").split(",")[0].strip()
    if not w: return ""
    if not w.startswith("http"): w="https://"+w
    return w
def work(x):
    site=norm_site(x.get("website"))
    if not site or (x.get("email") and x.get("phone")): return x
    t=get(site); pages=[t]
    for l in contact_links(site,t): pages.append(get(l))
    if not any(pages):
        x["notes"]=((x.get("notes") or "")+" | الموقع لا يستجيب").strip(" |"); return x
    E,T,W=[],[],[]
    for p in pages:
        e,tl,w=extract(p); E+=e; T+=tl; W+=w
    dom=urllib.parse.urlparse(site).netloc.replace("www.","")
    E=sorted(dict.fromkeys(E),key=lambda e:(dom.split(".")[0] not in e, not re.match(r"(hr|career|jobs|recruit)",e), e))
    if not x.get("email") and E: x["email"]=", ".join(E[:2]); x["notes"]=((x.get("notes") or "")+" | الإيميل من موقع الجهة").strip(" |")
    if not x.get("phone") and T: x["phone"]=", ".join(list(dict.fromkeys(T))[:2])
    if not x.get("whatsapp") and W: x["whatsapp"]=W[0]
    return x
if __name__=="__main__":
    d=json.load(open(sys.argv[1],encoding="utf-8"))
    import os
    with ThreadPoolExecutor(int(os.environ.get("ENRICH_THREADS","5"))) as ex: d["targets"]=list(ex.map(work,d["targets"]))
    json.dump(d,open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    ts=d["targets"]; print(len(ts),"email",sum(1 for x in ts if x.get("email")),"phone",sum(1 for x in ts if x.get("phone")),"wa",sum(1 for x in ts if x.get("whatsapp")))
