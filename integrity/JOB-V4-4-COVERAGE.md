# JOB V4-4 Coverage

## Checker package

- `integrity/check_report.py` — CLI entry
- `integrity/build_report_contract.py` — contract builder
- `integrity/model.py`, `numeric.py`, `extract.py`, `rules.py`

## Categories (12)

01_input_lineage · 02_active_asset_coverage · 03_canonical_metric_coverage ·
04_rendered_binding_consistency · 05_duplicate_consistency · 06_ath_drawdown_arithmetic ·
07_moving_average_language · 08_relative_strength_language · 09_freshness_asof_consistency ·
10_tooltip_visible_visual_agreement · 11_derived_metric_arithmetic · 12_permanent_regressions

## Derive rules (4)

- btc.leverage.x.current (RATIO)
- global.leverage.x.current (RATIO)
- sol.supply.net_change.tokens.per_year (SUBTRACT)
- zec.leverage.x.current (RATIO)

## Bindings

418 Job3 bindings checked via anchor_before + source_literal + anchor_after.

## Active assets

btc, sol, render, pump, io, nos, fartcoin, spx6900, zec, hype

Excluded: ray, grass, drift
