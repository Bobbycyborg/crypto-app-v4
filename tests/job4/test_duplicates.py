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

    for tag in ("M04", "M05", "M06", "M15"):
        code, report = run_checker(
            snapshot=FIX / f"{tag}-snapshot.json",
            rendered=FIX / f"{tag}-rendered.html",
            run_id=tag,
        )
        assert code in (2, 3), (tag, code, report.get("failures", [])[:2])
        dup = [c for c in report["checks"] if c["category"] == "05_duplicate_consistency" and c["status"] == "FAIL"]
        perm = [c for c in report["checks"] if c["category"] == "12_permanent_regressions" and c["status"] == "FAIL"]
        spx = [c for c in report["checks"] if c["check_id"] == "12_reg_spx_price_duplicate" and c["status"] == "FAIL"]
        assert dup or perm or spx, tag
    print("test_duplicates OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
