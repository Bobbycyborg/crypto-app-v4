#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.build_binding_manifest import _infer_literal
from renderer.formatters import adjust_formatter_for_binding, format_value, infer_formatter

REQUIRED = []


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
    direct = [
        ("~−37.1%", -37.1, "~−37.1%"),
        ("-2.796e-05", -2.796e-05, "-2.796e-05"),
        ("$516k/d", 516000, "$516k/d"),
        ("$6.8M/wk", 6800000, "$6.8M/wk"),
        ("+12.4%", 12.4, "+12.4%"),
        ("3.7x", 3.7, "3.7x"),
        ("+3.7pp", 3.7, "+3.7pp"),
        ("~9.2×", 9.2, "~9.2×"),
        ("−8.7M/yr", -8_700_000, "−8.7M/yr"),
    ]
    for lit, val, want in direct:
        assert format_value(val, infer_formatter(lit)) == want, lit

    prefix = infer_formatter("9.2x")
    prefix = dict(prefix)
    prefix["literal_prefix"] = "Fut/spot "
    assert format_value(9.2, prefix) == "Fut/spot 9.2x"

    approx_m = infer_formatter("~412M")
    approx_m = dict(approx_m)
    approx_m["literal_suffix"] = " remaining"
    assert format_value(412_000_000, approx_m) == "~412M remaining"

    frac = infer_formatter("2")
    frac = dict(frac)
    frac["literal_suffix"] = "/10 beat BTC"
    assert format_value(2, frac) == "2/10 beat BTC"

    split_m = _fmt("$27", effective="$27", manifest_lit="$27<span class='econ-u'>M</span>", anchor_after="<span class='econ-u'>M</span>")
    assert format_value(27_000_000, split_m) == "$27"

    split_pct = _fmt("0.82", effective="0.82", manifest_lit="0.82<span>%</span>", anchor_after="<span class='econ-u'>%</span>")
    assert format_value(0.82, split_pct) == "0.82"


def test_compact_usd() -> None:
    from integrity.numeric import compact_usd_parts

    assert compact_usd_parts(1_219_200_000) == ("$1.22", "B", False)
    assert compact_usd_parts(-201_800_000) == ("$202", "M", True)
    assert compact_usd_parts(102_100_000) == ("$102", "M", False)
    assert compact_usd_parts(167_300_000) == ("$167", "M", False)
    assert compact_usd_parts(171_400_000) == ("$171", "M", False)
    assert compact_usd_parts(54_110_000_000) == ("$54.1", "B", False)
    assert compact_usd_parts(12_270_000_000) == ("$12.3", "B", False)
    assert compact_usd_parts(1_838_300_000) == ("$1.84", "B", False)


def test_unknown_exact() -> None:
    assert format_value(1, {"type": "numeric"}, status="UNKNOWN") == "UNKNOWN"


def test_grouping() -> None:
    fmt = infer_formatter("$6,760,818")
    assert format_value(6760818, fmt) == "$6,760,818"


def main() -> int:
    test_unknown_exact()
    test_required_goldens()
    test_grouping()
    test_compact_usd()
    print("test_formatters OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
