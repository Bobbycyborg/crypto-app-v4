#!/usr/bin/env python3
"""Replay provenance + later-data rejection + mutation/deletion."""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JOB5 = ROOT / "shadow/job5"
sys.path.insert(0, str(JOB5))
from build_historical_evidence_facts import build_facts  # noqa: E402

ARCHIVE = (ROOT.parent / "_Old:archive/crypto-app-v3").resolve()
PLAN = {e["metric_id"]: e for e in json.loads((ROOT / "collectors/collector-plan.json").read_text())["entries"]}


def _pump_manifest():
    man = json.loads((JOB5 / "historical_evidence_manifest.json").read_text())
    ids = {
        "pump.buyback.usd.7d",
        "pump.buyback.usd.1d",
        "pump.buyback.usd_per_day.current",
        "pump.revenue.usd.7d",
        "pump.revenue.usd_per_day.current",
    }
    return {"metrics": [m for m in man["metrics"] if m["metric_id"] in ids]}


def test_replay_provenance():
    man = _pump_manifest()
    out = build_facts(manifest=man, archive_root=ARCHIVE, plan=PLAN)
    by = {f["metric_id"]: f for f in out["facts"]}
    assert by["pump.buyback.usd.7d"]["normalized_value"] in (6760818, 6760818.0)
    assert by["pump.buyback.usd.7d"]["raw_capture_sha256"]
    side = {s["metric_id"]: s for s in out["sidecars"]}
    assert side["pump.buyback.usd.7d"]["evidence_mode"] == "ARCHIVED_EXTRACTED_SOURCE_EVIDENCE"
    assert side["pump.buyback.usd.7d"]["raw_http_capture_available"] is False
    assert "RAW_REPLAY_CAPTURE" not in json.dumps(out["sidecars"])
    assert by["pump.buyback.usd.7d"]["source_as_of"].startswith("2026-08-25")
    print("test_replay_provenance PASS")


def test_mutation_and_deletion_and_later():
    src = ARCHIVE / "reports/2026-08-25/pump-market-refresh/FETCH-SNAPSHOT.json"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        reports = td / "reports/2026-08-25/pump-market-refresh"
        reports.mkdir(parents=True)
        dest = reports / "FETCH-SNAPSHOT.json"
        doc = json.loads(src.read_text())
        doc["_fixture_kind"] = "SYNTHETIC_TEST_ONLY"
        orig = doc["defillama"]["buyback_burn"]["total_7d_usd"]
        doc["defillama"]["buyback_burn"]["total_7d_usd"] = orig + 1
        dest.write_text(json.dumps(doc))
        man = _pump_manifest()
        mutated = build_facts(manifest=man, archive_root=td, plan=PLAN)
        mval = [f["normalized_value"] for f in mutated["facts"] if f["metric_id"] == "pump.buyback.usd.7d"][0]
        assert mval != orig

        del doc["defillama"]["buyback_burn"]["total_7d_usd"]
        dest.write_text(json.dumps(doc))
        try:
            build_facts(manifest=man, archive_root=td, plan=PLAN)
            raise SystemExit("deletion should fail")
        except RuntimeError as exc:
            assert "ARCHIVE_FIELD_MISSING" in str(exc)

        later = ROOT / "runtime-NOT-FOR-GH/job2/20260826T164605Z_d26f8f0a/collector-run.json"
        man2 = copy.deepcopy(man)
        man2["metrics"][0]["archive_path"] = str(later.relative_to(ROOT)) if False else "later.json"
        (td / "later.json").write_text(later.read_text() if later.is_file() else "{}")
        man2["metrics"] = [
            {
                **man["metrics"][0],
                "archive_path": "later.json",
                "archive_field": "/facts/0",
                "fetched_at_field": None,
            }
        ]
        # fetched_at absent + 26 Aug in path of original later file: copy name
        later_dir = td / "20260826-run"
        later_dir.mkdir()
        payload = {"defillama": {"buyback_burn": {"total_7d_usd": 7096242}, "fetched_at": "2026-08-26T16:46:05Z"}}
        (later_dir / "FETCH.json").write_text(json.dumps(payload))
        man3 = {
            "metrics": [
                {
                    **man["metrics"][0],
                    "archive_path": "20260826-run/FETCH.json",
                    "archive_field": "/defillama/buyback_burn/total_7d_usd",
                    "fetched_at_field": "/defillama/fetched_at",
                }
            ]
        }
        try:
            build_facts(manifest=man3, archive_root=td, plan=PLAN)
            raise SystemExit("later data should be rejected")
        except RuntimeError as exc:
            assert "LATER_DATA_REJECTED" in str(exc)
    print("test_replay_provenance extras PASS")


if __name__ == "__main__":
    test_replay_provenance()
    test_mutation_and_deletion_and_later()
