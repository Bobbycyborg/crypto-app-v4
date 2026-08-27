#!/usr/bin/env python3
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.formatters import format_value, infer_formatter


def test_unknown_exact() -> None:
    assert format_value(1, {"type": "numeric"}, status="UNKNOWN") == "UNKNOWN"


def test_currency_m() -> None:
    fmt = infer_formatter("$6.8M/wk")
    assert format_value(6760818, fmt) == "$6.8M/wk"


def test_grouping() -> None:
    fmt = infer_formatter("$6,760,818")
    assert format_value(6760818, fmt) == "$6,760,818"


def test_percent_plus() -> None:
    fmt = infer_formatter("+12.4%")
    out = format_value(12.4, fmt)
    assert out == "+12.4%"


def test_ratio_x() -> None:
    fmt = infer_formatter("3.7x")
    assert format_value(3.7, fmt) == "3.7x"


def main() -> int:
    test_unknown_exact()
    test_currency_m()
    test_grouping()
    test_percent_plus()
    test_ratio_x()
    print("test_formatters OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
