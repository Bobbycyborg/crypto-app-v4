"""Current Stance — human judgement from independent evidence families.

No magic score. No auto WAIT/deploy/reduce gates. No invented thresholds.
"""

from __future__ import annotations

import html
from typing import Any


def _e(s: Any) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def make_stance(
    *,
    headline: str,
    summary: str,
    confidence: str,
    why: str,
    supports: list[str],
    holds_back: list[str],
    stronger_if: list[str],
    weaker_if: list[str],
) -> dict[str, Any]:
    """Single source of truth for asset Current Stance (Job #5)."""
    conf = (confidence or "MEDIUM").upper()
    if conf not in ("HIGH", "MEDIUM", "LOW"):
        conf = "MEDIUM"
    return {
        "headline": headline,
        "summary": summary,
        "confidence": conf,
        "why": why,
        "supports": list(supports)[:3],
        "holds_back": list(holds_back)[:3],
        "stronger_if": list(stronger_if)[:2],
        "weaker_if": list(weaker_if)[:2],
        # Compatibility aliases for older readers
        "explanation": summary,
    }


def btc_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="JUST ABOVE 200D · ETF INFLOWS · LEVERAGE HEAVY",
        summary=(
            "Week bounce put BTC just above the 50d and 200d (~$69.5k, +9% / 7d). "
            "US spot ETFs printed +$606M on 20 Aug, with four straight inflow days (~+$1.55B from 14–20 Aug). "
            "That is support. 60d structure is still lower-high / lower-low. Perps still ~10× spot."
        ),
        confidence="MEDIUM",
        why=(
            "Price reclaimed the 200-day (~$69.0k) after a +9.4% week, with ~45% still retraced from ATH. "
            "Farside US spot BTC ETFs: 20 Aug +$606.3M; 19 Aug +$517.2M; 18 Aug +$189.3M; 17 Aug +$297.5M. "
            "14–20 Aug net is about +$1.55B. All-time creations still ~$53.5B. "
            "Binance perps remain ~10× spot. Structure last-60d is still LH+LL — inflow plus a reclaim, not a proven breakout."
        ),
        supports=[
            "Spot is above both 50d and 200d on this print",
            "ETF last day +$606M (20 Aug) and four consecutive inflow sessions",
            "+9.4% / 7d bounce is real in USD",
        ],
        holds_back=[
            "60d structure still LH+LL — rebound, not proven trend change",
            "Perps ~10× spot; funding +0.01%/8h — leverage still heavy",
            "~45% retraced from ATH",
        ],
        stronger_if=[
            "Inflows continue while price holds above the 200d",
            "60d structure stops printing lower highs; perp/spot cools",
        ],
        weaker_if=[
            "Price loses the 200d on expanding perp dominance",
            "ETF prints flip back to multi-day outflows",
        ],
    )


def pump_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="VALUE CAPTURE STRONG · RS LEADS · PERPS STILL LEAD",
        summary=(
            "~50% of parent net revenue is still locked into open-market PUMP buys through ~Apr 2027 — not 100%. "
            "30d price leads BTC/SOL (+58%). 7d buybacks +5%. Tape is still perp-led; funding is calm. "
            "Unlock behaviour after transfers is not finished evidence."
        ),
        confidence="MEDIUM",
        why=(
            "Platform value capture is still the strong leg: ~$7.8M protocol revenue / 7d and ~$5.7M buybacks / 7d. "
            "That path is ~50% of parent net revenue, locked ~through Apr 2027, then discretionary. "
            "Price confirmation improved this week (golden-cross ~6d, +12.7% / 7d, +57.7% / 30d). "
            "Binance perps are still ~8.5× spot. Funding is calm — that is not spot-led. Transfer ≠ sale."
        ),
        supports=[
            "~50% revenue → open-market buys → burn, locked ~Apr 2027",
            "7d buybacks +5% vs prior week; revenue +7%",
            "30d RS leads BTC by ~+52pp and SOL by ~+48pp",
        ],
        holds_back=[
            "Perps still lead (~8.5× spot); funding calm ≠ spot demand",
            "September unlock still split: DefiLlama ~6.9B vs Tokenomics ~9.2B — unresolved",
            "August recipient → CEX/DEX/OTC 72h flow UNKNOWN. Transfer ≠ sale.",
        ],
        stronger_if=[
            "Spot quote rises while funding stays calm and buybacks continue",
            "72h tracing shows no material August-recipient flow to liquid venues",
        ],
        weaker_if=[
            "Daily close below $0.00215",
            "Material UNKNOWN-holder or Squads supply reaches CEX/DEX with proven selling",
        ],
    )


def zec_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="SHIELDED STOCK · 7D BOUNCE · 30D STILL MIXED",
        summary=(
            "Shielded-pool stock and the monetary schedule are unchanged. "
            "This week bounced with majors (+12% / 7d) but 30d (+1.2%) still lags BTC/SOL. "
            "Owners and flows stay opaque. Capture is monetary, not cash-flow."
        ),
        confidence="MEDIUM",
        why=(
            "The 7d bounce does not rewrite the ZEC picture. Shielded stock is still the structural fact. "
            "30d RS lags BTC (−5pp) and SOL (−8pp). Throughput and owner identity were not refreshed this pass. "
            "Price is still far below ATH (~83% retraced)."
        ),
        supports=[
            "~4.37M ZEC / ~26% shielded stock with Ironwood active post-NU6.3",
            "Major spot venues remain live (Binance + Coinbase)",
            "Above 50d and 200d on this print (50>200)",
        ],
        holds_back=[
            "30d still lags BTC/SOL despite the 7d bounce",
            "No cash-flow-style token capture — holder thesis depends on monetary/network demand",
            "Ownership, buyer/seller quality and shielded usage-rate trend remain UNKNOWN",
        ],
        stronger_if=[
            "Verified shielded usage rises without leverage dominating discovery",
            "30d RS vs BTC turns sustainably positive",
        ],
        weaker_if=[
            "Shielded stock stagnates or falls while price depends on leverage",
            "Major venue access deteriorates",
        ],
    )


def hype_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="FEES REAL · AF BUYBACKS REAL · RS NOW LEADS",
        summary=(
            "Venue fees and fee-funded AF buys are still the strong facts. "
            "The old 'RS soft' line is dead this week: +26% / 7d, +14% / 30d, leads BTC and SOL. "
            "Only ~7% off ATH. Supply is still minority-circulating. AF buy ≠ organic demand."
        ),
        confidence="MEDIUM",
        why=(
            "Hyperliquid usage/fees and the Assistance Fund buyback path are unchanged as mechanisms. "
            "What changed is tape: 30d HYPE leads BTC by ~+8pp and SOL by ~+5pp, above 50d and 200d (50>200). "
            "That is relative strength, not proof of non-AF buying. Circulating is still a minority of supply."
        ),
        supports=[
            "Fee-funded AF still buys HYPE — mechanism is real",
            "+25.9% / 7d and +14.2% / 30d; leads both BTC and SOL",
            "Price holds above 50d and 200d; only ~7% retraced from ATH",
        ],
        holds_back=[
            "Circulating definition split + large remaining supply",
            "Total-supply burn accounting unresolved",
            "Buyer quality beyond AF still UNKNOWN; no Binance spot pair in this feed",
        ],
        stronger_if=[
            "Fees hold up while non-AF spot demand becomes visible",
            "Contributor cadence and burn accounting resolve on first-party data",
        ],
        weaker_if=[
            "Fee decline while emissions/releases enter float",
            "AF inventory starts distributing rather than accumulating",
        ],
    )


def fartcoin_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="7D BOUNCE · STILL BELOW 200D · OWNERS UNKNOWN",
        summary=(
            "Mint/freeze revoked, near-full float, liquid venues still exist. "
            "This week bounced with majors (+13% / 7d) but price is still below the 200d and ~94% off ATH. "
            "30d is only in line with BTC, still lags SOL. Large holders mostly unlabeled."
        ),
        confidence="MEDIUM",
        why=(
            "The 7d bounce does not fix structure. Price is above the 50d and still below the 200d. "
            "30d +5.8% vs BTC +6.2% / SOL +9.5%. Binance perps remain material. "
            "Stage 2 ownership map is still incomplete — not a discretionary-whale call."
        ),
        supports=[
            "Real multi-venue spot liquidity remains after the ATH collapse",
            "Mint and freeze authorities revoked; circulating ≈ max",
            "+13.4% / 7d — bounce with the majors is real",
        ],
        holds_back=[
            "Still below 200d; ~94% retraced from ATH",
            "30d still lags SOL; leverage is material",
            "Large-holder identities remain mostly unlabeled",
        ],
        stronger_if=[
            "Price reclaims the 200d with spot-led participation, not just OI",
            "Verified labeling shows discretionary holders accumulating rather than distributing",
        ],
        weaker_if=[
            "OI/funding expand while the 50d fails and FART/SOL rolls over",
            "Verified large discretionary holders move size toward exchanges",
        ],
    )


def nos_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="NETWORK ACTIVE · RAIL REAL · 7D BOUNCE",
        summary=(
            "GPU jobs and the NOS rail are still the real facts. Open-market buying from those jobs is still unproven. "
            "Tape improved this week (+13% / 7d, above 50d and 200d). 30d is only with BTC, still slightly lags SOL."
        ),
        confidence="MEDIUM",
        why=(
            "Nothing in the usage/capture story flipped. What flipped is the 7d tape. "
            "Price is above 50d and 200d after a death-cross ~18d ago on the averages — 50 still below 200. "
            "30d +7.0% vs BTC +6.2% / SOL +9.5%. Credits vs paid NOS conversion still UNKNOWN."
        ),
        supports=[
            "First-party jobs + GPU-hours (network operationally alive)",
            "Documented NOS payment / coordination rail",
            "+13.2% / 7d and price above both moving averages this print",
        ],
        holds_back=[
            "Usage → open-market NOS demand still unproven",
            "50d still below 200d (death-cross ~18d) — bounce, not a golden cross",
            "30d still lags SOL; holder concentration UNKNOWN",
        ],
        stronger_if=[
            "Paid NOS settlement share disclosed and rising",
            "50d reclaims 200d while NOS/SOL stops lagging",
        ],
        weaker_if=[
            "Jobs/hours fade while emissions remain high",
            "Price loses the 50d without any clearer NOS conversion evidence",
        ],
    )


def grass_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="REVENUE REAL · CAPTURE EARLY · TAPE STILL WEAK",
        summary=(
            "Disclosed revenue and utility are unchanged. Revenue-driven GRASS buying is still unmeasured. "
            "This week did not bounce with majors (−5% / 7d, −21% / 30d). Price is below 50d and 200d."
        ),
        confidence="MEDIUM",
        why=(
            "Unlike SOL/BTC/HYPE, GRASS did not participate in the week bounce. "
            "30d lags BTC by ~27pp and SOL by ~30pp. Vesting overhang and unproven token capture still stand. "
            "SMA is perp-venue labelled — treat as tape, not a spot SMA."
        ),
        supports=[
            "First-party revenue disclosure still stands",
            "Documented GRASS utility / revenue-conversion design",
            "Stage 2 USDC rewards add no new GRASS emissions for that payout",
        ],
        holds_back=[
            "Revenue-driven GRASS buying remains unmeasured",
            "Material vesting/unlock overhang",
            "7d and 30d both lag BTC/SOL; price below 50d and 200d",
        ],
        stronger_if=[
            "Verified persistent revenue-funded GRASS buys/burns at meaningful scale",
            "Unlock pressure eases while GRASS/SOL improves",
        ],
        weaker_if=[
            "Large unlocks continue without clearer token value capture",
            "GRASS keeps making lower lows while majors hold the bounce",
        ],
    )


def io_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="EARNINGS REAL · CAPTURE EARLY · 30D STILL WEAK",
        summary=(
            "Network earnings and compute are still real. IO payment/burn capture is still unproven. "
            "A +11% / 7d bounce happened; 30d is still −20% and lags BTC/SOL hard. Price is below 50d and 200d."
        ),
        confidence="MEDIUM",
        why=(
            "The 7d bounce is a bounce, not a capture upgrade. ~half of max supply is still not circulating. "
            "30d lags BTC by ~26pp and SOL by ~29pp. Burns remain unmeasured. Customers can still pay in USDC/card."
        ),
        supports=[
            "First-party network earnings and compute-hour data",
            "Documented IO payment incentive, staking and IDE burn design",
            "+10.7% / 7d — participated in the week bounce",
        ],
        holds_back=[
            "Measured IO burns/buy-pressure unproven",
            "Material emissions/vesting overhang",
            "30d still lags badly; price below 50d and 200d",
        ],
        stronger_if=[
            "Verified persistent IO burns/buybacks at material scale under IDE",
            "Price reclaims 50d/200d while IO/SOL stops lagging",
        ],
        weaker_if=[
            "Network earnings keep softening while token capture stays unmeasured",
            "The 7d bounce fails and 30d lag widens into more unlocks",
        ],
    )


def spx_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="7D BOUNCE · 30D STILL LAGS · BUYERS UNKNOWN",
        summary=(
            "~84% off ATH. CEX-heavy, owners opaque, ~93% circulating — those facts did not change. "
            "This week bounced hard (+16% / 7d) and is above 50d and 200d. 30d still lags BTC/SOL. Buyers still UNKNOWN."
        ),
        confidence="MEDIUM",
        why=(
            "A 7d bounce and a 50>200 print are not the same as 30d leadership. "
            "30d +3.5% vs BTC +6.2% / SOL +9.5%. Buyer quality was not identified this pass. "
            "Do not treat ZEC-style exceptions as SPX evidence."
        ),
        supports=[
            "~93% of max supply already circulating",
            "Active multi-venue CEX liquidity",
            "+16.1% / 7d; price above 50d and 200d (50>200)",
        ],
        holds_back=[
            "30d still lags BTC and SOL",
            "Buyer/seller quality UNKNOWN",
            "~84% retraced from ATH; leverage present on Binance perps",
        ],
        stronger_if=[
            "30d SPX/SOL and SPX/BTC turn sustainably positive with clearer spot participation",
            "Verified persistent accumulation by identifiable non-MM capital",
        ],
        weaker_if=[
            "The 7d bounce fades while 30d lag continues",
            "Verified material discretionary distribution from large holders",
        ],
    )


def ray_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="PROTOCOL ACTIVE · BUYBACK REAL · 30D STILL LAGS",
        summary=(
            "Raydium still has volume and a documented fee→RAY buyback. "
            "Price is now above 50d and 200d, but 30d still lags BTC/SOL. "
            "Helius DEX sample failed this pass (429) — do not pretend buyer quality was re-checked."
        ),
        confidence="MEDIUM",
        why=(
            "The SMA reclaim is new. The 30d lag is not: −6.7% vs BTC +6.2% / SOL +9.5%. "
            "Buyback mechanism is still documented. Recent on-chain accumulation pace and organic vs MM flow "
            "were not freshly verified this week because the Helius RAY sample 429'd."
        ),
        supports=[
            "Raydium still clears substantial DEX volume and fees",
            "12% fee→RAY buyback route is documented",
            "Price above 50d and 200d this print (range LH+HL)",
        ],
        holds_back=[
            "30d lags BTC ~13pp and SOL ~16pp",
            "Helius RAY sample failed — buyer quality this week is UNKNOWN",
            "7d bounce (+5.4%) was weaker than SOL/BTC",
        ],
        stronger_if=[
            "Fresh sample shows organic spot accumulation while RAY/SOL stops lagging",
            "Auditable buyback consolidation continues",
        ],
        weaker_if=[
            "Fees/revenue deteriorate while RAY loses the 50d",
            "Verified unlock/treasury distribution reaches liquid venues without matching demand",
        ],
    )


def render_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="USAGE REAL · BME INFLATIONARY · 30D STILL WEAK",
        summary=(
            "Usage and BME burns are still real, and recent burns still sit below node emissions. "
            "A +8% / 7d bounce happened with BTC. 30d is still −11% and lags badly. "
            "Price remains below 50d and 200d (death-cross ~39d). Helius sample 429'd this pass."
        ),
        confidence="MEDIUM",
        why=(
            "Network use does not make RENDER scarce this week any more than last week. "
            "30d lags BTC by ~17pp and SOL by ~20pp. The 7d bounce is not a 50d reclaim. "
            "DEX-buyer concentration was not re-measured (Helius 429)."
        ),
        supports=[
            "Real measurable Render Network usage",
            "BME genuinely links network jobs to RENDER burns",
            "+8.2% / 7d — participated in the week bounce",
        ],
        holds_back=[
            "Recent BME is still net inflationary (unchanged mechanism read)",
            "Below 50d and 200d; death-cross ~39d",
            "30d RS weak; this week's buyer concentration UNKNOWN (sample fail)",
        ],
        stronger_if=[
            "Verified burns rise toward or above emissions",
            "Price reclaims 50d while 30d RS vs SOL improves",
        ],
        weaker_if=[
            "Emissions continue materially exceeding burns",
            "The 7d bounce fails and 30d lag widens",
        ],
    )


def sol_current_stance() -> dict[str, Any]:
    return make_stance(
        headline="ABOVE 200D · LEADS BTC 30D · STILL INFLATIONARY",
        summary=(
            "The old 'tape weak' line is dead this week: +12% / 7d, +9.5% / 30d, leads BTC by ~3pp. "
            "Price is above 50d and 200d. Ecosystem depth is still real. Issuance still dwarfs burn. "
            "Who is buying or selling is still UNKNOWN."
        ),
        confidence="MEDIUM",
        why=(
            "SOL reclaimed both moving averages and is leading BTC on 30d. That is a tape change. "
            "It is still ~71% retraced from ATH, 50d is still below 200d, and perps are ~7.9× spot. "
            "Fees/issuance/burn identity were not rewritten by the bounce. "
            "US SOL spot ETFs printed +$14.6M on 20 Aug — real but small next to the BTC ETF pulse."
        ),
        supports=[
            "Above 50d and 200d; 30d leads BTC (+9.5% vs +6.2%)",
            "TVL, stables and DEX activity remain substantial",
            "+12.3% / 7d bounce is real in USD",
        ],
        holds_back=[
            "~71% retraced from ATH; 50d still below 200d",
            "Issuance still exceeds burn; buyer/seller identity UNKNOWN",
            "Perps ~7.9× spot — bounce is not proven spot-led",
        ],
        stronger_if=[
            "50d reclaims 200d while SOL/BTC keeps leading",
            "Fee intensity rises and burn closes more of the issuance gap",
        ],
        weaker_if=[
            "Price loses the 200d while 30d BTC leadership fades",
            "Fee intensity and net dilution stay depressed with no clearer flow identity",
        ],
    )


STANCE_FOR_SLUG = {
    "btc": btc_current_stance,
    "sol": sol_current_stance,
    "pump": pump_current_stance,
    "hype": hype_current_stance,
    "zec": zec_current_stance,
    "fartcoin": fartcoin_current_stance,
    "nos": nos_current_stance,
    "grass": grass_current_stance,
    "io": io_current_stance,
    "spx6900": spx_current_stance,
    "ray": ray_current_stance,
    "render": render_current_stance,
}


def resolve_stance(asset_top: dict[str, Any]) -> dict[str, Any]:
    """Prefer current_stance; fall back to legacy current_posture."""
    stance = asset_top.get("current_stance")
    if isinstance(stance, dict) and stance.get("headline"):
        return stance
    legacy = asset_top.get("current_posture") or {}
    if not legacy:
        return make_stance(
            headline="EVIDENCE INCOMPLETE",
            summary="Not enough verified evidence to describe the asset picture yet.",
            confidence="LOW",
            why="Evidence is incomplete, so no stance is locked yet.",
            supports=[],
            holds_back=["Insufficient verified evidence"],
            stronger_if=["Core market and capital-flow evidence becomes available"],
            weaker_if=["Key evidence remains missing or contradictory"],
        )
    return make_stance(
        headline=str(legacy.get("headline") or "EVIDENCE INCOMPLETE"),
        summary=str(legacy.get("summary") or legacy.get("explanation") or ""),
        confidence=str(legacy.get("confidence") or "MEDIUM"),
        why=str(legacy.get("why") or legacy.get("explanation") or ""),
        supports=list(legacy.get("supports") or []),
        holds_back=list(legacy.get("holds_back") or []),
        stronger_if=list(legacy.get("stronger_if") or []),
        weaker_if=list(legacy.get("weaker_if") or []),
    )


def _ul(items: list[str]) -> str:
    if not items:
        return "<p class='stance-empty'>None locked yet.</p>"
    lis = "".join(f"<li>{_e(x)}</li>" for x in items)
    return f"<ul class='stance-list'>{lis}</ul>"


def stance_modal_body_html(stance: dict[str, Any]) -> str:
    """Inner modal content only (~100–180 words target)."""
    conf = _e(stance.get("confidence") or "MEDIUM")
    return (
        f"<p class='stance-conf'>Evidence confidence · {conf}</p>"
        f"<p class='stance-p'>{_e(stance.get('why'))}</p>"
        f"<section class='stance-sec'>"
        f"<h3 class='stance-h'>What supports it</h3>"
        f"{_ul(list(stance.get('supports') or []))}"
        f"</section>"
        f"<section class='stance-sec'>"
        f"<h3 class='stance-h'>What holds it back</h3>"
        f"{_ul(list(stance.get('holds_back') or []))}"
        f"</section>"
        f"<section class='stance-sec'>"
        f"<h3 class='stance-h'>What would change it</h3>"
        f"<div class='stance-change'>"
        f"<div><h4 class='stance-h4'>Stronger if</h4>{_ul(list(stance.get('stronger_if') or []))}</div>"
        f"<div><h4 class='stance-h4'>Weaker if</h4>{_ul(list(stance.get('weaker_if') or []))}</div>"
        f"</div>"
        f"</section>"
    )


def stance_hero_block_html(stance: dict[str, Any], *, clamp_lines: bool = False) -> str:
    """Hero Current Stance column + hidden modal source for (see more)."""
    body = stance_modal_body_html(stance)
    summary = _e(stance.get("summary"))
    expl = (
        f'<span class="alt-stance-expl-text">{summary}</span> '
        if clamp_lines
        else f"{summary} "
    )
    return (
        f'<div class="alt-stance">'
        f'<span class="alt-eyebrow">Current Stance</span>'
        f'<div class="alt-stance-headline">{_e(stance.get("headline"))}</div>'
        f'<p class="alt-stance-expl">'
        f"{expl}"
        f'<button type="button" class="stance-see-more">(see more)</button>'
        f"</p>"
        f'<div class="stance-modal-src" hidden>{body}</div>'
        f"</div>"
    )


STANCE_CSS = """
.alt-stance { text-align: right; min-width: 0; }
.alt-stance-headline {
  font-family: var(--display);
  font-size: 1.55rem;
  font-weight: 700;
  line-height: 1.12;
  color: var(--orange);
  text-transform: uppercase;
  margin: 0.55rem 0 0.55rem;
}
.alt-stance-expl {
  margin: 0;
  font-size: 0.92rem;
  line-height: 1.45;
  color: var(--ink);
  max-width: 36rem;
  margin-left: auto;
}
.stance-see-more {
  appearance: none;
  border: 0;
  background: none;
  padding: 0;
  margin: 0;
  font: inherit;
  font-size: inherit;
  color: var(--muted);
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}
.stance-see-more:hover,
.stance-see-more:focus-visible {
  color: var(--ink);
  outline: none;
}
.stance-modal-root {
  position: fixed; inset: 0; z-index: 10050;
  display: flex; align-items: center; justify-content: center;
  padding: 1rem;
}
.stance-modal-root[hidden] { display: none !important; }
.stance-modal-backdrop {
  position: absolute; inset: 0;
  background: rgba(18, 20, 28, 0.48);
  backdrop-filter: blur(2px);
}
[data-theme="dark"] .stance-modal-backdrop {
  background: rgba(0, 0, 0, 0.62);
}
.stance-modal-panel {
  position: relative;
  z-index: 1;
  width: min(560px, 100%);
  max-height: min(82vh, 720px);
  overflow: auto;
  background: var(--surface-strong, var(--surface));
  color: var(--ink);
  border: 1px solid var(--pill-off, #3d4256);
  border-radius: 16px;
  box-shadow: 0 18px 48px rgba(0,0,0,0.28);
  padding: 1.25rem 1.35rem 1.4rem;
}
.stance-modal-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 1rem; margin-bottom: 0.85rem;
}
.stance-modal-title {
  font-family: var(--display);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin: 0;
  color: var(--muted);
}
.stance-modal-close {
  appearance: none; border: 0; background: transparent;
  color: var(--muted); font-size: 1.35rem; line-height: 1;
  cursor: pointer; padding: 0.1rem 0.35rem; border-radius: 8px;
}
.stance-modal-close:hover,
.stance-modal-close:focus-visible { color: var(--ink); outline: none; }
.stance-conf {
  margin: 0 0 0.9rem;
  font-size: 0.72rem;
  color: var(--muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.stance-sec { margin: 0 0 1rem; }
.stance-h {
  font-family: var(--display);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0 0 0.4rem;
}
.stance-h4 {
  font-family: var(--display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin: 0 0 0.35rem;
  color: var(--muted);
}
.stance-p {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.45;
}
.stance-list {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.88rem;
  line-height: 1.4;
}
.stance-list li { margin: 0.28rem 0; }
.stance-change {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem 1.1rem;
}
.stance-empty { margin: 0; font-size: 0.88rem; color: var(--muted); }
@media (max-width: 640px) {
  .alt-stance { text-align: left; border-top: 1px solid var(--pill-off, #3d4256); padding-top: 1.1rem; }
  .alt-stance-expl { margin-left: 0; max-width: none; }
  .stance-change { grid-template-columns: 1fr; }
}
body.stance-modal-open { overflow: hidden; }
"""


STANCE_MODAL_SHELL = """
<div id="stance-modal" class="stance-modal-root" hidden>
  <div class="stance-modal-backdrop" data-stance-close="1"></div>
  <div class="stance-modal-panel" role="dialog" aria-modal="true" aria-labelledby="stance-modal-title" tabindex="-1">
    <div class="stance-modal-head">
      <h2 id="stance-modal-title" class="stance-modal-title">Why this stance</h2>
      <button type="button" class="stance-modal-close" data-stance-close="1" aria-label="Close">×</button>
    </div>
    <div id="stance-modal-body"></div>
  </div>
</div>
"""


STANCE_JS = """
(function () {
  var modal = document.getElementById('stance-modal');
  var body = document.getElementById('stance-modal-body');
  if (!modal || !body) return;
  var lastFocus = null;
  function openFrom(btn) {
    var host = btn.closest('.alt-stance') || btn.closest('.alt-posture');
    if (!host) return;
    var src = host.querySelector('.stance-modal-src');
    if (!src) return;
    lastFocus = btn;
    body.innerHTML = src.innerHTML;
    modal.hidden = false;
    document.body.classList.add('stance-modal-open');
    var panel = modal.querySelector('.stance-modal-panel');
    if (panel) panel.focus();
  }
  function closeModal() {
    modal.hidden = true;
    body.innerHTML = '';
    document.body.classList.remove('stance-modal-open');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
    lastFocus = null;
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.stance-see-more');
    if (btn) { e.preventDefault(); openFrom(btn); return; }
    if (e.target.closest('[data-stance-close]')) { closeModal(); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) closeModal();
  });
})();
"""
