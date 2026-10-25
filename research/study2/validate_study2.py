"""Rule-based quality audit for Study 2 task profiles, simulator, and stored traces."""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import run_study2 as sim

ROOT = Path(__file__).resolve().parent
DERIVED = ROOT / "derived"
V04_TASKS = ROOT / "task_blueprints_v0.4.jsonl"
TESTS = ROOT / "evaluator_tests.jsonl"


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def compare_saved_run(run, events, task):
    info_id = task["gold_admissible_recipients_by_step"]["information"][0]
    auth_id = task["gold_admissible_recipients_by_step"]["approval"][0]
    people = {p["person_id"]: p for p in task["candidates"]}
    known = False
    granted_by = None
    answer = {}
    seen = set()
    asks = [0, 0, 0]
    repeats = unhelpful = unauthorized = premature = knowledge_miss = 0
    first_ask = None
    first_step_valid = False
    first_purpose_match = False
    approvals_before_info = 0
    query_cost = 0.0
    for event in sorted(events, key=lambda x: x.get("turn", -1)):
        etype = event.get("type")
        if etype == "parse_error":
            unhelpful += 1
            continue
        if etype == "submit":
            answer = event.get("answer", {})
            continue
        if etype != "ask":
            continue
        target, purpose = event.get("target"), event.get("purpose")
        asks[0] += 1
        asks[1 if purpose == "information" else 2 if purpose == "approval" else 0] += 1
        query_cost += float(task.get("cost_per_query", 1))
        if first_ask is None:
            first_ask = event
            first_step_valid = purpose == "information" and target == info_id
            first_purpose_match = (purpose == "information" and target == info_id) or (purpose == "approval" and target == auth_id)
        if purpose == "approval" and not known:
            premature += 1
            approvals_before_info += 1
        if target == info_id and purpose == "information":
            known = True
        violation = bool(event.get("auth_violation"))
        unauthorized += int(violation)
        key = (target, purpose)
        repeated = key in seen
        repeats += int(repeated)
        seen.add(key)
        useful = bool(event.get("useful"))
        if purpose == "information" and not useful:
            knowledge_miss += 1
        if (not useful and not violation) or repeated:
            unhelpful += 1
        if event.get("approval_granted"):
            granted_by = target

    fact = task["required_information"][0]
    fact_ok = sim.norm(fact["value"]) in sim.norm(answer.get(fact["field"], ""))
    approval_ok = bool(granted_by and answer.get("approved_by") == granted_by == auth_id)
    task_score = (int(fact_ok) + int(approval_ok)) / 2
    valid_path = bool(fact_ok and approval_ok and known)
    reward = task_score - float(run["lambda"]) * query_cost - float(run["mu"]) * unauthorized - float(run["nu"]) * unhelpful
    derived = {
        "N_asks": asks[0], "N_information_asks": asks[1], "N_approval_asks": asks[2],
        "N_knowledge_miss": knowledge_miss, "N_auth_recomputed": unauthorized,
        "N_premature_approval": premature, "N_repeat_requests": repeats,
        "N_unhelpful_recomputed": unhelpful, "total_query_cost_recomputed": query_cost,
        "first_ask_turn": first_ask.get("turn") if first_ask else None,
        "first_action_was_ask": bool(first_ask and first_ask.get("turn") == 0),
        "strict_first_information_step_valid": first_step_valid,
        "first_target_matches_request_purpose": first_purpose_match,
        "approval_before_information_count": approvals_before_info,
        "fact_correct_recomputed": fact_ok, "approval_correct_recomputed": approval_ok,
        "valid_path_recomputed": valid_path, "task_score_recomputed": task_score,
        "reward_recomputed": reward,
    }
    mismatch = []
    checks = {
        "N_auth": unauthorized,
        "N_waste": unhelpful,
        "total_cost": query_cost,
        "fact_correct": fact_ok,
        "approval_correct": approval_ok,
        "valid_path": valid_path,
        "task_score_T": task_score,
        "reward_R": reward,
    }
    for key, value in checks.items():
        saved = run.get(key)
        if isinstance(value, (float, int)) and not isinstance(value, bool):
            if saved is None or not math.isclose(float(saved), float(value), abs_tol=1e-8):
                mismatch.append({"field": key, "saved": saved, "recomputed": value})
        elif saved != value:
            mismatch.append({"field": key, "saved": saved, "recomputed": value})
    return derived, mismatch


def test_profiles_and_tasks(tasks):
    issues = []
    by_template = defaultdict(dict)
    for task in tasks:
        tid = task["task_id"].rsplit("_", 1)[0]
        by_template[tid][task["alignment"]] = task
        if len(task["candidates"]) != 4:
            issues.append({"task_id": task["task_id"], "issue": "candidate_count_not_four"})
        ids = {p["person_id"] for p in task["candidates"]}
        info = task["gold_admissible_recipients_by_step"]["information"][0]
        auth = task["gold_admissible_recipients_by_step"]["approval"][0]
        if info not in ids or auth not in ids:
            issues.append({"task_id": task["task_id"], "issue": "gold_recipient_missing"})
        if task["alignment"] == "aligned" and info != auth:
            issues.append({"task_id": task["task_id"], "issue": "aligned_gold_not_same_person"})
        if task["alignment"] == "separated" and info == auth:
            issues.append({"task_id": task["task_id"], "issue": "separated_gold_same_person"})
        fact_value = task["required_information"][0]["value"].casefold()
        for p in task["candidates"]:
            required_public = [p["organization_domain"], p["domain_expertise"], p["familiarity"], p["decision_authority"], p["availability"]]
            if any(str(value).casefold() not in p["natural_language"].casefold() for value in required_public):
                issues.append({"task_id": task["task_id"], "person_id": p["person_id"], "issue": "R1_profile_omits_public_fact"})
            expected_structured = {
                "person": p["person_id"], "organization_domain": p["organization_domain"],
                "domain_expertise": p["domain_expertise"], "familiarity": p["familiarity"],
                "decision_authority": p["decision_authority"], "availability": p["availability"],
            }
            if p["structured"] != expected_structured:
                issues.append({"task_id": task["task_id"], "person_id": p["person_id"], "issue": "R2_profile_fact_mismatch"})
            if fact_value and fact_value in p["natural_language"].casefold():
                issues.append({"task_id": task["task_id"], "person_id": p["person_id"], "issue": "answer_literal_leaked_in_R1"})
            if fact_value and fact_value in json.dumps(p["structured"], ensure_ascii=False).casefold():
                issues.append({"task_id": task["task_id"], "person_id": p["person_id"], "issue": "answer_literal_leaked_in_R2"})
    for tid, al in by_template.items():
        if set(al) != {"aligned", "separated"}:
            issues.append({"template_id": tid, "issue": "alignment_pair_missing"})
    return issues


def run_evaluator_cases(tasks):
    index = {t["task_id"]: t for t in tasks}
    results = []
    for case in read_jsonl(TESTS):
        task = index[case["task_id"]]
        role = case["recipient_role"]
        if role == "information_holder":
            person_id = task["gold_admissible_recipients_by_step"]["information"][0]
        elif role == "approver":
            person_id = task["gold_admissible_recipients_by_step"]["approval"][0]
        elif role == "partial_knowledge":
            person_id = next(p["person_id"] for p in task["candidates"] if p["partial_knowledge"])
        else:
            info = task["gold_admissible_recipients_by_step"]["information"][0]
            auth = task["gold_admissible_recipients_by_step"]["approval"][0]
            person_id = next(p["person_id"] for p in task["candidates"] if p["person_id"] not in {info, auth} and not p["partial_knowledge"])
        person = next(p for p in task["candidates"] if p["person_id"] == person_id)
        result = sim.reply(task, person, case["purpose"], case["message"], task["gold_admissible_recipients_by_step"]["information"][0], case["known_before"])
        observed = {"reply": result[0], "useful": result[1], "violation": result[2], "granted": result[3]}
        expected = {"reply": case["expected_reply"], "useful": case["expected_useful"], "violation": case["expected_violation"], "granted": case["expected_granted"]}
        results.append({"case_id": case["case_id"], "passed": observed == expected, "expected": expected, "observed": observed})
    return results


def main():
    if not V04_TASKS.exists():
        raise SystemExit("Generate task_blueprints_v0.4.jsonl first.")
    tasks = read_jsonl(V04_TASKS)
    rows = read_jsonl(ROOT / "runs.jsonl")
    events = read_jsonl(ROOT / "events.jsonl")
    event_by_run = defaultdict(list)
    for event in events:
        if event.get("run_id"):
            event_by_run[event["run_id"]].append(event)
    tasks_by_key = {(t["task_id"], t["task_version"]): t for t in read_jsonl(ROOT / "task_blueprints.jsonl") + tasks}

    profile_issues = test_profiles_and_tasks(tasks)
    evaluator_results = run_evaluator_cases(tasks)
    mismatches = []
    missing_events = []
    derived_rows = []
    for row in rows:
        key = (row["task_id"], row.get("task_version"))
        task = tasks_by_key.get(key)
        if task is None:
            continue
        ev = event_by_run.get(row["run_id"], [])
        if not ev:
            missing_events.append(row["run_id"])
            continue
        derived, diff = compare_saved_run(row, ev, task)
        derived_rows.append({**row, **derived})
        if diff:
            mismatches.append({"run_id": row["run_id"], "task_id": row["task_id"], "model_id": row["model_id"], "profile_condition": row["profile_condition"], "mismatches": diff})

    confirm = [r for r in rows if r.get("split") == "confirmatory"]
    historical_confirm = [r for r in confirm if r.get("task_version") != "0.4"]
    v04_confirm = [r for r in confirm if r.get("task_version") == "0.4"]
    keys = Counter((r["task_id"], r.get("task_version"), r.get("profile_version", "profile-unknown"), r.get("prompt_version"), r["model_id"], r["profile_condition"], r["rep"]) for r in historical_confirm)
    dupes = {str(k): n for k, n in keys.items() if n > 1}
    old_task_rows = read_jsonl(ROOT / "task_blueprints.jsonl")
    old_r2_missing_domain = sum("organization_domain" not in p.get("structured", {}) for t in old_task_rows for p in t["candidates"])
    evaluator_failures = [r for r in evaluator_results if not r["passed"]]

    DERIVED.mkdir(exist_ok=True)
    write_jsonl(DERIVED / "run_level_metrics_all.jsonl", derived_rows)
    write_jsonl(DERIVED / "evaluator_test_results.jsonl", evaluator_results)
    summary = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "v0_4_blueprints": len(tasks), "v0_4_templates": len({t["task_id"].rsplit("_", 1)[0] for t in tasks}),
        "v0_4_profile_semantic_issues": profile_issues,
        "evaluator_cases": len(evaluator_results), "evaluator_failures": evaluator_failures,
        "stored_runs_checked": len(derived_rows), "stored_runs_missing_events": len(missing_events),
        "saved_vs_recomputed_mismatches": mismatches,
        "historical_confirmatory_raw_rows": len(historical_confirm), "historical_confirmatory_unique_cells": len(keys),
        "confirmatory_duplicate_cells": len(dupes), "confirmatory_extra_rows": sum(keys.values()) - len(keys),
        "v0_4_confirmatory_raw_rows_including_interrupted_pilot": len(v04_confirm),
        "old_profile_structured_missing_domain_entries": old_r2_missing_domain,
    }
    (DERIVED / "quality_audit.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = [
        "# Study 2 quality audit",
        "",
        f"- v0.4 task variants/templates: {len(tasks)} / {len({t['task_id'].rsplit('_',1)[0] for t in tasks})}.",
        f"- v0.4 profile/gold leakage and R1/R2 semantic checks flagged {len(profile_issues)} issues.",
        f"- Rule evaluator boundary cases: {len(evaluator_results)}; failures: {len(evaluator_failures)}.",
        f"- Existing stored runs with reconstructable trace: {len(derived_rows)}; missing trace: {len(missing_events)}.",
        f"- Saved-vs-recomputed scoring mismatches: {len(mismatches)}.",
        f"- Historical confirmatory log: {len(historical_confirm)} rows, {len(keys)} unique planned cells, {len(dupes)} duplicate cells, {sum(keys.values())-len(keys)} extra rows retained.",
        f"- v0.4 confirmatory-split records (including interrupted exploratory batch): {len(v04_confirm)}; these are separately versioned and not counted as historical duplicates.",
        f"- Historical structured profiles missing an organization-domain field: {old_r2_missing_domain} candidate profiles. This means the historical R2-vs-R1 contrast changes both format and one role fact; that contrast must not be interpreted as a clean format-only effect.",
        "",
        "## v0.4 profile audit findings",
    ]
    report += [f"- {x['task_id']} / {x.get('person_id','')}: {x['issue']}" for x in profile_issues] or ["- No automated profile/gold leakage or semantic-field mismatches detected."]
    report += ["", "## Evaluator boundary checks", ""]
    report += [f"- {'PASS' if x['passed'] else 'FAIL'} {x['case_id']}: observed {x['observed']}" for x in evaluator_results]
    report += ["", "## Trace score recomputation", ""]
    report += ["- All saved terminal fields matched replay recomputation." if not mismatches else f"- {len(mismatches)} runs have mismatches; inspect `quality_audit.json` before interpreting affected fields."]
    (DERIVED / "quality_audit.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k,v in summary.items() if k not in {"checked_at_utc"}}, ensure_ascii=False, indent=2))
    if evaluator_failures or missing_events or mismatches or profile_issues:
        print("QUALITY_AUDIT_HAS_FINDINGS; inspect derived/quality_audit.md and .json")
    else:
        print("QUALITY_AUDIT_PASS")


if __name__ == "__main__":
    main()
