"""Job 3 binding eligibility — identity copied from Job 1 + Job 2 only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DORMANT_ASSETS = frozenset({"RAY", "GRASS", "DRIFT", "ORCA", "BONK"})
BINDABLE_DISPOSITIONS = frozenset({"COLLECT", "DERIVE", "BLOCKED_SOURCE"})
NON_BINDABLE_CLASSIFICATIONS = frozenset(
    {
        "HISTORICAL",
        "STATIC_DECISION_THRESHOLD",
        "WALLET_OWNED",
        "CONTEXT_ONLY",
        "EVIDENCE_REFERENCE",
        "QUALITATIVE_NON_METRIC",
        "FALSE_POSITIVE",
        "LEGACY_INACTIVE",
        "PRESERVE",
    }
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_job1_job2() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    reg = {m["metric_id"]: m for m in load_json(ROOT / "metrics/metric-registry.json")["metrics"]}
    plan = {e["metric_id"]: e for e in load_json(ROOT / "collectors/collector-plan.json")["entries"]}
    manifest = load_json(ROOT / "metrics/ui-mapping-manifest.json")
    mappings = manifest["mappings"]
    return reg, plan, manifest, mappings


def mapping_eligible(mapping: dict[str, Any], reg: dict[str, Any], plan: dict[str, Any]) -> bool:
    mid = mapping.get("metric_id")
    if not mid:
        return False
    row = reg.get(mid)
    entry = plan.get(mid)
    if not row or not entry:
        return False
    asset = (mapping.get("asset") or row.get("asset") or "").upper()
    if asset in DORMANT_ASSETS:
        return False
    if row.get("owner") != "CGPT_CURSOR":
        return False
    if row.get("metric_type") != "CURRENT_DYNAMIC":
        return False
    if entry.get("disposition") not in BINDABLE_DISPOSITIONS:
        return False
    cls = mapping.get("classification") or row.get("classification")
    if cls in NON_BINDABLE_CLASSIFICATIONS:
        return False
    return True


def eligible_mappings(mappings: list[dict[str, Any]], reg: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [m for m in mappings if mapping_eligible(m, reg, plan)]
