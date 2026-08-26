"""Price fetch freshness helpers and HTML data-snapshot block."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.paths import CONFIG, REPORTS

FRESH_SEC = 300
STALE_SEC = 900

PRICE_SOURCE_KEYS = ("coingecko", "dexscreener", "binance", "geckoterminal", "coinbase")

SOURCE_LINKS = {
    "coingecko": "https://www.coingecko.com/en/api",
    "dexscreener": "https://docs.dexscreener.com/",
    "binance": "https://binance-docs.github.io/apidocs/spot/en/",
    "geckoterminal": "https://www.geckoterminal.com/dex-api",
    "coinbase": "https://docs.cdp.coinbase.com/coinbase-app/docs/track/api-pricing",
    "solana_rpc": "https://docs.solana.com/api/http",
    "blockchain_info": "https://api.blockchain.info/charts/market-price",
    "render_foundation": "https://stats.renderfoundation.com/",
}


def age_sec(timestamp: str | None) -> float | None:
    if not timestamp:
        return None
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds()
    except Exception:
        return None


def freshness_status(timestamp: str | None) -> str:
    age = age_sec(timestamp)
    if age is None:
        return "MISSING"
    if age <= FRESH_SEC:
        return "FRESH"
    if age <= STALE_SEC:
        return "AGING"
    return "STALE"


def load_integrity_json() -> dict[str, Any] | None:
    path = REPORTS / "data-integrity" / "latest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def price_check_status(sources: dict[str, Any], comparisons: list[dict]) -> str:
    if sources.get("price_check_status"):
        return str(sources["price_check_status"])
    summary = sources.get("compare_summary") or {}
    if summary.get("missing", 0) > 0:
        return "RED"
    if summary.get("diverge", 0) > 0:
        return "RED"
    if sources.get("prices_fallback_used"):
        return "AMBER"
    if summary.get("single_source", 0) > 0:
        return "AMBER"
    fresh = sources.get("freshness") or {}
    if any(v in ("STALE", "MISSING") for v in fresh.values()):
        return "AMBER"
    return "GREEN"


def build_snapshot_from_sources(sources: dict[str, Any], portfolio_fetched_at: str | None) -> dict[str, Any]:
    fetched = dict(sources.get("fetched_at") or {})
    snapshot_at = fetched.get("snapshot") or fetched.get("compare") or portfolio_fetched_at or datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    freshness = sources.get("freshness") or {
        k: freshness_status(fetched.get(k)) for k in PRICE_SOURCE_KEYS
    }
    comparisons = sources.get("comparisons") or []
    status = price_check_status(sources, comparisons)
    thr = sources.get("diverge_alert_pct", 2.0)
    thr_status = sources.get("diverge_threshold_status", "PROVISIONAL")
    return {
        "snapshot_at": snapshot_at,
        "price_check_status": status,
        "diverge_alert_pct": thr,
        "diverge_threshold_status": thr_status,
        "fetched_at": fetched,
        "freshness": freshness,
        "prices_fallback_used": bool(sources.get("prices_fallback_used")),
        "coingecko_auth": sources.get("coingecko_auth"),
        "comparisons": comparisons,
        "source_links": SOURCE_LINKS,
        "sources_checked": list(sources.get("sources") or PRICE_SOURCE_KEYS),
    }


def snapshot_html(snapshot: dict[str, Any]) -> str:
    status = snapshot.get("price_check_status", "AMBER")
    status_cls = {"GREEN": "ds-green", "AMBER": "ds-amber", "RED": "ds-red"}.get(status, "ds-amber")
    at = snapshot.get("snapshot_at", "")
    display_at = at.replace("T", " ").replace("Z", " UTC") if at else "—"
    thr = snapshot.get("diverge_alert_pct", 2.0)
    thr_note = snapshot.get("diverge_threshold_status", "PROVISIONAL")
    fallback = snapshot.get("prices_fallback_used")
    fetched = snapshot.get("fetched_at") or {}
    fresh = snapshot.get("freshness") or {}
    links = snapshot.get("source_links") or SOURCE_LINKS
    labels = {
        "coingecko": "CoinGecko",
        "dexscreener": "DexScreener",
        "binance": "Binance",
        "geckoterminal": "GeckoTerminal",
        "coinbase": "Coinbase",
    }

    def src_line(key: str) -> str:
        ts = fetched.get(key) or "—"
        fr = fresh.get(key, "MISSING")
        url = links.get(key, "#")
        fr_cls = "c-green" if fr == "FRESH" else ("c-orange" if fr == "AGING" else "c-muted")
        return (
            f'<span class="ds-src"><a href="{url}" target="_blank" rel="noopener">{labels[key]}</a> '
            f'<span class="{fr_cls}">{fr}</span> · {ts}</span>'
        )

    src_html = "".join(src_line(k) for k in PRICE_SOURCE_KEYS)
    fb = '<span class="ds-fb c-orange">FALLBACK active</span>' if fallback else ""
    return (
        '<section class="data-snapshot" aria-label="Data snapshot">'
        '<div class="ds-head">'
        '<span class="label">DATA SNAPSHOT · PRICE CHECK</span>'
        f'<span class="ds-status {status_cls}">{status}</span>'
        '</div>'
        f'<div class="ds-line"><b>Snapshot as of</b> {display_at}</div>'
        f'<div class="ds-line ds-sources">{src_html}</div>'
        f'<div class="ds-line ds-thr">5-source compare · agree threshold {thr}% · '
        f'<span class="c-muted">{thr_note}</span> {fb}</div>'
        '</section>'
    )
