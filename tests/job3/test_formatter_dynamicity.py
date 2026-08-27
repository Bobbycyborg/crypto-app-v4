#!/usr/bin/env python3
"""Prove numeric bindings render dynamically — sentinel must change the number only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.formatter_recovery import check_dynamicity, is_numeric_raw

MANIFEST = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
BINDINGS = MANIFEST["bindings"]

NOS_IDS = {
    "nos.jobs.completed.cumulative::1d70a41f9cd855bf",
    "nos.jobs.completed.cumulative::8a7acfe56c2b879d",
    "nos.jobs.completed.cumulative::90b401930a563bb4",
    "nos.jobs.completed.cumulative::df45ff651c167316",
}


def gates() -> tuple[int, int, list[str], str]:
    checked = 0
    failures = 0
    errors: list[str] = []
    nos_outputs: list[str] = []
    for b in BINDINGS:
        raw = b.get("binding_raw")
        if raw is None or not is_numeric_raw(raw):
            continue
        checked += 1
        if not check_dynamicity(b["source_literal"], raw, b["formatter"]):
            failures += 1
            if len(errors) < 12:
                errors.append(b["binding_id"])
        if b["binding_id"] in NOS_IDS:
            from renderer.formatter_recovery import sentinel_raw
            from renderer.formatters import format_value

            nos_outputs.append(format_value(sentinel_raw(raw), b["formatter"]))
    nos_fanout = "PASS"
    if len(nos_outputs) != 4:
        nos_fanout = "FAIL"
    elif len(set(nos_outputs)) != 1:
        nos_fanout = "FAIL"
    elif nos_outputs[0] == "4.09M":
        nos_fanout = "FAIL"
    return checked, failures, errors, nos_fanout


def main() -> int:
    checked, failures, errors, nos_fanout = gates()
    print(f"numeric_dynamicity_checked={checked}")
    print(f"numeric_dynamicity_failures={failures}")
    print(f"nos_sentinel_fanout={nos_fanout}")
    for e in errors:
        print(e)
    ok = checked == 408 and failures == 0 and nos_fanout == "PASS"
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
