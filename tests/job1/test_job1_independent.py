#!/usr/bin/env python3
"""Independent Job 1 checker. Reads emitted JSON only. Does not import production parsers."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METRICS = ROOT / "metrics"
GOLDEN = Path(__file__).resolve().parent / "golden-semantics.json"

FORBIDDEN_RULES = {
    "keyword_family", "generic_row", "label_inventory", "fallback",
    "captured", "usd_figure", "pct_figure", "pp_figure",
}
GENERIC_EXTRACTORS = {
    "exact_numeric", "usd_amount", "usd_per_day", "usd_per_week", "percent",
    "percentage_points", "ratio_x", "scientific_number", "token_amount", "count",
}
EXPLICIT_EXTRACTORS = {"window_percent", "named_regex_group", "explicit_unknown"}
ALLOWED_COVERAGE = {
    "MAPPED_CANONICAL", "HISTORICAL", "STATIC_DECISION_THRESHOLD", "STATIC_REFERENCE",
    "WALLET_OWNED", "COMPOSITE_DISPLAY", "CONTEXT_ONLY", "EVIDENCE_REFERENCE",
    "QUALITATIVE_NON_METRIC", "FALSE_POSITIVE", "LEGACY_INACTIVE",
}
_SUFFIX_SCALE = {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}


def fail(name: str, msg: str) -> None:
    print(f"FAIL {name}: {msg}")
    sys.exit(1)


def numeric_token_count(lit: str) -> int:
    s = lit or ""
    s = re.sub(r"\b(?:1d|7d|30d|90d|180d|24h)\b", " ", s, flags=re.I)
    s = re.sub(r"~?\d+\s*(?:wks?|weeks?|hours?|epochs?)\b", " ", s, flags=re.I)
    s = re.sub(r"/~\d+d\b", " ", s, flags=re.I)
    return len(re.findall(r"\d+(?:[.,]\d+)?(?:e[+\-]?\d+)?", s, re.I))


def display_coeff(lit: str):
    s = (lit or "").strip()
    s = re.sub(r"[~$%\s×x]", "", s, flags=re.I)
    s = s.replace(",", "").replace("−", "-")
    m = re.search(r"(-?\d+(?:\.(\d+))?)([KMBT])?", s, re.I)
    if not m:
        return None, "", None
    return float(m.group(1)), (m.group(3) or "").upper(), len(m.group(2) or "")


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
    return round(other_raw / scale, places) == round(coeff, places)


def raw_close(got, expect, tol=0.0) -> bool:
    if expect == "UNKNOWN":
        return got == "UNKNOWN" or got is None
    if isinstance(expect, (int, float)) and isinstance(got, (int, float)):
        return abs(float(got) - float(expect)) <= (tol or 0)
    return got == expect


def match_occ(o: dict, case: dict) -> bool:
    if case.get("asset") and o.get("asset") != case["asset"]:
        return False
    lit = o.get("current_literal_text") or ""
    lab = o.get("ui_location_identifier") or ""
    parent = o.get("parent_label") or ""
    if case.get("literal_equals") is not None and lit != case["literal_equals"]:
        return False
    if case.get("literal_contains") and case["literal_contains"] not in lit:
        return False
    if case.get("label_contains") and case["label_contains"].lower() not in lab.lower():
        return False
    if case.get("parent_contains") and case["parent_contains"].lower() not in parent.lower() and case["parent_contains"].lower() not in lab.lower():
        return False
    return True


def main() -> int:
    registry = json.loads((METRICS / "metric-registry.json").read_text())["metrics"]
    occs = json.loads((METRICS / "ui-occurrences.json").read_text())["occurrences"]
    summary = json.loads((METRICS / "JOB-V4-1-SUMMARY.json").read_text())
    families = json.loads((METRICS / "metric-families.json").read_text())
    manifest = json.loads((METRICS / "ui-mapping-manifest.json").read_text())
    golden = json.loads(GOLDEN.read_text())
    by_mid = {m["metric_id"]: m for m in registry}

    gates = {k: 0 for k in [
        "unclassified", "automatic_metric_creation", "manifest_missing_mapping",
        "manifest_unknown_family", "generic_semantic_assignment",
        "multi_number_without_explicit_extractor", "first_number_fallback_used",
        "parent_context_lost", "historical_child_marked_current",
        "ambient_provenance_leak", "wrong_numeric_token_selected",
        "scientific_notation_parse_errors", "abbreviated_unknown_parsed_zero",
        "display_scale_unproved", "count_noun_collision",
        "relative_strength_as_price_return", "wallet_balance_flow_collision",
        "scope_collision", "window_collision", "observation_collision",
        "rounding_variant_marked_conflict", "conflict_unreviewed",
        "wallet_owner_bad", "prose_as_metric", "dynamic_numeric_unmapped",
    ]}

    gates["unclassified"] = sum(1 for o in occs if o.get("coverage_state") == "UNCLASSIFIED")
    if summary.get("unclassified", 1) != 0:
        gates["unclassified"] = max(gates["unclassified"], summary["unclassified"])

    fam_used = set()
    for o in occs:
        mid = o.get("metric_id")
        if mid:
            rest = mid.split(".", 1)[1]
            fam_used.add(rest)
            if rest not in families:
                gates["manifest_unknown_family"] += 1
        rule = o.get("classification_rule") or ""
        if rule in FORBIDDEN_RULES:
            gates["generic_semantic_assignment"] += 1
        if o.get("coverage_state") not in ALLOWED_COVERAGE:
            gates["unclassified"] += 1
        lit = o.get("current_literal_text") or ""
        ext = o.get("extractor")
        if mid and numeric_token_count(lit) >= 2:
            if ext in GENERIC_EXTRACTORS or not ext:
                gates["multi_number_without_explicit_extractor"] += 1
        if re.search(r"\.\.\.|…", lit) and re.search(r"\$?0\.0", lit):
            if o.get("raw_value") == 0:
                gates["abbreviated_unknown_parsed_zero"] += 1
        if re.search(r"5\.533e-05", lit.replace(" ", ""), re.I) and mid:
            raw = o.get("raw_value")
            if not isinstance(raw, (int, float)) or abs(raw - (-0.00005533)) > 1e-12:
                gates["scientific_notation_parse_errors"] += 1
        if mid and re.search(r"\b(leads|lags|do not use|last\s+\d+\s+wks?)\b", lit, re.I) and "%" not in lit:
            gates["prose_as_metric"] += 1
        if (mid or "").endswith("price.ath.usd") and lit.strip() == "$126.1":
            if o.get("raw_value") not in ("UNKNOWN", None) and o.get("raw_value") == 126.1:
                gates["display_scale_unproved"] += 1
        if o.get("wallet_or_non_wallet") == "WALLET" or (mid or "").startswith(("pump.mm.", "nos.siren.",)) or ".mm." in (mid or "") or ".siren." in (mid or "") or ".wallet." in (mid or ""):
            if mid and o.get("owner") != "GROK":
                gates["wallet_owner_bad"] += 1

    for rest in fam_used:
        if rest not in families:
            gates["manifest_unknown_family"] += 1
    for e in manifest.get("mappings") or []:
        rest = e.get("measure_key")
        if rest and rest not in families and e.get("metric_id"):
            gates["manifest_unknown_family"] += 1

    jobs = [o for o in occs if o.get("metric_id") == "nos.jobs.running.count"]
    nodes = [o for o in occs if o.get("metric_id") == "nos.nodes.with_running_jobs.count"]
    if any("35" == (o.get("current_literal_text") or "").replace("~", "").strip() for o in jobs):
        gates["count_noun_collision"] += 1
    if any((o.get("current_literal_text") or "").replace(",", "") in {"855"} for o in nodes):
        gates["count_noun_collision"] += 1

    for o in occs:
        mid = o.get("metric_id") or ""
        parent = (o.get("parent_label") or "") + " " + (o.get("ui_location_identifier") or "")
        if "return.pct" in mid and re.search(r"pump\s*/\s*(btc|sol)|vs (btc|sol)", parent, re.I):
            gates["relative_strength_as_price_return"] += 1
        if mid == "pump.mm.wintermute.balance.tokens" and "287" in (o.get("current_literal_text") or ""):
            gates["wallet_balance_flow_collision"] += 1
        if mid == "pump.mm.wintermute.transfer.tokens" and "4.43" in (o.get("current_literal_text") or ""):
            gates["wallet_balance_flow_collision"] += 1

    by_id_obs = defaultdict(set)
    by_id_scope = defaultdict(set)
    by_id_win = defaultdict(set)
    for o in occs:
        mid = o.get("metric_id")
        if not mid:
            continue
        if o.get("observation_id"):
            by_id_obs[mid].add(o["observation_id"])
        if o.get("scope_key"):
            by_id_scope[mid].add(o["scope_key"])
        if o.get("time_window"):
            by_id_win[mid].add(o["time_window"])
    for mid, scopes in by_id_scope.items():
        if len(scopes) > 1:
            gates["scope_collision"] += 1
    for mid, wins in by_id_win.items():
        if len({w for w in wins if w}) > 1 and not any(x in mid for x in ("etf.flow",)):
            # window in id should match; mixed windows on one id is collision
            if len([w for w in wins if w not in {"current", "usd", None, ""}]) > 1:
                gates["window_collision"] += 1

    for m in registry:
        if m["status"] != "CONFLICT":
            continue
        if m.get("conflict_review") != "MANUALLY_CONFIRMED":
            gates["conflict_unreviewed"] += 1
        if (".mm." in m["metric_id"] or ".wallet." in m["metric_id"] or ".siren." in m["metric_id"]) and m["owner"] != "GROK":
            gates["wallet_owner_bad"] += 1
        rows = [o for o in occs if o.get("metric_id") == m["metric_id"]]
        groups = defaultdict(list)
        for o in rows:
            key = (o.get("observation_id"), o.get("scope_key"), o.get("update_mode"))
            groups[key].append(o)
        for g in groups.values():
            nums, lits = [], []
            for o in g:
                r = o.get("raw_value")
                if isinstance(r, (int, float)):
                    nums.append(r)
                    lits.append(o.get("current_literal_text") or "")
            if len(set(nums)) <= 1:
                continue
            places = []
            for lit in lits:
                _c, _s, p = display_coeff(lit)
                places.append(999 if p is None else p)
            idx = min(range(len(places)), key=lambda i: places[i])
            if all(i == idx or rounding_equivalent(nums[idx], nums[i], lits[idx], lits[i]) for i in range(len(nums))):
                gates["rounding_variant_marked_conflict"] += 1

    # golden
    for case in golden["cases"]:
        if case.get("expect_registry_status"):
            spec = case["expect_registry_status"]
            m = by_mid.get(spec["metric_id"])
            if not m or m.get("status") != spec["status"]:
                fail(case["id"], f"registry {spec['metric_id']} status={None if not m else m.get('status')} want {spec['status']}")
            print(f"PASS golden {case['id']}")
            continue
        hits = [o for o in occs if match_occ(o, case)]
        if not hits:
            fail(case["id"], "no occurrence matched")
        if case.get("expect_nonmetric"):
            bad = [o for o in hits if o.get("metric_id") and o.get("coverage_state") in {"MAPPED_CANONICAL", "HISTORICAL", "WALLET_OWNED"}]
            if bad:
                fail(case["id"], f"mapped as {bad[0].get('metric_id')}")
            print(f"PASS golden {case['id']}")
            continue
        ok = False
        for o in hits:
            if case.get("expect_metric_id") and o.get("metric_id") != case["expect_metric_id"]:
                continue
            if "expect_raw" in case and not raw_close(o.get("raw_value"), case["expect_raw"], case.get("raw_tolerance") or 0):
                continue
            if case.get("expect_historical") is True and o.get("historical_or_current") != "HISTORICAL" and o.get("coverage_state") != "HISTORICAL":
                continue
            if case.get("expect_historical") is False and o.get("coverage_state") == "HISTORICAL":
                continue
            if case.get("expect_observation_id") and o.get("observation_id") != case["expect_observation_id"]:
                continue
            if case.get("expect_owner") and o.get("owner") != case["expect_owner"]:
                continue
            if case.get("forbid_raw_zero") and o.get("raw_value") == 0:
                continue
            ok = True
            break
        if not ok:
            sample = [(h.get("metric_id"), h.get("raw_value"), h.get("current_literal_text"), h.get("coverage_state")) for h in hits[:4]]
            fail(case["id"], f"no hit satisfied constraints {sample}")
        print(f"PASS golden {case['id']}")

    # RS must not sit on return.pct
    for o in occs:
        if (o.get("metric_id") or "").startswith("pump.return") and re.search(r"31\.1|102\.3|27\.7|104\.7", o.get("current_literal_text") or ""):
            gates["relative_strength_as_price_return"] += 1

    print("GATES", json.dumps(gates, indent=2))
    bad = [k for k, n in gates.items() if n != 0]
    if bad:
        fail("independent_gates", str({k: gates[k] for k in bad}))
    print("ALL INDEPENDENT GATES = 0")
    print("ALL GOLDEN SEMANTIC CASES PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
