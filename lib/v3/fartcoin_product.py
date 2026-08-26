"""FARTCOIN V3 product layer — meme market structure (not compute fundamentals)."""

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
from lib.v3.current_stance import fartcoin_current_stance
from lib.v3.fields import category_state, pack_risk_confirmation, now_iso
from lib.v3.sma_trend import technical_trend_category
from lib.v3.fartcoin_stage1_loader import (
    STANCE_HEADLINE,
    SUPPLY_READ,
    load_fartcoin_canonical,
)
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

CG = "https://www.coingecko.com/en/coins/fartcoin"
BINANCE_PERP = "https://www.binance.com/en/futures/FARTCOINUSDT"


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


def build_fartcoin_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    c = _s1(doc)
    price = c.get("price_structure") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    rs_pump = c.get("rs_vs_pump_pp") or {}
    spot = c.get("spot_liquidity") or {}
    lev = c.get("leverage") or {}
    supply = c.get("supply") or {}
    own = c.get("ownership") or {}
    flow = c.get("capital_flow") or {}
    mm = c.get("mm") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc") or now_iso()
    now_usd = price.get("now_usd")
    price_disp = f"~${now_usd:.3f}" if isinstance(now_usd, (int, float)) else "—"
    rets = price.get("returns_pct") or {}

    top = empty_asset_top("FARTCOIN", price_disp)
    top["price_as_of"] = as_of

    top["groups"]["market_structure"]["signals"] = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state="POST-ATH WEAK",
            display=retrace_label(price.get("drawdown_pct")),
            light=LIGHT_ORANGE,
            meaning=meaning("fartcoin", price.get("drawdown_pct")),
            evidence=(
                f"FARTCOIN {price_disp} · ATH ${price.get('ath_usd')} ({price.get('ath_date')}) · "
                f"drawdown {_fmt_pct(price.get('drawdown_pct'))} · mcap {_fmt_usd(price.get('mcap_usd'))}. "
                f"Coinbase 7d {_fmt_pct(rets.get('7'))} · 30d {_fmt_pct(rets.get('30'))} · "
                f"90d {_fmt_pct(rets.get('90'))} · 180d {_fmt_pct(rets.get('180'))}. "
                "Close was above SMA20 and below SMA50 in the research snapshot."
            ),
            source="CoinGecko + Coinbase daily",
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
            meaning="Priority relative strength — Solana beta context.",
            evidence=(
                f"7d {_fmt_pp(rs_sol.get('7'))} · 30d {_fmt_pp(rs_sol.get('30'))} · "
                f"90d {_fmt_pp(rs_sol.get('90'))} · 180d {_fmt_pp(rs_sol.get('180'))}."
            ),
            source="Coinbase FART + Binance SOL",
            source_url=price.get("source_url_coinbase"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_btc",
            label="vs BTC",
            state="WEAK 30d/90d",
            display="WEAK VS BTC",
            light=LIGHT_ORANGE,
            meaning="Tiny +7d vs BTC does not overwrite broader structure.",
            evidence=(
                f"7d {_fmt_pp(rs_btc.get('7'))} · 30d {_fmt_pp(rs_btc.get('30'))} · "
                f"90d {_fmt_pp(rs_btc.get('90'))} · 180d {_fmt_pp(rs_btc.get('180'))}."
            ),
            source="Coinbase FART + Binance BTC",
            source_url=price.get("source_url_coinbase"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_pump",
            label="vs PUMP (context)",
            state="LAGGING",
            display="LAGS PUMP 30d/90d",
            light=LIGHT_ORANGE,
            meaning="Meme context only — not a leaderboard.",
            evidence=(
                f"7d {_fmt_pp(rs_pump.get('7'))} · 30d {_fmt_pp(rs_pump.get('30'))} · "
                f"90d {_fmt_pp(rs_pump.get('90'))}."
            ),
            source="Coinbase FART + Binance PUMP",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["market_structure"]["group_state"] = "POST-ATH STRUCTURE WEAK"
    top["groups"]["market_structure"]["group_light"] = LIGHT_ORANGE
    top["groups"]["market_structure"]["title"] = "Price / Market Structure"

    top["groups"]["capital_flow"]["signals"] = [
        signal(
            signal_id="spot_liquidity",
            label="Spot Liquidity",
            state="REAL SPOT EXISTS",
            display="CEX + DEX SPOT REAL",
            light=LIGHT_GREEN,
            meaning="Not perp-only. Binance spot absent; Coinbase + DEX + others present.",
            evidence=(
                f"Binance spot {spot.get('binance_spot')} · Binance perp {spot.get('binance_perp')} · "
                f"Coinbase spot {spot.get('coinbase_spot')}. "
                f"CG total 24h ~{_fmt_usd(spot.get('cg_vol24_usd'))} · "
                f"Coinbase comparator ~{_fmt_usd(spot.get('coinbase_vol24_usd'))} · "
                f"top Raydium liq ~{_fmt_usd(spot.get('top_pool_liq_usd'))}. "
                f"{spot.get('note')}"
            ),
            source="CoinGecko + DexScreener + Binance",
            source_url=spot.get("source_url") or CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="leverage",
            label="Leverage / Perps",
            state="LEVERAGE MATERIAL",
            display="BINANCE PERP MATERIAL",
            light=LIGHT_ORANGE,
            meaning="OI rising ≠ bearish. Mild funding ≠ top.",
            evidence=(
                f"Binance OI ~{_fmt_usd(lev.get('oi_usd_approx'))} · "
                f"perp 24h ~{_fmt_usd(lev.get('perp_quote_vol_24h'))} · "
                f"funding ~{lev.get('funding_rate')}. "
                f"Perp/Coinbase-spot comparator ~{lev.get('perp_vs_coinbase_spot_ratio')}× "
                f"({lev.get('ratio_label')}; confidence {lev.get('ratio_confidence')}). "
                f"OI ~30d {_fmt_usd(lev.get('oi_hist_30d_start_usd'))} → "
                f"{_fmt_usd(lev.get('oi_hist_30d_end_usd'))}. "
                f"Multi-venue OI aggregate = {lev.get('multi_venue_oi_aggregate')}."
            ),
            source="Binance futures",
            source_url=lev.get("source_url") or BINANCE_PERP,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="who_is_buying",
            label="Who Is Buying?",
            state="UNKNOWN",
            display="UNKNOWN BEYOND SAMPLE",
            light=LIGHT_UNKNOWN,
            meaning="Bounded DEX sample ≠ market-wide flow.",
            evidence=(
                f"Sample n={flow.get('sample_n')}: buys {flow.get('sample_buys')} / "
                f"sells {flow.get('sample_sells')} · buy USD {_fmt_usd(flow.get('sample_buy_usd'))} · "
                f"sell USD {_fmt_usd(flow.get('sample_sell_usd'))}. {flow.get('dex_note')}"
            ),
            unknown="Market-wide buyer quality UNKNOWN.",
            source="GeckoTerminal sample",
            source_url=flow.get("source_url"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="who_is_selling",
            label="Who Is Selling?",
            state="UNKNOWN",
            display="UNKNOWN BEYOND SAMPLE",
            light=LIGHT_UNKNOWN,
            meaning="Sample sell USD edge ≠ confirmed distribution.",
            evidence=flow.get("dex_note") or "",
            unknown="Market-wide seller quality UNKNOWN.",
            source="GeckoTerminal sample",
            source_url=flow.get("source_url"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="mm_otc",
            label="MM / OTC",
            state=mm.get("read") or "SMALL WM INVENTORY",
            display="SMALL WM INVENTORY",
            light=LIGHT_UNKNOWN,
            meaning="Inventory observation only — not dump/suppression.",
            evidence=(
                f"Wintermute registry ~{_fmt_n(mm.get('wintermute_fartcoin'))} FARTCOIN "
                f"(~{mm.get('wintermute_pct_supply')}% supply). {mm.get('note')}"
            ),
            source="Shared MM registry + Solana RPC",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["capital_flow"]["group_state"] = "SPOT REAL · LEVERAGE MATERIAL"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_ORANGE
    top["groups"]["capital_flow"]["title"] = "Spot / Leverage / Flow"

    top["groups"]["project_supply"]["signals"] = [
        signal(
            signal_id="float_clean",
            label="Supply / Float",
            state=SUPPLY_READ,
            display=SUPPLY_READ,
            light=LIGHT_GREEN,
            meaning=(
                "Almost all max supply circulating; mint/freeze revoked. "
                "Says nothing about who owns existing tokens."
            ),
            evidence=(
                f"Circ ~{_fmt_n(supply.get('circulating'))} / max {_fmt_n(supply.get('max_supply'))} "
                f"(~{supply.get('circulating_pct_of_max')}%). "
                f"Mint authority {supply.get('mint_authority_status')} · "
                f"freeze {supply.get('freeze_authority_status')}. "
                f"{supply.get('display_rule')}"
            ),
            unknown="Vesting/team/creator holdings UNKNOWN.",
            source="CoinGecko + Solana mint account",
            source_url=supply.get("source_url") or CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="raw_concentration",
            label="Raw Holder Concentration",
            state="RAW TOP-20 HIGH",
            display=f"TOP-20 ~{own.get('top20_raw_pct')}%",
            light=LIGHT_ORANGE,
            meaning="Raw token-account share — not proven discretionary whales.",
            evidence=(
                f"Top 20 token accounts ~{own.get('top20_raw_pct')}% of supply. "
                f"Unclassified in top-20: {own.get('unclassified_in_top20')}/20. "
                f"{own.get('note')}"
            ),
            source="Helius getTokenLargestAccounts",
            source_url=own.get("source_url"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="adjusted_owners",
            label="Discretionary Ownership",
            state="UNKNOWN",
            display="ADJUSTED CONCENTRATION UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Fully circulating ≠ decentralised ownership.",
            evidence=own.get("read") or "",
            unknown="CEX/LP/program vs discretionary labeling incomplete.",
            source="Stage 1 ownership pass",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="creator",
            label="Creator / Early",
            state="UNKNOWN",
            display="CREATOR OWNERSHIP UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Early wallet ≠ insider.",
            evidence=(c.get("creator") or {}).get("note") or "",
            source="Stage 1",
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
    ]
    top["groups"]["project_supply"]["group_state"] = "FLOAT CLEAN · OWNERS UNRESOLVED"
    top["groups"]["project_supply"]["group_light"] = LIGHT_ORANGE
    top["groups"]["project_supply"]["title"] = "Supply / Ownership"

    stance = fartcoin_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "explanation": stance["summary"],
        "directional_state": "DESCRIPTIVE",
        "confidence": stance["confidence"],
        "evidence_refs": [],
    }
    return enrich_tooltips(top)


def build_fartcoin_warning_stack(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    supply = c.get("supply") or {}
    cats = [
        technical_trend_category("fartcoin"),
        category_state(
            "float",
            "FLOAT",
            "CLEAR",
            detail=(
                f"Mint authority {supply.get('mint_authority_status')} · "
                f"freeze {supply.get('freeze_authority_status')} · circ ≈ max. "
                "Supply is clean. Not the same as decentralised owners."
            ),
            summary="Mint/freeze revoked · ~100% circ",
        ),
        category_state(
            "leverage",
            "LEVERAGE",
            "PARTIAL",
            detail="Binance perp material vs Coinbase spot comparator. No Binance spot. OI ≠ crash.",
            summary="Binance perp material vs Coinbase spot",
        ),
        category_state(
            "owners",
            "OWNERS",
            "UNKNOWN",
            detail="Raw top-20 ~45% unusable as discretionary concentration. Adjusted owners UNKNOWN.",
            summary="Discretionary concentration UNKNOWN",
        ),
        category_state(
            "creator",
            "CREATOR",
            "UNKNOWN",
            detail="Deployer/creator/early-wallet attribution not verified. Do not infer from mint suffix.",
            summary="Creator / early UNKNOWN",
        ),
    ]
    return pack_risk_confirmation(cats, "FARTCOIN Stage 1 evidence")


def build_fartcoin_change_mind(intel: dict[str, Any]) -> dict[str, Any]:
    constructive = [
        condition(
            condition_id="reclaim_structure_spot",
            title="Reclaims 200d on spot-led tape",
            summary="FART reclaims the 200-day while Coinbase spot holds up and Binance perp does not do the work.",
            status="NO",
            interpretation="Above 50d on perp, still below 200d. Priority RS vs SOL/BTC is weak. Structure has not repaired.",
            evidence_rows=[
                ("50d / 200d", "Above ~$0.138 · below ~$0.169 (perp)"),
                ("Binance spot", "Absent"),
                ("Funding", "Mild positive"),
            ],
            source="FARTCOIN Stage 1",
            source_url=BINANCE_PERP,
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
        condition(
            condition_id="identifiable_spot_accumulation",
            title="Identifiable spot accumulation",
            summary="Repeat or attributable wallets accumulate on spot venues — not just an unlabeled top-20 print.",
            status="UNKNOWN",
            interpretation="Raw top-20 ~45% is unusable. Discretionary owners unresolved. Cleaner labels alone would not change the thesis; accumulation would.",
            evidence_rows=[
                ("Raw top-20", "~44.7%"),
                ("Adjusted discretionary", "UNKNOWN"),
            ],
            source="FARTCOIN Stage 1",
            source_url=CG,
            as_of="2026-08-12",
            confidence="LOW",
            epistemic_status="UNKNOWN",
            icon="up",
        ),
    ]
    defensive = [
        condition(
            condition_id="leverage_dominates",
            title="Leverage carries price as 50d fails",
            summary="Binance perp stays elevated vs Coinbase spot while price loses the 50-day.",
            status="PARTIAL",
            interpretation="Perp vs Coinbase comparator is already material. A 50d loss on that tape would confirm leverage doing the work.",
            evidence_rows=[
                ("Perp vs Coinbase comparator", "~12.8×"),
                ("50d", "Currently above on perp"),
                ("Multi-venue OI", "UNKNOWN"),
            ],
            source="FARTCOIN Stage 1",
            source_url=BINANCE_PERP,
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
        condition(
            condition_id="cex_distribution_risk",
            title="Discretionary size reaches exchanges",
            summary="Verified large discretionary holders move sustained size toward exchanges.",
            status="WATCH",
            interpretation="CEX deposit ≠ sale — but it would raise distribution risk against a clean float.",
            evidence_rows=[
                ("Discipline", "CEX DEPOSIT ≠ SALE"),
                ("Creator/early", "UNKNOWN"),
            ],
            source="FARTCOIN Stage 1",
            source_url=CG,
            as_of="2026-08-12",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
    ]
    return pack_change_mind(constructive, defensive, schema_version=1)


def build_fartcoin_reality_check(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    lev = c.get("leverage") or {}
    supply = c.get("supply") or {}
    own = c.get("ownership") or {}
    mm = c.get("mm") or {}
    rets = price.get("returns_pct") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    rc = empty_reality_check()
    rc["priority_headline"] = "FLOAT CLEAN ≠ OWNERSHIP CLEAN"
    rc["known"] = [
        rc_item(
            item_id="identity_price",
            title=rc_title("fartcoin", price.get("drawdown_pct")),
            summary=(
                f"Mint verified · ~${price.get('now_usd')} · ATH ${price.get('ath_usd')} · "
                f"{_fmt_pct(price.get('drawdown_pct'))}."
            ),
            evidence_rows=[
                ("7d / 30d / 90d", f"{_fmt_pct(rets.get('7'))} / {_fmt_pct(rets.get('30'))} / {_fmt_pct(rets.get('90'))}"),
                ("MCAP", _fmt_usd(price.get("mcap_usd"))),
            ],
            interpretation=meaning("fartcoin", price.get("drawdown_pct")),
            priority="HIGH",
            source="FARTCOIN Stage-1",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="rs",
            title="Priority RS weak vs SOL/BTC",
            summary=f"FART/SOL 30d {_fmt_pp(rs_sol.get('30'))} · 90d {_fmt_pp(rs_sol.get('90'))}.",
            evidence_rows=[("7d FART/SOL", _fmt_pp(rs_sol.get("7")))],
            interpretation="Not a clean leadership print.",
            priority="HIGH",
            source="FARTCOIN Stage-1",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="leverage",
            title="Binance perp material; spot absent",
            summary=(
                f"OI ~{_fmt_usd(lev.get('oi_usd_approx'))} · "
                f"perp 24h ~{_fmt_usd(lev.get('perp_quote_vol_24h'))} · "
                f"funding ~{lev.get('funding_rate')}."
            ),
            evidence_rows=[
                ("Perp vs Coinbase comparator", f"~{lev.get('perp_vs_coinbase_spot_ratio')}×"),
                ("Label", lev.get("ratio_label") or ""),
            ],
            interpretation="Leverage is first-class — not an automatic bearish rule.",
            priority="HIGH",
            source="FARTCOIN Stage-1",
            source_url=BINANCE_PERP,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="float",
            title="Float clean",
            summary=(
                f"Circ ≈ max · mint {supply.get('mint_authority_status')} · "
                f"freeze {supply.get('freeze_authority_status')}."
            ),
            evidence_rows=[("Read", SUPPLY_READ)],
            interpretation="Mint/future-supply risk low — ownership risk separate.",
            priority="HIGH",
            source="FARTCOIN Stage-1",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="holders_raw",
            title="Raw top-20 high; adjusted UNKNOWN",
            summary=f"Top-20 token accounts ~{own.get('top20_raw_pct')}% of supply.",
            evidence_rows=[("Adjusted discretionary", "UNKNOWN")],
            interpretation="Do not call this whale control.",
            priority="HIGH",
            source="FARTCOIN Stage-1",
            source_url=own.get("source_url"),
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="mm",
            title="Small Wintermute inventory",
            summary=f"~{_fmt_n(mm.get('wintermute_fartcoin'))} FARTCOIN in registry wallet.",
            evidence_rows=[("Read", mm.get("read") or "")],
            interpretation="Not a suppression/dump narrative.",
            priority="MEDIUM",
            source="FARTCOIN Stage-1",
            source_url=CG,
            as_of="2026-08-12",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    rc["suggests"] = [
        rc_item(item_id="s1", title="Tape is not clean leadership", summary="Weak priority RS vs SOL/BTC.", epistemic_status="INTERPRETATION"),
        rc_item(item_id="s2", title="Leverage is first-class structure", summary="Perp intensity matters on Binance.", epistemic_status="INTERPRETATION"),
        rc_item(item_id="s3", title="Future mint risk is low", summary="Revoked authorities + near-full float.", epistemic_status="INTERPRETATION"),
        rc_item(item_id="s4", title="Ownership risk unresolved", summary="Raw concentration ≠ labeled whales.", epistemic_status="INTERPRETATION"),
        rc_item(item_id="s5", title="MM inventory ≠ suppression", summary="Small verified Wintermute balance only.", epistemic_status="INTERPRETATION"),
    ]
    rc["unknowns"] = [
        rc_item(item_id="u1", title="Adjusted discretionary holder concentration", summary="CEX/LP/program labeling incomplete.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u2", title="Creator / deployer / early-wallet ownership", summary="Not verified.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u3", title="Top-wallet accumulation / distribution timelines", summary="Not reconstructed.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u4", title="Organic vs leveraged global demand share", summary="Unresolved.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u5", title="Multi-venue aggregate OI", summary="Bybit+OKX+Binance not summed.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u6", title="Attention / reflexivity quality", summary="No clean social series.", epistemic_status="UNKNOWN"),
    ]
    return rc


def fartcoin_spot_lev_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    spot = c.get("spot_liquidity") or {}
    lev = c.get("leverage") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    lines = (
        mline_tip(
            ICON_GRID,
            "Spot venues",
            "CEX + DEX",
            "SPOT REAL",
            evidence_tip_html(
                name="SPOT LIQUIDITY",
                read="REAL SPOT EXISTS",
                rows=[
                    ("Binance spot", str(spot.get("binance_spot"))),
                    ("Binance perp", str(spot.get("binance_perp"))),
                    ("Coinbase spot", str(spot.get("coinbase_spot"))),
                    ("CG 24h vol", _fmt_usd(spot.get("cg_vol24_usd"))),
                    ("Top Raydium liq", _fmt_usd(spot.get("top_pool_liq_usd"))),
                ],
                note="Not perp-only. Binance primary FARTCOIN market is the perpetual.",
                source="FARTCOIN Stage-1",
                source_url=spot.get("source_url") or CG,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_LEVERAGE,
            "Perp intensity",
            "Binance USDT-M",
            "LEVERAGE MATERIAL",
            evidence_tip_html(
                name="LEVERAGE",
                read="LEVERAGE MATERIAL",
                rows=[
                    ("OI", _fmt_usd(lev.get("oi_usd_approx"))),
                    ("Perp 24h", _fmt_usd(lev.get("perp_quote_vol_24h"))),
                    ("Funding", str(lev.get("funding_rate"))),
                    ("Perp vs Coinbase spot", f"~{lev.get('perp_vs_coinbase_spot_ratio')}×"),
                    ("Comparator label", lev.get("ratio_label") or ""),
                ],
                note="Venue comparator only — not global futures/spot. OI≠bearish rule; mild funding≠top.",
                source="FARTCOIN Stage-1",
                source_url=BINANCE_PERP,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Spot / leverage</h4>"
        '<div class="band-status c-orange">SPOT REAL · LEVERAGE MATERIAL</div>'
        + lines
        + "</div>"
    )


def fartcoin_supply_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    supply = c.get("supply") or {}
    own = c.get("ownership") or {}
    mm = c.get("mm") or {}
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
            "Float clean",
            "Mint / freeze",
            SUPPLY_READ,
            evidence_tip_html(
                name="SUPPLY",
                read=SUPPLY_READ,
                rows=[
                    ("Circ / max", f"{_fmt_n(supply.get('circulating'))} / {_fmt_n(supply.get('max_supply'))}"),
                    ("Mint authority", str(supply.get("mint_authority_status"))),
                    ("Freeze authority", str(supply.get("freeze_authority_status"))),
                ],
                note=supply.get("display_rule") or "",
                source="FARTCOIN Stage-1",
                source_url=CG,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_CIRCLES,
            "Ownership",
            "Holders / MM",
            "OWNERS UNRESOLVED",
            evidence_tip_html(
                name="OWNERSHIP",
                read="RAW HIGH · ADJUSTED UNKNOWN",
                rows=[
                    ("Raw top-20", f"~{own.get('top20_raw_pct')}%"),
                    ("Adjusted discretionary", "UNKNOWN"),
                    ("Wintermute inventory", _fmt_n(mm.get("wintermute_fartcoin"))),
                ],
                note="Do not label raw top-20 as whale control. MM inventory ≠ suppression.",
                source="FARTCOIN Stage-1",
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
        '<div class="band-status c-orange">FLOAT CLEAN · OWNERS UNRESOLVED</div>'
        + ddbar
        + lines
        + "</div>"
    )


def render_fartcoin_evidence_cards(intel: dict[str, Any]) -> str:
    from lib.v3.forensic_cards import evidence_card, evidence_section

    c = _s1(intel)
    own = c.get("ownership") or {}
    lev = c.get("leverage") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    cards = [
        evidence_card(
            title="Float vs ownership",
            read="FLOAT CLEAN · OWNERS OPAQUE",
            copy="Mint/freeze revoked · circ≈max · ownership still opaque.",
            tone="orange",
            status="KNOWN",
            kpis=[("Mint/freeze", "REVOKED"), ("Owners", "OPAQUE")],
            tip_rows=[
                ("Float", "Clean"),
                ("Ownership", "still opaque"),
            ],
            source="FARTCOIN Stage-1",
            as_of=as_of,
            note="Clean float does not mean clean ownership.",
        ),
        evidence_card(
            title="Raw top-20",
            read="NOT A WHALE METRIC",
            copy=f"~{own.get('top20_raw_pct')}% — not labeled discretionary whales.",
            tone="orange",
            status="KNOWN",
            kpis=[("Raw top-20", f"~{own.get('top20_raw_pct')}%")],
            tip_rows=[
                ("Raw top-20", f"~{own.get('top20_raw_pct')}%"),
                ("Label", "not discretionary whales"),
            ],
            source="FARTCOIN Stage-1",
            as_of=as_of,
            note="Do not label raw top-20 as whale control.",
        ),
        evidence_card(
            title="Adjusted owners",
            read="ADJUSTED CONC. UNKNOWN",
            copy="Adjusted discretionary concentration UNKNOWN",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Adjusted discretionary", "UNKNOWN")],
            tip_rows=[("Adjusted discretionary concentration", "UNKNOWN")],
            source="FARTCOIN Stage-1",
            as_of=as_of,
            note="UNKNOWN is honest. Do not fill with raw top-20.",
        ),
        evidence_card(
            title="Leverage comparator",
            read="VENUE ONLY",
            copy=f"~{lev.get('perp_vs_coinbase_spot_ratio')}× Binance perp vs Coinbase spot (venue only)",
            tone="orange",
            status="KNOWN",
            kpis=[("Perp vs CB spot", f"~{lev.get('perp_vs_coinbase_spot_ratio')}×")],
            tip_rows=[
                ("Ratio", f"~{lev.get('perp_vs_coinbase_spot_ratio')}×"),
                ("Scope", "venue only"),
            ],
            source="FARTCOIN Stage-1",
            as_of=as_of,
            note="Venue comparator, not global leverage.",
        ),
        evidence_card(
            title="Creator / early",
            read="STORY UNKNOWN",
            copy="Deployer & early-wallet story UNKNOWN",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Deployer story", "UNKNOWN")],
            tip_rows=[("Deployer & early-wallet", "UNKNOWN")],
            source="FARTCOIN Stage-1",
            as_of=as_of,
            note="Do not invent a creator narrative.",
        ),
        evidence_card(
            title="DEX sample",
            read="BOUNDED SAMPLE",
            copy="Bounded Raydium sample — not market-wide flow.",
            tone="orange",
            status="PARTIAL",
            kpis=[("Scope", "Raydium sample")],
            tip_rows=[("Read", "Bounded Raydium sample — not market-wide flow")],
            source="FARTCOIN Stage-1",
            as_of=as_of,
            note="Not market-wide.",
        ),
        evidence_card(
            title="Wintermute",
            read="SMALL INVENTORY",
            copy="Small inventory observation — not dump/suppression.",
            tone="muted",
            status="KNOWN",
            kpis=[("Claim", "NOT SUPPRESSION")],
            tip_rows=[("Read", "Small inventory observation — not dump/suppression")],
            source="FARTCOIN Stage-1",
            as_of=as_of,
            note="MM inventory ≠ suppression.",
        ),
        evidence_card(
            title="Attention quality",
            read="NO CLEAN SERIES",
            copy="No clean social/reflexivity series.",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Social series", "UNKNOWN")],
            tip_rows=[("Read", "No clean social/reflexivity series")],
            source="FARTCOIN Stage-1",
            as_of=as_of,
            note="Do not invent attention quality.",
        ),
    ]
    return evidence_section(
        cards,
        note="Compact conclusions first. Holders, leverage and method stay in tips underneath.",
    )


def render_fartcoin_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">'
        "Clean float does not mean clean ownership — and leverage can still dominate the tape."
        "</p></div><div class=\"split\">"
        + fartcoin_spot_lev_band(intel)
        + fartcoin_supply_band(intel)
        + "</div></section>"
    )
    return (
        split
        + warning_stack_html(intel)
        + change_mind_section(intel, slug="fartcoin")
        + reality_check_section(intel)
        + render_fartcoin_evidence_cards(intel)
    )


def build_fartcoin_v3_from_packs(report_date: str, v4_report: dict | None = None) -> dict[str, Any]:
    stage1 = load_fartcoin_canonical()
    price = stage1.get("price_structure") or {}
    stance = fartcoin_current_stance()
    assert stance["headline"] == STANCE_HEADLINE
    assert (stage1.get("supply") or {}).get("pressure_read") == SUPPLY_READ
    now_usd = price.get("now_usd")
    price_display = f"~${now_usd:.3f}" if isinstance(now_usd, (int, float)) else "—"
    doc: dict[str, Any] = {
        "meta": {
            "schema": "fartcoin-v3",
            "slug": "fartcoin",
            "report_date": report_date,
            "generated_at": now_iso(),
            "version": "stage1-v1",
            "v4_report_date": (v4_report or {}).get("report_date"),
        },
        "hero": {
            "asset": "FARTCOIN",
            "price_usd": now_usd,
            "price_display": price_display,
            "ath_display": f"${price.get('ath_usd')}",
            "drawdown_pct": price.get("drawdown_pct"),
            "price_as_of": (stage1.get("meta") or {}).get("fetched_at_utc"),
            "thesis": (
                "Clean float does not mean clean ownership — and leverage can still dominate the tape."
            ),
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
            "v3_stance": stance["headline"],
            "v3_stance_note": stance["summary"],
            "confidence": stance["confidence"],
            "data_completeness": (
                "Stage-1 packs wired — adjusted owners UNKNOWN; creator UNKNOWN; "
                "multi-venue OI UNKNOWN; attention quality UNKNOWN."
            ),
        },
        "triad": {
            "lifecycle": {
                "display": "Post-ATH / weak",
                "detail": meaning("fartcoin", price.get("drawdown_pct")),
            },
            "project_health": {
                "display": "FLOAT CLEAN",
                "detail": "Mint/freeze revoked; ownership unresolved — meme, not compute fundamentals.",
            },
            "market_timing": {
                "display": "LEVERAGE MATERIAL",
                "detail": "Binance perp active; spot real elsewhere; confirmation weak.",
            },
        },
        "stage1": stage1,
    }
    doc["asset_top"] = build_fartcoin_asset_top(doc)
    doc["warning_stack"] = build_fartcoin_warning_stack(doc)
    doc["what_would_change_mind"] = build_fartcoin_change_mind(doc)
    doc["reality_check"] = build_fartcoin_reality_check(doc)
    return doc


def write_fartcoin_v3(out_dir: Path | None = None) -> dict[str, Any]:
    report_date = now_iso()[:10]
    doc = build_fartcoin_v3_from_packs(report_date)
    out_dir = out_dir or (REPORTS / report_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "fartcoin-v3.json").write_text(payload, encoding="utf-8")
    (ROOT / "fartcoin-v3.json").write_text(payload, encoding="utf-8")
    return doc
