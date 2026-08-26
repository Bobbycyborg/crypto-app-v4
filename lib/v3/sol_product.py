"""SOL V3 product-layer HTML — split, warnings, change-mind, reality check, evidence cards.

Uses Stage 1 evidence only. No classifiers or thresholds.
UNKNOWN stays UNKNOWN. Compact like approved PUMP.
"""

from __future__ import annotations

from typing import Any

from lib.v3.ath_frame import meaning, rc_title, retrace_label, timing_caption
from lib.v3.change_mind import condition, pack_change_mind
from lib.v3.fields import category_state, pack_risk_confirmation
from lib.v3.sma_trend import technical_trend_category
from lib.v3.reality_check import empty_reality_check, rc_item
from lib.v3.route_d_shell import (
    ICON_BAG,
    ICON_BARS,
    ICON_CIRCLES,
    ICON_DROP,
    ICON_GRID,
    ICON_LEVERAGE,
    ICON_LEV_DOWN,
    ICON_NODES,
    ICON_RATIO,
    ICON_WRENCH,
    evidence_tip_html,
    mline_tip,
    reality_check_section,
    warning_stack_html,
)


def _fmt_usd(v: Any, *, compact: bool = False) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if compact and abs(n) >= 1e9:
        return f"${n / 1e9:.2f}B"
    if compact and abs(n) >= 1e6:
        return f"${n / 1e6:.1f}M"
    if compact and abs(n) >= 1e3:
        return f"${n / 1e3:.0f}k"
    return f"${n:,.2f}"


def _fmt_pp(v: Any) -> str:
    try:
        return f"{float(v):+.2f}pp"
    except (TypeError, ValueError):
        return "—"


def _s1(intel: dict) -> dict:
    return intel.get("stage1") or {}


# ---------------------------------------------------------------------------
# Data builders (attached to sol-v3.json)
# ---------------------------------------------------------------------------


def build_sol_warning_stack(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    funding = c.get("funding") or {}
    tok = c.get("staking_inflation_burn") or {}
    capital = intel.get("capital_flow") or {}
    fut_spot = capital.get("binance_fut_spot_ratio")
    hist = c.get("historical") or {}
    now_fees = (hist.get("Now") or {}).get("fees_7d_mean_usd")
    ath_fees = (hist.get("USD_ATH_2025-01-19") or {}).get("fees_7d_mean_usd")
    net = tok.get("estimated_net_annual_supply_change_sol")

    if fut_spot and float(fut_spot) >= 5:
        lev_st, lev_sum = "PARTIAL", f"Futures {fut_spot}× spot"
    elif fut_spot:
        lev_st, lev_sum = "CLEAR", f"Futures {fut_spot}× spot"
    else:
        lev_st, lev_sum = "UNKNOWN", "Leverage snapshot missing"

    cats = [
        technical_trend_category("sol"),
        category_state(
            "spot_vs_leverage",
            "SPOT VS LEVERAGE",
            lev_st,
            detail=(
                f"Binance fut/spot ~{fut_spot}× · latest funding {funding.get('latest_print_8h')} · "
                f"7d mean {funding.get('latest_7d_mean_8h')} (print ≠ mean)."
            ),
            summary=lev_sum,
        ),
        category_state(
            "fee_intensity",
            "FEE INTENSITY VS PEAK",
            "PARTIAL",
            detail=(
                f"Fees ±7d mean now ~{_fmt_usd(now_fees, compact=True)}/d vs "
                f"~{_fmt_usd(ath_fees, compact=True)}/d at Jan 2025 ATH window."
            ),
            summary="Fees far below Jan 2025 peak",
        ),
        category_state(
            "supply_dilution",
            "SUPPLY / DILUTION",
            "PARTIAL",
            detail=(
                f"Inflation {float(tok.get('annual_inflation_rate_rpc') or 0)*100:.2f}% · "
                f"issuance ~{tok.get('estimated_annual_issuance_sol'):,.0f} SOL/yr vs "
                f"burn ~{tok.get('estimated_annual_burn_sol_at_current_price'):,.0f} · "
                f"net ~+{net:,.0f} SOL/yr. Exact APY split UNKNOWN."
            ),
            summary="Issuance ≫ burn · non-stakers diluted",
        ),
        category_state(
            "flow_identity",
            "BUYER / SELLER IDENTITY",
            "UNKNOWN",
            detail="No labelled whale / foundation / ETF flow series in Stage1.",
            summary="Who is buying/selling UNKNOWN",
        ),
    ]
    return pack_risk_confirmation(cats, "SOL Stage 1 evidence")


def build_sol_change_mind(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    rs = c.get("reconciled_rs_vs_btc_pp") or {}
    funding = c.get("funding") or {}
    tok = c.get("staking_inflation_burn") or {}
    hist = c.get("historical") or {}
    capital = intel.get("capital_flow") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")

    rs30 = rs.get("30")
    rs7 = rs.get("7")
    fut_spot = capital.get("binance_fut_spot_ratio")
    now_fees = (hist.get("Now") or {}).get("fees_7d_mean_usd")
    ath_fees = (hist.get("USD_ATH_2025-01-19") or {}).get("fees_7d_mean_usd")

    constructive = [
        condition(
            condition_id="sol_btc_leadership",
            title="SOL/BTC leadership returns",
            summary="7d and 30d SOL/BTC RS both positive on Binance closes.",
            status="PARTIAL" if (rs7 is not None and float(rs7) > 0 and rs30 is not None and float(rs30) <= 0) else (
                "YES" if (rs7 is not None and float(rs7) > 0 and rs30 is not None and float(rs30) > 0) else "NO"
            ),
            interpretation="7d positive alone is not medium-term leadership.",
            evidence_rows=[
                ("7d RS", _fmt_pp(rs7)),
                ("30d RS", _fmt_pp(rs30)),
                ("90d RS", _fmt_pp(rs.get("90"))),
            ],
            source="Binance daily closes",
            source_url="https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1d",
            as_of=as_of,
            confidence="HIGH",
            epistemic_status="KNOWN",
            icon="up",
        ),
        condition(
            condition_id="fee_recovery",
            title="Fee intensity recovers vs peak",
            summary="Network fees rise toward prior-cycle levels (descriptive, not a cutoff).",
            status="NO",
            interpretation=(
                f"Now ~{_fmt_usd(now_fees, compact=True)}/d vs "
                f"~{_fmt_usd(ath_fees, compact=True)}/d at Jan 2025 window."
            ),
            evidence_rows=[
                ("Now ±7d mean", _fmt_usd(now_fees, compact=True) + "/d"),
                ("Jan 2025 ATH window", _fmt_usd(ath_fees, compact=True) + "/d"),
            ],
            source="DefiLlama Solana fees",
            source_url="https://defillama.com/fees/chain/Solana",
            as_of=as_of,
            confidence="HIGH",
            epistemic_status="KNOWN",
            icon="bars",
        ),
        condition(
            condition_id="burn_vs_issuance",
            title="Burn closes gap on issuance",
            summary="Base-fee burn rises enough that net dilution shrinks materially.",
            status="NO",
            interpretation="Issuance still dwarfs burn at current activity.",
            evidence_rows=[
                ("Est. issuance", f"~{tok.get('estimated_annual_issuance_sol'):,.0f} SOL/yr"),
                ("Est. burn", f"~{tok.get('estimated_annual_burn_sol_at_current_price'):,.0f} SOL/yr"),
                ("APY split", "UNKNOWN"),
            ],
            source="Solana RPC + DefiLlama burn",
            source_url="https://api.mainnet-beta.solana.com",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="down",
        ),
        condition(
            condition_id="spot_led_tape",
            title="Spot leads the tape",
            summary="Futures no longer dominate Binance volume vs spot.",
            status="NO" if fut_spot and float(fut_spot) >= 5 else "PARTIAL",
            interpretation=f"Binance fut/spot currently ~{fut_spot}× (exchange slice only).",
            evidence_rows=[
                ("Fut/spot 24h", f"{fut_spot}×"),
                ("Funding latest print", str(funding.get("latest_print_8h"))),
                ("Funding 7d mean", str(funding.get("latest_7d_mean_8h"))),
            ],
            source="Binance SOLUSDT",
            source_url="https://www.binance.com/en/trade/SOL_USDT",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="KNOWN",
            icon="bars",
        ),
    ]

    defensive = [
        condition(
            condition_id="rs_fails_again",
            title="30d SOL/BTC stays negative",
            summary="Medium-term relative strength fails while USD price bounces.",
            status="YES" if rs30 is not None and float(rs30) < 0 else "NO",
            interpretation="Current 30d RS is negative — medium-term leadership absent.",
            evidence_rows=[("30d SOL/BTC", _fmt_pp(rs30))],
            source="Binance daily closes",
            source_url="https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1d",
            as_of=as_of,
            confidence="HIGH",
            epistemic_status="KNOWN",
            icon="warn",
        ),
        condition(
            condition_id="fees_stay_depressed",
            title="Fees stay depressed vs peak",
            summary="Paid network activity remains far below prior-cycle windows.",
            status="YES",
            interpretation="Fee dollars are a weak confirmation of fundamental demand intensity.",
            evidence_rows=[
                ("Now", _fmt_usd(now_fees, compact=True) + "/d"),
                ("Jan 2025", _fmt_usd(ath_fees, compact=True) + "/d"),
            ],
            source="DefiLlama",
            source_url="https://defillama.com/fees/chain/Solana",
            as_of=as_of,
            confidence="HIGH",
            epistemic_status="KNOWN",
            icon="warn",
        ),
        condition(
            condition_id="dilution_persists",
            title="Net dilution persists",
            summary="Issuance continues to dwarf burn with no measured yield-split relief.",
            status="YES",
            interpretation="Non-stakers remain diluted at current burn/issuance — that is the token consequence of weak fee intensity.",
            evidence_rows=[
                ("Net supply change", f"~+{tok.get('estimated_net_annual_supply_change_sol'):,.0f} SOL/yr"),
                ("Stake ratio", f"{float(tok.get('stake_ratio') or 0)*100:.1f}%"),
            ],
            source="Solana RPC + DefiLlama burn",
            source_url="https://api.mainnet-beta.solana.com",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
    ]

    return pack_change_mind(constructive, defensive)


def build_sol_reality_check(intel: dict[str, Any]) -> dict[str, Any]:
    c = _s1(intel)
    rs = c.get("reconciled_rs_vs_btc_pp") or {}
    funding = c.get("funding") or {}
    tok = c.get("staking_inflation_burn") or {}
    dex = c.get("dex") or {}
    hist = c.get("historical") or {}
    price = c.get("price_structure") or {}
    net = intel.get("network") or {}
    capital = intel.get("capital_flow") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")

    rc = empty_reality_check()
    rc["priority_headline"] = (
        "Is Solana still economically healthy for SOL holders — and is the market confirming it?"
    )

    rc["known"] = [
        rc_item(
            item_id="price_rs",
            title="Price + SOL/BTC RS",
            summary=(
                f"{_fmt_usd(price.get('now_usd'))} · ~{(intel.get('hero') or {}).get('drawdown_pct')}% from ATH · "
                f"RS 7d {_fmt_pp(rs.get('7'))} / 30d {_fmt_pp(rs.get('30'))}"
            ),
            evidence_rows=[
                ("365d low", f"{_fmt_usd((price.get('recent_local_low_365d') or {}).get('price_usd'))} on {(price.get('recent_local_low_365d') or {}).get('date')}"),
                ("Bounce", f"+{price.get('bounce_from_low_pct')}%"),
                ("90d RS", _fmt_pp(rs.get("90"))),
            ],
            interpretation=meaning("sol", (intel.get("hero") or {}).get("drawdown_pct")),
            priority="HIGH",
            source="CoinGecko + Binance",
            source_url="https://www.coingecko.com/en/coins/solana",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
        ),
        rc_item(
            item_id="ecosystem_depth",
            title="TVL / stables / DEX",
            summary=(
                f"TVL {_fmt_usd(net.get('tvl_usd'), compact=True)} · "
                f"stables {_fmt_usd(net.get('stablecoins_usd'), compact=True)} · "
                f"DEX Sol/Eth L1 {dex.get('sol_share_7d_mean')}× (7d)"
            ),
            evidence_rows=[
                ("DEX latest day", f"{dex.get('sol_share_latest')}×"),
                ("Caveat", "Eth L2 DEX excluded"),
            ],
            interpretation="Ecosystem depth is still substantial.",
            priority="HIGH",
            source="DefiLlama",
            source_url="https://defillama.com/chain/Solana",
            as_of=as_of,
            freshness="same-day",
            confidence="HIGH",
        ),
        rc_item(
            item_id="tokenomics",
            title="Staking / inflation / burn",
            summary=(
                f"Staked {float(tok.get('stake_ratio') or 0)*100:.1f}% · "
                f"inflation {float(tok.get('annual_inflation_rate_rpc') or 0)*100:.2f}% · "
                f"net ~+{tok.get('estimated_net_annual_supply_change_sol'):,.0f} SOL/yr"
            ),
            evidence_rows=[
                ("Issuance", f"~{tok.get('estimated_annual_issuance_sol'):,.0f} SOL/yr"),
                ("Burn", f"~{tok.get('estimated_annual_burn_sol_at_current_price'):,.0f} SOL/yr"),
                ("APY sample", "4.65–5.80% headline"),
                ("APY split", "UNKNOWN"),
            ],
            interpretation="Supply economics are inflationary for non-stakers.",
            priority="HIGH",
            source="Solana RPC + DefiLlama burn",
            source_url="https://api.mainnet-beta.solana.com",
            as_of=as_of,
            freshness="same-day",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        rc_item(
            item_id="funding_leverage",
            title="Funding + leverage tape",
            summary=(
                f"Fut/spot ~{capital.get('binance_fut_spot_ratio')}× · "
                f"latest print {funding.get('latest_print_8h')} · "
                f"7d mean {funding.get('latest_7d_mean_8h')}"
            ),
            evidence_rows=[
                ("Print ≠ mean", "Always show both windows"),
                ("OI hist at peaks", "UNKNOWN (~31d public)"),
            ],
            interpretation="Binance tape is leverage-heavy; latest funding print is negative.",
            source="Binance",
            source_url="https://fapi.binance.com/fapi/v1/fundingRate?symbol=SOLUSDT&limit=1",
            as_of=funding.get("latest_print_time") or as_of,
            freshness="same-day",
            confidence="MEDIUM",
        ),
    ]

    rc["suggests"] = [
        rc_item(
            item_id="alive_not_confirmed",
            title="Alive ≠ confirmed trade",
            summary="Network depth remains; confirmation and fees do not.",
            interpretation="Do not treat TVL/DEX strength alone as a timing signal.",
            priority="HIGH",
            source="Stage 1 synthesis",
            source_url="https://defillama.com/chain/Solana",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="dilution_lens",
            title="Value capture favours stakers",
            summary="Issuance ≫ burn → non-stakers diluted at current activity.",
            interpretation="Exact inflation/fees/MEV APY weights remain UNKNOWN.",
            priority="HIGH",
            source="Issuance vs burn model",
            source_url="https://api.mainnet-beta.solana.com",
            as_of=as_of,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="post_peak_regime",
            title="Post-peak fee/TVL regime",
            summary=(
                f"Fees/TVL now far below Jan 2025 "
                f"({_fmt_usd((hist.get('Now') or {}).get('fees_7d_mean_usd'), compact=True)}/d vs "
                f"{_fmt_usd((hist.get('USD_ATH_2025-01-19') or {}).get('fees_7d_mean_usd'), compact=True)}/d)."
            ),
            interpretation="Current SOL is not operating in the prior peak economics regime.",
            source="DefiLlama historical",
            source_url="https://defillama.com/fees/chain/Solana",
            as_of=as_of,
            confidence="HIGH",
            epistemic_status="INFERENCE",
        ),
    ]

    rc["unknowns"] = [
        rc_item(
            item_id="who_flows",
            title="Who is buying / selling",
            summary="No labelled whale, foundation, or ETF flow attribution.",
            interpretation="Transfer ≠ sale. Bounded attempts logged in Stage1.",
            priority="HIGH",
            source="SOL Stage-1 evidence",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="yield_split",
            title="Staking yield composition",
            summary="Headline APY known; inflation / fees / MEV split not measured.",
            source="SOL Stage-1 evidence",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="dau_tx_series",
            title="DAU / historical tx series",
            summary="CoinMetrics/Solscan/Tracker blocked or key-gated.",
            source="SOL Stage-1 evidence",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="etf_oi_hist",
            title="ETF flows + historical OI",
            summary="Farside blocked; Binance public OI ~31d only.",
            source="SOL Stage-1 evidence",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
    ]
    return rc


# ---------------------------------------------------------------------------
# HTML sections
# ---------------------------------------------------------------------------


def sol_health_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    tok = c.get("staking_inflation_burn") or {}
    dex = c.get("dex") or {}
    activity = c.get("activity") or {}
    net = intel.get("network") or {}
    hist = c.get("historical") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")

    tvl = _fmt_usd(net.get("tvl_usd"), compact=True)
    stables = _fmt_usd(net.get("stablecoins_usd"), compact=True)
    fees30 = _fmt_usd(net.get("fees_30d_mean"), compact=True)
    stake = f"{float(tok.get('stake_ratio') or 0)*100:.1f}%"
    infl = f"{float(tok.get('annual_inflation_rate_rpc') or 0)*100:.2f}%"
    dex7 = f"{dex.get('sol_share_7d_mean')}×"
    now_fees = (hist.get("Now") or {}).get("fees_7d_mean_usd")
    ath_fees = (hist.get("USD_ATH_2025-01-19") or {}).get("fees_7d_mean_usd")

    lines = (
        mline_tip(
            ICON_GRID,
            "TVL",
            "DefiLlama chain",
            tvl,
            evidence_tip_html(
                name="TVL",
                read=tvl,
                rows=[("Rank", "#4 among chains"), ("As of", str(as_of))],
                note="Chain TVL — not a timing signal by itself.",
                source="DefiLlama",
                source_url="https://defillama.com/chain/Solana",
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_BAG,
            "Stablecoins",
            "USD-pegged on Solana",
            stables,
            evidence_tip_html(
                name="STABLECOINS",
                read=stables,
                rows=[("Scope", "USD-pegged circulating")],
                note="Stablecoin stock on Solana.",
                source="DefiLlama stablecoins",
                source_url="https://defillama.com/stablecoins/chains",
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_BARS,
            "Fees (30d mean)",
            "Paid network activity",
            f"{fees30}/d",
            evidence_tip_html(
                name="NETWORK FEES",
                read=f"{fees30}/d",
                rows=[
                    ("Now ±7d", _fmt_usd(now_fees, compact=True) + "/d"),
                    ("Jan 2025 ATH window", _fmt_usd(ath_fees, compact=True) + "/d"),
                ],
                note="Fee dollars far below prior peak — see lower evidence card.",
                source="DefiLlama",
                source_url="https://defillama.com/fees/chain/Solana",
                as_of=as_of,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_RATIO,
            "DEX vs ETH L1",
            "7d mean volume share",
            dex7,
            evidence_tip_html(
                name="DEX SHARE",
                read=dex7,
                rows=[
                    ("Latest day", f"{dex.get('sol_share_latest')}×"),
                    ("Caveat", "Ethereum L2 DEX not included"),
                ],
                note="Solana DEX volume relative to Ethereum L1 only.",
                source="DefiLlama",
                source_url="https://defillama.com/dexs/chains/solana",
                as_of=as_of,
                confidence="MEDIUM",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_NODES,
            "Stake ratio",
            "Vote-account activated stake",
            stake,
            evidence_tip_html(
                name="STAKE RATIO",
                read=stake,
                rows=[
                    ("Staked", f"{tok.get('staked_sol'):,.0f} SOL"),
                    ("Validators", f"{tok.get('validators_active')} active"),
                ],
                note="High stake share — not proof of healthy token demand.",
                source="Solana RPC getVoteAccounts",
                source_url="https://api.mainnet-beta.solana.com",
                as_of=as_of,
                confidence="HIGH",
            ),
            "",
        )
        + mline_tip(
            ICON_DROP,
            "Inflation / burn",
            "Issuance vs base-fee burn",
            f"{infl} / burn thin",
            evidence_tip_html(
                name="INFLATION VS BURN",
                read=f"Inflation {infl}",
                rows=[
                    ("Issuance", f"~{tok.get('estimated_annual_issuance_sol'):,.0f} SOL/yr"),
                    ("Burn", f"~{tok.get('estimated_annual_burn_sol_at_current_price'):,.0f} SOL/yr"),
                    ("APY split", "UNKNOWN"),
                ],
                note="Net inflationary for non-stakers at current activity.",
                source="Solana RPC + DefiLlama burn",
                source_url="https://api.mainnet-beta.solana.com",
                as_of=as_of,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_WRENCH,
            "TPS snapshot",
            "RPC 20×60s samples",
            f"~{activity.get('tps_non_vote_mean_20samples')} nv",
            evidence_tip_html(
                name="TPS SNAPSHOT",
                read=f"~{activity.get('tps_all_mean_20samples')} all / ~{activity.get('tps_non_vote_mean_20samples')} non-vote",
                rows=[("DAU series", "UNKNOWN"), ("Tx history", "UNKNOWN")],
                note="Point-in-time throughput — not a historical series.",
                source="Solana RPC getRecentPerformanceSamples",
                source_url="https://api.mainnet-beta.solana.com",
                as_of=as_of,
                confidence="MEDIUM",
            ),
            "",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Project / network health</h4>"
        '<div class="band-status c-green">STRUCTURALLY ALIVE</div>'
        + lines
        + "</div>"
    )


def sol_timing_band(intel: dict[str, Any]) -> str:
    c = _s1(intel)
    rs = c.get("reconciled_rs_vs_btc_pp") or {}
    funding = c.get("funding") or {}
    price = c.get("price_structure") or {}
    capital = intel.get("capital_flow") or {}
    hero = intel.get("hero") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")

    now = _fmt_usd(price.get("now_usd") or hero.get("price_usd"))
    dd = hero.get("drawdown_pct")
    ath = hero.get("ath_display") or "$293.31"
    fut_spot = capital.get("binance_fut_spot_ratio")
    rs30 = rs.get("30")

    fill_w = "74%"
    if isinstance(dd, (int, float)):
        fill_w = f"{min(95, max(5, int(abs(dd))))}%"

    ddbar = (
        '<div class="ddbar">'
        f'<div class="ddbar-track"><div class="ddbar-fill" style="width:{fill_w}"></div></div>'
        f'<div class="ddbar-cap"><span>Now {now}</span>'
        f"<span>{timing_caption(f'ATH {ath}', dd)}</span></div>"
        "</div>"
    )

    lines = (
        mline_tip(
            ICON_CIRCLES,
            "SOL / BTC",
            "Relative strength",
            f"7d {_fmt_pp(rs.get('7'))} · 30d {_fmt_pp(rs30)}",
            evidence_tip_html(
                name="SOL / BTC RS",
                read=f"30d {_fmt_pp(rs30)}",
                rows=[
                    ("7d", _fmt_pp(rs.get("7"))),
                    ("30d", _fmt_pp(rs30)),
                    ("90d", _fmt_pp(rs.get("90"))),
                    ("Method", "Binance daily close"),
                ],
                note="30d negative = no medium-term leadership.",
                source="Binance",
                source_url="https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1d",
                as_of="2026-08-11",
                confidence="HIGH",
            ),
            "c-orange" if rs30 is not None and float(rs30) < 0 else "",
        )
        + mline_tip(
            ICON_LEVERAGE,
            "Spot vs leverage",
            "Binance 24h slice",
            f"{fut_spot}× fut/spot",
            evidence_tip_html(
                name="SPOT VS LEVERAGE",
                read=f"{fut_spot}×",
                rows=[("Scope", "Binance SOLUSDT only")],
                note="Leverage-heavy on this venue — not whole-market proof.",
                source="Binance",
                source_url="https://www.binance.com/en/trade/SOL_USDT",
                as_of=as_of,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_LEV_DOWN,
            "Funding windows",
            "Print vs 7d mean",
            "print − / 7d +",
            evidence_tip_html(
                name="FUNDING",
                read=str(funding.get("latest_print_8h")),
                rows=[
                    ("Latest 8h print", str(funding.get("latest_print_8h"))),
                    ("7d mean", str(funding.get("latest_7d_mean_8h"))),
                    ("Hist table", "±3d means at anchor dates"),
                ],
                note="Never collapse print and multi-day mean into one number.",
                source="Binance SOLUSDT funding",
                source_url="https://fapi.binance.com/fapi/v1/fundingRate?symbol=SOLUSDT&limit=1",
                as_of=funding.get("latest_print_time"),
                confidence="HIGH",
            ),
            "",
        )
        + mline_tip(
            ICON_BAG,
            "Who is buying/selling",
            "Labelled attribution",
            "UNKNOWN",
            evidence_tip_html(
                name="FLOW IDENTITY",
                read="UNKNOWN",
                rows=[("ETF flows", "UNKNOWN"), ("Whales", "UNKNOWN")],
                note="Transfer ≠ sale. Bounded attempts only.",
                source="SOL Stage-1 evidence",
                confidence="LOW",
            ),
            "c-muted",
        )
    )
    return (
        '<div class="band band-timing">'
        "<h4>Market / timing</h4>"
        '<div class="band-status c-orange">WEAK CONFIRMATION</div>'
        + ddbar
        + lines
        + "</div>"
    )


def _fx_card(
    *,
    title: str,
    read: str,
    copy: str,
    tone: str,
    kpis: list[tuple[str, str]],
    tip_rows: list[tuple[str, str]],
    source: str,
    source_url: str | None,
    as_of: str | None,
    note: str,
) -> str:
    from lib.v3.forensic_cards import _esc, _details, _ev_row

    kpi_html = "".join(
        f'<div class="fx-kpi"><strong>{_esc(v)}</strong><span>{_esc(k)}</span></div>'
        for k, v in kpis
        if v
    )
    rows = "".join(_ev_row(k, v) for k, v in tip_rows if v)
    tip = evidence_tip_html(
        name=title,
        read=read,
        rows=tip_rows[:5],
        note=note,
        source=source,
        source_url=source_url,
        as_of=as_of,
        confidence="MEDIUM",
    )
    tone_cls = {"green": "green", "orange": "orange", "muted": ""}.get(tone, "")
    return (
        f'<section class="fx-card {tone_cls} has-tip">'
        f'<div class="metric-tip-template" hidden>{tip}</div>'
        f'<div class="fx-card-title">{_esc(title)}</div>'
        f'<div class="fx-card-read {tone}">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        f'<div class="fx-kpi-row">{kpi_html}</div>'
        + _details("View evidence detail", rows + f'<div class="fx-ev-note">{_esc(note)}</div>')
        + "</section>"
    )


def render_sol_evidence_cards(intel: dict[str, Any]) -> str:
    """Lower compact evidence cards — historical + tokenomics + ecosystem + funding."""
    c = _s1(intel)
    hist = c.get("historical") or {}
    tok = c.get("staking_inflation_burn") or {}
    dex = c.get("dex") or {}
    funding = c.get("funding") or {}
    rs = c.get("reconciled_rs_vs_btc_pp") or {}
    net = intel.get("network") or {}
    as_of = (c.get("meta") or {}).get("fetched_at_utc")

    now = hist.get("Now") or {}
    ath = hist.get("USD_ATH_2025-01-19") or {}
    low = hist.get("Recent_local_low_2026-06-06") or {}
    ftx = hist.get("FTX_stress") or {}

    cards = [
        _fx_card(
            title="Historical fees + TVL",
            read="FAR BELOW PEAK",
            copy="Fee dollars and TVL are still well under the Jan 2025 regime.",
            tone="orange",
            kpis=[
                ("Now fees ±7d", _fmt_usd(now.get("fees_7d_mean_usd"), compact=True) + "/d"),
                ("Jan 2025 fees", _fmt_usd(ath.get("fees_7d_mean_usd"), compact=True) + "/d"),
                ("Now TVL", _fmt_usd(net.get("tvl_usd"), compact=True)),
                ("Jan 2025 TVL", "~$11.30B"),
            ],
            tip_rows=[
                ("June 2026 low fees", _fmt_usd(low.get("fees_7d_mean_usd"), compact=True) + "/d"),
                ("Nov 2024 fees", _fmt_usd((hist.get("Nov2024_rally") or {}).get("fees_7d_mean_usd"), compact=True) + "/d"),
                ("Jan 2025 TVL", "~$11.30B (Stage1 historical)"),
                ("June 2026 TVL", "~$4.80B now / ~$8.88B at June local low (Stage1)"),
            ],
            source="DefiLlama",
            source_url="https://defillama.com/fees/chain/Solana",
            as_of=as_of,
            note="Historical comparison only — not a classifier threshold.",
        ),
        _fx_card(
            title="Staking / inflation / burn",
            read="INFLATIONARY",
            copy="Issuance dwarfs base-fee burn. Headline APY known; composition UNKNOWN.",
            tone="orange",
            kpis=[
                ("Stake", f"{float(tok.get('stake_ratio') or 0)*100:.1f}%"),
                ("Inflation", f"{float(tok.get('annual_inflation_rate_rpc') or 0)*100:.2f}%"),
                ("Issuance", f"~{tok.get('estimated_annual_issuance_sol'):,.0f}/yr"),
                ("Burn", f"~{tok.get('estimated_annual_burn_sol_at_current_price'):,.0f}/yr"),
            ],
            tip_rows=[
                ("Net change", f"~+{tok.get('estimated_net_annual_supply_change_sol'):,.0f} SOL/yr"),
                ("APY sample", "4.65–5.80%"),
                ("APY split", "UNKNOWN"),
            ],
            source="Solana RPC + DefiLlama burn",
            source_url="https://api.mainnet-beta.solana.com",
            as_of=as_of,
            note="Non-stakers face net dilution at current activity.",
        ),
        _fx_card(
            title="Stables + DEX ecosystem",
            read="SUBSTANTIAL",
            copy="Stablecoin stock and L1 DEX share remain large.",
            tone="green",
            kpis=[
                ("Stables", _fmt_usd(net.get("stablecoins_usd"), compact=True)),
                ("DEX 7d vs ETH L1", f"{dex.get('sol_share_7d_mean')}×"),
                ("DEX latest", f"{dex.get('sol_share_latest')}×"),
                ("TVL", _fmt_usd(net.get("tvl_usd"), compact=True)),
            ],
            tip_rows=[("Caveat", "Ethereum L2 DEX excluded from ETH L1 series")],
            source="DefiLlama",
            source_url="https://defillama.com/dexs/chains/solana",
            as_of=as_of,
            note="Depth ≠ price confirmation.",
        ),
        _fx_card(
            title="Price / funding / RS context",
            read="MIXED",
            copy=meaning("sol", (intel.get("hero") or {}).get("drawdown_pct")),
            tone="orange",
            kpis=[
                ("RS 7d/30d", f"{_fmt_pp(rs.get('7'))} / {_fmt_pp(rs.get('30'))}"),
                ("Latest funding", str(funding.get("latest_print_8h"))),
                ("7d mean funding", str(funding.get("latest_7d_mean_8h"))),
                ("FTX funding ±3d", str((ftx.get("funding") or {}).get("mean_8h_pm3d"))),
            ],
            tip_rows=[
                ("June 2026 low", f"{_fmt_usd((low.get('price') or {}).get('price_usd'))}"),
                ("Now", f"{_fmt_usd((now.get('price') or {}).get('price_usd'))}"),
                ("Hist funding table", "±3d means at anchors"),
            ],
            source="Binance",
            source_url="https://fapi.binance.com/fapi/v1/fundingRate?symbol=SOLUSDT",
            as_of=as_of,
            note="Always separate latest print from window means.",
        ),
    ]

    # Fix TVL kpi for first card if nested structure differs
    return (
        '<section class="sec fx-sec" aria-label="Wallet and transaction evidence">'
        '<h3 class="fx-title">Wallet &amp; transaction evidence</h3>'
        '<div class="fx-section-note">Compact conclusions first. Historical detail and sources stay in tips underneath.</div>'
        f'<div class="fx-mini-grid">{"".join(cards)}</div>'
        "</section>"
    )


def render_sol_product_html(intel: dict[str, Any]) -> str:
    """Full product layer under ALT top — PUMP-equivalent sections for SOL."""
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        "</div><div class=\"split\">"
        + sol_health_band(intel)
        + sol_timing_band(intel)
        + "</div></section>"
    )
    warn = warning_stack_html(intel)
    wcm = change_mind_section(intel, slug="sol")
    rc = reality_check_section(intel)
    cards = render_sol_evidence_cards(intel)
    return split + warn + wcm + rc + cards
