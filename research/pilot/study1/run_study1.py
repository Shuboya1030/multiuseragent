"""Reproducible Study 1 diagnostic analysis for the TAC trace pilot.

Run from the repository root: python research/pilot/study1/run_study1.py
This script reads the committed TAC raw trajectories and evaluator scores. It
does not alter the legacy pilot outputs.
"""
from __future__ import annotations

import csv, gzip, json, re, hashlib, platform
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research" / "pilot"
OUT = PILOT / "study1"
OUT.mkdir(exist_ok=True)

def norm_model(s):
    return s.replace("20241217_OpenHands-0.14.2-", "")

def wilson(x, n, alpha=.05):
    if n == 0: return [None, None]
    z = 1.959963984540054; p=x/n; den=1+z*z/n
    ctr=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(ctr-half), float(ctr+half)]

def p_fmt(p): return "<0.001" if p < .001 else f"{p:.3f}"

def norm_sf(z): return 0.5*__import__('math').erfc(z/np.sqrt(2))

def chi2_sf(x, df):
    import math
    a=df/2; xx=x/2
    if xx < a+1:
        ap=a; term=1/a; total=term
        for _ in range(10000):
            ap+=1; term*=xx/ap; total+=term
            if abs(term)<abs(total)*1e-15: break
        return max(0.0,min(1.0,1-total*math.exp(-xx+a*math.log(xx)-math.lgamma(a))))
    b=xx+1-a; c=1e300; d=1/b; h=d
    for i in range(1,10000):
        an=-i*(i-a); b+=2; d=an*d+b
        if abs(d)<1e-300: d=1e-300
        c=b+an/c
        if abs(c)<1e-300: c=1e-300
        d=1/d; delta=d*c; h*=delta
        if abs(delta-1)<1e-15: break
    return max(0.0,min(1.0,math.exp(-xx+a*math.log(xx)-math.lgamma(a))*h))

def rankdata(x):
    x=np.asarray(x); order=np.argsort(x); out=np.empty(len(x),float); i=0
    while i<len(order):
        j=i+1
        while j<len(order) and x[order[j]]==x[order[i]]: j+=1
        out[order[i:j]]=(i+1+j)/2; i=j
    return out

def wilcoxon_approx(a,b):
    d=np.asarray(a)-np.asarray(b); d=d[d!=0]
    if not len(d): return 0.0,1.0
    r=rankdata(np.abs(d)); wp=float(r[d>0].sum()); wm=float(r[d<0].sum()); n=len(d)
    _,counts=np.unique(np.abs(d),return_counts=True); tie=float(np.sum(counts**3-counts))
    var=n*(n+1)*(2*n+1)/24-tie/48; z=max(0,(abs(wp-n*(n+1)/4)-.5)/np.sqrt(var)) if var>0 else 0
    return min(wp,wm),min(1,2*norm_sf(z))

def cluster_ols(d):
    # Task/model fixed effects with task-clustered sandwich SE.
    td=pd.get_dummies(d.task,dtype=float).to_numpy()[:,1:]; md=pd.get_dummies(d.model,dtype=float).to_numpy()[:,1:]
    x=np.column_stack([np.ones(len(d)),d.scenario_coverage.to_numpy(float),td,md]); y=d.score.to_numpy(float)
    beta=np.linalg.lstsq(x,y,rcond=None)[0]; residual=y-x@beta; inv=np.linalg.pinv(x.T@x); meat=np.zeros((x.shape[1],x.shape[1]))
    for _,idx in d.groupby('task').indices.items():
        ix=np.asarray(idx); v=x[ix].T@residual[ix]; meat+=np.outer(v,v)
    G=d.task.nunique(); n=len(d); k=x.shape[1]; cov=inv@meat@inv*(G/(G-1))*((n-1)/(n-k))
    se=float(np.sqrt(max(cov[1,1],0))); t=float(beta[1]/se); p=float(min(1,2*norm_sf(abs(t))))
    r2=float(1-np.sum(residual**2)/np.sum((y-y.mean())**2))
    return {'estimate':float(beta[1]),'se':se,'ci95':[float(beta[1]-1.96*se),float(beta[1]+1.96*se)],'p':p,'R2':r2,'n':n,'task_clusters':int(G)}

def main():
    # Rebuild parser-derived events directly from raw files using the documented
    # legacy parser logic, while adding an auditable sent-action count.
    npc=json.loads((PILOT/"tac/npc_definition.json").read_text(encoding="utf-8"))
    u2n={f"{x['first_name']}_{x['last_name']}".lower().replace(' ','_'):f"{x['first_name']} {x['last_name']}" for x in npc}
    raw_dir=PILOT/"traj/raw"; events=[]
    for fp in sorted(raw_dir.glob("*.json.gz")):
        m,t=fp.name.split("__",1); task=re.sub(r'^traj_|(-image)?\.json\.gz$','',t)
        d=json.loads(gzip.open(fp,'rt',encoding='utf-8').read())
        sc=json.loads((PILOT/f"tac/{task}/scenarios.json").read_text(encoding="utf-8"))
        room=None; sent=[]; finished=False; fabricated=False; reached=False; n_enter=0
        for e in d:
            if e.get('observation'):
                ex=e.get('extras') or {}; url=ex.get('url','') if isinstance(ex,dict) else ''
                c=e.get('content') or ''
                h=re.findall(r'\n#\s+([a-z_\.]+)\s*\n',c)
                # Prefer mapping the active direct-message URL to the username
                # in the rendered DM sidebar; retain heading fallback.
                dm_links={u2n.get(name,name):rid for name,rid in re.findall(r'\[\s*([a-z]+_[a-z]+)\b[^\]]*\]\(/direct/([A-Za-z0-9]+)\)',c)}
                if re.search(r':3000/(direct|channel|group)/',url): reached=True
                if '/direct/' in url:
                    rid=url.split('/direct/',1)[1].split('?',1)[0].strip('/')
                    room=next((name for name,link_id in dm_links.items() if link_id==rid),u2n.get(h[0].strip(),h[0].strip()) if h else None)
                elif url and '/direct/' not in url and ':3000' not in url: room=None
            if e.get('action'):
                a=json.dumps(e.get('args',{}),ensure_ascii=False)
                if e['action']=='finish': finished=True
                if re.search(r'simulat|hypothetical|placeholder|assum(e|ing) (the|that)|mock data|dummy',a,re.I) and e['action'] in ('message','finish','run_ipython','run'): fabricated=True
                ba=(e.get('args') or {}).get('browser_actions','') if isinstance(e.get('args'),dict) else ''
                if room and re.search(r"press\([^)]*Enter|keyboard_press\('Enter'|\n'\)\s*$",ba): sent.append(room); n_enter+=1
                elif room and re.search(r"fill\(",ba) and 'Enter' in ba: sent.append(room); n_enter+=1
                for u in re.findall(r"@([a-z]+_[a-z]+)",ba):
                    if u in u2n and 'Enter' in ba: sent.append(u2n[u])
        events.append(dict(model=norm_model(m),task=task,targets=sorted(sc.keys()),sent=sent,contacted=sorted(set(sent)),n_sent_actions=n_enter,steps=len(d),finished=finished,fabricated=fabricated,reached_chat=reached,source_file=fp.name))

    # Reconcile full balanced panel and evaluator results.
    res={}
    for fp in (PILOT/"traj/res").glob("*.json"):
        m,t=fp.name.split("__",1); task=re.sub(r'^eval_|(-image)?\.json$','',t)
        fs=json.loads(fp.read_text(encoding='utf-8'))['final_score']; res[(norm_model(m),task)]=(fs['result'],fs['total'])
    rows=[]
    for e in events:
        if e['task'] not in [p.name for p in (PILOT/'tac').iterdir() if p.is_dir()]: continue
        if not e['targets']: continue
        score,total=res[(e['model'],e['task'])]
        T=set(e['targets']); C=set(e['contacted']); hit=T&C; outside=C-T; miss=T-C
        rows.append({**e,'score':score/total if total else np.nan,'raw_score':score,'score_total':total,'success':int(score==total),'n_target':len(T),'n_contacted_target':len(hit),'n_outside_scenario':len(outside),'n_uncalled_scenario':len(miss),'scenario_coverage':len(hit)/len(T),'any_scenario_contact':int(bool(hit)),'any_outside_scenario':int(bool(outside)),'all_scenario_contacts':int(len(miss)==0)})
    df=pd.DataFrame(rows)
    if len(df)!=390 or df.task.nunique()!=39 or df.model.nunique()!=10 or df.groupby(['task','model']).size().max()!=1:
        raise RuntimeError(f"Expected balanced 39 x 10 panel; got rows={len(df)}, tasks={df.task.nunique()}, models={df.model.nunique()}")
    df.to_json(OUT/'episode_level.json',orient='records',indent=2,force_ascii=False)
    df.drop(columns=['targets','sent','contacted']).to_csv(OUT/'episode_level.csv',index=False,encoding='utf-8-sig')
    legacy=json.loads((PILOT/'traj/events.json').read_text(encoding='utf-8'))
    legacy_map={(x['model'],x['task']):set(x['contacted']) for x in legacy}
    contact_mismatches=[(r.model,r.task) for r in df.itertuples() if set(r.contacted)!=legacy_map.get((r.model,r.task),set())]
    if contact_mismatches: raise RuntimeError(f"Recipient parser differs from legacy events for {len(contact_mismatches)} episodes")
    qa={'raw_traces':len(events),'parsed_event_rows':len(events),'analysis_rows':len(df),'excluded_empty_roster_rows':len(events)-len(df),'balanced_task_model_panel':True,'recipient_set_mismatches_vs_legacy':len(contact_mismatches),'evaluator_join_complete':True}
    (OUT/'quality_checks.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')

    # Descriptives and model-level matched tests (task is the repeated unit).
    summary=[]
    for model,g in df.groupby('model',sort=True):
        summary.append({'model':model,'n_tasks':len(g),'mean_scenario_coverage':g.scenario_coverage.mean(),'sd_scenario_coverage':g.scenario_coverage.std(ddof=1),'any_target_contact_n':int(g.any_scenario_contact.sum()),'any_target_contact_rate':g.any_scenario_contact.mean(),'contact_rate_ci95':wilson(int(g.any_scenario_contact.sum()),len(g)),'success_n':int(g.success.sum()),'success_rate':g.success.mean(),'mean_checkpoint_score':g.score.mean(),'sd_checkpoint_score':g.score.std(ddof=1),'outside_scenario_rate':g.any_outside_scenario.mean(),'no_chat_rate':1-g.reached_chat.mean()})
    sm=pd.DataFrame(summary); sm.to_csv(OUT/'model_summary.csv',index=False,encoding='utf-8-sig')
    contact_out=[]
    for contacted,g in df.groupby('any_scenario_contact'):
        contact_out.append({'any_scenario_contact':int(contacted),'n':len(g),'mean_score':g.score.mean(),'sd_score':g.score.std(ddof=1),'success_n':int(g.success.sum()),'success_rate':g.success.mean()})
    pd.DataFrame(contact_out).to_csv(OUT/'contact_outcome_summary.csv',index=False,encoding='utf-8-sig')
    # Dependency-free SVG figure: mean task coverage with ±1 SD across tasks.
    figdir=OUT/'figures'; figdir.mkdir(exist_ok=True)
    ordered=sm.sort_values('mean_scenario_coverage')
    W,H=1000,650; left,right,top,bottom=300,80,50,80; pw=W-left-right; ph=H-top-bottom
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>', '<style>text{font-family:Arial,sans-serif;fill:#222}.small{font-size:13px}.label{font-size:15px}.title{font-size:21px;font-weight:bold}</style>', '<text x="500" y="28" text-anchor="middle" class="title">Scenario-roster contact coverage by model</text>']
    for tick in range(0,11,2):
        x=left+pw*tick/10; parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ph}" stroke="#ddd"/>')
        parts.append(f'<text x="{x:.1f}" y="{top+ph+24}" text-anchor="middle" class="small">{tick/10:.1f}</text>')
    rowh=ph/len(ordered)
    for i,(_,r) in enumerate(ordered.iterrows()):
        y=top+(i+.5)*rowh; mean=float(r.mean_scenario_coverage); sd=float(r.sd_scenario_coverage)
        x=left+pw*mean; x0=left+pw*max(0,mean-sd); x1=left+pw*min(1,mean+sd)
        label=str(r.model).replace('&','&amp;').replace('<','&lt;')
        parts.append(f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" class="label">{label}</text>')
        parts.append(f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" stroke="#4385bd" stroke-width="2"/>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#185a8d"/>')
        parts.append(f'<text x="{x+10:.1f}" y="{y+4:.1f}" class="small">{mean:.2f}</text>')
    parts += [f'<text x="{left+pw/2}" y="{H-18}" text-anchor="middle" class="label">Mean proportion of scenario-listed people contacted (±1 SD across 39 tasks)</text>', '<text x="20" y="620" class="small">Roster coverage is a proxy; scenario lists are not verified required-recipient labels.</text>', '</svg>']
    (figdir/'model_coverage.svg').write_text('\n'.join(parts),encoding='utf-8')
    wide=df.pivot(index='task',columns='model',values='scenario_coverage')
    rankmat=np.vstack([rankdata(-row) for row in wide.to_numpy(float)])
    n,k=rankmat.shape; rank_sums=rankmat.sum(axis=0)
    q0=12/(n*k*(k+1))*np.sum(rank_sums**2)-3*n*(k+1)
    tie_sum=0
    for row in wide.to_numpy(float):
        _,counts=np.unique(row,return_counts=True); tie_sum+=np.sum(counts**3-counts)
    friedman=float(q0/(1-tie_sum/(n*(k**3-k)))); fp=chi2_sf(friedman,k-1)
    kendall_w=float(friedman/(n*(k-1)))
    pair=[]
    names=list(wide.columns)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            w,pv=wilcoxon_approx(wide[a].values,wide[b].values)
            pair.append({'model_a':a,'model_b':b,'median_paired_delta':float(np.median(wide[a]-wide[b])),'mean_paired_delta':float(np.mean(wide[a]-wide[b])),'wilcoxon_W':w,'p_raw':pv})
    order=np.argsort([p['p_raw'] for p in pair]); adjusted=np.ones(len(pair)); running=0
    for rank,idx in enumerate(order):
        running=max(running,min(1,(len(pair)-rank)*pair[idx]['p_raw'])); adjusted[idx]=running
    for p,q in zip(pair,adjusted): p['p_holm']=float(q); p['reject_holm_0_05']=bool(q<.05)
    pd.DataFrame(pair).to_csv(OUT/'coverage_pairwise_holm.csv',index=False,encoding='utf-8-sig')
    n_pair_sig=sum(p['reject_holm_0_05'] for p in pair)

    # Overall episode-level descriptive rates with Wilson intervals.
    def rate(k):
        x=int(df[k].sum()); n=len(df); return {'n':x,'N':n,'rate':x/n,'ci95_wilson':wilson(x,n)}
    rates={k:rate(k) for k in ['any_scenario_contact','all_scenario_contacts','any_outside_scenario','success','fabricated']}
    # Exploratory association: task and model fixed effects, task-clustered SE.
    fit=cluster_ols(df)
    coef={'term':'scenario_coverage','estimate':fit['estimate'],'se_task_clustered':fit['se'],'ci95':fit['ci95'],'p':fit['p'],'R2':fit['R2'],'n':fit['n'],'task_clusters':fit['task_clusters'],'interpretation':'score association per 1.0 (0-to-1) increase in scenario-set coverage; observational, not causal'}
    # Sensitivity excluding task(s) with very large candidate sets (17 people).
    dsmall=df[df.n_target<10].copy()
    fsmall=cluster_ols(dsmall)
    coef['sensitivity_n_target_lt_10']={'estimate':fsmall['estimate'],'se':fsmall['se'],'ci95':fsmall['ci95'],'p':fsmall['p'],'n':fsmall['n'],'task_clusters':fsmall['task_clusters']}
    # Binary successful task completion model with fixed effects is reported only as sensitivity.
    # Sparse successes make this unstable; primary endpoint remains fractional score.
    summary_json={'panel':{'n_episodes':len(df),'n_tasks':df.task.nunique(),'n_models':len(names),'balanced':True,'task_repetitions':10},'overall_rates':rates,'model_coverage_friedman':{'statistic':friedman,'df':9,'p':fp,'kendall_W':kendall_w,'matched_unit':'task','posthoc':'45 pairwise asymptotic Wilcoxon signed-rank tests; Holm adjusted; see coverage_pairwise_holm.csv','holm_significant_pairs':n_pair_sig},'coverage_score_association':coef,'model_summary':summary}
    (OUT/'metrics.json').write_text(json.dumps(summary_json,indent=2,ensure_ascii=False),encoding='utf-8')
    manifest={'analysis':'Study 1 trace diagnostic','data_source':'TheAgentCompany/OpenHands 0.14.2 archived pilot traces in research/pilot/traj/raw and evaluator outputs in research/pilot/traj/res','run_date_local':'2026-10-23','python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'source_trace_count':len(events),'episode_count_in_analysis':len(df),'seed':None,'note':'Deterministic parsing and inferential analyses; no resampling randomness used.'}
    manifest['raw_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(raw_dir.glob('*.json.gz'))}
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

    # Human-readable statistical appendix and concise results report.
    model_table='\n'.join(f"| {r.model} | {r.mean_scenario_coverage:.3f} | {r.mean_checkpoint_score:.3f} | {int(r.success_n)}/39 |" for r in sm.sort_values('mean_scenario_coverage',ascending=False).itertuples())
    report=f'''# Study 1 analysis report\n\n## Scope and conclusion\n\nThis is a retrospective trace diagnostic, not a causal evaluation of a help-seeking method. We reprocessed {len(events)} raw trajectories and analyzed the balanced subset of {len(df)} task-model episodes ({df.task.nunique()} tasks × {df.model.nunique()} model configurations). We operationalize help-seeking only as contact with people listed in each task's `scenarios.json`; that list is a candidate/context roster, not verified ground truth for who was required or appropriate to contact. Therefore all contact rates below are **scenario-roster proxies**.\n\n## Data and processing\n\nRaw browser actions were parsed to detect chat-room context and Enter-submitted messages; evaluator outputs provide normalized checkpoint score (result/total) and exact completion. The analysis excludes the single task with no `scenarios.json` recipient roster (10 episodes). We verified the expected complete balanced panel and complete evaluator join. Parsed unique-recipient sets match the legacy event extraction exactly for all analyzed rows; this checks implementation consistency, not semantic correctness. A new row-level dataset preserves parsed recipient lists and sends. The parser has not received independent double annotation.\n\nTask policy audit: of the 40 task folders, 17 explicitly specify a fixed contact set/group, 15 involve conditional or choice-based contact, 6 require dynamic recipient discovery, 1 has no person-contact task, and 1 has a prompt/roster mismatch. These are first-pass single-researcher codes; see `task_policy_codebook.csv`.\n\n## Findings\n\n- At least one roster-listed person was contacted in {rates['any_scenario_contact']['n']}/{len(df)} episodes ({rates['any_scenario_contact']['rate']:.1%}; Wilson 95% CI {rates['any_scenario_contact']['ci95_wilson'][0]:.1%}–{rates['any_scenario_contact']['ci95_wilson'][1]:.1%}). This is contact occurrence, not a correctness rate.\n- Every scenario-listed person was contacted in {rates['all_scenario_contacts']['n']}/{len(df)} episodes ({rates['all_scenario_contacts']['rate']:.1%}); this is **not** a required-contact completion rate because task rosters can include conditional/alternative contacts.\n- An unlisted person was also contacted in {rates['any_outside_scenario']['n']}/{len(df)} episodes ({rates['any_outside_scenario']['rate']:.1%}); this is a roster mismatch signal, not proof of an inappropriate recipient.\n- Exact evaluator completion occurred in {rates['success']['n']}/{len(df)} episodes ({rates['success']['rate']:.1%}; Wilson 95% CI {rates['success']['ci95_wilson'][0]:.1%}–{rates['success']['ci95_wilson'][1]:.1%}).\n\n| Model configuration | Mean roster coverage | Mean checkpoint score | Exact completions |\n|---|---:|---:|---:|\n{model_table}\n\n### H1a — Are help-seeking-related behaviors visible in failures?\n\n**Answer: partially, as a descriptive signal only.** Episodes with at least one roster-listed contact had mean normalized score {contact_out[1]["mean_score"]:.3f} (SD {contact_out[1]["sd_score"]:.3f}; exact completion {contact_out[1]["success_n"]}/{contact_out[1]["n"]}, {contact_out[1]["success_rate"]:.1%}); episodes with no roster-listed contact had mean score {contact_out[0]["mean_score"]:.3f} (SD {contact_out[0]["sd_score"]:.3f}; exact completion {contact_out[0]["success_n"]}/{contact_out[0]["n"]}, {contact_out[0]["success_rate"]:.1%}). This descriptive split is strongly confounded by task difficulty and agent competence. Existing trace structure alone does not establish that every roster member was necessary, that an unlisted contact was wrong, or that non-contact caused a failure. Among the 357 non-complete episodes, {int(((df.success==0)&(df.any_scenario_contact==0)).sum())} ({int(((df.success==0)&(df.any_scenario_contact==0)).sum())/int((df.success==0).sum()):.1%}) had no observed contact with a roster-listed person. This is a failure-associated trace pattern, not a verified missed-help event. Thus the stronger “fraction of failures caused by wrong/missed help-seeking” claim is **not identified by these data**.\n\n### H1b — Do models differ in help-seeking behavior?\n\nMean scenario-roster coverage ranges from {sm.mean_scenario_coverage.min():.3f} to {sm.mean_scenario_coverage.max():.3f} across model configurations. A Friedman test on matched task-level coverage gives χ²(9)={friedman:.2f}, p{p_fmt(fp)}, Kendall's W={kendall_w:.3f}. {n_pair_sig} of 45 Holm-corrected pairwise comparisons are significant (α=.05); details are in `coverage_pairwise_holm.csv`. This supports model heterogeneity in **roster coverage behavior** on this fixed task sample; it does not establish relative quality of recipient choice.\n\n### H1c — Is contact coverage associated with task score?\n\nIn an exploratory OLS model with task and model fixed effects and standard errors clustered by task, a 0-to-1 increase in scenario-roster coverage is associated with a {coef['estimate']:.3f} change in normalized checkpoint score (95% CI {coef['ci95'][0]:.3f} to {coef['ci95'][1]:.3f}; p{p_fmt(coef['p'])}; n={coef['n']}, {coef['task_clusters']} task clusters). This is an observational association, not a causal effect; both score and contact behavior can be driven by task-specific difficulty or agent competence. Excluding tasks with 10+ roster members, the estimate is {coef['sensitivity_n_target_lt_10']['estimate']:.3f} (95% CI {coef['sensitivity_n_target_lt_10']['ci95'][0]:.3f} to {coef['sensitivity_n_target_lt_10']['ci95'][1]:.3f}; p{p_fmt(coef['sensitivity_n_target_lt_10']['p'])}; {coef['sensitivity_n_target_lt_10']['task_clusters']} tasks).\n\n## Study-level conclusion\n\nStudy 1 establishes a reproducible baseline showing that help-seeking traces and task outcomes can be measured, and that roster coverage varies across model-task runs. It does **not yet validate a benchmark of correct “who to ask” decisions**, nor demonstrate that help-seeking errors explain failures. The strongest defensible contribution is a diagnostic motivation study that identifies measurement and annotation needs for Study 2.\n\n## Required follow-up before publication\n\n1. Independently annotate a stratified sample of send actions, active recipient, whether the recipient was required/valid, whether a reply was received, and whether the agent used it; report inter-annotator agreement.\n2. Code each task's recipient policy from its full task instructions and scenarios: mandatory named contacts, conditional/alternative contacts, information-discovery tasks, and ambiguous/non-help-seeking tasks. Re-estimate H1a on the verified subset.\n3. Treat `reached_chat=False` as “no observed Rocket.Chat page in parsed trace,” not “UI-blocked.”\n4. Avoid causal language for H1c; test causality only in a controlled rerun/intervention.\n'''
    (OUT/'analysis-report.md').write_text(report,encoding='utf-8')
    appendix=f'''# Statistical appendix\n\n## Design and analysis units\n\n- Primary repeated unit: task (39 paired tasks × 10 fixed model configurations).\n- Episode-level denominator: {len(df)}; each task appears once per model.\n- Contact proxies: `scenario_coverage` = unique contacted scenario-listed NPCs / number listed; `any_scenario_contact`; `all_scenario_contacts`; `any_outside_scenario`.\n- Outcome: normalized checkpoint score = evaluator result / total. Exact completion is descriptive only.\n- Missing roster: one no-scenario task excluded, leaving 390/400 episodes.\n\n## H1a descriptive inference\n\nWilson score intervals (95%) are reported for key binary episode rates in `metrics.json`. They describe uncertainty over episode proportions under a binomial approximation, but episodes are clustered by task and model; hence they are not population-level independent-sample intervals. Treat as descriptive precision, not a design-based generalization.\n\n## H1b matched model comparison\n\nFriedman rank test across 10 model configurations, blocking by task, on per-task roster coverage; statistic χ²(9)={friedman:.4f}, p={fp:.6g}. Kendall's W={kendall_w:.4f} (χ²/[n(k−1)]). Pairwise follow-ups use two-sided asymptotic Wilcoxon signed-rank tests on the 39 matched task differences, with Holm family-wise correction over 45 comparisons. Full estimates, raw p-values, adjusted p-values and adjusted decisions are in `coverage_pairwise_holm.csv`.\n\n## H1c adjusted association\n\nOLS: normalized score ~ scenario coverage + task fixed effects + model fixed effects; task-clustered sandwich standard errors with finite-sample correction. Estimate={coef['estimate']:.5f}, SE={coef['se_task_clustered']:.5f}, 95% CI [{coef['ci95'][0]:.5f}, {coef['ci95'][1]:.5f}], p={coef['p']:.6g}, R²={coef['R2']:.4f}. Sensitivity excluding tasks whose roster has ≥10 people: estimate={coef['sensitivity_n_target_lt_10']['estimate']:.5f}, SE={coef['sensitivity_n_target_lt_10']['se']:.5f}, 95% CI [{coef['sensitivity_n_target_lt_10']['ci95'][0]:.5f}, {coef['sensitivity_n_target_lt_10']['ci95'][1]:.5f}], p={coef['sensitivity_n_target_lt_10']['p']:.6g}.\n\nNo normality test is used to select the regression: inference uses task-clustered robust errors and asymptotic normal p-values/CIs. The small number of clusters (39), unmodeled task-by-model interactions, bounded score, and endogenous coverage remain limitations. These results should be considered exploratory.\n\n## Reproduction\n\nFrom repository root: `python research/pilot/study1/run_study1.py`. Deterministic parser and analysis; no random seed required. Environment and SHA-256 hashes are in `run_manifest.json`.\n'''
    (OUT/'stats-appendix.md').write_text(appendix,encoding='utf-8')
    (OUT/'figure-catalog.md').write_text('# Figure catalog\n\n- `figures/model_coverage.svg`: model mean scenario-roster coverage across 39 matched tasks; horizontal bars show ±1 SD across tasks (descriptive dispersion, not a confidence interval). The roster is a proxy, not gold labels of required recipients.\n',encoding='utf-8')
    print(json.dumps({'episodes':len(df),'tasks':df.task.nunique(),'models':df.model.nunique(),'friedman':summary_json['model_coverage_friedman'],'association':coef,'rates':rates},indent=2))

if __name__=='__main__': main()
