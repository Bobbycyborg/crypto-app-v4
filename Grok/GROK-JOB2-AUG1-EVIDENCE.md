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
| FART | 31 | 27 | 3 (Fart21, Fart45, Raydium AMM Authority) | 1 (Wintermute, 266 txs) | 3 | batch 1. FART real 1 Aug not overwritten. |
| LOCKIN | 31 | 30 (Lockin21–50) | 1 (Raydium AMM Authority, 301 txs) | 0 | 1 | batch 2. Reconstructed 0s: Lockin21, 23, 34, 47, 50. |
| RETARDIO | 37 | 36 (Retardio21–56) | 1 (Raydium AMM Authority, 301 txs) | 0 | 1 | batch 3. Reconstructed 0s: Retardio31, 46, 52. |
| SPX | 40 | 38 | 2 (Orca Whirlpool, Raydium AMM Authority) | 0 | 2 | batch 4. Binance CEX was thin (5 txs) so proved, not dest-watch. Reconstructed 0: Spx40. |
| 2Z | 46 | 39 | 2 (TwoZ56, Raydium CLMM; both gt300) | 5 (Bybit, Bithumb, OKX-C68a, Coinbase, Binance) | 2 | batch 5. Gate.io (11 txs) + second OKX-8wM4 (7 txs) thin so proved. No reconstructed 0s. |
| GRASS | 57 | 0 | 0 | 0 | 57 | SKIP — Oliver: GRASS dead. Do not walk / splice. |
| IO | 57 | 0 | 0 | 0 | 57 | walking in parallel (separate proofs/log) |
| RENDER | 62 | 0 | 0 | 0 | 62 | walking in parallel |
| BONK | 73 | 0 | 0 | 0 | 73 | walking in parallel |
| NOS | 75 | 0 | 0 | 0 | 75 | walking in parallel |
| GIGA | 77 | 0 | 0 | 0 | 77 | walking in parallel |
| **total** | **586** | **170 on page** (27+30+36+38+39) | **9** | **6** | **415 on page** | GRASS 57 of leftover are skip |

PUMP / ORCA / DRIFT had no fake27. HOM not present. G2 leftover 16 not in the fake27 set and not walked.

## What landed on the page

### Batch 1 (eb21ce2)
- FART: 27 new real 1 Aug stamps. Old real 1 Aug kept. 3 thick whales still `as_of_now`. Wintermute → dest-watch `MM book`.
- JS `since 1 Aug` percent row. Label still `1 Aug`.

### Batch 2 (332acd8)
- LOCKIN: 30 new real 1 Aug stamps (Lockin21–50). FART not touched.
- Note: `e657cb5` (also titled batch 2) spliced RETARDIO 21–27 mid-flight; batch 3 superseded that with the full RETARDIO splice.

### Batch 3 (2b0c655)
- RETARDIO: 36 new real 1 Aug stamps (Retardio21–56). Raydium left `as_of_now` (DEFER gt300).
- LOCKIN Raydium walked DEFER gt300.

### Batch 4 (1a66bce / 84f7e2c)
- SPX: 38 new real 1 Aug stamps. Orca Whirlpool + Raydium AMM Authority left `as_of_now` (DEFER gt300, no UNKNOWN).
- FART / LOCKIN / RETARDIO spliced boxes not overwritten.
- Row label still `1 Aug`. JS row already present.

### Batch 5 (this commit)
- 2Z: 39 new real 1 Aug stamps. TwoZ56 + Raydium CLMM left `as_of_now` (DEFER gt300, no UNKNOWN).
- Dest-watch `CEX book`: Bybit, Bithumb, OKX (C68a6RCG, 301 txs), Coinbase, Binance.
- Gate.io and the second OKX (8wM44Ryv, 7 txs) were thin so proved, not dest-watch.
- FART / LOCKIN / RETARDIO / SPX real 1 Aug counts not dropped. Label still `1 Aug`. JS row present.
- No reconstructed 0s on 2Z.

## What this resume did / did not

Did:
- Pulled origin/main. No rebase.
- Did not start over. Waited for the already-running 2Z public-RPC walk (pid 295321) to finish; did not start a second 2Z walk.
- 2Z done: proved=39 defer=7 (5 dest-watch + 2 whale) err=0. 429 backoff persist-and-continue.
- Remaining live coins (IO, RENDER, BONK, NOS, GIGA) spreading in parallel with separate proofs/logs. Not walked sequentially after 2Z. Not launched as duplicates from this splice owner.
- Skipped GRASS / DRIFT / PUMP / ORCA.
- Left reconstructed 0s only where the walk proved them.
- Persist each proof before splice. Sleep/backoff on 429.

Did not:
- Did not invent numbers or guess zeros.
- Did not add wallets or change config address lists.
- Did not touch HOM or hold-card look.
- Did not start Job 3.
- Did not FAIL Job 1.
- Did not walk or splice GRASS.
- Did not stamp UNKNOWN on thick whales.

## Files touched

- `index-v4.html` — siren-watch-data for FART (batch 1, left alone after), LOCKIN, RETARDIO, SPX, 2Z. JS row from batch 1.
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md` — this pack

## Files left alone

- `config/siren-wallets.json` / `config/siren-wallet-tags.json`
- HOM (not present)
- DRIFT / GRASS / PUMP / ORCA
- FART / LOCKIN / RETARDIO / SPX real 1 Aug stamps
- Unfinished parallel coins this batch (IO, RENDER, BONK, NOS, GIGA)
- No invented wallets
- `data/cache/job2-aug1-proofs.json` local persist (gitignored)

## Persist

Each proved 1 Aug written immediately to `data/cache/job2-aug1-proofs.json` (and box `/workspace/job2-aug1-proofs.json`) before splice.

## Commits

- Batch 1: `eb21ce2`
- Batch 2: `332acd8` (LOCKIN). `e657cb5` also titled batch 2 (partial RETARDIO 21–27) from a parallel splice; superseded by batch 3.
- Batch 3: `2b0c655` (RETARDIO 36)
- Batch 4: `1a66bce` / `84f7e2c` (SPX 38)
- Batch 5: this commit (2Z 39). Hash: read `git log -1`.

## Status

**NOT DONE.** Live remaining: IO, RENDER, BONK, NOS, GIGA (parallel walks). GRASS skipped. Honest DEFERs left as_of_now: FART 3, LOCKIN Raydium, RETARDIO Raydium, SPX Orca Whirlpool + Raydium, 2Z TwoZ56 + Raydium CLMM. Grok has not marked this complete.
