"""Inject convergence Variant A footer into Report 02 articles."""

from __future__ import annotations

import re
from typing import Any

from lib.v3.convergence.profiles import PROFILES
from lib.v3.convergence.render_footer import ensure_convergence_css, render_footer, validate_asset_payload

_FOOTER_RE = re.compile(
    r'<section class="cv-convergence"[^>]*data-convergence-source="autojob01-v1"[^>]*>.*?</section>',
    re.S,
)


def _strip_footers(body: str) -> str:
    return _FOOTER_RE.sub("", body)


def _inject_footer(body: str, footer: str) -> str:
    body = _strip_footers(body)
    return body.rstrip() + footer


def apply_convergence(
    html: str,
    bundle: dict[str, Any],
    log: list[str],
    touches: list[dict] | None = None,
) -> str:
    """Append one convergence footer per asset article. Fails safe when data missing."""
    conv = bundle.get("convergence") or {}
    assets = conv.get("assets") or {}
    if not assets:
        log.append("APPLY_SKIP CONVERGENCE no bundle.convergence")
        return html

    html = ensure_convergence_css(html)
    injected = 0
    skipped = 0

    for sym, profile in PROFILES.items():
        slug = profile.slug
        payload = assets.get(sym)
        if not payload:
            log.append(f"APPLY_SKIP CONVERGENCE.{sym} missing")
            skipped += 1
            continue
        errs = validate_asset_payload(payload)
        if errs:
            log.append(f"APPLY_SKIP CONVERGENCE.{sym} invalid: {'; '.join(errs)}")
            skipped += 1
            continue

        footer = render_footer(payload)
        pat = re.compile(
            rf'(<article\b(?=[^>]*\bdata-asset="{re.escape(slug)}")[^>]*>)(.*?)(</article>)',
            re.S,
        )
        m = pat.search(html)
        if not m:
            log.append(f"APPLY_MISS CONVERGENCE.{sym} article")
            skipped += 1
            continue

        new_body = _inject_footer(m.group(2), footer)
        html = html[: m.start()] + m.group(1) + new_body + m.group(3) + html[m.end() :]
        log.append(f"APPLY_OK CONVERGENCE.{sym}")
        injected += 1
        if touches is not None:
            touches.append(
                {
                    "asset": slug,
                    "section": "convergence_footer",
                    "needle": payload.get("headline", ""),
                    "field": f"CONVERGENCE.{sym}",
                }
            )

    log.append(f"APPLY_OK CONVERGENCE injected={injected} skipped={skipped}")
    return html
