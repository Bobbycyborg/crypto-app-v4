# JOB-V4-1-CONFLICT-AUDIT

BEFORE: 30

The v6 pack at `bdd5f92` recorded 30 CONFLICT rows. Each row below is that old metric_id.

## Old conflicts

### `btc.price.ath.usd`
- disposition: PARSE_ERROR_FIXED
- new metric(s): `btc.price.ath.usd`
- reason: Bare `$126.1` has no proved display_multiplier. Raw is UNKNOWN. `~$126.1k` remains 126100. Not a 126.1-vs-126100 conflict.

### `btc.price.drawdown_from_ath.pct`
- disposition: DIFFERENT_OBSERVATION
- new metric(s): `btc.price.drawdown_from_ath.pct` (observation `current_report_2026_08_10` vs `unknown_snapshot`)
- reason: `~−37.1%` and `~−49.6%` are not the same snapshot. Not compared as one conflict.

### `fart.price.usd.live`
- disposition: TRUE_CONFLICT
- new metric(s): `fart.price.usd.live`
- reason: Hold/desk live seeds both claim current live price and disagree (`$0.15055` vs `$0.180`).

### `giga.price.usd.live`
- disposition: ROUNDING_VARIANT
- new metric(s): `giga.price.usd.live`
- reason: `$0.0025` is the rounded display of `$0.00246`. Status FORMAT_VARIANT.

### `hype.af.inventory.tokens.current`
- disposition: ROUNDING_VARIANT
- new metric(s): `hype.af.inventory.tokens.current`
- reason: `46.37M` and `46.4M` / `~46.4M` are rounding variants of one observation.

### `hype.emissions.tokens.remaining`
- disposition: ROUNDING_VARIANT
- new metric(s): `hype.emissions.tokens.remaining`
- reason: `412.44M` and `412M` are rounding variants.

### `hype.ncu.hyperlabs.tokens`
- disposition: ROUNDING_VARIANT
- new metric(s): `hype.ncu.hyperlabs.tokens`
- reason: `241.24M` and `~241M` are rounding variants.

### `io.leverage.x.current`
- disposition: DIFFERENT_SCOPE
- new metric(s): `io.leverage.x.current`, `io.leverage.x.stage1`
- reason: `2.5×` Binance-defined current is not `3.77×` Stage1. Separate IDs.

### `io.price.usd.live`
- disposition: TRUE_CONFLICT
- new metric(s): `io.price.usd.live`
- reason: Visible current live marks disagree.

### `io.revenue.usd.cumulative`
- disposition: ROUNDING_VARIANT
- new metric(s): `io.revenue.usd.cumulative`
- reason: `$27M` / `$26.7M` rounding. `$27.1M` vs `$26,768/d` split: cumulative vs per-day.

### `lockin.price.usd.live`
- disposition: TRUE_CONFLICT
- new metric(s): `lockin.price.usd.live`
- reason: Visible current live marks disagree.

### `nos.jobs.running.count`
- disposition: DIFFERENT_SCOPE
- new metric(s): `nos.jobs.running.count` (855), `nos.nodes.with_running_jobs.count` (35)
- reason: Jobs counted is not nodes counted.

### `nos.price.usd.live`
- disposition: TRUE_CONFLICT
- new metric(s): `nos.price.usd.live`
- reason: Visible current live marks disagree.

### `pump.mm.wintermute.tokens`
- disposition: WALLET_SUBTYPE_SPLIT
- new metric(s): `pump.mm.wintermute.balance.tokens` (~4.43B), `pump.mm.wintermute.transfer.tokens` (~287M). Owner GROK.
- reason: Wallet inventory is not the OTC/transfer amount.

### `pump.price.usd.live`
- disposition: TRUE_CONFLICT
- new metric(s): `pump.price.usd.live`
- reason: Visible current live marks disagree.

### `pump.price.usd.report`
- disposition: ROUNDING_VARIANT
- new metric(s): `pump.price.usd.report`
- reason: `$0.004686` and `$0.0047` are rounding-equivalent. FORMAT_VARIANT.

### `pump.return.pct.30d`
- disposition: PARSE_ERROR_FIXED
- new metric(s): `pump.rs.vs_btc.pct.30d` = 102.3, `pump.rs.vs_sol.pct.30d` = 104.7. Direct price-return no longer carries PUMP/BTC or PUMP/SOL.
- reason: `7d +31.1% · 30d +102.3%` is RS, and the 30d token is 102.3 not 31.1.

### `pump.return.pct.7d`
- disposition: DIFFERENT_SCOPE
- new metric(s): `pump.rs.vs_btc.pct.7d` = 31.1, `pump.rs.vs_sol.pct.7d` = 27.7
- reason: Parent series PUMP/BTC and PUMP/SOL are relative strength, not asset price return.

### `pump.return.pct.90d`
- disposition: DIFFERENT_SCOPE
- new metric(s): RS series inherit parent identity; 90d not merged into 30d/7d return.
- reason: Series identity is inherited. No merge across RS vs direct return.

### `pump.revenue.usd.7d`
- disposition: TRUE_CONFLICT
- new metric(s): `pump.revenue.usd.7d`
- reason: `$9.0M/wk` and `$7.0M/wk` share local DefiLlama as_of `2026-08-25T18:35:17Z` and disagree. Same observation, material disagreement.

### `render.price.usd.live`
- disposition: TRUE_CONFLICT
- new metric(s): `render.price.usd.live`
- reason: Visible current live marks disagree.

### `retardio.price.usd.live`
- disposition: TRUE_CONFLICT
- new metric(s): `retardio.price.usd.live`
- reason: Visible current live marks disagree.

### `sol.dex_eth_ratio.x.current`
- disposition: DIFFERENT_SCOPE
- new metric(s): `sol.dex_eth_ratio.x.current` (1.816×), `sol.dex_eth_ratio.latest_day.x` (1.786×), `sol.dex_eth_ratio.7d.x` (1.762×)
- reason: Latest-day and 7d are not the unscoped current ratio.

### `sol.fees.usd_per_day.mean_30d`
- disposition: DIFFERENT_OBSERVATION
- new metric(s): current `$809k/d` vs Stage1 `$516,236.10/d` (`observation_id=stage1_2026_08_12`)
- reason: Evidence-child 516 is not the same fetch as the current 809 print.

### `sol.inflation.pct.current`
- disposition: ROUNDING_VARIANT
- new metric(s): `sol.inflation.pct.current`
- reason: `3.68%` and `3.7%` / `3.70%` are rounding variants.

### `sol.price.usd.live`
- disposition: TRUE_CONFLICT
- new metric(s): `sol.price.usd.live`
- reason: Visible current live marks disagree.

### `sol.stablecoin.usd.current`
- disposition: DIFFERENT_OBSERVATION
- new metric(s): `sol.stablecoin.usd.current` ($15.91B), `sol.stablecoin.usd.stage1` ($15.64B)
- reason: Current vs Stage1 stock.

### `sol.tvl.usd.current`
- disposition: DIFFERENT_OBSERVATION
- new metric(s): `sol.tvl.usd.current` ($5.65B), `sol.tvl.usd.stage1` ($4.80B / $4.8B)
- reason: Current vs Stage1 TVL.

### `spx.oi.usd.current`
- disposition: DIFFERENT_SCOPE
- new metric(s): `spx.oi.usd.stage1` ($2.95M), `spx.oi.binance.usd.current` (~$6.4M)
- reason: Stage1 notional is not Binance OI.

### `spx.price.usd.live`
- disposition: TRUE_CONFLICT
- new metric(s): `spx.price.usd.live`
- reason: Visible current live marks disagree.

---

AFTER: 10 genuine conflicts

Disposition tallies for the old 30 (one primary each):

- TRUE_CONFLICT: 10 (`fart/io/lockin/nos/pump/render/retardio/sol/spx` live prices + `pump.revenue.usd.7d`)
- ROUNDING_VARIANT: 7
- DIFFERENT_SCOPE: 6
- DIFFERENT_OBSERVATION: 4
- PARSE_ERROR_FIXED: 2
- NONMETRIC: 0
- WALLET_SUBTYPE_SPLIT: 1

Remaining 10 CONFLICT rows (all `conflict_review=MANUALLY_CONFIRMED`):

1. `fart.price.usd.live` — `$0.15055` vs `$0.180` — same live_current observation, not rounding.
2. `io.price.usd.live` — `$0.122848` vs `$0.141` — same live_current observation, not rounding.
3. `lockin.price.usd.live` — `$0.001417` vs `$0.001407` — same live_current; 6 vs 6 dp, not a rounding of each other.
4. `nos.price.usd.live` — `$0.28377` vs `$0.297` — same live_current observation, not rounding.
5. `pump.price.usd.live` — `$0.003228` vs `$0.00409` — same live_current observation, not rounding.
6. `pump.revenue.usd.7d` — `$9.0M/wk` vs `$7.0M/wk` — same DefiLlama as_of, same observation, material disagreement.
7. `render.price.usd.live` — `$1.37` vs `$1.48` — same live_current observation, not rounding.
8. `retardio.price.usd.live` — `$0.001738` vs `$0.001701` — same live_current observation, not rounding.
9. `sol.price.usd.live` — `$85.81` vs `$90.18` — same live_current observation, not rounding.
10. `spx.price.usd.live` — `$0.373899` vs `$0.432` — same live_current observation, not rounding.
