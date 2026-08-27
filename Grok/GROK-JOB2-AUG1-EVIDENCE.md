# Job 2 — reconstruct 1 Aug 2026 00:00 UTC on new dest-watch boxes

**Date:** 27 Aug 2026
**Owner:** Grok
**Status:** NOT DONE. Grok has not marked this complete. Partial walk. CGPT reviews pack + diff only.

Official start = 1 Aug 2026 00:00 UTC only. Formula: `aug1 = now + this-mint outs − this-mint ins` since that instant, ATA of that coin on that wallet. No 10 Aug fallback. No guessed zeros. No UNKNOWN written as a new whale stamp. G2 leftover 16 not walked.

Helius key stayed on the Mac (`config/helius.local.env`, never pasted). Helius returned **max usage reached** after the first AMM probe, so the walk used the existing public-RPC ATA path from `scripts/backfill_siren_aug1.py` (`getSignaturesForAddress` on the ATA + `getTransaction` mint delta). Same formula.

## The lie

New dest-watch boxes from Job 1 had `aug1_status=as_of_now` and `aug1_as_of=2026-08-27T00:00:00Z` with `aug1 == balance` (today’s pile on the 1 Aug line). 586 boxes. Existing real 1 Aug boxes left alone.

## Per coin (this pack)

| Coin | fake27 | proved 1 Aug (this job) | DEFER whale (left as_of_now) | DEFER dest-watch (CEX/MM book) | still as_of_now |
|---|---:|---:|---:|---:|---:|
| FART | 31 | 27 | 3 (Fart21, Fart45, Raydium AMM Authority) | 1 (Wintermute, 266 txs) | 3 |
| LOCKIN | 31 | 0 | 0 | 0 | 31 |
| RETARDIO | 37 | 0 | 0 | 0 | 37 |
| SPX | 40 | 0 | 0 | 0 | 40 |
| 2Z | 46 | 0 | 0 | 0 | 46 |
| GRASS | 57 | 0 | 0 | 0 | 57 |
| IO | 57 | 0 | 0 | 0 | 57 |
| RENDER | 62 | 0 | 0 | 0 | 62 |
| BONK | 73 | 0 | 0 | 0 | 73 |
| NOS | 75 | 0 | 0 | 0 | 75 |
| GIGA | 77 | 0 | 0 | 0 | 77 |
| **total** | **586** | **27** | **3** | **1** | **559** |

PUMP / ORCA / DRIFT had no fake27. HOM not present. G2 leftover 16 not in the fake27 set and not walked.

## What landed on the page (batch 1)

- FART: 27 new real 1 Aug stamps (`proved` or `unmoved_equals_now`, `aug1_as_of=2026-08-01T00:00:00Z`). Old 16 real 1 Aug kept. 3 thick whales still `as_of_now` (DEFER, no UNKNOWN stamp). Wintermute new box converted to dest-watch `MM book` (same pattern as the older Wintermute row).
- now / last_out / left_24h kept.
- Hardcoded row label still `1 Aug` (not renamed 27 Aug).
- Tiny JS row next to the existing siren popup renderer: if a box has a real 1 Aug (`proved` / `unmoved_equals_now` + `2026-08-01`) AND a real now, show `since 1 Aug` with `(now-aug1)/aug1` as `−12%` / `+8%`. Same `siren-box-row` classes. Live.

## Files touched

- `index-v4.html` — siren-watch-data FART boxes + one JS row. No other coins spliced this batch.
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md` — this pack

## Files left alone

- `config/siren-wallets.json` / `config/siren-wallet-tags.json` (addresses and tags stay)
- HOM (not present)
- DRIFT
- Other baked coins’ boxes this batch
- No invented wallets
- `data/cache/job2-aug1-proofs.json` local persist (gitignored)

## Persist

Each proved 1 Aug written immediately to `data/cache/job2-aug1-proofs.json` before splice.

## Commits

- Batch 1: this commit (FART + JS row + pack). Hash: read `git log -1`.

## Status

**NOT DONE.** 559 fake27 boxes still on the 27 Aug lie. Walk continues coin by coin. Grok has not marked this complete.
