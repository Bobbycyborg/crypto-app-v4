"""Shared price and market-data fetches for asset weekly reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lib.fetchers.http import get_json

IO_MINT = "BZLbGTNCSFfoth2GYDtwr7e4imWzpR5jqcUuGEwr646K"
NOS_MINT = "nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7"


def fetch_price_coingecko(coin_id: str) -> dict[str, Any]:
    coin = get_json(
        f"https://api.coingecko.com/api/v3/coins/{coin_id}",
        params={
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false",
        },
    )
    md = coin["market_data"]
    return {
        "source": "coingecko",
        "url": f"https://www.coingecko.com/en/coins/{coin_id}",
        "price_usd": float(md["current_price"]["usd"]),
        "ath_usd": float(md["ath"]["usd"]),
        "ath_change_pct": float(md["ath_change_percentage"]["usd"]),
        "change_7d_pct": md.get("price_change_percentage_7d_in_currency", {}).get("usd"),
        "change_30d_pct": md.get("price_change_percentage_30d_in_currency", {}).get("usd"),
        "circulating_supply": md.get("circulating_supply"),
        "total_supply": md.get("total_supply"),
        "max_supply": md.get("max_supply"),
        "market_cap_usd": (md.get("market_cap") or {}).get("usd"),
        "fdv_usd": (md.get("fully_diluted_valuation") or {}).get("usd"),
        "total_volume_usd": (md.get("total_volume") or {}).get("usd"),
    }


def fetch_price_dexscreener(mint: str) -> dict[str, Any]:
    data = get_json(f"https://api.dexscreener.com/latest/dex/tokens/{mint}")
    pairs = data.get("pairs") or []
    if not pairs:
        raise RuntimeError(f"DexScreener: no pairs for mint {mint}")
    best = max(pairs, key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0))
    ch = best.get("priceChange") or {}
    return {
        "source": "dexscreener",
        "url": best.get("url", "https://api.dexscreener.com"),
        "price_usd": float(best["priceUsd"]),
        "ath_usd": None,
        "ath_change_pct": None,
        "change_7d_pct": float(ch["h24"]) if ch.get("h24") is not None else None,
        "change_30d_pct": None,
        "circulating_supply": None,
        "total_supply": None,
        "max_supply": None,
        "market_cap_usd": None,
        "fdv_usd": None,
        "total_volume_usd": None,
    }


def fetch_btc_7d_change() -> float | None:
    try:
        d = get_json(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd", "include_7d_change": "true"},
        )
        return d["bitcoin"].get("usd_7d_change")
    except Exception:
        return None


def fetch_daily_prices(coin_id: str, days: int = 30) -> dict[str, float]:
    chart = get_json(
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
        params={"vs_currency": "usd", "days": str(days)},
    )
    by_day: dict[str, float] = {}
    for ts, px in chart["prices"]:
        d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        by_day[d] = float(px)
    return by_day


def fetch_site_ok(url: str, min_length: int = 2000) -> bool:
    try:
        from lib.fetchers.http import get_text

        text = get_text(url)
        return len(text) >= min_length
    except Exception:
        return False
