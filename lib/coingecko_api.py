"""CoinGecko HTTP client — shared demo key, retries, same .env as MCP."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import certifi
import requests

from lib.paths import ROOT

_WORKSPACE = ROOT.parent.parent
_ENV_CANDIDATES = [
    Path(os.environ.get("COINGECKO_ENV_FILE", "")),
    _WORKSPACE / ".cursor" / "mcps" / "coingecko" / ".env",
    ROOT / "config" / "coingecko.local.env",
]

_BASE = "https://api.coingecko.com/api/v3"
_LOADED = False


def _parse_env_file(path: Path) -> None:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and val and key not in os.environ:
            os.environ[key] = val


def _ensure_env_loaded() -> None:
    global _LOADED
    if _LOADED:
        return
    for path in _ENV_CANDIDATES:
        if path and path.is_file():
            _parse_env_file(path)
    _LOADED = True


def demo_api_key() -> str | None:
    _ensure_env_loaded()
    key = os.environ.get("COINGECKO_DEMO_API_KEY")
    if not key or key == "your_demo_api_key_here":
        return None
    return key


def pro_api_key() -> str | None:
    _ensure_env_loaded()
    return os.environ.get("COINGECKO_PRO_API_KEY") or None


def auth_status() -> dict[str, Any]:
    _ensure_env_loaded()
    if pro_api_key():
        return {"mode": "pro", "key_present": True, "account_required": False}
    if demo_api_key():
        return {"mode": "demo", "key_present": True, "account_required": True}
    return {"mode": "public", "key_present": False, "account_required": False}


def _headers() -> dict[str, str]:
    _ensure_env_loaded()
    if pro_api_key():
        return {"x-cg-pro-api-key": pro_api_key() or ""}
    if demo_api_key():
        return {"x-cg-demo-api-key": demo_api_key() or ""}
    return {}


def get_json(url: str, params: dict | None = None, retries: int = 6) -> Any:
    """GET with demo/pro key. 429 uses Retry-After or exponential backoff."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            r = requests.get(
                url,
                params=params,
                headers=_headers(),
                timeout=45,
                verify=certifi.where(),
            )
            if r.status_code == 429:
                if attempt >= retries - 1:
                    r.raise_for_status()
                wait = None
                ra = r.headers.get("Retry-After")
                if ra:
                    try:
                        wait = float(ra)
                    except ValueError:
                        wait = None
                if wait is None:
                    wait = min(60.0, 4.0 * (2 ** attempt))
                time.sleep(max(wait, 1.0))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last_err = exc
            if attempt < retries - 1:
                time.sleep(min(30.0, 2.0 * (attempt + 1)))
    if last_err:
        raise last_err
    raise RuntimeError("coingecko get_json failed")


def simple_price(ids: list[str]) -> dict[str, Any]:
    if not ids:
        return {}
    auth = auth_status()
    chunk = 4 if auth["mode"] == "public" else len(ids)
    out: dict[str, Any] = {}
    for i in range(0, len(ids), chunk):
        batch = ids[i : i + chunk]
        url = f"{_BASE}/simple/price"
        params = {
            "ids": ",".join(batch),
            "vs_currencies": "usd,gbp",
            "include_24hr_change": "true",
            "include_7d_change": "true",
            "include_30d_change": "true",
        }
        try:
            out.update(get_json(url, params=params))
        except Exception:
            pass
        if auth["mode"] == "public" and i + chunk < len(ids):
            time.sleep(0.6)
    return out


def coins_markets(ids: list[str]) -> list[dict[str, Any]]:
    """One CoinGecko markets call — price, ATH, circ, 7d/30d. Same source as coins/{id} ATH."""
    if not ids:
        return []
    uniq: list[str] = []
    seen: set[str] = set()
    for i in ids:
        if i and i not in seen:
            uniq.append(i)
            seen.add(i)
    data = get_json(
        f"{_BASE}/coins/markets",
        {
            "vs_currency": "usd",
            "ids": ",".join(uniq),
            "price_change_percentage": "7d,30d",
            "per_page": max(len(uniq), 1),
            "page": 1,
        },
        retries=6,
    )
    if not isinstance(data, list):
        raise RuntimeError("CoinGecko coins/markets malformed")
    return data


def global_stats() -> dict[str, Any] | None:
    try:
        return get_json(f"{_BASE}/global")
    except Exception:
        return None
