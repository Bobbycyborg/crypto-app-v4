#!/usr/bin/env python3
"""Flag current/weekly report values leaked into production integrity files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

STRUCTURAL_ALLOWLIST = frozenset(
    {
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "7",
        "10",
        "12",
        "100",
        "418",
        "1000",
        "1000000",
        "1000000000",
        "1000000000000",
    }
)

_HASH_RE = re.compile(r"\b[a-f0-9]{64}\b", re.I)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_distinctive(token: str) -> bool:
    t = token.strip()
    if not t or t in STRUCTURAL_ALLOWLIST:
        return False
    if any(ch in t for ch in "$,%/"):
        return True
    if t[-1:] in "kKmMbBtT" and any(c.isdigit() for c in t):
        return True
    if "." in t:
        return True
    if re.fullmatch(r"\d+", t) and len(t) >= 4:
        return True
    return False


def corpus_values(
    *,
    registry: dict[str, Any],
    manifest: dict[str, Any],
    snapshot: dict[str, Any] | None,
) -> set[str]:
    out: set[str] = set()

    def _add(v: Any) -> None:
        if v is None or isinstance(v, bool):
            return
        if isinstance(v, (int, float)):
            s = str(v)
            if s.endswith(".0"):
                out.add(str(int(v)))
            out.add(s)
            return
        if isinstance(v, str):
            t = v.strip()
            if t and not _HASH_RE.fullmatch(t):
                out.add(t)
                compact = t.replace(",", "").replace("$", "")
                if compact != t:
                    out.add(compact)

    for m in registry.get("metrics", []):
        if m.get("metric_type") != "CURRENT_DYNAMIC":
            continue
        for key in ("value", "raw_value", "normalized_value", "display_value"):
            _add(m.get(key))
    for b in manifest.get("bindings", []):
        _add(b.get("source_literal"))
        _add(b.get("binding_raw"))
    if snapshot:
        for rec in (snapshot.get("metrics") or {}).values():
            _add(rec.get("normalized_value"))
            _add(rec.get("raw_value"))
    return {x for x in out if x and x not in STRUCTURAL_ALLOWLIST and _is_distinctive(x)}


def scan_integrity_text(text: str, corpus: set[str]) -> list[str]:
    stripped = _HASH_RE.sub("", text)
    hits: list[str] = []
    for token in sorted(corpus, key=len, reverse=True):
        if not _is_distinctive(token):
            continue
        pat = r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])"
        if re.search(pat, stripped):
            hits.append(token)
    return sorted(set(hits))


def audit_production(
    *,
    integrity_dir: Path,
    registry: dict[str, Any],
    manifest: dict[str, Any],
    snapshot: dict[str, Any] | None,
) -> list[tuple[str, str]]:
    corpus = corpus_values(registry=registry, manifest=manifest, snapshot=snapshot)
    flagged: list[tuple[str, str]] = []
    for path in sorted(integrity_dir.rglob("*")):
        if path.suffix not in {".py", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for hit in scan_integrity_text(text, corpus):
            flagged.append((str(path.relative_to(integrity_dir.parent)), hit))
    return flagged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=ROOT / "metrics/metric-registry.json")
    parser.add_argument("--bindings", type=Path, default=ROOT / "renderer/binding-manifest.json")
    parser.add_argument("--snapshot", type=Path, default=None)
    parser.add_argument("--integrity", type=Path, default=ROOT / "integrity")
    parser.add_argument("--inject", default=None, help="inject this token into a contract copy")
    args = parser.parse_args()
    registry = _load_json(args.registry)
    manifest = _load_json(args.bindings)
    snapshot = _load_json(args.snapshot) if args.snapshot and args.snapshot.is_file() else None
    if args.inject:
        contract_path = args.integrity / "report-contract.json"
        blob = contract_path.read_text(encoding="utf-8")
        tmp = args.integrity / "_audit_inject.json"
        tmp.write_text(blob.rstrip()[:-1] + f', "probe_current_value": "{args.inject}"}}\n')
        try:
            hits = scan_integrity_text(tmp.read_text(encoding="utf-8"), {args.inject})
        finally:
            tmp.unlink(missing_ok=True)
        print(json.dumps({"inject_hits": hits}))
        return 0 if hits else 2
    flagged = audit_production(
        integrity_dir=args.integrity,
        registry=registry,
        manifest=manifest,
        snapshot=snapshot,
    )
    print(json.dumps({"hardcoded_current_values": len(flagged), "hits": flagged[:50]}))
    return 0 if not flagged else 2


if __name__ == "__main__":
    raise SystemExit(main())
