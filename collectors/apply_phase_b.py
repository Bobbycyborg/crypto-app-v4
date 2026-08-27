#!/usr/bin/env python3
"""Regenerate collector-plan.json after Job 2B Phase A + CGPT decisions + Phase B specs."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

IO_EMISSIONS_NOTES = (
    "Legacy pre-IDE fixed-emission tokenomics. "
    "io.net's Incentive Dynamic Engine went live 11 Jun 2026 "
    "and replaced inflation-based tokenomics with a "
    "demand-driven issuance/burn system. "
    "The historical 300M-over-20y statement must not be "
    "collected or represented as a current remaining-emissions figure."
)

SOL_STAKING_APY_NOTES = (
    "V3 sol_product liquid-staking APY sample band (4.65–5.80%) only; "
    "no recoverable live APY endpoint. Preserved as static reference."
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required_for(m: dict) -> bool:
    if m["owner"] == "GROK" or m.get("wallet_or_non_wallet") == "WALLET":
        return False
    if m["asset"] in {"RAY", "GRASS", "DRIFT"}:
        return False
    if m["metric_id"] == "io.emissions.tokens.remaining":
        return False
    if m["metric_id"] == "sol.staking.apy.pct":
        return False
    if m.get("metric_type") in {"HISTORICAL", "STATIC_DECISION_THRESHOLD", "STATIC_REFERENCE"}:
        return False
    if m.get("update_mode") in {"HISTORICAL", "STATIC_THRESHOLD"}:
        return False
    if m.get("historical_or_current") in {"HISTORICAL", "STATIC"}:
        return False
    return m.get("metric_type") == "CURRENT_DYNAMIC" and m.get("wallet_or_non_wallet") == "NON_WALLET"


def main() -> None:
    author = _load_module("author_plan", ROOT / "collectors/_author_plan.py")
    phase_b = _load_module("phase_b_specs", ROOT / "collectors/phase_b_collect_specs.py")
    reg = json.loads((ROOT / "metrics/metric-registry.json").read_text(encoding="utf-8"))

    merged_collect = dict(author.COLLECT)
    merged_collect.update(phase_b.PHASE_B_COLLECT)

    entries = []
    for m in reg["metrics"]:
        mid = m["metric_id"]
        base = {
            "metric_id": mid,
            "asset": m["asset"],
            "owner": m["owner"],
            "unit": m.get("allowed_unit") or m["unit"],
        }
        if m["owner"] == "GROK" or m.get("metric_type") == "WALLET_OWNED" or m.get("wallet_or_non_wallet") == "WALLET":
            row = {**base, "disposition": "GROK_WALLET", "source_key": None, "request_key": None,
                   "selector": None, "normalizer": None, "derivation": None, "required": False,
                   "notes": "Job 1 owner=GROK. Cursor does not collect."}
        elif m["asset"] in {"RAY", "GRASS", "DRIFT"}:
            row = {**base, "disposition": "LEGACY_INACTIVE", "source_key": None, "request_key": None,
                   "selector": None, "normalizer": None, "derivation": None, "required": False,
                   "notes": "LEGACY_INACTIVE per asset-state-overrides.json (Job 2B)."}
        elif mid == "io.emissions.tokens.remaining":
            row = {**base, "disposition": "PRESERVE", "source_key": None, "request_key": None,
                   "selector": None, "normalizer": None, "derivation": None, "required": False,
                   "notes": IO_EMISSIONS_NOTES}
        elif mid == "sol.staking.apy.pct":
            row = {**base, "disposition": "PRESERVE", "source_key": None, "request_key": None,
                   "selector": None, "normalizer": None, "derivation": None, "required": False,
                   "notes": SOL_STAKING_APY_NOTES}
        elif (
            m.get("metric_type") in {"HISTORICAL", "STATIC_DECISION_THRESHOLD", "STATIC_REFERENCE"}
            or m.get("update_mode") in {"HISTORICAL", "STATIC_THRESHOLD"}
            or m.get("historical_or_current") in {"HISTORICAL", "STATIC"}
            or mid in author.DATED_PRESERVE
        ):
            row = {**base, "disposition": "PRESERVE", "source_key": None, "request_key": None,
                   "selector": None, "normalizer": None, "derivation": None, "required": False,
                   "notes": "Historical, static, threshold, or dated event. No live collector."}
        elif mid in merged_collect:
            spec = merged_collect[mid]
            row = {**base, **spec, "required": required_for(m)}
        elif m.get("metric_type") == "CURRENT_DYNAMIC":
            row = {
                **base,
                **author.blocked(m, f"unresolved after Phase B apply: {mid}"),
                "required": True,
            }
        else:
            row = {**base, "disposition": "PRESERVE", "source_key": None, "request_key": None,
                   "selector": None, "normalizer": None, "derivation": None, "required": False,
                   "notes": "Non-dynamic Job 1 record."}

        entries.append(row)

    plan = {
        "job": "V4-JOB-2B",
        "job1_commit": "0084838bf3587be0116653ac1c0f68ff0edddcc6",
        "job1_registry_sha256": sha256_file(ROOT / "metrics/metric-registry.json"),
        "phase_b_applied": True,
        "entries": entries,
    }
    out = ROOT / "collectors/collector-plan.json"
    out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    counts = Counter(e["disposition"] for e in entries)
    blocked = [e["metric_id"] for e in entries if e["disposition"] == "BLOCKED_SOURCE"]
    print("wrote", out, "n", len(entries), dict(counts))
    if blocked:
        raise SystemExit(f"BLOCKED_SOURCE remaining: {blocked[:10]} ... ({len(blocked)} total)")


if __name__ == "__main__":
    main()
