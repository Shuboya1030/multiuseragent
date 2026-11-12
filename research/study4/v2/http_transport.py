"""One-shot HTTP adapter: no implicit credentials, proxy, redirects or retries."""
import http.client
import errno
from email.utils import parsedate_to_datetime
import json
import re
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


TRANSPORT_DIAGNOSIS_VERSION = "study4-http-stages-2-safe-error-fields"
HTTP_ERROR_BYTES = 16384
ERROR_FIELD_VALUES = frozenset({
    "insufficient_quota", "rate_limit_exceeded", "tokens", "requests",
    "invalid_request_error", "server_error", "authentication_error", "permission_error",
    "billing_hard_limit_reached", "billing_not_active", "model_not_found",
})
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


def collect_http_error(response, diagnostic, byte_limit):
    """Keep only enumerated provider fields and validated operational metadata."""
    for suffix in ("requests", "tokens"):
        for field in ("limit", "remaining"):
            value = response.getheader("x-ratelimit-" + field + "-" + suffix)
            if isinstance(value, str) and re.fullmatch(r"[0-9]{1,12}", value):
                diagnostic[field + "_" + suffix] = int(value)
        value = response.getheader("x-ratelimit-reset-" + suffix)
        if isinstance(value, str) and len(value) <= 32:
            parts = re.fullmatch(r"(?:(\d{1,3})h)?(?:(\d{1,4})m)?(?:(\d{1,6}(?:\.\d{1,3})?)s)?"
                                 r"(?:(\d{1,8})ms)?", value)
            if parts and any(p is not None for p in parts.groups()):
                hours, minutes, seconds, millis = (float(p or 0) for p in parts.groups())
                total = round(hours * 3600000 + minutes * 60000 + seconds * 1000 + millis)
                if 0 <= total <= 86400000:
                    diagnostic["reset_" + suffix + "_milliseconds"] = total
    value = response.getheader("x-request-id")
    if isinstance(value, str) and re.fullmatch(r"req_[a-fA-F0-9]{16,64}", value):
        diagnostic["request_id"] = value
    value = response.getheader("Retry-After")
    if isinstance(value, str) and len(value) <= 80:
        if re.fullmatch(r"\d{1,6}(?:\.\d{1,3})?", value) and float(value) <= 604800:
            diagnostic["retry_after_seconds"] = float(value)
        else:
            try:
                date = parsedate_to_datetime(value)
            except (ValueError, TypeError, IndexError, OverflowError):
                diagnostic["retry_after_invalid"] = True
            else:
                if date.tzinfo is not None and 2000 <= date.year <= 2100:
                    diagnostic["retry_after_utc_unix_seconds"] = int(date.timestamp())
                else:
                    diagnostic["retry_after_invalid"] = True
    elif value is not None:
        diagnostic["retry_after_invalid"] = True
    diagnostic["body_byte_limit"] = byte_limit
    raw = response.read(byte_limit + 1)
    diagnostic["body_bytes_observed"] = len(raw)
    if len(raw) > byte_limit:
        diagnostic["body_status"] = "over_limit"
        return
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeError):
        diagnostic["body_status"] = "not_json"
        return
    diagnostic["body_status"] = "json"
    error = payload.get("error") if isinstance(payload, dict) else None
    diagnostic["error_object"] = isinstance(error, dict)
    if isinstance(error, dict):
        for key in ("type", "code"):
            value = error.get(key)
            diagnostic["error_" + key] = (
                value if isinstance(value, str) and value in ERROR_FIELD_VALUES else
                "absent" if value is None else "unrecognized")


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
            if type(status) is int and status != 200:
                primary = ("status", ValueError("Non-success/redirect HTTP response"))
                metrics["http_error"] = {}
                collect_http_error(response, metrics["http_error"], min(HTTP_ERROR_BYTES, self.max_response_bytes))
                raise primary[1]
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
            if primary is None:
                primary = (stage, error)
            elif error is not primary[1]:
                metrics["http_error"]["collection_error"] = error_summary(error)
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
