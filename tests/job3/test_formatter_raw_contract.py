#!/usr/bin/env python3
"""Formatter raw-selection safety gates — no calibration, no display-value as data."""

from __future__ import annotations

import json
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
        if "_absolute_from_metric_value" in text:
            hits += text.count("_absolute_from_metric_value")
        if "allow_value_parse" in text:
            hits += text.count("allow_value_parse")
    return hits


def _metric_value_as_numeric_source() -> int:
    banned = (
        "_absolute_from_metric_value",
        "allow_value_parse",
        'row.get("value")',
    )
    hits = 0
    for path in (ROOT / "renderer").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            hits += text.count(token)
    return hits


def main() -> int:
    coef_bindings = 0
    presentation_syntax: list[str] = []
    nos_ok = True
    for b in BINDINGS:
        fmt = b["formatter"]
        if "coefficient_override" in fmt:
            coef_bindings += 1
        if fmt.get("formatter_evidence_mode") == "PRESENTATION_SYNTAX_INVALID_OCCURRENCE_RAW":
            presentation_syntax.append(b["binding_id"])
        if b["binding_id"] in NOS_IDS:
            if fmt.get("formatter_evidence_mode") != "PRESENTATION_SYNTAX_INVALID_OCCURRENCE_RAW":
                nos_ok = False
            if fmt.get("rejected_occurrence_raw") != 4.0:
                nos_ok = False
            if b.get("binding_raw") is not None:
                nos_ok = False
            if not fmt.get("presentation_syntax_recovered"):
                nos_ok = False

    code_refs = _code_refs()
    metric_value_hits = _metric_value_as_numeric_source()
    print(f"coefficient_override_bindings={coef_bindings}")
    print(f"coefficient_override_code_refs={code_refs}")
    print(f"presentation_syntax_recovered={len(presentation_syntax)}")
    print(f"metric_value_as_numeric_source={metric_value_hits}")
    print(f"nos_syntax_recovery={'PASS' if nos_ok else 'FAIL'}")
    ok = (
        coef_bindings == 0
        and code_refs == 0
        and len(presentation_syntax) == 4
        and set(presentation_syntax) == NOS_IDS
        and metric_value_hits == 0
        and nos_ok
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
