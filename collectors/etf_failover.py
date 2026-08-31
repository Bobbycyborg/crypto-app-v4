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


def farside_failover(request_key: str) -> HttpResponse:
    spec = SPECS[request_key]
    rows: list[tuple[str, str]] = []
    used = ""
    if spec["use_tftc"]:
        try:
            resp = request("GET", TFTC_BTC, extra_headers={"Accept": "application/json"})
            payload = json.loads(resp.body.decode("utf-8"))
            rows = rows_from_tftc(payload)
            used = TFTC_BTC
        except Exception:
            rows = []
    if not rows:
        for fallback_dir in FALLBACK_DIRS:
            md_path = fallback_dir / spec["md_name"]
            if md_path.is_file():
                rows = rows_from_markdown(md_path.read_text(encoding="utf-8"))
                used = str(md_path)
                break
    if not rows:
        raise HttpError("SOURCE_UNAVAILABLE", f"ETF failover empty for {request_key}")
    html = _html_page(spec["title"], spec["tickers"], rows)
    _ = body_sha256(html.encode("utf-8"))
    return _as_response(used or request_key, html)
