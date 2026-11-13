"""Zero-API v7 stop/context-boundary audit, not an execution admission."""
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import types

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo))
from research.study4.v2.contracts import fingerprint, require, strict_json
from research.study4.v2.phase0 import (
    Phase0Runtime, build_request, history_events, load_case, npc_system,
    public_sources, restore_public_state, scorer, task_ids, write_new)
from research.study4.v2.phase0_admission import runtime_binding
from research.study4.v2 import reference_completion as current

if len(sys.argv) != 4:
    raise SystemExit("Usage: audit_context_recovery.py STOPPED_V7_ROOT REVIEWED_ANALYSIS NEW_OUTPUT")
root = Path(sys.argv[1]).resolve()
plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
receipt = strict_json((root / "FINAL_RECEIPT.json").read_bytes())
require(receipt["complete_episodes"] == 67 and receipt["budget"]["in_flight"] == 0,
        "Exact stopped v7 evidence, no live request")
analysis = strict_json(Path(sys.argv[2]).read_bytes())
require(analysis["complete_episodes"] == 67 and not analysis["private_review_queue"],
        "All actual completed evidence reviewed; not a full240 gate")
old_source = subprocess.check_output(
    ["git", "show", plan["code_commit"] + ":research/study4/v2/reference_completion.py"],
    text=True, encoding="utf-8")
legacy = types.ModuleType("research.study4.v2._v7_context_audit")
legacy.__package__ = "research.study4.v2"
sys.modules[legacy.__name__] = legacy
exec(compile(old_source, "<frozen-v7-reference>", "exec"), legacy.__dict__)
require(legacy.VERSION == "study4-reference-completion-7", "Frozen v7 comparator required")
binding = runtime_binding()
require({k: v for k, v in binding.items() if k != "phase0_sources"} ==
        {k: v for k, v in plan["runtime"].items() if k != "phase0_sources"} and
        {k: v for k, v in binding["phase0_sources"].items() if k != "reference_completion.py"} ==
        {k: v for k, v in plan["runtime"]["phase0_sources"].items() if k != "reference_completion.py"},
        "Executor/NPC/scorer/public what/tools/history/limits unchanged")
ac = strict_json((repo / "research/study4/v2/reports/REFERENCE_V8_AC26_CERTIFIED_20261113.json").read_bytes())
require(ac["current_runtime_binding"] == binding and ac["retained_complete_episodes"] == 26,
        "Entire original A/C cohort must be revalidated, not selected individually")
source_rows = []
for tid in task_ids():
    case = load_case(tid)
    require({k: asdict(v) for k, v in current.contracts(case).items()} ==
            {k: asdict(v) for k, v in legacy.contracts(case).items()},
            "No node completion obligation, grant rule, truth or derivation changed")
    public = case.public.instruction + "\n" + "\n".join(t for _, t in case.public.documents)
    hidden = {h["id"]: h for h in case.blueprint["hidden_information"]}
    for node in case.blueprint["gold_dag"]["nodes"]:
        contexts = [c for hid in node["information_ids"] for c in hidden[hid]["required_context"]]
        source_rows.append({
            "task_id": tid, "node_id": node["id"], "required_context": contexts,
            "source_node_sha256": fingerprint(node),
            "public_packet_sha256": fingerprint(public),
            "public_expansions": {str(c): list(current.public_context_aliases(c, public)) for c in contexts},
            "public_alias_witnesses": [
                {"required_context": c, "alias": alias, "path": path,
                 "source_text": text, "source_sha256": fingerprint(text)}
                for c in contexts for alias in current.public_context_aliases(c, public)
                for path, text in (("public_instruction", case.public.instruction), *case.public.documents)
                if alias in " ".join(current.normalize(text).split())],
        })
require(len(source_rows) == 95, "All60/95 unchanged source obligations")

def entries(folder):
    return [strict_json(line) for line in (folder / "events.jsonl").read_bytes().splitlines()]

journal = entries(root)
prior = Path(plan["history"][-1]["root"])
prior_journal = entries(prior)
all_requests = [e for e in journal + prior_journal if e["kind"] == "model_request"]

def route(module, case, history):
    released = module.progress(case, history, scorer())["released"]
    ready = [n for n in case.blueprint["gold_dag"]["nodes"]
             if n["id"] not in released and set(n["requires"]) <= released]
    return min(ready[0]["admissible_recipients"], key=lambda p: (
        case.costs[p], ready[0]["admissible_recipients"].index(p))) if ready else None

rows, branches = [], []
records = [strict_json(p.read_bytes()) for p in sorted(root.glob("slot-*.json"))]
for record in records:
    slot = record["slot"]
    requests = [e for e in all_requests if e["episode_id"] == slot["episode_id"]]
    if slot["arm"] in {"A", "C"}:
        for entry in requests:
            request = entry["request"]
            if entry["operation"] == "npc":
                rebuilt = build_request("npc", dialogue=request["input"])
            else:
                body = strict_json(request["input"][-1]["content"])
                native = request["input"][1:-1]
                state = restore_public_state(body["state"], native)
                rebuilt = build_request(body["mode"], state, person=body["person_id"], history=native)
            require(fingerprint(rebuilt) == entry["request_sha256"],
                    "Reject entire shared A/C group if a public request changed")
    divergence = None
    controls = 0
    if slot["arm"] in {"B", "D"}:
        case = load_case(slot["task_id"])
        for i, event in enumerate(record["history"]):
            if event["kind"] != "control_decision":
                continue
            controls += 1
            prefix = record["history"][:i]
            old, new = route(legacy, case, prefix), route(current, case, prefix)
            actual = event.get("person_id") if event["action"] == "ASK" else None
            require(old == actual, "Original whole path must reproduce frozen v7 decisions")
            if old != new:
                boundary = next(e for e in requests if e["operation"] == "question" and
                                restore_public_state(strict_json(e["request"]["input"][-1]["content"])["state"],
                                                     e["request"]["input"][1:-1])["history"] == prefix)
                native = boundary["request"]["input"][1:-1]
                state = restore_public_state(strict_json(
                    boundary["request"]["input"][-1]["content"])["state"], native)
                require(not state["terminal"] and not state["failed"],
                        "No terminal restart or invented rescue")
                source_journal = journal if boundary in journal else prior_journal
                before_request = source_journal[:source_journal.index(boundary)]
                prefix_requests = [e for e in before_request if e["kind"] == "model_request" and
                                   e["episode_id"] == slot["episode_id"]]
                prefix_results = [e for e in before_request if e["kind"] == "model_result" and
                                  e["episode_id"] == slot["episode_id"]]
                require([e["operation"] for e in prefix_requests] == ["question", "npc", "ordinary"] and
                        len(prefix_results) == 3 and all(e["index"] == 0 for e in prefix_requests),
                        "This bounded certificate preserves exactly the first complete paid cycle")
                source_root = root if boundary in journal else prior
                source_plan = strict_json((source_root / "FROZEN_PLAN.json").read_bytes())
                paid_db = sqlite3.connect((source_root / (source_plan["run_id"] + ".sqlite3")).as_uri() +
                                           "?mode=ro", uri=True)
                try:
                    for request, result in zip(prefix_requests, prefix_results):
                        paid = paid_db.execute(
                            "select state,request_sha256,result_sha256,result from calls where id=?",
                            (f"{slot['episode_id']}:{request['operation']}:{request['index']}",)).fetchone()
                        saved = {k: v for k, v in result["result"].items() if k != "replayed_without_send"}
                        require(paid[0] == "settled" and paid[1] == fingerprint(request["request"]) ==
                                request["request_sha256"] and paid[2] == fingerprint(saved) and
                                strict_json(paid[3]) == saved, "Exact three settled request/result bindings")
                finally:
                    paid_db.close()
                runtime = Phase0Runtime(case, slot["episode_id"])
                runtime.workspace, runtime.history = state["workspace"], prefix
                runtime.normal_actions, runtime.cost = state["normal_actions"], state["contact_cost"]
                runtime.contacts = sum(e["kind"] == "send_message" for e in prefix)
                runtime.artifact_revision = state["progress"]["artifact_revision"]
                for event_before in prefix:
                    if event_before["kind"] == "send_message":
                        runtime.messages[event_before["message_id"]] = {
                            k: event_before[k] for k in ("message_id", "person_id", "content")}
                        runtime.messages[event_before["message_id"]]["sender"] = "agent"
                    elif event_before["kind"] == "read_messages":
                        runtime.messages[event_before["message_id"]] = {k: event_before[k] for k in
                            ("message_id", "in_reply_to", "person_id", "content")}
                        runtime.seen.add(event_before["message_id"])
                        runtime.after_reply = True
                require(fingerprint(runtime.observe()) == fingerprint(state) and history_events(native) == prefix,
                        "Hydration must preserve full observation, messages, receipts and applied ordinary0")
                require(prefix[-1]["tool"] == "read_file" and
                        prefix[-1]["content"] == runtime.workspace[prefix[-1]["path"]] and
                        not state["progress"]["posted_current_revision"] and
                        not state["progress"]["bridge_submitted"], "Actual paid read, no write/post replay")
                person = prefix[1]["person_id"]
                dialogue = [{"role": "system", "content": npc_system(person, case.scenarios[person])},
                            {"role": "user", "content": prefix[1]["content"]},
                            {"role": "assistant", "content": prefix[2]["content"]}]
                require(prefix_requests[1]["request"]["input"] + [dialogue[-1]] == dialogue and
                        slot["arm"] == "B", "Actual same-person conversation and empty B source cache")
                divergence = {
                    "slot": slot, "boundary_event_index": i, "old_person": old, "new_person": new,
                    "source_episode_id": slot["episode_id"], "next_question_index": boundary["index"],
                    "native_history_sha256": fingerprint(native), "public_state_sha256": fingerprint(state),
                    "public_history_sha256": fingerprint(prefix), "normal_actions": state["normal_actions"],
                    "branch_before_request_sha256": boundary["request_sha256"],
                    "known_paid_prefix_not_resampled": True, "old_suffix_diagnostic_fully_charged": True,
                    "retained_settled_calls": 3, "applied_ordinary0_preserved": True,
                    "messages_sha256": fingerprint(runtime.messages), "seen_ids": sorted(runtime.seen),
                    "NPC_dialogue_sha256_NOT_system_text": fingerprint(dialogue),
                    "known_sources": {}, "next_indices": {"question": 1, "npc": 1, "ordinary": 1},
                    "event_cursor": len(prefix), "after_reply": runtime.after_reply,
                    "prefix_request_sha256": [e["request_sha256"] for e in prefix_requests],
                    "prefix_result_sha256": [fingerprint({k: v for k, v in e["result"].items()
                                                         if k != "replayed_without_send"})
                                            for e in prefix_results],
                }
                branches.append(divergence)
                break
    rows.append({
        "slot": slot, "record_sha256": fingerprint(record), "control_decisions_through_boundary": controls,
        "public_requests_rebuilt": len(requests),
        "action": "branch_original_prefix" if divergence else "retain_entire_path",
        "selection_uses_score": False,
    })
manifest = []
by_slot = {row["slot"]["slot"]: row for row in rows}
for slot in plan["slots"]:
    row = by_slot.get(slot["slot"])
    manifest.append({"slot": slot, "action": row["action"] if row else "not_complete_not_zero"})
db = sqlite3.connect((root / (plan["run_id"] + ".sqlite3")).as_uri() + "?mode=ro", uri=True)
db.row_factory = sqlite3.Row
calls = [dict(row) for row in db.execute(
    "select id,episode,operation,state,charged,input_tokens,output_tokens,created,updated,diagnostic "
    "from calls order by created")]
db.close()
unknown = [c for c in calls if c["state"] == "unknown"]
require(len(calls) == 624 and len(unknown) == 1 and calls[-1] == unknown[0], "Exact no-retry stop")
failed = unknown[0]
failed_request = next(e for e in journal if e["kind"] == "model_request" and
                      f"{e['episode_id']}:{e['operation']}:{e['index']}" == failed["id"])
failed_body = strict_json(failed_request["request"]["input"][-1]["content"])
failed_state = restore_public_state(failed_body["state"], failed_request["request"]["input"][1:-1])
partial_slot = next(s for s in plan["slots"] if s["episode_id"] == failed["episode"])
partial_changes = []
for i, event in enumerate(failed_state["history"]):
    if event["kind"] == "control_decision":
        case = load_case(partial_slot["task_id"])
        old, new = route(legacy, case, failed_state["history"][:i]), route(
            current, case, failed_state["history"][:i])
        if old != new:
            partial_changes.append({"event_index": i, "old_person": old, "new_person": new})
            break
spent = sum((Decimal(c["charged"]) for c in calls if c["state"] == "settled"), Decimal(0))
costs, counts = defaultdict(Decimal), Counter()
for record in records:
    slot = record["slot"]
    own = [c for c in calls if c["episode"] == slot["episode_id"]]
    if own:
        counts[slot["arm"]] += 1
        costs[slot["arm"]] += sum((Decimal(c["charged"]) for c in own), Decimal(0))
# Fully new v7 A/C/B/D sample only; inherited prefixes are explicitly not a free forecast.
base = sum((costs[a] / counts[a] * sum(
    s["arm"] == a and (s["slot"] not in by_slot or
                      by_slot[s["slot"]]["action"] == "branch_original_prefix")
    for s in plan["slots"]) for a in "ABCD"), Decimal(0))
partial_cost = sum((Decimal(c["charged"]) for c in calls
                    if c["episode"] == failed["episode"] and c["state"] == "settled"), Decimal(0))
diagnostic = strict_json(failed["diagnostic"])
partial_case = load_case(partial_slot["task_id"])
partial_runtime = Phase0Runtime(partial_case, partial_slot["episode_id"])
for event in failed_state["history"]:
    if event["kind"] == "write_file":
        if (event["path"] == partial_case.public.artifact_path and
                partial_runtime.workspace.get(event["path"]) != event["content"]):
            partial_runtime.artifact_revision += 1
        partial_runtime.workspace[event["path"]] = event["content"]
    elif event["kind"] == "post_channel" and (
            partial_runtime.artifact_revision > 0 and
            partial_case.public.artifact_path in event["content"] and
            event["content"].strip() != partial_case.public.artifact_path):
        partial_runtime.posted_revision = partial_runtime.artifact_revision
    elif event["kind"] == "send_message":
        partial_runtime.messages[event["message_id"]] = {k: event[k] for k in
            ("message_id", "person_id", "content")}
        partial_runtime.messages[event["message_id"]]["sender"] = "agent"
    elif event["kind"] == "read_messages":
        partial_runtime.messages[event["message_id"]] = {k: event[k] for k in
            ("message_id", "in_reply_to", "person_id", "content")}
        partial_runtime.seen.add(event["message_id"])
        partial_runtime.after_reply = True
partial_runtime.history = failed_state["history"]
partial_runtime.normal_actions = failed_state["normal_actions"]
partial_runtime.contacts = sum(e["kind"] == "send_message" for e in partial_runtime.history)
partial_runtime.cost = failed_state["contact_cost"]
partial_native = failed_request["request"]["input"][1:-1]
require(fingerprint(partial_runtime.observe()) == fingerprint(failed_state) and
        history_events(partial_native) == partial_runtime.history,
        "Known partial workspace/revisions/delivery/messages/receipts must hydrate without tool execution")
partial_entries = [e for e in journal if e.get("episode_id") == failed["episode"]]
partial_requests = [e for e in partial_entries if e["kind"] == "model_request"]
partial_results = [e for e in partial_entries if e["kind"] == "model_result"]
require(len(partial_results) == 188 and len(partial_requests) == 189,
        "188 settled paid prefix calls, one distinct unknown ordinary62")
paid_db = sqlite3.connect((root / (plan["run_id"] + ".sqlite3")).as_uri() + "?mode=ro", uri=True)
try:
    for request, result in zip(partial_requests, partial_results):
        stored = {k: v for k, v in result["result"].items() if k != "replayed_without_send"}
        paid = paid_db.execute(
            "select state,request_sha256,result_sha256 from calls where id=?",
            (f"{failed['episode']}:{request['operation']}:{request['index']}",)).fetchone()
        require(paid == ("settled", fingerprint(request["request"]), fingerprint(stored)),
                "Each known partial request/result must bind its settled original ledger")
finally:
    paid_db.close()
dialogs, cache = {}, {}
for i, event in enumerate(partial_runtime.history):
    if event["kind"] not in {"send_message", "read_messages"}:
        continue
    person = event["person_id"]
    dialogs.setdefault(person, [{"role": "system", "content": npc_system(
        person, partial_case.scenarios[person])}])
    dialogs[person].append({"role": "user" if event["kind"] == "send_message" else "assistant",
                            "content": event["content"]})
    if event["kind"] == "read_messages":
        cache.setdefault(person, set()).update(s["source_id"] for s in public_sources(
            {"history": partial_runtime.history[:i]}))
last_npc = next(e for e in reversed(partial_requests) if e["operation"] == "npc")
last_read = next(e for e in reversed(partial_runtime.history) if e["kind"] == "read_messages")
require(last_npc["request"]["input"] + [{"role": "assistant", "content": last_read["content"]}] ==
        dialogs[last_read["person_id"]], "Same-person full NPC dialogue is preserved")
from research.study4.v2.contracts import canonical
require(len(canonical(failed_request["request"]).encode()) ==
        diagnostic["transport"]["request_bytes"], "Exact persisted failed request byte count")
window_start = datetime.fromisoformat(failed["created"]) - timedelta(seconds=60)
recent = [c for c in calls if c["state"] == "settled" and
          datetime.fromisoformat(c["created"]) >= window_start]
usage = {c["id"]: c for c in calls}
growth = []
for request in partial_requests:
    if request["operation"] != "ordinary" or request["index"] not in {0, 20, 40, 60, 61, 62}:
        continue
    body = request["request"]
    paid = usage[f"{failed['episode']}:ordinary:{request['index']}"]
    growth.append({"ordinary_index": request["index"], "request_bytes": len(canonical(body).encode()),
                   "native_history_items": len(body["input"][1:-1]),
                   "input_tokens": paid["input_tokens"], "output_tokens": paid["output_tokens"]})
remaining_by_arm = Counter(s["arm"] for s in plan["slots"] if s["slot"] not in by_slot or
                          by_slot[s["slot"]]["action"] == "branch_original_prefix")
tail_inclusive = sum((costs[a] / counts[a] * remaining_by_arm[a]
                      for a in "ABC"), Decimal(0))
tail_inclusive += (costs["D"] + partial_cost) / (counts["D"] + 1) * (remaining_by_arm["D"] - 1)
result = {
    "schema": "study4-reference-v8-context-and-rate-stop-audit-1", "execution_approved": False,
    "frozen_v7_commit": plan["code_commit"], "frozen_v7_plan_sha256": fingerprint(plan),
    "source_sha256_LF": binding["phase0_sources"]["reference_completion.py"],
    "current_runtime_binding": binding, "source_rule_coverage": {"tasks": 60, "nodes": 95},
    "source_contexts": source_rows, "whole_actual_paths": rows, "branches": branches,
    "retained_complete": sum(r["action"] == "retain_entire_path" for r in rows),
    "all_AC_retained_together": sum(r["slot"]["arm"] in {"A", "C"} for r in rows),
    "not_score_selected_or_redrawn": True, "full240_manifest": manifest,
    "partial": {"slot": partial_slot, "known_public_state_sha256": fingerprint(failed_state),
                "ordinary_actions_completed": failed_state["normal_actions"],
                "contacts": sum(e["kind"] == "send_message" for e in failed_state["history"]),
                "v8_first_divergence": partial_changes, "unknown_call_id": failed["id"],
                "unknown_request_sha256": failed_request["request_sha256"],
                "unknown_never_replayed": True, "paid_known_prefix_USD_upper": str(partial_cost),
                "188_settled_request_result_bindings_checked": True,
                "native_history_sha256": fingerprint(partial_native),
                "NPC_dialogues_sha256_NOT_system_text": fingerprint(dialogs),
                "known_sources_sha256": fingerprint({p: sorted(v) for p, v in cache.items()}),
                "messages_sha256": fingerprint(partial_runtime.messages),
                "next_indices_NOT_permission_to_send": {"question": 63, "npc": 63, "ordinary": 62},
                "ordinary62_not_applied_no_tool_replay": True},
    "actual_safe_error": diagnostic, "last8_calls": calls[-8:],
    "last60s_settled": {"calls": len(recent), "input_tokens": sum(c["input_tokens"] for c in recent),
                       "output_tokens": sum(c["output_tokens"] for c in recent),
                       "window_uses_our_created_timestamps_not_provider_bucket_accounting": True},
    "partial_actual_growth": growth,
    "partial_first3_actual_exchanges_public": [
        {"kind": e["kind"], "person_id": e["person_id"],
         "original_question_or_reply": e["content"].partition(
             "\nPublic read-source index (quoted mentions, not new grants):\n")[0],
         "full_content_sha256": hashlib.sha256(e["content"].encode()).hexdigest()}
        for e in [e for e in partial_runtime.history if e["kind"] in {"send_message", "read_messages"}][:6]],
    "remaining_targets_by_arm": dict(remaining_by_arm),
    "budget": {"v7_new_settled_USD_upper": str(spent), "cumulative_calls": 1964,
               "cumulative_settled": 1957, "cumulative_unknown": 7,
               "occupied_USD_upper": receipt["budget"]["occupied_USD_upper"],
               "remaining_USD": str(Decimal(50) - Decimal(receipt["budget"]["occupied_USD_upper"])),
               "unknown_held_USD": "6.006000", "in_flight": 0, "cap_USD": "50"},
    "v7_new_complete_costs": {a: {"n": counts[a], "sum_USD_upper": str(costs[a]),
                                 "mean_USD_upper": str(costs[a] / counts[a])} for a in "ABCD"},
    "remaining_cost_scenarios_NOT_guarantees": {
        "observed_v7_new_complete_arm_weighted_USD_upper": str(base),
        "twice_observed": str(base * 2), "four_times_observed": str(base * 4),
        "does_not_predict_alias_fix_effect_or_partial_completion": True,
        "prefix_cost_already_paid_diagnostic_tails_not_reclaimed": True,
        "complete_samples_exclude_partial_tail_so_may_underestimate": True,
        "tail_inclusive_incurred_mean_D_for43_unstarted_USD_lower_scenario": str(tail_inclusive),
        "tail_inclusive_excludes_already_paid_partial_and_unknown_reservation_but_needs_its_future_completion": True,
        "all64step_worst_case_not_guaranteed_to_fit": True},
    "v7_analysis": analysis, "no_new_API": True,
    "new_unknown_requires_explicit_recovery_not_automatic_rate_retry": True,
    "pacing_proposal_fixture_NOT_runtime_implementation": strict_json(
        (root.parent / "PHASE0_V8_PACING_PROPOSAL_FIXTURE.json").read_bytes()),
    "checker_sha256_LF": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
}
write_new(Path(sys.argv[3]), result)
print(json.dumps({k: result[k] for k in (
    "retained_complete", "all_AC_retained_together", "branches", "partial", "budget",
    "v7_new_complete_costs", "remaining_cost_scenarios_NOT_guarantees")}, ensure_ascii=True))
