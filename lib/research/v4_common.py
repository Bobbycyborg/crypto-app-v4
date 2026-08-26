"""Shared V4 report helpers — trend, bottoming, vs BTC, call logic."""

from __future__ import annotations

from typing import Any


def fmt_usd(price: float) -> str:
    if price >= 100:
        return f"${price:.0f}"
    if price >= 1:
        return f"${price:.2f}"
    if price >= 0.01:
        return f"${price:.3f}"
    return f"${price:.4f}"


def price_display(price: float) -> str:
    if price >= 0.1:
        return f"~${price:.2f}"
    if price >= 0.01:
        return f"~${price:.3f}"
    return f"~${price:.4f}"


def price_window(by_day: dict[str, float], price: float) -> tuple[float, float, float]:
    if not by_day:
        return price, price, price
    recent = sorted(by_day)[-14:]
    recent_low = min(by_day[d] for d in recent)
    recent_high = max(by_day[d] for d in recent)
    peak_date = max(recent, key=lambda d: by_day[d])
    ref_high = by_day.get(peak_date, recent_high)
    return recent_low, recent_high, ref_high


def signal_trend(price: float, ath: float | None, ath_pct: float | None, ref_high: float) -> dict:
    px = fmt_usd(price)
    if ath_pct is not None and ath_pct < -50:
        return {
            "name": "Trend",
            "colour": "RED",
            "evidence": f"{px} now · {abs(ath_pct):.0f}% below ATH ({fmt_usd(ath)})." if ath else f"{px} now · {abs(ath_pct):.0f}% below ATH.",
            "type": "RULE",
        }
    if ref_high and price < ref_high * 0.95:
        return {
            "name": "Trend",
            "colour": "RED",
            "evidence": f"Down from {fmt_usd(ref_high)} recent high to {px}.",
            "type": "RULE",
        }
    return {
        "name": "Trend",
        "colour": "ORANGE",
        "evidence": f"Price {px}; no clear uptrend on 14d window.",
        "type": "RULE",
    }


def signal_bottoming(price: float, recent_low: float, recent_high: float) -> dict:
    if not recent_high:
        return {
            "name": "Bottoming",
            "colour": "ORANGE",
            "evidence": "14d price window unavailable — excluded from decision.",
            "type": "JUDGEMENT",
        }
    range_pct = (recent_high - recent_low) / recent_high * 100 if recent_high else 0
    if range_pct < 8 and price > recent_low * 1.02:
        ev = (
            f"Trading {fmt_usd(recent_low)}–{fmt_usd(recent_high)} ({range_pct:.0f}% range); "
            f"no confirmed reversal."
        )
        return {"name": "Bottoming", "colour": "ORANGE", "evidence": ev, "type": "JUDGEMENT"}
    if price <= recent_low * 1.01:
        return {
            "name": "Bottoming",
            "colour": "RED",
            "evidence": f"At/near 14d low {fmt_usd(recent_low)}; no base confirmed.",
            "type": "JUDGEMENT",
        }
    return {
        "name": "Bottoming",
        "colour": "ORANGE",
        "evidence": f"14d range {fmt_usd(recent_low)}–{fmt_usd(recent_high)}; structure unconfirmed.",
        "type": "JUDGEMENT",
    }


def signal_vs_btc(r7: float | None, b7: float | None, asset_symbol: str) -> dict:
    rs_pp = (float(r7) - float(b7)) if r7 is not None and b7 is not None else None
    if rs_pp is None:
        return {
            "name": "vs BTC",
            "colour": "ORANGE",
            "evidence": "7d relative performance vs BTC: data unavailable — excluded from decision.",
            "type": "RULE",
        }
    if rs_pp < -3:
        return {
            "name": "vs BTC",
            "colour": "RED",
            "evidence": (
                f"Underperformed BTC by {abs(rs_pp):.1f}pp over 7d "
                f"({asset_symbol} {r7:+.1f}% vs BTC {b7:+.1f}%)."
            ),
            "type": "RULE",
        }
    if rs_pp > 3:
        return {
            "name": "vs BTC",
            "colour": "GREEN",
            "evidence": f"Outperformed BTC by {rs_pp:.1f}pp over 7d.",
            "type": "RULE",
        }
    return {
        "name": "vs BTC",
        "colour": "ORANGE",
        "evidence": f"Near parity with BTC over 7d ({rs_pp:+.1f}pp).",
        "type": "RULE",
    }


def signal_token_economics(price_block: dict[str, Any]) -> dict:
    circ = price_block.get("circulating_supply")
    total = price_block.get("total_supply") or price_block.get("max_supply")
    mcap = price_block.get("market_cap_usd")
    fdv = price_block.get("fdv_usd")

    if not circ or not total:
        return {
            "name": "Token economics",
            "colour": "ORANGE",
            "evidence": "Supply stats not retrieved this run — token economics excluded.",
            "type": "RULE",
        }

    pct_circ = circ / total * 100 if total else 0
    mcap_s = f"${mcap/1e6:.0f}M mcap" if mcap else "mcap n/a"
    fdv_s = f"${fdv/1e6:.0f}M FDV" if fdv else "FDV n/a"
    dilution = fdv / mcap if fdv and mcap and mcap > 0 else None

    if pct_circ < 50 or (dilution and dilution > 3):
        colour = "RED"
    elif pct_circ < 75 or (dilution and dilution > 1.8):
        colour = "ORANGE"
    else:
        colour = "ORANGE"

    ev = (
        f"{pct_circ:.0f}% of supply circulating ({circ/1e6:.1f}M / {total/1e6:.1f}M); "
        f"{mcap_s} · {fdv_s}."
    )
    return {"name": "Token economics", "colour": colour, "evidence": ev, "type": "RULE"}


def signal_market_turnover(price_block: dict[str, Any]) -> dict:
    vol = price_block.get("total_volume_usd")
    mcap = price_block.get("market_cap_usd")
    if not vol or not mcap:
        return signal_network_unavailable()
    ratio = vol / mcap
    if ratio >= 0.12:
        colour = "GREEN"
    elif ratio >= 0.04:
        colour = "ORANGE"
    else:
        colour = "RED"
    return {
        "name": "Market liquidity",
        "colour": colour,
        "evidence": (
            f"24h volume ${vol/1e6:.0f}M vs ${mcap/1e6:.0f}M mcap "
            f"({ratio*100:.0f}% turnover)."
        ),
        "type": "RULE",
    }


def signal_dex_liquidity(dex: dict[str, Any] | None) -> dict:
    if not dex or not dex.get("liquidity_usd"):
        return {
            "name": "Liquidity",
            "colour": "ORANGE",
            "evidence": "DEX liquidity data unavailable this run — excluded.",
            "type": "RULE",
        }
    liq = float(dex["liquidity_usd"])
    vol = float(dex.get("volume_24h_usd") or 0)
    if liq >= 5_000_000:
        colour = "GREEN"
    elif liq >= 500_000:
        colour = "ORANGE"
    else:
        colour = "RED"
    vol_s = f" · 24h vol ${vol/1e6:.1f}M" if vol else ""
    return {
        "name": "Liquidity",
        "colour": colour,
        "evidence": f"Top Solana pair liquidity ${liq/1e6:.1f}M{vol_s} (DexScreener).",
        "type": "RULE",
    }


def signal_speculative_risk(ath_pct: float | None, asset: str) -> dict:
    if ath_pct is None:
        return {
            "name": "Speculative risk",
            "colour": "ORANGE",
            "evidence": f"{asset} labelled speculative — ATH drawdown data unavailable.",
            "type": "JUDGEMENT",
        }
    draw = abs(ath_pct)
    if draw >= 80:
        colour = "RED"
    elif draw >= 50:
        colour = "ORANGE"
    else:
        colour = "ORANGE"
    return {
        "name": "Speculative risk",
        "colour": colour,
        "evidence": (
            f"Speculative asset — {draw:.0f}% below ATH; no revenue/fundamental thesis. "
            f"Position size should reflect total-loss risk."
        ),
        "type": "JUDGEMENT",
    }


def signal_network_unavailable() -> dict:
    return {
        "name": "Network usage",
        "colour": "ORANGE",
        "evidence": "Network utilisation data unavailable from free sources this run — excluded.",
        "type": "RULE",
    }


def signal_development(site_ok: bool, detail: str) -> dict:
    if site_ok:
        return {"name": "Development", "colour": "GREEN", "evidence": detail, "type": "JUDGEMENT"}
    return {
        "name": "Development",
        "colour": "ORANGE",
        "evidence": "Project site unreachable this run — development signal excluded.",
        "type": "JUDGEMENT",
    }


def derive_call(signals: list[dict]) -> tuple[str, str]:
    by_name = {s["name"]: s for s in signals}
    trend = by_name.get("Trend", {}).get("colour", "ORANGE")
    rs = by_name.get("vs BTC", {}).get("colour", "ORANGE")
    if trend == "RED" and rs == "RED":
        return "REDUCE", "LOW"
    if trend == "GREEN" and rs == "GREEN":
        return "BUY", "MEDIUM"
    return "HOLD", "MEDIUM"


def bottom_line(signals: list[dict], price: float, ath_pct: float | None, asset: str) -> str:
    reds = sum(1 for s in signals if s["colour"] == "RED")
    greens = sum(1 for s in signals if s["colour"] == "GREEN")
    px = fmt_usd(price)
    ath_bit = f"{abs(ath_pct):.0f}% below ATH" if ath_pct is not None else "ATH data unavailable"
    if greens >= 2 and reds >= 2:
        return (
            f"At {px}, {ath_bit} — {asset} fundamentals mixed vs weak price; "
            f"no case for new capital."
        )
    if reds >= 3:
        return f"At {px}, {ath_bit} — majority of signals negative; hold only, no adds."
    return f"At {px}, {ath_bit} — mixed evidence; maintain position, no deployment."


def what_changed(
    prior: dict | None,
    price: float,
    signals: list[dict],
    *,
    extra_checks: list[tuple[str, Any, Any]] | None = None,
) -> str:
    if not prior:
        return f"First weekly report. Price {fmt_usd(price)}. Baseline recorded for next week."
    parts = []
    old_p = prior.get("price_usd")
    if old_p and old_p != price:
        parts.append(f"Price moved {fmt_usd(old_p)} → {fmt_usd(price)}.")
    for label, old_v, new_v in extra_checks or []:
        if old_v is not None and new_v is not None and old_v != new_v:
            parts.append(f"{label}: {old_v} → {new_v}.")
    for s in signals:
        prev = prior.get("_signal_colours", {}).get(s["name"])
        if prev and prev != s["colour"]:
            parts.append(f"{s['name']} signal: {prev} → {s['colour']}.")
    return " ".join(parts) if parts else "No material change vs prior week on tracked metrics."
