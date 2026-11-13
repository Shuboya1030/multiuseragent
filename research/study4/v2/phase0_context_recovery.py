"""Approved v8 paths66+targets174, one explicit unknown attempt, shared pacing."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
from pathlib import Path
import shutil
import sqlite3
import subprocess

from .contracts import fingerprint, require, strict_json, canonical
from .phase0 import (
    Phase0Mini, Phase0Runtime, build_request, episode, history_events, load_case, now, npc_system,
    public_sources, restore_public_state, write_new)
from .request_pacing import CONFIG, PacedTransport
from .phase0_derivation_recovery import verify_history as verify_old_history

VERSION = "study4-phase0-reference-v8-paced-continuation-1"
RUN_ID = "study4-phase0-reference-v8-path66-target174-paced-20261113"
SOURCE = {"id": "e7a380f6-ea65-4840-ad16-6d3ff182707d", "revision": 2}
DELEGATION = {"id": "436cdf88-6a13-40ae-8627-2cf2ea0fc274", "revision": 1}
REVIEW = {
    "coordinator_session_id": "741f367f-a37b-48de-a57d-1e7bbe84ade4",
    "assignment_id": "assignment:741f367f-a37b-48de-a57d-1e7bbe84ade4:call_4MYPAdmnnTXjbfxy788Jnmgy",
    "delegation_call": "call_4MYPAdmnnTXjbfxy788Jnmgy",
    "confirmation_call": "call_j8L2v7imNyQa0bEKlnOtrDlx",
    "delegation_source": DELEGATION, "confirmation_source": SOURCE,
    "attribution": "User delegates rate handling and confirms; coordinator selects original50 paced recovery",
}
INHERITED = {"calls": 1964, "settled_calls": 1957, "unknown_calls": 7,
             "settled_USD_upper": "22.1899095000", "unknown_held_USD": "6.006000"}
REPORT = "REFERENCE_V8_CONTEXT_RATE_BOUNDARY_20261113.json"


def reviewed():
    return strict_json((Path(__file__).parent / "reports" / REPORT).read_bytes())


def selection():
    audit = reviewed()
    require(audit["retained_complete"] == 66 and len(audit["branches"]) == 1 and
            audit["partial"]["188_settled_request_result_bindings_checked"],
            "Exact whole-batch66 plus two original prefixes")
    full, fresh = [], []
    for item in audit["full240_manifest"]:
        slot = deepcopy(item["slot"])
        if item["action"] != "retain_entire_path":
            slot["episode_id"] = "reference-v8:" + slot["episode_id"].removeprefix("reference-v7:")
            fresh.append(slot)
        full.append(slot)
    require(len(full) == 240 and len(fresh) == 174 and
            {a: sum(s["arm"] == a for s in fresh) for a in "ABCD"} ==
            {"A": 43, "B": 44, "C": 43, "D": 44}, "No omitted or result-selected target")
    return audit, full, fresh


def verify_history(history, *, locked=False):
    require(len(history) == 13, "All1964 inherited calls and seven unknown required")
    verify_old_history(history[:12], locked=locked)
    entry = history[-1]
    root = Path(entry["root"])
    for name, digest in entry["file_sha256"].items():
        if locked and name.endswith(".lock"):
            continue
        require(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
                "Old v7 evidence changed")
    plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    receipt = strict_json((root / "FINAL_RECEIPT.json").read_bytes())
    require(plan["history"] == history[:12] and receipt["complete_episodes"] == 67 and
            receipt["budget"]["in_flight"] == 0 and receipt["budget"]["unknown"] == 1 and
            receipt["budget"]["occupied_USD_upper"] == "28.1959095000",
            "Exact v7 token-rate stop")
    db = sqlite3.connect((root / (plan["run_id"] + ".sqlite3")).as_uri() + "?mode=ro", uri=True)
    try:
        calls = db.execute(
            "select id,state,charged,input_tokens,output_tokens,request_sha256 from calls").fetchall()
    finally:
        db.close()
    audit = reviewed()
    from .budget import CallCaps
    settled = [r for r in calls if r[1] == "settled"]
    unknown = [r for r in calls if r[1] == "unknown"]
    require(len(calls) == 624 and len(settled) == 623 and len(unknown) == 1 and
            unknown[0][0] == audit["partial"]["unknown_call_id"] and
            unknown[0][5] == audit["partial"]["unknown_request_sha256"] and
            all(Decimal(r[2]) == CallCaps().charge(r[3], r[4]) for r in settled) and
            sum((Decimal(r[2]) for r in settled), Decimal(0)) == Decimal("10.1641435500"),
            "Every settled charge and retained unknown matched")
    return deepcopy(INHERITED)


def hydrate(root, slot):
    """Restore request-bound receipts/state without applying any old tool or call."""
    audit = reviewed()
    branch, partial = audit["branches"][0], audit["partial"]
    is_partial = slot["slot"] == partial["slot"]["slot"]
    require(is_partial or slot["slot"] == branch["slot"]["slot"], "Only two certified original prefixes")
    cert = partial if is_partial else branch
    old_id = cert["slot"]["episode_id"]
    journal = [strict_json(line) for line in (Path(root) / "events.jsonl").read_bytes().splitlines()]
    request = next(e for e in journal if e["kind"] == "model_request" and
                   e["episode_id"] == old_id and
                   (f"{old_id}:{e['operation']}:{e['index']}" == partial["unknown_call_id"]
                    if is_partial else e["request_sha256"] == branch["branch_before_request_sha256"]))
    native = deepcopy(request["request"]["input"][1:-1])
    state = restore_public_state(strict_json(request["request"]["input"][-1]["content"])["state"], native)
    require(fingerprint(state) == cert["known_public_state_sha256" if is_partial else "public_state_sha256"]
            and fingerprint(native) == cert["native_history_sha256"],
            "Exact actual prefix, no replacement observation")
    case = load_case(slot["task_id"])
    runtime = Phase0Runtime(case, slot["episode_id"])
    for event in state["history"]:
        if event["kind"] == "write_file":
            if event["path"] == case.public.artifact_path and runtime.workspace.get(
                    event["path"]) != event["content"]:
                runtime.artifact_revision += 1
            runtime.workspace[event["path"]] = event["content"]
        elif event["kind"] == "post_channel" and (
                runtime.artifact_revision > 0 and case.public.artifact_path in event["content"] and
                event["content"].strip() != case.public.artifact_path):
            runtime.posted_revision = runtime.artifact_revision
        elif event["kind"] == "send_message":
            runtime.messages[event["message_id"]] = {k: event[k] for k in
                                                     ("message_id", "person_id", "content")}
            runtime.messages[event["message_id"]]["sender"] = "agent"
        elif event["kind"] == "read_messages":
            runtime.messages[event["message_id"]] = {k: event[k] for k in
                ("message_id", "in_reply_to", "person_id", "content")}
            runtime.seen.add(event["message_id"])
            runtime.after_reply = True
    runtime.history = deepcopy(state["history"])
    runtime.normal_actions, runtime.cost = state["normal_actions"], state["contact_cost"]
    runtime.contacts = sum(e["kind"] == "send_message" for e in runtime.history)
    require(not state["terminal"] and not state["failed"] and
            fingerprint(runtime.observe()) == fingerprint(state) and history_events(native) == runtime.history,
            "Actual public workspace/revisions/messages/receipts must be identical")
    dialogues, cache = {}, {}
    for i, event in enumerate(runtime.history):
        if event["kind"] not in {"send_message", "read_messages"}:
            continue
        person = event["person_id"]
        dialogues.setdefault(person, [{"role": "system", "content": npc_system(person, case.scenarios[person])}])
        dialogues[person].append({"role": "user" if event["kind"] == "send_message" else "assistant",
                                 "content": event["content"]})
        if is_partial and event["kind"] == "read_messages":
            cache.setdefault(person, set()).update(s["source_id"] for s in public_sources(
                {"history": runtime.history[:i]}))
    require(fingerprint(runtime.messages) == cert["messages_sha256"] and
            fingerprint(dialogues if is_partial else next(iter(dialogues.values()))) ==
            cert["NPC_dialogues_sha256_NOT_system_text" if is_partial else "NPC_dialogue_sha256_NOT_system_text"],
            "Actual full NPC conversation preserved")
    if is_partial:
        require(fingerprint({p: sorted(v) for p, v in cache.items()}) == cert["known_sources_sha256"],
                "Full original publicwhat source cache")
    return runtime, native, dialogues, cache, deepcopy(
        cert["next_indices_NOT_permission_to_send"] if is_partial else cert["next_indices"])


def validate_review(plan, approval):
    audit, full, fresh = selection()
    require(plan["run_id"] == RUN_ID and plan["slots"] == full and plan["fresh_slots"] == fresh and
            plan["reference_recovery"] == {"version": VERSION, "reviewed_audit": fingerprint(audit),
                                          "review_release": REVIEW} and
            plan["inherited"] == INHERITED and len(plan["history"]) == 13 and
            plan["direct_user_source"] == SOURCE and approval.get("review_release") == REVIEW and
            plan["pacing"] == CONFIG and plan["unknown_attempt"] == {
                "old_call_id": audit["partial"]["unknown_call_id"],
                "old_request_sha256": audit["partial"]["unknown_request_sha256"],
                "new_episode_id": next(s["episode_id"] for s in fresh if
                                      s["slot"] == audit["partial"]["slot"]["slot"]),
                "operation": "ordinary", "index": 62, "max_new_attempts": 1,
                "old_unknown_preserved": True},
            "Exact delegated/confirmed original50 recovery and one explicit unknown attempt")
    cohort = plan["execution_cohort_audit"]
    require(cohort["current_runtime_binding"] == plan["runtime"] and
            cohort["retained_complete_episodes"] == 26 and
            cohort["reference_source_sha256_LF"] == audit["source_sha256_LF"] ==
            plan["runtime"]["phase0_sources"]["reference_completion.py"] and
            plan["runtime"]["phase0_sources"]["phase0.py"] ==
            audit["current_runtime_binding"]["phase0_sources"]["phase0.py"],
            "Final original26 cohort source binding and unchanged public protocol")
    original = strict_json((Path(__file__).parent / "reports" /
                            "REFERENCE_V8_AC26_CERTIFIED_20261113.json").read_bytes())
    require(all(cohort[k] == original[k] for k in ("rows", "contracts", "checker_sha256_LF")),
            "Whole26 original AC not individually screened")


def freeze(root, prior, cohort_path):
    from .admission import root_binding, validate_binding
    from .phase0_admission import make_plan
    root, prior = Path(root).resolve(), Path(prior).resolve()
    require(not root.exists(), "Do not replace attempted namespaces")
    old = strict_json((prior / "FROZEN_PLAN.json").read_bytes())
    history = deepcopy(old["history"]) + [{"root": str(prior), "file_sha256": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in prior.iterdir() if p.is_file()}}]
    verify_history(history)
    audit, full, fresh = selection()
    plan = make_plan(history, INHERITED, local_test=True)
    plan.update(run_id=RUN_ID, mode="provider", endpoint="https://api.openai.com/v1/responses",
                slots=full, fresh_slots=fresh, episodes=[s["episode_id"] for s in fresh],
                max_calls=174 * 192, max_episodes=174, total_input_tokens=174 * 192 * 272000,
                total_output_tokens=174 * 192 * 128000, direct_user_source=deepcopy(SOURCE),
                execution_cohort_audit=strict_json(Path(cohort_path).read_bytes()),
                pacing=deepcopy(CONFIG), reference_progress="study4-reference-completion-8-public-context",
                reference_recovery={"version": VERSION, "reviewed_audit": fingerprint(audit),
                                    "review_release": deepcopy(REVIEW)},
                unknown_attempt={
                    "old_call_id": audit["partial"]["unknown_call_id"],
                    "old_request_sha256": audit["partial"]["unknown_request_sha256"],
                    "new_episode_id": next(s["episode_id"] for s in fresh if
                                          s["slot"] == audit["partial"]["slot"]["slot"]),
                    "operation": "ordinary", "index": 62, "max_new_attempts": 1,
                    "old_unknown_preserved": True})
    for slot in fresh:
        if slot["slot"] in {audit["branches"][0]["slot"]["slot"], audit["partial"]["slot"]["slot"]}:
            hydrate(prior, slot)
    plan["code_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    at = datetime.now(timezone.utc)
    approval = {"approved": True, "run_id": RUN_ID, "plan_sha256": fingerprint(plan),
                "storage_root_sha256": root_binding(root), "budget_cap_USD": "50.00",
                "direct_user_source": SOURCE, "review_release": REVIEW,
                "scope": "STUDY4_FORMAL_PHASE0_240_PATH66_REMAIN174_PACED_SAME50",
                "not_before": at.isoformat(), "expires": (at + timedelta(days=7)).isoformat(),
                "reference": REVIEW["assignment_id"]}
    validate_binding(plan, approval, root, plan["endpoint"])
    root.mkdir(parents=True)
    write_new(root / "FROZEN_PLAN.json", plan)
    write_new(root / "APPROVAL.json", approval)
    write_new(root / "AUTHORIZATION_SOURCE.json", {
        "delegation_user_text": "限流你决定应该怎么办", "delegation_source": DELEGATION,
        "confirmation_user_text": "按照你说的来吧", "confirmation_source": SOURCE,
        "coordinator_selection_NOT_verbatim_user_text": REVIEW, "cap_USD": "50", "inherited": INHERITED})
    return {"frozen": True, "plan_sha256": fingerprint(plan), "remaining": 174, "retained": 66}


def run(root, plan, approval, transport):
    from .admission import validate_binding
    from .budget import BudgetBlocked
    from .durable import BatchLock, DurableLedger
    root = Path(root)
    validate_binding(plan, approval, root, transport.endpoint)
    require(not (root / "STARTED.json").exists(), "No automatic interrupted-run replay")
    verify_history(plan["history"])
    audit, _, _ = selection()
    prior = Path(plan["history"][-1]["root"])
    retained = {r["slot"]["slot"]: r for r in audit["whole_actual_paths"]
                if r["action"] == "retain_entire_path"}
    completed, groups, status, failure = [], {}, "complete", None
    with ExitStack() as stack:
        for entry in plan["history"]:
            name = next(n for n in entry["file_sha256"] if n.endswith(".sqlite3")).removesuffix(".sqlite3")
            stack.callback(BatchLock(Path(entry["root"]) / (name + ".lock")).close)
        verify_history(plan["history"], locked=True)
        ledger = DurableLedger(root, plan, approval, create=True)
        stack.callback(ledger.close)
        from .phase0 import Journal
        journal = Journal(root / "events.jsonl")
        stack.callback(journal.close)
        paced = PacedTransport(transport, journal,
                               prior_error=audit["actual_safe_error"]["transport"]["http_error"])
        write_new(root / "STARTED.json", {"at": now(), "plan_sha256": fingerprint(plan),
                                         "direct_user_source": SOURCE, "pacing": CONFIG})
        try:
            shutil.copyfile(prior / "REVIEWS_LIVE_005.json", root / "REVIEWS_RETAINED.json")
            for slot in plan["slots"]:
                if slot["slot"] not in retained:
                    continue
                path = prior / f"slot-{slot['slot']:03d}.json"
                record = strict_json(path.read_bytes())
                require(fingerprint(record) == retained[slot["slot"]]["record_sha256"],
                        "Retained whole path must be identical")
                shutil.copyfile(path, root / path.name)
                row = {k: record[k] for k in ("slot", "official_raw", "progress", "model_calls")}
                completed.append(row)
                groups.setdefault(slot["group"], []).append(row)
                journal.append({"kind": "retained_record", "slot": slot,
                                "source_record_sha256": retained[slot["slot"]]["record_sha256"]})
            for slot in plan["fresh_slots"]:
                mini = Phase0Mini(ledger, paced, slot, journal)
                runtime = None
                if slot["slot"] in {audit["branches"][0]["slot"]["slot"], audit["partial"]["slot"]["slot"]}:
                    runtime, mini.history, mini.dialogues, mini.known_sources, mini.indices = hydrate(prior, slot)
                    mini.event_cursor = len(runtime.history)
                    journal.append({"kind": "continued_paid_prefix", "slot": slot,
                                    "source_root": str(prior), "audit_sha256": fingerprint(audit),
                                    "next_indices": mini.indices, "public_state_sha256": fingerprint(runtime.observe())})
                    if slot["slot"] == audit["partial"]["slot"]["slot"]:
                        def event(e):
                            e["timestamp"] = now()
                            runtime.history[-1]["timestamp"] = e["timestamp"]
                            journal.append({"kind": "runtime_event", "episode_id": runtime.episode_id, "event": e})
                        runtime.event_sink = event
                        request = build_request("ordinary", runtime.observe(), history=mini.history)
                        require(fingerprint(request) == plan["unknown_attempt"]["old_request_sha256"],
                                "Explicit attempt only for identical unknown ordinary62 request")
                        journal.append({"kind": "explicit_unknown_new_attempt", "binding": plan["unknown_attempt"],
                                        "direct_user_source": SOURCE, "old_unknown_not_released": True})
                        mini.ordinary(runtime, mini.call("ordinary", runtime.observe()))
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
                    print(canonical({"kind": "complete_four_arm_block", "rows": group,
                                     "budget": ledger.status()}), flush=True)
        except BaseException as error:
            status = "budget_stopped" if isinstance(error, BudgetBlocked) and ledger.status()["unknown"] == 0 else "stopped"
            failure = type(error).__name__
        verify_history(plan["history"], locked=True)
        receipt = {"schema": VERSION, "status": status, "error_type": failure,
                   "complete_episodes": len(completed), "complete_four_arm_blocks": sum(len(g) == 4 for g in groups.values()),
                   "retained_complete_episodes": 66, "fresh_complete_episodes": len(completed) - 66,
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
