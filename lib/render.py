"""Render report.json to self-contained HTML."""

from __future__ import annotations

import html
import json
from pathlib import Path

from lib.paths import REPORTS, ROOT, TEMPLATES

COLOUR_CLASS = {"GREEN": "green", "YELLOW": "amber", "RED": "red"}
COLOUR_LABEL = {"GREEN": "Green", "YELLOW": "Amber", "RED": "Red"}


def _e(s) -> str:
    return html.escape(str(s)) if s is not None else ""


def _fmt_gbp(n: float) -> str:
    return f"£{n:,.0f}"


def _lamp(colour: str) -> tuple[str, str]:
    css = COLOUR_CLASS.get(colour, "amber")
    return css, COLOUR_LABEL.get(colour, colour.title())


def list_report_weeks() -> list[str]:
    if not REPORTS.exists():
        return []
    return sorted(d.name for d in REPORTS.iterdir() if d.is_dir() and (d / "report.json").exists())


def render(report: dict, weeks: list[str] | None = None, *, from_root: bool = True) -> str:
    weeks = weeks if weeks is not None else list_report_weeks()
    mock_text = (TEMPLATES / "mock-week1.html").read_text()
    i0 = mock_text.index("<style>") + len("<style>")
    i1 = mock_text.index("</style>")
    mock_css = mock_text[i0:i1]
    week_href = (lambda w: f"reports/{w}/report.html") if from_root else (lambda w: f"../{w}/report.html")
    r = report
    meta = r["meta"]
    port = r["portfolio"]
    top = r["topline"]
    sig = r["signals"]
    crypto = r["crypto_cycle_thesis"]
    alt = r["alt_cycle_thesis"]
    btc_ev = r["btc_cycle_evidence"]
    rec = r["recommendation"]

    cc, cl = _lamp(crypto["colour"])
    ac, al = _lamp(alt["colour"])
    mc, ml = _lamp(sig["btc_60d_momentum"]["colour"])
    bc, bl = _lamp(sig["alt_breadth_30d"]["colour"])

    week_opts = "".join(
        f'<option value="{_e(week_href(w))}"{" selected" if w == meta["report_date"] else ""}>{_e(w)}</option>'
        for w in reversed(weeks)
    )

    holdings_rows = ""
    for h in port["holdings"]:
        if h.get("status") == "INCOMPLETE":
            holdings_rows += f'<tr><td>{_e(h["symbol"])}</td><td class="num-r">—</td><td class="num-r incomplete" colspan="2">INCOMPLETE</td><td>—</td></tr>\n'
        else:
            bar = max(h.get("pct_portfolio", 0), 1)
            usd = h.get("value_usd", 0)
            holdings_rows += (
                f'<tr><td>{_e(h["symbol"])}</td><td class="num-r">{h["balance"]}</td>'
                f'<td class="num-r">{_fmt_gbp(h["value_gbp"])}</td><td class="num-r">${usd:,.0f}</td>'
                f'<td class="bar-cell"><div class="bar"><i style="width:{bar}%"></i></div></td></tr>\n'
            )

    changes_li = "".join(
        f'<li><strong>{_e(c["change"])}</strong><span>{_e(c["why_it_matters"])}</span></li>'
        for c in r["changes"]
    )
    counter_li = "".join(
        f'<li><strong>{_e(c["claim"])}</strong><span>{_e(c["counter"])}</span></li>'
        for c in r["counterarguments"]
    )
    actions_li = "".join(f"<li>{_e(a)}</li>" for a in rec["actions"])

    signal_cards = ""
    labels = {
        "btc_leg_fatigue": "Leg fatigue",
        "btc_drawdown_365d": "Drawdown 365d",
        "btc_60d_momentum": "60d momentum",
        "btc_four_year_position": "4y position",
        "alt_breadth_7d": "Alt breadth 7d",
        "alt_breadth_30d": "Alt breadth 30d",
        "btc_dominance_trend": "BTC dominance",
    }
    for sid, label in labels.items():
        s = sig[sid]
        c, lbl = _lamp(s["colour"])
        signal_cards += (
            f'<div class="sig"><div class="lbl">{_e(label)}</div>'
            f'<div class="val"><span class="lamp-a {c}"></span> {_e(lbl)}</div>'
            f'<div class="type">{_e(s["type"])}</div></div>\n'
        )

    sig_details = ""
    for sid in ("btc_leg_fatigue", "alt_breadth_30d"):
        s = sig[sid]
        c, lbl = _lamp(s["colour"])
        sig_details += (
            f'<details class="sig-detail"><summary>{_e(labels[sid])} '
            f'<span class="lamp-a {c}"></span> {_e(lbl)} · {_e(s["type"])}</summary>'
            f'<div class="body">{_e(s["detail"])}</div></details>\n'
        )

    incomplete = " · BTC incomplete" if meta.get("incomplete_flags") else ""
    report_json = json.dumps(report, separators=(",", ":"))

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crypto Decision Report — Week of {_e(meta["report_date"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=Jost:wght@600;700;800&display=swap" rel="stylesheet">
<style>
{mock_css}
</style>
</head>
<body>
<div class="wrap">
  <div class="banner">Week {_e(meta["report_date"])} · report v{_e(meta["version"])}</div>
  <div style="margin-bottom:1rem">
    <label for="weekPick" style="font-size:0.7rem;color:var(--muted)">Report week </label>
    <select id="weekPick" onchange="if(this.value)location.href=this.value">{week_opts}</select>
  </div>
  <header class="masthead">
    <h1>Crypto Decision Report</h1>
    <div class="meta">
      <span>Week of {_e(meta["report_date"])}</span>
      <span>Data as of {_e(meta["data_as_of"])}</span>
      <span>Report {_e(meta["version"])}</span>
    </div>
  </header>

  <div class="tl-bar">
    <div class="tl"><div class="title">Crypto Cycle</div><div class="lamp {cc}"></div><div class="status {"g" if cc=="green" else "am" if cc=="amber" else "r"}">{_e(cl)}</div></div>
    <div class="tl"><div class="title">Alt Cycle</div><div class="lamp {ac}"></div><div class="status {"g" if ac=="green" else "am" if ac=="amber" else "r"}">{_e(al)}</div></div>
    <div class="tl"><div class="title">Weekly Call</div><div class="lamp amber"></div><div class="status am">{_e(top["weekly_call"].replace("_", " "))}</div></div>
    <div class="tl"><div class="title">BTC Momentum</div><div class="lamp {mc}"></div><div class="status {"g" if mc=="green" else "am" if mc=="amber" else "r"}">{_e(ml)}</div></div>
    <div class="tl"><div class="title">Alt Breadth</div><div class="lamp {bc}"></div><div class="status {"g" if bc=="green" else "am" if bc=="amber" else "r"}">{_e(bl)}</div></div>
  </div>
  <p class="tl-key"><strong>Green</strong> supportive · <strong>Amber</strong> mixed · <strong>Red</strong> negative</p>

  <div class="hero">
    <div class="watermark" aria-hidden="true">{_e(top["weekly_call"].replace("_", " "))}</div>
    <div class="call">{_e(top["weekly_call"].replace("_", " "))}</div>
    <div class="deploy">Deploy <strong>{_fmt_gbp(top["deploy_gbp"])}</strong> this week · Confidence <strong>{_e(top["confidence"])}</strong></div>
    <p class="headline">{_e(top["headline"])}</p>
  </div>

  <div class="stat-strip">
    <div class="stat"><div class="lbl">Portfolio (tracked)</div><div class="num">{_fmt_gbp(port["total_gbp"])}</div><div class="sub">${port["total_usd"]:,.0f} USD · Sol wallet{incomplete}</div></div>
    <div class="stat"><div class="lbl">Thesis clock</div><div class="num">{meta.get("days_elapsed", 1)}</div><div class="sub">of 150 days · deadline {_e(meta["thesis_deadline"])}</div></div>
    <div class="stat"><div class="lbl">BTC leg</div><div class="num">{btc_ev["current_leg_days"]}d</div><div class="sub">{btc_ev["current_leg_dir"]} · {btc_ev["pct_through_median"]:.0%} of median</div></div>
    <div class="stat"><div class="lbl">Alts beating BTC (30d)</div><div class="num">{sig["alt_breadth_30d"]["summary"].split()[0]}</div><div class="sub">of 8 tracked</div></div>
  </div>

  <div class="grid-2">
    <section><h2>What changed</h2><ul class="plain">{changes_li}</ul></section>
    <section><h2>What could prove us wrong</h2><ul class="plain">{counter_li}</ul></section>
  </div>

  <div class="capital-grid">
    <div class="panel"><h3>Owned capital</h3><p class="big">{_fmt_gbp(r["capital"]["owned_gbp"])}</p><p class="foot">Wallet snapshot · Coinbase when connected</p></div>
    <div class="panel"><h3>Borrowed credit (separate)</h3><p class="big">{_fmt_gbp(r["capital"]["borrowed_gbp"])}</p><p class="foot">0% available · not deployed · never merged with owned total</p></div>
  </div>

  <div class="grid-2">
    <div class="panel">
      <div class="row"><h3>Crypto cycle thesis</h3><span class="pill {cc}">{_e(crypto["colour"])}</span></div>
      <p>{_e(crypto["summary"])}</p>
      <div class="clock" title="Day {meta.get('days_elapsed',1)} of 150"><i></i></div>
      <p class="foot">Confidence {_e(crypto["confidence"])} · JUDGEMENT · Day {meta.get("days_elapsed",1)} / 150</p>
    </div>
    <div class="panel">
      <div class="row"><h3>Alt-cycle thesis</h3><span class="pill {ac}">{_e(alt["colour"])}</span></div>
      <p>{_e(alt["summary"])}</p>
      <p class="foot">Confidence {_e(alt["confidence"])} · JUDGEMENT · breadth RULE {_e(alt["breadth_rule_colour"])}</p>
    </div>
  </div>

  <section style="margin-bottom:2rem">
    <h2>BTC cycle evidence</h2>
    <div class="panel">
      <p>BTC ${btc_ev["btc_price_usd"]:,.0f} · from 365d high <strong>{btc_ev["from_high_365d_pct"]:+.0f}%</strong> · 60d return <strong>{r["signals"]["btc_60d_momentum"]["summary"].split()[2]}</strong></p>
      <div class="btc-mini">
        <div><div class="l">Current leg</div><div class="n">{btc_ev["current_leg_days"]}d {btc_ev["current_leg_dir"]}</div></div>
        <div><div class="l">Avg leg (type)</div><div class="n">{btc_ev["median_leg_days"]}d</div></div>
        <div><div class="l">4y since low</div><div class="n">{r["signals"]["btc_four_year_position"]["summary"].split()[0]}d</div></div>
      </div>
      <p class="foot">{_e(btc_ev["hist_reversal_note"])}</p>
    </div>
  </section>

  <section>
    <h2>Signals</h2>
    <div class="signals">{signal_cards}</div>
    {sig_details}
  </section>

  <div class="actions">
    <h2>This week</h2>
    <ul>{actions_li}</ul>
  </div>

  <section>
    <h2>Holdings</h2>
    <table>
      <thead><tr><th>Asset</th><th class="num-r">Balance</th><th class="num-r">GBP</th><th class="num-r">USD</th><th class="bar-cell">Weight</th></tr></thead>
      <tbody>{holdings_rows}</tbody>
    </table>
  </section>

  <footer>
    Fonts: Futura (main) + DM Sans (body) · Pastel palette ·
    <code>python run_week.py</code> → report.json → HTML archive
  </footer>
</div>
<script type="application/json" id="report-json">{report_json}</script>
</body>
</html>"""
    return body


def write_report_files(report: dict, force: bool = False) -> Path:
    date = report["meta"]["report_date"]
    out_dir = REPORTS / date
    if out_dir.exists() and not force:
        raise FileExistsError(f"Report already exists: {out_dir} (use --force to replace)")
    out_dir.mkdir(parents=True, exist_ok=True)
    weeks = list_report_weeks() + [date]
    weeks = sorted(set(weeks))
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (out_dir / "report.html").write_text(render(report, weeks, from_root=False))
    (out_dir / "index.html").write_text(render(report, weeks, from_root=False))
    (ROOT / "index.html").write_text(render(report, weeks, from_root=True))
    return out_dir
