"""Cluster-aware analysis and figure generation for the v0.4 Study 2 extension."""
from __future__ import annotations
import csv, hashlib, json, math, random, subprocess
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DER = ROOT / "derived"
RUNS = ROOT / "runs.jsonl"
OUTCOMES = [
    ("total_tokens", "Input + output tokens per episode"),
    ("strict_first_information_step_valid", "Strict first information step"),
    ("valid_path", "Valid path completion"),
    ("task_score_T", "Task score T"),
    ("reward_R", "Fixed composite R"),
    ("total_cost", "Query cost"),
    ("N_knowledge_miss", "Knowledge misses"),
    ("N_auth_recomputed", "Unauthorized approval attempts"),
    ("N_premature_approval", "Premature approval requests"),
    ("N_repeat_requests", "Repeated requests"),
    ("N_unhelpful_recomputed", "Unhelpful requests"),
    ("N_asks", "Help requests"),
]

def read_jsonl(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def mean(xs): return sum(xs)/len(xs) if xs else float("nan")
def template(task_id): return task_id.removeprefix("S2_").removesuffix("_aligned").removesuffix("_separated")
def num(r,k):
    if k=="total_tokens":return float(r.get("input_tokens",0) or 0)+float(r.get("output_tokens",0) or 0)
    v=r.get(k)
    return float(bool(v)) if isinstance(v,bool) else float(v or 0)
def write_csv(path, rows):
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        fields=list(dict.fromkeys(k for r in rows for k in r))
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def cluster_effects(rows, metric, high, low, model_filter=None, alignment_filter=None, origin_filter=None):
    cells=defaultdict(list)
    for r in rows:
        if model_filter and r["model_id"] not in model_filter: continue
        if alignment_filter and r["alignment"] not in alignment_filter: continue
        if origin_filter and r.get("template_origin") not in origin_filter: continue
        cells[(r["model_id"],r["task_id"],r["profile_condition"])].append(num(r,metric))
    by_cluster=defaultdict(dict)
    for (m,t,c),vs in cells.items(): by_cluster[(m,t)][c]=mean(vs)
    # Average model-specific condition differences within task template; keep each template as a cluster.
    diff=defaultdict(list)
    for (m,t),cs in by_cluster.items():
        if high in cs and low in cs: diff[template(t)].append(cs[high]-cs[low])
    return {k:mean(v) for k,v in diff.items()}

def boot_interval(vals, seed, draws=20000):
    keys=sorted(vals); x=[vals[k] for k in keys]; rng=random.Random(seed); n=len(x)
    if not n:return float("nan"),float("nan")
    bs=sorted(mean([x[rng.randrange(n)] for _ in range(n)]) for _ in range(draws))
    return bs[int(.025*draws)],bs[min(draws-1,int(.975*draws))]

def signflip(vals, seed, draws=50000):
    x=list(vals.values()); n=len(x)
    if n==0:return 1.0
    obs=abs(mean(x)); rng=random.Random(seed); ge=0
    for _ in range(draws):
        ge += abs(mean([v if rng.getrandbits(1) else -v for v in x])) >= obs-1e-12
    return (ge+1)/(draws+1)

def holm(pvals):
    order=sorted(range(len(pvals)),key=lambda i:pvals[i]); out=[0.0]*len(pvals); running=0
    for rank,i in enumerate(order):
        running=max(running,(len(pvals)-rank)*pvals[i]); out[i]=min(1,running)
    return out

def svg_bar(rows, title, path):
    # Compact standalone SVG forest plot; error bars are bootstrap intervals.
    W,H=1050,max(280,95+38*len(rows)); left,right=360,1000; center=(left+right)/2; scale=270
    axis=max([abs(float(r[k])) for r in rows for k in ("ci_low","ci_high")]+[0.1])*1.08
    scale=270/axis
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<rect width="100%" height="100%" fill="white"/>',
       f'<text x="30" y="32" font-family="Arial" font-size="21" font-weight="bold">{title}</text>',
       f'<line x1="{center}" y1="58" x2="{center}" y2="{H-25}" stroke="#666" stroke-dasharray="4 4"/>']
    for i,r in enumerate(rows):
        y=78+i*38; est=float(r["mean_difference"]); lo=float(r["ci_low"]); hi=float(r["ci_high"])
        x=center+est*scale; x1=center+lo*scale; x2=center+hi*scale
        label=f'{r["model"]} · {r["contrast"]} · {r["outcome_label"]}'
        s += [f'<text x="28" y="{y+5}" font-family="Arial" font-size="13">{label}</text>',
              f'<line x1="{x1:.1f}" y1="{y}" x2="{x2:.1f}" y2="{y}" stroke="#2463a6" stroke-width="2"/>',
              f'<line x1="{x1:.1f}" y1="{y-5}" x2="{x1:.1f}" y2="{y+5}" stroke="#2463a6"/>',
              f'<line x1="{x2:.1f}" y1="{y-5}" x2="{x2:.1f}" y2="{y+5}" stroke="#2463a6"/>',
              f'<circle cx="{x:.1f}" cy="{y}" r="4.5" fill="#d35400"/>',
              f'<text x="{min(W-64,x2+8):.1f}" y="{y+4}" font-family="Arial" font-size="11">{est:+.2f}</text>']
    s+=['<text x="390" y="%d" font-family="Arial" font-size="11">← negative contrast · zero reference · positive contrast →</text>'%(H-8),'</svg>']
    path.write_text("\n".join(s),encoding="utf-8")

def main():
    DER.mkdir(exist_ok=True)
    # Use trace-recomputed metrics, not just the original run rows. The strict
    # first-step and decomposed error outcomes are derived by validate_study2.py.
    allruns=read_jsonl(DER/"run_level_metrics_all.jsonl")
    blueprints=read_jsonl(ROOT/"task_blueprints_v0.4.jsonl")
    tasks={x["task_id"]:x for x in blueprints}
    rows=[r for r in allruns if r.get("task_version")=="0.4" and r.get("profile_version")=="profile-0.4"
          and tasks.get(r["task_id"],{}).get("template_origin")=="previously_seen_template" and r.get("rep")==0]
    expected={(t,m,c,0) for t in {x["task_id"] for x in blueprints if x["template_origin"]=="previously_seen_template"} for m in {x["model_id"] for x in allruns if x.get("task_version")=="0.4"} for c in ("R0","R1","R2")}
    observed={(x["task_id"],x["model_id"],x["profile_condition"],x["rep"]) for x in rows}
    if len(rows)!=len(observed): raise SystemExit("Duplicate v0.4 planned cells detected; preserve and audit before primary analysis.")
    if observed!=expected: raise SystemExit(f"Incomplete v0.4 collection: {len(observed)}/{len(expected)} cells")
    order_sets=defaultdict(set)
    for r in rows:order_sets[(r["task_id"],r["rep"])].add(tuple(r.get("candidate_order",[])))
    order_mismatches={str(k):v for k,v in order_sets.items() if len(v)!=1}
    if order_mismatches:raise SystemExit(f"Candidate display order differs within paired cells: {list(order_mismatches)[:3]}")
    for r in rows:r["template_origin"]=tasks[r["task_id"]]["template_origin"]
    write_csv(DER/"study2_v04_task_inventory.csv",[
        {"task_id":t["task_id"],"workflow_template":template(t["task_id"]),"template_origin":t["template_origin"],"domain":t["domain"],"alignment":t["alignment"],"candidate_count":len(t["candidates"]),"knowledge_holder":t["gold_admissible_recipients_by_step"]["information"][0],"approver":t["gold_admissible_recipients_by_step"]["approval"][0],"knowledge_and_authority_same_person":t["alignment"]=="aligned","partial_knowledge_distractor_count":sum(bool(p.get("partial_knowledge")) for p in t["candidates"])}
        for t in blueprints if t["template_origin"]=="previously_seen_template"
    ])
    write_csv(DER/"study2_v04_profile_lengths.csv",[
        {"model":m,"condition":c,"n_episodes":len(g),"mean_profile_char_count":mean([int(x.get("profile_char_count",0)) for x in g]),"min_chars":min(int(x.get("profile_char_count",0)) for x in g),"max_chars":max(int(x.get("profile_char_count",0)) for x in g)}
        for (m,c),g in sorted(_group(rows,lambda r:(r["model_id"],r["profile_condition"])).items())
    ])
    token_rows=[]
    for c in ("R0","R1","R2"):
        g=[r for r in rows if r["profile_condition"]==c]
        n_success=sum(bool(r.get("valid_path_recomputed")) for r in g)
        total=sum(num(r,"total_tokens") for r in g)
        token_rows.append({"condition":c,"n_episodes":len(g),"task_successes":n_success,"task_success_rate":n_success/len(g),"mean_input_tokens_per_episode":mean([float(r.get("input_tokens",0) or 0) for r in g]),"mean_output_tokens_per_episode":mean([float(r.get("output_tokens",0) or 0) for r in g]),"mean_total_tokens_per_episode":mean([num(r,"total_tokens") for r in g]),"median_total_tokens_per_episode":sorted(num(r,"total_tokens") for r in g)[len(g)//2],"aggregate_tokens_per_success":total/n_success if n_success else float("nan"),"mean_total_tokens_among_successes":mean([num(r,"total_tokens") for r in g if r.get("valid_path_recomputed")])})
    write_csv(DER/"study2_v04_token_costs.csv",token_rows)
    write_csv(DER/"study2_v04_cell_summary.csv",[
        {"model":m,"alignment":a,"condition":c,"template_origin":o,"n_episodes":len(g),**{k:mean([num(x,k) for x in g]) for k,_ in OUTCOMES}}
        for (m,a,c,o),g in sorted(_group(rows,lambda r:(r["model_id"],r["alignment"],r["profile_condition"],r["template_origin"])).items())
    ])
    models=sorted({r["model_id"] for r in rows}); contrast_pairs=[("R1-R0","R1","R0"),("R2-R1","R2","R1")]
    res=[]
    for metric,label in OUTCOMES:
      for m in models+(["fixed_model_average"]):
       mf=None if m=="fixed_model_average" else {m}
       for con,h,l in contrast_pairs:
        for ali,af in [("all",None),("aligned",{"aligned"}),("separated",{"separated"})]:
         vals=cluster_effects(rows,metric,h,l,mf,af)
         lo,hi=boot_interval(vals,20261024+len(res))
         res.append({"model":m,"outcome":metric,"outcome_label":label,"contrast":con,"alignment":ali,"n_template_clusters":len(vals),"mean_difference":mean(list(vals.values())),"ci_low":lo,"ci_high":hi,"signflip_p_mc":signflip(vals,20263000+len(res))})
    # Holm correction only for the declared primary outcomes and two contrasts (fixed-model aggregate).
    idx=[i for i,r in enumerate(res) if r["model"]=="fixed_model_average" and r["alignment"]=="all" and r["outcome"] in {"strict_first_information_step_valid","valid_path","task_score_T"}]
    adj=holm([res[i]["signflip_p_mc"] for i in idx])
    for i,p in zip(idx,adj):res[i]["holm_p_primary_family"]=p
    write_csv(DER/"study2_v04_contrasts.csv",res)
    # Prespecified difference-in-differences: separated minus aligned contrast, averaged within workflow template.
    did_rows=[]
    for metric,label in OUTCOMES:
      for con,h,l in contrast_pairs:
       per_template=defaultdict(list)
       for model in models:
        for tid in {template(r["task_id"]) for r in rows}:
         vals={}
         for align in ("aligned","separated"):
          for cond in (h,l):
           v=[num(r,metric) for r in rows if r["model_id"]==model and template(r["task_id"])==tid and r["alignment"]==align and r["profile_condition"]==cond]
           if v: vals[(align,cond)]=mean(v)
         if all(k in vals for k in [("aligned",h),("aligned",l),("separated",h),("separated",l)]):
          d=(vals[("separated",h)]-vals[("separated",l)])-(vals[("aligned",h)]-vals[("aligned",l)])
          per_template[tid].append(d)
       effects={k:mean(v) for k,v in per_template.items()}; lo,hi=boot_interval(effects,20266000+len(did_rows))
       did_rows.append({"outcome":metric,"outcome_label":label,"contrast":con,"n_template_clusters":len(effects),"mean_difference_in_differences":mean(list(effects.values())),"ci_low":lo,"ci_high":hi,"signflip_p_mc":signflip(effects,20267000+len(did_rows))})
    write_csv(DER/"study2_v04_alignment_interactions.csv",did_rows)
    figrows=[r for r in res if r["model"]=="fixed_model_average" and r["alignment"]=="all" and r["outcome"] in ("strict_first_information_step_valid","valid_path","task_score_T","reward_R","total_cost")]
    svg_bar(figrows,"Study 2 v0.4: paired profile-condition effects (95% template-cluster bootstrap CI)",DER/"study2_v04_main_effects.svg")
    errrows=[r for r in res if r["model"]=="fixed_model_average" and r["alignment"]=="all" and r["contrast"]=="R1-R0" and r["outcome"] in ("N_knowledge_miss","N_auth_recomputed","N_premature_approval","N_repeat_requests","N_unhelpful_recomputed")]
    svg_bar(errrows,"Study 2 v0.4: error and interaction changes, R1 minus R0",DER/"study2_v04_error_effects.svg")
    # Coverage and run metadata.
    origins=Counter([tasks[t]["template_origin"] for t in tasks])
    md=["# Study 2 v0.4 corrected-profile replication analysis", "",f"- Episodes: {len(rows)}; planned cells: {len(expected)}; task variants: {len({x['task_id'] for x in rows})}; workflow-template clusters: {len({template(r['task_id']) for r in rows})}.",f"- Task blueprint inventory (including excluded extension): {dict(origins)}.",f"- Models: {', '.join(models)}; conditions: R0/R1/R2; one analyzed episode per planned cell.",f"- Candidate display-order mismatches within paired cells: {len(order_mismatches)}.",f"- Run statuses: {dict(Counter(r.get('status') for r in rows))}.","- Inference unit: workflow-template cluster. Bootstrap intervals resample templates; sign-flip p-values use Monte Carlo sign randomization. Primary family uses Holm adjustment.","- Historical runs and the interrupted v0.4 three-repetition batch are analyzed separately/excluded from this 168-cell replication. Fixed R weights are unchanged and no weight sensitivity scan was run.","- Strict first-step validity requires the first action to request information from an admissible knowledge holder; the legacy `first_valid` field is not used.","", "## Primary contrasts (fixed-model average)",""]
    for r in res:
      if r["model"]=="fixed_model_average" and r["alignment"]=="all" and r["outcome"] in ("strict_first_information_step_valid","valid_path","task_score_T","reward_R","total_cost","N_auth_recomputed","N_knowledge_miss"):
       adj=(f'; Holm-adjusted p={r["holm_p_primary_family"]:.4f}' if "holm_p_primary_family" in r else "")
       md.append(f'- {r["outcome_label"]}, {r["contrast"]}: {r["mean_difference"]:+.3f} (95% CI {r["ci_low"]:+.3f} to {r["ci_high"]:+.3f}; {r["n_template_clusters"]} templates; Monte Carlo sign-flip p={r["signflip_p_mc"]:.4f}{adj}).')
    md += ["", "## Token use (input plus output tokens)", "", "Token counts are summed over every model call in an episode. They are a usage measure, not billed-dollar cost; this Codex CLI run does not provide a comparable monetary price.", ""]
    for r in token_rows:
       md.append(f'- {r["condition"]}: mean {r["mean_total_tokens_per_episode"]:,.0f} tokens/episode; {r["task_successes"]}/{r["n_episodes"]} valid-path successes; {r["aggregate_tokens_per_success"]:,.0f} aggregate tokens per successful task.')
    for r in res:
       if r["model"]=="fixed_model_average" and r["alignment"]=="all" and r["outcome"]=="total_tokens":
          md.append(f'- {r["contrast"]}: {r["mean_difference"]:,.0f} tokens/episode (95% CI {r["ci_low"]:,.0f} to {r["ci_high"]:,.0f}; template-cluster bootstrap).')
    md += ["", "## Model-stratified estimates", "", "These describe two fixed model configurations, not a comparison of model families.", ""]
    for r in res:
      if r["model"]!="fixed_model_average" and r["alignment"]=="all" and r["outcome"] in ("strict_first_information_step_valid","valid_path","task_score_T","reward_R","total_cost","N_auth_recomputed","N_knowledge_miss"):
       md.append(f'- {r["model"]}, {r["outcome_label"]}, {r["contrast"]}: {r["mean_difference"]:+.3f} (95% CI {r["ci_low"]:+.3f} to {r["ci_high"]:+.3f}).')
    md += ["", "## Alignment interactions",""]
    for r in did_rows:
      if r["outcome"] in ("strict_first_information_step_valid","valid_path","task_score_T","reward_R"):
       md.append(f'- {r["outcome_label"]}, {r["contrast"]}, separated-minus-aligned difference-in-differences: {r["mean_difference_in_differences"]:+.3f} (95% CI {r["ci_low"]:+.3f} to {r["ci_high"]:+.3f}).')
    md += ["", "## Interpretation guardrails", "", "- R1 and R2 contain the same audited role facts, but their profile strings are not length-matched (see `study2_v04_profile_lengths.csv`). Interpret R2−R1 as the effect of the structured-profile package, including formatting and its length/serialization, rather than a pure typography effect.","- Model-specific rows are fixed-configuration comparisons; they are not evidence that one model family is generally better.","- The 14 workflow-template clusters remain the basis for uncertainty.","- The 12 new extension templates are audited but excluded from this 168-cell confirmatory replication.","- Simulation realism and lack of human-response variability limit external validity; automated checks are not a substitute for human double-review of task realism.",""]
    (DER/"study2_v04_analysis.md").write_text("\n".join(md),encoding="utf-8")
    def sha256(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    try:commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    except Exception:commit="unavailable"
    manifest={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"code_commit_at_analysis":commit,"working_tree_changes_at_analysis":True,"task_version":"0.4","profile_version":"profile-0.4","prompt_version":"S2-prompt-0.3","n_episodes":len(rows),"n_templates":len({template(r['task_id']) for r in rows}),"models":models,"model_cli_versions":sorted({r.get("codex_cli_version","unknown") for r in rows}),"conditions":["R0","R1","R2"],"reps":1,"seed":20261024,"analysis_script":"analyze_study2_v04.py","primary_outcomes":["strict_first_information_step_valid","valid_path_recomputed","task_score_recomputed"],"secondary_resource_outcome":"sum(input_tokens, output_tokens) across calls in each episode; usage proxy, not billed-dollar cost","cluster_bootstrap_draws":20000,"signflip_monte_carlo_draws":50000,"multiple_testing":"Holm across 6 fixed-model-average primary contrasts","no_reward_weight_sensitivity_scan":True,"sha256_task_blueprints_v0_4":sha256(ROOT/"task_blueprints_v0.4.jsonl"),"sha256_analysis_script":sha256(ROOT/"analyze_study2_v04.py"),"sha256_protocol":sha256(ROOT/"confirmatory_extension_protocol_v0.2.md"),"sha256_raw_runs":sha256(RUNS),"sha256_raw_events":sha256(ROOT/"events.jsonl"),"sha256_trace_recomputed_metrics":sha256(DER/"run_level_metrics_all.jsonl")}
    (DER/"study2_v04_analysis_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(f"Analyzed {len(rows)} v0.4 episodes across {len(tasks)} task variants; wrote contrast tables, report and SVG figures.")

def _group(rows,key):
    out=defaultdict(list)
    for r in rows:out[key(r)].append(r)
    return out
from collections import Counter
if __name__=="__main__":main()
