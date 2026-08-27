"""Mandatory golden regressions for CGPT Job 2B blocker decisions."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from collectors.extract import ExtractError, extract, parse_json_body
from collectors.normalize import normalize
from collectors.phase_b_selectors import open_interest_change_pct

FIX = ROOT / "tests/job2/fixtures/replay/raw"
PLAN = json.loads((ROOT / "collectors/collector-plan.json").read_text())


def _plan(mid: str) -> dict:
    return next(e for e in PLAN["entries"] if e["metric_id"] == mid)


def test_hype_af_buys_daily_holders_revenue_not_daily_fees() -> None:
    doc = {"name": "Hyperliquid", "total30d": 43900000, "total24h": 2304022}
    sel = _plan("hype.af.buys.usd.30d")["selector"]
    val = extract(doc, sel)
    assert normalize(val, {"type": "identity"}) == Decimal("43900000")

    try:
        extract({"name": "Hyperliquid"}, sel)
        raise AssertionError("expected missing total30d")
    except ExtractError:
        pass


def test_io_emissions_preserve_no_requests() -> None:
    row = _plan("io.emissions.tokens.remaining")
    assert row["disposition"] == "PRESERVE"
    assert row["required"] is False
    assert row["request_key"] is None


def test_render_leftover_emissions_supply_info() -> None:
    supply = {"leftoverEmissions": 2384638, "circulatingSupply": 555631962}
    sel = _plan("render.emissions.tokens.remaining")["selector"]
    val = extract(supply, sel)
    assert normalize(val, {"type": "identity"}) == Decimal("2384638")

    try:
        extract({}, sel)
        raise AssertionError("missing leftoverEmissions")
    except ExtractError:
        pass


def test_spx_oi_trailing_change_not_pct_of_max() -> None:
    latest_ts = 1_700_000_000_000
    day = 24 * 60 * 60 * 1000
    baseline_ts = latest_ts - 30 * day
    rows = []
    for i in range(31):
        ts = baseline_ts + i * day
        oi = Decimal("2000000") if i < 30 else Decimal("3000000")
        rows.append(
            {
                "symbol": "SPXUSDT",
                "sumOpenInterestValue": str(oi),
                "timestamp": ts,
            }
        )
    pct = open_interest_change_pct(rows, {"window": 30, "expected_symbol": "SPXUSDT"})
    assert pct == Decimal("50")

    # V3-style: current = 87% of 30d max => NOT +87% change
    max_oi = Decimal("10000000")
    current = max_oi * Decimal("0.87")
    oi_rows = [
        {"symbol": "SPXUSDT", "sumOpenInterestValue": str(max_oi), "timestamp": baseline_ts},
        {"symbol": "SPXUSDT", "sumOpenInterestValue": str(current), "timestamp": latest_ts},
    ]
    trailing = open_interest_change_pct(oi_rows, {"window": 30, "expected_symbol": "SPXUSDT"})
    assert trailing != Decimal("87")


if __name__ == "__main__":
    test_hype_af_buys_daily_holders_revenue_not_daily_fees()
    test_io_emissions_preserve_no_requests()
    test_render_leftover_emissions_supply_info()
    test_spx_oi_trailing_change_not_pct_of_max()
    print("ok")
