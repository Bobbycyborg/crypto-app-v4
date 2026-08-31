#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
sys.path.insert(0, str(ROOT / "tests/job4"))
sys.path.insert(0, str(FIX))


def main() -> int:
    subprocess.run([sys.executable, str(FIX / "build_mutations.py")], check=True, cwd=str(ROOT))
    from _helpers import run_checker
    from build_mutations import MUTATION_EXPECTATIONS

    assert len(MUTATION_EXPECTATIONS) == 33
    exact = 0
    missing = 0
    wrong_status = 0
    wrong_check_id = 0
    for mid in [f"M{i:02d}" for i in range(1, 34)]:
        exp = MUTATION_EXPECTATIONS[mid]
        snap = FIX / f"{mid}-snapshot.json"
        html = FIX / f"{mid}-rendered.html"
        if not snap.is_file() or not html.is_file():
            raise FileNotFoundError(f"missing mutation fixture {mid}")
        kwargs = {"snapshot": snap, "rendered": html, "run_id": mid}
        if exp.get("contract"):
            kwargs["contract"] = FIX / exp["contract"]
        if exp.get("bindings"):
            kwargs["bindings"] = FIX / exp["bindings"]
        if exp.get("source_html"):
            kwargs["source_html"] = FIX / exp["source_html"]
        code, report = run_checker(**kwargs)
        ok = True
        if code != exp["exit_code"]:
            ok = False
            wrong_status += 1
            print(f"{mid} exit {code} != {exp['exit_code']}")
        if report.get("overall_status") != exp["overall"]:
            ok = False
            wrong_status += 1
            print(f"{mid} overall {report.get('overall_status')} != {exp['overall']}")
        cid = exp["check_id"]
        hit = next((c for c in report["checks"] if c["check_id"] == cid), None)
        if hit is None or hit["status"] != exp["check_status"] or hit["category"] != exp["category"]:
            ok = False
            wrong_check_id += 1
            print(f"{mid} check {cid} {hit}")
        if ok:
            exact += 1
    print(
        f"mutation_total=33 mutation_executed={33 - missing} "
        f"mutation_exact_matches={exact} mutation_missing={missing} "
        f"mutation_wrong_status={wrong_status} mutation_wrong_check_id={wrong_check_id}"
    )
    assert missing == 0
    assert exact == 33
    assert wrong_status == 0
    assert wrong_check_id == 0
    print("test_regressions OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
