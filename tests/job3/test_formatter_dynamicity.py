#!/usr/bin/env python3
"""Prove numeric bindings render dynamically — sentinel must change the number only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.formatter_recovery import check_dynamicity, is_numeric_raw, select_binding_raw

MANIFEST = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
BINDINGS = MANIFEST["bindings"]
REG, _, _, _ = __import__("renderer.eligibility", fromlist=["load_job1_job2"]).load_job1_job2()


def gates() -> tuple[int, int, list[str]]:
    checked = 0
    failures = 0
    errors: list[str] = []
    for b in BINDINGS:
        raw, _src = select_binding_raw(REG, b["metric_id"], b["job1_occurrence_id"])
        if raw is None or not is_numeric_raw(raw):
            continue
        checked += 1
        if not check_dynamicity(b["source_literal"], raw, b["formatter"]):
            failures += 1
            if len(errors) < 12:
                errors.append(b["binding_id"])
    return checked, failures, errors


def main() -> int:
    checked, failures, errors = gates()
    print(f"numeric_dynamicity_checked={checked}")
    print(f"numeric_dynamicity_failures={failures}")
    for e in errors:
        print(e)
    ok = checked == 408 and failures == 0
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
