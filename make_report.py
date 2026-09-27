#!/usr/bin/env python3
"""One command for the next report.

Writes a candidate file only. Does not replace the live page.
Does not push. Does not walk wallets unless --walk is passed.
"""

from __future__ import annotations

import argparse
import hashlib
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
from renderer.prose_slots import apply_prose
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
    cfg = load_report()
    candidate = RUNTIME / f"candidate-{cfg['report_number']}.html"
    if not candidate.exists():
        return False, "no candidate"
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if report.get("candidate_sha256") != digest or gate.get("candidate_sha256") != digest:
        return False, "the page was not the one that was checked"
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


def _write_summary(lines: list[str]) -> None:
    path = RUNTIME / "run-summary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines[:24]) + "\n"
    path.write_text(text, encoding="utf-8")
    print(text)


def _run_steps(replay: Path | None, live: bool, base: Path, walk: bool = False) -> int:
    notes_out: list[str] = []
    pre = preflight()
    if pre:
        notes_out.append("Preflight: pipeline files are still edited. The run continued.")
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
        notes_out.append(f"Collector exit {code}. Later steps still ran.")
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
        snap = build_snapshot(run_doc, labels, allow_partial=set(failed))
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        notes_out.append(f"Snapshot refused: {exc}")
        snap = {"metrics": {}}
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
        print(f"{exc}; checker still runs on the base page", file=sys.stderr)
        notes_out.append(f"Render failed: {exc}")
        rendered = source.read_text(encoding="utf-8")
        render_code = 3
    if render_code != 0:
        print(f"render exit {render_code}", file=sys.stderr)
    rendered = apply_known_slots(rendered, snap)
    rendered = apply_prose(rendered, snap, previous_html=_report_05_page().read_text(encoding="utf-8"))
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
    if walk:
        try:
            from lib.v3.siren_watch import apply_index, run_check

            apply_index(run_check(), target=candidate)
            notes_out.append("Wallet walk wrote the candidate only.")
        except Exception as exc:  # noqa: BLE001
            notes_out.append(f"Wallet walk failed: {exc}")
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
    check_code = report.exit_code()
    print(f"checker {report.overall_status} exit {check_code}")
    previous = _report_05_page()
    problems = stale_problems(
        rendered,
        snapshot=snap,
        bindings=bindings,
        previous_html=previous.read_text(encoding="utf-8"),
        base_html=source.read_text(encoding="utf-8"),
        report_number=number,
    )
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    stale_path = RUNTIME / "job3" / "stale-gate.json"
    stale_path.write_text(
        json.dumps(
            {
                "status": "PASS" if not problems else "FAIL",
                "count": len(problems),
                "candidate_sha256": digest,
                "problems": problems,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    checked = report.to_dict()
    checked["candidate_sha256"] = digest
    check_path = RUNTIME / "job3" / "check-report.json"
    check_path.write_text(json.dumps(checked, indent=2) + "\n")
    if problems:
        print("stale gate FAIL")
        for item in problems:
            print(f"  {item}")
    else:
        print("stale gate PASS")
    print("Live page was not changed.")
    fresh = int(run_doc.get("required_ok") or 0)
    total = int(run_doc.get("required_dynamic") or 0) or 1
    lines = [
        f"Report {number} candidate. Fresh {fresh}/{total} ({round(100 * fresh / total)}%). Live page not touched.",
        f"Candidate sha256 {digest}",
        f"Checker {report.overall_status}. Stale lines {len(problems)}. Critical misses {len(critical)}.",
    ]
    for asset in ("eth", "sol"):
        for window in ("1d", "7d", "30d"):
            mid = f"{asset}.etf.flow.usd.{window}"
            row = (snap.get("metrics") or {}).get(mid) or {}
            if row.get("status") != "OK":
                used = row.get("source_used") or "none"
                lines.append(f"- {mid}: missing ({row.get('status') or 'absent'}, source {used}). Fix: the next live ETF source, or leave UNKNOWN.")
    for item in failed:
        if ".etf.flow." in item:
            continue
        lines.append(f"- {item}: no number this pull. Fix: use the next live source, or leave it UNKNOWN.")
        if len(lines) > 16:
            break
    for item in undated[:3]:
        lines.append(f"- {item}: no source date. Fix: read the date that came with that source.")
    for item in problems[:3]:
        lines.append(f"- {item}")
    for row in load_overrides(number):
        lines.append(
            f"- Override {row['metric_id']} by {row.get('author')} source {row.get('source')}: "
            f"show {row['value']}, pulled {row.get('pulled_value')}. {row.get('reason')}"
        )
    lines.append(f"Needs you: {len(notes)} stance lines. July low stays as written. Confirm the $6.8M buyback.")
    for note in notes[:2]:
        lines.append(f"- {note}")
    lines.extend(notes_out[:2])
    _write_summary(lines)
    if render_code or check_code or problems or critical or undated or failed:
        return render_code or check_code or (1 if problems or undated or failed else 2)
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
        cfg = load_report()
        candidate = RUNTIME / f"candidate-{cfg['report_number']}.html"
        if not candidate.exists():
            print(f"{name} refused. No candidate.", file=sys.stderr)
            return 2
        if args.promote:
            (ROOT / "index-v4.html").write_bytes(candidate.read_bytes())
            print(f"promoted {candidate} onto index-v4.html")
        else:
            frozen = ROOT / "baselines" / f"report-{cfg['report_number']}.html"
            frozen.write_bytes(candidate.read_bytes())
            print(f"froze {candidate} as {frozen}")
        return 0
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
    return _run_steps(args.replay, args.live, args.base, walk=args.walk)


if __name__ == "__main__":
    raise SystemExit(main())
