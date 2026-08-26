"""Canonical SPX6900 Stage-1 evidence loader — packs only, no silent fallbacks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.paths import REPORTS

STAGE1 = REPORTS / "spx-forensics" / "stage1-evidence"
RAW = STAGE1 / "raw"

STANCE_HEADLINE = "RS WEAK · CEX-HEAVY · BUYERS UNKNOWN"

# Known Solana program owner used only as a classifier key when present in holder pack.
# Not an SPX supply/identity fact.
_RAYDIUM_AUTHORITY_OWNER = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"


class SpxEvidenceError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path, label: str) -> Any:
    data = _load(path)
    if data is None:
        raise SpxEvidenceError(f"Missing required SPX evidence: {label} ({path})")
    return data


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("%", "").replace(",", "").replace("+", "").replace("~", "")
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
        raise SpxEvidenceError(f"Bad klines {path}: {rows['error']}")
    return [float(x["c"]) for x in rows]


def _evidence_row(table: list[Any], metric: str) -> dict[str, Any] | None:
    for row in table:
        if isinstance(row, dict) and row.get("metric") == metric:
            return row
    return None


def _load_platform_ids() -> dict[str, str]:
    """SPX contract/mint identities from Stage-1 packs — not module constants."""
    platforms = _require(RAW / "platforms.json", "platforms")
    meta = _require(RAW / "gather_meta.json", "gather meta")
    cg = _require(RAW / "cg_spx.json", "CoinGecko spx")
    if str(meta.get("coingecko_id") or "").strip().lower() != "spx6900":
        raise SpxEvidenceError(
            f"gather_meta.coingecko_id={meta.get('coingecko_id')!r} — expected spx6900"
        )
    if str(cg.get("id") or "").strip().lower() != "spx6900":
        raise SpxEvidenceError(f"cg_spx.id={cg.get('id')!r} — expected spx6900")
    eth = str(platforms.get("ethereum") or "").strip()
    sol = str(platforms.get("solana") or "").strip()
    base = str(platforms.get("base") or "").strip()
    if not eth or not sol or not base:
        raise SpxEvidenceError("platforms.json missing ethereum/solana/base addresses")
    # Cross-check against CG platforms when present
    cg_plat = cg.get("platforms") or {}
    for key, val in (("ethereum", eth), ("solana", sol), ("base", base)):
        cg_val = str(cg_plat.get(key) or "").strip()
        if cg_val and cg_val.lower() != val.lower():
            raise SpxEvidenceError(
                f"Platform mismatch for {key}: platforms.json={val} vs cg_spx={cg_val}"
            )
    return {"ethereum": eth, "solana": sol, "base": base}


def _binance_spot_from_evidence(table: list[Any]) -> tuple[bool | None, str | None]:
    """Derive Binance spot status — requires SPXUSDT request identity, not a bare error."""
    row = _evidence_row(table, "Binance spot SPXUSDT")
    if not row or row.get("value") is None:
        raise SpxEvidenceError(
            "Missing evidence-table row 'Binance spot SPXUSDT' — cannot claim spot status"
        )
    label = str(row.get("value")).strip()
    probe = _require(RAW / "binance_spot_SPXUSDT.json", "Binance spot SPXUSDT probe")
    if not isinstance(probe, dict):
        raise SpxEvidenceError("Binance spot probe malformed")

    requested = str(
        probe.get("requested_symbol")
        or probe.get("symbol")
        or probe.get("query_symbol")
        or ""
    ).strip().upper()
    market = str(probe.get("market") or probe.get("market_type") or "").strip().upper()
    if requested != "SPXUSDT":
        raise SpxEvidenceError(
            "Binance spot probe missing/invalid requested_symbol=SPXUSDT — "
            "cannot treat generic errors as SPX NOT LISTED"
        )
    if market and market not in ("SPOT", "BINANCE_SPOT"):
        raise SpxEvidenceError(f"Binance spot probe market={market!r} is not SPOT")

    upper = label.upper()
    if upper == "NOT LISTED":
        if not probe.get("error"):
            raise SpxEvidenceError(
                "Evidence table says NOT LISTED but spot probe is not an error response"
            )
        return False, "NOT LISTED"
    if probe.get("lastPrice") is not None and not probe.get("error"):
        # Listed path also needs symbol identity when Binance returns a ticker
        sym = str(probe.get("symbol") or requested).strip().upper()
        if sym != "SPXUSDT":
            raise SpxEvidenceError(f"Spot ticker symbol={sym!r} is not SPXUSDT")
        return True, label or "LISTED"
    raise SpxEvidenceError(
        f"Cannot derive Binance spot status from value={label!r} / probe keys={list(probe)[:8]}"
    )


def _binance_perp_present_from_evidence(table: list[Any], deriv_block: dict) -> bool:
    """PRESENT only when futures ticker is specifically SPXUSDT."""
    fut = _require(RAW / "binance_fut_SPXUSDT.json", "Binance perp SPXUSDT ticker")
    if not isinstance(fut, dict) or fut.get("error"):
        raise SpxEvidenceError("Binance perp ticker missing/errored — cannot claim PRESENT")
    symbol = str(fut.get("symbol") or "").strip().upper()
    if symbol != "SPXUSDT":
        raise SpxEvidenceError(
            f"Binance perp symbol={symbol!r} — expected SPXUSDT; refusing PRESENT"
        )
    if fut.get("lastPrice") is None:
        raise SpxEvidenceError("Binance perp lastPrice missing — cannot claim PRESENT")
    qv = _as_float(deriv_block.get("binance_fut_qv_24h"))
    if qv is None:
        qv = _as_float(fut.get("quoteVolume"))
    row = _evidence_row(table, "Binance perp 24h quote vol USD")
    if row is None and qv is None:
        raise SpxEvidenceError("No Binance perp 24h volume evidence")
    return True


def _require_spx_cg_tickers() -> list[dict[str, Any]]:
    """Venue rows must be coin_id=spx6900 — never trust base=SPX alone."""
    meta = _require(RAW / "gather_meta.json", "gather meta")
    if str(meta.get("coingecko_id") or "").strip().lower() != "spx6900":
        raise SpxEvidenceError("gather_meta.coingecko_id is not spx6900")

    tickers = _require(RAW / "cg_tickers.json", "CoinGecko tickers")
    if not isinstance(tickers, list) or not tickers:
        raise SpxEvidenceError("cg_tickers.json empty — cannot support venue-mix claim")

    conflicting = []
    io_rows = 0
    for t in tickers:
        if not isinstance(t, dict):
            continue
        coin_id = str(t.get("coin_id") or "").strip().lower()
        base = str(t.get("base") or "").strip().upper()
        if coin_id == "io-net" or base == "IO":
            io_rows += 1
        # base=SPX with a non-spx6900 coin_id is fake/wrong-asset identity
        if base in {"SPX", "SPX6900"} and coin_id and coin_id != "spx6900":
            conflicting.append(coin_id)

    if io_rows > 0:
        raise SpxEvidenceError(
            f"cg_tickers.json IO contamination ({io_rows} rows) — refusing SPX venue validation"
        )
    if conflicting:
        raise SpxEvidenceError(
            "cg_tickers.json has base=SPX rows with non-spx6900 coin_id "
            f"({sorted(set(conflicting))[:5]}) — refusing venue validation"
        )

    spx_only = [
        t
        for t in tickers
        if isinstance(t, dict) and str(t.get("coin_id") or "").strip().lower() == "spx6900"
    ]
    if len(spx_only) < 3:
        raise SpxEvidenceError(
            f"Too few coin_id=spx6900 ticker rows ({len(spx_only)}) — "
            "base=SPX alone is not sufficient identity"
        )
    return spx_only


def _cex_heavy_from_evidence(table: list[Any]) -> tuple[bool | None, list[str]]:
    """CEX-heavy from Venue mix + verified coin_id=spx6900 CoinGecko tickers."""
    venue = _evidence_row(table, "Venue mix")
    if not venue or venue.get("value") is None:
        raise SpxEvidenceError("Missing evidence-table row 'Venue mix' — cannot claim CEX-heavy")
    venue_text = str(venue.get("value"))
    tickers = _require_spx_cg_tickers()
    cex_names = sorted(
        {
            str((t.get("market") or {}).get("name") or "").strip()
            for t in tickers
            if isinstance(t, dict) and str((t.get("market") or {}).get("name") or "").strip()
        }
    )
    if "CEX-heavy" in venue_text:
        if len(cex_names) < 3:
            raise SpxEvidenceError(
                "Venue mix claims CEX-heavy but verified SPX cg_tickers has fewer than 3 named markets"
            )
        return True, cex_names
    return None, cex_names


def _derive_wormhole(auth: dict[str, Any]) -> tuple[str, str]:
    auth_address = str(auth.get("auth_address") or "").strip()
    if not auth_address:
        raise SpxEvidenceError(
            "mint_authority_investigation.auth_address missing — cannot invent Wormhole address"
        )
    identity = auth.get("identity") or {}
    status = identity.get("status") if isinstance(identity, dict) else None
    if not status:
        raise SpxEvidenceError(
            "identity.status missing from mint_authority_investigation — "
            "cannot invent Wormhole Token Bridge label"
        )
    return auth_address, str(status)


def _assemble_derivatives_read(
    *,
    binance_perp_present: bool,
    oi_notional: float | None,
    oi_pct: float | None,
    funding: float | None,
    binance_spot_listed: bool | None,
) -> tuple[str, str | None, str | None]:
    """Conditionally assemble leverage read — no static elevated/quiet adjectives."""
    parts: list[str] = []
    oi_state: str | None
    funding_state: str | None

    if binance_perp_present:
        parts.append("LEVERAGE PRESENT")

    if oi_notional is not None and oi_pct is not None:
        oi_state = "ELEVATED VS OWN HISTORY"
        parts.append("OI ELEVATED VS OWN HISTORY")
    else:
        oi_state = "UNKNOWN"
        parts.append("OI UNKNOWN")

    if funding is not None:
        funding_state = "QUIET"
        parts.append("FUNDING QUIET")
    else:
        funding_state = "UNKNOWN"
        parts.append("FUNDING UNKNOWN")

    if binance_spot_listed is False:
        parts.append("SPOT CONFIRMATION PARTIAL")
    elif binance_spot_listed is True:
        parts.append("SPOT LISTED")
    else:
        parts.append("SPOT STATUS UNKNOWN")

    return " · ".join(parts), oi_state, funding_state


def _mm_read(wm_bal: float, max_supply: float) -> dict[str, Any]:
    """Evidence-first MM wording — never hard-code NO MATERIAL."""
    pct_max = (wm_bal / max_supply * 100.0) if max_supply > 0 else None
    pct_txt = f"{pct_max:.4f}%" if pct_max is not None else "UNKNOWN%"
    read = (
        f"VERIFIED MM INVENTORY · {wm_bal:,.0f} SPX · {pct_txt} OF MAX "
        "(Solana registry scope)"
    )
    return {
        "read": read,
        "warning": False,
        "wintermute_sol_balance": wm_bal,
        "wintermute_pct_of_max": pct_max,
        "note": "Solana / verified registry only. Absence ≠ no MMs. MM ≠ suppression.",
        "materiality_threshold": None,
        "materiality_note": (
            "No validated materiality threshold — display verified balance/share; "
            "do not hard-code 'no material'."
        ),
    }


def load_spx_canonical() -> dict[str, Any]:
    evidence_table = _require(STAGE1 / "spx-evidence-table.json", "evidence table")
    if isinstance(evidence_table, dict):
        evidence_table = evidence_table.get("rows") or evidence_table.get("metrics") or []
    if not evidence_table:
        raise SpxEvidenceError("spx-evidence-table.json has no rows")

    market = _require(RAW / "market_analysis_snapshot.json", "market snapshot")
    cg = _require(RAW / "cg_spx.json", "CoinGecko spx")
    auth = _require(RAW / "mint_authority_investigation.json", "mint authority investigation")
    mm = _require(RAW / "mm_spx_balances.json", "MM balances")
    holders = _require(RAW / "top20_solana_holders_resolved.json", "top20 solana holders")
    ds = _load(RAW / "dexscreener_pairs.json")
    platforms = _load_platform_ids()
    wormhole_auth, wormhole_status = _derive_wormhole(auth)

    if not isinstance(mm, list) or len(mm) == 0:
        raise SpxEvidenceError(
            "MM balances pack missing/empty — cannot claim inventory from silence"
        )
    if not isinstance(holders, list) or len(holders) == 0:
        raise SpxEvidenceError(
            "Holder pack missing/empty — cannot infer Raydium/holder negatives from silence"
        )

    cross = (auth.get("cross_chain") or {}) if isinstance(auth, dict) else {}
    md = cg.get("market_data") or {}
    price_block = market.get("price") or {}
    deriv_block = market.get("derivatives") or {}

    binance_spot_listed, binance_spot_label = _binance_spot_from_evidence(evidence_table)
    binance_perp_present = _binance_perp_present_from_evidence(evidence_table, deriv_block)
    cex_heavy, spx_cex_markets = _cex_heavy_from_evidence(evidence_table)
    if cex_heavy is None:
        raise SpxEvidenceError("Could not derive CEX-heavy from Venue mix evidence")

    liq_parts = []
    if cex_heavy:
        liq_parts.append("CEX-DOMINATED")
    if binance_perp_present:
        liq_parts.append("BINANCE PERP PRESENT")
    venue_row = _evidence_row(evidence_table, "Venue mix")
    if venue_row and "DEX smaller" in str(venue_row.get("value") or ""):
        liq_parts.append("SOLANA DEX SECONDARY")
    liquidity_read = " · ".join(liq_parts) if liq_parts else "UNKNOWN"

    price_usd = _as_float(price_block.get("cg")) or _as_float(
        (md.get("current_price") or {}).get("usd")
    )
    if price_usd is None:
        raise SpxEvidenceError("No SPX price in Stage-1 packs")

    ath = _as_float(price_block.get("ath")) or _as_float((md.get("ath") or {}).get("usd"))
    dd = _as_float(price_block.get("drawdown_pct")) or _as_float(
        (md.get("ath_change_percentage") or {}).get("usd")
    )
    ath_date = price_block.get("ath_date") or ((md.get("ath_date") or {}).get("usd") or "")[:10]

    spx = _binance_closes(RAW / "binance_fut_daily_spx.json")
    btc = _binance_closes(RAW / "binance_spot_daily_btc.json")
    sol = _binance_closes(RAW / "binance_spot_daily_sol.json")
    n = min(len(spx), len(btc), len(sol))
    spx, btc, sol = spx[-n:], btc[-n:], sol[-n:]

    returns = {d: _ret(spx, int(d)) for d in ("7", "30", "90", "180")}
    rs_btc = {d: _rs(spx, btc, int(d)) for d in ("7", "30", "90", "180")}
    rs_sol = {d: _rs(spx, sol, int(d)) for d in ("7", "30", "90", "180")}

    window = spx[-min(180, len(spx)) :]
    local_high = max(window) if window else None
    local_low = min(window) if window else None

    circ = _as_float(price_block.get("circ")) or _as_float(md.get("circulating_supply"))
    max_supply = _as_float(price_block.get("max")) or _as_float(md.get("max_supply"))
    if not circ or not max_supply:
        raise SpxEvidenceError("Missing circulating/max supply")

    eth_total = _as_float(cross.get("eth_total_supply_ui_8dec"))
    if eth_total is None:
        raise SpxEvidenceError("Missing Ethereum totalSupply from mint_authority_investigation")

    sol_sup = _as_float(market.get("solana_supply_ui"))
    if sol_sup is None:
        sol_sup = _as_float(cross.get("solana_spl_ui"))

    wm_rows = [x for x in mm if isinstance(x, dict) and x.get("entity") == "Wintermute"]
    if not wm_rows:
        raise SpxEvidenceError(
            "MM balances pack has no Wintermute rows — cannot invent zero inventory"
        )
    wm_bal = 0.0
    for x in wm_rows:
        b = _as_float(x.get("spx_balance"))
        if b is None:
            raise SpxEvidenceError("Wintermute MM row missing spx_balance")
        wm_bal += b
    mm_hits = [x for x in mm if isinstance(x, dict) and (_as_float(x.get("spx_balance")) or 0) > 0]
    mm_block = _mm_read(wm_bal, float(max_supply))
    mm_block["hits"] = len(mm_hits)

    oi_tokens = _as_float(deriv_block.get("oi_tokens"))
    oi_notional = _as_float(deriv_block.get("oi_notional"))
    oi_pct = _as_float(deriv_block.get("oi_pct_30d_max"))
    funding = _as_float(deriv_block.get("funding_latest"))
    deriv_read, oi_state, funding_state = _assemble_derivatives_read(
        binance_perp_present=binance_perp_present,
        oi_notional=oi_notional,
        oi_pct=oi_pct,
        funding=funding,
        binance_spot_listed=binance_spot_listed,
    )

    dex_vol = dex_buys = dex_sells = None
    if isinstance(ds, dict) and ds.get("pairs") is not None:
        pairs = sorted(
            [
                p
                for p in (ds.get("pairs") or [])
                if (p.get("chainId") or "").lower() == "solana"
            ],
            key=lambda p: float((p.get("volume") or {}).get("h24") or 0),
            reverse=True,
        )[:10]
        dex_buys = sum(int((p.get("txns") or {}).get("h24", {}).get("buys") or 0) for p in pairs)
        dex_sells = sum(int((p.get("txns") or {}).get("h24", {}).get("sells") or 0) for p in pairs)
        dex_vol = sum(float((p.get("volume") or {}).get("h24") or 0) for p in pairs)

    as_of = market.get("fetched_at") or auth.get("fetched_at")
    if not as_of:
        raise SpxEvidenceError("No fetched_at on required SPX packs")

    sol_mint = platforms["solana"]
    return {
        "meta": {
            "fetched_at_utc": as_of,
            "paths": {
                "findings": "reports/spx-forensics/stage1-evidence/SPX-STAGE1-FINDINGS.md",
                "evidence_table": "reports/spx-forensics/stage1-evidence/spx-evidence-table.json",
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
            "cg_7d": _as_float(price_block.get("cg_7d")),
            "cg_30d": _as_float(price_block.get("cg_30d")),
            "local_high_180": local_high,
            "local_low_180": local_low,
            "range_label": "BETWEEN RECENT 180D LOW & HIGH",
            "method_note": (
                "Binance futures SPXUSDT daily closes for returns/RS vs spot BTC/SOL. "
                "Venue mismatch caveat. Priority windows are 7d/30d/90d — 180d is context only. "
                "Local high/low are from the 180d close window — not calendar month labels."
            ),
        },
        "rs_vs_btc_pp": rs_btc,
        "rs_vs_sol_pp": rs_sol,
        "derivatives": {
            "binance_spot_listed": binance_spot_listed,
            "binance_perp_present": binance_perp_present,
            "fut_quote_vol_24h": _as_float(deriv_block.get("binance_fut_qv_24h")),
            "fut_spot_ratio": None,
            "oi_tokens": oi_tokens,
            "oi_notional_usd": oi_notional,
            "oi_vs_30d_max_pct": oi_pct,
            "oi_state": oi_state,
            "funding_latest": funding,
            "funding_state": funding_state,
            "read": deriv_read,
            "note": "OI rising ≠ bearish. No clean Binance fut/spot ratio (spot absent). Not perp-only market-wide.",
            "source_url": "https://www.binance.com/en/futures/SPXUSDT",
        },
        "liquidity": {
            "read": liquidity_read,
            "binance_spot": binance_spot_label,
            "cex_heavy": cex_heavy,
            "cex_market_names": spx_cex_markets,
            "cex_market_count": len(spx_cex_markets),
            "dex_vol_24h_top10_sol": dex_vol,
            "dex_buys_24h": dex_buys,
            "dex_sells_24h": dex_sells,
            "note": "Do not present one Solana pool as the market. Do not say Binance dominates global spot.",
            "source_url": "https://www.coingecko.com/en/coins/spx6900",
        },
        "supply": {
            "max_supply": max_supply,
            "circulating_cg": circ,
            "circulating_pct_of_max": float(circ) / float(max_supply) * 100.0,
            "pressure_read": "MOSTLY CIRCULATING",
            "eth_canonical": platforms["ethereum"],
            "eth_total_supply": eth_total,
            "solana_mint": sol_mint,
            "solana_supply": sol_sup,
            "solana_pct_of_cg_circ": _as_float(market.get("solana_pct_of_cg_circ")),
            "base_portal": platforms["base"],
            "base_supply": _as_float(cross.get("base_total_supply_ui_8dec")),
            "wormhole_mint_auth": wormhole_auth,
            "wormhole_auth_identity": wormhole_status,
            "architecture_note": (
                "Solana/Base are Wormhole portal representations of the Ethereum SPX token. "
                "Solana mint authority is bridge mint-burn mechanics — not evidence of "
                "discretionary SPX-team printing of an independent extra 1B."
            ),
            "display_rule": (
                "Most of SPX’s maximum supply is already circulating. "
                "Mostly circulating ≠ decentralised ownership."
            ),
        },
        "holders": {
            "market_wide": "UNKNOWN",
            "solana_top10_pct_of_sol_mint": _as_float(market.get("top10_sol_pct")),
            "solana_top20_pct_of_sol_mint": _as_float(market.get("top20_sol_pct")),
            "solana_slice_note": (
                "Solana is only ~9% of CG circulating. Never present Solana concentration as global."
            ),
            "top1_identity": "UNKNOWN",
            "raydium_in_top": any(
                (h.get("owner") or "") == _RAYDIUM_AUTHORITY_OWNER for h in holders
            ),
            "read": "SOLANA HOLDER MAP PARTIAL · MARKET-WIDE OWNERSHIP UNKNOWN",
        },
        "capital_flow": {
            "who_buying": "UNKNOWN",
            "who_selling": "UNKNOWN",
            "dex_note": (
                "CEX-heavy market. DEX txn counts are not buyer identity, net accumulation, "
                "or market-wide capital flow."
            ),
            "source_url": f"https://dexscreener.com/solana/{sol_mint}",
        },
        "mm": mm_block,
        "attention": {
            "read": "UNKNOWN",
            "note": "No defensible attention time-series this pass. Do not invent social metrics.",
        },
    }
