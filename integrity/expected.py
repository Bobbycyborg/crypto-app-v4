"""Deterministic expected check-ID set from report-contract.json — stdlib only."""

from __future__ import annotations

from typing import Any

LINEAGE_CHECK_IDS: tuple[str, ...] = (
    "01_lineage_01_registry",
    "01_lineage_02_collector_plan",
    "01_lineage_03_binding_manifest",
    "01_lineage_04_source_html_contract",
    "01_lineage_05_snapshot_job1_registry",
    "01_lineage_06_snapshot_collector_plan",
    "01_lineage_07_manifest_source_actual",
    "01_lineage_08_manifest_source_contract",
)

PERMANENT_REGRESSION_IDS: tuple[str, ...] = (
    "12_reg_spx_price_duplicate",
    "12_reg_pump_buyback_duplicate",
    "12_reg_pump_wallet_invariance",
)


def expected_check_ids(contract: dict[str, Any]) -> list[str]:
    """Complete expected check-ID list from contract structure only. Never from runtime."""
    stored = contract.get("expected_check_ids")
    if isinstance(stored, list) and stored:
        return list(stored)
    return compute_expected_check_ids(contract)


def compute_expected_check_ids(contract: dict[str, Any]) -> list[str]:
    ids: list[str] = list(LINEAGE_CHECK_IDS)
    for asset in contract["active_report_assets"]:
        ids.append(f"02_asset_{asset}")
    for ex in contract["excluded_assets"]:
        ids.append(f"02_excluded_{ex}_not_required")
    for mid in contract["bound_metric_ids"]:
        ids.append(f"03_metric_{mid.replace('.', '_')}")
    for bid in sorted(contract.get("surface_by_binding", {})):
        ids.append(f"04_bind_{bid}")
    for mid in sorted(contract.get("duplicate_metric_groups", {})):
        ids.append(f"05_dup_{mid.replace('.', '_')}")
    for rule in contract.get("ath_drawdown_rules", []):
        ids.append(f"06_ath_{rule['asset']}")
    for claim in contract.get("ma_language_claims", []):
        ids.append(f"07_ma_{claim['claim_id'].replace('::', '_')}")
    for claim in contract.get("rs_language_claims", []):
        ids.append(f"08_rs_{claim['claim_id'].replace('::', '_')}")
    for mid in contract.get("freshness_metric_ids", []):
        ids.append(f"09_fresh_{mid.replace('.', '_')}")
    for mid in contract.get("surface_metric_ids", []):
        ids.append(f"10_surface_{mid.replace('.', '_')}")
    for rule in contract.get("derive_rules", []):
        ids.append(f"11_derive_{rule['metric_id'].replace('.', '_')}")
    ids.extend(PERMANENT_REGRESSION_IDS)
    return ids
