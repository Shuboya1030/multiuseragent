"""Versioned native-function execution; all historic exposure remains under the same USD50."""
from contextlib import ExitStack, closing
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import os
from pathlib import Path
import sqlite3

from .contracts import canonical, fingerprint, require, strict_json
from .native_protocol import BOUND, VERSION, build_native_request
from .paid_driver import PaidMini, frozen_plan, write_new

SOURCE = {"id": "f0d83ab9-9180-4da1-8ff7-7a2feaf440e1", "revision": 3}
RECOVERY_VERSION = "study4-native-ceiling50-recovery-1"


def verify_history(history):
    require(len(history) in {5, 6}, "Five original runs, optionally one new successful validation")
    total = {"held": Decimal(0), "settled": Decimal(0), "calls": 0, "input": 0, "output": 0,
             "unknown": 0, "settled_calls": 0}
    roots = set()
    for index, item in enumerate(history):
        root = Path(item["root"]).resolve()
        require(root not in roots and root.is_dir(), "Distinct existing frozen history roots")
        roots.add(root)
        expected = item["file_sha256"]
        dbname = item["run_id"] + ".sqlite3"
        require(dbname in expected, "Frozen prior database required")
        for name, digest in expected.items():
            require(Path(name).name == name, "Frozen basename required")
            if name != item["run_id"] + ".lock":
                require(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
                        "Historical actual evidence changed")
        db = root / dbname
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(db) + suffix)
            require(not sidecar.exists() or sidecar.name in expected, "Unbound historical sidecar")
            require(suffix != "-wal" or not sidecar.exists() or sidecar.stat().st_size == 0,
                    "Unapplied prior WAL; stop")
        with closing(sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True)) as reader:
            rows = reader.execute(
                "select state,reserved,charged,input_tokens,output_tokens from calls").fetchall()
        require(rows, "Each frozen run must contain actual calls")
        from .budget import CallCaps
        for state, reserve, charge, incoming, outgoing in rows:
            require(Decimal(reserve) == Decimal(".858") and state in {"unknown", "settled"},
                    "No unaccounted historical in-flight exposure")
            total["calls"] += 1
            if state == "unknown":
                require(charge is None, "Do not release unknown")
                total["held"] += Decimal(reserve)
                total["unknown"] += 1
                total["input"] += 272000
                total["output"] += 128000
            else:
                require(Decimal(charge) == CallCaps().charge(incoming, outgoing), "Frozen usage/cost drift")
                total["settled"] += Decimal(charge)
                total["settled_calls"] += 1
                total["input"] += incoming
                total["output"] += outgoing
        if index == 4:
            require(total["held"] == Decimal("3.432") and total["settled"] == Decimal(".013762650") and
                    total["calls"] == 14 and total["unknown"] == 4 and total["settled_calls"] == 10,
                    "All four unknown and ten settled historical calls must count")
        if index == 5:
            receipt = strict_json((root / "VALIDATION_FINAL.json").read_bytes())
            require("VALIDATION_FINAL.json" in expected and len(rows) == 1 and rows[0][0] == "settled" and
                    receipt["error_type"] is None and receipt["model_HTTP_attempts"] == 1 and
                    receipt["environment_tools_executed"] == receipt["complete_episodes"] == 0,
                    "Only one successful no-tools native validation unlocks batch")
    return total


def make_plan(config):
    from .admission import pending_plan
    phase = config["phase"]
    require(phase in {"validation", "batch"}, "Native validation or batch only")
    plan = frozen_plan() if phase == "batch" else pending_plan()
    plan.update(run_id="study4-v2-native-" + phase + "-20261112-v1", budget_cap_USD="50.00",
                native_protocol=VERSION, native_recovery=config, token_bound=deepcopy(BOUND))
    if config.get("local_test") is True:
        plan.update(mode="local_test", endpoint="http://127.0.0.1:9/v1/responses")
    if phase == "validation":
        plan.update(max_calls=1, max_episodes=1, episodes=["native-validation-no-tools"],
                    environment_tools_allowed=False)
    else:
        summary = verify_history(config["history"])
        plan["max_calls"] -= summary["calls"]
        plan["total_input_tokens"] -= summary["input"]
        plan["total_output_tokens"] -= summary["output"]
    return plan


def validate_recovery(plan, approval):
    config = plan["native_recovery"]
    require(config["version"] == RECOVERY_VERSION and config["new_direct_user_source"] == SOURCE and
            config["protocol"] == VERSION and len(config["history"]) ==
            (5 if config["phase"] == "validation" else 6) and plan == make_plan(config),
            "Exact new native protocol scope required")
    authority = approval.get("native_recovery_authorization")
    require(isinstance(authority, dict) and authority.get("approved") is True and
            authority.get("new_direct_user_source") == SOURCE and
            authority.get("recovery_sha256") == fingerprint(config), "New explicit native authorization required")
    verify_history(config["history"])


def history_locks(stack, history):
    from .durable import BatchLock
    for item in history:
        lock = BatchLock(Path(item["root"]) / (item["run_id"] + ".lock"))
        stack.callback(lock.close)
    verify_history(history)


class NativeMini(PaidMini):
    def __init__(self, *args):
        super().__init__(*args)
        self.identity = self.identity.split(":")[0] + ":" + VERSION
        self.native_history, self.pending = [], None

    def receipt(self, result, output):
        function = result["native_function"]
        self.native_history.extend(deepcopy(function["output_items"]))
        self.native_history.append({"type": "function_call_output", "call_id": function["call_id"],
                                    "output": canonical(output)})
        self.journal.append({"kind": "native_function_result", "episode_id": self.episode_id,
                             "call_id": function["call_id"], "function": function["name"], "public_result": output})

    def _call(self, operation, observation, **kwargs):
        require(not self.failed, "No automatic failed-call retry")
        require(operation != "ordinary" or self.pending is None, "Unresolved ordinary proposal")
        request = build_native_request(operation, observation, native_history=self.native_history, **kwargs)
        index = self.indices[operation]
        self.journal.append({"kind": "model_request", "episode_id": self.episode_id, "operation": operation,
                             "index": index, "request_sha256": fingerprint(request),
                             "public_observation_sha256": fingerprint(observation), "public_request": request})
        try:
            result = self.ledger.call(self.episode_id, operation, index, request, self.transport)
            require(not result["replayed_without_send"], "No cached action replay in fresh native batch")
            self.indices[operation] += 1
            self.journal.append({"kind": "model_result", "episode_id": self.episode_id, "operation": operation,
                                 "index": index, "result": result, "budget": self.ledger.status()})
            if operation == "ordinary":
                self.pending = result
            else:
                self.receipt(result, {"status": "decision_recorded" if operation == "control" else
                                      "question_composed_not_yet_sent", "data": result["data"]})
            return result["data"]
        except BaseException:
            self.failed = True
            raise

    def observe_event(self, event):
        if self.pending is None:
            return
        if event["kind"] == "control_decision" and event["action"] == "ASK":
            self.receipt(self.pending, {"status": "proposal_discarded_not_executed", "reason": "ASK_refresh"})
        elif event["kind"] == "submission_blocked":
            require(self.pending["data"]["tool"] == "submit", "Only an ordinary submit can be blocked")
            self.receipt(self.pending, {"status": "not_executed_ordinary_submission_blocked", "event": event})
        elif event["kind"] in {"write_file", "post_channel", "submit", "tool_result"}:
            data = self.pending["data"]
            tool = event.get("tool") if event["kind"] == "tool_result" else event["kind"]
            require(data["tool"] == tool, "Public tool result does not match pending native call")
            args = strict_json(data["arguments"])
            require(all(event.get(key) == value for key, value in args.items()), "Native result arguments drift")
            self.receipt(self.pending, {"status": "applied", "event": event})
        else:
            return
        self.pending = None


def validate_once(root, plan, approval, request, transport):
    from .admission import prepare_request, validate_binding
    from .diagnostic_dispatch import ObservedTransport
    from .durable import DurableLedger
    root = Path(root).resolve()
    validate_binding(plan, approval, root, transport.endpoint)
    config = plan["native_recovery"]
    require(config["phase"] == "validation" and fingerprint(request) == config["request_sha256"],
            "Exact one native preflight request required")
    prepare_request(request, "ordinary", plan)
    with ExitStack() as stack:
        history_locks(stack, config["history"])
        require(not (root / "VALIDATION_STARTED.json").exists(), "Already attempted; never replay validation")
        ledger = DurableLedger(root, plan, approval, create=True)
        stack.callback(ledger.close)
        write_new(root / "VALIDATION_STARTED.json", {"at": datetime.now(timezone.utc).isoformat(),
            "plan_sha256": fingerprint(plan), "prior_unknown_held_USD": "3.432000",
            "prior_settled_USD_upper": "0.013762650", "environment_tools_allowed": False})
        observed, error = ObservedTransport(transport, root), None
        try:
            result = ledger.call(plan["episodes"][0], "ordinary", 0, request, observed)
            require(not result["replayed_without_send"], "No native validation cache replay")
        except Exception as failure:
            error = type(failure).__name__
        rows = [dict(row) for row in ledger.connection.execute(
            "select id,state,reserved,charged,input_tokens,output_tokens,response_sha256,response_bytes,"
            "error_type,diagnostic from calls")]
        for row in rows:
            if row["diagnostic"] is not None:
                row["diagnostic"] = strict_json(row["diagnostic"])
        receipt = {"schema": RECOVERY_VERSION, "plan_sha256": fingerprint(plan),
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
    require(plan["native_recovery"]["phase"] == "batch", "Only validated native batch")
    with ExitStack() as stack:
        history_locks(stack, plan["native_recovery"]["history"])
        return run_fresh(root, plan, approval, transport, on_group)


if __name__ == "__main__":
    import argparse
    from .admission import validate_binding
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
    if plan["native_recovery"]["phase"] == "validation":
        result = validate_once(root, plan, approval, strict_json((root / "REQUEST.json").read_bytes()), transport)
    else:
        def group_report(rows, budget):
            print(canonical({"kind": "actual_group_complete", "rows": rows, "budget": budget}), flush=True)
        result = run_batch(root, plan, approval, transport, group_report)
    print(canonical(result), flush=True)
