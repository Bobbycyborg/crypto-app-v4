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

    print("ALL JOB 1 SEMANTIC TESTS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
