"""Port of V1 swing-leg and cycle math from build_dashboard.py JS."""

from __future__ import annotations

import statistics
from datetime import datetime
from typing import Any


def detect_legs(data: list[dict], pct: float = 0.05) -> list[dict]:
    if not data:
        return []
    legs: list[dict] = []
    direction = None
    start_idx = 0
    extreme = data[0]["close"]
    extreme_idx = 0

    for i in range(1, len(data)):
        px = data[i]["close"]
        if direction is None:
            if px > data[start_idx]["close"] * (1 + pct * 0.5):
                direction = "up"
                extreme = px
                extreme_idx = i
            elif px < data[start_idx]["close"] * (1 - pct * 0.5):
                direction = "down"
                extreme = px
                extreme_idx = i
            continue
        if direction == "up":
            if px >= extreme:
                extreme = px
                extreme_idx = i
            elif px <= extreme * (1 - pct):
                legs.append(_leg_row(data, start_idx, extreme_idx, "up"))
                direction = "down"
                start_idx = extreme_idx
                extreme = px
                extreme_idx = i
        else:
            if px <= extreme:
                extreme = px
                extreme_idx = i
            elif px >= extreme * (1 + pct):
                legs.append(_leg_row(data, start_idx, extreme_idx, "down"))
                direction = "up"
                start_idx = extreme_idx
                extreme = px
                extreme_idx = i

    last_idx = len(data) - 1
    legs.append(
        {
            **_leg_row(data, start_idx, last_idx, direction or "up"),
            "open": True,
        }
    )
    return legs


def _leg_row(data: list[dict], start_idx: int, end_idx: int, direction: str) -> dict:
    start_px = data[start_idx]["close"]
    end_px = data[end_idx]["close"]
    return {
        "startIdx": start_idx,
        "endIdx": end_idx,
        "dir": direction,
        "start": data[start_idx]["date"],
        "end": data[end_idx]["date"],
        "days": end_idx - start_idx + 1,
        "move": (end_px / start_px - 1) * 100,
    }


def find_major_lows(data: list[dict], window: int = 365) -> list[dict]:
    lows: list[dict] = []
    for i in range(window, len(data) - 30):
        px = data[i]["close"]
        is_low = True
        for j in range(i - window, i + window + 1):
            if j < 0 or j >= len(data) or j == i:
                continue
            if data[j]["close"] < px:
                is_low = False
                break
        if is_low:
            if not lows or i - lows[-1]["idx"] > 180:
                lows.append({"idx": i, "date": data[i]["date"], "close": px})
    return lows


def four_year_stats(data: list[dict], lows: list[dict]) -> dict:
    gaps = []
    for i in range(1, len(lows)):
        gaps.append(
            (datetime.fromisoformat(lows[i]["date"]) - datetime.fromisoformat(lows[i - 1]["date"])).days
        )
    last = lows[-1] if lows else None
    days_since = 0
    if last:
        days_since = (
            datetime.fromisoformat(data[-1]["date"]) - datetime.fromisoformat(last["date"])
        ).days
    return {
        "gaps": gaps,
        "avg_gap": statistics.mean(gaps) if gaps else 0,
        "days_since": days_since,
        "last_low": last,
    }


def statistical_outlook(data: list[dict], legs: list[dict], current: dict) -> dict:
    up_legs = [l for l in legs if l["dir"] == "up" and not l.get("open")]
    down_legs = [l for l in legs if l["dir"] == "down" and not l.get("open")]
    same_type = up_legs if current["dir"] == "up" else down_legs
    med = statistics.median([l["days"] for l in same_type]) if same_type else 30
    pct_through = current["days"] / med if med else 0

    late_ends = late_total = 0
    thresh = int(med * 0.75)
    for leg in same_type:
        if leg["days"] <= thresh:
            continue
        late_total += 1
        if leg["days"] <= med * 1.35:
            late_ends += 1
    hist_rev_rate = (late_ends / late_total * 100) if late_total else 50

    p_reversal = 20
    if pct_through >= 1.15:
        p_reversal = min(78, 42 + (pct_through - 1) * 35)
    elif pct_through >= 0.85:
        p_reversal = 28 + (pct_through - 0.85) * 45
    elif pct_through >= 0.6:
        p_reversal = 15 + (pct_through - 0.6) * 30
    p_reversal = round(p_reversal * 0.55 + hist_rev_rate * 0.45)
    p_reversal = max(12, min(82, p_reversal))

    samples = []
    for i in range(40, len(data) - 14):
        r20 = data[i]["close"] / data[i - 20]["close"] - 1
        d = "up" if r20 > 0.03 else "down" if r20 < -0.03 else None
        if d != current["dir"]:
            continue
        fwd = (data[i + 14]["close"] / data[i]["close"] - 1) * 100
        samples.append(fwd)

    return {
        "median_leg_days": round(med),
        "pct_through_median": round(pct_through, 2),
        "hist_reversal_rate_pct": round(hist_rev_rate),
        "comparable_sample_n": len(samples),
        "late_leg_sample_n": late_total,
        "p_reversal_30d_blend": p_reversal,
    }


def market_context(data: list[dict], current: dict, up_legs: list[dict], down_legs: list[dict]) -> dict:
    last = data[-1]
    d30, d60, d90 = data[-31], data[-61], data[-91]
    slice365 = data[-365:]
    typ_avg = (
        statistics.mean([l["days"] for l in up_legs])
        if current["dir"] == "up" and up_legs
        else statistics.mean([l["days"] for l in down_legs])
        if down_legs
        else 0
    )
    pct_through = current["days"] / typ_avg if typ_avg else 0
    high365 = max(d["close"] for d in slice365)
    low365 = min(d["close"] for d in slice365)
    return {
        "btc_price_usd": last["close"],
        "btc_date": last["date"],
        "current_leg": current,
        "pct_through_avg_leg": round(pct_through, 2),
        "return_30d_pct": round((last["close"] / d30["close"] - 1) * 100, 2),
        "return_60d_pct": round((last["close"] / d60["close"] - 1) * 100, 2),
        "return_90d_pct": round((last["close"] / d90["close"] - 1) * 100, 2),
        "from_high_365d_pct": round((last["close"] / high365 - 1) * 100, 2),
        "from_low_365d_pct": round((last["close"] / low365 - 1) * 100, 2),
        "high_365d": high365,
        "low_365d": low365,
    }


def analyse_btc(data: list[dict], reversal_pct: float = 0.05) -> dict[str, Any]:
    legs = detect_legs(data, reversal_pct)
    current = legs[-1]
    closed = [l for l in legs if not l.get("open")]
    up_legs = [l for l in closed if l["dir"] == "up"]
    down_legs = [l for l in closed if l["dir"] == "down"]
    lows = find_major_lows(data)
    ctx = market_context(data, current, up_legs, down_legs)
    outlook = statistical_outlook(data, legs, current)
    four_y = four_year_stats(data, lows)
    return {
        "legs": legs,
        "current_leg": current,
        "market": ctx,
        "outlook": outlook,
        "four_year": four_y,
        "major_lows": lows,
    }
