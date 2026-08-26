"""ATH retracement framing — user-visible copy only.

Retracement from ATH is a natural part of a bull. Not bad on its own.
Question: how far we expect it to go, and when we expect it to turn.
~90% off, late in a bull → zombie-coin territory (Invest Answers / James).
Exception: ZEC late-cycle meteoric rise.
Do not put this back into Risk & Confirmation.
"""

from __future__ import annotations

from typing import Any

ZOMBIE_PCT = 85.0


def retrace_pct(dd: Any) -> float | None:
    if dd is None:
        return None
    try:
        return abs(float(dd))
    except (TypeError, ValueError):
        return None


def retrace_label(dd: Any) -> str:
    n = retrace_pct(dd)
    if n is None:
        return "ATH retracement UNKNOWN"
    return f"~{n:.0f}% retraced from ATH"


def timing_caption(ath_disp: Any, dd: Any) -> str:
    ath = ath_disp if ath_disp not in (None, "") else "ATH"
    n = retrace_pct(dd)
    if n is None:
        return str(ath)
    return f"{ath} · ~{n:.0f}% retraced"


def meaning(slug: str, dd: Any) -> str:
    n = retrace_pct(dd) or 0.0
    s = (slug or "").strip().lower()
    base = (
        "Retracement from ATH is a natural part of a bull — not bad on its own. "
        "The question is how far it goes, and when it turns."
    )
    if s == "zec":
        return (
            base
            + " ZEC is the exception: a meteoric rise late in the bull, not a 90%-off zombie."
        )
    if s == "btc":
        return base + " ~50% off is a mid retrace, not zombie territory. Watch the turn."
    if n >= ZOMBIE_PCT:
        return (
            base
            + " This deep, this late in a bull (~90% off) is zombie-coin territory "
            "(Invest Answers). Can still be wrong — ZEC showed a late-cycle exception."
        )
    return base + " Distance alone is not a verdict."


def rc_title(slug: str, dd: Any) -> str:
    s = (slug or "").strip().lower()
    n = retrace_pct(dd)
    label = retrace_label(dd)
    if s == "zec":
        return "Late-bull rise — not a zombie print"
    if s == "btc":
        return "~50% retraced from Oct 2025 ATH"
    if n is not None and n >= ZOMBIE_PCT:
        return f"{label} · zombie-risk zone"
    return label
