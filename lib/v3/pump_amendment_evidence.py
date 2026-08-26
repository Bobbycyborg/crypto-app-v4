"""PUMP V3 amendment pack — static JSON only. Not canonical until review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AMENDMENT_PATH = (
    ROOT
    / "reports"
    / "2026-08-17"
    / "pump-v3-amendment"
    / "derived"
    / "amendment_evidence.json"
)


def load_amendment_evidence() -> dict[str, Any] | None:
    if not AMENDMENT_PATH.is_file():
        return None
    try:
        data = json.loads(AMENDMENT_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def synthesize_pump_stance(amd: dict[str, Any] | None) -> dict[str, Any]:
    """Evidence-led stance. Does not force a more bullish read."""
    amd = amd or {}
    tape = amd.get("tape") or {}
    buy = amd.get("buyback") or {}
    unlocks = amd.get("unlocks") or {}
    flow = (unlocks.get("august_drip") or {}).get("claimed_distribution") or {}

    parts: list[str] = []
    supports: list[str] = []
    holds: list[str] = []

    if buy.get("latest_daily_usd") and (amd.get("policy") or {}).get("allocation"):
        parts.append("VALUE CAPTURE STRONG")
        supports.append(
            "~50% of parent net revenue is locked into programmatic PUMP buybacks/burns through ~Apr 2027"
        )
    fund = tape.get("funding_8h")
    if fund is not None and abs(float(fund)) < 0.0002:
        parts.append("FUNDING CALM")
        supports.append(f"Binance funding {float(fund):.6f}/8h — not crowded-long in this snapshot")
    if tape.get("read") == "PERPS LEAD":
        parts.append("PERPS LEAD")
        holds.append(
            f"Binance futures ${tape.get('futures_quote_24h_usd', 0)/1e6:.0f}M vs spot "
            f"${tape.get('spot_quote_24h_usd', 0)/1e6:.0f}M — perps dominate; do not say spot leads"
        )
    parts.append("SUPPLY BEHAVIOUR STILL UNDER OBSERVATION")
    if flow.get("status") != "VERIFIED":
        holds.append("August recipient → CEX/DEX/OTC 72h flow is UNKNOWN. Transfer ≠ sale.")
    holds.append("UNKNOWN large holders (incl. ~25B / 25B / 24B / 23B / 19.13B) can move supply.")
    community = unlocks.get("community_tbd") or {}
    if community.get("tokens"):
        holds.append(
            f"~{community['tokens']/1e9:.0f}B community allocation is future supply uncertainty, not circulating."
        )

    headline = " · ".join(parts) if parts else "MIXED — EVIDENCE INCOMPLETE"
    wow = buy.get("wow_pct")
    wow_bit = f" · 7d buybacks {wow:+.0f}% vs prior week" if wow is not None else ""
    summary = (
        "Tokenomics/value capture is the strong leg: live buybacks exist and the ~50% revenue path is locked "
        f"for now{wow_bit}. Market confirmation is mixed (funding calm, perps still lead). "
        "Supply behaviour after unlocks is not finished evidence."
    )
    return {
        "headline": headline,
        "summary": summary,
        "confidence": "MEDIUM",
        "why": (
            "Pump.fun success creates PUMP demand only through the buyback/burn path "
            "(~50% of parent net revenue, not 100%). That path is observable now, but it does not "
            "require price to rise. Unlocks, UNKNOWN holders, and perp-led tape keep the stance mixed."
        ),
        "supports": supports[:3],
        "holds_back": holds[:3],
        "stronger_if": [
            "72h tracing shows no material flow from August recipients to identified CEX/DEX/liquid venues",
            "Spot quote volume rises while funding stays calm and buybacks continue",
        ],
        "weaker_if": [
            "Daily close below $0.00215",
            "Material UNKNOWN-holder or Squads supply reaches CEX/DEX with proven selling",
        ],
        "explanation": summary,
    }


def apply_amendment_to_doc(doc: dict[str, Any]) -> dict[str, Any]:
    amd = load_amendment_evidence()
    if not amd:
        return doc
    doc["amendment"] = amd
    stance = synthesize_pump_stance(amd)
    from lib.v3.current_stance import make_stance

    locked = make_stance(
        headline=stance["headline"],
        summary=stance["summary"],
        confidence=stance["confidence"],
        why=stance["why"],
        supports=stance["supports"],
        holds_back=stance["holds_back"],
        stronger_if=stance["stronger_if"],
        weaker_if=stance["weaker_if"],
    )
    top = doc.get("asset_top") or {}
    top["current_stance"] = locked
    doc["asset_top"] = top
    hero = doc.setdefault("hero", {})
    hero["v3_posture"] = locked["headline"]
    hero["v3_posture_note"] = locked["summary"]
    hero["v3_stance"] = locked["headline"]
    hero["v3_stance_note"] = locked["summary"]
    return doc
