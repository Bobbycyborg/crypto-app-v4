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

Helius maxed; public-RPC ATA path (`getSignaturesForAddress` + `getTransaction` mint delta). Persist each proof before splice. Sleep/backoff on 429.

## The lie

586 new dest-watch boxes had today pile on the 1 Aug line (`as_of_now` / `2026-08-27`). Existing real 1 Aug left alone.

## Per coin (this pack)

| Coin | fake27 | proved 1 Aug (this job, on page) | DEFER whale (left as_of_now) | DEFER dest-watch (CEX/MM) | still as_of_now | notes |
|---|---:|---:|---:|---:|---:|---|
| FART | 31 | 27 | 3 | 1 | 3 | batch 1. FART real 1 Aug not overwritten. |
| LOCKIN | 31 | 30 | 1 (Raydium) | 0 | 1 | batch 2 |
| RETARDIO | 37 | 36 | 1 (Raydium) | 0 | 1 | batch 3 |
| SPX | 40 | 38 | 2 (Orca Whirlpool, Raydium) | 0 | 2 | batch 4 |
| 2Z | 46 | 39 | 2 (TwoZ56, Raydium CLMM) | 5 | 2 | batch 5 |
| IO | 57 | 55 | 0 | 1 | 1 (Jupiter, not yet walked) | parallel + this resume. Jupiter leftover. |
| NOS | 75 | 70 | 3 (2x Raydium CLMM, Nos67) | 2 | 3 | walked/spliced. Honest DEFER. |
| RENDER | 62 | 21 | 0 | 5 | 35 | this batch spliced proved Render24–38 + dest-watch. Rest still walking. |
| BONK | 73 | 18 | 0 | 0 | 52 | Bonk34 spliced this batch; rest still walking. |
| GIGA | 77 | 43 | 0 | 0 | 34 | Giga34–63 spliced this batch; rest still walking. |
| GRASS | 57 | 0 | 0 | 0 | 57 | SKIP — Oliver: GRASS dead. |
| **total** | **586** | **377 on page** | **12** | **14** | **191 on page** | GRASS 57 of leftover are skip |

PUMP / ORCA / DRIFT no fake27. HOM not present. G2 leftover 16 not walked.

## What this resume did / did not

Did:
- Pulled origin/main. No rebase. Did not start over.
- Spliced already-proved LOCKIN first, then walked RETARDIO / SPX / 2Z / IO.
- Parallel commits also landed batches 2–7 (same job, same persist). This resume did not overwrite those splices.
- This batch: spliced unspliced proved RENDER / GIGA / BONK from persist onto current HEAD.
- Skipped GRASS / DRIFT / PUMP / ORCA.
- Reconstructed 0s only when walk-proved.
- Persist each proof. Backoff on 429.

Did not:
- Invent numbers or guess zeros.
- Add wallets / change config address lists.
- Touch HOM or hold-card look.
- Start Job 3.
- FAIL Job 1.
- Walk or splice GRASS.

## Files touched

- `index-v4.html` — siren-watch-data only (RENDER / GIGA / BONK this commit). JS `since 1 Aug` row from batch 1. Label still `1 Aug`.
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md` — this pack

## Files left alone

- config address lists
- HOM / DRIFT / GRASS / PUMP / ORCA
- FART real 1 Aug
- `data/cache/job2-aug1-proofs.json` local persist (gitignored)

## Commits

- Batch 1: `eb21ce2` FART 27 + JS row
- Batch 2: `332acd8` LOCKIN 30; `e657cb5` partial RETARDIO (superseded)
- Batch 3: `2b0c655` RETARDIO 36
- Batch 4: `84f7e2c` / `1a66bce` SPX 38
- Batch 5: `baf3ee7` / `a625a6a` / `bcc4953` 2Z
- Batch 6–7: `d63223d` / `8b207fc` (parallel: IO / NOS / partial others)
- This commit: RENDER + GIGA + BONK splice from persist. Hash: read `git log -1`.

## Status

**NOT DONE.** Live leftover still `as_of_now` and not yet walked or still walking: RENDER 35, BONK 52, GIGA 34, IO Jupiter 1. Honest DEFERs left as_of_now on FART/LOCKIN/RETARDIO/SPX/2Z/NOS. GRASS skipped. Grok has not marked this complete.
