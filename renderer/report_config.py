"""Single roster and report-date file. Pipeline code reads this, not a week number baked into Python."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_report() -> dict[str, Any]:
    return json.loads((ROOT / "config" / "report.json").read_text(encoding="utf-8"))


def dormant_assets() -> frozenset[str]:
    return frozenset(a.upper() for a in load_report()["dormant"])


def siren_walk_coins() -> list[str]:
    return list(load_report()["siren_walk"])
