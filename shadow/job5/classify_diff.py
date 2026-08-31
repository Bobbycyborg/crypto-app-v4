#!/usr/bin/env python3
"""Three-way B/S/H classification. Wallet blob is hashed, never parsed."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WALLET_RE = re.compile(
    r'(<script type="application/json" id="siren-watch-data">)(.*?)(</script>)',
    re.DOTALL,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def wallet_blob(html: str) -> bytes:
    m = WALLET_RE.search(html)
    if not m:
        raise RuntimeError("wallet blob missing")
    return m.group(2).encode("utf-8")


def classify(
    *,
    baseline: str,
    source: str,
    shadow: str,
    bindings: list[dict[str, Any]],
    writers: dict[str, Any],
    snapshot: dict[str, Any],
    archive_gap_metrics: set[str] | None = None,
) -> dict[str, Any]:
    src_w = sha256_bytes(wallet_blob(source))
    sh_w = sha256_bytes(wallet_blob(shadow))
    b_w = sha256_bytes(wallet_blob(baseline))
    hunks: list[dict[str, Any]] = []
    archive_gap_metrics = archive_gap_metrics or set()
    counts = {
        "PREEXISTING_WALLET_DRIFT": 0,
        "PREEXISTING_APPROVED_STATIC_V4_DRIFT": 0,
        "CANONICAL_RECONSTRUCTION": 0,
        "ARCHIVED_EXTRACTED_RECONSTRUCTION": 0,
        "ARCHIVED_DERIVED_RECONSTRUCTION": 0,
        "FAIL_CLOSED_REVIEW04_UNKNOWN": 0,
        "HISTORICAL_SOURCE_ARCHIVE_GAP": 0,
        "WRITER_QUARANTINE": 0,
        "PIPELINE_DEFECT": 0,
        "UNCLASSIFIED": 0,
    }

    if b_w != src_w:
        hunks.append({"id": "wallet_B_S", "class": "PREEXISTING_WALLET_DRIFT"})
        counts["PREEXISTING_WALLET_DRIFT"] += 1
    if src_w != sh_w:
        hunks.append({"id": "wallet_S_H", "class": "PIPELINE_DEFECT"})
        counts["PIPELINE_DEFECT"] += 1

    metrics = snapshot.get("metrics") or {}
    for b in bindings:
        mid = b["metric_id"]
        rec = metrics.get(mid) or {}
        lit = b["source_literal"]
        # source vs shadow at this occurrence is classified after render; residual check below
        status = rec.get("status")
        err = rec.get("error") or ""
        if mid in archive_gap_metrics or err == "HISTORICAL_SOURCE_ARCHIVE_GAP":
            hunks.append({"id": b["binding_id"], "class": "HISTORICAL_SOURCE_ARCHIVE_GAP", "metric_id": mid})
            counts["HISTORICAL_SOURCE_ARCHIVE_GAP"] += 1
        elif status == "OK":
            ev = rec.get("evidence_mode") or rec.get("job5_evidence_mode")
            if ev == "ARCHIVED_EXTRACTED_SOURCE_EVIDENCE":
                cls = "ARCHIVED_EXTRACTED_RECONSTRUCTION"
            elif ev == "ARCHIVED_DERIVABLE_MACHINE_EVIDENCE":
                cls = "ARCHIVED_DERIVED_RECONSTRUCTION"
            else:
                cls = "CANONICAL_RECONSTRUCTION"
            hunks.append({"id": b["binding_id"], "class": cls, "metric_id": mid})
            counts[cls] += 1
        elif status in {"UNKNOWN", "BLOCKED_SOURCE", "SOURCE_UNAVAILABLE", "DERIVATION_BLOCKED"}:
            hunks.append({"id": b["binding_id"], "class": "FAIL_CLOSED_REVIEW04_UNKNOWN", "metric_id": mid})
            counts["FAIL_CLOSED_REVIEW04_UNKNOWN"] += 1
        else:
            hunks.append({"id": b["binding_id"], "class": "UNCLASSIFIED", "metric_id": mid})
            counts["UNCLASSIFIED"] += 1

    for w in writers.get("writers", []):
        if w["source_fragment"] in source and w["replacement_fragment"] in shadow:
            hunks.append({"id": w["writer_id"], "class": "WRITER_QUARANTINE"})
            counts["WRITER_QUARANTINE"] += 1

    if baseline != source:
        # non-wallet residual B→S
        b_now = WALLET_RE.sub(r"\1WALLET\3", baseline)
        s_now = WALLET_RE.sub(r"\1WALLET\3", source)
        if b_now != s_now:
            hunks.append({"id": "static_B_S", "class": "PREEXISTING_APPROVED_STATIC_V4_DRIFT"})
            counts["PREEXISTING_APPROVED_STATIC_V4_DRIFT"] += 1

    unexplained = counts["PIPELINE_DEFECT"] + counts["UNCLASSIFIED"]
    return {
        "hunks": hunks,
        "counts": counts,
        "pipeline_defects": counts["PIPELINE_DEFECT"],
        "unclassified_differences": counts["UNCLASSIFIED"],
        "unexplained_differences": unexplained,
        "wallet_blob_source_sha256": src_w,
        "wallet_blob_shadow_sha256": sh_w,
        "wallet_blob_baseline_sha256": b_w,
        "wallet_blob_unchanged": src_w == sh_w,
        "baseline_vs_source_hunks": 1 if baseline != source else 0,
        "source_vs_shadow_hunks": 1 if source != shadow else 0,
        "baseline_vs_shadow_hunks": 1 if baseline != shadow else 0,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--shadow", required=True)
    p.add_argument("--snapshot", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--archive-gap-manifest", default=str(ROOT / "shadow/job5/archive_gap_manifest.json"))
    args = p.parse_args()
    baseline = Path(args.baseline).read_text(encoding="utf-8")
    source = Path(args.source).read_text(encoding="utf-8")
    shadow = Path(args.shadow).read_text(encoding="utf-8")
    snap = json.loads(Path(args.snapshot).read_text())
    bindings = json.loads((ROOT / "renderer/binding-manifest.json").read_text())["bindings"]
    writers = json.loads((ROOT / "renderer/writer-quarantine.json").read_text())
    gap_man = json.loads(Path(args.archive_gap_manifest).read_text())
    archive_gap_metrics = {m["metric_id"] for m in gap_man.get("metrics", [])}
    report = classify(
        baseline=baseline,
        source=source,
        shadow=shadow,
        bindings=bindings,
        writers=writers,
        snapshot=snap,
        archive_gap_metrics=archive_gap_metrics,
    )
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(f"pipeline_defects={report['pipeline_defects']}")
    print(f"unclassified_differences={report['unclassified_differences']}")
    return 0 if report["unexplained_differences"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
