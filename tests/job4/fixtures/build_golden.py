#!/usr/bin/env python3
"""Build golden Job4 fixtures from binding manifest + index-v4.html — tests only."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from integrity.numeric import parse_display_token


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _pick_hero_binding(group: list[dict]) -> dict:
    numeric = [
        b
        for b in group
        if (b.get("formatter") or {}).get("type") == "numeric" and b.get("binding_raw") is not None
    ]
    if numeric:
        return numeric[0]
    alt = [b for b in group if "alt-price" in b.get("anchor_before", "")]
    if alt:
        return alt[0]
    return group[0]


def _canonical_raw(hero: dict) -> int | float | str | None:
    fmt = hero.get("formatter") or {}
    lit = hero.get("source_literal", "")
    if fmt.get("type") == "string_exact":
        return lit
    parsed = parse_display_token(lit)
    if parsed is not None:
        return float(parsed)
    raw = hero.get("binding_raw")
    if raw is not None:
        return float(raw)
    return None


def _build_snapshot_from_bindings(contract: dict) -> dict:
    base = _load(ROOT / "tests/job3/fixtures/snapshot-baseline.json")
    manifest = _load(ROOT / "renderer/binding-manifest.json")
    reg = {m["metric_id"]: m for m in _load(ROOT / "metrics/metric-registry.json")["metrics"]}
    metrics = copy.deepcopy(base["metrics"])
    by_metric: dict[str, list[dict]] = {}
    for b in manifest["bindings"]:
        if b.get("owner") != "CGPT_CURSOR":
            continue
        by_metric.setdefault(b["metric_id"], []).append(b)
    for mid, group in by_metric.items():
        hero = _pick_hero_binding(group)
        raw = _canonical_raw(hero)
        if raw is None:
            continue
        rec = metrics.get(mid)
        if not rec:
            rec = {
                "metric_id": mid,
                "status": "OK",
                "unit": reg.get(mid, {}).get("unit") or "UNKNOWN",
                "source_key": "synthetic",
                "source_label": "SYNTHETIC_TEST_ONLY",
                "source_as_of": "2026-08-01T00:00:00Z",
                "fetched_at": "UNKNOWN",
                "freshness": "UNKNOWN",
                "calculation_version": "SYNTHETIC_TEST_ONLY",
                "derivation_inputs": None,
                "error": None,
            }
        rec["status"] = "OK"
        rec["normalized_value"] = raw
        metrics[mid] = rec
    snapshot = {
        "schema_version": base["schema_version"],
        "_fixture_kind": "SYNTHETIC_TEST_ONLY",
        "source_run_id": "JOB4_GOLDEN_SYNTHETIC",
        "source_collector_run_sha256": base["source_collector_run_sha256"],
        "job1_registry_sha256": base["job1_registry_sha256"],
        "collector_plan_sha256": base["collector_plan_sha256"],
        "generated_at": "2026-08-01T00:00:00Z",
        "metrics": metrics,
    }
    return snapshot


def _patch_ath(snapshot: dict, contract: dict) -> None:
    metrics = snapshot["metrics"]
    reg = {m["metric_id"]: m for m in _load(ROOT / "metrics/metric-registry.json")["metrics"]}
    for rule in contract.get("ath_drawdown_rules", []):
        price = metrics.get(rule["price_metric_id"])
        dd = metrics.get(rule["drawdown_metric_id"])
        if not price or not dd:
            continue
        if price.get("status") != "OK" or dd.get("status") != "OK":
            continue
        p = Decimal(str(price["normalized_value"]))
        d = Decimal(str(dd["normalized_value"]))
        if d == Decimal("-100"):
            continue
        ath_val = p / (Decimal("1") + d / Decimal("100"))
        mid = rule["ath_metric_id"]
        rec = metrics.get(mid)
        if not rec:
            rec = {
                "metric_id": mid,
                "status": "OK",
                "unit": reg.get(mid, {}).get("unit") or "USD",
                "source_key": "synthetic",
                "source_label": "SYNTHETIC_TEST_ONLY",
                "source_as_of": "2026-08-01T00:00:00Z",
                "fetched_at": "UNKNOWN",
                "freshness": "UNKNOWN",
                "calculation_version": "SYNTHETIC_TEST_ONLY",
                "derivation_inputs": None,
                "error": None,
            }
        rec["status"] = "OK"
        rec["normalized_value"] = float(ath_val)
        metrics[mid] = rec


def _patch_golden_fixes(snapshot: dict, contract: dict) -> None:
    """Surgical snapshot fixes so golden passes contract semantics after render."""
    metrics = snapshot["metrics"]
    for claim in contract.get("rs_language_claims", []):
        rec = metrics.get(claim["metric_id"])
        if not rec or rec.get("status") != "OK":
            continue
        val = float(rec.get("normalized_value") or 0)
        if claim["language"] == "LEADS" and val < 0:
            rec["normalized_value"] = abs(val) if val else 5.0
        elif claim["language"] == "LAGS" and val > 0:
            rec["normalized_value"] = -abs(val) if val else -5.0
    for claim in contract.get("ma_language_claims", []):
        if claim.get("asset") != "io":
            continue
        price = metrics.get(claim["price_metric_id"])
        ma50 = metrics.get(claim.get("ma50_metric_id") or "")
        ma200 = metrics.get(claim.get("ma200_metric_id") or "")
        if not price or not ma50 or not ma200:
            continue
        p = Decimal("0.18")
        m50 = Decimal("0.15")
        m200 = Decimal("0.12")
        price["normalized_value"] = float(p)
        ma50["normalized_value"] = float(m50)
        ma200["normalized_value"] = float(m200)


def _patch_derive(snapshot: dict, contract: dict) -> None:
    metrics = snapshot["metrics"]
    for rule in contract.get("derive_rules", []):
        mid = rule["metric_id"]
        inputs = rule["inputs"]
        vals = []
        for i in inputs:
            rec = metrics.get(i)
            if not rec:
                continue
            vals.append(Decimal(str(rec["normalized_value"])))
        if len(vals) != len(inputs):
            continue
        if rule["op"] == "RATIO" and vals[1] != 0:
            result = vals[0] / vals[1]
        elif rule["op"] == "SUBTRACT":
            result = vals[0] - vals[1]
        else:
            continue
        if mid in metrics:
            metrics[mid]["normalized_value"] = float(result)
            metrics[mid]["status"] = "OK"


def _render_html(snapshot_path: Path, out_path: Path) -> int:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "renderer/render_report.py"),
            "--snapshot",
            str(snapshot_path),
            "--source",
            str(ROOT / "index-v4.html"),
            "--bindings",
            str(ROOT / "renderer/binding-manifest.json"),
            "--writers",
            str(ROOT / "renderer/writer-quarantine.json"),
            "--out",
            str(out_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode not in (0, 2):
        raise RuntimeError(f"renderer failed ({proc.returncode}): {proc.stderr or proc.stdout}")
    return proc.returncode


def main() -> int:
    contract = _load(ROOT / "integrity/report-contract.json")
    snapshot = _build_snapshot_from_bindings(contract)
    _patch_golden_fixes(snapshot, contract)
    _patch_ath(snapshot, contract)
    _patch_derive(snapshot, contract)
    snap_path = FIX / "golden-snapshot.json"
    _save(snap_path, snapshot)
    rendered_path = FIX / "golden-rendered.html"
    _render_html(snap_path, rendered_path)
    src_orig = (ROOT / "index-v4.html").read_text(encoding="utf-8")
    banner = "<!-- SYNTHETIC TEST ONLY — NOT CURRENT DATA -->\n"
    (FIX / "golden-source.html").write_text(banner + src_orig, encoding="utf-8")
    print(f"golden fixtures written to {FIX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
