import urllib.request,urllib.parse,json,time,sys,re
def inv(ii):
    if not ii: return ''
    w=[None]*(max(p for v in ii.values() for p in v)+1)
    for k,v in ii.items():
        for p in v: w[p]=k
    return ' '.join(x for x in w if x)
out={}
for t in [l.strip() for l in open(sys.argv[1],encoding='utf-8') if l.strip()]:
    u='https://api.openalex.org/works?per_page=1&mailto=x@example.com&search='+urllib.parse.quote(re.sub(r'[^\w\s-]',' ',t))
    try:
        r=json.load(urllib.request.urlopen(u,timeout=30))['results']
        if r:
            w=r[0]; loc=(w.get('primary_location') or {}).get('source') or {}
            out[t]={'title':w['title'],'year':w['publication_year'],'venue':loc.get('display_name'),'doi':w.get('doi'),
              'authors':[a['author']['display_name'] for a in w['authorships'][:5]],'cited':w['cited_by_count'],'abs':inv(w.get('abstract_inverted_index'))}
    except Exception as e: out[t]={'err':str(e)}
    time.sleep(1)
json.dump(out,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
