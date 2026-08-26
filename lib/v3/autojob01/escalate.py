"""Contradiction escalation. Never rewrite frozen thesis/stance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lib.v3.autojob01.protect import write_text
from lib.v3.autojob01.paths import AUTOJOB01_DIR

# Stance / thesis words AUTOJOB01 must not rewrite.
FROZEN_WORD_KEYS = (
    "headline",
    "stance",
    "thesis",
    "explanation",
    "summary",
    "v3_posture",
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def contradiction_score(old: Any, new: Any, frozen_words: str) -> str | None:
    """Return a flag if a number flip likely invalidates frozen wording. Heuristic only."""
    if old is None or new is None:
        return None
    try:
        o, n = float(old), float(new)
    except (TypeError, ValueError):
        return None
    if o == 0:
        return None
    change = (n - o) / abs(o)
    words = (frozen_words or "").upper()
    bearish = any(w in words for w in ("WEAK", "BEAR", "BELOW", "DRAIN", "HEAVY", "SOFT"))
    bullish = any(w in words for w in ("STRONG", "BULL", "AHEAD", "SUPPORT"))
    # Material: >25% relative move on a figure the wording leans on.
    if abs(change) < 0.25:
        return None
    if bearish and change > 0.25:
        return "FRESH_NUMBER_UP_VS_BEARISH_WORDS"
    if bullish and change < -0.25:
        return "FRESH_NUMBER_DOWN_VS_BULLISH_WORDS"
    if abs(change) >= 0.5:
        return "FRESH_NUMBER_MOVED_50PCT"
    return None


def escalate(
    field_id: str,
    *,
    report_01_value: Any,
    first_pull: Any,
    re_pull: Any,
    bounded_note: str,
    frozen_words: str,
    source: str,
    thesis_relevant: bool,
) -> dict[str, Any]:
    """Verify → bounded research → artifact. Do not rewrite wording."""
    row = {
        "field_id": field_id,
        "flag": "REVIEW REQUIRED — FRESH DATA MAY INVALIDATE FROZEN WORDING",
        "escalation": "CRYPTO_7_OLLY",
        "thesis_rewritten": False,
        "report_01_value": report_01_value,
        "first_pull": first_pull,
        "re_pull": re_pull,
        "re_pull_confirmed": first_pull == re_pull or (
            _close(first_pull, re_pull)
        ),
        "bounded_research": bounded_note,
        "frozen_words_excerpt": (frozen_words or "")[:280],
        "source": source,
        "thesis_relevant": thesis_relevant,
        "action": "leave frozen wording; do not publish a silent rewrite",
        "created_at": _now(),
    }
    return row


def _close(a: Any, b: Any) -> bool:
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)
    base = max(abs(fa), abs(fb), 1e-12)
    return abs(fa - fb) / base < 0.01


VISIBLE_BANNER = "🚨 REVIEW REQUIRED — THESIS MAY HAVE CHANGED"
RUN_STATUS = "REVIEW_REQUIRED"
GATE_STATUS = "PASS_WITH_REVIEW"


def paint_review_required_html(html: str, *, asset: str) -> str:
    """Paint visible REVIEW REQUIRED on a copy. Never rewrite stance/thesis text."""
    style = (
        '<style id="autojob-review-required-css">'
        "#autojob-run-status,.autojob-review-required{"
        "display:block;margin:12px 16px;padding:12px 16px;"
        "background:#3a0d0d;color:#ffd2d2;border:1px solid #c44;"
        "font:700 15px/1.35 ui-sans-serif,system-ui,sans-serif}"
        "</style>"
    )
    bar = (
        f'<div id="autojob-run-status" role="status" '
        f'data-run-status="{RUN_STATUS}" data-gate-status="{GATE_STATUS}">'
        f"{VISIBLE_BANNER}</div>"
    )
    asset_bar = (
        f'<div class="autojob-review-required" role="status" '
        f'data-run-status="{RUN_STATUS}" data-gate-status="{GATE_STATUS}" '
        f'data-affected-asset="{asset}">{VISIBLE_BANNER}</div>'
    )
    if "</head>" in html:
        html = html.replace("</head>", style + "</head>", 1)
    if "<body>" in html:
        html = html.replace("<body>", "<body>\n" + bar, 1)
    html = html.replace(
        f'<article class="report asset-v3-report is-hidden" data-asset="{asset}">',
        f'<article class="report asset-v3-report" data-asset="{asset}">',
        1,
    )
    marker = f'data-asset="{asset}"'
    start = html.find(marker)
    if start < 0:
        raise ValueError(f"asset {asset} missing from HTML")
    h = html.find('<div class="alt-stance-headline">', start)
    if h < 0:
        raise ValueError(f"stance headline missing for {asset}")
    end = html.find("</div>", h)
    html = html[: end + 6] + asset_bar + html[end + 6 :]
    return html


def write_escalation_artifact(flags: list[dict[str, Any]]) -> Any:
    AUTOJOB01_DIR.mkdir(parents=True, exist_ok=True)
    path = AUTOJOB01_DIR / "REVIEW-REQUIRED-ESCALATION.json"
    payload = {
        "schema": "autojob01-escalation-v1",
        "created_at": _now(),
        "count": len(flags),
        "note": (
            "Frozen stance/thesis was not rewritten. "
            "Crypto 7 / Olly decide whether wording must change."
        ),
        "flags": flags,
    }
    import json

    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    md = AUTOJOB01_DIR / "REVIEW-REQUIRED-ESCALATION.md"
    lines = [
        "# REVIEW REQUIRED — escalation for Crypto 7 / Olly",
        "",
        "Frozen wording was **not** rewritten.",
        "",
    ]
    if not flags:
        lines.append("No thesis-relevant contradictions after re-pull.")
    for f in flags:
        lines += [
            f"## {f['field_id']}",
            f"- Report 01: `{f['report_01_value']}`",
            f"- First pull: `{f['first_pull']}`",
            f"- Re-pull: `{f['re_pull']}`",
            f"- Bounded note: {f['bounded_research']}",
            f"- Frozen words: {f['frozen_words_excerpt']}",
            "",
        ]
    write_text(md, "\n".join(lines) + "\n")
    return path
