#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
sys.path.insert(0, str(ROOT / "tests/job4"))

from _helpers import run_checker


def main() -> int:
    snap = FIX / "golden-snapshot.json"
    html = FIX / "golden-rendered.html"
    if not snap.is_file() or not html.is_file():
        subprocess.run([sys.executable, str(FIX / "build_golden.py")], check=True, cwd=str(ROOT))
    code, report = run_checker(snapshot=snap, rendered=html, run_id="golden-pass")
    assert code == 0, (code, report.get("overall_status"), report.get("counts"))
    assert report["overall_status"] == "PASS"
    assert report["counts"]["fail"] == 0
    assert report["counts"]["coverage_gap"] == 0
    for cat in report["categories"]:
        assert report["categories"][cat].get("present"), cat
    print("test_checker_pass OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
