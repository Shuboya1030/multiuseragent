from contextlib import closing, contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from .admission import (pending_plan, prepare_request, root_binding, strict_json,
                        token_bound)
from .budget import BudgetBlocked
from .contracts import canonical, fingerprint
from .durable import BatchBusy, DurableLedger
from .http_transport import HTTPTransport
from .local_ceiling_check import make_case
from .mini_request import MODEL, build_request

HTTP_REQUESTS_OBSERVED = []
SUBPROCESS_OUTCOMES = []


def local_config(root, endpoint="http://127.0.0.1:9/v1/responses"):
    plan = pending_plan()
    plan.update(run_id="LOCAL_TEMP_TEST", mode="local_test", endpoint=endpoint,
                budget_cap_USD="1.00", episodes=["ep-0", "ep-1"],
                token_bound={"kind": "LOCAL_BYTE_IDENTITY_ONLY", "model": MODEL, "provider_framing_upper": 0})
    return plan, approval_for(root, plan)


def approval_for(root, plan):
    now = datetime.now(timezone.utc)
    return {"approved": True, "run_id": plan["run_id"], "plan_sha256": fingerprint(plan),
            "storage_root_sha256": root_binding(root), "budget_cap_USD": plan["budget_cap_USD"],
            "reference": "LOCAL_TEST_ONLY_NOT_USER_APPROVAL",
            "scope": "LOCAL_TEST_NOT_PAID_AUTHORIZATION",
            "not_before": (now - timedelta(minutes=1)).isoformat(), "expires": (now + timedelta(hours=1)).isoformat()}


def request():
    _, rt, _, _ = make_case("m-low-customer-mailing", "A")
    return build_request("control", rt.observe())


def success(body):
    return {"id": "local-response", "model": MODEL, "status": "completed", "error": None,
            "incomplete_details": None, "usage": {"input_tokens": len(body), "output_tokens": 10},
            "output": [{"type": "message", "role": "assistant", "content": [
                {"type": "output_text", "text": canonical({"action": "SELF", "person_id": None})}]}]}


class MockProvider:
    def __init__(self, plan, transform=None, count_file=None):
        self.endpoint, self.mode = plan["endpoint"], plan["mode"]
        self.transform, self.calls, self.count_file = transform, 0, count_file
        self.observed_states = []

    def send(self, permit, body):
        permit.consume(body, self.endpoint, self.mode)
        with closing(sqlite3.connect(permit.ledger.path)) as reader:
            row = reader.execute("select state,reserved from calls where id=?", (permit.call_id,)).fetchone()
        self.observed_states.append(row)
        self.calls += 1
        if self.count_file is not None:
            with Path(self.count_file).open("ab") as out:
                out.write(b"sent\n")
                out.flush()
                os.fsync(out.fileno())
        data = success(body)
        if self.transform is not None:
            data = self.transform(data)
        return data if isinstance(data, bytes) else canonical(data).encode("utf-8")


def subprocess_worker(config_path, stage):
    config = strict_json(Path(config_path).read_bytes())
    root = Path(config_path).parent
    try:
        ledger = DurableLedger(root, config["plan"], config["approval"], create=False)
    except BatchBusy:
        raise SystemExit(42)
    provider = MockProvider(config["plan"], count_file=root / "provider_calls.txt")
    def crash(where):
        if where == stage:
            os._exit(73)
    try:
        ledger.call("ep-0", "control", 0, config["request"], provider, crash)
    finally:
        ledger.close()


@contextmanager
def loopback_server(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01))
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1/responses"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


class DurableTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="study4_v2_preflight_test_")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.plan, self.approval = local_config(self.root)

    def ledger(self, create=True):
        ledger = DurableLedger(self.root, self.plan, self.approval, create=create)
        self.addCleanup(ledger.close)
        return ledger

    def worker(self, stage):
        path = self.root / "local_worker_config.json"
        path.write_text(canonical({"plan": self.plan, "approval": self.approval, "request": request()}), encoding="utf-8")
        code = ("from research.study4.v2.test_durable_preflight import subprocess_worker; "
                "import sys; subprocess_worker(sys.argv[1],sys.argv[2])")
        result = subprocess.run([sys.executable, "-c", code, str(path), stage], capture_output=True, timeout=15)
        SUBPROCESS_OUTCOMES.append({"stage": stage, "returncode": result.returncode})
        return result

    def test_pending_or_unmatched_authorization_blocks_before_files_dns_or_socket(self):
        cases = [(pending_plan(), None), (self.plan, None)]
        bad = deepcopy(self.approval)
        bad["budget_cap_USD"] = "55"
        cases.append((self.plan, bad))
        for plan, approval in cases:
            with self.subTest(approval=approval is None), patch("socket.getaddrinfo") as dns, \
                    patch("socket.create_connection") as connect:
                with self.assertRaises((ValueError, BudgetBlocked)):
                    DurableLedger(self.root, plan, approval, create=True)
                dns.assert_not_called()
                connect.assert_not_called()
                self.assertEqual(list(self.root.iterdir()), [])

    def test_expired_wrong_storage_or_runtime_binding_blocks_creation(self):
        approvals = []
        for key, value in (("expires", "2000-01-01T00:00:00+00:00"), ("storage_root_sha256", "0" * 64),
                           ("plan_sha256", "0" * 64), ("scope", "STUDY4_V2_INDEPENDENT_PAID")):
            record = deepcopy(self.approval)
            record[key] = value
            approvals.append(record)
        for approval in approvals:
            with self.assertRaises(ValueError):
                DurableLedger(self.root, self.plan, approval, create=True)
        plan = deepcopy(self.plan)
        plan["runtime"]["protocol"] = "changed"
        with self.assertRaisesRegex(ValueError, "Runtime/source"):
            DurableLedger(self.root, plan, approval_for(self.root, plan), create=True)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_byte_bound_is_only_proved_for_local_identity_and_unicode_bytes(self):
        for text in ("", "abc", "\u4e2d\u6587", "\U0001f600", '"\\\n', "\u200d\u00e9"):
            raw = canonical({"text": text}).encode("utf-8")
            self.assertEqual(token_bound(raw, self.plan), len(raw))
            limited = deepcopy(self.plan)
            limited["max_request_bytes"] = len(raw)
            self.assertEqual(token_bound(raw, limited), len(raw))
            limited["max_request_bytes"] -= 1
            with self.assertRaisesRegex(ValueError, "byte cap"):
                token_bound(raw, limited)
        provider = deepcopy(self.plan)
        provider.update(mode="provider", endpoint="https://api.openai.com/v1/responses")
        approval = approval_for(self.root, provider)
        approval["scope"] = "STUDY4_V2_INDEPENDENT_PAID"
        with self.assertRaisesRegex(BudgetBlocked, "unproved"):
            DurableLedger(self.root, provider, approval, create=True)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_static_schema_is_local_validation_not_provider_acceptance(self):
        for raw in ('{"x":NaN}', '{"x":Infinity}', '{"x":1e309}'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "Nonfinite"):
                strict_json(raw)
        original = request()
        raw, bound, _, _ = prepare_request(original, "control", self.plan)
        self.assertEqual(bound, len(raw))
        for key, value in (("model", "different"), ("max_output_tokens", 999)):
            changed = deepcopy(original)
            changed[key] = value
            with self.assertRaises(ValueError):
                prepare_request(changed, "control", self.plan)
        limited = deepcopy(self.plan)
        limited["caps"]["input_tokens"] = bound - 1
        with self.assertRaisesRegex(ValueError, "context cap"):
            prepare_request(original, "control", limited)
        self.assertFalse(self.plan["actual_provider_schema_verified"])

    def test_persist_before_send_and_reopen_completed_without_resending(self):
        ledger = self.ledger()
        provider = MockProvider(self.plan)
        result = ledger.call("ep-0", "control", 0, request(), provider)
        self.assertFalse(result["replayed_without_send"])
        self.assertEqual(provider.observed_states[0][0], "sending")
        self.assertGreater(Decimal(provider.observed_states[0][1]), 0)
        ledger.close()
        reopened = self.ledger(False)
        new_provider = MockProvider(self.plan)
        recovered = reopened.call("ep-0", "control", 0, request(), new_provider)
        self.assertTrue(recovered["replayed_without_send"])
        self.assertEqual(recovered["data"], result["data"])
        self.assertEqual(new_provider.calls, 0)
        self.assertEqual(reopened.status()["settled"], 1)

    def test_reused_id_changed_request_and_mutated_binding_block_without_send(self):
        ledger = self.ledger()
        provider = MockProvider(self.plan)
        ledger.call("ep-0", "control", 0, request(), provider)
        changed = request()
        body = strict_json(changed["input"][1]["content"])
        body["state"]["contact_cost"] = 1
        changed["input"][1]["content"] = canonical(body)
        with self.assertRaisesRegex(ValueError, "changed request"):
            ledger.call("ep-0", "control", 0, changed, provider)
        ledger.plan["budget_cap_USD"] = "55"
        with self.assertRaisesRegex(ValueError, "Live config"):
            ledger.call("ep-0", "control", 1, request(), provider)
        self.assertEqual(provider.calls, 1)

    def test_batch_process_exclusion_and_no_create_overwrite(self):
        ledger = self.ledger()
        child = self.worker("never")
        self.assertEqual(child.returncode, 42, child.stderr.decode(errors="replace"))
        with self.assertRaises(BatchBusy):
            DurableLedger(self.root, self.plan, self.approval, create=True)
        ledger.close()
        with self.assertRaisesRegex(ValueError, "Never recreate"):
            DurableLedger(self.root, self.plan, self.approval, create=True)

    def test_real_process_crash_reservation_or_sent_becomes_unknown_without_retry(self):
        for stage, sent in (("after_reserve", 0), ("before_send", 0), ("after_send", 1)):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(prefix="study4_v2_crash_test_") as folder:
                previous = self.root, self.plan, self.approval
                self.root = Path(folder)
                self.plan, self.approval = local_config(self.root)
                ledger = DurableLedger(self.root, self.plan, self.approval, create=True)
                ledger.close()
                child = self.worker(stage)
                self.assertEqual(child.returncode, 73, child.stderr.decode(errors="replace"))
                reopened = DurableLedger(self.root, self.plan, self.approval, create=False)
                try:
                    self.assertEqual(reopened.status()["unknown"], 1)
                    self.assertGreater(Decimal(reopened.status()["held_USD_upper"]), 0)
                    provider = MockProvider(self.plan)
                    with self.assertRaises(BudgetBlocked):
                        reopened.call("ep-0", "control", 0, request(), provider)
                    with self.assertRaises(BudgetBlocked):
                        reopened.call("ep-1", "control", 0, request(), provider)
                    self.assertEqual(provider.calls, 0)
                    counts = self.root / "provider_calls.txt"
                    self.assertEqual(counts.read_bytes().count(b"sent") if counts.exists() else 0, sent)
                finally:
                    reopened.close()
                    self.root, self.plan, self.approval = previous

    def test_real_process_crash_after_settle_replays_and_does_not_pay_again(self):
        self.ledger().close()
        child = self.worker("after_settle")
        self.assertEqual(child.returncode, 73, child.stderr.decode(errors="replace"))
        reopened = self.ledger(False)
        provider = MockProvider(self.plan)
        self.assertTrue(reopened.call("ep-0", "control", 0, request(), provider)["replayed_without_send"])
        self.assertEqual(provider.calls, 0)
        self.assertEqual((self.root / "provider_calls.txt").read_bytes().count(b"sent"), 1)

    def test_unknown_usage_parse_model_and_resource_errors_hold_max_and_stop(self):
        def missing_usage(data):
            del data["usage"]
            return data
        def excess_usage(data):
            data["usage"]["input_tokens"] += 1
            return data
        def wrong_model(data):
            data["model"] = "different"
            return data
        def invalid_tool(data):
            data["output"][0]["content"][0]["text"] = '{"action":"SECRET","person_id":null}'
            return data
        mutations = [missing_usage, excess_usage, wrong_model, invalid_tool,
                     lambda _: b"not-json", lambda _: b'{"a":1,"a":2}',
                     lambda _: b"x" * (self.plan["max_response_bytes"] + 1)]
        for transform in mutations:
            with self.subTest(transform=transform.__name__), tempfile.TemporaryDirectory(
                    prefix="study4_v2_unknown_test_") as folder:
                root = Path(folder)
                plan, approval = local_config(root)
                ledger = DurableLedger(root, plan, approval, create=True)
                try:
                    provider = MockProvider(plan, transform)
                    with self.assertRaises((ValueError, KeyError)):
                        ledger.call("ep-0", "control", 0, request(), provider)
                    state = ledger.status()
                    self.assertEqual(state["unknown"], 1)
                    self.assertGreater(Decimal(state["held_USD_upper"]), 0)
                    diagnostic = strict_json(ledger.connection.execute("select diagnostic from calls").fetchone()[0])
                    self.assertIsInstance(diagnostic, dict)
                    self.assertNotIn("output", diagnostic)
                    with self.assertRaises(BudgetBlocked):
                        ledger.call("ep-0", "control", 1, request(), provider)
                    self.assertEqual(provider.calls, 1)
                finally:
                    ledger.close()

    def test_duplicate_embedded_tool_arguments_cannot_silently_change_the_action(self):
        _, rt, _, _ = make_case("m-low-customer-mailing", "A")
        ordinary = build_request("ordinary", rt.observe())
        def duplicate_arguments(data):
            output = {"tool": "write_file", "arguments":
                      '{"path":"/workspace/a","path":"/workspace/b","content":"x"}'}
            data["output"][0]["content"][0]["text"] = canonical(output)
            return data
        ledger = self.ledger()
        provider = MockProvider(self.plan, duplicate_arguments)
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            ledger.call("ep-0", "ordinary", 0, ordinary, provider)
        self.assertEqual(ledger.status()["unknown"], 1)

    def test_tiny_usd_call_total_tokens_and_episode_limits_prevent_send(self):
        for key, value in (("budget_cap_USD", ".000001"), ("total_input_tokens", 1),
                           ("total_output_tokens", 1)):
            with self.subTest(key=key):
                plan = deepcopy(self.plan)
                plan[key] = value
                ledger = DurableLedger(self.root, plan, approval_for(self.root, plan), create=True)
                try:
                    provider = MockProvider(plan)
                    with self.assertRaises(BudgetBlocked):
                        ledger.call("ep-0", "control", 0, request(), provider)
                    self.assertEqual(provider.calls, 0)
                    self.assertEqual(ledger.status()["calls"], 0)
                finally:
                    path = ledger.path
                    ledger.close()
                    path.unlink()
        ledger = self.ledger()
        provider = MockProvider(self.plan)
        with self.assertRaisesRegex(ValueError, "frozen episode"):
            ledger.call("unplanned", "control", 0, request(), provider)
        self.assertEqual(provider.calls, 0)

    def test_socket_failure_is_one_unknown_attempt_with_no_retry(self):
        class Fail(MockProvider):
            def send(self, permit, body):
                super().send(permit, body)
                raise TimeoutError("LOCAL simulated ambiguous send")
        ledger = self.ledger()
        provider = Fail(self.plan)
        with self.assertRaises(TimeoutError):
            ledger.call("ep-0", "control", 0, request(), provider)
        self.assertEqual(ledger.status()["unknown"], 1)
        self.assertEqual(provider.calls, 1)

    def test_aggregate_call_token_and_per_operation_limits_survive_settlement(self):
        bound = len(canonical(request()).encode("utf-8"))
        for key, value, allowed in (("max_calls", 1, 1), ("total_input_tokens", bound, 1),
                                    ("total_output_tokens", 1024, 1), ("max_calls", 100, 24)):
            with self.subTest(key=key, allowed=allowed), tempfile.TemporaryDirectory(
                    prefix="study4_v2_aggregate_test_") as folder:
                root = Path(folder)
                plan, _ = local_config(root)
                plan[key] = value
                ledger = DurableLedger(root, plan, approval_for(root, plan), create=True)
                try:
                    provider = MockProvider(plan)
                    for index in range(allowed):
                        ledger.call("ep-0", "control", index, request(), provider)
                    with self.assertRaises(BudgetBlocked):
                        ledger.call("ep-0", "control", allowed, request(), provider)
                    self.assertEqual(provider.calls, allowed)
                    self.assertEqual(ledger.status()["settled"], allowed)
                    self.assertLessEqual(Decimal(ledger.status()["occupied_USD_upper"]), Decimal(plan["budget_cap_USD"]))
                finally:
                    ledger.close()


class HTTPTests(unittest.TestCase):
    def test_loopback_http_observes_committed_sending_no_auth_and_replay_skips_socket(self):
        observed = []
        with tempfile.TemporaryDirectory(prefix="study4_v2_http_test_") as folder:
            root = Path(folder)
            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *_):
                    pass
                def do_POST(self):
                    HTTP_REQUESTS_OBSERVED.append({"case": "success", "path": self.path, "host": "literal-loopback"})
                    body = self.rfile.read(int(self.headers["Content-Length"]))
                    with closing(sqlite3.connect(root / "LOCAL_TEMP_TEST.sqlite3")) as reader:
                        state = reader.execute("select state from calls").fetchone()[0]
                    observed.append((state, self.headers.get("Authorization"), self.path))
                    raw = canonical(success(body)).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
            with loopback_server(Handler) as endpoint:
                plan, approval = local_config(root, endpoint)
                ledger = DurableLedger(root, plan, approval, create=True)
                try:
                    transport = HTTPTransport(endpoint, "local_test")
                    first = ledger.call("ep-0", "control", 0, request(), transport)
                    again = ledger.call("ep-0", "control", 0, request(), transport)
                    self.assertFalse(first["replayed_without_send"])
                    self.assertTrue(again["replayed_without_send"])
                    self.assertEqual(observed, [("sending", None, "/v1/responses")])
                finally:
                    ledger.close()

    def test_redirect_is_not_followed_and_response_size_cap_retains_unknown(self):
        for kind in ("redirect", "oversize"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="study4_v2_http_fail_") as folder:
                count = []
                class Handler(BaseHTTPRequestHandler):
                    def log_message(self, *_):
                        pass
                    def do_POST(self):
                        HTTP_REQUESTS_OBSERVED.append({"case": kind, "path": self.path, "host": "literal-loopback"})
                        self.rfile.read(int(self.headers["Content-Length"]))
                        count.append(self.path)
                        self.send_response(307 if kind == "redirect" else 200)
                        self.send_header("Location", "/must-not-follow")
                        self.send_header("Content-Type", "application/json")
                        raw = b"x" * 101
                        self.send_header("Content-Length", str(len(raw)))
                        self.end_headers()
                        self.wfile.write(raw)
                with loopback_server(Handler) as endpoint:
                    plan, approval = local_config(Path(folder), endpoint)
                    ledger = DurableLedger(folder, plan, approval, create=True)
                    try:
                        transport = HTTPTransport(endpoint, "local_test", max_response_bytes=100)
                        with self.assertRaises(ValueError):
                            ledger.call("ep-0", "control", 0, request(), transport)
                        self.assertEqual(ledger.status()["unknown"], 1)
                        self.assertEqual(count, ["/v1/responses"])
                    finally:
                        ledger.close()

    def test_loopback_absolute_deadline_and_cleanup(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_POST(self):
                HTTP_REQUESTS_OBSERVED.append({"case": "deadline", "path": self.path, "host": "literal-loopback"})
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "2")
                self.end_headers()
                time.sleep(2)
                try:
                    self.wfile.write(b"{}")
                except (BrokenPipeError, ConnectionResetError):
                    pass
        with tempfile.TemporaryDirectory(prefix="study4_v2_deadline_test_") as folder, loopback_server(Handler) as endpoint:
            plan, approval = local_config(Path(folder), endpoint)
            ledger = DurableLedger(folder, plan, approval, create=True)
            try:
                started = time.monotonic()
                with self.assertRaises((ValueError, RuntimeError)):
                    ledger.call("ep-0", "control", 0, request(), HTTPTransport(endpoint, "local_test", timeout=1))
                self.assertLess(time.monotonic() - started, 3.5)
                self.assertEqual(ledger.status()["unknown"], 1)
            finally:
                ledger.close()

    def test_endpoint_and_permit_gates_do_not_resolve_external_hosts(self):
        with patch("socket.getaddrinfo") as dns, patch("socket.create_connection") as connect:
            for endpoint in ("http://localhost:1/v1/responses", "http://example.com/v1/responses",
                             "http://127.0.0.1:1/v1/responses?secret=x"):
                with self.assertRaises(ValueError):
                    HTTPTransport(endpoint, "local_test")
            with self.assertRaisesRegex(ValueError, "genuine durable"):
                HTTPTransport("http://127.0.0.1:1/v1/responses", "local_test").send(None, b"{}")
            dns.assert_not_called()
            connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
