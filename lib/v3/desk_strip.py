"""Wallet desk strip: name · price · get-out · siren. Daily close vs config, not live tick."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from typing import Any

from lib.paths import CONFIG

DESK_CSS = """
.desk { margin: 0 0 1.1rem; }
.desk-head, .desk-row {
  display: grid;
  grid-template-columns: 6.2rem 7.6rem minmax(12rem,1fr) 7.2rem;
  gap: 0.55rem 0.8rem;
  align-items: center;
}
.desk-head {
  font-size: 0.62rem; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--muted);
  padding: 0 0.75rem 0.35rem;
}
.desk-row {
  width: 100%; text-align: left; font-family: inherit; color: var(--ink);
  background: var(--surface); border: 0; border-radius: 10px;
  padding: 0.55rem 0.75rem; margin: 0 0 0.35rem;
}
.desk-row.has-article { cursor: pointer; }
.desk-row.no-article { cursor: default; }
.desk-row.has-article:hover, .desk-row.active { background: var(--surface-strong); }
.desk-row.active { box-shadow: var(--shadow); }
.desk-name { font-family: var(--display); font-weight: 700; font-size: 0.92rem; letter-spacing: 0.04em; }
.desk-px { font-size: 0.8rem; color: var(--muted); }
.desk-out { font-size: 0.72rem; line-height: 1.3; color: var(--ink); border-radius: 6px; padding: 0.2rem 0.35rem; }
.desk-out.is-fired { color: var(--red); font-weight: 700; background: var(--red-wash); }
.desk-siren { font-size: 0.72rem; line-height: 1.3; min-height: 1em; }
@media (max-width: 840px) {
  .desk-head, .desk-row { grid-template-columns: 4.6rem 5.4rem 1fr 4.4rem; }
  .desk-out { font-size: 0.64rem; }
}
"""

DESK_JS = """
  document.querySelectorAll('.desk-row').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var slug = btn.getAttribute('data-asset-slug');
      if (!slug) return;
      var art = document.querySelector('.asset-v3-report[data-asset="'+slug+'"]');
      if (!art) return;
      document.querySelectorAll('.desk-row').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      document.querySelectorAll('.asset-v3-report').forEach(function (el) {
        if (el.getAttribute('data-asset') === slug) el.classList.remove('is-hidden');
        else el.classList.add('is-hidden');
      });
    });
  });
"""


def load_get_out() -> dict[str, Any]:
    return json.loads((CONFIG / "get_out.json").read_text())


def _e(s: str) -> str:
    return html.escape(str(s), quote=True)


def last_closed_kline(venue: str, symbol: str, interval: str) -> float | None:
    from urllib.parse import urlencode

    from lib.fetchers.http import get_json

    ms = {"1d": 86_400_000, "1h": 3_600_000}[interval]
    if venue == "spot":
        url = "https://api.binance.com/api/v3/klines"
    elif venue == "perp":
        url = "https://fapi.binance.com/fapi/v1/klines"
    else:
        return None
    rows = get_json(url, params={"symbol": symbol, "interval": interval, "limit": 5})
    if not isinstance(rows, list) or not rows:
        return None
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    closed = [r for r in rows if int(r[0]) + ms <= now]
    if not closed:
        closed = rows[:-1]
    if not closed:
        return None
    return float(closed[-1][4])


def last_closed_coingecko_daily(coin_id: str) -> float | None:
    from lib.fetchers.http import get_json

    data = get_json(
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
        params={"vs_currency": "usd", "days": 5, "interval": "daily"},
    )
    prices = data.get("prices") if isinstance(data, dict) else None
    if not isinstance(prices, list) or len(prices) < 2:
        return None
    # Last 00:00 UTC point is the in-progress day; prior point is last completed daily.
    return float(prices[-2][1])


def get_out_fired(name: str, cfg: dict[str, Any], closes: dict[str, dict[str, float]]) -> bool:
    spec = (cfg.get("levels") or {}).get(name) or {}
    kind = spec.get("kind")
    pack = closes.get(name) or {}
    if kind == "daily_close":
        close = pack.get("daily")
        level = spec.get("level")
        return close is not None and level is not None and close < float(level)
    if kind == "grass":
        d = pack.get("daily")
        h = pack.get("h1")
        fire_d = d is not None and d < float(spec["level_daily"])
        fire_h = h is not None and h < float(spec["level_1h"])
        return bool(fire_d or fire_h)
    return False


def fetch_closes(cfg: dict[str, Any]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for name, venue in (cfg.get("venues") or {}).items():
        kind, symbol = venue
        pack: dict[str, float] = {}
        if kind == "coingecko":
            d = last_closed_coingecko_daily(symbol)
            if d is not None:
                pack["daily"] = d
        else:
            d = last_closed_kline(kind, symbol, "1d")
            if d is not None:
                pack["daily"] = d
            if name == "GRASS":
                h = last_closed_kline(kind, symbol, "1h")
                if h is not None:
                    pack["h1"] = h
        if pack:
            out[name] = pack
    return out


def desk_html(rows: list[dict[str, Any]]) -> str:
    head = (
        '<section class="desk" aria-label="Wallet desk">'
        '<div class="desk-head"><span>Name</span><span>Price</span>'
        "<span>Get-out</span><span>Siren</span></div>"
    )
    bits = [head]
    for row in rows:
        slug = row.get("article_slug")
        cls = "desk-row has-article" if slug else "desk-row no-article"
        slug_attr = f' data-asset-slug="{_e(slug)}"' if slug else ""
        tag = "button" if slug else "div"
        type_attr = ' type="button"' if slug else ""
        out_cls = "desk-out is-fired" if row.get("fired") else "desk-out"
        siren = row.get("siren") or ""
        bits.append(
            f'<{tag} class="{cls}"{type_attr}{slug_attr}>'
            f'<span class="desk-name">{_e(row["name"])}</span>'
            f'<span class="desk-px">{_e(row["price"])}</span>'
            f'<span class="{out_cls}">{_e(row["get_out"])}</span>'
            f'<span class="desk-siren">{_e(siren) if siren else ""}</span>'
            f"</{tag}>"
        )
    bits.append("</section>")
    return "\n".join(bits)
