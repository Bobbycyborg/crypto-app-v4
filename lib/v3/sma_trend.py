"""Shared 50d/200d technical-trend helper for Risk & Confirmation stacks.

Spot preferred; perp fallback labelled. NOS uses CoinGecko daily.
Do not call 50>200 a bullish golden when price is below both MAs.
Tiny 60d HH → range, not a new uptrend.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any
from urllib.parse import urlencode

from lib.v3.fields import category_state

TINY_HH_PCT = 0.03
GOLDEN_LOST_DAYS = 40

VENUES: dict[str, tuple[str, str]] = {
    "render": ("spot", "RENDERUSDT"),
    "ray": ("spot", "RAYUSDT"),
    "io": ("spot", "IOUSDT"),
    "zec": ("spot", "ZECUSDT"),
    "grass": ("perp", "GRASSUSDT"),
    "fartcoin": ("perp", "FARTCOINUSDT"),
    "spx": ("perp", "SPXUSDT"),
    "hype": ("perp", "HYPEUSDT"),
    "nos": ("coingecko", "nosana"),
    "btc": ("spot", "BTCUSDT"),
    "sol": ("spot", "SOLUSDT"),
    "pump": ("spot", "PUMPUSDT"),
}

_CACHE: dict[str, dict[str, Any]] = {}


def _norm_slug(slug: str) -> str:
    s = str(slug or "").strip().lower()
    return {"spx6900": "spx", "fart": "fartcoin"}.get(s, s)


def _px(n: float) -> str:
    if n >= 100:
        return f"~{n:.0f}"
    if n >= 10:
        return f"~{n:.1f}"
    if n >= 1:
        return f"~{n:.2f}"
    return f"~{n:.3f}"


def _http_json(url: str, params: dict[str, Any] | None = None) -> Any:
    try:
        from lib.fetchers.http import get_json

        return get_json(url, params=params)
    except Exception:
        q = url
        if params:
            q = f"{url}?{urlencode(params)}"
        r = subprocess.run(
            ["curl", "-sS", "--max-time", "45", q],
            capture_output=True,
            text=True,
            timeout=50,
            check=False,
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or f"curl failed {q}")
        return json.loads(r.stdout)


def _closes_binance(symbol: str, venue: str) -> list[float]:
    if venue == "spot":
        url = "https://api.binance.com/api/v3/klines"
    else:
        url = "https://fapi.binance.com/fapi/v1/klines"
    rows = _http_json(url, {"symbol": symbol, "interval": "1d", "limit": 300})
    if not isinstance(rows, list) or len(rows) < 200:
        raise RuntimeError(f"short kline pack {venue} {symbol}")
    return [float(r[4]) for r in rows]


def _closes_coingecko(coin_id: str) -> list[float]:
    data = _http_json(
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
        {"vs_currency": "usd", "days": 250, "interval": "daily"},
    )
    prices = data.get("prices") if isinstance(data, dict) else None
    if not isinstance(prices, list) or len(prices) < 200:
        raise RuntimeError(f"short CoinGecko pack {coin_id}")
    return [float(p[1]) for p in prices if isinstance(p, (list, tuple)) and len(p) >= 2]


def _sma(closes: list[float], n: int, end: int) -> float:
    window = closes[end - n + 1 : end + 1]
    return sum(window) / n


def _last_cross(closes: list[float]) -> tuple[str | None, int | None]:
    last: tuple[str, int] | None = None
    prev_diff: float | None = None
    for i in range(199, len(closes)):
        diff = _sma(closes, 50, i) - _sma(closes, 200, i)
        if prev_diff is not None and prev_diff <= 0 < diff:
            last = ("golden", len(closes) - 1 - i)
        elif prev_diff is not None and prev_diff >= 0 > diff:
            last = ("death", len(closes) - 1 - i)
        prev_diff = diff
    if last is None:
        return None, None
    return last


def _structure(closes: list[float]) -> tuple[str, str, bool]:
    last = closes[-60:]
    prior = closes[-120:-60]
    last_h, last_l = max(last), min(last)
    prior_h, prior_l = max(prior), min(prior)
    hh = last_h > prior_h
    hl = last_l > prior_l
    lh = last_h < prior_h
    ll = last_l < prior_l
    tiny_hh = hh and prior_h > 0 and (last_h - prior_h) / prior_h < TINY_HH_PCT
    if tiny_hh:
        return "range", "tiny HH", True
    if lh and ll:
        return "LH+LL", "LH+LL", False
    if lh and hl:
        return "LH+HL", "LH+HL", False
    if hh and hl:
        return "HH+HL", "HH+HL", False
    if hh and ll:
        return "HH+LL", "HH+LL", False
    return "range", "mixed", False


def compute_sma_trend(slug: str) -> dict[str, Any]:
    key = _norm_slug(slug)
    if key in _CACHE:
        return _CACHE[key]
    spec = VENUES.get(key)
    if spec is None:
        out = {
            "ok": False,
            "state": "UNKNOWN",
            "summary": "50d/200d UNKNOWN",
            "detail": f"No venue map for {key}.",
            "venue": "unknown",
        }
        _CACHE[key] = out
        return out
    venue, symbol = spec
    try:
        closes = (
            _closes_coingecko(symbol)
            if venue == "coingecko"
            else _closes_binance(symbol, venue)
        )
        i = len(closes) - 1
        price = closes[i]
        sma50 = _sma(closes, 50, i)
        sma200 = _sma(closes, 200, i)
        above_50 = price > sma50
        above_200 = price > sma200
        below_both = (not above_50) and (not above_200)
        cross, cross_days = _last_cross(closes)
        struct_code, struct_raw, tiny_hh = _structure(closes)
        golden_lost = (
            cross == "golden"
            and cross_days is not None
            and cross_days <= GOLDEN_LOST_DAYS
            and not above_50
        )
        range_mode = tiny_hh or struct_code in ("LH+HL", "range")
        if tiny_hh:
            struct_vis = "range"
        elif range_mode and struct_code == "LH+HL":
            struct_vis = "range (LH+HL)"
        else:
            struct_vis = struct_code

        parts: list[str] = []
        if above_50 and above_200:
            parts.append("Above 50d + 200d")
        elif below_both:
            parts.append("Below 50d + 200d")
        elif above_50:
            parts.append("Above 50d · below 200d")
        else:
            parts.append("Below 50d · above 200d")

        if golden_lost and cross_days is not None:
            parts.append(f"50/200 golden ~{cross_days}d then lost")
        elif cross == "death" and cross_days is not None and cross_days <= 60:
            parts.append(f"death ~{cross_days}d")
        elif sma50 < sma200:
            parts.append("50<200")
        elif sma50 > sma200 and above_50 and above_200:
            parts.append("50>200")

        parts.append(struct_vis)
        summary = " · ".join(parts)

        if venue == "spot":
            venue_line = f"Binance spot {symbol}"
        elif venue == "perp":
            venue_line = f"Binance perp {symbol} (no Binance spot) — perp SMA labelled"
        else:
            venue_line = "CoinGecko daily (no Binance NOS pair)"

        sma50_vs = "50>200" if sma50 > sma200 else "50<200"
        if below_both and sma50 > sma200:
            cross_note = (
                "50 still > 200 but price is below both — not a bullish golden cross."
            )
        elif golden_lost:
            cross_note = "Do not treat a failed golden cross as bullish."
        else:
            cross_note = sma50_vs

        detail = (
            f"{venue_line}. px {_px(price)} · 50d {_px(sma50)} · 200d {_px(sma200)}. "
            f"{cross_note} Structure last-60d vs prior-60d: {struct_raw}."
        )
        if tiny_hh:
            detail += " 60d HH is tiny — call range, not a new uptrend."

        state = "CLEAR" if above_50 and above_200 else "PARTIAL"
        out = {
            "ok": True,
            "state": state,
            "summary": summary,
            "detail": detail,
            "venue": venue,
            "symbol": symbol,
            "price": price,
            "sma50": sma50,
            "sma200": sma200,
            "above_50": above_50,
            "above_200": above_200,
            "cross": cross,
            "cross_days": cross_days,
            "structure": struct_vis,
        }
    except Exception as exc:
        out = {
            "ok": False,
            "state": "UNKNOWN",
            "summary": "50d/200d UNKNOWN",
            "detail": f"Technical fetch failed: {exc}",
            "venue": venue,
        }
    _CACHE[key] = out
    return out


def technical_trend_category(slug: str) -> dict[str, Any]:
    t = compute_sma_trend(slug)
    return category_state(
        "technical_trend",
        "TECHNICAL TREND",
        t["state"],
        summary=t["summary"],
        detail=t["detail"],
    )
