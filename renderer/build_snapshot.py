#!/usr/bin/env python3
"""Build Job 3 render snapshot from Job 2 collector-run.json — no network."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

NON_OK = frozenset(
    {
        "UNKNOWN",
        "SOURCE_UNAVAILABLE",
        "AUTH_MISSING",
        "SOURCE_SCHEMA_MISMATCH",
        "VALUE_MISSING",
        "VALUE_INVALID",
        "DERIVATION_BLOCKED",
        "BLOCKED_SOURCE",
    }
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_label(source_key: str | None, labels: dict[str, str]) -> str:
    if not source_key:
        return "Derived from canonical inputs"
    if source_key not in labels:
        raise SystemExit(f"UNKNOWN_SOURCE_LABEL:{source_key}")
    return labels[source_key]


def _derived_as_of(inputs: list[Any], facts_by_id: dict[str, dict[str, Any]]) -> str:
    if not inputs:
        return "UNKNOWN"
    as_ofs: set[str] = set()
    for inp in inputs:
        if isinstance(inp, str):
            fact = facts_by_id.get(inp)
            if not fact:
                return "UNKNOWN"
            as_of = fact.get("source_as_of")
        elif isinstance(inp, dict):
            as_of = inp.get("source_as_of")
        else:
            return "UNKNOWN"
        if not as_of or as_of == "UNKNOWN":
            return "UNKNOWN"
        as_ofs.add(as_of)
    if len(as_ofs) == 1:
        return next(iter(as_ofs))
    return "UNKNOWN"


def build_snapshot(collector_run: dict[str, Any], labels: dict[str, str]) -> dict[str, Any]:
    reg_path = ROOT / "metrics/metric-registry.json"
    plan_path = ROOT / "collectors/collector-plan.json"
    reg_sha = _sha256_file(reg_path)
    plan_sha = _sha256_file(plan_path)
    if collector_run.get("job1_registry_sha256") != reg_sha:
        raise SystemExit("SNAPSHOT_UPSTREAM_HASH_MISMATCH: job1_registry_sha256")
    if collector_run.get("collector_plan_sha256") != plan_sha:
        raise SystemExit("SNAPSHOT_UPSTREAM_HASH_MISMATCH: collector_plan_sha256")

    reg = {m["metric_id"]: m for m in json.loads(reg_path.read_text())["metrics"]}
    plan = {e["metric_id"]: e for e in json.loads(plan_path.read_text())["entries"]}
    facts_by_id: dict[str, dict[str, Any]] = {}
    for fact in collector_run.get("facts", []):
        mid = fact["metric_id"]
        if mid in facts_by_id:
            raise SystemExit(f"duplicate metric_id in collector-run: {mid}")
        facts_by_id[mid] = fact

    metrics: dict[str, Any] = {}
    for mid, fact in facts_by_id.items():
        row = reg.get(mid)
        entry = plan.get(mid)
        if not row or not entry:
            raise SystemExit(f"metric not in registry/plan: {mid}")
        status = fact.get("status", "UNKNOWN")
        unit = fact.get("unit") or row.get("unit")
        if entry.get("unit") and unit != entry.get("unit"):
            raise SystemExit(f"UNIT_MISMATCH:{mid}")
        source_key = fact.get("source_key")
        derivation_inputs = fact.get("derivation_inputs")
        if entry.get("disposition") == "DERIVE" and not source_key:
            source_label = "Derived from canonical inputs"
            source_as_of = _derived_as_of(derivation_inputs or [], facts_by_id)
        else:
            source_label = _source_label(source_key, labels) if status == "OK" else "UNKNOWN"
            source_as_of = fact.get("source_as_of") or "UNKNOWN"
        metrics[mid] = {
            "metric_id": mid,
            "status": status,
            "normalized_value": fact.get("normalized_value"),
            "unit": unit,
            "source_key": source_key,
            "source_label": source_label,
            "source_as_of": source_as_of,
            "fetched_at": fact.get("fetched_at") or "UNKNOWN",
            "freshness": fact.get("freshness") or "UNKNOWN",
            "calculation_version": fact.get("calculation_version"),
            "derivation_inputs": derivation_inputs,
            "error": fact.get("error"),
        }
        if status in NON_OK:
            metrics[mid]["normalized_value"] = None

    return {
        "schema_version": "job3.v1",
        "source_run_id": collector_run.get("run_id", "UNKNOWN"),
        "source_collector_run_sha256": hashlib.sha256(json.dumps(collector_run, sort_keys=True).encode()).hexdigest(),
        "job1_registry_sha256": reg_sha,
        "collector_plan_sha256": plan_sha,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": metrics,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--collector-run", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    run_path = Path(args.collector_run)
    labels = json.loads((ROOT / "renderer/source-labels.json").read_text())
    run = json.loads(run_path.read_text())
    snap = build_snapshot(run, labels)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(snap, indent=2) + "\n")
    tmp.replace(out)
    print(f"wrote {out} metrics={len(snap['metrics'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
