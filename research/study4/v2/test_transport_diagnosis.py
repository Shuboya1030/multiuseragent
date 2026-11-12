from decimal import Decimal
import errno
import http.client
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from .budget import BudgetBlocked
from .contracts import canonical, strict_json
from .durable import DurableLedger
from .http_transport import HTTPTransport, TransportFailure
from .test_durable_preflight import success
from .test_provider_bound import control_request, model_max_config, standard_mock

SENSITIVE = "LOCAL_SENSITIVE_EXCEPTION_MESSAGE_NOT_FOR_STORAGE"
CHILD_FAILURES_OBSERVED = []


def injected_call(ledger, kind, close_errors=False):
    request = control_request()
    connection = MagicMock()
    response = connection.getresponse.return_value
    response.status = 200
    response.getheader.return_value = "application/json"
    response.read.return_value = canonical(standard_mock(success(canonical(request).encode()))).encode()
    timer = MagicMock()
    failures = {"connect": socket.gaierror(errno.EIO, SENSITIVE),
                "send": BrokenPipeError(errno.EPIPE, SENSITIVE),
                "headers": http.client.RemoteDisconnected(SENSITIVE),
                "read": http.client.IncompleteRead(SENSITIVE.encode()),
                "interrupt": KeyboardInterrupt(SENSITIVE)}
    if kind in failures:
        target = {"connect": connection.connect, "send": connection.request,
                  "headers": connection.getresponse, "read": response.read,
                  "interrupt": connection.request}[kind]
        target.side_effect = failures[kind]
    elif kind == "status":
        response.status = 429
    elif kind == "content_type":
        response.getheader.return_value = SENSITIVE
    elif kind == "byte_limit":
        response.read.return_value = b"x" * (ledger.plan["max_response_bytes"] + 1)
    elif kind == "deadline":
        timer.start.side_effect = lambda: None
    elif kind == "unknown_exception":
        class LOCAL_SENSITIVE_TYPE_NOT_FOR_STORAGE(OSError):
            pass
        connection.connect.side_effect = LOCAL_SENSITIVE_TYPE_NOT_FOR_STORAGE(SENSITIVE)
    if close_errors:
        response.close.side_effect = OSError(errno.EIO, SENSITIVE)
        connection.close.side_effect = RuntimeError(SENSITIVE)
    def timer_factory(delay, callback):
        if kind == "deadline":
            connection.sock.shutdown.side_effect = OSError(errno.EIO, SENSITIVE)
            timer.start.side_effect = callback
        return timer
    transport = HTTPTransport(ledger.plan["endpoint"], ledger.plan["mode"])
    with patch("research.study4.v2.http_transport.http.client.HTTPConnection", return_value=connection), \
            patch("research.study4.v2.http_transport.threading.Timer", side_effect=timer_factory), \
            patch("socket.getaddrinfo", side_effect=AssertionError("No external DNS in injected tests")):
        ledger.call("ep-0", "control", 0, request, transport)


def local_config(root):
    plan, approval = model_max_config(root)
    return plan, approval


def write_failed_transport_in_child(config_path, stage):
    config_path = Path(config_path)
    config = strict_json(config_path.read_bytes())
    ledger = DurableLedger(config_path.parent, config["plan"], config["approval"], create=True)
    try:
        try:
            injected_call(ledger, stage)
        except TransportFailure:
            pass
        else:
            raise AssertionError("Injected transport must fail")
    finally:
        ledger.close()


class TransportDiagnosisTests(unittest.TestCase):
    def test_four_HTTP_stages_survive_child_exit_reopen_keep_reserve_no_retry_or_sensitive_bytes(self):
        for stage in ("connect", "send", "headers", "read"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(prefix="study4_v2_http_stage_") as folder:
                root = Path(folder)
                plan, approval = local_config(root)
                path = root / "LOCAL_CHILD_CONFIG.json"
                path.write_text(canonical({"plan": plan, "approval": approval}), encoding="utf-8")
                code = ("from research.study4.v2.test_transport_diagnosis import write_failed_transport_in_child;"
                        "import sys; write_failed_transport_in_child(sys.argv[1],sys.argv[2])")
                child = subprocess.run([sys.executable, "-c", code, str(path), stage],
                                       capture_output=True, timeout=30)
                self.assertEqual(child.returncode, 0, child.stderr.decode(errors="replace"))
                self.assertNotIn(SENSITIVE.encode(), child.stdout + child.stderr)
                ledger = DurableLedger(root, plan, approval, create=False)
                try:
                    row = ledger.connection.execute("select * from calls").fetchone()
                    diagnostic = strict_json(row["diagnostic"])["transport"]
                    self.assertEqual(diagnostic["stage"], stage)
                    self.assertEqual(row["state"], "unknown")
                    self.assertEqual(Decimal(ledger.status()["held_USD_upper"]), Decimal(".858"))
                    self.assertIsNone(row["charged"])
                    self.assertEqual(diagnostic["cleanup_errors"], [])
                    with patch("socket.getaddrinfo") as dns:
                        with self.assertRaises(BudgetBlocked):
                            ledger.call("ep-0", "control", 1, control_request(),
                                        HTTPTransport(plan["endpoint"], plan["mode"]))
                        dns.assert_not_called()
                    CHILD_FAILURES_OBSERVED.append({"stage": stage, "child_returncode": child.returncode,
                                                   "state": row["state"], "held_USD": row["reserved"],
                                                   "diagnostic": diagnostic})
                finally:
                    ledger.close()
                for file in root.iterdir():
                    if file.is_file():
                        self.assertNotIn(SENSITIVE.encode(), file.read_bytes())

    def test_status_content_type_deadline_and_byte_limit_remain_rejections_with_safe_metrics(self):
        for stage in ("status", "content_type", "deadline", "byte_limit"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(prefix="study4_v2_http_contract_") as folder:
                root = Path(folder)
                plan, approval = local_config(root)
                ledger = DurableLedger(root, plan, approval, create=True)
                try:
                    with self.assertRaises(ValueError):
                        injected_call(ledger, stage)
                    row = ledger.connection.execute("select * from calls").fetchone()
                    diagnostic = strict_json(row["diagnostic"])["transport"]
                    self.assertEqual(diagnostic["stage"], stage)
                    self.assertEqual(row["state"], "unknown")
                    self.assertNotIn(SENSITIVE, canonical(diagnostic))
                    if stage == "status":
                        self.assertEqual(diagnostic["http_status"], 429)
                    if stage == "content_type":
                        self.assertFalse(diagnostic["content_type_json"])
                    if stage == "deadline":
                        self.assertTrue(diagnostic["deadline_expired"])
                        self.assertEqual(diagnostic["cleanup_errors"][0]["operation"], "deadline_shutdown")
                    if stage == "byte_limit":
                        self.assertEqual(diagnostic["response_bytes_observed"], plan["max_response_bytes"] + 1)
                finally:
                    ledger.close()

    def test_primary_read_failure_preserved_with_response_and_connection_cleanup_failures(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_http_cleanup_primary_") as folder:
            root = Path(folder)
            plan, approval = local_config(root)
            ledger = DurableLedger(root, plan, approval, create=True)
            try:
                with self.assertRaises(TransportFailure):
                    injected_call(ledger, "read", close_errors=True)
                diagnostic = strict_json(ledger.connection.execute("select diagnostic from calls").fetchone()[0])
                diagnostic = diagnostic["transport"]
                self.assertEqual(diagnostic["stage"], "read")
                self.assertEqual(diagnostic["cause_type"], "IncompleteRead")
                self.assertEqual([x["operation"] for x in diagnostic["cleanup_errors"]],
                                 ["response_close", "connection_close"])
                self.assertNotIn(SENSITIVE, canonical(diagnostic))
                self.assertEqual(ledger.status()["unknown"], 1)
            finally:
                ledger.close()

    def test_cleanup_failure_after_valid_body_is_unknown_not_success_or_settlement(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_http_cleanup_success_") as folder:
            root = Path(folder)
            plan, approval = local_config(root)
            ledger = DurableLedger(root, plan, approval, create=True)
            try:
                with self.assertRaises(TransportFailure):
                    injected_call(ledger, "success", close_errors=True)
                row = ledger.connection.execute("select * from calls").fetchone()
                self.assertEqual(strict_json(row["diagnostic"])["transport"]["stage"], "cleanup")
                self.assertIsNone(row["charged"])
                self.assertEqual(ledger.status()["settled"], 0)
            finally:
                ledger.close()

    def test_unknown_exception_class_and_interrupt_text_are_not_persisted(self):
        for kind in ("unknown_exception", "interrupt"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="study4_v2_http_safe_type_") as folder:
                root = Path(folder)
                plan, approval = local_config(root)
                ledger = DurableLedger(root, plan, approval, create=True)
                try:
                    with self.assertRaises((TransportFailure, KeyboardInterrupt)):
                        injected_call(ledger, kind)
                    diagnostic = strict_json(ledger.connection.execute("select diagnostic from calls").fetchone()[0])
                    self.assertNotIn("LOCAL_SENSITIVE", canonical(diagnostic))
                    if kind == "unknown_exception":
                        self.assertEqual(diagnostic["transport"]["cause_type"], "unrecognized")
                    else:
                        self.assertEqual(diagnostic["transport"]["cause_type"], "KeyboardInterrupt")
                        self.assertEqual(diagnostic["transport"]["stage"], "send")
                finally:
                    ledger.close()


if __name__ == "__main__":
    unittest.main()
