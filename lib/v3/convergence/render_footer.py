"""Variant A convergence footer HTML — state primary, evidence secondary."""

from __future__ import annotations

import html
from typing import Any

from lib.v3.convergence.engine import DIM_FUNDAMENTALS_SUPPLY

CSS_MARKER = "/* --- Variant A Stack: convergence footer (Report 02 integration) --- */"

CONVERGENCE_CSS = f"""{CSS_MARKER}
.cv-convergence {{ background: var(--surface-strong); border-radius: 12px; padding: 1.15rem 1.25rem 1.05rem; box-shadow: var(--shadow); margin-top: 1.25rem; }}
.cv-head {{ margin-bottom: 0.65rem; }}
.cv-head--pos .cv-title {{ color: var(--green); }}
.cv-head--neg .cv-title {{ color: var(--red); }}
.cv-head--div .cv-title {{ color: var(--orange); }}
.cv-head--mix .cv-title, .cv-head--ins .cv-title {{ color: var(--muted); }}
.cv-head--ins {{ border-left: 3px solid var(--orange); padding-left: 0.65rem; }}
.cv-title {{ font-family: var(--display); font-size: 1.2rem; font-weight: 700; line-height: 1.15; margin: 0.2rem 0 0; }}
.cv-rows {{ border-top: 1px solid var(--faint); border-bottom: 1px solid var(--faint); }}
.cv-row {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 0.48rem 0; border-bottom: 1px solid var(--faint); font-size: 0.84rem; }}
.cv-row:last-child {{ border-bottom: 0; }}
.cv-dim {{ color: var(--muted); font-weight: 600; font-size: 0.72rem; flex: 0 0 auto; }}
.cv-state {{ font-weight: 600; text-align: right; flex: 1; display: inline-flex; align-items: center; justify-content: flex-end; gap: 0.35rem; flex-wrap: wrap; }}
.cv-ev {{ display: inline-block; width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }}
.cv-ev--complete {{ background: var(--muted); opacity: 0.85; }}
.cv-ev--partial {{ background: transparent; border: 2px solid var(--muted); opacity: 0.65; }}
.cv-ev--insufficient {{ background: transparent; border: 1px dashed var(--muted); opacity: 0.45; }}
.cv-ev-tag {{ font-size: 0.56rem; font-weight: 700; letter-spacing: 0.08em; color: var(--muted); }}
.cv-syn {{ margin-top: 0.8rem; }}
.cv-syn-row {{ display: grid; grid-template-columns: 8.5rem 1fr; gap: 0.55rem; padding: 0.28rem 0; font-size: 0.8rem; }}
.cv-syn-k {{ color: var(--muted); font-weight: 600; }}
.cv-syn-v {{ color: var(--ink); }}
.cv-syn-row--next {{ margin-top: 0.35rem; padding-top: 0.55rem; border-top: 1px dashed var(--faint); }}
@media (max-width: 560px) {{ .cv-syn-row {{ grid-template-columns: 1fr; gap: 0.15rem; }} }}
"""

_HEAD_CLASS = {
    ("ALIGNED", "POSITIVE"): "cv-head--pos",
    ("ALIGNED", "NEGATIVE"): "cv-head--neg",
    "DIVERGING": "cv-head--div",
    "MIXED": "cv-head--mix",
    "INSUFFICIENT": "cv-head--ins",
}

_EV_CLASS = {
    "COMPLETE": "cv-ev--complete",
    "PARTIAL": "cv-ev--partial",
    "INSUFFICIENT": "cv-ev--insufficient",
}


def _head_modifier(payload: dict[str, Any]) -> str:
    conv = payload.get("convergence") or "INSUFFICIENT"
    direction = payload.get("aligned_direction")
    if conv == "ALIGNED" and direction:
        return _HEAD_CLASS.get(("ALIGNED", direction), "cv-head--ins")
    return _HEAD_CLASS.get(conv, "cv-head--ins")


def _row_html(row: dict[str, str]) -> str:
    dim = html.escape(row.get("dimension") or "")
    state = html.escape(row.get("state") or "UNKNOWN")
    ev = (row.get("evidence_status") or "INSUFFICIENT").upper()
    ev_cls = _EV_CLASS.get(ev, "cv-ev--insufficient")
    tag = ""
    if ev in ("PARTIAL", "INSUFFICIENT"):
        tag = f'<span class="cv-ev-tag">{html.escape(ev)}</span>'
    return (
        f'<div class="cv-row"><span class="cv-dim">{dim}</span>'
        f'<span class="cv-state">{state}'
        f'<span class="cv-ev {ev_cls}" aria-hidden="true"></span>{tag}</span></div>'
    )


def render_footer(payload: dict[str, Any]) -> str:
    """Render one asset footer from map_asset / convergence.json asset entry."""
    if not payload or not payload.get("rows"):
        return ""

    headline = html.escape(payload.get("headline") or "CONVERGENCE: INSUFFICIENT")
    head_mod = _head_modifier(payload)
    rows = "".join(_row_html(r) for r in payload["rows"])
    syn = payload.get("synthesis") or {}
    next_label = html.escape(payload.get("next_label") or "Next evidence priority")

    def _syn(key: str) -> str:
        return html.escape(syn.get(key) or "—")

    return (
        '<section class="cv-convergence" aria-label="Evidence convergence" '
        'data-convergence-source="autojob01-v1">'
        f'<header class="cv-head {head_mod}">'
        '<span class="label">Evidence convergence</span>'
        f'<h3 class="cv-title">{headline}</h3>'
        "</header>"
        f'<div class="cv-rows">{rows}</div>'
        '<div class="cv-syn">'
        f'<div class="cv-syn-row"><span class="cv-syn-k">What aligns</span>'
        f'<span class="cv-syn-v">{_syn("aligns")}</span></div>'
        f'<div class="cv-syn-row"><span class="cv-syn-k">What conflicts</span>'
        f'<span class="cv-syn-v">{_syn("conflicts")}</span></div>'
        f'<div class="cv-syn-row"><span class="cv-syn-k">What\'s missing</span>'
        f'<span class="cv-syn-v">{_syn("missing")}</span></div>'
        f'<div class="cv-syn-row cv-syn-row--next"><span class="cv-syn-k">{next_label}</span>'
        f'<span class="cv-syn-v">{_syn("next_priority")}</span></div>'
        "</div></section>"
    )


def ensure_convergence_css(html_doc: str) -> str:
    if CSS_MARKER in html_doc:
        return html_doc
    return html_doc.replace("</style>", CONVERGENCE_CSS + "\n</style>", 1)


def validate_asset_payload(payload: dict[str, Any]) -> list[str]:
    """Return validation errors — empty list means OK."""
    errs: list[str] = []
    rows = payload.get("rows") or []
    if len(rows) != 5:
        errs.append(f"expected 5 rows, got {len(rows)}")
    dims = [r.get("dimension") for r in rows]
    expected = [
        "Price + RS",
        "Spot / Capital",
        "Whales / Players",
        "Attention",
        DIM_FUNDAMENTALS_SUPPLY,
    ]
    if dims != expected:
        errs.append(f"dimension order/names mismatch: {dims}")
    for banned in ("weak_count", "directional_votes", "confidence"):
        if banned in payload:
            errs.append(f"forbidden key in payload: {banned}")
    return errs
