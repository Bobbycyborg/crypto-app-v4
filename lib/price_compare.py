"""Multi-source price compare — consensus + spread for portfolio alts."""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from typing import Any

from lib.coingecko_api import auth_status
from lib.paths import CACHE, CONFIG
from lib.price_sources import (
    COINGECKO_IDS,
    fetch_binance,
    fetch_coingecko,
    fetch_coingecko_batch,
    fetch_coinbase,
    fetch_dexscreener_selection,
    fetch_geckoterminal,
    mint_for,
)
from lib.wallet import load_assets_config

SOURCE_NAMES = ("coingecko", "dexscreener", "binance", "geckoterminal", "coinbase")
DEFAULT_DIVERGE_PCT = 2.0
MAX_CACHE_AGE_SEC = 900


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _diverge_pct() -> float:
    try:
        thr = json.loads((CONFIG / "thresholds.json").read_text())
        return float(thr.get("prices", {}).get("diverge_alert_pct", DEFAULT_DIVERGE_PCT))
    except Exception:
        return DEFAULT_DIVERGE_PCT


def _threshold_status() -> str:
    try:
        thr = json.loads((CONFIG / "thresholds.json").read_text())
        return str(thr.get("prices", {}).get("diverge_threshold_status", "PROVISIONAL"))
    except Exception:
        return "PROVISIONAL"


def _price_check_status(meta: dict[str, Any]) -> str:
    summary = meta.get("compare_summary") or {}
    if summary.get("missing", 0) > 0:
        return "RED"
    if summary.get("diverge", 0) > 0:
        return "RED"
    if meta.get("prices_fallback_used"):
        return "AMBER"
    if summary.get("single_source", 0) > 0:
        return "AMBER"
    return "GREEN"


def _cache_age_sec(timestamp: str | None) -> float | None:
    if not timestamp:
        return None
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds()
    except Exception:
        return None


def _diff_pct(a: float, b: float) -> float:
    base = max(abs(a), abs(b), 1e-12)
    return abs(a - b) / base * 100.0


def _max_spread(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    return max(_diff_pct(values[i], values[j]) for i in range(len(values)) for j in range(i + 1, len(values)))


def compare_symbol(
    symbol: str,
    *,
    mint: str | None = None,
    chain: str = "solana",
    cg_batch: dict[str, Any] | None = None,
    alert_pct: float | None = None,
) -> dict[str, Any]:
    """Fetch all sources for one symbol and return compare report."""
    alert = alert_pct if alert_pct is not None else _diverge_pct()
    dex_sel = fetch_dexscreener_selection(mint, symbol=symbol, chain=chain)
    sources: dict[str, float | None] = {
        "coingecko": fetch_coingecko(symbol, cg_batch),
        "dexscreener": float(dex_sel["price_usd"]) if dex_sel else None,
        "binance": fetch_binance(symbol),
        "geckoterminal": fetch_geckoterminal(mint),
        "coinbase": fetch_coinbase(symbol),
    }
    available = {k: v for k, v in sources.items() if v is not None}
    values = list(available.values())
    spread = _max_spread(values)
    agreed = spread is not None and spread <= alert
    consensus = statistics.median(values) if values else None

    if len(values) >= 2 and agreed:
        status = "ok"
    elif len(values) >= 2:
        status = "diverge"
    elif len(values) == 1:
        status = "single_source"
    else:
        status = "missing"

    chosen_source = None
    is_fallback = False
    if sources.get("coingecko") is not None:
        chosen_source = "coingecko"
    elif sources.get("geckoterminal") is not None:
        chosen_source = "geckoterminal"
        is_fallback = True
    elif sources.get("dexscreener") is not None:
        chosen_source = "dexscreener"
        is_fallback = True
    elif sources.get("binance") is not None:
        chosen_source = "binance"
        is_fallback = True
    elif sources.get("coinbase") is not None:
        chosen_source = "coinbase"
        is_fallback = True

    usd = float(sources[chosen_source]) if chosen_source else None
    gbp = usd * 0.79 if usd is not None else None

    cg_id = COINGECKO_IDS.get(symbol)
    cg_row = (cg_batch or {}).get(cg_id, {}) if cg_id else {}

    return {
        "symbol": symbol,
        "usd": usd,
        "gbp": gbp,
        "consensus_usd": round(consensus, 8) if consensus is not None else None,
        "consensus_method": "median" if len(values) >= 2 else ("single" if len(values) == 1 else None),
        "source": chosen_source,
        "is_fallback": is_fallback,
        "sources_checked": list(available.keys()),
        "sources_available": len(available),
        "source_prices_usd": {k: (round(v, 8) if v is not None else None) for k, v in sources.items()},
        "dexscreener_selection": dex_sel,
        "max_spread_pct": round(spread, 4) if spread is not None else None,
        "sources_agree": agreed if spread is not None else None,
        "status": status,
        "change_24h_pct": cg_row.get("usd_24h_change"),
        "change_7d_pct": cg_row.get("usd_7d_change"),
        "change_30d_pct": cg_row.get("usd_30d_change"),
    }


def compare_portfolio(
    symbols: list[str] | None = None,
    *,
    force: bool = False,
    report_date: str | None = None,
) -> tuple[dict[str, dict], dict[str, Any]]:
    """Compare all portfolio symbols across every source."""
    cache_file = CACHE / f"prices-{report_date or _today()}.json"
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    alert_pct = _diverge_pct()

    if cache_file.exists() and not force:
        cached = json.loads(cache_file.read_text())
        sources = cached.get("sources") or {}
        age = _cache_age_sec((sources.get("fetched_at") or {}).get("compare"))
        if cached.get("prices") and sources.get("mode") == "multi_compare" and age is not None and age < MAX_CACHE_AGE_SEC:
            return cached["prices"], sources

    assets = load_assets_config()["assets"]
    symbol_to_mint = {a["symbol"]: a.get("mint") for a in assets if a.get("mint")}
    symbol_to_chain = {a["symbol"]: a.get("chain") or "solana" for a in assets}
    if symbols is None:
        symbols = [a["symbol"] for a in assets if a["symbol"] in COINGECKO_IDS]

    cg_batch = fetch_coingecko_batch(symbols)
    prices: dict[str, dict] = {}
    comparisons: list[dict[str, Any]] = []
    ok = diverge = single = missing = 0

    for symbol in symbols:
        chain = symbol_to_chain.get(symbol) or "solana"
        if chain == "multi":
            chain = "solana"
        row = compare_symbol(
            symbol,
            mint=mint_for(symbol, symbol_to_mint),
            chain=chain,
            cg_batch=cg_batch,
            alert_pct=alert_pct,
        )
        comparisons.append(
            {
                "symbol": symbol,
                "status": row["status"],
                "sources_available": row["sources_available"],
                "max_spread_pct": row["max_spread_pct"],
                "sources_agree": row["sources_agree"],
                "source_prices_usd": row["source_prices_usd"],
                "dexscreener_selection": row.get("dexscreener_selection"),
            }
        )
        if row["status"] == "ok":
            ok += 1
        elif row["status"] == "diverge":
            diverge += 1
        elif row["status"] == "single_source":
            single += 1
        else:
            missing += 1
        if row["status"] != "missing":
            prices[symbol] = row

    meta = {
        "mode": "multi_compare",
        "sources": list(SOURCE_NAMES),
        "prices_primary": "coingecko",
        "diverge_alert_pct": alert_pct,
        "diverge_threshold_status": _threshold_status(),
        "coingecko_auth": auth_status(),
        "prices_fallback_used": any(p.get("is_fallback") for p in prices.values()),
        "compare_summary": {
            "ok": ok,
            "diverge": diverge,
            "single_source": single,
            "missing": missing,
        },
        "comparisons": comparisons,
        "fetched_at": {name: fetched_at for name in SOURCE_NAMES},
        "freshness": {name: "FRESH" for name in SOURCE_NAMES},
    }
    meta["fetched_at"]["snapshot"] = fetched_at
    meta["fetched_at"]["compare"] = fetched_at
    meta["price_check_status"] = _price_check_status(meta)
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"prices": prices, "sources": meta}, indent=2))
    return prices, meta
