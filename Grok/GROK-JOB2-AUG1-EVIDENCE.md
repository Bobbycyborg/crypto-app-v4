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
| FART | 31 | 27 | 3 (Fart21, Fart45, Raydium AMM Authority) | 1 (Wintermute, MM book) | 3 | batch 1. Real 1 Aug not overwritten. |
| LOCKIN | 31 | 30 | 1 (Raydium AMM Authority) | 0 | 1 | batch 2. Reconstructed 0s: Lockin21, 23, 34, 47, 50. |
| RETARDIO | 37 | 36 | 1 (Raydium AMM Authority) | 0 | 1 | batch 3. Reconstructed 0s: Retardio31, 46, 52. |
| SPX | 40 | 38 | 2 (Orca Whirlpool, Raydium AMM Authority) | 0 | 2 | batch 4. Binance thin so proved. Reconstructed 0: Spx40. |
| 2Z | 46 | 39 | 2 (TwoZ56, Raydium CLMM) | 5 (Bybit, Bithumb, OKX-C68a, Coinbase, Binance) | 2 | batch 5 (`baf3ee7`). Gate.io + OKX-8wM4 thin so proved. No recon 0s. |
| IO | 57 | 55 | 1 (Jupiter, walk unfinished / as_of_now) | 4 (Bybit, Gate.io, Binance, KuCoin) | 1 | mid-flight splice by parallel walk. Jupiter not stamped UNKNOWN. |
| RENDER | 62 | in flight | — | some desk | leftover | walk in flight; not fully spliced this commit |
| BONK | 73 | in flight | — | some desk | leftover | walk in flight |
| NOS | 75 | 70 | 3 (Nos67, 2× Raydium CLMM; gt300) | 2 (MEXC, SwissBorg → CEX book) | 3 | batch 7. Walk complete. No recon 0s. Pre-existing Nos10 / NosRewardsVault UNKNOWN left alone. |
| GIGA | 77 | in flight | — | — | leftover | walk in flight |
| GRASS | 57 | 0 | 0 | 0 | 57 | SKIP — Oliver: GRASS dead. |
| **page** | **586** | **see commits** | **honest DEFERs** | **desk books** | **leftover + GRASS skip** | |

PUMP / ORCA / DRIFT had no fake27. HOM not present. G2 leftover 16 not in the fake27 set and not walked.

## What landed on the page

- JS `since 1 Aug` percent row from batch 1. Label still `1 Aug`. Not renamed 27 Aug.
- FART / LOCKIN / RETARDIO / SPX / 2Z / IO real 1 Aug counts not dropped by later splices.
- Batch 5 (`baf3ee7`): 2Z 39 new real 1 Aug; 5 CEX book; TwoZ56 + Raydium CLMM left `as_of_now`.
- Batch 6 (`d63223d`): parallel mid-flight splices (IO partial + others). Not overwritten.
- Batch 7 (this commit): NOS remainder. 70 proved this job (31 newly stamped here on top of earlier mid-flight NOS splices). SwissBorg → `CEX book`. Nos67 + 2× Raydium CLMM left `as_of_now`. No UNKNOWN whale stamps.

## What this resume did / did not

Did:
- Waited for existing 2Z walk (pid 295321) to finish. Did not start a second 2Z walk.
- 2Z done proved=39 defer=7 err=0. 429 persist-and-continue.
- Did not launch duplicate IO/RENDER/BONK/NOS/GIGA walks. Monitored parallel walks. Accumulated proofs in SAFE file against shared-file races.
- Spliced NOS when that walk reached 75/75.
- Skipped GRASS / DRIFT / PUMP / ORCA.
- Left reconstructed 0s only where the walk proved them.

Did not:
- Did not invent numbers or guess zeros.
- Did not add wallets or change config address lists.
- Did not touch HOM or hold-card look.
- Did not start Job 3.
- Did not FAIL Job 1.
- Did not walk or splice GRASS.
- Did not stamp UNKNOWN on thick whales.

## Files touched

- `index-v4.html` — siren-watch-data for FART, LOCKIN, RETARDIO, SPX, 2Z, IO (partial), NOS. JS row from batch 1.
- `Grok/GROK-JOB2-AUG1-EVIDENCE.md` — this pack

## Files left alone

- `config/siren-wallets.json` / `config/siren-wallet-tags.json`
- HOM (not present)
- DRIFT / GRASS / PUMP / ORCA
- FART / LOCKIN / RETARDIO / SPX / 2Z real 1 Aug stamps
- RENDER / BONK / GIGA unfinished boxes this commit
- No invented wallets
- `data/cache/job2-aug1-proofs.json` local persist (gitignored)

## Persist

Each proved 1 Aug written immediately to box proofs (+ SAFE accumulator) and copied to `data/cache/job2-aug1-proofs.json` before/after splice.

## Commits

- Batch 1: `eb21ce2` (FART 27 + JS)
- Batch 2: `332acd8` (LOCKIN). `e657cb5` partial RETARDIO, superseded by batch 3.
- Batch 3: `2b0c655` (RETARDIO 36)
- Batch 4: `1a66bce` / `84f7e2c` (SPX 38)
- Batch 5: `baf3ee7` (2Z 39). Later `a625a6a` / `bcc4953` also titled batch 5 (parallel mid-flight splices).
- Batch 6: `d63223d` (parallel mid-flight)
- Batch 7: this commit (NOS 70 complete). Hash: read `git log -1`.

## Status

**NOT DONE.** Live remaining walks: IO (Jupiter leftover), RENDER, BONK, GIGA. GRASS skipped. Honest DEFERs left as_of_now include FART 3, LOCKIN Raydium, RETARDIO Raydium, SPX Orca+Raydium, 2Z TwoZ56+Raydium CLMM, IO Jupiter, NOS Nos67+2×Raydium CLMM. Grok has not marked this complete.
