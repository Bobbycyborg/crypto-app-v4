#!/usr/bin/env python3
"""Gates for the report pipeline. No network. No live page."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from collectors.phase_b_selectors_extra import dex_chain_ratio, earnings_mean_last_n, sol_burn_tokens_per_year
from collectors.extract import ExtractError
from integrity.stale_gate import stale_problems
from lib.v3.siren_state import protect_row
from renderer.coin_span import coin_regions, hits_in_regions, number_bounded
from renderer.formatters import format_value
from renderer.manual_zones import wrap_manual_zones


def test_number_does_not_match_inside_a_longer_number() -> None:
    html = '<article data-asset="pump">$0.00215</article>'
    assert number_bounded(html, html.index("0.002"), "0.002") is False
    assert number_bounded(html, html.index("$0.00215") , "$0.00215") is True


def test_match_stays_inside_the_coin() -> None:
    html = (
        '<article data-asset="grass">$0.347713</article>'
        '<article data-asset="spx">$0.463713</article>'
    )
    regions = coin_regions(html, "GRASS")
    assert hits_in_regions(html, "$0.463713", regions) == []
    assert len(hits_in_regions(html, "$0.347713", regions)) == 1


def test_dex_ratio_is_not_a_percent() -> None:
    got = dex_chain_ratio({"total7d": 200}, {"total7d": 100}, {"numerator_field": "total7d", "den_field": "total7d"})
    assert got == 2


def test_earnings_use_daily_not_the_cumulative_total() -> None:
    rows = [{"daily_earnings": 10, "total_earnings": 27000000} for _ in range(3)]
    got = earnings_mean_last_n({"data": rows}, {"n": 3})
    assert got == 10


def test_burn_is_not_the_inflation_copy() -> None:
    try:
        sol_burn_tokens_per_year({"result": {"total": 0.04}}, {"n": 1})
    except ExtractError as exc:
        assert "inflation" in str(exc)
    else:
        raise AssertionError("burn accepted the inflation rate")
    got = sol_burn_tokens_per_year({"total24h": 100}, {"lastPrice": "10"}, {"price_request_key": "x"})
    assert got == 3650


def test_long_decimal_is_rounded() -> None:
    assert format_value(1.167965779, {"type": "string_exact"}) == "1.168"


def test_stale_date_fails_the_gate() -> None:
    problems = stale_problems("<p>As of 2026-08-25</p>")
    assert any("2026-08-25" in item for item in problems)
    allowed = stale_problems("<p>1 Aug start 2026-08-01</p>")
    assert not any("stale date" in item for item in allowed)


def test_proved_start_is_kept() -> None:
    fresh = protect_row(
        {"aug1": 500_000_000, "aug1_status": "proved", "aug1_as_of": "2026-08-01T00:00:00Z"},
        {"balance": 728_000_000, "sent": 0, "received": 0, "aug1": 728_000_000, "aug1_status": "proved"},
    )
    assert fresh["aug1"] == 500_000_000
    assert fresh["aug1_status"] == "inconsistent"


def test_unwalked_coins_survive_a_save() -> None:
    import tempfile
    from lib.v3.siren_state import load_state, save_state

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "siren-state.json"
        save_state(
            {"coins": {"IO": {"wallets": [{"wallet": "io1", "aug1": 1, "aug1_status": "proved"}]}, "PUMP": {"wallets": [{"wallet": "p1", "aug1": 2}]}}},
            path,
        )
        save_state({"coins": {"PUMP": {"wallets": [{"wallet": "p1", "aug1": 2, "balance": 9}]}}}, path)
        coins = load_state(path)["coins"]
        assert coins["IO"]["wallets"][0]["aug1"] == 1
        assert coins["PUMP"]["wallets"][0]["balance"] == 9


def test_manual_zone_uses_the_report_number() -> None:
    html = wrap_manual_zones('<p class="alt-stance-expl">Leave this.</p>', "06")
    assert "report=06" in html


def main() -> int:
    test_number_does_not_match_inside_a_longer_number()
    test_match_stays_inside_the_coin()
    test_dex_ratio_is_not_a_percent()
    test_earnings_use_daily_not_the_cumulative_total()
    test_burn_is_not_the_inflation_copy()
    test_long_decimal_is_rounded()
    test_stale_date_fails_the_gate()
    test_proved_start_is_kept()
    test_unwalked_coins_survive_a_save()
    test_manual_zone_uses_the_report_number()
    print("test_report_pipeline OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
