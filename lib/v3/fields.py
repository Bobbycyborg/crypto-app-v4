"""V3 field metadata — data honesty model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def field(
    metric_id: str,
    label: str,
    value: Any,
    *,
    unit: str | None = None,
    as_of: str | None = None,
    source: str | None = None,
    source_url: str | None = None,
    fetched_at: str | None = None,
    data_status: str = "LIVE",
    epistemic: str = "KNOWN",
    impl_status: str = "PRODUCTION_READY",
    confidence: str = "MEDIUM",
    note: str | None = None,
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "label": label,
        "value": value,
        "unit": unit,
        "as_of": as_of,
        "source": source,
        "source_url": source_url,
        "fetched_at": fetched_at or now_iso(),
        "data_status": data_status,
        "epistemic_status": epistemic,
        "implementation_status": impl_status,
        "confidence": confidence,
        "note": note,
    }


def missing_field(
    metric_id: str,
    label: str,
    *,
    data_status: str = "MISSING",
    impl_status: str = "NEEDS_ENGINEERING",
    note: str | None = None,
    source_url: str | None = None,
) -> dict[str, Any]:
    return field(
        metric_id,
        label,
        None,
        data_status=data_status,
        epistemic="UNKNOWN",
        impl_status=impl_status,
        confidence="NOT_ASSESSED",
        note=note or "Feed not wired in Phase 1.",
        source_url=source_url,
    )


def family_block(
    family_id: str,
    title: str,
    question: str,
    display_state: str,
    fields: list[dict],
    *,
    note: str | None = None,
    impl_status: str = "PRODUCTION_READY",
) -> dict[str, Any]:
    return {
        "family_id": family_id,
        "title": title,
        "question": question,
        "display_state": display_state,
        "fields": fields,
        "note": note,
        "implementation_status": impl_status,
    }


def concerning_meter(categories: list[dict[str, Any]] | None) -> int:
    """Confirmed concerning = ACTIVE only. PARTIAL / UNKNOWN / CONFLICT stay visible, not counted."""
    n = 0
    for c in categories or []:
        if str(c.get("state") or "").upper() == "ACTIVE":
            n += 1
    return n


def _unit(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def pack_risk_confirmation(
    categories: list[dict[str, Any]],
    source: str,
) -> dict[str, Any]:
    """Risk & Confirmation counter: CONCERNS = ACTIVE+PARTIAL, POSITIVES = CLEAR, UNKNOWN = rest."""
    n_c = n_p = n_u = 0
    for c in categories or []:
        st = str(c.get("state") or "").upper()
        if st in ("ACTIVE", "PARTIAL"):
            n_c += 1
        elif st == "CLEAR":
            n_p += 1
        else:
            n_u += 1
    line = (
        f"{n_c} {_unit(n_c, 'CONCERN', 'CONCERNS')} · "
        f"{n_p} {_unit(n_p, 'POSITIVE', 'POSITIVES')} · "
        f"{n_u} UNKNOWN"
    )
    return {
        "schema": "risk_confirmation",
        "schema_version": 1,
        "section_title": "RISK & CONFIRMATION",
        "counter_line": line,
        "n_concerns": n_c,
        "n_positives": n_p,
        "n_unknown": n_u,
        "categories": categories,
        "meter_active": n_c,
        "meter_total": len(categories),
        "source": source,
    }


def category_state(
    category_id: str,
    label: str,
    state: str,
    *,
    detail: str | None = None,
    summary: str | None = None,
    impl_status: str = "PRODUCTION_READY",
) -> dict[str, Any]:
    return {
        "category_id": category_id,
        "label": label,
        "state": state,
        "detail": detail,
        "summary": summary,
        "implementation_status": impl_status,
    }
