"""Canonical FARTCOIN Stage-1 evidence loader — packs only, no silent fallbacks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.paths import REPORTS

STAGE1 = REPORTS / "fartcoin-forensics" / "stage1-evidence"
RAW = STAGE1 / "raw"

STANCE_HEADLINE = "STRUCTURE WEAK · LEV MATERIAL · OWNERS UNKNOWN"
SUPPLY_READ = "FLOAT CLEAN"
MINT = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"


class FartcoinEvidenceError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path, label: str) -> Any:
    data = _load(path)
    if data is None:
        raise FartcoinEvidenceError(f"Missing required FARTCOIN evidence: {label} ({path})")
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


def load_fartcoin_canonical() -> dict[str, Any]:
    evidence_table = _require(STAGE1 / "fartcoin-evidence-table.json", "evidence table")
    metrics = _metric_map(evidence_table if isinstance(evidence_table, dict) else {})
    if not metrics:
        raise FartcoinEvidenceError("fartcoin-evidence-table.json has no metrics")

    ps = _require(RAW / "fart-price-structure.json", "price structure")
    cg = _require(RAW / "cg-market-extract.json", "CoinGecko extract")
    lev = _require(RAW / "fart-leverage-snapshot.json", "leverage snapshot")
    mint = _require(RAW / "fart-mint-authorities.json", "mint authorities")
    top = _require(RAW / "fart-top20-classified.json", "top20 holders")
    dx = _load(RAW / "fart-dex-sample-summary.json") or {}
    # Data Trust: MM evidence required for visible inventory claim — never invent zero
    mm = _require(RAW / "mm-fart-balances.json", "MM balances")
    if not isinstance(mm, list):
        raise FartcoinEvidenceError("mm-fart-balances.json must be a list")

    now_usd = _as_float(cg.get("price_usd")) or _as_float(ps.get("spot_close_usd"))
    if now_usd is None:
        raise FartcoinEvidenceError("No FARTCOIN price in Stage-1 packs")

    max_supply = _as_float(cg.get("max"))
    if max_supply is None:
        max_row = metrics.get("max_supply") or {}
        max_supply = _as_float(max_row.get("value"))
    # Data Trust: no silent 1B fallback
    circ = _as_float(cg.get("circulating"))
    if circ is None:
        circ_row = metrics.get("circulating_supply") or {}
        circ = _as_float(circ_row.get("value"))

    rets = ps.get("returns_pct") or {}
    rs_map = ps.get("rs_vs_pct") or {}

    def _rs_pair(asset: str) -> dict[str, float | None]:
        out: dict[str, float | None] = {}
        for d in ("7", "30", "90", "180"):
            block = rs_map.get(d) or rs_map.get(int(d)) or {}
            out[d] = _as_float(block.get(asset)) if isinstance(block, dict) else None
        return out

    as_of = ps.get("as_of") or evidence_table.get("gathered_at")
    if not as_of:
        raise FartcoinEvidenceError("No as_of on FARTCOIN Stage-1 packs")

    mint_auth = mint.get("mintAuthority")
    freeze_auth = mint.get("freezeAuthority")
    # Explicit null from on-chain = revoked; missing key = UNKNOWN
    if "mintAuthority" not in mint:
        raise FartcoinEvidenceError("mintAuthority missing from Stage-1 mint pack")
    if "freezeAuthority" not in mint:
        raise FartcoinEvidenceError("freezeAuthority missing from Stage-1 mint pack")

    # Data Trust: no silent FARTCOINUSDT / ABSENT / PRESENT invention
    binance_perp_symbol = lev.get("binance_perp_symbol")
    binance_spot_status = lev.get("binance_spot")
    if not binance_perp_symbol:
        raise FartcoinEvidenceError("binance_perp_symbol missing from leverage snapshot")
    if not binance_spot_status:
        raise FartcoinEvidenceError("binance_spot missing from leverage snapshot")

    # Binance perp PRESENT only if Stage-1 perp ticker evidence exists
    binance_perp_24h = _require(RAW / "binance-fart-perp-24h.json", "Binance perp 24h")
    if not isinstance(binance_perp_24h, dict) or binance_perp_24h.get("code"):
        raise FartcoinEvidenceError("Binance perp 24h evidence is not a live ticker")
    if binance_perp_24h.get("lastPrice") is None:
        raise FartcoinEvidenceError("Binance perp lastPrice missing — cannot claim PRESENT")
    binance_perp_status = "PRESENT"

    # Coinbase spot PRESENT only if Stage-1 Coinbase ticker evidence exists
    coinbase_ticker = _require(RAW / "coinbase-fart-ticker.json", "Coinbase spot ticker")
    if not isinstance(coinbase_ticker, dict):
        raise FartcoinEvidenceError("Coinbase spot ticker evidence malformed")
    if (
        _as_float(coinbase_ticker.get("price")) is None
        and _as_float(coinbase_ticker.get("volume")) is None
    ):
        raise FartcoinEvidenceError(
            "Coinbase ticker missing price/volume — cannot claim PRESENT"
        )
    coinbase_spot_status = "PRESENT"

    wm_hits = [
        x
        for x in mm
        if isinstance(x, dict) and x.get("entity") == "Wintermute"
    ]
    if not wm_hits:
        raise FartcoinEvidenceError(
            "MM balances pack has no Wintermute rows — cannot invent zero inventory"
        )
    wm_bal = 0.0
    for x in wm_hits:
        b = _as_float(x.get("fartcoin"))
        if b is None:
            raise FartcoinEvidenceError("Wintermute row missing fartcoin balance")
        if b > wm_bal:
            wm_bal = b

    pool_path = RAW / "top-pool.txt"
    top_pool = pool_path.read_text(encoding="utf-8").strip() if pool_path.exists() else None

    return {
        "meta": {
            "fetched_at_utc": as_of,
            "paths": {
                "findings": "reports/fartcoin-forensics/stage1-evidence/FARTCOIN-STAGE1-FINDINGS.md",
                "evidence_table": "reports/fartcoin-forensics/stage1-evidence/fartcoin-evidence-table.json",
            },
            "evidence_metric_count": len(metrics),
            "stance_locked": STANCE_HEADLINE,
            "supply_read_locked": SUPPLY_READ,
            "mint": MINT,
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
            "method_note": (
                "CoinGecko for spot/ATH/mcap; Coinbase daily candles for returns/RS. "
                "SMA descriptive only — not a trading rule. Priority RS = 7d/30d/90d."
            ),
            "source_url_cg": "https://www.coingecko.com/en/coins/fartcoin",
            "source_url_coinbase": "https://www.coinbase.com/price/fartcoin",
        },
        "rs_vs_btc_pp": _rs_pair("btc"),
        "rs_vs_sol_pp": _rs_pair("sol"),
        "rs_vs_pump_pp": _rs_pair("pump"),
        "rs_vs_spx_pp": _rs_pair("spx"),
        "spot_liquidity": {
            "binance_spot": binance_spot_status,
            "binance_perp": binance_perp_status,
            "coinbase_spot": coinbase_spot_status,
            "cg_vol24_usd": _as_float(cg.get("vol24_usd")),
            "coinbase_vol24_usd": _as_float(lev.get("cg_coinbase_vol_24h")),
            "top_raydium_pool": top_pool,
            "top_pool_liq_usd": _as_float((metrics.get("dex_top_pool_liq") or {}).get("value")),
            "read": "REAL SPOT EXISTS · BINANCE PRIMARY MARKET IS PERP",
            "note": (
                "Do not call FARTCOIN perp-only. Coinbase + DEX + other CEX spot exist. "
                f"Binance spot from leverage pack: {binance_spot_status}; "
                f"Binance perp from binance-fart-perp-24h.json + symbol {binance_perp_symbol}; "
                "Coinbase spot from coinbase-fart-ticker.json."
            ),
            "source_url": "https://www.coingecko.com/en/coins/fartcoin",
        },
        "leverage": {
            "read": "LEVERAGE MATERIAL",
            "binance_perp_symbol": binance_perp_symbol,
            "binance_spot": binance_spot_status,
            "oi_tokens": _as_float(lev.get("oi_tokens")),
            "oi_usd_approx": _as_float(lev.get("oi_usd_approx")),
            "perp_quote_vol_24h": _as_float(lev.get("perp_quote_vol_24h")),
            "funding_rate": _as_float(lev.get("funding_rate")),
            "perp_vs_coinbase_spot_ratio": _as_float(lev.get("perp_vs_coinbase_spot_ratio")),
            "oi_hist_30d_start_usd": _as_float(lev.get("oi_hist_30d_start_usd")),
            "oi_hist_30d_end_usd": _as_float(lev.get("oi_hist_30d_end_usd")),
            "ratio_label": (
                "BINANCE PERP VOLUME vs COINBASE SPOT COMPARATOR — not global futures/spot"
            ),
            "ratio_confidence": "MEDIUM",
            "note": (
                "OI rising ≠ bearish. Mild positive funding ≠ top. "
                "OI stable/up + soft price = mixed. Multi-venue OI aggregate UNKNOWN."
            ),
            "multi_venue_oi_aggregate": "UNKNOWN",
            "source_url": f"https://www.binance.com/en/futures/{binance_perp_symbol}",
        },
        "supply": {
            "max_supply": max_supply,
            "circulating": circ,
            "circulating_pct_of_max": (float(circ) / float(max_supply) * 100.0)
            if circ is not None and max_supply
            else None,
            "mint_authority": mint_auth,
            "freeze_authority": freeze_auth,
            "mint_authority_status": "REVOKED" if mint_auth is None else "PRESENT",
            "freeze_authority_status": "REVOKED" if freeze_auth is None else "PRESENT",
            "pressure_read": SUPPLY_READ,
            "vesting_unlocks": "UNKNOWN",
            "team_treasury_allocation": "UNKNOWN",
            "creator_holdings": "UNKNOWN",
            "display_rule": (
                "FLOAT CLEAN = almost all max supply circulating + mint/freeze revoked. "
                "Says nothing about who owns existing tokens. "
                "Fully circulating ≠ decentralised ownership."
            ),
            "source_url": "https://www.coingecko.com/en/coins/fartcoin",
        },
        "ownership": {
            "top20_raw_pct": _as_float(top.get("top20_pct")),
            "top20_sum": _as_float(top.get("top20_sum")),
            "adjusted_discretionary_pct": None,
            "adjusted_status": "UNKNOWN",
            "unclassified_in_top20": sum(
                1
                for r in (top.get("rows") or [])
                if isinstance(r, dict) and r.get("kind") == "unclassified_token_account"
            ),
            "read": "RAW CONCENTRATION HIGH · ADJUSTED DISCRETIONARY UNKNOWN",
            "note": (
                "Do not label raw top-20 as whale control. Accounts may be CEX/LP/program/"
                "discretionary/other. Adjusted concentration UNKNOWN."
            ),
            "source_url": "https://solana.com/docs/rpc/http/gettokenlargestaccounts",
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
                "Bounded GeckoTerminal sample on top Raydium pool only — not market-wide. "
                "TRANSFER ≠ SALE. CEX deposit ≠ SALE."
            ),
            "source_url": (
                f"https://www.geckoterminal.com/solana/pools/{top_pool}" if top_pool else None
            ),
        },
        "mm": {
            "read": "SMALL VERIFIED WINTERMUTE INVENTORY",
            "wintermute_fartcoin": wm_bal,
            "wintermute_pct_supply": (wm_bal / float(circ) * 100.0) if circ and wm_bal else None,
            "warning": False,
            "note": (
                "Inventory observation only. MM interaction ≠ suppression. "
                "OTC interaction ≠ sale. Not a dump/short narrative."
            ),
        },
        "creator": {
            "status": "UNKNOWN",
            "note": (
                "Pump.fun-style mint suffix is consistent with pump.fun launch path, "
                "but deployer/creator/early-wallet attribution is not verified. "
                "Early wallet ≠ insider."
            ),
        },
        "reflexivity": {
            "status": "UNKNOWN",
            "known": [
                "Remains actively traded after ~95% ATH drawdown",
                "Multi-million USD daily volume persists",
                "Listed across real venues",
                "Current RS vs SOL is weak",
            ],
            "note": "No clean attention time-series in Stage 1. Do not invent social metrics.",
        },
    }
