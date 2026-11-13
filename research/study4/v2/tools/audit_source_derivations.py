"""Bounded source-role and whole-batch path audit; no model, transport or tool execution."""
from dataclasses import asdict
from decimal import Decimal
import hashlib
from pathlib import Path
import sqlite3
import subprocess
import sys
import types

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo))
from research.study4.v2.contracts import fingerprint, require, strict_json
from research.study4.v2.phase0 import (
    Phase0Runtime, build_request, history_events, load_case, restore_public_state,
    npc_system, scorer, task_ids, write_new)
from research.study4.v2.reference_completion import contracts, progress, VERSION

if len(sys.argv) != 3:
    raise SystemExit("Usage: audit_source_derivations.py STOPPED_V6_ROOT NEW_OUTPUT_JSON")
root = Path(sys.argv[1]).resolve()
plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
receipt = strict_json((root / "FINAL_RECEIPT.json").read_bytes())
require(receipt["budget"]["unknown"] == receipt["budget"]["in_flight"] == 0,
        "Only a settled operator pause can be audited")
frozen_source = subprocess.check_output(
    ["git", "show", plan["code_commit"] + ":research/study4/v2/reference_completion.py"],
    text=True, encoding="utf-8")
legacy = types.ModuleType("research.study4.v2._frozen_reference_for_audit")
legacy.__package__ = "research.study4.v2"
sys.modules[legacy.__name__] = legacy
exec(compile(frozen_source, "<frozen-reference-v6>", "exec"), legacy.__dict__)
require(legacy.VERSION == "study4-reference-completion-6", "Exact source v6 comparator")

nodes, role_counts = [], {}
for tid in task_ids():
    case = load_case(tid)
    hidden = {h["id"]: h for h in case.blueprint["hidden_information"]}
    specs = contracts(case)
    for node in case.blueprint["gold_dag"]["nodes"]:
        spec = specs[node["id"]]
        records = [hidden[h] for h in node["information_ids"]]
        facts = {k: v for h in records for k, v in h["facts"].items()}
        roles = {}
        for key in facts:
            if key in spec.issued_fields:
                role = "actual_issued_record_never_publicly_derived"
            elif key in spec.qualifiers:
                role = "applicability_or_explanatory_metadata_not_literal_recitation"
            elif any(r["target"] == key for r in spec.derivations):
                role = "direct_or_public_rule_derived_after_actual_premises"
            elif any(key not in alternative for alternative in spec.alternatives):
                role = "direct_quote_or_unit_input_alternative"
            else:
                role = "direct_witness_required"
            roles[key] = role
            role_counts[role] = role_counts.get(role, 0) + 1
        require(not (set(spec.issued_fields) & {d["target"] for d in spec.derivations}),
                "A public rule cannot issue an authorization or attestation")
        nodes.append({
            "task_id": tid, "node_id": node["id"], "source_node": node,
            "source_records": records, "contract": asdict(spec), "field_roles": roles,
            "public_documents": dict(case.public.documents),
            "downstream_required_context": [
                {"node_id": n["id"], "context": hidden[h]["required_context"]}
                for n in case.blueprint["gold_dag"]["nodes"] for h in n["information_ids"]
                if node["id"] in n["requires"]],
            "audit_basis": "Direct reading of release_rule, public policy, output and downstream context; not canonical full-hiddenfacts fixture or episode score",
            "unlisted_derivations_not_guessed": True})
require(len(nodes) == 95, "All60/95 original nodes, not a result-selected subset")

def route(module, case, events):
    obtained = module.progress(case, events, scorer())["released"]
    ready = [n for n in case.blueprint["gold_dag"]["nodes"]
             if n["id"] not in obtained and set(n["requires"]) <= obtained]
    return min(ready[0]["admissible_recipients"],
               key=lambda p: (case.costs[p], ready[0]["admissible_recipients"].index(p))) if ready else None

current = sys.modules[progress.__module__]
issued_probes = []
for tid, key in (("m-high-incident-postmortem", "root_cause_code"),
                 ("m-high-payroll-correction", "hr_verification_id"),
                 ("m-high-price-change", "margin_check_id")):
    case = load_case(tid)
    hidden = {h["id"]: h for h in case.blueprint["hidden_information"]}
    events = []
    def exchange(person, question, reply):
        mid = "source-audit-fixture:" + str(len(events))
        events.extend([{"kind": "send_message", "person_id": person, "message_id": mid, "content": question},
                       {"kind": "read_messages", "person_id": person, "message_id": mid + ":reply",
                        "in_reply_to": mid, "content": reply}])
    for node in case.blueprint["gold_dag"]["nodes"]:
        records = [hidden[h] for h in node["information_ids"]]
        facts = {k: v for h in records for k, v in h["facts"].items()}
        question = " ".join(str(c) for h in records for c in h["required_context"])
        if key in facts:
            break
        exchange(node["admissible_recipients"][0], question,
                 "\n".join(k + ": " + str(v) for k, v in facts.items()))
    require(set(node["requires"]) <= legacy.progress(case, events, scorer())["released"],
            "Issuance fixture prerequisites must actually be satisfied")
    exchange(node["admissible_recipients"][0], question, "If approved, " + key + ": " + facts[key])
    before, after = legacy.progress(case, events, scorer()), progress(case, events, scorer())
    require(node["id"] in before["released"] and node["id"] not in after["released"],
            "Original source-act role omission must reproduce before/after")
    issued_probes.append({"task_id": tid, "field": key, "original_release_rule": records[0]["release_rule"],
                          "fixture_not_actual_model_result": True,
                          "v6_conditional_incorrectly_released": True, "v7_conditional_not_released": True})
rows, branches = [], []
journal = [strict_json(line) for line in (root / "events.jsonl").read_bytes().splitlines()]
db = sqlite3.connect((root / (plan["run_id"] + ".sqlite3")).resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
try:
    calls = db.execute(
        "select id,episode,operation,state,charged,result,request_sha256,result_sha256 from calls order by created"
    ).fetchall()
finally:
    db.close()
paid = {c[0]: c for c in calls}
for path in sorted(root.glob("slot-*.json")):
    record = strict_json(path.read_bytes())
    slot = record["slot"]
    row = {"slot": slot, "source_record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
           "action": "retain_publicly_unchanged_AC" if slot["arm"] in {"A", "C"} else None}
    divergences = []
    if slot["arm"] in {"B", "D"}:
        case = load_case(slot["task_id"])
        controls = [i for i, e in enumerate(record["history"]) if e["kind"] == "control_decision"]
        for i in controls:
            prefix = record["history"][:i]
            event = record["history"][i]
            old, new = route(legacy, case, prefix), route(current, case, prefix)
            actual = event["person_id"] if event["action"] == "ASK" else None
            require(old == actual, "Frozen v6 path must reproduce actual decisions before comparison")
            if old != new:
                divergences.append({"boundary_event_index": i, "old_person": old, "new_person": new,
                                    "public_history_sha256": fingerprint(prefix)})
        row["decisions_checked"] = len(controls)
        row["action"] = "retain_complete_path_without_resampling" if not divergences else "branch_original_trajectory"
        row["first_divergence"] = divergences[0] if divergences else None
        if divergences:
            boundary = divergences[0]["boundary_event_index"]
            prefix = record["history"][:boundary]
            requests = [r for r in journal if r["kind"] == "model_request" and
                        r["episode_id"] == slot["episode_id"] and r["operation"] == "question"]
            next_request = next(r for r in requests if restore_public_state(
                strict_json(r["request"]["input"][-1]["content"])["state"],
                r["request"]["input"][1:-1])["history"] == prefix)
            history = next_request["request"]["input"][1:-1]
            state = restore_public_state(strict_json(next_request["request"]["input"][-1]["content"])["state"], history)
            runtime = Phase0Runtime(case, slot["episode_id"])
            runtime.workspace, runtime.history = state["workspace"], prefix
            runtime.normal_actions, runtime.cost = state["normal_actions"], state["contact_cost"]
            runtime.contacts = sum(e["kind"] == "send_message" for e in prefix)
            runtime.artifact_revision = state["progress"]["artifact_revision"]
            require(not state["progress"]["posted_current_revision"] and
                    not state["progress"]["bridge_submitted"] and not state["failed"] and not state["terminal"],
                    "This branch precedes delivery/submit; do not guess terminal state")
            require(fingerprint(runtime.observe()) == fingerprint(state) and history_events(history) == prefix,
                    "Hydrated branch must reproduce the complete actual public observation and receipts")
            require([e["kind"] for e in prefix] ==
                    ["control_decision", "send_message", "read_messages", "tool_result"],
                    "This bounded certificate covers the actual first complete ASK/ordinary cycle")
            control, send, read, applied = prefix
            runtime.messages[send["message_id"]] = {
                k: send[k] for k in ("message_id", "person_id", "content")}
            runtime.messages[send["message_id"]]["sender"] = "agent"
            runtime.messages[read["message_id"]] = {
                k: read[k] for k in ("message_id", "in_reply_to", "person_id", "content")}
            runtime.seen, runtime.after_reply = {read["message_id"]}, True
            prior_journal = journal[:journal.index(next_request)]
            prefix_requests = [e for e in prior_journal if e["kind"] == "model_request" and
                               e["episode_id"] == slot["episode_id"]]
            prefix_results = [e for e in prior_journal if e["kind"] == "model_result" and
                              e["episode_id"] == slot["episode_id"]]
            require([e["operation"] for e in prefix_requests] == ["question", "npc", "ordinary"] and
                    len(prefix_results) == 3 and all(e["index"] == 0 for e in prefix_requests),
                    "Exactly three original settled calls precede first divergence")
            for request, result in zip(prefix_requests, prefix_results):
                paid_row = paid[f"{slot['episode_id']}:{request['operation']}:{request['index']}"]
                stored = {k: v for k, v in result["result"].items() if k != "replayed_without_send"}
                require(paid_row[3] == "settled" and fingerprint(request["request"]) == request["request_sha256"] ==
                        paid_row[6] and strict_json(paid_row[5]) == stored and fingerprint(stored) == paid_row[7] and
                        result["result"]["replayed_without_send"] is False,
                        "Each original prefix request and result must match settled ledger hashes")
            question, npc, ordinary = [e["result"]["data"] for e in prefix_results]
            require(question["tool"] == "ask_colleague" and
                    control["person_id"] == send["person_id"] == read["person_id"] ==
                    question["arguments"]["person_id"] and
                    send["content"] == question["arguments"]["question"] and
                    read["in_reply_to"] == send["message_id"] and read["content"] == npc["text"] and
                    applied["tool"] == ordinary["tool"] == "read_file" and
                    applied["path"] == ordinary["arguments"]["path"] and
                    applied["content"] == runtime.workspace[applied["path"]],
                    "Already applied ASK/read/ordinary must bind exact original paid outputs")
            dialogue = [{"role": "system", "content": npc_system(send["person_id"], case.scenarios[send["person_id"]])},
                        {"role": "user", "content": send["content"]},
                        {"role": "assistant", "content": read["content"]}]
            require(prefix_requests[1]["request"]["input"] + [dialogue[-1]] == dialogue and
                    "Public read-source index" not in send["content"],
                    "Complete original NPC conversation and initially empty D source cache preserved")
            new_request = build_request("question", state, person=divergences[0]["new_person"], history=history)
            branches.append({**divergences[0], "slot": slot,
                "branch_before_request_index": next_request["index"],
                "retained_prefix_calls": next_request["index"] * 3,
                "native_history_sha256": fingerprint(history),
                "public_state_sha256": fingerprint(state),
                "new_routed_request_sha256": fingerprint(new_request),
                "restored_messages_sha256": fingerprint(runtime.messages),
                "restored_seen_message_ids": sorted(runtime.seen),
                "restored_after_reply": runtime.after_reply, "restored_event_cursor": len(prefix),
                "restored_NPC_dialogue_sha256_NOT_system_text": fingerprint(dialogue),
                "restored_known_sources": {send["person_id"]: []},
                "next_call_indices": {"question": 1, "npc": 1, "ordinary": 1},
                "settled_prefix_request_fingerprints": [e["request_sha256"] for e in prefix_requests],
                "old_suffix_only_diagnostic_and_fully_charged": True,
                "no_old_call_or_tool_reexecution": True,
                "first_sufficient_reply": next(e for e in prefix if e["kind"] == "read_messages"),
                "private_derivation_proofs": progress(case, prefix, scorer())["public_derivation_proofs_PRIVATE"]})
    rows.append(row)

require(len(calls) == 300 and all(c[3] == "settled" for c in calls), "No unaccounted/unknown v6 exposure")
last = calls[-1]
recorded_results = {f"{e['episode_id']}:{e['operation']}:{e['index']}"
                    for e in journal if e["kind"] == "model_result"}
require(last[0] not in recorded_results and all(c[0] in recorded_results for c in calls[:-1]),
        "Exactly one settled proposal failed only the post-settlement journal append")
pending = strict_json(last[5])
require(last[2] == "question" and pending["data"]["tool"] == "ask_colleague" and
        not any(e["kind"] == "runtime_event" and e["episode_id"] == last[1] for e in journal),
        "Pending first question has never executed send/tool/NPC")
pending_request = next(e for e in journal if e["kind"] == "model_request" and e["episode_id"] == last[1])
body = strict_json(pending_request["request"]["input"][-1]["content"])
pending_slot = next(s for s in plan["slots"] if s["episode_id"] == last[1])
require(route(current, load_case(pending_slot["task_id"]), []) == body["person_id"] ==
        pending["data"]["arguments"]["person_id"], "Settled pending proposal remains legal under repaired contract")
cost = sum((Decimal(c[4]) for c in calls), Decimal(0))
by_slot = {r["slot"]["slot"]: r for r in rows}
manifest = []
for slot in plan["slots"]:
    row = by_slot.get(slot["slot"])
    action = (row["action"] if row is not None else
              "apply_settled_pending_proposal_then_continue" if slot == pending_slot else "unstarted_fresh")
    manifest.append({"slot": slot, "action": action,
                     "retention_or_prefix_requires_reviewed_new_source_binding": True})
require(len(manifest) == 240 and len({m["slot"]["slot"] for m in manifest}) == 240,
        "Every logical slot retained or continued, never drop/redraw based on reply or score")
write_new(Path(sys.argv[2]), {
    "schema": VERSION + "-95-source-and-whole-path-audit-1", "frozen_v6_source": plan["code_commit"],
    "frozen_v6_plan_sha256": fingerprint(plan), "nodes": nodes, "field_role_counts": role_counts,
    "source_issued_record_counterexamples": issued_probes,
    "complete_rows": rows, "branches": branches,
    "proposed_resume_manifest_NOT_execution_approval": manifest,
    "all_or_branch_not_retain_then_redraw": True, "score_not_used_in_any_reuse_branch_decision": True,
    "complete_retained_by_path": sum(r["action"] != "branch_original_trajectory" for r in rows),
    "pending_settled_proposal": {"slot": pending_slot, "call_id": last[0],
        "result_sha256": fingerprint(pending), "applied": False, "request_sha256": pending_request["request_sha256"],
        "next_stage": "apply_this_already_paid_question_once_then_NPC_then_one_ordinary",
        "no_provider_replay_required": True},
    "budget": {"v6_calls": 300, "v6_settled": 300, "v6_unknown": 0, "inflight": 0,
        "v6_settled_USD_upper": str(cost), "all_calls": 1340, "all_settled": 1334, "all_unknown": 6,
        "occupied_USD_upper": receipt["budget"]["occupied_USD_upper"],
        "remaining_USD": str(Decimal(50) - Decimal(receipt["budget"]["occupied_USD_upper"])),
        "old_unknown_held_USD": "5.148000"},
    "source_sha256_LF": hashlib.sha256((repo / "research/study4/v2/reference_completion.py").read_bytes()
                                      .replace(b"\r\n", b"\n")).hexdigest(),
    "review_pause_is_Agent_not_user": True, "execution_not_authorized_by_this_audit": True})
print({"nodes": len(nodes), "roles": role_counts, "complete_path_rows": len(rows),
       "retained_complete": sum(r["action"] != "branch_original_trajectory" for r in rows),
       "branches": len(branches), "pending_paid_proposals": 1})
