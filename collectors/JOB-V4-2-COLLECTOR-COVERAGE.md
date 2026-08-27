# JOB V4-2 Collector Coverage

| metric_id | disposition | source_key | required | request_key | notes |
|---|---|---|---|---|
| 2z.price.usd.live | COLLECT | dexscreener | True | dexscreener.token.2z | index-v4.html dex:J6pQQ3FAcJQeWPPGppWRb4nM8jU3wLyYbRrLh7feMfvd highest-liquidity |
| 2z.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| 2z.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| 2z.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| 2z.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| bonk.price.usd.live | COLLECT | binance | True | binance.spot.tickerPrice.BONKUSDT | index-v4.html data-feed spot:BONKUSDT; Binance spot ticker price. |
| bonk.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| bonk.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| bonk.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| bonk.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| btc.etf.flow.usd.1d | COLLECT | farside | True | farside.html.btc | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions |
| btc.etf.flow.usd.2026_08_03_07 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| btc.etf.flow.usd.2026_08_10 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| btc.etf.flow.usd.2026_08_11 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| btc.etf.flow.usd.30d | COLLECT | farside | True | farside.html.btc | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions |
| btc.etf.flow.usd.7d | COLLECT | farside | True | farside.html.btc | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions |
| btc.etf.flow.usd.all_time | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| btc.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.BTCUSDT | Job 1 names Binance; official futures/spot JSON API. |
| btc.inflation.pct.current | COLLECT | coingecko | True | coingecko.markets.active | V3 apply_dynamic btc_body: 3.125*144*365/circulating*100 from CG bitcoin circula |
| btc.leverage.x.current | DERIVE | — | True | {'op': 'RATIO', 'inputs': ['btc.volume.perp.usd.24h', 'btc.volume.spot.usd.24h'], 'calculation_version': 'v1'} | V3 AUTOJOB01 BTCUSDT perp quoteVolume / spot quoteVolume. |
| btc.ma.usd.200d | COLLECT | binance | True | binance.spot.klines.BTCUSDT.1d | V3 sma_trend VENUES btc→spot BTCUSDT; SMA200 USD. |
| btc.ma.usd.50d | COLLECT | binance | True | binance.spot.klines.BTCUSDT.1d | V3 sma_trend VENUES btc→spot BTCUSDT; SMA50 USD. |
| btc.oi.btc.current | COLLECT | binance | True | binance.fapi.openInterest.BTCUSDT | Job 1 names Binance; official futures/spot JSON API. |
| btc.oi.change.pct.1d | COLLECT | binance | True | binance.fapi.openInterestHist.BTCUSDT.1d | Binance openInterestHist sumOpenInterestValue Δ1d for BTCUSDT. |
| btc.oi.change.pct.30d | COLLECT | binance | True | binance.fapi.openInterestHist.BTCUSDT.1d | Binance openInterestHist sumOpenInterestValue Δ30d for BTCUSDT. |
| btc.oi.change.pct.7d | COLLECT | binance | True | binance.fapi.openInterestHist.BTCUSDT.1d | Binance openInterestHist sumOpenInterestValue Δ7d for BTCUSDT. |
| btc.price.ath.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| btc.price.drawdown_from_ath.pct | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| btc.price.usd.july_2026_low | COLLECT | binance | True | binance.spot.klines.BTCUSDT.1d | Job 1 Binance daily; V3 re-reads July 2026 BTCUSDT daily lows. |
| btc.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| btc.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| btc.return.pct.30d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| btc.return.pct.7d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| btc.return.pct.90d | COLLECT | coingecko | True | coingecko.market_chart.bitcoin.90d | CG 90d return via market_chart; markets endpoint no longer exposes 90d field. |
| btc.stablecoin.change.pct.30d | COLLECT | defillama | True | defillama.stablecoincharts.all | lib/stablecoin_supply.py fetch_stablecoin_supply change_30d_pct. |
| btc.supply.circulating.pct | COLLECT | coingecko | True | coingecko.markets.active | V3 apply_dynamic: circulating_supply/21_000_000*100. |
| btc.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| btc.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| btc.volume.perp.usd.24h | COLLECT | binance | True | binance.fapi.ticker24h.BTCUSDT | Job 1 names Binance; official futures/spot JSON API. |
| btc.volume.spot.usd.24h | COLLECT | binance | True | binance.spot.ticker24h.BTCUSDT | Job 1 names Binance; official futures/spot JSON API. |
| drift.price.usd.live | LEGACY_INACTIVE | — | False | — | LEGACY_INACTIVE per asset-state-overrides.json (Job 2B). |
| drift.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| drift.threshold.out.usd | LEGACY_INACTIVE | — | False | — | LEGACY_INACTIVE per asset-state-overrides.json (Job 2B). |
| drift.threshold.this_move.usd | LEGACY_INACTIVE | — | False | — | LEGACY_INACTIVE per asset-state-overrides.json (Job 2B). |
| eth.etf.flow.usd.1d | COLLECT | farside | True | farside.html.eth | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions |
| eth.etf.flow.usd.30d | COLLECT | farside | True | farside.html.eth | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions |
| eth.etf.flow.usd.7d | COLLECT | farside | True | farside.html.eth | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions |
| eth.etf.flow.usd.all_time | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| fart.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.FARTCOINUSDT | Job 1 names Binance; official futures/spot JSON API. |
| fart.holders.lp.pct | COLLECT | stage1_evidence | True | stage1.fart.top20_classified | V3 apply_stage2_meme_overlay FART_HOLDER_READ; stage1 fart-top20-classified Rayd |
| fart.holders.unattributed.pct | COLLECT | stage1_evidence | True | stage1.fart.top20_classified | V3 apply_stage2_meme_overlay FART_HOLDER_READ; stage1 fart-top20-classified unat |
| fart.holders.unit_treasury.pct | COLLECT | stage1_evidence | True | stage1.fart.top20_classified | V3 apply_stage2_meme_overlay FART_HOLDER_READ; stage1 fart-top20-classified Unit |
| fart.leverage.perp_spot_notional.x | COLLECT | binance | True | binance.fapi.ticker24h.FARTCOINUSDT | V3 fartcoin_stage1_loader leverage.perp_vs_coinbase_spot_ratio. |
| fart.liquidity.dex.usd.current | COLLECT | dexscreener | True | dexscreener.token.fartcoin | V3 fartcoin_stage1_loader spot_liquidity.top_pool_liq_usd; Raydium top pool. |
| fart.ma.usd.200d | COLLECT | binance | True | binance.fapi.klines.FARTCOINUSDT.1d | V3 sma_trend VENUES fart→perp FARTCOINUSDT; SMA200 USD. |
| fart.ma.usd.50d | COLLECT | binance | True | binance.fapi.klines.FARTCOINUSDT.1d | V3 sma_trend VENUES fart→perp FARTCOINUSDT; SMA50 USD. |
| fart.market_cap.usd.current | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.oi.usd.current | COLLECT | binance | True | binance.fapi.openInterest.FARTCOINUSDT | Job 1 is USD OI; Binance openInterest is contracts. See selector identity; norma |
| fart.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| fart.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_prices / stage1 price_structure.now_usd via CG markets fartcoin. |
| fart.return.pct.30d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.return.pct.7d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.return.pct.90d | COLLECT | coingecko | True | coingecko.market_chart.fartcoin.90d | CG 90d return via market_chart. |
| fart.rs.vs_sol.pp.7d | COLLECT | binance | True | binance.fapi.klines.FARTCOINUSDT.1d | V3 rs.py ratio_change_pct; FARTCOINUSDT vs SOLUSDT 7d daily closes (perp). |
| fart.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| fart.supply.circulating.pct | COLLECT | coingecko | True | coingecko.markets.active | V3 stage1 supply.circulating_pct_of_max from CG circ/max for fartcoin. |
| fart.supply.circulating.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.supply.max.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| fart.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| fart.volume.cg.usd.24h | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.volume.perp.usd.24h | COLLECT | binance | True | binance.fapi.ticker24h.FARTCOINUSDT | Job 1 names Binance; official futures/spot JSON API. |
| giga.price.usd.live | COLLECT | dexscreener | True | dexscreener.token.giga | index-v4.html dex:63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9 highest-liquidity |
| giga.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| giga.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| giga.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| giga.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| global.fear_greed.index.current | COLLECT | alternative_me | True | alternative_me.fng | Job 1 source alternative.me; official JSON API. |
| global.leverage.x.current | DERIVE | — | True | {'op': 'RATIO', 'inputs': ['btc.volume.perp.usd.24h', 'btc.volume.spot.usd.24h'], 'calculation_version': 'v1'} | V3 market leverage uses BTCUSDT perp and spot 24h quote. |
| global.participation.above_50dma.count | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_participation above_50d_n; breadth_universe 21-coin CG market_chart 5 |
| global.participation.beat_btc.count | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_participation beat_btc_n; CG markets 30d vs bitcoin. |
| hype.af.buys.usd.30d | COLLECT | defillama | True | defillama.overview.fees.dailyHoldersRevenue | CGPT Job 2B: overview fees dailyHoldersRevenue; identity name=Hyperliquid exact; |
| hype.af.inventory.share_hl_circ.pct | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | V3 hype_stage1_loader af_inventory/circulatingSupply*100 from tokenDetails NCU 0 |
| hype.af.inventory.tokens.current | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | V3 asset_live collect_hype_live AF_ADDR on tokenDetails.nonCirculatingUserBalanc |
| hype.emissions.tokens.remaining | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | Job 1 URL api.hyperliquid.xyz/info; V3 tokenDetails futureEmissions. Identity na |
| hype.fees.change.pct.30d | COLLECT | defillama | True | defillama.summary.fees.hyperliquid.dailyFees | 30d percent change of daily fees series. |
| hype.fees.perps.usd.30d | COLLECT | defillama | True | defillama.summary.fees.hyperliquid.dailyFees | Same DefiLlama hyperliquid-perp 30d fees payload as hype.fees.usd.30d; Job 1 URL |
| hype.fees.usd.30d | COLLECT | defillama | True | defillama.summary.fees.hyperliquid.dailyFees | Job 1 URL api.llama.fi/summary/fees/hyperliquid-perp. |
| hype.ma.usd.200d | COLLECT | binance | True | binance.fapi.klines.HYPEUSDT.1d | V3 sma_trend VENUES hype→perp HYPEUSDT; SMA200 USD. |
| hype.ma.usd.50d | COLLECT | binance | True | binance.fapi.klines.HYPEUSDT.1d | V3 sma_trend VENUES hype→perp HYPEUSDT; SMA50 USD. |
| hype.ncu.hyperlabs.tokens | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | V3 HyperLabs NCU address on tokenDetails.nonCirculatingUserBalances. |
| hype.oi.binance.usd.current | COLLECT | binance | True | binance.fapi.openInterest.HYPEUSDT | CGPT Job 2B: V3 hype_stage1_loader leverage.binance_oi_usd despite Job 1 CoinGec |
| hype.oi.native.usd.current | COLLECT | hyperliquid | True | hyperliquid.info.metaAndAssetCtxs | V3 hype_stage1_loader leverage.hype_token_oi_usd from metaAndAssetCtxs HYPE row. |
| hype.oi.platform.usd.current | COLLECT | hyperliquid | True | hyperliquid.info.metaAndAssetCtxs | V3 hype_stage1_loader leverage.platform_oi_usd; platform open_interest_mark_usd. |
| hype.oi.token.usd.current | COLLECT | hyperliquid | True | hyperliquid.info.metaAndAssetCtxs | V3 hype_stage1_loader leverage.hype_token_oi_usd from metaAndAssetCtxs HYPE row. |
| hype.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| hype.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_prices / stage1 price_structure.now_usd via CG markets hyperliquid. |
| hype.return.pct.30d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| hype.return.pct.7d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| hype.stake.tokens.current | COLLECT | hyperliquid | True | hyperliquid.info.validatorSummaries | V3 hype_stage1_loader staking.total_stake_hype from validatorSummaries. |
| hype.supply.circulating.pct | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | V3 hype conflict preserved: HL circulatingSupply/maxSupply*100. |
| hype.supply.hl_circulating.pct | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | circulatingSupply/maxSupply*100 from tokenDetails. |
| hype.supply.max.tokens | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | V3 asset_live collect_hype_live tokenDetails maxSupply. |
| hype.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| hype.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| hype.volume.l1_perp.usd.24h | COLLECT | hyperliquid | True | hyperliquid.info.metaAndAssetCtxs | V3 hype_stage1_loader hl_perp_market_snapshot day_notional_volume_usd. |
| hype.volume.token.usd.24h | COLLECT | hyperliquid | True | hyperliquid.info.metaAndAssetCtxs | V3 hype_stage1_loader leverage.hype_token_day_notional_usd. |
| hype.wallet.foundation.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| io.clusters.running.count | COLLECT | io_explorer | True | io.clusters | Job 1 io.net Explorer clusters URL. |
| io.devices.inventory.count | COLLECT | io_explorer | True | io.inventory | V3 io_stage1_loader inventory_total from network/inventory-aggregated. |
| io.emissions.tokens.remaining | PRESERVE | — | False | — | Legacy pre-IDE fixed-emission tokenomics. io.net's Incentive Dynamic Engine went |
| io.leverage.x.current | COLLECT | binance | True | binance.fapi.ticker24h.IOUSDT | V3 feeds_live _binance_lev perp/spot 24h quote ratio for IOUSDT. |
| io.leverage.x.stage1 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| io.ma.usd.200d | COLLECT | binance | True | binance.spot.klines.IOUSDT.1d | V3 sma_trend VENUES io→spot IOUSDT; SMA200 USD. |
| io.ma.usd.50d | COLLECT | binance | True | binance.spot.klines.IOUSDT.1d | V3 sma_trend VENUES io→spot IOUSDT; SMA50 USD. |
| io.oi.usd.current | COLLECT | binance | True | binance.fapi.openInterest.IOUSDT | Binance USDT-M openInterest × mark for IOUSDT. |
| io.oi.usd.stage1 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| io.price.ath.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| io.price.drawdown_from_ath.pct | COLLECT | coingecko | True | coingecko.markets.active | V3 AUTOJOB01 CoinGecko markets id=io field=ath_change_percentage. |
| io.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| io.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_prices / stage1 price_structure.now_usd via CG markets io. |
| io.revenue.usd.cumulative | COLLECT | io_explorer | True | io.clusters | Job 1 clusters URL; V3 total_earnings on clusters payload. |
| io.revenue.usd.july_2026 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| io.revenue.usd.june_2026 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| io.revenue.usd.may_2026 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| io.revenue.usd_per_day.mean_30d | COLLECT | io_explorer | True | io.total_earnings_summary | V3 feeds_live _io_earnings avg_30d from total-earnings-summary daily_earnings. |
| io.rs.vs_sol.pp.30d | COLLECT | binance | True | binance.spot.klines.IOUSDT.1d | V3 rs.py ratio_change_pct; IOUSDT vs SOLUSDT 30d daily closes (spot). |
| io.rs.vs_sol.pp.7d | COLLECT | binance | True | binance.spot.klines.IOUSDT.1d | V3 rs.py ratio_change_pct; IOUSDT vs SOLUSDT 7d daily closes (spot). |
| io.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| io.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| io.siren.watched_wallet_count.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| io.supply.circulating.pct | COLLECT | coingecko | True | coingecko.markets.active | V3 stage1 supply.circulating_pct_of_max from CG circ/max for io. |
| io.supply.circulating.tokens | COLLECT | coingecko | True | coingecko.markets.active | V3 AUTOJOB01 CoinGecko markets id=io field=circulating_supply. |
| io.supply.max.tokens | COLLECT | coingecko | True | coingecko.markets.active | V3 io_stage1_loader supply.max_supply 800M design via CG max_supply. |
| io.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| io.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| lockin.price.usd.live | COLLECT | dexscreener | True | dexscreener.token.lockin | index-v4.html dex:8Ki8DpuWNxu9VsS3kQbarsCWMcFGWkzzA8pUPto9zBd5 highest-liquidity |
| lockin.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| lockin.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| lockin.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| lockin.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| nos.gpu_hours.approx_31d | COLLECT | nosana | True | nosana.jobs.timestamps_hours | V3 nos_stage1_loader network.gpu_hours_window_total from stats endpoint. |
| nos.host_rewards.usd.cumulative | COLLECT | nosana | True | nosana.jobs.stats | V3 nos_stage1_loader network.jobs_stats_usd_reward_cum. |
| nos.jobs.approx_30d.count | COLLECT | nosana | True | nosana.jobs.count | Requires last30Days on jobs/count; else SOURCE_SCHEMA_MISMATCH. |
| nos.jobs.completed.cumulative | COLLECT | nosana | True | nosana.jobs.count | Job 1 Nosana blockchain-indexer jobs/count. |
| nos.jobs.queued.count | COLLECT | nosana | True | nosana.jobs.count | Job 1 URL jobs/count. |
| nos.jobs.running.count | COLLECT | nosana | True | nosana.jobs.count | Job 1 URL jobs/count. |
| nos.ma.usd.200d | COLLECT | coingecko | True | coingecko.market_chart.nosana | V3 sma_trend VENUES nos→coingecko nosana; SMA200 USD. |
| nos.ma.usd.50d | COLLECT | coingecko | True | coingecko.market_chart.nosana | V3 sma_trend VENUES nos→coingecko nosana; SMA50 USD. |
| nos.market_cap.usd.current | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| nos.nodes.with_running_jobs.count | COLLECT | nosana | True | nosana.jobs.count | Field name must exist on jobs/count. Fail closed if renamed. |
| nos.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| nos.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_prices / stage1 price_structure.now_usd via CG markets nosana. |
| nos.return.pct.180d | COLLECT | coingecko | True | coingecko.market_chart.nosana | V3 nos_stage1_loader price_structure.returns_pct.180 from CG daily. |
| nos.rs.vs_sol.pp.30d | COLLECT | coingecko | True | coingecko.market_chart.nosana | V3 nos_stage1_loader RS vs SOL 30d; NOS CG daily, bench SOL Binance spot. |
| nos.rs.vs_sol.pp.7d | COLLECT | coingecko | True | coingecko.market_chart.nosana | V3 nos_stage1_loader RS vs SOL 7d; NOS CG daily, bench SOL Binance spot. |
| nos.siren.aug1_unknown_wallet_count.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| nos.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| nos.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| nos.siren.watched_wallet_count.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| nos.stake.ratio.pct | COLLECT | nosana | True | nosana.stats | V3 feeds_live _nos_indexer staked_pct nosStaked/100M*100. |
| nos.stake.tokens.current | COLLECT | nosana | True | nosana.stats | V3 nos_stage1_loader supply.nos_staked from stats nosStaked. |
| nos.supply.circulating.pct | COLLECT | coingecko | True | coingecko.markets.active | V3 stage1 supply.circulating_pct_of_max from CG circ/max for nosana. |
| nos.supply.circulating.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| nos.supply.max.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| nos.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| nos.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| orca.price.usd.live | COLLECT | binance | True | binance.spot.tickerPrice.ORCAUSDT | index-v4.html data-feed spot:ORCAUSDT; Binance spot ticker price. |
| orca.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| orca.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| orca.siren.watched_wallet_count.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| orca.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| orca.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| portfolio.portfolio.value.usd.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| pump.buyback.usd.1d | COLLECT | defillama | True | defillama.summary.fees.pump.fun.dailyHoldersRevenue | V3 pump_platform_health buyback_burn.total_24h_usd. |
| pump.buyback.usd.7d | COLLECT | defillama | True | defillama.summary.fees.pump.fun.dailyHoldersRevenue | V3 holdersRevenue 7d chart sum for pump.fun. |
| pump.buyback.usd_per_day.ath_sep | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.buyback.usd_per_day.current | COLLECT | defillama | True | defillama.summary.fees.pump.fun.dailyHoldersRevenue | V3 pump_platform_health dailyHoldersRevenue total24h. |
| pump.buyback.usd_per_day.jan_high | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.buyback.usd_per_day.june_atl | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.fees.usd_per_day.ath_sep | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.fees.usd_per_day.current | COLLECT | defillama | True | defillama.summary.fees.pump.fun.dailyFees | V3 pump_platform_health via _llama_fees fees_1d. |
| pump.fees.usd_per_day.jan_high | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.fees.usd_per_day.june_atl | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.PUMPUSDT | Job 1 names Binance; official futures/spot JSON API. |
| pump.holders.unattributed.pct | COLLECT | forensics | True | forensics.pump.ownership_vesting | V3 pump_forensics_loader ownership unattributed_still_held_top pct. |
| pump.leverage.x.current | COLLECT | binance | True | binance.fapi.ticker24h.PUMPUSDT | Job 1 binance futures PUMPUSDT; V3 perp/spot 24h quote ratio. |
| pump.liquidity.dex.usd.current | COLLECT | dexscreener | True | dexscreener.token.pump | Job 1 source dexscreener; V3 DexScreener pair for PUMP mint. First-pair is forbi |
| pump.ma.usd.200d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | V3 sma_trend VENUES pump→spot PUMPUSDT; SMA200 USD. |
| pump.ma.usd.50d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | V3 sma_trend VENUES pump→spot PUMPUSDT; SMA50 USD. |
| pump.market_share.pct.ath_sep | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.market_share.pct.aug_10 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.market_share.pct.current | COLLECT | defillama | True | defillama.overview.fees | V3 Launchpad category 24h fee share. |
| pump.market_share.pct.jan_high | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.market_share.pct.june_atl | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.market_share.pct.share_history | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.mm.wintermute.balance.tokens | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| pump.mm.wintermute.transfer.tokens | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| pump.oi.usd.current | COLLECT | binance | True | binance.fapi.openInterest.PUMPUSDT | Binance USDT-M openInterest × mark; Job 1 names Binance futures PUMPUSDT. |
| pump.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| pump.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_prices / stage1 price_structure.now_usd via CG markets pump-fun. |
| pump.revenue.usd.7d | COLLECT | defillama | True | defillama.summary.fees.pump.fun.dailyRevenue | Job 1 URL DefiLlama pump.fun fees page; V3 uses dataType=dailyRevenue 7d chart s |
| pump.revenue.usd_per_day.ath_sep | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.revenue.usd_per_day.current | COLLECT | defillama | True | defillama.summary.fees.pump.fun.dailyRevenue | V3 pump_platform_health revenue.total_24h_usd. |
| pump.revenue.usd_per_day.jan_high | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.revenue.usd_per_day.june_atl | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.rs.vs_btc.pct.30d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | Job 1 binance-daily klines; RS = PUMP window return minus bench window return. |
| pump.rs.vs_btc.pct.7d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | Job 1 binance-daily klines; RS = PUMP window return minus bench window return. |
| pump.rs.vs_sol.pct.30d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | Job 1 binance-daily klines; RS = PUMP window return minus bench window return. |
| pump.rs.vs_sol.pct.7d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | Job 1 binance-daily klines; RS = PUMP window return minus bench window return. |
| pump.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| pump.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| pump.siren.watched_wallet_count.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| pump.supply.circulating.pct | COLLECT | coingecko | True | coingecko.markets.active | V3 pump_stage1_evidence circulating_pct_of_max; CG + Solana RPC cross-check. |
| pump.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| pump.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| render.bme.burned.tokens.last4 | COLLECT | render_foundation | True | render.epochBurnStats | Job 1 epochBurnStats. |
| render.bme.burned.tokens.last8 | COLLECT | render_foundation | True | render.epochBurnStats | Job 1 epochBurnStats. |
| render.bme.emissions.tokens.last8 | COLLECT | render_foundation | True | render.liabilityEpochs | V3 render_stage1_loader bme.last8.node_emissions from liabilityEpochs. |
| render.bme.node_due.tokens.per_epoch | COLLECT | render_foundation | True | render.epochBurnStats | V3 render_stage1_loader bme.node_operator_due_per_epoch. |
| render.bme.ratio.last4 | COLLECT | render_foundation | True | render.epochBurnStats | V3 render_stage1_loader bme.last4.ratio. |
| render.bme.ratio.last8 | COLLECT | render_foundation | True | render.epochBurnStats | V3 render_stage1_loader bme.last8.ratio. |
| render.emissions.tokens.remaining | COLLECT | render_foundation | True | render.dashboard.main | CGPT Job 2B: render.dashboard.main html selector render_leftover_emissions label |
| render.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.RENDERUSDT | Job 1 names Binance; official futures/spot JSON API. |
| render.leverage.x.current | COLLECT | binance | True | binance.fapi.ticker24h.RENDERUSDT | V3 feeds_live _binance_lev perp/spot 24h quote ratio for RENDERUSDT. |
| render.ma.usd.200d | COLLECT | binance | True | binance.spot.klines.RENDERUSDT.1d | V3 sma_trend VENUES render→spot RENDERUSDT; SMA200 USD. |
| render.ma.usd.50d | COLLECT | binance | True | binance.spot.klines.RENDERUSDT.1d | V3 sma_trend VENUES render→spot RENDERUSDT; SMA50 USD. |
| render.nodes.count.listed | COLLECT | render_foundation | True | render.nodes_and_frames | Same Foundation stats payload as frames. |
| render.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| render.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_prices / stage1 price_structure.now_usd via CG markets render-token. |
| render.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| render.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| render.siren.watched_wallet_count.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| render.supply.circulating.tokens | COLLECT | render_foundation | True | render.supplyInfo | Job 1 Foundation supplyInfo. |
| render.supply.max.tokens | COLLECT | render_foundation | True | render.supplyInfo | Job 1 Foundation supplyInfo. |
| render.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| render.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| render.usage.frames.cumulative | COLLECT | render_foundation | True | render.nodes_and_frames | V3 stats.renderfoundation.com/api/nodes_and_frames; Job 1 URL is the stats site. |
| retardio.price.usd.live | COLLECT | dexscreener | True | dexscreener.token.retardio | index-v4.html dex:6ogzHhzdrQr9Pgv6hZ2MNze7UrzBMAFyBBWUYp1Fhitx highest-liquidity |
| retardio.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| retardio.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| retardio.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| retardio.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.burn.tokens.per_year | COLLECT | solana_rpc | True | solana.rpc.getInflationRate | V3 sol_intel staking_inflation_burn estimated burn tokens/yr. |
| sol.dex_eth_ratio.7d.x | COLLECT | defillama | True | defillama.overview.dexs.solana | V3 feeds_live _llama_dex_ratio ratio_7d. |
| sol.dex_eth_ratio.latest_day.x | COLLECT | defillama | True | defillama.overview.dexs.solana | V3 feeds_live _llama_dex_ratio ratio_24h. |
| sol.dex_eth_ratio.x.current | COLLECT | defillama | True | defillama.overview.dexs.solana | V3 feeds_live _llama_dex_ratio ratio_24h. |
| sol.etf.flow.usd.1d | COLLECT | farside | True | farside.html.sol | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions |
| sol.etf.flow.usd.30d | COLLECT | farside | True | farside.html.sol | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions |
| sol.etf.flow.usd.7d | COLLECT | farside | True | farside.html.sol | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions |
| sol.etf.flow.usd.all_time | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.fees.usd_per_day.current | COLLECT | defillama | True | defillama.summary.fees.solana.dailyFees | V3 feeds_live _llama_fees + collect sol.fees total24h. |
| sol.fees.usd_per_day.june_2026 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.fees.usd_per_day.mean_30d | COLLECT | defillama | True | defillama.summary.fees.solana.dailyFees | Job 1 URL DefiLlama Solana fees. |
| sol.fees.usd_per_day.nov_2024 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.SOLUSDT | Job 1 URL is fundingRate; V3 live feed uses premiumIndex lastFundingRate on the  |
| sol.funding.rate.mean_7d | COLLECT | binance | True | binance.fapi.fundingRate.SOLUSDT | V3 sol_intel funding 7d mean from Binance fundingRate history. |
| sol.inflation.pct.current | COLLECT | solana_rpc | True | solana.rpc.getInflationRate | Job 1 Solana RPC; getInflationRate.total is a fraction. |
| sol.inflation.pct.stage1 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.issuance.tokens.per_year | COLLECT | solana_rpc | True | solana.rpc.getInflationRate | lib/supporting_feeds.py fetch_solana_network issuance_yr. |
| sol.leverage.x.current | COLLECT | binance | True | binance.fapi.ticker24h.SOLUSDT | V3 feeds_live _binance_lev perp/spot 24h quote ratio for SOLUSDT. |
| sol.leverage.x.stage1 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.ma.usd.200d | COLLECT | binance | True | binance.spot.klines.SOLUSDT.1d | V3 sma_trend VENUES sol→spot SOLUSDT; SMA200 USD. |
| sol.ma.usd.50d | COLLECT | binance | True | binance.spot.klines.SOLUSDT.1d | V3 sma_trend VENUES sol→spot SOLUSDT; SMA50 USD. |
| sol.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| sol.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_prices / stage1 price_structure.now_usd via CG markets solana. |
| sol.rs.vs_btc.pp.30d | COLLECT | binance | True | binance.spot.klines.SOLUSDT.1d | Job 1 URL is SOLUSDT daily klines. |
| sol.rs.vs_btc.pp.7d | COLLECT | binance | True | binance.spot.klines.SOLUSDT.1d | Job 1 URL is SOLUSDT daily klines. |
| sol.stablecoin.usd.current | COLLECT | defillama | True | defillama.stablecoinchains | Job 1 URL DefiLlama stablecoins/chains; V3 stablecoinchains peggedUSD. |
| sol.stablecoin.usd.stage1 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.stake.ratio.pct | COLLECT | solana_rpc | True | solana.rpc.getVoteAccounts | lib/supporting_feeds.py fetch_solana_network stake_pct. |
| sol.stake.tokens.current | COLLECT | solana_rpc | True | solana.rpc.getVoteAccounts | Sum activatedStake lamports / 1e9. |
| sol.staking.apy.pct | PRESERVE | — | False | — | V3 sol_product liquid-staking APY sample band (4.65–5.80%) only; no recoverable  |
| sol.supply.circulating.pct | COLLECT | solana_rpc | True | solana.rpc.getSupply | lib/supporting_feeds.py getSupply circulating/total*100. |
| sol.supply.net_change.tokens.per_year | DERIVE | — | True | {'op': 'SUBTRACT', 'inputs': ['sol.issuance.tokens.per_year', 'sol.burn.tokens.per_year'], 'calculation_version': 'v1'} | V3 sol_intel net issuance - burn SOL/yr. |
| sol.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.tps.all.current | COLLECT | solana_rpc | True | solana.rpc.getRecentPerformanceSamples | V3 sol_intel activity.tps_all_mean_20samples. |
| sol.tps.nonvote.current | COLLECT | solana_rpc | True | solana.rpc.getRecentPerformanceSamples | Job 1 getRecentPerformanceSamples. |
| sol.tvl.usd.current | COLLECT | defillama | True | defillama.historicalChainTvl.Solana | Job 1 URL DefiLlama Solana chain; V3 historicalChainTvl last tvl. |
| sol.tvl.usd.jan_2025 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.tvl.usd.stage1 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| sol.validators.active.count | COLLECT | solana_rpc | True | solana.rpc.getVoteAccounts | Job 1 getVoteAccounts. |
| spx.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.SPXUSDT | Job 1 names Binance; official futures/spot JSON API. |
| spx.holders.top20.pct | COLLECT | solana_rpc | True | solana.rpc.getTokenLargestAccounts.spx | V3 spx_stage1_loader holders.solana_top20_pct_of_sol_mint. |
| spx.ma.usd.200d | COLLECT | binance | True | binance.fapi.klines.SPXUSDT.1d | V3 sma_trend VENUES spx→perp SPXUSDT; SMA200 USD. |
| spx.ma.usd.50d | COLLECT | binance | True | binance.fapi.klines.SPXUSDT.1d | V3 sma_trend VENUES spx→perp SPXUSDT; SMA50 USD. |
| spx.oi.binance.usd.current | COLLECT | binance | True | binance.fapi.openInterest.SPXUSDT | Job 1 URL is Binance futures SPXUSDT. |
| spx.oi.change.pct.30d | COLLECT | binance | True | binance.fapi.openInterestHist.SPXUSDT.1d | Binance openInterestHist sumOpenInterestValue Δ30d for SPXUSDT. |
| spx.oi.usd.stage1 | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| spx.price.ath.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| spx.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| spx.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_prices / stage1 price_structure.now_usd via CG markets spx6900. |
| spx.return.pct.30d | COLLECT | coingecko | True | coingecko.markets.active | V3 AUTOJOB01 CoinGecko markets id=spx6900 field=price_change_percentage_30d_in_c |
| spx.siren.supply.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| spx.siren.tracked.tokens.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| spx.siren.watched_wallet_count.current | GROK_WALLET | — | False | — | Job 1 owner=GROK. Cursor does not collect. |
| spx.supply.circulating.pct | COLLECT | coingecko | True | coingecko.markets.active | V3 stage1 supply.circulating_pct_of_max from CG circ/max for spx6900. |
| spx.supply.circulating.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| spx.supply.max.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| spx.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| spx.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| spx.volume.perp.usd.24h | COLLECT | binance | True | binance.fapi.ticker24h.SPXUSDT | CGPT Job 2B: Binance perp SPXUSDT quoteVolume despite Job 1 CoinGecko URL. |
| zec.inflation.pct.current | COLLECT | zcash_explorer | True | zcash.explorer.blockchain-info | V3 zec_stage1_loader supply.estimated_annual_inflation_pct. |
| zec.leverage.x.current | DERIVE | — | True | {'op': 'RATIO', 'inputs': ['zec.volume.perp.usd.24h', 'zec.volume.spot.usd.24h'], 'calculation_version': 'v1'} | Same V3 perp/spot definition; Job 1 names Binance futures ZECUSDT. |
| zec.ma.usd.200d | COLLECT | binance | True | binance.spot.klines.ZECUSDT.1d | V3 sma_trend VENUES zec→spot ZECUSDT; SMA200 USD. |
| zec.ma.usd.50d | COLLECT | binance | True | binance.spot.klines.ZECUSDT.1d | V3 sma_trend VENUES zec→spot ZECUSDT; SMA50 USD. |
| zec.oi.binance.usd.current | COLLECT | binance | True | binance.fapi.openInterest.ZECUSDT | Job 1 ZEC Stage-1 / Binance futures ZECUSDT. |
| zec.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not |
| zec.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | V3 collect_prices / stage1 price_structure.now_usd via CG markets zcash. |
| zec.shielded.share.pct | COLLECT | zcash_explorer | True | zcash.explorer.blockchain-info | V3 zec_stage1_loader monetary.shielded_pct_of_chain from valuePools. |
| zec.shielded.tokens.current | COLLECT | zcash_explorer | True | zcash.explorer.blockchain-info | Job 1 zcashexplorer blockchain-info. |
| zec.supply.circulating.pct | COLLECT | coingecko | True | coingecko.markets.active | V3 stage1 supply.circulating_pct_of_max from CG circ/max for zcash. |
| zec.supply.circulating.tokens | COLLECT | coingecko | True | coingecko.markets.active | V3 AUTOJOB01 CoinGecko markets id=zcash field=circulating_supply. |
| zec.supply.max.tokens | COLLECT | coingecko | True | coingecko.markets.active | V3 zec_stage1_loader supply.max_supply 21M via CG. |
| zec.threshold.out.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| zec.threshold.this_move.usd | PRESERVE | — | False | — | Historical, static, threshold, or dated event. No live collector. |
| zec.tx.count.24h | COLLECT | zcash_explorer | True | zcash.explorer.blockchain-info | Fail closed if explorer uses a different 24h tx field name. |
| zec.volume.perp.usd.24h | COLLECT | binance | True | binance.fapi.ticker24h.ZECUSDT | Job 1 names Binance; official futures/spot JSON API. |
| zec.volume.spot.usd.24h | COLLECT | binance | True | binance.spot.ticker24h.ZECUSDT | Job 1 names Binance; official futures/spot JSON API. |

## Summary

- COLLECT: 208
- DERIVE: 4
- GROK_WALLET: 35
- LEGACY_INACTIVE: 3
- PRESERVE: 70
- total: 320
