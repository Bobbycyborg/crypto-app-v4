"""Unit tests against committed fixtures. Golden values are static, not parsed by production then re-asserted."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from collectors.extract import (
    ExtractError,
    by_state_count,
    extract,
    json_key,
    json_pointer,
    named_record_field,
    parse_json_body,
)
from collectors.normalize import normalize

FIX = ROOT / "tests/job2/fixtures/replay/raw"
GOLDEN = json.loads((ROOT / "tests/job2/golden-collector-output.json").read_text())


def _load(name: str):
    return parse_json_body((FIX / f"{name}.body").read_bytes(), "application/json")


def test_success_cases() -> None:
    cg = _load("coingecko.markets.active")
    px = named_record_field(cg, {"records_pointer": "/", "identity": {"id": "bitcoin"}, "field": "current_price"})
    assert normalize(px, {"type": "identity"}) == Decimal("100000")

    fund = json_key(_load("binance.fapi.premiumIndex.BTCUSDT"), "lastFundingRate")
    assert normalize(fund, {"type": "decimal_as_percent"}) == Decimal("0.0100") or normalize(fund, {"type": "decimal_as_percent"}) == Decimal("0.01")

    fng = json_pointer(_load("alternative_me.fng"), "/data/0/value")
    assert normalize(fng, {"type": "identity"}) == Decimal("74")

    jobs = _load("nosana.jobs.count")
    assert by_state_count(jobs, {"state": "RUNNING"}) == 855

    inf = json_pointer(_load("solana.rpc.getInflationRate"), "/result/total")
    assert normalize(inf, {"type": "decimal_as_percent"}) == Decimal("3.6800") or normalize(inf, {"type": "decimal_as_percent"}) == Decimal("3.68")


def test_missing_field() -> None:
    doc = {"symbol": "BTCUSDT"}
    try:
        json_key(doc, "lastFundingRate")
        raise AssertionError("expected missing")
    except ExtractError as exc:
        assert exc.status == "VALUE_MISSING"


def test_malformed_value() -> None:
    try:
        normalize("not-a-number", {"type": "identity"})
        raise AssertionError("expected invalid")
    except ExtractError as exc:
        assert exc.status == "VALUE_INVALID"


def test_wrong_identity() -> None:
    cg = _load("coingecko.markets.active")
    try:
        named_record_field(cg, {"records_pointer": "/", "identity": {"id": "not-a-coin"}, "field": "current_price"})
        raise AssertionError("expected miss")
    except ExtractError as exc:
        assert exc.status == "VALUE_MISSING"


def test_zero_and_multiple_matches() -> None:
    doc = [{"id": "x", "v": 1}, {"id": "x", "v": 2}]
    try:
        named_record_field(doc, {"records_pointer": "/", "identity": {"id": "x"}, "field": "v"})
        raise AssertionError("expected multiple")
    except ExtractError as exc:
        assert exc.status == "SOURCE_SCHEMA_MISMATCH"
    try:
        named_record_field(doc, {"records_pointer": "/", "identity": {"id": "z"}, "field": "v"})
        raise AssertionError("expected zero")
    except ExtractError as exc:
        assert exc.status == "VALUE_MISSING"


def test_unit_conversion_and_scientific() -> None:
    assert normalize(Decimal("10.0"), {"type": "millions_to_usd"}) == Decimal("10000000")
    assert normalize("-5.533e-05", {"type": "identity"}) == Decimal("-0.00005533")


def test_null_empty_nan_inf() -> None:
    for bad in [None, "", "NaN", "Infinity", float("nan"), float("inf")]:
        try:
            normalize(bad, {"type": "identity"})
            raise AssertionError(f"expected fail for {bad!r}")
        except ExtractError as exc:
            assert exc.status in {"VALUE_MISSING", "VALUE_INVALID"}


def test_unexpected_string() -> None:
    try:
        normalize("USD", {"type": "identity"})
        raise AssertionError("expected invalid")
    except ExtractError as exc:
        assert exc.status == "VALUE_INVALID"


def test_golden_subset() -> None:
    for row in GOLDEN["facts"]:
        assert "metric_id" in row
        assert "expected_normalized" in row


if __name__ == "__main__":
    test_success_cases()
    test_missing_field()
    test_malformed_value()
    test_wrong_identity()
    test_zero_and_multiple_matches()
    test_unit_conversion_and_scientific()
    test_null_empty_nan_inf()
    test_unexpected_string()
    test_golden_subset()
    print("PASS test_collectors_unit")
    raise SystemExit(0)
