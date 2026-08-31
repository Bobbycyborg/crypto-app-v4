#!/usr/bin/env python3
"""Job5-only: archived extracted Review04 facts. No collectors/renderer/integrity edits."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_NAME_FRAGMENTS = (
    "index-v4.html",
    "v4-start-from-final-v3.html",
    "report-04.html",
    "source_literal",
)
REVIEW04_CUTOFF = datetime(2026, 8, 25, 23, 59, 59, tzinfo=timezone.utc)
LATER_RUN_MARKERS = ("20260826", "20260827", "2026-08-26", "2026-08-27")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_pointer(obj: Any, pointer: str) -> Any:
    if not pointer.startswith("/"):
        raise ValueError(f"archive_field must be a JSON pointer: {pointer}")
    cur = obj
    if pointer == "/":
        return cur
    for part in pointer[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            raise KeyError(pointer)
    return cur


def parse_iso(ts: str) -> datetime:
    raw = ts.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def calendar_date_utc(ts: str) -> str:
    return parse_iso(ts).strftime("%Y-%m-%d")


def as_of_display(iso_date: str) -> str:
    dt = datetime.strptime(iso_date[:10], "%Y-%m-%d")
    return dt.strftime("%-d %b %Y") if hasattr(dt, "strftime") else dt.strftime("%d %b %Y").lstrip("0")


def refuse_html_path(path: Path) -> None:
    text = str(path).replace("\\", "/")
    lower = text.lower()
    if lower.endswith(".html") or lower.endswith(".htm"):
        raise RuntimeError(f"HTML_FORBIDDEN_AS_DATA:{path}")
    for frag in FORBIDDEN_NAME_FRAGMENTS:
        if frag.lower() in lower:
            raise RuntimeError(f"HTML_FORBIDDEN_AS_DATA:{path}")


def refuse_later_review05(path: Path, fetched_at: str | None) -> None:
    blob = str(path)
    if fetched_at:
        blob += " " + fetched_at
    for mark in LATER_RUN_MARKERS:
        if mark in blob:
            raise RuntimeError(f"LATER_DATA_REJECTED:{path}")
    if fetched_at:
        try:
            if parse_iso(fetched_at) > REVIEW04_CUTOFF:
                raise RuntimeError(f"LATER_DATA_REJECTED:{path}:{fetched_at}")
        except ValueError:
            pass


def load_archive_json(path: Path) -> Any:
    refuse_html_path(path)
    if path.suffix.lower() not in {".json"}:
        raise RuntimeError(f"UNSUPPORTED_ARCHIVE:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def extract_value(doc: Any, entry: dict[str, Any]) -> Any:
    field = entry["archive_field"]
    raw = json_pointer(doc, field)
    ext = entry.get("extract")
    if not ext:
        return raw
    if ext["type"] == "regex":
        if not isinstance(raw, str):
            raise RuntimeError(f"REGEX_NEEDS_STRING:{entry['metric_id']}")
        m = re.search(ext["pattern"], raw)
        if not m:
            raise RuntimeError(f"ARCHIVE_FIELD_MISSING:{entry['metric_id']}:{field}")
        return float(m.group(1)) if "." in m.group(1) else int(m.group(1))
    raise RuntimeError(f"UNKNOWN_EXTRACT:{ext['type']}")


def build_facts(*, manifest: dict[str, Any], archive_root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    refuse_html_path(archive_root)
    facts: list[dict[str, Any]] = []
    sidecars: list[dict[str, Any]] = []
    for entry in manifest["metrics"]:
        mid = entry["metric_id"]
        rel = entry["archive_path"]
        path = (archive_root / rel).resolve()
        refuse_html_path(path)
        if not path.is_file():
            raise RuntimeError(f"ARCHIVE_MISSING:{mid}:{path}")
        doc = load_archive_json(path)
        try:
            value = extract_value(doc, entry)
        except KeyError as exc:
            raise RuntimeError(f"ARCHIVE_FIELD_MISSING:{mid}:{entry['archive_field']}") from exc
        if value is None:
            raise RuntimeError(f"ARCHIVE_FIELD_MISSING:{mid}:{entry['archive_field']}")
        fetched_at = None
        if entry.get("fetched_at_field"):
            try:
                fetched_at = str(json_pointer(doc, entry["fetched_at_field"]))
            except KeyError:
                fetched_at = None
        refuse_later_review05(path, fetched_at)
        source_as_of = None
        source_as_of_basis = None
        if entry.get("source_as_of_regex"):
            blob = str(json_pointer(doc, entry["archive_field"]))
            m = re.search(entry["source_as_of_regex"], blob)
            if m:
                source_as_of = m.group(1)
                source_as_of_basis = "EXPLICIT_ARCHIVE_SOURCE_AS_OF"
        if entry.get("source_as_of_field"):
            try:
                source_as_of = str(json_pointer(doc, entry["source_as_of_field"]))
                source_as_of_basis = "EXPLICIT_ARCHIVE_SOURCE_AS_OF"
            except KeyError:
                source_as_of = source_as_of
        if not source_as_of:
            if not fetched_at:
                raise RuntimeError(f"NO_AS_OF_PROVENANCE:{mid}")
            source_as_of = calendar_date_utc(fetched_at)
            source_as_of_basis = "HISTORICAL_FETCH_OBSERVATION"
        pe = plan[mid]
        archive_sha = sha256_file(path)
        fact = {
            "metric_id": mid,
            "status": entry.get("status", "OK"),
            "raw_source_value": str(value),
            "normalized_value": value if isinstance(value, (int, float)) else str(value),
            "unit": pe.get("unit"),
            "source_key": pe.get("source_key"),
            "request_key": pe.get("request_key"),
            "source_field": entry["archive_field"],
            "source_as_of": source_as_of,
            "fetched_at": fetched_at or "UNKNOWN",
            "raw_capture_sha256": archive_sha,
            "freshness": entry.get("freshness", "UNKNOWN"),
            "calculation_version": None,
            "derivation_inputs": None,
            "error": None,
        }
        sidecar = {
            "metric_id": mid,
            "evidence_mode": "ARCHIVED_EXTRACTED_SOURCE_EVIDENCE",
            "archive_path": rel,
            "archive_field": entry["archive_field"],
            "archive_sha256": archive_sha,
            "original_source": entry.get("original_source") or pe.get("source_key"),
            "raw_http_capture_available": False,
            "source_as_of_basis": source_as_of_basis,
        }
        facts.append(fact)
        sidecars.append(sidecar)
    return {"facts": facts, "sidecars": sidecars}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--archive-root", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    man_path = Path(args.manifest)
    archive_root = Path(args.archive_root)
    refuse_html_path(man_path)
    refuse_html_path(archive_root)
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    plan = {e["metric_id"]: e for e in json.loads((ROOT / "collectors/collector-plan.json").read_text())["entries"]}
    out = build_facts(manifest=manifest, archive_root=archive_root, plan=plan)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"bridged_facts={len(out['facts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
