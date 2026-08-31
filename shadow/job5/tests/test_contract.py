#!/usr/bin/env python3
"""Job5 tests: contract shape only — no Review04 market values."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = json.loads((ROOT / "shadow/job5/review04_contract.json").read_text())
FORBIDDEN_VALUE_TOKENS = ("6760818", "6.8M", "8998365", "1004290", "1387170")


def test_contract():
    assert CONTRACT["expected_bound_metrics"] == 212
    assert CONTRACT["expected_bindings"] == 418
    assert CONTRACT["expected_job4_checks"] == 868
    assert CONTRACT["baseline_html"] == "baselines/v4-start-from-final-v3.html"
    blob = json.dumps(CONTRACT)
    for tok in FORBIDDEN_VALUE_TOKENS:
        assert tok not in blob
    assert "RAY" in CONTRACT["excluded_assets"]
    print("test_contract PASS")


if __name__ == "__main__":
    test_contract()
