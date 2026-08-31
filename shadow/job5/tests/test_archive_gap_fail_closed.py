#!/usr/bin/env python3
"""Archive-gap metrics must become UNKNOWN — no old Review04 numeric survives."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shadow/job5"))
from rebuild_review04 import apply_archive_gaps  # noqa: E402

REPRESENTATIVE = (
    "btc.etf.flow.usd.7d",
    "btc.price.drawdown_from_ath.pct",
    "sol.tps.all.current",
    "hype.oi.token.usd.current",
    "nos.jobs.running.count",
)


def test_archive_gap_fail_closed():
    plan = json.loads((ROOT / "collectors/collector-plan.json").read_text())
    gap_man = json.loads((ROOT / "shadow/job5/archive_gap_manifest.json").read_text())
    gap_ids = {m["metric_id"] for m in gap_man["metrics"]}
    assert len(gap_ids) == 80
    facts = []
    for e in plan["entries"]:
        facts.append(
            {
                "metric_id": e["metric_id"],
                "status": "OK",
                "normalized_value": 12345.67,
                "error": None,
            }
        )
    run = {"facts": facts}
    out, applied = apply_archive_gaps(run, gap_man, plan)
    assert len(applied) == 80
    by_id = {f["metric_id"]: f for f in out["facts"]}
    for mid in REPRESENTATIVE:
        assert mid in gap_ids
        rec = by_id[mid]
        assert rec["status"] == "UNKNOWN"
        assert rec["normalized_value"] is None
        assert rec["error"] == "HISTORICAL_SOURCE_ARCHIVE_GAP"
    for mid in gap_ids:
        rec = by_id[mid]
        assert rec["status"] == "UNKNOWN"
        assert rec["normalized_value"] is None
        assert rec["error"] == "HISTORICAL_SOURCE_ARCHIVE_GAP"
    print("test_archive_gap_fail_closed PASS")


if __name__ == "__main__":
    test_archive_gap_fail_closed()
