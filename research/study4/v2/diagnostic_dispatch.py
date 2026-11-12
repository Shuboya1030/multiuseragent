"""Exactly one newly authorized diagnostic; no environment runtime or tool application."""
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import os
from pathlib import Path
import sqlite3

from .admission import prepare_request, response_diagnostic, validate_binding
from .contracts import fingerprint, require, strict_json
from .durable import BatchLock, DurableLedger
from .http_transport import HTTPTransport
from .paid_driver import write_new
from .response_diagnosis import inspect_response_shape

SOURCE = {"id": "19929303-1e63-4f65-8225-a57b583a8623", "revision": 4}
VERSION = "study4-single-diagnostic-v1"


def verify_prior(recovery):
    root = Path(recovery["prior_root"]).resolve()
    expected = recovery["prior_original_file_sha256"]
    require(root.is_dir() and recovery["prior_run_id"] + ".sqlite3" in expected,
            "Prior original evidence missing")
    for name, digest in expected.items():
        require(Path(name).name == name, "Prior evidence path must be a basename")
        if name == recovery["prior_run_id"] + ".lock":
            # Windows excludes byte reads while this process holds the byte-range mutex.
            continue
        require(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, "Prior evidence byte binding changed")
    db = root / (recovery["prior_run_id"] + ".sqlite3")
    wal, shm = Path(str(db) + "-wal"), Path(str(db) + "-shm")
    require(not wal.exists() or (wal.name in expected and wal.stat().st_size == 0),
            "Prior database has unapplied WAL frames; stop rather than infer state")
    require(not shm.exists() or shm.name in expected, "Prior sidecar not in frozen evidence")
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True)) as reader:
        rows = reader.execute("select state,reserved,charged from calls").fetchall()
    require(len(rows) == 1 and rows[0][0] == "unknown" and Decimal(rows[0][1]) == Decimal(".858")
            and rows[0][2] is None, "Original unknown must remain unmodified")
    return root


class ObservedTransport:
    """Persist only safe shape and whitelisted diagnostics while raw is still in memory."""
    def __init__(self, delegate, root):
        self.delegate, self.root = delegate, root
        self.endpoint, self.mode = delegate.endpoint, delegate.mode
        self.calls = 0

    def send(self, permit, body):
        require(self.calls == 0, "One diagnostic HTTP attempt only")
        self.calls += 1
        raw = self.delegate.send(permit, body)
        write_new(self.root / "ACTUAL_RESPONSE_SHAPE.json", {
            "actual_not_reconstruction": True, "response_sha256": hashlib.sha256(raw).hexdigest(),
            "response_bytes": len(raw), "shape": inspect_response_shape(raw),
            "diagnostic": response_diagnostic(raw)})
        return raw


def execute_once(root, plan, approval, request, transport):
    root = Path(root).resolve()
    validate_binding(plan, approval, root, transport.endpoint)
    recovery = plan["diagnostic_recovery"]
    require(plan["dispatcher_version"] == VERSION and fingerprint(request) == plan["request_sha256"],
            "Diagnostic request/dispatcher binding mismatch")
    prepare_request(request, "ordinary", plan)
    prior = verify_prior(recovery)
    lock = BatchLock(prior / (recovery["prior_run_id"] + ".lock"))
    ledger = None
    try:
        verify_prior(recovery)
        require(not (root / "DIAGNOSTIC_STARTED.json").exists(), "Already attempted; no diagnostic replay")
        ledger = DurableLedger(root, plan, approval, create=True)
        write_new(root / "DIAGNOSTIC_STARTED.json", {
            "at": datetime.now(timezone.utc).isoformat(), "plan_sha256": fingerprint(plan),
            "approval_sha256": fingerprint(approval), "request_sha256": fingerprint(request),
            "prior_unknown_held_USD": ".858000", "environment_tools_allowed": False})
        observed = ObservedTransport(transport, root)
        error = None
        try:
            result = ledger.call("diagnostic-only-no-tools", "ordinary", 0, request, observed)
            require(not result["replayed_without_send"], "No cache replay allowed")
        except Exception as failure:
            error = type(failure).__name__
        rows = [dict(row) for row in ledger.connection.execute(
            "select id,state,input_bound,output_bound,reserved,charged,input_tokens,output_tokens,"
            "response_sha256,response_bytes,error_type,diagnostic from calls")]
        for row in rows:
            if row["diagnostic"] is not None:
                row["diagnostic"] = strict_json(row["diagnostic"])
        receipt = {"schema": VERSION, "at": datetime.now(timezone.utc).isoformat(),
                   "plan_sha256": fingerprint(plan), "request_sha256": fingerprint(request),
                   "model_HTTP_attempts": observed.calls, "error_type": error,
                   "calls": rows, "budget": ledger.status(), "prior_unknown_unchanged": True,
                   "environment_tools_executed": 0, "complete_episodes": 0, "automatic_retry": False}
        verify_prior(recovery)
        write_new(root / "DIAGNOSTIC_FINAL.json", receipt)
        return receipt
    finally:
        if ledger is not None:
            ledger.close()
        lock.close()


if __name__ == "__main__":
    import argparse
    from .contracts import canonical
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    plan = strict_json((root / "PLAN.json").read_bytes())
    approval = strict_json((root / "APPROVAL.json").read_bytes())
    request = strict_json((root / "REQUEST.json").read_bytes())
    validate_binding(plan, approval, root, plan["endpoint"])
    verify_prior(plan["diagnostic_recovery"])
    require(not (root / "DIAGNOSTIC_STARTED.json").exists() and
            not (root / (plan["run_id"] + ".sqlite3")).exists(), "Never restart a diagnostic attempt")
    key = os.environ.get("OPENAI_API_KEY")
    require(isinstance(key, str) and key, "Explicit process credential injection missing")
    transport = HTTPTransport(plan["endpoint"], plan["mode"], credential=key,
                              timeout=plan["http_timeout_seconds"], max_response_bytes=plan["max_response_bytes"])
    print(canonical(execute_once(root, plan, approval, request, transport)), flush=True)
