import json,os,re,collections
ev=json.load(open('traj/events.json',encoding='utf-8'))
res={}
for f in os.listdir('traj/res'):
    m,t=f.split('__'); t=re.sub(r'^eval_|(-image)?\.json$','',t)
    d=json.load(open('traj/res/'+f)); fs=d['final_score']
    res[(m.replace('20241217_OpenHands-0.14.2-',''),t)]=(fs['result'],fs['total'])
rows=[]
for e in ev:
    r,tot=res[(e['model'],e['task'])]
    T=set(e['targets']); C=set(e['contacted'])
    hit=T&C; wrong=C-T; miss=T-C
    if not T: continue
    if not C and not e['reached_chat']: cat='ui_blocked'
    elif not C: cat='omitted_all'
    elif miss and wrong: cat='partial+wrong'
    elif miss: cat='partial'
    elif wrong: cat='complete+extra'
    else: cat='complete'
    rows.append(dict(**e,score=r/tot if tot else 0,success=(r==tot),cat=cat,n_hit=len(hit),n_wrong=len(wrong),n_miss=len(miss),cov=len(hit)/len(T)))
json.dump(rows,open('traj/rq1_rows.json','w'),indent=1,ensure_ascii=False)
N=len(rows); print('trajectories',N,'tasks',len({r['task'] for r in rows}),'models',len({r['model'] for r in rows}))
print('\nHelp-seeking category distribution:')
cc=collections.Counter(r['cat'] for r in rows)
for k,v in cc.most_common(): 
    sub=[r for r in rows if r['cat']==k]; print(f"  {k:16s} {v:4d} ({v/N:5.1%})  success={sum(r['success'] for r in sub)/len(sub):5.1%}  mean_score={sum(r['score'] for r in sub)/len(sub):.2f}")
print('\nFailures (not fully successful):',sum(not r['success'] for r in rows))
fail=[r for r in rows if not r['success']]
print('  of which incomplete help-seeking (missed >=1 target):',sum(r['n_miss']>0 for r in fail),f"({sum(r['n_miss']>0 for r in fail)/len(fail):.1%})")
print('  of which omitted entirely:',sum(r['cat']=='omitted_all' for r in fail))
print('\nPer model: coverage / success / wrong-person rate / fabricated')
for m in sorted({r['model'] for r in rows}):
    s=[r for r in rows if r['model']==m]
    print(f"  {m:22s} cov={sum(r['cov'] for r in s)/len(s):.2f}  succ={sum(r['success'] for r in s)/len(s):5.1%}  any_wrong={sum(r['n_wrong']>0 for r in s)/len(s):5.1%}  omit={sum(r['cat']=='omitted_all' for r in s)/len(s):5.1%}")
# association
import statistics
cov_full=[r['score'] for r in rows if r['n_miss']==0]; cov_part=[r['score'] for r in rows if r['n_miss']>0]
print(f"\nMean checkpoint score: all targets contacted={statistics.mean(cov_full):.2f} (n={len(cov_full)}) vs missed>=1={statistics.mean(cov_part):.2f} (n={len(cov_part)})")
print("Success rate: all contacted=%.1f%% vs missed=%.1f%%"%(100*sum(r['success'] for r in rows if r['n_miss']==0)/len(cov_full),100*sum(r['success'] for r in rows if r['n_miss']>0)/len(cov_part)))
print('\nWrong-person contacts (who):',collections.Counter(n for r in rows for n in set(r['contacted'])-set(r['targets'])).most_common(8))
