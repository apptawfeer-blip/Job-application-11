import re,sys,html,json
t=open(sys.argv[1],encoding='utf-8',errors='ignore').read()
t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
x=html.unescape(re.sub(r'<[^>]+>','\n',t)); lines=[l.strip() for l in x.split('\n') if l.strip()]
start=next(i for i,l in enumerate(lines) if l.startswith('مدارس الإعاقة السمعية'))
out=[];cur=None;section=''
for l in lines[start:]:
    if l.startswith('مدارس ') or l in ('متلازمة داون','الإعاقة الحركية','صعوبات التعلم','الإعاقة الفكرية','مراكز التأهيل'):
        section=l; continue
    if l.startswith('المدينة'):
        if cur: cur['city']=l.split(':',1)[-1].strip()
        continue
    if re.match(r'^(العنوان|الموقع الإلكتروني|بريد الإلكتروني|البريد الإلكتروني|الهاتف|هاتف|صفحة تويتر)',l):
        if not cur: continue
        k,_,v=l.partition(':'); v=v.strip().replace('. ','.').replace(' .','.')
        if 'بريد' in k and '@' in v: cur['email']=v.replace(' ','')
        elif 'هاتف' in k: cur['phone']=v
        elif 'الموقع' in k and v not in ('','-'): cur['website']=v.replace(' ','')
        continue
    if len(l)>80 or 'سيدتي' in l or l.startswith('اقرئي') : 
        if out and len(l)>80: break
        continue
    cur={'name':l,'type':'مركز تربية خاصة','city':'','source':'https://www.sayidaty.net/node/448641','notes':'دليل سيدتي 2016 – '+section+' – يُفضّل التحقق'}
    out.append(cur)
out=[o for o in out if o.get('phone') or o.get('email')]
json.dump({'targets':out},open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(out)); [print(o) for o in out[:3]+out[-3:]]
