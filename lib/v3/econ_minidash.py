"""Job #9 token-econ mini-dash — one visual grammar, per-asset facts.

Olly-locked 15 Aug 2026. No fake 0–100 scores. Orange items render grey (pending).
"""

from __future__ import annotations

import html
import math
import re
from typing import Any

_e = html.escape

TICKER_TO_SLUG = {
    "BTC": "btc",
    "SOL": "sol",
    "RENDER": "render",
    "PUMP": "pump",
    "GRASS": "grass",
    "RAY": "ray",
    "IO": "io",
    "NOS": "nos",
    "FARTCOIN": "fartcoin",
    "SPX": "spx6900",
    "SPX6900": "spx6900",
    "ZEC": "zec",
    "HYPE": "hype",
}

ECON_DASH_CSS = """
/* econ-dash-v9 */
.econ-dash { display: flex; flex-wrap: wrap; gap: 0.6rem 0.55rem; margin: 0 0 2.4rem; align-items: flex-start; justify-content: flex-start; }
.econ-dial { width: 4.4rem; display: flex; flex-direction: column; align-items: center; min-width: 0; }
.econ-dial.is-wide { width: 7.2rem; }
.econ-dial-vis { position: relative; width: 3.1rem; height: 3.1rem; }
.econ-dial.is-wide .econ-dial-vis { width: 5.4rem; }
.econ-dial-vis svg { width: 100%; height: 100%; display: block; }
.econ-dial-track { fill: none; stroke: var(--pill-off); stroke-width: 3.2; }
.econ-dial-fill { fill: none; stroke-width: 3.2; stroke-linecap: butt; }
.econ-dial-num {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-family: var(--display); font-size: 0.72rem; font-weight: 700; line-height: 1.05;
  text-align: center; flex-direction: column; gap: 0;
}
.econ-dial-num-sm { font-size: 0.52rem; }
.econ-u { font-size: 70%; font-weight: 700; letter-spacing: 0.02em; }
.econ-dial-label {
  margin-top: 0.2rem; font-size: 0.54rem; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--muted); text-align: center; line-height: 1.15;
}
.econ-sub {
  margin-top: 0.08rem; font-size: 0.46rem; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--muted); text-align: center; line-height: 1.15;
  opacity: 0.85;
}
.econ-dir-box {
  display: flex; align-items: center; justify-content: center;
  width: 3.1rem; height: 3.1rem; border-radius: 50%;
  border: 1.6px solid var(--pill-off);
  font-family: var(--display); font-size: 0.46rem; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase; text-align: center; line-height: 1.1;
}
.econ-dial.is-pending { opacity: 0.42; filter: grayscale(1); }
.econ-dial.has-tip { cursor: default; }
.econ-star { font-size: 0.55rem; vertical-align: super; margin-left: 0.05rem; }
@media (max-width: 700px) {
  .econ-dial.is-wide { width: 7.2rem; }
}
"""

_NUM_UNIT = re.compile(r"^(\+?\$?~?[\d.]+)(%|[MB]|k)$", re.I)


def slug_from_ticker(ticker: Any) -> str:
    return TICKER_TO_SLUG.get(str(ticker or "").upper(), str(ticker or "").lower())


def _num_html(num: str) -> str:
    raw = num.strip()
    m = _NUM_UNIT.match(raw)
    if m:
        return f"{_e(m.group(1))}<span class='econ-u'>{_e(m.group(2))}</span>"
    m = re.match(r"^(\$)([\d.]+)([MBKkm])$", raw)
    if m:
        return f"{_e(m.group(1) + m.group(2))}<span class='econ-u'>{_e(m.group(3))}</span>"
    parts = raw.split("\n")
    if len(parts) > 1:
        return "<br>".join(_e(p) for p in parts)
    return _e(raw)


def _label_html(label: str, star: bool) -> str:
    inner = "<br>".join(_e(p) for p in label.split("\n"))
    if star:
        inner += "<span class='econ-star'>*</span>"
    return inner


def _tip_block(tip: str | None) -> str:
    if not tip:
        return ""
    return f'<div class="metric-tip-template" hidden><p class="metric-tip-source">{_e(tip)}</p></div>'


def _ring_svg(fill: float | None, pending: bool) -> str:
    r = 18.0
    c = 2 * math.pi * r
    if fill is None:
        color = "var(--muted)"
        dash = f"0 {c:.3f}"
    else:
        color = "var(--muted)" if pending else "var(--green)"
        dash = f"{c * min(float(fill), 100.0) / 100:.3f} {c:.3f}"
    return (
        f'<svg viewBox="0 0 44 44" aria-hidden="true">'
        f'<circle class="econ-dial-track" cx="22" cy="22" r="18"/>'
        f'<circle class="econ-dial-fill" cx="22" cy="22" r="18" stroke="{color}" '
        f'stroke-dasharray="{dash}" transform="rotate(-90 22 22)"/></svg>'
    )


def _dial_html(item: dict[str, Any]) -> str:
    kind = item.get("kind") or "ring"
    pending = bool(item.get("pending"))
    star = bool(item.get("star"))
    tip = item.get("tip")
    num = str(item.get("num") or "")
    label = str(item.get("label") or "")
    sub = item.get("sub")
    cls = "econ-dial"
    if item.get("wide") or kind == "wide":
        cls += " is-wide"
    if pending:
        cls += " is-pending"
    if tip:
        cls += " has-tip"
    num_cls = "econ-dial-num"
    plain = num.replace("\n", "")
    if len(plain) > 5 and not _NUM_UNIT.match(plain) and "$" not in plain[:2]:
        num_cls += " econ-dial-num-sm"
    elif len(plain) > 6:
        num_cls += " econ-dial-num-sm"

    if kind == "dir":
        vis = f'<div class="econ-dial-vis"><div class="econ-dir-box">{_num_html(num)}</div></div>'
    else:
        vis = (
            f'<div class="econ-dial-vis">{_ring_svg(item.get("fill"), pending)}'
            f'<span class="{num_cls}">{_num_html(num)}</span></div>'
        )

    sub_html = f'<span class="econ-sub">{_e(str(sub))}</span>' if sub else ""
    return (
        f'<div class="{cls}">{_tip_block(tip)}{vis}'
        f'<span class="econ-dial-label">{_label_html(label, star)}</span>{sub_html}</div>'
    )


def render_econ_minidash(slug: str) -> str:
    items = ASSET_DIALS.get(slug) or ()
    if not items:
        return ""
    ordered = [i for i in items if not (i.get("wide") or i.get("kind") == "wide")]
    ordered += [i for i in items if (i.get("wide") or i.get("kind") == "wide")]
    cells = "".join(_dial_html(i) for i in ordered)
    return f'<div class="econ-dash" data-econ-asset="{_e(slug)}" aria-label="Token economics dials">{cells}</div>'


# --- Olly-locked + Goose orange-field pack 15 Aug 2026. No pending greys. ---

ASSET_DIALS: dict[str, tuple[dict[str, Any], ...]] = {
    "btc": (
        {
            "label": "Circulating",
            "num": "95.6%",
            "fill": 95.6,
            "sub": "20.1M / 21M",
            "tip": "CoinGecko circulating 20.07M of 21M max (13 Aug 2026).",
        },
        {"label": "Issuance\nper year", "num": "0.82%", "fill": None},
        {
            "label": "ETF\nshare",
            "num": "6.3%",
            "fill": 6.3,
            "tip": "US spot ETFs ~1.27M BTC / 20.07M circulating. Not global funds. Not companies.",
        },
        {"label": "Next\nhalving", "num": "APR 2028", "fill": None},
    ),
    "sol": (
        {
            "label": "Circulating",
            "num": "92.2%",
            "fill": 92.2,
            "sub": "582M / 632M",
            "tip": "Share of total supply. SOL has no 21M-style hard max in this pack.",
        },
        {"label": "Issuance\nper year", "num": "3.70%", "fill": None, "sub": "GROSS · ~23M"},
        {"label": "Net growth", "num": "3.66%", "fill": None, "sub": "/ YEAR", "tip": "Gross issuance minus tiny fee-burn. 23.14M / 632M total."},
        {"label": "Staked", "num": "69%", "fill": 69},
        {"label": "Real yield", "num": "~1.7%", "fill": None, "sub": "PARTIAL", "tip": "Stake yield minus inflation. Q2 2026 ~1.7%. Not a live RPC print."},
        {"label": "Fees", "num": "$516k", "fill": None, "sub": "/ DAY"},
        {"label": "Utility", "num": "GAS +\nSTAKE", "fill": None},
    ),
    "render": (
        {
            "label": "Circulating",
            "num": "CONFLICT",
            "fill": None,
            "sub": "555M · 519M · 472M",
            "star": True,
            "tip": "Different counts, not a range. Foundation 555.4M · CoinGecko 518.8M · Solana-only 471.8M. Max 644.2M. Do not average.",
        },
        {
            "label": "Burn",
            "num": "12.8k",
            "fill": None,
            "sub": "LAST 4 WKS",
            "tip": "Work spend (like gas), not a holder buyback. One epoch = 7 days.",
        },
        {"label": "Emissions", "num": "60.0k", "fill": None, "sub": "LAST 4 WKS", "tip": "New RENDER to operators, same 4 weeks."},
        {"label": "Net", "num": "+47.2k", "fill": None, "sub": "28 DAYS", "tip": "Emissions minus burn. Do not annualise this window."},
        {"kind": "dir", "label": "Supply", "num": "NET\nINFL", "tip": "Capped max. Last 4 weeks still printing more than burned."},
        {"label": "Utility", "num": "GPU\nWORK", "fill": None},
    ),
    "pump": (
        {
            "label": "Circulating",
            "num": "39.3%",
            "fill": 39.3,
            "sub": "393B / 1T",
            "tip": "CoinGecko ~39.3% of 1T. Schedule-unlocked is 67.9% — that gap stays. Not the same number.",
        },
        {"label": "Supply\npressure", "num": "31.2%", "fill": 31.2, "sub": "311.67B LEFT", "tip": "Remaining scheduled tokens. Not a quality score."},
        {"label": "Token\nutility", "num": "OPTIONAL", "fill": None, "tip": "Launchpad works without holding PUMP."},
        {"label": "Value\ncapture", "num": "48%", "fill": 48, "tip": "7d holders revenue / protocol revenue: $5.7M / $11.83M. Combined buyback+burn, not a fake score."},
        {"label": "Revenue\n/ fees", "num": "$11.8M", "fill": None, "sub": "/ 7D", "tip": "DefiLlama protocol revenue 7d (15 Aug 2026). Packed $7M/week was stale."},
        {
            "label": "Buyback",
            "num": "$5.7M",
            "fill": None,
            "sub": "/ 7D",
            "tip": "Combined buyback + burn. Cannot split. Not a token burn count.",
        },
        {"kind": "dir", "label": "Liquidity\n(def./inf.)", "num": "RELEAS", "tip": "Still releasing scheduled supply."},
        {
            "kind": "wide",
            "wide": True,
            "label": "Unlock\nschedule",
            "num": "312B",
            "fill": None,
            "sub": "CADENCE UNKNOWN",
            "tip": "Remaining schedule 311.67B (~31.2% of max). Monthly size not first-party.",
        },
    ),
    "grass": (
        {"label": "Circulating", "num": "65.5%", "fill": 65.5, "sub": "655M / 1B"},
        {"label": "Revenue", "num": "$17M", "fill": None, "sub": "H1 2026", "tip": "Company/network figure. Not protocol fees. Not audited."},
        {"kind": "dir", "label": "Supply", "num": "RELEAS", "sub": "~35% LOCKED"},
        {"label": "Utility", "num": "OPTIONAL", "fill": None, "tip": "Customers can pay USD."},
        {"label": "Capture", "num": "UNVERIF", "fill": None, "sub": "REV → GRASS", "tip": "Docs say convert revenue to GRASS. Not measured. Conversion rate unknown."},
    ),
    "ray": (
        {"label": "Circulating", "num": "48.6%", "fill": 48.6, "sub": "270M / 555M"},
        {"label": "Fees", "num": "$5.1M", "fill": None, "sub": "30D · $798k SLICE"},
        {"label": "Buyback", "num": "5.6%", "fill": 5.6, "sub": "15.0M HELD", "tip": "Buybacks sit in a wallet. Held is not burned."},
        {"label": "Emissions", "num": "1.9M", "fill": None, "sub": "0.70% CIRC / YR", "tip": "Docs mining-reserve run-rate. Mint authority disabled."},
        {"kind": "dir", "label": "Supply", "num": "CAPPED", "tip": "Max 555M. Residual emissions ~1.9M/yr. Not deflationary. Buybacks held, not burned."},
        {"label": "Utility", "num": "OPTIONAL", "fill": None, "tip": "You can trade on Raydium without holding RAY."},
        {"label": "Capture", "num": "12%→HELD", "fill": None, "tip": "12% of fees buy RAY. Inventory still exists."},
        {
            "kind": "wide",
            "wide": True,
            "label": "Unlock\nschedule",
            "num": "VEST 0",
            "fill": None,
            "sub": "3/6/12M 0.48 · 0.95 · 1.9M",
            "tip": "Team/seed vest completed 21 Feb 2024. 3/6/12m figures are emissions at the current 1.9M/yr rate, not vest cliffs.",
        },
    ),
    "io": (
        {"label": "Circulating", "num": "47.7%", "fill": 47.7, "sub": "381M / 800M"},
        {"label": "Earnings", "num": "$27M", "fill": None, "sub": "CUM · JUL $0.93M", "tip": "Supplier network earnings in USD. Not protocol revenue. Not IO burns."},
        {"label": "Emissions\nleft", "num": "300M", "fill": None, "sub": "~20 YEARS"},
        {"label": "Utility", "num": "OPTIONAL", "fill": None, "tip": "Customers can pay USDC/card. Suppliers stake IO."},
        {"label": "Capture", "num": "UNVERIF", "fill": None, "sub": "IDE → BURN", "tip": "IDE surplus→burn is design. Measured burn total not production-safe."},
    ),
    "nos": (
        {"label": "Circulating", "num": "~100%", "fill": 100, "sub": "100M / 100M"},
        {"label": "Staked", "num": "12%", "fill": 12},
        {"label": "Utility", "num": "PARTIAL", "fill": None, "tip": "Jobs can settle in credits/Stripe and skip NOS."},
        {"label": "Capture", "num": "PARTIAL", "fill": None, "sub": "JOB → NOS", "tip": "Native rail uses NOS. Credits/Stripe bypass unquantified. Indexer $ is not revenue."},
    ),
    "fartcoin": (
        {"label": "Circulating", "num": "~100%", "fill": 100, "sub": "1B · MINT OFF"},
        {"kind": "dir", "label": "Supply", "num": "FIXED"},
        {"label": "Utility", "num": "MEME", "fill": None},
    ),
    "spx6900": (
        {"label": "Circulating", "num": "93.1%", "fill": 93.1, "sub": "931M / 1B"},
        {"kind": "dir", "label": "Supply", "num": "FIXED", "tip": "Wormhole mint/burn is the bridge, not extra printing."},
        {"label": "Dead", "num": "69.0M", "fill": None, "sub": "BURNED", "tip": "Burn wallet 0x0000. Not locked, not treasury, not unreleased."},
        {"label": "Utility", "num": "MEME", "fill": None},
        {
            "kind": "wide",
            "wide": True,
            "label": "Unlock\nschedule",
            "num": "0",
            "fill": None,
            "sub": "3 / 6 / 12M",
            "tip": "Fair launch. Owner renounced. No vest book. 3/6/12m = 0.",
        },
    ),
    "zec": (
        {"label": "Circulating", "num": "80.4%", "fill": 80.4, "sub": "16.9M / 21M"},
        {"label": "Issuance\nper year", "num": "3.9%", "fill": None, "sub": "~657k ZEC", "tip": "Mining issuance, not a vest unlock."},
        {"label": "Next 12m\nissuance", "num": "657k", "fill": None},
        {"kind": "dir", "label": "Supply", "num": "INFL", "tip": "Capped 21M. Still inflating."},
        {"label": "Utility", "num": "MONEY +\nPRIVACY", "fill": None},
    ),
    "hype": (
        {
            "label": "Circulating",
            "num": "22/30",
            "fill": None,
            "sub": "CG 22.2% · HL 29.9%",
            "star": True,
            "tip": "CoinGecko 22.2% (222M) and Hyperliquid 29.9% (299M) of 1B. Different definitions. Do not average. Do not pick one.",
        },
        {"label": "Fees", "num": "$44.8M", "fill": None, "sub": "30D", "tip": "Venue trading fees. Not holder yield."},
        {
            "label": "AF stock",
            "num": "46.4M",
            "fill": None,
            "sub": "15.5% HL CIRC",
            "tip": "Assistance Fund still holds ~46.4M. Held is not burned. Do not say 46M burned.",
        },
        {
            "label": "AF buys",
            "num": "$31.1M",
            "fill": None,
            "sub": "30D",
            "tip": "DefiLlama holders revenue: 1d $0.84M · 7d $5.94M · 30d $31.14M. Token buy count not reconstructed.",
        },
        {"label": "Emissions\nleft", "num": "412M", "fill": None, "tip": "Future emissions stock. 3/6/12m cadence unknown — omitted."},
        {"label": "Utility", "num": "GAS +\nSTAKE", "fill": None, "tip": "Needed for the chain. Not needed to trade BTC/ETH on the venue."},
        {
            "kind": "wide",
            "wide": True,
            "label": "System",
            "num": "351M",
            "fill": None,
            "sub": "AF 46 · LAB 241 · FDN 60",
            "tip": "System inventory, not whale concentration: AF 46.4M · HyperLabs 241.2M · Foundation 60.4M · grants 3.0M. Discretionary owners unknown.",
        },
    ),
}


def pending_fields(slug: str) -> list[str]:
    return [str(i.get("label") or "").replace("\n", " ") for i in ASSET_DIALS.get(slug, ()) if i.get("pending")]
