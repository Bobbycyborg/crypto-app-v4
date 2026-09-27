"""Fail the build when the page still shows last week's numbers or junk."""

from __future__ import annotations

import re
from datetime import datetime

from renderer.coin_span import coin_regions
from renderer.formatters import format_value
from renderer.report_config import dormant_assets, load_report

_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")
_REPEAT = re.compile(r"(\b7d\b)\s+\1|\(row above\)\s+\(row above\)", re.I)
_LONG_DECIMAL = re.compile(r"\d+\.\d{5,}")
_MANUAL = re.compile(r"<!-- MANUAL:zone report=(\d+) -->")
_ALLOW = ("1 aug", "2026-08-01", "ath", "launch")


def _article(html: str, slug: str) -> str | None:
    regions = coin_regions(html, slug)
    for start, end in regions:
        if html[start:start + 8].lower().startswith("<article"):
            return html[start:end]
    return None


def stale_problems(
    html: str,
    *,
    snapshot: dict | None = None,
    bindings: list | None = None,
    previous_html: str | None = None,
    report_number: str | None = None,
) -> list[str]:
    cfg = load_report()
    previous = datetime.strptime(cfg["previous_report_date"], "%Y-%m-%d")
    number = report_number or cfg["report_number"]
    problems: list[str] = []

    for match in _DATE.finditer(html):
        found = datetime.strptime(match.group(0), "%Y-%m-%d")
        if found.date() >= previous.date():
            continue
        window = html[max(0, match.start() - 40) : match.end() + 40].lower()
        if any(word in window for word in _ALLOW):
            continue
        problems.append(f"stale date {match.group(0)}")
        break

    if _REPEAT.search(html):
        problems.append("repeated token")
    if _LONG_DECIMAL.search(html):
        problems.append("more than 4 decimal places")

    for match in _MANUAL.finditer(html):
        if match.group(1) != number:
            problems.append(f"manual zone report={match.group(1)}")

    if previous_html is not None:
        for asset in sorted(dormant_assets()):
            now = _article(html, asset)
            old = _article(previous_html, asset)
            if now != old:
                problems.append(f"dormant article changed {asset}")

    metrics = (snapshot or {}).get("metrics") or {}
    unknown = 0
    held = {c.upper() for c in cfg["held"]} | {c.upper() for c in cfg["always_shown"]}
    for binding in bindings or []:
        asset = (binding.get("asset") or "").upper()
        if asset not in held:
            continue
        art = _article(html, asset)
        if art and art.count("UNKNOWN") > 0:
            unknown += art.count("UNKNOWN")
        metric = metrics.get(binding.get("metric_id"))
        if not metric or metric.get("status") != "OK":
            continue
        try:
            fresh = format_value(metric.get("normalized_value"), binding.get("formatter") or {})
        except Exception:
            continue
        old = binding.get("source_literal") or ""
        if not old or fresh == old or fresh == "UNKNOWN":
            continue
        combo = f"{binding.get('anchor_before', '')}{old}{binding.get('anchor_after', '')}"
        if combo and combo in html:
            problems.append(f"stale value {binding.get('binding_id')}")
    if unknown:
        problems.append(f"UNKNOWN in a held coin article ({unknown})")
    return problems
