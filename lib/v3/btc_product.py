"""BTC V3 product layer — split, warnings, WCM, Reality Check, evidence cards.

BTC-specific labels (no Project Health). Evidence from approved research pack only.
"""

from __future__ import annotations

import html
from typing import Any

from lib.v3.ath_frame import meaning, rc_title
from lib.v3.change_mind import condition
from lib.v3.fields import category_state, pack_risk_confirmation
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
    ICON_WARN,
    ICON_WRENCH,
    evidence_tip_html,
    mline_tip,
    reality_check_section,
    warning_stack_html,
)

AS_OF = "2026-08-12"
FETCHED = "2026-08-12T06:51:23Z"
FARSIDE = "https://farside.co.uk/btc/"
CG_BTC = "https://www.coingecko.com/en/coins/bitcoin"
BINANCE_SPOT = "https://www.binance.com/en/trade/BTC_USDT"
BINANCE_FUT = "https://www.binance.com/en/futures/BTCUSDT"
BINANCE_OI = "https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT"
COINMETRICS_NFCI = "https://www.chicagofed.org/research/data/nfci/current-data"


def _e(s: Any) -> str:
    return html.escape("" if s is None else str(s), quote=True)


# ---------------------------------------------------------------------------
# Data builders
# ---------------------------------------------------------------------------


def build_btc_warning_stack(_intel: dict[str, Any] | None = None) -> dict[str, Any]:
    cats = [
        technical_trend_category("btc"),
        category_state(
            "perp_dominance",
            "PERP VS SPOT",
            "PARTIAL",
            detail="Binance perp 24h ~$6.9B vs spot ~$0.86B · fut/spot ~8.0×. Leverage elevated, not blow-off from this evidence.",
            summary="Binance perp volume ~8× spot",
        ),
        category_state(
            "etf_spot",
            "ETF / SPOT SUPPORT",
            "PARTIAL",
            detail=(
                "Aug 3–7 ~+$853–865M net. Aug 10 −$144.6M. Aug 11 +$7.8M. "
                "Cumulative since launch ~$52.1B. One outflow day ≠ bearish."
            ),
            summary="Recent ETF support · not one-way",
        ),
        category_state(
            "flow_identity",
            "BUYER IDENTITY",
            "UNKNOWN",
            detail="ETF demand visible. CEX / LTH-STH / whale identity UNKNOWN.",
            summary="Beyond ETFs, buyers UNKNOWN",
        ),
    ]
    return pack_risk_confirmation(cats, "BTC V3 research pack")


def build_btc_change_mind() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "constructive": [
            condition(
                condition_id="etf_reclaim",
                title="ETF + reclaim local highs",
                summary="ETF inflows persist while price reclaims/holds above declining local highs.",
                status="WATCH",
                interpretation="Would show spot support converting into structure repair — not a price target.",
                evidence_rows=[
                    ("ETF Aug 3–7", "~+$853–865M net"),
                    ("Aug 10 / 11", "−$144.6M / +$7.8M"),
                    ("Structure", "Range / HL since July · lower highs intact"),
                ],
                source="Farside + Binance daily",
                source_url=FARSIDE,
                as_of=AS_OF,
                confidence="MEDIUM",
                epistemic_status="PARTIAL",
                icon="up",
            ),
            condition(
                condition_id="leverage_cools",
                title="Leverage cools · spot firm",
                summary="Perp dominance cools while spot/ETF demand remains firm.",
                status="WATCH",
                interpretation="Would clean the leverage-heavy structure without needing a waterfall narrative.",
                evidence_rows=[
                    ("Fut/spot now", "~8.0×"),
                    ("OI", "~109k BTC · mild up"),
                    ("Funding", "~+0.0078%/8h (mild)"),
                ],
                source="Binance spot + USDT-M",
                source_url=BINANCE_FUT,
                as_of=AS_OF,
                confidence="MEDIUM",
                epistemic_status="PARTIAL",
                icon="up",
            ),
        ],
        "defensive": [
            condition(
                condition_id="july_range_breaks",
                title="July range / HL breaks",
                summary="July higher-low / range structure breaks with expanding perp dominance.",
                status="WATCH",
                interpretation="Would reopen the post-ATH down-leg as an active breakdown, not just consolidation.",
                evidence_rows=[
                    ("July low", "~$57.8k"),
                    ("Now", "Range holding above July low"),
                    ("Perp", "~8× spot ongoing"),
                ],
                source="Binance daily structure",
                source_url=BINANCE_SPOT,
                as_of=AS_OF,
                confidence="MEDIUM",
                epistemic_status="PARTIAL",
                icon="warn",
            ),
            condition(
                condition_id="etf_outflows_range_loss",
                title="Multi-day ETF outflows + range loss",
                summary="Multi-day ETF outflows combine with range loss.",
                status="WATCH",
                interpretation="One redemption day is not enough; sustained outflows plus structure break would weaken the spot-support read.",
                evidence_rows=[
                    ("One-day outflow", "Aug 10 −$144.6M (not decisive alone)"),
                    ("Cumulative ETF", "~$52.1B since launch"),
                ],
                source="Farside Investors",
                source_url=FARSIDE,
                as_of="2026-08-11",
                confidence="MEDIUM",
                epistemic_status="PARTIAL",
                icon="warn",
            ),
        ],
    }


def build_btc_reality_check() -> dict[str, Any]:
    rc = empty_reality_check()
    rc["priority_headline"] = "WEAKENING BUT NOT CONFIRMED"
    rc["known"] = [
        rc_item(
            item_id="ath_drawdown",
            title=rc_title("btc", 49.6),
            summary="BTC ~$63.6k · ATH ~$126.1k · ~−49.6%.",
            evidence_rows=[("7d", "~−1.1%"), ("30d", "~+1.3%"), ("90d", "~−21.5%")],
            interpretation=meaning("btc", 49.6),
            priority="HIGH",
            source="CoinGecko + Binance",
            source_url=CG_BTC,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="lower_highs",
            title="Lower-high structure remains",
            summary="Lower highs since ATH; May 2026 clear LH vs Jan.",
            evidence_rows=[("ATH fail", "2025-10-07"), ("SMA50 break", "2026-01-20")],
            interpretation="Structural down-leg not repaired.",
            priority="HIGH",
            source="Binance daily",
            source_url=BINANCE_SPOT,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="july_hl",
            title="July low not re-broken",
            summary="July low ~$57.8k · range / higher-low holding.",
            evidence_rows=[("Phase", "Consolidation / range, not fresh waterfall")],
            interpretation="Stabilization question is open.",
            priority="HIGH",
            source="Binance daily",
            source_url=BINANCE_SPOT,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="etf_support",
            title="Recent ETF inflows supportive",
            summary="Aug 3–7 ~+$853–865M net; Aug 10 −$144.6M; Aug 11 +$7.8M.",
            evidence_rows=[("Cumulative", "~$52.1B since launch")],
            interpretation="Institutional spot proxy still present. One outflow day ≠ bearish.",
            priority="MEDIUM",
            source="Farside Investors",
            source_url=FARSIDE,
            as_of="2026-08-11",
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="perp_heavy",
            title="Perp activity ≫ spot",
            summary="Binance fut/spot ~8.0× · OI ~109k BTC · funding mild positive.",
            evidence_rows=[("OI Δ", "+2.8% 1d / +1.0% 7d / +1.8% 30d")],
            interpretation="Leverage-heavy structure. OI↑ ≠ bearish · funding+ ≠ top.",
            priority="HIGH",
            source="Binance",
            source_url=BINANCE_FUT,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    rc["suggests"] = [
        rc_item(
            item_id="trend_weakened",
            title="Trend already weakened",
            summary="Structural bull trend has already weakened materially.",
            interpretation="Retracement is the base case — not a fresh break starting now. Watch the turn.",
            priority="HIGH",
            source="BTC V3 synthesis",
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="range_phase",
            title="Consolidation / range",
            summary="Range/consolidation — not a fresh waterfall.",
            interpretation="July higher-low still holds.",
            priority="MEDIUM",
            source="BTC V3 synthesis",
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="spot_support",
            title="Institutional spot still present",
            summary="ETF creations recently supportive — spot support has not disappeared.",
            interpretation="Proxy only; not complete demand.",
            priority="MEDIUM",
            source="Farside Investors",
            source_url=FARSIDE,
            as_of="2026-08-11",
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="lev_structure",
            title="Still leverage-heavy",
            summary="Structure remains leverage-heavy (~8× fut/spot on Binance).",
            interpretation="Elevated ≠ blow-off from this evidence.",
            priority="HIGH",
            source="Binance",
            source_url=BINANCE_FUT,
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
    ]
    rc["unknowns"] = [
        rc_item(
            item_id="exchange_netflow",
            title="Full exchange netflow",
            summary="Not fetched this pass.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="lth_sth",
            title="LTH / STH flows",
            summary="Buyer/seller cohort attribution unavailable.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="liq_basis",
            title="Liquidation / basis history",
            summary="Reliable series unavailable this pass.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="etf_machine",
            title="Full ETF 10d / 20d machine series",
            summary="Daily Farside points used; machine series not fetched.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="miner_whale",
            title="Proven miner / whale sell pressure",
            summary="No verified major dump events this pass. TRANSFER ≠ SALE.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
    ]
    return rc


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------


def btc_trend_band(_intel: dict[str, Any] | None = None) -> str:
    lines = (
        mline_tip(
            ICON_CIRCLES,
            "Retracement",
            "From Oct 2025 ATH",
            "~−49.6%",
            evidence_tip_html(
                name="RETRACEMENT",
                read="~−49.6%",
                rows=[("Now", "~$63.6k"), ("ATH", "~$126.1k"), ("90d", "~−21.5%")],
                note=meaning("btc", 49.6),
                source="CoinGecko + Binance",
                source_url=CG_BTC,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_BARS,
            "MAs",
            "Descriptive only",
            "Below 200d",
            evidence_tip_html(
                name="MOVING AVERAGES",
                read="Below 20d · above 50d · below 200d",
                rows=[("Rule", "Not trading signals")],
                note="MA location describes structure — not a cross rule.",
                source="Binance daily",
                source_url=BINANCE_SPOT,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_GRID,
            "Range",
            "Since July low",
            "HL holding",
            evidence_tip_html(
                name="JULY RANGE",
                read="Higher-low / range holding",
                rows=[("July low", "~$57.8k"), ("Question", "Stabilize vs breakdown")],
                note="Range intact ≠ trend repaired.",
                source="Binance daily",
                source_url=BINANCE_SPOT,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_WARN,
            "Lower highs",
            "Since ATH",
            "Intact",
            evidence_tip_html(
                name="LOWER HIGHS",
                read="Intact",
                rows=[("ATH fail", "2025-10-07"), ("Clear LH", "May 2026 vs Jan")],
                note="Cleanest early warning came from price structure.",
                source="Binance swing highs",
                source_url=BINANCE_SPOT,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Structural trend</h4>"
        '<div class="band-status c-orange">DAMAGED · RANGE HOLDING</div>'
        + lines
        + "</div>"
    )


def btc_capital_band(_intel: dict[str, Any] | None = None) -> str:
    lines = (
        mline_tip(
            ICON_BAG,
            "ETF flows",
            "US spot proxy",
            "Recent support",
            evidence_tip_html(
                name="ETF / INSTITUTIONAL SPOT",
                read="RECENT SUPPORT",
                rows=[
                    ("Aug 3–7", "~+$853–865M net"),
                    ("Aug 10", "−$144.6M"),
                    ("Aug 11", "+$7.8M"),
                    ("Cumulative", "~$52.1B"),
                ],
                note="Best institutional spot proxy here — not complete BTC spot demand. One outflow day ≠ bearish.",
                source="Farside Investors",
                source_url=FARSIDE,
                as_of="2026-08-11",
                confidence="MEDIUM",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_LEVERAGE,
            "Fut / spot",
            "Binance 24h",
            "~8.0×",
            evidence_tip_html(
                name="SPOT VS LEVERAGE",
                read="LEVERAGE HEAVY",
                rows=[
                    ("Spot 24h", "~$0.86B"),
                    ("Perp 24h", "~$6.9B"),
                    ("OI", "~109k BTC"),
                    ("Funding", "~+0.0078%/8h"),
                ],
                note="Elevated leverage, not blow-off from this evidence. OI↑ ≠ bearish · funding+ ≠ top.",
                source="Binance",
                source_url=BINANCE_FUT,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_RATIO,
            "OI trend",
            "Binance BTC",
            "+1.8% 30d",
            evidence_tip_html(
                name="OPEN INTEREST",
                read="+2.8% 1d / +1.0% 7d / +1.8% 30d",
                rows=[("Level", "~109k BTC")],
                note="Inventory rising mildly — not a standalone warning.",
                source="Binance openInterest",
                source_url=BINANCE_OI,
                as_of=AS_OF,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_DROP,
            "Funding",
            "8h print",
            "Mild +",
            evidence_tip_html(
                name="FUNDING",
                read="~+0.0078% / 8h",
                rows=[("7d mean", "~+0.0052% / 8h"), ("Basis / liq", "UNKNOWN")],
                note="Positive funding ≠ top.",
                source="Binance premiumIndex",
                source_url="https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT",
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-green",
        )
    )
    return (
        '<div class="band band-timing">'
        "<h4>Capital support</h4>"
        '<div class="band-status c-orange">ETF SUPPORT RECENT · LEVERAGE HEAVY</div>'
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
    as_of: str,
    note: str = "",
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
    tone_cls = {"green": "green", "orange": "orange", "muted": "", "grey": ""}.get(tone, "")
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


def render_btc_evidence_cards(intel: dict[str, Any]) -> str:
    ctx = intel.get("context") or {}
    cards = [
        _fx_card(
            title="Monetary / institutional",
            read="ETF ACCESS REAL",
            copy="US spot ETFs are the cleanest institutional access layer here. Issuance/halving and miner economics left UNKNOWN where not sourced.",
            tone="green",
            kpis=[
                ("ETF cum.", "~$52.1B"),
                ("Recent", "Supportive"),
                ("Issuance", "UNKNOWN"),
            ],
            tip_rows=[
                ("Proxy", "ETF creations/redemptions"),
                ("Not claimed", "Complete spot demand"),
                ("Miner econ", "UNKNOWN this pass"),
            ],
            source="Farside Investors",
            source_url=FARSIDE,
            as_of="2026-08-11",
            note="Do not invent alt-style project fundamentals for BTC.",
        ),
        _fx_card(
            title="Market participation / rotation",
            read="NARROW",
            copy="Alts mostly lag BTC. BTC weakness is not obviously being replaced by a broad alt melt-up. Context only.",
            tone="orange",
            kpis=[
                ("BTC.D", f"~{ctx.get('btc_dominance_pct', 56.3)}%"),
                ("Beat BTC 30d", f"~{ctx.get('breadth_pct_beat_btc_30d', 33.3)}%"),
                ("Med alt-BTC", f"~{ctx.get('breadth_median_alt_btc_pp', -5.1)}pp"),
            ],
            tip_rows=[
                ("State", "NARROW"),
                ("Gate", "None — context only"),
            ],
            source="Market V3 participation (verified)",
            source_url=CG_BTC,
            as_of=AS_OF,
            note="NARROW ≠ WAIT / reduce logic.",
        ),
        _fx_card(
            title="Macro / liquidity",
            read="SOFT PULSE",
            copy="Liquidity pulse soft · NFCI easier · stablecoin supply soft. Context only — not a BTC trade rule.",
            tone="grey",
            kpis=[
                ("Liq pulse YoY", f"~{ctx.get('liquidity_pulse_yoy_pct', -5.92)}%"),
                ("NFCI", str(ctx.get("nfci", -0.529))),
                ("Stables", f"~${ctx.get('stablecoin_supply_usd_b', 306)}B"),
            ],
            tip_rows=[
                ("Stables 30d", f"~{ctx.get('stablecoin_30d_pct', -1.0)}%"),
                ("DXY", "UNKNOWN"),
            ],
            source="Approved Market evidence",
            source_url=COINMETRICS_NFCI,
            as_of=AS_OF,
            note="Do not rebuild Market section here.",
        ),
        _fx_card(
            title="Sell-side pressure",
            read="NO VERIFIED DUMP",
            copy="Miners / large holders UNKNOWN. No verified gov, estate, or corporate sale event this pass. TRANSFER ≠ SALE.",
            tone="grey",
            kpis=[
                ("Miners", "UNKNOWN"),
                ("Gov / seized", "None verified"),
                ("ETFs", "Creations > redemptions recently"),
            ],
            tip_rows=[
                ("Estates", "No verified event"),
                ("Corporates", "No verified event"),
                ("CEX flow", "≠ sale claim"),
            ],
            source="BTC V3 research pass",
            source_url=FARSIDE,
            as_of=AS_OF,
            note="No manipulation claims.",
        ),
        _fx_card(
            title="What led",
            read="PRICE STRUCTURE FIRST",
            copy="ATH fail → SMA50 break → lower high → July low. ETF/participation/leverage mostly confirmed later. No timing classifier.",
            tone="orange",
            kpis=[
                ("ATH fail", "2025-10-07"),
                ("SMA50 break", "2026-01-20"),
                ("July low", "2026-07"),
            ],
            tip_rows=[
                ("Clear LH", "May 2026"),
                ("ETF weak→rebound", "July → Aug"),
                ("Leverage / participation", "Coincident context"),
            ],
            source="btc-signal-timing research",
            source_url=BINANCE_SPOT,
            as_of=AS_OF,
            note="Price structure gave the cleanest early warning.",
        ),
    ]
    return (
        '<section class="sec fx-sec" aria-label="Wallet and transaction evidence">'
        '<h3 class="fx-title">Wallet &amp; transaction evidence</h3>'
        '<div class="fx-section-note">Compact conclusions first. Structure, ETF and leverage detail stay in tips underneath.</div>'
        f'<div class="fx-mini-grid">{"".join(cards)}</div>'
        "</section>"
    )


def render_btc_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">Trend damage is real, but current spot support means another breakdown is not confirmed.</p>'
        "</div><div class=\"split\">"
        + btc_trend_band(intel)
        + btc_capital_band(intel)
        + "</div></section>"
    )
    warn = warning_stack_html(intel)
    wcm = change_mind_section(intel, slug="btc")
    rc = reality_check_section(intel)
    cards = render_btc_evidence_cards(intel)
    return split + warn + wcm + rc + cards
