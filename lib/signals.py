"""RULE signal evaluation from prices + cycle context."""

from __future__ import annotations

import json
from typing import Any

from lib.paths import CONFIG


def _load_thresholds() -> dict:
    return json.loads((CONFIG / "thresholds.json").read_text())


def _colour_leg_fatigue(pct_through: float, t: dict) -> str:
    if pct_through > t["leg_fatigue_stretched"]:
        return "RED"
    if pct_through >= t["leg_fatigue_maturing"]:
        return "YELLOW"
    if pct_through < t["leg_fatigue_early"]:
        return "GREEN"
    return "YELLOW"


def _colour_drawdown(from_high_pct: float, t: dict) -> str:
    if from_high_pct < t["drawdown_deep_pct"]:
        return "RED"
    if from_high_pct < t["drawdown_moderate_pct"]:
        return "YELLOW"
    return "GREEN"


def _colour_momentum(ret_60d: float) -> str:
    if ret_60d > 0.5:
        return "GREEN"
    if ret_60d < -0.5:
        return "RED"
    return "YELLOW"


def _colour_four_year(days_since: int, t: dict) -> str:
    window = t["four_year_low_window_days"]
    if 0.75 * window <= days_since <= 1.25 * window:
        return "GREEN"
    if 0.5 * window <= days_since <= 1.5 * window:
        return "YELLOW"
    return "RED"


def _breadth_colour(count: int, green_min: int, yellow_min: int) -> str:
    if count >= green_min:
        return "GREEN"
    if count >= yellow_min:
        return "YELLOW"
    return "RED"


def _outperform_count(prices: dict[str, dict], symbols: list[str], field: str) -> int:
    btc = prices.get("BTC", {}).get(field)
    if btc is None:
        return 0
    n = 0
    for sym in symbols:
        chg = prices.get(sym, {}).get(field)
        if chg is not None and chg > btc:
            n += 1
    return n


def evaluate_signals(
    cycle: dict[str, Any],
    prices: dict[str, dict],
    dominance_meta: dict,
    previous: dict | None = None,
) -> dict[str, dict]:
    t = _load_thresholds()
    bc = t["btc_cycle"]
    ab = t["alt_breadth"]
    dom_t = t["btc_dominance"]
    market = cycle["market"]
    outlook = cycle["outlook"]
    four_y = cycle["four_year"]

    same_type = [l for l in cycle["legs"] if l["dir"] == market["current_leg"]["dir"] and not l.get("open")]
    med = outlook["median_leg_days"]
    pct = market["current_leg"]["days"] / med if med else 0

    prev_signals = (previous or {}).get("signals", {})
    alt_symbols = ab["portfolio_assets_counted"]

    breadth_7 = _outperform_count(prices, alt_symbols, "change_7d_pct")
    breadth_30 = _outperform_count(prices, alt_symbols, "change_30d_pct")

    dom_chg = dominance_meta.get("change_7d_pct")
    if dom_chg is None:
        dom_colour = "YELLOW"
        dom_detail = "No prior dominance baseline — flat assumed."
    elif dom_chg >= dom_t["rising_7d_pct"]:
        dom_colour = "RED"
        dom_detail = f"BTC dominance rose {dom_chg:+.2f} pts over cached baseline."
    elif dom_chg <= dom_t["falling_7d_pct"]:
        dom_colour = "GREEN"
        dom_detail = f"BTC dominance fell {dom_chg:+.2f} pts over cached baseline."
    else:
        dom_colour = "YELLOW"
        dom_detail = f"BTC dominance change {dom_chg:+.2f} pts — within flat band."

    defs = {
        "btc_leg_fatigue": {
            "colour": _colour_leg_fatigue(pct, bc),
            "summary": f"Current {market['current_leg']['dir']} leg is {market['current_leg']['days']}d ({pct:.0%} of median {med}d).",
            "detail": f"Thresholds: GREEN <{bc['leg_fatigue_early']:.0%} · YELLOW to {bc['leg_fatigue_stretched']:.0%} · RED above.",
            "source": "btc-daily-close.json swing-leg detection",
        },
        "btc_drawdown_365d": {
            "colour": _colour_drawdown(market["from_high_365d_pct"], bc),
            "summary": f"BTC {market['from_high_365d_pct']:+.1f}% from 365d high (${market['high_365d']:,.0f}).",
            "detail": f"365d range ${market['low_365d']:,.0f} – ${market['high_365d']:,.0f}.",
            "source": "btc-daily-close.json",
        },
        "btc_60d_momentum": {
            "colour": _colour_momentum(market["return_60d_pct"]),
            "summary": f"60d return {market['return_60d_pct']:+.1f}%.",
            "detail": f"30d {market['return_30d_pct']:+.1f}% · 90d {market['return_90d_pct']:+.1f}%.",
            "source": "btc-daily-close.json",
        },
        "btc_four_year_position": {
            "colour": _colour_four_year(int(four_y["days_since"]), bc),
            "summary": f"{int(four_y['days_since'])} days since last major low.",
            "detail": f"Target window ~{bc['four_year_low_window_days']}d from prior cycle low.",
            "source": "btc-daily-close.json major-low detection",
        },
        "alt_breadth_7d": {
            "colour": _breadth_colour(breadth_7, ab["outperform_7d_green_count"], ab["outperform_7d_yellow_count"]),
            "summary": f"{breadth_7} of {len(alt_symbols)} portfolio alts beat BTC over 7d.",
            "detail": "CoinGecko 7d change vs BTC. Missing changes count as not outperforming.",
            "source": "coingecko simple/price",
        },
        "alt_breadth_30d": {
            "colour": _breadth_colour(breadth_30, ab["outperform_30d_green_count"], ab["outperform_30d_yellow_count"]),
            "summary": f"{breadth_30} of {len(alt_symbols)} portfolio alts beat BTC over 30d.",
            "detail": "CoinGecko 30d change vs BTC.",
            "source": "coingecko simple/price",
        },
        "btc_dominance_trend": {
            "colour": dom_colour,
            "summary": dom_detail,
            "detail": f"Current dominance {dominance_meta.get('dominance', 'n/a')}%.",
            "source": "coingecko /global",
        },
    }

    signals: dict[str, dict] = {}
    for sid, body in defs.items():
        prev_c = prev_signals.get(sid, {}).get("colour")
        signals[sid] = {
            "id": sid,
            "type": "RULE",
            "colour": body["colour"],
            "summary": body["summary"],
            "detail": body["detail"],
            "source": body["source"],
            "confidence": "HIGH",
            "previous_colour": prev_c,
        }
    return signals


def colour_score(colour: str) -> int:
    return {"GREEN": 2, "YELLOW": 1, "RED": 0}.get(colour, 1)
