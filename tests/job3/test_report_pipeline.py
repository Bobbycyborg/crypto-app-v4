#!/usr/bin/env python3
"""Gates for the report pipeline. No network. No live page."""

from __future__ import annotations

import json
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
    price = "$79,374"
    assert number_bounded(price, 0, "$79") is False
    assert number_bounded(price, 0, "$79,374") is True


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
    assert not any(item.startswith("stale") for item in allowed)
    hidden = stale_problems('<p>As of 2026-08-20</p><svg><path d="M ath z"/></svg>')
    assert any("2026-08-20" in item for item in hidden)
    ath = stale_problems("<p>ATH on 2025-10-06</p>")
    assert not any(item.startswith("stale date") for item in ath)
    assert not any("more than 4" in item for item in stale_problems("<p>$0.00215321</p>"))
    assert any("more than 4" in item for item in stale_problems("<p>$1.167965779</p>"))
    for phrase in ("$79,374", "$79,073", "bounce is gone", "$104.45", "$1.43", "$1.84B", "$3.28B"):
        assert any(phrase in item for item in stale_problems(f"<p>{phrase}</p>")), phrase
    crossed = stale_problems(
        '<article data-asset="pump">$0.463713</article><article data-asset="sol">$0.463713</article>'
    )
    assert any("both" in item for item in crossed)


def test_proved_start_is_kept() -> None:
    fresh = protect_row(
        {"aug1": 500_000_000, "aug1_status": "proved", "aug1_as_of": "2026-08-01T00:00:00Z", "balance": 500_000_000},
        {"balance": 728_000_000, "sent": 0, "received": 0, "aug1": 728_000_000, "aug1_status": "proved"},
    )
    assert fresh["aug1"] == 500_000_000
    assert fresh["aug1_status"] == "proved"
    assert fresh["balance_mismatch"] is True
    quiet = protect_row(
        {"aug1": 500_000_000, "aug1_status": "proved", "balance": 500_000_000},
        {"balance": 500_000_000, "sent": 0, "received": 0, "aug1_status": "unmoved_equals_now"},
    )
    assert quiet["aug1"] == 500_000_000
    assert quiet["aug1_status"] == "proved"
    assert quiet["balance_mismatch"] is False


def test_rebuilt_contract_uses_this_weeks_bindings() -> None:
    import tempfile
    from integrity.build_report_contract import build_contract
    from integrity.rules import check_binding_consistency

    page = Path(tempfile.mkdtemp()) / "page.html"
    page.write_text("<p>SOL is $120.45 this week.</p>", encoding="utf-8")
    contract = build_contract(
        registry_path=ROOT / "metrics/metric-registry.json",
        plan_path=ROOT / "collectors/collector-plan.json",
        bindings_path=ROOT / "renderer/binding-manifest.json",
        source_html_path=page,
    )
    manifest_ids = {b["binding_id"] for b in json.loads((ROOT / "renderer/binding-manifest.json").read_text())["bindings"]}
    assert set(contract["surface_by_binding"]) <= manifest_ids
    checks = check_binding_consistency(
        rendered_html=page.read_text(encoding="utf-8"),
        source_html=page.read_text(encoding="utf-8"),
        snapshot={"metrics": {}},
        bindings=[],
        reg={},
        contract={"surface_by_binding": {"not-this-week::1": ["hero"]}},
    )
    assert any(c.status == "COVERAGE_GAP" for c in checks)
    assert stale_problems(page.read_text(encoding="utf-8")) == []
    planted = stale_problems("<p>BEAR MARKET $79,374. The bounce is gone.</p>")
    assert any("$79,374" in item for item in planted)
    assert any("bounce is gone" in item for item in planted)


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
    test_rebuilt_contract_uses_this_weeks_bindings()
    test_unwalked_coins_survive_a_save()
    test_manual_zone_uses_the_report_number()
    print("test_report_pipeline OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
