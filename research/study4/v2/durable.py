"""Independent durable reservations. Current execution is restricted to local tests."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import threading

from .admission import (decode_response, prepare_request, response_diagnostic, root_binding, strict_json,
                        validate_binding)
from .budget import BudgetBlocked, LocalBudget
from .contracts import canonical, fingerprint, require
from .provider_bound import reservation_output_bound
from .response_diagnosis import inspect_response_shape, ResponseStageError
from .recovery_guard import prior_hold, prior_settled


class BatchBusy(RuntimeError):
    pass


class BatchLock:
    """Kernel-held lifetime lock; leave the lock file in place to avoid unlink races."""
    def __init__(self, path):
        self.fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            if os.fstat(self.fd).st_size == 0:
                os.write(self.fd, b"0")
            os.lseek(self.fd, 0, os.SEEK_SET)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.fd)
            self.fd = None
            raise BatchBusy("Batch already owned; no second ledger/sender") from None

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


class _Permit:
    def __init__(self, ledger, call_id, body_sha256):
        self.ledger, self.call_id, self.body_sha256 = ledger, call_id, body_sha256
        self.used = False

    def consume(self, body, endpoint, mode):
        ledger = self.ledger
        require(fingerprint(ledger.plan) == ledger.metadata["plan_sha256"] and
                fingerprint(ledger.approval) == ledger.metadata["approval_sha256"], "Send binding mutated")
        validate_binding(ledger.plan, ledger.approval, ledger.root, endpoint)
        require(ledger.active_permit is self and not self.used and ledger.lock.fd is not None,
                "Missing/reused admission permit")
        require(endpoint == ledger.plan["endpoint"] and mode == ledger.plan["mode"] and
                hashlib.sha256(body).hexdigest() == self.body_sha256, "Transport/request binding changed")
        require(ledger.connection.execute("select state from calls where id=?", (self.call_id,)).fetchone()[0]
                == "sending", "Send not durably reserved")
        self.used = True


class DurableLedger:
    def __init__(self, root, plan, approval, *, create=False):
        self.root = Path(root).resolve()
        self.plan, self.approval = deepcopy(plan), deepcopy(approval)
        self.caps = validate_binding(plan, approval, self.root, plan["endpoint"])
        self.cap = Decimal(str(plan["budget_cap_USD"]))
        require(self.cap.is_finite() and self.cap > 0, "Positive independently matched cap required")
        require(re.fullmatch(r"[A-Za-z0-9_-]{1,80}", plan["run_id"]) is not None, "Unsafe batch identifier")
        require(self.root.is_dir(), "Explicit existing storage root required")
        self.path = self.root / (plan["run_id"] + ".sqlite3")
        self.lock = BatchLock(self.root / (plan["run_id"] + ".lock"))
        self.connection, self.active_permit = None, None
        self.thread_lock = threading.Lock()
        try:
            require((create and not self.path.exists()) or (not create and self.path.is_file()),
                    "Never recreate an existing/attempted batch")
            if create:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
                os.close(fd)
            self.connection = sqlite3.connect(self.path, isolation_level=None, timeout=0)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("pragma journal_mode=WAL")
            self.connection.execute("pragma synchronous=FULL")
            metadata = {"schema": "study4-v2-durable-3-transport-diagnostics", "plan_sha256": fingerprint(plan),
                        "approval_sha256": fingerprint(approval), "root_sha256": root_binding(self.root),
                        "mode": plan["mode"], "run_id": plan["run_id"]}
            self.metadata = metadata
            if create:
                with self.transaction():
                    self.connection.execute("create table metadata(payload text not null)")
                    self.connection.execute("""create table calls(
                        id text primary key, episode text not null, operation text not null,
                        request_sha256 text not null, state text not null
                        check(state in ('reserved','sending','settled','unknown')),
                        input_bound integer not null, output_bound integer not null,
                        reserved text not null, charged text, input_tokens integer, output_tokens integer,
                        result text, result_sha256 text, response_sha256 text, response_bytes integer,
                        error_type text, diagnostic text, created text not null, updated text not null)""")
                    self.connection.execute("create table audit(seq integer primary key,event text not null)")
                    self.connection.execute("insert into metadata values(?)", (canonical(metadata),))
            found = self.connection.execute("select payload from metadata").fetchall()
            require(len(found) == 1 and strict_json(found[0][0]) == metadata, "Immutable ledger binding mismatch")
            with self.transaction():
                interrupted = self.connection.execute(
                    "select id from calls where state in ('reserved','sending')").fetchall()
                for row in interrupted:
                    self.connection.execute(
                        "update calls set state='unknown',error_type='InterruptedOwner',updated=? where id=?",
                        (self.now(), row["id"]))
                    self.audit("recovered_unknown", call_id=row["id"])
        except BaseException:
            self.close()
            raise

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    @contextmanager
    def transaction(self):
        self.connection.execute("begin immediate")
        try:
            yield
            self.connection.execute("commit")
        except BaseException:
            self.connection.execute("rollback")
            raise

    def audit(self, event, **fields):
        self.connection.execute("insert into audit(event) values(?)",
                                (canonical({"event": event, "at": self.now(), **fields}),))

    def close(self):
        try:
            if self.connection is not None:
                self.connection.close()
                self.connection = None
        finally:
            self.lock.close()

    def status(self):
        rows = self.connection.execute("select * from calls").fetchall()
        settled = sum((Decimal(r["charged"]) for r in rows if r["state"] == "settled"), Decimal(0))
        external = prior_hold(self.plan)
        external_settled = prior_settled(self.plan)
        held = sum((Decimal(r["reserved"]) for r in rows if r["state"] != "settled"), Decimal(0)) + external
        return {"calls": len(rows), "settled": sum(r["state"] == "settled" for r in rows),
                "unknown": sum(r["state"] == "unknown" for r in rows),
                "in_flight": sum(r["state"] in {"reserved", "sending"} for r in rows),
                "occupied_USD_upper": str(settled + held + external_settled), "held_USD_upper": str(held),
                "cap_USD": str(self.cap), "mode": self.plan["mode"],
                "prior_unknown_held_USD": str(external), "prior_settled_USD_upper": str(external_settled)}

    def _reserve(self, call_id, episode, operation, request_hash, bound):
        with self.transaction():
            existing = self.connection.execute("select * from calls where id=?", (call_id,)).fetchone()
            if existing is not None:
                require(existing["request_sha256"] == request_hash and existing["episode"] == episode
                        and existing["operation"] == operation, "Once-only call ID changed request")
                if existing["state"] != "settled":
                    raise BudgetBlocked("Call unresolved; never resend or free its reservation")
                require(fingerprint(strict_json(existing["result"])) == existing["result_sha256"],
                        "Stored result integrity failure")
                return {"replayed_without_send": True, **strict_json(existing["result"])}
            rows = self.connection.execute("select * from calls").fetchall()
            if any(row["state"] != "settled" for row in rows):
                raise BudgetBlocked("Unresolved/unknown exposure stops the batch")
            output_bound = reservation_output_bound(self.plan)
            reservation = self.caps.charge(bound, output_bound)
            incoming = sum(r["input_tokens"] for r in rows) + bound
            outgoing = sum(r["output_tokens"] for r in rows) + output_bound
            operations = sum(r["episode"] == episode and r["operation"] == operation for r in rows)
            if (len(rows) >= self.plan["max_calls"] or incoming > self.plan["total_input_tokens"] or
                    outgoing > self.plan["total_output_tokens"] or
                    operations >= self.plan.get("operation_limits", LocalBudget.LIMITS)[operation] or
                    Decimal(self.status()["occupied_USD_upper"]) + reservation > self.cap):
                raise BudgetBlocked("Durable call/token/operation/USD cap reached before send")
            now = self.now()
            self.connection.execute("""insert into calls(
                id,episode,operation,request_sha256,state,input_bound,output_bound,reserved,created,updated)
                values(?,?,?,?,'reserved',?,?,?,?,?)""",
                (call_id, episode, operation, request_hash, bound, output_bound, str(reservation), now, now))
            self.audit("reserved", call_id=call_id, request_sha256=request_hash, reserved_USD=str(reservation))
        return None

    def call(self, episode, operation, index, request, transport, fault_hook=None):
        require(self.thread_lock.acquire(blocking=False), "One call at a time per batch")
        try:
            return self._call(episode, operation, index, request, transport, fault_hook or (lambda _: None))
        finally:
            self.thread_lock.release()

    def _call(self, episode, operation, index, request, transport, fault):
        require(fingerprint(self.plan) == self.metadata["plan_sha256"] and
                fingerprint(self.approval) == self.metadata["approval_sha256"], "Live config/authorization changed")
        validate_binding(self.plan, self.approval, self.root, transport.endpoint)
        require(transport.mode == self.plan["mode"], "Transport authorization scope mismatch")
        require(episode in self.plan["episodes"] and type(index) is int and index >= 0,
                "Only frozen episode/call identities")
        if self.plan.get("dispatcher_version") is not None:
            require(operation == "ordinary" and index == 0 and
                    fingerprint(request) == self.plan["request_sha256"], "Only frozen single ordinary diagnostic")
        continuation = self.plan.get("continuation")
        if continuation is not None and continuation["phase"] == "validation":
            require(operation == "ordinary" and index == 0 and
                    fingerprint(request) == continuation["request_sha256"],
                    "Only frozen single prompt-v2 validation")
        native = self.plan.get("native_recovery")
        if native is not None and native["phase"] == "validation":
            require(operation == "ordinary" and index == 0 and fingerprint(request) == native["request_sha256"],
                    "Only exact single native validation")
        body, bound, observation, assistance = prepare_request(request, operation, self.plan)
        call_id = f"{episode}:{operation}:{index}"
        cached = self._reserve(call_id, episode, operation, hashlib.sha256(body).hexdigest(), bound)
        if cached is not None:
            return cached
        raw = None
        try:
            fault("after_reserve")
            with self.transaction():
                self.connection.execute("update calls set state='sending',updated=? where id=?", (self.now(), call_id))
                self.audit("send_permitted", call_id=call_id)
            permit = _Permit(self, call_id, hashlib.sha256(body).hexdigest())
            self.active_permit = permit
            fault("before_send")
            raw = transport.send(permit, body)
            require(permit.used, "Transport did not consume durable admission")
            require(isinstance(raw, bytes) and len(raw) <= self.plan["max_response_bytes"], "Response byte cap")
            fault("after_send")
            result = decode_response(raw, operation, observation, assistance, self.plan, bound)
            usage = result["usage"]
            charge = self.caps.charge(usage["input_tokens"], usage["output_tokens"])
            with self.transaction():
                row = self.connection.execute("select reserved from calls where id=?", (call_id,)).fetchone()
                require(charge <= Decimal(row["reserved"]), "Cost exceeds reservation")
                self.connection.execute("""update calls set state='settled',charged=?,input_tokens=?,output_tokens=?,
                    result=?,result_sha256=?,response_sha256=?,response_bytes=?,updated=? where id=?""",
                    (str(charge), usage["input_tokens"], usage["output_tokens"], canonical(result), fingerprint(result),
                     hashlib.sha256(raw).hexdigest(), len(raw), self.now(), call_id))
                self.audit("settled", call_id=call_id, result_sha256=fingerprint(result))
            fault("after_settle")
            return {"replayed_without_send": False, **result}
        except BaseException as error:
            with self.transaction():
                state = self.connection.execute("select state from calls where id=?", (call_id,)).fetchone()["state"]
                if state != "settled":
                    raw_bytes = raw if isinstance(raw, bytes) else None
                    diagnostic = response_diagnostic(raw_bytes) if raw_bytes is not None else {}
                    if raw_bytes is not None:
                        diagnostic["response_shape"] = inspect_response_shape(raw_bytes)
                    if isinstance(error, ResponseStageError):
                        diagnostic.update(validation_stage=error.stage, cause_type=error.cause_type,
                                          validator_frames=error.validator_frames)
                    from .http_transport import TransportFailure
                    if isinstance(error, TransportFailure):
                        diagnostic["transport"] = error.diagnostic
                    elif type(error) in (KeyboardInterrupt, SystemExit) and hasattr(error, "transport_diagnostic"):
                        diagnostic["transport"] = error.transport_diagnostic
                    self.connection.execute("""update calls set state='unknown',error_type=?,response_sha256=?,
                        response_bytes=?,diagnostic=?,updated=? where id=?""",
                        (type(error).__name__, hashlib.sha256(raw_bytes).hexdigest() if raw_bytes is not None else None,
                         len(raw_bytes) if raw_bytes is not None else None,
                         canonical(diagnostic),
                         self.now(), call_id))
                    self.audit("unknown", call_id=call_id, error_type=type(error).__name__)
            raise
        finally:
            self.active_permit = None
