"""Job 2 QA integrity — hero/stance sync, RENDER deep patch, freshness, reconciliation."""

from __future__ import annotations

import re
from typing import Any

from lib.fetchers.http import get_json
from lib.v3.autojob01.contracts import PRICE_ASSETS

AS_OF = "2026-08-25"
OLD_ASOF = re.compile(r"2026-08-1[123]|11 Aug 2026|12 Aug 2026|13 Aug 2026", re.I)
FRESH_ASOF = re.compile(r"Freshness · 2026-08-25|Freshness · research_snapshot", re.I)


def _slug_sym_ticker(asset: str) -> tuple[str | None, str]:
    for sym, spec in PRICE_ASSETS.items():
        if spec.get("slug") == asset:
            ticker = spec.get("hero_ticker") or spec.get("html_ticker") or sym
            return sym, str(ticker)
    if asset == "spx6900":
        return "SPX6900", "SPX"
    return None, asset.upper()


def sync_hero_stance_prices_article(body: str, asset: str, bundle: dict[str, Any], log: list[str]) -> str:
    sym, ticker = _slug_sym_ticker(asset)
    if not sym:
        return body
    row = ((bundle.get("prices") or {}).get("assets") or {}).get(sym) or {}
    hero_m = re.search(r'<span class="alt-price">([^<]+)</span>', body)
    hero = (hero_m.group(1).strip() if hero_m else None) or row.get("print")
    if not hero:
        return body
    before = body
    body = re.sub(rf"({re.escape(ticker)})\s+at\s+\$[\d.,]+", rf"\1 at {hero}", body, flags=re.I)
    body = re.sub(rf"({re.escape(ticker)})\s+~?\$[\d.,]+", rf"\1 {hero}", body)
    body = re.sub(rf"({re.escape(ticker)})\s+~[\d.,]+", rf"\1 {hero}", body)
    if body != before:
        log.append(f"APPLY_OK SYNC.{asset}.stance_price")
    return body


def patch_render_usage_article(body: str, rend: dict[str, Any], log: list[str]) -> str:
    fr = (rend.get("frames") or {}).get("cumulative")
    bme = rend.get("bme") or {}
    emit = (rend.get("bme_emit") or {}).get("last4_emit")
    if not isinstance(fr, (int, float)) or fr <= 0:
        return body
    fr_s = f"{fr / 1e6:.2f}M"
    before = body
    body = re.sub(r"78\.07M", fr_s, body)
    body = re.sub(r"~78\.07M", f"~{fr_s}", body)
    if isinstance(bme.get("last4_burned"), (int, float)) and bme["last4_burned"] > 0:
        burn_k = f"{bme['last4_burned'] / 1e3:.1f}k"
        body = body.replace("12.8k", burn_k)
        body = body.replace("~12.8k", f"~{burn_k}")
    if isinstance(emit, (int, float)) and emit > 0:
        em_k = f"{emit / 1e3:.1f}k"
        body = re.sub(r"~60\.0k", f"~{em_k}", body)
        body = re.sub(r"emissions ~60\.0k", f"emissions ~{em_k}", body)
        body = re.sub(r"node emissions ~60\.0k", f"node emissions ~{em_k}", body)
    if body != before:
        log.append("APPLY_OK RENDER.usage_deep")
        body = _refresh_render_asof(body, log)
    nodes_stale = "5600" in body or "5,600" in body
    if nodes_stale and not rend.get("nodes_evidence_table"):
        body = _mark_nodes_evidence_stale(body, log)
    return body


def _refresh_render_asof(body: str, log: list[str]) -> str:
    def fix_block(m: re.Match[str]) -> str:
        block = m.group(0)
        if "78.07M" in block or "12.8k" in block:
            return block
        block = OLD_ASOF.sub(AS_OF, block)
        block = re.sub(r"Freshness · research_snapshot", f"Freshness · {AS_OF}", block)
        return block

    out = re.sub(r'<div class="ev-tip">.*?</div></div></div>', fix_block, body, flags=re.S)
    if out != body:
        log.append("APPLY_OK RENDER.asof_foot")
    return out


def _mark_nodes_evidence_stale(body: str, log: list[str]) -> str:
    """Nodes-since-inception table not re-fetched — do not imply fresh."""
    marker = "STALE · LAST VERIFIED 12 Aug 2026"
    if marker in body:
        return body
    body2, n = re.subn(
        r"(Nodes since inception \(evidence table\)[^<]*5600[^<]*)</span>",
        rf"\1 · {marker}</span>",
        body,
        count=1,
    )
    if n:
        log.append("APPLY_OK RENDER.nodes_stale")
        return body2
    return body


def fix_freshness_integrity_article(body: str, log: list[str]) -> str:
    """Never show Freshness 2026-08-25 on evidence still dated Aug 11–13."""

    def fix_tip(m: re.Match[str]) -> str:
        block = m.group(0)
        asof_m = re.search(r"As of · ([^<]+)", block)
        if not asof_m:
            return block
        asof = asof_m.group(1).strip()
        if not OLD_ASOF.search(asof):
            return block
        if f"Freshness · {AS_OF}" not in block and f'<span class="ev-v">{AS_OF}</span>' not in block:
            return block
        block = block.replace(f"Freshness · {AS_OF}", "Freshness · research_snapshot")
        block = re.sub(
            rf'<span class="ev-k">Freshness</span><span class="ev-v">{re.escape(AS_OF)}</span>',
            '<span class="ev-k">Freshness</span><span class="ev-v">research_snapshot</span>',
            block,
        )
        return block

    out = re.sub(r'<div class="ev-tip-foot">.*?</div></div>', fix_tip, body, flags=re.S)
    if out != body:
        log.append("APPLY_OK FRESH.revert_mismatch")
    return out


def fix_tape_label_double(text: str) -> str:
    text = re.sub(r"(?i)Market\s+market activity", "Market activity", text)
    text = re.sub(r"(?i)market\s+market activity", "market activity", text)
    text = re.sub(r"(?i)Market\s+tape", "Market activity", text)
    return text


def enrich_pump_buyback_daily(amd: dict[str, Any], bundle: dict[str, Any] | None) -> dict[str, Any]:
    """Rebuild 7d buyback bars + est PUMP bought from DefiLlama + Binance daily closes."""
    bundle = bundle or {}
    feeds = bundle.get("feeds") or {}
    llama = feeds.get("llama") or {}
    assets = bundle.get("assets") or {}
    pump_wrap = llama.get("pump") or assets.get("pump") or {}
    pump = pump_wrap.get("data") or pump_wrap
    buy = amd.setdefault("buyback", {})
    try:
        hold = get_json("https://api.llama.fi/summary/fees/pump.fun?dataType=dailyHoldersRevenue")
        chart = hold.get("totalDataChart") or []
        daily_usd = [float(v) for _, v in chart[-7:]] if len(chart) >= 7 else []
    except Exception:  # noqa: BLE001
        chart = []
        daily_usd = []
    if daily_usd:
        buy["daily_last7_usd"] = daily_usd
        buy["latest_daily_usd"] = daily_usd[-1]
        buy["daily_min_7d_usd"] = min(daily_usd)
        buy["daily_max_7d_usd"] = max(daily_usd)
        buy["total_7d_usd"] = sum(daily_usd)
        if len(chart) >= 14:
            prev = sum(float(v) for _, v in chart[-14:-7])
            buy["wow_pct"] = (buy["total_7d_usd"] - prev) / prev * 100 if prev else None
    rev7 = (pump.get("revenue") or {}).get("total_7d_usd")
    if isinstance(rev7, (int, float)):
        buy["revenue_7d_usd"] = rev7
    wow = (pump.get("buyback_burn") or {}).get("wow_pct")
    if isinstance(wow, (int, float)) and "wow_pct" not in buy:
        buy["wow_pct"] = wow
    prices = (bundle.get("prices") or {}).get("assets") or {}
    prow = prices.get("PUMP") or {}
    px = prow.get("price_usd")
    daily_px: list[float] = []
    try:
        kl = get_json(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": "PUMPUSDT", "interval": "1d", "limit": 7},
        )
        daily_px = [float(k[4]) for k in kl[-len(daily_usd) :]] if kl else []
    except Exception:  # noqa: BLE001
        daily_px = []
    if daily_usd and daily_px and len(daily_px) == len(daily_usd):
        est = [u / p for u, p in zip(daily_usd, daily_px)]
        buy["daily_last7_pump_est"] = est
        buy["pump_bought_7d_est"] = sum(est)
    elif isinstance(px, (int, float)) and px and daily_usd:
        est = [u / float(px) for u in daily_usd]
        buy["daily_last7_pump_est"] = est
        buy["pump_bought_7d_est"] = sum(est)
    tape = amd.setdefault("tape", {})
    if isinstance(px, (int, float)):
        tape["last_price"] = px
    pl = (feeds.get("perp_liquidity") or {}).get("PUMP") or {}
    if pl:
        tape.setdefault("futures_quote_24h_usd", pl.get("fut_quote_24h"))
        tape.setdefault("spot_quote_24h_usd", pl.get("spot_quote_24h"))
        tape.setdefault("funding_8h", pl.get("funding_8h"))
        if pl.get("fut_quote_24h") and pl.get("spot_quote_24h"):
            tape["read"] = "PERPS LEAD" if pl["fut_quote_24h"] > pl["spot_quote_24h"] else "SPOT LEAD"
    return amd


def _parse_usd_title(title: str) -> float | None:
    t = title.strip().replace(",", "").replace("$", "").strip()
    if not t:
        return None
    if t.endswith("M"):
        return float(t[:-1]) * 1e6
    if t.endswith("K") or t.endswith("k"):
        return float(t[:-1]) * 1e3
    try:
        return float(t)
    except ValueError:
        return None


def _parse_tok_title(title: str) -> float | None:
    t = title.strip()
    if t.endswith("B"):
        return float(t[:-1]) * 1e9
    if t.endswith("M"):
        return float(t[:-1]) * 1e6
    if t.endswith("k"):
        return float(t[:-1]) * 1e3
    try:
        return float(t)
    except ValueError:
        return None


def _chart_kpi_text(block: str) -> str:
    m = re.search(
        r'<span class="econ-chart-kpi">([^<]+)(?:<span[^>]*>([A-Za-z]+)</span>)?',
        block,
    )
    if not m:
        return ""
    return (m.group(1) + (m.group(2) or "")).replace(" ", "")


def reconciliation_qa(
    html: str,
    canonical: str,
    *,
    assets: tuple[str, ...],
    frozen: tuple[str, ...],
) -> dict[str, Any]:
    from lib.v3.autojob01.apply_pump_hero import ARTICLE_RE as PUMP_RE

    results: dict[str, Any] = {"overall": "PASS", "checks": []}

    def fail(name: str, detail: str) -> None:
        results["checks"].append({"check": name, "status": "FAIL", "detail": detail})
        results["overall"] = "FAIL"

    def ok(name: str, detail: str = "") -> None:
        results["checks"].append({"check": name, "status": "PASS", "detail": detail})

    pm = PUMP_RE.search(html)
    if pm:
        art = pm.group(0)
        dash_i = art.find('econ-dash pump-dash')
        dash = art[dash_i : dash_i + 12000] if dash_i >= 0 else ""
        charts = re.findall(
            r'<div class="econ-chart-wrap"><div class="econ-bars">(.*?)</div><span class="econ-chart-kpi">',
            dash,
            re.S,
        )
        if len(charts) >= 1:
            usd_titles = re.findall(r'title="([^"]+)"', charts[0])
            usd_vals = [_parse_usd_title(t) for t in usd_titles]
            kpi_txt = _chart_kpi_text(dash)
            kpi = _parse_usd_title(kpi_txt)
            if usd_vals and all(v is not None for v in usd_vals) and kpi:
                s = sum(usd_vals)  # type: ignore[type-var]
                if abs(s - kpi) / kpi > 0.02:
                    fail("pump_buyback_bars_sum", f"bars={s/1e6:.2f}M kpi={kpi/1e6:.2f}M")
                else:
                    ok("pump_buyback_bars_sum", f"{s/1e6:.2f}M ≈ {kpi/1e6:.2f}M")
        if len(charts) >= 2:
            tok_titles = re.findall(r'title="([^"]+)"', charts[1])
            tok_vals = [_parse_tok_title(t) for t in tok_titles]
            second = dash.split('<div class="econ-chart-wrap">', 2)[2] if dash.count("econ-chart-wrap") >= 2 else ""
            kpi_txt = _chart_kpi_text(second)
            kpi = _parse_tok_title(kpi_txt)
            if tok_vals and all(v is not None for v in tok_vals) and kpi:
                s = sum(tok_vals)  # type: ignore[type-var]
                if abs(s - kpi) / kpi > 0.03:
                    fail("pump_est_bought_bars_sum", f"bars={s/1e9:.2f}B kpi={kpi/1e9:.2f}B")
                else:
                    ok("pump_est_bought_bars_sum", f"{s/1e9:.2f}B ≈ {kpi/1e9:.2f}B")
        if "Market market activity" in art or "market market activity" in art:
            fail("pump_tape_label", "Market market activity present")
        else:
            ok("pump_tape_label")

    for asset in assets:
        m = re.search(rf'<article[^>]*\bdata-asset="{re.escape(asset)}"[^>]*>.*?</article>', html, re.S)
        if not m:
            continue
        body = m.group(0)
        hero = re.search(r'<span class="alt-price">([^<]+)</span>', body)
        if not hero:
            continue
        hp = hero.group(1).strip()
        _, ticker = _slug_sym_ticker(asset)
        bad = re.findall(rf"{re.escape(ticker)}(?:\s+at)?\s+~?\$[\d.,]+", body)
        hero_norm = re.sub(r"[^\d.]", "", hp)
        stale_hits = []
        for match in bad:
            stale_norm = re.sub(r"[^\d.]", "", match)
            if stale_norm and hero_norm and stale_norm != hero_norm:
                stale_hits.append(match)
        if stale_hits:
            fail(f"hero_stance_{asset}", f"hero={hp} stale={stale_hits[:2]}")
        else:
            ok(f"hero_stance_{asset}", hp)

    for asset in assets:
        m = re.search(rf'<article[^>]*\bdata-asset="{re.escape(asset)}"[^>]*>.*?</article>', html, re.S)
        if not m:
            continue
        for foot in re.finditer(r'<div class="ev-tip-foot">.*?</div></div>', m.group(0), re.S):
            block = foot.group(0)
            asof_m = re.search(r"As of · ([^<]+)", block)
            if not asof_m:
                continue
            asof = asof_m.group(1).strip()
            if OLD_ASOF.search(asof) and f"Freshness · {AS_OF}" in block:
                fail(f"freshness_mismatch_{asset}", f"as-of={asof[:20]} freshness={AS_OF}")
                break
        else:
            ok(f"freshness_mismatch_{asset}")

    rm = re.search(r'<article[^>]*\bdata-asset="render"[^>]*>.*?</article>', html, re.S)
    if rm:
        r = rm.group(0)
        if "78.07M" in r:
            fail("render_frames", "78.07M still present")
        elif "STALE · LAST VERIFIED" in r or re.search(r"78\.\d{2}M", r):
            ok("render_frames", "refreshed or marked stale")
        else:
            ok("render_frames", "no stale 78.07M")

    for asset in frozen:
        cm = re.search(rf'<article[^>]*\bdata-asset="{re.escape(asset)}"[^>]*>.*?</article>', canonical, re.S)
        am = re.search(rf'<article[^>]*\bdata-asset="{re.escape(asset)}"[^>]*>.*?</article>', html, re.S)
        if cm and am and cm.group(0) == am.group(0):
            ok(f"frozen_{asset}", "byte-identical")
        elif cm and am:
            fail(f"frozen_{asset}", "article changed")

    return results
