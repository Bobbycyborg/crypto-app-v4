"""Report 01 baseline vs live index-v3.html. Report 01 is immutable for AUTOJOB01."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from lib.paths import ROOT, REPORTS

REPORT_01_HTML = ROOT / "baselines" / "report-01.html"
REPORT_02_BASELINE_HTML = ROOT / "baselines" / "report-02.html"  # Sunday 17 Aug — immutable
REPORT_03_BASELINE_HTML = ROOT / "baselines" / "report-03.html"  # Week of 20 Aug — immutable
REPORT_02_HTML = ROOT / "index-v4.html"  # live HTML; V4 working report
LIVE_REVIEW_NUM = "04"
LIVE_APPLY_TEMPLATE_HTML = REPORT_03_BASELINE_HTML  # structure seed for live apply
REPORT_02_SHA256_BASELINE = "431fbea4fd0aa6ee6bc9eb8c7667faba4537b0a30d698a32a7636963772d769e"
REPORT_03_SHA256_BASELINE = "cab4328c0e0ba883f13214eb8d1a7588ecde4a1ef7f134f02ca9d75b47b937fe"
REPORT_01_JSON_DIR = REPORTS / "2026-08-14"
REPORT_01_FREEZE_HTML = (
    REPORTS / "2026-08-15" / "freeze" / "index-v3-review-01.v1-freeze-20260815T105439Z.html"
)
AHMAD_HANDOFF_HTML = (
    REPORTS / "2026-08-15" / "freeze" / "ahmad-v3-handoff" / "index-v3-review-01.html"
)

# Frozen Report 01 hash (Olly-approved week pill). Do not mutate.
REPORT_01_SHA256_BASELINE = "3b68a5a7192928d19b82b8089230bf03be22faa4a13d6258902b6b42bc77428c"

REPORT_01_PROTECTED = (
    REPORT_01_HTML,
    REPORT_02_BASELINE_HTML,
    REPORT_03_BASELINE_HTML,
    REPORT_01_FREEZE_HTML,
    AHMAD_HANDOFF_HTML,
)

# Historical Aug-15 pack — read-only reference; not the default write target.
_HISTORICAL_AUTOJOB01 = REPORTS / "2026-08-15" / "autojob01"


def resolve_autojob01_dir() -> Path:
    """Current-run artifact dir. Weekly sets AUTOJOB01_RUN_DIR before AUTOJOB01."""
    env = os.environ.get("AUTOJOB01_RUN_DIR", "").strip()
    if env:
        return Path(env)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_dir = REPORTS / today / "autojob01"
    hist_manifest = _HISTORICAL_AUTOJOB01 / "AUTOJOB01-MANIFEST.json"
    if today_dir.is_dir() and (today_dir / "AUTOJOB01-MANIFEST.json").is_file():
        return today_dir
    if hist_manifest.is_file():
        return _HISTORICAL_AUTOJOB01
    return today_dir


def autojob01_paths() -> dict[str, Path]:
    d = resolve_autojob01_dir()
    return {
        "AUTOJOB01_DIR": d,
        "MANIFEST_JSON": d / "AUTOJOB01-MANIFEST.json",
        "MANIFEST_TXT": d / "AUTOJOB01-MANIFEST.txt",
        "BASELINE_HASHES": d / "REPORT01-BASELINE-HASHES.txt",
        "DELTA_JSON": d / "REPORT01-TO-02-DELTA.json",
        "DELTA_TXT": d / "REPORT01-TO-02-DELTA.txt",
    }


# Lazy default for imports that expect module-level names (tests / legacy).
_p = autojob01_paths()
AUTOJOB01_DIR = _p["AUTOJOB01_DIR"]
MANIFEST_JSON = _p["MANIFEST_JSON"]
MANIFEST_TXT = _p["MANIFEST_TXT"]
BASELINE_HASHES = _p["BASELINE_HASHES"]
DELTA_JSON = _p["DELTA_JSON"]
DELTA_TXT = _p["DELTA_TXT"]


def is_report_01_path(path: Path) -> bool:
    resolved = path.resolve()
    if resolved in {p.resolve() for p in REPORT_01_PROTECTED}:
        return True
    try:
        rel = resolved.relative_to(REPORT_01_JSON_DIR.resolve())
    except ValueError:
        return False
    return rel.suffix == ".json" and "-v3" in rel.name
