"""Solana RPC wallet balances for assets in config/assets.json."""

from __future__ import annotations

import json
import time
from typing import Any

import requests
import certifi

from lib.paths import CONFIG

SOLANA_RPC = "https://api.mainnet-beta.solana.com"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
RPC_TIMEOUT_S = 12
RPC_ATTEMPTS = 2
FETCH_DEADLINE_S = 60


def _rpc_urls() -> list[str]:
    urls = [SOLANA_RPC]
    try:
        from lib.helius_client import rpc_url

        urls.insert(0, rpc_url())
    except Exception:
        pass
    return urls


def _rpc(method: str, params: list[Any], *, deadline: float | None = None) -> Any:
    last = None
    for url in _rpc_urls():
        for attempt in range(RPC_ATTEMPTS):
            if deadline is not None and time.monotonic() >= deadline:
                raise RuntimeError(f"Solana RPC {method}: deadline {FETCH_DEADLINE_S}s")
            timeout = RPC_TIMEOUT_S
            if deadline is not None:
                timeout = max(1.0, min(RPC_TIMEOUT_S, deadline - time.monotonic()))
            try:
                r = requests.post(
                    url,
                    json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                    timeout=timeout,
                    verify=certifi.where(),
                )
                if r.status_code == 429:
                    time.sleep(min(1.5 * (2 ** attempt), 3.0))
                    last = RuntimeError(f"429 {method}")
                    continue
                r.raise_for_status()
                body = r.json()
                if "error" in body:
                    last = RuntimeError(f"Solana RPC {method}: {body['error']}")
                    break
                return body["result"]
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(0.2 * (attempt + 1))
    raise RuntimeError(last or f"Solana RPC {method} failed")


def load_assets_config() -> dict:
    return json.loads((CONFIG / "assets.json").read_text())


def _parse_token_accounts(
    result: dict,
    mint_to_symbol: dict[str, str],
    balances: dict[str, float],
) -> None:
    for item in result.get("value", []):
        info = item["account"]["data"]["parsed"]["info"]
        mint = info["mint"]
        symbol = mint_to_symbol.get(mint)
        if not symbol:
            continue
        amount = float(info["tokenAmount"]["uiAmount"] or 0)
        balances[symbol] = balances.get(symbol, 0.0) + amount


def fetch_balances(wallet_address: str | None = None) -> dict[str, float]:
    cfg = load_assets_config()
    address = wallet_address or cfg["wallet"]
    mint_to_symbol = {
        a["mint"]: a["symbol"]
        for a in cfg["assets"]
        if a.get("mint")
    }
    balances: dict[str, float] = {a["symbol"]: 0.0 for a in cfg["assets"]}
    deadline = time.monotonic() + FETCH_DEADLINE_S

    lamports = _rpc("getBalance", [address], deadline=deadline)["value"]
    balances["SOL"] = lamports / 1_000_000_000

    for program_id in (TOKEN_PROGRAM, TOKEN_2022_PROGRAM):
        result = _rpc(
            "getTokenAccountsByOwner",
            [address, {"programId": program_id}, {"encoding": "jsonParsed"}],
            deadline=deadline,
        )
        _parse_token_accounts(result, mint_to_symbol, balances)

    return balances
