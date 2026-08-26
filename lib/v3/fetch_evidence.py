"""Gather live evidence for V3 market + RENDER builds."""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from lib.btc_history import load_btc_daily
from lib.cycles import analyse_btc
from lib.fetchers.http import get_json
from lib.fetchers.asset_evidence import fetch_all_standard_evidence
from lib.fetchers.live_spot_price import MIXED_WEEKLY_ASSETS
from lib.fetchers.price_common import fetch_daily_prices, fetch_price_coingecko
from lib.fetchers.render_sources import fetch_all_render_evidence
from lib.paths import CONFIG, REPORTS
from lib.macro_liquidity import fetch_global_liquidity
from lib.stablecoin_supply import fetch_stablecoin_supply
from lib.v3.fragility_feeds import enrich_btc_fragility_with_mcap
from lib.v3.breadth_universe import (
    compute_market_breadth,
    compute_portfolio_breadth,
    fetch_universe_daily_for_evidence,
    load_universe_config,
)
from lib.v3.sector_destination import compute_sector_destination, load_sector_baskets

TRACKED_ALTS = [
    ("sol", "solana", "SOL"),
    ("render", "render-token", "RENDER"),
    ("io", "io-net", "IO"),
    ("nos", "nosana", "NOS"),
    ("grass", "grass", "GRASS"),
    ("fartcoin", "fartcoin", "FARTCOIN"),
    ("spx6900", "spx6900", "SPX6900"),
    ("pump", "pump-fun", "PUMP"),
]


def _fetched_at() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_ai_basket() -> dict:
    path = CONFIG / "v3-ai-basket.json"
    return json.loads(path.read_text())


def _latest_archived_slug(slug: str) -> dict | None:
    if not REPORTS.exists():
        return None
    found: Path | None = None
    for d in sorted(REPORTS.iterdir()):
        if d.is_dir() and (d / f"{slug}.json").exists():
            found = d / f"{slug}.json"
    if not found:
        return None
    return json.loads(found.read_text())


def _fetch_coingecko_batch(ids: list[str]) -> dict[str, dict]:
    if not ids:
        return {}
    data = get_json(
        "https://api.coingecko.com/api/v3/simple/price",
        params={
            "ids": ",".join(ids),
            "vs_currencies": "usd",
            "include_7d_change": "true",
            "include_30d_change": "true",
        },
    )
    return data


def _fetch_coingecko_markets(ids: list[str]) -> dict[str, dict]:
    """Batch 7d/30d % — one call; free tier does not return these on simple/price."""
    if not ids:
        return {}
    rows = get_json(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "ids": ",".join(ids),
            "price_change_percentage": "7d,30d",
            "per_page": min(250, len(ids)),
        },
    )
    out: dict[str, dict] = {}
    for row in rows:
        out[row["id"]] = {
            "usd": row.get("current_price"),
            "usd_7d_change": row.get("price_change_percentage_7d_in_currency"),
            "usd_30d_change": row.get("price_change_percentage_30d_in_currency"),
            "market_cap": row.get("market_cap"),
            "last_updated": row.get("last_updated"),
        }
    return out


def _fetch_coingecko_markets_with_fallback(ids: list[str]) -> dict[str, dict]:
    for attempt in range(3):
        try:
            return _fetch_coingecko_markets(ids)
        except Exception:
            if attempt < 2:
                time.sleep(12)
    out: dict[str, dict] = {}
    for coin_id in ids:
        try:
            time.sleep(1.2)
            row = fetch_price_coingecko(coin_id)
            out[coin_id] = {
                "usd": row.get("price_usd"),
                "usd_7d_change": row.get("change_7d_pct"),
                "usd_30d_change": row.get("change_30d_pct"),
                "last_updated": None,
            }
        except Exception:
            continue
    if not out:
        raise RuntimeError("CoinGecko markets batch and per-coin fallback both failed")
    return out


def gather_v3_evidence() -> dict[str, Any]:
    bundle: dict[str, Any] = {"calls": []}

    btc_rows, btc_meta = load_btc_daily(refresh=False)
    cache_to = btc_meta.get("to")
    if cache_to:
        try:
            if (date.today() - date.fromisoformat(cache_to)).days > 1:
                btc_rows, btc_meta = load_btc_daily(refresh=True)
        except ValueError:
            btc_rows, btc_meta = load_btc_daily(refresh=True)
    bundle["btc_daily"] = btc_rows
    bundle["btc_meta"] = btc_meta
    bundle["btc_analysis"] = analyse_btc(btc_rows) if btc_rows else None

    price_ids = ["bitcoin", "ethereum", "solana", "render-token", "pump-fun"]
    for slug, coin_id, _ in TRACKED_ALTS:
        if coin_id not in price_ids:
            price_ids.append(coin_id)
    basket = _load_ai_basket()
    universe_cfg = load_universe_config()
    for c in basket["constituents"]:
        if c["coingecko_id"] not in price_ids:
            price_ids.append(c["coingecko_id"])
    for c in universe_cfg.get("constituents", []):
        if c["coingecko_id"] not in price_ids:
            price_ids.append(c["coingecko_id"])
    sector_cfg = load_sector_baskets()
    for basket in sector_cfg.get("baskets", []):
        for c in basket.get("constituents", []):
            if c["coingecko_id"] not in price_ids:
                price_ids.append(c["coingecko_id"])

    try:
        bundle["market_prices"] = _fetch_coingecko_markets_with_fallback(price_ids)
        bundle["simple_prices"] = {
            cid: {
                "usd": row.get("usd"),
                "usd_7d_change": row.get("usd_7d_change"),
                "usd_30d_change": row.get("usd_30d_change"),
            }
            for cid, row in bundle["market_prices"].items()
        }
        bundle["calls"].append({"fn": "coingecko_markets_batch", "ok": True})
    except Exception as e:
        bundle["market_prices"] = {}
        bundle["simple_prices"] = {}
        bundle["calls"].append({"fn": "coingecko_markets_batch", "ok": False, "error": str(e)})

    render_evidence = fetch_all_render_evidence()
    bundle["render_evidence"] = render_evidence

    try:
        pump = MIXED_WEEKLY_ASSETS["PUMP"]
        bundle["pump_evidence"] = fetch_all_standard_evidence(
            pump["coin_id"],
            mint=pump["dex_mint"],
            site_url="https://pump.fun",
            symbol=pump["symbol"],
            binance_pair=pump["binance_pair"],
        )
        bundle["calls"].append({"fn": "fetch_pump_evidence", "ok": True})
    except Exception as e:
        bundle["pump_evidence"] = None
        bundle["calls"].append({"fn": "fetch_pump_evidence", "ok": False, "error": str(e)})

    daily: dict[str, dict[str, float]] = {}
    if btc_rows:
        daily["btc"] = {r["date"]: r["close"] for r in btc_rows}
    render_daily = render_evidence.get("daily_prices")
    if render_daily:
        daily["render"] = render_daily

    bundle["daily_prices"] = daily

    alt_snapshots = []
    mp = bundle.get("market_prices") or {}
    for slug, coin_id, symbol in TRACKED_ALTS:
        archived = _latest_archived_slug(slug)
        row = mp.get(coin_id, {})
        sp = bundle["simple_prices"].get(coin_id, {})
        alt_snapshots.append(
            {
                "slug": slug,
                "symbol": symbol,
                "coingecko_id": coin_id,
                "price_usd": row.get("usd") or sp.get("usd"),
                "change_7d_pct": row.get("usd_7d_change"),
                "change_30d_pct": row.get("usd_30d_change"),
                "price_as_of": row.get("last_updated"),
                "archived_call": archived.get("asset_call") if archived else None,
                "archived_date": archived.get("report_date") if archived else None,
            }
        )
    bundle["alt_snapshots"] = alt_snapshots
    bundle["ai_basket_config"] = basket

    universe_ids = [c["coingecko_id"] for c in universe_cfg.get("constituents", [])]
    try:
        universe_daily = fetch_universe_daily_for_evidence(universe_ids)
        bundle["breadth_universe_daily"] = universe_daily
        from lib.v3.breadth_universe import load_universe_daily_meta

        bundle["breadth_universe_daily_meta"] = load_universe_daily_meta()
        bundle["calls"].append({"fn": "breadth_universe_daily", "ok": bool(universe_daily)})
    except Exception as e:
        bundle["breadth_universe_daily"] = {}
        bundle["calls"].append({"fn": "breadth_universe_daily", "ok": False, "error": str(e)})

    bundle["market_breadth"] = compute_market_breadth(bundle, bundle.get("breadth_universe_daily") or {})
    bundle["portfolio_breadth"] = compute_portfolio_breadth(bundle)
    bundle["sector_destination"] = compute_sector_destination(bundle)

    sc = fetch_stablecoin_supply()
    bundle["stablecoin_supply"] = sc
    bundle["calls"].append(
        {"fn": "defillama_stablecoin_supply", "ok": sc.get("ok"), "error": sc.get("error")}
    )

    gl = fetch_global_liquidity()
    bundle["global_liquidity"] = gl
    bundle["calls"].append(
        {"fn": "fred_global_liquidity", "ok": gl.get("ok"), "error": gl.get("error")}
    )

    try:
        from lib.supporting_feeds import gather_supporting_feeds

        sf = gather_supporting_feeds()
        frag = (sf.get("btc_fragility") or {})
        btc_mcap = (bundle.get("market_prices") or {}).get("bitcoin", {}).get("market_cap")
        if frag.get("ok"):
            sf["btc_fragility"] = enrich_btc_fragility_with_mcap(frag, btc_mcap)
        bundle["supporting_feeds"] = sf
        bundle["calls"].append(
            {
                "fn": "supporting_feeds",
                "ok": sf.get("fear_greed", {}).get("ok") and sf.get("btc_funding", {}).get("ok"),
            }
        )
    except Exception as e:
        bundle["supporting_feeds"] = None
        bundle["calls"].append({"fn": "supporting_feeds", "ok": False, "error": str(e)})

    bundle["fetched_at"] = _fetched_at()
    return bundle
