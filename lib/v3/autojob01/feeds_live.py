"""Extra live feeds for mini-dash / R&C / forensics. Never dated Stage-1 JSON."""

from __future__ import annotations

import json
import time
from typing import Any

import certifi
import requests

from lib.fetchers.http import get_json
from lib.fetchers.live_spot_price import now_iso
from lib.paths import CACHE
from lib.v3.source_provenance import LIVE, CACHE_FALLBACK, SOURCE_FAILED, mark_cache_fallback, mark_live, mark_source_failed
from lib.supporting_feeds import (
    fetch_owner_mint_balance,
    fetch_solana_network,
    fetch_token_concentration,
)
from lib.v3.autojob01.contracts import PRICE_ASSETS
from lib.v3.autojob01.asset_live import collect_hype_live, collect_pump_live, collect_render_live, collect_sol_live
from lib.v3.autojob01.helius_sample import sample_mint

WM = "MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa"
RAY_BUYBACK = "DdHDoz94o2WJmD9myRobHCwtx1bESpHTd4SSPe6VEZaz"
PUMP_MINT = "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn"

BINANCE_PERP = {
    "BTC": "BTCUSDT",
    "SOL": "SOLUSDT",
    "RENDER": "RENDERUSDT",
    "RAY": "RAYUSDT",
    "IO": "IOUSDT",
    "FARTCOIN": "FARTCOINUSDT",
    "ZEC": "ZECUSDT",
    "GRASS": "GRASSUSDT",
    "PUMP": "PUMPUSDT",
    "SPX6900": "SPXUSDT",
    "HYPE": "HYPEUSDT",
}

ZEC_EXPLORER = "https://mainnet.zcashexplorer.app/api/v1/blockchain-info"
ZEC_CACHE = CACHE / "zec-shielded.json"
ZEC_CACHE_MAX_DAYS = 3
ZEC_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) crypto-app-v3-autojob01"}


def _fail(field: str, err: str) -> dict[str, Any]:
    return {"ok": False, "field": field, "error": str(err), "freshness": "MISSING"}


def _binance_lev(symbol: str) -> dict[str, Any]:
    try:
        fut: dict[str, Any] | None = None
        try:
            fut = get_json("https://fapi.binance.com/fapi/v1/ticker/24hr", {"symbol": symbol})
            if not isinstance(fut, dict) or not fut.get("lastPrice"):
                fut = None
        except Exception:
            fut = None
        oi: dict[str, Any] = {}
        try:
            oi = get_json("https://fapi.binance.com/fapi/v1/openInterest", {"symbol": symbol}) or {}
        except Exception as exc:  # noqa: BLE001
            oi = {"error": str(exc)}
        spot = None
        try:
            spot = get_json("https://api.binance.com/api/v3/ticker/24hr", {"symbol": symbol})
        except Exception:
            spot = None
        funding = None
        try:
            prem = get_json("https://fapi.binance.com/fapi/v1/premiumIndex", {"symbol": symbol})
            funding = float(prem.get("lastFundingRate")) if prem.get("lastFundingRate") is not None else None
        except Exception:
            funding = None
        fut_q = float((fut or {}).get("quoteVolume") or 0) if fut else None
        spot_q = float((spot or {}).get("quoteVolume") or 0)
        mark = float((fut or {}).get("lastPrice") or (spot or {}).get("lastPrice") or 0)
        oi_tok = float(oi.get("openInterest") or 0) if isinstance(oi.get("openInterest"), (int, float, str)) else None
        ratio = (fut_q / spot_q) if fut_q and spot_q > 0 else None
        if not fut and not (spot and spot.get("lastPrice")):
            return _fail(f"BINANCE.{symbol}", "empty futures ticker")
        return {
            "ok": True,
            "symbol": symbol,
            "fut_quote_24h": fut_q,
            "spot_quote_24h": spot_q if spot else None,
            "perp_spot": ratio,
            "oi_tokens": oi_tok,
            "oi_usd": (oi_tok * mark) if oi_tok is not None and mark else None,
            "last": mark,
            "funding": funding,
            "spot_listed": bool(spot and spot.get("lastPrice")),
        }
    except Exception as exc:  # noqa: BLE001
        return _fail(f"BINANCE.{symbol}", str(exc))


def _llama_fees(slug: str) -> dict[str, Any]:
    try:
        fees = get_json(f"https://api.llama.fi/summary/fees/{slug}?dataType=dailyFees")
        rev = get_json(f"https://api.llama.fi/summary/fees/{slug}?dataType=dailyRevenue")
        hold = get_json(f"https://api.llama.fi/summary/fees/{slug}?dataType=dailyHoldersRevenue")

        def _last(d: dict, n: int) -> float | None:
            chart = d.get("totalDataChart") or []
            if len(chart) < n:
                return None
            return sum(v for _, v in chart[-n:])

        return {
            "ok": True,
            "slug": slug,
            "fees_1d": fees.get("total24h"),
            "fees_7d": _last(fees, 7),
            "fees_30d": _last(fees, 30),
            "rev_1d": rev.get("total24h"),
            "rev_7d": _last(rev, 7),
            "rev_30d": _last(rev, 30),
            "hold_1d": hold.get("total24h"),
            "hold_7d": _last(hold, 7),
            "hold_30d": _last(hold, 30),
            "tvl": fees.get("tvl"),
        }
    except Exception as exc:  # noqa: BLE001
        return _fail(f"LLAMA.{slug}", str(exc))


def _zec_cache_age_days(row: dict[str, Any]) -> int | None:
    ts = row.get("cached_at") or row.get("fetched_at")
    if not ts:
        return None
    try:
        from datetime import datetime, timezone

        if "T" in str(ts):
            d = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date()
        else:
            from datetime import date

            d = date.fromisoformat(str(ts)[:10])
        return (datetime.now(timezone.utc).date() - d).days
    except ValueError:
        return None


def _zec_save_cache(payload: dict[str, Any]) -> None:
    try:
        ZEC_CACHE.parent.mkdir(parents=True, exist_ok=True)
        out = dict(payload)
        out["cached_at"] = now_iso()
        ZEC_CACHE.write_text(json.dumps(out, indent=2) + "\n")
    except Exception:
        pass


def _zec_cache() -> dict[str, Any] | None:
    if not ZEC_CACHE.is_file():
        return None
    try:
        row = json.loads(ZEC_CACHE.read_text())
    except Exception:
        return None
    if not isinstance(row, dict) or not row.get("ok"):
        return None
    age = _zec_cache_age_days(row)
    if age is not None and age > ZEC_CACHE_MAX_DAYS:
        return None
    return row


def _zec_shielded() -> dict[str, Any]:
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.get(ZEC_EXPLORER, timeout=20, verify=certifi.where(), headers=ZEC_UA)
            r.raise_for_status()
            d = r.json()
            named: dict[str, float] = {}
            raw_pools = d.get("valuePools") or []
            if isinstance(raw_pools, list):
                for p in raw_pools:
                    if isinstance(p, dict):
                        k = str(p.get("id") or "").lower()
                        v = p.get("chainValue")
                        if k and v is not None:
                            named[k] = float(v)
            cs = d.get("chainSupply")
            if isinstance(cs, dict):
                chain = float(cs.get("chainValue") or 0)
            else:
                chain = float(cs or 0)
            if not chain:
                chain = sum(named.values())
            shielded = sum(named.get(k, 0) for k in ("sprout", "sapling", "orchard", "ironwood"))
            pct = (shielded / chain * 100.0) if chain else None
            live = {
                "ok": pct is not None,
                "chain_supply": chain,
                "shielded": shielded,
                "pct": pct,
                "pools": named,
                "source": ZEC_EXPLORER,
                "fetched_at": now_iso(),
            }
            live = mark_live(live, as_of=live["fetched_at"][:10])
            _zec_save_cache(live)
            return live
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt + 1 < 3:
                time.sleep(min(1.0 * (attempt + 1), 3.0))
    cached = _zec_cache()
    if cached:
        out = mark_cache_fallback(dict(cached), as_of=cached.get("cached_at"), live_error=str(last_exc or "unknown"))
        return out
    return mark_source_failed(_fail("ZEC.shielded", str(last_exc or "unknown")), live_error=str(last_exc or "unknown"))


def _io_earnings() -> dict[str, Any]:
    url = "https://api.io.solutions/v1/io-explorer/network/info/cluster/total-earnings-summary"
    cl_url = "https://api.io.solutions/v1/io-explorer/network/info/clusters"
    try:
        r = requests.get(url, timeout=45, verify=certifi.where(), headers=ZEC_UA)
        r.raise_for_status()
        d = r.json()
        rows = d.get("data") or []
        last = rows[-1] if rows else {}
        total = last.get("total_earnings")
        window = rows[-30:] if len(rows) >= 30 else rows
        dailies = [
            float(x["daily_earnings"])
            for x in window
            if isinstance(x.get("daily_earnings"), (int, float))
        ]
        avg_30d = (sum(dailies) / len(dailies)) if dailies else None
        clusters = None
        hours = None
        try:
            cr = requests.get(cl_url, timeout=45, verify=certifi.where(), headers=ZEC_UA)
            cr.raise_for_status()
            cl = (cr.json() or {}).get("data") or {}
            clusters = cl.get("running_clusters")
            hours = cl.get("total_compute_hours_served")
        except Exception:  # noqa: BLE001
            pass
        return {
            "ok": isinstance(total, (int, float)),
            "total_earnings": float(total) if total is not None else None,
            "daily_earnings": last.get("daily_earnings"),
            "avg_30d": avg_30d,
            "running_clusters": clusters,
            "total_compute_hours": float(hours) if isinstance(hours, (int, float)) else None,
            "source": url,
            "clusters_source": cl_url,
        }
    except Exception as exc:  # noqa: BLE001
        return _fail("IO.earnings", str(exc))


def _nos_indexer() -> dict[str, Any]:
    try:
        jobs = get_json("https://blockchain-indexer.k8s.prd.nos.ci/jobs/count")
        stats = get_json("https://blockchain-indexer.k8s.prd.nos.ci/stats/")
        completed = ((jobs or {}).get("byState") or {}).get("COMPLETED")
        staked = float((stats or {}).get("nosStaked") or 0)
        return {
            "ok": completed is not None,
            "jobs_completed": completed,
            "jobs_total": (jobs or {}).get("total"),
            "nos_staked": staked,
            "staked_pct": staked / 100_000_000 * 100 if staked else None,
            "source": "https://blockchain-indexer.k8s.prd.nos.ci/jobs/count",
        }
    except Exception as exc:  # noqa: BLE001
        return _fail("NOS.indexer", str(exc))


def _oi_vs_30d(symbol: str) -> dict[str, Any]:
    try:
        hist = get_json(
            "https://fapi.binance.com/futures/data/openInterestHist",
            {"symbol": symbol, "period": "1d", "limit": 30},
        )
        if not isinstance(hist, list) or not hist:
            return _fail(f"OI30.{symbol}", "empty hist")
        vals = [float(x.get("sumOpenInterestValue") or 0) for x in hist]
        last = vals[-1]
        mx = max(vals) if vals else None
        pct = (last / mx * 100.0) if mx else None
        return {"ok": pct is not None, "pct_of_30d_max": pct, "last_usd": last, "max_usd": mx, "symbol": symbol}
    except Exception as exc:  # noqa: BLE001
        return _fail(f"OI30.{symbol}", str(exc))


def _okx_oi(inst: str) -> dict[str, Any]:
    try:
        d = get_json("https://www.okx.com/api/v5/public/open-interest", {"instType": "SWAP", "instId": inst})
        row = ((d or {}).get("data") or [None])[0] or {}
        oi_usd = float(row.get("oiUsd") or 0) if row.get("oiUsd") is not None else None
        return {"ok": isinstance(oi_usd, float) and oi_usd > 0, "oi_usd": oi_usd, "inst": inst, "source": "OKX"}
    except Exception as exc:  # noqa: BLE001
        return _fail(f"OKX.{inst}", str(exc))


def _coinbase_spot_quote(product: str) -> dict[str, Any]:
    try:
        stats = get_json(f"https://api.exchange.coinbase.com/products/{product}/stats")
        last = float((stats or {}).get("last") or 0)
        vol = float((stats or {}).get("volume") or 0)
        quote = last * vol if last and vol else None
        return {"ok": quote is not None, "quote_24h": quote, "last": last, "volume": vol, "product": product}
    except Exception as exc:  # noqa: BLE001
        return _fail(f"COINBASE.{product}", str(exc))


def _binance_180d(symbol: str) -> dict[str, Any]:
    try:
        kl = get_json(
            "https://api.binance.com/api/v3/klines",
            {"symbol": symbol, "interval": "1d", "limit": 180},
        )
        if not isinstance(kl, list) or len(kl) < 2:
            return _fail(f"BN180.{symbol}", "short series")
        first = float(kl[0][4])
        last = float(kl[-1][4])
        ret = (last / first - 1.0) * 100.0 if first else None
        return {"ok": ret is not None, "ret_180d": ret, "symbol": symbol}
    except Exception as exc:  # noqa: BLE001
        return _fail(f"BN180.{symbol}", str(exc))


def _llama_dex_ratio() -> dict[str, Any]:
    try:
        sol = get_json("https://api.llama.fi/overview/dexs/solana")
        eth = get_json("https://api.llama.fi/overview/dexs/ethereum")
        s7 = float((sol or {}).get("total7d") or 0)
        e7 = float((eth or {}).get("total7d") or 0)
        s1 = float((sol or {}).get("total24h") or 0)
        e1 = float((eth or {}).get("total24h") or 0)
        return {
            "ok": s7 > 0 and e7 > 0,
            "ratio_7d": (s7 / e7) if e7 else None,
            "ratio_24h": (s1 / e1) if e1 else None,
            "sol_24h": s1,
            "eth_24h": e1,
        }
    except Exception as exc:  # noqa: BLE001
        return _fail("LLAMA.dex_ratio", str(exc))


def _labelled() -> dict[str, Any]:
    from lib.v3.autojob01.contracts import PRICE_ASSETS as PA

    out: dict[str, Any] = {"ok": True}
    mints = {s: (PA.get(s) or {}).get("dex_mint") for s in ("FARTCOIN", "SPX6900", "RAY", "PUMP")}
    try:
        fart = fetch_owner_mint_balance(WM, mints["FARTCOIN"]) if mints["FARTCOIN"] else None
        spx = fetch_owner_mint_balance(WM, mints["SPX6900"]) if mints["SPX6900"] else None
        ray = fetch_owner_mint_balance(RAY_BUYBACK, mints["RAY"]) if mints["RAY"] else None
        time.sleep(0.2)
        out["fart_wm"] = fart
        out["spx_wm"] = spx
        out["ray_buyback"] = ray
        conc = fetch_token_concentration(mints["SPX6900"], "SPX6900") if mints["SPX6900"] else {}
        out["spx_sol_supply"] = conc.get("total_supply_ui")
        vaults = _squads_vaults()
        pump_sum = 0.0
        n_ok = 0
        deadline = time.monotonic() + 60
        for i, w in enumerate(vaults):
            if time.monotonic() >= deadline:
                out["pump_squads_truncated"] = True
                break
            if i and i % 8 == 0:
                time.sleep(0.35)
            bal = fetch_owner_mint_balance(w, PUMP_MINT)
            if isinstance(bal, (int, float)):
                pump_sum += bal
                n_ok += 1
        out["pump_squads"] = pump_sum
        out["pump_squads_n"] = n_ok
        out["pump_squads_vaults"] = len(vaults)
        out["ok"] = True
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["error"] = str(exc)
    return out


def _squads_vaults() -> list[str]:
    from pathlib import Path
    import json

    from lib.paths import ROOT

    p = ROOT / "reports/pump-forensics/ownership-buyer-quality/ownership-vesting.json"
    if not p.is_file():
        return []
    import json

    data = json.loads(p.read_text())
    seen: set[str] = set()
    for cluster in data.get("controller_clusters_by_create_fee_payer") or []:
        for v in cluster.get("vaults") or []:
            w = v.get("wallet")
            if w:
                seen.add(w)
    return sorted(seen)


def collect_feeds(cg_markets: dict[str, Any] | None = None, reuse: dict[str, Any] | None = None) -> dict[str, Any]:
    by_id = (cg_markets or {}).get("by_id") or {}
    errors: list[str] = []
    lev: dict[str, Any] = {}
    for sym, pair in BINANCE_PERP.items():
        lev[sym] = _binance_lev(pair)
        if not lev[sym].get("ok"):
            errors.append(f"{sym} binance: {lev[sym].get('error')}")

    llama = {
        "pump": collect_pump_live(),
        "hype": _llama_fees("hyperliquid"),
        "ray": _llama_fees("raydium"),
        "sol": collect_sol_live(),
        "ray_tvl": None,
    }
    try:
        tvl = get_json("https://api.llama.fi/tvl/raydium")
        llama["ray_tvl"] = {"ok": True, "tvl": float(tvl) if not isinstance(tvl, dict) else tvl.get("tvl")}
    except Exception as exc:  # noqa: BLE001
        llama["ray_tvl"] = _fail("RAY.tvl", str(exc))
        errors.append(f"RAY TVL: {exc}")
    try:
        dexs = get_json("https://api.llama.fi/summary/dexs/raydium")
        llama["ray_dex"] = {
            "ok": True,
            "vol_24h": (dexs or {}).get("total24h"),
            "vol_30d": (dexs or {}).get("total30d"),
            "source": "https://api.llama.fi/summary/dexs/raydium",
        }
    except Exception as exc:  # noqa: BLE001
        llama["ray_dex"] = _fail("RAY.dex", str(exc))
    try:
        ll = get_json("https://api.llama.fi/summary/dexs/launchlab")
        llama["ray_launchlab"] = {
            "ok": True,
            "vol_24h": (ll or {}).get("total24h"),
            "source": "https://api.llama.fi/summary/dexs/launchlab",
        }
    except Exception as exc:  # noqa: BLE001
        llama["ray_launchlab"] = _fail("RAY.launchlab", str(exc))

    llama["dex_ratio"] = _llama_dex_ratio()

    render = collect_render_live(by_id.get("render-token"))
    hype = collect_hype_live(by_id.get("hyperliquid"))
    zec = _zec_shielded()
    io_earn = _io_earnings()
    nos_idx = _nos_indexer()
    conc: dict[str, Any] = {}
    for i, sym in enumerate(("FARTCOIN", "SPX6900", "RENDER")):
        mint = (PRICE_ASSETS.get(sym) or {}).get("dex_mint")
        if not mint:
            continue
        if i:
            time.sleep(1.2)
        row = fetch_token_concentration(mint, sym)
        for attempt in range(4):
            if row.get("ok") or "429" not in str(row.get("error") or ""):
                break
            time.sleep(2.0 * (attempt + 1))
            row = fetch_token_concentration(mint, sym)
        conc[sym] = row
        if not row.get("ok"):
            errors.append(f"{sym} concentration: {row.get('error')}")

    prev = (reuse or {}).get("helius_sample") or {}
    if (prev.get("RAY") or {}).get("ok") and (prev.get("RENDER") or {}).get("ok"):
        helius = prev
    else:
        helius = {"RAY": sample_mint("RAY"), "RENDER": sample_mint("RENDER")}
    sol_rpc = fetch_solana_network()
    if not sol_rpc.get("ok"):
        errors.append(f"SOL rpc network: {sol_rpc.get('error')}")
    prev_lab = (reuse or {}).get("labelled") or {}
    labelled = prev_lab if prev_lab.get("ok") else _labelled()
    oi30 = {s: _oi_vs_30d(p) for s, p in (("GRASS", "GRASSUSDT"), ("RENDER", "RENDERUSDT"), ("SPX6900", "SPXUSDT"))}
    okx_ray = _okx_oi("RAY-USDT-SWAP")
    cb_fart = _coinbase_spot_quote("FARTCOIN-USD")
    ret180 = {s: _binance_180d(p) for s, p in (("GRASS", "GRASSUSDT"), ("IO", "IOUSDT"))}

    adapter_errors: list[str] = []
    for k, row in helius.items():
        if not row.get("ok"):
            adapter_errors.append(f"Helius {k}: {row.get('error')}")
    emit = (render.get("bme_emit") or {})
    if not emit.get("ok"):
        adapter_errors.append(f"Foundation emit: {emit.get('error') or emit.get('failure_type')}")
    for sym in ("FARTCOIN", "SPX6900"):
        row = conc.get(sym) or {}
        if not row.get("ok"):
            adapter_errors.append(f"Solana RPC {sym} concentration: {row.get('error')}")

    btc_d = None
    try:
        from lib.coingecko_api import global_stats

        g = global_stats() or {}
        btc_d = ((g.get("data") or {}).get("market_cap_percentage") or {}).get("btc")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"BTC.D: {exc}")

    for name, row in (("render", render), ("hype_token", hype), ("zec", zec)):
        if not row.get("ok"):
            errors.extend(row.get("errors") or [f"{name} failed"])

    return {
        "ok": not adapter_errors,
        "adapter_errors": adapter_errors,
        "errors": errors + adapter_errors,
        "fetched_at": now_iso(),
        "leverage": lev,
        "llama": llama,
        "render": render,
        "hype": hype,
        "zec": zec,
        "io_earnings": io_earn,
        "nos_indexer": nos_idx,
        "concentration": conc,
        "helius_sample": helius,
        "sol_rpc": sol_rpc,
        "labelled": labelled,
        "oi_30d": oi30,
        "okx_ray": okx_ray,
        "coinbase_fart": cb_fart,
        "ret_180d": ret180,
        "btc_dominance": {"ok": btc_d is not None, "pct": btc_d, "source": "coingecko /global"},
        "cg_by_id": {
            k: {
                "price": v.get("current_price"),
                "ath": v.get("ath"),
                "circ": v.get("circulating_supply"),
                "total": v.get("total_supply"),
                "max": v.get("max_supply"),
                "mcap": v.get("market_cap"),
                "chg_30d": v.get("price_change_percentage_30d_in_currency"),
                "chg_7d": v.get("price_change_percentage_7d_in_currency"),
                "chg_1y": v.get("price_change_percentage_1y_in_currency"),
                "vol": v.get("total_volume"),
            }
            for k, v in by_id.items()
        },
    }
