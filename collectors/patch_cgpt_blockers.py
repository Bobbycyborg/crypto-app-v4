#!/usr/bin/env python3
"""Apply CGPT Job 2B blocker decisions to source-recovery-contract.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "collectors/source-recovery-contract.json"

AUDIT = {
    "decision_authority": "CGPT",
    "decision_date": "2026-08-27",
}

PATCHES = {
    "hype.af.buys.usd.30d": {
        "required": True,
        "resolution": "CGPT_DECISION_COLLECT",
        "recovery_tier": "CGPT_DECISION",
        "source_key": "defillama",
        "request_key": "defillama.summary.fees.hyperliquid.dailyHoldersRevenue",
        "provider": "DefiLlama",
        "endpoint_or_method": "/summary/fees/hyperliquid?dataType=dailyHoldersRevenue",
        "selector": {"type": "json_key", "key": "total30d"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "decision_reason": (
            "DefiLlama methodology defines Hyperliquid Holders Revenue as fees "
            "directed to the Assistance Fund for buying HYPE."
        ),
        "notes": (
            "CGPT resolved blocker after historical recovery: "
            "DefiLlama methodology defines Hyperliquid Holders Revenue "
            "as fees directed to the Assistance Fund for buying HYPE."
        ),
        "semantic_match": {
            "asset": True,
            "measure": True,
            "scope": True,
            "window": True,
            "unit": True,
            "update_mode": True,
        },
    },
    "io.emissions.tokens.remaining": {
        "required": False,
        "resolution": "CGPT_DECISION_PRESERVE",
        "recovery_tier": "CGPT_DECISION",
        "source_key": None,
        "request_key": None,
        "provider": None,
        "endpoint_or_method": None,
        "selector": None,
        "normalizer": None,
        "derivation": None,
        "decision_reason": (
            "io.net IDE (Jun 2026) retired fixed 300M-over-20y emissions; "
            "no defensible current remaining-emissions collector."
        ),
        "notes": (
            "Legacy pre-IDE fixed-emission tokenomics. "
            "io.net's Incentive Dynamic Engine went live 11 Jun 2026 "
            "and replaced inflation-based tokenomics with a "
            "demand-driven issuance/burn system. "
            "The historical 300M-over-20y statement must not be "
            "collected or represented as a current remaining-emissions figure."
        ),
        "semantic_match": {
            "asset": "N/A",
            "measure": "N/A",
            "scope": "N/A",
            "window": "N/A",
            "unit": "N/A",
            "update_mode": "N/A",
        },
    },
    "render.emissions.tokens.remaining": {
        "required": True,
        "resolution": "CGPT_DECISION_COLLECT",
        "recovery_tier": "CGPT_DECISION",
        "source_key": "render_foundation",
        "request_key": "render.supplyInfo",
        "provider": "Render Network Foundation",
        "endpoint_or_method": "stats.renderfoundation.com dashboard supplyInfo leftoverEmissions",
        "selector": {"type": "json_key", "key": "leftoverEmissions"},
        "normalizer": {"type": "identity"},
        "derivation": None,
        "decision_reason": (
            "Official Render Foundation dashboard publishes explicit Leftover Emissions field."
        ),
        "notes": (
            "CGPT Job 2B: collect Leftover Emissions from stats.renderfoundation.com; "
            "epochBurnStats is not the semantic source for remaining emissions."
        ),
        "semantic_match": {
            "asset": True,
            "measure": True,
            "scope": True,
            "window": True,
            "unit": True,
            "update_mode": True,
        },
    },
    "spx.oi.change.pct.30d": {
        "required": True,
        "resolution": "CGPT_DECISION_COLLECT",
        "recovery_tier": "CGPT_DECISION",
        "source_key": "binance",
        "request_key": "binance.fapi.openInterestHist.SPXUSDT.1d",
        "provider": "Binance USDⓈ-M Futures",
        "endpoint_or_method": "openInterestHist SPXUSDT 1d sumOpenInterestValue",
        "selector": {
            "type": "named_record_field",
            "name": "open_interest_change_pct",
            "window": 30,
        },
        "normalizer": {"type": "identity"},
        "derivation": None,
        "decision_reason": (
            "CGPT resolved conflict in favour of Job 1 trailing 30d OI % change; "
            "V3 oi_vs_30d_max_pct is a different measure."
        ),
        "notes": (
            "CGPT resolved conflict in favour of the approved Job-1 semantic definition. "
            "V3 oi_vs_30d_max_pct remains historical evidence for a different measure "
            "and is forbidden as an input to this metric."
        ),
        "semantic_match": {
            "asset": True,
            "measure": True,
            "scope": True,
            "window": True,
            "unit": True,
            "update_mode": True,
        },
    },
}


def main() -> None:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    by_id = {e["metric_id"]: e for e in data["entries"]}
    for mid, patch in PATCHES.items():
        if mid not in by_id:
            raise SystemExit(f"missing contract entry {mid}")
        row = by_id[mid]
        row.update(patch)
        row.update(AUDIT)
    data["cgpt_blocker_decisions_applied_at"] = "2026-08-27T12:00:00Z"
    CONTRACT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("patched", len(PATCHES), "CGPT blocker entries")


if __name__ == "__main__":
    main()
