#!/usr/bin/env python3
"""Formatter round-trip gate — every numeric-usable binding must verify."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.formatter_recovery import is_numeric_raw, select_binding_raw
from renderer.formatters import format_value

MANIFEST = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
BINDINGS = MANIFEST["bindings"]
REG, _, _, _ = __import__("renderer.eligibility", fromlist=["load_job1_job2"]).load_job1_job2()


def gates() -> dict[str, int | list[str]]:
    numeric_usable = 0
    roundtrip_verified = 0
    unverified_numeric = 0
    numeric_string_exact = 0
    mismatch = 0
    errors: list[str] = []

    for b in BINDINGS:
        raw, _src = select_binding_raw(REG, b["metric_id"], b["job1_occurrence_id"])
        if raw is None or not is_numeric_raw(raw):
            continue
        numeric_usable += 1
        fmt = b["formatter"]
        if fmt.get("type") == "string_exact":
            numeric_string_exact += 1
        got = format_value(raw, fmt)
        want = b["source_literal"]
        if fmt.get("roundtrip_verified") and got == want:
            roundtrip_verified += 1
        else:
            unverified_numeric += 1
            mismatch += 1
            if len(errors) < 12:
                errors.append(f"{b['binding_id']}: got {got!r} want {want!r} verified={fmt.get('roundtrip_verified')}")

    return {
        "numeric_usable_total": numeric_usable,
        "roundtrip_verified": roundtrip_verified,
        "unverified_numeric": unverified_numeric,
        "numeric_string_exact": numeric_string_exact,
        "formatter_roundtrip_mismatch": mismatch,
        "errors": errors,
    }


def main() -> int:
    g = gates()
    print(f"numeric_usable_total={g['numeric_usable_total']}")
    print(f"roundtrip_verified={g['roundtrip_verified']}")
    print(f"unverified_numeric={g['unverified_numeric']}")
    print(f"numeric_string_exact={g['numeric_string_exact']}")
    print(f"formatter_roundtrip_checked={g['roundtrip_verified']}")
    print(f"formatter_roundtrip_mismatch={g['formatter_roundtrip_mismatch']}")
    for e in g["errors"]:
        print(e)
    ok = (
        g["numeric_usable_total"] == 408
        and g["roundtrip_verified"] == 408
        and g["unverified_numeric"] == 0
        and g["numeric_string_exact"] == 0
        and g["formatter_roundtrip_mismatch"] == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
