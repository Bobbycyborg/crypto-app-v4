"""Explicit request catalog. One key = one HTTP call. No per-metric fetching."""

from __future__ import annotations

from typing import Any

COINGECKO_IDS = [
    "bitcoin",
    "solana",
    "render-token",
    "pump-fun",
    "io",
    "nosana",
    "fartcoin",
    "spx6900",
    "zcash",
    "hyperliquid",
]

FARSIDE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
}

REQUESTS: dict[str, dict[str, Any]] = {
    "coingecko.markets.active": {
        "source_key": "coingecko",
        "method": "GET",
        "url": "https://api.coingecko.com/api/v3/coins/markets",
        "params": {
            "vs_currency": "usd",
            "ids": ",".join(COINGECKO_IDS),
            "price_change_percentage": "7d,30d,90d",
            "per_page": 50,
            "page": 1,
        },
        "auth": "coingecko_optional",
    },
    "alternative_me.fng": {
        "source_key": "alternative_me",
        "method": "GET",
        "url": "https://api.alternative.me/fng/",
        "params": {"limit": 1},
    },
    "defillama.summary.fees.pump.fun.dailyRevenue": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/summary/fees/pump.fun",
        "params": {"dataType": "dailyRevenue"},
    },
    "defillama.summary.fees.pump.fun.dailyHoldersRevenue": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/summary/fees/pump.fun",
        "params": {"dataType": "dailyHoldersRevenue"},
    },
    "defillama.summary.fees.pump.fun.dailyFees": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/summary/fees/pump.fun",
        "params": {"dataType": "dailyFees"},
    },
    "defillama.overview.fees": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/overview/fees",
        "params": {"excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true"},
    },
    "defillama.summary.fees.hyperliquid-perp.dailyFees": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/summary/fees/hyperliquid-perp",
        "params": {"dataType": "dailyFees"},
    },
    "defillama.summary.fees.hyperliquid.dailyFees": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/summary/fees/hyperliquid",
        "params": {"dataType": "dailyFees"},
    },
    "defillama.historicalChainTvl.Solana": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/v2/historicalChainTvl/Solana",
    },
    "defillama.summary.fees.solana.dailyFees": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/summary/fees/solana",
        "params": {"dataType": "dailyFees"},
    },
    "defillama.stablecoinchains": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://stablecoins.llama.fi/stablecoinchains",
    },
    "defillama.overview.dexs.solana": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/overview/dexs/solana",
    },
    "farside.html.btc": {
        "source_key": "farside",
        "method": "GET",
        "url": "https://farside.co.uk/btc/",
        "headers": FARSIDE_HEADERS,
        "response_kind": "html",
    },
    "farside.html.eth": {
        "source_key": "farside",
        "method": "GET",
        "url": "https://farside.co.uk/eth/",
        "headers": FARSIDE_HEADERS,
        "response_kind": "html",
    },
    "farside.html.sol": {
        "source_key": "farside",
        "method": "GET",
        "url": "https://farside.co.uk/sol/",
        "headers": FARSIDE_HEADERS,
        "response_kind": "html",
    },
    "hyperliquid.info.tokenDetails": {
        "source_key": "hyperliquid",
        "method": "POST",
        "url": "https://api.hyperliquid.xyz/info",
        "json_body": {"type": "tokenDetails", "tokenId": "0x0d01dc56dcaaca66ad901c959b4011ec"},
        "identity": {"name": "HYPE"},
    },
    "io.clusters": {
        "source_key": "io_explorer",
        "method": "GET",
        "url": "https://api.io.solutions/v1/io-explorer/network/info/clusters",
    },
    "nosana.jobs.count": {
        "source_key": "nosana",
        "method": "GET",
        "url": "https://blockchain-indexer.k8s.prd.nos.ci/jobs/count",
    },
    "render.supplyInfo": {
        "source_key": "render_foundation",
        "method": "GET",
        "url": "https://infra.shikumi.cc/api/v1/supplyInfo",
        "headers": {
            "Origin": "https://stats.renderfoundation.com",
            "Referer": "https://stats.renderfoundation.com/",
        },
    },
    "render.epochBurnStats": {
        "source_key": "render_foundation",
        "method": "POST",
        "url": "https://infra.shikumi.cc/api/v1/epochBurnStats",
        "json_body": {"start": 0},
        "headers": {
            "Origin": "https://stats.renderfoundation.com",
            "Referer": "https://stats.renderfoundation.com/",
        },
    },
    "render.nodes_and_frames": {
        "source_key": "render_foundation",
        "method": "GET",
        "url": "https://stats.renderfoundation.com/api/nodes_and_frames",
    },
    "solana.rpc.getInflationRate": {
        "source_key": "solana_rpc",
        "method": "POST",
        "url": "https://api.mainnet-beta.solana.com",
        "json_body": {"jsonrpc": "2.0", "id": 1, "method": "getInflationRate", "params": []},
    },
    "solana.rpc.getVoteAccounts": {
        "source_key": "solana_rpc",
        "method": "POST",
        "url": "https://api.mainnet-beta.solana.com",
        "json_body": {"jsonrpc": "2.0", "id": 1, "method": "getVoteAccounts", "params": []},
    },
    "solana.rpc.getRecentPerformanceSamples": {
        "source_key": "solana_rpc",
        "method": "POST",
        "url": "https://api.mainnet-beta.solana.com",
        "json_body": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getRecentPerformanceSamples",
            "params": [1],
        },
    },
    "zcash.explorer.blockchain-info": {
        "source_key": "zcash_explorer",
        "method": "GET",
        "url": "https://mainnet.zcashexplorer.app/api/v1/blockchain-info",
    },
    "dexscreener.token.pump": {
        "source_key": "dexscreener",
        "method": "GET",
        "url": "https://api.dexscreener.com/latest/dex/tokens/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
    },
    "dexscreener.token.2z": {
        "source_key": "dexscreener",
        "method": "GET",
        "url": "https://api.dexscreener.com/latest/dex/tokens/J6pQQ3FAcJQeWPPGppWRb4nM8jU3wLyYbRrLh7feMfvd",
    },
    "dexscreener.token.giga": {
        "source_key": "dexscreener",
        "method": "GET",
        "url": "https://api.dexscreener.com/latest/dex/tokens/63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9",
    },
    "dexscreener.token.lockin": {
        "source_key": "dexscreener",
        "method": "GET",
        "url": "https://api.dexscreener.com/latest/dex/tokens/8Ki8DpuWNxu9VsS3kQbarsCWMcFGWkzzA8pUPto9zBd5",
    },
    "dexscreener.token.retardio": {
        "source_key": "dexscreener",
        "method": "GET",
        "url": "https://api.dexscreener.com/latest/dex/tokens/6ogzHhzdrQr9Pgv6hZ2MNze7UrzBMAFyBBWUYp1Fhitx",
    },
    "dexscreener.token.fartcoin": {
        "source_key": "dexscreener",
        "method": "GET",
        "url": "https://api.dexscreener.com/latest/dex/tokens/9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
    },
    "binance.spot.tickerPrice.BONKUSDT": {
        "source_key": "binance",
        "method": "GET",
        "url": "https://api.binance.com/api/v3/ticker/price",
        "params": {"symbol": "BONKUSDT"},
        "identity": {"symbol": "BONKUSDT"},
    },
    "binance.spot.tickerPrice.ORCAUSDT": {
        "source_key": "binance",
        "method": "GET",
        "url": "https://api.binance.com/api/v3/ticker/price",
        "params": {"symbol": "ORCAUSDT"},
        "identity": {"symbol": "ORCAUSDT"},
    },
    "defillama.overview.fees.dailyHoldersRevenue": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/overview/fees",
        "params": {
            "dataType": "dailyHoldersRevenue",
            "excludeTotalDataChart": "true",
            "excludeTotalDataChartBreakdown": "true",
        },
    },
    "defillama.stablecoincharts.all": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://stablecoins.llama.fi/stablecoincharts/all",
    },
    "defillama.overview.dexs.ethereum": {
        "source_key": "defillama",
        "method": "GET",
        "url": "https://api.llama.fi/overview/dexs/ethereum",
        "params": {"excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true"},
    },
    "binance.fapi.openInterestHist.BTCUSDT.1d": {
        "source_key": "binance",
        "method": "GET",
        "url": "https://fapi.binance.com/futures/data/openInterestHist",
        "params": {"symbol": "BTCUSDT", "period": "1d", "limit": 31},
    },
    "binance.fapi.openInterestHist.SPXUSDT.1d": {
        "source_key": "binance",
        "method": "GET",
        "url": "https://fapi.binance.com/futures/data/openInterestHist",
        "params": {"symbol": "SPXUSDT", "period": "1d", "limit": 31},
    },
    "binance.fapi.fundingRate.SOLUSDT": {
        "source_key": "binance",
        "method": "GET",
        "url": "https://fapi.binance.com/fapi/v1/fundingRate",
        "params": {"symbol": "SOLUSDT", "limit": 7},
    },
    "render.dashboard.main": {
        "source_key": "render_foundation",
        "method": "GET",
        "url": "https://stats.renderfoundation.com/",
        "response_kind": "html",
        "headers": {"User-Agent": "Mozilla/5.0 crypto-app-v4-job2"},
    },
    "render.liabilityEpochs": {
        "source_key": "render_foundation",
        "method": "GET",
        "url": "https://infra.shikumi.cc/api/v1/liabilityEpochs",
        "headers": {
            "Origin": "https://stats.renderfoundation.com",
            "Referer": "https://stats.renderfoundation.com/",
        },
    },
    "io.inventory": {
        "source_key": "io_explorer",
        "method": "GET",
        "url": "https://api.io.solutions/v1/io-explorer/network/inventory-aggregated",
    },
    "io.total_earnings_summary": {
        "source_key": "io_explorer",
        "method": "GET",
        "url": "https://api.io.solutions/v1/io-explorer/network/info/cluster/total-earnings-summary",
    },
    "coingecko.market_chart.nosana": {
        "source_key": "coingecko",
        "method": "GET",
        "url": "https://api.coingecko.com/api/v3/coins/nosana/market_chart",
        "params": {"vs_currency": "usd", "days": 250, "interval": "daily"},
        "auth": "coingecko_optional",
    },
    "coingecko.market_chart.bitcoin.90d": {
        "source_key": "coingecko",
        "method": "GET",
        "url": "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
        "params": {"vs_currency": "usd", "days": 90, "interval": "daily"},
        "auth": "coingecko_optional",
    },
    "coingecko.market_chart.fartcoin.90d": {
        "source_key": "coingecko",
        "method": "GET",
        "url": "https://api.coingecko.com/api/v3/coins/fartcoin/market_chart",
        "params": {"vs_currency": "usd", "days": 90, "interval": "daily"},
        "auth": "coingecko_optional",
    },
    "hyperliquid.info.metaAndAssetCtxs": {
        "source_key": "hyperliquid",
        "method": "POST",
        "url": "https://api.hyperliquid.xyz/info",
        "json_body": {"type": "metaAndAssetCtxs"},
    },
    "hyperliquid.info.validatorSummaries": {
        "source_key": "hyperliquid",
        "method": "POST",
        "url": "https://api.hyperliquid.xyz/info",
        "json_body": {"type": "validatorSummaries"},
    },
    "nosana.stats": {
        "source_key": "nosana",
        "method": "GET",
        "url": "https://blockchain-indexer.k8s.prd.nos.ci/stats",
    },
    "nosana.jobs.stats": {
        "source_key": "nosana",
        "method": "GET",
        "url": "https://blockchain-indexer.k8s.prd.nos.ci/jobs/stats",
    },
    "nosana.jobs.timestamps_hours": {
        "source_key": "nosana",
        "method": "GET",
        "url": "https://blockchain-indexer.k8s.prd.nos.ci/jobs/stats/timestamps-hours",
    },
    "solana.rpc.getSupply": {
        "source_key": "solana_rpc",
        "method": "POST",
        "url": "https://api.mainnet-beta.solana.com",
        "json_body": {"jsonrpc": "2.0", "id": 1, "method": "getSupply", "params": []},
    },
    "solana.rpc.getTokenSupply.pump": {
        "source_key": "solana_rpc",
        "method": "POST",
        "url": "https://api.mainnet-beta.solana.com",
        "json_body": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenSupply",
            "params": ["pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn"],
        },
    },
    "solana.rpc.getTokenLargestAccounts.spx": {
        "source_key": "solana_rpc",
        "method": "POST",
        "url": "https://api.mainnet-beta.solana.com",
        "json_body": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenLargestAccounts",
            "params": ["J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr"],
        },
    },
    "solana.rpc.getTokenSupply.spx": {
        "source_key": "solana_rpc",
        "method": "POST",
        "url": "https://api.mainnet-beta.solana.com",
        "json_body": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenSupply",
            "params": ["J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr"],
        },
    },
    "coinbase.spot.stats.FARTCOIN-USD": {
        "source_key": "coinbase",
        "method": "GET",
        "url": "https://api.exchange.coinbase.com/products/FARTCOIN-USD/stats",
    },
    "coingecko.market_charts.breadth_bundle": {
        "source_key": "coingecko",
        "method": "GET",
        "url": "file://tests/job2/fixtures/local/breadth_market_charts.json",
    },
    "forensics.pump.ownership_vesting": {
        "source_key": "forensics",
        "method": "GET",
        "url": "file://tests/job2/fixtures/local/pump_ownership_vesting.json",
    },
    "stage1.fart.top20_classified": {
        "source_key": "stage1_evidence",
        "method": "GET",
        "url": "file://tests/job2/fixtures/local/fart_top20.json",
    },
}

BINANCE_FAPI_SYMBOLS = [
    "BTCUSDT",
    "SOLUSDT",
    "RENDERUSDT",
    "PUMPUSDT",
    "IOUSDT",
    "FARTCOINUSDT",
    "ZECUSDT",
    "HYPEUSDT",
    "SPXUSDT",
]
BINANCE_SPOT_SYMBOLS = ["BTCUSDT", "SOLUSDT", "RENDERUSDT", "PUMPUSDT", "IOUSDT", "ZECUSDT", "BONKUSDT", "ORCAUSDT"]
BINANCE_KLINES = ["BTCUSDT", "SOLUSDT", "PUMPUSDT", "IOUSDT", "RENDERUSDT", "ZECUSDT"]
BINANCE_FAPI_KLINES = ["FARTCOINUSDT", "HYPEUSDT", "SOLUSDT", "SPXUSDT"]

for _sym in BINANCE_FAPI_SYMBOLS:
    REQUESTS[f"binance.fapi.premiumIndex.{_sym}"] = {
        "source_key": "binance",
        "method": "GET",
        "url": "https://fapi.binance.com/fapi/v1/premiumIndex",
        "params": {"symbol": _sym},
        "identity": {"symbol": _sym},
    }
    REQUESTS[f"binance.fapi.openInterest.{_sym}"] = {
        "source_key": "binance",
        "method": "GET",
        "url": "https://fapi.binance.com/fapi/v1/openInterest",
        "params": {"symbol": _sym},
        "identity": {"symbol": _sym},
    }
    REQUESTS[f"binance.fapi.ticker24h.{_sym}"] = {
        "source_key": "binance",
        "method": "GET",
        "url": "https://fapi.binance.com/fapi/v1/ticker/24hr",
        "params": {"symbol": _sym},
        "identity": {"symbol": _sym},
    }

for _sym in BINANCE_SPOT_SYMBOLS:
    REQUESTS[f"binance.spot.ticker24h.{_sym}"] = {
        "source_key": "binance",
        "method": "GET",
        "url": "https://api.binance.com/api/v3/ticker/24hr",
        "params": {"symbol": _sym},
        "identity": {"symbol": _sym},
    }

for _sym in BINANCE_KLINES:
    REQUESTS[f"binance.spot.klines.{_sym}.1d"] = {
        "source_key": "binance",
        "method": "GET",
        "url": "https://api.binance.com/api/v3/klines",
        "params": {"symbol": _sym, "interval": "1d", "limit": 400},
        "identity": {"symbol": _sym},
    }

for _sym in BINANCE_FAPI_KLINES:
    REQUESTS[f"binance.fapi.klines.{_sym}.1d"] = {
        "source_key": "binance",
        "method": "GET",
        "url": "https://fapi.binance.com/fapi/v1/klines",
        "params": {"symbol": _sym, "interval": "1d", "limit": 400},
        "identity": {"symbol": _sym},
    }
