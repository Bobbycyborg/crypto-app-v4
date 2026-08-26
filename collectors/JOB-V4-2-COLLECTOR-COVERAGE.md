# JOB-V4-2 collector coverage

Every Job 1 canonical metric has exactly one Job 2 disposition.

| metric_id | disposition | source_key | required | implementation | reason |
|---|---|---|---|---|---|
| 2z.price.usd.live | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| 2z.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| 2z.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| 2z.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| 2z.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| bonk.price.usd.live | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| bonk.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| bonk.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| bonk.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| bonk.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| btc.etf.flow.usd.1d | COLLECT | farside | True | farside.html.btc | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions. |
| btc.etf.flow.usd.2026_08_03_07 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| btc.etf.flow.usd.2026_08_10 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| btc.etf.flow.usd.2026_08_11 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| btc.etf.flow.usd.30d | COLLECT | farside | True | farside.html.btc | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions. |
| btc.etf.flow.usd.7d | COLLECT | farside | True | farside.html.btc | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions. |
| btc.etf.flow.usd.all_time | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| btc.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.BTCUSDT | Job 1 names Binance; official futures/spot JSON API. |
| btc.inflation.pct.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| btc.leverage.x.current | DERIVE | None | True | RATIO | V3 AUTOJOB01 BTCUSDT perp quoteVolume / spot quoteVolume. |
| btc.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| btc.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| btc.oi.btc.current | COLLECT | binance | True | binance.fapi.openInterest.BTCUSDT | Job 1 names Binance; official futures/spot JSON API. |
| btc.oi.change.pct.1d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://www.binance.com/en/futures/BTCUSDT'). No provider substitution. |
| btc.oi.change.pct.30d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Binance openInterest' url='https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT'). No provider substitution. |
| btc.oi.change.pct.7d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://www.binance.com/en/futures/BTCUSDT'). No provider substitution. |
| btc.price.ath.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| btc.price.drawdown_from_ath.pct | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| btc.price.usd.july_2026_low | COLLECT | binance | True | binance.spot.klines.BTCUSDT.1d | Job 1 Binance daily; V3 re-reads July 2026 BTCUSDT daily lows. |
| btc.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| btc.price.usd.report | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| btc.return.pct.30d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| btc.return.pct.7d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| btc.return.pct.90d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| btc.stablecoin.change.pct.30d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Approved Market evidence' url='https://www.chicagofed.org/research/data/nfci/current-data'). No provider substitution. |
| btc.supply.circulating.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| btc.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| btc.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| btc.volume.perp.usd.24h | COLLECT | binance | True | binance.fapi.ticker24h.BTCUSDT | Job 1 names Binance; official futures/spot JSON API. |
| btc.volume.spot.usd.24h | COLLECT | binance | True | binance.spot.ticker24h.BTCUSDT | Job 1 names Binance; official futures/spot JSON API. |
| drift.price.usd.live | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| drift.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| drift.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| drift.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| eth.etf.flow.usd.1d | COLLECT | farside | True | farside.html.eth | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions. |
| eth.etf.flow.usd.30d | COLLECT | farside | True | farside.html.eth | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions. |
| eth.etf.flow.usd.7d | COLLECT | farside | True | farside.html.eth | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions. |
| eth.etf.flow.usd.all_time | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| fart.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.FARTCOINUSDT | Job 1 names Binance; official futures/spot JSON API. |
| fart.holders.lp.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://www.coingecko.com/en/coins/fartcoin'). No provider substitution. |
| fart.holders.unattributed.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://www.coingecko.com/en/coins/fartcoin'). No provider substitution. |
| fart.holders.unit_treasury.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://www.coingecko.com/en/coins/fartcoin'). No provider substitution. |
| fart.leverage.perp_spot_notional.x | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='FARTCOIN Stage-1' url=''). No provider substitution. |
| fart.liquidity.dex.usd.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='FARTCOIN Stage-1' url='https://www.coingecko.com/en/coins/fartcoin'). No provider substitution. |
| fart.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| fart.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| fart.market_cap.usd.current | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.oi.usd.current | COLLECT | binance | True | binance.fapi.openInterest.FARTCOINUSDT | Job 1 is USD OI; Binance openInterest is contracts. See selector identity; normalized via mark from same-run ticker capture. |
| fart.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| fart.price.usd.report | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| fart.return.pct.30d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.return.pct.7d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.return.pct.90d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.rs.vs_sol.pp.7d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='FARTCOIN Stage-1' url='https://www.coingecko.com/en/coins/fartcoin'). No provider substitution. |
| fart.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| fart.supply.circulating.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| fart.supply.circulating.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.supply.max.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| fart.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| fart.volume.cg.usd.24h | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| fart.volume.perp.usd.24h | COLLECT | binance | True | binance.fapi.ticker24h.FARTCOINUSDT | Job 1 names Binance; official futures/spot JSON API. |
| giga.price.usd.live | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| giga.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| giga.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| giga.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| giga.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| global.fear_greed.index.current | COLLECT | alternative_me | True | alternative_me.fng | Job 1 source alternative.me; official JSON API. |
| global.leverage.x.current | DERIVE | None | True | RATIO | V3 market leverage uses BTCUSDT perp and spot 24h quote. |
| global.participation.above_50dma.count | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='CoinGecko markets' url=''). No provider substitution. |
| global.participation.beat_btc.count | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='CoinGecko markets' url=''). No provider substitution. |
| hype.af.buys.usd.30d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees'). No provider substitution. |
| hype.af.inventory.share_hl_circ.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| hype.af.inventory.tokens.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees'). No provider substitution. |
| hype.emissions.tokens.remaining | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | Job 1 URL api.hyperliquid.xyz/info; V3 tokenDetails futureEmissions. Identity name=HYPE. |
| hype.fees.change.pct.30d | COLLECT | defillama | True | defillama.summary.fees.hyperliquid-perp.dailyFees | 30d percent change of daily fees series. |
| hype.fees.perps.usd.30d | COLLECT | defillama | True | defillama.summary.fees.hyperliquid-perp.dailyFees | Same DefiLlama hyperliquid-perp 30d fees payload as hype.fees.usd.30d; Job 1 URL identical. |
| hype.fees.usd.30d | COLLECT | defillama | True | defillama.summary.fees.hyperliquid-perp.dailyFees | Job 1 URL api.llama.fi/summary/fees/hyperliquid-perp. |
| hype.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://www.coingecko.com/en/coins/hyperliquid'). No provider substitution. |
| hype.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://www.coingecko.com/en/coins/hyperliquid'). No provider substitution. |
| hype.ncu.hyperlabs.tokens | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | V3 HyperLabs NCU address on tokenDetails.nonCirculatingUserBalances. |
| hype.oi.binance.usd.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://www.coingecko.com/en/coins/hyperliquid'). No provider substitution. |
| hype.oi.native.usd.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://www.coingecko.com/en/coins/hyperliquid'). No provider substitution. |
| hype.oi.platform.usd.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://api.hyperliquid.xyz/info'). No provider substitution. |
| hype.oi.token.usd.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://api.hyperliquid.xyz/info'). No provider substitution. |
| hype.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| hype.price.usd.report | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| hype.return.pct.30d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| hype.return.pct.7d | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| hype.stake.tokens.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://api.hyperliquid.xyz/info'). No provider substitution. |
| hype.supply.circulating.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://api.hyperliquid.xyz/info'). No provider substitution. |
| hype.supply.hl_circulating.pct | COLLECT | hyperliquid | True | hyperliquid.info.tokenDetails | circulatingSupply/maxSupply*100 from tokenDetails. |
| hype.supply.max.tokens | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees'). No provider substitution. |
| hype.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| hype.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| hype.volume.l1_perp.usd.24h | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://api.hyperliquid.xyz/info'). No provider substitution. |
| hype.volume.token.usd.24h | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='HYPE Stage-1 evidence' url='https://api.hyperliquid.xyz/info'). No provider substitution. |
| hype.wallet.foundation.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| io.clusters.running.count | COLLECT | io_explorer | True | io.clusters | Job 1 io.net Explorer clusters URL. |
| io.devices.inventory.count | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='io.net Explorer API' url='https://api.io.solutions/v1/io-explorer/network/info/clusters'). No provider substitution. |
| io.emissions.tokens.remaining | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| io.leverage.x.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://www.binance.com/en/futures/IOUSDT'). No provider substitution. |
| io.leverage.x.stage1 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| io.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| io.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| io.oi.usd.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| io.oi.usd.stage1 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| io.price.ath.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| io.price.drawdown_from_ath.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Stage-1 price' url=''). No provider substitution. |
| io.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| io.price.usd.report | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Stage-1 price' url=''). No provider substitution. |
| io.revenue.usd.cumulative | COLLECT | io_explorer | True | io.clusters | Job 1 clusters URL; V3 total_earnings on clusters payload. |
| io.revenue.usd.july_2026 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| io.revenue.usd.june_2026 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| io.revenue.usd.may_2026 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| io.revenue.usd_per_day.mean_30d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://api.io.solutions/v1/io-explorer/network/info/clusters'). No provider substitution. |
| io.rs.vs_sol.pp.30d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Binance' url=''). No provider substitution. |
| io.rs.vs_sol.pp.7d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Binance' url=''). No provider substitution. |
| io.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| io.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| io.siren.watched_wallet_count.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| io.supply.circulating.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| io.supply.circulating.tokens | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Stage-1 supply' url=''). No provider substitution. |
| io.supply.max.tokens | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Stage-1 supply' url=''). No provider substitution. |
| io.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| io.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| lockin.price.usd.live | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| lockin.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| lockin.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| lockin.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| lockin.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| nos.gpu_hours.approx_31d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://blockchain-indexer.k8s.prd.nos.ci/jobs/count'). No provider substitution. |
| nos.host_rewards.usd.cumulative | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Stage 1' url='https://learn.nosana.com/api/first-job.html'). No provider substitution. |
| nos.jobs.approx_30d.count | COLLECT | nosana | True | nosana.jobs.count | Requires last30Days on jobs/count; else SOURCE_SCHEMA_MISMATCH. |
| nos.jobs.completed.cumulative | COLLECT | nosana | True | nosana.jobs.count | Job 1 Nosana blockchain-indexer jobs/count. |
| nos.jobs.queued.count | COLLECT | nosana | True | nosana.jobs.count | Job 1 URL jobs/count. |
| nos.jobs.running.count | COLLECT | nosana | True | nosana.jobs.count | Job 1 URL jobs/count. |
| nos.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| nos.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| nos.market_cap.usd.current | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| nos.nodes.with_running_jobs.count | COLLECT | nosana | True | nosana.jobs.count | Field name must exist on jobs/count. Fail closed if renamed. |
| nos.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| nos.price.usd.report | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| nos.return.pct.180d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='CoinGecko + GT OHLCV' url='https://www.coingecko.com/en/coins/nosana'). No provider substitution. |
| nos.rs.vs_sol.pp.30d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Stage 1' url='https://www.coingecko.com/en/coins/nosana'). No provider substitution. |
| nos.rs.vs_sol.pp.7d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Stage 1' url='https://www.coingecko.com/en/coins/nosana'). No provider substitution. |
| nos.siren.aug1_unknown_wallet_count.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| nos.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| nos.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| nos.siren.watched_wallet_count.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| nos.stake.ratio.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| nos.stake.tokens.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Stage 1' url='https://www.coingecko.com/en/coins/nosana'). No provider substitution. |
| nos.supply.circulating.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| nos.supply.circulating.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| nos.supply.max.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| nos.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| nos.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| orca.price.usd.live | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| orca.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| orca.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| orca.siren.watched_wallet_count.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| orca.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| orca.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| portfolio.portfolio.value.usd.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| pump.buyback.usd.1d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| pump.buyback.usd.7d | COLLECT | defillama | True | defillama.summary.fees.pump.fun.dailyHoldersRevenue | V3 holdersRevenue 7d chart sum for pump.fun. |
| pump.buyback.usd_per_day.ath_sep | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.buyback.usd_per_day.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| pump.buyback.usd_per_day.jan_high | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.buyback.usd_per_day.june_atl | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.fees.usd_per_day.ath_sep | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.fees.usd_per_day.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| pump.fees.usd_per_day.jan_high | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.fees.usd_per_day.june_atl | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.PUMPUSDT | Job 1 names Binance; official futures/spot JSON API. |
| pump.holders.unattributed.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Solscan · Squads custody + OTC' url='https://solscan.io/account/5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9'). No provider substitution. |
| pump.leverage.x.current | COLLECT | binance | True | binance.fapi.ticker24h.PUMPUSDT | Job 1 binance futures PUMPUSDT; V3 perp/spot 24h quote ratio. |
| pump.liquidity.dex.usd.current | COLLECT | dexscreener | True | dexscreener.token.pump | Job 1 source dexscreener; V3 DexScreener pair for PUMP mint. First-pair is forbidden — use identity pairAddress if present. |
| pump.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| pump.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| pump.market_share.pct.ath_sep | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.market_share.pct.aug_10 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.market_share.pct.current | COLLECT | defillama | True | defillama.overview.fees | V3 Launchpad category 24h fee share. |
| pump.market_share.pct.jan_high | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.market_share.pct.june_atl | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.market_share.pct.share_history | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.mm.wintermute.balance.tokens | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| pump.mm.wintermute.transfer.tokens | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| pump.oi.usd.current | COLLECT | binance | True | binance.fapi.openInterest.PUMPUSDT | Binance USDT-M openInterest × mark; Job 1 names Binance futures PUMPUSDT. |
| pump.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| pump.price.usd.report | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='coingecko/dex' url=''). No provider substitution. |
| pump.revenue.usd.7d | COLLECT | defillama | True | defillama.summary.fees.pump.fun.dailyRevenue | Job 1 URL DefiLlama pump.fun fees page; V3 uses dataType=dailyRevenue 7d chart sum. Does not prefer $9M or $7M. |
| pump.revenue.usd_per_day.ath_sep | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.revenue.usd_per_day.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| pump.revenue.usd_per_day.jan_high | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.revenue.usd_per_day.june_atl | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.rs.vs_btc.pct.30d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | Job 1 binance-daily klines; RS = PUMP window return minus bench window return. |
| pump.rs.vs_btc.pct.7d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | Job 1 binance-daily klines; RS = PUMP window return minus bench window return. |
| pump.rs.vs_sol.pct.30d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | Job 1 binance-daily klines; RS = PUMP window return minus bench window return. |
| pump.rs.vs_sol.pct.7d | COLLECT | binance | True | binance.spot.klines.PUMPUSDT.1d | Job 1 binance-daily klines; RS = PUMP window return minus bench window return. |
| pump.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| pump.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| pump.siren.watched_wallet_count.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| pump.supply.circulating.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| pump.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| pump.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| render.bme.burned.tokens.last4 | COLLECT | render_foundation | True | render.epochBurnStats | Job 1 epochBurnStats. |
| render.bme.burned.tokens.last8 | COLLECT | render_foundation | True | render.epochBurnStats | Job 1 epochBurnStats. |
| render.bme.emissions.tokens.last8 | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Foundation first-party API' url='https://infra.shikumi.cc/api/v1/epochBurnStats'). No provider substitution. |
| render.bme.node_due.tokens.per_epoch | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Foundation first-party API' url='https://infra.shikumi.cc/api/v1/epochBurnStats'). No provider substitution. |
| render.bme.ratio.last4 | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Foundation API' url='https://infra.shikumi.cc/api/v1/epochBurnStats'). No provider substitution. |
| render.bme.ratio.last8 | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Foundation first-party API' url='https://infra.shikumi.cc/api/v1/epochBurnStats'). No provider substitution. |
| render.emissions.tokens.remaining | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Foundation API' url='https://infra.shikumi.cc/api/v1/epochBurnStats'). No provider substitution. |
| render.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.RENDERUSDT | Job 1 names Binance; official futures/spot JSON API. |
| render.leverage.x.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://www.binance.com/en/futures/RENDERUSDT'). No provider substitution. |
| render.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| render.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| render.nodes.count.listed | COLLECT | render_foundation | True | render.nodes_and_frames | Same Foundation stats payload as frames. |
| render.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| render.price.usd.report | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| render.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| render.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| render.siren.watched_wallet_count.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| render.supply.circulating.tokens | COLLECT | render_foundation | True | render.supplyInfo | Job 1 Foundation supplyInfo. |
| render.supply.max.tokens | COLLECT | render_foundation | True | render.supplyInfo | Job 1 Foundation supplyInfo. |
| render.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| render.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| render.usage.frames.cumulative | COLLECT | render_foundation | True | render.nodes_and_frames | V3 stats.renderfoundation.com/api/nodes_and_frames; Job 1 URL is the stats site. |
| retardio.price.usd.live | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| retardio.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| retardio.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| retardio.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| retardio.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.burn.tokens.per_year | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Solana RPC + DefiLlama burn' url='https://api.mainnet-beta.solana.com'). No provider substitution. |
| sol.dex_eth_ratio.7d.x | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://defillama.com/dexs/chains/solana'). No provider substitution. |
| sol.dex_eth_ratio.latest_day.x | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://defillama.com/dexs/chains/solana'). No provider substitution. |
| sol.dex_eth_ratio.x.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://defillama.com/dexs/chains/solana'). No provider substitution. |
| sol.etf.flow.usd.1d | COLLECT | farside | True | farside.html.sol | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions. |
| sol.etf.flow.usd.30d | COLLECT | farside | True | farside.html.sol | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions. |
| sol.etf.flow.usd.7d | COLLECT | farside | True | farside.html.sol | Job 1 Farside Investors; official HTML tables. Values stored as USD not millions. |
| sol.etf.flow.usd.all_time | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.fees.usd_per_day.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| sol.fees.usd_per_day.june_2026 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.fees.usd_per_day.mean_30d | COLLECT | defillama | True | defillama.summary.fees.solana.dailyFees | Job 1 URL DefiLlama Solana fees. |
| sol.fees.usd_per_day.nov_2024 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.SOLUSDT | Job 1 URL is fundingRate; V3 live feed uses premiumIndex lastFundingRate on the same Binance USDT-M product. |
| sol.funding.rate.mean_7d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Binance SOLUSDT' url='https://www.binance.com/en/trade/SOL_USDT'). No provider substitution. |
| sol.inflation.pct.current | COLLECT | solana_rpc | True | solana.rpc.getInflationRate | Job 1 Solana RPC; getInflationRate.total is a fraction. |
| sol.inflation.pct.stage1 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.issuance.tokens.per_year | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Solana RPC + DefiLlama burn' url='https://api.mainnet-beta.solana.com'). No provider substitution. |
| sol.leverage.x.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://fapi.binance.com/fapi/v1/fundingRate?symbol=SOLUSDT&limit=1'). No provider substitution. |
| sol.leverage.x.stage1 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| sol.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| sol.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| sol.price.usd.report | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Binance' url='https://fapi.binance.com/fapi/v1/fundingRate?symbol=SOLUSDT'). No provider substitution. |
| sol.rs.vs_btc.pp.30d | COLLECT | binance | True | binance.spot.klines.SOLUSDT.1d | Job 1 URL is SOLUSDT daily klines. |
| sol.rs.vs_btc.pp.7d | COLLECT | binance | True | binance.spot.klines.SOLUSDT.1d | Job 1 URL is SOLUSDT daily klines. |
| sol.stablecoin.usd.current | COLLECT | defillama | True | defillama.stablecoinchains | Job 1 URL DefiLlama stablecoins/chains; V3 stablecoinchains peggedUSD. |
| sol.stablecoin.usd.stage1 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.stake.ratio.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Solana RPC getVoteAccounts' url='https://api.mainnet-beta.solana.com'). No provider substitution. |
| sol.stake.tokens.current | COLLECT | solana_rpc | True | solana.rpc.getVoteAccounts | Sum activatedStake lamports / 1e9. |
| sol.staking.apy.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Solana RPC + DefiLlama burn' url='https://api.mainnet-beta.solana.com'). No provider substitution. |
| sol.supply.circulating.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| sol.supply.net_change.tokens.per_year | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Solana RPC + DefiLlama burn' url='https://api.mainnet-beta.solana.com'). No provider substitution. |
| sol.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.tps.all.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://defillama.com/chain/Solana'). No provider substitution. |
| sol.tps.nonvote.current | COLLECT | solana_rpc | True | solana.rpc.getRecentPerformanceSamples | Job 1 getRecentPerformanceSamples. |
| sol.tvl.usd.current | COLLECT | defillama | True | defillama.historicalChainTvl.Solana | Job 1 URL DefiLlama Solana chain; V3 historicalChainTvl last tvl. |
| sol.tvl.usd.jan_2025 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.tvl.usd.stage1 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| sol.validators.active.count | COLLECT | solana_rpc | True | solana.rpc.getVoteAccounts | Job 1 getVoteAccounts. |
| spx.funding.rate.latest | COLLECT | binance | True | binance.fapi.premiumIndex.SPXUSDT | Job 1 names Binance; official futures/spot JSON API. |
| spx.holders.top20.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='Solana RPC getTokenLargestAccounts · SPX Stage-1' url='https://www.coingecko.com/en/coins/spx6900'). No provider substitution. |
| spx.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| spx.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| spx.oi.binance.usd.current | COLLECT | binance | True | binance.fapi.openInterest.SPXUSDT | Job 1 URL is Binance futures SPXUSDT. |
| spx.oi.change.pct.30d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='SPX Stage-1' url='https://www.binance.com/en/futures/SPXUSDT'). No provider substitution. |
| spx.oi.usd.stage1 | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| spx.price.ath.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| spx.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| spx.price.usd.report | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| spx.return.pct.30d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| spx.siren.supply.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| spx.siren.tracked.tokens.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| spx.siren.watched_wallet_count.current | GROK_WALLET | None | False | none | Job 1 owner=GROK. Cursor does not collect. |
| spx.supply.circulating.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='SPX Stage 1' url='https://www.coingecko.com/en/coins/spx6900'). No provider substitution. |
| spx.supply.circulating.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| spx.supply.max.tokens | COLLECT | coingecko | True | coingecko.markets.active | Job 1 CoinGecko provenance and/or V3 CG_MARKETS relationship. |
| spx.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| spx.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| spx.volume.perp.usd.24h | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='SPX Stage-1' url='https://www.coingecko.com/en/coins/spx6900'). No provider substitution. |
| zec.inflation.pct.current | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='ZEC Stage-1 evidence' url='https://electriccoin.co/blog/zcash-halvening-nu6-embracing-the-new-dev-fund/'). No provider substitution. |
| zec.leverage.x.current | DERIVE | None | True | RATIO | Same V3 perp/spot definition; Job 1 names Binance futures ZECUSDT. |
| zec.ma.usd.200d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://www.coingecko.com/en/coins/zcash'). No provider substitution. |
| zec.ma.usd.50d | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://www.coingecko.com/en/coins/zcash'). No provider substitution. |
| zec.oi.binance.usd.current | COLLECT | binance | True | binance.fapi.openInterest.ZECUSDT | Job 1 ZEC Stage-1 / Binance futures ZECUSDT. |
| zec.price.usd.live | COLLECT | coingecko | True | coingecko.markets.active | Job 1 live-price source is UNKNOWN. Bound to V3 AUTOJOB01 CoinGecko markets, not HTML data-feed. |
| zec.price.usd.report | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url=''). No provider substitution. |
| zec.shielded.share.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://mainnet.zcashexplorer.app/api/v1/blockchain-info'). No provider substitution. |
| zec.shielded.tokens.current | COLLECT | zcash_explorer | True | zcash.explorer.blockchain-info | Job 1 zcashexplorer blockchain-info. |
| zec.supply.circulating.pct | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://electriccoin.co/blog/zcash-halvening-nu6-embracing-the-new-dev-fund/'). No provider substitution. |
| zec.supply.circulating.tokens | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://electriccoin.co/blog/zcash-halvening-nu6-embracing-the-new-dev-fund/'). No provider substitution. |
| zec.supply.max.tokens | BLOCKED_SOURCE | None | True | none | Job 1 provenance is insufficient for a reliable collector (source='UNKNOWN' url='https://electriccoin.co/blog/zcash-halvening-nu6-embracing-the-new-dev-fund/'). No provider substitution. |
| zec.threshold.out.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| zec.threshold.this_move.usd | PRESERVE | None | False | none | Historical, static, threshold, or dated event. No live collector. |
| zec.tx.count.24h | COLLECT | zcash_explorer | True | zcash.explorer.blockchain-info | Fail closed if explorer uses a different 24h tx field name. |
| zec.volume.perp.usd.24h | COLLECT | binance | True | binance.fapi.ticker24h.ZECUSDT | Job 1 names Binance; official futures/spot JSON API. |
| zec.volume.spot.usd.24h | COLLECT | binance | True | binance.spot.ticker24h.ZECUSDT | Job 1 names Binance; official futures/spot JSON API. |

## Totals

- COLLECT: 95
- DERIVE: 3
- PRESERVE: 70
- COMPOSITE_ONLY: 0
- GROK_WALLET: 35
- LEGACY_INACTIVE: 0
- BLOCKED_SOURCE: 117
- plan entries: 320
