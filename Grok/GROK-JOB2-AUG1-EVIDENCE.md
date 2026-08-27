# Job 2 — reconstruct 1 Aug 2026 00:00 UTC on new dest-watch boxes

**Date:** 27 Aug 2026
**Owner:** Grok
**Status:** NOT DONE. Grok has not marked this complete. Partial walk + splice. CGPT reviews pack + diff only.

Dummy objective: official start = 1 Aug 2026 00:00 UTC only. Formula: `aug1 = now + this-mint outs − this-mint ins` since that instant, ATA of that coin on that wallet. No 10 Aug fallback. No guessed zeros. A reconstructed 0 is OK only when the walk proved the wallet held none on 1 Aug and received later. No UNKNOWN written as a new whale stamp. G2 leftover 16 not walked.

Oliver 27 Aug:
- Job 1 is CGPT PASS / CLOSED. Out of scope. Do not FAIL Job 1.
- 1 Aug stays 1 Aug (start of this move). Do not rename the row 27 Aug.
- Last sell stays. now / last_out / left_24h kept.
- % gone since 1 Aug only when both 1 Aug and now are real.
- GRASS is DEAD (same as DRIFT) — do not walk GRASS, do not splice GRASS, skip all GRASS queue items. DRIFT stays out.
- Skip PUMP / ORCA (no fake27 / dead). HOM not present.

Helius key stayed on the Mac (`config/helius.local.env`, never pasted). Helius returned **max usage reached**, so the walk used the existing public-RPC ATA path from `scripts/backfill_siren_aug1.py` (`getSignaturesForAddress` on the ATA + `getTransaction` mint delta). Same formula. Persist each proof before splice. Sleep/backoff on 429.

## The lie

New dest-watch boxes from Job 1 had `aug1_status=as_of_now` and `aug1_as_of=2026-08-27T00:00:00Z` with `aug1 == balance` (today’s pile on the 1 Aug line). 586 boxes. Existing real 1 Aug boxes left alone.

## Per coin (this pack)

| Coin | fake27 | proved 1 Aug (this job) | DEFER whale (left as_of_now) | DEFER dest-watch (CEX/MM book) | still as_of_now | notes |
|---|---:|---:|---:|---:|---:|---|
| FART | 31 | 27 | 3 (Fart21, Fart45, Raydium AMM Authority) | 1 (Wintermute) | 3 | batch 1. FART real 1 Aug not overwritten. |
| LOCKIN | 31 | 30 | 1 (Raydium AMM Authority) | 0 | 1 | batch 2. Reconstructed 0s: Lockin21, 23, 34, 47, 50. |
| RETARDIO | 37 | 36 | 1 (Raydium AMM Authority) | 0 | 1 | batch 3. Reconstructed 0s: Retardio31, 46, 52. |
| SPX | 40 | 38 | 2 (Orca Whirlpool, Raydium AMM Authority) | 0 | 2 | batch 4. Reconstructed 0: Spx40. |
| 2Z | 46 | 39 | 2 (TwoZ56, Raydium CLMM) | 5 (Bybit, Bithumb, OKX, Coinbase, Binance) | 2 | batch 5. Thin CEX (Gate.io + one OKX) proved. |
| GRASS | 57 | 0 | 0 | 0 | 57 | SKIP — Oliver: GRASS dead. |
| IO | 57 | 0 | 0 | 0 | 57 | walking now |
| RENDER | 62 | 0 | 0 | 0 | 62 | not walked |
| BONK | 73 | 0 | 0 | 0 | 73 | not walked |
| NOS | 75 | 0 | 0 | 0 | 75 | not walked |
| GIGA | 77 | 0 | 0 | 0 | 77 | not walked |
| **total** | **586** | **170 on page** (27+30+36+38+39) | **9** | **6** | **415 on page** | GRASS 57 of leftover are skip |

PUMP / ORCA / DRIFT had no fake27. HOM not present. G2 leftover 16 not walked.

## What landed on the page

### Batch 1 (eb21ce2)
FART 27 + JS `since 1 Aug` row. Label still `1 Aug`.

### Batch 2 (332acd8)
LOCKIN 30. `e657cb5` also titled batch 2 (partial RETARDIO); superseded by batch 3.

### Batch 3 (2b0c655)
RETARDIO 36. LOCKIN Raydium DEFER recorded.

### Batch 4 (1a66bce / 84f7e2c)
SPX 38. Parallel batch-4 commits; counts match.

### Batch 5 (this commit)
- 2Z: 39 new real 1 Aug stamps. 5 thick CEX → dest-watch `CEX book`. TwoZ56 + Raydium CLMM left `as_of_now` (DEFER gt300, no UNKNOWN).
- Prior coins not overwritten. Row label still `1 Aug`.

## What this resume did / did not

Did: resume from persist (no start-over); splice LOCKIN first; walk remaining live coins; skip GRASS/DRIFT/PUMP/ORCA; persist each proof; backoff on 429; reconstructed 0s only when walk-proved.

Did not: invent numbers; add wallets; change config address lists; touch HOM / hold-card look; start Job 3; FAIL Job 1; walk or splice GRASS.

## Files touched

- `index-v4.html` — siren-watch-data for LOCKIN / RETARDIO / SPX / 2Z this resume. JS row from batch 1.
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md` — this pack

## Files left alone

- `config/siren-wallets.json` / `config/siren-wallet-tags.json`
- HOM / DRIFT / GRASS / PUMP / ORCA
- FART real 1 Aug stamps
- Unwalked coins
- `data/cache/job2-aug1-proofs.json` local persist (gitignored)

## Commits

- Batch 1: `eb21ce2`
- Batch 2: `332acd8` (LOCKIN). `e657cb5` partial RETARDIO (superseded).
- Batch 3: `2b0c655` (RETARDIO 36)
- Batch 4: `84f7e2c` / `1a66bce` (SPX 38)
- Batch 5: this commit (2Z 39 + 5 dest-watch). Hash: read `git log -1`.

## Status

**NOT DONE.** Live remaining: IO (walking), RENDER, BONK, NOS, GIGA. GRASS skipped. Grok has not marked this complete.
