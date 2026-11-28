import json, sys, re
CITY_AR={"amman":"عمّان","irbd":"إربد","irbid":"إربد","al-zarqa":"الزرقاء","zarqa":"الزرقاء","al-salet":"السلط","salt":"السلط","al-karak":"الكرك","karak":"الكرك","al-mafraq":"المفرق","mafraq":"المفرق","al-aqaba":"العقبة","aqaba":"العقبة","ajloon":"عجلون","ajloun":"عجلون","jerash":"جرش","madaba":"مادبا","maan":"معان","tafileh":"الطفيلة","al-tafila":"الطفيلة","doha":"الدوحة","dubai":"دبي","abu-dhabi":"أبوظبي","sharjah":"الشارقة","ajman":"عجمان","al-ain":"العين","ras-al-khaimah":"رأس الخيمة","fujairah":"الفجيرة","umm-al-quwain":"أم القيوين","riyadh":"الرياض","jeddah":"جدة","dammam":"الدمام","al-khobar":"الخبر","khobar":"الخبر","makkah":"مكة","mecca":"مكة","madinah":"المدينة المنورة","medina":"المدينة المنورة","dhahran":"الظهران","jubail":"الجبيل","kuwait-city":"مدينة الكويت","salmiya":"السالمية","hawally":"حولي","muscat":"مسقط","sohar":"صحار","salalah":"صلالة","nizwa":"نزوى","manama":"المنامة","riffa":"الرفاع","isa-town":"مدينة عيسى","muharraq":"المحرق","al-wakra":"الوكرة","al-rayyan":"الريان","lusail":"لوسيل"}
def city_from(s):
    s=(s or "").strip()
    if not s: return ""
    k=s.lower().replace(" ","-")
    return CITY_AR.get(k,s)
def city_from_slug(slug,country):
    base=re.sub(r"-"+country+r"$","",slug)
    for k in sorted(CITY_AR,key=len,reverse=True):
        if base.endswith("-"+k) or base==k: return CITY_AR[k]
    return ""
def clean_web(w): return re.sub(r"[?&]utm_source=Edarabia\.com","",w or "")
def main():
    country_slug, out = sys.argv[1], sys.argv[2]; files=sys.argv[3:]
    targets=[]
    for f in files:
        for x in json.load(open(f,encoding="utf-8")):
            if x.get("err"): continue
            if not (x.get("email") or x.get("phone") or x.get("whatsapp")): continue
            src=x["url"]
            city=city_from(x.get("city")) or city_from_slug(x.get("slug",""),country_slug)
            note=""
            if "madaresonajo" in src and not x.get("phone"): note="الهاتف مخفي في الدليل"
            targets.append({"name":x["name"],"type":x["type"],"phone":x.get("phone",""),"whatsapp":x.get("whatsapp",""),
                "email":x.get("email",""),"city":city,"website":clean_web(x.get("website","")),"source":src,"notes":note})
    json.dump({"targets":targets},open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(len(targets))
main()
