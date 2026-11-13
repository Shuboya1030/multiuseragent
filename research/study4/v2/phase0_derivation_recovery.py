"""Narrow reviewed v7 continuation: all paths retained or branched, never redrawn."""
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
from .phase0 import (Phase0Mini, Phase0Runtime, Journal, build_request, episode, history_events,
                     load_case, now, npc_system, restore_public_state, schedule, write_new)
from .phase0_recovery import CONTINUE_SOURCE, verify_history as verify_prior_history

RECOVERY = "study4-phase0-reference-v7-source-derivation-continuation-1"
RUN_ID = "study4-phase0-reference-v7-path41-branch1-pending1-fresh197-20261112"
INHERITED = {"unknown_held_USD": "5.148000", "settled_USD_upper": "12.0257659500",
             "calls": 1340, "settled_calls": 1334, "unknown_calls": 6}
PRIOR_PLAN = "6dec4132afd14b8c2da01e11b6c903594dea15c1110d48028f1c806fcffed88f"
REVIEWED = "af74c28df6acbf4667c13660e875930731e81a3e41a00898664469fa95ca3d71"
REVIEW = {"coordinator_session_id": "741f367f-a37b-48de-a57d-1e7bbe84ade4",
          "assignment_id": "assignment:741f367f-a37b-48de-a57d-1e7bbe84ade4:call_aGDv7TIetvAn4IU0CUgUSo0b",
          "release_message_tool_call_id": "call_Kspbz4P7lgJw01HTKOSpDwJm",
          "attribution": "Agent releases own implementation-review pause; not new user authorization"}


def reviewed():
    audit = strict_json((Path(__file__).parent / "reports" /
                         "REFERENCE_V7_SOURCE_PATH_AUDIT_20261112.json").read_bytes())
    require(fingerprint(audit) == REVIEWED, "Exact coordinator-reviewed whole-batch source/path proof")
    return audit


def selection():
    audit = reviewed()
    rows = {r["slot"]["slot"]: r for r in audit["complete_rows"]}
    full = deepcopy(schedule())
    for slot in full:
        old = rows.get(slot["slot"])
        if old is not None and old["action"] != "branch_original_trajectory":
            slot.update(old["slot"])
        else:
            slot["episode_id"] = "reference-v7:" + slot["episode_id"]
    fresh = [s for s in full if s["slot"] not in rows or
             rows[s["slot"]]["action"] == "branch_original_trajectory"]
    require(len(full) == 240 and len(fresh) == 199 and
            {a: sum(s["arm"] == a for s in fresh) for a in "ABCD"} ==
            {"A": 47, "B": 52, "C": 47, "D": 53}, "All logical paths, not score-selected redraws")
    return audit, full, fresh


def ledger_rows(root):
    root = Path(root)
    plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    db = sqlite3.connect((root / (plan["run_id"] + ".sqlite3")).resolve().as_uri() +
                         "?mode=ro&immutable=1", uri=True)
    try:
        return db.execute(
            "select id,state,charged,input_tokens,output_tokens,result,result_sha256 from calls order by created"
        ).fetchall()
    finally:
        db.close()


def verify_history(history, *, locked=False):
    require(len(history) == 12, "All1340 inherited calls and six held unknown required")
    verify_prior_history(history[:11], locked=locked)
    entry, root = history[-1], Path(history[-1]["root"])
    for name, digest in entry["file_sha256"].items():
        if locked and name.endswith(".lock"):
            continue
        require(Path(name).name == name and hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
                "Settled v6 evidence changed")
    plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    receipt = strict_json((root / "FINAL_RECEIPT.json").read_bytes())
    require(fingerprint(plan) == PRIOR_PLAN and plan["history"] == history[:11] and
            receipt["complete_episodes"] == 42 and
            receipt["budget"]["unknown"] == receipt["budget"]["in_flight"] == 0,
            "Exact safe post-settlement operator pause required")
    from .budget import CallCaps
    rows = ledger_rows(root)
    require(len(rows) == 300 and all(r[1] == "settled" and
            Decimal(r[2]) == CallCaps().charge(r[3], r[4]) for r in rows) and
            sum((Decimal(r[2]) for r in rows), Decimal(0)) == Decimal("1.4904326250"),
            "Every v6 charge including diagnostic tail stays counted")
    return deepcopy(INHERITED)


def continuation(root, slot):
    """Reconstruct only the audited applied prefix or unapplied paid proposal."""
    audit = reviewed()
    source = Path(root)
    branch = audit["branches"][0]
    pending = audit["pending_settled_proposal"]
    if slot["slot"] == pending["slot"]["slot"]:
        row = next(r for r in ledger_rows(source) if r[0] == pending["call_id"])
        result = strict_json(row[5])
        require(row[1] == "settled" and fingerprint(result) == pending["result_sha256"] and
                not pending["applied"], "Only exactly identified unapplied paid proposal")
        runtime = Phase0Runtime(load_case(slot["task_id"]), slot["episode_id"])
        return runtime, [], {}, {}, {"question": 1, "npc": 0, "ordinary": 0}, result
    require(slot["slot"] == branch["slot"]["slot"], "No arbitrary trajectory restart")
    entries = [strict_json(line) for line in (source / "events.jsonl").read_bytes().splitlines()]
    request = next(e for e in entries if e["kind"] == "model_request" and
                   e["episode_id"] == branch["slot"]["episode_id"] and
                   e["operation"] == "question" and e["index"] == branch["branch_before_request_index"])
    history = request["request"]["input"][1:-1]
    state = restore_public_state(strict_json(request["request"]["input"][-1]["content"])["state"], history)
    require(fingerprint(state) == branch["public_state_sha256"] and
            fingerprint(history) == branch["native_history_sha256"] and
            fingerprint(state["history"]) == branch["public_history_sha256"],
            "Exact originally sampled public prefix and native receipts, no tool replay")
    case = load_case(slot["task_id"])
    runtime = Phase0Runtime(case, slot["episode_id"])
    runtime.workspace, runtime.history = deepcopy(state["workspace"]), deepcopy(state["history"])
    runtime.normal_actions, runtime.cost = state["normal_actions"], state["contact_cost"]
    runtime.contacts = sum(e["kind"] == "send_message" for e in runtime.history)
    runtime.artifact_revision = state["progress"]["artifact_revision"]
    for e in runtime.history:
        if e["kind"] == "send_message":
            runtime.messages[e["message_id"]] = {k: e[k] for k in ("message_id", "person_id", "content")}
            runtime.messages[e["message_id"]]["sender"] = "agent"
        elif e["kind"] == "read_messages":
            runtime.messages[e["message_id"]] = {k: e[k] for k in
                                                ("message_id", "in_reply_to", "person_id", "content")}
            runtime.seen.add(e["message_id"])
            runtime.after_reply = True
    person = runtime.history[1]["person_id"]
    dialogue = [{"role": "system", "content": npc_system(person, case.scenarios[person])}] + [
        {"role": "user" if e["kind"] == "send_message" else "assistant", "content": e["content"]}
        for e in runtime.history if e["kind"] in {"send_message", "read_messages"}]
    require(fingerprint(runtime.observe()) == branch["public_state_sha256"] and
            fingerprint(runtime.messages) == branch["restored_messages_sha256"] and
            sorted(runtime.seen) == branch["restored_seen_message_ids"] and
            fingerprint(dialogue) == branch["restored_NPC_dialogue_sha256_NOT_system_text"] and
            history_events(history) == runtime.history,
            "Public observation, messages, NPC dialogue and delivery state all reproduced")
    return (runtime, deepcopy(history), {person: dialogue},
            {p: set(v) for p, v in branch["restored_known_sources"].items()},
            deepcopy(branch["next_call_indices"]), None)


def validate_review(plan, approval):
    audit, full, fresh = selection()
    require(plan["run_id"] == RUN_ID and plan["slots"] == full and plan["fresh_slots"] == fresh and
            plan["reference_recovery"] == {"version": RECOVERY, "reviewed_audit": REVIEWED,
                                          "review_release": REVIEW} and
            plan["inherited"] == INHERITED and len(plan["history"]) == 12 and
            plan["direct_user_source"] == CONTINUE_SOURCE and approval.get("review_release") == REVIEW,
            "Exact reviewed41+199 source/cap and released Agent pause")
    cohort = plan["execution_cohort_audit"]
    original_cohort = strict_json((Path(__file__).parent / "reports" /
                                  "REFERENCE_V7_AC26_AUDIT_20261112.json").read_bytes())
    require(cohort["current_runtime_binding"] == plan["runtime"] and
            all(cohort[k] == original_cohort[k] for k in ("rows", "contracts", "checker_sha256_LF")) and
            cohort["source_rule_coverage"] == {"tasks": 60, "nodes": 95} and
            cohort["retained_complete_episodes"] == 26 and
            cohort["retained_counts_by_arm"] == {"A": 13, "B": 0, "C": 13, "D": 0} and
            all(r["request_count_checked"] > 0 and
                r["shared_executor_NPC_tools_public_input_scorer_terminal_code_unchanged"]
                for r in cohort["rows"] if r["retain_in_formal_cohort"]) and
            cohort["reference_source_sha256_LF"] == audit["source_sha256_LF"] ==
            plan["runtime"]["phase0_sources"]["reference_completion.py"],
            "Final execution source must revalidate entire original26AC and reviewed private rules")


def freeze(root, prior_root, audit_path):
    from .admission import root_binding, validate_binding
    from .phase0_admission import make_plan
    root, prior_root = Path(root).resolve(), Path(prior_root).resolve()
    require(not root.exists(), "Never replace an existing execution namespace")
    prior = strict_json((prior_root / "FROZEN_PLAN.json").read_bytes())
    require(fingerprint(prior) == PRIOR_PLAN, "Exact settled v6 source required")
    history = deepcopy(prior["history"]) + [{
        "root": str(prior_root), "file_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in prior_root.iterdir() if p.is_file()}}]
    inherited = verify_history(history)
    audit, full, fresh = selection()
    plan = make_plan(history, inherited, local_test=True)
    plan.update(run_id=RUN_ID, mode="provider", endpoint="https://api.openai.com/v1/responses",
                slots=full, fresh_slots=fresh, episodes=[s["episode_id"] for s in fresh],
                max_calls=199 * 192, max_episodes=199,
                total_input_tokens=199 * 192 * 272000, total_output_tokens=199 * 192 * 128000,
                direct_user_source=deepcopy(CONTINUE_SOURCE),
                execution_cohort_audit=strict_json(Path(audit_path).read_bytes()),
                reference_progress="study4-reference-completion-7-source-bound-public-derivations",
                reference_recovery={"version": RECOVERY, "reviewed_audit": REVIEWED, "review_release": REVIEW})
    for slot in fresh:
        if slot["slot"] in {audit["branches"][0]["slot"]["slot"], audit["pending_settled_proposal"]["slot"]["slot"]}:
            continuation(prior_root, slot)
    plan["code_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    at = datetime.now(timezone.utc)
    approval = {"approved": True, "run_id": RUN_ID, "plan_sha256": fingerprint(plan),
                "storage_root_sha256": root_binding(root), "budget_cap_USD": "50.00",
                "direct_user_source": CONTINUE_SOURCE, "review_release": REVIEW,
                "scope": "STUDY4_FORMAL_PHASE0_240_PATH41_REMAIN199_SAME50",
                "not_before": at.isoformat(), "expires": (at + timedelta(hours=24)).isoformat(),
                "reference": REVIEW["assignment_id"]}
    validate_binding(plan, approval, root, plan["endpoint"])
    root.mkdir(parents=True)
    write_new(root / "FROZEN_PLAN.json", plan)
    write_new(root / "APPROVAL.json", approval)
    write_new(root / "AUTHORIZATION_SOURCE.json", {
        "direct_user_source": CONTINUE_SOURCE, "direct_user_text": "同意你的决策，请你按照这个来继续",
        "Agent_review_release_NOT_new_user_authorization": REVIEW, "new_budget": False,
        "original_cap_USD": "50.00", "inherited": INHERITED})
    return {"frozen": True, "plan_sha256": fingerprint(plan), "remaining": 199, "retained": 41}


def run(root, plan, approval, transport):
    from .admission import validate_binding
    from .budget import BudgetBlocked
    from .durable import BatchLock, DurableLedger
    root = Path(root)
    validate_binding(plan, approval, root, transport.endpoint)
    require(not (root / "STARTED.json").exists(), "Interrupted roots never automatically replay")
    verify_history(plan["history"])
    audit, _, _ = selection()
    rows = {r["slot"]["slot"]: r for r in audit["complete_rows"]
            if r["action"] != "branch_original_trajectory"}
    prior = Path(plan["history"][-1]["root"])
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
            shutil.copyfile(prior / "REVIEWS_BATCH04.json", root / "REVIEWS_RETAINED_AC.json")
            for slot in plan["slots"]:
                if slot["slot"] not in rows:
                    continue
                old = prior / f"slot-{slot['slot']:03d}.json"
                require(hashlib.sha256(old.read_bytes()).hexdigest() == rows[slot["slot"]]["source_record_sha256"],
                        "Whole-path actual source bytes changed")
                shutil.copyfile(old, root / old.name)
                record = strict_json(old.read_bytes())
                journal.append({"kind": "retained_record", "slot": slot,
                                "source_sha256": rows[slot["slot"]]["source_record_sha256"]})
                row = {k: record[k] for k in ("slot", "official_raw", "progress", "model_calls")}
                completed.append(row)
                groups.setdefault(slot["group"], []).append(row)
            special = {audit["branches"][0]["slot"]["slot"], audit["pending_settled_proposal"]["slot"]["slot"]}
            for slot in plan["fresh_slots"]:
                mini = Phase0Mini(ledger, transport, slot, journal)
                runtime, pending = None, None
                if slot["slot"] in special:
                    runtime, mini.history, mini.dialogues, mini.known_sources, mini.indices, pending = continuation(prior, slot)
                    mini.event_cursor = len(runtime.history)
                    journal.append({"kind": "continued_paid_prefix", "slot": slot,
                                    "source_root": str(prior), "reviewed_audit": REVIEWED,
                                    "pending_proposal_applied_next": pending is not None})
                else:
                    journal.append({"kind": "episode_start", "slot": slot})
                if pending is not None:
                    def event(e):
                        e["timestamp"] = now()
                        runtime.history[-1]["timestamp"] = e["timestamp"]
                        journal.append({"kind": "runtime_event", "episode_id": runtime.episode_id, "event": e})
                    runtime.event_sink = event
                    runtime._event("control_decision", action="ASK", person_id=pending["data"]["arguments"]["person_id"])
                    mini.ask(load_case(slot["task_id"]), runtime, pending, supplement=False)
                    mini.ordinary(runtime, mini.call("ordinary", runtime.observe()))
                record = episode(load_case(slot["task_id"]), slot, mini, journal, runtime=runtime)
                if slot["slot"] in special:
                    record["continued_source_audit"] = REVIEWED
                write_new(root / f"slot-{slot['slot']:03d}.json", record)
                row = {k: record[k] for k in ("slot", "official_raw", "progress", "model_calls")}
                completed.append(row)
                block = groups.setdefault(slot["group"], [])
                block.append(row)
                if len(block) == 4:
                    print(canonical({"kind": "complete_four_arm_block", "rows": block, "budget": ledger.status()}), flush=True)
        except BaseException as error:
            status = "budget_stopped" if isinstance(error, BudgetBlocked) and ledger.status()["unknown"] == 0 else "stopped"
            failure = type(error).__name__
        verify_history(plan["history"], locked=True)
        receipt = {"schema": RECOVERY, "status": status, "error_type": failure,
                   "complete_episodes": len(completed), "complete_four_arm_blocks": sum(len(g) == 4 for g in groups.values()),
                   "retained_complete_episodes": 41, "fresh_complete_episodes": len(completed) - 41,
                   "completed": completed, "budget": ledger.status(), "automatic_retry": False,
                   "incomplete_not_business_zero": True, "finished": now()}
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
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        print(canonical(freeze(args.root, args.prior_root, args.audit)))
    else:
        from .admission import validate_binding
        plan = strict_json((args.root / "FROZEN_PLAN.json").read_bytes())
        approval = strict_json((args.root / "APPROVAL.json").read_bytes())
        validate_binding(plan, approval, args.root, plan["endpoint"])
        verify_history(plan["history"])
        require(not (args.root / "STARTED.json").exists(), "No interrupted-root replay")
        if args.check:
            print(canonical({"binding_verified_before_key": True, "remaining": 199, "inherited": INHERITED}))
        else:
            from .http_transport import HTTPTransport
            key = os.environ.get("OPENAI_API_KEY")
            require(isinstance(key, str) and key, "Existing process-only authorized credential missing")
            transport = HTTPTransport(plan["endpoint"], plan["mode"], credential=key,
                                      timeout=plan["http_timeout_seconds"], max_response_bytes=plan["max_response_bytes"])
            result = run(args.root, plan, approval, transport)
            print(canonical({"kind": "recovery_terminal", **{k: result[k] for k in
                  ("status", "error_type", "complete_episodes", "complete_four_arm_blocks", "budget")}}))
