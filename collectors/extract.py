"""Explicit selectors only. No first-number, no fuzzy key match."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any


class ExtractError(Exception):
    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def parse_json_body(body: bytes, content_type: str | None) -> Any:
    text = body.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"malformed JSON: {exc}") from exc


def json_pointer(doc: Any, pointer: str) -> Any:
    if pointer == "" or pointer == "/":
        return doc
    if not pointer.startswith("/"):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"invalid json_pointer {pointer!r}")
    cur = doc
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list):
            try:
                idx = int(token)
            except ValueError as exc:
                raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"list index not integer: {token}") from exc
            if idx < 0 or idx >= len(cur):
                raise ExtractError("VALUE_MISSING", f"json_pointer {pointer} missing")
            cur = cur[idx]
        elif isinstance(cur, dict):
            if token not in cur:
                raise ExtractError("VALUE_MISSING", f"json_pointer {pointer} missing")
            cur = cur[token]
        else:
            raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"cannot walk {type(cur).__name__} at {token}")
    return cur


def json_key(doc: Any, key: str) -> Any:
    if not isinstance(doc, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "json_key expects object")
    if key not in doc:
        raise ExtractError("VALUE_MISSING", f"missing key {key}")
    return doc[key]


def _identity_match(row: dict[str, Any], identity: dict[str, Any]) -> bool:
    for k, expected in identity.items():
        if k.startswith("_"):
            continue
        got = row.get(k)
        if got != expected and str(got) != str(expected):
            return False
    return True


def named_record_field(doc: Any, selector: dict[str, Any]) -> Any:
    """Select exactly one record by identity, then a field."""
    path = selector.get("records_pointer")
    records = json_pointer(doc, path) if path else doc
    if not isinstance(records, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "named_record_field expects a list")
    identity = selector.get("identity") or {}
    matches = [r for r in records if isinstance(r, dict) and _identity_match(r, identity)]
    if len(matches) == 0:
        raise ExtractError("VALUE_MISSING", f"zero records matched identity {identity}")
    if len(matches) > 1:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"multiple records matched identity {identity}")
    field = selector.get("field")
    if not field:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "named_record_field missing field")
    row = matches[0]
    if field not in row:
        raise ExtractError("VALUE_MISSING", f"field {field} missing on matched record")
    return row[field]


def csv_column(_doc: Any, _selector: dict[str, Any]) -> Any:
    raise ExtractError("SOURCE_SCHEMA_MISMATCH", "csv_column not used by this plan")


def explicit_html_selector(html: str, selector: dict[str, Any]) -> Any:
    """Farside ETF tables: identity via title + required/forbidden tickers, then named aggregate."""
    from html.parser import HTMLParser

    name = selector.get("name")
    if name == "render_leftover_emissions":
        from collectors.phase_b_selectors import render_leftover_emissions_html

        return render_leftover_emissions_html(html, selector)
    if name != "farside_etf_flow":
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"unknown html selector {name}")

    title_must = selector["title_must"]
    tickers_must = list(selector["tickers_must"])
    forbidden = list(selector.get("forbidden_tickers") or [])
    window = selector.get("window")  # latest | 7d | 30d

    title_m = re.search(r"<title>([^<]+)", html, re.I)
    title = re.sub(r"\s+", " ", (title_m.group(1) if title_m else "")).replace("&#8211;", "–")
    if title_must.lower() not in title.lower():
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"wrong Farside title: {title!r}")

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

    parser = _TableParser()
    parser.feed(html)
    date_re = re.compile(r"^\d{1,2}\s+[A-Za-z]{3}\s+\d{4}$")
    best = None
    best_dates = 0
    for table in parser.tables:
        n = sum(1 for row in table if row and date_re.match(row[0].strip()))
        if n > best_dates:
            best, best_dates = table, n
    if not best or best_dates == 0:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "no dated ETF flow rows")

    tickers: list[str] = []
    for row in best[:4]:
        for cell in row[1:]:
            token = cell.strip().upper()
            if re.fullmatch(r"[A-Z]{3,5}", token) and token not in ("TOTAL", "FEE", "SEED"):
                tickers.append(token)
        if tickers:
            break
    ticker_set = set(tickers)
    missing = [t for t in tickers_must if t not in ticker_set]
    if missing:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"missing identity tickers {missing}")
    bad = [t for t in forbidden if t in ticker_set]
    if bad:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"foreign tickers {bad}")

    def parse_millions(raw: str) -> Decimal | None:
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
            val = Decimal(s)
        except InvalidOperation as exc:
            raise ExtractError("VALUE_INVALID", f"unparseable flow cell {raw!r}") from exc
        return -val if neg else val

    daily: list[Decimal] = []
    for row in best:
        label = (row[0] or "").strip()
        if not date_re.match(label):
            continue
        total_cell = row[-1] if row else ""
        parsed = parse_millions(total_cell)
        if parsed is None:
            continue
        daily.append(parsed)
    if not daily:
        raise ExtractError("VALUE_MISSING", "no numeric daily ETF totals")
    if window == "latest":
        return daily[0] if selector.get("order") == "newest_first" else daily[-1]
    # Farside tables are typically newest-first
    newest_first = daily
    if window == "7d":
        chunk = newest_first[:7]
        if len(chunk) < 1:
            raise ExtractError("VALUE_MISSING", "need 7 daily ETF rows")
        return sum(chunk, Decimal("0"))
    if window == "30d":
        chunk = newest_first[:30]
        if len(chunk) < 1:
            raise ExtractError("VALUE_MISSING", "need 30 daily ETF rows")
        return sum(chunk, Decimal("0"))
    raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"unknown farside window {window}")


def extract(doc: Any, selector: dict[str, Any], *, html: str | None = None) -> Any:
    stype = selector.get("type")
    if stype == "json_pointer":
        return json_pointer(doc, selector["pointer"])
    if stype == "json_key":
        return json_key(doc, selector["key"])
    if stype == "named_record_field":
        name = selector.get("name")
        if name == "klines_close_return_pct":
            return klines_close_return_pct(doc, selector)
        if name == "klines_july_min_close":
            return klines_july_min_close(doc, selector)
        if name == "klines_rs_pct":
            raise ExtractError("SOURCE_SCHEMA_MISMATCH", "klines_rs_pct requires orchestrator dual capture")
        if name == "chart_sum_last_n":
            return chart_sum_last_n(doc, selector)
        if name == "chart_mean_last_n":
            return chart_mean_last_n(doc, selector)
        if name == "chart_pct_change_last_n":
            return chart_pct_change_last_n(doc, selector)
        if name == "latest_chart_value":
            return latest_chart_value(doc, selector)
        if name == "stablecoin_chain_usd":
            return stablecoin_chain_usd(doc, selector)
        if name == "ncu_balance":
            return ncu_balance(doc, selector)
        if name == "pool_sum":
            return pool_sum(doc, selector)
        if name == "vote_accounts_active_count":
            return vote_accounts_active_count(doc)
        if name == "vote_accounts_activated_stake":
            return vote_accounts_activated_stake(doc)
        if name == "perf_tps_nonvote":
            return perf_tps_nonvote(doc)
        if name == "launchpad_share_pct":
            return launchpad_share_pct(doc, selector)
        if name == "epoch_burn_last_n":
            return epoch_burn_last_n(doc, selector)
        if name == "by_state_count":
            return by_state_count(doc, selector)
        if name == "ratio_pct" and selector.get("num_key") == "af_inventory":
            from collectors.phase_b_selectors_extra import hype_af_share_hl_circ

            return hype_af_share_hl_circ(doc, selector)
        if name == "ratio_pct":
            if any(selector.get(k) for k in ("num_field", "den_field", "den_const")) or selector.get("identity"):
                from collectors.phase_b_selectors_extra import ratio_pct_extended

                return ratio_pct_extended(doc, selector)
            return ratio_pct(doc, selector)
        if name == "latest_list_field":
            return latest_list_field(doc, selector)
        if name == "dex_pair_liquidity_usd":
            return dex_pair_liquidity_usd(doc, selector)
        if name:
            from collectors.phase_b_selectors import dispatch_phase_b
            from collectors.phase_b_selectors_extra import dispatch_phase_b_extra

            out = dispatch_phase_b(name, doc, selector, html=html)
            if out is not None:
                return out
            out = dispatch_phase_b_extra(name, doc, selector, html=html)
            if out is not None:
                return out
        return named_record_field(doc, selector)
    if stype == "csv_column":
        return csv_column(doc, selector)
    if stype == "explicit_html_selector":
        if html is None:
            raise ExtractError("SOURCE_SCHEMA_MISMATCH", "html selector without html body")
        return explicit_html_selector(html, selector)
    raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"unknown selector type {stype}")


def _as_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        raise ExtractError("VALUE_MISSING", "empty value")
    if isinstance(value, bool):
        raise ExtractError("VALUE_INVALID", "boolean is not numeric")
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ExtractError("VALUE_INVALID", "NaN/Inf")
        return Decimal(str(value))
    if isinstance(value, str):
        s = value.strip()
        if s.lower() in {"nan", "inf", "+inf", "-inf", "infinity", "-infinity"}:
            raise ExtractError("VALUE_INVALID", s)
        try:
            return Decimal(s)
        except InvalidOperation as exc:
            raise ExtractError("VALUE_INVALID", f"not numeric: {value!r}") from exc
    raise ExtractError("VALUE_INVALID", f"unsupported type {type(value).__name__}")


def klines_close_return_pct(doc: Any, selector: dict[str, Any]) -> Decimal:
    if not isinstance(doc, list) or not doc:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "klines must be a non-empty list")
    days = int(selector["window_days"])
    if len(doc) < days + 1:
        raise ExtractError("VALUE_MISSING", f"need {days+1} klines, got {len(doc)}")
    # Binance klines newest is last when fetched chronological
    close_now = _as_decimal(doc[-1][4])
    close_then = _as_decimal(doc[-1 - days][4])
    if close_then == 0:
        raise ExtractError("VALUE_INVALID", "division by zero")
    return (close_now - close_then) / close_then * Decimal("100")


def klines_july_min_close(doc: Any, selector: dict[str, Any]) -> Decimal:
    if not isinstance(doc, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "klines must be a list")
    year = int(selector["year"])
    month = int(selector["month"])
    closes: list[Decimal] = []
    for row in doc:
        if not isinstance(row, list) or len(row) < 5:
            raise ExtractError("SOURCE_SCHEMA_MISMATCH", "malformed kline row")
        ts = int(row[0])
        import datetime

        dt = datetime.datetime.fromtimestamp(ts / 1000, tz=datetime.timezone.utc)
        if dt.year == year and dt.month == month:
            closes.append(_as_decimal(row[3]))  # low
    if not closes:
        raise ExtractError("VALUE_MISSING", f"no klines in {year}-{month:02d}")
    return min(closes)


def chart_sum_last_n(doc: Any, selector: dict[str, Any]) -> Decimal:
    pointer = selector.get("pointer", "/totalDataChart")
    chart = json_pointer(doc, pointer)
    n = int(selector["n"])
    if not isinstance(chart, list) or len(chart) < n:
        raise ExtractError("VALUE_MISSING", f"chart shorter than {n}")
    total = Decimal("0")
    for pair in chart[-n:]:
        if not isinstance(pair, list) or len(pair) < 2:
            raise ExtractError("SOURCE_SCHEMA_MISMATCH", "chart pair malformed")
        total += _as_decimal(pair[1])
    return total


def chart_mean_last_n(doc: Any, selector: dict[str, Any]) -> Decimal:
    n = int(selector["n"])
    total = chart_sum_last_n(doc, selector)
    return total / Decimal(n)


def chart_pct_change_last_n(doc: Any, selector: dict[str, Any]) -> Decimal:
    pointer = selector.get("pointer", "/totalDataChart")
    chart = json_pointer(doc, pointer)
    n = int(selector["n"])
    if not isinstance(chart, list) or len(chart) < n + 1:
        raise ExtractError("VALUE_MISSING", f"chart shorter than {n}+1")
    now = _as_decimal(chart[-1][1])
    then = _as_decimal(chart[-1 - n][1])
    if then == 0:
        raise ExtractError("VALUE_INVALID", "division by zero")
    return (now - then) / then * Decimal("100")


def latest_chart_value(doc: Any, selector: dict[str, Any]) -> Decimal:
    pointer = selector.get("pointer")
    chart = json_pointer(doc, pointer)
    if not isinstance(chart, list) or not chart:
        raise ExtractError("VALUE_MISSING", "empty chart")
    last = chart[-1]
    if not isinstance(last, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "expected object chart rows")
    field = selector["field"]
    if field not in last:
        raise ExtractError("VALUE_MISSING", field)
    return last[field]


def stablecoin_chain_usd(doc: Any, selector: dict[str, Any]) -> Any:
    identity = {"name": selector["chain_name"]}
    if not isinstance(doc, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "stablecoinchains expects list")
    matches = [r for r in doc if isinstance(r, dict) and r.get("name") == identity["name"]]
    if len(matches) != 1:
        raise ExtractError(
            "VALUE_MISSING" if not matches else "SOURCE_SCHEMA_MISMATCH",
            f"stablecoin chain identity {identity} matched {len(matches)}",
        )
    tcu = matches[0].get("totalCirculatingUSD")
    if not isinstance(tcu, dict) or "peggedUSD" not in tcu:
        raise ExtractError("VALUE_MISSING", "peggedUSD missing")
    return tcu["peggedUSD"]


def ncu_balance(doc: Any, selector: dict[str, Any]) -> Decimal:
    addr = str(selector["address"]).lower()
    rows = doc.get("nonCirculatingUserBalances")
    if not isinstance(rows, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "nonCirculatingUserBalances missing")
    matches = []
    for item in rows:
        if not isinstance(item, list) or len(item) < 2:
            continue
        if str(item[0]).lower() == addr:
            matches.append(item[1])
    if len(matches) != 1:
        raise ExtractError(
            "VALUE_MISSING" if not matches else "SOURCE_SCHEMA_MISMATCH",
            f"NCU address matched {len(matches)}",
        )
    return matches[0]


def pool_sum(doc: Any, selector: dict[str, Any]) -> Decimal:
    pools = json_pointer(doc, selector.get("pointer", "/valuePools"))
    names = {n.lower() for n in selector["ids"]}
    if not isinstance(pools, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "valuePools not a list")
    total = Decimal("0")
    found = 0
    for p in pools:
        if not isinstance(p, dict):
            continue
        if str(p.get("id") or "").lower() in names:
            total += _as_decimal(p.get("chainValue"))
            found += 1
    if found == 0:
        raise ExtractError("VALUE_MISSING", "no matching valuePools")
    return total


def vote_accounts_active_count(doc: Any) -> int:
    current = doc.get("result", doc).get("current") if isinstance(doc.get("result"), dict) else doc.get("current")
    if not isinstance(current, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "getVoteAccounts current missing")
    return len(current)


def vote_accounts_activated_stake(doc: Any) -> Decimal:
    root = doc.get("result", doc) if isinstance(doc.get("result"), dict) else doc
    current = root.get("current")
    if not isinstance(current, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "getVoteAccounts current missing")
    lamports = Decimal("0")
    for row in current:
        if isinstance(row, dict) and "activatedStake" in row:
            lamports += _as_decimal(row["activatedStake"])
    return lamports / Decimal("1000000000")


def perf_tps_nonvote(doc: Any) -> Decimal:
    root = doc.get("result", doc)
    if not isinstance(root, list) or not root:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "getRecentPerformanceSamples empty")
    row = root[0]
    if not isinstance(row, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "performance sample not object")
    num = _as_decimal(row.get("numNonVoteTransactions", row.get("numTransactions")))
    secs = _as_decimal(row.get("samplePeriodSecs"))
    if secs == 0:
        raise ExtractError("VALUE_INVALID", "division by zero")
    return num / secs


def launchpad_share_pct(doc: Any, selector: dict[str, Any]) -> Decimal:
    protocols = doc if isinstance(doc, list) else doc.get("protocols")
    if not isinstance(protocols, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "overview fees protocols missing")
    slug = selector["slug"]
    launchpads = [p for p in protocols if isinstance(p, dict) and (p.get("category") or "") == "Launchpad"]
    total = sum((_as_decimal(p.get("total24h") or 0) for p in launchpads), Decimal("0"))
    pump = [p for p in launchpads if p.get("slug") == slug]
    if len(pump) != 1:
        raise ExtractError("VALUE_MISSING" if not pump else "SOURCE_SCHEMA_MISMATCH", f"slug {slug} matched {len(pump)}")
    if total == 0:
        raise ExtractError("VALUE_INVALID", "division by zero")
    return _as_decimal(pump[0].get("total24h") or 0) / total * Decimal("100")


def epoch_burn_last_n(doc: Any, selector: dict[str, Any]) -> Decimal:
    rows = doc if isinstance(doc, list) else (doc.get("data") or doc.get("epochs") or [])
    if not isinstance(rows, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "epochBurnStats not a list")
    ep = [e for e in rows if isinstance(e, dict) and isinstance(e.get("id"), int) and e["id"] < 10000]
    ep.sort(key=lambda e: e["id"])
    n = int(selector["n"])
    last = ep[-n:] if len(ep) >= n else ep
    if not last:
        raise ExtractError("VALUE_MISSING", "no epoch burn rows")
    field = selector.get("field", "burnedRender")
    total = Decimal("0")
    for row in last:
        total += _as_decimal(row.get(field) or row.get("burned") or 0)
    return total


def by_state_count(doc: Any, selector: dict[str, Any]) -> Any:
    state = selector["state"]
    by_state = doc.get("byState")
    if not isinstance(by_state, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "byState missing")
    if state not in by_state:
        raise ExtractError("VALUE_MISSING", f"byState.{state} missing")
    return by_state[state]


def ratio_pct(doc: Any, selector: dict[str, Any]) -> Decimal:
    if not isinstance(doc, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "ratio_pct expects object")
    num = _as_decimal(json_key(doc, selector["num_key"]))
    den = _as_decimal(json_key(doc, selector["den_key"]))
    if den == 0:
        raise ExtractError("VALUE_INVALID", "division by zero")
    return num / den * Decimal("100")


def latest_list_field(doc: Any, selector: dict[str, Any]) -> Any:
    if not isinstance(doc, list) or not doc:
        raise ExtractError("VALUE_MISSING", "empty list")
    last = doc[-1]
    if not isinstance(last, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "last row not object")
    field = selector["field"]
    if field not in last:
        raise ExtractError("VALUE_MISSING", field)
    return last[field]


def dex_pair_liquidity_usd(doc: Any, selector: dict[str, Any]) -> Any:
    pairs = doc.get("pairs") if isinstance(doc, dict) else None
    if not isinstance(pairs, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "pairs missing")
    chain = selector["chain_id"]
    base = str(selector["base_token_address"])
    matches = []
    for p in pairs:
        if not isinstance(p, dict):
            continue
        tok = p.get("baseToken") if isinstance(p.get("baseToken"), dict) else {}
        if p.get("chainId") == chain and str(tok.get("address") or "") == base:
            matches.append(p)
    if len(matches) == 0:
        raise ExtractError("VALUE_MISSING", "zero dex pairs matched mint/chain")
    if len(matches) > 1:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"multiple dex pairs matched ({len(matches)})")
    liq = matches[0].get("liquidity")
    if not isinstance(liq, dict) or "usd" not in liq:
        raise ExtractError("VALUE_MISSING", "liquidity.usd missing")
    return liq["usd"]


def open_interest_usd(oi_doc: Any, mark_doc: Any, selector: dict[str, Any]) -> Decimal:
    oi = json_pointer(oi_doc, selector.get("oi_pointer", "/openInterest"))
    mark = json_pointer(mark_doc, selector.get("mark_pointer", "/lastPrice"))
    return _as_decimal(oi) * _as_decimal(mark)


def perp_spot_ratio(perp_doc: Any, spot_doc: Any, selector: dict[str, Any]) -> Decimal:
    perp = json_pointer(perp_doc, selector.get("perp_pointer", "/quoteVolume"))
    spot = json_pointer(spot_doc, selector.get("spot_pointer", "/quoteVolume"))
    spot_d = _as_decimal(spot)
    if spot_d == 0:
        raise ExtractError("VALUE_INVALID", "division by zero")
    return _as_decimal(perp) / spot_d


def klines_rs_pct(base_doc: Any, bench_doc: Any, window_days: int) -> Decimal:
    base = klines_close_return_pct(base_doc, {"window_days": window_days})
    bench = klines_close_return_pct(bench_doc, {"window_days": window_days})
    return base - bench
