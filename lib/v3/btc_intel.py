"""BTC Current Stance + intel builder — approved research pack → V3 asset JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.v3.asset_top import (
    LIGHT_GREEN,
    LIGHT_ORANGE,
    LIGHT_RED,
    LIGHT_UNKNOWN,
    empty_asset_top,
    signal,
)
from lib.v3.current_stance import btc_current_stance

ROOT = Path(__file__).resolve().parents[2]


def build_btc_asset_top() -> dict[str, Any]:
    top = empty_asset_top("BTC", "~$63.6k")
    top["price_as_of"] = "2026-08-12"
    stance = btc_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "explanation": stance["summary"],
        "directional_state": "WEAK",
        "confidence": stance["confidence"],
        "evidence_refs": [],
    }

    top["groups"] = {
        "market_structure": {
            "group_id": "market_structure",
            "title": "Price / Trend",
            "group_state": "WEAK · RANGE HOLDING",
            "group_light": LIGHT_ORANGE,
            "signals": [
                signal(
                    signal_id="price_trend",
                    label="Price Trend",
                    state="WEAK",
                    display="~50% retraced from ATH",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "Price ~$63.6k at research snapshot. ATH ~$126.1k (2025-10-06). "
                        "~−49.6% from ATH. 7d ~−1.1% · 30d ~+1.3% · 90d ~−21.5%."
                    ),
                    unknown="",
                    meaning="Own-price direction and retracement from cycle high — not a verdict by itself.",
                    source="CoinGecko + Binance daily",
                    source_url="https://www.coingecko.com/en/coins/bitcoin",
                    as_of="2026-08-12",
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="trend_structure",
                    label="Trend Structure",
                    state="RANGE HOLDING",
                    display="Below 200d · HL since July",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "Below 20d · above 50d · below 200d. Lower highs since ATH. "
                        "July low ~$57.8k. Current structure = range / higher-low since July. "
                        "MA crosses are descriptive only — not trading rules."
                    ),
                    unknown="",
                    meaning="Whether the post-ATH down-leg is still extending or consolidating. Retracement is not bad on its own — watch the turn.",
                    source="Binance BTCUSDT daily klines",
                    source_url="https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=1000",
                    as_of="2026-08-12",
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="cycle_context",
                    label="Cycle Context",
                    state="POST-ATH DOWN LEG",
                    display="POST-ATH DOWN LEG",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "Retracement from the Oct 2025 ATH has already happened. "
                        "Current question is how far it goes, and when it turns."
                    ),
                    unknown="",
                    meaning="Where BTC sits in the post-ATH cycle phase.",
                    source="Binance swing highs/lows",
                    source_url="https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=1000",
                    as_of="2026-08-12",
                    freshness="research_snapshot",
                    confidence="MEDIUM",
                    epistemic_status="KNOWN",
                ),
            ],
        },
        "capital_flow": {
            "group_id": "capital_flow",
            "title": "Capital Flow",
            "group_state": "MIXED",
            "group_light": LIGHT_ORANGE,
            "signals": [
                signal(
                    signal_id="etf_institutional_spot",
                    label="ETF / Institutional Spot",
                    state="RECENT SUPPORT",
                    display="RECENT SUPPORT",
                    light=LIGHT_GREEN,
                    evidence=(
                        "Aug 3–7 roughly +$853M to +$865M net. Aug 10 −$144.6M. "
                        "Aug 11 +$7.8M. Cumulative since launch ~$52.1B. "
                        "ETF flow = best available institutional spot proxy here — not complete BTC spot demand. "
                        "One outflow day ≠ bearish."
                    ),
                    unknown="Full machine 10d/20d series not fetched this pass.",
                    meaning="Whether US spot ETFs are absorbing or releasing BTC.",
                    source="Farside Investors",
                    source_url="https://farside.co.uk/btc/",
                    as_of="2026-08-11",
                    freshness="research_snapshot",
                    confidence="MEDIUM",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="who_buying",
                    label="Who Is Buying?",
                    state="PARTIAL",
                    display="PARTIAL · ETF DEMAND VISIBLE",
                    light=LIGHT_ORANGE,
                    evidence="ETF creations recently supportive.",
                    unknown="CEX buyer identity · LTH/STH buyer attribution · whale identity.",
                    meaning="Visible demand sources behind price.",
                    source="Farside Investors (ETF proxy)",
                    source_url="https://farside.co.uk/btc/",
                    as_of="2026-08-11",
                    freshness="research_snapshot",
                    confidence="MEDIUM",
                    epistemic_status="PARTIAL",
                ),
                signal(
                    signal_id="who_selling",
                    label="Who Is Selling?",
                    state="UNKNOWN",
                    display="UNKNOWN / PARTIAL",
                    light=LIGHT_UNKNOWN,
                    evidence=(
                        "No verified major miner dump, government dump, estate dump, "
                        "or corporate distribution in this pass. "
                        "TRANSFER ≠ SALE · CEX FLOW ≠ SALE."
                    ),
                    unknown="Exchange netflow · LTH/STH distribution · large-holder identity.",
                    meaning="Proven sell-side supply entering the market.",
                    source="BTC V3 research pass",
                    source_url="https://farside.co.uk/btc/",
                    as_of="2026-08-12",
                    freshness="research_snapshot",
                    confidence="LOW",
                    epistemic_status="UNKNOWN",
                ),
            ],
        },
        "project_supply": {
            "group_id": "project_supply",
            "title": "Spot vs Leverage",
            "group_state": "LEVERAGE HEAVY",
            "group_light": LIGHT_ORANGE,
            "signals": [
                signal(
                    signal_id="fut_spot_ratio",
                    label="Futures vs Spot",
                    state="LEVERAGE HEAVY",
                    display="~8.0× fut/spot",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "Binance spot 24h quote volume ~$0.86B. Binance perp 24h ~$6.9B. "
                        "Fut/spot ~8.0× (venue-local proxy)."
                    ),
                    unknown="Global multi-venue spot/perp split.",
                    meaning="How much of observed activity is leveraged vs spot.",
                    source="Binance spot + USDT-M futures 24hr",
                    source_url="https://www.binance.com/en/trade/BTC_USDT",
                    as_of="2026-08-12",
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="open_interest",
                    label="Open Interest",
                    state="STABLE-UP",
                    display="~109k BTC · +1.8% 30d",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "Binance OI ~109k BTC. OI +2.8% 1d / +1.0% 7d / +1.8% 30d. "
                        "OI rising ≠ bearish by itself."
                    ),
                    unknown="Cross-exchange OI aggregate.",
                    meaning="Leverage inventory on Binance perps.",
                    source="Binance openInterest / openInterestHist",
                    source_url="https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT",
                    as_of="2026-08-12",
                    freshness="research_snapshot",
                    confidence="MEDIUM",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="funding",
                    label="Funding",
                    state="MILD POSITIVE",
                    display="~+0.0078% / 8h",
                    light=LIGHT_GREEN,
                    evidence=(
                        "Funding ~+0.0078% / 8h. 7d mean ~+0.0052% / 8h. "
                        "Positive funding ≠ top. Not a blow-off extreme from this evidence."
                    ),
                    unknown="Basis · liquidations (unavailable this pass).",
                    meaning="Perp positioning cost / crowding proxy.",
                    source="Binance premiumIndex / fundingRate",
                    source_url="https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT",
                    as_of="2026-08-12",
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
            ],
        },
    }
    return top


def build_btc_v3() -> dict[str, Any]:
    stance = btc_current_stance()
    asset_top = build_btc_asset_top()
    from lib.v3.btc_product import (
        build_btc_change_mind,
        build_btc_reality_check,
        build_btc_warning_stack,
    )

    doc: dict[str, Any] = {
        "meta": {
            "schema": "btc-v3",
            "report_date": "2026-08-12",
            "gathered_at_utc": "2026-08-12T06:51:23Z",
            "research_pack": "reports/btc-forensics/v3-evidence/BTC-V3-FINDINGS.md",
            "overall_read": "PARTIAL — WEAKENING BUT NOT CONFIRMED",
            "trend": "WEAK",
            "capital_flow": "MIXED",
            "market_structure": "LEVERAGE-HEAVY · RANGE HOLDING",
        },
        "hero": {
            "asset": "BTC",
            "price_display": "~$63.6k",
            "ath_display": "~$126.1k",
            "drawdown_pct": 49.6,
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
        },
        "asset_top": asset_top,
        "warning_stack": build_btc_warning_stack(),
        "what_would_change_mind": build_btc_change_mind(),
        "reality_check": build_btc_reality_check(),
        "context": {
            "btc_dominance_pct": 56.3,
            "breadth_pct_beat_btc_30d": 33.3,
            "breadth_median_alt_btc_pp": -5.1,
            "breadth_state": "NARROW",
            "liquidity_pulse_yoy_pct": -5.92,
            "nfci": -0.529,
            "stablecoin_supply_usd_b": 306.0,
            "stablecoin_30d_pct": -1.0,
        },
        # Raw evidence table stays in reports/btc-forensics/v3-evidence/ — not production JSON
        "research_evidence_table_path": "reports/btc-forensics/v3-evidence/btc-evidence-table.json",
    }
    return doc


def write_btc_v3(out_dir: Path | None = None) -> dict[str, Any]:
    doc = build_btc_v3()
    out_dir = out_dir or (ROOT / "reports" / "2026-08-12")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "btc-v3.json"
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "btc-v3.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return doc
