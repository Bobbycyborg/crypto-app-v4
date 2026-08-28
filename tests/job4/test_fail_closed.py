#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
sys.path.insert(0, str(ROOT / "tests/job4"))


def main() -> int:
    if not (FIX / "golden-snapshot.json").is_file():
        subprocess.run([sys.executable, str(FIX / "build_golden.py")], check=True, cwd=str(ROOT))
    subprocess.run([sys.executable, str(FIX / "build_mutations.py")], check=True, cwd=str(ROOT))
    from _helpers import run_checker

    code, report = run_checker(
        snapshot=FIX / "M20-snapshot.json",
        rendered=FIX / "M20-rendered.html",
        run_id="M20",
    )
    assert code == 2, code
    fails = [c for c in report["checks"] if c["status"] == "FAIL" and "btc.price.usd.live" in c.get("metric_ids", [])]
    assert fails, report.get("failures", [])[:3]

    code, report = run_checker(
        snapshot=FIX / "M21-snapshot.json",
        rendered=FIX / "M21-rendered.html",
        run_id="M21",
    )
    assert code == 0, (code, report.get("overall_status"), report.get("failures", [])[:3])

    code, report = run_checker(snapshot=FIX / "M02-snapshot.json", rendered=FIX / "M02-rendered.html", run_id="M02")
    assert code == 3

    code, report = run_checker(
        snapshot=FIX / "M03-snapshot.json",
        rendered=FIX / "M03-rendered.html",
        contract=FIX / "M03-contract.json",
        run_id="M03",
    )
    assert code == 3
    assert "04_bind_intentionally_absent_probe" in report.get("missing_check_ids", [])
    assert report["categories"]["04_rendered_binding_consistency"]["present"]

    code, report = run_checker(
        snapshot=FIX / "M22-snapshot.json",
        rendered=FIX / "M22-rendered.html",
        bindings=FIX / "M22-manifest.json",
        contract=FIX / "M22-contract.json",
        run_id="M22",
    )
    assert code == 4, code
    assert any(c["check_id"] == "01_lineage_07_manifest_source_actual" and c["status"] == "FAIL" for c in report["checks"])

    code, report = run_checker(
        snapshot=FIX / "M23-snapshot.json",
        rendered=FIX / "M23-rendered.html",
        source_html=FIX / "M23-source.html",
        run_id="M23",
    )
    assert code == 4, code
    assert any(c["check_id"] == "01_lineage_04_source_html_contract" and c["status"] == "FAIL" for c in report["checks"])

    print("test_fail_closed OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
