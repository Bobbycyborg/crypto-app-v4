"""Build dashboard v1 HTML from latest archived asset reports."""

from __future__ import annotations

import json
from pathlib import Path

from lib.asset_v4 import _format_report_date
from lib.paths import REPORTS, TEMPLATES

ASSET_SLUGS = [
    ("btc", "BTC", "btc"),
    ("sol", "SOL", "sol"),
    ("render", "RENDER", "render"),
    ("ray", "RAY", "ray"),
    ("io", "IO", "io"),
    ("nos", "NOS", "nos"),
    ("grass", "GRASS", "grass"),
    ("fartcoin", "FARTCOIN", "fartcoin"),
    ("spx6900", "SPX6900", "spx6900"),
    ("pump", "PUMP", "pump"),
    ("zec", "ZEC", "zec"),
    ("hype", "HYPE", "hype"),
]

# Keep these on the far right of the holdings strip (not ranked by wallet size).
HOLDING_STRIP_TRAIL = ("ZEC", "HYPE")


def _latest_report(slug: str) -> dict | None:
    if not REPORTS.exists():
        return None
    found: tuple[str, Path] | None = None
    for d in sorted(REPORTS.iterdir()):
        if not d.is_dir():
            continue
        p = d / f"{slug}.json"
        if p.exists():
            found = (d.name, p)
    if not found:
        return None
    return json.loads(found[1].read_text())


def _call_markup(call: str) -> tuple[str, str, str]:
    c = call.upper()
    if c in ("REDUCE", "SELL"):
        return "call-red", "lamp-red", c
    if c == "BUY":
        return "call-green", "lamp-green", c
    return "call-orange", "lamp-orange", c


def _hold_btn(asset_id: str, ticker: str, json_slug: str | None, report: dict | None) -> str:
    if not json_slug or not report:
        return f"""      <button type="button" class="hold-btn" data-asset="{asset_id}">
        <span class="hold-ticker">{ticker}</span>
        <span class="hold-price">—</span>
        <span class="hold-call call-muted">INCOMPLETE</span>
      </button>"""
    call_cls, lamp_cls, call_txt = _call_markup(report["asset_call"])
    price = report["price_display"].replace("~", "")
    src = f"{json_slug}-v4.html"
    active = ' active' if json_slug == "render" else ""
    lamp = f'<span class="lamp {lamp_cls}" aria-hidden="true"></span> '
    return f"""      <button type="button" class="hold-btn{active}" data-asset="{asset_id}" data-src="{src}">
        <span class="hold-ticker">{ticker}</span>
        <span class="hold-price">{price}</span>
        <span class="hold-call {call_cls}">{lamp}{call_txt}</span>
      </button>"""


def render_dashboard_v1() -> str:
    reports = {slug: _latest_report(slug) for _, _, slug in ASSET_SLUGS if slug}
    dates = sorted({r["report_date"] for r in reports.values() if r})
    week_label = _format_report_date(dates[-1]) if dates else "—"
    css_href = "../dashboard-v1.css"

    hold_buttons = "\n".join(
        _hold_btn(aid, tick, slug, reports.get(slug) if slug else None)
        for aid, tick, slug in ASSET_SLUGS
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crypto Decision Report — Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=Jost:wght@600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css_href}">
</head>
<body>
<div class="dash">

  <header class="dash-head">
    <h1>Crypto Decision Report</h1>
    <select class="week-inline" aria-label="Report week">
      <option selected>{week_label}</option>
    </select>
  </header>

  <section class="metric-block" aria-label="Portfolio summary">
    <div class="metric-row metric-row-4">
      <div class="metric-card">
        <div class="metric-label">Portfolio value</div>
        <div class="metric-value">$2,283</div>
        <div class="metric-sub">£1,714 tracked · BTC incomplete</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Weekly call</div>
        <div class="metric-value call-orange">WAIT</div>
        <div class="metric-sub">Confidence LOW</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Deploy this week</div>
        <div class="metric-value">$0</div>
        <div class="metric-sub">£250/mo planned · not deployed</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Alts beating BTC (30d)</div>
        <div class="metric-value call-red">0</div>
        <div class="metric-sub">of 8 tracked</div>
      </div>
    </div>
    <div class="metric-row metric-row-3">
      <div class="metric-card">
        <div class="metric-label">Crypto cycle</div>
        <div class="metric-value metric-with-lamp"><span class="lamp lamp-orange" aria-hidden="true"></span> Orange</div>
        <div class="metric-sub">BTC down-leg maturing · not confirmed</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Alt cycle</div>
        <div class="metric-value metric-with-lamp"><span class="lamp lamp-red" aria-hidden="true"></span> Red</div>
        <div class="metric-sub">Breadth weak · dominance rising</div>
      </div>
      <div class="metric-card metric-wide">
        <div class="metric-label">Bottom line</div>
        <div class="metric-bl">Hold all positions. Deploy $0 until BTC is connected and signals align.</div>
      </div>
    </div>
  </section>

  <section class="holdings-block" aria-label="Holdings">
    <h2 class="section-label">Holdings · tap to open report</h2>
    <div class="holdings-grid">
{hold_buttons}
    </div>
  </section>

  <section class="report-panel" aria-label="Asset report">
    <div class="report-panel-head">
      <h2 class="section-label" id="reportTitle">RENDER · Weekly Report</h2>
    </div>
    <div class="report-frame-wrap" id="reportFrameWrap">
      <iframe class="report-frame" id="reportFrame" title="Asset weekly report" src="render-v4.html"></iframe>
    </div>
    <div class="report-placeholder hidden" id="reportPlaceholder">
      <p><strong>Report not built yet.</strong></p>
      <p>BTC needs Coinbase connected. Other coins use the V4 weekly report when built.</p>
    </div>
  </section>
</div>
<script type="application/json" id="dashboard-holdings-json">{json.dumps({k: v for k, v in reports.items() if v})}</script>
<script>
(function () {{
  const buttons = document.querySelectorAll('.hold-btn');
  const frame = document.getElementById('reportFrame');
  const wrap = document.getElementById('reportFrameWrap');
  const placeholder = document.getElementById('reportPlaceholder');
  const title = document.getElementById('reportTitle');
  const labels = {{ btc: 'BTC', sol: 'SOL', render: 'RENDER', io: 'IO', nos: 'NOS', grass: 'GRASS', fartcoin: 'FARTCOIN', spx6900: 'SPX6900', '2z': '2Z' }};

  buttons.forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      buttons.forEach(function (b) {{ b.classList.remove('active'); }});
      btn.classList.add('active');
      const id = btn.dataset.asset;
      title.textContent = (labels[id] || id.toUpperCase()) + ' · Weekly Report';
      const src = btn.dataset.src;
      if (src) {{
        frame.src = src;
        wrap.classList.remove('hidden');
        placeholder.classList.add('hidden');
      }} else {{
        wrap.classList.add('hidden');
        placeholder.classList.remove('hidden');
      }}
      document.querySelector('.report-panel')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }});
  }});
}})();
</script>
</body>
</html>
"""


def write_dashboard_v1() -> Path:
    out = TEMPLATES / "samples" / "dashboard-v1.html"
    out.write_text(render_dashboard_v1())
    return out
