#!/usr/bin/env python3
"""Job5 reconstruction: Job2 replay → historical bridge merge → Job3 snapshot/render → Job4."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shadow/job5"))

from collectors.derive import derive
from collectors.extract import ExtractError
from build_historical_evidence_facts import build_facts, refuse_html_path, refuse_later_review05


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode_value(v: Any) -> Any:
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v
    d = Decimal(str(v))
    if d == d.to_integral_value():
        return int(d)
    return format(d, "f")


def run_job2_replay(replay_dir: Path) -> Path:
    cmd = [sys.executable, str(ROOT / "collectors/run_collectors.py"), "--replay", str(replay_dir)]
    subprocess.check_call(cmd, cwd=str(ROOT))
    produced = ROOT / "runtime-NOT-FOR-GH/job2/replay/collector-run.json"
    if not produced.is_file():
        raise SystemExit("job2 replay did not write collector-run.json")
    return produced


def apply_archive_gaps(
    run: dict[str, Any],
    gap_manifest: dict[str, Any],
    plan: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Force UNKNOWN for documented historical archive gaps — never preserve Review04 numbers."""
    by_id = {f["metric_id"]: i for i, f in enumerate(run["facts"])}
    applied: list[dict[str, Any]] = []
    gap_ids = {e["metric_id"] for e in gap_manifest.get("metrics", [])}
    for mid in sorted(gap_ids):
        if mid not in by_id:
            raise RuntimeError(f"ARCHIVE_GAP_METRIC_NOT_IN_RUN:{mid}")
        idx = by_id[mid]
        prev = run["facts"][idx]
        run["facts"][idx] = {
            "metric_id": mid,
            "status": "UNKNOWN",
            "raw_source_value": None,
            "normalized_value": None,
            "unit": prev.get("unit"),
            "source_key": prev.get("source_key"),
            "request_key": prev.get("request_key"),
            "source_field": prev.get("source_field"),
            "source_as_of": None,
            "fetched_at": None,
            "raw_capture_sha256": None,
            "freshness": "UNKNOWN",
            "error": "HISTORICAL_SOURCE_ARCHIVE_GAP",
        }
        applied.append(
            {
                "metric_id": mid,
                "previous_status": prev.get("status"),
                "previous_normalized_value": prev.get("normalized_value"),
                "gap_reason": next(
                    (g["reason_unavailable"] for g in gap_manifest["metrics"] if g["metric_id"] == mid),
                    "HISTORICAL_SOURCE_ARCHIVE_GAP",
                ),
            }
        )
    facts_by = {f["metric_id"]: f for f in run["facts"]}
    for e in plan["entries"]:
        if e["disposition"] != "DERIVE":
            continue
        mid = e["metric_id"]
        der = e["derivation"]
        inputs = der["inputs"]
        if not any(inp in gap_ids for inp in inputs):
            continue
        idx = by_id[mid]
        run["facts"][idx] = {
            "metric_id": mid,
            "status": "UNKNOWN",
            "raw_source_value": None,
            "normalized_value": None,
            "unit": e.get("unit"),
            "source_key": None,
            "request_key": None,
            "source_field": der["op"],
            "source_as_of": None,
            "fetched_at": None,
            "raw_capture_sha256": None,
            "freshness": "UNKNOWN",
            "error": "HISTORICAL_SOURCE_ARCHIVE_GAP",
            "derivation_inputs": inputs,
        }
        facts_by[mid] = run["facts"][idx]
    return run, applied


def merge_bridge(run: dict[str, Any], bridged: dict[str, Any], plan: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    by_id = {f["metric_id"]: i for i, f in enumerate(run["facts"])}
    replacements = []
    html_derived = 0
    synthetic = 0
    live = 0
    for fact, side in zip(bridged["facts"], bridged["sidecars"]):
        mid = fact["metric_id"]
        orig = run["facts"][by_id[mid]]
        if orig.get("status") not in {"SOURCE_UNAVAILABLE", "AUTH_MISSING", "VALUE_MISSING"}:
            # still allowed if raw historical capture absent — Job2 synthetic/live must not remain
            if orig.get("status") == "OK" and orig.get("fetched_at", "").startswith("2026-08-26"):
                live += 1
                continue
        if "SYNTHETIC" in json.dumps(orig):
            synthetic += 1
        run["facts"][by_id[mid]] = deepcopy(fact)
        replacements.append(
            {
                "original_replay_status": orig.get("status"),
                "replacement_metric_id": mid,
                "archived_evidence_path": side["archive_path"],
                "archived_evidence_field": side["archive_field"],
                "archived_value": fact["normalized_value"],
                "replacement_reason": "HISTORICAL_RAW_CAPTURE_NOT_ARCHIVED",
            }
        )
    # re-derive from merged COLLECT facts
    facts_by = {f["metric_id"]: f for f in run["facts"]}
    for e in plan["entries"]:
        if e["disposition"] != "DERIVE":
            continue
        mid = e["metric_id"]
        der = e["derivation"]
        inputs = der["inputs"]
        vals = []
        blocked = False
        for inp in inputs:
            src = facts_by.get(inp)
            if not src or src.get("status") != "OK":
                blocked = True
                break
            vals.append(Decimal(str(src["normalized_value"])))
        idx = by_id[mid]
        if blocked:
            run["facts"][idx]["status"] = "DERIVATION_BLOCKED"
            run["facts"][idx]["normalized_value"] = None
            run["facts"][idx]["error"] = f"inputs not OK: {inputs}"
            continue
        try:
            out = derive(der["op"], vals, der["calculation_version"])
            run["facts"][idx] = {
                "metric_id": mid,
                "status": "OK",
                "raw_source_value": None,
                "normalized_value": encode_value(out),
                "unit": e.get("unit"),
                "source_key": None,
                "request_key": None,
                "source_field": der["op"],
                "source_as_of": "UNKNOWN",
                "fetched_at": None,
                "raw_capture_sha256": None,
                "freshness": "UNKNOWN",
                "calculation_version": der["calculation_version"],
                "derivation_inputs": inputs,
                "error": None,
            }
            facts_by[mid] = run["facts"][idx]
        except ExtractError as exc:
            run["facts"][idx]["status"] = exc.status
            run["facts"][idx]["normalized_value"] = None
            run["facts"][idx]["error"] = exc.message
    stats = {
        "html_derived_replacements": html_derived,
        "synthetic_replacements": synthetic,
        "live_fetched_replacements": live,
        "replacements": replacements,
    }
    if live:
        raise RuntimeError("LIVE_FETCHED_REPLACEMENT_ATTEMPTED")
    return run, stats


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--archive-root", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--archive-gap-manifest", default=str(ROOT / "shadow/job5/archive_gap_manifest.json"))
    p.add_argument("--runtime", default=str(ROOT / "runtime-NOT-FOR-GH/job5"))
    p.add_argument("--skip-render", action="store_true")
    args = p.parse_args()
    runtime = Path(args.runtime)
    runtime.mkdir(parents=True, exist_ok=True)
    refuse_html_path(Path(args.archive_root))
    refuse_html_path(Path(args.manifest))
    refuse_later_review05(Path(args.archive_root), None)

    replay_dir = runtime / "review04-replay"
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "shadow/job5/build_review04_replay.py"),
            "--out",
            str(replay_dir),
        ]
    )
    produced = run_job2_replay(replay_dir)
    dest_run = runtime / "review04-collector-run.json"
    dest_run.write_bytes(produced.read_bytes())

    run = json.loads(dest_run.read_text())
    plan = json.loads((ROOT / "collectors/collector-plan.json").read_text())
    man = json.loads(Path(args.manifest).read_text())
    bridged = build_facts(manifest=man, archive_root=Path(args.archive_root), plan={e["metric_id"]: e for e in plan["entries"]})
    (runtime / "historical-bridge-facts.json").write_text(json.dumps(bridged, indent=2) + "\n")
    merged, stats = merge_bridge(run, bridged, plan)
    gap_man = json.loads(Path(args.archive_gap_manifest).read_text())
    refuse_html_path(Path(args.archive_gap_manifest))
    merged, gap_applied = apply_archive_gaps(merged, gap_man, plan)
    dest_run.write_text(json.dumps(merged, indent=2) + "\n")
    (runtime / "bridge-replacements.json").write_text(json.dumps(stats, indent=2) + "\n")
    (runtime / "archive-gap-applied.json").write_text(json.dumps({"applied": gap_applied}, indent=2) + "\n")

    if args.skip_render:
        print("skip_render")
        return 0

    snap_path = runtime / "review04-render-snapshot.json"
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "renderer/build_snapshot.py"),
            "--collector-run",
            str(dest_run),
            "--out",
            str(snap_path),
        ]
    )
    html_out = runtime / "review04-shadow.html"
    manifest_out = runtime / "review04-render-manifest.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "renderer/render_report.py"),
            "--snapshot",
            str(snap_path),
            "--source",
            str(ROOT / "index-v4.html"),
            "--out",
            str(html_out),
            "--manifest-out",
            str(manifest_out),
        ],
        cwd=str(ROOT),
    )
    if proc.returncode not in (0, 2):
        raise subprocess.CalledProcessError(proc.returncode, proc.args)
    print(f"collector_run {dest_run}")
    print(f"snapshot {snap_path}")
    print(f"shadow {html_out}")
    print(f"replacements {len(stats['replacements'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
