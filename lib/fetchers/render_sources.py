"""RENDER-specific source fetches — called fresh each weekly run."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from lib.fetchers.http import get_json, get_text, parse_int_from_html

RENDER_MINT = "rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof"
COINGECKO_ID = "render-token"


def fetch_price_coingecko() -> dict[str, Any]:
    coin = get_json(
        "https://api.coingecko.com/api/v3/coins/render-token",
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
        "url": "https://www.coingecko.com/en/coins/render-token",
        "price_usd": float(md["current_price"]["usd"]),
        "ath_usd": float(md["ath"]["usd"]),
        "ath_change_pct": float(md["ath_change_percentage"]["usd"]),
        "change_7d_pct": md.get("price_change_percentage_7d_in_currency", {}).get("usd"),
        "change_30d_pct": md.get("price_change_percentage_30d_in_currency", {}).get("usd"),
    }


def fetch_price_dexscreener() -> dict[str, Any]:
    data = get_json(f"https://api.dexscreener.com/latest/dex/tokens/{RENDER_MINT}")
    pairs = data.get("pairs") or []
    if not pairs:
        raise RuntimeError("DexScreener: no pairs for RENDER")
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


def fetch_daily_prices(days: int = 30) -> dict[str, float]:
    chart = get_json(
        f"https://api.coingecko.com/api/v3/coins/{COINGECKO_ID}/market_chart",
        params={"vs_currency": "usd", "days": str(days)},
    )
    by_day: dict[str, float] = {}
    for ts, px in chart["prices"]:
        d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        by_day[d] = float(px)
    return by_day


def fetch_foundation_stats() -> dict[str, Any]:
    url = "https://stats.renderfoundation.com/"
    text = get_text(url)

    def after_dt_label(label: str) -> int | None:
        m = re.search(
            rf">{re.escape(label)}</dt>[\s\S]{{0,300}}?>([\d,]+)</dd>",
            text,
            re.I,
        )
        return int(m.group(1).replace(",", "")) if m else None

    def after_card_title(label: str) -> int | None:
        m = re.search(
            rf">{re.escape(label)}</div></div><div[^>]*><dd[^>]*>([\d,]+)</dd>",
            text,
            re.I,
        )
        return int(m.group(1).replace(",", "")) if m else None

    frames = after_dt_label("total frames rendered")
    nodes = after_card_title("Total Nodes Since Inception")
    burned = after_dt_label("Cumulative Burned to Date") or after_card_title("Cumulative Burned to Date")
    ok = frames is not None and nodes is not None
    status = "OK" if ok else "FAILED"
    return {
        "source": "render_foundation_dashboard",
        "url": url,
        "frames_rendered": frames,
        "nodes_total": nodes,
        "cumulative_burned": burned,
        "raw_length": len(text),
        "parse_status": status,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def fetch_all_render_evidence() -> dict[str, Any]:
    """One weekly evidence bundle. Tries primary sources; records failures."""
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bundle: dict[str, Any] = {"fetched_at": fetched_at, "calls": []}

    price = None
    for fn in (fetch_price_coingecko, fetch_price_dexscreener):
        try:
            price = fn()
            bundle["calls"].append({"fn": fn.__name__, "ok": True})
            break
        except Exception as e:
            bundle["calls"].append({"fn": fn.__name__, "ok": False, "error": str(e)})
    bundle["price"] = price

    try:
        bundle["daily_prices"] = fetch_daily_prices()
        bundle["calls"].append({"fn": "fetch_daily_prices", "ok": True})
    except Exception as e:
        bundle["daily_prices"] = None
        bundle["calls"].append({"fn": "fetch_daily_prices", "ok": False, "error": str(e)})

    try:
        bundle["btc_7d_change_pct"] = fetch_btc_7d_change()
        bundle["calls"].append({"fn": "fetch_btc_7d_change", "ok": True})
    except Exception as e:
        bundle["btc_7d_change_pct"] = None
        bundle["calls"].append({"fn": "fetch_btc_7d_change", "ok": False, "error": str(e)})

    try:
        bundle["foundation"] = fetch_foundation_stats()
        bundle["calls"].append({"fn": "fetch_foundation_stats", "ok": True})
    except Exception as e:
        bundle["foundation"] = None
        bundle["calls"].append({"fn": "fetch_foundation_stats", "ok": False, "error": str(e)})

    return bundle
