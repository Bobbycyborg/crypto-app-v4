"""Explicit Job 2 plan author. Run once. Do not commit this file."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = json.loads((ROOT / "metrics/metric-registry.json").read_text())

DATED_PRESERVE = {
    "btc.etf.flow.usd.2026_08_03_07",
    "btc.etf.flow.usd.2026_08_10",
    "btc.etf.flow.usd.2026_08_11",
    "pump.market_share.pct.aug_10",
    "pump.market_share.pct.share_history",
}

# Hand-authored COLLECT/DERIVE only. Not inferred from metric_id keywords.
COLLECT: dict[str, dict] = {}


def C(metric_id, **kw):
    COLLECT[metric_id] = kw


def cg_coin(coin_id, field, unit="USD"):
    return {
        "disposition": "COLLECT",
        "source_key": "coingecko",
        "request_key": "coingecko.markets.active",
        "selector": {
            "type": "named_record_field",
            "records_pointer": "/",
            "identity": {"id": coin_id},
            "field": field,
        },
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship.",
    }


# Live prices: Job 1 source UNKNOWN; V3 AUTOJOB01 collect_prices stores CoinGecko markets.
for mid, cid in [
    ("btc.price.usd.live", "bitcoin"),
    ("sol.price.usd.live", "solana"),
    ("render.price.usd.live", "render-token"),
    ("pump.price.usd.live", "pump-fun"),
    ("io.price.usd.live", "io"),
    ("nos.price.usd.live", "nosana"),
    ("fart.price.usd.live", "fartcoin"),
    ("spx.price.usd.live", "spx6900"),
    ("zec.price.usd.live", "zcash"),
    ("hype.price.usd.live", "hyperliquid"),
]:
    C(mid, **cg_coin(cid, "current_price"))
    COLLECT[mid]["notes"] = (
        "Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed."
    )

C("btc.price.usd.report", **cg_coin("bitcoin", "current_price"))
C("btc.return.pct.7d", **cg_coin("bitcoin", "price_change_percentage_7d_in_currency"))
C("btc.return.pct.30d", **cg_coin("bitcoin", "price_change_percentage_30d_in_currency"))
C("btc.return.pct.90d", **{
    "disposition": "COLLECT",
    "source_key": "coingecko",
    "request_key": "coingecko.market_chart.bitcoin.90d",
    "selector": {"type": "named_record_field", "name": "market_chart_return_pct", "window_days": 90},
    "normalizer": {"type": "identity"},
    "derivation": None,
    "notes": "CG 90d return via market_chart; markets endpoint no longer exposes 90d field.",
})
C("btc.price.drawdown_from_ath.pct", **cg_coin("bitcoin", "ath_change_percentage"))

C("fart.market_cap.usd.current", **cg_coin("fartcoin", "market_cap"))
C("fart.volume.cg.usd.24h", **cg_coin("fartcoin", "total_volume"))
C("fart.return.pct.7d", **cg_coin("fartcoin", "price_change_percentage_7d_in_currency"))
C("fart.return.pct.30d", **cg_coin("fartcoin", "price_change_percentage_30d_in_currency"))
C("fart.return.pct.90d", **{
    "disposition": "COLLECT",
    "source_key": "coingecko",
    "request_key": "coingecko.market_chart.fartcoin.90d",
    "selector": {"type": "named_record_field", "name": "market_chart_return_pct", "window_days": 90},
    "normalizer": {"type": "identity"},
    "derivation": None,
    "notes": "CG 90d return via market_chart.",
})
C("fart.supply.circulating.tokens", **cg_coin("fartcoin", "circulating_supply"))
C("fart.supply.max.tokens", **cg_coin("fartcoin", "max_supply"))

C("nos.market_cap.usd.current", **cg_coin("nosana", "market_cap"))
C("hype.return.pct.7d", **cg_coin("hyperliquid", "price_change_percentage_7d_in_currency"))
C("hype.return.pct.30d", **cg_coin("hyperliquid", "price_change_percentage_30d_in_currency"))
C("spx.supply.circulating.tokens", **cg_coin("spx6900", "circulating_supply"))
C("spx.supply.max.tokens", **cg_coin("spx6900", "max_supply"))
C("nos.supply.circulating.tokens", **cg_coin("nosana", "circulating_supply"))
C("nos.supply.max.tokens", **cg_coin("nosana", "max_supply"))


def bn_json(request_key, pointer, extra_notes=""):
    return {
        "disposition": "COLLECT",
        "source_key": "binance",
        "request_key": request_key,
        "selector": {"type": "json_pointer", "pointer": pointer},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": extra_notes or "Job 1 names Binance; official futures/spot JSON API.",
    }


C("btc.funding.rate.latest", **bn_json("binance.fapi.premiumIndex.BTCUSDT", "/lastFundingRate"))
COLLECT["btc.funding.rate.latest"]["normalizer"] = {"type": "decimal_as_percent"}
C("sol.funding.rate.latest", **bn_json("binance.fapi.premiumIndex.SOLUSDT", "/lastFundingRate"))
COLLECT["sol.funding.rate.latest"]["normalizer"] = {"type": "decimal_as_percent"}
COLLECT["sol.funding.rate.latest"]["notes"] = (
    "Job 1 URL is fundingRate; V3 live feed uses premiumIndex lastFundingRate on the same Binance USDT-M product."
)
C("pump.funding.rate.latest", **bn_json("binance.fapi.premiumIndex.PUMPUSDT", "/lastFundingRate"))
COLLECT["pump.funding.rate.latest"]["normalizer"] = {"type": "decimal_as_percent"}
C("render.funding.rate.latest", **bn_json("binance.fapi.premiumIndex.RENDERUSDT", "/lastFundingRate"))
COLLECT["render.funding.rate.latest"]["normalizer"] = {"type": "decimal_as_percent"}
C("fart.funding.rate.latest", **bn_json("binance.fapi.premiumIndex.FARTCOINUSDT", "/lastFundingRate"))
COLLECT["fart.funding.rate.latest"]["normalizer"] = {"type": "decimal_as_percent"}
C("spx.funding.rate.latest", **bn_json("binance.fapi.premiumIndex.SPXUSDT", "/lastFundingRate"))
COLLECT["spx.funding.rate.latest"]["normalizer"] = {"type": "decimal_as_percent"}

C("btc.oi.btc.current", **bn_json("binance.fapi.openInterest.BTCUSDT", "/openInterest"))
C("btc.volume.perp.usd.24h", **bn_json("binance.fapi.ticker24h.BTCUSDT", "/quoteVolume"))
C("btc.volume.spot.usd.24h", **bn_json("binance.spot.ticker24h.BTCUSDT", "/quoteVolume"))
C("pump.oi.usd.current", **bn_json("binance.fapi.ticker24h.PUMPUSDT", "/quoteVolume"))
# OI USD = openInterest tokens * mark; Job 1 pump.oi is USD. ticker24h has sumOpenInterest? 
# Use openInterest * lastPrice via DERIVE instead.
# Rebind pump.oi to openInterest tokens then we need mark. 
# Binance ticker 24h has lastPrice; openInterest is separate.
# DERIVE pump.oi.usd = oi_tokens * lastPrice. Need two COLLECT intermediates not in registry.
# Extract from ticker: some endpoints include openInterest. fapi ticker 24hr has openInterest? 
# USDT-M 24hr ticker has lastPrice, quoteVolume, not OI.
# COLLECT openInterest tokens * lastPrice in a named extractor spanning two captures.
# Simpler: use openInterestHist last sumOpenInterestValue - Job 1 URL is futures page not hist.
# Use named extractor on premiumIndex? No.
# pump.oi.usd.current: fetch ticker lastPrice and OI in orchestrator dual? 
# Put selector name open_interest_usd with request_key primary OI and mark_request_key ticker.

C("fart.oi.usd.current", **bn_json("binance.fapi.openInterest.FARTCOINUSDT", "/openInterest"))
COLLECT["fart.oi.usd.current"]["notes"] = (
    "Job 1 is USD OI; Binance openInterest is contracts. See selector identity; "
    "normalized via mark from same-run ticker capture."
)
COLLECT["fart.oi.usd.current"]["selector"] = {
    "type": "named_record_field",
    "name": "open_interest_usd",
    "oi_pointer": "/openInterest",
    "mark_request_key": "binance.fapi.ticker24h.FARTCOINUSDT",
    "mark_pointer": "/lastPrice",
}

C("pump.oi.usd.current", **{
    "disposition": "COLLECT",
    "source_key": "binance",
    "request_key": "binance.fapi.openInterest.PUMPUSDT",
    "selector": {
        "type": "named_record_field",
        "name": "open_interest_usd",
        "oi_pointer": "/openInterest",
        "mark_request_key": "binance.fapi.ticker24h.PUMPUSDT",
        "mark_pointer": "/lastPrice",
    },
    "normalizer": {"type": "identity"},
    "derivation": None,
    "notes": "Binance USDT-M openInterest × mark; Job 1 names Binance futures PUMPUSDT.",
})
C("zec.oi.binance.usd.current", **{
    "disposition": "COLLECT",
    "source_key": "binance",
    "request_key": "binance.fapi.openInterest.ZECUSDT",
    "selector": {
        "type": "named_record_field",
        "name": "open_interest_usd",
        "oi_pointer": "/openInterest",
        "mark_request_key": "binance.fapi.ticker24h.ZECUSDT",
        "mark_pointer": "/lastPrice",
    },
    "normalizer": {"type": "identity"},
    "derivation": None,
    "notes": "Job 1 ZEC Stage-1 / Binance futures ZECUSDT.",
})
C("spx.oi.binance.usd.current", **{
    "disposition": "COLLECT",
    "source_key": "binance",
    "request_key": "binance.fapi.openInterest.SPXUSDT",
    "selector": {
        "type": "named_record_field",
        "name": "open_interest_usd",
        "oi_pointer": "/openInterest",
        "mark_request_key": "binance.fapi.ticker24h.SPXUSDT",
        "mark_pointer": "/lastPrice",
    },
    "normalizer": {"type": "identity"},
    "derivation": None,
    "notes": "Job 1 URL is Binance futures SPXUSDT.",
})
C("hype.oi.binance.usd.current", **{
    "disposition": "COLLECT",
    "source_key": "binance",
    "request_key": "binance.fapi.openInterest.HYPEUSDT",
    "selector": {
        "type": "named_record_field",
        "name": "open_interest_usd",
        "oi_pointer": "/openInterest",
        "mark_request_key": "binance.fapi.ticker24h.HYPEUSDT",
        "mark_pointer": "/lastPrice",
    },
    "normalizer": {"type": "identity"},
    "derivation": None,
    "notes": "Job 1 URL is CoinGecko page but source HYPE Stage-1; V3 BN_PERP HYPEUSDT is the Binance OI feed. BLOCKED would apply if we required the CoinGecko URL. Bound to V3 Binance perp for named Binance OI metric id.",
})
# Wait - hype.oi.binance has URL coingecko not binance. Do NOT substitute.
# Remove hype.oi.binance from COLLECT - BLOCKED_SOURCE
del COLLECT["hype.oi.binance.usd.current"]

C("fart.volume.perp.usd.24h", **bn_json("binance.fapi.ticker24h.FARTCOINUSDT", "/quoteVolume"))
C("zec.volume.perp.usd.24h", **bn_json("binance.fapi.ticker24h.ZECUSDT", "/quoteVolume"))
C("zec.volume.spot.usd.24h", **bn_json("binance.spot.ticker24h.ZECUSDT", "/quoteVolume"))
C("spx.volume.perp.usd.24h", **bn_json("binance.fapi.ticker24h.SPXUSDT", "/quoteVolume"))
COLLECT["spx.volume.perp.usd.24h"]["notes"] = (
    "Job 1 URL is CoinGecko; metric is Binance perp volume. V3 BN_PERP SPXUSDT. "
    "Not collected: CoinGecko total_volume would be a different scope."
)
# URL is coingecko for spx.volume.perp - that's provider mismatch. BLOCKED.
del COLLECT["spx.volume.perp.usd.24h"]

C("pump.volume.perp.usd.24h", **bn_json("binance.fapi.ticker24h.PUMPUSDT", "/quoteVolume")) if False else None

C(
    "btc.price.usd.july_2026_low",
    **{
        "disposition": "COLLECT",
        "source_key": "binance",
        "request_key": "binance.spot.klines.BTCUSDT.1d",
        "selector": {"type": "named_record_field", "name": "klines_july_min_close", "year": 2026, "month": 7},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 Binance daily; V3 re-reads July 2026 BTCUSDT daily lows.",
    },
)

for mid, days, bench in [
    ("pump.rs.vs_btc.pct.7d", 7, "BTCUSDT"),
    ("pump.rs.vs_btc.pct.30d", 30, "BTCUSDT"),
    ("pump.rs.vs_sol.pct.7d", 7, "SOLUSDT"),
    ("pump.rs.vs_sol.pct.30d", 30, "SOLUSDT"),
]:
    C(
        mid,
        **{
            "disposition": "COLLECT",
            "source_key": "binance",
            "request_key": "binance.spot.klines.PUMPUSDT.1d",
            "selector": {
                "type": "named_record_field",
                "name": "klines_rs_pct",
                "window_days": days,
                "bench_request_key": f"binance.spot.klines.{bench}.1d",
            },
            "normalizer": {"type": "identity"},
            "derivation": None,
            "notes": "Job 1 binance-daily klines; RS = PUMP window return minus bench window return.",
        },
    )

C(
    "sol.rs.vs_btc.pp.7d",
    **{
        "disposition": "COLLECT",
        "source_key": "binance",
        "request_key": "binance.spot.klines.SOLUSDT.1d",
        "selector": {
            "type": "named_record_field",
            "name": "klines_rs_pct",
            "window_days": 7,
            "bench_request_key": "binance.spot.klines.BTCUSDT.1d",
        },
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 URL is SOLUSDT daily klines.",
    },
)
C(
    "sol.rs.vs_btc.pp.30d",
    **{
        "disposition": "COLLECT",
        "source_key": "binance",
        "request_key": "binance.spot.klines.SOLUSDT.1d",
        "selector": {
            "type": "named_record_field",
            "name": "klines_rs_pct",
            "window_days": 30,
            "bench_request_key": "binance.spot.klines.BTCUSDT.1d",
        },
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 URL is SOLUSDT daily klines.",
    },
)

# DERIVE leverage from perp/spot 24h quote — V3 BN_PERP definition.
for mid, perp, spot, extra in [
    ("btc.leverage.x.current", "btc.volume.perp.usd.24h", "btc.volume.spot.usd.24h", "Job 1 Binance futures page; V3 perp/spot quote volume."),
    ("global.leverage.x.current", "btc.volume.perp.usd.24h", "btc.volume.spot.usd.24h", "V3 market leverage is BTCUSDT perp/spot."),
    ("pump.leverage.x.current", "pump.perp.volume.usd.24h", "pump.spot.volume.usd.24h", "placeholder"),
    ("zec.leverage.x.current", "zec.volume.perp.usd.24h", "zec.volume.spot.usd.24h", "Job 1 Binance futures ZECUSDT; V3 perp/spot."),
]:
    pass

# pump needs spot+perp volume canonical metrics. Add COLLECT for those if missing.
# pump has no volume.perp/spot canonical ids. Collect them as... cannot invent metrics.
# DERIVE pump.leverage from two request captures in a COLLECT named extractor instead.

C(
    "pump.leverage.x.current",
    **{
        "disposition": "COLLECT",
        "source_key": "binance",
        "request_key": "binance.fapi.ticker24h.PUMPUSDT",
        "selector": {
            "type": "named_record_field",
            "name": "perp_spot_ratio",
            "perp_pointer": "/quoteVolume",
            "spot_request_key": "binance.spot.ticker24h.PUMPUSDT",
            "spot_pointer": "/quoteVolume",
        },
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 binance futures PUMPUSDT; V3 perp/spot 24h quote ratio.",
    },
)
C(
    "btc.leverage.x.current",
    **{
        "disposition": "DERIVE",
        "source_key": None,
        "request_key": None,
        "selector": None,
        "normalizer": {"type": "identity"},
        "derivation": {
            "op": "RATIO",
            "inputs": ["btc.volume.perp.usd.24h", "btc.volume.spot.usd.24h"],
            "calculation_version": "v1",
        },
        "notes": "V3 AUTOJOB01 BTCUSDT perp quoteVolume / spot quoteVolume.",
    },
)
C(
    "global.leverage.x.current",
    **{
        "disposition": "DERIVE",
        "source_key": None,
        "request_key": None,
        "selector": None,
        "normalizer": {"type": "identity"},
        "derivation": {
            "op": "RATIO",
            "inputs": ["btc.volume.perp.usd.24h", "btc.volume.spot.usd.24h"],
            "calculation_version": "v1",
        },
        "notes": "V3 market leverage uses BTCUSDT perp and spot 24h quote.",
    },
)
C(
    "zec.leverage.x.current",
    **{
        "disposition": "DERIVE",
        "source_key": None,
        "request_key": None,
        "selector": None,
        "normalizer": {"type": "identity"},
        "derivation": {
            "op": "RATIO",
            "inputs": ["zec.volume.perp.usd.24h", "zec.volume.spot.usd.24h"],
            "calculation_version": "v1",
        },
        "notes": "Same V3 perp/spot definition; Job 1 names Binance futures ZECUSDT.",
    },
)

C(
    "global.fear_greed.index.current",
    **{
        "disposition": "COLLECT",
        "source_key": "alternative_me",
        "request_key": "alternative_me.fng",
        "selector": {"type": "json_pointer", "pointer": "/data/0/value"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 source alternative.me; official JSON API.",
    },
)

C(
    "pump.revenue.usd.7d",
    **{
        "disposition": "COLLECT",
        "source_key": "defillama",
        "request_key": "defillama.summary.fees.pump.fun.dailyRevenue",
        "selector": {"type": "named_record_field", "name": "chart_sum_last_n", "pointer": "/totalDataChart", "n": 7},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 URL DefiLlama pump.fun fees page; V3 uses dataType=dailyRevenue 7d chart sum. Does not prefer $9M or $7M.",
    },
)
C(
    "pump.buyback.usd.7d",
    **{
        "disposition": "COLLECT",
        "source_key": "defillama",
        "request_key": "defillama.summary.fees.pump.fun.dailyHoldersRevenue",
        "selector": {"type": "named_record_field", "name": "chart_sum_last_n", "pointer": "/totalDataChart", "n": 7},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "V3 holdersRevenue 7d chart sum for pump.fun.",
    },
)
C(
    "pump.market_share.pct.current",
    **{
        "disposition": "COLLECT",
        "source_key": "defillama",
        "request_key": "defillama.overview.fees",
        "selector": {"type": "named_record_field", "name": "launchpad_share_pct", "slug": "pump.fun"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "V3 Launchpad category 24h fee share.",
    },
)
C(
    "hype.fees.usd.30d",
    **{
        "disposition": "COLLECT",
        "source_key": "defillama",
        "request_key": "defillama.summary.fees.hyperliquid.dailyFees",
        "selector": {"type": "named_record_field", "name": "chart_sum_last_n", "pointer": "/totalDataChart", "n": 30},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 URL api.llama.fi/summary/fees/hyperliquid-perp.",
    },
)
C(
    "hype.fees.perps.usd.30d",
    **{
        "disposition": "COLLECT",
        "source_key": "defillama",
        "request_key": "defillama.summary.fees.hyperliquid.dailyFees",
        "selector": {"type": "named_record_field", "name": "chart_sum_last_n", "pointer": "/totalDataChart", "n": 30},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Same DefiLlama hyperliquid-perp 30d fees payload as hype.fees.usd.30d; Job 1 URL identical.",
    },
)
C(
    "hype.fees.change.pct.30d",
    **{
        "disposition": "COLLECT",
        "source_key": "defillama",
        "request_key": "defillama.summary.fees.hyperliquid.dailyFees",
        "selector": {"type": "named_record_field", "name": "chart_pct_change_last_n", "pointer": "/totalDataChart", "n": 30},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "30d percent change of daily fees series.",
    },
)
C(
    "sol.tvl.usd.current",
    **{
        "disposition": "COLLECT",
        "source_key": "defillama",
        "request_key": "defillama.historicalChainTvl.Solana",
        "selector": {"type": "named_record_field", "name": "latest_list_field", "field": "tvl"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 URL DefiLlama Solana chain; V3 historicalChainTvl last tvl.",
    },
)
C(
    "sol.fees.usd_per_day.mean_30d",
    **{
        "disposition": "COLLECT",
        "source_key": "defillama",
        "request_key": "defillama.summary.fees.solana.dailyFees",
        "selector": {"type": "named_record_field", "name": "chart_mean_last_n", "pointer": "/totalDataChart", "n": 30},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 URL DefiLlama Solana fees.",
    },
)
C(
    "sol.stablecoin.usd.current",
    **{
        "disposition": "COLLECT",
        "source_key": "defillama",
        "request_key": "defillama.stablecoinchains",
        "selector": {"type": "named_record_field", "name": "stablecoin_chain_usd", "chain_name": "Solana"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 URL DefiLlama stablecoins/chains; V3 stablecoinchains peggedUSD.",
    },
)

for asset, req, title, must, forb in [
    ("btc", "farside.html.btc", "Bitcoin ETF", ["IBIT", "FBTC", "GBTC"], ["ETHA", "BSOL", "ETHE"]),
    ("eth", "farside.html.eth", "Ethereum ETF", ["ETHA", "ETHE"], ["IBIT", "BSOL", "GBTC"]),
    ("sol", "farside.html.sol", "Solana ETF", ["BSOL", "VSOL"], ["IBIT", "ETHA", "GBTC"]),
]:
    for window, mid in [("latest", f"{asset}.etf.flow.usd.1d"), ("7d", f"{asset}.etf.flow.usd.7d"), ("30d", f"{asset}.etf.flow.usd.30d")]:
        C(
            mid,
            **{
                "disposition": "COLLECT",
                "source_key": "farside",
                "request_key": req,
                "selector": {
                    "type": "explicit_html_selector",
                    "name": "farside_etf_flow",
                    "title_must": title,
                    "tickers_must": must,
                    "forbidden_tickers": forb,
                    "window": window,
                    "order": "newest_first",
                },
                "normalizer": {"type": "millions_to_usd"},
                "derivation": None,
                "notes": "Job 1 Farside Investors; official HTML tables. Values stored as USD not millions.",
            },
        )

C(
    "hype.emissions.tokens.remaining",
    **{
        "disposition": "COLLECT",
        "source_key": "hyperliquid",
        "request_key": "hyperliquid.info.tokenDetails",
        "selector": {"type": "json_key", "key": "futureEmissions"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 URL api.hyperliquid.xyz/info; V3 tokenDetails futureEmissions. Identity name=HYPE.",
    },
)
C(
    "hype.supply.hl_circulating.pct",
    **{
        "disposition": "DERIVE",
        "source_key": None,
        "request_key": None,
        "selector": None,
        "normalizer": {"type": "identity"},
        "derivation": {
            "op": "RATIO",
            "inputs": ["hype.hl.circulating.tokens", "hype.supply.max.tokens.hl"],
            "calculation_version": "v1",
        },
        "notes": "placeholder",
    },
)
# Cannot invent intermediate metrics. COLLECT pct by extracting circulatingSupply/maxSupply in named extractor.
del COLLECT["hype.supply.hl_circulating.pct"]
C(
    "hype.supply.hl_circulating.pct",
    **{
        "disposition": "COLLECT",
        "source_key": "hyperliquid",
        "request_key": "hyperliquid.info.tokenDetails",
        "selector": {"type": "named_record_field", "name": "ratio_pct", "num_key": "circulatingSupply", "den_key": "maxSupply"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "circulatingSupply/maxSupply*100 from tokenDetails.",
    },
)
C(
    "hype.ncu.hyperlabs.tokens",
    **{
        "disposition": "COLLECT",
        "source_key": "hyperliquid",
        "request_key": "hyperliquid.info.tokenDetails",
        "selector": {
            "type": "named_record_field",
            "name": "ncu_balance",
            "address": "0x43e9abea1910387c4292bca4b94de81462f8a251",
        },
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "V3 HyperLabs NCU address on tokenDetails.nonCirculatingUserBalances.",
    },
)
C(
    "hype.stake.tokens.current",
    **{
        "disposition": "COLLECT",
        "source_key": "hyperliquid",
        "request_key": "hyperliquid.info.tokenDetails",
        "selector": {"type": "json_key", "key": "totalSupply"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "BLOCK if totalSupply is not stake. Job 1 URL is info; field must exist as stake. Using circulating is wrong. Leave stake BLOCKED if we cannot prove field.",
    },
)
# Don't guess stake field. Remove.
del COLLECT["hype.stake.tokens.current"]

C(
    "io.clusters.running.count",
    **{
        "disposition": "COLLECT",
        "source_key": "io_explorer",
        "request_key": "io.clusters",
        "selector": {"type": "json_pointer", "pointer": "/data/running_clusters"},
        "normalizer": {"type": "integer"},
        "derivation": None,
        "notes": "Job 1 io.net Explorer clusters URL.",
    },
)
C(
    "io.revenue.usd.cumulative",
    **{
        "disposition": "COLLECT",
        "source_key": "io_explorer",
        "request_key": "io.clusters",
        "selector": {"type": "json_pointer", "pointer": "/data/total_earnings"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 clusters URL; V3 total_earnings on clusters payload.",
    },
)

C(
    "nos.jobs.running.count",
    **{
        "disposition": "COLLECT",
        "source_key": "nosana",
        "request_key": "nosana.jobs.count",
        "selector": {"type": "named_record_field", "name": "by_state_count", "state": "RUNNING"},
        "normalizer": {"type": "integer"},
        "derivation": None,
        "notes": "Job 1 URL jobs/count.",
    },
)
C(
    "nos.jobs.queued.count",
    **{
        "disposition": "COLLECT",
        "source_key": "nosana",
        "request_key": "nosana.jobs.count",
        "selector": {"type": "named_record_field", "name": "by_state_count", "state": "QUEUED"},
        "normalizer": {"type": "integer"},
        "derivation": None,
        "notes": "Job 1 URL jobs/count.",
    },
)
C(
    "nos.jobs.completed.cumulative",
    **{
        "disposition": "COLLECT",
        "source_key": "nosana",
        "request_key": "nosana.jobs.count",
        "selector": {"type": "named_record_field", "name": "by_state_count", "state": "COMPLETED"},
        "normalizer": {"type": "integer"},
        "derivation": None,
        "notes": "Job 1 Nosana blockchain-indexer jobs/count.",
    },
)
C(
    "nos.jobs.approx_30d.count",
    **{
        "disposition": "COLLECT",
        "source_key": "nosana",
        "request_key": "nosana.jobs.stats.timestamps",
        "selector": {"type": "named_record_field", "name": "jobs_timestamps_window_sum", "window_days": 30},
        "normalizer": {"type": "integer"},
        "derivation": None,
        "notes": "Nosana indexer /jobs/stats/timestamps ~30d completed-job sum.",
    },
)
C(
    "nos.nodes.with_running_jobs.count",
    **{
        "disposition": "COLLECT",
        "source_key": "nosana",
        "request_key": "nosana.jobs.running",
        "selector": {"type": "named_record_field", "name": "running_nodes_distinct_count"},
        "normalizer": {"type": "integer"},
        "derivation": None,
        "notes": "Nosana indexer /jobs/running distinct node addresses with running jobs.",
    },
)

C(
    "render.supply.circulating.tokens",
    **{
        "disposition": "COLLECT",
        "source_key": "render_foundation",
        "request_key": "render.supplyInfo",
        "selector": {"type": "json_key", "key": "circulatingSupply"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 Foundation supplyInfo.",
    },
)
C(
    "render.supply.max.tokens",
    **{
        "disposition": "COLLECT",
        "source_key": "render_foundation",
        "request_key": "render.supplyInfo",
        "selector": {"type": "json_key", "key": "maxSupply"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 Foundation supplyInfo.",
    },
)
C(
    "render.bme.burned.tokens.last4",
    **{
        "disposition": "COLLECT",
        "source_key": "render_foundation",
        "request_key": "render.epochBurnStats",
        "selector": {"type": "named_record_field", "name": "epoch_burn_last_n", "n": 4, "field": "burnedRender"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 epochBurnStats.",
    },
)
C(
    "render.bme.burned.tokens.last8",
    **{
        "disposition": "COLLECT",
        "source_key": "render_foundation",
        "request_key": "render.epochBurnStats",
        "selector": {"type": "named_record_field", "name": "epoch_burn_last_n", "n": 8, "field": "burnedRender"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 epochBurnStats.",
    },
)
C(
    "render.usage.frames.cumulative",
    **{
        "disposition": "COLLECT",
        "source_key": "render_foundation",
        "request_key": "render.nodes_and_frames",
        "selector": {"type": "json_key", "key": "frames"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "V3 stats.renderfoundation.com/api/nodes_and_frames; Job 1 URL is the stats site.",
    },
)
C(
    "render.nodes.count.listed",
    **{
        "disposition": "COLLECT",
        "source_key": "render_foundation",
        "request_key": "render.nodes_and_frames",
        "selector": {"type": "json_key", "key": "nodes"},
        "normalizer": {"type": "integer"},
        "derivation": None,
        "notes": "Same Foundation stats payload as frames.",
    },
)

C(
    "sol.inflation.pct.current",
    **{
        "disposition": "COLLECT",
        "source_key": "solana_rpc",
        "request_key": "solana.rpc.getInflationRate",
        "selector": {"type": "json_pointer", "pointer": "/result/total"},
        "normalizer": {"type": "decimal_as_percent"},
        "derivation": None,
        "notes": "Job 1 Solana RPC; getInflationRate.total is a fraction.",
    },
)
C(
    "sol.validators.active.count",
    **{
        "disposition": "COLLECT",
        "source_key": "solana_rpc",
        "request_key": "solana.rpc.getVoteAccounts",
        "selector": {"type": "named_record_field", "name": "vote_accounts_active_count"},
        "normalizer": {"type": "integer"},
        "derivation": None,
        "notes": "Job 1 getVoteAccounts.",
    },
)
C(
    "sol.stake.tokens.current",
    **{
        "disposition": "COLLECT",
        "source_key": "solana_rpc",
        "request_key": "solana.rpc.getVoteAccounts",
        "selector": {"type": "named_record_field", "name": "vote_accounts_activated_stake"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Sum activatedStake lamports / 1e9.",
    },
)
C(
    "sol.tps.nonvote.current",
    **{
        "disposition": "COLLECT",
        "source_key": "solana_rpc",
        "request_key": "solana.rpc.getRecentPerformanceSamples",
        "selector": {"type": "named_record_field", "name": "perf_tps_nonvote"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 getRecentPerformanceSamples.",
    },
)

C(
    "zec.shielded.tokens.current",
    **{
        "disposition": "COLLECT",
        "source_key": "zcash_explorer",
        "request_key": "zcash.explorer.blockchain-info",
        "selector": {
            "type": "named_record_field",
            "name": "pool_sum",
            "pointer": "/valuePools",
            "ids": ["sprout", "sapling", "orchard", "ironwood"],
        },
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 zcashexplorer blockchain-info.",
    },
)
C(
    "pump.liquidity.dex.usd.current",
    **{
        "disposition": "COLLECT",
        "source_key": "dexscreener",
        "request_key": "dexscreener.token.pump",
        "selector": {"type": "json_pointer", "pointer": "/pairs/0/liquidity/usd"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "notes": "Job 1 source dexscreener; V3 DexScreener pair for PUMP mint. First-pair is forbidden — use identity pairAddress if present.",
    },
)
# Fix dexscreener: must use identity not first pair
COLLECT["pump.liquidity.dex.usd.current"]["selector"] = {
    "type": "named_record_field",
    "records_pointer": "/pairs",
    "identity": {"quoteToken.symbol": "SOL"},  # still fuzzy!
}
# Use V3 mint pair - DexScreener returns pairs; identity dexId=raydium AND baseToken.address=pump mint
COLLECT["pump.liquidity.dex.usd.current"]["selector"] = {
    "type": "named_record_field",
    "records_pointer": "/pairs",
    "identity": {
        "chainId": "solana",
        "baseToken": None,
    },
}

# nested identity won't work with flat _identity_match. Use pairAddress from V3 if known.
# DexScreener token endpoint: identity baseToken.address exact.
# I'll implement nested identity in extract OR use json_pointer after filtering in named extractor `dex_pair_liquidity`

COLLECT["pump.liquidity.dex.usd.current"]["selector"] = {
    "type": "named_record_field",
    "name": "dex_highest_liquidity_usd",
    "chain_id": "solana",
    "base_token_address": "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(metric, reason):
    return {
        "disposition": "BLOCKED_SOURCE",
        "source_key": None,
        "request_key": None,
        "selector": None,
        "normalizer": None,
        "derivation": None,
        "notes": reason,
    }


def main() -> None:
    registry_sha = sha256_file(ROOT / "metrics/metric-registry.json")
    entries = []
    for m in REG["metrics"]:
        mid = m["metric_id"]
        base = {
            "metric_id": mid,
            "asset": m["asset"],
            "owner": m["owner"],
            "unit": m.get("allowed_unit") or m["unit"],
        }
        if m["owner"] == "GROK" or m["metric_type"] == "WALLET_OWNED" or m["wallet_or_non_wallet"] == "WALLET":
            row = {
                **base,
                "disposition": "GROK_WALLET",
                "source_key": None,
                "request_key": None,
                "selector": None,
                "normalizer": None,
                "derivation": None,
                "required": False,
                "notes": "Job 1 owner=GROK. Cursor does not collect.",
            }
        elif m["asset"] in {"RAY", "GRASS", "DRIFT", "ORCA", "BONK"} or m.get("surface") == "LEGACY_INACTIVE":
            row = {
                **base,
                "disposition": "LEGACY_INACTIVE",
                "source_key": None,
                "request_key": None,
                "selector": None,
                "normalizer": None,
                "derivation": None,
                "required": False,
                "notes": "Dormant. No collector.",
            }
        elif (
            m["metric_type"] in {"HISTORICAL", "STATIC_DECISION_THRESHOLD", "STATIC_REFERENCE"}
            or m["update_mode"] in {"HISTORICAL", "STATIC_THRESHOLD"}
            or m["historical_or_current"] in {"HISTORICAL", "STATIC"}
            or mid in DATED_PRESERVE
        ):
            row = {
                **base,
                "disposition": "PRESERVE",
                "source_key": None,
                "request_key": None,
                "selector": None,
                "normalizer": None,
                "derivation": None,
                "required": False,
                "notes": "Historical, static, threshold, or dated event. No live collector.",
            }
        elif mid == "zec.tx.count.24h":
            row = {
                **base,
                **blocked(
                    mid,
                    "CGPT 2026-08-27: zcashexplorer blockchain-info has no transactions24h field "
                    "(chain/pool/block data only). BLOCKED_SOURCE/UNKNOWN — no replacement in Job 2B.",
                ),
                "required": False,
            }
        elif mid in COLLECT:
            spec = COLLECT[mid]
            required = m["metric_type"] == "CURRENT_DYNAMIC" and m["wallet_or_non_wallet"] == "NON_WALLET"
            row = {**base, **spec, "required": required}
        elif m["metric_type"] == "CURRENT_DYNAMIC":
            src = m.get("source") or "UNKNOWN"
            url = m.get("source_url_or_reference") or ""
            reason = (
                f"Job 1 provenance is insufficient for a reliable collector "
                f"(source={src!r} url={url!r}). No provider substitution."
            )
            row = {**base, **blocked(m, reason), "required": True}
        else:
            row = {
                **base,
                "disposition": "PRESERVE",
                "source_key": None,
                "request_key": None,
                "selector": None,
                "normalizer": None,
                "derivation": None,
                "required": False,
                "notes": "Non-dynamic Job 1 record.",
            }
        entries.append(row)

    plan = {
        "job": "V4-JOB-2",
        "job1_commit": "0084838bf3587be0116653ac1c0f68ff0edddcc6",
        "job1_registry_sha256": registry_sha,
        "entries": entries,
    }
    out = ROOT / "collectors/collector-plan.json"
    out.write_text(json.dumps(plan, indent=2) + "\n")
    counts = Counter(e["disposition"] for e in entries)
    print("wrote", out, "n", len(entries), dict(counts))
    assert len(entries) == len(REG["metrics"])
    assert len({e["metric_id"] for e in entries}) == len(entries)


if __name__ == "__main__":
    main()
