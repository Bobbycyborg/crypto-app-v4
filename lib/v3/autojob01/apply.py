"""Patch Report 02 HTML only. Same price print on strip and hero. Rollback on failure."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from lib.v3.autojob01.protect import refuse_report_01_write, write_text
from lib.v3.autojob01.paths import REPORT_01_HTML, REPORT_02_HTML, LIVE_APPLY_TEMPLATE_HTML, LIVE_REVIEW_NUM, REPORT_03_BASELINE_HTML
from lib.v3.autojob01.contracts import PRICE_ASSETS


def report_week_label(when: date | None = None) -> str:
    """Human week label for live Report 02 — matches html_review_01 ordinal style."""
    d = when or datetime.now(timezone.utc).date()
    day = d.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} of {d.strftime('%B')}, {d.year}"


def report_week_headline(when: date | None = None) -> str:
    return f"Week of {report_week_label(when)} · Review {LIVE_REVIEW_NUM}"


def _sub_once(
    html: str,
    pattern: str,
    repl: str,
    field: str,
    log: list[str],
    touches: list | None = None,
    *,
    asset: str = "",
    section: str = "",
    needle: str = "",
) -> str:
    new, n = re.subn(pattern, repl, html, count=1, flags=re.S)
    if n != 1:
        log.append(f"APPLY_MISS {field} n={n}")
        return html
    log.append(f"APPLY_OK {field}")
    if touches is not None:
        nd = needle
        if not nd:
            nd = {
                "MARKET.btc_trend": "RETRACED",
                "MARKET.etf_amts": "7 M D",
                "MARKET.macro": "Global liquidity",
                "MARKET.leverage": "perps",
            }.get(field, "")
        if nd:
            touches.append({"asset": asset or "MARKET", "section": section or "market_top", "needle": nd, "field": field})
    return new


def _sub_proto(html: str, old_pat: str, new: str, field: str, log: list[str]) -> str:
    return _sub_once(
        html,
        rf'(<span class="proto-line">{old_pat}</span>)',
        rf'<span class="proto-line">{new}</span>',
        field,
        log,
    )


def _fmt_k(usd: float) -> str:
    if usd >= 1000:
        return f"~${usd/1000:.0f}K"
    return f"~${usd:.0f}"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def apply_market(html: str, bundle: dict[str, Any], log: list[str], touches: list | None = None) -> str:
    mkt = (bundle.get("market") or {}).get("data") or {}
    gl = mkt.get("macro_fred") or {}
    st = mkt.get("stablecoins") or {}
    gp = gl.get("global_pulse_yoy")
    stables_b = st.get("total_usd_b")
    ch30 = st.get("change_30d_pct")
    if isinstance(gp, (int, float)) and isinstance(stables_b, (int, float)):
        drain = " · still draining" if isinstance(ch30, (int, float)) and ch30 < 0 else ""
        line = f"Global liquidity down {abs(gp):.0f}% YoY · Stablecoins ${stables_b:.0f}B{drain}"
        html = _sub_once(
            html,
            r'(<span class="proto-line">)Global liquidity down \d+% YoY · Stablecoins \$[0-9.]+B[^<]*',
            rf"\g<1>{line}",
            "MARKET.macro",
            log,
            touches,
            asset="MARKET",
            section="market_top",
            needle="Global liquidity",
        )

    btc_px = (mkt.get("btc_cg") or {}).get("price_usd")
    ath = (mkt.get("btc_ath") or {}).get("ath_usd")
    floor = (mkt.get("july_floor") or {}).get("usd")
    if isinstance(btc_px, (int, float)) and isinstance(ath, (int, float)) and isinstance(floor, (int, float)):
        now_pct = abs(btc_px / ath - 1.0) * 100
        max_pct = abs(floor / ath - 1.0) * 100
        next_pct = abs(floor / btc_px - 1.0) * 100
        line = f"RETRACED {now_pct:.0f}% FROM ATH · MAX −{max_pct:.0f}% · NEXT {_fmt_k(floor)} −{next_pct:.0f}%"
        html = _sub_once(
            html,
            r'(<span class="proto-line">)RETRACED \d+% FROM ATH · MAX −\d+% · NEXT ~\$\d+K −\d+%',
            rf"\g<1>{line}",
            "MARKET.btc_trend",
            log,
            touches,
            asset="MARKET",
            section="market_top",
            needle="RETRACED",
        )

    rot = mkt.get("rotation") or {}
    if rot.get("eth_line") and rot.get("sol_line"):
        html = _sub_once(
            html,
            r'(<span class="proto-line">)ETH (?:ahead of|still behind) BTC · SOL (?:ahead of|still behind) BTC',
            rf"\g<1>{rot['eth_line']} · {rot['sol_line']}",
            "MARKET.rotation",
            log,
        )

    part = mkt.get("participation") or {}
    if part.get("line"):
        html = _sub_once(
            html,
            r'(<span class="proto-line">)Only \d+ of \d+ beat BTC · \d+ of \d+ above 50d',
            rf"\g<1>{part['line']}",
            "MARKET.participation",
            log,
        )

    lev = ((mkt.get("btc_leverage") or {}).get("volume") or {}).get("perp_spot_ratio")
    etf = mkt.get("etf") or {}
    assets = etf.get("assets") or {}
    fg = mkt.get("fear_greed") or {}
    from lib.v3.autojob01.apply_parity import (
        patch_btc_leverage_dual,
        patch_etf_dual,
        patch_fear_greed_dual,
    )

    html = patch_btc_leverage_dual(html, lev if isinstance(lev, (int, float)) else None, log)
    html = patch_fear_greed_dual(html, fg, log)
    html = patch_etf_dual(html, assets, log, touches)
    return html


def apply_sma(html: str, bundle: dict[str, Any], log: list[str]) -> str:
    tech = (bundle.get("technicals") or {}).get("assets") or {}
    for slug, row in tech.items():
        if not row.get("ok") or not row.get("summary"):
            log.append(f"SKIP_SMA {slug}")
            continue
        summary = _esc(row["summary"])
        html = _sub_once(
            html,
            rf'(<article[^>]*data-asset="{re.escape(slug)}"[^>]*>[\s\S]*?<span class="flag-detail">)(?:Below|Above) 50d[^<]*',
            rf"\g<1>{summary}",
            f"SMA.{slug}",
            log,
        )
    return html


def apply_conflicts(html: str, bundle: dict[str, Any], log: list[str]) -> str:
    assets = bundle.get("assets") or {}
    rend = assets.get("render") or {}
    f_circ = (rend.get("foundation") or {}).get("circulating")
    cg_circ = (rend.get("coingecko") or {}).get("circulating")
    sol_s = (rend.get("foundation") or {}).get("solana_supply")
    eth = (rend.get("foundation") or {}).get("ethereum_rndr")
    raw = ((rend.get("foundation") or {}).get("raw") or {})
    sol_c = raw.get("solanaCirculatingSupply")
    if isinstance(f_circ, (int, float)) and isinstance(cg_circ, (int, float)):
        html = _sub_once(
            html,
            r"Foundation [\d.]+M · CoinGecko [\d.]+M · Solana-only [\d.]+M",
            (
                f"Foundation {f_circ/1e6:.1f}M · CoinGecko {cg_circ/1e6:.1f}M · "
                f"Solana-only {(float(sol_c)/1e6 if isinstance(sol_c,(int,float)) else 0):.1f}M"
            ),
            "RENDER.foundation_circ",
            log,
        )
        sol_s_p = f"{sol_s/1e6:.2f}M" if isinstance(sol_s, (int, float)) else "—"
        sol_c_p = f"{sol_c/1e6:.2f}M" if isinstance(sol_c, (int, float)) else "—"
        eth_p = f"{eth/1e6:.2f}M" if isinstance(eth, (int, float)) else "—"
        html = _sub_once(
            html,
            r"Solana supply ~[\d.]+M · Solana circ ~[\d.]+M · legacy ETH RNDR ~[\d.]+M · Foundation circ ~[\d.]+M · CG circ ~[^·]+· max",
            (
                f"Solana supply ~{sol_s_p} · Solana circ ~{sol_c_p} · legacy ETH RNDR ~{eth_p} · "
                f"Foundation circ ~{f_circ/1e6:.2f}M · CG circ ~{cg_circ/1e6:.2f}M · max"
            ),
            "RENDER.circ_both",
            log,
        )

    hype = (assets.get("hype") or {}).get("conflict") or {}
    if hype.get("print"):
        html = _sub_once(
            html,
            r"CG [\d.]+% · (?:HL|Hyperliquid) [\d.]+%",
            hype["print"].replace("HL ", "HL "),
            "HYPE.circ_both",
            log,
        )
        cg = hype.get("cg_pct")
        hl = hype.get("hl_pct")
        if cg is not None and hl is not None:
            html = _sub_once(
                html,
                r"Circ CONFLICT [\d.]+%/[\d.]+%",
                f"Circ CONFLICT {cg:.0f}%/{hl:.0f}%",
                "HYPE.circ_conflict_flag",
                log,
            )
            html = _sub_once(
                html,
                r"CG [\d.]+% · HL [\d.]+%",
                f"CG {cg:.1f}% · HL {hl:.1f}%",
                "HYPE.metric_val_circ",
                log,
            )
    return html


def apply_week_identity(html: str, log: list[str]) -> str:
    """Live page is Review 04. Reports 01–03 stay frozen baselines."""
    week_label = report_week_label()
    week_line = report_week_headline()
    new, n = re.subn(
        r"<title>Crypto Decision Report — V3 Review \d+</title>",
        f"<title>Crypto Decision Report — V3 Review {LIVE_REVIEW_NUM}</title>",
        html,
        count=1,
    )
    log.append("APPLY_OK IDENTITY.title" if n == 1 else f"APPLY_MISS IDENTITY.title n={n}")
    html = new
    new, n = re.subn(
        r"(<button class=\"week-btn\"[^>]*>\s*<span>)Week of [^<]+",
        rf"\g<1>{week_line}",
        html,
        count=1,
    )
    log.append("APPLY_OK IDENTITY.week_btn" if n == 1 else f"APPLY_MISS IDENTITY.week_btn n={n}")
    html = new
    menu = (
        '          <a class="week-opt" href="baselines/report-01.html" role="option">\n'
        '            <span class="week-opt-date">Week of 14th of August, 2026</span>\n'
        '            <span class="week-opt-sub">Review 01</span>\n'
        "          </a>\n"
        '          <a class="week-opt" href="baselines/report-02.html" role="option">\n'
        '            <span class="week-opt-date">Week of 17th of August, 2026</span>\n'
        '            <span class="week-opt-sub">Review 02</span>\n'
        "          </a>\n"
        '          <a class="week-opt" href="baselines/report-03.html" role="option">\n'
        '            <span class="week-opt-date">Week of 20th of August, 2026</span>\n'
        '            <span class="week-opt-sub">Review 03</span>\n'
        "          </a>\n"
        '          <a class="week-opt is-current" href="index-v4.html" role="option">\n'
        f'            <span class="week-opt-date">Week of {week_label}</span>\n'
        f'            <span class="week-opt-sub">Review {LIVE_REVIEW_NUM}</span>\n'
        "          </a>"
    )
    new, n = re.subn(
        r'(<div class="week-menu" role="listbox">)\s*.*?(</div>)',
        rf"\g<1>\n{menu}\n        \g<2>",
        html,
        count=1,
        flags=re.S,
    )
    log.append("APPLY_OK IDENTITY.week_menu" if n == 1 else f"APPLY_MISS IDENTITY.week_menu n={n}")
    html = new
    if 'class="week-opt is-current" href="index-v4.html"' in html:
        log.append("APPLY_OK IDENTITY.is_current")
    else:
        log.append("APPLY_MISS IDENTITY.is_current")
    return html


def apply_report_02(bundle: dict[str, Any], html_path: Path | None = None) -> dict[str, Any]:
    dest = html_path or REPORT_02_HTML
    refuse_report_01_write(dest)
    original = dest.read_text(encoding="utf-8") if dest.exists() else ""
    template = LIVE_APPLY_TEMPLATE_HTML if LIVE_APPLY_TEMPLATE_HTML.is_file() else REPORT_01_HTML
    html = (
        template.read_text(encoding="utf-8")
        if dest.resolve() == REPORT_02_HTML.resolve()
        else original
    )
    log: list[str] = []
    touches: list[dict] = []
    prices = (bundle.get("prices") or {}).get("assets") or {}
    wallet = bundle.get("wallet") or {}
    owned = wallet.get("owned") or {}

    try:
        for sym, spec in PRICE_ASSETS.items():
            row = prices.get(sym) or {}
            if not row.get("ok"):
                log.append(f"SKIP_PRICE {sym}")
                continue
            print_px = row["print"]
            strip = spec.get("html_ticker") or sym
            hero = spec.get("hero_ticker") or strip
            html = _sub_once(
                html,
                rf'(<span class="hold-ticker">{re.escape(strip)}</span><span class="hold-px">)[^<]+',
                rf"\g<1>{print_px}",
                f"HOLDINGS.{strip}.price",
                log,
            )
            html = _sub_once(
                html,
                rf'(<h2 class="alt-ticker">{re.escape(hero)}</h2><span class="alt-price">)[^<]+',
                rf"\g<1>{print_px}",
                f"HERO.{hero}.price",
                log,
            )
            own = owned.get(sym) or owned.get(strip) or {}
            own_print = own.get("print")
            if own_print and own_print != "—" and "$" in str(own_print):
                html = _sub_once(
                    html,
                    rf'(<span class="hold-ticker">{re.escape(strip)}</span><span class="hold-px">[^<]+</span></span><span class="hold-owned">)[^<]+',
                    rf"\g<1>{own_print}",
                    f"HOLDINGS.{strip}.owned",
                    log,
                    touches,
                    asset="HOLDINGS",
                    section="asset_body",
                    needle=own_print,
                )

        if wallet.get("total_print"):
            from lib.v3.autojob01.apply_parity import patch_portfolio_dual

            html = patch_portfolio_dual(html, wallet["total_print"], log, touches)

        html = apply_market(html, bundle, log, touches)
        html = apply_sma(html, bundle, log)
        html = apply_conflicts(html, bundle, log)
        from lib.v3.autojob01.apply_dynamic import apply_dynamic

        html = apply_dynamic(html, bundle, log, touches)
        from lib.v3.autojob01.apply_convergence import apply_convergence
        from lib.v3.autojob01.apply_pump_hero import apply_pump_hero, require_pump_hero
        from lib.v3.autojob01.apply_stage2_meme_overlay import apply_stage2_meme_overlay

        html = apply_stage2_meme_overlay(html, log)
        html = apply_convergence(html, bundle, log, touches)
        html = apply_week_identity(html, log)
        if 'data-asset="pump"' in html:
            html = apply_pump_hero(html, bundle, log)
            require_pump_hero(html)
        write_text(dest, html)
        skip_holdings = (
            LIVE_APPLY_TEMPLATE_HTML.resolve() == REPORT_03_BASELINE_HTML.resolve()
        )
        fatal = [
            x
            for x in log
            if x.startswith("APPLY_MISS")
            and not x.split()[1].startswith("F.")
            and not (skip_holdings and x.split()[1].startswith("HOLDINGS."))
        ]
        return {
            "ok": not fatal,
            "log": log,
            "path": str(dest),
            "fatal_miss": fatal,
            "touches": touches,
        }
    except Exception as exc:  # noqa: BLE001
        write_text(dest, original)
        return {"ok": False, "rolled_back": True, "error": str(exc), "log": log, "path": str(dest)}
