#!/usr/bin/env python3
"""Independent Job 3 checker — no production renderer imports."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
    assert manifest["eligible_occurrences"] == len(manifest["bindings"]) == 418
    assert _sha(ROOT / "metrics/metric-registry.json") == manifest["job1_registry_sha256"]
    for b in manifest["bindings"]:
        assert b.get("owner") != "GROK"
        assert (b.get("asset") or "").upper() not in {"RAY", "GRASS", "DRIFT"}
    for py in (ROOT / "renderer").glob("*.py"):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    assert "requests" not in n.name
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "requests" not in node.module
    for fix in (ROOT / "tests/job3/fixtures").glob("collector-run-*.json"):
        data = json.loads(fix.read_text())
        assert data.get("_fixture_kind") == "SYNTHETIC_TEST_ONLY" or "SYNTHETIC" in data.get("run_id", "")
    print("test_job3_independent OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
