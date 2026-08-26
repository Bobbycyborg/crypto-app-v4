"""V3 weekly automation — asset discovery and paths. Read live repo state at runtime."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from lib.dashboard_v1 import ASSET_SLUGS
from lib.paths import CONFIG, REPORTS, ROOT
from lib.v3.html_v3 import SLUG_TO_SYMBOL, V3_ASSET_SLUGS

CANONICAL_HTML = ROOT / "index-v4.html"
SOURCE_REGISTRY = CONFIG / "source-registry-v3.json"
WEEKLY_RUNS = REPORTS / "weekly-runs"

# HTML data-asset slug → dated JSON stem (SPX page slug is spx6900; files are spx-v3.json).
JSON_STEM = {
    "spx6900": "spx",
}

REQUIRED_SCRIPTS = (
    ROOT / "scripts" / "build_v3_review_01.py",
    ROOT / "scripts" / "audit_data_sources_v3.py",
    ROOT / "scripts" / "qa_v3_final.py",
    ROOT / "scripts" / "autojob01_run.py",
)

REQUIRED_PROBES = ("coingecko_global", "binance")


def configured_slugs() -> tuple[str, ...]:
    """Current V3 page set. Dashboard strip order ∩ V3_ASSET_SLUGS — not wallet-only config."""
    ordered = [slug for _, _, slug in ASSET_SLUGS if slug in V3_ASSET_SLUGS]
    extra = sorted(V3_ASSET_SLUGS.difference(ordered))
    return tuple(ordered + extra)


def symbol_for(slug: str) -> str:
    return SLUG_TO_SYMBOL.get(slug, slug.upper())


def ticker_aliases(slug: str) -> tuple[str, ...]:
    """Visible hero ticker. SPX page uses SPX, config/symbol map uses SPX6900."""
    primary = symbol_for(slug)
    if slug == "spx6900":
        return ("SPX", "SPX6900")
    return (primary,)


def json_stem(slug: str) -> str:
    return JSON_STEM.get(slug, slug)


def v3_json_name(slug: str) -> str:
    return f"{json_stem(slug)}-v3.json"


def reports_root() -> Path:
    env = os.environ.get("WEEKLY_V3_REPORTS")
    return Path(env) if env else REPORTS


def latest_dated_report_dir(root: Path | None = None) -> Path | None:
    base = root if root is not None else reports_root()
    if not base.is_dir():
        return None
    dated = sorted(
        [p for p in base.iterdir() if p.is_dir() and len(p.name) == 10 and p.name[4] == "-"],
        reverse=True,
    )
    return dated[0] if dated else None


def latest_v3_json(slug: str, root: Path | None = None) -> Path | None:
    """Newest dated {stem}-v3.json. Assets land in different date folders."""
    name = v3_json_name(slug)
    found: Path | None = None
    base = root if root is not None else reports_root()
    if not base.exists():
        return None
    for d in sorted(base.iterdir()):
        if not d.is_dir() or len(d.name) != 10 or d.name[4] != "-":
            continue
        p = d / name
        if p.is_file():
            found = p
    return found


def freeze_dir_for(report_date: str | None = None) -> Path:
    day = report_date or date.today().isoformat()
    return REPORTS / day / "freeze"
