"""Coinbase stub — BTC holdings INCOMPLETE until read-only API key."""

from __future__ import annotations


def fetch_btc_balance() -> dict:
    return {
        "balance_btc": None,
        "status": "INCOMPLETE",
        "note": "Coinbase read-only API key not configured.",
    }
