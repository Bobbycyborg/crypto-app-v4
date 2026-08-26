# V4 metric_id naming

Pattern: `{asset}.{family}.{measure}[.{window}]`

Banned production families: `captured`, `usd_figure`, `pct_figure`, `pp_figure`.

Windows: `current`, `1d`, `7d`, `30d`, `90d`, `180d`, `ath`, `all_time`, `aug1`.

Same meaning, many slots = one ID.
Different window or definition = different ID.

`pump.buyback.usd.7d` = trailing-week total only.
`pump.buyback.usd.1d` = latest daily observation.
Daily range text is not the weekly total.

Hold-card-only tickers use their real asset (`orca.price.usd.current`), never `market.*`.
