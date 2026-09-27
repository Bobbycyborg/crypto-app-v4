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

from collectors.run_collectors import RUNTIME as JOB2
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
HAND_06 = ROOT / "reports-NOT-FOR-GH/HAND-report-06-before-coded-render.html"


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


def _report_05_page() -> Path:
    dest = RUNTIME / "previous-report.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    frozen = ROOT / "baselines/report-05.html"
    if frozen.exists():
        dest.write_bytes(frozen.read_bytes())
    else:
        dest.write_bytes(subprocess.check_output(["git", "show", "HEAD:index-v4.html"], cwd=ROOT))
    return dest


def _run_steps(replay: Path | None, live: bool, base: Path) -> int:
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
    folder = "replay" if replay else collector.get("run_id", "")
    run_path = JOB2 / folder / "collector-run.json"
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
    try:
        snap = build_snapshot(run_doc, labels, allow_partial=set())
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    snap_path = RUNTIME / "job3" / "render-snapshot.json"
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(snap, indent=2) + "\n")

    if not base.exists():
        print(f"missing base page: {base}", file=sys.stderr)
        return 2
    source = base
    built = build_manifest(source)
    blockers = built.pop("blockers")
    critical = [row for row in blockers if row.get("critical")]
    (RUNTIME / "job3" / "blockers.json").write_text(json.dumps(blockers, indent=2) + "\n")
    if critical:
        print(f"critical misses {len(critical)}; wrote nothing", file=sys.stderr)
        return 2
    # The displayed weekly buyback stays $6.8M. The pulled wallet figure is a different number.
    bindings = [row for row in built["bindings"] if row.get("metric_id") != "pump.buyback.usd.7d"]
    print(f"bindings {len(bindings)}")
    writers = json.loads((ROOT / "renderer/writer-quarantine.json").read_text())
    try:
        rendered, _manifest, render_code = render_report(
            source_html=source.read_text(encoding="utf-8"),
            bindings=bindings,
            snapshot=snap,
            writer_quarantine=writers,
            publishable=False,
        )
    except RuntimeError as exc:
        print(f"{exc}; wrote nothing", file=sys.stderr)
        return 3
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
    parser.add_argument("--base", type=Path, help="Page to build on. Report 06 uses the hand page.")
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
        print("Run:")
        print(f"  python3 make_report.py --base {HAND_06} --replay {REPLAY_26}")
        print(f"  python3 make_report.py --base {HAND_06} --live")
        return 2
    if args.base is None:
        print(f"pass --base. Report 06 builds on {HAND_06}", file=sys.stderr)
        return 2
    return _run_steps(args.replay, args.live, args.base)


if __name__ == "__main__":
    raise SystemExit(main())
