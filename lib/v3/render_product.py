"""RENDER V3 product layer — asset_top, warnings, WCM, Reality Check, evidence cards.

Uses canonical Stage-1 completion packs only. Adapt PUMP/SOL visual system.
No score. No BUY/SELL. No Wintermute warning.
"""

from __future__ import annotations

from typing import Any

from lib.v3.ath_frame import meaning, rc_title, retrace_label, timing_caption
from lib.v3.asset_top import (
    LIGHT_GREEN,
    LIGHT_ORANGE,
    LIGHT_UNKNOWN,
    empty_asset_top,
    enrich_tooltips,
    signal,
)
from lib.v3.change_mind import condition, pack_change_mind
from lib.v3.current_stance import render_current_stance
from lib.v3.fields import category_state, pack_risk_confirmation, now_iso
from lib.v3.sma_trend import technical_trend_category
from lib.v3.reality_check import empty_reality_check, rc_item
from lib.v3.route_d_shell import (
    ICON_BAG,
    ICON_BARS,
    ICON_CIRCLES,
    ICON_DROP,
    ICON_GRID,
    ICON_LEVERAGE,
    ICON_NODES,
    ICON_RATIO,
    evidence_tip_html,
    mline_tip,
    reality_check_section,
    warning_stack_html,
)
from lib.v3.render_stage1_loader import load_render_canonical


def _fmt_pp(v: Any) -> str:
    try:
        return f"{float(v):+.2f}pp"
    except (TypeError, ValueError):
        return "—"


def _fmt_k(v: Any) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.1f}k"
    return f"{n:,.0f}"


def _fmt_m(v: Any) -> str:
    try:
        return f"{float(v) / 1_000_000:.2f}M"
    except (TypeError, ValueError):
        return "—"


def _s1(intel: dict) -> dict:
    return intel.get("stage1") or {}


def build_render_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    c = doc.get("stage1") or {}
    price = c.get("price_structure") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    deriv = c.get("derivatives") or {}
    net = c.get("network") or {}
    bme = c.get("bme") or {}
    supply = c.get("supply") or {}
    bs = c.get("buyer_seller") or {}
    wm = c.get("wintermute") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc") or now_iso()
    now_usd = price.get("now_usd")
    price_disp = f"~${now_usd:,.2f}" if isinstance(now_usd, (int, float)) else "—"

    top = empty_asset_top("RENDER", price_disp)
    top["price_as_of"] = as_of

    last4 = bme.get("last4") or {}
    market_signals = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state="WEAK",
            display=retrace_label(price.get("drawdown_pct")),
            light=LIGHT_ORANGE,
            meaning=meaning("render", price.get("drawdown_pct")),
            evidence=(
                f"RENDER ${now_usd} · ATH ${price.get('ath_usd')} · ~{price.get('drawdown_pct')}% · "
                f"7d {price.get('change_7d_pct')}% · 30d {price.get('change_30d_pct')}% · "
                f"1y {price.get('change_1y_pct')}%."
            ),
            source="Binance + CoinGecko",
            source_url="https://www.coingecko.com/en/coins/render-token",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_btc",
            label="vs BTC",
            state="LAGGING",
            display="LAGGING",
            light=LIGHT_ORANGE,
            meaning="Relative strength vs Bitcoin (RENDER return minus BTC return).",
            evidence=(
                f"7d {_fmt_pp(rs_btc.get('7'))} · 30d {_fmt_pp(rs_btc.get('30'))} · "
                f"90d {_fmt_pp(rs_btc.get('90'))}."
            ),
            source="Binance daily closes",
            source_url="https://api.binance.com/api/v3/klines?symbol=RENDERUSDT&interval=1d",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_sol",
            label="vs SOL",
            state="LAGGING",
            display="LAGGING",
            light=LIGHT_ORANGE,
            meaning="Relative strength vs Solana.",
            evidence=(
                f"7d {_fmt_pp(rs_sol.get('7'))} · 30d {_fmt_pp(rs_sol.get('30'))} · "
                f"90d {_fmt_pp(rs_sol.get('90'))}."
            ),
            source="Binance daily closes",
            source_url="https://api.binance.com/api/v3/klines?symbol=RENDERUSDT&interval=1d",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["market_structure"]["signals"] = market_signals
    top["groups"]["market_structure"]["group_state"] = "WEAK · LAGGING"
    top["groups"]["market_structure"]["group_light"] = LIGHT_ORANGE

    capital_signals = [
        signal(
            signal_id="spot_vs_leverage",
            label="Spot vs Leverage",
            state=deriv.get("read") or "LEVERAGE PRESENT",
            display=deriv.get("read") or "LEVERAGE PRESENT",
            light=LIGHT_ORANGE,
            meaning="Binance futures vs spot activity — not a whole-market verdict.",
            evidence=(
                f"Fut/spot ~{deriv.get('fut_spot_ratio')}× · OI ~${_fmt_k(deriv.get('oi_notional_usd'))} · "
                f"~{deriv.get('oi_vs_30d_max_pct')}% of 30d OI max · funding slightly negative "
                f"(~{deriv.get('funding_pctile_100')}th pctile). {deriv.get('note','')}"
            ),
            source="Binance RENDERUSDT",
            source_url="https://www.binance.com/en/futures/RENDERUSDT",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="who_is_buying",
            label="Who Is Buying?",
            state=bs.get("classification") or "REAL BUYING · CONCENTRATED",
            display=bs.get("classification") or "REAL BUYING · CONCENTRATED",
            light=LIGHT_ORANGE,
            meaning="Bounded Solana DEX SWAP sample — not market-wide.",
            evidence=(
                f"~{bs.get('span_hours')}h · {bs.get('swap_tx_count')} swaps · "
                f"{bs.get('unique_buyers')} buyers · {bs.get('net_accumulators')} net accumulators · "
                f"~{_fmt_k(bs.get('gross_buy'))} RENDER gross buys · "
                f"top-5 ~{bs.get('top5_buy_share_pct')}% · top-10 ~{bs.get('top10_buy_share_pct')}% · "
                f"{bs.get('repeat_buyers')} repeat buyers ~{bs.get('repeat_buyer_share_pct')}% of gross. "
                f"Limits: {'; '.join((bs.get('limitations') or [])[:4])}."
            ),
            source=bs.get("source"),
            source_url=bs.get("source_url"),
            as_of=bs.get("gathered_at_utc") or as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="who_is_selling",
            label="Who Is Selling?",
            state=bs.get("seller_read") or "MIXED / PARTIAL",
            display=bs.get("seller_read") or "MIXED / PARTIAL",
            light=LIGHT_ORANGE,
            meaning="Observed DEX sellers in the same bounded window.",
            evidence=(
                f"{bs.get('unique_sellers')} sellers · {bs.get('net_distributors')} net distributors · "
                f"~{_fmt_k(bs.get('gross_sell'))} gross sell · top-5 ~{bs.get('top5_sell_share_pct')}%. "
                f"Buys slightly exceeded sells in sample. CEX sellers UNKNOWN."
            ),
            unknown="CEX spot sellers invisible.",
            source=bs.get("source"),
            source_url=bs.get("source_url"),
            as_of=bs.get("gathered_at_utc") or as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="whales_major_holders",
            label="Whales / Major Holders",
            state=bs.get("whales_read") or "UNKNOWN / PARTIAL",
            display=bs.get("whales_read") or "UNKNOWN / PARTIAL",
            light=LIGHT_UNKNOWN,
            meaning="No full labelled whale map beyond sample intersections.",
            evidence=(
                f"Wintermute OTC MfDu… two-way MM churn in sample "
                f"(buy ~{_fmt_k(wm.get('gross_buy'))} / sell ~{_fmt_k(wm.get('gross_sell'))} / "
                f"still holds ~{_fmt_k(wm.get('balance'))}). Read: {wm.get('read')}. "
                f"{' · '.join(wm.get('discipline') or [])}."
            ),
            unknown="Broader whale / foundation directional flows not verified.",
            source="Shared MM registry ∩ Helius sample",
            source_url="https://solscan.io/account/MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa",
            as_of=as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
    ]
    top["groups"]["capital_flow"]["signals"] = capital_signals
    top["groups"]["capital_flow"]["group_state"] = "PARTIAL / MIXED"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_ORANGE

    health_signals = [
        signal(
            signal_id="network_usage",
            label="Network Usage",
            state=net.get("usage_read") or "REAL USAGE",
            display=net.get("usage_read") or "REAL USAGE",
            light=LIGHT_GREEN,
            meaning="Structural network activity — not a token-price timing signal.",
            evidence=(
                f"Cumulative frames ~{_fmt_m(net.get('frames_cumulative')).replace('M','')}M · "
                f"{net.get('nodes_label')}: {net.get('nodes_since_inception')}."
            ),
            source="Render Foundation dashboard",
            source_url=net.get("source_url"),
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="bme_value_capture",
            label="Burn vs Emissions (BME)",
            state=bme.get("read") or "RECENT BME NET INFLATIONARY",
            display=bme.get("read") or "RECENT BME NET INFLATIONARY",
            light=LIGHT_ORANGE,
            meaning=bme.get("simple_english") or "",
            evidence=(
                f"Last 4 epochs: burned ~{_fmt_k(last4.get('burned'))} vs node emissions "
                f"~{_fmt_k(last4.get('node_emissions'))} (ratio ~{float(last4.get('ratio') or 0):.2f}). "
                f"Last 8 near-balance (~{float((bme.get('last8') or {}).get('ratio') or 0):.2f}) "
                f"distorted by one ~62k burn spike. Cumulative burned ~{_fmt_m(bme.get('cumulative_burned'))}. "
                f"Node-operator due ~{_fmt_k(bme.get('node_operator_due_per_epoch'))}/epoch. "
                f"{bme.get('availability_note','')}"
            ),
            source="Foundation first-party API (infra.shikumi.cc)",
            source_url=(bme.get("source_urls") or [None])[0],
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="supply_migration",
            label="Supply / Migration",
            state="PARTIAL",
            display="PARTIAL",
            light=LIGHT_ORANGE,
            meaning=supply.get("display_rule") or "",
            evidence=(
                f"Solana supply ~{_fmt_m(supply.get('solana_supply'))} · "
                f"Solana circ ~{_fmt_m(supply.get('solana_circulating'))} · "
                f"legacy ETH RNDR ~{_fmt_m(supply.get('ethereum_rndr'))} · "
                f"Foundation circ ~{_fmt_m(supply.get('foundation_circulating'))} · "
                f"CG circ ~{_fmt_m(supply.get('cg_circulating'))} · "
                f"max {supply.get('max_supply'):,}."
            ),
            unknown="Foundation-vs-CG circulating formula not fully reconciled.",
            source="Foundation supplyInfo + CoinGecko reference",
            source_url=supply.get("source_url"),
            as_of=as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
    ]
    top["groups"]["project_supply"]["signals"] = health_signals
    top["groups"]["project_supply"]["group_state"] = "REAL USAGE · RECENTLY INFLATIONARY"
    top["groups"]["project_supply"]["group_light"] = LIGHT_ORANGE
    top["groups"]["project_supply"]["title"] = "Network / Tokenomics"

    stance = render_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "summary": stance["summary"],
        "confidence": stance["confidence"],
    }
    return enrich_tooltips(top)


def build_render_warning_stack(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    bme = c.get("bme") or {}
    bs = c.get("buyer_seller") or {}
    supply = c.get("supply") or {}
    last4 = bme.get("last4") or {}
    ratio = float(last4.get("ratio") or 0)

    cats = [
        technical_trend_category("render"),
        category_state(
            "burn_vs_emissions",
            "BURN VS EMISSIONS",
            "PARTIAL",
            detail=(
                f"Last 4 epochs burned ~{_fmt_k(last4.get('burned'))} vs node emissions "
                f"~{_fmt_k(last4.get('node_emissions'))} (ratio ~{ratio:.2f}). "
                "Net inflationary on current window. Not annualised."
            ),
            summary=f"Last 4 weeks burn/emit ~{ratio:.2f}",
        ),
        category_state(
            "network_usage",
            "NETWORK USAGE",
            "CLEAR",
            detail="Work still burns RENDER via BME. Confirms usage, not scarcity.",
            summary="BME burns are real",
        ),
        category_state(
            "buyer_quality",
            "BUYER QUALITY",
            "PARTIAL",
            detail=(
                f"Top-5 ~{bs.get('top5_buy_share_pct')}% of ~{bs.get('span_hours')}h principal-pool gross buys "
                f"({bs.get('unique_buyers')} buyers). Packed top-5 share high in bounded sample."
            ),
            summary="DEX buys concentrated",
        ),
        category_state(
            "circulating",
            "CIRCULATING",
            "UNKNOWN",
            detail=(
                supply.get("display_rule")
                or "Foundation / CG / Solana-only circulating defs CONFLICT. Do not average."
            ),
            summary="Circ defs CONFLICT",
        ),
    ]
    return pack_risk_confirmation(cats, "RENDER Stage-1 completion packs")


def build_render_change_mind(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    bme = c.get("bme") or {}
    last4 = bme.get("last4") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")

    constructive = [
        condition(
            condition_id="burns_catch_emissions",
            title="Burns catch or exceed emissions",
            summary="Verified RENDER burns move to or above node-operator emissions — usage starts tightening float.",
            status="NO",
            interpretation=f"Last-4 burn/emit ratio ~{float(last4.get('ratio') or 0):.2f}. Usage is real; scarcity is not.",
            evidence_rows=[
                ("Last-4 burned", _fmt_k(last4.get("burned"))),
                ("Last-4 node emissions", _fmt_k(last4.get("node_emissions"))),
                ("Ratio", f"{float(last4.get('ratio') or 0):.2f}"),
            ],
            source="Foundation first-party BME",
            source_url="https://infra.shikumi.cc/api/v1/epochBurnStats",
            as_of=as_of,
            confidence="HIGH",
            epistemic_status="KNOWN",
            icon="up",
        ),
        condition(
            condition_id="broader_bid_reclaims_50d",
            title="Less-concentrated bid reclaims 50d",
            summary="Spot buying broadens beyond a packed top-5 while price reclaims and holds the 50-day.",
            status="NO",
            interpretation="DEX sample is still concentrated; structure remains below 50d/200d. RS lag alone is not the falsifier.",
            evidence_rows=[
                ("Buyer read", "REAL BUYING · CONCENTRATED"),
                ("Structure", "Below 50d ~$1.45 and 200d ~$1.65"),
            ],
            source="Helius sample + Binance RENDERUSDT",
            source_url="https://api.binance.com/api/v3/klines?symbol=RENDERUSDT&interval=1d",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
    ]
    defensive = [
        condition(
            condition_id="emissions_stay_above",
            title="Emissions keep exceeding burns",
            summary="Node-operator emissions continue materially above verified burns — net new RENDER keeps hitting float.",
            status="YES",
            interpretation="Recent measured window is net inflationary. That is the token consequence of usage without scarcity.",
            evidence_rows=[("Last-4 ratio", f"{float(last4.get('ratio') or 0):.2f}")],
            source="Foundation BME",
            source_url="https://infra.shikumi.cc/api/v1/epochBurnStats",
            as_of=as_of,
            confidence="HIGH",
            epistemic_status="KNOWN",
            icon="warn",
        ),
        condition(
            condition_id="concentrated_bid_no_reclaim",
            title="Bid stays concentrated; 50d not reclaimed",
            summary="Observed buying remains packed in a few wallets and price fails to reclaim the 50-day.",
            status="YES",
            interpretation="Demand quality is not broadening and structure is not repairing.",
            evidence_rows=[
                ("Buyer read", "REAL BUYING · CONCENTRATED"),
                ("50d / 200d", "Price below both"),
            ],
            source="Helius sample + Binance daily",
            source_url="https://api.binance.com/api/v3/klines?symbol=RENDERUSDT&interval=1d",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
    ]
    return pack_change_mind(constructive, defensive)


def build_render_reality_check(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    price = c.get("price_structure") or {}
    net = c.get("network") or {}
    bme = c.get("bme") or {}
    bs = c.get("buyer_seller") or {}
    supply = c.get("supply") or {}
    rs_btc = c.get("rs_vs_btc_pp") or {}
    rs_sol = c.get("rs_vs_sol_pp") or {}
    last4 = bme.get("last4") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")

    rc = empty_reality_check()
    rc["priority_headline"] = (
        "Useful network ≠ automatically good token economics."
    )
    rc["known"] = [
        rc_item(
            item_id="network_real",
            title="Network usage is measurable and real",
            summary=f"Cumulative frames ~{_fmt_m(net.get('frames_cumulative'))}; BME mechanism burns RENDER for jobs.",
            evidence_rows=[
                ("Frames", _fmt_m(net.get("frames_cumulative"))),
                ("Nodes label", net.get("nodes_label") or ""),
            ],
            interpretation="Structural usage evidence — not a price timing signal.",
            priority="HIGH",
            source="Render Foundation",
            source_url=net.get("source_url"),
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
        ),
        rc_item(
            item_id="price_rs_weak",
            title=rc_title("render", price.get("drawdown_pct")),
            summary=(
                f"~${price.get('now_usd')} · ~{price.get('drawdown_pct')}% from ATH · "
                f"BTC 30d {_fmt_pp(rs_btc.get('30'))} · SOL 30d {_fmt_pp(rs_sol.get('30'))}"
            ),
            interpretation=meaning("render", price.get("drawdown_pct")),
            priority="HIGH",
            source="Binance + CoinGecko",
            source_url="https://www.coingecko.com/en/coins/render-token",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
        ),
        rc_item(
            item_id="bme_net_inflationary",
            title="Recent first-party BME is net inflationary",
            summary=(
                f"Last 4 epochs burned ~{_fmt_k(last4.get('burned'))} vs "
                f"~{_fmt_k(last4.get('node_emissions'))} node emissions (ratio ~{float(last4.get('ratio') or 0):.2f})."
            ),
            interpretation="8-epoch near-balance is spike-distorted — recent epochs weaker.",
            priority="HIGH",
            source="Foundation API",
            source_url="https://infra.shikumi.cc/api/v1/epochBurnStats",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
        ),
        rc_item(
            item_id="dex_buying_concentrated",
            title="Bounded Solana DEX buying is real but concentrated",
            summary=(
                f"{bs.get('swap_tx_count')} swaps · {bs.get('unique_buyers')} buyers · "
                f"top-5 ~{bs.get('top5_buy_share_pct')}% of gross buys."
            ),
            priority="MEDIUM",
            source="Helius sample",
            source_url=bs.get("source_url"),
            as_of=bs.get("gathered_at_utc") or as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
    ]
    rc["suggests"] = [
        rc_item(
            item_id="product_vs_token",
            title="Network/product can survive weak token price",
            summary="Usage evidence and weak market structure can coexist.",
            interpretation="Do not treat network health as automatic token confirmation.",
            priority="HIGH",
            source="Render Foundation + CoinGecko",
            source_url=net.get("source_url") or "https://stats.renderfoundation.com/",
            as_of=as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="INFERRED",
        ),
        rc_item(
            item_id="no_clear_scarcity",
            title="Usage not producing recent token scarcity",
            summary="Burns well below node emissions in the recent window.",
            source="Foundation first-party BME",
            source_url="https://infra.shikumi.cc/api/v1/epochBurnStats",
            as_of=as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="INFERRED",
        ),
        rc_item(
            item_id="demand_not_broad",
            title="Capital demand exists but is not broad",
            summary="DEX bid concentrated — not market-wide accumulation.",
            source="Helius sample",
            source_url=bs.get("source_url"),
            as_of=bs.get("gathered_at_utc") or as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="INFERRED",
        ),
    ]
    rc["unknowns"] = [
        rc_item(
            item_id="cex_identity",
            title="Full CEX buyer/seller identity",
            summary="CEX spot legs invisible in the Solana DEX sample.",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="circ_formula",
            title="Foundation vs CG circulating formula",
            summary="SPL / ETH RNDR / market circ are different views — do not add.",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="usdc_burn_lag",
            title="USDC burn accounting vs RENDER burns",
            summary="Epochs can show USDC burn activity with near-zero burnedRender.",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="treasury_flows",
            title="Foundation/treasury directional flows",
            summary="Not separately verified this pass.",
            epistemic_status="UNKNOWN",
        ),
    ]
    return rc


def render_health_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    net = c.get("network") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    lines = (
        mline_tip(
            ICON_NODES,
            "Frames rendered",
            "Cumulative",
            _fmt_m(net.get("frames_cumulative")),
            evidence_tip_html(
                name="NETWORK USAGE",
                read="REAL USAGE",
                rows=[
                    ("Frames", _fmt_m(net.get("frames_cumulative"))),
                    ("Nodes metric", net.get("nodes_label") or ""),
                    ("Nodes value", str(net.get("nodes_since_inception"))),
                ],
                note="Structural evidence only — not a price timing signal. Do not equate inception nodes with active nodes today.",
                source="Render Foundation",
                source_url=net.get("source_url"),
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_GRID,
            "Usage read",
            "Network health",
            "REAL USAGE",
            evidence_tip_html(
                name="NETWORK HEALTH",
                read="REAL USAGE",
                rows=[("Central lesson", "Useful network ≠ automatically good token economics.")],
                note="Left side of the split — product/network, not trade confirmation.",
                source="Stage-1 completion",
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Network health</h4>"
        '<div class="band-status c-green">REAL USAGE</div>'
        + lines
        + "</div>"
    )


def render_token_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    bme = c.get("bme") or {}
    price = c.get("price_structure") or {}
    last4 = bme.get("last4") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")
    now = f"${price.get('now_usd')}"
    dd = price.get("drawdown_pct")
    fill_w = f"{min(95, max(5, int(abs(float(dd or 90)))))}%"
    ddbar = (
        '<div class="ddbar">'
        f'<div class="ddbar-track"><div class="ddbar-fill" style="width:{fill_w}"></div></div>'
        f'<div class="ddbar-cap"><span>Now {now}</span>'
        f"<span>{timing_caption('ATH $' + str(price.get('ath_usd')), dd)}</span></div>"
        "</div>"
    )
    lines = (
        mline_tip(
            ICON_DROP,
            "Recent BME",
            "Burn vs node emissions",
            f"ratio ~{float(last4.get('ratio') or 0):.2f}",
            evidence_tip_html(
                name="RECENT BME",
                read="NET INFLATIONARY",
                rows=[
                    ("Last-4 burned", _fmt_k(last4.get("burned"))),
                    ("Last-4 emissions", _fmt_k(last4.get("node_emissions"))),
                    ("Ratio", f"{float(last4.get('ratio') or 0):.2f}"),
                    ("8-epoch note", (bme.get("last8") or {}).get("spike_note") or ""),
                ],
                note=bme.get("simple_english") or "",
                source="Foundation API",
                source_url="https://infra.shikumi.cc/api/v1/epochBurnStats",
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_CIRCLES,
            "Market structure",
            "Price + RS",
            "WEAK · LAGGING",
            evidence_tip_html(
                name="TOKEN / MARKET",
                read="WEAK · RECENTLY INFLATIONARY",
                rows=[("Group read", "WEAK · LAGGING")],
                note="Right side of the split — token/market confirmation.",
                source="Stage-1 completion",
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-timing">'
        "<h4>Token / market confirmation</h4>"
        '<div class="band-status c-orange">WEAK · RECENTLY INFLATIONARY</div>'
        + ddbar
        + lines
        + "</div>"
    )


def _fx_card(
    *,
    title: str,
    read: str,
    copy: str,
    tone: str,
    kpis: list[tuple[str, str]],
    tip_rows: list[tuple[str, str]],
    source: str,
    source_url: str | None,
    as_of: str | None,
    note: str,
) -> str:
    from lib.v3.forensic_cards import _esc, _details, _ev_row

    kpi_html = "".join(
        f'<div class="fx-kpi"><strong>{_esc(v)}</strong><span>{_esc(k)}</span></div>'
        for k, v in kpis
        if v
    )
    rows = "".join(_ev_row(k, v) for k, v in tip_rows if v)
    tip = evidence_tip_html(
        name=title,
        read=read,
        rows=tip_rows[:5],
        note=note,
        source=source,
        source_url=source_url,
        as_of=as_of,
        confidence="MEDIUM",
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


def render_render_evidence_cards(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    bme = c.get("bme") or {}
    supply = c.get("supply") or {}
    bs = c.get("buyer_seller") or {}
    wm = c.get("wintermute") or {}
    deriv = c.get("derivatives") or {}
    last4 = bme.get("last4") or {}
    last8 = bme.get("last8") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")

    cards = [
        _fx_card(
            title="Burn vs emissions (BME)",
            read="RECENT NET INFLATIONARY",
            copy=bme.get("simple_english") or "",
            tone="orange",
            kpis=[
                ("Last-4 burn", _fmt_k(last4.get("burned"))),
                ("Last-4 emit", _fmt_k(last4.get("node_emissions"))),
                ("Ratio", f"{float(last4.get('ratio') or 0):.2f}"),
                ("Cumulative burn", _fmt_m(bme.get("cumulative_burned"))),
            ],
            tip_rows=[
                ("Last-8 burn", _fmt_k(last8.get("burned"))),
                ("Last-8 emit", _fmt_k(last8.get("node_emissions"))),
                ("Last-8 ratio", f"{float(last8.get('ratio') or 0):.2f}"),
                ("Spike note", last8.get("spike_note") or ""),
                ("Node due / epoch", _fmt_k(bme.get("node_operator_due_per_epoch"))),
            ],
            source="Foundation first-party API",
            source_url="https://infra.shikumi.cc/api/v1/epochBurnStats",
            as_of=as_of,
            note="Measured recent window — not a permanent inflation claim.",
        ),
        _fx_card(
            title="Supply / migration",
            read="PARTIAL — DO NOT ADD",
            copy=supply.get("display_rule") or "",
            tone="orange",
            kpis=[
                ("Solana supply", _fmt_m(supply.get("solana_supply"))),
                ("Legacy ETH", _fmt_m(supply.get("ethereum_rndr"))),
                ("Foundation circ", _fmt_m(supply.get("foundation_circulating"))),
                ("CG circ", _fmt_m(supply.get("cg_circulating"))),
            ],
            tip_rows=[
                ("Solana circ", _fmt_m(supply.get("solana_circulating"))),
                ("Max supply", f"{supply.get('max_supply'):,}"),
            ],
            source="Foundation supplyInfo",
            source_url=supply.get("source_url"),
            as_of=as_of,
            note="Prefer Foundation max supply. CG circulating is market reference only.",
        ),
        _fx_card(
            title="DEX buyer / seller sample",
            read=bs.get("classification") or "REAL BUYING · CONCENTRATED",
            copy="Principal Solana pools only — CEX and ETH RNDR excluded.",
            tone="orange",
            kpis=[
                ("Swaps", str(bs.get("swap_tx_count"))),
                ("Buyers", str(bs.get("unique_buyers"))),
                ("Top-5 buy", f"{bs.get('top5_buy_share_pct')}%"),
                ("Gross buy", _fmt_k(bs.get("gross_buy"))),
            ],
            tip_rows=[
                ("Net accumulators", str(bs.get("net_accumulators"))),
                ("Sellers", str(bs.get("unique_sellers"))),
                ("Gross sell", _fmt_k(bs.get("gross_sell"))),
                ("Top-5 sell", f"{bs.get('top5_sell_share_pct')}%"),
                ("Span", f"~{bs.get('span_hours')}h"),
            ],
            source="Helius SWAP sample",
            source_url=bs.get("source_url"),
            as_of=bs.get("gathered_at_utc") or as_of,
            note="TRANSFER ≠ SALE. Not market-wide.",
        ),
        _fx_card(
            title="Wintermute / MM",
            read=wm.get("read") or "MM INVENTORY / DEX CHURN",
            copy="Two-way DEX churn with residual inventory — not a dump warning.",
            tone="muted",
            kpis=[
                ("Sample buy", _fmt_k(wm.get("gross_buy"))),
                ("Sample sell", _fmt_k(wm.get("gross_sell"))),
                ("Net", _fmt_k(wm.get("net"))),
                ("Still held", _fmt_k(wm.get("balance"))),
            ],
            tip_rows=[
                ("Wallet", "MfDu…"),
                ("Discipline", " · ".join(wm.get("discipline") or [])),
            ],
            source="MM registry ∩ sample",
            source_url="https://solscan.io/account/MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa",
            as_of=as_of,
            note="No Wintermute warning on this page.",
        ),
        _fx_card(
            title="Derivatives slice",
            read=deriv.get("read") or "LEVERAGE PRESENT",
            copy=deriv.get("note") or "",
            tone="orange",
            kpis=[
                ("Fut/spot", f"{deriv.get('fut_spot_ratio')}×"),
                ("OI", f"${_fmt_k(deriv.get('oi_notional_usd'))}"),
                ("vs 30d max", f"~{deriv.get('oi_vs_30d_max_pct')}%"),
            ],
            tip_rows=[
                ("Funding", str(deriv.get("funding_latest"))),
                ("Funding pctile", str(deriv.get("funding_pctile_100"))),
            ],
            source="Binance RENDERUSDT",
            source_url="https://www.binance.com/en/futures/RENDERUSDT",
            as_of=as_of,
            note="Do not call leverage bearish by itself.",
        ),
    ]
    return (
        '<section class="sec fx-sec" aria-label="Wallet and transaction evidence">'
        '<h3 class="fx-title">Wallet &amp; transaction evidence</h3>'
        '<div class="fx-section-note">Compact conclusions first. Burns, DEX sample and method stay in tips underneath.</div>'
        '<div class="fx-grid">' + "".join(cards) + "</div></section>"
    )


def render_render_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">Useful network ≠ automatically good token economics.</p>'
        "</div><div class=\"split\">"
        + render_health_band(intel)
        + render_token_band(intel)
        + "</div></section>"
    )
    warn = warning_stack_html(intel)
    wcm = change_mind_section(intel, slug="render")
    rc = reality_check_section(intel)
    cards = render_render_evidence_cards(intel)
    return split + warn + wcm + rc + cards


def build_render_v3_from_packs(
    report_date: str,
    v4_report: dict | None = None,
) -> dict[str, Any]:
    """Assemble full RENDER V3 intel from canonical packs (no live research)."""
    stage1 = load_render_canonical()
    price = stage1.get("price_structure") or {}
    stance = render_current_stance()
    now_usd = price.get("now_usd")
    doc: dict[str, Any] = {
        "meta": {
            "schema": "render-v3",
            "slug": "render",
            "report_date": report_date,
            "generated_at": now_iso(),
            "version": "stage1-completion-v1",
            "v4_report_date": (v4_report or {}).get("report_date"),
        },
        "hero": {
            "asset": "RENDER",
            "price_usd": now_usd,
            "price_display": f"~${now_usd:,.2f}" if isinstance(now_usd, (int, float)) else "—",
            "ath_display": f"${price.get('ath_usd')}",
            "drawdown_pct": price.get("drawdown_pct"),
            "price_as_of": (stage1.get("meta") or {}).get("fetched_at_utc"),
            "thesis": (
                "Useful network ≠ automatically good token economics. "
                "Do not confuse real usage with recent token scarcity."
            ),
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
            "v3_stance": stance["headline"],
            "v3_stance_note": stance["summary"],
            "confidence": stance["confidence"],
            "data_completeness": "Completion packs wired — supply reconciliation PARTIAL.",
        },
        "triad": {
            "lifecycle": {
                "display": "Post-cycle / weak leadership",
                "detail": meaning("render", price.get("drawdown_pct")),
            },
            "project_health": {
                "display": "REAL USAGE",
                "detail": "Network usage measurable; recent BME net inflationary.",
            },
            "market_timing": {
                "display": "WEAK · LAGGING",
                "detail": "Price and RS weak; DEX buying real but concentrated.",
            },
        },
        "stage1": stage1,
        "capital_flow": {
            "binance_fut_spot_ratio": (stage1.get("derivatives") or {}).get("fut_spot_ratio"),
        },
        "network": stage1.get("network") or {},
    }
    doc["asset_top"] = build_render_asset_top(doc)
    doc["warning_stack"] = build_render_warning_stack(doc)
    doc["what_would_change_mind"] = build_render_change_mind(doc)
    doc["reality_check"] = build_render_reality_check(doc)
    return doc
