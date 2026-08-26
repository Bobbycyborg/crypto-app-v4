"""Build IO weekly report from fresh source fetches."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from lib.fetchers.io_sources import fetch_all_io_evidence
from lib.paths import REPORTS
from lib.research.v4_common import (
    bottom_line,
    derive_call,
    price_window,
    signal_bottoming,
    signal_development,
    signal_network_unavailable,
    signal_token_economics,
    signal_trend,
    signal_vs_btc,
    what_changed,
)
from lib.wallet import fetch_balances


def _prior_io(before_date: str) -> dict | None:
    if not REPORTS.exists():
        return None
    dates = sorted(
        d.name for d in REPORTS.iterdir() if d.is_dir() and d.name < before_date and (d / "io.json").exists()
    )
    if not dates:
        return None
    return json.loads((REPORTS / dates[-1] / "io.json").read_text())


def build_io_report(report_date: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    report_date = report_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evidence = fetch_all_io_evidence()
    fetched_at = evidence["fetched_at"]
    prior = _prior_io(report_date)

    price_block = evidence.get("price")
    if not price_block:
        raise RuntimeError("No price source available for IO this run")
    price = float(price_block["price_usd"])
    ath = price_block.get("ath_usd")
    ath_pct = price_block.get("ath_change_pct")

    by_day = evidence.get("daily_prices") or {}
    recent_low, recent_high, ref_high = price_window(by_day, price)
    r7 = price_block.get("change_7d_pct")
    b7 = evidence.get("btc_7d_change_pct")
    rs_pp = (float(r7) - float(b7)) if r7 is not None and b7 is not None else None

    balance = fetch_balances().get("IO", 0)

    signals = [
        signal_trend(price, ath, ath_pct, ref_high),
        signal_bottoming(price, recent_low, recent_high),
        signal_vs_btc(r7, b7, "IO"),
        signal_network_unavailable(),
        signal_development(
            evidence.get("site_io_net", False),
            "io.net active; IO Cloud and Explorer product surfaces maintained publicly.",
        ),
        signal_token_economics(price_block),
    ]

    asset_call, confidence = derive_call(signals)
    if sum(1 for c in evidence["calls"] if not c.get("ok")) >= 2:
        confidence = "LOW"

    greens = [s for s in signals if s["colour"] == "GREEN"]
    reds = [s for s in signals if s["colour"] == "RED"]

    report = {
        "asset": "IO",
        "template": "v4",
        "report_date": report_date,
        "report_date_display": datetime.strptime(report_date, "%Y-%m-%d").strftime("%d %B %Y").lstrip("0"),
        "price_usd": round(price, 4 if price < 1 else 2),
        "price_display": f"~${price:.2f}" if price >= 0.1 else f"~${price:.4f}",
        "holding_balance": round(balance, 6),
        "asset_call": asset_call,
        "confidence": confidence,
        "thesis_status": "ALIVE, UNCONFIRMED" if asset_call != "SELL" else "THESIS BROKEN",
        "bottom_line": bottom_line(signals, price, ath_pct, "IO"),
        "signals": signals,
        "sources": [
            {"name": f"Price — {price_block['source']}", "url": price_block["url"], "fetched_at": fetched_at},
            {"name": "io.net", "url": "https://io.net", "fetched_at": fetched_at},
            {"name": "Solana wallet", "url": "https://api.mainnet-beta.solana.com", "fetched_at": fetched_at},
        ],
        "what_changed": what_changed(prior, price, signals),
        "bull_case": (
            f"Green signals: {', '.join(s['name'] for s in greens) or 'none'}."
            + (f" DePIN GPU narrative intact at {abs(ath_pct):.0f}% below ATH." if ath_pct else "")
        ),
        "bear_case": (
            f"Red/orange signals: {', '.join(s['name'] for s in signals if s['colour'] in ('RED', 'ORANGE'))}."
            + " Compute demand does not guarantee token performance."
        ),
        "thesis_fails_if": "Sustained new lows + IO/BTC weakens + no verified network utilisation recovery.",
        "thesis_strengthens_if": "Higher highs/lows + IO outperforms BTC 7d+ + authenticated network metrics show rising GPU hire.",
        "_signal_colours": {s["name"]: s["colour"] for s in signals},
        "_raw": {"rs_pp_7d": rs_pp, "network_metrics": evidence.get("network_metrics")},
    }

    sources_file = {
        "asset": "IO",
        "report_date": report_date,
        "generated_at": fetched_at,
        "evidence": evidence,
        "report_snapshot": report,
    }
    return report, sources_file
