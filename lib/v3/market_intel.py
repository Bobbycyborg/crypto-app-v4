"""Build shared market intelligence JSON for V3."""

from __future__ import annotations

from typing import Any

from lib.v3.fields import category_state, family_block, field, missing_field, now_iso
from lib.v3.breadth_universe import cg_market_as_of, btc_30d_pct_coingecko

_BTC_CHART_URL = "https://www.blockchain.com/charts/market-price"
_COINGECKO_API = "https://www.coingecko.com/en/api"
_BINANCE_FUNDING_DOCS = "https://binance-docs.github.io/apidocs/futures/en/#index-price-and-mark-price"


def _daily_as_of(daily: dict[str, float] | None) -> str | None:
    if not daily:
        return None
    return max(daily)


def _btc_meta_as_of(ev: dict[str, Any]) -> str | None:
    return (ev.get("btc_meta") or {}).get("to")


def _btc_regime_family(ev: dict[str, Any], fetched_at: str) -> dict:
    analysis = ev.get("btc_analysis")
    btc_meta = ev.get("btc_meta") or {}
    if not analysis:
        return family_block(
            "btc_regime",
            "BTC market regime",
            "Is BTC providing a healthy foundation for crypto/alt risk?",
            "UNKNOWN",
            [missing_field("btc_analysis", "BTC cycle analysis", note="BTC daily history unavailable.")],
            impl_status="NEEDS_ENGINEERING",
        )
    m = analysis["market"]
    leg = analysis["current_leg"]
    cache_note = None
    if btc_meta.get("to"):
        cache_note = f"Daily series through {btc_meta['to']}"
        if btc_meta.get("fetched"):
            cache_note += f" · cache {btc_meta['fetched']}"
    fields = [
        field(
            "btc_price_usd",
            "BTC price (USD)",
            m["btc_price_usd"],
            unit="USD",
            as_of=m["btc_date"],
            source="blockchain.info",
            source_url=_BTC_CHART_URL,
            fetched_at=btc_meta.get("fetched") or fetched_at,
            data_status="LIVE",
            confidence="HIGH",
            note=cache_note,
        ),
        field(
            "btc_return_30d_pct",
            "BTC 30d return",
            m["return_30d_pct"],
            unit="%",
            as_of=m["btc_date"],
            source="blockchain.info",
            source_url=_BTC_CHART_URL,
            fetched_at=btc_meta.get("fetched") or fetched_at,
        ),
        field(
            "btc_return_90d_pct",
            "BTC 90d return",
            m["return_90d_pct"],
            unit="%",
            as_of=m["btc_date"],
            source="blockchain.info",
            source_url=_BTC_CHART_URL,
            fetched_at=btc_meta.get("fetched") or fetched_at,
        ),
        field(
            "btc_from_high_365d_pct",
            "From 365d high",
            m["from_high_365d_pct"],
            unit="%",
            as_of=m["btc_date"],
            source="blockchain.info",
            source_url=_BTC_CHART_URL,
            fetched_at=btc_meta.get("fetched") or fetched_at,
        ),
        field(
            "btc_current_leg",
            "Current swing leg",
            f"{leg['dir']} · {leg['days']}d · {leg['move']:+.1f}%",
            as_of=leg["end"],
            source="local_cycle_math",
            source_url=_BTC_CHART_URL,
            fetched_at=fetched_at,
            epistemic="INFERRED",
            impl_status="NEEDS_BACKTESTING",
            note="Descriptive leg detection — not a production trigger.",
        ),
    ]
    return family_block(
        "btc_regime",
        "BTC market regime",
        "Is BTC providing a healthy foundation for crypto/alt risk?",
        "UNKNOWN",
        fields,
        note="Raw regime metrics live · classifier NEEDS_BACKTESTING (no invented thresholds).",
        impl_status="NEEDS_BACKTESTING",
    )


def _macro_family(ev: dict[str, Any], fetched_at: str) -> dict:
    sc = ev.get("stablecoin_supply") or {}
    gl = ev.get("global_liquidity") or {}
    fields: list[dict] = []

    if gl.get("partial_ok") or gl.get("ok"):
        gl_fetched = gl.get("fetched_at") or fetched_at
        gl_url = gl.get("source_url") or "https://fred.stlouisfed.org/"
        if gl.get("global_pulse_yoy") is not None:
            fields.append(
                field(
                    "global_liquidity_pulse",
                    "Global liquidity pulse (US+EU+JP)",
                    gl["global_pulse_yoy"],
                    unit="% YoY",
                    as_of=gl.get("as_of"),
                    source="fred",
                    source_url=gl_url,
                    fetched_at=gl_fetched,
                    data_status="LIVE",
                    note=gl.get("global_pulse_note") or "Equal-weight regional YoY mean.",
                )
            )
        net_b = gl.get("net_liquidity_usd_b")
        if net_b is not None:
            fields.append(
                field(
                    "us_net_liquidity",
                    "US net liquidity (Fed−TGA−RRP)",
                    net_b,
                    unit="USD B",
                    as_of=gl.get("net_liquidity_as_of"),
                    source="fred",
                    source_url=gl.get("series_urls", {}).get("walcl") or gl_url,
                    fetched_at=gl_fetched,
                    data_status="LIVE",
                    note=f"90d {gl.get('net_liquidity_90d_pct'):+.1f}%"
                    if gl.get("net_liquidity_90d_pct") is not None
                    else "Fed balance sheet minus TGA and reverse repo.",
                )
            )
        if gl.get("ecb_assets_yoy_pct") is not None:
            fields.append(
                field(
                    "ecb_assets_yoy_pct",
                    "ECB total assets YoY",
                    gl["ecb_assets_yoy_pct"],
                    unit="%",
                    as_of=gl.get("ecb_assets_as_of"),
                    source="fred",
                    source_url=gl.get("series_urls", {}).get("ecb") or gl_url,
                    fetched_at=gl_fetched,
                    data_status="LIVE",
                )
            )
        if gl.get("boj_assets_yoy_pct") is not None:
            fields.append(
                field(
                    "boj_assets_yoy_pct",
                    "BoJ total assets YoY",
                    gl["boj_assets_yoy_pct"],
                    unit="%",
                    as_of=gl.get("boj_assets_as_of"),
                    source="fred",
                    source_url=gl.get("series_urls", {}).get("boj") or gl_url,
                    fetched_at=gl_fetched,
                    data_status="LIVE",
                )
            )
        if gl.get("m2_usd_b") is not None:
            fields.append(
                field(
                    "m2_money_stock",
                    "US M2 money stock",
                    gl["m2_usd_b"],
                    unit="USD B",
                    as_of=gl.get("m2_as_of"),
                    source="fred",
                    source_url=gl.get("series_urls", {}).get("m2sl") or gl_url,
                    fetched_at=gl_fetched,
                    data_status="LIVE",
                    note=f"YoY {gl.get('m2_yoy_pct'):+.1f}%"
                    if gl.get("m2_yoy_pct") is not None
                    else None,
                )
            )
        if gl.get("nfci_latest") is not None:
            fields.append(
                field(
                    "financial_conditions_nfci",
                    "US financial conditions (NFCI)",
                    gl["nfci_latest"],
                    unit="index",
                    as_of=gl.get("nfci_as_of"),
                    source="fred",
                    source_url=gl.get("series_urls", {}).get("nfci") or gl_url,
                    fetched_at=gl_fetched,
                    data_status="LIVE",
                    note="Negative = easier conditions · positive = tighter.",
                )
            )
    else:
        fields.append(
            missing_field(
                "global_liquidity",
                "Global liquidity / financial conditions",
                data_status="MISSING",
                note=gl.get("error") or "FRED macro liquidity fetch failed.",
                source_url="https://fred.stlouisfed.org/",
            )
        )

    if sc.get("ok") and sc.get("total_usd_b") is not None:
        src_url = sc.get("source_url") or "https://defillama.com/stablecoins"
        as_of = sc.get("as_of")
        sc_fetched = sc.get("fetched_at") or fetched_at
        fields.extend(
            [
                field(
                    "stablecoin_supply_total",
                    "Total stablecoin supply",
                    sc["total_usd_b"],
                    unit="USD B",
                    as_of=as_of,
                    source="defillama",
                    source_url=src_url,
                    fetched_at=sc_fetched,
                    note=f"Data as of {as_of} · freshness {sc.get('freshness', 'MISSING')}",
                ),
                field(
                    "stablecoin_supply_30d_pct",
                    "Stablecoin supply · 30d change",
                    sc.get("change_30d_pct"),
                    unit="%",
                    as_of=as_of,
                    source="defillama",
                    source_url=src_url,
                    fetched_at=sc_fetched,
                    note="Momentum only — not proof of alt buying.",
                ),
                field(
                    "stablecoin_supply_90d_pct",
                    "Stablecoin supply · 90d change",
                    sc.get("change_90d_pct"),
                    unit="%",
                    as_of=as_of,
                    source="defillama",
                    source_url=src_url,
                    fetched_at=sc_fetched,
                ),
            ]
        )
    else:
        fields.append(
            missing_field(
                "stablecoin_supply_total",
                "Total stablecoin supply",
                data_status="MISSING",
                source_url="https://defillama.com/stablecoins",
                note=sc.get("error") or "DefiLlama fetch failed.",
            )
        )
        fields.extend(
            [
                missing_field(
                    "stablecoin_supply_30d_pct",
                    "Stablecoin supply · 30d change",
                    data_status="MISSING",
                    source_url="https://defillama.com/stablecoins",
                ),
                missing_field(
                    "stablecoin_supply_90d_pct",
                    "Stablecoin supply · 90d change",
                    data_status="MISSING",
                    source_url="https://defillama.com/stablecoins",
                ),
            ]
        )

    gl_ok = gl.get("ok") or gl.get("partial_ok")
    return family_block(
        "macro_liquidity",
        "Macro / liquidity capacity",
        "Can the environment support sustained speculative risk?",
        "UNKNOWN",
        fields,
        note="Regime filter · global pulse (US+EU+JP) + NFCI + stablecoins via FRED/DefiLlama.",
        impl_status="PRODUCTION_READY" if gl_ok else "NEEDS_ENGINEERING",
    )


def _rotation_family(ev: dict[str, Any], fetched_at: str) -> dict:
    mp = ev.get("market_prices") or {}

    btc_30 = btc_30d_pct_coingecko(ev)
    eth_30 = mp.get("ethereum", {}).get("usd_30d_change")
    sol_30 = mp.get("solana", {}).get("usd_30d_change")
    eth_btc = (eth_30 - btc_30) if eth_30 is not None and btc_30 is not None else None
    sol_btc = (sol_30 - btc_30) if sol_30 is not None and btc_30 is not None else None

    as_of = cg_market_as_of(ev)

    alts = ev.get("alt_snapshots") or []
    beating_30d = sum(
        1
        for a in alts
        if a.get("change_30d_pct") is not None and btc_30 is not None and a["change_30d_pct"] > btc_30
    )
    tracked = sum(1 for a in alts if a.get("change_30d_pct") is not None)

    fields: list[dict] = [
        missing_field(
            "broad_ex_btc_rs",
            "Broad ex-BTC / BTC relative strength",
            data_status="UNAVAILABLE",
            source_url=_COINGECKO_API,
            note="TOTAL2ES/TOTAL3ES panel not wired — NEEDS_ENGINEERING.",
        ),
        field(
            "eth_btc_30d_pp",
            "ETH vs BTC (30d)",
            eth_btc,
            unit="pp",
            as_of=as_of,
            source="coingecko_markets",
            source_url=_COINGECKO_API,
            fetched_at=fetched_at,
            data_status="LIVE" if eth_btc is not None else "MISSING",
            note="USD return spread · BTC/ETH/SOL 30d from same CoinGecko markets batch.",
        ),
        field(
            "sol_btc_30d_pp",
            "SOL vs BTC (30d)",
            sol_btc,
            unit="pp",
            as_of=as_of,
            source="coingecko_markets",
            source_url=_COINGECKO_API,
            fetched_at=fetched_at,
            data_status="LIVE" if sol_btc is not None else "MISSING",
            note="USD return spread · BTC/ETH/SOL 30d from same CoinGecko markets batch.",
        ),
        field(
            "alts_beating_btc_30d",
            "Tracked alts beating BTC (30d)",
            beating_30d,
            unit=f"of {tracked}",
            as_of=as_of,
            source="coingecko_markets",
            source_url=_COINGECKO_API,
            fetched_at=fetched_at,
            data_status="LIVE" if tracked else "MISSING",
            note="Fixed tracked universe — not hindsight-selected majors.",
        ),
        missing_field(
            "btc_dominance",
            "BTC dominance trend",
            data_status="UNAVAILABLE",
            note="Descriptive context only — not an independent vote.",
        ),
    ]

    has_rs = eth_btc is not None or sol_btc is not None or tracked > 0
    display = "UNCLASSIFIED" if has_rs else "UNKNOWN"

    return family_block(
        "outward_rotation",
        "Outward capital rotation",
        "Are non-BTC assets actually outperforming BTC?",
        display,
        fields,
        note="Raw relative strength visible · classifier NEEDS_BACKTESTING.",
        impl_status="NEEDS_BACKTESTING",
    )


def _breadth_family(ev: dict[str, Any], fetched_at: str) -> dict:
    market = ev.get("market_breadth") or {}
    portfolio = ev.get("portfolio_breadth") or {}
    as_of = cg_market_as_of(ev) or _btc_meta_as_of(ev)

    rs_n = market.get("outperforming_sample_n") or 0
    sma_n = market.get("above_50dma_sample_n") or 0
    universe_size = market.get("universe_size") or 0
    daily_cov = market.get("daily_available_coverage") or f"{market.get('daily_available_n', 0)}/{universe_size}"
    sma_cov = market.get("above_50dma_coverage") or f"{market.get('above_50dma_n', 0)}/{sma_n}"
    prov = market.get("daily_series_provenance") or ""
    prov_bit = f" · {prov}" if prov else ""
    market_note = (
        f"Fixed universe · {rs_n}/{universe_size} with 30d RS · "
        f"{sma_cov} above 50DMA · {daily_cov} available{prov_bit}"
    )

    port_beat = portfolio.get("beating_btc_30d")
    port_tracked = portfolio.get("tracked_with_30d") or 0

    fields = [
        field(
            "market_pct_outperforming_btc_30d",
            "Market · % outperforming BTC (30d)",
            market.get("pct_outperforming_btc_30d"),
            unit="%",
            as_of=as_of,
            source="coingecko_markets + participation universe",
            source_url=_COINGECKO_API,
            fetched_at=fetched_at,
            data_status="LIVE" if rs_n else "MISSING",
            impl_status="NEEDS_BACKTESTING",
            note=market_note,
        ),
        field(
            "market_median_alt_btc_30d_pp",
            "Market · median alt/BTC (30d)",
            market.get("median_alt_btc_30d_pp"),
            unit="pp",
            as_of=as_of,
            source="coingecko_markets + participation universe",
            source_url=_COINGECKO_API,
            fetched_at=fetched_at,
            data_status="LIVE" if market.get("median_alt_btc_30d_pp") is not None else "MISSING",
            impl_status="NEEDS_BACKTESTING",
            note=market_note,
        ),
        field(
            "market_pct_above_50dma",
            "Market · % above 50DMA",
            market.get("pct_above_50dma"),
            unit="%",
            as_of=as_of,
            source="coingecko_market_chart",
            source_url=_COINGECKO_API,
            fetched_at=fetched_at,
            data_status="LIVE" if sma_n else "MISSING",
            impl_status="PRODUCTION_READY",
            note=f"Descriptive only · {sma_cov} above 50DMA · {daily_cov} available{prov_bit}.",
        ),
        field(
            "portfolio_beating_btc_30d",
            "Portfolio · alts beating BTC (30d)",
            port_beat,
            unit=f"of {port_tracked}",
            as_of=as_of,
            source="coingecko_markets",
            source_url=_COINGECKO_API,
            fetched_at=fetched_at,
            data_status="LIVE" if port_tracked else "MISSING",
            impl_status="PRODUCTION_READY",
            note="Holdings only — not market participation.",
            epistemic="KNOWN",
        ),
    ]

    has_market = rs_n > 0 or sma_n > 0
    display = "UNCLASSIFIED" if has_market else "UNKNOWN"

    return family_block(
        "breadth",
        "Market participation",
        "Is participation broadening or narrowing?",
        display,
        fields,
        note="Market = fixed liquidity-qualified universe · Portfolio line is secondary.",
        impl_status="NEEDS_BACKTESTING",
    )


def _sector_family(ev: dict[str, Any], fetched_at: str) -> dict:
    sd = ev.get("sector_destination") or {}
    sectors = sd.get("sectors") or []
    ranked = sd.get("ranked_by_vs_btc") or []
    leader = sd.get("leader_display") or "NO RANK DATA"
    leader_subline = sd.get("leader_subline") or ""
    rank2_subline = sd.get("rank2_subline") or ""
    as_of = cg_market_as_of(ev) or _btc_meta_as_of(ev)

    fields: list[dict] = [
        field(
            "sector_leader",
            "Strongest sector (30d rank)",
            leader,
            as_of=as_of,
            source="coingecko_markets",
            source_url=_COINGECKO_API,
            fetched_at=fetched_at,
            data_status="LIVE" if ranked else "MISSING",
            impl_status="NEEDS_BACKTESTING",
            note=leader_subline or "Descriptive rank only — strongest alt sector, not necessarily beating BTC.",
        ),
    ]
    if rank2_subline:
        fields.append(
            field(
                "sector_rank2",
                "Second-ranked sector (30d)",
                sd.get("rank2_display"),
                as_of=as_of,
                source="coingecko_markets",
                source_url=_COINGECKO_API,
                fetched_at=fetched_at,
                data_status="LIVE",
                impl_status="NEEDS_BACKTESTING",
                note=rank2_subline,
            )
        )

    for s in sectors:
        sid = s["sector_id"]
        n = s.get("constituents_with_30d") or 0
        total = s.get("constituent_count") or 0
        fields.append(
            field(
                f"sector_{sid}_vs_btc_30d_pp",
                f"{s['label']} basket vs BTC (30d)",
                s.get("vs_btc_30d_pp"),
                unit="pp",
                as_of=as_of,
                source="coingecko_markets",
                source_url=_COINGECKO_API,
                fetched_at=fetched_at,
                data_status="LIVE" if s.get("vs_btc_30d_pp") is not None else "MISSING",
                impl_status="NEEDS_BACKTESTING",
                note=f"Equal-weight basket · coverage {n}/{total} constituents with 30d data.",
            )
        )
        fields.append(
            field(
                f"sector_{sid}_vs_broad_30d_pp",
                f"{s['label']} basket vs broad alts (30d)",
                s.get("vs_broad_alt_30d_pp"),
                unit="pp",
                as_of=as_of,
                source="coingecko_markets",
                source_url=_COINGECKO_API,
                fetched_at=fetched_at,
                data_status="LIVE" if s.get("vs_broad_alt_30d_pp") is not None else "MISSING",
                impl_status="NEEDS_BACKTESTING",
                note="Broad-alt benchmark = equal-weight mean of fixed participation universe.",
            )
        )

    has_data = bool(ranked)
    display = "UNCLASSIFIED" if has_data else "UNKNOWN"

    return family_block(
        "sector_destination",
        "Sector / ecosystem destination",
        "Where is marginal crypto risk capital actually going?",
        display,
        fields,
        note="Fixed sector baskets · where money is going, not participation.",
        impl_status="NEEDS_BACKTESTING",
    )


def _fragility_family(ev: dict[str, Any], fetched_at: str) -> dict:
    sf = ev.get("supporting_feeds") or {}
    frag = sf.get("btc_fragility") or {}
    funding = sf.get("btc_funding") or {}
    oi = frag.get("oi") or {}
    vol = frag.get("volume") or {}
    frag_fetched = frag.get("fetched_at") or fetched_at
    fund_fetched = funding.get("fetched_at") or frag_fetched
    fields: list[dict] = []

    if frag.get("ok") and oi.get("oi_mcap_ratio") is not None:
        fields.append(
            field(
                "oi_mcap",
                "BTC OI notional / market cap",
                oi.get("oi_mcap_ratio"),
                unit="ratio",
                as_of=frag_fetched,
                source="binance_futures + coingecko_markets",
                source_url=oi.get("source_url"),
                fetched_at=frag_fetched,
                data_status="LIVE",
                impl_status="PRODUCTION_READY",
                note=(
                    f"OI ${oi.get('oi_notional_usd_b')}B / mcap ${oi.get('btc_market_cap_usd_b')}B "
                    f"· Binance BTCUSDT · descriptive only."
                ),
            )
        )
    elif frag.get("ok") and oi.get("oi_notional_usd_b") is not None:
        fields.append(
            field(
                "oi_mcap",
                "BTC OI notional / market cap",
                None,
                as_of=frag_fetched,
                source="binance_futures",
                source_url=oi.get("source_url"),
                fetched_at=frag_fetched,
                data_status="PARTIAL",
                note=f"OI notional ${oi.get('oi_notional_usd_b')}B · BTC market cap missing from CoinGecko batch.",
            )
        )
    else:
        fields.append(
            missing_field(
                "oi_mcap",
                "BTC OI notional / market cap",
                data_status="MISSING",
                source_url=oi.get("source_url") or _BINANCE_OI_DOCS,
                note=frag.get("error") or "Binance OI or enrichment failed.",
            )
        )

    if frag.get("ok") and vol.get("perp_spot_ratio") is not None:
        fields.append(
            field(
                "perp_spot_volume",
                "BTC perp / spot volume (24h)",
                vol.get("perp_spot_ratio"),
                unit="ratio",
                as_of=frag_fetched,
                source="binance_futures + binance_spot",
                source_url=vol.get("perp_source_url"),
                fetched_at=frag_fetched,
                data_status="LIVE",
                impl_status="PRODUCTION_READY",
                note=(
                    f"Perp ${vol.get('perp_quote_volume_24h_usd_b')}B / "
                    f"spot ${vol.get('spot_quote_volume_24h_usd_b')}B quote vol · descriptive only."
                ),
            )
        )
    else:
        fields.append(
            missing_field(
                "perp_spot_volume",
                "BTC perp / spot volume (24h)",
                data_status="MISSING",
                note=frag.get("error") or "Binance 24h volume fetch failed.",
            )
        )

    if funding.get("ok") and funding.get("last_funding_rate_pct") is not None:
        pct_rank = funding.get("percentile_rank")
        range_min = funding.get("range_min_pct")
        range_max = funding.get("range_max_pct")
        fund_note = f"Current {funding['last_funding_rate_pct']:+.4f}% (8h)"
        if range_min is not None and range_max is not None:
            hist_n = funding.get("history_n")
            fund_note += (
                f" · last {hist_n} funding prints range "
                f"{range_min:+.4f}% to {range_max:+.4f}%"
            )
        if pct_rank is not None:
            fund_note += f" · {_ordinal_percentile(pct_rank)} percentile · no bearish cutoff"
        fields.append(
            field(
                "btc_funding_context",
                "BTC funding context",
                funding.get("last_funding_rate_pct"),
                unit="%",
                as_of=fund_fetched,
                source="binance_futures",
                source_url=funding.get("history_source_url") or funding.get("source_url"),
                fetched_at=fund_fetched,
                data_status="LIVE",
                impl_status="PRODUCTION_READY",
                note=fund_note,
            )
        )
    else:
        fields.append(
            missing_field(
                "btc_funding_context",
                "BTC funding context",
                data_status="MISSING",
                source_url=funding.get("source_url") or _BINANCE_FUNDING_DOCS,
                note=funding.get("error") or frag.get("error") or "Binance funding feed failed.",
            )
        )

    still_missing = frag.get("still_missing") or []
    if still_missing:
        fields.append(
            missing_field(
                "breadth_concentration_divergence",
                "Participation / concentration divergence",
                data_status="UNAVAILABLE",
                note=" · ".join(still_missing) + " — NEEDS_ENGINEERING.",
            )
        )

    has_live = (
        (frag.get("ok") and (
            oi.get("oi_mcap_ratio") is not None
            or vol.get("perp_spot_ratio") is not None
        ))
        or (funding.get("ok") and funding.get("last_funding_rate_pct") is not None)
    )
    display = "UNCLASSIFIED" if has_live else "UNKNOWN"

    return family_block(
        "market_fragility",
        "Market fragility / speculative structure",
        "Is strength increasingly leverage-dependent or concentrated?",
        display,
        fields,
        note="Raw leverage evidence · no HIGH/LOW classifier · participation/concentration divergence still missing.",
        impl_status="NEEDS_BACKTESTING",
    )


_BINANCE_OI_DOCS = "https://binance-docs.github.io/apidocs/futures/en/#open-interest"


def _ordinal_percentile(rank: float) -> str:
    n = int(round(rank))
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _market_stacks(families: list[dict]) -> dict:
    def fam_state(fid: str) -> str:
        for f in families:
            if f["family_id"] == fid:
                return f["display_state"]
        return "UNKNOWN"

    early_ids = [
        ("btc_foundation", "BTC foundation healthy", "btc_regime"),
        ("outward_rs", "Genuine outward non-BTC RS", "outward_rotation"),
        ("breadth_expanding", "Participation expanding", "breadth"),
        ("sector_leadership", "Sector leadership developing", "sector_destination"),
    ]
    late_ids = [
        ("btc_deteriorates", "BTC foundation deteriorates", "btc_regime"),
        ("outward_fails", "Outward RS fails", "outward_rotation"),
        ("breadth_narrows", "Participation narrows", "breadth"),
        ("fragility", "Market structure fragile", "market_fragility"),
    ]

    def stack_categories(items: list[tuple[str, str, str]]) -> list[dict]:
        out = []
        for cid, label, fid in items:
            st = fam_state(fid)
            if st in ("UNKNOWN", "UNCLASSIFIED"):
                cat = "UNKNOWN"
            else:
                cat = "UNKNOWN"
            out.append(
                category_state(
                    cid,
                    label,
                    cat,
                    detail=f"Family state: {st}. No category classifier wired.",
                    impl_status="NEEDS_BACKTESTING",
                )
            )
        return out

    early = stack_categories(early_ids)
    late = stack_categories(late_ids)
    early_confirmed = sum(1 for c in early if c["state"] == "CONFIRMED")
    late_active = sum(1 for c in late if c["state"] == "ACTIVE")
    return {
        "early_alt_risk_on": {
            "categories": early,
            "summary": f"{early_confirmed} of {len(early)} independent categories confirmed",
            "note": "Supportive macro/liquidity context not counted as additional votes.",
        },
        "late_fragility": {
            "categories": late,
            "summary": f"{late_active} of {len(late)} deterioration categories active",
            "note": "Meme/high-beta speculation is context, not a fifth vote.",
        },
    }


def build_market_v3(evidence: dict[str, Any], report_date: str) -> dict[str, Any]:
    from lib.v3.market_family_states import apply_family_states, build_market_summary

    fetched_at = evidence.get("fetched_at") or now_iso()
    families = [
        _macro_family(evidence, fetched_at),
        _btc_regime_family(evidence, fetched_at),
        _rotation_family(evidence, fetched_at),
        _breadth_family(evidence, fetched_at),
        _sector_family(evidence, fetched_at),
        _fragility_family(evidence, fetched_at),
    ]
    market = {
        "meta": {
            "schema": "market-v3",
            "report_date": report_date,
            "generated_at": fetched_at,
            "version": "phase1-v1",
        },
        "families": families,
        "stacks": _market_stacks(families),
    }
    apply_family_states(market, evidence)
    market["summary"] = build_market_summary(market, evidence)
    return market
