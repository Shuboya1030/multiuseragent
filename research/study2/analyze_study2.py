"""Descriptive and paired cluster-bootstrap analysis for Study 2 JSONL runs."""
import csv, json, random
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RUNS=ROOT/'runs.jsonl'; DER=ROOT/'derived'
METRICS=['valid_path','task_score_T','reward_R','total_cost','N_auth','N_waste','first_valid']

def load(): return [json.loads(x) for x in RUNS.read_text(encoding='utf-8').splitlines() if x.strip()]
def template_id(task_id): return task_id.removeprefix('S2_').removesuffix('_aligned').removesuffix('_separated')
def avg(xs): return sum(xs)/len(xs) if xs else float('nan')
def exact_sign_p(ds):
    ds=[d for d in ds if d!=0]
    if not ds: return 1.0
    obs=abs(avg(ds)); n=len(ds); ge=0
    for mask in range(1<<n):
        v=avg([d if mask&(1<<i) else -d for i,d in enumerate(ds)])
        ge += abs(v)>=obs-1e-12
    return ge/(1<<n)
def boot_ci(ds,seed=20261024,B=10000):
    if not ds: return (float('nan'),float('nan'))
    rng=random.Random(seed); vals=[]
    for _ in range(B): vals.append(avg([rng.choice(ds) for __ in ds]))
    vals.sort(); return vals[int(.025*B)],vals[min(B-1,int(.975*B))]
def main():
    if not RUNS.exists(): raise SystemExit('No model runs yet; no inferential results generated.')
    rows=load(); DER.mkdir(exist_ok=True)
    groups=defaultdict(list)
    for r in rows: groups[(r['model_id'],r['alignment'],r['profile_condition'])].append(r)
    with (DER/'cell_summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['model','alignment','condition','n_runs']+METRICS); w.writeheader()
        for (m,a,c),rs in sorted(groups.items()): w.writerow({'model':m,'alignment':a,'condition':c,'n_runs':len(rs),**{k:avg([float(x[k]) for x in rs]) for k in METRICS}})
    # Average repeated runs within task, then make matched condition differences.
    cells=defaultdict(list)
    for r in rows: cells[(r['model_id'],r['task_id'],r['profile_condition'])].append(r)
    taskmean={(m,t,c):{k:avg([float(x[k]) for x in xs]) for k in METRICS}
              for (m,t,c),xs in cells.items()}
    models=sorted({r['model_id'] for r in rows}); contrasts=[]
    for m in models:
        for outcome in ['valid_path','reward_R','task_score_T','total_cost','N_auth','N_waste']:
            for label,hi,lo in [('R1-R0','R1','R0'),('R2-R1','R2','R1')]:
                diffs=[]
                for (mm,t,c),v in taskmean.items():
                    if mm==m and c==hi and (m,t,lo) in taskmean:
                        diffs.append((template_id(t),v[outcome]-taskmean[(m,t,lo)][outcome]))
                bytemp=defaultdict(list)
                for tid,d in diffs: bytemp[tid].append(d)
                ds=[avg(v) for v in bytemp.values()]
                ci=boot_ci(ds,seed=20261024+len(contrasts))
                contrasts.append({'model':m,'outcome':outcome,'contrast':label,'n_templates':len(ds),'mean_difference':avg(ds),'cluster_boot_95_low':ci[0],'cluster_boot_95_high':ci[1],'exact_sign_flip_p':exact_sign_p(ds)})
        # Difference-in-differences across matched alignment versions for each template.
        for outcome in ['valid_path','reward_R','task_score_T']:
            for label,hi,lo in [('R1-R0','R1','R0'),('R2-R1','R2','R1')]:
                diff_by_template=defaultdict(dict)
                for (mm,t,c),v in taskmean.items():
                    if mm!=m or c!=hi or (m,t,lo) not in taskmean: continue
                    align='aligned' if t.endswith('_aligned') else 'separated'
                    diff_by_template[template_id(t)][align]=v[outcome]-taskmean[(m,t,lo)][outcome]
                ds=[x['separated']-x['aligned'] for x in diff_by_template.values() if {'aligned','separated'}<=set(x)]
                ci=boot_ci(ds,seed=20261024+len(contrasts))
                contrasts.append({'model':m,'outcome':outcome,'contrast':label+' DID separated-aligned','n_templates':len(ds),'mean_difference':avg(ds),'cluster_boot_95_low':ci[0],'cluster_boot_95_high':ci[1],'exact_sign_flip_p':exact_sign_p(ds)})
    with (DER/'paired_contrasts.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=contrasts[0].keys()); w.writeheader(); w.writerows(contrasts)
    print(f'Wrote descriptive summaries and paired, template-clustered contrasts for {len(rows)} runs to {DER}')
    print('Note: these bootstrap/sign-flip estimates do not replace the preregistered mixed-effects analysis; with the current 6 task templates, treat them as pilot diagnostics.')
if __name__=='__main__': main()
