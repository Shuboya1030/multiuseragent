"""Execute the approved six-episode design once, with a frozen source snapshot."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'pilot_runs/r1_supplement_20261025_evalv3'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def main():
    # No output dir or API request until credentials and offline checks succeed.
    assert all(os.environ.get(k) for k in ('OPENAI_API_KEY','MOONSHOT_API_KEY','ANTHROPIC_API_KEY')), 'Missing configured credentials'
    checks=[]
    for args in (['-m','unittest','test_evaluator_v3.py','test_pilot_audit.py'],['validate_taskset.py']):
        p=subprocess.run([sys.executable]+args,cwd=ROOT,capture_output=True,text=True)
        checks.append(dict(command=[sys.executable]+args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
        if p.returncode: raise RuntimeError('Offline preflight failed')
    OUT.mkdir(exist_ok=False)
    write(OUT/'preflight_checks.json',checks)
    tasks={'optional-vendor-risk-memo','nohelp-webinar-agenda'}
    rescored=json.loads((ROOT/'pilot_runs/posthoc_eval_v3_20261025/summary.json').read_text())
    for row in rescored['rows']:
        ep=ROOT/'pilot_runs'/row['batch']/'episodes'/row['episode']
        record=ep/'run_record.json'
        if not record.exists(): record=ep/'run_record_recovered.json'
        if record.exists(): tasks.add(json.loads(record.read_text())['task_id'])
    sources=list(ROOT.glob('*.py'))+list(ROOT.glob('*schema.json'))+[ROOT.parent/'study2_1_run_metadata_schema.json',ROOT.parent/'Study2_1_R1_Supplement_Decision_20261025.md']
    sources += [p for task in sorted(tasks) for p in (ROOT/'tasks'/task).iterdir() if p.is_file()]
    manifest={}
    for p in sources:
        rel=p.relative_to(ROOT.parent); dest=OUT/'source_snapshot'/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,dest); manifest[str(rel)]=sha(p)
    write(OUT/'source_manifest.json',manifest)
    commands=[]
    for label,offset,seed in [('optional',3,20261026),('nohelp',6,20261027)]:
        cmd=[sys.executable,str(ROOT/'multimodel_r1_pilot.py'),'--output',str(OUT/label),'--start-index',str(offset),'--limit-per-provider','1','--seed',str(seed),'--run-tag','supplement20261025v3-'+label]
        commands.append(dict(label=label,argv=cmd,instance_seed=seed+1))
    write(OUT/'execution_manifest.json',dict(started_at=datetime.now(timezone.utc).isoformat(),python=sys.executable,base_commit=subprocess.check_output(['/opt/homebrew/bin/git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_dirty=True,planned_episodes=6,commands=commands,automatic_retries=False))
    for entry in commands:
        # Verify the actual runtime source still matches the pre-collection freeze.
        assert all(sha(ROOT.parent/rel)==h for rel,h in manifest.items()), 'Source changed during collection'
        print('Starting '+entry['label'],flush=True)
        with (OUT/(entry['label']+'_console.log')).open('w') as log:
            p=subprocess.run(entry['argv'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        entry['exit_code']=p.returncode
        print('Finished '+entry['label']+' exit='+str(p.returncode),flush=True)
    assert all(sha(ROOT.parent/rel)==h for rel,h in manifest.items()), 'Source changed during collection'
    write(OUT/'execution_completion.json',dict(ended_at=datetime.now(timezone.utc).isoformat(),commands=commands,source_freeze_verified=True))
if __name__=='__main__': main()
