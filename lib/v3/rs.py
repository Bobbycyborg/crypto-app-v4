"""Relative strength helpers — deterministic from aligned daily USD closes."""

from __future__ import annotations

from typing import Any


def align_series(a: dict[str, float], b: dict[str, float]) -> list[tuple[str, float, float]]:
    keys = sorted(set(a) & set(b))
    return [(d, a[d], b[d]) for d in keys]


def pct_change(prices: dict[str, float], days: int) -> float | None:
    if not prices:
        return None
    dates = sorted(prices)
    if len(dates) < days + 1:
        return None
    end = prices[dates[-1]]
    start = prices[dates[-1 - days]]
    if not start:
        return None
    return (end / start - 1) * 100


def ratio_now(asset: dict[str, float], ref: dict[str, float]) -> float | None:
    aligned = align_series(asset, ref)
    if not aligned:
        return None
    _, a, r = aligned[-1]
    if not r:
        return None
    return a / r


def ratio_change_pct(asset: dict[str, float], ref: dict[str, float], days: int) -> float | None:
    aligned = align_series(asset, ref)
    if len(aligned) < days + 1:
        return None
    end_ratio = aligned[-1][1] / aligned[-1][2]
    start_ratio = aligned[-1 - days][1] / aligned[-1 - days][2]
    if not start_ratio:
        return None
    return (end_ratio / start_ratio - 1) * 100


def rs_block(
    asset_id: str,
    asset_label: str,
    asset_prices: dict[str, float] | None,
    ref_prices: dict[str, float] | None,
    ref_label: str,
    fetched_at: str,
    *,
    impl_status: str = "PRODUCTION_READY",
) -> dict[str, Any]:
    if not asset_prices or not ref_prices:
        return {
            "pair_id": asset_id,
            "label": asset_label,
            "reference": ref_label,
            "ratio": None,
            "change_7d_pct": None,
            "change_30d_pct": None,
            "change_90d_pct": None,
            "data_status": "MISSING",
            "implementation_status": impl_status,
            "fetched_at": fetched_at,
            "note": "Price series unavailable for ratio calculation.",
        }
    ratio = ratio_now(asset_prices, ref_prices)
    return {
        "pair_id": asset_id,
        "label": asset_label,
        "reference": ref_label,
        "ratio": round(ratio, 6) if ratio is not None else None,
        "change_7d_pct": ratio_change_pct(asset_prices, ref_prices, 7),
        "change_30d_pct": ratio_change_pct(asset_prices, ref_prices, 30),
        "change_90d_pct": ratio_change_pct(asset_prices, ref_prices, 90),
        "data_status": "LIVE",
        "implementation_status": impl_status,
        "fetched_at": fetched_at,
        "source": "coingecko_market_chart",
        "epistemic_status": "KNOWN",
    }
