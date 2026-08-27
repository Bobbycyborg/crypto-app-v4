#!/usr/bin/env python3
"""Production Job 4 fail-closed integrity checker CLI — stdlib only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrity.model import EXIT_INTERNAL, IntegrityReport, REQUIRED_CATEGORIES, SCHEMA_VERSION
from integrity.rules import run_all_checks


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_checker(
    *,
    snapshot_path: Path,
    rendered_html_path: Path,
    source_html_path: Path,
    bindings_path: Path,
    registry_path: Path,
    plan_path: Path,
    contract_path: Path,
    run_id: str,
) -> IntegrityReport:
    snapshot = _load(snapshot_path)
    rendered_html = rendered_html_path.read_text(encoding="utf-8")
    source_html = source_html_path.read_text(encoding="utf-8")
    manifest = _load(bindings_path)
    bindings = manifest["bindings"]
    reg_list = _load(registry_path)["metrics"]
    reg = {m["metric_id"]: m for m in reg_list}
    contract = _load(contract_path)

    report = IntegrityReport(
        schema_version=SCHEMA_VERSION,
        run_id=run_id,
        inputs={
            "snapshot": str(snapshot_path),
            "rendered_html": str(rendered_html_path),
            "source_html": str(source_html_path),
            "bindings": str(bindings_path),
            "registry": str(registry_path),
            "collector_plan": str(plan_path),
            "contract": str(contract_path),
        },
        counts={},
        categories={},
        assets={},
    )
    report.checks = run_all_checks(
        snapshot=snapshot,
        rendered_html=rendered_html,
        source_html=source_html,
        bindings=bindings,
        reg=reg,
        contract=contract,
        registry_path=str(registry_path),
        plan_path=str(plan_path),
        bindings_path=str(bindings_path),
        source_html_path=str(source_html_path),
        manifest=manifest,
    )
    report.finalize(
        contract_required=tuple(contract.get("required_categories", REQUIRED_CATEGORIES))
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Job 4 integrity checker")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--rendered-html", type=Path, required=True)
    parser.add_argument("--source-html", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--collector-plan", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        report = run_checker(
            snapshot_path=args.snapshot,
            rendered_html_path=args.rendered_html,
            source_html_path=args.source_html,
            bindings_path=args.bindings,
            registry_path=args.registry,
            plan_path=args.collector_plan,
            contract_path=args.contract,
            run_id=args.run_id,
        )
        args.out.write_text(
            json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return report.exit_code()
    except Exception as exc:
        print(f"INTERNAL_ERROR: {exc}", file=sys.stderr)
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
