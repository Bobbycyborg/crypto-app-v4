"""Canonical GRASS Stage-1 evidence loader — packs only, no silent fallbacks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.paths import REPORTS

STAGE1 = REPORTS / "grass-forensics" / "stage1-evidence"
RAW = STAGE1 / "raw"

ATH_USD_KNOWN = 3.89
ATH_DATE_KNOWN = "2024-11-08"


class GrassEvidenceError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path, label: str) -> Any:
    data = _load(path)
    if data is None:
        raise GrassEvidenceError(f"Missing required GRASS evidence: {label} ({path})")
    return data


def _table_lookup(rows: list[dict], metric: str) -> dict | None:
    for r in rows or []:
        if r.get("metric") == metric:
            return r
    return None


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("%", "").replace(",", "").replace("+", "")
    try:
        return float(s)
    except ValueError:
        return None


def load_grass_canonical() -> dict[str, Any]:
    evidence_table = _require(STAGE1 / "grass-evidence-table.json", "evidence table")
    if isinstance(evidence_table, dict):
        evidence_table = evidence_table.get("rows") or evidence_table.get("metrics") or []
    if not evidence_table:
        raise GrassEvidenceError("grass-evidence-table.json has no rows")

    market = _require(RAW / "market_analysis_snapshot.json", "market snapshot")
    cg = _require(RAW / "cg_grass.json", "CoinGecko grass")
    deriv = _require(RAW / "derivatives_summary.json", "derivatives summary")
    dex = _require(RAW / "dex_flow_summary.json", "dex flow summary")
    tok = _require(RAW / "tokenomics_notes.json", "tokenomics notes")
    spl = _load(RAW / "solana_token_supply.json") or {}

    md = cg.get("market_data") or {}
    price_usd = _as_float((md.get("current_price") or {}).get("usd"))
    if price_usd is None:
        price_usd = _as_float(market.get("binance_fut_price"))

    dd = _as_float((md.get("ath_change_percentage") or {}).get("usd"))
    ath = _as_float((md.get("ath") or {}).get("usd"))
    if ath is None:
        raise GrassEvidenceError("No GRASS ATH in Stage-1 packs — will not invent ATH_USD_KNOWN")
    ath_date_raw = (md.get("ath_date") or {}).get("usd")
    if not ath_date_raw:
        raise GrassEvidenceError("No GRASS ATH date in Stage-1 packs — will not invent ATH_DATE_KNOWN")
    ath_date = str(ath_date_raw)[:10]

    rs = market.get("rs") or {}

    def _pp(base: str, d: str) -> float | None:
        block = (rs.get(base) or {}).get(d) or {}
        v = block.get("pp")
        return float(v) if isinstance(v, (int, float)) else None

    returns = market.get("returns_grass_pct") or {}
    july = (tok.get("july7_call") or {})
    alloc = tok.get("allocations") or {}
    secondary = tok.get("secondary_unlock_monitor") or {}

    spl_ui = ((spl.get("result") or {}).get("value") or {}).get("uiAmount")
    circ = _as_float(md.get("circulating_supply"))
    max_supply = _as_float(md.get("max_supply"))
    if max_supply is None:
        raise GrassEvidenceError("No GRASS max_supply in Stage-1 packs — will not invent 1B")

    as_of = (
        market.get("fetched_at_utc")
        or cg.get("fetched_at")
        or deriv.get("fetched_at")
    )
    if not as_of:
        raise GrassEvidenceError("No fetched_at on required GRASS packs")

    return {
        "meta": {
            "fetched_at_utc": as_of,
            "paths": {
                "findings": str(STAGE1 / "GRASS-STAGE1-FINDINGS.md"),
                "evidence_table": str(STAGE1 / "grass-evidence-table.json"),
            },
        },
        "stance_headline": "REVENUE REAL · CAPTURE EARLY · TAPE WEAK",
        "price_structure": {
            "now_usd": price_usd,
            "ath_usd": ath,
            "ath_date": ath_date,
            "ath_note": "Historical CoinGecko ATH event — intentional labelled constant if used",
            "drawdown_pct": dd,
            "returns_pct": {
                "7": _as_float(returns.get("7")),
                "30": _as_float(returns.get("30")),
                "90": _as_float(returns.get("90")),
                "180": _as_float(returns.get("180")),
            },
            "cg_change_7d_pct": _as_float(md.get("price_change_percentage_7d")),
            "cg_change_30d_pct": _as_float(md.get("price_change_percentage_30d")),
            "cg_change_1y_pct": _as_float(md.get("price_change_percentage_1y")),
            "local_high": market.get("recent_local_high_close"),
            "local_low": market.get("recent_local_low_close"),
            "method_note": market.get("method"),
        },
        "rs_vs_btc_pp": {d: _pp("BTC", d) for d in ("7", "30", "90", "180")},
        "rs_vs_sol_pp": {d: _pp("SOL", d) for d in ("7", "30", "90", "180")},
        "rs_vs_render_pp": {d: _pp("RENDER", d) for d in ("7", "30", "90", "180")},
        "rs_vs_tao_pp": {d: _pp("TAO", d) for d in ("7", "30", "90", "180")},
        "derivatives": {
            "fut_quote_vol_24h": _as_float(deriv.get("fut_quote_vol_24h")),
            "spot_quote_vol_24h": _as_float(deriv.get("spot_quote_vol_24h")),
            "binance_spot_listed": False,
            "fut_spot_ratio": None,
            "oi_tokens": _as_float(deriv.get("oi_tokens")),
            "oi_notional_usd": _as_float(deriv.get("oi_notional_approx")),
            "oi_vs_30d_max_pct": _as_float(deriv.get("oi_vs_30d_max_pct")),
            "funding_latest": _as_float(deriv.get("funding_latest")),
            "read": "LEVERAGE PRESENT · VENUE FUT/SPOT UNKNOWN · FUNDING QUIET",
            "note": "Binance spot GRASSUSDT not listed. OI rising ≠ bearish.",
            "source_url": "https://www.binance.com/en/futures/GRASSUSDT",
        },
        "value_capture": {
            "read": "MECHANISM EXISTS · REVENUE REAL · TOKEN BUY-PRESSURE UNPROVEN",
            "group_read": "REVENUE REAL · TOKEN CAPTURE EARLY",
            "revenue_2025_usd": july.get("revenue_2025_total_usd"),
            "revenue_2026_h1_usd": july.get("revenue_2026_h1_usd"),
            "fy2026_guide": july.get("fy2026_training_data_guide_usd"),
            "fy2026_guide_label": "Forward guidance (not audited)",
            "opex_month": july.get("opex_usd_per_month"),
            "doc_mechanism": tok.get("value_capture_doc_claim"),
            "doc_url": tok.get("value_capture_doc"),
            "measured_buys": None,
            "measured_buys_status": "UNKNOWN",
            "stage2_rewards": july.get("stage2_rewards"),
            "call_url": july.get("url"),
            "call_as_of": july.get("as_of"),
            # Hero/stance copy stays evidence-safe: revenue + opex disclosure.
            # Profitability first-party claim exists in evidence table but is not
            # reintroduced into primary hero wording unless separately required.
        },
        "supply": {
            "max_supply": max_supply,
            "circulating_cg": circ,
            "spl_onchain": _as_float(spl_ui),
            "pressure_read": "MATERIAL",
            "investors": (alloc.get("early_investors") or {}).get("amount"),
            "contributors": (alloc.get("contributors") or {}).get("amount"),
            "foundation_ecosystem": alloc.get("foundation_ecosystem"),
            "community": (alloc.get("community") or {}).get("amount"),
            "next_unlock_first_party": None,
            "next_unlock_first_party_status": "UNKNOWN",
            "next_unlock_secondary": secondary.get("next_unlock_cited"),
            "next_unlock_secondary_note": secondary.get("note"),
            "secondary_source_url": secondary.get("source"),
            "display_rule": "SPL on-chain total ≠ liquid circulating. Do not treat ~1B mint as float.",
        },
        "capital_flow": {
            "who_buying": "UNKNOWN",
            "who_selling": "UNKNOWN",
            "dex_buys_24h": dex.get("buys24_sum_top10"),
            "dex_sells_24h": dex.get("sells24_sum_top10"),
            "dex_vol_24h": dex.get("vol24_sum_top10"),
            "dex_note": "Top-10 Solana pools by DexScreener 24h vol — txn counts only, not market-wide, not wallet identity.",
            "source_url": "https://dexscreener.com/solana/Grass7B4RdKfBCjTKgSqnXkqjwiGvQyFbuSCUJr3XXjs",
        },
        "mm": {
            "read": "NO VERIFIED MATERIAL MM / OTC PRINT",
            "warning": False,
        },
        "network": {
            "traffic_concentration": "150k users ≈ 90% Stage 2 traffic (first-party call)",
            "nodes_exact": None,
            "lcr_status": "First LCR products launching summer 2026 (stated)",
        },
        "evidence_table": evidence_table,
    }
