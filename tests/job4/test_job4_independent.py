#!/usr/bin/env python3
"""Independent Job 4 checker — subprocess only, no integrity rule imports."""

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


def _run_checker(
    *,
    snapshot: Path,
    rendered: Path,
    contract: Path,
    run_id: str,
    out: Path,
    source_html: Path | None = None,
    bindings: Path | None = None,
) -> tuple[int, dict]:
    cmd = [
        sys.executable,
        str(INTEGRITY / "check_report.py"),
        "--snapshot",
        str(snapshot),
        "--rendered-html",
        str(rendered),
        "--source-html",
        str(source_html or ROOT / "index-v4.html"),
        "--bindings",
        str(bindings or ROOT / "renderer/binding-manifest.json"),
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


def _source_literal_value_fallback_refs() -> int:
    n = 0
    for path in INTEGRITY.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        n += len(re.findall(r"lit_val\s*=", text))
        n += len(re.findall(r"accept source_literal instead", text))
        n += text.count("or span.strip() == str(b.get(\"source_literal\"")
        n += text.count("or span.strip() == str(binding.get(\"source_literal\"")
    return n


def main() -> int:
    _assert_no_banned_imports(Path(__file__))
    subprocess.run([sys.executable, str(FIX / "build_mutations.py")], check=True, cwd=str(ROOT))
    contract_path = INTEGRITY / "report-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    required = contract["required_categories"]
    assert len(required) == 12

    before = {
        p: _sha(p)
        for p in [FIX / "golden-snapshot.json", FIX / "golden-rendered.html", ROOT / "index-v4.html"]
    }
    out = FIX / "independent-golden.json"
    code, report = _run_checker(
        snapshot=FIX / "golden-snapshot.json",
        rendered=FIX / "golden-rendered.html",
        contract=contract_path,
        run_id="independent-golden",
        out=out,
    )
    after = {p: _sha(p) for p in before}
    assert before == after
    assert code == 0
    assert report["counts"]["fail"] == 0
    assert report["counts"]["coverage_gap"] == 0
    assert report["missing_check_ids"] == []
    assert report["unexpected_check_ids"] == []
    assert set(report["expected_check_ids"]) == set(report["executed_check_ids"])
    for cat in required:
        assert report["categories"][cat]["present"]
    for c in report["checks"]:
        if c["status"] == "PASS":
            assert c["assertions_executed"] >= 1

    code, m03 = _run_checker(
        snapshot=FIX / "M03-snapshot.json",
        rendered=FIX / "M03-rendered.html",
        contract=FIX / "M03-contract.json",
        run_id="independent-m03",
        out=FIX / "independent-m03.json",
    )
    assert code == 3
    assert "04_bind_intentionally_absent_probe" in m03["missing_check_ids"]

    code, m16 = _run_checker(
        snapshot=FIX / "M16-snapshot.json",
        rendered=FIX / "M16-rendered.html",
        contract=contract_path,
        run_id="independent-m16",
        out=FIX / "independent-m16.json",
    )
    assert code == 2
    assert any(
        c["check_id"] == "04_bind_btc.inflation.pct.current::01660e6a6d540fca" and c["status"] == "FAIL"
        for c in m16["checks"]
    )

    code, m17 = _run_checker(
        snapshot=FIX / "M17-snapshot.json",
        rendered=FIX / "M17-rendered.html",
        contract=contract_path,
        run_id="independent-m17",
        out=FIX / "independent-m17.json",
    )
    assert code == 2
    assert any(
        c["check_id"] == "04_bind_render.bme.ratio.last4::00a581be80d3bc08" and c["status"] == "FAIL"
        for c in m17["checks"]
    )

    code, m22 = _run_checker(
        snapshot=FIX / "M22-snapshot.json",
        rendered=FIX / "M22-rendered.html",
        contract=FIX / "M22-contract.json",
        bindings=FIX / "M22-manifest.json",
        run_id="independent-m22",
        out=FIX / "independent-m22.json",
    )
    assert code == 4

    code, m07 = _run_checker(
        snapshot=FIX / "M07-snapshot.json",
        rendered=FIX / "M07-rendered.html",
        contract=contract_path,
        run_id="independent-m07",
        out=FIX / "independent-m07.json",
    )
    inv = next(c for c in m07["checks"] if c["check_id"] == "12_reg_pump_wallet_invariance")
    assert inv["status"] == "PASS"
    assert inv["assertions_executed"] >= 1
    ev = inv["evidence"]
    assert ev["wallet_occurrence_identified_as_grok_owned"]
    assert ev["wallet_occurrence_excluded_from_nonwallet_comparison"]
    assert ev["non_wallet_binding_set_unchanged"]

    assert _source_literal_value_fallback_refs() == 0

    audit = subprocess.run(
        [
            sys.executable,
            str(INTEGRITY / "audit_literals.py"),
            "--snapshot",
            str(FIX / "golden-snapshot.json"),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    audit_payload = json.loads(audit.stdout)
    assert audit.returncode == 0, audit_payload
    assert audit_payload["hardcoded_current_values"] == 0

    inject_val = json.loads((FIX / "golden-snapshot.json").read_text())["metrics"]["pump.buyback.usd.7d"][
        "normalized_value"
    ]
    inj = subprocess.run(
        [
            sys.executable,
            str(INTEGRITY / "audit_literals.py"),
            "--snapshot",
            str(FIX / "golden-snapshot.json"),
            "--inject",
            str(inject_val),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert inj.returncode == 0, inj.stdout
    assert json.loads(inj.stdout)["inject_hits"]

    code, m05 = _run_checker(
        snapshot=FIX / "M05-snapshot.json",
        rendered=FIX / "M05-rendered.html",
        contract=contract_path,
        run_id="independent-m05",
        out=FIX / "independent-m05.json",
    )
    assert code == 2
    assert any(
        c["check_id"] == "12_reg_pump_buyback_duplicate" and c["status"] == "FAIL"
        for c in m05["checks"]
    )

    code, m23 = _run_checker(
        snapshot=FIX / "M23-snapshot.json",
        rendered=FIX / "M23-rendered.html",
        contract=contract_path,
        source_html=FIX / "M23-source.html",
        run_id="independent-m23",
        out=FIX / "independent-m23.json",
    )
    assert code == 4

    proc = subprocess.run(
        [sys.executable, str(ROOT / "tests/job4/test_regressions.py")],
        cwd=str(ROOT),
    )
    assert proc.returncode == 0

    proc = subprocess.run(
        [sys.executable, str(INTEGRITY / "build_report_contract.py"), "--check"],
        cwd=str(ROOT),
    )
    assert proc.returncode == 0

    print("test_job4_independent OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
