#!/usr/bin/env python3
"""Apply explicit mapping manifest. No semantic inference."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from job1_classify import (
    CATALOG,
    DEFS,
    TYPE_SPEC,
    is_historical_window,
    rest_scope,
)
from job1_extractors import (
    ALLOWED_EXTRACTORS,
    GENERIC_EXTRACTORS,
    extract_value,
    has_ellipsis_price,
    numeric_token_count,
    rounding_equivalent,
)

FORBIDDEN_RULES = {
    "keyword_family", "generic_row", "label_inventory", "fallback",
    "captured", "usd_figure", "pct_figure", "pp_figure",
}
ALLOWED_MAPPED_RULES = {
    "manifest_exact", "manifest_compound_child", "manifest_window_capture",
    "manifest_named_capture", "manifest_wallet_inventory", "manifest_wallet_transfer",
}

VK_EXTRACTOR = {
    "PRICE_USD": "usd_amount",
    "USD_AMOUNT": "usd_amount",
    "USD_PER_DAY": "usd_per_day",
    "USD_PER_DAY_MEAN_30D": "usd_per_day",
    "USD_7D_TOTAL": "usd_amount",
    "USD_30D_TOTAL": "usd_amount",
    "PERCENT": "percent",
    "PERCENTAGE_POINTS": "percentage_points",
    "RATIO_X": "ratio_x",
    "TOKEN_AMOUNT": "token_amount",
    "COUNT": "count",
    "INDEX": "exact_numeric",
    "FUNDING_RATE": "scientific_number",
    "MA_LEVEL": "usd_amount",
}


def slug_id(asset_slug: str, rest: str) -> str:
    a = "fart" if asset_slug == "fartcoin" else "spx" if asset_slug == "spx6900" else asset_slug
    a = re.sub(r"[^a-z0-9]+", "", a)
    return f"{a}.{rest}"


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_manifest(manifest: dict, families: dict) -> list[str]:
    errors = []
    for i, e in enumerate(manifest.get("mappings") or []):
        mid = e.get("mapping_id") or f"idx-{i}"
        if not e.get("match"):
            errors.append(f"{mid}: missing match")
        rest = None
        metric_id = e.get("metric_id")
        if metric_id:
            rest = metric_id.split(".", 1)[1] if "." in metric_id else None
        rest = e.get("measure_key") or rest
        if metric_id or e.get("classification") in {
            "MAPPED_CANONICAL", "HISTORICAL", "STATIC_DECISION_THRESHOLD", "WALLET_OWNED",
        }:
            if rest and rest not in families:
                errors.append(f"{mid}: manifest_unknown_family {rest}")
        ext = e.get("extractor") or {}
        if isinstance(ext, str):
            et = ext
        else:
            et = ext.get("type")
        if et and et not in ALLOWED_EXTRACTORS:
            errors.append(f"{mid}: bad extractor {et}")
    return errors


def _match_ok(match: dict, c: dict) -> bool:
    if not match:
        return False
    oid = match.get("occurrence_id")
    if oid and oid != c.get("occurrence_id"):
        return False
    if match.get("asset"):
        want = str(match["asset"]).lower()
        got = (c.get("asset_slug") or "").lower()
        alias = {"fart": "fartcoin", "fartcoin": "fart", "spx": "spx6900", "spx6900": "spx"}
        if want != got and alias.get(want) != got and alias.get(got) != want:
            if want not in {got, (c.get("asset") or "").lower()}:
                return False
    if match.get("kind") and match["kind"] != c.get("kind"):
        return False
    if match.get("label") is not None and match["label"] != (c.get("label") or ""):
        return False
    if match.get("parent_label") is not None and match["parent_label"] != (c.get("parent_label") or ""):
        return False
    if match.get("literal") is not None and match["literal"] != (c.get("literal") or ""):
        return False
    pat = match.get("literal_pattern")
    if pat and not re.search(pat, c.get("literal") or "", re.I):
        return False
    row = match.get("row_label")
    if row is not None and row != (c.get("label") or ""):
        return False
    loc = match.get("locator") or match.get("selector")
    if loc and loc != (c.get("html_locator") or ""):
        return False
    surface = match.get("surface")
    if surface and surface != c.get("surface"):
        return False
    return True


def match_specificity(match: dict) -> int:
    score = 0
    if match.get("occurrence_id"):
        score += 100
    for k in ("literal", "literal_pattern", "locator", "selector", "parent_label", "label", "row_label", "kind", "asset"):
        if match.get(k):
            score += 8
    return score


def find_mapping(c: dict, mappings: list[dict]) -> dict | None:
    hits = [e for e in mappings if _match_ok(e.get("match") or {}, c)]
    if not hits:
        return None
    hits.sort(key=lambda e: match_specificity(e.get("match") or {}), reverse=True)
    return hits[0]


def rule_for(entry: dict) -> str:
    if entry.get("classification_rule") in ALLOWED_MAPPED_RULES:
        return entry["classification_rule"]
    ext = entry.get("extractor") or {}
    et = ext if isinstance(ext, str) else ext.get("type")
    owner = (entry.get("owner") or "").upper()
    rest = (entry.get("measure_key") or "") + " " + (entry.get("metric_id") or "")
    if "wintermute.balance" in rest or entry.get("classification_rule") == "manifest_wallet_inventory":
        return "manifest_wallet_inventory"
    if "wintermute.transfer" in rest or entry.get("classification_rule") == "manifest_wallet_transfer":
        return "manifest_wallet_transfer"
    if et == "window_percent":
        return "manifest_window_capture"
    if et == "named_regex_group":
        return "manifest_named_capture"
    if c_is_child := (entry.get("match") or {}).get("parent_label"):
        return "manifest_compound_child"
    return "manifest_exact"


def apply_entry(c: dict, entry: dict) -> dict:
    lit = c.get("literal") or ""
    slug = c.get("asset_slug") or entry.get("asset") or "global"
    cls = entry.get("classification")
    metric_id = entry.get("metric_id")
    rest = entry.get("measure_key")
    if metric_id and not rest:
        rest = metric_id.split(".", 1)[1]
    if rest and not metric_id and cls not in {
        "CONTEXT_ONLY", "EVIDENCE_REFERENCE", "QUALITATIVE_NON_METRIC",
        "FALSE_POSITIVE", "COMPOSITE_DISPLAY", "LEGACY_INACTIVE",
    }:
        metric_id = slug_id(slug, rest)

    ext = entry.get("extractor") or {"type": "explicit_unknown"}
    if isinstance(ext, str):
        ext = {"type": ext}
    tokens = numeric_token_count(lit)
    et = ext.get("type")
    if metric_id and tokens >= 2 and et in GENERIC_EXTRACTORS:
        raise RuntimeError(
            f"multi_number_without_explicit_extractor {c.get('occurrence_id')} {lit!r} extractor={et}"
        )
    if has_ellipsis_price(lit) and et != "explicit_unknown":
        ext = {"type": "explicit_unknown"}
        et = "explicit_unknown"

    raw = "UNKNOWN"
    if metric_id or et not in {None, "explicit_unknown"}:
        raw = extract_value(ext, lit)
    if entry.get("display_multiplier") and isinstance(raw, (int, float)):
        raw = raw * float(entry["display_multiplier"])

    owner = entry.get("owner") or "CGPT_CURSOR"
    update_mode = entry.get("update_mode") or "REPORT_SNAPSHOT"
    observation_id = entry.get("observation_id") or entry.get("observation_anchor") or "unknown_snapshot"
    scope_key = entry.get("scope_key") or (rest_scope(rest) if rest else "UNSPECIFIED")
    time_window = entry.get("time_window")
    if not time_window and rest:
        time_window = rest.split(".")[-1]

    if cls in {
        "CONTEXT_ONLY", "EVIDENCE_REFERENCE", "QUALITATIVE_NON_METRIC",
        "FALSE_POSITIVE", "COMPOSITE_DISPLAY", "LEGACY_INACTIVE",
    } and not metric_id:
        c["coverage_state"] = cls
        c["classification_rule"] = entry.get("classification_rule") or "manifest_exact"
        c["metric_id"] = None
        c["owner"] = owner
        c["extractor"] = ext
        c["observation_id"] = observation_id
        c["observation_anchor"] = observation_id
        c["update_mode"] = update_mode
        c["scope_key"] = scope_key
        c["time_window"] = time_window
        c["raw_value"] = raw
        c["source_binding"] = entry.get("source_binding") or "unknown"
        c["linked_metric_ids"] = entry.get("linked_metric_ids") or []
        c["notes"] = entry.get("notes")
        _apply_source(c, entry)
        return c

    if not metric_id:
        c["coverage_state"] = cls or "CONTEXT_ONLY"
        c["classification_rule"] = entry.get("classification_rule") or "manifest_exact"
        c["metric_id"] = None
        c["owner"] = owner
        c["extractor"] = ext
        c["observation_id"] = observation_id
        c["raw_value"] = raw
        _apply_source(c, entry)
        return c

    if rest not in CATALOG:
        raise RuntimeError(f"manifest_unknown_family {rest}")

    mtype = "CURRENT_DYNAMIC"
    cov = "MAPPED_CANONICAL"
    if owner == "GROK" or (rest or "").startswith(("mm.", "wallet.", "siren.", "portfolio.")):
        owner = "GROK"
        mtype = "WALLET_OWNED"
        cov = "WALLET_OWNED"
        update_mode = entry.get("update_mode") or "WALLET_SNAPSHOT"
    elif (rest or "").startswith("threshold."):
        mtype = "STATIC_DECISION_THRESHOLD"
        cov = "STATIC_DECISION_THRESHOLD"
        update_mode = entry.get("update_mode") or "STATIC_THRESHOLD"
    elif is_historical_window(str(time_window or "")) or (rest and is_historical_window(rest.split(".")[-1])) or update_mode == "HISTORICAL":
        mtype = "HISTORICAL"
        cov = "HISTORICAL"
        update_mode = "HISTORICAL"
    if cls == "HISTORICAL":
        mtype = "HISTORICAL"
        cov = "HISTORICAL"
        update_mode = "HISTORICAL"
    if cls == "STATIC_DECISION_THRESHOLD":
        mtype = "STATIC_DECISION_THRESHOLD"
        cov = "STATIC_DECISION_THRESHOLD"
        update_mode = "STATIC_THRESHOLD"
    if cls == "WALLET_OWNED":
        mtype = "WALLET_OWNED"
        cov = "WALLET_OWNED"
        owner = "GROK"

    c["metric_id"] = metric_id
    c["coverage_state"] = cov if cls not in {"UNKNOWN_SCOPE"} else "MAPPED_CANONICAL"
    c["classification_rule"] = rule_for(entry)
    if c["classification_rule"] in FORBIDDEN_RULES:
        raise RuntimeError(f"generic_semantic_assignment {c['classification_rule']}")
    c["owner"] = owner
    c["metric_type"] = mtype
    c["value_kind"] = TYPE_SPEC[rest][0]
    c["time_window"] = time_window
    c["update_mode"] = update_mode
    c["scope_key"] = scope_key
    c["observation_id"] = observation_id
    c["observation_anchor"] = observation_id
    c["extractor"] = ext
    c["raw_value"] = raw
    c["display_multiplier"] = entry.get("display_multiplier")
    c["linked_metric_ids"] = entry.get("linked_metric_ids") or []
    c["notes"] = entry.get("notes")
    c["source_binding"] = entry.get("source_binding") or "unknown"
    if cls == "UNKNOWN_SCOPE":
        c["scope_key"] = "UNKNOWN"
        c["status_hint"] = "UNKNOWN_SCOPE"
    _apply_source(c, entry)
    return c


def _apply_source(c: dict, entry: dict) -> None:
    bind = (entry.get("source_binding") or "unknown").lower()
    if bind in {"unknown", "manifest"}:
        if bind == "unknown" and entry.get("source") is None:
            c["source"] = "UNKNOWN"
            c["as_of"] = "UNKNOWN"
        elif bind == "manifest":
            c["source"] = entry.get("source") or "UNKNOWN"
            c["as_of"] = entry.get("as_of") or "UNKNOWN"
        return
    if bind == "atomic_child":
        return
    if bind == "row":
        return
    if bind == "parent_block":
        return
    c["source"] = "UNKNOWN"
    c["as_of"] = "UNKNOWN"


def inherit_parent(child: dict, parent: dict, entry: dict | None) -> None:
    if not parent:
        return
    bind = (entry or {}).get("source_binding") or child.get("source_binding") or "unknown"
    if bind == "parent_block":
        if (not child.get("source") or child.get("source") == "UNKNOWN") and parent.get("source"):
            child["source"] = parent["source"]
        if (not child.get("as_of") or child.get("as_of") == "UNKNOWN") and parent.get("as_of"):
            child["as_of"] = parent["as_of"]
    if not child.get("parent_label"):
        child["parent_label"] = parent.get("label") or parent.get("parent_label")


def apply_manifest(candidates: list[dict], manifest: dict) -> list[dict]:
    mappings = manifest.get("mappings") or []
    errors = validate_manifest(manifest, CATALOG)
    if errors:
        raise RuntimeError("manifest_unknown_family: " + "; ".join(errors[:8]))
    by_id = {c["occurrence_id"]: c for c in candidates}
    out = []
    for c in candidates:
        c = nonmetric_then_manifest(c, mappings)
        parent = by_id.get(c.get("parent_occurrence_id") or "")
        entry = find_mapping(c, mappings)
        inherit_parent(c, parent, entry)
        out.append(c)
    return out


def nonmetric_then_manifest(c: dict, mappings: list[dict]) -> dict:
    from job1_classify import nonmetric_preclassify
    c = nonmetric_preclassify(dict(c))
    entry = find_mapping(c, mappings)
    if entry:
        return apply_entry(c, entry)
    if not c.get("classification_rule"):
        c["coverage_state"] = "UNCLASSIFIED"
        c["classification_rule"] = "unmapped"
        c["metric_id"] = None
    return c


def conflict_groups(occs: list[dict]) -> dict:
    groups = defaultdict(list)
    for o in occs:
        key = (
            o.get("metric_id"),
            o.get("observation_id") or o.get("observation_anchor"),
            o.get("scope_key"),
            o.get("update_mode"),
        )
        groups[key].append(o)
    return groups


def group_status(group: list[dict]) -> str:
    nums = []
    lits = []
    for o in group:
        r = o.get("raw_value")
        if isinstance(r, (int, float)):
            nums.append(r)
            lits.append(o.get("literal") or o.get("current_literal_text") or "")
    if len(set(nums)) <= 1:
        return "OK"
    from job1_extractors import display_coeff
    places = []
    for lit in lits:
        _c, _s, p = display_coeff(lit)
        places.append(999 if p is None else p)
    idx = min(range(len(places)), key=lambda i: places[i])
    for i, n in enumerate(nums):
        if i == idx:
            continue
        if not rounding_equivalent(nums[idx], n, lits[idx], lits[i]):
            return "CONFLICT"
    return "FORMAT_VARIANT"
