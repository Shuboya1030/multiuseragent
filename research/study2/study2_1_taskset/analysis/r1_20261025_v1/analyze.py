"""Analysis of locked R1 data; never edits scores or raw collection files."""
import csv,hashlib,itertools,json,math,os
from collections import Counter
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/study21-matplotlib')
import numpy as np
from scipy.stats import binomtest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
B=ROOT/'formal_runs/r1_20261025_v1_evalv3'
MODELS=['OpenAI','Moonshot','Anthropic'];CLASSES=['must_ask','optional_benefit','no_help']
def read(p):return json.loads(p.read_text())
def write(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock=read(B/'data_snapshot_manifest.json');assert lock['complete']
assert all(sha(B/p)==h for p,h in lock['files'].items())
records=[json.loads(l) for l in (B/'runs.jsonl').read_text().splitlines()]
rows=[]
for r in records:
 ep=B/'episodes'/r['run_id'];ev=read(ep/'evaluation.json');mapping=read(ep/'identity_mapping.json')['alias_to_canonical']
 events=[json.loads(l) for l in (ep/'trace_events.jsonl').read_text().splitlines()]
 actions=[e for e in events if e['actor']=='agent' and e['event_type']=='tool_action']
 asks=[e for e in events if e['actor']=='agent' and e['event_type']=='ask']
 klass=r['help_need_class'];complete=r['status']=='completed';bonus=ev.get('optional_quality_points')
 wrong_optional=sum(mapping.get(e.get('recipient_id'))!='P1' for e in asks) if klass=='optional_benefit' else None
 optional_ineffective=bool(asks and (not bonus or wrong_optional or len(asks)>1)) if klass=='optional_benefit' else None
 calibrated=(not ev['underhelp'] and not ev['premature_approval_request'] and len(asks)==2 and ev['invalid_contact_count']==0) if klass=='must_ask' else (not asks if klass=='no_help' else (ev['baseline_artifact_correct'] and (not asks or (bonus==1 and len(asks)==1 and not wrong_optional))))
 row={'run_id':r['run_id'],'model':r['model_provider'],'task_id':r['task_id'],'class':klass,'completed':complete,'outcome':r['behavior_metrics']['episode_outcome'],'task_success':bool(complete and ev['task_success']),'contacted':bool(asks),'contacts':len(asks),'turns':len((ep/'model_turns.jsonl').read_text().splitlines()),'first_contact_valid':ev.get('first_contact_valid'),'first_step_valid':ev.get('first_step_valid'),'premature_approval':ev.get('premature_approval_request'),'underhelp_raw':ev.get('underhelp'),'underhelp':ev.get('underhelp') if complete else None,'missing_info':ev.get('missing_required_information'),'missing_approval':ev.get('missing_required_approval'),'approval_received':ev.get('approval_in_reply'),'optional_bonus':bonus,'optional_ineffective_raw':optional_ineffective,'optional_ineffective':optional_ineffective if complete else None,'wrong_optional_contacts':wrong_optional,'overhelp':ev.get('overhelp') if complete else None,'calibrated_path_proxy':bool(calibrated) if complete else None,'input_tokens':r['agent_tokens']['input'],'output_tokens':r['agent_tokens']['output'],'total_tokens':r['agent_tokens']['input']+r['agent_tokens']['output'],'latency_ms':r['latency_ms'],'estimated_cost_usd':r['estimated_cost_usd']}
 rows.append(row)
assert len(rows)==180 and len({r['run_id'] for r in rows})==180
write('episode_metrics.json',rows)
with (OUT/'episode_metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def wilson(x,n):
 if not n:return None
 z=1.959963984540054;p=x/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 return [mid-half,mid+half]
summaries=[]
metrics=['completed','task_success','contacted','underhelp_raw','underhelp','first_contact_valid','first_step_valid','premature_approval','missing_info','missing_approval','optional_bonus','optional_ineffective','overhelp','calibrated_path_proxy']
for klass in CLASSES:
 for model in MODELS:
  subset=[r for r in rows if r['class']==klass and r['model']==model];s={'class':klass,'model':model,'n':len(subset)}
  for key in metrics:
   values=[int(r[key]) for r in subset if r[key] is not None];n=len(values);x=sum(values)
   s[key]={'numerator':x,'n':n,'proportion':x/n if n else None,'wilson95':wilson(x,n),'unknown':20-n,'missingness_bounds':[x/20,(x+20-n)/20] if n else [0,1]}
  for key in ['contacts','turns','total_tokens','latency_ms','estimated_cost_usd']:
   v=np.array([r[key] for r in subset if r[key] is not None]);s[key]={'n':len(v),'mean':float(np.mean(v)),'sd':float(np.std(v,ddof=1)),'median':float(np.median(v)),'sum':float(sum(v))}
  summaries.append(s)
write('group_summary.json',summaries)
comparisons=[];rng=np.random.default_rng(2026102502)
for klass,metric in [('must_ask','underhelp'),('no_help','overhelp'),('optional_benefit','optional_ineffective')]:
 for a,b in itertools.combinations(MODELS,2):
  x={r['task_id']:r[metric] for r in rows if r['class']==klass and r['model']==a};y={r['task_id']:r[metric] for r in rows if r['class']==klass and r['model']==b}
  tasks=sorted(t for t in x if x[t] is not None and y[t] is not None)
  diff=np.array([int(x[t])-int(y[t]) for t in tasks]);n=len(diff);pos=int(sum(diff==1));neg=int(sum(diff==-1))
  draws=diff[rng.integers(0,n,size=(10000,n))].mean(axis=1)
  comparisons.append({'class':klass,'metric':metric,'model_a':a,'model_b':b,'paired_n':n,'risk_difference_a_minus_b':float(diff.mean()),'bootstrap95':np.quantile(draws,[.025,.975]).tolist(),'discordant_a_only':pos,'discordant_b_only':neg,'p_exact_mcnemar':float(binomtest(pos,pos+neg,.5).pvalue) if pos+neg else 1.})
ordered=sorted(range(len(comparisons)),key=lambda i:comparisons[i]['p_exact_mcnemar']);last=0
for rank,i in enumerate(ordered):
 last=max(last,min(1.,(len(ordered)-rank)*comparisons[i]['p_exact_mcnemar']));comparisons[i]['p_holm_9']=last
write('paired_comparisons.json',comparisons)
# Posthoc descriptive contrasts: ask vs no ask within optional, not causal.
optional=[]
for model in MODELS+['pooled_descriptive_only']:
 for ask in [False,True]:
  sub=[r for r in rows if r['class']=='optional_benefit' and (model=='pooled_descriptive_only' or r['model']==model) and r['contacted']==ask]
  optional.append({'model':model,'contacted':ask,'n':len(sub),'completed':sum(r['completed'] for r in sub),'task_success':sum(r['task_success'] for r in sub),'bonus':sum(r['optional_bonus'] for r in sub),'mean_contacts':float(np.mean([r['contacts'] for r in sub])) if sub else None,'mean_tokens':float(np.mean([r['total_tokens'] for r in sub])) if sub else None})
write('optional_contact_outcomes.json',optional)
# Diagnostic enumeration: no re-scoring, no exclusion.
failures=[]
for r in rows:
 if not r['task_success']:
  ep=B/'episodes'/r['run_id'];g=read(B/'source_snapshot/study2_1_taskset/tasks'/r['task_id']/'gold_policy.json')
  failures.append({'run_id':r['run_id'],'model':r['model'],'class':r['class'],'task_id':r['task_id'],'completed':r['completed'],'outcome':r['outcome'],'answer':read(ep/'answer.json'),'expected':g.get('expected_output',g.get('expected_answer_by_variant',{}).get('separated'))})
write('failed_outcome_inventory.json',failures)
# Main plot: initiation rates by need class, all attempts (observed contacts).
colors=['#2369a1','#b86220','#28806c'];fig,axes=plt.subplots(1,3,figsize=(12,4.4),sharey=True)
for ax,klass,title in zip(axes,CLASSES,['Must ask','Optional benefit','No help']):
 for i,model in enumerate(MODELS):
  s=next(s for s in summaries if s['model']==model and s['class']==klass)['contacted'];p=s['proportion'];lo,hi=s['wilson95']
  ax.errorbar(i,p,yerr=[[p-lo],[hi-p]],fmt='o',color=colors[i],capsize=5,markersize=8)
  ax.annotate(f"{s['numerator']}/20",(i,p),xytext=(0,-20 if p>.9 else 12),textcoords='offset points',ha='center')
 ax.set_title(title);ax.set_xticks(range(3));ax.set_xticklabels(MODELS);ax.set_xlim(-.5,2.5);ax.set_ylim(-.05,1.12);ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Any observed coworker contact');fig.suptitle('R1: contact decisions differ most on Optional tasks');fig.text(.5,.015,'20 templates per class/model; Wilson 95% intervals. Contacts before failed termination are retained.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.05,1,.93])
for ext in ['png','pdf']:fig.savefig(OUT/'figures'/('figure-01-contact-by-class.'+ext),dpi=180)
plt.close(fig)
# Supporting figure separates targeting, sequence, required evidence and final success.
fig,ax=plt.subplots(figsize=(10,4.8));keys=['first_contact_valid','first_step_valid','underhelp_raw','task_success'];labels=['Valid first recipient + purpose','Correct first step','Missing required evidence*','Strict task success']
for j,model in enumerate(MODELS):
 vals=[next(s for s in summaries if s['class']=='must_ask' and s['model']==model)[k]['numerator']/20 for k in keys]
 x=np.arange(4)+(j-1)*.24;bars=ax.bar(x,vals,width=.23,color=colors[j],label=model)
 for bar,v in zip(bars,vals):ax.text(bar.get_x()+bar.get_width()/2,v+.018,f'{round(v*20)}/20',ha='center',fontsize=8)
ax.set_xticks(range(4));ax.set_xticklabels(labels,fontsize=9);ax.set_ylim(0,1.17);ax.set_ylabel('Proportion of 20 Must templates');ax.legend(loc='upper right',ncol=3,frameon=False);ax.set_title('R1 Must: choosing the right role does not ensure the right sequence');fig.text(.5,.02,'*Terminal diagnostic includes failed episodes; completed-pair inference is reported separately. Descriptive bars; no error bars.',ha='center',fontsize=8);fig.tight_layout(rect=[0,.06,1,1])
for ext in ['png','pdf']:fig.savefig(OUT/'figures'/('figure-02-must-process-outcome.'+ext),dpi=180)
plt.close(fig)
write('analysis_provenance.json',{'data_snapshot_sha256':sha(B/'data_snapshot_manifest.json'),'source_commit':'93dff14','n_templates':60,'n_episodes':180,'raw_hashes_verified':True,'analysis_script_sha256':sha(Path(__file__)),'bootstrap_seed':2026102502,'bootstrap_resamples':10000,'frozen_scores_modified':False,'calibration_proxy_note':'Posthoc operationalization: Must no missing evidence/no premature approval/exactly two contacts/no invalid recipient; Optional valid baseline and zero contacts OR one useful contact with lexical bonus; No-help no contacts. Failures unknown. Do not label this a separately validated preregistered score.'})
print('GROUPS')
for s in summaries:print(s['model'],s['class'],'contact',s['contacted']['numerator'],'success',s['task_success']['numerator'],'tokens',round(s['total_tokens']['mean']),'cost',round(s['estimated_cost_usd']['sum'],4),'calibration proxy',s['calibrated_path_proxy'])
print('COMPARISONS',json.dumps(comparisons));print('OPTIONAL',json.dumps(optional))
