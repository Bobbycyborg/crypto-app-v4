#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.build_binding_manifest import _infer_literal
from renderer.formatters import adjust_formatter_for_binding, format_value, infer_formatter

REQUIRED = [
    ("~−37.1%", -37.1, "~−37.1%"),
    ("-2.796e-05", -2.796e-05, "-2.796e-05"),
    ("$516k/d", 516000, "$516k/d"),
    ("$6.8M/wk", 6800000, "$6.8M/wk"),
    ("+12.4%", 12.4, "+12.4%"),
    ("3.7x", 3.7, "3.7x"),
]


def _fmt(lit: str, effective: str | None = None, manifest_lit: str | None = None, anchor_after: str = "") -> dict:
    manifest = manifest_lit or lit
    eff = effective or lit
    return adjust_formatter_for_binding(
        infer_formatter(_infer_literal(manifest, eff)),
        manifest,
        eff,
        anchor_after,
    )


def test_required_goldens() -> None:
    for lit, val, want in REQUIRED:
        assert format_value(val, infer_formatter(lit)) == want, lit

    split_m = _fmt("$27", effective="$27", manifest_lit="$27<span class='econ-u'>M</span>", anchor_after="<span class='econ-u'>M</span>")
    assert format_value(27_000_000, split_m) == "$27"

    split_pct = _fmt("0.82", effective="0.82", manifest_lit="0.82<span>%</span>", anchor_after="<span class='econ-u'>%</span>")
    assert format_value(0.82, split_pct) == "0.82"


def test_unknown_exact() -> None:
    assert format_value(1, {"type": "numeric"}, status="UNKNOWN") == "UNKNOWN"


def test_grouping() -> None:
    fmt = infer_formatter("$6,760,818")
    assert format_value(6760818, fmt) == "$6,760,818"


def main() -> int:
    test_unknown_exact()
    test_required_goldens()
    test_grouping()
    print("test_formatters OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
