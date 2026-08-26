"""Shared HTTP helper for Job 2. No cache fallback. No provider substitution."""

from __future__ import annotations

import hashlib
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

CONNECT_TIMEOUT_S = 10
READ_TIMEOUT_S = 30
MAX_ATTEMPTS = 3
RETRY_DELAYS_S = (1.0, 2.0, 4.0)
MAX_BODY_BYTES = 8 * 1024 * 1024
USER_AGENT = "crypto-app-v4-job2-collectors/1.0"

_RETRY_STATUS = {429, 500, 501, 502, 503, 504, 507, 509, 529}
_NO_RETRY_STATUS = {400, 401, 403, 404}


class HttpError(Exception):
    def __init__(self, status: str, message: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.http_status = http_status
        self.message = message


@dataclass
class HttpResponse:
    url: str
    method: str
    status_code: int
    headers: dict[str, str]
    body: bytes
    fetched_at: str
    attempts: int


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def redact_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted = []
    for k, v in q:
        lk = k.lower()
        if any(s in lk for s in ("key", "token", "secret", "password", "auth")):
            redacted.append((k, "REDACTED"))
        else:
            redacted.append((k, v))
    query = urllib.parse.urlencode(redacted)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def body_sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _is_transient(exc: BaseException, status: int | None) -> bool:
    if status in _RETRY_STATUS:
        return True
    if status in _NO_RETRY_STATUS:
        return False
    if isinstance(exc, (TimeoutError, ConnectionError, urllib.error.URLError)):
        return True
    if isinstance(exc, urllib.error.HTTPError) and exc.code in _RETRY_STATUS:
        return True
    return False


def request(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> HttpResponse:
    if params:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{url}{'&' if '?' in url else '?'}{query}"
    hdrs = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    }
    if headers:
        hdrs.update(headers)
    if extra_headers:
        hdrs.update(extra_headers)
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")

    last_exc: BaseException | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs, method=method.upper())
            ctx = ssl.create_default_context()
            try:
                import certifi

                ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                pass
            # connect timeout via urlopen; read bounded by same timeout window + size check
            with urllib.request.urlopen(req, timeout=READ_TIMEOUT_S, context=ctx) as resp:
                status_code = int(resp.status)
                raw_headers = {k: v for k, v in resp.headers.items()}
                body = resp.read(MAX_BODY_BYTES + 1)
            fetched_at = utc_now()
            if len(body) > MAX_BODY_BYTES:
                raise HttpError("SOURCE_UNAVAILABLE", "response exceeded size sanity limit", status_code)
            if status_code >= 500 or status_code == 429:
                err = HttpError("SOURCE_UNAVAILABLE", f"HTTP {status_code}", status_code)
                if attempt < MAX_ATTEMPTS and status_code in _RETRY_STATUS:
                    time.sleep(RETRY_DELAYS_S[attempt - 1])
                    last_exc = err
                    continue
                raise err
            if status_code == 401:
                raise HttpError("AUTH_MISSING", "HTTP 401", 401)
            if status_code in (400, 403, 404):
                raise HttpError("SOURCE_UNAVAILABLE", f"HTTP {status_code}", status_code)
            if status_code < 200 or status_code >= 300:
                raise HttpError("SOURCE_UNAVAILABLE", f"HTTP {status_code}", status_code)
            return HttpResponse(
                url=url,
                method=method.upper(),
                status_code=status_code,
                headers=raw_headers,
                body=body,
                fetched_at=fetched_at,
                attempts=attempt,
            )
        except HttpError:
            raise
        except urllib.error.HTTPError as exc:
            last_exc = exc
            code = int(exc.code)
            if code == 401:
                raise HttpError("AUTH_MISSING", "HTTP 401", 401) from exc
            if code in _NO_RETRY_STATUS:
                raise HttpError("SOURCE_UNAVAILABLE", f"HTTP {code}", code) from exc
            if attempt < MAX_ATTEMPTS and _is_transient(exc, code):
                time.sleep(RETRY_DELAYS_S[attempt - 1])
                continue
            raise HttpError("SOURCE_UNAVAILABLE", f"HTTP {code}", code) from exc
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < MAX_ATTEMPTS and _is_transient(exc, None):
                time.sleep(RETRY_DELAYS_S[attempt - 1])
                continue
            raise HttpError("SOURCE_UNAVAILABLE", f"{type(exc).__name__}: {exc}") from exc
    raise HttpError("SOURCE_UNAVAILABLE", f"retries exhausted: {last_exc}")
