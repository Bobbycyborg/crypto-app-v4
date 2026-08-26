"""Verbatim Route D HTML shells — structure locked to render-v3-route-d.html."""

from __future__ import annotations

import html
from typing import Any

# ---- SVG icons (exact from Route D) ----
ICON_GRID = '<svg class="icon" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>'
ICON_NODES = '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="5" r="2.2"/><circle cx="5" cy="18" r="2.2"/><circle cx="19" cy="18" r="2.2"/><path d="M12 7.2 6 16M12 7.2 18 16M7.2 18h9.6"/></svg>'
ICON_DROP = '<svg class="icon" viewBox="0 0 24 24"><path d="M12 3c2 3.5 6 5.5 6 10a6 6 0 0 1-12 0c0-4.5 4-6.5 6-10z"/><path d="M12 13c1 1.2 2 2 2 3.6a2 2 0 0 1-4 0c0-1.6 1-2.4 2-3.6z"/></svg>'
ICON_RATIO = '<svg class="icon" viewBox="0 0 24 24"><circle cx="7" cy="7" r="3"/><circle cx="17" cy="17" r="3"/><path d="M19 5 5 19"/></svg>'
ICON_CIRCLES = '<svg class="icon" viewBox="0 0 24 24"><circle cx="8" cy="12" r="5"/><circle cx="16" cy="12" r="5"/></svg>'
ICON_CIRCLES_DIAG = '<svg class="icon" viewBox="0 0 24 24"><circle cx="8" cy="8" r="4"/><circle cx="16" cy="16" r="4"/><path d="M19 5 5 19"/></svg>'
ICON_BAG = '<svg class="icon" viewBox="0 0 24 24"><path d="M4 9h16l-2 11H6L4 9z"/><path d="M8 9a4 4 0 0 1 8 0"/></svg>'
ICON_LEVERAGE = '<svg class="icon" viewBox="0 0 24 24"><path d="M12 4v3M4 20a8 8 0 0 1 16 0"/><path d="M12 20l4-6"/></svg>'
ICON_WRENCH = '<svg class="icon" viewBox="0 0 24 24"><path d="M14.7 6.3a4.5 4.5 0 0 0-6 6L3 18l3 3 5.7-5.7a4.5 4.5 0 0 0 6-6L14 13l-3-3 3.7-3.7z"/></svg>'
ICON_UP = '<svg class="icon" viewBox="0 0 24 24"><path d="M3 18l6-7 4 4 8-9"/><path d="M21 6v5h-5"/></svg>'
ICON_BARS = '<svg class="icon" viewBox="0 0 24 24"><path d="M5 21V10M12 21V4M19 21v-8"/></svg>'
ICON_DOWN = '<svg class="icon" viewBox="0 0 24 24"><path d="M12 3v12M8 11l4 4 4-4"/><path d="M4 21h16"/></svg>'
ICON_WARN = '<svg class="icon" viewBox="0 0 24 24"><path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5M12 18v.5"/></svg>'
ICON_DIST = '<svg class="icon" viewBox="0 0 24 24"><path d="M12 21V9M8 13l4-4 4 4"/><path d="M4 3h16"/></svg>'
ICON_LEV_DOWN = '<svg class="icon" viewBox="0 0 24 24"><path d="M12 4v3M4 20a8 8 0 0 1 16 0"/><path d="M12 20l-5-4"/></svg>'


def _e(s: Any) -> str:
    return html.escape(str(s)) if s is not None else ""


def _page_ticker(intel: dict | None = None, slug: str | None = None) -> str:
    raw = (
        slug
        or ((intel or {}).get("meta") or {}).get("slug")
        or ((intel or {}).get("hero") or {}).get("asset")
        or ""
    )
    s = str(raw).strip().upper()
    if s in ("SPX6900", "SPX"):
        return "SPX"
    return s


def _stage1_source_label(
    item_source: str | None,
    intel: dict | None = None,
    slug: str | None = None,
) -> str:
    """Never invent another asset's evidence stamp. Empty → this page's Stage-1, else UNKNOWN."""
    page = _page_ticker(intel, slug)
    src = (item_source or "").strip()
    if src.lower() in ("", "—", "-", "unknown", "asset evidence", "stage-1 evidence"):
        src = ""
    if src.lower() == "pump evidence" and page != "PUMP":
        src = ""
    if src:
        return src
    if page:
        return f"{page} Stage-1 evidence"
    return "UNKNOWN"


from lib.v3.change_mind import STATUSES  # live status vocabulary
from lib.v3.fields import concerning_meter


TIP_MARK = (
    '<span class="tip-mark" aria-hidden="true">'
    '<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5"/>'
    '<circle cx="8" cy="5.25" r="0.85" fill="currentColor" stroke="none"/>'
    '<line x1="8" y1="7.25" x2="8" y2="11.25"/></svg></span>'
)


def mline(icon: str, label: str, small: str, value: str, val_cls: str = "") -> str:
    cls = f"metric-val {_e(val_cls)}".strip()
    return (
        f'<div class="mline">{icon}<div class="mtxt"><strong>{_e(label)}</strong>'
        f'<small>{_e(small)}</small></div><div class="{cls}">{_e(value)}</div></div>'
    )


def evidence_tip_html(
    *,
    name: str,
    read: str,
    rows: list[tuple[str, str]],
    note: str,
    source: str,
    as_of: str | None = None,
    source_url: str | None = None,
    confidence: str | None = None,
    freshness: str | None = None,
) -> str:
    """Small designed evidence card for tooltips."""
    if (source or "").strip() in ("", "—", "-", "–"):
        source = "UNKNOWN"
    row_html = "".join(
        f'<div class="ev-tip-row"><span class="ev-k">{_e(k)}</span>'
        f'<span class="ev-v">{_e(v)}</span></div>'
        for k, v in rows
        if v
    )
    if source_url:
        src_bit = (
            f'<a class="ev-tip-link" href="{_e(source_url)}" target="_blank" rel="noopener">'
            f"{_e(source)}</a>"
        )
    else:
        src_bit = _e(source)
    foot_parts = [f"<div>Source · {src_bit}</div>"]
    if confidence:
        foot_parts.append(f"<div>Confidence · {_e(confidence)}</div>")
    if as_of:
        foot_parts.append(f"<div>As of · {_e(as_of)}</div>")
    if freshness:
        foot_parts.append(f"<div>Freshness · {_e(freshness)}</div>")
    return (
        f'<div class="ev-tip">'
        f'<div class="ev-tip-name">{_e(name)}</div>'
        f'<div class="ev-tip-read">{_e(read)}</div>'
        f'<div class="ev-tip-rows">{row_html}</div>'
        f'<p class="ev-tip-note">{_e(note)}</p>'
        f'<div class="ev-tip-foot">{"".join(foot_parts)}</div>'
        f"</div>"
    )


def mline_tip(
    icon: str,
    label: str,
    small: str,
    value: str,
    tip_html: str,
    val_cls: str = "",
) -> str:
    """Split-section metric row: short display + structured evidence tooltip."""
    cls = f"metric-val {_e(val_cls)}".strip()
    return (
        f'<div class="mline has-tip">'
        f"{icon}"
        f'<div class="mtxt"><strong>{_e(label)}{TIP_MARK}</strong>'
        f"<small>{_e(small)}</small></div>"
        f'<div class="{cls}">{_e(value)}</div>'
        f'<div class="metric-tip-template" hidden>{tip_html}</div>'
        f"</div>"
    )


def lifecycle_ring(
    stage_n: str = "05",
    stage_t: str = "RESET",
    active_seg: int | None = 4,
    *,
    segments: int = 5,
) -> str:
    """Ring SVG — active_seg lit orange. None = no asserted stage (UNKNOWN)."""
    n = max(2, int(segments))
    circ = 2 * 3.1415926535 * 62
    seg_len = circ / n
    dash = f"{seg_len * 0.85:.2f} {circ - seg_len * 0.85:.2f}"
    step = 360 / n
    segs = []
    for i in range(n):
        on = " on" if active_seg is not None and i == active_seg else ""
        segs.append(
            f'<circle class="ring-seg{on}" cx="90" cy="90" r="62" '
            f'stroke-dasharray="{dash}" transform="rotate({step * i} 90 90)"/>'
        )
    aria = f"{n}-segment capital confirmation ring" if n == 4 else f"{n}-segment lifecycle ring"
    if active_seg is None:
        aria = f"{aria} · UNKNOWN — no active stage"
    return (
        f'<div class="stage-ring"><svg viewBox="0 0 180 180" role="img" aria-label="{aria}">'
        f'<g transform="rotate(-90 90 90)">{"".join(segs)}</g>'
        f'<text class="ring-center-n" x="90" y="88" text-anchor="middle">{_e(stage_n)}</text>'
        f'<text class="ring-center-t" x="90" y="108" text-anchor="middle">{_e(stage_t)}</text>'
        "</svg></div>"
    )


def lifecycle_stages_render() -> str:
    return (
        '<div class="stage"><span class="n">01</span><h5>Accumulation</h5><p>Large-wallet withdrawals, RS turning up, spot demand before mass attention.</p></div>'
        '<div class="stage"><span class="n">02</span><h5>Leadership</h5><p>RENDER beats BTC, SOL and AI peers; fundamentals validate the story.</p></div>'
        '<div class="stage"><span class="n">03</span><h5>Reflexivity</h5><p>AI/NVIDIA narrative, catalyst anticipation, price accelerates.</p></div>'
        '<div class="stage"><span class="n">04</span><h5>Distribution</h5><p>Controlled supply enters MM/CEX infrastructure; price fails despite good news.</p></div>'
        '<div class="stage active"><span class="now-tag">NOW</span><span class="n">05</span><h5>Reset / base</h5><p>Fundamentals survive, but leadership must return before a new cycle is trusted.</p></div>'
    )


def price_figure_render(now_price: str = "$1.32", ath: str = "$13.53") -> str:
    return f"""
      <div class="figure">
        <svg viewBox="0 0 1000 330" role="img" aria-label="RENDER price journey 2023 to 2026 with six annotated forensic events">
          <path class="fig-area" d="M0,292 C60,288 130,262 180,232 C210,215 240,246 265,250 C300,255 310,222 335,207 C380,180 430,90 470,44 C495,15 505,90 520,140 C545,215 555,95 580,72 C605,50 640,140 680,182 C760,262 900,268 1000,272 L1000,330 L0,330 Z"/>
          <path class="fig-price" d="M0,292 C60,288 130,262 180,232 C210,215 240,246 265,250 C300,255 310,222 335,207 C380,180 430,90 470,44 C495,15 505,90 520,140 C545,215 555,95 580,72 C605,50 640,140 680,182 C760,262 900,268 1000,272"/>
          <line class="fig-drop" x1="180" y1="232" x2="180" y2="310"/>
          <line class="fig-drop" x1="335" y1="207" x2="335" y2="310"/>
          <line class="fig-drop" x1="452" y1="70" x2="452" y2="310"/>
          <line class="fig-drop" x1="470" y1="44" x2="470" y2="16"/>
          <line class="fig-drop" x1="580" y1="72" x2="580" y2="310"/>
          <line class="fig-drop" x1="985" y1="272" x2="985" y2="310"/>
          <circle class="fig-mark" cx="180" cy="232" r="6"/>
          <circle class="fig-mark" cx="335" cy="207" r="6"/>
          <circle class="fig-mark-red" cx="452" cy="70" r="6"/>
          <circle class="fig-mark" cx="470" cy="44" r="6"/>
          <circle class="fig-mark-green" cx="580" cy="72" r="6"/>
          <circle class="fig-mark-red" cx="985" cy="272" r="6"/>
          <text class="fig-tag" x="168" y="260">A</text>
          <text class="fig-tag" x="323" y="235">B</text>
          <text class="fig-tag" x="426" y="98">C</text>
          <text class="fig-tag" x="463" y="12">D</text>
          <text class="fig-tagnote" x="478" y="34">ATH {_e(ath)} · Mar 2024</text>
          <text class="fig-tag" x="592" y="66">E</text>
          <text class="fig-tag" x="962" y="260">F</text>
          <text class="fig-tagnote" x="878" y="245">Now {_e(now_price)} · −90%</text>
          <text class="fig-axis" x="0" y="326">2023</text>
          <text class="fig-axis" x="380" y="326">2024</text>
          <text class="fig-axis" x="680" y="326">2025</text>
          <text class="fig-axis" x="950" y="326">2026</text>
        </svg>
        <div class="legend">
          <div class="leg"><span class="key">A</span><div><b>2023 · Price led fundamentals</b><span>RNDR rose ~425% before BME burns were live. Burn alone is not a timing engine.</span></div></div>
          <div class="leg"><span class="key">B</span><div><b>Dec 2023 · Whale two-way churn</b><span>8.13M RNDR toward Coinbase while 5.29M was withdrawn by new whales — not simple distribution.</span></div></div>
          <div class="leg"><span class="key" style="color:var(--red)">C</span><div><b>9 Mar 2024 · RESEARCH CLAIM · ~2.266M RNDR → GSR</b><span>Secondary research only — <b>NOT on-chain verified.</b> Alleged controlled supply into liquidity infra before ATH. Intent unknown.</span></div></div>
          <div class="leg"><span class="key">D</span><div><b>Mar 2024 · Catalyst saturation</b><span>AI/GPU leadership, BTC strength and NVIDIA GTC anticipation culminated at the top.</span></div></div>
          <div class="leg"><span class="key" style="color:var(--green)">E</span><div><b>Apr–May 2024 · Spot support, then failure</b><span>Research claims whale accumulation — bullish setup failed ATH; GSR-linked narrative unverified on-chain.</span></div></div>
          <div class="leg"><span class="key" style="color:var(--red)">F</span><div><b>2026 · Reset</b><span>Fundamentals survived; leadership did not. This is where the report finds RENDER today.</span></div></div>
        </div>
        <div class="fig-cap">Schematic curve reconstructed from the forensic research — illustrative shape, not live price data.</div>
      </div>"""


def capital_confirmation_stages_pump(active_n: str | None = "03") -> str:
    stages = [
        ("01", "Platform health", "Revenue, buyback/burn and launchpad share supportive."),
        ("02", "Relative leadership", "PUMP outperforming BTC and SOL on wired RS."),
        ("03", "Spot confirmation", "Spot participation sufficient versus leverage."),
        ("04", "Buyer confirmation", "Repeat or high-quality net spot buyers identified."),
    ]
    parts = []
    for n, title, body in stages:
        is_active = bool(active_n) and n == active_n
        active = " active" if is_active else ""
        now = '<span class="now-tag">NOW</span>' if is_active else ""
        parts.append(
            f'<div class="stage{active}">{now}<span class="n">{n}</span>'
            f"<h5>{_e(title)}</h5><p>{_e(body)}</p></div>"
        )
    return "".join(parts)


def lifecycle_stages_pump(active_n: str | None = "03") -> str:
    return capital_confirmation_stages_pump(active_n)


# Stroke icons for change-mind mockup (exact paths)
WCM_ICONS = {
    "up": (
        '<svg class="wcm-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">'
        '<path d="M3 17l6-6 4 4 8-9"/><path d="M17 6h4v4"/></svg>'
    ),
    "lev": (
        '<svg class="wcm-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">'
        '<path d="M4 19a8 8 0 0 1 16 0"/><path d="M12 19l5-6"/></svg>'
    ),
    "bars": (
        '<svg class="wcm-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">'
        '<path d="M5 20V11M12 20V5M19 20v-7"/></svg>'
    ),
    "warn": (
        '<svg class="wcm-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">'
        '<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5M12 18v.5"/></svg>'
    ),
    "dist": (
        '<svg class="wcm-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">'
        '<path d="M12 20V8M8 12l4-4 4 4"/><path d="M4 4h16"/></svg>'
    ),
    "lev_down": (
        '<svg class="wcm-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">'
        '<path d="M4 19a8 8 0 0 1 16 0"/><path d="M12 19l-5-5"/></svg>'
    ),
}


def _wcm_status_class(status: str, *, defensive: bool) -> str:
    st = (status or "UNKNOWN").upper()
    if st == "UNKNOWN":
        return "c-muted"
    if defensive:
        if st == "YES":
            return "c-red"
        if st == "NO":
            return "c-green"
        return "c-orange"  # PARTIAL / WATCH
    if st == "YES":
        return "c-green"
    if st == "NO":
        return "c-red"
    return "c-orange"


def _wcm_row_html(
    item: dict,
    *,
    defensive: bool = False,
    intel: dict | None = None,
    slug: str | None = None,
) -> str:
    status = (item.get("status") or "UNKNOWN").upper()
    title = item.get("title") or item.get("label") or ""
    summary = item.get("summary") or item.get("detail") or ""
    icon = WCM_ICONS.get(item.get("icon") or "up", WCM_ICONS["up"])
    rows = item.get("evidence_rows") or []
    tip_rows = [(r.get("key"), r.get("value")) for r in rows if isinstance(r, dict)]
    tip = evidence_tip_html(
        name=title,
        read=f"Current read: {status}",
        rows=tip_rows[:5],
        note=item.get("interpretation") or summary,
        source=_stage1_source_label(item.get("source"), intel, slug),
        as_of=item.get("as_of"),
        source_url=item.get("source_url"),
        confidence=item.get("confidence"),
    )
    st_cls = _wcm_status_class(status, defensive=defensive)
    return (
        f'<div class="wcm-row has-tip">'
        f'<div class="metric-tip-template" hidden>{tip}</div>'
        f"{icon}"
        f'<div class="wcm-row-title">{_e(title)}</div>'
        f'<div class="wcm-status {st_cls}">{_e(status)}</div>'
        f'<div class="wcm-info" aria-hidden="true">i</div>'
        f'<div class="wcm-row-sub">{_e(summary)}</div>'
        f"</div>"
    )


def change_mind_section(intel: dict | None = None, slug: str = "render") -> str:
    """Approved mockup layout — live status per condition. PUMP only for now."""
    wcm = (intel or {}).get("what_would_change_mind") or {}
    constructive = wcm.get("constructive") or []
    defensive = wcm.get("defensive") or []

    # Legacy shape fallback (old REQUIRED/WARNING lists)
    if not constructive and wcm.get("more_constructive"):
        constructive = [
            {
                "title": x.get("label"),
                "summary": x.get("detail"),
                "status": x.get("status") if x.get("status") in STATUSES else "UNKNOWN",
                "icon": "up",
                "interpretation": x.get("detail"),
                "evidence_rows": [],
                "source": "legacy",
            }
            for x in wcm["more_constructive"]
        ]
    if not defensive and wcm.get("more_defensive"):
        defensive = [
            {
                "title": x.get("label"),
                "summary": x.get("detail"),
                "status": x.get("status") if x.get("status") in STATUSES else "UNKNOWN",
                "icon": "warn",
                "interpretation": x.get("detail"),
                "evidence_rows": [],
                "source": "legacy",
            }
            for x in wcm["more_defensive"]
        ]

    if not constructive and not defensive:
        return wcm_unavailable_section()

    cons = "".join(_wcm_row_html(c, defensive=False, intel=intel, slug=slug) for c in constructive)
    defs = "".join(_wcm_row_html(d, defensive=True, intel=intel, slug=slug) for d in defensive)
    return (
        '<section class="sec wcm-sec">'
        '<h3 class="wcm-title">What would change our mind?</h3>'
        '<div class="wcm-grid">'
        '<section class="wcm-card good">'
        "<h2>More constructive</h2>"
        '<div class="wcm-kicker">Would strengthen the setup</div>'
        f'<div class="wcm-rows">{cons}</div></section>'
        '<section class="wcm-card bad">'
        "<h2>More defensive</h2>"
        '<div class="wcm-kicker">Would weaken the setup</div>'
        f'<div class="wcm-rows">{defs}</div></section>'
        "</div></section>"
    )


def wcm_unavailable_section() -> str:
    """No asset-specific WCM — never substitute another asset's conditions."""
    return (
        '<section class="sec wcm-sec">'
        '<h3 class="wcm-title">What would change our mind?</h3>'
        '<p class="wcm-unavailable">UNKNOWN — asset-specific conditions are not available.</p>'
        "</section>"
    )


def falsifiers_section_legacy_render() -> str:
    """Deprecated. Must not inject RENDER WCM into any asset."""
    return wcm_unavailable_section()


def falsifiers_section(intel: dict | None = None, slug: str = "render") -> str:
    return change_mind_section(intel, slug=slug)


def designnote_footer() -> str:
    return (
        '<footer class="designnote">'
        '<b>ROUTE D — FINAL MASHUP.</b> Route A base (fonts, soft boxes, light paper) + B\'s bigger titles and giant lifecycle numerals + C\'s warning meter and dark palette behind the theme button + E\'s iconed split, price-journey figure, change-our-mind and knowledge census + F\'s lifecycle ring docked left of the stages. Chart curve remains schematic until live data is wired in.'
        '</footer>'
    )


def _fmt_frames(n: int | float | None, status: str | None = None) -> str:
    if status == "FAILED":
        return "FAILED"
    if n is None:
        return "MISSING"
    v = float(n)
    if v >= 1_000_000:
        return f"{v / 1_000_000:.2f}M FRAMES"
    return f"{int(v):,} FRAMES"


def render_health_band(metrics: list[dict]) -> str:
    by_id = {m.get("metric_id"): m for m in metrics}
    frames = by_id.get("frames_rendered")
    nodes = by_id.get("nodes_total")
    burned = by_id.get("cumulative_burned")
    burn_ratio = by_id.get("burn_emission_ratio")

    frames_st = frames.get("data_status") if frames else None
    frames_val = _fmt_frames(frames.get("value") if frames else None, frames_st)
    frames_cls = "c-green" if frames and frames.get("value") is not None else "c-muted"
    if frames_st == "FAILED":
        frames_cls = "c-muted"

    nodes_st = nodes.get("data_status") if nodes else None
    if nodes and nodes.get("value") is not None:
        nodes_val, nodes_cls = str(nodes.get("value")), "c-green"
    elif nodes_st == "FAILED":
        nodes_val, nodes_cls = "FAILED", "c-muted"
    else:
        nodes_val, nodes_cls = "MISSING", "c-muted"

    if burned and burned.get("value") is not None:
        bme_val, bme_cls = "VALID", "c-green"
    else:
        bme_val, bme_cls = "NOT LIVE YET", "c-muted"

    ratio_val = "NOT LIVE YET"
    ratio_cls = "c-muted"
    if burn_ratio and burn_ratio.get("value") is not None:
        ratio_val = str(burn_ratio.get("value"))
        ratio_cls = "c-green"

    lines = (
        mline(ICON_GRID, "Network usage", "Foundation dashboard snapshot", frames_val, frames_cls)
        + mline(ICON_NODES, "Network scale", "Nodes since inception", nodes_val, nodes_cls)
        + mline(ICON_DROP, "BME / burn model", "Real token-economic mechanism; historically not a timing signal", bme_val, bme_cls)
        + mline(ICON_RATIO, "Burn / emission ratio", "Should become the real token-economics health metric", ratio_val, ratio_cls)
        + mline(ICON_WRENCH, "Dispersed / development", "Roadmap remains relevant to future compute demand", "ACTIVE", "c-green")
    )
    return (
        '<div class="band band-health">'
        '<h4>Project health</h4>'
        '<div class="band-status c-green">Credible / improving</div>'
        + lines
        + '</div>'
    )


def timing_band(
    symbol: str,
    metrics: list[dict],
    price_display: str,
    ath_display: str,
    dd_pct: str,
    band_status: str | None = None,
) -> str:
    sym = symbol.upper()
    sym_lower = symbol.lower()
    by_id = {m.get("metric_id"): m for m in metrics}

    def rs_val(key: str, fallback: str) -> tuple[str, str]:
        m = by_id.get(key)
        if m and m.get("value") is not None:
            return str(m.get("value")), ""
        return fallback, "c-muted"

    btc_v, btc_cls = rs_val(f"{sym_lower}_btc", "LIVE SERIES NEEDED")
    sol_v, sol_cls = rs_val(f"{sym_lower}_sol", "LIVE SERIES NEEDED")
    basket_v, basket_cls = rs_val(f"{sym_lower}_ai_basket", "NOT BUILT")
    lev_v, lev_cls = rs_val("oi_funding", "OI / FUNDING MISSING")

    fill_w = "10%"
    if dd_pct and dd_pct.replace("-", "").replace(".", "").isdigit():
        try:
            pct = abs(float(dd_pct.replace("%", "")))
            fill_w = f"{min(95, max(5, int(pct)))}%"
        except ValueError:
            pass

    lines = (
        mline(ICON_CIRCLES, f"{sym} / BTC", "Highest-priority timing ratio", btc_v, btc_cls)
        + mline(ICON_CIRCLES_DIAG, f"{sym} / SOL", "Required for genuine leadership", sol_v, sol_cls)
        + mline(ICON_BAG, f"{sym} / AI basket", "Separates token leadership from sector beta", basket_v, basket_cls)
        + mline(ICON_LEVERAGE, "Spot vs leverage", "Healthy = spot confirms while leverage stays restrained", lev_v, lev_cls)
    )
    status = band_status or "No leadership confirmation"
    status_cls = "c-red"
    if band_status and band_status.upper() == "UNCLASSIFIED":
        status_cls = "c-orange"
    return (
        '<div class="band band-timing">'
        '<h4>Market / timing</h4>'
        f'<div class="band-status {status_cls}">{_e(status)}</div>'
        '<div class="ddbar">'
        f'<div class="ddbar-track"><div class="ddbar-fill" style="width:{fill_w}"></div></div>'
        f'<div class="ddbar-cap"><span>Now {price_display}</span><span>ATH {ath_display} · ~{dd_pct} below</span></div>'
        '</div>'
        + lines
        + '</div>'
    )


def pump_health_band(metrics: list[dict], intel: dict | None = None) -> str:
    by_id = {m.get("metric_id"): m for m in metrics}
    s1 = (intel or {}).get("stage1_evidence") or {}
    plat = s1.get("platform") or {}
    share_hist = plat.get("launchpad_fee_share_history") or {}
    fee_lines = plat.get("fee_revenue_buyback_history") or []

    price = by_id.get("pump_price_usd") or by_id.get("pump_price") or by_id.get("price")
    price_raw = price.get("value") if price else None
    price_val = f"${float(price_raw):.4f}" if price_raw is not None else "—"
    price_cls = "" if price_raw is not None else "c-muted"
    price_tip = evidence_tip_html(
        name="PRICE",
        read=price_val,
        rows=[
            ("Live spot", price_val),
            ("Source field", str((price or {}).get("source") or "live")),
        ],
        note="Current spot price for the Project health panel.",
        source=str((price or {}).get("source") or "market"),
        as_of=(price or {}).get("fetched_at"),
    )

    dex = by_id.get("dex_liquidity_usd")
    if dex and dex.get("value") is not None:
        dex_val, dex_cls = str(dex.get("value")), ""
    else:
        dex_val, dex_cls = "UNKNOWN", "c-muted"
    dex_tip = evidence_tip_html(
        name="DEX LIQUIDITY",
        read=dex_val,
        rows=[
            ("Best pool", dex_val),
            ("Note", str((dex or {}).get("note") or "DexScreener best pool by liquidity")),
        ],
        note="Liquidity in the deepest observed DEX pool — not total venue depth.",
        source=str((dex or {}).get("source") or "dexscreener"),
        as_of=(dex or {}).get("fetched_at"),
    )

    platform = by_id.get("platform_site")
    plat_val = str(platform.get("value")) if platform and platform.get("value") else "UNKNOWN"
    plat_cls = "c-green" if plat_val == "ACTIVE" else "c-muted"
    plat_tip = evidence_tip_html(
        name="PLATFORM",
        read=plat_val,
        rows=[("Site", "pump.fun"), ("Status", plat_val)],
        note="Platform endpoint observed live this run.",
        source="pump.fun",
        as_of=(platform or {}).get("fetched_at"),
    )

    def _metric(metric_id: str, fallback: str = "UNKNOWN") -> tuple[dict | None, str, str]:
        m = by_id.get(metric_id)
        if m and m.get("value") is not None and m.get("data_status") != "MISSING":
            return m, str(m.get("value")), ""
        return m, fallback, "c-muted"

    rev_m, rev_val, rev_cls = _metric("platform_revenue")
    buy_m, buy_val, buy_cls = _metric("buyback_burn")
    share_m, share_val, share_cls = _metric("launchpad_share")

    buy_display = buy_val.replace(" burned", "") if buy_val.endswith(" burned") else buy_val

    rev_tip = evidence_tip_html(
        name="REVENUE",
        read=rev_val,
        rows=[("Weekly", rev_val), ("Detail", str((rev_m or {}).get("note") or "Weekly platform revenue"))],
        note="Platform revenue snapshot — not a timing signal by itself.",
        source=str((rev_m or {}).get("source") or "defillama"),
        as_of=(rev_m or {}).get("fetched_at"),
    )
    buy_tip = evidence_tip_html(
        name="BUYBACK / BURN",
        read=buy_display,
        rows=[("Weekly", buy_val), ("Detail", str((buy_m or {}).get("note") or "Programmatic buyback/burn"))],
        note="Programmatic absorption — does not prove all unlock supply is absorbed.",
        source=str((buy_m or {}).get("source") or "defillama"),
        as_of=(buy_m or {}).get("fetched_at"),
    )
    share_tip = evidence_tip_html(
        name="MARKET SHARE",
        read=share_val,
        rows=[("Live 24h", share_val), ("Scope", "Launchpad fee share — live window")],
        note="Live 24h launchpad share. Dated historical points are in Share history below.",
        source=str((share_m or {}).get("source") or "defillama"),
        as_of=(share_m or {}).get("fetched_at"),
    )

    aug10 = share_hist.get("aug_10_pct")
    if aug10 is not None:
        share_hist_display = f"{aug10:.1f}% AUG 10"
        share_hist_tip = evidence_tip_html(
            name="SHARE HISTORY",
            read=share_hist_display,
            rows=[
                ("ATH Sep", f"{share_hist.get('ath_sep_pct'):.2f}%" if share_hist.get("ath_sep_pct") is not None else "—"),
                ("Jan high", f"{share_hist.get('jan_high_pct'):.2f}%" if share_hist.get("jan_high_pct") is not None else "—"),
                ("June ATL", f"{share_hist.get('june_atl_pct'):.2f}%" if share_hist.get("june_atl_pct") is not None else "—"),
                ("Aug 10", f"{aug10:.2f}%"),
                ("Live 24h", f"{share_val} (row above)"),
                ("Coverage", str(share_hist.get("coverage") or "DefiLlama Launchpad dailyFees")),
            ],
            note=str(
                plat.get("interpretation")
                or "Recovered after Jan low share, then lost share again. Fee share ≠ launches/users."
            ),
            source=str(share_hist.get("source") or "defillama"),
        )
        share_hist_row = mline_tip(
            ICON_RATIO, "Share history", "Dated fee-share points", share_hist_display, share_hist_tip, ""
        )
    else:
        share_hist_row = ""

    if fee_lines:
        fee_rows = []
        for line in fee_lines:
            if ":" in line:
                k, v = line.split(":", 1)
                fee_rows.append((k.strip(), v.strip()))
            else:
                fee_rows.append(("Point", line))
        fee_hist_tip = evidence_tip_html(
            name="FEE HISTORY",
            read="RECOVERED VS ATL",
            rows=fee_rows,
            note="Fees / revenue / buyback windows from Stage-1. Recovered vs June ATL — not a price-timing rule.",
            source="defillama",
        )
        fee_hist_row = mline_tip(
            ICON_BARS, "Fee history", "Rev / buyback windows", "RECOVERED VS ATL", fee_hist_tip, ""
        )
    else:
        fee_hist_row = ""

    lines = (
        mline_tip(ICON_GRID, "Price", "Live spot", price_val, price_tip, price_cls)
        + mline_tip(ICON_WRENCH, "Platform", "pump.fun", plat_val, plat_tip, plat_cls)
        + mline_tip(ICON_BAG, "DEX liquidity", "Best pool", dex_val, dex_tip, dex_cls)
        + mline_tip(ICON_BARS, "Revenue", "Weekly platform", rev_val, rev_tip, rev_cls)
        + mline_tip(ICON_DROP, "Buyback / burn", "Programmatic", buy_display, buy_tip, buy_cls)
        + mline_tip(
            ICON_RATIO,
            "Value capture",
            "~50% net rev → PUMP burn",
            "~50% LOCKED",
            evidence_tip_html(
                name="VALUE CAPTURE",
                read="~50% of parent net revenue → buybacks → burn",
                rows=[
                    ("Share", "~50% of Bonding Curve + PumpSwap + Terminal net revenue"),
                    ("Not", "Not 100% of revenue"),
                    ("Lock", "~29 Apr 2026 through ~Apr 2027; then discretionary"),
                    ("BOOST", "Not a PUMP buyback — launched-token feature only"),
                ],
                note="Pump.fun success creates PUMP demand through this buyback path. Active buybacks ≠ price must rise.",
                source="Pump.fun Apr 2026 announcement + DefiLlama holdersRevenue",
                as_of=(buy_m or {}).get("fetched_at"),
            ),
            "c-green",
        )
        + mline_tip(ICON_RATIO, "Market share", "Launchpad 24h (live)", share_val, share_tip, share_cls)
        + share_hist_row
        + fee_hist_row
    )
    return (
        '<div class="band band-health">'
        "<h4>Project health</h4>"
        '<div class="band-status c-green">Platform operational</div>'
        + lines
        + "</div>"
    )


def pump_timing_band(
    intel: dict,
    metrics: list[dict],
    price_display: str,
    ath_display: str | None,
    dd_pct: str | None,
) -> str:
    sd = (intel.get("forensics") or {}).get("split_display") or {}
    rs = intel.get("relative_strength") or {}
    rs_btc = rs.get("pump_btc") or {}
    rs_sol = rs.get("pump_sol") or {}
    s1 = intel.get("stage1_evidence") or {}
    funding = s1.get("funding") or {}

    btc_v = sd.get("pump_btc", "UNKNOWN")
    sol_v = sd.get("pump_sol", "UNKNOWN")
    lev_v = sd.get("fut_spot", "UNKNOWN")
    lev_note = sd.get("oi_funding", "")
    buyer_v = sd.get("buyer_evidence", "INCONCLUSIVE")

    def _rs_read(pair: dict, fallback: str) -> str:
        c7 = pair.get("change_7d_pct")
        if c7 is None:
            return "UNKNOWN" if fallback == "UNKNOWN" else "WIRED"
        try:
            return f"LEADING {float(c7):+.0f}%"
        except (TypeError, ValueError):
            return "WIRED"

    btc_display = _rs_read(rs_btc, btc_v)
    sol_display = _rs_read(rs_sol, sol_v)
    rs_cls = "" if btc_v != "UNKNOWN" else "c-muted"
    buyer_cls = "c-orange" if buyer_v in ("INCONCLUSIVE", "MIXED") else ""

    btc_tip = evidence_tip_html(
        name="PUMP / BTC",
        read=btc_display,
        rows=[
            ("7d", f"{rs_btc.get('change_7d_pct'):+.1f}%" if rs_btc.get("change_7d_pct") is not None else "—"),
            ("30d", f"{rs_btc.get('change_30d_pct'):+.1f}%" if rs_btc.get("change_30d_pct") is not None else "—"),
            ("90d", f"{rs_btc.get('change_90d_pct'):+.1f}%" if rs_btc.get("change_90d_pct") is not None else "—"),
        ],
        note="Relative strength versus Bitcoin. Leading on recent windows does not alone classify posture.",
        source=str(rs_btc.get("source") or "binance-daily"),
        as_of=rs_btc.get("fetched_at"),
    )
    sol_tip = evidence_tip_html(
        name="PUMP / SOL",
        read=sol_display,
        rows=[
            ("7d", f"{rs_sol.get('change_7d_pct'):+.1f}%" if rs_sol.get("change_7d_pct") is not None else "—"),
            ("30d", f"{rs_sol.get('change_30d_pct'):+.1f}%" if rs_sol.get("change_30d_pct") is not None else "—"),
            ("90d", f"{rs_sol.get('change_90d_pct'):+.1f}%" if rs_sol.get("change_90d_pct") is not None else "—"),
        ],
        note="Relative strength versus Solana.",
        source=str(rs_sol.get("source") or "binance-daily"),
        as_of=rs_sol.get("fetched_at"),
    )

    lev_display = "ELEVATED VS SPOT" if lev_v and lev_v != "UNKNOWN" else "UNKNOWN"
    if isinstance(lev_v, str) and "×" in lev_v and lev_v != "UNKNOWN":
        ratio_bit = lev_v.split()[0]
        if len(ratio_bit) <= 8:
            lev_display = f"{ratio_bit} VS SPOT"
    amd = intel.get("amendment") or {}
    tape = amd.get("tape") or {}
    if tape.get("read") == "PERPS LEAD":
        fut_q = tape.get("futures_quote_24h_usd") or 0
        spot_q = tape.get("spot_quote_24h_usd") or 0
        lev_display = f"{tape.get('perp_spot', 0):.1f}× PERPS LEAD"
        lev_v = f"futures ${fut_q/1e6:.0f}M / spot ${spot_q/1e6:.0f}M"
        lev_note = "FUNDING CALM · PERPS LEAD — do not say spot leads"
    lev_tip = evidence_tip_html(
        name="SPOT VS LEVERAGE",
        read=lev_display,
        rows=[
            ("Futures / spot", str(lev_v)),
            ("OI / funding", lev_note or "—"),
            ("Caveat", "Elevated vs spot only — historical threshold unvalidated"),
        ],
        note="Futures activity versus spot. Funding and leverage are separate. No fixed heavy-leverage threshold yet.",
        source="binance",
    )

    pct = funding.get("percentile_vs_binance_history")
    latest = funding.get("latest_rate_8h")
    hist_n = funding.get("history_n")
    if pct is not None and float(pct) < 25:
        fund_display = "LOW VS HISTORY"
    elif pct is not None and float(pct) > 75:
        fund_display = "HIGH VS HISTORY"
    elif pct is not None:
        fund_display = "MID VS HISTORY"
    else:
        fund_display = "UNKNOWN"
    fund_cls = "c-green" if fund_display == "LOW VS HISTORY" else ("c-orange" if fund_display != "UNKNOWN" else "c-muted")
    fund_tip = evidence_tip_html(
        name="BINANCE FUNDING",
        read=fund_display,
        rows=[
            ("Latest", f"{latest:.5f} / 8h" if latest is not None else "—"),
            ("History", f"{pct}th percentile" if pct is not None else "—"),
            ("Sample", f"n={hist_n}" if hist_n is not None else "—"),
            ("Coverage", str(funding.get("coverage") or "Binance PUMPUSDT")),
        ],
        note=str(
            funding.get("wording")
            or "Funding is unusually low versus PUMP's own Binance history. This does not mean overall leverage is low."
        ),
        source="Binance",
        as_of=funding.get("latest_time"),
    )

    buyer_detail = ((intel.get("forensics") or {}).get("buyer_forensics") or {}).get("verdict_detail") or ""
    buyer_tip = evidence_tip_html(
        name="BUYER / FLOW QUALITY",
        read=str(buyer_v),
        rows=[
            ("Verdict", str(buyer_v)),
            ("Sample", buyer_detail[:220] if buyer_detail else "Principal-pool SWAP sample"),
        ],
        note="Observed DEX net buying in the retrieval span. Buyer identity remains incomplete. CEX buyers unobservable.",
        source="wallet-forensics",
        as_of=((intel.get("forensics") or {}).get("buyer_forensics") or {}).get("gathered_at"),
    )

    triad_mt = intel.get("triad", {}).get("market_timing", {})
    status = triad_mt.get("display", "UNCLASSIFIED")

    ath_ok = bool(ath_display) and ath_display not in ("$13.53", "—", "")
    ddbar = ""
    if ath_ok and dd_pct:
        fill_w = "10%"
        try:
            pct_dd = abs(float(str(dd_pct).replace("%", "")))
            fill_w = f"{min(95, max(5, int(pct_dd)))}%"
        except ValueError:
            pass
        ddbar = (
            '<div class="ddbar">'
            f'<div class="ddbar-track"><div class="ddbar-fill" style="width:{fill_w}"></div></div>'
            f'<div class="ddbar-cap"><span>Now {price_display}</span>'
            f"<span>ATH {ath_display} · ~{dd_pct} below</span></div>"
            "</div>"
        )

    fund_row = (
        mline_tip(ICON_LEV_DOWN, "Binance funding", "Vs own Binance history only", fund_display, fund_tip, fund_cls)
        if pct is not None or funding.get("display")
        else ""
    )

    lines = (
        mline_tip(ICON_CIRCLES, "PUMP / BTC", "Relative strength", btc_display, btc_tip, rs_cls)
        + mline_tip(ICON_CIRCLES_DIAG, "PUMP / SOL", "Relative strength", sol_display, sol_tip, rs_cls)
        + mline_tip(ICON_LEVERAGE, "Spot vs leverage", lev_note or "Futures vs spot", lev_display, lev_tip, "")
        + fund_row
        + mline_tip(ICON_BARS, "Buyer / flow quality", "Principal-pool SWAP sample", str(buyer_v), buyer_tip, buyer_cls)
        + mline_tip(
            ICON_WARN,
            "Course-change / get-out",
            "Separate from tokenomics",
            "Daily close < $0.00215",
            evidence_tip_html(
                name="GET-OUT",
                read="Daily close below $0.00215",
                rows=[
                    ("Level", "$0.00215 daily close"),
                    ("Role", "Market-risk invalidation — not a fundamental tokenomics fail"),
                ],
                note="This remains the course-change / get-out. Independent of buyback policy.",
                source="locked V3 market-risk level",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-timing">'
        "<h4>Market / timing</h4>"
        f'<div class="band-status c-orange">{_e(status)}</div>'
        + ddbar
        + lines
        + "</div>"
    )



def _stack_flags_html(ws: dict, intel: dict | None) -> str:
    cats = ws.get("categories", [])
    dot_map = {"ACTIVE": "dot-red", "PARTIAL": "dot-orange", "CLEAR": "dot-green", "UNKNOWN": "dot-grey"}
    state_read = {"ACTIVE": "CONCERNING", "PARTIAL": "PARTIAL", "CLEAR": "CLEAR", "UNKNOWN": "UNKNOWN"}
    flags = ""
    for c in cats:
        dot = dot_map.get(c.get("state", "UNKNOWN"), "dot-grey")
        label = c.get("label") or c.get("title", "")
        detail = (c.get("detail") or "").strip()
        summary = (c.get("summary") or "").strip()
        if not summary:
            summary = detail[:55].rstrip(" .;") if detail else "—"
        tip = evidence_tip_html(
            name=label,
            read=state_read.get(c.get("state", "UNKNOWN"), c.get("state", "UNKNOWN")),
            rows=[("Evidence", detail[:280])] if detail else [],
            note="Full category read. Visible line is the short scan only.",
            source=_stage1_source_label(ws.get("source"), intel),
        )
        flags += (
            f'<div class="flag has-tip">'
            f'<div class="metric-tip-template" hidden>{tip}</div>'
            f'<div class="flag-head"><span class="dot {dot}"></span>'
            f'<strong class="flag-title">{_e(label)}{TIP_MARK}</strong></div>'
            f'<span class="flag-detail">{_e(summary)}</span></div>'
        )
    return flags


def warning_stack_html(intel: dict | None = None) -> str:
    """Same meter graphic for all assets. Title only changes for risk_confirmation."""
    ws = (intel or {}).get("warning_stack", {})
    cats = ws.get("categories", [])
    flags = _stack_flags_html(ws, intel)
    if ws.get("schema") == "risk_confirmation":
        title = ws.get("section_title") or "RISK & CONFIRMATION"
        active = int(ws.get("n_concerns") or 0)
    else:
        title = "Warning stack"
        active = concerning_meter(cats)
    total = ws.get("meter_total", len(cats)) or len(cats) or 6
    meter_on = min(active, total)
    meter = "".join(f'<span class="{"on" if i < meter_on else ""}"></span>' for i in range(total))
    return (
        '<section class="sec"><div class="sec-head">'
        f"<h3>{_e(title)}</h3>"
        "</div><div class=\"stackrow\"><div>"
        f'<div class="stack-num">{active}<span class="of">/{total}</span></div>'
        f'<div class="meter">{meter}</div>'
        '<div class="stack-den">categories currently concerning from the data we actually have</div>'
        '</div><div class="flags">' + flags + "</div></div></section>"
    )


def warning_stack_pump(intel: dict | None = None) -> str:
    return warning_stack_html(intel)


def warning_stack_render(intel: dict, rs_btc: dict | None = None, ath_pct: float | None = None) -> str:
    return warning_stack_html(intel)


def knowledge_census_render(intel: dict, slug: str = "render") -> str:
    if slug == "pump" and (intel or {}).get("reality_check"):
        return reality_check_section(intel)

    k = intel.get("knowledge_census", {})
    known = k.get("known", [])
    inferred = k.get("inferred", [])
    unknown = k.get("unknown", [])

    def col(count: int, title: str, cls: str, items: list[str]) -> str:
        lis = "".join(f"<li>{_e(x)}</li>" for x in items)
        return (
            f'<div class="col"><div class="count {cls}">{count}</div>'
            f'<h4 class="{cls}">{_e(title)}</h4><ul>{lis}</ul></div>'
        )

    # Route D prototype fallbacks when sparse (RENDER only — PUMP should always have census from forensics)
    if slug == "render":
        if not known:
            known = [
                "Project fundamentals did not time the 2024 top.",
                "RENDER relative strength was materially more useful.",
                "Network health remained credible after price collapsed.",
            ]
        if not inferred:
            inferred = [
                "RS + spot confirmation + restrained leverage is the healthiest leadership stack.",
                "Project health should validate exposure, not dictate entry timing.",
            ]
        if not unknown:
            unknown = [
                "Current labelled GSR / treasury / CEX flows.",
                "Current OI / funding percentile and spot-perp split.",
                "Current 30d RENDER/BTC, RENDER/SOL and AI-basket RS.",
            ]

    return (
        '<section class="sec"><div class="sec-head">'
        '<h3>Knowledge census</h3>'
        '</div><div class="three">'
        + col(len(known), "Known", "c-green", known)
        + col(len(inferred), "Strongly inferred", "c-orange", inferred)
        + col(len(unknown), "Unknown / not live", "c-muted", unknown)
        + '</div></section>'
    )


def _rc_item_html(item: dict, *, col: str, intel: dict | None = None) -> str:
    title = item.get("title") or ""
    summary = item.get("summary") or ""
    priority = (item.get("priority") or "").upper()
    rows = item.get("evidence_rows") or []
    tip_rows = [(r.get("key"), r.get("value")) for r in rows if isinstance(r, dict)]
    src = _stage1_source_label(item.get("source"), intel)
    tip = evidence_tip_html(
        name=title,
        read=item.get("interpretation") or summary,
        rows=tip_rows[:5],
        note=item.get("interpretation") or summary,
        source=src,
        as_of=item.get("as_of"),
        source_url=item.get("source_url"),
        confidence=item.get("confidence"),
        freshness=item.get("freshness"),
    )
    # Avoid duplicating interpretation as both read + note when rows exist
    if tip_rows:
        tip = evidence_tip_html(
            name=title,
            read=summary[:80],
            rows=tip_rows[:5],
            note=item.get("interpretation") or "",
            source=src,
            as_of=item.get("as_of"),
            source_url=item.get("source_url"),
            confidence=item.get("confidence"),
            freshness=item.get("freshness"),
        )
    tag = ""
    if priority == "HIGH":
        tag = '<span class="rc-tag high">High</span>'
    elif priority == "MEDIUM":
        tag = '<span class="rc-tag med">Medium</span>'
    else:
        tag = '<span class="rc-info" aria-hidden="true">i</span>'
    return (
        f'<div class="rc-item has-tip">'
        f'<div class="metric-tip-template" hidden>{tip}</div>'
        f'<div class="rc-item-top">'
        f'<span class="rc-dot"></span>'
        f'<div class="rc-item-title">{_e(title)}</div>'
        f"{tag}"
        f"</div>"
        f'<div class="rc-item-line">{_e(summary)}</div>'
        f"</div>"
    )


def reality_check_section(intel: dict | None = None) -> str:
    """Approved mockup layout — REALITY CHECK with FINAL wording override."""
    rc = (intel or {}).get("reality_check") or {}
    known = rc.get("known") or []
    suggests = rc.get("suggests") or []
    unknowns = rc.get("unknowns") or []
    headline = rc.get("priority_headline") or (
        "Who is actually driving this rally — and who is distributing into it?"
    )

    known_html = "".join(_rc_item_html(x, col="known", intel=intel) for x in known)
    sug_html = "".join(_rc_item_html(x, col="suggests", intel=intel) for x in suggests)
    unk_html = "".join(_rc_item_html(x, col="unknowns", intel=intel) for x in unknowns)

    return (
        '<section class="sec rc-sec">'
        '<h3 class="rc-title">Reality check</h3>'
        '<div class="rc-grid">'
        '<section class="rc-col known">'
        '<div class="rc-col-head"><div class="rc-col-title">Known</div></div>'
        f"{known_html}</section>"
        '<section class="rc-col suggests">'
        '<div class="rc-col-head"><div class="rc-col-title">What it suggests</div></div>'
        f"{sug_html}</section>"
        '<section class="rc-col unknowns">'
        '<div class="rc-col-head"><div class="rc-col-title">Unknowns</div></div>'
        f"{unk_html}</section>"
        "</div></section>"
    )
