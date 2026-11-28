import re, sys, json, time, subprocess, html, urllib.parse
from concurrent.futures import ThreadPoolExecutor
BASE="https://madaresonajo.com"
SITE_PHONE="962796385230"
CATS={"centers-for-people-with-special-needs":"مركز تربية خاصة","private-schools":"مدرسة",
      "colleges-and-universities":"جامعة","training-and-consulting":"مركز تدريب"}
def get(u):
    for i in range(3):
        r=subprocess.run(["curl","-s","-m","40","-L",u],capture_output=True)
        if r.returncode==0 and r.stdout: return r.stdout.decode("utf-8","ignore")
        time.sleep(2)
    return ""
def links(cat):
    out=set(); p=1
    while True:
        t=get(f"{BASE}/en/institutions/{cat}?page={p}")
        ls={l for l in re.findall(r'href="/en/institutions/([^"?#/]+)"',t) if l not in CATS and l not in ("kindergartens","nurseries")}
        new=ls-out
        if not new: break
        out|=new; p+=1
        if p>200: break
    return out
def detail(slug):
    u=f"{BASE}/en/institutions/{slug}"; t=get(u)
    if not t: return {"slug":slug,"url":u,"err":"fetch"}
    def f(k):
        m=re.findall(r'\\"'+k+r'\\":\\"([^\\]{0,200})',t); return m
    name=re.search(r"<title>(.*?) \| Madaresona",t); name=html.unescape(name.group(1)) if name else slug
    emails=sorted(set(e for e in f("email") if "@" in e))
    phones=sorted(set(p for p in f("phone") if re.search(r"\d{6}",p) and SITE_PHONE not in re.sub(r"\D","",p)))
    was=sorted(set(w for w in re.findall(r"wa\.me/(\d+)",t) if w!=SITE_PHONE))
    city=(f("cityName") or [""])[0]
    webs=sorted(set(w for w in re.findall(r'\\"(?:websiteUrl|website)\\":\\"(https?://[^\\]+)',t) if "madaresona" not in w))
    return {"slug":slug,"url":u,"name":name,"city":city,"email":", ".join(emails),"phone":", ".join(phones),"whatsapp":", ".join(was),"website":", ".join(webs[:1])}
if __name__=="__main__":
    out={}
    for cat,typ in CATS.items():
        ls=sorted(links(cat)); print(cat,len(ls),file=sys.stderr)
        with ThreadPoolExecutor(8) as ex:
            for d in ex.map(detail,ls):
                d["type"]=typ; out.setdefault(d["slug"],d)
    json.dump(list(out.values()),open(sys.argv[1],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
