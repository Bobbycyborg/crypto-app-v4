#!/usr/bin/env python3
"""Walk held wallets onto a candidate page. Never the live page."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.v3.siren_watch import apply_index, run_check


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Candidate HTML. index-v4.html is refused.")
    args = parser.parse_args()
    target = Path(args.target)
    if target.name == "index-v4.html" or target.resolve() == (ROOT / "index-v4.html").resolve():
        print("refusing to write index-v4.html", file=sys.stderr)
        return 2
    bundle = run_check()
    apply_index(bundle, target=target)
    print(f"wrote wallet lines to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
