#!/usr/bin/env python3
"""Build Job 3 binding manifest from Job 1 mappings + index-v4.html."""

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

from renderer.coin_span import coin_regions, hits_in_regions
from renderer.formatters import infer_formatter
from renderer.anchors import (
    build_anchor,
    build_html_index,
    classify_target_kind,
    parse_xpath_segments,
    _article_index_score,
    _location_score,
    _path_at_position,
    _path_prefix_len,
    _path_suffix_len,
    _xpath_score,
)
from renderer.eligibility import eligible_mappings, load_job1_job2
from renderer.formatter_recovery import FormatterRecoveryError, recover_presentation_formatter, recover_formatter, resolve_binding_raw

MANIFEST_PATH = Path(__file__).resolve().parent / "binding-manifest.json"
HTML_PATH = ROOT / "index-v4.html"


def _binding_id(metric_id: str, occurrence_id: str) -> str:
    return f"{metric_id}::{occurrence_id}"


_CRITICAL_ZONES = frozenset({"hold", "hero", "desk", "etf", "fear", "greed", "stance", "trend"})


def _zone(mapping: dict[str, Any], occ_row: dict[str, Any], hint: str | None, xpath: str | None) -> str:
    blob = " ".join(
        [
            str(hint or ""),
            str(occ_row.get("ui_location_type") or ""),
            str(occ_row.get("surface") or ""),
            str(xpath or ""),
            str((mapping.get("match") or {}).get("locator") or ""),
        ]
    ).lower()
    for name in ("stance", "fear", "greed", "etf", "desk", "hero", "hold"):
        if name in blob:
            return name
    if "btc trend" in blob:
        return "trend"
    if "/button" in blob:
        return "hold"
    return "article"


_PRICE_NODE = re.compile(r'class="(?:alt-price|desk-px|hold-px)">([^<]+)')


def _price_literal(html: str, regions: list[tuple[int, int]]) -> str | None:
    for start, end in regions:
        match = _PRICE_NODE.search(html, start, end)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return None


def _etf_literal(html: str, asset: str, metric_id: str) -> tuple[str, list[tuple[int, int]]] | None:
    ticker = (asset or "").upper()
    if not ticker:
        return None
    window = "7D" if ".7d" in metric_id else "30D" if ".30d" in metric_id else ""
    if window == "" and ".1d" in metric_id:
        tip = re.search(
            rf'etf-tip-asset">{re.escape(ticker)}</div>.*?ev-k">1D</span><span class="ev-v[^"]*">(\$[\d,.]+)',
            html,
        )
        if not tip:
            return None
        return tip.group(1), [(tip.start(1), tip.end(1))]
    if not window:
        return None
    row = re.search(rf'class="etf-row"><a [^>]*>{re.escape(ticker)}</a>.*?</div>', html)
    if not row:
        return None
    match = re.search(
        rf'(\$[\d,.]+)(?=<span class="u-unit">[^<]*</span>\s*<span class="u">{window}</span>)',
        row.group(0),
    )
    if not match:
        return None
    return match.group(1), [(row.start(), row.end())]


def _dial_literal(html: str, regions: list[tuple[int, int]], label: str) -> tuple[str, list[tuple[int, int]]] | None:
    key = re.sub(r"[^a-z0-9]", "", (label or "").lower())
    if len(key) < 4:
        return None
    for start, end in regions:
        chunk = html[start:end]
        for match in re.finditer(r">([^<]{2,48})<", chunk):
            got = re.sub(r"[^a-z0-9]", "", match.group(1).lower())
            if not got or got not in key and key not in got:
                continue
            rest = chunk[match.end() : match.end() + 900]
            num = re.search(r'class="econ-dial-num[^"]*">([^<]+)', rest)
            if not num or not num.group(1).strip():
                continue
            abs_start = start + match.end() + num.start(1)
            text = num.group(1).strip()
            if not re.fullmatch(r"[+\-~−$]?[\d,.]+[%kKmMbBx×]?", text):
                return ("__NOT_NUMERIC__", [])
            return text, [(abs_start, abs_start + len(text))]
    return None


def _amount_near_label(html: str, regions: list[tuple[int, int]], label: str) -> tuple[str, list[tuple[int, int]]] | None:
    key = (label or "").strip()
    if len(re.sub(r"[^a-z0-9]", "", key.lower())) < 4:
        return None
    for start, end in regions:
        if not html[start : start + 8].lower().startswith("<article"):
            continue
        chunk = html[start:end]
        match = re.search(re.escape(key), chunk, re.I)
        if not match:
            continue
        window = chunk[match.end() : match.end() + 160]
        num = re.search(r"\$[\d,.]+[kKmMbB]?", window)
        if not num:
            continue
        abs_start = start + match.end() + num.start()
        text = num.group(0)
        return text, [(abs_start, abs_start + len(text))]
    return None


def _oneday_literal(html: str, regions: list[tuple[int, int]]) -> str | None:
    for start, end in regions:
        match = re.search(r"1d\s+[+−\-]*(\$[\d,.]+[MB]?)", html[start:end], re.I)
        if match:
            return match.group(1)
    return None


def _critical(zone: str, metric_id: str) -> bool:
    if zone in _CRITICAL_ZONES:
        return True
    mid = metric_id.lower()
    return any(part in mid for part in (".etf.", "fear_greed", ".price.usd"))


def _effective_literal(
    html: str,
    manifest_lit: str,
    regions: list[tuple[int, int]],
    *,
    longer_literals: list[str] | None = None,
) -> str | None:
    if not manifest_lit or not regions:
        return None
    for i in hits_in_regions(html, manifest_lit, regions):
        if longer_literals and any(
            html.startswith(longer, i) for longer in longer_literals if len(longer) > len(manifest_lit)
        ):
            continue
        if "<" not in manifest_lit and ">" not in manifest_lit:
            return manifest_lit
    return None


def _infer_literal(manifest_lit: str, effective: str) -> str:
    if manifest_lit:
        plain = re.sub(r"<[^>]+>", "", manifest_lit)
        if plain and "<" not in plain and ">" not in plain:
            return plain
    return effective


def _assign_bindings(
    html: str,
    mappings: list[dict[str, Any]],
    occ: dict[str, Any],
    reg: dict[str, Any],
    blockers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    index = build_html_index(html)
    region_cache: dict[str, list[tuple[int, int]]] = {}
    bound_once: set[str] = set()
    priced: set[str] = set()
    longer_literals = sorted({(m["match"].get("literal") or "") for m in mappings if m["match"].get("literal")}, key=len, reverse=True)
    used: list[tuple[int, int]] = []
    out: list[dict[str, Any]] = []
    def _order(mapping: dict[str, Any]) -> tuple:
        mid = mapping["metric_id"]
        if mid.endswith("price.usd.live"):
            rank = 0
        elif ".price.usd" in mid:
            rank = 1
        elif ".etf.flow." in mid or "fear_greed" in mid:
            rank = 2
        else:
            rank = 3
        return (rank, mapping["match"]["occurrence_id"])

    for mapping in sorted(mappings, key=_order):
        mid = mapping["metric_id"]
        match = mapping["match"]
        oid = match["occurrence_id"]
        xpath = match.get("locator")
        occ_row = occ.get(oid, {})
        hint = occ_row.get("ui_location_identifier")
        manifest_lit = match.get("literal") or ""
        if mid in bound_once and (".price.usd" in mid or ".etf.flow." in mid or "fear_greed" in mid):
            continue
        asset_key = mapping.get("asset") or ""
        if asset_key not in region_cache:
            region_cache[asset_key] = coin_regions(html, asset_key)
        regions = list(region_cache[asset_key])
        zone = _zone(mapping, occ_row, hint, xpath)
        critical = _critical(zone, mid)

        def _miss(reason: str, *, _mid: str = mid, _oid: str = oid, _zone: str = zone) -> None:
            crit = _critical(_zone, _mid)
            if ".price.usd" in _mid and asset_key.upper() in priced:
                crit = False
            blockers.append(
                {
                    "metric_id": _mid,
                    "occurrence_id": _oid,
                    "asset": mapping.get("asset") or "",
                    "zone": _zone,
                    "critical": crit,
                    "reason": reason,
                }
            )

        if not regions and ".etf.flow." not in mid and "fear_greed" not in mid:
            _miss("no coin region")
            continue
        effective = _effective_literal(html, manifest_lit, regions, longer_literals=longer_literals) if regions else None
        extra: list[tuple[int, int]] = []
        refreshed = False
        if ".price.usd" in mid:
            price = _price_literal(html, regions)
            if price:
                effective = price
                refreshed = True
        if ".etf.flow." in mid and (".7d" in mid or ".30d" in mid):
            found = _etf_literal(html, mapping.get("asset") or "", mid)
            if found:
                effective, extra = found
                refreshed = True
        elif not effective and ".etf.flow." in mid:
            one = _oneday_literal(html, regions)
            if one:
                effective = one
                refreshed = True
        if not effective and hint:
            dial = _dial_literal(html, regions, hint)
            if dial and dial[0] == "__NOT_NUMERIC__":
                blockers.append(
                    {
                        "metric_id": mid,
                        "occurrence_id": oid,
                        "asset": mapping.get("asset") or "",
                        "zone": zone,
                        "critical": False,
                        "reason": "label is not a number",
                    }
                )
                continue
            if dial:
                effective, extra = dial
                refreshed = True
        if not effective and hint:
            near = _amount_near_label(html, regions, hint)
            if near:
                effective, extra = near
                refreshed = True
        if not effective and ".etf.flow." in mid and ".1d" in mid:
            found = _etf_literal(html, mapping.get("asset") or "", mid)
            if found:
                effective, extra = found
                refreshed = True
        if "fear_greed" in mid:
            match = re.search(r'class="fg-dial-num"[^>]*>(\d+)<', html)
            if match:
                effective = match.group(1)
                extra = [(match.start(1), match.end(1))]
                refreshed = True
        if not effective:
            _miss("missing literal")
            continue
        regions = list(regions) + extra

        cands: list[tuple[int, int, int]] = []
        for i in hits_in_regions(html, effective, regions):
            end = i + len(effective)
            if any(html.startswith(longer, i) for longer in longer_literals if len(longer) > len(effective)):
                continue
            if any(not (end <= u[0] or i >= u[1]) for u in used):
                continue
            try:
                build_anchor(html, i, effective)
            except ValueError:
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
            cands.append((score, i, end))

        if not cands:
            _miss("no anchor")
            continue
        if "<" in effective or ">" in effective:
            _miss("markup literal")
            continue
        cands.sort(key=lambda x: (-x[0], x[1]))
        score, pos, end = cands[0]
        used.append((pos, end))
        anchor = build_anchor(html, pos, effective)
        target_kind = classify_target_kind(html, pos, effective)
        if target_kind == "HTML_TEXT" and ("<" in effective or ">" in effective):
            _miss("tag crossing")
            continue
        if refreshed:
            fmt = infer_formatter(effective)
            if fmt.get("type") != "numeric":
                _miss("no formatter")
                continue
            raw_value = None
        else:
            try:
                selection = resolve_binding_raw(
                    reg,
                    mid,
                    oid,
                    source_literal=effective,
                    manifest_lit="",
                    anchor_after=anchor["anchor_after"],
                )
            except FormatterRecoveryError as exc:
                _miss(f"formatter: {exc}")
                continue
            if selection is None:
                _miss("no formatter")
                continue
            if selection.presentation_only:
                raw_value = None
                fmt = recover_presentation_formatter(
                    source_literal=effective,
                    manifest_lit="",
                    anchor_after=anchor["anchor_after"],
                )
                fmt["formatter_evidence_mode"] = selection.source
                fmt["rejected_occurrence_raw"] = selection.rejected_occurrence_raw
            else:
                raw_value = selection.raw
                fmt = recover_formatter(
                    source_literal=effective,
                    raw_value=raw_value,
                    manifest_lit="",
                    anchor_after=anchor["anchor_after"],
                )
                fmt["formatter_raw_source"] = selection.source
                if selection.rejected_occurrence_raw is not None:
                    fmt["rejected_occurrence_raw"] = selection.rejected_occurrence_raw
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
            "binding_raw": raw_value,
            "anchor_before": anchor["anchor_before"],
            "anchor_after": anchor["anchor_after"],
            "anchor_sha256": anchor["anchor_sha256"],
            "component_id": occ.get(oid, {}).get("ui_location_identifier"),
            "formatter": fmt,
            "status_behavior": "UNKNOWN_ON_NON_OK",
            "notes": None,
        }
        if ".price.usd" in mid or ".etf.flow." in mid or "fear_greed" in mid:
            bound_once.add(mid)
        if ".price.usd" in mid:
            priced.add(asset_key.upper())
        out.append(entry)
    return out


def build_manifest(html_path: Path | None = None) -> dict[str, Any]:
    reg, plan, manifest_meta, mappings = load_job1_job2()
    occ_list = json.loads((ROOT / "metrics/ui-occurrences.json").read_text(encoding="utf-8"))["occurrences"]
    occ = {o["occurrence_id"]: o for o in occ_list}
    elig = eligible_mappings(mappings, reg, plan)
    path = html_path or HTML_PATH
    html = path.read_text(encoding="utf-8")
    blockers: list[dict[str, Any]] = []
    bindings = _assign_bindings(html, elig, occ, reg, blockers)
    return {
        "schema_version": "job3.binding.v1",
        "source_html": path.name,
        "source_html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "job1_registry_sha256": hashlib.sha256((ROOT / "metrics/metric-registry.json").read_bytes()).hexdigest(),
        "eligible_occurrences": len(elig),
        "bindings": bindings,
        "blockers": blockers,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--html", default="")
    p.add_argument("--out", default=str(MANIFEST_PATH))
    args = p.parse_args()
    html_path = Path(args.html) if args.html else None
    built = build_manifest(html_path)
    blockers = built.pop("blockers")
    blocker_path = Path(args.out).with_name("blockers.json")
    blocker_path.write_text(json.dumps(blockers, indent=2) + "\n", encoding="utf-8")
    critical = [b for b in blockers if b.get("critical")]
    if args.check:
        committed = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if committed != built:
            print("binding manifest drift", file=sys.stderr)
            return 1
        print("binding manifest check OK")
        return 0
    Path(args.out).write_text(json.dumps(built, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} bindings={len(built['bindings'])} critical={len(critical)}")
    if critical:
        print(f"blockers critical={len(critical)} total={len(blockers)} file={blocker_path}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
