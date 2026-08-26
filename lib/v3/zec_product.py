"""ZEC V3 product layer — monetary + privacy asset (not compute/BME)."""

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
from lib.v3.current_stance import zec_current_stance
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
from lib.v3.zec_stage1_loader import STANCE_HEADLINE, SUPPLY_READ, load_zec_canonical

CG = "https://www.coingecko.com/en/coins/zcash"
BINANCE_PERP = "https://www.binance.com/en/futures/ZECUSDT"
EXPLORER = "https://mainnet.zcashexplorer.app/api/v1/blockchain-info"
SRC = "ZEC Stage-1 evidence"


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
        return f"~${float(now_usd):,.0f}"
    except (TypeError, ValueError):
        return "—"


def _perp_spot_disp(lev: dict[str, Any]) -> str:
    try:
        return f"{float(lev.get('perp_vs_binance_spot_ratio')):.1f}×"
    except (TypeError, ValueError):
        return "—"


def build_zec_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    c = _s1(doc)
    price = c.get("price_structure") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    spot = c.get("spot_liquidity") or {}
    lev = c.get("leverage") or {}
    supply = c.get("supply") or {}
    priv = c.get("privacy") or {}
    own = c.get("ownership") or {}
    flow = c.get("capital_flow") or {}
    mm = c.get("mm") or {}
    vc = c.get("value_capture") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc") or now_iso()
    now_usd = price.get("now_usd")
    rets = price.get("returns_pct") or {}

    top = empty_asset_top("ZEC", _price_disp(now_usd))
    top["price_as_of"] = as_of

    top["groups"]["market_structure"]["signals"] = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state="1Y EXTREME · NEAR-TERM SOFT",
            display="1Y ~+1,178%",
            light=LIGHT_ORANGE,
            meaning=(
                "Long-window move is extreme. Near-term leadership is weak. Not proof of privacy adoption. "
                + meaning("zec", price.get("drawdown_pct"))
            ),
            evidence=(
                f"ZEC {_price_disp(now_usd)} · mcap {_fmt_usd(price.get('mcap_usd'))} · "
                f"max-supply implied {_fmt_usd(price.get('max_supply_implied_usd'))}. "
                f"Binance 7d {_fmt_pct(rets.get('7'))} · 30d {_fmt_pct(rets.get('30'))} · "
                f"90d {_fmt_pct(rets.get('90'))} · 180d {_fmt_pct(rets.get('180'))}. "
                f"CG 1y {_fmt_pct(price.get('cg_1y_change_pct'))}. "
                f"CG ATH ${price.get('ath_usd')} ({price.get('ath_date')}) is early-market distorted. "
                f"{price.get('valuation_note')}"
            ),
            source="CoinGecko + Binance daily",
            source_url=price.get("source_url_cg") or CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_btc",
            label="vs BTC",
            state="NEAR-TERM WEAK · 90d/180d STRONG",
            display="LAGS BTC 7d/30d",
            light=LIGHT_ORANGE,
            meaning="Priority: 7d/30d/90d. Medium-term leadership real; near-term not.",
            evidence=(
                f"7d {_fmt_pp(rs_btc.get('7'))} · 30d {_fmt_pp(rs_btc.get('30'))} · "
                f"90d {_fmt_pp(rs_btc.get('90'))} · 180d {_fmt_pp(rs_btc.get('180'))}."
            ),
            source="Binance ZEC/BTC daily",
            source_url=price.get("source_url_binance"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_sol",
            label="vs SOL",
            state="NEAR-TERM WEAK · 90d/180d STRONG",
            display="LAGS SOL 7d/30d",
            light=LIGHT_ORANGE,
            meaning="Same windows. Long-window RS is not usage proof.",
            evidence=(
                f"7d {_fmt_pp(rs_sol.get('7'))} · 30d {_fmt_pp(rs_sol.get('30'))} · "
                f"90d {_fmt_pp(rs_sol.get('90'))} · 180d {_fmt_pp(rs_sol.get('180'))}."
            ),
            source="Binance ZEC/SOL daily",
            source_url=price.get("source_url_binance"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["market_structure"]["group_state"] = "NEAR-TERM WEAK · LONG MOVE EXTREME"
    top["groups"]["market_structure"]["group_light"] = LIGHT_ORANGE
    top["groups"]["market_structure"]["title"] = "Price / Market Structure"

    ratio = lev.get("perp_vs_binance_spot_ratio")
    try:
        ratio_txt = f"~{float(ratio):.1f}×"
    except (TypeError, ValueError):
        ratio_txt = "—"

    top["groups"]["capital_flow"]["signals"] = [
        signal(
            signal_id="spot_vs_leverage",
            label="Spot vs Leverage",
            state="LEVERAGE MATERIAL",
            display="BINANCE PERP vs BINANCE SPOT",
            light=LIGHT_ORANGE,
            meaning="Venue comparator only. Not global futures/spot. OI falling ~30d ≠ blow-off.",
            evidence=(
                f"Binance spot {spot.get('binance_spot')} · perp {spot.get('binance_perp')} · "
                f"Coinbase spot {spot.get('coinbase_spot')}. "
                f"Binance OI {_fmt_usd(lev.get('oi_usd_approx'))} · "
                f"perp 24h {_fmt_usd(lev.get('perp_quote_vol_24h'))} · "
                f"spot 24h {_fmt_usd(lev.get('spot_quote_vol_24h'))} · "
                f"ratio {ratio_txt} ({lev.get('ratio_label')}). "
                f"Partial BNB+Bybit+OKX OI {_fmt_usd(lev.get('partial_multi_venue_oi_usd'))}. "
                f"Full global OI {lev.get('multi_venue_oi_aggregate')}. "
                f"{lev.get('note')}"
            ),
            source=SRC,
            source_url=BINANCE_PERP,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="who_is_buying",
            label="Who Is Buying?",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Privacy prevents market-wide buyer quality.",
            evidence=flow.get("note") or "UNKNOWN",
            source=SRC,
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="who_is_selling",
            label="Who Is Selling?",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Miner receipt ≠ dumping. CEX deposit ≠ sale.",
            evidence=own.get("note") or "UNKNOWN",
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
            state="OPAQUE",
            display="OWNERSHIP UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Shielded beneficial ownership is unknowable by design.",
            evidence=(
                f"{own.get('read')} · beneficial {own.get('beneficial_ownership')} · "
                f"transparent whale map {own.get('transparent_whale_map')} · "
                f"MM {mm.get('inventory')} (Solana registry does not apply)."
            ),
            source=SRC,
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="team_dev_ceo",
            label="Issuance / Funding",
            state="FUNDING SPLIT KNOWN · BALANCES UNKNOWN",
            display="NU6 80/8/12",
            light=LIGHT_UNKNOWN,
            meaning="Issuance allocation is protocol; discretionary org balances UNKNOWN.",
            evidence=(
                f"Post-NU6: {(supply.get('issuance_allocation') or {})}. "
                "Lockbox is funding accrual, not privacy stock."
            ),
            source="ECC NU6",
            source_url=supply.get("source_url"),
            as_of=as_of,
            freshness="protocol",
            confidence="HIGH",
            epistemic_status="PARTIAL",
        ),
    ]
    top["groups"]["capital_flow"]["group_state"] = "LEVERAGE MATERIAL · FLOWS OPAQUE"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_ORANGE
    top["groups"]["capital_flow"]["title"] = "Spot / Leverage / Flows"

    pools = priv.get("pools_zec") or {}
    top["groups"]["project_supply"]["signals"] = [
        signal(
            signal_id="project_health",
            label="Privacy / Network",
            state="STOCK MATERIAL · USAGE TREND UNKNOWN",
            display=f"~{priv.get('shielded_pct_of_chain'):.1f}% SHIELDED STOCK"
            if isinstance(priv.get("shielded_pct_of_chain"), (int, float))
            else "SHIELDED STOCK",
            light=LIGHT_GREEN,
            meaning="Stock observation only. Not usage growth. Lockbox is not privacy stock.",
            evidence=(
                f"Shielded ~{_fmt_n(priv.get('shielded_zec'))} ZEC "
                f"(~{priv.get('shielded_pct_of_chain'):.1f}% of chain). "
                f"Transparent {_fmt_n(pools.get('transparent'))} · Ironwood {_fmt_n(pools.get('ironwood'))} · "
                f"Orchard {_fmt_n(pools.get('orchard'))} · Sapling {_fmt_n(pools.get('sapling'))} · "
                f"Sprout {_fmt_n(pools.get('sprout'))} · Lockbox {_fmt_n(priv.get('lockbox_zec'))} (not privacy). "
                f"Tx/24h ~{priv.get('tx_24h')} (mixed types). "
                f"Usage-rate trend {priv.get('usage_rate_trend')}. {priv.get('tx_note')}"
            ),
            source="Zcash Explorer valuePools",
            source_url=priv.get("source_url") or EXPLORER,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="liquidity_absorption",
            label="Liquidity / Access",
            state="MAJOR SPOT PRESENT",
            display="BINANCE + COINBASE SPOT",
            light=LIGHT_GREEN,
            meaning="Current access is not structurally impaired in observed evidence. Forward regulatory path UNKNOWN.",
            evidence=spot.get("note") or "",
            source=SRC,
            source_url=CG,
            as_of=as_of,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="supply_unlocks",
            label="Issuance (not unlock)",
            state=SUPPLY_READ,
            display="~3.9% EST. INFLATION",
            light=LIGHT_ORANGE,
            meaning=(
                "Programmatic mining issuance — not a vesting schedule. "
                "Tooltip: almost 80% circulating; remaining unissued is future issuance, not vesting."
            ),
            evidence=(
                f"Max {_fmt_n(supply.get('max_supply'))} · circ {_fmt_n(supply.get('circulating'))} "
                f"(~{supply.get('circulating_pct_of_max'):.1f}%). "
                f"Remaining unissued ~{supply.get('remaining_unissued_pct'):.1f}%. "
                f"Est. 3m/6m/12m issuance {_fmt_n(supply.get('next_3m_issuance_zec'))} / "
                f"{_fmt_n(supply.get('next_6m_issuance_zec'))} / {_fmt_n(supply.get('next_12m_issuance_zec'))} ZEC. "
                f"Value capture: {vc.get('model')}. Staking no · buyback no. "
                f"{supply.get('display_rule')}"
            ),
            source="CG + ECC NU6",
            source_url=supply.get("source_url"),
            as_of=as_of,
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="DERIVED",
        ),
    ]
    top["groups"]["project_supply"]["group_state"] = "MONETARY-ONLY · SHIELDED STOCK MATERIAL"
    top["groups"]["project_supply"]["group_light"] = LIGHT_GREEN
    top["groups"]["project_supply"]["title"] = "Supply / Privacy / Capture"

    stance = zec_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "explanation": stance["summary"],
        "directional_state": "DESCRIPTIVE",
        "confidence": stance["confidence"],
        "evidence_refs": [],
    }
    return enrich_tooltips(top)


def build_zec_warning_stack(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    priv = c.get("privacy") or {}
    lev = c.get("leverage") or {}
    supply = c.get("supply") or {}
    shielded_pct = priv.get("shielded_pct_of_chain")
    shielded_vis = (
        f"~{float(shielded_pct):.0f}% of chain shielded"
        if isinstance(shielded_pct, (int, float))
        else "~26% of chain shielded"
    )
    infl = supply.get("estimated_annual_inflation_pct")
    infl_vis = f"~{float(infl):.1f}%/yr" if isinstance(infl, (int, float)) else "~3.9%/yr"
    next12_n = supply.get("next_12m_issuance_zec")
    next12 = (
        f"{float(next12_n)/1000:.0f}k"
        if isinstance(next12_n, (int, float)) and float(next12_n) >= 1000
        else _fmt_n(next12_n)
    )
    ratio = lev.get("perp_vs_binance_spot_ratio")
    ratio_vis = f"~{float(ratio):.1f}×" if isinstance(ratio, (int, float)) else "~8.7×"
    cats = [
        technical_trend_category("zec"),
        category_state(
            "shielded_stock",
            "SHIELDED STOCK",
            "CLEAR",
            detail=(
                f"~{_fmt_n(priv.get('shielded_zec'))} ZEC shielded ({shielded_vis}). "
                "Stock, not a usage-rate."
            ),
            summary=shielded_vis,
        ),
        category_state(
            "leverage",
            "LEVERAGE",
            "PARTIAL",
            detail=(
                f"Binance perp/spot {ratio_vis}. {lev.get('ratio_label') or ''} "
                "Global OI UNKNOWN. OI falling over ~30d observed window."
            ),
            summary=f"Binance perp/spot {ratio_vis}",
        ),
        category_state(
            "issuance",
            "ISSUANCE",
            "PARTIAL",
            detail=(
                f"Capped but still inflating. Est. {infl_vis} · next 12m ~{next12} ZEC. "
                "Programmatic mining — not a vest book."
            ),
            summary=f"{infl_vis} · next 12m ~{next12} ZEC",
        ),
        category_state(
            "owners_flows",
            "OWNERS / FLOWS",
            "UNKNOWN",
            detail="Beneficial owners unknowable. Privacy. Do not fake concentration.",
            summary="Beneficial owners unknowable",
        ),
    ]
    return pack_risk_confirmation(cats, SRC)


def build_zec_change_mind(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    priv = c.get("privacy") or {}
    shielded_pct = priv.get("shielded_pct_of_chain")
    constructive = [
        condition(
            condition_id="shielded_absorbs_issuance",
            title="Shielded stock absorbs issuance",
            summary="Shielded share holds or rises as ~3.9%/yr issuance prints — inflation going into privacy stock, not liquid float.",
            status="PARTIAL",
            interpretation="Shielded stock is material. Usage-rate trend is UNKNOWN — stock ≠ proven usage. Expanding stock would confirm the monetary thesis.",
            evidence_rows=[
                ("Shielded stock", f"~{_fmt_n(priv.get('shielded_zec'))} / ~{shielded_pct:.1f}%" if shielded_pct is not None else "—"),
                ("Issuance", "~3.9%/yr · next 12m ~657k ZEC"),
                ("Usage-rate trend", "UNKNOWN"),
            ],
            source=SRC,
            source_url=priv.get("source_url") or EXPLORER,
            as_of="2026-08-13",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
        condition(
            condition_id="holds_50_200_spot",
            title="Holds 50d/200d without perp blowout",
            summary="Spot keeps ZEC above both moving averages while Binance perp/spot cools from ~8.7×.",
            status="PARTIAL",
            interpretation="Already above 50d+200d on spot. Perp/spot still elevated. Structure is confirmation; leverage is the risk.",
            evidence_rows=[
                ("50d / 200d", "Above ~$488 / ~$393 (spot ZECUSDT)"),
                ("Binance perp/spot", "~8.7×"),
                ("Global OI", "UNKNOWN"),
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
            condition_id="stock_falls_issuance_continues",
            title="Shielded share falls as issuance continues",
            summary="Shielded stock stagnates or falls while programmatic issuance keeps adding ZEC.",
            status="WATCH",
            interpretation="Would mean inflation is not being absorbed into privacy stock — the monetary thesis weakens.",
            evidence_rows=[
                ("Shielded share now", f"~{shielded_pct:.1f}%" if shielded_pct is not None else "—"),
                ("Discipline", "Stock ≠ usage"),
            ],
            source=SRC,
            source_url=priv.get("source_url") or EXPLORER,
            as_of="2026-08-13",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
        condition(
            condition_id="loses_50d_leverage_carries",
            title="Loses 50d while leverage stays elevated",
            summary="Price loses the 50-day while Binance perp/spot stays elevated.",
            status="WATCH",
            interpretation="Would show leverage carrying a structure that just failed. Global OI remains UNKNOWN.",
            evidence_rows=[
                ("50d now", "Still above"),
                ("Perp/spot", "~8.7×"),
                ("Global OI", "UNKNOWN"),
            ],
            source=SRC,
            source_url=BINANCE_PERP,
            as_of="2026-08-13",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
    ]
    return pack_change_mind(constructive, defensive, schema_version=1)


def build_zec_reality_check(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    lev = c.get("leverage") or {}
    supply = c.get("supply") or {}
    priv = c.get("privacy") or {}
    rc = empty_reality_check()
    rc["priority_headline"] = "SHIELDED STOCK ≠ SHIELDED USAGE"
    rc["known"] = [
        rc_item(
            item_id="identity",
            title="Identity + extreme 1y tape",
            summary=(
                f"Zcash L1 · {_price_disp(price.get('now_usd'))} · mcap {_fmt_usd(price.get('mcap_usd'))} · "
                f"1y {_fmt_pct(price.get('cg_1y_change_pct'))}."
            ),
            evidence_rows=[
                ("Max-supply implied", _fmt_usd(price.get("max_supply_implied_usd"))),
                ("CG FDV field", f"{_fmt_usd(price.get('cg_fdv_usd'))} ≈ mcap — not 21M FDV"),
            ],
            interpretation="Long-window price is extreme. Not usage proof.",
            priority="HIGH",
            source=SRC,
            source_url=CG,
            as_of="2026-08-13",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="shielded_stock",
            title="Shielded stock material",
            summary=(
                f"~{_fmt_n(priv.get('shielded_zec'))} ZEC · "
                f"~{priv.get('shielded_pct_of_chain'):.1f}% of chain. Snapshot, not a trend."
            ),
            evidence_rows=[
                ("Ironwood / Orchard", f"{_fmt_n((priv.get('pools_zec') or {}).get('ironwood'))} / {_fmt_n((priv.get('pools_zec') or {}).get('orchard'))}"),
                ("Lockbox", "Funding pool — not privacy stock"),
            ],
            interpretation="Capability real. Usage-rate trend UNKNOWN.",
            priority="HIGH",
            source=SRC,
            source_url=priv.get("source_url") or EXPLORER,
            as_of="2026-08-13",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="issuance",
            title="Capped but still inflating",
            summary=(
                f"~{supply.get('circulating_pct_of_max'):.1f}% circulating · "
                f"est. inflation ~{supply.get('estimated_annual_inflation_pct'):.1f}% · issuance ≠ unlock."
            ),
            evidence_rows=[
                ("Next 12m issuance est.", _fmt_n(supply.get("next_12m_issuance_zec")) + " ZEC"),
                ("NU6 split", "80% miners / 8% ZCG / 12% lockbox"),
            ],
            interpretation="Monetary scarcity is incomplete — still programmatic issuance.",
            priority="HIGH",
            source=SRC,
            source_url=supply.get("source_url"),
            as_of="2026-08-13",
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="DERIVED",
        ),
        rc_item(
            item_id="leverage_access",
            title="Spot live · leverage material",
            summary=(
                f"Spot live · OI {_fmt_usd(lev.get('oi_usd_approx'))} · "
                f"perp/spot ~{_perp_spot_disp(lev)}."
            ),
            evidence_rows=[
                ("Label", lev.get("ratio_label") or ""),
                ("Global OI", "UNKNOWN"),
            ],
            interpretation="Access not impaired today. Leverage is part of structure. OI down ~30d.",
            priority="HIGH",
            source=SRC,
            source_url=BINANCE_PERP,
            as_of="2026-08-13",
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    rc["suggests"] = [
        rc_item(
            item_id="s1",
            title="Privacy capability + stock are real",
            summary="A material share of supply sits in shielded pools today.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s2",
            title="Price already moved a long way",
            summary="1y extreme; modest throughput. Not a measured lag.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s3",
            title="Holder case is monetary, not cash-flow",
            summary="No staking/buyback/revenue→token. Absence ≠ bearish.",
            epistemic_status="INTERPRETATION",
        ),
        rc_item(
            item_id="s4",
            title="Ownership forensics stay limited",
            summary="Opacity is a product feature and a research limit.",
            epistemic_status="INTERPRETATION",
        ),
    ]
    rc["unknowns"] = [
        rc_item(item_id="u1", title="Shielded transaction-share time series", summary="History probe failed. Stock ≠ usage.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u2", title="Fee economics / value capture", summary="Blockchair fee USD unreliable.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u3", title="Beneficial ownership", summary="Shielded balances unknowable by design.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u4", title="Market-wide buyers/sellers", summary="TRANSFER ≠ SALE.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u5", title="ZEC MM inventories", summary="Solana registry N/A. Absence ≠ zero.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u6", title="Full multi-venue OI", summary="Partial BNB+Bybit+OKX is not global.", epistemic_status="UNKNOWN"),
        rc_item(item_id="u7", title="Forward regulatory / listing path", summary="Current access ≠ future access.", epistemic_status="UNKNOWN"),
    ]
    return rc


def zec_spot_lev_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    spot = c.get("spot_liquidity") or {}
    lev = c.get("leverage") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    try:
        ratio_txt = f"~{float(lev.get('perp_vs_binance_spot_ratio')):.1f}×"
    except (TypeError, ValueError):
        ratio_txt = "—"
    lines = (
        mline_tip(
            ICON_GRID,
            "Spot access",
            "Binance + Coinbase",
            "SPOT PRESENT",
            evidence_tip_html(
                name="SPOT / ACCESS",
                read="MAJOR SPOT NOT STRUCTURALLY IMPAIRED",
                rows=[
                    ("Binance spot", str(spot.get("binance_spot"))),
                    ("Binance perp", str(spot.get("binance_perp"))),
                    ("Coinbase spot", str(spot.get("coinbase_spot"))),
                ],
                note="Historical privacy-coin fear ≠ current observed access failure. Forward path UNKNOWN.",
                source=SRC,
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
                    ("Binance OI", _fmt_usd(lev.get("oi_usd_approx"))),
                    ("Perp 24h", _fmt_usd(lev.get("perp_quote_vol_24h"))),
                    ("Spot 24h", _fmt_usd(lev.get("spot_quote_vol_24h"))),
                    ("Perp vs Binance spot", ratio_txt),
                    ("Label", lev.get("ratio_label") or ""),
                    ("Global OI", "UNKNOWN"),
                ],
                note="Venue comparator only. OI down ~30d — not a clean expanding blow-off. Mild funding ≠ top.",
                source=SRC,
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
        '<div class="band-status c-orange">SPOT PRESENT · LEVERAGE MATERIAL</div>'
        + lines
        + "</div>"
    )


def zec_supply_privacy_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    supply = c.get("supply") or {}
    priv = c.get("privacy") or {}
    vc = c.get("value_capture") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    lines = (
        mline_tip(
            ICON_DROP,
            "Issuance",
            "Not an unlock",
            "INFLATING · PROGRAMMATIC",
            evidence_tip_html(
                name="SUPPLY / ISSUANCE",
                read=SUPPLY_READ,
                rows=[
                    ("Circ / max", f"{_fmt_n(supply.get('circulating'))} / {_fmt_n(supply.get('max_supply'))}"),
                    ("Circulating %", f"~{supply.get('circulating_pct_of_max'):.1f}%"),
                    ("Est. inflation", f"~{supply.get('estimated_annual_inflation_pct'):.1f}%"),
                    ("Next 12m issuance", _fmt_n(supply.get("next_12m_issuance_zec")) + " ZEC"),
                ],
                note=supply.get("display_rule") or "",
                source=SRC,
                source_url=supply.get("source_url"),
                as_of=as_of,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_NODES,
            "Shielded stock",
            "Snapshot",
            "MATERIAL · USAGE UNKNOWN",
            evidence_tip_html(
                name="PRIVACY STOCK",
                read=str(priv.get("read") or ""),
                rows=[
                    ("Shielded", f"{_fmt_n(priv.get('shielded_zec'))} (~{priv.get('shielded_pct_of_chain'):.1f}%)"),
                    ("Tx/24h", str(priv.get("tx_24h"))),
                    ("Usage-rate trend", "UNKNOWN"),
                ],
                note="Usage-rate trend UNKNOWN. Stock is a snapshot. Lockbox is not privacy stock.",
                source=SRC,
                source_url=priv.get("source_url") or EXPLORER,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_CIRCLES,
            "Value capture",
            "Monetary / privacy",
            "NOT CASH-FLOW",
            evidence_tip_html(
                name="VALUE CAPTURE",
                read=str(vc.get("model") or ""),
                rows=[
                    ("Staking", "No"),
                    ("Buyback", "No"),
                    ("Revenue→token", "No"),
                    ("Fee economics", "UNKNOWN"),
                ],
                note=vc.get("note") or "",
                source=SRC,
                source_url=CG,
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Supply / privacy / capture</h4>"
        '<div class="band-status c-green">STOCK MATERIAL · MONETARY-ONLY</div>'
        + lines
        + "</div>"
    )


def render_zec_evidence_cards(intel: dict[str, Any]) -> str:
    from lib.v3.forensic_cards import evidence_card, evidence_section

    c = _s1(intel)
    priv = c.get("privacy") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    cards = [
        evidence_card(
            title="Shielded stock",
            read="MATERIAL SNAPSHOT",
            copy="~26% of chain — snapshot, not a usage trend.",
            tone="green",
            status="KNOWN",
            kpis=[
                ("Shielded", f"~{priv.get('shielded_pct_of_chain')}%"),
                ("Usage trend", "UNKNOWN"),
            ],
            tip_rows=[
                ("Shielded", f"{_fmt_n(priv.get('shielded_zec'))} (~{priv.get('shielded_pct_of_chain'):.1f}%)" if priv.get("shielded_pct_of_chain") is not None else "~26%"),
                ("Usage-rate trend", "UNKNOWN"),
            ],
            source=SRC,
            source_url=priv.get("source_url") or EXPLORER,
            as_of=as_of,
            note="Stock is a snapshot. Lockbox is not privacy stock.",
        ),
        evidence_card(
            title="1y price",
            read="EXTREME MOVE",
            copy="Extreme move. Not proof of privacy adoption.",
            tone="orange",
            status="KNOWN",
            kpis=[("Privacy proof", "NO")],
            tip_rows=[("Read", "Extreme move. Not proof of privacy adoption.")],
            source=SRC,
            as_of=as_of,
            note="Price move ≠ measured usage lag proof.",
        ),
        evidence_card(
            title="Spot access",
            read="MAJOR SPOT PRESENT",
            copy="Binance + Coinbase present now.",
            tone="green",
            status="KNOWN",
            kpis=[("Binance", "SPOT"), ("Coinbase", "SPOT")],
            tip_rows=[("Binance + Coinbase", "present now")],
            source=SRC,
            as_of=as_of,
            note="Historical privacy-coin fear ≠ current observed access failure.",
        ),
        evidence_card(
            title="Owners / MM / flows",
            read="OPAQUE",
            copy="UNKNOWN — Solana MM registry does not apply.",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Owners", "UNKNOWN"), ("MM", "N/A")],
            tip_rows=[("Solana MM registry", "does not apply")],
            source=SRC,
            as_of=as_of,
            note="Do not import Solana MM reads onto ZEC.",
        ),
        evidence_card(
            title="Usage-rate series",
            read="TREND UNKNOWN",
            copy="UNKNOWN — history probe failed.",
            tone="muted",
            status="UNKNOWN",
            kpis=[("Usage-rate series", "UNKNOWN")],
            tip_rows=[("History probe", "failed")],
            source=SRC,
            as_of=as_of,
            note="Do not invent a usage-rate trend.",
        ),
        evidence_card(
            title="Issuance",
            read="PROGRAMMATIC",
            copy="Programmatic — not a vesting unlock.",
            tone="orange",
            status="KNOWN",
            kpis=[("Type", "ISSUANCE"), ("Unlock", "NO")],
            tip_rows=[("Read", SUPPLY_READ)],
            source=SRC,
            as_of=as_of,
            note="Issuance is not an unlock.",
        ),
    ]
    return evidence_section(
        cards,
        note="Compact conclusions first. Shielded stock, access and method stay in tips underneath.",
    )


def render_zec_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">'
        "Shielded stock is not shielded usage. Monetary capture is not cash-flow capture. "
        "Issuance is not an unlock."
        "</p></div><div class=\"split\">"
        + zec_spot_lev_band(intel)
        + zec_supply_privacy_band(intel)
        + "</div></section>"
    )
    return (
        split
        + warning_stack_html(intel)
        + change_mind_section(intel, slug="zec")
        + reality_check_section(intel)
        + render_zec_evidence_cards(intel)
    )


def build_zec_v3_from_packs(report_date: str, v4_report: dict | None = None) -> dict[str, Any]:
    stage1 = load_zec_canonical()
    price = stage1.get("price_structure") or {}
    stance = zec_current_stance()
    assert stance["headline"] == STANCE_HEADLINE
    assert (stage1.get("supply") or {}).get("pressure_read") == SUPPLY_READ
    now_usd = price.get("now_usd")
    doc: dict[str, Any] = {
        "meta": {
            "schema": "zec-v3",
            "slug": "zec",
            "report_date": report_date,
            "generated_at": now_iso(),
            "version": "stage1-v1",
            "v4_report_date": (v4_report or {}).get("report_date"),
        },
        "hero": {
            "asset": "ZEC",
            "price_usd": now_usd,
            "price_display": _price_disp(now_usd),
            "ath_display": f"${price.get('ath_usd')}",
            "drawdown_pct": price.get("drawdown_pct"),
            "price_as_of": (stage1.get("meta") or {}).get("fetched_at_utc"),
            "thesis": (
                "Shielded stock is not shielded usage. Monetary capture is not cash-flow capture."
            ),
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
            "v3_stance": stance["headline"],
            "v3_stance_note": stance["summary"],
            "confidence": stance["confidence"],
            "data_completeness": (
                "Stage-1 packs wired — usage-rate UNKNOWN; owners/flows/MM UNKNOWN; "
                "global OI UNKNOWN; CG FDV is not 21M FDV."
            ),
        },
        "triad": {
            "lifecycle": {
                "display": "Price move extreme",
                "detail": "1y ~+1,178%; near-term RS vs BTC/SOL weak.",
            },
            "project_health": {
                "display": "Monetary-only capture",
                "detail": "No staking/buyback/revenue→token. Issuance programmatic, not unlock.",
            },
            "market_timing": {
                "display": "Leverage material",
                "detail": "Binance perp vs Binance spot comparator; global OI UNKNOWN.",
            },
        },
        "stage1": stage1,
    }
    doc["asset_top"] = build_zec_asset_top(doc)
    doc["warning_stack"] = build_zec_warning_stack(doc)
    doc["what_would_change_mind"] = build_zec_change_mind(doc)
    doc["reality_check"] = build_zec_reality_check(doc)
    return doc


def write_zec_v3(out_dir: Path | None = None) -> dict[str, Any]:
    report_date = "2026-08-13"
    doc = build_zec_v3_from_packs(report_date)
    payload = json.dumps(doc, indent=2)
    out_dir = out_dir or (ROOT / "reports" / report_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "zec-v3.json").write_text(payload, encoding="utf-8")
    (ROOT / "zec-v3.json").write_text(payload, encoding="utf-8")
    return doc
