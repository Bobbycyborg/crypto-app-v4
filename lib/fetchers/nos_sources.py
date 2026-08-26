"""NOS-specific source fetches — fresh each weekly run."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lib.fetchers.http import get_json
from lib.fetchers.price_common import (
    NOS_MINT,
    fetch_btc_7d_change,
    fetch_daily_prices,
    fetch_price_coingecko,
    fetch_price_dexscreener,
    fetch_site_ok,
)

COINGECKO_ID = "nosana"

# Public indexer endpoints (may be unavailable — failures recorded, never invented).
NOSANA_STATS_URLS = (
    "https://dashboard.nosana.com/stats",
    "https://indexer.nosana.com/stats",
    "https://api.nosana.com/stats",
)


def _try_nosana_stats() -> dict[str, Any] | None:
    for url in NOSANA_STATS_URLS:
        try:
            data = get_json(url)
            if isinstance(data, dict) and data:
                return {"source": "nosana_indexer", "url": url, **data}
        except Exception:
            continue
    return None


def fetch_all_nos_evidence() -> dict[str, Any]:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bundle: dict[str, Any] = {"fetched_at": fetched_at, "calls": []}

    price = None
    for fn in (lambda: fetch_price_coingecko(COINGECKO_ID), lambda: fetch_price_dexscreener(NOS_MINT)):
        try:
            price = fn()
            bundle["calls"].append({"fn": "price_fetch", "ok": True})
            break
        except Exception as e:
            bundle["calls"].append({"fn": "price_fetch", "ok": False, "error": str(e)})
    bundle["price"] = price

    try:
        bundle["daily_prices"] = fetch_daily_prices(COINGECKO_ID)
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

    bundle["site_nosana"] = fetch_site_ok("https://nosana.com")
    bundle["calls"].append({"fn": "fetch_site_nosana", "ok": bundle["site_nosana"]})

    stats = _try_nosana_stats()
    bundle["network_stats"] = stats
    bundle["calls"].append({"fn": "nosana_network_stats", "ok": stats is not None})

    return bundle
