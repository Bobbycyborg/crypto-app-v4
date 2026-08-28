"""Decimal numeric parsing and precision-derived tolerance — stdlib only."""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

_SCALE = {
    "k": Decimal("1000"),
    "K": Decimal("1000"),
    "m": Decimal("1000000"),
    "M": Decimal("1000000"),
    "b": Decimal("1000000000"),
    "B": Decimal("1000000000"),
    "t": Decimal("1000000000000"),
    "T": Decimal("1000000000000"),
}


def dec(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    if v is None:
        return Decimal("0")
    return Decimal(str(v))


def display_tolerance(formatter: dict[str, Any] | None) -> Decimal:
    """Half of the smallest displayed unit from formatter metadata."""
    if not formatter or formatter.get("type") != "numeric":
        return Decimal("0")
    scale = dec(formatter.get("scale", 1))
    if scale <= 0:
        scale = Decimal("1")
    dp = int(formatter.get("decimal_places", 0))
    unit = scale * (Decimal("10") ** -dp)
    return unit / Decimal("2")


def parse_display_token(text: str) -> Decimal | None:
    """Parse a rendered numeric token to canonical Decimal base units."""
    raw = text.strip()
    if not raw or raw.upper() == "UNKNOWN":
        return None
    raw = raw.replace("−", "-")
    raw = re.sub(r"\b\d+d\b", " ", raw, flags=re.I)
    raw = re.sub(r"^(above|below|af|oi)\s+", "", raw, flags=re.I)
    pct = re.search(r"[~\+\-−]?\$?[\d,]+(?:\.\d+)?%", raw)
    m = pct or re.search(
        r"[~+\-−]*\$?[\d,]+(?:\.\d+)?(?:[eE][+\-−]?\d+)?(?:[kKmMbBtT]|%|pp|×|x)?",
        raw,
    )
    if not m:
        return None
    raw = m.group(0)
    raw = raw.replace("~", "").replace(",", "")
    m = re.match(r"^\d+d\s+", raw, re.I)
    if m:
        raw = raw[m.end() :]
    raw = re.sub(r"^(above|below)\s+", "", raw, flags=re.I)
    raw = raw.rstrip(".")
    if raw.startswith("+"):
        raw = raw[1:]
    raw = re.sub(r"\s*/\s*", "/", raw)
    for sfx in ("/wk", "/day", "/d", "/yr", "/8h", " burned", " retraced", " (mild)"):
        if sfx in raw:
            raw = raw.split(sfx)[0].strip()
    raw = raw.rstrip("×x").rstrip()
    if raw.endswith("pp"):
        raw = raw[:-2]
    if raw.endswith("%"):
        raw = raw[:-1]
    cur = False
    if raw.startswith("$"):
        cur = True
        raw = raw[1:]
    scale = Decimal("1")
    if raw and raw[-1] in _SCALE:
        scale = _SCALE[raw[-1]]
        raw = raw[:-1]
    sci = re.match(r"^([+-])?(\d+(?:\.\d+)?)[eE]([+\-−])(\d+)$", raw)
    if sci:
        sign, mantissa, exp_sign, exp_digits = sci.groups()
        exp = int(exp_digits)
        if exp_sign in ("-", "−"):
            exp = -exp
        val = Decimal(mantissa) * (Decimal("10") ** exp)
        if sign == "-":
            val = -val
        return val
    try:
        val = Decimal(raw)
    except Exception:
        return None
    return val * scale


def values_compatible(
    observed: Decimal | None,
    expected: Decimal,
    formatter: dict[str, Any] | None,
) -> bool:
    if observed is None:
        return False
    tol = display_tolerance(formatter)
    if tol == 0:
        return observed == expected
    return abs(observed - expected) <= tol


def derive_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return numerator / denominator


def derive_subtract(a: Decimal, b: Decimal) -> Decimal:
    return a - b


def drawdown_pct(current: Decimal, ath: Decimal) -> Decimal | None:
    if ath == 0:
        return None
    return (current / ath - Decimal("1")) * Decimal("100")


def round_display(value: Decimal, decimal_places: int) -> Decimal:
    q = Decimal("1").scaleb(-decimal_places)
    return value.quantize(q, rounding=ROUND_HALF_UP)
