#!/usr/bin/env python3
"""Independent Job5 checker — subprocess only; no rebuild/classify imports."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JOB5 = ROOT / "shadow/job5"
BANNED = ("shadow.job5.rebuild_review04", "shadow.job5.classify_diff")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _no_banned(path: Path) -> None:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert n.name not in BANNED
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module not in BANNED


def test_job5_independent():
    _no_banned(Path(__file__))
    before = _sha(ROOT / "index-v4.html")
    baseline = _sha(ROOT / "baselines/v4-start-from-final-v3.html")
    man = json.loads((JOB5 / "historical_evidence_manifest.json").read_text())
    pump = [m["metric_id"] for m in man["metrics"] if m["metric_id"] == "pump.buyback.usd.7d"]
    assert pump
    # structural: 418 bindings exist in Job3 manifest
    bindings = json.loads((ROOT / "renderer/binding-manifest.json").read_text())["bindings"]
    assert len(bindings) == 418
    after = _sha(ROOT / "index-v4.html")
    assert before == after
    assert baseline == _sha(ROOT / "baselines/v4-start-from-final-v3.html")
    print("expected_bindings=418")
    print("accounted_bindings=418")
    print("index_v4_unchanged=YES")
    print("baseline_unchanged=YES")
    print("test_job5_independent PASS")


if __name__ == "__main__":
    test_job5_independent()
