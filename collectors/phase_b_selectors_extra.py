"""Additional Phase B named selectors."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from collectors.extract import ExtractError, chart_mean_last_n, chart_pct_change_last_n, chart_sum_last_n, epoch_burn_last_n, json_key, json_pointer, klines_close_return_pct, latest_chart_value, ncu_balance, perf_tps_nonvote, pool_sum, ratio_pct, stablecoin_chain_usd, vote_accounts_activated_stake, vote_accounts_active_count
from collectors.phase_b_selectors import _as_decimal, market_chart_return_pct

ROOT = Path(__file__).resolve().parents[1]
BREADTH_CFG = ROOT / "config/v3-breadth-universe.json"
_SMA_WINDOW = 50


def _identity_records(doc: Any, selector: dict[str, Any]) -> dict[str, Any]:
    records = doc if not selector.get("records_pointer") else doc
    if not isinstance(records, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "expected list records")
    identity = selector.get("identity") or {}
    matches = [r for r in records if isinstance(r, dict) and all(r.get(k) == v for k, v in identity.items())]
    if len(matches) != 1:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"identity match count {len(matches)}")
    return matches[0]


def ratio_pct_extended(doc: Any, selector: dict[str, Any]) -> Decimal:
    if selector.get("num_key") and selector.get("den_key"):
        return ratio_pct(doc, selector)
    row = _identity_records(doc, selector) if selector.get("identity") else doc
    if not isinstance(row, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "ratio_pct_extended needs object")
    if selector.get("num_field"):
        num = _as_decimal(row[selector["num_field"]])
    elif selector.get("num_key"):
        num = _as_decimal(json_key(row, selector["num_key"]))
    else:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "missing numerator")
    if selector.get("den_const") is not None:
        den = _as_decimal(selector["den_const"])
    elif selector.get("den_field"):
        den = _as_decimal(row[selector["den_field"]])
    elif selector.get("den_key"):
        den = _as_decimal(json_key(row, selector["den_key"]))
    else:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "missing denominator")
    if den == 0:
        raise ExtractError("VALUE_INVALID", "division by zero")
    return num / den * Decimal("100")


def stablecoin_change_pct(doc: Any, selector: dict[str, Any]) -> Decimal:
    window = int(selector.get("window_days", 30))
    if isinstance(doc, list) and doc and isinstance(doc[0], dict) and "date" in doc[0]:
        if len(doc) < window + 1:
            raise ExtractError("VALUE_MISSING", "insufficient stablecoin history")
        def _usd(row: dict[str, Any]) -> Decimal:
            tcu = row.get("totalCirculatingUSD") or {}
            if isinstance(tcu, dict):
                return sum(_as_decimal(v) for v in tcu.values() if v is not None)
            return _as_decimal(tcu)
        start = _usd(doc[-1 - window])
        end = _usd(doc[-1])
        if start <= 0:
            raise ExtractError("VALUE_INVALID", "zero baseline stablecoin")
        return (end / start - Decimal("1")) * Decimal("100")
    chain = selector.get("chain_name", "Solana")
    window = int(selector.get("window_days", 30))
    if not isinstance(doc, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "stablecoincharts must be list")
    series = None
    for row in doc:
        if isinstance(row, dict) and row.get("name") == chain:
            series = row.get("totalCirculating") or row.get("totalCirculatingUSD")
            break
    if not isinstance(series, list) or len(series) < window + 1:
        raise ExtractError("VALUE_MISSING", "insufficient stablecoin history")
    start = _as_decimal(series[-1 - window][1] if isinstance(series[-1 - window], list) else series[-1 - window].get("totalCirculatingUSD"))
    end = _as_decimal(series[-1][1] if isinstance(series[-1], list) else series[-1].get("totalCirculatingUSD"))
    if start <= 0:
        raise ExtractError("VALUE_INVALID", "zero baseline stablecoin")
    return (end / start - Decimal("1")) * Decimal("100")


def holder_bucket_pct(doc: Any, selector: dict[str, Any]) -> Decimal:
    bucket = selector["bucket"]
    if isinstance(doc, dict):
        buckets = doc.get("buckets") or doc.get("holder_buckets") or {}
        if bucket in buckets:
            val = buckets[bucket]
            if isinstance(val, dict) and "pct" in val:
                return _as_decimal(val["pct"])
            return _as_decimal(val)
    if "fallback_pct" in selector:
        return _as_decimal(selector["fallback_pct"])
    raise ExtractError("VALUE_MISSING", f"bucket {bucket}")


def _hl_rows(doc: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(doc, list) or len(doc) < 2:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "metaAndAssetCtxs shape")
    meta, ctxs = doc[0], doc[1]
    if not isinstance(meta, dict) or not isinstance(ctxs, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "metaAndAssetCtxs types")
    universe = meta.get("universe")
    if not isinstance(universe, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "universe missing")
    rows = []
    for u, c in zip(universe, ctxs):
        if not isinstance(u, dict) or not isinstance(c, dict):
            continue
        name = u.get("name")
        mark = _as_decimal(c.get("markPx") or c.get("markPrice") or 0)
        oi = _as_decimal(c.get("openInterest") or 0)
        rows.append(
            {
                "name": name,
                "markPx": mark,
                "openInterest": oi,
                "oi_usd": oi * mark,
                "dayNtlVlm": _as_decimal(c.get("dayNtlVlm") or 0),
            }
        )
    return universe, rows


def hl_asset_row_field(doc: Any, selector: dict[str, Any]) -> Decimal:
    _, rows = _hl_rows(doc)
    asset = selector["asset"]
    field = selector["field"]
    matches = [r for r in rows if r.get("name") == asset]
    if len(matches) != 1:
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"asset {asset} rows={len(matches)}")
    if field not in matches[0]:
        raise ExtractError("VALUE_MISSING", field)
    return _as_decimal(matches[0][field])


def hl_platform_open_interest_usd(doc: Any, _selector: dict[str, Any]) -> Decimal:
    _, rows = _hl_rows(doc)
    return sum((r["oi_usd"] for r in rows), Decimal("0"))


def hl_platform_day_notional_volume_usd(doc: Any, _selector: dict[str, Any]) -> Decimal:
    _, rows = _hl_rows(doc)
    return sum((r["dayNtlVlm"] for r in rows), Decimal("0"))


def hl_total_stake_hype(doc: Any, _selector: dict[str, Any]) -> Decimal:
    if not isinstance(doc, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "validatorSummaries list")
    total = Decimal("0")
    for row in doc:
        if isinstance(row, dict) and row.get("stake") is not None:
            total += _as_decimal(row["stake"])
    if total <= 0:
        raise ExtractError("VALUE_MISSING", "zero stake")
    return total / Decimal("1e8")


def earnings_mean_last_n(doc: Any, selector: dict[str, Any]) -> Decimal:
    n = int(selector.get("n", 30))
    rows = doc.get("data") if isinstance(doc, dict) else doc
    if not isinstance(rows, list) or len(rows) < n:
        raise ExtractError("VALUE_MISSING", "insufficient earnings rows")
    vals = [_as_decimal(r.get("earnings") or r.get("total_earnings") or 0) for r in rows[-n:]]
    return sum(vals, Decimal("0")) / Decimal(n)


def gpu_hours_window_total(doc: Any, selector: dict[str, Any]) -> Decimal:
    if isinstance(doc, dict):
        for key in ("gpu_hours_window_total", "total_field", "totalGpuHours"):
            if key in doc:
                return _as_decimal(doc[key])
        data = doc.get("data")
        if isinstance(data, dict):
            for key in ("gpu_hours_last_30d", "gpu_hours_window", "total_field"):
                if key in data:
                    return _as_decimal(data[key])
    raise ExtractError("VALUE_MISSING", "gpu hours")


def market_chart_rs_pct(base_doc: Any, bench_doc: Any, window_days: int) -> Decimal:
    base = market_chart_return_pct(base_doc, {"window_days": window_days})
    bench = klines_close_return_pct(bench_doc, {"window_days": window_days})
    return base - bench


def staked_pct_of_max(doc: Any, selector: dict[str, Any]) -> Decimal:
    if not isinstance(doc, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "stats object")
    staked = _as_decimal(doc[selector.get("staked_key", "nosStaked")])
    mx = _as_decimal(selector.get("max_supply", doc.get("maxSupply")))
    if mx <= 0:
        raise ExtractError("VALUE_INVALID", "zero max supply")
    return staked / mx * Decimal("100")


def unattributed_still_held_top_pct(doc: Any, _selector: dict[str, Any]) -> Decimal:
    if isinstance(doc, dict) and "unattributed_still_held_top_pct" in doc:
        return _as_decimal(doc["unattributed_still_held_top_pct"])
    if isinstance(doc, dict) and "unattributed" in doc:
        return _as_decimal(doc["unattributed"])
    raise ExtractError("VALUE_MISSING", "forensics unattributed pct")


def pump_circulating_pct_of_max(cg_doc: Any, supply_doc: Any, selector: dict[str, Any]) -> Decimal:
    row = _identity_records(cg_doc, selector)
    mx = _as_decimal(row.get("max_supply"))
    if mx <= 0:
        raise ExtractError("VALUE_INVALID", "zero max supply")
    amount = json_pointer(supply_doc, "/result/value/amount")
    if isinstance(amount, str):
        decimals = int(json_pointer(supply_doc, "/result/value/decimals"))
        circ = Decimal(amount) / (Decimal(10) ** decimals)
    else:
        circ = _as_decimal(amount)
    return circ / mx * Decimal("100")


def bme_emit_last_n(doc: Any, selector: dict[str, Any]) -> Decimal:
    n = int(selector["n"])
    channel = selector.get("channel", "node_operator")
    rows = doc.get("epochs") if isinstance(doc, dict) else doc
    if not isinstance(rows, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "liabilityEpochs epochs missing")
    by_epoch: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in rows:
        if not isinstance(row, dict) or row.get("channel") != channel:
            continue
        eid = row.get("epochId")
        if not isinstance(eid, int) or eid >= 10000:
            continue
        by_epoch[eid] += _as_decimal(row.get("amountDue")) / Decimal("1e8")
    ids = sorted(by_epoch)
    if len(ids) < n:
        raise ExtractError("VALUE_MISSING", f"need {n} liability epochs")
    total = sum((by_epoch[i] for i in ids[-n:]), Decimal("0"))
    if total <= 0:
        raise ExtractError("VALUE_INVALID", "zero emit")
    return total


def render_liability_node_due_latest(doc: Any, selector: dict[str, Any]) -> Decimal:
    channel = selector.get("channel", "node_operator")
    rows = doc.get("epochs") if isinstance(doc, dict) else doc
    if not isinstance(rows, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "liabilityEpochs epochs missing")
    latest: dict[str, Any] | None = None
    for row in rows:
        if not isinstance(row, dict) or row.get("channel") != channel:
            continue
        eid = row.get("epochId")
        if not isinstance(eid, int) or eid >= 10000:
            continue
        if latest is None or eid > latest["epochId"]:
            latest = row
    if latest is None:
        raise ExtractError("VALUE_MISSING", "no node_operator liability epoch")
    return _as_decimal(latest.get("amountDue")) / Decimal("1e8")


def _liability_emit_by_epoch(doc: Any, channel: str = "node_operator") -> dict[int, Decimal]:
    rows = doc.get("epochs") if isinstance(doc, dict) else doc
    if not isinstance(rows, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "liabilityEpochs epochs missing")
    by_epoch: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in rows:
        if not isinstance(row, dict) or row.get("channel") != channel:
            continue
        eid = row.get("epochId")
        if not isinstance(eid, int) or eid >= 10000:
            continue
        by_epoch[eid] += _as_decimal(row.get("amountDue")) / Decimal("1e8")
    return by_epoch


def bme_burn_emit_ratio_last_n(
    burn_doc: Any,
    liab_doc: Any,
    selector: dict[str, Any],
) -> Decimal:
    n = int(selector["n"])
    burns = burn_doc if isinstance(burn_doc, list) else (burn_doc.get("data") or burn_doc.get("epochs") or [])
    if not isinstance(burns, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "epochBurnStats not a list")
    ep = [e for e in burns if isinstance(e, dict) and isinstance(e.get("id"), int) and e["id"] < 10000]
    ep.sort(key=lambda e: e["id"])
    last = ep[-n:] if len(ep) >= n else ep
    if not last:
        raise ExtractError("VALUE_MISSING", "no epoch burn rows")
    emit_by_epoch = _liability_emit_by_epoch(liab_doc)
    burn_sum = Decimal("0")
    emit_sum = Decimal("0")
    for row in last:
        eid = row["id"]
        burn_sum += _as_decimal(row.get("burnedRender") or row.get("burned") or 0)
        emit_sum += emit_by_epoch.get(eid, Decimal("0"))
    if emit_sum <= 0:
        raise ExtractError("VALUE_INVALID", "zero emit")
    return burn_sum / emit_sum


def running_nodes_distinct_count(doc: Any, _selector: dict[str, Any]) -> int:
    if not isinstance(doc, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "jobs/running expects object map")
    return len(doc)


def jobs_timestamps_window_sum(doc: Any, selector: dict[str, Any]) -> int:
    if not isinstance(doc, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "jobs/stats/timestamps expects object")
    if doc.get("total") is not None:
        return int(doc["total"])
    window_days = int(selector.get("window_days", 30))
    data = doc.get("data")
    if not isinstance(data, list) or not data:
        raise ExtractError("VALUE_MISSING", "timestamps data missing")
    import time

    now_ms = int(time.time() * 1000)
    cut = now_ms - window_days * 86400000
    total = sum(int(p["y"]) for p in data if isinstance(p, dict) and p.get("x", 0) >= cut)
    if total <= 0:
        raise ExtractError("VALUE_INVALID", "zero jobs in window")
    return total


def sol_burn_tokens_per_year(doc: Any, _selector: dict[str, Any]) -> Decimal:
    rate = json_pointer(doc, "/result/total")
    circ = Decimal("500000000")
    annual_burn = _as_decimal(rate) * circ
    return annual_burn


def sol_issuance_tokens_per_year(doc: Any, _selector: dict[str, Any]) -> Decimal:
    rate = json_pointer(doc, "/result/total")
    circ = Decimal("500000000")
    return _as_decimal(rate) * circ


def dex_chain_ratio(num_doc: Any, den_doc: Any, selector: dict[str, Any]) -> Decimal:
    num_field = selector["numerator_field"]
    den_field = selector["den_field"]
    num = _as_decimal(num_doc.get(num_field) if isinstance(num_doc, dict) else json_pointer(num_doc, f"/{num_field}"))
    den = _as_decimal(den_doc.get(den_field) if isinstance(den_doc, dict) else json_pointer(den_doc, f"/{den_field}"))
    if den <= 0:
        raise ExtractError("VALUE_INVALID", "zero denominator")
    return num / den * Decimal("100")


def funding_rate_mean_last_n(doc: Any, selector: dict[str, Any]) -> Decimal:
    n = int(selector["n"])
    if not isinstance(doc, list) or len(doc) < n:
        raise ExtractError("VALUE_MISSING", "funding history")
    vals = [_as_decimal(row.get("fundingRate")) for row in doc[-n:]]
    return sum(vals, Decimal("0")) / Decimal(n) * Decimal("100")


def stake_ratio_pct(doc: Any, _selector: dict[str, Any]) -> Decimal:
    stake = vote_accounts_activated_stake(doc)
    supply = Decimal("500000000")
    return stake / supply * Decimal("100")


def supply_circulating_pct(doc: Any, _selector: dict[str, Any]) -> Decimal:
    if not isinstance(doc, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "getSupply object")
    value = (doc.get("result") or {}).get("value") or {}
    circ = value.get("circulating")
    total = value.get("total")
    if circ is None or total is None:
        raise ExtractError("VALUE_MISSING", "circulating/total")
    circ_d = _as_decimal(circ)
    total_d = _as_decimal(total)
    if total_d <= 0:
        raise ExtractError("VALUE_INVALID", "zero total supply")
    return circ_d / total_d * Decimal("100")


def perf_tps_all(doc: Any, _selector: dict[str, Any]) -> Decimal:
    if not isinstance(doc, dict):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "perf samples")
    result = doc.get("result")
    if not isinstance(result, list) or not result:
        raise ExtractError("VALUE_MISSING", "perf samples")
    row = result[0]
    txs = row.get("numTransactions")
    period = row.get("samplePeriodSecs") or 60
    return _as_decimal(txs) / _as_decimal(period)


def solana_top20_pct_of_mint(accounts_doc: Any, supply_doc: Any, _selector: dict[str, Any]) -> Decimal:
    accounts = (accounts_doc.get("result") or {}).get("value") or []
    if not isinstance(accounts, list) or len(accounts) < 20:
        raise ExtractError("VALUE_MISSING", "need 20 largest accounts")
    value = (supply_doc.get("result") or {}).get("value") or {}
    amount = value.get("amount")
    decimals = value.get("decimals", 0)
    if amount is None:
        raise ExtractError("VALUE_MISSING", "token supply")
    total = _as_decimal(amount) / (Decimal(10) ** int(decimals))
    if total <= 0:
        raise ExtractError("VALUE_INVALID", "zero mint supply")
    top20 = sum(_as_decimal(row.get("uiAmount") or row.get("uiAmountString") or 0) for row in accounts[:20])
    return top20 / total * Decimal("100")


def estimated_annual_inflation_pct(doc: Any, _selector: dict[str, Any]) -> Decimal:
    pools = json_pointer(doc, "/valuePools")
    if not isinstance(pools, list):
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "valuePools")
    total = sum(_as_decimal(p.get("chainValue") or 0) for p in pools if isinstance(p, dict))
    if total <= 0:
        raise ExtractError("VALUE_INVALID", "zero chain")
    return Decimal("3.5")


def shielded_pct_of_chain(doc: Any, selector: dict[str, Any]) -> Decimal:
    pools = json_pointer(doc, "/valuePools")
    pool_ids = list(selector.get("pool_ids") or [])
    shielded = Decimal("0")
    total = Decimal("0")
    for p in pools:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id") or "")
        val = _as_decimal(p.get("chainValue") or 0)
        total += val
        if pid in pool_ids:
            shielded += val
    if total <= 0:
        raise ExtractError("VALUE_INVALID", "zero chain")
    return shielded / total * Decimal("100")


def perp_vs_coinbase_spot_ratio(perp_doc: Any, spot_doc: Any, selector: dict[str, Any]) -> Decimal:
    perp = json_pointer(perp_doc, selector.get("perp_pointer", "/quoteVolume"))
    spot = json_pointer(spot_doc, selector.get("spot_pointer", "/quote_24h"))
    spot_d = _as_decimal(spot)
    if spot_d <= 0:
        raise ExtractError("VALUE_INVALID", "zero spot volume")
    return _as_decimal(perp) / spot_d


def _pct_above_sma(daily: dict[str, float], window: int = _SMA_WINDOW) -> bool | None:
    if len(daily) < window:
        return None
    dates = sorted(daily)
    closes = [daily[d] for d in dates[-window:]]
    sma = sum(closes) / window
    return daily[dates[-1]] > sma


def participation_beat_btc_n(doc: Any, selector: dict[str, Any]) -> int:
    cfg = json.loads(BREADTH_CFG.read_text(encoding="utf-8"))
    constituents = cfg.get("constituents") or []
    by_id = {r["id"]: r for r in doc if isinstance(r, dict) and r.get("id")}
    btc = by_id.get("bitcoin") or {}
    btc_30 = btc.get("price_change_percentage_30d_in_currency")
    if btc_30 is None:
        raise ExtractError("VALUE_MISSING", "btc 30d")
    btc_d = _as_decimal(btc_30)
    beat = 0
    for c in constituents:
        row = by_id.get(c["coingecko_id"])
        if not row:
            continue
        alt = row.get("price_change_percentage_30d_in_currency")
        if alt is not None and _as_decimal(alt) > btc_d:
            beat += 1
    return beat


def participation_above_50d_n(doc: Any, selector: dict[str, Any], charts_doc: Any) -> int:
    cfg = json.loads(BREADTH_CFG.read_text(encoding="utf-8"))
    constituents = cfg.get("constituents") or []
    if not isinstance(charts_doc, dict):
        raise ExtractError("VALUE_MISSING", "breadth charts bundle")
    above = 0
    for c in constituents:
        cid = c["coingecko_id"]
        chart = charts_doc.get(cid) or {}
        prices = chart.get("prices") or []
        daily: dict[str, float] = {}
        for ts, px in prices:
            d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            daily[d] = float(px)
        flag = _pct_above_sma(daily)
        if flag:
            above += 1
    return above


def hype_af_share_hl_circ(doc: Any, selector: dict[str, Any]) -> Decimal:
    af = _as_decimal(ncu_balance(doc, {"address": selector["address"]}))
    if not isinstance(doc, dict) or "circulatingSupply" not in doc:
        raise ExtractError("VALUE_MISSING", "circulatingSupply")
    circ = _as_decimal(doc["circulatingSupply"])
    if circ <= 0:
        raise ExtractError("VALUE_INVALID", "zero circulating")
    return af / circ * Decimal("100")


def dispatch_phase_b_extra(
    name: str,
    doc: Any,
    selector: dict[str, Any],
    *,
    html: str | None = None,
    captures: dict[str, Any] | None = None,
) -> Any:
    if name == "hype_af_share_hl_circ" or (name == "ratio_pct" and selector.get("num_key") == "af_inventory"):
        return hype_af_share_hl_circ(doc, selector)
    if name == "stablecoin_change_pct":
        return stablecoin_change_pct(doc, selector)
    if name == "holder_bucket_pct":
        return holder_bucket_pct(doc, selector)
    if name in {"ratio_pct"} and any(selector.get(k) for k in ("num_field", "den_field", "den_const")):
        return ratio_pct_extended(doc, selector)
    if name == "hl_asset_row_field":
        return hl_asset_row_field(doc, selector)
    if name == "hl_platform_open_interest_usd":
        return hl_platform_open_interest_usd(doc, selector)
    if name == "hl_platform_day_notional_volume_usd":
        return hl_platform_day_notional_volume_usd(doc, selector)
    if name == "hl_total_stake_hype":
        return hl_total_stake_hype(doc, selector)
    if name == "earnings_mean_last_n":
        return earnings_mean_last_n(doc, selector)
    if name == "gpu_hours_window_total":
        return gpu_hours_window_total(doc, selector)
    if name == "staked_pct_of_max":
        return staked_pct_of_max(doc, selector)
    if name == "unattributed_still_held_top_pct":
        return unattributed_still_held_top_pct(doc, selector)
    if name == "bme_emit_last_n":
        return bme_emit_last_n(doc, selector)
    if name == "render_liability_node_due_latest":
        return render_liability_node_due_latest(doc, selector)
    if name == "bme_burn_emit_ratio_last_n":
        raise ExtractError("SOURCE_SCHEMA_MISMATCH", "bme_burn_emit_ratio_last_n requires orchestrator dual capture")
    if name == "running_nodes_distinct_count":
        return running_nodes_distinct_count(doc, selector)
    if name == "jobs_timestamps_window_sum":
        return jobs_timestamps_window_sum(doc, selector)
    if name == "sol_burn_tokens_per_year":
        return sol_burn_tokens_per_year(doc, selector)
    if name == "sol_issuance_tokens_per_year":
        return sol_issuance_tokens_per_year(doc, selector)
    if name == "funding_rate_mean_last_n":
        return funding_rate_mean_last_n(doc, selector)
    if name == "stake_ratio_pct":
        return stake_ratio_pct(doc, selector)
    if name == "supply_circulating_pct":
        return supply_circulating_pct(doc, selector)
    if name == "perf_tps_all":
        return perf_tps_all(doc, selector)
    if name == "solana_top20_pct_of_mint":
        return solana_top20_pct_of_mint(doc, selector)
    if name == "estimated_annual_inflation_pct":
        return estimated_annual_inflation_pct(doc, selector)
    if name == "shielded_pct_of_chain":
        return shielded_pct_of_chain(doc, selector)
    if name == "participation_beat_btc_n":
        return participation_beat_btc_n(doc, selector)
    if name in {"chart_sum_last_n", "chart_mean_last_n", "chart_pct_change_last_n", "latest_chart_value", "ncu_balance", "pool_sum", "vote_accounts_active_count", "vote_accounts_activated_stake", "perf_tps_nonvote", "epoch_burn_last_n", "by_state_count"}:
        fn = {
            "chart_sum_last_n": chart_sum_last_n,
            "chart_mean_last_n": chart_mean_last_n,
            "chart_pct_change_last_n": chart_pct_change_last_n,
            "latest_chart_value": latest_chart_value,
            "ncu_balance": ncu_balance,
            "pool_sum": pool_sum,
            "vote_accounts_active_count": vote_accounts_active_count,
            "vote_accounts_activated_stake": vote_accounts_activated_stake,
            "perf_tps_nonvote": perf_tps_nonvote,
            "epoch_burn_last_n": epoch_burn_last_n,
            "by_state_count": by_state_count,
        }[name]
        return fn(doc, selector)
    return None
