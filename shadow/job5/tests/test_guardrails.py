#!/usr/bin/env python3
"""Static product guardrails on source HTML (S). Job5 must not require editing them."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_guardrails():
    html = (ROOT / "index-v4.html").read_text(encoding="utf-8")
    assert "$ held" not in html.lower()
    assert "MARKET PARTICIPATION" in html
    assert html.lower().count("breadth") == 0
    # RAY/GRASS/DRIFT remain out of Job3 bindings
    man = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
    assets = {(b.get("asset") or "").upper() for b in man["bindings"]}
    assert "RAY" not in assets
    assert "GRASS" not in assets
    assert "DRIFT" not in assets
    assert "ORCA" in html  # hold-card may exist; report lane not onboarded as active research
    print("test_guardrails PASS")


if __name__ == "__main__":
    test_guardrails()
