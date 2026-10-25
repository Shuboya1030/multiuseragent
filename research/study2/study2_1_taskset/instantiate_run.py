#!/usr/bin/env python3
"""Create run-specific visible candidates while permuting role identity/order.

Writes the model-visible task and candidate profiles plus a separate hidden
alias map for scoring. Keep identity_mapping.json out of the agent context.
"""
import argparse
import json
import random
import re
from pathlib import Path

NAMES=["Avery Chen","Jordan Lee","Taylor Wu","Morgan Patel","Riley Park","Casey Lin","Quinn Zhao","Jamie Rivera","Skyler Kim","Drew Morgan","Robin Shah","Cameron Yu","Emery Brooks","Sasha Nguyen","Reese Wang","Alex Rivera","Kai Sullivan","Rowan Diaz","Samira Cole","Devon Li"]
GENERIC_TITLES=["Project Team Member","Program Associate","Operations Associate","Business Associate"]

def instantiate(task_dir, output_dir, run_id, seed, profile_condition, alignment="aligned"):
    rng=random.Random(seed)
    task_dir=Path(task_dir).resolve(); out=Path(output_dir).resolve(); out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((task_dir/"metadata.json").read_text(encoding="utf-8"))
    scenarios=json.loads((task_dir/"scenarios.json").read_text(encoding="utf-8"))
    if meta["help_need_class"]=="must_ask":
        if alignment not in {"aligned", "separated"}:
            raise ValueError("must-ask tasks require aligned or separated alignment")
        canonical=scenarios["variants"][alignment]
        profile_source={k:v["public_profile"] for k,v in canonical.items()}
    else:
        alignment = "not_applicable"
        canonical=scenarios["candidates"]
        profile_source={k:v["public_profile"] for k,v in canonical.items()}
    ids=list(canonical)
    aliases=[f"C{i+1}" for i in range(len(ids))]
    shuffled_ids=ids[:]; rng.shuffle(shuffled_ids)
    alias_for={person:aliases[i] for i,person in enumerate(shuffled_ids)}
    order=aliases[:]; rng.shuffle(order)
    names=rng.sample(NAMES,len(ids)); rng.shuffle(names)
    titles=[GENERIC_TITLES[i%len(GENERIC_TITLES)] for i in range(len(ids))]; rng.shuffle(titles)
    name_title={alias:(names[i],titles[i]) for i,alias in enumerate(aliases)}
    visible=[]
    for alias in order:
        person=next(k for k,v in alias_for.items() if v==alias)
        name,title=name_title[alias]
        base=f"{name} — {title}"
        profile=base if profile_condition=="R0" else base+". "+profile_source[person].replace(person,name)
        visible.append({"candidate_id":alias,"name":name,"job_title":title,"profile":profile})
    task=(task_dir/"task.md").read_text(encoding="utf-8")
    task=re.sub(r"Available colleague IDs: [^.]*(\.)", "Available colleague IDs: "+", ".join(order)+r"\1", task)
    (out/"task.md").write_text(task,encoding="utf-8")
    (out/"candidate_profiles.json").write_text(json.dumps(visible,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    private={"run_id":run_id,"task_id":meta["task_id"],"seed":seed,"profile_condition":profile_condition,"alignment":alignment,"alias_to_canonical":{alias_for[k]:k for k in ids},"canonical_to_alias":alias_for}
    (out/"identity_mapping.json").write_text(json.dumps(private,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    manifest={k:v for k,v in private.items() if k not in {"alias_to_canonical","canonical_to_alias"}}
    manifest["candidate_order"]=order
    (out/"run_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"manifest":manifest,"profiles":visible,"private_mapping":private,"task_file":out/"task.md"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--task-dir",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--run-id",required=True)
    p.add_argument("--seed",required=True,type=int)
    p.add_argument("--profile-condition",choices=["R0","R1"],required=True)
    p.add_argument("--alignment",choices=["aligned","separated","not_applicable"],default="not_applicable")
    a=p.parse_args()
    instantiate(a.task_dir,a.output_dir,a.run_id,a.seed,a.profile_condition,a.alignment)

if __name__=="__main__": main()
