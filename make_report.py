#!/usr/bin/env python3
"""One command for the next report.

Writes a candidate file only. Does not replace the live page.
Does not push. Does not walk wallets unless --walk is passed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.run_collectors import run as run_collectors
from integrity.build_report_contract import build_contract
from integrity.stale_gate import stale_problems
from renderer.build_binding_manifest import build_manifest
from renderer.build_snapshot import build_snapshot
from renderer.manual_zones import wrap_manual_zones
from renderer.render_report import render_report
from renderer.report_config import load_report

RUNTIME = ROOT / "runtime-NOT-FOR-GH"
PIPELINE = ("collectors", "renderer", "integrity", "lib", "config", "make_report.py")
REPLAY_26 = ROOT / "runtime-NOT-FOR-GH/job2/20260926T103538Z_3e1c5167"


def _git_dirty() -> list[str]:
    out = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    dirty = []
    for line in out.splitlines():
        path = line[3:].strip()
        if path in {"index-v4.html", "baselines/report-05.html"} or path.startswith("tests/job4/fixtures/"):
            continue
        if any(path == name or path.startswith(name + "/") for name in PIPELINE):
            dirty.append(path)
    return dirty


def preflight() -> int:
    cfg = load_report()
    dirty = _git_dirty()
    if dirty:
        print("preflight failed. Pipeline files are still edited:", file=sys.stderr)
        for path in dirty:
            print(f"  {path}", file=sys.stderr)
        return 2
    print(f"preflight ok. Next report {cfg['report_number']} on {cfg['report_date']}.")
    return 0


def _previous_page() -> Path:
    dest = RUNTIME / "previous-report.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(subprocess.check_output(["git", "show", "HEAD:index-v4.html"], cwd=ROOT))
    return dest


def _run_steps(replay: Path | None, live: bool) -> int:
    code = preflight()
    if code:
        return code
    cfg = load_report()
    number = cfg["report_number"]
    if live:
        code, collector = run_collectors("live", None)
    else:
        if replay is None or not replay.exists():
            print(f"missing replay captures: {replay}", file=sys.stderr)
            return 2
        code, collector = run_collectors("replay", replay)
    if code not in {0, 2}:
        print(f"collector exit {code}", file=sys.stderr)
        return code or 2
    run_dir = RUNTIME / ("replay" if replay else collector.get("run_id", "live"))
    run_path = run_dir / "collector-run.json"
    if not run_path.exists():
        print(f"no collector run at {run_path}", file=sys.stderr)
        return 2
    labels = json.loads((ROOT / "renderer/source-labels.json").read_text())
    run_doc = json.loads(run_path.read_text())
    failed = list(run_doc.get("required_failed_ids") or [])
    if failed:
        print("metrics with no number this run:")
        for mid in failed:
            print(f"  {mid}")
    snap = build_snapshot(run_doc, labels, allow_partial=set(failed))
    snap_path = RUNTIME / "job3" / "render-snapshot.json"
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(snap, indent=2) + "\n")

    source = _previous_page()
    built = build_manifest(source)
    blockers = built.pop("blockers")
    critical = [row for row in blockers if row.get("critical")]
    (RUNTIME / "job3" / "blockers.json").write_text(json.dumps(blockers, indent=2) + "\n")
    if critical:
        print(f"critical misses {len(critical)}; wrote nothing", file=sys.stderr)
        return 2
    ok_ids = {
        mid
        for mid, row in (snap.get("metrics") or {}).items()
        if row.get("status") == "OK"
    }
    bindings = [row for row in built["bindings"] if row.get("metric_id") in ok_ids]
    print(f"bindings used {len(bindings)} of {len(built['bindings'])}")
    writers = json.loads((ROOT / "renderer/writer-quarantine.json").read_text())
    rendered, _manifest, render_code = render_report(
        source_html=source.read_text(encoding="utf-8"),
        bindings=bindings,
        snapshot=snap,
        writer_quarantine=writers,
        publishable=False,
    )
    if render_code != 0:
        print(f"render exit {render_code}; wrote nothing", file=sys.stderr)
        return render_code
    rendered = wrap_manual_zones(rendered, number)
    candidate = RUNTIME / f"candidate-{number}.html"
    candidate.write_text(rendered, encoding="utf-8")
    print(f"wrote {candidate}")

    manifest_path = RUNTIME / "job3" / "binding-manifest.json"
    manifest_path.write_text(json.dumps(built, indent=2) + "\n")
    contract = build_contract(
        registry_path=ROOT / "metrics/metric-registry.json",
        plan_path=ROOT / "collectors/collector-plan.json",
        bindings_path=manifest_path,
        source_html_path=candidate,
    )
    (RUNTIME / "job3" / "report-contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    print(f"contract checks {contract['expected_check_count']}")
    problems = stale_problems(rendered, snapshot=snap, bindings=bindings, report_number=number)
    if problems:
        print("stale gate FAIL")
        for item in problems[:20]:
            print(f"  {item}")
        print("candidate kept for review. Live page was not changed.")
        return 1
    print("stale gate PASS")
    print("Live page was not changed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue the next crypto report")
    parser.add_argument("--replay", type=Path, help="Raw capture folder. No network.")
    parser.add_argument("--live", action="store_true", help="Pull new numbers. Uses the network.")
    parser.add_argument("--walk", action="store_true", help="Walk held wallets. Off unless you pass this.")
    parser.add_argument("--promote", action="store_true", help="Refused. The live page is not replaced here.")
    args = parser.parse_args()
    if args.promote:
        print("promote is off. The live page stays index-v4.html.", file=sys.stderr)
        return 2
    if args.walk:
        print("wallet walk is off in this command until you ask for it on its own.", file=sys.stderr)
        return 2
    if args.live and args.replay:
        print("pass --live or --replay, not both", file=sys.stderr)
        return 2
    if not args.live and args.replay is None:
        print("Run one of:")
        print(f"  python3 make_report.py --replay {REPLAY_26}")
        print("  python3 make_report.py --live")
        return 2
    return _run_steps(args.replay, args.live)


if __name__ == "__main__":
    raise SystemExit(main())
