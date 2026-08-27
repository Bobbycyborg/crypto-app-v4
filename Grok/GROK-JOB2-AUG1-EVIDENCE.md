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
- GRASS is DEAD (same as DRIFT) — do not walk / splice GRASS. DRIFT stays out.
- Skip PUMP / ORCA. HOM not present.

Helius maxed; public-RPC ATA path. Persist each proof before splice. Sleep/backoff on 429.

## The lie

586 new dest-watch boxes had today pile on the 1 Aug line (`as_of_now` / `2026-08-27`). Existing real 1 Aug left alone.

## Per coin (this pack)

| Coin | fake27 | proved 1 Aug (this job, on page) | DEFER whale (left as_of_now) | DEFER dest-watch | still as_of_now | notes |
|---|---:|---:|---:|---:|---:|---|
| FART | 31 | 27 | 3 | 1 | 3 | batch 1. FART real 1 Aug not overwritten. |
| LOCKIN | 31 | 30 | 1 | 0 | 1 | batch 2 |
| RETARDIO | 37 | 36 | 1 | 0 | 1 | batch 3 |
| SPX | 40 | 38 | 2 | 0 | 2 | batch 4 |
| 2Z | 46 | 39 | 2 | 5 | 2 | batch 5 |
| IO | 57 | 55 | 0 | 1 | 1 (Jupiter) | walk still running; Jupiter not yet |
| NOS | 75 | 70 | 3 | 2 | 3 | walked / honest DEFER |
| RENDER | 62 | 51 | 1 | 10 | 1 (Jupiter) | Jupiter honest gt300 DEFER; left as_of_now |
| BONK | 73 | 56 | 5 | 2 | 12 | batch 14 +6 Bonk69-71/73-75 + Binance dest-watch; Bonk37/44/49/61/72 gt300; walk on Bonk76 |
| GIGA | 77 | 64 | 1 | 0 | 13 | batch 12 +4 Giga82-85; Giga65 gt300; walk on Giga86 |
| GRASS | 57 | 0 | 0 | 0 | 57 | SKIP |
| **total** | **586** | **466 on page** | **19** | **21** | **96 on page** | GRASS 57 of leftover are skip |

PUMP / ORCA / DRIFT no fake27. HOM not present. G2 leftover 16 not walked.

Live page after batch 14: RENDER 85 real / 1 fake27 / 11 dest. BONK 73 real / 12 fake27 / 8 dest. GIGA 81 real / 13 fake27 / 1 dest. IO 71 real / 1 fake27 / 4 dest.

## What this resume did / did not

Did: resume persist (no start-over); splice LOCKIN first; walk RETARDIO/SPX/2Z/IO; splice proved RENDER/GIGA/BONK as proofs landed; skip GRASS/DRIFT/PUMP/ORCA; persist each proof; backoff 429; reconstructed 0s only when walk-proved. This pack: splice BONK Bonk69-71/73-75 + Binance dest-watch. RENDER Jupiter honestly DEFERred gt300 (left as_of_now, no UNKNOWN).

Did not: invent numbers; add wallets; change config lists; touch HOM / hold-card look; start Job 3; FAIL Job 1; walk or splice GRASS.

## Files touched

- `index-v4.html` — siren-watch-data only. JS `since 1 Aug` from batch 1. Label still `1 Aug`.
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md` — this pack

## Files left alone

- config address lists; HOM; DRIFT; GRASS; PUMP; ORCA; FART real 1 Aug; `data/cache` persist (gitignored)

## Commits (this resume)

- `332acd8` batch 2 LOCKIN 30
- `2b0c655` batch 3 RETARDIO 36
- `1a66bce` batch 4 SPX 38 (parallel `84f7e2c`)
- `a625a6a` batch 5 pack (2Z HTML in parallel `baf3ee7`/`bcc4953`)
- `6496feb` batch 8 RENDER/GIGA/BONK splice
- `a45a9d5` batch 9
- `107083e` batch 10 GIGA +14 / BONK +13
- `ce6e432` / `2795250` batch 11
- `7854c3a` batch 12 GIGA +4 / BONK +1
- `4615ae0` batch 13 BONK +4
- This commit: batch 14 BONK +6 + Binance dest-watch. Hash: read `git log -1`.
- Parallel also landed `e657cb5`, `d63223d`, `8b207fc`, `e7dd955`.

## Status

**NOT DONE.** Live leftover still as_of_now / still walking: RENDER Jupiter 1 (honest gt300 DEFER), BONK 12 (5 honest gt300), GIGA 13 (1 honest gt300), IO Jupiter 1. GRASS skipped. Grok has not marked this complete.
