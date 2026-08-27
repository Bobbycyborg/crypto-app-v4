"""Named selectors for Job 2B Phase B metrics. Evidence-backed extraction only."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from decimal import InvalidOperation

from collectors.extract import ExtractError


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
    try:
        return Decimal(str(value).replace(",", ""))
    except InvalidOperation as exc:
        raise ExtractError("VALUE_INVALID", f"not numeric: {value!r}") from exc


def klines_sma(doc: Any, selector: dict[str, Any]) -> Decimal:
    if not isinstance(doc, list) or not doc:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "klines must be non-empty list")
    n = int(selector["window_days"])
    if len(doc) < n:
        raise ExtractError("VALUE_MISSING", f"need {n} klines, got {len(doc)}")
    closes = [_as_decimal(row[4]) for row in doc if isinstance(row, list) and len(row) > 4]
    if len(closes) < n:
        raise ExtractError("VALUE_MISSING", "malformed kline closes")
    window = closes[-n:]
    return sum(window, Decimal("0")) / Decimal(n)


def open_interest_change_pct(doc: Any, selector: dict[str, Any]) -> Decimal:
    if not isinstance(doc, list) or not doc:
        raise ExtractError("VALUE_MISSING", "empty openInterestHist")
    rows = []
    for row in doc:
        if not isinstance(row, dict):
            raise ExtractError("SOURCE_SCHEMA_MISMATCH", "hist row not object")
        sym = str(row.get("symbol") or "")
        if sym and sym != selector.get("expected_symbol", sym):
            continue
        oi = row.get("sumOpenInterestValue")
        ts = row.get("timestamp")
        if oi is None or ts is None:
            raise ExtractError("VALUE_MISSING", "missing sumOpenInterestValue/timestamp")
        rows.append({"ts": int(ts), "oi": _as_decimal(oi)})
    if not rows:
        raise ExtractError("VALUE_MISSING", "no OI rows")
    rows.sort(key=lambda r: r["ts"])
    latest = rows[-1]
    window = int(selector.get("window", 30))
    target = latest["ts"] - window * 24 * 60 * 60 * 1000
    baseline = None
    best_delta = None
    for row in rows[:-1]:
        delta = abs(row["ts"] - target)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            baseline = row
    if baseline is None or best_delta is None or best_delta > 36 * 60 * 60 * 1000:
        raise ExtractError("VALUE_MISSING", "no baseline within 36h of target timestamp")
    if latest["ts"] <= baseline["ts"] or baseline["oi"] <= 0:
        raise ExtractError("VALUE_INVALID", "invalid OI baseline/latest")
    return (latest["oi"] / baseline["oi"] - Decimal("1")) * Decimal("100")


def dex_live_price_highest_liquidity(doc: Any, _selector: dict[str, Any]) -> Decimal:
    pairs = doc.get("pairs") if isinstance(doc, dict) else None
    if not isinstance(pairs, list) or not pairs:
        raise ExtractError("VALUE_MISSING", "no dex pairs")
    best = None
    best_liq = Decimal("-1")
    for p in pairs:
        if not isinstance(p, dict):
            continue
        liq = p.get("liquidity") if isinstance(p.get("liquidity"), dict) else {}
        usd = liq.get("usd")
        if usd is None:
            continue
        d = _as_decimal(usd)
        if d > best_liq:
            best_liq = d
            best = p
    if not best or best.get("priceUsd") is None:
        raise ExtractError("VALUE_MISSING", "no priceUsd on highest-liquidity pair")
    return _as_decimal(best["priceUsd"])


def dex_highest_liquidity_usd(doc: Any, selector: dict[str, Any]) -> Decimal:
    pairs = doc.get("pairs") if isinstance(doc, dict) else None
    if not isinstance(pairs, list) or not pairs:
        raise ExtractError("VALUE_MISSING", "no dex pairs")
    chain = selector.get("chain_id")
    mint = str(selector.get("base_token_address") or "")
    best_liq = Decimal("0")
    for p in pairs:
        if not isinstance(p, dict):
            continue
        if chain and p.get("chainId") != chain:
            continue
        tok = p.get("baseToken") if isinstance(p.get("baseToken"), dict) else {}
        if mint and str(tok.get("address") or "") != mint:
            continue
        liq = p.get("liquidity") if isinstance(p.get("liquidity"), dict) else {}
        if "usd" not in liq:
            continue
        d = _as_decimal(liq["usd"])
        if d > best_liq:
            best_liq = d
    if best_liq <= 0:
        raise ExtractError("VALUE_MISSING", "no liquidity.usd for token")
    return best_liq


def defillama_hyperliquid_holders_revenue_30d(doc: Any, selector: dict[str, Any]) -> Decimal:
    protocols = doc.get("protocols") if isinstance(doc, dict) else None
    if not isinstance(protocols, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "protocols missing")
    identity = selector.get("identity") or {}
    want = identity.get("name")
    matches = [p for p in protocols if isinstance(p, dict) and p.get("name") == want]
    if len(matches) != 1:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"expected exactly one {want!r}, got {len(matches)}")
    field = selector.get("field", "total30d")
    if field not in matches[0]:
        raise ExtractError("VALUE_MISSING", field)
    val = _as_decimal(matches[0][field])
    if val < 0:
        raise ExtractError("VALUE_INVALID", "negative holders revenue")
    return val


def render_leftover_emissions_html(html: str, selector: dict[str, Any]) -> int:
    label = selector.get("label", "Leftover Emissions")
    pattern = re.compile(
        rf"{re.escape(label)}[^\d]{{0,80}}([\d,]+)",
        re.IGNORECASE | re.DOTALL,
    )
    hits = pattern.findall(html)
    if len(hits) != 1:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"label {label!r} matched {len(hits)} times")
    raw = hits[0].replace(",", "").strip()
    if not raw.isdigit():
        raise ExtractError("VALUE_INVALID", f"non-integer leftover emissions {raw!r}")
    return int(raw)


def market_chart_return_pct(doc: Any, selector: dict[str, Any]) -> Decimal:
    prices = doc.get("prices") if isinstance(doc, dict) else None
    if not isinstance(prices, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "prices missing")
    days = int(selector["window_days"])
    if len(prices) <= days:
        raise ExtractError("VALUE_MISSING", f"need >{days} price points")
    start = _as_decimal(prices[-1 - days][1])
    end = _as_decimal(prices[-1][1])
    if start <= 0:
        raise ExtractError("VALUE_INVALID", "zero start price")
    return (end / start - Decimal("1")) * Decimal("100")


def btc_issuance_inflation_pct(doc: Any, selector: dict[str, Any]) -> Decimal:
    identity = selector.get("identity") or {}
    records = doc if not selector.get("records_pointer") else doc
    if not isinstance(records, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "btc issuance expects list")
    matches = [r for r in records if isinstance(r, dict) and all(r.get(k) == v for k, v in identity.items())]
    if len(matches) != 1:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"btc identity match count {len(matches)}")
    if "circulating_supply" not in matches[0]:
        raise ExtractError("VALUE_MISSING", "circulating_supply missing")
    circ = matches[0]["circulating_supply"]
    reward = Decimal(str(selector.get("block_reward", 3.125)))
    annual = reward * Decimal("144") * Decimal("365")
    circ_d = _as_decimal(circ)
    if circ_d <= 0:
        raise ExtractError("VALUE_INVALID", "zero circulating")
    return annual / circ_d * Decimal("100")


def market_chart_sma(doc: Any, selector: dict[str, Any]) -> Decimal:
    prices = doc.get("prices") if isinstance(doc, dict) else None
    if not isinstance(prices, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "prices missing")
    n = int(selector["window_days"])
    if len(prices) < n:
        raise ExtractError("VALUE_MISSING", f"need {n} price points")
    window = [_as_decimal(p[1]) for p in prices[-n:]]
    return sum(window, Decimal("0")) / Decimal(n)


def dispatch_phase_b(name: str, doc: Any, selector: dict[str, Any], *, html: str | None = None) -> Any:
    if name == "klines_sma":
        return klines_sma(doc, selector)
    if name == "open_interest_change_pct":
        sym = selector.get("symbol")
        if sym:
            selector = {**selector, "expected_symbol": sym}
        return open_interest_change_pct(doc, selector)
    if name == "dex_live_price_highest_liquidity":
        return dex_live_price_highest_liquidity(doc, selector)
    if name == "dex_highest_liquidity_usd":
        return dex_highest_liquidity_usd(doc, selector)
    if name == "defillama_hyperliquid_holders_revenue_30d":
        return defillama_hyperliquid_holders_revenue_30d(doc, selector)
    if name == "market_chart_return_pct":
        return market_chart_return_pct(doc, selector)
    if name == "market_chart_sma":
        return market_chart_sma(doc, selector)
    if name == "btc_issuance_inflation_pct":
        return btc_issuance_inflation_pct(doc, selector)
    if name == "render_leftover_emissions":
        if html is None:
            raise ExtractError("SOURCE_SCHEMA_MISMATCH", "html required")
        return render_leftover_emissions_html(html, selector)
    return None
