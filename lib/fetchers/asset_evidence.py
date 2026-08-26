"""Generic evidence bundle for standard V4 asset reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lib.fetchers.price_common import (
    fetch_btc_7d_change,
    fetch_daily_prices,
    fetch_site_ok,
)


def fetch_dex_liquidity(mint: str) -> dict[str, Any] | None:
    try:
        from lib.fetchers.http import get_json

        data = get_json(f"https://api.dexscreener.com/latest/dex/tokens/{mint}")
        pairs = data.get("pairs") or []
        if not pairs:
            return None
        best = max(pairs, key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0))
        liq = float((best.get("liquidity") or {}).get("usd") or 0)
        vol = float((best.get("volume") or {}).get("h24") or 0)
        return {
            "source": "dexscreener",
            "url": best.get("url", "https://api.dexscreener.com"),
            "liquidity_usd": liq,
            "volume_24h_usd": vol,
            "dex_id": best.get("dexId"),
        }
    except Exception:
        return None


def fetch_all_standard_evidence(
    coin_id: str,
    *,
    mint: str | None = None,
    site_url: str | None = None,
    symbol: str | None = None,
    binance_pair: str | None = None,
) -> dict[str, Any]:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bundle: dict[str, Any] = {"fetched_at": fetched_at, "calls": []}

    from lib.fetchers.live_spot_price import fetch_current_spot, resolve_spot_spec, identity_contract

    spec = resolve_spot_spec(
        coin_id=coin_id,
        symbol=symbol,
        dex_mint=mint,
        binance_pair=binance_pair,
    )
    spot = fetch_current_spot(
        spec["symbol"],
        coin_id=spec.get("coin_id"),
        dex_mint=spec.get("dex_mint"),
        binance_pair=spec.get("binance_pair"),
    )
    bundle["spot_spec"] = identity_contract(spec)
    bundle["price"] = spot.get("price_block") if spot.get("ok") else None
    bundle["price_attempts"] = spot.get("attempts") or []
    bundle["calls"].append(
        {
            "fn": "fetch_current_spot",
            "ok": bool(spot.get("ok")),
            "source": spot.get("source"),
            "error": spot.get("error"),
        }
    )

    try:
        bundle["daily_prices"] = fetch_daily_prices(coin_id)
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

    if site_url:
        ok = fetch_site_ok(site_url)
        bundle["site_ok"] = ok
        bundle["site_url"] = site_url
        bundle["calls"].append({"fn": "fetch_site", "ok": ok, "url": site_url})
    else:
        bundle["site_ok"] = False

    if mint:
        dex = fetch_dex_liquidity(mint)
        bundle["dex_liquidity"] = dex
        bundle["calls"].append({"fn": "fetch_dex_liquidity", "ok": dex is not None})
    else:
        bundle["dex_liquidity"] = None

    return bundle
