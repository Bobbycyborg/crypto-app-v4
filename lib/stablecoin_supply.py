"""DefiLlama aggregate stablecoin supply — total level and momentum."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lib.data_integrity import freshness_status
from lib.fetchers.http import get_json

_CHART_URL = "https://stablecoins.llama.fi/stablecoincharts/all"
_SOURCE_PAGE = "https://defillama.com/stablecoins"
_DAY_SEC = 86400


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_series(rows: list[dict]) -> list[tuple[int, float]]:
    out: list[tuple[int, float]] = []
    for row in rows:
        usd = row.get("totalCirculatingUSD", {}).get("peggedUSD")
        if usd is None:
            usd = row.get("totalCirculating", {}).get("peggedUSD")
        if usd is None:
            continue
        out.append((int(row["date"]), float(usd)))
    out.sort(key=lambda x: x[0])
    return out


def _closest(series: list[tuple[int, float]], target_ts: int) -> tuple[int, float] | None:
    if not series:
        return None
    return min(series, key=lambda x: abs(x[0] - target_ts))


def _pct_change(current: float, past: float) -> float | None:
    if past <= 0:
        return None
    return round((current - past) / past * 100, 2)


def fetch_stablecoin_supply() -> dict[str, Any]:
    """Return total USD supply, 30d/90d % change, timestamps, and freshness."""
    fetched_at = _now_iso()
    try:
        rows = get_json(_CHART_URL)
        series = _parse_series(rows)
        if len(series) < 2:
            raise ValueError("stablecoin chart empty")

        latest_ts, latest_usd = series[-1]
        as_of = datetime.fromtimestamp(latest_ts, tz=timezone.utc).strftime("%Y-%m-%d")

        ch30: float | None = None
        ch90: float | None = None
        pt30 = _closest(series, latest_ts - 30 * _DAY_SEC)
        pt90 = _closest(series, latest_ts - 90 * _DAY_SEC)
        if pt30:
            ch30 = _pct_change(latest_usd, pt30[1])
        if pt90:
            ch90 = _pct_change(latest_usd, pt90[1])

        return {
            "ok": True,
            "total_usd": latest_usd,
            "total_usd_b": round(latest_usd / 1e9, 2),
            "change_30d_pct": ch30,
            "change_90d_pct": ch90,
            "as_of": as_of,
            "fetched_at": fetched_at,
            "source": "defillama",
            "source_url": _SOURCE_PAGE,
            "api_url": _CHART_URL,
            "freshness": freshness_status(fetched_at),
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "total_usd": None,
            "total_usd_b": None,
            "change_30d_pct": None,
            "change_90d_pct": None,
            "as_of": None,
            "fetched_at": fetched_at,
            "source": "defillama",
            "source_url": _SOURCE_PAGE,
            "api_url": _CHART_URL,
            "freshness": "MISSING",
            "error": str(exc),
        }

