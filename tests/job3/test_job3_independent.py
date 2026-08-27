#!/usr/bin/env python3
"""Independent Job 3 checker — no production renderer imports."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.eligibility import eligible_mappings, load_job1_job2

BANNED_IMPORT_PREFIXES = (
    "renderer.render_report",
    "renderer.build_snapshot",
    "renderer.formatters",
    "renderer.build_binding_manifest",
)

NEGATIVE_OCCURRENCE_IDS = {
    "143109097f847b67",
    "6cef931ee1ef29a2",
    "c6ae973de6959e49",
    "4d568968d384da40",
    "ad9b911811492672",
    "ce940255df156255",
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _assert_no_banned_imports(path: Path) -> int:
    tree = ast.parse(path.read_text())
    hits = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if any(n.name == p or n.name.startswith(p + ".") for p in BANNED_IMPORT_PREFIXES):
                    hits += 1
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(node.module == p or node.module.startswith(p + ".") for p in BANNED_IMPORT_PREFIXES):
                hits += 1
    return hits


def main() -> int:
    self_path = Path(__file__)
    prod_imports = _assert_no_banned_imports(self_path)
    print(f"independent_checker_production_imports={prod_imports}")
    assert prod_imports == 0

    manifest = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
    bindings = manifest["bindings"]
    reg, plan, _manifest_meta, maps = load_job1_job2()
    elig = eligible_mappings(maps, reg, plan)
    elig_pairs = {(m["metric_id"], m["match"]["occurrence_id"]) for m in elig}
    bound_pairs = {(b["metric_id"], b["job1_occurrence_id"]) for b in bindings}
    bound_occ = {b["job1_occurrence_id"] for b in bindings}

    assert manifest["eligible_occurrences"] == len(bindings) == 418
    assert len(elig) == 418
    assert elig_pairs == bound_pairs
    assert _sha(ROOT / "metrics/metric-registry.json") == manifest["job1_registry_sha256"]
    assert _sha(ROOT / "index-v4.html") == manifest["source_html_sha256"]

    for rel in ("tests/job4", "tests/job5", "tests/job6", "renderer/job4", "renderer/job5", "renderer/job6"):
        assert not (ROOT / rel).exists(), rel

    markup = sum(
        1
        for b in bindings
        if b["target_kind"] == "HTML_TEXT" and ("<" in b["source_literal"] or ">" in b["source_literal"])
    )
    assert markup == 0
    print(f"markup_inside_HTML_TEXT_binding={markup}")
    print(f"binding_crosses_tag_boundary={markup}")

    anchors = [b["anchor_sha256"] for b in bindings]
    assert len(anchors) == len(set(anchors))

    for b in bindings:
        assert b.get("owner") != "GROK"
        assert (b.get("asset") or "").upper() not in {"RAY", "GRASS", "DRIFT"}
        cls = b.get("occurrence_classification")
        assert cls not in {"HISTORICAL", "STATIC_DECISION_THRESHOLD", "WALLET_OWNED", "PRESERVE"}

    for oid in NEGATIVE_OCCURRENCE_IDS:
        assert oid not in bound_occ, oid

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
        for mid in (
            "btc.leverage.x.current",
            "global.leverage.x.current",
            "sol.supply.net_change.tokens.per_year",
            "zec.leverage.x.current",
        ):
            fact = next(f for f in data["facts"] if f["metric_id"] == mid)
            assert fact.get("source_key") is None, mid
            assert isinstance(fact.get("derivation_inputs"), list), mid

    suites = [
        "tests/job3/test_snapshot_derive.py",
        "tests/job3/test_formatter_roundtrip.py",
        "tests/job3/test_golden_render.py",
        "tests/job3/test_renderer_fail_closed.py",
        "tests/job3/test_writer_quarantine.py",
    ]
    for rel in suites:
        rc = subprocess.run([sys.executable, str(ROOT / rel)], capture_output=True, text=True)
        assert rc.returncode == 0, f"{rel} failed:\n{rc.stdout}\n{rc.stderr}"

    rc = subprocess.run([sys.executable, str(ROOT / "tests/job3/test_writer_quarantine.py")], capture_output=True, text=True)
    m = re.search(r"shadow_nonwallet_current_network_writers=(\d+)", rc.stdout)
    assert m and m.group(1) == "0"

    for py in (ROOT / "renderer").glob("*.py"):
        assert "legacy_current" not in py.read_text().lower()

    print("test_job3_independent OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
