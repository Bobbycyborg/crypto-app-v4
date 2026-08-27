#!/usr/bin/env python3
"""Formatter round-trip gate — all verified bindings must match exactly."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.formatters import format_value

MANIFEST = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
BINDINGS = MANIFEST["bindings"]
REG = {m["metric_id"]: m for m in json.loads((ROOT / "metrics/metric-registry.json").read_text())["metrics"]}


def _numeric_raw(binding: dict[str, Any]) -> Any | None:
    row = REG.get(binding["metric_id"])
    if not row:
        return None
    raw = row.get("raw_value")
    for ev in row.get("evidence_variants", []):
        if ev.get("occurrence_id") == binding["job1_occurrence_id"]:
            raw = ev.get("raw_value", raw)
            break
    if raw is None or raw == "UNKNOWN":
        return None
    if isinstance(raw, str):
        try:
            float(raw)
        except ValueError:
            return None
    return raw


def gates() -> tuple[int, int, list[str]]:
    checked = 0
    mismatch = 0
    errors: list[str] = []
    for b in BINDINGS:
        if not b["formatter"].get("roundtrip_verified"):
            continue
        raw = _numeric_raw(b)
        if raw is None:
            continue
        checked += 1
        got = format_value(raw, b["formatter"])
        want = b["source_literal"]
        if got != want:
            mismatch += 1
            if len(errors) < 12:
                errors.append(f"{b['binding_id']}: got {got!r} want {want!r}")
    return checked, mismatch, errors


def main() -> int:
    checked, mismatch, errors = gates()
    print(f"formatter_roundtrip_checked={checked}")
    print(f"formatter_roundtrip_mismatch={mismatch}")
    for e in errors:
        print(e)
    return 1 if mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
