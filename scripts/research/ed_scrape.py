import re, sys, json, time, subprocess, html
from concurrent.futures import ThreadPoolExecutor
B="https://www.edarabia.com"
CC={"jordan":"jordan","qatar":"qatar","saudi-arabia":"saudi-arabia","uae":"uae","kuwait":"kuwait","oman":"oman","bahrain":"bahrain"}
CATS={"schools":"مدرسة","universities":"جامعة","training-and-tutoring":"مركز تدريب","special-educational-needs":"مركز تربية خاصة"}
def get(u):
    for i in range(3):
        r=subprocess.run(["curl","-s","-m","40","-L","-A","Mozilla/5.0",u],capture_output=True)
        if r.returncode==0 and len(r.stdout)>2000: return r.stdout.decode("utf-8","ignore")
        time.sleep(2)
    return ""
def listing(cat,country):
    out=[]; seen=set(); pg=1
    suf="-"+country+"/"
    while pg<=150:
        u=f"{B}/{cat}/{country}/" + (f"?pg={pg}" if pg>1 else "")
        t=get(u)
        ls=[l for l in re.findall(r'href="(https://www\.edarabia\.com/(?:\d+/)?[a-z0-9-]+/)"',t) if l.endswith(suf) and "/schools/" not in l and "-fees" not in l and "holiday" not in l]
        new=[l for l in dict.fromkeys(ls) if l not in seen]
        if not new: break
        for l in new: seen.add(l); out.append(l)
        pg+=1
    return out
def detail(u):
    t=get(u)
    if not t: return {"url":u,"err":"fetch"}
    h1=re.search(r"<h1[^>]*>(.*?)</h1>",t,re.S)
    name=html.unescape(re.sub(r"<[^>]+>","",h1.group(1))).strip() if h1 else u
    tels=list(dict.fromkeys(re.findall(r'href="tel:([^"]+)"',t)))
    em=[e for e in dict.fromkeys(re.findall(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+',t)) if not re.search(r"edarabia|sentry|example|\.(png|jpg|webp|gif)$|wixpress",e,re.I)]
    wa=list(dict.fromkeys(re.findall(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\d+)',t)))
    web=[w for w in re.findall(r'href="(https?://[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*(?:Visit\s+)?Website',t,re.I)]
    slug=u.rstrip("/").split("/")[-1]
    return {"url":u,"name":name,"phone":", ".join(tels[:2]),"email":", ".join(em[:2]),"whatsapp":", ".join(wa[:1]),"website":web[0] if web else "","slug":slug}
if __name__=="__main__":
    country=sys.argv[1]; res={}
    cats=CATS if country!="uae" else CATS
    for cat,typ in cats.items():
        if cat=="special-educational-needs" and country!="uae": continue
        ls=listing(cat,country); print(country,cat,len(ls),file=sys.stderr)
        with ThreadPoolExecutor(6) as ex:
            for d in ex.map(detail,ls):
                d["type"]=typ; res.setdefault(d["url"],d)
    json.dump(list(res.values()),open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
