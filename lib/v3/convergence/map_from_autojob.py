"""Map AUTOJOB collect_all() bundle → convergence payload per asset."""

from __future__ import annotations

from typing import Any

from lib.v3.convergence.completeness import build_context, dimension_rows
from lib.v3.convergence.engine import DIM_FUNDAMENTALS_SUPPLY, ConvergenceResult, Row, evaluate_convergence
from lib.v3.convergence.profiles import TWELVE, get_profile


def _headline(result: ConvergenceResult) -> str:
    if result.convergence == "ALIGNED" and result.aligned_direction:
        return f"CONVERGENCE: ALIGNED {result.aligned_direction}"
    return f"CONVERGENCE: {result.convergence}"


def _next_label(convergence: str) -> str:
    return "Next evidence priority" if convergence == "INSUFFICIENT" else "Next confirmation"


def _synthesis(sym: str, result: ConvergenceResult, rows: list[Row]) -> dict[str, str]:
    """Qualitative copy — no scores. INSUFFICIENT gate → conservative aligns line."""
    aligns = "No clear directional alignment yet."

    pos_complete = result.directional_votes.get("positive") or []
    neg_complete = result.directional_votes.get("negative") or []

    conflicts = "None currently resolvable — too many incomplete rows."
    if result.convergence != "INSUFFICIENT":
        if pos_complete and neg_complete:
            conflicts = (
                f"{pos_complete[0]} vs {neg_complete[0]} — complete evidence only, no gate block."
            )
        elif len(pos_complete) == 1 and not neg_complete:
            conflicts = "Single directional complete row — not enough for alignment."

    if result.convergence == "INSUFFICIENT":
        weak_dims = [r.dimension for r in rows if r.evidence_status in ("PARTIAL", "INSUFFICIENT")]
        if sym in ("FARTCOIN", "SPX6900"):
            has_weak_rs = any(r.dimension == "Price + RS" and r.evidence_status != "COMPLETE" for r in rows)
            has_support_supply = any(
                r.dimension == DIM_FUNDAMENTALS_SUPPLY
                and r.state == "SUPPORTIVE"
                and r.evidence_status == "COMPLETE"
                for r in rows
            )
            has_weak_price = any(r.dimension == "Price + RS" and r.state == "WEAK" for r in rows)
            if has_weak_price and has_support_supply:
                conflicts = (
                    "Weak price/RS vs supportive supply — incomplete spot, whale and attention "
                    "evidence prevents a cleaner read."
                )
            elif sym == "FARTCOIN" and has_support_supply:
                conflicts = (
                    "Supportive supply vs weak/mixed tape — whale and attention panels stay incomplete."
                )
        missing = (
            f"Incomplete dimensions: {', '.join(weak_dims)}. "
            "Attention has no weekly Trends series in AUTOJOB."
        )
    else:
        missing = "Further evidence would sharpen directional read."

    next_priority = _next_priority(sym, rows, result.convergence)

    return {
        "aligns": aligns,
        "conflicts": conflicts,
        "missing": missing,
        "next_priority": next_priority,
    }


def _next_priority(sym: str, rows: list[Row], convergence: str) -> str:
    if convergence != "INSUFFICIENT":
        return "Monitor for second complete directional row on priority dimension."

    by_dim = {r.dimension: r for r in rows}
    att = by_dim.get("Attention")
    if att and att.evidence_status == "INSUFFICIENT":
        if sym == "SPX6900":
            return (
                "Confirm spot-led participation across major CEXs — perp/OI presence alone "
                "does not prove buyer quality."
            )
        if sym == "FARTCOIN":
            return (
                "Verify discretionary buyers beyond bounded DEX sample — venue presence alone "
                "does not resolve flow quality."
            )

    spot = by_dim.get("Spot / Capital")
    if spot and spot.evidence_status == "PARTIAL":
        return "Prove spot-led participation or buyer quality beyond venue/OI panel."

    whales = by_dim.get("Whales / Players")
    if whales and whales.evidence_status == "PARTIAL":
        return "Improve beneficiary labelling beyond concentration snapshot."

    price = by_dim.get("Price + RS")
    if price and price.evidence_status == "PARTIAL":
        if sym in ("FARTCOIN", "GRASS", "IO", "NOS"):
            return "Attach missing priority RS benchmark series for this asset profile."
        return "Refresh priority RS vs BTC/SOL with full technical structure."

    return "Close weakest evidence dimension before synthesis upgrade."


def map_asset(bundle: dict[str, Any], sym: str) -> dict[str, Any]:
    profile = get_profile(sym)
    ctx = build_context(bundle, profile)
    raw_rows = dimension_rows(ctx)
    rows = [Row(d, s, e) for d, s, e in raw_rows]
    result = evaluate_convergence(rows)
    synthesis = _synthesis(sym, result, rows)

    return {
        "asset": sym,
        "slug": profile.slug,
        "as_of": bundle.get("fetched_at"),
        "headline": _headline(result),
        "convergence": result.convergence,
        "aligned_direction": result.aligned_direction,
        "next_label": _next_label(result.convergence),
        "rows": [r.to_dict() for r in rows],
        "synthesis": synthesis,
        "_qa": {
            "weak_count": result.weak_count,
            "complete_count": result.complete_count,
            "directional_votes": result.directional_votes,
        },
    }


def map_all_assets(bundle: dict[str, Any]) -> dict[str, Any]:
    assets = {sym: map_asset(bundle, sym) for sym in TWELVE}
    return {
        "model_version": "v1-frozen",
        "as_of": bundle.get("fetched_at"),
        "assets": assets,
    }
