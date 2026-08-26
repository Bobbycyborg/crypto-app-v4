# G5 BRIEF — Grok to Grok (and CGPT check)

**Job:** G5. Skinny pages: Orca / Drift (Velocity) / 2Z  
**Owner:** Grok  
**Review:** CGPT reads this brief + the evidence pack + the diff. CGPT does not hunt, brief, or write wallet code. Cursor stays out. Grok does not mark this done.  
**Live file:** `crypto-app-v4` only. GitHub is the bible.  
**Not:** Job 1, C1–C6, Job 17, Job 19 ORCA onboard, HOM, V3 writes, G1 dest seed, G2 leftover 1 Aug walks (skipped, Oliver approved).

G2–G4 PASSed on `e9ea2f9`. This job is now clear.

---

## For Oliver (dummy)

Three skinny pages. Not weekly reports. Not a thesis.

2Z: unlock — when, how big, who, dest-watch on those wallets. One proved “is it earning” line if it exists.

Drift: the exchange is now Velocity. Old Drift is paused. Page answers: is Velocity open, how many markets, what is the take vs pre-hack, dest-watch on Foundation / Team. Users coming back = volume and markets, not a rename.

Orca: does the DEX still take fees, and does ORCA get them. Treasury dest-watch. One volume line.

Memes stay on cards. FART and SPX already have fat pages. Do not add meme pages. Do not onboard ORCA as Job 19. Do not restyle hold cards. Do not invent unlock size or Velocity volume.

---

## Intention — full, no shortcuts

### G5 is
Three standalone skinny HTML pages on the V4 repo that Oliver can open. Bare guts only. Every number has a source URL or is written UNKNOWN.

### G5 is not
- A full weekly report (no signal pallets, no thesis, no week dropdown, no SELL/WORRIED)
- Job 19 ORCA onboard (no new ORCA metrics, no hold-card changes, ORCA card stays as it is)
- Embedding fat `asset-v3-report` articles into `index-v4.html`
- Touching Job 1 `metrics/` or `tests/job1/`
- New dests, new watch wallets, 1 Aug walks
- Invented 2Z unlock size
- Calling Velocity “Drift v3 live and used” unless volume/markets prove users came back
- Meme pages
- Cloud agents

### Why standalone, not inside index-v4
Job 1 owns `index-v4.html`. 2Z / DRIFT / ORCA cards have no report article today. Splicing three articles into the live index is a Job 1 collision. Pages live under `skinny/`. Click-path from hold cards is a later ask, not this job.

---

## Drift page must say this (already proved 26 Aug)

- Same team. Rebrand 1 July 2026. `@driftprotocol` is now `@VelocityDEX`.
- `app.drift.trade` and `docs.drift.trade` redirect to Velocity.
- `www.drift.trade` is leftover marketing chrome.
- Old program `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH` is paused.
- New program `vELoC1audYbSYVRXn1vPaV8Axoa9oU6BYmNGZZBDZ1P`.
- No balances carry over. Quote is USDT, not USDC.
- Official: https://docs.velocity.exchange/developers/migrate-from-drift (updated 24 Aug 2026).
- Private beta press: ~25 Aug 2026. Confirm on the page with the dated source. If still private beta, say private beta, not “fully open.”
- Markets: Oliver saw ~4 vs old Drift 40+. Count live perps from Velocity or a dated listing. If only 4, write 4.
- Take / volume: DefiLlama or Velocity API. If unlisted or $0, write that. Do not invent a healthy book.
- Dest-watch: existing tags only — Foundation `9Wiiyvy8zzbZ…`, Team `HPjkU5hUR1di…`, Team `DemTRm4sQbLx…`. Tags, not raw addresses in the UI.
- Recovery tokens / Tether credit: one line, not the page.

“Did users come back” = live markets + live volume vs pre-hack Drift, not the rename.

---

## 2Z page

- Unlock: date, size, who — **official PDF / official site only**. https://doublezero.xyz/2z-tokenomics-disclosure.pdf
- Unlock calendars (tokenomics.com etc) may be listed as unofficial if they disagree. Do not treat them as first-party.
- Who: Foundation / Jump / Team only if the official source prints those names on those wallets. G4 already refused Coinranking FOUNDATION. TwoZ1 / TwoZ7–11 stay number tags.
- Dest-watch: those tagged wallets. Any transfer raises eyes. Desk dest is the loud siren.
- One earning line only if proved (usage / fees). Else UNKNOWN.
- No thesis.

---

## Orca page

- One volume line (DefiLlama or official, dated).
- Does the DEX still take fees? Prove.
- Does ORCA the token get them (buyback / DAO / xORCA / fee treasury)? Official docs only. If the path is “fees sit in Fee treasury” and capture is unproved, say that.
- Dest-watch: Community treasury, Fee treasury, xORCA vault — already tagged. Do not add new official wallets this job.
- Not a DEX explainer. Not Job 19.

---

## Exact files I will touch

Allowed:

- `skinny/2z.html`
- `skinny/drift.html`
- `skinny/orca.html`
- `skinny/skinny.css` (shared, match existing V4 cream/ink/Jost/DM Sans — no new chrome)
- `GROK-G5-BRIEF.md` (this file)
- `GROK-G5-EVIDENCE.md`
- `GROK-JOBS.md` — G5 line only if a one-line status is needed
- `README.md` — one line that the three skinny pages exist, optional

Forbidden:

- `index-v4.html` (Job 1 live page / hold cards / ALT Moves)
- `metrics/`, `tests/job1/`
- `config/siren-wallets.json`, `config/siren-wallet-tags.json`
- `config/known-cex-wallets.json`, `config/known-mm-wallets.json`
- `lib/v3/siren_watch.py`
- `alt-moves/`
- V3
- Job 19 ORCA onboard
- Meme pages
- Invented dests / invented unlocks

---

## What “done” looks like (CGPT checks)

A. Three pages exist and open. Each is skinny: title, a few guts lines, dest-watch tags, sources. No weekly-report chrome.

B. Every number has a source URL in the evidence pack. UNKNOWN is allowed. Guessed unlock / guessed volume is FAIL.

C. Drift page names Velocity, paused old program, market count, volume-or-unlisted. Does not say “v3 is live and used” unless volume proves it.

D. 2Z unlock who/size only from official source, or marked unofficial / UNKNOWN.

E. Orca page has one volume line + fee capture line + existing treasury dest-watch.

F. `index-v4.html`, `metrics/`, hold cards, siren files: no diff.

G. No new wallets. No G2 leftover walks.

H. Evidence pack at `GROK-G5-EVIDENCE.md` with sources, files touched, `git diff --name-only`, statement: Grok has not marked this done.

I. Grok does not PASS.

---

## What I will not “helpfully” do

- Do not splice pages into hold-card clicks.
- Do not restyle the dashboard.
- Do not start Job 19.
- Do not walk the 16 skipped 1 Aug boxes.
- Do not refresh GRASS.
- Do not launch a cloud agent.
- Do not commit Job 1 WIP.

---

## Order of work

1. Publish this brief.
2. Prove facts (official pages + DefiLlama / Velocity). Write holes as UNKNOWN.
3. Build the three pages.
4. Write `GROK-G5-EVIDENCE.md`.
5. Commit only allowed files.
6. Stop. Wait for CGPT.

---

## CGPT review questions (pack + diff only)

1. Did Grok invent a 2Z unlock size not in the official PDF/site? (FAIL if yes)
2. Did Grok invent Velocity volume? (FAIL if yes)
3. Does the Drift page treat Velocity as “users came back” without a volume/market prove? (FAIL if yes)
4. Is `index-v4.html` / `metrics/` / `tests/job1/` in the commit? (FAIL if yes)
5. Were any wallets added or renamed? (FAIL if yes)
6. Are the pages fat weekly reports? (FAIL if yes)
7. Did Grok mark this done himself? (FAIL if yes)
8. Is Job 19 ORCA onboard in the diff? (FAIL if yes)

If any is FAIL, write FAIL + the line. Do not brief a new job.
