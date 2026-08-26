"""Build RENDER V3 intelligence JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.paths import REPORTS
from lib.v3.fields import category_state, concerning_meter, pack_risk_confirmation, field, missing_field, now_iso
from lib.v3.sma_trend import technical_trend_category
from lib.v3.pump_forensics_loader import fmt_rs_line
from lib.v3.rs import rs_block


def _prior_asset_v3(slug: str, before_date: str) -> dict | None:
    if not REPORTS.exists():
        return None
    dates = sorted(
        d.name
        for d in REPORTS.iterdir()
        if d.is_dir() and d.name < before_date and (d / f"{slug}-v3.json").exists()
    )
    if not dates:
        return None
    return json.loads((REPORTS / dates[-1] / f"{slug}-v3.json").read_text())


def _health_metrics(ev: dict[str, Any], fetched_at: str) -> list[dict]:
    foundation = (ev.get("render_evidence") or {}).get("foundation") or {}
    parse_st = foundation.get("parse_status")
    f_at = foundation.get("fetched_at") or fetched_at
    frames = foundation.get("frames_rendered")
    nodes = foundation.get("nodes_total")
    burned = foundation.get("cumulative_burned")
    metrics = []
    if frames is not None:
        metrics.append(
            field(
                "frames_rendered",
                "Cumulative frames rendered",
                frames,
                source="render_foundation_dashboard",
                source_url="https://stats.renderfoundation.com/",
                fetched_at=f_at,
            )
        )
    else:
        metrics.append(
            missing_field(
                "frames_rendered",
                "Cumulative frames rendered",
                data_status="FAILED" if parse_st == "FAILED" else "MISSING",
                source_url="https://stats.renderfoundation.com/",
            )
        )
    if nodes is not None:
        metrics.append(
            field(
                "nodes_total",
                "Nodes since inception",
                nodes,
                source="render_foundation_dashboard",
                source_url="https://stats.renderfoundation.com/",
                fetched_at=f_at,
            )
        )
    else:
        metrics.append(
            missing_field(
                "nodes_total",
                "Nodes since inception",
                data_status="FAILED" if parse_st == "FAILED" else "MISSING",
                source_url="https://stats.renderfoundation.com/",
            )
        )
    if burned:
        metrics.append(
            field(
                "cumulative_burned",
                "Cumulative RENDER burned",
                burned,
                source="render_foundation_dashboard",
                fetched_at=fetched_at,
                note="Cumulative — burn/emission ratio not live.",
            )
        )
    else:
        metrics.append(
            missing_field("cumulative_burned", "Cumulative RENDER burned", note="Burn scrape failed this run.")
        )
    metrics.extend(
        [
            missing_field(
                "burn_emission_ratio",
                "Burn / emission ratio",
                note="NEEDS_ENGINEERING — emissions not on dashboard scrape.",
            ),
            missing_field("usd_network_usage", "USD/EUR paid network usage"),
            missing_field("ai_compute_split", "Rendering vs AI compute split", impl_status="NEEDS_ENGINEERING"),
        ]
    )
    return metrics


def _health_pump(ev: dict[str, Any], fetched_at: str) -> list[dict]:
    pump_ev = ev.get("pump_evidence") or {}
    price_block = pump_ev.get("price") or {}
    dex = pump_ev.get("dex_liquidity")
    site_ok = pump_ev.get("site_ok", False)
    metrics = []
    if price_block.get("price_usd"):
        metrics.append(
            field(
                "pump_price_usd",
                "PUMP price",
                price_block["price_usd"],
                unit="USD",
                source="coingecko/dex",
                fetched_at=fetched_at,
            )
        )
    if dex and dex.get("usd"):
        metrics.append(
            field(
                "dex_liquidity_usd",
                "DEX liquidity (best pool)",
                dex["usd"],
                unit="USD",
                source="dexscreener",
                fetched_at=fetched_at,
            )
        )
    else:
        metrics.append(missing_field("dex_liquidity_usd", "DEX liquidity"))
    metrics.append(
        field(
            "platform_site",
            "pump.fun status",
            "ACTIVE" if site_ok else "NOT VERIFIED",
            source="pump.fun",
            fetched_at=fetched_at,
            epistemic="KNOWN" if site_ok else "UNKNOWN",
        )
    )
    from lib.v3.pump_platform_health import fetch_pump_platform_health, platform_health_fields

    plat = fetch_pump_platform_health()
    metrics.extend(platform_health_fields(plat, fetched_at))
    return metrics


def _timing_metrics(
    ev: dict[str, Any],
    market: dict[str, Any],
    fetched_at: str,
    *,
    evidence_key: str,
    daily_key: str,
    asset_label: str,
    rs_btc_id: str,
    rs_sol_id: str,
    include_ai_basket: bool = True,
) -> list[dict]:
    daily = ev.get("daily_prices") or {}
    render_p = daily.get(daily_key) or {}
    btc_p = daily.get("btc") or {}
    sol_p = daily.get("sol") or {}
    price_block = (ev.get(evidence_key) or {}).get("price") or {}
    price = price_block.get("price_usd")
    ath_pct = price_block.get("ath_change_pct")

    metrics = []
    if price is not None:
        metrics.append(
            field(f"{daily_key}_price_usd", f"{asset_label} price", price, unit="USD", source="coingecko", fetched_at=fetched_at)
        )
    if ath_pct is not None:
        metrics.append(
            field(
                "ath_drawdown_pct",
                "From ATH",
                abs(ath_pct),
                unit="% retraced",
                fetched_at=fetched_at,
                source="coingecko",
            )
        )

    rs_btc = rs_block(rs_btc_id, f"{asset_label} / BTC", render_p, btc_p, "BTC", fetched_at)
    rs_sol = rs_block(rs_sol_id, f"{asset_label} / SOL", render_p, sol_p, "SOL", fetched_at)
    for key, block in [(rs_btc_id, rs_btc), (rs_sol_id, rs_sol)]:
        if block.get("ratio") is not None:
            ch7 = block.get("change_7d_pct")
            ch30 = block.get("change_30d_pct")
            if ch7 is not None and ch30 is not None:
                val = (
                    f"ratio {block['ratio']:.4f} · 7d {ch7:+.1f}% · 30d {ch30:+.1f}%"
                )
            else:
                val = f"ratio {block['ratio']:.4f}"
            metrics.append(
                field(
                    key,
                    block["label"],
                    val,
                    source="coingecko_market_chart",
                    fetched_at=fetched_at,
                    impl_status=block.get("implementation_status", "PRODUCTION_READY"),
                )
            )
        else:
            metrics.append(missing_field(key, block["label"]))

    if include_ai_basket:
        metrics.append(
            missing_field(
                f"{daily_key}_ai_basket",
                f"{asset_label} / AI basket",
                note="See config/v3-ai-basket.json — not wired for this asset.",
            )
        )
    metrics.extend(
        [
            missing_field("oi_funding", "OI / funding", data_status="MISSING", impl_status="NEEDS_BACKTESTING"),
            missing_field("spot_perp", "Spot vs perp volume", data_status="MISSING"),
        ]
    )

    for fam in market.get("families", []):
        metrics.append(
            field(
                f"market_ref_{fam['family_id']}",
                f"Market · {fam['title']}",
                fam["display_state"],
                fetched_at=fetched_at,
                source="market-v3",
                epistemic="INFERRED",
                note=fam.get("note"),
            )
        )
    return metrics


def _warning_stack(
    ev: dict[str, Any],
    rs_btc: dict,
    rs_sol: dict,
    *,
    asset_label: str = "RENDER",
) -> dict:
    price_block = (ev.get("render_evidence") or {}).get("price") or {}
    ath_pct = price_block.get("ath_change_pct")
    categories = []

    categories.append(
        category_state(
            "btc_market",
            "BTC / MARKET ENVIRONMENT",
            "UNKNOWN",
            detail="Market family states not classified — see shared market layer.",
            impl_status="NEEDS_BACKTESTING",
        )
    )

    rs_weak = (
        rs_btc.get("change_30d_pct") is not None
        and rs_btc["change_30d_pct"] < 0
        and rs_sol.get("change_30d_pct") is not None
        and rs_sol["change_30d_pct"] < 0
    )
    rs_missing = rs_btc.get("ratio") is None
    if rs_missing:
        lead_st = "UNKNOWN"
        lead_detail = "RS series incomplete."
    elif rs_weak:
        lead_st = "PARTIAL"
        lead_detail = f"30d {asset_label}/BTC and {asset_label}/SOL both negative."
    else:
        lead_st = "CLEAR"
        lead_detail = "30d RS not uniformly negative on wired pairs."

    categories.append(
        category_state(
            "render_leadership",
            "RELATIVE STRENGTH / LEADERSHIP",
            lead_st,
            detail=lead_detail,
            impl_status="NEEDS_BACKTESTING",
        )
    )

    categories.append(
        category_state(
            "liquid_supply",
            "LIQUID SUPPLY / DISTRIBUTION",
            "UNKNOWN",
            detail="Wallet/GSR/CEX pipeline not wired.",
            impl_status="NEEDS_ENGINEERING + NEEDS_BACKTESTING",
        )
    )
    categories.append(
        category_state(
            "spot_leverage",
            "SPOT VS LEVERAGE",
            "UNKNOWN",
            detail="OI / funding percentiles not in the current system.",
            impl_status="NEEDS_BACKTESTING",
        )
    )

    if ath_pct is not None and ath_pct < -70:
        cat_st = "PARTIAL"
        cat_detail = "Deep retracement from ATH — lifecycle context only. Retracement is not bad on its own; watch how far and when it turns."
    else:
        cat_st = "UNKNOWN"
        cat_detail = "Catalyst response tracker not wired."
    categories.append(
        category_state(
            "catalyst_lifecycle",
            "CATALYST / LIFECYCLE",
            cat_st,
            detail=cat_detail,
            impl_status="NEEDS_BACKTESTING",
        )
    )
    categories.append(
        category_state(
            "network_fundamentals",
            "NETWORK FUNDAMENTALS",
            "CLEAR",
            detail="No evidence the underlying network failed with the token price.",
            impl_status="PRODUCTION_READY",
        )
    )

    active = concerning_meter(categories)
    return {
        "categories": categories,
        "meter_active": active,
        "meter_total": len(categories),
        "summary": f"{active} of {len(categories)} categories concerning or partial",
    }


def _bullish_stack(rs_btc: dict, rs_sol: dict, health_metrics: list[dict]) -> dict:
    cats = [
        category_state("market_regime", "Market regime supportive", "UNKNOWN", impl_status="NEEDS_BACKTESTING"),
        category_state(
            "render_rs",
            "RENDER relative leadership",
            "NOT CONFIRMED" if rs_btc.get("change_30d_pct") is None or rs_btc["change_30d_pct"] <= 0 else "PARTIAL",
            detail="Based on 30d RENDER/BTC only — SOL/AI incomplete.",
            impl_status="NEEDS_BACKTESTING",
        ),
        category_state("spot_capital", "Spot / capital confirmation", "UNKNOWN", impl_status="NEEDS_ENGINEERING"),
        category_state("supply_absorbed", "Sellable supply absorbed", "UNKNOWN", impl_status="NEEDS_ENGINEERING"),
        category_state(
            "project_health",
            "Project Health improving",
            "PARTIAL",
            detail="Network metrics live; burn/emission ratio not wired.",
            impl_status="PRODUCTION_READY",
        ),
    ]
    confirmed = sum(1 for c in cats if c["state"] == "CONFIRMED")
    return {
        "categories": cats,
        "summary": f"{confirmed} of {len(cats)} independent categories confirmed",
    }


def _bullish_stack_pump(
    rs_btc: dict,
    rs_sol: dict,
    health_metrics: list[dict],
    wf: dict,
    deriv: dict,
    buyer: dict | None = None,
) -> dict:
    from lib.v3.pump_forensics_loader import buyer_evidence_detail, buyer_evidence_label

    buyer_label = buyer_evidence_label(wf, buyer)
    rs_st = "PARTIAL" if rs_btc.get("change_30d_pct") and rs_btc["change_30d_pct"] > 0 else "NOT CONFIRMED"
    if rs_sol.get("change_30d_pct") is not None and rs_sol["change_30d_pct"] <= 0:
        rs_st = "NOT CONFIRMED"
    fut_ratio = deriv.get("fut_spot_vol_ratio")
    spot_st = "UNKNOWN" if not fut_ratio else ("PARTIAL" if fut_ratio > 5 else "PARTIAL")
    hm = {m.get("metric_id"): m for m in health_metrics}
    health_st = "PARTIAL" if hm.get("platform_revenue", {}).get("data_status") == "LIVE" else "UNKNOWN"
    buyer_st = "PARTIAL" if buyer_label in ("INCONCLUSIVE", "MIXED", "LEVERAGE-LED") else "UNKNOWN"
    if buyer_label == "ACCUMULATION SIGNAL":
        buyer_st = "PARTIAL"
    cats = [
        category_state(
            "platform_economics",
            "Platform economics supportive",
            health_st,
            detail="Revenue and buyback/burn wired from DefiLlama.",
            impl_status="PRODUCTION_READY",
        ),
        category_state(
            "pump_rs",
            "PUMP relative leadership",
            rs_st,
            detail="PUMP/BTC and PUMP/SOL 30d RS from forensics snapshot.",
            impl_status="PRODUCTION_READY",
        ),
        category_state(
            "spot_capital",
            "Spot / capital confirmation",
            spot_st,
            detail=f"Futures {fut_ratio:.1f}× spot — leverage-heavy." if fut_ratio else "Derivatives snapshot missing.",
            impl_status="PRODUCTION_READY",
        ),
        category_state(
            "buyer_quality",
            "Buyer / flow quality",
            buyer_st,
            detail=buyer_evidence_detail(buyer),
            impl_status="PRODUCTION_READY",
        ),
    ]
    confirmed = sum(1 for c in cats if c["state"] == "CONFIRMED")
    return {
        "categories": cats,
        "summary": f"{confirmed} of {len(cats)} capital-entry categories confirmed",
    }


def _knowledge_census(ev: dict[str, Any], rs_btc: dict, rs_sol: dict) -> dict:
    known, inferred, unknown = [], [], []

    foundation = (ev.get("render_evidence") or {}).get("foundation") or {}
    if foundation.get("frames_rendered"):
        known.append("Foundation dashboard frames/nodes observed this run.")
    if rs_btc.get("ratio") is not None:
        known.append(f"RENDER/BTC ratio and rolling changes computed from CoinGecko daily prices.")
    if (ev.get("render_evidence") or {}).get("price"):
        known.append("RENDER USD price and ATH drawdown from CoinGecko.")

    inferred.append("Project fundamentals alone do not time entries — per final research.")
    if rs_btc.get("change_30d_pct") is not None and rs_btc["change_30d_pct"] < 0:
        inferred.append("30d RENDER/BTC deterioration suggests weak relative leadership.")

    unknown.extend(
        [
            "Current labelled GSR / treasury / CEX flows.",
            "OI / funding percentile and spot-perp split.",
            "MM intent and beneficial ownership.",
            "Whether CEX deposits became sales.",
            "AI basket RS until basket history validated.",
        ]
    )
    if rs_sol.get("ratio") is None:
        unknown.append("Full RENDER/SOL RS series when price fetch fails.")

    return {"known": known, "inferred": inferred, "unknown": unknown}


def _falsifiers(rs_btc: dict, rs_sol: dict) -> dict:
    constructive = [
        {
            "label": "Leadership returns",
            "detail": "RENDER/BTC + RENDER/SOL + RENDER/AI positive on 30d with live series.",
            "status": "REQUIRED",
        },
        {
            "label": "Spot confirms",
            "detail": "Spot volume improves without leverage becoming dominant engine.",
            "status": "REQUIRED",
        },
        {
            "label": "Supply absorbed",
            "detail": "No concerning controlled-wallet/CEX flow while price holds leadership.",
            "status": "CONFIRM",
        },
    ]
    defensive = [
        {
            "label": "RS deteriorates into strength",
            "detail": "USD rises but BTC/SOL/AI ratios stop confirming.",
            "status": "WARNING",
        },
        {
            "label": "Distribution stack",
            "detail": "Controlled supply → MM/CEX plus deposits plus failed breakout.",
            "status": "RED",
        },
        {
            "label": "Leverage takes over",
            "detail": "OI/funding extreme while spot participation weakens.",
            "status": "RED",
        },
    ]
    if rs_btc.get("change_30d_pct") is not None and rs_btc["change_30d_pct"] < -5:
        defensive[0]["detail"] += f" (30d RENDER/BTC {rs_btc['change_30d_pct']:+.1f}% now.)"
    return {"more_constructive": constructive, "more_defensive": defensive}


def _what_changed(prior: dict | None, current: dict, fetched_at: str, rs_keys: tuple[str, str]) -> list[dict]:
    if not prior:
        return [
            {
                "metric": "v3_snapshot",
                "previous": None,
                "current": "baseline",
                "delta": "NO PRIOR V3 SNAPSHOT — CHANGE COMPARISON NOT AVAILABLE",
                "why": "First V3 run.",
                "confidence": "HIGH",
                "data_status": "LIVE",
            }
        ]

    changes = []
    old_rs = prior.get("relative_strength", {})
    new_rs = current.get("relative_strength", {})
    for pair in rs_keys:
        o30 = old_rs.get(pair, {}).get("change_30d_pct")
        n30 = new_rs.get(pair, {}).get("change_30d_pct")
        if o30 is not None and n30 is not None and abs(n30 - o30) > 0.5:
            changes.append(
                {
                    "metric": pair,
                    "previous": f"30d {o30:+.1f}%",
                    "current": f"30d {n30:+.1f}%",
                    "delta": f"{n30 - o30:+.1f}pp",
                    "why": "Relative strength roll.",
                    "confidence": "MEDIUM",
                    "data_status": "LIVE",
                }
            )
    if not changes:
        changes.append(
            {
                "metric": "tracked_states",
                "previous": prior.get("meta", {}).get("report_date"),
                "current": current.get("meta", {}).get("report_date"),
                "delta": "No material change on wired V3 metrics.",
                "why": "Stable week on available feeds.",
                "confidence": "MEDIUM",
                "data_status": "LIVE",
            }
        )
    return changes


def build_asset_v3(
    slug: str,
    symbol: str,
    evidence: dict[str, Any],
    market: dict[str, Any],
    report_date: str,
    v4_report: dict | None,
    *,
    evidence_key: str,
    daily_key: str,
    thesis: str,
    health_metrics_fn,
    rs_btc_id: str,
    rs_sol_id: str,
    ai_basket_note: str,
) -> dict[str, Any]:
    fetched_at = evidence.get("fetched_at") or now_iso()
    prior = _prior_asset_v3(slug, report_date)

    daily = evidence.get("daily_prices") or {}
    asset_p = daily.get(daily_key) or {}
    btc_p = daily.get("btc") or {}
    sol_p = daily.get("sol") or {}

    rs_btc = rs_block(rs_btc_id, f"{symbol} / BTC", asset_p, btc_p, "BTC", fetched_at)
    rs_sol = rs_block(rs_sol_id, f"{symbol} / SOL", asset_p, sol_p, "SOL", fetched_at)

    price_block = (evidence.get(evidence_key) or {}).get("price") or {}
    price = price_block.get("price_usd")
    ath_pct = price_block.get("ath_change_pct")

    health_metrics = health_metrics_fn(evidence, fetched_at)
    timing_metrics = _timing_metrics(
        evidence,
        market,
        fetched_at,
        evidence_key=evidence_key,
        daily_key=daily_key,
        asset_label=symbol,
        rs_btc_id=rs_btc_id,
        rs_sol_id=rs_sol_id,
        include_ai_basket=(slug != "pump"),
    )
    warning = _warning_stack(evidence, rs_btc, rs_sol, asset_label=symbol)

    lifecycle_stage = "UNCLEAR"
    lifecycle_note = "No approved lifecycle classifier — descriptive inputs only."
    health_display = "UNCLASSIFIED"
    health_note = "Raw evidence shown — no invented overall health threshold."
    timing_display = "UNCLASSIFIED"
    if rs_btc.get("change_30d_pct") is not None and rs_btc["change_30d_pct"] < 0:
        timing_display = "WEAK RS (30d)"
        timing_note = f"{symbol}/BTC 30d negative — not a production rule."
    else:
        timing_note = "Timing classification incomplete — RS/leverage/supply not fully wired."

    doc = {
        "meta": {
            "schema": f"{slug}-v3",
            "slug": slug,
            "report_date": report_date,
            "generated_at": fetched_at,
            "version": "phase1-v1",
            "v4_report_date": v4_report.get("report_date") if v4_report else None,
        },
        "hero": {
            "asset": symbol,
            "price_usd": price,
            "price_display": v4_report.get("price_display") if v4_report else (f"~${price:.4f}" if price and price < 1 else f"~${price:.2f}" if price else "—"),
            "thesis": thesis,
            "v3_posture": "NOT YET WIRED",
            "v3_posture_note": "No approved V3 decision engine in Phase 1.",
            "confidence": "NOT_ASSESSED",
            "data_completeness": "Partial — wallets, derivatives, supply chain not live.",
            "legacy_v4_call": v4_report.get("asset_call") if v4_report else None,
        },
        "triad": {
            "lifecycle": {
                "display": lifecycle_stage,
                "detail": lifecycle_note,
                "implementation_status": "NEEDS_BACKTESTING",
            },
            "project_health": {"display": health_display, "detail": health_note},
            "market_timing": {"display": timing_display, "detail": timing_note},
        },
        "project_health": {"overall_state": health_display, "metrics": health_metrics},
        "market_timing": {"overall_state": timing_display, "metrics": timing_metrics},
        "relative_strength": {
            rs_btc_id: rs_btc,
            rs_sol_id: rs_sol,
            "ai_basket": {
                "data_status": "MISSING",
                "implementation_status": "NEEDS_ENGINEERING",
                "note": ai_basket_note,
            },
        },
        "capital_entry": {
            "display_state": "UNKNOWN",
            "implementation_status": "NEEDS_ENGINEERING + NEEDS_BACKTESTING",
            "note": "Wallet cohort model not wired — cannot drive V3 posture.",
        },
        "liquid_supply": {
            "display_state": "UNKNOWN",
            "chain_stages": ["CONTROLLED", "TRANSFER", "MM_INFRA", "CEX", "EXECUTION"],
            "implementation_status": "NEEDS_ENGINEERING",
            "note": "Progressive evidence chain scaffolded — feeds not live.",
        },
        "spot_vs_leverage": {"display_state": "UNKNOWN", "implementation_status": "NEEDS_BACKTESTING"},
        "catalyst_response": {
            "display_state": "NO ACTIVE CATALYST",
            "events": [],
            "implementation_status": "NEEDS_BACKTESTING",
        },
        "warning_stack": warning,
        "bullish_stack": _bullish_stack(rs_btc, rs_sol, health_metrics),
        "lifecycle": {
            "current_stage": lifecycle_stage,
            "stages": [
                {"n": 1, "id": "reset_base", "label": "RESET / BASE"},
                {"n": 2, "id": "emerging", "label": "EMERGING LEADERSHIP"},
                {"n": 3, "id": "established", "label": "ESTABLISHED LEADERSHIP"},
                {"n": 4, "id": "extended", "label": "EXTENDED / REFLEXIVE"},
                {"n": 5, "id": "deteriorating", "label": "DETERIORATING / DISTRIBUTION"},
            ],
            "active_index": None,
            "note": lifecycle_note,
        },
        "knowledge_census": _knowledge_census(evidence, rs_btc, rs_sol),
        "what_would_change_mind": _falsifiers(rs_btc, rs_sol),
    }
    doc["what_changed"] = _what_changed(
        prior,
        {"meta": {"report_date": report_date}, "relative_strength": {rs_btc_id: rs_btc, rs_sol_id: rs_sol}},
        fetched_at,
        (rs_btc_id, rs_sol_id),
    )
    return doc


def build_render_v3(
    evidence: dict[str, Any],
    market: dict[str, Any],
    report_date: str,
    v4_report: dict | None,
) -> dict[str, Any]:
    """RENDER V3 from canonical Stage-1 completion packs (no broad live research)."""
    from lib.v3.render_product import build_render_v3_from_packs

    _ = evidence, market  # retained for call-site compatibility; packs are canonical
    return build_render_v3_from_packs(report_date, v4_report)


def _fmt_b(tokens: float) -> str:
    if tokens >= 1_000_000_000:
        return f"{tokens / 1_000_000_000:.2f}B"
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M"
    return f"{tokens:,.0f}"


def _apply_stage1_evidence(doc: dict) -> None:
    from lib.v3.pump_stage1_evidence import load_stage1_evidence

    s1 = load_stage1_evidence()
    if not s1:
        return
    doc["stage1_evidence"] = s1

    timing = doc.get("market_timing", {}).get("metrics", [])
    funding = s1.get("funding") or {}
    if funding.get("display"):
        _patch_metric(
            timing,
            "binance_funding_context",
            funding["display"],
            label="Binance funding context",
            source="binance",
            note=funding.get("wording"),
            epistemic="KNOWN",
        )
        # Enrich existing oi_funding note without replacing spot snapshot
        for m in timing:
            if m.get("metric_id") == "oi_funding":
                m["note"] = (
                    f"{m.get('note', '')} · {funding.get('wording', '')} "
                    f"Jan/Sep OI {funding.get('oi_jan_sep', 'UNKNOWN')}."
                ).strip(" ·")

    health = doc.get("project_health", {}).get("metrics", [])
    plat = s1.get("platform") or {}
    if plat.get("display_share_history"):
        _patch_metric(
            health,
            "launchpad_share_history",
            plat["display_share_history"],
            label="Launchpad fee share (historical)",
            source="defillama",
            note=(
                "DefiLlama Launchpad dailyFees · ATH Sep / Jan / June ATL / Aug 10 dated points. "
                "Live 24h share is the separate metric above — not the Aug-10 figure."
            ),
            epistemic="KNOWN",
        )
    if plat.get("display_fee_context"):
        _patch_metric(
            health,
            "platform_fee_history",
            plat["display_fee_context"],
            label="Fees / revenue / buyback (historical)",
            source="defillama",
            note="15d means around ATH Sep, Jan high, June ATL, and latest window — not causation proof.",
            epistemic="KNOWN",
        )

    sd = doc.get("forensics", {}).get("split_display") or {}
    if funding.get("display"):
        sd["funding_context"] = funding["display"]
    doc.setdefault("forensics", {})["split_display"] = sd


def _knowledge_census_pump(
    forensics_ev: dict,
    wf: dict,
    rs_btc: dict,
    rs_sol: dict,
    deriv: dict,
    health_metrics: list[dict] | None = None,
    buyer: dict | None = None,
    stage1: dict | None = None,
) -> dict:
    unlock = forensics_ev.get("unlock_schedule_sources", {})
    aug = unlock.get("august_reconciliation", {})
    known, inferred, unknown = [], [], []

    hm = {m.get("metric_id"): m for m in (health_metrics or [])}
    if hm.get("platform_revenue", {}).get("data_status") == "LIVE":
        known.append(f"Platform revenue {hm['platform_revenue'].get('value')} ({hm['platform_revenue'].get('note', 'DefiLlama')}).")
    if hm.get("buyback_burn", {}).get("data_status") == "LIVE":
        known.append(f"Buyback/burn {hm['buyback_burn'].get('value')} ({hm['buyback_burn'].get('note', 'DefiLlama')}).")
    if hm.get("launchpad_share", {}).get("data_status") == "LIVE":
        known.append(f"Launchpad fee share {hm['launchpad_share'].get('value')}.")

    if deriv.get("fut_spot_vol_ratio"):
        known.append(
            f"Binance spot ${deriv['spot_vol_24h_usd'] / 1e6:.1f}M vs futures "
            f"${deriv['fut_vol_24h_usd'] / 1e6:.1f}M ({deriv['fut_spot_vol_ratio']:.1f}×)."
        )
    if rs_btc.get("change_30d_pct") is not None and rs_sol.get("change_30d_pct") is not None:
        known.append(f"PUMP/BTC + PUMP/SOL RS strong ({fmt_rs_line(rs_btc)} / {fmt_rs_line(rs_sol)}).")

    inferred.append("Rally shows strong relative strength on PUMP/BTC and PUMP/SOL.")
    inferred.append("Leverage participation is elevated (futures volume well above spot).")
    from lib.v3.pump_forensics_loader import buyer_evidence_label

    buyer_label = buyer_evidence_label(wf, buyer)
    if buyer_label in ("MIXED", "INCONCLUSIVE", "LEVERAGE-LED"):
        inferred.append("Buyer quality not yet established — DEX attribution incomplete.")
    elif buyer_label == "ACCUMULATION SIGNAL":
        inferred.append("Some DEX net accumulators holding in principal-pool sample.")

    unknown.append("Who is actually driving/buying this rally — highest priority.")
    from lib.v3.pump_forensics_loader import load_july_attribution

    july_attr = load_july_attribution() or (
        (forensics_ev.get("july_attribution") if isinstance(forensics_ev, dict) else None) or {}
    )
    own = july_attr.get("ownership_buyer_quality") or {}
    if july_attr.get("pct") or own:
        p = july_attr.get("pct") or {}
        known.append(
            own.get("supply_evidence")
            or (
                "July Streamflow cohort already fully unlocked into Squads custody. "
                f"~{p.get('DEX_SWAP', 0):.2f}% observed DEX swaps; "
                f"{p.get('CEX_DEPOSIT', 0):.2f}% labelled CEX deposit."
            )
        )
        wm = own.get("wintermute_otc") or {}
        if wm.get("outflow_to_wintermute_tokens"):
            known.append(
                f"Large unattributed holder transferred ~{wm['outflow_to_wintermute_tokens'] / 1e6:.0f}M "
                "PUMP to labelled Wintermute OTC."
            )
        inferred.append(
            own.get("supply_interpretation")
            or (
                "Supply overhang is controlled through already-unlocked multisigs rather than "
                "future Streamflow vesting."
            )
        )
        if wm.get("interpretation"):
            inferred.append(
                "Some large-holder inventory is reaching an OTC/MM counterparty. "
                + (wm.get("discipline") or "OTC INTERACTION ≠ SALE")
            )
        bq = own.get("buyer_quality") or {}
        if bq.get("display"):
            inferred.append(
                f"Observed DEX buying reads {bq['display']} — not strong/persistent accumulators."
            )
        unknown.append("Who controls the Squads vaults?")
        unknown.append("When will those vaults distribute?")
        if wm:
            unknown.append(
                "Was the Wintermute OTC flow a sale, inventory transfer or settlement?"
            )
            if wm.get("current_balance_pump"):
                unknown.append(
                    f"What is the source of the ~{wm['current_balance_pump'] / 1e9:.2f}B wallet inventory?"
                )
    else:
        unknown.append("Final destination of July cohort supply (trace partial).")
    if stage1:
        fund = stage1.get("funding") or {}
        if fund.get("wording"):
            known.append(fund["wording"])
        sup = stage1.get("supply") or {}
        if sup.get("display_full"):
            known.append(sup["display_full"])
        plat = stage1.get("platform") or {}
        if plat.get("display_share_history"):
            known.append(plat["display_share_history"])
        if plat.get("display_fee_context"):
            known.append(plat["display_fee_context"])
        if plat.get("interpretation"):
            inferred.append(plat["interpretation"])
        stress = stage1.get("stress") or {}
        if stress.get("wording"):
            inferred.append(stress["wording"])
        for gap in stage1.get("gaps_documented") or []:
            unknown.append(gap)
        aug_s1 = sup.get("august_discrepancy") or {}
        if aug_s1.get("tokenomics_b") is not None and aug_s1.get("defillama_b") is not None:
            unknown.append(
                f"August unlock schedule discrepancy: Tokenomics {aug_s1['tokenomics_b']}B vs "
                f"DefiLlama {aug_s1['defillama_b']}B — SCHEDULED ≠ DISTRIBUTED."
            )
    elif aug.get("tokenomics_amount_tokens") or aug.get("defillama_total_tokens"):
        unknown.append(
            f"Exact August unlock discrepancy if unresolved "
            f"(Tokenomics {_fmt_b(aug.get('tokenomics_amount_tokens', 0))} vs "
            f"DefiLlama {_fmt_b(aug.get('defillama_total_tokens', 0))})."
        )
    return {"known": known, "inferred": inferred, "unknown": unknown}


def _falsifiers_pump(
    forensics_ev: dict,
    wf: dict,
    rs_btc: dict,
    rs_sol: dict,
    deriv: dict,
    buyer: dict | None = None,
    health_metrics: list[dict] | None = None,
    stage1: dict | None = None,
) -> dict:
    from lib.v3.change_mind import build_pump_change_mind

    return build_pump_change_mind(
        forensics_ev=forensics_ev,
        wf=wf,
        rs_btc=rs_btc,
        rs_sol=rs_sol,
        deriv=deriv,
        buyer=buyer,
        health_metrics=health_metrics,
        stage1=stage1,
    )


def _pump_confirmation_stage(
    rs_btc: dict,
    rs_sol: dict,
    deriv: dict,
    health_metrics: list[dict],
    wf: dict,
    buyer: dict | None = None,
) -> tuple[str, int, str]:
    """Return (active_stage_id, active_index 0-based, ring_label) for capital confirmation path."""
    from lib.v3.pump_forensics_loader import buyer_evidence_label

    hm = {m.get("metric_id"): m for m in health_metrics}
    econ_ok = hm.get("platform_revenue", {}).get("data_status") == "LIVE"
    rs_ok = (
        rs_btc.get("change_30d_pct") is not None
        and rs_btc["change_30d_pct"] > 0
        and rs_sol.get("change_30d_pct") is not None
        and rs_sol["change_30d_pct"] > 0
    )
    fut_ratio = deriv.get("fut_spot_vol_ratio") or 0
    spot_heavy = fut_ratio > 5
    buyer_label = buyer_evidence_label(wf, buyer)
    buyers_confirmed = buyer_label in ("ACCUMULATION SIGNAL", "MIXED") and buyer is not None
    if buyers_confirmed and buyer_label == "ACCUMULATION SIGNAL":
        return "buyer_confirmation", 3, "BUYERS"
    if spot_heavy and rs_ok:
        return "spot_confirmation", 2, "SPOT CHECK"
    if not rs_ok and econ_ok:
        return "relative_leadership", 1, "RS CHECK"
    if not econ_ok:
        return "platform_health", 0, "PLATFORM"
    if rs_ok and not spot_heavy:
        return "spot_confirmation", 2, "SPOT CHECK"
    return "relative_leadership", 1, "RS CHECK"


def _warning_stack_pump_forensics(
    forensics_ev: dict,
    wf: dict,
    rs_btc: dict,
    rs_sol: dict,
    deriv: dict,
    health_metrics: list[dict] | None = None,
    buyer: dict | None = None,
) -> dict:
    from lib.v3.pump_forensics_loader import buyer_evidence_detail, buyer_evidence_label

    beh = wf.get("july_recipient_behaviour", {})
    moved_n = beh.get("MOVED_DESTINATION_UNKNOWN", {}).get("count", 0)
    hm = {m.get("metric_id"): m for m in (health_metrics or [])}
    categories = []
    categories.append(technical_trend_category("pump"))

    from lib.v3.pump_forensics_loader import load_july_attribution

    july_attr = load_july_attribution() or {}
    own = july_attr.get("ownership_buyer_quality") or {}
    if july_attr.get("pct") or own:
        p = july_attr.get("pct") or {}
        supply_detail = (
            (own.get("supply_evidence") or july_attr.get("headline_full") or "")
            + " "
            + (
                (own.get("wintermute_otc") or {}).get("evidence")
                or ""
            )
            + " TRANSFER ≠ SALE · CEX DEPOSIT ≠ SALE · custody ≠ sale · OTC INTERACTION ≠ SALE."
        ).strip()
        supply_summary = (
            own.get("headline_compact")
            or july_attr.get("headline_compact")
            or "52B unlocked · OTC flow observed"
        )
    else:
        supply_detail = (
            f"Jul cohort: {moved_n}/80 wallets emptied; destination largely UNKNOWN."
            if moved_n
            else "Jul cohort supply movement not fully traced."
        )
        supply_summary = (
            f"{moved_n}/80 emptied · destination unknown"
            if moved_n
            else "Supply path incomplete"
        )
    categories.append(
        category_state(
            "supply_distribution",
            "SUPPLY / DISTRIBUTION",
            "PARTIAL",
            detail=supply_detail,
            summary=supply_summary,
            impl_status="PRODUCTION_READY",
        )
    )

    buyer_label = buyer_evidence_label(wf, buyer)
    bq = (own.get("buyer_quality") if own else None) or {}
    buyer_st = "PARTIAL" if buyer_label in ("INCONCLUSIVE", "MIXED") else "UNKNOWN"
    if buyer_label == "ACCUMULATION SIGNAL":
        buyer_st = "CLEAR"
    if bq.get("display"):
        buyer_st = "PARTIAL"
        buyer_summary = "REAL BUYING · TRADER-HEAVY"
        buyer_detail = bq.get("evidence") or buyer_evidence_detail(buyer)
    elif buyer_st == "CLEAR":
        buyer_summary = "Real DEX buying · holding checked"
        buyer_detail = buyer_evidence_detail(buyer)
    elif buyer_st == "PARTIAL":
        buyer_summary = "Real DEX buying · quality unresolved"
        buyer_detail = buyer_evidence_detail(buyer)
    else:
        buyer_summary = "Buyer quality unknown"
        buyer_detail = buyer_evidence_detail(buyer)
    categories.append(
        category_state(
            "buyer_quality",
            "BUYER / FLOW QUALITY",
            buyer_st,
            detail=buyer_detail,
            summary=buyer_summary,
            impl_status="PRODUCTION_READY",
        )
    )

    fut_ratio = deriv.get("fut_spot_vol_ratio")
    if fut_ratio and fut_ratio > 5:
        lev_st = "PARTIAL"
        lev_detail = f"Futures {fut_ratio:.1f}× spot · OI ${deriv.get('oi_notional_usd', 0) / 1e6:.1f}M."
        lev_summary = f"Futures {fut_ratio:.1f}× spot"
    elif fut_ratio:
        lev_st = "CLEAR"
        lev_detail = f"Futures {fut_ratio:.1f}× spot."
        lev_summary = f"Futures {fut_ratio:.1f}× spot"
    else:
        lev_st, lev_detail, lev_summary = "UNKNOWN", "Derivatives snapshot missing.", "Derivatives missing"
    categories.append(
        category_state(
            "spot_vs_leverage",
            "SPOT VS LEVERAGE",
            lev_st,
            detail=lev_detail,
            summary=lev_summary,
        )
    )

    rev = hm.get("platform_revenue", {})
    buy = hm.get("buyback_burn", {})
    if rev.get("data_status") == "LIVE" and buy.get("data_status") == "LIVE":
        burn_disp = str(buy.get("value", "")).replace(" burned", "")
        econ_st = "CLEAR"
        econ_detail = f"Revenue {rev.get('value')} · burn {burn_disp}."
        rev_short = str(rev.get("value", "")).replace("/wk", "")
        burn_short = burn_disp.replace("/wk", "")
        econ_summary = f"{rev_short} rev · {burn_short} burn"
    else:
        econ_st, econ_detail, econ_summary = (
            "UNKNOWN",
            "Platform economics not wired this run.",
            "Economics not wired",
        )
    categories.append(
        category_state(
            "platform_economics",
            "PLATFORM ECONOMICS",
            econ_st,
            detail=econ_detail,
            summary=econ_summary,
        )
    )

    share = hm.get("launchpad_share", {})
    dex = hm.get("dex_liquidity_usd", {})
    if share.get("data_status") == "LIVE" and dex.get("data_status") == "LIVE":
        liq_st = "CLEAR"
        liq_detail = f"Launchpad share {share.get('value')} · DEX liquidity {dex.get('value')}."
        liq_summary = f"{share.get('value')} share · {dex.get('value')} liquidity"
    elif share.get("data_status") == "LIVE":
        liq_st = "PARTIAL"
        liq_detail = f"Launchpad share {share.get('value')}."
        liq_summary = f"{share.get('value')} share"
    elif dex.get("data_status") == "LIVE":
        liq_st = "PARTIAL"
        liq_detail = f"DEX liquidity {dex.get('value')}."
        liq_summary = f"{dex.get('value')} liquidity"
    else:
        liq_st, liq_detail, liq_summary = "UNKNOWN", "Share and liquidity not wired.", "Share/liquidity missing"
    categories.append(
        category_state(
            "market_share_liquidity",
            "MARKET SHARE / LIQUIDITY",
            liq_st,
            detail=liq_detail,
            summary=liq_summary,
        )
    )

    return pack_risk_confirmation(categories, "PUMP Stage-1 evidence")


def _pump_health_triad_detail(metrics: list[dict]) -> str:
    by_id = {m.get("metric_id"): m for m in metrics}
    rev = by_id.get("platform_revenue", {})
    buy = by_id.get("buyback_burn", {})
    if rev.get("data_status") == "LIVE" and buy.get("data_status") == "LIVE":
        return f"{rev.get('value')} revenue · {buy.get('value')}"
    if rev.get("data_status") == "LIVE":
        return f"{rev.get('value')} revenue"
    return "Revenue / buyback UNKNOWN"


def _patch_metric(metrics: list[dict], metric_id: str, value: str, **kwargs) -> None:
    for m in metrics:
        if m.get("metric_id") == metric_id:
            m["value"] = value
            m["data_status"] = "LIVE"
            m["epistemic_status"] = kwargs.get("epistemic", "KNOWN")
            m["implementation_status"] = kwargs.get("impl", "PRODUCTION_READY")
            if "note" in kwargs:
                m["note"] = kwargs["note"]
            if kwargs.get("source"):
                m["source"] = kwargs["source"]
            if kwargs.get("source_url"):
                m["source_url"] = kwargs["source_url"]
            if kwargs.get("fetched_at"):
                m["fetched_at"] = kwargs["fetched_at"]
            return
    metrics.append(
        field(
            metric_id,
            kwargs.get("label", metric_id),
            value,
            source=kwargs.get("source", "pump-forensics"),
            source_url=kwargs.get("source_url"),
            fetched_at=kwargs.get("fetched_at"),
            note=kwargs.get("note"),
        )
    )


# Public pages already used in live PUMP product — fill production-facing gaps only.
_PUMP_SOURCE_URL_BY_SOURCE = {
    "coingecko/dex": "https://www.coingecko.com/en/coins/pump-fun",
    "coingecko": "https://www.coingecko.com/en/coins/pump-fun",
    "pump.fun": "https://pump.fun",
    "defillama": "https://defillama.com/protocol/fees/pump.fun",
    "binance-daily": "https://api.binance.com/api/v3/klines?symbol=PUMPUSDT&interval=1d",
    "binance": "https://www.binance.com/en/futures/PUMPUSDT",
    "wallet-forensics": "https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
    "dexscreener": "https://dexscreener.com/solana/2uf4xh61rdwxng9woyxsvqp7zua6klfpb3nvnrqeoisd",
}


def _fill_pump_production_source_urls(doc: dict, evidence: dict | None = None) -> None:
    """Populate missing source_url on production-facing PUMP nodes from known public pages."""
    dex_url = ((evidence or {}).get("pump_evidence") or {}).get("dex_liquidity", {}).get("url")
    source_map = dict(_PUMP_SOURCE_URL_BY_SOURCE)
    if dex_url:
        source_map["dexscreener"] = dex_url

    for section in ("project_health", "market_timing"):
        for m in (doc.get(section) or {}).get("metrics") or []:
            if m.get("source_url"):
                continue
            src = m.get("source")
            if src in source_map:
                m["source_url"] = source_map[src]
            if not m.get("as_of") and m.get("fetched_at"):
                m["as_of"] = m["fetched_at"]

    for _pair_id, rs in (doc.get("relative_strength") or {}).items():
        if not isinstance(rs, dict):
            continue
        if not rs.get("source_url"):
            src = rs.get("source")
            if src in source_map:
                rs["source_url"] = source_map[src]
        if not rs.get("freshness") and (rs.get("fetched_at") or rs.get("data_status")):
            rs["freshness"] = rs.get("data_status") or "as_of-dated"


def _apply_pump_forensics(
    doc: dict,
    forensics: dict,
    evidence: dict,
    buyer_forensics: dict | None = None,
) -> None:
    from lib.v3.pump_forensics_loader import (
        buyer_evidence_detail,
        buyer_evidence_label,
        buyer_forensics_evidence_path,
        forensics_evidence_pack_path,
        fmt_rs_line,
        rs_from_forensics_snapshot,
    )

    forensics_ev = forensics.get("evidence", forensics)
    wf = forensics_ev.get("wallet_forensics") or {}
    rec = wf.get("july_distribution_reconciliation") or {}
    beh = wf.get("july_recipient_behaviour") or {}
    dest = wf.get("july_cohort_destination_trace") or {}
    deriv = forensics_ev.get("derivatives_snapshot") or {}
    unlock = forensics_ev.get("unlock_schedule_sources") or {}
    aug = unlock.get("august_reconciliation") or {}
    rally = forensics_ev.get("rally_quality_verdict") or {}

    from lib.v3.pump_forensics_loader import load_july_attribution

    july_attr = load_july_attribution()

    rs_btc, rs_sol = rs_from_forensics_snapshot(forensics)
    doc["relative_strength"]["pump_btc"] = rs_btc
    doc["relative_strength"]["pump_sol"] = rs_sol

    doc["forensics"] = {
        "snapshot_id": forensics.get("snapshot_id"),
        "gathered_at": forensics.get("gathered_at"),
        "evidence_pack_path": forensics_evidence_pack_path(forensics),
        "july_reconciliation": rec,
        "july_behaviour": beh,
        "destination_trace": dest,
        "july_attribution": july_attr,
        "derivatives": deriv,
        "august_unlock": aug,
        "rally_quality": rally,
        "swap_net_buyers": wf.get("swap_net_buyers"),
        "repeat_player_summary": wf.get("repeat_player_summary"),
        "important_flows": wf.get("important_flows"),
        "post_july_distributor_activity": wf.get("post_july_distributor_activity"),
    }
    # Also expose on forensics_ev-shaped path for census helpers that receive forensics_ev
    if july_attr:
        forensics_ev["july_attribution"] = july_attr
    if buyer_forensics:
        from lib.v3.pump_forensics_loader import buyer_observed_window

        ow = buyer_observed_window(buyer_forensics)
        doc["forensics"]["buyer_forensics"] = {
            "snapshot_id": buyer_forensics.get("snapshot_id"),
            "gathered_at": buyer_forensics.get("gathered_at"),
            "verdict": (buyer_forensics.get("verdict_block") or {}).get("verdict"),
            "verdict_detail": (buyer_forensics.get("verdict_block") or {}).get("detail"),
            "channel_read": (buyer_forensics.get("verdict_block") or {}).get("channel_read"),
            "retrieval_span": buyer_forensics.get("retrieval_span"),
            "observed_window": ow,
            "windows": buyer_forensics.get("windows"),
            "wallet_profiles_checked": buyer_forensics.get("wallet_profiles_checked"),
            "evidence_report_path": buyer_forensics_evidence_path(buyer_forensics),
        }

    timing = doc["market_timing"]["metrics"]
    fut_ratio = deriv.get("fut_spot_vol_ratio")
    buyer_label = buyer_evidence_label(wf, buyer_forensics)

    _patch_metric(
        timing,
        "pump_btc",
        fmt_rs_line(rs_btc),
        label="PUMP / BTC",
        source="binance-daily",
        source_url="https://api.binance.com/api/v3/klines?symbol=PUMPUSDT&interval=1d",
        note="Rolling RS from forensics snapshot daily closes.",
    )
    _patch_metric(
        timing,
        "pump_sol",
        fmt_rs_line(rs_sol),
        label="PUMP / SOL",
        source="binance-daily",
        source_url="https://api.binance.com/api/v3/klines?symbol=PUMPUSDT&interval=1d",
        note="Rolling RS from forensics snapshot daily closes.",
    )
    if deriv:
        _patch_metric(
            timing,
            "spot_perp",
            f"{deriv['fut_spot_vol_ratio']:.1f}× futures/spot",
            label="Spot vs leverage",
            source="binance",
            source_url="https://www.binance.com/en/futures/PUMPUSDT",
            note=(
                f"spot ${deriv['spot_vol_24h_usd'] / 1e6:.1f}M · "
                f"fut ${deriv['fut_vol_24h_usd'] / 1e6:.1f}M"
            ),
        )
        oi_mcap = ""
        if deriv.get("oi_notional_usd") and evidence.get("pump_evidence", {}).get("price", {}).get("market_cap"):
            mcap = evidence["pump_evidence"]["price"]["market_cap"]
            if mcap:
                oi_mcap = f" · OI/mcap ~{100 * deriv['oi_notional_usd'] / mcap:.1f}%"
        _patch_metric(
            timing,
            "oi_funding",
            f"OI ${deriv['oi_notional_usd'] / 1e6:.1f}M · funding {deriv.get('funding_rate_8h', 0):.5f}/8h{oi_mcap}",
            label="OI / funding",
            source="binance",
            source_url="https://www.binance.com/en/futures/PUMPUSDT",
            note="Binance futures open interest and funding from forensics snapshot.",
        )
    _patch_metric(
        timing,
        "buyer_evidence",
        buyer_label,
        label="Buyer / flow quality",
        source="wallet-forensics",
        source_url="https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
        note="Principal-pool SWAP sample · observed retrieval span only (not 14d).",
    )

    doc["forensics"]["split_display"] = {
        "pump_btc": fmt_rs_line(rs_btc),
        "pump_sol": fmt_rs_line(rs_sol),
        "fut_spot": f"{fut_ratio:.1f}× futures/spot" if fut_ratio else "UNKNOWN",
        "oi_funding": (
            f"OI ${deriv['oi_notional_usd'] / 1e6:.1f}M · funding {deriv.get('funding_rate_8h', 0):.5f}/8h"
            if deriv.get("oi_notional_usd")
            else ""
        ),
        "buyer_evidence": buyer_label,
    }

    pump_ev = evidence.get("pump_evidence") or {}
    dex = pump_ev.get("dex_liquidity") or {}
    if dex.get("liquidity_usd"):
        health = doc["project_health"]["metrics"]
        _patch_metric(
            health,
            "dex_liquidity_usd",
            f"${dex['liquidity_usd'] / 1e6:.1f}M",
            label="DEX liquidity (best pool)",
            source="dexscreener",
            source_url=dex.get("url")
            or "https://dexscreener.com/solana/2uf4xh61rdwxng9woyxsvqp7zua6klfpb3nvnrqeoisd",
            note="DexScreener best pool by liquidity.",
        )

    moved_n = beh.get("MOVED_DESTINATION_UNKNOWN", {}).get("count", 0)
    july_attr = doc["forensics"].get("july_attribution") or {}
    buyer_label = buyer_evidence_label(wf, buyer_forensics)
    fut_ratio = deriv.get("fut_spot_vol_ratio")
    capital_display = "INCONCLUSIVE"
    if buyer_label == "MIXED":
        capital_display = "MIXED"
    elif buyer_label == "ACCUMULATION SIGNAL":
        capital_display = "PARTIAL SIGNAL"

    doc["triad"].pop("supply_unlock", None)
    capital_detail = "RS strong · leverage heavy · buyer attribution incomplete"
    if buyer_forensics:
        from lib.v3.pump_forensics_loader import buyer_observed_window

        ow = buyer_observed_window(buyer_forensics)
        net_n = ow.get("net_accumulator_count", 0)
        hold_claim = ow.get("holding_claim") or "balances partially checked"
        span_h = ow.get("span_hours")
        span_bit = f"~{span_h:.0f}h observed" if span_h is not None else "observed span"
        capital_detail = (
            f"RS strong · leverage heavy · {net_n} net DEX buyers in {span_bit} · {hold_claim}"
        )
    doc["triad"]["capital_entry"] = {
        "display": capital_display,
        "detail": capital_detail,
        "implementation_status": "PRODUCTION_READY",
    }
    # Reconcile top-level capital_entry with triad (remove stale UNKNOWN/not-wired)
    doc["capital_entry"] = {
        "display_state": capital_display,
        "detail": capital_detail,
        "implementation_status": "PRODUCTION_READY",
        "note": "Principal-pool DEX SWAP sample; CEX buyers unobservable.",
    }
    # Remove stale ai_basket scaffold on PUMP
    doc.get("relative_strength", {}).pop("ai_basket", None)
    doc["triad"]["project_health"] = {
        "display": "Platform operational",
        "detail": _pump_health_triad_detail(doc.get("project_health", {}).get("metrics") or []),
    }
    rs_st = "RS wired" if rs_btc.get("change_30d_pct") is not None else "RS UNKNOWN"
    doc["triad"]["market_timing"] = {
        "display": f"Fut/spot {fut_ratio:.1f}× · {rs_st}" if fut_ratio else rs_st,
        "detail": "Rally quality UNCLASSIFIED — timing from RS, leverage and buyers.",
        "implementation_status": "PRODUCTION_READY",
    }
    doc["triad"].pop("lifecycle", None)

    doc["hero"]["thesis"] = (
        "Who is buying this rally — credible capital accumulation, or mainly speculative / leverage-driven strength?"
    )
    doc["hero"]["v3_posture"] = "UNCLASSIFIED"
    doc["hero"]["v3_posture_note"] = "No approved classifier — posture not invented."
    doc["hero"]["confidence"] = "MEDIUM"
    doc["hero"]["data_completeness"] = ""

    stage_id, active_index, ring_label = _pump_confirmation_stage(
        rs_btc,
        rs_sol,
        deriv,
        doc.get("project_health", {}).get("metrics") or [],
        wf,
        buyer_forensics,
    )
    doc["lifecycle"] = {
        "framework": "capital_confirmation_path",
        "current_stage": stage_id,
        "active_index": active_index,
        "ring_label": ring_label,
        "stages": [
            {"n": 1, "id": "platform_health", "label": "PLATFORM HEALTH"},
            {"n": 2, "id": "relative_leadership", "label": "RELATIVE LEADERSHIP"},
            {"n": 3, "id": "spot_confirmation", "label": "SPOT CONFIRMATION"},
            {"n": 4, "id": "buyer_confirmation", "label": "BUYER CONFIRMATION"},
        ],
        "note": "Explanatory framework — not a proven lifecycle law.",
    }
    if july_attr.get("pct") or july_attr.get("ownership_buyer_quality"):
        p = july_attr.get("pct") or {}
        own_ls = july_attr.get("ownership_buyer_quality") or {}
        doc["liquid_supply"] = {
            "display_state": "PARTIAL",
            "chain_stages": [
                "UNLOCKED",
                "DISTRIBUTED",
                "ALREADY_UNLOCKED_SQUADS_CUSTODY",
                "LIMITED_SELL_EVIDENCE",
            ],
            "implementation_status": "PRODUCTION_READY",
            "note": july_attr.get("headline_who_selling")
            or own_ls.get("who_selling_evidence")
            or (
                f"July cohort already unlocked into Squads custody · "
                f"~{p.get('DEX_SWAP', 0):.2f}% DEX swap upper-bound · "
                f"{p.get('CEX_DEPOSIT', 0):.2f}% labelled CEX. Transfer ≠ sale. custody ≠ sale."
            ),
            "first_hop_context": july_attr.get("first_hop_context"),
            "attribution": july_attr,
        }
    else:
        doc["liquid_supply"] = {
            "display_state": "PARTIAL",
            "chain_stages": ["UNLOCKED", "DISTRIBUTED", "MOVED", "DESTINATION_UNKNOWN"],
            "implementation_status": "PRODUCTION_READY",
            "note": f"{moved_n}/80 Jul cohort wallets emptied. Transfer ≠ sale.",
        }
    doc["spot_vs_leverage"] = {
        "display_state": "PARTIAL" if deriv.get("fut_spot_vol_ratio", 0) > 5 else "UNKNOWN",
        "implementation_status": "PRODUCTION_READY",
        "note": f"Fut/spot {deriv.get('fut_spot_vol_ratio', '—')}× from Binance snapshot.",
    }

    _apply_stage1_evidence(doc)

    from lib.v3.pump_amendment_evidence import load_amendment_evidence

    amd = load_amendment_evidence()
    if amd:
        doc["amendment"] = amd

    from lib.v3.asset_top import build_pump_asset_top

    doc["asset_top"] = build_pump_asset_top(doc)

    doc["knowledge_census"] = _knowledge_census_pump(
        forensics_ev,
        wf,
        rs_btc,
        rs_sol,
        deriv,
        doc.get("project_health", {}).get("metrics"),
        buyer_forensics,
        stage1=doc.get("stage1_evidence"),
    )
    from lib.v3.reality_check import build_pump_reality_check

    doc["reality_check"] = build_pump_reality_check(
        forensics_ev=forensics_ev,
        wf=wf,
        rs_btc=rs_btc,
        rs_sol=rs_sol,
        deriv=deriv,
        buyer=buyer_forensics,
        health_metrics=doc.get("project_health", {}).get("metrics"),
        stage1=doc.get("stage1_evidence"),
    )
    doc["what_would_change_mind"] = _falsifiers_pump(
        forensics_ev,
        wf,
        rs_btc,
        rs_sol,
        deriv,
        buyer_forensics,
        doc.get("project_health", {}).get("metrics"),
        doc.get("stage1_evidence"),
    )
    doc["warning_stack"] = _warning_stack_pump_forensics(
        forensics_ev, wf, rs_btc, rs_sol, deriv, doc.get("project_health", {}).get("metrics"), buyer_forensics
    )
    doc["bullish_stack"] = _bullish_stack_pump(
        rs_btc, rs_sol, doc.get("project_health", {}).get("metrics") or [], wf, deriv, buyer_forensics
    )
    from datetime import datetime, timezone

    doc["meta"]["forensics_snapshot_id"] = forensics.get("snapshot_id")
    doc["meta"]["buyer_forensics_snapshot_id"] = (buyer_forensics or {}).get("snapshot_id")
    doc["meta"]["version"] = "pump-audit-v1-stage1-wired"
    doc["meta"]["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_pump_v3(
    evidence: dict[str, Any],
    market: dict[str, Any],
    report_date: str,
    v4_report: dict | None,
    *,
    forensics: dict[str, Any] | None = None,
    buyer_forensics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doc = build_asset_v3(
        "pump",
        "PUMP",
        evidence,
        market,
        report_date,
        v4_report,
        evidence_key="pump_evidence",
        daily_key="pump",
        thesis=(
            "Who is buying this rally — credible capital accumulation, or mainly speculative / leverage-driven strength?"
        ),
        health_metrics_fn=_health_pump,
        rs_btc_id="pump_btc",
        rs_sol_id="pump_sol",
        ai_basket_note="Meme/platform basket not wired in Phase 1.",
    )
    if forensics:
        _apply_pump_forensics(doc, forensics, evidence, buyer_forensics)
    if not doc.get("asset_top"):
        # Weekly live used to skip forensics → no asset_top → empty ALT chrome → QA FAIL.
        # Stance/ticker must exist even when lifecycle stays UNKNOWN (active_index=None).
        from lib.v3.asset_top import build_pump_asset_top

        doc["asset_top"] = build_pump_asset_top(doc)
    _fill_pump_production_source_urls(doc, evidence)
    return doc

