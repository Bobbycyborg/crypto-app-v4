"""Patch visible metric cards AND hidden tooltip templates in one pass."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable

from lib.v3.market_top_v3 import _etf_amt_html, _etf_amt_class, _fmt_etf_tip

_PROTO_PORT_OPEN = r'<div class="metric-card has-tip[^"]*proto-port[^"]*">'


def _norm_num(s: str) -> str | None:
    if not s:
        return None
    t = re.sub(r"[^0-9.]", "", s.replace(",", ""))
    if not t or t == ".":
        return None
    try:
        v = float(t)
        if abs(v - round(v)) < 0.05:
            return str(int(round(v)))
        return f"{v:.3f}".rstrip("0").rstrip(".")
    except ValueError:
        return None


def _card_pat(extra_class: str) -> str:
    cls = re.escape(extra_class)
    return (
        rf'(<div class="metric-card has-tip(?:\s+{cls})+[^"]*"[^>]*>)'
        rf'(.*?)(</div>\s*(?:<div class="metric-card has-tip|<div class="metric-row|<div class="mkt-lead|<section class="holdings))'
    )


def _patch_in_card(
    card_html: str,
    *,
    visible_pat: str,
    visible_repl: str,
    tip_patches: list[tuple[str, str]] | None = None,
    tip_read: str | None = None,
) -> str:
    out, n = re.subn(visible_pat, visible_repl, card_html, count=1, flags=re.S)
    if visible_pat != "DOES_NOT_MATCH" and n != 1:
        return card_html
    if tip_read is not None:
        out, n2 = re.subn(
            r'(<div class="ev-tip-read">)([^<]*)(</div>)',
            rf"\g<1>{tip_read}\g<3>",
            out,
            count=1,
        )
        if n2 != 1:
            return card_html
    for label, new_val in tip_patches or []:
        pat = (
            rf'(<span class="ev-k">{re.escape(label)}</span>\s*<span class="ev-v[^"]*">)'
            rf'([^<]*)(</span>)'
        )
        out, n3 = re.subn(pat, rf"\g<1>{new_val}\g<3>", out, count=1)
        if n3 != 1:
            return card_html
    return out


def _map_card(html: str, extra_class: str, fn: Callable[[str], str]) -> str:
    pat = _card_pat(extra_class)
    m = re.search(pat, html, flags=re.S)
    if not m:
        return html
    new_body = fn(m.group(2))
    if new_body == m.group(2):
        return html
    return html[: m.start()] + m.group(1) + new_body + m.group(3) + html[m.end() :]


def _fmt_lev_shown(ratio: float) -> str:
    return (
        f"{ratio:.0f}"
        if abs(ratio - round(ratio)) < 0.5
        else f"{ratio:.1f}".rstrip("0").rstrip(".")
    )


def _fg_color(val: int) -> tuple[str, str]:
    if val <= 25:
        return "var(--red)", "c-red"
    if val <= 45:
        return "var(--orange)", "c-orange"
    if val <= 55:
        return "var(--muted)", "c-muted"
    if val <= 75:
        return "var(--orange)", "c-orange"
    return "var(--green)", "c-green"


def _fg_tip_visual_html(trend: list[dict[str, Any]], val: int) -> str:
    rows = list(reversed((trend or [])[:7]))
    if not rows:
        rows = [{"value": val}]
    bars: list[str] = []
    days: list[str] = []
    for i, row in enumerate(rows):
        v = int(row.get("value") or 0)
        is_now = i == len(rows) - 1
        _, cls = _fg_color(v)
        bar_cls = f"fg-tip-bar {cls}" + (" is-now" if is_now else "")
        bars.append(f'<div class="{bar_cls}" style="height:{max(14, min(100, v))}%"></div>')
        day_cls = "fg-tip-day is-now" if is_now else "fg-tip-day"
        days.append(f'<div class="{day_cls}">{v}</div>')
    return (
        '<div class="ev-tip-visual">'
        '<div class="fg-tip-scale-wrap">'
        '<div class="fg-tip-scale"></div>'
        f'<div class="fg-tip-needle" style="left:{val}%"></div></div>'
        '<div class="fg-tip-scale-labels"><span>Extreme fear</span><span>Extreme greed</span></div>'
        f'<div class="fg-tip-bars">{"".join(bars)}</div>'
        f'<div class="fg-tip-days">{"".join(days)}</div>'
        "</div>"
    )


def patch_portfolio_dual(html: str, total_print: str, log: list[str], touches: list | None = None) -> str:
    field = "MARKET.portfolio_value"
    html2, n = re.subn(
        rf'({_PROTO_PORT_OPEN}.*?<div class="metric-value">)\$[0-9,]+',
        rf"\g<1>{total_print}",
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        log.append(f"APPLY_MISS {field} n=0")
        return html
    html3, n2 = re.subn(
        rf'({_PROTO_PORT_OPEN}.*?<div class="ev-tip-read">)\$[0-9,]+',
        rf"\g<1>{total_print}",
        html2,
        count=1,
        flags=re.S,
    )
    if n2 != 1:
        log.append(f"APPLY_MISS {field}.tip n=0")
        return html
    log.append(f"APPLY_OK {field}")
    if touches is not None:
        touches.append(
            {"asset": "MARKET", "section": "market_top", "needle": total_print, "field": field}
        )
    return html3


def patch_fear_greed_dual(html: str, fg: dict[str, Any], log: list[str]) -> str:
    field = "MARKET.fear_greed"
    cur = fg.get("current") or {}
    val = cur.get("value")
    if val is None and isinstance(fg.get("recent_trend"), list) and fg["recent_trend"]:
        val = fg["recent_trend"][0].get("value")
    if val is None and isinstance(fg.get("trend"), list) and fg["trend"]:
        val = fg["trend"][0].get("value")
    if val is None:
        log.append(f"APPLY_MISS {field} n=0")
        return html
    val_i = int(val)
    word = (cur.get("classification") or cur.get("value_classification") or "—").title()
    stroke, _ = _fg_color(val_i)
    ts = cur.get("timestamp")
    as_of = ""
    if ts:
        try:
            as_of = datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
        except (TypeError, ValueError, OSError):
            as_of = str(ts)
    stale = fg.get("freshness") == "STALE" or fg.get("cache_fallback")
    fresh_lbl = "STALE" if stale else "FRESH"
    delta = fg.get("delta_vs_prior")
    delta_s = f"{delta:+d}" if isinstance(delta, int) else ("+0" if delta == 0 else str(delta or "+0"))

    html2, n = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<span class="fg-dial-num"[^>]*>)\d+',
        rf"\g<1>{val_i}",
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        log.append(f"APPLY_MISS {field} n=0")
        return html
    html2, n2 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<path class="fg-dial-fill"[^>]*stroke-dasharray=")\d+',
        rf"\g<1>{val_i}",
        html2,
        count=1,
        flags=re.S,
    )
    if n2 != 1:
        log.append(f"APPLY_MISS {field}.dash n=0")
        return html
    html2, n3 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<path class="fg-dial-fill"[^>]*stroke=")[^"]+',
        rf'\g<1>{stroke}',
        html2,
        count=1,
        flags=re.S,
    )
    html2, n4 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<span class="fg-dial-num"[^>]*style="color:)[^"]+',
        rf'\g<1>{stroke}',
        html2,
        count=1,
        flags=re.S,
    )
    html2, n5 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<div class="fg-mood">)[^<]+',
        rf"\g<1>{word}",
        html2,
        count=1,
        flags=re.S,
    )
    html2, n6 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<div class="ev-tip-read">)[^<]+',
        rf"\g<1>{word.upper()}",
        html2,
        count=1,
        flags=re.S,
    )
    if min(n2, n3, n4, n5, n6) != 1:
        log.append(f"APPLY_MISS {field}.tip n=0")
        return html
    trend = fg.get("recent_trend") or fg.get("trend") or []
    visual = _fg_tip_visual_html(trend, val_i)
    html2, nv2 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?)(<div class="ev-tip-visual">.*?</div>)(<div class="ev-tip-rows">)',
        rf"\g<1>{visual}\g<3>",
        html2,
        count=1,
        flags=re.S,
    )
    if nv2 != 1:
        log.append(f"APPLY_MISS {field}.visual n=0")
        return html
    html2, n7 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<span class="ev-k">Index</span>\s*<span class="ev-v">)[^<]+',
        rf"\g<1>{val_i}",
        html2,
        count=1,
        flags=re.S,
    )
    html2, n8 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<span class="ev-k">Δ prior</span>\s*<span class="ev-v">)[^<]+',
        rf"\g<1>{delta_s}",
        html2,
        count=1,
        flags=re.S,
    )
    html2, n9 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<span class="ev-k">Freshness</span>\s*<span class="ev-v">)[^<]+',
        rf"\g<1>{fresh_lbl}",
        html2,
        count=1,
        flags=re.S,
    )
    html2, n10 = re.subn(
        r'(<div class="metric-card has-tip fg-card">.*?<span class="ev-k">As of</span>\s*<span class="ev-v">)[^<]+',
        rf"\g<1>{as_of or '—'}",
        html2,
        count=1,
        flags=re.S,
    )
    if min(n7, n8, n9, n10) != 1:
        log.append(f"APPLY_MISS {field}.rows n=0")
        return html
    if as_of:
        html2, _ = re.subn(
            r'(<div class="metric-card has-tip fg-card">.*?<div class="ev-tip-foot">.*?<div>As of · )[^<]+',
            rf"\g<1>{as_of}",
            html2,
            count=1,
            flags=re.S,
        )
    log.append(f"APPLY_OK {field}")
    return html2


def patch_btc_leverage_dual(html: str, ratio: float | None, log: list[str]) -> str:
    field = "MARKET.leverage"
    if not isinstance(ratio, (int, float)):
        log.append(f"APPLY_MISS {field} n=0")
        return html
    shown = _fmt_lev_shown(float(ratio))
    line = f"BTC perps ~{shown}× spot · BTC leverage only"
    tip_ratio = f"{float(ratio):.3f}×"

    def body(b: str) -> str:
        nb, n = re.subn(
            r'(<span class="proto-line">)BTC perps ~[\d.]+× spot · BTC leverage only',
            rf"\g<1>{line}",
            b,
            count=1,
        )
        if n != 1:
            return b
        return _patch_in_card(
            nb,
            visible_pat="DOES_NOT_MATCH",
            visible_repl="",
            tip_patches=[("Ratio", tip_ratio)],
        )

    lev_pat = (
        r'(<div class="metric-card has-tip">(?:(?!metric-card has-tip etf-card).)*?'
        r'<div class="label">BTC LEVERAGE.*?</div>\s*</div>\s*)'
        r'(?=<div class="metric-card has-tip etf-card")'
    )
    m = re.search(lev_pat, html, flags=re.S)
    if not m:
        log.append(f"APPLY_MISS {field} n=0")
        return html
    chunk = m.group(1)
    new_chunk = body(chunk)
    if new_chunk == chunk:
        log.append(f"APPLY_MISS {field} n=0")
        return html
    log.append(f"APPLY_OK {field}")
    return html[: m.start()] + new_chunk + html[m.end() :]


def _etf_tip_val_inner(usd: Any, *, prefer_billions: bool = False) -> str:
    shown = _fmt_etf_tip(usd, prefer_billions=prefer_billions)
    if shown in ("—", "N/A"):
        cls = "c-muted is-dash"
    else:
        cls = _etf_amt_class(usd)
    return f'<span class="ev-v {cls}">{shown}</span>'


def patch_etf_dual(html: str, etf_assets: dict[str, Any], log: list[str], touches: list | None = None) -> str:
    field = "MARKET.etf_amts"
    keys = [
        ("BTC", "flow_7d_usd", "7d"),
        ("BTC", "flow_30d_usd", "30d"),
        ("ETH", "flow_7d_usd", "7d"),
        ("ETH", "flow_30d_usd", "30d"),
        ("SOL", "flow_7d_usd", "7d"),
        ("SOL", "flow_30d_usd", "30d"),
    ]
    as_ofs: list[str] = []

    def body(b: str) -> str:
        face_i = b.find('<div class="etf-a">')
        if face_i < 0:
            return b
        amt_re = re.compile(
            r'<span class="amt [^"]+">\$[^<]*(?:<span class="u[^"]*">[^<]*</span>\s*)*</span>',
            re.S,
        )
        chunk = b[face_i : face_i + 4000]
        found = list(amt_re.finditer(chunk))
        if len(found) != 6:
            return b
        pieces: list[str] = []
        last = 0
        for (sym, key, horizon), m in zip(keys, found):
            row = etf_assets.get(sym) or {}
            usd = row.get(key) if row.get("ok") else None
            if row.get("as_of"):
                as_ofs.append(str(row["as_of"]))
            if not row.get("ok"):
                repl = '<span class="amt c-muted">N/A <span class="u">' + horizon.upper() + '</span></span>'
            else:
                repl = _etf_amt_html(usd, horizon)
            pieces.append(chunk[last : m.start()])
            pieces.append(repl)
            last = m.end()
        pieces.append(chunk[last:])
        nb = b[:face_i] + "".join(pieces) + b[face_i + 4000 :]

        for sym in ("BTC", "ETH", "SOL"):
            row = etf_assets.get(sym) or {}
            if not row.get("ok"):
                continue
            specs = (
                ("1D", row.get("flow_1d_usd"), False),
                ("7D", row.get("flow_7d_usd"), False),
                ("30D", row.get("flow_30d_usd"), True),
                ("ALL-TIME", row.get("flow_all_time_usd"), True),
            )
            for label, val, billions in specs:
                inner = _etf_tip_val_inner(val, prefer_billions=billions)
                pat = (
                    rf'(<div class="etf-tip-asset">{re.escape(sym)}</div>.*?'
                    rf'<span class="ev-k">{re.escape(label)}</span>\s*)'
                    rf'<span class="ev-v[^"]*">[^<]*</span>'
                )
                nb2, n = re.subn(pat, rf"\g<1>{inner}", nb, count=1, flags=re.S)
                if n != 1:
                    return b
                nb = nb2
        as_of = max(as_ofs) if as_ofs else None
        if as_of:
            nb2, n = re.subn(
                r'(<div class="ev-tip-foot"><div>As of · )[^<]+',
                rf"\g<1>{as_of}",
                nb,
                count=1,
            )
            if n != 1:
                return b
            nb = nb2
        return nb

    out = _map_card(html, "etf-card", body)
    if out != html:
        log.append(f"APPLY_OK {field}")
        if touches is not None:
            for needle in ("7 M D", "30 M D"):
                touches.append(
                    {"asset": "MARKET", "section": "market_top", "needle": needle, "field": field}
                )
    else:
        log.append(f"APPLY_MISS {field} n=0")
    return out


def verify_dual_render_parity(html: str) -> list[str]:
    """Return human-readable mismatches for dual-render market-top fields."""
    errs: list[str] = []

    vm = re.search(
        rf'{_PROTO_PORT_OPEN}.*?<div class="metric-value">\$([^<]+)',
        html,
        flags=re.S,
    )
    tm = re.search(
        rf'{_PROTO_PORT_OPEN}.*?<div class="ev-tip-read">\$([^<]+)',
        html,
        flags=re.S,
    )
    if vm and tm:
        v, t = _norm_num(vm.group(1)), _norm_num(tm.group(1))
        if v and t and v != t:
            errs.append(f"portfolio visible ${vm.group(1)} vs tooltip ${tm.group(1)}")

    m = re.search(
        r'class="metric-card has-tip fg-card"[^>]*>.*?class="fg-dial-num"[^>]*>(\d+).*?'
        r'<span class="ev-k">Index</span>\s*<span class="ev-v">(\d+)',
        html,
        flags=re.S,
    )
    if m and m.group(1) != m.group(2):
        errs.append(f"fear_greed dial {m.group(1)} vs tooltip index {m.group(2)}")

    m = re.search(
        r'BTC LEVERAGE.*?class="proto-line">BTC perps ~([\d.]+)×.*?'
        r'<span class="ev-k">Ratio</span>\s*<span class="ev-v">([\d.]+)×',
        html,
        flags=re.S,
    )
    if m:
        v, t = _norm_num(m.group(1)), _norm_num(m.group(2))
        if v and t and abs(float(v) - float(t)) > 0.05:
            errs.append(f"btc_leverage visible ~{m.group(1)}× vs tooltip {m.group(2)}×")

    etf = re.search(
        r'class="metric-card has-tip etf-card"[^>]*>(.*?)(?:</div>\s*){2,3}<div class="mkt-lead',
        html,
        flags=re.S,
    )
    if etf:
        block = etf.group(1)
        as_of_m = re.search(r"As of · ([^<]+)", block)
        foot_dates = re.findall(r"2026-\d{2}-\d{2}", block)
        if as_of_m and foot_dates and as_of_m.group(1).strip() not in foot_dates:
            errs.append(f"etf tooltip as_of {as_of_m.group(1)} not in row dates")
    return errs
