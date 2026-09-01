"""Report 05 roster: paused GRASS/RAY/ORCA/BONK stay dormant (hide if present, never rewrite). Add ANSEM. Never run on frozen 01-04."""

from __future__ import annotations

import json
import re
from typing import Any

ANSEM_MINT = "9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump"
ANSEM_POOL = "FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC"

# Top owners from getTokenLargestAccounts (31 Aug 2026). Balances in tokens.
ANSEM_WATCH: list[tuple[str, str, float]] = [
    ("7oU9nR9VEvFPwvp2PpXo2LQc6A92QRhcUTwhLWT7MsDM", "Largest bag", 491_000_104.0),
    ("GV6UUmNxz2RpKxmNAPadYKb7uQpszwqQAu3qLJxVdC52", "ansemconzimp bag", 91_584_684.0),
    ("87ZDLDDbMAqmHJwsAgNjpJVCf9gZvwMJJMbFbXNTrkva", "Ansem3", 23_776_901.0),
    ("9SLPTL41SPsYkgdsMzdfJsxymEANKr5bYoBsQzJyKpKS", "Ansem4", 12_765_700.0),
    ("CLM6E4zpTviEC77nWKogpVLQoXx9tgoQCYJ8NibxKg1Q", "Ansem5", 9_327_234.0),
    ("2ozxuSn8UhZ1ZsoZJvmmY65GBPpyZ7sAHzogpVcn4Yam", "Ansem6", 7_574_826.0),
    (ANSEM_POOL, "PumpSwap pool", 5_273_704.0),
    ("HCgo8gvk99Wk13XWbbAoyxyEx2DgzidzVDma4ny32uYC", "Ansem8", 4_250_887.0),
    ("8wLPuPpZgbxnhTMiMG3suqsQgYQ1oy1s8nVYJjaT33m4", "Ansem9", 4_041_807.0),
    ("E2jUGJCTuHTgJxePiG5pPuaEkUuFwY4pwgxVA8Q7NHNd", "Ansem10", 3_826_176.0),
]

_SIREN_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
    'stroke-linejoin="round" class="lucide lucide-siren-icon lucide-siren">'
    '<path d="M7 18v-6a5 5 0 1 1 10 0v6"/>'
    '<path d="M5 21a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-1a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2z"/>'
    '<path d="M21 12h1"/><path d="M18.5 4.5 18 5"/><path d="M2 12h1"/>'
    '<path d="M12 2v1"/><path d="m4.929 4.929.707.707"/><path d="M12 12v6"/></svg>'
)


def _fmt_tok(n: float) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        x = n / 1_000_000
        return f"{x:.0f}M" if x >= 100 else (f"{x:.1f}M" if x >= 10 else f"{x:.2f}M")
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(int(n))


def _desk() -> str:
    return (
        '<button class="desk-row has-article" type="button" data-asset-slug="ansem">'
        '<span class="desk-name">ANSEM</span>'
        '<span class="desk-px">$0.287</span>'
        '<span class="desk-out">—</span>'
        '<span class="desk-siren"></span></button>'
    )


def _hold() -> str:
    n = len(ANSEM_WATCH)
    title = f"{n} watched · one LP pool"
    return (
        f'<button class="hold" type="button" data-asset-slug="ansem" data-feed="dex:{ANSEM_MINT}">'
        f'<span class="hold-name"><span class="hold-top"><span class="hold-ticker">ANSEM</span>'
        f'<span class="hold-siren-ico has-watch" data-siren-key="ANSEM" title="{title}">'
        f"{_SIREN_SVG}</span></span>"
        f'<span class="hold-px" data-live-px>$0.287</span></span>'
        f'<span class="hold-grid4">'
        f'<span><span class="hold-k">Out</span><span class="hold-out">—</span></span>'
        f'<span><span class="hold-k">This move</span><span class="hold-shelf">—</span></span>'
        f"</span></button>"
    )


def _article() -> str:
    return (
        '<article class="report asset-v3-report is-hidden" data-asset="ansem">'
        '<div class="alt-top"><section class="alt-hero">'
        '<div class="alt-hero-left">'
        '<span class="alt-eyebrow">V3 Intelligence · Asset Research Layer</span>'
        '<h2 class="alt-ticker">ANSEM</h2>'
        '<span class="alt-price">$0.287</span></div>'
        '<div class="alt-stance"><span class="alt-eyebrow">Current Stance</span>'
        '<div class="alt-stance-headline">ATTENTION COIN · ONE WALLET HEAVY · NOT HIS PROJECT</div>'
        '<p class="alt-stance-expl">The Black Bull ($ANSEM). Ansem did not launch it. '
        "One wallet holds about half the supply. Price is attention, not a product. "
        '<button type="button" class="stance-see-more">(see more)</button></p>'
        '<div class="stance-modal-src" hidden>'
        "<p class='stance-conf'>Evidence confidence · MEDIUM</p>"
        "<p class='stance-p'>Mint "
        f"{ANSEM_MINT}. "
        "An anonymous deployer sent a majority bag to a wallet tied to Ansem. "
        "He leaned in and airdropped. He did not write a product. "
        "Largest bag this fetch: 491M (~49%). PumpSwap pool is live. "
        "Get-out not set this week.</p>"
        "<section class='stance-sec'><h3 class='stance-h'>What supports it</h3>"
        "<ul class='stance-list'>"
        "<li>Verified mint on CoinGecko: The Black Bull (ANSEM).</li>"
        "<li>On-chain: 491M in 7oU9… and 91.6M in GV6UU… (Arkham: ansemconzimp).</li>"
        "<li>PumpSwap pool FnzKY6… is the live LP.</li>"
        "</ul></section>"
        "<section class='stance-sec'><h3 class='stance-h'>What holds it back</h3>"
        "<ul class='stance-list'>"
        "<li>Not Ansem’s launch. Name coin. Copycats exist — mint must match.</li>"
        "<li>One wallet can reprice the coin. No cash-flow. No get-out printed yet.</li>"
        "</ul></section>"
        "</div></div></section></div>"
        '<section class="econ-dash" aria-label="Black Bull wallet hunt">'
        '<div class="fx-card"><div class="fx-card-title">Largest bag</div>'
        '<div class="fx-card-read">491M · ~49%</div>'
        '<div class="fx-card-copy">7oU9nR9V…LWT7MsDM. Biggest holder this fetch.</div>'
        '<span class="fx-status is-known">WATCHED</span></div>'
        '<div class="fx-card"><div class="fx-card-title">ansemconzimp bag</div>'
        '<div class="fx-card-read">91.6M</div>'
        '<div class="fx-card-copy">GV6UUmNx…JxVdC52. Arkham label ansemconzimp.</div>'
        '<span class="fx-status is-known">WATCHED</span></div>'
        '<div class="fx-card"><div class="fx-card-title">PumpSwap pool</div>'
        '<div class="fx-card-read">5.3M</div>'
        '<div class="fx-card-copy">FnzKY6x7…hb8L3CC. Liquidity, not a person.</div>'
        '<span class="fx-status is-known">POOL</span></div>'
        "</section></article>"
    )


def _watch_blob() -> dict[str, Any]:
    wallets = []
    boxes = []
    popup = []
    tracked = 0.0
    for i, (wallet, tag, bal) in enumerate(ANSEM_WATCH, 1):
        tracked += bal
        fmt = _fmt_tok(bal)
        wallets.append(
            {
                "wallet": wallet,
                "line": "still sitting",
                "status": "still sitting",
                "sent": 0.0,
                "received": 0.0,
                "new_hops": [],
                "error": None,
                "balance": bal,
                "aug1": None,
                "aug1_status": "unproved",
                "aug1_as_of": None,
                "last_out_amount": 0,
                "last_out_ts": None,
                "last_out_status": "unknown",
            }
        )
        boxes.append(
            {
                "tag": tag,
                "book": "",
                "aug1": None,
                "aug1_status": "unproved",
                "aug1_as_of": None,
                "aug1_fmt": "—",
                "balance": bal,
                "balance_fmt": fmt,
                "left_24h": 0,
                "left_24h_fmt": "none left",
                "last_out_ts": None,
                "last_out_when": "not yet sampled",
                "last_out_amount": 0,
                "last_out_fmt": "",
                "last_out_status": "unknown",
                "last_out_dest_tag": "",
                "dest": "",
                "error": None,
                "now_prev": None,
                "now_as_of": None,
                "now_chg_fmt": "",
            }
        )
        popup.append(f"{tag} · still sitting")
    supply = 1_000_000_000.0
    n = len(ANSEM_WATCH)
    return {
        "wallets": wallets,
        "boxes": boxes,
        "summary": f"{n} watched · one LP pool",
        "loud": False,
        "popup": popup,
        "supply": supply,
        "supply_fmt": "1.0B",
        "tracked": tracked,
        "tracked_fmt": _fmt_tok(tracked),
        "cover_fmt": f"1.0B / {_fmt_tok(tracked)}",
    }


def _ensure_hidden_all(html: str, unique: str) -> str:
    start_search = 0
    while True:
        i = html.find(unique, start_search)
        if i < 0:
            return html
        start = i if html[i] == "<" else html.rfind("<", 0, i)
        end = html.find(">", start)
        tag = html[start : end + 1]
        if "is-hidden" not in tag and 'class="' in tag:
            tag2 = re.sub(
                r'class="([^"]*)"',
                lambda m: f'class="{m.group(1)} is-hidden"',
                tag,
                count=1,
            )
            html = html[:start] + tag2 + html[end + 1 :]
            start_search = start + len(tag2)
        else:
            start_search = i + len(unique)
    return html


def _hide_r05_out(html: str) -> str:
    """Keep GRASS/RAY/ORCA/BONK in the file. Hide them on the Report 05 board."""
    for unique in (
        'data-asset-slug="grass"',
        'data-asset-slug="orca"',
        '<div class="desk-row no-article"><span class="desk-name">BONK</span>',
        '<div class="desk-row no-article is-hidden"><span class="desk-name">BONK</span>',
        'data-feed="spot:BONKUSDT"',
        'data-asset-slug="ray"',
    ):
        html = _ensure_hidden_all(html, unique)
    return html


def _insert_ansem(html: str) -> str:
    if 'data-asset-slug="ansem"' in html:
        return html
    html = html.replace(
        '<div class="desk-row no-article"><span class="desk-name">GIGA</span>',
        _desk() + "\n" + '<div class="desk-row no-article"><span class="desk-name">GIGA</span>',
        1,
    )
    html = html.replace(
        '<button class="hold hold-no-article" type="button" data-feed="dex:63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9">',
        _hold()
        + "\n"
        + '<button class="hold hold-no-article" type="button" data-feed="dex:63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9">',
        1,
    )
    html = html.replace(
        '<article class="report asset-v3-report is-hidden" data-asset="2z">',
        _article() + "\n" + '<article class="report asset-v3-report is-hidden" data-asset="2z">',
        1,
    )
    return html


def _patch_hash_js(html: str) -> str:
    html = html.replace(
        "if (h === '2z' || h === 'drift' || h === 'orca') return h;",
        "if (h === '2z' || h === 'drift' || h === 'ansem') return h;",
        1,
    )
    html = html.replace(
        "var want = (slug === '2z' || slug === 'drift' || slug === 'orca') ? ('#' + slug) : '';",
        "var want = (slug === '2z' || slug === 'drift' || slug === 'ansem') ? ('#' + slug) : '';",
        1,
    )
    html = html.replace(
        "/#(?:2z|drift|orca|velocity)$/i",
        "/#(?:2z|drift|ansem|velocity)$/i",
        1,
    )
    html = html.replace("#2z / #drift / #orca / #velocity", "#2z / #drift / #ansem / #velocity")
    return html


def _patch_siren(html: str) -> str:
    needle = '<script type="application/json" id="siren-watch-data">'
    i = html.find(needle)
    if i < 0:
        raise RuntimeError("SIREN_WATCH_MISSING")
    start = i + len(needle)
    data, end_off = json.JSONDecoder().raw_decode(html[start:])
    if "ANSEM" not in data:
        data["ANSEM"] = _watch_blob()
        blob = json.dumps(data, separators=(",", ":"))
        return html[:start] + blob + html[start + end_off :]
    return html


def apply_roster(html: str) -> str:
    """Hide paused coins if present. Never rewrite them. Add ANSEM. Report 05 only."""
    html = _insert_ansem(html)
    html = _hide_r05_out(html)
    html = _patch_hash_js(html)
    html = _patch_siren(html)
    if 'data-asset="ansem"' not in html or 'data-siren-key="ANSEM"' not in html:
        raise RuntimeError("ROSTER_ANSEM_MISSING")
    return html
