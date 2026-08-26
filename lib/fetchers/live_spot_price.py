"""Current spot price for weekly MIXED assets.

Shared by the V4 builder and the weekly source audit so they cannot disagree
on what counts as a usable current SOL/PUMP price.

Never reads dated sol.json / pump.json caches. Stale cache is not CURRENT.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import requests

from lib.price_sources import BINANCE_SYMBOLS, COINGECKO_IDS, SOL_MINT

# Weekly MIXED assets that must have a current price before live mutation.
MIXED_WEEKLY_ASSETS: dict[str, dict[str, Any]] = {
    "SOL": {
        "symbol": "SOL",
        "coin_id": "solana",
        "binance_pair": "SOLUSDT",
        "dex_mint": SOL_MINT,
        "dex_symbols": ("SOL", "WSOL"),
    },
    "PUMP": {
        "symbol": "PUMP",
        "coin_id": "pump-fun",
        "binance_pair": None,
        "dex_mint": "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
        "dex_symbols": ("PUMP",),
    },
}

# Registry + production price layer: CoinGecko simple/price is APPROVED_PRIMARY
# (same path as the portfolio audit). coins/{id} is a richer CG attempt.
# Binance + DexScreener are APPROVED_SECONDARY current venues — not stale cache.
SOURCE_ORDER = ("coingecko_simple", "coingecko_coins", "binance", "dexscreener")

_test_backends: dict[str, Callable[..., dict[str, Any]]] | None = None


def set_test_backends(backends: dict[str, Callable[..., dict[str, Any]]] | None) -> None:
    global _test_backends
    _test_backends = backends


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify_failure(exc: BaseException) -> str:
    if isinstance(exc, requests.Timeout):
        return "timeout"
    if isinstance(exc, requests.HTTPError):
        code = getattr(getattr(exc, "response", None), "status_code", None)
        if code == 429:
            return "rate_limit"
        if code:
            return f"http_{code}"
        return "http_error"
    text = str(exc).lower()
    if "symbol" in text or "identity" in text or "pair" in text:
        return "symbol_mismatch"
    if "malformed" in text or "missing" in text or "no pairs" in text:
        return "malformed_response"
    if "timeout" in text:
        return "timeout"
    return "other"


def _positive_price(raw: Any) -> float:
    price = float(raw)
    if price <= 0 or price != price:  # noqa: PLR0124 — NaN check
        raise ValueError("missing field: price is not a real positive number")
    return price


def _attempt(name: str, **fields: Any) -> dict[str, Any]:
    row = {"source": name, **fields}
    return row


def _fetch_coingecko_coins(spec: dict[str, Any]) -> dict[str, Any]:
    from lib.fetchers.price_common import fetch_price_coingecko

    coin_id = spec["coin_id"]
    block = fetch_price_coingecko(coin_id)
    if (block.get("source") or "") != "coingecko":
        raise RuntimeError("identity: CoinGecko coins payload source mismatch")
    price = _positive_price(block.get("price_usd"))
    block["price_usd"] = price
    block["freshness"] = "CURRENT"
    block["fetched_at"] = now_iso()
    return block


def _fetch_coingecko_simple(spec: dict[str, Any]) -> dict[str, Any]:
    from lib.coingecko_api import simple_price

    coin_id = spec["coin_id"]
    symbol = spec["symbol"]
    data = simple_price([coin_id])
    if coin_id not in data:
        raise RuntimeError(f"identity: CoinGecko simple/price missing id {coin_id}")
    row = data[coin_id] or {}
    price = _positive_price(row.get("usd"))
    return {
        "source": "coingecko",
        "url": f"https://www.coingecko.com/en/coins/{coin_id}",
        "price_usd": price,
        "ath_usd": None,
        "ath_change_pct": None,
        "change_7d_pct": row.get("usd_7d_change"),
        "freshness": "CURRENT",
        "fetched_at": now_iso(),
        "identity": {"coin_id": coin_id, "symbol": symbol},
    }


def _fetch_binance(spec: dict[str, Any]) -> dict[str, Any]:
    from lib.fetchers.http import get_json

    pair = spec.get("binance_pair")
    if not pair:
        raise RuntimeError("no Binance pair configured")
    body = get_json("https://api.binance.com/api/v3/ticker/price", {"symbol": pair})
    got = str(body.get("symbol") or "")
    if got != pair:
        raise RuntimeError(f"identity: expected pair {pair}, got {got or '(none)'}")
    price = _positive_price(body.get("price"))
    return {
        "source": "binance",
        "url": f"https://api.binance.com/api/v3/ticker/price?symbol={pair}",
        "price_usd": price,
        "ath_usd": None,
        "ath_change_pct": None,
        "change_7d_pct": None,
        "freshness": "CURRENT",
        "fetched_at": now_iso(),
        "identity": {"pair": pair, "symbol": spec["symbol"]},
    }


def _fetch_dexscreener(spec: dict[str, Any]) -> dict[str, Any]:
    from lib.dex_identity import select_dex_usd_price
    from lib.fetchers.http import get_json

    mint = spec.get("dex_mint")
    if not mint:
        raise RuntimeError("no DexScreener mint configured")
    data = get_json(f"https://api.dexscreener.com/latest/dex/tokens/{mint}")
    pairs = data.get("pairs") or []
    if not pairs:
        raise RuntimeError("malformed: DexScreener returned no pairs")
    selected = select_dex_usd_price(
        pairs,
        mint,
        symbol=spec.get("symbol"),
        chain="solana",
    )
    if not selected:
        raise RuntimeError(
            f"identity: no DexScreener USD pair for {spec['symbol']} mint {mint}"
        )
    price = _positive_price(selected["price_usd"])
    return {
        "source": "dexscreener",
        "url": selected.get("url") or "https://api.dexscreener.com",
        "price_usd": price,
        "liquidity_usd": selected.get("liquidity_usd"),
        "ath_usd": None,
        "ath_change_pct": None,
        "change_7d_pct": None,
        "freshness": "CURRENT",
        "fetched_at": now_iso(),
        "identity": {
            "mint": mint,
            "orientation": selected.get("orientation"),
            "base_symbol": selected.get("base_symbol"),
            "quote_symbol": selected.get("quote_symbol"),
            "pair_address": selected.get("pair_address"),
        },
    }


def _backends() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    if _test_backends is not None:
        return _test_backends
    return {
        "coingecko_coins": _fetch_coingecko_coins,
        "coingecko_simple": _fetch_coingecko_simple,
        "binance": _fetch_binance,
        "dexscreener": _fetch_dexscreener,
    }


def spec_for(symbol: str, **overrides: Any) -> dict[str, Any]:
    base = dict(MIXED_WEEKLY_ASSETS.get(symbol.upper()) or {})
    if not base:
        base = {
            "symbol": symbol.upper(),
            "coin_id": COINGECKO_IDS.get(symbol.upper()),
            "binance_pair": BINANCE_SYMBOLS.get(symbol.upper()),
            "dex_mint": overrides.get("dex_mint"),
            "dex_symbols": (symbol.upper(),),
        }
    base.update({k: v for k, v in overrides.items() if v is not None})
    return base


def _mixed_row(*, coin_id: str | None = None, symbol: str | None = None) -> dict[str, Any] | None:
    if symbol and str(symbol).upper() in MIXED_WEEKLY_ASSETS:
        return MIXED_WEEKLY_ASSETS[str(symbol).upper()]
    if coin_id:
        for row in MIXED_WEEKLY_ASSETS.values():
            if row["coin_id"] == coin_id:
                return row
    return None


def resolve_spot_spec(
    *,
    coin_id: str | None = None,
    symbol: str | None = None,
    dex_mint: str | None = None,
    binance_pair: str | None = None,
) -> dict[str, Any]:
    """Canonical identity. coin_id=solana never becomes symbol=SOLANA."""
    mixed = _mixed_row(coin_id=coin_id, symbol=symbol)
    if mixed:
        return spec_for(
            mixed["symbol"],
            coin_id=coin_id or mixed["coin_id"],
            dex_mint=dex_mint,
            binance_pair=binance_pair,
        )
    resolved = (symbol or coin_id or "").upper()
    if not resolved:
        raise RuntimeError("cannot resolve spot spec without symbol or coin_id")
    return spec_for(
        resolved,
        coin_id=coin_id,
        dex_mint=dex_mint,
        binance_pair=binance_pair,
    )


def identity_contract(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": spec.get("symbol"),
        "coin_id": spec.get("coin_id"),
        "binance_pair": spec.get("binance_pair"),
        "dex_mint": spec.get("dex_mint"),
    }


def fetch_current_spot(symbol: str, **overrides: Any) -> dict[str, Any]:
    """Return a current price block or a failed probe. Never uses dated JSON caches."""
    spec = resolve_spot_spec(
        symbol=symbol,
        coin_id=overrides.get("coin_id"),
        dex_mint=overrides.get("dex_mint"),
        binance_pair=overrides.get("binance_pair"),
    )
    backends = _backends()
    attempts: list[dict[str, Any]] = []
    for name in SOURCE_ORDER:
        fn = backends.get(name)
        if fn is None:
            continue
        if name == "binance" and not spec.get("binance_pair"):
            attempts.append(_attempt(name, ok=False, failure_type="other", error="no pair configured"))
            continue
        if name == "dexscreener" and not spec.get("dex_mint"):
            attempts.append(_attempt(name, ok=False, failure_type="other", error="no mint configured"))
            continue
        try:
            block = fn(spec)
            price = _positive_price(block.get("price_usd"))
            block["price_usd"] = price
            block.setdefault("freshness", "CURRENT")
            block.setdefault("fetched_at", now_iso())
            if block.get("freshness") == "STALE":
                attempts.append(
                    _attempt(name, ok=False, failure_type="stale_cache", error="stale value cannot be CURRENT")
                )
                continue
            attempts.append(_attempt(name, ok=True, failure_type=None, price_usd=price))
            return {
                "ok": True,
                "symbol": spec["symbol"],
                "identity": identity_contract(spec),
                "price_block": block,
                "attempts": attempts,
                "freshness": "CURRENT",
                "source": block["source"],
            }
        except Exception as exc:  # noqa: BLE001 — record every attempted source
            attempts.append(
                _attempt(name, ok=False, failure_type=classify_failure(exc), error=str(exc))
            )
    return {
        "ok": False,
        "symbol": spec["symbol"],
        "identity": identity_contract(spec),
        "price_block": None,
        "attempts": attempts,
        "freshness": "MISSING",
        "source": None,
        "error": f"No current price source available for {spec['symbol']} this run",
    }


def probe_mixed_weekly_prices() -> dict[str, Any]:
    """SOL + PUMP current-price availability. Same contract as the builder."""
    assets: dict[str, Any] = {}
    errors: list[str] = []
    for symbol in MIXED_WEEKLY_ASSETS:
        row = fetch_current_spot(symbol)
        assets[symbol] = {
            "ok": row["ok"],
            "source": row.get("source"),
            "freshness": row.get("freshness"),
            "price_usd": (row.get("price_block") or {}).get("price_usd"),
            "attempts": row.get("attempts"),
            "error": row.get("error"),
            "identity": row.get("identity") or identity_contract(spec_for(symbol)),
        }
        if not row["ok"] or row.get("freshness") != "CURRENT":
            errors.append(row.get("error") or f"{symbol} has no current price")
    return {
        "ok": not errors,
        "errors": errors,
        "assets": assets,
        "note": "CURRENT alternative venue is a valid live fallback. Dated JSON cache is not.",
    }
