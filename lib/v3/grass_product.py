"""GRASS V3 product layer — Stage-1 packs → asset_top, warnings, WCM, RC, HTML."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.v3.ath_frame import meaning, rc_title, retrace_label, timing_caption
from lib.paths import REPORTS, ROOT
from lib.v3.asset_top import (
    LIGHT_GREEN,
    LIGHT_ORANGE,
    LIGHT_UNKNOWN,
    empty_asset_top,
    enrich_tooltips,
    signal,
)
from lib.v3.change_mind import condition, pack_change_mind
from lib.v3.current_stance import grass_current_stance
from lib.v3.fields import category_state, pack_risk_confirmation, now_iso
from lib.v3.sma_trend import technical_trend_category
from lib.v3.grass_stage1_loader import load_grass_canonical
from lib.v3.reality_check import empty_reality_check, rc_item
from lib.v3.route_d_shell import (
    ICON_BAG,
    ICON_CIRCLES,
    ICON_DROP,
    ICON_GRID,
    ICON_LEVERAGE,
    ICON_NODES,
    evidence_tip_html,
    mline_tip,
    reality_check_section,
    warning_stack_html,
)


def _fmt_pp(v: Any) -> str:
    try:
        return f"{float(v):+.2f}pp"
    except (TypeError, ValueError):
        return "—"


def _fmt_pct(v: Any) -> str:
    try:
        return f"{float(v):+.1f}%"
    except (TypeError, ValueError):
        return "—"


def _fmt_m(v: Any) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.0f}k"
    return f"{n:,.0f}"


def _fmt_usd_m(v: Any) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(n) >= 1_000_000:
        return f"${n / 1_000_000:.0f}M"
    return f"${n:,.0f}"


def _s1(intel: dict) -> dict:
    return intel.get("stage1") or {}


def build_grass_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    c = doc.get("stage1") or {}
    price = c.get("price_structure") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    rs_render = c.get("rs_vs_render_pp") or {}
    deriv = c.get("derivatives") or {}
    vc = c.get("value_capture") or {}
    supply = c.get("supply") or {}
    flow = c.get("capital_flow") or {}
    mm = c.get("mm") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc") or now_iso()
    now_usd = price.get("now_usd")
    price_disp = f"~${now_usd:,.2f}" if isinstance(now_usd, (int, float)) else "—"
    rets = price.get("returns_pct") or {}

    top = empty_asset_top("GRASS", price_disp)
    top["price_as_of"] = as_of

    # --- 1 Price / Market Structure ---
    market_signals = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state="MIXED · NEAR-TERM LAGGING",
            display="MIXED · NEAR-TERM LAGGING",
            light=LIGHT_ORANGE,
            meaning=meaning("grass", price.get("drawdown_pct")),
            evidence=(
                f"GRASS {price_disp} · ATH ${price.get('ath_usd')} ({price.get('ath_date')}) · "
                f"drawdown {_fmt_pct(price.get('drawdown_pct'))} · "
                f"fut closes 7d {_fmt_pct(rets.get('7'))} · 30d {_fmt_pct(rets.get('30'))} · "
                f"90d {_fmt_pct(rets.get('90'))} · 180d {_fmt_pct(rets.get('180'))}. "
                f"Do not flatten into always-weak — 90d/180d recovery is real."
            ),
            source="CoinGecko + Binance futures daily",
            source_url="https://www.coingecko.com/en/coins/grass",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_btc",
            label="vs BTC",
            state="LAGGING 30d",
            display="LAGGING 30d",
            light=LIGHT_ORANGE,
            meaning="Relative strength vs Bitcoin — descriptive only.",
            evidence=(
                f"7d {_fmt_pp(rs_btc.get('7'))} · 30d {_fmt_pp(rs_btc.get('30'))} · "
                f"90d {_fmt_pp(rs_btc.get('90'))} · 180d {_fmt_pp(rs_btc.get('180'))}."
            ),
            source="Binance futures GRASS vs spot BTC",
            source_url="https://fapi.binance.com/fapi/v1/klines?symbol=GRASSUSDT&interval=1d",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_sol",
            label="vs SOL",
            state="LAGGING 7d/30d",
            display="LAGGING 7d/30d",
            light=LIGHT_ORANGE,
            meaning="Priority RS — GRASS is Solana-native.",
            evidence=(
                f"7d {_fmt_pp(rs_sol.get('7'))} · 30d {_fmt_pp(rs_sol.get('30'))} · "
                f"90d {_fmt_pp(rs_sol.get('90'))} · 180d {_fmt_pp(rs_sol.get('180'))}."
            ),
            source="Binance futures GRASS vs spot SOL",
            source_url="https://fapi.binance.com/fapi/v1/klines?symbol=GRASSUSDT&interval=1d",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_render_tao",
            label="vs RENDER / TAO",
            state="MIXED · MEDIUM-TERM AHEAD",
            display="90d/180d AHEAD",
            light=LIGHT_ORANGE,
            meaning="AI/DePIN peer context — optional, not a timing rule.",
            evidence=(
                f"vs RENDER 30d {_fmt_pp(rs_render.get('30'))} · 90d {_fmt_pp(rs_render.get('90'))}; "
                f"vs TAO 30d {_fmt_pp((c.get('rs_vs_tao_pp') or {}).get('30'))} · "
                f"90d {_fmt_pp((c.get('rs_vs_tao_pp') or {}).get('90'))}."
            ),
            source="Binance daily closes",
            as_of=as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["market_structure"]["signals"] = market_signals
    top["groups"]["market_structure"]["group_state"] = "MIXED · NEAR-TERM LAGGING"
    top["groups"]["market_structure"]["group_light"] = LIGHT_ORANGE
    top["groups"]["market_structure"]["title"] = "Price / Market Structure"

    # --- 2 Value Capture / Network Economics (reuse capital_flow slot visually as middle) ---
    # Remap: capital_flow group → value capture; project_supply → supply/capital
    vc_signals = [
        signal(
            signal_id="revenue",
            label="Disclosed Revenue",
            state="REVENUE REAL",
            display="REVENUE REAL",
            light=LIGHT_GREEN,
            meaning="First-party revenue disclosure — not audited financials.",
            evidence=(
                f"2025 {_fmt_usd_m(vc.get('revenue_2025_usd'))} · "
                f"2026 H1 {_fmt_usd_m(vc.get('revenue_2026_h1_usd'))} · "
                f"FY26 training-data guide {vc.get('fy2026_guide')} "
                f"({vc.get('fy2026_guide_label')}). Opex ~${vc.get('opex_month')}/mo disclosed."
            ),
            source="Grass July 7 2026 call recap",
            source_url=vc.get("call_url"),
            as_of=vc.get("call_as_of") or as_of,
            freshness="dated-call",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="token_mechanism",
            label="Revenue → GRASS Mechanism",
            state=vc.get("read") or "MECHANISM EXISTS · TOKEN BUY-PRESSURE UNPROVEN",
            display="MECHANISM EXISTS · BUY-PRESSURE UNPROVEN",
            light=LIGHT_ORANGE,
            meaning="Docs describe conversion; measured GRASS demand from revenue is UNKNOWN.",
            evidence=(
                f"{vc.get('doc_mechanism') or ''} "
                f"Measured revenue-driven GRASS buys = {vc.get('measured_buys_status')}. "
                "Do not say revenue automatically creates token demand."
            ),
            source="Grass Foundation docs",
            source_url=vc.get("doc_url"),
            as_of=as_of,
            freshness="docs",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="stage2_usdc",
            label="Stage 2 Rewards",
            state="USDC · ZERO NEW GRASS EMISSIONS",
            display="USDC · ZERO NEW EMISSIONS",
            light=LIGHT_GREEN,
            meaning="Stage 2 participant rewards funded by revenue in USDC.",
            evidence=str(vc.get("stage2_rewards") or ""),
            source="Grass July 7 2026 call recap",
            source_url=vc.get("call_url"),
            as_of=vc.get("call_as_of") or as_of,
            freshness="dated-call",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="spot_vs_leverage",
            label="Spot vs Leverage",
            state=deriv.get("read") or "LEVERAGE PRESENT",
            display="LEVERAGE PRESENT · FUT/SPOT UNKNOWN",
            light=LIGHT_ORANGE,
            meaning="Binance perp slice only — spot pair not listed.",
            evidence=(
                f"Perp 24h ~${_fmt_m(deriv.get('fut_quote_vol_24h'))} · "
                f"OI ~${_fmt_m(deriv.get('oi_notional_usd'))} · "
                f"~{deriv.get('oi_vs_30d_max_pct')}% of 30d max · "
                f"funding {deriv.get('funding_latest')}. {deriv.get('note','')}"
            ),
            source="Binance GRASSUSDT perps",
            source_url=deriv.get("source_url"),
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["capital_flow"]["signals"] = vc_signals
    top["groups"]["capital_flow"]["group_state"] = vc.get("group_read") or "REVENUE REAL · TOKEN CAPTURE EARLY"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_ORANGE
    top["groups"]["capital_flow"]["title"] = "Value Capture / Network Economics"

    supply_signals = [
        signal(
            signal_id="supply_pressure",
            label="Supply Pressure",
            state=f"MATERIAL",
            display="MATERIAL",
            light=LIGHT_ORANGE,
            meaning=supply.get("display_rule") or "",
            evidence=(
                f"Max {_fmt_m(supply.get('max_supply'))} · CG circulating ~{_fmt_m(supply.get('circulating_cg'))} · "
                f"investors {_fmt_m(supply.get('investors'))} · contributors {_fmt_m(supply.get('contributors'))} · "
                f"vesting ongoing. Next first-party unlock amount = UNKNOWN. "
                f"Secondary (PARTIAL/LOW): {supply.get('next_unlock_secondary') or '—'}."
            ),
            unknown="Exact next first-party unlock size unknown.",
            source="Foundation docs + CoinGecko",
            source_url="https://grass-foundation.gitbook.io/grass-docs/introduction/grass/grass-tokenomics",
            as_of=as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="who_is_buying",
            label="Who Is Buying?",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="No wallet-level sample this pass.",
            evidence=(
                f"DEX top-10 txn counts (bounded): buys {flow.get('dex_buys_24h')} / "
                f"sells {flow.get('dex_sells_24h')} · vol ~${_fmt_m(flow.get('dex_vol_24h'))}. "
                f"{flow.get('dex_note')}"
            ),
            unknown="CEX and wallet identity UNKNOWN. Not accumulation.",
            source="DexScreener top pools",
            source_url=flow.get("source_url"),
            as_of=as_of,
            freshness="same-day",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="who_is_selling",
            label="Who Is Selling?",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="TRANSFER ≠ SALE.",
            evidence="No labelled seller identity. DEX txn tape mixed/sell-leaning on a small slice only.",
            unknown="Seller identity unresolved.",
            source="Stage-1 capital-flow",
            as_of=as_of,
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="mm_otc",
            label="MM / OTC",
            state=mm.get("read") or "NO VERIFIED MATERIAL MM / OTC PRINT",
            display="NO MATERIAL PRINT",
            light=LIGHT_UNKNOWN,
            meaning="Absence is not a warning.",
            evidence="Shared MM registry scan: zero verified GRASS hits this pass.",
            source="Shared MM registry scan",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="UNKNOWN",
        ),
    ]
    top["groups"]["project_supply"]["signals"] = supply_signals
    top["groups"]["project_supply"]["group_state"] = "SUPPLY PRESSURE MATERIAL · BUYER IDENTITY UNKNOWN"
    top["groups"]["project_supply"]["group_light"] = LIGHT_ORANGE
    top["groups"]["project_supply"]["title"] = "Supply / Capital Flow"

    stance = grass_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "summary": stance["summary"],
        "confidence": stance["confidence"],
    }
    return enrich_tooltips(top)


def build_grass_warning_stack(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    vc = c.get("value_capture") or {}
    h1 = _fmt_usd_m(vc.get("revenue_2026_h1_usd"))
    cats = [
        technical_trend_category("grass"),
        category_state(
            "unlock_vest",
            "UNLOCK / VEST",
            "PARTIAL",
            detail=(
                "Investor 252M + contributor 220M allocations still vesting per Foundation docs. "
                "First-party shape KNOWN; 3/6/12m amounts still not first-party."
            ),
            summary="Investor + contributor vest ongoing",
        ),
        category_state(
            "token_capture",
            "TOKEN CAPTURE",
            "PARTIAL",
            detail="Docs say revenue converts to GRASS; no measured buy series. Do not equate revenue with token bid.",
            summary="Rev → GRASS unverified",
        ),
        category_state(
            "business_revenue",
            "BUSINESS REVENUE",
            "CLEAR",
            detail=f"First-party 2026 H1 revenue {h1} disclosed. Confirms the company, not the token bid.",
            summary=f"{h1} H1 2026 disclosed",
        ),
        category_state(
            "flow_identity",
            "FLOW IDENTITY",
            "UNKNOWN",
            detail="No labelled buyer/seller sample. UNKNOWN stays grey — not automatic red.",
            summary="Buyers / sellers UNKNOWN",
        ),
    ]
    return pack_risk_confirmation(cats, "GRASS Stage-1 completion packs")


def build_grass_change_mind(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    vc = c.get("value_capture") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    constructive = [
        condition(
            condition_id="revenue_funded_demand",
            title="Revenue-funded GRASS demand verified",
            summary="Persistent buys/burns/buybacks funded by revenue at meaningful scale.",
            status="NO",
            interpretation="Measured revenue-driven GRASS buys remain UNKNOWN.",
            evidence_rows=[
                ("Measured buys", vc.get("measured_buys_status") or "UNKNOWN"),
                ("Doc mechanism", "Stated"),
            ],
            source="Stage-1 value capture",
            source_url=vc.get("doc_url"),
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="UNKNOWN",
            icon="up",
        ),
        condition(
            condition_id="unlock_eases_rs",
            title="Unlock pressure eases with GRASS/SOL improvement",
            summary="Unlock overhang eases while GRASS/SOL improves with broader spot accumulation.",
            status="NO",
            interpretation=f"Near-term GRASS/SOL still {_fmt_pp(rs_sol.get('30'))} on 30d.",
            evidence_rows=[
                ("GRASS/SOL 30d", _fmt_pp(rs_sol.get("30"))),
                ("Next first-party unlock", "UNKNOWN"),
            ],
            source="Binance RS + supply pack",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
    ]
    defensive = [
        condition(
            condition_id="unlocks_without_capture",
            title="Large unlocks without clearer capture",
            summary="Vesting releases continue while token value capture stays unproven.",
            status="PARTIAL",
            interpretation="Supply pressure MATERIAL; buy-pressure still unproven.",
            evidence_rows=[("Supply pressure", "MATERIAL"), ("Buy-pressure", "UNPROVEN")],
            source="Foundation docs",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
        condition(
            condition_id="keeps_lagging_sol",
            title="Keeps lagging SOL without linkage proof",
            summary="GRASS keeps lagging SOL while revenue/token linkage remains unproven.",
            status="YES",
            interpretation="Current 7d/30d GRASS/SOL RS is negative.",
            evidence_rows=[
                ("7d", _fmt_pp(rs_sol.get("7"))),
                ("30d", _fmt_pp(rs_sol.get("30"))),
            ],
            source="Binance daily",
            as_of=as_of,
            confidence="HIGH",
            epistemic_status="KNOWN",
            icon="warn",
        ),
    ]
    return pack_change_mind(constructive, defensive)


def build_grass_reality_check(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    vc = c.get("value_capture") or {}
    supply = c.get("supply") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    rets = price.get("returns_pct") or {}

    rc = empty_reality_check()
    rc["priority_headline"] = "A real business does not automatically mean a strong token."
    rc["known"] = [
        rc_item(
            item_id="price_ath",
            title=rc_title("grass", price.get("drawdown_pct")),
            summary=f"~${price.get('now_usd')} · {_fmt_pct(price.get('drawdown_pct'))} from ATH ${price.get('ath_usd')}",
            interpretation=meaning("grass", price.get("drawdown_pct")),
            priority="HIGH",
            source="CoinGecko",
            source_url="https://www.coingecko.com/en/coins/grass",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
        ),
        rc_item(
            item_id="rs_mixed",
            title="Near-term lag vs SOL/BTC; medium-term recovery",
            summary=(
                f"SOL 30d {_fmt_pp(rs_sol.get('30'))} · BTC 30d {_fmt_pp(rs_btc.get('30'))} · "
                f"180d return {_fmt_pct(rets.get('180'))}"
            ),
            interpretation="Do not flatten into always-weak.",
            priority="HIGH",
            source="Binance futures GRASS vs spot peers",
            as_of=as_of,
            confidence="HIGH",
        ),
        rc_item(
            item_id="revenue",
            title="First-party revenue + opex disclosure",
            summary=(
                f"2025 {_fmt_usd_m(vc.get('revenue_2025_usd'))} · "
                f"2026 H1 {_fmt_usd_m(vc.get('revenue_2026_h1_usd'))} · "
                f"opex ~${vc.get('opex_month')}/mo"
            ),
            priority="HIGH",
            source="July 7 call recap",
            source_url=vc.get("call_url"),
            as_of=vc.get("call_as_of") or as_of,
            confidence="HIGH",
        ),
        rc_item(
            item_id="mechanism",
            title="Docs: rev→GRASS; Stage 2 paid USDC",
            summary="Mechanism exists · Stage 2 USDC = 0 new GRASS emissions",
            source="Foundation docs + call",
            source_url=vc.get("doc_url"),
            as_of=as_of,
            confidence="HIGH",
        ),
        rc_item(
            item_id="supply",
            title="Supply pressure MATERIAL",
            summary=f"Max {_fmt_m(supply.get('max_supply'))} · circ ~{_fmt_m(supply.get('circulating_cg'))} · vesting overhang",
            source="Foundation + CoinGecko",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
    ]
    rc["suggests"] = [
        rc_item(
            item_id="biz_vs_token",
            title="Business can be real; token still weak",
            summary="Revenue disclosure ≠ proven GRASS scarcity.",
            epistemic_status="INFERRED",
        ),
        rc_item(
            item_id="near_term_drivers",
            title="Price fits SOL beta + supply overhang",
            summary="7d/30d lag vs SOL; MATERIAL vesting still open.",
            epistemic_status="INFERRED",
        ),
        rc_item(
            item_id="usdc_rewards",
            title="USDC Stage 2 cuts emissions and demand",
            summary="Zero new GRASS for that payout — dual-edged.",
            epistemic_status="INFERRED",
        ),
    ]
    rc["unknowns"] = [
        rc_item(item_id="buyers", title="Wallet-level who is buying / selling", summary="No bounded Helius sample.", epistemic_status="UNKNOWN"),
        rc_item(item_id="buys", title="Measured revenue → GRASS buys/burns/buybacks", summary="Unproven at scale.", epistemic_status="UNKNOWN"),
        rc_item(item_id="unlock", title="Exact next first-party unlock size", summary="Secondary monitors only (PARTIAL/LOW).", epistemic_status="UNKNOWN"),
        rc_item(item_id="nodes", title="Exact active nodes / data-volume series", summary="Qualitative first-party only.", epistemic_status="UNKNOWN"),
        rc_item(item_id="mm", title="Verified MM/OTC GRASS events", summary="Registry: no material hit.", epistemic_status="UNKNOWN"),
    ]
    return rc


def grass_health_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    vc = c.get("value_capture") or {}
    as_of = vc.get("call_as_of") or (c.get("meta") or {}).get("fetched_at_utc")
    lines = (
        mline_tip(
            ICON_NODES,
            "2025 / 2026 H1 revenue",
            "First-party disclosure",
            f"{_fmt_usd_m(vc.get('revenue_2025_usd'))} / {_fmt_usd_m(vc.get('revenue_2026_h1_usd'))}",
            evidence_tip_html(
                name="REVENUE",
                read="REVENUE REAL",
                rows=[
                    ("2025", _fmt_usd_m(vc.get("revenue_2025_usd"))),
                    ("2026 H1", _fmt_usd_m(vc.get("revenue_2026_h1_usd"))),
                    ("FY26 guide", str(vc.get("fy2026_guide"))),
                    ("Guide label", vc.get("fy2026_guide_label") or ""),
                ],
                note="Disclosed figures — not audited. Do not equate revenue with token demand.",
                source="July 7 call recap",
                source_url=vc.get("call_url"),
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_GRID,
            "Commercial read",
            "Network / business",
            "REVENUE REAL",
            evidence_tip_html(
                name="NETWORK / COMMERCIAL TRACTION",
                read="REVENUE REAL",
                rows=[("Core lesson", "A real business does not automatically mean a strong token.")],
                note="Left side of the split.",
                source="Stage-1",
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Network / commercial traction</h4>"
        '<div class="band-status c-green">REVENUE REAL</div>'
        + lines
        + "</div>"
    )


def grass_token_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    supply = c.get("supply") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    dd = price.get("drawdown_pct")
    fill_w = f"{min(95, max(5, int(abs(float(dd or 90)))))}%"
    ddbar = (
        '<div class="ddbar">'
        f'<div class="ddbar-track"><div class="ddbar-fill" style="width:{fill_w}"></div></div>'
        f'<div class="ddbar-cap"><span>Now ${price.get("now_usd")}</span>'
        f"<span>{timing_caption('ATH $' + str(price.get('ath_usd')), dd)}</span></div>"
        "</div>"
    )
    lines = (
        mline_tip(
            ICON_DROP,
            "Token capture",
            "Buy-pressure",
            "UNPROVEN",
            evidence_tip_html(
                name="TOKEN CAPTURE",
                read="CAPTURE EARLY",
                rows=[
                    ("Mechanism", "Documented"),
                    ("Measured buys", "UNKNOWN"),
                    ("Supply pressure", supply.get("pressure_read") or "MATERIAL"),
                ],
                note="MECHANISM EXISTS · REVENUE REAL · TOKEN BUY-PRESSURE UNPROVEN",
                source="Stage-1 value capture",
                as_of=as_of,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_CIRCLES,
            "Near-term RS",
            "vs SOL",
            f"30d {_fmt_pp(rs_sol.get('30'))}",
            evidence_tip_html(
                name="TOKEN / MARKET",
                read="CAPTURE EARLY · SUPPLY MATERIAL · RS WEAK",
                rows=[
                    ("GRASS/SOL 7d", _fmt_pp(rs_sol.get("7"))),
                    ("GRASS/SOL 30d", _fmt_pp(rs_sol.get("30"))),
                ],
                note="Right side of the split.",
                source="Binance",
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-timing">'
        "<h4>Token / market confirmation</h4>"
        '<div class="band-status c-orange">CAPTURE EARLY · SUPPLY MATERIAL · RS WEAK</div>'
        + ddbar
        + lines
        + "</div>"
    )


def _fx_card(*, title, read, copy, tone, kpis, tip_rows, source, source_url, as_of, note) -> str:
    from lib.v3.forensic_cards import _esc, _details, _ev_row

    kpi_html = "".join(
        f'<div class="fx-kpi"><strong>{_esc(v)}</strong><span>{_esc(k)}</span></div>'
        for k, v in kpis
        if v
    )
    rows = "".join(_ev_row(k, v) for k, v in tip_rows if v)
    tip = evidence_tip_html(
        name=title, read=read, rows=tip_rows[:5], note=note,
        source=source, source_url=source_url, as_of=as_of, confidence="MEDIUM",
    )
    tone_cls = {"green": "green", "orange": "orange", "muted": ""}.get(tone, "")
    return (
        f'<section class="fx-card {tone_cls} has-tip">'
        f'<div class="metric-tip-template" hidden>{tip}</div>'
        f'<div class="fx-card-title">{_esc(title)}</div>'
        f'<div class="fx-card-read {tone}">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        f'<div class="fx-kpi-row">{kpi_html}</div>'
        + _details("View evidence detail", rows + f'<div class="fx-ev-note">{_esc(note)}</div>')
        + "</section>"
    )


def render_grass_evidence_cards(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    vc = c.get("value_capture") or {}
    supply = c.get("supply") or {}
    deriv = c.get("derivatives") or {}
    flow = c.get("capital_flow") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    cards = [
        _fx_card(
            title="Value capture",
            read=vc.get("read") or "TOKEN BUY-PRESSURE UNPROVEN",
            copy="Revenue is real. Token demand from that revenue is not automatically proven.",
            tone="orange",
            kpis=[
                ("2025 rev", _fmt_usd_m(vc.get("revenue_2025_usd"))),
                ("2026 H1", _fmt_usd_m(vc.get("revenue_2026_h1_usd"))),
                ("FY26 guide", str(vc.get("fy2026_guide") or "—")),
                ("Measured buys", "UNKNOWN"),
            ],
            tip_rows=[
                ("Doc mechanism", "Stated"),
                ("Stage 2", "USDC · zero new GRASS emissions"),
                ("Guide label", vc.get("fy2026_guide_label") or ""),
            ],
            source="Foundation docs + July 7 call",
            source_url=vc.get("call_url"),
            as_of=vc.get("call_as_of") or as_of,
            note="Do not say revenue automatically creates token demand.",
        ),
        _fx_card(
            title="Supply / vesting",
            read="MATERIAL",
            copy=supply.get("display_rule") or "",
            tone="orange",
            kpis=[
                ("Max", _fmt_m(supply.get("max_supply"))),
                ("CG circ", _fmt_m(supply.get("circulating_cg"))),
                ("Investors", _fmt_m(supply.get("investors"))),
                ("Contributors", _fmt_m(supply.get("contributors"))),
            ],
            tip_rows=[
                ("Next first-party unlock", "UNKNOWN"),
                ("Secondary (PARTIAL/LOW)", str(supply.get("next_unlock_secondary") or "—")),
            ],
            source="Foundation tokenomics",
            source_url="https://grass-foundation.gitbook.io/grass-docs/introduction/grass/grass-tokenomics",
            as_of=as_of,
            note=str(supply.get("next_unlock_secondary_note") or ""),
        ),
        _fx_card(
            title="Leverage slice",
            read=deriv.get("read") or "LEVERAGE PRESENT",
            copy=deriv.get("note") or "",
            tone="orange",
            kpis=[
                ("Perp 24h", f"${_fmt_m(deriv.get('fut_quote_vol_24h'))}"),
                ("OI", f"${_fmt_m(deriv.get('oi_notional_usd'))}"),
                ("vs 30d max", f"~{deriv.get('oi_vs_30d_max_pct')}%"),
                ("Funding", str(deriv.get("funding_latest"))),
            ],
            tip_rows=[("Binance spot", "Not listed")],
            source="Binance perps",
            source_url=deriv.get("source_url"),
            as_of=as_of,
            note="OI rising ≠ bearish. Funding quiet.",
        ),
        _fx_card(
            title="DEX txn tape (bounded)",
            read="NOT IDENTITY",
            copy=flow.get("dex_note") or "",
            tone="muted",
            kpis=[
                ("Buys", str(flow.get("dex_buys_24h"))),
                ("Sells", str(flow.get("dex_sells_24h"))),
                ("Vol", f"${_fmt_m(flow.get('dex_vol_24h'))}"),
            ],
            tip_rows=[("Who buying", "UNKNOWN"), ("Who selling", "UNKNOWN")],
            source="DexScreener",
            source_url=flow.get("source_url"),
            as_of=as_of,
            note="Not market-wide. Not accumulation.",
        ),
    ]
    return (
        '<section class="sec fx-sec" aria-label="Wallet and transaction evidence">'
        '<h3 class="fx-title">Wallet &amp; transaction evidence</h3>'
        '<div class="fx-section-note">Compact conclusions first. Revenue, supply and method stay in tips underneath.</div>'
        f'<div class="fx-mini-grid">{"".join(cards)}</div></section>'
    )


def render_grass_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">A real business does not automatically mean a strong token.</p>'
        "</div><div class=\"split\">"
        + grass_health_band(intel)
        + grass_token_band(intel)
        + "</div></section>"
    )
    return (
        split
        + warning_stack_html(intel)
        + change_mind_section(intel, slug="grass")
        + reality_check_section(intel)
        + render_grass_evidence_cards(intel)
    )


def build_grass_v3_from_packs(report_date: str, v4_report: dict | None = None) -> dict[str, Any]:
    stage1 = load_grass_canonical()
    price = stage1.get("price_structure") or {}
    stance = grass_current_stance()
    now_usd = price.get("now_usd")
    doc: dict[str, Any] = {
        "meta": {
            "schema": "grass-v3",
            "slug": "grass",
            "report_date": report_date,
            "generated_at": now_iso(),
            "version": "stage1-v1",
            "v4_report_date": (v4_report or {}).get("report_date"),
        },
        "hero": {
            "asset": "GRASS",
            "price_usd": now_usd,
            "price_display": f"~${now_usd:,.2f}" if isinstance(now_usd, (int, float)) else "—",
            "ath_display": f"${price.get('ath_usd')}",
            "drawdown_pct": price.get("drawdown_pct"),
            "price_as_of": (stage1.get("meta") or {}).get("fetched_at_utc"),
            "thesis": "A real business does not automatically mean a strong token.",
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
            "v3_stance": stance["headline"],
            "v3_stance_note": stance["summary"],
            "confidence": stance["confidence"],
            "data_completeness": "Stage-1 packs wired — buyer identity UNKNOWN; next unlock first-party UNKNOWN.",
        },
        "triad": {
            "lifecycle": {"display": "Post-ATH / mixed", "detail": meaning("grass", price.get("drawdown_pct"))},
            "project_health": {"display": "REVENUE REAL", "detail": "First-party revenue disclosed; token capture early."},
            "market_timing": {"display": "NEAR-TERM WEAK", "detail": "Lags SOL/BTC near-term; supply pressure material."},
        },
        "stage1": stage1,
    }
    doc["asset_top"] = build_grass_asset_top(doc)
    doc["warning_stack"] = build_grass_warning_stack(doc)
    doc["what_would_change_mind"] = build_grass_change_mind(doc)
    doc["reality_check"] = build_grass_reality_check(doc)
    return doc


def write_grass_v3(out_dir: Path | None = None) -> dict[str, Any]:
    report_date = now_iso()[:10]
    doc = build_grass_v3_from_packs(report_date)
    out_dir = out_dir or (REPORTS / report_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "grass-v3.json").write_text(payload, encoding="utf-8")
    (ROOT / "grass-v3.json").write_text(payload, encoding="utf-8")
    return doc
