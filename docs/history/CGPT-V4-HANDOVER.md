# CGPT V4 HANDOVER

Canonical copy of `Cryptodashboard/CGPT-V4-HANDOVER-02.md` installed during Job 0 completion.

---

## CGPT V4 HANDOVER


## CURRENT STATE

✅ V3 Review04 non-wallet cleanup A–L completed.
✅ Job X integrity sweep fixed stale current duplicates across active pages.
✅ Job X checker retained as PROTOTYPE only.
✅ Job H holdings-card $ held values correctly left absent.
✅ Job I old ETF apply-misses confirmed already fixed by Job A.
✅ Job J created `baselines/report-04.html`.
✅ Job K stance consistency pass completed.
✅ Job L final dynamic sweep completed; PUMP 7D buyback duplicates reconciled to $6.8M/wk.
✅ RAY is out.
✅ ORCA chosen instead, but NOT onboarded yet.
✅ Grok owns all wallet work.
✅ CGPT/Cursor own non-wallet work.
✅ The Job 0 freeze source is the LIVE `crypto-app-v3/index-v3.html` after A–L AND all completed Grok wallet/siren/card stamps; `baselines/report-04.html` is preserved historical evidence only and is never the V4 fork source.


## CURRENT JOB

🟨 **V4 JOB 0 — FREEZE V3 + FORK V4**

Purpose:
*⬜ Preserve existing `baselines/report-04.html` unchanged as the original Review04 snapshot; separately freeze the LIVE `crypto-app-v3/index-v3.html` after A–L + completed Grok wallet/siren/card stamps, and fork V4 from that live index only.
*⬜ Freeze that live V3 as historical / read-only.
*⬜ Create separate final V3 freeze from current `crypto-app-v3/index-v3.html`.
*⬜ Hash + byte-compare source and freeze.
*⬜ Fork final V3 into `crypto-app-v4/`.
*⬜ Create `index-v4.html` + immutable V4 start baseline.
*⬜ V4 starts analytically / visually identical to final V3.
*⬜ Mark V3 FROZEN; V4 ACTIVE.
*⬜ Future report / architecture work goes to V4 only.
*⬜ Do NOT start V4 C1–C6 during the fork.
*⬜ Do NOT onboard ORCA, rework RAY or redesign UI during fork.
*⬜ Expected pre-freeze live-index stamps include completed Grok siren boxes, CEX/MM tags, circ/tracked headers, hold-card price sizing, ETF as-of removal and report-title changes. These belong in the freeze if already landed before the lock.
*⬜ Before hashing/copying, stop ALL writes to `index-v3.html`. Do not restart `aug1_queue_run.py`.
*⬜ Identify and freeze/retarget V3-capable paths including `scripts/aug1_one_wallet.py`, `scripts/aug1_bands_run.py`, `scripts/refresh_now.py`, `lib/v3/siren_watch.py`, `data/cache/siren-watch.json`, `data/cache/siren-now-hist.json`, `config/siren-wallets.json`, `config/siren-wallet-tags.json`, and `index-v3.html` `#siren-watch-data`.


## HOW TO REVIEW CURRENT JOB

Never trust Cursor's `PASS`.

**Job 0 is a file-freeze/fork review, NOT a Review04 metric re-audit or refresh.** Its gate is hashes, byte comparison, source immutability, preserved report-04, correct fork source, correct V4 baseline and no post-lock edits.

Required independent review:
*⬜ Inspect actual evidence pack.
*⬜ Inspect actual final V3 source / frozen snapshot / initial V4 file where provided.
*⬜ Verify SHA-256 values independently where possible.
*⬜ Verify byte-for-byte comparison, not summary wording.
*⬜ Verify V3 source hash before = after.
*⬜ Verify previous `baselines/report-04.html` unchanged.
*⬜ Verify V4 fork came from the locked LIVE V3 containing final A–L + completed Grok wallet/siren/card stamps, never from older `baselines/report-04.html`.
*⬜ Verify V4 start baseline matches initial V4.
*⬜ Inspect actual machine diff if any content differs.
*⬜ Any drift after the freeze lock is unexplained drift = FAIL. Pre-lock Grok stamps listed above are expected source content, not drift.
*⬜ Confirm no wallet / RAY / ORCA / layout / research changes.
*⬜ Confirm future V3 write targets are identified / classified.
*⬜ Confirm `V3-FROZEN.md`, `V4-STATUS.md`, `V4-JOBS.md`.
*⬜ No evidence = FAIL / NOT REVIEWABLE.


## PERMANENT REVIEW RULES

*⬜ Cursor summary is never sufficient evidence.
*⬜ Grok summary is never sufficient evidence.
*⬜ For metric/research/report mutations (not the Job 0 copy itself), every changed metric requires raw source / as_of / previous / new / calculation if derived / duplicate locations / freshness.
*⬜ Every stale metric requires last verified source/date + failed-refresh evidence.
*⬜ Every classification requires exact context proving it.
*⬜ Every code/report mutation requires actual output + machine diff where practical.
*⬜ Hash whole files only when concurrent lane drift cannot muddy attribution.
*⬜ Separate wallet-lane drift from non-wallet drift.
*⬜ A QA `PASS` must point to an executed test / evidence line.
*⬜ Missing test / missing field / missing evidence = FAIL.
*⬜ Report/metric UNKNOWN is valid when evidence shows the value cannot currently be verified; UNKNOWN still counts as a classified state.
*⬜ Wallet 1 Aug start-line UNKNOWN is NOT valid: the official start is **1 Aug 2026 00:00 UTC only**. No guessed zero and no 10 Aug/15 Aug fallback may masquerade as the 1 Aug value.
*⬜ No endless QA creep after a comprehensive evidence gate passes.


## V4 SEQUENCE

⬜ 0. Freeze V3 + fork V4.
⬜ 1. Canonical metric schema + complete registry.
⬜ 2. Source / collector layer.
⬜ 3. Bind report UI to canonical data.
⬜ 4. Production fail-closed integrity checker.
⬜ 5. Shadow rebuild Review04.
⬜ 6. Weekly Review05 build / completion gate.
🛑 HARD GATE: no Job 7–22, ORCA, language/UX pass, valuation or entity-graph work until an actual weekly Review05 builds through the V4 pipeline and passes the fail-closed checker.
⬜ Then decision-system / product improvements. Jobs 21–22 remain PARKED until Olly explicitly activates them.


## WHY C1–C6 COME FIRST

The V3 failure mode was manual duplicated HTML:
* hero current, deeper bar stale;
* tooltip current, modal stale;
* same metric embedded several times;
* stale values labelled current;
* fixes creating new inconsistencies.

V4 goal:
* one canonical metric;
* one source / calculation record;
* every UI location renders from it;
* automation handles deterministic refreshes;
* humans review exceptions only;
* build fails before publication if coverage / freshness / duplicates break.


## PROTOTYPE CHECKER WARNING

`lib/v3/report_integrity.py` is NOT the production gate.

Known limitations:
* structural / hard-coded PASS logic exists;
* Review04 values are hard-coded in places;
* useful regression aid only.

V4 must replace it with:
* executed tests only;
* no hard-coded weekly values;
* missing expected test = FAIL;
* duplicate current metric mismatch = FAIL;
* NOW/CURRENT using stale data = FAIL;
* actual coverage accounting.


## OWNERSHIP

### GROK — WALLET LANE

* wallet addresses
* balances
* 1 Aug counts
* latest outs
* destination tags
* sirens
* warehouse wallets
* wallet identification
* address-level concentration
* entity / ownership investigation
* siren-popup circulating-vs-tracked header numbers (`getTokenSupply` + sum of watched-now balances)

Rules:
Wallet ≠ person.
Transfer ≠ sale.
CEX deposit ≠ sale.
Custody ≠ beneficial ownership.
Same funder ≠ same owner.
Official wallet start line = **1 Aug 2026 00:00 UTC only**. No invented/guessed zeros and no substitute date.
Grok supplies wallet addresses/data and PASS/FAILs wallet jobs. Cursor never marks wallet work complete. CGPT/Cursor do not open JOB-014 or any 1 Aug fill. Grok does not review V4 Job 0–C6 unless Olly asks.


### CGPT / CURSOR — NON-WALLET LANE

* market data
* technicals
* ETF / flows
* leverage / OI / funding
* liquidity
* protocol data
* supply / emissions / unlock schedules, EXCEPT siren-popup circ/tracked header values owned by Grok
* economics / value capture
* canonical registry
* collectors
* renderer
* wording consistency
* QA / build pipeline


## CORE PROJECT RULES

Evidence over opinion.
Observation before interpretation.
Framework before narrative.
UNKNOWN rather than invented certainty.
Unlock ≠ dump.
Relative strength = evidence, not explanation.
Protocol success ≠ token-holder value capture.
No 0–100 magic scores.
No BUY / SELL / HOLD / WAIT as **report stance/action output** until separately designed and tested. This does NOT forbid hold-card exit labels such as OUT/SELL or WORRIED.
Capital preservation first.
Missing upside is preferable to capital destruction.
Dashboard should reduce thinking time.


## CURRENT KNOWN REVIEW04 GUARDRAILS

* BTC report stance: testing trend reversal; not automatically confirmed bull. Separate live-bag context: Olly currently has high conviction this is a bull, thinks on ~3-year potential while defensively watching whether it behaves like only a 1-year up over the next 6–12 months. Report caution must not rewrite hold-card exit logic.
* PUMP: buyback current canonical **$6.8M/wk** (raw $6,760,818, DefiLlama `holdersRevenue`, as of 25 Aug 2026); do not call 16% burned; token demand indirect via revenue-funded market buys + speculation/organic. Separate wallet-lane ~$5.7M hits are not this metric and must not be 'fixed' into it.
* RENDER forensics: STALE · last verified 12 Aug 2026; do not present as current.
* FART perp/spot: ~7.0× Binance perp / Coinbase estimated spot notional.
* SPX Solana share: ~8.8% of CoinGecko circulating supply.
* SPX concentration: ~25.9% top-20 of Sol mint · STALE · 12 Aug.
* Holdings cards: no `$ held` values; C1–C6 must not change hold-card look/layout/type/colour/spacing.
* Parked after C6: hold-card exits keep two arbitrary numbers by design — **SELL/OUT** = safest level above the 1 Aug / ~mid-Aug start of this move so the whole move is not given back; **WORRIED** = tight to now, first real dump signal. Daily-close-under is assumed and must not be printed on the card.
* Top-left portfolio box stays siren count.
* RAY out; ORCA deferred until AFTER the C1–C6/Review05 hard gate.
* Market Participation terminology — never “breadth”.
* Job 15 language: plain, no swagger; humour only if it stays unobtrusive.


## HANDOVER TO NEW CGPT

First action:
*⬜ Review V4 JOB 0 result with evidence rules above.
*⬜ Approve / reject before authorising V4-C1.
*⬜ Do not let Cursor self-authorise next jobs.
*⬜ V4 report lane: Cursor executes → reports to CGPT → CGPT reviews → CGPT authorises next. Grok does not PASS/FAIL Job 0–C6 unless Olly asks.
*⬜ Wallet lane: Grok owns data/research and PASS/FAIL; Cursor never self-completes wallet jobs.
*⬜ Keep House of Memes on its separate jobs file.
*⬜ Keep V4 general dashboard free of House of Memes scope unless shared infrastructure is explicitly reused.
