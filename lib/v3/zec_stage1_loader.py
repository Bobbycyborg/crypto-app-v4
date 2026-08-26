"""Canonical ZEC Stage-1 evidence loader — packs only, no silent fallbacks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.paths import REPORTS

STAGE1 = REPORTS / "zec-forensics" / "stage1-evidence"
RAW = STAGE1 / "raw"

STANCE_HEADLINE = "SHIELDED STOCK · 1Y EXTREME · FLOWS OPAQUE"
SUPPLY_READ = "CAPPED BUT STILL INFLATING · ISSUANCE PROGRAMMATIC"
CG_ID = "zcash"
BINANCE_SYMBOL = "ZECUSDT"


class ZecEvidenceError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path, label: str) -> Any:
    data = _load(path)
    if data is None:
        raise ZecEvidenceError(f"Missing required ZEC evidence: {label} ({path})")
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


def _require_identity(cg: dict[str, Any], table: dict[str, Any]) -> None:
    cg_id = str(cg.get("id") or "").strip().lower()
    if cg_id != CG_ID:
        raise ZecEvidenceError(f"CoinGecko id={cg.get('id')!r} — expected {CG_ID}")
    sym = str(cg.get("symbol") or "").strip().lower()
    if sym != "zec":
        raise ZecEvidenceError(f"CoinGecko symbol={cg.get('symbol')!r} — expected zec")
    name = str(cg.get("name") or "").strip().lower()
    if name != "zcash":
        raise ZecEvidenceError(f"CoinGecko name={cg.get('name')!r} — expected Zcash")
    if str(table.get("asset") or "").strip().upper() != "ZEC":
        raise ZecEvidenceError(f"evidence table asset={table.get('asset')!r} — expected ZEC")
    if str(table.get("coingecko_id") or "").strip().lower() != CG_ID:
        raise ZecEvidenceError(
            f"evidence table coingecko_id={table.get('coingecko_id')!r} — expected {CG_ID}"
        )


def _venue_status_from_ticker(pack: dict[str, Any], *, symbol: str, label: str) -> str:
    pack_sym = str(pack.get("symbol") or pack.get("instId") or "").upper()
    if pack_sym and pack_sym not in {symbol, f"{symbol[:3]}-USD", "ZEC-USD"}:
        # Binance uses ZECUSDT; Coinbase ticker has no symbol field
        if "lastPrice" in pack or "quoteVolume" in pack:
            if pack_sym and pack_sym != symbol:
                raise ZecEvidenceError(
                    f"{label} symbol={pack.get('symbol')!r} — expected {symbol}"
                )
    if pack.get("code") not in (None, 0, "0") and pack.get("msg"):
        raise ZecEvidenceError(f"{label} is an error payload, not a live ticker")
    if _as_float(pack.get("lastPrice") or pack.get("price")) is None:
        raise ZecEvidenceError(f"{label} missing lastPrice/price — cannot claim PRESENT")
    return "PRESENT"


def load_zec_canonical() -> dict[str, Any]:
    evidence_table = _require(STAGE1 / "zec-evidence-table.json", "evidence table")
    if not isinstance(evidence_table, dict):
        raise ZecEvidenceError("zec-evidence-table.json malformed")
    metrics = _metric_map(evidence_table)
    if not metrics:
        raise ZecEvidenceError("zec-evidence-table.json has no metrics")

    cg = _require(RAW / "cg-market-extract.json", "CoinGecko extract")
    _require_identity(cg, evidence_table)

    ps = _require(RAW / "zec-price-structure.json", "price structure")
    lev = _require(RAW / "zec-leverage-snapshot.json", "leverage snapshot")
    pools = _require(RAW / "zec-value-pools.json", "shielded valuePools")
    mon = _require(RAW / "zec-monetary-estimate.json", "monetary estimate")
    net = _require(RAW / "zec-network-activity.json", "network activity")
    util = _require(RAW / "zec-token-utility.json", "token utility")
    mm_note = _require(RAW / "mm-zec-note.json", "MM note (UNKNOWN, not zero)")
    bybit = _require(RAW / "bybit-zec-perp.json", "Bybit perp")
    okx_oi = _require(RAW / "okx-zec-oi.json", "OKX OI")

    now_usd = _as_float(cg.get("price_usd")) or _as_float(ps.get("spot_close_usd"))
    if now_usd is None:
        raise ZecEvidenceError("No ZEC price in Stage-1 packs")

    max_supply = _as_float(cg.get("max"))
    circ = _as_float(cg.get("circulating"))
    if max_supply is None:
        raise ZecEvidenceError("max supply missing from CoinGecko extract")
    if circ is None:
        raise ZecEvidenceError("circulating supply missing from CoinGecko extract")

    binance_perp_symbol = lev.get("binance_perp_symbol")
    if binance_perp_symbol != BINANCE_SYMBOL:
        raise ZecEvidenceError(
            f"binance_perp_symbol={binance_perp_symbol!r} — expected {BINANCE_SYMBOL}"
        )

    spot_24h = _require(RAW / "binance-zec-spot-24h.json", "Binance spot 24h")
    perp_24h = _require(RAW / "binance-zec-perp-24h.json", "Binance perp 24h")
    cb = _require(RAW / "coinbase-zec-ticker.json", "Coinbase spot ticker")
    if not isinstance(spot_24h, dict) or not isinstance(perp_24h, dict) or not isinstance(cb, dict):
        raise ZecEvidenceError("venue ticker packs malformed")

    binance_spot_status = _venue_status_from_ticker(
        spot_24h, symbol=BINANCE_SYMBOL, label="Binance spot"
    )
    binance_perp_status = _venue_status_from_ticker(
        perp_24h, symbol=BINANCE_SYMBOL, label="Binance perp"
    )
    if _as_float(cb.get("price")) is None and _as_float(cb.get("volume")) is None:
        raise ZecEvidenceError("Coinbase ticker missing price/volume — cannot claim PRESENT")
    coinbase_spot_status = "PRESENT"

    pool_map = pools.get("pools_zec")
    if not isinstance(pool_map, dict):
        raise ZecEvidenceError("valuePools pack missing pools_zec")
    for key in ("transparent", "sprout", "sapling", "orchard", "ironwood", "lockbox"):
        if key not in pool_map:
            raise ZecEvidenceError(f"valuePools missing {key}")
    shielded = _as_float(pools.get("shielded_zec_sum"))
    shielded_pct = _as_float(pools.get("shielded_pct_of_chain"))
    if shielded is None or shielded_pct is None:
        raise ZecEvidenceError("shielded stock missing from valuePools pack")

    rets = ps.get("returns_pct") or {}
    rs_map = ps.get("rs_vs_pct") or {}

    def _rs_pair(asset: str) -> dict[str, float | None]:
        out: dict[str, float | None] = {}
        for d in ("7", "30", "90", "180"):
            block = rs_map.get(d) or rs_map.get(int(d)) or {}
            out[d] = _as_float(block.get(asset)) if isinstance(block, dict) else None
        return out

    as_of = ps.get("as_of") or cg.get("fetched_at") or evidence_table.get("gathered_at")
    if not as_of:
        raise ZecEvidenceError("No as_of on ZEC Stage-1 packs")

    mcap = _as_float(cg.get("mcap_usd"))
    cg_fdv = _as_float(cg.get("fdv_usd"))
    max_implied = now_usd * max_supply

    mm_status = mm_note.get("zec_chain_mm_balances")
    if mm_status != "UNKNOWN":
        raise ZecEvidenceError(
            "ZEC MM must remain UNKNOWN — Solana registry does not apply; do not invent inventory"
        )
    if util.get("staking") or util.get("buyback") or util.get("protocol_revenue_to_token"):
        raise ZecEvidenceError("Stage-1 utility pack contradicts monetary-only capture")

    by_list = ((bybit.get("result") or {}).get("list") or []) if isinstance(bybit, dict) else []
    by_oi = _as_float((by_list[0] if by_list else {}).get("openInterestValue"))
    okx_row = ((okx_oi.get("data") or [{}])[0]) if isinstance(okx_oi, dict) else {}
    okx_usd = _as_float(okx_row.get("oiUsd"))
    binance_oi = _as_float(lev.get("oi_usd_approx"))
    if by_oi is None or okx_usd is None or binance_oi is None:
        raise ZecEvidenceError("Partial venue OI incomplete — cannot invent global or partial sum")
    partial_oi = binance_oi + by_oi + okx_usd

    return {
        "meta": {
            "fetched_at_utc": as_of,
            "paths": {
                "findings": "reports/zec-forensics/stage1-evidence/ZEC-STAGE1-FINDINGS.md",
                "evidence_table": "reports/zec-forensics/stage1-evidence/zec-evidence-table.json",
            },
            "evidence_metric_count": len(metrics),
            "stance_locked": STANCE_HEADLINE,
            "supply_read_locked": SUPPLY_READ,
            "coingecko_id": CG_ID,
        },
        "stance_headline": STANCE_HEADLINE,
        "price_structure": {
            "now_usd": now_usd,
            "ath_usd": _as_float(cg.get("ath_usd")),
            "ath_date": (cg.get("ath_date") or "")[:10] or None,
            "ath_caveat": "2016 early-market ATH — distorted vs modern cycle highs",
            "drawdown_pct": _as_float(cg.get("ath_change_pct")),
            "sample_high_usd": _as_float((ps.get("sample_high") or {}).get("usd")),
            "sample_high_ts": (ps.get("sample_high") or {}).get("ts"),
            "returns_pct": {
                "7": _as_float(rets.get("7") or rets.get(7)),
                "30": _as_float(rets.get("30") or rets.get(30)),
                "90": _as_float(rets.get("90") or rets.get(90)),
                "180": _as_float(rets.get("180") or rets.get(180)),
            },
            "cg_1y_change_pct": _as_float((cg.get("price_change_pct") or {}).get("1y")),
            "mcap_usd": mcap,
            "cg_fdv_usd": cg_fdv,
            "max_supply_implied_usd": max_implied,
            "valuation_note": (
                "MARKET CAP = price × circulating. "
                "CoinGecko FDV ≈ mcap because total_supply ≈ circulating — NOT 21M FDV. "
                "MAX-SUPPLY IMPLIED = price × 21M. Do not substitute CG FDV for max implied."
            ),
            "vol24_usd": _as_float(cg.get("vol24_usd")),
            "sma20": _as_float(ps.get("sma20")),
            "sma50": _as_float(ps.get("sma50")),
            "method_note": (
                "CoinGecko for spot/ATH/mcap; Binance daily for returns/RS. "
                "SMA descriptive only — not a trading rule. "
                "Near-term leadership weak; medium-term real; long-window extreme."
            ),
            "source_url_cg": "https://www.coingecko.com/en/coins/zcash",
            "source_url_binance": "https://www.binance.com/en/trade/ZEC_USDT",
        },
        "rs_vs_btc_pp": _rs_pair("btc"),
        "rs_vs_sol_pp": _rs_pair("sol"),
        "spot_liquidity": {
            "binance_spot": binance_spot_status,
            "binance_perp": binance_perp_status,
            "coinbase_spot": coinbase_spot_status,
            "cg_vol24_usd": _as_float(cg.get("vol24_usd")),
            "binance_spot_vol_24h": _as_float(lev.get("spot_quote_vol_24h")),
            "read": "MAJOR SPOT ACCESS NOT STRUCTURALLY IMPAIRED",
            "note": (
                "Binance spot + Coinbase spot PRESENT in Stage-1 tickers. "
                "Historical privacy-coin regulatory fear ≠ current observed access failure. "
                "Forward listing/regulatory path UNKNOWN."
            ),
            "source_url": "https://www.coingecko.com/en/coins/zcash",
        },
        "leverage": {
            "read": "LEVERAGE MATERIAL",
            "binance_perp_symbol": binance_perp_symbol,
            "binance_spot": binance_spot_status,
            "oi_tokens": _as_float(lev.get("oi_tokens")),
            "oi_usd_approx": _as_float(lev.get("oi_usd_approx")),
            "perp_quote_vol_24h": _as_float(lev.get("perp_quote_vol_24h")),
            "spot_quote_vol_24h": _as_float(lev.get("spot_quote_vol_24h")),
            "funding_rate": _as_float(lev.get("funding_rate")),
            "perp_vs_binance_spot_ratio": _as_float(lev.get("perp_vs_binance_spot_ratio")),
            "oi_hist_30d_start_usd": _as_float(lev.get("oi_hist_30d_start_usd")),
            "oi_hist_30d_end_usd": _as_float(lev.get("oi_hist_30d_end_usd")),
            "ratio_label": (
                "BINANCE PERP VOLUME vs BINANCE SPOT — not global futures/spot"
            ),
            "ratio_confidence": "MEDIUM",
            "partial_multi_venue_oi_usd": partial_oi,
            "multi_venue_oi_aggregate": "UNKNOWN",
            "note": (
                "OI falling over ~30d observed window — not a clean expanding-leverage blow-off. "
                "Mild positive funding ≠ top. Partial Binance+Bybit+OKX sum is not global OI."
            ),
            "source_url": f"https://www.binance.com/en/futures/{binance_perp_symbol}",
        },
        "supply": {
            "max_supply": max_supply,
            "circulating": circ,
            "circulating_pct_of_max": (float(circ) / float(max_supply) * 100.0),
            "remaining_unissued": max_supply - circ,
            "remaining_unissued_pct": ((max_supply - circ) / max_supply * 100.0),
            "block_reward_zec": _as_float(mon.get("block_reward_zec")),
            "estimated_annual_inflation_pct": _as_float(
                mon.get("estimated_annual_inflation_pct_of_circ")
            ),
            "next_3m_issuance_zec": _as_float(mon.get("next_3m_issuance_zec")),
            "next_6m_issuance_zec": _as_float(mon.get("next_6m_issuance_zec")),
            "next_12m_issuance_zec": _as_float(mon.get("next_12m_issuance_zec")),
            "issuance_allocation": mon.get("issuance_allocation_post_NU6"),
            "pressure_read": SUPPLY_READ,
            "issuance_model": "PROGRAMMATIC MINING + FUNDING ALLOCATION",
            "not_an_unlock": True,
            "staking": False,
            "buyback": bool(util.get("buyback")),
            "display_rule": (
                "Capped 21M max, still inflating via programmatic issuance. "
                "Issuance is programmatic mining + funding allocation, not a vesting schedule. "
                "Prefer NEXT 12M ISSUANCE · REMAINING UNISSUED · CURRENT INFLATION."
            ),
            "source_url": "https://electriccoin.co/blog/zcash-halvening-nu6-embracing-the-new-dev-fund/",
        },
        "privacy": {
            "read": "CAPABILITY REAL · SHIELDED STOCK MATERIAL · USAGE-RATE TREND UNKNOWN",
            "pools_zec": pool_map,
            "shielded_zec": shielded,
            "shielded_pct_of_chain": shielded_pct,
            "lockbox_zec": _as_float(pools.get("lockbox_zec")),
            "lockbox_is_privacy_stock": False,
            "nu63_active": bool(pools.get("nu63_active")),
            "tx_24h": net.get("transactions_24h"),
            "tx_note": (
                "Throughput is network-wide mixed tx types — not a shielded-usage rate. "
                "Do not imply these transactions are all shielded. "
                "Usage-rate trend remains UNKNOWN."
            ),
            "usage_rate_trend": "UNKNOWN",
            "historical_shielded_series": "UNKNOWN",
            "source_url": pools.get("source")
            or "https://mainnet.zcashexplorer.app/api/v1/blockchain-info",
        },
        "value_capture": {
            "model": "MONETARY / PRIVACY DEMAND — not cash-flow token",
            "staking": False,
            "buyback": False,
            "revenue_to_token": False,
            "fee_economics": "UNKNOWN",
            "note": (
                "Need for ZEC is fees/transfers + optional privacy. "
                "Absence of buyback/revenue is not automatically bearish."
            ),
        },
        "ownership": {
            "adjusted_status": "UNKNOWN",
            "beneficial_ownership": "UNKNOWN",
            "transparent_whale_map": "UNKNOWN",
            "shielded_beneficial": "unknowable by design",
            "read": "OWNERS / FLOWS OPAQUE",
            "note": (
                "Do not invent global whale concentration from incomplete transparent data. "
                "TRANSFER ≠ SALE. CEX deposit ≠ SALE. Miner receipt ≠ dumping."
            ),
        },
        "capital_flow": {
            "who_buying": "UNKNOWN",
            "who_selling": "UNKNOWN",
            "note": "Market-wide buyer/seller quality cannot be established. Privacy is the constraint.",
        },
        "mm": {
            "read": "UNKNOWN",
            "wintermute_zec": "UNKNOWN",
            "inventory": "UNKNOWN",
            "solana_registry_applies": False,
            "note": mm_note.get("note")
            or "Solana MM registry does not apply. Absence ≠ zero inventory.",
        },
        "partial_oi": {
            "binance_usd": binance_oi,
            "bybit_usd": by_oi,
            "okx_usd": okx_usd,
            "partial_sum_usd": partial_oi,
            "global_aggregate": "UNKNOWN",
        },
    }
