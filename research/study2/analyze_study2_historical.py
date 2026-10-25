"""Reanalyze historical Study 2 confirmatory rows, using trace-reconstructed metrics."""
import csv,json,random
from collections import defaultdict,Counter
from pathlib import Path
from analyze_study2_v04 import mean,template,boot_interval,signflip
ROOT=Path(__file__).resolve().parent; DER=ROOT/"derived"

def read(path):return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def write(path,rows):
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    rows=[r for r in read(DER/"run_level_metrics_all.jsonl") if r.get("split")=="confirmatory" and r.get("task_version")!="0.4"]
    key=lambda r:(r["task_id"],r["model_id"],r["profile_condition"],r.get("rep",0))
    groups=defaultdict(list)
    for r in rows:groups[key(r)].append(r)
    first=[v[0] for v in groups.values()]
    metric_keys=["strict_first_information_step_valid","first_target_matches_request_purpose","valid_path_recomputed","task_score_recomputed","reward_recomputed","total_query_cost_recomputed","N_knowledge_miss","N_auth_recomputed","N_premature_approval","N_repeat_requests","N_unhelpful_recomputed"]
    # Contrast paired planned cells, once with first-appended records and once averaged over retained duplicate rows.
    results=[]
    for label,data in [("first_appended",{k:v[:1] for k,v in groups.items()}),("mean_all_retained_attempts",groups)]:
      cell={}
      for k,rs in data.items():cell[k]= {m:mean([float(bool(r[m])) if isinstance(r[m],bool) else float(r.get(m,0) or 0) for r in rs]) for m in metric_keys}
      for metric in metric_keys:
       for contrast,hi,lo in [("R1-R0","R1","R0"),("R2-R1","R2","R1")]:
        per_model=defaultdict(lambda:defaultdict(list))
        for (task,model,cond,rep),vals in cell.items():
          if cond==hi and (task,model,lo,rep) in cell:
             per_model[model][template(task)].append(vals[metric]-cell[(task,model,lo,rep)][metric])
        for model,clusters in per_model.items():
          vals={tid:mean(v) for tid,v in clusters.items()};lo_ci,hi_ci=boot_interval(vals,20261025+len(results))
          results.append({"analysis_set":label,"model":model,"outcome":metric,"contrast":contrast,"n_templates":len(vals),"mean_difference":mean(list(vals.values())),"ci_low":lo_ci,"ci_high":hi_ci,"signflip_p_mc":signflip(vals,20265000+len(results))})
    write(DER/"historical_confirmatory_contrasts.csv",results)
    # Explicit first-step metric disagreement with legacy stored field.
    disagreements=[r for r in first if bool(r["first_valid"])!=bool(r["strict_first_information_step_valid"])]
    report=["# Historical Study 2 confirmatory reanalysis","",f"- Historical raw confirmatory rows: {len(rows)}; unique planned cells: {len(groups)}; extra duplicate attempts retained: {sum(len(v)-1 for v in groups.values())}.","- `first_appended` is the historical planned-cell analysis; `mean_all_retained_attempts` checks whether all duplicate attempts change the estimate. Raw traces remain in the source files.","- Outcomes were recomputed from event traces. The first-information-step outcome requires an information request to an admissible knowledge holder; legacy first_valid may accept approval-first behavior.",f"- Legacy first_valid disagrees with strict first-step validity in {len(disagreements)} of {len(first)} first-appended cells.","- Historical R1/R2 contrasts are not format-only comparisons: v0.3 structured profiles omit organization-domain facts present in prose profiles. Do not use historical R2−R1 to claim a pure structured-format effect.","- Cluster bootstrap and Monte Carlo sign-flip summaries use 14 workflow-template clusters; uncertainty is coarse and p-values descriptive.","", "## Historical R1−R0 estimates (first appended record)",""]
    for r in results:
      if r["analysis_set"]=="first_appended" and r["contrast"]=="R1-R0" and r["model"] in {"gpt-6-luna","gpt-5.6-terra"}:
       report.append(f'- {r["model"]}, {r["outcome"]}: {r["mean_difference"]:+.3f} (95% cluster bootstrap CI {r["ci_low"]:+.3f} to {r["ci_high"]:+.3f}).')
    report += ["", "## Duplicate-cell sensitivity for reward R1−R0", ""]
    for model in sorted({r["model"] for r in results}):
      pair={(r["analysis_set"],r["outcome"],r["contrast"]):r for r in results if r["model"]==model}
      first_r=pair.get(("first_appended","reward_recomputed","R1-R0"),{}).get("mean_difference",float("nan"))
      all_r=pair.get(("mean_all_retained_attempts","reward_recomputed","R1-R0"),{}).get("mean_difference",float("nan"))
      report.append(f'- {model}: first appended {first_r:+.3f}; per-cell mean across every retained attempt {all_r:+.3f}.')
    report += ["", "Full estimates and duplicate sensitivity are in `historical_confirmatory_contrasts.csv`.",""]
    (DER/"historical_confirmatory_reanalysis.md").write_text("\n".join(report),encoding="utf-8")
    print(f"Historical rows={len(rows)}; unique planned cells={len(groups)}; extra duplicate rows={sum(len(v)-1 for v in groups.values())}; first_valid/strict disagreements={len(disagreements)}")
if __name__=="__main__":main()
