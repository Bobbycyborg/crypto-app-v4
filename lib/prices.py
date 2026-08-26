"""Multi-source portfolio prices — delegates to price_compare."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lib.coingecko_api import global_stats
from lib.paths import CACHE
from lib.price_compare import compare_portfolio
from lib.price_sources import COINGECKO_IDS

__all__ = ["COINGECKO_IDS", "fetch_prices", "fetch_btc_dominance"]


def fetch_prices(report_date: str | None = None, force: bool = False) -> tuple[dict[str, dict], dict]:
    return compare_portfolio(force=force, report_date=report_date)


def fetch_btc_dominance() -> tuple[float | None, dict]:
    """Current BTC dominance % and cache for 7d trend."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE / "btc-dominance.json"
    prev = None
    if cache_path.exists():
        import json

        prev = json.loads(cache_path.read_text())

    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    current = None
    try:
        body = global_stats()
        if body:
            current = float(body["data"]["market_cap_percentage"]["btc"])
    except Exception:
        return None, {"fetched_at": fetched_at, "change_7d_pct": None}

    change_7d = None
    if prev and prev.get("dominance") is not None:
        change_7d = current - float(prev["dominance"])

    import json

    cache_path.write_text(
        json.dumps({"dominance": current, "fetched_at": fetched_at}, indent=2)
    )
    return current, {"dominance": current, "change_7d_pct": change_7d, "fetched_at": fetched_at}
