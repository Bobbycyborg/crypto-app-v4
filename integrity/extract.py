"""HTML extraction via Job3 anchor contract — no renderer imports."""

from __future__ import annotations

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

VALUE_FLEX = (
    r"(?:UNKNOWN|~?[\+\-−]?(?:\$)?[\d,]+(?:\.\d+)?"
    r"(?:[eE][+\-−]?\d+)?(?:[kKmMbBtT]|%|pp|×|x)?(?:\s*/\s*\w+)?)"
)
MAX_TARGET_CHARS = 240
SEARCH_PAD = 900


def extract_articles(html: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in ARTICLE_RE.finditer(html)}


def _combo(binding: dict[str, Any]) -> str:
    return binding["anchor_before"] + binding["source_literal"] + binding["anchor_after"]


def _peer_literals(bindings: list[dict[str, Any]], exclude_id: str) -> list[tuple[str, str]]:
    return sorted(
        [
            (b["binding_id"], b["source_literal"])
            for b in bindings
            if b.get("owner") == "CGPT_CURSOR"
            and b.get("field", "value") == "value"
            and b["binding_id"] != exclude_id
            and b.get("source_literal")
        ],
        key=lambda x: -len(x[1]),
    )


_PERIOD_LABEL_GAP = re.compile(r"(\\ ·\\ )\d+d\\ ")


def _relax_period_labels(pattern: str) -> str:
    """UNKNOWN renders may drop period labels (7d / 30d) before sibling values."""
    return _PERIOD_LABEL_GAP.sub(r"\1(?:\\d+d\\ )?", pattern)


def _mask_fragment_regex(fragment: str, exclude_id: str, bindings: list[dict[str, Any]]) -> str:
    if not fragment:
        return ""
    peers = _peer_literals(bindings, exclude_id)
    parts: list[str] = []
    i = 0
    while i < len(fragment):
        matched: str | None = None
        for _bid, lit in peers:
            if fragment.startswith(lit, i):
                matched = lit
                break
        if matched:
            parts.append(VALUE_FLEX)
            i += len(matched)
            continue
        nxt = len(fragment)
        for _bid, lit in peers:
            j = fragment.find(lit, i + 1)
            if j >= 0:
                nxt = min(nxt, j)
        parts.append(re.escape(fragment[i:nxt]))
        i = nxt
    return _relax_period_labels("".join(parts))


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


def _skip_leading_sibling(before: str, rendered: str, value_start: int) -> int:
    if not re.search(r"\$[\d.,]+[kKmMbBtT]?\s*·\s*$", before):
        return value_start
    m = re.match(r"\$[\d.,]+[kKmMbBtT]?\s*·\s*", rendered[value_start:])
    return value_start + m.end() if m else value_start


def _find_before(rendered: str, before: str, start: int = 0) -> tuple[int, int] | None:
    for key in _before_search_keys(before):
        pos = rendered.find(key, start)
        if pos >= 0:
            value_start = pos + len(key)
            if key != before:
                value_start = _skip_leading_sibling(before, rendered, value_start)
            return pos, value_start
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
                value_start = pos + len(suffix)
                if key != before:
                    value_start = _skip_leading_sibling(before, rendered, value_start)
                return pos, value_start
    return None


def _masked_after_fragment(after: str) -> str:
    """Use the first closing span — avoids overspan into sibling rows."""
    if "</span>" in after:
        return after[: after.index("</span>") + len("</span>")]
    return after


def _masked_window_locate(
    rendered_html: str,
    binding: dict[str, Any],
    *,
    source_html: str,
    bindings: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    """Structural masked locate in a source-aligned window — no canonical values."""
    before = binding["anchor_before"]
    after = binding["anchor_after"]
    literal = binding["source_literal"]
    bid = binding["binding_id"]
    combo = before + literal + after
    if combo not in source_html or source_html.count(combo) != 1:
        return None, "source_combo_missing"
    src_at = source_html.index(combo)
    win_start = max(0, src_at - SEARCH_PAD)
    win_end = min(len(rendered_html), src_at + len(combo) + SEARCH_PAD)
    window = rendered_html[win_start:win_end]
    before_pat = _mask_fragment_regex(before, bid, bindings)
    after_pat = _mask_fragment_regex(_masked_after_fragment(after), bid, bindings)
    prefix = (binding.get("formatter") or {}).get("literal_prefix") or ""
    if prefix:
        capture = rf"(?P<val>(?:{re.escape(prefix)})?{VALUE_FLEX})"
    else:
        capture = rf"(?P<val>{VALUE_FLEX})"
    pattern = before_pat + capture + after_pat
    try:
        rx = re.compile(pattern, re.S)
    except re.error:
        return None, "pattern_error"
    matches = list(rx.finditer(window))
    if len(matches) != 1:
        return None, "rendered_before_missing" if len(matches) == 0 else "anchor_after_overspan"
    val = matches[0].group("val")
    if len(val) > MAX_TARGET_CHARS or "</" in val or "><" in val:
        return None, "anchor_after_overspan"
    return val, None


def locate_binding_span(
    rendered_html: str,
    binding: dict[str, Any],
    *,
    source_html: str | None = None,
    bindings: list[dict[str, Any]] | None = None,
    expected_numeric: float | None = None,
) -> tuple[str | None, str | None]:
    """Return (span_text, error). Location is structure-only — no canonical values."""
    _ = expected_numeric
    before = binding["anchor_before"]
    after = binding["anchor_after"]
    literal = binding["source_literal"]
    fmt = binding.get("formatter") or {}

    combo = before + literal + after
    if rendered_html.count(combo) == 1:
        start = rendered_html.index(combo) + len(before)
        end = start + len(literal)
        return rendered_html[start:end], None

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
        stripped = raw.strip()
        if stripped.upper() == "UNKNOWN":
            return "UNKNOWN"
        if fmt.get("type") == "string_exact":
            return raw
        prefix = fmt.get("literal_prefix") or ""
        if " · " in stripped and prefix:
            tail = stripped.rsplit(" · ", 1)[-1].strip()
            if tail.upper() == "UNKNOWN":
                stripped = tail
        s2 = _strip_prefix_suffix(stripped)
        if s2 != raw.strip():
            return s2
        # Exact token only — never substring-match inside a longer overspan.
        if _DISPLAY_TOKEN_RE.fullmatch(stripped):
            return stripped
        m = _DISPLAY_TOKEN_RE.match(stripped)
        if m and m.end() == len(stripped):
            return m.group(0)
        return stripped

    def _extract_at(start: int) -> tuple[str | None, str | None]:
        end = _find_after(rendered_html, start, after)
        if end < 0 and bindings is not None:
            after_pat = _mask_fragment_regex(
                _masked_after_fragment(after), binding["binding_id"], bindings
            )
            m = re.search(after_pat, rendered_html[start : start + MAX_TARGET_CHARS + 200], re.S)
            if m:
                end = start + m.start()
        if end < 0:
            return None, "anchor_after_missing"
        raw = rendered_html[start:end]
        if len(raw) > MAX_TARGET_CHARS or "</" in raw or "><" in raw:
            return None, "anchor_after_overspan"
        return _finalize(raw), None

    if source_html is not None and bindings is not None:
        masked = _masked_window_locate(
            rendered_html,
            binding,
            source_html=source_html,
            bindings=bindings,
        )
        if masked[0] is not None:
            return _finalize(masked[0]), None
        combo = before + literal + after
        if combo not in source_html:
            return None, "source_combo_missing"
        src_at = source_html.index(combo)
        try:
            nth = _nth_before_index(source_html, before, src_at)
        except ValueError:
            return None, "before_occurrence_not_found"
        occ = 0
        pos = 0
        nth_span: tuple[str | None, str | None] | None = None
        while pos < len(rendered_html):
            found = _find_before(rendered_html, before, pos)
            if found is None:
                break
            match_pos, start = found
            if match_pos < pos:
                break
            occ += 1
            if occ == nth:
                nth_span = _extract_at(start)
                break
            pos = max(match_pos + 1, start)
        if nth_span is not None and nth_span[0] is not None:
            return nth_span
        if rendered_html.count(before) == 1:
            found = _find_before(rendered_html, before)
            if found:
                return _extract_at(found[1])
        return masked if masked[1] else (None, "rendered_before_missing")

    if rendered_html.count(combo) != 1:
        return None, f"combo_count_{rendered_html.count(combo)}"
    start = rendered_html.index(combo) + len(before)
    end = start + len(literal)
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
