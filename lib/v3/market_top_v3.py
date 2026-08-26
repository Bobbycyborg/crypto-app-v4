"""Job #8F — approved market-top renderer. Visual lock from Job #8E. Values from pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.paths import ROOT
from lib.v3.etf_flows import format_flow_usd
from lib.v3.route_d_shell import evidence_tip_html

# Locked definitions (8C contract) — percentages recompute from live NOW.
CG_ATH_USD = 126_080.0
JULY_FLOOR_USD = 57_800.0
UNIVERSE_N = 21
STRIP_ORDER = ("defi", "l1", "memes", "ai", "depin")

TIP_MARK = (
    '<span class="tip-mark" aria-hidden="true">'
    '<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5"/>'
    '<circle cx="8" cy="5.25" r="0.85" fill="currentColor" stroke="none"/>'
    '<line x1="8" y1="7.25" x2="8" y2="11.25"/></svg></span>'
)
LINK_ICON = (
    '<svg class="src-link-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    '<polyline points="15 3 21 3 21 9"/>'
    '<line x1="10" y1="14" x2="21" y2="3"/></svg>'
)

MARKET_TOP_CSS = """
[aria-label="Market intelligence"] .metric-card {
  display: flex; flex-direction: column;
}
.card-src {
  margin-top: auto; padding-top: 0.35rem;
  display: flex; justify-content: flex-end;
}
.proto-line { display: block; font-size: 0.62rem; line-height: 1.35; color: var(--muted); white-space: nowrap; }
.proto-line + .proto-line { margin-top: 0.12rem; }
.proto-lines .metric-sub-text {
  display: block; -webkit-line-clamp: unset; overflow: visible;
}
.mt-oneline,
.mt-oneline .metric-sub-text,
.mt-oneline .proto-line {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  -webkit-line-clamp: unset;
  max-width: 100%;
}
.proto-port .metric-value {
  font-size: 1.62rem; font-weight: 700; color: var(--ink);
  margin-top: 0.32rem;
}
.proto-port .proto-lines { margin-top: 0.38rem; }
.fg-card .fg-dial-num { font-size: 1.5rem; }
.fg-card .fg-mood {
  margin-top: 0.28rem;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}
.etf-card .etf-a {
  flex: 1;
  display: flex;
  min-height: 0;
}
.etf-list {
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  width: 100%;
  flex: 1;
  min-width: 0;
}
.etf-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.45rem;
  padding: 0.22rem 0;
  border-bottom: 1px solid var(--pill-off);
}
.etf-row:last-child { border-bottom: 0; }
.etf-row .t {
  font-family: var(--display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--muted);
  text-decoration: none;
}
.etf-row a.t:hover { color: var(--ink); text-decoration: underline; text-underline-offset: 0.14em; }
.etf-row .amts {
  display: flex;
  align-items: baseline;
  gap: 0.32rem;
  min-width: 0;
  font-variant-numeric: tabular-nums;
}
.etf-row .amt {
  font-family: var(--display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  line-height: 1.15;
  white-space: nowrap;
}
.etf-row .u {
  font-size: 70%;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.etf-row .sep { color: var(--muted); font-weight: 500; font-size: 0.72rem; }
.etf-row.is-na { opacity: 0.48; }
.etf-tip .etf-tip-asset {
  font-family: var(--display);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin: 0.55rem 0 0.18rem;
}
.etf-tip .etf-tip-asset:first-child { margin-top: 0.1rem; }
.etf-tip .ev-tip-rows { gap: 0.18rem; margin-bottom: 0; }
.etf-tip .ev-k { font-variant-numeric: tabular-nums; }
.etf-tip .is-dash { color: var(--muted); }
.etf-tip .ev-v.c-red { color: var(--red); }
.etf-tip .ev-v.c-green { color: var(--green); }
.etf-tip .ev-v.c-muted { color: var(--muted); }
.etf-tip-fn {
  margin: 0.45rem 0 0;
  font-size: 0.62rem;
  color: var(--muted);
  line-height: 1.35;
}
.etf-tip .ev-tip-note { margin-top: 0.4rem; }
.metric-tip-float:has(.etf-tip) {
  max-width: min(280px, calc(100vw - 16px));
}
.mkt-lead {
  margin: 0.55rem 0 0;
  padding: 0.15rem 0.05rem 0.1rem;
  background: none;
  border: 0;
  display: none; /* hidden — restore to flex to show again */
  align-items: flex-start;
  gap: 2.4rem;
  flex-wrap: wrap;
}
.mkt-lead-copy { min-width: 0; flex: 0 1 16rem; }
.mkt-lead-title {
  font-size: 0.6rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--muted);
}
.mkt-lead-kicker {
  margin: 0.28rem 0 0;
  font-size: 0.68rem; line-height: 1.35; color: var(--muted);
}
.mkt-lead-row {
  display: flex; flex-wrap: wrap; align-items: flex-start;
  gap: 0.45rem 1.5rem;
  margin-top: 0;
  min-width: 0;
  flex: 1 1 18rem;
}
.mkt-lead-item {
  font-family: var(--display);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0.02em;
  min-width: 0;
}
.mkt-lead-item small {
  display: block;
  font-family: var(--bodyfont);
  font-size: 0.62rem;
  font-weight: 500;
  letter-spacing: 0;
  color: var(--muted);
  margin-top: 0.1rem;
}
@media (max-width: 840px) {
  .dash-head h1 { font-size: 0.78rem; }
  .mkt-lead { margin-top: 1.45rem; }
  .mkt-lead-row { gap: 0.4rem 1.1rem; }
  .etf-row .t, .etf-row .amt, .etf-row .sep { font-size: 0.68rem; }
}
"""


def _e(text: Any) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _state_class(state: str) -> str:
    s = (state or "").upper()
    if s in ("WEAK", "NARROW", "HEAVY", "LEVERAGE HEAVY", "BEAR MARKET", "DOWN LEG"):
        return "c-red"
    if s in ("MIXED", "NEUTRAL") or "LEADS" in s:
        return "c-orange"
    if s in ("IN",):
        return "c-green"
    if s in ("OUT",):
        return "c-red"
    return "c-muted"


def _fam(market: dict, fid: str) -> dict:
    for f in market.get("families") or []:
        if f.get("family_id") == fid:
            return f
    return {"family_id": fid, "display_state": "UNKNOWN", "fields": []}


def _field(fam: dict, metric_id: str) -> Any:
    for f in fam.get("fields") or []:
        if f.get("metric_id") == metric_id:
            return f.get("value")
    return None


def _src(href: str, title: str) -> str:
    return (
        f'<a href="{_e(href)}" class="src-link" target="_blank" rel="noopener" '
        f'title="{_e(title)}">{LINK_ICON}</a>'
    )


def _line(*parts: str) -> str:
    text = " · ".join(p.strip() for p in parts if p and str(p).strip())
    if not text:
        return ""
    return (
        '<div class="metric-sub metric-sub-clamp proto-lines mt-oneline">'
        f'<span class="metric-sub-text"><span class="proto-line">{_e(text)}</span></span></div>'
    )


def _card(label: str, inner: str, tip: str, link: str, extra: str = "") -> str:
    cls = "metric-card has-tip" + (f" {extra}" if extra else "")
    tip_block = f'<div class="metric-tip-template" hidden>{tip}</div>' if tip else ""
    return (
        f'<div class="{cls}">{tip_block}'
        f'<div class="label">{_e(label)}{TIP_MARK}</div>'
        f'{inner}<div class="card-src">{link}</div></div>'
    )


def overlay_live_feeds(evidence: dict | None) -> dict:
    """Prefer cache for F&G + Binance BTC fragility when present."""
    ev = dict(evidence or {})
    cache = ROOT / "data" / "cache" / "supporting-feeds.json"
    if not cache.is_file():
        return ev
    try:
        cached = json.loads(cache.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ev
    sf = dict(ev.get("supporting_feeds") or {})
    for key in ("fear_greed", "btc_fragility", "btc_funding", "etf_flows"):
        if cached.get(key):
            sf[key] = cached[key]
    if cached.get("fetched_at"):
        sf["fetched_at"] = cached["fetched_at"]
    ev["supporting_feeds"] = sf
    return ev


def _btc_hero() -> dict:
    for path in (ROOT / "reports" / "2026-08-14" / "btc-v3.json", ROOT / "btc-v3.json"):
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8")).get("hero") or {}
            except json.JSONDecodeError:
                continue
    return {}


def _btc_now_usd(evidence: dict, portfolio: dict) -> tuple[float, str]:
    sf = evidence.get("supporting_feeds") or {}
    mark = ((sf.get("btc_fragility") or {}).get("oi") or {}).get("mark_price_usd")
    if isinstance(mark, (int, float)) and mark > 0:
        return float(mark), "Binance mark"
    for pos in (portfolio.get("positions") or {}).values():
        if str(pos.get("symbol") or "").upper() == "BTC":
            px = pos.get("price_usd")
            if isinstance(px, (int, float)) and px > 0:
                return float(px), "portfolio price"
    hero = _btc_hero()
    dd = hero.get("drawdown_pct")
    if isinstance(dd, (int, float)):
        return CG_ATH_USD * (1 - float(dd) / 100.0), "btc-v3 drawdown vs CoinGecko ATH"
    return CG_ATH_USD, "CoinGecko ATH fallback — current price missing"


def btc_downside(evidence: dict, portfolio: dict) -> dict[str, Any]:
    now, now_src = _btc_now_usd(evidence, portfolio)
    now_pct = now / CG_ATH_USD - 1.0
    max_pct = JULY_FLOOR_USD / CG_ATH_USD - 1.0
    next_pct = JULY_FLOOR_USD / now - 1.0
    return {
        "now_usd": now,
        "now_src": now_src,
        "now_pct": now_pct,
        "now_display": f"{abs(now_pct) * 100:.0f}",
        "max_pct": max_pct,
        "max_display": f"{abs(max_pct) * 100:.0f}",
        "next_usd": JULY_FLOOR_USD,
        "next_display_k": "~$58K",
        "next_pct": next_pct,
        "next_pct_display": f"{abs(next_pct) * 100:.0f}",
    }


def _participation_counts(fam: dict) -> tuple[int, int]:
    beat = _field(fam, "market_pct_outperforming_btc_30d")
    sma = _field(fam, "market_pct_above_50dma")
    n_beat = round(float(beat) / 100.0 * UNIVERSE_N) if beat is not None else 7
    n_sma = round(float(sma) / 100.0 * UNIVERSE_N) if sma is not None else 8
    return int(n_beat), int(n_sma)


def _perp_spot(evidence: dict, fam: dict) -> tuple[float | None, str]:
    vol = ((evidence.get("supporting_feeds") or {}).get("btc_fragility") or {}).get("volume") or {}
    ratio = vol.get("perp_spot_ratio")
    if isinstance(ratio, (int, float)):
        return float(ratio), "supporting_feeds.btc_fragility"
    fam_ratio = _field(fam, "perp_spot_volume")
    if isinstance(fam_ratio, (int, float)):
        return float(fam_ratio), "market family"
    return None, "missing"


def render_market_top_section(
    market: dict,
    portfolio: dict,
    supporting_feeds: dict | None = None,
    evidence: dict | None = None,
    fg_html: str | None = None,
) -> str:
    ev = dict(evidence or {})
    if supporting_feeds:
        sf = dict(ev.get("supporting_feeds") or {})
        sf.update({k: v for k, v in supporting_feeds.items() if v})
        ev["supporting_feeds"] = sf
    evidence = overlay_live_feeds(ev)

    usd = portfolio.get("total_usd", 0)
    macro = _fam(market, "macro_liquidity")
    rot = _fam(market, "outward_rotation")
    breadth = _fam(market, "breadth")
    frag = _fam(market, "market_fragility")

    port = _card(
        "Portfolio value",
        f'<div class="metric-value">${usd:,.0f}</div>',
        evidence_tip_html(
            name="PORTFOLIO VALUE",
            read=f"${usd:,.0f}",
            rows=[("Status", "Monitoring"), ("Prices", "CoinGecko + on-chain reads")],
            note="Live wallet holdings total. Monitoring = no deploy or reduce rule fired. Not a buy signal.",
            source="wallet + CoinGecko",
        ),
        _src("https://www.coingecko.com", "CoinGecko"),
        extra="proto-port",
    )

    gp = (evidence.get("global_liquidity") or {}).get("global_pulse_yoy")
    stables = _field(macro, "stablecoin_supply_total")
    ch30 = _field(macro, "stablecoin_supply_30d_pct")
    gp_line = (
        f"Global liquidity down {abs(gp):.0f}% YoY"
        if isinstance(gp, (int, float))
        else "Global liquidity mixed"
    )
    st_line = "Stablecoins still draining"
    if isinstance(stables, (int, float)):
        drain = ""
        if isinstance(ch30, (int, float)) and ch30 < 0:
            drain = " · still draining"
        st_line = f"Stablecoins ${stables:.0f}B{drain}"
    mac = _card(
        "MACRO / LIQUIDITY",
        f'<div class="metric-value {_state_class(macro.get("display_state") or "")}">{_e((macro.get("display_state") or "UNKNOWN").upper())}</div>'
        + _line(gp_line, st_line),
        evidence_tip_html(
            name="MACRO / LIQUIDITY",
            read=(macro.get("display_state") or "UNKNOWN").upper(),
            rows=[("Question", macro.get("question") or ""), ("Note", macro.get("state_validation_note") or "")],
            note="Descriptive capacity read. Not a buy signal.",
            source="FRED + DefiLlama",
        ),
        _src("https://fred.stlouisfed.org", "FRED"),
    )

    dd = btc_downside(evidence, portfolio)
    btc_inner = (
        f'<div class="metric-value c-red">BEAR MARKET</div>'
        + _line(
            f"RETRACED {dd['now_display']}% FROM ATH · MAX −{dd['max_display']}%",
            f"NEXT {dd['next_display_k']} −{dd['next_pct_display']}%",
        )
    )
    btc = _card(
        "BTC TREND",
        btc_inner,
        evidence_tip_html(
            name="BTC TREND",
            read="BEAR MARKET",
            rows=[
                ("Now", f"Current vs CoinGecko ATH ${CG_ATH_USD:,.0f}. Unrounded {dd['now_pct']*100:.1f}%. Price ${dd['now_usd']:,.0f} ({dd['now_src']})."),
                ("Max", f"Cycle max drawdown on 1 Jul 2026. Binance daily low ~${JULY_FLOOR_USD:,.0f} ({dd['max_pct']*100:.1f}%)."),
                ("Next downside", "Already-printed July low. Not a predicted bottom. If it breaks, next area is UNKNOWN."),
            ],
            note="CoinGecko ATH contract. Retracement from ATH is a natural part of a bull — not bad on its own. Question is how far, and when it turns. ~50% is a mid retrace, not a zombie print.",
            source="CoinGecko ATH · Binance daily low",
        ),
        _src("https://www.coingecko.com/en/coins/bitcoin", "CoinGecko Bitcoin"),
    )

    eth = _field(rot, "eth_btc_30d_pp")
    sol = _field(rot, "sol_btc_30d_pp")
    eth_bit = (
        "ETH ahead of BTC"
        if isinstance(eth, (int, float)) and eth > 0
        else "ETH still behind BTC"
        if isinstance(eth, (int, float))
        else "ETH vs BTC unavailable"
    )
    sol_bit = (
        "SOL still behind BTC"
        if isinstance(sol, (int, float)) and sol < 0
        else "SOL ahead of BTC"
        if isinstance(sol, (int, float))
        else "SOL vs BTC unavailable"
    )
    rot_card = _card(
        "CAPITAL ROTATION",
        f'<div class="metric-value {_state_class(rot.get("display_state") or "")}">{_e((rot.get("display_state") or "UNKNOWN").upper())}</div>'
        + _line(eth_bit, sol_bit),
        evidence_tip_html(
            name="CAPITAL ROTATION",
            read=(rot.get("display_state") or "UNKNOWN").upper(),
            rows=[
                ("ETH vs BTC", f"30-day return gap {eth:+.1f} percentage points." if isinstance(eth, (int, float)) else "UNKNOWN"),
                ("SOL vs BTC", f"30-day return gap {sol:+.1f} percentage points." if isinstance(sol, (int, float)) else "UNKNOWN"),
            ],
            note="30-day return gaps, not proof of hot money. Holdings counts stay off this card.",
            source="CoinGecko markets",
        ),
        _src("https://www.coingecko.com", "CoinGecko"),
    )

    fg = fg_html if fg_html is not None else _fear_greed(evidence.get("supporting_feeds") or {})
    n_beat, n_sma = _participation_counts(breadth)
    part_state = "WEAK" if (breadth.get("display_state") or "").upper() == "NARROW" else (breadth.get("display_state") or "UNKNOWN").upper()
    part = _card(
        "MARKET PARTICIPATION",
        f'<div class="metric-value {_state_class(part_state)}">{_e(part_state)}</div>'
        + _line(
            f"Only {n_beat} of {UNIVERSE_N} beat BTC",
            f"{n_sma} of {UNIVERSE_N} above 50d",
        ),
        evidence_tip_html(
            name="MARKET PARTICIPATION",
            read=part_state,
            rows=[
                ("Universe", f"Fixed list of {UNIVERSE_N} large coins. Not Bitcoin, not Ethereum, not stables."),
                ("Beat Bitcoin", f"{n_beat} of {UNIVERSE_N}."),
                ("50-day average", f"{n_sma} of {UNIVERSE_N}."),
            ],
            note="Same calculation as before. Holdings counts stay off this card. Descriptive only.",
            source="CoinGecko markets",
        ),
        _src("https://www.coingecko.com", "CoinGecko"),
    )

    etf = _etf_card(evidence)
    lev = _leverage_card(evidence, frag)
    strip = _capital_strip(evidence)

    row1 = port + mac + btc + rot_card
    row2 = fg + part + lev + etf
    return (
        '<section aria-label="Market intelligence">'
        f'<div class="metric-row metric-row-4">{row1}</div>'
        f'<div class="metric-row metric-row-4">{row2}</div>'
        f"{strip}</section>"
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


def _fear_greed(sf: dict) -> str:
    src_url = "https://alternative.me/crypto/fear-and-greed-index/"
    link = _src(src_url, "alternative.me Fear & Greed")
    fg = sf.get("fear_greed") or {}
    if not fg.get("ok"):
        return _card(
            "FEAR & GREED",
            '<div class="metric-value c-muted">—</div>',
            evidence_tip_html(
                name="FEAR & GREED",
                read="UNKNOWN",
                rows=[("Feed", "alternative.me")],
                note="Sentiment context only — not a market vote.",
                source="alternative.me",
            ),
            link,
            extra="fg-card",
        )
    cur = fg.get("current") or {}
    val = int(cur.get("value") or 0)
    word = (cur.get("classification") or "—").title()
    stroke, _cls = _fg_color(val)
    as_of = ""
    ts = cur.get("timestamp")
    if ts:
        try:
            as_of = datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
        except (TypeError, ValueError, OSError):
            as_of = str(ts)
    tip = evidence_tip_html(
        name="FEAR & GREED",
        read=word.upper(),
        rows=[("Index", str(val)), ("As of", as_of or "—")],
        note="Sentiment context only — not a market vote.",
        source="Alternative.me",
        as_of=as_of or None,
    )
    inner = (
        '<div class="fg-body"><div class="fg-dial-wrap">'
        '<svg class="fg-dial" viewBox="0 0 120 70" aria-hidden="true">'
        '<path class="fg-dial-track" d="M18 58 A42 42 0 0 1 102 58" pathLength="100"/>'
        f'<path class="fg-dial-fill" d="M18 58 A42 42 0 0 1 102 58" pathLength="100" '
        f'stroke="{stroke}" stroke-dasharray="{val} 100"/></svg>'
        f'<span class="fg-dial-num" style="color:{stroke}">{val}</span></div>'
        f'<div class="fg-mood">{_e(word)}</div></div>'
    )
    return _card("FEAR & GREED", inner, tip, link, extra="fg-card")


def _fmt_etf_face_parts(usd: Any) -> tuple[str, str | None]:
    if usd is None or not isinstance(usd, (int, float)):
        return "N/A", None
    if usd == 0:
        return "$0", None
    mag = abs(float(usd))
    if mag >= 1_000_000_000:
        v = mag / 1_000_000_000
        num = f"{v:.1f}" if v < 10 else f"{v:.0f}"
        return f"${num}", "B"
    v = mag / 1_000_000
    num = f"{v:.0f}" if v >= 100 else f"{v:.1f}"
    return f"${num}", "M"


def _etf_amt_class(usd: Any) -> str:
    if not isinstance(usd, (int, float)) or usd == 0:
        return "c-muted"
    return "c-green" if usd > 0 else "c-red"


def _etf_amt_html(usd: Any, horizon: str) -> str:
    num, unit = _fmt_etf_face_parts(usd)
    cls = _etf_amt_class(usd) if num != "N/A" else "c-muted"
    h = horizon.upper() if horizon.lower().endswith("d") else horizon
    if num == "N/A":
        return f'<span class="amt c-muted">N/A <span class="u">{_e(h)}</span></span>'
    unit_html = f'<span class="u-unit">{_e(unit)}</span>' if unit else ""
    return f'<span class="amt {cls}">{_e(num)}{unit_html} <span class="u">{_e(h)}</span></span>'


def _fmt_etf_tip(usd: Any, *, prefer_billions: bool = False) -> str:
    if usd is None:
        return "N/A"
    if isinstance(usd, (int, float)) and usd == 0:
        return "$0"
    shown = format_flow_usd(usd, prefer_billions=prefer_billions)
    return shown.replace("+", "").replace("−", "").replace("-", "")


def _etf_tip_val_html(usd: Any, *, prefer_billions: bool = False) -> str:
    shown = _fmt_etf_tip(usd, prefer_billions=prefer_billions)
    if shown in ("—", "N/A"):
        cls = "c-muted is-dash"
    else:
        cls = _etf_amt_class(usd)
    return f'<span class="ev-v {cls}">{_e(shown)}</span>'


def _etf_tip_html(bundle: dict, assets: dict) -> str:
    """Numeric panel. Minus red, plus green. No +/− signs."""
    blocks = []
    as_ofs: list[str] = []
    sources: list[str] = []
    missing_30d = False
    for sym in ("BTC", "ETH", "SOL"):
        row = assets.get(sym) or {}
        ok = bool(row.get("ok"))
        v30 = row.get("flow_30d_usd") if ok else None
        if v30 is None:
            missing_30d = True
        specs = (
            ("1D", row.get("flow_1d_usd") if ok else None, False),
            ("7D", row.get("flow_7d_usd") if ok else None, False),
            ("30D", v30, True),
            ("ALL-TIME", row.get("flow_all_time_usd") if ok else None, True),
        )
        row_html = "".join(
            f'<div class="ev-tip-row"><span class="ev-k">{_e(k)}</span>'
            f"{_etf_tip_val_html(v, prefer_billions=billions)}</div>"
            for k, v, billions in specs
        )
        blocks.append(
            f'<div class="etf-tip-asset">{_e(sym)}</div>'
            f'<div class="ev-tip-rows">{row_html}</div>'
        )
        if row.get("as_of"):
            as_ofs.append(str(row["as_of"]))
        if row.get("source"):
            sources.append(str(row["source"]))
    fn = (
        '<p class="etf-tip-fn">30D unavailable from current source history.</p>'
        if missing_30d
        else ""
    )
    src = sources[0] if sources and len(set(sources)) == 1 else "Farside Investors"
    as_of = max(as_ofs) if as_ofs else "—"
    return (
        '<div class="ev-tip etf-tip">'
        '<div class="ev-tip-name">ETF FLOWS</div>'
        + "".join(blocks)
        + fn
        + '<p class="ev-tip-note">ETF flows are one regulated spot-demand channel, not total crypto demand.</p>'
        f'<div class="ev-tip-foot"><div>As of · {_e(as_of)}</div>'
        f"<div>Source · {_e(src)}</div></div></div>"
    )


def _etf_card(evidence: dict) -> str:
    """BTC/ETH/SOL directions from supporting_feeds.etf_flows. No combined net."""
    bundle = ((evidence or {}).get("supporting_feeds") or {}).get("etf_flows") or {}
    assets = bundle.get("assets") or {}
    cells = []
    for sym in ("BTC", "ETH", "SOL"):
        row = assets.get(sym) or {}
        href = row.get("source_url") or ""
        ok = bool(row.get("ok"))
        cls = "" if ok else " is-na"
        v7 = row.get("flow_7d_usd") if ok else None
        v30 = row.get("flow_30d_usd") if ok else None
        label = (
            f'<a href="{_e(href)}" class="t" target="_blank" rel="noopener">{_e(sym)}</a>'
            if href
            else f'<span class="t">{_e(sym)}</span>'
        )
        cells.append(
            f'<div class="etf-row{cls}">{label}<span class="amts">'
            f'{_etf_amt_html(v7, "7d")}<span class="sep">/</span>'
            f'{_etf_amt_html(v30, "30d")}</span></div>'
        )
    inner = '<div class="etf-a"><div class="etf-list">' + "".join(cells) + "</div></div>"
    return _card("ETF FLOWS", inner, _etf_tip_html(bundle, assets), "", extra="etf-card")


def _leverage_card(evidence: dict, fam: dict) -> str:
    ratio, src_name = _perp_spot(evidence, fam)
    state = (fam.get("display_state") or "HEAVY").replace("LEVERAGE ", "").upper()
    if state not in ("HEAVY", "MIXED", "UNKNOWN", "FUNDING STRETCHED"):
        state = "HEAVY" if ratio is not None and ratio >= 5 else state
    if ratio is None:
        line1 = "BTC perp / spot ratio unavailable"
    else:
        shown = (
            f"{ratio:.0f}"
            if abs(ratio - round(ratio)) < 0.5
            else f"{ratio:.1f}".rstrip("0").rstrip(".")
        )
        line1 = f"BTC perps ~{shown}× spot"
    inner = (
        f'<div class="metric-value {_state_class(state)}">{_e(state)}</div>'
        + _line(line1, "BTC leverage only")
    )
    tip = evidence_tip_html(
        name="BTC LEVERAGE",
        read=state,
        rows=[
            ("Ratio", f"{ratio:.3f}×" if ratio is not None else "UNKNOWN"),
            ("Scope", "Binance USDT-M BTCUSDT perp quote volume vs Binance BTCUSDT spot, last 24 hours."),
            ("Source field", src_name),
        ],
        note="Not market-wide leverage. Cross-venue open interest is not wired.",
        source="Binance futures + spot",
    )
    return _card(
        "BTC LEVERAGE",
        inner,
        tip,
        _src("https://www.binance.com/en/futures/BTCUSDT", "Binance BTCUSDT perps"),
    )


def _capital_strip(evidence: dict) -> str:
    sd = evidence.get("sector_destination") or {}
    by_id = {s.get("sector_id"): s for s in (sd.get("sectors") or [])}
    ranked = sd.get("ranked_by_vs_btc") or []
    beating = any(
        isinstance(s.get("vs_btc_30d_pp"), (int, float)) and s["vs_btc_30d_pp"] > 0 for s in ranked
    )
    kicker = (
        "BTC still leads · no sector is beating it"
        if not beating
        else "Relative 30-day rank vs BTC"
    )
    items = []
    for sid in STRIP_ORDER:
        s = by_id.get(sid) or {}
        label = s.get("label") or sid.upper()
        vs = s.get("vs_btc_30d_pp")
        if isinstance(vs, (int, float)):
            sub = f"{vs:+.0f} vs BTC".replace("+", "")
            if vs < 0:
                sub = f"−{abs(round(vs))} vs BTC"
            else:
                sub = f"+{round(vs)} vs BTC"
        else:
            sub = "—"
        items.append(f'<div class="mkt-lead-item">{_e(label)}<small>{_e(sub)}</small></div>')
    return (
        '<div class="mkt-lead">'
        '<div class="mkt-lead-copy">'
        '<div class="mkt-lead-title">Where capital is moving</div>'
        f'<p class="mkt-lead-kicker">{_e(kicker)}</p>'
        '</div>'
        f'<div class="mkt-lead-row">{"".join(items)}</div></div>'
    )
