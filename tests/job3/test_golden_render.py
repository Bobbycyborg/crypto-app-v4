#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.formatters import format_value
from renderer.render_report import render_report

FIX = ROOT / "tests/job3/fixtures"


def main() -> int:
    source = (ROOT / "index-v4.html").read_text(encoding="utf-8")
    bindings = json.loads((ROOT / "renderer/binding-manifest.json").read_text())["bindings"]
    snapshot = json.loads((FIX / "snapshot-mutation.json").read_text())
    writers = json.loads((ROOT / "renderer/writer-quarantine.json").read_text())
    out, _manifest, code = render_report(
        source_html=source,
        bindings=bindings,
        snapshot=snapshot,
        writer_quarantine=writers,
    )
    gold = json.loads((ROOT / "tests/job3/golden-bindings.json").read_text())["cases"]
    for case in gold:
        mid = case["metric_id"]
        rec = snapshot["metrics"][mid]
        b = next(x for x in bindings if x["binding_id"] == case["binding_id"])
        expected = format_value(rec["normalized_value"], b["formatter"], status="OK")
        assert expected in out, f"missing {mid} -> {expected}"
    assert "siren-watch-data" in out
    print("test_golden_render OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
