#!/usr/bin/env python3
"""Deterministic mutation matrix M01-M24 for Job 4."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent

MUTATION_EXPECTATIONS: dict[str, dict[str, Any]] = {
    "M01": {
        "exit_code": 3,
        "overall": "COVERAGE_GAP",
        "check_id": "02_asset_zec",
        "check_status": "COVERAGE_GAP",
        "category": "02_active_asset_coverage",
    },
    "M02": {
        "exit_code": 3,
        "overall": "COVERAGE_GAP",
        "check_id": "03_metric_btc_price_usd_live",
        "check_status": "COVERAGE_GAP",
        "category": "03_canonical_metric_coverage",
    },
    "M03": {
        "exit_code": 3,
        "overall": "COVERAGE_GAP",
        "check_id": "04_bind_intentionally_absent_probe",
        "check_status": "COVERAGE_GAP",
        "category": "04_rendered_binding_consistency",
        "contract": "M03-contract.json",
    },
    "M04": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "12_reg_spx_price_duplicate",
        "check_status": "FAIL",
        "category": "12_permanent_regressions",
    },
    "M05": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "12_reg_pump_buyback_duplicate",
        "check_status": "FAIL",
        "category": "12_permanent_regressions",
    },
    "M06": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "12_reg_pump_buyback_duplicate",
        "check_status": "FAIL",
        "category": "12_permanent_regressions",
    },
    "M07": {
        "exit_code": 0,
        "overall": "PASS",
        "check_id": "12_reg_pump_wallet_invariance",
        "check_status": "PASS",
        "category": "12_permanent_regressions",
    },
    "M08": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "06_ath_btc",
        "check_status": "FAIL",
        "category": "06_ath_drawdown_arithmetic",
    },
    "M09": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "06_ath_btc",
        "check_status": "FAIL",
        "category": "06_ath_drawdown_arithmetic",
    },
    "M10": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "07_ma_btc_ma_language_stance_headline",
        "check_status": "FAIL",
        "category": "07_moving_average_language",
    },
    "M11": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "08_rs_sol.rs.vs_btc.pp.7d_128b8d765ef15fa0_rs_language",
        "check_status": "FAIL",
        "category": "08_relative_strength_language",
    },
    "M12": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "09_fresh_btc_price_usd_live",
        "check_status": "FAIL",
        "category": "09_freshness_asof_consistency",
    },
    "M13": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "09_fresh_btc_price_usd_live",
        "check_status": "FAIL",
        "category": "09_freshness_asof_consistency",
    },
    "M14": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "10_surface_pump_buyback_usd_7d",
        "check_status": "FAIL",
        "category": "10_tooltip_visible_visual_agreement",
    },
    "M15": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "05_dup_pump_buyback_usd_7d",
        "check_status": "FAIL",
        "category": "05_duplicate_consistency",
    },
    "M16": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "04_bind_btc.inflation.pct.current::01660e6a6d540fca",
        "check_status": "FAIL",
        "category": "04_rendered_binding_consistency",
    },
    "M17": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "04_bind_render.bme.ratio.last4::00a581be80d3bc08",
        "check_status": "FAIL",
        "category": "04_rendered_binding_consistency",
    },
    "M18": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "11_derive_btc_leverage_x_current",
        "check_status": "FAIL",
        "category": "11_derived_metric_arithmetic",
    },
    "M19": {
        "exit_code": 3,
        "overall": "COVERAGE_GAP",
        "check_id": "11_derive_btc_leverage_x_current",
        "check_status": "COVERAGE_GAP",
        "category": "11_derived_metric_arithmetic",
    },
    "M20": {
        "exit_code": 2,
        "overall": "FAIL",
        "check_id": "04_bind_btc.price.usd.live::30f665b010005234",
        "check_status": "FAIL",
        "category": "04_rendered_binding_consistency",
    },
    "M21": {
        "exit_code": 0,
        "overall": "PASS",
        "check_id": "04_bind_btc.price.usd.live::30f665b010005234",
        "check_status": "PASS",
        "category": "04_rendered_binding_consistency",
    },
    "M22": {
        "exit_code": 4,
        "overall": "FAIL",
        "check_id": "01_lineage_07_manifest_source_actual",
        "check_status": "FAIL",
        "category": "01_input_lineage",
        "bindings": "M22-manifest.json",
        "contract": "M22-contract.json",
    },
    "M23": {
        "exit_code": 4,
        "overall": "FAIL",
        "check_id": "01_lineage_04_source_html_contract",
        "check_status": "FAIL",
        "category": "01_input_lineage",
        "source_html": "M23-source.html",
    },
    "M24": {
        "exit_code": 0,
        "overall": "PASS",
        "check_id": "12_reg_pump_wallet_invariance",
        "check_status": "PASS",
        "category": "12_permanent_regressions",
    },
}


def _load(name: str) -> dict[str, Any]:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def _save(name: str, data: dict[str, Any]) -> Path:
    p = FIX / name
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p


def build_mutations() -> None:
    snap = _load("golden-snapshot.json")
    html = (FIX / "golden-rendered.html").read_text(encoding="utf-8")
    contract = json.loads((ROOT / "integrity/report-contract.json").read_text())
    manifest = json.loads((ROOT / "renderer/binding-manifest.json").read_text())

    # M01 missing active asset
    h01 = re.sub(
        r'<article[^>]*data-asset="zec"[^>]*>.*?</article>',
        "",
        html,
        count=1,
        flags=re.S,
    )
    (FIX / "M01-rendered.html").write_text(h01, encoding="utf-8")
    _save("M01-snapshot.json", snap)

    # M02 missing metric
    s02 = copy.deepcopy(snap)
    s02["metrics"].pop("btc.price.usd.live", None)
    _save("M02-snapshot.json", s02)
    (FIX / "M02-rendered.html").write_text(html, encoding="utf-8")

    # M03 extra expected check while category 04 still present
    c03 = copy.deepcopy(contract)
    extra = "04_bind_intentionally_absent_probe"
    c03.setdefault("expected_check_ids", [])
    if extra not in c03["expected_check_ids"]:
        c03["expected_check_ids"] = list(c03["expected_check_ids"]) + [extra]
    _save("M03-contract.json", c03)
    _save("M03-snapshot.json", snap)
    (FIX / "M03-rendered.html").write_text(html, encoding="utf-8")

    # M04 SPX duplicate — break first SPX regression binding span
    s04 = copy.deepcopy(snap)
    (FIX / "M04-snapshot.json").write_text(json.dumps(s04, indent=2) + "\n")
    spx_ids = contract.get("permanent_regressions", {}).get("spx_price_duplicate", {}).get("binding_ids", [])
    h04 = html
    if spx_ids:
        hero_b = next(b for b in manifest["bindings"] if b["binding_id"] == spx_ids[0])
        lit = hero_b.get("source_literal", "")
        if lit and lit in h04:
            h04 = h04.replace(lit, "$0.316", 1)
        elif "$0.373899" in h04:
            h04 = h04.replace("$0.373899", "$0.316", 1)
    (FIX / "M04-rendered.html").write_text(h04, encoding="utf-8")

    # M05/M06 PUMP buyback stale values
    buyback_lit = None
    for b in manifest["bindings"]:
        if b.get("metric_id") == "pump.buyback.usd.7d" and b.get("owner") == "CGPT_CURSOR":
            buyback_lit = b.get("source_literal")
            break
    for mid, val, tag in (("M05", "$5.7M", "M05"), ("M06", "$5.2M", "M06")):
        s = copy.deepcopy(snap)
        _save(f"{tag}-snapshot.json", s)
        needle = buyback_lit or "$6.8M/wk"
        h = html.replace(needle, val, 1) if needle in html else html
        (FIX / f"{tag}-rendered.html").write_text(h, encoding="utf-8")

    # M07 wallet $5.7M in siren data — should not fail non-wallet check
    s07 = copy.deepcopy(snap)
    _save("M07-snapshot.json", s07)
    h07 = html.replace('"sent":8848274', '"sent":5700000', 1)
    (FIX / "M07-rendered.html").write_text(h07, encoding="utf-8")

    # M08 wrong ATH drawdown in snapshot
    s08 = copy.deepcopy(snap)
    if "btc.price.drawdown_from_ath.pct" in s08["metrics"]:
        s08["metrics"]["btc.price.drawdown_from_ath.pct"]["normalized_value"] = 99
    _save("M08-snapshot.json", s08)
    (FIX / "M08-rendered.html").write_text(html, encoding="utf-8")

    # M09 visual bar mutation — inject a wrong BTC ATH bar
    sys.path.insert(0, str(ROOT))
    from integrity.extract import extract_articles

    articles = extract_articles(html)
    btc_art = articles.get("btc", "")
    marker = '<h2 class="alt-ticker">BTC</h2>'
    bar = '<div class="ddbar-fill" style="width:5%"></div>'
    btc_art_m = btc_art.replace(marker, marker + bar, 1) if marker in btc_art else btc_art
    h09 = html.replace(btc_art, btc_art_m, 1) if btc_art_m != btc_art else html
    (FIX / "M09-rendered.html").write_text(h09, encoding="utf-8")
    _save("M09-snapshot.json", snap)

    # M10 MA contradiction — flip snapshot MA above to below
    s10 = copy.deepcopy(snap)
    if "btc.ma.usd.50d" in s10["metrics"]:
        s10["metrics"]["btc.ma.usd.50d"]["normalized_value"] = 999999
    _save("M10-snapshot.json", s10)
    (FIX / "M10-rendered.html").write_text(html, encoding="utf-8")

    # M11 RS contradiction
    s11 = copy.deepcopy(snap)
    for claim in contract.get("rs_language_claims", []):
        if claim["language"] == "LEADS" and claim["metric_id"] in s11["metrics"]:
            s11["metrics"][claim["metric_id"]]["normalized_value"] = -99
            break
    _save("M11-snapshot.json", s11)
    (FIX / "M11-rendered.html").write_text(html, encoding="utf-8")

    # M12 freshness FRESH vs UNKNOWN
    s12 = copy.deepcopy(snap)
    fresh_mid = "btc.price.usd.live"
    if fresh_mid in s12["metrics"]:
        s12["metrics"][fresh_mid]["freshness"] = "UNKNOWN"
    _save("M12-snapshot.json", s12)
    btc_b = next(
        b
        for b in manifest["bindings"]
        if b.get("metric_id") == fresh_mid and b.get("owner") == "CGPT_CURSOR"
    )
    h12 = html
    before = btc_b["anchor_before"]
    if before in h12:
        h12 = h12.replace(before, before + "Freshness · same-day ", 1)
    (FIX / "M12-rendered.html").write_text(h12, encoding="utf-8")

    # M13 source_as_of mismatch
    s13 = copy.deepcopy(snap)
    if fresh_mid in s13["metrics"]:
        s13["metrics"][fresh_mid]["source_as_of"] = "2099-01-01T00:00:00Z"
    _save("M13-snapshot.json", s13)
    h13 = html
    if before in h13:
        h13 = h13.replace(before, before + "As of · 2026-01-01 ", 1)
    (FIX / "M13-rendered.html").write_text(h13, encoding="utf-8")

    # M14 tooltip duplicate — corrupt one pump buyback tooltip span
    h14 = html.replace("$6.8M/wk</div><div class=\"ev-tip-rows\">", "$9.9M/wk</div><div class=\"ev-tip-rows\">", 1)
    (FIX / "M14-rendered.html").write_text(h14, encoding="utf-8")
    _save("M14-snapshot.json", snap)

    # M15 body duplicate
    h15 = html.replace("$6.8M buybacks / 7d", "$5.7M buybacks / 7d", 1)
    (FIX / "M15-rendered.html").write_text(h15, encoding="utf-8")
    _save("M15-snapshot.json", snap)

    # M16 ordinary numeric: mutate one rendered occurrence; source_literal still canonical
    inf_b = next(
        b
        for b in manifest["bindings"]
        if b["binding_id"] == "btc.inflation.pct.current::01660e6a6d540fca"
    )
    needle = inf_b["anchor_before"] + inf_b["source_literal"]
    h16 = html.replace(needle, inf_b["anchor_before"] + "0.99", 1)
    (FIX / "M16-rendered.html").write_text(h16, encoding="utf-8")
    _save("M16-snapshot.json", snap)

    # M17 string_exact: change snapshot canonical, leave rendered at old source_literal
    s17 = copy.deepcopy(snap)
    ratio_mid = "render.bme.ratio.last4"
    if ratio_mid in s17["metrics"]:
        s17["metrics"][ratio_mid]["normalized_value"] = "STALE_LITERAL_PROBE"
    _save("M17-snapshot.json", s17)
    (FIX / "M17-rendered.html").write_text(html, encoding="utf-8")

    # M18 derived mismatch
    s18 = copy.deepcopy(snap)
    if "btc.leverage.x.current" in s18["metrics"]:
        s18["metrics"]["btc.leverage.x.current"]["normalized_value"] = 999
    _save("M18-snapshot.json", s18)
    (FIX / "M18-rendered.html").write_text(html, encoding="utf-8")

    # M19 missing derivation input
    s19 = copy.deepcopy(snap)
    s19["metrics"].pop("btc.volume.spot.usd.24h", None)
    _save("M19-snapshot.json", s19)
    (FIX / "M19-rendered.html").write_text(html, encoding="utf-8")

    # M20 UNKNOWN + old numeric — use failclosed snapshot pattern
    s20 = copy.deepcopy(snap)
    s20["metrics"]["btc.price.usd.live"]["status"] = "UNKNOWN"
    _save("M20-snapshot.json", s20)
    (FIX / "M20-rendered.html").write_text(html, encoding="utf-8")

    # M21 UNKNOWN + UNKNOWN UI — mutate only the bound live-price occurrence
    s21 = copy.deepcopy(snap)
    s21["metrics"]["btc.price.usd.live"]["status"] = "UNKNOWN"
    _save("M21-snapshot.json", s21)
    live_b = next(
        b
        for b in manifest["bindings"]
        if b["binding_id"] == "btc.price.usd.live::30f665b010005234"
    )
    live_needle = live_b["anchor_before"] + live_b["source_literal"]
    h21 = html.replace(live_needle, live_b["anchor_before"] + "UNKNOWN", 1)
    (FIX / "M21-rendered.html").write_text(h21, encoding="utf-8")

    # M22 mutate only manifest-declared source hash
    man22 = copy.deepcopy(manifest)
    man22["source_html_sha256"] = "0" * 64
    man22_path = FIX / "M22-manifest.json"
    man22_path.write_text(json.dumps(man22, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    c22 = copy.deepcopy(contract)
    c22["binding_manifest_sha256"] = hashlib.sha256(man22_path.read_bytes()).hexdigest()
    _save("M22-contract.json", c22)
    _save("M22-snapshot.json", snap)
    (FIX / "M22-rendered.html").write_text(html, encoding="utf-8")

    # M23 mutate only actual source file
    src = (ROOT / "index-v4.html").read_text(encoding="utf-8")
    (FIX / "M23-source.html").write_text(src + "\n<!-- job4-source-mutation -->\n", encoding="utf-8")
    _save("M23-snapshot.json", snap)
    (FIX / "M23-rendered.html").write_text(html, encoding="utf-8")

    # M24 wallet mutation — same as M07
    _save("M24-snapshot.json", s07)
    (FIX / "M24-rendered.html").write_text(h07, encoding="utf-8")


if __name__ == "__main__":
    build_mutations()
