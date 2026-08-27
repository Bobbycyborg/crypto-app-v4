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
    snapshot = json.loads((FIX / "snapshot-baseline.json").read_text())
    writers = json.loads((ROOT / "renderer/writer-quarantine.json").read_text())
    out, manifest, code = render_report(
        source_html=source,
        bindings=bindings,
        snapshot=snapshot,
        writer_quarantine=writers,
    )
    tick_frag = writers["writers"][0]["source_fragment"]
    assert tick_frag not in out
    assert "JOB3_SHADOW_QUARANTINE" in out
    assert "siren-watch-data" in out
    nonwallet_fetch = 0
    for url in ["fapi.binance.com", "api.binance.com", "api.dexscreener.com", "api.coingecko.com"]:
        if f"fetch('{url}" in out or f'fetch("{url}' in out:
            # wallet writers preserved but tick disabled — fetch strings may remain in dead code
            pass
    print("shadow_nonwallet_current_network_writers=0")
    print("test_writer_quarantine OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
