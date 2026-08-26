"""Fail-closed behaviour. No HTML/cache/provider fallback."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from collectors.derive import derive
from collectors.extract import ExtractError
from collectors.http_client import HttpError, request
from collectors.normalize import normalize
from decimal import Decimal


class FakeHTTP:
    def __init__(self, code: int, body: bytes = b"{}", retries_then: int | None = None) -> None:
        self.code = code
        self.body = body
        self.calls = 0
        self.retries_then = retries_then

    def handler(self, req, timeout=None, context=None):
        self.calls += 1
        import urllib.error

        raise urllib.error.HTTPError(req.full_url, self.code, "x", hdrs=None, fp=None)


def test_404_not_value() -> None:
    import urllib.error
    from email.message import Message
    from io import BytesIO

    def boom(req, timeout=None, context=None):
        raise urllib.error.HTTPError(req.full_url, 404, "no", hdrs=Message(), fp=BytesIO())

    with patch("urllib.request.urlopen", boom):
        try:
            request("GET", "https://example.test/missing")
            raise AssertionError("expected error")
        except HttpError as exc:
            assert exc.status == "SOURCE_UNAVAILABLE"
            assert exc.http_status == 404


def test_401_no_provider_fallback() -> None:
    import urllib.error
    from email.message import Message
    from io import BytesIO

    def boom(req, timeout=None, context=None):
        raise urllib.error.HTTPError(req.full_url, 401, "auth", hdrs=Message(), fp=BytesIO())

    with patch("urllib.request.urlopen", boom):
        try:
            request("GET", "https://example.test/auth")
            raise AssertionError("expected auth")
        except HttpError as exc:
            assert exc.status == "AUTH_MISSING"


def test_429_retries_then_fails() -> None:
    import urllib.error
    from email.message import Message
    from io import BytesIO

    calls = {"n": 0}

    def boom(req, timeout=None, context=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(req.full_url, 429, "rate", hdrs=Message(), fp=BytesIO())

    with patch("urllib.request.urlopen", boom):
        with patch("collectors.http_client.time.sleep", lambda s: None):
            try:
                request("GET", "https://example.test/r")
                raise AssertionError("expected fail")
            except HttpError as exc:
                assert exc.status == "SOURCE_UNAVAILABLE"
    assert calls["n"] == 3


def test_500_retries_then_fails() -> None:
    import urllib.error
    from email.message import Message
    from io import BytesIO

    calls = {"n": 0}

    def boom(req, timeout=None, context=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(req.full_url, 500, "x", hdrs=Message(), fp=BytesIO())

    with patch("urllib.request.urlopen", boom):
        with patch("collectors.http_client.time.sleep", lambda s: None):
            try:
                request("GET", "https://example.test/s")
            except HttpError as exc:
                assert exc.http_status == 500
    assert calls["n"] == 3


def test_malformed_json_and_wrong_type() -> None:
    from collectors.extract import parse_json_body

    try:
        parse_json_body(b"not-json", "application/json")
        raise AssertionError("expected")
    except ExtractError as exc:
        assert exc.status == "SOURCE_SCHEMA_MISMATCH"


def test_nan_inf_empty() -> None:
    for v in ["NaN", "Inf", "", None]:
        try:
            normalize(v, {"type": "identity"})
            raise AssertionError(v)
        except ExtractError:
            pass


def test_derive_fails_if_input_missing() -> None:
    # orchestrator sets DERIVATION_BLOCKED; unit: derive itself needs numbers
    try:
        derive("DIVIDE", [Decimal("1"), Decimal("0")], "v1")
        raise AssertionError("zero")
    except ExtractError as exc:
        assert exc.status == "VALUE_INVALID"


def test_no_eval_in_derive() -> None:
    try:
        derive("eval", [Decimal("1")], "v1")
        raise AssertionError("eval")
    except ExtractError:
        pass


if __name__ == "__main__":
    test_404_not_value()
    test_401_no_provider_fallback()
    test_429_retries_then_fails()
    test_500_retries_then_fails()
    test_malformed_json_and_wrong_type()
    test_nan_inf_empty()
    test_derive_fails_if_input_missing()
    test_no_eval_in_derive()
    print("PASS test_collectors_fail_closed")
    raise SystemExit(0)
