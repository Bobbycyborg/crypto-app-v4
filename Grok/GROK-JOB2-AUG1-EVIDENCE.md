# Job 2 — reconstruct 1 Aug 2026 00:00 UTC on new dest-watch boxes

**Date:** 27 Aug 2026
**Owner:** Grok
**Status:** NOT DONE. Grok has not marked this complete. Partial walk. CGPT reviews pack + diff only.

Official start = 1 Aug 2026 00:00 UTC only. `aug1 = now + this-mint outs − this-mint ins` since 1 Aug 2026 00:00 UTC, ATA of that coin on that wallet. No 10 Aug fallback. No guessed zeros (reconstructed 0 only when the walk proved the wallet held none on 1 Aug). No UNKNOWN written as a new whale stamp. G2 leftover 16 not walked.

Helius key stayed on the Mac (never pasted). Helius hit **max usage reached**; walk used the existing public-RPC ATA path (`getSignaturesForAddress` on the ATA + `getTransaction` mint delta) from `scripts/backfill_siren_aug1.py`. Persist each proof immediately.

Oliver: 1 Aug label stays. Last sell stays. GRASS dead — not walked, not spliced. DRIFT / HOM out. % row only when real 1 Aug AND real now.

## Per coin

| Coin | fake27 | proved 1 Aug (this job) | DEFER whale (still as_of_now) | DEFER dest-watch | still as_of_now |
|---|---:|---:|---:|---:|---:|
| FART | 31 | 27 | 3 (Fart21, Fart45, Raydium AMM) | 1 (Wintermute → MM book) | 3 |
| LOCKIN | 31 | 30 | 1 (Raydium AMM) | 0 | 1 |
| RETARDIO | 37 | 36 | 1 (Raydium AMM) | 0 | 1 |
| SPX | 40 | 38 | 2 (Raydium AMM, Orca Whirlpool) | 0 | 2 |
| 2Z | 46 | 36 | 2 (Raydium CLMM, TwoZ56) + 1 other gt300 | 7 CEX → CEX book | 2 |
| IO | 57 | 55 | 0 | 1 (KuCoin → CEX book) | 1 (Jupiter, walk unfinished) |
| RENDER | 62 | ~5 | — | some desk | 56 (walk in flight) |
| BONK | 73 | ~17 | — | some desk | 53 (walk in flight) |
| NOS | 75 | ~39 | — | some desk | 35 (walk in flight) |
| GIGA | 77 | ~13 | — | — | 64 (walk in flight) |
| GRASS | 57 | 0 | — | — | 57 SKIP (dead) |
| **on page** | **586** | **~290 resolved** | **9** | **desk books converted** | **~282 leftover** (57 GRASS skip) |

PUMP / ORCA / DRIFT: no fake27. G2 leftover 16 not walked. No invented wallets.

## Page

- Hardcoded row label still `1 Aug`.
- JS `since 1 Aug` percent is live (real 1 Aug + real now). `−` if smaller now, `+` if grown. Same `siren-box-row` classes.
- now / last_out / left_24h kept on spliced boxes.
- Existing real 1 Aug boxes left alone.

## Files touched

- `index-v4.html` — siren-watch-data boxes + JS row only
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md`

## Files left alone

- `config/siren-wallets.json` / `config/siren-wallet-tags.json`
- HOM, DRIFT, GRASS, PUMP, ORCA
- `data/cache/job2-aug1-proofs.json` local persist (gitignored)

## Commits

- `eb21ce2` batch 1 — FART + JS
- `332acd8` / `e657cb5` batch 2 — LOCKIN
- `2b0c655` batch 3 — RETARDIO
- `84f7e2c` batch 4 — SPX
- this commit batch 5 — 2Z + IO partial + in-flight NOS/BONK/RENDER/GIGA splices

## Status

**NOT DONE.** Left to finish: IO 8 leftover; RENDER ~56; BONK ~53; NOS ~35; GIGA ~64. GRASS 57 skipped. 9 DEFER whales still as_of_now. Grok has not marked this complete.
