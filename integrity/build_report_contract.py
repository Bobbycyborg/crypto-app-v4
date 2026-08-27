#!/usr/bin/env python3
"""Deterministic report-contract builder — stdlib only."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrity.extract import classify_surface, extract_articles, extract_stance_headline
from integrity.model import (
    ACTIVE_REPORT_ASSETS,
    ASSET_METRIC_PREFIX,
    CONTRACT_SCHEMA_VERSION,
    EXCLUDED_ASSETS,
    REQUIRED_CATEGORIES,
)

DUPLICATE_FOCUS_SUFFIXES = (
    ".price.usd.live",
    ".price.usd.report",
    ".return.pct.",
    ".liquidity.",
    ".buyback.",
    ".revenue.",
    ".fees.",
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _metric_prefix(asset: str) -> str:
    return ASSET_METRIC_PREFIX.get(asset, asset)


def _parse_ma_claim(text: str) -> dict[str, str] | None:
    if not text:
        return None
    up = text.upper()
    low = text.lower()
    if "50D" not in up and "200D" not in up and "50d" not in low:
        return None
    claim: dict[str, str] = {}
    if "ABOVE 50D + 200D" in up or "above 50d and 200d" in low:
        claim["ma50"] = "ABOVE"
        claim["ma200"] = "ABOVE"
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
    return claim or None


def _article_ma_text(article_html: str) -> str:
    headline = extract_stance_headline(article_html) or ""
    m = re.search(r'<p class="alt-stance-expl">(.*?)</p>', article_html, re.S)
    expl = re.sub(r"<[^>]+>", " ", m.group(1)) if m else ""
    return f"{headline} {expl}"


def _parse_rs_claim(headline: str, binding: dict[str, Any]) -> dict[str, Any] | None:
    ctx = headline or ""
    mid = binding["metric_id"]
    if ".rs." not in mid:
        return None
    up = ctx.upper()
    language = None
    if "LEADS" in up and "LAGS" not in up.split("LEADS")[0][-10:]:
        language = "LEADS"
    elif "LAGS" in up:
        language = "LAGS"
    if language is None:
        anchor = (binding.get("anchor_before", "") + binding.get("anchor_after", "")).upper()
        if "LEADS" in anchor:
            language = "LEADS"
        elif "LAGS" in anchor:
            language = "LAGS"
    if language is None:
        return None
    window = "30d" if ".30d" in mid or ".30d" in mid else "7d"
    if ".30d" in mid:
        window = "30d"
    elif ".7d" in mid:
        window = "7d"
    return {
        "claim_id": f"{binding['binding_id']}::rs_language",
        "asset": binding["asset"],
        "metric_id": mid,
        "binding_id": binding["binding_id"],
        "language": language,
        "window": window,
        "location": "stance_or_binding_context",
    }


def _discover_ma_claims(source_html: str, reg: dict[str, Any]) -> list[dict[str, Any]]:
    articles = extract_articles(source_html)
    claims: list[dict[str, Any]] = []
    for asset in ACTIVE_REPORT_ASSETS:
        art = articles.get(asset, "")
        text = _article_ma_text(art)
        parsed = _parse_ma_claim(text)
        if not parsed:
            continue
        prefix = _metric_prefix(asset)
        price_mid = f"{prefix}.price.usd.live"
        ma50_mid = f"{prefix}.ma.usd.50d"
        ma200_mid = f"{prefix}.ma.usd.200d"
        missing = [
            m
            for m in (price_mid, ma50_mid, ma200_mid)
            if m not in reg and not any(k.startswith(prefix) for k in reg)
        ]
        if price_mid not in reg:
            alt = f"{prefix}.price.usd.report"
            if alt in reg:
                price_mid = alt
        if ma50_mid not in reg or ma200_mid not in reg:
            continue
        claims.append(
            {
                "claim_id": f"{asset}::ma_language::stance_headline",
                "asset": asset,
                "location": "alt-stance-headline",
                "price_metric_id": price_mid,
                "ma50_metric_id": ma50_mid if "ma50" in parsed else None,
                "ma200_metric_id": ma200_mid if "ma200" in parsed else None,
                "ma50_language": parsed.get("ma50"),
                "ma200_language": parsed.get("ma200"),
            }
        )
    return claims


def _discover_rs_claims(
    bindings: list[dict[str, Any]],
    source_html: str,
) -> list[dict[str, Any]]:
    articles = extract_articles(source_html)
    claims: list[dict[str, Any]] = []
    seen: set[str] = set()
    for b in bindings:
        if b["asset"] not in ACTIVE_REPORT_ASSETS:
            continue
        if ".rs." not in b["metric_id"]:
            continue
        art = articles.get(b["asset"], "")
        headline = extract_stance_headline(art) or ""
        parsed = _parse_rs_claim(headline, b)
        if not parsed:
            continue
        if parsed["claim_id"] in seen:
            continue
        seen.add(parsed["claim_id"])
        claims.append(parsed)
    return claims


def _discover_ath_rules(reg: dict[str, Any]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for asset in ACTIVE_REPORT_ASSETS:
        prefix = _metric_prefix(asset)
        price = f"{prefix}.price.usd.live"
        ath = f"{prefix}.price.ath.usd"
        dd = f"{prefix}.price.drawdown_from_ath.pct"
        if price in reg and ath in reg and dd in reg:
            rules.append(
                {
                    "rule_id": f"{asset}::ath_drawdown",
                    "asset": asset,
                    "price_metric_id": price,
                    "ath_metric_id": ath,
                    "drawdown_metric_id": dd,
                }
            )
    return rules


def _discover_derive_rules(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for mid, entry in sorted(plan.items()):
        if entry.get("disposition") != "DERIVE":
            continue
        deriv = entry.get("derivation") or {}
        op = deriv.get("op")
        inputs = deriv.get("inputs") or []
        if not op or not inputs:
            raise SystemExit(
                f"DERIVATION_CONTRACT_INCOMPLETE: {mid} missing op/inputs"
            )
        rules.append(
            {
                "metric_id": mid,
                "op": op,
                "inputs": inputs,
                "calculation_version": deriv.get("calculation_version", "v1"),
            }
        )
    return rules


def _duplicate_groups(bindings: list[dict[str, Any]]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for b in bindings:
        mid = b["metric_id"]
        if b.get("owner") != "CGPT_CURSOR":
            continue
        if b["asset"] in EXCLUDED_ASSETS:
            continue
        groups.setdefault(mid, []).append(b["binding_id"])
    return {k: sorted(v) for k, v in sorted(groups.items()) if len(v) > 1}


def _focus_duplicate_metrics(groups: dict[str, list[str]]) -> list[str]:
    out: list[str] = []
    for mid in groups:
        if any(s in mid for s in DUPLICATE_FOCUS_SUFFIXES):
            out.append(mid)
        elif mid.endswith(".usd.live") or ".return." in mid:
            out.append(mid)
    return sorted(set(out))


def build_contract(
    *,
    registry_path: Path,
    plan_path: Path,
    bindings_path: Path,
    source_html_path: Path,
) -> dict[str, Any]:
    reg_list = _load_json(registry_path)["metrics"]
    reg = {m["metric_id"]: m for m in reg_list}
    plan = {e["metric_id"]: e for e in _load_json(plan_path)["entries"]}
    manifest = _load_json(bindings_path)
    bindings = manifest["bindings"]
    source_html = source_html_path.read_text(encoding="utf-8")

    cgpt_bindings = [
        b
        for b in bindings
        if b.get("owner") == "CGPT_CURSOR"
        and b.get("asset") not in EXCLUDED_ASSETS
    ]
    bound_metric_ids = sorted({b["metric_id"] for b in cgpt_bindings})

    dup_groups = _duplicate_groups(cgpt_bindings)
    derive_rules = _discover_derive_rules(plan)
    ma_claims = _discover_ma_claims(source_html, reg)
    rs_claims = _discover_rs_claims(cgpt_bindings, source_html)
    ath_rules = _discover_ath_rules(reg)

    freshness_metric_ids = sorted(
        {
            b["metric_id"]
            for b in cgpt_bindings
            if any(
                tok in (b.get("anchor_before", "") + b.get("anchor_after", "")).lower()
                for tok in ("freshness", "as of", "as-of", "last verified", "fetched")
            )
        }
    )
    if not freshness_metric_ids:
        freshness_metric_ids = sorted(
            {
                m["metric_id"]
                for m in reg_list
                if m.get("owner") == "CGPT_CURSOR"
                and m.get("metric_type") == "CURRENT_DYNAMIC"
                and m.get("metric_id", "").endswith(".price.usd.live")
            }
        )[:3]

    surface_map: dict[str, list[str]] = {}
    for b in cgpt_bindings:
        surf = classify_surface(b)
        surface_map.setdefault(b["binding_id"], surf)

    contract = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "source_html_sha256": _sha256_file(source_html_path),
        "job1_registry_sha256": _sha256_file(registry_path),
        "collector_plan_sha256": _sha256_file(plan_path),
        "binding_manifest_sha256": _sha256_file(bindings_path),
        "active_report_assets": list(ACTIVE_REPORT_ASSETS),
        "excluded_assets": list(EXCLUDED_ASSETS),
        "required_categories": list(REQUIRED_CATEGORIES),
        "binding_count": len(bindings),
        "cgpt_binding_count": len(cgpt_bindings),
        "bound_metric_ids": bound_metric_ids,
        "duplicate_metric_groups": dup_groups,
        "duplicate_focus_metrics": _focus_duplicate_metrics(dup_groups),
        "derive_rules": derive_rules,
        "derive_plan_count": len(derive_rules),
        "ma_language_claims": ma_claims,
        "rs_language_claims": rs_claims,
        "ath_drawdown_rules": ath_rules,
        "freshness_metric_ids": freshness_metric_ids,
        "surface_by_binding": surface_map,
        "permanent_regressions": {
            "spx_price_duplicate": {
                "metric_id": "spx.price.usd.live",
                "binding_ids": dup_groups.get("spx.price.usd.live", []),
            },
            "pump_buyback_duplicate": {
                "metric_id": "pump.buyback.usd.7d",
                "binding_ids": dup_groups.get("pump.buyback.usd.7d", []),
                "wallet_lane_exclusion": "GROK-owned wallet values are not this metric",
            },
        },
        "expected_checks": {
            "input_lineage": 7,
            "active_assets": len(ACTIVE_REPORT_ASSETS),
            "binding_consistency": len(cgpt_bindings),
            "derive_rules": len(derive_rules),
            "ma_claims": len(ma_claims),
            "rs_claims": len(rs_claims),
            "ath_rules": len(ath_rules),
        },
    }
    return contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=ROOT / "metrics/metric-registry.json")
    parser.add_argument("--plan", type=Path, default=ROOT / "collectors/collector-plan.json")
    parser.add_argument("--bindings", type=Path, default=ROOT / "renderer/binding-manifest.json")
    parser.add_argument("--source-html", type=Path, default=ROOT / "index-v4.html")
    parser.add_argument("--out", type=Path, default=ROOT / "integrity/report-contract.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    built = build_contract(
        registry_path=args.registry,
        plan_path=args.plan,
        bindings_path=args.bindings,
        source_html_path=args.source_html,
    )
    if args.check:
        if not args.out.is_file():
            print(f"MISSING {args.out}", file=sys.stderr)
            return 1
        committed = _load_json(args.out)
        if committed != built:
            print("report-contract.json drift", file=sys.stderr)
            return 1
        print("contract check OK")
        return 0
    args.out.write_text(json.dumps(built, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
