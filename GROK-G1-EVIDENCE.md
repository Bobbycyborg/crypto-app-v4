# G1 EVIDENCE PACK

**Job:** G1. Seed proved dests already hunted  
**Date:** 26 Aug 2026  
**Owner:** Grok  
**Status:** NOT DONE. Grok has not marked this complete. CGPT reviews this pack + the diff.

## Dummy
V4 can now name Wintermute and DWF when a watched wallet sends there. Three proved MM dests were missing. The MM folder is not on GitHub, so the checker could not read them. That is fixed. Any send still raises eyes. Desk name is the loud one.

## Before
- `config/known-cex-wallets.json`: 301 wallets (227 cex, 8 mm, 64 custody, 2 treasury)
- Official Binance Solana hot/cold 19: already present (0 missing)
- OKX / Bybit / Bitfinex official Solana dests: already present
- Wintermute Solana `MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa`: present as `type=mm` (CEX map skipped it)
- `reports/shared-mm-registry/shared-entity-wallet-registry.json` on V4: **FileNotFoundError**
- Dest loader MM map: **could not load**
- Wintermute dest resolve on V4: **fail** (MM path missing; type=mm not read)

## After
- CEX map: **227**
- MM map: **4** Solana HIGH/MEDIUM
- Wintermute `MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa` resolves to **Wintermute**
- DWF `HwDkuDCUipJHHKodBBCjffFvrjhmd4iVVh7fq25fShvt` resolves to **DWF Labs**
- `known-cex` wallet count: **304** (+3). Not tens of thousands.

## Added (only these three)

| entity | chain | type | confidence | address | source |
|---|---|---|---|---|---|
| Wintermute | solana | mm | MEDIUM | `5sTQ5ih7xtctBhMXHr3f1aWdaXazWrWfoehqWdqWnTFP` | `crypto-app-v3/reports/shared-mm-registry/shared-entity-wallet-registry.json` |
| Wintermute | solana | mm | MEDIUM | `BMnT51N4iSNhWU5PyFFgWwFvN1jgaiiDr9ZHgnkm3iLJ` | same |
| DWF Labs | solana | mm | HIGH | `HwDkuDCUipJHHKodBBCjffFvrjhmd4iVVh7fq25fShvt` | same |

Also wrote `config/known-mm-wallets.json` with those four Solana MM dests (the three new + already-known Wintermute HIGH) so V4 does not need a reports folder.

## Already present (count only)
- Binance official hot/cold: 19
- OKX: 164
- Bybit: 30
- Bitfinex: 4
- Wintermute HIGH Solana `MfDuWeq…`: already in known-cex
- 22 watched bag wallets that are dests already had desk tags. None of the three new dests are watch wallets. `siren-wallet-tags.json` unchanged.

## Skipped / holes (still holes)
- 60,454 official Binance user deposit keys: **not seeded**
- Gate / Kraken / Coinbase Solana dests: **none published, none invented**
- `5tzFki…P1P` stays MED Solscan attribution
- Jump Trading Solana LOW: **not seeded**
- ETH MM dests already in known-cex as `0x…` / `type=mm`: dest loader still skips `0x` for the Solana hop map (this job is Solana dest-watch)

## Files touched
- `config/known-cex-wallets.json`
- `config/known-mm-wallets.json` (new)
- `lib/v3/siren_watch.py` (dest loader only)
- `GROK-G1-BRIEF.md`
- `GROK-G1-EVIDENCE.md`

## Files proved untouched (must stay that way in the commit)
- `config/siren-wallets.json`
- `config/siren-wallet-tags.json`
- `index-v4.html`
- `metrics/`
- `tests/job1/`
- V3 files
- 1 Aug stamps

## Loader change (what, not a rewrite)
`_load_dest_tags()` now:
1. Puts `type=="cex"` in the CEX map (same as before).
2. Puts Solana `type=="mm"` from known-cex in the MM map (new; skips `0x`).
3. Reads `config/known-mm-wallets.json` if present.
4. Still reads the old reports MM file **if** it exists locally.
5. Does not change hop following, loud rule, 1 Aug, or UI chrome.

## CGPT check list
1. Any added address not in the v3 MM registry? (must be no)
2. 60k deposit list seeded? (must be no)
3. Does V4 name Wintermute without `reports/` on GitHub? (must be yes)
4. `siren-wallets.json` unchanged? (must be yes)
5. `index-v4.html` / `metrics/` unchanged in this commit? (must be yes)
6. Gate / Kraken / Coinbase Solana invented? (must be no)
7. Did Grok mark the job done? (must be no — this file says NOT DONE)
8. Before/after counts present? (yes)

If FAIL: write FAIL + the line. Do not brief a new job.
