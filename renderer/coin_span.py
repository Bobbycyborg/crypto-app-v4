"""Find one coin's own tags. Never search the rest of the page."""

from __future__ import annotations

import re

from renderer.report_config import load_report

_OPEN = re.compile(r"<([a-zA-Z0-9]+)\b")


def number_bounded(html: str, pos: int, literal: str) -> bool:
    """A number must not start or end inside another number."""
    if pos < 0 or pos + len(literal) > len(html):
        return False
    before = html[pos - 1] if pos else " "
    after = html[pos + len(literal)] if pos + len(literal) < len(html) else " "
    if before.isdigit() or after.isdigit():
        return False
    if before == "." and literal[:1].isdigit():
        return False
    if after == "." and literal[-1:].isdigit():
        return False
    if after == "," and pos + len(literal) + 1 < len(html) and html[pos + len(literal) + 1].isdigit():
        return False
    if before == "," and pos >= 2 and html[pos - 2].isdigit():
        return False
    if before == ":" or after == ":":
        return False
    return True


def _element_containing(html: str, attr_pos: int) -> tuple[int, int] | None:
    start = html.rfind("<", 0, attr_pos)
    if start < 0:
        return None
    m = _OPEN.match(html, start)
    if not m:
        return None
    tag = m.group(1)
    token = re.compile(rf"</?{tag}\b[^>]*?/?>", re.I)
    depth = 0
    for t in token.finditer(html, start):
        piece = t.group(0)
        if piece.startswith("</"):
            depth -= 1
            if depth == 0:
                return start, t.end()
        elif piece.endswith("/>"):
            if depth == 0:
                return start, t.end()
        else:
            depth += 1
    return None


def _slugs(asset: str) -> list[str]:
    key = asset.upper()
    names = load_report().get("desk_names", {}).get(key, [key])
    out = []
    for name in names:
        slug = name.lower()
        if slug not in out:
            out.append(slug)
    base = asset.lower()
    if base not in out:
        out.append(base)
    return out


def coin_regions(html: str, asset: str) -> list[tuple[int, int]]:
    if not asset:
        return []
    regions: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()

    def add(span: tuple[int, int] | None) -> None:
        if span and span not in seen and span[1] > span[0]:
            seen.add(span)
            regions.append(span)

    for slug in _slugs(asset):
        for m in re.finditer(rf'<article\b[^>]*\bdata-asset="{re.escape(slug)}"', html, re.I):
            end = html.find("</article>", m.start())
            if end >= 0:
                add((m.start(), end + len("</article>")))
        for attr in ("data-asset-slug", "data-asset"):
            for m in re.finditer(rf'\b{attr}="{re.escape(slug)}"', html, re.I):
                add(_element_containing(html, m.start()))
        for m in re.finditer(
            rf'<span class="desk-name">{re.escape(slug)}</span>',
            html,
            re.I,
        ):
            add(_element_containing(html, m.start()))
    return regions


def hits_in_regions(html: str, literal: str, regions: list[tuple[int, int]]) -> list[int]:
    if not literal or not regions:
        return []
    found: list[int] = []
    for start, end in regions:
        pos = start
        while True:
            i = html.find(literal, pos, end)
            if i < 0 or i + len(literal) > end:
                break
            if number_bounded(html, i, literal):
                found.append(i)
            pos = i + 1
    return found
