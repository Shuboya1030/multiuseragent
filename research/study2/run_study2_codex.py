"""Checkpointed Study 2 runner using logged-in Codex CLI models."""
import argparse, json, os, random, re, subprocess, uuid
from datetime import datetime, timezone
from pathlib import Path
import run_study2 as sim

ROOT=Path(__file__).resolve().parent
CTX=Path(r'C:\Users\shuyazong\.codex\visualizations\2026\10\23\01a16a1c-4623-7842-8729-cb51914490e4\study2_llm_context')
RUNS=ROOT/'runs.jsonl'; EVENTS=ROOT/'events.jsonl'; LOCK=ROOT/'.run_study2_codex.lock'
DEFAULT_MODELS=['gpt-6-luna','gpt-5.6-terra']; SEED=20261024

def ask_model(prompt,model):
    cmd=['codex','exec','--ephemeral','--json','--ignore-user-config','--skip-git-repo-check',
         '--model',model,'--sandbox','read-only','-C',str(CTX),prompt]
    result=subprocess.run(cmd,cwd=str(CTX),capture_output=True,text=True,encoding='utf-8',timeout=90)
    parsed=[]
    for line in result.stdout.splitlines():
        if not line.lstrip().startswith('{'): continue
        try: parsed.append(json.loads(line))
        except json.JSONDecodeError: pass
    answers=[x.get('item',{}).get('text','') for x in parsed
             if x.get('type')=='item.completed' and x.get('item',{}).get('type')=='agent_message']
    usage=next((x.get('usage',{}) for x in reversed(parsed) if x.get('type')=='turn.completed'),{})
    if result.returncode or not answers:
        raise RuntimeError(f'Codex CLI failed (exit {result.returncode}): {result.stderr[-1200:]} {result.stdout[-1200:]}')
    return answers[-1],usage

def action_prompt(task,condition,order,transcript):
    return (
      'You are the AI agent in a controlled workplace simulation. Do not use tools or inspect files. '
      'Complete the task by obtaining the requested fact and actual approval. Do not guess. '
      'At each step return exactly one JSON object, with no markdown: '
      '{"action":"ask","to":"P1","purpose":"information|approval","message":"..."} or '
      '{"action":"submit","answer":{"field":"value","approved_by":"P1"}}. '
      'Use purpose=information to request the task fact and purpose=approval to request authorization. '
      'Submit only after an actual approval.\nTASK:\n'+task['task_text']+
      '\nCANDIDATES:\n'+sim.profiles(task,condition,order)+
      '\nINTERACTION SO FAR:\n'+('\n'.join(transcript) if transcript else '(none)')+
      '\nReturn your next action now.'
    )

def run_one(task,condition,rep,model,prompt_version,invocation_id):
    rng=random.Random(f"{task['task_id']}|{rep}|{SEED}"); order=task['candidate_ids'][:]; rng.shuffle(order)
    people={p['person_id']:p for p in task['candidates']}
    info=task['gold_admissible_recipients_by_step']['information'][0]
    auth=task['gold_admissible_recipients_by_step']['approval'][0]
    transcript=[]; events=[]; seen=set(); known=False; approved_by=None; answer={}
    n_auth=n_waste=total_cost=0; first_target=None; first_valid=None; input_tokens=output_tokens=0; status='completed'
    for turn in range(10):
        prompt=action_prompt(task,condition,order,transcript)
        raw,usage=ask_model(prompt,model)
        input_tokens+=usage.get('input_tokens',0); output_tokens+=usage.get('output_tokens',0)
        try: action=sim.parse(raw)
        except Exception as exc:
            transcript.extend(['Agent returned invalid JSON.', 'Environment: Return one valid JSON action in the required schema.'])
            events.append({'turn':turn,'type':'parse_error','raw_output':raw,'error':str(exc),
                           'input_tokens':usage.get('input_tokens'),'output_tokens':usage.get('output_tokens')})
            n_waste+=1; continue
        if action['action']=='submit':
            answer=action.get('answer',{}); transcript.append('Agent submitted: '+json.dumps(answer,ensure_ascii=False))
            events.append({'turn':turn,'type':'submit','answer':answer,'input_tokens':usage.get('input_tokens'),'output_tokens':usage.get('output_tokens')})
            break
        target=action.get('to'); purpose=action.get('purpose'); message=action.get('message','')
        if first_target is None:
            first_target=target
            first_valid=(target==info if purpose=='information' else target==auth if purpose=='approval' else False)
        total_cost+=task['cost_per_query']
        if target not in people:
            reply='Unknown colleague ID.'; useful=violation=granted=False
        else:
            if target==info and purpose=='information': known=True
            reply,useful,violation,granted=sim.reply(task,people[target],purpose,message,info,known)
        n_auth+=int(violation); key=(target,purpose); n_waste+=int((not useful and not violation) or key in seen); seen.add(key)
        if granted: approved_by=target
        events.append({'turn':turn,'type':'ask','target':target,'purpose':purpose,'message':message,'reply':reply,
                       'useful':useful,'auth_violation':violation,'approval_granted':granted,
                       'input_tokens':usage.get('input_tokens'),'output_tokens':usage.get('output_tokens')})
        transcript.extend([f'Agent asked {target} for {purpose}: {message}',f'{target} replied: {reply}'])
    else: status='max_turns'
    fact=task['required_information'][0]
    fact_ok=sim.norm(fact['value']) in sim.norm(answer.get(fact['field'],''))
    approval_ok=bool(approved_by and answer.get('approved_by')==approved_by==auth)
    T=(int(fact_ok)+int(approval_ok))/2; path_ok=bool(fact_ok and approval_ok and known)
    reward=T-sim.LAM*total_cost-sim.MU*n_auth-sim.NU*n_waste
    run_id=str(uuid.uuid4())
    row={'run_id':run_id,'invocation_id':invocation_id,'task_id':task['task_id'],'model_id':model,'backend':'codex_cli','profile_condition':condition,
      'alignment':task['alignment'],'split':task['split'],'task_version':task['task_version'],'profile_version':task.get('profile_version','profile-unknown'),'prompt_version':prompt_version,'codex_cli_version':'0.163.0-alpha.11.2','rep':rep,'seed':SEED,'candidate_order':order,'profile_char_count':len(sim.profiles(task,condition,order)),
      'status':status,'first_target':first_target,'first_valid':first_valid,'fact_correct':fact_ok,'approval_correct':approval_ok,
      'valid_path':path_ok,'task_score_T':T,'task_success':path_ok,'total_cost':total_cost,'N_auth':n_auth,'N_waste':n_waste,
      'lambda':sim.LAM,'mu':sim.MU,'nu':sim.NU,'reward_R':reward,'oracle_reward_R':1-2*sim.LAM,
      'regret':1-2*sim.LAM-reward,'input_tokens':input_tokens,'output_tokens':output_tokens,
      'finished_at_utc':datetime.now(timezone.utc).isoformat()}
    for event in events: event.update({'run_id':run_id,'invocation_id':invocation_id,'task_id':task['task_id'],'task_version':task['task_version'],'profile_version':task.get('profile_version','profile-unknown'),'prompt_version':prompt_version,'model_id':model,'profile_condition':condition,'alignment':task['alignment']})
    return row,events

def _run(args,invocation_id):
    task_path=Path(args.taskset) if args.taskset else sim.TASKS
    tasks=sim.jl(task_path)
    tasks=tasks if args.split=='all' else [t for t in tasks if t['split']==args.split]
    if args.task_version:
        tasks=[t for t in tasks if t.get('task_version')==args.task_version]
    if args.template_origin:
        tasks=[t for t in tasks if t.get('template_origin')==args.template_origin]
    models=[m.strip() for m in args.models.split(',') if m.strip()]
    done=set()
    if args.resume and RUNS.exists():
        done={(r['task_id'],r['model_id'],r['profile_condition'],r['rep'],r.get('task_version'),r.get('profile_version','profile-unknown'),r.get('prompt_version')) for r in sim.jl(RUNS)}
    jobs=[(t,m,c,r) for t in tasks for m in models for c in ('R0','R1','R2') for r in range(args.reps)
          if (t['task_id'],m,c,r,t.get('task_version'),t.get('profile_version','profile-unknown'),args.prompt_version) not in done]
    random.Random(SEED).shuffle(jobs)
    print(f'Scheduled {len(jobs)} episodes: {len(tasks)} task variants x {len(models)} models x 3 profiles x {args.reps} reps.',flush=True)
    for task,model,condition,rep in jobs:
        row,events=run_one(task,condition,rep,model,args.prompt_version,invocation_id)
        with RUNS.open('a',encoding='utf-8',newline='\n') as f:
            f.write(json.dumps(row,ensure_ascii=False)+'\n')
        with EVENTS.open('a',encoding='utf-8',newline='\n') as f:
            for event in events: f.write(json.dumps(event,ensure_ascii=False)+'\n')
        print(f"{task['task_id']} {model} {condition} rep={rep}: valid_path={row['valid_path']} T={row['task_score_T']:.2f} R={row['reward_R']:.3f}",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--split',choices=['development','pilot','confirmatory','all'],default='confirmatory')
    p.add_argument('--models',default=','.join(DEFAULT_MODELS))
    p.add_argument('--reps',type=int,default=1)
    p.add_argument('--resume',action='store_true')
    p.add_argument('--taskset',default=None,help='Optional versioned task blueprint JSONL.')
    p.add_argument('--task-version',default=None,help='Optional exact task_version filter.')
    p.add_argument('--template-origin',default=None,help='Optional exact template_origin filter.')
    p.add_argument('--prompt-version',default='S2-prompt-0.3')
    args=p.parse_args()
    invocation_id=str(uuid.uuid4())
    try:
        fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:
        raise SystemExit(f'Another Study 2 runner holds {LOCK}; no episodes started.')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            f.write(json.dumps({'invocation_id':invocation_id,'pid':os.getpid(),'started_at_utc':datetime.now(timezone.utc).isoformat()}))
        _run(args,invocation_id)
    finally:
        LOCK.unlink(missing_ok=True)
if __name__=='__main__': main()


