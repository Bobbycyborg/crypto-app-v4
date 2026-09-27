"""Tracked wallet state. Proved 1 Aug starts are kept. The page is written from this file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "state" / "siren-state.json"


def load_state(path: Path | None = None) -> dict[str, Any]:
    target = path or STATE_PATH
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def merge_state(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Update coins and wallets that were walked. Leave every other coin in place."""
    if not isinstance(incoming, dict):
        raise RuntimeError("refuse to save empty siren state")
    out = dict(existing or {})
    coins = {name: dict(block) for name, block in (out.get("coins") or {}).items()}
    for coin, block in (incoming.get("coins") or {}).items():
        prev = dict(coins.get(coin) or {})
        by_wallet = {row.get("wallet"): row for row in (prev.get("wallets") or []) if row.get("wallet")}
        for row in block.get("wallets") or []:
            if row.get("wallet"):
                by_wallet[row["wallet"]] = row
        merged = dict(prev)
        merged.update({key: value for key, value in block.items() if key != "wallets"})
        merged["wallets"] = list(by_wallet.values())
        coins[coin] = merged
    for key, value in incoming.items():
        if key != "coins":
            out[key] = value
    out["coins"] = coins
    if not coins:
        raise RuntimeError("refuse to save empty siren state")
    return out


def save_state(bundle: dict[str, Any], path: Path | None = None) -> None:
    target = path or STATE_PATH
    existing = load_state(target)
    merged = merge_state(existing, bundle)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    tmp.replace(target)


def prior_row(state: dict[str, Any], coin: str, wallet: str) -> dict[str, Any] | None:
    rows = ((state.get("coins") or {}).get(coin) or {}).get("wallets") or []
    for row in rows:
        if row.get("wallet") == wallet:
            return row
    return None


def protect_row(prior: dict[str, Any] | None, fresh: dict[str, Any]) -> dict[str, Any]:
    """A proved 1 Aug start is never replaced. No transfer plus a changed balance is inconsistent."""
    if prior and prior.get("aug1_status") == "proved" and prior.get("aug1") is not None:
        fresh["aug1"] = prior.get("aug1")
        fresh["aug1_as_of"] = prior.get("aug1_as_of")
        fresh["aug1_status"] = "proved"
        balance = fresh.get("balance")
        sent = float(fresh.get("sent") or 0)
        received = float(fresh.get("received") or 0)
        if balance is not None and abs(float(balance) - float(prior["aug1"])) > 1e-6 and sent == 0 and received == 0:
            fresh["aug1_status"] = "inconsistent"
            fresh["aug1"] = prior.get("aug1")
        return fresh
    if fresh.get("aug1_status") == "unmoved_equals_now":
        fresh["aug1"] = None
        fresh["aug1_status"] = "inconsistent"
    return fresh


def unread_row(prior: dict[str, Any] | None, wallet: str, error: str) -> dict[str, Any]:
    """Keep last week's values when this week's read fails."""
    row = dict(prior or {})
    row["wallet"] = wallet
    row["error"] = error
    row["status"] = "unread this week"
    row["line"] = "unread this week"
    return row
