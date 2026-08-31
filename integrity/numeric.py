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


def compact_usd_parts(value: Any) -> tuple[str, str, bool]:
    """Hard display lock: 3 digits max. Never 4-digit millions. Never 0.xx billion. No minus."""
    mag = abs(dec(value))
    negative = dec(value) < 0
    if mag == 0:
        return "$0", "M", False
    if mag >= Decimal("1000000000"):
        unit, sfx = Decimal("1000000000"), "B"
    else:
        unit, sfx = Decimal("1000000"), "M"
    shown = mag / unit
    if sfx == "M" and shown >= 1000:
        unit, sfx = Decimal("1000000000"), "B"
        shown = mag / unit
    if sfx == "B" and shown < 1:
        unit, sfx = Decimal("1000000"), "M"
        shown = mag / unit
    if shown >= 100:
        places = 0
    elif shown >= 10:
        places = 1
    else:
        places = 2
    shown = shown.quantize(Decimal("1").scaleb(-places), rounding=ROUND_HALF_UP)
    if sfx == "M" and shown >= 1000:
        unit, sfx = Decimal("1000000000"), "B"
        shown = (mag / unit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        places = 2
    if sfx == "B" and shown < 1:
        unit, sfx = Decimal("1000000"), "M"
        shown = mag / unit
        places = 0 if shown >= 100 else (1 if shown >= 10 else 2)
        shown = shown.quantize(Decimal("1").scaleb(-places), rounding=ROUND_HALF_UP)
    if places == 0:
        num = str(int(shown))
    else:
        num = format(shown, f".{places}f")
    int_digits = num.split(".", 1)[0]
    if len(int_digits) > 3:
        raise RuntimeError(f"ETF_DISPLAY_FOUR_DIGITS:{num}{sfx}")
    if sfx == "B" and Decimal(num) < 1:
        raise RuntimeError(f"ETF_DISPLAY_FRACTION_BILLION:{num}{sfx}")
    return f"${num}", sfx, negative


def compact_usd_formatter(value: Any) -> dict[str, Any]:
    text, sfx, _neg = compact_usd_parts(value)
    num = text[1:]
    dp = len(num.split(".", 1)[1]) if "." in num else 0
    return {
        "type": "numeric",
        "currency_prefix": "$",
        "scale": int(_SCALE[sfx]),
        "decimal_places": dp,
        "external_scale_suffix": sfx,
    }


def is_etf_flow_metric(metric_id: str) -> bool:
    return ".etf.flow.usd." in metric_id


def dec(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    if v is None:
        return Decimal("0")
    return Decimal(str(v))


def inferred_numeric_formatter(span: str) -> dict[str, Any]:
    """Build a numeric formatter from a display span's own decimals and scale."""
    raw = (span or "").strip().replace("−", "-")
    m = re.search(
        r"[~+\-]*\$?[\d,]+(?:\.(\d+))?(?:[eE][+\-]?\d+)?([kKmMbBtT])?",
        raw,
    )
    dp = len(m.group(1) or "") if m else 0
    sfx = m.group(2) if m else None
    scale = _SCALE.get(sfx or "", Decimal("1"))
    return {"type": "numeric", "decimal_places": dp, "scale": scale}


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


def parse_binding_observed(
    text: str,
    formatter: dict[str, Any] | None,
    *,
    canonical: Decimal | None = None,
) -> Decimal | None:
    """Parse a located binding span using formatter metadata (validation only)."""
    val = parse_display_token(text)
    if val is None or not formatter or formatter.get("type") != "numeric":
        return val
    scale = dec(formatter.get("scale", 1))
    ext = formatter.get("external_scale_suffix")
    token = text.strip()
    inline_scale = bool(re.search(r"[kKmMbBtT]$", token.rstrip("%×x")))
    if not ext or inline_scale or scale <= 1:
        return val
    scaled = val * scale
    if canonical is None:
        return scaled if val < scale else val
    if abs(scaled - canonical) <= abs(val - canonical):
        return scaled
    return val


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
