"""Week dropdown. The live week comes from config/report.json."""

from __future__ import annotations

import re

from renderer.report_config import load_report


def _weeks() -> tuple[tuple[str, str], ...]:
    return tuple((num, label) for num, label in load_report()["weeks"])


def live_number() -> str:
    return str(load_report()["live_number"])

_MENU_RE = re.compile(
    r'(<div class="week-menu" role="listbox">)\s*.*?(</div>)',
    re.S,
)


def href_for(num: str, *, from_baselines: bool) -> str:
    live = live_number()
    if from_baselines:
        return "../index-v4.html" if num == live else f"report-{num}.html"
    return "index-v4.html" if num == live else f"baselines/report-{num}.html"


def menu_inner(*, current: str, from_baselines: bool) -> str:
    lines = []
    for num, label in _weeks():
        cls = ' class="week-opt is-current"' if num == current else ' class="week-opt"'
        href = href_for(num, from_baselines=from_baselines)
        lines.append(
            f'          <a{cls} href="{href}" role="option">\n'
            f'            <span class="week-opt-date">{label}</span>\n'
            f"          </a>"
        )
    return "\n".join(lines)


def apply_week_menu(html: str, *, current: str, from_baselines: bool) -> str:
    inner = menu_inner(current=current, from_baselines=from_baselines)
    new, n = _MENU_RE.subn(
        rf"\g<1>\n{inner}\n        \g<2>",
        html,
        count=1,
    )
    if n != 1:
        raise RuntimeError(f"WEEK_MENU_REPLACE_FAIL:{n}")
    return new
