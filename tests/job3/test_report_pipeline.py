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
    stamp = "As of · 2026-08-12T16:23:47Z"
    assert number_bounded(stamp, stamp.index("T") + 1, "16") is False


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
    try:
        sol_burn_tokens_per_year({"total24h": 100}, {"lastPrice": "10"}, {"price_request_key": "x"})
    except ExtractError as exc:
        assert "dailyRevenue" in str(exc)
    else:
        raise AssertionError("burn accepted total fees")
    got = sol_burn_tokens_per_year({"dailyRevenue": 50}, {"lastPrice": "10"}, {"field": "dailyRevenue"})
    assert got == 1825


def test_long_decimal_is_rounded() -> None:
    assert format_value(1.167965779, {"type": "string_exact"}) == "1.168"


def test_known_stale_strings_must_fail() -> None:
    earlier = (
        "<p>BEAR MARKET $79,374. bounce is gone. As of 2026-08-25. "
        "ETF was $1.84B/$3.28B.</p>"
    )
    problems = " ".join(stale_problems(earlier, previous_html=earlier))
    for sample in ("BEAR MARKET $79,374", "bounce is gone", "$1.84B/$3.28B", "2026-08-25"):
        assert sample in problems, sample


def test_stale_date_fails_the_gate() -> None:
    assert stale_problems("<p>As of 2026-08-25</p>")
    assert stale_problems("<p>Freshness 2026-08-25</p>")
    assert stale_problems("<p>vesting ongoing. Next unlock 2026-08-28</p>")
    assert stale_problems("<p>SOL is $120.45 this week.</p>") == []
    assert any("2026-08-20" in item for item in stale_problems("<p>2026-08-20</p>"))
    allowed = stale_problems("<p>1 Aug start 2026-08-01</p>")
    assert not any(item.startswith("stale") for item in allowed)
    hidden = stale_problems('<p>2026-08-20</p><svg><path d="M ath z"/></svg>')
    assert any("2026-08-20" in item for item in hidden)
    ath = stale_problems("<p>ATH on 2025-10-06</p>")
    assert not any(item.startswith("stale date") for item in ath)
    assert not any("more than 4" in item for item in stale_problems("<p>$0.00215321</p>"))
    assert any("more than 4" in item for item in stale_problems("<p>$1.167965779</p>"))
    previous = '<button data-asset-slug="sol"><span class="desk-px">$104.45</span></button>'
    still = stale_problems(
        previous,
        previous_html=previous,
        snapshot={"metrics": {"sol.price.usd.live": {"status": "OK", "normalized_value": 120.45}}},
    )
    assert any("$104.45" in item for item in still)
    crossed = stale_problems(
        '<article data-asset="pump"><span class="alt-price">$0.463713</span></article>'
        '<article data-asset="sol"><span class="alt-price">$0.463713</span></article>',
        bindings=[
            {"asset": "pump", "source_literal": "$0.463713"},
            {"asset": "sol", "source_literal": "$0.463713"},
        ],
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
    planted = stale_problems(
        '<button data-asset-slug="btc"><span class="hold-px">$79,374</span></button>',
        previous_html='<button data-asset-slug="btc"><span class="hold-px">$79,374</span></button>',
        snapshot={"metrics": {"btc.price.usd.live": {"status": "OK", "normalized_value": 84128}}},
    )
    assert any("$79,374" in item for item in planted)


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


def test_price_slots_use_the_snapshot_not_a_nearby_low() -> None:
    from renderer.surface_slots import apply_known_slots

    html = (
        '<article data-asset="btc"><span class="alt-price">$83,934</span>'
        'Price $83,934 (Binance spot). Binance daily low ~$57.8k</article>'
        '<button data-asset-slug="btc"><span class="desk-px">$83,934</span></button>'
        '<button data-asset-slug="btc"><span class="hold-px" data-live-px>$83,934</span></button>'
    )
    # The trend helper looks for BTC TREND. This snippet only checks price nodes.
    out = apply_known_slots(
        html,
        {"metrics": {"btc.price.usd.live": {"status": "OK", "normalized_value": 84128}}},
    )
    assert out.count("$84,128") == 3
    assert "~$57.8k" in out


def test_roster_hides_config_coins() -> None:
    import re
    from renderer.roster import apply_roster

    html = '<button class="hold" data-asset-slug="fart">FART</button><button class="hold" data-asset-slug="sol">SOL</button>'
    out = apply_roster(html)
    tags = re.findall(r'<button class="([^"]*)"[^>]*data-asset-slug="([^"]+)"', out)
    by = {slug: cls for cls, slug in tags}
    assert "is-hidden" in by["fart"]
    assert "is-hidden" not in by["sol"]


def test_manual_zone_is_not_stamped_as_this_week() -> None:
    from renderer.manual_zones import manual_zone_notes

    html = wrap_manual_zones('<p class="alt-stance-expl">Leave this.</p>', "06")
    assert "report=06" not in html
    assert "needs-human-edit" in html
    assert manual_zone_notes(html) == ["Leave this."]


def test_funding_mean_is_the_raw_rate() -> None:
    from decimal import Decimal
    from collectors.phase_b_selectors_extra import funding_rate_mean_last_n

    rows = [{"fundingRate": "0.00003045"}] * 7
    assert funding_rate_mean_last_n(rows, {"n": 7}) == Decimal("0.00003045")


def test_fart_leverage_uses_24h_dollars() -> None:
    from collectors.phase_b_selectors_extra import perp_vs_coinbase_spot_ratio

    ratio = perp_vs_coinbase_spot_ratio(
        {"quoteVolume": "43896117.97"},
        {"volume": "16703146.91", "volume_30day": "572832360.76", "last": "0.19403"},
        {"perp_pointer": "/quoteVolume", "spot_pointer": "/volume_30day"},
    )
    assert ratio > 10


def test_approved_btc_stance_replaces_the_number_dump() -> None:
    from renderer.stance_copy import apply_approved_stances

    html = (
        '<article data-asset="btc"><div class="alt-stance">'
        '<div class="alt-stance-headline">7D UP</div>'
        '<p class="alt-stance-expl">BTC $1 (+1% / 7d, +1% / 30d). '
        '<button type="button" class="stance-see-more">(see more)</button></p>'
        '<div class="stance-modal-src" hidden>'
        "<p class='stance-conf'>Evidence confidence · MEDIUM</p>"
        "<p class='stance-p'>old</p>"
        "<ul class='stance-list'><li>ETF flows were not re-fetched this pass</li>"
        "<li>30d is +4.6% and 7d is +3.3%</li></ul>"
        '</div></div><div class="econ-dash"></div></article>'
    )
    out = apply_approved_stances(html)
    assert "BACK ABOVE THE 200D" in out
    assert "not re-fetched" not in out
    assert "+4.6%" not in out
    assert "ETF buyers are back in size" in out


def test_sol_chart_supplies_30d_without_stopping() -> None:
    from datetime import date
    from decimal import Decimal

    from collectors.etf_backups import farside_windows, fill_missing_etf, flows_from_inflow_html

    series = ",".join(str(i) for i in range(100, 140))
    html = f"<td>25 Sep 2026</td><script>const totalData = [{series}];</script>"
    got = farside_windows(html, date(2026, 9, 26))
    assert got["30d"] == Decimal("30")
    assert got["all_time"] == Decimal("139")
    fill_missing_etf([], {})
    funds = ",".join("1" for _ in range(31))
    summed = farside_windows(
        f'<td>25 Sep 2026</td><script>const seriesData = {{"A":[{funds}],"B":[{funds}]}};</script>',
        date(2026, 9, 26),
    )
    assert summed["30d"] == Decimal("0")
    assert summed["all_time"] == Decimal("2")
    flows = flows_from_inflow_html(
        "<td>Sep 25, 2026</td><td class=\"num flow pos\">+$10.0M</td>"
        "<td>Sep 24, 2026</td><td class=\"num flow neg\">-$2.0M</td>"
    )
    assert flows == [(date(2026, 9, 24), Decimal("-2000000")), (date(2026, 9, 25), Decimal("10000000"))]


def test_wallet_walk_refuses_the_live_page() -> None:
    from lib.v3.siren_watch import apply_index

    try:
        apply_index({"coins": {"PUMP": {"wallets": []}}}, target=ROOT / "index-v4.html")
    except RuntimeError as exc:
        assert "index-v4.html" in str(exc)
    else:
        raise AssertionError("walk accepted the live page")


def main() -> int:
    test_number_does_not_match_inside_a_longer_number()
    test_match_stays_inside_the_coin()
    test_dex_ratio_is_not_a_percent()
    test_earnings_use_daily_not_the_cumulative_total()
    test_burn_is_not_the_inflation_copy()
    test_long_decimal_is_rounded()
    test_known_stale_strings_must_fail()
    test_stale_date_fails_the_gate()
    test_proved_start_is_kept()
    test_rebuilt_contract_uses_this_weeks_bindings()
    test_unwalked_coins_survive_a_save()
    test_price_slots_use_the_snapshot_not_a_nearby_low()
    test_roster_hides_config_coins()
    test_manual_zone_is_not_stamped_as_this_week()
    test_funding_mean_is_the_raw_rate()
    test_fart_leverage_uses_24h_dollars()
    test_approved_btc_stance_replaces_the_number_dump()
    test_sol_chart_supplies_30d_without_stopping()
    test_wallet_walk_refuses_the_live_page()
    print("test_report_pipeline OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
