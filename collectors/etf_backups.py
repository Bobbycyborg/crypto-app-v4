"""Fill ETF box cells that Farside's short table cannot.

Order for each cell: Farside chart or Total row, SoSoValue, CoinGlass,
ETFDB, then The Block. A dead source is skipped. This never raises.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from collectors.http_client import HttpError, request

_BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json",
}
_DATE_RE = re.compile(r"(\d{1,2} [A-Za-z]{3} 20\d\d)")
_WINDOWS = ("1d", "7d", "30d", "all_time")
_PAGES = {
    "btc": "https://farside.co.uk/bitcoin-etf-flow-all-data/",
    "eth": "https://farside.co.uk/ethereum-etf-flow-all-data/",
    "sol": "https://farside.co.uk/sol/",
}
_CAPTURE = {
    "btc": "farside.html.btc",
    "eth": "farside.html.eth",
    "sol": "farside.html.sol",
}
_SOSO = {"btc": "us-btc-spot", "eth": "us-eth-spot", "sol": "us-sol-spot"}
_BLOCK = {
    "btc": "https://www.theblock.co/api/charts/chart/crypto-markets/bitcoin-etf/spot-bitcoin-etf-flows",
    "eth": "https://www.theblock.co/api/charts/chart/crypto-markets/ethereum-etf/spot-ethereum-etf-flows",
    "sol": "https://www.theblock.co/api/charts/chart/crypto-markets/solana-etf/spot-solana-etf-flows",
}
_ETFDB_TICKERS = {
    "btc": {"IBIT", "FBTC", "BITB", "ARKB", "BTCO", "EZBC", "BRRR", "HODL", "BTCW", "GBTC", "MSBT"},
    "eth": {"ETHA", "FETH", "ETHW", "CETH", "ETHV", "EZET", "QETH", "ETHE", "ETH"},
    "sol": {"BSOL", "VSOL", "FSOL", "TSOL", "GSOL", "SOEZ"},
}
_MILLION = Decimal("1000000")


def _encode(value: Decimal) -> str | int:
    if value == value.to_integral_value():
        return int(value)
    return format(value, "f")


def _num(raw: str) -> Decimal | None:
    text = (raw or "").replace(",", "").strip()
    if not text or text in {"-", "–", "—"}:
        return None
    neg = text.startswith("(") and text.endswith(")")
    if neg:
        text = text[1:-1]
    try:
        val = Decimal(text)
    except InvalidOperation:
        return None
    return -val if neg else val


def chart_cumulative(html: str) -> list[Decimal] | None:
    """Farside chart Total line. Cumulative millions, oldest first."""
    match = re.search(r"totalData\s*=\s*\[([^\]]+)\]", html)
    if not match:
        return None
    nums = [_num(part) for part in match.group(1).split(",")]
    series = [n for n in nums if n is not None]
    return series or None


def window_from_cumulative(series: list[Decimal], days: int) -> Decimal | None:
    """Last point minus the point this many trading days earlier."""
    if len(series) < days + 1:
        return None
    return series[-1] - series[-(days + 1)]


def _newest_table_date(html: str) -> date | None:
    found: list[date] = []
    for label in _DATE_RE.findall(html):
        try:
            found.append(datetime.strptime(label, "%d %b %Y").date())
        except ValueError:
            continue
    return max(found) if found else None


def _total_row_millions(html: str) -> Decimal | None:
    """Last cell of the Total row. The SOL short table's Total is not lifetime."""
    best: Decimal | None = None
    best_n = 0
    for match in re.finditer(r">Total<", html):
        chunk = html[match.start() : match.start() + 4000]
        end = chunk.find("</tr>")
        row = chunk if end < 0 else chunk[:end]
        nums = [_num(part) for part in re.findall(r">\(?([\d,]+\.?\d*)\)?<", row)]
        nums = [n for n in nums if n is not None]
        if len(nums) > best_n:
            best_n = len(nums)
            best = nums[-1]
    if best_n < 8:
        return None
    return best


def farside_windows(html: str, report_day: date) -> dict[str, Decimal]:
    """Millions. Chart first. Total row only when the chart is absent."""
    newest = _newest_table_date(html)
    if newest is not None and newest > report_day:
        return {}
    out: dict[str, Decimal] = {}
    series = chart_cumulative(html)
    if series and len(series) >= 31:
        change = window_from_cumulative(series, 30)
        if change is not None:
            out["30d"] = change
        out["all_time"] = series[-1]
        return out
    total = _total_row_millions(html)
    dated = len(set(_DATE_RE.findall(html)))
    if total is not None and dated >= 30:
        out["all_time"] = total
    return out


def _get(url: str, *, data: dict | None = None) -> str | None:
    try:
        if data is None:
            resp = request("GET", url, extra_headers=_BROWSER)
        else:
            resp = request(
                "POST",
                url,
                json_body=data,
                extra_headers={**_BROWSER, "Content-Type": "application/json"},
            )
    except HttpError:
        return None
    if resp.status_code >= 400:
        return None
    return resp.body.decode("utf-8", "replace")


def _sosovalue(asset: str, report_day: date) -> dict[str, Decimal]:
    kind = _SOSO.get(asset)
    if not kind:
        return {}
    text = _get(
        "https://api.sosovalue.xyz/openapi/v2/etf/historicalInflowChart",
        data={"type": kind},
    )
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    rows = []
    for row in payload.get("data") or []:
        try:
            when = datetime.strptime(str(row.get("date") or ""), "%Y-%m-%d").date()
        except ValueError:
            continue
        if when > report_day:
            continue
        flow = row.get("totalNetInflow")
        cum = row.get("cumNetInflow")
        if flow is None:
            continue
        rows.append((when, Decimal(str(flow)), Decimal(str(cum)) if cum is not None else None))
    rows.sort(key=lambda item: item[0], reverse=True)
    if not rows:
        return {}
    out: dict[str, Decimal] = {"1d": rows[0][1]}
    if len(rows) >= 7:
        out["7d"] = sum((item[1] for item in rows[:7]), Decimal("0"))
    if len(rows) >= 30:
        out["30d"] = sum((item[1] for item in rows[:30]), Decimal("0"))
    if rows[0][2] is not None:
        out["all_time"] = rows[0][2]
    return out


def _coinglass(asset: str, report_day: date) -> dict[str, Decimal]:
    """Public CoinGlass ETF pages are drawn in the browser. Try the open API, then stop."""
    urls = [
        f"https://open-api-v4.coinglass.com/api/etf/{asset}/flow-history",
        f"https://www.coinglass.com/etf/{'bitcoin' if asset == 'btc' else 'ethereum' if asset == 'eth' else 'solana'}",
    ]
    for url in urls:
        text = _get(url)
        if not text or "totalNetInflow" not in text and "netFlow" not in text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            continue
        parsed = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            raw_day = str(row.get("date") or row.get("t") or "")[:10]
            flow = row.get("netFlow") or row.get("totalNetInflow")
            if flow is None:
                continue
            try:
                when = datetime.strptime(raw_day, "%Y-%m-%d").date()
            except ValueError:
                continue
            if when <= report_day:
                parsed.append((when, Decimal(str(flow))))
        parsed.sort(key=lambda item: item[0], reverse=True)
        if len(parsed) < 30:
            continue
        return {
            "1d": parsed[0][1],
            "7d": sum((item[1] for item in parsed[:7]), Decimal("0")),
            "30d": sum((item[1] for item in parsed[:30]), Decimal("0")),
        }
    return {}


def _etfdb(asset: str) -> dict[str, Decimal]:
    """1-week fund-flow column only. Empty cells are not a number."""
    text = _get("https://etfdb.com/etfs/currency/cryptocurrency/")
    if not text:
        return {}
    want = _ETFDB_TICKERS.get(asset) or set()
    total = Decimal("0")
    seen = 0
    for row in re.findall(r"<tr\b[^>]*>.*?</tr>", text, re.S):
        symbol = re.search(r'data-th="Symbol"[^>]*>\s*(?:<[^>]+>)?\s*([A-Z]{3,5})', row)
        if not symbol or symbol.group(1) not in want:
            continue
        cell = re.search(r'data-th="1 Week FF"[^>]*>(.*?)</td>', row, re.S)
        if not cell:
            continue
        plain = re.sub(r"<[^>]+>", "", cell.group(1))
        val = _num(plain.replace("$", "").replace("M", ""))
        if val is None:
            continue
        total += val
        seen += 1
    if not seen:
        return {}
    return {"7d": total * _MILLION}


def _theblock(asset: str, report_day: date) -> dict[str, Decimal]:
    text = _get(_BLOCK.get(asset, ""))
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    series = ((payload.get("chart") or {}).get("jsonFile") or {}).get("Series") or {}
    if not isinstance(series, dict) or not series:
        return {}
    by_day: dict[date, Decimal] = {}
    for points in series.values():
        if not isinstance(points, dict):
            continue
        for point in points.get("Data") or []:
            try:
                when = datetime.fromtimestamp(int(point["Timestamp"]), timezone.utc)
            except (KeyError, TypeError, ValueError, OSError):
                continue
            day = when.date()
            if day > report_day:
                continue
            by_day[day] = by_day.get(day, Decimal("0")) + Decimal(str(point.get("Result") or 0))
    days = sorted(by_day, reverse=True)
    if len(days) < 30:
        return {}
    flows = [by_day[day] for day in days]
    return {
        "1d": flows[0],
        "7d": sum(flows[:7], Decimal("0")),
        "30d": sum(flows[:30], Decimal("0")),
    }


def _farside_html(asset: str, captures: dict[str, Any]) -> str:
    cap = captures.get(_CAPTURE[asset])
    html = getattr(cap, "html", None) or ""
    if "totalData" in html or (asset != "sol" and ">Total<" in html and len(set(_DATE_RE.findall(html))) >= 30):
        return html
    fresh = _get(_PAGES[asset])
    return fresh or html


def _books(asset: str, captures: dict[str, Any], report_day: date) -> list[tuple[str, str, dict[str, Decimal]]]:
    """(source_key, source_used, usd windows). Later books are only built if needed."""
    found: list[tuple[str, str, dict[str, Decimal]]] = []
    try:
        html = _farside_html(asset, captures)
        millions = farside_windows(html, report_day) if html else {}
    except Exception:
        millions = {}
    if millions:
        found.append(("farside", "farside-chart" if "30d" in millions and asset == "sol" else "farside-total", {k: v * _MILLION for k, v in millions.items()}))
    return found


def _later_books(asset: str, report_day: date) -> list[tuple[str, str, dict[str, Decimal]]]:
    loaders = (
        ("sosovalue", "sosovalue", lambda: _sosovalue(asset, report_day)),
        ("coinglass", "coinglass", lambda: _coinglass(asset, report_day)),
        ("etfdb", "etfdb", lambda: _etfdb(asset)),
        ("theblock", "theblock", lambda: _theblock(asset, report_day)),
    )
    books = []
    for key, used, loader in loaders:
        try:
            windows = loader()
        except Exception:
            windows = {}
        if windows:
            books.append((key, used, windows))
    return books


def _apply(fact: dict[str, Any], usd: Decimal, source_key: str, source_used: str, as_of: str) -> None:
    fact["status"] = "OK"
    fact["raw_source_value"] = format(usd, "f")
    fact["normalized_value"] = _encode(usd)
    fact["unit"] = fact.get("unit") or "USD"
    fact["source_key"] = source_key
    fact["source_used"] = source_used
    fact["source_as_of"] = as_of
    fact["error"] = None


def fill_missing_etf(facts: list[dict[str, Any]], captures: dict[str, Any]) -> None:
    """Write a number into any empty BTC/ETH/SOL ETF cell. Never raises."""
    try:
        from renderer.report_config import load_report

        report_day = datetime.strptime(load_report()["report_date"], "%Y-%m-%d").date()
    except Exception:
        return
    by_id = {row.get("metric_id"): row for row in facts}
    as_of = report_day.strftime("%Y-%m-%dT00:00:00Z")
    for asset in ("btc", "eth", "sol"):
        missing = []
        for window in _WINDOWS:
            row = by_id.get(f"{asset}.etf.flow.usd.{window}")
            if row is None or row.get("status") == "OK":
                continue
            missing.append((window, row))
        if not missing:
            continue
        try:
            books = _books(asset, captures, report_day)
            if any(window not in {k for _s, _u, book in books for k in book} for window, _row in missing):
                books.extend(_later_books(asset, report_day))
        except Exception:
            continue
        for window, row in missing:
            for source_key, source_used, book in books:
                usd = book.get(window)
                if usd is None:
                    continue
                _apply(row, usd, source_key, source_used, as_of)
                break
