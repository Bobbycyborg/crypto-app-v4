"""Persistent Stage 2 FART/SPX Report02 text corrections — survives weekly rebuild."""

from __future__ import annotations

import re
from typing import Callable

# --- FART Stage 2 locked findings (report copy only — not Convergence Attention feed) ---

FART_HOLDER_READ = "UNIT 9.77% · LP 2.15% · 33.23% UNATTRIBUTED"

FART_OWNERSHIP_EVIDENCE = (
    "Stage 2 top-20 attribution: Unit / Hyperunit protocol-custody treasury 9.77%; "
    "Raydium LP 2.15%; 33.23% unattributed — not whales. "
    "Distributor / flow-linked cohorts may be described as such; same-source or flow-linked "
    "does not prove same beneficial owner. Bounded DEX sampling found no evidenced "
    "discretionary whale-buying behaviour — not proof discretionary whales are absent."
)

FART_FLOAT_EVIDENCE = (
    "Near-full float with revoked mint/freeze. Unit 9.77% protocol-custody treasury; "
    "Raydium LP 2.15%; 33.23% unattributed structure — not whales."
)

FART_STANCE_BULLET = (
    "Top-20 structure partly mapped (Unit 9.77%, Raydium LP 2.15%) but 33.23% "
    "remains unattributed — not discretionary whale concentration"
)

FART_ATTENTION_READ = "FADING"
FART_ATTENTION_EVIDENCE = (
    "Approved Google Trends series (Stage 2 research lock) — FADING. "
    "Not wired into AUTOJOB Convergence Attention row."
)

# --- SPX Stage 2 locked findings ---

SPX_HOLDER_READ = "ETH CANONICAL + SOL PORTAL"

SPX_ETH_OWNERSHIP_EVIDENCE = (
    "ETH canonical ownership (Ethplorer top-50): Wormhole bridge ~11.08%; burn ~6.90%; "
    "Uniswap LP ~1.38%; ETH top-50 unlabelled ~39.25%. No labelled CEX/MM in ETH top-50. "
    "Holdings outside top-50 remain UNKNOWN. Custody ≠ beneficial ownership; "
    "concentration ≠ whales. Solana portal slice is partial only."
)

SPX_ETH_OWNERSHIP_BLOCK = (
    '<div class="ev-tip-row stage2-eth-ownership"><span class="ev-k">ETH canonical (Stage 2)</span>'
    '<span class="ev-v">Wormhole ~11.08% · burn ~6.90% · Uniswap LP ~1.38% · '
    "top-50 unlabelled ~39.25%. No labelled CEX/MM in ETH top-50. Outside top-50: UNKNOWN."
    "</span></div>"
)

SPX_ATTENTION_EVIDENCE = (
    "UNKNOWN — approved Google Trends query is below usable floor (Stage 2 research lock). "
    "Not wired into AUTOJOB Convergence Attention row."
)


def _map_article(html: str, asset: str, fn: Callable[[str], str]) -> str:
    pat = re.compile(
        rf'(<article\b(?=[^>]*\bdata-asset="{re.escape(asset)}")[^>]*>)(.*?)(</article>)',
        re.S,
    )
    m = pat.search(html)
    if not m:
        return html
    return html[: m.start()] + m.group(1) + fn(m.group(2)) + m.group(3) + html[m.end() :]


def _sub(body: str, old: str, new: str) -> str:
    return body.replace(old, new) if old in body else body


def _sub_all(body: str, old: str, new: str) -> str:
    return body.replace(old, new)


def _sub_re(body: str, pattern: str, repl: str, flags: int = 0, count: int = 0) -> str:
    return re.sub(pattern, repl, body, count=count, flags=flags)


def _sub_re_all(body: str, pattern: str, repl: str, flags: int = 0) -> str:
    return re.sub(pattern, repl, body, flags=flags)


def _patch_fart(body: str) -> str:
    body = _sub(
        body,
        "Raw top-20 ~45% unusable as discretionary concentration. Adjusted owners UNKNOWN.",
        FART_OWNERSHIP_EVIDENCE,
    )
    body = _sub_re(
        body,
        r'(<div class="ev-tip-name">Raw Holder Concentration</div><div class="ev-tip-read">)TOP-20 ~[\d.]+%',
        rf"\g<1>{FART_HOLDER_READ}",
    )
    body = _sub_re(
        body,
        r'(<div class="ev-tip-row"><span class="ev-k">Evidence</span><span class="ev-v">)Top 20 token accounts ~[\d.]+% of supply\. Unclassified in top-20: \d+/\d+\. Do not label raw top-20 as whale control\. Accounts may be CEX/LP/program/discretionary/other\. Adjusted concentration UNKNOWN\.',
        rf"\g<1>{FART_OWNERSHIP_EVIDENCE}",
    )
    body = _sub_re_all(
        body,
        r"Top-20 token accounts ~[\d.]+% of supply\.",
        (
            "Unit / Hyperunit treasury 9.77%; Raydium LP 2.15%; 33.23% unattributed — not whales."
        ),
    )
    body = _sub_re_all(
        body,
        r'(<span class="ev-k">Raw top-20</span><span class="ev-v">)~[\d.]+%',
        r"\g<1>9.77% Unit · 2.15% LP · 33.23% unattributed",
    )
    body = _sub_re_all(
        body,
        r'(<div class="fx-ev-k">Raw top-20</div><div class="fx-ev-v">)~[\d.]+%',
        r"\g<1>9.77% Unit · 2.15% LP · 33.23% unattributed",
    )
    body = _sub_all(
        body,
        "Do not label raw top-20 as whale control.",
        "33.23% unattributed is not whale concentration. Same-source or flow-linked ≠ same owner.",
    )
    body = _sub_all(
        body,
        "Do not call this whale control.",
        "Unattributed balances are not discretionary whales.",
    )
    body = _sub_re(
        body,
        r'(<div class="alt-signal-state">)TOP-20 ~[\d.]+%',
        rf"\g<1>{FART_HOLDER_READ}",
    )
    body = _sub_re(
        body,
        r'(<div class="fx-kpi"><strong>)~[\d.]+%(</strong><span>Raw top-20</span></div>)',
        rf"\g<1>STAGE 2\g<2>",
    )
    body = _sub_re_all(
        body,
        r'~[\d.]+% — not labeled discretionary whales\.',
        "9.77% Unit · 2.15% LP · 33.23% unattributed — not whales.",
    )
    body = _sub(
        body,
        "Raw top-holder concentration is high while discretionary ownership is unresolved",
        FART_STANCE_BULLET,
    )
    body = _sub(
        body,
        "Raw top-20 ~45% is unusable. Discretionary owners unresolved. Cleaner labels alone would not change the thesis; accumulation would.",
        (
            "33.23% unattributed in top-20 — not whales. Unit 9.77% and Raydium LP 2.15% labelled. "
            "Cleaner labels alone would not change the thesis; evidenced accumulation would."
        ),
    )
    body = _sub_re(
        body,
        r'(<div class="ev-tip-name">Float vs ownership</div><div class="ev-tip-read">)FLOAT CLEAN · OWNERS OPAQUE',
        r"\g<1>FLOAT CLEAN · OWNERS PARTIALLY MAPPED",
    )
    body = _sub_re(
        body,
        r'(<div class="ev-tip-row"><span class="ev-k">Ownership</span><span class="ev-v">)Opaque',
        r"\g<1>Unit 9.77% treasury · Raydium LP 2.15% · 33.23% unattributed",
    )
    body = _sub_re(
        body,
        r'(<div class="ev-tip-name">Attention / reflexivity quality</div><div class="ev-tip-read">)No clean social series\.',
        rf"\g<1>{FART_ATTENTION_READ}",
    )
    body = _sub(body, "No clean social series.", FART_ATTENTION_READ)
    body = _sub_re(
        body,
        r'(<div class="ev-tip-name">Attention / reflexivity quality</div>.*?<div class="ev-tip-row"><span class="ev-k">Evidence</span><span class="ev-v">)[^<]*',
        rf"\g<1>{FART_ATTENTION_EVIDENCE}",
        flags=re.S,
    )
    return body


def _patch_spx(body: str) -> str:
    body = _sub_re(
        body,
        r'(<div class="ev-tip-name">Holder Identity</div><div class="ev-tip-read">)SOLANA SLICE ONLY',
        rf"\g<1>{SPX_HOLDER_READ}",
    )
    body = _sub_re(
        body,
        r'(<div class="ev-tip-row"><span class="ev-k">Evidence</span><span class="ev-v">)SOLANA HOLDER MAP PARTIAL · MARKET-WIDE OWNERSHIP UNKNOWN\. Solana top-10 ~[\d.]+% of Solana mint · top-20 ~[\d.]+% of Solana mint\. #1 identity UNKNOWN\. Raydium authority in top: True \(PROGRAM / LP — not discretionary whale\)\. Solana is only ~[\d.]+% ',
        rf"\g<1>{SPX_ETH_OWNERSHIP_EVIDENCE} ",
    )
    if "stage2-eth-ownership" not in body:
        body = _sub_re(
            body,
            r'(<div class="ev-tip-name">Holder Identity</div><div class="ev-tip-read">[^<]+</div><div class="ev-tip-rows">)',
            rf"\g<1>{SPX_ETH_OWNERSHIP_BLOCK}",
            count=1,
        )
    body = _sub(
        body,
        "Beneficial owners across chains UNKNOWN.",
        (
            "ETH canonical structure mapped (Stage 2); beneficial owners of unlabelled "
            "ETH wallets and balances outside top-50 remain UNKNOWN."
        ),
    )
    body = _sub_re(
        body,
        r'(<div class="ev-tip-row"><span class="ev-k">Evidence</span><span class="ev-v">)No defensible attention time-series this pass\. Do not invent social metrics\.',
        rf"\g<1>{SPX_ATTENTION_EVIDENCE}",
    )
    return body


def apply_stage2_meme_overlay(html: str, log: list[str]) -> str:
    """Surgical FART/SPX Stage 2 wording — idempotent on rebuild."""
    before_fart = "45% unusable as discretionary" in html or "TOP-20 ~44.7%" in html
    before_spx = "SOLANA SLICE ONLY" in html

    html = _map_article(html, "fartcoin", _patch_fart)
    html = _map_article(html, "spx6900", _patch_spx)

    fart_slice = ""
    m_fart = re.search(
        r'<article\b[^>]*data-asset="fartcoin"[^>]*>.*?</article>',
        html,
        re.S,
    )
    if m_fart:
        fart_slice = m_fart.group(0)

    fart_ok = (
        "9.77%" in fart_slice
        and "33.23% unattributed" in fart_slice
        and "45% unusable" not in fart_slice
        and "TOP-20 ~44.7%" not in fart_slice
        and "whale control" not in fart_slice
        and "44.7%" not in fart_slice
    )
    spx_ok = "stage2-eth-ownership" in html and "Wormhole ~11.08%" in html

    if fart_ok:
        log.append("APPLY_OK STAGE2.FARTCOIN")
    elif before_fart:
        log.append("APPLY_MISS STAGE2.FARTCOIN partial")
    else:
        log.append("APPLY_OK STAGE2.FARTCOIN idempotent")

    if spx_ok:
        log.append("APPLY_OK STAGE2.SPX6900")
    elif before_spx:
        log.append("APPLY_MISS STAGE2.SPX6900 partial")
    else:
        log.append("APPLY_OK STAGE2.SPX6900 idempotent")

    return html
