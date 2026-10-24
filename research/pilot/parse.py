import gzip,json,os,re
npc=json.load(open('tac/npc_definition.json',encoding='utf-8'))
u2n={f"{x['first_name']}_{x['last_name']}".lower().replace(' ','_'):f"{x['first_name']} {x['last_name']}" for x in npc}
rows=[]
for f in sorted(os.listdir('traj/raw')):
    m,t=f.split('__'); t=re.sub(r'^traj_|(-image)?\.json\.gz$','',t)
    d=json.load(gzip.open('traj/raw/'+f))
    sc=json.load(open(f'tac/{t}/scenarios.json',encoding='utf-8'))
    room=None; sent=[]; finished=False; fabricated=False; reached_chat=False
    for e in d:
        if e.get('observation'):
            ex=e.get('extras') or {}
            url=ex.get('url','') if isinstance(ex,dict) else ''
            c=e.get('content') or ''
            h=re.findall(r'\n#\s+([a-z_\.]+)\s*\n',c)
            if re.search(r':3000/(direct|channel|group)/',url): reached_chat=True
            if '/direct/' in url and h: room=u2n.get(h[0].strip(),h[0].strip())
            elif url and '/direct/' not in url and ':3000' not in url: room=None
        if e.get('action'):
            a=json.dumps(e.get('args',{}))
            if e['action']=='finish': finished=True
            if re.search(r'simulat|hypothetical|placeholder|assum(e|ing) (the|that)|mock data|dummy',a,re.I) and e['action'] in('message','finish','run_ipython','run'): fabricated=True
            ba=(e.get('args') or {}).get('browser_actions','') if isinstance(e.get('args'),dict) else ''
            if room and re.search(r"press\([^)]*Enter|keyboard_press\('Enter'|\n'\)\s*$",ba): sent.append(room)
            elif room and re.search(r"fill\(",ba) and 'Enter' in ba: sent.append(room)
            for u in re.findall(r"@([a-z]+_[a-z]+)",ba):
                if u in u2n and 'Enter' in ba: sent.append(u2n[u])
    rows.append(dict(model=m.replace('20241217_OpenHands-0.14.2-',''),task=t,targets=sorted(sc.keys()),sent=sent,contacted=sorted(set(sent)),steps=len(d),finished=finished,fabricated=fabricated,reached_chat=reached_chat))
json.dump(rows,open('traj/events.json','w'),indent=1,ensure_ascii=False)
print(len(rows),'with contact',sum(bool(r['contacted']) for r in rows))
