"""RAY V3 product layer — DEX economics + value capture (not generic alt Project Health)."""

from __future__ import annotations

from typing import Any

from lib.v3.ath_frame import meaning, rc_title
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
    ICON_RATIO,
    ICON_WARN,
    evidence_tip_html,
    mline_tip,
    reality_check_section,
    warning_stack_html,
)

AS_OF = "2026-08-12"
CG = "https://www.coingecko.com/en/coins/raydium"
LLAMA = "https://defillama.com/protocol/raydium"
DOCS = "https://docs.raydium.io/ray/ray-buybacks"
BINANCE = "https://www.binance.com/en/trade/RAY_USDT"
OKX = "https://www.okx.com/trade-swap/ray-usdt-swap"
HOLDER = "https://solscan.io/account/DdHDoz94o2WJmD9myRobHCwtx1bESpHTd4SSPe6VEZaz"
WM = "https://solscan.io/account/MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa"
GT_POOL = "https://www.geckoterminal.com/solana/pools/2AXXcN6oN9bBT5owwmTH53C7QHUXvhLeu718Kqt8rvY2"


def build_ray_warning_stack(_intel: dict[str, Any] | None = None) -> dict[str, Any]:
    cats = [
        technical_trend_category("ray"),
        category_state(
            "protocol_fees",
            "PROTOCOL FEES",
            "CLEAR",
            detail="DefiLlama fees ~$5.12M / 30d. Venue is alive.",
            summary="Fees ~$5.1M / 30d",
        ),
        category_state(
            "buyback_mechanism",
            "BUYBACK MECHANISM",
            "CLEAR",
            detail="12% of protocol fees → RAY buybacks. Holder inventory ~15.0M RAY. Real sink. Held ≠ burned.",
            summary="12% fees → RAY held ~15M",
        ),
        category_state(
            "buyback_pace",
            "BUYBACK PACE / FATE",
            "PARTIAL",
            detail=(
                "Mechanism documented, but holder last-25 sigs only span 2026-06-09→06-25. "
                "Aug on-chain accumulation not cleanly verified. Inventory can be sold. "
                "Team vest completed 21 Feb 2024. Residual emissions ~1.9M RAY/yr — not a sixth row."
            ),
            summary="Recent accumulation not clean · not burned",
        ),
        category_state(
            "organic_buyers",
            "ORGANIC BUYERS",
            "UNKNOWN",
            detail=(
                "Bounded DEX sample is MM-heavy (Wintermute both sides). "
                "Wintermute both sides ≠ dump. Bounded sample ≠ market-wide accumulation."
            ),
            summary="Sample MM-heavy · market-wide UNKNOWN",
        ),
    ]
    return pack_risk_confirmation(cats, "RAY Stage 1 evidence")


def build_ray_change_mind() -> dict[str, Any]:
    constructive = [
        condition(
            condition_id="buyback_tightens_float",
            title="Buybacks keep tightening float",
            summary="Auditable fee→RAY buybacks keep adding to the holder and stay there — capture shows up as a smaller tradeable float.",
            status="PARTIAL",
            interpretation="Mechanism is real (~15.0M held). Recent accumulation pace is not clean. Held ≠ burned.",
            evidence_rows=[
                ("Holder now", "~15.0M RAY"),
                ("Mechanism", "12% fees → buybacks"),
                ("Pace / fate", "Recent accumulation not clean · not burned"),
            ],
            source="Raydium docs + holder",
            source_url=DOCS,
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
        condition(
            condition_id="organic_spot_fees_hold",
            title="Organic spot with fees holding",
            summary="Non-MM spot accumulation appears across pools while protocol fees stay stable or rise.",
            status="WATCH",
            interpretation="Would mean fee capture is meeting genuine token demand, not just MM inventory churn.",
            evidence_rows=[
                ("Sample read", "PARTIAL · MM-HEAVY"),
                ("Fees 30d", "~$5.12M"),
                ("Rev 30d", "~$798k"),
            ],
            source="GeckoTerminal sample + DefiLlama",
            source_url=LLAMA,
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="up",
        ),
    ]
    defensive = [
        condition(
            condition_id="fees_and_buyback_fade",
            title="Fees fade and buybacks stall",
            summary="Protocol fees/revenue deteriorate and the buyback holder stops consolidating.",
            status="WATCH",
            interpretation="Would break the only measured RAY sink while the venue is still the thesis.",
            evidence_rows=[
                ("Rev vs ~180d-ago window", "Softer recent mean"),
                ("Holder", "~15.0M · fate unburned"),
            ],
            source="DefiLlama + holder",
            source_url=LLAMA,
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
        condition(
            condition_id="buyback_inventory_distributed",
            title="Buyback inventory hits the market",
            summary="The ~15M RAY holder distributes into liquid venues instead of remaining locked/held.",
            status="WATCH",
            interpretation="Held ≠ burned. Inventory sold would reverse the capture observation. TRANSFER ≠ SALE until sold.",
            evidence_rows=[
                ("Holder", "~15.0M RAY"),
                ("Burn", "None automatic"),
                ("Discipline", "TRANSFER ≠ SALE"),
            ],
            source="Solscan holder",
            source_url=HOLDER,
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
            icon="warn",
        ),
    ]
    return pack_change_mind(constructive, defensive, schema_version=1)


def build_ray_reality_check() -> dict[str, Any]:
    rc = empty_reality_check()
    rc["priority_headline"] = "HEALTHY DEX ≠ TOKEN LEADERSHIP"
    rc["known"] = [
        rc_item(
            item_id="drawdown",
            title=rc_title("ray", 96.3),
            summary="RAY ~$0.63 · ~−96% from 2021 ATH · ~−85% from 365d high.",
            evidence_rows=[("7d", "~+2.2%"), ("30d", "~−4.9%"), ("90d", "~−20.3%")],
            interpretation=meaning("ray", 96.3),
            priority="HIGH",
            source="CoinGecko + Binance",
            source_url=CG,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="protocol_active",
            title="Protocol still active",
            summary="Raydium parent DEX ~$100M+/day · TVL ~$0.85B.",
            evidence_rows=[("24h vol", "~$106M"), ("30d vol", "~$2.21B"), ("Fees 30d", "~$5.12M")],
            interpretation="Economic activity is real.",
            priority="HIGH",
            source="DefiLlama",
            source_url=LLAMA,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="buyback_route",
            title="Buyback route documented",
            summary="12% fee→RAY buybacks · holder ~15.0M RAY.",
            evidence_rows=[("Burn", "No automatic burn"), ("Held ≠ burned", "True")],
            interpretation="Mechanism real; scale modest vs volume.",
            priority="HIGH",
            source="Raydium docs + RPC",
            source_url=DOCS,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="revenue_printing",
            title="Protocol revenue still printing",
            summary="DefiLlama revenue ~$25–60k/day recent.",
            evidence_rows=[("24h", "~$53k"), ("30d", "~$798k")],
            interpretation="Capture exists but is small vs DEX volume.",
            priority="MEDIUM",
            source="DefiLlama",
            source_url=LLAMA,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="lag_sol",
            title="Lags SOL recently",
            summary="RAY/SOL soft over 30d/90d.",
            evidence_rows=[("30d", "~−6.7pp"), ("90d", "~−4.0pp"), ("180d", "~+12.2pp")],
            interpretation="Not leading the chain on the priority lens.",
            priority="HIGH",
            source="Binance daily",
            source_url=BINANCE,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="HIGH",
            epistemic_status="KNOWN",
        ),
        rc_item(
            item_id="mm_sample",
            title="Bounded sample MM-heavy",
            summary="Wintermute top actor both sides in bounded DEX sample.",
            evidence_rows=[("Top5 buy conc.", "~93.7%"), ("WM bal", "~82.1k RAY")],
            interpretation="MM two-way ≠ bearish · sample ≠ market-wide accumulation.",
            priority="MEDIUM",
            source="GeckoTerminal + MM registry",
            source_url=WM,
            as_of=AS_OF,
            freshness="research_snapshot",
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
    ]
    rc["suggests"] = [
        rc_item(
            item_id="relevant",
            title="Still economically relevant",
            summary="Protocol remains economically relevant on Solana.",
            interpretation="Product activity continues.",
            priority="HIGH",
            source="RAY Stage 1 synthesis",
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="modest_capture",
            title="Capture modest",
            summary="Value capture real but modest — not a dominant buy-pressure engine.",
            interpretation="Volume ≫ fees ≫ token capture.",
            priority="HIGH",
            source="RAY Stage 1 synthesis",
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="no_leadership",
            title="No clean leadership",
            summary="Market not confirming clean RAY leadership vs SOL.",
            interpretation="Healthy DEX ≠ token lead.",
            priority="HIGH",
            source="RAY Stage 1 synthesis",
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="mm_inventory",
            title="Buyer prints may be MM",
            summary="Observed buyer prints can be MM inventory, not organic demand.",
            interpretation="Identity quality unresolved.",
            priority="MEDIUM",
            source="RAY Stage 1 synthesis",
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
        rc_item(
            item_id="not_deflationary",
            title="Not proven deflationary",
            summary="Supply not proven deflationary without burns / unlock clarity.",
            interpretation="Held ≠ burned.",
            priority="MEDIUM",
            source="RAY Stage 1 synthesis",
            as_of=AS_OF,
            confidence="MEDIUM",
            epistemic_status="INFERENCE",
        ),
    ]
    rc["unknowns"] = [
        rc_item(
            item_id="buyback_usd_day",
            title="Current buyback USD/day",
            summary="On-chain reconstruction into holder for Aug not completed.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="unlocks",
            title="Live emissions / unlocks",
            summary="Schedule not fetched this pass.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="multi_pool_identity",
            title="Multi-pool buyer identity",
            summary="Beyond one GeckoTerminal page.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="volume_sector_mix",
            title="Volume sector mix",
            summary="Meme vs other share UNKNOWN.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="global_oi",
            title="Global perp OI",
            summary="Binance perp unavailable; OKX only partial.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
        rc_item(
            item_id="treasury_ray",
            title="Treasury / team RAY",
            summary="Outside buyback holder not mapped.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
    ]
    return rc


def ray_protocol_band(_intel: dict[str, Any] | None = None) -> str:
    lines = (
        mline_tip(
            ICON_GRID,
            "DEX volume",
            "Parent 24h / 30d",
            "~$106M / $2.2B",
            evidence_tip_html(
                name="DEX VOLUME",
                read="REAL / ACTIVE",
                rows=[("AMM child 24h", "~$90.6M"), ("LaunchLab 24h", "~$0.53M")],
                note="Volume ≠ RAY-holder value.",
                source="DefiLlama",
                source_url=LLAMA,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_BAG,
            "TVL",
            "Solana pools",
            "~$846M",
            evidence_tip_html(
                name="TVL",
                read="~$846M",
                rows=[("Staking TVL", "~$25.8M")],
                note="Locked liquidity — not a timing signal alone.",
                source="DefiLlama",
                source_url=LLAMA,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_BARS,
            "Fees",
            "Gross trading fees",
            "~$5.1M 30d",
            evidence_tip_html(
                name="FEES",
                read="~$349k 24h / ~$5.12M 30d",
                rows=[("LP share", "Most of fees"), ("Capture", "See revenue")],
                note="Distinguish fees from protocol/token capture.",
                source="DefiLlama",
                source_url=LLAMA,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-green",
        )
        + mline_tip(
            ICON_DROP,
            "Revenue",
            "Buyback + treasury alloc",
            "~$798k 30d",
            evidence_tip_html(
                name="PROTOCOL REVENUE",
                read="~$53k 24h / ~$798k 30d",
                rows=[("HoldersRevenue", "12% buybacks"), ("Treasury", "4% CLMM/CPMM")],
                note="Modest vs $100M+ daily volume.",
                source="DefiLlama",
                source_url=LLAMA,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-health">'
        "<h4>Protocol health</h4>"
        '<div class="band-status c-green">ACTIVE · ECONOMICALLY RELEVANT</div>'
        + lines
        + "</div>"
    )


def ray_token_band(_intel: dict[str, Any] | None = None) -> str:
    lines = (
        mline_tip(
            ICON_CIRCLES,
            "Buyback",
            "Documented route",
            "12% real",
            evidence_tip_html(
                name="BUYBACK MECHANISM",
                read="REAL · PACE UNCLEAR",
                rows=[("Holder", "~15.0M RAY"), ("Burn", "None automatic")],
                note="Buyback-held ≠ burned.",
                source="Raydium docs + RPC",
                source_url=DOCS,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_RATIO,
            "RAY / SOL",
            "Priority RS",
            "Lagging",
            evidence_tip_html(
                name="RAY/SOL",
                read="30d −6.7pp · 90d −4.0pp",
                rows=[("180d", "~+12.2pp"), ("Note", "Recent lag ≠ erase 180d")],
                note="Token confirmation weak vs chain.",
                source="Binance daily",
                source_url=BINANCE,
                as_of=AS_OF,
                confidence="HIGH",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_WARN,
            "Supply",
            "Health label",
            "Unclear",
            evidence_tip_html(
                name="SUPPLY",
                read="NOT PROVEN DEFLATIONARY",
                rows=[("Circ/max", "~48.6%"), ("Unlocks", "UNKNOWN")],
                note="Do not call deflationary from buybacks alone.",
                source="CoinGecko + docs",
                source_url=CG,
                as_of=AS_OF,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
        + mline_tip(
            ICON_LEVERAGE,
            "Capital flow",
            "Bounded sample",
            "MM-heavy",
            evidence_tip_html(
                name="WHO IS BUYING",
                read="PARTIAL · MM-HEAVY",
                rows=[
                    ("Sample", "~$10.4k buys / ~$4.3k sells"),
                    ("Top actor", "Wintermute both sides"),
                    ("WM net in-sample", "Net buy (tiny)"),
                ],
                note="MM two-way ≠ bearish · sample ≠ market-wide accumulation · TRANSFER ≠ SALE.",
                source="GeckoTerminal + registry",
                source_url=GT_POOL,
                as_of=AS_OF,
                confidence="MEDIUM",
            ),
            "c-orange",
        )
    )
    return (
        '<div class="band band-timing">'
        "<h4>Token confirmation</h4>"
        '<div class="band-status c-orange">BUYBACK REAL · RS WEAK · SUPPLY UNCLEAR</div>'
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
    as_of: str,
    note: str = "",
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
    tone_cls = {"green": "green", "orange": "orange", "muted": "", "grey": ""}.get(tone, "")
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


def render_ray_evidence_cards(intel: dict[str, Any]) -> str:
    ctx = intel.get("context") or {}
    cards = [
        _fx_card(
            title="Capital flow / who is buying",
            read="PARTIAL · MM-HEAVY",
            copy=(
                "Bounded GeckoTerminal sample on top RAY pool: high concentration; "
                "Wintermute top buyer and seller. MM two-way flow ≠ bearish. "
                "Bounded sample ≠ market-wide accumulation. Organic buyers UNKNOWN."
            ),
            tone="orange",
            kpis=[
                ("Sample buys", "~$10.4k"),
                ("Sample sells", "~$4.3k"),
                ("Top5 buy conc.", "~94%"),
            ],
            tip_rows=[
                ("Top actor", "Wintermute OTC MfDu…"),
                ("WM RAY bal", f"~{ctx.get('wintermute_ray_balance', 82061):,.0f}"),
                ("Discipline", "TRANSFER ≠ SALE · MM ≠ suppression"),
            ],
            source="GeckoTerminal + shared MM registry",
            source_url=GT_POOL,
            as_of=AS_OF,
            note="Do not promote Wintermute presence as a standalone warning.",
        ),
        _fx_card(
            title="Spot vs leverage",
            read="ON-CHAIN SPOT ACTIVE · GLOBAL LEVERAGE INCOMPLETE",
            copy=(
                "On-chain DEX spot is the large print. Binance CEX spot tiny; Binance perp unavailable. "
                "OKX OI/funding are partial context only. No fabricated fut/spot ratio."
            ),
            tone="grey",
            kpis=[
                ("Binance spot 24h", "~$0.21M"),
                ("Binance perp", "UNAVAILABLE"),
                ("OKX OI", "~$0.80M"),
            ],
            tip_rows=[
                ("OKX funding", "~+0.01%/period (context)"),
                ("Raydium DEX 24h", f"~${ctx.get('raydium_dex_24h_usd', 106155498)/1e6:.0f}M"),
                ("Global fut/spot", "UNKNOWN"),
            ],
            source="Binance + OKX + DefiLlama",
            source_url=OKX,
            as_of=AS_OF,
            note="OI/funding stay context unless more is proven.",
        ),
        _fx_card(
            title="Solana ecosystem position",
            read="RELEVANT · NOT DOMINANT",
            copy=(
                "Raydium still economically relevant, but not dominant in this 24h snapshot. "
                "PumpSwap/memecoin complex larger; Orca/Meteora same general scale. "
                "LaunchLab small vs core volume. Product works ≠ token leadership."
            ),
            tone="green",
            kpis=[
                ("Raydium AMM share", "~5% of Sol DEX 24h"),
                ("LaunchLab 24h", "~$0.53M"),
                ("TVL", "~$846M"),
            ],
            tip_rows=[
                ("Pump family 24h", "Much larger"),
                ("Orca / Meteora", "Same order as Raydium AMM"),
            ],
            source="DefiLlama Solana DEX overview",
            source_url="https://defillama.com/dexs/chains/solana",
            as_of=AS_OF,
            note="Supporting context only.",
        ),
    ]
    return (
        '<section class="sec fx-sec" aria-label="Wallet and transaction evidence">'
        '<h3 class="fx-title">Wallet &amp; transaction evidence</h3>'
        '<div class="fx-section-note">Compact conclusions first. DEX, buyback and flow detail stay in tips underneath.</div>'
        f'<div class="fx-mini-grid">{"".join(cards)}</div>'
        "</section>"
    )


def render_ray_product_html(intel: dict[str, Any]) -> str:
    from lib.v3.route_d_shell import change_mind_section

    split = (
        '<section class="sec"><div class="sec-head">'
        "<h3>The split that matters</h3>"
        '<p class="sec-sub">Raydium can be a healthy DEX while RAY still fails to lead.</p>'
        '</div><div class="split">'
        + ray_protocol_band(intel)
        + ray_token_band(intel)
        + "</div></section>"
    )
    warn = warning_stack_html(intel)
    wcm = change_mind_section(intel, slug="ray")
    rc = reality_check_section(intel)
    cards = render_ray_evidence_cards(intel)
    return split + warn + wcm + rc + cards
