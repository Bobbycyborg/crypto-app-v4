#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "integrity/build_report_contract.py"), "--check"],
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        return proc.returncode
    print("test_contract OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
