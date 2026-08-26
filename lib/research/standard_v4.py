"""Standard V4 report builder — SOL, GRASS, memecoins, 2Z."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable, Literal

from lib.fetchers.asset_evidence import fetch_all_standard_evidence
from lib.fetchers.live_spot_price import resolve_spot_spec
from lib.paths import REPORTS
from lib.research.v4_common import (
    bottom_line,
    derive_call,
    price_display,
    price_window,
    signal_bottoming,
    signal_development,
    signal_dex_liquidity,
    signal_market_turnover,
    signal_network_unavailable,
    signal_speculative_risk,
    signal_token_economics,
    signal_trend,
    signal_vs_btc,
    what_changed,
)
from lib.wallet import fetch_balances

Profile = Literal["major", "depin", "memecoin", "infra"]


def _prior(slug: str, before_date: str) -> dict | None:
    if not REPORTS.exists():
        return None
    dates = sorted(
        d.name
        for d in REPORTS.iterdir()
        if d.is_dir() and d.name < before_date and (d / f"{slug}.json").exists()
    )
    if not dates:
        return None
    return json.loads((REPORTS / dates[-1] / f"{slug}.json").read_text())


ASSETS: dict[str, dict[str, Any]] = {
    "sol": {
        "symbol": "SOL",
        "coin_id": "solana",
        "mint": None,
        "binance_pair": "SOLUSDT",
        "site_url": "https://solana.com",
        "profile": "major",
        "dev_detail": "solana.com active; core L1 maintained publicly.",
        "source_sites": [("solana.com", "https://solana.com")],
        "bull_extra": "Core L1 exposure if alt cycle returns.",
        "bear_extra": "L1 does not guarantee SOL outperforms in risk-off periods.",
        "fails": "Sustained new lows + SOL/BTC weakens + turnover collapses.",
        "strengthens": "Higher highs/lows + SOL outperforms BTC 7d+ + rising market turnover.",
    },
    "grass": {
        "symbol": "GRASS",
        "coin_id": "grass",
        "mint": "Grass7B4RdKfBCjTKgSqnXkqjwiGvQyFbuSCUJr3XXjs",
        "site_url": "https://www.getgrass.io",
        "profile": "depin",
        "dev_detail": "getgrass.io active; bandwidth network product maintained publicly.",
        "source_sites": [("getgrass.io", "https://www.getgrass.io")],
        "bull_extra": "DePIN bandwidth narrative if usage scales.",
        "bear_extra": "Grass user growth does not guarantee token performance.",
        "fails": "Sustained new lows + GRASS/BTC weakens + no verified network growth.",
        "strengthens": "Higher highs/lows + GRASS outperforms BTC 7d+ + verified usage rising.",
    },
    "fartcoin": {
        "symbol": "FARTCOIN",
        "coin_id": "fartcoin",
        "mint": "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
        "site_url": None,
        "profile": "memecoin",
        "source_sites": [],
        "bull_extra": "Meme liquidity can return quickly in risk-on phases — size for total loss.",
        "bear_extra": "No fundamental thesis; liquidity can vanish in drawdowns.",
        "fails": "Liquidity thins + new lows + underperforms BTC for multiple weeks.",
        "strengthens": "Outperforms BTC 7d+ with stable DEX liquidity and higher lows.",
    },
    "spx6900": {
        "symbol": "SPX6900",
        "coin_id": "spx6900",
        "mint": "J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr",
        "site_url": None,
        "profile": "memecoin",
        "source_sites": [],
        "bull_extra": "Community/mindshare asset — only viable as small speculative sleeve.",
        "bear_extra": "Meme cycle may be over; no earnings or usage floor.",
        "fails": "Liquidity thins + new lows + underperforms BTC for multiple weeks.",
        "strengthens": "Outperforms BTC 7d+ with stable DEX liquidity and higher lows.",
    },
    "pump": {
        "symbol": "PUMP",
        "coin_id": "pump-fun",
        "mint": "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
        "site_url": "https://pump.fun",
        "profile": "memecoin",
        "dev_detail": "pump.fun active; launchpad revenue and buyback programme documented publicly.",
        "source_sites": [("pump.fun", "https://pump.fun")],
        "bull_extra": "Platform share + buyback/absorption narrative if speculative regime returns.",
        "bear_extra": "Token is not pure revenue capture; supply and holder flows dominate timing.",
        "fails": "Liquidity thins + new lows + underperforms BTC + platform share slips.",
        "strengthens": "Outperforms BTC 7d+ with stable DEX liquidity and absorption evidence.",
    },
}


def _extra_signals(
    profile: Profile,
    price_block: dict,
    evidence: dict,
    symbol: str,
    ath_pct: float | None,
    cfg: dict,
) -> list[dict]:
    site_ok = evidence.get("site_ok", False)

    if profile == "major":
        return [
            signal_market_turnover(price_block),
            signal_development(site_ok, cfg.get("dev_detail", "Project site checked.")),
        ]
    if profile == "memecoin":
        return [
            signal_dex_liquidity(evidence.get("dex_liquidity")),
            signal_speculative_risk(ath_pct, symbol),
        ]
    return [
        signal_network_unavailable(),
        signal_development(site_ok, cfg.get("dev_detail", "Project site checked.")),
    ]


def build_standard_report(slug: str, report_date: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    if slug not in ASSETS:
        raise ValueError(f"Unknown asset slug: {slug}")
    cfg = ASSETS[slug]
    symbol = cfg["symbol"]
    profile: Profile = cfg["profile"]

    report_date = report_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    spec = resolve_spot_spec(
        coin_id=cfg["coin_id"],
        symbol=cfg["symbol"],
        dex_mint=cfg.get("mint"),
        binance_pair=cfg.get("binance_pair"),
    )
    evidence = fetch_all_standard_evidence(
        spec["coin_id"],
        mint=cfg.get("mint"),
        site_url=cfg.get("site_url"),
        symbol=spec["symbol"],
        binance_pair=spec.get("binance_pair"),
    )
    fetched_at = evidence["fetched_at"]
    prior = _prior(slug, report_date)

    price_block = evidence.get("price")
    if not price_block:
        attempts = evidence.get("price_attempts") or []
        raise RuntimeError(
            f"No current price source available for {symbol} this run; attempts={attempts}"
        )

    price = float(price_block["price_usd"])
    ath = price_block.get("ath_usd")
    ath_pct = price_block.get("ath_change_pct")

    by_day = evidence.get("daily_prices") or {}
    recent_low, recent_high, ref_high = price_window(by_day, price)
    r7 = price_block.get("change_7d_pct")
    b7 = evidence.get("btc_7d_change_pct")

    balance = fetch_balances().get(symbol, 0)

    signals = [
        signal_trend(price, ath, ath_pct, ref_high),
        signal_bottoming(price, recent_low, recent_high),
        signal_vs_btc(r7, b7, symbol),
        *_extra_signals(profile, price_block, evidence, symbol, ath_pct, cfg),
        signal_token_economics(price_block),
    ]

    asset_call, confidence = derive_call(signals)
    if sum(1 for c in evidence["calls"] if not c.get("ok")) >= 2:
        confidence = "LOW"

    greens = [s for s in signals if s["colour"] == "GREEN"]
    memecoin_note = " Speculative — no adds." if profile == "memecoin" else ""

    sources = [
        {"name": f"Price — {price_block['source']}", "url": price_block["url"], "fetched_at": fetched_at},
        {"name": "Solana wallet", "url": "https://api.mainnet-beta.solana.com", "fetched_at": fetched_at},
    ]
    for name, url in cfg.get("source_sites", []):
        sources.insert(1, {"name": name, "url": url, "fetched_at": fetched_at})
    if profile == "memecoin" and evidence.get("dex_liquidity"):
        dex = evidence["dex_liquidity"]
        sources.insert(1, {"name": "DexScreener", "url": dex["url"], "fetched_at": fetched_at})

    report = {
        "asset": symbol,
        "template": "v4",
        "report_date": report_date,
        "report_date_display": datetime.strptime(report_date, "%Y-%m-%d").strftime("%d %B %Y").lstrip("0"),
        "price_usd": round(price, 6 if price < 0.01 else 4 if price < 1 else 2),
        "price_display": price_display(price),
        "holding_balance": round(balance, 6),
        "asset_call": asset_call,
        "confidence": confidence,
        "thesis_status": "ALIVE, UNCONFIRMED" if asset_call != "SELL" else "THESIS BROKEN",
        "bottom_line": bottom_line(signals, price, ath_pct, symbol) + memecoin_note,
        "signals": signals,
        "sources": sources,
        "what_changed": what_changed(prior, price, signals),
        "bull_case": (
            f"Green signals: {', '.join(s['name'] for s in greens) or 'none'}."
            + (f" {abs(ath_pct):.0f}% below ATH leaves upside if cycle turns." if ath_pct else "")
            + f" {cfg.get('bull_extra', '')}"
        ).strip(),
        "bear_case": (
            f"Red/orange signals dominate."
            + f" {cfg.get('bear_extra', '')}"
        ),
        "thesis_fails_if": cfg["fails"],
        "thesis_strengthens_if": cfg["strengthens"],
        "_signal_colours": {s["name"]: s["colour"] for s in signals},
        "_raw": {"profile": profile, "dex_liquidity": evidence.get("dex_liquidity")},
    }

    sources_file = {
        "asset": symbol,
        "report_date": report_date,
        "generated_at": fetched_at,
        "evidence": evidence,
        "report_snapshot": report,
    }
    return report, sources_file


def make_builder(slug: str) -> Callable[[str | None], tuple[dict[str, Any], dict[str, Any]]]:
    def _build(report_date: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        return build_standard_report(slug, report_date)

    return _build
