"""Refuse writes to frozen V3 live HTML.

V3 is historical/read-only after Job 0. Future live writes go to
crypto-app-v4/index-v4.html. See crypto-app-v3/V3-FROZEN.md.
"""

from __future__ import annotations

from pathlib import Path


class V3FrozenError(RuntimeError):
    """Attempted write to frozen V3 live report."""


def refuse_frozen_v3_live_write(path: Path) -> None:
    resolved = Path(path).resolve()
    if resolved.name == "index-v3.html" and "crypto-app-v3" in resolved.parts:
        raise V3FrozenError(
            f"V3 is FROZEN. Refusing write to {resolved}. "
            "Future work: crypto-app-v4/index-v4.html. See crypto-app-v3/V3-FROZEN.md"
        )
