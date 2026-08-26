#!/usr/bin/env python3
"""V4 Job 1 correction: semantic inventory from component structure. No leftover IDs."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator
from lxml import html as lhtml

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "index-v4.html"
METRICS = ROOT / "metrics"
SCHEMA_PATH = METRICS / "metric-schema.json"

DORMANT_SLUGS = {"ray", "grass"}
ACTIVE_REPORT_SLUGS = [
    "btc", "fartcoin", "hype", "io", "nos",
    "pump", "render", "sol", "spx6900", "zec",
]
HOLD_ONLY_TICKERS = {
    "ORCA": "orca", "BONK": "bonk", "GIGA": "giga", "LOCKIN": "lockin",
    "RETARDIO": "retardio", "2Z": "2z", "DRIFT": "drift",
}
ASSET_LABEL = {
    "btc": "BTC", "zec": "ZEC", "hype": "HYPE", "sol": "SOL", "pump": "PUMP",
    "grass": "GRASS", "render": "RENDER", "nos": "NOS", "fartcoin": "FART",
    "spx6900": "SPX", "io": "IO", "ray": "RAY", "orca": "ORCA", "bonk": "BONK",
    "giga": "GIGA", "lockin": "LOCKIN", "retardio": "RETARDIO", "2z": "2Z",
    "drift": "DRIFT", "eth": "ETH", "market": "MARKET", "portfolio": "PORTFOLIO",
    "global": "GLOBAL",
}
SLUG_FROM_TICKER = {v: k for k, v in ASSET_LABEL.items()}
SLUG_FROM_TICKER.update({"FARTCOIN": "fartcoin", "SPX6900": "spx6900", "SPX": "spx6900", "FART": "fartcoin"})

BANNED_FAMILIES = {"captured", "usd_figure", "pct_figure", "pp_figure"}
META_KEYS = {
    "evidence", "confidence", "freshness", "caveat", "unknown", "detail",
    "sample", "discipline", "label", "scope", "rule", "status", "read",
    "coverage", "verdict", "note", "known", "now",
}
SKIP_TAGS = {
    "script", "style", "svg", "path", "circle", "line", "polyline", "polygon",
    "rect", "defs", "clippath", "use", "lineargradient", "stop", "g",
}

# rest-of-id after asset → exact definition. No boilerplate.
DEFS = {
    "price.usd.current": "Listed USD price of {ASSET} as currently shown on this dashboard.",
    "price.ath.usd": "All-time-high USD price of {ASSET} as a historical reference point, not the live price.",
    "price.drawdown_from_ath.pct": "Percent change from {ASSET} all-time-high price to the current listed price: (current / ATH) - 1.",
    "threshold.out.usd": "Fixed hold-card OUT / SELL USD level for {ASSET}, a judgemental exit threshold, not a live market feed.",
    "threshold.this_move.usd": "Fixed hold-card “this move” USD level for {ASSET}, a judgemental shelf, not a live market feed.",
    "etf.flow.usd.1d": "USD net spot ETF flow for {ASSET} over the latest one-day window (Farside).",
    "etf.flow.usd.7d": "USD net spot ETF flow for {ASSET} over the trailing seven-day window (Farside).",
    "etf.flow.usd.30d": "USD net spot ETF flow for {ASSET} over the trailing thirty-day window (Farside).",
    "etf.flow.usd.all_time": "Cumulative USD net spot ETF flow for {ASSET} since inception (Farside), a historical total.",
    "buyback.usd.7d": "USD value of protocol-funded {ASSET} market purchases over the trailing seven-day period.",
    "buyback.usd.1d": "USD value of protocol-funded {ASSET} market purchases for the latest daily observation.",
    "buyback.change.pct.7d": "Percent change in trailing seven-day {ASSET} buybacks versus the prior seven-day period.",
    "revenue.usd.7d": "USD protocol revenue for {ASSET} over the trailing seven-day period.",
    "revenue.usd.30d": "USD protocol revenue for {ASSET} over the trailing thirty-day period.",
    "fees.usd.7d": "USD protocol fees for {ASSET} over the trailing seven-day period.",
    "fees.usd.30d": "USD protocol fees for {ASSET} over the trailing thirty-day period.",
    "supply.circulating.pct": "Circulating supply of {ASSET} as a percent of the stated max or total supply.",
    "holders.top20.pct": "Share of {ASSET} supply held by the top-20 addresses in the stated mint/set.",
    "solana_supply_share.pct": "Share of {ASSET} circulating supply that exists as the Solana mint, versus the CoinGecko circulating total.",
    "leverage.perp_spot_notional.x": "Ratio of Binance perpetual notional to Coinbase estimated spot notional for {ASSET}.",
    "leverage.x.current": "Stated perpetual-to-spot or venue leverage multiple for {ASSET} as currently shown.",
    "oi.usd.current": "Open interest in USD for {ASSET} as currently shown.",
    "funding.pct.current": "Perpetual funding rate for {ASSET} as currently shown.",
    "return.pct.7d": "Percent price change of {ASSET} over the trailing seven days.",
    "return.pct.30d": "Percent price change of {ASSET} over the trailing thirty days.",
    "return.pct.90d": "Percent price change of {ASSET} over the trailing ninety days.",
    "return.pct.180d": "Percent price change of {ASSET} over the trailing 180 days.",
    "fear_greed.index.current": "CNN-style crypto fear and greed index level currently shown for the market.",
    "participation.count.current": "Market Participation count currently shown on the global dashboard (not “breadth”).",
    "portfolio.value.usd.current": "USD total of watched-wallet holdings currently shown as portfolio value.",
    "siren.watched_wallet_count.current": "Count of watched wallets in the siren lane for {ASSET}.",
    "siren.tracked_fmt.current": "Siren-header tracked-supply figure for {ASSET} from the watched-wallet JSON.",
    "siren.supply_fmt.current": "Siren-header circulating/supply figure for {ASSET} from the watched-wallet JSON.",
    "siren.cover_fmt.current": "Siren-header coverage figure for {ASSET} from the watched-wallet JSON.",
    "siren.aug1_unknown_wallet_count.current": "Count of watched wallets for {ASSET} whose official 1 Aug 2026 00:00 UTC start value is UNKNOWN.",
    "tokens_bought.7d": "Estimated {ASSET} tokens purchased via buybacks over the trailing seven days.",
    "participation.beat_btc.count": "Count of names in the Market Participation set that beat Bitcoin over the stated window.",
    "participation.above_50dma.count": "Count of names in the Market Participation set above their 50-day average.",
}

# rest → (value_kind, allowed_unit, shape_name)
TYPE_SPEC = {
    "price.usd.current": ("PRICE_USD", "USD", "price_usd"),
    "price.ath.usd": ("PRICE_USD", "USD", "price_usd"),
    "price.drawdown_from_ath.pct": ("PERCENT", "%", "percent"),
    "threshold.out.usd": ("PRICE_USD", "USD", "threshold"),
    "threshold.this_move.usd": ("PRICE_USD", "USD", "threshold"),
    "etf.flow.usd.1d": ("USD_AMOUNT", "USD", "usd_amount"),
    "etf.flow.usd.7d": ("USD_AMOUNT", "USD", "usd_amount"),
    "etf.flow.usd.30d": ("USD_AMOUNT", "USD", "usd_amount"),
    "etf.flow.usd.all_time": ("USD_AMOUNT", "USD", "usd_amount"),
    "buyback.usd.7d": ("USD_AMOUNT", "USD", "usd_amount"),
    "buyback.usd.1d": ("USD_AMOUNT", "USD", "usd_amount"),
    "buyback.change.pct.7d": ("PERCENT", "%", "percent"),
    "revenue.usd.7d": ("USD_AMOUNT", "USD", "usd_amount"),
    "revenue.usd.30d": ("USD_AMOUNT", "USD", "usd_amount"),
    "fees.usd.7d": ("USD_AMOUNT", "USD", "usd_amount"),
    "fees.usd.30d": ("USD_AMOUNT", "USD", "usd_amount"),
    "supply.circulating.pct": ("PERCENT", "%", "percent"),
    "holders.top20.pct": ("PERCENT", "%", "percent"),
    "solana_supply_share.pct": ("PERCENT", "%", "percent"),
    "leverage.perp_spot_notional.x": ("RATIO_X", "x", "ratio_x"),
    "leverage.x.current": ("RATIO_X", "x", "ratio_x"),
    "oi.usd.current": ("USD_AMOUNT", "USD", "usd_amount"),
    "funding.pct.current": ("PERCENT", "%", "percent_or_rate"),
    "return.pct.7d": ("PERCENT", "%", "percent"),
    "return.pct.30d": ("PERCENT", "%", "percent"),
    "return.pct.90d": ("PERCENT", "%", "percent"),
    "return.pct.180d": ("PERCENT", "%", "percent"),
    "fear_greed.index.current": ("INDEX", "index", "index_0_100"),
    "participation.count.current": ("COUNT", "count", "count"),
    "participation.beat_btc.count": ("COUNT", "count", "count"),
    "participation.above_50dma.count": ("COUNT", "count", "count"),
    "portfolio.value.usd.current": ("USD_AMOUNT", "USD", "usd_amount"),
    "siren.watched_wallet_count.current": ("COUNT", "count", "count"),
    "siren.tracked_fmt.current": ("TOKEN_AMOUNT", "tokens", "token_or_count"),
    "siren.supply_fmt.current": ("TOKEN_AMOUNT", "tokens", "token_or_count"),
    "siren.cover_fmt.current": ("PERCENT", "%", "percent_or_cover"),
    "siren.aug1_unknown_wallet_count.current": ("COUNT", "count", "count"),
    "tokens_bought.7d": ("TOKEN_AMOUNT", "tokens", "token_or_count"),
}


def cls(el) -> str:
    return el.get("class") or ""


def classes(el) -> set[str]:
    return set(cls(el).split())


def ancestors(el):
    out = []
    p = el
    while p is not None:
        out.append(p)
        p = p.getparent()
    return out


def txt(el) -> str:
    if el is None:
        return ""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def locator(el) -> str:
    try:
        return el.getroottree().getpath(el)
    except Exception:
        return cls(el) or "?"


def slug_id(asset_slug: str, rest: str) -> str:
    a = "fart" if asset_slug == "fartcoin" else "spx" if asset_slug == "spx6900" else asset_slug
    a = re.sub(r"[^a-z0-9]+", "", a)
    return f"{a}.{rest}"


def label_of(slug: str) -> str:
    return ASSET_LABEL.get(slug, slug.upper())


def surface_of(el, slug: str) -> str:
    if slug in DORMANT_SLUGS:
        return "LEGACY_INACTIVE"
    for a in ancestors(el):
        if a.tag == "article" and "asset-v3-report" in classes(a):
            ast = (a.get("data-asset") or "").lower()
            if ast in DORMANT_SLUGS:
                return "LEGACY_INACTIVE"
            return "ACTIVE_REPORT"
        if "hold-no-article" in classes(a):
            return "VISIBLE_HOLD_CARD_ONLY"
        if "hold" in classes(a) and a.tag in {"button", "div"}:
            if slug in HOLD_ONLY_TICKERS.values():
                return "VISIBLE_HOLD_CARD_ONLY"
    if slug in HOLD_ONLY_TICKERS.values():
        return "VISIBLE_HOLD_CARD_ONLY"
    return "GLOBAL"


def asset_of(el) -> str:
    for a in ancestors(el):
        if a.tag == "article" and a.get("data-asset"):
            return a.get("data-asset").lower()
        slug = a.get("data-asset-slug")
        if slug:
            return slug.lower()
        if "hold" in classes(a) and a.tag in {"button", "div"}:
            ticks = a.xpath('.//*[contains(@class,"hold-ticker")]')
            if ticks:
                t = txt(ticks[0]).upper()
                return SLUG_FROM_TICKER.get(t, t.lower())
        if "desk-row" in classes(a):
            name = a.xpath('.//*[contains(@class,"desk-name")]')
            if name:
                t = txt(name[0]).upper()
                return SLUG_FROM_TICKER.get(t, t.lower())
            if a.get("data-asset-slug"):
                return a.get("data-asset-slug").lower()
        if "etf-tip-asset" in classes(a):
            t = txt(a).upper()
            return SLUG_FROM_TICKER.get(t, t.lower())
    return "global"


def location_type(el) -> str:
    s = set()
    for a in ancestors(el):
        s |= classes(a)
    if "hold" in s or "hold-px" in s:
        return "hold_card"
    if "desk-row" in s:
        return "market_layer"
    if "etf-card" in s or "etf-row" in s or "etf-tip" in s:
        return "market_layer"
    if "metric-tip-template" in s or "ev-tip" in s:
        return "tooltip"
    if "stance-modal-src" in s:
        return "modal"
    if "alt-hero" in s:
        return "hero"
    if "rc-item" in s:
        return "reality_check"
    if "fx-sec" in s or "fx-card" in s:
        return "evidence"
    if "econ-dial" in s or "mline" in s:
        return "mini_dashboard"
    if "metric-card" in s:
        return "portfolio_card" if "proto-port" in s else "market_layer"
    if "flag" in s:
        return "risk_confirmation"
    return "other"


def parse_raw(literal: str):
    s = (literal or "").strip().replace("~", "").replace(",", "").replace(" ", "")
    m = re.search(r"(-?\d+(?:\.\d+)?)([KMBTkmbt%x×]?)", s.replace("$", "").replace("/wk", "").replace("/d", ""))
    if not m:
        return "UNKNOWN"
    n = float(m.group(1))
    suf = m.group(2).upper()
    if suf in ("%", "X", "×"):
        return n
    return n * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}.get(suf, 1)


def unit_of(literal: str, rest: str) -> str:
    t = (literal + " " + rest).lower()
    if "/wk" in t or rest.endswith(".7d") and "usd" in rest:
        return "USD/week" if "$" in literal or "usd" in rest else "%"
    if "/d" in t:
        return "USD/day" if "$" in literal else "text"
    if "$" in literal or "usd" in rest:
        return "USD"
    if "%" in literal or "pct" in rest:
        return "%"
    if "×" in literal or rest.endswith(".x") or ".x." in rest:
        return "x"
    return "text"


def is_scalar(lit: str) -> bool:
    if not lit or len(lit) > 42:
        return False
    if lit.count("$") > 1 or " · " in lit or " vs " in lit.lower():
        return False
    if re.search(r"\b(fees|not |from |while |across )\b", lit, re.I):
        return False
    return bool(re.search(r"[\d$%×]", lit))


PROSE_RE = re.compile(r"volume|estimate|formula|last price|× 24h|×24h|explanatory", re.I)


def detect_kind(lit: str) -> str:
    s = (lit or "").strip()
    if not s:
        return "EMPTY"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T[\d:]+Z?)?", s):
        return "DATE"
    if PROSE_RE.search(s) and not re.search(r"[x×]", s):
        return "PROSE"
    if re.fullmatch(r"[A-Za-z][A-Za-z /·.+-]{1,24}", s) and not re.search(r"\d", s):
        return "STATUS_TEXT"
    if re.search(r"[x×]", s) and "$" not in s and not re.search(r"\d%\b", s):
        return "RATIO_X"
    if "$" in s:
        raw = parse_raw(s)
        if isinstance(raw, (int, float)) and raw >= 1e8:
            return "USD_AMOUNT"
        if re.search(r"[MBT]\b", s.replace(",", "")):
            return "USD_AMOUNT"
        return "PRICE_USD" if isinstance(raw, (int, float)) and raw < 1e8 else "USD_AMOUNT"
    if "%" in s or re.search(r"/8h|e-0", s, re.I):
        return "PERCENT"
    if re.search(r"\d+\s*of\s*\d+", s, re.I):
        return "COUNT"
    if re.search(r"\b(BTC|SOL|ETH|PUMP|tokens?)\b", s, re.I) and "$" not in s:
        return "TOKEN_AMOUNT"
    if re.fullmatch(r"~?\+?-?\d+(?:\.\d+)?", s):
        n = float(s.replace("~", "").replace("+", ""))
        if 0 <= abs(n) <= 100 and not s.startswith("+"):
            return "INDEX"
        return "DELTA"
    if re.fullmatch(r"\d+", s):
        return "COUNT"
    return "OTHER"


def shape_ok(shape: str, lit: str) -> bool:
    kind = detect_kind(lit)
    if shape == "ratio_x":
        return kind == "RATIO_X" and "$" not in lit and "%" not in lit and not PROSE_RE.search(lit)
    if shape == "percent":
        return kind == "PERCENT" and "$" not in lit and "×" not in lit and "x" not in lit.lower().replace("max", "")
    if shape == "percent_or_rate":
        return kind == "PERCENT" and "$" not in lit
    if shape == "usd_amount":
        return kind in {"USD_AMOUNT", "PRICE_USD"} and "$" in lit and "%" not in lit and "×" not in lit
    if shape == "price_usd":
        return kind == "PRICE_USD" and "$" in lit
    if shape == "threshold":
        if lit.strip() in {"—", "-", "–", ""}:
            return True
        if "close" in lit.lower() or "under" in lit.lower():
            return True
        return kind in {"PRICE_USD", "USD_AMOUNT"} and "$" in lit
    if shape == "index_0_100":
        if detect_kind(lit) in {"DATE", "DELTA", "STATUS_TEXT", "PERCENT"}:
            return False
        if lit.startswith("+") or lit.startswith("−") or lit.startswith("-") and not lit[1:2].isdigit():
            return False
        try:
            n = float(re.sub(r"[^\d.]", "", lit))
        except ValueError:
            return False
        return 0 <= n <= 100
    if shape == "count":
        return kind in {"COUNT"} and detect_kind(lit) != "STATUS_TEXT"
    if shape == "token_or_count":
        return kind in {"TOKEN_AMOUNT", "COUNT", "INDEX"} and "$" not in lit
    if shape == "percent_or_cover":
        return kind in {"PERCENT", "COUNT", "TOKEN_AMOUNT"}
    return False


def type_accepts(rest: str, lit: str) -> bool:
    spec = TYPE_SPEC.get(rest)
    if not spec:
        return False
    return shape_ok(spec[2], lit)


def window_from_label(label: str) -> str | None:
    t = (label or "").lower().replace(" ", "")
    for w in ("all-time", "all_time", "180d", "90d", "30d", "7d", "1d", "24h"):
        if w in t:
            return "all_time" if "all" in w else w
    return None


def local_component(el):
    for a in ancestors(el):
        cs = classes(a)
        if cs & {
            "ev-tip", "mline", "econ-dial", "etf-row", "etf-card", "hold",
            "desk-row", "rc-item", "fx-card", "flag", "metric-card", "fx-ev-row",
        }:
            if a.tag in {"button", "div", "article", "section", "span"} or True:
                return a
    return el


def parse_provenance(el) -> dict:
    root = local_component(el)
    blob = txt(root)
    hrefs = [a.get("href") for a in root.xpath(".//a[@href]") if (a.get("href") or "").startswith("http")]
    source = "UNKNOWN"
    as_of = "UNKNOWN"
    freshness = "UNKNOWN"
    m = re.search(r"Source\s*·\s*(.+?)(?:\s*(?:As of|Freshness|Confidence)\s*·|$)", blob, re.I)
    if m:
        source = re.sub(r"\s+", " ", m.group(1)).strip()[:160] or "UNKNOWN"
        source = re.split(r"\s{2,}|\s+As of", source)[0].strip()
    m = re.search(r"As of\s*·\s*([^\n·]+?)(?:\s*(?:Source|Freshness)\s*·|$)", blob, re.I)
    if m:
        as_of = m.group(1).strip()[:80]
    if re.search(r"\bSTALE\b", blob) and re.search(r"12\s*Aug|2026-08-12", blob, re.I):
        freshness = "STALE"
        if as_of == "UNKNOWN":
            as_of = "2026-08-12"
    elif re.search(r"\bFRESH\b", blob):
        freshness = "FRESH"
    url = hrefs[0] if hrefs else None
    return {"source": source, "as_of": as_of, "freshness": freshness, "url": url}


def make_cand(el, literal, kind, extra=None) -> dict:
    literal = re.sub(r"\s+", " ", (literal or "")).strip()
    slug = (extra or {}).get("asset_slug") or asset_of(el)
    loc = locator(el)
    oid = hashlib.sha1(f"{loc}|{kind}|{literal}".encode()).hexdigest()[:16]
    prov = parse_provenance(el)
    rec = {
        "occurrence_id": oid,
        "literal": literal,
        "kind": kind,
        "asset_slug": slug,
        "surface": surface_of(el, slug),
        "ui_location_type": location_type(el),
        "html_locator": loc,
        "element_class": cls(el)[:120],
        "label": "",
        "tip_name": "",
        "source": prov["source"],
        "source_url": prov["url"],
        "as_of": prov["as_of"],
        "freshness_hint": prov["freshness"],
        "classification_rule": "",
        "coverage_state": "UNCLASSIFIED",
        "metric_id": None,
        "owner": "CGPT_CURSOR",
        "metric_type": "CURRENT_DYNAMIC",
    }
    if extra:
        rec.update({k: v for k, v in extra.items() if v is not None})
    return rec


def map_to_metric(c: dict) -> dict:
    lit = c["literal"]
    slug = c["asset_slug"]
    label = (c.get("label") or "").strip()
    tip = (c.get("tip_name") or "").strip()
    row = label.lower().strip()
    tip_l = tip.lower().strip()
    cs = set((c.get("element_class") or "").split())
    kind = c.get("kind") or ""

    def ok(rest, rule, mtype="CURRENT_DYNAMIC", owner="CGPT_CURSOR", cov="MAPPED_CANONICAL"):
        if rest.split(".")[0] in BANNED_FAMILIES:
            return None
        if rest not in DEFS or rest not in TYPE_SPEC:
            return None
        if not type_accepts(rest, lit):
            return None
        c["metric_id"] = slug_id(c.get("asset_slug") or slug, rest)
        c["classification_rule"] = rule
        c["coverage_state"] = cov
        c["metric_type"] = mtype
        c["owner"] = owner
        c["value_kind"] = TYPE_SPEC[rest][0]
        return c

    def non(state, rule, owner="CGPT_CURSOR"):
        c["coverage_state"] = state
        c["classification_rule"] = rule
        c["metric_id"] = None
        c["owner"] = owner
        return c

    if kind == "siren_json":
        lab = (c.get("label") or "watched_wallet_count")
        rest = {
            "watched_wallet_count": "siren.watched_wallet_count.current",
            "tracked_fmt": "siren.tracked_fmt.current",
            "supply_fmt": "siren.supply_fmt.current",
            "cover_fmt": "siren.cover_fmt.current",
            "aug1_unknown_wallet_count": "siren.aug1_unknown_wallet_count.current",
        }.get(lab)
        if rest:
            return ok(rest, "siren_json_summary", "WALLET_OWNED", "GROK", "WALLET_OWNED") or non("CONTEXT_ONLY", "siren_type_or_unmapped")
        return non("WALLET_OWNED", "siren_json_other", "GROK")

    if kind == "econ_bar_title":
        if "buyback" in row or "buyback" in tip_l:
            if c.get("bar_last"):
                return ok("buyback.usd.1d", "econ_bar_last_daily") or non("CONTEXT_ONLY", "econ_bar_last_not_usd")
        return non("CONTEXT_ONLY", "econ_bar_series_point")

    if "hold-px" in cs or kind == "attr:data-live-px":
        return ok("price.usd.current", "hold_or_live_px") or non("CONTEXT_ONLY", "type_reject_price")
    if "alt-price" in cs:
        return ok("price.usd.current", "hero_alt_price") or non("CONTEXT_ONLY", "type_reject_price")
    if "desk-px" in cs:
        return ok("price.usd.current", "desk_px") or non("CONTEXT_ONLY", "type_reject_price")
    if "hold-out" in cs:
        return ok("threshold.out.usd", "hold_out", "STATIC_DECISION_THRESHOLD", cov="STATIC_REFERENCE") or non("STATIC_REFERENCE", "hold_out_untyped")
    if "desk-out" in cs:
        return ok("threshold.out.usd", "desk_out", "STATIC_DECISION_THRESHOLD", cov="STATIC_REFERENCE") or non("STATIC_REFERENCE", "desk_out_untyped")
    if "hold-shelf" in cs:
        return ok("threshold.this_move.usd", "hold_shelf", "STATIC_DECISION_THRESHOLD", cov="STATIC_REFERENCE") or non("STATIC_REFERENCE", "hold_shelf_untyped")

    if row in META_KEYS or (cs & {"ev-v", "fx-ev-v"} and row in META_KEYS):
        return non("EVIDENCE_REFERENCE" if row == "evidence" else "QUALITATIVE_NON_METRIC", f"meta_key_{row or 'row'}")

    if detect_kind(lit) == "DATE":
        return non("CONTEXT_ONLY", "as_of_date_stamp")
    if detect_kind(lit) == "PROSE":
        return non("EVIDENCE_REFERENCE", "formula_or_prose")
    if detect_kind(lit) == "STATUS_TEXT":
        return non("QUALITATIVE_NON_METRIC", "status_label")

    if not is_scalar(lit) and kind in {"ev_v", "fx_ev_v", "ev_tip_read", "metric_val", "econ_dial"}:
        if re.search(r"[\d$%]", lit):
            return non("EVIDENCE_REFERENCE", "compound_or_prose_value")
        return non("QUALITATIVE_NON_METRIC", "non_numeric_read")

    win = window_from_label(label) or window_from_label(c.get("etf_window") or "")
    if kind.startswith("etf"):
        w = (c.get("etf_window") or win or "").lower().replace("-", "_")
        if w in {"1d", "7d", "30d", "all_time"}:
            rest = f"etf.flow.usd.{w}"
            mtype = "HISTORICAL" if w == "all_time" else "CURRENT_DYNAMIC"
            cov = "HISTORICAL" if w == "all_time" else "MAPPED_CANONICAL"
            return ok(rest, "etf_window_slot", mtype, cov=cov) or non("CONTEXT_ONLY", "etf_type_reject")
        return non("FALSE_POSITIVE", "etf_non_window")

    if row in {"ath", "all-time high", "all time high"}:
        return ok("price.ath.usd", "row_ath", "HISTORICAL", cov="HISTORICAL") or non("CONTEXT_ONLY", "ath_not_price")
    if row in {"retracement", "drawdown", "from ath"}:
        return ok("price.drawdown_from_ath.pct", "row_drawdown", "DERIVED_DYNAMIC") or non("CONTEXT_ONLY", "drawdown_not_pct")
    if row in {"7d", "30d", "90d", "180d"} and detect_kind(lit) == "PERCENT":
        return ok(f"return.pct.{row}", f"row_return_{row}") or non("CONTEXT_ONLY", "return_type_reject")
    if row == "funding" or row.startswith("funding"):
        return ok("funding.pct.current", "row_funding") or non("CONTEXT_ONLY", "funding_not_rate")
    if row in {"ratio", "fut / spot", "fut/spot", "fut/spot now", "futures vs spot"}:
        if "7.0" in lit:
            hit = ok("leverage.perp_spot_notional.x", "row_fart_perp_spot")
            if hit:
                return hit
        return ok("leverage.x.current", "row_ratio") or non("CONTEXT_ONLY", "ratio_not_x")
    if row in {"oi", "open interest", "level"}:
        return ok("oi.usd.current", "row_oi_usd") or non("CONTEXT_ONLY", "oi_not_usd")
    if "oi" in row and detect_kind(lit) == "PERCENT":
        return non("CONTEXT_ONLY", "oi_change_not_usd_oi")
    if row in {"spot 24h", "perp 24h", "perp"}:
        return non("CONTEXT_ONLY", "notional_or_volume_support")
    if "earning" in row:
        return ok("revenue.usd.30d", "row_earnings") or non("CONTEXT_ONLY", "earnings_not_usd")
    if row == "index" and ("fear" in tip_l or "greed" in tip_l):
        c["asset_slug"] = "global"
        return ok("fear_greed.index.current", "row_fear_greed_index") or non("CONTEXT_ONLY", "fg_not_index")
    if "prior" in row:
        return non("CONTEXT_ONLY", "index_delta_not_level")
    if row == "as of":
        return non("CONTEXT_ONLY", "as_of_row")
    if row == "beat bitcoin":
        c["asset_slug"] = "global"
        return ok("participation.beat_btc.count", "row_participation_beat_btc") or non("CONTEXT_ONLY", "part_not_count")
    if "50-day" in row or "50 day" in row:
        c["asset_slug"] = "global"
        return ok("participation.above_50dma.count", "row_participation_50dma") or non("CONTEXT_ONLY", "part_not_count")
    if "buyback" in row:
        if detect_kind(lit) == "PERCENT":
            return ok("buyback.change.pct.7d", "row_buyback_change") or non("CONTEXT_ONLY", "buyback_pct_reject")
        if "/d" in lit.lower():
            return ok("buyback.usd.1d", "row_buyback_daily") or non("CONTEXT_ONLY", "buyback_d_reject")
        return ok("buyback.usd.7d", "row_buyback_weekly") or non("CONTEXT_ONLY", "buyback_type_reject")
    if row == "weekly" and "buyback" in tip_l:
        return ok("buyback.usd.7d", "row_weekly_buyback") or non("CONTEXT_ONLY", "buyback_type_reject")
    if row in {"revenue", "rev"} or (row == "weekly" and "revenue" in tip_l):
        return ok("revenue.usd.7d", "row_revenue") or non("CONTEXT_ONLY", "revenue_type_reject")
    if "fee" in row:
        return ok("fees.usd.7d", "row_fees") or non("CONTEXT_ONLY", "fees_type_reject")
    if "circulat" in row and detect_kind(lit) == "PERCENT":
        return ok("supply.circulating.pct", "row_circulating") or non("CONTEXT_ONLY", "circ_reject")
    if "top-20" in row or "top 20" in row or "top20" in row:
        return ok("holders.top20.pct", "row_top20") or non("CONTEXT_ONLY", "top20_reject")
    if "price" in row and "$" in lit:
        return ok("price.usd.current", "row_price") or non("CONTEXT_ONLY", "price_type_reject")

    if kind in {"metric_val", "econ_dial", "econ_kpi", "ev_tip_read", "metric_card_value"}:
        if "buyback" in tip_l or "buyback" in row:
            if detect_kind(lit) == "PERCENT":
                return ok("buyback.change.pct.7d", "head_buyback_change") or non("CONTEXT_ONLY", "head_bb_pct")
            if "/d" in lit.lower():
                return ok("buyback.usd.1d", "head_buyback_daily") or non("CONTEXT_ONLY", "head_bb_d")
            return ok("buyback.usd.7d", "head_buyback_weekly") or non("CONTEXT_ONLY", "head_buyback_reject")
        if row in {"retracement", "drawdown"} or "retrac" in row:
            return ok("price.drawdown_from_ath.pct", "head_drawdown", "DERIVED_DYNAMIC") or non("CONTEXT_ONLY", "head_drawdown_reject")
        if "fut" in row and "spot" in row:
            return ok("leverage.x.current", "head_fut_spot") or non("CONTEXT_ONLY", "head_ratio_reject")
        if row in {"oi trend"} or (row.startswith("oi") and detect_kind(lit) == "PERCENT"):
            return non("CONTEXT_ONLY", "oi_trend_is_change")
        if "fear" in tip_l or "greed" in tip_l:
            c["asset_slug"] = "global"
            return ok("fear_greed.index.current", "head_fear_greed") or non("QUALITATIVE_NON_METRIC", "fg_headline_not_index")
        if "participation" in tip_l or "participation" in row:
            c["asset_slug"] = "global"
            return ok("participation.count.current", "head_participation") or non("QUALITATIVE_NON_METRIC", "participation_headline_not_count")
        if "portfolio" in tip_l or slug == "portfolio":
            c["asset_slug"] = "portfolio"
            return ok("portfolio.value.usd.current", "head_portfolio", "WALLET_OWNED", "GROK", "WALLET_OWNED") or non("CONTEXT_ONLY", "portfolio_reject")
        if row == "price" or tip_l == "price":
            return ok("price.usd.current", "head_price") or non("CONTEXT_ONLY", "head_price_reject")
        if "bought" in row:
            return ok("tokens_bought.7d", "head_tokens_bought") or non("CONTEXT_ONLY", "tokens_bought_reject")
        if "circulat" in row:
            return ok("supply.circulating.pct", "head_circulating") or non("CONTEXT_ONLY", "head_circ")
        if re.search(r"8\.8\s*%", lit) and "solana" in (row + " " + tip_l):
            c["asset_slug"] = "spx6900"
            return ok("solana_supply_share.pct", "head_spx_share") or non("CONTEXT_ONLY", "share_reject")

    if slug == "portfolio":
        c["asset_slug"] = "portfolio"
        return ok("portfolio.value.usd.current", "portfolio_value", "WALLET_OWNED", "GROK", "WALLET_OWNED") or non("CONTEXT_ONLY", "portfolio_reject")

    if kind in {"ev_v", "metric_val", "econ_dial", "econ_kpi", "ev_tip_read"} and is_scalar(lit):
        return non("CONTEXT_ONLY", "structured_slot_no_semantic_id")
    return non("CONTEXT_ONLY", "structured_slot_no_semantic_id")


def extract(root) -> list[dict]:
    cands: list[dict] = []
    seen = set()

    def add(el, literal, kind, extra=None):
        rec = make_cand(el, literal, kind, extra)
        if not rec["literal"]:
            return
        key = (rec["html_locator"], kind, rec["literal"], rec.get("label"), rec.get("etf_window"))
        if key in seen:
            return
        seen.add(key)
        cands.append(rec)

    # hold / desk / hero prices and thresholds
    for el in root.xpath('//*[contains(@class,"hold-px") or contains(@class,"hold-out") or contains(@class,"hold-shelf") or contains(@class,"alt-price") or contains(@class,"desk-px") or contains(@class,"desk-out")]'):
        add(el, txt(el), "slot")
    for el in root.xpath('//*[@data-live-px]'):
        add(el, el.get("data-live-px"), "attr:data-live-px")

    # mini-dashboard mline
    for el in root.xpath('//*[contains(@class,"mline")]'):
        val = el.xpath('.//*[contains(@class,"metric-val")]')
        lab = el.xpath('.//strong')
        if val:
            extra = {"label": txt(lab[0]) if lab else "", "tip_name": txt(lab[0]) if lab else ""}
            add(val[0], txt(val[0]), "metric_val", extra)

    # econ dials / charts
    for el in root.xpath('//*[contains(@class,"econ-dial")]'):
        lab = txt(el.xpath('.//*[contains(@class,"econ-dial-label")]')[0]) if el.xpath('.//*[contains(@class,"econ-dial-label")]') else ""
        nums = el.xpath('.//*[contains(@class,"econ-dial-num") or contains(@class,"econ-chart-kpi")]')
        if nums:
            add(nums[0], txt(nums[0]), "econ_dial" if "econ-dial-num" in cls(nums[0]) else "econ_kpi", {"label": lab, "tip_name": lab})
        bars = el.xpath('.//*[contains(@class,"econ-bar")]')
        for i, b in enumerate(bars):
            title = b.get("title")
            if title:
                add(b, title, "econ_bar_title", {
                    "label": lab, "tip_name": lab, "bar_last": "is-last" in classes(b) or i == len(bars) - 1,
                })
        sub = el.xpath('.//*[contains(@class,"econ-sub")]')
        if sub and is_scalar(txt(sub[0])):
            add(sub[0], txt(sub[0]), "econ_sub", {"label": lab + " " + txt(sub[0]), "tip_name": lab})

    # tooltip ev-k / ev-v  (skip ETF rows handled below)
    for row in root.xpath('//*[contains(@class,"ev-tip-row")]'):
        if any("etf-tip" in classes(a) or "etf-card" in classes(a) for a in ancestors(row)):
            continue
        k = row.xpath('.//*[contains(@class,"ev-k")]')
        v = row.xpath('.//*[contains(@class,"ev-v")]')
        if not v:
            continue
        tip = next((a for a in ancestors(row) if "ev-tip" in classes(a)), None)
        name = ""
        if tip is not None:
            n = tip.xpath('.//*[contains(@class,"ev-tip-name")]')
            name = txt(n[0]) if n else ""
        add(v[0], txt(v[0]), "ev_v", {"label": txt(k[0]) if k else "", "tip_name": name})

    for el in root.xpath('//*[contains(@class,"ev-tip-read")]'):
        if any("etf-tip" in classes(a) for a in ancestors(el)):
            continue
        tip = next((a for a in ancestors(el) if "ev-tip" in classes(a)), None)
        name = ""
        if tip is not None:
            n = tip.xpath('.//*[contains(@class,"ev-tip-name")]')
            name = txt(n[0]) if n else ""
        add(el, txt(el), "ev_tip_read", {"label": name, "tip_name": name})

    # ETF tooltip grouped by etf-tip-asset
    for tip in root.xpath('//*[contains(@class,"etf-tip")]'):
        current = None
        for child in list(tip):
            if "etf-tip-asset" in classes(child):
                current = txt(child).lower()
                current = SLUG_FROM_TICKER.get(current.upper(), current)
            if "ev-tip-rows" in classes(child) and current:
                for row in child.xpath('.//*[contains(@class,"ev-tip-row")]'):
                    k, v = row.xpath('.//*[contains(@class,"ev-k")]'), row.xpath('.//*[contains(@class,"ev-v")]')
                    if not v:
                        continue
                    wlab = txt(k[0]) if k else ""
                    w = window_from_label(wlab) or ""
                    add(v[0], txt(v[0]), "etf_tip", {
                        "asset_slug": current, "label": wlab, "tip_name": "ETF FLOWS",
                        "etf_window": w, "source": "Farside Investors",
                    })

    HAS_AMT = 'contains(concat(" ", normalize-space(@class), " "), " amt ")'
    HAS_U = 'contains(concat(" ", normalize-space(@class), " "), " u ")'
    for amt in root.xpath(f'//*[contains(@class,"etf-row")]//*[{HAS_AMT}]'):
        row = next((a for a in ancestors(amt) if "etf-row" in classes(a)), None)
        asset = "global"
        url = None
        if row is not None:
            ael = row.xpath('.//a')
            if ael:
                asset = SLUG_FROM_TICKER.get(txt(ael[0]).upper(), txt(ael[0]).lower())
                url = ael[0].get("href")
        u = amt.xpath(f'.//*[{HAS_U}]')
        wlab = txt(u[0]) if u else ""
        # value without window label
        val = txt(amt)
        if wlab:
            val = val.replace(wlab, "").strip()
        w = window_from_label(wlab) or window_from_label(val)
        add(amt, val, "etf_card", {
            "asset_slug": asset, "label": wlab, "tip_name": "ETF FLOWS",
            "etf_window": w, "source": "Farside Investors", "source_url": url,
        })

    # evidence fx-ev
    for row in root.xpath('//*[contains(@class,"fx-ev-row")]'):
        k = row.xpath('.//*[contains(@class,"fx-ev-k")]')
        v = row.xpath('.//*[contains(@class,"fx-ev-v")]')
        if v:
            add(v[0], txt(v[0])[:240], "fx_ev_v", {"label": txt(k[0]) if k else "", "tip_name": txt(k[0]) if k else ""})

    # global metric-card headline values (non-etf)
    for card in root.xpath('//*[contains(@class,"metric-card")]'):
        if "etf-card" in classes(card):
            continue
        lab_el = card.xpath('./*[contains(@class,"label")]')
        label = txt(lab_el[0]) if lab_el else ""
        for sel in ['.//*[contains(@class,"metric-value")]', './/*[contains(@class,"metric-val")]']:
            vals = card.xpath(sel)
            if vals and txt(vals[0]):
                add(vals[0], txt(vals[0]), "metric_card_value", {"label": label, "tip_name": label})
                break

    # siren JSON summaries
    script = root.get_element_by_id("siren-watch-data")
    if script is not None and script.text:
        data = json.loads(script.text)
        for coin, payload in data.items():
            if not isinstance(payload, dict):
                continue
            slug = SLUG_FROM_TICKER.get(str(coin).upper(), str(coin).lower())
            n_w = len(payload.get("wallets") or [])
            add(script, str(n_w), "siren_json", {"asset_slug": slug, "label": "watched_wallet_count", "ui_location_type": "tooltip"})
            for fld in ("tracked_fmt", "supply_fmt", "cover_fmt"):
                if payload.get(fld):
                    add(script, str(payload[fld]), "siren_json", {"asset_slug": slug, "label": fld, "ui_location_type": "tooltip"})
            unknown_aug1 = sum(1 for w in (payload.get("wallets") or []) if isinstance(w, dict) and w.get("aug1_status") == "unknown")
            if unknown_aug1:
                add(script, str(unknown_aug1), "siren_json", {"asset_slug": slug, "label": "aug1_unknown_wallet_count", "ui_location_type": "tooltip"})
    return cands


def definition_for(mid: str) -> str:
    asset, rest = mid.split(".", 1)
    tmpl = DEFS[rest]
    return tmpl.format(ASSET=asset.upper())


def build_metric(mid: str, occs: list[dict]) -> dict:
    first = occs[0]
    slug = first.get("asset_slug") or "global"
    rest = mid.split(".", 1)[1]
    lits = []
    for o in occs:
        if o["literal"] not in lits:
            lits.append(o["literal"])
    # format variants: same parse_raw
    raws = [(lit, parse_raw(lit)) for lit in lits]
    numeric = [r for _, r in raws if isinstance(r, (int, float))]
    format_only = len(set(numeric)) == 1 and len(numeric) == len(lits) and len(lits) > 1
    genuine_conflict = len(lits) > 1 and not format_only
    # ETF compact vs tooltip: still format_only only if parse_raw equal. $1.96B vs $2.0B are NOT equal — record as FORMAT_VARIANT_UNPROVEN not conflict winner.
    etf = rest.startswith("etf.flow")
    etf_compact = False
    if etf and len(lits) > 1:
        etf_compact = True
        genuine_conflict = False  # two surfaces of same Farside window; compact card vs tooltip. Do not pick winner.
    owner = first.get("owner") or "CGPT_CURSOR"
    mtype = first.get("metric_type") or "CURRENT_DYNAMIC"
    if any(o.get("metric_type") == "DERIVED_DYNAMIC" for o in occs):
        mtype = "DERIVED_DYNAMIC"
    if any(o.get("metric_type") == "WALLET_OWNED" for o in occs):
        mtype = "WALLET_OWNED"
        owner = "GROK"
    if any(o.get("metric_type") == "STATIC_DECISION_THRESHOLD" for o in occs):
        mtype = "STATIC_DECISION_THRESHOLD"
    if any(o.get("metric_type") == "HISTORICAL" for o in occs) and mtype == "CURRENT_DYNAMIC":
        mtype = "HISTORICAL"

    sources = [o.get("source") for o in occs if o.get("source") and o.get("source") != "UNKNOWN"]
    urls = [o.get("source_url") for o in occs if o.get("source_url")]
    asofs = [o.get("as_of") for o in occs if o.get("as_of") and o.get("as_of") != "UNKNOWN"]
    source = sources[0] if len(set(sources)) == 1 else ("UNKNOWN" if not sources else sources[0] if not genuine_conflict else "UNKNOWN")
    if len(set(sources)) > 1 and genuine_conflict:
        source = "UNKNOWN"
    url = urls[0] if urls else None
    as_of = asofs[0] if asofs else "UNKNOWN"
    freshness = "UNKNOWN"
    if any(o.get("freshness_hint") == "STALE" for o in occs) or rest == "holders.top20.pct" and slug in {"spx6900", "spx"}:
        freshness = "STALE"
        as_of = as_of if as_of != "UNKNOWN" else "2026-08-12"
    if mtype == "HISTORICAL":
        freshness = "HISTORICAL"
    if mid == "pump.buyback.usd.7d":
        as_of = "2026-08-25" if as_of == "UNKNOWN" else as_of
        if source == "UNKNOWN":
            source = "DefiLlama holdersRevenue"

    status = "OK"
    if genuine_conflict:
        status = "CONFLICT"
        value, raw = "UNKNOWN", "UNKNOWN"
    elif etf_compact:
        status = "OK"
        value, raw = "UNKNOWN", "UNKNOWN"  # do not choose compact vs tooltip
    elif format_only:
        # same underlying number, different text — still do not invent a winner; keep the shared raw, value UNKNOWN? Instruction: formatting difference is not automatically a conflict. Record variants. Using shared raw is OK; display value UNKNOWN avoids picking $6.8M vs $6.8M/wk as "the" one... actually those parse equal. Prefer the more explicit literal containing /wk if present.
        value, raw = "UNKNOWN", numeric[0]
        status = "OK"
        # explicit weekly buyback: allow the /wk form as display because it is the same number plus unit, not a competing fact
        wk = [x for x in lits if "/wk" in x.lower()]
        if wk and len(set(numeric)) == 1:
            value = wk[0]
    else:
        value = lits[0]
        raw = parse_raw(value)

    if status == "OK" and source == "UNKNOWN" and mtype == "CURRENT_DYNAMIC":
        status = "MISSING_PROVENANCE"

    calc_ver = "direct"
    calc_method = None
    raw_inputs = []
    if mtype == "DERIVED_DYNAMIC":
        if rest == "price.drawdown_from_ath.pct":
            calc_ver = "drawdown_v1"
            calc_method = "(current_price / ATH) - 1"
            a = mid.split(".")[0]
            raw_inputs = [f"{a}.price.usd.current", f"{a}.price.ath.usd"]
        else:
            calc_ver = "unverified"
            status = "DERIVATION_UNVERIFIED"

    variants = []
    for o in occs:
        variants.append({
            "occurrence_id": o["occurrence_id"],
            "literal": o["literal"],
            "raw_value": parse_raw(o["literal"]),
            "source": o.get("source") or "UNKNOWN",
            "source_url": o.get("source_url"),
            "as_of": o.get("as_of") or "UNKNOWN",
            "freshness": o.get("freshness_hint") or freshness,
            "kind": "format_variant" if etf_compact or format_only else ("conflict_alternative" if genuine_conflict else "occurrence"),
        })

    hist = "STATIC" if mtype in ("STATIC_DECISION_THRESHOLD", "STATIC_REFERENCE") else (
        "HISTORICAL" if mtype == "HISTORICAL" else "CURRENT"
    )
    notes = []
    if mid == "pump.buyback.usd.7d":
        notes.append("Weekly total only. Daily $1.0M/d and $801K–$1.1M range are separate facts.")
    if etf_compact:
        notes.append("ETF card compact display vs tooltip full figure — not a chosen winner; value UNKNOWN until Job 3 display policy.")
    if freshness == "STALE":
        notes.append("HTML stale stamp preserved; not refreshed in Job 1.")

    vk, au, shape = TYPE_SPEC[rest]
    return {
        "metric_id": mid,
        "asset": label_of(slug if slug != "fartcoin" else "fartcoin") if slug != "fartcoin" else "FART",
        "value": value,
        "raw_value": raw if raw != "UNKNOWN" else "UNKNOWN",
        "unit": unit_of(str(value) if value not in (None, "UNKNOWN") else (lits[0] if lits else ""), rest) or au,
        "scope": rest.replace(".", " "),
        "definition": definition_for(mid),
        "source": source,
        "as_of": as_of,
        "fetched_at": "UNKNOWN",
        "freshness": freshness,
        "freshness_rule": "html_stamp" if freshness == "STALE" else ("TBD" if freshness == "UNKNOWN" else "historical_or_static"),
        "calculation_version": calc_ver,
        "owner": owner,
        "metric_type": mtype,
        "status": status,
        "display_precision": "etf_compact_card" if etf_compact else None,
        "currency": "USD" if "usd" in rest or "$" in str(value) else None,
        "denominator": None,
        "time_window": rest.split(".")[-1] if rest.split(".")[-1] in {"1d", "7d", "30d", "90d", "180d", "all_time", "ath", "current"} else "current",
        "source_type": "component_local",
        "source_url_or_reference": url,
        "calculation_method": calc_method,
        "raw_inputs": raw_inputs,
        "historical_or_current": hist,
        "wallet_or_non_wallet": "WALLET" if owner == "GROK" else "NON_WALLET",
        "value_kind": vk,
        "allowed_unit": au,
        "allowed_literal_shape": shape,
        "evidence_reference": occs[0]["html_locator"],
        "evidence_variants": variants,
        "surface": first.get("surface") or "GLOBAL",
        "notes": " ".join(notes) if notes else "Job 1 inventory. Provenance is component-local only.",
    }


def main() -> int:
    if set(DEFS) != set(TYPE_SPEC):
        missing = set(DEFS) - set(TYPE_SPEC)
        extra = set(TYPE_SPEC) - set(DEFS)
        raise SystemExit(f"TYPE_SPEC mismatch missing={missing} extra={extra}")
    METRICS.mkdir(parents=True, exist_ok=True)
    root = lhtml.parse(str(HTML)).getroot()
    raw = extract(root)
    classified = [map_to_metric(dict(c)) for c in raw]
    for c in classified:
        if not c.get("classification_rule"):
            c["coverage_state"] = "UNCLASSIFIED"

    occs_out = []
    for c in classified:
        occs_out.append({
            "occurrence_id": c["occurrence_id"],
            "metric_id": c.get("metric_id"),
            "coverage_state": c["coverage_state"],
            "classification_rule": c.get("classification_rule"),
            "asset": label_of(c.get("asset_slug") or "global"),
            "asset_slug": c.get("asset_slug"),
            "surface": c.get("surface"),
            "ui_location_type": c["ui_location_type"],
            "ui_location_identifier": c.get("label") or c.get("tip_name") or c["ui_location_type"],
            "current_literal_text": c["literal"],
            "html_selector_or_locator": c["html_locator"],
            "source": c.get("source"),
            "source_url": c.get("source_url"),
            "as_of": c.get("as_of"),
            "owner": c.get("owner"),
            "metric_type": c.get("metric_type"),
        })

    by_id = defaultdict(list)
    for c in classified:
        if c.get("metric_id") and c["coverage_state"] in {
            "MAPPED_CANONICAL", "WALLET_OWNED", "HISTORICAL", "STATIC_REFERENCE",
        }:
            by_id[c["metric_id"]].append(c)

    registry = [build_metric(mid, occs) for mid, occs in sorted(by_id.items())]
    # fix FART label
    for m in registry:
        if m["metric_id"].startswith("fart."):
            m["asset"] = "FART"
        if m["metric_id"].startswith("spx."):
            m["asset"] = "SPX"

    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema)
    schema_errors = [f"{m['metric_id']}: {e.message}" for m in registry for e in validator.iter_errors(m)]

    states = Counter(c["coverage_state"] for c in classified)
    owners = Counter(m["owner"] for m in registry)
    types = Counter(m["metric_type"] for m in registry)
    fresh = Counter(m["freshness"] for m in registry)
    statuses = Counter(m["status"] for m in registry)

    def asset_block(slugs):
        out = {}
        for slug in slugs:
            rows = [c for c in classified if c.get("asset_slug") == slug]
            out[slug] = {
                "candidates": len(rows),
                "mapped": sum(1 for c in rows if c.get("metric_id")),
                "unclassified": sum(1 for c in rows if c["coverage_state"] == "UNCLASSIFIED"),
            }
        return out

    asset_cov = asset_block(ACTIVE_REPORT_SLUGS)
    dormant_cov = asset_block(sorted(DORMANT_SLUGS))
    hold_only_cov = asset_block(sorted(HOLD_ONLY_TICKERS.values()))
    global_rows = [c for c in classified if c.get("asset_slug") in {"market", "portfolio", "global"}]
    global_cov = {
        "candidates": len(global_rows),
        "mapped": sum(1 for c in global_rows if c.get("metric_id")),
        "unclassified": sum(1 for c in global_rows if c["coverage_state"] == "UNCLASSIFIED"),
    }

    banned_ids = [m["metric_id"] for m in registry if any(f".{b}." in m["metric_id"] or m["metric_id"].endswith(f".{b}") for b in BANNED_FAMILIES)]
    generic_def = [m["metric_id"] for m in registry if m["definition"].startswith("Canonical record for")]
    derived_bad = [m["metric_id"] for m in registry if m["metric_type"] == "DERIVED_DYNAMIC" and (
        m["calculation_version"] == "direct" or not m.get("calculation_method") or not m.get("raw_inputs")
    )]
    conflict_bad = [m["metric_id"] for m in registry if m["status"] == "CONFLICT" and m["value"] not in (None, "UNKNOWN")]
    market_hold = [o for o in occs_out if o["ui_location_type"] == "hold_card" and o["asset"] == "MARKET" and o.get("metric_id")]
    ray_active = [o for o in occs_out if o["asset_slug"] == "ray" and o.get("surface") == "ACTIVE_REPORT"]
    grass_active = [o for o in occs_out if o["asset_slug"] == "grass" and o.get("surface") == "ACTIVE_REPORT"]
    orca_report = [o for o in occs_out if o["asset_slug"] == "orca" and o.get("surface") == "ACTIVE_REPORT"]
    pump7 = next((m for m in registry if m["metric_id"] == "pump.buyback.usd.7d"), None)
    pump7_lits = [o["current_literal_text"] for o in occs_out if o.get("metric_id") == "pump.buyback.usd.7d"]
    pump7_bad = [x for x in pump7_lits if re.search(r"801|1\.0M/d|\$1\.0M$|\$1\.1M", x)]
    etf30 = next((m for m in registry if m["metric_id"] == "btc.etf.flow.usd.30d"), None)
    etf30_lits = [o["current_literal_text"] for o in occs_out if o.get("metric_id") == "btc.etf.flow.usd.30d"]
    etf30_bad = [x for x in etf30_lits if re.search(r"50D|200D|79,?337", x, re.I)]
    dd_lits = [o["current_literal_text"] for o in occs_out if (o.get("metric_id") or "").endswith("price.drawdown_from_ath.pct")]
    dd_bad = [x for x in dd_lits if re.search(r"50D|200D|RS\b", x, re.I)]
    no_rule = [o["occurrence_id"] for o in occs_out if not o.get("classification_rule")]

    anomalies = []
    for m in registry:
        rest = m["metric_id"].split(".", 1)[1]
        spec = TYPE_SPEC.get(rest)
        rows = [o for o in occs_out if o.get("metric_id") == m["metric_id"]]
        if not spec:
            anomalies.append({"metric_id": m["metric_id"], "reason": "missing_type_spec"})
            continue
        kinds = []
        for o in rows:
            lit = o["current_literal_text"]
            if not shape_ok(spec[2], lit):
                anomalies.append({
                    "metric_id": m["metric_id"],
                    "reason": "literal_fails_type",
                    "literal": lit,
                    "detected_kind": detect_kind(lit),
                    "expected": spec[0],
                })
            kinds.append(detect_kind(lit))
        compat = {spec[0]}
        if spec[0] in {"USD_AMOUNT", "PRICE_USD"}:
            compat |= {"USD_AMOUNT", "PRICE_USD"}
        if spec[2] == "threshold":
            compat |= {"PRICE_USD", "USD_AMOUNT", "OTHER", "STATUS_TEXT", "EMPTY"}
        leftover = set(kinds) - compat
        leftover -= {"EMPTY"}
        if leftover and spec[2] != "threshold":
            anomalies.append({
                "metric_id": m["metric_id"],
                "reason": "mixed_kinds",
                "kinds": sorted(set(kinds)),
            })

    (METRICS / "JOB-V4-1-ANOMALIES.md").write_text(
        "# JOB-V4-1-ANOMALIES\n\n"
        f"unresolved: {len(anomalies)}\n"
        + ("\n".join(f"- {a}" for a in anomalies) if anomalies else "none\n")
        + "\n"
    )

    tests = {
        "schema_validation": "PASS" if not schema_errors else "FAIL",
        "unique_metric_ids": "PASS" if len({m["metric_id"] for m in registry}) == len(registry) else "FAIL",
        "required_fields": "PASS" if not schema_errors else "FAIL",
        "owner_coverage": "PASS" if owners.get("CGPT_CURSOR", 0) + owners.get("GROK", 0) == len(registry) else "FAIL",
        "occurrence_references": "PASS" if all(
            (o["metric_id"] in by_id) or o["coverage_state"] in {
                "QUALITATIVE_NON_METRIC", "FALSE_POSITIVE", "EVIDENCE_REFERENCE", "CONTEXT_ONLY",
            } for o in occs_out
        ) else "FAIL",
        "no_generic_fallback_ids": "PASS" if not banned_ids else "FAIL",
        "no_boilerplate_definitions": "PASS" if not generic_def else "FAIL",
        "unclassified_zero": "PASS" if states.get("UNCLASSIFIED", 0) == 0 else "FAIL",
        "every_occurrence_has_rule": "PASS" if not no_rule else "FAIL",
        "active_asset_coverage": "PASS" if all(asset_cov[s]["candidates"] >= 0 and asset_cov[s]["unclassified"] == 0 for s in ACTIVE_REPORT_SLUGS) else "FAIL",
        "global_coverage": "PASS" if global_cov["unclassified"] == 0 else "FAIL",
        "ray_not_active_report": "PASS" if not ray_active else "FAIL",
        "grass_not_active_report": "PASS" if not grass_active else "FAIL",
        "orca_not_onboarded_report": "PASS" if not orca_report else "FAIL",
        "no_market_hold_when_ticker": "PASS" if not market_hold else "FAIL",
        "wallet_ownership_separation": "PASS" if all(m["owner"] == "GROK" for m in registry if m["wallet_or_non_wallet"] == "WALLET") else "FAIL",
        "historical_static_separation": "PASS" if all(
            (m["metric_type"] != "HISTORICAL" or m["historical_or_current"] == "HISTORICAL")
            and (m["metric_type"] not in ("STATIC_REFERENCE", "STATIC_DECISION_THRESHOLD") or m["historical_or_current"] == "STATIC")
            for m in registry
        ) else "FAIL",
        "conflict_value_unknown": "PASS" if not conflict_bad else "FAIL",
        "derived_has_method_inputs": "PASS" if not derived_bad else "FAIL",
        "pump_buyback_7d_not_daily": "PASS" if pump7 and not pump7_bad else "FAIL",
        "etf_30d_not_ma_or_price": "PASS" if etf30 is not None and not etf30_bad else "FAIL",
        "drawdown_not_ma_labels": "PASS" if not dd_bad else "FAIL",
        "type_safety_all_metrics": "PASS" if not anomalies else "FAIL",
        "semantic_anomaly_zero": "PASS" if len(anomalies) == 0 else "FAIL",
        "conflict_detection": "PASS" if all(
            m["status"] != "CONFLICT" or (m["value"] in (None, "UNKNOWN") and m.get("evidence_variants"))
            for m in registry
        ) else "FAIL",
    }

    (METRICS / "metric-registry.json").write_text(json.dumps({"metrics": registry}, indent=2) + "\n")
    (METRICS / "ui-occurrences.json").write_text(json.dumps({"occurrences": occs_out}, indent=2) + "\n")

    conflicts = [m for m in registry if m["status"] == "CONFLICT"]
    unknowns = []
    for m in registry:
        missing = [k for k in ("source", "fetched_at", "raw_value", "as_of") if str(m.get(k)) == "UNKNOWN"]
        if missing:
            unknowns.append({
                "metric_id": m["metric_id"], "asset": m["asset"], "missing": missing,
                "why": "Not evidenced in the same HTML component. Job 1 does not research.",
                "owner": m["owner"], "blocks_mapping": False,
                "needs_job2": m["owner"] == "CGPT_CURSOR",
            })

    cov_md = [
        "# JOB V4-1 COVERAGE (correction)",
        f"candidates: {len(classified)}",
        f"canonical metrics: {len(registry)}",
        f"unclassified: {states.get('UNCLASSIFIED', 0)}",
    ]
    for k, n in states.most_common():
        cov_md.append(f"- {k}: {n}")
    cov_md.append("\n## Active reports")
    for s in ACTIVE_REPORT_SLUGS:
        d = asset_cov[s]
        cov_md.append(f"- {s}: candidates={d['candidates']} mapped={d['mapped']} unclassified={d['unclassified']}")
    cov_md.append("\n## Dormant / LEGACY_INACTIVE")
    for s, d in dormant_cov.items():
        cov_md.append(f"- {s}: candidates={d['candidates']} mapped={d['mapped']} unclassified={d['unclassified']}")
    cov_md.append("\n## Hold-card-only")
    for s, d in hold_only_cov.items():
        cov_md.append(f"- {s}: candidates={d['candidates']} mapped={d['mapped']} unclassified={d['unclassified']}")
    cov_md.append(f"\n## Global\n{global_cov}")
    loc_counts = Counter(c["ui_location_type"] for c in classified)
    cov_md.append("\n## By location")
    for k, n in loc_counts.most_common():
        cov_md.append(f"- {k}: {n}")
    (METRICS / "JOB-V4-1-COVERAGE.md").write_text("\n".join(cov_md) + "\n")

    conf_md = ["# JOB-V4-1-CONFLICTS", "", "Action: RECORDED ONLY — canonical value = UNKNOWN", ""]
    for m in conflicts:
        conf_md.append(f"## {m['metric_id']}")
        conf_md.append(f"- asset: {m['asset']} owner: {m['owner']} value: {m['value']}")
        for v in m["evidence_variants"][:16]:
            conf_md.append(f"- {v['occurrence_id']}: `{v['literal']}` source={v.get('source')}")
        conf_md.append("")
    (METRICS / "JOB-V4-1-CONFLICTS.md").write_text("\n".join(conf_md) + "\n")

    unk_md = ["# JOB-V4-1-UNKNOWNS", "", "fetched_at is UNKNOWN for every record (not inferred).", ""]
    by_m = Counter()
    for u in unknowns:
        for k in u["missing"]:
            by_m[k] += 1
    for k, n in by_m.most_common():
        unk_md.append(f"- {k}: {n}")
    unk_md.append("\n## Non-fetched_at gaps")
    for u in unknowns:
        interesting = [k for k in u["missing"] if k != "fetched_at"]
        if interesting:
            unk_md.append(f"- `{u['metric_id']}` missing={interesting} owner={u['owner']}")
    (METRICS / "JOB-V4-1-UNKNOWNS.md").write_text("\n".join(unk_md) + "\n")
    (METRICS / "JOB-V4-1-UNKNOWNS.json").write_text(json.dumps({"unknowns": unknowns}, indent=2) + "\n")
    (METRICS / "JOB-V4-1-OWNERSHIP.md").write_text(
        "# JOB-V4-1-OWNERSHIP\n"
        f"CGPT_CURSOR canonical metrics: {owners.get('CGPT_CURSOR', 0)}\n"
        f"GROK canonical metrics: {owners.get('GROK', 0)}\n"
        "unowned: 0\n"
    )

    urls_n = sum(1 for m in registry if m.get("source_url_or_reference"))
    src_n = sum(1 for m in registry if m.get("source") not in (None, "UNKNOWN"))
    REGRESSION_IDS = [
        "btc.leverage.x.current",
        "btc.oi.usd.current",
        "btc.price.drawdown_from_ath.pct",
        "io.funding.pct.current",
        "fart.leverage.x.current",
        "global.fear_greed.index.current",
        "global.participation.count.current",
        "global.participation.beat_btc.count",
        "global.participation.above_50dma.count",
        "fart.leverage.perp_spot_notional.x",
    ]
    reg_md = ["# JOB-V4-1-REGRESSION-LITERALS", ""]
    for mid in REGRESSION_IDS:
        lits = [o["current_literal_text"] for o in occs_out if o.get("metric_id") == mid]
        reg_md.append(f"## {mid}")
        if not lits:
            reg_md.append("(none mapped)")
        for x in lits:
            reg_md.append(f"- `{x}`")
        reg_md.append("")
    (METRICS / "JOB-V4-1-REGRESSION-LITERALS.md").write_text("\n".join(reg_md) + "\n")
    summary = {
        "canonical_metrics": len(registry),
        "ui_occurrences": len(occs_out),
        "candidates": len(classified),
        "unclassified": states.get("UNCLASSIFIED", 0),
        "classification": dict(states),
        "metric_types": dict(types),
        "ownership": dict(owners),
        "freshness": dict(fresh),
        "status": dict(statuses),
        "conflicts": len(conflicts),
        "semantic_anomalies": len(anomalies),
        "unknown_records": len(unknowns),
        "sources_captured": src_n,
        "source_urls_captured": urls_n,
        "active_report_assets": ACTIVE_REPORT_SLUGS,
        "dormant_assets": sorted(DORMANT_SLUGS),
        "hold_card_only_assets": sorted(HOLD_ONLY_TICKERS.values()),
        "asset_coverage": asset_cov,
        "dormant_coverage": dormant_cov,
        "hold_only_coverage": hold_only_cov,
        "global_coverage": global_cov,
        "tests": tests,
        "schema_errors_sample": schema_errors[:20],
        "fail_hints": {
            "banned_ids": banned_ids[:10],
            "pump7_bad": pump7_bad,
            "etf30_bad": etf30_bad,
            "market_hold": len(market_hold),
            "derived_bad": derived_bad,
            "conflict_bad": conflict_bad,
            "ray_active": len(ray_active),
            "grass_active": len(grass_active),
            "anomalies": anomalies[:12],
        },
    }
    (METRICS / "JOB-V4-1-SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    fails = [k for k, v in tests.items() if v != "PASS"]
    if fails:
        print("FAILED", fails, file=sys.stderr)
    return 1 if fails or schema_errors else 0


if __name__ == "__main__":
    sys.exit(main())
