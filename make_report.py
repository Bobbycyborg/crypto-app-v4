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
from integrity.check_report import run_checker
from integrity.stale_gate import stale_problems
from renderer.build_binding_manifest import build_manifest
from renderer.build_snapshot import build_snapshot
from renderer.manual_zones import manual_zone_notes, wrap_manual_zones
from renderer.overrides import apply_overrides, load_overrides
from renderer.render_report import render_report
from renderer.report_config import load_report
from renderer.roster import apply_roster
from renderer.surface_slots import apply_known_slots, price_slot_bindings, restore_dormant_articles

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


def _undated_critical(snap: dict) -> list[str]:
    cfg = load_report()
    board = {asset.lower() for asset in list(cfg["always_shown"]) + list(cfg["held"]) + list(cfg["hidden"])}
    missing = []
    for mid, row in (snap.get("metrics") or {}).items():
        if not row or row.get("status") != "OK":
            continue
        asset = mid.split(".", 1)[0]
        interesting = (
            mid.endswith(".price.usd.live")
            or ".etf.flow." in mid
            or "fear_greed" in mid
            or mid.endswith(".funding.rate.mean_7d")
            or mid.endswith(".funding.rate.latest")
            or mid.endswith(".buyback.usd.7d")
            or mid.endswith(".inflation.pct.current")
        )
        if asset not in board and "fear_greed" not in mid:
            continue
        if not interesting:
            continue
        if not row.get("source_as_of") or row.get("source_as_of") == "UNKNOWN":
            missing.append(mid)
    return missing


def _gates_clear() -> tuple[bool, str]:
    check_path = RUNTIME / "job3" / "check-report.json"
    stale_path = RUNTIME / "job3" / "stale-gate.json"
    if not check_path.exists() or not stale_path.exists():
        return False, "checker and stale gate have not both been run"
    report = json.loads(check_path.read_text(encoding="utf-8"))
    gate = json.loads(stale_path.read_text(encoding="utf-8"))
    if report.get("overall_status") != "PASS":
        return False, f"checker is {report.get('overall_status')}"
    if gate.get("status") != "PASS":
        return False, "stale gate failed"
    return True, "ok"


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
    snap = apply_overrides(snap, number)
    undated = _undated_critical(snap)
    if undated:
        print("critical numbers with no source date:")
        for mid in undated:
            print(f"  {mid}")
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
        print(f"critical misses {len(critical)}")
        for row in critical[:20]:
            print(f"  {row['metric_id']} {row['reason']}")
    bindings = list(built["bindings"])
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
        print(f"render exit {render_code}", file=sys.stderr)
    rendered = apply_known_slots(rendered, snap)
    rendered = apply_roster(rendered)
    rendered = wrap_manual_zones(rendered, number)
    rendered = restore_dormant_articles(rendered, _report_05_page().read_text(encoding="utf-8"))
    notes = manual_zone_notes(rendered)
    print(f"needs human edit: {len(notes)} stance lines")
    for note in notes:
        print(f"  needs human edit: {note}")
    bindings.extend(price_slot_bindings(rendered, snap))
    built["bindings"] = bindings
    candidate = RUNTIME / f"candidate-{number}.html"
    candidate.write_text(rendered, encoding="utf-8")
    print(f"wrote {candidate}")

    manifest_path = RUNTIME / "job3" / "binding-manifest.json"
    manifest_path.write_text(json.dumps(built, indent=2) + "\n")
    contract = build_contract(
        registry_path=ROOT / "metrics/metric-registry.json",
        plan_path=ROOT / "collectors/collector-plan.json",
        bindings_path=manifest_path,
        source_html_path=source,
    )
    contract["overrides"] = load_overrides(number)
    contract_path = RUNTIME / "job3" / "report-contract.json"
    contract_path.write_text(json.dumps(contract, indent=2) + "\n")
    report = run_checker(
        snapshot_path=snap_path,
        rendered_html_path=candidate,
        source_html_path=source,
        bindings_path=manifest_path,
        registry_path=ROOT / "metrics/metric-registry.json",
        plan_path=ROOT / "collectors/collector-plan.json",
        contract_path=contract_path,
        run_id=str(collector.get("run_id") or "replay"),
    )
    check_path = RUNTIME / "job3" / "check-report.json"
    check_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    check_code = report.exit_code()
    print(f"checker {report.overall_status} exit {check_code}")
    previous = _report_05_page()
    problems = stale_problems(
        rendered,
        snapshot=snap,
        bindings=bindings,
        previous_html=previous.read_text(encoding="utf-8"),
        report_number=number,
    )
    stale_path = RUNTIME / "job3" / "stale-gate.json"
    stale_path.write_text(
        json.dumps({"status": "PASS" if not problems else "FAIL", "problems": problems}, indent=2) + "\n",
        encoding="utf-8",
    )
    if problems:
        print("stale gate FAIL")
        for item in problems:
            print(f"  {item}")
    else:
        print("stale gate PASS")
    print("Live page was not changed.")
    if render_code or check_code or problems or critical or undated:
        return render_code or check_code or (1 if problems or undated else 2)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue the next crypto report")
    parser.add_argument("--base", type=Path, help="Page to build on. Report 06 uses the hand page.")
    parser.add_argument("--replay", type=Path, help="Raw capture folder. No network.")
    parser.add_argument("--live", action="store_true", help="Pull new numbers. Uses the network.")
    parser.add_argument("--walk", action="store_true", help="Walk held wallets. Off unless you pass this.")
    parser.add_argument("--promote", action="store_true", help="Copy the candidate onto the live page. Refused until both gates pass.")
    parser.add_argument("--freeze", action="store_true", help="Save the candidate as a frozen report. Refused until both gates pass.")
    args = parser.parse_args()
    if args.promote or args.freeze:
        ok, why = _gates_clear()
        name = "promote" if args.promote else "freeze"
        if not ok:
            print(f"{name} refused. {why}.", file=sys.stderr)
            return 2
        print(f"{name} refused. Both gates passed, and the live page is still not replaced from this command.", file=sys.stderr)
        return 2
    if args.walk:
        print("wallet walk is off. It cannot write index-v4.html.", file=sys.stderr)
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
