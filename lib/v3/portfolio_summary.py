"""Live portfolio totals from Solana wallet + prices."""

from __future__ import annotations

from datetime import datetime, timezone

from lib.prices import fetch_prices
from lib.wallet import fetch_balances, load_assets_config


def portfolio_snapshot(force_prices: bool = False) -> dict:
    cfg = load_assets_config()
    wallet = cfg["wallet"]
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        balances = fetch_balances(wallet)
        wallet_ok = True
        wallet_error = None
    except Exception as e:
        balances = {a["symbol"]: 0.0 for a in cfg["assets"]}
        wallet_ok = False
        wallet_error = str(e)

    prices, sources = fetch_prices(force=force_prices)

    total_usd = 0.0
    total_gbp = 0.0
    positions: dict[str, dict] = {}

    for asset in cfg["assets"]:
        sym = asset["symbol"]
        bal = balances.get(sym, 0.0) if sym != "BTC" else 0.0
        px = prices.get(sym, {})
        usd_px = float(px.get("usd") or 0)
        gbp_px = float(px.get("gbp") or usd_px * 0.79)
        usd = bal * usd_px
        gbp = bal * gbp_px
        if sym != "BTC":
            total_usd += usd
            total_gbp += gbp
        positions[sym] = {
            "balance": bal,
            "usd_price": usd_px,
            "gbp_price": gbp_px,
            "usd_value": round(usd, 2),
            "gbp_value": round(gbp, 2),
        }

    short = f"{wallet[:6]}…{wallet[-4:]}" if len(wallet) > 10 else wallet
    if wallet_ok:
        holdings_note = f"£{total_gbp:,.0f} live wallet · {short}"
    else:
        holdings_note = f"Wallet fetch failed · {short}"

    return {
        "wallet": wallet,
        "wallet_short": short,
        "total_usd": round(total_usd, 2),
        "total_gbp": round(total_gbp, 2),
        "holdings_note": holdings_note,
        "wallet_connected": wallet_ok,
        "wallet_error": wallet_error,
        "balances": balances,
        "positions": positions,
        "fetched_at": fetched_at,
        "price_sources": sources,
        "prices_fallback_used": bool(sources.get("prices_fallback_used")),
        "price_check_status": sources.get("price_check_status"),
    }
