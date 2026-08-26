"""Hold-card crash net: live price · get-out · shelf — · empty siren. Do not restyle the desk strip."""

from __future__ import annotations

from typing import Any

from lib.v3.desk_strip import _e

HOLD_CARD_CSS = """
.hold-owned { display: none !important; }
.hold.hold-no-article { cursor: default; }
.hold-out { display: block; font-size: 0.62rem; line-height: 1.3; margin-top: 0.35rem; color: var(--ink); }
.hold-out.is-fired { color: var(--red); font-weight: 700; }
.hold-shelf { display: block; font-size: 0.62rem; color: var(--muted); margin-top: 0.12rem; min-height: 0.85em; }
.hold-siren { display: block; font-size: 0.62rem; min-height: 0.72rem; margin-top: 0.08rem; }
"""

HOLD_CLICK_JS = """
  document.querySelectorAll('.hold').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var slug = btn.getAttribute('data-asset-slug');
      if (!slug) return;
      var art = document.querySelector('.asset-v3-report[data-asset="'+slug+'"]');
      if (!art) return;
      document.querySelectorAll('.hold').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      document.querySelectorAll('.asset-v3-report').forEach(function (el) {
        if (el.getAttribute('data-asset') === slug) el.classList.remove('is-hidden');
        else el.classList.add('is-hidden');
      });
    });
  });
"""

HOLD_LIVE_JS = """
  (function holdLivePx() {
    function fmt(n) {
      var x = Number(n);
      if (!isFinite(x)) return null;
      if (x >= 1000) return '$' + Math.round(x).toLocaleString('en-US');
      if (x >= 1) return '$' + x.toFixed(2);
      var s = x.toFixed(10).replace(/0+$/, '');
      if (s.charAt(s.length - 1) === '.') s += '0';
      return '$' + s;
    }
    function setPx(el, n) {
      var t = fmt(n);
      if (t) el.textContent = t;
    }
    function tick() {
      var cards = document.querySelectorAll('.hold[data-feed]');
      var spot = [];
      cards.forEach(function (c) {
        var raw = c.getAttribute('data-feed') || '';
        var i = raw.indexOf(':');
        if (i < 0) return;
        var kind = raw.slice(0, i);
        var id = raw.slice(i + 1);
        var px = c.querySelector('[data-live-px]');
        if (!px) return;
        if (kind === 'spot') spot.push({ id: id, px: px });
        else if (kind === 'perp') {
          fetch('https://fapi.binance.com/fapi/v1/ticker/price?symbol=' + encodeURIComponent(id))
            .then(function (r) { return r.json(); })
            .then(function (j) { if (j && j.price) setPx(px, j.price); })
            .catch(function () {});
        } else if (kind === 'dex') {
          fetch('https://api.dexscreener.com/latest/dex/tokens/' + encodeURIComponent(id))
            .then(function (r) { return r.json(); })
            .then(function (js) {
              var pairs = (js && js.pairs) || [];
              pairs.sort(function (a, b) {
                var la = (a.liquidity && a.liquidity.usd) || 0;
                var lb = (b.liquidity && b.liquidity.usd) || 0;
                return lb - la;
              });
              if (pairs[0] && pairs[0].priceUsd) setPx(px, pairs[0].priceUsd);
            })
            .catch(function () {});
        } else if (kind === 'cg') {
          fetch('https://api.coingecko.com/api/v3/simple/price?ids=' + encodeURIComponent(id) + '&vs_currencies=usd')
            .then(function (r) { return r.json(); })
            .then(function (js) {
              var n = js && js[id] && js[id].usd;
              if (n != null) setPx(px, n);
            })
            .catch(function () {});
        }
      });
      if (spot.length) {
        fetch('https://api.binance.com/api/v3/ticker/price')
          .then(function (r) { return r.json(); })
          .then(function (rows) {
            var map = {};
            if (Array.isArray(rows)) rows.forEach(function (r) { map[r.symbol] = r.price; });
            spot.forEach(function (s) { if (map[s.id]) setPx(s.px, map[s.id]); });
          })
          .catch(function () {});
      }
    }
    tick();
    setInterval(tick, 45000);
  })();
"""


def feed_attr(name: str, cfg: dict[str, Any]) -> str:
    venue = (cfg.get("venues") or {}).get(name)
    extras = cfg.get("extra_mints") or {}
    if name == "NOS":
        mint = extras.get("NOS") or "nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7"
        return f"dex:{mint}"
    if venue:
        kind, symbol = venue
        if kind == "coingecko":
            mint = extras.get(name)
            if mint:
                return f"dex:{mint}"
            return f"cg:{symbol}"
        return f"{kind}:{symbol}"
    mint = extras.get(name)
    if mint:
        return f"dex:{mint}"
    return ""


def fmt_px(n: float) -> str:
    if n >= 1000:
        return f"${n:,.0f}"
    if n >= 1:
        return f"${n:.2f}"
    s = f"{n:.10f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return "$" + s


def hold_cards_html(rows: list[dict[str, Any]]) -> str:
    bits = []
    for row in rows:
        slug = row.get("article_slug")
        cls = "hold" if slug else "hold hold-no-article"
        slug_attr = f' data-asset-slug="{_e(slug)}"' if slug else ""
        feed = row.get("feed") or ""
        feed_attr_s = f' data-feed="{_e(feed)}"' if feed else ""
        out_cls = "hold-out is-fired" if row.get("fired") else "hold-out"
        bits.append(
            f'<button class="{cls}" type="button"{slug_attr}{feed_attr_s}>'
            f'<span class="hold-name"><span class="hold-ticker">{_e(row["name"])}</span>'
            f'<span class="hold-px" data-live-px>{_e(row["price"])}</span></span>'
            f'<span class="{out_cls}">{_e(row["get_out"])}</span>'
            f'<span class="hold-shelf">—</span>'
            f'<span class="hold-siren" aria-hidden="true"></span>'
            f"</button>"
        )
    return "\n".join(bits)
