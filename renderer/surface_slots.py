"""Fill the price spots, the ETF box, and the BTC trend price from the snapshot.

Only those marked fields. Never the first dollar amount near a word.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from integrity.numeric import compact_usd_parts
from renderer.coin_span import coin_regions
from renderer.formatters import _four_sig
from renderer.report_config import load_report

_NODE = re.compile(r'(class="(?:alt-price|desk-px|hold-px)">)([^<]+)')


def one_price(value: object) -> str:
    num = Decimal(str(value))
    if num >= 1000:
        shown = num.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"${shown:,.0f}"
    if num >= 1:
        shown = num.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"${shown:.2f}"
    return f"${_four_sig(num)}"


def _metric(snapshot: dict, *names: str) -> dict | None:
    metrics = snapshot.get("metrics") or {}
    for name in names:
        row = metrics.get(name)
        if row and row.get("status") == "OK" and row.get("normalized_value") is not None:
            return row
    return None


def _replace_price_nodes(html: str, asset: str, text: str) -> str:
    regions = coin_regions(html, asset)
    spans: list[tuple[int, int]] = []
    for start, end in regions:
        for match in _NODE.finditer(html, start, end):
            spans.append((match.start(2), match.end(2)))
    for start, end in sorted(spans, reverse=True):
        html = html[:start] + text + html[end:]
    return html


def _replace_etf(html: str, ticker: str, window: str, amount: str, unit: str) -> str:
    row = re.search(rf'class="etf-row"><a [^>]*>{ticker}</a>.*?</div>', html)
    if not row:
        return html
    body = row.group(0)
    found = re.search(
        rf'\$[\d,.]+(?=<span class="u-unit">[^<]*</span>\s*<span class="u">{window}</span>)',
        body,
    )
    if not found:
        return html
    new_body = body[: found.start()] + amount + body[found.end() :]
    new_body = re.sub(
        rf'(<span class="u-unit">)[^<]*(</span>\s*<span class="u">{window}</span>)',
        rf"\g<1>{unit}\g<2>",
        new_body,
        count=1,
    )
    return html[: row.start()] + new_body + html[row.end() :]


def _trend_now_price(html: str, text: str) -> str:
    return re.sub(
        r"(BTC TREND</div>.*?ev-k\">Now</span><span class=\"ev-v\">.*?Price )\$[\d,]+",
        rf"\1{text}",
        html,
        count=1,
        flags=re.S,
    )


def _fear_date(html: str, source_as_of: str | None) -> str:
    match = re.search(r"As of · [^<·]+", html)
    if not match:
        return html
    if source_as_of and re.match(r"20\d\d-\d\d-\d\d", source_as_of):
        when = datetime.strptime(source_as_of[:10], "%Y-%m-%d")
        pretty = f"{when.day} {when.strftime('%b')} {when.year}"
        return html[: match.start()] + f"As of · {pretty} " + html[match.end() :]
    if "MANUAL:zone" in html[max(0, match.start() - 40) : match.start()]:
        return html
    marked = f"<!-- MANUAL:zone report=06 -->{match.group(0)}<!-- /MANUAL:zone -->"
    return html[: match.start()] + marked + html[match.end() :]


def apply_known_slots(html: str, snapshot: dict) -> str:
    cfg = load_report()
    for asset in list(cfg["always_shown"]) + list(cfg["held"]):
        slug = asset.lower()
        row = _metric(snapshot, f"{slug}.price.usd.live", f"{slug}.price.usd.report")
        if not row:
            continue
        html = _replace_price_nodes(html, asset, one_price(row["normalized_value"]))
    btc = _metric(snapshot, "btc.price.usd.live", "btc.price.usd.report")
    if btc:
        html = _trend_now_price(html, one_price(btc["normalized_value"]))
    for ticker, slug in (("BTC", "btc"), ("ETH", "eth"), ("SOL", "sol")):
        for window, metric in (("7D", f"{slug}.etf.flow.usd.7d"), ("30D", f"{slug}.etf.flow.usd.30d")):
            row = _metric(snapshot, metric)
            if not row:
                continue
            amount, unit, _neg = compact_usd_parts(row["normalized_value"])
            html = _replace_etf(html, ticker, window, amount, unit)
    fear = (snapshot.get("metrics") or {}).get("global.fear_greed.index.current") or {}
    html = _fear_date(html, fear.get("source_as_of") if isinstance(fear, dict) else None)
    return html
