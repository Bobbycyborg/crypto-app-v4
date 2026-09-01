"""Job 4 integrity checker data model — stdlib only."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "job4.integrity.v1"
CONTRACT_SCHEMA_VERSION = "job4.contract.v1"

ACTIVE_REPORT_ASSETS: tuple[str, ...] = (
    "btc",
    "sol",
    "render",
    "pump",
    "io",
    "nos",
    "fartcoin",
    "spx6900",
    "zec",
    "hype",
)

EXCLUDED_ASSETS: tuple[str, ...] = ("ray", "grass", "drift", "orca", "bonk")

REQUIRED_CATEGORIES: tuple[str, ...] = (
    "01_input_lineage",
    "02_active_asset_coverage",
    "03_canonical_metric_coverage",
    "04_rendered_binding_consistency",
    "05_duplicate_consistency",
    "06_ath_drawdown_arithmetic",
    "07_moving_average_language",
    "08_relative_strength_language",
    "09_freshness_asof_consistency",
    "10_tooltip_visible_visual_agreement",
    "11_derived_metric_arithmetic",
    "12_permanent_regressions",
)

CHECK_STATUSES = frozenset(
    {"PASS", "FAIL", "COVERAGE_GAP", "BLOCKED_UNKNOWN", "NOT_APPLICABLE"}
)

NON_OK_STATUSES = frozenset(
    {
        "UNKNOWN",
        "SOURCE_UNAVAILABLE",
        "AUTH_MISSING",
        "SOURCE_SCHEMA_MISMATCH",
        "VALUE_MISSING",
        "VALUE_INVALID",
        "DERIVATION_BLOCKED",
        "BLOCKED_SOURCE",
        "OUT_OF_SCOPE",
    }
)

EXIT_PASS = 0
EXIT_FAIL = 2
EXIT_COVERAGE_GAP = 3
EXIT_INPUT_LINEAGE = 4
EXIT_INTERNAL = 5

ASSET_METRIC_PREFIX: dict[str, str] = {
    "btc": "btc",
    "sol": "sol",
    "render": "render",
    "pump": "pump",
    "io": "io",
    "nos": "nos",
    "fartcoin": "fart",
    "spx6900": "spx",
    "zec": "zec",
    "hype": "hype",
}


@dataclass
class CheckResult:
    check_id: str
    category: str
    asset: str | None
    rule_type: str
    metric_ids: list[str]
    status: str
    assertions_executed: int
    observed: Any
    expected_relation: str
    evidence: dict[str, Any]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntegrityReport:
    schema_version: str
    run_id: str
    inputs: dict[str, Any]
    counts: dict[str, int]
    categories: dict[str, dict[str, Any]]
    assets: dict[str, dict[str, Any]]
    checks: list[CheckResult] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)
    overall_status: str = "FAIL"
    expected_check_ids: list[str] = field(default_factory=list)
    executed_check_ids: list[str] = field(default_factory=list)
    missing_check_ids: list[str] = field(default_factory=list)
    unexpected_check_ids: list[str] = field(default_factory=list)

    def finalize(
        self,
        *,
        contract_required: tuple[str, ...] | None = None,
        expected_check_ids: list[str] | None = None,
    ) -> None:
        req = contract_required or REQUIRED_CATEGORIES
        contract_incomplete = set(req) != set(REQUIRED_CATEGORIES)
        expected = list(expected_check_ids or [])
        executed_before = [c.check_id for c in self.checks]
        missing = sorted(set(expected) - set(executed_before))
        unexpected = sorted(set(executed_before) - set(expected))
        self.expected_check_ids = expected
        self.executed_check_ids = list(executed_before)
        self.missing_check_ids = missing
        self.unexpected_check_ids = unexpected
        for cid in missing:
            cat = cid.split("_")[0]
            if cid.startswith("01_"):
                cat = "01_input_lineage"
            elif cid.startswith("02_"):
                cat = "02_active_asset_coverage"
            elif cid.startswith("03_"):
                cat = "03_canonical_metric_coverage"
            elif cid.startswith("04_"):
                cat = "04_rendered_binding_consistency"
            elif cid.startswith("05_"):
                cat = "05_duplicate_consistency"
            elif cid.startswith("06_"):
                cat = "06_ath_drawdown_arithmetic"
            elif cid.startswith("07_"):
                cat = "07_moving_average_language"
            elif cid.startswith("08_"):
                cat = "08_relative_strength_language"
            elif cid.startswith("09_"):
                cat = "09_freshness_asof_consistency"
            elif cid.startswith("10_"):
                cat = "10_tooltip_visible_visual_agreement"
            elif cid.startswith("11_"):
                cat = "11_derived_metric_arithmetic"
            elif cid.startswith("12_"):
                cat = "12_permanent_regressions"
            self.checks.append(
                CheckResult(
                    check_id=cid,
                    category=cat,
                    asset=None,
                    rule_type="expected_check_missing",
                    metric_ids=[],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=None,
                    expected_relation="check executed",
                    evidence={"missing": True},
                    reason="expected check not executed",
                )
            )
        for cid in unexpected:
            self.checks.append(
                CheckResult(
                    check_id=f"00_unexpected_{cid}",
                    category="01_input_lineage",
                    asset=None,
                    rule_type="unexpected_check",
                    metric_ids=[],
                    status="FAIL",
                    assertions_executed=1,
                    observed=cid,
                    expected_relation="check_id in expected_check_ids",
                    evidence={"unexpected": cid},
                    reason="unexpected check_id",
                )
            )
        self.checks.sort(key=lambda c: c.check_id)
        self.failures = [
            {
                "check_id": c.check_id,
                "category": c.category,
                "asset": c.asset,
                "rule_type": c.rule_type,
                "metric_ids": c.metric_ids,
                "status": c.status,
                "reason": c.reason,
            }
            for c in self.checks
            if c.status in {"FAIL", "COVERAGE_GAP"}
        ]
        self.failures.sort(key=lambda f: f["check_id"])
        counts = {
            "expected": 0,
            "executed": 0,
            "pass": 0,
            "fail": 0,
            "coverage_gap": 0,
            "blocked_unknown": 0,
            "not_applicable": 0,
        }
        for c in self.checks:
            counts["executed"] += 1
            key = c.status.lower()
            if key == "pass":
                counts["pass"] += 1
            elif key == "fail":
                counts["fail"] += 1
            elif key == "coverage_gap":
                counts["coverage_gap"] += 1
            elif key == "blocked_unknown":
                counts["blocked_unknown"] += 1
            elif key == "not_applicable":
                counts["not_applicable"] += 1
        counts["executed"] = len(self.executed_check_ids)
        counts["expected"] = len(expected)
        self.counts = counts
        cats: dict[str, dict[str, Any]] = {}
        for cat in req:
            cat_checks = [c for c in self.checks if c.category == cat]
            if not cat_checks:
                cats[cat] = {"present": False, "status": "COVERAGE_GAP"}
            else:
                statuses = {c.status for c in cat_checks}
                if "FAIL" in statuses:
                    st = "FAIL"
                elif "COVERAGE_GAP" in statuses:
                    st = "COVERAGE_GAP"
                elif statuses <= {"PASS", "NOT_APPLICABLE", "BLOCKED_UNKNOWN"}:
                    st = "PASS"
                else:
                    st = "FAIL"
                cats[cat] = {
                    "present": True,
                    "status": st,
                    "checks": len(cat_checks),
                    "pass": sum(1 for c in cat_checks if c.status == "PASS"),
                    "fail": sum(1 for c in cat_checks if c.status == "FAIL"),
                    "coverage_gap": sum(
                        1 for c in cat_checks if c.status == "COVERAGE_GAP"
                    ),
                    "blocked_unknown": sum(
                        1 for c in cat_checks if c.status == "BLOCKED_UNKNOWN"
                    ),
                    "not_applicable": sum(
                        1 for c in cat_checks if c.status == "NOT_APPLICABLE"
                    ),
                }
        self.categories = cats
        assets: dict[str, dict[str, Any]] = {}
        for asset in sorted(ACTIVE_REPORT_ASSETS):
            ac = [c for c in self.checks if c.asset == asset]
            if not ac:
                assets[asset] = {"checks": 0, "status": "COVERAGE_GAP"}
            else:
                st = "FAIL" if any(c.status == "FAIL" for c in ac) else (
                    "COVERAGE_GAP"
                    if any(c.status == "COVERAGE_GAP" for c in ac)
                    else "PASS"
                )
                assets[asset] = {
                    "checks": len(ac),
                    "status": st,
                    "fail": sum(1 for c in ac if c.status == "FAIL"),
                }
        self.assets = assets
        missing_cats = list(set(REQUIRED_CATEGORIES) - set(req)) if contract_incomplete else [
            c for c in req if c not in cats or not cats[c].get("present")
        ]
        ids_match = bool(expected) and set(self.executed_check_ids) == set(expected)
        if (
            counts["fail"]
            or counts["coverage_gap"]
            or missing_cats
            or missing
            or unexpected
            or not ids_match
        ):
            self.overall_status = (
                "COVERAGE_GAP"
                if counts["coverage_gap"] or missing_cats or missing
                else "FAIL"
            )
        else:
            self.overall_status = "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "inputs": self.inputs,
            "counts": self.counts,
            "categories": self.categories,
            "assets": self.assets,
            "checks": [c.to_dict() for c in self.checks],
            "failures": self.failures,
            "overall_status": self.overall_status,
            "expected_check_ids": self.expected_check_ids,
            "executed_check_ids": self.executed_check_ids,
            "missing_check_ids": self.missing_check_ids,
            "unexpected_check_ids": self.unexpected_check_ids,
        }

    def exit_code(self) -> int:
        lineage = any(
            c.check_id.startswith("01_lineage_") and c.status == "FAIL"
            for c in self.checks
        )
        if lineage:
            return EXIT_INPUT_LINEAGE
        if self.overall_status == "PASS":
            return EXIT_PASS
        if self.overall_status == "COVERAGE_GAP" or self.missing_check_ids:
            return EXIT_COVERAGE_GAP
        if self.counts.get("coverage_gap", 0):
            return EXIT_COVERAGE_GAP
        return EXIT_FAIL
