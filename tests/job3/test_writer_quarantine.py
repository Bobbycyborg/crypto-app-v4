#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.render_report import render_report

FIX = ROOT / "tests/job3/fixtures"
NON_WALLET_PRICE_HOSTS = (
    "fapi.binance.com",
    "api.binance.com",
    "api.dexscreener.com",
    "api.coingecko.com",
)


def _extract_script_blocks(html: str) -> list[str]:
    return re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.DOTALL | re.IGNORECASE)


def _active_nonwallet_current_writers(html: str) -> list[str]:
    """Classify surviving executable hold-card price writers after quarantine."""
    hits: list[str] = []
    if re.search(r"(?m)^\s*tick\(\);\s*$", html):
        hits.append("tick() invocation")
    if re.search(r"setInterval\(\s*tick\s*,", html):
        hits.append("setInterval(tick)")
    for block in _extract_script_blocks(html):
        if "function tick(" not in block:
            continue
        for host in NON_WALLET_PRICE_HOSTS:
            if f"fetch('{host}" in block or f'fetch("{host}' in block:
                # Dead only if tick is never scheduled/invoked.
                if not hits:
                    hits.append(f"dead_fetch_in_tick:{host}")
    return [h for h in hits if not h.startswith("dead_fetch_in_tick:")]


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
    active = _active_nonwallet_current_writers(out)
    print(f"shadow_nonwallet_current_network_writers={len(active)}")
    if active:
        raise AssertionError(f"active non-wallet writers survived quarantine: {active}")
    print("test_writer_quarantine OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
