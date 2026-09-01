#!/usr/bin/env python3
"""Independent Job 3 checker — no production renderer imports."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.eligibility import eligible_mappings, load_job1_job2
from renderer.formatter_recovery import is_numeric_binding, is_numeric_raw, _occurrence_raw

BANNED_IMPORT_PREFIXES = (
    "renderer.render_report",
    "renderer.build_snapshot",
    "renderer.formatters",
    "renderer.build_binding_manifest",
)

NEGATIVE_OCCURRENCE_IDS = {
    "143109097f847b67",
    "6cef931ee1ef29a2",
    "c6ae973de6959e49",
    "4d568968d384da40",
    "ad9b911811492672",
    "ce940255df156255",
}

NONNUMERIC_EXPECTED = {
    "render.bme.ratio.last4::00a581be80d3bc08",
    "btc.price.usd.report::24c837b712b58400",
    "hype.af.buys.usd.30d::4fb9087d25d45f86",
    "render.bme.ratio.last8::6ab520f912c0df64",
    "bonk.price.usd.live::73f03441b6c01eac",
    "render.bme.ratio.last8::a3bea5ef565305ea",
    "render.bme.ratio.last4::ade009462532f2d3",
    "render.bme.ratio.last4::b7bd7028b2909464",
    "render.bme.ratio.last4::bfa9b81a99db1d51",
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _assert_no_banned_imports(path: Path) -> int:
    tree = ast.parse(path.read_text())
    hits = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if any(n.name == p or n.name.startswith(p + ".") for p in BANNED_IMPORT_PREFIXES):
                    hits += 1
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(node.module == p or node.module.startswith(p + ".") for p in BANNED_IMPORT_PREFIXES):
                hits += 1
    return hits


def _parse_subprocess_counters(stdout: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in stdout.splitlines():
        if "=" in line and not line.startswith(" "):
            k, v = line.split("=", 1)
            if v.isdigit() or (v.startswith("-") and v[1:].isdigit()):
                out[k] = int(v)
    return out


def _nonnumeric_reason(binding: dict[str, Any], reg: dict[str, Any]) -> str:
    if is_numeric_binding(binding):
        return "not numeric usable"
    occ_raw = _occurrence_raw(reg.get(binding["metric_id"], {}), binding["job1_occurrence_id"])
    if occ_raw == "UNKNOWN" or occ_raw is None:
        return "occurrence raw missing or UNKNOWN"
    if not is_numeric_raw(occ_raw):
        return f"occurrence raw not parseable: {occ_raw!r}"
    return "occurrence raw failed natural formatter recovery"


def _compute_numeric_gates(bindings: list[dict[str, Any]], reg: dict[str, Any]) -> dict[str, int]:
    g = {
        "total_bindings": len(bindings),
        "numeric_bindings": 0,
        "nonnumeric_total": 0,
        "raw_roundtrip_verified": 0,
        "presentation_syntax_recovered": 0,
        "roundtrip_verified": 0,
        "unverified_numeric": 0,
        "numeric_string_exact": 0,
    }
    for b in bindings:
        if not is_numeric_binding(b):
            g["nonnumeric_total"] += 1
            continue
        g["numeric_bindings"] += 1
        fmt = b["formatter"]
        if fmt.get("type") == "string_exact":
            g["numeric_string_exact"] += 1
        if fmt.get("presentation_syntax_recovered"):
            g["presentation_syntax_recovered"] += 1
            g["roundtrip_verified"] += 1
        elif fmt.get("roundtrip_verified"):
            g["raw_roundtrip_verified"] += 1
            g["roundtrip_verified"] += 1
        else:
            g["unverified_numeric"] += 1
    return g


def main() -> int:
    self_path = Path(__file__)
    prod_imports = _assert_no_banned_imports(self_path)
    print(f"independent_checker_production_imports={prod_imports}")
    assert prod_imports == 0

    manifest = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
    bindings = manifest["bindings"]
    reg, plan, _manifest_meta, maps = load_job1_job2()
    elig = eligible_mappings(maps, reg, plan)
    elig_pairs = {(m["metric_id"], m["match"]["occurrence_id"]) for m in elig}
    bound_pairs = {(b["metric_id"], b["job1_occurrence_id"]) for b in bindings}
    bound_occ = {b["job1_occurrence_id"] for b in bindings}

    assert manifest["eligible_occurrences"] == len(bindings) == 418
    assert len(elig) == 418
    assert elig_pairs == bound_pairs
    assert _sha(ROOT / "metrics/metric-registry.json") == manifest["job1_registry_sha256"]
    assert _sha(ROOT / "index-v4.html") == manifest["source_html_sha256"]

    for rel in ("tests/job5", "tests/job6", "renderer/job4", "renderer/job5", "renderer/job6"):
        assert not (ROOT / rel).exists(), rel

    markup = sum(
        1
        for b in bindings
        if b["target_kind"] == "HTML_TEXT" and ("<" in b["source_literal"] or ">" in b["source_literal"])
    )
    assert markup == 0
    print(f"markup_inside_HTML_TEXT_binding={markup}")
    print(f"binding_crosses_tag_boundary={markup}")

    anchors = [b["anchor_sha256"] for b in bindings]
    assert len(anchors) == len(set(anchors))

    for b in bindings:
        assert b.get("owner") != "GROK"
        assert (b.get("asset") or "").upper() not in {"RAY", "GRASS", "DRIFT", "ORCA", "BONK"}
        cls = b.get("occurrence_classification")
        assert cls not in {"HISTORICAL", "STATIC_DECISION_THRESHOLD", "WALLET_OWNED", "PRESERVE"}

    for oid in NEGATIVE_OCCURRENCE_IDS:
        assert oid not in bound_occ, oid

    for py in (ROOT / "renderer").glob("*.py"):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    assert "requests" not in n.name
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "requests" not in node.module

    for fix in (ROOT / "tests/job3/fixtures").glob("collector-run-*.json"):
        data = json.loads(fix.read_text())
        assert data.get("_fixture_kind") == "SYNTHETIC_TEST_ONLY" or "SYNTHETIC" in data.get("run_id", "")
        for mid in (
            "btc.leverage.x.current",
            "global.leverage.x.current",
            "sol.supply.net_change.tokens.per_year",
            "zec.leverage.x.current",
        ):
            fact = next(f for f in data["facts"] if f["metric_id"] == mid)
            assert fact.get("source_key") is None, mid
            assert isinstance(fact.get("derivation_inputs"), list), mid

    gates = _compute_numeric_gates(bindings, reg)
    for k, v in gates.items():
        print(f"{k}={v}")

    assert gates["total_bindings"] == 418
    assert gates["numeric_bindings"] == 409
    assert gates["nonnumeric_total"] == 9
    assert gates["raw_roundtrip_verified"] == 405
    assert gates["presentation_syntax_recovered"] == 4
    assert gates["roundtrip_verified"] == 409
    assert gates["unverified_numeric"] == 0
    assert gates["numeric_string_exact"] == 0

    nonnumeric_ids = {b["binding_id"] for b in bindings if b["binding_id"] in NONNUMERIC_EXPECTED}
    assert nonnumeric_ids == NONNUMERIC_EXPECTED
    print("nonnumeric_bindings:")
    for b in bindings:
        if b["binding_id"] in NONNUMERIC_EXPECTED:
            print(f"  {b['binding_id']} {b['source_literal']!r} reason={_nonnumeric_reason(b, reg)}")

    suites = [
        "tests/job3/test_snapshot_derive.py",
        "tests/job3/test_formatter_roundtrip.py",
        "tests/job3/test_formatter_dynamicity.py",
        "tests/job3/test_formatter_raw_contract.py",
        "tests/job3/test_formatters.py",
        "tests/job3/test_golden_render.py",
        "tests/job3/test_renderer_fail_closed.py",
        "tests/job3/test_writer_quarantine.py",
    ]
    for rel in suites:
        rc = subprocess.run([sys.executable, str(ROOT / rel)], capture_output=True, text=True)
        assert rc.returncode == 0, f"{rel} failed:\n{rc.stdout}\n{rc.stderr}"

    rt = _parse_subprocess_counters(
        subprocess.run(
            [sys.executable, str(ROOT / "tests/job3/test_formatter_roundtrip.py")],
            capture_output=True,
            text=True,
        ).stdout
    )
    dyn = _parse_subprocess_counters(
        subprocess.run(
            [sys.executable, str(ROOT / "tests/job3/test_formatter_dynamicity.py")],
            capture_output=True,
            text=True,
        ).stdout
    )
    print(f"numeric_dynamicity_checked={dyn.get('numeric_dynamicity_checked', 0)}")
    print(f"numeric_dynamicity_failures={dyn.get('numeric_dynamicity_failures', 0)}")
    assert rt.get("roundtrip_verified") == 409
    assert rt.get("unverified_numeric") == 0
    assert dyn.get("numeric_dynamicity_checked") == 409
    assert dyn.get("numeric_dynamicity_failures") == 0

    rc = subprocess.run([sys.executable, str(ROOT / "tests/job3/test_writer_quarantine.py")], capture_output=True, text=True)
    m = re.search(r"shadow_nonwallet_current_network_writers=(\d+)", rc.stdout)
    assert m and m.group(1) == "0"

    for py in (ROOT / "renderer").glob("*.py"):
        assert "legacy_current" not in py.read_text().lower()

    print("test_job3_independent OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
