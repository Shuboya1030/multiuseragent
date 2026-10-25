"""Frozen 180-episode R1 orchestration, separate from pilot collection."""
import argparse
import hashlib
import itertools
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import jsonschema
import multimodel_r1_pilot as engine
from instantiate_run import instantiate
from evaluate_episode import evaluate_task
ROOT=Path(__file__).resolve().parent
PROTOCOL='study21-formal-r1-v1-evalv3'
EXPECTED={'openai':'gpt-5.4-mini-2026-03-17','moonshot':'kimi-k2.6','anthropic':'claude-haiku-5-5'}
PRICES={'openai':{'input':.75,'cached':.075,'output':4.5,'source':'https://developers.openai.com/api/docs/models/gpt-5.4-mini'},'moonshot':{'input':.95,'cached':.16,'output':4.,'source':'https://platform.kimi.ai/docs/pricing/chat'},'anthropic':{'input':.10,'cached':.01,'output':.50,'cache_write':.20,'source':'https://platform.claude.com/docs/en/models/haiku-5-5/overview'}}
INPUT_BOUND=32768

def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(p.read_text())
def write(p,d): engine.write_json(p,d)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def loadrows(p): return engine.load_lines(p) if p.exists() else []

def schedule():
    rng=random.Random(2026102501); byclass={k:[] for k in ('must_ask','optional_benefit','no_help')}
    metas=[read(p) for p in sorted((ROOT/'tasks').glob('*/metadata.json'))]
    seeds={m['task_id']:202610250100+i for i,m in enumerate(metas)}
    for m in metas: byclass[m['help_need_class']].append(m['task_id'])
    assert {k:len(v) for k,v in byclass.items()}=={k:20 for k in byclass}
    for v in byclass.values(): rng.shuffle(v)
    permutations=list(itertools.permutations(EXPECTED))*10; rng.shuffle(permutations)
    result=[];block=0
    for i in range(20):
        classes=list(byclass);rng.shuffle(classes)
        for klass in classes:
            task=byclass[klass][i]
            for position,provider in enumerate(permutations[block]):
                result.append({'ordinal':len(result)+1,'block':block+1,'round':i+1,'provider_position':position+1,'provider':provider,'task_id':task,'help_need_class':klass,'alignment':'separated' if klass=='must_ask' else 'not_applicable','instance_seed':seeds[task],'replicate':1,'profile_condition':'R1','run_id':f'formal-r1-{provider}-{task}-{seeds[task]}-rep1-20261025v1'})
            block+=1
    return result

def prepare(out,budget):
    assert budget==10., 'This approved block has a USD 10 budget'
    out.mkdir(parents=True,exist_ok=False)
    checks=[]
    for cmd in ([sys.executable,'-m','unittest','test_evaluator_v3.py','test_pilot_audit.py','test_formal_r1.py'],[sys.executable,'validate_taskset.py']):
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);checks.append({'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        if p.returncode: write(out/'preflight_checks.json',checks);raise RuntimeError('Offline preflight failed')
    write(out/'preflight_checks.json',checks)
    sources=list(ROOT.glob('*.py'))+list(ROOT.glob('*schema.json'))+[ROOT/'catalog.jsonl',ROOT.parent/'study2_1_run_metadata_schema.json',ROOT.parent/'Study2_1_R1_Formal_Protocol_20261025.md']
    sources += [p for p in (ROOT/'tasks').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    hashes={}
    for p in sources:
        rel=p.relative_to(ROOT.parent);dest=out/'source_snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);hashes[str(rel)]=sha(p)
    jobs=schedule();fingerprints={}
    with tempfile.TemporaryDirectory() as temp:
        for job in jobs[::3]:
            dest=Path(temp)/job['task_id'];instantiate(ROOT/'tasks'/job['task_id'],dest,'freeze',job['instance_seed'],'R1',job['alignment'])
            profiles=read(dest/'candidate_profiles.json');system,messages=engine.initial_prompt((dest/'task.md').read_text(),profiles)
            fingerprints[job['task_id']]={'task':sha(dest/'task.md'),'profiles':sha(dest/'candidate_profiles.json'),'mapping':read(dest/'identity_mapping.json')['alias_to_canonical'],'candidate_order':[p['candidate_id'] for p in profiles]}
    write(out/'schedule.json',jobs);write(out/'instance_fingerprints.json',fingerprints);write(out/'source_manifest.json',hashes)
    write(out/'pricing_snapshot.json',{'checked_at':now(),'currency':'USD','unit':'per_million_tokens','rates':PRICES,'actual_billing':'unavailable','taxes':'excluded; USD 1 reserve below user budget','cache_policy':'automatic reads billed by reported usage; no cache_control writes requested'})
    write(out/'confirmatory_manifest.json',{'protocol_version':PROTOCOL,'frozen_at':now(),'base_commit':subprocess.check_output(['/opt/homebrew/bin/git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'run_type':'confirmatory','collection_stage':'R1','episodes':180,'replicate':1,'models':engine.MODELS,'expected_returned_models':EXPECTED,'max_turns':8,'max_output_tokens':1600,'request_attempts':1,'moonshot_min_interval_seconds':21,'user_budget_usd':budget,'operating_ceiling_usd':budget-1,'max_input_token_reservation':INPUT_BOUND,'randomization_seed':2026102501,'extension_rule':'fixed n; no automatic repeats or R0','precision_reporting_target_half_width':.10,'accepted_limitations':['user explicitly retains known No-help output ambiguity','independent content review not completed','optional lexical quality proxy not independently validated','provider reasoning defaults differ'],'frozen_files':{p.name:sha(p) for p in (out/'schedule.json',out/'instance_fingerprints.json',out/'source_manifest.json',out/'pricing_snapshot.json')}})
    write(out/'manifest_lock.json',{'confirmatory_manifest_sha256':sha(out/'confirmatory_manifest.json')})
    print(json.dumps({'prepared':str(out),'episodes':180,'manifest_sha256':sha(out/'confirmatory_manifest.json')}))

def cost(provider,usage):
    rates=PRICES[provider];inp=usage.get('prompt_tokens',0);output=usage.get('completion_tokens',0)
    cached=usage.get('cache_read_input_tokens',usage.get('prompt_tokens_details',{}).get('cached_tokens',0)) or 0
    creation=usage.get('cache_creation_input_tokens',0) or 0
    if provider=='anthropic': value=inp*rates['input']+cached*rates['cached']+creation*rates['cache_write']+output*rates['output']
    else: value=(inp-cached)*rates['input']+cached*rates['cached']+output*rates['output']
    return value/1_000_000

def call_reservation(provider): return (INPUT_BOUND*PRICES[provider]['input']+1600*PRICES[provider]['output'])/1_000_000

class Guard:
    def __init__(self,out,ceiling,call):
        self.out=out;self.ceiling=ceiling;self.call=call;self.stop_reason=None
        self.ledger=loadrows(out/'cost_ledger.jsonl')
    @property
    def charged(self): return sum(r['safety_charge_usd'] for r in self.ledger)
    def __call__(self,messages,key):
        if self.stop_reason:
            raise RuntimeError(self.stop_reason)
        provider=engine.CURRENT_MODEL;reserve=call_reservation(provider)
        bound=len(json.dumps({'messages':messages,'tools':engine.TOOLS},ensure_ascii=False).encode())+4096
        if bound>INPUT_BOUND or self.charged+reserve>self.ceiling:
            self.stop_reason='input_or_budget_guard';raise RuntimeError(self.stop_reason)
        row={'run_id':engine.CURRENT_RUN_ID,'turn':engine.CURRENT_TURN,'provider':provider,'started_at':now(),'reservation_usd':reserve}
        try:
            result=self.call(messages,key);usage=result[1];estimated=cost(provider,usage)
            row.update(usage=usage,estimated_cost_usd=estimated,safety_charge_usd=estimated,status='usage_available')
            total_input=usage.get('prompt_tokens',0)+usage.get('cache_read_input_tokens',0)+usage.get('cache_creation_input_tokens',0)
            if total_input>INPUT_BOUND or usage.get('completion_tokens',0)>1600:self.stop_reason='usage_exceeded_reservation'
            if result[2]!=EXPECTED[provider]:self.stop_reason='model_id_drift'
            return result
        except Exception:
            row.update(estimated_cost_usd=None,safety_charge_usd=reserve,status='unknown_usage_reserved')
            raise
        finally:
            self.ledger.append(row);engine.append_jsonl(self.out/'cost_ledger.jsonl',row)

def verify_freeze(out):
    assert sha(out/'confirmatory_manifest.json')==read(out/'manifest_lock.json')['confirmatory_manifest_sha256']
    for name,digest in read(out/'confirmatory_manifest.json')['frozen_files'].items(): assert sha(out/name)==digest,name
    for rel,digest in read(out/'source_manifest.json').items():
        assert sha(out/'source_snapshot'/rel)==digest,rel
        assert sha(ROOT.parent/rel)==digest,'Working source changed: '+rel

def audit_episode(out,job,record):
    ep=out/'episodes'/record['run_id'];rid=record['run_id'];events=loadrows(ep/'trace_events.jsonl');api=loadrows(ep/'api_io.jsonl')
    jsonschema.validate(record,read(ROOT.parent/'study2_1_run_metadata_schema.json'))
    assert all(e['run_id']==rid for e in events+api)
    assert [e['event_id'] for e in events]==list(range(len(events)))
    f=read(out/'instance_fingerprints.json')[job['task_id']]
    assert sha(ep/'task.md')==f['task'] and sha(ep/'candidate_profiles.json')==f['profiles']
    assert read(ep/'identity_mapping.json')['alias_to_canonical']==f['mapping']
    replay=evaluate_task(engine.TASKS/job['task_id'],ep/'answer.json',ep/'trace_events.jsonl',rid,job['alignment'],ep/'identity_mapping.json')
    assert replay==read(ep/'evaluation.json')
    assert record['run_type']=='confirmatory' and record['collection_stage']=='R1'
    requests=sum(e['event']=='request' for e in api);responses=sum(e['event']=='response' for e in api);errors=sum(e['event']=='error' for e in api)
    assert requests==responses+errors,'Unresolved API request'
    assert len(loadrows(ep/'model_turns.jsonl'))==responses
    return {'run_id':rid,'checked_at':now(),'passed':True,'api_requests':requests,'api_errors':errors}

def run(out):
    verify_freeze(out);manifest=read(out/'confirmatory_manifest.json');jobs=read(out/'schedule.json')
    engine.HERE=out/'source_snapshot/study2_1_taskset';engine.TASKS=engine.HERE/'tasks'
    engine.SECRETS=[os.environ.get(c['env'],'') for c in engine.MODELS.values()];assert all(engine.SECRETS),'Missing credentials'
    guard=Guard(out,manifest['operating_ceiling_usd'],engine.call_model);engine.call_model=guard
    records=loadrows(out/'runs.jsonl');done={r['run_id'] for r in records}
    started={r['run_id'] for r in loadrows(out/'run_status.jsonl') if r['status']=='started'}
    if started-done: raise RuntimeError('Interrupted started cell requires audit; no implicit retry')
    engine.LAST_API_REQUEST_AT={}
    api_streak=Counter();recent={p:[] for p in EXPECTED}
    # Resumption rebuilds error-stop counters from saved records.
    for rec in records:
        p=next(p for p,c in engine.MODELS.items() if c['provider']==rec['model_provider'])
        api_streak[p]=api_streak[p]+1 if any(e['type']=='api_error' for e in rec['errors']) else 0
        recent[p].append(any(e['type']=='parse_error' for e in rec['errors']))
    for job in jobs:
        if job['run_id'] in done:continue
        verify_freeze(out);p=job['provider'];engine.CURRENT_MODEL=p
        if guard.charged+8*call_reservation(p)>guard.ceiling:guard.stop_reason='episode_budget_reservation';break
        if api_streak[p]>=3 or sum(recent[p][-10:])>=3:guard.stop_reason='systematic_provider_failure';break
        def finalize(rec):
            entries=[x for x in guard.ledger if x['run_id']==rec['run_id']]
            rec['estimated_cost_usd']=sum(x['estimated_cost_usd'] for x in entries) if entries and all(x['estimated_cost_usd'] is not None for x in entries) else None
            rec['cost_status']='estimated' if rec['estimated_cost_usd'] is not None else 'unavailable'
            rec['pricing_snapshot']={'date':'2026-10-25','rates_per_million_tokens':PRICES[p],'reference':'pricing_snapshot.json','taxes_included':False}
            rec['sampling_parameters']['input_token_safety_reservation']=INPUT_BOUND
            rec['artifact_refs']['cost_ledger']='cost_ledger.jsonl'
        print(json.dumps({'ordinal':job['ordinal'],'of':180,'provider':p,'task_id':job['task_id'],'status':'starting'}),flush=True)
        try:
            record=engine.run_episode(job['task_id'],job['alignment'],job['instance_seed'],out,os.environ[engine.MODELS[p]['env']],run_context={'run_id':job['run_id'],'run_type':'confirmatory','collection_stage':'R1','protocol_version':PROTOCOL,'finalize_record':finalize})
            engine.append_jsonl(out/'runs.jsonl',record);records.append(record)
            audit=audit_episode(out,job,record);engine.append_jsonl(out/'quality_checks.jsonl',audit)
        except Exception as exc:
            write(out/'collection_stop.json',{'stopped_at':now(),'reason':'runtime_or_audit_exception','run_id':job['run_id'],'type':type(exc).__name__,'detail':str(exc)[:500]});raise
        api_streak[p]=api_streak[p]+1 if any(e['type']=='api_error' for e in record['errors']) else 0
        recent[p].append(any(e['type']=='parse_error' for e in record['errors']))
        status={'updated_at':now(),'recorded':len(records),'planned':180,'collection_status':'running','completed_submissions':sum(r['status']=='completed' for r in records),'failed_runs':sum(r['status']!='completed' for r in records),'estimated_safety_charge_usd':guard.charged,'operating_ceiling_usd':guard.ceiling,'per_provider':dict(Counter(r['model_provider'] for r in records))}
        write(out/'progress.json',status);print(json.dumps(status),flush=True)
        if guard.stop_reason:break
    complete=len(records)==180
    write(out/'collection_status.json',{'finished_at':now(),'status':'complete' if complete else 'stopped','episodes_recorded':len(records),'stop_reason':guard.stop_reason,'estimated_safety_charge_usd':guard.charged})
    # Lock raw data before any behavior comparison. Analysis adds new files only.
    files={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name not in {'console.log','data_snapshot_manifest.json'} and '__pycache__' not in p.parts}
    write(out/'data_snapshot_manifest.json',{'locked_at':now(),'complete':complete,'algorithm':'sha256','files':files})
    return complete

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run']);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--budget-usd',type=float,default=10.)
    args=parser.parse_args();out=args.output.resolve()
    if args.mode=='prepare':prepare(out,args.budget_usd)
    else:sys.exit(0 if run(out) else 2)
