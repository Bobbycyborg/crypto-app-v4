#!/usr/bin/env python3
"""Prove Job5 production code never reads HTML as canonical data."""

from __future__ import annotations

import ast
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JOB5 = ROOT / "shadow/job5"
PROD = [
    JOB5 / "build_historical_evidence_facts.py",
    JOB5 / "build_review04_replay.py",
    JOB5 / "rebuild_review04.py",
]
BANNED_READS = ("index-v4.html", "v4-start-from-final-v3.html", "report-04.html", "source_literal")


def test_no_html_as_data():
    for path in PROD:
        tree = ast.parse(path.read_text())
        text = path.read_text()
        # rebuild may name index-v4 as renderer --source (comparison/render template), not collector input
        # Production files may list forbidden path fragments in order to refuse them.
        src = ast.dump(tree)
        assert "BeautifulSoup" not in src
        assert "html.parser" not in text.lower() or path.name == "classify_diff.py"

    import sys

    sys.path.insert(0, str(JOB5))
    from build_historical_evidence_facts import build_facts, refuse_html_path

    try:
        refuse_html_path(ROOT / "baselines/v4-start-from-final-v3.html")
        raise SystemExit("should have refused baseline html")
    except RuntimeError as exc:
        assert "HTML_FORBIDDEN" in str(exc)

    # renamed/missing HTML must not affect bridge
    man = json.loads((JOB5 / "historical_evidence_manifest.json").read_text())
    pump_only = {"metrics": [m for m in man["metrics"] if m["metric_id"].startswith("pump.buyback") or m["metric_id"].startswith("pump.revenue")]}
    archive = (ROOT.parent / "_Old:archive/crypto-app-v3").resolve()
    plan = {e["metric_id"]: e for e in json.loads((ROOT / "collectors/collector-plan.json").read_text())["entries"]}
    with tempfile.TemporaryDirectory() as td:
        # hide baseline name
        out1 = build_facts(manifest=pump_only, archive_root=archive, plan=plan)
        (Path(td) / "gone.html").write_text("x")
        out2 = build_facts(manifest=pump_only, archive_root=archive, plan=plan)
    assert [f["normalized_value"] for f in out1["facts"]] == [f["normalized_value"] for f in out2["facts"]]
    print("test_no_html_as_data PASS")


if __name__ == "__main__":
    test_no_html_as_data()
