"""PUMP-only hero mini-dashboard — amendment evidence, 7d bar charts."""

from __future__ import annotations

from typing import Any

from lib.v3.econ_minidash import _dial_html, _e, _label_html, _num_html, _tip_block

PUMP_MINIDASH_CSS = """
/* pump-hero-minidash-v1 */
[data-asset="pump"] .econ-dash.pump-dash {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 0.5rem 0.45rem;
  margin: 0.85rem 0 0;
  align-items: start;
  width: 100%;
}
[data-asset="pump"] .pump-dash .econ-dial {
  width: auto;
  max-width: none;
}
[data-asset="pump"] .pump-dash .econ-dial.is-chart {
  min-width: 0;
}
[data-asset="pump"] .econ-chart-wrap {
  position: relative;
  width: 3.1rem;
  height: 3.1rem;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-end;
}
[data-asset="pump"] .econ-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1px;
  height: 2.35rem;
  width: 100%;
  padding: 0 0.05rem;
}
[data-asset="pump"] .econ-bar {
  flex: 1 1 0;
  min-width: 0;
  border-radius: 1px 1px 0 0;
  background: var(--green);
  opacity: 0.92;
}
[data-asset="pump"] .econ-bar.is-last { opacity: 1; }
[data-asset="pump"] .econ-chart-kpi {
  font-family: var(--display);
  font-size: 0.52rem;
  font-weight: 700;
  line-height: 1.05;
  text-align: center;
  color: var(--ink);
  margin-top: 0.12rem;
}
[data-asset="pump"] .alt-stance-headline {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 1.42rem;
  line-height: 1.1;
}
[data-asset="pump"] .alt-stance-expl-text {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
@media (max-width: 1100px) {
  [data-asset="pump"] .econ-dash.pump-dash { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
@media (max-width: 700px) {
  [data-asset="pump"] .econ-dash.pump-dash { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
"""

PUMP_STANCE_CLAMP_CSS = PUMP_MINIDASH_CSS  # same scoped block


def _usd_short(v: float | None) -> str:
    if v is None:
        return "—"
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:.0f}"


def _tok_short(v: float | None) -> str:
    if v is None:
        return "—"
    if v >= 1e9:
        return f"{v / 1e9:.1f}B"
    if v >= 1e6:
        return f"{v / 1e6:.0f}M"
    return f"{v / 1e3:.0f}k"


def _bar_chart_cell(
    *,
    label: str,
    values: list[float],
    kpi: str,
    sub: str | None = None,
    tip: str | None = None,
    unit_fn=_usd_short,
) -> str:
    if not values:
        return _dial_html({"label": label, "num": "—", "fill": None, "tip": tip})
    mx = max(values) or 1.0
    bars = []
    for i, v in enumerate(values):
        h = max(12.0, 100.0 * float(v) / mx)
        last = " is-last" if i == len(values) - 1 else ""
        bars.append(
            f'<span class="econ-bar{last}" style="height:{h:.0f}%" '
            f'title="{_e(unit_fn(v))}"></span>'
        )
    tip_html = _tip_block(tip)
    cls = "econ-dial is-chart has-tip" if tip else "econ-dial is-chart"
    sub_html = f'<span class="econ-sub">{_e(sub)}</span>' if sub else ""
    return (
        f'<div class="{cls}">{tip_html}'
        f'<div class="econ-chart-wrap"><div class="econ-bars">{"".join(bars)}</div>'
        f'<span class="econ-chart-kpi">{_num_html(kpi)}</span></div>'
        f'<span class="econ-dial-label">{_label_html(label, False)}</span>{sub_html}</div>'
    )


def render_pump_minidash(amd: dict[str, Any] | None) -> str:
    amd = amd or {}
    buy = amd.get("buyback") or {}
    tape = amd.get("tape") or {}
    unlocks = amd.get("unlocks") or {}
    pol = amd.get("policy") or {}
    daily_usd = [float(v) for v in (buy.get("daily_last7_usd") or [])]
    px = tape.get("last_price") or (amd.get("supply_burn") or {}).get("price_used")
    daily_tok = [float(v) for v in (buy.get("daily_last7_pump_est") or [])]
    if not daily_tok and px and daily_usd:
        daily_tok = [v / float(px) for v in daily_usd]

    rev_7d = buy.get("revenue_7d_usd")
    buy_7d = buy.get("total_7d_usd")
    wow = buy.get("wow_pct")

    # Circulating ~39% CG-style; on-chain gap is not the same number
    supply = amd.get("supply") or {}
    circ_pct = float(supply["circ_pct"]) if isinstance(supply.get("circ_pct"), (int, float)) else 39.3
    circ_sub = str(supply.get("circ_sub") or "393B / 1T")
    sched_pct = 31.2
    sched_sub = "312B scheduled"

    sep = unlocks.get("september") or {}
    sep_ll = sep.get("linear_defillama_tokens")
    sep_tok = sep.get("tokenomics_tokens")
    sep_b_ll = f"{float(sep_ll) / 1e9:.1f}B" if sep_ll else "?"
    sep_b_tok = f"{float(sep_tok) / 1e9:.1f}B" if sep_tok else "?"

    fut = tape.get("futures_quote_24h_usd") or 0
    spot = tape.get("spot_quote_24h_usd") or 0
    fund = tape.get("funding_8h")
    tape_read = tape.get("read") or "UNKNOWN"
    fund_calm = fund is not None and abs(float(fund)) < 0.0002

    cells: list[str] = []

    cells.append(
        _dial_html(
            {
                "label": "Circulating",
                "num": f"{circ_pct:.1f}%",
                "fill": circ_pct,
                "sub": circ_sub,
                "tip": "CoinGecko-style float share. On-chain supply ≠ circulating.",
            }
        )
    )
    cells.append(
        _dial_html(
            {
                "label": "Supply\npressure",
                "num": f"{sched_pct:.1f}%",
                "fill": sched_pct,
                "sub": sched_sub,
                "tip": (
                    "Scheduled tokens still vesting — not all are circulating float. "
                    "July was a cliff; August drip 6.875B. Post-unlock flow still under observation."
                ),
            }
        )
    )
    cells.append(
        _dial_html(
            {
                "label": "Value\ncapture",
                "num": "~50%",
                "fill": 50.0,
                "sub": "LOCKED APR27",
                "tip": (
                    (pol.get("allocation") or "~50% parent net revenue → open-market PUMP purchases → burn")
                    + ". Locked ~through Apr 2027, then discretionary. Not 100% of revenue."
                ),
            }
        )
    )
    cells.append(
        _dial_html(
            {
                "label": "Revenue",
                "num": _usd_short(rev_7d).replace("$", "$"),
                "fill": None,
                "sub": "/ 7D",
                "tip": "DefiLlama protocol revenue 7d. Distinct from holdersRevenue buyback line.",
            }
        )
    )
    cells.append(
        _bar_chart_cell(
            label="Buybacks",
            values=daily_usd,
            kpi=_usd_short(buy_7d),
            sub=(f"+{wow:.0f}% vs prior wk" if wow is not None else "/ 7D"),
            tip=(
                f"Latest {_usd_short(buy.get('latest_daily_usd'))}/d · "
                f"7d range {_usd_short(buy.get('daily_min_7d_usd'))}–{_usd_short(buy.get('daily_max_7d_usd'))}. "
                "DefiLlama holdersRevenue = on-chain PUMP buyback/burn USD."
            ),
        )
    )
    if daily_tok:
        cells.append(
            _bar_chart_cell(
                label="Est. PUMP\nbought*",
                values=daily_tok,
                kpi=_tok_short(buy.get("pump_bought_7d_est")),
                sub="/ 7D EST",
                tip=(
                    "USD buyback ÷ live price. Same buyback→burn path — not a pure cumulative burn tally. "
                    "Cannot split buyback vs burn in this feed."
                ),
                unit_fn=_tok_short,
            )
        )
    cells.append(
        _dial_html(
            {
                "kind": "dir",
                "label": "Market\nactivity",
                "num": "PERPS\nLEAD" if tape_read == "PERPS LEAD" else tape_read.replace(" ", "\n"),
                "sub": "FUND CALM" if fund_calm else "CHECK FUND",
                "tip": (
                    f"Binance futures {_usd_short(fut)} vs spot {_usd_short(spot)} 24h. "
                    f"Funding {fund}. Calm funding ≠ spot-led."
                ),
            }
        )
    )
    cells.append(
        _dial_html(
            {
                "kind": "dir",
                "label": "Next\nunlock",
                "num": "SEP\n~12",
                "sub": f"{sep_b_ll} VS {sep_b_tok}",
                "tip": (
                    "September unlock: DefiLlama 6.875B vs Tokenomics 9.17B — UNRESOLVED. "
                    "August 12 + Aug 15 = one event. Transfer ≠ sale."
                ),
            }
        )
    )

    return (
        f'<div class="econ-dash pump-dash" data-econ-asset="pump" '
        f'aria-label="PUMP token economics mini-dashboard">{"".join(cells)}</div>'
    )
