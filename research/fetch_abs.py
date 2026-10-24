import urllib.request,urllib.parse,re,json,time,sys
titles=[l.strip() for l in open(sys.argv[1],encoding='utf-8') if l.strip()]
out={}
for t in titles:
    q=urllib.parse.quote('ti:"'+re.sub(r'[^\w\s-]',' ',t).strip()+'"')
    url=f'http://export.arxiv.org/api/query?search_query={q}&max_results=1'
    try:
        x=urllib.request.urlopen(url,timeout=30).read().decode()
        e=re.search(r'<entry>(.*?)</entry>',x,re.S)
        if e:
            e=e.group(1)
            g=lambda k:re.sub(r'\s+',' ',re.search(f'<{k}[^>]*>(.*?)</{k}>',e,re.S).group(1)).strip()
            out[t]={'title':g('title'),'id':g('id'),'published':g('published')[:10],'abs':g('summary'),
                    'authors':[re.sub(r'\s+',' ',a) for a in re.findall(r'<name>(.*?)</name>',e)][:6],
                    'comment':(re.search(r'<arxiv:comment[^>]*>(.*?)</arxiv:comment>',e,re.S) or [None,''])[1]}
        else: out[t]=None
    except Exception as ex: out[t]={'err':str(ex)}
    time.sleep(3.2)
json.dump(out,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(sum(1 for v in out.values() if v and 'abs' in v),'/',len(out))
