"""Occurrence-specific display formatting — stdlib Decimal only."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

_SCALE = {
    "k": 1000,
    "K": 1000,
    "m": 1_000_000,
    "M": 1_000_000,
    "b": 1_000_000_000,
    "B": 1_000_000_000,
    "t": 1_000_000_000_000,
    "T": 1_000_000_000_000,
}


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

    unicode_minus = "−" in raw
    if unicode_minus:
        fmt["unicode_minus"] = True
        raw = raw.replace("−", "-")

    if raw.startswith("~+"):
        fmt["approx_prefix"] = "~"
        fmt["explicit_plus_positive"] = True
        raw = raw[2:]
    elif raw.startswith("~"):
        fmt["approx_prefix"] = "~"
        raw = raw[1:]

    unicode_x = False
    if raw.endswith("×"):
        unicode_x = True
        raw = raw[:-1]
    ratio_x = raw.endswith("x") or unicode_x
    if ratio_x and raw.endswith("x"):
        raw = raw[:-1]

    pp = raw.endswith("pp")
    if pp:
        raw = raw[:-2]

    time_suffix = None
    for sfx in ("/wk", "/day", "/d", "/yr"):
        if raw.endswith(sfx):
            time_suffix = sfx
            raw = raw[: -len(sfx)]
            break

    sci = re.match(r"^([+-])?(\d+(?:\.\d+)?)[eE]([+\-−])(\d+)$", raw)
    if sci:
        sign, mantissa, _exp_sign, exp_digits = sci.groups()
        fmt["scientific"] = True
        fmt["decimal_places"] = len(mantissa.split(".", 1)[1]) if "." in mantissa else 0
        fmt["exponent_pad"] = len(exp_digits)
        if sign == "+":
            fmt["explicit_plus_positive"] = True
        elif sign == "-":
            fmt["negative"] = True
        return fmt

    m = re.match(
        r"^([+-])?(\$)?([0-9,]+(?:\.[0-9]+)?)([kKmMbBtT])?(%?)$",
        raw,
    )
    if m:
        sign, cur, num, scale_sfx, pct = m.groups()
        if sign == "+":
            fmt["explicit_plus_positive"] = True
        elif sign == "-":
            fmt["negative"] = True
        if cur:
            fmt["currency_prefix"] = "$"
        if "," in num:
            fmt["grouping"] = True
        if scale_sfx:
            fmt["scale_suffix"] = scale_sfx
            fmt["scale"] = _SCALE[scale_sfx]
        else:
            fmt["scale"] = 1
        if pct:
            fmt["percent"] = True
        if pp:
            fmt["percentage_points"] = True
        if time_suffix:
            fmt["suffix"] = time_suffix
        fmt["decimal_places"] = len(num.split(".", 1)[1]) if "." in num else 0
        if ratio_x:
            fmt["ratio_x"] = True
            if unicode_x:
                fmt["unicode_x"] = True
        return fmt

    if ratio_x and re.match(r"^\+?[0-9]+(?:\.[0-9]+)?$", raw):
        fmt["ratio_x"] = True
        fmt["scale"] = 1
        fmt["decimal_places"] = len(raw.split(".")[1]) if "." in raw else 0
        if raw.startswith("+"):
            fmt["explicit_plus_positive"] = True
        if unicode_x:
            fmt["unicode_x"] = True
        return fmt

    if "%" in literal and not pp:
        fmt["percent"] = True
        return fmt

    fmt["type"] = "string_exact"
    return fmt


def adjust_formatter_for_binding(
    formatter: dict[str, Any],
    manifest_lit: str,
    effective: str,
    anchor_after: str,
) -> dict[str, Any]:
    fmt = dict(formatter)
    sfx = fmt.get("scale_suffix")
    if sfx and sfx not in effective:
        if anchor_after.lstrip().startswith("<") or sfx in (manifest_lit or ""):
            fmt.pop("scale_suffix", None)
            fmt["external_scale_suffix"] = sfx
    if fmt.get("percent") and "%" not in effective:
        if "%" in anchor_after or anchor_after.lstrip().startswith("<"):
            fmt.pop("percent", None)
            fmt["external_percent"] = True
    return fmt


def _apply_unicode_minus(out: str, formatter: dict[str, Any]) -> str:
    if not formatter.get("unicode_minus"):
        return out
    prefix = formatter.get("approx_prefix", "")
    if prefix and out.startswith(prefix):
        rest = out[len(prefix) :]
        if rest.startswith("-"):
            return prefix + "−" + rest[1:]
    if out.startswith("-"):
        return "−" + out[1:]
    return out


def _format_scientific(shown: Decimal, places: int, exp_pad: int) -> str:
    if shown == 0:
        return f"0.{'0' * places}e-{'0' * exp_pad}"
    sign = "-" if shown < 0 else ""
    d = abs(shown)
    exp = int(d.adjusted())
    coeff = d.scaleb(-exp)
    coeff_s = format(coeff, f".{places}f")
    exp_sign = "+" if exp >= 0 else "-"
    exp_s = str(abs(exp)).zfill(exp_pad)
    return f"{sign}{coeff_s}e{exp_sign}{exp_s}"


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

    if formatter.get("scientific"):
        s = _format_scientific(shown, places, int(formatter.get("exponent_pad", 2)))
        if formatter.get("approx_prefix"):
            s = formatter["approx_prefix"] + s
        return _apply_unicode_minus(s, formatter)

    q = Decimal("1").scaleb(-places)
    shown = shown.quantize(q, rounding=ROUND_HALF_UP)
    if places > 0:
        s = format(shown, f",.{places}f") if formatter.get("grouping") else format(shown, f".{places}f")
    elif shown == shown.to_integral_value():
        shown = shown.to_integral_value()
        s = f"{shown:,}" if formatter.get("grouping") else str(shown)
    else:
        s = f"{shown:,}" if formatter.get("grouping") else str(shown)

    out = ""
    if formatter.get("literal_prefix"):
        out += formatter["literal_prefix"]
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
    if formatter.get("percentage_points"):
        out += "pp"
    if formatter.get("ratio_x"):
        out += "×" if formatter.get("unicode_x") else "x"
    if formatter.get("suffix"):
        out += formatter["suffix"]
    if formatter.get("literal_suffix"):
        out += formatter["literal_suffix"]
    return _apply_unicode_minus(out, formatter)
