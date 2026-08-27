"""Occurrence-specific display formatting — stdlib Decimal only."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any


def _dec(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    if v is None:
        return Decimal("0")
    return Decimal(str(v))


def infer_formatter(literal: str) -> dict[str, Any]:
    raw = literal.strip()
    fmt: dict[str, Any] = {"type": "numeric"}
    if raw.upper() == "UNKNOWN":
        fmt["type"] = "string_exact"
        return fmt
    m = re.match(r"^(~)?(\+)?(\$)?([0-9,]+(?:\.[0-9]+)?)([kKmMbBtT])?(%?)(/wk|/day|/d)?$", raw)
    if m:
        approx, plus, cur, num, scale_sfx, pct, suffix = m.groups()
        if approx:
            fmt["approx_prefix"] = "~"
        if plus:
            fmt["explicit_plus_positive"] = True
        if cur:
            fmt["currency_prefix"] = "$"
        if "," in num:
            fmt["grouping"] = True
        if scale_sfx:
            fmt["scale_suffix"] = scale_sfx
            fmt["scale"] = {"k": 1000, "K": 1000, "m": 1_000_000, "M": 1_000_000, "b": 1_000_000_000, "B": 1_000_000_000, "t": 1_000_000_000_000, "T": 1_000_000_000_000}[scale_sfx]
        else:
            fmt["scale"] = 1
        if pct:
            fmt["percent"] = True
        if suffix:
            fmt["suffix"] = suffix
        if "." in num:
            fmt["decimal_places"] = len(num.split(".", 1)[1])
        else:
            fmt["decimal_places"] = 0
        if raw.endswith("x"):
            fmt["ratio_x"] = True
        return fmt
    if raw.endswith("x") and re.match(r"^\+?[0-9]+(?:\.[0-9]+)?x$", raw):
        fmt["ratio_x"] = True
        fmt["decimal_places"] = len(raw.split(".")[1][:-1]) if "." in raw else 0
        return fmt
    if "%" in raw and fmt.get("type") == "numeric":
        fmt["percent"] = True
        return fmt
    fmt["type"] = "string_exact"
    return fmt


def format_value(value: Any, formatter: dict[str, Any], *, status: str = "OK") -> str:
    if status != "OK":
        return "UNKNOWN"
    if formatter.get("type") == "string_exact":
        return str(value) if value is not None else "UNKNOWN"
    d = _dec(value)
    if d == 0 or d == Decimal("0"):
        d = Decimal("0")
    scale = Decimal(str(formatter.get("scale", 1)))
    shown = d / scale if scale != 1 else d
    places = int(formatter.get("decimal_places", 2))
    q = Decimal("1").scaleb(-places)
    shown = shown.quantize(q, rounding=ROUND_HALF_UP)
    if shown == shown.to_integral_value():
        shown = shown.to_integral_value()
    s = f"{shown:,}" if formatter.get("grouping") else str(shown)
    out = ""
    if formatter.get("approx_prefix"):
        out += formatter["approx_prefix"]
    if formatter.get("comparison_prefix"):
        out += formatter["comparison_prefix"]
    if formatter.get("currency_prefix"):
        out += formatter["currency_prefix"]
    if formatter.get("explicit_plus_positive") and d > 0:
        out += "+"
    out += s
    if formatter.get("scale_suffix"):
        out += str(formatter["scale_suffix"])
    if formatter.get("percent"):
        out += "%"
    if formatter.get("ratio_x"):
        out += "x"
    if formatter.get("suffix"):
        out += formatter["suffix"]
    return out
