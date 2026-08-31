"""Hard lock: previous weekly reports cannot be overwritten."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FROZEN_REPORTS = (
    ROOT / "baselines/report-01.html",
    ROOT / "baselines/report-02.html",
    ROOT / "baselines/report-03.html",
    ROOT / "baselines/report-04.html",
)


def refuse_frozen_write(path: Path) -> None:
    target = path.resolve()
    frozen = {p.resolve() for p in FROZEN_REPORTS if p.exists()}
    if target in frozen:
        raise RuntimeError(f"REFUSE_WRITE_FROZEN_REPORT:{target}")
