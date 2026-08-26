"""HTTP helpers — fresh fetch each weekly run."""

from __future__ import annotations

import re
import time
from typing import Any

import certifi
import requests

from lib.coingecko_api import get_json as coingecko_get_json

_UA = "crypto-app-v2-weekly-report/1.0"


def get_json(url: str, params: dict | None = None) -> Any:
    if "coingecko.com" in url:
        return coingecko_get_json(url, params=params)
    r = requests.get(url, params=params, timeout=30, verify=certifi.where())
    r.raise_for_status()
    return r.json()


def get_text(url: str, *, timeout: int = 30, retries: int = 3) -> str:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = requests.get(
                url,
                timeout=timeout,
                verify=certifi.where(),
                headers={"User-Agent": _UA},
            )
            r.raise_for_status()
            return r.text
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt + 1 < retries:
                time.sleep(0.4 * (2**attempt))
    raise last or RuntimeError(f"GET failed: {url}")


def parse_int_from_html(text: str, label: str) -> int | None:
    """Find number near a label in rendered or SSR HTML."""
    patterns = [
        rf"{re.escape(label)}[^\d]{{0,80}}([\d,]+)",
        rf"{re.escape(label)}[\s\S]{{0,120}}?([\d][\d,]*)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return int(m.group(1).replace(",", ""))
    return None
