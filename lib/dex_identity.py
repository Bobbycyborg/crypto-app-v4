"""Identity-safe DexScreener pair selection for a token USD price.

DexScreener /latest/dex/tokens/{mint} returns many pools. priceUsd is only a
USD price when the counter-asset is a USD stable or (for non-SOL tokens) wrapped
SOL. Highest-liquidity alt/alt pools (PUMP/MET, RAY/JUP) must not win.
"""

from __future__ import annotations

from typing import Any

from lib.price_sources import SOL_MINT

# Solana USD-settled quotes. Addresses from config/assets.json + live Dex dumps.
USD_STABLE_MINTS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
    "USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB": "USD1",
}

EXPECTED_CHAIN = "solana"


def _addr(token: dict[str, Any] | None) -> str:
    return str((token or {}).get("address") or "")


def _sym(token: dict[str, Any] | None) -> str:
    return str((token or {}).get("symbol") or "")


def _liq(pair: dict[str, Any]) -> float:
    try:
        return float((pair.get("liquidity") or {}).get("usd") or 0)
    except (TypeError, ValueError):
        return 0.0


def _positive(raw: Any) -> float | None:
    try:
        price = float(raw)
    except (TypeError, ValueError):
        return None
    if price <= 0 or price != price:  # noqa: PLR0124 — NaN
        return None
    return price


def _counter_ok(requested_mint: str, counter_mint: str) -> bool:
    if not counter_mint or counter_mint == requested_mint:
        return False
    if counter_mint in USD_STABLE_MINTS:
        return True
    return counter_mint == SOL_MINT and requested_mint != SOL_MINT


def _chain_ok(pair: dict[str, Any], chain: str) -> bool:
    got = str(pair.get("chainId") or "").lower()
    want = (chain or EXPECTED_CHAIN).lower()
    return bool(got) and got == want


def candidate_usd_price(
    pair: dict[str, Any],
    mint: str,
    *,
    symbol: str | None = None,
    chain: str = EXPECTED_CHAIN,
) -> dict[str, Any] | None:
    """Return a validated USD price for `mint` from one Dex pair, or None."""
    if not mint or not _chain_ok(pair, chain):
        return None
    base = pair.get("baseToken") or {}
    quote = pair.get("quoteToken") or {}
    base_addr, quote_addr = _addr(base), _addr(quote)
    is_base = base_addr == mint
    is_quote = quote_addr == mint
    if is_base == is_quote:
        return None
    if is_base:
        if not _counter_ok(mint, quote_addr):
            return None
        price = _positive(pair.get("priceUsd"))
        orientation = "base"
    else:
        if not _counter_ok(mint, base_addr):
            return None
        base_usd = _positive(pair.get("priceUsd"))
        native = _positive(pair.get("priceNative"))
        if base_usd is None or native is None:
            return None
        price = _positive(base_usd / native)
        orientation = "quote"
    if price is None:
        return None
    return {
        "ok": True,
        "price_usd": price,
        "orientation": orientation,
        "chainId": pair.get("chainId"),
        "dexId": pair.get("dexId"),
        "pair_address": pair.get("pairAddress"),
        "url": pair.get("url"),
        "liquidity_usd": _liq(pair),
        "base_symbol": _sym(base),
        "base_address": base_addr,
        "quote_symbol": _sym(quote),
        "quote_address": quote_addr,
        "priceUsd_raw": pair.get("priceUsd"),
    }


def select_dex_usd_price(
    pairs: list[dict[str, Any]] | None,
    mint: str,
    *,
    symbol: str | None = None,
    chain: str = EXPECTED_CHAIN,
) -> dict[str, Any] | None:
    """Identity-filter first, then highest USD liquidity among valid candidates."""
    valid: list[dict[str, Any]] = []
    for pair in pairs or []:
        row = candidate_usd_price(pair, mint, symbol=symbol, chain=chain)
        if row:
            valid.append(row)
    if not valid:
        return None
    return max(valid, key=lambda r: r["liquidity_usd"])
