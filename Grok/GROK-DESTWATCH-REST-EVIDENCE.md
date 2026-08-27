# Dest-watch rest splice — CGPT review pack

Job 1 only (Oliver thumbs-up 27 Aug 2026). Grok has **not** marked this complete.
Do **not** treat this pack as a PASS. Review pack + diff only.

## What ran

Same splice as SPX/GIGA (`aaaed76`) and RETARDIO/LOCKIN (`087066f`).
New boxes: now = hunt-proved balance; start = same figure; `aug1_as_of` = `2026-08-27T00:00:00Z` (`as_of_now`). No 1 Aug walk. No guessed zero. No UNKNOWN start/now on new boxes.
Existing boxes: start/now figures kept. No existing wallet deleted.
Popup lines are tags only. No raw new addresses.
Supply / `supply_fmt` left as already on the live blob.

Sources (do not invent, do not hunt more):
- `/workspace/wallet-hunt-mid.json` — FART 31, BONK 73, GRASS 57, NOS 75
- `/workspace/wallet-hunt-close.json` — RENDER 62, IO 57, 2Z 46

## Per coin

| Coin | Wallets before → after | New | Tracked before → after | Supply fmt stayed |
|---|---|---|---|---|
| FART | 21 → 52 | 31 | 443.1M → 637.4M | 1000M |
| BONK | 22 → 95 | 73 | 40433.7B → 66343.7B | 87994.6B |
| GRASS | 22 → 79 | 57 | 454.2M → 640.8M | 1000M |
| NOS | 21 → 96 | 75 | 51.1M → 66.7M | 100M |
| RENDER | 40 → 102 | 62 | 306.7M → 399.3M | 484.8M |
| IO | 19 → 76 | 57 | 528.1M → 688.6M | 798.2M |
| 2Z | 21 → 67 | 46 | 7B → 8.5B | 10B |

Exact tracked floats:
- FART 443065926.9367169 → 637386244.9172568
- BONK 40433658112281.38 → 66343679808013.91
- GRASS 454177197.83776563 → 640837223.9392617
- NOS 51127658.806444995 → 66696575.556398
- RENDER 306692974.7326417 → 399340826.7444274
- IO 528125973.4236965 → 688593704.9310247
- 2Z 6975342948.865223 → 8472713550.692934

## Files touched

- `config/siren-wallets.json` — append only on FART, BONK, GRASS, NOS, RENDER, IO, 2Z
- `config/siren-wallet-tags.json` — tags from the two hunt JSON files; real names kept (Binance, Gate.io, CoinSpot, Crypto.com, MEXC, OKX, Bybit, Raydium AMM Authority, Raydium CLMM, Wintermute, Jupiter, Bithumb, KuCoin, Coinbase, SwissBorg)
- `index-v4.html` — rebuilt only those 7 coin objects inside `<script id="siren-watch-data">`
- `Grok/GROK-DESTWATCH-REST-EVIDENCE.md` — this pack

## Files left alone

- Other baked coins: SPX 58, GIGA 96, RETARDIO 56, LOCKIN 50, ORCA 29, PUMP 150, DRIFT 22 — blob byte-equal
- HOM not present, not added
- DRIFT wallets not touched
- GRASS stay `is-hidden` on the hold-card board (dest-watch on the GRASS page only)
- Hardcoded `1 Aug` row header not changed (Job 2)
- No last-cycle dash (Job 3)
- No caches, no `helius.local.env`, no `reports-NOT-FOR-GH`

## Confirmations

- Baked box counts match config and tags for all 7 coins (52 / 95 / 79 / 96 / 102 / 76 / 67)
- No other coin in the baked blob changed
- No invented wallets; add lists are exactly `new` from the two hunt JSON files
- New-box start/now never UNKNOWN and never guessed zero
- Commit message: `Seed proved FART BONK GRASS NOS RENDER IO 2Z dest-watch whales.`
- Commit hash: this same `origin/main` commit (read `git log -1` / parent report)

## Status

**NOT DONE.** Grok has not marked this complete. Job 2 and Job 3 were not done.
