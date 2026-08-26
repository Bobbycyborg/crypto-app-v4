#!/usr/bin/env python3
"""Job 1 helpers: explode, nonmetric, shape. Semantic identity lives in ui-mapping-manifest.json."""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

BANNED_FAMILIES = {"captured", "usd_figure", "pct_figure", "pp_figure"}
DORMANT_SLUGS = {"ray", "grass"}
META_KEYS = {
    "evidence", "confidence", "freshness", "caveat", "unknown", "detail",
    "sample", "discipline", "label", "scope", "rule", "status", "read",
    "coverage", "verdict", "note", "known",
}
PROSE_RE = re.compile(r"volume|estimate|formula|last price|× 24h|×24h|explanatory", re.I)
HAS_NUM = re.compile(r"\d")
SLASH_SPLIT = re.compile(r"\s*/\s*")

# rest → (definition, value_kind, allowed_unit, shape)
CATALOG: dict[str, tuple[str, str, str, str]] = {}


def family(rest: str, definition: str, value_kind: str, unit: str, shape: str) -> None:
    CATALOG[rest] = (definition, value_kind, unit, shape)


def _seed() -> None:
    if CATALOG:
        return
    path = Path(__file__).resolve().parents[2] / "metrics" / "metric-families.json"
    data = json.loads(path.read_text())
    for rest, spec in data.items():
        CATALOG[rest] = (
            spec["definition"],
            spec["value_kind"],
            spec["allowed_unit"],
            spec["allowed_literal_shape"],
        )


_seed()
DEFS = {k: v[0] for k, v in CATALOG.items()}
TYPE_SPEC = {k: (v[1], v[2], v[3]) for k, v in CATALOG.items()}


def is_non_value_label(lit: str) -> bool:
    s = (lit or "").strip()
    if not s:
        return False
    if re.fullmatch(r"(?:last\s+)?\d+\s*(?:wks?|weeks?|days?|d|hours?|h|epochs?)\.?", s, re.I):
        return True
    if re.fullmatch(r"/?\s*~?\d+\s*h", s, re.I):
        return True
    if re.search(r"means at anchor", s, re.I):
        return True
    if re.search(r"^print\s*[−\-+/]", s, re.I) and not looks_like_funding_rate(s):
        return True
    if re.fullmatch(r"[±+\-−]?\d+\s*d\s+means.*", s, re.I):
        return True
    return False


def looks_like_funding_rate(lit: str) -> bool:
    s = (lit or "").strip()
    if not s or re.fullmatch(r"/?\s*~?\d+\s*h", s, re.I):
        return False
    if re.search(r"means at anchor", s, re.I):
        return False
    if re.search(r"^print\s*[−\-+/]", s, re.I) and not re.search(r"\d(?:\.\d+)?[eE][+\-]|\d%/8h|-0\.\d+", s):
        return False
    if re.search(r"\d(?:\.\d+)?[eE][+\-]?\d+", s):
        return True
    if re.search(r"[+\-−]?\d+(?:\.\d+)?%\s*/\s*8h", s, re.I):
        return True
    if re.search(r"[+\-−]?0\.0+\d+", s):
        return True
    if re.search(r"[+\-−]?\d+\.\d+%?\s*/\s*8h", s, re.I):
        return True
    return False


def _to_float(num: str, suf: str = "") -> float:
    n = float(num.replace("−", "-").replace(",", ""))
    u = (suf or "").upper()
    if u in ("%", "X", "×"):
        return n
    return n * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}.get(u, 1)


def parse_raw(literal: str, value_kind: str | None = None, rest: str | None = None):
    s = (literal or "").strip()
    vk = (value_kind or "").upper()
    rest = rest or ""
    if not s or is_address_literal(s) or is_prose_status(s):
        return "UNKNOWN"
    if is_non_value_label(s):
        return "UNKNOWN"
    if re.search(r"\byears?\b", s, re.I) and vk in {"TOKEN_AMOUNT", ""}:
        return "UNKNOWN"
    if re.search(r"\.\.\.|…", s) and re.search(r"\$?0\.0", s):
        return "UNKNOWN"

    sci = re.search(r"([+\-−]?\d+(?:\.\d+)?)[eE]([+\-]?\d+)", s.replace("−", "-"))
    if sci and (vk in {"", "FUNDING_RATE"} or "funding.rate" in rest):
        return float(sci.group(1).replace("−", "-") + "e" + sci.group(2))

    if vk == "PERCENTAGE_POINTS" or ".pp." in f".{rest}" or re.search(r"\d\s*pp\b", s, re.I):
        m = re.search(r"([+\-−]?\d+(?:\.\d+)?)\s*pp\b", s, re.I)
        if not m:
            return "UNKNOWN"
        return float(m.group(1).replace("−", "-"))

    if vk == "PERCENT":
        m = re.search(r"\((\d+(?:\.\d+)?)%\)", s)
        if m:
            return float(m.group(1))
        m = re.search(r"([+\-−]?\d+(?:\.\d+)?)\s*%", s)
        if m:
            return float(m.group(1).replace("−", "-"))
        return "UNKNOWN"

    if vk == "FUNDING_RATE" or "funding.rate" in rest:
        if not looks_like_funding_rate(s):
            return "UNKNOWN"
        if sci:
            return float(sci.group(1).replace("−", "-") + "e" + sci.group(2))
        m = re.search(r"([+\-−]?\d+(?:\.\d+)?)(%)?", s.replace("−", "-"))
        if not m:
            return "UNKNOWN"
        return float(m.group(1).replace("−", "-"))

    if "gpu_hours" in rest or (vk == "COUNT" and re.search(r"\d[\d,]*\s*h\b", s, re.I)):
        m = re.search(r"([\d,]+(?:\.\d+)?)\s*h\b", s, re.I)
        if m:
            return float(m.group(1).replace(",", ""))

    if "jobs.running" in rest:
        m = re.search(r"([\d,]+)\s*run", s, re.I) or re.search(r"([\d,]+)", s)
        if m:
            return float(m.group(1).replace(",", ""))

    compact = s.replace("~", "").replace(",", "")
    for m in re.finditer(
        r"([+\-−]?\d+(?:\.\d+)?)([KMBTkmbt%x×]?)",
        compact.replace("$", "").replace("/wk", "").replace("/d", "").replace("−", "-"),
    ):
        after = compact[m.end():m.end() + 4]
        if re.match(r"[dD]\b", after) and not m.group(2):
            continue
        if re.match(r"[hH]\b", after) and "gpu" not in rest and vk != "COUNT":
            continue
        if re.match(r"\s*(?:wks?|weeks?)\b", after, re.I):
            continue
        return _to_float(m.group(1), m.group(2))
    return "UNKNOWN"


def is_address_literal(lit: str) -> bool:
    s = (lit or "").strip()
    if re.search(r"[1-9A-HJ-NP-Za-km-z]{6,}(?:…|\.\.\.)", s):
        return True
    if re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", s):
        return True
    return False


def is_prose_status(lit: str) -> bool:
    s = (lit or "").strip()
    if re.search(r"do not use", s, re.I):
        return True
    if re.search(r"\b(leads|lags)\b", s, re.I) and re.search(r"\b(btc|sol)\b", s, re.I) and "%" not in s:
        return True
    if re.match(r"^(leads|lags|leading|lagging)\b", s, re.I) and "$" not in s and "%" not in s:
        return True
    return False


def detect_kind(lit: str) -> str:
    s = (lit or "").strip()
    if not s:
        return "EMPTY"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T[\d:.]+Z?)?", s):
        return "DATE"
    if PROSE_RE.search(s) and not re.search(r"[x×]", s) and "$" not in s:
        return "PROSE"
    if re.search(r"\d+\s*pp\b", s, re.I) or s.lower().endswith("pp"):
        return "PERCENTAGE_POINTS"
    if re.fullmatch(r"[A-Za-z][A-Za-z /·.+%-]{1,40}", s) and not re.search(r"\d", s):
        return "STATUS_TEXT"
    if "/d" in s.lower() and "$" in s:
        return "USD_PER_DAY"
    if re.search(r"/8h|e-0|/ 8h", s, re.I) and "$" not in s:
        return "FUNDING_RATE"
    if re.search(r"[x×]", s) and "$" not in s and "%" not in s:
        return "RATIO_X"
    if "$" in s:
        raw = parse_raw(s)
        if "/wk" in s.lower():
            return "USD_7D_TOTAL"
        if isinstance(raw, (int, float)) and raw >= 1e8:
            return "USD_AMOUNT"
        if re.search(r"[MBT]\b", s.replace(",", "")):
            return "USD_AMOUNT"
        return "PRICE_USD" if isinstance(raw, (int, float)) and raw < 1e8 else "USD_AMOUNT"
    if "%" in s:
        return "PERCENT"
    if re.search(r"\d+\s*of\s*\d+", s, re.I):
        return "COUNT"
    if re.search(r"\d+(?:\.\d+)?[KMBT]\b", s, re.I) and "$" not in s:
        return "TOKEN_AMOUNT"
    if re.search(r"\b(BTC|SOL|ETH|PUMP|HYPE|tokens?|ZEC)\b", s, re.I) and "$" not in s:
        return "TOKEN_AMOUNT"
    if re.fullmatch(r"[+\-−]\d+(?:\.\d+)?", s):
        return "DELTA"
    if re.fullmatch(r"~?\d+(?:\.\d+)?", s):
        return "COUNT"
    if re.search(r"\d", s):
        return "OTHER"
    return "STATUS_TEXT"


def shape_ok(shape: str, lit: str) -> bool:
    kind = detect_kind(lit)
    if shape == "ratio_x":
        return kind == "RATIO_X" and "$" not in lit and "%" not in lit and not PROSE_RE.search(lit)
    if shape == "ratio_loose":
        return kind in {"RATIO_X", "INDEX", "COUNT", "OTHER"} and "$" not in lit and "%" not in lit
    if shape == "percent":
        return kind in {"PERCENT", "PERCENTAGE_POINTS"} and "$" not in lit
    if shape == "percent_or_rate":
        return kind in {"PERCENT", "FUNDING_RATE"} and "$" not in lit
    if shape == "funding_rate":
        return looks_like_funding_rate(lit) and "$" not in lit
    if shape == "usd_amount":
        return kind in {"USD_AMOUNT", "PRICE_USD", "USD_7D_TOTAL", "USD_PER_DAY"} and "$" in lit and "×" not in lit
    if shape == "usd_per_day":
        return "$" in lit and ("/d" in lit.lower() or detect_kind(lit) in {"USD_PER_DAY", "USD_AMOUNT", "PRICE_USD"})
    if shape == "price_usd":
        return "$" in lit and "%" not in lit and "/d" not in lit.lower() and "/wk" not in lit.lower()
    if shape == "threshold":
        if lit.strip() in {"—", "-", "–", ""}:
            return True
        if "close" in lit.lower() or "under" in lit.lower():
            return True
        return "$" in lit or lit.strip() in {"—"}
    if shape == "index_0_100":
        if detect_kind(lit) in {"DATE", "DELTA", "STATUS_TEXT", "PERCENT"}:
            return False
        if lit.startswith("+") or lit.startswith("−"):
            return False
        try:
            n = float(re.sub(r"[^\d.]", "", lit))
        except ValueError:
            return False
        return 0 <= n <= 100
    if shape == "count":
        return kind in {"COUNT", "INDEX", "TOKEN_AMOUNT", "OTHER"} and "$" not in lit
    if shape == "token_or_count":
        return kind in {"TOKEN_AMOUNT", "COUNT", "INDEX", "OTHER"} and "$" not in lit
    if shape == "ma_level":
        return kind in {"PRICE_USD", "USD_AMOUNT", "INDEX", "COUNT", "OTHER", "TOKEN_AMOUNT"} or bool(re.search(r"\d", lit))
    if shape == "pp":
        return kind in {"PERCENTAGE_POINTS", "PERCENT", "DELTA"} or "pp" in lit.lower()
    if shape == "any_numeric":
        return bool(re.search(r"\d", lit))
    return False


def ensure(rest: str, lit: str, definition: str | None = None) -> str:
    raise RuntimeError("automatic_metric_creation is forbidden")


def spec_from_kind(kind: str, rest: str, lit: str) -> tuple[str, str, str]:
    if "usd_per_day" in rest or "/d" in lit.lower():
        return ("USD_PER_DAY_MEAN_30D" if "mean_30d" in rest else "USD_PER_DAY", "USD/day", "usd_per_day")
    if (rest.endswith(".30d") or ".30d." in rest) and "usd" in rest:
        return ("USD_30D_TOTAL", "USD", "usd_amount")
    if (rest.endswith(".7d") or ".7d." in rest) and "usd" in rest:
        return ("USD_7D_TOTAL", "USD", "usd_amount")
    if "funding" in rest:
        return ("FUNDING_RATE", "rate", "funding_rate")
    if rest.endswith(".pp") or ".pp." in rest:
        return ("PERCENTAGE_POINTS", "pp", "pp")
    if "ma.usd" in rest:
        return ("MA_LEVEL", "USD", "ma_level")
    mapping = {
        "USD_AMOUNT": ("USD_AMOUNT", "USD", "usd_amount"),
        "USD_PER_DAY": ("USD_PER_DAY", "USD/day", "usd_per_day"),
        "USD_7D_TOTAL": ("USD_7D_TOTAL", "USD", "usd_amount"),
        "PRICE_USD": ("PRICE_USD", "USD", "price_usd"),
        "PERCENT": ("PERCENT", "%", "percent"),
        "PERCENTAGE_POINTS": ("PERCENTAGE_POINTS", "pp", "pp"),
        "RATIO_X": ("RATIO_X", "x", "ratio_x"),
        "TOKEN_AMOUNT": ("TOKEN_AMOUNT", "tokens", "token_or_count"),
        "COUNT": ("COUNT", "count", "count"),
        "INDEX": ("INDEX", "index", "index_0_100"),
        "FUNDING_RATE": ("FUNDING_RATE", "rate", "funding_rate"),
    }
    return mapping.get(kind, ("USD_AMOUNT" if "$" in lit else "COUNT", "text", "any_numeric"))


def type_accepts(rest: str, lit: str) -> bool:
    spec = TYPE_SPEC.get(rest)
    if not spec:
        return False
    return shape_ok(spec[2], lit)


def slug_id(asset_slug: str, rest: str) -> str:
    a = "fart" if asset_slug == "fartcoin" else "spx" if asset_slug == "spx6900" else asset_slug
    a = re.sub(r"[^a-z0-9]+", "", a)
    return f"{a}.{rest}"


def infer_window(row: str, tip: str, hint: str, lit: str, parent_label: str = "", source: str = "", inherited: str = "") -> str:
    """Event/historical parent context beats unit tokens such as /d in the child literal."""
    event = inherited or _event_from(f"{row} {parent_label}") or _event_from(tip)
    if not event:
        event = _event_from(lit) if not re.search(r"/d", (lit or "").lower()) else None
    if event:
        return event
    obs = _observation_window(f"{row} {hint}")
    if obs:
        return obs
    obs = _observation_window(f"{tip} {parent_label}")
    if obs:
        return obs
    obs = _observation_window(lit)
    if obs:
        return obs
    return "current"


def _event_from(s: str) -> str | None:
    b = (s or "").lower()
    if not b.strip():
        return None
    if re.search(r"\bnow\b", b) and not re.search(r"ath sep|jan high|june atl|stage\s*1|jan 2025|nov 2024", b):
        return None
    if "ath sep" in b or (re.search(r"\bath\b", b) and re.search(r"\bsep\b", b)):
        return "ath_sep"
    if "jan high" in b:
        return "jan_high"
    if "june atl" in b or "jun atl" in b:
        return "june_atl"
    if "nov 2024" in b:
        return "nov_2024"
    if "stage1" in b or "stage 1" in b:
        return "stage1"
    if "jan 2025" in b:
        if "tvl" in b:
            return "jan_2025"
        if "fee" in b or "ath" in b:
            return "jan_2025_ath"
        return "jan_2025"
    if "june 2026" in b and "fee" in b:
        return "june_2026"
    if re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", b) and len(re.findall(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", b)) >= 2:
        return None
    if re.search(r"\bjuly\b", b) and "earn" in b:
        return "july_2026"
    if re.search(r"\bmay\b", b) and "earn" in b:
        return "may_2026"
    if re.search(r"\bjune\b", b) and "earn" in b:
        return "june_2026"
    return None


def _observation_window(s: str) -> str | None:
    b = (s or "").lower()
    if "cumulative" in b:
        return "cumulative"
    if "30d mean" in b or "30d avg" in b or "avg /d" in b or "avg/day" in b:
        return "mean_30d"
    if "7d mean" in b or "±7d" in b:
        return "mean_7d"
    if "latest print" in b or "latest 8h" in b or re.search(r"\blatest\b", b):
        if "7d mean" not in b:
            return "latest"
    compact = b.replace(" ", "").replace("-", "")
    for token, w in (
        ("alltime", "all_time"), ("24h", "1d"),
        ("180d", "180d"), ("90d", "90d"), ("30d", "30d"),
        ("7d", "7d"), ("1d", "1d"),
    ):
        if token.replace("-", "") in compact:
            return w
    if b.strip() in {"30d", "7d", "1d"}:
        return b.strip()
    return None


def historical_container(c: dict, extra: str = "") -> str | None:
    blob = " ".join([
        c.get("label") or "",
        c.get("tip_name") or "",
        c.get("parent_label") or "",
        c.get("window_hint") or "",
        extra,
    ]).lower()
    ev = _event_from(blob)
    if ev:
        return ev
    src = (c.get("source") or "").lower()
    row = (c.get("label") or "").lower().strip()
    if "stage1" in blob or "stage 1" in blob or "stage-1" in blob:
        return "stage1"
    if ("stage1" in src or "stage 1" in src or "stage-1" in src) and row in {"evidence", ""}:
        return "stage1"
    return None


def rest_scope(rest: str) -> str:
    r = rest or ""
    for key, scope in (
        ("volume.spot.", "SPOT"), ("volume.perp.", "PERP"), ("volume.l1_perp.", "L1_PERP"),
        ("volume.token.", "TOKEN"), ("volume.cg.", "CG"),
        ("oi.platform.", "PLATFORM"), ("oi.token.", "TOKEN"), ("oi.binance.", "BINANCE"),
        ("oi.native.", "NATIVE"), ("oi.change.", "OI_CHANGE"), ("oi.btc.", "BTC"),
        ("fees.perps.", "PERPS"), ("return.pct.", "PRICE"),
        ("rs.vs_btc.", "RS_BTC"), ("rs.vs_sol.", "RS_SOL"),
        ("holders.unit_treasury.", "UNIT_TREASURY"), ("holders.lp.", "LP"),
        ("holders.unattributed.", "UNATTRIBUTED"), ("holders.top20.", "TOP20"),
        ("mm.wintermute.", "WALLET_MM"), ("wallet.", "WALLET"), ("siren.", "WALLET"),
        ("buyback.", "BUYBACK"), ("revenue.", "REVENUE"), ("fees.", "FEES"),
    ):
        if r.startswith(key) or f".{key}" in f".{r}":
            return scope
    return "UNSPECIFIED"


def infer_scope(row: str, tip: str, parent: str, lit: str) -> str:
    r = (row or "").lower()
    if "l1 perp" in r:
        return "L1_PERP"
    if "hype-token" in r and ("vol" in r or "day" in r) and "oi" not in r:
        return "TOKEN"
    if "hype-token oi" in r:
        return "TOKEN"
    if r in {"spot 24h"} or (r.startswith("spot") and "24h" in r):
        return "SPOT"
    if r in {"perp 24h", "perps 24h", "binance perp 24h"}:
        return "PERP"
    if "cg" in r and "vol" in r:
        return "CG"
    if "platform oi" in r or r == "platform oi":
        return "PLATFORM"
    if "native" in r and "oi" in r:
        return "NATIVE"
    if "binance" in r and "oi" in r:
        return "BINANCE"
    if r in {"unit"} or r.endswith(" unit"):
        return "UNIT_TREASURY"
    if r in {"lp"}:
        return "LP"
    if "unattributed" in r:
        return "UNATTRIBUTED"
    if "wintermute" in r or "wintermute" in (tip or "").lower():
        return "WALLET_MM"
    if "open interest" in r or r.endswith(" oi") or r in {"oi", "oi trend", "oi δ"}:
        return "OI_CHANGE" if "%" in (lit or "") else "UNSPECIFIED"
    return "UNSPECIFIED"


def is_historical_window(win: str) -> bool:
    return win in {
        "nov_2024", "june_2026", "jan_2025", "jan_2025_ath",
        "july_2026", "may_2026", "all_time", "ath",
        "ath_sep", "jan_high", "june_atl", "stage1",
    }


def update_mode_for(c: dict, rest: str, mtype: str) -> str:
    if mtype == "WALLET_OWNED" or rest.startswith("siren.") or rest.startswith("portfolio.") or rest.startswith("mm.") or rest.startswith("wallet."):
        return "WALLET_SNAPSHOT"
    if mtype == "STATIC_DECISION_THRESHOLD":
        return "STATIC_THRESHOLD"
    if mtype == "HISTORICAL" or is_historical_window(rest.split(".")[-1]):
        return "HISTORICAL"
    cs = set((c.get("element_class") or "").split())
    kind = c.get("kind") or ""
    if "hold-px" in cs or kind == "attr:data-live-px" or "desk-px" in cs:
        return "LIVE"
    if rest.endswith(".live") or rest == "price.usd.live":
        return "LIVE"
    return "REPORT_SNAPSHOT"


def has_number(lit: str) -> bool:
    return bool(HAS_NUM.search(lit or ""))


def explode_atomic(cands: list[dict]) -> list[dict]:
    out: list[dict] = []
    for c in cands:
        kids = _children_from(c)
        if kids:
            parent = deepcopy(c)
            parent["kind"] = parent.get("kind") or "compound"
            parent["is_compound_parent"] = True
            out.append(parent)
            out.extend(kids)
        else:
            out.append(c)
    return out


def _child(parent: dict, literal: str, label: str, extra_rest: str | None = None) -> dict:
    ch = deepcopy(parent)
    ch["literal"] = re.sub(r"\s+", " ", literal).strip()
    ch["parent_label"] = parent.get("label") or parent.get("parent_label") or ""
    ch["label"] = label
    ch["parent_occurrence_id"] = parent["occurrence_id"]
    ch["kind"] = "atomic_span"
    ch["is_compound_parent"] = False
    ch["occurrence_id"] = parent["occurrence_id"] + ":" + re.sub(r"[^a-z0-9]+", "", (label + literal).lower())[:18]
    ch["observation_anchor"] = (
        historical_container(parent, f"{parent.get('label','')} {label}")
        or _event_from(ch["parent_label"])
        or ("now" if re.search(r"\bnow\b", (ch["parent_label"] + " " + label).lower()) else None)
    )
    if extra_rest:
        ev = historical_container(parent) or _event_from(ch["parent_label"])
        if ev and is_historical_window(ev):
            if extra_rest.endswith(".current"):
                extra_rest = extra_rest[: -len("current")] + ev
            elif extra_rest.endswith((".30d", ".7d", ".1d")):
                extra_rest = extra_rest + "." + ev
        ch["forced_rest"] = extra_rest
    return ch


def _children_from(c: dict) -> list[dict]:
    if c.get("kind") == "econ_bar_title":
        return []
    lit = c.get("literal") or ""
    row = (c.get("label") or "").strip()
    row_l = row.lower()
    kids: list[dict] = []

    labs = [x.strip() for x in SLASH_SPLIT.split(row) if x.strip()]
    vals = [x.strip() for x in SLASH_SPLIT.split(lit) if x.strip()]
    if (
        len(labs) >= 2
        and len(vals) == len(labs)
        and all(has_number(v) for v in vals)
        and len(lit) < 160
        and row_l not in META_KEYS
        and "unlockschedule" not in row_l.replace(" ", "")
    ):
        for lab, val in zip(labs, vals):
            kids.append(_child(c, val, lab))
        return kids

    # percent + explicit window only (do not split "Staked 68.8% · inflation 3.7%")
    bits = re.findall(r"([+\-−]?\d[\d.]*%\s*(?:1d|7d|30d|90d|180d))", lit, re.I)
    if len(bits) >= 2 and row_l not in META_KEYS:
        for bit in bits:
            w = re.search(r"(1d|7d|30d|90d|180d)", bit, re.I).group(1).lower()
            kids.append(_child(c, bit.strip(), f"{row} {w}"))
        return kids
    bits_w = re.findall(r"((?:1d|7d|30d|90d|180d)\s*[+\-−]?\d[\d.]*%)", lit, re.I)
    if len(bits_w) >= 2 and row_l not in META_KEYS:
        for bit in bits_w:
            w = re.search(r"(1d|7d|30d|90d|180d)", bit, re.I).group(1).lower()
            kids.append(_child(c, bit.strip(), w))
        return kids
    bits_pp = re.findall(r"((?:1d|7d|30d|90d|180d)\s*[+\-−]?\d[\d.]*\s*pp)", lit, re.I)
    if len(bits_pp) >= 2 and row_l not in META_KEYS:
        for bit in bits_pp:
            w = re.search(r"(1d|7d|30d|90d|180d)", bit, re.I).group(1).lower()
            kids.append(_child(c, bit.strip(), w))
        return kids
    parts = [x.strip() for x in re.split(r"\s*[·•∙⋅]\s*", lit) if x.strip()]
    def _part_value(val: str) -> str | None:
        if re.search(r"\b(run|jobs?|queued|h|hours?|gpu-?h)\b", val, re.I):
            m = re.search(r"([\d,]+(?:\.\d+)?)", val)
            if m:
                return m.group(0)
        if re.search(r"\b\d+[dD]\b", val) and not re.search(r"\$|%|[x×]|e[+\-]|/d|/wk|/8h|\bpp\b", val, re.I):
            return None
        if re.search(r"percentile|pctile|\d(?:st|nd|rd|th)\b", val, re.I):
            pm = re.search(r"~?\d+(?:\.\d+)?(?:st|nd|rd|th)?", val, re.I)
            if pm:
                return pm.group(0)
        m = re.search(
            r"([~\-−+$]?\d[\d,]*(?:\.\d+)?(?:e[+\-]?\d+)?(?:[KMB])?(?:T(?![a-z]))?(?:%|/d|/wk|/yr|/8h)?(?:[x×])?)",
            val,
        )
        if not m:
            return None
        num = m.group(1)
        if re.fullmatch(r"~?\d+[dD]?", num) and not re.search(r"\$|%|[x×]|[KMBT]|e[+\-]|/d|/8h", num, re.I):
            return None
        if not re.search(r"\$|%|[x×]|[KMBTe]|/d|/wk|/yr|/8h", num, re.I) and not re.search(r"\$|%|[x×]|e[+\-]|/d|/wk|/8h|[KMBT]\b", val, re.I):
            return None
        return num

    if len(parts) >= 2 and all(has_number(v) for v in parts) and len(lit) < 160 and row_l not in META_KEYS:
        extracted = [(p, _part_value(p)) for p in parts]
        if all(num for _, num in extracted):
            for i, (val, num) in enumerate(extracted):
                lab = re.split(r"\s*[$~+\-−\d]", val, maxsplit=1)[0].strip(" ·:-") or f"{row} p{i+1}"
                trail = re.search(r"(?:%|[x×]|[KMBT]|/d)\s+([A-Za-z][A-Za-z0-9+\- ]{0,28})$", val)
                if trail:
                    lab = trail.group(1).strip()
                if re.search(r"\brun\b", val, re.I):
                    lab = "run"
                elif re.search(r"\bqueued\b", val, re.I):
                    lab = "queued"
                elif re.search(r"\bh\b|gpu", val, re.I):
                    lab = "gpu hours"
                kids.append(_child(c, num, lab))
            return kids

    # labeled evidence spans
    if row_l in {"evidence", ""} or c.get("kind") in {"fx_ev_v", "ev_tip_read"}:
        hist = historical_container(c, lit)
        for rx, lab in (
            (r"(?:^|[^A-Za-z0-9])50d\s*[~≈]?\s*(\$?\d[\d,.]*)", "50d"),
            (r"(?:^|[^A-Za-z0-9])200d\s*[~≈]?\s*(\$?\d[\d,.]*)", "200d"),
            (r"(?:^|[^A-Za-z0-9])20d\s*[~≈]?\s*(\$?\d[\d,.]*)", "20d"),
            (r"OI\s*[~≈]?\s*(~?\d[\d.]+k\s*BTC)", "OI BTC"),
            (r"fut/spot\s*[~≈]?\s*(~?\d[\d.]+×)", "fut/spot"),
            (r"stablecoins?\s*[~≈]?\s*(\$[\d.]+[MBT])", "Stablecoins"),
            (r"frames?\s*[~≈]?\s*(~?[\d.]+M)", "Frames"),
            (r"perps?\s*30d\s*(?:fees)?\s*[~≈]?\s*(\$[\d.]+[MB])", "Fees 30d"),
            (r"Staked\s+(\d+(?:\.\d+)?%)", "Staked"),
            (r"inflation\s+(\d+(?:\.\d+)?%)", "inflation"),
            (r"TPS[^\d~]*~?(\d+(?:\.\d+)?)\s*all", "TPS all"),
            (r"~?(\d+(?:\.\d+)?)\s*non-vote", "TPS nv"),
            (r"fees?\s*30d\s*mean\s+(\$[\d,]+(?:\.\d+)?(?:[kKmM])?/d)", "fees 30d mean"),
        ):
            m = re.search(rx, lit, re.I)
            if m:
                kids.append(_child(c, m.group(1), lab))
        for m in re.finditer(
            r"TVL\s*[~≈]?\s*(\$[\d.]+[MBT])(?:\s*vs\s*(~?\$[\d.]+[MBT]))?",
            lit,
            re.I,
        ):
            kids.append(_child(c, m.group(1), "TVL"))
            if m.group(2):
                kids.append(_child(c, m.group(2).lstrip("~"), "TVL ATH"))
    return kids



def nonmetric_preclassify(c: dict) -> dict:
    """Nonmetric / coverage helpers only. Does not assign metric identity."""
    lit = c.get("literal") or ""
    slug = c.get("asset_slug") or ""
    label = (c.get("label") or "").strip()
    row = label.lower().strip()
    kind = c.get("kind") or ""
    tip = (c.get("tip_name") or "").strip()
    blob = f"{row} {tip.lower()} {lit}".lower()

    def non(state, rule, owner="CGPT_CURSOR"):
        c["coverage_state"] = state
        c["classification_rule"] = rule
        c["metric_id"] = None
        c["owner"] = owner
        return c

    if slug in DORMANT_SLUGS:
        owner = "GROK" if kind == "siren_json" else "CGPT_CURSOR"
        return non("LEGACY_INACTIVE", "dormant_asset_excluded", owner)
    if c.get("is_compound_parent"):
        return non(
            "EVIDENCE_REFERENCE" if row in META_KEYS or row == "evidence" else "COMPOSITE_DISPLAY",
            "compound_parent",
        )
    if is_non_value_label(lit):
        return non("CONTEXT_ONLY", "non_value_label")
    if kind in {"ev_tip_read"} and len(lit) > 70:
        return non("EVIDENCE_REFERENCE", "long_prose_container")
    if row in {"definition", "coinbase estimate", "label", "comparator label"}:
        return non("QUALITATIVE_NON_METRIC", "definition_text")
    if row in META_KEYS:
        return non("EVIDENCE_REFERENCE" if row == "evidence" else "QUALITATIVE_NON_METRIC", f"meta_key_{row}")
    if "last price" in lit.lower() and "volume" in lit.lower():
        return non("QUALITATIVE_NON_METRIC", "formula_prose")
    if is_address_literal(lit):
        return non("CONTEXT_ONLY", "address_not_metric", "GROK")
    if is_prose_status(lit):
        return non("QUALITATIVE_NON_METRIC", "prose_status_not_metric")
    if re.search(r"\byears?\b", lit, re.I) and "emission" in blob:
        return non("QUALITATIVE_NON_METRIC", "duration_not_tokens")
    dk = detect_kind(lit)
    if dk == "DATE":
        return non("CONTEXT_ONLY", "as_of_date_stamp")
    if dk == "STATUS_TEXT":
        return non("QUALITATIVE_NON_METRIC", "status_label")
    if dk == "PROSE" and not re.search(r"\d", lit):
        return non("EVIDENCE_REFERENCE", "formula_or_prose")
    if re.fullmatch(r"(?:~?\d+\s*)?(?:[127]d|30d|90d|180d|24h)|/ ?day|/d|/ ?7d|/ ?30d", lit.strip(), re.I):
        return non("CONTEXT_ONLY", "window_label_not_value")
    if len(lit) >= 40:
        return non("EVIDENCE_REFERENCE", "long_prose_container")
    if "mint verified" in lit.lower():
        return non("EVIDENCE_REFERENCE", "long_prose_container")
    if re.match(r"^(not |unknown|n/?a|none packed)", lit.strip(), re.I):
        return non("QUALITATIVE_NON_METRIC", "negation_status")
    if re.fullmatch(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}", lit.strip(), re.I):
        return non("CONTEXT_ONLY", "month_year_stamp")
    if re.match(r"^(above|below|intact|holding|leading|lagging)\b", lit.strip(), re.I) and "$" not in lit:
        return non("QUALITATIVE_NON_METRIC", "relation_status")
    if re.search(r"last\s+\d+\s+wks?", lit, re.I) and not re.search(r"\$|%", lit):
        return non("CONTEXT_ONLY", "non_value_label")
    return c


def classify(c: dict) -> dict:
    """Kept for import compatibility. Does not assign metric identity."""
    return nonmetric_preclassify(c)


def is_dynamic_numeric(c: dict) -> bool:
    if (c.get("asset_slug") or "") in DORMANT_SLUGS:
        return False
    if c.get("classification_rule") in {
        "window_label_not_value", "month_year_stamp", "as_of_date_stamp",
        "econ_bar_series_point", "formula_or_prose", "formula_prose",
        "definition_text", "relation_status", "index_delta_not_level",
        "long_prose_container", "status_sentence", "rev_7d_reject", "mm_scan_note", "nu6_split", "negation_status",
        "prose_status_not_metric", "address_not_metric", "duration_not_tokens", "no_explicit_family",
        "non_value_label", "funding_not_rate", "window_label_not_value",
    }:
        return False
    if len(c.get("literal") or "") > 70 and (c.get("kind") in {"ev_tip_read"} or (c.get("label") or "").lower() in META_KEYS):
        return False
    if c.get("coverage_state") in {
        "LEGACY_INACTIVE", "CONTEXT_ONLY", "EVIDENCE_REFERENCE",
        "QUALITATIVE_NON_METRIC", "FALSE_POSITIVE", "COMPOSITE_DISPLAY",
    } and not c.get("metric_id"):
        return False
    if c.get("coverage_state") == "LEGACY_INACTIVE":
        return False
    if c.get("is_compound_parent"):
        return False
    lit = c.get("literal") or ""
    if not has_number(lit):
        return False
    row = (c.get("label") or "").lower().strip()
    if row in META_KEYS:
        return False
    if is_non_value_label(lit) or is_address_literal(lit) or is_prose_status(lit):
        return False
    dk = detect_kind(lit)
    if dk in {"DATE", "STATUS_TEXT", "PROSE", "EMPTY"}:
        return False
    return True
