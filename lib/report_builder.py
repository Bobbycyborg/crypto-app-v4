"""Assemble report.json for Week 1."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lib.coinbase import fetch_btc_balance
from lib.cycles import analyse_btc
from lib.paths import CONFIG, REPORTS
from lib.prices import fetch_btc_dominance, fetch_prices
from lib.signals import colour_score, evaluate_signals
from lib.wallet import fetch_balances, load_assets_config


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _latest_prior_report(before_date: str) -> dict | None:
    if not REPORTS.exists():
        return None
    dates = sorted(d.name for d in REPORTS.iterdir() if d.is_dir() and d.name < before_date)
    if not dates:
        return None
    p = REPORTS / dates[-1] / "report.json"
    return json.loads(p.read_text()) if p.exists() else None


def _thesis_colour(signals: dict[str, dict], keys: list[str]) -> str:
    scores = [colour_score(signals[k]["colour"]) for k in keys if k in signals]
    if not scores:
        return "YELLOW"
    avg = sum(scores) / len(scores)
    if avg >= 1.6:
        return "GREEN"
    if avg <= 0.6:
        return "RED"
    return "YELLOW"


def _weekly_call(signals: dict, incomplete: bool) -> tuple[str, int, str, str]:
    if incomplete:
        return "WAIT", 0, "Data incomplete (BTC on Coinbase not connected). Hold.", "LOW"
    red_count = sum(1 for s in signals.values() if s["colour"] == "RED")
    green_count = sum(1 for s in signals.values() if s["colour"] == "GREEN")
    if red_count >= 4:
        return "WAIT", 0, "Multiple RULE signals red. No deployment.", "MEDIUM"
    if green_count >= 5 and signals["alt_breadth_30d"]["colour"] == "GREEN":
        return "DEPLOY_LIGHTLY", 62, "Breadth improving — light DCA only.", "MEDIUM"
    return "WAIT", 0, "Mixed evidence. Default hold.", "MEDIUM"


def _confidence(base: str, price_fallback: bool, incomplete: bool) -> str:
    if incomplete or price_fallback:
        return "LOW" if base == "LOW" else "MEDIUM" if base == "MEDIUM" else "MEDIUM"
    return base


def build_report(report_date: str | None = None, refresh_btc: bool = False) -> dict:
    from lib.btc_history import load_btc_daily

    now = datetime.now(timezone.utc)
    report_date = report_date or now.strftime("%Y-%m-%d")
    data_as_of = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    thesis_cfg = _load_json(CONFIG / "thesis.json")
    capital_cfg = _load_json(CONFIG / "capital.json")
    assets_cfg = load_assets_config()

    if thesis_cfg.get("thesis_start_date") is None:
        thesis_cfg["thesis_start_date"] = report_date
        thesis_cfg["thesis_deadline"] = (
            datetime.fromisoformat(report_date) + timedelta(days=thesis_cfg["thesis_window_days"])
        ).strftime("%Y-%m-%d")
        (CONFIG / "thesis.json").write_text(json.dumps(thesis_cfg, indent=2) + "\n")

    start = thesis_cfg["thesis_start_date"]
    deadline = thesis_cfg["thesis_deadline"]
    days_elapsed = (datetime.fromisoformat(report_date) - datetime.fromisoformat(start)).days + 1
    days_remaining = max(0, (datetime.fromisoformat(deadline) - datetime.fromisoformat(report_date)).days)

    prior = _latest_prior_report(report_date)

    balances = fetch_balances()
    coinbase = fetch_btc_balance()
    prices, price_sources = fetch_prices(report_date)
    dominance, dom_meta = fetch_btc_dominance()
    btc_rows, btc_meta = load_btc_daily(refresh=refresh_btc)
    cycle = analyse_btc(btc_rows)

    signals = evaluate_signals(cycle, prices, dom_meta, prior)
    incomplete_flags: list[str] = []
    if coinbase["status"] == "INCOMPLETE":
        incomplete_flags.append("btc_coinbase")

    holdings = []
    total_gbp = total_usd = 0.0
    for asset in assets_cfg["assets"]:
        sym = asset["symbol"]
        if sym == "BTC":
            holdings.append(
                {
                    "symbol": sym,
                    "balance": 0,
                    "price_gbp": prices.get("BTC", {}).get("gbp", 0),
                    "value_gbp": 0,
                    "pct_portfolio": 0,
                    "status": "INCOMPLETE",
                }
            )
            continue
        bal = balances.get(sym, 0.0)
        px = prices.get(sym, {})
        gbp = px.get("gbp", 0) * bal
        usd = px.get("usd", 0) * bal
        total_gbp += gbp
        total_usd += usd
        holdings.append(
            {
                "symbol": sym,
                "balance": round(bal, 6) if bal < 1000 else round(bal, 2),
                "price_gbp": round(px.get("gbp", 0), 4),
                "value_gbp": round(gbp, 2),
                "value_usd": round(usd, 2),
                "pct_portfolio": 0,
                "status": "ok",
            }
        )

    if total_gbp > 0:
        for h in holdings:
            if h["status"] == "ok":
                h["pct_portfolio"] = round(h["value_gbp"] / total_gbp * 100, 1)

    week_change = None
    if prior:
        prev_gbp = prior.get("portfolio", {}).get("total_gbp")
        if prev_gbp:
            week_change = round((total_gbp / prev_gbp - 1) * 100, 2)

    crypto_keys = ["btc_leg_fatigue", "btc_drawdown_365d", "btc_60d_momentum", "btc_four_year_position"]
    alt_keys = ["alt_breadth_7d", "alt_breadth_30d", "btc_dominance_trend"]
    crypto_colour = _thesis_colour(signals, crypto_keys)
    alt_colour = _thesis_colour(signals, alt_keys)

    call, deploy_gbp, summary, conf = _weekly_call(signals, bool(incomplete_flags))
    conf = _confidence(conf, price_sources.get("prices_fallback_used", False), bool(incomplete_flags))

    market = cycle["market"]
    outlook = cycle["outlook"]

    changes = []
    if prior:
        for sid, sig in signals.items():
            prev_c = sig.get("previous_colour")
            if prev_c and prev_c != sig["colour"]:
                changes.append(
                    {
                        "change": f"{sid} moved {prev_c} → {sig['colour']}",
                        "why_it_matters": sig["summary"],
                        "action_impact": "monitor",
                    }
                )
        if not changes:
            changes.append(
                {
                    "change": "Signal colours unchanged vs prior week",
                    "why_it_matters": "Thesis inputs stable.",
                    "action_impact": "none",
                }
            )
    else:
        changes = [
            {
                "change": "First V2 report — baseline week",
                "why_it_matters": "No prior report to compare.",
                "action_impact": "none",
            },
            {
                "change": f"Wallet mapped: {len([h for h in holdings if h['status']=='ok'])} tokens + SOL",
                "why_it_matters": "Matches assets.json.",
                "action_impact": "none",
            },
            {
                "change": f"BTC {market['current_leg']['dir']} leg day {market['current_leg']['days']}",
                "why_it_matters": signals["btc_leg_fatigue"]["summary"],
                "action_impact": "monitor",
            },
        ]

    counterarguments = [
        {
            "claim": "Major BTC bottom may be forming within the 150-day thesis window",
            "counter": "BTC could break prior lows on volume before reversal confirms",
            "severity": "high",
            "would_change_call_if": "BTC closes below recent swing low with rising volume",
        },
        {
            "claim": "Portfolio alts will participate when BTC stabilises",
            "counter": f"Only {signals['alt_breadth_30d']['summary'].split()[0]} alts beat BTC over 30d; dominance trend {signals['btc_dominance_trend']['colour']}",
            "severity": "medium",
            "would_change_call_if": "4+ portfolio alts outperform BTC over 30d for two consecutive weeks",
        },
    ]

    report = {
        "meta": {
            "report_date": report_date,
            "data_as_of": data_as_of,
            "version": "week1-v1",
            "thesis_start_date": start,
            "thesis_deadline": deadline,
            "days_remaining": days_remaining,
            "days_elapsed": days_elapsed,
            "incomplete_flags": incomplete_flags,
        },
        "portfolio": {
            "total_gbp": round(total_gbp, 2),
            "total_usd": round(total_usd, 2),
            "week_change_pct": week_change,
            "holdings": holdings,
            "btc_note": coinbase["note"] if incomplete_flags else None,
        },
        "capital": {
            "owned_gbp": round(total_gbp, 2),
            "borrowed_gbp": capital_cfg["borrowed_gbp"],
            "planned_monthly_deploy_gbp": capital_cfg["planned_monthly_deploy_gbp"],
            "profit_ladder_status": "NOT_YET_APPROVED",
        },
        "topline": {
            "headline": summary,
            "weekly_call": call,
            "deploy_gbp": deploy_gbp,
            "confidence": conf,
        },
        "signals": signals,
        "crypto_cycle_thesis": {
            "type": "JUDGEMENT",
            "colour": crypto_colour,
            "summary": (
                "Major bottom may be forming within the 150-day window."
                if crypto_colour != "RED"
                else "BTC cycle evidence weak — bottom not confirmed."
            ),
            "evidence": [signals[k]["summary"] for k in crypto_keys],
            "counterargument": counterarguments[0]["counter"],
            "confidence": conf,
            "days_remaining": days_remaining,
            "status": "deadline_review" if days_remaining <= 14 else "active",
        },
        "alt_cycle_thesis": {
            "type": "JUDGEMENT",
            "colour": alt_colour,
            "summary": (
                "Broad alt participation not yet visible."
                if alt_colour != "GREEN"
                else "Alts showing relative strength vs BTC."
            ),
            "evidence": [signals[k]["summary"] for k in alt_keys],
            "counterargument": counterarguments[1]["counter"],
            "confidence": conf if alt_colour == "RED" else "MEDIUM",
            "breadth_rule_colour": signals["alt_breadth_30d"]["colour"],
            "days_remaining": days_remaining,
            "status": "active",
        },
        "btc_cycle_evidence": {
            "btc_price_usd": market["btc_price_usd"],
            "current_leg_days": market["current_leg"]["days"],
            "current_leg_dir": market["current_leg"]["dir"],
            "median_leg_days": outlook["median_leg_days"],
            "pct_through_median": outlook["pct_through_median"],
            "from_high_365d_pct": market["from_high_365d_pct"],
            "hist_reversal_note": (
                f"{outlook['hist_reversal_rate_pct']}% of comparable late legs (n={outlook['late_leg_sample_n']}) "
                f"ended within 35% of median ({outlook['median_leg_days']}d). Not a forecast."
            ),
        },
        "changes": changes[:5],
        "counterarguments": counterarguments,
        "recommendation": {
            "call": call,
            "deploy_gbp": deploy_gbp,
            "summary": summary,
            "confidence": conf,
            "change_from_last_week": "new" if not prior else "same",
            "would_change_if": counterarguments[0]["would_change_call_if"],
            "actions": [
                f"Deploy £{deploy_gbp}. Hold all positions." if deploy_gbp == 0 else f"Deploy £{deploy_gbp} per plan.",
                "Add Coinbase read-only API key when ready (BTC currently INCOMPLETE)."
                if incomplete_flags
                else "Monitor RULE signals before changing deployment.",
                "Profit ladder: NOT YET APPROVED",
            ],
        },
        "predictions": [],
        "previous_week_review": None if not prior else {
            "prior_report_date": prior["meta"]["report_date"],
            "prior_call": prior["topline"]["weekly_call"],
            "prior_deploy_gbp": prior["topline"]["deploy_gbp"],
            "predictions_scored": [],
            "call_was_correct": "too_early",
        },
        "sources": {
            "wallet_rpc": "https://api.mainnet-beta.solana.com",
            "prices_primary": price_sources.get("prices_primary", "coingecko"),
            "prices_fallback_used": price_sources.get("prices_fallback_used", False),
            "btc_history": btc_meta.get("source", "btc-daily-close.json"),
            "btc_dominance": dominance,
            "fetched_at": {
                **price_sources.get("fetched_at", {}),
                "btc_history": btc_meta.get("fetched"),
            },
        },
    }
    return report
