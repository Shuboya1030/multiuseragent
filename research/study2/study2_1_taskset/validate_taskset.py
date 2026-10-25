#!/usr/bin/env python3
"""Structural validation for the generated Study 2.1 task bundles."""
import collections
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "tasks"
required_files = {"task.md", "metadata.json", "gold_policy.json", "scenarios.json", "evaluator_spec.json", "evaluator.py"}
sys.path.insert(0, str(ROOT))
from evaluate_episode import evaluate_task
from instantiate_run import instantiate
errors = []
rows = []
fixture_cases = 0
required_meta = {"schema_version","task_id","template_id","task_version","split","created_at","author","source","license_status","help_need_class","domain","workflow_type","profile_conditions","candidate_ids","environment","evaluator_version","checkpoint_ids","artifact_schema","attempt_abstention","quality_review","known_limitations","trace_schema_file","run_record_schema_file"}
for d in sorted(x for x in TASKS.iterdir() if x.is_dir()):
    missing = required_files - {f.name for f in d.iterdir()}
    if missing:
        errors.append(f"{d.name}: missing {sorted(missing)}")
        continue
    try:
        meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
        gold = json.loads((d / "gold_policy.json").read_text(encoding="utf-8"))
        scenario = json.loads((d / "scenarios.json").read_text(encoding="utf-8"))
        spec = json.loads((d / "evaluator_spec.json").read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"{d.name}: invalid JSON: {e}")
        continue
    prompt = (d / "task.md").read_text(encoding="utf-8").lower()
    if meta.get("task_id") != d.name or gold.get("task_id") != d.name:
        errors.append(f"{d.name}: task ID mismatch")
    if meta.get("help_need_class") != gold.get("help_need_class"):
        errors.append(f"{d.name}: class mismatch between metadata and gold")
    if required_meta - meta.keys():
        errors.append(f"{d.name}: missing task metadata {sorted(required_meta-meta.keys())}")
    if meta.get("profile_rendering", {}).get("R0") != "synthetic name + generic job title" or "same name/title" not in meta.get("profile_rendering", {}).get("R1", ""):
        errors.append(f"{d.name}: R0/R1 renderer metadata does not follow the approved definitions")
    if meta.get("audit_status", "").find("confirmatory") >= 0:
        errors.append(f"{d.name}: incorrectly marked confirmatory before review/pilot")
    klass = meta.get("help_need_class")
    if klass in prompt:
        errors.append(f"{d.name}: hidden class label leaked into task prompt")
    if klass == "must_ask":
        if not gold.get("required_information") or not gold.get("required_authority"):
            errors.append(f"{d.name}: must-ask gold lacks required fact or authority")
        if "approved_by` field must be one string" not in prompt or "visible candidate id" not in prompt:
            errors.append(f"{d.name}: task prompt does not define approved_by as one visible candidate ID string")
        if not gold.get("valid_paths_by_variant") or not gold.get("admissible_recipients_by_step"):
            errors.append(f"{d.name}: must-ask gold lacks recipient/path definitions")
        if len(scenario.get("variants", {})) != 2:
            errors.append(f"{d.name}: expected aligned/separated NPC variants")
        for variant, expected in gold.get("expected_answer_by_variant", {}).items():
            if not isinstance(expected.get("approved_by"), str):
                errors.append(f"{d.name}/{variant}: gold approved_by must be one candidate ID string")
            for key, value in expected.items():
                if key == "approved_by":
                    continue  # candidate IDs are intentionally visible to the agent
                if isinstance(value, str) and value.casefold() in prompt:
                    errors.append(f"{d.name}: hidden expected value leaks into task prompt")
    elif klass == "optional_benefit":
        if not gold.get("no_contact_outcome", {}).get("baseline_success_possible"):
            errors.append(f"{d.name}: optional task has no valid no-contact baseline")
        if not gold.get("optional_information") or not gold.get("effective_contact_outcome"):
            errors.append(f"{d.name}: optional task lacks optional information or benefit rule")
        hidden = gold["optional_information"]["optional_fact"]
        if hidden.casefold() in prompt:
            errors.append(f"{d.name}: optional private fact leaks into task prompt")
        if not gold.get("checkpoint_ids") or not spec.get("optional_bonus", {}).get("required_concept_terms"):
            errors.append(f"{d.name}: optional task lacks objective quality scoring terms")
    elif klass == "no_help":
        if not gold.get("expected_output") or gold.get("admissible_help_steps") != []:
            errors.append(f"{d.name}: no-help task lacks deterministic answer or has a help step")
    else:
        errors.append(f"{d.name}: unknown class {klass}")
    rows.append(meta)

counts = collections.Counter(x.get("help_need_class") for x in rows)
if len(rows) != 60:
    errors.append(f"expected 60 valid task packages, got {len(rows)}")
if counts != {"must_ask": 20, "optional_benefit": 20, "no_help": 20}:
    errors.append(f"unexpected class counts: {dict(counts)}")
if len({x.get("template_id") for x in rows}) != len(rows):
    errors.append("template_id values are not unique")

# Exercise evaluator positive and negative branches for every template.
try:
    with tempfile.TemporaryDirectory(prefix=".study21-eval-check-", dir=ROOT) as td:
        td = Path(td)
        (td/"trace.jsonl").write_text("",encoding="utf-8")
        for d in sorted(x for x in TASKS.iterdir() if x.is_dir()):
            gold=json.loads((d/"gold_policy.json").read_text(encoding="utf-8"))
            klass=gold["help_need_class"]
            if klass=="must_ask":
                for variant, expected in gold["expected_answer_by_variant"].items():
                    recips=gold["admissible_recipients_by_step"][variant]
                    ih=recips["information"][0]; ap=recips["approval"][0]
                    fact=gold["required_information"][0]["value"]
                    trace=[
                        {"run_id":"fixture","event_id":1,"actor":"agent","event_type":"ask","recipient_id":ih,"purpose":"information","content":"Please provide the verified task fact."},
                        {"run_id":"fixture","event_id":2,"actor":"npc","event_type":"reply","recipient_id":ih,"content":fact},
                        {"run_id":"fixture","event_id":3,"actor":"agent","event_type":"ask","recipient_id":ap,"purpose":"approval","content":"Please approve this request."},
                        {"run_id":"fixture","event_id":4,"actor":"npc","event_type":"reply","recipient_id":ap,"authorized":True,"content":"Approved."}]
                    (td/"answer.json").write_text(json.dumps(expected),encoding="utf-8")
                    (td/"trace.jsonl").write_text("\n".join(json.dumps(x) for x in trace),encoding="utf-8")
                    res=evaluate_task(d,td/"answer.json",td/"trace.jsonl","fixture",variant)
                    fixture_cases += 1
                    if res.get("task_success") is not True: errors.append(f"{d.name}/{variant}: positive evaluator fixture failed")
                    legacy_answer = dict(expected)
                    legacy_answer["approved_by"] = [expected["approved_by"]]
                    (td/"answer.json").write_text(json.dumps(legacy_answer),encoding="utf-8")
                    legacy_res=evaluate_task(d,td/"answer.json",td/"trace.jsonl","fixture",variant)
                    fixture_cases += 1
                    if legacy_res.get("task_success") is not True: errors.append(f"{d.name}/{variant}: singleton-list approved_by compatibility fixture failed")
                (td/"trace.jsonl").write_text("",encoding="utf-8")
                res=evaluate_task(d,td/"answer.json",td/"trace.jsonl","fixture","aligned")
                fixture_cases += 1
                if res.get("underhelp") is not True: errors.append(f"{d.name}: no-contact under-help fixture failed")
            elif klass=="optional_benefit":
                terms=gold["effective_contact_outcome"]["required_concept_terms"]
                answer={"baseline_summary":gold["visible_information"],"recommendation":" ".join(terms),"quality_notes":[" ".join(terms)]}
                (td/"answer.json").write_text(json.dumps(answer),encoding="utf-8")
                (td/"trace.jsonl").write_text("",encoding="utf-8")
                noask=evaluate_task(d,td/"answer.json",td/"trace.jsonl","fixture")
                fixture_cases += 1
                if noask.get("task_success") is not True or noask.get("optional_quality_points")!=0: errors.append(f"{d.name}: no-contact optional fixture failed")
                trace=[{"run_id":"fixture","event_id":1,"actor":"agent","event_type":"ask","recipient_id":"P1","purpose":"optional_advice","content":"What is your recommendation?"},{"run_id":"fixture","event_id":2,"actor":"npc","event_type":"reply","recipient_id":"P1","content":gold["optional_information"]["optional_fact"]}]
                (td/"trace.jsonl").write_text("\n".join(json.dumps(x) for x in trace),encoding="utf-8")
                asked=evaluate_task(d,td/"answer.json",td/"trace.jsonl","fixture")
                fixture_cases += 1
                if asked.get("task_success") is not True or asked.get("optional_quality_points")!=1: errors.append(f"{d.name}: useful-contact optional fixture failed")
            else:
                (td/"answer.json").write_text(json.dumps(gold["expected_output"]),encoding="utf-8")
                (td/"trace.jsonl").write_text("",encoding="utf-8")
                noask=evaluate_task(d,td/"answer.json",td/"trace.jsonl","fixture")
                fixture_cases += 1
                if noask.get("task_success") is not True or noask.get("overhelp") is not False: errors.append(f"{d.name}: no-contact no-help fixture failed")
                trace=[{"run_id":"fixture","event_id":1,"actor":"agent","event_type":"ask","recipient_id":"P1","purpose":"question","content":"Can you help?"}]
                (td/"trace.jsonl").write_text(json.dumps(trace[0]),encoding="utf-8")
                asked=evaluate_task(d,td/"answer.json",td/"trace.jsonl","fixture")
                fixture_cases += 1
                if asked.get("task_success") is not True or asked.get("overhelp") is not True: errors.append(f"{d.name}: unnecessary-contact no-help fixture failed")

        # Verify run-randomized public aliases are mapped back only inside scoring.
        d=TASKS/"must-expense-reimbursement"; g=json.loads((d/"gold_policy.json").read_text(encoding="utf-8"))
        expected=g["expected_answer_by_variant"]["aligned"]
        recips=g["admissible_recipients_by_step"]["aligned"]
        ih=recips["information"][0]; ap=recips["approval"][0]; fact=g["required_information"][0]["value"]
        alias_for={"P1":"C3","P2":"C1","P3":"C4","P4":"C2"}
        alias_to={v:k for k,v in alias_for.items()}
        remapped={k:([alias_for[x] for x in v] if k=="approved_by" and isinstance(v,list) else alias_for[v] if k=="approved_by" and isinstance(v,str) else v) for k,v in expected.items()}
        (td/"answer.json").write_text(json.dumps(remapped),encoding="utf-8")
        events=[{"run_id":"fixture-map","event_id":1,"actor":"agent","event_type":"ask","recipient_id":alias_for[ih],"purpose":"information","content":"Please provide the fact."},{"run_id":"fixture-map","event_id":2,"actor":"npc","event_type":"reply","recipient_id":alias_for[ih],"content":fact},{"run_id":"fixture-map","event_id":3,"actor":"agent","event_type":"ask","recipient_id":alias_for[ap],"purpose":"approval","content":"Please approve this request."},{"run_id":"fixture-map","event_id":4,"actor":"npc","event_type":"reply","recipient_id":alias_for[ap],"authorized":True,"content":"Approved."}]
        (td/"trace.jsonl").write_text("\n".join(json.dumps(x) for x in events),encoding="utf-8")
        (td/"mapping.json").write_text(json.dumps({"alias_to_canonical":alias_to}),encoding="utf-8")
        res=evaluate_task(d,td/"answer.json",td/"trace.jsonl","fixture-map","aligned",td/"mapping.json")
        fixture_cases += 1
        if res.get("task_success") is not True: errors.append(f"run-specific alias mapping evaluator fixture failed: {res}")
        remapped_legacy=dict(remapped)
        remapped_legacy["approved_by"]=[remapped["approved_by"]]
        (td/"answer.json").write_text(json.dumps(remapped_legacy),encoding="utf-8")
        legacy_res=evaluate_task(d,td/"answer.json",td/"trace.jsonl","fixture-map","aligned",td/"mapping.json")
        fixture_cases += 1
        if legacy_res.get("task_success") is not True: errors.append(f"run-specific alias mapping singleton-list compatibility fixture failed: {legacy_res}")

        # R0/R1 are paired: same randomized synthetic name/title, with R1 adding general role context.
        r0=instantiate(TASKS/"must-expense-reimbursement",td/"r0", "profile-check-r0", 147, "R0", "separated")
        r1=instantiate(TASKS/"must-expense-reimbursement",td/"r1", "profile-check-r1", 147, "R1", "separated")
        by_id_r0={x["candidate_id"]:x for x in r0["profiles"]}; by_id_r1={x["candidate_id"]:x for x in r1["profiles"]}
        if set(by_id_r0)!=set(by_id_r1): errors.append("R0/R1 paired candidate IDs differ")
        for cid, x in by_id_r0.items():
            y=by_id_r1[cid]
            base=f"{x['name']} — {x['job_title']}"
            if x["profile"]!=base: errors.append(f"{cid}: R0 is not synthetic name + generic title")
            if y["name"]!=x["name"] or y["job_title"]!=x["job_title"] or not y["profile"].startswith(base+". "):
                errors.append(f"{cid}: R1 is not matched R0 plus role detail")
        mapping_signatures=set(); order_signatures=set()
        for seed in range(1,7):
            inst=instantiate(TASKS/"must-expense-reimbursement",td/f"shuffle-{seed}",f"shuffle-{seed}",seed,"R0","aligned")
            mapping_signatures.add(tuple(sorted(inst["private_mapping"]["canonical_to_alias"].items())))
            order_signatures.add(tuple(inst["manifest"]["candidate_order"]))
        if len(mapping_signatures)<2: errors.append("candidate-role-to-alias assignment did not vary across seeds")
        if len(order_signatures)<2: errors.append("candidate order did not vary across seeds")
except Exception as e:
    errors.append(f"evaluator fixture raised: {e}")

print(f"Validated package count: {len(rows)}")
print(f"Class counts: {dict(counts)}")
print(f"Evaluator fixture cases: {fixture_cases}")
print(f"Structural errors: {len(errors)}")
for error in errors:
    print(f"FAIL: {error}")
raise SystemExit(1 if errors else 0)
