#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.formatters import format_value
from renderer.render_report import render_report
sys.path.insert(0, str(ROOT / "tests/job3"))
from _binding_span import rendered_span

FIX = ROOT / "tests/job3/fixtures"


def _render_one(source: str, binding: dict, snapshot: dict, writers: dict) -> str:
    out, _, _ = render_report(
        source_html=source,
        bindings=[binding],
        snapshot=snapshot,
        writer_quarantine=writers,
    )
    return rendered_span(out, binding, source=source)


def main() -> int:
    source = (ROOT / "index-v4.html").read_text(encoding="utf-8")
    bindings = json.loads((ROOT / "renderer/binding-manifest.json").read_text())["bindings"]
    snapshot = json.loads((FIX / "snapshot-mutation.json").read_text())
    writers = json.loads((ROOT / "renderer/writer-quarantine.json").read_text())
    gold = json.loads((ROOT / "tests/job3/golden-bindings.json").read_text())["cases"]
    by_id = {b["binding_id"]: b for b in bindings}

    for case in gold:
        b = by_id[case["binding_id"]]
        rec = snapshot["metrics"][case["metric_id"]]
        if rec.get("status") != "OK":
            expected = "UNKNOWN"
        else:
            expected = format_value(rec["normalized_value"], b["formatter"], status="OK")
        actual = _render_one(source, b, snapshot, writers)
        assert actual == expected, f"{case['binding_id']}: got {actual!r} want {expected!r}"

    fanout_mid = "pump.buyback.usd.7d"
    fanout = [b for b in bindings if b["metric_id"] == fanout_mid]
    assert len(fanout) >= 2
    fanout_val = snapshot["metrics"][fanout_mid]["normalized_value"]
    rendered_fanout = set()
    for b in fanout:
        expected = format_value(fanout_val, b["formatter"], status="OK")
        actual = _render_one(source, b, snapshot, writers)
        assert actual == expected, b["binding_id"]
        rendered_fanout.add(actual)
    assert len(rendered_fanout) >= 2, "fanout metric must change every mapped occurrence"

    out_all, _, _ = render_report(
        source_html=source,
        bindings=bindings,
        snapshot=snapshot,
        writer_quarantine=writers,
    )
    other = by_id["btc.price.usd.live::30f665b010005234"]
    other_expected = format_value(
        snapshot["metrics"]["btc.price.usd.live"]["normalized_value"],
        other["formatter"],
        status="OK",
    )
    assert _render_one(source, other, snapshot, writers) == other_expected
    assert "daily close under $70" in out_all
    assert "siren-watch-data" in out_all
    print("test_golden_render OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
