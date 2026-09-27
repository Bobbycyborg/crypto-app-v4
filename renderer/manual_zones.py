"""Mark stance text that the pull does not fill. The writer must not invent it."""

from __future__ import annotations

import re

_STANCE = re.compile(r'(<p class="alt-stance-expl">.*?</p>)', re.S)


def wrap_manual_zones(html: str, report_number: str) -> str:
    def repl(match: re.Match[str]) -> str:
        block = match.group(1)
        if "MANUAL:zone" in block:
            return block
        return f"<!-- MANUAL:zone report={report_number} -->{block}<!-- /MANUAL:zone -->"

    return _STANCE.sub(repl, html)
