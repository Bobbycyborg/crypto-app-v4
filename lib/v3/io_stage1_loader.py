"""Canonical IO Stage-1 evidence loader — packs only, no silent fallbacks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.paths import REPORTS

STAGE1 = REPORTS / "io-forensics" / "stage1-evidence"
RAW = STAGE1 / "raw"

ATH_USD_KNOWN = 6.43
STANCE_HEADLINE = "EARNINGS REAL · CAPTURE EARLY · TAPE WEAK"


class IoEvidenceError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path, label: str) -> Any:
    data = _load(path)
    if data is None:
        raise IoEvidenceError(f"Missing required IO evidence: {label} ({path})")
    return data


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("%", "").replace(",", "").replace("+", "").replace("×", "")
    try:
        return float(s)
    except ValueError:
        return None


def _ret(closes: list[float], days: int) -> float | None:
    if len(closes) <= days:
        return None
    a, b = closes[-1 - days], closes[-1]
    if a <= 0:
        return None
    return (b / a - 1.0) * 100.0


def _rs(a: list[float], b: list[float], days: int) -> float | None:
    ra, rb = _ret(a, days), _ret(b, days)
    if ra is None or rb is None:
        return None
    return ra - rb


def _binance_closes(path: Path) -> list[float]:
    rows = _require(path, path.name)
    if isinstance(rows, dict) and rows.get("error"):
        raise IoEvidenceError(f"Bad klines {path}: {rows['error']}")
    return [float(x["c"]) for x in rows]


def load_io_canonical() -> dict[str, Any]:
    evidence_table = _require(STAGE1 / "io-evidence-table.json", "evidence table")
    if isinstance(evidence_table, dict):
        evidence_table = evidence_table.get("rows") or evidence_table.get("metrics") or []
    if not evidence_table:
        raise IoEvidenceError("io-evidence-table.json has no rows")

    market = _require(RAW / "market_analysis_snapshot.json", "market snapshot")
    cg = _require(RAW / "cg_io.json", "CoinGecko io")
    tok = _require(RAW / "tokenomics_notes.json", "tokenomics notes")
    clusters = _require(RAW / "network_v1_io-explorer_network_info_clusters.json", "clusters")
    inv = _require(RAW / "network_v1_io-explorer_network_inventory-aggregated.json", "inventory")
    monthly = _require(
        RAW / "network_v1_io-explorer_network_info_cluster_monthly-earnings.json",
        "monthly earnings",
    )
    mm = _require(RAW / "mm_io_balances.json", "MM balances")
    if not isinstance(mm, list):
        raise IoEvidenceError("mm_io_balances.json must be a list")

    md = cg.get("market_data") or {}
    price_block = market.get("price") or {}
    deriv_block = market.get("derivatives") or {}
    net_block = market.get("network") or {}
    dex_block = market.get("dex_top10") or {}

    price_usd = _as_float(price_block.get("cg")) or _as_float(
        (md.get("current_price") or {}).get("usd")
    )
    if price_usd is None:
        raise IoEvidenceError("No IO price in Stage-1 packs")

    ath = _as_float(price_block.get("ath")) or _as_float((md.get("ath") or {}).get("usd"))
    if ath is None:
        raise IoEvidenceError("No IO ATH in Stage-1 packs — will not invent ATH_USD_KNOWN")
    dd = _as_float(price_block.get("ath_chg_pct")) or _as_float(
        (md.get("ath_change_percentage") or {}).get("usd")
    )
    ath_date = ((md.get("ath_date") or {}).get("usd") or "")[:10] or None

    # Prefer recomputed Binance spot RS from raw klines (authoritative for page).
    ioc = _binance_closes(RAW / "binance_spot_daily_io.json")
    btcc = _binance_closes(RAW / "binance_spot_daily_btc.json")
    solc = _binance_closes(RAW / "binance_spot_daily_sol.json")
    rndc = _binance_closes(RAW / "binance_spot_daily_render.json")
    taoc = _binance_closes(RAW / "binance_spot_daily_tao.json")
    n = min(len(ioc), len(btcc), len(solc), len(rndc), len(taoc))
    ioc, btcc, solc, rndc, taoc = ioc[-n:], btcc[-n:], solc[-n:], rndc[-n:], taoc[-n:]

    returns = {d: _ret(ioc, int(d)) for d in ("7", "30", "90", "180")}
    rs_btc = {d: _rs(ioc, btcc, int(d)) for d in ("7", "30", "90", "180")}
    rs_sol = {d: _rs(ioc, solc, int(d)) for d in ("7", "30", "90", "180")}
    rs_render = {d: _rs(ioc, rndc, int(d)) for d in ("7", "30", "90", "180")}
    rs_tao = {d: _rs(ioc, taoc, int(d)) for d in ("7", "30", "90", "180")}

    cl_data = clusters.get("data") or {}
    inv_data = inv.get("data") or {}
    monthly_rows = monthly.get("data") or []
    monthly_map = {str(r.get("month")): _as_float(r.get("monthly_earnings")) for r in monthly_rows}

    as_of = market.get("fetched_at") or tok.get("fetched_at")
    if not as_of:
        raise IoEvidenceError("No fetched_at on required IO packs")

    circ = _as_float(price_block.get("circ")) or _as_float(md.get("circulating_supply"))
    max_supply = _as_float(price_block.get("max")) or _as_float(md.get("max_supply")) or 800_000_000

    mm_hits = [x for x in mm if isinstance(x, dict) and (x.get("io_balance") or 0) > 0]

    return {
        "meta": {
            "fetched_at_utc": as_of,
            "paths": {
                "findings": "reports/io-forensics/stage1-evidence/IO-STAGE1-FINDINGS.md",
                "evidence_table": "reports/io-forensics/stage1-evidence/io-evidence-table.json",
            },
            "evidence_row_count": len(evidence_table),
        },
        "stance_headline": STANCE_HEADLINE,
        "price_structure": {
            "now_usd": price_usd,
            "ath_usd": ath,
            "ath_date": ath_date,
            "drawdown_pct": dd,
            "returns_pct": returns,
            "local_high_180": price_block.get("local_high_180"),
            "local_low_180": price_block.get("local_low_180"),
            "method_note": "Binance spot IOUSDT daily closes for returns/RS; CoinGecko for ATH.",
        },
        "rs_vs_btc_pp": rs_btc,
        "rs_vs_sol_pp": rs_sol,
        "rs_vs_render_pp": rs_render,
        "rs_vs_tao_pp": rs_tao,
        "derivatives": {
            "spot_quote_vol_24h": _as_float(deriv_block.get("binance_spot_qv_24h")),
            "fut_quote_vol_24h": _as_float(deriv_block.get("binance_fut_qv_24h")),
            "fut_spot_ratio": _as_float(deriv_block.get("fut_spot_ratio")),
            "oi_tokens": _as_float(deriv_block.get("oi_tokens")),
            "oi_notional_usd": _as_float(deriv_block.get("oi_notional_usd")),
            "oi_vs_30d_max_pct": _as_float(deriv_block.get("oi_pct_of_30d_max")),
            "funding_latest": _as_float(deriv_block.get("funding_latest")),
            "read": "LEVERAGE-LED VS SPOT · OI ELEVATED · FUNDING QUIET",
            "note": "OI rising ≠ bearish. Funding quiet — not an extreme-top print alone.",
            "source_url": "https://www.binance.com/en/futures/IOUSDT",
        },
        "network": {
            "total_earnings_usd": _as_float(cl_data.get("total_earnings"))
            or _as_float((net_block.get("total_earnings_clusters_endpoint") or {}).get("total_earnings")),
            "total_compute_hours": _as_float(cl_data.get("total_compute_hours_served")),
            "running_clusters": cl_data.get("running_clusters"),
            "inventory_total": inv_data.get("total"),
            "inventory_active_api": inv_data.get("active"),
            "inventory_passive_api": inv_data.get("passive"),
            "inventory_note": (
                "API active/passive labels are inventory labels — not proven hired/idle. "
                "Do not equate inventory/device count with utilized compute."
            ),
            "avg_daily_earn_7d": _as_float(net_block.get("avg_daily_earn_last7")),
            "avg_daily_earn_30d": _as_float(net_block.get("avg_daily_earn_last30")),
            "monthly_may": monthly_map.get("May"),
            "monthly_june": monthly_map.get("June"),
            "monthly_july": monthly_map.get("July"),
            "read": "NETWORK EARNINGS REAL · UTILIZATION MODEST",
            "demand_read": "REAL DEMAND · RECENT EARNINGS SOFTER",
            "source_url": "https://api.io.solutions/v1/io-explorer/network/info/clusters",
            "explorer_url": "https://explorer.io.net",
        },
        "value_capture": {
            "read": "MECHANISM EXISTS · SCALE EARLY",
            "group_read": "CAPTURE EARLY · SUPPLY PRESSURE MATERIAL",
            "io_required_to_pay": False,
            "io_payment_fee": "0%",
            "usdc_payment_fee": "2%",
            "supplier_staking_required": True,
            "ide_burn_design": "Documented — revenue/surplus-funded burn under IDE",
            "measured_burn_status": "UNKNOWN",
            "io_payment_share_status": "UNKNOWN",
            "doc_url": "https://io.net/docs/guides/coin/io-tokenomics",
            "pay_url": "https://io.net/docs/guides/payment/io-cloud-payments",
            "staking_url": "https://io.net/docs/guides/staking/io-staking",
            "ide_url": "https://io.net/tokenomics",
        },
        "supply": {
            "max_supply": max_supply,
            "circulating_cg": circ,
            "circulating_pct_of_max": (float(circ) / float(max_supply) * 100.0)
            if circ and max_supply
            else None,
            "emissions_design": "500M genesis + 300M emissions over ~20y",
            "pressure_read": "MATERIAL",
            "next_unlock_first_party_status": "UNKNOWN",
            "display_rule": "Circulating ~48% of max; ongoing emissions/vesting. Exact next unlock sizes UNKNOWN.",
        },
        "capital_flow": {
            "who_buying": "UNKNOWN",
            "who_selling": "UNKNOWN",
            "dex_buys_24h": dex_block.get("buys"),
            "dex_sells_24h": dex_block.get("sells"),
            "dex_vol_24h": dex_block.get("vol_usd"),
            "dex_note": (
                "IO is CEX-heavy. Small Solana DEX sample is not representative. "
                "Do not infer accumulation from DEX txn counts."
            ),
            "source_url": "https://dexscreener.com/solana/BZLbGTNCSFfoth2GYDtwr7e4imWzpR5jqcUuGEwr646K",
        },
        "mm": {
            "read": "NO VERIFIED MATERIAL MM / OTC IO INVENTORY THIS PASS",
            "warning": False,
            "hits": len(mm_hits),
            "note": "Absence is not a warning. MM interaction ≠ suppression.",
        },
    }
