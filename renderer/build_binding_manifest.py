#!/usr/bin/env python3
"""Build Job 3 binding manifest from Job 1 mappings + index-v4.html."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderer.anchors import (
    build_anchor,
    build_html_index,
    classify_target_kind,
    extract_region_literal,
    find_markup_literal,
    locate_literal,
    locate_literal_in_region,
    plain_text_binding_literal,
    parse_xpath_segments,
    resolve_region,
    _article_index_score,
    _location_score,
    _path_at_position,
    _path_prefix_len,
    _path_suffix_len,
    _xpath_score,
)
from renderer.eligibility import eligible_mappings, load_job1_job2
from renderer.formatters import adjust_formatter_for_binding, infer_formatter

MANIFEST_PATH = Path(__file__).resolve().parent / "binding-manifest.json"
HTML_PATH = ROOT / "index-v4.html"


def _binding_id(metric_id: str, occurrence_id: str) -> str:
    return f"{metric_id}::{occurrence_id}"


def _effective_literal(
    html: str,
    index,
    manifest_lit: str,
    xpath: str | None,
    location_hint: str | None,
    *,
    longer_literals: list[str] | None = None,
) -> str | None:
    region = resolve_region(index, xpath, html=html, location_hint=location_hint, literal=manifest_lit) if xpath else None
    if region and manifest_lit:
        plain = plain_text_binding_literal(html, region, manifest_lit)
        if plain:
            return plain[0]
    if manifest_lit and manifest_lit in html:
        start = 0
        while True:
            i = html.find(manifest_lit, start)
            if i < 0:
                break
            if longer_literals:
                if any(html.startswith(longer, i) for longer in longer_literals if len(longer) > len(manifest_lit)):
                    start = i + 1
                    continue
            eff = manifest_lit
            if "<" not in eff and ">" not in eff:
                return eff
            start = i + 1
    if manifest_lit:
        found = find_markup_literal(html, index, manifest_lit, xpath=xpath, location_hint=location_hint)
        if found:
            eff = found[0].split("<", 1)[0]
            if eff:
                return eff
    return None


def _assign_bindings(html: str, mappings: list[dict[str, Any]], occ: dict[str, Any]) -> list[dict[str, Any]]:
    index = build_html_index(html)
    longer_literals = sorted({(m["match"].get("literal") or "") for m in mappings if m["match"].get("literal")}, key=len, reverse=True)
    used: list[tuple[int, int]] = []
    out: list[dict[str, Any]] = []
    for mapping in sorted(mappings, key=lambda m: m["match"]["occurrence_id"]):
        mid = mapping["metric_id"]
        match = mapping["match"]
        oid = match["occurrence_id"]
        xpath = match.get("locator")
        hint = occ.get(oid, {}).get("ui_location_identifier")
        manifest_lit = match.get("literal") or ""

        effective = _effective_literal(html, index, manifest_lit, xpath, hint, longer_literals=longer_literals)
        if not effective:
            raise SystemExit(f"JOB 3 BINDING CONTRACT BLOCKER missing literal {mid} {oid}")

        region = resolve_region(index, xpath, html=html, location_hint=hint) if xpath else None
        cands: list[tuple[int, int, int]] = []
        start = 0
        while True:
            i = html.find(effective, start)
            if i < 0:
                break
            end = i + len(effective)
            skip = False
            if manifest_lit and manifest_lit == effective:
                for longer in longer_literals:
                    if len(longer) <= len(manifest_lit):
                        break
                    if html.startswith(longer, i):
                        skip = True
                        break
            if skip:
                start = i + 1
                continue
            if any(not (end <= u[0] or i >= u[1]) for u in used):
                start = i + 1
                continue
            try:
                build_anchor(html, i, effective)
            except ValueError:
                start = i + 1
                continue
            score = (
                _location_score(html, i, hint)
                + _xpath_score(html, i, xpath)
                + _article_index_score(html, i, xpath)
            )
            at = _path_at_position(index, i)
            if at is not None and xpath:
                score += _path_prefix_len(parse_xpath_segments(xpath), at) * 25
                score += _path_suffix_len(parse_xpath_segments(xpath), at) * 25
            if region and region[0] <= i < region[1]:
                score += 1000
            cands.append((score, i, end))
            start = i + 1

        if not cands:
            pos = locate_literal(
                index,
                manifest_lit or effective,
                xpath,
                location_hint=hint,
                effective_literal=effective,
            )
            if pos is not None:
                end = pos + len(effective)
                if all(end <= u[0] or pos >= u[1] for u in used):
                    try:
                        build_anchor(html, pos, effective)
                        cands = [(2000, pos, end)]
                    except ValueError:
                        pass

        if not cands and manifest_lit:
            start = 0
            while True:
                i = html.find(manifest_lit, start)
                if i < 0:
                    break
                end = i + len(manifest_lit)
                skip = False
                for longer in longer_literals:
                    if len(longer) <= len(manifest_lit):
                        break
                    if html.startswith(longer, i):
                        skip = True
                        break
                if skip:
                    start = i + 1
                    continue
                if any(not (end <= u[0] or i >= u[1]) for u in used):
                    start = i + 1
                    continue
                try:
                    build_anchor(html, i, manifest_lit)
                except ValueError:
                    start = i + 1
                    continue
                score = (
                    _location_score(html, i, hint)
                    + _xpath_score(html, i, xpath)
                    + _article_index_score(html, i, xpath)
                )
                at = _path_at_position(index, i)
                if at is not None and xpath:
                    p = parse_xpath_segments(xpath)
                    score += _path_prefix_len(p, at) * 25 + _path_suffix_len(p, at) * 25
                if region and region[0] <= i < region[1]:
                    score += 1000
                cands.append((score, i, end))
                start = i + 1
            if cands:
                effective = manifest_lit

        if not cands:
            raise SystemExit(f"JOB 3 BINDING CONTRACT BLOCKER no anchor {mid} {oid}")
        if "<" in effective or ">" in effective:
            raise SystemExit(f"JOB 3 BINDING CONTRACT BLOCKER markup literal {mid} {oid}")
        cands.sort(key=lambda x: (-x[0], x[1]))
        score, pos, end = cands[0]
        used.append((pos, end))
        anchor = build_anchor(html, pos, effective)
        target_kind = classify_target_kind(html, pos, effective)
        if target_kind == "HTML_TEXT" and ("<" in effective or ">" in effective):
            raise SystemExit(f"JOB 3 BINDING CONTRACT BLOCKER tag crossing {mid} {oid}")
        fmt = adjust_formatter_for_binding(infer_formatter(manifest_lit or effective), manifest_lit, effective, anchor["anchor_after"])
        entry = {
            "binding_id": _binding_id(mid, oid),
            "metric_id": mid,
            "asset": mapping.get("asset") or "",
            "owner": mapping.get("owner") or "CGPT_CURSOR",
            "job1_occurrence_id": oid,
            "job1_mapping_id": mapping.get("mapping_id"),
            "occurrence_classification": mapping.get("classification"),
            "update_mode": mapping.get("update_mode") or occ.get(oid, {}).get("update_mode"),
            "target_kind": target_kind,
            "field": "value",
            "source_literal": effective,
            "anchor_before": anchor["anchor_before"],
            "anchor_after": anchor["anchor_after"],
            "anchor_sha256": anchor["anchor_sha256"],
            "component_id": occ.get(oid, {}).get("ui_location_identifier"),
            "formatter": fmt,
            "status_behavior": "UNKNOWN_ON_NON_OK",
            "notes": None,
        }
        out.append(entry)
    return out


def build_manifest() -> dict[str, Any]:
    reg, plan, manifest_meta, mappings = load_job1_job2()
    occ_list = json.loads((ROOT / "metrics/ui-occurrences.json").read_text(encoding="utf-8"))["occurrences"]
    occ = {o["occurrence_id"]: o for o in occ_list}
    elig = eligible_mappings(mappings, reg, plan)
    html = HTML_PATH.read_text(encoding="utf-8")
    bindings = _assign_bindings(html, elig, occ)
    return {
        "schema_version": "job3.binding.v1",
        "source_html": "index-v4.html",
        "source_html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "job1_registry_sha256": hashlib.sha256((ROOT / "metrics/metric-registry.json").read_bytes()).hexdigest(),
        "eligible_occurrences": len(elig),
        "bindings": bindings,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--out", default=str(MANIFEST_PATH))
    args = p.parse_args()
    built = build_manifest()
    if args.check:
        committed = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if committed != built:
            print("binding manifest drift", file=sys.stderr)
            return 1
        print("binding manifest check OK")
        return 0
    Path(args.out).write_text(json.dumps(built, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} bindings={len(built['bindings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
