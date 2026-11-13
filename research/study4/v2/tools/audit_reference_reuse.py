import ast
from dataclasses import asdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo))
from research.study4.v2.contracts import fingerprint
from research.study4.v2.phase0 import (
    build_request, load_case, restore_public_state, task_ids, verify_inherited)
from research.study4.v2.phase0_admission import runtime_binding
from research.study4.v2.reference_completion import contracts, VERSION

if len(sys.argv) != 3:
    raise SystemExit("Usage: audit_reference_reuse.py ACTUAL_ROOT NEW_OUTPUT_JSON")
root = Path(sys.argv[1]).resolve()
def read(path):
    return json.loads(path.read_text(encoding="utf-8"))
plan = read(root / "FROZEN_PLAN.json")
prior_audit = read(repo / "research/study4/v2/reports/REFERENCE_CONTRACT_AUDIT_20261112.json")
historical_reuse_path = repo / "research/study4/v2/reports/REFERENCE_REPAIR_REUSE_20261112.json"
historical_reuse = read(historical_reuse_path)
assert verify_inherited(plan["history"]) == plan["inherited"]
current = runtime_binding()
assert {k: v for k, v in plan["runtime"].items() if k != "phase0_sources"} == {
    k: v for k, v in current.items() if k != "phase0_sources"}
def functions(text):
    return {n.name: ast.dump(normalize_episode(n), include_attributes=False) for n in ast.parse(text).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
def normalize_episode(node):
    if isinstance(node, ast.FunctionDef) and node.name == "episode" and node.args.kwonlyargs:
        assert [a.arg for a in node.args.kwonlyargs] == ["runtime"]
        assert ast.dump(node.args.kw_defaults[0]) == ast.dump(ast.Constant(None))
        assert ast.dump(node.body[0], include_attributes=False) == ast.dump(ast.parse(
            'if runtime is None:\n    runtime = Phase0Runtime(case, slot["episode_id"])').body[0],
            include_attributes=False)
        node.args.kwonlyargs, node.args.kw_defaults = [], []
        node.body[0] = node.body[0].body[0]
    return node
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
    module.body = [normalize_episode(n) for n in module.body]
    return ast.dump(module, include_attributes=False)
assert public_module(old) == public_module(new)
episode_ast = next(n for n in ast.parse(new).body if isinstance(n, ast.FunctionDef) and n.name == "episode")
reference_calls = [n for n in ast.walk(episode_ast) if isinstance(n, ast.Call) and
                   isinstance(n.func, ast.Name) and n.func.id == "reference_person"]
expected_guard = ast.parse(
    'reference_person(case, runtime) if slot["arm"] in {"B", "D"} else None', mode="eval").body
assert len(reference_calls) == 1 and any(
    ast.dump(n, include_attributes=False) == ast.dump(expected_guard, include_attributes=False)
    for n in ast.walk(episode_ast))
assert plan["runtime"]["phase0_sources"]["phase0_analysis.py"] == current[
    "phase0_sources"]["phase0_analysis.py"]

journal = [json.loads(line) for line in (root / "events.jsonl").read_text(encoding="utf-8").splitlines()]
by_episode = {}
for entry in journal:
    if entry["kind"] == "model_request":
        by_episode.setdefault(entry["episode_id"], []).append(entry)

rows = []
paths = sorted(root.glob("slot-*.json"))
assert len(paths) == 52
assert [read(p)["slot"] for p in paths] == plan["slots"][:52]
assert len({s["task_id"] for s in plan["slots"][:52]}) == 13
historical_rows = {r["slot"]["slot"]: r for r in historical_reuse["rows"]}
for path in paths:
    record = read(path)
    slot = record["slot"]
    record_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    assert record_sha == historical_rows[slot["slot"]]["actual_record_sha256"]
    retained_arm = slot["arm"] in {"A", "C"}
    requests = by_episode[slot["episode_id"]] if retained_arm else []
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
        assert fingerprint(rebuilt) == entry["request_sha256"], (
            "Entire predefined A/C cohort rejected: a shared request changed", slot, entry["index"])
    if retained_arm:
        assert record["complete"] is True and requests
        assert len(requests) == sum(record["model_calls"].values())
    rows.append({
        "slot": slot, "retain_in_formal_cohort": retained_arm,
        "reason": "entire_original_13task_AC_cohort" if retained_arm else "all_BD_fresh_without_filtering",
        "actual_record_sha256": record_sha,
        "all_recorded_requests_checked": retained_arm,
        "request_count_checked": len(requests), "BD_decisions_not_rescreened": True,
        "shared_executor_NPC_tools_public_input_scorer_terminal_code_unchanged": True,
        "not_selected_by_score_or_reply_equivalence": True,
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
retained = [r for r in rows if r["retain_in_formal_cohort"]]
assert len(retained) == 26 and all(sum(
    r["slot"]["arm"] == a for r in retained) == 13 for a in ("A", "C"))
remaining = [s for s in plan["slots"] if s["slot"] not in {r["slot"]["slot"] for r in retained}]
fresh_counts = {a: sum(s["arm"] == a for s in remaining) for a in "ABCD"}
assert len(remaining) == 214 and fresh_counts == {"A": 47, "B": 60, "C": 47, "D": 60}
complete_cost = Decimal(prior_audit["budget"]["new_settled_USD_upper"])
import sqlite3
db = sqlite3.connect("file:" + str(root / (plan["run_id"] + ".sqlite3")) + "?mode=ro", uri=True)
partial_cost = sum((Decimal(row[0]) for row in db.execute(
    "select charged from calls where episode=?", (plan["slots"][52]["episode_id"],))), Decimal(0))
complete_cost -= partial_cost
observed_mean = complete_cost / 52
known_bad = Decimal("4.957084275")
nonpathological_mean = (complete_cost - known_bad) / 51
cost_by_arm = {a: Decimal(0) for a in "ABCD"}
calls_by_arm = {a: 0 for a in "ABCD"}
for row in rows:
    call_rows = list(db.execute("select charged from calls where episode=?",
                               (row["slot"]["episode_id"],)))
    cost_by_arm[row["slot"]["arm"]] += sum((Decimal(r[0]) for r in call_rows), Decimal(0))
    calls_by_arm[row["slot"]["arm"]] += len(call_rows)
assert sum(cost_by_arm.values()) == complete_cost
stratified_cost = sum((cost_by_arm[a] / 13 * fresh_counts[a] for a in "ABCD"), Decimal(0))
stratified_calls = sum((Decimal(calls_by_arm[a]) / 13 * fresh_counts[a] for a in "ABCD"), Decimal(0))
tail_sensitivity_cost = sum((
    ((cost_by_arm[a] - known_bad) / 12 if a == "D" else cost_by_arm[a] / 13) * fresh_counts[a]
    for a in "ABCD"), Decimal(0))
assert hashlib.sha256((root / "FINAL_RECEIPT.json").read_bytes()).hexdigest() == prior_audit["pause"]["receipt_sha256"]
assert hashlib.sha256((root / "events.jsonl").read_bytes()).hexdigest() == prior_audit["pause"]["journal_sha256"]
assert (repo / "research/study4/v2/reports/REFERENCE_REPAIR_REUSE_20261112.json").read_bytes().replace(b"\r\n", b"\n") == subprocess.check_output(
    ["git", "show", "274c2426365244af80738cac0ce53b7e6a1172b6:research/study4/v2/reports/REFERENCE_REPAIR_REUSE_20261112.json"])
assert hashlib.sha256((repo / "research/study4/v2/reports/PHASE0_PAUSED52_PUBLIC.jsonl.gz").read_bytes()).hexdigest() == (
    "7bcbd1e52f720f4a55e75fde633ecc8fab0e3231b95f1c46204b105503841730")
db.close()
result = {
    "schema": VERSION + "-fixed-AC-cohort-2", "frozen_actual_source": plan["code_commit"],
    "frozen_actual_plan_sha256": fingerprint(plan),
    "current_runtime_binding": current,
    "checker_sha256_LF": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
    "supersedes_formal_reuse_not_historical_43audit": True,
    "historical_43audit_sha256": hashlib.sha256(historical_reuse_path.read_bytes()).hexdigest(),
    "selection_policy": "All original13tasks A/C retained together only if every shared-contract check passes; all B/D fresh",
    "cohort_is_all_or_none_not_individual_success_filter": True,
    "BD_stochastic_trajectory_equivalence_not_used_for_selection": True,
    "current_public_protocol_label_unchanged_because_public_schema_unchanged": True,
    "new_private_reference_version": VERSION, "audit_is_not_execution_approval": True,
    "old_full240_paid_recovery_disabled": True,
    "reference_source_sha256_LF": hashlib.sha256(
        (repo / "research/study4/v2/reference_completion.py").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
    "shared_phase0_functions_AST_identical_except_reference_released": True,
    "shared_phase0_module_constants_imports_AST_identical_except_reference_released": True,
    "episode_optional_hydrated_runtime_only_default_branch_AST_identical": True,
    "reference_call_guard_AST_B_D_only": True,
    "all9historical_roots_unchanged": True,
    "original_run_receipt_still_same_sha256": hashlib.sha256(
        (root / "FINAL_RECEIPT.json").read_bytes()).hexdigest() == prior_audit["pause"]["receipt_sha256"],
    "source_rule_coverage": {"tasks": len(compiled), "nodes": sum(len(t["nodes"]) for t in compiled)},
    "contracts": compiled, "complete_actual_episodes_checked": len(rows),
    "retained_complete_episodes": len(retained), "diagnostic_only_complete_episodes": len(rows) - len(retained),
    "retained_counts_by_arm": {a: sum(r["slot"]["arm"] == a for r in retained) for a in "ABCD"},
    "fresh_counts_by_arm": fresh_counts,
    "rows": rows, "remaining_fresh_slots": len(remaining), "remaining_manifest": remaining,
    "partial52_excluded_even_though_all6calls_settled": True,
    "retention_is_offline_proof_not_new_execution_or_paid_authority": True,
    "same_NL_reward_review_required_for_all_final240_not_reuse_selection": True,
    "budget": prior_audit["budget"],
    "cost_scenarios_not_guarantees": {
        "actual52complete_cost_USD_upper": str(complete_cost),
        "actual_partial_cost_USD_upper": str(partial_cost),
        "actual_complete_cost_by_arm_USD_upper": {a: str(v) for a, v in cost_by_arm.items()},
        "actual_complete_calls_by_arm": calls_by_arm,
        "remaining_at_all52observed_mean_USD_upper": str(observed_mean * len(remaining)),
        "remaining_at51excluding_proven_ledger_loop_USD_upper": str(nonpathological_mean * len(remaining)),
        "primary_arm_weighted214_USD_upper": str(stratified_cost),
        "primary_arm_weighted214_calls": str(stratified_calls),
        "sensitivity_arm_weighted_excluding_one_D_loop_USD_upper": str(tail_sensitivity_cost),
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
    "source_rule_coverage", "retained_complete_episodes", "diagnostic_only_complete_episodes",
    "retained_counts_by_arm", "fresh_counts_by_arm", "remaining_fresh_slots", "cost_scenarios_not_guarantees"]}))
