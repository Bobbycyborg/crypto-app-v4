#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
sys.path.insert(0, str(ROOT / "tests/job4"))


def main() -> int:
    if not (FIX / "golden-snapshot.json").is_file():
        subprocess.run([sys.executable, str(FIX / "build_golden.py")], check=True, cwd=str(ROOT))
    subprocess.run([sys.executable, str(FIX / "build_mutations.py")], check=True, cwd=str(ROOT))
    from _helpers import run_checker

    # M20 UNKNOWN + old numeric
    code, report = run_checker(
        snapshot=FIX / "M20-snapshot.json",
        rendered=FIX / "M20-rendered.html",
        run_id="M20",
    )
    assert code in (2, 3), code
    fails = [c for c in report["checks"] if c["status"] == "FAIL" and "btc.price.usd.live" in c.get("metric_ids", [])]
    assert fails, report.get("failures", [])[:3]

    # M21 UNKNOWN + UNKNOWN UI
    code, report = run_checker(
        snapshot=FIX / "M21-snapshot.json",
        rendered=FIX / "M21-rendered.html",
        run_id="M21",
    )
    blocked = [c for c in report["checks"] if "btc.price.usd.live" in c.get("metric_ids", [])]
    assert any(c["status"] in ("PASS", "BLOCKED_UNKNOWN") for c in blocked), [c["status"] for c in blocked[:5]]

    # M02 missing metric
    code, report = run_checker(snapshot=FIX / "M02-snapshot.json", rendered=FIX / "M02-rendered.html", run_id="M02")
    assert code == 3
    assert any(c["status"] == "COVERAGE_GAP" for c in report["checks"])

    # M22 hash mismatch
    snap = json.loads((FIX / "golden-snapshot.json").read_text())
    bad = copy.deepcopy(snap)
    bad["job1_registry_sha256"] = "0" * 64
    bad_path = FIX / "M22-snapshot.json"
    bad_path.write_text(json.dumps(bad, indent=2) + "\n")
    code, report = run_checker(snapshot=bad_path, rendered=FIX / "golden-rendered.html", run_id="M22")
    assert code in (3, 4), code
  # M03 missing category via truncated contract
    contract = json.loads((ROOT / "integrity/report-contract.json").read_text())
    bad_contract = copy.deepcopy(contract)
    bad_contract["required_categories"] = bad_contract["required_categories"][:-1]
    cpath = FIX / "M03-contract.json"
    cpath.write_text(json.dumps(bad_contract, indent=2) + "\n")
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "integrity/check_report.py"),
            "--snapshot",
            str(FIX / "golden-snapshot.json"),
            "--rendered-html",
            str(FIX / "golden-rendered.html"),
            "--source-html",
            str(ROOT / "index-v4.html"),
            "--bindings",
            str(ROOT / "renderer/binding-manifest.json"),
            "--registry",
            str(ROOT / "metrics/metric-registry.json"),
            "--collector-plan",
            str(ROOT / "collectors/collector-plan.json"),
            "--contract",
            str(cpath),
            "--out",
            str(FIX / "M03-out.json"),
            "--run-id",
            "M03",
        ],
        cwd=str(ROOT),
    )
    assert proc.returncode in (2, 3)

    print("test_fail_closed OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
