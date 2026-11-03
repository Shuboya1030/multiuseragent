"""Final R0 coverage/wire/ledger/preservation audit; no network access."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "frozen_stage/runner"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


scope = load(ROOT / "scope.json")
queue = load(RUN / "queue.json")
decisions = load(ROOT / "evaluation_v1/adjudications.json")
full_pairs = {d["task_id"]: d["episode_id"] for d in load(ROOT.parent /
              "r1_openai_repeat_and_full_v1/derived_full_v1/adjudications.json")}
assert len(scope) == len(queue) == len(decisions) == 60
assert len({s["task_id"] for s in queue}) == len({s["episode_id"] for s in queue}) == 60
assert {s["task_id"] for s in scope} == {d["task_id"] for d in decisions}
assert {s["task_id"]: s["episode_id"] for s in queue} == {
    d["task_id"]: d["episode_id"] for d in decisions}
assert all(s["paired_R1_episode_id"] == full_pairs[s["task_id"]] for s in scope)
assert sum(d["help_class"] == "Must-help" for d in decisions) == 30
assert not (RUN / "controller.lock").exists() and (RUN / "completion.json").exists()
assert load(RUN / "first_three_admission.json")["passed"]
baseline = load(RUN / "baseline.json")
ledger = ROOT.parent / "r1_formal/shared_budget/cost_ledger.jsonl"
events = lines(ledger)
settled = {e["id"]: e for e in events if e["event"] == "settle"}
reserved = {e["id"]: e for e in events if e["event"] == "reserve"}
unknown = {k: v for k, v in reserved.items() if k not in settled}
assert unknown == baseline["budget"]["unknown"]
paid = sum((Decimal(e["amount_usd"]) for e in settled.values()), Decimal(0))
held = sum((Decimal(e["amount_usd"]) for e in unknown.values()), Decimal(0))
assert paid + held <= 20
all_ids, agent_n, npc_n = set(), 0, 0
for slot in queue:
    run = RUN / "episodes/r0_gpt54" / slot["task_id"]
    status = load(run / "status.json")
    assert status["collection_complete"] and status["terminal"] != "runtime_error"
    manifest = load(run / "run_manifest.json")
    assert manifest["condition"] == "R0" and manifest["npc_backend"] == "controlled_rest_conversational_repair_v6"
    assert manifest["agent_model"] == "gpt-5.4-2026-03-05" and manifest["max_agent_steps"] == 64
    assert manifest["max_agent_output_tokens"] == 2048 and manifest["max_npc_output_tokens"] == 1024
    requests = {e["call_id"]: e for e in lines(run / "api_io.jsonl") if e["stage"] == "request"}
    responses = {e["call_id"]: e for e in lines(run / "api_io.jsonl") if e["stage"] == "response"}
    assert set(requests) == set(responses) <= set(settled)
    assert not all_ids & set(requests)
    all_ids.update(requests)
    input_audit = load(run / "actual_input_audit.json")
    assert input_audit["all_agent_requests_retain_directory"]
    directory = (ROOT / "task_inputs/templates" / slot["task_id"] /
                 "tac/documents_R0/directory.md").read_text(encoding="utf-8")
    for ident, item in requests.items():
        request, response = item["request"], responses[ident]["response"]
        role = item["role"]
        expected = "gpt-5.4-2026-03-05" if role == "agent" else "gpt-5.4-mini-2026-03-17"
        assert request["model"] == response["model"] == expected
        assert response["usage"] == settled[ident]["usage"]
        assert response["usage"].get("completion_tokens_details", {}).get("reasoning_tokens", 0) == 0
        assert request["reasoning_effort"] == "none"
        if role == "agent":
            agent_n += 1
            assert request["max_completion_tokens"] == 2048
            assert request["tool_choice"] == "auto" and request["parallel_tool_calls"] is False
            assert request["messages"][1]["content"].endswith(directory)
        else:
            npc_n += 1
        assert Decimal(settled[ident]["amount_usd"]) <= Decimal(reserved[ident]["amount_usd"])
    agent_requests = [item for item in requests.values() if item["role"] == "agent"]
    for earlier_request, later_request in zip(agent_requests, agent_requests[1:]):
        earlier, later = earlier_request["request"]["messages"], later_request["request"]["messages"]
        assert later[:len(earlier)] == earlier, "Agent history must not truncate across NPC calls"
for name, item in baseline["shared_prefixes"].items():
    assert hashlib.sha256(Path(name).read_bytes()[:item["bytes"]]).hexdigest() == item["sha256"]
for name, digest in baseline["source_hashes"].items():
    assert sha(Path(name)) == digest
new_paid = sum((Decimal(settled[i]["amount_usd"]) for i in all_ids), Decimal(0))
recorded_ids = {e["call_id"] for path in RUN.rglob("api_io.jsonl")
                for e in lines(path) if e["stage"] == "request"}
assert recorded_ids == all_ids, "No extra/unindexed model calls allowed"
result = {
    "passed": True, "scope": 60, "reviewed": 60, "Must": 30, "Optional": 30,
    "unique_episodes": 60, "actual_calls": len(all_ids), "agent_calls": agent_n, "NPC_calls": npc_n,
    "R0_cost_usd": str(new_paid), "global_settled_usd": str(paid),
    "old_unknown_count": len(unknown), "old_unknown_usd": str(held), "new_unknown": 0,
    "global_occupied_usd": str(paid + held), "historical_source_hashes_preserved": len(baseline["source_hashes"]),
    "all_wires_models_limits_full_history_directory_verified": True,
    "extra_model_attempts": 0, "R_prime_computed": False,
    "gold_validity_dispute": ["o-high-eval-budget"],
    "no_external_dependencies_downloaded": True,
}
(ROOT / "evaluation_v1/final_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
