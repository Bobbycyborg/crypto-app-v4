"""NOS V3 product layer — Stage-1 packs → asset_top, warnings, WCM, RC, HTML.

Central question: is real network usage translating into meaningful NOS token demand / value capture?
Keep NETWORK ACTIVITY · COMMERCIAL DEMAND · TOKEN VALUE CAPTURE as separate layers.
"""

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
from lib.v3.current_stance import nos_current_stance
from lib.v3.fields import category_state, pack_risk_confirmation, now_iso
from lib.v3.sma_trend import technical_trend_category
from lib.v3.nos_stage1_loader import SUPPLY_READ, STANCE_HEADLINE, load_nos_canonical
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

CG = "https://www.coingecko.com/en/coins/nosana"
IDX = "https://blockchain-indexer.k8s.prd.nos.ci"


def _s1(intel: dict[str, Any]) -> dict[str, Any]:
    return intel.get("stage1") or {}


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


def _fmt_n(v: Any) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"{n:,.0f}"
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


def build_nos_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    c = _s1(doc)
    price = c.get("price_structure") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    rs_render = c.get("rs_vs_render_pp") or {}
    net = c.get("network") or {}
    com = c.get("commercial_demand") or {}
    vc = c.get("value_capture") or {}
    supply = c.get("supply") or {}
    flow = c.get("capital_flow") or {}
    mm = c.get("mm") or {}
    deriv = c.get("derivatives") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc") or now_iso()
    now_usd = price.get("now_usd")
    if isinstance(now_usd, (int, float)):
        price_disp = f"~${now_usd:.3f}" if now_usd < 1 else f"~${now_usd:,.2f}"
    else:
        price_disp = "—"
    rets = price.get("returns_pct") or {}

    top = empty_asset_top("NOS", price_disp)
    top["price_as_of"] = as_of

    top["groups"]["market_structure"]["signals"] = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state="WEAK CONFIRMATION",
            display="WEAK VS NEAR WINDOWS",
            light=LIGHT_ORANGE,
            meaning=meaning("nos", price.get("drawdown_pct")),
            evidence=(
                f"NOS {price_disp} · ATH ${price.get('ath_usd')} · "
                f"drawdown {_fmt_pct(price.get('drawdown_pct'))} · mcap {_fmt_usd(price.get('mcap_usd'))}. "
                f"7d {_fmt_pct(rets.get('7'))} · 30d {_fmt_pct(rets.get('30'))} · "
                f"90d {_fmt_pct(rets.get('90'))} · 180d {_fmt_pct(rets.get('180'))}. "
                "Close was below SMA20/SMA50 in the research snapshot."
            ),
            source="CoinGecko + GeckoTerminal OHLCV",
            source_url=price.get("source_url_cg") or CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_sol",
            label="vs SOL",
            state="LAGGING 7d/30d/90d",
            display="LAGS SOL (PRIORITY)",
            light=LIGHT_ORANGE,
            meaning="Priority RS — separate Solana beta from compute story.",
            evidence=(
                f"7d {_fmt_pp(rs_sol.get('7'))} · 30d {_fmt_pp(rs_sol.get('30'))} · "
                f"90d {_fmt_pp(rs_sol.get('90'))} · 180d {_fmt_pp(rs_sol.get('180'))}."
            ),
            source="GT NOS + Binance SOL daily",
            source_url=price.get("source_url_gt"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_render",
            label="vs RENDER",
            state="AHEAD 30d/90d",
            display="AHEAD VS RENDER (CONTEXT)",
            light=LIGHT_GREEN,
            meaning="Compute-sector ratio context only — not a leadership claim.",
            evidence=(
                f"7d {_fmt_pp(rs_render.get('7'))} · 30d {_fmt_pp(rs_render.get('30'))} · "
                f"90d {_fmt_pp(rs_render.get('90'))} · 180d {_fmt_pp(rs_render.get('180'))}."
            ),
            source="GT NOS + Binance RENDER daily",
            source_url=price.get("source_url_gt"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_btc",
            label="vs BTC",
            state="LAGGING 7d–90d",
            display="LAGS BTC NEAR-TERM",
            light=LIGHT_ORANGE,
            meaning="Descriptive relative strength only.",
            evidence=(
                f"7d {_fmt_pp(rs_btc.get('7'))} · 30d {_fmt_pp(rs_btc.get('30'))} · "
                f"90d {_fmt_pp(rs_btc.get('90'))} · 180d {_fmt_pp(rs_btc.get('180'))}."
            ),
            source="GT NOS + Binance BTC daily",
            source_url=price.get("source_url_gt"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["market_structure"]["group_state"] = "MARKET CONFIRMATION WEAK"
    top["groups"]["market_structure"]["group_light"] = LIGHT_ORANGE
    top["groups"]["market_structure"]["title"] = "Price / Market Structure"

    top["groups"]["capital_flow"]["signals"] = [
        signal(
            signal_id="network_activity",
            label="Network Activity",
            state="NETWORK ACTIVE",
            display="JOBS + GPU-HOURS REAL",
            light=LIGHT_GREEN,
            meaning="First-party indexer. Cumulative completed jobs ≠ growth.",
            evidence=(
                f"Running ~{_fmt_n(net.get('jobs_running'))} · queued ~{_fmt_n(net.get('jobs_queued'))} · "
                f"GPU-hours ~{_fmt_n(net.get('gpu_hours_window_total'))} in ~31d window · "
                f"last 7d ~{_fmt_n(net.get('gpu_hours_last_7d'))} vs prior 7d ~{_fmt_n(net.get('gpu_hours_prev_7d'))} · "
                f"~30d jobs ~{_fmt_n(net.get('jobs_sum_last_30d'))} · "
                f"markets {net.get('markets_listed')}. "
                f"{net.get('window_note')}"
            ),
            source="Nosana blockchain-indexer",
            source_url=net.get("source_url") or f"{IDX}/jobs/count",
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="utilized_nodes",
            label="Nodes Running Jobs",
            state="~35 UTILIZED NOW",
            display="~35 WITH RUNNING JOBS",
            light=LIGHT_GREEN,
            meaning="Distinct nodes currently running ≥1 job — not registered / online / capacity.",
            evidence=(
                f"~{_fmt_n(net.get('distinct_nodes_with_running_jobs'))} distinct nodes with running jobs "
                f"(~{_fmt_n(net.get('running_jobs_sum'))} running job slots). "
                f"{net.get('node_terminology')}"
            ),
            unknown="Total online hosts / registered nodes / utilization % UNKNOWN.",
            source="Nosana indexer /jobs/running",
            source_url=f"{IDX}/jobs/running",
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="commercial_demand",
            label="Commercial Demand",
            state="PARTIAL",
            display="PARTIAL · BUYERS UNKNOWN",
            light=LIGHT_ORANGE,
            meaning="Throughput ≠ proven organic paying customers. Not revenue.",
            evidence=(
                f"Rails documented (credits / Stripe path / swap / NOS settlement). "
                f"Indexer host usdReward cum ~{_fmt_usd(net.get('jobs_stats_usd_reward_cum'))} "
                f"— not audited Nosana revenue. {com.get('usd_reward_field_note')}"
            ),
            unknown="; ".join(com.get("unknown") or []),
            source="Nosana docs + indexer",
            source_url=com.get("docs_url"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="buyers_sellers",
            label="Buyers / Sellers",
            state="SAMPLE ONLY",
            display="BOUNDED DEX SAMPLE",
            light=LIGHT_UNKNOWN,
            meaning="Small DEX sample ≠ market-wide accumulation/distribution.",
            evidence=(
                f"Sample n={flow.get('sample_n')}: buys {flow.get('sample_buys')} / "
                f"sells {flow.get('sample_sells')} · buy USD {_fmt_usd(flow.get('sample_buy_usd'))} · "
                f"sell USD {_fmt_usd(flow.get('sample_sell_usd'))}. {flow.get('dex_note')}"
            ),
            unknown="Buyer/seller identity beyond sample UNKNOWN.",
            source="GeckoTerminal trades sample",
            source_url=flow.get("source_url"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="mm_otc",
            label="MM / OTC",
            state=mm.get("read") or "NO MATERIAL HIT",
            display="NO MATERIAL REGISTRY HIT",
            light=LIGHT_UNKNOWN,
            meaning="MM interaction ≠ suppression. Absence ≠ no market makers exist.",
            evidence=mm.get("note") or "",
            source="Shared verified MM registry + Solana RPC",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["capital_flow"]["group_state"] = "NETWORK ACTIVE · DEMAND PARTIAL"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_GREEN
    top["groups"]["capital_flow"]["title"] = "Network / Commercial / Flow"

    top["groups"]["project_supply"]["signals"] = [
        signal(
            signal_id="value_capture",
            label="Value Capture",
            state="PARTIAL",
            display="RAIL REAL · AUTO DEMAND UNPROVEN",
            light=LIGHT_ORANGE,
            meaning="NOS on payment rail ≠ proven open-market buy from every job.",
            evidence=vc.get("core_interpretation") or "",
            unknown=(
                f"Usage→open-market NOS demand = {vc.get('usage_to_open_market_demand')}. "
                f"NNP-0001 implementation = {vc.get('nnp0001_implementation')}."
            ),
            source="Nosana docs + NNP-0001",
            source_url=vc.get("nnp_url"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="supply",
            label="Supply",
            state=SUPPLY_READ,
            display=SUPPLY_READ,
            light=LIGHT_UNKNOWN,
            meaning="Near-full float ≠ measured live emission pressure.",
            evidence=(
                f"Circ ~{_fmt_n(supply.get('circulating'))} / max {_fmt_n(supply.get('max_supply'))} · "
                f"staked ~{_fmt_n(supply.get('nos_staked'))} (~{supply.get('stakers')} stakers). "
                f"{supply.get('display_rule')}"
            ),
            unknown="Live inflation/emission rate · unlock schedule · NNP live status.",
            source="CoinGecko + Nosana indexer /stats",
            source_url=supply.get("source_url") or CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="holders",
            label="Holders",
            state="UNKNOWN",
            display="HOLDER CONCENTRATION UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="RPC largest-accounts failed. Staked NOS ≠ whale dump inventory.",
            evidence=flow.get("holders_note") or "Top-holder concentration UNKNOWN.",
            unknown="Treasury / CEX / liquid whale classification UNKNOWN.",
            source="Stage 1 ownership pass",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="spot_vs_leverage",
            label="Spot vs Leverage",
            state=deriv.get("read") or "NO MAJOR CEX PERP",
            display="NO MAJOR CEX PERP",
            light=LIGHT_UNKNOWN,
            meaning="Absence of perp data — do not invent OI/funding.",
            evidence=deriv.get("note") or "",
            source="Binance / Bybit / OKX scan (Stage 1)",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["project_supply"]["group_state"] = "VALUE CAPTURE PARTIAL · EMISSION UNKNOWN"
    top["groups"]["project_supply"]["group_light"] = LIGHT_ORANGE
    top["groups"]["project_supply"]["title"] = "Token Value Capture / Supply"

    stance = nos_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "explanation": stance["summary"],
        "directional_state": "DESCRIPTIVE",
        "confidence": stance["confidence"],
        "evidence_refs": [],
    }
    return enrich_tooltips(top)


def build_nos_warning_stack(intel: dict[str, Any]) -> dict[str, Any]:
    c = intel.get("stage1") or {}
    net = c.get("network") or {}
    cats = [
        technical_trend_category("nos"),
        category_state(
            "network_usage",
            "NETWORK USAGE",
            "CLEAR",
            detail=(
                f"Jobs + GPU-hours real. Running ~{_fmt_n(net.get('jobs_running'))} · "
                f"GPU-hours ~{_fmt_n(net.get('gpu_hours_window_total'))} in ~31d. "
                "Throughput is the confirmation. Do not use indexer $ as revenue."
            ),
            summary="Jobs + GPU-hours real",
        ),
        category_state(
            "token_capture",
            "TOKEN CAPTURE",
            "PARTIAL",
            detail=(
                "NOS rail documented; usage→open-market NOS demand UNKNOWN. "
                "Credits/Stripe unquantified. Do not use indexer usdReward as revenue."
            ),
            summary="NOS rail real · credits/Stripe unquantified",
        ),
        category_state(
            "live_emissions",
            "LIVE EMISSIONS",
            "UNKNOWN",
            detail="Near fully circulating — no large unissued overhang. NNP-0001 is not a live issuance rate.",
            summary="Current issuance UNKNOWN",
        ),
        category_state(
            "ownership",
            "OWNERSHIP",
            "UNKNOWN",
            detail="Top-holder RPC failed. Do not invent whale/treasury/CEX concentration.",
            summary="Holder concentration UNKNOWN",
        ),
    ]
    return pack_risk_confirmation(cats, "NOS Stage 1 evidence")


def build_nos_change_mind(intel: dict[str, Any]) -> dict[str, Any]:
    constructive = [
        condition(
            condition_id="paid_nos_settlement",
            title="Paid NOS settlement becomes material",
            summary="GPU-hours stay real and a disclosed organic/paid NOS share shows usage converting into token demand.",
            status="WATCH",
            interpretation="Jobs are real. Organic share and usage→market NOS are UNKNOWN. Hours alone do not bid NOS.",
            evidence_rows=[
                ("GPU-h ~31d", "~119k"),
                ("Organic share", "UNKNOWN"),
                ("Usage→market NOS", "UNKNOWN"),
            ],
            source="Nosana indexer + Stage 1",
            source_url=f"{IDX}/jobs/stats/timestamps-hours",
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
        condition(
            condition_id="nnp_sinks_live",
            title="Measured NNP lock/fee sink",
            summary="Live host Smin locks or fee→rebate flow is measured — designed tokenomics become an actual NOS sink.",
            status="WATCH",
            interpretation="Would move value capture from paper to observed. NNP-0001 is not a live rate.",
            evidence_rows=[
                ("NNP-0001 live", "UNKNOWN"),
                ("Measured fee flow", "UNKNOWN"),
            ],
            source="NNP-0001",
            source_url=(
                "https://github.com/nosana-ci/network-proposals/blob/main/nnp/NNP-0001-tokenomics.md"
            ),
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
    ]
    defensive = [
        condition(
            condition_id="hours_fade",
            title="GPU-hours fade",
            summary="Network hours/jobs roll over — the usage confirmation behind the token rail weakens.",
            status="WATCH",
            interpretation="~31d activity is stable-to-slightly-up. A fade would hit the 'network active' leg. Live emission rate stays UNKNOWN and is not the condition.",
            evidence_rows=[
                ("~31d activity", "Stable-to-slightly-up"),
                ("Live emission rate", "UNKNOWN — not used as a falsifier"),
            ],
            source="Stage 1",
            source_url=IDX + "/jobs/stats/timestamps-hours",
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
        condition(
            condition_id="credits_without_nos",
            title="Credits/fiat dominate without NOS conversion",
            summary="Credits/Stripe rails take the work without converting into NOS demand.",
            status="WATCH",
            interpretation="Would further weaken already-partial token value capture on a thin spot tape.",
            evidence_rows=[
                ("Conversion path", "Not fully traced"),
                ("Spot liquidity", "Thin"),
            ],
            source="Stage 1",
            source_url=CG,
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
    ]
    return pack_change_mind(constructive, defensive, schema_version=1)


def build_nos_reality_check(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    net = c.get("network") or {}
    price = c.get("price_structure") or {}
    rets = price.get("returns_pct") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    rc = empty_reality_check()
    rc["priority_headline"] = "NETWORK ALIVE ≠ TOKEN DEMAND PROVEN"
    rc["known"] = [
        rc_item(
            item_id="price",
            title=rc_title("nos", price.get("drawdown_pct")),
            summary=(
                f"NOS ~${price.get('now_usd')} · ~−97% from ATH · "
                f"7d {_fmt_pct(rets.get('7'))} · 30d {_fmt_pct(rets.get('30'))} · "
                f"90d {_fmt_pct(rets.get('90'))}."
            ),
            evidence_rows=[
                ("MCAP", _fmt_usd(price.get("mcap_usd"))),
                ("NOS/SOL 30d", _fmt_pp(rs_sol.get("30"))),
                ("180d", _fmt_pct(rets.get("180"))),
            ],
            interpretation=meaning("nos", price.get("drawdown_pct")),
            priority="HIGH",
            source="CoinGecko + GT OHLCV",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="network",
            title="Network operationally alive",
            summary=(
                f"~{_fmt_n(net.get('jobs_running'))} jobs · "
                f"~{_fmt_n(net.get('gpu_hours_window_total'))} GPU-h/~31d · "
                f"~{_fmt_n(net.get('distinct_nodes_with_running_jobs'))} nodes running."
            ),
            evidence_rows=[
                ("Completed (cum)", _fmt_n(net.get("jobs_completed_cumulative"))),
                ("~30d jobs", _fmt_n(net.get("jobs_sum_last_30d"))),
                ("Markets", str(net.get("markets_listed"))),
            ],
            interpretation="Cumulative completed ≠ growth. Visible window roughly stable-to-slightly-up.",
            priority="HIGH",
            source="Nosana indexer",
            source_url=net.get("source_url"),
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="rail",
            title="NOS payment rail documented",
            summary="NOS on jobs path; credits/Stripe/swap wrappers too.",
            evidence_rows=[("Capture read", "PARTIAL"), ("Buyback like RAY", "Not verified")],
            interpretation="Designed rail ≠ measured open-market demand from every job.",
            priority="HIGH",
            source="Nosana docs",
            source_url="https://learn.nosana.com/api/first-job.html",
            as_of="2026-08-12",
            freshness="docs",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="supply_float",
            title="Near fully circulating",
            summary=SUPPLY_READ,
            evidence_rows=[
                ("Circ / max", "~100M / 100M"),
                ("Staked", "~11.9M"),
                ("Live emissions", "UNKNOWN"),
            ],
            interpretation="No large unissued overhang. Emission pressure unresolved — not MATERIAL call.",
            priority="HIGH",
            source="CoinGecko + indexer",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="leverage_absent",
            title="No major CEX perp found",
            summary="Binance/Bybit/OKX NOS perp absent. Spot books thin.",
            evidence_rows=[("OI", "N/A"), ("Funding", "N/A")],
            interpretation="Do not manufacture a leverage view.",
            priority="MEDIUM",
            source="Stage 1 venue scan",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="mm",
            title="No material MM registry hit",
            summary="Wintermute/DWF scanned wallets: 0 NOS.",
            evidence_rows=[("Read", "No material inventory event")],
            interpretation="Absence ≠ no MMs. MM interaction ≠ suppression.",
            priority="MEDIUM",
            source="Shared MM registry",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    rc["suggests"] = [
        rc_item(
            item_id="s1",
            title="Usage real; token confirmation soft",
            summary="Alive network with weak near-term NOS/SOL confirmation.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s2",
            title="Three layers diverge",
            summary="Network activity > proven commercial mix > proven token market demand.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s3",
            title="Thin books amplify moves",
            summary="~$230k CG vol / thin DEX liq — small flows can move price.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s4",
            title="Capture weaker than RENDER BME",
            summary="NOS rail real; BME-like burn/buyback not verified.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s5",
            title="Emission-risk story, not unlock overhang",
            summary="Near-full float → live emissions still UNKNOWN.",
            epistemic_status="INTERPRETATION",
        ),
    ]
    rc["unknowns"] = [
        rc_item(item_id="u1", title="Top-holder / liquid-supply classification", summary="RPC failed.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u2", title="NNP-0001 on-chain completeness", summary="Proposal/vote site ≠ verified live sinks.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u3", title="Organic paid demand vs credits/incentives", summary="Mix unresolved.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u4", title="GPU-hours/jobs trend beyond ~31d", summary="Indexer window bounded.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u5", title="Utilization % / capacity denominator", summary="Need online capacity.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u6", title="Named commercial customers / payer concentration", summary="Not disclosed this pass.", epistemic_status="UNKNOWN"),
    ]
    return rc


def nos_network_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    net = c.get("network") or {}
    com = c.get("commercial_demand") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    lines = (
        mline_tip(
            ICON_NODES,
            "Jobs + GPU-hours",
            "First-party indexer",
            f"{_fmt_n(net.get('jobs_running'))} run · {_fmt_n(net.get('gpu_hours_window_total'))} h/~31d",
            evidence_tip_html(
                name="NETWORK ACTIVITY",
                read="NETWORK ACTIVE",
                rows=[
                    ("Running / queued", f"{_fmt_n(net.get('jobs_running'))} / {_fmt_n(net.get('jobs_queued'))}"),
                    ("GPU-h ~31d", _fmt_n(net.get("gpu_hours_window_total"))),
                    ("Last 7d / prior 7d", f"{_fmt_n(net.get('gpu_hours_last_7d'))} / {_fmt_n(net.get('gpu_hours_prev_7d'))}"),
                    ("Nodes with running jobs", _fmt_n(net.get("distinct_nodes_with_running_jobs"))),
                    ("Completed (cum)", _fmt_n(net.get("jobs_completed_cumulative"))),
                ],
                note="Cumulative completed ≠ growth. ~35 = utilized now — not registered/online/capacity.",
                source="Nosana blockchain-indexer",
                source_url=net.get("source_url"),
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_GRID,
            "Commercial demand",
            "Paying layer",
            "PARTIAL",
            evidence_tip_html(
                name="COMMERCIAL DEMAND",
                read="PARTIAL",
                rows=[
                    ("Rails", "Credits / Stripe path / swap / NOS settlement"),
                    ("Named customers", "UNKNOWN"),
                    ("Organic vs incentives", "UNKNOWN"),
                    ("Host usdReward cum", _fmt_usd(net.get("jobs_stats_usd_reward_cum"))),
                ],
                note="Host usdReward ≠ audited Nosana revenue. Throughput ≠ proven organic demand.",
                source="Stage 1",
                source_url=com.get("docs_url"),
                as_of=as_of,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Network activity · commercial demand</h4>"
        '<div class="band-status c-green">NETWORK ACTIVE · DEMAND PARTIAL</div>'
        + lines
        + "</div>"
    )


def nos_token_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    supply = c.get("supply") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    vc = c.get("value_capture") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    dd = price.get("drawdown_pct")
    try:
        fill_w = f"{min(95, max(5, int(abs(float(dd or 90)))))}%"
    except (TypeError, ValueError):
        fill_w = "90%"
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
            "Token value capture",
            "NOS rail",
            "PARTIAL",
            evidence_tip_html(
                name="TOKEN VALUE CAPTURE",
                read="PARTIAL",
                rows=[
                    ("NOS on rail", "Yes (documented)"),
                    ("Usage→open-market demand", str(vc.get("usage_to_open_market_demand"))),
                    ("NNP-0001 live", str(vc.get("nnp0001_implementation"))),
                    ("Verified buyback/burn", "Not evidenced"),
                ],
                note=vc.get("core_interpretation") or "",
                source="Nosana docs + NNP-0001",
                source_url=vc.get("nnp_url"),
                as_of=as_of,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_CIRCLES,
            "Supply · market confirmation",
            "Float / NOS/SOL",
            f"30d {_fmt_pp(rs_sol.get('30'))}",
            evidence_tip_html(
                name="SUPPLY + RS",
                read=f"{SUPPLY_READ} · CONFIRMATION WEAK",
                rows=[
                    ("Supply read", SUPPLY_READ),
                    ("NOS/SOL 7d", _fmt_pp(rs_sol.get("7"))),
                    ("NOS/SOL 30d", _fmt_pp(rs_sol.get("30"))),
                    ("NOS/SOL 90d", _fmt_pp(rs_sol.get("90"))),
                    ("Staked", _fmt_n(supply.get("nos_staked"))),
                ],
                note="Do not use MATERIAL supply pressure. Priority RS = near windows vs SOL.",
                source="Stage 1",
                source_url=CG,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-token">'
        "<h4>Token demand · value capture · confirmation</h4>"
        '<div class="band-status c-orange">CAPTURE PARTIAL · CONFIRMATION WEAK</div>'
        + ddbar
        + lines
        + "</div>"
    )


def render_nos_evidence_cards(intel: dict[str, Any]) -> str:
    from lib.v3.forensic_cards import evidence_card, evidence_section

    c = _s1(intel)
    net = c.get("network") or {}
    flow = c.get("capital_flow") or {}
    mm = c.get("mm") or {}
    comp = c.get("competitive") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    cards = [
        evidence_card(
            title="Three layers",
            read="KEEP THE LAYERS SEPARATE",
            copy="1) Network activity real · 2) Commercial demand PARTIAL · 3) Token demand PARTIAL",
            tone="orange",
            status="PARTIAL",
            kpis=[
                ("Network", "REAL"),
                ("Commercial", "PARTIAL"),
                ("Token demand", "PARTIAL"),
            ],
            tip_rows=[
                ("Network activity", "Real"),
                ("Commercial demand", "PARTIAL"),
                ("Token demand", "PARTIAL"),
            ],
            source="NOS Stage-1",
            as_of=as_of,
            note="Do not collapse the three layers into one score.",
        ),
        evidence_card(
            title="Cumulative jobs",
            read="THROUGHPUT REAL",
            copy="All-time completed jobs are a stock, not a growth proof.",
            tone="green",
            status="KNOWN",
            kpis=[("Jobs completed", f"~{_fmt_n(net.get('jobs_completed_cumulative'))}")],
            tip_rows=[("Cumulative jobs", _fmt_n(net.get("jobs_completed_cumulative")))],
            source="Nosana",
            as_of=as_of,
            note="Not a growth proof.",
        ),
        evidence_card(
            title="Holders",
            read="CLASSIFICATION UNKNOWN",
            copy="Top-holder / liquid supply classification UNKNOWN",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Liquid supply class", "UNKNOWN")],
            tip_rows=[("Holders", "UNKNOWN")],
            source="NOS Stage-1",
            as_of=as_of,
            note="Do not invent a whale metric.",
        ),
        evidence_card(
            title="NNP live",
            read="IMPLEMENTATION UNKNOWN",
            copy="NNP-0001 implementation completeness UNKNOWN",
            tone="muted",
            status="UNKNOWN",
            kpis=[("NNP-0001", "UNKNOWN")],
            tip_rows=[("NNP-0001 completeness", "UNKNOWN")],
            source="NNP-0001",
            as_of=as_of,
            note="Documented rail ≠ proven live completeness.",
        ),
        evidence_card(
            title="DEX sample",
            read="BOUNDED SAMPLE",
            copy="Sell USD > buy USD in sample — not market-wide.",
            tone="orange",
            status="PARTIAL",
            kpis=[("n", str(flow.get("sample_n")))],
            tip_rows=[
                ("Sample n", str(flow.get("sample_n"))),
                ("Read", "sell USD > buy USD in sample — not market-wide"),
            ],
            source="DEX sample",
            as_of=as_of,
            note="Bounded sample ≠ market-wide flow.",
        ),
        evidence_card(
            title="MM registry",
            read="NO MATERIAL HIT",
            copy="Registry miss is not proof of zero market makers.",
            tone="muted",
            status="KNOWN",
            kpis=[("Registry", "NO MATERIAL HIT")],
            tip_rows=[("Read", str(mm.get("read") or "No material hit"))],
            source="MM registry",
            as_of=as_of,
            note="Known registry result. Not a suppression claim.",
        ),
        evidence_card(
            title="vs RENDER / IO (size only)",
            read="SIZE CONTEXT ONLY",
            copy="Market-cap comparison is size context, not quality.",
            tone="muted",
            status="KNOWN",
            kpis=[
                ("NOS", _fmt_usd(comp.get("nos_mcap_usd"))),
                ("RENDER", _fmt_usd(comp.get("render_mcap_usd"))),
                ("IO", _fmt_usd(comp.get("io_mcap_usd"))),
            ],
            tip_rows=[
                ("NOS", _fmt_usd(comp.get("nos_mcap_usd"))),
                ("RENDER", _fmt_usd(comp.get("render_mcap_usd"))),
                ("IO", _fmt_usd(comp.get("io_mcap_usd"))),
            ],
            source="CoinGecko",
            as_of=as_of,
            note="Size only. Not a quality ranking.",
        ),
        evidence_card(
            title="Leverage",
            read="NO MAJOR CEX PERP",
            copy="No major CEX perp found — no OI/funding invented.",
            tone="orange",
            status="KNOWN",
            kpis=[("CEX perp", "NONE FOUND")],
            tip_rows=[("OI/funding", "Not invented")],
            source="NOS Stage-1",
            as_of=as_of,
            note="Absence of a perp is not a hidden leverage print.",
        ),
    ]
    return evidence_section(
        cards,
        note="Compact conclusions first. Jobs, rail and method stay in tips underneath.",
    )


def render_nos_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">'
        "Real network usage does not automatically create strong open-market NOS demand."
        "</p></div><div class=\"split\">"
        + nos_network_band(intel)
        + nos_token_band(intel)
        + "</div></section>"
    )
    return (
        split
        + warning_stack_html(intel)
        + change_mind_section(intel, slug="nos")
        + reality_check_section(intel)
        + render_nos_evidence_cards(intel)
    )


def build_nos_v3_from_packs(report_date: str, v4_report: dict | None = None) -> dict[str, Any]:
    stage1 = load_nos_canonical()
    price = stage1.get("price_structure") or {}
    stance = nos_current_stance()
    assert stance["headline"] == STANCE_HEADLINE
    assert (stage1.get("supply") or {}).get("pressure_read") == SUPPLY_READ
    now_usd = price.get("now_usd")
    if isinstance(now_usd, (int, float)):
        price_display = f"~${now_usd:.3f}" if now_usd < 1 else f"~${now_usd:,.2f}"
    else:
        price_display = "—"
    doc: dict[str, Any] = {
        "meta": {
            "schema": "nos-v3",
            "slug": "nos",
            "report_date": report_date,
            "generated_at": now_iso(),
            "version": "stage1-v1",
            "v4_report_date": (v4_report or {}).get("report_date"),
        },
        "hero": {
            "asset": "NOS",
            "price_usd": now_usd,
            "price_display": price_display,
            "ath_display": f"${price.get('ath_usd')}",
            "drawdown_pct": price.get("drawdown_pct"),
            "price_as_of": (stage1.get("meta") or {}).get("fetched_at_utc"),
            "thesis": (
                "Real network usage does not automatically create strong open-market NOS demand."
            ),
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
            "v3_stance": stance["headline"],
            "v3_stance_note": stance["summary"],
            "confidence": stance["confidence"],
            "data_completeness": (
                "Stage-1 packs wired — holders UNKNOWN; NNP live UNKNOWN; "
                "organic vs credits UNKNOWN; >31d growth UNKNOWN."
            ),
        },
        "triad": {
            "lifecycle": {
                "display": "Post-ATH / weak confirmation",
                "detail": meaning("nos", price.get("drawdown_pct")),
            },
            "project_health": {
                "display": "NETWORK ACTIVE",
                "detail": "Jobs + GPU-hours real; commercial demand PARTIAL; capture PARTIAL.",
            },
            "market_timing": {
                "display": "CONFIRMATION WEAK",
                "detail": "Thin spot; no major CEX perp; near-window RS vs SOL weak.",
            },
        },
        "stage1": stage1,
    }
    doc["asset_top"] = build_nos_asset_top(doc)
    doc["warning_stack"] = build_nos_warning_stack(doc)
    doc["what_would_change_mind"] = build_nos_change_mind(doc)
    doc["reality_check"] = build_nos_reality_check(doc)
    return doc


def write_nos_v3(out_dir: Path | None = None) -> dict[str, Any]:
    report_date = now_iso()[:10]
    doc = build_nos_v3_from_packs(report_date)
    out_dir = out_dir or (REPORTS / report_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "nos-v3.json").write_text(payload, encoding="utf-8")
    (ROOT / "nos-v3.json").write_text(payload, encoding="utf-8")
    return doc
