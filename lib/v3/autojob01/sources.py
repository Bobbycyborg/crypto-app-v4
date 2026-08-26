"""Real approved sources for AUTOJOB01 fields. One live dependency can feed many fields."""

from __future__ import annotations

from typing import Any

# Canonical live jobs — not 244 APIs.
DEP = {
    "CG_MARKETS": "CoinGecko coins/markets (price, ATH, circ, mcap, 7d/30d/1y)",
    "BN_SPOT": "Binance spot 24h ticker (listed pairs only)",
    "BN_DAILY": "Binance spot daily klines (50d/200d/July floor)",
    "BN_PERP": "Binance USDT-M perp ticker + openInterest + premiumIndex",
    "DEX": "DexScreener pair for Solana mint",
    "RPC": "Solana RPC (qty, token supply, largest accounts)",
    "FRED": "FRED WALCL/WDTGAL/RRPONTSYD/M2SL/NFCI/ECBASSETSW/JPNASSETS",
    "LLAMA_STABLE": "DefiLlama stablecoincharts/all",
    "LLAMA_HYPE": "DefiLlama summary/fees/hyperliquid",
    "LLAMA_PUMP": "DefiLlama summary/fees/pump.fun",
    "LLAMA_RAY": "DefiLlama summary/fees/raydium + tvl/raydium",
    "LLAMA_SOL": "DefiLlama historicalChainTvl/Solana + summary/fees/solana",
    "FARSIDE": "Farside Investors BTC/ETH/SOL US spot ETF tables",
    "FNG": "alternative.me fear and greed",
    "CG_GLOBAL": "CoinGecko /global BTC.D",
    "HL_INFO": "Hyperliquid info tokenDetails HYPE",
    "FOUNDATION": "Render Foundation supplyInfo + epochBurnStats + liabilityEpochs",
    "ZEC_EXPL": "zcashexplorer.app /api/v1/blockchain-info",
    "IO_EXPL": "api.io.solutions /v1/io-explorer network earnings",
    "NOS_IDX": "Nosana blockchain-indexer /jobs/count and /stats",
    "HELIUS": "Helius enhanced txs / bounded Solana DEX sample (same as Stage-1)",
    "DOCS": "Tokenomics parameter / historical disclosure — not a weekly API",
    "DERIVED": "Derived from already-pulled canonical inputs (no extra API)",
}


def sources_for(field: dict[str, Any]) -> tuple[str, str | None]:
    text = field.get("report_01_text") or ""
    asset = (field.get("asset") or "").lower()
    sec = field.get("visible_section") or ""
    label = field.get("visible_label") or ""
    cls = field.get("classification") or ""

    if cls == "UNKNOWN":
        return "none", None
    if "52B unlocked · 287M" in text or "52B unlocked" in text:
        return DEP["RPC"] + " remaining Squads balances ; historical WM OTC is not weekly", None
    if "Jan 2025" in text or "Aug 10 fee share" in text or "12%→HELD" in text or "$17M" in text:
        return DEP["DOCS"], None
    if text.strip() in ("~1.7 %", "~1.7%") or "Real yield" in label:
        return DEP["DOCS"] + " — Q2 2026 stake yield minus inflation; not a live RPC print", None
    if cls == "MULTI" or "Foundation circ" in text or "22.2% CG" in text or "29.9% HL" in text or "CONFLICT 22%" in text:
        if "Foundation" in text or "555.40M" in text:
            return DEP["FOUNDATION"], DEP["CG_MARKETS"]
        return DEP["CG_MARKETS"], DEP["HL_INFO"]

    if sec in ("holdings_strip", "hero") or label in ("hold-px", "hold-owned", "alt-price"):
        return DEP["CG_MARKETS"] + " ; " + DEP["BN_SPOT"] + " ; " + DEP["DEX"], DEP["RPC"]
    if "Portfolio" in label or sec == "market_top" and "metric-value" in label:
        return DEP["RPC"] + " × live price", None
    if "Global liquidity" in text or "Stablecoins $" in text:
        return DEP["FRED"], DEP["LLAMA_STABLE"]
    if "RETRACED" in text and "ATH" in text:
        return DEP["CG_MARKETS"] + " ATH+price", DEP["BN_DAILY"] + " July low"
    if "beat BTC" in text or "above 50d" in text:
        return DEP["CG_MARKETS"] + " 30d + market_chart 50DMA", None
    if "perps" in text and "spot" in text and asset in ("market", "page"):
        return DEP["BN_PERP"] + " and Binance spot 24h BTCUSDT", None
    if " 7 M D" in text or " 30 M D" in text or "7 D" in text:
        return DEP["FARSIDE"], None
    if "Fear" in label or sec == "market_top" and "fg" in (field.get("css_class") or ""):
        return DEP["FNG"], None

    if "retraced from ATH" in text or "from ATH" in text:
        return DEP["CG_MARKETS"] + " price+ATH (derived %)", None
    if "fut/spot" in text.lower() or "Fut/spot" in text or "perp" in text.lower() and "OI" in text:
        return DEP["BN_PERP"], None
    if "BTC.D" in text:
        return DEP["CG_GLOBAL"], None
    if "Stables" in text and asset == "btc":
        return DEP["LLAMA_STABLE"], None
    if "Liq pulse" in text:
        return DEP["FRED"], None
    if "Beat BTC" in text:
        return DEP["CG_MARKETS"], None
    if "ETF cum" in text or "ETF share" in text.lower() or "ETF" in text and "6.3" in text:
        return DEP["FARSIDE"] + " all-time / holdings vs " + DEP["CG_MARKETS"] + " circ", None
    if "July low" in text:
        return DEP["BN_DAILY"], None
    if "50d" in text or "200d" in text:
        return DEP["BN_DAILY"] + " else CoinGecko daily", None

    if asset == "hype" and ("fee" in text.lower() or "$44.8" in text or "$31" in text):
        return DEP["LLAMA_HYPE"], None
    if asset == "hype" and ("Inventory" in text or "AF" in text or "NCU" in text or "totalSupply" in text):
        return DEP["HL_INFO"], None
    if asset == "pump" and ("Revenue" in text or "Buyback" in text or "Fees now" in text or "$11.8" in text or "$5.7" in text or "$7.0" in text):
        return DEP["LLAMA_PUMP"], None
    if asset == "ray" and ("TVL" in text or "Fees" in text or "$5.1" in text or "$846" in text):
        return DEP["LLAMA_RAY"], None
    if asset == "sol" and ("TVL" in text or "fees" in text.lower() or "$516" in text or "$4.80" in text):
        return DEP["LLAMA_SOL"], None
    if asset == "render" and ("burn" in text.lower() or "emit" in text.lower() or "BME" in text or "frames" in text.lower()):
        return DEP["FOUNDATION"], None
    if asset in ("io",) and ("earnings" in text.lower() or "$26.7" in text or "$27" in text or "$27,120" in text):
        return DEP["IO_EXPL"], None
    if asset == "nos" and ("Jobs" in text or "staked" in text.lower() or "NOS" in text and "$25.3" in text):
        return DEP["NOS_IDX"], None
    if "Sample buy" in text or "Sample sell" in text or "Top-5 buy" in text or "Top5 buy" in text or "Gross buy" in text:
        return DEP["HELIUS"], None
    if "Shielded" in text or "of chain" in text and asset == "zec":
        return DEP["ZEC_EXPL"], None
    if "CG circ" in text or "Circulating" in label or "%" in text and "circ" in text.lower():
        return DEP["CG_MARKETS"] + " circulating_supply", None
    if "top-20" in text.lower() or "Top-20" in text or "Sol top-20" in text:
        return DEP["RPC"] + " getTokenLargestAccounts", None

    if "RETRACED" in text and "FROM ATH" in text:
        return DEP["DERIVED"] + " from CoinGecko BTC ATH+price and Binance July-low daily", None
    if "Aug 3" in text or ("M D" in text and sec == "market_top"):
        return DEP["FARSIDE"] + " daily net-flow rows (same table as 7d/30d)", None
    if text.strip() in ("6.3 %", "6.3%") or "ETF\nshare" in label or "ETF share" in label:
        return DEP["FARSIDE"] + " US spot ETF BTC holdings / CoinGecko circulating", None
    if asset == "pump" and text.strip() in ("31.2 %", "31.2%"):
        return DEP["DOCS"] + " remaining scheduled 311.67B / 1T", None
    if asset == "ray" and ("5.6" in text and "%" in text):
        return DEP["RPC"] + " RAY buyback-holder balance / CoinGecko circ", None
    if asset == "sol" and ("3.70" in text or "3.66" in text or text.strip() in ("69 %", "69%", "68.8%")):
        return DEP["RPC"] + " getInflationRate + getVoteAccounts / supply", None
    if asset == "zec" and "3.9" in text:
        return DEP["ZEC_EXPL"] + " chain issuance / circulating (derived %)", None
    if "Parent 24h" in label or "$106M" in text:
        return "DefiLlama summary/dexs/raydium 24h and 30d volume", None
    if "$798k" in text:
        return DEP["LLAMA_RAY"] + " holdersRevenue 30d", None
    if "LEADING" in text:
        return DEP["DERIVED"] + " from CoinGecko 30d PUMP minus BTC/SOL 30d", None
    if "$17.7M" in text:
        return DEP["DEX"] + " pair liquidityUsd (same DexScreener mint as price)", None
    if "Vol" in label or "$95k" in text and asset == "grass":
        return DEP["CG_MARKETS"] + " total_volume", None
    if "CG vol" in text:
        return DEP["CG_MARKETS"] + " total_volume", None
    if "Perp vs CB" in text or "perp vs CB" in text.lower():
        return DEP["BN_PERP"] + " quoteVolume / Coinbase FARTCOIN-USD 24h quote (Stage-1)", None
    if "registry wallet" in text or "WM ~379" in text or "Burned/dead" in text or "69.0M" in text:
        return DEP["RPC"] + " labelled token accounts (same Stage-1 registry)", None
    if "Solana ~9%" in text:
        return DEP["DERIVED"] + " from Solana RPC supply / CoinGecko circ", None
    if "vs 30d max" in text or "Vs 30d max" in text:
        return DEP["BN_PERP"] + " openInterest vs 30d max of same series (derived %)", None
    if "Stables" in text and asset == "sol" or (asset == "sol" and "$15.64B" in text):
        return "DefiLlama stablecoinchains Solana totalCirculatingUSD.peggedUSD", None
    if "DEX 7d vs ETH" in text or "DEX latest" in text or "1.762" in text:
        return "DefiLlama dexs/chains Solana vs Ethereum (derived ratio)", None
    if "LaunchLab" in text or "of Sol DEX" in text:
        return "DefiLlama dexs Raydium LaunchLab + Solana DEX 24h (derived share)", None
    if "pp ·" in text or "180d return" in text:
        return DEP["DERIVED"] + " from CoinGecko/Binance 30d and 180d already pulled", None
    if sec in ("risk_confirmation", "forensics_or_fingerprint", "asset_body", "mini_dash"):
        return DEP["DERIVED"] + " from already-pulled canonical inputs (no extra API)", None
    return DEP["CG_MARKETS"], None
