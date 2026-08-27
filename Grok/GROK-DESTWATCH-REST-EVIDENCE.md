# Dest-watch rest splice — CGPT review pack

**Job:** Job 1 of the 27 Aug 2026 dest-watch leftover (not V4 schema Job 1)
**Date:** 27 Aug 2026
**Owner:** Grok
**Commit:** `f261613` on `Bobbycyborg/crypto-app-v4` main
**Status:** NOT DONE. Grok has not marked this complete. CGPT reviews this pack + the diff only.

---

## Dummy (what Oliver wants)

Oliver watches where the majority of each bag coin sits, and whether size moves. Unnamed whales stay on the list with tags (Fart21, Io22). Real names stay when proved (Binance, Wintermute, Raydium). Dest to a market maker or exchange is the loud siren. Any transfer raises eyes. Follow the hop. Do not treat a transfer as nothing. Do not invent wallets. Popup shows tags, not raw addresses.

This job: take whales we already proved this morning and put them on the live siren popups for **FART, BONK, GRASS, NOS, RENDER, IO, 2Z**. Same as SPX / GIGA / RETARDIO / LOCKIN earlier today. So he can see the bigger piles.

This job is **not** the 1 Aug walk. New boxes currently have today’s balance on both the 1 Aug line and the now line (`aug1_status=as_of_now`, `aug1_as_of=2026-08-27`). That is known. Oliver later said: 1 Aug stays 1 Aug (start of this move), now is what’s left, last sell stays, and % gone since 1 Aug only if we have both real numbers. That walk is **Job 2**. Do **not** FAIL this pack because 1 Aug is still today’s figure.

---

## Oliver rules that apply

- Majority-of-supply location plus movement. Names optional. Tags are enough.
- Unlabeled whales stay on if they are large. Do not drop a pile because it has no name.
- Pools stay on if they hold size (Raydium / Meteora / Orca), tagged as the pool.
- Dest to Wintermute / any MM / any CEX is the siren. The sending whale does not need a real name.
- Transfer ≠ dismissable. Sold is sold. A hop is still a watch.
- No invented wallets. No guessed zeros. No UNKNOWN written as a new start figure.
- No raw addresses in the siren popup.
- GRASS stays off the main hold-card board (`is-hidden`). Dest-watch on the GRASS page stays.
- DRIFT is sold and dead. Do not hunt it. Do not add it.
- PUMP stays the 150 airdrop list. Not this job.
- HOM is not this job. Cursor schema Jobs 1–6 are not this job.
- Grok does the work and does not mark it done. CGPT reviews pack + diff only: proved dests, no invented wallets, dest-watch files only, nothing else broken. CGPT does not hunt. Cursor stays out.

---

## What Grok did

Same splice as SPX/GIGA (`aaaed76`) and RETARDIO/LOCKIN (`087066f`).

Add lists were already-proved `new` rows from two hunts (27 Aug morning). Not a new hunt in this commit.

| Coin | Wallets before → after | New | Tracked before → after | Supply fmt stayed |
|---|---|---|---|---|
| FART | 21 → 52 | 31 | 443.1M → 637.4M | 1000M |
| BONK | 22 → 95 | 73 | 40433.7B → 66343.7B | 87994.6B |
| GRASS | 22 → 79 | 57 | 454.2M → 640.8M | 1000M |
| NOS | 21 → 96 | 75 | 51.1M → 66.7M | 100M |
| RENDER | 40 → 102 | 62 | 306.7M → 399.3M | 484.8M |
| IO | 19 → 76 | 57 | 528.1M → 688.6M | 798.2M |
| 2Z | 21 → 67 | 46 | 7B → 8.5B | 10B |

Existing boxes on those coins: old 1 Aug / now figures kept. No existing wallet deleted.
New boxes: now = hunt-proved balance; 1 Aug line = same number, labelled as_of_now 27 Aug in the blob. Header on the page still says “1 Aug”. That header was left for Job 2.
Popup: tags only.
Supply / supply_fmt left as already on the live blob.
Named tags kept when proved: Binance, Gate.io, CoinSpot, Crypto.com, MEXC, OKX, Bybit, Raydium AMM Authority, Raydium CLMM, Wintermute, Jupiter, Bithumb, KuCoin, Coinbase, SwissBorg. Rest are TickerN.

Loud desks in this add (already on other coins, missing on these lists):
- BONK Binance `9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM` ~7.19T
- IO Binance same desk ~48.3M

---

## What Grok did not do

- Did not invent wallets
- Did not walk 1 Aug 2026 00:00 UTC on the new boxes (Job 2)
- Did not rename the row header to 27 Aug (Oliver rejected that; 1 Aug stays 1 Aug)
- Did not add % gone since 1 Aug (Job 2, and only when both numbers are real)
- Did not touch last-cycle / G3 dash (Job 3)
- Did not change SPX 58, GIGA 96, RETARDIO 56, LOCKIN 50, ORCA 29, PUMP 150, DRIFT 22
- Did not un-hide GRASS
- Did not touch HOM
- Did not touch Cursor/CGPT schema Jobs 1–6
- Did not change hold-card look, layout, type, colours, or spacing
- Did not write UNKNOWN or a guessed zero

---

## Files touched (only these)

- `config/siren-wallets.json` — append only on FART, BONK, GRASS, NOS, RENDER, IO, 2Z
- `config/siren-wallet-tags.json` — tags from the hunt lists; real names kept
- `index-v4.html` — those 7 objects inside `<script id="siren-watch-data">` only
- `Grok/GROK-DESTWATCH-REST-EVIDENCE.md` — this pack

## Files left alone

Every other coin in the baked blob (byte-equal). HOM. DRIFT wallets. Hold-card CSS. Hardcoded “1 Aug” row label. Last-cycle / ALT Moves. `helius.local.env`. caches. reports-NOT-FOR-GH.

---

## How CGPT reviews (only this)

1. Diff is dest-watch files only (the four paths above).
2. Every new address was in the proved hunt add-list. No invented wallets.
3. Counts match: FART 52, BONK 95, GRASS 79, NOS 96, RENDER 102, IO 76, 2Z 67. Config = tags = baked boxes.
4. Other coins unchanged.
5. New boxes have a real now figure (not UNKNOWN, not zero-guess).
6. GRASS hold card still hidden. DRIFT not expanded.
7. Do not hunt. Do not brief Grok. Do not open Job 2 or Job 3.

**PASS** if 1–6 hold.
**FAIL** if a wallet was invented, another coin changed, dest-watch files were not the only code/config change, or counts do not match.

Do not FAIL this job because 1 Aug equals now on new boxes. That is Job 2.

---

## Job 2 / Job 3 (context only — not in this diff)

**Job 2 (Oliver, later 27 Aug):** 1 Aug stays 1 Aug. Now is remaining. Last sell stays. Get a real 1 Aug 2026 00:00 UTC reconstruct for the as_of_now boxes. Add % gone since 1 Aug only when both figures are real. Do not rename the line 27 Aug.

**Job 3 (Oliver, later 27 Aug):** Last-cycle autopsy on the V4 dash. Price map, March 2024 tops, four wallet turns. Not buried notes. Not this commit.
