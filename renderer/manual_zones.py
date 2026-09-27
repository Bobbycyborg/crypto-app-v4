"""Mark stance text the pull does not fill.

These lines are not stamped as this week's report. A person still has to edit them.
"""

from __future__ import annotations

import re

_STANCE = re.compile(r'(<p class="alt-stance-expl">)(.*?)(</p>)', re.S)
_MARKER = "<!-- MANUAL:zone needs-human-edit -->"


def wrap_manual_zones(html: str, report_number: str | None = None) -> str:
    del report_number

    def repl(match: re.Match[str]) -> str:
        block = match.group(0)
        if "MANUAL:zone" in block:
            return block
        return f"{_MARKER}{block}<!-- /MANUAL:zone -->"

    return _STANCE.sub(repl, html)


def manual_zone_notes(html: str) -> list[str]:
    from renderer.report_config import dormant_assets

    dormant = {asset.lower() for asset in dormant_assets()}
    notes = []
    for match in _STANCE.finditer(html):
        start = html.rfind("<article", 0, match.start())
        tag = html[start : start + 180] if start >= 0 else ""
        owner = re.search(r'data-asset="([^"]+)"', tag)
        if owner and owner.group(1).lower() in dormant:
            continue
        text = re.sub(r"<[^>]+>", " ", match.group(2))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            notes.append(text[:80])
    return notes
