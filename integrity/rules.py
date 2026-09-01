"""Integrity check rules — stdlib only, no renderer imports."""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import Any

from integrity.extract import (
    classify_surface,
    extract_articles,
    extract_stance_headline,
    extract_visual_bar_width,
    locate_binding_span,
)
from integrity.model import (
    ACTIVE_REPORT_ASSETS,
    EXCLUDED_ASSETS,
    NON_OK_STATUSES,
    REQUIRED_CATEGORIES,
    CheckResult,
)
from integrity.numeric import (
    compact_usd_formatter,
    dec,
    derive_ratio,
    derive_subtract,
    display_tolerance,
    drawdown_pct,
    inferred_numeric_formatter,
    is_etf_flow_metric,
    parse_binding_observed,
    parse_display_token,
    values_compatible,
)


def _fmt_for_metric(metric_id: str, binding_fmt: dict[str, Any] | None, canonical: Decimal) -> dict[str, Any]:
    if is_etf_flow_metric(metric_id):
        return compact_usd_formatter(canonical)
    return binding_fmt or {}


def _signed_etf_obs(metric_id: str, observed: Decimal | None, canonical: Decimal) -> Decimal | None:
    if observed is None:
        return None
    if is_etf_flow_metric(metric_id) and canonical < 0 and observed > 0:
        return -observed
    return observed


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: str) -> str:
    from pathlib import Path

    return _sha256_bytes(Path(path).read_bytes())


def _snap_metric(snapshot: dict[str, Any], mid: str) -> dict[str, Any] | None:
    return snapshot.get("metrics", {}).get(mid)


def _is_grok(reg: dict[str, Any], mid: str) -> bool:
    row = reg.get(mid) or {}
    return row.get("owner") == "GROK"


def _roster_removed(*htmls: str, asset: str | None = None, metric_id: str = "") -> bool:
    """ORCA/BONK hidden (or absent) on Report 05 UI. Same check IDs, NOT_APPLICABLE."""
    mid = (metric_id or "").lower()
    a = (asset or "").lower()
    token = None
    if a == "orca" or mid.startswith("orca."):
        token = "orca"
    elif a == "bonk" or mid.startswith("bonk."):
        token = "bonk"
    if not token:
        return False
    for h in htmls:
        if not h:
            continue
        if token == "orca":
            if 'data-asset-slug="orca"' not in h:
                return True
            m = re.search(r'<[^>]*data-asset-slug="orca"[^>]*>', h)
            if m and "is-hidden" in m.group(0):
                return True
        if token == "bonk":
            if 'hold-ticker">BONK' not in h and 'desk-name">BONK' not in h:
                return True
            m = re.search(r'<[^>]*data-feed="spot:BONKUSDT"[^>]*>', h)
            if m and "is-hidden" in m.group(0):
                return True
            m = re.search(r'<div class="desk-row[^"]*"[^>]*>\s*<span class="desk-name">BONK</span>', h)
            if m and "is-hidden" in m.group(0):
                return True
    return False


def _na_roster(check_id: str, category: str, asset: str | None, mid: str) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        category=category,
        asset=asset,
        rule_type="roster_removed",
        metric_ids=[mid] if mid else [],
        status="NOT_APPLICABLE",
        assertions_executed=1,
        observed=None,
        expected_relation="hidden on report 05 roster",
        evidence={},
        reason="hidden on report 05 roster",
    )


def _expected_numeric(snap: dict[str, Any] | None) -> float | None:
    if not snap or snap.get("status") != "OK":
        return None
    raw = snap.get("normalized_value")
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


def check_input_lineage(
    *,
    snapshot: dict[str, Any],
    registry_path: str,
    plan_path: str,
    bindings_path: str,
    source_html_path: str,
    manifest: dict[str, Any],
    contract: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    actual_source = _sha256_file(source_html_path)
    specs = [
        ("01_lineage_01_registry", _sha256_file(registry_path), contract["job1_registry_sha256"], registry_path),
        ("01_lineage_02_collector_plan", _sha256_file(plan_path), contract["collector_plan_sha256"], plan_path),
        (
            "01_lineage_03_binding_manifest",
            _sha256_file(bindings_path),
            contract["binding_manifest_sha256"],
            bindings_path,
        ),
        (
            "01_lineage_04_source_html_contract",
            actual_source,
            contract["source_html_sha256"],
            source_html_path,
        ),
        (
            "01_lineage_05_snapshot_job1_registry",
            snapshot.get("job1_registry_sha256"),
            contract["job1_registry_sha256"],
            None,
        ),
        (
            "01_lineage_06_snapshot_collector_plan",
            snapshot.get("collector_plan_sha256"),
            contract["collector_plan_sha256"],
            None,
        ),
        (
            "01_lineage_07_manifest_source_actual",
            manifest.get("source_html_sha256"),
            actual_source,
            None,
        ),
        (
            "01_lineage_08_manifest_source_contract",
            manifest.get("source_html_sha256"),
            contract["source_html_sha256"],
            None,
        ),
    ]
    for check_id, actual, expected, path in specs:
        ok = bool(expected) and actual == expected
        checks.append(
            CheckResult(
                check_id=check_id,
                category="01_input_lineage",
                asset=None,
                rule_type="hash_match",
                metric_ids=[],
                status="PASS" if ok else "FAIL",
                assertions_executed=1,
                observed=actual,
                expected_relation=f"sha256 == {expected}",
                evidence={"path": path},
                reason="lineage hash match" if ok else "INPUT_LINEAGE_FAILURE",
            )
        )
    return checks


def check_active_asset_coverage(
    *,
    rendered_html: str,
    contract: dict[str, Any],
) -> list[CheckResult]:
    articles = extract_articles(rendered_html)
    checks: list[CheckResult] = []
    for asset in contract["active_report_assets"]:
        present = asset in articles
        checks.append(
            CheckResult(
                check_id=f"02_asset_{asset}",
                category="02_active_asset_coverage",
                asset=asset,
                rule_type="article_present",
                metric_ids=[],
                status="PASS" if present else "COVERAGE_GAP",
                assertions_executed=1,
                observed=present,
                expected_relation="article exists",
                evidence={"data-asset": asset},
                reason="active asset article present" if present else "missing article",
            )
        )
    for ex in contract["excluded_assets"]:
        checks.append(
            CheckResult(
                check_id=f"02_excluded_{ex}_not_required",
                category="02_active_asset_coverage",
                asset=ex,
                rule_type="excluded_asset",
                metric_ids=[],
                status="NOT_APPLICABLE",
                assertions_executed=1,
                observed=ex in articles,
                expected_relation="excluded from active scope",
                evidence={},
                reason="excluded asset not in active scope",
            )
        )
    return checks


def check_canonical_metric_coverage(
    *,
    snapshot: dict[str, Any],
    bindings: list[dict[str, Any]],
    reg: dict[str, Any],
    contract: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    by_id = {b["metric_id"]: b for b in bindings if b.get("owner") == "CGPT_CURSOR"}
    for mid in contract["bound_metric_ids"]:
        b = by_id.get(mid) or next((x for x in bindings if x.get("metric_id") == mid), {})
        row = reg.get(mid)
        snap = _snap_metric(snapshot, mid)
        gap = row is None or snap is None
        unit_ok = True
        if row and snap:
            ru = (row.get("allowed_unit") or row.get("unit") or "").lower()
            su = (snap.get("unit") or "").lower()
            if ru and su and ru not in su and su not in ru and ru.split("/")[0] != su.split("/")[0]:
                unit_ok = False
        checks.append(
            CheckResult(
                check_id=f"03_metric_{mid.replace('.', '_')}",
                category="03_canonical_metric_coverage",
                asset=b.get("asset"),
                rule_type="canonical_snapshot_registry",
                metric_ids=[mid],
                status="COVERAGE_GAP" if gap else ("FAIL" if not unit_ok else "PASS"),
                assertions_executed=1,
                observed={"registry": row is not None, "snapshot": snap is not None},
                expected_relation="registry + snapshot present",
                evidence={"unit_ok": unit_ok},
                reason="missing canonical coverage" if gap else "canonical coverage ok",
            )
        )
    return checks


def check_binding_consistency(
    *,
    rendered_html: str,
    source_html: str,
    snapshot: dict[str, Any],
    bindings: list[dict[str, Any]],
    reg: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    by_id = {b["binding_id"]: b for b in bindings}
    bind_ids = list((contract or {}).get("surface_by_binding", {}).keys()) or [
        b["binding_id"]
        for b in bindings
        if b.get("owner") == "CGPT_CURSOR" and b["asset"] not in EXCLUDED_ASSETS
    ]
    for bid in sorted(bind_ids):
        b = by_id[bid]
        if b.get("owner") != "CGPT_CURSOR":
            continue
        if b["asset"] in EXCLUDED_ASSETS:
            continue
        if _is_grok(reg, b["metric_id"]):
            continue
        mid = b["metric_id"]
        if _roster_removed(rendered_html, source_html, asset=b.get("asset"), metric_id=mid):
            checks.append(
                _na_roster(
                    f"04_bind_{b['binding_id']}",
                    "04_rendered_binding_consistency",
                    b.get("asset"),
                    mid,
                )
            )
            continue
        snap = _snap_metric(snapshot, mid)
        span, err = locate_binding_span(
            rendered_html,
            b,
            source_html=source_html,
            bindings=bindings,
        )
        if err:
            checks.append(
                CheckResult(
                    check_id=f"04_bind_{b['binding_id']}",
                    category="04_rendered_binding_consistency",
                    asset=b.get("asset"),
                    rule_type="anchor_locate",
                    metric_ids=[mid],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=None,
                    expected_relation="binding locatable",
                    evidence={"error": err},
                    reason=f"binding not locatable: {err}",
                )
            )
            continue
        if snap is None:
            checks.append(
                CheckResult(
                    check_id=f"04_bind_{b['binding_id']}",
                    category="04_rendered_binding_consistency",
                    asset=b.get("asset"),
                    rule_type="snapshot_missing",
                    metric_ids=[mid],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=span,
                    expected_relation="snapshot entry exists",
                    evidence={},
                    reason="missing snapshot metric",
                )
            )
            continue
        status = snap.get("status", "UNKNOWN")
        if status != "OK":
            ok = span.strip().upper() == "UNKNOWN"
            checks.append(
                CheckResult(
                    check_id=f"04_bind_{b['binding_id']}",
                    category="04_rendered_binding_consistency",
                    asset=b.get("asset"),
                    rule_type="fail_closed_unknown",
                    metric_ids=[mid],
                    status="PASS" if ok else "FAIL",
                    assertions_executed=1,
                    observed=span,
                    expected_relation="UNKNOWN when canonical non-OK",
                    evidence={"canonical_status": status},
                    reason="fail-closed UNKNOWN" if ok else "stale numeric on non-OK",
                )
            )
            continue
        fmt = b.get("formatter") or {}
        if fmt.get("type") == "string_exact":
            expected = str(snap.get("normalized_value", ""))
            ok = span.strip() == expected
            checks.append(
                CheckResult(
                    check_id=f"04_bind_{b['binding_id']}",
                    category="04_rendered_binding_consistency",
                    asset=b.get("asset"),
                    rule_type="string_exact",
                    metric_ids=[mid],
                    status="PASS" if ok else "FAIL",
                    assertions_executed=1,
                    observed=span,
                    expected_relation="rendered text == canonical normalized_value",
                    evidence={},
                    reason="string binding ok" if ok else "string mismatch",
                )
            )
            continue
        try:
            canonical = dec(snap.get("normalized_value"))
        except Exception:
            checks.append(
                CheckResult(
                    check_id=f"04_bind_{b['binding_id']}",
                    category="04_rendered_binding_consistency",
                    asset=b.get("asset"),
                    rule_type="non_numeric_canonical",
                    metric_ids=[mid],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=span,
                    expected_relation="numeric canonical",
                    evidence={},
                    reason="canonical not numeric",
                )
            )
            continue
        fmt = _fmt_for_metric(mid, fmt, canonical)
        parse_can = abs(canonical) if is_etf_flow_metric(mid) else canonical
        observed = parse_binding_observed(span, fmt, canonical=parse_can)
        observed = _signed_etf_obs(mid, observed, canonical)
        ok = values_compatible(observed, canonical, fmt)
        checks.append(
            CheckResult(
                check_id=f"04_bind_{b['binding_id']}",
                category="04_rendered_binding_consistency",
                asset=b.get("asset"),
                rule_type="numeric_render",
                metric_ids=[mid],
                status="PASS" if ok else "FAIL",
                assertions_executed=1,
                observed=str(observed) if observed is not None else span,
                expected_relation=f"numeric == {canonical}",
                evidence={"tolerance": str(display_tolerance(fmt))},
                reason="numeric binding ok" if ok else "numeric mismatch",
            )
        )
    return checks


def check_duplicate_consistency(
    *,
    rendered_html: str,
    source_html: str,
    snapshot: dict[str, Any],
    bindings: list[dict[str, Any]],
    reg: dict[str, Any],
    contract: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    by_id = {b["binding_id"]: b for b in bindings}
    for mid, binding_ids in sorted(contract.get("duplicate_metric_groups", {}).items()):
        if _is_grok(reg, mid):
            continue
        if _roster_removed(rendered_html, source_html, metric_id=mid):
            checks.append(
                _na_roster(
                    f"05_dup_{mid.replace('.', '_')}",
                    "05_duplicate_consistency",
                    None,
                    mid,
                )
            )
            continue
        snap = _snap_metric(snapshot, mid)
        if snap is None:
            checks.append(
                CheckResult(
                    check_id=f"05_dup_{mid.replace('.', '_')}",
                    category="05_duplicate_consistency",
                    asset=None,
                    rule_type="duplicate_group",
                    metric_ids=[mid],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=None,
                    expected_relation="all duplicates agree",
                    evidence={"binding_ids": binding_ids},
                    reason="missing snapshot for duplicate group",
                )
            )
            continue
        if snap.get("status") != "OK":
            checks.append(
                CheckResult(
                    check_id=f"05_dup_{mid.replace('.', '_')}",
                    category="05_duplicate_consistency",
                    asset=None,
                    rule_type="duplicate_group",
                    metric_ids=[mid],
                    status="BLOCKED_UNKNOWN",
                    assertions_executed=1,
                    observed=snap.get("status"),
                    expected_relation="canonical non-OK",
                    evidence={"binding_ids": binding_ids},
                    reason="canonical non-OK duplicate group",
                )
            )
            continue
        raw = snap.get("normalized_value")
        canonical_dec: Decimal | None = None
        try:
            canonical_dec = dec(raw)
        except Exception:
            canonical_dec = None
        if canonical_dec is None:
            values = []
            fail = False
            for bid in binding_ids:
                b = by_id[bid]
                span, err = locate_binding_span(
                    rendered_html, b, source_html=source_html, bindings=bindings
                )
                if err or span is None:
                    fail = True
                    values.append((bid, err or "missing"))
                    continue
                if span.strip() != raw.strip():
                    fail = True
                values.append((bid, span))
            checks.append(
                CheckResult(
                    check_id=f"05_dup_{mid.replace('.', '_')}",
                    category="05_duplicate_consistency",
                    asset=by_id[binding_ids[0]].get("asset") if binding_ids else None,
                    rule_type="duplicate_group_string",
                    metric_ids=[mid],
                    status="FAIL" if fail else "PASS",
                    assertions_executed=max(1, len(binding_ids)),
                    observed=values,
                    expected_relation="all string duplicates agree",
                    evidence={"binding_ids": binding_ids},
                    reason="duplicate consistency ok" if not fail else "duplicate mismatch",
                )
            )
            continue
        canonical = canonical_dec if canonical_dec is not None else dec(raw)
        values: list[tuple[str, str]] = []
        fail = False
        for bid in binding_ids:
            b = by_id[bid]
            span, err = locate_binding_span(
                rendered_html,
                b,
                source_html=source_html,
                bindings=bindings,
            )
            if err or span is None:
                fail = True
                values.append((bid, err or "missing"))
                continue
            fmt = _fmt_for_metric(mid, b.get("formatter") or {}, canonical)
            if fmt.get("type") == "numeric":
                parse_can = abs(canonical) if is_etf_flow_metric(mid) else canonical
                obs = parse_binding_observed(span, fmt, canonical=parse_can)
                obs = _signed_etf_obs(mid, obs, canonical)
                ok = values_compatible(obs, canonical, fmt)
            else:
                obs = parse_binding_observed(span, None, canonical=canonical)
                ok = values_compatible(obs, canonical, inferred_numeric_formatter(span))
            if not ok:
                fail = True
            values.append((bid, span))
        checks.append(
            CheckResult(
                check_id=f"05_dup_{mid.replace('.', '_')}",
                category="05_duplicate_consistency",
                asset=by_id[binding_ids[0]].get("asset") if binding_ids else None,
                rule_type="duplicate_group",
                metric_ids=[mid],
                status="FAIL" if fail else "PASS",
                assertions_executed=max(1, len(binding_ids)),
                observed=values,
                expected_relation="all occurrences match canonical",
                evidence={"binding_ids": binding_ids},
                reason="duplicate consistency ok" if not fail else "duplicate mismatch",
            )
        )
    return checks


def check_ath_drawdown(
    *,
    snapshot: dict[str, Any],
    rendered_html: str,
    contract: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for rule in contract.get("ath_drawdown_rules", []):
        price = _snap_metric(snapshot, rule["price_metric_id"])
        ath = _snap_metric(snapshot, rule["ath_metric_id"])
        dd = _snap_metric(snapshot, rule["drawdown_metric_id"])
        asset = rule["asset"]
        if not price or not ath or not dd:
            checks.append(
                CheckResult(
                    check_id=f"06_ath_{asset}",
                    category="06_ath_drawdown_arithmetic",
                    asset=asset,
                    rule_type="ath_inputs",
                    metric_ids=[
                        rule["price_metric_id"],
                        rule["ath_metric_id"],
                        rule["drawdown_metric_id"],
                    ],
                    status="NOT_APPLICABLE",
                    assertions_executed=1,
                    observed=None,
                    expected_relation="inputs present",
                    evidence={},
                    reason="ath metrics not in snapshot scope",
                )
            )
            continue
        if any(
            m.get("status") != "OK"
            for m in (price, ath, dd)
        ):
            checks.append(
                CheckResult(
                    check_id=f"06_ath_{asset}",
                    category="06_ath_drawdown_arithmetic",
                    asset=asset,
                    rule_type="ath_blocked",
                    metric_ids=[rule["drawdown_metric_id"]],
                    status="BLOCKED_UNKNOWN",
                    assertions_executed=1,
                    observed=[m.get("status") for m in (price, ath, dd)],
                    expected_relation="non-OK canonical",
                    evidence={},
                    reason="ath inputs non-OK",
                )
            )
            continue
        calc = drawdown_pct(dec(price["normalized_value"]), dec(ath["normalized_value"]))
        canonical_dd = dec(dd["normalized_value"])
        tol = Decimal("0.5")
        ok = calc is not None and abs(calc - canonical_dd) <= tol
        art = extract_articles(rendered_html).get(asset, "")
        bar = extract_visual_bar_width(art)
        bar_ok = True
        if bar is not None and calc is not None:
            bar_ok = abs(Decimal(bar) - abs(calc)) <= Decimal("1")
        checks.append(
            CheckResult(
                check_id=f"06_ath_{asset}",
                category="06_ath_drawdown_arithmetic",
                asset=asset,
                rule_type="ath_arithmetic",
                metric_ids=[rule["drawdown_metric_id"]],
                status="PASS" if ok and bar_ok else "FAIL",
                assertions_executed=2 if bar is not None else 1,
                observed={"calc_dd": str(calc), "canonical_dd": str(canonical_dd), "bar": bar},
                expected_relation="drawdown = (price/ath-1)*100",
                evidence={"bar_ok": bar_ok},
                reason="ath arithmetic ok" if ok and bar_ok else "ath arithmetic mismatch",
            )
        )
    return checks


def _article_ma_text(article_html: str) -> str:
    headline = extract_stance_headline(article_html) or ""
    m = re.search(r'<p class="alt-stance-expl">(.*?)</p>', article_html, re.S)
    expl = re.sub(r"<[^>]+>", " ", m.group(1)) if m else ""
    return f"{headline} {expl}"


def _parse_ma_from_text(text: str) -> dict[str, str]:
    if not text:
        return {}
    up = text.upper()
    low = text.lower()
    claim: dict[str, str] = {}
    if "ABOVE 50D + 200D" in up or "above 50d and 200d" in low:
        claim["ma50"] = "ABOVE"
        claim["ma200"] = "ABOVE"
    if "BELOW 50D + 200D" in up or "below 50d and 200d" in low:
        claim["ma50"] = "BELOW"
        claim["ma200"] = "BELOW"
    if "above 50d but below 200d" in low:
        claim["ma50"] = "ABOVE"
        claim["ma200"] = "BELOW"
    if re.search(r"ABOVE\s+50D", up) or re.search(r"above\s+50d", low):
        if "ma50" not in claim:
            claim["ma50"] = "ABOVE"
    if re.search(r"BELOW\s+50D", up) or re.search(r"below\s+50d", low):
        claim["ma50"] = "BELOW"
    if re.search(r"ABOVE\s+200D", up) or re.search(r"above\s+200d", low):
        if "ma200" not in claim:
            claim["ma200"] = "ABOVE"
    if re.search(r"BELOW\s+200D", up) or re.search(r"below\s+200d", low):
        claim["ma200"] = "BELOW"
    if "BELOW 50D + 200D" in up:
        claim["ma50"] = "BELOW"
        claim["ma200"] = "BELOW"
    return claim


def _ma_langs_from_html(rendered_html: str, asset: str, claim: dict[str, Any]) -> tuple[str | None, str | None]:
    art = extract_articles(rendered_html).get(asset, "")
    parsed = _parse_ma_from_text(_article_ma_text(art))
    ma50 = parsed.get("ma50") or claim.get("ma50_language")
    ma200 = parsed.get("ma200") or claim.get("ma200_language")
    return ma50, ma200


def _rs_language_from_html(rendered_html: str, claim: dict[str, Any]) -> str | None:
    asset = claim.get("asset") or ""
    art = extract_articles(rendered_html).get(asset, "")
    if not art:
        return None
    up = re.sub(r"<[^>]+>", " ", art).upper()
    window = (claim.get("window") or "").upper()
    if not window:
        window = "30D" if ".30d" in claim.get("metric_id", "") else "7D"
    mid = claim.get("metric_id", "")
    vs = "BTC" if "vs_btc" in mid else "SOL" if "vs_sol" in mid else None
    if vs:
        mixed = re.search(rf"(LEADS|LAGS)\s+{vs}\s+7D\s*[·.]\s*(LEADS|LAGS)\s+30D", up)
        if mixed:
            return mixed.group(1) if window == "7D" else mixed.group(2)
        both = re.search(rf"(LEADS|LAGS)\s+{vs}\s+7D/30D", up)
        if both:
            return both.group(1)
    mixed_h = re.search(r"(LEADS|LAGS)\s+7D\s*[·.]\s*(LEADS|LAGS)\s+30D", up)
    if mixed_h:
        return mixed_h.group(1) if window == "7D" else mixed_h.group(2)
    return None


def check_ma_language(
    *,
    snapshot: dict[str, Any],
    contract: dict[str, Any],
    rendered_html: str = "",
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for claim in contract.get("ma_language_claims", []):
        price = _snap_metric(snapshot, claim["price_metric_id"])
        ma50 = _snap_metric(snapshot, claim["ma50_metric_id"]) if claim.get("ma50_metric_id") else None
        ma200 = _snap_metric(snapshot, claim["ma200_metric_id"]) if claim.get("ma200_metric_id") else None
        asset = claim["asset"]
        if not price or (claim.get("ma50_language") and not ma50) or (claim.get("ma200_language") and not ma200):
            checks.append(
                CheckResult(
                    check_id=f"07_ma_{claim['claim_id'].replace('::', '_')}",
                    category="07_moving_average_language",
                    asset=asset,
                    rule_type="ma_inputs",
                    metric_ids=[claim["price_metric_id"]],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=None,
                    expected_relation="price + MA metrics present",
                    evidence=claim,
                    reason="missing MA inputs",
                )
            )
            continue
        if price.get("status") != "OK":
            checks.append(
                CheckResult(
                    check_id=f"07_ma_{claim['claim_id'].replace('::', '_')}",
                    category="07_moving_average_language",
                    asset=asset,
                    rule_type="ma_blocked",
                    metric_ids=[claim["price_metric_id"]],
                    status="BLOCKED_UNKNOWN",
                    assertions_executed=1,
                    observed=price.get("status"),
                    expected_relation="non-OK price",
                    evidence=claim,
                    reason="price non-OK",
                )
            )
            continue
        p = dec(price["normalized_value"])
        ok = True
        assertions = 0
        ma50_lang, ma200_lang = _ma_langs_from_html(rendered_html, asset, claim)
        if ma50_lang and ma50 and ma50.get("status") == "OK":
            m50 = dec(ma50["normalized_value"])
            assertions += 1
            if ma50_lang == "ABOVE" and not (p > m50):
                ok = False
            if ma50_lang == "BELOW" and not (p < m50):
                ok = False
        if ma200_lang and ma200 and ma200.get("status") == "OK":
            m200 = dec(ma200["normalized_value"])
            assertions += 1
            if ma200_lang == "ABOVE" and not (p > m200):
                ok = False
            if ma200_lang == "BELOW" and not (p < m200):
                ok = False
        if assertions == 0:
            st = "COVERAGE_GAP"
        elif ok:
            st = "PASS"
        else:
            st = "FAIL"
        checks.append(
            CheckResult(
                check_id=f"07_ma_{claim['claim_id'].replace('::', '_')}",
                category="07_moving_average_language",
                asset=asset,
                rule_type="ma_language",
                metric_ids=[claim["price_metric_id"]],
                status=st,
                assertions_executed=max(1, assertions),
                observed={"price": str(p), "ma50_lang": ma50_lang, "ma200_lang": ma200_lang},
                expected_relation="language matches price vs MA",
                evidence=claim,
                reason="MA language ok" if ok else "MA language contradiction",
            )
        )
    return checks


def check_rs_language(
    *,
    snapshot: dict[str, Any],
    contract: dict[str, Any],
    rendered_html: str = "",
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for claim in contract.get("rs_language_claims", []):
        mid = claim["metric_id"]
        rec = _snap_metric(snapshot, mid)
        asset = claim["asset"]
        if not rec:
            checks.append(
                CheckResult(
                    check_id=f"08_rs_{claim['claim_id'].replace('::', '_')}",
                    category="08_relative_strength_language",
                    asset=asset,
                    rule_type="rs_inputs",
                    metric_ids=[mid],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=None,
                    expected_relation="RS metric present",
                    evidence=claim,
                    reason="missing RS metric",
                )
            )
            continue
        if rec.get("status") != "OK":
            checks.append(
                CheckResult(
                    check_id=f"08_rs_{claim['claim_id'].replace('::', '_')}",
                    category="08_relative_strength_language",
                    asset=asset,
                    rule_type="rs_blocked",
                    metric_ids=[mid],
                    status="BLOCKED_UNKNOWN",
                    assertions_executed=1,
                    observed=rec.get("status"),
                    expected_relation="non-OK RS",
                    evidence=claim,
                    reason="RS non-OK",
                )
            )
            continue
        rs = dec(rec["normalized_value"])
        lang = _rs_language_from_html(rendered_html, claim) or claim["language"]
        ok = (lang == "LEADS" and rs > 0) or (lang == "LAGS" and rs < 0)
        checks.append(
            CheckResult(
                check_id=f"08_rs_{claim['claim_id'].replace('::', '_')}",
                category="08_relative_strength_language",
                asset=asset,
                rule_type="rs_language",
                metric_ids=[mid],
                status="PASS" if ok else "FAIL",
                assertions_executed=1,
                observed={"rs": str(rs), "language": lang},
                expected_relation="RS sign matches LEADS/LAGS",
                evidence=claim,
                reason="RS language ok" if ok else "RS language contradiction",
            )
        )
    return checks


def check_freshness(
    *,
    rendered_html: str,
    source_html: str,
    snapshot: dict[str, Any],
    bindings: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for mid in contract.get("freshness_metric_ids", []):
        if _roster_removed(rendered_html, source_html, metric_id=mid):
            checks.append(
                _na_roster(
                    f"09_fresh_{mid.replace('.', '_')}",
                    "09_freshness_asof_consistency",
                    None,
                    mid,
                )
            )
            continue
        snap = _snap_metric(snapshot, mid)
        if not snap:
            checks.append(
                CheckResult(
                    check_id=f"09_fresh_{mid.replace('.', '_')}",
                    category="09_freshness_asof_consistency",
                    asset=None,
                    rule_type="freshness_metric",
                    metric_ids=[mid],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=None,
                    expected_relation="snapshot present",
                    evidence={},
                    reason="missing freshness metric",
                )
            )
            continue
        fresh = (snap.get("freshness") or "UNKNOWN").upper()
        as_of = snap.get("source_as_of", "UNKNOWN")
        related = [b for b in bindings if b["metric_id"] == mid]
        stale_claim = False
        for b in related:
            span, err = locate_binding_span(
                rendered_html, b, source_html=source_html, bindings=bindings
            )
            if not span:
                continue
            pos = rendered_html.find(span)
            ctx = (
                rendered_html[max(0, pos - 200) : pos + len(span) + 200].lower()
                if pos >= 0
                else (b.get("anchor_before", "") + span + b.get("anchor_after", "")).lower()
            )
            if fresh == "UNKNOWN" and any(
                tok in ctx for tok in ("freshness · same-day", "fresh today", "freshness · fresh")
            ):
                stale_claim = True
            if as_of != "UNKNOWN" and "as of" in ctx.lower():
                if as_of not in ctx and as_of[:10] not in ctx:
                    stale_claim = True
        status = "FAIL" if stale_claim else (
            "BLOCKED_UNKNOWN" if snap.get("status") in NON_OK_STATUSES else "PASS"
        )
        checks.append(
            CheckResult(
                check_id=f"09_fresh_{mid.replace('.', '_')}",
                category="09_freshness_asof_consistency",
                asset=related[0]["asset"] if related else None,
                rule_type="freshness_asof",
                metric_ids=[mid],
                status=status,
                assertions_executed=1,
                observed={"freshness": fresh, "source_as_of": as_of},
                expected_relation="UI freshness matches canonical",
                evidence={"stale_claim": stale_claim},
                reason="freshness ok" if not stale_claim else "stale masquerading as fresh",
            )
        )
    if not contract.get("freshness_metric_ids"):
        checks.append(
            CheckResult(
                check_id="09_fresh_scope_na",
                category="09_freshness_asof_consistency",
                asset=None,
                rule_type="freshness_scope",
                metric_ids=[],
                status="NOT_APPLICABLE",
                assertions_executed=1,
                observed=0,
                expected_relation="no freshness-bound metrics in contract",
                evidence={},
                reason="no freshness bindings discovered",
            )
        )
    return checks


def _span_value_ok(span: str, binding: dict[str, Any], snap: dict[str, Any]) -> bool:
    fmt = binding.get("formatter") or {}
    if fmt.get("type") == "string_exact":
        expected = str(snap.get("normalized_value", ""))
        return span.strip() == expected
    try:
        canonical = dec(snap["normalized_value"])
    except Exception:
        return False
    fmt = _fmt_for_metric(binding["metric_id"], fmt, canonical)
    parse_can = abs(canonical) if is_etf_flow_metric(binding["metric_id"]) else canonical
    observed = parse_binding_observed(span, fmt, canonical=parse_can)
    observed = _signed_etf_obs(binding["metric_id"], observed, canonical)
    return values_compatible(observed, canonical, fmt)


def check_surface_agreement(
    *,
    rendered_html: str,
    source_html: str,
    snapshot: dict[str, Any],
    bindings: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    by_metric: dict[str, list[dict[str, Any]]] = {}
    for b in bindings:
        if b.get("owner") != "CGPT_CURSOR":
            continue
        by_metric.setdefault(b["metric_id"], []).append(b)
    for mid in contract.get("surface_metric_ids", []):
        if _roster_removed(rendered_html, source_html, metric_id=mid):
            checks.append(
                _na_roster(
                    f"10_surface_{mid.replace('.', '_')}",
                    "10_tooltip_visible_visual_agreement",
                    None,
                    mid,
                )
            )
            continue
        group = by_metric.get(mid, [])
        snap = _snap_metric(snapshot, mid)
        if not group:
            checks.append(
                CheckResult(
                    check_id=f"10_surface_{mid.replace('.', '_')}",
                    category="10_tooltip_visible_visual_agreement",
                    asset=None,
                    rule_type="multi_surface_agreement",
                    metric_ids=[mid],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=None,
                    expected_relation="surfaces agree",
                    evidence={},
                    reason="surface metric has no bindings",
                )
            )
            continue
        if not snap or snap.get("status") != "OK":
            checks.append(
                CheckResult(
                    check_id=f"10_surface_{mid.replace('.', '_')}",
                    category="10_tooltip_visible_visual_agreement",
                    asset=group[0].get("asset"),
                    rule_type="multi_surface_agreement",
                    metric_ids=[mid],
                    status="BLOCKED_UNKNOWN" if snap else "COVERAGE_GAP",
                    assertions_executed=1,
                    observed=None if not snap else snap.get("status"),
                    expected_relation="surfaces agree",
                    evidence={"surfaces": sorted({classify_surface(b) for b in group})},
                    reason="surface canonical non-OK or missing",
                )
            )
            continue
        vals: list[tuple[str, str]] = []
        fail = False
        for b in group:
            span, err = locate_binding_span(
                rendered_html,
                b,
                source_html=source_html,
                bindings=bindings,
            )
            if err or span is None:
                fail = True
                continue
            if not _span_value_ok(span, b, snap):
                fail = True
            vals.append((classify_surface(b), span))
        checks.append(
            CheckResult(
                check_id=f"10_surface_{mid.replace('.', '_')}",
                category="10_tooltip_visible_visual_agreement",
                asset=group[0].get("asset"),
                rule_type="multi_surface_agreement",
                metric_ids=[mid],
                status="FAIL" if fail else "PASS",
                assertions_executed=max(1, len(group)),
                observed=vals,
                expected_relation="surfaces agree",
                evidence={"surfaces": sorted({classify_surface(b) for b in group})},
                reason="surface agreement ok" if not fail else "surface mismatch",
            )
        )
    return checks


def check_derived_metrics(
    *,
    snapshot: dict[str, Any],
    contract: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for rule in contract.get("derive_rules", []):
        mid = rule["metric_id"]
        snap = _snap_metric(snapshot, mid)
        inputs = rule["inputs"]
        input_recs = [_snap_metric(snapshot, i) for i in inputs]
        if snap is None:
            checks.append(
                CheckResult(
                    check_id=f"11_derive_{mid.replace('.', '_')}",
                    category="11_derived_metric_arithmetic",
                    asset=None,
                    rule_type="derive_snapshot",
                    metric_ids=[mid],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=None,
                    expected_relation="derived metric in snapshot",
                    evidence={"inputs": inputs},
                    reason="missing derived metric",
                )
            )
            continue
        if any(r is None for r in input_recs):
            checks.append(
                CheckResult(
                    check_id=f"11_derive_{mid.replace('.', '_')}",
                    category="11_derived_metric_arithmetic",
                    asset=None,
                    rule_type="derive_inputs_missing",
                    metric_ids=[mid] + inputs,
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=[r is not None for r in input_recs],
                    expected_relation="derivation inputs present",
                    evidence={"inputs": inputs},
                    reason="missing derivation input",
                )
            )
            continue
        if any(r.get("status") != "OK" for r in input_recs if r):
            checks.append(
                CheckResult(
                    check_id=f"11_derive_{mid.replace('.', '_')}",
                    category="11_derived_metric_arithmetic",
                    asset=None,
                    rule_type="derive_inputs_non_ok",
                    metric_ids=[mid],
                    status="BLOCKED_UNKNOWN",
                    assertions_executed=1,
                    observed=[r.get("status") for r in input_recs],
                    expected_relation="inputs non-OK",
                    evidence={},
                    reason="derivation inputs non-OK",
                )
            )
            continue
        if snap.get("status") != "OK":
            checks.append(
                CheckResult(
                    check_id=f"11_derive_{mid.replace('.', '_')}",
                    category="11_derived_metric_arithmetic",
                    asset=None,
                    rule_type="derive_non_ok",
                    metric_ids=[mid],
                    status="BLOCKED_UNKNOWN",
                    assertions_executed=1,
                    observed=snap.get("status"),
                    expected_relation="derived non-OK",
                    evidence={},
                    reason="derived metric non-OK",
                )
            )
            continue
        op = rule["op"]
        vals = [dec(r["normalized_value"]) for r in input_recs if r]
        if op == "RATIO":
            calc = derive_ratio(vals[0], vals[1])
        elif op == "SUBTRACT":
            calc = derive_subtract(vals[0], vals[1])
        else:
            calc = None
        canonical = dec(snap["normalized_value"])
        ok = calc is not None and abs(calc - canonical) <= max(Decimal("0.0001"), abs(canonical) * Decimal("0.0001"))
        checks.append(
            CheckResult(
                check_id=f"11_derive_{mid.replace('.', '_')}",
                category="11_derived_metric_arithmetic",
                asset=None,
                rule_type="derive_arithmetic",
                metric_ids=[mid],
                status="PASS" if ok else "FAIL",
                assertions_executed=1,
                observed={"calc": str(calc), "canonical": str(canonical)},
                expected_relation=f"{op}({', '.join(inputs)})",
                evidence={"op": op, "inputs": inputs},
                reason="derive ok" if ok else "derive mismatch",
            )
        )
    return checks


def _identify_grok_wallet_occurrences(rendered_html: str) -> list[dict[str, Any]]:
    """GROK-owned wallet-lane values in #siren-watch-data. Not non-wallet report metrics."""
    hits: list[dict[str, Any]] = []
    m = re.search(
        r'<script[^>]*id="siren-watch-data"[^>]*>(.*?)</script>',
        rendered_html,
        re.S,
    )
    if not m:
        return hits
    try:
        import json as _json

        data = _json.loads(m.group(1))
    except Exception:
        return [{"owner": "GROK", "source": "siren-watch-data", "parse": "invalid"}]
    pump = (data.get("PUMP") or {}).get("wallets") or []
    for w in pump:
        hits.append(
            {
                "owner": "GROK",
                "source": "siren-watch-data",
                "wallet": w.get("wallet"),
                "sent": w.get("sent"),
                "excluded_from": "pump.buyback.usd.7d",
            }
        )
    return hits


def check_permanent_regressions(
    *,
    rendered_html: str,
    source_html: str,
    snapshot: dict[str, Any],
    bindings: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    by_id = {b["binding_id"]: b for b in bindings}
    spx = contract.get("permanent_regressions", {}).get("spx_price_duplicate", {})
    spx_ids = spx.get("binding_ids", [])
    if spx_ids:
        mid = spx["metric_id"]
        snap = _snap_metric(snapshot, mid)
        vals = []
        fail = False
        if snap and snap.get("status") == "OK":
            canonical = dec(snap["normalized_value"])
            for bid in spx_ids:
                b = by_id[bid]
                exp = snap.get("normalized_value")
                span, err = locate_binding_span(
                    rendered_html,
                    b,
                    source_html=source_html,
                    bindings=bindings,
                )
                if err:
                    fail = True
                    continue
                obs = parse_binding_observed(span or "", b.get("formatter"), canonical=canonical)
                if not values_compatible(obs, canonical, b.get("formatter")):
                    fail = True
                vals.append((bid, span))
        checks.append(
            CheckResult(
                check_id="12_reg_spx_price_duplicate",
                category="12_permanent_regressions",
                asset="spx6900",
                rule_type="spx_duplicate",
                metric_ids=[mid],
                status="FAIL" if fail else "PASS",
                assertions_executed=max(1, len(spx_ids)),
                observed=vals,
                expected_relation="all spx.price.usd.live occurrences agree",
                evidence={"binding_ids": spx_ids},
                reason="SPX duplicate ok" if not fail else "SPX duplicate mismatch",
            )
        )
    pump = contract.get("permanent_regressions", {}).get("pump_buyback_duplicate", {})
    pump_ids = [b for b in pump.get("binding_ids", []) if by_id.get(b, {}).get("owner") == "CGPT_CURSOR"]
    if pump_ids:
        mid = pump["metric_id"]
        snap = _snap_metric(snapshot, mid)
        vals = []
        fail = False
        if snap and snap.get("status") == "OK":
            canonical = dec(snap["normalized_value"])
            for bid in pump_ids:
                b = by_id[bid]
                exp = snap.get("normalized_value")
                span, err = locate_binding_span(
                    rendered_html,
                    b,
                    source_html=source_html,
                    bindings=bindings,
                )
                if err:
                    fail = True
                    continue
                obs = parse_binding_observed(span or "", b.get("formatter"), canonical=canonical)
                if not values_compatible(obs, canonical, b.get("formatter")):
                    fail = True
                vals.append((bid, span))
        checks.append(
            CheckResult(
                check_id="12_reg_pump_buyback_duplicate",
                category="12_permanent_regressions",
                asset="pump",
                rule_type="pump_buyback_duplicate",
                metric_ids=[mid],
                status="FAIL" if fail else "PASS",
                assertions_executed=max(1, len(pump_ids)),
                observed=vals,
                expected_relation="non-wallet pump.buyback.usd.7d agree",
                evidence={"binding_ids": pump_ids},
                reason="PUMP buyback ok" if not fail else "PUMP buyback duplicate mismatch",
            )
        )
        wallet_hits = _identify_grok_wallet_occurrences(rendered_html)
        grok_bindings = [b for b in bindings if b.get("owner") == "GROK"]
        grok_buyback = [b["binding_id"] for b in grok_bindings if b.get("metric_id") == mid]
        excluded = grok_buyback == []
        identified = bool(wallet_hits)
        nonwallet_unchanged = not fail
        wallet_ok = identified and excluded and nonwallet_unchanged
        checks.append(
            CheckResult(
                check_id="12_reg_pump_wallet_invariance",
                category="12_permanent_regressions",
                asset="pump",
                rule_type="wallet_lane_exclusion",
                metric_ids=[mid],
                status="PASS" if wallet_ok else "FAIL",
                assertions_executed=max(1, len(wallet_hits) + 1),
                observed={
                    "wallet_hits": wallet_hits[:8],
                    "grok_buyback_bindings": grok_buyback,
                    "nonwallet_binding_ids": pump_ids,
                },
                expected_relation="GROK wallet values excluded from pump.buyback.usd.7d",
                evidence={
                    "wallet_occurrence_identified_as_grok_owned": bool(wallet_hits) or bool(grok_bindings),
                    "wallet_occurrence_excluded_from_nonwallet_comparison": excluded,
                    "non_wallet_binding_set_unchanged": nonwallet_unchanged,
                    "note": pump.get("wallet_lane_exclusion"),
                },
                reason="wallet lane excluded from pump.buyback.usd.7d checks"
                if wallet_ok
                else "wallet invariance failed",
            )
        )
    return checks


def run_all_checks(
    *,
    snapshot: dict[str, Any],
    rendered_html: str,
    source_html: str,
    bindings: list[dict[str, Any]],
    reg: dict[str, Any],
    contract: dict[str, Any],
    registry_path: str,
    plan_path: str,
    bindings_path: str,
    source_html_path: str,
    manifest: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(
        check_input_lineage(
            snapshot=snapshot,
            registry_path=registry_path,
            plan_path=plan_path,
            bindings_path=bindings_path,
            source_html_path=source_html_path,
            manifest=manifest,
            contract=contract,
        )
    )
    checks.extend(check_active_asset_coverage(rendered_html=rendered_html, contract=contract))
    checks.extend(
        check_canonical_metric_coverage(
            snapshot=snapshot, bindings=bindings, reg=reg, contract=contract
        )
    )
    checks.extend(
        check_binding_consistency(
            rendered_html=rendered_html,
            source_html=source_html,
            snapshot=snapshot,
            bindings=bindings,
            reg=reg,
            contract=contract,
        )
    )
    checks.extend(
        check_duplicate_consistency(
            rendered_html=rendered_html,
            source_html=source_html,
            snapshot=snapshot,
            bindings=bindings,
            reg=reg,
            contract=contract,
        )
    )
    checks.extend(check_ath_drawdown(snapshot=snapshot, rendered_html=rendered_html, contract=contract))
    checks.extend(check_ma_language(snapshot=snapshot, contract=contract, rendered_html=rendered_html))
    checks.extend(check_rs_language(snapshot=snapshot, contract=contract, rendered_html=rendered_html))
    checks.extend(
        check_freshness(
            rendered_html=rendered_html,
            source_html=source_html,
            snapshot=snapshot,
            bindings=bindings,
            contract=contract,
        )
    )
    checks.extend(
        check_surface_agreement(
            rendered_html=rendered_html,
            source_html=source_html,
            snapshot=snapshot,
            bindings=bindings,
            contract=contract,
        )
    )
    checks.extend(check_derived_metrics(snapshot=snapshot, contract=contract))
    checks.extend(
        check_permanent_regressions(
            rendered_html=rendered_html,
            source_html=source_html,
            snapshot=snapshot,
            bindings=bindings,
            contract=contract,
        )
    )
    present = {c.category for c in checks}
    for cat in REQUIRED_CATEGORIES:
        if cat not in present:
            checks.append(
                CheckResult(
                    check_id=f"00_missing_{cat}",
                    category=cat,
                    asset=None,
                    rule_type="category_presence",
                    metric_ids=[],
                    status="COVERAGE_GAP",
                    assertions_executed=1,
                    observed=False,
                    expected_relation="category executed",
                    evidence={},
                    reason=f"missing category {cat}",
                )
            )
    return checks
