"""Copy Oliver's approved stance. Do not invent one from the numbers."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_FILE = ROOT / "config" / "stances.json"
_PROCESS = re.compile(r"not re-fetched|this pass|were not re-fetched", re.I)
_PCT = re.compile(r"([+−\-]\d+(?:\.\d+)?)\s*%\s*/\s*(7d|30d)", re.I)
_BULLET_PCT = re.compile(r"([+−\-]\d+(?:\.\d+)?)\s*%.*\b(7d|30d)\b|\b(7d|30d)\b.*?([+−\-]\d+(?:\.\d+)?)\s*%", re.I)


def load_stances() -> dict:
    if not _FILE.is_file():
        return {}
    data = json.loads(_FILE.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _lis(items: list[str]) -> str:
    return "".join(f"<li>{item}</li>" for item in items)


def _block(stance: dict) -> tuple[str, str]:
    summary = stance["summary"]
    modal = (
        f"<p class='stance-conf'>Evidence confidence · MEDIUM</p>"
        f"<p class='stance-p'>{stance['why']}</p>"
        f"<section class='stance-sec'><h3 class='stance-h'>What supports it</h3>"
        f"<ul class='stance-list'>{_lis(stance['supports'])}</ul></section>"
        f"<section class='stance-sec'><h3 class='stance-h'>What holds it back</h3>"
        f"<ul class='stance-list'>{_lis(stance['holds_back'])}</ul></section>"
        f"<section class='stance-sec'><h3 class='stance-h'>What would change it</h3>"
        f"<div class='stance-change'><div><h4 class='stance-h4'>Stronger if</h4>"
        f"<ul class='stance-list'>{_lis(stance['stronger'])}</ul></div>"
        f"<div><h4 class='stance-h4'>Weaker if</h4>"
        f"<ul class='stance-list'>{_lis(stance['weaker'])}</ul></div></div></section>"
    )
    return summary, modal


def _headline_percents(text: str) -> dict[str, str]:
    found = {}
    for sign, window in _PCT.findall(text):
        found[window.lower()] = sign.replace("-", "−").replace("+", "+")
    return found


def _drop_bad_bullets(html: str) -> str:
    def one_list(match: re.Match[str]) -> str:
        body = match.group(1)
        article_start = html.rfind("<article", 0, match.start())
        article = html[article_start:match.start()] if article_start >= 0 else ""
        headline = _headline_percents(re.sub(r"<[^>]+>", " ", article))
        kept = []
        for item in re.findall(r"<li>(.*?)</li>", body, re.S):
            plain = re.sub(r"<[^>]+>", " ", item)
            if _PROCESS.search(plain):
                continue
            percents = _BULLET_PCT.findall(plain)
            bad = False
            for a, b, c, d in percents:
                window = (b or c).lower()
                sign = (a or d).replace("-", "−")
                if window not in headline or headline[window] != sign:
                    bad = True
            if bad:
                continue
            kept.append(item)
        return "<ul class='stance-list'>" + "".join(f"<li>{item}</li>" for item in kept) + "</ul>"

    return re.sub(r"<ul class='stance-list'>(.*?)</ul>", one_list, html, flags=re.S)


def _strip_process_sentences(html: str) -> str:
    return re.sub(r"\s*[^.<>]*not re-fetched this pass\.", "", html)


def apply_approved_stances(html: str) -> str:
    stances = load_stances()
    for slug, stance in stances.items():
        marker = f'data-asset="{slug}"'
        start = html.find(marker)
        if start < 0:
            continue
        end = html.find("<article", start + 1)
        if end < 0:
            end = len(html)
        block = html[start:end]
        summary, modal = _block(stance)
        block = re.sub(
            r'(<div class="alt-stance-headline">)[^<]*(</div>)',
            rf"\1{stance['title']}\2",
            block,
            count=1,
        )
        block = re.sub(
            r'(<p class="alt-stance-expl">).*?(<button type="button" class="stance-see-more">)',
            rf"\1{summary} \2",
            block,
            count=1,
            flags=re.S,
        )
        block = re.sub(
            r'(<div class="stance-modal-src" hidden>).*?(<div class="econ-dash")',
            lambda m, modal=modal: m.group(1) + modal + "</div></div>" + m.group(2),
            block,
            count=1,
            flags=re.S,
        )
        html = html[:start] + block + html[end:]
    return _strip_process_sentences(_drop_bad_bullets(html))
