"""Per-dimension evidence completeness — EVIDENCE-COMPLETENESS-RULES.md predicates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lib.v3.convergence.engine import DIM_FUNDAMENTALS_SUPPLY
from lib.v3.convergence.profiles import AssetProfile

COMPLETE = "COMPLETE"
PARTIAL = "PARTIAL"
INSUFFICIENT = "INSUFFICIENT"

RS_STRONG_PP = 1.0
RS_WEAK_PP = -1.0
LEVERAGE_LED_RATIO = 2.0
SPOT_LED_RATIO = 0.85
MEME_FLOAT_PCT = 0.88

# Retrace-from-ATH thresholds for Price+RS are not frozen — structure (50d/200d) proxies tape.
#
# CRYPTO7 — Fundamentals / Supply directional state (SUPPORTIVE/STRESSED):
# Frozen examples only defend meme_float (FART/SPX). For RENDER/SOL/HYPE/RAY/PUMP/IO/GRASS/NOS
# the bundle carries usage, value-capture, and supply-pressure inputs but no approved rule to
# combine them into a directional state. Mapper stays NEUTRAL (or UNKNOWN for NOS emissions)
# with evidence COMPLETE/PARTIAL per feed presence — not single-metric STRESSED.


@dataclass
class BundleContext:
    profile: AssetProfile
    price_ok: bool
    price_usd: float | None
    ath_usd: float | None
    freshness: str | None
    chg_30d: float | None
    pp_btc_30: float | None
    pp_sol_30: float | None
    pp_extra_30: float | None
    technical_ok: bool
    above_50: bool | None
    above_200: bool | None
    leverage_ok: bool
    spot_listed: bool | None
    perp_spot: float | None
    oi_usd: float | None
    funding: float | None
    coinbase_spot_ok: bool
    concentration_ok: bool
    concentration_top20_pct: float | None
    labelled_wm_balance: float | None
    helius_ok: bool
    helius_net_positive: bool | None
    circ: float | None
    max_supply: float | None
    render_foundation_ok: bool
    render_bme_ok: bool
    render_last4_burned: float | None
    render_last4_emit: float | None
    render_frames_ok: bool
    hype_hl_ok: bool
    hype_circulating: float | None
    hype_future_emissions: float | None
    zec_shielded_ok: bool
    sol_rpc_ok: bool
    sol_issuance_yr: float | None
    pump_squads_ok: bool
    meme_static_ok: bool


def _num(v: Any) -> float | None:
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _meme_static_ok(sym: str, row: dict[str, Any]) -> bool:
    if not row.get("ok"):
        return False
    if sym == "FARTCOIN":
        return row.get("mint_authority_revoked") is True and row.get("freeze_authority_revoked") is True
    if sym == "SPX6900":
        return row.get("portal_architecture_known") is True
    return False


def build_context(bundle: dict[str, Any], profile: AssetProfile) -> BundleContext:
    sym = profile.sym
    prices = ((bundle.get("prices") or {}).get("assets") or {}).get(sym) or {}
    feeds = bundle.get("feeds") or {}
    cg = (feeds.get("cg_by_id") or {}).get(profile.coin_id) or {}
    tech = ((bundle.get("technicals") or {}).get("assets") or {}).get(profile.slug) or {}
    lev = (feeds.get("leverage") or {}).get(sym) or {}
    conc = (feeds.get("concentration") or {}).get(sym) or {}
    labelled = feeds.get("labelled") or {}
    helius = (feeds.get("helius_sample") or {}).get(sym) or {}
    assets = bundle.get("assets") or {}
    supply_static = ((feeds.get("supply_static") or {}).get(sym) or {})

    btc_30 = _num((feeds.get("cg_by_id") or {}).get("bitcoin", {}).get("chg_30d"))
    sol_30 = _num((feeds.get("cg_by_id") or {}).get("solana", {}).get("chg_30d"))
    asset_30 = _num(prices.get("change_30d_pct")) or _num(cg.get("chg_30d"))

    pp_btc = (asset_30 - btc_30) if asset_30 is not None and btc_30 is not None else None
    pp_sol = (asset_30 - sol_30) if asset_30 is not None and sol_30 is not None else None

    pp_extra = None
    if profile.extra_rs_coin_id:
        extra_30 = _num((feeds.get("cg_by_id") or {}).get(profile.extra_rs_coin_id, {}).get("chg_30d"))
        if asset_30 is not None and extra_30 is not None:
            pp_extra = asset_30 - extra_30

    wm_key = {"FARTCOIN": "fart_wm", "SPX6900": "spx_wm", "RAY": "ray_buyback"}.get(sym)
    wm_bal = _num(labelled.get(wm_key)) if wm_key else None

    render = assets.get("render") or {}
    hype = assets.get("hype") or {}
    zec = feeds.get("zec") or {}
    sol_rpc = feeds.get("sol_rpc") or {}
    hl = hype.get("hyperliquid") or {}
    bme = render.get("bme") or {}
    bme_emit = render.get("bme_emit") or {}
    frames = render.get("frames") or {}

    helius_net = None
    if helius.get("ok"):
        net = _num(helius.get("net_tokens"))
        helius_net = net > 0 if net is not None else None

    above_50 = tech.get("above_50") if tech.get("ok") else None
    above_200 = tech.get("above_200") if tech.get("ok") else None
    if above_50 is not None:
        above_50 = bool(above_50)
    if above_200 is not None:
        above_200 = bool(above_200)

    return BundleContext(
        profile=profile,
        price_ok=bool(prices.get("ok")),
        price_usd=_num(prices.get("price_usd")),
        ath_usd=_num(prices.get("ath_usd")) or _num(cg.get("ath")),
        freshness=prices.get("freshness"),
        chg_30d=asset_30,
        pp_btc_30=pp_btc,
        pp_sol_30=pp_sol,
        pp_extra_30=pp_extra,
        technical_ok=bool(tech.get("ok")),
        above_50=above_50,
        above_200=above_200,
        leverage_ok=bool(lev.get("ok")),
        spot_listed=lev.get("spot_listed") if lev else None,
        perp_spot=_num(lev.get("perp_spot")),
        oi_usd=_num(lev.get("oi_usd")),
        funding=_num(lev.get("funding")),
        coinbase_spot_ok=bool((feeds.get("coinbase_fart") or {}).get("ok")) if sym == "FARTCOIN" else False,
        concentration_ok=bool(conc.get("ok")),
        concentration_top20_pct=_num(conc.get("top20_pct")) or _num(conc.get("top_20_pct")),
        labelled_wm_balance=wm_bal,
        helius_ok=bool(helius.get("ok")),
        helius_net_positive=helius_net,
        circ=_num(prices.get("circulating_supply")) or _num(cg.get("circ")),
        max_supply=_num(cg.get("max")) or _num(cg.get("total")),
        render_foundation_ok=bool((render.get("foundation") or {}).get("ok")),
        render_bme_ok=bool(bme.get("ok")),
        render_last4_burned=_num(bme.get("last4_burned")),
        render_last4_emit=_num(bme_emit.get("last4_emit")),
        render_frames_ok=bool(frames.get("ok")),
        hype_hl_ok=bool(hl.get("ok")),
        hype_circulating=_num(hl.get("circulating")) or _num(hl.get("circulatingSupply")),
        hype_future_emissions=_num(hl.get("future_emissions")) or _num(hl.get("futureEmissions")),
        zec_shielded_ok=bool(zec.get("ok")) and zec.get("provenance") == "LIVE" and not zec.get("cache_fallback"),
        sol_rpc_ok=bool(sol_rpc.get("ok")),
        sol_issuance_yr=_num(sol_rpc.get("issuance_yr")),
        pump_squads_ok=bool(labelled.get("pump_squads_n", 0) or labelled.get("ok")),
        meme_static_ok=_meme_static_ok(sym, supply_static),
    )


def _rs_signal(ctx: BundleContext) -> str:
    if ctx.profile.rs_profile == "nos_sol_render":
        if ctx.pp_sol_30 is not None:
            if ctx.pp_sol_30 >= RS_STRONG_PP:
                return "STRONG"
            if ctx.pp_sol_30 <= RS_WEAK_PP:
                return "WEAK"
        return "NEUTRAL"

    if ctx.pp_btc_30 is not None and ctx.pp_sol_30 is not None:
        if ctx.pp_btc_30 >= RS_STRONG_PP and ctx.pp_sol_30 >= RS_STRONG_PP:
            return "STRONG"
        if ctx.pp_btc_30 <= RS_WEAK_PP and ctx.pp_sol_30 <= RS_WEAK_PP:
            return "WEAK"
    return "NEUTRAL"


def _structure_signal(ctx: BundleContext) -> str | None:
    if not ctx.technical_ok or ctx.above_50 is None or ctx.above_200 is None:
        return None
    if ctx.above_50 and ctx.above_200:
        return "STRONG"
    if not ctx.above_50 and not ctx.above_200:
        return "WEAK"
    return "NEUTRAL"


def price_rs_state(ctx: BundleContext) -> str:
    if not ctx.price_ok:
        return "UNKNOWN"

    rs = _rs_signal(ctx)
    struct = _structure_signal(ctx)

    if struct is None:
        return rs if rs in ("STRONG", "WEAK") else "NEUTRAL"

    if rs == "STRONG" and struct == "STRONG":
        return "STRONG"
    if rs == "WEAK" and struct == "WEAK":
        return "WEAK"
    return "NEUTRAL"


def _price_rs_complete(ctx: BundleContext) -> bool:
    fresh = ctx.freshness in (None, "CURRENT")
    has_ath = ctx.ath_usd is not None
    if not (fresh and has_ath and ctx.technical_ok):
        return False

    if ctx.profile.rs_profile == "nos_sol_render":
        return ctx.pp_sol_30 is not None and ctx.pp_extra_30 is not None

    btc_sol_pp = ctx.pp_btc_30 is not None and ctx.pp_sol_30 is not None
    if ctx.profile.rs_profile == "btc_sol_extra":
        extra_ok = ctx.pp_extra_30 is not None
        return btc_sol_pp and extra_ok

    return btc_sol_pp


def _price_rs_partial(ctx: BundleContext) -> bool:
    if not ctx.price_ok:
        return False

    has_ath = ctx.ath_usd is not None

    if ctx.profile.rs_profile == "nos_sol_render":
        sol_ok = ctx.pp_sol_30 is not None
        render_ok = ctx.pp_extra_30 is not None
        return sol_ok or render_ok or has_ath

    btc_sol_pp = ctx.pp_btc_30 is not None and ctx.pp_sol_30 is not None
    return btc_sol_pp or has_ath


def price_rs_evidence(ctx: BundleContext) -> str:
    if not ctx.price_ok:
        return INSUFFICIENT

    if _price_rs_complete(ctx):
        return COMPLETE
    if _price_rs_partial(ctx):
        return PARTIAL
    return INSUFFICIENT


def spot_state(ctx: BundleContext) -> str:
    if ctx.leverage_ok and ctx.perp_spot is not None:
        if ctx.perp_spot >= LEVERAGE_LED_RATIO:
            return "LEVERAGE_LED"
        if ctx.spot_listed and ctx.perp_spot <= SPOT_LED_RATIO:
            return "SPOT_LED"
        return "MIXED"
    if ctx.coinbase_spot_ok and ctx.profile.sym == "FARTCOIN":
        return "MIXED"
    return "UNKNOWN"


def spot_evidence(ctx: BundleContext) -> str:
    venue_ok = ctx.leverage_ok or ctx.coinbase_spot_ok
    if not venue_ok:
        return INSUFFICIENT

    has_panel = (
        ctx.perp_spot is not None
        and ctx.oi_usd is not None
        and ctx.funding is not None
        and ctx.spot_listed is not None
    )

    if (
        has_panel
        and ctx.profile.spot_helius_flow
        and ctx.helius_ok
        and ctx.helius_net_positive is not None
    ):
        return COMPLETE

    if venue_ok and (ctx.perp_spot is not None or ctx.oi_usd is not None):
        return PARTIAL

    return INSUFFICIENT


def whales_state(ctx: BundleContext) -> str:
    if ctx.profile.whale_structural_opaque:
        return "OPAQUE"
    if ctx.helius_ok and ctx.helius_net_positive is True:
        return "ACCUMULATING"
    if ctx.helius_ok and ctx.helius_net_positive is False:
        return "DISTRIBUTING"
    if ctx.concentration_ok or ctx.labelled_wm_balance:
        return "OPAQUE"
    return "UNKNOWN"


def whales_evidence(ctx: BundleContext) -> str:
    if ctx.profile.whale_structural_opaque and (ctx.concentration_ok or ctx.labelled_wm_balance or ctx.price_ok):
        return PARTIAL

    if (
        ctx.concentration_ok
        and ctx.helius_ok
        and ctx.helius_net_positive is not None
        and not ctx.profile.whale_structural_opaque
    ):
        return COMPLETE

    if ctx.concentration_ok or ctx.labelled_wm_balance is not None:
        return PARTIAL

    return INSUFFICIENT


def attention_state(_ctx: BundleContext) -> str:
    return "UNKNOWN"


def attention_evidence(_ctx: BundleContext) -> str:
    return INSUFFICIENT


def _meme_near_full_float(ctx: BundleContext) -> bool:
    return bool(ctx.max_supply and ctx.circ and ctx.circ / ctx.max_supply >= MEME_FLOAT_PCT)


def _render_fundamentals_panel_ok(ctx: BundleContext) -> bool:
    """Usage + burn/emit panel present — evidence only; not a directional state rule."""
    has_bme = ctx.render_bme_ok and ctx.render_last4_burned is not None
    has_emit = ctx.render_last4_emit is not None
    has_usage = ctx.render_frames_ok or (has_bme and (ctx.render_last4_burned or 0) > 0)
    return bool(
        ctx.render_foundation_ok
        and has_bme
        and has_emit
        and has_usage
    )


def supply_state(ctx: BundleContext) -> str:
    """Directional state — only where frozen research defends it."""
    if ctx.circ is None:
        return "UNKNOWN"

    sp = ctx.profile.supply_profile

    if sp == "meme_float":
        if _meme_near_full_float(ctx) and ctx.meme_static_ok:
            return "SUPPORTIVE"
        return "NEUTRAL"

    if sp == "vesting_partial" and ctx.profile.sym == "NOS":
        return "UNKNOWN"

    return "NEUTRAL"


def supply_evidence(ctx: BundleContext) -> str:
    if ctx.circ is None:
        return INSUFFICIENT

    sp = ctx.profile.supply_profile
    circ_ok = ctx.circ is not None and ctx.circ > 0

    if sp == "btc_macro" and circ_ok:
        return COMPLETE
    if sp == "sol_enhanced" and circ_ok and ctx.sol_rpc_ok:
        return COMPLETE
    if sp == "render_enhanced" and circ_ok:
        if _render_fundamentals_panel_ok(ctx):
            return COMPLETE
        if ctx.render_foundation_ok or ctx.render_bme_ok:
            return PARTIAL
        return PARTIAL
    if sp == "hype_enhanced" and circ_ok and ctx.hype_hl_ok:
        return COMPLETE
    if sp == "zec_enhanced" and circ_ok and ctx.zec_shielded_ok:
        return COMPLETE
    if sp == "pump_squads" and circ_ok and ctx.pump_squads_ok:
        return COMPLETE
    if sp == "meme_float":
        if circ_ok and _meme_near_full_float(ctx) and ctx.meme_static_ok:
            return COMPLETE
        if circ_ok:
            return PARTIAL
        return INSUFFICIENT
    if sp == "vesting_partial" and circ_ok:
        return PARTIAL
    if circ_ok:
        return PARTIAL
    return INSUFFICIENT


def dimension_rows(ctx: BundleContext) -> list[tuple[str, str, str]]:
    return [
        ("Price + RS", price_rs_state(ctx), price_rs_evidence(ctx)),
        ("Spot / Capital", spot_state(ctx), spot_evidence(ctx)),
        ("Whales / Players", whales_state(ctx), whales_evidence(ctx)),
        ("Attention", attention_state(ctx), attention_evidence(ctx)),
        (DIM_FUNDAMENTALS_SUPPLY, supply_state(ctx), supply_evidence(ctx)),
    ]
