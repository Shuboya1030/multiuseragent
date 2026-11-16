"""One explicitly authorized NPC6 attempt; never regenerate or resend the paid question."""
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
from .phase0 import (
    Journal, Phase0Mini, Phase0Runtime, build_request, episode, export_events, history_events,
    load_case, now, npc_system, public_sources, restore_public_state, write_new)
from .phase0_context_recovery import verify_history as verify_prior
from .request_pacing import CONFIG, PacedTransport

VERSION = "study4-phase0-reference-v8-npc6-continuation-1"
RUN_ID = "study4-phase0-reference-v8-path73-target167-npc6-20261115"
SOURCE = {"id": "de32a741-1d64-4655-bf85-6f5aeb4213ea", "revision": 2}
REVIEW = {
    "coordinator_session_id": "741f367f-a37b-48de-a57d-1e7bbe84ade4",
    "assignment_id": "assignment:741f367f-a37b-48de-a57d-1e7bbe84ade4:call_VQv0ZXPwbH68jQPq4hYIMj8g",
    "source": SOURCE, "attribution": "User approves one independent pending NPC6 attempt within original50",
}
INHERITED = {"calls": 2080, "settled_calls": 2072, "unknown_calls": 8,
             "settled_USD_upper": "23.0652996750", "unknown_held_USD": "6.864000"}
REPORT = "REFERENCE_V8_PACED_STOP_20261115.json"


def reviewed():
    return strict_json((Path(__file__).parent / "reports" / REPORT).read_bytes())


def selection():
    audit = reviewed()
    full = sorted([deepcopy(r["slot"]) for r in audit["analysis"]["rows"]] +
                  deepcopy(audit["analysis"]["missing_slots"]), key=lambda s: s["slot"])
    missing = {s["slot"] for s in audit["analysis"]["missing_slots"]}
    fresh = []
    for slot in full:
        if slot["slot"] in missing:
            slot["episode_id"] = "reference-v8-npc6:" + slot["episode_id"].removeprefix("reference-v8:")
            fresh.append(slot)
    require(len(full) == 240 and len({s["slot"] for s in full}) == 240 and len(fresh) == 167 and
            {a: sum(s["arm"] == a for s in fresh) for a in "ABCD"} ==
            {"A": 42, "B": 42, "C": 41, "D": 42}, "Whole73, one original partial,166 unstarted")
    return audit, full, fresh


def attempt_binding(fresh):
    audit = reviewed()
    boundary = audit["partial_recovery_boundary"]
    return {"old_call_id": audit["unknown"]["id"],
            "old_request_sha256": boundary["pending_NPC_request_sha256"],
            "new_episode_id": next(s["episode_id"] for s in fresh if s["slot"] == boundary["slot"]["slot"]),
            "operation": "npc", "index": 6, "max_new_attempts": 1, "old_unknown_preserved": True,
            "paid_question_not_regenerated_or_resent": True}


def verify_history(history, *, locked=False):
    require(len(history) == 14, "All2080 original calls required")
    verify_prior(history[:13], locked=locked)
    entry, audit = history[-1], reviewed()
    root = Path(entry["root"])
    for name, digest in entry["file_sha256"].items():
        if locked and name.endswith(".lock"):
            continue
        require(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
                "Original paced run immutable")
    old = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    receipt = strict_json((root / "FINAL_RECEIPT.json").read_bytes())
    require(old["history"] == history[:13] and fingerprint(old) == audit["plan_sha256"] and
            receipt["complete_episodes"] == 73 and receipt["budget"]["in_flight"] == 0 and
            receipt["budget"]["occupied_USD_upper"] == "29.9292996750", "Exact actual stopped root")
    db = sqlite3.connect((root / (old["run_id"] + ".sqlite3")).as_uri() + "?mode=ro", uri=True)
    try:
        rows = db.execute("select id,state,charged,input_tokens,output_tokens,request_sha256 from calls").fetchall()
    finally:
        db.close()
    from .budget import CallCaps
    settled, unknown = [r for r in rows if r[1] == "settled"], [r for r in rows if r[1] == "unknown"]
    require(len(rows) == 116 and len(settled) == 115 and len(unknown) == 1 and
            unknown[0][0] == audit["unknown"]["id"] and unknown[0][5] == audit["unknown"]["request_sha256"] and
            all(Decimal(r[2]) == CallCaps().charge(r[3], r[4]) for r in settled) and
            sum((Decimal(r[2]) for r in settled), Decimal(0)) == Decimal("0.8753901750"),
            "All settled charges checked, no uncertain release")
    return deepcopy(INHERITED)


def hydrate(root, slot):
    """Reconstruct exact post-send state by assignment, without calling any tool."""
    audit = reviewed()
    cert = audit["partial_recovery_boundary"]
    require(slot["slot"] == cert["slot"]["slot"], "Only original pending NPC6")
    old_id = cert["slot"]["episode_id"]
    events = [strict_json(line) for line in (Path(root) / "events.jsonl").read_bytes().splitlines()]
    failed = next(e for e in events if e["kind"] == "model_request" and
                  e["request_sha256"] == cert["pending_NPC_request_sha256"])
    question = next(e for e in events if e["kind"] == "model_request" and
                    e["episode_id"] == old_id and e["operation"] == "question" and e["index"] == 6)
    result = next(e["result"] for e in events if e["kind"] == "model_result" and
                  e["episode_id"] == old_id and e["operation"] == "question" and e["index"] == 6)
    incomplete = next(e for e in events if e["kind"] == "incomplete_episode" and
                      e["slot"]["episode_id"] == old_id)
    native = deepcopy(question["request"]["input"][1:-1])
    state = restore_public_state(strict_json(question["request"]["input"][-1]["content"])["state"], native)
    require(fingerprint(state) == cert["pre_question6_public_state_sha256"] and
            fingerprint(native) == cert["native_history_before_question6_sha256"] and
            fingerprint(incomplete["history"]) == cert["history_after_question6_send_sha256"] and
            history_events(native) == state["history"] == incomplete["history"][:-2],
            "Public history is exactly the paid question prefix plus original control/send")
    case = load_case(slot["task_id"])
    runtime = Phase0Runtime(case, slot["episode_id"])
    cache, dialogues = {}, {}
    for i, event in enumerate(incomplete["history"]):
        kind = event["kind"]
        if kind == "write_file":
            if event["path"] == case.public.artifact_path and runtime.workspace.get(event["path"]) != event["content"]:
                runtime.artifact_revision += 1
            runtime.workspace[event["path"]] = event["content"]
        elif kind == "post_channel" and (
                runtime.artifact_revision > 0 and case.public.artifact_path in event["content"] and
                event["content"].strip() != case.public.artifact_path):
            runtime.posted_revision = runtime.artifact_revision
        elif kind in {"send_message", "read_messages"}:
            person = event["person_id"]
            dialogues.setdefault(person, [{"role": "system", "content": npc_system(person, case.scenarios[person])}])
            dialogues[person].append({"role": "user" if kind == "send_message" else "assistant",
                                     "content": event["content"]})
            fields = ("message_id", "person_id", "content") if kind == "send_message" else (
                "message_id", "in_reply_to", "person_id", "content")
            runtime.messages[event["message_id"]] = {k: event[k] for k in fields}
            if kind == "send_message":
                runtime.messages[event["message_id"]]["sender"] = "agent"
                runtime.contacts += 1
                runtime.cost += case.costs[person]
            else:
                runtime.seen.add(event["message_id"])
                runtime.after_reply = True
                cache.setdefault(person, set()).update(s["source_id"] for s in public_sources(
                    {"history": incomplete["history"][:i]}))
    runtime.history, runtime.normal_actions = deepcopy(incomplete["history"]), incomplete["normal_actions"]
    outgoing = runtime.history[-1]
    require(runtime.workspace == incomplete["workspace"] == state["workspace"] and
            runtime.progress() == incomplete["progress"] == state["progress"] and
            runtime.contacts == 7 and len(runtime.seen) == 6 and runtime.normal_actions == 6 and
            runtime.cost == state["contact_cost"] + case.costs[outgoing["person_id"]] and
            outgoing == cert["last_outgoing_message"] and outgoing["kind"] == "send_message" and
            build_request("npc", dialogue=dialogues[outgoing["person_id"]]) == failed["request"] and
            fingerprint(failed["request"]) == cert["pending_NPC_request_sha256"],
            "Exact pending dialogue, no missing reply fabricated, no send/tool reapplied")
    require(incomplete["model_calls"] == cert["next_indices"], "Exact paid call indices")
    return runtime, native, dialogues, cache, deepcopy(incomplete["model_calls"]), deepcopy(result), len(state["history"])


def finish_pending(mini, runtime, paid_question, *, supplement):
    """Complete only the already-sent ASK, following Phase0Mini.ask after NPC call."""
    outgoing = runtime.history[-1]
    require(outgoing["kind"] == "send_message" and runtime.contacts == 7 and
            mini.indices == {"ordinary": 6, "question": 7, "npc": 6},
            "Pending NPC6 cannot replay an applied question/receipt")
    person = outgoing["person_id"]
    reply = mini.call("npc", person=person)["data"]["text"]
    if supplement:
        mini.known_sources.setdefault(person, set()).update(s["source_id"] for s in public_sources(runtime.observe()))
    mini.dialogues[person].append({"role": "assistant", "content": reply})
    message = {"message_id": outgoing["message_id"].removesuffix(":out") + ":reply",
               "in_reply_to": outgoing["message_id"], "person_id": person, "content": reply}
    runtime._deliver(message)
    mini.receipt(paid_question, runtime, {"status": "sent_and_read", "request_message_id": outgoing["message_id"],
                 "reply_message_id": message["message_id"], "ordinary_action_required_next": True})
    mini.ordinary(runtime, mini.call("ordinary", runtime.observe()))


def validate_review(plan, approval):
    audit, full, fresh = selection()
    require(plan["run_id"] == RUN_ID and plan["slots"] == full and plan["fresh_slots"] == fresh and
            plan["reference_recovery"] == {"version": VERSION, "reviewed_audit": fingerprint(audit),
                                          "review_release": REVIEW} and
            plan["inherited"] == INHERITED and plan["direct_user_source"] == SOURCE and
            plan["pacing"] == CONFIG and plan["unknown_attempt"] == attempt_binding(fresh) and
            approval.get("review_release") == REVIEW, "Exact one explicitly approved NPC6 attempt")
    old_runtime = audit["analysis"]
    require(old_runtime["complete_episodes"] == 73 and not old_runtime["private_review_queue"],
            "All original73 complete and reviewed, not result screened")
    original = strict_json((Path(__file__).parent / "reports" /
                            "REFERENCE_V8_PACED_EXECUTION_AC26_20261113.json").read_bytes())
    cohort = plan["execution_cohort_audit"]
    require(cohort["current_runtime_binding"] == plan["runtime"] and
            all(cohort[k] == original[k] for k in ("rows", "contracts", "checker_sha256_LF")) and
            cohort["retained_complete_episodes"] == 26, "Entire original26 AC unchanged")
    prior_binding = original["current_runtime_binding"]
    require(all(v == plan["runtime"][k] for k, v in prior_binding.items() if k != "phase0_sources") and
            all(plan["runtime"]["phase0_sources"][k] == v for k, v in prior_binding["phase0_sources"].items()
                if k != "phase0_admission.py"), "Only recovery admission changes; scientific paths unchanged")


def freeze(root, prior, cohort_path):
    from .admission import root_binding, validate_binding
    from .phase0_admission import make_plan
    root, prior = Path(root).resolve(), Path(prior).resolve()
    require(not root.exists(), "Never replace an attempted root")
    old = strict_json((prior / "FROZEN_PLAN.json").read_bytes())
    history = deepcopy(old["history"]) + [{"root": str(prior), "file_sha256": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in prior.iterdir() if p.is_file()}}]
    verify_history(history)
    audit, full, fresh = selection()
    plan = make_plan(history, INHERITED, local_test=True)
    plan.update(run_id=RUN_ID, mode="provider", endpoint="https://api.openai.com/v1/responses",
                slots=full, fresh_slots=fresh, episodes=[s["episode_id"] for s in fresh],
                max_calls=167 * 192, max_episodes=167, total_input_tokens=167 * 192 * 272000,
                total_output_tokens=167 * 192 * 128000, direct_user_source=deepcopy(SOURCE),
                execution_cohort_audit=strict_json(Path(cohort_path).read_bytes()), pacing=deepcopy(CONFIG),
                reference_progress="study4-reference-completion-8-public-context",
                reference_recovery={"version": VERSION, "reviewed_audit": fingerprint(audit),
                                    "review_release": deepcopy(REVIEW)}, unknown_attempt=attempt_binding(fresh))
    hydrate(prior, next(s for s in fresh if s["slot"] == audit["partial_recovery_boundary"]["slot"]["slot"]))
    plan["code_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    at = datetime.now(timezone.utc)
    approval = {"approved": True, "run_id": RUN_ID, "plan_sha256": fingerprint(plan),
                "storage_root_sha256": root_binding(root), "budget_cap_USD": "50.00",
                "direct_user_source": SOURCE, "review_release": REVIEW,
                "scope": "STUDY4_FORMAL_PHASE0_240_PATH73_TARGET167_NPC6_SAME50",
                "not_before": at.isoformat(), "expires": (at + timedelta(days=7)).isoformat(),
                "reference": REVIEW["assignment_id"]}
    validate_binding(plan, approval, root, plan["endpoint"])
    root.mkdir(parents=True)
    write_new(root / "FROZEN_PLAN.json", plan)
    write_new(root / "APPROVAL.json", approval)
    write_new(root / "AUTHORIZATION_SOURCE.json", {"direct_user_text": "继续运行吧", "direct_user_source": SOURCE,
              "coordinator_selection_NOT_verbatim_user_text": REVIEW, "cap_USD": "50", "inherited": INHERITED,
              "old_unknown_not_released": True, "one_new_NPC6_attempt_not_unlimited_retries": True})
    return {"frozen": True, "plan_sha256": fingerprint(plan), "retained": 73, "targets": 167}


def run(root, plan, approval, transport):
    from .admission import validate_binding
    from .budget import BudgetBlocked
    from .durable import BatchLock, DurableLedger
    root = Path(root)
    validate_binding(plan, approval, root, transport.endpoint)
    require(not (root / "STARTED.json").exists(), "Do not restart interrupted namespaces")
    verify_history(plan["history"])
    audit = reviewed()
    prior = Path(plan["history"][-1]["root"])
    retained = {r["slot"]["slot"] for r in audit["analysis"]["rows"]}
    partial = audit["partial_recovery_boundary"]["slot"]["slot"]
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
        paced = PacedTransport(transport, journal)
        write_new(root / "STARTED.json", {"at": now(), "plan_sha256": fingerprint(plan),
                                         "direct_user_source": SOURCE, "pacing": CONFIG})
        try:
            shutil.copyfile(prior / "REVIEWS_STOP003.json", root / "REVIEWS_RETAINED.json")
            for slot in plan["slots"]:
                if slot["slot"] not in retained:
                    continue
                path = prior / f"slot-{slot['slot']:03d}.json"
                record = strict_json(path.read_bytes())
                require(record["slot"] == slot, "Original whole73 record identity")
                shutil.copyfile(path, root / path.name)
                row = {k: record[k] for k in ("slot", "official_raw", "progress", "model_calls")}
                completed.append(row)
                groups.setdefault(slot["group"], []).append(row)
                journal.append({"kind": "retained_record", "slot": slot, "source_record_sha256": fingerprint(record)})
            for slot in plan["fresh_slots"]:
                mini = Phase0Mini(ledger, paced, slot, journal)
                runtime = None
                if slot["slot"] == partial:
                    runtime, mini.history, mini.dialogues, mini.known_sources, mini.indices, paid, mini.event_cursor = (
                        hydrate(prior, slot))
                    journal.append({"kind": "continued_paid_prefix", "slot": slot, "source_root": str(prior),
                                    "audit_sha256": fingerprint(audit), "next_indices": mini.indices,
                                    "public_state_sha256": fingerprint(runtime.observe()),
                                    "paid_question_result_sha256": fingerprint(paid)})
                    def event(e):
                        e["timestamp"] = now()
                        runtime.history[-1]["timestamp"] = e["timestamp"]
                        journal.append({"kind": "runtime_event", "episode_id": runtime.episode_id, "event": e})
                    runtime.event_sink = event
                    require(fingerprint(build_request("npc", dialogue=mini.dialogues[
                        runtime.history[-1]["person_id"]])) == plan["unknown_attempt"]["old_request_sha256"],
                        "One new attempt must be byte-identical to the actual pending NPC request")
                    journal.append({"kind": "explicit_unknown_new_attempt", "binding": plan["unknown_attempt"],
                                    "direct_user_source": SOURCE, "old_unknown_not_released": True})
                    try:
                        finish_pending(mini, runtime, paid, supplement=slot["arm"] in {"C", "D"})
                    except BaseException as error:
                        journal.append({"kind": "incomplete_episode", "slot": slot, "complete": False,
                                        "error_type": type(error).__name__, "business_outcome": None,
                                        "workspace": runtime.workspace, "events": export_events(runtime),
                                        "history": runtime.history, "progress": runtime.progress(),
                                        "model_calls": mini.indices, "normal_actions": runtime.normal_actions})
                        raise
                    journal.append({"kind": "pending_NPC_receipt_and_ordinary_completed", "slot": slot,
                                    "next_indices": mini.indices, "normal_actions": runtime.normal_actions,
                                    "contacts": runtime.contacts})
                    print(canonical({"kind": "actual_NPC6_recovered_no_question_or_send_replay",
                                     "slot": slot, "budget": ledger.status()}), flush=True)
                else:
                    journal.append({"kind": "episode_start", "slot": slot})
                record = episode(load_case(slot["task_id"]), slot, mini, journal, runtime=runtime)
                if runtime is not None:
                    record["continued_source_audit"] = fingerprint(audit)
                write_new(root / f"slot-{slot['slot']:03d}.json", record)
                row = {k: record[k] for k in ("slot", "official_raw", "progress", "model_calls")}
                completed.append(row)
                group = groups.setdefault(slot["group"], [])
                group.append(row)
                if len(group) == 4:
                    print(canonical({"kind": "complete_four_arm_block", "rows": group, "budget": ledger.status()}), flush=True)
        except BaseException as error:
            status = "budget_stopped" if isinstance(error, BudgetBlocked) and ledger.status()["unknown"] == 0 else "stopped"
            failure = type(error).__name__
        verify_history(plan["history"], locked=True)
        receipt = {"schema": VERSION, "status": status, "error_type": failure,
                   "complete_episodes": len(completed), "complete_four_arm_blocks": sum(len(g) == 4 for g in groups.values()),
                   "retained_complete_episodes": 73, "fresh_complete_episodes": len(completed) - 73,
                   "completed": completed, "budget": ledger.status(), "automatic_retry": False,
                   "incomplete_not_business_zero": True, "finished": now()}
        write_new(root / "FINAL_RECEIPT.json", receipt)
    verify_history(plan["history"])
    return receipt


if __name__ == "__main__":
    import argparse
    import os
    from .admission import validate_binding
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--prior-root", type=Path)
    parser.add_argument("--cohort", type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        print(canonical(freeze(args.root, args.prior_root, args.cohort)))
    else:
        plan = strict_json((args.root / "FROZEN_PLAN.json").read_bytes())
        approval = strict_json((args.root / "APPROVAL.json").read_bytes())
        validate_binding(plan, approval, args.root, plan["endpoint"])
        verify_history(plan["history"])
        if args.check:
            print(canonical({"checked": True, "plan_sha256": fingerprint(plan), "inherited": INHERITED}))
        else:
            from .http_transport import HTTPTransport
            key = os.environ.get("OPENAI_API_KEY")
            require(key, "Existing authorized ephemeral credential required")
            result = run(args.root, plan, approval, HTTPTransport(plan["endpoint"], "provider", credential=key))
            print(canonical({k: result[k] for k in ("status", "error_type", "complete_episodes", "budget")}))
