"""Patch visible DYNAMIC figures in Report 02. Market-top dual-render uses apply_parity."""

from __future__ import annotations

import re
from typing import Any, Callable

MINUS = "\u2212"


def _cg(feeds: dict, cid: str) -> dict:
    return ((feeds.get("cg_by_id") or {}).get(cid) or {})


def _retrace(price: Any, ath: Any) -> float | None:
    if isinstance(price, (int, float)) and isinstance(ath, (int, float)) and ath:
        return (price / ath - 1.0) * 100.0
    return None


def _fmt_m(n: Any, d: int = 1) -> str:
    if not isinstance(n, (int, float)):
        return "—"
    if abs(n) >= 1e9:
        return f"{n/1e9:.{d}f}B"
    if abs(n) >= 1e6:
        return f"{n/1e6:.{d}f}M"
    if abs(n) >= 1e3:
        return f"{n/1e3:.0f}k"
    return f"{n:.0f}"


def _kprice(n: Any) -> str | None:
    if not isinstance(n, (int, float)):
        return None
    if n >= 1000:
        return f"~${n/1000:.1f}k"
    if n >= 1:
        s = f"~${n:.2f}"
        return s
    s = f"~${n:.6f}".rstrip("0")
    return s


def _usd(n: Any) -> str | None:
    if not isinstance(n, (int, float)):
        return None
    if abs(n) >= 1e9:
        return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n/1e6:.1f}M"
    if abs(n) >= 1e3:
        return f"${n/1e3:.0f}k"
    return f"${n:.0f}"


def _map_article(html: str, asset: str, fn: Callable[[str], str]) -> str:
    pat = re.compile(
        rf'(<article\b(?=[^>]*\bdata-asset="{re.escape(asset)}")[^>]*>)(.*?)(</article>)',
        re.S,
    )
    m = pat.search(html)
    if not m:
        return html
    return html[: m.start()] + m.group(1) + fn(m.group(2)) + m.group(3) + html[m.end() :]


def _ok(log: list[str], touches: list, field: str, asset: str, section: str, needle: str) -> None:
    log.append(f"APPLY_OK {field}")
    touches.append({"asset": asset, "section": section, "needle": needle, "field": field})


def _miss(log: list[str], field: str) -> None:
    log.append(f"APPLY_MISS {field} n=0")


def _patch_kpi(body: str, label: str, new_strong: str, field: str, log: list[str], touches: list, asset: str) -> str:
    pat = rf'(<div class="fx-kpi"><strong>)([^<]*)(</strong><span>{re.escape(label)}</span></div>)'
    m = re.search(pat, body)
    if not m:
        _miss(log, field)
        return body
    _ok(log, touches, field, asset, "forensics_or_fingerprint", m.group(2) + " " + label)
    return body[: m.start()] + m.group(1) + new_strong + m.group(3) + body[m.end() :]


def _patch_dial(
    body: str,
    label: str,
    inner: str,
    field: str,
    log: list[str],
    touches: list,
    asset: str,
    sub: str | None = None,
) -> str:
    lab = label.replace("\n", "<br>")
    pat = (
        rf'(<span class="econ-dial-num(?: econ-dial-num-sm)?">)'
        rf'((?:(?!econ-dial-num|econ-dial-label).)*?)'
        rf'(</span></div>\s*<span class="econ-dial-label">{re.escape(lab)})'
    )
    m = re.search(pat, body, flags=re.S)
    if not m:
        _miss(log, field)
        return body
    _ok(log, touches, field, asset, "mini_dash", m.group(2))
    body = body[: m.start()] + m.group(1) + inner + m.group(3) + body[m.end() :]
    if sub is not None:
        spat = rf'(<span class="econ-dial-label">{re.escape(lab)}</span><span class="econ-sub">)[^<]*'
        body, n = re.subn(spat, rf"\g<1>{sub}", body, count=1)
        if n != 1:
            log.append(f"APPLY_MISS {field}.sub n={n}")
    return body


def _patch_div(body: str, cls: str, contains: str, new: str, field: str, log: list[str], touches: list, asset: str, section: str) -> str:
    pat = rf'(<(?:div|span) class="{re.escape(cls)}[^"]*">)([^<]*)(</(?:div|span)>)'
    for m in re.finditer(pat, body):
        if contains not in m.group(2):
            continue
        _ok(log, touches, field, asset, section, m.group(2))
        return body[: m.start()] + m.group(1) + new + m.group(3) + body[m.end() :]
    _miss(log, field)
    return body


def _patch_metric(body: str, small: str, new: str, field: str, log: list[str], touches: list, asset: str, *, nth: int = 1) -> str:
    """Bind to <small>LABEL</small> then the following metric-val. Never match the old number."""
    pat = rf'(<small>{re.escape(small)}</small></div><div class="metric-val[^"]*">)([^<]*)'
    matches = list(re.finditer(pat, body))
    if len(matches) < nth:
        _miss(log, field)
        return body
    m = matches[nth - 1]
    _ok(log, touches, field, asset, "asset_body", m.group(2))
    return body[: m.start()] + m.group(1) + new + body[m.end() :]


def _patch_flag(body: str, contains: str, new: str, field: str, log: list[str], touches: list, asset: str) -> str:
    return _patch_div(body, "flag-detail", contains, new, field, log, touches, asset, "asset_body")


def apply_dynamic(html: str, bundle: dict[str, Any], log: list[str], touches: list | None = None) -> str:
    touches = touches if touches is not None else []
    feeds = bundle.get("feeds") or {}
    mkt = (bundle.get("market") or {}).get("data") or {}
    prices = (bundle.get("prices") or {}).get("assets") or {}
    assets = bundle.get("assets") or {}
    lev = feeds.get("leverage") or {}
    llama = feeds.get("llama") or {}

    def px(sym: str, cid: str) -> Any:
        return (prices.get(sym) or {}).get("price_usd") or _cg(feeds, cid).get("price")

    def dd(sym: str, cid: str) -> float | None:
        return _retrace(px(sym, cid), _cg(feeds, cid).get("ath") or (mkt.get("btc_ath") or {}).get("ath_usd") if cid == "bitcoin" else _cg(feeds, cid).get("ath"))

    # ----- BTC -----
    def btc_body(b: str) -> str:
        btc = _cg(feeds, "bitcoin")
        circ = btc.get("circ")
        if isinstance(circ, (int, float)):
            pct = circ / 21_000_000 * 100
            b = _patch_dial(b, "Circulating", f"{pct:.1f}<span class='econ-u'>%</span>", "F.BTC.dial_circ", log, touches, "btc", sub=f"{circ/1e6:.1f}M / 21M")
            iss = 3.125 * 144 * 365 / circ * 100
            b = _patch_dial(b, "Issuance<br>per year", f"{iss:.2f}<span class='econ-u'>%</span>", "F.BTC.dial_iss", log, touches, "btc")
        btc_d = (feeds.get("btc_dominance") or {}).get("pct")
        if isinstance(btc_d, (int, float)):
            b = _patch_kpi(b, "BTC.D", f"~{btc_d:.1f}%", "F.BTC.D", log, touches, "btc")
        st = (mkt.get("stablecoins") or {}).get("total_usd_b")
        if isinstance(st, (int, float)):
            b = _patch_kpi(b, "Stables", f"~${st:.1f}B", "F.BTC.stables", log, touches, "btc")
        gp = (mkt.get("macro_fred") or {}).get("global_pulse_yoy")
        if isinstance(gp, (int, float)):
            b = _patch_kpi(b, "Liq pulse YoY", f"~{gp:.2f}%", "F.BTC.liq", log, touches, "btc")
        part = mkt.get("participation") or {}
        if part.get("beat_btc_n") is not None and part.get("universe_n"):
            pctp = part["beat_btc_n"] / part["universe_n"] * 100
            b = _patch_kpi(b, "Beat BTC 30d", f"~{pctp:.1f}%", "F.BTC.beat", log, touches, "btc")
        etf = ((mkt.get("etf") or {}).get("assets") or {}).get("BTC") or {}
        if etf.get("ok") and isinstance(etf.get("flow_all_time_usd"), (int, float)):
            b = _patch_kpi(b, "ETF cum.", f"~${etf['flow_all_time_usd']/1e9:.1f}B", "F.BTC.etf_cum", log, touches, "btc")
            p_btc = px("BTC", "bitcoin")
            circ_btc = btc.get("circ")
            if isinstance(p_btc, (int, float)) and isinstance(circ_btc, (int, float)) and p_btc and circ_btc:
                held = etf["flow_all_time_usd"] / p_btc
                share = held / circ_btc * 100.0
                b = _patch_dial(b, "ETF<br>share", f"{share:.1f}<span class='econ-u'>%</span>", "F.BTC.etf_share", log, touches, "btc")
        daily = etf.get("recent_daily") or []
        if isinstance(daily, list) and len(daily) >= 3:
            last = daily[-1]
            prev = daily[-2]
            def _m(u):
                return f"${abs(u)/1e6:.1f}M" if isinstance(u, (int, float)) else "—"
            line = (
                f"{daily[-3]['date'][-5:] if daily[-3].get('date') else 'd-2'} "
                f"{_m(daily[-3].get('usd'))}; "
                f"{prev.get('date','')[-5:]} {_m(prev.get('usd'))}; "
                f"{last.get('date','')[-5:]} {_m(last.get('usd'))}."
            )
            b = _patch_div(b, "rc-item-line", "Aug 3", line, "F.BTC.rc_etf_days", log, touches, "btc", "risk_confirmation")
        p, ath = px("BTC", "bitcoin"), (mkt.get("btc_ath") or {}).get("ath_usd") or btc.get("ath")
        ddv = _retrace(p, ath)
        if ddv is not None and _kprice(p) and _kprice(ath):
            title = f"~{abs(ddv):.0f}% retraced from Oct 2025 ATH"
            line = f"BTC {_kprice(p)} · ATH {_kprice(ath)} · ~{MINUS}{abs(ddv):.1f}%."
            b = _patch_div(b, "rc-item-title", "retraced from Oct 2025 ATH", title, "F.BTC.rc_title", log, touches, "btc", "risk_confirmation")
            b = _patch_div(b, "rc-item-line", "ATH", line, "F.BTC.rc_ath", log, touches, "btc", "risk_confirmation")
            b = _patch_metric(b, "From Oct 2025 ATH", f"~{MINUS}{abs(ddv):.1f}%", "F.BTC.metric_dd", log, touches, "btc")
        floor = (mkt.get("july_floor") or {}).get("usd")
        if isinstance(floor, (int, float)):
            b = _patch_div(b, "rc-item-line", "July low", f"July low ~${floor/1000:.1f}k · range / higher-low holding.", "F.BTC.july", log, touches, "btc", "risk_confirmation")
        bl = lev.get("BTC") or {}
        if isinstance(bl.get("perp_spot"), (int, float)):
            oi = bl.get("oi_tokens")
            oi_s = f" · OI ~{oi/1000:.0f}k BTC" if isinstance(oi, (int, float)) else ""
            b = _patch_div(
                b,
                "rc-item-line",
                "Binance fut/spot",
                f"Binance fut/spot ~{bl['perp_spot']:.1f}×{oi_s} · funding mild positive.",
                "F.BTC.rc_fut",
                log,
                touches,
                "btc",
                "risk_confirmation",
            )
            b = _patch_div(
                b,
                "rc-item-line",
                "leverage-heavy",
                f"Structure remains leverage-heavy (~{bl['perp_spot']:.0f}× fut/spot on Binance).",
                "F.BTC.rc_lev",
                log,
                touches,
                "btc",
                "risk_confirmation",
            )
            b = _patch_metric(b, "Binance 24h", f"~{bl['perp_spot']:.1f}×", "F.BTC.metric_lev", log, touches, "btc")
            b = _patch_flag(b, "perp volume", f"Binance perp volume ~{bl['perp_spot']:.0f}× spot", "F.BTC.flag_lev", log, touches, "btc")
        ch30 = btc.get("chg_30d") or (prices.get("BTC") or {}).get("change_30d")
        if isinstance(ch30, (int, float)):
            sign = "+" if ch30 >= 0 else MINUS
            b = _patch_metric(b, "Binance BTC", f"{sign}{abs(ch30):.1f}% 30d", "F.BTC.metric_30d", log, touches, "btc")
        return b

    html = _map_article(html, "btc", btc_body)

    # ----- FARTCOIN -----
    def fart_body(b: str) -> str:
        row = _cg(feeds, "fartcoin")
        p, ath = px("FARTCOIN", "fartcoin"), row.get("ath")
        ddv = _retrace(p, ath)
        if ddv is not None:
            b = _patch_div(b, "rc-item-title", "retraced from ATH", f"~{abs(ddv):.0f}% retraced from ATH · zombie-risk zone", "F.FART.rc_title", log, touches, "fartcoin", "risk_confirmation")
            ath_s = f"ATH ${ath:.2f}" if isinstance(ath, (int, float)) else "ATH —"
            b = _patch_div(
                b,
                "rc-item-line",
                "Mint verified",
                f"Mint verified · {_kprice(p)} · {ath_s} · {ddv:.1f}%.",
                "F.FART.rc_px",
                log,
                touches,
                "fartcoin",
                "risk_confirmation",
            )
        fl = lev.get("FARTCOIN") or {}
        if isinstance(fl.get("oi_usd"), (int, float)) and isinstance(fl.get("fut_quote_24h"), (int, float)):
            fund = fl.get("funding")
            fs = f" · funding ~{fund:.0e}" if isinstance(fund, (int, float)) else ""
            b = _patch_div(
                b,
                "rc-item-line",
                "OI ~$",
                f"OI ~{_usd(fl['oi_usd'])} · perp 24h ~{_usd(fl['fut_quote_24h'])}{fs}.",
                "F.FART.rc_oi",
                log,
                touches,
                "fartcoin",
                "risk_confirmation",
            )
        fl = lev.get("FARTCOIN") or {}
        cb = feeds.get("coinbase_fart") or {}
        if isinstance(fl.get("fut_quote_24h"), (int, float)) and isinstance(cb.get("quote_24h"), (int, float)) and cb["quote_24h"]:
            ratio = fl["fut_quote_24h"] / cb["quote_24h"]
            b = _patch_kpi(b, "Perp vs CB spot", f"~{ratio:.2f}×", "F.FART.kpi_perp", log, touches, "fartcoin")
        conc = (feeds.get("concentration") or {}).get("FARTCOIN") or {}
        if conc.get("ok"):
            acc = conc.get("top_accounts") or []
            tot = conc.get("total_supply_ui") or 0
            if tot and acc:
                top20 = sum(a.get("ui_amount") or 0 for a in acc[:20]) / tot * 100
                b = _patch_kpi(b, "Raw top-20", f"~{top20:.1f}%", "F.FART.top20", log, touches, "fartcoin")
                b = _patch_div(b, "rc-item-line", "Top-20", f"Top-20 token accounts ~{top20:.1f}% of supply.", "F.FART.rc_top20", log, touches, "fartcoin", "risk_confirmation")
        wm = (feeds.get("labelled") or {}).get("fart_wm")
        if isinstance(wm, (int, float)) and wm > 0:
            b = _patch_div(
                b,
                "rc-item-line",
                "registry wallet",
                f"~{wm/1e6:.2f}M FARTCOIN in registry wallet.",
                "F.FART.rc_wm",
                log,
                touches,
                "fartcoin",
                "risk_confirmation",
            )
        if isinstance(row.get("circ"), (int, float)) and isinstance(row.get("max") or 1e9, (int, float)):
            mx = row.get("max") or 1e9
            if mx and row["circ"] / mx > 0.98:
                b = _patch_dial(b, "Circulating", "~100<span class='econ-u'>%</span>", "F.FART.dial_circ", log, touches, "fartcoin")
                b = _patch_flag(b, "circ", "Mint/freeze revoked · ~100% circ", "F.FART.flag_circ", log, touches, "fartcoin")
        return b

    html = _map_article(html, "fartcoin", fart_body)

    # ----- GRASS -----
    def grass_body(b: str) -> str:
        row = _cg(feeds, "grass")
        if isinstance(row.get("circ"), (int, float)):
            pct = row["circ"] / 1_000_000_000 * 100
            b = _patch_dial(b, "Circulating", f"{pct:.1f}<span class='econ-u'>%</span>", "F.GRASS.dial_circ", log, touches, "grass", sub=f"{row['circ']/1e6:.0f}M / 1B")
            b = _patch_kpi(b, "CG circ", f"{row['circ']/1e6:.1f}M", "F.GRASS.circ", log, touches, "grass")
            b = _patch_div(b, "rc-item-line", "Max 1.00B", f"Max 1.00B · circ ~{row['circ']/1e6:.1f}M · vesting overhang", "F.GRASS.rc_circ", log, touches, "grass", "risk_confirmation")
        p, ath = px("GRASS", "grass"), row.get("ath")
        ddv = _retrace(p, ath)
        if ddv is not None and isinstance(ath, (int, float)):
            b = _patch_div(b, "rc-item-title", "retraced from ATH", f"~{abs(ddv):.0f}% retraced from ATH · zombie-risk zone", "F.GRASS.rc_title", log, touches, "grass", "risk_confirmation")
            b = _patch_div(b, "rc-item-line", "from ATH", f"{_kprice(p)} · {ddv:.1f}% from ATH ${ath:.2f}", "F.GRASS.rc_px", log, touches, "grass", "risk_confirmation")
        gl = lev.get("GRASS") or {}
        if isinstance(gl.get("fut_quote_24h"), (int, float)):
            b = _patch_kpi(b, "Perp 24h", _usd(gl["fut_quote_24h"]) or "", "F.GRASS.perp", log, touches, "grass")
        if isinstance(gl.get("oi_usd"), (int, float)):
            b = _patch_kpi(b, "OI", _usd(gl["oi_usd"]) or "", "F.GRASS.oi", log, touches, "grass")
        vol = row.get("vol")
        if isinstance(vol, (int, float)):
            b = _patch_kpi(b, "Vol", _usd(vol) or "", "F.GRASS.vol", log, touches, "grass")
        oi30 = ((feeds.get("oi_30d") or {}).get("GRASS") or {}).get("pct_of_30d_max")
        if isinstance(oi30, (int, float)):
            b = _patch_kpi(b, "vs 30d max", f"~{oi30:.1f}%", "F.GRASS.oi30", log, touches, "grass")
        g30 = row.get("chg_30d")
        s30 = _cg(feeds, "solana").get("chg_30d")
        b30 = _cg(feeds, "bitcoin").get("chg_30d")
        r180 = ((feeds.get("ret_180d") or {}).get("GRASS") or {}).get("ret_180d")
        if isinstance(g30, (int, float)) and isinstance(s30, (int, float)) and isinstance(b30, (int, float)):
            r180s = f" · 180d return {r180:+.1f}%" if isinstance(r180, (int, float)) else ""
            b = _patch_div(
                b,
                "rc-item-line",
                "SOL 30d",
                f"SOL 30d {g30-s30:+.2f}pp · BTC 30d {g30-b30:+.2f}pp{r180s}",
                "F.GRASS.rc_rs",
                log,
                touches,
                "grass",
                "risk_confirmation",
            )
        return b

    html = _map_article(html, "grass", grass_body)

    # ----- HYPE -----
    def hype_body(b: str) -> str:
        hype = feeds.get("hype") or assets.get("hype") or {}
        hl = hype.get("hyperliquid") or {}
        llama_h = llama.get("hype") or {}
        if isinstance(llama_h.get("fees_30d"), (int, float)):
            inner = f"${llama_h['fees_30d']/1e6:.1f}<span class='econ-u'>M</span>"
            b = _patch_dial(b, "Fees", inner, "F.HYPE.fees_dial", log, touches, "hype")
            b = _patch_flag(b, "/30d · soft", f"~${llama_h['fees_30d']/1e6:.1f}M/30d · soft vs own prior month", "F.HYPE.fees_flag", log, touches, "hype")
        if isinstance(llama_h.get("hold_30d"), (int, float)):
            inner = f"${llama_h['hold_30d']/1e6:.1f}<span class='econ-u'>M</span>"
            b = _patch_dial(b, "AF buys", inner, "F.HYPE.af_dial", log, touches, "hype")
            b = _patch_flag(b, "Llama ~$", f"Fees → AF buys (Llama ~${llama_h['hold_30d']/1e6:.0f}M/30d)", "F.HYPE.af_flag", log, touches, "hype")
        if isinstance(hl.get("af_inventory"), (int, float)):
            inv = hl["af_inventory"] / 1e6
            b = _patch_kpi(b, "Inventory", f"{inv:.2f}M", "F.HYPE.inv", log, touches, "hype")
            b = _patch_div(b, "rc-item-line", "Inventory", f"Fee→HYPE buys. Inventory {inv:.2f}M. Ex-circ. Not staked.", "F.HYPE.rc_inv", log, touches, "hype", "risk_confirmation")
            b = _patch_flag(b, "AF still holds", f"Docs say burned · AF still holds ~{inv:.1f}M", "F.HYPE.flag_af", log, touches, "hype")
        if isinstance(hl.get("hyperlabs_ncu"), (int, float)):
            b = _patch_kpi(b, "HyperLabs NCU", f"~{hl['hyperlabs_ncu']/1e6:.0f}M", "F.HYPE.ncu", log, touches, "hype")
        if isinstance(hl.get("total_supply"), (int, float)):
            b = _patch_kpi(b, "totalSupply", f"~{hl['total_supply']/1e6:.0f}M", "F.HYPE.tot", log, touches, "hype")
        fees30 = llama_h.get("fees_30d")
        hl_lev = lev.get("HYPE") or {}
        if isinstance(fees30, (int, float)):
            nb, n = re.subn(r"perps 30d fees \$[\d.]+M", f"perps 30d fees {_usd(fees30)}", b, count=1)
            if n == 1:
                b = nb
                _ok(log, touches, "F.HYPE.rc_fees", "hype", "risk_confirmation", "perps 30d fees")
            else:
                _miss(log, "F.HYPE.rc_fees")
        if isinstance(hl_lev.get("oi_usd"), (int, float)):
            nb, n = re.subn(
                r"HYPE-token OI \$[\d.]+B",
                f"HYPE-token OI {_usd(hl_lev['oi_usd'])}",
                b,
                count=1,
            )
            if n == 1:
                b = nb
                _ok(log, touches, "F.HYPE.rc_oi", "hype", "risk_confirmation", "HYPE-token OI")
            else:
                _miss(log, "F.HYPE.rc_oi")
        return b

    html = _map_article(html, "hype", hype_body)

    # ----- IO -----
    def io_body(b: str) -> str:
        row = _cg(feeds, "io")
        if isinstance(row.get("circ"), (int, float)):
            pct = row["circ"] / 800_000_000 * 100
            b = _patch_dial(b, "Circulating", f"{pct:.1f}<span class='econ-u'>%</span>", "F.IO.dial_circ", log, touches, "io", sub=f"{row['circ']/1e6:.0f}M / 800M")
            b = _patch_kpi(b, "CG circ", f"{row['circ']/1e6:.1f}M", "F.IO.circ", log, touches, "io")
            b = _patch_div(b, "rc-item-line", "Circ ~", f"Circ ~{row['circ']/1e6:.1f}M · 500M genesis + 300M emissions over ~20y", "F.IO.rc_circ", log, touches, "io", "risk_confirmation")
            b = _patch_div(b, "rc-item-title", "circulating of 800M", f"~{pct:.0f}% circulating of 800M max", "F.IO.rc_title_circ", log, touches, "io", "risk_confirmation")
            b = _patch_flag(b, "% circ · 300M", f"~{pct:.0f}% circ · 300M emissions left", "F.IO.flag_circ", log, touches, "io")
        p, ath = px("IO", "io"), row.get("ath")
        if isinstance(p, (int, float)):
            b = _patch_kpi(b, "Now", f"~${p:.5f}".rstrip("0"), "F.IO.now", log, touches, "io")
        if isinstance(ath, (int, float)):
            b = _patch_kpi(b, "ATH", f"${ath:.2f}", "F.IO.ath", log, touches, "io")
        ddv = _retrace(p, ath)
        if ddv is not None and isinstance(ath, (int, float)):
            b = _patch_div(b, "rc-item-title", "retraced from ATH", f"~{abs(ddv):.0f}% retraced from ATH · zombie-risk zone", "F.IO.rc_title", log, touches, "io", "risk_confirmation")
            b = _patch_div(b, "rc-item-line", "from ATH $6.43", f"{_kprice(p)} · {ddv:.1f}% from ATH ${ath:.2f}", "F.IO.rc_px", log, touches, "io", "risk_confirmation")
        il = lev.get("IO") or {}
        if isinstance(il.get("perp_spot"), (int, float)):
            b = _patch_kpi(b, "Fut/spot", f"~{il['perp_spot']:.2f}×", "F.IO.futspot", log, touches, "io")
            oi_s = f" · OI ~{_usd(il['oi_usd'])}" if isinstance(il.get("oi_usd"), (int, float)) else ""
            b = _patch_div(b, "rc-item-line", "fut/spot", f"fut/spot ~{il['perp_spot']:.2f}×{oi_s} · funding quiet", "F.IO.rc_fut", log, touches, "io", "risk_confirmation")
            b = _patch_flag(b, "fut/spot", f"Binance fut/spot ~{il['perp_spot']:.2f}× · OI elevated", "F.IO.flag_fut", log, touches, "io")
        if isinstance(il.get("oi_usd"), (int, float)):
            b = _patch_kpi(b, "OI", _usd(il["oi_usd"]) or "", "F.IO.oi", log, touches, "io")
        earn = feeds.get("io_earnings") or {}
        if isinstance(earn.get("total_earnings"), (int, float)):
            tot = earn["total_earnings"]
            day = earn.get("avg_30d") if isinstance(earn.get("avg_30d"), (int, float)) else earn.get("daily_earnings")
            b = _patch_kpi(b, "Cumulative", f"${tot/1e6:.1f}M", "F.IO.kpi_cum", log, touches, "io")
            if isinstance(day, (int, float)):
                b = _patch_kpi(b, "30d avg", f"${day:,.0f}/d", "F.IO.kpi_day", log, touches, "io")
                b = _patch_dial(b, "Earnings", f"${tot/1e6:.0f}<span class='econ-u'>M</span>", "F.IO.dial_earn", log, touches, "io")
                nb, n = re.subn(r"~\$[0-9.]+M cum", f"~{_usd(tot)} cum", b, count=1)
                if n == 1:
                    _ok(log, touches, "F.IO.flag_earn", "io", "asset_body", _usd(tot) or "")
                    b = nb
                else:
                    _miss(log, "F.IO.flag_earn")
                b = _patch_metric(
                    b,
                    "Explorer API",
                    f"${tot/1e6:.1f}M · ${day:,.0f}/d",
                    "F.IO.metric_earn",
                    log,
                    touches,
                    "io",
                )
                cl, hrs = earn.get("running_clusters"), earn.get("total_compute_hours")
                head = f"Cum {_usd(tot)} · ~${day:,.0f}/day"
                if isinstance(cl, (int, float)) and isinstance(hrs, (int, float)):
                    hrs_s = f"{hrs/1e6:.1f}M" if hrs >= 1e6 else f"{hrs:,.0f}"
                    head = f"{head} · clusters {int(cl)} · hours {hrs_s}"
                    b = _patch_kpi(b, "Clusters", f"{int(cl)}", "F.IO.kpi_cl", log, touches, "io")
                b = _patch_div(b, "rc-item-line", "Cum $", head, "F.IO.rc_earn", log, touches, "io", "risk_confirmation")
        i30 = row.get("chg_30d")
        s30 = _cg(feeds, "solana").get("chg_30d")
        b30 = _cg(feeds, "bitcoin").get("chg_30d")
        r180 = ((feeds.get("ret_180d") or {}).get("IO") or {}).get("ret_180d")
        if isinstance(i30, (int, float)) and isinstance(s30, (int, float)) and isinstance(b30, (int, float)):
            r180s = f" · 180d return {r180:+.1f}%" if isinstance(r180, (int, float)) else ""
            b = _patch_div(
                b,
                "rc-item-line",
                "SOL 30d",
                f"SOL 30d {i30-s30:+.2f}pp · BTC 30d {i30-b30:+.2f}pp{r180s}",
                "F.IO.rc_rs",
                log,
                touches,
                "io",
                "risk_confirmation",
            )
        return b

    html = _map_article(html, "io", io_body)

    # ----- NOS -----
    def nos_body(b: str) -> str:
        row = _cg(feeds, "nosana")
        p, ath = px("NOS", "nosana"), row.get("ath")
        ddv = _retrace(p, ath)
        ch7, ch30 = row.get("chg_7d"), row.get("chg_30d")
        if ddv is not None:
            b = _patch_div(b, "rc-item-title", "retraced from ATH", f"~{abs(ddv):.0f}% retraced from ATH · zombie-risk zone", "F.NOS.rc_title", log, touches, "nos", "risk_confirmation")
            extra = ""
            if isinstance(ch7, (int, float)) and isinstance(ch30, (int, float)):
                extra = f" · 7d {ch7:+.1f}% · 30d {ch30:+.1f}%"
            b = _patch_div(
                b,
                "rc-item-line",
                "NOS ~$",
                f"NOS {_kprice(p)} · ~{MINUS}{abs(ddv):.0f}% from ATH{extra}.",
                "F.NOS.rc_px",
                log,
                touches,
                "nos",
                "risk_confirmation",
            )
        if isinstance(row.get("circ"), (int, float)) and isinstance(row.get("max") or 1e8, (int, float)):
            mx = row.get("max") or 1e8
            if mx and row["circ"] / mx > 0.98:
                b = _patch_dial(b, "Circulating", "~100<span class='econ-u'>%</span>", "F.NOS.dial_circ", log, touches, "nos")
        nos = feeds.get("nos_indexer") or {}
        if isinstance(nos.get("jobs_completed"), (int, float)):
            b = _patch_kpi(b, "Jobs completed", f"~{nos['jobs_completed']/1e6:.2f}M", "F.NOS.jobs", log, touches, "nos")
        if isinstance(nos.get("staked_pct"), (int, float)):
            b = _patch_dial(b, "Staked", f"{nos['staked_pct']:.0f}<span class='econ-u'>%</span>", "F.NOS.dial_staked", log, touches, "nos")
        vol = row.get("vol")
        if isinstance(vol, (int, float)):
            b = _patch_div(
                b,
                "rc-item-line",
                "CG vol",
                f"~{_usd(vol)} CG vol / thin DEX liq — small flows can move price.",
                "F.NOS.rc_vol",
                log,
                touches,
                "nos",
                "risk_confirmation",
            )
        for cid, lab, fld in (("nosana", "NOS", "F.NOS.mcap"), ("render-token", "RENDER", "F.NOS.mcap_render"), ("io", "IO", "F.NOS.mcap_io")):
            mc = _cg(feeds, cid).get("mcap")
            if isinstance(mc, (int, float)):
                b = _patch_kpi(b, lab, _usd(mc) or "", fld, log, touches, "nos")
        return b

    html = _map_article(html, "nos", nos_body)

    # ----- PUMP -----
    def pump_body(b: str) -> str:
        pump_wrap = llama.get("pump") or assets.get("pump") or {}
        pump = pump_wrap.get("data") or pump_wrap
        row = _cg(feeds, "pump-fun")
        rev7 = ((pump.get("revenue") or {}).get("total_7d_usd"))
        buy7 = ((pump.get("buyback_burn") or {}).get("total_7d_usd"))
        # Hero 8-cell dash is owned by apply_pump_hero. Never write buy/rev as a 73% value-capture dial.
        if isinstance(rev7, (int, float)):
            b = _patch_metric(b, "Weekly platform", f"${rev7/1e6:.1f}M/wk", "F.PUMP.metric_rev", log, touches, "pump")
        if isinstance(buy7, (int, float)):
            b = _patch_metric(b, "Programmatic", f"${buy7/1e6:.1f}M/wk", "F.PUMP.metric_buy", log, touches, "pump")
        if isinstance(rev7, (int, float)) and isinstance(buy7, (int, float)):
            b = _patch_flag(b, "rev ·", f"${rev7/1e6:.1f}M rev · ${buy7/1e6:.1f}M buyback", "F.PUMP.flag_rev", log, touches, "pump")
        fees1 = (pump.get("revenue") or {}).get("total_24h_usd")
        buy1 = (pump.get("buyback_burn") or {}).get("total_24h_usd")
        share = (pump.get("launchpad_share") or {}).get("share_pct_24h")
        pump_fees = (pump.get("launchpad_share") or {}).get("pump_fees_24h_usd")
        if isinstance(pump_fees, (int, float)):
            b = _patch_kpi(b, "Fees now", f"${pump_fees/1e6:.1f}M/d", "F.PUMP.kpi_fees", log, touches, "pump")
        if isinstance(fees1, (int, float)):
            if fees1 >= 1e6:
                b = _patch_kpi(b, "Revenue now", f"${fees1/1e6:.1f}M/d", "F.PUMP.kpi_rev", log, touches, "pump")
            else:
                b = _patch_kpi(b, "Revenue now", f"${fees1/1e3:.0f}K/d", "F.PUMP.kpi_rev", log, touches, "pump")
        if isinstance(buy1, (int, float)) and buy1 >= 1e3:
            b = _patch_kpi(b, "Buyback / burn", f"${buy1/1e3:.0f}K/d", "F.PUMP.kpi_buy", log, touches, "pump")
        if isinstance(share, (int, float)):
            b = _patch_metric(b, "Launchpad 24h (live)", f"{share:.0f}%", "F.PUMP.metric_share", log, touches, "pump")
        pl = lev.get("PUMP") or {}
        if isinstance(pl.get("perp_spot"), (int, float)):
            b = _patch_flag(b, "Futures", f"Futures {pl['perp_spot']:.1f}× spot", "F.PUMP.flag_fut", log, touches, "pump")
            b = _patch_div(b, "metric-val", "VS SPOT", f"{pl['perp_spot']:.1f}× VS SPOT", "F.PUMP.metric_fut", log, touches, "pump", "asset_body")
        p = px("PUMP", "pump-fun")
        if isinstance(p, (int, float)):
            b = _patch_metric(b, "Live spot", f"${p:.4f}", "F.PUMP.metric_px", log, touches, "pump")
        p30 = row.get("chg_30d")
        b30 = _cg(feeds, "bitcoin").get("chg_30d")
        s30 = _cg(feeds, "solana").get("chg_30d")
        if isinstance(p30, (int, float)) and isinstance(b30, (int, float)):
            vs = p30 - b30
            word = "LEADING" if vs > 0 else "LAGGING"
            b = _patch_metric(b, "Relative strength", f"{word} {vs:+.0f}%", "F.PUMP.metric_rs_btc", log, touches, "pump", nth=1)
        if isinstance(p30, (int, float)) and isinstance(s30, (int, float)):
            vs = p30 - s30
            word = "LEADING" if vs > 0 else "LAGGING"
            b = _patch_metric(b, "Relative strength", f"{word} {vs:+.0f}%", "F.PUMP.metric_rs_sol", log, touches, "pump", nth=2)
        liq = (prices.get("PUMP") or {}).get("liquidity_usd") or (prices.get("PUMP") or {}).get("dex_liquidity")
        if isinstance(liq, (int, float)):
            b = _patch_metric(b, "Best pool", _usd(liq) or "", "F.PUMP.metric_liq", log, touches, "pump")
        squads = (feeds.get("labelled") or {}).get("pump_squads")
        if isinstance(squads, (int, float)) and squads > 1e9:
            b = _patch_div(
                b,
                "rc-item-line",
                "in Squads",
                f"~{squads/1e9:.2f}B in Squads. Escrow ~0. Owners/timing UNKNOWN.",
                "F.PUMP.rc_squads",
                log,
                touches,
                "pump",
                "risk_confirmation",
            )
            b = _patch_flag(
                b,
                "unlocked",
                f"{squads/1e9:.0f}B unlocked · 287M → Wintermute OTC",
                "F.PUMP.flag_unlock",
                log,
                touches,
                "pump",
            )
        return b

    html = _map_article(html, "pump", pump_body)

    # ----- RAY -----
    def ray_body(b: str) -> str:
        row = _cg(feeds, "raydium")
        mx = row.get("max") or 555_000_000
        if isinstance(row.get("circ"), (int, float)) and mx:
            pct = row["circ"] / mx * 100
            b = _patch_dial(b, "Circulating", f"{pct:.1f}<span class='econ-u'>%</span>", "F.RAY.dial_circ", log, touches, "ray", sub=f"{row['circ']/1e6:.0f}M / 555M")
        fees30 = (llama.get("ray") or {}).get("fees_30d")
        if isinstance(fees30, (int, float)):
            b = _patch_dial(b, "Fees", f"${fees30/1e6:.1f}<span class='econ-u'>M</span>", "F.RAY.dial_fees", log, touches, "ray")
            b = _patch_flag(b, "Fees ~$", f"Fees ~${fees30/1e6:.1f}M / 30d", "F.RAY.flag_fees", log, touches, "ray")
            b = _patch_metric(b, "Gross trading fees", f"~${fees30/1e6:.1f}M 30d", "F.RAY.metric_fees", log, touches, "ray")
            b = _patch_div(b, "rc-item-line", "DefiLlama revenue", f"DefiLlama revenue ~${(llama.get('ray') or {}).get('rev_1d', 0)/1e3:.0f}k/day recent." if isinstance((llama.get("ray") or {}).get("rev_1d"), (int, float)) else f"DefiLlama fees ~${fees30/1e6:.1f}M / 30d.", "F.RAY.rc_rev", log, touches, "ray", "risk_confirmation")
        tvl = ((llama.get("ray_tvl") or {}).get("tvl"))
        if isinstance(tvl, (int, float)):
            b = _patch_kpi(b, "TVL", f"~${tvl/1e6:.0f}M", "F.RAY.kpi_tvl", log, touches, "ray")
            b = _patch_metric(b, "Solana pools", f"~${tvl/1e6:.0f}M", "F.RAY.metric_tvl", log, touches, "ray")
            b = _patch_div(b, "rc-item-line", "TVL ~$", f"Raydium parent DEX ~$100M+/day · TVL ~${tvl/1e9:.2f}B.", "F.RAY.rc_tvl", log, touches, "ray", "risk_confirmation")
        p, ath = px("RAY", "raydium"), row.get("ath")
        ddv = _retrace(p, ath)
        if ddv is not None:
            b = _patch_div(b, "rc-item-title", "retraced from ATH", f"~{abs(ddv):.0f}% retraced from ATH · zombie-risk zone", "F.RAY.rc_title", log, touches, "ray", "risk_confirmation")
            b = _patch_div(b, "rc-item-line", "RAY ~$", f"RAY {_kprice(p)} · ~{MINUS}{abs(ddv):.0f}% from 2021 ATH.", "F.RAY.rc_px", log, touches, "ray", "risk_confirmation")
        rl = lev.get("RAY") or {}
        if isinstance(rl.get("spot_quote_24h"), (int, float)):
            b = _patch_kpi(b, "Binance spot 24h", f"~{_usd(rl['spot_quote_24h'])}", "F.RAY.kpi_spot", log, touches, "ray")
        okx = feeds.get("okx_ray") or {}
        if isinstance(okx.get("oi_usd"), (int, float)):
            b = _patch_kpi(b, "OKX OI", f"~{_usd(okx['oi_usd'])}", "F.RAY.okx_oi", log, touches, "ray")
        hs = (feeds.get("helius_sample") or {}).get("RAY") or {}
        if hs.get("ok"):
            if isinstance(hs.get("sample_buy_usd"), (int, float)):
                b = _patch_kpi(b, "Sample buys", f"~{_usd(hs['sample_buy_usd'])}", "F.RAY.sample_buy", log, touches, "ray")
            if isinstance(hs.get("sample_sell_usd"), (int, float)):
                b = _patch_kpi(b, "Sample sells", f"~{_usd(hs['sample_sell_usd'])}", "F.RAY.sample_sell", log, touches, "ray")
            if isinstance(hs.get("top5_buy_pct"), (int, float)):
                b = _patch_kpi(b, "Top5 buy conc.", f"~{hs['top5_buy_pct']:.0f}%", "F.RAY.top5", log, touches, "ray")
        hold30 = (llama.get("ray") or {}).get("hold_30d")
        if isinstance(hold30, (int, float)):
            b = _patch_metric(b, "Buyback + treasury alloc", f"~${hold30/1e3:.0f}k 30d", "F.RAY.metric_hold", log, touches, "ray")
        rdx = llama.get("ray_dex") or {}
        v24, v30 = rdx.get("vol_24h"), rdx.get("vol_30d")
        if isinstance(v24, (int, float)) and isinstance(v30, (int, float)):
            b = _patch_metric(
                b,
                "Parent 24h / 30d",
                f"~{_usd(v24)} / {_usd(v30)}",
                "F.RAY.metric_dex",
                log,
                touches,
                "ray",
            )
        sol24 = ((llama.get("sol") or {}).get("dex_24h_usd"))
        ray24 = rdx.get("vol_24h") if isinstance(rdx.get("vol_24h"), (int, float)) else None
        if isinstance(sol24, (int, float)) and sol24 and isinstance(ray24, (int, float)):
            share = ray24 / sol24 * 100
            b = _patch_kpi(b, "Raydium AMM share", f"~{share:.0f}% of Sol DEX 24h", "F.RAY.amm", log, touches, "ray")
        ll = (llama.get("ray_launchlab") or {}).get("vol_24h")
        if isinstance(ll, (int, float)):
            b = _patch_kpi(b, "LaunchLab 24h", f"~{_usd(ll)}", "F.RAY.launchlab", log, touches, "ray")
        bb = (feeds.get("labelled") or {}).get("ray_buyback")
        circ_r = row.get("circ")
        if isinstance(bb, (int, float)) and isinstance(circ_r, (int, float)) and circ_r:
            pct = bb / circ_r * 100
            b = _patch_dial(b, "Buyback", f"{pct:.1f}<span class='econ-u'>%</span>", "F.RAY.dial_bb", log, touches, "ray")
        return b

    html = _map_article(html, "ray", ray_body)

    # ----- RENDER -----
    def rend_body(b: str) -> str:
        rend = feeds.get("render") or assets.get("render") or {}
        bme = rend.get("bme") or {}
        emit = rend.get("bme_emit") or {}
        found = rend.get("foundation") or {}
        if isinstance(bme.get("last4_burned"), (int, float)) and bme["last4_burned"] > 0:
            burn = bme["last4_burned"]
            b = _patch_kpi(b, "Last-4 burn", f"{burn/1e3:.1f}k", "F.RENDER.burn4", log, touches, "render")
            b = _patch_dial(b, "Burn", f"{burn/1e3:.1f}k", "F.RENDER.dial_burn", log, touches, "render")
        if isinstance(emit.get("last4_emit"), (int, float)) and emit["last4_emit"] > 100:
            em = emit["last4_emit"]
            b = _patch_kpi(b, "Last-4 emit", f"{em/1e3:.1f}k", "F.RENDER.emit4", log, touches, "render")
            b = _patch_dial(b, "Emissions", f"{em/1e3:.1f}k", "F.RENDER.dial_emit", log, touches, "render")
            if isinstance(bme.get("last4_burned"), (int, float)) and bme["last4_burned"] > 0:
                net = em - bme["last4_burned"]
                b = _patch_dial(b, "Net", f"{net/1e3:+.1f}k", "F.RENDER.dial_net", log, touches, "render")
                b = _patch_div(
                    b,
                    "rc-item-line",
                    "Last 4 epochs burned",
                    f"Last 4 epochs burned ~{bme['last4_burned']/1e3:.1f}k vs ~{em/1e3:.1f}k node emissions (ratio ~{bme['last4_burned']/em:.2f}).",
                    "F.RENDER.rc_bme",
                    log,
                    touches,
                    "render",
                    "risk_confirmation",
                )
        if isinstance(found.get("solana_supply"), (int, float)):
            b = _patch_kpi(b, "Solana supply", f"{found['solana_supply']/1e6:.2f}M", "F.RENDER.sol_sup", log, touches, "render")
        if isinstance(found.get("ethereum_rndr"), (int, float)):
            b = _patch_kpi(b, "Legacy ETH", f"{found['ethereum_rndr']/1e6:.2f}M", "F.RENDER.eth_sup", log, touches, "render")
        fr = (rend.get("frames") or {}).get("cumulative")
        if isinstance(fr, (int, float)) and fr > 0:
            b = _patch_kpi(b, "Frames", f"{fr/1e6:.2f}M", "F.RENDER.frames", log, touches, "render")
            b = _patch_metric(b, "Cumulative", f"{fr/1e6:.2f}M", "F.RENDER.metric_frames", log, touches, "render")
            b = _patch_div(
                b,
                "rc-item-line",
                "Cumulative frames",
                f"Cumulative frames ~{fr/1e6:.2f}M; BME mechanism burns RENDER for jobs.",
                "F.RENDER.rc_frames",
                log,
                touches,
                "render",
                "risk_confirmation",
            )
        row = _cg(feeds, "render-token")
        p, ath = px("RENDER", "render-token"), row.get("ath")
        ddv = _retrace(p, ath)
        if ddv is not None:
            b = _patch_div(b, "rc-item-title", "retraced from ATH", f"~{abs(ddv):.0f}% retraced from ATH · zombie-risk zone", "F.RENDER.rc_title", log, touches, "render", "risk_confirmation")
            b = _patch_div(b, "rc-item-line", "from ATH", f"{_kprice(p)} · ~{ddv:.1f}% from ATH", "F.RENDER.rc_px", log, touches, "render", "risk_confirmation")
        rl = lev.get("RENDER") or {}
        if isinstance(rl.get("perp_spot"), (int, float)):
            b = _patch_kpi(b, "Fut/spot", f"{rl['perp_spot']:.2f}×", "F.RENDER.futspot", log, touches, "render")
        if isinstance(rl.get("oi_usd"), (int, float)):
            b = _patch_kpi(b, "OI", _usd(rl["oi_usd"]) or "", "F.RENDER.oi", log, touches, "render")
        if isinstance(bme.get("cumulative_burned"), (int, float)) and bme["cumulative_burned"] > 0:
            cum = bme["cumulative_burned"]
            b = _patch_kpi(b, "Cumulative burn", f"{cum/1e6:.2f}M", "F.RENDER.cum_burn", log, touches, "render")
        hs = (feeds.get("helius_sample") or {}).get("RENDER") or {}
        if hs.get("ok"):
            def _tk(n: Any) -> str:
                if not isinstance(n, (int, float)):
                    return ""
                if abs(n) >= 1e6:
                    return f"{n/1e6:.2f}M"
                if abs(n) >= 1e3:
                    return f"{n/1e3:.1f}k"
                return f"{n:.1f}"

            if isinstance(hs.get("top5_buy_pct"), (int, float)):
                b = _patch_kpi(b, "Top-5 buy", f"{hs['top5_buy_pct']:.2f}%", "F.RENDER.top5", log, touches, "render")
            if isinstance(hs.get("gross_buy_tokens"), (int, float)):
                b = _patch_kpi(b, "Gross buy", _tk(hs["gross_buy_tokens"]), "F.RENDER.gross", log, touches, "render")
            if isinstance(hs.get("sample_buy_tokens"), (int, float)):
                b = _patch_kpi(b, "Sample buy", _tk(hs["sample_buy_tokens"]), "F.RENDER.sbuy", log, touches, "render")
            if isinstance(hs.get("sample_sell_tokens"), (int, float)):
                b = _patch_kpi(b, "Sample sell", _tk(hs["sample_sell_tokens"]), "F.RENDER.ssell", log, touches, "render")
            if isinstance(hs.get("net_tokens"), (int, float)):
                b = _patch_kpi(b, "Net", _tk(hs["net_tokens"]), "F.RENDER.net", log, touches, "render")
            if isinstance(hs.get("still_held_tokens"), (int, float)):
                b = _patch_kpi(b, "Still held", _tk(hs["still_held_tokens"]), "F.RENDER.held", log, touches, "render")
            if isinstance(hs.get("swap_count"), (int, float)):
                b = _patch_kpi(b, "Swaps", f"{int(hs['swap_count'])}", "F.RENDER.swaps", log, touches, "render")
            if isinstance(hs.get("unique_buyers"), (int, float)):
                b = _patch_kpi(b, "Buyers", f"{int(hs['unique_buyers'])}", "F.RENDER.buyers", log, touches, "render")
            top5 = hs.get("top5_buy_pct")
            if isinstance(hs.get("swap_count"), (int, float)) and isinstance(hs.get("unique_buyers"), (int, float)) and isinstance(top5, (int, float)):
                b = _patch_div(
                    b,
                    "rc-item-line",
                    "swaps ·",
                    f"{int(hs['swap_count'])} swaps · {int(hs['unique_buyers'])} buyers · top-5 ~{top5:.2f}% of gross buys.",
                    "F.RENDER.rc_swaps",
                    log,
                    touches,
                    "render",
                    "risk_confirmation",
                )
        oi30 = ((feeds.get("oi_30d") or {}).get("RENDER") or {}).get("pct_of_30d_max")
        if isinstance(oi30, (int, float)):
            b = _patch_kpi(b, "vs 30d max", f"~{oi30:.1f}%", "F.RENDER.oi30", log, touches, "render")
        return b

    html = _map_article(html, "render", rend_body)

    # ----- SOL -----
    def sol_body(b: str) -> str:
        row = _cg(feeds, "solana")
        if isinstance(row.get("circ"), (int, float)) and isinstance(row.get("total"), (int, float)) and row["total"]:
            pct = row["circ"] / row["total"] * 100
            b = _patch_dial(b, "Circulating", f"{pct:.1f}<span class='econ-u'>%</span>", "F.SOL.dial_circ", log, touches, "sol", sub=f"{row['circ']/1e6:.0f}M / {row['total']/1e6:.0f}M")
        sol_live = llama.get("sol") or assets.get("sol") or {}
        tvl = sol_live.get("tvl_usd")
        fees = sol_live.get("fees_7d_avg")
        if isinstance(tvl, (int, float)):
            b = _patch_kpi(b, "Now TVL", f"${tvl/1e9:.2f}B", "F.SOL.tvl", log, touches, "sol")
            b = _patch_kpi(b, "TVL", f"${tvl/1e9:.2f}B", "F.SOL.tvl2", log, touches, "sol")
            b = _patch_metric(b, "DefiLlama chain", f"${tvl/1e9:.2f}B", "F.SOL.metric_tvl", log, touches, "sol")
        if isinstance(fees, (int, float)):
            inner = f"${fees/1e3:.0f}<span class='econ-u'>k</span>"
            b = _patch_dial(b, "Fees", inner, "F.SOL.dial_fees", log, touches, "sol")
            b = _patch_kpi(b, "Now fees ±7d", f"${fees/1e3:.0f}k/d", "F.SOL.kpi_fees", log, touches, "sol")
            b = _patch_metric(b, "Paid network activity", f"${fees/1e3:.0f}k/d", "F.SOL.metric_fees", log, touches, "sol")
        stables = sol_live.get("stables_usd")
        if isinstance(stables, (int, float)):
            b = _patch_kpi(b, "Stables", f"${stables/1e9:.2f}B", "F.SOL.stables", log, touches, "sol")
            b = _patch_metric(b, "USD-pegged on Solana", f"${stables/1e9:.2f}B", "F.SOL.metric_stables", log, touches, "sol")
        p, ath = px("SOL", "solana"), row.get("ath")
        ddv = _retrace(p, ath)
        if ddv is not None:
            b = _patch_div(b, "rc-item-line", "from ATH", f"{_kprice(p)} · ~{ddv:.2f}% from ATH", "F.SOL.rc_px", log, touches, "sol", "risk_confirmation")
        if isinstance(tvl, (int, float)):
            nb, n = re.subn(r"TVL \$[\d.]+B", f"TVL ${tvl/1e9:.2f}B", b, count=1)
            if n == 1:
                b = nb
                _ok(log, touches, "F.SOL.rc_tvl", "sol", "risk_confirmation", "TVL $")
            else:
                _miss(log, "F.SOL.rc_tvl")
        sl = lev.get("SOL") or {}
        if isinstance(sl.get("perp_spot"), (int, float)):
            nb, n = re.subn(r"Fut/spot ~[\d.]+×", f"Fut/spot ~{sl['perp_spot']:.2f}×", b, count=1)
            if n == 1:
                b = nb
                _ok(log, touches, "F.SOL.rc_fut", "sol", "risk_confirmation", "Fut/spot")
            else:
                _miss(log, "F.SOL.rc_fut")
            b = _patch_flag(b, "Futures", f"Futures {sl['perp_spot']:.2f}× spot", "F.SOL.flag_fut", log, touches, "sol")
            b = _patch_metric(b, "Binance 24h slice", f"{sl['perp_spot']:.2f}× fut/spot", "F.SOL.metric_fut", log, touches, "sol")
        net = feeds.get("sol_rpc") or {}
        if net.get("ok"):
            st = net.get("stake_pct")
            inf = net.get("inflation_pct")
            iss = net.get("issuance_yr")
            if isinstance(st, (int, float)):
                b = _patch_kpi(b, "Stake", f"{st:.1f}%", "F.SOL.kpi_stake", log, touches, "sol")
                b = _patch_dial(b, "Staked", f"{st:.0f}<span class='econ-u'>%</span>", "F.SOL.dial_stake", log, touches, "sol")
                b = _patch_metric(b, "Vote-account activated stake", f"{st:.1f}%", "F.SOL.metric_stake", log, touches, "sol")
            if isinstance(inf, (int, float)):
                b = _patch_kpi(b, "Inflation", f"{inf:.2f}%", "F.SOL.kpi_inf", log, touches, "sol")
                b = _patch_dial(b, "Issuance<br>per year", f"{inf:.2f}<span class='econ-u'>%</span>", "F.SOL.dial_inf", log, touches, "sol")
                b = _patch_metric(b, "Issuance vs base-fee burn", f"{inf:.2f}% / burn thin", "F.SOL.metric_inf", log, touches, "sol")
            if isinstance(iss, (int, float)) and isinstance(inf, (int, float)) and isinstance(st, (int, float)):
                burn_yr = iss * 0.01  # placeholder avoided — use fees if present
                fees_d = sol_live.get("fees_7d_avg")
                burn_yr = (fees_d * 365 / (px("SOL", "solana") or 1)) if isinstance(fees_d, (int, float)) and isinstance(px("SOL", "solana"), (int, float)) else None
                net_yr = iss - burn_yr if isinstance(burn_yr, (int, float)) else iss
                net_pct = (net_yr / (net.get("total_sol") or 1)) * 100 if net.get("total_sol") else inf
                b = _patch_dial(b, "Net growth", f"{net_pct:.2f}<span class='econ-u'>%</span>", "F.SOL.dial_net", log, touches, "sol")
                b = _patch_kpi(b, "Issuance", f"~{iss:,.0f}/yr", "F.SOL.kpi_iss", log, touches, "sol")
                line = f"Staked {st:.1f}% · inflation {inf:.2f}% · net ~+{net_yr:,.0f} SOL/yr"
                b = _patch_div(b, "rc-item-line", "Staked ", line, "F.SOL.rc_stake", log, touches, "sol", "risk_confirmation")
            if isinstance(fees, (int, float)):
                b = _patch_div(
                    b,
                    "rc-item-line",
                    "Jan 2025",
                    f"Fees/TVL now far below Jan 2025 (${fees/1e3:.0f}k/d vs $10.2M/d).",
                    "F.SOL.rc_jan",
                    log,
                    touches,
                    "sol",
                    "risk_confirmation",
                )
        ratio = llama.get("dex_ratio") or {}
        if isinstance(ratio.get("ratio_7d"), (int, float)):
            b = _patch_kpi(b, "DEX 7d vs ETH L1", f"{ratio['ratio_7d']:.3f}×", "F.SOL.dex7", log, touches, "sol")
            b = _patch_metric(b, "7d mean volume share", f"{ratio['ratio_7d']:.3f}×", "F.SOL.metric_dex7", log, touches, "sol")
        if isinstance(ratio.get("ratio_24h"), (int, float)):
            b = _patch_kpi(b, "DEX latest", f"{ratio['ratio_24h']:.3f}×", "F.SOL.dex1", log, touches, "sol")
        return b

    html = _map_article(html, "sol", sol_body)

    # ----- SPX -----
    def spx_body(b: str) -> str:
        row = _cg(feeds, "spx6900")
        if isinstance(row.get("circ"), (int, float)):
            pct = row["circ"] / 1e9 * 100
            b = _patch_dial(b, "Circulating", f"{pct:.1f}<span class='econ-u'>%</span>", "F.SPX.dial_circ", log, touches, "spx6900", sub=f"{row['circ']/1e6:.0f}M / 1B")
            b = _patch_kpi(b, "Circ", f"{row['circ']/1e6:.1f}M", "F.SPX.kpi_circ", log, touches, "spx6900")
            b = _patch_div(b, "rc-item-line", "CG ~", f"CG ~{row['circ']/1e6:.1f}M / 1.00B · ETH totalSupply 1.00B.", "F.SPX.rc_circ", log, touches, "spx6900", "risk_confirmation")
            b = _patch_div(b, "rc-item-line", "~93% circulating", f"~{pct:.0f}% circulating; Solana map cannot answer global whale risk.", "F.SPX.rc_float", log, touches, "spx6900", "risk_confirmation")
            b = _patch_flag(b, "% circ · 69M", f"~{pct:.0f}% circ · 69M burned dead · unlock 0", "F.SPX.flag_circ", log, touches, "spx6900")
        p, ath = px("SPX6900", "spx6900"), row.get("ath")
        ddv = _retrace(p, ath)
        if ddv is not None and isinstance(ath, (int, float)):
            b = _patch_div(b, "rc-item-title", "retraced from ATH", f"~{abs(ddv):.0f}% retraced from ATH · zombie-risk zone", "F.SPX.rc_title", log, touches, "spx6900", "risk_confirmation")
            b = _patch_div(b, "rc-item-line", "ATH $2.27", f"{_kprice(p)} · ATH ${ath:.2f} · {ddv:.1f}%.", "F.SPX.rc_px", log, touches, "spx6900", "risk_confirmation")
        sl = lev.get("SPX6900") or {}
        if sl.get("ok"):
            spot = "Binance spot NOT LISTED" if not sl.get("spot_listed") else f"Binance spot 24h ~{_usd(sl.get('spot_quote_24h'))}"
            b = _patch_div(b, "rc-item-line", "Binance perp 24h", f"Binance perp 24h ~{_usd(sl.get('fut_quote_24h'))} · {spot}.", "F.SPX.rc_perp", log, touches, "spx6900", "risk_confirmation")
            if isinstance(sl.get("oi_usd"), (int, float)):
                b = _patch_kpi(b, "OI", _usd(sl["oi_usd"]) or "", "F.SPX.kpi_oi", log, touches, "spx6900")
                b = _patch_div(b, "rc-item-line", "OI ~$", f"OI ~{_usd(sl['oi_usd'])} · funding QUIET.", "F.SPX.rc_oi", log, touches, "spx6900", "risk_confirmation")
        conc = (feeds.get("concentration") or {}).get("SPX6900") or {}
        if conc.get("ok"):
            acc = conc.get("top_accounts") or []
            tot = conc.get("total_supply_ui") or 0
            if tot and acc:
                top20 = sum(a.get("ui_amount") or 0 for a in acc[:20]) / tot * 100
                b = _patch_kpi(b, "Sol top-20", f"~{top20:.1f}%", "F.SPX.top20", log, touches, "spx6900")
        oi30 = ((feeds.get("oi_30d") or {}).get("SPX6900") or {}).get("pct_of_30d_max")
        if isinstance(oi30, (int, float)):
            b = _patch_kpi(b, "Vs 30d max", f"~{oi30:.0f}%", "F.SPX.oi30", log, touches, "spx6900")
            if sl.get("ok") and isinstance(sl.get("oi_usd"), (int, float)):
                b = _patch_div(
                    b,
                    "rc-item-line",
                    "OI ~$",
                    f"OI ~{_usd(sl['oi_usd'])} · ~{oi30:.0f}% of 30d max · funding QUIET.",
                    "F.SPX.rc_oi30",
                    log,
                    touches,
                    "spx6900",
                    "risk_confirmation",
                )
        b = _patch_kpi(b, "Burned/dead", "69.0M", "F.SPX.dead", log, touches, "spx6900")
        wm = (feeds.get("labelled") or {}).get("spx_wm")
        if isinstance(wm, (int, float)) and wm > 0:
            pctm = wm / 1e9 * 100
            b = _patch_div(
                b,
                "rc-item-line",
                "WM ~",
                f"WM ~{wm:,.0f} SPX · {pctm:.4f}% of max (SOL registry).",
                "F.SPX.rc_wm",
                log,
                touches,
                "spx6900",
                "risk_confirmation",
            )
        sol_sup = (feeds.get("labelled") or {}).get("spx_sol_supply")
        cg_circ = row.get("circ")
        if isinstance(sol_sup, (int, float)) and isinstance(cg_circ, (int, float)) and cg_circ:
            b = _patch_div(
                b,
                "rc-item-line",
                "Multi-chain",
                f"Multi-chain; Solana ~{sol_sup/cg_circ*100:.0f}% of CG float.",
                "F.SPX.rc_solshare",
                log,
                touches,
                "spx6900",
                "risk_confirmation",
            )
        return b

    html = _map_article(html, "spx6900", spx_body)

    # ----- ZEC -----
    def zec_body(b: str) -> str:
        row = _cg(feeds, "zcash")
        if isinstance(row.get("circ"), (int, float)):
            pct = row["circ"] / 21_000_000 * 100
            b = _patch_dial(b, "Circulating", f"{pct:.1f}<span class='econ-u'>%</span>", "F.ZEC.dial_circ", log, touches, "zec", sub=f"{row['circ']/1e6:.1f}M / 21M")
        zec = feeds.get("zec") or {}
        if isinstance(zec.get("pct"), (int, float)):
            b = _patch_kpi(b, "Shielded", f"~{zec['pct']:.1f}%", "F.ZEC.shield_kpi", log, touches, "zec")
            b = _patch_flag(b, "chain shielded", f"~{zec['pct']:.0f}% of chain shielded", "F.ZEC.shield_flag", log, touches, "zec")
            b = _patch_div(
                b,
                "rc-item-line",
                "of chain",
                f"~{(zec.get('shielded') or 0)/1e6:.2f}M ZEC · ~{zec['pct']:.1f}% of chain. Snapshot, not a trend.",
                "F.ZEC.rc_shield",
                log,
                touches,
                "zec",
                "risk_confirmation",
            )
        p, ath = px("ZEC", "zcash"), row.get("ath")
        mcap = row.get("mcap")
        ch1y = row.get("chg_1y")
        if isinstance(p, (int, float)):
            mcap_s = f" · mcap {_usd(mcap)}" if isinstance(mcap, (int, float)) else ""
            y_s = f" · 1y {ch1y:+.1f}%" if isinstance(ch1y, (int, float)) else ""
            b = _patch_div(b, "rc-item-line", "Zcash L1", f"Zcash L1 · {_kprice(p)}{mcap_s}{y_s}.", "F.ZEC.rc_px", log, touches, "zec", "risk_confirmation")
        if isinstance(row.get("circ"), (int, float)):
            iss = 657_000.0
            inf = iss / row["circ"] * 100.0
            b = _patch_div(b, "rc-item-line", "circulating · est", f"~{row['circ']/21_000_000*100:.1f}% circulating · est. inflation ~{inf:.1f}% · issuance ≠ unlock.", "F.ZEC.rc_circ", log, touches, "zec", "risk_confirmation")
            b = _patch_dial(b, "Issuance<br>per year", f"{inf:.1f}<span class='econ-u'>%</span>", "F.ZEC.dial_iss", log, touches, "zec")
            b = _patch_dial(b, "Next 12m<br>issuance", "657k", "F.ZEC.dial_12m", log, touches, "zec")
            b = _patch_flag(b, "%/yr", f"~{inf:.1f}%/yr · next 12m ~657k ZEC", "F.ZEC.flag_iss", log, touches, "zec")
        zl = lev.get("ZEC") or {}
        if isinstance(zl.get("perp_spot"), (int, float)):
            oi_s = f" · OI {_usd(zl['oi_usd'])}" if isinstance(zl.get("oi_usd"), (int, float)) else ""
            b = _patch_div(b, "rc-item-line", "perp/spot", f"Spot live{oi_s} · perp/spot ~{zl['perp_spot']:.1f}×.", "F.ZEC.rc_fut", log, touches, "zec", "risk_confirmation")
            b = _patch_flag(b, "perp/spot", f"Binance perp/spot ~{zl['perp_spot']:.1f}×", "F.ZEC.flag_fut", log, touches, "zec")
        return b

    html = _map_article(html, "zec", zec_body)
    return html
