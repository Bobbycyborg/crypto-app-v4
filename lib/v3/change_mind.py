"""What would change our mind — live evidence conditions (universal ALT shape, PUMP wired)."""

from __future__ import annotations

import re
from typing import Any


STATUSES = frozenset({"YES", "NO", "PARTIAL", "WATCH", "UNKNOWN"})

BINANCE_PUMP_FUT = "https://www.binance.com/en/futures/PUMPUSDT"
BINANCE_PUMP_SPOT = "https://www.binance.com/en/trade/PUMP_USDT"


def condition(
    *,
    condition_id: str,
    title: str,
    summary: str,
    status: str,
    interpretation: str,
    evidence_rows: list[tuple[str, str]] | None = None,
    source: str = "",
    source_url: str | None = None,
    as_of: str | None = None,
    freshness: str | None = None,
    confidence: str = "MEDIUM",
    epistemic_status: str = "PARTIAL",
    icon: str = "up",
) -> dict[str, Any]:
    st = (status or "UNKNOWN").upper()
    if st not in STATUSES:
        st = "UNKNOWN"
    if freshness is None and as_of:
        freshness = "as_of-dated"
    return {
        "id": condition_id,
        "title": title,
        "summary": summary,
        "status": st,
        "interpretation": interpretation,
        "evidence_rows": [{"key": k, "value": v} for k, v in (evidence_rows or []) if v],
        "source": source,
        "source_url": source_url,
        "as_of": as_of,
        "freshness": freshness,
        "confidence": confidence,
        "epistemic_status": epistemic_status,
        "icon": icon,
    }


def empty_change_mind() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "constructive": [],
        "defensive": [],
        "more_constructive": [],
        "more_defensive": [],
    }


def pack_change_mind(
    constructive: list[dict[str, Any]],
    defensive: list[dict[str, Any]],
    *,
    schema_version: int = 2,
) -> dict[str, Any]:
    """Attach list + compact more_* rows. Status vocabulary unchanged."""
    return {
        "schema_version": schema_version,
        "constructive": constructive,
        "defensive": defensive,
        "more_constructive": [
            {"label": c["title"], "detail": c["summary"], "status": c["status"]}
            for c in constructive
        ],
        "more_defensive": [
            {"label": c["title"], "detail": c["summary"], "status": c["status"]}
            for c in defensive
        ],
    }


def _buyer_status(buyer: dict | None, wf: dict | None) -> tuple[str, str, list[tuple[str, str]], str]:
    from lib.v3.pump_forensics_loader import buyer_evidence_label, buyer_observed_window

    label = buyer_evidence_label(wf, buyer)
    ow = buyer_observed_window(buyer)
    net_n = ow.get("net_accumulator_count")
    hold_n = ow.get("holding_among_checked_n")
    hold_claim = ow.get("holding_claim") or ""
    span = ow.get("span_hours")
    top5 = ow.get("top5_gross_buy_share_pct")

    rows: list[tuple[str, str]] = []
    if net_n is not None:
        span_bit = f" in ~{span:.0f}h span" if span is not None else ""
        rows.append(("Observed", f"{net_n} net DEX accumulators{span_bit}"))
    if hold_claim:
        rows.append(("Holding", hold_claim))
    elif hold_n is not None:
        rows.append(("Holding", f"{hold_n} of checked still hold"))
    if top5 is not None:
        rows.append(("Concentration", f"Top-5 gross buy share {top5:.0f}%"))
    rows.append(("Unknown", "Repeat / attributable buyer identity"))

    if label == "ACCUMULATION SIGNAL":
        return (
            "YES",
            "Repeat or attributable buyers keep accumulating.",
            rows,
            "Identifiable accumulation signal present in the sampled window.",
        )
    if label in ("MIXED", "INCONCLUSIVE", "WEAK SAMPLE") and net_n:
        return (
            "PARTIAL",
            "Repeat or attributable buyers keep accumulating.",
            rows,
            "Real DEX buying is present, but buyer quality is not yet established.",
        )
    if label == "LEVERAGE-LED":
        return (
            "NO",
            "Repeat or attributable buyers keep accumulating.",
            rows,
            "Sample reads leverage-led rather than identifiable spot accumulation.",
        )
    if not buyer and not wf:
        return (
            "UNKNOWN",
            "Repeat or attributable buyers keep accumulating.",
            [("Evidence", "Buyer forensics not loaded")],
            "No buyer sample available this run.",
        )
    return (
        "PARTIAL",
        "Repeat or attributable buyers keep accumulating.",
        rows or [("Evidence", "Buyer sample incomplete")],
        "Buyer attribution remains incomplete.",
    )


def _buyer_source_url(buyer: dict | None) -> str | None:
    if not buyer:
        return None
    for w in buyer.get("wallet_profiles_checked") or []:
        links = w.get("sample_explorer_links") or []
        if links:
            return str(links[0])
        url = w.get("sample_explorer")
        if url:
            return str(url)
    return None


def _rs_pair(rs_btc: dict, rs_sol: dict) -> tuple[Any, Any, Any, Any, str | None]:
    return (
        rs_btc.get("change_7d_pct"),
        rs_btc.get("change_30d_pct"),
        rs_sol.get("change_7d_pct"),
        rs_sol.get("change_30d_pct"),
        rs_btc.get("fetched_at") or rs_sol.get("fetched_at"),
    )


def _fmt_pct(v: Any) -> str:
    try:
        return f"{float(v):+.1f}%"
    except (TypeError, ValueError):
        return "—"


def _rs_statuses(
    b7: Any, b30: Any, s7: Any, s30: Any
) -> tuple[str, str, str, str, list[tuple[str, str]]]:
    """Return (constructive_status, constructive_note, defensive_status, defensive_note, rows)."""
    rows = [
        ("vs BTC 7d / 30d", f"{_fmt_pct(b7)} / {_fmt_pct(b30)}"),
        ("vs SOL 7d / 30d", f"{_fmt_pct(s7)} / {_fmt_pct(s30)}"),
    ]
    if any(v is None for v in (b7, b30, s7, s30)):
        return (
            "UNKNOWN",
            "RS series incomplete on 7d or 30d — leadership not classified.",
            "UNKNOWN",
            "Cannot judge RS failure without both 7d and 30d on BTC and SOL.",
            rows + [("Need", "Complete 7d + 30d on both pairs")],
        )

    b7f, b30f, s7f, s30f = float(b7), float(b30), float(s7), float(s30)
    all_pos = b7f > 0 and b30f > 0 and s7f > 0 and s30f > 0
    both_30_pos = b30f > 0 and s30f > 0
    both_30_neg = b30f <= 0 and s30f <= 0
    any_7_neg = b7f <= 0 or s7f <= 0
    both_7_neg = b7f <= 0 and s7f <= 0

    if all_pos:
        return (
            "YES",
            "Both 7d and 30d are supportive versus BTC and SOL.",
            "NO",
            "Relative strength is not failing on 7d or 30d.",
            rows + [("Need", "Leadership persists on both horizons")],
        )

    if both_30_pos and any_7_neg:
        return (
            "WATCH",
            "30d leadership still positive, but 7d has deteriorated on at least one pair.",
            "WATCH",
            "7d RS has rolled over while 30d remains positive — early failure watch.",
            rows + [("Watch", "7d deterioration vs still-positive 30d")],
        )

    if both_30_neg or (both_7_neg and (b30f <= 0 or s30f <= 0)):
        return (
            "NO",
            "Established weakness across horizons versus BTC and/or SOL.",
            "YES",
            "PUMP/BTC or PUMP/SOL leadership is weak across horizons.",
            rows + [("Concern", "USD strength without relative leadership")],
        )

    return (
        "PARTIAL",
        "Mixed leadership across BTC/SOL and 7d/30d horizons.",
        "PARTIAL",
        "RS read is mixed across pairs or horizons.",
        rows,
    )


def _metric_direction(m: dict) -> str:
    """Per-metric direction from that metric's own note only. No combined-string hacks."""
    if (m or {}).get("data_status") != "LIVE":
        return "unknown"
    note = str(m.get("note") or "")
    nlow = note.lower()
    has_compare = any(tok in nlow for tok in ("prior", "wow", "w/w", "vs prior", "vs "))
    if re.search(r"\+\d+(?:\.\d+)?%", note) and has_compare:
        return "up"
    if re.search(r"-\d+(?:\.\d+)?%", note) and has_compare:
        return "down"
    if m.get("value") is not None:
        return "flat"
    return "unknown"


def _platform_econ_status(
    rev: dict, burn: dict, share: dict
) -> tuple[str, str, list[tuple[str, str]]]:
    pieces = [
        ("Revenue", rev),
        ("Buyback / burn", burn),
        ("Launchpad share", share),
    ]
    rows: list[tuple[str, str]] = []
    dirs: list[str] = []
    for label, m in pieces:
        direction = _metric_direction(m)
        dirs.append(direction)
        if m.get("value") is not None:
            rows.append((label, f"{m.get('value')} · {direction}"))
        elif direction == "unknown":
            rows.append((label, "unavailable"))

    live = [d for d in dirs if d != "unknown"]
    if not live:
        return "UNKNOWN", "Platform economics not wired this run.", rows or [("Evidence", "Not wired")]

    if all(d == "up" for d in live) and len(live) >= 2:
        return (
            "YES",
            "Revenue, buyback/burn and available activity reads are each supportive.",
            rows,
        )
    if any(d == "up" for d in live) and any(d in ("flat", "down", "unknown") for d in dirs):
        return (
            "PARTIAL",
            "Mixed platform-economics direction across revenue, burn and share.",
            rows,
        )
    if all(d == "up" for d in live):
        return "YES", "Available platform-economics reads are supportive.", rows
    if any(d == "down" for d in live):
        return "PARTIAL", "At least one platform metric is deteriorating.", rows
    return "PARTIAL", "Live platform metrics lack clear directional confirmation.", rows


def _leverage_watch_status(
    fut: Any, fund_disp: str, fund_pct: Any, fund_word: str
) -> tuple[str, str, str, str]:
    """No unvalidated fut/spot cutoff. Observe only → WATCH or UNKNOWN."""
    if fut is None and not fund_disp:
        return (
            "UNKNOWN",
            "Derivatives / funding snapshot missing — cannot judge spot vs leverage.",
            "UNKNOWN",
            "Cannot judge leverage vs spot without derivatives evidence.",
        )

    bits = []
    if fut is not None:
        bits.append(f"futures/spot {float(fut):.1f}× observed")
    if fund_disp:
        bits.append(fund_disp)
    observed = "; ".join(bits) if bits else "partial derivatives evidence"

    # Cold funding is context, not a classifier. No ratio cutoff.
    cons_note = (
        f"Watching spot vs derivatives ({observed}). "
        "No validated leverage cutoff — not classified as improved spot leadership."
    )
    def_note = (
        f"Watching whether derivatives outrun spot ({observed}). "
        "High futures/spot alone is not treated as proven danger; funding context noted, threshold not invented."
    )
    if fund_word:
        cons_note = f"{cons_note} {fund_word}"
        def_note = f"{def_note} {fund_word}"
    return "WATCH", cons_note, "WATCH", def_note


def build_pump_change_mind(
    *,
    forensics_ev: dict,
    wf: dict,
    rs_btc: dict,
    rs_sol: dict,
    deriv: dict,
    buyer: dict | None,
    health_metrics: list[dict] | None = None,
    stage1: dict | None = None,
) -> dict[str, Any]:
    """PUMP-specific constructive / defensive conditions from live evidence."""
    from lib.v3.pump_forensics_loader import buyer_evidence_label

    hm = {m.get("metric_id"): m for m in (health_metrics or [])}
    stage1 = stage1 or {}
    funding = stage1.get("funding") or {}
    supply_stage = stage1.get("supply") or {}
    beh = (wf or {}).get("july_recipient_behaviour") or {}
    moved_n = (beh.get("MOVED_DESTINATION_UNKNOWN") or {}).get("count", 0)

    out = empty_change_mind()
    b7, b30, s7, s30, rs_as_of = _rs_pair(rs_btc, rs_sol)
    buyer_st, buyer_sum, buyer_rows, buyer_note = _buyer_status(buyer, wf)
    buyer_as = (buyer or {}).get("gathered_at") or rs_as_of
    buyer_label = buyer_evidence_label(wf, buyer)
    buyer_url = _buyer_source_url(buyer)

    # --- Constructive ---
    out["constructive"].append(
        condition(
            condition_id="identifiable_spot_buyers",
            title="Identifiable net spot buyers",
            summary=buyer_sum,
            status=buyer_st,
            interpretation=buyer_note,
            evidence_rows=buyer_rows,
            source="Helius / Solana DEX sample",
            source_url=buyer_url,
            as_of=buyer_as,
            confidence="MEDIUM" if buyer_st != "UNKNOWN" else "LOW",
            epistemic_status="PARTIAL" if buyer_st == "PARTIAL" else ("KNOWN" if buyer_st == "YES" else "UNKNOWN"),
            icon="up",
        )
    )

    rs_st, rs_note, fail_st, fail_note, rs_rows = _rs_statuses(b7, b30, s7, s30)
    out["constructive"].append(
        condition(
            condition_id="sustained_relative_strength",
            title="Sustained BTC + SOL leadership",
            summary="PUMP keeps outperforming both benchmark assets.",
            status=rs_st,
            interpretation=rs_note,
            evidence_rows=rs_rows,
            source=rs_btc.get("source") or "binance-daily",
            source_url=BINANCE_PUMP_SPOT,
            as_of=rs_as_of,
            confidence="MEDIUM" if rs_st != "UNKNOWN" else "LOW",
            epistemic_status="KNOWN" if rs_st == "YES" else "PARTIAL",
            icon="up",
        )
    )

    fut = deriv.get("fut_spot_vol_ratio")
    oi = deriv.get("oi_notional_usd")
    fund_disp = funding.get("display") or ""
    fund_pct = funding.get("percentile_vs_binance_history")
    fund_word = funding.get("wording") or ""
    lev_rows: list[tuple[str, str]] = []
    if fut is not None:
        lev_rows.append(("Futures / spot", f"{float(fut):.1f}× (observed — no cutoff)"))
    if oi:
        lev_rows.append(("OI", f"${float(oi) / 1e6:.1f}M"))
    if fund_disp:
        lev_rows.append(("Funding", fund_disp))
    if fund_pct is not None:
        lev_rows.append(("Funding pctile", f"{float(fund_pct):.1f}th vs own history"))
    lev_rows.append(("Rule", "No unvalidated futures/spot threshold"))

    spot_st, spot_note, lev_def_st, lev_def_note = _leverage_watch_status(
        fut, fund_disp, fund_pct, fund_word
    )
    lev_as = deriv.get("gathered_at") or funding.get("latest_time") or rs_as_of
    out["constructive"].append(
        condition(
            condition_id="spot_vs_leverage_quality",
            title="More spot, less leverage dependence",
            summary="Spot participation improves versus derivatives.",
            status=spot_st,
            interpretation=spot_note,
            evidence_rows=lev_rows,
            source="Binance",
            source_url=BINANCE_PUMP_FUT,
            as_of=lev_as,
            confidence="LOW" if spot_st == "UNKNOWN" else "MEDIUM",
            epistemic_status="PARTIAL",
            icon="lev",
        )
    )

    rev = hm.get("platform_revenue") or {}
    burn = hm.get("buyback_burn") or {}
    share = hm.get("launchpad_share") or {}
    econ_st, econ_interp, econ_rows = _platform_econ_status(rev, burn, share)
    econ_url = rev.get("source_url") or burn.get("source_url") or share.get("source_url")
    out["constructive"].append(
        condition(
            condition_id="platform_economics",
            title="Platform economics keep improving",
            summary="Revenue, buybacks and activity remain supportive.",
            status=econ_st,
            interpretation=econ_interp,
            evidence_rows=econ_rows,
            source="Pump.fun / DefiLlama",
            source_url=econ_url,
            as_of=rev.get("fetched_at") or burn.get("fetched_at") or rs_as_of,
            confidence="MEDIUM" if econ_st != "UNKNOWN" else "LOW",
            epistemic_status="KNOWN" if econ_st == "YES" else "PARTIAL",
            icon="bars",
        )
    )

    # --- Defensive ---
    out["defensive"].append(
        condition(
            condition_id="relative_strength_failure",
            title="Relative strength starts failing",
            summary="PUMP/BTC or PUMP/SOL leadership weakens.",
            status=fail_st,
            interpretation=fail_note,
            evidence_rows=rs_rows,
            source=rs_btc.get("source") or "binance-daily",
            source_url=BINANCE_PUMP_SPOT,
            as_of=rs_as_of,
            confidence="MEDIUM" if fail_st != "UNKNOWN" else "LOW",
            epistemic_status="KNOWN" if fail_st in ("YES", "NO") else "PARTIAL",
            icon="warn",
        )
    )

    from lib.v3.pump_forensics_loader import load_july_attribution

    july_attr = load_july_attribution() or ((forensics_ev or {}).get("july_attribution") or {})
    own = july_attr.get("ownership_buyer_quality") or {}
    mint_url = (supply_stage or {}).get("mint_explorer")
    if july_attr.get("pct") or own:
        p = july_attr.get("pct") or {}
        wm = own.get("wintermute_otc") or {}
        supply_st = "PARTIAL"
        supply_note = (
            own.get("who_selling_evidence")
            or (
                f"{p.get('CEX_DEPOSIT', 0):.2f}% of July cohort reached a labelled Bybit hot wallet. "
                "Deposit ≠ sale. Most traced supply is already-unlocked Squads custody."
            )
        )
        supply_rows = [
            ("July unlocked", "~52.04B into Squads (Streamflow escrow ~0)"),
            ("Labelled CEX deposit", f"{p.get('CEX_DEPOSIT', 0):.2f}% (Bybit hot · deposit ≠ sale)"),
            ("Observed DEX swap", f"~{p.get('DEX_SWAP', 0):.2f}% upper bound"),
            ("Unattributed held", f"{p.get('STILL_HELD', 0):.2f}%"),
            ("UNKNOWN", f"{p.get('UNKNOWN', 0):.2f}%"),
            ("Rule", "TRANSFER ≠ SALE · CEX DEPOSIT ≠ SALE · custody ≠ sale · OTC INTERACTION ≠ SALE"),
        ]
        if wm.get("outflow_to_wintermute_tokens"):
            supply_rows.insert(
                1,
                (
                    "Wintermute OTC",
                    f"~{wm['outflow_to_wintermute_tokens'] / 1e6:.0f}M observed · OTC INTERACTION ≠ SALE",
                ),
            )
        supply_as = own.get("gathered_at") or july_attr.get("gathered_at") or (forensics_ev or {}).get("gathered_at") or rs_as_of
        supply_src = (
            (own.get("who_selling_source") or {}).get("source_label")
            or own.get("source_label")
            or july_attr.get("source_label")
            or "Solscan · Squads custody + OTC"
        )
        supply_url = (
            (own.get("who_selling_source") or {}).get("source_url")
            or wm.get("explorer")
            or own.get("source_url")
            or july_attr.get("source_url")
            or mint_url
        )
        supply_fresh = (
            (own.get("who_selling_source") or {}).get("freshness")
            or own.get("freshness")
            or july_attr.get("freshness")
            or "research-pack"
        )
        supply_conf = july_attr.get("confidence") or "MEDIUM"
        supply_epi = "PARTIAL"
        supply_sum = (
            "PARTIAL / WATCH — already-unlocked Squads custody + OTC flow observed; mass dump not evidenced."
        )
    elif moved_n:
        supply_st = "UNKNOWN"
        supply_note = (
            f"Jul cohort movement observed ({moved_n}/80 emptied), but final liquid-venue "
            "destinations are not verified. Transfer ≠ sale."
        )
        supply_rows = [
            ("Moved", f"{moved_n}/80 Jul cohort emptied"),
            ("Destination", "Largely UNKNOWN"),
            ("Important", "Transfer ≠ sale · CEX deposit ≠ sale"),
        ]
        supply_as = (forensics_ev or {}).get("gathered_at") or rs_as_of
        supply_src = "on-chain cohort / forensics"
        supply_url = mint_url
        supply_fresh = None
        supply_conf = "LOW"
        supply_epi = "UNKNOWN"
        supply_sum = "Verified deposits or liquid distribution increase."
    else:
        supply_st = "UNKNOWN"
        supply_note = "No verified unlocked-supply → exchange path this run."
        supply_rows = [("Evidence", "Supply destination unresolved")]
        supply_as = (forensics_ev or {}).get("gathered_at") or rs_as_of
        supply_src = "on-chain cohort / forensics"
        supply_url = mint_url
        supply_fresh = None
        supply_conf = "LOW"
        supply_epi = "UNKNOWN"
        supply_sum = "Verified deposits or liquid distribution increase."
    out["defensive"].append(
        condition(
            condition_id="supply_to_liquid_venues",
            title="Unlocked supply reaches exchanges",
            summary=supply_sum,
            status=supply_st,
            interpretation=supply_note,
            evidence_rows=supply_rows,
            source=supply_src,
            source_url=supply_url,
            as_of=supply_as,
            confidence=supply_conf,
            epistemic_status=supply_epi,
            icon="dist",
        )
    )

    out["defensive"].append(
        condition(
            condition_id="leverage_without_spot",
            title="Leverage outruns spot demand",
            summary="Derivatives expand without matching spot support.",
            status=lev_def_st,
            interpretation=lev_def_note,
            evidence_rows=lev_rows,
            source="Binance",
            source_url=BINANCE_PUMP_FUT,
            as_of=lev_as,
            confidence="LOW" if lev_def_st == "UNKNOWN" else "MEDIUM",
            epistemic_status="PARTIAL",
            icon="lev_down",
        )
    )

    if buyer_label == "ACCUMULATION SIGNAL":
        bq_st, bq_note = "NO", "Buyer quality is not stuck unresolved — accumulation signal present."
    elif buyer_st == "UNKNOWN":
        bq_st, bq_note = "UNKNOWN", "Buyer quality cannot be judged without a sample."
    else:
        bq_st, bq_note = "YES", "Buyer identity / repeat quality remains unresolved."
    amd_px = None
    try:
        from lib.v3.pump_amendment_evidence import load_amendment_evidence

        amd = load_amendment_evidence() or {}
        amd_px = (amd.get("tape") or {}).get("last_price")
    except Exception:
        amd = {}
    getout_st = "UNKNOWN"
    if isinstance(amd_px, (int, float)):
        getout_st = "NO" if float(amd_px) >= 0.00215 else "YES"
    out["defensive"].append(
        condition(
            condition_id="price_invalidation_00215",
            title="Daily close below $0.00215",
            summary="Course-change / get-out. Separate from tokenomics.",
            status=getout_st,
            interpretation=(
                f"Live ~${float(amd_px):.4f}. Invalidation is a daily close below $0.00215 — "
                "market-risk discipline, not a buyback-policy fail."
                if isinstance(amd_px, (int, float))
                else "Get-out remains daily close below $0.00215. Live close UNKNOWN this pass."
            ),
            evidence_rows=[
                ("Level", "$0.00215 daily close"),
                ("Live", f"${float(amd_px):.4f}" if isinstance(amd_px, (int, float)) else "UNKNOWN"),
                ("Rule", "Independent of value-capture / buyback evidence"),
            ],
            source="locked V3 market-risk level",
            source_url=BINANCE_PUMP_SPOT,
            as_of=(amd.get("fetched_at_utc") if amd else None),
            confidence="MEDIUM",
            epistemic_status="KNOWN" if getout_st in ("YES", "NO") else "UNKNOWN",
            icon="warn",
        )
    )

    out["defensive"].append(
        condition(
            condition_id="buyer_quality_unresolved",
            title="Buyer quality stays unresolved",
            summary="No repeat or attributable accumulation emerges.",
            status=bq_st,
            interpretation=bq_note,
            evidence_rows=buyer_rows
            or [
                ("Known", "Real DEX buying may exist"),
                ("Unknown", "Who is driving it"),
                ("Need", "Repeat / high-quality attributed buyers"),
            ],
            source="Helius / Solana DEX sample",
            source_url=buyer_url,
            as_of=buyer_as,
            confidence="MEDIUM" if bq_st != "UNKNOWN" else "LOW",
            epistemic_status="PARTIAL",
            icon="warn",
        )
    )

    out["more_constructive"] = [
        {"label": c["title"], "detail": c["summary"], "status": c["status"]} for c in out["constructive"]
    ]
    out["more_defensive"] = [
        {"label": c["title"], "detail": c["summary"], "status": c["status"]} for c in out["defensive"]
    ]
    return out
