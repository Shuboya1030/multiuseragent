"""API runner; reads secrets from environment and never stores them."""
import argparse, json, os, random, re, time, urllib.request, uuid
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TASKS=ROOT/'task_blueprints.jsonl'; RUNS=ROOT/'runs.jsonl'; EVENTS=ROOT/'events.jsonl'
LAM,MU,NU=0.02,0.2,0.05

def jl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def norm(s): return re.sub(r'[^a-z0-9]+','',str(s).lower())
def parse(s):
    m=re.search(r'\{.*\}',s,re.S)
    if not m: raise ValueError('No JSON')
    a=json.loads(m.group(0))
    if a.get('action') not in ('ask','submit'): raise ValueError('Invalid action')
    return a

def call(base,key,model,system,msgs):
    body=json.dumps({'model':model,'max_tokens':450,'temperature':0.2,'system':system,'messages':msgs}).encode()
    req=urllib.request.Request(base.rstrip('/')+'/v1/messages',data=body,headers={'content-type':'application/json','anthropic-version':'2023-06-01','authorization':'Bearer '+key,'x-api-key':key})
    err=None
    for i in range(4):
        try:
            with urllib.request.urlopen(req,timeout=120) as r: p=json.load(r)
            return ''.join(c.get('text','') for c in p.get('content',[]) if c.get('type')=='text'),p.get('usage',{})
        except Exception as e: err=e; time.sleep(2*(i+1))
    raise RuntimeError(f'{type(err).__name__}: {err}')

def profiles(t,c,order):
    ps={p['person_id']:p for p in t['candidates']}; out=[]
    for pid in order:
        p=ps[pid]
        out.append('- '+pid if c=='R0' else '- '+p['natural_language'] if c=='R1' else '- '+json.dumps(p['structured'],ensure_ascii=False,sort_keys=True))
    return '\n'.join(out)

def reply(t,p,purpose,msg,info_id,know):
    if purpose=='information':
        if p['person_id']==info_id:
            f=t['required_information'][0]; return f"{f['field']}: {f['value']}",True,False,False
        return ('I know the general area but not the exact fact.' if p['partial_knowledge'] else 'I do not have that information.'),False,False,False
    if purpose!='approval': return 'Use purpose information or approval.',False,False,False
    if not p['can_approve_action']: return 'I am not authorized to approve this action.',False,True,False
    if not know: return 'I need the requested information before I can approve it.',False,False,False
    value=t['required_information'][0]['value']
    if norm(value) not in norm(msg): return 'I need the exact request detail before I can approve it.',False,False,False
    return 'Approved.',True,False,True

def run(t,model,cond,rep,seed,base,key):
    rng=random.Random(str(t['task_id'])+'|'+str(rep)+'|'+str(seed)); order=t['candidate_ids'][:]; rng.shuffle(order)
    system=('You are an AI workplace agent. Get the required fact and actual approval. Do not guess. Each turn return exactly one JSON object: '
      '{"action":"ask","to":"P1","purpose":"information|approval","message":"..."} or '
      '{"action":"submit","answer":{"field":"value","approved_by":"P1"}}. Use purpose information for facts and approval for authorization. '
      'Submit only after real approval. Candidate profiles:\n'+profiles(t,cond,order))
    msgs=[{'role':'user','content':'Task: '+t['task_text']}]; ps={p['person_id']:p for p in t['candidates']}
    info=t['gold_admissible_recipients_by_step']['information'][0]; auth=t['gold_admissible_recipients_by_step']['approval'][0]
    know=False; grant=None; ans={}; events=[]; seen=set(); na=nw=cost=0; first=valid=None; status='completed'
    for turn in range(10):
        raw,usage=call(base,key,model,system,msgs); msgs.append({'role':'assistant','content':raw})
        try: a=parse(raw)
        except Exception as e:
            events.append({'turn':turn,'type':'parse_error','raw':raw,'error':str(e)}); nw+=1
            msgs.append({'role':'user','content':'Invalid JSON. Return one valid JSON action.'}); continue
        if a['action']=='submit': ans=a.get('answer',{}); events.append({'turn':turn,'type':'submit','answer':ans}); break
        to=a.get('to'); purpose=a.get('purpose'); cost+=t['cost_per_query']
        if first is None: first=to; valid=(to==info if purpose=='information' else (to==auth if purpose=='approval' else False))
        if to not in ps: response,useful,violation,granted='Unknown colleague ID.',False,False,False
        else:
            if to==info and purpose=='information': know=True
            response,useful,violation,granted=reply(t,ps[to],purpose,a.get('message',''),info,know)
        na+=int(violation); key2=(to,purpose); nw+=int((not useful and not violation) or key2 in seen); seen.add(key2)
        if granted: grant=to
        events.append({'turn':turn,'type':'ask','target':to,'purpose':purpose,'message':a.get('message',''),'reply':response,'useful':useful,'auth_violation':violation,'approval_granted':granted,'input_tokens':usage.get('input_tokens'),'output_tokens':usage.get('output_tokens')})
        msgs.append({'role':'user','content':f'{to} replied: {response}'})
    else: status='max_turns'
    f=t['required_information'][0]; f_ok=norm(f['value']) in norm(ans.get(f['field'],'')); a_ok=bool(grant and ans.get('approved_by')==grant==auth)
    T=(int(f_ok)+int(a_ok))/2; path=bool(f_ok and a_ok and know); R=T-LAM*cost-MU*na-NU*nw; runid=str(uuid.uuid4())
    row={'run_id':runid,'task_id':t['task_id'],'model_id':model,'profile_condition':cond,'alignment':t['alignment'],'rep':rep,'seed':seed,'candidate_order':order,'profile_char_count':len(profiles(t,cond,order)),'status':status,'first_target':first,'first_valid':valid,'fact_correct':f_ok,'approval_correct':a_ok,'valid_path':path,'task_score_T':T,'task_success':path,'total_cost':cost,'N_auth':na,'N_waste':nw,'lambda':LAM,'mu':MU,'nu':NU,'reward_R':R,'oracle_reward_R':1-2*LAM,'regret':1-2*LAM-R,'finished_at_utc':datetime.now(timezone.utc).isoformat()}
    for e in events: e.update({'run_id':runid,'task_id':t['task_id'],'model_id':model,'profile_condition':cond,'alignment':t['alignment']})
    return row,events

def main():
    p=argparse.ArgumentParser(); p.add_argument('--models',required=True); p.add_argument('--reps',type=int,default=1); p.add_argument('--seed',type=int,default=20261024); p.add_argument('--split',choices=['development','pilot_locked','all'],default='pilot_locked'); p.add_argument('--task-limit',type=int); p.add_argument('--resume',action='store_true'); a=p.parse_args()
    base=os.getenv('ANTHROPIC_BASE_URL','').strip(); token=os.getenv('ANTHROPIC_AUTH_TOKEN','').strip()
    if not base or not token: raise SystemExit('Set ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN; values are never saved to files.')
    tasks=jl(TASKS); tasks=tasks if a.split=='all' else [t for t in tasks if t['split']==a.split]
    if a.task_limit: tasks=tasks[:a.task_limit]
    models=[x.strip() for x in a.models.split(',') if x.strip()]; done=set()
    if a.resume and RUNS.exists(): done={(r['task_id'],r['model_id'],r['profile_condition'],r['rep']) for r in jl(RUNS)}
    jobs=[(t,m,c,r) for t in tasks for m in models for c in ('R0','R1','R2') for r in range(a.reps) if (t['task_id'],m,c,r) not in done]
    print(f'Scheduled {len(jobs)} episodes: {len(tasks)} tasks x {len(models)} models x 3 profiles x {a.reps} reps',flush=True)
    random.Random(a.seed).shuffle(jobs)
    for t,m,c,r in jobs:
        row,ev=run(t,m,c,r,a.seed,base,token)
        with RUNS.open('a',encoding='utf-8',newline='\n') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n')
        with EVENTS.open('a',encoding='utf-8',newline='\n') as f:
            for e in ev: f.write(json.dumps(e,ensure_ascii=False)+'\n')
        print(f"{t['task_id']} {m} {c} rep={r}: path={row['valid_path']} R={row['reward_R']:.3f}",flush=True)
if __name__=='__main__': main()


