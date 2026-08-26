"""Render index-v3.html — Route D structure locked; live data in value slots only."""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Any

from lib.asset_v4 import _format_report_date
from lib.dashboard_v1 import ASSET_SLUGS, HOLDING_STRIP_TRAIL, _call_markup, _latest_report
from lib.paths import ROOT, TEMPLATES
from lib.data_integrity import build_snapshot_from_sources, snapshot_html
from lib.v3.forensic_cards import FORENSIC_CSS
from lib.v3.current_stance import STANCE_CSS, STANCE_JS, STANCE_MODAL_SHELL
from lib.v3.desk_strip import DESK_CSS, DESK_JS, desk_html
from lib.v3.hold_cards import HOLD_CARD_CSS, HOLD_CLICK_JS, HOLD_LIVE_JS
from lib.v3.route_d_shell import (
    designnote_footer,
    evidence_tip_html,
    falsifiers_section,
    knowledge_census_render,
    lifecycle_ring,
    lifecycle_stages_pump,
    lifecycle_stages_render,
    price_figure_render,
    pump_health_band,
    pump_timing_band,
    render_health_band,
    timing_band,
    warning_stack_pump,
    warning_stack_render,
)
from lib.v3.econ_minidash import ECON_DASH_CSS
from lib.v3.pump_minidash import PUMP_MINIDASH_CSS

V3_ASSET_SLUGS = frozenset(
    {"render", "pump", "sol", "btc", "ray", "grass", "io", "nos", "fartcoin", "spx6900", "zec", "hype"}
)

# Option 3 v5 ALT top — structure copied from approved mock; sizes fitted to dash (~1020px)
ALT_TOP_CSS = """
.alt-top { margin-bottom: 3rem; }
.alt-hero {
  background: var(--surface);
  border-radius: 18px;
  padding: 2rem 1.7rem 1.65rem;
  display: grid;
  grid-template-columns: 0.78fr 1.22fr;
  gap: 1.6rem;
  align-items: start;
}
.alt-hero .econ-dash { grid-column: 1 / -1; margin: 1rem 0 0; }
""" + ECON_DASH_CSS + PUMP_MINIDASH_CSS + """
.alt-eyebrow {
  font-family: var(--display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  display: block;
}
.alt-ticker {
  font-family: var(--display);
  font-size: 3.35rem;
  font-weight: 700;
  line-height: 0.92;
  margin: 0.55rem 0 0;
}
.alt-price {
  display: block;
  font-family: var(--display);
  font-size: 1.55rem;
  font-weight: 600;
  color: var(--muted);
  margin: 0.7rem 0 0;
  margin-left: 0;
}
.alt-stance, .alt-posture { text-align: right; min-width: 0; }
.alt-stance-headline, .alt-posture-headline {
  font-family: var(--display);
  font-size: 1.85rem;
  font-weight: 700;
  line-height: 1.08;
  color: var(--orange);
  text-transform: uppercase;
  margin: 0.55rem 0 0.55rem;
}
.alt-stance-expl, .alt-posture-expl {
  font-size: 0.92rem;
  line-height: 1.45;
  color: var(--muted);
  margin: 0;
  max-width: 36rem;
  margin-left: auto;
}
.alt-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.7rem;
  margin-top: 0.7rem;
}
.alt-group {
  background: var(--surface);
  border-radius: 14px;
  padding: 1.05rem 1.1rem 0.85rem;
}
.alt-group-title {
  font-family: var(--display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}
.alt-group-state {
  font-family: var(--display);
  font-size: 1.2rem;
  font-weight: 700;
  line-height: 1.05;
  margin-top: 0.55rem;
}
.alt-group-state.c-green { color: var(--green); }
.alt-group-state.c-orange { color: var(--orange); }
.alt-group-state.c-red { color: var(--red); }
.alt-group-state.c-muted { color: var(--muted); }
.alt-rows { margin-top: 0.75rem; }
.alt-signal {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 0.45rem;
  align-items: center;
  padding: 0.48rem 0;
  border-top: 1px solid rgba(150, 154, 172, 0.16);
  cursor: default;
}
.alt-signal:first-child { border-top: 0; }
.alt-signal-left,
.alt-signal-state {
  font-family: var(--bodyfont);
  font-size: 0.88rem;
  font-weight: 400;
  line-height: 1.2;
  letter-spacing: normal;
  text-transform: none;
}
.alt-signal-left {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
  color: var(--ink);
}
.alt-signal-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.alt-signal .alt-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex: 0 0 12px;
  margin-right: 0;
  display: inline-block;
}
.alt-dot.g { background: var(--green); }
.alt-dot.o { background: var(--orange); }
.alt-dot.r { background: var(--red); }
.alt-dot.u { background: var(--muted); }
.alt-signal-state {
  color: var(--muted);
  text-align: right;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 900px) {
  .alt-hero { grid-template-columns: 1fr; }
  .alt-stance, .alt-posture { text-align: left; border-top: 1px solid var(--pill-off, #3d4256); padding-top: 1.1rem; }
  .alt-stance-expl, .alt-posture-expl { margin-left: 0; max-width: none; }
  .alt-summary { grid-template-columns: 1fr; }
  .alt-ticker { font-size: 2.6rem; }
}
"""

# What would change our mind — locked mockup (must ship in review + baseline builds)
WCM_CSS = """
.wcm-sec { margin-top: 0; }
.wcm-title {
  margin: 0 0 1.2rem;
  font-family: var(--display);
  font-weight: 700;
  font-size: 1.85rem;
  line-height: 1.05;
  letter-spacing: 0.01em;
}
.wcm-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.wcm-card {
  min-height: 0;
  border-radius: 18px;
  padding: 22px 24px 18px;
}
.wcm-card.good { background: #e7efeb; }
.wcm-card.bad { background: #efe8ea; }
[data-theme="dark"] .wcm-card.good { background: #2f3c3d; }
[data-theme="dark"] .wcm-card.bad { background: #3a343b; }
.wcm-card h2 {
  margin: 0;
  font-family: var(--display);
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.wcm-kicker { margin-top: 0.15rem; font-size: 0.72rem; font-weight: 700; }
.wcm-card.good .wcm-kicker { color: var(--green); }
.wcm-card.bad .wcm-kicker { color: var(--red); }
.wcm-rows { margin-top: 0.85rem; }
.wcm-row {
  position: relative;
  display: grid;
  grid-template-columns: 22px 1fr auto 18px;
  grid-template-rows: auto auto;
  column-gap: 0.8rem;
  row-gap: 0.1rem;
  align-items: center;
  padding: 0.55rem 0;
  cursor: default;
}
.wcm-row + .wcm-row { border-top: 1px solid rgba(150,154,172,0.18); }
.wcm-icon {
  grid-column: 1;
  grid-row: 1;
  width: 15px;
  height: 15px;
  min-width: 15px;
  min-height: 15px;
  max-width: 15px;
  max-height: 15px;
  margin: 0;
  color: var(--muted);
  flex-shrink: 0;
  display: block;
  overflow: visible;
}
.wcm-row-title {
  grid-column: 2;
  grid-row: 1;
  font-family: var(--display);
  font-size: 0.85rem;
  font-weight: 600;
  line-height: 1.2;
}
.wcm-status {
  grid-column: 3;
  grid-row: 1;
  font-family: var(--display);
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin: 0;
  line-height: 1.2;
  white-space: nowrap;
}
.wcm-info {
  grid-column: 4;
  grid-row: 1;
  width: 16px; height: 16px;
  border: 1px solid rgba(150,154,172,0.35);
  color: var(--muted);
  border-radius: 50%;
  font-size: 10px;
  font-weight: 700;
  display: grid;
  place-items: center;
  margin: 0;
}
.wcm-row-sub {
  grid-column: 2 / -1;
  grid-row: 2;
  margin: 0;
  max-width: 560px;
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
@media (max-width: 900px) {
  .wcm-grid { grid-template-columns: 1fr; }
  .wcm-card { min-height: 0; padding: 20px 18px; }
}
"""


# Reality check — locked mockup (title/columns overridden in render)
RC_CSS = """
.rc-sec { margin-top: 0; }
.rc-title {
  margin: 0 0 1.2rem;
  font-family: var(--display);
  font-weight: 700;
  font-size: 1.85rem;
  line-height: 1.05;
  letter-spacing: 0.01em;
  text-transform: none;
}
.rc-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }
.rc-col {
  background: var(--surface);
  border-radius: 17px;
  padding: 22px 24px 18px;
  min-height: 0;
}
.rc-col-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 0.85rem;
}
.rc-col-title {
  font-family: var(--display);
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.rc-col.known .rc-col-title { color: var(--green); }
.rc-col.suggests .rc-col-title { color: var(--orange); }
.rc-col.unknowns .rc-col-title { color: var(--muted); }
.rc-col-sub { font-size: 0.72rem; color: var(--muted); white-space: nowrap; }
.rc-item {
  position: relative;
  padding: 0.5rem 0;
  border-top: 1px solid rgba(150,154,172,0.16);
  cursor: default;
}
.rc-item:first-of-type { border-top: 0; padding-top: 4px; }
.rc-item-top {
  display: grid;
  grid-template-columns: 14px 1fr auto;
  gap: 0.8rem;
  align-items: center;
}
.rc-dot { width: 10px; height: 10px; border-radius: 50%; }
.rc-col.known .rc-dot { background: var(--green); }
.rc-col.suggests .rc-dot { background: var(--orange); }
.rc-col.unknowns .rc-dot { background: var(--muted); }
.rc-item-title {
  font-family: var(--display);
  font-size: 0.85rem;
  font-weight: 600;
  line-height: 1.2;
}
.rc-item-line {
  margin: 0.1rem 24px 0;
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
.rc-tag {
  font-family: var(--display);
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.rc-tag.high { color: var(--orange); }
.rc-tag.med { color: var(--muted); }
.rc-info {
  width: 17px; height: 17px;
  display: inline-grid; place-items: center;
  border: 1px solid rgba(150,154,172,0.35);
  color: var(--muted);
  border-radius: 50%;
  font-size: 10px; font-weight: 800;
}
@media (max-width: 900px) {
  .rc-grid { grid-template-columns: 1fr; }
  .rc-col { min-height: 0; }
}
"""


def _e(s: Any) -> str:
    return html.escape(str(s)) if s is not None else ""


# PUMP capital-confirmation ring has 4 segments (0–3).
# Missing-key fallback is the pre-existing default: index 2 → displayed "03" / SPOT CHECK.
# Explicit None is UNKNOWN and must not use that fallback.
PUMP_LIFECYCLE_MISSING_INDEX_DEFAULT = 2


def _lifecycle_active_view(lifecycle: dict[str, Any], *, n_stages: int) -> dict[str, Any]:
    """Typed lifecycle ring state. Never add to an untyped value."""
    label_default = "SPOT CHECK" if n_stages == 4 else "RESET"
    if "active_index" not in lifecycle:
        idx = PUMP_LIFECYCLE_MISSING_INDEX_DEFAULT if n_stages == 4 else n_stages - 1
        return {
            "mode": "legacy_missing_key",
            "ring_seg": idx,
            "display_n": f"{idx + 1:02d}",
            "ring_label": lifecycle.get("ring_label") or label_default,
        }
    raw = lifecycle["active_index"]
    unknown = {
        "mode": "unknown",
        "ring_seg": None,
        "display_n": "—",
        "ring_label": lifecycle.get("ring_label") or "UNKNOWN",
    }
    if raw is None:
        return unknown
    if isinstance(raw, bool) or not isinstance(raw, int):
        return unknown
    if raw < 0 or raw >= n_stages:
        return unknown
    return {
        "mode": "active",
        "ring_seg": raw,
        "display_n": f"{raw + 1:02d}",
        "ring_label": lifecycle.get("ring_label") or label_default,
    }


def _alt_light_class(light: str) -> str:
    return {"green": "g", "orange": "o", "red": "r", "unknown": "u"}.get(light, "u")


def _alt_state_class(light: str) -> str:
    return {"green": "c-green", "orange": "c-orange", "red": "c-red", "unknown": "c-muted"}.get(
        light, "c-muted"
    )


# Visible row labels — keep under ~14 chars. Full original stays in the tooltip.
ALT_LABEL_SHORT = {
    "ETF / Institutional Spot": "ETF / Inst",
    "Who Is Buying?": "Buyers",
    "Who Is Selling?": "Sellers",
    "Whales / Major Holders": "Whales",
    "Team / Dev / CEO": "Team",
    "Foundation / Treasury Flows": "Treasury",
    "Tokenomics / Value Capture": "Capture",
    "Token Value Capture": "Capture",
    "Value Capture / Buybacks": "Capture",
    "Protocol / Token Capture": "Capture",
    "Value Capture": "Capture",
    "Trend Structure": "Structure",
    "Cycle Context": "Cycle",
    "Cycle / Range": "Cycle",
    "Spot vs Leverage": "Spot / Lev",
    "Futures vs Spot": "Fut / Spot",
    "Open Interest": "OI",
    "Network Health": "Health",
    "Platform / Project Health": "Health",
    "TVL / Stables / DEX": "TVL / DEX",
    "Liquidity / Absorption": "Liquidity",
    "Liquidity / Access": "Liquidity",
    "Supply / Unlocks": "Supply",
    "Supply Pressure": "Supply",
    "Supply / Float": "Float",
    "Supply / Migration": "Supply",
    "Supply Health": "Supply",
    "Circulating Supply": "Circulating",
    "Cross-chain Supply Architecture": "Cross-chain",
    "Raw Holder Concentration": "Top holders",
    "Discretionary Ownership": "Owners",
    "Holder Identity": "Holders",
    "Contributor / Labs inventory": "Labs inv.",
    "Revenue → GRASS Mechanism": "Rev → GRASS",
    "Burn vs Emissions (BME)": "Burn vs emit",
    "Funding / Spot Confirmation": "Funding",
    "vs PUMP (context)": "vs PUMP",
    "vs SOL (priority)": "vs SOL",
    "vs RENDER / TAO": "vs RNDR",
    "Issuance (not unlock)": "Issuance",
    "Issuance / Funding": "Issuance",
    "Buyback Mechanism": "Buyback",
    "Buyback Holder": "Held RAY",
    "Commercial Demand": "Demand",
    "Network Activity": "Activity",
    "Nodes Running Jobs": "Nodes",
    "Utilized Compute": "Compute",
    "Network Earnings": "Earnings",
    "Disclosed Revenue": "Revenue",
    "Attention / Reflexivity": "Attention",
    "Privacy / Network": "Privacy",
    "Spot Liquidity": "Spot liq",
    "Leverage / Perps": "Perps",
    "Creator / Early": "Creator",
    "Venue Mix": "Venues",
    "Binance Perp": "Binance",
    "Buyers / Sellers": "Flow",
    "TVL · Fees": "TVL / Fees",
    "DEX Volume": "DEX vol",
    "Network Usage": "Usage",
    "Stage 2 Rewards": "Stage 2",
    "Price Trend": "Trend",
}


def _alt_label_short(label: str | None) -> str:
    raw = (label or "").strip()
    return ALT_LABEL_SHORT.get(raw, raw)


def _alt_signal_tip_html(sig: dict[str, Any]) -> str:
    """Evidence-card tip for ALT signal rows (same design as Split TT)."""
    rows: list[tuple[str, str]] = []
    if sig.get("evidence"):
        rows.append(("Evidence", str(sig["evidence"])[:240]))
    if sig.get("unknown"):
        rows.append(("Unknown", str(sig["unknown"])[:180]))
    if sig.get("confidence"):
        rows.append(("Confidence", str(sig["confidence"])))
    if sig.get("freshness"):
        rows.append(("Freshness", str(sig["freshness"])))
    return evidence_tip_html(
        name=str(sig.get("label") or "SIGNAL"),
        read=str(sig.get("display") or sig.get("state") or "—"),
        rows=rows[:4],
        note=str(sig.get("meaning") or "Signal read from current evidence."),
        source=str(sig.get("source") or "feeds"),
        as_of=sig.get("as_of"),
        source_url=sig.get("source_url"),
        confidence=sig.get("confidence"),
        freshness=sig.get("freshness"),
    )


def _alt_top_html(
    asset_top: dict[str, Any],
    extra: str = "",
    *,
    stance_clamp: bool = False,
) -> str:
    """Render approved Option 3 v5 ALT header + signal grid from universal schema."""
    if not asset_top:
        return ""
    from lib.v3.current_stance import resolve_stance, stance_hero_block_html
    from lib.v3.econ_minidash import render_econ_minidash, slug_from_ticker

    stance = resolve_stance(asset_top)
    groups = asset_top.get("groups") or {}
    order = ("market_structure", "capital_flow", "project_supply")

    group_html = []
    for gid in order:
        g = groups.get(gid) or {}
        rows = []
        for sig in g.get("signals") or []:
            tip_html = _alt_signal_tip_html(sig)
            rows.append(
                f'<div class="alt-signal has-tip">'
                f'<div class="metric-tip-template" hidden>{tip_html}</div>'
                f'<div class="alt-signal-left">'
                f'<span class="alt-dot {_alt_light_class(sig.get("light", "unknown"))}"></span>'
                f'<span class="alt-signal-label">{_e(_alt_label_short(sig.get("label")))}</span></div>'
                f'<div class="alt-signal-state">{_e(sig.get("display"))}</div></div>'
            )
        group_html.append(
            f'<div class="alt-group">'
            f'<div class="alt-group-title">{_e(g.get("title"))}</div>'
            f'<div class="alt-group-state {_alt_state_class(g.get("group_light", "unknown"))}">'
            f'{_e(g.get("group_state"))}</div>'
            f'<div class="alt-rows">{"".join(rows)}</div></div>'
        )

    dash = extra or render_econ_minidash(slug_from_ticker(asset_top.get("asset")))
    return (
        f'<div class="alt-top">'
        f'<section class="alt-hero">'
        f'<div class="alt-hero-left">'
        f'<span class="alt-eyebrow">V3 Intelligence · Asset Research Layer</span>'
        f'<h2 class="alt-ticker">{_e(asset_top.get("asset"))}</h2>'
        f'<span class="alt-price">{_e(asset_top.get("price"))}</span>'
        f'</div>'
        f'{stance_hero_block_html(stance, clamp_lines=stance_clamp)}'
        f'{dash}'
        f'</section>'
        f'<section class="alt-summary">{"".join(group_html)}</section>'
        f'</div>'
    )


SLUG_TO_SYMBOL = {"btc": "BTC", "ray": "RAY", "render": "RENDER", "pump": "PUMP", "sol": "SOL", "io": "IO", "nos": "NOS", "grass": "GRASS", "fartcoin": "FARTCOIN", "spx6900": "SPX6900", "zec": "ZEC", "hype": "HYPE"}


def _sorted_asset_slugs(portfolio: dict | None) -> list[tuple[str, str, str | None]]:
    """BTC #1, SOL #2; alts ranked by holding USD; trail tickers pinned far right."""
    positions = (portfolio or {}).get("positions", {})
    pinned: list[tuple[str, str, str | None]] = []
    alts: list[tuple[str, str, str | None]] = []
    trail: list[tuple[str, str, str | None]] = []
    for item in ASSET_SLUGS:
        _, tick, slug = item
        if tick == "BTC":
            pinned.insert(0, item)
        elif tick == "SOL":
            pinned.append(item)
        elif tick in HOLDING_STRIP_TRAIL:
            trail.append(item)
        else:
            alts.append(item)
    alts.sort(
        key=lambda x: (
            -(positions.get(x[1], {}).get("usd_value") or 0),
            x[1],
        )
    )
    trail.sort(key=lambda x: HOLDING_STRIP_TRAIL.index(x[1]))
    return pinned + alts + trail


def _default_v3_slug(portfolio: dict | None, assets: dict[str, dict]) -> str:
    """Open on BTC when available — market-first default."""
    if "btc" in assets:
        return "btc"
    positions = (portfolio or {}).get("positions", {})
    v3 = [s for s in V3_ASSET_SLUGS if s in assets]
    if not v3:
        return "render"
    return max(
        v3,
        key=lambda s: positions.get(SLUG_TO_SYMBOL.get(s, s.upper()), {}).get("usd_value", 0),
    )


def _call_class(call_cls: str) -> str:
    """Route D uses c-orange / c-red / c-muted — not call-orange."""
    return call_cls.replace("call-", "c-")


def _fmt_unit_price(report: dict | None, pos: dict) -> str:
    if report and report.get("price_display"):
        return report["price_display"].replace("~", "").strip()
    usd_px = float(pos.get("usd_price") or 0)
    if usd_px <= 0:
        return "—"
    if usd_px >= 1:
        s = f"${usd_px:,.2f}".rstrip("0").rstrip(".")
        return s
    s = f"${usd_px:.6f}".rstrip("0").rstrip(".")
    return s


def _fmt_holding_usd(usd_val: float, bal: float) -> str:
    if bal <= 0:
        return "$0"
    if usd_val >= 1:
        return f"${usd_val:,.0f}"
    if usd_val > 0:
        return f"${usd_val:.2f}"
    return "—"


def _hold_price_line(report: dict | None, pos: dict) -> str:
    unit = _fmt_unit_price(report, pos)
    bal = float(pos.get("balance") or 0)
    if bal <= 0:
        return unit
    hold = _fmt_holding_usd(float(pos.get("usd_value") or 0), bal)
    if unit == "—" and hold in ("—", "$0"):
        return "—"
    return f"{unit} · {hold}"


def _hold_owned_line(pos: dict) -> str:
    bal = float(pos.get("balance") or 0)
    if bal <= 0:
        return "—"
    return _fmt_holding_usd(float(pos.get("usd_value") or 0), bal)


def _hold_button_inner(tick: str, unit: str, owned: str, call_html: str) -> str:
    return (
        f'<span class="hold-name"><span class="hold-ticker">{_e(tick)}</span>'
        f'<span class="hold-px">{_e(unit)}</span></span>'
        f'<span class="hold-owned">{_e(owned)}</span>'
        f"{call_html}"
    )


def _desk_section_html() -> str:
    p = ROOT / "data" / "cache" / "wallet-desk.json"
    if not p.is_file():
        return ""
    import json as _json

    rows = (_json.loads(p.read_text()).get("rows") or [])
    return desk_html(rows)


def _holdings_html(active_slug: str = "render", portfolio: dict | None = None) -> str:
    p = ROOT / "data" / "cache" / "hold-cards.json"
    if p.is_file():
        import json as _json

        from lib.v3.hold_cards import hold_cards_html

        rows = _json.loads(p.read_text()).get("rows") or []
        if rows:
            return hold_cards_html(rows)
    reports = {slug: _latest_report(slug) for _, _, slug in ASSET_SLUGS if slug}
    positions = (portfolio or {}).get("positions", {})
    buttons = []
    empty_call = '<span class="hold-call hold-call-empty" aria-hidden="true"></span>'
    for _, tick, slug in _sorted_asset_slugs(portfolio):
        slug_attr = f' data-asset-slug="{slug}"' if slug else ""
        pos = positions.get(tick, {})

        report = reports.get(slug) if slug else None
        unit = _fmt_unit_price(report, pos)
        owned = _hold_owned_line(pos)
        active = " active" if slug and slug == active_slug else ""

        # V3: hold-call chips stay blank. Never populate BUY/SELL/HOLD/WAIT from V4.
        buttons.append(
            f'<button class="hold{active}" type="button"{slug_attr}>'
            f"{_hold_button_inner(tick, unit, owned, empty_call)}</button>"
        )
    return "\n".join(buttons)


def _newsletter_html(v4_report: dict, wallet_short: str = "", *, legacy: bool = False) -> str:
    sig_cards = ""
    for s in v4_report.get("signals", []):
        cc = s["colour"].lower()
        sig_cards += (
            f'<div class="sig sig-{cc}"><span class="sig-name">{_e(s["name"])}</span>'
            f'<p>{_e(s["evidence"])}</p></div>'
        )
    sources = " · ".join(_e(s["name"]) for s in v4_report.get("sources", []))
    conf = v4_report.get("confidence", "MEDIUM")
    nl_cls = "newsletter legacy-appendix" if legacy else "newsletter"
    nl_label = (
        "Legacy weekly report · reference appendix (not main read)"
        if legacy
        else "Existing weekly newsletter · preserved beneath V3"
    )
    return (
        f'<section class="{nl_cls}" aria-label="Existing weekly newsletter">'
        f'<span class="label">{nl_label}</span>'
        f'<div class="newsletter-head">'
        f'<h3>{_e(v4_report["asset"])} {_e(v4_report["price_display"])} · Weekly Report</h3>'
        f'<div class="newsletter-call">{_e(v4_report["asset_call"])}</div></div>'
        f'<p class="nl-bl"><b>Bottom line:</b> {_e(v4_report["bottom_line"])} '
        f'Thesis: {_e(v4_report.get("thesis_status"))} · Confidence: {_e(conf)}.</p>'
        f'<div class="signals">{sig_cards}</div>'
        f'<div class="nl-row"><div><h5>What changed?</h5><p>{_e(v4_report.get("what_changed"))}</p></div>'
        f'<div><h5>Sources</h5><p>{sources}</p></div></div>'
        f'<div class="nl-row"><div><h5 class="c-green">Bull case</h5><p>{_e(v4_report.get("bull_case"))}</p></div>'
        f'<div><h5 class="c-red">Bear case</h5><p>{_e(v4_report.get("bear_case"))}</p></div></div>'
        f'<div class="nl-row"><div><h5>Bull thesis fails</h5><p>{_e(v4_report.get("thesis_fails_if"))}</p></div>'
        f'<div><h5>Bull thesis strengthens</h5><p>{_e(v4_report.get("thesis_strengthens_if"))}</p></div></div>'
        f'<div class="nl-meta">V4 weekly report · Wallet {_e(wallet_short)} live · '
        f'No live derivatives feed · Historical MM/CEX movements are evidence of liquid-supply movement/deposits, not proof of sale or manipulation.</div>'
        f'</section>'
    )


def _pump_forensics_detail_html(intel: dict) -> str:
    from lib.v3.forensic_cards import render_pump_forensic_section

    return render_pump_forensic_section(intel)


def _render_article(slug: str, intel: dict, v4_report: dict, hidden: bool = False, wallet_short: str = "") -> str:
    hero = intel["hero"]
    triad = intel.get("triad") or {}
    sym = hero.get("asset", slug.upper())
    hide_cls = " is-hidden" if hidden else ""

    # PUMP: never render empty chrome. Build ALT top from Stage-1/V3 intel if missing.
    if slug == "pump" and not (intel.get("asset_top") or {}):
        from lib.v3.asset_top import build_pump_asset_top

        intel = {**intel, "asset_top": build_pump_asset_top(intel)}

    # SOL product layer: ALT top + split / warn / WCM / reality / evidence cards
    if slug == "sol":
        from lib.v3.sol_product import render_sol_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_sol_product_html(intel)
            + "</article>"
        )

    # RENDER product layer — same shell as SOL/PUMP Job #5 stance
    if slug == "render":
        from lib.v3.render_product import render_render_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_render_product_html(intel)
            + "</article>"
        )

    # BTC product layer — monetary/institutional (no Project Health)
    if slug == "btc":
        from lib.v3.btc_product import render_btc_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_btc_product_html(intel)
            + "</article>"
        )

    # RAY product layer — DEX economics + token value capture
    if slug == "ray":
        from lib.v3.ray_product import render_ray_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_ray_product_html(intel)
            + "</article>"
        )

    # GRASS product layer — revenue vs token capture
    if slug == "grass":
        from lib.v3.grass_product import render_grass_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_grass_product_html(intel)
            + "</article>"
        )

    if slug == "io":
        from lib.v3.io_product import render_io_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_io_product_html(intel)
            + "</article>"
        )

    if slug == "nos":
        from lib.v3.nos_product import render_nos_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_nos_product_html(intel)
            + "</article>"
        )

    if slug == "fartcoin":
        from lib.v3.fartcoin_product import render_fartcoin_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_fartcoin_product_html(intel)
            + "</article>"
        )

    if slug == "spx6900":
        from lib.v3.spx_product import render_spx_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_spx_product_html(intel)
            + "</article>"
        )

    if slug == "zec":
        from lib.v3.zec_product import render_zec_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_zec_product_html(intel)
            + "</article>"
        )

    if slug == "hype":
        from lib.v3.hype_product import render_hype_product_html

        top_html = _alt_top_html(intel.get("asset_top") or {})
        return (
            f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
            + top_html
            + render_hype_product_html(intel)
            + "</article>"
        )

    price_disp = hero.get("price_display", "~$1.32")
    # Never invent RENDER ATH for PUMP — only use hero ath_display when present
    ath_disp = hero.get("ath_display")

    health_metrics = intel.get("project_health", {}).get("metrics", [])
    timing_metrics = intel.get("market_timing", {}).get("metrics", [])
    rs_map = intel.get("relative_strength", {})
    rs_btc_key = f"{slug}_btc"
    rs_btc = rs_map.get(rs_btc_key, {})

    by_id = {m.get("metric_id"): m for m in timing_metrics}
    ath_m = by_id.get("ath_drawdown_pct")
    if slug == "pump":
        # Omit ATH/drawdown until a real PUMP ATH is wired into hero
        ath_disp = ath_disp if ath_disp and ath_disp != "$13.53" else None
        dd_pct = None
    else:
        ath_disp = ath_disp or None
        dd_pct = f"{ath_m.get('value')}%" if ath_m and ath_m.get("value") is not None else None
        if not ath_disp:
            ath_disp = hero.get("ath_display") or None

    if slug == "render":
        health_band = render_health_band(health_metrics)
        warn = warning_stack_render(intel, rs_btc=rs_btc, ath_pct=-float(str(ath_m.get("value", 90)) if ath_m else 90))
        figure = price_figure_render(
            now_price=price_disp.replace("~", ""),
            ath=ath_disp,
        )
        triad_lifecycle = triad["lifecycle"]["display"]
        if triad_lifecycle == "UNCLEAR":
            triad_lifecycle = "Post-cycle / weak leadership"
        triad_lifecycle_detail = triad["lifecycle"]["detail"]
        if "No approved" in triad_lifecycle_detail:
            triad_lifecycle_detail = "Not yet showing the accumulation + relative-strength pattern seen before the 2024 rallies."
        health_display = triad["project_health"]["display"]
        if health_display == "UNCLASSIFIED":
            health_display = "UNKNOWN"
        health_detail = triad["project_health"]["detail"]
        if "Raw evidence" in health_detail:
            health_detail = "Network activity and development remain credible. Fundamentals qualify the project, not the timing."
        timing_display = triad["market_timing"]["display"]
        if timing_display == "UNCLASSIFIED":
            timing_display = "RED–ORANGE"
        timing_detail = triad["market_timing"]["detail"]
        if "Timing classification" in timing_detail:
            timing_detail = "Retraced from ATH; key RS, wallet-flow and leverage confirmation is missing or weak. Retracement is not bad on its own — watch how far and when it turns."
        posture = hero.get("v3_posture") or "UNKNOWN"
        if posture in ("NOT YET WIRED", "HOLD / WAIT", "HOLD/WAIT", "HOLD", "WAIT"):
            posture = "UNKNOWN"
        conf = hero.get("data_completeness", "")
        if "Partial" in conf:
            conf = "Confidence MEDIUM · timing data incomplete"
        thesis = (
            "Strong project health, weak market confirmation. The research says "
            "<b>do not confuse a healthy network with a healthy trade.</b>"
        )
    else:
        health_band = pump_health_band(health_metrics, intel)
        warn = warning_stack_pump(intel)
        figure = ""
        lc = _lifecycle_active_view(intel.get("lifecycle") or {}, n_stages=4)
        lifecycle_active = lc["display_n"]
        lifecycle_ring_seg = lc["ring_seg"]
        ring_label = lc["ring_label"]
        pump_lc_unknown = lc["mode"] == "unknown"

    split_section = (
        '<section class="sec"><div class="sec-head">'
        '<h3>The split that matters</h3>'
        '</div><div class="split">'
        + health_band
        + (
            pump_timing_band(intel, timing_metrics, price_disp.replace("~", ""), ath_disp, dd_pct)
            if slug == "pump"
            else timing_band(sym, timing_metrics, price_disp.replace("~", ""), ath_disp, dd_pct)
        )
        + '</div></section>'
    )

    if slug == "pump":
        ring_n, ring_t = lifecycle_active, ring_label
        stage_n = None if pump_lc_unknown else lifecycle_active
        lifecycle_stages = lifecycle_stages_pump(stage_n)
        ring_seg = lifecycle_ring_seg
        lifecycle_heading = "Capital confirmation path"
        ring_html = lifecycle_ring(stage_n=ring_n, stage_t=ring_t, active_seg=ring_seg, segments=4)
        lifecycle_wrap_cls = "lifecycle lifecycle-pump-4"
    else:
        ring_n, ring_t, ring_seg = "05", "RESET", 4
        lifecycle_stages = lifecycle_stages_render()
        lifecycle_heading = "Lifecycle map"
        ring_html = lifecycle_ring(stage_n=ring_n, stage_t=ring_t, active_seg=ring_seg, segments=5)
        lifecycle_wrap_cls = "lifecycle"

    note_html = ""
    if slug == "pump" and intel.get("lifecycle", {}).get("note"):
        note_html = (
            f'<p class="lifecycle-note">* {_e(intel.get("lifecycle", {}).get("note", ""))}</p>'
        )

    lifecycle_section = (
        '<section class="sec"><div class="sec-head">'
        f"<h3>{_e(lifecycle_heading)}</h3>"
        "</div>"
        + f'<div class="{lifecycle_wrap_cls}">'
        + ring_html
        + lifecycle_stages
        + "</div>"
        + note_html
        + "</section>"
    )

    figure_section = ""
    if figure:
        figure_section = (
            '<section class="sec"><div class="sec-head">'
            '<h3>What actually mattered — as one picture</h3>'
            '</div>' + figure + '</section>'
        )

    if slug == "render":
        triad_html = (
            f'<div class="triad">'
            f'<div class="triad-cell"><span class="label">Lifecycle</span>'
            f'<div class="triad-big">{_e(triad_lifecycle)}</div>'
            f'<div class="triad-sub">{_e(triad_lifecycle_detail)}</div></div>'
            f'<div class="triad-cell"><span class="label">Project health</span>'
            f'<div class="triad-big c-green">{_e(health_display)}</div>'
            f'<div class="triad-sub">{_e(health_detail)}</div></div>'
            f'<div class="triad-cell"><span class="label">Market / timing</span>'
            f'<div class="triad-big c-red">{_e(timing_display)}</div>'
            f'<div class="triad-sub">{_e(timing_detail)}</div></div></div>'
        )
        hero_conf_html = f'<div class="hero-conf">{_e(conf)}</div>' if conf else ""
        top_html = (
            f'<div class="report-hero"><div>'
            f'<span class="label">V3 intelligence · asset research layer</span>'
            f'<h2>{_e(sym)}<span class="hero-price">{_e(price_disp)}</span></h2>'
            f'<p class="hero-thesis">{thesis}</p></div>'
            f'<div class="hero-call-block"><span class="label">Current Stance</span>'
            f'<div class="hero-call">{_e(posture)}</div>'
            f'{hero_conf_html}</div></div>'
            + triad_html
        )
    else:
        # Universal ALT top (Option 3 v5) — PUMP and future alts
        if slug == "pump":
            from lib.v3.pump_amendment_evidence import load_amendment_evidence
            from lib.v3.pump_minidash import render_pump_minidash

            amd = intel.get("amendment") or load_amendment_evidence()
            top_html = _alt_top_html(
                intel.get("asset_top") or {},
                extra=render_pump_minidash(amd),
                stance_clamp=True,
            )
        else:
            top_html = _alt_top_html(intel.get("asset_top") or {})

    return (
        f'<article class="report asset-v3-report{hide_cls}" data-asset="{_e(slug)}">'
        + top_html
        + split_section
        + warn
        + falsifiers_section(intel, slug=slug)
        + ("" if slug == "pump" else lifecycle_section)
        + figure_section
        + knowledge_census_render(intel, slug=slug)
        + (_pump_forensics_detail_html(intel) if slug == "pump" else "")
        + (lifecycle_section if slug == "pump" else "")
        + (_newsletter_html(v4_report, wallet_short) if slug != "pump" else "")
        + (designnote_footer() if slug == "render" else "")
        + '</article>'
    )


def _portfolio_metrics(market: dict, portfolio: dict, bottom_line: str) -> str:
    rotation = next((f for f in market.get("families", []) if f["family_id"] == "outward_rotation"), None)
    breadth = next((f for f in market.get("families", []) if f["family_id"] == "breadth"), None)
    alts_field = next(
        (f for f in (rotation or {}).get("fields", []) if f.get("metric_id") == "alts_beating_btc_30d"),
        None,
    )
    alts_val = alts_field.get("value") if alts_field and alts_field.get("value") is not None else 0
    tracked_n = 8

    usd = portfolio.get("total_usd", 0)
    gbp_note = portfolio.get("holdings_note", "")

    crypto_sub = "BTC down-leg maturing · not confirmed"
    alt_val = "Red"
    alt_sub = "Participation weak · dominance rising"
    if breadth:
        st = (breadth.get("display_state") or "").upper()
        if st == "RED":
            alt_val, alt_sub = "Red", "Participation weak · dominance rising"
        elif st == "ORANGE":
            alt_val, alt_sub = "Orange", breadth.get("note", "Mixed participation")
        elif st == "GREEN":
            alt_val, alt_sub = "Green", breadth.get("note", "Participation supportive")

    return (
        f'<div class="metric-row metric-row-4">'
        f'<div class="metric-card"><div class="label">Portfolio value</div>'
        f'<div class="metric-value">${usd:,.0f}</div>'
        f'<div class="metric-sub">{_e(gbp_note)}</div></div>'
        f'<div class="metric-card"><div class="label">Weekly call</div>'
        f'<div class="metric-value c-orange">WAIT</div>'
        f'<div class="metric-sub">Confidence LOW</div></div>'
        f'<div class="metric-card"><div class="label">Deploy this week</div>'
        f'<div class="metric-value">$0</div>'
        f'<div class="metric-sub">£250/mo planned · not deployed</div></div>'
        f'<div class="metric-card"><div class="label">Alts beating BTC (30d)</div>'
        f'<div class="metric-value c-red">{_e(alts_val)}</div>'
        f'<div class="metric-sub">of {tracked_n} tracked</div></div></div>'
        f'<div class="metric-row metric-row-3">'
        f'<div class="metric-card"><div class="label">Crypto cycle</div>'
        f'<div class="metric-value c-orange">Orange</div>'
        f'<div class="metric-sub">{_e(crypto_sub)}</div></div>'
        f'<div class="metric-card"><div class="label">Alt cycle</div>'
        f'<div class="metric-value c-red">{_e(alt_val)}</div>'
        f'<div class="metric-sub">{_e(alt_sub)}</div></div>'
        f'<div class="metric-card"><div class="label">Bottom line</div>'
        f'<div class="metric-bl">{_e(bottom_line)}</div></div></div>'
    )


def build_index_v3(
    market: dict[str, Any],
    assets: dict[str, dict[str, Any]],
    v4_reports: dict[str, dict[str, Any]],
    report_date: str,
    portfolio: dict[str, Any],
) -> str:
    from lib.v3.html_review_01 import REVIEW_01_CSS, _top_market_section_review_01

    css_path = TEMPLATES / "v3.css"
    design_css = ROOT.parent / "Design" / "render-v3-route-d.html"
    if design_css.exists():
        text = design_css.read_text(encoding="utf-8")
        start = text.index("<style>") + 7
        end = text.index("</style>")
        css = text[start:end]
    else:
        css = css_path.read_text(encoding="utf-8")

    # Surgical overrides — Design CSS still ships 8px dots / 5-col lifecycle
    html_repair_css = """
.lifecycle-note {
  font-size: 0.702rem;
  color: color-mix(in srgb, var(--muted) 50%, #000);
  margin: 0.9rem 0 0;
  font-style: italic;
}
.dot { display: inline-block; width: 20px; height: 20px; border-radius: 50%; margin-right: 8px; flex-shrink: 0; }
.flag-title { font-size: 0.9rem; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase; }
.flag-detail {
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2;
  overflow: hidden; padding-left: 0; margin: 0; font-size: 0.72rem;
  line-height: 1.35; color: var(--muted); max-width: 100%;
}
.flag.has-tip { cursor: default; }
.flag .tip-mark { opacity: 0.55; margin-left: 0.25rem; }
.mline .icon { flex-shrink: 0; }
.mline .mtxt { flex: 1; min-width: 0; }
.mline .metric-val {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  text-align: right;
  max-width: 48%;
  flex: 0 1 auto;
  min-width: 0;
  line-height: 1.25;
  font-size: 0.78rem;
}
.mline.has-tip { cursor: default; position: relative; }
.mline .tip-mark { opacity: 0.55; margin-left: 0.25rem; }
.metric-tip-float {
  max-width: min(380px, calc(100vw - 20px));
  padding: 1rem 1.1rem;
  border-radius: 14px;
  box-shadow: 0 14px 36px rgba(0,0,0,0.22);
  pointer-events: auto;
}
.metric-tip-visual { max-width: min(380px, calc(100vw - 20px)); }
.ev-tip-visual { margin: 0.15rem 0 0.75rem; }
.ev-tip { color: var(--ink); }
.ev-tip-name {
  font-family: var(--display);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}
.ev-tip-read {
  font-family: var(--display);
  font-size: 1.05rem;
  font-weight: 700;
  margin: 0.35rem 0 0.7rem;
  line-height: 1.15;
}
.ev-tip-rows { display: grid; gap: 0.35rem; margin-bottom: 0.7rem; }
.ev-tip-row {
  display: grid;
  grid-template-columns: 6.2rem 1fr;
  gap: 0.55rem;
  font-size: 0.74rem;
  line-height: 1.35;
}
.ev-k { color: var(--muted); font-weight: 600; }
.ev-v { color: var(--ink); word-break: break-word; }
.ev-tip-note {
  margin: 0 0 0.75rem;
  font-size: 0.74rem;
  line-height: 1.4;
  color: var(--ink);
  opacity: 0.92;
}
.ev-tip-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.9rem;
  font-size: 0.66rem;
  color: var(--muted);
  border-top: 1px solid rgba(150,154,172,0.18);
  padding-top: 0.55rem;
}
.ev-tip-link { color: var(--link, #4a7ab8); text-decoration: underline; pointer-events: auto; }
.metric-tip-float { pointer-events: auto; }
.lifecycle-pump-4 { display: grid; grid-template-columns: 150px repeat(4,1fr); gap: 0.6rem; }
.pump-census .count { display: none !important; }
@media (max-width: 900px) {
  .lifecycle-pump-4 { grid-template-columns: 1fr; }
}
"""

    week_label = _format_report_date(report_date)

    wallet_short = portfolio.get("wallet_short", "")
    default_slug = _default_v3_slug(portfolio, assets)
    report_css = (
        ".asset-v3-report.is-hidden { display: none !important; }\n"
        + DESK_CSS
        + HOLD_CARD_CSS
        + html_repair_css
        + ALT_TOP_CSS
        + STANCE_CSS
        + WCM_CSS
        + RC_CSS
        + FORENSIC_CSS
    )
    snapshot = build_snapshot_from_sources(
        portfolio.get("price_sources") or {},
        portfolio.get("fetched_at"),
    )
    data_bar = snapshot_html(snapshot)

    articles = []
    for slug in sorted(V3_ASSET_SLUGS):
        if slug not in assets:
            continue
        articles.append(
            _render_article(
                slug,
                assets[slug],
                v4_reports.get(slug) or {},
                hidden=True,
                wallet_short=wallet_short,
            )
        )

    market_top = _top_market_section_review_01(market, portfolio)

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crypto Decision Report — Route D (Mashup)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Jost:wght@500;600;700;800&display=swap" rel="stylesheet">
<style>{css}{report_css}{REVIEW_01_CSS}</style>
</head>
<body>
<div class="dash">
  <header class="dash-head">
    <h1>Crypto Decision Report</h1>
    <div class="head-right">
      <div class="dash-date">Week of {week_label}</div>
      <button class="theme-btn" id="themeBtn" type="button" aria-label="Toggle dark mode">
        <svg class="icon-moon" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        <svg class="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        <span class="theme-label-dark">Dark</span><span class="theme-label-light">Light</span>
      </button>
    </div>
  </header>

  {data_bar}

  {_desk_section_html()}

  {market_top}

  <section class="holdings" aria-label="Holdings">
    <div class="holdings-grid">{_holdings_html(default_slug, portfolio)}</div>
  </section>

  <div id="asset-report-pane">
  {"\n".join(articles)}
  </div>
</div>
<div id="metric-tip-float" class="metric-tip-float" hidden role="tooltip"></div>
{STANCE_MODAL_SHELL}
<script>
(function () {{
  var root = document.documentElement;
  var saved = localStorage.getItem('cdr-theme');
  if (saved === 'dark') root.setAttribute('data-theme', 'dark');
  document.getElementById('themeBtn').addEventListener('click', function () {{
    var dark = root.getAttribute('data-theme') === 'dark';
    if (dark) {{ root.removeAttribute('data-theme'); localStorage.setItem('cdr-theme', 'light'); }}
    else {{ root.setAttribute('data-theme', 'dark'); localStorage.setItem('cdr-theme', 'dark'); }}
  }});
__DESK_JS__
__HOLD_JS__
  (function () {{
    var tip = document.getElementById('metric-tip-float');
    if (!tip) return;
    var active = null;
    var offset = 12;
    function placeTip(x, y) {{
      tip.style.left = '0'; tip.style.top = '0';
      var w = tip.offsetWidth, h = tip.offsetHeight, pad = 10;
      var left = x - w * 0.25, top = y + offset;
      if (left < pad) left = pad;
      if (left + w > window.innerWidth - pad) left = window.innerWidth - w - pad;
      if (top + h > window.innerHeight - pad) top = y - h - offset;
      if (top < pad) top = pad;
      tip.style.left = Math.round(left) + 'px';
      tip.style.top = Math.round(top) + 'px';
    }}
    function showTip(card, x, y) {{
      var tpl = card.querySelector('.metric-tip-template');
      if (!tpl) return;
      if (tip._hideTimer) {{ clearTimeout(tip._hideTimer); tip._hideTimer = null; }}
      tip.textContent = '';
      tip.innerHTML = tpl.innerHTML;
      tip.classList.add('metric-tip-visual');
      tip.hidden = false;
      active = card;
      placeTip(x, y);
    }}
    function hideTipSoon() {{
      if (tip._hideTimer) clearTimeout(tip._hideTimer);
      tip._hideTimer = setTimeout(function () {{
        tip.hidden = true; tip.innerHTML = ''; tip.classList.remove('metric-tip-visual');
        active = null; tip._hideTimer = null;
      }}, 180);
    }}
    tip.addEventListener('mouseenter', function () {{
      if (tip._hideTimer) {{ clearTimeout(tip._hideTimer); tip._hideTimer = null; }}
    }});
    tip.addEventListener('mouseleave', hideTipSoon);
    document.querySelectorAll('.metric-card.has-tip, .alt-signal.has-tip, .mline.has-tip, .flag.has-tip, .wcm-row.has-tip, .rc-item.has-tip, .econ-dial.has-tip').forEach(function (card) {{
      card.addEventListener('mouseenter', function (e) {{ showTip(card, e.clientX, e.clientY); }});
      card.addEventListener('mousemove', function (e) {{ if (active === card) placeTip(e.clientX, e.clientY); }});
      card.addEventListener('mouseleave', hideTipSoon);
    }});
  }})();
}})();
{STANCE_JS}
</script>
</body>
</html>"""
    return body.replace("__DESK_JS__", DESK_JS).replace(
        "__HOLD_JS__", HOLD_CLICK_JS + HOLD_LIVE_JS
    )


def write_index_v3(
    market: dict[str, Any],
    assets: dict[str, dict[str, Any]],
    v4_reports: dict[str, dict[str, Any]],
    report_date: str,
    portfolio: dict[str, Any],
) -> Path:
    html_out = build_index_v3(market, assets, v4_reports, report_date, portfolio)
    root_path = ROOT.parent / "_Old:archive" / "crypto-app-v3" / "html" / "index-v3-route-d.html"
    root_path.parent.mkdir(parents=True, exist_ok=True)
    root_path.write_text(html_out)
    return root_path
