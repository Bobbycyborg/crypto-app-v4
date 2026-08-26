# G1 EVIDENCE PACK

**Job:** G1. Seed proved dests already hunted  
**Date:** 26 Aug 2026  
**Owner:** Grok  
**Status:** NOT DONE. Grok has not marked this complete. CGPT reviews this pack + the diff.

**Commits:** `4a3ac2b` (implementation) + this follow-up (evidence gaps only).

## Dummy
V4 can now name Wintermute and DWF when a watched wallet sends there. Three proved dests were missing. The old MM file is not on GitHub so the checker could not read them. That is fixed. Any send still raises eyes. Desk name is the loud one.

## Before
- `config/known-cex-wallets.json`: 301 wallets (227 cex, 8 mm, 64 custody, 2 treasury)
- Official Binance Solana hot/cold 19: already present (0 missing)
- OKX / Bybit / Bitfinex official Solana dests: already present
- Wintermute Solana `MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa`: present as `type=mm` (CEX map skipped it)
- `reports/shared-mm-registry/shared-entity-wallet-registry.json` on V4: **FileNotFoundError**
- Dest loader MM map: **could not load**
- Wintermute dest resolve on V4: **fail**

## After
- CEX map: **227**
- MM map: **4** Solana HIGH/MEDIUM
- Wintermute `MfDuWeq…` resolves to **Wintermute**
- DWF `HwDkuDCU…` resolves to **DWF Labs**
- `known-cex` wallet count: **304** (+3). Not tens of thousands.

## Added (only these three)

| entity | chain | type | confidence | address | source registry id |
|---|---|---|---|---|---|
| Wintermute | solana | mm | MEDIUM | `5sTQ5ih7xtctBhMXHr3f1aWdaXazWrWfoehqWdqWnTFP` | wm-sol-5stq |
| Wintermute | solana | mm | MEDIUM | `BMnT51N4iSNhWU5PyFFgWwFvN1jgaiiDr9ZHgnkm3iLJ` | wm-sol-bmnt |
| DWF Labs | solana | mm | HIGH | `HwDkuDCUipJHHKodBBCjffFvrjhmd4iVVh7fq25fShvt` | dwf-sol-hwdk |

Also wrote `config/known-mm-wallets.json` with those four Solana MM dests (the three new + already-known Wintermute HIGH).

## Gap 1 — verbatim source rows (from the already-hunted V3 registry)

Copied from local `crypto-app-v3/reports/shared-mm-registry/shared-entity-wallet-registry.json` on 26 Aug 2026. No new hunt. Fields below are the original row. Supporting tx lists omitted where empty.

### wm-sol-5stq (newly seeded)
```
address: 5sTQ5ih7xtctBhMXHr3f1aWdaXazWrWfoehqWdqWnTFP
entity: Wintermute
chain: solana
confidence: MEDIUM
role: market-making
attribution_source: agentmila/solana-market-makers (Nansen cross-ref claim)
source_urls:
  - https://github.com/agentmila/solana-market-makers
  - https://solscan.io/account/5sTQ5ih7xtctBhMXHr3f1aWdaXazWrWfoehqWdqWnTFP
last_checked_utc: 2026-08-12T06:01:31Z
notes: Not independently confirmed on Meteora ops list. Keep MEDIUM.
```

### wm-sol-bmnt (newly seeded)
```
address: BMnT51N4iSNhWU5PyFFgWwFvN1jgaiiDr9ZHgnkm3iLJ
entity: Wintermute
chain: solana
confidence: MEDIUM
role: OTC
attribution_source: agentmila/solana-market-makers (Nansen cross-ref claim)
source_urls:
  - https://github.com/agentmila/solana-market-makers
  - https://solscan.io/account/BMnT51N4iSNhWU5PyFFgWwFvN1jgaiiDr9ZHgnkm3iLJ
last_checked_utc: 2026-08-12T06:01:31Z
notes: Secondary list role OTC/Trading. Keep MEDIUM.
```

### dwf-sol-hwdk (newly seeded)
```
address: HwDkuDCUipJHHKodBBCjffFvrjhmd4iVVh7fq25fShvt
entity: DWF Labs
chain: solana
confidence: HIGH
role: trading
attribution_source: Official disclosure by DWF Labs partner Andrei Grachev (May 2025) via multiple news reprints of disclosed addresses
source_urls:
  - https://blockchainreporter.net/dwf-labs-unveils-official-wallets-used-for-buyouts-on-secondary-marketplaces/
  - https://www.panewslab.com/en/articles/32793415
  - https://solscan.io/account/HwDkuDCUipJHHKodBBCjffFvrjhmd4iVVh7fq25fShvt
first_evidence_date: 2025-05-06
last_checked_utc: 2026-08-12T06:01:31Z
```

## Gap 3 — Wintermute MfDu confidence

`known-cex` had `MfDuWeq…GVWa` as **MEDIUM** (Meteora-only label).  
`known-mm-wallets.json` had the same address as **HIGH**.

The already-hunted registry row is **HIGH**. That is why HIGH is correct. Not a new hunt. Not a guess. Brief said: do not upgrade MED → HIGH unless the old shared-MM registry independently proved HIGH. It did.

### wm-sol-mfdu (already in known-cex; confidence aligned to HIGH this follow-up)
```
address: MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa
entity: Wintermute
chain: solana
confidence: HIGH
role: OTC
attribution_source: MeteoraAg/ops blacklist report (W45 Wintermute OTC) + secondary analytics list (agentmila/solana-market-makers) + Dune curated label Wintermute 4
source_urls:
  - https://github.com/MeteoraAg/ops/issues/9
  - https://github.com/agentmila/solana-market-makers
  - https://dune.com/queries/4904811
  - https://solscan.io/account/MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa
last_checked_utc: 2026-08-12T06:01:31Z
```

`config/known-cex-wallets.json` `MfDuWeq…` confidence is now HIGH to match that row. `known-mm-wallets.json` already said HIGH.

## Gap 2 — raw loader test

Command (from `crypto-app-v4/`):

```
python3 tests/g1/test_g1_dest_loader.py
```

Stdout + exit (26 Aug 2026, after this follow-up, no reports MM file on V4):

```
cwd_root /Users/olivergoodrum/Documents/GithubNew/Cryptodashboard/crypto-app-v4
reports_mm_exists False
cex_n 227
mm_n 4
wintermute_resolve Wintermute
dwf_resolve DWF Labs
mm_keys ['5sTQ5ih7xtctBhMXHr3f1aWdaXazWrWfoehqWdqWnTFP', 'BMnT51N4iSNhWU5PyFFgWwFvN1jgaiiDr9ZHgnkm3iLJ', 'HwDkuDCUipJHHKodBBCjffFvrjhmd4iVVh7fq25fShvt', 'MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa']
PASS
EXIT:0
```

Test file: `tests/g1/test_g1_dest_loader.py`. No RPC. Asserts the reports MM path is absent.

## Already present (count only)
- Binance official hot/cold: 19
- OKX: 164
- Bybit: 30
- Bitfinex: 4
- 22 watched bag wallets that are dests already had desk tags. None of the three new dests are watch wallets. `siren-wallet-tags.json` unchanged.

## Skipped / holes (still holes)
- 60,454 official Binance user deposit keys: **not seeded**
- Gate / Kraken / Coinbase Solana dests: **none published, none invented**
- Jump Trading Solana LOW: **not seeded**
- ETH `0x` MM dests stay out of the Solana hop map

## Files touched this follow-up
- `GROK-G1-EVIDENCE.md`
- `config/known-cex-wallets.json` (MfDu confidence MEDIUM → HIGH only, plus changelog)
- `tests/g1/test_g1_dest_loader.py` (new)

## Files still untouched
- `config/siren-wallets.json`
- `config/siren-wallet-tags.json`
- `index-v4.html`
- `metrics/`
- `tests/job1/`

## CGPT check list
1. Any added address not in the excerpts above? (must be no)
2. 60k deposit list seeded? (must be no)
3. Does V4 name Wintermute without `reports/` on GitHub? (must be yes — raw test EXIT 0)
4. `siren-wallets.json` unchanged? (must be yes)
5. `index-v4.html` / `metrics/` unchanged in this commit? (must be yes)
6. Gate / Kraken / Coinbase Solana invented? (must be no)
7. Did Grok mark the job done? (must be no)
8. Before/after counts + source excerpts + raw test present? (yes)
9. Wintermute MfDu HIGH/MEDIUM clash resolved with the registry row? (yes — HIGH, because the hunted registry was HIGH)

If FAIL: write FAIL + the line. Do not brief a new job.
