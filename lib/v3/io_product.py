"""IO V3 product layer — Stage-1 packs → asset_top, warnings, WCM, RC, HTML."""

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
from lib.v3.current_stance import io_current_stance
from lib.v3.fields import category_state, pack_risk_confirmation, now_iso
from lib.v3.sma_trend import technical_trend_category
from lib.v3.io_stage1_loader import load_io_canonical
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


def _fmt_usd(v: Any) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(n) >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"${n:,.0f}"
    return f"${n:,.2f}"


def _fmt_ratio(v: Any) -> str:
    try:
        return f"{float(v):.2f}×"
    except (TypeError, ValueError):
        return "—"


def _fmt_pct_raw(v: Any) -> str:
    try:
        return f"{float(v):.0f}%"
    except (TypeError, ValueError):
        return "—"


def _s1(intel: dict) -> dict:
    return intel.get("stage1") or {}


def build_io_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    c = doc.get("stage1") or {}
    price = c.get("price_structure") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    rs_render = c.get("rs_vs_render_pp") or {}
    deriv = c.get("derivatives") or {}
    net = c.get("network") or {}
    vc = c.get("value_capture") or {}
    supply = c.get("supply") or {}
    flow = c.get("capital_flow") or {}
    mm = c.get("mm") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc") or now_iso()
    now_usd = price.get("now_usd")
    price_disp = f"~${now_usd:,.3f}".rstrip("0").rstrip(".") if isinstance(now_usd, (int, float)) else "—"
    if isinstance(now_usd, (int, float)) and now_usd < 1:
        price_disp = f"~${now_usd:.3f}"
    rets = price.get("returns_pct") or {}

    top = empty_asset_top("IO", price_disp)
    top["price_as_of"] = as_of

    market_signals = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state="MIXED · NEAR-TERM LAGGING",
            display="MIXED · NEAR-TERM LAGGING",
            light=LIGHT_ORANGE,
            meaning=meaning("io", price.get("drawdown_pct")),
            evidence=(
                f"IO {price_disp} · ATH ${price.get('ath_usd')} · "
                f"drawdown {_fmt_pct(price.get('drawdown_pct'))} · "
                f"spot 7d {_fmt_pct(rets.get('7'))} · 30d {_fmt_pct(rets.get('30'))} · "
                f"90d {_fmt_pct(rets.get('90'))} · 180d {_fmt_pct(rets.get('180'))}. "
                "Do not flatten into always-weak — 180d recovery from April low is real."
            ),
            source="CoinGecko + Binance spot IOUSDT",
            source_url="https://www.coingecko.com/en/coins/io",
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
            source="Binance spot IO vs BTC",
            source_url="https://www.binance.com/en/trade/IO_USDT",
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
            meaning="Priority RS — separate Solana beta from compute beta.",
            evidence=(
                f"7d {_fmt_pp(rs_sol.get('7'))} · 30d {_fmt_pp(rs_sol.get('30'))} · "
                f"90d {_fmt_pp(rs_sol.get('90'))} · 180d {_fmt_pp(rs_sol.get('180'))}."
            ),
            source="Binance spot IO vs SOL",
            source_url="https://www.binance.com/en/trade/IO_USDT",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_render",
            label="vs RENDER",
            state="LAGGING 30d · AHEAD 90d/180d",
            display="MIXED VS RENDER",
            light=LIGHT_ORANGE,
            meaning="Priority RS — decentralized-compute / AI peer context.",
            evidence=(
                f"7d {_fmt_pp(rs_render.get('7'))} · 30d {_fmt_pp(rs_render.get('30'))} · "
                f"90d {_fmt_pp(rs_render.get('90'))} · 180d {_fmt_pp(rs_render.get('180'))}."
            ),
            source="Binance spot IO vs RENDER",
            source_url="https://www.binance.com/en/trade/IO_USDT",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["market_structure"]["signals"] = market_signals
    top["groups"]["market_structure"]["group_state"] = "MIXED · NEAR-TERM LAGGING"
    top["groups"]["market_structure"]["group_light"] = LIGHT_ORANGE
    top["groups"]["market_structure"]["title"] = "Price / Market Structure"

    net_signals = [
        signal(
            signal_id="network_earnings",
            label="Network Earnings",
            state="NETWORK EARNINGS REAL",
            display="EARNINGS REAL",
            light=LIGHT_GREEN,
            meaning="Public Explorer API — cumulative and recent daily earnings.",
            evidence=(
                f"Cumulative ~{_fmt_usd(net.get('total_earnings_usd'))} · "
                f"recent ~{_fmt_usd(net.get('avg_daily_earn_30d'))}/day (30d avg) · "
                f"May {_fmt_usd(net.get('monthly_may'))} · June {_fmt_usd(net.get('monthly_june'))} · "
                f"July {_fmt_usd(net.get('monthly_july'))}. Read: {net.get('demand_read')}."
            ),
            source="io.net Explorer API",
            source_url=net.get("source_url"),
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="utilization",
            label="Utilized Compute",
            state="UTILIZATION MODEST",
            display="MODEST VS INVENTORY",
            light=LIGHT_ORANGE,
            meaning="Inventory/device count ≠ utilized compute.",
            evidence=(
                f"Running clusters ~{net.get('running_clusters')} · "
                f"compute hours cum ~{_fmt_m(net.get('total_compute_hours'))} · "
                f"inventory total ~{net.get('inventory_total')}. "
                f"{net.get('inventory_note')}"
            ),
            unknown="API active/passive not proven hired/idle.",
            source="io.net Explorer API",
            source_url=net.get("explorer_url"),
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="spot_vs_leverage",
            label="Spot vs Leverage",
            state=deriv.get("read") or "LEVERAGE-LED VS SPOT",
            display="LEVERAGE-LED · OI ELEVATED",
            light=LIGHT_ORANGE,
            meaning="Binance venue structure — OI rising ≠ bearish.",
            evidence=(
                f"Spot 24h ~{_fmt_usd(deriv.get('spot_quote_vol_24h'))} · "
                f"perp 24h ~{_fmt_usd(deriv.get('fut_quote_vol_24h'))} · "
                f"fut/spot ~{_fmt_ratio(deriv.get('fut_spot_ratio'))} · "
                f"OI ~{_fmt_usd(deriv.get('oi_notional_usd'))} · "
                f"~{_fmt_pct_raw(deriv.get('oi_vs_30d_max_pct'))} of 30d max · "
                f"funding {deriv.get('funding_latest')}. {deriv.get('note','')}"
            ),
            source="Binance spot + USDT-M IOUSDT",
            source_url=deriv.get("source_url"),
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["capital_flow"]["signals"] = net_signals
    top["groups"]["capital_flow"]["group_state"] = net.get("read") or "NETWORK EARNINGS REAL · UTILIZATION MODEST"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_ORANGE
    top["groups"]["capital_flow"]["title"] = "Network / Product Demand"

    supply_signals = [
        signal(
            signal_id="token_capture",
            label="Token Value Capture",
            state=vc.get("read") or "MECHANISM EXISTS · SCALE EARLY",
            display="MECHANISM EXISTS · SCALE EARLY",
            light=LIGHT_ORANGE,
            meaning="Do not say token value capture is proven at scale.",
            evidence=(
                f"IO not required for payment · IO fee {vc.get('io_payment_fee')} vs USDC "
                f"{vc.get('usdc_payment_fee')} · supplier staking required · "
                f"{vc.get('ide_burn_design')} · measured burn = {vc.get('measured_burn_status')} · "
                f"% payments in IO = {vc.get('io_payment_share_status')}."
            ),
            unknown="Measured burn scale and IO payment share UNKNOWN.",
            source="io.net docs + IDE",
            source_url=vc.get("ide_url"),
            as_of=as_of,
            freshness="docs",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="supply_pressure",
            label="Supply Pressure",
            state="MATERIAL",
            display="MATERIAL",
            light=LIGHT_ORANGE,
            meaning=supply.get("display_rule") or "",
            evidence=(
                f"Max {_fmt_m(supply.get('max_supply'))} · circulating ~{_fmt_m(supply.get('circulating_cg'))} "
                f"(~{_fmt_pct_raw(supply.get('circulating_pct_of_max'))}) · {supply.get('emissions_design')}. "
                f"Exact next unlock sizes = {supply.get('next_unlock_first_party_status')}."
            ),
            unknown="Exact next first-party unlock size unknown.",
            source="io.net docs + CoinGecko",
            source_url="https://io.net/docs/guides/coin/io-tokenomics",
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
            meaning="CEX-heavy market — DEX sample not representative.",
            evidence=(
                f"DEX top-10 txn counts (bounded): buys {flow.get('dex_buys_24h')} / "
                f"sells {flow.get('dex_sells_24h')} · vol ~{_fmt_usd(flow.get('dex_vol_24h'))}. "
                f"{flow.get('dex_note')}"
            ),
            unknown="CEX and wallet identity UNKNOWN.",
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
            meaning="TRANSFER ≠ SALE. CEX DEPOSIT ≠ SALE.",
            evidence="No labelled seller identity. Do not infer from DEX txn counts.",
            unknown="Seller identity unresolved.",
            source="Stage-1 capital-flow",
            as_of=as_of,
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="mm_otc",
            label="MM / OTC",
            state=mm.get("read") or "NO VERIFIED MATERIAL MM / OTC IO INVENTORY THIS PASS",
            display="NO MATERIAL PRINT",
            light=LIGHT_UNKNOWN,
            meaning=mm.get("note") or "Absence is not a warning.",
            evidence=f"Shared MM registry Solana wallets with IO balance >0: {mm.get('hits', 0)}.",
            source="Shared MM registry scan",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="UNKNOWN",
        ),
    ]
    top["groups"]["project_supply"]["signals"] = supply_signals
    top["groups"]["project_supply"]["group_state"] = vc.get("group_read") or "CAPTURE EARLY · SUPPLY PRESSURE MATERIAL"
    top["groups"]["project_supply"]["group_light"] = LIGHT_ORANGE
    top["groups"]["project_supply"]["title"] = "Token Value Capture / Supply"

    stance = io_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "summary": stance["summary"],
        "confidence": stance["confidence"],
    }
    return enrich_tooltips(top)


def build_io_warning_stack(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    net = c.get("network") or {}
    deriv = c.get("derivatives") or {}
    supply = c.get("supply") or {}
    cats = [
        technical_trend_category("io"),
        category_state(
            "network_earnings",
            "NETWORK EARNINGS",
            "CLEAR",
            detail=(
                f"Public Explorer API — cumulative ~{_fmt_usd(net.get('total_earnings_usd'))} · "
                f"July ~{_fmt_usd(net.get('monthly_july'))}. Supplier earnings. Not protocol take."
            ),
            summary=(
                f"~{_fmt_usd(net.get('total_earnings_usd'))} cum · "
                f"July ~${float(net.get('monthly_july') or 0)/1_000_000:.2f}M"
                if isinstance(net.get("monthly_july"), (int, float))
                else f"~{_fmt_usd(net.get('total_earnings_usd'))} cum · July ~{_fmt_usd(net.get('monthly_july'))}"
            ),
        ),
        category_state(
            "token_capture",
            "TOKEN CAPTURE",
            "PARTIAL",
            detail=(
                "IDE/burn design documented; measured burns and IO payment share UNKNOWN. "
                "LinkedIn 1.1M is a claim, not explorer-locked."
            ),
            summary="IDE designed · measured burn unverified",
        ),
        category_state(
            "supply",
            "SUPPLY",
            "PARTIAL",
            detail=(
                f"Circulating ~{_fmt_pct_raw(supply.get('circulating_pct_of_max'))} of 800M max. "
                "Remaining ~300M emissions (~20y stock). No first-party 3/6/12m vest."
            ),
            summary="~48% circ · 300M emissions left",
        ),
        category_state(
            "leverage",
            "LEVERAGE",
            "PARTIAL",
            detail=(
                f"Binance fut/spot ~{_fmt_ratio(deriv.get('fut_spot_ratio'))} · "
                f"OI ~{_fmt_usd(deriv.get('oi_notional_usd'))} · funding quiet. "
                "Leverage present. OI rising ≠ crash."
            ),
            summary=f"Binance fut/spot ~{_fmt_ratio(deriv.get('fut_spot_ratio'))} · OI elevated",
        ),
    ]
    return pack_risk_confirmation(cats, "IO Stage-1 completion packs")


def build_io_change_mind(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    vc = c.get("value_capture") or {}
    net = c.get("network") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    constructive = [
        condition(
            condition_id="ide_burns_material",
            title="Verified persistent IO burns/buybacks",
            summary="Material-scale IDE burns or buybacks show compute earnings converting into IO float reduction.",
            status="NO",
            interpretation=f"Measured burn = {vc.get('measured_burn_status')}. Earnings are real; token sink is not measured.",
            evidence_rows=[
                ("Measured burn", vc.get("measured_burn_status") or "UNKNOWN"),
                ("IDE design", "Documented"),
            ],
            source="Stage-1 value capture",
            source_url=vc.get("ide_url"),
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="UNKNOWN",
            icon="up",
        ),
        condition(
            condition_id="earnings_fund_io_demand",
            title="Earnings fund observable IO demand",
            summary="Network earnings stop softening and show up as persistent IO absorption, not just supplier payouts.",
            status="NO",
            interpretation="July earnings softer than May; no measured IO buy/burn series from that revenue.",
            evidence_rows=[
                ("July earnings", _fmt_usd(net.get("monthly_july"))),
                ("May earnings", _fmt_usd(net.get("monthly_may"))),
                ("Demand read", net.get("demand_read") or "REAL DEMAND · RECENT EARNINGS SOFTER"),
            ],
            source="Explorer API + Stage-1",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
    ]
    defensive = [
        condition(
            condition_id="earnings_soften_capture_unknown",
            title="Earnings soften while IO is not absorbed",
            summary="Network earnings keep softening while IO burns/buybacks stay unmeasured — usage does not bid the token.",
            status="PARTIAL",
            interpretation=net.get("demand_read") or "REAL DEMAND · RECENT EARNINGS SOFTER",
            evidence_rows=[
                ("July earnings", _fmt_usd(net.get("monthly_july"))),
                ("May earnings", _fmt_usd(net.get("monthly_may"))),
                ("Measured burn", vc.get("measured_burn_status") or "UNKNOWN"),
            ],
            source="Explorer API + Stage-1",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
        condition(
            condition_id="emissions_without_sink",
            title="Emissions continue without an IO sink",
            summary="Remaining ~300M emissions keep hitting float with no verified burn/buyback offset.",
            status="PARTIAL",
            interpretation="Supply pressure MATERIAL; measured token capture still UNKNOWN.",
            evidence_rows=[("Supply pressure", "MATERIAL"), ("Measured burn", "UNKNOWN")],
            source="Tokenomics docs",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
    ]
    return pack_change_mind(constructive, defensive)


def build_io_reality_check(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    net = c.get("network") or {}
    supply = c.get("supply") or {}
    vc = c.get("value_capture") or {}
    deriv = c.get("derivatives") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    rets = price.get("returns_pct") or {}

    rc = empty_reality_check()
    rc["priority_headline"] = "Real compute earnings do not automatically create strong IO token demand."
    rc["known"] = [
        rc_item(
            item_id="price_ath",
            title=rc_title("io", price.get("drawdown_pct")),
            summary=f"~${price.get('now_usd')} · {_fmt_pct(price.get('drawdown_pct'))} from ATH ${price.get('ath_usd')}",
            interpretation=meaning("io", price.get("drawdown_pct")),
            priority="HIGH",
            source="CoinGecko",
            source_url="https://www.coingecko.com/en/coins/io",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
        ),
        rc_item(
            item_id="rs_mixed",
            title="Near-term lag vs SOL/BTC; 180d recovery real",
            summary=(
                f"SOL 30d {_fmt_pp(rs_sol.get('30'))} · BTC 30d {_fmt_pp(rs_btc.get('30'))} · "
                f"180d return {_fmt_pct(rets.get('180'))}"
            ),
            interpretation="Do not flatten into always-weak.",
            priority="HIGH",
            source="Binance spot",
            as_of=as_of,
            confidence="HIGH",
        ),
        rc_item(
            item_id="earnings",
            title="First-party network earnings + compute hours",
            summary=(
                f"Cum {_fmt_usd(net.get('total_earnings_usd'))} · "
                f"~{_fmt_usd(net.get('avg_daily_earn_30d'))}/day · "
                f"clusters {net.get('running_clusters')} · "
                f"hours {_fmt_m(net.get('total_compute_hours'))}"
            ),
            priority="HIGH",
            source="io.net Explorer API",
            source_url=net.get("source_url"),
            as_of=as_of,
            confidence="HIGH",
        ),
        rc_item(
            item_id="supply",
            title="~48% circulating of 800M max",
            summary=f"Circ ~{_fmt_m(supply.get('circulating_cg'))} · {supply.get('emissions_design')}",
            priority="HIGH",
            source="CoinGecko + docs",
            as_of=as_of,
            confidence="HIGH",
        ),
        rc_item(
            item_id="capture_design",
            title="Payment incentive + staking + IDE burn design",
            summary=vc.get("read") or "MECHANISM EXISTS · SCALE EARLY",
            priority="MEDIUM",
            source="io.net docs",
            source_url=vc.get("doc_url"),
            as_of=as_of,
            confidence="HIGH",
        ),
        rc_item(
            item_id="leverage",
            title="Binance leverage-led vs spot; OI elevated",
            summary=(
                f"fut/spot ~{_fmt_ratio(deriv.get('fut_spot_ratio'))} · "
                f"OI ~{_fmt_usd(deriv.get('oi_notional_usd'))} · funding quiet"
            ),
            interpretation="OI rising ≠ bearish.",
            priority="MEDIUM",
            source="Binance",
            as_of=as_of,
            confidence="HIGH",
        ),
    ]
    rc["suggests"] = [
        rc_item(
            item_id="s1",
            title="Demand can be real while token is weak",
            summary="Earnings tape stronger than proven scarcity tape.",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="s2",
            title="Price fits SOL beta, overhang, leverage",
            summary="Not proven as an earnings-breakout token move.",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="s3",
            title="IDE capture better; scale still early",
            summary="Burns/IO-settled share unmeasured.",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="s4",
            title="Inventory overstates demand if misread",
            summary="Use earnings / hours / clusters.",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="s5",
            title="OI elevated vs history; funding quiet",
            summary="Not a clear squeeze-top signal alone.",
            epistemic_status="INFERENCE",
        ),
    ]
    rc["unknowns"] = [
        rc_item(item_id="buyers", title="Wallet-level who is buying / selling", summary="CEX-dominated; no identity sample.", epistemic_status="UNKNOWN"),
        rc_item(item_id="burns", title="Measured IDE burn / buyback volumes", summary="Unproven at scale.", epistemic_status="UNKNOWN"),
        rc_item(item_id="pay_share", title="% of customer payments settled in IO", summary="Not disclosed in aggregate.", epistemic_status="UNKNOWN"),
        rc_item(item_id="unlock", title="Exact next first-party unlock sizes", summary="No machine table this pass.", epistemic_status="UNKNOWN"),
        rc_item(item_id="hired", title="Hired vs idle inventory mapping", summary="API labels only.", epistemic_status="UNKNOWN"),
        rc_item(item_id="mm", title="Verified MM/OTC IO inventory events", summary="Registry: no material hit.", epistemic_status="UNKNOWN"),
    ]
    return rc


def io_health_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    net = c.get("network") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    lines = (
        mline_tip(
            ICON_NODES,
            "Cumulative / recent earnings",
            "Explorer API",
            f"{_fmt_usd(net.get('total_earnings_usd'))} · {_fmt_usd(net.get('avg_daily_earn_30d'))}/d",
            evidence_tip_html(
                name="NETWORK EARNINGS",
                read="EARNINGS REAL",
                rows=[
                    ("Cumulative", _fmt_usd(net.get("total_earnings_usd"))),
                    ("30d avg/day", _fmt_usd(net.get("avg_daily_earn_30d"))),
                    ("May / Jun / Jul", f"{_fmt_usd(net.get('monthly_may'))} / {_fmt_usd(net.get('monthly_june'))} / {_fmt_usd(net.get('monthly_july'))}"),
                    ("Running clusters", str(net.get("running_clusters"))),
                ],
                note="Inventory/device count ≠ utilized compute.",
                source="io.net Explorer API",
                source_url=net.get("source_url"),
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_GRID,
            "Commercial read",
            "Network / product",
            "EARNINGS REAL",
            evidence_tip_html(
                name="NETWORK / COMMERCIAL DEMAND",
                read="EARNINGS REAL",
                rows=[("Core lesson", "Real compute earnings do not automatically create strong IO token demand.")],
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
        "<h4>Network / commercial demand</h4>"
        '<div class="band-status c-green">EARNINGS REAL</div>'
        + lines
        + "</div>"
    )


def io_token_band(intel: dict[str, Any]) -> str:
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
            "Burn / buy-pressure",
            "SCALE EARLY",
            evidence_tip_html(
                name="TOKEN CAPTURE",
                read="CAPTURE EARLY",
                rows=[
                    ("Mechanism", "Documented (IDE / fees / staking)"),
                    ("Measured burns", "UNKNOWN"),
                    ("Supply pressure", supply.get("pressure_read") or "MATERIAL"),
                ],
                note="MECHANISM EXISTS · SCALE EARLY",
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
                name="TOKEN / MARKET CONFIRMATION",
                read="CAPTURE EARLY · SUPPLY MATERIAL · RS WEAK",
                rows=[
                    ("IO/SOL 7d", _fmt_pp(rs_sol.get("7"))),
                    ("IO/SOL 30d", _fmt_pp(rs_sol.get("30"))),
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
        '<div class="band band-token">'
        "<h4>Token / market confirmation</h4>"
        '<div class="band-status c-orange">CAPTURE EARLY · SUPPLY MATERIAL · RS WEAK</div>'
        + ddbar
        + lines
        + "</div>"
    )


def render_io_evidence_cards(intel: dict[str, Any]) -> str:
    from lib.v3.forensic_cards import evidence_card, evidence_section

    c = _s1(intel)
    price = c.get("price_structure") or {}
    net = c.get("network") or {}
    vc = c.get("value_capture") or {}
    supply = c.get("supply") or {}
    deriv = c.get("derivatives") or {}
    flow = c.get("capital_flow") or {}
    mm = c.get("mm") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    cards = [
        evidence_card(
            title="Price / ATH",
            read=f"{_fmt_pct(price.get('drawdown_pct'))} from ATH",
            copy=meaning("io", price.get("drawdown_pct")),
            tone="orange",
            status="KNOWN",
            kpis=[
                ("Now", f"~${price.get('now_usd')}"),
                ("ATH", f"${price.get('ath_usd')}"),
            ],
            tip_rows=[
                ("Now", f"~${price.get('now_usd')}"),
                ("Drawdown", _fmt_pct(price.get("drawdown_pct"))),
                ("ATH", f"${price.get('ath_usd')}"),
            ],
            source="Stage-1 price",
            as_of=as_of,
            note="Known price structure. Not a buy/sell call.",
        ),
        evidence_card(
            title="Network earnings",
            read="EARNINGS REAL",
            copy="Publicly queryable network earnings. Not protocol token capture.",
            tone="green",
            status="KNOWN",
            kpis=[
                ("Cumulative", _fmt_usd(net.get("total_earnings_usd"))),
                ("30d avg", f"{_fmt_usd(net.get('avg_daily_earn_30d'))}/d"),
            ],
            tip_rows=[
                ("Cumulative", _fmt_usd(net.get("total_earnings_usd"))),
                ("30d avg /d", _fmt_usd(net.get("avg_daily_earn_30d"))),
            ],
            source="io.net Explorer API",
            source_url=net.get("source_url"),
            as_of=as_of,
            note="Real compute earnings do not automatically create strong IO token demand.",
        ),
        evidence_card(
            title="Utilization",
            read="INVENTORY ≠ HIRED",
            copy="Running clusters and inventory are not the same as hired compute.",
            tone="orange",
            status="KNOWN",
            kpis=[
                ("Clusters", str(net.get("running_clusters"))),
                ("Inventory", str(net.get("inventory_total"))),
            ],
            tip_rows=[
                ("Running clusters", str(net.get("running_clusters"))),
                ("Inventory total", str(net.get("inventory_total"))),
            ],
            source="io.net Explorer API",
            source_url=net.get("source_url"),
            as_of=as_of,
            note="Inventory/device count ≠ utilized compute.",
        ),
        evidence_card(
            title="Value capture",
            read=vc.get("read") or "MECHANISM EXISTS · SCALE EARLY",
            copy="Documented mechanism. Measured burn/buy-pressure still unproven.",
            tone="orange",
            status="PARTIAL",
            kpis=[("Scale", "EARLY"), ("Measured burns", "UNKNOWN")],
            tip_rows=[
                ("Read", vc.get("read") or "MECHANISM EXISTS · SCALE EARLY"),
                ("Measured burns", "UNKNOWN"),
            ],
            source="Stage-1 value capture",
            as_of=as_of,
            note="MECHANISM EXISTS · SCALE EARLY",
        ),
        evidence_card(
            title="Supply",
            read="MATERIAL",
            copy="Circulating versus max remains a pressure fact, not a score.",
            tone="orange",
            status="PARTIAL",
            kpis=[
                ("CG circ", _fmt_m(supply.get("circulating_cg"))),
                ("Max", _fmt_m(supply.get("max_supply"))),
            ],
            tip_rows=[
                ("CG circ", _fmt_m(supply.get("circulating_cg"))),
                ("Max", _fmt_m(supply.get("max_supply"))),
                ("Pressure", "MATERIAL"),
            ],
            source="Stage-1 supply",
            as_of=as_of,
            note="Do not invent unlock cadence.",
        ),
        evidence_card(
            title="Leverage",
            read="FUT/SPOT OBSERVED",
            copy="Venue ratio and OI are prints, not automatic warnings.",
            tone="orange",
            status="KNOWN",
            kpis=[
                ("Fut/spot", f"~{_fmt_ratio(deriv.get('fut_spot_ratio'))}"),
                ("OI", _fmt_usd(deriv.get("oi_notional_usd"))),
            ],
            tip_rows=[
                ("Fut/spot", _fmt_ratio(deriv.get("fut_spot_ratio"))),
                ("OI", _fmt_usd(deriv.get("oi_notional_usd"))),
            ],
            source="Stage-1 derivatives",
            as_of=as_of,
            note="Leverage present ≠ bearish by itself.",
        ),
        evidence_card(
            title="Buyers / sellers",
            read="CEX-HEAVY · IDENTITY UNKNOWN",
            copy=f"{flow.get('who_buying')} / {flow.get('who_selling')} — who remains unresolved.",
            tone="muted",
            status="UNKNOWN",
            kpis=[
                ("Who buying", str(flow.get("who_buying") or "UNKNOWN")),
                ("Who selling", str(flow.get("who_selling") or "UNKNOWN")),
            ],
            tip_rows=[
                ("Who buying", str(flow.get("who_buying") or "UNKNOWN")),
                ("Who selling", str(flow.get("who_selling") or "UNKNOWN")),
            ],
            source="Stage-1 capital flow",
            as_of=as_of,
            note="CEX-heavy mix is not buyer quality.",
        ),
        evidence_card(
            title="MM / OTC",
            read="NO MATERIAL HIT",
            copy="Registry miss is not proof of zero market makers.",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Registry", "NO MATERIAL HIT")],
            tip_rows=[("Read", str(mm.get("read") or "NO MATERIAL PRINT"))],
            source="Stage-1 MM",
            as_of=as_of,
            note="UNKNOWN, not zero.",
        ),
    ]
    return evidence_section(
        cards,
        note="Compact conclusions first. Earnings, inventory and method stay in tips underneath.",
    )


def render_io_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">Real compute earnings do not automatically create strong IO token demand.</p>'
        "</div><div class=\"split\">"
        + io_health_band(intel)
        + io_token_band(intel)
        + "</div></section>"
    )
    return (
        split
        + warning_stack_html(intel)
        + change_mind_section(intel, slug="io")
        + reality_check_section(intel)
        + render_io_evidence_cards(intel)
    )


def build_io_v3_from_packs(report_date: str, v4_report: dict | None = None) -> dict[str, Any]:
    stage1 = load_io_canonical()
    price = stage1.get("price_structure") or {}
    stance = io_current_stance()
    now_usd = price.get("now_usd")
    if isinstance(now_usd, (int, float)):
        price_display = f"~${now_usd:.3f}"
    else:
        price_display = "—"
    doc: dict[str, Any] = {
        "meta": {
            "schema": "io-v3",
            "slug": "io",
            "report_date": report_date,
            "generated_at": now_iso(),
            "version": "stage1-v1",
            "v4_report_date": (v4_report or {}).get("report_date"),
        },
        "hero": {
            "asset": "IO",
            "price_usd": now_usd,
            "price_display": price_display,
            "ath_display": f"${price.get('ath_usd')}",
            "drawdown_pct": price.get("drawdown_pct"),
            "price_as_of": (stage1.get("meta") or {}).get("fetched_at_utc"),
            "thesis": "Real compute earnings do not automatically create strong IO token demand.",
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
            "v3_stance": stance["headline"],
            "v3_stance_note": stance["summary"],
            "confidence": stance["confidence"],
            "data_completeness": (
                "Stage-1 packs wired — buyers/sellers UNKNOWN; measured burns UNKNOWN; "
                "next unlock first-party UNKNOWN."
            ),
        },
        "triad": {
            "lifecycle": {
                "display": "Post-ATH / mixed",
                "detail": meaning("io", price.get("drawdown_pct")),
            },
            "project_health": {
                "display": "EARNINGS REAL",
                "detail": "Explorer earnings real; utilization modest vs inventory; capture early.",
            },
            "market_timing": {
                "display": "NEAR-TERM WEAK",
                "detail": "Lags SOL/BTC near-term; supply pressure material; leverage elevated.",
            },
        },
        "stage1": stage1,
    }
    doc["asset_top"] = build_io_asset_top(doc)
    doc["warning_stack"] = build_io_warning_stack(doc)
    doc["what_would_change_mind"] = build_io_change_mind(doc)
    doc["reality_check"] = build_io_reality_check(doc)
    return doc


def write_io_v3(out_dir: Path | None = None) -> dict[str, Any]:
    report_date = now_iso()[:10]
    doc = build_io_v3_from_packs(report_date)
    out_dir = out_dir or (REPORTS / report_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "io-v3.json").write_text(payload, encoding="utf-8")
    (ROOT / "io-v3.json").write_text(payload, encoding="utf-8")
    return doc
