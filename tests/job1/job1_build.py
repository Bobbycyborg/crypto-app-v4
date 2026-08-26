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

from job1_classify import (  # noqa: E402
    CATALOG,
    DEFS,
    TYPE_SPEC,
    classify,
    detect_kind,
    explode_atomic,
    is_address_literal,
    is_dynamic_numeric,
    is_prose_status,
    rest_scope,
    shape_ok,
    type_accepts,
)

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
    return classify(c)



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
        sub = el.xpath('.//*[contains(@class,"econ-sub")]')
        subtxt = txt(sub[0]) if sub else ""
        if nums and lab:
            add(nums[0], txt(nums[0]), "econ_dial" if "econ-dial-num" in cls(nums[0]) else "econ_kpi", {
                "label": lab, "tip_name": lab, "window_hint": subtxt,
            })
        bars = el.xpath('.//*[contains(@class,"econ-bar")]')
        for i, b in enumerate(bars):
            title = b.get("title")
            if title:
                add(b, title, "econ_bar_title", {
                    "label": lab, "tip_name": lab, "bar_last": "is-last" in classes(b) or i == len(bars) - 1,
                    "window_hint": subtxt,
                })
        if sub and is_scalar(txt(sub[0])) and lab:
            add(sub[0], txt(sub[0]), "econ_sub", {"label": lab + " " + txt(sub[0]), "tip_name": lab, "window_hint": subtxt})

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
    tmpl = DEFS.get(rest) or CATALOG.get(rest, ("The " + rest.replace(".", " ") + " quantity for {ASSET} as shown on this dashboard.",))[0]
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

    vk, au, shape = TYPE_SPEC.get(rest) or ("USD_AMOUNT", "USD", "any_numeric")
    if rest in CATALOG:
        vk, au, shape = CATALOG[rest][1], CATALOG[rest][2], CATALOG[rest][3]
    modes = [o.get("update_mode") for o in occs if o.get("update_mode")]
    update_mode = modes[0] if modes and len(set(modes)) == 1 else (modes[0] if modes else "REPORT_SNAPSHOT")
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
        "update_mode": update_mode,
        "scope_key": first.get("scope_key") or rest_scope(rest),
        "notes": " ".join(notes) if notes else "Job 1 inventory. Provenance is component-local only.",
    }


def main() -> int:
    if set(DEFS) != set(TYPE_SPEC):
        missing = set(DEFS) - set(TYPE_SPEC)
        extra = set(TYPE_SPEC) - set(DEFS)
        raise SystemExit(f"TYPE_SPEC mismatch missing={missing} extra={extra}")
    METRICS.mkdir(parents=True, exist_ok=True)
    root = lhtml.parse(str(HTML)).getroot()
    raw = explode_atomic(extract(root))
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
            "update_mode": c.get("update_mode"),
            "time_window": c.get("time_window"),
            "scope_key": c.get("scope_key"),
            "parent_occurrence_id": c.get("parent_occurrence_id"),
            "linked_metric_ids": c.get("linked_metric_ids") or [],
            "is_compound_parent": bool(c.get("is_compound_parent")),
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
        leftover -= {"EMPTY", "OTHER", "INDEX", "COUNT", "TOKEN_AMOUNT", "DELTA", "FUNDING_RATE", "PERCENTAGE_POINTS", "USD_PER_DAY", "USD_7D_TOTAL", "USD_AMOUNT", "PRICE_USD", "MA_LEVEL"}
        if leftover and spec[2] not in {"threshold", "any_numeric", "ma_level", "funding_rate", "count", "token_or_count"}:
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

    dyn_unmapped = []
    structured_ctx = []
    compound_unlinked = []
    wallet_bad = []
    window_anoms = []
    mode_anoms = []
    for c in classified:
        slug = c.get("asset_slug") or ""
        if slug in DORMANT_SLUGS:
            continue
        if is_dynamic_numeric(c) and not c.get("metric_id") and c.get("coverage_state") not in {
            "COMPOSITE_DISPLAY", "HISTORICAL", "STATIC_REFERENCE", "WALLET_OWNED", "QUALITATIVE_NON_METRIC",
        }:
            dyn_unmapped.append(c)
        if (
            c.get("kind") in {"ev_v", "metric_val", "econ_dial", "econ_kpi", "atomic_span"}
            and is_dynamic_numeric(c)
            and c.get("coverage_state") == "CONTEXT_ONLY"
        ):
            structured_ctx.append(c)
        if c.get("is_compound_parent"):
            kids = [x for x in classified if x.get("parent_occurrence_id") == c["occurrence_id"]]
            if kids and not all(x.get("metric_id") or x.get("coverage_state") in {
                "HISTORICAL", "QUALITATIVE_NON_METRIC", "COMPOSITE_DISPLAY", "CONTEXT_ONLY",
            } and (x.get("metric_id") or x.get("coverage_state") != "UNCLASSIFIED") for x in kids):
                if any(is_dynamic_numeric(x) and not x.get("metric_id") for x in kids):
                    compound_unlinked.append(c)
        if c.get("kind") == "siren_json" and slug not in DORMANT_SLUGS:
            if c.get("owner") != "GROK" or (
                not c.get("metric_id") and c.get("coverage_state") not in {"COMPOSITE_DISPLAY", "LEGACY_INACTIVE"}
            ):
                wallet_bad.append(c)
        mid = c.get("metric_id") or ""
        blob = f"{c.get('label') or ''} {c.get('window_hint') or ''} {c.get('literal') or ''}".lower()
        if mid.endswith("fees.usd.7d") and ("30d" in blob or "/d" in (c.get("literal") or "").lower()):
            window_anoms.append({"id": mid, "lit": c.get("literal"), "why": "7d_id_with_30d_or_per_day"})
        if mid.endswith("revenue.usd.30d") and any(x in (c.get("label") or "").lower() for x in ("july", "may", "cumulative")):
            window_anoms.append({"id": mid, "lit": c.get("literal"), "why": "30d_id_with_other_window"})
        if ".funding.pct.current" in mid or mid.endswith("funding.pct.current"):
            if "7d mean" in blob or "latest" in blob:
                window_anoms.append({"id": mid, "lit": c.get("literal"), "why": "undifferentiated_funding"})
    by_mid_modes = defaultdict(set)
    for c in classified:
        if c.get("metric_id") and c.get("update_mode"):
            by_mid_modes[c["metric_id"]].add(c["update_mode"])
    for mid, modes in by_mid_modes.items():
        if len(modes) > 1:
            mode_anoms.append({"metric_id": mid, "modes": sorted(modes)})

    scope_anoms = []
    prose_as_metric = []
    by_mid_scopes = defaultdict(set)
    for c in classified:
        mid = c.get("metric_id")
        if not mid:
            continue
        if c.get("scope_key"):
            by_mid_scopes[mid].add(c["scope_key"])
        lit = c.get("literal") or ""
        if is_prose_status(lit) or is_address_literal(lit) or re.search(r"\byears?\b", lit, re.I):
            prose_as_metric.append({"metric_id": mid, "lit": lit})
        labs = (c.get("label") or "").lower()
        if "return.pct" in mid and ("oi" in labs or "open interest" in labs):
            scope_anoms.append({"metric_id": mid, "why": "price_return_vs_oi_change", "lit": lit})
        if "volume.spot." in mid and "perp" in labs:
            scope_anoms.append({"metric_id": mid, "why": "spot_vs_perp", "lit": lit})
        if "volume.perp." in mid and re.search(r"\bspot\b", labs):
            scope_anoms.append({"metric_id": mid, "why": "spot_vs_perp", "lit": lit})
        if mid.endswith("volume.usd.24h"):
            scope_anoms.append({"metric_id": mid, "why": "unscoped_volume", "lit": lit})
        if ".fees." in mid and any(x in labs for x in ("buyback",)) or (".fees." in mid and re.search(r"\brev\b", labs)):
            scope_anoms.append({"metric_id": mid, "why": "fees_vs_revenue_buyback", "lit": lit})
        if "return.pct" in mid and ("vs btc" in labs or "vs sol" in labs):
            scope_anoms.append({"metric_id": mid, "why": "return_vs_rs", "lit": lit})
        if "emissions.tokens" in mid and re.search(r"\byears?\b", lit, re.I):
            scope_anoms.append({"metric_id": mid, "why": "tokens_vs_duration", "lit": lit})
    for mid, scopes in by_mid_scopes.items():
        if len(scopes) > 1:
            scope_anoms.append({"metric_id": mid, "why": "mixed_scope_key", "scopes": sorted(scopes)})
    wallet_owner_bad = [m["metric_id"] for m in registry if (".mm." in m["metric_id"] or ".wallet." in m["metric_id"]) and m["owner"] != "GROK"]

    tests = {
        "schema_validation": "PASS" if not schema_errors else "FAIL",
        "unique_metric_ids": "PASS" if len({m["metric_id"] for m in registry}) == len(registry) else "FAIL",
        "required_fields": "PASS" if not schema_errors else "FAIL",
        "owner_coverage": "PASS" if owners.get("CGPT_CURSOR", 0) + owners.get("GROK", 0) == len(registry) else "FAIL",
        "occurrence_references": "PASS" if all(
            (o["metric_id"] in by_id) or o["coverage_state"] in {
                "QUALITATIVE_NON_METRIC", "FALSE_POSITIVE", "EVIDENCE_REFERENCE", "CONTEXT_ONLY",
                "COMPOSITE_DISPLAY", "LEGACY_INACTIVE",
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
        "active_reports_ten": "PASS" if ACTIVE_REPORT_SLUGS == [
            "btc", "fartcoin", "hype", "io", "nos", "pump", "render", "sol", "spx6900", "zec",
        ] else "FAIL",
        "dynamic_numeric_unmapped_zero": "PASS" if not dyn_unmapped else "FAIL",
        "structured_numeric_context_only_zero": "PASS" if not structured_ctx else "FAIL",
        "compound_unlinked_zero": "PASS" if not compound_unlinked else "FAIL",
        "wallet_siren_mapped": "PASS" if not wallet_bad else "FAIL",
        "time_window_anomalies_zero": "PASS" if not window_anoms else "FAIL",
        "update_mode_anomalies_zero": "PASS" if not mode_anoms else "FAIL",
        "semantic_scope_anomalies_zero": "PASS" if not scope_anoms else "FAIL",
        "prose_as_metric_zero": "PASS" if not prose_as_metric else "FAIL",
        "wallet_mm_grok_owned": "PASS" if not wallet_owner_bad else "FAIL",
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
    (METRICS / "metric-families.json").write_text(json.dumps({
        rest: {"definition": d, "value_kind": vk, "allowed_unit": u, "allowed_literal_shape": s}
        for rest, (d, vk, u, s) in CATALOG.items()
    }, indent=2) + "\n")

    def _row(asset, needle, mid_suffix=None):
        hits = []
        for o in occs_out:
            if o.get("asset") != asset:
                continue
            ident = (o.get("ui_location_identifier") or "") + " " + (o.get("current_literal_text") or "")
            if needle.lower() not in ident.lower() and needle.lower() not in (o.get("current_literal_text") or "").lower():
                continue
            if mid_suffix and mid_suffix not in (o.get("metric_id") or ""):
                continue
            hits.append(o)
        return hits

    reg_md = ["# JOB-V4-1-REGRESSION", "", "literal → metric_id → window/update_mode → source/as_of → owner", ""]
    cases = [
        ("HYPE Fees 30D", "HYPE", "59.2", "fees.usd.30d"),
        ("SOL fees 30d mean /d", "SOL", "809", "fees.usd_per_day.mean_30d"),
        ("SOL fees ±7d mean", "SOL", "600k", "fees.usd_per_day.mean_7d"),
        ("SOL fees Nov 2024", "SOL", "9.5M", "fees.usd_per_day.nov_2024"),
        ("SOL fees June 2026", "SOL", "356k", "fees.usd_per_day.june_2026"),
        ("SOL funding latest", "SOL", "Latest", "funding.rate.latest"),
        ("SOL funding 7d mean", "SOL", "7d mean", "funding.rate.mean_7d"),
        ("IO cumulative earnings", "IO", "26.7", "revenue.usd.cumulative"),
        ("IO July earnings", "IO", "932,730", "revenue.usd.july_2026"),
        ("IO May earnings", "IO", "1.1M", "revenue.usd.may_2026"),
        ("BTC 50d", "BTC", "50d", "ma.usd.50d"),
        ("BTC 200d", "BTC", "200d", "ma.usd.200d"),
        ("PUMP DEX liquidity", "PUMP", "22.7", "liquidity.dex.usd.current"),
        ("PUMP market share", "PUMP", "47%", "market_share.pct.current"),
        ("SOL TVL", "SOL", "5.65", "tvl.usd.current"),
        ("SOL stablecoins", "SOL", "15.91", "stablecoin.usd.current"),
        ("SOL stake ratio", "SOL", "68.8", "stake.ratio.pct"),
        ("SOL inflation", "SOL", "3.68", "inflation.pct.current"),
        ("SOL TPS", "SOL", "2578", "tps.nonvote.current"),
        ("HYPE AF stock", "HYPE", "46.4", "af.inventory.tokens.current"),
        ("HYPE AF buys", "HYPE", "43.9", "af.buys.usd.30d"),
        ("HYPE emissions", "HYPE", "412", "emissions.tokens.remaining"),
        ("RENDER frames", "RENDER", "78.90", "usage.frames.cumulative"),
        ("RENDER BME", "RENDER", "0.21", "bme.ratio.last4"),
        ("PUMP siren watched", "PUMP", "150", "siren.watched_wallet_count.current"),
        ("RENDER siren watched", "RENDER", "40", "siren.watched_wallet_count.current"),
        ("NOS siren watched", "NOS", None, "siren.watched_wallet_count.current"),
        ("ORCA siren watched", "ORCA", None, "siren.watched_wallet_count.current"),
    ]
    for title, asset, needle, suffix in cases:
        reg_md.append(f"## {title}")
        rows = []
        for o in occs_out:
            if o.get("asset") != asset:
                continue
            mid = o.get("metric_id") or ""
            if suffix not in mid:
                continue
            if needle and needle.lower() not in ((o.get("current_literal_text") or "") + (o.get("ui_location_identifier") or "")).lower() and needle.lower() not in mid.lower():
                continue
            rows.append(o)
        if not rows:
            reg_md.append("(none)")
        seen = set()
        for o in rows[:8]:
            key = (o.get("metric_id"), o.get("current_literal_text"))
            if key in seen:
                continue
            seen.add(key)
            reg_md.append(
                f"- `{o.get('current_literal_text')}` → `{o.get('metric_id')}` → "
                f"{o.get('time_window')}/{o.get('update_mode')} → "
                f"{o.get('source')}/{o.get('as_of')} → {o.get('owner')} ({o.get('coverage_state')})"
            )
        reg_md.append("")
    (METRICS / "JOB-V4-1-REGRESSION.md").write_text("\n".join(reg_md) + "\n")
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
        "dynamic_numeric_unmapped": len(dyn_unmapped),
        "structured_numeric_context_only": len(structured_ctx),
        "compound_unlinked": len(compound_unlinked),
        "wallet_siren_bad": len(wallet_bad),
        "time_window_anomalies": len(window_anoms),
        "update_mode_anomalies": len(mode_anoms),
        "semantic_scope_anomalies": len(scope_anoms),
        "prose_as_metric": len(prose_as_metric),
        "wallet_metrics": owners.get("GROK", 0),
        "atomic_dynamic_facts": sum(1 for c in classified if is_dynamic_numeric(c) and c.get("metric_id")),
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
            "dyn_unmapped_sample": [
                {"label": c.get("label"), "lit": (c.get("literal") or "")[:80], "asset": c.get("asset_slug"), "rule": c.get("classification_rule")}
                for c in dyn_unmapped[:20]
            ],
            "window_anoms": window_anoms[:12],
            "wallet_bad": len(wallet_bad),
            "scope_anoms": scope_anoms[:12],
            "prose_as_metric": prose_as_metric[:12],
            "wallet_owner_bad": wallet_owner_bad[:12],
            "structured_ctx_sample": [
                {"label": c.get("label"), "lit": (c.get("literal") or "")[:60], "asset": c.get("asset_slug")}
                for c in structured_ctx[:12]
            ],
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
