"""Review 01 — top market layer only (Scrutiny brief). Baseline untouched."""

from __future__ import annotations

import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from lib.asset_v4 import _format_report_date
from lib.paths import ROOT, TEMPLATES
from lib.dashboard_v1 import HOLDING_STRIP_TRAIL
from lib.v3.html_v3 import (
    ALT_TOP_CSS,
    FORENSIC_CSS,
    RC_CSS,
    WCM_CSS,
    _default_v3_slug,
    _e,
    _holdings_html,
    _render_article,
)
from lib.v3.current_stance import STANCE_CSS, STANCE_JS, STANCE_MODAL_SHELL
from lib.v3.market_top_v3 import MARKET_TOP_CSS, overlay_live_feeds, render_market_top_section
from lib.v3.econ_minidash import ECON_DASH_CSS
from lib.v3.route_d_shell import evidence_tip_html

REVIEW_01_CSS = """
.lifecycle-note {
  font-size: 0.702rem;
  color: color-mix(in srgb, var(--muted) 50%, #000);
  margin: 0.9rem 0 0;
  font-style: italic;
}
""" + ECON_DASH_CSS + """
.metric-row-4 { margin-bottom: 0.6rem; }
.metric-card-full { margin-bottom: 0.6rem; }
.metric-tip-float {
  position: fixed; z-index: 9999;
  max-width: min(380px, calc(100vw - 20px));
  padding: 1rem 1.1rem; border-radius: 14px;
  background: var(--surface-strong); color: var(--ink);
  border: 1px solid var(--pill-off);
  font-size: 0.72rem; line-height: 1.45; font-weight: 500;
  box-shadow: 0 14px 36px rgba(0,0,0,0.22);
  pointer-events: auto;
}
.metric-tip-float[hidden] { display: none; }
.metric-card.has-tip { cursor: default; }
.tip-mark {
  display: inline-flex; align-items: center; margin-left: 0.3rem;
  vertical-align: middle; color: var(--muted); opacity: 0.65;
}
.tip-mark svg { width: 0.68rem; height: 0.68rem; stroke: currentColor; fill: none;
  stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.metric-sub-clamp {
  display: flex; align-items: flex-end; gap: 0.35rem; min-width: 0;
}
.metric-sub-text {
  flex: 1; min-width: 0;
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2;
  overflow: hidden; line-height: 1.35;
}
.metric-sub-links {
  display: inline-flex; flex-shrink: 0; align-items: center; gap: 0.2rem;
  align-self: flex-end;
}
.metric-tip-sources-hd { margin-top: 0.45rem; font-size: 0.66rem; font-weight: 700;
  letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); }
.metric-tip-source { font-size: 0.68rem; color: var(--muted); line-height: 1.35; }
.src-link { display: inline-flex; flex-shrink: 0; color: var(--link, #4a7ab8); opacity: 0.3; }
.src-link:hover { opacity: 0.7; }
.src-link-icon { width: 0.75rem; height: 0.75rem; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.src-link-multi { cursor: default; gap: 0.15rem; }
.src-count { font-size: 0.58rem; font-weight: 700; line-height: 1; opacity: 0.9; }
.fg-card .fg-body { display: flex; flex-direction: column; align-items: center; text-align: center; }
.fg-dial-wrap { position: relative; width: 5.5rem; height: 3rem; margin-top: 0.15rem; }
.fg-dial { width: 100%; height: 100%; display: block; }
.fg-dial-track { fill: none; stroke: var(--pill-off); stroke-width: 9; stroke-linecap: round; }
.fg-dial-fill { fill: none; stroke-width: 9; stroke-linecap: round; }
.fg-dial-num { position: absolute; left: 50%; bottom: 0.05rem; transform: translateX(-50%);
  font-family: var(--display); font-size: 1.35rem; font-weight: 700; line-height: 1; }
.fg-card .metric-value { margin-top: 0.2rem; font-size: 1.1rem; }
.fg-label-link { display: inline-flex; margin-left: 0.35rem; vertical-align: middle; }
.fg-tip-hd { font-size: 0.72rem; font-weight: 600; margin-bottom: 0.45rem; }
.fg-tip-scale-wrap { position: relative; height: 12px; margin: 0.35rem 0 0.25rem; }
.fg-tip-scale {
  height: 100%; border-radius: 6px;
  background: linear-gradient(90deg, var(--red) 0%, var(--orange) 35%, var(--muted) 50%, var(--orange) 65%, var(--green) 100%);
}
.fg-tip-needle {
  position: absolute; top: -3px; width: 3px; height: 18px; border-radius: 2px;
  background: var(--ink); transform: translateX(-50%); box-shadow: 0 0 0 2px var(--surface-strong);
}
.fg-tip-scale-labels {
  display: flex; justify-content: space-between; font-size: 0.58rem; color: var(--muted);
  letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 0.5rem;
}
.fg-tip-bars {
  display: flex; align-items: flex-end; gap: 0.28rem; height: 2.2rem; margin-top: 0.15rem;
}
.fg-tip-bar {
  flex: 1; min-width: 0; border-radius: 3px 3px 1px 1px; background: var(--muted); opacity: 0.55;
}
.fg-tip-bar.is-now { opacity: 1; box-shadow: 0 0 0 1px var(--surface-strong); }
.fg-tip-bar.c-red { background: var(--red); }
.fg-tip-bar.c-orange { background: var(--orange); }
.fg-tip-bar.c-muted { background: var(--muted); }
.fg-tip-bar.c-green { background: var(--green); }
.fg-tip-days {
  display: flex; justify-content: space-between; gap: 0.28rem;
  font-size: 0.58rem; color: var(--muted); margin-top: 0.2rem;
}
.fg-tip-day { flex: 1; text-align: center; min-width: 0; }
.fg-tip-day.is-now { font-weight: 700; color: var(--ink); }
.fg-tip-meta { margin-top: 0.45rem; font-size: 0.66rem; color: var(--muted); line-height: 1.4; }
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
.ev-tip-visual { margin: 0.15rem 0 0.75rem; }
.metric-tip-visual { max-width: min(380px, calc(100vw - 20px)); }
""" + MARKET_TOP_CSS

REVIEW_01_FAMILIES = [
    ("macro_liquidity", "MACRO / LIQUIDITY"),
    ("btc_regime", "BTC TREND"),
    ("outward_rotation", "CAPITAL ROTATION"),
    ("breadth", "MARKET PARTICIPATION"),
    ("sector_destination", "SECTOR DESTINATION"),
    ("market_fragility", "LEVERAGE"),
]

_LINK_ICON = (
    '<svg class="src-link-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    '<polyline points="15 3 21 3 21 9"/>'
    '<line x1="10" y1="14" x2="21" y2="3"/>'
    '</svg>'
)

_SOURCES_ICON = (
    '<svg class="src-link-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<rect x="4" y="5" width="16" height="3" rx="0.75" fill="currentColor" stroke="none"/>'
    '<rect x="4" y="10.5" width="16" height="3" rx="0.75" fill="currentColor" stroke="none"/>'
    '<rect x="4" y="16" width="16" height="3" rx="0.75" fill="currentColor" stroke="none"/>'
    '</svg>'
)

_TIP_MARK = (
    '<span class="tip-mark" aria-hidden="true">'
    '<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5"/>'
    '<circle cx="8" cy="5.25" r="0.85" fill="currentColor" stroke="none"/>'
    '<line x1="8" y1="7.25" x2="8" y2="11.25"/></svg></span>'
)


def _btc_days_since_high(evidence: dict | None) -> int | None:
    if not evidence:
        return None
    analysis = evidence.get("btc_analysis") or {}
    market = analysis.get("market") or {}
    rows = evidence.get("btc_daily") or []
    high = market.get("high_365d")
    btc_date = market.get("btc_date")
    if not rows or high is None or not btc_date:
        return None
    slice365 = rows[-365:]
    high_dates = [r["date"] for r in slice365 if r["close"] == high]
    if not high_dates:
        high_dates = [r["date"] for r in slice365 if abs(r["close"] - high) < 1]
    if not high_dates:
        return None
    high_date = max(high_dates)
    return (date.fromisoformat(btc_date) - date.fromisoformat(high_date)).days


def _format_usd_price(val: float) -> str:
    if val >= 1000:
        return f"${val:,.0f}"
    return f"${val:.2f}"


def _subline_html(text: str, links_html: str | None = None) -> str:
    if not text and not links_html:
        return ""
    text_html = f'<span class="metric-sub-text">{_e(text)}</span>' if text else ""
    links = f'<span class="metric-sub-links">{links_html}</span>' if links_html else ""
    return f'<div class="metric-sub metric-sub-clamp">{text_html}{links}</div>'


def _metric_card_html(
    label: str,
    value_html: str,
    sub_html: str,
    tooltip: str | None = None,
    card_class: str = "",
    tip_html: str | None = None,
) -> str:
    """Market cards — tip_html preferred (evidence-card). Legacy tooltip string still accepted."""
    cls = "metric-card has-tip" if (tip_html or tooltip) else "metric-card"
    if card_class:
        cls += f" {card_class}"
    label_html = f'<div class="label">{_e(label)}{_TIP_MARK if (tip_html or tooltip) else ""}</div>'
    if tip_html:
        tip_block = f'<div class="metric-tip-template" hidden>{tip_html}</div>'
    elif tooltip:
        # Convert plain lines into evidence card
        parts = [p.strip() for p in tooltip.replace("\n", "|").split("|") if p.strip()]
        read = parts[0] if parts else label
        note = parts[1] if len(parts) > 1 else ""
        rows = [(f"Detail {i}", p) for i, p in enumerate(parts[2:], start=1)] if len(parts) > 2 else []
        tip_block = (
            f'<div class="metric-tip-template" hidden>'
            f'{evidence_tip_html(name=label, read=read[:80], rows=rows[:4], note=note or read, source="market")}'
            f"</div>"
        )
    else:
        tip_block = ""
    return (
        f'<div class="{cls}">'
        f"{tip_block}"
        f"{label_html}{value_html}{sub_html}</div>"
    )


def _state_class(state: str) -> str:
    s = (state or "").upper()
    if s in (
        "SUPPORTIVE", "CONSTRUCTIVE", "ACCELERATING", "STRENGTHENING",
        "BROADENING", "LOW", "GREEN", "HEALTHY", "CLEAR", "OUTWARD", "UP LEG",
    ):
        return "c-green"
    if s in (
        "RESTRICTIVE", "DETERIORATING", "WEAKENING", "NARROW", "NARROWING",
        "HIGH", "RED", "WEAK", "DOWN LEG", "BTC LED", "HEAVY", "LEVERAGE HEAVY",
        "DRAINING", "FUNDING STRETCHED", "BEAR MARKET",
    ):
        return "c-red"
    if s in (
        "MIXED", "NEUTRAL", "ELEVATED", "ORANGE", "PARTIAL", "UNCLASSIFIED",
    ) or "LEADS" in s:
        return "c-orange"
    return "c-muted"


def _field_val(fam: dict, metric_id: str) -> Any:
    for f in fam.get("fields", []):
        if f.get("metric_id") == metric_id:
            return f.get("value")
    return None


def _family_subline(fam: dict, evidence: dict | None = None, full: bool = False) -> str:
    fid = fam.get("family_id", "")

    if fid == "btc_regime":
        analysis = (evidence or {}).get("btc_analysis") or {}
        market = analysis.get("market") or {}
        high = market.get("high_365d")
        from_hi = _field_val(fam, "btc_from_high_365d_pct") or market.get("from_high_365d_pct")
        leg = _field_val(fam, "btc_current_leg")
        days_since = _btc_days_since_high(evidence)
        r30 = _field_val(fam, "btc_return_30d_pct")
        r90 = _field_val(fam, "btc_return_90d_pct")
        parts = []
        if high is not None:
            parts.append(f"{_format_usd_price(high)} high")
        if from_hi is not None:
            parts.append(f"{from_hi:+.0f}% retraced")
        if days_since is not None:
            parts.append(f"{days_since}d since high")
        if leg:
            parts.append(str(leg))
        if full:
            if r30 is not None:
                parts.append(f"30d {r30:+.1f}%")
            if r90 is not None:
                parts.append(f"90d {r90:+.1f}%")
        return " · ".join(parts) if parts else "BTC swing data unavailable"

    if fid == "outward_rotation":
        eth = _field_val(fam, "eth_btc_30d_pp")
        sol = _field_val(fam, "sol_btc_30d_pp")
        alts = _field_val(fam, "alts_beating_btc_30d")
        bits = []
        if eth is not None:
            bits.append(f"ETH/BTC 30d {eth:+.1f}pp")
        if sol is not None:
            bits.append(f"SOL/BTC 30d {sol:+.1f}pp")
        if alts is not None:
            unit = ""
            for f in fam.get("fields", []):
                if f.get("metric_id") == "alts_beating_btc_30d":
                    unit = f.get("unit") or ""
                    break
            bits.append(f"{alts} {unit} beating BTC")
        return " · ".join(bits) if bits else "Rotation data incomplete"

    if fid == "breadth":
        beat = _field_val(fam, "market_pct_outperforming_btc_30d")
        med = _field_val(fam, "market_median_alt_btc_30d_pp")
        sma = _field_val(fam, "market_pct_above_50dma")
        port = _field_val(fam, "portfolio_beating_btc_30d")
        port_n = ""
        for f in fam.get("fields", []):
            if f.get("metric_id") == "portfolio_beating_btc_30d":
                port_n = f.get("unit") or ""
        parts = []
        if beat is not None:
            parts.append(f"{beat}% outperform BTC")
        if med is not None:
            parts.append(f"median {med:+.1f}pp")
        if sma is not None:
            parts.append(f"{sma}% above 50DMA")
        if port is not None:
            parts.append(f"Holdings {port}/{port_n.replace('of ', '')}")
        return " · ".join(parts) if parts else "Participation data incomplete"

    if fid == "sector_destination":
        ranked_notes = []
        leader_field = next(
            (f for f in fam.get("fields", []) if f.get("metric_id") == "sector_leader"), None
        )
        rank2_field = next(
            (f for f in fam.get("fields", []) if f.get("metric_id") == "sector_rank2"), None
        )
        if leader_field and leader_field.get("note"):
            ranked_notes.append(leader_field["note"].split(" · ")[0])
        if rank2_field and rank2_field.get("note"):
            note = rank2_field["note"]
            if note.startswith("#2 "):
                ranked_notes.append(note.replace("#2 ", "").replace(" vs BTC", ""))
        return " · ".join(ranked_notes) if ranked_notes else "Sector ranks unavailable"

    if fid == "macro_liquidity":
        gl = (evidence or {}).get("global_liquidity") or {}
        parts: list[str] = []
        gp = gl.get("global_pulse_yoy")
        n_reg = gl.get("global_pulse_regions")
        if gp is not None and n_reg:
            parts.append(f"Global {gp:+.1f}% YoY ({n_reg}-region)")
        net_b = gl.get("net_liquidity_usd_b")
        if net_b is not None:
            net_label = f"${net_b / 1000:.2f}T US net" if net_b >= 1000 else f"${net_b:,.0f}B US net"
            parts.append(net_label)
        ecb_yoy = gl.get("ecb_assets_yoy_pct")
        if ecb_yoy is not None:
            parts.append(f"ECB {ecb_yoy:+.1f}%")
        boj_yoy = gl.get("boj_assets_yoy_pct")
        if boj_yoy is not None:
            parts.append(f"BoJ {boj_yoy:+.1f}%")
        nfci = gl.get("nfci_latest")
        if nfci is not None:
            parts.append(f"NFCI {nfci:+.2f}")
        total = _field_val(fam, "stablecoin_supply_total")
        ch30 = _field_val(fam, "stablecoin_supply_30d_pct")
        ch90 = _field_val(fam, "stablecoin_supply_90d_pct")
        if total is not None:
            parts.append(f"${total}B stables")
            if ch30 is not None:
                parts.append(f"30d {ch30:+.1f}%")
            if ch90 is not None and full:
                parts.append(f"90d {ch90:+.1f}%")
        return " · ".join(parts) if parts else "Macro liquidity feeds incomplete"

    if fid == "market_fragility":
        bits: list[str] = []
        oi = _field_val(fam, "oi_mcap")
        vol = _field_val(fam, "perp_spot_volume")
        fund_field = next(
            (f for f in fam.get("fields", []) if f.get("metric_id") == "btc_funding_context"), None
        )
        if oi is not None:
            bits.append(f"OI/mcap {oi:.3f}")
        if vol is not None:
            bits.append(f"perp/spot {vol:.2f}×")
        if fund_field and fund_field.get("note"):
            note = fund_field["note"]
            if full:
                bits.append(note.strip())
            else:
                for strip in (" · no bearish cutoff", "no bearish cutoff", " (91st pct)", "91st pct"):
                    note = note.replace(strip, "")
                if "funding" in note.lower():
                    bits.append(note.split(" · ")[0].strip())
        return " · ".join(bits) if bits else "Leverage context incomplete"

    return fam.get("note") or "Data unavailable"


def _family_source_entries(fam: dict) -> list[tuple[str, str]]:
    seen: set[str] = set()
    entries: list[tuple[str, str]] = []
    for f in fam.get("fields", []):
        url = f.get("source_url")
        src = f.get("source")
        if url and f.get("data_status") == "LIVE" and url not in seen:
            seen.add(url)
            label = (src or "Source").replace("_", " ")
            entries.append((label, url))
    return entries


def _family_source_links_html(fam: dict) -> str:
    entries = _family_source_entries(fam)
    if not entries:
        return ""
    if len(entries) == 1:
        label, url = entries[0]
        return (
            f'<a href="{_e(url)}" class="src-link" target="_blank" rel="noopener" '
            f'title="{_e(label)}">{_LINK_ICON}</a>'
        )
    tips = "; ".join(f"{label}: {url}" for label, url in entries)
    return (
        f'<span class="src-link src-link-multi" title="{_e(tips)}" '
        f'aria-label="{len(entries)} sources">{_SOURCES_ICON}'
        f'<span class="src-count">{len(entries)}</span></span>'
    )


def _family_card_tooltip(fam: dict, evidence: dict | None = None) -> str:
    title = (fam.get("title") or fam.get("family_id") or "SIGNAL").strip()
    state = (fam.get("display_state") or "UNKNOWN").upper()
    question = (fam.get("question") or "").strip()
    full_sub = _family_subline(fam, evidence, full=True)
    state_note = (fam.get("state_validation_note") or "").strip()
    note = (fam.get("note") or "").strip()
    interpretation = state_note or note or question or "Market family read from current evidence."
    rows: list[tuple[str, str]] = []
    if question:
        rows.append(("Question", question))
    if full_sub:
        rows.append(("Evidence", full_sub[:220]))
    sources = _family_source_entries(fam)
    source_label = sources[0][0] if sources else "market feeds"
    if sources:
        rows.append(("Feeds", ", ".join(label for label, _ in sources[:4])))
    as_of = None
    for field in fam.get("fields") or []:
        if field.get("fetched_at"):
            as_of = field.get("fetched_at")
            break
    return evidence_tip_html(
        name=title,
        read=state,
        rows=rows[:4],
        note=interpretation,
        source=source_label,
        as_of=as_of,
    )


def _family_card(fam: dict, label: str, evidence: dict | None = None) -> str:
    state = fam.get("display_state") or "UNKNOWN"
    display = state.upper()
    sub = _family_subline(fam, evidence, full=True)
    links = _family_source_links_html(fam)
    tip = _family_card_tooltip(fam, evidence)
    value_html = f'<div class="metric-value {_state_class(display)}">{_e(display)}</div>'
    return _metric_card_html(label, value_html, _subline_html(sub, links), tip_html=tip)


def _feed_freshness(fetched_at: str, ref_fetched_at: str | None = None) -> str:
    if not fetched_at:
        return "UNKNOWN"
    try:
        dt = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
        ref = datetime.now(timezone.utc)
        if ref_fetched_at:
            ref = datetime.fromisoformat(ref_fetched_at.replace("Z", "+00:00"))
        age = abs((ref - dt).total_seconds())
        if age <= 300:
            return "FRESH"
        if age <= 86400:
            return "STALE"
        return "STALE"
    except ValueError:
        return "UNKNOWN"


def _fg_color_class(val: int) -> str:
    if val <= 25:
        return "c-red"
    if val <= 45:
        return "c-orange"
    if val <= 55:
        return "c-muted"
    if val <= 75:
        return "c-orange"
    return "c-green"


def _fg_dial_color(val: int) -> str:
    if val <= 25:
        return "var(--red)"
    if val <= 45:
        return "var(--orange)"
    if val <= 55:
        return "var(--muted)"
    if val <= 75:
        return "var(--orange)"
    return "var(--green)"


def _fg_tooltip_visual(
    trend: list[dict],
    val: int,
    freshness: str,
    as_of: str,
    src_url: str,
    delta: int | None,
    label: str,
) -> str:
    rows = list(reversed(trend[:7]))
    bars = []
    days = []
    for i, row in enumerate(rows):
        v = int(row.get("value") or 0)
        is_now = i == len(rows) - 1
        cls = f"fg-tip-bar {_fg_color_class(v)}"
        if is_now:
            cls += " is-now"
        bars.append(f'<div class="{cls}" style="height:{max(14, min(100, v))}%"></div>')
        day_cls = "fg-tip-day is-now" if is_now else "fg-tip-day"
        days.append(f'<div class="{day_cls}">{v}</div>')

    delta_txt = f"{delta:+d}" if delta is not None else "—"
    visual = (
        f'<div class="ev-tip-visual">'
        f'<div class="fg-tip-scale-wrap">'
        f'<div class="fg-tip-scale"></div>'
        f'<div class="fg-tip-needle" style="left:{val}%"></div></div>'
        f'<div class="fg-tip-scale-labels"><span>Extreme fear</span><span>Extreme greed</span></div>'
        f'<div class="fg-tip-bars">{"".join(bars)}</div>'
        f'<div class="fg-tip-days">{"".join(days)}</div>'
        f"</div>"
    )
    tip = evidence_tip_html(
        name="FEAR & GREED",
        read=label,
        rows=[
            ("Index", str(val)),
            ("Δ prior", delta_txt),
            ("Freshness", freshness),
            ("As of", as_of or "—"),
        ],
        note="Sentiment context only — not a market vote.",
        source="alternative.me",
        as_of=as_of or None,
    )
    # Inject visual chart under the read line
    return tip.replace(
        f'<div class="ev-tip-read">{_e(label)}</div>',
        f'<div class="ev-tip-read">{_e(label)}</div>{visual}',
        1,
    )


def _fear_greed_card(sf: dict | None) -> str:
    fg = (sf or {}).get("fear_greed") or {}
    src_url = "https://alternative.me/crypto/fear-and-greed-index/"
    if not fg.get("ok"):
        return _metric_card_html(
            "FEAR & GREED",
            '<div class="metric-value c-muted">—</div>',
            "",
            tip_html=evidence_tip_html(
                name="FEAR & GREED",
                read="UNKNOWN",
                rows=[("Feed", "alternative.me")],
                note="Crypto sentiment index unavailable this run. Sentiment context only — not a market vote.",
                source="alternative.me",
            ),
            card_class="fg-card",
        )

    cur = fg.get("current") or {}
    val = int(cur.get("value") or 0)
    word = (cur.get("classification") or "—").title()
    trend = fg.get("recent_trend") or []
    delta = fg.get("delta_vs_prior")
    fetched = fg.get("fetched_at") or ""
    freshness = _feed_freshness(fetched, (sf or {}).get("fetched_at"))
    idx_ts = cur.get("timestamp")
    as_of = ""
    if idx_ts:
        try:
            as_of = datetime.fromtimestamp(int(idx_ts), tz=timezone.utc).strftime("%Y-%m-%d")
        except (TypeError, ValueError, OSError):
            as_of = str(idx_ts)

    dial_color = _fg_dial_color(val)
    link_html = (
        f'<a href="{_e(src_url)}" class="src-link" target="_blank" rel="noopener" '
        f'title="alternative.me Fear & Greed">{_LINK_ICON}</a>'
    )
    value_html = (
        f'<div class="fg-body">'
        f'<div class="fg-dial-wrap">'
        f'<svg class="fg-dial" viewBox="0 0 120 70" aria-hidden="true">'
        f'<path class="fg-dial-track" d="M18 58 A42 42 0 0 1 102 58" pathLength="100"/>'
        f'<path class="fg-dial-fill" d="M18 58 A42 42 0 0 1 102 58" pathLength="100" '
        f'stroke="{dial_color}" stroke-dasharray="{val} 100"/>'
        f'</svg>'
        f'<span class="fg-dial-num" style="color:{dial_color}">{val}</span></div>'
        f'<div class="fg-mood">{_e(word)}</div></div>'
    )
    tip_visual = _fg_tooltip_visual(trend, val, freshness, as_of, src_url, delta, word.upper())
    return (
        f'<div class="metric-card has-tip fg-card">'
        f'<div class="metric-tip-template" hidden>{tip_visual}</div>'
        f'<div class="label">FEAR & GREED{_TIP_MARK}</div>'
        f'{value_html}<div class="card-src">{link_html}</div></div>'
    )


def _top_market_section_review_01(
    market: dict,
    portfolio: dict,
    supporting_feeds: dict | None = None,
    evidence: dict | None = None,
) -> str:
    ev = overlay_live_feeds(evidence)
    if supporting_feeds:
        sf = dict(ev.get("supporting_feeds") or {})
        sf.update({k: v for k, v in supporting_feeds.items() if v})
        ev = overlay_live_feeds({**ev, "supporting_feeds": sf})
    sf = ev.get("supporting_feeds") or supporting_feeds
    fg_card = _fear_greed_card(sf)
    return render_market_top_section(market, portfolio, sf, ev, fg_html=fg_card)


def _placeholder_article(slug: str, ticker: str) -> str:
    """Strip-only stub — no research page yet."""
    return (
        f'<article class="report asset-v3-report is-hidden" data-asset="{_e(slug)}">'
        f'<div class="alt-top"><section class="alt-hero">'
        f'<div class="alt-hero-left">'
        f'<span class="alt-eyebrow">V3 Intelligence · Asset Research Layer</span>'
        f'<h2 class="alt-ticker">{_e(ticker)}</h2>'
        f'<span class="alt-price">—</span>'
        f'</div>'
        f'<div class="alt-stance"><span class="alt-eyebrow">Current Stance</span>'
        f'<div class="alt-stance-headline">COMING NEXT</div>'
        f'<p class="alt-stance-expl">Placeholder in the holdings strip. Research page comes later.</p>'
        f'</div></section></div></article>'
    )


def _load_css() -> str:
    design_css = ROOT.parent / "Design" / "render-v3-route-d.html"
    if design_css.exists():
        text = design_css.read_text(encoding="utf-8")
        start = text.index("<style>") + 7
        end = text.index("</style>")
        return text[start:end]
    return (TEMPLATES / "v3.css").read_text(encoding="utf-8")


def build_index_v3_review_01(
    market: dict[str, Any],
    assets: dict[str, dict[str, Any]],
    v4_reports: dict[str, dict[str, Any]],
    report_date: str,
    portfolio: dict[str, Any],
    supporting_feeds: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> str:
    css = _load_css()
    report_css = (
        ".asset-v3-report.is-hidden { display: none !important; }\n"
        + ALT_TOP_CSS
        + STANCE_CSS
        + WCM_CSS
        + RC_CSS
        + FORENSIC_CSS
    )
    week_label = _format_report_date(report_date)

    wallet_short = portfolio.get("wallet_short", "")
    default_slug = _default_v3_slug(portfolio, assets)

    articles = []
    for slug in sorted(
        {"btc", "ray", "render", "pump", "sol", "grass", "io", "nos", "fartcoin", "spx6900", "zec", "hype"}
    ):
        if slug not in assets:
            continue
        articles.append(
            _render_article(
                slug,
                assets[slug],
                v4_reports.get(slug) or {},
                hidden=slug != default_slug,
                wallet_short=wallet_short,
            )
        )
    for tick in HOLDING_STRIP_TRAIL:
        slug = tick.lower()
        if slug in assets:
            continue
        articles.append(_placeholder_article(slug, tick))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crypto Decision Report — V3 Review 01</title>
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
      <div class="week" id="weekSwitch">
        <button class="week-btn" type="button" aria-haspopup="listbox" aria-expanded="false" aria-label="Choose week">
          <span>Week of {week_label} · Review 01</span>
          <svg class="week-chev" viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5"/></svg>
        </button>
        <div class="week-menu" role="listbox">
          <a class="week-opt is-current" href="index-v3-review-01.html" role="option">
            <span class="week-opt-date">Week of {week_label}</span>
            <span class="week-opt-sub">Review 01</span>
          </a>
          <a class="week-opt" href="index-v3-review-02.html" role="option">
            <span class="week-opt-date">Week of 16th of August, 2026</span>
            <span class="week-opt-sub">Review 02</span>
          </a>
        </div>
      </div>
      <button class="theme-btn" id="themeBtn" type="button" aria-label="Toggle dark mode">
        <svg class="icon-moon" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        <svg class="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        <span class="theme-label-dark">Dark</span><span class="theme-label-light">Light</span>
      </button>
    </div>
  </header>

  {_top_market_section_review_01(market, portfolio, supporting_feeds, evidence)}

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
  (function () {{
    var week = document.getElementById('weekSwitch');
    if (!week) return;
    var btn = week.querySelector('.week-btn');
    btn.addEventListener('click', function (e) {{
      e.stopPropagation();
      var open = !week.classList.contains('is-open');
      week.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }});
    document.addEventListener('click', function () {{
      week.classList.remove('is-open');
      btn.setAttribute('aria-expanded', 'false');
    }});
    document.addEventListener('keydown', function (e) {{
      if (e.key === 'Escape') {{
        week.classList.remove('is-open');
        btn.setAttribute('aria-expanded', 'false');
      }}
    }});
  }})();
  document.querySelectorAll('.hold').forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      var slug = btn.getAttribute('data-asset-slug');
      document.querySelectorAll('.hold').forEach(function (b) {{ b.classList.remove('active'); }});
      btn.classList.add('active');
      document.querySelectorAll('.asset-v3-report').forEach(function (el) {{
        if (slug && el.getAttribute('data-asset') === slug) {{
          el.classList.remove('is-hidden');
        }} else {{
          el.classList.add('is-hidden');
        }}
      }});
    }});
  }});
  // Always open on the active holdings tab (BTC by default).
  (function () {{
    var start = document.querySelector('.hold.active[data-asset-slug]')
      || document.querySelector('.hold[data-asset-slug="btc"]')
      || document.querySelector('.hold[data-asset-slug]');
    if (start) start.click();
  }})();
  (function () {{
    var tip = document.getElementById('metric-tip-float');
    if (!tip) return;
    var active = null;
    var offset = 12;
    function placeTip(x, y) {{
      tip.style.left = '0';
      tip.style.top = '0';
      var w = tip.offsetWidth;
      var h = tip.offsetHeight;
      var pad = 10;
      var left = x - w * 0.25;
      var top = y + offset;
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
        tip.hidden = true;
        tip.innerHTML = '';
        tip.classList.remove('metric-tip-visual');
        active = null;
        tip._hideTimer = null;
      }}, 180);
    }}
    tip.addEventListener('mouseenter', function () {{
      if (tip._hideTimer) {{ clearTimeout(tip._hideTimer); tip._hideTimer = null; }}
    }});
    tip.addEventListener('mouseleave', hideTipSoon);
    document.querySelectorAll('.metric-card.has-tip, .alt-signal.has-tip, .mline.has-tip, .flag.has-tip, .wcm-row.has-tip, .rc-item.has-tip, .fx-card.has-tip, .econ-dial.has-tip').forEach(function (card) {{
      card.addEventListener('mouseenter', function (e) {{ showTip(card, e.clientX, e.clientY); }});
      card.addEventListener('mousemove', function (e) {{
        if (active === card) placeTip(e.clientX, e.clientY);
      }});
      card.addEventListener('mouseleave', hideTipSoon);
    }});
  }})();
}})();
{STANCE_JS}
</script>
</body>
</html>"""


def splice_market_top_into_html(
    existing_html: str,
    market: dict[str, Any],
    portfolio: dict[str, Any],
    supporting_feeds: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> str:
    """Replace only the market-intelligence section. Asset articles stay byte-identical."""
    new_sec = _top_market_section_review_01(market, portfolio, supporting_feeds, evidence)
    pat = re.compile(
        r'<section aria-label="Market intelligence">.*?</section>',
        re.S,
    )
    if not pat.search(existing_html):
        raise RuntimeError("Market intelligence section missing — refuse to splice")
    html = pat.sub(lambda _m: new_sec, existing_html, count=1)
    if ".mkt-lead-title" not in html or ".proto-port .metric-value" not in html:
        html = html.replace("</style>", MARKET_TOP_CSS + "\n</style>", 1)
    return html


JOB8_LAYOUT_CSS = """
/* job8-visual-qa */
.fx-grid-2, .fx-mini-grid, .fx-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; }
.fx-status {
  display: inline-flex; align-items: center; margin-top: 10px; padding: 2px 8px;
  border-radius: 999px; font-size: 0.58rem; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; background: rgba(150,154,172,0.16); color: var(--muted); line-height: 1.3;
}
.fx-status.is-known { background: var(--green-wash); color: var(--green); }
.fx-status.is-partial, .fx-status.is-conflict { background: var(--orange-wash, #efe8ea); color: var(--orange); }
.fx-status.is-unknown, .fx-status.is-muted { background: rgba(150,154,172,0.16); color: var(--muted); }
.split { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
.band { min-width: 0; }
.band-token { background: var(--red-wash); }
.band-status { white-space: normal; overflow-wrap: anywhere; line-height: 1.35; max-width: 100%; }
.mline { min-width: 0; }
.mline .metric-val {
  white-space: normal !important; overflow-wrap: anywhere; word-break: break-word;
  text-align: right; max-width: 48%; flex: 0 1 auto; min-width: 0; line-height: 1.25; font-size: 0.78rem;
}
.fx-card-read, .fx-kpi strong { overflow-wrap: anywhere; word-break: break-word; }
@media (max-width: 850px) {
  .fx-grid-2, .fx-mini-grid, .fx-grid, .split { grid-template-columns: 1fr; }
  .mline .metric-val { max-width: 100%; text-align: left; }
}
"""


def inject_job8_layout_css(html: str) -> str:
    """Patch live canonical CSS without a full HTML rebuild (BTC/SOL/PUMP articles stay)."""
    html = re.sub(
        r"\.mline \.metric-val \{\s*white-space: nowrap;.*?line-height: 1\.2;\s*\}",
        ".mline .metric-val {\n  white-space: normal;\n  overflow-wrap: anywhere;\n"
        "  word-break: break-word;\n  text-align: right;\n  max-width: 48%;\n"
        "  flex: 0 1 auto;\n  min-width: 0;\n  line-height: 1.25;\n  font-size: 0.78rem;\n}",
        html,
        count=1,
        flags=re.S,
    )
    html = html.replace(
        ".fx-grid-2, .fx-mini-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }",
        ".fx-grid-2, .fx-mini-grid, .fx-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; }",
        1,
    )
    html = html.replace(
        ".fx-kpi strong {\n  display: block;\n  font-family: var(--display);\n  font-size: 1rem;\n  font-weight: 700;\n  line-height: 1.1;\n}",
        ".fx-kpi strong {\n  display: block;\n  font-family: var(--display);\n  font-size: 0.88rem;\n  font-weight: 700;\n  line-height: 1.15;\n  overflow-wrap: anywhere;\n  word-break: break-word;\n}",
        1,
    )
    if "job8-visual-qa" not in html:
        html = html.replace("</style>", JOB8_LAYOUT_CSS + "\n</style>", 1)
    return html


def splice_asset_articles_into_html(existing_html: str, articles: dict[str, str]) -> str:
    """Replace named asset <article> blocks. Does not touch Market Top / other assets."""
    html = existing_html
    for slug, article in articles.items():
        pat = re.compile(
            rf'<article class="report asset-v3-report[^"]*" data-asset="{re.escape(slug)}">.*?</article>',
            re.S,
        )
        html, n = pat.subn(article, html, count=1)
        if n != 1:
            raise RuntimeError(f"Failed to splice article data-asset={slug} (n={n})")
    return html


def _canonical_html_path() -> Path:
    env = os.environ.get("WEEKLY_V3_CANONICAL")
    return Path(env) if env else ROOT.parent / "_Old:archive" / "crypto-app-v3" / "html" / "builder-output.html"


def write_index_v3_review_01(
    market: dict[str, Any],
    assets: dict[str, Any],
    v4_reports: dict[str, Any],
    report_date: str,
    portfolio: dict[str, Any],
    supporting_feeds: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
    out_path: Path | None = None,
) -> Path:
    html = build_index_v3_review_01(
        market, assets, v4_reports, report_date, portfolio, supporting_feeds, evidence
    )
    dest = out_path if out_path is not None else _canonical_html_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html)
    return dest
