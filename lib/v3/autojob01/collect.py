"""Live AUTOJOB01 collection. Never reads dated JSON as live. Report 01 not written."""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from typing import Any

from lib.fetchers.live_spot_price import now_iso
from lib.price_compare import DEFAULT_DIVERGE_PCT
from lib.v3.autojob01.contracts import PRICE_ASSETS

TWELVE = (
    "BTC", "SOL", "RENDER", "PUMP", "GRASS", "RAY",
    "IO", "NOS", "FARTCOIN", "SPX6900", "ZEC", "HYPE",
)
CG_ROTATION_IDS = ("bitcoin", "ethereum", "solana")


def _fail(field: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "field": field, "failure_type": reason, "freshness": "MISSING", **extra}


def _timing(name: str):
    """stderr start/end timing — find hangs without a weekly rerun."""
    t0 = time.monotonic()
    print(f"[AUTOJOB01-TIMING] START {name}", file=sys.stderr, flush=True)

    def _end(extra: str = "") -> float:
        dt = time.monotonic() - t0
        tail = f" {extra}" if extra else ""
        print(f"[AUTOJOB01-TIMING] END {name} {dt:.1f}s{tail}", file=sys.stderr, flush=True)
        return dt

    return _end


def _diff_pct(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-12) * 100.0


def collect_cg_markets() -> dict[str, Any]:
    """One CoinGecko markets call for 12 assets + ETH (rotation + ATH + circ)."""
    from lib.coingecko_api import coins_markets

    ids = [PRICE_ASSETS[s]["coingecko_id"] for s in TWELVE]
    for extra in CG_ROTATION_IDS:
        if extra not in ids:
            ids.append(extra)
    try:
        from lib.v3.breadth_universe import load_universe_config

        for c in load_universe_config().get("constituents") or []:
            cid = c.get("coingecko_id")
            if cid and cid not in ids:
                ids.append(cid)
    except Exception:
        pass
    rows = coins_markets(ids)
    by_id = {str(r.get("id")): r for r in rows if isinstance(r, dict) and r.get("id")}
    missing = [i for i in ids if i not in by_id]
    return {
        "ok": not missing,
        "errors": [f"CoinGecko markets missing {m}" for m in missing],
        "by_id": by_id,
        "fetched_at": now_iso(),
        "source": "coingecko coins/markets",
        "n": len(by_id),
    }


def collect_prices(cg_markets: dict[str, Any] | None = None) -> dict[str, Any]:
    """CG markets batch first (one call). Binance/Dex only for 2% gate — no extra CG coins/{id}."""
    from lib.fetchers.live_spot_price import spec_for, _fetch_binance, _fetch_dexscreener

    cg = cg_markets if cg_markets is not None else collect_cg_markets()
    by_id = cg.get("by_id") or {}
    rows: dict[str, Any] = {}
    errors: list[str] = []
    for sym in TWELVE:
        spec = PRICE_ASSETS[sym]
        ticker = spec.get("html_ticker") or sym
        cid = spec["coingecko_id"]
        mrow = by_id.get(cid) or {}
        cg_px = mrow.get("current_price")
        attempts: list[dict[str, Any]] = []
        if not isinstance(cg_px, (int, float)) or cg_px <= 0:
            errors.append(f"{sym} CoinGecko markets has no current_price")
            rows[sym] = _fail(f"PRICE.{sym}", "SOURCE_FAILURE", ticker=ticker, attempts=attempts)
            continue
        cg_px = float(cg_px)
        attempts.append({"source": "coingecko_markets", "ok": True, "price_usd": cg_px})
        others: list[tuple[str, float]] = []
        dex_liq = None
        live_spec = spec_for(
            sym,
            coin_id=cid,
            binance_pair=spec.get("binance_spot"),
            dex_mint=spec.get("dex_mint"),
        )
        if spec.get("binance_spot"):
            try:
                b = _fetch_binance(live_spec)
                bp = float(b["price_usd"])
                attempts.append({"source": "binance", "ok": True, "price_usd": bp})
                others.append(("binance", bp))
            except Exception as exc:  # noqa: BLE001
                attempts.append({"source": "binance", "ok": False, "error": str(exc)})
        dex_liq = None
        if spec.get("dex_mint"):
            try:
                d = _fetch_dexscreener(live_spec)
                dp = float(d["price_usd"])
                attempts.append({"source": "dexscreener", "ok": True, "price_usd": dp})
                others.append(("dexscreener", dp))
                dex_liq = d.get("liquidity_usd") or d.get("liquidityUsd")
            except Exception as exc:  # noqa: BLE001
                attempts.append({"source": "dexscreener", "ok": False, "error": str(exc)})
        diverge = []
        for name, px in others:
            spread = _diff_pct(cg_px, px)
            if spread > DEFAULT_DIVERGE_PCT:
                diverge.append(f"{sym} {name} vs CG {spread:.2f}% > {DEFAULT_DIVERGE_PCT}%")
        if diverge:
            errors.extend(diverge)
            rows[sym] = _fail(
                f"PRICE.{sym}",
                "MULTI_SOURCE_DIVERGENCE",
                ticker=ticker,
                attempts=attempts,
                errors=diverge,
            )
            continue
        rows[sym] = {
            "ok": True,
            "ticker": ticker,
            "slug": spec["slug"],
            "price_usd": cg_px,
            "print": fmt_price(cg_px),
            "source": "coingecko_markets",
            "fetched_at": now_iso(),
            "freshness": "CURRENT",
            "ath_usd": mrow.get("ath"),
            "circulating_supply": mrow.get("circulating_supply"),
            "change_30d_pct": mrow.get("price_change_percentage_30d_in_currency"),
            "change_7d_pct": mrow.get("price_change_percentage_7d_in_currency"),
            "identity": {"coin_id": cid, "binance_spot": spec.get("binance_spot"), "dex_mint": spec.get("dex_mint")},
            "attempts": attempts,
            "liquidity_usd": dex_liq,
        }
    return {
        "ok": not errors,
        "errors": errors,
        "assets": rows,
        "fetched_at": now_iso(),
        "cg_markets": {"ok": cg.get("ok"), "n": cg.get("n"), "errors": cg.get("errors")},
    }


def fmt_price(usd: float) -> str:
    if usd >= 1:
        s = f"${usd:,.2f}".rstrip("0").rstrip(".")
        return s
    s = f"${usd:.6f}".rstrip("0").rstrip(".")
    return s


def fmt_owned(usd: float, qty: float) -> str:
    if qty <= 0:
        return "$0"
    if usd >= 1:
        return f"${usd:,.0f}"
    if usd > 0:
        return f"${usd:.2f}"
    return "$0"


def collect_wallet(prices: dict[str, Any]) -> dict[str, Any]:
    from lib.wallet import fetch_balances, load_assets_config

    cfg = load_assets_config()
    wallet = cfg["wallet"]
    try:
        bals = fetch_balances(wallet)
        wallet_ok = True
        err = None
    except Exception as exc:  # noqa: BLE001
        bals = {}
        wallet_ok = False
        err = str(exc)
        return _fail("WALLET", "SOURCE_FAILURE", error=err, wallet=wallet)

    owned: dict[str, Any] = {}
    total = 0.0
    px_map = prices.get("assets") or {}
    for asset in cfg["assets"]:
        sym = asset["symbol"]
        if sym == "BTC":
            owned[sym] = {"qty": None, "usd": None, "print": "—", "note": "Coinbase not wired"}
            continue
        qty = float(bals.get(sym) or 0)
        px_row = px_map.get(sym) or {}
        px = float(px_row.get("price_usd") or 0)
        usd = qty * px
        if qty > 0:
            total += usd
        if not asset.get("mint") and not asset.get("native"):
            owned[sym] = {"qty": None, "usd": None, "print": "—", "note": "not a Solana wallet asset"}
            continue
        owned[sym] = {
            "qty": qty,
            "usd": round(usd, 2),
            "print": fmt_owned(usd, qty),
            "price_print": px_row.get("print"),
        }
    # HYPE not in assets.json
    if "HYPE" not in owned:
        owned["HYPE"] = {"qty": None, "usd": None, "print": "—", "note": "not in assets.json"}
    return {
        "ok": wallet_ok,
        "wallet": wallet,
        "owned": owned,
        "total_usd": round(total, 2),
        "total_print": f"${total:,.0f}",
        "fetched_at": now_iso(),
        "freshness": "CURRENT",
    }


def collect_market(cg_markets: dict[str, Any] | None = None, prices: dict[str, Any] | None = None) -> dict[str, Any]:
    from lib.macro_liquidity import fetch_global_liquidity
    from lib.stablecoin_supply import fetch_stablecoin_supply
    from lib.supporting_feeds import fetch_fear_greed
    from lib.v3.etf_flows import fetch_etf_flows
    from lib.v3.fragility_feeds import fetch_btc_fragility_feeds
    from lib.fetchers.http import get_json

    errors: list[str] = []
    out: dict[str, Any] = {"fetched_at": now_iso()}
    by_id = (cg_markets or {}).get("by_id") or {}

    gl = fetch_global_liquidity()
    out["macro_fred"] = gl
    if not (gl.get("ok") or gl.get("partial_ok")):
        errors.append("FRED macro failed")

    try:
        out["stablecoins"] = fetch_stablecoin_supply()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"DefiLlama stables: {exc}")
        out["stablecoins"] = _fail("MARKET.stables", "SOURCE_FAILURE", error=str(exc))

    btc_m = by_id.get("bitcoin") or {}
    btc_px = btc_m.get("current_price")
    if btc_px is None:
        btc_px = ((prices or {}).get("assets") or {}).get("BTC", {}).get("price_usd")
    out["btc_cg"] = {
        "ok": isinstance(btc_px, (int, float)),
        "price_usd": float(btc_px) if isinstance(btc_px, (int, float)) else None,
        "source": "coingecko_markets",
        "fetched_at": now_iso(),
    }
    if not out["btc_cg"]["ok"]:
        errors.append("CoinGecko BTC price missing from markets batch")

    ath = btc_m.get("ath")
    out["btc_ath"] = {
        "ok": isinstance(ath, (int, float)),
        "ath_usd": float(ath) if isinstance(ath, (int, float)) else None,
        "source": "coingecko coins/markets bitcoin ath (same CoinGecko ATH as coins/bitcoin)",
        "fetched_at": now_iso(),
    }
    if not out["btc_ath"]["ok"]:
        errors.append("CoinGecko BTC ATH missing from markets batch")

    try:
        kl = get_json(
            "https://api.binance.com/api/v3/klines",
            {"symbol": "BTCUSDT", "interval": "1d", "limit": 400},
        )
        july = []
        for row in kl:
            ts = int(row[0]) / 1000
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            if dt.year == 2026 and dt.month == 7:
                july.append(float(row[3]))  # low
        floor = min(july) if july else None
        out["july_floor"] = {
            "ok": floor is not None,
            "usd": floor,
            "source": "binance BTCUSDT daily lows July 2026",
            "fetched_at": now_iso(),
            "freshness": "CURRENT_REREAD",
        }
        if floor is None:
            errors.append("July floor missing from Binance daily")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Binance July floor: {exc}")
        out["july_floor"] = _fail("MARKET.july_floor", "SOURCE_FAILURE", error=str(exc))

    fg = fetch_fear_greed(7)
    out["fear_greed"] = fg
    if not fg.get("ok"):
        errors.append("Fear & Greed failed")

    frag = fetch_btc_fragility_feeds(now_iso())
    out["btc_leverage"] = frag
    if not frag.get("ok"):
        errors.append("BTC leverage (Binance perp+spot) failed")

    etf = fetch_etf_flows()
    out["etf"] = etf
    if not etf.get("ok"):
        # unavailable ≠ bearish; record honestly — never coerce to zero
        out["etf"]["unavailable"] = True
        for sym, row in (etf.get("assets") or {}).items():
            if not row.get("ok"):
                for k in ("flow_1d_usd", "flow_7d_usd", "flow_30d_usd"):
                    if row.get(k) == 0:
                        errors.append(f"ETF {sym} unavailable coerced to zero")
                row["flow_7d_usd"] = None if not row.get("ok") else row.get("flow_7d_usd")
                row["flow_30d_usd"] = None if not row.get("ok") else row.get("flow_30d_usd")

    out["rotation"] = _rotation_from_markets(by_id)
    if not out["rotation"].get("ok"):
        errors.append("rotation ETH/SOL vs BTC 30d missing")

    t_part = _timing("collect_participation")
    part = collect_participation(by_id)
    t_part(f"ok={part.get('ok')} sma_n={part.get('above_50d_sample_n')}")
    out["participation"] = part
    if not part.get("ok"):
        errors.append("Market Participation failed")

    return {"ok": not errors, "errors": errors, "data": out}


def _chg30(row: dict[str, Any]) -> float | None:
    v = row.get("price_change_percentage_30d_in_currency")
    return float(v) if isinstance(v, (int, float)) else None


def _rotation_from_markets(by_id: dict[str, Any]) -> dict[str, Any]:
    btc = _chg30(by_id.get("bitcoin") or {})
    eth = _chg30(by_id.get("ethereum") or {})
    sol = _chg30(by_id.get("solana") or {})
    eth_pp = (eth - btc) if eth is not None and btc is not None else None
    sol_pp = (sol - btc) if sol is not None and btc is not None else None
    eth_bit = (
        "ETH ahead of BTC" if isinstance(eth_pp, float) and eth_pp > 0
        else "ETH still behind BTC" if isinstance(eth_pp, float)
        else "ETH vs BTC unavailable"
    )
    sol_bit = (
        "SOL still behind BTC" if isinstance(sol_pp, float) and sol_pp < 0
        else "SOL ahead of BTC" if isinstance(sol_pp, float)
        else "SOL vs BTC unavailable"
    )
    return {
        "ok": eth_pp is not None and sol_pp is not None,
        "btc_30d": btc,
        "eth_30d": eth,
        "sol_30d": sol,
        "eth_btc_30d_pp": eth_pp,
        "sol_btc_30d_pp": sol_pp,
        "eth_line": eth_bit,
        "sol_line": sol_bit,
        "source": "coingecko markets 30d (bitcoin, ethereum, solana)",
        "fetched_at": now_iso(),
    }


def collect_participation(by_id: dict[str, Any]) -> dict[str, Any]:
    """21-coin beat BTC (from markets 30d) + above 50d (paced daily). Fail loud — no stale cache as live."""
    from lib.coingecko_api import get_json as cg_get
    from lib.v3.breadth_universe import load_universe_config, _pct_above_sma, _SMA_WINDOW

    cfg = load_universe_config()
    constituents = cfg.get("constituents") or []
    n = len(constituents) or 21
    btc_30 = _chg30(by_id.get("bitcoin") or {})
    beat = 0
    rs_n = 0
    missing_30 = []
    for c in constituents:
        cid = c["coingecko_id"]
        row = by_id.get(cid)
        if row is None:
            try:
                time.sleep(2.5)
                extra = cg_get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    {"vs_currency": "usd", "ids": cid, "price_change_percentage": "30d"},
                )
                row = extra[0] if isinstance(extra, list) and extra else None
                if row:
                    by_id[cid] = row
            except Exception:
                row = None
        alt = _chg30(row or {})
        if alt is not None and btc_30 is not None:
            rs_n += 1
            if alt > btc_30:
                beat += 1
        else:
            missing_30.append(cid)

    above = 0
    sma_n = 0
    sma_fail: list[str] = []
    for c in constituents:
        cid = c["coingecko_id"]
        tick = _timing(f"participation.market_chart:{cid}")
        try:
            time.sleep(2.5)
            chart = cg_get(
                f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart",
                {"vs_currency": "usd", "days": "90"},
            )
            prices = chart.get("prices") or []
            daily: dict[str, float] = {}
            for ts, px in prices:
                d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                daily[d] = float(px)
            flag = _pct_above_sma(daily, _SMA_WINDOW)
            if flag is None:
                sma_fail.append(cid)
                tick("no_sma")
                continue
            sma_n += 1
            if flag:
                above += 1
            tick()
        except Exception as exc:  # noqa: BLE001
            tick(f"FAIL {exc}")
            sma_fail.append(f"{cid}:{exc}")

    ok = rs_n == n and sma_n == n
    errors = []
    if rs_n != n:
        errors.append(f"participation 30d coverage {rs_n}/{n} missing={missing_30}")
    if sma_n != n:
        errors.append(f"participation 50d coverage {sma_n}/{n} fail={sma_fail[:5]}")
    return {
        "ok": ok,
        "universe_n": n,
        "beat_btc_n": beat,
        "beat_sample_n": rs_n,
        "above_50d_n": above,
        "above_50d_sample_n": sma_n,
        "line": f"Only {beat} of {n} beat BTC · {above} of {n} above 50d",
        "source": "coingecko markets 30d + market_chart 50DMA",
        "errors": errors,
        "fetched_at": now_iso(),
    }


def collect_technicals() -> dict[str, Any]:
    from lib.v3.sma_trend import compute_sma_trend, _norm_slug

    rows: dict[str, Any] = {}
    errors: list[str] = []
    slugs = [PRICE_ASSETS[s]["slug"] for s in TWELVE]
    for slug in slugs:
        try:
            rows[slug] = compute_sma_trend(slug)
            rows[slug]["ok"] = True
            rows[slug]["fetched_at"] = now_iso()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{slug} SMA: {exc}")
            rows[slug] = _fail(f"TECH.{slug}", "SOURCE_FAILURE", error=str(exc))
    _ = _norm_slug
    return {"ok": not errors, "errors": errors, "assets": rows}


def collect_assets(cg_markets: dict[str, Any] | None = None) -> dict[str, Any]:
    from lib.v3.autojob01.asset_live import (
        collect_hype_live,
        collect_pump_live,
        collect_render_live,
        collect_sol_live,
    )
    from lib.coingecko_api import global_stats

    by_id = (cg_markets or {}).get("by_id") or {}
    errors: list[str] = []
    render = collect_render_live(by_id.get("render-token"))
    hype = collect_hype_live(by_id.get("hyperliquid"))
    pump = collect_pump_live()
    sol = collect_sol_live()
    btc_d = None
    try:
        glob = global_stats() or {}
        btc_d = ((glob.get("data") or {}).get("market_cap_percentage") or {}).get("btc")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"BTC.D: {exc}")
    for name, row in (("render", render), ("hype", hype), ("pump", pump), ("sol", sol)):
        if not row.get("ok"):
            errors.extend(row.get("errors") or [f"{name} failed"])
    return {
        "ok": not errors,
        "errors": errors,
        "render": render,
        "hype": hype,
        "pump": pump,
        "sol": sol,
        "btc_dominance": {"ok": btc_d is not None, "pct": btc_d, "source": "coingecko /global"},
        "fetched_at": now_iso(),
    }


def collect_all() -> dict[str, Any]:
    t = _timing("collect_cg_markets")
    cg = collect_cg_markets()
    t(f"ok={cg.get('ok')} n={cg.get('n')}")
    t = _timing("collect_prices")
    prices = collect_prices(cg)
    t(f"ok={prices.get('ok')}")
    t = _timing("collect_wallet")
    wallet = collect_wallet(prices) if prices.get("ok") else _fail("WALLET", "SKIPPED_NO_PRICE")
    t(f"ok={wallet.get('ok')}")
    t = _timing("collect_market")
    market = collect_market(cg, prices)
    t(f"ok={market.get('ok')}")
    t = _timing("collect_technicals")
    tech = collect_technicals()
    t(f"ok={tech.get('ok')}")
    t = _timing("collect_assets")
    assets = collect_assets(cg)
    t(f"ok={assets.get('ok')}")
    from lib.v3.autojob01.feeds_live import collect_feeds

    t = _timing("collect_feeds")
    feeds = collect_feeds(cg)
    t(f"ok={feeds.get('ok')}")
    errors = (
        list(cg.get("errors") or [])
        + list(prices.get("errors") or [])
        + list(market.get("errors") or [])
        + list(assets.get("errors") or [])
    )
    warnings = list(tech.get("errors") or [])
    errors.extend(list(feeds.get("adapter_errors") or []))
    warnings.extend([e for e in (feeds.get("errors") or []) if e not in (feeds.get("adapter_errors") or [])])
    if not wallet.get("ok"):
        errors.append(wallet.get("error") or "wallet failed")
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "fetched_at": now_iso(),
        "cg_markets": {"ok": cg.get("ok"), "n": cg.get("n")},
        "prices": prices,
        "wallet": wallet,
        "market": market,
        "technicals": tech,
        "assets": assets,
        "feeds": feeds,
    }
