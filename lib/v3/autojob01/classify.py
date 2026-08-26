"""Identity-based 274-field classification. Counts must stay 244/20/3/7/0."""

from __future__ import annotations

from typing import Any

from lib.v3.autojob01.canonical import canonical_id
from lib.v3.autojob01.sources import sources_for

DYNAMIC = "DYNAMIC"
STATIC = "STATIC"
UNKNOWN = "UNKNOWN"
MULTI = "MULTI-SOURCE / CONFLICT"
NONDATA = "NON-DATA"

_STATIC_MARKERS = (
    "2025 rev",
    "$17M 2026 H1",
    "FY26 guide",
    "1.00B Max",
    "252.0M Investors",
    "220.0M Contributors",
    "800.0M Max",
    "Aug 10 fee share",
    "51.5% AUG 10",
    "Jan 2025 fees",
    "Jan 2025 TVL",
    "12% real",
    "12%→HELD",
    "12% fees → RAY held",
    "12% fee→RAY buybacks",
    "ETH canonical 1B",
    "$17 M",
    "$17M / $17M",
    "$17M H1 2026 disclosed",
    "2025 $17M · 2026 H1 $17M",
    "~287M to labelled WM OTC",
    "~287M PUMP sent to labelled Wintermute OTC",
    "~1.7 %",
)
_UNKNOWN_MARKERS = (
    "UNKNOWN 3/6/12m",
    "Exact 3/6/12m releases",
    "Do not invent 9.92M",
)
_MULTI_MARKERS = (
    "22.2% CG",
    "29.9% HL",
    "555.40M Foundation circ",
    "CG 22.2% · HL 29.9%",
    "CG 22.2% · Hyperliquid 29.9%",
    "Circ CONFLICT 22%/30%",
    "Minority float + ~412M emissions + ~241M HyperLabs NCU",
)


def classify_one(text: str, asset: str = "") -> tuple[str, str, str, str | None]:
    if any(m in text for m in _UNKNOWN_MARKERS):
        return UNKNOWN, "No first-party dated series — keep UNKNOWN", "none", None
    if any(m in text for m in _MULTI_MARKERS):
        return MULTI, "Two approved sources — show both, never average", "source A", "source B"
    if (asset or "").lower() == "pump" and text.strip() in ("31.2 %", "31.2%"):
        return STATIC, "Remaining scheduled tokens (311.67B / 1T) — not a weekly Llama print", "docs / disclosure", None
    if any(m in text for m in _STATIC_MARKERS):
        return STATIC, "Historical disclosure or tokenomics parameter", "docs / disclosure", None
    return DYNAMIC, "Weekly refresh from the same approved source(s) as Report 01", "approved live feed", None


def classify_inventory(fields: list[dict[str, Any]]) -> dict[str, Any]:
    if len(fields) != 274:
        raise RuntimeError(f"inventory is {len(fields)}, must be 274")
    counts = {DYNAMIC: 0, STATIC: 0, UNKNOWN: 0, MULTI: 0, NONDATA: 0}
    out: list[dict[str, Any]] = []
    for i, f in enumerate(fields):
        cls, reason, s1, s2 = classify_one(f.get("report_01_text") or "", f.get("asset") or "")
        row = {
            "asset": f["asset"],
            "visible_section": f["visible_section"],
            "visible_label": f["visible_label"],
            "report_01_text": f["report_01_text"],
            "classification": cls,
        }
        s1, s2 = sources_for(row)
        counts[cls] += 1
        fid = canonical_id(f["asset"], f["visible_section"], f["report_01_text"])
        out.append(
            {
                "field_id": fid,
                "asset": f["asset"],
                "visible_section": f["visible_section"],
                "visible_label": f["visible_label"],
                "report_01_text": f["report_01_text"],
                "report_01_numbers": f.get("numbers") or [],
                "classification": cls,
                "reason": reason,
                "source_1": s1,
                "source_2": s2,
                "conflict_policy": "show_all_no_average" if cls == MULTI else "n/a",
                "unknown_policy": "keep_UNKNOWN" if cls == UNKNOWN else "fail_loud_if_required_source_down",
                "refresh": "weekly" if cls in {DYNAMIC, MULTI} else "no_weekly_refresh",
            }
        )
    total = sum(counts.values())
    if total != 274 or counts[UNKNOWN] != 3 or counts[MULTI] != 7:
        raise RuntimeError(f"class counts drifted: {counts}")
    return {
        "schema": "autojob01-manifest-v4-canonical-ids",
        "visible_field_count": 274,
        "classification_counts": counts,
        "classification_total": total,
        "reconcile_ok": total == 274,
        "fields": out,
    }
