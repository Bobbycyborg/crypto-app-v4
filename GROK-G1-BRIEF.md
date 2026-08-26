# G1 BRIEF — Grok to Grok (and CGPT check)

**Job:** G1. Seed proved dests already hunted  
**Owner:** Grok  
**Review:** CGPT reads this brief + the evidence pack + the diff. CGPT does not hunt, brief, or write wallet code. Cursor stays out. Grok does not mark this done.  
**Live file:** `crypto-app-v4` only. GitHub is the bible.  
**Not:** Job 1, C1–C6, Job 17, HOM, V3 writes, 1 Aug walks.

---

## For Oliver (dummy)

When a watched wallet sends coins somewhere, we need to know if that place is a desk (Binance, Bybit, OKX, Bitfinex, Wintermute, and the rest). If it is, the siren should say the desk name. We already found those desk addresses. This job puts the missing proved ones on the live watch and makes sure V4 can actually read them. Any send still raises eyes. A desk name is the loud one. No new hunting. No invented wallets. Nothing else on the page changes.

---

## Intention — full, no shortcuts

G1 is **not** “go hunt again.”  
G1 is **not** “add 60,000 Binance deposit keys.”  
G1 is **not** a new siren UI.  
G1 is **not** 1 Aug counts.  
G1 is **not** Job 1 metrics.

G1 **is**:

1. Take dests we already proved from official / named sources.
2. Put every missing HIGH / MEDIUM dest onto the V4 dest-watch the live checker actually reads.
3. Make the V4 checker able to name a desk when a watched wallet sends there.
4. If a watched bag wallet **is** itself a dest, stamp its tag so the popup says the desk name (already true for 22; keep that true after the seed).
5. Leave every other file and every other behaviour alone.

Any transfer raises eyes. Follow the hop. Know the dest. A hop to a nameless wallet stays on the watch. A hop to a named desk is the loud siren. Do **not** write “transfer is not a sale” in a way that sounds like ignore it.

---

## How dest-watch actually works today (must not break)

Live checker: `lib/v3/siren_watch.py`

It builds two maps in `_load_dest_tags()`:

- **CEX map:** every address in `config/known-cex-wallets.json` → `wallets` whose `type` is exactly `"cex"`.
- **MM map:** Solana wallets in `reports/shared-mm-registry/shared-entity-wallet-registry.json` with confidence HIGH or MEDIUM.

A send is loud when `_last_outbound_dest()` finds a hop in one of those maps.

Hard facts already checked (26 Aug 2026):

- `known-cex-wallets.json` has **301** addresses: 227 `cex`, 64 `custody`, 8 `mm`, 2 `treasury`.
- Official Binance Solana hot/cold **19** are already in that file. Missing vs that dump: **0**.
- OKX 164, Bybit 30, Bitfinex 4 are already in that file.
- Wintermute Solana `MfDuWeq…GVWa` is in the file as `type: "mm"`. That means it is **not** in the CEX map.
- V4 has **no** `reports/shared-mm-registry/` (reports stay off GitHub). So the MM map path **fails on V4**. Hops to Wintermute / DWF Solana can fail to name the desk even though we already proved them.
- 22 watched bag wallets already match dests and already have desk tags (Wintermute, Binance, Bybit).
- Gate / Kraken / Coinbase still have **no** published Solana dest list. Do not invent them.
- 60,454 official Binance **user deposit** keys exist in the hunt pack. They are **not** dests for this job. Do not seed them.

So the real G1 hole is: **proved MM dests (and any stray HIGH dest) are not loaded by the V4 checker**, plus a last pass that every hunted HIGH/MEDIUM dest is in a file V4 can read.

---

## Exact files I will touch

Allowed:

- `config/known-cex-wallets.json` — add only missing proved dests; keep existing rows; set `type` correctly (`cex` or `mm`).
- `config/known-mm-wallets.json` — **new lean file** if needed, so V4 can load MM dests without a reports folder. Solana HIGH/MEDIUM only. No reports on GitHub.
- `config/siren-wallet-tags.json` — only if a **already-watched** wallet is a dest and its tag does not already say the desk. No new watch wallets. Tags only, no raw addresses in the UI.
- `lib/v3/siren_watch.py` — dest **loader only**: also treat `type == "mm"` from known-cex as MM dests, and load `config/known-mm-wallets.json` if present. If the old reports path exists locally, still read it. Do not change loud logic, 1 Aug, UI chrome, or hop following.
- `GROK-G1-BRIEF.md` (this file)
- `GROK-G1-EVIDENCE.md` (the check pack)

Forbidden (do not open to edit):

- `index-v4.html` (Job 1 live page / hold cards / metric boxes / ALT Moves)
- `metrics/`, `tests/job1/`
- `config/siren-wallets.json` (do not add or drop watch wallets)
- `config/wallet.json`, `config/capital.json`, `config/helius.local.env`
- V3 `index-v3.html` and V3 config
- 1 Aug stamps, UNKNOWN fills, RPC/Helius walks
- HOM / FyAz
- Reports zips on GitHub
- 60k Binance deposit keys
- Invented Gate / Kraken / Coinbase Solana dests
- Upgrading MED dests to HIGH
- Hold-card look, SELL/WORRIED, Job 1 values

---

## Exact sources I may use (already hunted)

Only these. If an address is not in one of these, it does not go in.

1. `crypto-app-v3/reports/last-cycle/cex-mm-dest-registry-binance.json` — official Binance Solana hot/cold (19). Already in V4. Confirm still present. Do not add the 60k deposits.
2. `crypto-app-v3/reports/last-cycle/cex-mm-dest-registry.md` — OKX / Bybit / Bitfinex official PoR dests already copied into known-cex on 21–22 Aug. Diff and add only rows that are missing.
3. `crypto-app-v3/reports/shared-mm-registry/shared-entity-wallet-registry.json` — Wintermute / DWF Solana HIGH or MEDIUM only. Jump Solana LOW stays out.
4. Addresses already in `config/known-cex-wallets.json` with a real source URL and type cex/mm.

If a source is missing or the address is not in the file, skip. Write the skip in the evidence pack. Do not guess.

---

## What “done” looks like (this is what CGPT checks)

A. **Dest map on V4 actually loads desks.**  
A loader test (no live RPC required) prints: CEX count, MM count, and that Wintermute Solana `MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa` resolves to Wintermute. Before G1 this MM resolve can fail on V4. After G1 it must succeed.

B. **No invented wallets.**  
Every **new** address in the diff is in one of the source files above, with the same entity name. CGPT can grep the evidence table.

C. **No 60k dump.**  
`known-cex-wallets.json` does not jump by tens of thousands of keys.

D. **Watch list unchanged.**  
`config/siren-wallets.json` diff is empty.

E. **Tags only if needed.**  
`siren-wallet-tags.json` only changes when a watched wallet is a dest and the tag did not already name the desk. UI still shows tags, not raw addresses.

F. **Job 1 / page chrome untouched.**  
`index-v4.html`, `metrics/`, hold cards, ALT Moves: no diff.

G. **1 Aug untouched.**  
No new 1 Aug walks. No UNKNOWN. No guessed zeros.

H. **Holes stay holes.**  
Gate / Kraken / Coinbase Solana dests remain unseeded and listed as holes. MED Solscan-only Binance tags stay MED.

I. **Evidence pack exists** at `GROK-G1-EVIDENCE.md` with:

- before / after dest-map counts (CEX n, MM n)
- table of **added** addresses: entity, chain, type, source file, confidence
- table of **already present** (count only, not a dump)
- skipped / holes
- files touched
- files proved untouched (`git diff --name-only`)
- loader test output
- statement: Grok has not marked this done

J. **Grok does not PASS.**  
CGPT writes PASS or FAIL on the pack. I read that. Olly does not brief either side.

---

## What I will not “helpfully” do

- Do not restyle the siren popup.
- Do not rename tags Oliver already has (Grass3, Pump23, Render2, etc.).
- Do not start G2–G5.
- Do not refresh GRASS (dormant).
- Do not onboard ORCA dests beyond what is already watched.
- Do not run a paid Helius burst.
- Do not launch a cloud agent.
- Do not commit Job 1 WIP.
- Do not put reports on GitHub.

---

## Order of work

1. Publish this brief.
2. Snapshot before counts (loader, if it currently errors, record the error).
3. Diff hunted HIGH/MEDIUM dests vs V4 dest files.
4. Add only missing proved dests.
5. Fix the V4 dest loader so type=mm and `config/known-mm-wallets.json` are read.
6. Stamp tags only where a watched wallet is a dest and unnamed as a desk.
7. Re-run loader test.
8. Write `GROK-G1-EVIDENCE.md`.
9. Commit only the allowed files.
10. Stop. Wait for CGPT on the pack.

---

## CGPT review questions (answer only from the pack + diff)

1. Did Grok add any address that is not in the listed source files?
2. Did the 60k deposit list get seeded? (FAIL if yes)
3. Does the V4 loader now name Wintermute Solana without needing `reports/` on GitHub?
4. Is `siren-wallets.json` unchanged?
5. Is `index-v4.html` / `metrics/` unchanged?
6. Were Gate / Kraken / Coinbase Solana dests invented? (FAIL if yes)
7. Did Grok mark the job done himself? (FAIL if yes)
8. Does the evidence pack have before/after counts and the added table?

If any is FAIL, write FAIL + the line. Do not brief a new job. I read the file and fix only that line.
