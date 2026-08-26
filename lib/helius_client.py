"""Load Helius API key from local env. Forensics only — not V3 cards."""

from __future__ import annotations

import re
from pathlib import Path

import certifi
import requests

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "config" / "helius.local.env"


def load_api_key() -> str:
    if not ENV_PATH.exists():
        raise FileNotFoundError(f"Missing {ENV_PATH}")
    text = ENV_PATH.read_text()
    m = re.search(r"^HELIUS_API_KEY=(.+)$", text, re.M)
    if not m or not m.group(1).strip():
        raise ValueError("HELIUS_API_KEY empty in helius.local.env")
    return m.group(1).strip().strip('"').strip("'")


def rpc_url() -> str:
    return f"https://mainnet.helius-rpc.com/?api-key={load_api_key()}"


def rpc(method: str, params: list) -> dict:
    r = requests.post(
        rpc_url(),
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=45,
        verify=certifi.where(),
    )
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]


def enhanced_transactions(
    address: str,
    *,
    limit: int = 100,
    gte_time: int | None = None,
    lte_time: int | None = None,
) -> list:
    params = {"api-key": load_api_key(), "limit": limit}
    if gte_time is not None:
        params["gte-time"] = gte_time
    if lte_time is not None:
        params["lte-time"] = lte_time
    r = requests.get(
        f"https://api.helius.xyz/v0/addresses/{address}/transactions",
        params=params,
        timeout=60,
        verify=certifi.where(),
    )
    r.raise_for_status()
    return r.json()
