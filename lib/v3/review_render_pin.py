"""Pin RENDER article HTML in Review-01 builds — PUMP edits must not alter RENDER.

Safety stays on: every Review-01 build replaces generated RENDER with the frozen
canonical article verified by SHA-256.

To adopt a newly approved RENDER page, call adopt_render_canonical() once
(via RENDER_UNLOCK_CANONICAL=1 in the build script, or directly). That freezes
the exact article, updates the dated path + SHA, and keeps pin safety enabled.
"""

from __future__ import annotations

import hashlib
import os
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DIR = ROOT / "canonical"
# Active freeze — Stage-1 completion RENDER (2026-08-12)
CANONICAL_RENDER_ARTICLE = CANONICAL_DIR / "render-article-review-01-2026-08-12.html"
CANONICAL_RENDER_ZIP = CANONICAL_DIR / "2026-08-12-render.zip"
# Legacy bootstrap only (never preferred once 2026-08-12 article exists)
_LEGACY_RENDER_ARTICLE = CANONICAL_DIR / "render-article-review-01-2026-08-10.html"
_LEGACY_RENDER_ZIP = CANONICAL_DIR / "2026-08-10.zip"
CANONICAL_RENDER_SHA256 = (
    "c2f357a1c001b95f9d7822d11d544bf9b3e59b74ced1a1d90a0f0af35aefda36"
)


class RenderCanonicalError(RuntimeError):
    """Frozen RENDER canonical missing or failed SHA-256 verification."""


def _extract_render_article(html: str) -> str:
    m = re.search(
        r'(<article class="report asset-v3-report[^"]*" data-asset="render">.*?</article>)',
        html,
        re.S,
    )
    if not m:
        raise RenderCanonicalError("No RENDER <article> found in source HTML")
    return m.group(1)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _verify_canonical(article: str) -> str:
    digest = _sha256(article)
    if digest != CANONICAL_RENDER_SHA256:
        raise RenderCanonicalError(
            "RENDER canonical SHA-256 mismatch — "
            f"expected {CANONICAL_RENDER_SHA256}, got {digest}. "
            "Never silently use regenerated RENDER."
        )
    return article


def _zip_candidates() -> list[Path]:
    env_zip = os.environ.get("RENDER_CANONICAL_ZIP")
    candidates = [
        CANONICAL_RENDER_ZIP,
        _LEGACY_RENDER_ZIP,
        ROOT.parent / "2026-08-12-render.zip",
        ROOT.parent / "2026-08-10.zip",
    ]
    if env_zip:
        candidates.insert(0, Path(env_zip))
    return candidates


def install_render_canonical_from_zip(zip_path: Path) -> Path:
    """Extract verified RENDER article from frozen zip into canonical/."""
    if not zip_path.exists():
        raise RenderCanonicalError(f"Frozen zip not found: {zip_path}")

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        review_names = [
            n
            for n in names
            if n.endswith("index-v3-review-01.html") and not n.startswith("__MACOSX")
        ]
        if not review_names:
            raise RenderCanonicalError(
                f"No index-v3-review-01.html in zip: {zip_path}"
            )
        review_names.sort(key=len)
        html = zf.read(review_names[0]).decode("utf-8")

    article = _verify_canonical(_extract_render_article(html))
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
    CANONICAL_RENDER_ARTICLE.write_text(article, encoding="utf-8")
    return CANONICAL_RENDER_ARTICLE


def ensure_render_canonical() -> Path:
    """Load frozen canonical, bootstrapping from zip only when article file is absent."""
    if CANONICAL_RENDER_ARTICLE.exists():
        article = CANONICAL_RENDER_ARTICLE.read_text(encoding="utf-8")
        _verify_canonical(article)
        return CANONICAL_RENDER_ARTICLE

    # One-time migrate: approved 2026-08-12 article may still live under legacy filename
    if _LEGACY_RENDER_ARTICLE.exists():
        article = _LEGACY_RENDER_ARTICLE.read_text(encoding="utf-8")
        if _sha256(article) == CANONICAL_RENDER_SHA256:
            CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
            CANONICAL_RENDER_ARTICLE.write_text(article, encoding="utf-8")
            return CANONICAL_RENDER_ARTICLE

    for zip_path in _zip_candidates():
        if zip_path.exists():
            return install_render_canonical_from_zip(zip_path)

    raise RenderCanonicalError(
        "Frozen RENDER canonical unavailable. "
        f"Place verified article at {CANONICAL_RENDER_ARTICLE} "
        f"or frozen zip at {CANONICAL_RENDER_ZIP} "
        f"(SHA-256 {CANONICAL_RENDER_SHA256})."
    )


def adopt_render_canonical(html: str) -> str:
    """Freeze the RENDER article from generated HTML as the new pinned canonical.

    Updates the dated article file and persists SHA into this module.
    Pin safety remains enabled afterward.
    Returns the frozen article text.
    """
    global CANONICAL_RENDER_SHA256

    article = _extract_render_article(html)
    # Refuse to freeze obviously stale Stage-0 RENDER
    stale_marks = ("HOLD / WAIT", "NOT LIVE YET", "LIVE SERIES NEEDED", "NOT BUILT")
    if any(m in article for m in stale_marks):
        raise RenderCanonicalError(
            "Refusing to freeze stale RENDER article "
            f"(contains one of {stale_marks})."
        )
    if "NETWORK USAGE REAL · RECENT BME NET INFLATIONARY · MARKET STRUCTURE WEAK" not in article:
        raise RenderCanonicalError(
            "Refusing to freeze RENDER article — approved Current Stance headline missing."
        )

    digest = _sha256(article)
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
    CANONICAL_RENDER_ARTICLE.write_text(article, encoding="utf-8")
    # Keep legacy path in sync so older tooling still sees the approved article
    _LEGACY_RENDER_ARTICLE.write_text(article, encoding="utf-8")

    pin_path = Path(__file__)
    pin_src = pin_path.read_text(encoding="utf-8")
    pin_src2, n = re.subn(
        r'CANONICAL_RENDER_SHA256 = \(\s*"[0-9a-f]{64}"\s*\)',
        f'CANONICAL_RENDER_SHA256 = (\n    "{digest}"\n)',
        pin_src,
        count=1,
    )
    if n != 1:
        raise RenderCanonicalError(f"Failed to persist RENDER canonical SHA (n={n})")
    pin_path.write_text(pin_src2, encoding="utf-8")
    CANONICAL_RENDER_SHA256 = digest
    return article


def canonical_render_article() -> str:
    ensure_render_canonical()
    return CANONICAL_RENDER_ARTICLE.read_text(encoding="utf-8")


def pin_render_article(html: str) -> str:
    """Replace generated RENDER article with frozen canonical copy."""
    canonical = canonical_render_article()
    replaced, count = re.subn(
        r'<article class="report asset-v3-report[^"]*" data-asset="render">.*?</article>',
        canonical,
        html,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RenderCanonicalError("Generated review HTML has no RENDER article to pin")
    return replaced
