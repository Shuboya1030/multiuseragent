"""Shared pre-send waiting, outside the HTTP deadline; errors never cause retries."""
import threading
import time

from .contracts import require
from .http_transport import TransportFailure

CONFIG = {"version": "phase0-shared-pre-send-pacing-1", "initial_seconds": 60,
          "spacing_seconds": 20, "unknown_stops_no_retry": True}


def server_wait(fields, wall):
    return max(
        float(fields.get("retry_after_seconds", 0)),
        float(fields.get("reset_tokens_milliseconds", 0)) / 1000,
        float(fields.get("reset_requests_milliseconds", 0)) / 1000,
        max(0, float(fields.get("retry_after_utc_unix_seconds", wall)) - wall))


class PacedTransport:
    def __init__(self, transport, journal, *, prior_error=None,
                 clock=time.monotonic, sleep=time.sleep, wall=time.time):
        self.transport, self.journal = transport, journal
        self.endpoint, self.mode = transport.endpoint, transport.mode
        self.clock, self.sleep, self.wall = clock, sleep, wall
        self.next_start = clock() + max(CONFIG["initial_seconds"], server_wait(prior_error or {}, wall()))
        self.stopped, self.last_start = False, None
        self.lock = threading.Lock()

    def send(self, permit, body):
        require(self.lock.acquire(blocking=False), "One shared pacing owner across all operations")
        try:
            require(not self.stopped, "Pacing cannot retry or continue after an unknown")
            wait = max(0, self.next_start - self.clock())
            self.journal.append({"kind": "pre_send_wait", "call_id": permit.call_id,
                                 "seconds": wait, "until_unix": self.wall() + wait,
                                 "network_deadline_not_started": True})
            while self.clock() < self.next_start:
                self.sleep(min(5, self.next_start - self.clock()))
            started = self.clock()
            self.journal.append({"kind": "paced_dispatch", "call_id": permit.call_id,
                                 "start_unix": self.wall(),
                                 "previous_start_spacing_seconds": (
                                     None if self.last_start is None else started - self.last_start)})
            self.last_start = started
            try:
                return self.transport.send(permit, body)
            except TransportFailure as error:
                fields = error.diagnostic.get("http_error", {})
                self.next_start = max(self.next_start, self.clock() + server_wait(fields, self.wall()))
                self.stopped = True
                raise
            except BaseException:
                self.stopped = True
                raise
            finally:
                # Completion+20 is at least as conservative as start+20.
                self.next_start = max(self.next_start, self.clock() + CONFIG["spacing_seconds"])
        finally:
            self.lock.release()
