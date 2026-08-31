#!/usr/bin/env python3
"""Prove numeric bindings render dynamically."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.formatter_recovery import (
    PRESENTATION_PROOF_OUTPUT,
    PRESENTATION_PROOF_VALUE,
    check_dynamicity,
    is_numeric_binding,
)
from renderer.formatters import format_value

MANIFEST = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
BINDINGS = MANIFEST["bindings"]

NOS_IDS = {
    "nos.jobs.completed.cumulative::1d70a41f9cd855bf",
    "nos.jobs.completed.cumulative::8a7acfe56c2b879d",
    "nos.jobs.completed.cumulative::90b401930a563bb4",
    "nos.jobs.completed.cumulative::df45ff651c167316",
}


def gates() -> tuple[int, int, str, str]:
    checked = 0
    failures = 0
    errors: list[str] = []
    nos_outputs: list[str] = []
    for b in BINDINGS:
        if not is_numeric_binding(b):
            continue
        checked += 1
        raw = b.get("binding_raw")
        if not check_dynamicity(b["source_literal"], raw, b["formatter"]):
            failures += 1
            if len(errors) < 12:
                errors.append(b["binding_id"])
        if b["binding_id"] in NOS_IDS:
            nos_outputs.append(format_value(PRESENTATION_PROOF_VALUE, b["formatter"]))
    nos_fanout = "PASS" if len(nos_outputs) == 4 and len(set(nos_outputs)) == 1 else "FAIL"
    nos_proof = "PASS" if nos_outputs and nos_outputs[0] == PRESENTATION_PROOF_OUTPUT else "FAIL"
    return checked, failures, nos_fanout, nos_proof


def main() -> int:
    checked, failures, nos_fanout, nos_proof = gates()
    print(f"numeric_dynamicity_checked={checked}")
    print(f"numeric_dynamicity_failures={failures}")
    print(f"nos_sentinel_fanout={nos_fanout}")
    print(f"nos_1234567_to_1_23M={nos_proof}")
    ok = checked == 409 and failures == 0 and nos_fanout == "PASS" and nos_proof == "PASS"
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
