#!/usr/bin/env python3
"""One command for the next report.

Writes a candidate file only. Replaces the live page only after every check passes.
Does not push. Does not walk wallets unless --walk is passed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderer.report_config import load_report

LIVE = ROOT / "index-v4.html"
PIPELINE = ("collectors", "renderer", "integrity", "lib", "config", "make_report.py")


def _git_dirty() -> list[str]:
    out = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    dirty = []
    for line in out.splitlines():
        path = line[3:].strip()
        if path == "index-v4.html" or path.startswith("tests/job4/fixtures/"):
            continue
        if any(path == name or path.startswith(name + "/") for name in PIPELINE):
            dirty.append(path)
    return dirty


def preflight() -> int:
    cfg = load_report()
    dirty = _git_dirty()
    if dirty:
        print("preflight failed. Pipeline files are still edited:", file=sys.stderr)
        for path in dirty:
            print(f"  {path}", file=sys.stderr)
        return 2
    print(f"preflight ok. Next report {cfg['report_number']} on {cfg['report_date']}.")
    print("Live page stays index-v4.html. This command will not touch it unless --promote.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue the next crypto report")
    parser.add_argument("--walk", action="store_true", help="Walk held wallets. Off unless you pass this.")
    parser.add_argument("--promote", action="store_true", help="Replace the live page only after the gates pass.")
    args = parser.parse_args()
    code = preflight()
    if code:
        return code
    cfg = load_report()
    number = cfg["report_number"]
    candidate = ROOT / "runtime-NOT-FOR-GH" / f"candidate-{number}.html"
    print("Next steps, in order:")
    print("  1. collectors/run_collectors.py --live")
    print("  2. renderer/build_snapshot.py  (refuses a partial pull unless you name the failed metrics)")
    print(f"  3. renderer/build_binding_manifest.py --html the previous report --out the candidate manifest")
    print(f"  4. renderer/render_report.py --out {candidate}")
    print("  5. wrap stance paragraphs as MANUAL zones")
    if args.walk:
        print("  6. wallet walk into state/siren-state.json, then embed that file")
    else:
        print("  6. wallet walk skipped. Pass --walk when you want it. State file is not rebuilt here.")
    print("  7. integrity checker, then integrity/stale_gate.py")
    if args.promote:
        print("  8. promote is refused until a candidate has passed both gates.")
        return 2
    print("  8. promote stays off. The live page was not changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
