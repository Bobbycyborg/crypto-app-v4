"""Explicit identity + source contracts. No fuzzy ticker matching."""

from __future__ import annotations

from typing import Any

# CoinGecko id is explicit. Binance pair is spot only (None = not used as spot).
# Dex mint is Solana mint or None.
PRICE_ASSETS: dict[str, dict[str, Any]] = {
    "BTC": {
        "slug": "btc",
        "coingecko_id": "bitcoin",
        "binance_spot": "BTCUSDT",
        "dex_mint": None,
        "owned": "dash",  # stays — until Coinbase
    },
    "SOL": {
        "slug": "sol",
        "coingecko_id": "solana",
        "binance_spot": "SOLUSDT",
        "dex_mint": "So11111111111111111111111111111111111111112",
        "owned": "solana_rpc",
    },
    "RENDER": {
        "slug": "render",
        "coingecko_id": "render-token",
        "binance_spot": "RENDERUSDT",
        "dex_mint": "rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof",
        "owned": "solana_rpc",
    },
    "PUMP": {
        "slug": "pump",
        "coingecko_id": "pump-fun",
        "binance_spot": None,
        "dex_mint": "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
        "owned": "solana_rpc",
    },
    "GRASS": {
        "slug": "grass",
        "coingecko_id": "grass",
        "binance_spot": None,
        "dex_mint": "Grass7B4RdKfBCjTKgSqnXkqjwiGvQyFbuSCUJr3XXjs",
        "owned": "solana_rpc",
    },
    "RAY": {
        "slug": "ray",
        "coingecko_id": "raydium",
        "binance_spot": "RAYUSDT",
        "dex_mint": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        "owned": "solana_rpc",
    },
    "IO": {
        "slug": "io",
        "coingecko_id": "io",
        "binance_spot": "IOUSDT",
        "dex_mint": "BZLbGTNCSFfoth2GYDtwr7e4imWzpR5jqcUuGEwr646K",
        "owned": "solana_rpc",
    },
    "NOS": {
        "slug": "nos",
        "coingecko_id": "nosana",
        "binance_spot": None,
        "dex_mint": "nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7",
        "owned": "solana_rpc",
    },
    "FARTCOIN": {
        "slug": "fartcoin",
        "coingecko_id": "fartcoin",
        "binance_spot": "FARTCOINUSDT",
        "dex_mint": "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
        "owned": "solana_rpc",
    },
    "SPX6900": {
        "slug": "spx6900",
        "html_ticker": "SPX6900",
        "hero_ticker": "SPX",
        "coingecko_id": "spx6900",
        "binance_spot": None,
        "dex_mint": "J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr",
        "owned": "solana_rpc",
    },
    "ZEC": {
        "slug": "zec",
        "coingecko_id": "zcash",
        "binance_spot": "ZECUSDT",
        "dex_mint": None,
        "owned": "unknown",  # not in Solana wallet
    },
    "HYPE": {
        "slug": "hype",
        "coingecko_id": "hyperliquid",
        "binance_spot": None,  # Binance.com spot NOT LISTED — perp is not spot
        "dex_mint": None,
        "owned": "unknown",  # not in assets.json
    },
}

MARKET_SOURCES = {
    "macro_fred": ["WALCL", "WDTGAL", "RRPONTSYD", "M2SL", "NFCI", "ECBASSETSW", "JPNASSETS"],
    "macro_defillama": "https://stablecoins.llama.fi/stablecoincharts/all",
    "btc_ath": "coingecko coins/bitcoin ath",
    "july_floor": "binance BTCUSDT daily klines — re-read July 2026 low",
    "rotation_participation": "coingecko markets (existing V3 method)",
    "fear_greed": "https://api.alternative.me/fng/",
    "btc_leverage": "binance BTCUSDT perp 24h AND spot 24h",
    "etf": ["https://farside.co.uk/btc/", "https://farside.co.uk/eth/", "https://farside.co.uk/sol/"],
}
