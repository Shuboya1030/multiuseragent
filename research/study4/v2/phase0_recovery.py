"""Reviewed reference-v5 continuation of the original240 scope, never a tool replay."""
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
                     verify_inherited, write_new, Journal)

RECOVERY = "study4-phase0-reference-v5-AC26-fresh214-1"
RUN_ID = "study4-phase0-reference-v5-AC26-fresh214-20261112"
REVIEWED = "21c36555e2c031b631a40f1ab0bda9a7ecac33efc6fab04332af0b46f8142c3e"
PARENT_PLAN = "10becfc13f4c3d39ce39fc0098775b8a87c4f190d7927d59b92bc2421fe6ae23"
PARENT_LEDGER = "fc6b9248e775db250682dd70af23caffb1956c5868114b429acff4f6f4d1537b"
REVIEW = {
    "coordinator_session_id": "741f367f-a37b-48de-a57d-1e7bbe84ade4",
    "assignment_id": "assignment:741f367f-a37b-48de-a57d-1e7bbe84ade4:call_WROHXd0Ztjobl1hqrBccgjvV",
    "release_message_tool_call_id": "call_6rIfUGqMvljG4R3rDF9iRUVK",
    "attribution": "Agent review release and source correction; NOT new user authorization",
    "original_direct_user_source": SOURCE,
}
INHERITED = {"unknown_held_USD": "5.148000", "settled_USD_upper": "10.481236425",
             "calls": 1022, "settled_calls": 1016, "unknown_calls": 6}
REPORTS = Path(__file__).parent / "reports"


def selection():
    proof = strict_json((REPORTS / "REFERENCE_V5_AC26_FRESH214_20261112.json").read_bytes())
    require(fingerprint(proof) == REVIEWED, "Exact reviewed fixed-cohort proof required")
    retained = {r["slot"]["slot"] for r in proof["rows"] if r["retain_in_formal_cohort"]}
    full = deepcopy(schedule())
    for slot in full:
        if slot["slot"] not in retained:
            slot["episode_id"] = "reference-v5:" + slot["episode_id"]
    fresh = [s for s in full if s["slot"] not in retained]
    require(len(retained) == 26 and len(fresh) == 214 and
            {a: sum(s["arm"] == a for s in fresh) for a in "ABCD"} ==
            {"A": 47, "B": 60, "C": 47, "D": 60}, "Whole fixed A/C cohort; all B/D fresh")
    return proof, full, fresh


def verify_history(history, *, locked=False):
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
    return deepcopy(INHERITED)


def validate_review(plan, approval):
    proof, full, fresh = selection()
    require(plan["reference_recovery"] == {
        "version": RECOVERY, "reviewed_manifest_fingerprint": REVIEWED,
        "review_release": REVIEW, "retained_slots": [s["slot"] for s in full if s not in fresh],
        "old_partial_not_resumed": True, "all_BD_fresh": True},
        "Only reviewed214 recovery; review is not a new user source")
    require(plan["run_id"] == RUN_ID and plan["slots"] == full and plan["fresh_slots"] == fresh and
            plan["episodes"] == [s["episode_id"] for s in fresh] and
            plan["inherited"] == INHERITED and len(plan["history"]) == 10 and
            approval.get("review_release") == REVIEW,
            "Exact new namespace/cohort/original cumulative accounting")
    audit = plan["execution_cohort_audit"]
    require(audit["current_runtime_binding"] == plan["runtime"] and
            all(audit[k] == proof[k] for k in ("remaining_manifest", "retained_counts_by_arm",
                                              "rows", "contracts", "budget", "source_rule_coverage")) and
            audit["reference_source_sha256_LF"] == proof["reference_source_sha256_LF"],
            "Post-admission source audit must cover whole fixed A/C group")


def make_plan(prior_root, audit):
    from .phase0_admission import make_plan as base_plan
    prior_root = Path(prior_root).resolve()
    prior = strict_json((prior_root / "FROZEN_PLAN.json").read_bytes())
    require(fingerprint(prior) == PARENT_PLAN, "Exact paused52 original source required")
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
                reference_progress="study4-reference-completion-5-reviewed-recovery",
                reference_recovery={"version": RECOVERY, "reviewed_manifest_fingerprint": REVIEWED,
                    "review_release": deepcopy(REVIEW),
                    "retained_slots": [r["slot"]["slot"] for r in proof["rows"] if r["retain_in_formal_cohort"]],
                    "old_partial_not_resumed": True, "all_BD_fresh": True})
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
                "direct_user_source": SOURCE, "review_release": REVIEW,
                "scope": "STUDY4_FORMAL_PHASE0_240_AC26_FRESH214_SAME50",
                "not_before": at.isoformat(), "expires": (at + timedelta(hours=24)).isoformat(),
                "reference": REVIEW["assignment_id"]}
    validate_binding(plan, approval, root, plan["endpoint"])
    root.mkdir(parents=True)
    write_new(root / "FROZEN_PLAN.json", plan)
    write_new(root / "APPROVAL.json", approval)
    write_new(root / "AUTHORIZATION_SOURCE.json", {
        "direct_user_source": SOURCE, "direct_user_text": "我已经续费你继续吧",
        "new_direct_user_authorization_claimed": False, "agent_review_release": REVIEW,
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
                                         "direct_user_source": SOURCE, "review_release": REVIEW})
        try:
            # Preserve the entire predefined cohort before the first new POST.
            for slot in plan["slots"]:
                if slot["slot"] not in retained:
                    continue
                path = root / f"slot-{slot['slot']:03d}.json"
                old = Path(plan["history"][-1]["root"]) / path.name
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
                journal.append({"kind": "episode_start", "slot": slot})
                record = episode(load_case(slot["task_id"]), slot,
                                 Phase0Mini(ledger, transport, slot, journal), journal)
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
