"""Universal ALT asset-top schema — Option 3 v5 hero + signal grid.

Same framework for every ALT; each asset maps its own evidence into these signals.
Never invent certainty. UNKNOWN is first-class. Not an investment action.
"""

from __future__ import annotations

from typing import Any


LIGHT_GREEN = "green"
LIGHT_ORANGE = "orange"
LIGHT_RED = "red"
LIGHT_UNKNOWN = "unknown"

# Public source pages already used elsewhere in PUMP product (do not invent).
BINANCE_PUMP_DAILY = "https://api.binance.com/api/v3/klines?symbol=PUMPUSDT&interval=1d"
BINANCE_PUMP_FUT = "https://www.binance.com/en/futures/PUMPUSDT"
DEFILLAMA_PUMP_FEES = "https://defillama.com/protocol/fees/pump.fun"
DEXSCREENER_PUMP_FALLBACK = (
    "https://dexscreener.com/solana/2uf4xh61rdwxng9woyxsvqp7zua6klfpb3nvnrqeoisd"
)


def signal(
    *,
    signal_id: str,
    label: str,
    state: str,
    display: str,
    light: str,
    evidence: str = "",
    unknown: str = "",
    meaning: str = "",
    source: str | None = None,
    source_url: str | None = None,
    as_of: str | None = None,
    freshness: str | None = None,
    confidence: str | None = None,
    epistemic_status: str = "UNKNOWN",
) -> dict[str, Any]:
    return {
        "signal_id": signal_id,
        "label": label,
        "state": state,
        "display": display,
        "light": light,
        "evidence": evidence,
        "unknown": unknown,
        "meaning": meaning,
        "source": source,
        "source_url": source_url,
        "as_of": as_of,
        "freshness": freshness,
        "confidence": confidence,
        "epistemic_status": epistemic_status,
    }


def empty_signal(signal_id: str, label: str, meaning: str = "") -> dict[str, Any]:
    return signal(
        signal_id=signal_id,
        label=label,
        state="UNKNOWN",
        display="UNKNOWN",
        light=LIGHT_UNKNOWN,
        meaning=meaning,
        evidence="No verified evidence wired for this signal yet.",
        unknown="Insufficient evidence.",
        epistemic_status="UNKNOWN",
    )


def empty_asset_top(asset: str, price: str | None = None) -> dict[str, Any]:
    """Reusable scaffold — every ALT fills the same slots from its own evidence."""
    return {
        "asset": asset,
        "price": price,
        "price_as_of": None,
        "current_stance": {
            "headline": "EVIDENCE INCOMPLETE",
            "summary": "Not enough verified evidence to describe the asset picture yet.",
            "confidence": "LOW",
            "why": "Evidence is incomplete, so no stance is locked yet.",
            "supports": [],
            "holds_back": ["Insufficient verified evidence"],
            "stronger_if": ["Core market and capital-flow evidence becomes available"],
            "weaker_if": ["Key evidence remains missing or contradictory"],
            "explanation": "Not enough verified evidence to describe the asset picture yet.",
        },
        # Legacy alias — prefer current_stance
        "current_posture": {
            "headline": "EVIDENCE INCOMPLETE",
            "explanation": "Not enough verified evidence to describe the asset picture yet.",
            "directional_state": "UNKNOWN",
            "confidence": "LOW",
            "evidence_refs": [],
        },
        "groups": {
            "market_structure": {
                "group_id": "market_structure",
                "title": "Price / Market Structure",
                "group_state": "UNKNOWN",
                "group_light": LIGHT_UNKNOWN,
                "signals": [
                    empty_signal("price_trend", "Price Trend", "Direction of the asset's own price."),
                    empty_signal("vs_btc", "vs BTC", "Relative strength versus Bitcoin."),
                    empty_signal("vs_sol", "vs SOL", "Relative strength versus Solana."),
                ],
            },
            "capital_flow": {
                "group_id": "capital_flow",
                "title": "Capital Flow",
                "group_state": "UNKNOWN",
                "group_light": LIGHT_UNKNOWN,
                "signals": [
                    empty_signal(
                        "spot_vs_leverage",
                        "Spot vs Leverage",
                        "Whether the move looks spot-led or leverage-heavy. Funding ≠ leverage.",
                    ),
                    empty_signal("who_is_buying", "Who Is Buying?", "Who is providing demand."),
                    empty_signal("who_is_selling", "Who Is Selling?", "Who is providing supply / selling pressure."),
                    empty_signal(
                        "whales_major_holders",
                        "Whales / Major Holders",
                        "Whether large holders are accumulating or distributing.",
                    ),
                    empty_signal(
                        "team_dev_ceo",
                        "Team / Dev / CEO",
                        "Verified team/dev/CEO wallet behaviour only.",
                    ),
                ],
            },
            "project_supply": {
                "group_id": "project_supply",
                "title": "Project / Supply",
                "group_state": "UNKNOWN",
                "group_light": LIGHT_UNKNOWN,
                "signals": [
                    empty_signal(
                        "project_health",
                        "Platform / Project Health",
                        "Asset-specific platform or network fundamentals.",
                    ),
                    empty_signal(
                        "liquidity_absorption",
                        "Liquidity / Absorption",
                        "Can real liquidity / spot demand absorb available selling pressure?",
                    ),
                    empty_signal(
                        "supply_unlocks",
                        "Supply / Unlocks",
                        "Circulating vs unlocked vs on-chain supply; destination of unlocked tokens.",
                    ),
                ],
            },
        },
    }


def _fmt_pct(v: Any) -> str | None:
    try:
        return f"{float(v):+.1f}%"
    except (TypeError, ValueError):
        return None


def enrich_tooltips(asset_top: dict[str, Any]) -> dict[str, Any]:
    """Tips are built at render time as evidence cards from signal fields."""
    return asset_top


def build_pump_asset_top(doc: dict[str, Any]) -> dict[str, Any]:
    """Map verified PUMP evidence into the universal ALT-top schema."""
    hero = doc.get("hero") or {}
    rs = doc.get("relative_strength") or {}
    rs_btc = rs.get("pump_btc") or {}
    rs_sol = rs.get("pump_sol") or {}
    forensics = doc.get("forensics") or {}
    buyer = forensics.get("buyer_forensics") or {}
    deriv = forensics.get("derivatives") or {}
    stage1 = doc.get("stage1_evidence") or {}
    supply = stage1.get("supply") or {}
    funding = stage1.get("funding") or {}
    health_metrics = (doc.get("project_health") or {}).get("metrics") or []
    by_id = {m.get("metric_id"): m for m in health_metrics}
    sd = forensics.get("split_display") or {}
    from lib.v3.pump_amendment_evidence import load_amendment_evidence

    amd = doc.get("amendment") or load_amendment_evidence() or {}
    if amd and not doc.get("amendment"):
        doc["amendment"] = amd

    top = empty_asset_top(hero.get("asset", "PUMP"), hero.get("price_display"))
    top["price_as_of"] = hero.get("price_as_of") or rs_btc.get("fetched_at")

    btc_7 = _fmt_pct(rs_btc.get("change_7d_pct"))
    btc_30 = _fmt_pct(rs_btc.get("change_30d_pct"))
    sol_7 = _fmt_pct(rs_sol.get("change_7d_pct"))
    sol_30 = _fmt_pct(rs_sol.get("change_30d_pct"))
    rs_as_of = rs_btc.get("fetched_at")

    price_trend_ok = rs_btc.get("change_30d_pct") is not None and float(rs_btc["change_30d_pct"]) > 0
    vs_btc_ok = rs_btc.get("change_7d_pct") is not None and float(rs_btc["change_7d_pct"]) > 0
    vs_sol_ok = rs_sol.get("change_7d_pct") is not None and float(rs_sol["change_7d_pct"]) > 0

    market_signals = [
        signal(
            signal_id="price_trend",
            label="Price Trend",
            state="STRONG" if price_trend_ok else "UNKNOWN",
            display="STRONG" if price_trend_ok else "UNKNOWN",
            light=LIGHT_GREEN if price_trend_ok else LIGHT_UNKNOWN,
            meaning="Direction of PUMP's own price, read through relative-strength windows.",
            evidence=(
                f"PUMP/BTC 7d {btc_7 or '—'} · 30d {btc_30 or '—'}; "
                f"PUMP/SOL 7d {sol_7 or '—'} · 30d {sol_30 or '—'}."
                if price_trend_ok
                else "No verified trend window available."
            ),
            unknown="" if price_trend_ok else "Price-trend series incomplete.",
            source=rs_btc.get("source", "binance-daily"),
            source_url=rs_btc.get("source_url") or BINANCE_PUMP_DAILY,
            as_of=rs_as_of,
            freshness=rs_btc.get("freshness") or "as_of-dated",
            confidence="MEDIUM" if price_trend_ok else "LOW",
            epistemic_status="KNOWN" if price_trend_ok else "UNKNOWN",
        ),
        signal(
            signal_id="vs_btc",
            label="vs BTC",
            state="LEADING" if vs_btc_ok else "UNKNOWN",
            display="LEADING" if vs_btc_ok else "UNKNOWN",
            light=LIGHT_GREEN if vs_btc_ok else LIGHT_UNKNOWN,
            meaning="Relative strength versus Bitcoin.",
            evidence=f"PUMP/BTC 7d {btc_7 or '—'} · 30d {btc_30 or '—'}." if vs_btc_ok else "RS vs BTC missing.",
            unknown="" if vs_btc_ok else "PUMP/BTC series incomplete.",
            source=rs_btc.get("source", "binance-daily"),
            source_url=rs_btc.get("source_url") or BINANCE_PUMP_DAILY,
            as_of=rs_as_of,
            freshness=rs_btc.get("freshness") or "as_of-dated",
            confidence="MEDIUM" if vs_btc_ok else "LOW",
            epistemic_status=rs_btc.get("epistemic_status", "UNKNOWN"),
        ),
        signal(
            signal_id="vs_sol",
            label="vs SOL",
            state="LEADING" if vs_sol_ok else "UNKNOWN",
            display="LEADING" if vs_sol_ok else "UNKNOWN",
            light=LIGHT_GREEN if vs_sol_ok else LIGHT_UNKNOWN,
            meaning="Relative strength versus Solana.",
            evidence=f"PUMP/SOL 7d {sol_7 or '—'} · 30d {sol_30 or '—'}." if vs_sol_ok else "RS vs SOL missing.",
            unknown="" if vs_sol_ok else "PUMP/SOL series incomplete.",
            source=rs_sol.get("source", "binance-daily"),
            source_url=rs_sol.get("source_url") or BINANCE_PUMP_DAILY,
            as_of=rs_as_of,
            freshness=rs_sol.get("freshness") or "as_of-dated",
            confidence="MEDIUM" if vs_sol_ok else "LOW",
            epistemic_status=rs_sol.get("epistemic_status", "UNKNOWN"),
        ),
    ]
    top["groups"]["market_structure"]["signals"] = market_signals
    top["groups"]["market_structure"]["group_state"] = "STRONG" if price_trend_ok and vs_btc_ok and vs_sol_ok else "UNKNOWN"
    top["groups"]["market_structure"]["group_light"] = (
        LIGHT_GREEN if price_trend_ok and vs_btc_ok and vs_sol_ok else LIGHT_UNKNOWN
    )

    fut_ratio = deriv.get("fut_spot_vol_ratio")
    tape = amd.get("tape") or {}
    if tape.get("perp_spot") is not None:
        fut_ratio = float(tape["perp_spot"])
    fut_disp = f"{fut_ratio:.1f}×" if isinstance(fut_ratio, (int, float)) else sd.get("fut_spot") or "UNKNOWN"
    funding_disp = funding.get("display") or sd.get("funding_context") or ""
    funding_word = funding.get("wording") or ""
    oi_bit = sd.get("oi_funding") or ""
    has_fut_spot = isinstance(fut_ratio, (int, float))
    tape_read = tape.get("read") or ""
    if tape_read == "PERPS LEAD":
        spot_lev_state = "PERPS LEAD"
        spot_lev_display = "FUNDING CALM · PERPS LEAD"
        spot_lev_light = LIGHT_ORANGE
        spot_lev_ev = (
            f"Binance futures ${tape.get('futures_quote_24h_usd', 0)/1e6:.0f}M vs spot "
            f"${tape.get('spot_quote_24h_usd', 0)/1e6:.0f}M ({fut_disp}). "
            f"Funding {tape.get('funding_8h')}. Calm funding ≠ spot-led. Do not say spot leads."
        )
    else:
        spot_lev_state = "ELEVATED VS SPOT" if has_fut_spot else "UNKNOWN"
        spot_lev_display = "ELEVATED VS SPOT" if has_fut_spot else "UNKNOWN"
        spot_lev_light = LIGHT_ORANGE if has_fut_spot else LIGHT_UNKNOWN
        spot_lev_ev = (
            f"Futures/spot {fut_disp}. {oi_bit}. {funding_disp}. {funding_word} "
            "Label = elevated versus spot only — historical threshold unvalidated "
            "(no Sep ATH / Jan high / June ATL backtest yet)."
        ).strip() if has_fut_spot else "Derivatives snapshot missing."

    ow = (buyer.get("observed_window") or {}) if buyer else {}
    net_n = ow.get("net_accumulator_count")
    hold_claim = ow.get("holding_claim")
    span_h = ow.get("span_hours")
    verdict_detail = buyer.get("verdict_detail") or ""
    if verdict_detail:
        buyer_ev = verdict_detail
    elif net_n is not None:
        span_bit = f"~{span_h:.0f}h" if span_h is not None else "observed"
        buyer_ev = f"{net_n} net DEX accumulators in {span_bit} span"
        if hold_claim:
            buyer_ev += f"; {hold_claim}"
    else:
        buyer_ev = (doc.get("capital_entry") or {}).get("detail", "DEX buyer sample incomplete.")

    july_attr = (doc.get("forensics") or {}).get("july_attribution") or {}
    own = july_attr.get("ownership_buyer_quality") or {}
    supply_full = supply.get("display_full") or supply.get("display_compact") or ""
    if own.get("supply_evidence"):
        supply_ev = own["supply_evidence"]
        supply_unknown = own.get("supply_unknown_line") or (
            "Beneficial owners and future Squads outflow timing remain UNKNOWN."
        )
    elif july_attr.get("supply_unknown_line"):
        supply_ev = july_attr.get("supply_evidence") or supply_full or july_attr.get("headline_who_selling") or ""
        supply_unknown = july_attr["supply_unknown_line"]
    else:
        supply_ev = supply_full or (doc.get("liquid_supply") or {}).get("note") or "Supply model incomplete."
        supply_unknown = (
            "Reconciliation UNKNOWN. Final destination of unlocked/moved tokens largely UNKNOWN."
        )

    wm = own.get("wintermute_otc") or {}
    buy_src_meta = own.get("buyer_quality_source") or {}
    sell_src_meta = own.get("who_selling_source") or {}
    supply_src_meta = own.get("supply_source") or {}
    mint_url = (
        own.get("source_url")
        or july_attr.get("source_url")
        or supply.get("mint_explorer")
        or "https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn"
    )
    buyer_url = None
    for w in (buyer or {}).get("wallet_profiles_checked") or []:
        links = w.get("sample_explorer_links") or []
        if links:
            buyer_url = str(links[0])
            break
        if w.get("sample_explorer"):
            buyer_url = str(w["sample_explorer"])
            break
    own_fresh = own.get("freshness") or july_attr.get("freshness") or "research-pack"

    if july_attr.get("pct") or own:
        who_sell_ev = own.get("who_selling_evidence") or july_attr.get("headline_who_selling") or ""
        who_sell_unknown = (
            "Does not identify the full market sell-side. OTC INTERACTION ≠ SALE. "
            "CEX deposits / custody movement do not prove sales."
        )
        who_sell_state = "PARTIAL"
        who_sell_light = LIGHT_ORANGE
        who_sell_conf = july_attr.get("confidence") or own.get("confidence") or "MEDIUM"
        who_sell_as = own.get("gathered_at") or july_attr.get("gathered_at")
        who_sell_src = sell_src_meta.get("source_label") or "Solscan · Squads custody + OTC"
        who_sell_url = sell_src_meta.get("source_url") or wm.get("explorer") or mint_url
        who_sell_fresh = sell_src_meta.get("freshness") or own_fresh
    else:
        who_sell_ev = (
            (doc.get("liquid_supply") or {}).get("note")
            or "July unlock cohort movement observed; destination largely unknown."
        )
        who_sell_unknown = (
            "Final destination of moved supply and whether deposits became sales remain UNKNOWN."
        )
        who_sell_state = "UNKNOWN"
        who_sell_light = LIGHT_UNKNOWN
        who_sell_conf = "LOW"
        who_sell_as = None
        who_sell_src = "wallet-forensics"
        who_sell_url = None
        who_sell_fresh = None

    bq = own.get("buyer_quality") or {}
    if bq.get("evidence"):
        buy_display = bq.get("display") or "REAL BUYING · TRADER-HEAVY"
        buy_ev = bq["evidence"]
        buy_unknown = bq.get("unknown") or "Buyer identity incomplete."
    else:
        buy_display = "PARTIAL"
        buy_ev = (
            f"Real DEX net buying observed: {buyer_ev}. "
            "Buyer identity and repeat/high-quality attribution remain incomplete. "
            "Individual CEX buyers unobservable."
        )
        buy_unknown = "Buyer identity / entity attribution incomplete."
    buy_src = buy_src_meta.get("source_label") or "Helius / Solana DEX sample"
    buy_url = buy_src_meta.get("source_url") or buyer_url
    buy_fresh = (buy_src_meta.get("freshness") or own_fresh) if own else None

    holder_rows = ((amd.get("holders") or {}).get("accounts") or [])
    unknown_big = [
        h for h in holder_rows
        if h.get("class") == "UNKNOWN_holder" and (h.get("ui_b") or 0) >= 19
    ]
    if unknown_big:
        bits = ", ".join(f"~{h['ui_b']:.2f}B".rstrip("0").rstrip(".") for h in unknown_big[:6])
        whale_state = "WATCH"
        whale_display = "UNKNOWN HOLDERS · NOT INFRA WHALES"
        whale_light = LIGHT_ORANGE
        whale_ev = (
            f"Classified largest accounts into protocol/CEX/vesting vs UNKNOWN. "
            f"UNKNOWN concentration to watch: {bits}. Protocol/CEX/vesting wallets are not individual whales."
        )
        whale_unknown = "Beneficial owners UNKNOWN. Movement could affect supply. Transfer ≠ sale."
        whale_as = amd.get("fetched_at_utc")
        whale_src = "Solana RPC largest accounts + known-wallet registry"
        whale_url = "https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn"
        whale_fresh = "as_of-dated"
        whale_conf = "MEDIUM"
    elif wm.get("evidence"):
        whale_state = "PARTIAL"
        whale_display = wm.get("display") or "LARGE HOLDER → WINTERMUTE OTC"
        whale_light = LIGHT_ORANGE
        whale_ev = wm["evidence"]
        whale_unknown = (
            f"{wm.get('discipline') or 'OTC INTERACTION ≠ SALE'}. "
            "Entity of the large holder UNKNOWN. Inventory source UNKNOWN."
        )
        whale_as = own.get("gathered_at")
        whale_src = wm.get("source_label") or "Solscan · Wintermute OTC flow"
        whale_url = wm.get("source_url") or wm.get("explorer")
        whale_fresh = wm.get("freshness") or own_fresh
        whale_conf = "MEDIUM"
    else:
        whale_state = "UNKNOWN"
        whale_display = "UNKNOWN"
        whale_light = LIGHT_UNKNOWN
        whale_ev = "No verified current whale/major-holder accumulation or distribution classification."
        whale_unknown = "Historical whale/insider distribution at prior highs remains UNKNOWN."
        whale_as = None
        whale_src = None
        whale_url = None
        whale_fresh = None
        whale_conf = "LOW"

    capital_signals = [
        signal(
            signal_id="spot_vs_leverage",
            label="Spot vs Leverage",
            state=spot_lev_state,
            display=spot_lev_display,
            light=spot_lev_light,
            meaning="Whether the move looks spot-led or leverage-heavy. Funding ≠ leverage. Calm funding ≠ spot-led.",
            evidence=spot_lev_ev,
            unknown="Whether this futures/spot ratio is historically abnormal before tops is UNKNOWN until backtest.",
            source="binance",
            source_url=BINANCE_PUMP_FUT,
            as_of=forensics.get("gathered_at") or rs_as_of,
            freshness="as_of-dated",
            confidence="MEDIUM" if has_fut_spot else "LOW",
            epistemic_status="PARTIAL" if has_fut_spot else "UNKNOWN",
        ),
        signal(
            signal_id="who_is_buying",
            label="Who Is Buying?",
            state="PARTIAL",
            display=buy_display,
            light=LIGHT_ORANGE,
            meaning="Who is providing demand — verified swaps / net accumulators only.",
            evidence=buy_ev,
            unknown=buy_unknown,
            source=buy_src if bq else "wallet-forensics",
            source_url=buy_url,
            as_of=own.get("gathered_at")
            or buyer.get("snapshot_id")
            or doc.get("meta", {}).get("buyer_forensics_snapshot_id"),
            freshness=buy_fresh,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
        signal(
            signal_id="who_is_selling",
            label="Who Is Selling?",
            state=who_sell_state,
            display=who_sell_state,
            light=who_sell_light,
            meaning="Who is providing supply / selling pressure. Transfer ≠ sale. OTC INTERACTION ≠ SALE.",
            evidence=who_sell_ev,
            unknown=who_sell_unknown,
            source=who_sell_src,
            source_url=who_sell_url,
            as_of=who_sell_as,
            freshness=who_sell_fresh,
            confidence=who_sell_conf,
            epistemic_status=who_sell_state,
        ),
        signal(
            signal_id="whales_major_holders",
            label="Whales / Major Holders",
            state=whale_state,
            display=whale_display,
            light=whale_light,
            meaning="Whether large holders are accumulating or distributing.",
            evidence=whale_ev,
            unknown=whale_unknown,
            source=whale_src,
            source_url=whale_url,
            as_of=whale_as,
            freshness=whale_fresh,
            confidence=whale_conf,
            epistemic_status=whale_state,
        ),
        signal(
            signal_id="team_dev_ceo",
            label="Team / Dev / CEO",
            state="UNKNOWN",
            display="UNKNOWN",
            light=LIGHT_UNKNOWN,
            meaning="Verified team/dev/CEO wallet behaviour only.",
            evidence="No verified team/dev/CEO wallet attribution available for current behaviour.",
            unknown="Do not infer team selling from unlock movement alone.",
            confidence="LOW",
            epistemic_status="UNKNOWN",
        ),
    ]
    top["groups"]["capital_flow"]["signals"] = capital_signals
    top["groups"]["capital_flow"]["group_state"] = "UNRESOLVED"
    top["groups"]["capital_flow"]["group_light"] = LIGHT_ORANGE

    rev = by_id.get("platform_revenue") or {}
    buy = by_id.get("buyback_burn") or {}
    dex = by_id.get("dex_liquidity_usd") or {}
    share = by_id.get("launchpad_share") or {}
    health_live = rev.get("data_status") == "LIVE" or buy.get("data_status") == "LIVE"
    health_bits = []
    if rev.get("value"):
        health_bits.append(f"Revenue {rev['value']}")
    if buy.get("value"):
        health_bits.append(f"Buyback/burn {buy['value']}")
    if share.get("value"):
        health_bits.append(f"Launchpad 24h share {share['value']}")
    pol = amd.get("policy") or {}
    if pol.get("allocation"):
        health_bits.insert(
            0,
            "~50% parent net revenue → programmatic PUMP buybacks → burn (locked ~through Apr 2027; not 100%; not guaranteed after lock)",
        )
    buy_amd = amd.get("buyback") or {}
    if buy_amd.get("latest_daily_usd") is not None:
        health_bits.append(
            f"Buyback now ${buy_amd['latest_daily_usd']/1e3:.0f}K/d · 7d ${buy_amd.get('total_7d_usd', 0)/1e6:.1f}M "
            f"({buy_amd.get('wow_pct', 0):+.0f}% vs prior 7d)"
        )
    health_ev = " · ".join(health_bits) if health_bits else "Platform metrics incomplete."

    dex_live = dex.get("data_status") == "LIVE" and dex.get("value")
    liq_ev = (
        f"DEX liquidity {dex.get('value')}. Revenue/buyback live. "
        "Does not prove all sell-side pressure is absorbed."
        if dex_live
        else "Liquidity/absorption evidence incomplete."
    )

    supply_full = supply.get("display_full") or supply.get("display_compact") or ""
    # july_attr / who_sell_* / supply_ev prepared above capital_signals

    project_signals = [
        signal(
            signal_id="project_health",
            label="Platform / Project Health",
            state="HEALTHY" if health_live else "UNKNOWN",
            display="HEALTHY" if health_live else "UNKNOWN",
            light=LIGHT_GREEN if health_live else LIGHT_UNKNOWN,
            meaning="pump.fun platform economics — fees, revenue, buybacks, launchpad share.",
            evidence=health_ev,
            unknown="" if health_live else "Platform fundamentals not live.",
            source=rev.get("source") or buy.get("source") or "defillama",
            source_url=rev.get("source_url") or buy.get("source_url") or DEFILLAMA_PUMP_FEES,
            as_of=rev.get("fetched_at") or buy.get("fetched_at"),
            freshness="as_of-dated",
            confidence="MEDIUM" if health_live else "LOW",
            epistemic_status="KNOWN" if health_live else "UNKNOWN",
        ),
        signal(
            signal_id="liquidity_absorption",
            label="Liquidity / Absorption",
            state="PARTIAL" if dex_live else "UNKNOWN",
            display="PARTIAL" if dex_live else "UNKNOWN",
            light=LIGHT_ORANGE if dex_live else LIGHT_UNKNOWN,
            meaning="Can real liquidity / spot demand absorb available selling pressure?",
            evidence=liq_ev,
            unknown="Full sell-side absorption remains unverified.",
            source=dex.get("source") or "dexscreener",
            source_url=dex.get("source_url") or DEXSCREENER_PUMP_FALLBACK,
            as_of=dex.get("fetched_at"),
            freshness="as_of-dated",
            confidence="MEDIUM" if dex_live else "LOW",
            epistemic_status="PARTIAL" if dex_live else "UNKNOWN",
        ),
        signal(
            signal_id="supply_unlocks",
            label="Supply / Unlocks",
            state="WATCH",
            display="WATCH",
            light=LIGHT_ORANGE,
            meaning="Circulating vs schedule-unlocked vs on-chain supply. UNLOCKED ≠ LIQUID ≠ SOLD. TRANSFER ≠ SALE. custody ≠ sale.",
            evidence=(
                (
                    "July was a cliff (~82.5B scheduled / ~52B observed into Squads), not the normal monthly drip. "
                    "August drip is 6.875B (DefiLlama) — Aug 12 unlock and Aug 15 movement are one event. "
                    "Next ~12 Sep: DefiLlama 6.875B vs Tokenomics 9.17B — UNRESOLVED, both shown. "
                    "~240B community allocation is future supply uncertainty, not circulating. "
                    "Transfer ≠ sale. Unlock ≠ dump."
                )
                if amd.get("unlocks")
                else (
                    supply_ev
                    + (
                        f" {own.get('supply_interpretation')}"
                        if own.get("supply_interpretation")
                        else ""
                    )
                )
            ),
            unknown=supply_unknown,
            source=(
                supply_src_meta.get("source_label")
                or own.get("source_label")
                or "Solscan · PUMP mint / Squads custody"
            )
            if own
            else (
                "stage1-supply-model"
                if not july_attr.get("pct")
                else "Solscan · July cohort attribution"
            ),
            source_url=(
                supply_src_meta.get("source_url")
                or own.get("source_url")
                or mint_url
            )
            if own or july_attr.get("pct")
            else supply.get("mint_explorer"),
            as_of=own.get("gathered_at") or (july_attr.get("gathered_at") if july_attr else None),
            freshness=(supply_src_meta.get("freshness") or own_fresh) if own else None,
            confidence="MEDIUM",
            epistemic_status="PARTIAL",
        ),
    ]
    top["groups"]["project_supply"]["signals"] = project_signals
    top["groups"]["project_supply"]["group_state"] = "HEALTHY · WATCH SUPPLY"
    top["groups"]["project_supply"]["group_light"] = LIGHT_GREEN

    from lib.v3.current_stance import pump_current_stance

    stance = pump_current_stance()
    # Keep compact hero summary; optional forensics note must not reintroduce BUY/SELL language
    if july_attr and july_attr.get("posture_explanation"):
        # Prefer Job #5 locked summary — forensics note already reflected in modal holds_back
        pass
    top["current_stance"] = stance
    top["current_posture"] = {
        "headline": stance["headline"],
        "explanation": stance["summary"],
        "directional_state": "BULLISH_UNRESOLVED",
        "confidence": stance["confidence"],
        "evidence_refs": [
            "relative_strength.pump_btc",
            "relative_strength.pump_sol",
            "forensics.derivatives",
            "forensics.buyer_forensics",
            "stage1_evidence.supply",
            "project_health.metrics",
        ],
    }

    # Keep hero descriptive fields in sync (no action verbs)
    doc.setdefault("hero", {})
    doc["hero"]["v3_posture"] = stance["headline"]
    doc["hero"]["v3_posture_note"] = stance["summary"]
    doc["hero"]["v3_stance"] = stance["headline"]
    doc["hero"]["v3_stance_note"] = stance["summary"]
    doc["hero"]["thesis"] = ""  # removed from UI; old question line must not show

    return enrich_tooltips(top)
