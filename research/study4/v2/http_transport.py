"""One-shot HTTP adapter: no implicit credentials, proxy, redirects or retries."""
import http.client
import socket
import threading
import time
from urllib.parse import urlsplit

from .contracts import require


class TransportFailure(RuntimeError):
    pass


def validate_endpoint(endpoint, mode):
    parsed = urlsplit(endpoint)
    require(not parsed.username and not parsed.password and not parsed.query and not parsed.fragment,
            "Credential/query/fragment in endpoint forbidden")
    if mode == "local_test":
        require(parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and
                parsed.port is not None and 0 < parsed.port < 65536 and parsed.path == "/v1/responses",
                "Test transport must be literal loopback, not localhost/DNS/proxy")
    else:
        require(mode == "provider" and endpoint == "https://api.openai.com/v1/responses",
                "Unapproved provider endpoint")


class HTTPTransport:
    def __init__(self, endpoint, mode, *, credential=None, timeout=30, max_response_bytes=1_048_576):
        validate_endpoint(endpoint, mode)
        require(type(timeout) is int and timeout > 0 and type(max_response_bytes) is int and max_response_bytes > 0,
                "Explicit HTTP resource bounds")
        require((mode == "local_test" and credential is None) or
                (mode == "provider" and (credential is None or isinstance(credential, str))), "Credential scope")
        self.endpoint, self.mode = endpoint, mode
        self.timeout, self.max_response_bytes = timeout, max_response_bytes
        self._credential = credential

    def send(self, permit, body):
        from .durable import _Permit
        require(type(permit) is _Permit, "A genuine durable admission permit is required")
        permit.consume(body, self.endpoint, self.mode)  # Before DNS or socket.
        require(self.timeout <= permit.ledger.plan["http_timeout_seconds"] and
                self.max_response_bytes <= permit.ledger.plan["max_response_bytes"], "Transport limit drift")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.mode == "provider":
            require(self._credential and "\n" not in self._credential and "\r" not in self._credential,
                    "Explicit ephemeral credential required")
            headers["Authorization"] = "Bearer " + self._credential
        parsed = urlsplit(self.endpoint)
        connection_type = http.client.HTTPConnection if self.mode == "local_test" else http.client.HTTPSConnection
        connection = connection_type(parsed.hostname, parsed.port, timeout=self.timeout)
        timer, expired = None, threading.Event()
        started = time.monotonic()
        try:
            connection.connect()
            sock = connection.sock
            remaining = self.timeout - (time.monotonic() - started)
            require(remaining > 0, "HTTP connect exceeded deadline")
            def terminate():
                expired.set()
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    # The normal close may have won the race; expiration still rejects the result.
                    pass
            timer = threading.Timer(remaining, terminate)
            timer.daemon = True
            timer.start()
            connection.request("POST", parsed.path, body, headers)
            with connection.getresponse() as response:
                require(response.status == 200 and
                        response.getheader("Content-Type", "").split(";", 1)[0].strip() == "application/json",
                        "Non-JSON/non-success/redirect HTTP response")
                raw = response.read(self.max_response_bytes + 1)
            require(not expired.is_set() and time.monotonic() - started <= self.timeout, "HTTP deadline expired")
            require(len(raw) <= self.max_response_bytes, "HTTP response byte cap exceeded")
            return raw
        except (http.client.HTTPException, TimeoutError, OSError):
            raise TransportFailure("HTTP outcome unresolved; preserve reservation, no retry") from None
        finally:
            if timer is not None:
                timer.cancel()
                timer.join()
            connection.close()
