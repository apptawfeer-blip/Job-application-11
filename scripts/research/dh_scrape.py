import re,sys,json,html,subprocess
from concurrent.futures import ThreadPoolExecutor
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
def get(u):
    r=subprocess.run(["curl","-s","-m","40","-L","-A",UA,u],capture_output=True); return r.stdout.decode("utf-8","ignore")
def cf(h):
    k=int(h[:2],16); return "".join(chr(int(h[i:i+2],16)^k) for i in range(2,len(h),2))
COUNTRY={"Jordan":"Jordan","Saudi":"Saudi","United Arab Emirates":"UAE","UAE":"UAE","Qatar":"Qatar","Kuwait":"Kuwait","Oman":"Oman","Bahrain":"Bahrain"}
TYPE={"Private School":"مدرسة","Public School":"مدرسة","Special Needs Center":"مركز تربية خاصة","Non-Governmental Organisation":"منظمة","Public University":"جامعة","Private University":"جامعة","Public Inclusive Education":"جهة حكومية","Private Organisation":"مركز تربية خاصة","Governmental":"جهة حكومية","International Organisation":"منظمة"}
def page(n):
    u="https://disability-hub.com/arab-world-directory/"+(f"page/{n}/" if n>1 else "")
    t=get(u); t=re.sub(r'<a[^>]*data-cfemail="([0-9a-f]+)"[^>]*>.*?</a>',lambda m:cf(m.group(1)),t,flags=re.S)
    t=re.sub(r'<span[^>]*data-cfemail="([0-9a-f]+)"[^>]*>.*?</span>',lambda m:cf(m.group(1)),t,flags=re.S)
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    x=html.unescape(re.sub(r'<[^>]+>','\n',t)); L=[l.strip() for l in x.split('\n') if l.strip()]
    out=[];cur=None
    for i,l in enumerate(L):
        if i+1<len(L) and L[i+1]=="Type of Organization:":
            cur={"name":l,"src":u}; out.append(cur); continue
        if cur is None: continue
        for k in ("Type of Organization:","Address:","Phone:","Email:","Website:"):
            if l==k and i+1<len(L): cur[k[:-1]]=L[i+1]
    return out
if __name__=="__main__":
    last=int(sys.argv[1]); res=[]
    with ThreadPoolExecutor(8) as ex:
        for o in ex.map(page,range(1,last+1)): res+=o
    out={}
    for o in res:
        addr=o.get("Address","")
        c=next((v for k,v in COUNTRY.items() if k in addr),None)
        if not c: continue
        typ=o.get("Type of Organization","")
        city=addr.split(",")[-2].strip() if addr.count(",")>=1 else ""
        out.setdefault(c,[]).append({"name":o["name"],"type":TYPE.get(typ,"مركز تربية خاصة" if "Center" in typ or "Centre" in typ else "أخرى"),
          "phone":o.get("Phone",""),"email":o.get("Email","") if "@" in o.get("Email","") else "","website":o.get("Website",""),
          "city":city,"source":o["src"],"notes":"Disability Hub – "+typ})
    for c,v in out.items():
        json.dump({"targets":v},open(f"{sys.argv[2]}/dh_{c}.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(c,len(v),"email",sum(1 for x in v if x["email"]))
    print("total parsed",len(res))
