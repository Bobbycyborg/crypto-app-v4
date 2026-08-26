"""SPX6900 V3 product layer — meme market structure (not compute fundamentals)."""

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
from lib.v3.current_stance import spx_current_stance
from lib.v3.fields import category_state, pack_risk_confirmation, now_iso
from lib.v3.sma_trend import technical_trend_category
from lib.v3.reality_check import empty_reality_check, rc_item
from lib.v3.route_d_shell import (
    ICON_CIRCLES,
    ICON_DROP,
    ICON_GRID,
    ICON_LEVERAGE,
    evidence_tip_html,
    mline_tip,
    reality_check_section,
    warning_stack_html,
)
from lib.v3.spx_stage1_loader import STANCE_HEADLINE, load_spx_canonical

CG = "https://www.coingecko.com/en/coins/spx6900"
BINANCE_PERP = "https://www.binance.com/en/futures/SPXUSDT"
SUPPLY_READ = "SUPPLY MOSTLY CIRCULATING"


def _s1(intel: dict) -> dict:
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
        return f"${n / 1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"${n:,.0f}"
    return f"${n:,.3f}"


def _fmt_funding(v: Any) -> str:
    try:
        # Binance funding rate → % per 8h
        return f"{float(v) * 100:+.3f}% / 8h"
    except (TypeError, ValueError):
        return "—"


def _oi_pct_txt(deriv: dict) -> str:
    pct = deriv.get("oi_vs_30d_max_pct")
    if pct is None:
        return "UNKNOWN"
    try:
        return f"~{float(pct):.0f}%"
    except (TypeError, ValueError):
        return "UNKNOWN"


def build_spx_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    c = _s1(doc)
    price = c.get("price_structure") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    liq = c.get("liquidity") or {}
    deriv = c.get("derivatives") or {}
    supply = c.get("supply") or {}
    holders = c.get("holders") or {}
    flow = c.get("capital_flow") or {}
    mm = c.get("mm") or {}
    attn = c.get("attention") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc") or now_iso()
    now_usd = price.get("now_usd")
    price_disp = f"~${now_usd:.3f}" if isinstance(now_usd, (int, float)) else "—"
    rets = price.get("returns_pct") or {}

    top = empty_asset_top("SPX", price_disp)
    top["price_as_of"] = as_of

    top["groups"]["market_structure"]["signals"] = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state="NEAR-TERM WEAK",
            display=retrace_label(price.get("drawdown_pct")),
            light=LIGHT_ORANGE,
            meaning=meaning("spx", price.get("drawdown_pct")),
            evidence=(
                f"SPX {price_disp} · ATH ${price.get('ath_usd')} ({price.get('ath_date')}) · "
                f"drawdown {_fmt_pct(price.get('drawdown_pct'))}. "
                f"CG 7d {_fmt_pct(price.get('cg_7d'))} · 30d {_fmt_pct(price.get('cg_30d'))}. "
                f"Binance futures 7d {_fmt_pct(rets.get('7'))} · 30d {_fmt_pct(rets.get('30'))} · "
                f"90d {_fmt_pct(rets.get('90'))} · 180d {_fmt_pct(rets.get('180'))}. "
                f"Local ~180d range {_fmt_usd(price.get('local_low_180'))}–"
                f"{_fmt_usd(price.get('local_high_180'))} "
                "(between recent 180d low and high — not clean new highs)."
            ),
            source="CoinGecko + Binance futures SPXUSDT",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_btc",
            label="vs BTC",
            state="NEAR-TERM WEAK",
            display="LAGS BTC (PRIORITY)",
            light=LIGHT_ORANGE,
            meaning="RS = relative strength. Positive 180d does not overwrite 7d/30d/90d weakness.",
            evidence=(
                f"7d {_fmt_pp(rs_btc.get('7'))} · 30d {_fmt_pp(rs_btc.get('30'))} · "
                f"90d {_fmt_pp(rs_btc.get('90'))} · 180d {_fmt_pp(rs_btc.get('180'))}."
            ),
            source="Binance fut SPX + spot BTC",
            source_url=BINANCE_PERP,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_sol",
            label="vs SOL",
            state="NEAR-TERM WEAK",
            display="LAGS SOL (PRIORITY)",
            light=LIGHT_ORANGE,
            meaning="Especially soft vs SOL on priority windows.",
            evidence=(
                f"7d {_fmt_pp(rs_sol.get('7'))} · 30d {_fmt_pp(rs_sol.get('30'))} · "
                f"90d {_fmt_pp(rs_sol.get('90'))} · 180d {_fmt_pp(rs_sol.get('180'))}."
            ),
            source="Binance fut SPX + spot SOL",
            source_url=BINANCE_PERP,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="cycle_context",
            label="Cycle / Range",
            state="MID-RANGE",
            display=str(price.get("range_label") or "BETWEEN RECENT 180D LOW & HIGH"),
            light=LIGHT_ORANGE,
            meaning="Recovery context ≠ leadership breakout. Month labels require dated evidence.",
            evidence=(
                f"Local low ~{_fmt_usd(price.get('local_low_180'))} · "
                f"local high ~{_fmt_usd(price.get('local_high_180'))}. "
                "Not clean new highs; not clear leadership."
            ),
            source="Binance futures daily",
            source_url=BINANCE_PERP,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["market_structure"]["group_state"] = "NEAR-TERM RS WEAK"
    top["groups"]["market_structure"]["group_light"] = LIGHT_ORANGE
    top["groups"]["market_structure"]["title"] = "Price / Market Structure"

    top["groups"]["capital_flow"]["signals"] = [
        signal(
            signal_id="venue_mix",
            label="Venue Mix",
            state="CEX-HEAVY",
            display="CEX-DOMINATED",
            light=LIGHT_ORANGE,
            meaning="CEX = centralised exchange. Solana DEX is secondary — not the whole market.",
            evidence=(
                f"{liq.get('read')}. Binance spot: {liq.get('binance_spot')}. "
                f"Binance perp 24h ~{_fmt_usd(deriv.get('fut_quote_vol_24h'))}. "
                f"Top Solana DEX vol (top-10 sample) ~{_fmt_usd(liq.get('dex_vol_24h_top10_sol'))}. "
                f"{liq.get('note')}"
            ),
            source="CoinGecko + Binance + DexScreener",
            source_url=liq.get("source_url") or CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="binance_perp",
            label="Binance Perp",
            state="PRESENT",
            display="USDT-M PERP ACTIVE",
            light=LIGHT_ORANGE,
            meaning="Perp = perpetual futures. Binance spot is absent — no clean Binance fut/spot ratio.",
            evidence=(
                f"Perp quote vol 24h ~{_fmt_usd(deriv.get('fut_quote_vol_24h'))}. "
                f"Binance spot listed: {deriv.get('binance_spot_listed')}. "
                f"Futures/spot ratio: UNKNOWN."
            ),
            source="Binance futures",
            source_url=deriv.get("source_url") or BINANCE_PERP,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="open_interest",
            label="Open Interest",
            state=str(deriv.get("oi_state") or "UNKNOWN"),
            display=(
                f"OI ~{_fmt_usd(deriv.get('oi_notional_usd'))}"
                if deriv.get("oi_notional_usd") is not None
                else "OI UNKNOWN"
            ),
            light=LIGHT_ORANGE if deriv.get("oi_state") not in (None, "UNKNOWN") else LIGHT_UNKNOWN,
            meaning="OI = open interest. Elevated vs own 30d history ≠ automatic bearish rule.",
            evidence=(
                f"State: {deriv.get('oi_state')}. "
                f"~{_fmt_n(deriv.get('oi_tokens'))} SPX · "
                f"~{_fmt_usd(deriv.get('oi_notional_usd'))} notional · "
                f"vs 30d max: {_oi_pct_txt(deriv)}. "
                f"{deriv.get('note')}"
            ),
            unknown="OI UNKNOWN when notional or 30d-max basis is missing.",
            source="Binance futures OI",
            source_url=BINANCE_PERP,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH" if deriv.get("oi_state") not in (None, "UNKNOWN") else "LOW",
            epistemic_status="KNOWN" if deriv.get("oi_state") not in (None, "UNKNOWN") else "UNKNOWN",
        ),
        signal(
            signal_id="funding_spot",
            label="Funding / Spot Confirmation",
            state=(
                f"{deriv.get('funding_state')} · PARTIAL"
                if deriv.get("funding_state") not in (None, "UNKNOWN")
                else "UNKNOWN"
            ),
            display=(
                "FUNDING QUIET"
                if deriv.get("funding_state") == "QUIET"
                else "FUNDING UNKNOWN"
            ),
            light=LIGHT_UNKNOWN,
            meaning="Positive funding ≠ top. Market-wide spot vs leverage split remains UNKNOWN.",
            evidence=(
                f"Funding {_fmt_funding(deriv.get('funding_latest'))}. "
                f"Funding state: {deriv.get('funding_state')}. "
                f"Read: {deriv.get('read')}."
            ),
            unknown="Organic spot vs leverage contribution market-wide = UNKNOWN.",
            source="Binance funding",
            source_url=BINANCE_PERP,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="MEDIUM" if deriv.get("funding_state") not in (None, "UNKNOWN") else "LOW",
            epistemic_status="PARTIAL" if deriv.get("funding_state") not in (None, "UNKNOWN") else "UNKNOWN",
        ),
        signal(
            signal_id="who_buying",
            label="Who Is Buying?",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="DEX txn counts are not buyer identity or net accumulation.",
            evidence=flow.get("dex_note") or "",
            unknown="Market-wide buyer quality UNKNOWN (CEX-heavy).",
            source="SPX Stage 1",
            source_url=flow.get("source_url") or CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="who_selling",
            label="Who Is Selling?",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="CEX-heavy tape — wallet-level DEX evidence cannot answer this reliably.",
            evidence=flow.get("dex_note") or "",
            unknown="Market-wide seller identity UNKNOWN.",
            source="SPX Stage 1",
            source_url=flow.get("source_url") or CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
    ]
    top["groups"]["capital_flow"]["group_state"] = "CEX-HEAVY · LEVERAGE PRESENT"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_ORANGE
    top["groups"]["capital_flow"]["title"] = "Liquidity / Leverage"

    top["groups"]["project_supply"]["signals"] = [
        signal(
            signal_id="circulating",
            label="Circulating Supply",
            state=SUPPLY_READ,
            display=f"~{float(supply.get('circulating_pct_of_max') or 0):.0f}% OF MAX",
            light=LIGHT_GREEN,
            meaning=(
                "Most of the fixed/global supply is already circulating. "
                "It does NOT mean ownership is decentralised or that whales cannot sell."
            ),
            evidence=(
                f"CG circ ~{_fmt_n(supply.get('circulating_cg'))} / max "
                f"{_fmt_n(supply.get('max_supply'))} "
                f"(~{float(supply.get('circulating_pct_of_max') or 0):.1f}%). "
                f"{supply.get('display_rule')}"
            ),
            source="CoinGecko",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="cross_chain",
            label="Cross-chain Supply Architecture",
            state="WORMHOLE PORTALS",
            display="ETH CANONICAL · SOL/BASE PORTALS",
            light=LIGHT_GREEN,
            meaning=(
                "Wormhole portal = bridged representation of the same underlying token "
                "on another chain. Bridge mint authority ≠ team discretionary printing."
            ),
            evidence=(
                f"Ethereum canonical {supply.get('eth_canonical')} · "
                f"totalSupply {_fmt_n(supply.get('eth_total_supply'))}. "
                f"Solana ~{_fmt_n(supply.get('solana_supply'))} · "
                f"Base ~{_fmt_n(supply.get('base_supply'))}. "
                f"Mint auth {str(supply.get('wormhole_mint_auth') or '')[:8]}… · "
                f"{supply.get('wormhole_auth_identity')}. "
                f"{supply.get('architecture_note')}"
            ),
            source="Wormhole + Ethereum + Solana mint investigation",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="holder_identity",
            label="Holder Identity",
            state="MARKET-WIDE UNKNOWN",
            display="SOLANA SLICE ONLY",
            light=LIGHT_UNKNOWN,
            meaning="Solana holder tables must never be presented as global SPX ownership.",
            evidence=(
                f"{holders.get('read')}. "
                f"Solana top-10 ~{float(holders.get('solana_top10_pct_of_sol_mint') or 0):.1f}% "
                f"of Solana mint · top-20 ~"
                f"{float(holders.get('solana_top20_pct_of_sol_mint') or 0):.1f}% of Solana mint. "
                f"#1 identity {holders.get('top1_identity')}. "
                f"Raydium authority in top: {holders.get('raydium_in_top')} "
                "(PROGRAM / LP — not discretionary whale). "
                f"{holders.get('solana_slice_note')}"
            ),
            unknown="Beneficial owners across chains UNKNOWN.",
            source="Solana largest accounts (slice only)",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="mm_otc",
            label="MM / OTC",
            state=str(mm.get("read") or "UNKNOWN"),
            display=str(mm.get("read") or "UNKNOWN"),
            light=LIGHT_UNKNOWN,
            meaning="MM = market maker. Absence ≠ no MMs. MM interaction ≠ suppression.",
            evidence=(
                f"Wintermute Solana registry ~{_fmt_n(mm.get('wintermute_sol_balance'))} SPX"
                f" (~{mm.get('wintermute_pct_of_max')}% of max). "
                f"{mm.get('note')} {mm.get('materiality_note')}"
            ),
            source="Shared MM registry + Solana RPC",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="attention",
            label="Attention / Reflexivity",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="No fake social metrics.",
            evidence=attn.get("note") or "",
            unknown="Persistent memetic capital vs temporary hype UNKNOWN.",
            source="SPX Stage 1",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
    ]
    top["groups"]["project_supply"]["group_state"] = "MOSTLY CIRCULATING · OWNERS OPAQUE"
    top["groups"]["project_supply"]["group_light"] = LIGHT_ORANGE
    top["groups"]["project_supply"]["title"] = "Supply / Ownership"

    stance = spx_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "explanation": stance["summary"],
        "directional_state": "DESCRIPTIVE",
        "confidence": stance["confidence"],
        "evidence_refs": [],
    }
    return enrich_tooltips(top)


def build_spx_warning_stack(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    supply = c.get("supply") or {}
    circ_pct = float(supply.get("circulating_pct_of_max") or 0)
    cats = [
        technical_trend_category("spx"),
        category_state(
            "supply",
            "SUPPLY",
            "CLEAR",
            detail=(
                f"CG circ ~{_fmt_n(supply.get('circulating_cg'))} / max "
                f"(~{circ_pct:.0f}%). 69M burned dead-address. Remaining 69M is not an unlock book. Unlock 0."
            ),
            summary=f"~{circ_pct:.0f}% circ · 69M burned dead · unlock 0",
        ),
        category_state(
            "venue_mix",
            "VENUE MIX",
            "PARTIAL",
            detail="Liquidity real but CEX-heavy; Solana DEX secondary; no Binance spot. Tape quality, not ATH.",
            summary="Liquidity real · CEX-heavy · no Binance spot",
        ),
        category_state(
            "buyers",
            "BUYERS",
            "UNKNOWN",
            detail="CEX-heavy market — wallet DEX evidence cannot prove capital quality.",
            summary="Buyer / seller UNKNOWN",
        ),
        category_state(
            "owners",
            "OWNERS",
            "UNKNOWN",
            detail="Market-wide beneficial ownership UNKNOWN; Solana slice ≠ global.",
            summary="Market-wide owners UNKNOWN",
        ),
    ]
    return pack_risk_confirmation(cats, "SPX Stage 1 evidence")


def build_spx_change_mind(intel: dict[str, Any]) -> dict[str, Any]:
    mm = (_s1(intel).get("mm") or {})
    mm_read = str(mm.get("read") or "UNKNOWN")
    constructive = [
        condition(
            condition_id="spot_led_reclaim",
            title="Spot-led reclaim of 50d",
            summary="SPX reclaims the 50-day on CEX spot leadership, not a perp-only bounce after a failed golden cross.",
            status="NO",
            interpretation="Below 50d and 200d on perp. Failed 50/200 cross ~19d ago is not bullish. Tiny 60d HH = range.",
            evidence_rows=[
                ("50d / 200d", "Below both (perp SPXUSDT)"),
                ("Binance spot", "Absent"),
                ("Funding", "Quiet"),
            ],
            source="SPX Stage 1",
            source_url=BINANCE_PERP,
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
        condition(
            condition_id="identifiable_non_mm_bid",
            title="Identifiable non-MM accumulation",
            summary="Persistent accumulation by identifiable non-MM capital — not a cleaner ownership spreadsheet.",
            status="UNKNOWN",
            interpretation="Market-wide owners UNKNOWN. Solana slice cannot prove quality. Transparency alone is not thesis-changing.",
            evidence_rows=[
                ("Market-wide owners", "UNKNOWN"),
                ("Solana slice", "Partial only"),
                ("Circ", "~93% · unlock 0"),
            ],
            source="SPX Stage 1",
            source_url=CG,
            as_of="2026-08-12",
            confidence="LOW",
            epistemic_status="UNKNOWN",
            icon="up",
        ),
    ]
    defensive = [
        condition(
            condition_id="range_fails_leverage_sticky",
            title="Range fails while leverage stays sticky",
            summary="Price loses the range lows while OI stays elevated and spot venues do not lead.",
            status="WATCH",
            interpretation="OI elevated ≠ crash. A structure break on a CEX-heavy tape would confirm weak spot demand.",
            evidence_rows=[
                ("OI vs 30d max", "Elevated"),
                ("Discipline", "OI rising ≠ bearish"),
                ("Venue mix", "Liquidity real · CEX-heavy"),
            ],
            source="SPX Stage 1",
            source_url=BINANCE_PERP,
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
        condition(
            condition_id="discretionary_distribution",
            title="Verified discretionary distribution",
            summary="Material discretionary distribution from large holders, or MM inventory building into weakness.",
            status="WATCH",
            interpretation="TRANSFER ≠ SALE. CEX DEPOSIT ≠ SALE. MM ≠ SUPPRESSION — but verified distribution would matter.",
            evidence_rows=[
                ("Verified MM inventory", mm_read),
                ("Discipline", "MM ≠ SUPPRESSION"),
            ],
            source="SPX Stage 1",
            source_url=CG,
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
    ]
    return pack_change_mind(constructive, defensive, schema_version=1)


def build_spx_reality_check(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    deriv = c.get("derivatives") or {}
    supply = c.get("supply") or {}
    holders = c.get("holders") or {}
    mm = c.get("mm") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rc = empty_reality_check()
    rc["priority_headline"] = "SOFT / LAGGING TAPE · CAPITAL QUALITY UNPROVEN"
    rc["known"] = [
        rc_item(
            item_id="price_dd",
            title=rc_title("spx", price.get("drawdown_pct")),
            summary=(
                f"~{_fmt_usd(price.get('now_usd'))} · ATH ${price.get('ath_usd')} · "
                f"{_fmt_pct(price.get('drawdown_pct'))}."
            ),
            evidence_rows=[
                ("Local 180d", f"{_fmt_usd(price.get('local_low_180'))}–{_fmt_usd(price.get('local_high_180'))}"),
            ],
            interpretation=meaning("spx", price.get("drawdown_pct")),
            priority="HIGH",
            source="SPX Stage-1",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="rs",
            title="Near-term lags BTC/SOL",
            summary=(
                f"SPX/SOL 7d {_fmt_pp(rs_sol.get('7'))} · 30d {_fmt_pp(rs_sol.get('30'))} · "
                f"SPX/BTC 30d {_fmt_pp(rs_btc.get('30'))}."
            ),
            evidence_rows=[("180d RS", "Positive context — not leadership")],
            interpretation="Priority 7d/30d/90d weakness preserved.",
            priority="HIGH",
            source="SPX Stage-1",
            source_url=BINANCE_PERP,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="venues",
            title="CEX-heavy; Binance spot absent",
            summary=(
                f"Binance perp 24h ~{_fmt_usd(deriv.get('fut_quote_vol_24h'))} · "
                "Binance spot NOT LISTED."
            ),
            evidence_rows=[("Solana DEX", "Secondary vs broader CEX activity")],
            interpretation="Do not say Binance dominates global spot.",
            priority="HIGH",
            source="SPX Stage-1",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="leverage",
            title="OI elevated vs own history",
            summary=(
                f"OI ~{_fmt_usd(deriv.get('oi_notional_usd'))} · "
                f"{_oi_pct_txt(deriv)} of 30d max · "
                f"funding {deriv.get('funding_state')}."
            ),
            evidence_rows=[("Fut/spot ratio", "UNKNOWN (Binance spot absent)")],
            interpretation="Leverage present — not automatically extreme or bearish.",
            priority="HIGH",
            source="SPX Stage-1",
            source_url=BINANCE_PERP,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="supply",
            title="Mostly circulating · ETH canonical 1B",
            summary=(
                f"CG ~{_fmt_n(supply.get('circulating_cg'))} / "
                f"{_fmt_n(supply.get('max_supply'))} · "
                f"ETH totalSupply {_fmt_n(supply.get('eth_total_supply'))}."
            ),
            evidence_rows=[
                ("Solana/Base", "Wormhole portals"),
                ("Mint auth", "Wormhole Token Bridge — not team print"),
            ],
            interpretation="Supply overhang less important than ownership opacity.",
            priority="HIGH",
            source="SPX Stage-1",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="mm",
            title="Verified MM registry inventory",
            summary=(
                f"WM ~{_fmt_n(mm.get('wintermute_sol_balance'))} SPX · "
                f"{mm.get('wintermute_pct_of_max')}% of max (SOL registry)."
            ),
            evidence_rows=[("Scope", "Solana / verified registry only")],
            interpretation="Not ‘no market makers’ and not suppression.",
            priority="MEDIUM",
            source="SPX Stage-1",
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
            title="Tape looks soft / lagging vs leadership",
            summary="Near-term RS weak versus BTC and especially SOL.",
            epistemic_status="INTERPRETATION",
            source="SPX Stage-1",
        ),
        rc_item(
            item_id="s2",
            title="Capital quality unproven",
            summary="CEX-heavy market leaves buyer/seller identity UNKNOWN.",
            epistemic_status="INTERPRETATION",
            source="SPX Stage-1",
        ),
        rc_item(
            item_id="s3",
            title="Leverage matters; not clearly extreme",
            summary="OI elevated vs own history; funding quiet. Spot partial.",
            epistemic_status="INTERPRETATION",
            source="SPX Stage-1",
        ),
        rc_item(
            item_id="s4",
            title="Ownership opacity > supply overhang",
            summary="~93% circulating; Solana map cannot answer global whale risk.",
            epistemic_status="INTERPRETATION",
            source="SPX Stage-1",
        ),
    ]
    rc["unknowns"] = [
        rc_item(
            item_id="u1",
            title="Beneficial owners across chains",
            summary="Multi-chain; Solana ~9% of CG float.",
            epistemic_status="UNKNOWN",
            source="SPX Stage-1",
        ),
        rc_item(
            item_id="u2",
            title="CEX buyer / seller identity",
            summary="Wallet DEX evidence cannot answer market-wide flow.",
            epistemic_status="UNKNOWN",
            source="SPX Stage-1",
        ),
        rc_item(
            item_id="u3",
            title="Organic spot vs leverage split",
            summary="No clean Binance fut/spot ratio; multi-venue mix unresolved.",
            epistemic_status="UNKNOWN",
            source="SPX Stage-1",
        ),
        rc_item(
            item_id="u4",
            title="Attention persistence",
            summary="No defensible social time-series.",
            epistemic_status="UNKNOWN",
            source="SPX Stage-1",
        ),
        rc_item(
            item_id="u5",
            title="Solana #1 owner identity",
            summary=f"Top-1 identity {holders.get('top1_identity')}.",
            epistemic_status="UNKNOWN",
            source="SPX Stage-1",
        ),
        rc_item(
            item_id="u6",
            title="Discretionary treasury / entity ownership",
            summary="If any — not verified this pass.",
            epistemic_status="UNKNOWN",
            source="SPX Stage-1",
        ),
    ]
    return rc


def spx_liq_lev_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    liq = c.get("liquidity") or {}
    deriv = c.get("derivatives") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    lines = (
        mline_tip(
            ICON_GRID,
            "Venue mix",
            "CEX vs DEX",
            "CEX-HEAVY",
            evidence_tip_html(
                name="LIQUIDITY",
                read=str(liq.get("read") or "CEX-HEAVY"),
                rows=[
                    ("Binance spot", str(liq.get("binance_spot"))),
                    ("Binance perp 24h", _fmt_usd(deriv.get("fut_quote_vol_24h"))),
                    ("Solana DEX sample vol", _fmt_usd(liq.get("dex_vol_24h_top10_sol"))),
                ],
                note="Do not present one Solana pool as the market. Do not say Binance dominates global spot.",
                source="SPX Stage-1",
                source_url=liq.get("source_url") or CG,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_LEVERAGE,
            "Leverage",
            "Binance USDT-M",
            "LEVERAGE PRESENT",
            evidence_tip_html(
                name="LEVERAGE",
                read=str(deriv.get("read") or ""),
                rows=[
                    ("OI state", str(deriv.get("oi_state") or "UNKNOWN")),
                    ("OI notional", _fmt_usd(deriv.get("oi_notional_usd"))),
                    ("OI vs 30d max", _oi_pct_txt(deriv)),
                    ("Funding state", str(deriv.get("funding_state") or "UNKNOWN")),
                    ("Funding", _fmt_funding(deriv.get("funding_latest"))),
                    ("Fut/spot ratio", "UNKNOWN"),
                ],
                note="OI rising ≠ bearish. Positive funding ≠ top. Not an automatic leverage warning.",
                source="SPX Stage-1",
                source_url=BINANCE_PERP,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Liquidity / leverage</h4>"
        '<div class="band-status c-orange">CEX-HEAVY · LEVERAGE PRESENT</div>'
        + lines
        + "</div>"
    )


def spx_supply_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    supply = c.get("supply") or {}
    holders = c.get("holders") or {}
    mm = c.get("mm") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    dd = price.get("drawdown_pct")
    try:
        fill_w = f"{min(95, max(5, int(abs(float(dd or 86)))))}%"
    except (TypeError, ValueError):
        fill_w = "86%"
    ddbar = (
        '<div class="ddbar">'
        f'<div class="ddbar-track"><div class="ddbar-fill" style="width:{fill_w}"></div></div>'
        f'<div class="ddbar-cap"><span>Now {_fmt_usd(price.get("now_usd"))}</span>'
        f"<span>{timing_caption('ATH $' + str(price.get('ath_usd')), dd)}</span></div>"
        "</div>"
    )
    lines = (
        mline_tip(
            ICON_DROP,
            "Circulating / architecture",
            "ETH + Wormhole",
            SUPPLY_READ,
            evidence_tip_html(
                name="SUPPLY",
                read=SUPPLY_READ,
                rows=[
                    (
                        "Circ / max",
                        f"{_fmt_n(supply.get('circulating_cg'))} / {_fmt_n(supply.get('max_supply'))}",
                    ),
                    ("ETH totalSupply", _fmt_n(supply.get("eth_total_supply"))),
                    ("Solana / Base", "Wormhole portals"),
                    ("Mint authority", "Wormhole Token Bridge"),
                ],
                note=(
                    "Most of SPX’s maximum supply is already circulating. Solana and Base versions "
                    "are Wormhole bridge representations of the Ethereum token, so Solana’s bridge "
                    "mint authority is not evidence of an independent extra supply."
                ),
                source="SPX Stage-1",
                source_url=CG,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_CIRCLES,
            "Ownership / MM",
            "Holders",
            "MARKET-WIDE UNKNOWN",
            evidence_tip_html(
                name="OWNERSHIP",
                read=str(holders.get("read") or "UNKNOWN"),
                rows=[
                    (
                        "Solana top-20 (of Sol mint)",
                        f"~{float(holders.get('solana_top20_pct_of_sol_mint') or 0):.1f}%",
                    ),
                    ("Market-wide owners", "UNKNOWN"),
                    ("Wintermute Sol", _fmt_n(mm.get("wintermute_sol_balance"))),
                ],
                note=(
                    "Never present Solana concentration as global. Raydium authority = PROGRAM/LP, "
                    "not whale. MM inventory ≠ suppression."
                ),
                source="SPX Stage-1",
                source_url=CG,
                as_of=as_of,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-token">'
        "<h4>Supply / ownership</h4>"
        '<div class="band-status c-orange">MOSTLY CIRCULATING · OWNERS OPAQUE</div>'
        + ddbar
        + lines
        + "</div>"
    )


def render_spx_evidence_cards(intel: dict[str, Any]) -> str:
    from lib.v3.forensic_cards import evidence_card, evidence_section

    c = _s1(intel)
    holders = c.get("holders") or {}
    deriv = c.get("derivatives") or {}
    mm = c.get("mm") or {}
    supply = c.get("supply") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    oi_line = (
        f"state={deriv.get('oi_state')} · {_fmt_usd(deriv.get('oi_notional_usd'))} · "
        f"vs 30d max {_oi_pct_txt(deriv)} — not auto-bearish"
    )
    cards = [
        evidence_card(
            title="Near-term RS",
            read="LAGS BTC/SOL",
            copy="Lags BTC/SOL on 7d/30d/90d — 180d recovery is context only.",
            tone="orange",
            status="KNOWN",
            kpis=[("Priority windows", "7d / 30d / 90d"), ("180d", "CONTEXT ONLY")],
            tip_rows=[("Read", "Lags BTC/SOL on 7d/30d/90d — 180d recovery is context only")],
            source="SPX Stage-1",
            as_of=as_of,
            note="Priority RS = near windows.",
        ),
        evidence_card(
            title="Venue mix",
            read="CEX-HEAVY",
            copy="CEX-heavy · Binance spot absent · Binance perp present.",
            tone="orange",
            status="KNOWN",
            kpis=[("Binance spot", "ABSENT"), ("Binance perp", "PRESENT")],
            tip_rows=[("Read", "CEX-heavy · Binance spot absent · Binance perp present")],
            source="SPX Stage-1",
            as_of=as_of,
            note="Do not say Binance dominates global spot.",
        ),
        evidence_card(
            title="Open interest",
            read=str(deriv.get("oi_state") or "UNKNOWN"),
            copy=oi_line,
            tone="orange",
            status=str(deriv.get("oi_state") or "UNKNOWN"),
            kpis=[
                ("OI", _fmt_usd(deriv.get("oi_notional_usd"))),
                ("Vs 30d max", _oi_pct_txt(deriv)),
            ],
            tip_rows=[
                ("OI state", str(deriv.get("oi_state") or "UNKNOWN")),
                ("OI notional", _fmt_usd(deriv.get("oi_notional_usd"))),
                ("Vs 30d max", _oi_pct_txt(deriv)),
            ],
            source="SPX Stage-1",
            source_url=BINANCE_PERP,
            as_of=as_of,
            note="OI rising ≠ bearish.",
        ),
        evidence_card(
            title="Supply",
            read="MOSTLY CIRCULATING",
            copy="ETH canonical · Sol/Base = Wormhole portals.",
            tone="green",
            status="KNOWN",
            kpis=[
                ("Circ", _fmt_n(supply.get("circulating_cg"))),
                ("Burned/dead", "69.0M"),
                ("Unlock", "0"),
            ],
            tip_rows=[
                ("Circ / max", f"{_fmt_n(supply.get('circulating_cg'))} / {_fmt_n(supply.get('max_supply'))}"),
                ("ETH canonical", "1B"),
                ("Sol/Base", "Wormhole portals"),
                ("Burned/dead", "69.0M"),
                ("Unlock", "0"),
            ],
            source="SPX Stage-1",
            source_url=CG,
            as_of=as_of,
            note="69M burned/dead is not remaining/unreleased. Unlock 0.",
        ),
        evidence_card(
            title="Ownership",
            read="MARKET-WIDE UNKNOWN",
            copy=(
                f"Solana top-20 ~{float(holders.get('solana_top20_pct_of_sol_mint') or 0):.1f}% "
                "of Sol mint only"
            ),
            tone="muted",
            status="UNKNOWN",
            kpis=[
                ("Market-wide", "UNKNOWN"),
                ("Sol top-20", f"~{float(holders.get('solana_top20_pct_of_sol_mint') or 0):.1f}%"),
            ],
            tip_rows=[
                ("Market-wide owners", "UNKNOWN"),
                ("Solana top-20 (of Sol mint)", f"~{float(holders.get('solana_top20_pct_of_sol_mint') or 0):.1f}%"),
            ],
            source="SPX Stage-1",
            as_of=as_of,
            note="Sol mint share is not market-wide ownership.",
        ),
        evidence_card(
            title="Buyer quality",
            read="WHO UNKNOWN",
            copy="CEX-heavy — who is buying/selling remains UNKNOWN.",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Who buying/selling", "UNKNOWN")],
            tip_rows=[("Read", "CEX-heavy — who is buying/selling remains UNKNOWN")],
            source="SPX Stage-1",
            as_of=as_of,
            note="Venue mix ≠ buyer quality.",
        ),
        evidence_card(
            title="MM / OTC",
            read="VERIFIED REGISTRY PRINT",
            copy="Verified registry result. Not ‘no market makers’.",
            tone="muted",
            status="KNOWN",
            kpis=[("Registry", "VERIFIED")],
            tip_rows=[("Read", str(mm.get("read") or "UNKNOWN"))],
            source="SPX Stage-1",
            as_of=as_of,
            note="MM ≠ suppression.",
        ),
        evidence_card(
            title="Attention",
            read="NO DEFENSIBLE SERIES",
            copy="No defensible reflexivity time-series.",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Reflexivity series", "UNKNOWN")],
            tip_rows=[("Read", "No defensible reflexivity time-series")],
            source="SPX Stage-1",
            as_of=as_of,
            note="Do not invent attention quality.",
        ),
    ]
    return evidence_section(
        cards,
        note="Compact conclusions first. Venues, ownership and method stay in tips underneath.",
    )


def render_spx_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">'
        "Is SPX attracting persistent high-quality capital — or is this mostly a soft / lagging "
        "meme tape with capital quality still unproven?"
        "</p></div><div class=\"split\">"
        + spx_liq_lev_band(intel)
        + spx_supply_band(intel)
        + "</div></section>"
    )
    return (
        split
        + warning_stack_html(intel)
        + change_mind_section(intel, slug="spx6900")
        + reality_check_section(intel)
        + render_spx_evidence_cards(intel)
    )


def build_spx_v3_from_packs(report_date: str, v4_report: dict | None = None) -> dict[str, Any]:
    stage1 = load_spx_canonical()
    price = stage1.get("price_structure") or {}
    stance = spx_current_stance()
    assert stance["headline"] == STANCE_HEADLINE
    assert (stage1.get("supply") or {}).get("pressure_read") == "MOSTLY CIRCULATING"
    now_usd = price.get("now_usd")
    price_display = f"~${now_usd:.3f}" if isinstance(now_usd, (int, float)) else "—"
    doc: dict[str, Any] = {
        "meta": {
            "schema": "spx6900-v3",
            "slug": "spx6900",
            "report_date": report_date,
            "generated_at": now_iso(),
            "version": "stage1-v1",
            "v4_report_date": (v4_report or {}).get("report_date"),
        },
        "hero": {
            "asset": "SPX",
            "price_usd": now_usd,
            "price_display": price_display,
            "ath_display": f"${price.get('ath_usd')}",
            "drawdown_pct": price.get("drawdown_pct"),
            "price_as_of": (stage1.get("meta") or {}).get("fetched_at_utc"),
            "thesis": (
                "Is SPX attracting persistent high-quality capital — or is this mostly a soft / "
                "lagging meme tape with capital quality still unproven?"
            ),
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
            "v3_stance": stance["headline"],
            "v3_stance_note": stance["summary"],
            "confidence": stance["confidence"],
            "data_completeness": (
                "Stage-1 packs wired — market-wide owners UNKNOWN; buyer/seller UNKNOWN; "
                "spot vs leverage split UNKNOWN; attention UNKNOWN."
            ),
        },
        "triad": {
            "lifecycle": {
                "display": "Post-ATH / soft",
                "detail": meaning("spx", price.get("drawdown_pct")),
            },
            "project_health": {
                "display": "MOSTLY CIRCULATING",
                "detail": "ETH canonical · Wormhole portals · ownership opaque — meme, not compute.",
            },
            "market_timing": {
                "display": "CEX-HEAVY",
                "detail": "Binance perp present; Binance spot absent; buyer quality UNKNOWN.",
            },
        },
        "stage1": stage1,
    }
    doc["asset_top"] = build_spx_asset_top(doc)
    doc["warning_stack"] = build_spx_warning_stack(doc)
    doc["what_would_change_mind"] = build_spx_change_mind(doc)
    doc["reality_check"] = build_spx_reality_check(doc)
    return doc


def write_spx_v3(out_dir: Path | None = None) -> dict[str, Any]:
    report_date = now_iso()[:10]
    doc = build_spx_v3_from_packs(report_date)
    out_dir = out_dir or (REPORTS / report_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "spx-v3.json").write_text(payload, encoding="utf-8")
    (ROOT / "spx-v3.json").write_text(payload, encoding="utf-8")
    return doc
