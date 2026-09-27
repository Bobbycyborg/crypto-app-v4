"""Hand figures the pull must not overwrite. Renderer, contract, and checker all read this file."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config" / "overrides.json"


def load_overrides(report_number: str | None = None) -> list[dict]:
    if not PATH.exists():
        return []
    rows = json.loads(PATH.read_text(encoding="utf-8")).get("overrides") or []
    if report_number is None:
        return list(rows)
    return [row for row in rows if str(row.get("report")) == str(report_number)]


def apply_overrides(snapshot: dict, report_number: str) -> dict:
    snap = deepcopy(snapshot)
    rows = load_overrides(report_number)
    snap["overrides"] = rows
    metrics = snap.setdefault("metrics", {})
    for row in rows:
        mid = row["metric_id"]
        current = dict(metrics.get(mid) or {})
        current["normalized_value"] = row["value"]
        current["status"] = "OK"
        current["override_reason"] = row["reason"]
        metrics[mid] = current
    return snap
