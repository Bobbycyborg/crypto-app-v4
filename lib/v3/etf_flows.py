"""US spot ETF net flows — Farside tables. Not a market-family vote.

CoinGlass ETH/SOL pages are the public viewers Olly named. Their JSON API is
key-gated (401) and HTML table bodies are JS-rendered empty. Production numbers
come from Farside (same source already trusted for BTC), with identity checks
so BTC/ETH/SOL tables cannot be crossed.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Any

import certifi
import requests

from lib.paths import CACHE
from lib.v3.source_provenance import CACHE_FALLBACK, LIVE, mark_cache_fallback, mark_live

FARSIDE_BTC = "https://farside.co.uk/btc/"
FARSIDE_ETH = "https://farside.co.uk/eth/"
FARSIDE_SOL = "https://farside.co.uk/sol/"
FARSIDE_BTC_ALL = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
FARSIDE_ETH_ALL = "https://farside.co.uk/ethereum-etf-flow-all-data/"
COINGLASS_ETH = "https://www.coinglass.com/etf/ethereum"
COINGLASS_SOL = "https://www.coinglass.com/etf/solana"
COINGLASS_BTC = "https://www.coinglass.com/etf/bitcoin"

_SKIP_LABELS = {
    "fee",
    "staking fee",
    "seed",
    "total",
    "average",
    "maximum",
    "minimum",
    "",
}
_DATE_RE = re.compile(r"^\d{1,2}\s+[A-Za-z]{3}\s+\d{4}$")
_STALE_AFTER_DAYS = 5
_CACHE_FILE = CACHE / "etf-flows.json"
_FARSIDE_HTML = {
    "BTC": CACHE / "farside-btc.html",
    "ETH": CACHE / "farside-eth.html",
    "SOL": CACHE / "farside-sol.html",
}
_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

ASSETS: dict[str, dict[str, Any]] = {
    "BTC": {
        "url": FARSIDE_BTC,
        "history_url": FARSIDE_BTC_ALL,
        "title_must": "Bitcoin ETF",
        "tickers_must": ("IBIT", "FBTC", "GBTC"),
        "forbidden_tickers": ("ETHA", "BSOL", "ETHE"),
        "viewer_url": COINGLASS_BTC,
    },
    "ETH": {
        "url": FARSIDE_ETH,
        "history_url": FARSIDE_ETH_ALL,
        "title_must": "Ethereum ETF",
        "tickers_must": ("ETHA", "ETHE"),
        "forbidden_tickers": ("IBIT", "BSOL", "GBTC"),
        "viewer_url": COINGLASS_ETH,
    },
    "SOL": {
        "url": FARSIDE_SOL,
        "title_must": "Solana ETF",
        "tickers_must": ("BSOL", "VSOL"),
        "forbidden_tickers": ("IBIT", "ETHA", "GBTC"),
        "viewer_url": COINGLASS_SOL,
    },
}


class _EtfFlowError(ValueError):
    """Malformed or wrong-asset Farside payload."""


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._cur: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._cur = []
        elif tag == "tr" and self._cur is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None and self._cur is not None:
            if any(self._row):
                self._cur.append(self._row)
            self._row = None
        elif tag == "table" and self._cur is not None:
            self.tables.append(self._cur)
            self._cur = None

    def handle_data(self, data: str) -> None:
        if not self._skip and self._cell is not None:
            self._cell.append(data)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_millions(raw: str) -> float | None:
    s = (raw or "").replace("\xa0", " ").strip()
    if s in ("", "-", "–", "—", "*"):
        return None
    s = s.replace("*", "").replace(",", "").strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    if s in ("", "-"):
        return None
    try:
        val = float(s)
    except ValueError as exc:
        raise _EtfFlowError(f"unparseable flow cell {raw!r}") from exc
    if neg:
        val = -val
    return val


def _parse_date(label: str) -> date | None:
    if not _DATE_RE.match(label.strip()):
        return None
    return datetime.strptime(label.strip(), "%d %b %Y").date()


def _direction(flow_usd: float | None) -> str | None:
    if flow_usd is None:
        return None
    if flow_usd > 0:
        return "IN"
    if flow_usd < 0:
        return "OUT"
    return "FLAT"


def _pick_flow_table(tables: list[list[list[str]]]) -> list[list[str]]:
    best: list[list[str]] | None = None
    best_dates = 0
    for table in tables:
        dates = sum(1 for row in table if row and _parse_date(row[0]))
        if dates > best_dates:
            best = table
            best_dates = dates
    if not best or best_dates == 0:
        raise _EtfFlowError("no dated ETF flow rows")
    return best


def _header_tickers(table: list[list[str]]) -> list[str]:
    tickers: list[str] = []
    for row in table[:4]:
        for cell in row[1:]:
            token = cell.strip().upper()
            if re.fullmatch(r"[A-Z]{3,5}", token) and token not in ("TOTAL", "FEE", "SEED"):
                tickers.append(token)
        if tickers:
            return tickers
    return tickers


def parse_farside_html(html: str, asset: str) -> dict[str, Any]:
    """Parse one Farside ETF page. Raises _EtfFlowError on identity/malformed data."""
    asset = asset.upper()
    spec = ASSETS.get(asset)
    if not spec:
        raise _EtfFlowError(f"unknown asset {asset}")

    title_m = re.search(r"<title>([^<]+)", html, re.I)
    title = re.sub(r"\s+", " ", (title_m.group(1) if title_m else "")).replace("&#8211;", "–")
    if spec["title_must"].lower() not in title.lower():
        raise _EtfFlowError(f"wrong asset title for {asset}: {title!r}")

    parser = _TableParser()
    parser.feed(html)
    table = _pick_flow_table(parser.tables)
    tickers = _header_tickers(table)
    ticker_set = set(tickers)
    missing = [t for t in spec["tickers_must"] if t not in ticker_set]
    if missing:
        raise _EtfFlowError(f"{asset} missing identity tickers {missing}; saw {tickers}")
    forbidden = [t for t in spec["forbidden_tickers"] if t in ticker_set]
    if forbidden:
        raise _EtfFlowError(f"{asset} table contains foreign tickers {forbidden}")

    daily: list[tuple[date, float]] = []
    all_time_m: float | None = None
    for row in table:
        label = (row[0] or "").strip()
        total_cell = row[-1] if row else ""
        if label.strip().lower() == "total":
            parsed = _parse_millions(total_cell)
            if parsed is None:
                raise _EtfFlowError(f"{asset} Total row unparseable: {total_cell!r}")
            all_time_m = parsed
            continue
        if label.strip().lower() in _SKIP_LABELS:
            continue
        d = _parse_date(label)
        if d is None:
            continue
        millions = _parse_millions(total_cell)
        if millions is None:
            millions = 0.0
        daily.append((d, millions))

    if not daily:
        raise _EtfFlowError(f"{asset} has no daily net-flow rows")
    daily.sort(key=lambda x: x[0])
    as_of = daily[-1][0]
    flow_1d_m = daily[-1][1]
    start_7 = as_of - timedelta(days=6)
    flow_7d_m = sum(v for d, v in daily if start_7 <= d <= as_of)
    start_30 = as_of - timedelta(days=29)
    flow_30d_m = sum(v for d, v in daily if start_30 <= d <= as_of)
    thirty_note = None
    if all_time_m is None:
        raise _EtfFlowError(f"{asset} missing Total (all-time) row")

    today = datetime.now(timezone.utc).date()
    lag = (today - as_of).days
    freshness = "STALE" if lag > _STALE_AFTER_DAYS else "CURRENT"

    def usd(millions: float | None) -> float | None:
        return None if millions is None else round(millions * 1_000_000.0, 2)

    return {
        "ok": True,
        "asset": asset,
        "as_of": as_of.isoformat(),
        "source": "Farside Investors",
        "source_url": spec["url"],
        "viewer_url": spec["viewer_url"],
        "unit_source": "US$m",
        "scope": "US spot ETF net flows",
        "flow_1d_usd": usd(flow_1d_m),
        "flow_7d_usd": usd(flow_7d_m),
        "flow_30d_usd": usd(flow_30d_m),
        "flow_all_time_usd": usd(all_time_m),
        "direction_1d": _direction(usd(flow_1d_m)),
        "freshness": freshness,
        "lag_days": lag,
        "daily_n": len(daily),
        "daily_from": daily[0][0].isoformat(),
        "tickers": tickers,
        "title": title.strip(),
        "flow_30d_note": thirty_note,
        "recent_daily": [
            {"date": d.isoformat(), "usd": usd(v)} for d, v in daily[-14:]
        ],
        "note": "ETF flows are one institutional/regulated spot-demand channel, not total crypto spot demand.",
    }


def _fail_payload(asset: str, error: str, fetched_at: str) -> dict[str, Any]:
    spec = ASSETS[asset]
    return {
        "ok": False,
        "asset": asset,
        "as_of": None,
        "source": "Farside Investors",
        "source_url": spec["url"],
        "viewer_url": spec["viewer_url"],
        "flow_1d_usd": None,
        "flow_7d_usd": None,
        "flow_30d_usd": None,
        "flow_all_time_usd": None,
        "direction_1d": None,
        "freshness": "UNKNOWN",
        "error": error,
        "fetched_at": fetched_at,
    }


def _load_disk_cache() -> dict[str, Any] | None:
    if not _CACHE_FILE.is_file():
        return None
    try:
        data = json.loads(_CACHE_FILE.read_text())
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _save_disk_cache(bundle: dict[str, Any]) -> None:
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _refresh_freshness(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    as_of_s = out.get("as_of")
    if not as_of_s:
        return out
    try:
        as_of = date.fromisoformat(str(as_of_s))
    except ValueError:
        return out
    lag = (datetime.now(timezone.utc).date() - as_of).days
    out["lag_days"] = lag
    out["freshness"] = "STALE" if lag > _STALE_AFTER_DAYS else "CURRENT"
    return out


def _cached_asset(asset: str) -> dict[str, Any] | None:
    bundle = _load_disk_cache()
    if not bundle:
        return None
    row = (bundle.get("assets") or {}).get(asset.upper())
    if not row or not row.get("ok"):
        return None
    out = _refresh_freshness(row)
    if not out.get("recent_daily"):
        html_path = _FARSIDE_HTML.get(asset.upper())
        if html_path and html_path.is_file():
            try:
                parsed = parse_farside_html(html_path.read_text(), asset)
                if parsed.get("ok"):
                    out.update({k: parsed[k] for k in ("recent_daily", "as_of", "flow_1d_usd", "flow_7d_usd", "flow_30d_usd", "flow_all_time_usd", "direction_1d", "daily_n") if k in parsed})
                    out = _refresh_freshness(out)
            except Exception:
                pass
    out = mark_cache_fallback(
        out,
        as_of=out.get("as_of"),
        live_error=out.get("live_error"),
    )
    out["cache_source"] = str(_CACHE_FILE)
    return out


def fetch_farside_html(url: str, timeout: int = 30) -> str:
    r = requests.get(url, headers=_UA, timeout=timeout, verify=certifi.where())
    text = r.text or ""
    if "Just a moment" in text or r.headers.get("cf-mitigated") == "challenge":
        raise _EtfFlowError(f"Cloudflare challenge page, not ETF table ({url})")
    r.raise_for_status()
    if len(text) < 500:
        raise _EtfFlowError("empty payload")
    return text


def _fetch_farside_pages(spec: dict[str, Any]) -> str:
    """Public /btc /eth /sol pages first. All-data URLs 403 and must not block a live print."""
    urls = []
    for key in ("url", "history_url"):
        u = spec.get(key)
        if u and u not in urls:
            urls.append(u)
    last_exc: Exception | None = None
    for url in urls:
        try:
            return fetch_farside_html(url)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            continue
    raise last_exc or _EtfFlowError("no Farside URL")


def fetch_asset_etf_flows(asset: str, html: str | None = None) -> dict[str, Any]:
    fetched_at = _now()
    spec = ASSETS[asset.upper()]
    try:
        page = html if html is not None else _fetch_farside_pages(spec)
        if not (page or "").strip():
            raise _EtfFlowError("empty payload")
        out = parse_farside_html(page, asset)
        out["fetched_at"] = fetched_at
        out = mark_live(out, as_of=out.get("as_of"))
        return out
    except _EtfFlowError as exc:
        cached = _cached_asset(asset.upper())
        if cached:
            cached["fetched_at"] = fetched_at
            return mark_cache_fallback(cached, as_of=cached.get("as_of"), live_error=str(exc))
        return _fail_payload(asset.upper(), str(exc), fetched_at)
    except Exception as exc:
        cached = _cached_asset(asset.upper())
        if cached:
            cached["fetched_at"] = fetched_at
            return mark_cache_fallback(cached, as_of=cached.get("as_of"), live_error=str(exc))
        return _fail_payload(asset.upper(), str(exc), fetched_at)


def fetch_etf_flows(*, html_by_asset: dict[str, str] | None = None) -> dict[str, Any]:
    """BTC + ETH + SOL. No combined net. Failures stay per-asset."""
    fetched_at = _now()
    assets: dict[str, Any] = {}
    for sym in ("BTC", "ETH", "SOL"):
        html = (html_by_asset or {}).get(sym)
        assets[sym] = fetch_asset_etf_flows(sym, html=html)
    ok_n = sum(1 for row in assets.values() if row.get("ok"))
    bundle = {
        "ok": ok_n == 3,
        "feed_id": "etf_flows",
        "role": "institutional_spot_flow_context_only",
        "not_a_market_vote": True,
        "no_combined_net": True,
        "fetched_at": fetched_at,
        "assets": assets,
        "note": (
            "US spot ETF net flows from Farside tables. "
            "Not total crypto spot demand. No BTC+ETH+SOL aggregate."
        ),
    }
    if bundle["ok"] and not any(row.get("cache_fallback") for row in assets.values()):
        _save_disk_cache(bundle)
    if ok_n and ok_n < 3:
        bundle["partial_ok"] = True
    return bundle


def format_flow_usd(usd: float | None, *, prefer_billions: bool = False) -> str:
    if usd is None:
        return "UNKNOWN"
    sign = "+" if usd > 0 else ("−" if usd < 0 else "")
    mag = abs(usd)
    if prefer_billions or mag >= 1_000_000_000:
        return f"{sign}${mag / 1_000_000_000:.2f}B"
    return f"{sign}${mag / 1_000_000:.1f}M"
