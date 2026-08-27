#!/usr/bin/env python3
"""Independent Job 4 checker — subprocess only, no integrity imports."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
INTEGRITY = ROOT / "integrity"

BANNED_IMPORTS = (
    "integrity.check_report",
    "integrity.rules",
    "integrity.numeric",
    "integrity.extract",
    "integrity.model",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_no_banned_imports(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert not any(n.name == p or n.name.startswith(p + ".") for p in BANNED_IMPORTS)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module == p or node.module.startswith(p + ".") for p in BANNED_IMPORTS)


def _run_checker(*, snapshot: Path, rendered: Path, contract: Path, run_id: str, out: Path) -> tuple[int, dict]:
    cmd = [
        sys.executable,
        str(INTEGRITY / "check_report.py"),
        "--snapshot",
        str(snapshot),
        "--rendered-html",
        str(rendered),
        "--source-html",
        str(ROOT / "index-v4.html"),
        "--bindings",
        str(ROOT / "renderer/binding-manifest.json"),
        "--registry",
        str(ROOT / "metrics/metric-registry.json"),
        "--collector-plan",
        str(ROOT / "collectors/collector-plan.json"),
        "--contract",
        str(contract),
        "--out",
        str(out),
        "--run-id",
        run_id,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    report = json.loads(out.read_text(encoding="utf-8"))
    return proc.returncode, report


def _scan_no_hardcoded_values() -> list[str]:
    hits: list[str] = []
    banned = re.compile(r"\b(79337|98328|6760818|6800000)\b")
    for path in INTEGRITY.rglob("*"):
        if path.suffix not in {".py", ".json"}:
            continue
        if path.name == "report-contract.json":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if banned.search(text):
            hits.append(str(path))
    return hits


def main() -> int:
    _assert_no_banned_imports(Path(__file__))
    contract = json.loads((INTEGRITY / "report-contract.json").read_text(encoding="utf-8"))
    required = contract["required_categories"]
    assert len(required) == 12

    if not (FIX / "golden-rendered.html").is_file():
        subprocess.run([sys.executable, str(FIX / "build_golden.py")], check=True, cwd=str(ROOT))
    if not (FIX / "M04-rendered.html").is_file():
        subprocess.run([sys.executable, str(FIX / "build_mutations.py")], check=True, cwd=str(ROOT))

  # read-only inputs
    before = {p: _sha(p) for p in [FIX / "golden-snapshot.json", FIX / "golden-rendered.html", ROOT / "index-v4.html"]}
    out = FIX / "independent-golden.json"
    code, report = _run_checker(
        snapshot=FIX / "golden-snapshot.json",
        rendered=FIX / "golden-rendered.html",
        contract=INTEGRITY / "report-contract.json",
        run_id="independent-golden",
        out=out,
    )
    after = {p: _sha(p) for p in before}
    assert before == after
    assert code == 0
    assert report["counts"]["fail"] == 0
    assert report["counts"]["coverage_gap"] == 0
    for cat in required:
        assert report["categories"][cat]["present"]

    for c in report["checks"]:
        if c["status"] == "PASS":
            assert c["assertions_executed"] >= 1

    code, m04 = _run_checker(
        snapshot=FIX / "M04-snapshot.json",
        rendered=FIX / "M04-rendered.html",
        contract=INTEGRITY / "report-contract.json",
        run_id="independent-m04",
        out=FIX / "independent-m04.json",
    )
    assert code == 2
    assert any(c["check_id"] == "12_reg_spx_price_duplicate" and c["status"] == "FAIL" for c in m04["checks"])

    code, m05 = _run_checker(
        snapshot=FIX / "M05-snapshot.json",
        rendered=FIX / "M05-rendered.html",
        contract=INTEGRITY / "report-contract.json",
        run_id="independent-m05",
        out=FIX / "independent-m05.json",
    )
    assert code == 2

    code, m07 = _run_checker(
        snapshot=FIX / "M07-snapshot.json",
        rendered=FIX / "M07-rendered.html",
        contract=INTEGRITY / "report-contract.json",
        run_id="independent-m07",
        out=FIX / "independent-m07.json",
    )
    assert m07["checks"][-1]["check_id"] != "12_reg_pump_buyback_duplicate" or any(
        c["check_id"] == "12_reg_pump_wallet_invariance" for c in m07["checks"]
    )

    assert not _scan_no_hardcoded_values()

    proc = subprocess.run(
        [sys.executable, str(INTEGRITY / "build_report_contract.py"), "--check"],
        cwd=str(ROOT),
    )
    assert proc.returncode == 0

    print("test_job4_independent OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
