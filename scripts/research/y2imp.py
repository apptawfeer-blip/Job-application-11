import json,sys,re
d=json.load(open(sys.argv[1],encoding="utf-8")); out=[]
SN=re.compile(r"special (need|educ)|autis|disab|rehab|determination|learning (difficult|disab)|dyslex|speech|therap|down syndrome|deaf|blind|تربية خاصة|توحد|إعاقة|تأهيل|صعوبات|همم|نطق",re.I)
for x in d:
    s=(x["name"]+" "+x.get("desc","")).lower(); t=x["type"]
    if SN.search(s): t="مركز تربية خاصة"
    elif re.search(r"universit|college|جامعة|كلية",x["name"],re.I): t="جامعة"
    elif re.search(r"school|academy|مدرسة|مدارس|kindergarten|nursery|روضة",x["name"],re.I): t="مدرسة"
    elif re.search(r"training|institute|cent(er|re)|tutor|معهد|مركز",x["name"],re.I): t="مركز تدريب"
    out.append({"name":x["name"],"type":t,"phone":x["phone"],"email":x["email"],"website":x["website"],"city":x["city"],"source":x["source"]})
json.dump({"targets":out},open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=1); print(len(out))
