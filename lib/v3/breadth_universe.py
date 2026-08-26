"""Market breadth — fixed universe vs portfolio holdings."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from statistics import median
from typing import Any

from lib.fetchers.price_common import fetch_daily_prices
from lib.paths import CONFIG, DATA
from lib.v3.rs import pct_change

_CACHE_PATH = DATA / "breadth-universe-daily.json"
_SMA_WINDOW = 50
_MIN_DAYS_SMA = 55


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_universe_config() -> dict[str, Any]:
    return json.loads((CONFIG / "v3-breadth-universe.json").read_text())


def btc_30d_pct_coingecko(ev: dict[str, Any]) -> float | None:
    """BTC 30d return from CoinGecko markets batch — aligned with alt RS cards 3–5."""
    mp = ev.get("market_prices") or {}
    v = mp.get("bitcoin", {}).get("usd_30d_change")
    return float(v) if v is not None else None


def cg_market_as_of(ev: dict[str, Any]) -> str | None:
    mp = ev.get("market_prices") or {}
    ts = mp.get("bitcoin", {}).get("last_updated")
    if not ts:
        return None
    return ts[:10] if "T" in str(ts) else str(ts)


def _pct_above_sma(daily: dict[str, float], window: int = _SMA_WINDOW) -> bool | None:
    if len(daily) < window:
        return None
    dates = sorted(daily)
    closes = [daily[d] for d in dates[-window:]]
    sma = sum(closes) / window
    return daily[dates[-1]] > sma


def _migrate_cache(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("coins"):
        return raw
    series = raw.get("series") or {}
    coins: dict[str, Any] = {}
    legacy_fetched = raw.get("fetched_at")
    for cid, daily in series.items():
        if not daily:
            continue
        last_date = max(daily)
        coins[cid] = {
            "daily": daily,
            "last_date": last_date,
            "fetched_at": legacy_fetched,
            "status": "stale",
        }
    return {"cache_written_at": raw.get("fetched_at"), "coins": coins}


def _load_cache() -> dict[str, Any]:
    if not _CACHE_PATH.exists():
        return {"coins": {}, "cache_written_at": None}
    return _migrate_cache(json.loads(_CACHE_PATH.read_text()))


def _write_cache(coins: dict[str, Any]) -> dict[str, Any]:
    meta = {
        "cache_written_at": _now_iso(),
        "coins": coins,
    }
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(meta, separators=(",", ":")))
    return meta


def load_universe_daily(coin_ids: list[str], refresh_stale: bool = True) -> dict[str, dict[str, float]]:
    """Daily USD closes for 50DMA — per-coin cache with freshness metadata."""
    cache = _load_cache()
    coins: dict[str, Any] = dict(cache.get("coins") or {})

    for coin_id in coin_ids:
        entry = coins.get(coin_id) or {}
        daily = entry.get("daily") or {}
        fetched_at = entry.get("fetched_at")
        stale = True
        if fetched_at:
            try:
                dt = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
                stale = (datetime.now(timezone.utc) - dt).total_seconds() > 86400
            except ValueError:
                stale = True

        need = (
            refresh_stale
            or stale
            or not daily
            or len(daily) < _MIN_DAYS_SMA
        )
        if not need:
            continue

        try:
            time.sleep(1.0)
            new_daily = fetch_daily_prices(coin_id, days=90)
            if new_daily:
                coins[coin_id] = {
                    "daily": new_daily,
                    "last_date": max(new_daily),
                    "fetched_at": _now_iso(),
                    "status": "live",
                }
        except Exception:
            if daily:
                coins[coin_id] = {
                    "daily": daily,
                    "last_date": entry.get("last_date") or max(daily),
                    "fetched_at": fetched_at,
                    "status": "stale",
                }
            else:
                coins[coin_id] = {
                    "daily": {},
                    "last_date": None,
                    "fetched_at": fetched_at,
                    "status": "failed",
                }

    if coins:
        _write_cache(coins)

    series: dict[str, dict[str, float]] = {}
    for cid, entry in coins.items():
        if entry.get("daily"):
            series[cid] = entry["daily"]
    return series


def load_universe_daily_meta() -> dict[str, Any]:
    """Per-coin last-date and fetch status for breadth coverage UI."""
    cache = _load_cache()
    coins = cache.get("coins") or {}
    out: dict[str, Any] = {}
    for cid, entry in coins.items():
        out[cid] = {
            "last_date": entry.get("last_date"),
            "fetched_at": entry.get("fetched_at"),
            "status": entry.get("status"),
            "days": len(entry.get("daily") or {}),
        }
    return out


def _alt_30d_pct(coin_id: str, ev: dict[str, Any], universe_daily: dict[str, dict[str, float]]) -> float | None:
    mp = ev.get("market_prices") or {}
    row = mp.get(coin_id, {})
    if row.get("usd_30d_change") is not None:
        return float(row["usd_30d_change"])
    daily = universe_daily.get(coin_id) or {}
    return pct_change(daily, 30)


def compute_broad_alt_equal_weight_30d(
    ev: dict[str, Any],
    universe_daily: dict[str, dict[str, float]],
) -> tuple[float | None, int]:
    """Equal-weight mean 30d return of fixed breadth universe (ex-BTC panel)."""
    cfg = load_universe_config()
    ids = [c["coingecko_id"] for c in cfg.get("constituents", [])]
    vals: list[float] = []
    for cid in ids:
        v = _alt_30d_pct(cid, ev, universe_daily)
        if v is not None:
            vals.append(v)
    if not vals:
        return None, 0
    return sum(vals) / len(vals), len(vals)


def compute_market_breadth(ev: dict[str, Any], universe_daily: dict[str, dict[str, float]]) -> dict[str, Any]:
    cfg = load_universe_config()
    constituents = cfg.get("constituents") or []
    universe_size = len(constituents)
    btc_30 = btc_30d_pct_coingecko(ev)

    rs_pp: list[float] = []
    above_sma = 0
    sma_n = 0
    beat_btc = 0
    rs_n = 0
    daily_available = 0

    for c in constituents:
        cid = c["coingecko_id"]
        alt_30 = _alt_30d_pct(cid, ev, universe_daily)
        daily = universe_daily.get(cid) or {}
        if daily:
            daily_available += 1
        above = _pct_above_sma(daily)
        if above is not None:
            sma_n += 1
            if above:
                above_sma += 1
        if alt_30 is not None and btc_30 is not None:
            rs_n += 1
            if alt_30 > btc_30:
                beat_btc += 1
            rs_pp.append(alt_30 - btc_30)

    broad_avg, broad_n = compute_broad_alt_equal_weight_30d(ev, universe_daily)

    meta = ev.get("breadth_universe_daily_meta") or {}
    daily_live = 0
    daily_stale = 0
    daily_failed = 0
    for c in constituents:
        cid = c["coingecko_id"]
        if not universe_daily.get(cid):
            continue
        status = (meta.get(cid) or {}).get("status") or "stale"
        if status == "live":
            daily_live += 1
        elif status == "stale":
            daily_stale += 1
        else:
            daily_failed += 1
    if daily_stale:
        daily_provenance = f"{daily_live} live / {daily_stale} cached"
    elif daily_live:
        daily_provenance = f"{daily_live} live"
    else:
        daily_provenance = None

    return {
        "universe_name": cfg.get("name"),
        "universe_size": universe_size,
        "pct_outperforming_btc_30d": round(beat_btc / rs_n * 100, 1) if rs_n else None,
        "outperforming_n": beat_btc,
        "outperforming_sample_n": rs_n,
        "median_alt_btc_30d_pp": round(median(rs_pp), 2) if rs_pp else None,
        "broad_alt_avg_30d_pct": round(broad_avg, 2) if broad_avg is not None else None,
        "broad_alt_sample_n": broad_n,
        "pct_above_50dma": round(above_sma / sma_n * 100, 1) if sma_n else None,
        "above_50dma_n": above_sma,
        "above_50dma_sample_n": sma_n,
        "above_50dma_coverage": f"{above_sma}/{sma_n}" if sma_n else None,
        "daily_available_n": daily_available,
        "daily_available_coverage": f"{daily_available}/{universe_size}",
        "daily_live_n": daily_live,
        "daily_stale_n": daily_stale,
        "daily_failed_n": daily_failed,
        "daily_series_provenance": daily_provenance,
        "btc_30d_pct": btc_30,
        "btc_30d_source": "coingecko_markets",
        "cg_market_as_of": cg_market_as_of(ev),
    }


def compute_portfolio_breadth(ev: dict[str, Any]) -> dict[str, Any]:
    alts = ev.get("alt_snapshots") or []
    btc_30 = btc_30d_pct_coingecko(ev)
    beating = sum(
        1
        for a in alts
        if a.get("change_30d_pct") is not None and btc_30 is not None and a["change_30d_pct"] > btc_30
    )
    tracked = sum(1 for a in alts if a.get("change_30d_pct") is not None)
    return {
        "beating_btc_30d": beating,
        "tracked_with_30d": tracked,
        "total_holdings": len(alts),
    }


def fetch_universe_daily_for_evidence(coin_ids: list[str]) -> dict[str, dict[str, float]]:
    return load_universe_daily(coin_ids, refresh_stale=True)
