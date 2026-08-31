"""Week dropdown for every report page. Report 05 is live index-v4.html."""

from __future__ import annotations

import re

WEEKS = (
    ("01", "August 14th, 2026 - Report 01"),
    ("02", "August 17th, 2026 - Report 02"),
    ("03", "August 20th, 2026 - Report 03"),
    ("04", "August 25th, 2026 - Report 04"),
    ("05", "August 31st, 2026 - Report 05"),
)

_MENU_RE = re.compile(
    r'(<div class="week-menu" role="listbox">)\s*.*?(</div>)',
    re.S,
)


def href_for(num: str, *, from_baselines: bool) -> str:
    if from_baselines:
        return "../index-v4.html" if num == "05" else f"report-{num}.html"
    return "index-v4.html" if num == "05" else f"baselines/report-{num}.html"


def menu_inner(*, current: str, from_baselines: bool) -> str:
    lines = []
    for num, label in WEEKS:
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
