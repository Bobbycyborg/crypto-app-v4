#!/usr/bin/env python3
"""Atomic fact classification: windows, update modes, growable families. Not a small whitelist ceiling."""
from __future__ import annotations

import re
from copy import deepcopy

BANNED_FAMILIES = {"captured", "usd_figure", "pct_figure", "pp_figure"}
DORMANT_SLUGS = {"ray", "grass"}
META_KEYS = {
    "evidence", "confidence", "freshness", "caveat", "unknown", "detail",
    "sample", "discipline", "label", "scope", "rule", "status", "read",
    "coverage", "verdict", "note", "known",
}
PROSE_RE = re.compile(r"volume|estimate|formula|last price|× 24h|×24h|explanatory", re.I)
HAS_NUM = re.compile(r"\d")
SLASH_SPLIT = re.compile(r"\s*/\s*")

# rest → (definition, value_kind, allowed_unit, shape)
CATALOG: dict[str, tuple[str, str, str, str]] = {}


def family(rest: str, definition: str, value_kind: str, unit: str, shape: str) -> None:
    CATALOG[rest] = (definition, value_kind, unit, shape)


def _seed() -> None:
    if CATALOG:
        return
    family("price.usd.live", "Live USD mark for {ASSET} from the hold/desk ticker that updates with the page feed.", "PRICE_USD", "USD", "price_usd")
    family("price.usd.report", "USD price for {ASSET} frozen in the report snapshot, not the live ticker.", "PRICE_USD", "USD", "price_usd")
    family("price.ath.usd", "All-time-high USD price of {ASSET} as a historical reference point, not the live price.", "PRICE_USD", "USD", "price_usd")
    family("price.drawdown_from_ath.pct", "Percent change from {ASSET} all-time-high price to the listed snapshot price: (current / ATH) - 1.", "PERCENT", "%", "percent")
    family("threshold.out.usd", "Fixed hold-card OUT / SELL USD level for {ASSET}, a judgemental exit threshold, not a live market feed.", "PRICE_USD", "USD", "threshold")
    family("threshold.this_move.usd", "Fixed hold-card this-move USD level for {ASSET}, a judgemental shelf, not a live market feed.", "PRICE_USD", "USD", "threshold")
    family("etf.flow.usd.1d", "USD net spot ETF flow for {ASSET} over the latest one-day window (Farside).", "USD_AMOUNT", "USD", "usd_amount")
    family("etf.flow.usd.7d", "USD net spot ETF flow for {ASSET} over the trailing seven-day window (Farside).", "USD_AMOUNT", "USD", "usd_amount")
    family("etf.flow.usd.30d", "USD net spot ETF flow for {ASSET} over the trailing thirty-day window (Farside).", "USD_AMOUNT", "USD", "usd_amount")
    family("etf.flow.usd.all_time", "Cumulative USD net spot ETF flow for {ASSET} since inception (Farside), a historical total.", "USD_AMOUNT", "USD", "usd_amount")
    family("buyback.usd.7d", "USD value of protocol-funded {ASSET} market purchases over the trailing seven-day period.", "USD_7D_TOTAL", "USD", "usd_amount")
    family("buyback.usd.1d", "USD value of protocol-funded {ASSET} market purchases for the latest daily observation.", "USD_AMOUNT", "USD", "usd_amount")
    family("buyback.change.pct.7d", "Percent change in trailing seven-day {ASSET} buybacks versus the prior seven-day period.", "PERCENT", "%", "percent")
    family("revenue.usd.7d", "USD protocol revenue for {ASSET} over the trailing seven-day period.", "USD_7D_TOTAL", "USD", "usd_amount")
    family("revenue.usd.30d", "USD protocol revenue for {ASSET} over the trailing thirty-day period.", "USD_30D_TOTAL", "USD", "usd_amount")
    family("revenue.usd.cumulative", "Cumulative USD network or protocol earnings for {ASSET} as currently shown.", "USD_AMOUNT", "USD", "usd_amount")
    family("revenue.usd.july_2026", "USD network earnings for {ASSET} in July 2026, a historical monthly total.", "USD_AMOUNT", "USD", "usd_amount")
    family("revenue.usd.may_2026", "USD network earnings for {ASSET} in May 2026, a historical monthly total.", "USD_AMOUNT", "USD", "usd_amount")
    family("revenue.usd.june_2026", "USD network earnings for {ASSET} in June 2026, a historical monthly total.", "USD_AMOUNT", "USD", "usd_amount")
    family("revenue.usd_per_day.mean_30d", "USD per day {ASSET} earnings as a 30-day average.", "USD_PER_DAY_MEAN_30D", "USD/day", "usd_per_day")
    family("fees.usd.7d", "USD protocol or venue fees for {ASSET} over the trailing seven days.", "USD_7D_TOTAL", "USD", "usd_amount")
    family("fees.usd.30d", "USD protocol or venue fees for {ASSET} over the trailing thirty days.", "USD_30D_TOTAL", "USD", "usd_amount")
    family("fees.usd.1d", "USD protocol or venue fees for {ASSET} over the latest one-day or 24h window.", "USD_AMOUNT", "USD", "usd_amount")
    family("fees.usd_per_day.mean_30d", "USD per day {ASSET} fees as a 30-day mean.", "USD_PER_DAY_MEAN_30D", "USD/day", "usd_per_day")
    family("fees.usd_per_day.current", "USD per day {ASSET} fees as currently shown (not a 7d or 30d mean unless labelled).", "USD_PER_DAY", "USD/day", "usd_per_day")
    family("revenue.usd_per_day.current", "USD per day {ASSET} revenue as currently shown.", "USD_PER_DAY", "USD/day", "usd_per_day")
    family("fees.usd_per_day.nov_2024", "USD per day {ASSET} fees at the November 2024 historical window.", "USD_PER_DAY", "USD/day", "usd_per_day")
    family("fees.usd_per_day.june_2026", "USD per day {ASSET} fees at the June 2026 historical low window.", "USD_PER_DAY", "USD/day", "usd_per_day")
    family("fees.usd_per_day.jan_2025_ath", "USD per day {ASSET} fees at the January 2025 ATH window.", "USD_PER_DAY", "USD/day", "usd_per_day")
    family("fees.change.pct.30d", "Percent change in {ASSET} fees versus the prior 30-day period.", "PERCENT", "%", "percent")
    family("supply.circulating.pct", "Circulating supply of {ASSET} as a percent of the stated max or total supply.", "PERCENT", "%", "percent")
    family("supply.circulating.tokens", "Circulating token quantity of {ASSET} as currently shown.", "TOKEN_AMOUNT", "tokens", "token_or_count")
    family("supply.max.tokens", "Maximum or total token quantity of {ASSET} as currently shown.", "TOKEN_AMOUNT", "tokens", "token_or_count")
    family("holders.top20.pct", "Share of {ASSET} supply held by the top-20 addresses in the stated mint/set.", "PERCENT", "%", "percent")
    family("solana_supply_share.pct", "Share of {ASSET} circulating supply that exists as the Solana mint, versus the CoinGecko circulating total.", "PERCENT", "%", "percent")
    family("leverage.perp_spot_notional.x", "Ratio of Binance perpetual notional to Coinbase estimated spot notional for {ASSET}.", "RATIO_X", "x", "ratio_x")
    family("leverage.x.current", "Stated perpetual-to-spot or venue leverage multiple for {ASSET} as currently shown.", "RATIO_X", "x", "ratio_x")
    family("oi.usd.current", "Open interest in USD for {ASSET} as currently shown.", "USD_AMOUNT", "USD", "usd_amount")
    family("oi.btc.current", "Open interest in BTC for {ASSET} as currently shown.", "TOKEN_AMOUNT", "BTC", "token_or_count")
    family("oi.change.pct.1d", "Percent change in {ASSET} open interest over one day.", "PERCENT", "%", "percent")
    family("oi.change.pct.7d", "Percent change in {ASSET} open interest over seven days.", "PERCENT", "%", "percent")
    family("oi.change.pct.30d", "Percent change in {ASSET} open interest over thirty days.", "PERCENT", "%", "percent")
    family("funding.rate.latest", "Latest perpetual funding print for {ASSET} (not a 7-day mean).", "FUNDING_RATE", "rate", "funding_rate")
    family("funding.rate.mean_7d", "Seven-day mean perpetual funding for {ASSET} (not the latest print).", "FUNDING_RATE", "rate", "funding_rate")
    family("funding.percentile.current", "Percentile rank of {ASSET} perpetual funding versus its own history.", "COUNT", "percentile", "any_numeric")
    family("return.pct.7d", "Percent price change of {ASSET} over the trailing seven days.", "PERCENT", "%", "percent")
    family("return.pct.30d", "Percent price change of {ASSET} over the trailing thirty days.", "PERCENT", "%", "percent")
    family("return.pct.90d", "Percent price change of {ASSET} over the trailing ninety days.", "PERCENT", "%", "percent")
    family("return.pct.180d", "Percent price change of {ASSET} over the trailing 180 days.", "PERCENT", "%", "percent")
    family("fear_greed.index.current", "CNN-style crypto fear and greed index level currently shown for the market.", "INDEX", "index", "index_0_100")
    family("participation.beat_btc.count", "Count of names in the Market Participation set that beat Bitcoin over the stated window.", "COUNT", "count", "count")
    family("participation.above_50dma.count", "Count of names in the Market Participation set above their 50-day average.", "COUNT", "count", "count")
    family("portfolio.value.usd.current", "USD total of watched-wallet holdings currently shown as portfolio value.", "USD_AMOUNT", "USD", "usd_amount")
    family("siren.watched_wallet_count.current", "Count of watched wallets in the siren lane for {ASSET}.", "COUNT", "count", "count")
    family("siren.tracked.tokens.current", "Watched-wallet tracked token quantity for {ASSET} from the siren header.", "TOKEN_AMOUNT", "tokens", "token_or_count")
    family("siren.supply.tokens.current", "Siren-header circulating/supply token quantity for {ASSET}.", "TOKEN_AMOUNT", "tokens", "token_or_count")
    family("siren.aug1_unknown_wallet_count.current", "Count of watched wallets for {ASSET} whose official 1 Aug 2026 00:00 UTC start value is UNKNOWN.", "COUNT", "count", "count")
    family("tokens_bought.7d", "Estimated {ASSET} tokens purchased via buybacks over the trailing seven days.", "TOKEN_AMOUNT", "tokens", "token_or_count")
    family("ma.usd.20d", "20-day moving-average USD (or venue) level for {ASSET} as shown.", "MA_LEVEL", "USD", "ma_level")
    family("ma.usd.50d", "50-day moving-average USD (or venue) level for {ASSET} as shown.", "MA_LEVEL", "USD", "ma_level")
    family("ma.usd.200d", "200-day moving-average USD (or venue) level for {ASSET} as shown.", "MA_LEVEL", "USD", "ma_level")
    family("tvl.usd.current", "Total value locked in USD for {ASSET} as currently shown.", "USD_AMOUNT", "USD", "usd_amount")
    family("tvl.usd.jan_2025", "Total value locked in USD for {ASSET} at the January 2025 historical window.", "USD_AMOUNT", "USD", "usd_amount")
    family("stablecoin.usd.current", "USD-pegged stablecoin stock on {ASSET} as currently shown.", "USD_AMOUNT", "USD", "usd_amount")
    family("stake.ratio.pct", "Share of {ASSET} supply that is staked, as currently shown.", "PERCENT", "%", "percent")
    family("stake.tokens.current", "Quantity of {ASSET} that is staked, as currently shown.", "TOKEN_AMOUNT", "tokens", "token_or_count")
    family("inflation.pct.current", "Stated annual inflation rate for {ASSET}.", "PERCENT", "%", "percent")
    family("tps.nonvote.current", "Non-vote transactions-per-second snapshot for {ASSET}.", "COUNT", "count", "count")
    family("tps.all.current", "All transactions-per-second snapshot for {ASSET}.", "COUNT", "count", "count")
    family("liquidity.dex.usd.current", "DEX pool liquidity in USD for {ASSET} as currently shown.", "USD_AMOUNT", "USD", "usd_amount")
    family("market_share.pct.current", "Launchpad or venue market share for {ASSET} as currently shown.", "PERCENT", "%", "percent")
    family("market_cap.usd.current", "Market cap in USD for {ASSET} as currently shown.", "USD_AMOUNT", "USD", "usd_amount")
    family("usage.frames.cumulative", "Cumulative frames rendered on the {ASSET} network as currently shown.", "TOKEN_AMOUNT", "frames", "token_or_count")
    family("bme.ratio.last4", "Burn-versus-emissions ratio for {ASSET} over the last four epochs.", "RATIO_X", "x", "ratio_loose")
    family("bme.ratio.last8", "Burn-versus-emissions ratio for {ASSET} over the last eight epochs.", "RATIO_X", "x", "ratio_loose")
    family("af.inventory.tokens.current", "Assistance Fund HYPE inventory currently shown.", "TOKEN_AMOUNT", "tokens", "token_or_count")
    family("af.buys.usd.30d", "Assistance Fund USD buys of HYPE over a trailing 30-day window.", "USD_30D_TOTAL", "USD", "usd_amount")
    family("emissions.tokens.remaining", "Remaining future token emissions for {ASSET} as currently shown.", "TOKEN_AMOUNT", "tokens", "token_or_count")
    family("volume.usd.24h", "USD traded volume for {ASSET} over 24 hours as currently shown.", "USD_AMOUNT", "USD", "usd_amount")
    family("rs.vs_btc.pct.7d", "Relative-strength percent of {ASSET} versus Bitcoin over seven days.", "PERCENT", "%", "percent")
    family("rs.vs_btc.pct.30d", "Relative-strength percent of {ASSET} versus Bitcoin over thirty days.", "PERCENT", "%", "percent")
    family("rs.vs_sol.pct.7d", "Relative-strength percent of {ASSET} versus Solana over seven days.", "PERCENT", "%", "percent")
    family("rs.vs_sol.pct.30d", "Relative-strength percent of {ASSET} versus Solana over thirty days.", "PERCENT", "%", "percent")
    family("rs.vs_btc.pp.7d", "Relative-strength gap of {ASSET} versus Bitcoin over seven days, in percentage points.", "PERCENTAGE_POINTS", "pp", "pp")
    family("rs.vs_btc.pp.30d", "Relative-strength gap of {ASSET} versus Bitcoin over thirty days, in percentage points.", "PERCENTAGE_POINTS", "pp", "pp")
    family("rs.vs_sol.pp.7d", "Relative-strength gap of {ASSET} versus Solana over seven days, in percentage points.", "PERCENTAGE_POINTS", "pp", "pp")
    family("rs.vs_sol.pp.30d", "Relative-strength gap of {ASSET} versus Solana over thirty days, in percentage points.", "PERCENTAGE_POINTS", "pp", "pp")
    family("jobs.running.count", "Currently running jobs on the {ASSET} network.", "COUNT", "count", "count")
    family("jobs.queued.count", "Currently queued jobs on the {ASSET} network.", "COUNT", "count", "count")
    family("jobs.completed.cumulative", "Cumulative completed jobs on the {ASSET} network.", "COUNT", "count", "count")
    family("gpu_hours.approx_31d", "GPU-hours on the {ASSET} network over about 31 days.", "COUNT", "count", "count")
    family("dex_eth_ratio.x.current", "Solana DEX volume versus Ethereum L1 DEX volume, as a multiple.", "RATIO_X", "x", "ratio_x")


_seed()
DEFS = {k: v[0] for k, v in CATALOG.items()}
TYPE_SPEC = {k: (v[1], v[2], v[3]) for k, v in CATALOG.items()}


def parse_raw(literal: str):
    s = (literal or "").strip().replace("~", "").replace(",", "").replace(" ", "")
    m = re.search(r"(-?\d+(?:\.\d+)?)([KMBTkmbt%x×]?)", s.replace("$", "").replace("/wk", "").replace("/d", ""))
    if not m:
        return "UNKNOWN"
    n = float(m.group(1))
    suf = m.group(2).upper()
    if suf in ("%", "X", "×"):
        return n
    return n * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}.get(suf, 1)


def detect_kind(lit: str) -> str:
    s = (lit or "").strip()
    if not s:
        return "EMPTY"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T[\d:.]+Z?)?", s):
        return "DATE"
    if PROSE_RE.search(s) and not re.search(r"[x×]", s) and "$" not in s:
        return "PROSE"
    if re.search(r"\d+\s*pp\b", s, re.I) or s.lower().endswith("pp"):
        return "PERCENTAGE_POINTS"
    if re.fullmatch(r"[A-Za-z][A-Za-z /·.+%-]{1,40}", s) and not re.search(r"\d", s):
        return "STATUS_TEXT"
    if "/d" in s.lower() and "$" in s:
        return "USD_PER_DAY"
    if re.search(r"/8h|e-0|/ 8h", s, re.I) and "$" not in s:
        return "FUNDING_RATE"
    if re.search(r"[x×]", s) and "$" not in s and "%" not in s:
        return "RATIO_X"
    if "$" in s:
        raw = parse_raw(s)
        if "/wk" in s.lower():
            return "USD_7D_TOTAL"
        if isinstance(raw, (int, float)) and raw >= 1e8:
            return "USD_AMOUNT"
        if re.search(r"[MBT]\b", s.replace(",", "")):
            return "USD_AMOUNT"
        return "PRICE_USD" if isinstance(raw, (int, float)) and raw < 1e8 else "USD_AMOUNT"
    if "%" in s:
        return "PERCENT"
    if re.search(r"\d+\s*of\s*\d+", s, re.I):
        return "COUNT"
    if re.search(r"\d+(?:\.\d+)?[KMBT]\b", s, re.I) and "$" not in s:
        return "TOKEN_AMOUNT"
    if re.search(r"\b(BTC|SOL|ETH|PUMP|HYPE|tokens?|ZEC)\b", s, re.I) and "$" not in s:
        return "TOKEN_AMOUNT"
    if re.fullmatch(r"[+\-−]\d+(?:\.\d+)?", s):
        return "DELTA"
    if re.fullmatch(r"~?\d+(?:\.\d+)?", s):
        return "COUNT"
    if re.search(r"\d", s):
        return "OTHER"
    return "STATUS_TEXT"


def shape_ok(shape: str, lit: str) -> bool:
    kind = detect_kind(lit)
    if shape == "ratio_x":
        return kind == "RATIO_X" and "$" not in lit and "%" not in lit and not PROSE_RE.search(lit)
    if shape == "ratio_loose":
        return kind in {"RATIO_X", "INDEX", "COUNT", "OTHER"} and "$" not in lit and "%" not in lit
    if shape == "percent":
        return kind in {"PERCENT", "PERCENTAGE_POINTS"} and "$" not in lit
    if shape == "percent_or_rate":
        return kind in {"PERCENT", "FUNDING_RATE"} and "$" not in lit
    if shape == "funding_rate":
        return kind in {"FUNDING_RATE", "PERCENT", "INDEX", "OTHER", "DELTA"} and "$" not in lit
    if shape == "usd_amount":
        return kind in {"USD_AMOUNT", "PRICE_USD", "USD_7D_TOTAL", "USD_PER_DAY"} and "$" in lit and "×" not in lit
    if shape == "usd_per_day":
        return "$" in lit and ("/d" in lit.lower() or detect_kind(lit) in {"USD_PER_DAY", "USD_AMOUNT", "PRICE_USD"})
    if shape == "price_usd":
        return "$" in lit and "%" not in lit and "/d" not in lit.lower() and "/wk" not in lit.lower()
    if shape == "threshold":
        if lit.strip() in {"—", "-", "–", ""}:
            return True
        if "close" in lit.lower() or "under" in lit.lower():
            return True
        return "$" in lit or lit.strip() in {"—"}
    if shape == "index_0_100":
        if detect_kind(lit) in {"DATE", "DELTA", "STATUS_TEXT", "PERCENT"}:
            return False
        if lit.startswith("+") or lit.startswith("−"):
            return False
        try:
            n = float(re.sub(r"[^\d.]", "", lit))
        except ValueError:
            return False
        return 0 <= n <= 100
    if shape == "count":
        return kind in {"COUNT", "INDEX", "TOKEN_AMOUNT", "OTHER"} and "$" not in lit
    if shape == "token_or_count":
        return kind in {"TOKEN_AMOUNT", "COUNT", "INDEX", "OTHER"} and "$" not in lit
    if shape == "ma_level":
        return kind in {"PRICE_USD", "USD_AMOUNT", "INDEX", "COUNT", "OTHER", "TOKEN_AMOUNT"} or bool(re.search(r"\d", lit))
    if shape == "pp":
        return kind in {"PERCENTAGE_POINTS", "PERCENT", "DELTA"} or "pp" in lit.lower()
    if shape == "any_numeric":
        return bool(re.search(r"\d", lit))
    return False


def ensure(rest: str, lit: str, definition: str | None = None) -> str:
    if rest.split(".")[0] in BANNED_FAMILIES:
        raise ValueError(rest)
    if rest not in CATALOG:
        kind = detect_kind(lit)
        vk, unit, shape = spec_from_kind(kind, rest, lit)
        defn = definition or (
            f"The {rest.replace('.', ' ')} quantity for {{ASSET}} as shown on this dashboard; "
            "time basis and unit are encoded in the metric id."
        )
        CATALOG[rest] = (defn, vk, unit, shape)
        DEFS[rest] = defn
        TYPE_SPEC[rest] = (vk, unit, shape)
    return rest


def spec_from_kind(kind: str, rest: str, lit: str) -> tuple[str, str, str]:
    if "usd_per_day" in rest or "/d" in lit.lower():
        return ("USD_PER_DAY_MEAN_30D" if "mean_30d" in rest else "USD_PER_DAY", "USD/day", "usd_per_day")
    if rest.endswith(".30d") and "usd" in rest:
        return ("USD_30D_TOTAL", "USD", "usd_amount")
    if rest.endswith(".7d") and "usd" in rest:
        return ("USD_7D_TOTAL", "USD", "usd_amount")
    if "funding" in rest:
        return ("FUNDING_RATE", "rate", "funding_rate")
    if rest.endswith(".pp") or ".pp." in rest:
        return ("PERCENTAGE_POINTS", "pp", "pp")
    if "ma.usd" in rest:
        return ("MA_LEVEL", "USD", "ma_level")
    mapping = {
        "USD_AMOUNT": ("USD_AMOUNT", "USD", "usd_amount"),
        "USD_PER_DAY": ("USD_PER_DAY", "USD/day", "usd_per_day"),
        "USD_7D_TOTAL": ("USD_7D_TOTAL", "USD", "usd_amount"),
        "PRICE_USD": ("PRICE_USD", "USD", "price_usd"),
        "PERCENT": ("PERCENT", "%", "percent"),
        "PERCENTAGE_POINTS": ("PERCENTAGE_POINTS", "pp", "pp"),
        "RATIO_X": ("RATIO_X", "x", "ratio_x"),
        "TOKEN_AMOUNT": ("TOKEN_AMOUNT", "tokens", "token_or_count"),
        "COUNT": ("COUNT", "count", "count"),
        "INDEX": ("INDEX", "index", "index_0_100"),
        "FUNDING_RATE": ("FUNDING_RATE", "rate", "funding_rate"),
    }
    return mapping.get(kind, ("USD_AMOUNT" if "$" in lit else "COUNT", "text", "any_numeric"))


def type_accepts(rest: str, lit: str) -> bool:
    spec = TYPE_SPEC.get(rest)
    if not spec:
        return False
    return shape_ok(spec[2], lit)


def slug_id(asset_slug: str, rest: str) -> str:
    a = "fart" if asset_slug == "fartcoin" else "spx" if asset_slug == "spx6900" else asset_slug
    a = re.sub(r"[^a-z0-9]+", "", a)
    return f"{a}.{rest}"


def infer_window(row: str, tip: str, hint: str, lit: str, parent_label: str = "") -> str:
    b = f"{row} {tip} {hint} {lit} {parent_label}".lower()
    if "nov 2024" in b:
        return "nov_2024"
    if "june 2026" in b and "fee" in b:
        return "june_2026"
    if "ath sep" in b or (re.search(r"\bath\b", b) and re.search(r"\bsep\b", b)):
        return "ath_sep"
    if "jan high" in b:
        return "jan_high"
    if "june atl" in b or "jun atl" in b:
        return "june_atl"
    if "jan 2025" in b and ("fee" in b or "ath" in b) and "tvl" not in row:
        return "jan_2025_ath"
    if "jan 2025" in b and "tvl" in b:
        return "jan_2025"
    if re.search(r"\bjuly\b", row) and "earn" in b:
        return "july_2026"
    if re.search(r"\bmay\b", row) and "earn" in b:
        return "may_2026"
    if re.search(r"\bjune\b", row) and "earn" in b:
        return "june_2026"
    if "cumulative" in b or row == "cumulative":
        return "cumulative"
    if "/d" in lit.lower() or "/ day" in hint or "per day" in b or "avg /d" in b or "avg/day" in b:
        if "30d" in b or "30d" in hint:
            return "mean_30d"
        if "7d" in b or "±7d" in b or "+/-7d" in b:
            return "mean_7d"
        return "per_day"
    if "latest" in row or "latest print" in b or "latest 8h" in b:
        return "latest"
    if "7d mean" in b or row == "7d mean":
        return "mean_7d"
    compact = b.replace(" ", "").replace("-", "")
    for token, w in (
        ("alltime", "all_time"), ("all-time", "all_time"),
        ("180d", "180d"), ("90d", "90d"), ("30d", "30d"),
        ("7d", "7d"), ("24h", "1d"), ("1d", "1d"),
    ):
        if token.replace("-", "") in compact:
            return w
    if hint.strip().lower() in {"30d", "7d", "1d"}:
        return hint.strip().lower()
    return "current"


def is_historical_window(win: str) -> bool:
    return win in {
        "nov_2024", "june_2026", "jan_2025", "jan_2025_ath",
        "july_2026", "may_2026", "all_time", "ath",
        "ath_sep", "jan_high", "june_atl",
    }


def update_mode_for(c: dict, rest: str, mtype: str) -> str:
    if mtype == "WALLET_OWNED" or rest.startswith("siren.") or rest.startswith("portfolio."):
        return "WALLET_SNAPSHOT"
    if mtype == "STATIC_DECISION_THRESHOLD":
        return "STATIC_THRESHOLD"
    if mtype == "HISTORICAL" or is_historical_window(rest.split(".")[-1]):
        return "HISTORICAL"
    cs = set((c.get("element_class") or "").split())
    kind = c.get("kind") or ""
    if "hold-px" in cs or kind == "attr:data-live-px" or "desk-px" in cs:
        return "LIVE"
    if rest.endswith(".live") or rest == "price.usd.live":
        return "LIVE"
    return "REPORT_SNAPSHOT"


def has_number(lit: str) -> bool:
    return bool(HAS_NUM.search(lit or ""))


def explode_atomic(cands: list[dict]) -> list[dict]:
    out: list[dict] = []
    for c in cands:
        kids = _children_from(c)
        if kids:
            parent = deepcopy(c)
            parent["kind"] = parent.get("kind") or "compound"
            parent["is_compound_parent"] = True
            out.append(parent)
            out.extend(kids)
        else:
            out.append(c)
    return out


def _child(parent: dict, literal: str, label: str, extra_rest: str | None = None) -> dict:
    ch = deepcopy(parent)
    ch["literal"] = re.sub(r"\s+", " ", literal).strip()
    ch["parent_label"] = parent.get("label") or ""
    ch["label"] = label
    ch["parent_occurrence_id"] = parent["occurrence_id"]
    ch["kind"] = "atomic_span"
    ch["is_compound_parent"] = False
    ch["occurrence_id"] = parent["occurrence_id"] + ":" + re.sub(r"[^a-z0-9]+", "", (label + literal).lower())[:18]
    if extra_rest:
        ch["forced_rest"] = extra_rest
    return ch


def _children_from(c: dict) -> list[dict]:
    if c.get("kind") == "econ_bar_title":
        return []
    lit = c.get("literal") or ""
    row = (c.get("label") or "").strip()
    row_l = row.lower()
    kids: list[dict] = []

    labs = [x.strip() for x in SLASH_SPLIT.split(row) if x.strip()]
    vals = [x.strip() for x in SLASH_SPLIT.split(lit) if x.strip()]
    if (
        len(labs) >= 2
        and len(vals) == len(labs)
        and all(has_number(v) for v in vals)
        and len(lit) < 160
        and row_l not in META_KEYS
        and "unlockschedule" not in row_l.replace(" ", "")
    ):
        for lab, val in zip(labs, vals):
            kids.append(_child(c, val, lab))
        return kids

    # percent + explicit window only (do not split "Staked 68.8% · inflation 3.7%")
    bits = re.findall(r"([+\-−]?\d[\d.]*%\s*(?:1d|7d|30d|90d|180d))", lit, re.I)
    if len(bits) >= 2 and row_l not in META_KEYS:
        for bit in bits:
            w = re.search(r"(1d|7d|30d|90d|180d)", bit, re.I).group(1).lower()
            kids.append(_child(c, bit.strip(), f"{row} {w}"))
        return kids
    parts = [x.strip() for x in re.split(r"\s*[·•∙⋅]\s*", lit) if x.strip()]
    def _part_value(val: str) -> str | None:
        if re.search(r"\b\d+[dD]\b", val) and not re.search(r"\$|%|[x×]|e[+\-]|/d|/wk|/8h", val):
            return None
        if re.search(r"percentile|pctile|\d(?:st|nd|rd|th)\b", val, re.I):
            pm = re.search(r"~?\d+(?:\.\d+)?(?:st|nd|rd|th)?", val, re.I)
            if pm:
                return pm.group(0)
        m = re.search(
            r"([~\-−+$]?\d[\d,]*(?:\.\d+)?(?:e[+\-]?\d+)?(?:[KMB])?(?:T(?![a-z]))?(?:%|/d|/wk|/yr|/8h)?(?:[x×])?)",
            val,
        )
        if not m:
            return None
        num = m.group(1)
        if re.fullmatch(r"~?\d+[dD]?", num) and not re.search(r"\$|%|[x×]|[KMBT]|e[+\-]|/d|/8h", num, re.I):
            return None
        if not re.search(r"\$|%|[x×]|[KMBTe]|/d|/wk|/yr|/8h", num, re.I) and not re.search(r"\$|%|[x×]|e[+\-]|/d|/wk|/8h|[KMBT]\b", val, re.I):
            return None
        return num

    if len(parts) >= 2 and all(has_number(v) for v in parts) and len(lit) < 160 and row_l not in META_KEYS:
        extracted = [(p, _part_value(p)) for p in parts]
        if all(num for _, num in extracted):
            for i, (val, num) in enumerate(extracted):
                lab = re.split(r"\s*[$~+\-−\d]", val, maxsplit=1)[0].strip(" ·:-") or f"{row} p{i+1}"
                kids.append(_child(c, num, lab))
            return kids

    # labeled evidence spans
    if row_l in {"evidence", ""} or c.get("kind") in {"fx_ev_v", "ev_tip_read"}:
        for rx, rest, lab in (
            (r"(?:^|[^A-Za-z0-9])50d\s*[~≈]?\s*(\$?\d[\d,.]*)", "ma.usd.50d", "50d"),
            (r"(?:^|[^A-Za-z0-9])200d\s*[~≈]?\s*(\$?\d[\d,.]*)", "ma.usd.200d", "200d"),
            (r"(?:^|[^A-Za-z0-9])20d\s*[~≈]?\s*(\$?\d[\d,.]*)", "ma.usd.20d", "20d"),
            (r"OI\s*[~≈]?\s*(~?\d[\d.]+k\s*BTC)", "oi.btc.current", "OI BTC"),
            (r"fut/spot\s*[~≈]?\s*(~?\d[\d.]+×)", "leverage.x.current", "fut/spot"),
            (r"TVL\s*[~≈]?\s*(\$[\d.]+[MBT])", "tvl.usd.current", "TVL"),
            (r"stablecoins?\s*[~≈]?\s*(\$[\d.]+[MBT])", "stablecoin.usd.current", "Stablecoins"),
            (r"frames?\s*[~≈]?\s*(~?[\d.]+M)", "usage.frames.cumulative", "Frames"),
            (r"perps?\s*30d\s*(?:fees)?\s*[~≈]?\s*(\$[\d.]+[MB])", "fees.usd.30d", "Fees 30d"),
            (r"Staked\s+(\d+(?:\.\d+)?%)", "stake.ratio.pct", "Staked"),
            (r"inflation\s+(\d+(?:\.\d+)?%)", "inflation.pct.current", "inflation"),
            (r"TPS[^\d~]*~?(\d+(?:\.\d+)?)\s*all", "tps.all.current", "TPS all"),
            (r"~?(\d+(?:\.\d+)?)\s*non-vote", "tps.nonvote.current", "TPS nv"),
            (r"fees?\s*30d\s*mean\s+(\$[\d,]+(?:\.\d+)?(?:[kKmM])?/d)", "fees.usd_per_day.mean_30d", "fees 30d mean"),
        ):
            m = re.search(rx, lit, re.I)
            if m:
                kids.append(_child(c, m.group(1), lab, rest))
    return kids


def classify(c: dict) -> dict:
    lit = c["literal"]
    slug = c["asset_slug"]
    label = (c.get("label") or "").strip()
    tip = (c.get("tip_name") or "").strip()
    row = label.lower().strip()
    tip_l = tip.lower().strip()
    hint = (c.get("window_hint") or "").strip()
    hint_l = hint.lower()
    parent_lab = (c.get("parent_label") or "").lower()
    cs = set((c.get("element_class") or "").split())
    kind = c.get("kind") or ""
    blob = f"{row} {tip_l} {hint_l} {parent_lab}"
    win = infer_window(row, tip_l, hint_l, lit, parent_lab)

    def non(state, rule, owner="CGPT_CURSOR"):
        c["coverage_state"] = state
        c["classification_rule"] = rule
        c["metric_id"] = None
        c["owner"] = owner
        return c

    def ok(rest, rule, mtype="CURRENT_DYNAMIC", owner="CGPT_CURSOR", cov="MAPPED_CANONICAL"):
        if rest.split(".")[0] in BANNED_FAMILIES:
            return None
        ensure(rest, lit)
        if not type_accepts(rest, lit):
            return None
        if is_historical_window(rest.split(".")[-1]) or mtype == "HISTORICAL":
            mtype = "HISTORICAL"
            cov = "HISTORICAL"
        c["metric_id"] = slug_id(c.get("asset_slug") or slug, rest)
        c["classification_rule"] = rule
        c["coverage_state"] = cov
        c["metric_type"] = mtype
        c["owner"] = owner
        c["value_kind"] = TYPE_SPEC[rest][0]
        c["time_window"] = rest.split(".")[-1]
        c["update_mode"] = update_mode_for(c, rest, mtype)
        return c

    if slug in DORMANT_SLUGS:
        owner = "GROK" if kind == "siren_json" else "CGPT_CURSOR"
        return non("LEGACY_INACTIVE", "dormant_asset_excluded", owner)

    if c.get("is_compound_parent"):
        return non("EVIDENCE_REFERENCE" if row in META_KEYS or row == "evidence" else "COMPOSITE_DISPLAY", "compound_parent")

    if c.get("forced_rest"):
        mtype = "HISTORICAL" if is_historical_window(c["forced_rest"].split(".")[-1]) else "CURRENT_DYNAMIC"
        return ok(c["forced_rest"], "atomic_span_forced", mtype) or non("CONTEXT_ONLY", "forced_type_reject")

    if kind in {"ev_tip_read"} and len(lit) > 70:
        return non("EVIDENCE_REFERENCE", "long_prose_container")

    if kind == "siren_json":
        lab = c.get("label") or ""
        if slug in DORMANT_SLUGS:
            return non("LEGACY_INACTIVE", "dormant_siren", "GROK")
        if lab == "cover_fmt":
            c["coverage_state"] = "COMPOSITE_DISPLAY"
            c["classification_rule"] = "siren_cover_composite"
            c["metric_id"] = None
            c["owner"] = "GROK"
            c["metric_type"] = "WALLET_OWNED"
            c["update_mode"] = "WALLET_SNAPSHOT"
            c["linked_metric_ids"] = [
                slug_id(slug, "siren.supply.tokens.current"),
                slug_id(slug, "siren.tracked.tokens.current"),
            ]
            return c
        rest = {
            "watched_wallet_count": "siren.watched_wallet_count.current",
            "tracked_fmt": "siren.tracked.tokens.current",
            "supply_fmt": "siren.supply.tokens.current",
            "aug1_unknown_wallet_count": "siren.aug1_unknown_wallet_count.current",
        }.get(lab)
        if rest:
            return ok(rest, "siren_json_atomic", "WALLET_OWNED", "GROK", "WALLET_OWNED") or non("CONTEXT_ONLY", "siren_type_reject", "GROK")
        return non("CONTEXT_ONLY", "siren_other", "GROK")

    if "hold-px" in cs or kind == "attr:data-live-px" or "desk-px" in cs:
        return ok("price.usd.live", "live_px") or non("CONTEXT_ONLY", "type_reject_live_px")
    if "alt-price" in cs:
        return ok("price.usd.report", "report_px") or non("CONTEXT_ONLY", "type_reject_report_px")
    if "hold-out" in cs or "desk-out" in cs:
        return ok("threshold.out.usd", "hold_out", "STATIC_DECISION_THRESHOLD", cov="STATIC_REFERENCE") or non("STATIC_REFERENCE", "hold_out_untyped")
    if "hold-shelf" in cs:
        return ok("threshold.this_move.usd", "hold_shelf", "STATIC_DECISION_THRESHOLD", cov="STATIC_REFERENCE") or non("STATIC_REFERENCE", "hold_shelf_untyped")

    if row in {"definition", "coinbase estimate", "label", "comparator label"}:
        return non("QUALITATIVE_NON_METRIC", "definition_text")
    if row in META_KEYS:
        return non("EVIDENCE_REFERENCE" if row == "evidence" else "QUALITATIVE_NON_METRIC", f"meta_key_{row}")
    if "last price" in lit.lower() and "volume" in lit.lower():
        return non("QUALITATIVE_NON_METRIC", "formula_prose")

    dk = detect_kind(lit)
    if dk == "DATE":
        return non("CONTEXT_ONLY", "as_of_date_stamp")
    if dk == "STATUS_TEXT":
        return non("QUALITATIVE_NON_METRIC", "status_label")
    if dk == "PROSE" and not has_number(lit):
        return non("EVIDENCE_REFERENCE", "formula_or_prose")
    if re.fullmatch(r"(?:~?\d+\s*)?(?:[127]d|30d|90d|180d|24h)|/ ?day|/d|/ ?7d|/ ?30d", lit.strip(), re.I):
        return non("CONTEXT_ONLY", "window_label_not_value")
    if len(lit) >= 40:
        return non("EVIDENCE_REFERENCE", "long_prose_container")
    if "mint verified" in lit.lower():
        return non("EVIDENCE_REFERENCE", "long_prose_container")
    if re.match(r"^(not |unknown|n/?a|none packed)", lit.strip(), re.I):
        return non("QUALITATIVE_NON_METRIC", "negation_status")
    if re.fullmatch(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}", lit.strip(), re.I):
        return non("CONTEXT_ONLY", "month_year_stamp")
    if re.match(r"^(above|below|intact|holding|leading|lagging)\b", lit.strip(), re.I) and "$" not in lit:
        return non("QUALITATIVE_NON_METRIC", "relation_status")

    # ETF
    if kind.startswith("etf"):
        w = (c.get("etf_window") or win or "").replace("-", "_")
        if w == "24h":
            w = "1d"
        if w in {"1d", "7d", "30d", "all_time"}:
            rest = f"etf.flow.usd.{w}"
            mtype = "HISTORICAL" if w == "all_time" else "CURRENT_DYNAMIC"
            cov = "HISTORICAL" if w == "all_time" else "MAPPED_CANONICAL"
            return ok(rest, "etf_window_slot", mtype, cov=cov) or non("CONTEXT_ONLY", "etf_type_reject")
        return non("FALSE_POSITIVE", "etf_non_window")

    # Fear / participation
    if row == "index" and ("fear" in tip_l or "greed" in tip_l):
        c["asset_slug"] = "global"
        return ok("fear_greed.index.current", "row_fear_greed_index") or non("CONTEXT_ONLY", "fg_not_index")
    if "prior" in row:
        return non("CONTEXT_ONLY", "index_delta_not_level")
    if row == "as of":
        return non("CONTEXT_ONLY", "as_of_row")
    if row == "beat bitcoin":
        c["asset_slug"] = "global"
        return ok("participation.beat_btc.count", "row_participation_beat_btc") or non("CONTEXT_ONLY", "part_not_count")
    if "50-day" in row or "50 day" in row:
        c["asset_slug"] = "global"
        return ok("participation.above_50dma.count", "row_participation_50dma") or non("CONTEXT_ONLY", "part_not_count")

    if kind == "econ_bar_title":
        if "buyback" in blob:
            if c.get("bar_last") and dk in {"USD_AMOUNT", "PRICE_USD"}:
                return ok("buyback.usd.1d", "econ_bar_last_daily") or non("CONTEXT_ONLY", "econ_bar_last_not_usd")
        return non("CONTEXT_ONLY", "econ_bar_series_point")

    # ---- specific families (window-aware; no generic 7d default) ----
    if row in {"ath", "all-time high", "all time high"}:
        return ok("price.ath.usd", "row_ath", "HISTORICAL", cov="HISTORICAL") or non("CONTEXT_ONLY", "ath_not_price")
    if row in {"retracement", "drawdown", "from ath"} and "%" in lit:
        return ok("price.drawdown_from_ath.pct", "row_drawdown", "DERIVED_DYNAMIC") or non("CONTEXT_ONLY", "drawdown_not_pct")
    if row in {"7d", "30d", "90d", "180d"} and dk == "PERCENT" and "rs" not in tip_l and "pp" not in lit.lower():
        return ok(f"return.pct.{row}", f"row_return_{row}") or non("CONTEXT_ONLY", "return_type_reject")

    if "nu6" in row or "issuance / funding" in row or row.startswith("issuance /"):
        return non("QUALITATIVE_NON_METRIC", "nu6_split")
    if "funding" in row or (row in {"latest", "latest 8h print", "latest print"} and "fund" in tip_l):
        if "pctile" in row or "percentile" in row or re.search(r"\d+(st|nd|rd|th)\b", lit, re.I):
            return ok("funding.percentile.current", "funding_pctile") or non("CONTEXT_ONLY", "funding_pctile_reject")
        if "7d mean" in row or row == "7d mean" or win == "mean_7d":
            return ok("funding.rate.mean_7d", "funding_7d_mean") or non("CONTEXT_ONLY", "funding_mean_reject")
        if "latest" in row or win == "latest" or "print" in row:
            return ok("funding.rate.latest", "funding_latest") or non("CONTEXT_ONLY", "funding_latest_reject")
        return ok("funding.rate.latest", "funding_default_latest") or non("CONTEXT_ONLY", "funding_not_rate")

    if row in {"50d", "sma50", "50-day"} or row.startswith("50d"):
        return ok("ma.usd.50d", "row_ma_50d") or non("CONTEXT_ONLY", "ma50_reject")
    if row in {"200d", "sma200"} or row.startswith("200d"):
        return ok("ma.usd.200d", "row_ma_200d") or non("CONTEXT_ONLY", "ma200_reject")
    if row in {"20d", "sma20"}:
        return ok("ma.usd.20d", "row_ma_20d") or non("CONTEXT_ONLY", "ma20_reject")

    if row in {"ratio"} and "×" not in lit and "x" not in lit.lower() and re.search(r"\d", lit):
        return ok("bme.ratio.last4", "row_ratio_number") or non("CONTEXT_ONLY", "ratio_num")
    if row in {"ratio", "fut / spot", "fut/spot", "fut/spot now", "futures vs spot", "futures / spot", "perp/spot", "perp vs binance spot", "binance perp/spot"}:
        if "7.0" in lit or "coinbase" in blob:
            hit = ok("leverage.perp_spot_notional.x", "row_fart_perp_spot")
            if hit:
                return hit
        return ok("leverage.x.current", "row_ratio") or non("CONTEXT_ONLY", "ratio_not_x")

    if row in {"oi", "open interest", "level", "oi notional", "binance oi", "binance hype oi", "native hype oi", "hype-token oi", "platform oi"}:
        if "btc" in lit.lower():
            return ok("oi.btc.current", "row_oi_btc") or non("CONTEXT_ONLY", "oi_btc_reject")
        return ok("oi.usd.current", "row_oi_usd") or non("CONTEXT_ONLY", "oi_not_usd")
    if "oi" in row and dk == "PERCENT":
        w = win if win in {"1d", "7d", "30d"} else "30d"
        return ok(f"oi.change.pct.{w}", "oi_change") or non("CONTEXT_ONLY", "oi_change_reject")
    if row in {"oi trend", "oi δ"}:
        return non("COMPOSITE_DISPLAY", "oi_delta_compound") if "/" in lit else (
            ok("oi.change.pct.30d", "oi_trend_30d") or non("CONTEXT_ONLY", "oi_trend")
        )

    if row in {"spot 24h", "perp 24h", "cg 24h vol", "hype-token day vol", "binance perp 24h", "l1 perp day"}:
        return ok("volume.usd.24h", "row_volume_24h") or non("CONTEXT_ONLY", "vol_reject")

    # Fees — window required; section tip counts, parent prose tooltip does not
    if "fee" in row or tip_l in {"fees", "fee"} or (tip_l.startswith("fee") and len(tip_l) < 24):
        if dk == "PERCENT" or "δ" in row or "delta" in row:
            return ok("fees.change.pct.30d", "fees_delta") or non("CONTEXT_ONLY", "fees_delta_reject")
        if win == "nov_2024":
            return ok("fees.usd_per_day.nov_2024", "fees_nov_2024", "HISTORICAL") or non("CONTEXT_ONLY", "fees_hist")
        if win == "june_2026":
            return ok("fees.usd_per_day.june_2026", "fees_june_2026", "HISTORICAL") or non("CONTEXT_ONLY", "fees_hist")
        if win == "jan_2025_ath" or ("jan 2025" in blob and "/d" in lit.lower()):
            return ok("fees.usd_per_day.jan_2025_ath", "fees_jan_2025", "HISTORICAL") or non("CONTEXT_ONLY", "fees_hist")
        if win in {"ath_sep", "jan_high", "june_atl"}:
            return ok(f"fees.usd_per_day.{win}", "fees_named_hist", "HISTORICAL") or non("CONTEXT_ONLY", "fees_hist")
        if "/d" in lit.lower() or win in {"mean_30d", "mean_7d", "per_day"}:
            if win in {"mean_30d", "per_day"} and ("30d" in blob or win == "mean_30d"):
                return ok("fees.usd_per_day.mean_30d", "fees_mean_30d") or non("CONTEXT_ONLY", "fees_mean_reject")
            if win == "mean_7d" or "±7d" in blob:
                return ok("fees.usd_per_day.mean_7d", "fees_mean_7d") or non("CONTEXT_ONLY", "fees_mean7_reject")
            return ok("fees.usd_per_day.current", "fees_per_day_now") or non("CONTEXT_ONLY", "fees_day_now")
        if win in {"mean_30d", "per_day"} and ("/d" in lit.lower() or "mean" in blob or "/ day" in hint_l):
            return ok("fees.usd_per_day.mean_30d", "fees_mean_30d") or non("CONTEXT_ONLY", "fees_mean_reject")
        if win == "mean_7d" or "±7d" in blob:
            return ok("fees.usd_per_day.mean_7d", "fees_mean_7d") or non("CONTEXT_ONLY", "fees_mean7_reject")
        if hint_l == "30d" or win == "30d" or "30d" in row:
            return ok("fees.usd.30d", "fees_30d") or non("CONTEXT_ONLY", "fees_30d_reject")
        if win == "7d" or hint_l == "7d":
            return ok("fees.usd.7d", "fees_7d") or non("CONTEXT_ONLY", "fees_7d_reject")
        if win == "1d" or "24h" in row:
            return ok("fees.usd.1d", "fees_1d") or non("CONTEXT_ONLY", "fees_1d_reject")
        if "$" in lit and hint_l == "30d":
            return ok("fees.usd.30d", "fees_hint_30d") or non("CONTEXT_ONLY", "fees_hint_reject")
        return non("CONTEXT_ONLY", "fees_window_unknown")

    # Earnings / revenue — row label first; month cells; never inherit a long parent tooltip
    if re.fullmatch(r"(july|jul)", row) and "$" in lit:
        return ok("revenue.usd.july_2026", "month_usd_july", "HISTORICAL") or non("CONTEXT_ONLY", "july_earn_reject")
    if re.fullmatch(r"(may)", row) and "$" in lit:
        return ok("revenue.usd.may_2026", "month_usd_may", "HISTORICAL") or non("CONTEXT_ONLY", "may_earn_reject")
    if re.fullmatch(r"(june|jun)", row) and "$" in lit:
        return ok("revenue.usd.june_2026", "month_usd_june", "HISTORICAL") or non("CONTEXT_ONLY", "june_earn_reject")
    if re.fullmatch(r"(cum|cumulative)", row) and "$" in lit and "etf" not in tip_l:
        return ok("revenue.usd.cumulative", "row_cum_usd") or non("CONTEXT_ONLY", "cum_usd_reject")

    if "earning" in row or tip_l in {"earnings", "earn"}:
        if "july" in row:
            return ok("revenue.usd.july_2026", "july_earnings", "HISTORICAL") or non("CONTEXT_ONLY", "july_earn_reject")
        if re.search(r"\bmay\b", row):
            return ok("revenue.usd.may_2026", "may_earnings", "HISTORICAL") or non("CONTEXT_ONLY", "may_earn_reject")
        if "june" in row:
            return ok("revenue.usd.june_2026", "june_earnings", "HISTORICAL") or non("CONTEXT_ONLY", "june_earn_reject")
        if "cumulative" in row or (row in {"earnings", ""} and "/d" not in lit.lower() and win == "current"):
            if "/d" in lit.lower() or "avg" in row:
                return ok("revenue.usd_per_day.mean_30d", "earn_avg_day") or non("CONTEXT_ONLY", "earn_avg_reject")
            return ok("revenue.usd.cumulative", "earn_cumulative") or non("CONTEXT_ONLY", "earn_cum_reject")
        if "avg" in row or "/d" in lit.lower() or win == "mean_30d":
            return ok("revenue.usd_per_day.mean_30d", "earn_30d_avg") or non("CONTEXT_ONLY", "earn_avg_reject")
        return ok("revenue.usd.cumulative", "earn_generic_cumulative") or non("CONTEXT_ONLY", "earn_generic_reject")

    if "revenue" in row or re.search(r"\brev\b", row) or (row == "weekly" and "revenue" in tip_l):
        if "/wk" in lit.lower() or win == "7d":
            return ok("revenue.usd.7d", "revenue_7d") or non("CONTEXT_ONLY", "rev_7d_reject")
        if win == "30d":
            return ok("revenue.usd.30d", "revenue_30d") or non("CONTEXT_ONLY", "rev_30d_reject")
        if win in {"ath_sep", "jan_high", "june_atl"} and ("/d" in lit.lower() or "$" in lit):
            return ok(f"revenue.usd_per_day.{win}", "rev_named_hist", "HISTORICAL") or non("CONTEXT_ONLY", "rev_hist")
        if "/d" in lit.lower():
            if "30d" in blob or win == "mean_30d":
                return ok("revenue.usd_per_day.mean_30d", "revenue_per_day") or non("CONTEXT_ONLY", "rev_day_reject")
            return ok("revenue.usd_per_day.current", "revenue_per_day_now") or non("CONTEXT_ONLY", "rev_day_now")
        return non("CONTEXT_ONLY", "revenue_window_unknown")

    if "buyback" in row or (row == "weekly" and "buyback" in tip_l):
        if "hype" in lit.lower() and "$" not in lit:
            return ok("af.inventory.tokens.current", "af_in_buyback_row") or non("CONTEXT_ONLY", "af_from_bb")
        if dk == "PERCENT":
            return ok("buyback.change.pct.7d", "row_buyback_change") or non("CONTEXT_ONLY", "buyback_pct_reject")
        if "/d" in lit.lower():
            if win in {"ath_sep", "jan_high", "june_atl"}:
                return ok(f"buyback.usd_per_day.{win}", "buyback_named_hist", "HISTORICAL") or non("CONTEXT_ONLY", "buyback_hist")
            return ok("buyback.usd.1d", "row_buyback_daily") or non("CONTEXT_ONLY", "buyback_d_reject")
        return ok("buyback.usd.7d", "row_buyback_weekly") or non("CONTEXT_ONLY", "buyback_type_reject")

    if row in {"tvl"} or row.startswith("tvl"):
        if "jan 2025" in blob:
            return ok("tvl.usd.jan_2025", "tvl_jan_2025", "HISTORICAL") or non("CONTEXT_ONLY", "tvl_hist")
        return ok("tvl.usd.current", "row_tvl") or non("CONTEXT_ONLY", "tvl_reject")
    if "stablecoin" in row or row == "stables 30d":
        if "%" in lit:
            ensure("stablecoin.change.pct.30d", lit, "30-day percent change in stablecoin stock around {ASSET}.")
            return ok("stablecoin.change.pct.30d", "stables_30d_pct") or non("CONTEXT_ONLY", "stables_pct")
        return ok("stablecoin.usd.current", "row_stables") or non("CONTEXT_ONLY", "stables_reject")

    if "stake ratio" in row or row == "stake ratio":
        return ok("stake.ratio.pct", "row_stake_ratio") or non("CONTEXT_ONLY", "stake_ratio_reject")
    if row == "staked":
        if "%" in lit:
            return ok("stake.ratio.pct", "row_staked_pct") or non("CONTEXT_ONLY", "staked_pct")
        return ok("stake.tokens.current", "row_staked_tokens") or non("CONTEXT_ONLY", "staked_tok")
    if "inflation" in row or row == "issuanceper year":
        if "%" in lit:
            return ok("inflation.pct.current", "row_inflation") or non("CONTEXT_ONLY", "inflation_reject")
    if "tps" in row:
        if "all" in lit.lower() and "non" in lit.lower():
            return non("COMPOSITE_DISPLAY", "tps_all_and_nv")
        if "nv" in lit.lower() or "non-vote" in lit.lower() or "nonvote" in lit.lower():
            return ok("tps.nonvote.current", "row_tps_nv") or non("CONTEXT_ONLY", "tps_nv")
        return ok("tps.all.current", "row_tps_all") or non("CONTEXT_ONLY", "tps_all")

    if "liquidity" in row or row == "best pool" or "top raydium" in row:
        return ok("liquidity.dex.usd.current", "row_dex_liq") or non("CONTEXT_ONLY", "liq_reject")
    if row in {"market share", "share", "live 24h", "launchpad share"} or "market share" in row:
        if "%" in lit:
            return ok("market_share.pct.current", "row_mkt_share") or non("CONTEXT_ONLY", "share_reject")
    if row in {"mcap", "market cap"}:
        return ok("market_cap.usd.current", "row_mcap") or non("CONTEXT_ONLY", "mcap_reject")

    if row == "frames" or "frames rendered" in row:
        return ok("usage.frames.cumulative", "row_frames") or non("CONTEXT_ONLY", "frames_reject")
    if row == "ratio" and re.fullmatch(r"~?\d+(?:\.\d+)?", lit.strip()):
        return ok("bme.ratio.last4", "row_ratio_number") or non("CONTEXT_ONLY", "ratio_num")
        return ok("bme.ratio.last4", "row_bme4") or non("CONTEXT_ONLY", "bme4")
    if "last-8 ratio" in row:
        return ok("bme.ratio.last8", "row_bme8") or non("CONTEXT_ONLY", "bme8")

    if "af stock" in row or row in {"inventory", "af inventory"} or row == "inventory":
        if "%" in lit:
            ensure("af.inventory.share_hl_circ.pct", lit, "Assistance Fund inventory as a percent of Hyperliquid circulating supply.")
            return ok("af.inventory.share_hl_circ.pct", "row_af_share") or non("CONTEXT_ONLY", "af_share")
        if "hype" in (slug, tip_l) or slug == "hype":
            return ok("af.inventory.tokens.current", "row_af_stock") or non("CONTEXT_ONLY", "af_stock")
    if "af buys" in row:
        return ok("af.buys.usd.30d", "row_af_buys") or non("CONTEXT_ONLY", "af_buys")
    if "emission" in row or row == "futureemissions" or "emissionsleft" in row.replace(" ", ""):
        return ok("emissions.tokens.remaining", "row_emissions") or non("CONTEXT_ONLY", "emissions")

    if "circulat" in row and "%" in lit:
        return ok("supply.circulating.pct", "row_circ_pct") or non("CONTEXT_ONLY", "circ_pct")
    if "circ / max" in row or row.startswith("circulating ") and "/" in lit:
        return non("COMPOSITE_DISPLAY", "circ_max_pair")
    if row in {"cg circ", "solana circ"} or (row == "cg" and dk == "TOKEN_AMOUNT"):
        return ok("supply.circulating.tokens", "row_circ_tokens") or non("CONTEXT_ONLY", "circ_tok")
    if row in {"max", "max supply"} and "drawdown" not in lit.lower() and "$" not in lit:
        return ok("supply.max.tokens", "row_max_tokens") or non("CONTEXT_ONLY", "max_tok")
    if "top-20" in row or "top 20" in row or "top20" in row:
        return ok("holders.top20.pct", "row_top20") or non("CONTEXT_ONLY", "top20_reject")

    if row in {"running / queued"}:
        return non("COMPOSITE_DISPLAY", "jobs_run_queue")
    if row in {"clusters", "running clusters"}:
        ensure("clusters.running.count", lit, "Count of running compute clusters on the {ASSET} network.")
        return ok("clusters.running.count", "row_clusters") or non("CONTEXT_ONLY", "clusters")
    if row in {"hours"}:
        ensure("compute.hours.cumulative", lit, "Cumulative compute hours on the {ASSET} network.")
        return ok("compute.hours.cumulative", "row_hours") or non("CONTEXT_ONLY", "hours")
    if row in {"l1 perp day"}:
        return ok("volume.usd.24h", "row_l1_perp_day") or non("CONTEXT_ONLY", "vol_reject")
    if "no material mm" in row or "wintermute/dwf" in lit.lower():
        return non("QUALITATIVE_NON_METRIC", "mm_scan_note")
    if "running" in row and "job" in blob:
        return ok("jobs.running.count", "row_jobs_running") or non("CONTEXT_ONLY", "jobs_run")
    if "completed" in row or "cumulative jobs" in row:
        return ok("jobs.completed.cumulative", "row_jobs_cum") or non("CONTEXT_ONLY", "jobs_cum")
    if "gpu" in row:
        return ok("gpu_hours.approx_31d", "row_gpu_h") or non("CONTEXT_ONLY", "gpu")
    if "~30d jobs" in row:
        ensure("jobs.approx_30d.count", lit, "Jobs completed on {ASSET} over about 30 days.")
        return ok("jobs.approx_30d.count", "row_jobs_30d") or non("CONTEXT_ONLY", "jobs30")

    if "dex vs eth" in row or "dex latest" in row or "dex share" in row:
        return ok("dex_eth_ratio.x.current", "row_dex_eth") or non("CONTEXT_ONLY", "dex_eth")

    # RS windows
    if "vs btc 7d" in row:
        return ok("rs.vs_btc.pct.7d", "rs_btc_7d") or non("CONTEXT_ONLY", "rs")
    if "vs btc 30d" in row or row.endswith("/ 30d") and "btc" in row:
        pass
    if row in {"vs btc 7d / 30d", "7d / 30d"}:
        return non("COMPOSITE_DISPLAY", "rs_pair")
    if "nos/sol 7d" in row or "io/sol 7d" in row:
        return ok("rs.vs_sol.pp.7d", "rs_sol_7d_pp") or non("CONTEXT_ONLY", "rs")
    if "nos/sol 30d" in row or "io/sol 30d" in row or "30d rs" in row or "sol / btc rs" in row:
        if "pp" in lit.lower():
            rest = "rs.vs_btc.pp.30d" if "btc" in row else "rs.vs_sol.pp.30d"
            return ok(rest, "rs_pp_30d") or non("CONTEXT_ONLY", "rs")
    if re.search(r"7d .*(btc|sol)|vs btc|vs sol", row) and "pp" in lit.lower():
        rest = "rs.vs_btc.pp.7d" if "btc" in row else "rs.vs_sol.pp.7d"
        if "30d" in row:
            rest = rest.replace(".7d", ".30d")
        return ok(rest, "rs_pp") or non("CONTEXT_ONLY", "rs")
    if row in {"pump / btc", "pump / sol"} and "%" in lit:
        rest = "rs.vs_btc.pct.30d" if "btc" in row else "rs.vs_sol.pct.30d"
        return ok(rest, "pump_rs_head") or non("CONTEXT_ONLY", "rs")

    if row in {"now"} and "$" in lit and "/d" not in lit.lower():
        return ok("price.usd.report", "row_now_price") or non("CONTEXT_ONLY", "now_price")
    if "price" in row and "$" in lit and "/d" not in lit.lower() and "fee" not in blob:
        return ok("price.usd.report", "row_price") or non("CONTEXT_ONLY", "price_type_reject")

    if slug == "portfolio" or "portfolio" in tip_l:
        c["asset_slug"] = "portfolio"
        return ok("portfolio.value.usd.current", "portfolio_value", "WALLET_OWNED", "GROK", "WALLET_OWNED") or non("CONTEXT_ONLY", "portfolio_reject")

    if "fear" in tip_l or "greed" in tip_l:
        c["asset_slug"] = "global"
        if dk in {"INDEX", "COUNT"} and re.fullmatch(r"~?\d{1,3}", lit.strip()):
            return ok("fear_greed.index.current", "head_fear_greed") or non("QUALITATIVE_NON_METRIC", "fg_headline_not_index")
        return non("QUALITATIVE_NON_METRIC", "fg_headline_not_index")

    # generic keyword fallback that still encodes window
    rest = _keyword_rest(row, tip_l, hint_l, lit, win, dk)
    if rest:
        mtype = "HISTORICAL" if is_historical_window(rest.split(".")[-1]) else "CURRENT_DYNAMIC"
        hit = ok(rest, "keyword_family", mtype)
        if hit:
            return hit

    if re.fullmatch(r"(?:~?\d+\s*)?(?:[127]d|30d|90d|180d|24h)|/ ?day|/d|30D|7D", lit.strip(), re.I):
        return non("CONTEXT_ONLY", "window_label_not_value")
    if re.fullmatch(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}", lit.strip(), re.I):
        return non("CONTEXT_ONLY", "month_year_stamp")
    if re.match(r"^(above|below|intact|holding|leading|lagging)\b", lit.strip(), re.I) and not re.search(r"\$", lit):
        return non("QUALITATIVE_NON_METRIC", "relation_status")

    if has_number(lit) and kind in {
        "ev_v", "fx_ev_v", "ev_tip_read", "metric_val", "econ_dial", "econ_kpi",
        "metric_card_value", "atomic_span", "slot", "econ_sub",
    }:
        if dk == "STATUS_TEXT":
            return non("QUALITATIVE_NON_METRIC", "status_with_digits")
        key = re.sub(r"[^a-z0-9]+", "_", (row or tip_l or "slot").lower()).strip("_")[:40] or "slot"
        if key.split("_")[0] in BANNED_FAMILIES:
            key = "named_" + key
        alias = {
            "jul": "revenue.usd.july_2026", "july": "revenue.usd.july_2026",
            "may": "revenue.usd.may_2026", "jun": "revenue.usd.june_2026", "june": "revenue.usd.june_2026",
            "cum": "revenue.usd.cumulative", "cumulative": "revenue.usd.cumulative",
            "now": "fees.usd_per_day.mean_7d" if "/d" in lit.lower() else "price.usd.report",
            "now_7d": "fees.usd_per_day.mean_7d", "now_7d_mean": "fees.usd_per_day.mean_7d",
            "last_4_ratio": "bme.ratio.last4", "recent_bme": "bme.ratio.last4",
        }.get(key)
        if alias:
            mtype = "HISTORICAL" if is_historical_window(alias.split(".")[-1]) else "CURRENT_DYNAMIC"
            hit = ok(alias, "label_inventory_alias", mtype)
            if hit:
                return hit
        unit_part = {
            "USD_AMOUNT": "usd", "USD_PER_DAY": "usd_per_day", "USD_7D_TOTAL": "usd",
            "PRICE_USD": "usd", "PERCENT": "pct", "PERCENTAGE_POINTS": "pp",
            "RATIO_X": "x", "TOKEN_AMOUNT": "tokens", "COUNT": "count",
            "INDEX": "index", "FUNDING_RATE": "rate", "MA_LEVEL": "ma",
        }.get(dk, "value")
        rest = f"{key}.{unit_part}.{win}"
        mtype = "HISTORICAL" if is_historical_window(win) else "CURRENT_DYNAMIC"
        hit = ok(rest, "label_inventory", mtype)
        if hit:
            return hit
        return non("UNCLASSIFIED", "dynamic_numeric_unmapped")

    return non("CONTEXT_ONLY", "unstructured_or_non_metric")


def _keyword_rest(row: str, tip: str, hint: str, lit: str, win: str, dk: str) -> str | None:
    b = f"{row} {tip} {hint}"
    if "issuance" in row and "sol/yr" in lit.lower():
        return "issuance.tokens.per_year"
    if row in {"burn", "est. burn"} and "sol/yr" in lit.lower():
        return "burn.tokens.per_year"
    if "net change" in row or "net supply" in row:
        return "supply.net_change.tokens.per_year"
    if "july low" in row:
        return "price.usd.july_2026_low"
    if row in {"aug 10"} and "$" in lit:
        return "etf.flow.usd.2026_08_10"
    if row in {"aug 11"} and "$" in lit:
        return "etf.flow.usd.2026_08_11"
    if "aug 3" in row and "$" in lit:
        return "etf.flow.usd.2026_08_03_07"
    if row.startswith("cumulative") and "$" in lit and "etf" in f"{row} {tip}":
        return "etf.flow.usd.all_time"
    if "last-4 burned" in row:
        return "bme.burned.tokens.last4"
    if "last-4 emission" in row:
        return "bme.emissions.tokens.last4"
    if "last-8 burn" in row:
        return "bme.burned.tokens.last8"
    if "last-8 emit" in row:
        return "bme.emissions.tokens.last8"
    if row in {"node due / epoch"}:
        return "bme.node_due.tokens.per_epoch"
    if "shielded" in row and "%" in lit:
        return "shielded.share.pct"
    if "shielded" in row:
        return "shielded.tokens.current"
    if row in {"tx/24h"}:
        return "tx.count.24h"
    if "validator" in row:
        return "validators.active.count"
    if row in {"apy sample"}:
        return "staking.apy.pct"
    if "wintermute" in row and dk in {"TOKEN_AMOUNT", "COUNT"}:
        return "mm.wintermute.tokens"
    if row in {"nodes value"}:
        return "nodes.count.listed"
    if "host usdreward" in row:
        return "host_rewards.usd.cumulative"
    if row in {"l1 perp day"}:
        return "volume.usd.24h"
    if row in {"platform oi"}:
        return "oi.usd.current"
    if row in {"clusters", "running clusters"}:
        return "clusters.running.count"
    if row in {"hours"}:
        return "compute.hours.cumulative"
    if row in {"inventory total"}:
        return "devices.inventory.count"
    if row in {"contributor ncu", "hyperlabs ncu"}:
        return "ncu.hyperlabs.tokens"
    if "total stake" in row:
        return "stake.tokens.current"
    if "totalSupply" in row or row == "totalsupply":
        return "supply.max.tokens"
    if row in {"cg"} and "%" in lit:
        return "supply.circulating.pct"
    if row in {"hl"} and "%" in lit:
        return "supply.hl_circulating.pct"
    if "share history" in row or row in {"ath sep", "jan high", "june atl", "aug 10"} and "%" in lit:
        return f"market_share.pct.{re.sub(r'[^a-z0-9]+', '_', row)[:24]}"
    if "perps 24h" in row and "$" in lit:
        return "volume.usd.24h"
    if "perps 30d" in row and "$" in lit:
        return "fees.usd.30d"
    if win in {"7d", "30d", "90d", "180d"} and dk == "PERCENT" and "rs" not in b:
        return f"return.pct.{win}"
    return None


def is_dynamic_numeric(c: dict) -> bool:
    if (c.get("asset_slug") or "") in DORMANT_SLUGS:
        return False
    if c.get("classification_rule") in {
        "window_label_not_value", "month_year_stamp", "as_of_date_stamp",
        "econ_bar_series_point", "formula_or_prose", "formula_prose",
        "definition_text", "relation_status", "index_delta_not_level",
        "long_prose_container", "status_sentence", "rev_7d_reject", "mm_scan_note", "nu6_split", "negation_status",
    }:
        return False
    if len(c.get("literal") or "") > 70 and (c.get("kind") in {"ev_tip_read"} or (c.get("label") or "").lower() in META_KEYS):
        return False
    if c.get("coverage_state") == "LEGACY_INACTIVE":
        return False
    if c.get("is_compound_parent"):
        return False
    lit = c.get("literal") or ""
    if not has_number(lit):
        return False
    row = (c.get("label") or "").lower().strip()
    if row in META_KEYS:
        return False
    dk = detect_kind(lit)
    if dk in {"DATE", "STATUS_TEXT", "PROSE", "EMPTY"}:
        return False
    return True
