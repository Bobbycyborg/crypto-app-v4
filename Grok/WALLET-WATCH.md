# Wallet watch

Only coins in `config/report.json` under `siren_walk` get a fresh walk.

BTC, ZEC, and HYPE stay on the report. They are not part of this walk.

## How a check works

1. Copy the last saved file before the walk. Never start without that copy.
2. Read every wallet already on the list for those coins. Do not add wallets.
3. Plain Solana reads only. Public RPC first, then cheap Helius standard RPC if the public one fails. One wallet at a time.
4. Do not use the expensive Helius transaction history.
5. A send is not a sale. A send to a known exchange or market-maker is the loud mark.
6. Proved 1 Aug starts are kept by `lib/v3/siren_state.py`. The code will not replace a proved start with today's balance.
7. Save into `state/siren-state.json`. Coins not checked this time stay as they were.
8. The page is filled from that file.

## What we do not do

- Do not walk coins that are not in `siren_walk` unless Oliver asks.
- Do not invent wallets or tags.
- Do not delete the before-copy.
