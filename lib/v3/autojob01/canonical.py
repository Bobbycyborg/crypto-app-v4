"""Canonical AUTOJOB01 field IDs. Manifest owns the ID. Never re-number from walk order."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from lib.paths import REPORTS
from lib.v3.autojob01.paths import autojob01_paths

_HISTORICAL_MANIFEST = REPORTS / "2026-08-15" / "autojob01" / "AUTOJOB01-MANIFEST.json"


def _manifest_json():
    target = autojob01_paths()["MANIFEST_JSON"]
    if target.is_file():
        return target
    if _HISTORICAL_MANIFEST.is_file():
        return _HISTORICAL_MANIFEST
    return target


def _key(asset: str, section: str, text: str) -> tuple[str, str, str]:
    return (asset or "", section or "", text or "")


@lru_cache(maxsize=1)
def load_canonical_fields() -> list[dict[str, Any]]:
    data = json.loads(_manifest_json().read_text(encoding="utf-8"))
    fields = data.get("fields") or []
    if len(fields) != 274:
        raise RuntimeError(f"canonical manifest has {len(fields)} fields, need 274")
    ids = [f.get("field_id") for f in fields]
    if len(set(ids)) != 274:
        raise RuntimeError("canonical field_id not unique")
    return fields


def id_index() -> dict[tuple[str, str, str], str]:
    out: dict[tuple[str, str, str], str] = {}
    for f in load_canonical_fields():
        k = _key(f.get("asset") or "", f.get("visible_section") or "", f.get("report_01_text") or "")
        if k in out:
            raise RuntimeError(f"duplicate canonical key {k}")
        out[k] = f["field_id"]
    return out


def canonical_id(asset: str, section: str, text: str) -> str:
    idx = id_index()
    k = _key(asset, section, text)
    fid = idx.get(k)
    if not fid:
        raise RuntimeError(f"no canonical field_id for {asset!r} {section!r} {text[:80]!r}")
    return fid


def assert_ids_match(rows: list[dict[str, Any]], *, text_key: str = "report_01_text") -> int:
    """0 mismatches. Each row must carry the manifest field_id for its Report 01 text."""
    n = 0
    for r in rows:
        asset = r.get("asset") or ""
        section = r.get("visible_section") or r.get("section") or ""
        text = r.get(text_key) or r.get("report_01") or ""
        want = canonical_id(asset, section, text)
        got = r.get("field_id")
        if got != want:
            n += 1
    return n
