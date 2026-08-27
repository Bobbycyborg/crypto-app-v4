#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.render_report import render_report


def test_exact_anchor_multi_occurrence() -> None:
    html = '<div id="a"><span>OLD_A</span></div><div id="b"><span>OLD_A</span></div>'
    bindings = [
        {
            "binding_id": "m1::o1",
            "metric_id": "m1",
            "field": "value",
            "target_kind": "HTML_TEXT",
            "source_literal": "OLD_A",
            "anchor_before": '<div id="a"><span>',
            "anchor_after": "</span></div>",
            "anchor_sha256": "x",
            "formatter": {"type": "string_exact"},
            "status_behavior": "UNKNOWN_ON_NON_OK",
        },
        {
            "binding_id": "m1::o2",
            "metric_id": "m1",
            "field": "value",
            "target_kind": "HTML_TEXT",
            "source_literal": "OLD_A",
            "anchor_before": '<div id="b"><span>',
            "anchor_after": "</span></div>",
            "anchor_sha256": "y",
            "formatter": {"type": "string_exact"},
            "status_behavior": "UNKNOWN_ON_NON_OK",
        },
    ]
    snap = {"source_run_id": "t", "metrics": {"m1": {"metric_id": "m1", "status": "OK", "normalized_value": "NEW"}}}
    out, manifest, code = render_report(source_html=html, bindings=bindings, snapshot=snap, writer_quarantine={"writers": []})
    assert out.count("NEW") == 2
    assert code == 0


def main() -> int:
    test_exact_anchor_multi_occurrence()
    print("test_renderer_unit OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
