# Job 2 — reconstruct 1 Aug 2026 00:00 UTC on new dest-watch boxes

**Date:** 27 Aug 2026
**Owner:** Grok
**Status:** NOT DONE. Grok has not marked this complete. Partial. CGPT reviews pack + diff only.

Official start = 1 Aug 2026 00:00 UTC only. `aug1 = now + this-mint outs − this-mint ins` since that instant, ATA of that coin on that wallet. No 10 Aug fallback. No guessed zeros (0 only when the walk proved the wallet held none on 1 Aug). No UNKNOWN written as a new whale stamp. G2 leftover 16 not walked.

Helius key stayed on the Mac (never pasted). Helius hit max usage; walk used the existing public-RPC ATA path from `scripts/backfill_siren_aug1.py`. Persist each proof immediately.

Oliver: 1 Aug label stays. Last sell stays. GRASS dead — not walked, not spliced. DRIFT / HOM out. % row only when real 1 Aug AND real now.

## Per coin (live page counts, 27 Aug ~13:04 PT)

| Coin | fake27 start | proved 1 Aug this job (on page) | DEFER whale still as_of_now | dest-watch CEX/MM converted | still as_of_now |
|---|---:|---:|---|---:|---:|
| FART | 31 | 27 | Fart21, Fart45, Raydium AMM | 1 Wintermute → MM book | 3 |
| LOCKIN | 31 | 30 | Raydium AMM | 0 | 1 |
| RETARDIO | 37 | 36 | Raydium AMM | 0 | 1 |
| SPX | 40 | 38 | Raydium AMM, Orca Whirlpool | 0 | 2 |
| 2Z | 46 | 39 | Raydium CLMM, TwoZ56 | 7 CEX book | 2 |
| IO | 57 | 55 | Jupiter (unfinished / thick) | KuCoin + others | 1 |
| RENDER | 62 | 51 | Jupiter | ~10 CEX book | 1 |
| BONK | 73 | 58 | Bonk37/44/49/61/72 + some still in flight + Jupiter | several CEX book | 10 |
| NOS | 75 | 70 | 2× Raydium CLMM, Nos67 | 2 | 3 |
| GIGA | 77 | 65 | Giga65 + Raydium AMM + Meteora; Giga87–95 still in flight | 0 | 12 |
| GRASS | 57 | 0 | — | — | 57 SKIP |
| **total** | **586** | **~469 on page** | honest DEFER / in-flight | desk books | **93 on page** (57 GRASS skip) |

PUMP / ORCA / DRIFT: no fake27. G2 leftover 16 not walked. No invented wallets.

## Page

- Hardcoded row label still `1 Aug`.
- JS `since 1 Aug` percent is **live** (status `proved` or `unmoved_equals_now` + `aug1_as_of` 2026-08-01 + real now). Sign is pile change: `−12%` if smaller now, `+8%` if grown. Same `siren-box-row` classes.
- now / last_out / left_24h kept.
- Existing real 1 Aug boxes left alone.

## Files touched

- `index-v4.html` — siren-watch-data boxes + JS row only
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md`

## Files left alone

- `config/siren-wallets.json` / `config/siren-wallet-tags.json`
- HOM, DRIFT, GRASS, PUMP, ORCA
- `data/cache/job2-aug1-proofs.json` local persist (gitignored)

## Commits

- `eb21ce2` batch 1 FART + JS
- `332acd8` / `e657cb5` batch 2 LOCKIN
- `2b0c655` batch 3 RETARDIO
- `84f7e2c` / `1a66bce` batch 4 SPX
- `bcc4953` / `baf3ee7` / `a625a6a` batch 5 2Z/IO
- `d63223d` batch 6 IO
- `e7dd955` / `8b207fc` batch 7
- `6496feb` batch 8
- `a45a9d5` … `5357805` later batches (parallel resumes)
- this commit: current leftover inventory

## What's left

Walker still in flight on GIGA Giga82+ and the DEX tail. Live leftover **excluding GRASS skip**:

- Honest DEFER (gt300 / thick book, left as_of_now, no UNKNOWN stamp): FART 3, LOCKIN 1, RETARDIO 1, SPX 2, 2Z 2, NOS 3, IO Jupiter, RENDER Jupiter, several BONK (Bonk37/44/49/61/72), Giga65 / Raydium / Meteora
- Still walking / unspliced: BONK a few (Bonk78–81), GIGA Giga87–95
- GRASS 57 skipped (dead)

**NOT DONE.** Grok has not marked this complete.
