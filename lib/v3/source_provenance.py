"""Source provenance states for live vs cache vs failure."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

LIVE = "LIVE"
CACHE_FALLBACK = "CACHE_FALLBACK"
SUBSTITUTE_SOURCE = "SUBSTITUTE_SOURCE"
SOURCE_FAILED = "SOURCE_FAILED"
UNKNOWN = "UNKNOWN"

PROVENANCE_STATES = frozenset({LIVE, CACHE_FALLBACK, SUBSTITUTE_SOURCE, SOURCE_FAILED, UNKNOWN})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cache_age_days(as_of: str | None, *, now: date | None = None) -> int | None:
    if not as_of:
        return None
    try:
        if "T" in as_of:
            d = datetime.fromisoformat(as_of.replace("Z", "+00:00")).date()
        else:
            d = date.fromisoformat(str(as_of)[:10])
    except ValueError:
        return None
    ref = now or datetime.now(timezone.utc).date()
    return max(0, (ref - d).days)


def annotate_payload(
    payload: dict[str, Any],
    *,
    provenance: str,
    as_of: str | None = None,
    cache_fallback: bool | None = None,
    live_error: str | None = None,
    freshness: str | None = None,
) -> dict[str, Any]:
    """Return a shallow copy with provenance metadata."""
    out = dict(payload)
    out["provenance"] = provenance if provenance in PROVENANCE_STATES else UNKNOWN
    if as_of is not None:
        out["as_of"] = as_of
    age = cache_age_days(out.get("as_of") or out.get("cached_at") or out.get("fetched_at"))
    if age is not None:
        out["cache_age_days"] = age
    if cache_fallback is not None:
        out["cache_fallback"] = cache_fallback
    if live_error is not None:
        out["live_error"] = live_error
    if freshness is not None:
        out["freshness"] = freshness
    return out


def mark_live(payload: dict[str, Any], *, as_of: str | None = None) -> dict[str, Any]:
    return annotate_payload(
        payload,
        provenance=LIVE,
        as_of=as_of,
        cache_fallback=False,
        freshness="CURRENT",
    )


def mark_cache_fallback(
    payload: dict[str, Any],
    *,
    as_of: str | None = None,
    live_error: str | None = None,
) -> dict[str, Any]:
    return annotate_payload(
        payload,
        provenance=CACHE_FALLBACK,
        as_of=as_of,
        cache_fallback=True,
        live_error=live_error,
        freshness="STALE",
    )


def mark_substitute_source(payload: dict[str, Any], *, as_of: str | None = None, live_error: str | None = None) -> dict[str, Any]:
    return annotate_payload(
        payload,
        provenance=SUBSTITUTE_SOURCE,
        as_of=as_of,
        cache_fallback=True,
        live_error=live_error,
        freshness="STALE",
    )


def mark_source_failed(payload: dict[str, Any], *, live_error: str | None = None) -> dict[str, Any]:
    return annotate_payload(
        payload,
        provenance=SOURCE_FAILED,
        live_error=live_error,
        cache_fallback=False,
        freshness="MISSING",
    )


def stale_label(payload: dict[str, Any]) -> str | None:
    """HTML-facing label e.g. STALE · AS OF 13 AUG."""
    prov = payload.get("provenance")
    if prov not in (CACHE_FALLBACK, SUBSTITUTE_SOURCE) and payload.get("freshness") != "STALE":
        return None
    as_of = payload.get("as_of")
    if not as_of:
        return "STALE"
    try:
        d = date.fromisoformat(str(as_of)[:10])
        return f"STALE · AS OF {d.strftime('%d %b').upper()}"
    except ValueError:
        return "STALE"


def summarize_bundle_provenance(bundle: dict[str, Any]) -> dict[str, Any]:
    """Collect provenance warnings for RUN-SUMMARY / weekly run.json."""
    warnings: list[str] = []
    cache_fallback_count = 0
    cache_fallback_fields: set[str] = set()

    def _note(field: str, row: dict[str, Any]) -> None:
        nonlocal cache_fallback_count
        prov = row.get("provenance")
        if prov in (CACHE_FALLBACK, SUBSTITUTE_SOURCE) or row.get("cache_fallback"):
            cache_fallback_count += 1
            cache_fallback_fields.add(field)
            lbl = stale_label(row) or prov
            err = row.get("live_error")
            msg = f"{field}: {lbl}"
            if err:
                msg += f" ({err[:120]})"
            warnings.append(msg)

    mkt = (bundle.get("market") or {}).get("data") or {}
    etf = mkt.get("etf") or {}
    for sym, row in (etf.get("assets") or {}).items():
        if isinstance(row, dict):
            _note(f"MARKET.etf.{sym}", row)

    fg = mkt.get("fear_greed") or {}
    if isinstance(fg, dict) and fg.get("provenance"):
        _note("MARKET.fear_greed", fg)

    feeds = bundle.get("feeds") or {}
    zec = feeds.get("zec") or {}
    if isinstance(zec, dict):
        _note("feeds.zec_shielded", zec)

    sol_rpc = feeds.get("sol_rpc") or {}
    if isinstance(sol_rpc, dict) and sol_rpc.get("supply_provenance"):
        _note("feeds.sol_rpc_supply", sol_rpc)

    return {
        "provenance_warnings": warnings,
        "cache_fallback_count": cache_fallback_count,
        "cache_fallback_fields": sorted(cache_fallback_fields),
        "summarized_at": _now_iso(),
    }
