# Job 2 — reconstruct 1 Aug 2026 00:00 UTC on new dest-watch boxes

**Date:** 27 Aug 2026
**Owner:** Grok
**Status:** NOT DONE. Grok has not marked this complete. Partial walk. CGPT reviews pack + diff only.

Official start = 1 Aug 2026 00:00 UTC only. Formula: `aug1 = now + this-mint outs − this-mint ins` since that instant, ATA of that coin on that wallet. No 10 Aug fallback. No guessed zeros (a reconstructed 0 is only written when the walk proved the wallet held none on 1 Aug). No UNKNOWN written as a new whale stamp. G2 leftover 16 not walked.

Oliver 27 Aug:
- 1 Aug stays 1 Aug. Do not rename the row 27 Aug.
- Last sell stays. now / last_out / left_24h kept.
- % gone since 1 Aug only when both 1 Aug and now are real.
- GRASS is DEAD — do not walk GRASS, do not splice GRASS. DRIFT stays out.
- HOM not present. PUMP / ORCA had no fake27.

Helius key stayed on the Mac (`config/helius.local.env`, never pasted). Helius returned **max usage reached**, so the walk used the existing public-RPC ATA path from `scripts/backfill_siren_aug1.py`. Same formula. Persist each proof immediately.

## The lie

New dest-watch boxes had `aug1_status=as_of_now` / `aug1_as_of=2026-08-27T00:00:00Z` with `aug1 == balance`. 586 boxes.

## Per coin

| Coin | fake27 | proved 1 Aug (this job) | DEFER whale (left as_of_now) | DEFER dest-watch | still as_of_now |
|---|---:|---:|---:|---:|---:|
| FART | 31 | 27 | 3 (Fart21, Fart45, Raydium AMM Authority) | 1 (Wintermute → MM book) | 3 |
| LOCKIN | 31 | 30 | 1 (Raydium AMM Authority) | 0 | 1 |
| RETARDIO | 37 | 36 | 1 (Raydium AMM Authority) | 0 | 1 |
| SPX | 40 | 38 | 2 (Raydium AMM Authority, Orca Whirlpool) | 0 | 2 |
| 2Z | 46 | 0 | 0 | 0 | 46 |
| GRASS | 57 | 0 | 0 | 0 | 57 (SKIP — dead) |
| IO | 57 | 0 | 0 | 0 | 57 |
| RENDER | 62 | 0 | 0 | 0 | 62 |
| BONK | 73 | 0 | 0 | 0 | 73 |
| NOS | 75 | 0 | 0 | 0 | 75 |
| GIGA | 77 | 0 | 0 | 0 | 77 |
| **total** | **586** | **131 on page** | **7** | **1** | **455 on page** (57 of those are GRASS skip) |

PUMP / ORCA / DRIFT: no fake27. G2 leftover 16 not walked.

## What landed on the page

- Hardcoded row label still `1 Aug`.
- JS `since 1 Aug` percent row is live (`proved` / `unmoved_equals_now` + `2026-08-01` + real now). Sign is pile change: `−12%` if smaller now, `+8%` if grown.
- now / last_out / left_24h kept.
- Existing real 1 Aug boxes left alone.
- Thick whales left `as_of_now` (DEFER, no UNKNOWN stamp). Wintermute FART → dest-watch `MM book`.
- SPX Binance (thin CEX) reconstructed. SPX Meteora DLMM unmoved.

## Files touched

- `index-v4.html` — siren-watch-data boxes + JS row only
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md` — this pack

## Files left alone

- `config/siren-wallets.json` / `config/siren-wallet-tags.json`
- HOM, DRIFT, GRASS, PUMP, ORCA
- No invented wallets
- `data/cache/job2-aug1-proofs.json` local persist (gitignored)

## Commits

- `eb21ce2` batch 1 — FART + JS row
- `332acd8` / `e657cb5` batch 2 — LOCKIN
- `2b0c655` batch 3 — RETARDIO
- this commit batch 4 — SPX recover+splice

## Status

**NOT DONE.** Still to walk: 2Z 46, IO 57, RENDER 62, BONK 73, NOS 75, GIGA 77 (390). GRASS 57 skipped. 7 DEFER whales still as_of_now. Grok has not marked this complete.
