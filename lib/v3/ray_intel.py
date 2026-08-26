"""RAY Current Stance + intel builder — Stage 1 pack → V3 asset JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.v3.asset_top import (
    LIGHT_GREEN,
    LIGHT_ORANGE,
    LIGHT_UNKNOWN,
    empty_asset_top,
    signal,
)
from lib.v3.current_stance import ray_current_stance

ROOT = Path(__file__).resolve().parents[2]
AS_OF = "2026-08-12"
CG = "https://www.coingecko.com/en/coins/raydium"
LLAMA = "https://defillama.com/protocol/raydium"
DOCS_BUYBACK = "https://docs.raydium.io/ray/ray-buybacks"
BINANCE = "https://www.binance.com/en/trade/RAY_USDT"
HOLDER = "https://solscan.io/account/DdHDoz94o2WJmD9myRobHCwtx1bESpHTd4SSPe6VEZaz"


def build_ray_asset_top() -> dict[str, Any]:
    top = empty_asset_top("RAY", "~$0.63")
    top["price_as_of"] = AS_OF
    stance = ray_current_stance()
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "explanation": stance["summary"],
        "directional_state": "WEAK",
        "confidence": stance["confidence"],
        "evidence_refs": [],
    }

    top["groups"] = {
        "market_structure": {
            "group_id": "market_structure",
            "title": "Price / Market Structure",
            "group_state": "WEAK · LAGGING SOL",
            "group_light": LIGHT_ORANGE,
            "signals": [
                signal(
                    signal_id="price_trend",
                    label="Price Trend",
                    state="WEAK",
                    display="~96% retraced from ATH",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "Price ~$0.63. CoinGecko ATH ~$16.83 (2021-09-12) · ~−96.3%. "
                        "7d ~+2.2% · 30d ~−4.9% · 90d ~−20.3% · 180d ~+1.7%. "
                        "365d high ~$4.12 · still ~−85% from that high."
                    ),
                    unknown="",
                    meaning="Own-price direction and retracement from cycle high — not a verdict by itself.",
                    source="CoinGecko + Binance daily",
                    source_url=CG,
                    as_of=AS_OF,
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="vs_btc",
                    label="vs BTC",
                    state="MIXED",
                    display="30d −7.3pp · 180d +9.6pp",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "RAY/BTC 7d ~+3.4pp · 30d ~−7.3pp · 90d ~+1.1pp · 180d ~+9.6pp. "
                        "Recent 30d soft does not erase longer positive relative history."
                    ),
                    unknown="",
                    meaning="Relative strength versus Bitcoin.",
                    source="Binance daily RAYUSDT + BTCUSDT",
                    source_url=BINANCE,
                    as_of=AS_OF,
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="vs_sol",
                    label="vs SOL (priority)",
                    state="LAGGING",
                    display="30d −6.7pp · 90d −4.0pp",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "RAY/SOL 7d ~−1.0pp · 30d ~−6.7pp · 90d ~−4.0pp · 180d ~+12.2pp. "
                        "Priority lens: recent underperformance vs Solana — not leading the chain. "
                        "Positive 180d history remains, but confirmation is weak now."
                    ),
                    unknown="",
                    meaning="Whether Raydium's token leads or follows Solana.",
                    source="Binance daily RAYUSDT + SOLUSDT",
                    source_url=BINANCE,
                    as_of=AS_OF,
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
            ],
        },
        "capital_flow": {
            "group_id": "capital_flow",
            "title": "Protocol Economics",
            "group_state": "REAL / ACTIVE",
            "group_light": LIGHT_GREEN,
            "signals": [
                signal(
                    signal_id="dex_volume",
                    label="DEX Volume",
                    state="ACTIVE",
                    display="~$106M 24h · ~$2.21B 30d",
                    light=LIGHT_GREEN,
                    evidence=(
                        "Raydium parent DEX volume ~$106.2M 24h / ~$630.5M 7d / ~$2.21B 30d. "
                        "Raydium AMM child alone ~$90.6M 24h. "
                        "Volume ≠ value captured by RAY holders."
                    ),
                    unknown="",
                    meaning="Gross trading activity on Raydium.",
                    source="DefiLlama",
                    source_url=LLAMA,
                    as_of=AS_OF,
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="tvl_fees",
                    label="TVL · Fees",
                    state="REAL",
                    display="TVL ~$846M · fees ~$5.1M 30d",
                    light=LIGHT_GREEN,
                    evidence=(
                        "Solana pool TVL ~$846M (+ staking ~$25.8M). "
                        "Fees ~$349k 24h / ~$5.12M 30d — mostly LP share, not token capture."
                    ),
                    unknown="",
                    meaning="Locked liquidity and gross fee generation.",
                    source="DefiLlama",
                    source_url=LLAMA,
                    as_of=AS_OF,
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="protocol_revenue",
                    label="Protocol / Token Capture",
                    state="MODEST",
                    display="Rev ~$53k 24h · ~$798k 30d",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "DefiLlama revenue (buyback + treasury alloc) ~$53.3k 24h / ~$798k 30d. "
                        "LaunchLab vol ~$0.53M 24h / ~$15.7M 30d — small vs core Raydium. "
                        "Do not confuse $100M+ volume with $100M of RAY-holder value."
                    ),
                    unknown="Exact LaunchLab→buyback share not independently quantified.",
                    meaning="Fee share reaching protocol/token routes.",
                    source="DefiLlama revenue + LaunchLab",
                    source_url=LLAMA,
                    as_of=AS_OF,
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
            ],
        },
        "project_supply": {
            "group_id": "project_supply",
            "title": "Token Value Capture / Supply",
            "group_state": "REAL BUT MODEST · PACE UNCLEAR",
            "group_light": LIGHT_ORANGE,
            "signals": [
                signal(
                    signal_id="buyback_mechanism",
                    label="Buyback Mechanism",
                    state="REAL",
                    display="12% fees → RAY buybacks",
                    light=LIGHT_GREEN,
                    evidence=(
                        "Documented: 12% of trading fees route to open-market RAY buybacks. "
                        "CLMM/CPMM 84/12/4 · AMM v4 88/12. "
                        "BUYBACK MECHANISM REAL · CURRENT ACCUMULATION PACE UNCLEAR."
                    ),
                    unknown="Aug consolidation into holder not seen in last-25 sig sample.",
                    meaning="Whether usage creates recurring RAY demand.",
                    source="Raydium docs",
                    source_url=DOCS_BUYBACK,
                    as_of=AS_OF,
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="KNOWN",
                ),
                signal(
                    signal_id="buyback_holder",
                    label="Buyback Holder",
                    state="PARTIAL",
                    display="~15.0M RAY held",
                    light=LIGHT_ORANGE,
                    evidence=(
                        "Holder DdHDoz…VEZaz balance ~14.996M RAY (~$9.5M at ~$0.63). "
                        "Last 25 signatures on holder: 2026-06-09 → 2026-06-25 only. "
                        "Buyback-held ≠ burned. No automatic burn in docs."
                    ),
                    unknown="Full collection→holder reconstruction for Aug.",
                    meaning="Auditable stock of bought-back RAY.",
                    source="Solana RPC + Raydium docs",
                    source_url=HOLDER,
                    as_of=AS_OF,
                    freshness="research_snapshot",
                    confidence="HIGH",
                    epistemic_status="PARTIAL",
                ),
                signal(
                    signal_id="supply_health",
                    label="Supply Health",
                    state="UNKNOWN",
                    display="Not proven deflationary",
                    light=LIGHT_UNKNOWN,
                    evidence=(
                        "Circ ~269.5M / max 555M (~48.6%). "
                        "Live emissions/unlocks UNKNOWN. "
                        "Supply not proven deflationary — held tokens are not burns."
                    ),
                    unknown="Unlock schedule · team/treasury RAY outside holder.",
                    meaning="Whether float is shrinking or expanding.",
                    source="CoinGecko + Raydium docs",
                    source_url=CG,
                    as_of=AS_OF,
                    freshness="research_snapshot",
                    confidence="MEDIUM",
                    epistemic_status="UNKNOWN",
                ),
            ],
        },
    }
    return top


def build_ray_v3() -> dict[str, Any]:
    stance = ray_current_stance()
    from lib.v3.ray_product import (
        build_ray_change_mind,
        build_ray_reality_check,
        build_ray_warning_stack,
    )

    return {
        "meta": {
            "schema": "ray-v3",
            "report_date": AS_OF,
            "gathered_at_utc": "2026-08-12T09:26:49Z",
            "research_pack_path": "reports/ray-forensics/stage1-evidence/RAY-STAGE1-FINDINGS.md",
            "overall_read": "PROTOCOL ACTIVE · VALUE CAPTURE MODEST · RS WEAK",
            "protocol_economics": "REAL / ACTIVE",
            "value_capture": "REAL BUT MODEST · PACE UNCLEAR",
            "trend_rs": "WEAK vs SOL (30d) · MIXED vs BTC",
        },
        "hero": {
            "asset": "RAY",
            "price_display": "~$0.63",
            "ath_display": "~$16.83",
            "drawdown_pct": 96.3,
            "v3_posture": stance["headline"],
            "v3_posture_note": stance["summary"],
        },
        "asset_top": build_ray_asset_top(),
        "warning_stack": build_ray_warning_stack(),
        "what_would_change_mind": build_ray_change_mind(),
        "reality_check": build_ray_reality_check(),
        "context": {
            "raydium_dex_24h_usd": 106155498,
            "raydium_dex_30d_usd": 2214653733,
            "raydium_tvl_usd": 845878298,
            "launchlab_24h_usd": 534369,
            "buyback_holder_ray": 14996187.044277,
            "wintermute_ray_balance": 82061.478449,
        },
        "research_evidence_table_path": "reports/ray-forensics/stage1-evidence/ray-evidence-table.json",
    }


def write_ray_v3(out_dir: Path | None = None) -> dict[str, Any]:
    doc = build_ray_v3()
    out_dir = out_dir or (ROOT / "reports" / "2026-08-12")
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "ray-v3.json").write_text(text, encoding="utf-8")
    (ROOT / "ray-v3.json").write_text(text, encoding="utf-8")
    return doc
