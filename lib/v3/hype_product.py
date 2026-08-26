"""HYPE V3 product layer — venue success vs token capture / remaining supply."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.v3.ath_frame import meaning
from lib.paths import ROOT
from lib.v3.asset_top import (
    LIGHT_GREEN,
    LIGHT_ORANGE,
    LIGHT_UNKNOWN,
    empty_asset_top,
    enrich_tooltips,
    signal,
)
from lib.v3.change_mind import condition, pack_change_mind
from lib.v3.current_stance import hype_current_stance
from lib.v3.fields import category_state, pack_risk_confirmation, now_iso
from lib.v3.sma_trend import technical_trend_category
from lib.v3.reality_check import empty_reality_check, rc_item
from lib.v3.route_d_shell import (
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
from lib.v3.hype_stage1_loader import STANCE_HEADLINE, load_hype_canonical

CG = "https://www.coingecko.com/en/coins/hyperliquid"
HL_INFO = "https://api.hyperliquid.xyz/info"
FEES_DOCS = "https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees"
SRC = "HYPE Stage-1 evidence"


def _s1(intel: dict[str, Any]) -> dict[str, Any]:
    return intel.get("stage1") or {}


def _fmt_pp(v: Any) -> str:
    try:
        return f"{float(v):+.1f}pp"
    except (TypeError, ValueError):
        return "—"


def _fmt_pct(v: Any) -> str:
    try:
        return f"{float(v):+.1f}%"
    except (TypeError, ValueError):
        return "—"


def _fmt_n(v: Any) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"{n:,.0f}"
    return f"{n:,.2f}"


def _fmt_usd(v: Any) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(n) >= 1_000_000_000:
        return f"${n / 1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"${n:,.0f}"
    return f"${n:,.2f}"


def _price_disp(now_usd: Any) -> str:
    try:
        return f"~${float(now_usd):,.2f}"
    except (TypeError, ValueError):
        return "—"


def build_hype_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    c = _s1(doc)
    price = c.get("price_structure") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    spot = c.get("spot_liquidity") or {}
    lev = c.get("leverage") or {}
    supply = c.get("supply") or {}
    vc = c.get("value_capture") or {}
    fees = c.get("fees") or {}
    own = c.get("ownership") or {}
    flow = c.get("capital_flow") or {}
    mm = c.get("mm") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc") or now_iso()
    now_usd = price.get("now_usd")
    rets = price.get("returns_pct") or {}

    top = empty_asset_top("HYPE", _price_disp(now_usd))
    top["price_as_of"] = as_of

    top["groups"]["market_structure"]["signals"] = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state="NEAR-TERM MIXED / SOFT",
            display="30d SOFT · 90d/180d RECOVERY",
            light=LIGHT_ORANGE,
            meaning=meaning("hype", price.get("drawdown_pct")),
            evidence=(
                f"HYPE {_price_disp(now_usd)} · ATH ${price.get('ath_usd')} ({price.get('ath_date')}) · "
                f"drawdown {_fmt_pct(price.get('drawdown_pct'))}. "
                f"Aligned 7d {_fmt_pct(rets.get('7'))} · 30d {_fmt_pct(rets.get('30'))} · "
                f"90d {_fmt_pct(rets.get('90'))} · 180d {_fmt_pct(rets.get('180'))}. "
                f"RS uses Binance perp HYPE vs spot BTC/SOL because Binance.com spot is not listed."
            ),
            source="CoinGecko + Binance perp daily",
            source_url=price.get("source_url_cg") or CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_btc",
            label="vs BTC",
            state="30d LAGGING",
            display="LAGS BTC 30d",
            light=LIGHT_ORANGE,
            meaning="Priority near-term window is 30d. 90d/180d recovery is context, not a timing signal.",
            evidence=(
                f"7d {_fmt_pp(rs_btc.get('7'))} · 30d {_fmt_pp(rs_btc.get('30'))} · "
                f"90d {_fmt_pp(rs_btc.get('90'))} · 180d {_fmt_pp(rs_btc.get('180'))}."
            ),
            source="Binance aligned HYPE perp vs BTC spot",
            source_url=price.get("source_url_binance"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_sol",
            label="vs SOL",
            state="NOT LEADING",
            display="LAGS SOL 7d/30d",
            light=LIGHT_ORANGE,
            meaning="Do not describe current HYPE as leading SOL.",
            evidence=(
                f"7d {_fmt_pp(rs_sol.get('7'))} · 30d {_fmt_pp(rs_sol.get('30'))} · "
                f"90d {_fmt_pp(rs_sol.get('90'))} · 180d {_fmt_pp(rs_sol.get('180'))}."
            ),
            source="Binance aligned HYPE perp vs SOL spot",
            source_url=price.get("source_url_binance"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["market_structure"]["group_state"] = "NEAR-TERM RS SOFT"
    top["groups"]["market_structure"]["group_light"] = LIGHT_ORANGE
    top["groups"]["market_structure"]["title"] = "Price / Market Structure"

    top["groups"]["capital_flow"]["signals"] = [
        signal(
            signal_id="spot_vs_leverage",
            label="Spot vs Leverage",
            state="HYPE-TOKEN LEVERAGE MATERIAL ON HL",
            display="NATIVE HYPE OI ~$1.24B",
            light=LIGHT_ORANGE,
            meaning="Platform OI is not HYPE-token OI. Binance is not the HYPE market.",
            evidence=(
                f"Binance.com spot {spot.get('binance_com_spot')} · Binance perp {spot.get('binance_perp')}. "
                f"Native HYPE perp OI {_fmt_usd(lev.get('hype_token_oi_usd'))} · "
                f"vol {_fmt_usd(lev.get('hype_token_day_notional_usd'))}/day · 10x max · funding quiet. "
                f"Binance HYPE OI {_fmt_usd(lev.get('binance_oi_usd'))} "
                f"(~{lev.get('binance_oi_pct_30d_max'):.0f}% of own 30d max). "
                f"Platform OI {_fmt_usd(lev.get('platform_oi_usd'))} is BTC/ETH/etc usage — not HYPE-token leverage. "
                f"{lev.get('note')}"
            ),
            source="Hyperliquid + Binance USDT-M",
            source_url=HL_INFO,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="who_is_buying",
            label="Who Is Buying?",
            state="AF ONLY EVIDENCED",
            display="ASSISTANCE FUND",
            light=LIGHT_UNKNOWN,
            meaning="AF buying is not organic retail, smart-money, or whale accumulation.",
            evidence=str(flow.get("evidenced_buyer")) + " Other buyers UNKNOWN. " + str(flow.get("note")),
            unknown="Market-wide buyers UNKNOWN.",
            source=SRC,
            source_url=FEES_DOCS,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="who_is_selling",
            label="Who Is Selling?",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="TRANSFER ≠ SALE. CEX deposit ≠ sale.",
            evidence="Sellers UNKNOWN. CEX flows UNKNOWN.",
            unknown="Market-wide sellers UNKNOWN.",
            source=SRC,
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="whales_major_holders",
            label="Whales / Major Holders",
            state="SYSTEM PARTIAL · DISCRETIONARY UNKNOWN",
            display="CONCENTRATION UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Do not invent top-10 or adjusted discretionary %. Validator name ≠ ownership.",
            evidence=(
                f"AF {_fmt_n(own.get('af'))} · HyperLabs {_fmt_n(own.get('hyperlabs'))} · "
                f"Foundation wallet {_fmt_n(own.get('foundation_wallet'))} · Grants {_fmt_n(own.get('grants'))}. "
                f"{own.get('read')} MM inventory {mm.get('status')} — not zero."
            ),
            unknown="Discretionary holder concentration UNKNOWN. HYPE MM inventory UNKNOWN.",
            source=SRC,
            source_url=HL_INFO,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="team_dev_ceo",
            label="Contributor / Labs inventory",
            state="LABELED WALLETS ≠ TEAM %",
            display="HYPERLABS NCU ~241M",
            light=LIGHT_ORANGE,
            meaning="HyperLabs NCU is contributor inventory still non-circulating. Not a team concentration statistic.",
            evidence=(
                f"HyperLabs 0x43e9 ~{_fmt_n(supply.get('hyperlabs_ncu'))} (almost all staked). "
                f"Foundation genesis wallet ~{_fmt_n(supply.get('foundation_wallet_sum'))}. "
                "Do not say Foundation owns 212.5M validator stake."
            ),
            source=SRC,
            source_url=HL_INFO,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="PARTIAL",
        ),
    ]
    top["groups"]["capital_flow"]["group_state"] = "AF BUYER KNOWN · REST UNKNOWN"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_UNKNOWN
    top["groups"]["capital_flow"]["title"] = "Spot / Leverage / Flows"

    cg_pct = supply.get("cg_circulating_pct")
    hl_pct = supply.get("hl_circulating_pct")
    top["groups"]["project_supply"]["signals"] = [
        signal(
            signal_id="project_health",
            label="Platform / Project Health",
            state="USAGE REAL · FEES DECELERATING VS OWN MONTH",
            display="PERPS 30d ~$44.8M FEES",
            light=LIGHT_GREEN,
            meaning="Healthy high base. Near-term deterioration versus own recent history — not dead, not accelerating.",
            evidence=(
                f"L1 perp day {_fmt_usd(lev.get('platform_day_notional_usd'))} · "
                f"platform OI {_fmt_usd(lev.get('platform_oi_usd'))}. "
                f"Perps fees 24h {_fmt_usd(fees.get('perps_24h'))} · 7d {_fmt_usd(fees.get('perps_7d'))} · "
                f"30d {_fmt_usd(fees.get('perps_30d'))} · 1m Δ {_fmt_pct(fees.get('perps_change_1m'))}. "
                f"{fees.get('read')} Protocol fees ≠ token-holder yield."
            ),
            source="Hyperliquid + DefiLlama",
            source_url=fees.get("source_url"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="liquidity_absorption",
            label="Value Capture / Buybacks",
            state="AF BUYBACKS REAL · BURN UNRESOLVED",
            display="AF ~46.4M HYPE",
            light=LIGHT_ORANGE,
            meaning="Buyback mechanism known. Do not display AF inventory as destroyed supply.",
            evidence=(
                f"{vc.get('production_wording')}. Inventory {_fmt_n(vc.get('af_inventory'))} at 0xfefe, not staked. "
                f"Circulating removal KNOWN. Total-supply burn CONFLICT "
                f"(HL totalSupply still ~{_fmt_n(supply.get('hl_total_supply'))}; 1B−total ≈ {_fmt_n(supply.get('implied_total_supply_reduction'))}). "
                f"{vc.get('note')}"
            ),
            source="Hyperliquid docs + live AF + tokenDetails",
            source_url=FEES_DOCS,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="CONFLICT",
        ),
        signal(
            signal_id="supply_unlocks",
            label="Supply / Unlocks",
            state="CIRCULATING MINORITY · CADENCE UNKNOWN",
            display=f"CG {cg_pct:.1f}% · HL {hl_pct:.1f}%",
            light=LIGHT_ORANGE,
            meaning="Definition split locked. Show both. Do not invent 9.92M/month.",
            evidence=(
                f"CG {_fmt_n(supply.get('cg_circulating'))} ({cg_pct:.1f}% of 1B). "
                f"Hyperliquid {_fmt_n(supply.get('hl_circulating'))} ({hl_pct:.1f}%). "
                f"HL formula: {supply.get('hl_formula')}. "
                f"futureEmissions {_fmt_n(supply.get('future_emissions'))}. "
                f"HyperLabs NCU {_fmt_n(supply.get('hyperlabs_ncu'))}. "
                f"3m/6m/12m release UNKNOWN. Contributor supply remains a material risk. "
                f"{supply.get('display_rule')}"
            ),
            source="HL tokenDetails + CoinGecko",
            source_url=HL_INFO,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="CONFLICT",
        ),
    ]
    top["groups"]["project_supply"]["group_state"] = "CIRCULATING MINORITY · CAPTURE PARTIAL"
    top["groups"]["project_supply"]["group_light"] = LIGHT_ORANGE
    top["groups"]["project_supply"]["title"] = "Protocol Economics / Supply / Value Capture"

    stance = hype_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "explanation": stance["summary"],
        "directional_state": "DESCRIPTIVE",
        "confidence": stance["confidence"],
        "evidence_refs": [],
    }
    return enrich_tooltips(top)


def build_hype_warning_stack(intel: dict[str, Any]) -> dict[str, Any]:
    """CONCERNS = ACTIVE+PARTIAL. Burn conflict stays UNKNOWN, not red."""
    c = _s1(intel)
    fees = c.get("fees") or {}
    supply = c.get("supply") or {}
    cg_pct = supply.get("cg_circulating_pct")
    hl_pct = supply.get("hl_circulating_pct")
    cg_vis = f"{float(cg_pct):.0f}%" if isinstance(cg_pct, (int, float)) else "22%"
    hl_vis = f"{float(hl_pct):.0f}%" if isinstance(hl_pct, (int, float)) else "30%"
    cats = [
        technical_trend_category("hype"),
        category_state(
            "venue_fees",
            "VENUE FEES",
            "PARTIAL",
            detail=(
                f"Perps 30d {_fmt_usd(fees.get('perps_30d'))} · 1m Δ {_fmt_pct(fees.get('perps_change_1m'))}. "
                "Fees real and decelerating. Not dead."
            ),
            summary=f"~{_fmt_usd(fees.get('perps_30d'))}/30d · soft vs own prior month",
        ),
        category_state(
            "af_buybacks",
            "AF BUYBACKS",
            "CLEAR",
            detail=(
                f"Fees → Assistance Fund buys. AF inventory ~{_fmt_n(supply.get('af_inventory'))} HYPE. "
                "Capture flow is real. Llama ~$31M/30d is the buy-side read — not organic demand."
            ),
            summary="Fees → AF buys (Llama ~$31M/30d)",
        ),
        category_state(
            "supply_overhang",
            "SUPPLY OVERHANG",
            "PARTIAL",
            detail=(
                f"Circ CONFLICT CG {cg_vis} / HL {hl_vis}. "
                f"futureEmissions ~{_fmt_n(supply.get('future_emissions'))}. "
                "Minority float. Cadence UNKNOWN. Discretionary concentration UNKNOWN."
            ),
            summary=f"Circ CONFLICT {cg_vis}/{hl_vis} · ~412M future emissions",
        ),
        category_state(
            "burn_accounting",
            "BURN ACCOUNTING",
            "UNKNOWN",
            detail=(
                f"Docs say burned. AF still holds ~{_fmt_n(supply.get('af_inventory'))}. "
                "CONFLICT is unknown/unresolved, not a proven failure. Do not paint red."
            ),
            summary="Docs say burned · AF still holds ~46.4M",
        ),
    ]
    return pack_risk_confirmation(cats, SRC)


def build_hype_change_mind(intel: dict[str, Any]) -> dict[str, Any]:
    constructive = [
        condition(
            condition_id="fees_reaccelerate_af_absorbs",
            title="Fees reaccelerate and AF keeps absorbing",
            summary="Venue fees stop decelerating while Assistance Fund buys continue to take HYPE out of float.",
            status="WATCH",
            interpretation="Would mean venue success is still converting into token bid. AF buys ≠ organic demand.",
            evidence_rows=[
                ("Perps 30d fees", "Real · decelerating vs prior month in Stage 1"),
                ("AF buys ~30d", "Llama ~$31M (Stage 1)"),
                ("AF inventory", "~46.4M accumulating"),
            ],
            source=SRC,
            source_url=FEES_DOCS,
            as_of="2026-08-13",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
        condition(
            condition_id="reclaim_50d",
            title="Reclaims and holds the 50-day",
            summary="HYPE reclaims the 50-day while remaining above the 200-day — buybacks showing up in structure.",
            status="NO",
            interpretation="Longer uptrend intact above 200d; 50d already lost. That is the near-term confirmation failure.",
            evidence_rows=[
                ("50d", "Below ~$60.5 (perp HYPEUSDT)"),
                ("200d", "Above ~$47.9"),
            ],
            source=SRC,
            source_url=CG,
            as_of="2026-08-13",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
    ]
    defensive = [
        condition(
            condition_id="fees_down_emissions_in",
            title="Fees keep falling as supply enters float",
            summary="Fee decline persists while remaining ~412M emissions or contributor releases enter circulating supply.",
            status="WATCH",
            interpretation="Would weaken the buyback bid just as float expands.",
            evidence_rows=[
                ("Perps 1m Δ", "~−32%"),
                ("futureEmissions", "~412M remaining"),
            ],
            source=SRC,
            source_url=HL_INFO,
            as_of="2026-08-13",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
        condition(
            condition_id="af_distributes",
            title="AF starts distributing",
            summary="Assistance Fund inventory begins distributing rather than accumulating.",
            status="WATCH",
            interpretation="Would reverse the only measured HYPE sink. Burn-accounting conflict stays unresolved — that alone does not change the thesis.",
            evidence_rows=[
                ("AF inventory", "~46.4M, accumulating in Stage 1"),
                ("AF ≠ organic demand", "Still true"),
            ],
            source=SRC,
            source_url=FEES_DOCS,
            as_of="2026-08-13",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
    ]
    return pack_change_mind(constructive, defensive, schema_version=1)


def build_hype_reality_check(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    lev = c.get("leverage") or {}
    supply = c.get("supply") or {}
    vc = c.get("value_capture") or {}
    fees = c.get("fees") or {}
    rc = empty_reality_check()
    rc["priority_headline"] = "HYPERLIQUID SUCCESS ≠ AUTOMATIC HYPE HOLDER SUCCESS"
    rc["known"] = [
        rc_item(
            item_id="venue",
            title="Venue usage and fees are real",
            summary=(
                f"L1 perp day {_fmt_usd(lev.get('platform_day_notional_usd'))} · "
                f"platform OI {_fmt_usd(lev.get('platform_oi_usd'))} · "
                f"perps 30d fees {_fmt_usd(fees.get('perps_30d'))}."
            ),
            evidence_rows=[
                ("1m fee Δ", _fmt_pct(fees.get("perps_change_1m"))),
                ("Read", str(fees.get("read"))),
            ],
            interpretation="High base, decelerating vs own recent month.",
            priority="HIGH",
            source=SRC,
            source_url=fees.get("source_url"),
            as_of="2026-08-13",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="af",
            title="Assistance Fund buybacks + inventory",
            summary=(
                f"Fee→HYPE buys. Inventory {_fmt_n(vc.get('af_inventory'))}. "
                "Ex-circ. Not staked."
            ),
            evidence_rows=[
                ("Buyback", "KNOWN"),
                ("Total-supply burn", "CONFLICT"),
            ],
            interpretation="AF inventory is not destroyed supply. Protocol fees ≠ token-holder yield.",
            priority="HIGH",
            source=SRC,
            source_url=FEES_DOCS,
            as_of="2026-08-13",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="circ_split",
            title="Circulating definition split",
            summary=(
                f"CG {supply.get('cg_circulating_pct'):.1f}% · "
                f"Hyperliquid {supply.get('hl_circulating_pct'):.1f}%. Both valid. Never pick one."
            ),
            evidence_rows=[
                ("HL formula", str(supply.get("hl_formula"))),
                ("futureEmissions", _fmt_n(supply.get("future_emissions"))),
            ],
            interpretation="CONFLICT LOCKED. Display both.",
            priority="HIGH",
            source=SRC,
            source_url=HL_INFO,
            as_of="2026-08-13",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="CONFLICT",
        ),
        rc_item(
            item_id="hype_lev",
            title="Native HYPE leverage is material",
            summary=(
                f"HYPE-token OI {_fmt_usd(lev.get('hype_token_oi_usd'))} · "
                f"not platform {_fmt_usd(lev.get('platform_oi_usd'))}."
            ),
            evidence_rows=[
                ("Binance.com spot", "NOT LISTED"),
                ("Binance perp", "PRESENT"),
            ],
            interpretation="Token utility: gas, staking/validation, fee discounts.",
            priority="HIGH",
            source=SRC,
            source_url=HL_INFO,
            as_of="2026-08-13",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    rc["suggests"] = [
        rc_item(
            item_id="s1",
            title="Venue tape stronger than holder proof",
            summary="Fees real; holder link is buybacks + unresolved burn.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s2",
            title="Remaining supply still has to be absorbed",
            summary="Minority float + ~412M emissions + ~241M HyperLabs NCU.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s3",
            title="Near-term market is not confirming leadership",
            summary="30d lags BTC/SOL. 90d/180d recovery ≠ current leadership.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s4",
            title="AF is a protocol buyer, not proof",
            summary="Fee-funded purchases ≠ organic demand. Other buyers UNKNOWN.",
            epistemic_status="INTERPRETATION",
        ),
    ]
    rc["unknowns"] = [
        rc_item(item_id="u1", title="Exact 3/6/12m releases", summary="No first-party dated series. Do not invent 9.92M/month.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u2", title="Discretionary holder concentration", summary="System wallets PARTIAL. No holder map. No top-10.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u3", title="Market-wide buyers/sellers", summary="Beyond AF: UNKNOWN. TRANSFER ≠ SALE.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u4", title="Organic non-AF demand", summary="AF buying is not organic demand.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u5", title="HYPE MM inventories", summary="HyperCore not in Solana/EVM registry. Absence ≠ zero.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u6", title="Daily AF buy series", summary="Inventory known; daily reconstruction not packed.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u7", title="HyperEVM activity", summary="Not packed in Stage 1.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u8", title="Total-supply burn accounting", summary="CONFLICT — docs/CG vs HL totalSupply + AF balance.", epistemic_status="CONFLICT"),
    ]
    return rc


def hype_platform_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    lev = c.get("leverage") or {}
    fees = c.get("fees") or {}
    spot = c.get("spot_liquidity") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    lines = (
        mline_tip(
            ICON_GRID,
            "Platform vs token",
            "Different questions",
            "VENUE ≠ HYPE OI",
            evidence_tip_html(
                name="PLATFORM vs HYPE-TOKEN",
                read="Do not use platform OI as HYPE-token OI",
                rows=[
                    ("L1 perp day", _fmt_usd(lev.get("platform_day_notional_usd"))),
                    ("Platform OI", _fmt_usd(lev.get("platform_oi_usd"))),
                    ("HYPE-token OI", _fmt_usd(lev.get("hype_token_oi_usd"))),
                    ("HYPE-token day vol", _fmt_usd(lev.get("hype_token_day_notional_usd"))),
                ],
                note=str(lev.get("note") or ""),
                source=SRC,
                source_url=HL_INFO,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_LEVERAGE,
            "Spot / perps",
            "Binance.com spot absent",
            "PERP PRESENT",
            evidence_tip_html(
                name="SPOT / LEVERAGE",
                read="HYPE-TOKEN LEVERAGE MATERIAL ON NATIVE HL",
                rows=[
                    ("Binance.com spot", str(spot.get("binance_com_spot"))),
                    ("Binance perp", str(spot.get("binance_perp"))),
                    ("Binance HYPE OI", _fmt_usd(lev.get("binance_oi_usd"))),
                    ("Native HYPE OI", _fmt_usd(lev.get("hype_token_oi_usd"))),
                ],
                note="Do not use Binance alone as the HYPE market. Funding quiet. OI ≠ bearish.",
                source=SRC,
                source_url=spot.get("source_url") or CG,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_NODES,
            "Fees",
            "Large, decelerating vs own month",
            "FEES LARGE · DECELERATING",
            evidence_tip_html(
                name="FEES",
                read=str(fees.get("read") or ""),
                rows=[
                    ("Perps 24h / 30d", f"{_fmt_usd(fees.get('perps_24h'))} / {_fmt_usd(fees.get('perps_30d'))}"),
                    ("1m Δ", _fmt_pct(fees.get("perps_change_1m"))),
                    ("30d over prior 30d", _fmt_pct(fees.get("perps_change_30dover30d"))),
                ],
                note="Protocol fees ≠ token-holder yield.",
                source=SRC,
                source_url=fees.get("source_url"),
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Platform / HYPE-token / fees</h4>"
        '<div class="band-status c-orange">USAGE REAL · TOKEN LEVERAGE SEPARATE</div>'
        + lines
        + "</div>"
    )


def hype_supply_capture_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    supply = c.get("supply") or {}
    vc = c.get("value_capture") or {}
    stake = c.get("staking") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    lines = (
        mline_tip(
            ICON_DROP,
            "Circulating",
            "Show both",
            f"CG {supply.get('cg_circulating_pct'):.1f}% · HL {supply.get('hl_circulating_pct'):.1f}%",
            evidence_tip_html(
                name="CIRCULATING MINORITY",
                read="DEFINITION GAP LOCKED",
                rows=[
                    ("CG", f"{_fmt_n(supply.get('cg_circulating'))} ({supply.get('cg_circulating_pct'):.1f}%)"),
                    ("Hyperliquid", f"{_fmt_n(supply.get('hl_circulating'))} ({supply.get('hl_circulating_pct'):.1f}%)"),
                    ("HL formula", str(supply.get("hl_formula"))),
                    ("futureEmissions", _fmt_n(supply.get("future_emissions"))),
                    ("HyperLabs NCU", _fmt_n(supply.get("hyperlabs_ncu"))),
                    ("3/6/12m", "UNKNOWN"),
                ],
                note="Never average. Never pick one. Do not invent 9.92M/month.",
                source=SRC,
                source_url=HL_INFO,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_CIRCLES,
            "Assistance Fund",
            "Buybacks real",
            "BUYBACKS REAL · BURN UNRESOLVED",
            evidence_tip_html(
                name="AF BUYBACK vs BURN",
                read=str(vc.get("production_wording") or ""),
                rows=[
                    ("Inventory", _fmt_n(vc.get("af_inventory"))),
                    ("Circ exclusion", "KNOWN"),
                    ("Total-supply burn", "CONFLICT"),
                ],
                note="AF inventory is not destroyed supply. Buybacks are real; total-supply burn is CONFLICT.",
                source=SRC,
                source_url=FEES_DOCS,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_NODES,
            "Stake / ownership",
            "Name ≠ ownership",
            "CONC. UNKNOWN",
            evidence_tip_html(
                name="STAKE / CONCENTRATION",
                read="PROTOCOL/SYSTEM INVENTORY PARTIAL",
                rows=[
                    ("Total stake", _fmt_n(stake.get("total_stake_hype"))),
                    ("Foundation-named vals", _fmt_n(stake.get("foundation_named_stake"))),
                    ("Of that: HyperLabs", _fmt_n(stake.get("hyperlabs_to_foundation_vals"))),
                    ("Of that: Foundation wallet", _fmt_n(stake.get("foundation_wallet_to_foundation_vals"))),
                    ("Other delegators", _fmt_n(stake.get("other_delegators"))),
                ],
                note=str(stake.get("note") or ""),
                source=SRC,
                source_url=HL_INFO,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-muted",
        )
    )
    return (
        '<div class="band band-timing">'
        "<h4>Supply / capture</h4>"
        '<div class="band-status c-orange">CIRCULATING MINORITY · BURN UNRESOLVED</div>'
        + lines
        + "</div>"
    )


def render_hype_evidence_cards(intel: dict[str, Any]) -> str:
    from lib.v3.forensic_cards import evidence_card, evidence_section

    c = _s1(intel)
    vc = c.get("value_capture") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    cards = [
        evidence_card(
            title="Venue fees",
            read="FEES LARGE · DECELERATING",
            copy="Large perp fees. Decelerating vs own recent month — not dead.",
            tone="green",
            status="KNOWN",
            kpis=[("Fees", "LARGE"), ("Vs own month", "DECELERATING")],
            tip_rows=[("Read", "Large perp fees. Decelerating vs own recent month — not dead.")],
            source=SRC,
            as_of=as_of,
            note="Protocol fees ≠ token-holder yield.",
        ),
        evidence_card(
            title="AF buybacks",
            read="BUYBACKS REAL · NOT ORGANIC DEMAND",
            copy="Fee-funded HYPE purchases. Inventory ~46.4M. Not organic demand.",
            tone="orange",
            status="KNOWN",
            kpis=[("Inventory", _fmt_n(vc.get("af_inventory"))), ("Organic demand", "NO")],
            tip_rows=[
                ("Inventory", _fmt_n(vc.get("af_inventory"))),
                ("Circ exclusion", "KNOWN"),
                ("Total-supply burn", "CONFLICT"),
            ],
            source=SRC,
            source_url=FEES_DOCS,
            as_of=as_of,
            note="AF inventory is not destroyed supply.",
        ),
        evidence_card(
            title="Circ split",
            read="DEFINITION GAP LOCKED",
            copy="CG 22.2% · HL 29.9%. Never average. Never pick one.",
            tone="orange",
            status="CONFLICT",
            kpis=[("CG", "22.2%"), ("HL", "29.9%")],
            tip_rows=[
                ("CG", "22.2%"),
                ("HL", "29.9%"),
                ("Rule", "Never average. Never pick one."),
            ],
            source=SRC,
            source_url=HL_INFO,
            as_of=as_of,
            note="Show both circulating definitions.",
        ),
        evidence_card(
            title="Burn accounting",
            read="DOCS SAY BURNED · TOTAL SUPPLY ~999M",
            copy="AF inventory is not destroyed supply.",
            tone="orange",
            status="CONFLICT",
            kpis=[("totalSupply", "~999M"), ("AF inventory", "NOT BURNED")],
            tip_rows=[
                ("Docs", "say burned"),
                ("totalSupply", "~999M"),
                ("AF inventory", "not destroyed supply"),
            ],
            source=SRC,
            source_url=FEES_DOCS,
            as_of=as_of,
            note="Buybacks are real; total-supply burn is CONFLICT.",
        ),
        evidence_card(
            title="3/6/12m unlocks",
            read="UNLOCK CADENCE UNKNOWN",
            copy="Contributor inventory still ~241M in NCU. No 9.92M/month.",
            tone="muted",
            status="UNKNOWN",
            kpis=[("3/6/12m", "UNKNOWN"), ("HyperLabs NCU", "~241M")],
            tip_rows=[
                ("3/6/12m", "UNKNOWN"),
                ("Contributor NCU", "~241M"),
                ("Invented monthly", "Do not use 9.92M/month"),
            ],
            source=SRC,
            as_of=as_of,
            note="Do not invent 9.92M/month.",
        ),
        evidence_card(
            title="Owners / MM / buyers",
            read="DISCRETIONARY CONC. UNKNOWN",
            copy="Discretionary concentration UNKNOWN. MM UNKNOWN, not zero.",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Discretionary conc.", "UNKNOWN"), ("MM", "UNKNOWN")],
            tip_rows=[
                ("Discretionary concentration", "UNKNOWN"),
                ("MM", "UNKNOWN, not zero"),
            ],
            source=SRC,
            as_of=as_of,
            note="System inventory is not discretionary concentration.",
        ),
    ]
    return evidence_section(
        cards,
        note="Compact conclusions first. Venue, supply and AF detail stay in tips underneath.",
    )


def render_hype_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">'
        "Hyperliquid is successful — how much of that success actually reaches HYPE, "
        "and how much future supply still has to be absorbed? "
        "Platform usage is not HYPE-token speculation. Protocol fees are not token-holder yield."
        "</p></div><div class=\"split\">"
        + hype_platform_band(intel)
        + hype_supply_capture_band(intel)
        + "</div></section>"
    )
    return (
        split
        + warning_stack_html(intel)
        + change_mind_section(intel, slug="hype")
        + reality_check_section(intel)
        + render_hype_evidence_cards(intel)
    )


def build_hype_v3_from_packs(report_date: str, v4_report: dict | None = None) -> dict[str, Any]:
    stage1 = load_hype_canonical()
    price = stage1.get("price_structure") or {}
    stance = hype_current_stance()
    assert stance["headline"] == STANCE_HEADLINE
    now_usd = price.get("now_usd")
    supply = stage1.get("supply") or {}
    doc: dict[str, Any] = {
        "meta": {
            "schema": "hype-v3",
            "slug": "hype",
            "report_date": report_date,
            "generated_at": now_iso(),
            "version": "stage1-v1",
            "v4_report_date": (v4_report or {}).get("report_date"),
        },
        "hero": {
            "asset": "HYPE",
            "price_usd": now_usd,
            "price_display": _price_disp(now_usd),
            "ath_display": f"${price.get('ath_usd')}",
            "drawdown_pct": price.get("drawdown_pct"),
            "price_as_of": (stage1.get("meta") or {}).get("fetched_at_utc"),
            "thesis": (
                "Hyperliquid success is not automatic HYPE-holder success. "
                "Show both circulating definitions. AF inventory is not destroyed supply."
            ),
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
            "v3_stance": stance["headline"],
            "v3_stance_note": stance["summary"],
            "confidence": stance["confidence"],
            "data_completeness": (
                f"Circ split locked CG {supply.get('cg_circulating_pct'):.1f}% / "
                f"HL {supply.get('hl_circulating_pct'):.1f}%. "
                "AF buybacks KNOWN. Total-supply burn CONFLICT. 3/6/12m UNKNOWN."
            ),
        },
        "triad": {
            "lifecycle": {
                "display": "Near-term RS soft",
                "detail": "30d lags BTC/SOL. 90d/180d recovery is not current leadership.",
            },
            "project_health": {
                "display": "Usage and fees real",
                "detail": "Large venue; fees decelerating vs own month. AF buybacks real.",
            },
            "market_timing": {
                "display": "Circulating minority",
                "detail": "CG 22.2% · HL 29.9%. Definition gap locked.",
            },
        },
        "stage1": stage1,
    }
    doc["asset_top"] = build_hype_asset_top(doc)
    doc["warning_stack"] = build_hype_warning_stack(doc)
    doc["what_would_change_mind"] = build_hype_change_mind(doc)
    doc["reality_check"] = build_hype_reality_check(doc)
    return doc


def write_hype_v3(out_dir: Path | None = None) -> dict[str, Any]:
    report_date = "2026-08-13"
    doc = build_hype_v3_from_packs(report_date)
    payload = json.dumps(doc, indent=2)
    out_dir = out_dir or (ROOT / "reports" / report_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "hype-v3.json").write_text(payload, encoding="utf-8")
    (ROOT / "hype-v3.json").write_text(payload, encoding="utf-8")
    return doc
