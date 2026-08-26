# JOB-V4-2 source audit

Pre-coding inventory of COLLECT sources.

| source_key | metrics_count | machine-readable | authentication | endpoint/protocol known | expected requests/run |
|---|---|---|---|---|---|
| alternative_me | 1 | official JSON API | none | yes | 1 |
| binance | 24 | official JSON API | none | yes | 22 |
| coingecko | 29 | official JSON API | optional env COINGECKO_DEMO_API_KEY / COINGECKO_PRO_API_KEY; public allowed | yes | 1 |
| defillama | 9 | official JSON API | none | yes | 7 |
| dexscreener | 1 | official JSON API | none | yes | 1 |
| farside | 9 | official HTML tables (no JSON API) | none (HTML) | yes | 3 |
| hyperliquid | 3 | official JSON API | none | yes | 1 |
| io_explorer | 2 | official JSON API | none | yes | 1 |
| nosana | 5 | official JSON API | none | yes | 1 |
| render_foundation | 6 | official JSON API | none | yes | 3 |
| solana_rpc | 4 | official JSON API | none (public RPC; not wallet) | yes | 3 |
| zcash_explorer | 2 | official JSON API | none | yes | 1 |

Total unique source requests per live run: 45

