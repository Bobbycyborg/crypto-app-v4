#!/usr/bin/env python3
"""Formatter raw-selection safety gates — no calibration, invalid-occurrence fallbacks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

MANIFEST = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
BINDINGS = MANIFEST["bindings"]

NOS_IDS = {
    "nos.jobs.completed.cumulative::1d70a41f9cd855bf",
    "nos.jobs.completed.cumulative::8a7acfe56c2b879d",
    "nos.jobs.completed.cumulative::90b401930a563bb4",
    "nos.jobs.completed.cumulative::df45ff651c167316",
}


def _code_refs() -> int:
    hits = 0
    for path in (ROOT / "renderer").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "coefficient_override" in text:
            hits += text.count("coefficient_override")
    return hits


def main() -> int:
    coef_bindings = 0
    invalid_fallbacks: list[str] = []
    nos_ok = True
    for b in BINDINGS:
        fmt = b["formatter"]
        if "coefficient_override" in fmt:
            coef_bindings += 1
        if fmt.get("formatter_raw_source") == "METRIC_FALLBACK_INVALID_OCCURRENCE_RAW":
            invalid_fallbacks.append(b["binding_id"])
        if b["binding_id"] in NOS_IDS:
            if fmt.get("formatter_raw_source") != "METRIC_FALLBACK_INVALID_OCCURRENCE_RAW":
                nos_ok = False
            if fmt.get("rejected_occurrence_raw") != 4.0:
                nos_ok = False
            if b.get("binding_raw") != 4090000.0:
                nos_ok = False

    code_refs = _code_refs()
    print(f"coefficient_override_bindings={coef_bindings}")
    print(f"coefficient_override_code_refs={code_refs}")
    print(f"invalid_occurrence_raw_fallbacks={len(invalid_fallbacks)}")
    print(f"nos_metric_fallback_invalid_occurrence_raw={'YES' if nos_ok else 'NO'}")
    if invalid_fallbacks != sorted(NOS_IDS):
        print("invalid_fallback_ids:")
        for bid in invalid_fallbacks:
            print(f"  {bid}")
    ok = (
        coef_bindings == 0
        and code_refs == 0
        and len(invalid_fallbacks) == 4
        and set(invalid_fallbacks) == NOS_IDS
        and nos_ok
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
