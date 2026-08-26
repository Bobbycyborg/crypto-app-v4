#!/usr/bin/env python3
"""Deterministic value extractors and rounding. No semantic identity."""
from __future__ import annotations

import re

ALLOWED_EXTRACTORS = {
    "exact_numeric",
    "usd_amount",
    "usd_per_day",
    "usd_per_week",
    "percent",
    "percentage_points",
    "ratio_x",
    "scientific_number",
    "token_amount",
    "count",
    "window_percent",
    "named_regex_group",
    "explicit_unknown",
}

GENERIC_EXTRACTORS = {"exact_numeric", "usd_amount", "usd_per_day", "usd_per_week", "percent", "percentage_points", "ratio_x", "scientific_number", "token_amount", "count"}


def _to_float(num: str, suf: str = "") -> float:
    n = float(num.replace("−", "-").replace(",", ""))
    u = (suf or "").upper().replace("×", "X")
    if u in ("%", "X"):
        return n
    return n * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}.get(u, 1)


def has_ellipsis_price(lit: str) -> bool:
    s = lit or ""
    return bool(re.search(r"\.\.\.|…", s) and re.search(r"\$?0\.0", s))


def numeric_token_count(lit: str) -> int:
    s = lit or ""
    s = re.sub(r"\b(?:1d|7d|30d|90d|180d|24h)\b", " ", s, flags=re.I)
    s = re.sub(r"~?\d+\s*(?:wks?|weeks?|hours?|epochs?)\b", " ", s, flags=re.I)
    s = re.sub(r"/~\d+d\b", " ", s, flags=re.I)
    return len(re.findall(r"\d+(?:[.,]\d+)?(?:e[+\-]?\d+)?", s, re.I))


def extract_value(extractor: dict | str, literal: str):
    spec = extractor if isinstance(extractor, dict) else {"type": extractor}
    et = spec.get("type") or "explicit_unknown"
    s = (literal or "").strip()
    if et == "explicit_unknown" or has_ellipsis_price(s):
        return "UNKNOWN"
    if et == "scientific_number":
        m = re.search(r"([+\-−]?\d+(?:\.\d+)?)[eE]([+\-]?\d+)", s.replace("−", "-"))
        if not m:
            return "UNKNOWN"
        return float(m.group(1).replace("−", "-") + "e" + m.group(2))
    if et == "percentage_points":
        m = re.search(r"([+\-−]?\d+(?:\.\d+)?)\s*pp\b", s, re.I)
        return float(m.group(1).replace("−", "-")) if m else "UNKNOWN"
    if et == "percent":
        m = re.search(r"\((\d+(?:\.\d+)?)%\)", s)
        if m:
            return float(m.group(1))
        m = re.search(r"([+\-−]?\d+(?:\.\d+)?)\s*%", s)
        return float(m.group(1).replace("−", "-")) if m else "UNKNOWN"
    if et == "window_percent":
        win = spec.get("window") or ""
        m = re.search(rf"{re.escape(win)}\s*([+\-−]?\d+(?:\.\d+)?)\s*%", s, re.I)
        if m:
            return float(m.group(1).replace("−", "-"))
        m = re.search(rf"([+\-−]?\d+(?:\.\d+)?)\s*%\s*/?\s*{re.escape(win)}", s, re.I)
        return float(m.group(1).replace("−", "-")) if m else "UNKNOWN"
    if et == "named_regex_group":
        pat = spec.get("pattern") or ""
        grp = spec.get("group") or 1
        suf = spec.get("suffix") or ""
        m = re.search(pat, s, re.I)
        if not m:
            return "UNKNOWN"
        raw = m.group(grp)
        sm = re.match(r"([+\-−]?\d[\d,]*(?:\.\d+)?)([KMBTkmbt]?)", raw.replace("−", "-").replace(",", ""))
        if not sm:
            try:
                return float(str(raw).replace("−", "-").replace(",", ""))
            except ValueError:
                return "UNKNOWN"
        return _to_float(sm.group(1), suf or sm.group(2))
    if et == "ratio_x":
        m = re.search(r"([+\-−]?\d+(?:\.\d+)?)\s*[x×]", s, re.I)
        return float(m.group(1).replace("−", "-")) if m else "UNKNOWN"
    if et == "count":
        if spec.get("pattern"):
            return extract_value({"type": "named_regex_group", **spec}, s)
        m = re.search(r"([\d,]+)", s)
        return float(m.group(1).replace(",", "")) if m else "UNKNOWN"
    if et in {"usd_amount", "usd_per_day", "usd_per_week", "token_amount", "exact_numeric"}:
        if et == "usd_per_day" and "/d" not in s.lower() and spec.get("require_unit"):
            pass
        m = re.search(
            r"([+\-−]?\d[\d,]*(?:\.\d+)?)([KMBTkmbt]?)",
            s.replace("$", "").replace("~", "").replace("−", "-"),
        )
        if not m:
            return "UNKNOWN"
        return _to_float(m.group(1), m.group(2))
    return "UNKNOWN"


_SUFFIX_SCALE = {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}


def display_coeff(lit: str):
    s = (lit or "").strip()
    s = re.sub(r"[~$%\s×x]", "", s, flags=re.I)
    s = s.replace(",", "").replace("−", "-")
    m = re.search(r"(-?\d+(?:\.(\d+))?)([KMBT])?", s, re.I)
    if not m:
        return None, "", None
    coeff = float(m.group(1))
    places = len(m.group(2) or "")
    suf = (m.group(3) or "").upper()
    return coeff, suf, places


def rounding_equivalent(a, b, lit_a: str, lit_b: str) -> bool:
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return False
    if a == b:
        return True
    ca, sa, da = display_coeff(lit_a)
    cb, sb, db = display_coeff(lit_b)
    if ca is None or cb is None or da is None or db is None:
        return False
    if da <= db:
        places, suf, coeff = da, sa, ca
        other_raw = float(b)
    else:
        places, suf, coeff = db, sb, cb
        other_raw = float(a)
    scale = _SUFFIX_SCALE.get(suf, 1.0)
    other_in_unit = other_raw / scale
    return round(other_in_unit, places) == round(coeff, places)
