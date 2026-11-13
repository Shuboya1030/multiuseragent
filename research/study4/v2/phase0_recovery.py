"""Approved reference-v6 continuation, hydrating the settled prefix without replay."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
from pathlib import Path
import shutil
import sqlite3
import subprocess

from .contracts import canonical, fingerprint, require, strict_json
from .phase0 import (SOURCE, VERSION, Phase0Mini, episode, load_case, now, schedule,
                     verify_inherited, write_new, Journal, Phase0Runtime, build_request,
                     history_events, restore_public_state, npc_system, scorer)

RECOVERY = "study4-phase0-reference-v6-conflict-continuation-1"
RUN_ID = "study4-phase0-reference-v6-AC26-prefix18-fresh213-20261112"
CONTINUE_SOURCE = {"id": "f69f8951-214c-43f8-ad71-d57bb64d9573", "revision": 13}
PREFIX_PLAN = "f055257f6f16ef807f50bb8b9d6b718456e06c7e6dc966bcedd06b61ee7ef43c"
PREFIX_EPISODE = "reference-v5:phase0:m-med-service-credit:B:r0"
PREFIX_PROOF_SHA = "864887d78c56a4a33eaa61281f452f71e073238f4f5504d17b7b73ed588d7827"
REVIEWED = "21c36555e2c031b631a40f1ab0bda9a7ecac33efc6fab04332af0b46f8142c3e"
PARENT_PLAN = "10becfc13f4c3d39ce39fc0098775b8a87c4f190d7927d59b92bc2421fe6ae23"
PARENT_LEDGER = "fc6b9248e775db250682dd70af23caffb1956c5868114b429acff4f6f4d1537b"
REVIEW = {
    "coordinator_session_id": "741f367f-a37b-48de-a57d-1e7bbe84ade4",
    "assignment_id": "assignment:741f367f-a37b-48de-a57d-1e7bbe84ade4:call_aGDv7TIetvAn4IU0CUgUSo0b",
    "release_message_tool_call_id": "call_aGDv7TIetvAn4IU0CUgUSo0b",
    "attribution": "Agent explanation of approved conflict contract; direct revision13 is separately bound",
    "original_direct_user_source": SOURCE,
    "continuation_direct_user_source": CONTINUE_SOURCE,
}
BASE_INHERITED = {"unknown_held_USD": "5.148000", "settled_USD_upper": "10.481236425",
                  "calls": 1022, "settled_calls": 1016, "unknown_calls": 6}
INHERITED = {"unknown_held_USD": "5.148000", "settled_USD_upper": "10.5353333250",
             "calls": 1040, "settled_calls": 1034, "unknown_calls": 6}
REPORTS = Path(__file__).parent / "reports"


def selection():
    proof = strict_json((REPORTS / "REFERENCE_V5_AC26_FRESH214_20261112.json").read_bytes())
    require(fingerprint(proof) == REVIEWED, "Exact reviewed fixed-cohort proof required")
    retained = {r["slot"]["slot"] for r in proof["rows"] if r["retain_in_formal_cohort"]}
    full = deepcopy(schedule())
    for slot in full:
        if slot["slot"] not in retained:
            slot["episode_id"] = ("reference-v5:" if slot["slot"] == 1 else "reference-v6:") + slot["episode_id"]
    fresh = [s for s in full if s["slot"] not in retained]
    require(len(retained) == 26 and len(fresh) == 214 and
            {a: sum(s["arm"] == a for s in fresh) for a in "ABCD"} ==
            {"A": 47, "B": 60, "C": 47, "D": 60}, "Whole fixed A/C cohort; all B/D fresh")
    return proof, full, fresh


def verify_base_history(history, *, locked=False):
    require(len(history) == 10, "All9predecessors plus paused52 root required")
    verify_inherited(history[:9], locked=locked)
    last = history[-1]
    root = Path(last["root"])
    for name, digest in last["file_sha256"].items():
        if locked and name.endswith(".lock"):
            continue
        require(Path(name).name == name and hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
                "Paused52 evidence bytes changed")
    prior = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    require(fingerprint(prior) == PARENT_PLAN and prior["history"] == history[:9],
            "Exact paused52 lineage, not a new50")
    ledger = root / (prior["run_id"] + ".sqlite3")
    require(hashlib.sha256(ledger.read_bytes()).hexdigest() == PARENT_LEDGER, "Paused52 ledger changed")
    db = sqlite3.connect(ledger.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        rows = db.execute("select state,reserved,charged,input_tokens,output_tokens from calls").fetchall()
    finally:
        db.close()
    from .budget import CallCaps
    require(len(rows) == 643 and all(
        state == "settled" and Decimal(reserve) == Decimal(".858") and
        Decimal(charged) == CallCaps().charge(incoming, outgoing)
        for state, reserve, charged, incoming, outgoing in rows), "No partial billing/released unknown")
    require(sum((Decimal(r[2]) for r in rows), Decimal(0)) == Decimal("6.5190114000"),
            "Retain every paused52call including unexecuted last tool")
    return deepcopy(BASE_INHERITED)


def verify_history(history, *, locked=False):
    require(len(history) == 11, "All1040calls including settled18prefix required")
    verify_base_history(history[:10], locked=locked)
    entry, root = history[-1], Path(history[-1]["root"])
    for name, digest in entry["file_sha256"].items():
        if locked and name.endswith(".lock"):
            continue
        require(Path(name).name == name and hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
                "Stopped18prefix evidence bytes changed")
    plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    receipt = strict_json((root / "FINAL_RECEIPT.json").read_bytes())
    require(fingerprint(plan) == PREFIX_PLAN and plan["history"] == history[:10] and
            receipt["error_type"] == "ReferenceUncertain" and
            receipt["fresh_complete_episodes"] == 0 and receipt["retained_complete_episodes"] == 26 and
            receipt["budget"]["in_flight"] == receipt["budget"]["unknown"] == 0,
            "Exact safe post-ordinary18call stop required")
    db = sqlite3.connect((root / (plan["run_id"] + ".sqlite3")).resolve().as_uri() +
                         "?mode=ro&immutable=1", uri=True)
    try:
        rows = db.execute("select episode,state,charged,input_tokens,output_tokens from calls").fetchall()
    finally:
        db.close()
    from .budget import CallCaps
    require(len(rows) == 18 and all(ep == PREFIX_EPISODE and state == "settled" and
            Decimal(charged) == CallCaps().charge(incoming, outgoing)
            for ep, state, charged, incoming, outgoing in rows) and
            sum((Decimal(r[2]) for r in rows), Decimal(0)) == Decimal(".0540969000"),
            "Every prefix charge remains counted; no unknown or unexecuted result")
    return deepcopy(INHERITED)


def prefix_state(root):
    """Hydrate persisted state/receipts, without calling a model or executing a tool."""
    root = Path(root)
    entries = [strict_json(line) for line in (root / "events.jsonl").read_bytes().splitlines()]
    partials = [x for x in entries if x["kind"] == "incomplete_episode"]
    require(len(partials) == 1 and partials[0]["error_type"] == "ReferenceUncertain",
            "One certified post-ordinary prefix only")
    partial = partials[0]
    slot = partial["slot"]
    require(slot["episode_id"] == PREFIX_EPISODE and slot["slot"] == 1 and slot["arm"] == "B" and
            partial["model_calls"] == {"question": 6, "npc": 6, "ordinary": 6} and
            partial["normal_actions"] == 6, "No arbitrary interrupted trajectory recovery")
    events = [e["event"] for e in entries if e["kind"] == "runtime_event"]
    require(events == partial["history"], "Public snapshot/event evidence mismatch")
    requests = [x for x in entries if x["kind"] == "model_request"]
    results = [x for x in entries if x["kind"] == "model_result"]
    require(len(requests) == len(results) == 18 and
            [(x["operation"], x["index"]) for x in requests] ==
            [(op, i) for i in range(6) for op in ("question", "npc", "ordinary")],
            "All six ASK/read/ordinary cycles settled, no pending model response")
    plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    require(fingerprint(plan) == PREFIX_PLAN, "Exact prefix plan required")
    db = sqlite3.connect((root / (plan["run_id"] + ".sqlite3")).resolve().as_uri() +
                         "?mode=ro&immutable=1", uri=True)
    try:
        ledger = {row[0]: row[1:] for row in db.execute(
            "select id,state,request_sha256,result,result_sha256 from calls")}
    finally:
        db.close()
    for request, result in zip(requests, results):
        require((request["operation"], request["index"]) == (result["operation"], result["index"]),
                "Ordered model-result binding required")
        wire = request["request"]
        if request["operation"] == "npc":
            rebuilt = build_request("npc", dialogue=wire["input"])
        else:
            body, history = strict_json(wire["input"][-1]["content"]), wire["input"][1:-1]
            rebuilt = build_request(body["mode"], restore_public_state(body["state"], history),
                                    person=body["person_id"], history=history)
        row = ledger[f"{PREFIX_EPISODE}:{request['operation']}:{request['index']}"]
        stored = {k: v for k, v in result["result"].items() if k != "replayed_without_send"}
        require(fingerprint(rebuilt) == request["request_sha256"] == row[1] and row[0] == "settled" and
                strict_json(row[2]) == stored and fingerprint(stored) == row[3] and
                result["result"]["replayed_without_send"] is False, "Exact paid prefix request/result proof")
    case = load_case(slot["task_id"])
    runtime = Phase0Runtime(case, PREFIX_EPISODE)
    require(len(events) == 24, "Six complete four-event ASK/read/ordinary cycles required")
    for i in range(6):
        control, send, read, applied = events[4 * i:4 * i + 4]
        question, npc, ordinary = [x["result"]["data"] for x in results[3 * i:3 * i + 3]]
        args = ordinary["arguments"]
        require(control["kind"] == "control_decision" and control["action"] == "ASK" and
                question["tool"] == "ask_colleague" and send["kind"] == "send_message" and
                send["content"] == question["arguments"]["question"] and
                control["person_id"] == send["person_id"] == read["person_id"] ==
                question["arguments"]["person_id"] and read["kind"] == "read_messages" and
                read["in_reply_to"] == send["message_id"] and read["content"] == npc["text"],
                "Each actual question and NPC result must already be delivered once")
        require((ordinary["tool"] == "submit" and applied["kind"] == "submission_blocked") or
                (applied["kind"] == ordinary["tool"] and all(applied.get(k) == v for k, v in args.items())) or
                (applied["kind"] == "tool_result" and applied["tool"] == ordinary["tool"] and
                 all(applied.get(k) == v for k, v in args.items())),
                "Every paid ordinary result must have its matching applied event, not a pending tool")
    actions = 0
    for event in events:
        kind = event["kind"]
        if kind == "write_file":
            if event["path"] == case.public.artifact_path and runtime.workspace.get(event["path"]) != event["content"]:
                runtime.artifact_revision += 1
            runtime.workspace[event["path"]] = event["content"]
        elif kind == "post_channel":
            if (runtime.artifact_revision > 0 and case.public.artifact_path in event["content"] and
                    event["content"].strip() != case.public.artifact_path):
                runtime.posted_revision = runtime.artifact_revision
        elif kind == "send_message":
            runtime.messages[event["message_id"]] = {k: event[k] for k in (
                "message_id", "person_id", "content")}
            runtime.messages[event["message_id"]]["sender"] = "agent"
            runtime.contacts += 1
            runtime.cost += case.costs[event["person_id"]]
        elif kind == "read_messages":
            runtime.messages[event["message_id"]] = {k: event[k] for k in (
                "message_id", "in_reply_to", "person_id", "content")}
            runtime.seen.add(event["message_id"])
            runtime.after_reply = True
        require(kind in {"write_file", "post_channel", "send_message", "read_messages",
                         "control_decision", "tool_result", "submission_blocked"},
                "Unexpected prefix state transition, no guess/replay")
        actions += kind in {"write_file", "post_channel", "tool_result", "submission_blocked"}
    runtime.history, runtime.normal_actions = deepcopy(events), actions
    require(actions == 6 and runtime.contacts == 6 and runtime.cost == 18 and
            runtime.workspace == partial["workspace"] and runtime.progress() == partial["progress"] and
            events[-1]["kind"] == "submission_blocked" and
            results[-1]["result"]["data"]["tool"] == "submit",
            "All six ordinary actions already applied, final blocked submit cannot be re-executed")
    native_history = deepcopy(requests[-1]["request"]["input"][1:-1])
    cursor = len(history_events(native_history))
    require(events[:cursor] == history_events(native_history) and cursor == len(events) - 1,
            "All prior matched native receipts retained; exactly one final ordinary receipt to hydrate")
    function = results[-1]["result"]["native_function"]
    native_history.extend(deepcopy(function["output_items"]))
    native_history.append({"type": "function_call_output", "call_id": function["call_id"],
                           "output": canonical({"progress": runtime.progress(), "events": events[cursor:]})})
    npc_request, npc_result = requests[-2]["request"], results[-2]["result"]
    person = events[-2]["person_id"]
    dialogue = deepcopy(npc_request["input"]) + [{"role": "assistant", "content": npc_result["data"]["text"]}]
    actual_dialogue = [{"role": "system", "content": npc_system(person, case.scenarios[person])}] + [
        {"role": "user" if e["kind"] == "send_message" else "assistant", "content": e["content"]}
        for e in events if e["kind"] in {"send_message", "read_messages"}]
    require(dialogue == actual_dialogue and history_events(native_history) == events,
            "Complete same-person NPC dialogue and public native receipts required")
    proof = {"prefix_plan_sha256": PREFIX_PLAN, "episode_id": PREFIX_EPISODE,
             "settled_calls": 18, "ordinary_actions_already_applied": actions, "contacts": runtime.contacts,
             "history_sha256": fingerprint(events), "workspace_sha256": fingerprint(runtime.workspace),
             "native_history_sha256": fingerprint(native_history), "dialogue_sha256": fingerprint(dialogue),
             "request_fingerprints": [r["request_sha256"] for r in requests],
             "next_indices": partial["model_calls"], "no_model_or_tool_reexecution": True}
    return runtime, native_history, {person: dialogue}, proof


def validate_review(plan, approval):
    proof, full, fresh = selection()
    require(plan["reference_recovery"] == {
        "version": RECOVERY, "reviewed_manifest_fingerprint": REVIEWED,
        "review_release": REVIEW, "retained_slots": [s["slot"] for s in full if s not in fresh],
        "old_partial52_not_resumed": True, "all_BD_not_selected_by_results": True,
        "paid_prefix18_continued_without_replay": True},
        "Only approved conflict-contract continuation; no B/D resampling")
    require(plan["run_id"] == RUN_ID and plan["slots"] == full and plan["fresh_slots"] == fresh and
            plan["episodes"] == [s["episode_id"] for s in fresh] and
            plan["inherited"] == INHERITED and len(plan["history"]) == 11 and
            plan["direct_user_source"] == CONTINUE_SOURCE and
            approval.get("review_release") == REVIEW,
            "Exact new namespace/cohort/original cumulative accounting")
    audit = plan["execution_cohort_audit"]
    require(audit["current_runtime_binding"] == plan["runtime"] and
            all(audit[k] == proof[k] for k in ("remaining_manifest", "retained_counts_by_arm",
                                              "rows", "contracts", "budget", "source_rule_coverage")) and
            audit["reference_source_sha256_LF"] == plan["runtime"]["phase0_sources"]["reference_completion.py"] and
            audit["episode_optional_hydrated_runtime_only_default_branch_AST_identical"] is True,
            "Post-admission source audit must cover whole fixed A/C group")
    require(fingerprint(plan["prefix_proof"]) == PREFIX_PROOF_SHA,
            "Only certified fully applied18call prefix may continue")


def make_plan(prior_root, audit):
    from .phase0_admission import make_plan as base_plan
    prior_root = Path(prior_root).resolve()
    prior = strict_json((prior_root / "FROZEN_PLAN.json").read_bytes())
    require(fingerprint(prior) == PREFIX_PLAN, "Exact stopped18 source required")
    history = deepcopy(prior["history"]) + [{
        "root": str(prior_root), "file_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in prior_root.iterdir() if p.is_file()}}]
    inherited = verify_history(history)
    proof, full, fresh = selection()
    plan = base_plan(history, inherited, local_test=True)
    plan.update(run_id=RUN_ID, mode="provider", endpoint="https://api.openai.com/v1/responses",
                slots=full, fresh_slots=fresh, episodes=[s["episode_id"] for s in fresh],
                max_calls=214 * 192, max_episodes=214,
                total_input_tokens=214 * 192 * 272000, total_output_tokens=214 * 192 * 128000,
                fresh_only=True, execution_cohort_audit=audit,
                direct_user_source=deepcopy(CONTINUE_SOURCE),
                prefix_proof=prefix_state(prior_root)[-1],
                reference_progress="study4-reference-completion-6-truth-preserving-conflict-diagnostics",
                reference_recovery={"version": RECOVERY, "reviewed_manifest_fingerprint": REVIEWED,
                    "review_release": deepcopy(REVIEW),
                    "retained_slots": [r["slot"]["slot"] for r in proof["rows"] if r["retain_in_formal_cohort"]],
                    "old_partial52_not_resumed": True, "all_BD_not_selected_by_results": True,
                    "paid_prefix18_continued_without_replay": True})
    return plan


def freeze(root, prior_root, audit_path):
    from .admission import root_binding, validate_binding
    root = Path(root).resolve()
    require(not root.exists(), "Never replace an existing frozen/attempted recovery")
    audit = strict_json(Path(audit_path).read_bytes())
    plan = make_plan(prior_root, audit)
    plan["code_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    at = datetime.now(timezone.utc)
    approval = {"approved": True, "run_id": RUN_ID, "plan_sha256": fingerprint(plan),
                "storage_root_sha256": root_binding(root), "budget_cap_USD": "50.00",
                "direct_user_source": CONTINUE_SOURCE, "review_release": REVIEW,
                "scope": "STUDY4_FORMAL_PHASE0_240_AC26_FRESH214_SAME50",
                "not_before": at.isoformat(), "expires": (at + timedelta(hours=24)).isoformat(),
                "reference": REVIEW["assignment_id"]}
    validate_binding(plan, approval, root, plan["endpoint"])
    root.mkdir(parents=True)
    write_new(root / "FROZEN_PLAN.json", plan)
    write_new(root / "APPROVAL.json", approval)
    write_new(root / "AUTHORIZATION_SOURCE.json", {
        "direct_user_source": CONTINUE_SOURCE, "direct_user_text": "同意你的决策，请你按照这个来继续",
        "original_scope_source": SOURCE, "agent_contract_explanation": REVIEW,
        "review_pause_was_agent_not_later_user_restriction": True,
        "original_cap_USD": "50.00", "new_budget": False, "inherited": INHERITED})
    return {"frozen": True, "plan_sha256": fingerprint(plan), "fresh": 214, "retained": 26}


def run(root, plan, approval, transport):
    from .admission import validate_binding
    from .budget import BudgetBlocked
    from .durable import BatchLock, DurableLedger
    root = Path(root)
    validate_binding(plan, approval, root, transport.endpoint)
    require(not (root / "STARTED.json").exists(), "Interrupted recovery cannot replay calls or tools")
    verify_history(plan["history"])
    proof, _, _ = selection()
    retained = {r["slot"]["slot"]: r for r in proof["rows"] if r["retain_in_formal_cohort"]}
    completed, groups, status, failure = [], {}, "complete", None
    with ExitStack() as stack:
        for entry in plan["history"]:
            name = next(n for n in entry["file_sha256"] if n.endswith(".sqlite3")).removesuffix(".sqlite3")
            stack.callback(BatchLock(Path(entry["root"]) / (name + ".lock")).close)
        verify_history(plan["history"], locked=True)
        ledger = DurableLedger(root, plan, approval, create=True)
        stack.callback(ledger.close)
        journal = Journal(root / "events.jsonl")
        stack.callback(journal.close)
        write_new(root / "STARTED.json", {"at": now(), "plan_sha256": fingerprint(plan),
                                         "direct_user_source": CONTINUE_SOURCE, "review_release": REVIEW})
        try:
            review_path = root / "REVIEWS_RETAINED_AC.json"
            require(not review_path.exists(), "Never replace a review overlay")
            shutil.copyfile(Path(plan["history"][-1]["root"]) / "REVIEWS_RETAINED_AC_FINAL.json",
                            review_path)
            # Preserve the entire predefined cohort before the first new POST.
            for slot in plan["slots"]:
                if slot["slot"] not in retained:
                    continue
                path = root / f"slot-{slot['slot']:03d}.json"
                old = Path(plan["history"][-2]["root"]) / path.name
                require(hashlib.sha256(old.read_bytes()).hexdigest() ==
                        retained[slot["slot"]]["actual_record_sha256"], "Retained group record drift")
                require(not path.exists(), "No overwrite/replay of retained evidence")
                shutil.copyfile(old, path)
                record = strict_json(path.read_bytes())
                journal.append({"kind": "retained_record", "slot": slot,
                                "source_sha256": retained[slot["slot"]]["actual_record_sha256"]})
                row = {"slot": slot, "official_raw": record["official_raw"],
                       "progress": record["progress"], "model_calls": record["model_calls"]}
                completed.append(row)
                groups.setdefault(slot["group"], []).append(row)
            for slot in plan["fresh_slots"]:
                mini = Phase0Mini(ledger, transport, slot, journal)
                runtime = None
                if slot["episode_id"] == PREFIX_EPISODE:
                    runtime, mini.history, mini.dialogues, prefix = prefix_state(plan["history"][-1]["root"])
                    require(prefix == plan["prefix_proof"], "Certified prefix hydration changed")
                    mini.indices = deepcopy(prefix["next_indices"])
                    mini.event_cursor = len(runtime.history)
                    journal.append({"kind": "continued_paid_prefix", "slot": slot, "proof": prefix,
                                    "source_root": plan["history"][-1]["root"]})
                else:
                    journal.append({"kind": "episode_start", "slot": slot})
                record = episode(load_case(slot["task_id"]), slot, mini, journal, runtime=runtime)
                if slot["episode_id"] == PREFIX_EPISODE:
                    record["continued_paid_prefix"] = plan["prefix_proof"]
                write_new(root / f"slot-{slot['slot']:03d}.json", record)
                row = {"slot": slot, "official_raw": record["official_raw"],
                       "progress": record["progress"], "model_calls": record["model_calls"]}
                completed.append(row)
                block = groups.setdefault(slot["group"], [])
                block.append(row)
                if len(block) == 4:
                    print(canonical({"kind": "complete_four_arm_block", "rows": block,
                                     "budget": ledger.status()}), flush=True)
        except BaseException as error:
            status = "budget_stopped" if isinstance(error, BudgetBlocked) and ledger.status()["unknown"] == 0 else "stopped"
            failure = type(error).__name__
        verify_history(plan["history"], locked=True)
        receipt = {"schema": RECOVERY, "status": status, "error_type": failure,
                   "complete_episodes": len(completed),
                   "complete_four_arm_blocks": sum(len(g) == 4 for g in groups.values()),
                   "retained_complete_episodes": sum(r["slot"]["slot"] in retained for r in completed),
                   "fresh_complete_episodes": sum(r["slot"]["slot"] not in retained for r in completed),
                   "completed": completed, "budget": ledger.status(),
                   "automatic_retry": False, "incomplete_not_business_zero": True, "finished": now()}
        write_new(root / "FINAL_RECEIPT.json", receipt)
    verify_history(plan["history"])
    return receipt


if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--prior-root", type=Path)
    parser.add_argument("--audit", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        print(canonical(freeze(args.root, args.prior_root, args.audit)))
    else:
        from .admission import validate_binding
        plan = strict_json((args.root / "FROZEN_PLAN.json").read_bytes())
        approval = strict_json((args.root / "APPROVAL.json").read_bytes())
        validate_binding(plan, approval, args.root, plan["endpoint"])
        verify_history(plan["history"])
        require(not (args.root / "STARTED.json").exists(), "No interrupted recovery replay")
        if args.check:
            print(canonical({"binding_verified_before_key": True, "fresh": len(plan["fresh_slots"]),
                             "retained": 26, "inherited": plan["inherited"]}))
        else:
            from .http_transport import HTTPTransport
            key = os.environ.get("OPENAI_API_KEY")
            require(isinstance(key, str) and key, "Existing process-only authorized credential missing")
            transport = HTTPTransport(plan["endpoint"], plan["mode"], credential=key,
                                      timeout=plan["http_timeout_seconds"],
                                      max_response_bytes=plan["max_response_bytes"])
            receipt = run(args.root, plan, approval, transport)
            print(canonical({"kind": "recovery_terminal", **{k: receipt[k] for k in (
                "status", "error_type", "complete_episodes", "complete_four_arm_blocks",
                "fresh_complete_episodes", "retained_complete_episodes", "budget")}}))
