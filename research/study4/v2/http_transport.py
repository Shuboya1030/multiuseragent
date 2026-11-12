"""One-shot HTTP adapter: no implicit credentials, proxy, redirects or retries."""
import http.client
import errno
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit

from .contracts import require


class TransportFailure(RuntimeError):
    def __init__(self, diagnostic):
        super().__init__("HTTP outcome unresolved; preserve reservation, no retry")
        self.diagnostic = diagnostic


class TransportValidationFailure(TransportFailure, ValueError):
    pass


TRANSPORT_DIAGNOSIS_VERSION = "study4-http-stages-1"
ERROR_TYPES = (OSError, TimeoutError, ConnectionError, ConnectionRefusedError, ConnectionResetError,
               ConnectionAbortedError, BrokenPipeError, socket.gaierror, ssl.SSLError,
               ssl.SSLCertVerificationError, http.client.HTTPException, http.client.RemoteDisconnected,
               http.client.IncompleteRead, http.client.BadStatusLine, http.client.CannotSendRequest,
               http.client.ResponseNotReady, ValueError, TypeError, RuntimeError, KeyboardInterrupt, SystemExit)


def error_summary(error):
    result = {"cause_type": type(error).__name__ if type(error) in ERROR_TYPES else "unrecognized"}
    if type(error) in ERROR_TYPES and isinstance(error, OSError) and type(error.errno) is int:
        if error.errno in errno.errorcode:
            result["os_errno"] = error.errno
    return result


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
        connection, response = None, None
        timer, expired = None, threading.Event()
        started = time.monotonic()
        stage, primary, cleanup_primary = "connect", None, None
        cleanup_errors = []
        metrics = {"timeout_seconds": self.timeout, "max_response_bytes": self.max_response_bytes,
                   "request_bytes": len(body)}
        try:
            connection = connection_type(parsed.hostname, parsed.port, timeout=self.timeout)
            connection.connect()
            sock = connection.sock
            stage = "deadline"
            remaining = self.timeout - (time.monotonic() - started)
            require(remaining > 0, "HTTP connect exceeded deadline")
            def terminate():
                nonlocal cleanup_primary
                expired.set()
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except BaseException as error:
                    if cleanup_primary is None:
                        cleanup_primary = error
                    cleanup_errors.append({"operation": "deadline_shutdown", **error_summary(error)})
            stage = "watchdog"
            timer = threading.Timer(remaining, terminate)
            timer.daemon = True
            timer.start()
            stage = "send"
            connection.request("POST", parsed.path, body, headers)
            stage = "headers"
            response = connection.getresponse()
            stage = "status"
            status = response.status
            if type(status) is int and 100 <= status <= 599:
                metrics["http_status"] = status
            require(type(status) is int and status == 200, "Non-success/redirect HTTP response")
            stage = "content_type"
            content_type = response.getheader("Content-Type", "")
            metrics["content_type_json"] = (isinstance(content_type, str) and
                                           content_type.split(";", 1)[0].strip() == "application/json")
            require(metrics["content_type_json"], "Non-JSON HTTP response")
            stage = "read"
            raw = response.read(self.max_response_bytes + 1)
            metrics["response_bytes_observed"] = len(raw)
            stage = "deadline"
            require(not expired.is_set() and time.monotonic() - started <= self.timeout, "HTTP deadline expired")
            stage = "byte_limit"
            require(len(raw) <= self.max_response_bytes, "HTTP response byte cap exceeded")
        except BaseException as error:
            primary = (stage, error)
        finally:
            def cleanup(operation, action):
                nonlocal cleanup_primary
                try:
                    action()
                except BaseException as error:
                    if cleanup_primary is None:
                        cleanup_primary = error
                    cleanup_errors.append({"operation": operation, **error_summary(error)})
            if timer is not None:
                cleanup("watchdog_cancel", timer.cancel)
                cleanup("watchdog_join", timer.join)
            if response is not None:
                cleanup("response_close", response.close)
            if connection is not None:
                cleanup("connection_close", connection.close)
        if primary is None and cleanup_errors:
            primary = ("cleanup", cleanup_primary)
        if primary is None and (expired.is_set() or time.monotonic() - started > self.timeout):
            primary = ("deadline", ValueError("HTTP deadline expired"))
        if primary is not None:
            stage, error = primary
            metrics["elapsed_ms"] = max(0, round((time.monotonic() - started) * 1000))
            metrics["deadline_expired"] = expired.is_set()
            diagnostic = {"schema": TRANSPORT_DIAGNOSIS_VERSION, "stage": stage, **error_summary(error),
                          **metrics, "cleanup_errors": cleanup_errors}
            if not isinstance(error, Exception):
                error.transport_diagnostic = diagnostic
                raise error
            failure = TransportValidationFailure if isinstance(error, ValueError) else TransportFailure
            raise failure(diagnostic) from None
        return raw
