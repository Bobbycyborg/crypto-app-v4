"""DefiLlama pump.fun platform health — revenue, buyback, launchpad share."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lib.fetchers.http import get_json
from lib.v3.fields import field, missing_field

_PUMP_SLUG = "pump.fun"
_FEES_URL = f"https://api.llama.fi/summary/fees/{_PUMP_SLUG}"
_OVERVIEW_URL = (
    "https://api.llama.fi/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true"
)
_REVENUE_PAGE = "https://defillama.com/protocol/fees/pump.fun"

_cache: dict[str, Any] | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sum_windows(chart: list, days: int = 7) -> tuple[float, float | None]:
    if not chart or len(chart) < days:
        return 0.0, None
    last = sum(v for _, v in chart[-days:])
    prev = sum(v for _, v in chart[-2 * days : -days]) if len(chart) >= 2 * days else None
    return last, prev


def _pct_change(cur: float, prev: float | None) -> float | None:
    if prev is None or prev <= 0:
        return None
    return (cur - prev) / prev * 100


def _fmt_compact_usd(n: float) -> str:
    if abs(n) >= 1e6:
        return f"${n/1e6:.1f}M"
    if abs(n) >= 1e3:
        return f"${n/1e3:.0f}K"
    return f"${n:.0f}"


def fetch_pump_platform_health(*, refresh: bool = False) -> dict[str, Any]:
    global _cache
    if _cache is not None and not refresh:
        return _cache

    fetched_at = _now_iso()
    out: dict[str, Any] = {"fetched_at": fetched_at, "source": "defillama", "ok": False}
    try:
        rev = get_json(f"{_FEES_URL}?dataType=dailyRevenue")
        buy = get_json(f"{_FEES_URL}?dataType=dailyHoldersRevenue")
        fees = get_json(f"{_FEES_URL}?dataType=dailyFees")
        overview = get_json(_OVERVIEW_URL)
        protocols = overview if isinstance(overview, list) else overview.get("protocols", [])
        launchpads = [p for p in protocols if (p.get("category") or "") == "Launchpad"]
        launch_total_24h = sum(p.get("total24h") or 0 for p in launchpads)
        pump_lp = next((p for p in launchpads if p.get("slug") == _PUMP_SLUG), {})
        pump_fees_24h = float(pump_lp.get("total24h") or 0)
        share_pct = (pump_fees_24h / launch_total_24h * 100) if launch_total_24h else None

        rev_7d, rev_prev = _sum_windows(rev.get("totalDataChart") or [])
        buy_7d, buy_prev = _sum_windows(buy.get("totalDataChart") or [])
        fee_7d, fee_prev = _sum_windows(fees.get("totalDataChart") or [])

        rev_wow = _pct_change(rev_7d, rev_prev)
        buy_wow = _pct_change(buy_7d, buy_prev)
        fee_wow = _pct_change(fee_7d, fee_prev)
        methodology = fees.get("methodology") or {}

        out.update(
            {
                "ok": True,
                "revenue": {
                    "metric": "protocol_revenue",
                    "definition": methodology.get(
                        "Revenue",
                        "Pump protocol slice of bonding-curve fees plus graduation/Mayhem fees.",
                    ),
                    "total_7d_usd": rev_7d,
                    "total_24h_usd": rev.get("total24h"),
                    "wow_pct": rev_wow,
                    "display": f"{_fmt_compact_usd(rev_7d)}/wk",
                    "note": (
                        "Protocol revenue (not user fees)"
                        + (f" · {rev_wow:+.0f}% vs prior 7d" if rev_wow is not None else "")
                    ),
                    "source_url": _REVENUE_PAGE,
                },
                "buyback_burn": {
                    "metric": "holders_revenue",
                    "definition": methodology.get(
                        "HoldersRevenue",
                        "PUMP token buyback sourced from onchain burns.",
                    ),
                    "total_7d_usd": buy_7d,
                    "total_24h_usd": buy.get("total24h"),
                    "wow_pct": buy_wow,
                    "display": f"{_fmt_compact_usd(buy_7d)}/wk burned",
                    "note": (
                        "On-chain PUMP buyback/burn"
                        + (f" · {buy_wow:+.0f}% vs prior 7d" if buy_wow is not None else "")
                    ),
                    "source_url": _REVENUE_PAGE,
                },
                "launchpad_share": {
                    "metric": "fee_share_launchpad_category",
                    "definition": (
                        "pump.fun share of 24h fees among DefiLlama protocols tagged Launchpad "
                        "(user fees, not protocol revenue)."
                    ),
                    "share_pct_24h": share_pct,
                    "pump_fees_24h_usd": pump_fees_24h,
                    "launchpad_fees_24h_usd": launch_total_24h,
                    "launchpad_protocol_count": len(launchpads),
                    "pump_fees_wow_pct": fee_wow,
                    "display": f"{share_pct:.0f}%" if share_pct is not None else "UNKNOWN",
                    "note": (
                        "DefiLlama Launchpad-category 24h fees"
                        + (f" · pump fees {fee_wow:+.0f}% WoW" if fee_wow is not None else "")
                    ),
                    "source_url": _REVENUE_PAGE,
                    "top_peers_24h": [
                        {
                            "name": p.get("name"),
                            "slug": p.get("slug"),
                            "fees_24h_usd": p.get("total24h"),
                        }
                        for p in sorted(launchpads, key=lambda x: -(x.get("total24h") or 0))[:5]
                    ],
                },
            }
        )
    except Exception as exc:
        out["error"] = str(exc)

    _cache = out
    return out


def platform_health_fields(health: dict[str, Any] | None, fetched_at: str) -> list[dict]:
    if not health or not health.get("ok"):
        return [
            missing_field("platform_revenue", "Weekly platform revenue"),
            missing_field("buyback_burn", "Programmatic buyback / burn"),
            missing_field("launchpad_share", "Launchpad market share vs peers"),
        ]

    at = health.get("fetched_at") or fetched_at
    rev = health["revenue"]
    buy = health["buyback_burn"]
    share = health["launchpad_share"]
    return [
        field(
            "platform_revenue",
            "Weekly platform revenue",
            rev["display"],
            unit="USD",
            source="defillama",
            source_url=rev["source_url"],
            fetched_at=at,
            note=rev["note"],
            confidence="MEDIUM",
        ),
        field(
            "buyback_burn",
            "Programmatic buyback / burn",
            buy["display"],
            unit="USD",
            source="defillama",
            source_url=buy["source_url"],
            fetched_at=at,
            note=buy["note"],
            confidence="MEDIUM",
        ),
        field(
            "launchpad_share",
            "Launchpad market share vs peers",
            share["display"],
            source="defillama",
            source_url=share["source_url"],
            fetched_at=at,
            note=share["note"],
            confidence="MEDIUM",
        ),
    ]
