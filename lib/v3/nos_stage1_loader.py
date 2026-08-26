"""Canonical NOS Stage-1 evidence loader — packs only, no silent fallbacks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.paths import REPORTS

STAGE1 = REPORTS / "nos-forensics" / "stage1-evidence"
RAW = STAGE1 / "raw"

STANCE_HEADLINE = "NETWORK ACTIVE · RAIL REAL · TAPE WEAK"
SUPPLY_READ = "NEAR FULLY CIRCULATING · LIVE EMISSION PRESSURE UNKNOWN"


class NosEvidenceError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path, label: str) -> Any:
    data = _load(path)
    if data is None:
        raise NosEvidenceError(f"Missing required NOS evidence: {label} ({path})")
    return data


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip().replace(",", "").replace("%", "").replace("+", ""))
    except ValueError:
        return None


def _metric_map(table: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for row in table.get("metrics") or []:
        if isinstance(row, dict) and row.get("metric"):
            out[str(row["metric"])] = row
    return out


def load_nos_canonical() -> dict[str, Any]:
    evidence_table = _require(STAGE1 / "nos-evidence-table.json", "evidence table")
    metrics = _metric_map(evidence_table if isinstance(evidence_table, dict) else {})
    if not metrics:
        raise NosEvidenceError("nos-evidence-table.json has no metrics")

    ps = _require(RAW / "nos-price-structure.json", "price structure")
    cg = _require(RAW / "cg-market-extract.json", "CoinGecko extract")
    st = _require(RAW / "nosana-indexer-stats.json", "indexer stats")
    jc = _require(RAW / "nosana-jobs-count.json", "jobs count")
    js = _require(RAW / "nosana-jobs-stats.json", "jobs stats")
    ha = _require(RAW / "nosana-hours-agg.json", "hours agg")
    rs = _require(RAW / "nosana-running-summary.json", "running summary")
    jd = _require(RAW / "nosana-jobs-daily-agg.json", "jobs daily agg")
    dx = _load(RAW / "nos-dex-sample-summary.json") or {}
    mm = _require(RAW / "mm-nos-balances.json", "MM balances")
    if not isinstance(mm, list):
        raise NosEvidenceError("mm-nos-balances.json must be a list")

    now_usd = _as_float(cg.get("price_usd")) or _as_float(ps.get("spot_close_usd"))
    if now_usd is None:
        raise NosEvidenceError("No NOS price in Stage-1 packs")

    rets = ps.get("returns_pct") or {}
    rs_map = ps.get("rs_vs_pct") or {}
    # rs_vs_pct keys may be int or str
    def _rs_pair(asset: str) -> dict[str, float | None]:
        out: dict[str, float | None] = {}
        for d in ("7", "30", "90", "180"):
            block = rs_map.get(d) or rs_map.get(int(d)) or {}
            out[d] = _as_float(block.get(asset)) if isinstance(block, dict) else None
        return out

    by_state = jc.get("byState") or {}
    as_of = st.get("date") or ps.get("as_of") or evidence_table.get("gathered_at")
    if not as_of:
        raise NosEvidenceError("No as_of on NOS Stage-1 packs")

    circ = _as_float(cg.get("circulating")) or _as_float(st.get("circulatingSupply"))
    # Data Trust: no silent hard-coded max. Absent → None / UNKNOWN downstream.
    max_supply = _as_float(cg.get("max"))
    if max_supply is None:
        max_row = metrics.get("max_supply") or {}
        max_supply = _as_float(max_row.get("value"))
    staked = _as_float(st.get("nosStaked"))
    mm_hits = [
        x
        for x in mm
        if isinstance(x, dict) and _as_float(x.get("nos") or x.get("balance") or 0) not in (None, 0.0)
    ]

    series_high = ps.get("series_high") or {}
    series_low = ps.get("series_low") or {}

    return {
        "meta": {
            "fetched_at_utc": as_of,
            "paths": {
                "findings": "reports/nos-forensics/stage1-evidence/NOS-STAGE1-FINDINGS.md",
                "evidence_table": "reports/nos-forensics/stage1-evidence/nos-evidence-table.json",
            },
            "evidence_metric_count": len(metrics),
            "stance_locked": STANCE_HEADLINE,
            "supply_read_locked": SUPPLY_READ,
        },
        "stance_headline": STANCE_HEADLINE,
        "price_structure": {
            "now_usd": now_usd,
            "ath_usd": _as_float(cg.get("ath_usd")),
            "ath_date": (cg.get("ath_date") or "")[:10] or None,
            "drawdown_pct": _as_float(cg.get("ath_change_pct")),
            "returns_pct": {
                "7": _as_float(rets.get("7") or rets.get(7)),
                "30": _as_float(rets.get("30") or rets.get(30)),
                "90": _as_float(rets.get("90") or rets.get(90)),
                "180": _as_float(rets.get("180") or rets.get(180)),
            },
            "mcap_usd": _as_float(cg.get("mcap_usd")),
            "fdv_usd": _as_float(cg.get("fdv_usd")),
            "vol24_usd": _as_float(cg.get("vol24_usd")),
            "sma20": _as_float(ps.get("sma20")),
            "sma50": _as_float(ps.get("sma50")),
            "series_high": series_high,
            "series_low": series_low,
            "method_note": (
                "CoinGecko for spot/ATH/mcap; GeckoTerminal Raydium pool OHLCV for returns/RS "
                "(time-sorted). Priority market-confirmation lens = 7d/30d/90d — not 180d alone."
            ),
            "source_url_cg": "https://www.coingecko.com/en/coins/nosana",
            "source_url_gt": (
                "https://www.geckoterminal.com/solana/pools/"
                "3GkFzURGWNWyErnjQvnkZpgcLnNocjnRwvMYXiVDiVQk"
            ),
        },
        "rs_vs_btc_pp": _rs_pair("btc"),
        "rs_vs_sol_pp": _rs_pair("sol"),
        "rs_vs_render_pp": _rs_pair("render"),
        "rs_vs_io_pp": _rs_pair("io"),
        "network": {
            "jobs_completed_cumulative": by_state.get("COMPLETED"),
            "jobs_running": by_state.get("RUNNING"),
            "jobs_queued": by_state.get("QUEUED"),
            "jobs_stopped_cumulative": by_state.get("STOPPED"),
            "gpu_hours_window_total": _as_float(ha.get("total_field")),
            "gpu_hours_last_7d": _as_float(ha.get("sum_last_7d")),
            "gpu_hours_prev_7d": _as_float(ha.get("sum_prev_7d")),
            "jobs_sum_last_30d": jd.get("sum_last_30d"),
            "distinct_nodes_with_running_jobs": rs.get("distinct_nodes_with_running"),
            "running_jobs_sum": rs.get("running_jobs_sum"),
            "markets_listed": 47,
            "jobs_stats_price_cum_nos": _as_float(js.get("price")),
            "jobs_stats_usd_reward_cum": _as_float(js.get("usdReward")),
            "jobs_stats_duration_seconds_cum": _as_float(js.get("duration")),
            "window_note": (
                "~31d visible indexer window. Activity roughly stable-to-slightly-up. "
                "Longer-term growth beyond window = UNKNOWN. "
                "Cumulative completed jobs ≠ growth."
            ),
            "node_terminology": (
                "distinct_nodes_with_running_jobs = nodes currently running ≥1 job. "
                "NOT registered nodes, NOT total online hosts, NOT utilization %."
            ),
            "read": "NETWORK ACTIVE",
            "source_url": "https://blockchain-indexer.k8s.prd.nos.ci/jobs/count",
            "hours_url": "https://blockchain-indexer.k8s.prd.nos.ci/jobs/stats/timestamps-hours",
            "markets_url": "https://host-manager.k8s.prd.nosana.com/markets",
            "explorer_url": "https://explore.nosana.com/",
        },
        "commercial_demand": {
            "read": "PARTIAL",
            "known": [
                "Payment rails documented (credits, Stripe path, dashboard swap, native NOS settlement)",
            ],
            "unknown": [
                "Named customer quality",
                "Payer concentration",
                "Retention",
                "Organic paid demand vs credits/incentives",
                "Audited commercial revenue",
            ],
            "usd_reward_field_note": (
                "Indexer cumulative usdReward (~$host rewards) is NOT audited Nosana revenue."
            ),
            "docs_url": "https://learn.nosana.com/api/first-job.html",
            "swap_blog_url": "https://nosana.com/blog/introducing-swapping-and-priority-fees/",
        },
        "value_capture": {
            "read": "PARTIAL",
            "group_read": "TOKEN RAIL REAL · AUTOMATIC MARKET DEMAND UNPROVEN",
            "nos_on_payment_rail": True,
            "usage_to_open_market_demand": "UNKNOWN",
            "nnp0001_implementation": "UNKNOWN",
            "credits_stripe_conversion_traced": False,
            "verified_open_market_buyback": False,
            "verified_token_burn_program": False,
            "documented": [
                "NOS job-payment / settlement rail",
                "Dashboard swap into NOS",
                "Staking / fee reflection (docs)",
                "NNP host stake / collateral concept",
                "dNOS rebate concept (proposal)",
            ],
            "core_interpretation": (
                "NOS is the documented settlement / coordination token for compute, but "
                "automatic open-market demand from every job is not proven. Credits and "
                "possible multi-currency rails make value capture PARTIAL."
            ),
            "nnp_url": (
                "https://github.com/nosana-ci/network-proposals/blob/main/nnp/NNP-0001-tokenomics.md"
            ),
            "rewards_url": "https://learn.nosana.com/programs/rewards.html",
        },
        "supply": {
            "max_supply": max_supply,
            "circulating": circ,
            "circulating_pct_of_max": (float(circ) / float(max_supply) * 100.0)
            if circ and max_supply
            else None,
            "nos_staked": staked,
            "stakers": st.get("stakers"),
            "usd_value_staked": _as_float(st.get("usdValueStaked")),
            "pressure_read": SUPPLY_READ,
            "live_emission_rate": "UNKNOWN",
            "unlock_schedule": "UNKNOWN",
            "nnp_live_status": "UNKNOWN",
            "display_rule": (
                "Near-full circulation = no large unissued overhang. "
                "Live emission pressure UNKNOWN — do not label MATERIAL supply pressure."
            ),
            "source_url": "https://www.coingecko.com/en/coins/nosana",
            "staking_url": "https://blockchain-indexer.k8s.prd.nos.ci/stats/",
        },
        "derivatives": {
            "binance_nos": "ABSENT",
            "bybit_nos": "ABSENT",
            "okx_nos": "ABSENT",
            "oi": None,
            "funding": None,
            "read": "NO MAJOR CEX PERP FOUND THIS PASS",
            "note": "Do not invent OI, funding, or leverage stress. Spot liquidity is thin.",
        },
        "capital_flow": {
            "who_buying": "UNKNOWN beyond bounded DEX sample",
            "who_selling": "UNKNOWN beyond bounded DEX sample",
            "sample_n": dx.get("n"),
            "sample_buys": dx.get("buys"),
            "sample_sells": dx.get("sells"),
            "sample_buy_usd": _as_float(dx.get("buy_usd")),
            "sample_sell_usd": _as_float(dx.get("sell_usd")),
            "dex_note": (
                "Bounded GeckoTerminal sample on top pool only — not market-wide, not a census. "
                "TRANSFER ≠ SALE. CEX deposit ≠ SALE."
            ),
            "holders": "UNKNOWN",
            "holders_note": "Top-holder RPC query failed this pass. Staked NOS ≠ whale dump inventory.",
            "source_url": (
                "https://www.geckoterminal.com/solana/pools/"
                "3GkFzURGWNWyErnjQvnkZpgcLnNocjnRwvMYXiVDiVQk"
            ),
        },
        "mm": {
            "read": "NO MATERIAL MM INVENTORY EVENT OBSERVED IN VERIFIED REGISTRY WALLETS",
            "warning": False,
            "hits": len(mm_hits),
            "note": "Absence is not proof no market makers exist. MM interaction ≠ suppression.",
        },
        "competitive": {
            "nos_mcap_usd": _as_float(cg.get("mcap_usd")),
            "render_mcap_usd": 648_992_382,
            "io_mcap_usd": 44_256_652,
            "note": (
                "Size context only — not apples-to-apples. Smaller size ≠ better / faster / "
                "undervalued. Public evidence supports less automatic token capture than RENDER BME."
            ),
        },
    }
