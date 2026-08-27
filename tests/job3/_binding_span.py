"""Exact binding span extraction for Job 3 tests."""

from __future__ import annotations

from typing import Any


def _nth_before_index(html: str, before: str, combo_start: int) -> int:
    occ = 0
    pos = 0
    while pos <= combo_start:
        i = html.find(before, pos)
        if i < 0 or i > combo_start:
            break
        occ += 1
        if i == combo_start or combo_start >= i:
            last = i
        pos = i + 1
    # combo_start points at start of full combo; before starts combo
    assert html.startswith(before, combo_start), (combo_start, before[:40])
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


def rendered_span(rendered: str, binding: dict[str, Any], *, source: str | None = None) -> str:
    before = binding["anchor_before"]
    after = binding["anchor_after"]
    literal = binding["source_literal"]
    if source is not None:
        combo = before + literal + after
        src_at = source.index(combo)
        nth = _nth_before_index(source, before, src_at)
        occ = 0
        pos = 0
        while pos < len(rendered):
            i = rendered.find(before, pos)
            if i < 0:
                break
            occ += 1
            if occ == nth:
                start = i + len(before)
                end = rendered.find(after, start)
                if end < 0:
                    raise ValueError(f"missing anchor_after for {binding['binding_id']}")
                return rendered[start:end]
            pos = i + 1
        raise ValueError(f"rendered missing before occurrence {nth} for {binding['binding_id']}")
    start = rendered.index(before) + len(before)
    end = rendered.index(after, start)
    return rendered[start:end]
