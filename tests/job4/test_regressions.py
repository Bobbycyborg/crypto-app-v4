#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
sys.path.insert(0, str(ROOT / "tests/job4"))


def main() -> int:
    if not (FIX / "M04-rendered.html").is_file():
        subprocess.run([sys.executable, str(FIX / "build_mutations.py")], check=True, cwd=str(ROOT))
    from _helpers import run_checker
    sys.path.insert(0, str(FIX))
    from build_mutations import MUTATION_EXPECTATIONS

    caught = 0
    for mid, exp in MUTATION_EXPECTATIONS.items():
        snap = FIX / f"{mid}-snapshot.json"
        html = FIX / f"{mid}-rendered.html"
        if not snap.is_file() or not html.is_file():
            continue
        code, report = run_checker(snapshot=snap, rendered=html, run_id=mid)
        if exp["overall"] == "PASS":
            if report["overall_status"] == "PASS":
                caught += 1
        elif exp["overall"] == "FAIL" and code == 2:
            caught += 1
        elif exp["overall"] == "COVERAGE_GAP" and code == 3:
            caught += 1
        elif exp["overall"] == "FAIL" and exp.get("check_id"):
            chk = exp["check_id"]
            if any(c["check_id"] == chk and c["status"] == "FAIL" for c in report["checks"]):
                caught += 1
    assert caught >= 20, caught
    print("test_regressions OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
