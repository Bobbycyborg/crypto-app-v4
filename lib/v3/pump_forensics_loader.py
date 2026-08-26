"""Load audited PUMP forensics snapshot — no API calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FORENSICS_DIR = ROOT / "reports" / "pump-forensics"


def load_forensics_snapshot(path: Path | str | None = None) -> dict | None:
    if path is not None:
        p = Path(path)
        return json.loads(p.read_text()) if p.exists() else None
    if not FORENSICS_DIR.exists():
        return None
    snaps = sorted(FORENSICS_DIR.glob("snapshot-*.json"))
    if not snaps:
        return None
    return json.loads(snaps[-1].read_text())


def load_buyer_forensics_snapshot(path: Path | str | None = None) -> dict | None:
    if path is not None:
        p = Path(path)
        return json.loads(p.read_text()) if p.exists() else None
    if not FORENSICS_DIR.exists():
        return None
    snaps = sorted(FORENSICS_DIR.glob("buyer-forensics-*.json"))
    if not snaps:
        return None
    return json.loads(snaps[-1].read_text())


def buyer_forensics_evidence_path(snapshot: dict) -> str | None:
    sid = snapshot.get("snapshot_id")
    if not sid:
        return None
    p = FORENSICS_DIR / f"buyer-forensics-evidence-{sid}.md"
    return str(p.relative_to(ROOT)) if p.exists() else None


def forensics_evidence_pack_path(snapshot: dict) -> str | None:
    sid = snapshot.get("snapshot_id")
    if not sid:
        return None
    p = FORENSICS_DIR / f"evidence-pack-{sid}.md"
    return str(p.relative_to(ROOT)) if p.exists() else None


def daily_closes(rows: list[dict] | None) -> dict[str, float]:
    return {r["date"]: float(r["close"]) for r in (rows or []) if r.get("date") is not None}


def rs_from_forensics_snapshot(forensics: dict) -> tuple[dict[str, Any], dict[str, Any]]:
    from lib.v3.rs import rs_block

    fetched = forensics.get("gathered_at", "")
    pump = daily_closes(forensics.get("pump_daily"))
    btc = daily_closes(forensics.get("btc_daily"))
    sol = daily_closes(forensics.get("sol_daily"))

    def _stamp(block: dict[str, Any]) -> dict[str, Any]:
        # Forensics daily closes are Binance klines — not CoinGecko.
        if block.get("data_status") == "LIVE":
            block["source"] = "binance-daily"
        return block

    return (
        _stamp(rs_block("pump_btc", "PUMP / BTC", pump, btc, "BTC", fetched)),
        _stamp(rs_block("pump_sol", "PUMP / SOL", pump, sol, "SOL", fetched)),
    )


def fmt_rs_line(rs: dict[str, Any]) -> str:
    ch7 = rs.get("change_7d_pct")
    ch30 = rs.get("change_30d_pct")
    if ch7 is not None and ch30 is not None:
        return f"7d {ch7:+.1f}% · 30d {ch30:+.1f}%"
    if ch30 is not None:
        return f"30d {ch30:+.1f}%"
    if ch7 is not None:
        return f"7d {ch7:+.1f}%"
    return "UNKNOWN"


def buyer_evidence_label(
    wf: dict | None = None,
    buyer: dict | None = None,
) -> str:
    if buyer:
        verdict = (buyer.get("verdict_block") or {}).get("verdict", "UNKNOWN")
        if verdict == "CREDIBLE ACCUMULATION":
            return "ACCUMULATION SIGNAL"
        if verdict == "MIXED":
            return "MIXED"
        if verdict == "SPECULATIVE / LEVERAGE-LED":
            return "LEVERAGE-LED"
        return "INCONCLUSIVE"
    buyers = (wf or {}).get("swap_net_buyers") or {}
    if any(buyers.get(w) for w in ("24h", "3d", "7d", "14d")):
        return "WEAK SAMPLE"
    return "INCONCLUSIVE"


def buyer_observed_window(buyer: dict | None) -> dict:
    if not buyer:
        return {}
    return buyer.get("observed_window") or (buyer.get("windows") or {}).get("observed") or {}


def buyer_evidence_detail(buyer: dict | None) -> str:
    if not buyer:
        return "Principal-pool SWAP sample not loaded."
    v = buyer.get("verdict_block") or {}
    # Prefer verdict detail — already includes span, holding claim, concentration, CEX limit
    detail = (v.get("detail") or "").strip()
    if detail:
        return detail
    ow = buyer_observed_window(buyer)
    bits = []
    if ow.get("holding_claim"):
        bits.append(ow["holding_claim"] + ".")
    if ow.get("span_hours") is not None:
        bits.append(f"Observed span ~{ow['span_hours']:.0f}h (not a 14d sample).")
    if ow.get("top5_gross_buy_share_pct") is not None:
        bits.append(f"Top-5 gross buy share {ow['top5_gross_buy_share_pct']:.0f}%.")
    return " ".join(bits) or "Buyer evidence incomplete."


JULY_ATTR_DIR = FORENSICS_DIR / "july-destination-multihop"
JULY_ATTR_PATH = JULY_ATTR_DIR / "ATTRIBUTION-LATEST.json"
OWNERSHIP_DIR = FORENSICS_DIR / "ownership-buyer-quality"
OWNERSHIP_FINDINGS = OWNERSHIP_DIR / "FINDINGS.md"


def load_ownership_buyer_quality() -> dict | None:
    """Ownership + buyer-quality research pack (Aug 11/12). No API calls."""
    if not OWNERSHIP_DIR.exists():
        return None
    vest_path = OWNERSHIP_DIR / "ownership-vesting.json"
    buyer_path = OWNERSHIP_DIR / "buyer-quality.json"
    wm_path = OWNERSHIP_DIR / "wintermute-wallet-trace.json"
    vest = json.loads(vest_path.read_text()) if vest_path.exists() else {}
    buyer = json.loads(buyer_path.read_text()) if buyer_path.exists() else {}
    wm = json.loads(wm_path.read_text()) if wm_path.exists() else {}
    if not vest and not buyer and not wm:
        return None

    july_sf = vest.get("july_streamflow") or {}
    unlocked_b = float(july_sf.get("tokens") or 52_039_000_000) / 1e9
    wm_out = float((wm.get("wintermute") or {}).get("outflow_tokens_to_wm") or 0)
    wm_bal = wm.get("current_balance_pump")
    q = buyer.get("quant") or {}
    wm_wallet = wm.get("wallet") or "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9"
    wm_explorer = wm.get("explorer") or f"https://solscan.io/account/{wm_wallet}"
    mint_explorer = "https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn"
    gathered = (
        vest.get("gathered_at_utc")
        or buyer.get("gathered_at_utc")
        or wm.get("gathered_at_utc")
    )

    return {
        "gathered_at": gathered,
        # Internal pack paths — not for visible UI source labels
        "source_path": str(OWNERSHIP_DIR.relative_to(ROOT)),
        "findings_path": str(OWNERSHIP_FINDINGS.relative_to(ROOT))
        if OWNERSHIP_FINDINGS.exists()
        else None,
        "source_label": "Solscan · on-chain forensics",
        "source_url": mint_explorer,
        "freshness": "research-pack",
        "mint_explorer": mint_explorer,
        "confidence": "MEDIUM",
        "july_unlocked_squads": {
            "tokens": july_sf.get("tokens"),
            "tokens_b": round(unlocked_b, 2),
            "n_streams": july_sf.get("n_streams"),
            "escrow_tokens": july_sf.get("still_in_escrow_tokens"),
            "schedule": july_sf.get("schedule"),
            "finding": vest.get("finding"),
            "label": "ALREADY-UNLOCKED SQUADS CUSTODY",
        },
        "buyer_quality": {
            "quant": q,
            "sample_caveat": buyer.get("sample_caveat"),
            "profiles_deep_dived": buyer.get("profiles_deep_dived"),
            "observed_net_accumulators": buyer.get("observed_net_accumulators_in_sample"),
            "display": "REAL BUYING · TRADER-HEAVY",
            "evidence": (
                f"Top-sample deep dive: {q.get('pct_buying_from_repeat_accumulators_of_top_sample', '—')}% "
                f"of net from repeat multi-day accumulators; "
                f"{q.get('pct_still_held_of_top_sample_net', '—')}% still held; "
                f"{q.get('pct_from_wallets_age_lt_14d_proxy', '—')}% young-wallet proxy; "
                f"{q.get('single_day_buyers', '—')}/{q.get('multi_day_buyers', 0) + q.get('single_day_buyers', 0)} "
                f"top wallets single-day; trader-heavy. Sample ~15h DEX span — not market-wide."
            ),
            "unknown": (
                "Buyer identity incomplete. Do not call current buyers strong/persistent accumulators. "
                "CEX spot buyers unobservable."
            ),
        },
        "wintermute_otc": {
            "wallet": wm_wallet,
            "explorer": wm_explorer,
            "current_balance_pump": wm_bal,
            "outflow_to_wintermute_tokens": wm_out,
            "wintermute_address": (wm.get("wintermute") or {}).get("address"),
            "not_binance": wm.get("not_binance", True),
            "display": "LARGE HOLDER → WINTERMUTE OTC",
            "status": "PARTIAL",
            "source_label": "Solscan · Wintermute OTC flow",
            "source_url": wm_explorer,
            "freshness": "research-pack",
            "evidence": (
                f"Unattributed wallet currently holds ~{(wm_bal or 0) / 1e9:.2f}B PUMP (not the "
                f"similarly-prefixed Binance hot wallet). ~{wm_out / 1e6:.0f}M PUMP observed "
                "transferred to labelled Wintermute OTC. DEX swaps exist but are not the main "
                "observed behaviour. Inventory source UNKNOWN. Entity UNKNOWN."
            ),
            "interpretation": (
                f"~{wm_out / 1e6:.0f}M PUMP transferred from a large unattributed holder to a "
                "labelled Wintermute OTC wallet. This is important capital-flow evidence, but "
                "OTC interaction does not prove a sale, market dumping or price suppression."
            ),
            "discipline": "OTC INTERACTION ≠ SALE",
            "classification": wm.get("classification"),
        },
        "buyer_quality_source": {
            "source_label": "Helius / Solana DEX sample",
            "source_url": None,  # filled from live buyer sample explorers in UI builders
            "freshness": "research-pack",
        },
        "supply_source": {
            "source_label": "Solscan · PUMP mint / Squads custody",
            "source_url": mint_explorer,
            "freshness": "research-pack",
        },
        "who_selling_source": {
            "source_label": "Solscan · Squads custody + OTC",
            "source_url": wm_explorer,
            "freshness": "research-pack",
        },
        # Canonical UI copy (overrides misleading "vesting/custody" language)
        "headline_compact": f"{unlocked_b:.0f}B unlocked · {wm_out / 1e6:.0f}M → Wintermute OTC",
        "headline_warning": f"{unlocked_b:.0f}B unlocked custody · OTC flow observed",
        "supply_evidence": (
            f"~{unlocked_b:.2f}B July cohort already unlocked into Squads multisig custody. "
            "Streamflow escrow ~0. Beneficial owners and future Squads outflow timing remain UNKNOWN."
        ),
        "supply_interpretation": (
            "The risk is available supply controlled through unidentified multisigs, "
            "not a future Streamflow cliff."
        ),
        "supply_unknown_line": (
            "Beneficial owners of Squads vaults and future Squads outflow timing remain UNKNOWN. "
            "TRANSFER ≠ SALE · custody ≠ sale."
        ),
        "card_read": "ALREADY-UNLOCKED SQUADS CUSTODY",
        "card_copy": (
            f"~{unlocked_b:.2f}B unlocked on Jul 14 into Squads multisigs (Streamflow escrow ~0). "
            "No future Streamflow vesting calendar for this cohort. Selling is not proven."
        ),
        "posture_explanation": (
            "Price and relative strength remain strong and platform economics are healthy. "
            "Capital quality is less clean: observed DEX buying is trader-heavy, July supply is "
            "already unlocked in unidentified Squads custody, and a large unattributed holder has "
            "transferred material PUMP to Wintermute OTC."
        ),
        "who_selling_evidence": (
            f"July: ~{unlocked_b:.2f}B already-unlocked Squads custody (escrow ~0). "
            f"Large holder → Wintermute OTC: ~{wm_out / 1e6:.0f}M PUMP observed "
            f"(wallet holds ~{(wm_bal or 0) / 1e9:.2f}B). "
            "OTC INTERACTION ≠ SALE. Transfer ≠ sale. Custody ≠ sale."
        ),
    }


def load_july_attribution(path: Path | str | None = None) -> dict | None:
    """Final July cohort multi-hop attribution — research pack, no API calls."""
    p = Path(path) if path is not None else JULY_ATTR_PATH
    if not p.exists():
        return None
    raw = json.loads(p.read_text())
    pct = raw.get("pct_of_cohort") or {}
    toks = raw.get("tokens_of_cohort") or {}
    meth = raw.get("methodology") or {}
    notes = raw.get("special_notes") or {}
    unattr = raw.get("unattributed_still_held_top") or []
    custody = float(pct.get("KNOWN_ENTITY") or 0)
    still = float(pct.get("STILL_HELD") or 0)
    unknown = float(pct.get("UNKNOWN") or 0)
    dex = float(pct.get("DEX_SWAP") or 0)
    cex = float(pct.get("CEX_DEPOSIT") or 0)
    wintermute_note = None
    for w, meta in notes.items():
        if isinstance(meta, dict) and meta.get("observed_outflow_to_labelled_wintermute_otc"):
            wintermute_note = {
                "wallet": w,
                "tokens_unattributed_approx": (unattr[0].get("tokens") if unattr else None),
                "pct_approx": (unattr[0].get("pct") if unattr else None),
                "note": meta.get("classification"),
            }
            break

    own = load_ownership_buyer_quality() or {}
    # Prefer ownership-pack copy (already-unlocked Squads) over older vesting/custody phrasing
    headline_compact = own.get("headline_compact") or (
        f"{custody:.0f}% unlocked Squads custody · ~{dex:.0f}% DEX swap"
    )
    headline_who = own.get("who_selling_evidence") or (
        f"July cohort: ~52B already-unlocked Squads custody · ~{dex:.2f}% observed DEX swap "
        f"upper-bound · {cex:.2f}% labelled CEX deposit · {unknown:.2f}% UNKNOWN."
    )
    return {
        "gathered_at": raw.get("gathered_at_utc"),
        "pass": raw.get("pass"),
        "source_path": str(p.relative_to(ROOT)),
        "findings_path": str((JULY_ATTR_DIR / "FINDINGS-ATTRIBUTION.md").relative_to(ROOT))
        if (JULY_ATTR_DIR / "FINDINGS-ATTRIBUTION.md").exists()
        else None,
        "cohort_tokens": meth.get("cohort_tokens") or raw.get("checksum_tokens"),
        "cohort_wallets": meth.get("cohort_wallets") or 80,
        "pct": {
            "KNOWN_ENTITY": custody,
            "STILL_HELD": still,
            "UNKNOWN": unknown,
            "DEX_SWAP": dex,
            "CEX_DEPOSIT": cex,
        },
        "tokens": toks,
        "discipline": meth.get("discipline") or [],
        "label_sources": meth.get("label_sources") or [],
        "top_terminal_wallets": raw.get("top_terminal_wallets") or [],
        "unattributed_still_held_top": unattr,
        "wintermute_related_unattributed": wintermute_note,
        "ownership_buyer_quality": own or None,
        "confidence": "MEDIUM",
        "freshness": own.get("freshness") or "research-pack",
        "source_label": own.get("source_label") or "Solscan · on-chain forensics",
        "source_url": own.get("source_url")
        or "https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
        "headline_compact": headline_compact,
        "headline_warning": own.get("headline_warning") or headline_compact,
        "headline_who_selling": headline_who,
        "headline_full": own.get("supply_evidence")
        or (
            f"July cohort: {custody:.2f}% already-unlocked Squads custody · "
            f"{still:.2f}% unattributed held · ~{dex:.2f}% DEX swap upper-bound · "
            f"{cex:.2f}% labelled CEX."
        ),
        "card_read": own.get("card_read") or "ALREADY-UNLOCKED SQUADS CUSTODY",
        "card_copy": own.get("card_copy")
        or (
            "July Streamflow delivery was same-day unlock into Squads custody. "
            "Escrow ~0. Selling is not proven."
        ),
        "supply_evidence": own.get("supply_evidence"),
        "supply_interpretation": own.get("supply_interpretation"),
        "supply_unknown_line": own.get("supply_unknown_line")
        or (
            "Beneficial owners and future Squads outflow timing remain UNKNOWN. "
            "TRANSFER ≠ SALE · custody ≠ sale."
        ),
        "posture_explanation": own.get("posture_explanation"),
        "first_hop_context": (
            "Historical first-hop only: 79/80 original recipients emptied into downstream wallets "
            "(redistribution — not a sale conclusion)."
        ),
    }
