"""Canonical HYPE Stage-1 evidence loader — packs only, no silent fallbacks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.paths import REPORTS

STAGE1 = REPORTS / "hype-forensics" / "stage1-evidence"
RAW = STAGE1 / "raw"

STANCE_HEADLINE = "FEES REAL · AF BUYBACKS REAL · RS SOFT"
CG_ID = "hyperliquid"
BINANCE_SYMBOL = "HYPEUSDT"
TOKEN_ID = "0x0d01dc56dcaaca66ad901c959b4011ec"
AF_ADDR = "0xfefefefefefefefefefefefefefefefefefefefe"
HYPERLABS = "0x43e9abea1910387c4292bca4b94de81462f8a251"


class HypeEvidenceError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path, label: str) -> Any:
    data = _load(path)
    if data is None:
        raise HypeEvidenceError(f"Missing required HYPE evidence: {label} ({path.name})")
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


def _metric_map(table: Any) -> dict[str, Any]:
    rows = table if isinstance(table, list) else (table.get("metrics") or [])
    out: dict[str, Any] = {}
    for row in rows:
        if isinstance(row, dict) and row.get("metric"):
            out[str(row["metric"])] = row
    return out


def _require_identity(cg: dict[str, Any], cg_full: dict[str, Any] | None) -> None:
    cg_id = str(cg.get("id") or "").strip().lower()
    if cg_id != CG_ID:
        raise HypeEvidenceError(f"CoinGecko id={cg.get('id')!r} — expected {CG_ID}")
    if cg_full is not None:
        full_id = str(cg_full.get("id") or "").strip().lower()
        if full_id != CG_ID:
            raise HypeEvidenceError(f"cg_hype.json id={cg_full.get('id')!r} — expected {CG_ID}")
        sym = str(cg_full.get("symbol") or "").strip().lower()
        if sym != "hype":
            raise HypeEvidenceError(f"CoinGecko symbol={cg_full.get('symbol')!r} — expected hype")
    contract = str(cg.get("contract") or "").strip().lower()
    if contract and contract != TOKEN_ID:
        raise HypeEvidenceError(f"CG contract={cg.get('contract')!r} — expected {TOKEN_ID}")


def _assert_tickers(tickers: Any) -> int:
    rows = tickers
    if isinstance(tickers, dict):
        rows = tickers.get("tickers") or tickers.get("data") or []
    if not isinstance(rows, list) or not rows:
        raise HypeEvidenceError("CG ticker pack empty or malformed")
    bad = [r for r in rows if isinstance(r, dict) and str(r.get("coin_id") or "") != CG_ID]
    if bad:
        raise HypeEvidenceError(
            f"Foreign CG ticker pack: {len(bad)} rows with coin_id!={CG_ID}"
        )
    bases = {str(r.get("base") or "").upper() for r in rows if isinstance(r, dict)}
    if bases - {"HYPE"}:
        raise HypeEvidenceError(f"CG ticker bases not HYPE-only: {sorted(bases)}")
    return len(rows)


def load_hype_canonical() -> dict[str, Any]:
    table = _require(STAGE1 / "hype-evidence-table.json", "evidence table")
    metrics = _metric_map(table)
    if not metrics:
        raise HypeEvidenceError("hype-evidence-table.json has no metrics")

    cg = _require(RAW / "cg_market_extract.json", "CoinGecko extract")
    cg_full = _load(RAW / "cg_hype.json")
    if not isinstance(cg, dict):
        raise HypeEvidenceError("cg_market_extract.json malformed")
    _require_identity(cg, cg_full if isinstance(cg_full, dict) else None)

    tickers = _require(RAW / "cg_tickers.json", "CG tickers")
    ticker_n = _assert_tickers(tickers)

    td = _require(RAW / "hl_token_details_ncu.json", "HL tokenDetails + NCU")
    if not isinstance(td, dict):
        raise HypeEvidenceError("hl_token_details_ncu.json malformed")
    if str(td.get("name") or "").upper() != "HYPE":
        raise HypeEvidenceError(f"tokenDetails name={td.get('name')!r} — expected HYPE")
    circ_hl = _as_float(td.get("circulatingSupply"))
    total_hl = _as_float(td.get("totalSupply"))
    max_s = _as_float(td.get("maxSupply"))
    fut = _as_float(td.get("futureEmissions"))
    if None in (circ_hl, total_hl, max_s, fut):
        raise HypeEvidenceError("Missing HL circulating/total/max/futureEmissions — cannot pick a circ %")
    ncu: dict[str, float] = {}
    for a, b in td.get("nonCirculatingUserBalances") or []:
        v = _as_float(b)
        if v is None:
            raise HypeEvidenceError(f"Unparseable NCU balance for {a} — will not treat as 0")
        ncu[str(a).lower()] = v
    if AF_ADDR not in ncu:
        raise HypeEvidenceError("Missing AF evidence in NCU — cannot manufacture buyback/inventory state")
    if HYPERLABS not in ncu:
        raise HypeEvidenceError("Missing HyperLabs NCU row — cannot label contributor inventory")
    af_inv = ncu[AF_ADDR]
    labs = ncu[HYPERLABS]
    recon = total_hl - fut - sum(ncu.values())
    if abs(recon - circ_hl) > 1.0:
        raise HypeEvidenceError(
            f"HL circ formula failed: recon={recon} vs circulatingSupply={circ_hl}"
        )

    af_wallets = _require(RAW / "hl_assistance_fund_top_balances.json", "AF balances")
    af_hype = None
    if isinstance(af_wallets, dict):
        rows = af_wallets.get("hype") or []
        if rows:
            af_hype = rows[0]
    if not isinstance(af_hype, dict) or _as_float(af_hype.get("total")) is None:
        raise HypeEvidenceError("Missing AF HYPE inventory — cannot manufacture buyback/inventory state")

    spot = _require(RAW / "binance_spot_HYPEUSDT.json", "Binance.com spot HYPEUSDT")
    if not isinstance(spot, dict):
        raise HypeEvidenceError("Binance spot pack malformed")
    if str(spot.get("requested_symbol") or "").upper() != BINANCE_SYMBOL:
        raise HypeEvidenceError(
            f"Binance spot requested_symbol={spot.get('requested_symbol')!r} — expected {BINANCE_SYMBOL}"
        )
    if int(spot.get("http_code") or 0) != 400:
        raise HypeEvidenceError("Binance.com spot HYPEUSDT is not evidenced as NOT LISTED")
    binance_spot_status = "NOT LISTED"

    fut_pack = _require(RAW / "binance_fut_HYPEUSDT.json", "Binance USDT-M HYPEUSDT")
    if not isinstance(fut_pack, dict):
        raise HypeEvidenceError("Binance perp pack malformed")
    fut_sym = str(fut_pack.get("symbol") or "").upper()
    if fut_sym != BINANCE_SYMBOL:
        raise HypeEvidenceError(f"Binance perp symbol={fut_pack.get('symbol')!r} — expected {BINANCE_SYMBOL}")
    if _as_float(fut_pack.get("lastPrice")) is None:
        raise HypeEvidenceError("Binance perp missing lastPrice — cannot claim PRESENT")
    binance_perp_status = "PRESENT"

    rs = _require(RAW / "rs_binance_aligned.json", "aligned RS")
    if not isinstance(rs, dict):
        raise HypeEvidenceError("rs_binance_aligned.json malformed")
    plat = _require(RAW / "hl_perp_market_snapshot.json", "HL platform perp snapshot")
    if not isinstance(plat, dict):
        raise HypeEvidenceError("hl_perp_market_snapshot.json malformed")
    plat_oi = _as_float(plat.get("open_interest_mark_usd"))
    plat_vol = _as_float(plat.get("day_notional_volume_usd"))
    if plat_oi is None or plat_vol is None:
        raise HypeEvidenceError("Wrong/missing Hyperliquid platform OI/volume response")
    hype_row = plat.get("hype_row") or {}
    if str(hype_row.get("name") or "").upper() != "HYPE":
        raise HypeEvidenceError(
            f"Wrong asset/platform OI response: hype_row name={hype_row.get('name')!r}"
        )
    hype_oi_usd = _as_float(hype_row.get("oi_usd"))
    hype_day_vol = _as_float(hype_row.get("dayNtlVlm"))
    if hype_oi_usd is None:
        raise HypeEvidenceError("Missing native HYPE-token OI — cannot confuse with platform OI")

    fees = _require(RAW / "llama_fees_hl_protocols.json", "fee pack")
    if not isinstance(fees, list) or not fees:
        raise HypeEvidenceError("Missing fee pack — cannot retain old fees")
    fee_map = {str(x.get("name")): x for x in fees if isinstance(x, dict)}
    perps_fees = fee_map.get("Hyperliquid Perps") or {}
    spot_fees = fee_map.get("Hyperliquid Spot Orderbook") or {}
    if _as_float(perps_fees.get("total30d")) is None:
        raise HypeEvidenceError("Perps fee 30d missing")

    recon_pack = _require(RAW / "blocker_pass_reconciliation.json", "circ definition split")
    labeled = (recon_pack.get("live_labeled") or {}) if isinstance(recon_pack, dict) else {}
    own = (recon_pack.get("validator_name_is_not_ownership") or {}) if isinstance(recon_pack, dict) else {}
    stake_ex = _require(RAW / "hl_stake_extract.json", "validator/staking evidence")
    if not isinstance(stake_ex, dict) or _as_float(stake_ex.get("total_stake_hype_assuming_8_decimals")) is None:
        raise HypeEvidenceError("Missing validator/staking evidence — cannot invent stake ownership")

    oi_hist = _require(RAW / "binance_oi_hist_30d.json", "Binance OI hist")
    oi_now = _require(RAW / "binance_oi.json", "Binance OI")
    prem = _require(RAW / "binance_premium.json", "Binance funding")
    snap = _load(RAW / "market_analysis_snapshot.json") or {}
    meta = _load(RAW / "gather_meta.json") or {}
    fetched = str(meta.get("fetched_at") or (snap.get("fetched_at") if isinstance(snap, dict) else "") or "")

    circ_cg = _as_float(cg.get("circ"))
    if circ_cg is None:
        raise HypeEvidenceError("CG circulating missing — cannot silently choose circ %")

    now_usd = _as_float(cg.get("price_usd"))
    if now_usd is None:
        raise HypeEvidenceError("No HYPE price in Stage-1 packs")

    bn = (snap.get("binance") or {}) if isinstance(snap, dict) else {}
    oi_pct = _as_float(bn.get("oi_pct_30d_max"))
    bn_oi_usd = _as_float(bn.get("oi_notional"))
    funding = _as_float((prem.get("data") or prem).get("lastFundingRate") if isinstance(prem, dict) else None)

    fdn = labeled.get("HyperFoundation_genesis60M") or {}
    grant = labeled.get("CommunityGrant_genesis3M") or {}

    return {
        "meta": {
            "fetched_at_utc": fetched,
            "coingecko_id": CG_ID,
            "token_id": TOKEN_ID,
            "assistance_fund": AF_ADDR,
        },
        "price_structure": {
            "now_usd": now_usd,
            "ath_usd": _as_float(cg.get("ath")),
            "ath_date": str(cg.get("ath_date") or "")[:10],
            "drawdown_pct": _as_float(cg.get("ath_change_pct")),
            "mcap_usd": _as_float(cg.get("mcap")),
            "fdv_usd": _as_float(cg.get("fdv")),
            "vol24_usd": _as_float(cg.get("vol24")),
            "returns_pct": (rs.get("hype_returns") or {}),
            "local_high_180": rs.get("local_high_180"),
            "local_low_180": rs.get("local_low_180"),
            "rs_read": "NEAR-TERM MIXED / SOFT · 30d lags BTC+SOL · 90d/180d recovery not current leadership",
            "source_url_cg": "https://www.coingecko.com/en/coins/hyperliquid",
            "source_url_binance": "https://www.binance.com/en/futures/HYPEUSDT",
        },
        "rs_vs_btc_pp": rs.get("rs_vs_btc_pp") or {},
        "rs_vs_sol_pp": rs.get("rs_vs_sol_pp") or {},
        "spot_liquidity": {
            "binance_com_spot": binance_spot_status,
            "binance_perp": binance_perp_status,
            "binance_perp_symbol": BINANCE_SYMBOL,
            "cg_ticker_rows": ticker_n,
            "note": (
                "Binance.com spot HYPEUSDT NOT LISTED. Binance USDT-M PRESENT. "
                "Binance US on CG tickers is not Binance.com spot. Multi-CEX + native HL books exist."
            ),
            "source_url": "https://www.coingecko.com/en/coins/hyperliquid",
        },
        "leverage": {
            "platform_oi_usd": plat_oi,
            "platform_day_notional_usd": plat_vol,
            "hype_token_oi_usd": hype_oi_usd,
            "hype_token_oi_tokens": _as_float(hype_row.get("oi_tokens")),
            "hype_token_day_notional_usd": hype_day_vol,
            "hype_token_max_leverage": 10,
            "hype_token_funding": _as_float(hype_row.get("funding")),
            "binance_oi_usd": bn_oi_usd,
            "binance_oi_tokens": _as_float((oi_now.get("data") or oi_now).get("openInterest") if isinstance(oi_now, dict) else None),
            "binance_oi_pct_30d_max": oi_pct,
            "binance_funding": funding,
            "binance_perp_quote_vol_24h": _as_float(fut_pack.get("quoteVolume")),
            "read": "HYPE-TOKEN LEVERAGE MATERIAL ON NATIVE HL · platform OI is not HYPE-token OI",
            "note": (
                "Do not use ~$7.3B platform OI as HYPE-token OI. "
                "Native HYPE perp OI ~$1.24B. Binance HYPE perp ~$278M. "
                "OI elevated vs own 30d history is context, not a top. Positive funding ≠ top."
            ),
            "source_url": "https://api.hyperliquid.xyz/info",
        },
        "supply": {
            "max_supply": max_s,
            "hl_total_supply": total_hl,
            "hl_circulating": circ_hl,
            "hl_circulating_pct": circ_hl / max_s * 100.0,
            "cg_circulating": circ_cg,
            "cg_circulating_pct": circ_cg / max_s * 100.0,
            "future_emissions": fut,
            "hyperlabs_ncu": labs,
            "af_inventory": af_inv,
            "foundation_wallet_sum": _as_float(fdn.get("sum")),
            "grant_wallet_sum": _as_float(grant.get("sum")),
            "dddd_live": 0.0,
            "definition": "CONFLICT LOCKED / DEFINITION SPLIT",
            "hl_formula": "circulatingSupply = totalSupply − futureEmissions − sum(NCU)",
            "unlock_3m": "UNKNOWN",
            "unlock_6m": "UNKNOWN",
            "unlock_12m": "UNKNOWN",
            "linear_monthly_forbidden": True,
            "implied_total_supply_reduction": max_s - total_hl,
            "display_rule": (
                "Show CG 22.2% AND Hyperliquid 29.9%. Never average. Never pick one. "
                "3/6/12m release UNKNOWN. Do not invent 9.92M/month."
            ),
            "source_url": "https://api.hyperliquid.xyz/info",
        },
        "value_capture": {
            "mechanism": "KNOWN",
            "measured_scale": "PARTIAL",
            "holder_capture": "PARTIAL",
            "buyback": "KNOWN",
            "circ_exclusion": "KNOWN",
            "total_supply_burn": "CONFLICT",
            "af_inventory": af_inv,
            "af_staked": 0.0,
            "production_wording": "ASSISTANCE-FUND BUYBACKS REAL · BURN ACCOUNTING UNRESOLVED",
            "note": (
                "Fees fund automated HYPE purchases into the Assistance Fund. "
                "Protocol fees ≠ token-holder yield. AF inventory is not destroyed supply. "
                "AF inventory is excluded from circulating supply and still sits at 0xfefe."
            ),
            "source_url": "https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees",
        },
        "fees": {
            "perps_24h": _as_float(perps_fees.get("total24h")),
            "perps_7d": _as_float(perps_fees.get("total7d")),
            "perps_30d": _as_float(perps_fees.get("total30d")),
            "perps_change_7d": _as_float(perps_fees.get("change_7d")),
            "perps_change_1m": _as_float(perps_fees.get("change_1m")),
            "perps_change_30dover30d": _as_float(perps_fees.get("change_30dover30d")),
            "spot_24h": _as_float(spot_fees.get("total24h")),
            "spot_7d": _as_float(spot_fees.get("total7d")),
            "spot_30d": _as_float(spot_fees.get("total30d")),
            "spot_change_1m": _as_float(spot_fees.get("change_1m")),
            "read": "USAGE / FEES REAL AND LARGE · NEAR-TERM DECELERATING VS OWN RECENT MONTH",
            "source_url": "https://api.llama.fi/summary/fees/hyperliquid-perp",
        },
        "staking": {
            "n_validators": stake_ex.get("n_validators"),
            "n_active": stake_ex.get("n_active"),
            "total_stake_hype": _as_float(stake_ex.get("total_stake_hype_assuming_8_decimals")),
            "foundation_named_stake": _as_float(
                (recon_pack.get("foundation_named_validators") or {}).get("stake_hype")
            ),
            "hyperlabs_to_foundation_vals": _as_float(own.get("hyperlabs_delegated_to_foundation_named_vals")),
            "foundation_wallet_to_foundation_vals": _as_float(
                own.get("foundation_wallet_delegated_to_foundation_named_vals")
            ),
            "grants_to_foundation_vals": _as_float(own.get("grant_wallet_delegated_to_foundation_named_vals")),
            "other_delegators": _as_float(own.get("remainder_other_delegators")),
            "note": "VALIDATOR NAME ≠ BENEFICIAL OWNERSHIP. Staked ≠ sold. Do not say Foundation owns 212.5M.",
        },
        "ownership": {
            "read": "PROTOCOL/SYSTEM INVENTORY PARTIAL · DISCRETIONARY HOLDER CONCENTRATION UNKNOWN",
            "af": af_inv,
            "hyperlabs": labs,
            "foundation_wallet": _as_float(fdn.get("sum")),
            "grants": _as_float(grant.get("sum")),
            "discretionary_concentration": "UNKNOWN",
            "raw_top_holders": "UNKNOWN",
        },
        "capital_flow": {
            "evidenced_buyer": "ASSISTANCE FUND — automated fee-funded. Not organic demand.",
            "other_buyers": "UNKNOWN",
            "sellers": "UNKNOWN",
            "cex_flows": "UNKNOWN",
            "note": "TRANSFER ≠ SALE. CEX deposit ≠ sale. AF buying ≠ organic demand.",
        },
        "mm": {
            "status": "UNKNOWN",
            "inventory": None,
            "note": (
                "Shared Solana/EVM registry does not cover HyperCore. "
                "Absence of applicable identities ≠ proven zero inventory. "
                "Do not render ZERO MM INVENTORY."
            ),
        },
        "hyperevm": "UNKNOWN",
        "daily_af_buys": "UNKNOWN",
        "oi_hist_n": len((oi_hist.get("data") or [])) if isinstance(oi_hist, dict) else None,
    }
