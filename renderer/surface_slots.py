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

_NODE = re.compile(r'(class="(?:alt-price|desk-px|hold-px)"[^>]*>)([^<]+)')


def one_price(value: object) -> str:
    num = Decimal(str(value))
    if num >= 1000:
        if num == num.to_integral_value():
            shown = num.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            return f"${shown:,.0f}"
        shown = num.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"${shown:,.2f}"
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
    blank = re.search(rf'(?:UNKNOWN|STALE)(\s*)(?=<span class="u">{window}</span>)', body)
    if blank:
        unit_span = f'<span class="u-unit">{unit}</span> ' if unit else ""
        new_body = body[: blank.start()] + amount + unit_span + body[blank.end() :]
        return html[: row.start()] + new_body + html[row.end() :]
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
    from renderer.coin_span import _element_containing

    card = re.search(r'class="[^"]*\bfg-card\b', html)
    if not card:
        return html
    span = _element_containing(html, card.start())
    if not span:
        return html
    start, end = span
    block = html[start:end]
    match = re.search(r"As of · [^<·]+", block)
    if not match or not source_as_of or not re.match(r"20\d\d-\d\d-\d\d", source_as_of):
        return html
    when = datetime.strptime(source_as_of[:10], "%Y-%m-%d")
    pretty = f"{when.day} {when.strftime('%b')} {when.year}"
    block = block[: match.start()] + f"As of · {pretty} " + block[match.end() :]
    return html[:start] + block + html[end:]


def _clear_unknown_burn(html: str, snapshot: dict) -> str:
    row = (snapshot.get("metrics") or {}).get("sol.burn.tokens.per_year") or {}
    if row.get("status") == "OK":
        return html
    html = html.replace("burn ~255,690 SOL/yr", "burn UNKNOWN")
    html = html.replace("burn ~255,690", "burn UNKNOWN")
    html = html.replace(
        "<strong>~255,690/yr</strong><span>Burn</span>",
        "<strong>UNKNOWN</strong><span>Burn</span>",
    )
    return html


def _fart_leverage_card(html: str, snapshot: dict) -> str:
    row = _metric(snapshot, "fart.leverage.perp_spot_notional.x")
    if not row:
        return html
    shown = f"~{Decimal(str(row['normalized_value'])).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}×"
    match = re.search(r'<article\b[^>]*data-asset="fartcoin"', html)
    if not match:
        return html
    end = html.find("</article>", match.start())
    if end < 0:
        return html
    end += len("</article>")
    block = html[match.start() : end]
    block = block.replace(
        '<span class="ev-k">Ratio</span><span class="ev-v">~0.1×</span>',
        f'<span class="ev-k">Ratio</span><span class="ev-v">{shown}</span>',
    )
    block = block.replace(
        '<div class="fx-ev-k">Ratio</div><div class="fx-ev-v">~0.1×</div>',
        f'<div class="fx-ev-k">Ratio</div><div class="fx-ev-v">{shown}</div>',
    )
    return html[: match.start()] + block + html[end:]


def restore_dormant_articles(html: str, previous: str) -> str:
    from renderer.report_config import dormant_assets

    for asset in dormant_assets():
        slug = asset.lower()

        def grab(src: str) -> str | None:
            match = re.search(rf'<article\b[^>]*data-asset="{re.escape(slug)}"', src)
            if not match:
                return None
            end = src.find("</article>", match.start())
            if end < 0:
                return None
            return src[match.start() : end + len("</article>")]

        old = grab(previous)
        now = grab(html)
        if old and now and old != now:
            html = html.replace(now, old, 1)
    return html


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
    html = _clear_unknown_burn(html, snapshot)
    return _fart_leverage_card(html, snapshot)


def price_slot_bindings(html: str, snapshot: dict) -> list[dict]:
    """One checker row per hold, desk, and hero price, so mixed prices fail."""
    cfg = load_report()
    node = re.compile(r'class="(alt-price|desk-px|hold-px)"[^>]*>([^<]+)')
    rows: list[dict] = []
    for asset in list(cfg["always_shown"]) + list(cfg["held"]):
        slug = asset.lower()
        metric = _metric(snapshot, f"{slug}.price.usd.live", f"{slug}.price.usd.report")
        if not metric:
            continue
        mid = f"{slug}.price.usd.live"
        n = 0
        for start, end in coin_regions(html, asset):
            for match in node.finditer(html, start, end):
                text = match.group(2)
                places = 0
                if "." in text:
                    places = len(text.split(".", 1)[1].rstrip("%"))
                before = html[max(0, match.start(2) - 90) : match.start(2)]
                after = html[match.end(2) : match.end(2) + 40]
                rows.append(
                    {
                        "binding_id": f"{mid}::price-slot-{match.group(1)}-{n}",
                        "metric_id": mid,
                        "asset": slug,
                        "owner": "CGPT_CURSOR",
                        "job1_occurrence_id": f"price-slot-{n}",
                        "target_kind": "HTML_TEXT",
                        "field": "value",
                        "source_literal": text,
                        "anchor_before": before,
                        "anchor_after": after,
                        "formatter": {
                            "type": "numeric",
                            "currency_prefix": "$",
                            "grouping": True,
                            "decimal_places": places,
                            "scale": 1,
                        },
                        "status_behavior": "UNKNOWN_ON_NON_OK",
                    }
                )
                n += 1
    return rows
