"""Per-field DYNAMIC coverage. 244 = refreshed + source_failure. Pair by identity, not index."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable

from lib.v3.autojob01.canonical import canonical_id, load_canonical_fields
from lib.v3.autojob01.classify import DYNAMIC, MULTI, STATIC, UNKNOWN, classify_one
from lib.v3.autojob01.inventory import extract_fields


def _plain(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", "", s)


def _key(f: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        f.get("asset") or "",
        f.get("visible_section") or "",
        f.get("visible_label") or "",
        f.get("css_class") or "",
    )


_FIELD_ID_RE = re.compile(r"^F\d{4}$")


def resolve_cache_fallback_field_ids(keys: Iterable[str] | None) -> frozenset[str]:
    """Map provenance logical keys (MARKET.etf.BTC) to manifest field_ids (F0139)."""
    out: set[str] = set()
    keys_list = [k for k in (keys or ()) if k]
    if not keys_list:
        return frozenset()

    logical: list[str] = []
    for k in keys_list:
        if _FIELD_ID_RE.fullmatch(k):
            out.add(k)
        else:
            logical.append(k)
    if not logical:
        return frozenset(out)

    manifest = load_canonical_fields()
    etf_amts = [
        f
        for f in manifest
        if (f.get("asset") or "") == "MARKET"
        and (f.get("visible_section") or "") == "market_top"
        and (f.get("visible_label") or "") == "amt"
        and "Farside" in str(f.get("source_1") or "")
    ]
    etf_by_sym = {
        "BTC": etf_amts[0:2],
        "ETH": etf_amts[2:4],
        "SOL": etf_amts[4:6],
    }

    for key in logical:
        if key.startswith("MARKET.etf."):
            sym = key.rsplit(".", 1)[-1]
            pair = etf_by_sym.get(sym) or []
            if pair:
                out.add(str(pair[0]["field_id"]))
        elif key == "feeds.zec_shielded":
            for f in manifest:
                if (f.get("asset") or "").lower() == "zec" and "shielded" in str(f.get("report_01_text") or "").lower():
                    out.add(str(f["field_id"]))
                    break
        elif key == "MARKET.fear_greed":
            for f in manifest:
                if (f.get("asset") or "") == "MARKET" and (f.get("visible_section") or "") == "market_top":
                    txt = str(f.get("report_01_text") or "").lower()
                    if "fear" in txt or "greed" in txt:
                        out.add(str(f["field_id"]))
                        break
        elif key == "feeds.sol_rpc_supply":
            for f in manifest:
                if (f.get("asset") or "").lower() == "sol" and "supply" in str(f.get("report_01_text") or "").lower():
                    out.add(str(f["field_id"]))
                    break
    return frozenset(out)


def _pair(f01: list[dict[str, Any]], f02: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any] | None]]:
    buckets: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for b in f02:
        buckets[_key(b)].append(b)
    used: dict[tuple, int] = defaultdict(int)
    out: list[tuple[dict[str, Any], dict[str, Any] | None]] = []
    for a in f01:
        k = _key(a)
        occ = used[k]
        used[k] += 1
        cands = buckets.get(k) or []
        out.append((a, cands[occ] if occ < len(cands) else None))
    return out


def coverage_report(
    html01: str,
    html02: str,
    *,
    review_required: int = 0,
    touches: list[dict[str, Any]] | None = None,
    multi_re_pulled: bool = False,
    multi_conflict_preserved: int | None = None,
    cache_fallback_fields: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    f01 = extract_fields(html01)
    f02 = extract_fields(html02)
    if len(f01) != 274:
        raise RuntimeError(f"Report 01 inventory {len(f01)} != 274")
    cache_fb = set(resolve_cache_fallback_field_ids(cache_fallback_fields))
    rows: list[dict[str, Any]] = []
    n_dyn = n_ref = n_fail = n_unk = n_static = n_multi = n_multi_ref = 0
    n_cache_fallback = 0
    touch_needles = []
    for t in touches or []:
        touch_needles.append(
            (
                str(t.get("asset") or "").lower(),
                str(t.get("section") or ""),
                str(t.get("needle") or ""),
            )
        )

    def touched(a: dict[str, Any]) -> bool:
        asset = (a.get("asset") or "").lower()
        section = a.get("visible_section") or ""
        text = a.get("report_01_text") or ""
        for ta, ts, needle in touch_needles:
            if not needle:
                continue
            if ta and ta != asset:
                continue
            if ts and ts != section:
                continue
            if needle in text or text in needle:
                return True
            np, tp = _plain(needle), _plain(text)
            if np and tp and (np in tp or tp in np):
                return True
        return False

    for i, (a, b) in enumerate(_pair(f01, f02)):
        cls, reason, *_ = classify_one(a.get("report_01_text") or "", a.get("asset") or "")
        new = (b or {}).get("report_01_text")
        old = a.get("report_01_text")
        changed = new is not None and new != old
        same_live = (not changed) and touched(a)
        field_id = canonical_id(a["asset"], a["visible_section"], a.get("report_01_text") or "")
        cache_fb_hit = field_id in cache_fb or any(k in field_id for k in cache_fb if k)
        if cls == DYNAMIC:
            n_dyn += 1
            if cache_fb_hit and (changed or same_live):
                n_cache_fallback += 1
                status = "CACHE_FALLBACK"
            elif changed or same_live:
                n_ref += 1
                status = "REFRESHED" if changed else "REFRESHED_SAME_PRINT"
            else:
                n_fail += 1
                status = "SOURCE_FAILURE"
        elif cls == MULTI:
            n_multi += 1
            if multi_re_pulled or changed or same_live:
                n_multi_ref += 1
                status = "REFRESHED" if changed else "REFRESHED_SAME_PRINT"
            else:
                status = "SOURCE_FAILURE"
        elif cls == UNKNOWN:
            n_unk += 1
            status = "UNKNOWN"
        else:
            n_static += 1
            status = "STATIC"
        rows.append(
            {
                "field_id": field_id,
                "asset": a["asset"],
                "section": a["visible_section"],
                "classification": cls,
                "status": status,
                "report_01": old,
                "report_02": new,
            }
        )
    if n_ref + n_fail + n_cache_fallback != n_dyn:
        raise RuntimeError("DYNAMIC split does not sum")
    by_sec: dict[str, dict[str, int]] = defaultdict(lambda: {"refreshed": 0, "source_failure": 0})
    for r in rows:
        if r["classification"] != DYNAMIC:
            continue
        if r["status"].startswith("REFRESHED"):
            by_sec[r["section"]]["refreshed"] += 1
        elif r["status"] == "CACHE_FALLBACK":
            by_sec[r["section"]]["cache_fallback"] = by_sec[r["section"]].get("cache_fallback", 0) + 1
        else:
            by_sec[r["section"]]["source_failure"] += 1
    return {
        "schema": "autojob01-coverage-v3-canonical-ids",
        "dynamic_total": n_dyn,
        "refreshed_successfully": n_ref,
        "cache_fallback_count": n_cache_fallback,
        "genuine_unknown": n_unk,
        "source_failure": n_fail,
        "review_required": review_required,
        "dynamic_sum": n_ref + n_fail + n_cache_fallback,
        "dynamic_reconcile_ok": n_ref + n_fail + n_cache_fallback == n_dyn,
        "static": n_static,
        "multi_total": n_multi,
        "multi_freshly_re_pulled": n_multi_ref,
        "multi_conflict_preserved": multi_conflict_preserved if multi_conflict_preserved is not None else n_multi,
        "multi_source": n_multi,
        "multi_refreshed": n_multi_ref,
        "report_01_field_count": len(f01),
        "report_02_field_count": len(f02),
        "by_section": dict(by_sec),
        "fields": rows,
    }
