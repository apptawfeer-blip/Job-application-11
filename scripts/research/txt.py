import re,sys,html
t=open(sys.argv[1],encoding='utf-8',errors='ignore').read()
t=re.sub(r'<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>','',t,flags=re.S)
x=html.unescape(re.sub(r'<br\s*/?>','\n',t)); x=re.sub(r'<[^>]+>','\n',x)
x='\n'.join(l.strip() for l in x.split('\n') if l.strip())
a=x.find(sys.argv[2]) if len(sys.argv)>2 else 0
print(x[max(a,0):max(a,0)+int(sys.argv[3]) if len(sys.argv)>3 else 4000])
