"""Refuse AUTOJOB01 writes to Report 01. Fail loud."""

from __future__ import annotations

import hashlib
from pathlib import Path

from lib.v3.autojob01.paths import (
    REPORT_01_HTML,
    REPORT_01_SHA256_BASELINE,
    REPORT_02_BASELINE_HTML,
    REPORT_02_SHA256_BASELINE,
    REPORT_03_BASELINE_HTML,
    REPORT_03_SHA256_BASELINE,
    is_report_01_path,
)
from lib.v3.write_guard import refuse_frozen_v3_live_write


class Report01ImmutableError(RuntimeError):
    """AUTOJOB01 tried to write Report 01."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def refuse_report_01_write(path: Path) -> None:
    if is_report_01_path(path):
        raise Report01ImmutableError(
            f"AUTOJOB01 refuse write to frozen baseline: {path}"
        )


def write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    refuse_report_01_write(path)
    refuse_frozen_v3_live_write(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=encoding)


def write_bytes(path: Path, data: bytes) -> None:
    refuse_report_01_write(path)
    refuse_frozen_v3_live_write(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def prove_report_01_unchanged() -> dict[str, str]:
    if not REPORT_01_HTML.is_file():
        raise Report01ImmutableError("Report 01 HTML missing")
    got = sha256_file(REPORT_01_HTML)
    if got != REPORT_01_SHA256_BASELINE:
        raise Report01ImmutableError(
            f"Report 01 mutated: expected {REPORT_01_SHA256_BASELINE} got {got}"
        )
    if REPORT_02_BASELINE_HTML.is_file():
        got02 = sha256_file(REPORT_02_BASELINE_HTML)
        if got02 != REPORT_02_SHA256_BASELINE:
            raise Report01ImmutableError(
                f"Report 02 baseline mutated: expected {REPORT_02_SHA256_BASELINE} got {got02}"
            )
    if REPORT_03_BASELINE_HTML.is_file():
        got03 = sha256_file(REPORT_03_BASELINE_HTML)
        if got03 != REPORT_03_SHA256_BASELINE:
            raise Report01ImmutableError(
                f"Report 03 baseline mutated: expected {REPORT_03_SHA256_BASELINE} got {got03}"
            )
    return {"path": str(REPORT_01_HTML), "sha256": got, "status": "UNCHANGED"}
