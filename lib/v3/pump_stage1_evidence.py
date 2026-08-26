"""Load verified Stage-1 PUMP evidence-gap artifacts — static JSON only, no API calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STAGE1_DIR = ROOT / "reports" / "pump-forensics" / "stage1-evidence-gaps"

REQUIRED_ARTIFACTS = (
    "job1-funding-window-analysis.json",
    "job4-mint-account.json",
    "job4-supply-model.json",
    "job3-launchpad-share-history-full.json",
    "job3-5-stress-and-fees-analysis.json",
)


def _load(name: str) -> dict[str, Any] | None:
    p = STAGE1_DIR / name
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def _pct(val: Any, ndigits: int = 1) -> str | None:
    if val is None:
        return None
    try:
        return f"{round(float(val), ndigits):.{ndigits}f}"
    except (TypeError, ValueError):
        return None


def _fmt_usd_compact(n: Any) -> str | None:
    if n is None:
        return None
    try:
        v = float(n)
    except (TypeError, ValueError):
        return None
    if abs(v) >= 1e6:
        return f"${v / 1e6:.1f}M/d"
    if abs(v) >= 1e3:
        return f"${v / 1e3:.0f}K/d"
    return f"${v:.0f}/d"


def load_stage1_evidence() -> dict[str, Any] | None:
    """Assemble Stage-1 block — fail closed unless all required artifacts load."""
    loaded: dict[str, dict[str, Any] | None] = {name: _load(name) for name in REQUIRED_ARTIFACTS}
    missing = [name for name, data in loaded.items() if data is None]
    if missing:
        return None

    funding = loaded["job1-funding-window-analysis.json"]
    mint = loaded["job4-mint-account.json"]
    supply = loaded["job4-supply-model.json"]
    platform_share = loaded["job3-launchpad-share-history-full.json"]
    stress = loaded["job3-5-stress-and-fees-analysis.json"]

    assert funding and mint and supply and platform_share and stress

    fn = funding.get("funding_now") or {}
    pct_rank = fn.get("percentile_vs_full_binance_history")
    history_n = fn.get("history_n")
    latest_rate = fn.get("latest_rate_8h")

    cg = supply.get("coingecko") or {}
    tok = supply.get("tokenomics_schedule") or {}
    aug = supply.get("august_discrepancy") or {}

    circ_pct = _pct(cg.get("circulating_pct_of_max"))
    sched_pct = _pct(tok.get("schedule_unlocked_pct_of_1T"))
    minted_pct = _pct(mint.get("pct_of_max_minted"))
    unminted_b = mint.get("unminted_below_max_ui")
    unminted_b_disp = f"{unminted_b / 1e9:.2f}B" if unminted_b is not None else None

    share_keys = platform_share.get("key_dates") or {}
    ath_share = share_keys.get("2025-09-14", {}).get("share_pct")
    jan_share = share_keys.get("2026-01-28", {}).get("share_pct")
    jun_share = share_keys.get("2026-06-25", {}).get("share_pct")
    aug10_share = share_keys.get("2026-08-10", {}).get("share_pct")

    fee_win = stress.get("platform_fee_windows") or {}
    fee_lines: list[str] = []
    for label, key in (
        ("ATH Sep", "ATH_sep14"),
        ("Jan high", "jan_hi"),
        ("June ATL", "atl_jun"),
        ("Now", "now"),
    ):
        w = fee_win.get(key) or {}
        fees = _fmt_usd_compact(w.get("fees_15d_mean_usd"))
        rev = _fmt_usd_compact(w.get("revenue_15d_mean_usd"))
        burn = _fmt_usd_compact(w.get("holders_revenue_15d_mean_usd"))
        if fees and rev and burn:
            fee_lines.append(f"{label}: fees {fees} · rev {rev} · buyback/burn {burn}")

    stress_sum = stress.get("summary") or {}
    n_win = stress_sum.get("n_windows")
    btc_rs_up = stress_sum.get("pump_btc_rs_positive_count")
    sol_rs_up = stress_sum.get("pump_sol_rs_positive_count")

    funding_display = None
    if pct_rank is not None and history_n is not None and latest_rate is not None:
        funding_display = (
            f"Binance funding ~{pct_rank}th percentile vs own history (n={history_n}) "
            f"· latest {latest_rate:.5f}/8h"
        )

    share_history_display = None
    if all(v is not None for v in (ath_share, jan_share, jun_share, aug10_share)):
        share_history_display = (
            f"Launchpad fee share: ATH Sep {ath_share:.2f}% · Jan high {jan_share:.2f}% · "
            f"June ATL {jun_share:.2f}% · Aug 10 {aug10_share:.2f}% · "
            f"live 24h share labelled separately in metrics above"
        )

    supply_display = None
    if circ_pct and sched_pct and minted_pct and unminted_b_disp is not None:
        supply_display = (
            f"Circulating {circ_pct}% (CoinGecko) · schedule-unlocked {sched_pct}% (Tokenomics) · "
            f"on-chain supply {minted_pct}% (Solana RPC) · mint authority null → no additional minting possible · "
            f"vesting/unlocks transfer already-minted allocation, not new minting · "
            f"nominal max minus current supply ≈{unminted_b_disp}, cannot now be minted · reconciliation UNKNOWN"
        )

    stress_wording = None
    if n_win is not None and btc_rs_up is not None and sol_rs_up is not None:
        stress_wording = (
            f"In {n_win} selected stress windows (research: 7d BTC or SOL ≤ −10%), "
            f"PUMP/BTC RS rose in {btc_rs_up}/{n_win}; PUMP/SOL RS rose in {sol_rs_up}/{n_win}. "
            f"Research methodology only — not a classifier threshold."
        )

    return {
        "source": "stage1-evidence-gaps",
        "verified": True,
        "artifacts_dir": str(STAGE1_DIR.relative_to(ROOT)),
        "required_artifacts": list(REQUIRED_ARTIFACTS),
        "funding": {
            "source": "binance PUMPUSDT",
            "coverage": "2025-07-10 → 2026-08-11",
            "latest_rate_8h": latest_rate,
            "latest_time": fn.get("latest_time"),
            "percentile_vs_binance_history": pct_rank,
            "history_n": history_n,
            "display": funding_display,
            "wording": (
                "Binance PUMP funding unusually low/negative vs its own Binance history — "
                "does not prove overall leverage is low."
            ),
            "oi_jan_sep": "UNKNOWN",
            "oi_note": (funding.get("oi_coverage") or {}).get("gap_note"),
        },
        "supply": {
            "circulating_pct": circ_pct,
            "schedule_unlocked_pct": sched_pct,
            "on_chain_minted_pct": minted_pct,
            "unminted_below_max_b": unminted_b_disp,
            "mint_authority": mint.get("mint_authority"),
            "freeze_authority": mint.get("freeze_authority"),
            "additional_minting_possible": mint.get("additional_minting_possible"),
            "reconciliation": "UNKNOWN",
            "reconciliation_note": (
                "Circulating (CG) · schedule-unlocked (Tokenomics) · on-chain minted (Solana RPC) "
                "are separate measures — gap not fully reconciled."
            ),
            "august_discrepancy": {
                "date": aug.get("date"),
                "tokenomics_b": round(aug["tokenomics_amount_tokens"] / 1e9, 2)
                if aug.get("tokenomics_amount_tokens") is not None
                else None,
                "defillama_b": round(aug["defillama_total_tokens"] / 1e9, 2)
                if aug.get("defillama_total_tokens") is not None
                else None,
                "note": aug.get("discrepancy_note"),
            },
            "display_full": supply_display,
            "display_compact": supply_display,
            "mint_explorer": mint.get("explorer"),
            "fetched_at": mint.get("fetched_at_utc"),
        },
        "platform": {
            "launchpad_fee_share_history": {
                "source": "defillama Launchpad category dailyFees",
                "source_url": "https://defillama.com/protocol/fees/pump.fun",
                "coverage": f"{platform_share.get('coverage_first')} → {platform_share.get('coverage_last')}",
                "as_of": platform_share.get("coverage_last"),
                "ath_sep_pct": ath_share,
                "jan_high_pct": jan_share,
                "june_atl_pct": jun_share,
                "aug_10_pct": aug10_share,
            },
            "fee_revenue_buyback_history": fee_lines,
            "display_share_history": share_history_display,
            "display_fee_context": " · ".join(fee_lines) if fee_lines else None,
            "interpretation": (
                "Recovered strongly after Jan low share, then lost share again. "
                "Fee share ≠ launches/users and does not prove price causation."
            ),
            "launches_per_day": "UNKNOWN",
            "graduations_per_day": "UNKNOWN",
            "active_users": "UNKNOWN",
            "unknown_blockers": (
                "pump.fun APIs blocked; Dune/Bitquery require keys — bounded attempt documented in Stage-1."
            ),
            "confidence": "MEDIUM",
        },
        "stress": {
            "method": stress.get("method"),
            "n_selected_windows": n_win,
            "pump_btc_rs_positive_count": btc_rs_up,
            "pump_sol_rs_positive_count": sol_rs_up,
            "wording": stress_wording,
            "inference": stress_sum.get("inference"),
            "coverage": stress.get("coverage"),
            "source": ((stress.get("coverage") or {}).get("source") or "CoinGecko daily"),
            "confidence": "MEDIUM",
        },
        "gaps_documented": [
            "Jan/Sep historical OI — UNKNOWN (Binance public hist ~30d only).",
            "Historical whale distribution at prior highs — UNKNOWN.",
            "Tokens launched/day, graduations, active users — UNKNOWN.",
        ],
    }
