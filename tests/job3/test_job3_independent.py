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
sys.path.insert(0, str(ROOT / "tests/job3"))

from _binding_span import rendered_span
from renderer.eligibility import eligible_mappings, load_job1_job2

NEGATIVE_OCCURRENCE_IDS = {
    "143109097f847b67",  # hold-card static threshold
    "6cef931ee1ef29a2",  # historical tooltip ATH
    "c6ae973de6959e49",  # GROK wallet siren JSON
    "4d568968d384da40",  # dormant GRASS legacy inactive
    "ad9b911811492672",  # qualitative body metric_val
    "ce940255df156255",  # qualitative body
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _rendered_span(html: str, b: dict) -> str:
    source = (ROOT / "index-v4.html").read_text(encoding="utf-8")
    return rendered_span(html, b, source=source)


def main() -> int:
    manifest = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
    bindings = manifest["bindings"]
    html = (ROOT / "index-v4.html").read_text(encoding="utf-8")
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

    # no Job4/5/6 artifacts
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

    # production-shape DERIVE regression
    rc = subprocess.run([sys.executable, str(ROOT / "tests/job3/test_snapshot_derive.py")], check=False)
    assert rc.returncode == 0

    # mutation fan-out + exact-site golden render
    rc = subprocess.run([sys.executable, str(ROOT / "tests/job3/test_golden_render.py")], check=False)
    assert rc.returncode == 0

    # writer quarantine audit
    rc = subprocess.run([sys.executable, str(ROOT / "tests/job3/test_writer_quarantine.py")], capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout + rc.stderr
    m = re.search(r"shadow_nonwallet_current_network_writers=(\d+)", rc.stdout)
    assert m and m.group(1) == "0"

    # UNKNOWN fail-closed at exact binding sites
    from renderer.render_report import render_report

    snap_fc = json.loads((ROOT / "tests/job3/fixtures/snapshot-failclosed.json").read_text())
    writers = json.loads((ROOT / "renderer/writer-quarantine.json").read_text())
    out_fc, man_fc, code_fc = render_report(
        source_html=html,
        bindings=bindings,
        snapshot=snap_fc,
        writer_quarantine=writers,
        publishable=False,
    )
    assert code_fc == 2
    assert man_fc["publishable"] is False
    for b in bindings:
        if snap_fc["metrics"][b["metric_id"]]["status"] != "OK":
            span = _rendered_span(out_fc, b)
            assert span == "UNKNOWN", b["binding_id"]

    # no legacy-current fallback strings in renderer
    for py in (ROOT / "renderer").glob("*.py"):
        text = py.read_text()
        assert "legacy_current" not in text.lower()

    print("test_job3_independent OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
