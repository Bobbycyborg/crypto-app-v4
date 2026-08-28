#!/usr/bin/env python3
"""Shared helpers for Job 4 tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/job4/fixtures"
CONTRACT = ROOT / "integrity/report-contract.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_checker(
    *,
    snapshot: Path,
    rendered: Path,
    source_html: Path | None = None,
    bindings: Path | None = None,
    contract: Path | None = None,
    run_id: str = "test-run",
    out: Path | None = None,
) -> tuple[int, dict[str, Any]]:
    source_html = source_html or ROOT / "index-v4.html"
    bindings = bindings or ROOT / "renderer/binding-manifest.json"
    contract = contract or CONTRACT
    out = out or FIX / f"out-{run_id}.json"
    cmd = [
        sys.executable,
        str(ROOT / "integrity/check_report.py"),
        "--snapshot",
        str(snapshot),
        "--rendered-html",
        str(rendered),
        "--source-html",
        str(source_html),
        "--bindings",
        str(bindings),
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
    report = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}
    return proc.returncode, report


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def checks_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["check_id"]: c for c in report.get("checks", [])}
