#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
sys.path.insert(0, str(ROOT / "tests/job4"))


def main() -> int:
    if not (FIX / "M18-rendered.html").is_file():
        subprocess.run([sys.executable, str(FIX / "build_mutations.py")], check=True, cwd=str(ROOT))
    from _helpers import load_contract, run_checker

    contract = load_contract()
    assert contract["derive_plan_count"] == 4
    assert contract["derive_plan_count"] == len(contract["derive_rules"])

    code, report = run_checker(snapshot=FIX / "M18-snapshot.json", rendered=FIX / "M18-rendered.html", run_id="M18")
    assert code == 2
    assert any(c["category"] == "11_derived_metric_arithmetic" and c["status"] == "FAIL" for c in report["checks"])

    code, report = run_checker(snapshot=FIX / "M19-snapshot.json", rendered=FIX / "M19-rendered.html", run_id="M19")
    assert code == 3
    assert any(c["category"] == "11_derived_metric_arithmetic" and c["status"] == "COVERAGE_GAP" for c in report["checks"])

    print("test_derived OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
