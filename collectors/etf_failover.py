"""ETF fetch failover when Farside HTML is Cloudflare-blocked (403). Never return empty."""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

from collectors.http_client import HttpError, HttpResponse, body_sha256, request, utc_now

ROOT = Path(__file__).resolve().parents[1]
FALLBACK_DIRS = (
    ROOT / "collectors/etf-fallback",
    ROOT / "runtime-NOT-FOR-GH/job6/etf-fallback",
)
TFTC_BTC = "https://www.tftc.io/bitcoin-etf-flows/data.json"

_DATE_RE = re.compile(r"^\d{1,2}\s+[A-Za-z]{3}\s+\d{4}$")
_MD_ROW = re.compile(r"^\|(.+)\|\s*$")

SPECS = {
    "farside.html.btc": {
        "title": "Bitcoin ETF Flow (US$m) – Farside Investors",
        "tickers": ["IBIT", "FBTC", "BITB", "ARKB", "BTCO", "EZBC", "BRRR", "HODL", "BTCW", "MSBT", "GBTC", "BTC"],
        "md_name": "btc.md",
        "use_tftc": True,
    },
    "farside.html.eth": {
        "title": "Ethereum ETF Flow (US$m) – Farside Investors",
        "tickers": ["ETHA", "ETHB", "FETH", "ETHW", "TETH", "ETHV", "QETH", "EZET", "ETHE", "ETH"],
        "md_name": "eth.md",
        "use_tftc": False,
    },
    "farside.html.sol": {
        "title": "Solana ETF Flow (US$m) – Farside Investors",
        "tickers": ["BSOL", "VSOL", "FSOL", "TSOL", "SOEZ", "GSOL"],
        "md_name": "sol.md",
        "use_tftc": False,
    },
}


def _html_page(title: str, tickers: list[str], rows: list[tuple[str, str]]) -> str:
    """rows: newest-first (date_label, total_millions_text)."""
    head = "".join(f"<th>{escape(t)}</th>" for t in tickers)
    body = []
    pad = "".join("<td></td>" for _ in tickers)
    for date_label, total in rows:
        body.append(f"<tr><td>{escape(date_label)}</td>{pad}<td>{escape(total)}</td></tr>")
    return (
        "<!DOCTYPE html><html><head>"
        f"<title>{escape(title)}</title></head><body><table>"
        f"<tr><th>Date</th>{head}<th>Total</th></tr>"
        + "".join(body)
        + "</table></body></html>"
    )


def _skip_placeholder(date_label: str, total: str, cells: list[str]) -> bool:
    if total.strip() in {"", "-", "–", "—"}:
        return True
    if total.strip() in {"0.0", "0"} and all(c.strip() in {"", "-", "–", "—"} for c in cells):
        return True
    return False


def rows_from_markdown(text: str) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for line in text.splitlines():
        m = _MD_ROW.match(line.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if not cells or not _DATE_RE.match(cells[0]):
            continue
        total = cells[-1]
        if _skip_placeholder(cells[0], total, cells[1:-1]):
            continue
        parsed.append((cells[0], total))
    parsed.reverse()
    return parsed


def rows_from_tftc(payload: dict) -> list[tuple[str, str]]:
    months = (
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    )
    out: list[tuple[str, str]] = []
    for day in payload.get("days") or []:
        iso = str(day.get("date") or "")
        flow = day.get("netFlowUsd")
        if not iso or flow is None:
            continue
        y, m, d = iso.split("-")
        label = f"{int(d)} {months[int(m) - 1]} {y}"
        millions = float(flow) / 1_000_000.0
        total = f"({abs(millions):.1f})" if millions < 0 else f"{millions:.1f}"
        out.append((label, total))
    out.reverse()
    return out


def _as_response(url: str, html: str) -> HttpResponse:
    body = html.encode("utf-8")
    return HttpResponse(
        url=url,
        method="GET",
        status_code=200,
        headers={"Content-Type": "text/html; charset=utf-8", "X-V4-Etf-Failover": "1"},
        body=body,
        fetched_at=utc_now(),
        attempts=1,
    )


_ALL_DATA = {
    "farside.html.btc": (
        "https://farside.co.uk/bitcoin-etf-flow-all-data/",
        "https://farside.co.uk/btc/",
    ),
    "farside.html.eth": (
        "https://farside.co.uk/ethereum-etf-flow-all-data/",
        "https://farside.co.uk/eth/",
    ),
    "farside.html.sol": ("https://farside.co.uk/sol/",),
}
_BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


def _from_reader(request_key: str, page: str) -> HttpResponse | None:
    """A public reader of the live Farside page. Not the August file."""
    url = f"https://r.jina.ai/https://farside.co.uk/{page}"
    try:
        resp = request("GET", url, extra_headers={"User-Agent": "Mozilla/5.0", "Accept": "text/plain"})
    except HttpError:
        return None
    text = resp.body.decode("utf-8", "replace")
    rows = rows_from_markdown(text)
    if len(rows) < 7:
        return None
    spec = SPECS[request_key]
    html = _html_page(spec["title"], spec["tickers"], rows)
    html = html.replace("<head>", '<head><meta name="v4-etf-source" content="jina-farside">', 1)
    out = _as_response(url, html)
    out.headers["X-V4-Etf-Source"] = "jina-farside"
    return out


def farside_failover(request_key: str) -> HttpResponse:
    """Live Farside pages only. The August markdown files are not used."""
    last = "no live Farside page"
    for url in _ALL_DATA.get(request_key, ()):
        try:
            resp = request("GET", url, extra_headers=_BROWSER)
        except HttpError as exc:
            last = str(exc)
            continue
        if b"Just a moment" in resp.body or b"etf-fallback" in resp.body:
            last = f"blocked page {url}"
            continue
        resp.headers["X-V4-Etf-Source"] = "farside"
        return resp
    page = {"farside.html.btc": "btc/", "farside.html.eth": "eth/", "farside.html.sol": "sol/"}.get(request_key)
    if page:
        via = _from_reader(request_key, page)
        if via is not None:
            return via
        last = "reader returned too few rows"
    if request_key == "farside.html.btc":
        resp = request("GET", TFTC_BTC, extra_headers={"Accept": "application/json"})
        payload = json.loads(resp.body.decode("utf-8"))
        rows = rows_from_tftc(payload)
        if rows:
            spec = SPECS[request_key]
            html = _html_page(spec["title"], spec["tickers"], rows)
            through = str(payload.get("updatedThrough") or "")
            if through:
                html = html.replace(
                    "<head>",
                    f'<head><meta name="v4-updated-through" content="{escape(through)}">',
                    1,
                )
            return _as_response(TFTC_BTC, html)
    raise HttpError("SOURCE_UNAVAILABLE", f"{request_key}: {last}. Refusing collectors/etf-fallback.")
