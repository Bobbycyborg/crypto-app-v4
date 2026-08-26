# JOB-V4-1-REGRESSION-CONTEXT

original parent → child literal → metric_id/classification → raw_value → historical/current → observation anchor → source/as_of

## 1. PUMP ATH Sep fees/revenue/buyback
- `(none)` / `` → `fees $1.9M/d · rev $1.7M/d · buyback/burn $1.7M/d` → `None`/compound_parent → `1900000.0` → CURRENT_DYNAMIC → ath_sep → defillama/UNKNOWN
- `ATH Sep` / `fees $1.9M/d · rev $1.7M/d · buyback/burn $1.7M/d` → `$1.9M/d` → `pump.fees.usd_per_day.ath_sep`/fees_named_hist → `1900000.0` → HISTORICAL → ath_sep → defillama/UNKNOWN
- `ATH Sep` / `fees $1.9M/d · rev $1.7M/d · buyback/burn $1.7M/d` → `$1.7M/d` → `pump.revenue.usd_per_day.ath_sep`/rev_named_hist → `1700000.0` → HISTORICAL → ath_sep → defillama/UNKNOWN
- `ATH Sep` / `fees $1.9M/d · rev $1.7M/d · buyback/burn $1.7M/d` → `$1.7M/d` → `pump.buyback.usd_per_day.ath_sep`/buyback_named_hist → `1700000.0` → HISTORICAL → ath_sep → defillama/UNKNOWN

## 2. PUMP Jan high fees/revenue/buyback
- `(none)` / `` → `fees $1.5M/d · rev $1.2M/d · buyback/burn $1.1M/d` → `None`/compound_parent → `1500000.0` → CURRENT_DYNAMIC → jan_high → defillama/UNKNOWN
- `Jan high` / `fees $1.5M/d · rev $1.2M/d · buyback/burn $1.1M/d` → `$1.5M/d` → `pump.fees.usd_per_day.jan_high`/fees_named_hist → `1500000.0` → HISTORICAL → jan_high → defillama/UNKNOWN
- `Jan high` / `fees $1.5M/d · rev $1.2M/d · buyback/burn $1.1M/d` → `$1.2M/d` → `pump.revenue.usd_per_day.jan_high`/rev_named_hist → `1200000.0` → HISTORICAL → jan_high → defillama/UNKNOWN
- `Jan high` / `fees $1.5M/d · rev $1.2M/d · buyback/burn $1.1M/d` → `$1.1M/d` → `pump.buyback.usd_per_day.jan_high`/buyback_named_hist → `1100000.0` → HISTORICAL → jan_high → defillama/UNKNOWN

## 3. PUMP June ATL fees/revenue/buyback
- `(none)` / `` → `fees $806K/d · rev $618K/d · buyback/burn $442K/d` → `None`/compound_parent → `806000.0` → CURRENT_DYNAMIC → june_atl → defillama/UNKNOWN
- `June ATL` / `fees $806K/d · rev $618K/d · buyback/burn $442K/d` → `$806K/d` → `pump.fees.usd_per_day.june_atl`/fees_named_hist → `806000.0` → HISTORICAL → june_atl → defillama/UNKNOWN
- `June ATL` / `fees $806K/d · rev $618K/d · buyback/burn $442K/d` → `$618K/d` → `pump.revenue.usd_per_day.june_atl`/rev_named_hist → `618000.0` → HISTORICAL → june_atl → defillama/UNKNOWN
- `June ATL` / `fees $806K/d · rev $618K/d · buyback/burn $442K/d` → `$442K/d` → `pump.buyback.usd_per_day.june_atl`/buyback_named_hist → `442000.0` → HISTORICAL → june_atl → defillama/UNKNOWN

## 4. PUMP Now fees/revenue/buyback
- `(none)` / `` → `fees $1.3M/d · rev $998K/d · buyback/burn $738K/d` → `None`/compound_parent → `1300000.0` → CURRENT_DYNAMIC → now → defillama/UNKNOWN
- `Now` / `fees $1.3M/d · rev $998K/d · buyback/burn $738K/d` → `$1.3M/d` → `pump.fees.usd_per_day.current`/fees_per_day_now → `1300000.0` → CURRENT_DYNAMIC → now → defillama/UNKNOWN
- `Now` / `fees $1.3M/d · rev $998K/d · buyback/burn $738K/d` → `$998K/d` → `pump.revenue.usd_per_day.current`/revenue_per_day_now → `998000.0` → CURRENT_DYNAMIC → now → defillama/UNKNOWN
- `Now` / `fees $1.3M/d · rev $998K/d · buyback/burn $738K/d` → `$738K/d` → `pump.buyback.usd_per_day.current`/row_buyback_daily → `738000.0` → CURRENT_DYNAMIC → now → defillama/UNKNOWN

## 5. RENDER LAST 4 WKS
- `(none)` / `` → `LAST 4 WKS` → `None`/non_value_label → `UNKNOWN` → CURRENT_DYNAMIC → current → UNKNOWN/UNKNOWN

## 6. SOL print − / 7d +
- `(none)` / `` → `print − / 7d +` → `None`/non_value_label → `UNKNOWN` → CURRENT_DYNAMIC → 7d → Binance SOLUSDT funding/2026-08-11T16:00:00+00:00
- `(none)` / `` → `Binance fut/spot 24h ~6.8× · latest funding print 0.01%/8h.01%/8h.01%/8h.01%/8h.533e-05 · 7d mean 5.367e-05 (print ≠ multi-day mean).` → `None`/meta_key_evidence → `0.00533` → CURRENT_DYNAMIC → mean_7d → Binance SOLUSDT/2026-08-11T16:00:00+00:00
- `(none)` / `` → `Binance fut/spot ~6.8× · latest funding -5.533e-05 · 7d mean 5.367e-05 (print ≠ mean).` → `None`/compound_parent → `-5.533e-05` → CURRENT_DYNAMIC → mean_7d → SOL Stage 1 evidence/UNKNOWN
- `(none)` / `` → `fut/spot ~6.8× · latest print -5.533e-05 · 7d mean 5.367e-05` → `None`/compound_parent → `-5.533e-05` → CURRENT_DYNAMIC → mean_7d → Binance/2026-08-11T16:00:00+00:00

## 7. SOL ±3d means at anchors
- `(none)` / `` → `±3d means at anchor dates` → `None`/non_value_label → `UNKNOWN` → CURRENT_DYNAMIC → current → Binance SOLUSDT funding/2026-08-11T16:00:00+00:00
- `(none)` / `` → `±3d means at anchors` → `None`/non_value_label → `UNKNOWN` → CURRENT_DYNAMIC → current → Binance/2026-08-11T21:13:38.447286Z

## 8. SOL -5.533e-05
- `(none)` / `` → `-5.533e-05` → `sol.funding.rate.latest`/funding_latest → `-5.533e-05` → CURRENT_DYNAMIC → latest → Binance SOLUSDT funding/2026-08-11T16:00:00+00:00
- `(none)` / `` → `Binance fut/spot ~6.8× · latest funding -5.533e-05 · 7d mean 5.367e-05 (print ≠ mean).` → `None`/compound_parent → `-5.533e-05` → CURRENT_DYNAMIC → mean_7d → SOL Stage 1 evidence/UNKNOWN
- `(none)` / `` → `-5.533e-05` → `sol.funding.rate.latest`/funding_default_latest → `-5.533e-05` → CURRENT_DYNAMIC → current → Binance SOLUSDT funding/2026-08-11T16:00:00+00:00
- `(none)` / `` → `fut/spot ~6.8× · latest print -5.533e-05 · 7d mean 5.367e-05` → `None`/compound_parent → `-5.533e-05` → CURRENT_DYNAMIC → mean_7d → Binance/2026-08-11T16:00:00+00:00

## 9. PUMP bare 8h
- `OI / funding` / `OI $66.4M · funding -0.00001/8h` → `8h` → `None`/non_value_label → `UNKNOWN` → CURRENT_DYNAMIC → current → binance/UNKNOWN

## 10. NOS 855 run · 119,219 h/~31d
- `(none)` / `` → `855 run · 119,219 h/~31d` → `None`/compound_parent → `855.0` → CURRENT_DYNAMIC → 1d → Nosana blockchain-indexer/2026-08-12T16:25:04.142Z
- `Jobs + GPU-hours` / `855 run · 119,219 h/~31d` → `855` → `nos.jobs.running.count`/row_jobs_running → `855.0` → CURRENT_DYNAMIC → current → Nosana blockchain-indexer/2026-08-12T16:25:04.142Z
- `Jobs + GPU-hours` / `855 run · 119,219 h/~31d` → `119,219` → `nos.gpu_hours.approx_31d`/row_gpu_h → `119219.0` → CURRENT_DYNAMIC → current → Nosana blockchain-indexer/2026-08-12T16:25:04.142Z
- `(none)` / `` → `Running ~855 · queued ~40 · GPU-hours ~119,219 in ~31d window · last 7d ~26,533 vs prior 7d ~25,111 · ~30d jobs ~112,550 · markets 47. ~31d visible indexer window. Activity roughly stable-to-slightly-up. Longer-term growth beyond window = U` → `None`/meta_key_evidence → `855.0` → CURRENT_DYNAMIC → 30d → Nosana blockchain-indexer/2026-08-12T16:25:04.142Z
- `(none)` / `` → `855 / 40` → `None`/compound_parent → `855.0` → CURRENT_DYNAMIC → current → Nosana blockchain-indexer/2026-08-12T16:25:04.142Z
- `Running / queued` / `855 / 40` → `855` → `nos.jobs.running.count`/row_jobs_running → `855.0` → CURRENT_DYNAMIC → current → Nosana blockchain-indexer/2026-08-12T16:25:04.142Z
- `(none)` / `` → `119,219` → `nos.gpu_hours.approx_31d`/row_gpu_h → `119219.0` → CURRENT_DYNAMIC → 1d → Nosana blockchain-indexer/2026-08-12T16:25:04.142Z
- `(none)` / `` → `Jobs + GPU-hours real. Running ~855 · GPU-hours ~119,219 in ~31d. Throughput is the confirmation. Do not use indexer $ as revenue.` → `None`/meta_key_evidence → `UNKNOWN` → CURRENT_DYNAMIC → 1d → NOS Stage 1 evidence/UNKNOWN
- `(none)` / `` → `~855 jobs · ~119,219 GPU-h/~31d · ~35 nodes running.` → `None`/long_prose_container → `855.0` → CURRENT_DYNAMIC → 1d → Nosana indexer/2026-08-12

## 11. SOL 30d -1.00pp
- `(none)` / `` → `7d +3.76pp · 30d -1.00pp` → `None`/no_explicit_family → `3.76` → CURRENT_DYNAMIC → 30d → Binance/2026-08-11
- `(none)` / `` → `-1.00pp` → `None`/no_explicit_family → `-1.0` → CURRENT_DYNAMIC → 30d → Binance/2026-08-11
- `(none)` / `` → `-1.00pp` → `sol.rs.vs_sol.pp.30d`/rs_pp_30d → `-1.0` → CURRENT_DYNAMIC → 30d → Binance daily closes/2026-08-11T21:13:38.447286Z
- `(none)` / `` → `30d -1.00pp` → `sol.rs.vs_btc.pp.30d`/rs_pp_30d → `-1.0` → CURRENT_DYNAMIC → 30d → Binance/2026-08-11
- `(none)` / `` → `$98.28 · ~-66.5% from ATH · RS 7d +3.76pp / 30d -1.00pp` → `None`/compound_parent → `3.76` → CURRENT_DYNAMIC → 30d → CoinGecko + Binance/2026-08-11T21:13:38.447286Z
- `Price + SOL/BTC RS` / `$98.28 · ~-66.5% from ATH · RS 7d +3.76pp / 30d -1.00pp` → `30d -1.00pp` → `None`/no_explicit_family → `-1.0` → CURRENT_DYNAMIC → 30d → CoinGecko + Binance/2026-08-11T21:13:38.447286Z

## 12. $0.0... compact price/threshold
- `(none)` / `` → `$0.0...0288` → `bonk.price.usd.live`/live_px → `UNKNOWN` → CURRENT_DYNAMIC → current → UNKNOWN/UNKNOWN
- `(none)` / `` → `$0.0...0222` → `bonk.threshold.out.usd`/hold_out → `UNKNOWN` → STATIC_DECISION_THRESHOLD → current → UNKNOWN/UNKNOWN
- `(none)` / `` → `$0.0...0260` → `bonk.threshold.this_move.usd`/hold_shelf → `UNKNOWN` → STATIC_DECISION_THRESHOLD → current → UNKNOWN/UNKNOWN
- `(none)` / `` → `$0.0...0866` → `lockin.threshold.out.usd`/hold_out → `UNKNOWN` → STATIC_DECISION_THRESHOLD → current → UNKNOWN/UNKNOWN

## 13. HYPE 222.45M (22.2%)
- `(none)` / `` → `CG 22.2% · HL 29.9%` → `None`/compound_parent → `22.2` → CURRENT_DYNAMIC → current → HYPE Stage-1 evidence/2026-08-13T06:03:17Z
- `Circulating` / `CG 22.2% · HL 29.9%` → `22.2%` → `hype.supply.circulating.pct`/keyword_family → `22.2` → CURRENT_DYNAMIC → current → HYPE Stage-1 evidence/2026-08-13T06:03:17Z
- `(none)` / `` → `CG 222.45M (22.2% of 1B). Hyperliquid 298.99M (29.9%). HL formula: circulatingSupply = totalSupply − futureEmissions − sum(NCU). futureEmissions 412.44M. HyperLabs NCU 241.24M. 3m/6m/12m release UNKNOWN. Contributor supply remains a materia` → `None`/meta_key_evidence → `222450000.0` → CURRENT_DYNAMIC → current → HL tokenDetails + CoinGecko/2026-08-13T06:03:17Z
- `(none)` / `` → `222.45M (22.2%)` → `hype.supply.circulating.pct`/keyword_family → `22.2` → CURRENT_DYNAMIC → current → HYPE Stage-1 evidence/2026-08-13T06:03:17Z
- `(none)` / `` → `22.2%` → `hype.supply.circulating.pct`/keyword_family → `22.2` → CURRENT_DYNAMIC → current → HYPE Stage-1 evidence/2026-08-13T06:03:17Z
- `Supply / Unlocks` / `CG 22.2% · HL 29.9%` → `22.2%` → `hype.supply.circulating.pct`/keyword_family → `22.2` → CURRENT_DYNAMIC → current → HL tokenDetails + CoinGecko/2026-08-13T06:03:17Z
- `(none)` / `` → `CG 22.2% · Hyperliquid 29.9%. Both valid. Never pick one.` → `None`/compound_parent → `22.2` → CURRENT_DYNAMIC → current → HYPE Stage-1 evidence/2026-08-13
- `Circulating definition split` / `CG 22.2% · Hyperliquid 29.9%. Both valid. Never pick one.` → `22.2%` → `hype.supply.circulating.pct`/keyword_family → `22.2` → CURRENT_DYNAMIC → current → HYPE Stage-1 evidence/2026-08-13

## 14. SOL Stage1-historical TVL versus current TVL
- `(none)` / `` → `$5.65B` → `sol.tvl.usd.current`/row_tvl → `5650000000.0` → CURRENT_DYNAMIC → current → DefiLlama/2026-08-11T21:13:38.447286Z
- `(none)` / `` → `Fees now ~$600k/d vs ~$10.2M/d at Jan 2025 ATH window · TVL ~$4.8B vs ~$11.3B at ATH · price ~70% retraced from Binance ATH-day close.` → `None`/compound_parent → `600000.0` → CURRENT_DYNAMIC → current → DefiLlama + Binance (Stage1 historical)/2026-08-11T21:13:38.447286Z
- `Evidence` / `Fees now ~$600k/d vs ~$10.2M/d at Jan 2025 ATH window · TVL ~$4.8B vs ~$11.3B at` → `$4.8B` → `sol.tvl.usd.stage1`/atomic_span_forced → `4800000000.0` → HISTORICAL → stage1 → DefiLlama + Binance (Stage1 historical)/2026-08-11T21:13:38.447286Z
- `Evidence` / `Fees now ~$600k/d vs ~$10.2M/d at Jan 2025 ATH window · TVL ~$4.8B vs ~$11.3B at` → `$11.3B` → `sol.tvl.usd.jan_2025`/atomic_span_forced → `11300000000.0` → HISTORICAL → stage1 → DefiLlama + Binance (Stage1 historical)/2026-08-11T21:13:38.447286Z
- `(none)` / `` → `TVL $5.65B (#4) · fees 30d mean $516,236.10/d · TPS snapshot ~4198.0 all / ~2578.0 non-vote. DAU series UNKNOWN.` → `None`/compound_parent → `5650000000.0` → CURRENT_DYNAMIC → mean_30d → DefiLlama + Solana RPC/2026-08-11T21:13:38.447286Z
- `Evidence` / `TVL $5.65B (#4) · fees 30d mean $516,236.10/d · TPS snapshot ~4198.0 all / ~2578` → `$5.65B` → `sol.tvl.usd.current`/atomic_span_forced → `5650000000.0` → CURRENT_DYNAMIC → current → DefiLlama + Solana RPC/2026-08-11T21:13:38.447286Z
- `(none)` / `` → `~$11.30B (Stage1 historical)` → `None`/no_explicit_family → `11300000000.0` → CURRENT_DYNAMIC → jan_2025 → DefiLlama/2026-08-11T21:13:38.447286Z
- `(none)` / `` → `~$4.80B now / ~$8.88B at June local low (Stage1)` → `None`/long_prose_container → `4800000000.0` → CURRENT_DYNAMIC → stage1 → DefiLlama/2026-08-11T21:13:38.447286Z
- `(none)` / `` → `$4.80B` → `sol.tvl.usd.current`/row_tvl → `4800000000.0` → CURRENT_DYNAMIC → current → DefiLlama/2026-08-11T21:13:38.447286Z
- `(none)` / `` → `TVL $4.80B · stables $15.64B · DEX Sol/Eth L1 1.762× (7d)` → `None`/compound_parent → `4800000000.0` → CURRENT_DYNAMIC → 7d → DefiLlama/2026-08-11T21:13:38.447286Z
- `TVL / stables / DEX` / `TVL $4.80B · stables $15.64B · DEX Sol/Eth L1 1.762× (7d)` → `$4.80B` → `sol.tvl.usd.current`/atomic_span_forced → `4800000000.0` → CURRENT_DYNAMIC → current → DefiLlama/2026-08-11T21:13:38.447286Z

