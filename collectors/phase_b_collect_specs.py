"""Job 2B Phase B collector specs for previously BLOCKED_SOURCE metrics.

Hand-authored COLLECT/DERIVE bindings from V3 recovery evidence + CGPT decisions.
Excluded from this module (handled elsewhere): io.emissions.tokens.remaining (PRESERVE),
drift.price.usd.live (INACTIVE).
"""

from __future__ import annotations

# New request_key values not yet in collectors/source_requests.py:
#   - binance.fapi.fundingRate.SOLUSDT
#   - binance.fapi.klines.FARTCOINUSDT.1d
#   - binance.fapi.klines.HYPEUSDT.1d
#   - binance.fapi.klines.SOLUSDT.1d
#   - binance.fapi.klines.SPXUSDT.1d
#   - binance.fapi.openInterest.HYPEUSDT
#   - binance.fapi.openInterest.IOUSDT
#   - binance.fapi.openInterestHist.BTCUSDT.1d
#   - binance.fapi.openInterestHist.SPXUSDT.1d
#   - binance.fapi.ticker24h.FARTCOINUSDT
#   - binance.fapi.ticker24h.HYPEUSDT
#   - binance.fapi.ticker24h.IOUSDT
#   - binance.fapi.ticker24h.RENDERUSDT
#   - binance.fapi.ticker24h.SOLUSDT
#   - binance.fapi.ticker24h.SPXUSDT
#   - binance.spot.klines.IOUSDT.1d
#   - binance.spot.klines.RENDERUSDT.1d
#   - binance.spot.klines.ZECUSDT.1d
#   - binance.spot.ticker24h.IOUSDT
#   - binance.spot.ticker24h.RENDERUSDT
#   - binance.spot.ticker24h.SOLUSDT
#   - binance.spot.tickerPrice.BONKUSDT
#   - binance.spot.tickerPrice.ORCAUSDT
#   - coinbase.spot.stats.FARTCOIN-USD
#   - coingecko.market_chart.nosana
#   - defillama.overview.dexs.ethereum
#   - defillama.stablecoincharts.all
#   - dexscreener.token.2z
#   - dexscreener.token.fartcoin
#   - dexscreener.token.giga
#   - dexscreener.token.lockin
#   - dexscreener.token.retardio
#   - external_sample.sol_staking_apy
#   - forensics.pump.ownership_vesting
#   - hyperliquid.info.metaAndAssetCtxs
#   - hyperliquid.info.validatorSummaries
#   - io.inventory
#   - io.total_earnings_summary
#   - nosana.jobs.stats
#   - nosana.stats
#   - render.dashboard.main
#   - render.liabilityEpochs
#   - solana.rpc.getSupply
#   - solana.rpc.getTokenLargestAccounts.spx
#   - solana.rpc.getTokenSupply.pump
#   - stage1.fart.top20_classified

PHASE_B_COLLECT: dict[str, dict] = {}


def _c(metric_id: str, **kw) -> None:
    PHASE_B_COLLECT[metric_id] = kw

_c('2z.price.usd.live',
    disposition='COLLECT',
    derivation=None,
    source_key='dexscreener',
    request_key='dexscreener.token.2z',
    selector={'type': 'named_record_field', 'name': 'dex_live_price_highest_liquidity'},
    normalizer={'type': 'identity'},
    notes='index-v4.html dex:J6pQQ3FAcJQeWPPGppWRb4nM8jU3wLyYbRrLh7feMfvd highest-liquidity priceUsd.',
)

_c('bonk.price.usd.live',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.tickerPrice.BONKUSDT',
    selector={'type': 'json_pointer', 'pointer': '/price'},
    normalizer={'type': 'identity'},
    notes='index-v4.html data-feed spot:BONKUSDT; Binance spot ticker price.',
)

_c('btc.inflation.pct.current',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'btc_issuance_inflation_pct', 'identity': {'id': 'bitcoin'}, 'block_reward': 3.125},
    normalizer={'type': 'identity'},
    notes='V3 apply_dynamic btc_body: 3.125*144*365/circulating*100 from CG bitcoin circulating_supply.',
)

_c('btc.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.BTCUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 200, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES btc→spot BTCUSDT; SMA200 USD.',
)

_c('btc.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.BTCUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 50, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES btc→spot BTCUSDT; SMA50 USD.',
)

_c('btc.oi.change.pct.1d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.openInterestHist.BTCUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'open_interest_change_pct', 'window': 1},
    normalizer={'type': 'identity'},
    notes='Binance openInterestHist sumOpenInterestValue Δ1d for BTCUSDT.',
)

_c('btc.oi.change.pct.30d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.openInterestHist.BTCUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'open_interest_change_pct', 'window': 30},
    normalizer={'type': 'identity'},
    notes='Binance openInterestHist sumOpenInterestValue Δ30d for BTCUSDT.',
)

_c('btc.oi.change.pct.7d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.openInterestHist.BTCUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'open_interest_change_pct', 'window': 7},
    normalizer={'type': 'identity'},
    notes='Binance openInterestHist sumOpenInterestValue Δ7d for BTCUSDT.',
)

_c('btc.stablecoin.change.pct.30d',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.stablecoincharts.all',
    selector={'type': 'named_record_field', 'name': 'stablecoin_change_pct', 'window_days': 30},
    normalizer={'type': 'identity'},
    notes='lib/stablecoin_supply.py fetch_stablecoin_supply change_30d_pct.',
)

_c('btc.supply.circulating.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'ratio_pct', 'records_pointer': '/', 'identity': {'id': 'bitcoin'}, 'num_field': 'circulating_supply', 'den_const': 21000000},
    normalizer={'type': 'identity'},
    notes='V3 apply_dynamic: circulating_supply/21_000_000*100.',
)

_c('fart.holders.lp.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='stage1_evidence',
    request_key='stage1.fart.top20_classified',
    selector={'type': 'named_record_field', 'name': 'holder_bucket_pct', 'bucket': 'lp', 'fallback_pct': 2.15},
    normalizer={'type': 'identity'},
    notes='V3 apply_stage2_meme_overlay FART_HOLDER_READ; stage1 fart-top20-classified Raydium LP 2.15%.',
)

_c('fart.holders.unattributed.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='stage1_evidence',
    request_key='stage1.fart.top20_classified',
    selector={'type': 'named_record_field', 'name': 'holder_bucket_pct', 'bucket': 'unattributed', 'fallback_pct': 33.23},
    normalizer={'type': 'identity'},
    notes='V3 apply_stage2_meme_overlay FART_HOLDER_READ; stage1 fart-top20-classified unattributed top-20 33.23%.',
)

_c('fart.holders.unit_treasury.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='stage1_evidence',
    request_key='stage1.fart.top20_classified',
    selector={'type': 'named_record_field', 'name': 'holder_bucket_pct', 'bucket': 'unit_treasury', 'fallback_pct': 9.77},
    normalizer={'type': 'identity'},
    notes='V3 apply_stage2_meme_overlay FART_HOLDER_READ; stage1 fart-top20-classified Unit/Hyperunit treasury 9.77%.',
)

_c('fart.leverage.perp_spot_notional.x',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.ticker24h.FARTCOINUSDT',
    selector={'type': 'named_record_field', 'name': 'perp_vs_coinbase_spot_ratio', 'perp_pointer': '/quoteVolume', 'spot_request_key': 'coinbase.spot.stats.FARTCOIN-USD', 'spot_pointer': '/volume_30day'},
    normalizer={'type': 'identity'},
    notes='V3 fartcoin_stage1_loader leverage.perp_vs_coinbase_spot_ratio.',
)

_c('fart.liquidity.dex.usd.current',
    disposition='COLLECT',
    derivation=None,
    source_key='dexscreener',
    request_key='dexscreener.token.fartcoin',
    selector={'type': 'named_record_field', 'name': 'dex_highest_liquidity_usd', 'chain_id': 'solana', 'base_token_address': '9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump'},
    normalizer={'type': 'identity'},
    notes='V3 fartcoin_stage1_loader spot_liquidity.top_pool_liq_usd; Raydium top pool.',
)

_c('fart.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.klines.FARTCOINUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 200, 'venue': 'perp'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES fart→perp FARTCOINUSDT; SMA200 USD.',
)

_c('fart.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.klines.FARTCOINUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 50, 'venue': 'perp'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES fart→perp FARTCOINUSDT; SMA50 USD.',
)

_c('fart.price.usd.report',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'fartcoin'}, 'field': 'current_price'},
    normalizer={'type': 'identity'},
    notes='V3 collect_prices / stage1 price_structure.now_usd via CG markets fartcoin.',
)

_c('fart.rs.vs_sol.pp.7d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.klines.FARTCOINUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_rs_pct', 'window_days': 7, 'bench_request_key': 'binance.fapi.klines.SOLUSDT.1d'},
    normalizer={'type': 'identity'},
    notes='V3 rs.py ratio_change_pct; FARTCOINUSDT vs SOLUSDT 7d daily closes (perp).',
)

_c('fart.supply.circulating.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'ratio_pct', 'records_pointer': '/', 'identity': {'id': 'fartcoin'}, 'num_field': 'circulating_supply', 'den_field': 'max_supply'},
    normalizer={'type': 'identity'},
    notes='V3 stage1 supply.circulating_pct_of_max from CG circ/max for fartcoin.',
)

_c('giga.price.usd.live',
    disposition='COLLECT',
    derivation=None,
    source_key='dexscreener',
    request_key='dexscreener.token.giga',
    selector={'type': 'named_record_field', 'name': 'dex_live_price_highest_liquidity'},
    normalizer={'type': 'identity'},
    notes='index-v4.html dex:63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9 highest-liquidity priceUsd.',
)

_c('global.participation.above_50dma.count',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'participation_above_50d_n', 'universe': 'breadth_universe', 'charts_request_key': 'coingecko.market_charts.breadth_bundle'},
    normalizer={'type': 'integer'},
    notes='V3 collect_participation above_50d_n; breadth_universe 21-coin CG market_chart 50DMA.',
)

_c('global.participation.beat_btc.count',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'participation_beat_btc_n', 'universe': 'breadth_universe', 'window_days': 30},
    normalizer={'type': 'integer'},
    notes='V3 collect_participation beat_btc_n; CG markets 30d vs bitcoin.',
)

_c('hype.af.buys.usd.30d',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.summary.fees.hyperliquid.dailyHoldersRevenue',
    selector={'type': 'json_key', 'key': 'total30d'},
    normalizer={'type': 'identity'},
    notes='CGPT Job 2B: DefiLlama protocol summary hyperliquid dailyHoldersRevenue total30d.',
)

_c('hype.af.inventory.share_hl_circ.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.tokenDetails',
    selector={'type': 'named_record_field', 'name': 'ratio_pct', 'num_key': 'af_inventory', 'den_key': 'circulatingSupply', 'address': '0xfefefefefefefefefefefefefefefefefefefefe'},
    normalizer={'type': 'identity'},
    notes='V3 hype_stage1_loader af_inventory/circulatingSupply*100 from tokenDetails NCU 0xfefe.',
)

_c('hype.af.inventory.tokens.current',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.tokenDetails',
    selector={'type': 'named_record_field', 'name': 'ncu_balance', 'address': '0xfefefefefefefefefefefefefefefefefefefefe'},
    normalizer={'type': 'identity'},
    notes='V3 asset_live collect_hype_live AF_ADDR on tokenDetails.nonCirculatingUserBalances.',
)

_c('hype.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.klines.HYPEUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 200, 'venue': 'perp'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES hype→perp HYPEUSDT; SMA200 USD.',
)

_c('hype.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.klines.HYPEUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 50, 'venue': 'perp'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES hype→perp HYPEUSDT; SMA50 USD.',
)

_c('hype.oi.binance.usd.current',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.openInterest.HYPEUSDT',
    selector={'type': 'named_record_field', 'name': 'open_interest_usd', 'oi_pointer': '/openInterest', 'mark_request_key': 'binance.fapi.ticker24h.HYPEUSDT', 'mark_pointer': '/lastPrice'},
    normalizer={'type': 'identity'},
    notes='CGPT Job 2B: V3 hype_stage1_loader leverage.binance_oi_usd despite Job 1 CoinGecko URL.',
)

_c('hype.oi.native.usd.current',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.metaAndAssetCtxs',
    selector={'type': 'named_record_field', 'name': 'hl_asset_row_field', 'asset': 'HYPE', 'field': 'oi_usd'},
    normalizer={'type': 'identity'},
    notes='V3 hype_stage1_loader leverage.hype_token_oi_usd from metaAndAssetCtxs HYPE row.',
)

_c('hype.oi.platform.usd.current',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.metaAndAssetCtxs',
    selector={'type': 'named_record_field', 'name': 'hl_platform_open_interest_usd'},
    normalizer={'type': 'identity'},
    notes='V3 hype_stage1_loader leverage.platform_oi_usd; platform open_interest_mark_usd.',
)

_c('hype.oi.token.usd.current',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.metaAndAssetCtxs',
    selector={'type': 'named_record_field', 'name': 'hl_asset_row_field', 'asset': 'HYPE', 'field': 'oi_usd'},
    normalizer={'type': 'identity'},
    notes='V3 hype_stage1_loader leverage.hype_token_oi_usd from metaAndAssetCtxs HYPE row.',
)

_c('hype.price.usd.report',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'hyperliquid'}, 'field': 'current_price'},
    normalizer={'type': 'identity'},
    notes='V3 collect_prices / stage1 price_structure.now_usd via CG markets hyperliquid.',
)

_c('hype.stake.tokens.current',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.validatorSummaries',
    selector={'type': 'named_record_field', 'name': 'hl_total_stake_hype'},
    normalizer={'type': 'identity'},
    notes='V3 hype_stage1_loader staking.total_stake_hype from validatorSummaries.',
)

_c('hype.supply.circulating.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.tokenDetails',
    selector={'type': 'named_record_field', 'name': 'ratio_pct', 'num_key': 'circulatingSupply', 'den_key': 'maxSupply'},
    normalizer={'type': 'identity'},
    notes='V3 hype conflict preserved: HL circulatingSupply/maxSupply*100.',
)

_c('hype.supply.max.tokens',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.tokenDetails',
    selector={'type': 'json_key', 'key': 'maxSupply'},
    normalizer={'type': 'identity'},
    notes='V3 asset_live collect_hype_live tokenDetails maxSupply.',
)

_c('hype.volume.l1_perp.usd.24h',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.metaAndAssetCtxs',
    selector={'type': 'named_record_field', 'name': 'hl_platform_day_notional_volume_usd'},
    normalizer={'type': 'identity'},
    notes='V3 hype_stage1_loader hl_perp_market_snapshot day_notional_volume_usd.',
)

_c('hype.volume.token.usd.24h',
    disposition='COLLECT',
    derivation=None,
    source_key='hyperliquid',
    request_key='hyperliquid.info.metaAndAssetCtxs',
    selector={'type': 'named_record_field', 'name': 'hl_asset_row_field', 'asset': 'HYPE', 'field': 'dayNtlVlm'},
    normalizer={'type': 'identity'},
    notes='V3 hype_stage1_loader leverage.hype_token_day_notional_usd.',
)

_c('io.devices.inventory.count',
    disposition='COLLECT',
    derivation=None,
    source_key='io_explorer',
    request_key='io.inventory',
    selector={'type': 'json_pointer', 'pointer': '/data/total'},
    normalizer={'type': 'integer'},
    notes='V3 io_stage1_loader inventory_total from network/inventory-aggregated.',
)

_c('io.leverage.x.current',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.ticker24h.IOUSDT',
    selector={'type': 'named_record_field', 'name': 'perp_spot_ratio', 'perp_pointer': '/quoteVolume', 'spot_request_key': 'binance.spot.ticker24h.IOUSDT', 'spot_pointer': '/quoteVolume'},
    normalizer={'type': 'identity'},
    notes='V3 feeds_live _binance_lev perp/spot 24h quote ratio for IOUSDT.',
)

_c('io.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.IOUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 200, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES io→spot IOUSDT; SMA200 USD.',
)

_c('io.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.IOUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 50, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES io→spot IOUSDT; SMA50 USD.',
)

_c('io.oi.usd.current',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.openInterest.IOUSDT',
    selector={'type': 'named_record_field', 'name': 'open_interest_usd', 'oi_pointer': '/openInterest', 'mark_request_key': 'binance.fapi.ticker24h.IOUSDT', 'mark_pointer': '/lastPrice'},
    normalizer={'type': 'identity'},
    notes='Binance USDT-M openInterest × mark for IOUSDT.',
)

_c('io.price.drawdown_from_ath.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'io'}, 'field': 'ath_change_percentage'},
    normalizer={'type': 'identity'},
    notes='V3 AUTOJOB01 CoinGecko markets id=io field=ath_change_percentage.',
)

_c('io.price.usd.report',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'io'}, 'field': 'current_price'},
    normalizer={'type': 'identity'},
    notes='V3 collect_prices / stage1 price_structure.now_usd via CG markets io.',
)

_c('io.revenue.usd_per_day.mean_30d',
    disposition='COLLECT',
    derivation=None,
    source_key='io_explorer',
    request_key='io.total_earnings_summary',
    selector={'type': 'named_record_field', 'name': 'earnings_mean_last_n', 'n': 30},
    normalizer={'type': 'identity'},
    notes='V3 feeds_live _io_earnings avg_30d from total-earnings-summary daily_earnings.',
)

_c('io.rs.vs_sol.pp.30d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.IOUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_rs_pct', 'window_days': 30, 'bench_request_key': 'binance.spot.klines.SOLUSDT.1d'},
    normalizer={'type': 'identity'},
    notes='V3 rs.py ratio_change_pct; IOUSDT vs SOLUSDT 30d daily closes (spot).',
)

_c('io.rs.vs_sol.pp.7d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.IOUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_rs_pct', 'window_days': 7, 'bench_request_key': 'binance.spot.klines.SOLUSDT.1d'},
    normalizer={'type': 'identity'},
    notes='V3 rs.py ratio_change_pct; IOUSDT vs SOLUSDT 7d daily closes (spot).',
)

_c('io.supply.circulating.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'ratio_pct', 'records_pointer': '/', 'identity': {'id': 'io'}, 'num_field': 'circulating_supply', 'den_field': 'max_supply'},
    normalizer={'type': 'identity'},
    notes='V3 stage1 supply.circulating_pct_of_max from CG circ/max for io.',
)

_c('io.supply.circulating.tokens',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'io'}, 'field': 'circulating_supply'},
    normalizer={'type': 'identity'},
    notes='V3 AUTOJOB01 CoinGecko markets id=io field=circulating_supply.',
)

_c('io.supply.max.tokens',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'io'}, 'field': 'max_supply'},
    normalizer={'type': 'identity'},
    notes='V3 io_stage1_loader supply.max_supply 800M design via CG max_supply.',
)

_c('lockin.price.usd.live',
    disposition='COLLECT',
    derivation=None,
    source_key='dexscreener',
    request_key='dexscreener.token.lockin',
    selector={'type': 'named_record_field', 'name': 'dex_live_price_highest_liquidity'},
    normalizer={'type': 'identity'},
    notes='index-v4.html dex:8Ki8DpuWNxu9VsS3kQbarsCWMcFGWkzzA8pUPto9zBd5 highest-liquidity priceUsd.',
)

_c('nos.gpu_hours.approx_31d',
    disposition='COLLECT',
    derivation=None,
    source_key='nosana',
    request_key='nosana.jobs.timestamps_hours',
    selector={'type': 'json_key', 'key': 'total'},
    normalizer={'type': 'identity'},
    notes='V3 nos_stage1_loader network.gpu_hours_window_total from stats endpoint.',
)

_c('nos.host_rewards.usd.cumulative',
    disposition='COLLECT',
    derivation=None,
    source_key='nosana',
    request_key='nosana.jobs.stats',
    selector={'type': 'json_pointer', 'pointer': '/usdReward'},
    normalizer={'type': 'identity'},
    notes='V3 nos_stage1_loader network.jobs_stats_usd_reward_cum.',
)

_c('nos.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.market_chart.nosana',
    selector={'type': 'named_record_field', 'name': 'market_chart_sma', 'window_days': 200, 'venue': 'coingecko'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES nos→coingecko nosana; SMA200 USD.',
)

_c('nos.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.market_chart.nosana',
    selector={'type': 'named_record_field', 'name': 'market_chart_sma', 'window_days': 50, 'venue': 'coingecko'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES nos→coingecko nosana; SMA50 USD.',
)

_c('nos.price.usd.report',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'nosana'}, 'field': 'current_price'},
    normalizer={'type': 'identity'},
    notes='V3 collect_prices / stage1 price_structure.now_usd via CG markets nosana.',
)

_c('nos.return.pct.180d',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.market_chart.nosana',
    selector={'type': 'named_record_field', 'name': 'market_chart_return_pct', 'window_days': 180},
    normalizer={'type': 'identity'},
    notes='V3 nos_stage1_loader price_structure.returns_pct.180 from CG daily.',
)

_c('nos.rs.vs_sol.pp.30d',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.market_chart.nosana',
    selector={'type': 'named_record_field', 'name': 'market_chart_rs_pct', 'window_days': 30, 'bench_request_key': 'binance.spot.klines.SOLUSDT.1d'},
    normalizer={'type': 'identity'},
    notes='V3 nos_stage1_loader RS vs SOL 30d; NOS CG daily, bench SOL Binance spot.',
)

_c('nos.rs.vs_sol.pp.7d',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.market_chart.nosana',
    selector={'type': 'named_record_field', 'name': 'market_chart_rs_pct', 'window_days': 7, 'bench_request_key': 'binance.spot.klines.SOLUSDT.1d'},
    normalizer={'type': 'identity'},
    notes='V3 nos_stage1_loader RS vs SOL 7d; NOS CG daily, bench SOL Binance spot.',
)

_c('nos.stake.ratio.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='nosana',
    request_key='nosana.stats',
    selector={'type': 'named_record_field', 'name': 'staked_pct_of_max', 'staked_key': 'nosStaked', 'max_supply': 100000000},
    normalizer={'type': 'identity'},
    notes='V3 feeds_live _nos_indexer staked_pct nosStaked/100M*100.',
)

_c('nos.stake.tokens.current',
    disposition='COLLECT',
    derivation=None,
    source_key='nosana',
    request_key='nosana.stats',
    selector={'type': 'json_key', 'key': 'nosStaked'},
    normalizer={'type': 'identity'},
    notes='V3 nos_stage1_loader supply.nos_staked from stats nosStaked.',
)

_c('nos.supply.circulating.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'ratio_pct', 'records_pointer': '/', 'identity': {'id': 'nosana'}, 'num_field': 'circulating_supply', 'den_field': 'max_supply'},
    normalizer={'type': 'identity'},
    notes='V3 stage1 supply.circulating_pct_of_max from CG circ/max for nosana.',
)

_c('orca.price.usd.live',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.tickerPrice.ORCAUSDT',
    selector={'type': 'json_pointer', 'pointer': '/price'},
    normalizer={'type': 'identity'},
    notes='index-v4.html data-feed spot:ORCAUSDT; Binance spot ticker price.',
)

_c('pump.buyback.usd.1d',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.summary.fees.pump.fun.dailyHoldersRevenue',
    selector={'type': 'json_key', 'key': 'total24h'},
    normalizer={'type': 'identity'},
    notes='V3 pump_platform_health buyback_burn.total_24h_usd.',
)

_c('pump.buyback.usd_per_day.current',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.summary.fees.pump.fun.dailyHoldersRevenue',
    selector={'type': 'json_key', 'key': 'total24h'},
    normalizer={'type': 'identity'},
    notes='V3 pump_platform_health dailyHoldersRevenue total24h.',
)

_c('pump.fees.usd_per_day.current',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.summary.fees.pump.fun.dailyFees',
    selector={'type': 'json_key', 'key': 'total24h'},
    normalizer={'type': 'identity'},
    notes='V3 pump_platform_health via _llama_fees fees_1d.',
)

_c('pump.holders.unattributed.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='forensics',
    request_key='forensics.pump.ownership_vesting',
    selector={'type': 'named_record_field', 'name': 'unattributed_still_held_top_pct'},
    normalizer={'type': 'identity'},
    notes='V3 pump_forensics_loader ownership unattributed_still_held_top pct.',
)

_c('pump.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.PUMPUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 200, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES pump→spot PUMPUSDT; SMA200 USD.',
)

_c('pump.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.PUMPUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 50, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES pump→spot PUMPUSDT; SMA50 USD.',
)

_c('pump.price.usd.report',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'pump-fun'}, 'field': 'current_price'},
    normalizer={'type': 'identity'},
    notes='V3 collect_prices / stage1 price_structure.now_usd via CG markets pump-fun.',
)

_c('pump.revenue.usd_per_day.current',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.summary.fees.pump.fun.dailyRevenue',
    selector={'type': 'json_key', 'key': 'total24h'},
    normalizer={'type': 'identity'},
    notes='V3 pump_platform_health revenue.total_24h_usd.',
)

_c('pump.supply.circulating.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'pump_circulating_pct_of_max', 'identity': {'id': 'pump-fun'}, 'solana_supply_request_key': 'solana.rpc.getTokenSupply.pump'},
    normalizer={'type': 'identity'},
    notes='V3 pump_stage1_evidence circulating_pct_of_max; CG + Solana RPC cross-check.',
)

_c('render.bme.emissions.tokens.last8',
    disposition='COLLECT',
    derivation=None,
    source_key='render_foundation',
    request_key='render.liabilityEpochs',
    selector={'type': 'named_record_field', 'name': 'bme_emit_last_n', 'n': 8, 'channel': 'node_operator'},
    normalizer={'type': 'identity'},
    notes='V3 render_stage1_loader bme.last8.node_emissions from liabilityEpochs.',
)

_c('render.bme.node_due.tokens.per_epoch',
    disposition='COLLECT',
    derivation=None,
    source_key='render_foundation',
    request_key='render.liabilityEpochs',
    selector={'type': 'named_record_field', 'name': 'render_liability_node_due_latest', 'channel': 'node_operator'},
    normalizer={'type': 'identity'},
    notes='Render Foundation dashboard liabilityEpochs latest node_operator amountDue per epoch.',
)

_c('render.bme.ratio.last4',
    disposition='COLLECT',
    derivation=None,
    source_key='render_foundation',
    request_key='render.epochBurnStats',
    selector={'type': 'named_record_field', 'name': 'bme_burn_emit_ratio_last_n', 'n': 4, 'liability_request_key': 'render.liabilityEpochs'},
    normalizer={'type': 'identity'},
    notes='V3 render_stage1_loader bme.last4.ratio; burn epochBurnStats + emit liabilityEpochs.',
)

_c('render.bme.ratio.last8',
    disposition='COLLECT',
    derivation=None,
    source_key='render_foundation',
    request_key='render.epochBurnStats',
    selector={'type': 'named_record_field', 'name': 'bme_burn_emit_ratio_last_n', 'n': 8, 'liability_request_key': 'render.liabilityEpochs'},
    normalizer={'type': 'identity'},
    notes='V3 render_stage1_loader bme.last8.ratio; burn epochBurnStats + emit liabilityEpochs.',
)

_c('render.emissions.tokens.remaining',
    disposition='COLLECT',
    derivation=None,
    source_key='render_foundation',
    request_key='render.supplyInfo',
    selector={'type': 'json_key', 'key': 'leftoverEmissions'},
    normalizer={'type': 'identity'},
    notes='CGPT Job 2B: Render Foundation dashboard supplyInfo leftoverEmissions.',
)

_c('render.leverage.x.current',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.ticker24h.RENDERUSDT',
    selector={'type': 'named_record_field', 'name': 'perp_spot_ratio', 'perp_pointer': '/quoteVolume', 'spot_request_key': 'binance.spot.ticker24h.RENDERUSDT', 'spot_pointer': '/quoteVolume'},
    normalizer={'type': 'identity'},
    notes='V3 feeds_live _binance_lev perp/spot 24h quote ratio for RENDERUSDT.',
)

_c('render.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.RENDERUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 200, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES render→spot RENDERUSDT; SMA200 USD.',
)

_c('render.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.RENDERUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 50, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES render→spot RENDERUSDT; SMA50 USD.',
)

_c('render.price.usd.report',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'render-token'}, 'field': 'current_price'},
    normalizer={'type': 'identity'},
    notes='V3 collect_prices / stage1 price_structure.now_usd via CG markets render-token.',
)

_c('retardio.price.usd.live',
    disposition='COLLECT',
    derivation=None,
    source_key='dexscreener',
    request_key='dexscreener.token.retardio',
    selector={'type': 'named_record_field', 'name': 'dex_live_price_highest_liquidity'},
    normalizer={'type': 'identity'},
    notes='index-v4.html dex:6ogzHhzdrQr9Pgv6hZ2MNze7UrzBMAFyBBWUYp1Fhitx highest-liquidity priceUsd.',
)

_c('sol.burn.tokens.per_year',
    disposition='COLLECT',
    derivation=None,
    source_key='solana_rpc',
    request_key='solana.rpc.getInflationRate',
    selector={'type': 'named_record_field', 'name': 'sol_burn_tokens_per_year'},
    normalizer={'type': 'identity'},
    notes='V3 sol_intel staking_inflation_burn estimated burn tokens/yr.',
)

_c('sol.dex_eth_ratio.7d.x',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.overview.dexs.solana',
    selector={'type': 'named_record_field', 'name': 'dex_chain_ratio', 'numerator_field': 'total7d', 'den_request_key': 'defillama.overview.dexs.ethereum', 'den_field': 'total7d'},
    normalizer={'type': 'identity'},
    notes='V3 feeds_live _llama_dex_ratio ratio_7d.',
)

_c('sol.dex_eth_ratio.latest_day.x',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.overview.dexs.solana',
    selector={'type': 'named_record_field', 'name': 'dex_chain_ratio', 'numerator_field': 'total24h', 'den_request_key': 'defillama.overview.dexs.ethereum', 'den_field': 'total24h'},
    normalizer={'type': 'identity'},
    notes='V3 feeds_live _llama_dex_ratio ratio_24h.',
)

_c('sol.dex_eth_ratio.x.current',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.overview.dexs.solana',
    selector={'type': 'named_record_field', 'name': 'dex_chain_ratio', 'numerator_field': 'total24h', 'den_request_key': 'defillama.overview.dexs.ethereum', 'den_field': 'total24h'},
    normalizer={'type': 'identity'},
    notes='V3 feeds_live _llama_dex_ratio ratio_24h.',
)

_c('sol.fees.usd_per_day.current',
    disposition='COLLECT',
    derivation=None,
    source_key='defillama',
    request_key='defillama.summary.fees.solana.dailyFees',
    selector={'type': 'json_key', 'key': 'total24h'},
    normalizer={'type': 'identity'},
    notes='V3 feeds_live _llama_fees + collect sol.fees total24h.',
)

_c('sol.funding.rate.mean_7d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.fundingRate.SOLUSDT',
    selector={'type': 'named_record_field', 'name': 'funding_rate_mean_last_n', 'n': 7},
    normalizer={'type': 'decimal_as_percent'},
    notes='V3 sol_intel funding 7d mean from Binance fundingRate history.',
)

_c('sol.issuance.tokens.per_year',
    disposition='COLLECT',
    derivation=None,
    source_key='solana_rpc',
    request_key='solana.rpc.getInflationRate',
    selector={'type': 'named_record_field', 'name': 'sol_issuance_tokens_per_year'},
    normalizer={'type': 'identity'},
    notes='lib/supporting_feeds.py fetch_solana_network issuance_yr.',
)

_c('sol.leverage.x.current',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.ticker24h.SOLUSDT',
    selector={'type': 'named_record_field', 'name': 'perp_spot_ratio', 'perp_pointer': '/quoteVolume', 'spot_request_key': 'binance.spot.ticker24h.SOLUSDT', 'spot_pointer': '/quoteVolume'},
    normalizer={'type': 'identity'},
    notes='V3 feeds_live _binance_lev perp/spot 24h quote ratio for SOLUSDT.',
)

_c('sol.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.SOLUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 200, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES sol→spot SOLUSDT; SMA200 USD.',
)

_c('sol.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.SOLUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 50, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES sol→spot SOLUSDT; SMA50 USD.',
)

_c('sol.price.usd.report',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'solana'}, 'field': 'current_price'},
    normalizer={'type': 'identity'},
    notes='V3 collect_prices / stage1 price_structure.now_usd via CG markets solana.',
)

_c('sol.stake.ratio.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='solana_rpc',
    request_key='solana.rpc.getVoteAccounts',
    selector={'type': 'named_record_field', 'name': 'stake_ratio_pct'},
    normalizer={'type': 'identity'},
    notes='lib/supporting_feeds.py fetch_solana_network stake_pct.',
)

_c('sol.staking.apy.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='external_sample',
    request_key='external_sample.sol_staking_apy',
    selector={'type': 'named_record_field', 'name': 'sample_band_midpoint', 'low': 4.65, 'high': 5.8},
    normalizer={'type': 'identity'},
    notes='WEAK SPEC: V3 sol_product cites liquid-staking APY sample band only — no pinned live APY endpoint.',
)

_c('sol.supply.circulating.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='solana_rpc',
    request_key='solana.rpc.getSupply',
    selector={'type': 'named_record_field', 'name': 'supply_circulating_pct'},
    normalizer={'type': 'identity'},
    notes='lib/supporting_feeds.py getSupply circulating/total*100.',
)

_c('sol.supply.net_change.tokens.per_year',
    disposition='DERIVE',
    source_key=None,
    request_key=None,
    selector=None,
    normalizer={'type': 'identity'},
    derivation={'op': 'SUBTRACT', 'inputs': ['sol.issuance.tokens.per_year', 'sol.burn.tokens.per_year'], 'calculation_version': 'v1'},
    notes='V3 sol_intel net issuance - burn SOL/yr.',
)

_c('sol.tps.all.current',
    disposition='COLLECT',
    derivation=None,
    source_key='solana_rpc',
    request_key='solana.rpc.getRecentPerformanceSamples',
    selector={'type': 'named_record_field', 'name': 'perf_tps_all'},
    normalizer={'type': 'identity'},
    notes='V3 sol_intel activity.tps_all_mean_20samples.',
)

_c('spx.holders.top20.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='solana_rpc',
    request_key='solana.rpc.getTokenLargestAccounts.spx',
    selector={'type': 'named_record_field', 'name': 'solana_top20_pct_of_mint', 'mint': 'J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr', 'solana_supply_request_key': 'solana.rpc.getTokenSupply.spx'},
    normalizer={'type': 'identity'},
    notes='V3 spx_stage1_loader holders.solana_top20_pct_of_sol_mint.',
)

_c('spx.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.klines.SPXUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 200, 'venue': 'perp'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES spx→perp SPXUSDT; SMA200 USD.',
)

_c('spx.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.klines.SPXUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 50, 'venue': 'perp'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES spx→perp SPXUSDT; SMA50 USD.',
)

_c('spx.oi.change.pct.30d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.openInterestHist.SPXUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'open_interest_change_pct', 'window': 30},
    normalizer={'type': 'identity'},
    notes='Binance openInterestHist sumOpenInterestValue Δ30d for SPXUSDT.',
)

_c('spx.price.usd.report',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'spx6900'}, 'field': 'current_price'},
    normalizer={'type': 'identity'},
    notes='V3 collect_prices / stage1 price_structure.now_usd via CG markets spx6900.',
)

_c('spx.return.pct.30d',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'spx6900'}, 'field': 'price_change_percentage_30d_in_currency'},
    normalizer={'type': 'identity'},
    notes='V3 AUTOJOB01 CoinGecko markets id=spx6900 field=price_change_percentage_30d_in_currency.',
)

_c('spx.supply.circulating.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'ratio_pct', 'records_pointer': '/', 'identity': {'id': 'spx6900'}, 'num_field': 'circulating_supply', 'den_field': 'max_supply'},
    normalizer={'type': 'identity'},
    notes='V3 stage1 supply.circulating_pct_of_max from CG circ/max for spx6900.',
)

_c('spx.volume.perp.usd.24h',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.fapi.ticker24h.SPXUSDT',
    selector={'type': 'json_pointer', 'pointer': '/quoteVolume'},
    normalizer={'type': 'identity'},
    notes='CGPT Job 2B: Binance perp SPXUSDT quoteVolume despite Job 1 CoinGecko URL.',
)

_c('zec.inflation.pct.current',
    disposition='COLLECT',
    derivation=None,
    source_key='zcash_explorer',
    request_key='zcash.explorer.blockchain-info',
    selector={'type': 'named_record_field', 'name': 'estimated_annual_inflation_pct'},
    normalizer={'type': 'identity'},
    notes='V3 zec_stage1_loader supply.estimated_annual_inflation_pct.',
)

_c('zec.ma.usd.200d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.ZECUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 200, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES zec→spot ZECUSDT; SMA200 USD.',
)

_c('zec.ma.usd.50d',
    disposition='COLLECT',
    derivation=None,
    source_key='binance',
    request_key='binance.spot.klines.ZECUSDT.1d',
    selector={'type': 'named_record_field', 'name': 'klines_sma', 'window_days': 50, 'venue': 'spot'},
    normalizer={'type': 'identity'},
    notes='V3 sma_trend VENUES zec→spot ZECUSDT; SMA50 USD.',
)

_c('zec.price.usd.report',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'zcash'}, 'field': 'current_price'},
    normalizer={'type': 'identity'},
    notes='V3 collect_prices / stage1 price_structure.now_usd via CG markets zcash.',
)

_c('zec.shielded.share.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='zcash_explorer',
    request_key='zcash.explorer.blockchain-info',
    selector={'type': 'named_record_field', 'name': 'shielded_pct_of_chain', 'pool_ids': ['sprout', 'sapling', 'orchard', 'ironwood']},
    normalizer={'type': 'identity'},
    notes='V3 zec_stage1_loader monetary.shielded_pct_of_chain from valuePools.',
)

_c('zec.supply.circulating.pct',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'name': 'ratio_pct', 'records_pointer': '/', 'identity': {'id': 'zcash'}, 'num_field': 'circulating_supply', 'den_field': 'max_supply'},
    normalizer={'type': 'identity'},
    notes='V3 stage1 supply.circulating_pct_of_max from CG circ/max for zcash.',
)

_c('zec.supply.circulating.tokens',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'zcash'}, 'field': 'circulating_supply'},
    normalizer={'type': 'identity'},
    notes='V3 AUTOJOB01 CoinGecko markets id=zcash field=circulating_supply.',
)

_c('zec.supply.max.tokens',
    disposition='COLLECT',
    derivation=None,
    source_key='coingecko',
    request_key='coingecko.markets.active',
    selector={'type': 'named_record_field', 'records_pointer': '/', 'identity': {'id': 'zcash'}, 'field': 'max_supply'},
    normalizer={'type': 'identity'},
    notes='V3 zec_stage1_loader supply.max_supply 21M via CG.',
)


EXCLUDED_FROM_PHASE_B = frozenset({
    "io.emissions.tokens.remaining",  # PRESERVE in apply script
    "drift.price.usd.live",  # INACTIVE
})

PHASE_B_METRIC_COUNT = 115

WEAK_OR_PARTIAL_SPECS = [
    "sol.staking.apy.pct",
]

NEW_REQUEST_KEYS = [
    "binance.fapi.fundingRate.SOLUSDT",
    "binance.fapi.klines.FARTCOINUSDT.1d",
    "binance.fapi.klines.HYPEUSDT.1d",
    "binance.fapi.klines.SOLUSDT.1d",
    "binance.fapi.klines.SPXUSDT.1d",
    "binance.fapi.openInterest.HYPEUSDT",
    "binance.fapi.openInterest.IOUSDT",
    "binance.fapi.openInterestHist.BTCUSDT.1d",
    "binance.fapi.openInterestHist.SPXUSDT.1d",
    "binance.fapi.ticker24h.FARTCOINUSDT",
    "binance.fapi.ticker24h.HYPEUSDT",
    "binance.fapi.ticker24h.IOUSDT",
    "binance.fapi.ticker24h.RENDERUSDT",
    "binance.fapi.ticker24h.SOLUSDT",
    "binance.fapi.ticker24h.SPXUSDT",
    "binance.spot.klines.IOUSDT.1d",
    "binance.spot.klines.RENDERUSDT.1d",
    "binance.spot.klines.ZECUSDT.1d",
    "binance.spot.ticker24h.IOUSDT",
    "binance.spot.ticker24h.RENDERUSDT",
    "binance.spot.ticker24h.SOLUSDT",
    "binance.spot.tickerPrice.BONKUSDT",
    "binance.spot.tickerPrice.ORCAUSDT",
    "coinbase.spot.stats.FARTCOIN-USD",
    "coingecko.market_chart.nosana",
    "defillama.overview.dexs.ethereum",
    "defillama.stablecoincharts.all",
    "dexscreener.token.2z",
    "dexscreener.token.fartcoin",
    "dexscreener.token.giga",
    "dexscreener.token.lockin",
    "dexscreener.token.retardio",
    "external_sample.sol_staking_apy",
    "forensics.pump.ownership_vesting",
    "hyperliquid.info.metaAndAssetCtxs",
    "hyperliquid.info.validatorSummaries",
    "io.inventory",
    "io.total_earnings_summary",
    "nosana.jobs.stats",
    "nosana.stats",
    "render.dashboard.main",
    "render.liabilityEpochs",
    "solana.rpc.getSupply",
    "solana.rpc.getTokenLargestAccounts.spx",
    "solana.rpc.getTokenSupply.pump",
    "stage1.fart.top20_classified",
]

