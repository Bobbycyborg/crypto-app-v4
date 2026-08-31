#!/usr/bin/env python3
"""Formatter round-trip gate — raw-verified and presentation-syntax bindings."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.formatter_recovery import is_numeric_binding
from renderer.formatters import format_value

MANIFEST = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
BINDINGS = MANIFEST["bindings"]


def gates() -> dict[str, int | list[str]]:
    numeric_bindings = 0
    raw_roundtrip_verified = 0
    presentation_syntax_recovered = 0
    unverified_numeric = 0
    numeric_string_exact = 0
    mismatch = 0
    errors: list[str] = []

    for b in BINDINGS:
        if not is_numeric_binding(b):
            continue
        numeric_bindings += 1
        fmt = b["formatter"]
        if fmt.get("type") == "string_exact":
            numeric_string_exact += 1
        raw = b.get("binding_raw")
        if fmt.get("presentation_syntax_recovered"):
            presentation_syntax_recovered += 1
            continue
        got = format_value(raw, fmt)
        want = b["source_literal"]
        if fmt.get("roundtrip_verified") and got == want:
            raw_roundtrip_verified += 1
        else:
            unverified_numeric += 1
            mismatch += 1
            if len(errors) < 12:
                errors.append(f"{b['binding_id']}: got {got!r} want {want!r}")

    return {
        "numeric_bindings": numeric_bindings,
        "raw_roundtrip_verified": raw_roundtrip_verified,
        "presentation_syntax_recovered": presentation_syntax_recovered,
        "unverified_numeric": unverified_numeric,
        "numeric_string_exact": numeric_string_exact,
        "formatter_roundtrip_mismatch": mismatch,
        "errors": errors,
    }


def main() -> int:
    g = gates()
    print(f"numeric_bindings={g['numeric_bindings']}")
    print(f"raw_roundtrip_verified={g['raw_roundtrip_verified']}")
    print(f"presentation_syntax_recovered={g['presentation_syntax_recovered']}")
    print(f"unverified_numeric={g['unverified_numeric']}")
    print(f"numeric_string_exact={g['numeric_string_exact']}")
    print(f"roundtrip_verified={g['raw_roundtrip_verified'] + g['presentation_syntax_recovered']}")
    print(f"formatter_roundtrip_mismatch={g['formatter_roundtrip_mismatch']}")
    for e in g["errors"]:
        print(e)
    ok = (
        g["numeric_bindings"] == 409
        and g["raw_roundtrip_verified"] == 405
        and g["presentation_syntax_recovered"] == 4
        and g["unverified_numeric"] == 0
        and g["numeric_string_exact"] == 0
        and g["formatter_roundtrip_mismatch"] == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
