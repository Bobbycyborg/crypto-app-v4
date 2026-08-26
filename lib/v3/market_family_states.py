"""Defensible Market family display states — product layer, not portfolio action."""

from __future__ import annotations

from typing import Any

from lib.v3.breadth_universe import btc_30d_pct_coingecko


def _fam(market: dict, fid: str) -> dict | None:
    for f in market.get("families", []):
        if f.get("family_id") == fid:
            return f
    return None


def _set_state(fam: dict, state: str, validation_note: str | None = None) -> None:
    fam["display_state"] = state
    if validation_note:
        fam["state_validation_note"] = validation_note


def classify_macro(ev: dict[str, Any]) -> tuple[str, str | None]:
    gl = ev.get("global_liquidity") or {}
    sc = ev.get("stablecoin_supply") or {}
    if not gl.get("ok") and not gl.get("partial_ok"):
        if not sc.get("ok"):
            return "UNKNOWN", "Stablecoin supply feed failed — no macro liquidity proxy."
        return (
            "UNKNOWN",
            "Global liquidity / financial-conditions composite not wired — stablecoin supply alone cannot classify macro capacity.",
        )

    supportive = 0
    restrictive = 0
    gp = gl.get("global_pulse_yoy")
    m2_yoy = gl.get("m2_yoy_pct")
    nfci = gl.get("nfci_latest")
    sc_ch90 = sc.get("change_90d_pct") if sc.get("ok") else None
    if gp is not None:
        if gp > 1.0:
            supportive += 1
        elif gp < -1.0:
            restrictive += 1
    if m2_yoy is not None:
        if m2_yoy > 2.0:
            supportive += 1
        elif m2_yoy < 0.0:
            restrictive += 1
    if nfci is not None:
        if nfci < -0.25:
            supportive += 1
        elif nfci > 0.25:
            restrictive += 1
    if sc_ch90 is not None:
        if sc_ch90 > 1.0:
            supportive += 1
        elif sc_ch90 < -1.0:
            restrictive += 1

    validation = (
        "Global pulse = mean YoY of US net liq, ECB assets, BoJ assets (3-region). "
        "China/UK not in composite. Descriptive thresholds only."
    )
    if supportive >= 2 and restrictive == 0:
        return "SUPPORTIVE", validation
    if restrictive >= 2 and supportive == 0:
        return "RESTRICTIVE", validation
    if restrictive > supportive:
        return "DRAINING", validation
    if supportive > restrictive:
        return "CONSTRUCTIVE", validation
    return "MIXED", validation


def classify_btc_regime(ev: dict[str, Any]) -> tuple[str, str | None]:
    analysis = ev.get("btc_analysis")
    if not analysis:
        return "UNKNOWN", "BTC daily history unavailable."
    leg = analysis.get("current_leg") or {}
    direction = (leg.get("dir") or "").lower()
    if direction == "down":
        state = "DOWN LEG"
    elif direction == "up":
        state = "UP LEG"
    else:
        state = "MIXED"
    return state, (
        "Descriptive swing leg only. Alt-risk HEALTHY/UNHEALTHY label needs backtested BTC regime rules."
    )


def classify_rotation(ev: dict[str, Any]) -> tuple[str, str | None]:
    mp = ev.get("market_prices") or {}
    btc_30 = btc_30d_pct_coingecko(ev)
    eth_30 = mp.get("ethereum", {}).get("usd_30d_change")
    sol_30 = mp.get("solana", {}).get("usd_30d_change")
    if btc_30 is None:
        return "UNKNOWN", "BTC 30d return missing from CoinGecko batch."
    eth_btc = (eth_30 - btc_30) if eth_30 is not None else None
    sol_btc = (sol_30 - btc_30) if sol_30 is not None else None
    if eth_btc is None and sol_btc is None:
        return "UNKNOWN", "ETH/SOL 30d returns missing."
    if eth_btc is not None and sol_btc is not None and eth_btc > 0 and sol_btc > 0:
        return "OUTWARD", "Major ETH/SOL both beating BTC on 30d — descriptive RS only."
    if eth_btc is not None and sol_btc is not None and eth_btc < 0 and sol_btc < 0:
        return "BTC LED", "Major ETH/SOL both lagging BTC on 30d — descriptive RS only."
    return "MIXED", "Mixed major RS — outward rotation backtest still required for risk-on label."


def classify_breadth(ev: dict[str, Any]) -> tuple[str, str | None]:
    mb = ev.get("market_breadth") or {}
    pct = mb.get("pct_outperforming_btc_30d")
    med = mb.get("median_alt_btc_30d_pp")
    if pct is None:
        return "UNKNOWN", "Participation universe 30d RS incomplete."
    if pct < 35 and (med is None or med < 0):
        return "NARROW", "Low % beating BTC and negative median alt/BTC — descriptive only."
    if pct > 50 and med is not None and med > 0:
        return "BROADENING", "Majority beating BTC with positive median — descriptive only."
    return "MIXED", "Participation thresholds for alt participation need backtest validation."


def classify_sector(ev: dict[str, Any]) -> tuple[str, str | None]:
    sd = ev.get("sector_destination") or {}
    ranked = sd.get("ranked_by_vs_btc") or []
    if not ranked:
        return "UNKNOWN", "Sector basket 30d ranks unavailable."
    top = ranked[0]
    return f"{top['label']} LEADS", "Sector rank by vs BTC — destination not participation."


def classify_fragility(ev: dict[str, Any]) -> tuple[str, str | None]:
    sf = ev.get("supporting_feeds") or {}
    frag = sf.get("btc_fragility") or {}
    funding = sf.get("btc_funding") or {}
    if not frag.get("ok"):
        return "UNKNOWN", "Binance OI / volume feeds failed."
    vol = frag.get("volume") or {}
    ratio = vol.get("perp_spot_ratio")
    pct_rank = funding.get("percentile_rank")
    if ratio is not None and ratio >= 5:
        state = "HEAVY"
    elif pct_rank is not None and pct_rank >= 80:
        state = "FUNDING STRETCHED"
    elif ratio is not None or funding.get("ok"):
        state = "MIXED"
    else:
        return "UNKNOWN", "Leverage context incomplete."
    return state, (
        "Raw leverage descriptors only — participation/concentration divergence and cross-venue OI still missing."
    )


CLASSIFIERS = {
    "macro_liquidity": classify_macro,
    "btc_regime": classify_btc_regime,
    "outward_rotation": classify_rotation,
    "breadth": classify_breadth,
    "sector_destination": classify_sector,
    "market_fragility": classify_fragility,
}


def apply_family_states(market: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    unknown: list[dict[str, str]] = []
    for fid, fn in CLASSIFIERS.items():
        fam = _fam(market, fid)
        if not fam:
            continue
        state, validation = fn(evidence)
        _set_state(fam, state, validation)
        if state == "UNKNOWN":
            unknown.append(
                {
                    "family_id": fid,
                    "reason": validation or fam.get("note") or "Insufficient evidence.",
                }
            )
    market["state_audit"] = {"unknown_families": unknown}
    return market


def build_market_summary(market: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    families = market.get("families", [])
    states = {f["family_id"]: f.get("display_state") for f in families}
    classified = sum(1 for s in states.values() if s and s != "UNKNOWN")
    unknown_n = sum(1 for s in states.values() if s == "UNKNOWN")

    snippets: list[str] = []
    btc = states.get("btc_regime")
    if btc and btc != "UNKNOWN":
        snippets.append(btc.lower())
    rot = states.get("outward_rotation")
    if rot and rot != "UNKNOWN":
        snippets.append(rot.lower().replace("_", " "))
    br = states.get("breadth")
    if br and br != "UNKNOWN":
        snippets.append(br.lower())
    frag = states.get("market_fragility")
    if frag and frag not in ("UNKNOWN", "MIXED"):
        snippets.append(frag.lower().replace("_", " "))

    environment = " · ".join(snippets) if snippets else "Mixed — see family cards"

    return {
        "environment_line": environment,
        "families_total": len(families),
        "families_classified": classified,
        "families_unknown": unknown_n,
        "portfolio_action": "Monitoring only",
        "portfolio_action_note": "No deploy or reduce rule wired — market read is separate from portfolio action.",
        "states": states,
    }
