#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
sys.path.insert(0, str(ROOT / "tests/job4"))


def main() -> int:
    if not (FIX / "M08-rendered.html").is_file():
        subprocess.run([sys.executable, str(FIX / "build_mutations.py")], check=True, cwd=str(ROOT))
    from _helpers import run_checker

    code, report = run_checker(snapshot=FIX / "M08-snapshot.json", rendered=FIX / "M08-rendered.html", run_id="M08")
    assert code == 2
    assert any(c["category"] == "06_ath_drawdown_arithmetic" and c["status"] == "FAIL" for c in report["checks"])

    code, report = run_checker(snapshot=FIX / "M10-snapshot.json", rendered=FIX / "M10-rendered.html", run_id="M10")
    assert code == 2
    assert any(c["category"] == "07_moving_average_language" and c["status"] == "FAIL" for c in report["checks"])

    code, report = run_checker(snapshot=FIX / "M11-snapshot.json", rendered=FIX / "M11-rendered.html", run_id="M11")
    assert code == 2
    assert any(c["category"] == "08_relative_strength_language" and c["status"] == "FAIL" for c in report["checks"])

    print("test_semantics OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
