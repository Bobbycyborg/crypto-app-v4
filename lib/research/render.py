"""Build RENDER weekly report from fresh source fetches."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.fetchers.render_sources import fetch_all_render_evidence
from lib.paths import REPORTS
from lib.wallet import fetch_balances


def _prior_render(before_date: str) -> dict | None:
    if not REPORTS.exists():
        return None
    dates = sorted(
        d.name for d in REPORTS.iterdir() if d.is_dir() and d.name < before_date and (d / "render.json").exists()
    )
    if not dates:
        return None
    return json.loads((REPORTS / dates[-1] / "render.json").read_text())


def _colour_score(c: str) -> int:
    return {"GREEN": 2, "ORANGE": 1, "RED": 0}.get(c, 1)


def _derive_call(signals: list[dict]) -> tuple[str, str]:
    by_name = {s["name"]: s for s in signals}
    trend = by_name.get("Trend", {}).get("colour", "ORANGE")
    rs = by_name.get("vs BTC", {}).get("colour", "ORANGE")
    if trend == "RED" and rs == "RED":
        return "REDUCE", "LOW"
    if trend == "GREEN" and rs == "GREEN":
        return "BUY", "MEDIUM"
    return "HOLD", "MEDIUM"


def _bottom_line(signals: list[dict], price: float, ath_pct: float | None) -> str:
    reds = sum(1 for s in signals if s["colour"] == "RED")
    greens = sum(1 for s in signals if s["colour"] == "GREEN")
    ath_bit = f"{abs(ath_pct):.0f}% below ATH" if ath_pct is not None else "ATH data unavailable"
    if greens >= 2 and reds >= 2:
        return (
            f"At ${price:.2f}, {ath_bit} — network/fundamental signals green but "
            f"price and relative strength remain weak; no case for new capital."
        )
    if reds >= 3:
        return f"At ${price:.2f}, {ath_bit} — majority of signals negative; hold only, no adds."
    return f"At ${price:.2f}, {ath_bit} — mixed evidence; maintain position, no deployment."


def _what_changed(prior: dict | None, price: float, signals: list[dict], frames: int | None) -> str:
    if not prior:
        return f"First weekly RENDER report. Price ${price:.2f}. Baseline recorded for next week."
    parts = []
    old_p = prior.get("price_usd")
    if old_p and old_p != price:
        parts.append(f"Price moved ${old_p:.2f} → ${price:.2f}.")
    old_frames = (prior.get("_raw") or {}).get("frames_rendered")
    if frames and old_frames and frames != old_frames:
        parts.append(f"Frames rendered: {old_frames:,} → {frames:,}.")
    for s in signals:
        prev = prior.get("_signal_colours", {}).get(s["name"])
        if prev and prev != s["colour"]:
            parts.append(f"{s['name']} signal: {prev} → {s['colour']}.")
    return " ".join(parts) if parts else "No material change vs prior week on tracked metrics."


def build_render_report(report_date: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    report_date = report_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evidence = fetch_all_render_evidence()
    fetched_at = evidence["fetched_at"]
    prior = _prior_render(report_date)

    price_block = evidence.get("price")
    if not price_block:
        raise RuntimeError("No price source available for RENDER this run")
    price = float(price_block["price_usd"])
    ath = price_block.get("ath_usd")
    ath_pct = price_block.get("ath_change_pct")

    by_day = evidence.get("daily_prices") or {}
    if by_day:
        recent = sorted(by_day)[-14:]
        recent_low = min(by_day[d] for d in recent)
        recent_high = max(by_day[d] for d in recent)
        peak_date = max(by_day, key=lambda d: by_day[d] if d in recent else 0)
        ref_high = by_day.get(peak_date, recent_high)
    else:
        recent_low = recent_high = ref_high = price

    r7 = price_block.get("change_7d_pct")
    b7 = evidence.get("btc_7d_change_pct")
    rs_pp = (float(r7) - float(b7)) if r7 is not None and b7 is not None else None

    foundation = evidence.get("foundation") or {}
    frames = foundation.get("frames_rendered")
    nodes = foundation.get("nodes_total")
    burned = foundation.get("cumulative_burned")

    balance = fetch_balances().get("RENDER", 0)

    signals: list[dict] = []

    # Trend — RULE
    if ath_pct is not None and ath_pct < -50:
        trend_colour = "RED"
        trend_ev = f"${price:.2f} now · {abs(ath_pct):.0f}% below ATH (${ath:.2f})."
    elif by_day and price < ref_high * 0.95:
        trend_colour = "RED"
        trend_ev = f"Down from ${ref_high:.2f} recent high to ${price:.2f}."
    else:
        trend_colour = "ORANGE"
        trend_ev = f"Price ${price:.2f}; no clear uptrend on 14d window."
    signals.append({"name": "Trend", "colour": trend_colour, "evidence": trend_ev, "type": "RULE"})

    # Bottoming — JUDGEMENT from price range
    range_pct = (recent_high - recent_low) / recent_high * 100 if recent_high else 0
    if range_pct < 8 and price > recent_low * 1.02:
        bot_c, bot_e = "ORANGE", f"Trading ${recent_low:.2f}–${recent_high:.2f} ({range_pct:.0f}% range); no confirmed reversal."
    elif price <= recent_low * 1.01:
        bot_c, bot_e = "RED", f"At/near 14d low ${recent_low:.2f}; no base confirmed."
    else:
        bot_c, bot_e = "ORANGE", f"14d range ${recent_low:.2f}–${recent_high:.2f}; structure unconfirmed."
    signals.append({"name": "Bottoming", "colour": bot_c, "evidence": bot_e, "type": "JUDGEMENT"})

    # vs BTC — RULE
    if rs_pp is None:
        rs_c, rs_e = "ORANGE", "7d relative performance vs BTC: data unavailable — excluded from decision."
    elif rs_pp < -3:
        rs_c, rs_e = "RED", f"Underperformed BTC by {abs(rs_pp):.1f}pp over 7d (RENDER {r7:+.1f}% vs BTC {b7:+.1f}%)."
    elif rs_pp > 3:
        rs_c, rs_e = "GREEN", f"Outperformed BTC by {rs_pp:.1f}pp over 7d."
    else:
        rs_c, rs_e = "ORANGE", f"Near parity with BTC over 7d ({rs_pp:+.1f}pp)."
    signals.append({"name": "vs BTC", "colour": rs_c, "evidence": rs_e, "type": "RULE"})

    # Network — RULE from foundation scrape
    if frames and nodes and frames > 1_000_000:
        net_e = f"Foundation dashboard: {frames:,} frames rendered, {nodes:,} nodes since inception."
        net_c = "GREEN"
    elif frames:
        net_e = "Foundation dashboard metrics failed validation this run — excluded from decision."
        net_c = "ORANGE"
    else:
        net_e = "Foundation dashboard unreachable this run — network metrics excluded."
        net_c = "ORANGE"
    signals.append({"name": "Network usage", "colour": net_c, "evidence": net_e, "type": "RULE"})

    # Development — JUDGEMENT from Foundation / public roadmap cues
    if foundation and foundation.get("raw_length", 0) > 1000:
        dev_e = "Foundation dashboard active; Dispersed GPU roadmap (RNP-009) and BME burn programme documented publicly."
        dev_c = "GREEN"
    else:
        dev_e = "Development status not retrieved this run — excluded from decision."
        dev_c = "ORANGE"
    signals.append({"name": "Development", "colour": dev_c, "evidence": dev_e, "type": "JUDGEMENT"})

    # Token economics — from burned if scraped
    if burned and burned > 1000:
        tok_e = f"Cumulative burned (dashboard): {burned:,} RENDER; emissions schedule still active."
        tok_c = "ORANGE"
    else:
        tok_e = "Burn/mint stats not retrieved this run — token economics signal excluded."
        tok_c = "ORANGE"
    signals.append({"name": "Token economics", "colour": tok_c, "evidence": tok_e, "type": "RULE"})

    asset_call, confidence = _derive_call(signals)
    if evidence["calls"] and sum(1 for c in evidence["calls"] if not c.get("ok")) >= 2:
        confidence = "LOW"

    greens = [s for s in signals if s["colour"] == "GREEN"]
    reds = [s for s in signals if s["colour"] == "RED"]

    report = {
        "asset": "RENDER",
        "template": "v4",
        "report_date": report_date,
        "report_date_display": datetime.strptime(report_date, "%Y-%m-%d").strftime("%d %B %Y").lstrip("0"),
        "price_usd": round(price, 2),
        "price_display": f"~${price:.2f}",
        "holding_balance": round(balance, 6),
        "asset_call": asset_call,
        "confidence": confidence,
        "thesis_status": "ALIVE, UNCONFIRMED" if asset_call != "SELL" else "THESIS BROKEN",
        "bottom_line": _bottom_line(signals, price, ath_pct),
        "signals": signals,
        "sources": [
            {"name": f"Price — {price_block['source']}", "url": price_block["url"], "fetched_at": fetched_at},
            {"name": "Render Foundation dashboard", "url": "https://stats.renderfoundation.com/", "fetched_at": fetched_at},
            {"name": "Solana wallet", "url": "https://api.mainnet-beta.solana.com", "fetched_at": fetched_at},
        ],
        "what_changed": _what_changed(prior, price, signals, frames),
        "bull_case": (
            f"Green signals: {', '.join(s['name'] for s in greens) or 'none'}."
            + (f" Network at {frames:,} frames." if frames else "")
            + (f" Price {abs(ath_pct):.0f}% below ATH leaves upside if cycle turns." if ath_pct else "")
        ),
        "bear_case": (
            f"Red/orange signals: {', '.join(s['name'] for s in signals if s['colour'] in ('RED', 'ORANGE'))}."
            + " Network success does not guarantee token performance."
        ),
        "thesis_fails_if": "Sustained new lows + RENDER/BTC continues weakening + network frames stall week-on-week.",
        "thesis_strengthens_if": "Higher highs/lows + RENDER outperforms BTC 7d+ + frames rendered accelerating vs prior week.",
        "_signal_colours": {s["name"]: s["colour"] for s in signals},
        "_raw": {
            "frames_rendered": frames,
            "nodes": nodes,
            "cumulative_burned": burned,
            "rs_pp_7d": rs_pp,
        },
    }

    sources_file = {
        "asset": "RENDER",
        "report_date": report_date,
        "generated_at": fetched_at,
        "evidence": evidence,
        "report_snapshot": report,
    }
    return report, sources_file
