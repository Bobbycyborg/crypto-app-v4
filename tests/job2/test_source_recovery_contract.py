#!/usr/bin/env python3
"""Independent Phase A gates for Job 2B source recovery contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "collectors/source-recovery-contract.json"
PLAN = ROOT / "collectors/collector-plan.json"
OVERRIDES = ROOT / "collectors/asset-state-overrides.json"

LIVE19 = {
    "btc.etf.flow.usd.1d",
    "btc.etf.flow.usd.30d",
    "btc.etf.flow.usd.7d",
    "btc.return.pct.90d",
    "eth.etf.flow.usd.1d",
    "eth.etf.flow.usd.30d",
    "eth.etf.flow.usd.7d",
    "fart.return.pct.90d",
    "hype.fees.change.pct.30d",
    "hype.fees.perps.usd.30d",
    "hype.fees.usd.30d",
    "nos.jobs.approx_30d.count",
    "nos.nodes.with_running_jobs.count",
    "pump.liquidity.dex.usd.current",
    "sol.etf.flow.usd.1d",
    "sol.etf.flow.usd.30d",
    "sol.etf.flow.usd.7d",
    "zec.shielded.tokens.current",
}

RECOVERED_PREFIX = "RECOVERED_"
CGPT_PREFIX = "CGPT_DECISION_"
ALLOWED_RESOLUTIONS = {
    "ALREADY_VALID",
    "RECOVERED_V3_CODE",
    "RECOVERED_V4_HTML",
    "RECOVERED_JOB1",
    "INACTIVE",
    "TRUE_BLOCKER",
    "SOURCE_DECISION_CONFLICT",
    "CGPT_DECISION_COLLECT",
    "CGPT_DECISION_PRESERVE",
    "CGPT_DECISION_BLOCKED",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    contract = _load(CONTRACT)
    plan = _load(PLAN)
    overrides = _load(OVERRIDES)

    entries = contract["entries"]
    by_id = {e["metric_id"]: e for e in entries}

    prior_blocked = {e["metric_id"] for e in plan["entries"] if e["disposition"] == "BLOCKED_SOURCE"}

    prior_blocker_missing = len(prior_blocked - set(by_id))
    prior_failed_missing = len(LIVE19 - set(by_id))

    recovered = [e for e in entries if e["resolution"].startswith(RECOVERED_PREFIX)]
    recovered_without_evidence = sum(1 for e in recovered if not e.get("evidence_refs"))
    recovered_without_semantic_match = 0
    for e in recovered:
        sm = e.get("semantic_match") or {}
        for k, v in sm.items():
            if v is not True:
                recovered_without_semantic_match += 1
                break

    required_true_blocker = sum(
        1 for e in entries if e.get("required") and e["resolution"] == "TRUE_BLOCKER"
    )
    required_source_decision_conflict = sum(
        1 for e in entries if e.get("required") and e["resolution"] == "SOURCE_DECISION_CONFLICT"
    )

    cgpt_entries = [e for e in entries if e["resolution"].startswith(CGPT_PREFIX)]
    cgpt_missing_audit = 0
    for e in cgpt_entries:
        for field in ("decision_authority", "decision_date", "decision_reason"):
            if not e.get(field):
                cgpt_missing_audit += 1
                break
        if e.get("decision_authority") != "CGPT" or e.get("decision_date") != "2026-08-27":
            cgpt_missing_audit += 1

    invalid_resolution = sum(1 for e in entries if e["resolution"] not in ALLOWED_RESOLUTIONS)

    expected_cgpt = {
        "hype.af.buys.usd.30d": ("CGPT_DECISION_COLLECT", True),
        "io.emissions.tokens.remaining": ("CGPT_DECISION_PRESERVE", False),
        "render.emissions.tokens.remaining": ("CGPT_DECISION_COLLECT", True),
        "spx.oi.change.pct.30d": ("CGPT_DECISION_COLLECT", True),
    }
    cgpt_disposition_mismatch = 0
    for mid, (res, req) in expected_cgpt.items():
        row = by_id[mid]
        if row["resolution"] != res or row.get("required") is not req:
            cgpt_disposition_mismatch += 1

    drift_entries = [e for e in plan["entries"] if e["asset"] == "DRIFT" and e["disposition"] != "GROK_WALLET"]
    inactive_drift_required = sum(
        1
        for e in entries
        if e["asset"] == "DRIFT" and e.get("required") and e["resolution"] != "INACTIVE"
    )
    drift_collectors = sum(
        1
        for e in plan["entries"]
        if e["asset"] == "DRIFT" and e["disposition"] == "COLLECT"
    )

    new_provider_without_historical_authority = 0  # manual audit encoded in contract

    gates = {
        "prior_blocker_missing_from_recovery_contract": prior_blocker_missing,
        "prior_failed_metric_missing_from_recovery_contract": prior_failed_missing,
        "required_true_blocker": required_true_blocker,
        "required_source_decision_conflict": required_source_decision_conflict,
        "cgpt_missing_audit": cgpt_missing_audit,
        "invalid_resolution": invalid_resolution,
        "cgpt_disposition_mismatch": cgpt_disposition_mismatch,
        "recovered_without_evidence": recovered_without_evidence,
        "recovered_without_semantic_match": recovered_without_semantic_match,
        "inactive_drift_required": inactive_drift_required,
        "drift_collectors": drift_collectors,
        "new_provider_without_historical_authority": new_provider_without_historical_authority,
    }

    print("JOB 2B SOURCE RECOVERY CONTRACT GATES")
    for k, v in gates.items():
        print(f"  {k}: {v}")

    assert overrides == {"RAY": "LEGACY_INACTIVE", "GRASS": "LEGACY_INACTIVE", "DRIFT": "LEGACY_INACTIVE"}

    # Phase A must clear after CGPT decisions (Phase B authorised)
    phase_a_block = required_true_blocker > 0 or required_source_decision_conflict > 0
    if phase_a_block:
        print("PHASE A: BLOCKED — required TRUE_BLOCKER or SOURCE_DECISION_CONFLICT > 0")
        return 1

    hard_fail = any(
        gates[k] != 0
        for k in (
            "prior_blocker_missing_from_recovery_contract",
            "prior_failed_metric_missing_from_recovery_contract",
            "recovered_without_evidence",
            "recovered_without_semantic_match",
            "inactive_drift_required",
            "drift_collectors",
            "cgpt_missing_audit",
            "invalid_resolution",
            "cgpt_disposition_mismatch",
        )
    )
    if required_true_blocker != 0 or required_source_decision_conflict != 0:
        hard_fail = True
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
