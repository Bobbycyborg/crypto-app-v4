"""BTC market fragility feeds — OI and volume only; funding lives in supporting_feeds.btc_funding."""

from __future__ import annotations

from typing import Any

import certifi
import requests

BINANCE_SPOT_24H = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_FUT_24H = "https://fapi.binance.com/fapi/v1/ticker/24hr"
BINANCE_OI = "https://fapi.binance.com/fapi/v1/openInterest"
BINANCE_SPOT_DOCS = "https://binance-docs.github.io/apidocs/spot/en/#24hr-ticker-price-change-statistics"
BINANCE_FUT_DOCS = "https://binance-docs.github.io/apidocs/futures/en/#24hr-ticker-price-change-statistics"
BINANCE_OI_DOCS = "https://binance-docs.github.io/apidocs/futures/en/#open-interest"

_SYMBOL = "BTCUSDT"


def _get_json(url: str, params: dict | None = None) -> Any:
    r = requests.get(url, params=params, timeout=30, verify=certifi.where())
    r.raise_for_status()
    return r.json()


def enrich_btc_fragility_with_mcap(frag: dict[str, Any], market_cap_usd: float | None) -> dict[str, Any]:
    """Attach CoinGecko BTC market cap to OI block — same batch as Cards 3–5."""
    if not frag.get("ok") or market_cap_usd is None:
        return frag
    oi = frag.get("oi") or {}
    notional = oi.get("oi_notional_usd")
    if notional is None:
        return frag
    mcap_b = round(market_cap_usd / 1e9, 2)
    ratio = round(notional / market_cap_usd, 4) if market_cap_usd > 0 else None
    frag["oi"] = {
        **oi,
        "btc_market_cap_usd": market_cap_usd,
        "btc_market_cap_usd_b": mcap_b,
        "oi_mcap_ratio": ratio,
        "oi_mcap_note": "Binance BTCUSDT OI notional / CoinGecko BTC market cap · descriptive only.",
        "mcap_source": "coingecko_markets",
    }
    return frag


def fetch_btc_fragility_feeds(
    fetched_at: str,
    btc_funding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Binance BTCUSDT OI + 24h volumes — mark price from btc_funding when available."""
    base = {
        "ok": False,
        "feed_id": "btc_fragility",
        "role": "fragility_context_only",
        "not_a_market_vote": True,
        "no_classifier_thresholds": True,
        "symbol": _SYMBOL,
        "fetched_at": fetched_at,
    }
    try:
        spot = _get_json(BINANCE_SPOT_24H, {"symbol": _SYMBOL})
        fut = _get_json(BINANCE_FUT_24H, {"symbol": _SYMBOL})
        oi_row = _get_json(BINANCE_OI, {"symbol": _SYMBOL})

        mark = float((btc_funding or {}).get("mark_price_usd") or 0)
        oi_btc = float(oi_row.get("openInterest") or 0)
        oi_notional = oi_btc * mark if mark and oi_btc else None

        spot_vol = float(spot.get("quoteVolume") or 0)
        fut_vol = float(fut.get("quoteVolume") or 0)
        perp_spot = round(fut_vol / spot_vol, 3) if spot_vol > 0 else None

        return {
            **base,
            "ok": True,
            "oi": {
                "open_interest_btc": oi_btc,
                "mark_price_usd": mark if mark else None,
                "oi_notional_usd": oi_notional,
                "oi_notional_usd_b": round(oi_notional / 1e9, 2) if oi_notional else None,
                "source": "binance_futures",
                "source_url": BINANCE_OI_DOCS,
                "mark_source": "btc_funding" if mark and btc_funding else None,
            },
            "volume": {
                "spot_quote_volume_24h_usd": spot_vol,
                "spot_quote_volume_24h_usd_b": round(spot_vol / 1e9, 2),
                "perp_quote_volume_24h_usd": fut_vol,
                "perp_quote_volume_24h_usd_b": round(fut_vol / 1e9, 2),
                "perp_spot_ratio": perp_spot,
                "spot_source_url": BINANCE_SPOT_DOCS,
                "perp_source_url": BINANCE_FUT_DOCS,
            },
            "still_missing": [
                "breadth_concentration_divergence",
                "cross_venue_oi_aggregation",
            ],
        }
    except Exception as exc:
        return {**base, "error": str(exc)}
