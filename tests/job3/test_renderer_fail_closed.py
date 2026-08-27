#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.render_report import render_report

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
    zec = [b for b in bindings if b["metric_id"] == "zec.tx.count.24h"]
    for b in zec:
        combo = b["anchor_before"] + b["source_literal"] + b["anchor_after"]
        assert combo not in out
        assert "UNKNOWN" in out
    print("test_renderer_fail_closed OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
