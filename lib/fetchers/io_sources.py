"""IO-specific source fetches — fresh each weekly run."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lib.fetchers.price_common import (
    IO_MINT,
    fetch_btc_7d_change,
    fetch_daily_prices,
    fetch_price_coingecko,
    fetch_price_dexscreener,
    fetch_site_ok,
)

COINGECKO_ID = "io"


def fetch_all_io_evidence() -> dict[str, Any]:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bundle: dict[str, Any] = {"fetched_at": fetched_at, "calls": []}

    price = None
    for fn in (lambda: fetch_price_coingecko(COINGECKO_ID), lambda: fetch_price_dexscreener(IO_MINT)):
        try:
            price = fn()
            bundle["calls"].append({"fn": fn.__name__ if hasattr(fn, "__name__") else "fetch", "ok": True})
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

    bundle["site_io_net"] = fetch_site_ok("https://io.net")
    bundle["calls"].append({"fn": "fetch_site_io_net", "ok": bundle["site_io_net"]})

    # IO Explorer requires auth for device metrics — no free public API in V2.
    bundle["network_metrics"] = None
    bundle["calls"].append(
        {
            "fn": "io_explorer_network",
            "ok": False,
            "error": "IO Explorer device metrics require authenticated API — not integrated in V2.",
        }
    )

    return bundle
