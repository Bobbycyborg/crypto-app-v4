# JOB-V4-2-SOURCE-RECOVERY

## Previous state
- previous BLOCKED_SOURCE: 117
- previous attempted live failures: 19
- previous required COLLECT/DERIVE attempted: 98 (Job 2 v1 smoke)

## DRIFT
- non-wallet metrics inactive: 3 (drift.price + 2 PRESERVE → INACTIVE)
- required removed: all DRIFT non-wallet required=false
- collectors: 0
- network requests: 0

## Recovery summary
- RECOVERED_JOB1: 0
- RECOVERED_V4_CODE: 0
- RECOVERED_V3_CODE: 106
- RECOVERED_UI_BINDING: 0
- RECOVERED_REFRESH_SCRIPT: 0
- RECOVERED_EVIDENCE: 0
- RECOVERED_GIT_HISTORY: 0
- INACTIVE: 3
- TRUE_BLOCKER: 3
- SOURCE_DECISION_CONFLICT: 1
- ALREADY_VALID: 19

## Phase A gate
- required TRUE_BLOCKER: 3
- required SOURCE_DECISION_CONFLICT: 1
- **PHASE B NOT STARTED**

## Blockers (CGPT decisions required)

### `hype.af.buys.usd.30d`
- **resolution:** TRUE_BLOCKER
- **definition:** Assistance Fund USD buys of HYPE over a trailing 30-day window.
- **notes:** Hard-coded Stage-1 display value is not a source contract per brief §19/§30.
- **evidence:**
  - V3_CODE: `lib/v3/hype_stage1_loader.py` — Stage-1 loader explicitly marks AF 30d buys unknown
  - JOB1: `metrics/metric-registry.json` — Displayed value exists but no executable fetch/calc contract

### `io.emissions.tokens.remaining`
- **resolution:** TRUE_BLOCKER
- **definition:** Remaining future token emissions for IO as currently shown.
- **notes:** Static emissions schedule disclosure, not a recoverable live endpoint.
- **evidence:**
  - V3_CODE: `lib/v3/io_stage1_loader.py` — Tokenomics narrative only; no live remaining-emissions API field

### `render.emissions.tokens.remaining`
- **resolution:** TRUE_BLOCKER
- **definition:** Remaining future token emissions for RENDER as currently shown.
- **notes:** epochBurnStats tracks epoch burn/emit; does not expose remaining future emissions total.
- **evidence:**
  - JOB1: `metrics/metric-registry.json` — Job 1 cites epochBurnStats URL
  - V3_CODE: `lib/v3/render_stage1_loader.py` — No remaining-emissions counter in Foundation loaders

### `spx.oi.change.pct.30d`
- **resolution:** SOURCE_DECISION_CONFLICT
- **definition:** Percent change in SPX open interest over thirty days.
- **notes:** CGPT must decide: rename metric to oi_vs_30d_max or recover Binance OI % change methodology.
- **evidence:**
  - JOB1: `metrics/metric-registry.json` — Canonical definition is trailing OI % change
  - V3_CODE: `lib/v3/spx_stage1_loader.py` — V3 displays current OI as % of 30d max (~87%), not % change
  - V3_CODE: `lib/v3/autojob01/feeds_live.py` — openInterestHist used for % of max, not period change

## Detailed table (previously blocked)

| metric_id | old | resolution | provider/method | tier |
|---|---|---|---|---|
| 2z.price.usd.live | BLOCKED_SOURCE | RECOVERED_V4_HTML | dexscreener | 1 |
| bonk.price.usd.live | BLOCKED_SOURCE | RECOVERED_V4_HTML | binance | 1 |
| btc.inflation.pct.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | derived | 2 |
| btc.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| btc.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| btc.oi.change.pct.1d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| btc.oi.change.pct.30d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| btc.oi.change.pct.7d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| btc.stablecoin.change.pct.30d | BLOCKED_SOURCE | RECOVERED_V3_CODE | defillama | 2 |
| btc.supply.circulating.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| drift.price.usd.live | BLOCKED_SOURCE | INACTIVE | - | N/A |
| fart.holders.lp.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | stage2_overlay | 2 |
| fart.holders.unattributed.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | stage2_overlay | 2 |
| fart.holders.unit_treasury.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | stage2_overlay | 2 |
| fart.leverage.perp_spot_notional.x | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance+coinbase | 2 |
| fart.liquidity.dex.usd.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | dexscreener | 2 |
| fart.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| fart.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| fart.price.usd.report | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| fart.rs.vs_sol.pp.7d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| fart.supply.circulating.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| giga.price.usd.live | BLOCKED_SOURCE | RECOVERED_V4_HTML | dexscreener | 1 |
| global.participation.above_50dma.count | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| global.participation.beat_btc.count | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| hype.af.buys.usd.30d | BLOCKED_SOURCE | TRUE_BLOCKER | - | N/A |
| hype.af.inventory.share_hl_circ.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid | 2 |
| hype.af.inventory.tokens.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid | 2 |
| hype.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| hype.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| hype.oi.binance.usd.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| hype.oi.native.usd.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid | 2 |
| hype.oi.platform.usd.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid | 2 |
| hype.oi.token.usd.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid | 2 |
| hype.price.usd.report | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| hype.stake.tokens.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid | 2 |
| hype.supply.circulating.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid+coingecko | 2 |
| hype.supply.max.tokens | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid | 2 |
| hype.volume.l1_perp.usd.24h | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid | 2 |
| hype.volume.token.usd.24h | BLOCKED_SOURCE | RECOVERED_V3_CODE | hyperliquid | 2 |
| io.devices.inventory.count | BLOCKED_SOURCE | RECOVERED_V3_CODE | io_explorer | 2 |
| io.emissions.tokens.remaining | BLOCKED_SOURCE | TRUE_BLOCKER | - | N/A |
| io.leverage.x.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| io.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| io.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| io.oi.usd.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| io.price.drawdown_from_ath.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| io.price.usd.report | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| io.revenue.usd_per_day.mean_30d | BLOCKED_SOURCE | RECOVERED_V3_CODE | io_explorer+defillama | 2 |
| io.rs.vs_sol.pp.30d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| io.rs.vs_sol.pp.7d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| io.supply.circulating.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| io.supply.circulating.tokens | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| io.supply.max.tokens | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| lockin.price.usd.live | BLOCKED_SOURCE | RECOVERED_V4_HTML | dexscreener | 1 |
| nos.gpu_hours.approx_31d | BLOCKED_SOURCE | RECOVERED_V3_CODE | nosana | 2 |
| nos.host_rewards.usd.cumulative | BLOCKED_SOURCE | RECOVERED_V3_CODE | nosana | 2 |
| nos.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| nos.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| nos.price.usd.report | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| nos.return.pct.180d | BLOCKED_SOURCE | RECOVERED_V3_CODE | geckoterminal/coingecko | 2 |
| nos.rs.vs_sol.pp.30d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance/gecko | 2 |
| nos.rs.vs_sol.pp.7d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance/gecko | 2 |
| nos.stake.ratio.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | nosana | 2 |
| nos.stake.tokens.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | nosana | 2 |
| nos.supply.circulating.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| orca.price.usd.live | BLOCKED_SOURCE | RECOVERED_V4_HTML | binance | 1 |
| pump.buyback.usd.1d | BLOCKED_SOURCE | RECOVERED_V3_CODE | defillama | 2 |
| pump.buyback.usd_per_day.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | defillama | 2 |
| pump.fees.usd_per_day.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | defillama | 2 |
| pump.holders.unattributed.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | forensics | 2 |
| pump.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| pump.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| pump.price.usd.report | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| pump.revenue.usd_per_day.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | defillama | 2 |
| pump.supply.circulating.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko+solana_rpc | 2 |
| render.bme.emissions.tokens.last8 | BLOCKED_SOURCE | RECOVERED_V3_CODE | render_foundation | 2 |
| render.bme.node_due.tokens.per_epoch | BLOCKED_SOURCE | RECOVERED_V3_CODE | render_foundation | 2 |
| render.bme.ratio.last4 | BLOCKED_SOURCE | RECOVERED_V3_CODE | render_foundation | 2 |
| render.bme.ratio.last8 | BLOCKED_SOURCE | RECOVERED_V3_CODE | render_foundation | 2 |
| render.emissions.tokens.remaining | BLOCKED_SOURCE | TRUE_BLOCKER | - | N/A |
| render.leverage.x.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| render.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| render.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| render.price.usd.report | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| retardio.price.usd.live | BLOCKED_SOURCE | RECOVERED_V4_HTML | dexscreener | 1 |
| sol.burn.tokens.per_year | BLOCKED_SOURCE | RECOVERED_V3_CODE | solana_rpc | 2 |
| sol.dex_eth_ratio.7d.x | BLOCKED_SOURCE | RECOVERED_V3_CODE | defillama | 2 |
| sol.dex_eth_ratio.latest_day.x | BLOCKED_SOURCE | RECOVERED_V3_CODE | defillama | 2 |
| sol.dex_eth_ratio.x.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | defillama | 2 |
| sol.fees.usd_per_day.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | defillama | 2 |
| sol.funding.rate.mean_7d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| sol.issuance.tokens.per_year | BLOCKED_SOURCE | RECOVERED_V3_CODE | solana_rpc | 2 |
| sol.leverage.x.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| sol.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| sol.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| sol.price.usd.report | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| sol.stake.ratio.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | solana_rpc | 2 |
| sol.staking.apy.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | external_sample | 2 |
| sol.supply.circulating.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | solana_rpc+coingecko | 2 |
| sol.supply.net_change.tokens.per_year | BLOCKED_SOURCE | RECOVERED_V3_CODE | derived | 2 |
| sol.tps.all.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | solana_rpc | 2 |
| spx.holders.top20.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | solana_rpc | 2 |
| spx.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| spx.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| spx.oi.change.pct.30d | BLOCKED_SOURCE | SOURCE_DECISION_CONFLICT | - | N/A |
| spx.price.usd.report | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| spx.return.pct.30d | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko/binance | 2 |
| spx.supply.circulating.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| spx.volume.perp.usd.24h | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| zec.inflation.pct.current | BLOCKED_SOURCE | RECOVERED_V3_CODE | zcash_explorer+stage1 | 2 |
| zec.ma.usd.200d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| zec.ma.usd.50d | BLOCKED_SOURCE | RECOVERED_V3_CODE | binance | 2 |
| zec.price.usd.report | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| zec.shielded.share.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | zcash_explorer | 2 |
| zec.supply.circulating.pct | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| zec.supply.circulating.tokens | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
| zec.supply.max.tokens | BLOCKED_SOURCE | RECOVERED_V3_CODE | coingecko | 2 |
