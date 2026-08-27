#!/usr/bin/env python3
"""Job 3 binding contract gates — all anomaly counters must be zero."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from renderer.eligibility import eligible_mappings, load_job1_job2

MANIFEST = json.loads((ROOT / "renderer/binding-manifest.json").read_text())
BINDINGS = MANIFEST["bindings"]
REG, PLAN, _, MAPS = load_job1_job2()
ELIG = eligible_mappings(MAPS, REG, PLAN)
HTML = (ROOT / "index-v4.html").read_text()


def gates() -> dict[str, int]:
    g = {k: 0 for k in [
        "eligible_job1_occurrences", "binding_entries", "eligible_unbound", "bound_ineligible",
        "duplicate_binding_ids", "duplicate_job1_occurrences", "unknown_metric_ids", "owner_grok_bound",
        "dormant_asset_bound", "preserve_metric_bound", "static_threshold_bound", "historical_bound",
        "ambiguous_anchor", "missing_anchor", "overlapping_binding", "missing_formatter", "unknown_target_kind",
        "markup_inside_HTML_TEXT_binding", "binding_crosses_tag_boundary",
    ]}
    g["eligible_job1_occurrences"] = len(ELIG)
    g["binding_entries"] = len(BINDINGS)
    elig_pairs = {(m["metric_id"], m["match"]["occurrence_id"]) for m in ELIG}
    bound_pairs = {(b["metric_id"], b["job1_occurrence_id"]) for b in BINDINGS}
    g["eligible_unbound"] = len(elig_pairs - bound_pairs)
    g["duplicate_binding_ids"] = len(BINDINGS) - len({b["binding_id"] for b in BINDINGS})
    g["duplicate_job1_occurrences"] = len(BINDINGS) - len(bound_pairs)
    reg_ids = {m["metric_id"] for m in REG.values()}
    plan_ids = set(PLAN)
    for b in BINDINGS:
        if b["metric_id"] not in reg_ids or b["metric_id"] not in plan_ids:
            g["unknown_metric_ids"] += 1
        if b.get("owner") == "GROK":
            g["owner_grok_bound"] += 1
        if (b.get("asset") or "").upper() in {"RAY", "GRASS", "DRIFT"}:
            g["dormant_asset_bound"] += 1
        cls = b.get("occurrence_classification")
        if cls == "PRESERVE":
            g["preserve_metric_bound"] += 1
        if cls == "STATIC_DECISION_THRESHOLD":
            g["static_threshold_bound"] += 1
        if cls == "HISTORICAL":
            g["historical_bound"] += 1
        if not b.get("formatter"):
            g["missing_formatter"] += 1
        if b["target_kind"] == "HTML_TEXT" and ("<" in b["source_literal"] or ">" in b["source_literal"]):
            g["markup_inside_HTML_TEXT_binding"] += 1
            g["binding_crosses_tag_boundary"] += 1
        combo = b["anchor_before"] + b["source_literal"] + b["anchor_after"]
        c = HTML.count(combo)
        if c == 0:
            g["missing_anchor"] += 1
        elif c > 1:
            g["ambiguous_anchor"] += 1
    spans = []
    for b in BINDINGS:
        combo = b["anchor_before"] + b["source_literal"] + b["anchor_after"]
        i = HTML.index(combo) + len(b["anchor_before"])
        spans.append((i, i + len(b["source_literal"]), b["binding_id"]))
    spans.sort()
    for (a0, a1, _), (b0, b1, _) in zip(spans, spans[1:]):
        if not (a1 <= b0 or a0 >= b1):
            g["overlapping_binding"] += 1
    return g


def main() -> int:
    g = gates()
    for k, v in g.items():
        print(f"{k}={v}")
    bad = {k: v for k, v in g.items() if v != 0 and k not in {"eligible_job1_occurrences", "binding_entries"}}
    if g["eligible_job1_occurrences"] != g["binding_entries"]:
        return 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
