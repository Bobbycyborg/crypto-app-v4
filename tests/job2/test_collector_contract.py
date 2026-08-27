"""Job 2 contract: plan covers Job 1; no wallet/dormant collectors; COLLECT is complete."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from collectors.source_requests import REQUESTS

PLAN = json.loads((ROOT / "collectors/collector-plan.json").read_text())
REG = json.loads((ROOT / "metrics/metric-registry.json").read_text())


def test_every_job1_metric_in_plan() -> None:
    ids = {m["metric_id"] for m in REG["metrics"]}
    pids = {e["metric_id"] for e in PLAN["entries"]}
    assert ids == pids, sorted(ids ^ pids)[:20]


def test_no_duplicate_writers() -> None:
    ids = [e["metric_id"] for e in PLAN["entries"]]
    assert len(ids) == len(set(ids))


def test_no_job1_id_altered() -> None:
    assert {m["metric_id"] for m in REG["metrics"]} == {e["metric_id"] for e in PLAN["entries"]}


def test_no_ray_grass_collect() -> None:
    for e in PLAN["entries"]:
        if e["disposition"] in {"COLLECT", "DERIVE"}:
            assert "ray" not in e["metric_id"].split(".")[0]
            assert "grass" not in e["metric_id"].split(".")[0]
            assert e.get("asset") not in {"RAY", "GRASS"}


def test_no_grok_collect() -> None:
    by = {m["metric_id"]: m for m in REG["metrics"]}
    for e in PLAN["entries"]:
        m = by[e["metric_id"]]
        if m["owner"] == "GROK" or m["wallet_or_non_wallet"] == "WALLET":
            assert e["disposition"] == "GROK_WALLET"
            assert e["disposition"] != "COLLECT"


def test_no_wallet_or_helius_endpoint() -> None:
    blob = json.dumps(PLAN) + json.dumps(REQUESTS)
    assert "helius" not in blob.lower()
    assert "getSignaturesForAddress" not in blob


def test_collect_has_source_selector_normalizer() -> None:
    for e in PLAN["entries"]:
        if e["disposition"] != "COLLECT":
            continue
        assert e["source_key"]
        assert e["request_key"]
        assert e["selector"]
        assert e["normalizer"]
        assert e["request_key"] in REQUESTS
        assert REQUESTS[e["request_key"]]["source_key"] == e["source_key"]


def test_derive_has_inputs_no_eval() -> None:
    allowed = {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "RATIO", "PERCENT_CHANGE", "SUM", "MEAN"}
    for e in PLAN["entries"]:
        if e["disposition"] != "DERIVE":
            continue
        der = e["derivation"]
        assert der["op"] in allowed
        assert der["inputs"]
        assert der["calculation_version"]
        assert "eval" not in json.dumps(der).lower()


def test_required_dynamic_accounted() -> None:
    by = {m["metric_id"]: m for m in REG["metrics"]}
    for m in REG["metrics"]:
        if m["metric_type"] != "CURRENT_DYNAMIC":
            continue
        if m["wallet_or_non_wallet"] != "NON_WALLET":
            continue
        e = next(x for x in PLAN["entries"] if x["metric_id"] == m["metric_id"])
        assert e["disposition"] in {"COLLECT", "DERIVE", "PRESERVE", "BLOCKED_SOURCE", "COMPOSITE_ONLY", "LEGACY_INACTIVE"}


if __name__ == "__main__":
    test_every_job1_metric_in_plan()
    test_no_duplicate_writers()
    test_no_job1_id_altered()
    test_no_ray_grass_collect()
    test_no_grok_collect()
    test_no_wallet_or_helius_endpoint()
    test_collect_has_source_selector_normalizer()
    test_derive_has_inputs_no_eval()
    test_required_dynamic_accounted()
    print("PASS test_collector_contract")
    raise SystemExit(0)
