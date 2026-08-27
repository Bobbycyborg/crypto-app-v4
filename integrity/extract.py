"""HTML extraction via Job3 anchor contract — no renderer imports."""

from __future__ import annotations

import re
import re
from typing import Any

ARTICLE_RE = re.compile(
    r'<article[^>]*data-asset="([^"]+)"[^>]*>(.*?)</article>',
    re.S,
)

_DISPLAY_TOKEN_RE = re.compile(
    r"^[~+\-−]?"
    r"(?:\$)?[\d,]+(?:\.\d+)?(?:[eE][+\-−]?\d+)?"
    r"(?:[kKmMbBtT]|%|pp|×|x)?"
    r"(?:\s*/\s*\w+)?"
)


def extract_articles(html: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in ARTICLE_RE.finditer(html)}


def _nth_before_index(html: str, before: str, combo_start: int) -> int:
    occ = 0
    pos = 0
    while True:
        i = html.find(before, pos)
        if i < 0:
            raise ValueError("before occurrence not found")
        occ += 1
        if i == combo_start:
            return occ
        pos = i + 1


def _first_display_token(text: str) -> str:
    m = _DISPLAY_TOKEN_RE.match(text.strip())
    if m:
        return m.group(0)
    stripped = text.strip()
    return stripped.split()[0] if stripped else ""


def _find_after(rendered: str, start: int, after: str) -> int:
    pos = rendered.find(after, start)
    if pos >= 0:
        return pos
    min_len = 20
    best = -1
    for i in range(1, len(after)):
        suffix = after[i:]
        if len(suffix) < min_len:
            continue
        pos = rendered.find(suffix, start)
        if pos >= 0 and (best < 0 or pos < best):
            best = pos
    return best


def _before_search_keys(before: str) -> list[str]:
    keys = [before]
    stripped = re.sub(r"\$[\d.,]+[kKmMbBtT]?\s*·\s*", "", before)
    stripped = re.sub(r"~?[\d.,]+[kKmMbBtT%]?\s*·\s*", "", stripped)
    if stripped and stripped not in keys:
        keys.append(stripped)
    return keys


def _flex_anchor_pattern(anchor: str) -> re.Pattern[str]:
    """Allow numeric tokens in anchors to differ between source and rendered."""
    chunks = re.split(r"(~[\d.]+|\d+\.\d+\.|\$[\d.,]+[kKmMbBtT]?)", anchor)
    parts: list[str] = []
    for ch in chunks:
        if not ch:
            continue
        if re.fullmatch(r"~[\d.]+", ch):
            parts.append(r"~[\d.]+")
        elif re.fullmatch(r"\d+\.\d+\.", ch):
            parts.append(r"[\d.]+\.?")
        elif re.match(r"\$[\d.,]+", ch):
            parts.append(r"\$[\d.,]+[kKmMbBtT]?")
        else:
            parts.append(re.escape(ch))
    return re.compile("".join(parts), re.S)


def _find_before(rendered: str, before: str, start: int = 0) -> tuple[int, int] | None:
    """Return (match_pos, value_start) for anchor_before, with suffix fallback."""
    for key in _before_search_keys(before):
        pos = rendered.find(key, start)
        if pos >= 0:
            return pos, pos + len(key)
    m = _flex_anchor_pattern(before).search(rendered, start)
    if m:
        return m.start(), m.end()
    min_len = 20
    for key in _before_search_keys(before):
        for i in range(max(0, len(key) - min_len)):
            suffix = key[i:]
            if len(suffix) < min_len:
                continue
            pos = rendered.find(suffix, start)
            if pos >= 0:
                return pos, pos + len(suffix)
    return None


def locate_binding_span(
    rendered_html: str,
    binding: dict[str, Any],
    *,
    source_html: str | None = None,
    expected_numeric: float | None = None,
) -> tuple[str | None, str | None]:
    """Return (span_text, error). Uses anchor_before + anchor_after."""
    before = binding["anchor_before"]
    after = binding["anchor_after"]
    literal = binding["source_literal"]
    fmt = binding.get("formatter") or {}

    def _strip_prefix_suffix(text: str) -> str:
        s = text.strip()
        prefix = fmt.get("literal_prefix") or ""
        suffix = fmt.get("literal_suffix") or ""
        if prefix and s.startswith(prefix):
            s = s[len(prefix) :]
        if suffix and s.endswith(suffix):
            s = s[: -len(suffix)]
        return s.strip()

    def _finalize(raw: str) -> str:
        if fmt.get("type") == "string_exact":
            return raw
        if raw == literal:
            return raw
        stripped = _strip_prefix_suffix(raw)
        if stripped != raw:
            return stripped
        return _first_display_token(raw)

    def _extract_at(start: int) -> tuple[str | None, str | None]:
        end = _find_after(rendered_html, start, after)
        if end < 0:
            return None, "anchor_after_missing"
        raw = rendered_html[start:end]
        if len(raw) > 300 or "</" in raw or "><" in raw:
            return None, "anchor_after_overspan"
        return _finalize(raw), None

    if source_html is not None:
        combo = before + literal + after
        if combo not in source_html:
            return None, "source_combo_missing"
        src_at = source_html.index(combo)
        try:
            nth = _nth_before_index(source_html, before, src_at)
        except ValueError:
            return None, "before_occurrence_not_found"
        candidates: list[tuple[str, str | None]] = []
        occ = 0
        pos = 0
        while pos < len(rendered_html):
            found = _find_before(rendered_html, before, pos)
            if found is None:
                break
            match_pos, start = found
            occ += 1
            span, err = _extract_at(start)
            if err is None and span is not None:
                candidates.append((span, None))
            if occ == nth and err is None:
                return span, None
            pos = match_pos + 1
        if expected_numeric is not None and candidates:
            from integrity.numeric import dec, parse_display_token, values_compatible

            for span, _ in candidates:
                obs = parse_display_token(span)
                if values_compatible(obs, dec(expected_numeric), fmt):
                    return span, None
        if rendered_html.count(before) == 1:
            found = _find_before(rendered_html, before)
            if found:
                start = found[1]
                return _extract_at(start)
        if candidates:
            return candidates[0]
        return None, "rendered_before_missing"
    combo = before + literal + after
    if rendered_html.count(combo) != 1:
        return None, f"combo_count_{rendered_html.count(combo)}"
    start = rendered_html.index(combo) + len(before)
    end = start + len(binding["source_literal"])
    return rendered_html[start:end], None


def classify_surface(binding: dict[str, Any]) -> str:
    ctx = (
        binding.get("anchor_before", "")
        + binding.get("component_id", "")
        + binding.get("anchor_after", "")
    ).lower()
    if "ev-tip" in ctx or "metric-tip" in ctx:
        return "tooltip"
    if "ddbar" in ctx or "ddbar-fill" in ctx:
        return "visual"
    if "alt-price" in ctx or "desk-px" in ctx:
        return "hero"
    if "research" in ctx or "census" in ctx:
        return "research_census"
    if "wcm" in ctx:
        return "wcm"
    if "risk" in ctx:
        return "risk_line"
    if "hold" in ctx or "desk-" in ctx:
        return "hold_card"
    return "body"


def extract_stance_headline(article_html: str) -> str | None:
    m = re.search(
        r'<div class="alt-stance-headline">([^<]+)</div>',
        article_html,
        re.I,
    )
    return m.group(1).strip() if m else None


def extract_visual_bar_width(article_html: str) -> int | None:
    m = re.search(r'<div class="ddbar-fill" style="width:(\d+)%">', article_html)
    return int(m.group(1)) if m else None
