"""Per-asset convergence profiles — benchmarks and supply/whale defaults."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SupplyProfile = Literal[
    "btc_macro",
    "sol_enhanced",
    "render_enhanced",
    "hype_enhanced",
    "zec_enhanced",
    "pump_squads",
    "meme_float",
    "vesting_partial",
    "standard_circ",
]

RsProfile = Literal[
    "btc_sol",
    "btc_sol_extra",
    "nos_sol_render",
]


@dataclass(frozen=True)
class AssetProfile:
    sym: str
    slug: str
    coin_id: str
    extra_rs_coin_id: str | None = None
    rs_profile: RsProfile = "btc_sol"
    supply_profile: SupplyProfile = "standard_circ"
    whale_structural_opaque: bool = False
    spot_helius_flow: bool = False
    binance_perp: bool = True


PROFILES: dict[str, AssetProfile] = {
    "BTC": AssetProfile("BTC", "btc", "bitcoin", supply_profile="btc_macro", whale_structural_opaque=True, binance_perp=True),
    "SOL": AssetProfile("SOL", "sol", "solana", supply_profile="sol_enhanced", binance_perp=True),
    "RENDER": AssetProfile(
        "RENDER", "render", "render-token",
        supply_profile="render_enhanced",
        spot_helius_flow=True,
        binance_perp=True,
    ),
    "PUMP": AssetProfile("PUMP", "pump", "pump-fun", supply_profile="pump_squads", binance_perp=True),
    "GRASS": AssetProfile(
        "GRASS", "grass", "grass",
        extra_rs_coin_id="render-token",
        rs_profile="btc_sol_extra",
        supply_profile="vesting_partial",
        binance_perp=True,
    ),
    "RAY": AssetProfile("RAY", "ray", "raydium", spot_helius_flow=True, binance_perp=True),
    "IO": AssetProfile(
        "IO", "io", "io",
        extra_rs_coin_id="render-token",
        rs_profile="btc_sol_extra",
        supply_profile="vesting_partial",
        binance_perp=True,
    ),
    "NOS": AssetProfile(
        "NOS", "nos", "nosana",
        extra_rs_coin_id="render-token",
        rs_profile="nos_sol_render",
        supply_profile="vesting_partial",
        binance_perp=False,
    ),
    "FARTCOIN": AssetProfile(
        "FARTCOIN", "fartcoin", "fartcoin",
        extra_rs_coin_id="pump-fun",
        rs_profile="btc_sol_extra",
        supply_profile="meme_float",
        binance_perp=True,
    ),
    "SPX6900": AssetProfile("SPX6900", "spx6900", "spx6900", supply_profile="meme_float", binance_perp=True),
    "ZEC": AssetProfile("ZEC", "zec", "zcash", supply_profile="zec_enhanced", whale_structural_opaque=True, binance_perp=True),
    "HYPE": AssetProfile("HYPE", "hype", "hyperliquid", supply_profile="hype_enhanced", binance_perp=True),
}

TWELVE = tuple(PROFILES.keys())


def get_profile(sym: str) -> AssetProfile:
    if sym not in PROFILES:
        raise KeyError(f"unknown asset {sym!r}")
    return PROFILES[sym]
