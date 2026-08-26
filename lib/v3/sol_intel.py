"""SOL V3 intel — Stage 1 evidence → universal ALT asset_top.

Research-only wiring. No classifiers or thresholds.
UNKNOWN stays UNKNOWN.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.v3.ath_frame import meaning, retrace_label
from lib.paths import ROOT
from lib.v3.asset_top import (
    LIGHT_GREEN,
    LIGHT_ORANGE,
    LIGHT_UNKNOWN,
    empty_asset_top,
    enrich_tooltips,
    signal,
)

STAGE1_DIR = ROOT / "reports" / "sol-forensics" / "stage1-evidence"


def _load(name: str) -> dict[str, Any] | list[Any] | None:
    path = STAGE1_DIR / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_pp(v: Any) -> str:
    try:
        return f"{float(v):+.2f}pp"
    except (TypeError, ValueError):
        return "—"


def _fmt_usd(v: Any, *, compact: bool = False) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if compact and abs(n) >= 1e9:
        return f"${n/1e9:.2f}B"
    if compact and abs(n) >= 1e6:
        return f"${n/1e6:.1f}M"
    if abs(n) >= 1:
        return f"${n:,.2f}"
    return f"${n:.4f}"


def build_sol_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    """Map verified SOL Stage 1 evidence into ALT-top schema."""
    c = doc.get("stage1") or {}
    rs = c.get("reconciled_rs_vs_btc_pp") or {}
    price = c.get("price_structure") or {}
    funding = c.get("funding") or {}
    tok = c.get("staking_inflation_burn") or {}
    dex = c.get("dex") or {}
    activity = c.get("activity") or {}
    treasury = c.get("foundation_treasury") or {}
    hist = c.get("historical") or {}
    meta = c.get("meta") or {}
    as_of = meta.get("fetched_at_utc") or "2026-08-11"
    now_usd = price.get("now_usd") or (doc.get("hero") or {}).get("price_usd")
    price_disp = f"~${now_usd:,.2f}" if isinstance(now_usd, (int, float)) else (doc.get("hero") or {}).get("price_display")

    top = empty_asset_top("SOL", price_disp)
    top["price_as_of"] = as_of

    rs7, rs30, rs90 = rs.get("7"), rs.get("30"), rs.get("90")
    # Descriptive states only — no deploy/wait classifiers
    rs30_pos = isinstance(rs30, (int, float)) and rs30 > 0
    rs7_pos = isinstance(rs7, (int, float)) and rs7 > 0
    drawdown = (doc.get("hero") or {}).get("drawdown_pct")
    if drawdown is None and now_usd:
        drawdown = -74.14  # Stage1 verified vs ATH $293.31

    low = price.get("recent_local_low_365d") or {}
    bounce = price.get("bounce_from_low_pct")

    # --- Market structure ---
    # Price trend: deep ATH drawdown + only modest bounce → not "STRONG"
    trend_display = "WEAK / RECOVERING"
    trend_light = LIGHT_ORANGE
    if isinstance(drawdown, (int, float)) and abs(drawdown) >= 70 and not rs30_pos:
        trend_display = retrace_label(drawdown)
        trend_light = LIGHT_ORANGE

    vs_btc_display = "MIXED"
    vs_btc_light = LIGHT_ORANGE
    if rs30_pos and rs7_pos:
        vs_btc_display = "LEADING"
        vs_btc_light = LIGHT_GREEN
    elif rs30 is not None and float(rs30) < 0:
        vs_btc_display = "LAGGING 30d"
        vs_btc_light = LIGHT_ORANGE

    market_signals = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state=trend_display,
            display=trend_display,
            light=trend_light,
            meaning=meaning("sol", drawdown),
            evidence=(
                f"SOL {_fmt_usd(now_usd)} · drawdown from ATH ~{drawdown}% · "
                f"365d low {_fmt_usd(low.get('price_usd'))} on {low.get('date')} · "
                f"bounce +{bounce}% from that low."
            ),
            source="CoinGecko + Binance daily",
            source_url="https://www.coingecko.com/en/coins/solana",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="vs_btc",
            label="vs BTC",
            state=vs_btc_display,
            display=vs_btc_display,
            light=vs_btc_light,
            meaning="Relative strength vs Bitcoin (SOL return minus BTC return).",
            evidence=(
                f"SOL/BTC RS 7d {_fmt_pp(rs7)} · 30d {_fmt_pp(rs30)} · 90d {_fmt_pp(rs90)}. "
                f"Method: Binance daily closes."
            ),
            unknown="" if rs30 is not None else "RS series incomplete.",
            source="Binance SOLUSDT/BTCUSDT daily",
            source_url="https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1d",
            as_of="2026-08-11",
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="cycle_context",
            label="Cycle Context",
            state="POST-PEAK",
            display="POST-PEAK",
            light=LIGHT_ORANGE,
            meaning="Where current SOL sits vs prior peak fee/TVL/price regime.",
            evidence=(
                f"Fees now ~$600k/d vs ~$10.2M/d at Jan 2025 ATH window · "
                f"TVL ~$4.8B vs ~$11.3B at ATH · price ~70% retraced from Binance ATH-day close."
            ),
            source="DefiLlama + Binance (Stage1 historical)",
            source_url="https://defillama.com/fees/chain/Solana",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
    ]
    top["groups"]["market_structure"]["signals"] = market_signals
    top["groups"]["market_structure"]["group_state"] = "MIXED · NO 30d LEADERSHIP"
    top["groups"]["market_structure"]["group_light"] = LIGHT_ORANGE
    # Drop unused vs_sol slot — replaced by cycle_context above

    # --- Capital flow ---
    fut_spot = (doc.get("capital_flow") or {}).get("binance_fut_spot_ratio")
    latest_f = funding.get("latest_print_8h")
    mean7_f = funding.get("latest_7d_mean_8h")

    capital_signals = [
        signal(
            signal_id="spot_vs_leverage",
            label="Spot vs Leverage",
            state="LEVERAGE-HEAVY",
            display="LEVERAGE-HEAVY",
            light=LIGHT_ORANGE,
            meaning="Binance futures vs spot volume — exchange slice only. Funding ≠ leverage.",
            evidence=(
                f"Binance fut/spot 24h ~{fut_spot}× · "
                f"latest funding print {latest_f} · 7d mean {mean7_f} "
                f"(print ≠ multi-day mean)."
            ),
            unknown="Cross-exchange OI at prior highs UNKNOWN. ETF flows UNKNOWN.",
            source="Binance SOLUSDT",
            source_url="https://fapi.binance.com/fapi/v1/fundingRate?symbol=SOLUSDT&limit=1",
            as_of=funding.get("latest_print_time") or as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="who_is_buying",
            label="Who Is Buying?",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Identifiable demand — only with labelled proof.",
            evidence="No labelled buyer attribution in Stage1.",
            unknown="Whale / institutional / ETF buyer identity not verified.",
            source="SOL Stage-1 evidence",
            as_of=None,
            freshness="n/a",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="who_is_selling",
            label="Who Is Selling?",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Identifiable supply — transfer ≠ sale.",
            evidence="No labelled seller / distributor attribution in Stage1.",
            unknown="Foundation / treasury / CEX deposit direction not traced.",
            source="SOL Stage-1 evidence",
            as_of=None,
            freshness="n/a",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="whales_major_holders",
            label="Whales / Major Holders",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Large-holder accumulation or distribution.",
            evidence=(
                f"RPC non-circulating {treasury.get('non_circulating_sol_rpc')} SOL "
                f"across {treasury.get('non_circulating_accounts_n')} accounts — not directional."
            ),
            unknown="Directional whale flows require Arkham/Nansen-style labels.",
            source="Solana RPC getSupply",
            source_url="https://api.mainnet-beta.solana.com",
            as_of=as_of,
            freshness="same-day",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        signal(
            signal_id="team_dev_ceo",
            label="Foundation / Treasury Flows",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Foundation or labelled treasury wallet behaviour.",
            evidence="Bounded attempt counted non-circulating supply only.",
            unknown="No outbound labelled foundation flow series.",
            source="SOL Stage-1 evidence",
            freshness="n/a",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
    ]
    top["groups"]["capital_flow"]["signals"] = capital_signals
    top["groups"]["capital_flow"]["group_state"] = "LEVERAGE · IDENTITY UNRESOLVED"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_ORANGE

    # --- Project / supply / value capture ---
    stake_pct = round(float(tok.get("stake_ratio") or 0) * 100, 1)
    infl = round(float(tok.get("annual_inflation_rate_rpc") or 0) * 100, 2)
    issuance = tok.get("estimated_annual_issuance_sol")
    burn = tok.get("estimated_annual_burn_sol_at_current_price")
    net = tok.get("estimated_net_annual_supply_change_sol")
    tvl = (doc.get("network") or {}).get("tvl_usd")
    stables = (doc.get("network") or {}).get("stablecoins_usd")
    fees_30 = (doc.get("network") or {}).get("fees_30d_mean")

    project_signals = [
        signal(
            signal_id="project_health",
            label="Network Health",
            state="STRUCTURALLY ALIVE",
            display="STRUCTURALLY ALIVE",
            light=LIGHT_GREEN,
            meaning="Chain still processes activity; fee intensity far below peak.",
            evidence=(
                f"TVL {_fmt_usd(tvl, compact=True)} (#4) · fees 30d mean {_fmt_usd(fees_30, compact=True)}/d · "
                f"TPS snapshot ~{activity.get('tps_all_mean_20samples')} all / "
                f"~{activity.get('tps_non_vote_mean_20samples')} non-vote. "
                f"DAU series UNKNOWN."
            ),
            unknown="Daily active addresses / historical tx series UNKNOWN after bounded attempts.",
            source="DefiLlama + Solana RPC",
            source_url="https://defillama.com/chain/Solana",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="liquidity_absorption",
            label="TVL / Stables / DEX",
            state="SUBSTANTIAL",
            display="SUBSTANTIAL",
            light=LIGHT_GREEN,
            meaning="Ecosystem depth — not a price timing signal.",
            evidence=(
                f"Stablecoins ~{_fmt_usd(stables, compact=True)} USD-pegged · "
                f"DEX Sol/Eth L1 latest {dex.get('sol_share_latest')}× · "
                f"7d mean {dex.get('sol_share_7d_mean')}× "
                f"(Eth L2 DEX excluded)."
            ),
            source="DefiLlama",
            source_url="https://defillama.com/dexs/chains/solana",
            as_of=as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="KNOWN",
        ),
        signal(
            signal_id="supply_unlocks",
            label="Tokenomics / Value Capture",
            state="INFLATIONARY",
            display="INFLATIONARY",
            light=LIGHT_ORANGE,
            meaning="Issuance vs burn; staking ratio; non-staker dilution. Exact APY split UNKNOWN.",
            evidence=(
                f"Staked {stake_pct}% · inflation {infl}% · "
                f"est. issuance ~{issuance:,.0f} SOL/yr vs burn ~{burn:,.0f} SOL/yr · "
                f"net ~+{net:,.0f} SOL/yr. Liquid-staking APY sample 4.65–5.80% (headline only)."
            ),
            unknown="Exact inflation / fees / MEV yield composition not measured.",
            source="Solana RPC + DefiLlama burn",
            source_url="https://api.mainnet-beta.solana.com",
            as_of=as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
    ]
    top["groups"]["project_supply"]["title"] = "Network / Tokenomics"
    top["groups"]["project_supply"]["signals"] = project_signals
    top["groups"]["project_supply"]["group_state"] = "ALIVE · INFLATIONARY SUPPLY"
    top["groups"]["project_supply"]["group_light"] = LIGHT_ORANGE

    from lib.v3.current_stance import sol_current_stance

    stance = sol_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "explanation": stance["summary"],
        "directional_state": "MIXED_UNRESOLVED",
        "confidence": stance["confidence"],
        "evidence_refs": [
            "stage1.reconciled_rs_vs_btc_pp",
            "stage1.staking_inflation_burn",
            "stage1.dex",
            "stage1.funding",
        ],
    }
    return enrich_tooltips(top)


def build_sol_v3(sol_v4: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assemble SOL V3 intel document from Stage 1 pack + optional v4 price."""
    completion = _load("job-completion-pass.json") or {}
    evidence_table = _load("evidence-table.json") or []
    cg = _load("sol_coingecko_meta.json") or {}
    md = (cg.get("market_data") or {}) if isinstance(cg, dict) else {}

    price_usd = md.get("current_price", {}).get("usd")
    if price_usd is None and sol_v4:
        price_usd = sol_v4.get("price_usd")
    ath = md.get("ath", {}).get("usd") or 293.31
    drawdown = None
    if price_usd and ath:
        drawdown = round((float(price_usd) / float(ath) - 1) * 100, 2)

    # Pull network snapshot fields from completion + chains if present
    chains = _load("llama_chains.json") or []
    sol_chain = next((c for c in chains if isinstance(c, dict) and c.get("name") == "Solana"), {}) if isinstance(chains, list) else {}
    stables = _load("llama_stablecoin_chains.json") or []
    sol_stable = next((c for c in stables if isinstance(c, dict) and c.get("name") == "Solana"), {}) if isinstance(stables, list) else {}
    stable_usd = None
    if sol_stable:
        tcu = sol_stable.get("totalCirculatingUSD") or {}
        stable_usd = tcu.get("peggedUSD") if isinstance(tcu, dict) else tcu

    fees = _load("llama_sol_fees.json") or {}
    fee_chart = fees.get("totalDataChart") or []
    fees_30 = None
    if fee_chart:
        import statistics as stats

        fees_30 = stats.mean([v for _, v in fee_chart[-30:]])

    capital = {
        "binance_fut_spot_ratio": 11.87,  # Stage1 measured
    }
    # Prefer live tickers if present
    spot = _load("sol_spot_24h.json")
    fut = _load("sol_futures_24h.json")
    if isinstance(spot, dict) and isinstance(fut, dict):
        try:
            capital["binance_fut_spot_ratio"] = round(
                float(fut["quoteVolume"]) / float(spot["quoteVolume"]), 2
            )
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            pass

    doc: dict[str, Any] = {
        "asset": "SOL",
        "hero": {
            "asset": "SOL",
            "price_usd": price_usd,
            "price_display": f"~${price_usd:,.2f}" if price_usd else (sol_v4 or {}).get("price_display", "—"),
            "ath_display": f"${ath:,.2f}" if ath else None,
            "drawdown_pct": drawdown,
            "price_as_of": cg.get("last_updated") if isinstance(cg, dict) else None,
            "v3_posture": "",
            "v3_posture_note": "",
        },
        "triad": {
            "lifecycle": {"display": "Post-peak", "detail": meaning("sol", drawdown)},
            "project_health": {"display": "Structurally alive", "detail": "TVL, stables, DEX still substantial."},
            "market_timing": {"display": "Weak confirmation", "detail": "No 30d BTC leadership."},
        },
        "project_health": {"metrics": []},
        "market_timing": {"metrics": []},
        "relative_strength": {},
        "stage1": completion,
        "stage1_evidence_table": evidence_table,
        "network": {
            "tvl_usd": sol_chain.get("tvl"),
            "stablecoins_usd": stable_usd,
            "fees_30d_mean": fees_30,
        },
        "capital_flow": capital,
        "knowledge_census": {
            "known": [
                "Price, ATH drawdown, SOL/BTC RS windows (Binance).",
                "Stake ratio, inflation rate, issuance vs burn estimate.",
                "TVL, stablecoins, DEX vol vs Ethereum L1.",
                "Binance spot vs futures volume and funding prints.",
            ],
            "inferred": [
                "Non-stakers face net dilution at current burn/issuance.",
                "Ecosystem depth does not equal price confirmation.",
            ],
            "unknown": [
                "Who is buying / selling (labelled flows).",
                "Exact staking-yield split (inflation / fees / MEV).",
                "Daily active addresses / historical tx series.",
                "SOL ETF flows.",
                "Historical OI at prior highs.",
            ],
        },
    }
    doc["asset_top"] = build_sol_asset_top(doc)
    stance = doc["asset_top"]["current_stance"]
    doc["hero"]["v3_posture"] = stance["headline"]
    doc["hero"]["v3_posture_note"] = stance["summary"]
    doc["hero"]["v3_stance"] = stance["headline"]
    doc["hero"]["v3_stance_note"] = stance["summary"]

    from lib.v3.sol_product import (
        build_sol_change_mind,
        build_sol_reality_check,
        build_sol_warning_stack,
    )

    doc["warning_stack"] = build_sol_warning_stack(doc)
    doc["what_would_change_mind"] = build_sol_change_mind(doc)
    doc["reality_check"] = build_sol_reality_check(doc)
    return doc


def render_sol_census_html(intel: dict[str, Any]) -> str:
    """Deprecated — replaced by Reality Check in product layer."""
    from lib.v3.sol_product import render_sol_product_html

    return render_sol_product_html(intel)
