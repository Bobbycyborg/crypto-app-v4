"""Weekly V3 product QA — read-only. Does not repair research or edit canonical."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from lib.v3.weekly_config import configured_slugs, latest_v3_json, ticker_aliases, v3_json_name

RECOMMENDATION = re.compile(r"\b(BUY|SELL|HOLD|WAIT|REDUCE)\b")
HOLD_CALL_SPAN = re.compile(
    r'<span class="hold-call([^"]*)">([^<]*)</span>',
    re.I,
)
ARTICLE_RE = re.compile(
    r'(<article[^>]*data-asset="([^"]+)"[^>]*>.*?</article>)',
    re.S,
)
TICKER_RE = re.compile(r'<h2 class="alt-ticker">([^<]+)</h2>')


def _finding(status: str, check: str, detail: str, **extra: Any) -> dict[str, Any]:
    row = {"status": status, "check": check, "detail": detail}
    row.update(extra)
    return row


def _load_html(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_asset_articles(html: str, slugs: tuple[str, ...]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    articles = {m.group(2): m.group(1) for m in ARTICLE_RE.finditer(html)}
    for slug in slugs:
        art = articles.get(slug)
        if not art:
            findings.append(_finding("FAIL", "article_present", f"missing <article data-asset={slug}>", slug=slug))
            continue
        findings.append(_finding("PASS", "article_present", "present", slug=slug))
        m = TICKER_RE.search(art)
        want = ticker_aliases(slug)
        got = (m.group(1).strip() if m else "")
        if got not in want:
            findings.append(
                _finding(
                    "FAIL",
                    "ticker_identity",
                    f"expected {want}, got {got or '(none)'} — possible wrong pack / contamination",
                    slug=slug,
                )
            )
        else:
            findings.append(_finding("PASS", "ticker_identity", got, slug=slug))
        if "Current Stance" not in art and "alt-stance" not in art:
            findings.append(_finding("FAIL", "current_stance", "Current Stance block missing", slug=slug))
        else:
            findings.append(_finding("PASS", "current_stance", "present", slug=slug))
        # Foreign tickers as this article's hero ticker already covered.
        # Extra: another asset's exact h2 ticker string must not appear as this article's ticker.
    extra = sorted(set(articles) - set(slugs))
    if extra:
        findings.append(_finding("WARN", "unexpected_articles", f"extra data-asset values: {extra}"))
    findings.append(
        _finding(
            "PASS" if len(articles) >= len(slugs) else "FAIL",
            "asset_count",
            f"{len(articles)} articles found; configured {len(slugs)}: {list(slugs)}",
        )
    )
    return findings


def check_hold_calls(html: str) -> list[dict[str, Any]]:
    """Non-empty hold-call labels fail. Do not rely only on grepping HOLD/WAIT in the whole page."""
    findings: list[dict[str, Any]] = []
    nonempty: list[str] = []
    recs: list[str] = []
    for cls, text in HOLD_CALL_SPAN.findall(html):
        label = text.strip()
        if not label:
            continue
        nonempty.append(label)
        if RECOMMENDATION.search(label):
            recs.append(label)
    if nonempty:
        findings.append(
            _finding(
                "FAIL",
                "hold_call_blank",
                f"non-empty hold-call label(s): {nonempty[:12]}",
            )
        )
    else:
        findings.append(_finding("PASS", "hold_call_blank", "all hold-call chips empty"))
    if recs:
        findings.append(
            _finding("FAIL", "hold_call_recommendation", f"recommendation text in hold-call: {recs}")
        )
    else:
        findings.append(_finding("PASS", "hold_call_recommendation", "no BUY/SELL/HOLD/WAIT/REDUCE in hold-call"))
    return findings


def check_path_leak(html: str) -> list[dict[str, Any]]:
    if "/Users/" in html:
        return [_finding("FAIL", "internal_path_leak", "/Users/ present in rendered HTML")]
    return [_finding("PASS", "internal_path_leak", "no /Users/ leak")]


def check_unknown_not_fail(report_dir: Path | None, slugs: tuple[str, ...]) -> list[dict[str, Any]]:
    """Presence of UNKNOWN in asset JSON is legitimate — must not FAIL the weekly run."""
    findings: list[dict[str, Any]] = []
    if not report_dir or not report_dir.is_dir():
        findings.append(_finding("WARN", "unknown_preserved", "no dated report dir to scan"))
        return findings
    seen = 0
    missing_json = []
    for slug in slugs:
        path = None
        if report_dir:
            candidate = report_dir / v3_json_name(slug)
            if candidate.is_file():
                path = candidate
        if path is None:
            path = latest_v3_json(slug)
        if path is None or not path.is_file():
            missing_json.append(slug)
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(_finding("FAIL", "asset_json_parse", str(exc), slug=slug, path=str(path)))
            continue
        blob = json.dumps(doc)
        if "UNKNOWN" in blob:
            seen += 1
    if missing_json:
        findings.append(
            _finding("FAIL", "required_asset_json", f"missing V3 JSON for: {missing_json}")
        )
    else:
        findings.append(_finding("PASS", "required_asset_json", f"all {len(slugs)} dated V3 JSON files present"))
    findings.append(
        _finding(
            "PASS",
            "unknown_preserved",
            f"{seen} asset JSON file(s) contain UNKNOWN — treated as evidence, not pipeline failure",
        )
    )
    return findings


def check_pump_hero(html: str) -> list[dict[str, Any]]:
    from lib.v3.autojob01.apply_pump_hero import pump_hero_gaps

    gaps = pump_hero_gaps(html)
    if gaps:
        return [_finding("FAIL", "pump_hero_minidash", f"missing: {gaps}")]
    return [_finding("PASS", "pump_hero_minidash", "8-cell PUMP hero present")]


def run_product_qa(
    html_path: Path,
    report_dir: Path | None,
    *,
    slugs: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    slugs = slugs or configured_slugs()
    html = _load_html(html_path)
    findings: list[dict[str, Any]] = []
    findings.extend(check_asset_articles(html, slugs))
    findings.extend(check_hold_calls(html))
    findings.extend(check_path_leak(html))
    findings.extend(check_unknown_not_fail(report_dir, slugs))
    findings.extend(check_pump_hero(html))
    summary = {
        "FAIL": sum(1 for f in findings if f["status"] == "FAIL"),
        "WARN": sum(1 for f in findings if f["status"] == "WARN"),
        "PASS": sum(1 for f in findings if f["status"] == "PASS"),
    }
    status = "FAIL" if summary["FAIL"] else "PASS"
    return {
        "status": status,
        "html_path": str(html_path),
        "report_dir": str(report_dir) if report_dir else None,
        "asset_count": len(slugs),
        "assets": list(slugs),
        "summary": summary,
        "findings": findings,
    }
