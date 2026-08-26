"""Render asset report V4 to HTML."""

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from lib.paths import REPORTS, TEMPLATES


def _e(s) -> str:
    return html.escape(str(s))


def _emoji(colour: str) -> str:
    return {"GREEN": "🟢", "ORANGE": "🟠", "RED": "🔴"}.get(colour, "🟠")


def _call_class(call: str) -> str:
    return {"BUY": "call-green", "HOLD": "call-orange", "REDUCE": "call-red", "SELL": "call-red"}.get(
        call.upper(), "call-orange"
    )


def _lamp_html(colour: str) -> str:
    cc = colour.lower()
    return f'<span class="signal-lamp lamp-{cc}" aria-label="{_e(colour)}"></span>'


def _format_report_date(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    day = d.day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} of {d.strftime('%B')}, {d.year}"


def _asset_slug(report: dict) -> str:
    return {
        "RENDER": "render",
        "IO": "io",
        "NOS": "nos",
        "SOL": "sol",
        "GRASS": "grass",
        "FARTCOIN": "fartcoin",
        "SPX6900": "spx6900",
        "PUMP": "pump",
    }.get(report["asset"], report["asset"].lower())


def list_asset_weeks(asset_file: str = "render.json") -> list[str]:
    if not REPORTS.exists():
        return []
    return sorted(d.name for d in REPORTS.iterdir() if d.is_dir() and (d / asset_file).exists())


def render_asset_v4(report: dict, weeks: list[str] | None = None, *, sample: bool = False) -> str:
    css_path = TEMPLATES / "asset-v4.css"
    css = css_path.read_text() if css_path.exists() else ""

    signals_cards = ""
    slots = 8
    signals = report["signals"]
    for i in range(slots):
        if i < len(signals):
            s = signals[i]
            cc = s["colour"].lower()
            signals_cards += (
                f'<div class="signal-pallet signal-{cc}">'
                f'<div class="signal-head">'
                f'<span class="signal-name">{_e(s["name"])}</span>'
                f'{_lamp_html(s["colour"])}'
                f"</div>"
                f'<p class="signal-evidence">{_e(s["evidence"])}</p>'
                f"</div>\n"
            )
        else:
            signals_cards += (
                '<div class="signal-pallet signal-placeholder">'
                '<div class="signal-head">'
                '<span class="signal-name">Signal</span>'
                '<span class="signal-lamp lamp-grey" aria-hidden="true"></span>'
                "</div>"
                '<p class="signal-evidence">Evidence</p>'
                "</div>\n"
            )

    sources_line = " · ".join(_e(s["name"]) for s in report["sources"])

    weeks = weeks if weeks is not None else list_asset_weeks()
    if report["report_date"] not in weeks:
        weeks = sorted(set(weeks + [report["report_date"]]))

    slug = _asset_slug(report)

    def week_href(d: str) -> str:
        if sample:
            return f"../../reports/{d}/{slug}-v4.html"
        return f"../{d}/{slug}-v4.html"

    week_opts = "".join(
        f'<option value="{_e(week_href(w))}"{" selected" if w == report["report_date"] else ""}>'
        f'{_e(_format_report_date(w))}</option>'
        for w in reversed(weeks)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(report['asset'])} — Weekly Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600&family=Jost:wght@600;700;800&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<article class="asset-v4">
  <header class="verdict">
    <div class="title-bar">
      <h1 class="title-main">
        <span class="asset-name">{_e(report['asset'])}</span>
        <span class="price-inline">{_e(report['price_display'])}</span>
      </h1>
      <p class="call {_call_class(report['asset_call'])}">
        <span class="call-light" aria-hidden="true">{_emoji('GREEN' if report['asset_call']=='BUY' else 'RED' if report['asset_call'] in ('REDUCE','SELL') else 'ORANGE')}</span>
        {_e(report['asset_call'])}
      </p>
    </div>
    <div class="sub-bar">
      <p class="sub-line">
        Weekly Report
        <select class="week-inline" id="weekPick" aria-label="Report week" onchange="if(this.value)location.href=this.value">{week_opts}</select>
      </p>
      <p class="conf">Confidence: {_e(report['confidence'].title())}</p>
    </div>
    <p class="thesis">Thesis: {_e(report['thesis_status'])}</p>
    <p class="bottom-line"><strong>Bottom line:</strong> {_e(report['bottom_line'])}</p>
  </header>

  <div class="signals-grid">{signals_cards}</div>

  <p class="sources"><strong>Sources:</strong> {sources_line}</p>

  <section class="plain-section">
    <h2>What changed?</h2>
    <p>{_e(report['what_changed'])}</p>
  </section>

  <div class="cases-grid">
    <div class="case-pallet case-bull">
      <div class="case-head">
        <span class="case-name">Bull case</span>
        <span class="signal-lamp lamp-green" aria-hidden="true"></span>
      </div>
      <p class="case-body">{_e(report['bull_case'])}</p>
    </div>
    <div class="case-pallet case-bear">
      <div class="case-head">
        <span class="case-name">Bear case</span>
        <span class="signal-lamp lamp-red" aria-hidden="true"></span>
      </div>
      <p class="case-body">{_e(report['bear_case'])}</p>
    </div>
  </div>

  <section class="plain-section falsifiers">
    <h2>What proves us wrong?</h2>
    <p><strong>Bull thesis fails:</strong> {_e(report['thesis_fails_if'])}</p>
    <p><strong>Bull thesis strengthens:</strong> {_e(report['thesis_strengthens_if'])}</p>
  </section>
</article>
<script type="application/json" id="asset-report-json">{json.dumps(report)}</script>
</body>
</html>"""
