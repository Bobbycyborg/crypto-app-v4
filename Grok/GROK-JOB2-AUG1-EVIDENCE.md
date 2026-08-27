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
| FART | 31 | 27 | 3 (Fart21, Fart45, Raydium AMM Authority) | 1 (Wintermute, 266 txs) | 3 | batch 1 spliced. FART real 1 Aug not overwritten. |
| LOCKIN | 31 | 30 (Lockin21–50) | 0 | 0 | 1 (Raydium AMM Authority, not yet walked) | batch 2 spliced. 5 reconstructed 0s are walk-proved (held none 1 Aug, received later): Lockin21, 23, 34, 47, 50. |
| RETARDIO | 37 | 7 walked unspliced (Retardio21–27) | 0 | 0 | 37 | 21–27 proved in persist, not yet on the page. Walk died on 429 at Retardio28. |
| SPX | 40 | 0 | 0 | 0 | 40 | not walked |
| 2Z | 46 | 0 | 0 | 0 | 46 | not walked |
| GRASS | 57 | 0 | 0 | 0 | 57 | SKIP — Oliver: GRASS dead. Do not walk / splice. |
| IO | 57 | 0 | 0 | 0 | 57 | not walked |
| RENDER | 62 | 0 | 0 | 0 | 62 | not walked |
| BONK | 73 | 0 | 0 | 0 | 73 | not walked |
| NOS | 75 | 0 | 0 | 0 | 75 | not walked |
| GIGA | 77 | 0 | 0 | 0 | 77 | not walked |
| **total** | **586** | **57 on page** (27 FART + 30 LOCKIN) | **3** | **1** | **529 on page** (559 − 30 LOCKIN spliced; GRASS 57 of those are skip) | |

PUMP / ORCA / DRIFT had no fake27. HOM not present. G2 leftover 16 not in the fake27 set and not walked.

## What landed on the page

### Batch 1 (eb21ce2)
- FART: 27 new real 1 Aug stamps (`proved` or `unmoved_equals_now`, `aug1_as_of=2026-08-01T00:00:00Z`). Old 16 real 1 Aug kept. 3 thick whales still `as_of_now` (DEFER, no UNKNOWN stamp). Wintermute new box converted to dest-watch `MM book`.
- Tiny JS row: if a box has a real 1 Aug AND a real now, show `since 1 Aug` with `(now-aug1)/aug1`. Same `siren-box-row` classes. Live.
- Hardcoded row label still `1 Aug` (not renamed 27 Aug).

### Batch 2 (this commit)
- LOCKIN: 30 new real 1 Aug stamps for Lockin21–50. Old real 1 Aug kept. Raydium AMM Authority still `as_of_now` (not walked this batch; dest-watch thick, will DEFER if >300 txs).
- FART boxes not touched.
- RETARDIO 21–27 proofs exist in local persist but were **not** spliced this batch (LOCKIN first).
- Row label still `1 Aug`. JS row already present; LOCKIN boxes with aug1>0 will show `%` when both numbers are real.

## What this resume did / did not

Did:
- Pulled origin/main (already up to date at eb21ce2). No rebase.
- Read existing persist (`job2-aug1-proofs.json`, queue, walker, walk log). Did not start over.
- Spliced already-proved unspliced LOCKIN (30) before walking more.
- Skipped GRASS / DRIFT / PUMP / ORCA.
- Left reconstructed 0s only where the walk proved them.

Did not:
- Did not walk more wallets this commit (splice-first).
- Did not splice RETARDIO 21–27 yet.
- Did not invent numbers or guess zeros.
- Did not add wallets or change config address lists.
- Did not touch HOM or hold-card look.
- Did not start Job 3.
- Did not FAIL Job 1.

## Files touched

- `index-v4.html` — siren-watch-data LOCKIN boxes only this batch. JS row already present (batch 1).
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md` — this pack

## Files left alone

- `config/siren-wallets.json` / `config/siren-wallet-tags.json` (addresses and tags stay)
- HOM (not present)
- DRIFT / GRASS / PUMP / ORCA
- FART real 1 Aug stamps
- Other baked coins’ boxes this batch
- No invented wallets
- `data/cache/job2-aug1-proofs.json` local persist (gitignored)
- `data/cache/job2_aug1_walk.py` local walker (gitignored; GRASS removed from JOB_COINS)

## Persist

Each proved 1 Aug written immediately to `data/cache/job2-aug1-proofs.json` before splice.
Walk log: `data/cache/job2-aug1-walk.log` already PROVED Lockin21–50 and Retardio21–27 then died on 429.

## Commits

- Batch 1: `eb21ce2` Prove 1 Aug starts on new dest-watch boxes (batch 1).
- Batch 2: this commit (LOCKIN 30 + pack). Hash: read `git log -1`.

## Status

**NOT DONE.** Live remaining after this splice: LOCKIN Raydium AMM Authority (walk or honest DEFER), then RETARDIO (splice 21–27 after remaining walk), SPX, 2Z, IO, RENDER, BONK, NOS, GIGA. GRASS skipped. Grok has not marked this complete.
