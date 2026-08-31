"""Derive stance LEADS/LAGS and ABOVE/BELOW from the canonical snapshot."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

_ARTICLE_RE = re.compile(
    r'(<article[^>]*data-asset="([^"]+)"[^>]*>)(.*?)(</article>)',
    re.S,
)
_BTC_RS = re.compile(r"(?:LEADS|LAGS) BTC 7d(?:/30d| \u00b7 (?:LEADS|LAGS) 30d)")
_SOL_RS = re.compile(r"(?:LEADS|LAGS) SOL 7d(?:/30d| \u00b7 (?:LEADS|LAGS) 30d)")
_RS_HEAD = re.compile(
    r"(?:RS LEADS|RS LAGS|(?:LEADS|LAGS) 7D \u00b7 (?:LEADS|LAGS) 30D)"
)


def _num(snapshot: dict[str, Any], mid: str) -> Decimal | None:
    rec = snapshot.get("metrics", {}).get(mid)
    if not rec or rec.get("status") != "OK":
        return None
    try:
        return Decimal(str(rec["normalized_value"]))
    except Exception:
        return None


def _lang(val: Decimal) -> str:
    return "LAGS" if val < 0 else "LEADS"


def _rewrite_pump(art: str, snapshot: dict[str, Any]) -> str:
    btc7 = _num(snapshot, "pump.rs.vs_btc.pct.7d")
    btc30 = _num(snapshot, "pump.rs.vs_btc.pct.30d")
    sol7 = _num(snapshot, "pump.rs.vs_sol.pct.7d")
    sol30 = _num(snapshot, "pump.rs.vs_sol.pct.30d")
    if None in (btc7, btc30, sol7, sol30):
        return art
    btc7_l, btc30_l = _lang(btc7), _lang(btc30)
    sol7_l, sol30_l = _lang(sol7), _lang(sol30)
    art = _BTC_RS.sub(f"{btc7_l} BTC 7d \u00b7 {btc30_l} 30d", art)
    art = _SOL_RS.sub(f"{sol7_l} SOL 7d \u00b7 {sol30_l} 30d", art)
    if btc7_l == btc30_l:
        head = "RS LEADS" if btc7_l == "LEADS" else "RS LAGS"
    else:
        head = f"{btc7_l} 7D \u00b7 {btc30_l} 30D"
    return _RS_HEAD.sub(head, art, count=1)


def _rewrite_io(art: str, snapshot: dict[str, Any]) -> str:
    price = _num(snapshot, "io.price.usd.live")
    ma50 = _num(snapshot, "io.ma.usd.50d")
    ma200 = _num(snapshot, "io.ma.usd.200d")
    if None in (price, ma50, ma200):
        return art
    below50 = price < ma50
    below200 = price < ma200
    if below50 and below200:
        art = art.replace("Price is above 50d and 200d", "Price is below 50d and 200d")
        art = art.replace("Above 50d + 200d", "Below 50d + 200d")
    elif not below50 and not below200:
        art = art.replace("Price is below 50d and 200d", "Price is above 50d and 200d")
        art = art.replace("Below 50d + 200d", "Above 50d + 200d")
    return art


def apply_semantic_wording(html: str, snapshot: dict[str, Any]) -> str:
    def repl(m: re.Match[str]) -> str:
        asset, inner = m.group(2), m.group(3)
        if asset == "pump":
            inner = _rewrite_pump(inner, snapshot)
        elif asset == "io":
            inner = _rewrite_io(inner, snapshot)
        return m.group(1) + inner + m.group(4)

    return _ARTICLE_RE.sub(repl, html)
