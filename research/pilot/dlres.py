import os,urllib.request,urllib.parse,concurrent.futures as cf,json
tasks=[l.strip() for l in open('tac/npc_tasks.txt') if l.strip() and l.strip()!='example']
paths=[l.strip() for l in open('traj/res.txt')]
sel=[p for p in paths if '20250510' not in p and any(p.endswith(f"/eval_{t}-image.json") or p.endswith(f"/eval_{t}.json") for t in tasks)]
os.makedirs('traj/res',exist_ok=True)
def get(p):
    out='traj/res/'+p.split('/')[2].replace(':','_')+'__'+p.split('/')[-1]
    if not os.path.exists(out): urllib.request.urlretrieve('https://raw.githubusercontent.com/TheAgentCompany/experiments/main/'+urllib.parse.quote(p),out)
with cf.ThreadPoolExecutor(8) as ex: list(ex.map(get,sel))
print(len(sel),len(os.listdir('traj/res')))
