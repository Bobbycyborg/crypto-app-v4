#!/usr/bin/env python3
"""Semantic Job 1 gates. Must be able to FAIL."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
METRICS = ROOT / "metrics"
BANNED = ("captured", "usd_figure", "pct_figure", "pp_figure")
ACTIVE = {"BTC", "FART", "HYPE", "IO", "NOS", "PUMP", "RENDER", "SOL", "SPX", "ZEC"}
DORMANT = {"RAY", "GRASS"}


def fail(name: str, msg: str) -> None:
    print(f"FAIL {name}: {msg}")
    sys.exit(1)


def main() -> int:
    schema = json.loads((METRICS / "metric-schema.json").read_text())
    registry = json.loads((METRICS / "metric-registry.json").read_text())["metrics"]
    occs = json.loads((METRICS / "ui-occurrences.json").read_text())["occurrences"]
    summary = json.loads((METRICS / "JOB-V4-1-SUMMARY.json").read_text())
    ids = [m["metric_id"] for m in registry]
    idset = set(ids)
    validator = Draft202012Validator(schema)

    errors = [f"{m['metric_id']}: {e.message}" for m in registry for e in validator.iter_errors(m)]
    if errors:
        fail("schema_validation", "; ".join(errors[:8]))
    print("PASS schema_validation")

    if len(set(ids)) != len(ids):
        fail("unique_metric_ids", "duplicate metric_id")
    print("PASS unique_metric_ids")

    for m in registry:
        missing = [k for k in schema["required"] if k not in m]
        if missing:
            fail("required_fields", f"{m['metric_id']} {missing}")
    print("PASS required_fields")

    owners = Counter(m["owner"] for m in registry)
    if owners.get("CGPT_CURSOR", 0) + owners.get("GROK", 0) != len(registry):
        fail("owner_coverage", str(dict(owners)))
    print("PASS owner_coverage")

    for o in occs:
        if not o.get("classification_rule"):
            fail("every_occurrence_has_rule", o["occurrence_id"])
        if o.get("metric_id") and o["metric_id"] not in idset and o["coverage_state"] not in {
            "QUALITATIVE_NON_METRIC", "FALSE_POSITIVE", "EVIDENCE_REFERENCE", "CONTEXT_ONLY",
        }:
            fail("occurrence_references", o.get("metric_id"))
        if o.get("metric_id") is None and o["coverage_state"] not in {
            "QUALITATIVE_NON_METRIC", "FALSE_POSITIVE", "EVIDENCE_REFERENCE", "CONTEXT_ONLY",
        }:
            fail("occurrence_references", o["occurrence_id"])
    print("PASS occurrence_references")
    print("PASS every_occurrence_has_rule")

    for mid in ids:
        if any(f".{b}." in mid or mid.endswith(f".{b}") for b in BANNED):
            fail("no_generic_fallback_ids", mid)
    print("PASS no_generic_fallback_ids")

    for m in registry:
        if "Canonical record for" in m["definition"] or m["definition"].startswith("Canonical record"):
            fail("no_boilerplate_definitions", m["metric_id"])
        if len(m["definition"]) < 20:
            fail("no_boilerplate_definitions", m["metric_id"])
    print("PASS no_boilerplate_definitions")

    if summary["unclassified"] != 0:
        fail("unclassified_zero", str(summary["unclassified"]))
    print("PASS unclassified_zero")

    if any(o.get("surface") == "ACTIVE_REPORT" and o["asset"] == "RAY" for o in occs):
        fail("ray_not_active_report", "RAY marked ACTIVE_REPORT")
    print("PASS ray_not_active_report")
    if any(o.get("surface") == "ACTIVE_REPORT" and o["asset"] == "GRASS" for o in occs):
        fail("grass_not_active_report", "GRASS marked ACTIVE_REPORT")
    print("PASS grass_not_active_report")
    if any(o.get("surface") == "ACTIVE_REPORT" and o["asset"] == "ORCA" for o in occs):
        fail("orca_not_onboarded_report", "ORCA marked ACTIVE_REPORT")
    print("PASS orca_not_onboarded_report")

    for o in occs:
        if o["ui_location_type"] == "hold_card" and o["asset"] == "MARKET" and o.get("metric_id"):
            fail("no_market_hold_when_ticker", o["occurrence_id"])
    print("PASS no_market_hold_when_ticker")

    for m in registry:
        if m["wallet_or_non_wallet"] == "WALLET" and m["owner"] != "GROK":
            fail("wallet_ownership_separation", m["metric_id"])
        if m["metric_type"] == "HISTORICAL" and m["historical_or_current"] != "HISTORICAL":
            fail("historical_static_separation", m["metric_id"])
        if m["metric_type"] in ("STATIC_REFERENCE", "STATIC_DECISION_THRESHOLD") and m["historical_or_current"] != "STATIC":
            fail("historical_static_separation", m["metric_id"])
        if m["metric_type"] == "DERIVED_DYNAMIC":
            if m["calculation_version"] in ("direct", None, "") or not m.get("calculation_method") or not m.get("raw_inputs"):
                fail("derived_has_method_inputs", m["metric_id"])
        if m["status"] == "CONFLICT":
            if m["value"] not in (None, "UNKNOWN"):
                fail("conflict_value_unknown", m["metric_id"])
            if not m.get("evidence_variants"):
                fail("conflict_detection", m["metric_id"])
    print("PASS wallet_ownership_separation")
    print("PASS historical_static_separation")
    print("PASS derived_has_method_inputs")
    print("PASS conflict_value_unknown")
    print("PASS conflict_detection")

    pump7 = [o["current_literal_text"] for o in occs if o.get("metric_id") == "pump.buyback.usd.7d"]
    if not pump7:
        fail("pump_buyback_7d_not_daily", "missing pump.buyback.usd.7d")
    for x in pump7:
        if re.search(r"801K|1\.0M/d|\$1\.0M$|\$1\.1M", x):
            fail("pump_buyback_7d_not_daily", x)
    print("PASS pump_buyback_7d_not_daily")

    for x in [o["current_literal_text"] for o in occs if o.get("metric_id") == "btc.etf.flow.usd.30d"]:
        if re.search(r"50D|200D|79,?337", x, re.I):
            fail("etf_30d_not_ma_or_price", x)
    if not any(o.get("metric_id") == "btc.etf.flow.usd.30d" for o in occs):
        fail("etf_30d_not_ma_or_price", "missing metric")
    print("PASS etf_30d_not_ma_or_price")

    for x in [o["current_literal_text"] for o in occs if (o.get("metric_id") or "").endswith("price.drawdown_from_ath.pct")]:
        if re.search(r"50D|200D|\bRS\b", x, re.I):
            fail("drawdown_not_ma_labels", x)
    print("PASS drawdown_not_ma_labels")

    sys.path.insert(0, str(Path(__file__).parent))
    from job1_build import TYPE_SPEC, shape_ok, detect_kind  # noqa: E402

    if summary.get("semantic_anomalies", 1) != 0:
        fail("semantic_anomaly_zero", str(summary.get("semantic_anomalies")))
    print("PASS semantic_anomaly_zero")

    for m in registry:
        rest = m["metric_id"].split(".", 1)[1]
        spec = TYPE_SPEC.get(rest)
        if not spec:
            fail("type_safety_all_metrics", f"no spec {m['metric_id']}")
        if m.get("value_kind") != spec[0]:
            fail("type_safety_all_metrics", f"value_kind {m['metric_id']}")
        for o in occs:
            if o.get("metric_id") != m["metric_id"]:
                continue
            lit = o["current_literal_text"]
            if not shape_ok(spec[2], lit):
                fail("type_safety_all_metrics", f"{m['metric_id']} {lit!r} kind={detect_kind(lit)}")
            if spec[0] == "RATIO_X" and ("$" in lit or "%" in lit):
                fail("type_safety_all_metrics", f"ratio got money/pct {lit}")
            if spec[0] == "PERCENT" and "$" in lit:
                fail("type_safety_all_metrics", f"pct got usd {lit}")
            if spec[0] in {"USD_AMOUNT", "PRICE_USD"} and "%" in lit:
                fail("type_safety_all_metrics", f"usd got pct {lit}")
            if spec[0] == "INDEX" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", lit):
                fail("type_safety_all_metrics", f"index is date {lit}")
            if spec[0] == "COUNT" and re.search(r"[A-Za-z]{4,}", lit) and "of" not in lit.lower():
                fail("type_safety_all_metrics", f"count is text {lit}")
    print("PASS type_safety_all_metrics")

    def lits(mid: str) -> list[str]:
        return [o["current_literal_text"] for o in occs if o.get("metric_id") == mid]

    lev = lits("btc.leverage.x.current")
    if not lev:
        fail("regression_btc_leverage", "missing btc.leverage.x.current")
    for x in lev:
        if "$" in x or "%" in x or re.search(r"\bBTC\b", x) or "funding" in x.lower():
            fail("regression_btc_leverage", x)
    print("PASS regression_btc_leverage")

    for x in lits("btc.oi.usd.current"):
        if "%" in x or re.search(r"\bBTC\b", x) or "×" in x:
            fail("regression_btc_oi_usd", x)
    print("PASS regression_btc_oi_usd")

    dd = lits("btc.price.drawdown_from_ath.pct")
    if not dd:
        fail("regression_btc_drawdown", "missing")
    for x in dd:
        if "$" in x or re.search(r"50D|200D|\bRS\b", x, re.I) or "%" not in x:
            fail("regression_btc_drawdown", x)
    print("PASS regression_btc_drawdown")

    for x in lits("io.funding.pct.current"):
        if "$" in x:
            fail("regression_io_funding", x)
    if any(
        "932" in o["current_literal_text"] and (o.get("metric_id") or "").endswith("funding.pct.current")
        for o in occs
    ):
        fail("regression_io_funding", "$932k on funding")
    print("PASS regression_io_funding")

    for x in lits("fart.leverage.x.current"):
        if "$" in x or "volume" in x.lower() or "last price" in x.lower():
            fail("regression_fart_leverage", x)
    print("PASS regression_fart_leverage")

    fg = lits("global.fear_greed.index.current")
    if not any(re.fullmatch(r"~?\d{1,3}", x.strip()) for x in fg):
        fail("regression_fear_greed", f"no index level in {fg}")
    for x in fg:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", x.strip()) or x.strip() in {"+1", "−1", "-1"}:
            fail("regression_fear_greed", x)
    print("PASS regression_fear_greed")

    for x in lits("global.participation.count.current"):
        if "MIXED" in x.upper():
            fail("regression_participation", x)
    print("PASS regression_participation")

    print("ALL JOB 1 SEMANTIC TESTS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
