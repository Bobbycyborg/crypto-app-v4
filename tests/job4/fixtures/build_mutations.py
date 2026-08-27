#!/usr/bin/env python3
"""Deterministic mutation matrix M01-M24 for Job 4."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent

MUTATION_EXPECTATIONS: dict[str, dict[str, str]] = {
    "M01": {"overall": "COVERAGE_GAP", "category": "02_active_asset_coverage"},
    "M02": {"overall": "COVERAGE_GAP", "category": "03_canonical_metric_coverage"},
    "M03": {"overall": "COVERAGE_GAP", "category": "01_input_lineage"},
    "M04": {"overall": "FAIL", "category": "12_permanent_regressions", "check_id": "12_reg_spx_price_duplicate"},
    "M05": {"overall": "FAIL", "category": "12_permanent_regressions", "check_id": "12_reg_pump_buyback_duplicate"},
    "M06": {"overall": "FAIL", "category": "12_permanent_regressions", "check_id": "12_reg_pump_buyback_duplicate"},
    "M07": {"overall": "PASS", "category": "12_permanent_regressions", "check_id": "12_reg_pump_wallet_invariance"},
    "M08": {"overall": "FAIL", "category": "06_ath_drawdown_arithmetic"},
    "M09": {"overall": "FAIL", "category": "06_ath_drawdown_arithmetic"},
    "M10": {"overall": "FAIL", "category": "07_moving_average_language"},
    "M11": {"overall": "FAIL", "category": "08_relative_strength_language"},
    "M12": {"overall": "FAIL", "category": "09_freshness_asof_consistency"},
    "M13": {"overall": "FAIL", "category": "09_freshness_asof_consistency"},
    "M14": {"overall": "FAIL", "category": "10_tooltip_visible_visual_agreement"},
    "M15": {"overall": "FAIL", "category": "05_duplicate_consistency"},
    "M16": {"overall": "FAIL", "category": "05_duplicate_consistency"},
    "M17": {"overall": "FAIL", "category": "05_duplicate_consistency"},
    "M18": {"overall": "FAIL", "category": "11_derived_metric_arithmetic"},
    "M19": {"overall": "COVERAGE_GAP", "category": "11_derived_metric_arithmetic"},
    "M20": {"overall": "FAIL", "category": "04_rendered_binding_consistency"},
    "M21": {"overall": "PASS", "category": "04_rendered_binding_consistency"},
    "M22": {"overall": "FAIL", "category": "01_input_lineage"},
    "M23": {"overall": "COVERAGE_GAP", "category": "04_rendered_binding_consistency"},
    "M24": {"overall": "PASS", "category": "12_permanent_regressions"},
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

    # M03 bad contract handled in test via temp contract

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

    # M09 visual bar mutation — BTC ATH bar only
    sys.path.insert(0, str(ROOT))
    from integrity.extract import extract_articles

    articles = extract_articles(html)
    btc_art = articles.get("btc", "")
    btc_art_m = re.sub(
        r'(<div class="ddbar-fill" style="width:)\d+(%")',
        r"\g<1>5\2",
        btc_art,
        count=1,
    )
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

    # M16/M17 duplicate groups — reuse M05/M15 patterns
    (FIX / "M16-rendered.html").write_text(h15, encoding="utf-8")
    _save("M16-snapshot.json", snap)
    (FIX / "M17-rendered.html").write_text(h15, encoding="utf-8")
    _save("M17-snapshot.json", snap)

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

    # M21 UNKNOWN + UNKNOWN UI — re-render from UNKNOWN snapshot
    s21 = copy.deepcopy(snap)
    s21["metrics"]["btc.price.usd.live"]["status"] = "UNKNOWN"
    _save("M21-snapshot.json", s21)
    m21_out = FIX / "M21-rendered.html"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "renderer/render_report.py"),
            "--snapshot",
            str(FIX / "M21-snapshot.json"),
            "--source",
            str(ROOT / "index-v4.html"),
            "--out",
            str(m21_out),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode not in (0, 2):
        raise RuntimeError(proc.stderr or proc.stdout)

    # M22 hash mismatch handled in test

    # M23 removed binding occurrence — corrupt anchor context in rendered HTML
    first = contract["permanent_regressions"]["spx_price_duplicate"]["binding_ids"][0]
    b = next(x for x in manifest["bindings"] if x["binding_id"] == first)
    h23 = html.replace(b["anchor_before"], b["anchor_before"][:-12] + "ZZZCORRUPT", 1)
    (FIX / "M23-rendered.html").write_text(h23, encoding="utf-8")
    _save("M23-snapshot.json", snap)

    # M24 wallet mutation — same as M07
    _save("M24-snapshot.json", s07)
    (FIX / "M24-rendered.html").write_text(h07, encoding="utf-8")


if __name__ == "__main__":
    build_mutations()
