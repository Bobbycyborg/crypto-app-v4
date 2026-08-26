"""Extract every visible numerical token from Report 01 HTML."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

NUM_RE = re.compile(
    r"(?:"
    r"\$\s?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*[kKmMbBtT])?"
    r"|~\s*\$\s?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*[kKmMbBtT])?"
    r"|-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*%"
    r"|-?\d+(?:\.\d+)?\s*[×x]"
    r"|\b\d+\s+of\s+\d+\b"
    r"|-?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:[kKmMbBtT])\b"
    r")"
)

SKIP_TAGS = {"script", "style", "svg", "path", "polyline", "line", "circle"}
VALUE_CLASSES = {
    "hold-px",
    "hold-owned",
    "alt-price",
    "metric-value",
    "proto-line",
    "fg-dial-num",
    "econ-dial-num",
    "fx-kpi",
    "metric-val",
    "amt",
    "rc-item-line",
    "rc-item-title",
    "mkt-lead-item",
    "alt-signal-read",
    "flag-title",
    "flag-detail",
    "wcm-if",
    "hero-price",
}


class _Node:
    __slots__ = ("tag", "cls", "id", "attrs", "parent", "children", "text")

    def __init__(self, tag: str, attrs: dict[str, str], parent: _Node | None):
        self.tag = tag
        self.attrs = attrs
        self.cls = attrs.get("class", "")
        self.id = attrs.get("id", "")
        self.parent = parent
        self.children: list[_Node] = []
        self.text: list[str] = []


class _Tree(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("document", {}, None)
        self._stack = [self.root]
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self._skip += 1
            return
        if self._skip:
            return
        ad = {k: (v or "") for k, v in attrs}
        node = _Node(tag, ad, self._stack[-1])
        self._stack[-1].children.append(node)
        if tag not in {"br", "img", "meta", "link", "input", "hr"}:
            self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS:
            if self._skip:
                self._skip -= 1
            return
        if self._skip:
            return
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                break

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if data and data.strip():
            self._stack[-1].text.append(data)


def _joined(node: _Node) -> str:
    parts = list(node.text)
    for ch in node.children:
        t = _joined(ch)
        if t:
            parts.append(t)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def _has_class(node: _Node, name: str) -> bool:
    return name in node.cls.split()


def _find(node: _Node, pred, out: list[_Node] | None = None) -> list[_Node]:
    acc = out if out is not None else []
    if pred(node):
        acc.append(node)
    for ch in node.children:
        _find(ch, pred, acc)
    return acc


def _asset_of(node: _Node) -> str:
    cur: _Node | None = node
    while cur:
        if cur.tag == "article" and "asset-v3-report" in cur.cls.split():
            return cur.attrs.get("data-asset") or "UNKNOWN_ASSET"
        if cur.tag == "section" and cur.attrs.get("aria-label") == "Market intelligence":
            return "MARKET"
        if cur.tag == "section" and "holdings" in cur.cls.split():
            return "HOLDINGS"
        cur = cur.parent
    return "PAGE"


def _label_near(node: _Node) -> str:
    if _has_class(node, "hold"):
        tick = _find(node, lambda n: _has_class(n, "hold-ticker"))
        return _joined(tick[0]) if tick else "holding"
    parent = node.parent
    if parent:
        for ch in parent.children:
            if _has_class(ch, "label") or _has_class(ch, "econ-dial-label") or ch.tag == "span" and "fx-kpi" in (parent.cls or ""):
                t = _joined(ch)
                if t and t not in ("", "·"):
                    return t[:80]
        if parent.tag == "div" and "fx-kpi" in parent.cls.split():
            spans = [c for c in parent.children if c.tag == "span"]
            if spans:
                return _joined(spans[-1])[:80]
    return node.cls.split()[0] if node.cls else node.tag


def extract_fields(html: str) -> list[dict[str, Any]]:
    parser = _Tree()
    parser.feed(html)
    root = parser.root
    fields: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    def add(node: _Node, section: str) -> None:
        text = _joined(node)
        if not text:
            return
        nums = NUM_RE.findall(text)
        if not nums:
            return
        asset = _asset_of(node)
        label = _label_near(node)
        key = (asset, section, label, text[:180])
        if key in seen:
            return
        seen.add(key)
        fields.append(
            {
                "asset": asset,
                "visible_section": section,
                "visible_label": label,
                "report_01_text": text[:400],
                "numbers": nums,
                "css_class": node.cls,
            }
        )

    for node in _find(root, lambda n: _has_class(n, "hold")):
        add(node, "holdings_strip")
    for name in VALUE_CLASSES:
        for node in _find(root, lambda n, nm=name: _has_class(n, nm)):
            if _has_class(node, "hold"):
                continue
            section = "market_top" if _asset_of(node) == "MARKET" else "asset_body"
            if _has_class(node, "alt-price"):
                section = "hero"
            if _has_class(node, "econ-dial-num") or _has_class(node, "econ-dial"):
                section = "mini_dash"
            if "rc-" in node.cls:
                section = "risk_confirmation"
            if "fx-" in node.cls:
                section = "forensics_or_fingerprint"
            if "wcm" in node.cls:
                section = "what_would_change_mind"
            add(node, section)

    return fields
