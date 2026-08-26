"""Keep approved PUMP 8-cell hero minidash after weekly clone-from-report-01."""

from __future__ import annotations

import copy
import re
from typing import Any

from lib.v3.current_stance import pump_current_stance, stance_hero_block_html
from lib.v3.autojob01.apply_job2_integrity import enrich_pump_buyback_daily
from lib.v3.pump_amendment_evidence import load_amendment_evidence
from lib.v3.pump_minidash import PUMP_MINIDASH_CSS, render_pump_minidash

CSS_MARKER = "/* pump-hero-minidash-v1 */"
CSS_END = "/* pump-hero-minidash-v1 end */"
ARTICLE_RE = re.compile(
    r'(<article\b(?=[^>]*\bdata-asset="pump")[^>]*>)(.*?)(</article>)',
    re.S,
)


def _div_span(html: str, start: int) -> tuple[int, int]:
    if not html.startswith("<div", start):
        raise ValueError("not a div")
    depth = 0
    j = start
    n = len(html)
    while j < n:
        if html.startswith("<div", j):
            depth += 1
            j += 4
        elif html.startswith("</div>", j):
            depth -= 1
            j += 6
            if depth == 0:
                return start, j
        else:
            j += 1
    raise ValueError("unclosed div")


def inject_pump_css(html: str) -> str:
    block = PUMP_MINIDASH_CSS.strip() + f"\n{CSS_END}\n"
    if CSS_MARKER in html:
        return re.sub(
            rf"{re.escape(CSS_MARKER)}.*?(?={re.escape(CSS_END)}|{re.escape('</style>')})",
            block.rstrip() + "\n",
            html,
            count=1,
            flags=re.S,
        )
    return html.replace("</style>", block + "</style>", 1)


def overlay_amendment_from_bundle(bundle: dict[str, Any] | None) -> dict[str, Any]:
    amd = copy.deepcopy(load_amendment_evidence() or {})
    amd = enrich_pump_buyback_daily(amd, bundle)
    bundle = bundle or {}
    feeds = bundle.get("feeds") or {}
    prices = (bundle.get("prices") or {}).get("assets") or {}
    prow = prices.get("PUMP") or {}
    cg = ((feeds.get("cg_by_id") or {}).get("pump-fun") or {})
    circ = prow.get("circulating_supply")
    if not isinstance(circ, (int, float)):
        circ = cg.get("circ")
    if isinstance(circ, (int, float)) and circ > 0:
        amd["supply"] = {
            "circ_pct": circ / 1e12 * 100,
            "circ_sub": f"{circ / 1e9:.0f}B / 1T",
        }
    return amd


def apply_pump_hero(html: str, bundle: dict[str, Any] | None = None, log: list[str] | None = None) -> str:
    log = log if log is not None else []
    m = ARTICLE_RE.search(html)
    if not m:
        log.append("APPLY_MISS PUMP.hero_article")
        return html
    body = m.group(2)
    amd = overlay_amendment_from_bundle(bundle)
    dash = render_pump_minidash(amd)
    dash_i = body.find('<div class="econ-dash')
    if dash_i < 0:
        log.append("APPLY_MISS PUMP.hero_dash")
        return html
    ds, de = _div_span(body, dash_i)
    body = body[:ds] + dash + body[de:]
    stance_i = body.find('<div class="alt-stance">')
    if stance_i < 0:
        log.append("APPLY_MISS PUMP.hero_stance")
        return html
    ss, se = _div_span(body, stance_i)
    stance_html = stance_hero_block_html(pump_current_stance(), clamp_lines=True)
    body = body[:ss] + stance_html + body[se:]
    html = html[: m.start()] + m.group(1) + body + m.group(3) + html[m.end() :]
    html = inject_pump_css(html)
    missing = pump_hero_gaps(html)
    if missing:
        log.append("APPLY_MISS PUMP.hero_minidash " + ",".join(missing))
    else:
        log.append("APPLY_OK PUMP.hero_minidash")
    return html


def pump_hero_gaps(html: str) -> list[str]:
    """Required PUMP 8-cell hero. Missing any of these is a ship-blocker."""
    m = ARTICLE_RE.search(html)
    if not m:
        return ["pump_article"]
    art = m.group(0)
    dash_i = art.find('econ-dash pump-dash')
    dash = art[dash_i : dash_i + 8000] if dash_i >= 0 else ""
    need = {
        "css": CSS_MARKER in html,
        "pump_dash": "pump-dash" in art,
        "buyback_bars": "econ-bars" in art,
        "est_pump_bought": "Est. PUMP" in art,
        "value_capture_50": "~50%" in art and "LOCKED APR27" in art,
        "stance_clamp": "alt-stance-expl-text" in art,
        "no_73_in_dash": "73%" not in dash,
    }
    return [k for k, ok in need.items() if not ok]


def require_pump_hero(html: str) -> None:
    gaps = pump_hero_gaps(html)
    if gaps:
        raise RuntimeError("PUMP hero minidash missing after apply: " + ",".join(gaps))
