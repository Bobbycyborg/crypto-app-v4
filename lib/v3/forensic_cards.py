"""PUMP wallet & transaction evidence — compact cards + expandable detail."""

from __future__ import annotations

import html as _html
import re
from typing import Any


def _esc(s: Any) -> str:
    return _html.escape(str(s)) if s is not None else ""


def _fmt_b(tokens: Any) -> str:
    try:
        return f"{float(tokens) / 1e9:.2f}B"
    except (TypeError, ValueError):
        return "—"


def _fmt_tokens_short(tokens: Any) -> str:
    try:
        v = float(tokens)
    except (TypeError, ValueError):
        return "—"
    if abs(v) >= 1e9:
        return f"{v / 1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"{v / 1e6:.1f}M"
    return f"{v:,.0f}"


def _pct(v: Any, *, digits: int = 1) -> str:
    try:
        return f"{float(v):.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def _stat(value: str, label: str, *, muted: bool = False) -> str:
    cls = "fx-stat-v c-muted" if muted else "fx-stat-v"
    return (
        f'<div class="fx-stat"><div class="{cls}">{_esc(value)}</div>'
        f'<div class="fx-stat-l">{_esc(label)}</div></div>'
    )


def _ev_row(k: str, v: str) -> str:
    return f'<div class="fx-ev-row"><div class="fx-ev-k">{_esc(k)}</div><div class="fx-ev-v">{v}</div></div>'


def _details(summary: str, body: str) -> str:
    return (
        f"<details class='fx-details'><summary>{_esc(summary)}</summary>"
        f'<div class="fx-ev">{body}</div></details>'
    )


def _status_cls(status: str | None) -> str:
    s = (status or "").strip().upper()
    if s == "KNOWN":
        return "is-known"
    if s == "UNKNOWN":
        return "is-unknown"
    if s == "PARTIAL":
        return "is-partial"
    if s == "CONFLICT":
        return "is-conflict"
    return "is-muted"


def evidence_card(
    *,
    title: str,
    read: str,
    copy: str,
    tone: str = "orange",
    status: str | None = None,
    kpis: list[tuple[str, str]] | None = None,
    tip_rows: list[tuple[str, str]] | None = None,
    source: str = "UNKNOWN",
    source_url: str | None = None,
    as_of: str | None = None,
    note: str = "",
    confidence: str = "MEDIUM",
) -> str:
    """Reusable evidence card — same grammar as approved BTC/SOL/PUMP cards.

    Status (KNOWN / UNKNOWN / PARTIAL / CONFLICT) is a compact pill, not a
    dump line. Do not delete evidence to pretty the page.
    """
    from lib.v3.route_d_shell import evidence_tip_html

    kpis = kpis or []
    tip_rows = tip_rows or []
    kpi_html = "".join(
        f'<div class="fx-kpi"><strong>{_esc(v)}</strong><span>{_esc(k)}</span></div>'
        for k, v in kpis
        if v
    )
    rows = "".join(_ev_row(k, v) for k, v in tip_rows if v)
    tip = evidence_tip_html(
        name=title,
        read=read,
        rows=tip_rows[:6] or [("Read", read)],
        note=note or copy,
        source=source,
        source_url=source_url,
        as_of=as_of,
        confidence=confidence,
    )
    tone_cls = {"green": "green", "orange": "orange", "muted": "", "grey": ""}.get(tone, "")
    read_tone = "muted" if tone in ("muted", "grey", "") else tone
    pill = ""
    if status:
        pill = (
            f'<span class="fx-status {_status_cls(status)}">{_esc(status)}</span>'
        )
    kpi_block = f'<div class="fx-kpi-row">{kpi_html}</div>' if kpi_html else ""
    detail_body = rows + (f'<div class="fx-ev-note">{_esc(note)}</div>' if note else "")
    detail = _details("View evidence detail", detail_body) if detail_body.strip() else ""
    return (
        f'<section class="fx-card {tone_cls} has-tip">'
        f'<div class="metric-tip-template" hidden>{tip}</div>'
        f'<div class="fx-card-title">{_esc(title)}</div>'
        f'<div class="fx-card-read {read_tone}">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        + kpi_block
        + pill
        + detail
        + "</section>"
    )


def evidence_section(cards: list[str], *, note: str | None = None) -> str:
    note_html = (
        f'<div class="fx-section-note">{_esc(note)}</div>' if note else ""
    )
    return (
        '<section class="sec fx-sec" aria-label="Wallet and transaction evidence">'
        '<h3 class="fx-title">Wallet &amp; transaction evidence</h3>'
        + note_html
        + f'<div class="fx-mini-grid">{"".join(cards)}</div>'
        "</section>"
    )


def _buyer_card(f: dict) -> str:
    bf = f.get("buyer_forensics") or {}
    ow = bf.get("observed_window") or {}
    net_n = ow.get("net_accumulator_count")
    hold_n = ow.get("holding_among_checked_n")
    bal_n = ow.get("balances_checked_n") or 20
    top5 = ow.get("top5_gross_buy_share_pct")
    span = ow.get("span_hours")
    hold_claim = ow.get("holding_claim") or ""

    read = "REAL BUYING · TRADER-HEAVY"
    copy = (
        "Buying exists and is trader-heavy in the top sample. "
        "Do not call current buyers strong/persistent accumulators."
    )
    own = (f.get("july_attribution") or {}).get("ownership_buyer_quality") or {}
    bq = own.get("buyer_quality") or {}
    if bq.get("display"):
        read = bq["display"]
        copy = (
            "Top-sample deep dive is trader-heavy. Sample is short and not market-wide. "
            "Buyer identity remains incomplete."
        )
    if net_n is None:
        read = "BUYER SAMPLE INCOMPLETE"
        copy = "Principal-pool DEX buyer sample is incomplete this run."

    hold_disp = f"{hold_n}/{bal_n}" if hold_n is not None else "—"
    try:
        top5_disp = f"{float(top5):.0f}%"
    except (TypeError, ValueError):
        top5_disp = "—"
    try:
        span_disp = f"~{float(span):.0f}h"
    except (TypeError, ValueError):
        span_disp = "—"

    stats = (
        '<div class="fx-stats">'
        + _stat(str(net_n) if net_n is not None else "—", "Net accumulators")
        + _stat(hold_disp, "Top buyers still hold")
        + _stat(top5_disp, "Top-5 buy share")
        + _stat(span_disp, "Observed window")
        + "</div>"
    )

    nets = ow.get("top_net_accumulators") or bf.get("wallet_profiles_checked") or []
    rows = ""
    shown = 0
    for p in nets:
        if shown >= 8:
            break
        net = p.get("net_tokens")
        if net is None:
            continue
        links = " · ".join(
            f'<a href="{_esc(u)}" target="_blank" rel="noopener">Solscan</a>'
            for u in (p.get("sample_explorer_links") or [])[:2]
        )
        bal = p.get("current_balance_tokens")
        bal_bit = f" · bal {_fmt_tokens_short(bal)}" if bal is not None else ""
        rows += _ev_row(
            f"Wallet {shown + 1}",
            f"<code>{_esc((p.get('wallet') or '')[:10])}…</code> · "
            f"net {_fmt_tokens_short(net)} · buy {_fmt_tokens_short(p.get('gross_buy_tokens'))}"
            f"{bal_bit}"
            + (f" · {links}" if links else ""),
        )
        shown += 1

    rows += _ev_row("Coverage", "Principal-pool SWAP sample only")
    rows += _ev_row("CEX buyers", "Individually unobservable")
    if hold_claim:
        rows += _ev_row("Holding check", _esc(hold_claim))
    if bf.get("verdict"):
        rows += _ev_row("Verdict", _esc(bf.get("verdict")))
    if bf.get("verdict_detail"):
        rows += _ev_row("Detail", _esc(bf.get("verdict_detail")))
    if bf.get("channel_read"):
        rows += _ev_row("Channel", _esc(bf.get("channel_read")))
    # Prefer live Solscan over internal markdown path labels
    sample_url = None
    for p in nets:
        links = p.get("sample_explorer_links") or []
        if links:
            sample_url = links[0]
            break
    if sample_url:
        rows += _ev_row(
            "Evidence source",
            f'<a href="{_esc(sample_url)}" target="_blank" rel="noopener">Solscan · DEX sample tx</a>',
        )
    elif bf.get("evidence_report_path"):
        rows += _ev_row(
            "Evidence source",
            "Helius / Solana DEX sample",
        )

    note = (
        '<div class="fx-ev-note">Observed DEX buying is real evidence. '
        "Current top-sample read is trader-heavy — not strong/persistent accumulation. "
        "Individual CEX buyers remain unobservable.</div>"
    )
    as_of = bf.get("gathered_at") or f.get("gathered_at") or ""
    foot = (
        '<div class="fx-ev-note">Source · Helius / Solana DEX sample'
        + (f" · As of {_esc(as_of)}" if as_of else "")
        + " · Confidence MEDIUM</div>"
    )

    return (
        '<section class="fx-card green">'
        '<div class="fx-card-title">DEX buyer forensics</div>'
        f'<div class="fx-card-read orange">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        f"{stats}"
        + _details("View sample transactions", rows + note + foot)
        + "</section>"
    )


def _july_card(f: dict) -> str:
    rec = f.get("july_reconciliation") or {}
    beh = f.get("july_behaviour") or {}
    dest = f.get("destination_trace") or {}
    attr = f.get("july_attribution") or {}
    pct = attr.get("pct") or {}
    own = attr.get("ownership_buyer_quality") or {}
    wm_full = own.get("wintermute_otc") or {}
    moved = (beh.get("MOVED_DESTINATION_UNKNOWN") or {}).get("count")
    observed = rec.get("observed_recipients")
    tokens = rec.get("observed_tokens") or attr.get("cohort_tokens")

    if pct or own:
        unlocked_b = (own.get("july_unlocked_squads") or {}).get("tokens_b") or 52.04
        stats = (
            '<div class="fx-stats">'
            + _stat(f"~{unlocked_b:.0f}B", "Already unlocked")
            + _stat(f"~{pct.get('DEX_SWAP', 0):.1f}%", "DEX swap upper bound")
            + _stat(f"{pct.get('CEX_DEPOSIT', 0):.2f}%", "Labelled CEX deposit")
            + _stat(f"{pct.get('UNKNOWN', 0):.1f}%", "UNKNOWN")
            + "</div>"
        )
        read = attr.get("card_read") or "ALREADY-UNLOCKED SQUADS CUSTODY"
        copy = attr.get("card_copy") or (
            f"~{unlocked_b:.2f}B unlocked on Jul 14 into Squads multisigs (Streamflow escrow ~0). "
            "No future Streamflow vesting calendar for this cohort. Selling is not proven."
        )
    else:
        moved_disp = f"{moved}/{observed}" if moved is not None and observed else "—"
        stats = (
            '<div class="fx-stats">'
            + _stat(str(observed) if observed is not None else "—", "Observed wallets")
            + _stat(_fmt_b(tokens) if tokens is not None else "—", "PUMP observed")
            + _stat(moved_disp, "Moved onward")
            + _stat("?", "Final destination", muted=True)
            + "</div>"
        )
        read = "MOVED · DESTINATION UNKNOWN"
        copy = "Movement is confirmed. Selling is not."

    rows = ""
    if pct or own:
        rows += _ev_row("Cohort", f"{attr.get('cohort_wallets', 80)} wallets · {_fmt_b(tokens)}")
        rows += _ev_row("Read", "ALREADY-UNLOCKED SQUADS CUSTODY · Streamflow escrow ~0")
        rows += _ev_row(
            "Unattributed still held",
            f"{pct.get('STILL_HELD', 0):.2f}% of cohort",
        )
        rows += _ev_row(
            "Classifications",
            (
                f"KNOWN_ENTITY {pct.get('KNOWN_ENTITY', 0):.2f}% · "
                f"STILL_HELD {pct.get('STILL_HELD', 0):.2f}% · "
                f"DEX_SWAP ~{pct.get('DEX_SWAP', 0):.2f}% · "
                f"CEX_DEPOSIT {pct.get('CEX_DEPOSIT', 0):.2f}% · "
                f"UNKNOWN {pct.get('UNKNOWN', 0):.2f}%"
            ),
        )
        if attr.get("first_hop_context"):
            rows += _ev_row("First-hop context only", _esc(attr.get("first_hop_context")))
        if wm_full.get("evidence"):
            rows += _ev_row(
                "LARGE HOLDER → WINTERMUTE OTC",
                (
                    f"<code>{_esc((wm_full.get('wallet') or '')[:12])}…</code> · "
                    f"{_esc(wm_full['evidence'])} · "
                    f"{_esc(wm_full.get('discipline') or 'OTC INTERACTION ≠ SALE')}"
                ),
            )
        else:
            wm = attr.get("wintermute_related_unattributed") or {}
            if wm.get("wallet"):
                rows += _ev_row(
                    "Unattributed + Wintermute OTC note",
                    f"<code>{_esc(wm['wallet'][:12])}…</code> · {_esc(wm.get('note') or '')}",
                )
        for i, d in enumerate((attr.get("top_terminal_wallets") or [])[:8]):
            lab = d.get("label") or d.get("type") or "unattributed"
            rows += _ev_row(
                f"Terminal {i + 1}",
                f"<code>{_esc((d.get('wallet') or '')[:10])}…</code> · "
                f"{_fmt_tokens_short(d.get('tokens'))} PUMP · {_esc(lab)}"
                + (
                    f' · <a href="{_esc(d.get("explorer"))}" target="_blank" rel="noopener">Solscan</a>'
                    if d.get("explorer")
                    else ""
                ),
            )
    else:
        for i, d in enumerate((dest.get("top_destinations") or [])[:8]):
            tok = d.get("total_tokens_received", 0)
            ex = d.get("sample_explorer")
            link = f' · <a href="{_esc(ex)}" target="_blank" rel="noopener">Solscan</a>' if ex else ""
            rows += _ev_row(
                f"Traced {i + 1}",
                f"<code>{_esc((d.get('destination_wallet') or '')[:10])}…</code> · "
                f"{_fmt_tokens_short(tok)} PUMP{link}",
            )

    for fl in (f.get("important_flows") or [])[:5]:
        ex = fl.get("explorer")
        link = f' · <a href="{_esc(ex)}" target="_blank" rel="noopener">Solscan</a>' if ex else ""
        rows += _ev_row(
            "Distribution tx",
            f"{_fmt_tokens_short(fl.get('amount_tokens'))} PUMP → "
            f"<code>{_esc((fl.get('recipient') or '')[:10])}…</code>"
            + (f" · {_esc(fl.get('timestamp_utc'))}" if fl.get("timestamp_utc") else "")
            + link,
        )

    if rec.get("reported_recipients") is not None and rec.get("reported_tokens") is not None:
        rows += _ev_row(
            "Secondary report",
            f"{rec.get('reported_recipients')} wallets · {_fmt_b(rec.get('reported_tokens'))}",
        )
    if rec.get("gap_recipients") is not None and rec.get("gap_tokens") is not None:
        rows += _ev_row(
            "Gap",
            f"{rec.get('gap_recipients')} wallets · {_fmt_b(rec.get('gap_tokens'))}",
        )
    if dest.get("traced_moved_recipients") is not None:
        rows += _ev_row("Traced moved recipients (first-hop)", str(dest.get("traced_moved_recipients")))
    if dest.get("note"):
        rows += _ev_row("Trace note", _esc(dest.get("note")))
    if rec.get("event_window_utc"):
        rows += _ev_row("Event window", _esc(rec.get("event_window_utc")))
    for gx in (rec.get("gap_explanations") or [])[:4]:
        rows += _ev_row("Caveat", _esc(gx))
    if f.get("repeat_player_summary"):
        rows += _ev_row("Repeat players", _esc(f.get("repeat_player_summary")))
    if attr.get("source_path") or attr.get("findings_path") or own:
        mint = own.get("mint_explorer") or own.get("source_url") or (
            "https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn"
        )
        rows += _ev_row(
            "Evidence source",
            f'<a href="{_esc(mint)}" target="_blank" rel="noopener">Solscan · PUMP mint</a>',
        )
        if wm_full.get("explorer") or wm_full.get("wallet"):
            wurl = wm_full.get("explorer") or (
                f"https://solscan.io/account/{wm_full.get('wallet')}"
            )
            rows += _ev_row(
                "Wintermute OTC evidence",
                f'<a href="{_esc(wurl)}" target="_blank" rel="noopener">'
                "Solscan · large holder wallet</a>",
            )
    if f.get("snapshot_id"):
        rows += _ev_row("Snapshot", f"<code>{_esc(f.get('snapshot_id'))}</code>")
    if f.get("evidence_pack_path"):
        # Prefer live Solscan over internal pack path labels
        rows += _ev_row(
            "Evidence pack",
            f'<a href="{_esc(own.get("mint_explorer") or "https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn")}" '
            'target="_blank" rel="noopener">Solscan · on-chain forensics</a>',
        )

    note = (
        '<div class="fx-ev-note">TRANSFER ≠ SALE · CEX DEPOSIT ≠ SALE · '
        "custody ≠ sale · OTC INTERACTION ≠ SALE. "
        "Already-unlocked Squads custody ≠ sold. "
        "79/80 moved is first-hop redistribution context only — not the current conclusion.</div>"
    )
    conf = attr.get("confidence") or rec.get("confidence") or "MEDIUM"
    as_of = own.get("gathered_at") or attr.get("gathered_at") or f.get("gathered_at") or ""
    fresh = own.get("freshness") or attr.get("freshness") or "research-pack"
    foot = (
        '<div class="fx-ev-note">Source · '
        f'<a href="{_esc(own.get("source_url") or own.get("mint_explorer") or "https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn")}" '
        'target="_blank" rel="noopener">Solscan · on-chain forensics</a>'
        + (f" · As of {_esc(as_of)}" if as_of else "")
        + f" · Freshness {_esc(fresh)}"
        + f" · Confidence {_esc(conf)}</div>"
    )

    return (
        '<section class="fx-card orange">'
        '<div class="fx-card-title">July supply cohort</div>'
        f'<div class="fx-card-read orange">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        f"{stats}"
        + _details("View cohort evidence", rows + note + foot)
        + "</section>"
    )


def _provenance_foot(
    *,
    source: str,
    source_url: str | None = None,
    as_of: str | None = None,
    freshness: str | None = None,
    confidence: str | None = None,
) -> str:
    src = _esc(source)
    if source_url:
        src = f'<a href="{_esc(source_url)}" target="_blank" rel="noopener">{src}</a>'
    bits = [f"Source · {src}"]
    if as_of:
        bits.append(f"As of {_esc(as_of)}")
    if freshness:
        bits.append(f"Freshness {_esc(freshness)}")
    if confidence:
        bits.append(f"Confidence {_esc(confidence)}")
    return f'<div class="fx-ev-note">{" · ".join(bits)}</div>'


def _mint_authority_display(sup: dict) -> tuple[str, str]:
    """NULL only when the mint_authority field is present and verified null."""
    if "mint_authority" not in sup:
        return "UNKNOWN", "c-muted"
    val = sup.get("mint_authority")
    if val is None or str(val).strip().lower() in ("null", "none", ""):
        return "NULL", "c-green"
    return str(val), "c-muted"


def _usd_token_to_float(token: str) -> float | None:
    m = re.match(r"\$([0-9.]+)([KMB])?", token.strip())
    if not m:
        return None
    v = float(m.group(1))
    mult = {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2) or ""]
    return v * mult


def _fees_from_history_line(line: str) -> float | None:
    m = re.search(r"fees\s+(\$[0-9.]+[KMB]?)/d", line)
    if not m:
        return None
    return _usd_token_to_float(m.group(1))


def _platform_read(fee_lines: list[str]) -> tuple[str, str, str]:
    """Derive platform headline from Now vs June ATL fees. UNKNOWN if incomplete."""
    now_f = atl_f = None
    for line in fee_lines or []:
        s = str(line)
        if s.startswith("Now:"):
            now_f = _fees_from_history_line(s)
        elif s.startswith("June ATL:"):
            atl_f = _fees_from_history_line(s)
    if now_f is None or atl_f is None:
        return (
            "UNKNOWN",
            "muted",
            "Fee history windows are incomplete — recovery versus ATL cannot be confirmed.",
        )
    if now_f > atl_f:
        return (
            "RECOVERED VS ATL",
            "green",
            "Current economics are materially above the June low, but below prior peak conditions.",
        )
    if now_f < atl_f:
        return (
            "NOT RECOVERED VS ATL",
            "orange",
            "Current fees are not above the June ATL window.",
        )
    return (
        "FLAT VS ATL",
        "muted",
        "Current fees match the June ATL window.",
    )


def _stress_read(stress: dict) -> tuple[str, str, str]:
    """Derive stress headline from PUMP/BTC RS counts. UNKNOWN if incomplete."""
    n = stress.get("n_selected_windows")
    btc = stress.get("pump_btc_rs_positive_count")
    if btc is None or n is None or not isinstance(n, int) or n <= 0:
        return (
            "UNKNOWN",
            "muted",
            "Stress sample is incomplete this run.",
        )
    if btc == 0:
        return (
            "WEAK VS BTC IN STRESS",
            "orange",
            "In the selected stress sample, PUMP did not show defensive relative strength versus BTC.",
        )
    if btc < n:
        return (
            "MIXED VS BTC IN STRESS",
            "orange",
            f"In the selected stress sample, PUMP/BTC RS improved in {btc}/{n} windows.",
        )
    return (
        "IMPROVED VS BTC IN STRESS",
        "green",
        f"In the selected stress sample, PUMP/BTC RS improved in {btc}/{n} windows.",
    )


def _supply_card(s1: dict) -> str:
    sup = s1.get("supply") or {}
    circ = sup.get("circulating_pct")
    sched = sup.get("schedule_unlocked_pct")
    minted = sup.get("on_chain_minted_pct")
    aug = sup.get("august_discrepancy") or {}
    mint_auth, mint_cls = _mint_authority_display(sup)
    recon = (sup.get("reconciliation") or "UNKNOWN").upper()

    def _pct_face(v: Any) -> str:
        try:
            return f"{float(v):g}%"
        except (TypeError, ValueError):
            return "—"

    metrics = (
        '<div class="fx-supply-metrics">'
        f'<div class="fx-supply-metric"><div class="big">{_esc(_pct_face(circ))}</div>'
        f'<div class="label">Circulating</div></div>'
        f'<div class="fx-supply-metric"><div class="big">{_esc(_pct_face(sched))}</div>'
        f'<div class="label">Schedule unlocked</div></div>'
        f'<div class="fx-supply-metric"><div class="big">{_esc(_pct_face(minted))}</div>'
        f'<div class="label">On-chain minted</div></div>'
        "</div>"
    )
    status = (
        '<div class="fx-status-row">'
        f'<div class="fx-status"><span>Mint authority</span><strong class="{mint_cls}">{_esc(mint_auth)}</strong></div>'
        f'<div class="fx-status"><span>Supply reconciliation</span><strong class="c-muted">{_esc(recon)}</strong></div>'
        "</div>"
    )
    callout = ""
    if aug.get("tokenomics_b") is not None and aug.get("defillama_b") is not None:
        callout = (
            '<div class="fx-callout"><div>'
            '<div class="label">August schedule mismatch</div>'
            '<div class="fx-tiny" style="margin-top:4px">Different providers disagree on scheduled amount.</div>'
            "</div>"
            f'<div class="value">{_esc(aug["tokenomics_b"])}B vs {_esc(aug["defillama_b"])}B</div>'
            "</div>"
        )

    mint_ev = (
        "Null — additional minting is not possible"
        if mint_auth == "NULL"
        else "Mint authority not verified this run"
    )
    rows = (
        _ev_row("Circulating", "CoinGecko estimate of supply currently circulating")
        + _ev_row("Schedule unlocked", "Tokenomics schedule — not proof of distribution or sale")
        + _ev_row("On-chain minted", "Actual Solana mint supply")
        + _ev_row("Mint authority", mint_ev)
    )
    if mint_auth == "NULL" and sup.get("unminted_below_max_b") is not None:
        um = str(sup.get("unminted_below_max_b"))
        rows += _ev_row(
            "Unmintable remainder",
            f"≈{_esc(um)} nominal max minus current supply — cannot now be minted",
        )
    if aug.get("note"):
        rows += _ev_row("August note", _esc(aug.get("note")))
    if sup.get("reconciliation_note"):
        rows += _ev_row("Reconciliation", _esc(sup.get("reconciliation_note")))
    if sup.get("mint_explorer"):
        rows += _ev_row(
            "Mint",
            f'<a href="{_esc(sup.get("mint_explorer"))}" target="_blank" rel="noopener">Solscan token</a>',
        )

    note = (
        '<div class="fx-ev-note">Unlocked ≠ liquid ≠ sold. '
        "Vesting/unlocks transfer already-minted allocation; they do not create new tokens.</div>"
    )
    foot = _provenance_foot(
        source="CoinGecko / Tokenomics / Solana RPC",
        source_url=sup.get("mint_explorer"),
        as_of=sup.get("fetched_at"),
        freshness="stage1 supply snapshot",
        confidence="MEDIUM",
    )

    return (
        '<section class="fx-card supply">'
        '<div class="fx-supply-head"><div>'
        '<div class="fx-card-title">Supply picture</div>'
        '<div class="fx-card-read orange">MEASURABLE · NOT FULLY RECONCILED</div>'
        "</div>"
        '<div class="fx-card-copy">Three different supply concepts are being measured. '
        "They should not be treated as the same number.</div></div>"
        f"{metrics}{status}{callout}"
        + _details("Why these numbers differ", rows + note + foot)
        + "</section>"
    )


def _parse_fee_now(lines: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in lines or []:
        if not str(line).startswith("Now:"):
            continue
        m_fees = re.search(r"fees\s+(\$[0-9.]+[KMB]?/d)", line)
        m_rev = re.search(r"rev\s+(\$[0-9.]+[KMB]?/d)", line)
        m_burn = re.search(r"buyback/burn\s+(\$[0-9.]+[KMB]?/d)", line)
        if m_fees:
            out["fees"] = m_fees.group(1)
        if m_rev:
            out["rev"] = m_rev.group(1)
        if m_burn:
            out["burn"] = m_burn.group(1)
    return out


def _platform_card(s1: dict) -> str:
    plat = s1.get("platform") or {}
    fee_lines = plat.get("fee_revenue_buyback_history") or []
    share_h = plat.get("launchpad_fee_share_history") or {}
    now = _parse_fee_now(fee_lines)
    aug10 = share_h.get("aug_10_pct")
    aug_disp = _pct(aug10) if aug10 is not None else "—"
    read, tone, copy = _platform_read(fee_lines)

    kpis = (
        '<div class="fx-kpi-row">'
        f'<div class="fx-kpi"><strong>{_esc(now.get("fees", "—"))}</strong><span>Fees now</span></div>'
        f'<div class="fx-kpi"><strong>{_esc(now.get("rev", "—"))}</strong><span>Revenue now</span></div>'
        f'<div class="fx-kpi"><strong>{_esc(now.get("burn", "—"))}</strong><span>Buyback / burn</span></div>'
        f'<div class="fx-kpi"><strong>{_esc(aug_disp)}</strong><span>Aug 10 fee share</span></div>'
        "</div>"
    )

    rows = ""
    for line in fee_lines:
        s = str(line)
        if ":" in s and not s.startswith("Now:"):
            label, rest = s.split(":", 1)
            rows += _ev_row(label.strip(), _esc(rest.strip()))
    if share_h.get("ath_sep_pct") is not None:
        rows += _ev_row(
            "Fee share history",
            _esc(
                f"ATH Sep {_pct(share_h.get('ath_sep_pct'))} · Jan {_pct(share_h.get('jan_high_pct'))} · "
                f"June ATL {_pct(share_h.get('june_atl_pct'))} · Aug 10 {_pct(share_h.get('aug_10_pct'))}"
            ),
        )
    elif plat.get("display_share_history"):
        rows += _ev_row("Fee share history", _esc(plat.get("display_share_history")))
    if plat.get("interpretation"):
        rows += _ev_row("Interpretation", _esc(plat.get("interpretation")))
    rows += _ev_row(
        "BOOST (not a PUMP buyback)",
        "Pump.fun BOOST recycles dead launch liquidity into buybacks of the *launched* token. "
        "Do not count BOOST as a PUMP buyback or PUMP burn. Indirect only: better launches → maybe more "
        "platform activity/revenue → maybe larger PUMP buybacks. That chain is not proven.",
    )

    note = (
        '<div class="fx-ev-note">Platform activity supports the project thesis. '
        "It does not prove price causation.</div>"
    )
    as_of = share_h.get("as_of")
    if not as_of and share_h.get("coverage"):
        cov = str(share_h.get("coverage"))
        as_of = cov.split("→")[-1].strip() if "→" in cov else cov
    foot = _provenance_foot(
        source=share_h.get("source") or "DefiLlama",
        source_url=share_h.get("source_url") or "https://defillama.com/protocol/fees/pump.fun",
        as_of=as_of,
        freshness=share_h.get("coverage"),
        confidence=plat.get("confidence") or "MEDIUM",
    )

    return (
        '<section class="fx-card green">'
        '<div class="fx-card-title">Platform history</div>'
        f'<div class="fx-card-read {tone}">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        f"{kpis}"
        + _details("View historical windows", rows + note + foot)
        + "</section>"
    )


def _stress_card(s1: dict) -> str:
    stress = s1.get("stress") or {}
    n = stress.get("n_selected_windows")
    btc = stress.get("pump_btc_rs_positive_count")
    sol = stress.get("pump_sol_rs_positive_count")
    btc_disp = f"{btc}/{n}" if btc is not None and n is not None else "—"
    sol_disp = f"{sol}/{n}" if sol is not None and n is not None else "—"
    read, tone, copy = _stress_read(stress)

    kpis = (
        '<div class="fx-kpi-row">'
        f'<div class="fx-kpi"><strong>{_esc(btc_disp)}</strong><span>PUMP/BTC RS improved</span></div>'
        f'<div class="fx-kpi"><strong>{_esc(sol_disp)}</strong><span>PUMP/SOL RS improved</span></div>'
        "</div>"
    )
    tiny = (
        '<div class="fx-sep"></div>'
        '<div class="fx-tiny"><strong>Launches / graduations / users</strong> → UNKNOWN</div>'
    )

    cov = stress.get("coverage") or {}
    rows = (
        _ev_row("Sample", f"{n or '—'} selected, non-overlapping 7d stress windows")
        + _ev_row("Selection", "BTC or SOL return ≤ −10%")
        + _ev_row("Use", "Research evidence only")
        + _ev_row("Method", _esc(stress.get("method") or "CoinGecko daily stress windows"))
    )
    if cov.get("first") and cov.get("last"):
        rows += _ev_row("Coverage", _esc(f"{cov.get('first')} → {cov.get('last')}"))
    if stress.get("inference"):
        rows += _ev_row("Inference", _esc(stress.get("inference")))
    note = (
        '<div class="fx-ev-note">This is research evidence only — not a classifier threshold '
        "and should not be turned into a live trading rule without backtesting.</div>"
    )
    as_of = cov.get("last")
    freshness = None
    if cov.get("first") and cov.get("last"):
        freshness = f"{cov.get('first')} → {cov.get('last')}"
    elif cov.get("n_days") is not None:
        freshness = f"{cov.get('n_days')}d window"
    foot = _provenance_foot(
        source=stress.get("source") or "CoinGecko daily",
        source_url="https://www.coingecko.com/en/coins/pump-fun",
        as_of=as_of,
        freshness=freshness,
        confidence=stress.get("confidence") or "MEDIUM",
    )

    return (
        '<section class="fx-card">'
        '<div class="fx-card-title">Stress behaviour</div>'
        f'<div class="fx-card-read {tone}">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        f"{kpis}{tiny}"
        + _details("View research method", rows + note + foot)
        + "</section>"
    )


def _usd_k(n: Any) -> str:
    try:
        v = float(n)
    except (TypeError, ValueError):
        return "—"
    if abs(v) >= 1e6:
        return f"${v/1e6:.1f}M"
    if abs(v) >= 1e3:
        return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def _buyback_card(intel: dict) -> str:
    amd = intel.get("amendment") or {}
    buy = amd.get("buyback") or {}
    pol = amd.get("policy") or {}
    absb = amd.get("absorption") or {}
    burn = amd.get("supply_burn") or {}
    if not buy:
        return ""
    latest = buy.get("latest_daily_usd")
    d7 = buy.get("total_7d_usd")
    wow = buy.get("wow_pct")
    lo = buy.get("daily_min_7d_usd")
    hi = buy.get("daily_max_7d_usd")
    tok_d = buy.get("pump_bought_latest_day_est")
    tok_7 = buy.get("pump_bought_7d_est")
    gone = burn.get("pct_of_max_gone")
    stats = (
        '<div class="fx-stats">'
        + _stat(_usd_k(latest) + "/d", "Latest buyback")
        + _stat(_usd_k(d7) + "/wk", "7-day buyback")
        + _stat(f"{tok_d/1e6:.0f}M" if tok_d else "—", "PUMP bought (est.)")
        + _stat(f"{gone:.1f}%" if gone is not None else "—", "on-chain supply gap vs 1T*")
        + "</div>"
    )
    read = "~50% REV → BUYBACK → BURN"
    copy = (
        (pol.get("allocation") or "~50% of parent net revenue → open-market PUMP purchases → burn")
        + " Locked ~through April 2027. After that, continuation is discretionary. Not 100% of revenue. "
        "Buybacks being active ≠ price must rise."
    )
    rows = ""
    rows += _ev_row("Policy", _esc(pol.get("allocation") or ""))
    rows += _ev_row("Lock", "Start ~29 Apr 2026 · through ~Apr 2027 · then discretionary")
    rows += _ev_row(
        "7d range",
        f"{_usd_k(lo)}–{_usd_k(hi)}/d"
        + (f" · 7d {wow:+.0f}% vs prior week" if wow is not None else ""),
    )
    if tok_7:
        rows += _ev_row("PUMP bought 7d (est.)", f"{tok_7/1e9:.2f}B at live price — estimate, not a proven burn count")
    rows += _ev_row(
        "vs August drip",
        (
            f"August scheduled 6.875B vs latest-day buyback ~{(tok_d or 0)/1e6:.0f}M PUMP. "
            f"~{absb.get('days_to_absorb_august_drip_at_latest_day'):.0f} days to match the August drip at the latest print. "
            "Do not use a rolling-30d window — the July cliff falls out and absorption looks too strong."
            if absb.get("days_to_absorb_august_drip_at_latest_day")
            else "UNKNOWN"
        ),
    )
    rows += _ev_row(
        "Cumulative gap vs 1T",
        f"{_fmt_b(burn.get('burned_or_unminted_ui'))} ({gone:.1f}% of max) — mixes burns and never-minted residual",
    )
    rows += _ev_row("Source", "DefiLlama holdersRevenue (on-chain burns) · policy from Pump.fun Apr 2026 announcement")
    note = (
        '<div class="fx-ev-note">*1T minus on-chain supply is not a pure burn tally. '
        "Observed holdersRevenue/price is an estimate of PUMP bought.</div>"
    )
    foot = _provenance_foot(
        source="defillama holdersRevenue + Solana getTokenSupply",
        source_url=buy.get("source_url") or "https://defillama.com/protocol/fees/pump.fun",
        as_of=amd.get("fetched_at_utc"),
        freshness="as_of-dated",
        confidence="MEDIUM",
    )
    return (
        '<section class="fx-card green">'
        '<div class="fx-card-title">Value capture — buyback / burn</div>'
        f'<div class="fx-card-read">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        f"{stats}"
        + _details("Policy, live prints, vs unlocks", rows + note + foot)
        + "</section>"
    )


def _unlock_flow_card(intel: dict) -> str:
    amd = intel.get("amendment") or {}
    u = amd.get("unlocks") or {}
    if not u:
        return ""
    jul = u.get("july_cliff") or {}
    aug = u.get("august_drip") or {}
    sep = u.get("september") or {}
    com = u.get("community_tbd") or {}
    probe_n = 82
    probe_b = 4.37
    stats = (
        '<div class="fx-stats">'
        + _stat("~82.5B", "July cliff (scheduled)")
        + _stat("6.875B", "August drip (DefiLlama)")
        + _stat("UNRESOLVED", "September amount")
        + _stat("~240B", "Community TBD")
        + "</div>"
    )
    read = "JULY CLIFF ≠ MONTHLY DRIP"
    copy = (
        "July was a one-off cliff, not the normal monthly unlock. August is the drip. "
        "Aug 12 and Aug 15 are one unlock/distribution event, not two. Transfer ≠ sale. Unlock ≠ dump."
    )
    rows = ""
    rows += _ev_row(
        "July cliff",
        (
            f"Scheduled ~{jul.get('linear_schedule_tokens', 82.5e9)/1e9:.1f}B "
            f"(team 50B + investors 32.5B). DefiLlama print {jul.get('defillama_tokens', 0)/1e9:.2f}B. "
            f"On-chain observed ~52.04B into Squads. Scheduled ≠ distributed. ~121 July-associated wallets still monitored."
        ),
    )
    rows += _ev_row(
        "August drip",
        (
            f"DefiLlama 6.875B (team 4.167B + investors 2.708B) / ~${(aug.get('usd_at_live') or 0)/1e6:.0f}M at live price. "
            "Unlock date 12 Aug. Movement observed 15 Aug — same event."
        ),
    )
    rows += _ev_row(
        "Where August tokens went",
        (
            f"GsM3 sample 12–16 Aug (Helius, 100-tx cap): {probe_n} recipients · {probe_b:.2f}B PUMP. "
            "Several destinations are labelled Squads vaults. Claimed 125 wallets / 4.94B not fully counted this pass. "
            "72h CEX/DEX/OTC flow: UNKNOWN. Transfer ≠ sale."
        ),
    )
    rows += _ev_row(
        "September",
        (
            f"~12 Sep 2026. Linear/DefiLlama {sep.get('linear_defillama_tokens', 0)/1e9:.3f}B. "
            f"Tokenomics.com {sep.get('tokenomics_tokens', 0)/1e9:.2f}B. "
            f"{sep.get('status')}. Both numbers shown — not collapsed."
        ),
    )
    rows += _ev_row(
        "Community allocation",
        (
            f"~{com.get('tokens', 240e9)/1e9:.0f}B ({com.get('pct_of_max')}% of 1T) still TBD / unresolved. "
            "Future supply uncertainty — not immediate circulating supply."
        ),
    )
    note = (
        '<div class="fx-ev-note">Price surviving an unlock ≠ proof unlocked tokens were not sold. '
        "CEX deposit ≠ sale. OTC ≠ sale.</div>"
    )
    foot = _provenance_foot(
        source="DefiLlama unlocks + Tokenomics.com + Helius GsM3 sample",
        source_url="https://defillama.com/unlocks/pump",
        as_of=amd.get("fetched_at_utc"),
        freshness="as_of-dated",
        confidence="MEDIUM",
    )
    return (
        '<section class="fx-card orange">'
        '<div class="fx-card-title">Unlock calendar + destination</div>'
        f'<div class="fx-card-read orange">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        f"{stats}"
        + _details("July vs August vs September", rows + note + foot)
        + "</section>"
    )


def _holder_class_card(intel: dict) -> str:
    amd = intel.get("amendment") or {}
    holders = (amd.get("holders") or {}).get("accounts") or []
    if not holders:
        return ""
    counts: dict[str, int] = {}
    for h in holders:
        counts[h.get("class") or "UNKNOWN"] = counts.get(h.get("class") or "UNKNOWN", 0) + 1
    unknown = [h for h in holders if h.get("class") == "UNKNOWN_holder"]
    stats = (
        '<div class="fx-stats">'
        + _stat(str(counts.get("protocol_custodian", 0)), "Protocol / infra")
        + _stat(str(counts.get("vesting_vault", 0)), "Vesting vault")
        + _stat(str(counts.get("cex_inventory", 0)), "CEX inventory")
        + _stat(str(len(unknown)), "UNKNOWN holder")
        + "</div>"
    )
    read = "INFRA ≠ WHALES"
    copy = (
        "Largest accounts are classified. Protocol, CEX, vesting, and LP wallets are not individual whales. "
        "UNKNOWN round-size wallets (~25B, 25B, 24B, 23B, and ~19.13B plus larger) need watching."
    )
    rows = ""
    for h in holders[:12]:
        own = h.get("owner") or ""
        lab = h.get("label") or h.get("class")
        rows += _ev_row(
            f"{h.get('ui_b'):.2f}B {h.get('class')}",
            f"<code>{_esc(own[:12])}…</code> · {_esc(lab)}"
            + (
                f' · <a href="https://solscan.io/account/{_esc(own)}" target="_blank" rel="noopener">Solscan</a>'
                if own
                else ""
            ),
        )
    note = '<div class="fx-ev-note">Protocol/CEX/vesting wallets ≠ whales. Transfer ≠ sale.</div>'
    foot = _provenance_foot(
        source="Solana getTokenLargestAccounts + known-cex-wallets.json",
        source_url="https://solscan.io/token/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
        as_of=amd.get("fetched_at_utc"),
        freshness="as_of-dated",
        confidence="MEDIUM",
    )
    return (
        '<section class="fx-card">'
        '<div class="fx-card-title">Holder classification</div>'
        f'<div class="fx-card-read orange">{_esc(read)}</div>'
        f'<div class="fx-card-copy">{_esc(copy)}</div>'
        f"{stats}"
        + _details("Largest accounts", rows + note + foot)
        + "</section>"
    )


def render_pump_forensic_section(intel: dict) -> str:
    """Approved wallet & transaction evidence redesign — conclusion first, detail expandable."""
    f = intel.get("forensics") or {}
    s1 = intel.get("stage1_evidence") or {}
    amd = intel.get("amendment") or {}
    if not f and not s1 and not amd:
        return ""

    capture = _buyback_card(intel)
    unlock = _unlock_flow_card(intel)
    holders = _holder_class_card(intel)
    top = f'<div class="fx-grid-2">{_buyer_card(f)}{_july_card(f)}</div>' if f else ""
    supply = _supply_card(s1) if s1.get("supply") else ""
    bottom = ""
    if s1.get("platform") or s1.get("stress"):
        bottom = f'<div class="fx-mini-grid">{_platform_card(s1)}{_stress_card(s1)}</div>'

    parts = []
    if capture or unlock:
        parts.append(f'<div class="fx-grid-2">{capture}{unlock}</div>')
    if holders:
        parts.append('<div class="fx-gap"></div>' + holders)
    if top:
        parts.append(('<div class="fx-gap"></div>' if parts else "") + top)
    if supply:
        parts.append('<div class="fx-gap"></div>' + supply)
    if bottom:
        parts.append('<div class="fx-gap"></div>' + bottom)

    return (
        '<section class="sec fx-sec" aria-label="Wallet and transaction evidence">'
        '<h3 class="fx-title">Wallet &amp; transaction evidence</h3>'
        '<div class="fx-section-note">Compact conclusions first. Raw wallets, transactions '
        "and methodology stay available underneath.</div>"
        + "".join(parts)
        + "</section>"
    )


# Theme-aware CSS — match approved mockup; prefix fx- to avoid collisions
FORENSIC_CSS = """
.fx-sec { margin-top: 0; }
.fx-title {
  margin: 0 0 0.55rem;
  font-family: var(--display);
  font-weight: 700;
  font-size: 1.85rem;
  line-height: 1.05;
  letter-spacing: 0.01em;
}
.fx-section-note {
  color: var(--muted);
  font-size: 0.72rem;
  margin: -0.1rem 0 0.85rem;
}
.fx-grid-2, .fx-mini-grid, .fx-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; }
.fx-gap { height: 12px; }
.fx-card {
  background: var(--surface);
  border-radius: 14px;
  padding: 18px 20px 16px;
}
.fx-card.green { background: #e7efeb; }
.fx-card.orange, .fx-card.supply { background: #efe8ea; }
[data-theme="dark"] .fx-card.green { background: #2f3c3d; }
[data-theme="dark"] .fx-card.orange { background: #38363d; }
[data-theme="dark"] .fx-card.supply { background: #39363e; }
.fx-card-title {
  font-family: var(--display);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
.fx-card-read {
  margin-top: 5px;
  font-family: var(--display);
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.15;
}
.fx-card-read.green { color: var(--green); }
.fx-card-read.orange { color: var(--orange); }
.fx-card-read.muted { color: var(--muted); }
.fx-card-copy {
  margin-top: 5px;
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.4;
  max-width: 42rem;
}
.fx-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 12px;
}
.fx-stat {
  background: rgba(0,0,0,0.04);
  border-radius: 10px;
  padding: 8px 10px;
  min-width: 0;
}
[data-theme="dark"] .fx-stat { background: rgba(255,255,255,0.035); }
.fx-stat-v {
  font-family: var(--display);
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.1;
}
.fx-stat-l {
  color: var(--muted);
  font-size: 0.6rem;
  line-height: 1.25;
  margin-top: 3px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.fx-details {
  margin-top: 12px;
  border-top: 1px solid rgba(150,154,172,0.16);
  padding-top: 9px;
}
.fx-details summary {
  cursor: pointer;
  color: var(--link, #5a7a9a);
  font-size: 0.72rem;
  font-weight: 700;
  list-style: none;
  display: flex;
  align-items: center;
  gap: 6px;
}
[data-theme="dark"] .fx-details summary { color: #b8d4f0; }
.fx-details summary::-webkit-details-marker { display: none; }
.fx-details summary:before {
  content: "＋";
  font-family: var(--display);
  color: var(--muted);
  font-size: 0.85rem;
}
.fx-details[open] summary:before { content: "−"; }
.fx-ev {
  margin-top: 10px;
  background: rgba(0,0,0,0.04);
  border-radius: 10px;
  padding: 11px 12px;
}
[data-theme="dark"] .fx-ev { background: #242832; }
.fx-ev-row {
  display: grid;
  grid-template-columns: 112px 1fr;
  gap: 6px 10px;
  font-size: 0.72rem;
  line-height: 1.4;
  padding: 3px 0;
}
.fx-ev-k { color: var(--muted); font-weight: 600; }
.fx-ev-v { color: var(--ink); word-break: break-word; }
.fx-ev-v a { color: inherit; text-decoration: underline; text-underline-offset: 2px; }
.fx-ev-note {
  border-top: 1px solid rgba(150,154,172,0.14);
  margin-top: 8px;
  padding-top: 8px;
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.4;
}
.fx-supply-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-end;
}
.fx-supply-head .fx-card-copy { margin: 0; max-width: 32rem; text-align: right; }
.fx-supply-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 12px;
}
.fx-supply-metric {
  background: rgba(0,0,0,0.04);
  border-radius: 10px;
  padding: 10px 12px;
}
[data-theme="dark"] .fx-supply-metric { background: rgba(255,255,255,0.035); }
.fx-supply-metric .big {
  font-family: var(--display);
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.1;
}
.fx-supply-metric .label {
  margin-top: 3px;
  color: var(--muted);
  font-size: 0.6rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.fx-status-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 8px;
}
.fx-status {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  border-radius: 10px;
  padding: 8px 12px;
  background: rgba(0,0,0,0.035);
}
[data-theme="dark"] .fx-status { background: rgba(255,255,255,0.028); }
.fx-status span:first-child {
  color: var(--muted);
  font-size: 0.85rem;
  font-weight: 600;
  line-height: 1.2;
}
.fx-status strong {
  font-family: var(--display);
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  line-height: 1.2;
}
.fx-callout {
  margin-top: 8px;
  border: 1px solid rgba(232,163,92,0.28);
  background: rgba(232,163,92,0.10);
  border-radius: 10px;
  padding: 9px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.fx-callout .label {
  font-family: var(--display);
  color: var(--orange);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.fx-callout .value {
  font-family: var(--display);
  font-size: 0.85rem;
  font-weight: 700;
  white-space: nowrap;
}
.fx-kpi-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-top: 12px;
}
.fx-kpi {
  border-radius: 10px;
  background: rgba(0,0,0,0.04);
  padding: 8px 10px;
}
[data-theme="dark"] .fx-kpi { background: rgba(255,255,255,0.035); }
.fx-kpi strong {
  display: block;
  font-family: var(--display);
  font-size: 0.88rem;
  font-weight: 700;
  line-height: 1.15;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.fx-kpi span {
  display: block;
  color: var(--muted);
  font-size: 0.6rem;
  margin-top: 3px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.fx-tiny {
  margin-top: 10px;
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.35;
}
.fx-tiny strong { color: var(--ink); }
.fx-sep {
  margin: 10px 0 0;
  height: 1px;
  background: rgba(150,154,172,0.14);
}
.fx-status {
  display: inline-flex;
  align-items: center;
  margin-top: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: rgba(150,154,172,0.16);
  color: var(--muted);
  line-height: 1.3;
}
.fx-status.is-known { background: var(--green-wash); color: var(--green); }
.fx-status.is-partial, .fx-status.is-conflict { background: var(--orange-wash, #efe8ea); color: var(--orange); }
.fx-status.is-unknown, .fx-status.is-muted { background: rgba(150,154,172,0.16); color: var(--muted); }
.split { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
.band { min-width: 0; }
.band-token { background: var(--red-wash); }
.band-status {
  white-space: normal;
  overflow-wrap: anywhere;
  line-height: 1.35;
  max-width: 100%;
}
.mline { min-width: 0; }
.mline .metric-val {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  text-align: right;
  max-width: 48%;
  flex: 0 1 auto;
  min-width: 0;
  line-height: 1.25;
  font-size: 0.78rem;
}
.fx-card-read, .fx-kpi strong { overflow-wrap: anywhere; word-break: break-word; }
@media (max-width: 850px) {
  .fx-grid-2, .fx-mini-grid, .fx-grid { grid-template-columns: 1fr; }
  .fx-stats { grid-template-columns: repeat(2, 1fr); }
  .fx-supply-head { display: block; }
  .fx-supply-head .fx-card-copy { text-align: left; margin-top: 6px; }
  .split { grid-template-columns: 1fr; }
  .mline .metric-val { max-width: 100%; text-align: left; }
}
@media (max-width: 560px) {
  .fx-card { padding: 16px 16px; }
  .fx-stats, .fx-supply-metrics, .fx-status-row, .fx-kpi-row { grid-template-columns: 1fr; }
}
"""
