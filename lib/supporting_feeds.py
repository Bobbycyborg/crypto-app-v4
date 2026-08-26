"""Supporting context feeds — not market-family votes. Timestamped + linked."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import certifi
import requests

from lib.coingecko_api import auth_status
from lib.paths import CACHE, CONFIG
from lib.wallet import SOLANA_RPC, load_assets_config

FNG_URL = "https://api.alternative.me/fng/"
FNG_ATTRIBUTION = "Data by Alternative.me — https://alternative.me/crypto/fear-and-greed-index/"
BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/premiumIndex"
BINANCE_FUNDING_HIST = "https://fapi.binance.com/fapi/v1/fundingRate"
BINANCE_FUNDING_DOCS = "https://binance-docs.github.io/apidocs/futures/en/#index-price-and-mark-price"
BINANCE_FUNDING_HIST_DOCS = "https://binance-docs.github.io/apidocs/futures/en/#get-funding-rate-history"
_FUNDING_HIST_LIMIT = 90
SOLANA_RPC_DOCS = "https://solana.com/docs/rpc/http/gettokenlargestaccounts"

from lib.v3.etf_flows import fetch_etf_flows
from lib.v3.fragility_feeds import fetch_btc_fragility_feeds


def _load_known_labels() -> dict[str, str]:
    path = CONFIG / "known-spl-accounts.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
        return dict(data.get("accounts") or {})
    except Exception:
        return {}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_json(url: str, params: dict | None = None, timeout: int = 30) -> Any:
    r = requests.get(url, params=params, timeout=timeout, verify=certifi.where())
    r.raise_for_status()
    return r.json()


def _rpc_urls() -> list[str]:
    urls = [SOLANA_RPC]
    try:
        from lib.helius_client import rpc_url

        urls.insert(0, rpc_url())
    except Exception:
        pass
    return urls


def _rpc_on_url(url: str, method: str, params: list[Any], *, timeout: int = 20) -> Any:
    r = requests.post(
        url,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=timeout,
        verify=certifi.where(),
    )
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise RuntimeError(body["error"])
    return body["result"]


def _sol_supply_coingecko() -> tuple[float | None, float | None]:
    try:
        from lib.coingecko_api import get_json as cg_get

        d = cg_get(
            "https://api.coingecko.com/api/v3/coins/solana",
            {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false",
            },
        )
        md = d.get("market_data") or {}
        tot = md.get("total_supply")
        circ = md.get("circulating_supply")
        return (
            float(tot) if isinstance(tot, (int, float)) else None,
            float(circ) if isinstance(circ, (int, float)) else None,
        )
    except Exception:
        return None, None


def _rpc(method: str, params: list[Any]) -> Any:
    last = None
    for url in _rpc_urls():
        for attempt in range(2):
            try:
                r = requests.post(
                    url,
                    json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                    timeout=12,
                    verify=certifi.where(),
                )
                if r.status_code == 429:
                    time.sleep(1.5 * (2 ** attempt))
                    last = RuntimeError(f"429 {method}")
                    continue
                r.raise_for_status()
                body = r.json()
                if "error" in body:
                    last = RuntimeError(body["error"])
                    time.sleep(0.4)
                    break
                return body["result"]
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(0.6 * (attempt + 1))
        time.sleep(0.3)
    raise RuntimeError(last or f"RPC {method} failed")


def fetch_fear_greed(limit: int = 7) -> dict[str, Any]:
    """Alternative.me Fear & Greed — sentiment context only."""
    fetched_at = _now()
    try:
        body = _get_json(FNG_URL, {"limit": str(limit), "format": "json"})
        rows = body.get("data") or []
        current = rows[0] if rows else {}
        trend = []
        for row in rows[:limit]:
            trend.append(
                {
                    "value": int(row["value"]) if row.get("value") is not None else None,
                    "classification": row.get("value_classification"),
                    "timestamp": row.get("timestamp"),
                }
            )
        prev = trend[1]["value"] if len(trend) > 1 else None
        cur_val = trend[0]["value"] if trend else None
        delta = (cur_val - prev) if cur_val is not None and prev is not None else None
        return {
            "ok": True,
            "feed_id": "fear_greed",
            "role": "sentiment_context_only",
            "not_a_market_vote": True,
            "source": "alternative.me",
            "source_url": FNG_URL,
            "attribution": FNG_ATTRIBUTION,
            "fetched_at": fetched_at,
            "current": trend[0] if trend else None,
            "recent_trend": trend,
            "delta_vs_prior": delta,
        }
    except Exception as exc:
        return {
            "ok": False,
            "feed_id": "fear_greed",
            "role": "sentiment_context_only",
            "source": "alternative.me",
            "source_url": FNG_URL,
            "attribution": FNG_ATTRIBUTION,
            "fetched_at": fetched_at,
            "error": str(exc),
        }


def _funding_percentile_rank(current: float, history: list[float]) -> float | None:
    if not history:
        return None
    le = sum(1 for r in history if r <= current)
    return round(le / len(history) * 100, 1)


def fetch_btc_funding() -> dict[str, Any]:
    """Binance BTCUSDT perp funding — current rate + descriptive history stats."""
    fetched_at = _now()
    try:
        row = _get_json(BINANCE_FUNDING_URL, {"symbol": "BTCUSDT"})
        hist_rows = _get_json(
            BINANCE_FUNDING_HIST,
            {"symbol": "BTCUSDT", "limit": _FUNDING_HIST_LIMIT},
        )
        rate = float(row["lastFundingRate"])
        hist_rates = [float(r["fundingRate"]) for r in hist_rows if r.get("fundingRate") is not None]
        if hist_rates:
            min_r = min(hist_rates)
            max_r = max(hist_rates)
            pct_rank = _funding_percentile_rank(rate, hist_rates)
        else:
            min_r = max_r = None
            pct_rank = None
        return {
            "ok": True,
            "feed_id": "btc_funding",
            "role": "fragility_context_only",
            "not_a_macro_or_btc_regime_vote": True,
            "no_bearish_threshold": True,
            "source": "binance_futures",
            "source_url": BINANCE_FUNDING_DOCS,
            "history_source_url": BINANCE_FUNDING_HIST_DOCS,
            "fetched_at": fetched_at,
            "symbol": "BTCUSDT",
            "last_funding_rate": rate,
            "last_funding_rate_pct": round(rate * 100, 6),
            "mark_price_usd": float(row.get("markPrice") or 0) or None,
            "next_funding_time_ms": row.get("nextFundingTime"),
            "history_n": len(hist_rates),
            "range_min_pct": round(min_r * 100, 6) if min_r is not None else None,
            "range_max_pct": round(max_r * 100, 6) if max_r is not None else None,
            "percentile_rank": pct_rank,
            "percentile_note": "Rank within last 90 Binance 8h prints — descriptive, no bearish cutoff.",
            "note": "Single funding pipeline for Card 6 — current + history stats.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "feed_id": "btc_funding",
            "role": "fragility_context_only",
            "source": "binance_futures",
            "source_url": BINANCE_FUNDING_DOCS,
            "fetched_at": fetched_at,
            "error": str(exc),
        }


def fetch_token_concentration(mint: str, symbol: str, limit: int = 20) -> dict[str, Any]:
    """Top SPL token accounts — concentration proxy, NOT whale labels."""
    fetched_at = _now()
    labels = _load_known_labels()
    try:
        supply = _rpc("getTokenSupply", [mint])
        total_ui = float(supply["value"]["uiAmount"] or 0)
        largest = _rpc("getTokenLargestAccounts", [mint])
        accounts = []
        top_sum = 0.0
        for i, row in enumerate((largest.get("value") or [])[:limit]):
            ui = float(row.get("uiAmount") or 0)
            top_sum += ui
            pct = (ui / total_ui * 100) if total_ui > 0 else None
            addr = row.get("address")
            accounts.append(
                {
                    "rank": i + 1,
                    "token_account": addr,
                    "ui_amount": ui,
                    "pct_of_supply": round(pct, 4) if pct is not None else None,
                    "label": labels.get(addr),
                    "label_status": "KNOWN" if addr in labels else "UNLABELLED",
                }
            )
        top5_sum = sum(a["ui_amount"] for a in accounts[:5])
        top5_pct = (top5_sum / total_ui * 100) if total_ui > 0 else None
        return {
            "ok": True,
            "feed_id": "token_concentration",
            "role": "concentration_proxy_only",
            "not_whale_tracking": True,
            "symbol": symbol,
            "mint": mint,
            "source": "solana_rpc",
            "source_url": SOLANA_RPC_DOCS,
            "fetched_at": fetched_at,
            "total_supply_ui": total_ui,
            "top5_pct_of_supply": round(top5_pct, 4) if top5_pct is not None else None,
            "top_accounts": accounts,
            "disclaimer": (
                "Top token accounts — often LP pools, treasuries, or CEX wallets. "
                "Not labelled whales unless address is in known-spl-accounts config."
            ),
        }
    except Exception as exc:
        return {
            "ok": False,
            "feed_id": "token_concentration",
            "symbol": symbol,
            "mint": mint,
            "source": "solana_rpc",
            "source_url": SOLANA_RPC_DOCS,
            "fetched_at": fetched_at,
            "error": str(exc),
        }


def fetch_owner_mint_balance(owner: str, mint: str) -> float | None:
    try:
        res = _rpc(
            "getTokenAccountsByOwner",
            [owner, {"mint": mint}, {"encoding": "jsonParsed"}],
        )
        return sum(
            float(a["account"]["data"]["parsed"]["info"]["tokenAmount"].get("uiAmount") or 0)
            for a in (res or {}).get("value", [])
        )
    except Exception:
        return None


def fetch_solana_network() -> dict[str, Any]:
    """getInflationRate + getVoteAccounts / supply. Fail loud after backoff."""
    fetched_at = _now()
    supply_source = "solana_rpc getSupply"
    supply_provenance = "LIVE"
    try:
        infl = _rpc("getInflationRate", [])
        votes = _rpc("getVoteAccounts", [])
        tot_sol: float | None = None
        circ_sol: float | None = None
        supply_err: str | None = None
        for url in _rpc_urls():
            try:
                supply = _rpc_on_url(
                    url,
                    "getSupply",
                    [{"excludeNonCirculatingAccountsList": True}],
                    timeout=10,
                )
                val = (supply or {}).get("value") or {}
                tot_lamports = float(val.get("total") or 0)
                circ_lamports = float(val.get("circulating") or 0)
                if tot_lamports:
                    tot_sol = tot_lamports / 1e9
                    circ_sol = circ_lamports / 1e9 if circ_lamports else None
                    supply_source = f"solana_rpc getSupply ({url.split('?')[0]})"
                    break
            except Exception as exc:  # noqa: BLE001
                supply_err = str(exc)
        if tot_sol is None:
            tot_cg, circ_cg = _sol_supply_coingecko()
            tot_sol = tot_cg
            circ_sol = circ_cg
            if tot_sol is not None:
                supply_source = "coingecko coins/solana market_data supply (getSupply fallback)"
                supply_provenance = "SUBSTITUTE_SOURCE"
            elif supply_err:
                raise RuntimeError(supply_err)
        total = float((infl or {}).get("total") or 0)
        current = votes.get("current") or []
        delinquent = votes.get("delinquent") or []
        staked = sum(float(v.get("activatedStake") or 0) for v in current + delinquent) / 1e9
        stake_pct = (staked / tot_sol * 100.0) if tot_sol else None
        infl_pct = total * 100.0 if total else None
        issuance_yr = (total * tot_sol) if total and tot_sol else None
        return {
            "ok": infl_pct is not None and stake_pct is not None,
            "inflation_pct": infl_pct,
            "stake_pct": stake_pct,
            "staked_sol": staked,
            "total_sol": tot_sol,
            "circ_sol": circ_sol,
            "issuance_yr": issuance_yr,
            "source": f"solana_rpc getInflationRate + getVoteAccounts + {supply_source}",
            "supply_provenance": supply_provenance,
            "provenance": "SUBSTITUTE_SOURCE" if supply_provenance == "SUBSTITUTE_SOURCE" else "LIVE",
            "cache_fallback": supply_provenance == "SUBSTITUTE_SOURCE",
            "freshness": "STALE" if supply_provenance == "SUBSTITUTE_SOURCE" else "CURRENT",
            "fetched_at": fetched_at,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
            "source": "solana_rpc getInflationRate + getVoteAccounts + getSupply",
            "fetched_at": fetched_at,
        }


def fetch_portfolio_concentration() -> dict[str, Any]:
    """Concentration proxy for all portfolio SPL mints."""
    fetched_at = _now()
    assets = load_assets_config()["assets"]
    by_symbol: dict[str, Any] = {}
    for a in assets:
        mint = a.get("mint")
        sym = a.get("symbol")
        if not mint or not sym:
            continue
        by_symbol[sym] = fetch_token_concentration(mint, sym)
        time.sleep(0.35)
    return {
        "feed_id": "portfolio_concentration",
        "fetched_at": fetched_at,
        "symbols": by_symbol,
    }


def coingecko_reliability_status() -> dict[str, Any]:
    """Demo/pro key presence — reliability upgrade, not a signal."""
    status = auth_status()
    return {
        "feed_id": "coingecko_auth",
        "role": "reliability_only",
        "not_a_signal": True,
        "fetched_at": _now(),
        "source": "coingecko",
        "source_url": "https://www.coingecko.com/en/api/pricing",
        "env_paths": [
            str(CONFIG / "coingecko.local.env"),
            ".cursor/mcps/coingecko/.env",
        ],
        **status,
    }


def gather_supporting_feeds(*, include_concentration: bool = True) -> dict[str, Any]:
    """All supporting feeds for V3 evidence bundle."""
    fetched_at = _now()
    btc_funding = fetch_btc_funding()
    out: dict[str, Any] = {
        "schema": "supporting-feeds-v1",
        "fetched_at": fetched_at,
        "rules": {
            "not_market_family_votes": True,
            "no_classifier_thresholds": True,
            "reuse_on_relevant_cards_only": True,
        },
        "fear_greed": fetch_fear_greed(),
        "btc_funding": btc_funding,
        "btc_fragility": fetch_btc_fragility_feeds(fetched_at, btc_funding),
        "etf_flows": fetch_etf_flows(),
        "coingecko_auth": coingecko_reliability_status(),
    }
    if include_concentration:
        out["portfolio_concentration"] = fetch_portfolio_concentration()
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE / "supporting-feeds.json"
    cache_path.write_text(json.dumps(out, indent=2))
    out["cache_path"] = str(cache_path)
    return out


def load_cached_supporting_feeds() -> dict[str, Any] | None:
    path = CACHE / "supporting-feeds.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text())
