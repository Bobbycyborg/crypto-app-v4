#!/usr/bin/env python3
"""Three-way classifier unit checks on tiny SYNTHETIC_TEST_ONLY HTML."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shadow/job5"))
from classify_diff import classify  # noqa: E402

WALLET_A = '<script type="application/json" id="siren-watch-data">SYNTHETIC_WALLET_OPAQUE_A</script>'
WALLET_B = '<script type="application/json" id="siren-watch-data">SYNTHETIC_WALLET_OPAQUE_B</script>'


def test_three_way_diff():
    baseline = f"<html>hello{WALLET_A}</html>"
    source = f"<html>hello-v4{WALLET_B}</html>"
    shadow = source
    report = classify(
        baseline=baseline,
        source=source,
        shadow=shadow,
        bindings=[],
        writers={"writers": []},
        snapshot={"metrics": {}},
    )
    assert report["wallet_blob_unchanged"] is True
    assert report["counts"]["PREEXISTING_WALLET_DRIFT"] >= 1
    assert report["counts"]["PREEXISTING_APPROVED_STATIC_V4_DRIFT"] >= 1
    assert report["pipeline_defects"] == 0
    print("test_three_way_diff PASS")


if __name__ == "__main__":
    test_three_way_diff()
