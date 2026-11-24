import re,sys,json,html,subprocess,time
from concurrent.futures import ThreadPoolExecutor
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
host=sys.argv[1]; cats=sys.argv[2].split(","); out=sys.argv[3]
def get(u):
    for i in range(3):
        r=subprocess.run(["curl","-s","-m","30","-L","-A",UA,u],capture_output=True)
        t=r.stdout.decode("utf-8","ignore")
        if len(t)>3000: return t
        time.sleep(3)
    return ""
TYPEMAP={"schools":"مدرسة","education":"مدرسة","colleges":"جامعة","universities":"جامعة","training":"مركز تدريب","childrens_services":"مركز تربية خاصة","kindergartens":"مدرسة","associations":"جمعية","charity":"جمعية","nonprofit_organizations":"جمعية","special_education":"مركز تربية خاصة"}
links={}
for c in cats:
    p=1
    while p<=60:
        t=get(f"https://{host}/category/{c}"+(f"/{p}" if p>1 else ""))
        ls=re.findall(r'href="(/company/\d+/[^"/]+)"',t)
        new=[l for l in dict.fromkeys(ls) if l not in links]
        if not new: break
        for l in new: links[l]=c
        p+=1
    print(host,c,sum(1 for v in links.values() if v==c),file=sys.stderr)
def det(item):
    l,c=item; u=f"https://{host}{l}"; t=get(u)
    if not t or "BUSINESS CLOSED" in t: return None
    name=re.search(r"<h1[^>]*>(.*?)</h1>",t,re.S); name=html.unescape(re.sub(r"<[^>]+>","",name.group(1))).strip() if name else l
    name=re.sub(r"\s*-\s*[^-]+,\s*[^-]+$","",name)
    tel=list(dict.fromkeys(x.strip() for x in re.findall(r'href="tel:([^"]+)"',t)))
    em=[e for e in dict.fromkeys(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}",t)) if host.split(".")[1] not in e]
    city=re.search(r'Address</[^>]+>.*?\n?.*?<[^>]+>([^<]*)</',t,re.S)
    cityl=re.findall(r'href="/location/([^"]+)"',t)
    web=re.search(r'Website address</[^>]+>\s*<[^>]+>\s*(?:<a[^>]+href="([^"]+)")?',t)
    desc=re.search(r"Company description</[^>]+>(.*?)</div>",t,re.S)
    d=html.unescape(re.sub(r"<[^>]+>"," ",desc.group(1))).strip()[:300] if desc else ""
    w=web.group(1) if web and web.group(1) else ""
    if "facebook.com/login" in w: w=""
    return {"name":name,"type":TYPEMAP.get(c,"أخرى"),"phone":", ".join(tel[:2]),"email":", ".join(em[:2]),"website":w,
            "city":cityl[0].replace("_"," ") if cityl else "","source":u,"desc":d}
with ThreadPoolExecutor(8) as ex: res=[r for r in ex.map(det,links.items()) if r and (r["phone"] or r["email"])]
json.dump(res,open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1); print(host,"kept",len(res),file=sys.stderr)
