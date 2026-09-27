"""Fill written lines from the snapshot: prices, returns, ETF cells, ratios.

The stance judgment stays for a person. The numbers in those lines do not.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from integrity.numeric import compact_usd_parts
from renderer.coin_span import coin_regions
from renderer.formatters import format_value
from renderer.report_config import load_report
from renderer.surface_slots import _metric, one_price

_TICKER = {
    "BTC": "btc",
    "SOL": "sol",
    "ZEC": "zec",
    "HYPE": "hype",
    "PUMP": "pump",
    "RENDER": "render",
    "NOS": "nos",
    "SPX": "spx",
    "GIGA": "giga",
    "2Z": "2z",
    "FARTCOIN": "fart",
    "FART": "fart",
    "IO": "io",
}
_PROSE = re.compile(
    r"\b(BTC|SOL|ZEC|HYPE|PUMP|RENDER|NOS|SPX|GIGA|2Z|FARTCOIN|IO) \$[\d,]+(?:\.\d+)?"
    r"( \(\s*[+−\-][\d.]+%\s*/\s*7d,\s*[+−\-][\d.]+%\s*/\s*30d\))?"
)


def _pct(value: object) -> str:
    num = Decimal(str(value))
    sign = "+" if num > 0 else ("−" if num < 0 else "")
    shown = abs(num).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{sign}{shown}%"


def _pretty(stamp: str | None) -> str | None:
    if not stamp or not re.match(r"20\d\d-\d\d-\d\d", stamp):
        return None
    when = datetime.strptime(stamp[:10], "%Y-%m-%d")
    return f"{when.day} {when.strftime('%b')} {when.year}"


def _in_articles(html: str, asset: str, repl) -> str:
    for start, end in sorted(coin_regions(html, asset), key=lambda pair: pair[0], reverse=True):
        if not html[start:end].lower().startswith("<article"):
            continue
        html = html[:start] + repl(html[start:end]) + html[end:]
    return html


def _prose_prices(html: str, snapshot: dict) -> str:
    def repl(match: re.Match[str]) -> str:
        ticker = match.group(1)
        slug = _TICKER[ticker]
        price = _metric(snapshot, f"{slug}.price.usd.live", f"{slug}.price.usd.report")
        if not price:
            return match.group(0)
        text = f"{ticker} {one_price(price['normalized_value'])}"
        if match.group(2):
            week = _metric(snapshot, f"{slug}.return.pct.7d")
            month = _metric(snapshot, f"{slug}.return.pct.30d")
            week_txt = _pct(week["normalized_value"]) if week else "UNKNOWN"
            month_txt = _pct(month["normalized_value"]) if month else "UNKNOWN"
            text += f" ({week_txt} / 7d, {month_txt} / 30d)"
        return text

    return _PROSE.sub(repl, html)


def _as_of_stamps(html: str, snapshot: dict) -> str:
    cfg = load_report()

    def repl(asset: str):
        def one(block: str) -> str:
            row = _metric(snapshot, f"{asset.lower()}.price.usd.live")
            pretty = _pretty((row or {}).get("source_as_of"))
            if not pretty:
                return block
            return re.sub(r"As of · [^<·]+", f"As of · {pretty} ", block, count=1)

        return one

    for asset in list(cfg["always_shown"]) + list(cfg["held"]) + list(cfg["hidden"]):
        html = _in_articles(html, asset, repl(asset))
    fear = (snapshot.get("metrics") or {}).get("global.fear_greed.index.current") or {}
    pretty = _pretty(fear.get("source_as_of") if isinstance(fear, dict) else None)
    if pretty:
        card = re.search(r'class="[^"]*\bfg-card\b', html)
        if card:
            from renderer.coin_span import _element_containing

            span = _element_containing(html, card.start())
            if span:
                start, end = span
                block = re.sub(r"As of · [^<·]+", f"As of · {pretty} ", html[start:end], count=1)
                html = html[:start] + block + html[end:]
    return html


def _etf_cells(html: str, snapshot: dict) -> str:
    for ticker, slug in (("BTC", "btc"), ("ETH", "eth"), ("SOL", "sol")):
        for window, metric in (
            ("1D", f"{slug}.etf.flow.usd.1d"),
            ("7D", f"{slug}.etf.flow.usd.7d"),
            ("30D", f"{slug}.etf.flow.usd.30d"),
        ):
            row = (snapshot.get("metrics") or {}).get(metric) or {}
            if row.get("status") == "OK" and row.get("normalized_value") is not None:
                amount, unit, _neg = compact_usd_parts(row["normalized_value"])
                shown = amount
            else:
                shown, unit = "STALE", ""
            html = _replace_tip(html, ticker, window, shown, unit)
            if window == "30D" and slug in {"eth", "sol"}:
                html = _replace_tip(html, ticker, "ALL-TIME", "STALE", "")
            if window in {"7D", "30D"}:
                from renderer.surface_slots import _replace_etf

                if shown == "STALE":
                    html = _replace_etf(html, ticker, window, "STALE", "")
                elif row.get("status") == "OK":
                    html = _replace_etf(html, ticker, window, amount, unit)
    return html


def _replace_tip(html: str, ticker: str, window: str, amount: str, unit: str) -> str:
    start = html.find(f'class="etf-tip-asset">{ticker}<')
    if start < 0:
        return html
    nxt = html.find('class="etf-tip-asset">', start + 10)
    end = nxt if nxt > 0 else start + 1200
    block = html[start:end]
    found = re.search(
        rf'(<span class="ev-k">{window}</span><span class="ev-v[^"]*">)\$[\d,.]+(?:<span class="u-unit">[^<]*</span>)?',
        block,
    )
    if not found:
        return html
    unit_html = f'<span class="u-unit">{unit}</span>' if unit else ""
    piece = found.group(1) + amount + unit_html
    block = block[: found.start()] + piece + block[found.end() :]
    return html[:start] + block + html[end:]


def _flow_phrase(row: dict) -> str:
    if row.get("status") != "OK" or row.get("normalized_value") is None:
        return "UNKNOWN"
    amount, unit, negative = compact_usd_parts(row["normalized_value"])
    sign = "−" if negative else "+"
    return f"{sign}{amount}{unit}"


def _stance_etf(html: str, snapshot: dict) -> str:
    """Stance copies of the ETF box. A missing pull becomes UNKNOWN, not last month."""
    windows = (("1d", "1d"), ("7d", "7d"), ("30d", "30d"))

    def repl(slug: str):
        def one(block: str) -> str:
            for label, key in windows:
                row = (snapshot.get("metrics") or {}).get(f"{slug}.etf.flow.usd.{key}") or {}
                phrase = _flow_phrase(row)
                block = re.sub(
                    rf"{label} \+?\$[\d.,]+[MB]",
                    f"{label} {phrase}",
                    block,
                    flags=re.I,
                )
            return block

        return one

    for ticker, slug in (("BTC", "btc"), ("ETH", "eth"), ("SOL", "sol")):
        html = _in_articles(html, ticker, repl(slug))
    return html


def _clean_unknown(html: str) -> str:
    html = html.replace("+UNKNOWN", "UNKNOWN").replace("−UNKNOWN", "UNKNOWN")
    html = re.sub(r"(?<![A-Za-z])UNKNOWNM(?!M)", "UNKNOWN", html)
    html = re.sub(r"(?<![A-Za-z])UNKNOWN M(?=\s|,|\.|<|$)", "UNKNOWN", html)
    html = re.sub(r"UNKNOWN<span class=\"u-unit\">[^<]*</span>", "UNKNOWN", html)
    html = re.sub(r"(%/8h)(?:\.01%/8h)+", r"\1", html)
    return html


def _sol_lines(html: str, snapshot: dict) -> str:
    metrics = snapshot.get("metrics") or {}
    inf = _metric(snapshot, "sol.inflation.pct.current")
    if inf:
        text = f"{Decimal(str(inf['normalized_value'])).quantize(Decimal('0.01'))}%"

        def one(block: str) -> str:
            block = re.sub(r"(?i)(inflation\s+)[\d.]+%", lambda m: m.group(1) + text, block)
            block = re.sub(
                r"(<strong>)[\d.]+%(</strong><span>Inflation</span>)",
                rf"\g<1>{text}\g<2>",
                block,
            )
            return block

        html = _in_articles(html, "sol", one)
    net = metrics.get("sol.supply.net_change.tokens.per_year") or {}
    html = html.replace("net ~+20,281,672", "net UNKNOWN")
    html = html.replace("burn ~255,690 SOL/yr", "burn UNKNOWN")
    html = html.replace("burn ~255,690", "burn UNKNOWN")
    latest = _metric(snapshot, "sol.funding.rate.latest")
    if latest:
        sci = format_value(
            latest["normalized_value"],
            {"type": "numeric", "scientific": True, "decimal_places": 3, "exponent_pad": 2},
        )

        def fund(block: str) -> str:
            return re.sub(
                r"(latest funding print\s+)[-+0-9.e]+",
                lambda m, sci=sci: m.group(1) + sci,
                block,
            )

        html = _in_articles(html, "sol", fund)
    lev = _metric(snapshot, "sol.leverage.x.current")
    if lev:
        shown = f"~{Decimal(str(lev['normalized_value'])).quantize(Decimal('0.1'))}×"

        def spot(block: str) -> str:
            return block.replace("perps ~6.8×", f"perps {shown}")

        html = _in_articles(html, "sol", spot)
    return html


def _render_lines(html: str, snapshot: dict) -> str:
    ratio = _metric(snapshot, "render.bme.ratio.last4")
    lev = _metric(snapshot, "render.leverage.x.current")
    ratio_text = None
    if ratio:
        ratio_text = str(Decimal(str(ratio["normalized_value"])).quantize(Decimal("0.01")))

    def one(block: str) -> str:
        if ratio_text:
            block = block.replace("ratio ~0.21", f"ratio ~{ratio_text}")
            block = block.replace("burn/emit ~0.21", f"burn/emit ~{ratio_text}")
        if lev:
            shown = Decimal(str(lev["normalized_value"])).quantize(Decimal("0.1"))
            block = re.sub(r"fut/spot ~[\d.]+×", f"fut/spot ~{shown}×", block)
        return block

    html = _in_articles(html, "render", one)
    if ratio_text:
        html = html.replace("burn/emit ~0.21", f"burn/emit ~{ratio_text}")
        html = html.replace("ratio ~0.21", f"ratio ~{ratio_text}")
    return html


def _btc_lines(html: str, snapshot: dict) -> str:
    lev = _metric(snapshot, "btc.leverage.x.current")
    latest = _metric(snapshot, "btc.funding.rate.latest")
    mean = _metric(snapshot, "btc.funding.rate.mean_7d")

    def one(block: str) -> str:
        if lev:
            shown = Decimal(str(lev["normalized_value"])).quantize(Decimal("0.1"))
            block = re.sub(r"fut/spot ~[\d.]+×", f"fut/spot ~{shown}×", block)
        if latest:
            sci = format_value(
                latest["normalized_value"],
                {"type": "numeric", "scientific": True, "decimal_places": 3, "exponent_pad": 2},
            )
            block = block.replace("2.274e-03", sci)
        if mean:
            sci = format_value(
                mean["normalized_value"],
                {"type": "numeric", "scientific": True, "decimal_places": 3, "exponent_pad": 2},
            )
            block = block.replace("5.367e-05", sci)
        block = block.replace("As of 25 Aug · FRESH", "As of UNKNOWN")
        block = block.replace("As of · 25 Aug 2026 · FRESH", "As of · UNKNOWN")
        return block

    return _in_articles(html, "btc", one)


def _fart_lines(html: str, snapshot: dict) -> str:
    lev = _metric(snapshot, "fart.leverage.perp_spot_notional.x")
    if not lev:
        return html
    shown = f"~{Decimal(str(lev['normalized_value'])).quantize(Decimal('0.1'))}×"

    def one(block: str) -> str:
        block = block.replace("~7.0×", shown)
        block = block.replace("~$52.9M", "UNKNOWN")
        block = block.replace("~$7.6M", "UNKNOWN")
        return block

    return _in_articles(html, "fart", one)


def _one_io_price(html: str, snapshot: dict) -> str:
    row = _metric(snapshot, "io.price.usd.live", "io.price.usd.report")
    if not row:
        return html
    text = one_price(row["normalized_value"])

    def one(block: str) -> str:
        return re.sub(r"\bIO \$[\d,.]+", f"IO {text}", block)

    return _in_articles(html, "io", one)


def _mark_copied_detail(html: str, previous_html: str | None) -> str:
    """Click-open pages that still say last week's line are marked, not left looking current."""
    if not previous_html:
        return html
    cfg = load_report()
    shown = list(cfg["always_shown"]) + list(cfg["held"])
    for asset in shown:
        regions = [span for span in coin_regions(html, asset) if html[span[0]:span[0] + 8].lower().startswith("<article")]
        prev_regions = [span for span in coin_regions(previous_html, asset) if previous_html[span[0]:span[0] + 8].lower().startswith("<article")]
        if not regions or not prev_regions:
            continue
        prev = previous_html[prev_regions[0][0]:prev_regions[0][1]]
        start, end = regions[0]
        block = html[start:end]
        for chunk in re.split(r"(?<=\.)\s+", re.sub(r"<[^>]+>", " ", prev)):
            phrase = " ".join(chunk.split())
            if len(phrase) < 24 or "STALE" in phrase:
                continue
            if "bounce" not in phrase.lower() and not re.search(r"\d", phrase):
                continue
            if phrase in re.sub(r"<[^>]+>", " ", block) and f"{phrase} · STALE" not in re.sub(r"<[^>]+>", " ", block):
                block = block.replace(phrase, f"{phrase} · STALE", 1)
        html = html[:start] + block + html[end:]
    return html


def apply_prose(html: str, snapshot: dict, previous_html: str | None = None) -> str:
    html = _prose_prices(html, snapshot)
    html = _as_of_stamps(html, snapshot)
    html = _etf_cells(html, snapshot)
    html = _stance_etf(html, snapshot)
    html = _sol_lines(html, snapshot)
    html = _render_lines(html, snapshot)
    html = _btc_lines(html, snapshot)
    html = _fart_lines(html, snapshot)
    html = _one_io_price(html, snapshot)
    html = _mark_copied_detail(html, previous_html)
    return _clean_unknown(html)
