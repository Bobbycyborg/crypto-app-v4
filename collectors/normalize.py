"""Deterministic numeric normalization. No display rounding."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from collectors.extract import ExtractError, _as_decimal


def normalize(value: Any, spec: dict[str, Any] | None) -> Decimal | int:
    if spec is None:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "missing normalizer")
    ntype = spec.get("type")
    raw = _as_decimal(value)
    if ntype == "identity":
        out: Decimal | int = raw
    elif ntype == "decimal_as_percent":
        out = raw * Decimal("100")
    elif ntype == "percent_as_decimal":
        out = raw / Decimal("100")
    elif ntype == "millions_to_usd":
        out = raw * Decimal("1000000")
    elif ntype == "lamports_to_sol":
        out = raw / Decimal("1000000000")
    elif ntype == "integer":
        if raw != raw.to_integral_value():
            raise ExtractError("VALUE_INVALID", f"not an integer: {raw}")
        return int(raw)
    else:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"unknown normalizer {ntype}")
    as_int = spec.get("as_integer")
    if as_int:
        if out != out.to_integral_value():
            raise ExtractError("VALUE_INVALID", f"not an integer: {out}")
        return int(out)
    return out if isinstance(out, Decimal) else Decimal(out)
