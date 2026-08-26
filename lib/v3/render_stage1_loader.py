"""Canonical RENDER Stage-1 evidence merge.

Priority (ChatGPT-approved):
  1. RENDER-STAGE1-FINDINGS.md §16 Completion Pass
  2. render-evidence-table.json completion rows
  3. RENDER-BUYER-SELLER-FINDINGS.md
  4. render-buyer-seller-evidence.json
  5. MM registry intersections inside buyer pack
  6. Earlier Stage-1 only where not superseded

Earlier Stage-1 UNKNOWN on buyers / live burn / value-capture unproven is SUPERSEDED.
No live research in this module — pack files only.
No silent production fallbacks — missing pack fields stay None / UNKNOWN.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.paths import REPORTS

STAGE1 = REPORTS / "render-forensics" / "stage1-evidence"
BUYER = REPORTS / "render-forensics" / "buyer-seller-quality"
COMPLETION = STAGE1 / "raw" / "completion" / "completion_analysis"

# Intentional historical constant (labelled) — not a live scrape fallback
ATH_USD_KNOWN = 13.53
ATH_DATE_KNOWN = "2024-03-17"


class RenderEvidenceError(RuntimeError):
    """Required RENDER evidence pack missing or unusable."""


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path, label: str) -> Any:
    data = _load(path)
    if data is None:
        raise RenderEvidenceError(f"Missing required RENDER evidence: {label} ({path})")
    return data


def _table_lookup(rows: list[dict], metric: str) -> dict | None:
    for r in rows or []:
        if r.get("metric") == metric:
            return r
    return None


def _table_value(rows: list[dict], metric: str) -> Any:
    row = _table_lookup(rows, metric)
    if not row:
        return None
    return row.get("value")


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("%", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _parse_oi_vs_30d_max_pct(raw: Any) -> float | None:
    """Parse evidence text like 'Within 30d range (~94% of 30d max)' → 94.0."""
    if isinstance(raw, (int, float)):
        return float(raw)
    if not raw:
        return None
    m = re_search_pct(str(raw))
    return m


def re_search_pct(text: str) -> float | None:
    import re

    m = re.search(r"~?\s*(\d+(?:\.\d+)?)\s*%\s*of\s*30d", text, re.I)
    if not m:
        return None
    return float(m.group(1))


def load_render_canonical() -> dict[str, Any]:
    """One unambiguous RENDER evidence state for V3 wiring."""
    evidence_table = _require(STAGE1 / "render-evidence-table.json", "evidence table")
    if isinstance(evidence_table, dict):
        evidence_table = evidence_table.get("rows") or evidence_table.get("metrics") or []
    if not evidence_table:
        raise RenderEvidenceError("render-evidence-table.json has no rows")

    burn = _require(COMPLETION / "burn_vs_emissions_joined.json", "BME join")
    buyer = _require(BUYER / "render-buyer-seller-evidence.json", "buyer/seller pack")
    market = _require(STAGE1 / "raw" / "market_analysis_snapshot.json", "market snapshot")

    supply_recon = _load(COMPLETION / "supply_reconciliation.json") or {}
    nodes_frames = _load(
        STAGE1 / "raw" / "completion" / "api_api_nodes_and_frames.json"
    ) or {}

    buyer_totals = buyer.get("totals") or {}
    buyer_conc = buyer.get("concentration") or {}
    buyer_win = buyer.get("window") or {}
    if not buyer_totals:
        raise RenderEvidenceError("buyer pack missing totals")

    wm = None
    for row in buyer.get("mm_registry_intersections") or []:
        label = row.get("label") if isinstance(row.get("label"), dict) else {}
        ent = label.get("entity") or row.get("entity")
        wallet = row.get("wallet") or ""
        if "MfDu" in wallet or (isinstance(ent, str) and "Wintermute" in ent):
            wm = row
            break
    if wm is None:
        for row in buyer.get("top_gross_buyers") or []:
            if str(row.get("wallet", "")).startswith("MfDu"):
                wm = row
                break

    supply_info = burn.get("supplyInfo") or {}
    w4 = burn.get("window_last4") or {}
    w8 = burn.get("window_last8") or {}
    if not w4:
        raise RenderEvidenceError("BME pack missing window_last4")

    # Network — pack / table only; never invent frames/nodes
    frames = _as_float(_table_value(evidence_table, "Cumulative frames rendered"))
    if frames is None and isinstance(nodes_frames, dict):
        frames = _as_float(nodes_frames.get("frames"))
    nodes_inception = _as_float(_table_value(evidence_table, "Nodes since inception"))
    nodes_api = None
    if isinstance(nodes_frames, dict):
        nodes_api = _as_float(nodes_frames.get("nodes"))
    if nodes_api is None:
        nodes_api = _as_float(
            _table_value(evidence_table, "Nodes (Foundation nodes_and_frames API)")
        )

    rs = market.get("rs") or {}

    def _pp(key: str) -> float | None:
        block = rs.get(key) or {}
        v = block.get("pp")
        return float(v) if isinstance(v, (int, float)) else None

    fut_row = _table_lookup(evidence_table, "Binance fut/spot 24h quote vol ratio")
    oi_row = _table_lookup(evidence_table, "Binance OI notional (approx)")
    fund_row = _table_lookup(evidence_table, "Latest funding / 8h")
    oi_hist_row = _table_lookup(evidence_table, "OI unusual vs 30d Binance hist")
    chg7 = _table_lookup(evidence_table, "Price change 7d")
    chg30 = _table_lookup(evidence_table, "Price change 30d")
    chg1y = _table_lookup(evidence_table, "Price change 1y")
    dd_row = _table_lookup(evidence_table, "Drawdown from USD ATH")

    price_usd = _as_float(market.get("binance_spot_price"))
    drawdown_pct = _as_float((dd_row or {}).get("value"))
    if drawdown_pct is None and price_usd is not None:
        ath_live = _as_float((dd_row or {}).get("ath_usd"))
        if ath_live is None:
            raise RenderEvidenceError(
                "No RENDER drawdown in evidence table — will not compute from ATH_USD_KNOWN"
            )

    fut_spot = _as_float((fut_row or {}).get("value"))
    if fut_spot is None:
        fut_spot = _as_float(market.get("fut_spot_ratio"))
    oi_notional = _as_float((oi_row or {}).get("value"))
    oi_vs_30d = _parse_oi_vs_30d_max_pct((oi_hist_row or {}).get("value"))

    funding_latest = None
    if fund_row is not None and fund_row.get("value") is not None:
        funding_latest = _as_float(fund_row.get("value"))
    elif market.get("funding_latest") is not None:
        funding_latest = _as_float(market.get("funding_latest"))

    funding_pctile = market.get("funding_pctile_100")
    if funding_pctile is not None:
        funding_pctile = _as_float(funding_pctile)

    as_of = (
        buyer.get("gathered_at_utc")
        or burn.get("gathered_at_utc")
        or market.get("fetched_at_utc")
    )
    if not as_of:
        raise RenderEvidenceError("No gathered_at / fetched_at on required packs")

    usage_read = "REAL USAGE" if frames is not None else "UNKNOWN"
    deriv_read = "LEVERAGE PRESENT" if fut_spot is not None else "UNKNOWN"

    return {
        "meta": {
            "fetched_at_utc": as_of,
            "canonical_priority": [
                "FINDINGS §16",
                "render-evidence-table.json",
                "RENDER-BUYER-SELLER-FINDINGS",
                "render-buyer-seller-evidence.json",
                "MM intersections in buyer pack",
            ],
            "superseded": [
                "Earlier Stage-1 buyer/seller = UNKNOWN",
                "Earlier Stage-1 live burn/mint = UNKNOWN",
                "Earlier Stage-1 value capture = unproven",
            ],
            "paths": {
                "findings": str(STAGE1 / "RENDER-STAGE1-FINDINGS.md"),
                "evidence_table": str(STAGE1 / "render-evidence-table.json"),
                "buyer_findings": str(BUYER / "RENDER-BUYER-SELLER-FINDINGS.md"),
                "buyer_json": str(BUYER / "render-buyer-seller-evidence.json"),
                "bme": str(COMPLETION / "burn_vs_emissions_joined.json"),
            },
        },
        "stance_headline": "NETWORK USAGE REAL · RECENT BME NET INFLATIONARY · MARKET STRUCTURE WEAK",
        "price_structure": {
            "now_usd": price_usd,
            "ath_usd": ATH_USD_KNOWN,
            "ath_date": ATH_DATE_KNOWN,
            "ath_note": "Historical CoinGecko ATH event — intentional labelled constant",
            "drawdown_pct": drawdown_pct,
            "change_7d_pct": _as_float((chg7 or {}).get("value")),
            "change_30d_pct": _as_float((chg30 or {}).get("value")),
            "change_1y_pct": _as_float((chg1y or {}).get("value")),
        },
        "rs_vs_btc_pp": {
            "7": _pp("rs_btc_7d"),
            "30": _pp("rs_btc_30d"),
            "90": _pp("rs_btc_90d"),
        },
        "rs_vs_sol_pp": {
            "7": _pp("rs_sol_7d"),
            "30": _pp("rs_sol_30d"),
            "90": _pp("rs_sol_90d"),
        },
        "derivatives": {
            "fut_spot_ratio": fut_spot,
            "oi_notional_usd": oi_notional,
            "oi_vs_30d_max_pct": oi_vs_30d,
            "funding_latest": funding_latest,
            "funding_pctile_100": funding_pctile,
            "read": deriv_read,
            "note": (
                "Derivatives active; not an extreme top signal by itself."
                if fut_spot is not None
                else "Derivatives slice missing from evidence packs."
            ),
        },
        "network": {
            "frames_cumulative": frames,
            "nodes_since_inception": nodes_inception,
            "nodes_api_count": nodes_api,
            "nodes_label": "Nodes since inception (evidence table) — not active nodes today / not API node count",
            "usage_read": usage_read,
            "source_url": "https://stats.renderfoundation.com/",
        },
        "bme": {
            "read": "RECENT BME NET INFLATIONARY",
            "primary_window": "last_4_epochs",
            "last4": {
                "burned": w4.get("burn_sum_render"),
                "node_emissions": w4.get("node_operator_emit_sum_render"),
                "ratio": w4.get("burn_emit_ratio"),
                "from": w4.get("from"),
                "to": w4.get("to"),
            },
            "last8": {
                "burned": w8.get("burn_sum_render"),
                "node_emissions": w8.get("node_operator_emit_sum_render"),
                "ratio": w8.get("burn_emit_ratio"),
                "label": w8.get("label"),
                "spike_note": "Near-balance driven by epoch 134 ~62k burn spike — recent epochs weaker.",
            },
            "cumulative_burned": burn.get("cumulative_burn_dash"),
            "node_operator_due_per_epoch": burn.get("latest_node_operator_due"),
            "availability_note": "Availability emissions (~2.9k/epoch) sit on top of node-operator — more inflationary if included.",
            "simple_english": (
                "Network work burns RENDER. The network also emits RENDER to reward operators. "
                "What matters to holders is burn versus new emissions."
            ),
            "source_urls": burn.get("source_urls") or [],
        },
        "supply": {
            "status": "PARTIAL",
            "solana_supply": supply_info.get("solanaSupply"),
            "solana_circulating": supply_info.get("solanaCirculatingSupply"),
            "ethereum_rndr": supply_info.get("ethereumSupply"),
            "foundation_circulating": supply_info.get("circulatingSupply"),
            "cg_circulating": supply_recon.get("cg_circ"),
            "max_supply": supply_info.get("maxSupply"),
            "display_rule": (
                "SOLANA SPL / LEGACY ETH RNDR / MARKET CIRCULATING ARE DIFFERENT "
                "ACCOUNTING VIEWS — DO NOT ADD THEM TOGETHER."
            ),
            "source_url": "https://infra.shikumi.cc/api/v1/supplyInfo",
        },
        "buyer_seller": {
            "classification": buyer.get("classification"),
            "seller_read": "MIXED / PARTIAL",
            "whales_read": "UNKNOWN / PARTIAL",
            "span_hours": buyer_win.get("observed_span_hours"),
            "swap_tx_count": buyer.get("swap_tx_count"),
            "unique_buyers": buyer_totals.get("unique_buyers"),
            "net_accumulators": buyer_totals.get("net_accumulator_count"),
            "unique_sellers": buyer_totals.get("unique_sellers"),
            "net_distributors": buyer_totals.get("net_distributor_count"),
            "gross_buy": buyer_totals.get("gross_buy_tokens"),
            "gross_sell": buyer_totals.get("gross_sell_tokens"),
            "top5_buy_share_pct": buyer_conc.get("top5_gross_buy_share_pct"),
            "top10_buy_share_pct": buyer_conc.get("top10_gross_buy_share_pct"),
            "top5_sell_share_pct": buyer_conc.get("top5_gross_sell_share_pct"),
            "repeat_buyers": buyer_totals.get("repeat_buyer_count"),
            "repeat_buyer_share_pct": buyer_totals.get("repeat_buyer_gross_buy_share_pct"),
            "limitations": buyer_win.get("limitations") or [],
            "gathered_at_utc": buyer.get("gathered_at_utc"),
            "source": "Helius SWAP sample · principal Raydium/Meteora/Orca pools",
            "source_url": "https://dexscreener.com/solana/rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof",
        },
        "wintermute": {
            "wallet": "MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa",
            "gross_buy": (wm or {}).get("gross_buy_tokens"),
            "gross_sell": (wm or {}).get("gross_sell_tokens"),
            "net": (wm or {}).get("net_tokens"),
            "balance": (wm or {}).get("current_balance_tokens"),
            "read": "MM INVENTORY / DEX CHURN",
            "warning": False,
            "discipline": [
                "MM INTERACTION ≠ PRICE SUPPRESSION",
                "OTC INTERACTION ≠ SALE",
            ],
            "epistemic_status": "KNOWN" if wm else "UNKNOWN",
        },
        "evidence_table": evidence_table,
        "nodes_frames_probe": nodes_frames,
    }
