"""REALITY CHECK — compact evidence sanity section (universal ALT shape, PUMP wired)."""

from __future__ import annotations

from typing import Any

from lib.v3.change_mind import (
    BINANCE_PUMP_FUT,
    BINANCE_PUMP_SPOT,
    _fmt_pct,
    _metric_direction,
)


def rc_item(
    *,
    item_id: str,
    title: str,
    summary: str,
    evidence_rows: list[tuple[str, str]] | None = None,
    interpretation: str = "",
    priority: str | None = None,
    source: str = "",
    source_url: str | None = None,
    as_of: str | None = None,
    freshness: str | None = None,
    confidence: str = "MEDIUM",
    epistemic_status: str = "KNOWN",
) -> dict[str, Any]:
    pri = (priority or "").upper() or None
    if pri and pri not in ("HIGH", "MEDIUM"):
        pri = "MEDIUM"
    if freshness is None and as_of:
        freshness = "as_of-dated"
    return {
        "id": item_id,
        "title": title,
        "summary": summary,
        "evidence_rows": [{"key": k, "value": v} for k, v in (evidence_rows or []) if v],
        "interpretation": interpretation,
        "priority": pri,
        "source": source,
        "source_url": source_url,
        "as_of": as_of,
        "freshness": freshness,
        "confidence": confidence,
        "epistemic_status": epistemic_status,
    }


def empty_reality_check() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "priority_headline": "",
        "known": [],
        "suggests": [],
        "unknowns": [],
    }


def _rs_horizon_read(b7: Any, b30: Any, s7: Any, s30: Any) -> str:
    """all_strong | soft_7d | weak | incomplete | mixed — no magnitude thresholds."""
    if any(v is None for v in (b7, b30, s7, s30)):
        return "incomplete"
    b7f, b30f, s7f, s30f = float(b7), float(b30), float(s7), float(s30)
    if b7f > 0 and b30f > 0 and s7f > 0 and s30f > 0:
        return "all_strong"
    if b30f > 0 and s30f > 0 and (b7f <= 0 or s7f <= 0):
        return "soft_7d"
    if b30f <= 0 and s30f <= 0:
        return "weak"
    return "mixed"


def _funding_tone(funding: dict) -> str:
    """Derive tone from existing funding wording/display — no invented cutoffs."""
    text = f"{funding.get('wording') or ''} {funding.get('display') or ''}".lower()
    if not text.strip():
        return "unknown"
    cold_marks = (
        "unusually low",
        "low/negative",
        "negative vs",
        "cold",
    )
    hot_marks = (
        "unusually high",
        "high/positive",
        "elevated funding",
        "hot funding",
        "crowded-long",
    )
    if any(m in text for m in cold_marks):
        return "cold"
    if any(m in text for m in hot_marks):
        return "hot"
    return "present"


def _derivatives_suggest(
    fut: Any, funding: dict, oi: Any
) -> tuple[str, str, list[tuple[str, str]], str] | None:
    if fut is None and not (funding.get("display") or funding.get("wording")):
        return None
    tone = _funding_tone(funding)
    fut_txt = f"{float(fut):.1f}× observed" if fut is not None else "not wired"
    fund_disp = funding.get("display") or "incomplete"
    rows: list[tuple[str, str]] = [
        ("Futures/spot", fut_txt),
        ("Funding", fund_disp),
    ]
    if oi:
        rows.append(("OI now", f"${float(oi) / 1e6:.1f}M"))
    rows.append(("Historical OI", "Unavailable at prior tops"))

    if tone == "cold":
        return (
            "Derivatives matter, but no blow-off signal",
            "Futures activity is present, while funding remains unusually cold.",
            rows,
            "Current funding context is cold vs PUMP history — not a classic crowded-long top by itself.",
        )
    if tone == "hot":
        return (
            "Derivatives matter — funding is hot",
            "Futures activity is present and funding is elevated versus history.",
            rows,
            "Hot funding raises crowded-position risk. Still not a validated blow-off classifier.",
        )
    if tone == "present":
        return (
            "Derivatives matter — funding context mixed",
            "Futures activity is present; funding context is inconclusive.",
            rows,
            "Derivatives are relevant, but funding does not clearly read cold or hot.",
        )
    return (
        "Derivatives matter — funding incomplete",
        "Futures activity is present; funding context is incomplete.",
        rows,
        "Cannot claim blow-off presence or absence without clearer funding context.",
    )


def _fundamentals_suggest(
    rev: dict, burn: dict, share: dict
) -> tuple[str, str, list[tuple[str, str]], str] | None:
    dirs = {
        "Revenue": _metric_direction(rev),
        "Buyback/burn": _metric_direction(burn),
        "Share": _metric_direction(share),
    }
    live = {k: v for k, v in dirs.items() if v != "unknown"}
    if not live:
        return None
    rows: list[tuple[str, str]] = []
    for label, m in (("Revenue", rev), ("Buyback/burn", burn), ("Share", share)):
        if m.get("value") is not None:
            rows.append((label, f"{m.get('value')} · {dirs[label]}"))
    rows.append(("Limit", "Platform success ≠ guaranteed token-price success"))

    ups = sum(1 for v in live.values() if v == "up")
    downs = sum(1 for v in live.values() if v == "down")
    if ups == len(live) and ups >= 2:
        return (
            "Fundamentals support — they do not prove price",
            "Platform recovery strengthens the thesis, but causation is weak.",
            rows,
            "Improving economics support the project thesis — not a price-timing engine.",
        )
    if downs and not ups:
        return (
            "Fundamentals are weakening — they do not prove price",
            "Platform metrics are deteriorating; this still does not time price.",
            rows,
            "Weakening economics matter for thesis quality — not an automatic sell rule.",
        )
    if ups and downs:
        return (
            "Fundamentals are mixed — they do not prove price",
            "Some platform metrics improve while others deteriorate.",
            rows,
            "Mixed platform direction — do not treat as clean recovery.",
        )
    if ups:
        return (
            "Fundamentals are mixed — they do not prove price",
            "Some platform metrics improve while others are flat or unclear.",
            rows,
            "Partial improvement only — recovery not fully established.",
        )
    return (
        "Fundamentals are live — direction unclear",
        "Platform metrics are available, but recovery is not established.",
        rows,
        "Live levels without clear direction — do not invent a recovery claim.",
    )


def build_pump_reality_check(
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
    """PUMP reality-check items from live evidence — hierarchy, not a research dump."""
    from lib.v3.pump_forensics_loader import (
        buyer_evidence_label,
        buyer_observed_window,
    )

    hm = {m.get("metric_id"): m for m in (health_metrics or [])}
    stage1 = stage1 or {}
    funding = stage1.get("funding") or {}
    supply = stage1.get("supply") or {}
    beh = (wf or {}).get("july_recipient_behaviour") or {}
    moved_n = (beh.get("MOVED_DESTINATION_UNKNOWN") or {}).get("count", 0)
    from lib.v3.pump_forensics_loader import load_july_attribution

    july_attr = load_july_attribution() or ((forensics_ev or {}).get("july_attribution") or {})
    july_pct = july_attr.get("pct") or {}
    own = july_attr.get("ownership_buyer_quality") or {}

    rev = hm.get("platform_revenue") or {}
    burn = hm.get("buyback_burn") or {}
    share = hm.get("launchpad_share") or {}
    ow = buyer_observed_window(buyer)
    buyer_label = buyer_evidence_label(wf, buyer)
    buyer_as = (buyer or {}).get("gathered_at")
    rs_as = rs_btc.get("fetched_at") or rs_sol.get("fetched_at")
    b7, b30 = rs_btc.get("change_7d_pct"), rs_btc.get("change_30d_pct")
    s7, s30 = rs_sol.get("change_7d_pct"), rs_sol.get("change_30d_pct")
    fut = deriv.get("fut_spot_vol_ratio")
    oi = deriv.get("oi_notional_usd")
    rs_read = _rs_horizon_read(b7, b30, s7, s30)

    buyer_url = None
    for w in (buyer or {}).get("wallet_profiles_checked") or []:
        links = w.get("sample_explorer_links") or []
        if links:
            buyer_url = links[0]
            break

    out = empty_reality_check()
    out["priority_headline"] = (
        "Who is actually driving this rally — and who is distributing into it?"
    )

    # ---- KNOWN (hard facts only) ----
    if rev.get("data_status") == "LIVE" and burn.get("data_status") == "LIVE":
        out["known"].append(
            rc_item(
                item_id="platform_economics_real",
                title="Platform economics are real",
                summary="Revenue and buybacks are material and currently active.",
                evidence_rows=[
                    ("Revenue", str(rev.get("value") or "—")),
                    ("Buyback/burn", str(burn.get("value") or "—").replace(" burned", "")),
                    ("Share", str(share.get("value") or "—")),
                ],
                interpretation="These prove the platform is economically active. They do not prove token price must rise.",
                source="Pump.fun / DefiLlama",
                source_url=rev.get("source_url") or burn.get("source_url"),
                as_of=rev.get("fetched_at") or burn.get("fetched_at"),
                confidence="HIGH",
                epistemic_status="KNOWN",
            )
        )

    rs_rows = [
        ("PUMP/BTC", f"7d {_fmt_pct(b7)} · 30d {_fmt_pct(b30)}"),
        ("PUMP/SOL", f"7d {_fmt_pct(s7)} · 30d {_fmt_pct(s30)}"),
    ]
    if rs_read == "all_strong":
        out["known"].append(
            rc_item(
                item_id="rs_strong",
                title="Relative strength is strong",
                summary="PUMP is outperforming both BTC and SOL on 7d and 30d.",
                evidence_rows=rs_rows + [("Meaning", "Real leadership, not just USD beta")],
                interpretation="Strong RS on both horizons is a measured fact. It does not prove the rally continues.",
                source=rs_btc.get("source") or "binance-daily",
                source_url=BINANCE_PUMP_SPOT,
                as_of=rs_as,
                confidence="HIGH",
                epistemic_status="KNOWN",
            )
        )
    elif rs_read == "soft_7d":
        out["known"].append(
            rc_item(
                item_id="rs_soft_7d",
                title="Relative strength is mixed across horizons",
                summary="30d still leads both benchmarks, but 7d has softened.",
                evidence_rows=rs_rows + [("Watch", "7d deterioration vs still-positive 30d")],
                interpretation="Measured fact: longer window still positive while recent window has rolled over on at least one pair.",
                source=rs_btc.get("source") or "binance-daily",
                source_url=BINANCE_PUMP_SPOT,
                as_of=rs_as,
                confidence="MEDIUM",
                epistemic_status="KNOWN",
            )
        )
    elif rs_read in ("weak", "mixed") and b30 is not None and s30 is not None:
        out["known"].append(
            rc_item(
                item_id="rs_not_uniform",
                title="Relative strength is not uniform",
                summary="PUMP/BTC and PUMP/SOL are not jointly strong across horizons.",
                evidence_rows=rs_rows,
                interpretation="Measured RS fact — do not treat as sustained leadership.",
                source=rs_btc.get("source") or "binance-daily",
                source_url=BINANCE_PUMP_SPOT,
                as_of=rs_as,
                confidence="MEDIUM",
                epistemic_status="KNOWN",
            )
        )

    own = july_attr.get("ownership_buyer_quality") or {}
    if july_pct or own:
        p = july_pct or {}
        july_rows = [
            ("Read", "ALREADY-UNLOCKED SQUADS CUSTODY"),
            ("July unlocked", "~52.04B into Squads (Streamflow escrow ~0)"),
            ("Observed DEX swaps", f"~{p.get('DEX_SWAP', 0):.2f}% upper bound"),
            ("Labelled CEX deposit", f"{p.get('CEX_DEPOSIT', 0):.2f}%"),
            ("Unattributed held", f"{p.get('STILL_HELD', 0):.2f}%"),
            ("Rule", "TRANSFER ≠ SALE · custody ≠ sale"),
        ]
        out["known"].append(
            rc_item(
                item_id="july_unlocked_squads",
                title="July cohort unlocked into Squads custody",
                summary="~52.04B in Squads. Escrow ~0. Owners/timing UNKNOWN.",
                evidence_rows=july_rows,
                interpretation=(
                    own.get("supply_interpretation")
                    or (
                        "The risk is available supply controlled through unidentified multisigs, "
                        "not a future Streamflow cliff."
                    )
                ),
                source=own.get("source_label")
                or july_attr.get("source_label")
                or "Solscan · on-chain forensics",
                source_url=own.get("source_url")
                or july_attr.get("source_url")
                or supply.get("mint_explorer"),
                as_of=own.get("gathered_at")
                or july_attr.get("gathered_at")
                or (forensics_ev or {}).get("gathered_at"),
                freshness=own.get("freshness") or july_attr.get("freshness") or "research-pack",
                confidence=july_attr.get("confidence") or "MEDIUM",
                epistemic_status="KNOWN",
            )
        )
        wm = own.get("wintermute_otc") or {}
        if wm.get("outflow_to_wintermute_tokens"):
            out["known"].append(
                rc_item(
                    item_id="wintermute_otc_flow",
                    title="~287M PUMP sent to labelled Wintermute OTC",
                    summary="~287M to labelled WM OTC. Sale not proven.",
                    evidence_rows=[
                        ("Label", wm.get("display") or "LARGE HOLDER → WINTERMUTE OTC"),
                        ("Wallet", f"{(wm.get('wallet') or '')[:12]}…"),
                        (
                            "Balance",
                            f"~{(wm.get('current_balance_pump') or 0) / 1e9:.2f}B PUMP",
                        ),
                        (
                            "To Wintermute OTC",
                            f"~{wm['outflow_to_wintermute_tokens'] / 1e6:.0f}M PUMP",
                        ),
                        ("Rule", wm.get("discipline") or "OTC INTERACTION ≠ SALE"),
                    ],
                    interpretation=wm.get("interpretation")
                    or (
                        "Important capital-flow evidence; OTC interaction does not prove a sale, "
                        "market dumping or price suppression."
                    ),
                    source=wm.get("source_label")
                    or own.get("source_label")
                    or "Solscan · Wintermute OTC flow",
                    source_url=wm.get("source_url")
                    or wm.get("explorer")
                    or own.get("source_url")
                    or supply.get("mint_explorer"),
                    as_of=own.get("gathered_at") or july_attr.get("gathered_at"),
                    freshness=wm.get("freshness") or own.get("freshness") or "research-pack",
                    confidence="MEDIUM",
                    epistemic_status="PARTIAL",
                )
            )

    net_n = ow.get("net_accumulator_count")
    if net_n:
        hold = ow.get("holding_claim") or ""
        out["known"].append(
            rc_item(
                item_id="dex_buying_exists",
                title="Real DEX buying exists",
                summary="The sampled window shows genuine net accumulation on-chain.",
                evidence_rows=[
                    ("Net buyers", f"{net_n} observed net accumulators"),
                    ("Holding", hold or "holding check partial"),
                    ("Caveat", "Buyer identity remains incomplete"),
                ],
                interpretation="Observed buying ≠ identified high-quality buyers.",
                source="Helius / Solana DEX sample",
                source_url=buyer_url,
                as_of=buyer_as,
                confidence="MEDIUM",
                epistemic_status="KNOWN",
            )
        )

    if supply.get("circulating_pct") or supply.get("display_compact"):
        out["known"].append(
            rc_item(
                item_id="supply_measurable",
                title="Supply is measurable, not simple",
                summary="Circulating, scheduled-unlocked and minted supply are different numbers.",
                evidence_rows=[
                    ("Circulating", f"{supply.get('circulating_pct', '—')}%"),
                    ("Scheduled unlocked", f"{supply.get('schedule_unlocked_pct', '—')}%"),
                    ("On-chain supply", f"{supply.get('on_chain_minted_pct', '—')}%"),
                    (
                        "Mint authority",
                        "Null — no additional minting"
                        if supply.get("mint_authority") in (None, "null", "Null")
                        else str(supply.get("mint_authority")),
                    ),
                ],
                interpretation="Unlocked ≠ liquid ≠ sold. Reconciliation between supply concepts remains unresolved.",
                source="CoinGecko / Tokenomics / Solana RPC",
                source_url=supply.get("mint_explorer"),
                as_of=supply.get("fetched_at") or rs_as,
                confidence="MEDIUM",
                epistemic_status="KNOWN",
            )
        )

    # ---- WHAT IT SUGGESTS (inferences, not facts) ----
    if rs_read == "all_strong":
        out["suggests"].append(
            rc_item(
                item_id="leadership_bullish",
                title="Price leadership is genuinely bullish",
                summary="Real RS vs BTC/SOL — not just a market-wide bounce.",
                evidence_rows=rs_rows + [("Read", "Leading on both 7d and 30d")],
                interpretation="Evidence-based inference from 7d+30d RS — not a trading instruction.",
                source=rs_btc.get("source") or "binance-daily",
                source_url=BINANCE_PUMP_SPOT,
                as_of=rs_as,
                confidence="MEDIUM",
                epistemic_status="INFERRED",
            )
        )
    elif rs_read == "soft_7d":
        out["suggests"].append(
            rc_item(
                item_id="leadership_softening",
                title="Price leadership is softening",
                summary="30d still leads, but 7d has rolled over on at least one pair.",
                evidence_rows=rs_rows + [("Read", "Do not call this genuinely bullish")],
                interpretation="Softer inference while longer-window leadership remains positive.",
                source=rs_btc.get("source") or "binance-daily",
                source_url=BINANCE_PUMP_SPOT,
                as_of=rs_as,
                confidence="MEDIUM",
                epistemic_status="INFERRED",
            )
        )
    elif rs_read in ("weak", "mixed"):
        out["suggests"].append(
            rc_item(
                item_id="leadership_unclear",
                title="Price leadership is no longer clear",
                summary="Benchmark relative strength is mixed or weak across horizons.",
                evidence_rows=rs_rows,
                interpretation="Do not treat current price action as confirmed leadership.",
                source=rs_btc.get("source") or "binance-daily",
                source_url=BINANCE_PUMP_SPOT,
                as_of=rs_as,
                confidence="MEDIUM",
                epistemic_status="INFERRED",
            )
        )

    bq = own.get("buyer_quality") or {}
    if bq.get("display") or buyer_label in ("MIXED", "INCONCLUSIVE", "WEAK SAMPLE", "LEVERAGE-LED") or net_n:
        out["suggests"].append(
            rc_item(
                item_id="flow_quality_unresolved",
                title="Observed DEX buying is trader-heavy",
                summary=bq.get("display")
                or "Buying is real, but capital quality is not clean.",
                evidence_rows=[
                    ("Read", bq.get("display") or "REAL BUYING · TRADER-HEAVY"),
                    ("Detail", (bq.get("evidence") or "Observed DEX accumulation")[:180]),
                    ("Caveat", "Sample ~15h · not market-wide · not strong/persistent accumulators"),
                ],
                interpretation=bq.get("unknown")
                or "Observed buying ≠ identified high-quality buyers.",
                source=(own.get("buyer_quality_source") or {}).get("source_label")
                or "Helius / Solana DEX sample",
                source_url=buyer_url
                or (own.get("buyer_quality_source") or {}).get("source_url"),
                as_of=own.get("gathered_at") or buyer_as,
                freshness=(own.get("buyer_quality_source") or {}).get("freshness")
                or own.get("freshness")
                or "research-pack",
                confidence="MEDIUM",
                epistemic_status="INFERRED",
            )
        )

    if own.get("supply_interpretation") or july_pct:
        out["suggests"].append(
            rc_item(
                item_id="supply_overhang_multisig",
                title="Overhang sits in unlocked Squads vaults",
                summary="Controlled via Squads custody, not a future Streamflow cliff.",
                evidence_rows=[
                    ("July", "Already unlocked · Streamflow escrow ~0"),
                    ("Gate", "Squads signers / policy — timing UNKNOWN"),
                    ("Rule", "custody ≠ sale · TRANSFER ≠ SALE"),
                ],
                interpretation=own.get("supply_interpretation")
                or (
                    "Supply overhang is controlled through already-unlocked multisigs rather than "
                    "future Streamflow vesting."
                ),
                source=(own.get("supply_source") or {}).get("source_label")
                or own.get("source_label")
                or july_attr.get("source_label")
                or "Solscan · PUMP mint / Squads custody",
                source_url=(own.get("supply_source") or {}).get("source_url")
                or own.get("source_url")
                or july_attr.get("source_url")
                or supply.get("mint_explorer"),
                as_of=own.get("gathered_at") or july_attr.get("gathered_at"),
                freshness=(own.get("supply_source") or {}).get("freshness")
                or own.get("freshness")
                or "research-pack",
                confidence="MEDIUM",
                epistemic_status="INFERRED",
            )
        )

    wm_sug = own.get("wintermute_otc") or {}
    if wm_sug.get("outflow_to_wintermute_tokens"):
        out["suggests"].append(
            rc_item(
                item_id="otc_counterparty_reach",
                title="Large-holder inventory reaching OTC/MM",
                summary="Material PUMP to labelled WM OTC — sale not proven.",
                evidence_rows=[
                    (
                        "Observed",
                        f"~{wm_sug['outflow_to_wintermute_tokens'] / 1e6:.0f}M → Wintermute OTC",
                    ),
                    ("Rule", wm_sug.get("discipline") or "OTC INTERACTION ≠ SALE"),
                ],
                interpretation=wm_sug.get("interpretation")
                or "OTC interaction does not prove dumping or price suppression.",
                source=wm_sug.get("source_label")
                or "Solscan · Wintermute OTC flow",
                source_url=wm_sug.get("source_url") or wm_sug.get("explorer"),
                as_of=own.get("gathered_at"),
                freshness=wm_sug.get("freshness") or own.get("freshness") or "research-pack",
                confidence="MEDIUM",
                epistemic_status="INFERRED",
            )
        )

    deriv_sug = _derivatives_suggest(fut, funding, oi)
    if deriv_sug:
        d_title, d_sum, d_rows, d_note = deriv_sug
        out["suggests"].append(
            rc_item(
                item_id="derivatives_context",
                title=d_title,
                summary=d_sum,
                evidence_rows=d_rows,
                interpretation=d_note,
                source="Binance",
                source_url=BINANCE_PUMP_FUT,
                as_of=deriv.get("gathered_at") or funding.get("latest_time") or rs_as,
                confidence="MEDIUM",
                epistemic_status="INFERRED",
            )
        )

    fund_sug = _fundamentals_suggest(rev, burn, share)
    if fund_sug:
        f_title, f_sum, f_rows, f_note = fund_sug
        out["suggests"].append(
            rc_item(
                item_id="fundamentals_vs_price",
                title=f_title,
                summary=f_sum,
                evidence_rows=f_rows,
                interpretation=f_note,
                source="Pump.fun / DefiLlama",
                source_url=rev.get("source_url") or burn.get("source_url"),
                as_of=rev.get("fetched_at") or burn.get("fetched_at"),
                confidence="MEDIUM",
                epistemic_status="INFERRED",
            )
        )

    # ---- UNKNOWNS (prioritised) ----
    out["unknowns"].append(
        rc_item(
            item_id="major_buyers",
            title="Who are the major buyers?",
            summary="Repeat buyers, whales, attributable capital incomplete.",
            evidence_rows=[
                ("Known", f"Real DEX accumulation ({net_n} nets)" if net_n else "Partial DEX sample"),
                ("Unknown", "Identity / repeat behaviour of drivers"),
            ],
            interpretation="Highest-priority gap for capital-quality judgment.",
            priority="HIGH",
            source="Helius / Solana DEX sample",
            source_url=buyer_url,
            as_of=buyer_as,
            confidence="LOW",
            epistemic_status="UNKNOWN",
        )
    )
    out["unknowns"].append(
        rc_item(
            item_id="who_is_selling",
            title="Who is selling?",
            summary="Whale/team/treasury/major-holder distribution unresolved.",
            evidence_rows=[
                (
                    "Known",
                    july_attr.get("headline_compact")
                    if july_pct
                    else "Some cohort movement observable",
                ),
                ("Rule", "Transfer ≠ sale · CEX deposit ≠ sale · custody ≠ sale · OTC INTERACTION ≠ SALE"),
            ],
            interpretation="Labelled seller attribution remains incomplete.",
            priority="HIGH",
            source="on-chain cohort / forensics",
            source_url=supply.get("mint_explorer"),
            as_of=(own.get("gathered_at") if own else None)
            or (july_attr.get("gathered_at") if july_pct else None)
            or (forensics_ev or {}).get("gathered_at")
            or buyer_as,
            confidence="MEDIUM" if (july_pct or own) else "LOW",
            epistemic_status="PARTIAL" if (july_pct or own) else "UNKNOWN",
        )
    )
    if july_pct or own:
        wm = own.get("wintermute_otc") or july_attr.get("wintermute_related_unattributed") or {}
        unk_rows = [
            ("Open", "Who controls the Squads vaults?"),
            ("Open", "When will those vaults distribute?"),
        ]
        if wm.get("outflow_to_wintermute_tokens") or wm.get("wallet"):
            unk_rows.append(
                ("Open", "Was the Wintermute OTC flow a sale, inventory transfer or settlement?")
            )
            bal = wm.get("current_balance_pump")
            if bal:
                unk_rows.append(
                    ("Open", f"What is the source of the ~{bal / 1e9:.2f}B wallet inventory?")
                )
            elif wm.get("wallet"):
                unk_rows.append(
                    (
                        "Note",
                        f"Unattributed wallet {str(wm.get('wallet'))[:12]}… · Wintermute OTC observed",
                    )
                )
        out["unknowns"].append(
            rc_item(
                item_id="july_custody_control",
                title="Who controls Squads vaults — and when?",
                summary="July cohort unlocked in Squads; owners/timing UNKNOWN.",
                evidence_rows=unk_rows,
                interpretation=(
                    "custody ≠ sale. Already-unlocked ≠ sold. "
                    "OTC INTERACTION ≠ SALE."
                ),
                priority="MEDIUM",
                source=own.get("source_label")
                or july_attr.get("source_label")
                or "Solscan · Squads custody",
                source_url=own.get("source_url")
                or july_attr.get("source_url")
                or supply.get("mint_explorer"),
                as_of=own.get("gathered_at")
                or july_attr.get("gathered_at")
                or (forensics_ev or {}).get("gathered_at"),
                freshness=own.get("freshness") or july_attr.get("freshness") or "research-pack",
                confidence="MEDIUM",
                epistemic_status="PARTIAL",
            )
        )
    else:
        out["unknowns"].append(
            rc_item(
                item_id="july_destination",
                title="Where did July supply finally go?",
                summary="Most recipients moved tokens; final liquid destination is still unclear.",
                evidence_rows=[
                    (
                        "Known",
                        f"{moved_n}/80 recipient wallets emptied"
                        if moved_n
                        else "Cohort movement partial",
                    ),
                    ("Unknown", "Final destination / sale outcome"),
                ],
                interpretation="UNKNOWN ≠ bearish. Movement alone does not prove distribution into the rally.",
                priority="MEDIUM",
                source="on-chain cohort / forensics",
                source_url=supply.get("mint_explorer"),
                as_of=(forensics_ev or {}).get("gathered_at"),
                confidence="LOW",
                epistemic_status="UNKNOWN",
            )
        )
    out["unknowns"].append(
        rc_item(
            item_id="historical_leverage_gap",
            title="Historical leverage picture is incomplete",
            summary="Historical OI and liquidation data at prior highs are still missing.",
            evidence_rows=[
                ("OI", "Sep / Jan highs unavailable from public Binance hist"),
                ("Liquidations", "Historical series unavailable"),
            ],
            interpretation="Blocks confident claims that current leverage resembles previous tops.",
            priority="MEDIUM",
            source="Binance / forensics gaps",
            source_url=BINANCE_PUMP_FUT,
            as_of=funding.get("latest_time") or rs_as,
            confidence="LOW",
            epistemic_status="UNKNOWN",
        )
    )

    out["known"] = out["known"][:4]
    out["suggests"] = out["suggests"][:4]
    out["unknowns"] = out["unknowns"][:4]
    return out
