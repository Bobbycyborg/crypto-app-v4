"""Sector destination — fixed basket relative strength vs BTC and broad alts."""

from __future__ import annotations

import json
from typing import Any

from lib.paths import CONFIG
from lib.v3.breadth_universe import (
    btc_30d_pct_coingecko,
    compute_broad_alt_equal_weight_30d,
    load_universe_config,
)


def load_sector_baskets() -> dict[str, Any]:
    return json.loads((CONFIG / "v3-sector-baskets.json").read_text())


def _basket_avg_30d(coin_ids: list[str], mp: dict[str, dict]) -> tuple[float | None, int]:
    vals: list[float] = []
    for cid in coin_ids:
        row = mp.get(cid, {})
        v = row.get("usd_30d_change")
        if v is not None:
            vals.append(float(v))
    if not vals:
        return None, 0
    return sum(vals) / len(vals), len(vals)


def _vs_phrase(pp: float, benchmark: str) -> str:
    mag = abs(pp)
    if pp >= 0:
        return f"outperforming {benchmark} by {mag:.1f}pp"
    return f"underperforming {benchmark} by {mag:.1f}pp"


def _sector_subline(s: dict[str, Any]) -> str:
    vs_btc = s.get("vs_btc_30d_pp")
    vs_broad = s.get("vs_broad_alt_30d_pp")
    n = s.get("constituents_with_30d") or 0
    total = s.get("constituent_count") or 0
    bits: list[str] = []
    if vs_btc is not None:
        if vs_btc >= 0:
            bits.append(f"Outperforming BTC by {abs(vs_btc):.1f}pp")
        else:
            bits.append(f"Still underperforming BTC by {abs(vs_btc):.1f}pp")
    if vs_broad is not None:
        bits.append(_vs_phrase(vs_broad, "broad alts"))
    bits.append(f"{n}/{total} constituents available")
    return " · ".join(bits)


def _strongest_display(ranked: list[dict[str, Any]]) -> tuple[str, str]:
    if not ranked:
        return "NO RANK DATA", "Sector basket prices unavailable."
    top = ranked[0]
    return f"{top['label']} STRONGEST SECTOR", _sector_subline(top)


def compute_sector_destination(ev: dict[str, Any]) -> dict[str, Any]:
    cfg = load_sector_baskets()
    mp = ev.get("market_prices") or {}
    universe_daily = ev.get("breadth_universe_daily") or {}
    btc_30 = btc_30d_pct_coingecko(ev)
    broad_30, broad_n = compute_broad_alt_equal_weight_30d(ev, universe_daily)

    sectors: list[dict[str, Any]] = []
    for basket in cfg.get("baskets", []):
        ids = [c["coingecko_id"] for c in basket.get("constituents", [])]
        avg_30, n = _basket_avg_30d(ids, mp)
        vs_btc = (avg_30 - btc_30) if avg_30 is not None and btc_30 is not None else None
        vs_broad = (avg_30 - broad_30) if avg_30 is not None and broad_30 is not None else None
        sectors.append(
            {
                "sector_id": basket["sector_id"],
                "label": basket["label"],
                "basket_avg_30d_pct": round(avg_30, 2) if avg_30 is not None else None,
                "vs_btc_30d_pp": round(vs_btc, 2) if vs_btc is not None else None,
                "vs_broad_alt_30d_pp": round(vs_broad, 2) if vs_broad is not None else None,
                "constituent_count": len(ids),
                "constituents_with_30d": n,
                "coverage": f"{n}/{len(ids)}",
            }
        )

    ranked = sorted(
        [s for s in sectors if s.get("vs_btc_30d_pp") is not None],
        key=lambda x: x["vs_btc_30d_pp"],
        reverse=True,
    )
    leader_display, leader_subline = _strongest_display(ranked)

    rank2_display = None
    rank2_subline = None
    if len(ranked) > 1:
        s2 = ranked[1]
        rank2_display = f"{s2['label']} · {s2['coverage']} available"
        rank2_subline = f"#{2} {s2['label']} {s2['vs_btc_30d_pp']:+.1f}pp vs BTC · {s2['coverage']} available"

    return {
        "leader_display": leader_display,
        "leader_subline": leader_subline,
        "rank2_display": rank2_display,
        "rank2_subline": rank2_subline,
        "sectors": sectors,
        "ranked_by_vs_btc": ranked,
        "btc_30d_pct": btc_30,
        "btc_30d_source": "coingecko_markets",
        "broad_alt_avg_30d_pct": round(broad_30, 2) if broad_30 is not None else None,
        "broad_alt_sample_n": broad_n,
        "broad_alt_method": "equal_weight_breadth_universe_mean",
        "method": cfg.get("method"),
    }
