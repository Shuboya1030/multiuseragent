import ast
from dataclasses import asdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo))
from research.study4.v2.contracts import fingerprint
from research.study4.v2.phase0 import (
    build_request, load_case, reference_person, restore_public_state, task_ids, verify_inherited)
from research.study4.v2.phase0_admission import runtime_binding
from research.study4.v2.reference_completion import contracts, VERSION, ReferenceUncertain

if len(sys.argv) != 3:
    raise SystemExit("Usage: audit_reference_reuse.py ACTUAL_ROOT NEW_OUTPUT_JSON")
root = Path(sys.argv[1]).resolve()
def read(path):
    return json.loads(path.read_text(encoding="utf-8"))
plan = read(root / "FROZEN_PLAN.json")
prior_audit = read(repo / "research/study4/v2/reports/REFERENCE_CONTRACT_AUDIT_20261112.json")
assert verify_inherited(plan["history"]) == plan["inherited"]
current = runtime_binding()
assert {k: v for k, v in plan["runtime"].items() if k != "phase0_sources"} == {
    k: v for k, v in current.items() if k != "phase0_sources"}
def functions(text):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(text).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
old = subprocess.check_output(
    ["git", "show", plan["code_commit"] + ":research/study4/v2/phase0.py"], text=True, encoding="utf-8")
new = (repo / "research/study4/v2/phase0.py").read_text(encoding="utf-8")
old_functions, new_functions = functions(old), functions(new)
assert {k: v for k, v in old_functions.items() if k != "reference_released"} == {
    k: v for k, v in new_functions.items() if k != "reference_released"}
def public_module(text):
    module = ast.parse(text)
    module.body = [n for n in module.body if not (
        isinstance(n, ast.FunctionDef) and n.name == "reference_released")]
    return ast.dump(module, include_attributes=False)
assert public_module(old) == public_module(new)
assert plan["runtime"]["phase0_sources"]["phase0_analysis.py"] == current[
    "phase0_sources"]["phase0_analysis.py"]

journal = [json.loads(line) for line in (root / "events.jsonl").read_text(encoding="utf-8").splitlines()]
by_episode = {}
for entry in journal:
    if entry["kind"] == "model_request":
        by_episode.setdefault(entry["episode_id"], []).append(entry)

rows = []
for path in sorted(root.glob("slot-*.json")):
    record = read(path)
    slot = record["slot"]
    requests = by_episode[slot["episode_id"]]
    equivalent, reason, decisions = True, None, []
    previous_operation = None
    for entry in requests:
        request = entry["request"]
        operation = entry["operation"]
        if operation == "npc":
            rebuilt = build_request("npc", dialogue=request["input"])
        else:
            payload = json.loads(request["input"][-1]["content"])
            history = request["input"][1:-1]
            state = restore_public_state(payload["state"], history)
            rebuilt = build_request(payload["mode"], state, person=payload["person_id"], history=history)
            if slot["arm"] in "BD" and not (
                    operation == "ordinary" and previous_operation == "npc"):
                try:
                    person = reference_person(load_case(slot["task_id"]), SimpleNamespace(history=state["history"]))
                    old_person = payload["person_id"] if payload["mode"] == "question" else None
                    match = person == old_person
                    decision = {"operation": operation, "index": entry["index"],
                                "same_when_whom": match, "old_person": old_person, "new_person": person}
                    decisions.append(decision)
                    if not match:
                        equivalent, reason = False, "first_changed_when_whom_decision"
                except ReferenceUncertain:
                    equivalent, reason = False, "unresolved_release_not_safe_to_equate"
                    decisions.append({"operation": operation, "index": entry["index"],
                                      "same_when_whom": None, "release_requires_review": True})
        if fingerprint(rebuilt) != entry["request_sha256"]:
            equivalent, reason = False, "public_or_NPC_request_changed"
        previous_operation = operation
        if not equivalent:
            break
    rows.append({
        "slot": slot, "candidate": equivalent, "reason_if_not": reason,
        "actual_record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "all_recorded_requests_checked": equivalent,
        "request_count": len(requests), "reference_decisions": decisions,
        "shared_executor_NPC_tools_public_input_scorer_terminal_code_unchanged": True,
        "not_selected_by_score": True,
    })

compiled = []
for tid in task_ids():
    case = load_case(tid)
    specs = contracts(case)
    hidden = {h["id"]: h for h in case.blueprint["hidden_information"]}
    compiled.append({
        "task_id": tid, "blueprint_sha256": fingerprint(case.blueprint),
        "nodes": [{"contract": asdict(specs[n["id"]]), "source_node": n,
                   "source_records": [{"id": hidden[h]["id"],
                                       "fact_fields": list(hidden[h]["facts"]),
                                       "required_context": hidden[h]["required_context"],
                                       "release_rule": hidden[h]["release_rule"]}
                                      for h in n["information_ids"]]}
                  for n in case.blueprint["gold_dag"]["nodes"]],
    })
retained = [r for r in rows if r["candidate"]]
remaining = [s for s in plan["slots"] if s["slot"] not in {r["slot"]["slot"] for r in retained}]
complete_cost = Decimal(prior_audit["budget"]["new_settled_USD_upper"])
import sqlite3
db = sqlite3.connect("file:" + str(root / (plan["run_id"] + ".sqlite3")) + "?mode=ro", uri=True)
partial_cost = sum((Decimal(row[0]) for row in db.execute(
    "select charged from calls where episode=?", (plan["slots"][52]["episode_id"],))), Decimal(0))
complete_cost -= partial_cost
observed_mean = complete_cost / 52
known_bad = Decimal("4.957084275")
nonpathological_mean = (complete_cost - known_bad) / 51
result = {
    "schema": VERSION + "-offline-retention-1", "frozen_actual_source": plan["code_commit"],
    "current_public_protocol_label_unchanged_because_public_schema_unchanged": True,
    "new_private_reference_version": VERSION, "paid_recovery_disabled": True,
    "reference_source_sha256_LF": hashlib.sha256(
        (repo / "research/study4/v2/reference_completion.py").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
    "shared_phase0_functions_AST_identical_except_reference_released": True,
    "shared_phase0_module_constants_imports_AST_identical_except_reference_released": True,
    "all9historical_roots_unchanged": True,
    "original_run_receipt_still_same_sha256": hashlib.sha256(
        (root / "FINAL_RECEIPT.json").read_bytes()).hexdigest() == prior_audit["pause"]["receipt_sha256"],
    "source_rule_coverage": {"tasks": len(compiled), "nodes": sum(len(t["nodes"]) for t in compiled)},
    "contracts": compiled, "complete_actual_episodes_checked": len(rows),
    "reusable_candidates": len(retained), "diagnostic_only_complete_episodes": len(rows) - len(retained),
    "candidate_counts_by_arm": {a: sum(r["slot"]["arm"] == a for r in retained) for a in "ABCD"},
    "rows": rows, "remaining_fresh_slots": len(remaining), "remaining_manifest": remaining,
    "partial52_excluded_even_though_all6calls_settled": True,
    "candidate_is_offline_equivalence_not_new_execution_or_paid_authority": True,
    "candidate_NL_reward_reviews_still_required_for_final_statistics": True,
    "budget": prior_audit["budget"],
    "cost_scenarios_not_guarantees": {
        "actual52complete_cost_USD_upper": str(complete_cost),
        "actual_partial_cost_USD_upper": str(partial_cost),
        "remaining_at_all52observed_mean_USD_upper": str(observed_mean * len(remaining)),
        "remaining_at51excluding_proven_ledger_loop_USD_upper": str(nonpathological_mean * len(remaining)),
        "excluded_loop_not_evidence_future_loops_impossible": True,
        "per_call_reservation_USD": ".858000",
        "current_remaining_USD": prior_audit["budget"]["remaining_USD"],
        "maximum_64_action_tails_not_guaranteed_to_fit": True,
    },
}
assert result["source_rule_coverage"]["tasks"] == 60
out = Path(sys.argv[2]).resolve()
with out.open("x", encoding="utf-8") as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps({k: result[k] for k in [
    "source_rule_coverage", "reusable_candidates", "diagnostic_only_complete_episodes",
    "candidate_counts_by_arm", "remaining_fresh_slots", "cost_scenarios_not_guarantees"]}))
