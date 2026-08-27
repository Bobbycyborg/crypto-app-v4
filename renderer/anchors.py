"""Deterministic HTML anchor resolution from Job 1 locators."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

TAG_RE = re.compile(r"<\s*(/?)\s*([a-zA-Z][\w:-]*)\b([^>]*)>", re.DOTALL)
VOID_TAGS = frozenset({"meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "param", "track", "wbr"})


@dataclass
class _Node:
    tag: str
    idx: int
    open_start: int
    inner_start: int
    inner_end: int = 0
    close_end: int = 0
    parent: "_Node | None" = None
    path: tuple[tuple[str, int], ...] = ()
    children: list["_Node"] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.children is None:
            self.children = []


@dataclass(frozen=True)
class HtmlIndex:
    html: str
    by_path: dict[tuple[tuple[str, int], ...], tuple[int, int]]


def parse_xpath_segments(xpath: str) -> tuple[tuple[str, int], ...]:
    parts = [p for p in xpath.strip("/").split("/") if p]
    out: list[tuple[str, int]] = []
    for part in parts:
        if part in {"html", "body"}:
            continue
        if "[" in part:
            tag, idx_s = part.split("[", 1)
            out.append((tag.lower(), int(idx_s.rstrip("]"))))
        else:
            out.append((part.lower(), 1))
    return tuple(out)


def build_html_index(html: str) -> HtmlIndex:
    root = _Node("root", 0, 0, 0)
    stack: list[_Node] = [root]
    counts: dict[int, dict[str, int]] = {id(root): {}}
    by_path: dict[tuple[tuple[str, int], ...], tuple[int, int]] = {}

    for m in TAG_RE.finditer(html):
        closing, tag, _attrs = m.group(1), m.group(2).lower(), m.group(3)
        if closing:
            while len(stack) > 1:
                node = stack.pop()
                node.inner_end = m.start()
                node.close_end = m.end()
                if node.tag == tag:
                    break
            continue
        parent = stack[-1]
        pc = counts.setdefault(id(parent), {})
        pc[tag] = pc.get(tag, 0) + 1
        idx = pc[tag]
        path = parent.path + ((tag, idx),)
        node = _Node(tag, idx, m.start(), m.end(), parent=parent, path=path)
        parent.children.append(node)
        if tag in VOID_TAGS:
            by_path[path] = (node.inner_start, node.close_end)
            continue
        stack.append(node)
        counts[id(node)] = {}

    for node in _walk(root):
        if node.tag == "root":
            continue
        if node.inner_end == 0:
            node.inner_end = node.inner_start
            node.close_end = node.inner_start
        by_path[node.path] = (node.inner_start, node.inner_end)

    return HtmlIndex(html=html, by_path=by_path)


def _walk(node: _Node):
    yield node
    for ch in node.children or []:
        yield from _walk(ch)


def _article_index_from_xpath(xpath: str | None) -> int | None:
    if not xpath:
        return None
    for part in xpath.strip("/").split("/"):
        if part.startswith("article["):
            try:
                return int(part.split("[", 1)[1].rstrip("]"))
            except ValueError:
                return None
    return None


def _article_bounds(html: str) -> list[tuple[int, int]]:
    bounds: list[tuple[int, int]] = []
    for m in re.finditer(r"<article\b", html, re.I):
        start = m.start()
        close = html.find("</article>", start)
        if close < 0:
            continue
        bounds.append((start, close + len("</article>")))
    return bounds


def _article_index_score(html: str, pos: int, xpath: str | None) -> int:
    idx = _article_index_from_xpath(xpath)
    if idx is None:
        return 0
    bounds = _article_bounds(html)
    if idx < 1 or idx > len(bounds):
        return 0
    start, end = bounds[idx - 1]
    if start <= pos < end:
        return 500
    return 0


def _path_at_position(index: HtmlIndex, pos: int) -> tuple[tuple[str, int], ...] | None:
    best: tuple[tuple[str, int], ...] | None = None
    best_len = 0
    for path, (start, end) in index.by_path.items():
        if start <= pos < end and len(path) > best_len:
            best_len = len(path)
            best = path
    return best


def _path_prefix_len(want: tuple[tuple[str, int], ...], got: tuple[tuple[str, int], ...]) -> int:
    n = 0
    for a, b in zip(want, got):
        if a == b:
            n += 1
        else:
            break
    return n


def _path_suffix_len(want: tuple[tuple[str, int], ...], got: tuple[tuple[str, int], ...]) -> int:
    n = 0
    for a, b in zip(reversed(want), reversed(got)):
        if a == b:
            n += 1
        else:
            break
    return n


def resolve_region(
    index: HtmlIndex,
    xpath: str,
    *,
    html: str | None = None,
    location_hint: str | None = None,
    literal: str | None = None,
) -> tuple[int, int] | None:
    path = parse_xpath_segments(xpath)
    if path in index.by_path:
        region = index.by_path[path]
        if html is None or not literal or locate_literal_in_region(html, region, literal):
            return region

    best_prefix = 0
    prefix_hits: list[tuple[tuple[str, int], ...]] = []
    for candidate in index.by_path:
        match = 0
        for want, got in zip(path, candidate):
            if want == got:
                match += 1
            else:
                break
        if match > best_prefix:
            best_prefix = match
            prefix_hits = [candidate]
        elif match == best_prefix and match > 0:
            prefix_hits.append(candidate)

    candidate_paths: list[tuple[tuple[str, int], ...]] = []
    if best_prefix > 0:
        candidate_paths = prefix_hits
    else:
        for plen in range(len(path), 0, -1):
            suffix = path[-plen:]
            hits = [p for p in index.by_path if p[-plen:] == suffix]
            if hits:
                candidate_paths = hits
                break

    if not candidate_paths:
        return None
    if len(candidate_paths) == 1 and html is not None and literal:
        region = index.by_path[candidate_paths[0]]
        if locate_literal_in_region(html, region, literal):
            return region
        return None
    if len(candidate_paths) == 1:
        return index.by_path[candidate_paths[0]]

    if html is None:
        return index.by_path[candidate_paths[0]]

    best: tuple[int, int] | None = None
    best_score = -1
    for hit_path in candidate_paths:
        start, end = index.by_path[hit_path]
        if literal and not locate_literal_in_region(html, (start, end), literal):
            continue
        score = (
            _location_score(html, start, location_hint)
            + _xpath_score(html, start, xpath)
            + _article_index_score(html, start, xpath)
            + best_prefix * 10
        )
        at = _path_at_position(index, start)
        if at is not None:
            score += _path_prefix_len(path, at) * 25
            score += _path_suffix_len(path, at) * 25
        if literal:
            score += 2000
        if score > best_score:
            best_score = score
            best = (start, end)
    return best


def _xpath_score(html: str, pos: int, xpath: str | None) -> int:
    if not xpath:
        return 0
    segs = parse_xpath_segments(xpath)
    if not segs:
        return 0
    window = html[max(0, pos - 4000) : pos + 200]
    score = 0
    cursor = len(window)
    for tag, _idx in reversed(segs):
        pat = re.compile(rf"<\s*{re.escape(tag)}\b[^>]*>", re.I)
        matches = list(pat.finditer(window[:cursor]))
        if not matches:
            return 0
        score += 5
        cursor = matches[-1].start()
    return score


LOCATION_HINTS: dict[str, tuple[str, ...]] = {
    "hero": ("alt-hero", "alt-price", "alt-ticker"),
    "market_layer": ("market-layer", "data-live-px", "market-intelligence"),
    "hold_card": ("hold-card", "data-live-px", "hold-ticker"),
    "mini_dash": ("mini-dash", "mini-dashboard"),
    "tooltip": ("metric-tip", "ev-tip", "ev-v"),
    "research_census": ("research-census", "census"),
    "wcm": ("wcm", "world-crypto"),
    "body": ("stance-", "alt-stance", "report"),
    "bar": ("bar-", "progress", "meter"),
    "modal": ("stance-modal", "modal"),
}


def _location_score(html: str, pos: int, hint: str | None) -> int:
    if not hint:
        return 0
    keys = LOCATION_HINTS.get(hint, (hint.replace("_", "-"),))
    window = html[max(0, pos - 500) : pos + 500].lower()
    return sum(10 for k in keys if k in window)


def _plain_text(fragment: str) -> str:
    return re.sub(r"<[^>]+>", "", fragment)


def locate_literal_in_region(html: str, region: tuple[int, int], literal: str) -> tuple[str, int] | None:
    start, end = region
    fragment = html[start:end]
    plain = _plain_text(fragment)
    rel = plain.find(literal)
    if rel < 0:
        stripped = fragment.strip()
        if stripped == literal:
            pos = html.find(stripped, start)
            return stripped, pos
        return None
    plain_end = rel + len(literal)
    plain_i = 0
    html_i = 0
    match_start = None
    match_end = None
    while html_i < len(fragment) and plain_i <= plain_end:
        if fragment[html_i] == "<":
            close = fragment.find(">", html_i)
            if close < 0:
                break
            html_i = close + 1
            continue
        if plain_i == rel:
            match_start = html_i
        if plain_i == plain_end:
            match_end = html_i
            break
        plain_i += 1
        html_i += 1
    if match_start is None:
        return None
    if match_end is None:
        match_end = html_i
    eff = fragment[match_start:match_end]
    return eff, start + match_start


def find_markup_literal(
    html: str,
    index: HtmlIndex,
    literal: str,
    *,
    xpath: str | None = None,
    location_hint: str | None = None,
) -> tuple[str, int] | None:
    if not literal:
        return None
    best: tuple[str, int] | None = None
    best_score = -1
    for start, end in index.by_path.values():
        if end - start > 160:
            continue
        fragment = html[start:end].strip()
        if not fragment:
            continue
        plain = _plain_text(fragment)
        if literal not in plain:
            continue
        if plain != literal and fragment.count("<") > 4:
            continue
        located = locate_literal_in_region(html, (start, end), literal)
        if not located:
            continue
        eff, pos = located
        score = (
            _location_score(html, pos, location_hint)
            + _xpath_score(html, pos, xpath)
            + _article_index_score(html, pos, xpath)
        )
        if score > best_score:
            best_score = score
            best = (eff, pos)
    return best


def extract_region_literal(
    html: str,
    index: HtmlIndex,
    xpath: str,
    *,
    location_hint: str | None = None,
) -> str | None:
    region = resolve_region(index, xpath, html=html, location_hint=location_hint)
    if not region:
        return None
    inner_start, inner_end = region
    fragment = html[inner_start:inner_end].strip()
    if not fragment:
        return None
    if "<" not in fragment:
        return fragment
    if len(fragment) <= 120 and fragment.count("<") <= 3:
        return fragment
    text = _plain_text(fragment)
    return text.strip() or None


def locate_literal(
    index: HtmlIndex,
    literal: str,
    xpath: str | None,
    *,
    location_hint: str | None = None,
    effective_literal: str | None = None,
) -> int | None:
    html = index.html
    lit = effective_literal or literal
    if not lit:
        return None
    positions: list[int] = []
    start = 0
    while True:
        i = html.find(lit, start)
        if i < 0:
            break
        positions.append(i)
        start = i + 1
    if not positions and xpath:
        region = resolve_region(index, xpath, html=html, location_hint=location_hint)
        if region:
            inner_start, inner_end = region
            rel = html[inner_start:inner_end].find(lit)
            if rel >= 0:
                positions = [inner_start + rel]
            elif html[inner_start:inner_end].strip() == lit:
                positions = [inner_start]
    if not positions:
        return None
    candidates: list[tuple[int, int]] = []
    for p in positions:
        try:
            build_anchor(html, p, lit)
        except ValueError:
            continue
        score = _location_score(html, p, location_hint) + _xpath_score(html, p, xpath) + _article_index_score(html, p, xpath)
        candidates.append((p, score))
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0][0]
    best = max(candidates, key=lambda x: x[1])
    top = [c for c in candidates if c[1] == best[1]]
    if len(top) == 1:
        return top[0][0]
    return None


def build_anchor(html: str, pos: int, literal: str) -> dict[str, Any]:
    for width in range(80, 401, 40):
        before = html[max(0, pos - width) : pos]
        after = html[pos + len(literal) : pos + len(literal) + width]
        combo = before + literal + after
        if html.count(combo) == 1:
            return {
                "anchor_before": before,
                "source_literal": literal,
                "anchor_after": after,
                "anchor_sha256": hashlib.sha256(combo.encode("utf-8")).hexdigest(),
            }
    raise ValueError("JOB3_AMBIGUOUS_BINDING_ANCHOR")


def classify_target_kind(html: str, pos: int, literal: str) -> str:
    before = html[max(0, pos - 120) : pos]
    after = html[pos + len(literal) : pos + len(literal) + 40]
    if re.search(r'style\s*=\s*"[^"]*$', before, re.I) and re.match(r"^[0-9.%]+", after):
        return "STYLE_NUMBER"
    if re.search(r"=\s*['\"]?$", before[-4:]):
        return "HTML_ATTRIBUTE"
    if re.search(r"<\s*script\b", before[-120:], re.I):
        if '"' in before[-30:] or "'" in before[-30:]:
            return "JS_LITERAL"
        return "JSON_LITERAL"
    if re.search(r">\s*$", before):
        return "HTML_TEXT"
    return "HTML_TEXT"
