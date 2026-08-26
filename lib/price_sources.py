"""Individual price source fetchers — each returns USD or None."""

from __future__ import annotations

from typing import Any

import certifi
import requests

from lib.coingecko_api import simple_price

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "SOL": "solana",
    "RENDER": "render-token",
    "IO": "io",
    "NOS": "nosana",
    "GRASS": "grass",
    "FARTCOIN": "fartcoin",
    "SPX6900": "spx6900",
    "PUMP": "pump-fun",
    "RAY": "raydium",
    "ZEC": "zcash",
    "HYPE": "hyperliquid",
}

BINANCE_SYMBOLS = {
    "BTC": "BTCUSDT",
    "SOL": "SOLUSDT",
    "RENDER": "RENDERUSDT",
    "IO": "IOUSDT",
    "FARTCOIN": "FARTCOINUSDT",
    "RAY": "RAYUSDT",
    "ZEC": "ZECUSDT",
}

COINBASE_SYMBOLS = {
    "BTC": "BTC-USD",
    "SOL": "SOL-USD",
    "ETH": "ETH-USD",
}

SOL_MINT = "So11111111111111111111111111111111111111112"


def _get_json(url: str, params: dict | None = None, timeout: int = 25) -> Any:
    r = requests.get(url, params=params, timeout=timeout, verify=certifi.where())
    r.raise_for_status()
    return r.json()


def fetch_coingecko(symbol: str, batch: dict[str, Any] | None = None) -> float | None:
    cg_id = COINGECKO_IDS.get(symbol)
    if not cg_id:
        return None
    if batch is not None:
        row = batch.get(cg_id)
        if row and row.get("usd") is not None:
            return float(row["usd"])
        return None
    data = simple_price([cg_id])
    row = data.get(cg_id)
    if row and row.get("usd") is not None:
        return float(row["usd"])
    return None


def fetch_coingecko_batch(symbols: list[str]) -> dict[str, Any]:
    ids = [COINGECKO_IDS[s] for s in symbols if s in COINGECKO_IDS]
    return simple_price(ids) if ids else {}


def fetch_dexscreener_selection(
    mint: str | None,
    *,
    symbol: str | None = None,
    chain: str = "solana",
    pairs: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Identity-selected Dex pair for audit. Same selection as fetch_dexscreener."""
    if not mint:
        return None
    try:
        from lib.dex_identity import select_dex_usd_price

        if pairs is None:
            body = _get_json(f"https://api.dexscreener.com/latest/dex/tokens/{mint}")
            pairs = body.get("pairs") or []
        selected = select_dex_usd_price(pairs, mint, symbol=symbol, chain=chain)
        if not selected:
            return None
        return {
            "pair_address": selected.get("pair_address"),
            "base_symbol": selected.get("base_symbol"),
            "quote_symbol": selected.get("quote_symbol"),
            "orientation": selected.get("orientation"),
            "liquidity_usd": selected.get("liquidity_usd"),
            "priceUsd_raw": selected.get("priceUsd_raw"),
            "price_usd": float(selected["price_usd"]),
        }
    except Exception:
        return None


def fetch_dexscreener(
    mint: str | None,
    *,
    symbol: str | None = None,
    chain: str = "solana",
    pairs: list[dict[str, Any]] | None = None,
) -> float | None:
    """USD price for `mint`, or None if no identity-valid Dex pair exists."""
    selected = fetch_dexscreener_selection(
        mint, symbol=symbol, chain=chain, pairs=pairs
    )
    if not selected:
        return None
    return float(selected["price_usd"])


def fetch_binance(symbol: str) -> float | None:
    pair = BINANCE_SYMBOLS.get(symbol)
    if not pair:
        return None
    try:
        body = _get_json("https://api.binance.com/api/v3/ticker/price", {"symbol": pair})
        return float(body["price"])
    except Exception:
        return None


def fetch_geckoterminal(mint: str | None) -> float | None:
    if not mint:
        return None
    try:
        body = _get_json(
            f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{mint}"
        )
        price = (body.get("data") or {}).get("attributes", {}).get("price_usd")
        return float(price) if price is not None else None
    except Exception:
        return None


def fetch_jupiter(mint: str | None) -> float | None:
    """Deprecated — Jupiter price API unreachable; kept for registry compat."""
    return fetch_geckoterminal(mint)


def fetch_coinbase(symbol: str) -> float | None:
    pair = COINBASE_SYMBOLS.get(symbol)
    if not pair:
        return None
    try:
        body = _get_json(f"https://api.coinbase.com/v2/prices/{pair}/spot")
        return float(body["data"]["amount"])
    except Exception:
        return None


def mint_for(symbol: str, symbol_to_mint: dict[str, str | None]) -> str | None:
    mint = symbol_to_mint.get(symbol)
    if symbol == "SOL" and not mint:
        return SOL_MINT
    return mint
