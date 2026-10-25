"""Offline v3 rescoring: immutable inputs, independent output and provenance."""
import argparse
import hashlib
import json
from pathlib import Path
from evaluate_episode import EVALUATOR_VERSION, evaluate_task
ROOT=Path(__file__).resolve().parent
BATCHES=['multimodel_r1_pilot_20261024_v4_single_action','moonshot_r1_pilot_20261024_v5_paced','multimodel_r1_smoke_20261025_v6_evalv2']
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def main(output):
    output.mkdir(parents=True,exist_ok=False)
    inventory={str(p.relative_to(ROOT)):digest(p) for b in BATCHES for p in (ROOT/'pilot_runs'/b).rglob('*') if p.is_file()}
    results=[]
    for b in BATCHES:
        for ep in sorted((ROOT/'pilot_runs'/b/'episodes').iterdir()):
            if not ep.is_dir(): continue
            row={'batch':b,'episode':ep.name}
            try:
                rec=ep/'run_record.json'
                if not rec.exists(): rec=ep/'run_record_recovered.json'
                record=read(rec); task=ROOT/'tasks'/record['task_id']
                sources=[rec,ep/'answer.json',ep/'trace_events.jsonl',ep/'identity_mapping.json',task/'gold_policy.json',task/'metadata.json']
                missing=[str(p.relative_to(ROOT)) for p in sources if not p.exists()]
                if missing: raise FileNotFoundError(', '.join(missing))
                score=evaluate_task(task,ep/'answer.json',ep/'trace_events.jsonl',record['run_id'],record.get('variant_id') or record.get('alignment'),ep/'identity_mapping.json')
                oldpath=ep/'evaluation.json'; old=read(oldpath) if oldpath.exists() else {}
                v2path=ep/'evaluation_posthoc_eval_v2.json'; comparison=read(v2path) if v2path.exists() else old
                sources += [p for p in (oldpath,v2path) if p.exists()]
                provenance={'evaluator_version':EVALUATOR_VERSION,'evaluator_sha256':digest(ROOT/'evaluate_episode.py'),'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sources}}
                dest=Path(b)/ep.name/'evaluation_posthoc_eval_v3.json'
                write(output/dest,{'evaluation':score,'provenance':provenance})
                fields=['underhelp','task_success','checkpoint_score','required_fact_in_reply','approval_in_reply']
                row.update(status='rescored',run_id=record['run_id'],provider=record['model_provider'],help_need_class=score['help_need_class'],output=str(dest),comparison_source=str((v2path if v2path.exists() else oldpath).relative_to(ROOT)),changes={k:{'previous':comparison.get(k),'v3':score.get(k)} for k in fields if comparison.get(k)!=score.get(k)},missing_required_information=score.get('missing_required_information'),missing_required_approval=score.get('missing_required_approval'))
            except (FileNotFoundError,ValueError,KeyError,TypeError) as exc:
                row.update(status='unscorable',reason=str(exc))
            results.append(row)
    after={str(p.relative_to(ROOT)):digest(p) for b in BATCHES for p in (ROOT/'pilot_runs'/b).rglob('*') if p.is_file()}
    assert inventory==after,'Historical artifacts changed'
    write(output/'source_artifact_inventory.json',inventory)
    report={'evaluator_version':EVALUATOR_VERSION,'raw_artifacts_unchanged':True,'episodes':len(results),'rescored':sum(r['status']=='rescored' for r in results),'unscorable':sum(r['status']=='unscorable' for r in results),'rows':results}
    write(output/'summary.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,required=True); main(parser.parse_args().output)
