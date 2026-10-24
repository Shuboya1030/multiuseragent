import os,sys,urllib.request,concurrent.futures as cf
tasks=[l.strip() for l in open('tac/npc_tasks.txt') if l.strip() and l.strip()!='example']
paths=[l.strip() for l in open('traj/all.txt')]
sel=[p for p in paths if any(f"/traj_{t}-image.json.gz" in p or p.endswith(f"/traj_{t}.json.gz") for t in tasks)]
print(len(sel))
def get(p):
    out='traj/raw/'+p.split('/')[2].replace(':','_')+'__'+p.split('/')[-1]
    if os.path.exists(out): return
    urllib.request.urlretrieve('https://raw.githubusercontent.com/TheAgentCompany/experiments/main/'+urllib.parse.quote(p),out)
import urllib.parse
os.makedirs('traj/raw',exist_ok=True)
with cf.ThreadPoolExecutor(8) as ex: list(ex.map(get,sel))
print(len(os.listdir('traj/raw')))
