#!/usr/bin/env python3
"""Production-shape Job2 DERIVE → Job3 snapshot regression."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.build_snapshot import build_snapshot

LABELS = json.loads((ROOT / "renderer/source-labels.json").read_text())
REG_SHA = json.loads((ROOT / "tests/job3/fixtures/collector-run-baseline.json").read_text())[
    "job1_registry_sha256"
]
PLAN_SHA = json.loads((ROOT / "tests/job3/fixtures/collector-run-baseline.json").read_text())[
    "collector_plan_sha256"
]


def _job2_derive_run(*, perp_as_of: str, spot_as_of: str, perp_val: int = 9200, spot_val: int = 1000) -> dict:
    return {
        "_fixture_kind": "SYNTHETIC_TEST_ONLY",
        "run_id": "SYNTHETIC_DERIVE_SHAPE_JOB3",
        "job1_registry_sha256": REG_SHA,
        "collector_plan_sha256": PLAN_SHA,
        "facts": [
            {
                "metric_id": "btc.volume.perp.usd.24h",
                "status": "OK",
                "normalized_value": perp_val,
                "unit": "USD",
                "source_key": "binance",
                "source_as_of": perp_as_of,
                "fetched_at": perp_as_of,
                "freshness": "UNKNOWN",
                "calculation_version": "v1",
                "derivation_inputs": None,
                "error": None,
            },
            {
                "metric_id": "btc.volume.spot.usd.24h",
                "status": "OK",
                "normalized_value": spot_val,
                "unit": "USD",
                "source_key": "binance",
                "source_as_of": spot_as_of,
                "fetched_at": spot_as_of,
                "freshness": "UNKNOWN",
                "calculation_version": "v1",
                "derivation_inputs": None,
                "error": None,
            },
            {
                "metric_id": "btc.leverage.x.current",
                "status": "OK",
                "normalized_value": 9.2,
                "unit": "x",
                "source_key": None,
                "request_key": None,
                "source_field": "RATIO",
                "source_as_of": "UNKNOWN",
                "fetched_at": None,
                "raw_capture_sha256": None,
                "calculation_version": "v1",
                "derivation_inputs": ["btc.volume.perp.usd.24h", "btc.volume.spot.usd.24h"],
                "error": None,
            },
        ],
    }


def test_derive_resolves_source_as_of_from_metric_ids() -> None:
    run = _job2_derive_run(perp_as_of="2026-08-01T12:00:00Z", spot_as_of="2026-08-01T12:00:00Z")
    snap = build_snapshot(run, LABELS)
    row = snap["metrics"]["btc.leverage.x.current"]
    assert row["source_key"] is None
    assert row["derivation_inputs"] == ["btc.volume.perp.usd.24h", "btc.volume.spot.usd.24h"]
    assert row["source_as_of"] == "2026-08-01T12:00:00Z"
    assert row["source_label"] == "Derived from canonical inputs"


def test_derive_mismatched_inputs_become_unknown() -> None:
    run = _job2_derive_run(perp_as_of="2026-08-01T12:00:00Z", spot_as_of="2026-08-02T12:00:00Z")
    snap = build_snapshot(run, LABELS)
    assert snap["metrics"]["btc.leverage.x.current"]["source_as_of"] == "UNKNOWN"


def test_fixture_collector_runs_build_without_crash() -> None:
    fix = ROOT / "tests/job3/fixtures"
    for path in sorted(fix.glob("collector-run-*.json")):
        run = json.loads(path.read_text())
        snap = build_snapshot(run, LABELS)
        for mid in (
            "btc.leverage.x.current",
            "global.leverage.x.current",
            "sol.supply.net_change.tokens.per_year",
            "zec.leverage.x.current",
        ):
            row = snap["metrics"][mid]
            assert row["source_key"] is None, mid
            assert isinstance(row["derivation_inputs"], list), mid
            assert row["derivation_inputs"], mid


def main() -> int:
    test_derive_resolves_source_as_of_from_metric_ids()
    test_derive_mismatched_inputs_become_unknown()
    test_fixture_collector_runs_build_without_crash()
    print("test_snapshot_derive OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
