"""One prompt-v2 validation, then conditional fresh ceiling under the original USD50."""
from contextlib import ExitStack, closing
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import os
from pathlib import Path
import sqlite3

from .contracts import fingerprint, require, strict_json

SOURCE = {"id": "137aeefe-fc9f-49ba-9565-951bc6e77dcf", "revision": 2}
VERSION = "study4-ceiling50-prompt-v2-continuation-2"
PROMPT_VERSION = "study4-ordinary-single-action-v2"


def verify_history(history):
    """Immutable readers never settle, repair, checkpoint or release earlier ledgers."""
    require(len(history) in {3, 4}, "Exactly three old unknown runs, optionally one settled validation")
    held, settled = Decimal(0), Decimal(0)
    roots = set()
    for index, item in enumerate(history):
        root = Path(item["root"]).resolve()
        require(root not in roots and root.is_dir(), "Distinct existing prior roots required")
        roots.add(root)
        names = item["file_sha256"]
        dbname = item["run_id"] + ".sqlite3"
        require(dbname in names, "Prior ledger must be frozen")
        for name, digest in names.items():
            require(Path(name).name == name, "Prior evidence basename required")
            if name == item["run_id"] + ".lock":
                continue  # Windows cannot read the byte while the same owner holds its mutex.
            require(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
                    "Prior evidence byte binding changed")
        db = root / dbname
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(db) + suffix)
            require(not sidecar.exists() or sidecar.name in names, "Unbound prior sidecar")
            if suffix == "-wal":
                require(not sidecar.exists() or sidecar.stat().st_size == 0,
                        "Unapplied prior WAL; stop")
        with closing(sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True)) as reader:
            rows = reader.execute(
                "select state,reserved,charged,input_tokens,output_tokens from calls").fetchall()
        require(len(rows) == 1, "Each prior run must contain exactly one call")
        state, reserve, charge, incoming, outgoing = rows[0]
        require(Decimal(reserve) == Decimal(".858"), "Prior maximum reserve drift")
        if index < 3:
            require(state == "unknown" and charge is None, "Three old unknowns must remain unknown")
            held += Decimal(reserve)
        else:
            require(state == "settled" and Decimal(charge) >= 0 and
                    type(incoming) is int and type(outgoing) is int, "Validation not legally settled")
            receipt = strict_json((root / "VALIDATION_FINAL.json").read_bytes())
            require("VALIDATION_FINAL.json" in names and receipt["error_type"] is None and
                    receipt["model_HTTP_attempts"] == 1 and receipt["environment_tools_executed"] == 0 and
                    receipt["complete_episodes"] == 0 and receipt["budget"]["unknown"] == 0,
                    "Only successful no-tools validation unlocks the batch")
            from .budget import CallCaps
            require(Decimal(charge) == CallCaps().charge(incoming, outgoing), "Prior settled cost drift")
            settled += Decimal(charge)
    require(held == Decimal("2.574"), "Original unknown exposure must not be reduced")
    return held, settled


def make_plan(continuation):
    from .admission import pending_plan
    from .executor import ORDINARY_PROMPT_VERSION
    from .paid_driver import frozen_plan
    require(ORDINARY_PROMPT_VERSION == PROMPT_VERSION, "Frozen single-action-v2 prompt required")
    phase = continuation["phase"]
    require(phase in {"validation", "batch"}, "Unsupported continuation phase")
    plan = frozen_plan() if phase == "batch" else pending_plan()
    plan.update(run_id="study4-v2-prompt-v2-" + phase + "-20261112-v2",
                budget_cap_USD="50.00", continuation=continuation)
    if phase == "validation":
        plan.update(max_calls=1, max_episodes=1, episodes=["prompt-v2-validation-no-tools"],
                    environment_tools_allowed=False)
    else:
        # Earlier unknown token usage remains charged at model maxima, not guessed usage.
        verify_history(continuation["history"])
        for item in continuation["history"]:
            db = Path(item["root"]).resolve() / (item["run_id"] + ".sqlite3")
            with closing(sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True)) as reader:
                state, incoming, outgoing = reader.execute(
                    "select state,input_tokens,output_tokens from calls").fetchone()
            plan["max_calls"] -= 1
            plan["total_input_tokens"] -= incoming if state == "settled" else 272000
            plan["total_output_tokens"] -= outgoing if state == "settled" else 128000
    return plan


def validate_continuation(plan, approval):
    config = plan["continuation"]
    require(config["version"] == VERSION and config["new_direct_user_source"] == SOURCE and
            config["prompt_version"] == PROMPT_VERSION and plan["budget_cap_USD"] == "50.00",
            "Continuation source/version/original50 scope mismatch")
    expected_count = 3 if config["phase"] == "validation" else 4
    require(len(config["history"]) == expected_count and plan == make_plan(config),
            "Exact validation or unchanged 48-slot continuation plan required")
    authority = approval.get("continuation_authorization")
    require(isinstance(authority, dict) and authority.get("approved") is True and
            authority.get("new_direct_user_source") == SOURCE and
            authority.get("continuation_sha256") == fingerprint(config),
            "New explicit continuation approval required")
    verify_history(config["history"])


def history_locks(stack, history):
    from .durable import BatchLock
    for item in history:
        lock = BatchLock(Path(item["root"]) / (item["run_id"] + ".lock"))
        stack.callback(lock.close)
    verify_history(history)


def validate_once(root, plan, approval, request, transport):
    from .admission import prepare_request, validate_binding
    from .diagnostic_dispatch import ObservedTransport
    from .durable import DurableLedger
    from .paid_driver import write_new
    root = Path(root).resolve()
    validate_binding(plan, approval, root, transport.endpoint)
    config = plan["continuation"]
    require(config["phase"] == "validation" and
            fingerprint(request) == config["request_sha256"], "Only exact next-action validation")
    prepare_request(request, "ordinary", plan)
    with ExitStack() as stack:
        history_locks(stack, config["history"])
        require(not (root / "VALIDATION_STARTED.json").exists(), "Already attempted; never replay validation")
        ledger = DurableLedger(root, plan, approval, create=True)
        stack.callback(ledger.close)
        write_new(root / "VALIDATION_STARTED.json", {
            "at": datetime.now(timezone.utc).isoformat(), "plan_sha256": fingerprint(plan),
            "prior_unknown_held_USD": "2.574000", "environment_tools_allowed": False})
        observed = ObservedTransport(transport, root)
        error = None
        try:
            result = ledger.call(plan["episodes"][0], "ordinary", 0, request, observed)
            require(not result["replayed_without_send"], "No validation replay")
        except Exception as failure:
            error = type(failure).__name__
        rows = [dict(row) for row in ledger.connection.execute(
            "select id,state,reserved,charged,input_tokens,output_tokens,response_sha256,response_bytes,"
            "error_type,diagnostic from calls")]
        for row in rows:
            if row["diagnostic"] is not None:
                row["diagnostic"] = strict_json(row["diagnostic"])
        receipt = {"schema": VERSION, "phase": "validation", "plan_sha256": fingerprint(plan),
                   "model_HTTP_attempts": observed.calls, "error_type": error, "calls": rows,
                   "budget": ledger.status(), "environment_tools_executed": 0, "complete_episodes": 0,
                   "automatic_retry": False}
        verify_history(config["history"])
        write_new(root / "VALIDATION_FINAL.json", receipt)
        return receipt


def run_batch(root, plan, approval, transport, on_group=None):
    from .admission import validate_binding
    from .paid_driver import run_fresh
    validate_binding(plan, approval, root, transport.endpoint)
    require(plan["continuation"]["phase"] == "batch", "Only validated batch phase")
    with ExitStack() as stack:
        history_locks(stack, plan["continuation"]["history"])
        return run_fresh(root, plan, approval, transport, on_group)


if __name__ == "__main__":
    import argparse
    from .admission import validate_binding
    from .contracts import canonical
    from .http_transport import HTTPTransport
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    approval = strict_json((root / "APPROVAL.json").read_bytes())
    validate_binding(plan, approval, root, plan["endpoint"])
    require(not (root / (plan["run_id"] + ".sqlite3")).exists(), "Never restart an attempted run")
    key = os.environ.get("OPENAI_API_KEY")
    require(isinstance(key, str) and key, "Existing process-only credential injection required")
    transport = HTTPTransport(plan["endpoint"], plan["mode"], credential=key,
                              timeout=plan["http_timeout_seconds"], max_response_bytes=plan["max_response_bytes"])
    if plan["continuation"]["phase"] == "validation":
        result = validate_once(root, plan, approval, strict_json((root / "REQUEST.json").read_bytes()), transport)
    else:
        def group_report(rows, budget):
            print(canonical({"kind": "actual_group_complete", "rows": rows, "budget": budget}), flush=True)
        result = run_batch(root, plan, approval, transport, group_report)
    print(canonical(result), flush=True)
