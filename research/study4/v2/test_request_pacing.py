"""Fake clock plus local HTTP: no provider calls and no retry after429."""
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace
import threading
import unittest
from unittest.mock import patch

from .http_transport import HTTPTransport, TransportValidationFailure
from .request_pacing import PacedTransport


class Clock:
    def __init__(self):
        self.time = 0.0

    def now(self):
        return self.time

    def sleep(self, seconds):
        self.time += seconds


class Journal:
    def __init__(self):
        self.events = []

    def append(self, event):
        self.events.append(event)


class PacingTests(unittest.TestCase):
    def test_one_gate_shared_by_ordinary_question_npc_and_long_reset(self):
        clock, journal, starts = Clock(), Journal(), []

        class Transport:
            endpoint, mode = "http://127.0.0.1:9/v1/responses", "local_test"

            def send(self, permit, body):
                starts.append((permit.call_id, clock.now()))
                clock.sleep(1)
                return b"response"

        paced = PacedTransport(Transport(), journal, prior_error={"reset_tokens_milliseconds": 90000},
                               clock=clock.now, sleep=clock.sleep, wall=clock.now)
        for operation in ("ordinary", "question", "npc"):
            paced.send(SimpleNamespace(call_id=operation), b"request")
        self.assertEqual(starts, [("ordinary", 90), ("question", 111), ("npc", 132)])
        self.assertTrue(all(e["network_deadline_not_started"] for e in journal.events
                            if e["kind"] == "pre_send_wait"))

    def test_local429_wait_is_outside_http_deadline_and_never_retried(self):
        clock, journal, requests = Clock(), Journal(), []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                requests.append(self.path)
                body = b'{"error":{"type":"tokens","code":"rate_limit_exceeded"}}'
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Retry-After", "120")
                self.send_header("x-ratelimit-reset-tokens", "150s")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        from .durable import _Permit
        permit = object.__new__(_Permit)
        permit.call_id = "ordinary62-new-attempt"
        permit.ledger = SimpleNamespace(plan={"http_timeout_seconds": 30, "max_response_bytes": 1048576})
        permit.used = False
        transport = HTTPTransport(f"http://127.0.0.1:{server.server_port}/v1/responses", "local_test")
        paced = PacedTransport(transport, journal, clock=clock.now, sleep=clock.sleep, wall=clock.now)
        try:
            with patch.object(_Permit, "consume", lambda p, *args: setattr(p, "used", True)):
                with self.assertRaises(TransportValidationFailure) as failure:
                    paced.send(permit, b"{}")
                self.assertEqual(failure.exception.diagnostic["http_status"], 429)
                self.assertGreaterEqual(clock.now(), 60)
                self.assertGreaterEqual(paced.next_start, clock.now() + 150)
                clock.sleep(1000)
                with self.assertRaisesRegex(ValueError, "unknown"):
                    paced.send(permit, b"{}")
            self.assertEqual(requests, ["/v1/responses"])
            self.assertTrue(permit.used)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
