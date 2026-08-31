#!/usr/bin/env python3
"""Static shadow renderer — exact anchor replacements from canonical snapshot."""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderer.formatters import format_value
from renderer.frozen_reports import refuse_frozen_write
from renderer.semantic_wording import apply_semantic_wording
from renderer.week_nav import apply_week_menu

RENDERER_VERSION = "job3-v1"
NON_OK = frozenset(
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


_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ordinal(day: int) -> str:
    if 11 <= day <= 13:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suf}"


def apply_report_header(html: str, snapshot: dict[str, Any], source_html: str) -> str:
    """Add a new week. Never rename a previous report in the dropdown."""
    run_id = str(snapshot.get("source_run_id") or "")
    if "SYNTHETIC" in run_id.upper():
        return html
    parsed = re.match(r"^(\d{4})(\d{2})(\d{2})T", run_id)
    if not parsed:
        return html
    dt = date(int(parsed.group(1)), int(parsed.group(2)), int(parsed.group(3)))
    new_date = f"{_MONTHS[dt.month - 1]} {_ordinal(dt.day)}, {dt.year}"
    title_m = re.search(r"<title>([^<]+)</title>", source_html)
    if not title_m:
        return html
    old = title_m.group(1).strip()
    report_m = re.search(r"Report\s+(\d+)", old)
    if not report_m:
        return html
    new_n = int(report_m.group(1)) + 1
    new_header = f"{new_date} - Report {new_n:02d}"
    html = re.sub(r"<title>[^<]+</title>", f"<title>{new_header}</title>", html, count=1)
    html = re.sub(
        r'(<button class="week-btn"[^>]*>\s*<span>)[^<]+(</span>)',
        rf"\g<1>{new_header}\g<2>",
        html,
        count=1,
    )
    return apply_week_menu(html, current=f"{new_n:02d}", from_baselines=False)



def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _find_anchor(html: str, binding: dict[str, Any]) -> tuple[int, int]:
    combo = binding["anchor_before"] + binding["source_literal"] + binding["anchor_after"]
    if html.count(combo) != 1:
        raise RuntimeError(f"anchor mismatch for {binding['binding_id']}: count={html.count(combo)}")
    start = html.index(combo) + len(binding["anchor_before"])
    end = start + len(binding["source_literal"])
    return start, end


def _render_text(binding: dict[str, Any], snapshot: dict[str, Any]) -> tuple[str, str]:
    mid = binding["metric_id"]
    rec = snapshot["metrics"].get(mid)
    if rec is None:
        return "UNKNOWN", "missing_metric"
    status = rec.get("status", "UNKNOWN")
    if status == "OUT_OF_SCOPE":
        raise RuntimeError(f"BOUND_OUT_OF_SCOPE_METRIC:{mid}")
    if status != "OK":
        return "UNKNOWN", "unknown_binding"
    val = rec.get("normalized_value")
    rendered = format_value(val, binding["formatter"], status="OK")
    if binding["target_kind"] in {"HTML_TEXT", "HTML_ATTRIBUTE"}:
        rendered = html_lib.escape(rendered, quote=binding["target_kind"] == "HTML_ATTRIBUTE")
    elif binding["target_kind"] == "JS_LITERAL":
        rendered = json.dumps(rendered)
    elif binding["target_kind"] == "JSON_LITERAL":
        rendered = json.dumps(rendered)
    return rendered, "ok"


def render_report(
    *,
    source_html: str,
    bindings: list[dict[str, Any]],
    snapshot: dict[str, Any],
    writer_quarantine: dict[str, Any],
    publishable: bool = False,
) -> tuple[str, dict[str, Any], int]:
    spans: list[tuple[int, int, str, dict[str, Any], str]] = []
    unknown_bindings = 0
    visual_unknown_bindings = 0
    for b in bindings:
        if b.get("field") != "value":
            continue
        start, end = _find_anchor(source_html, b)
        if start == end and b["target_kind"] != "STYLE_NUMBER":
            raise RuntimeError(f"zero-width binding {b['binding_id']}")
        text, kind = _render_text(b, snapshot)
        if kind == "unknown_binding":
            unknown_bindings += 1
        if b["target_kind"] == "STYLE_NUMBER":
            if kind != "ok":
                visual_unknown_bindings += 1
                text = "0"
            spans.append((start, end, text, b, kind))
        else:
            spans.append((start, end, text, b, kind))

    spans.sort(key=lambda x: x[0], reverse=True)
    used: list[tuple[int, int]] = []
    for start, end, _text, _b, _k in spans:
        if any(not (end <= u[0] or start >= u[1]) for u in used):
            raise RuntimeError("overlapping_binding during render")
        used.append((start, end))

    out = source_html
    style_attrs: dict[str, str] = {}
    for start, end, text, binding, kind in spans:
        if binding["target_kind"] == "STYLE_NUMBER" and kind != "ok":
            style_attrs[binding["binding_id"]] = "UNKNOWN"
        out = out[:start] + text + out[end:]

    patches = 0
    for w in writer_quarantine.get("writers", []):
        frag = w["source_fragment"]
        count = out.count(frag)
        if count != w["expected_match_count"]:
            raise RuntimeError(f"WRITER_QUARANTINE_MISMATCH:{w['writer_id']}:{count}")
        out = out.replace(frag, w["replacement_fragment"])
        patches += 1

    out = apply_semantic_wording(out, snapshot)
    out = apply_report_header(out, snapshot, source_html)

    for bid, state in style_attrs.items():
        # paired textual UNKNOWN already rendered; mark geometry neutral
        marker = f'data-v4-metric-state="{state}"'
        if marker not in out:
            pass

    manifest = {
        "renderer_version": RENDERER_VERSION,
        "source_html_sha256": _sha256_bytes(source_html.encode()),
        "binding_manifest_sha256": _sha256_bytes(json.dumps(bindings, sort_keys=True).encode()),
        "writer_quarantine_sha256": _sha256_bytes(json.dumps(writer_quarantine, sort_keys=True).encode()),
        "snapshot_sha256": _sha256_bytes(json.dumps(snapshot, sort_keys=True).encode()),
        "snapshot_source_run_id": snapshot.get("source_run_id"),
        "total_bindings": len(bindings),
        "successful_bindings": len(bindings) - unknown_bindings,
        "unknown_bindings": unknown_bindings,
        "visual_unknown_bindings": visual_unknown_bindings,
        "writer_patches_applied": patches,
        "output_sha256": _sha256_bytes(out.encode()),
        "publishable": publishable,
        "synthetic_notice": None if publishable else "SYNTHETIC TEST ONLY — NOT CURRENT DATA — NOT PUBLISHABLE",
    }
    exit_code = 0
    if unknown_bindings:
        exit_code = 2
    return out, manifest, exit_code


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot", required=True)
    p.add_argument("--source", default=str(ROOT / "index-v4.html"))
    p.add_argument("--bindings", default=str(ROOT / "renderer/binding-manifest.json"))
    p.add_argument("--writers", default=str(ROOT / "renderer/writer-quarantine.json"))
    p.add_argument("--out", required=True)
    p.add_argument("--manifest-out")
    p.add_argument("--publishable", action="store_true")
    args = p.parse_args()

    source_html = Path(args.source).read_text(encoding="utf-8")
    bindings = json.loads(Path(args.bindings).read_text())["bindings"]
    snapshot = json.loads(Path(args.snapshot).read_text())
    writers = json.loads(Path(args.writers).read_text())
    try:
        rendered, manifest, code = render_report(
            source_html=source_html,
            bindings=bindings,
            snapshot=snapshot,
            writer_quarantine=writers,
            publishable=args.publishable,
        )
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 3

    out = Path(args.out)
    refuse_frozen_write(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    tmp.replace(out)

    if args.manifest_out:
        mpath = Path(args.manifest_out)
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mtmp = mpath.with_suffix(".tmp")
        mtmp.write_text(json.dumps(manifest, indent=2) + "\n")
        mtmp.replace(mpath)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
