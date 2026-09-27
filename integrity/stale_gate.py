"""Fail the build when visible text still shows last week's numbers or junk."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderer.coin_span import coin_regions
from renderer.formatters import format_value
from renderer.report_config import dormant_assets, load_report

_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")
_REPEAT = re.compile(r"(\b7d\b)\s+\1|\(row above\)\s+\(row above\)", re.I)
_LONG_DECIMAL = re.compile(r"\$?(\d[\d,]*\.\d{5,})")
_MANUAL = re.compile(r"<!-- MANUAL:zone report=(\d+) -->")
_ALLOW = re.compile(
    r"\b(?:1 aug|ath|launch|as of|freshness|coverage|unlock|vesting)\b|2026-08-01",
    re.I,
)
_PRICE = re.compile(r"\$\d[\d,]*(?:\.\d+)?(?:[kKmMbB])?")
_STRIP = (
    (re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S), " "),
    (re.compile(r"<style\b[^>]*>.*?</style>", re.I | re.S), " "),
    (re.compile(r"<svg\b[^>]*>.*?</svg>", re.I | re.S), " "),
    (re.compile(r"<[^>]+>"), " "),
)

def visible_text(html: str) -> str:
    text = html
    for pattern, repl in _STRIP:
        text = pattern.sub(repl, text)
    return text


def _article(html: str, slug: str) -> str | None:
    regions = coin_regions(html, slug)
    for start, end in regions:
        if html[start : start + 8].lower().startswith("<article"):
            return html[start:end]
    return None


_PRICE_NODE = re.compile(r'class="(?:alt-price|desk-px|hold-px)">([^<]+)')


def _fmt_price(value: object) -> str:
    from decimal import Decimal as D

    num = D(str(value))
    if num == num.to_integral_value() and num >= 1000:
        return f"${num:,.0f}"
    text = f"{num:.2f}".rstrip("0").rstrip(".")
    return f"${text}"


def _stale_against_previous(html: str, previous_html: str, snapshot: dict | None) -> list[str]:
    metrics = (snapshot or {}).get("metrics") or {}
    problems = []
    cfg = load_report()
    for asset in list(cfg["held"]) + list(cfg["always_shown"]):
        row = metrics.get(f"{asset.lower()}.price.usd.live") or metrics.get(f"{asset.lower()}.price.usd.report")
        if not row or row.get("status") != "OK" or row.get("normalized_value") is None:
            continue
        fresh = _fmt_price(row["normalized_value"])
        for match in _PRICE_NODE.finditer(previous_html):
            old = match.group(1).strip()
            if not old or old == fresh:
                continue
            slug = asset.lower()
            window_start = max(0, match.start() - 200)
            window = previous_html[window_start : match.end()]
            if f'data-asset-slug="{slug}"' not in window and f'data-asset="{slug}"' not in window:
                continue
            if old in html:
                problems.append(f"stale price {asset} {old}")
                break
    return problems


def _cross_coin(html: str) -> list[str]:
    cfg = load_report()
    names = list(cfg["held"]) + list(cfg["always_shown"]) + list(cfg["hidden"])
    found: dict[str, set[str]] = {}
    for asset in names:
        art = _article(html, asset)
        if not art:
            continue
        prices = set()
        for node in _PRICE_NODE.finditer(art):
            token = node.group(1).strip()
            if len(token) >= 5 and ("." in token or "," in token):
                prices.add(token)
        found[asset.upper()] = prices
    problems = []
    assets = list(found)
    for i, left in enumerate(assets):
        for right in assets[i + 1 :]:
            shared = found[left] & found[right]
            if shared:
                sample = sorted(shared)[0]
                problems.append(f"{sample} is in both {left} and {right}")
    return problems


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
    text = visible_text(html)
    problems: list[str] = []

    # Source stamps ("as of", freshness, an unlock date) are not the report date.
    # A bare date with none of those words still means the page is carrying an old stamp.
    for match in _DATE.finditer(text):
        found = datetime.strptime(match.group(0), "%Y-%m-%d")
        if found.date() >= previous.date():
            continue
        if match.end() < len(text) and text[match.end() : match.end() + 1] == "T":
            continue
        window = text[max(0, match.start() - 96) : match.end() + 24]
        if _ALLOW.search(window):
            continue
        if previous_html and match.group(0) in previous_html:
            continue
        problems.append(f"stale date {match.group(0)}")
        break

    if _REPEAT.search(text):
        problems.append("repeated token")

    for match in _LONG_DECIMAL.finditer(text):
        number_text = match.group(1).replace(",", "")
        if Decimal(number_text) < Decimal("1"):
            continue
        if previous_html and match.group(0) in previous_html:
            continue
        problems.append("more than 4 decimal places")
        break

    for match in _MANUAL.finditer(html):
        if match.group(1) != number:
            problems.append(f"manual zone report={match.group(1)}")

    problems.extend(_cross_coin(html))

    if previous_html is not None:
        problems.extend(_stale_against_previous(html, previous_html, snapshot))
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
        if art and "UNKNOWN" in visible_text(art):
            unknown += 1
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if the page still shows stale text")
    parser.add_argument("--html", required=True)
    parser.add_argument("--previous-html", default="")
    args = parser.parse_args()
    html = Path(args.html).read_text(encoding="utf-8")
    previous = Path(args.previous_html).read_text(encoding="utf-8") if args.previous_html else None
    problems = stale_problems(html, previous_html=previous)
    if not problems:
        print("stale gate PASS")
        return 0
    print("stale gate FAIL")
    for item in problems:
        print(item)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
