"""Fail the build when visible text still shows last week's numbers or junk."""

from __future__ import annotations

import argparse
import json
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
_ALLOW = re.compile(r"\b(?:1 aug|ath|launch)\b|2026-08-01", re.I)
# Leftovers from the week before this report. A new page must not still say these.
_KNOWN_STALE = (
    "BEAR MARKET",
    "$79,374",
    "$79,073",
    "bounce is gone",
    "2026-08-25",
    "As of 2026-08-25",
    "$104.45",
    "$1.43",
    "$1.84B",
    "$3.28B",
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


_PRICE_NODE = re.compile(r'class="(?:alt-price|desk-px|hold-px)"[^>]*>([^<]+)')


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


def _cross_coin(html: str, bindings: list | None) -> list[str]:
    """Only values a binding wrote. Shared prose that is not a bound value stays out."""
    found: dict[str, set[str]] = {}
    for binding in bindings or []:
        asset = (binding.get("asset") or "").upper()
        literal = (binding.get("source_literal") or "").strip()
        if not asset or len(literal) < 4:
            continue
        if literal not in html:
            continue
        art = _article(html, asset)
        if art and literal in art:
            found.setdefault(asset, set()).add(literal)
    problems = []
    assets = list(found)
    for i, left in enumerate(assets):
        for right in assets[i + 1 :]:
            shared = found[left] & found[right]
            if shared:
                sample = sorted(shared)[0]
                problems.append(f"{sample} is in both {left} and {right}")
    return problems


def _quiet_slugs() -> set[str]:
    from renderer.coin_span import _slugs

    cfg = load_report()
    slugs: set[str] = set()
    for asset in list(cfg.get("dormant") or []) + list(cfg.get("hidden") or []):
        slugs.update(name.lower() for name in _slugs(asset))
    return slugs


def _without_quiet_pages(html: str) -> str:
    """Dormant and hidden coin pages are not this week's stale count."""
    for slug in _quiet_slugs():
        html = re.sub(
            rf'<article\b[^>]*\bdata-asset="{re.escape(slug)}".*?</article>',
            " ",
            html,
            count=1,
            flags=re.I | re.S,
        )
    return html


def _copied_phrases(html: str, earlier: str | None, label: str, seen: set[str]) -> list[str]:
    """Numbered lines copied from an earlier page. Not a fixed list of words."""
    if not earlier:
        return []
    problems = []
    text = visible_text(html)
    for chunk in re.split(r"\.\s+|\n|·", visible_text(earlier)):
        phrase = " ".join(chunk.split())
        words = phrase.split()
        has_number = "$" in phrase or "%" in phrase or re.search(r"\d", phrase)
        claim = "bounce is gone" in phrase.lower() or "bear market" in phrase.lower()
        if len(phrase) < 8 or len(phrase) > 140:
            continue
        if not has_number and not claim:
            continue
        if len(words) < 3 and not ("$" in phrase or "%" in phrase):
            continue
        if _ALLOW.search(phrase) or re.search(r"Report 0\d", phrase):
            continue
        if phrase in text and phrase not in seen:
            seen.add(phrase)
            problems.append(f"stale phrase from {label}: {phrase[:90]}")
    return problems


def stale_problems(
    html: str,
    *,
    snapshot: dict | None = None,
    bindings: list | None = None,
    previous_html: str | None = None,
    base_html: str | None = None,
    report_number: str | None = None,
) -> list[str]:
    cfg = load_report()
    previous = datetime.strptime(cfg["previous_report_date"], "%Y-%m-%d")
    number = report_number or cfg["report_number"]
    scoped = _without_quiet_pages(html)
    text = visible_text(scoped)
    problems: list[str] = []
    seen_phrases: set[str] = set()

    problems.extend(_copied_phrases(scoped, _without_quiet_pages(previous_html) if previous_html else None, "last week", seen_phrases))
    if base_html and base_html != previous_html:
        problems.extend(_copied_phrases(scoped, _without_quiet_pages(base_html), "the base page", seen_phrases))

    seen_dates: set[str] = set()
    for match in _DATE.finditer(text):
        found = datetime.strptime(match.group(0), "%Y-%m-%d")
        if found.date() >= previous.date():
            continue
        window = text[max(0, match.start() - 48) : match.end() + 48]
        if _ALLOW.search(window):
            continue
        stamp = match.group(0)
        if stamp not in seen_dates:
            seen_dates.add(stamp)
            problems.append(f"stale date {stamp}")

    if _REPEAT.search(text):
        problems.append("repeated token")

    for match in _LONG_DECIMAL.finditer(text):
        number_text = match.group(1).replace(",", "")
        if Decimal(number_text) < Decimal("0.01"):
            continue
        problems.append("more than 4 decimal places")
        break

    for match in _MANUAL.finditer(html):
        if match.group(1) != number:
            problems.append(f"manual zone report={match.group(1)}")

    problems.extend(_cross_coin(html, bindings))

    problems.extend(_old_stamps_on_changed_cards(html, snapshot, previous))
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
        if art and re.search(r'class="(?:alt-price|desk-px|hold-px)"[^>]*>UNKNOWN<', art):
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


def _old_stamps_on_changed_cards(html: str, snapshot: dict | None, previous: datetime) -> list[str]:
    """A card we just refreshed must not still carry last week's source date."""
    metrics = (snapshot or {}).get("metrics") or {}
    cfg = load_report()
    problems = []
    for asset in list(cfg["held"]) + list(cfg["always_shown"]):
        row = metrics.get(f"{asset.lower()}.price.usd.live")
        if not row or row.get("status") != "OK":
            continue
        art = _article(html, asset)
        if not art:
            continue
        for match in _DATE.finditer(visible_text(art)):
            found = datetime.strptime(match.group(0), "%Y-%m-%d")
            if found.date() >= previous.date():
                continue
            window = visible_text(art)[max(0, match.start() - 48) : match.end() + 48]
            if _ALLOW.search(window):
                continue
            problems.append(f"old source stamp {asset} {match.group(0)}")
            break
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if the page still shows stale text")
    parser.add_argument("--html", required=True)
    parser.add_argument("--previous-html", default="")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--bindings", required=True)
    args = parser.parse_args()
    html = Path(args.html).read_text(encoding="utf-8")
    previous = Path(args.previous_html).read_text(encoding="utf-8") if args.previous_html else None
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    bindings = json.loads(Path(args.bindings).read_text(encoding="utf-8"))
    if isinstance(bindings, dict):
        bindings = bindings.get("bindings") or []
    problems = stale_problems(html, snapshot=snapshot, bindings=bindings, previous_html=previous)
    if not problems:
        print("stale gate PASS")
        return 0
    print("stale gate FAIL")
    for item in problems:
        print(item)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
