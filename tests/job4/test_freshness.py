#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
sys.path.insert(0, str(ROOT / "tests/job4"))


def main() -> int:
    if not (FIX / "M12-rendered.html").is_file():
        subprocess.run([sys.executable, str(FIX / "build_mutations.py")], check=True, cwd=str(ROOT))
    from _helpers import run_checker

    code, report = run_checker(snapshot=FIX / "M12-snapshot.json", rendered=FIX / "M12-rendered.html", run_id="M12")
    assert code in (2, 3)

    code, report = run_checker(snapshot=FIX / "M13-snapshot.json", rendered=FIX / "M13-rendered.html", run_id="M13")
    assert code in (2, 3)

    print("test_freshness OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
