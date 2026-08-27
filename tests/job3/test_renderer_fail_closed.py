#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.render_report import render_report
sys.path.insert(0, str(ROOT / "tests/job3"))
from _binding_span import rendered_span

FIX = ROOT / "tests/job3/fixtures"


def main() -> int:
    source = (ROOT / "index-v4.html").read_text(encoding="utf-8")
    bindings = json.loads((ROOT / "renderer/binding-manifest.json").read_text())["bindings"]
    snapshot = json.loads((FIX / "snapshot-failclosed.json").read_text())
    writers = json.loads((ROOT / "renderer/writer-quarantine.json").read_text())
    out, manifest, code = render_report(
        source_html=source,
        bindings=bindings,
        snapshot=snapshot,
        writer_quarantine=writers,
        publishable=False,
    )
    assert manifest["publishable"] is False
    assert code == 2
    for b in bindings:
        if snapshot["metrics"][b["metric_id"]]["status"] != "OK":
            assert rendered_span(out, b, source=source) == "UNKNOWN", b["binding_id"]
    print("test_renderer_fail_closed OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
