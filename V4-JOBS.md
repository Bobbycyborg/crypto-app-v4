# V4 JOBS

Canonical V4 work queue. Copied from `Cryptodashboard/v4-jobs-list-04.md` during Job 0 completion (docs + V3 write quarantine). Do not use older Job 0 job lists.

Job 0 is not self-approved. Job 1 / C1–C6 not started.

---

## V4 JOBS LIST


## V4 MIGRATION / AUTOMATION CORE

**Review ownership:** V4 report lane = Cursor executes → CGPT independently reviews → CGPT authorises next. Grok does not review Job 0–C6 unless Olly asks. Wallet lane = Grok owns data/research and PASS/FAIL; Cursor never marks wallet work complete. HOM remains outside this jobs file.

🟨 **0. Freeze V3 + fork V4**

*⬜ Preserve existing `baselines/report-04.html` unchanged as the original Review04 snapshot; separately freeze the LIVE `crypto-app-v3/index-v3.html` after A–L + completed Grok wallet/siren/card stamps, and fork V4 from that live index only.
*⬜ Freeze that live index separately as the immutable final V3 historical product.
*⬜ Hash / byte-compare final V3 source and freeze.
*⬜ Duplicate final V3 into `crypto-app-v4/`.
*⬜ Create `index-v4.html` + immutable V4 start baseline.
*⬜ Initial V4 must be byte-identical to the locked live final V3 except only where an explicitly evidenced path/name change is technically required; any difference must have a machine diff and explanation.
*⬜ Mark V3 FROZEN / READ-ONLY; V4 ACTIVE DEVELOPMENT.
*⬜ Future report / architecture work targets V4 only.
*⬜ Expected pre-freeze live-index content includes completed Grok siren boxes, CEX/MM tags, circ/tracked headers, hold-card price sizing, ETF as-of removal and report-title changes. These are source content if already landed before the lock, not fork drift.
*⬜ Before hashing/copying, stop ALL writes to `index-v3.html`; do not restart `aug1_queue_run.py`.
*⬜ Identify, freeze or retarget V3-capable paths including `scripts/aug1_one_wallet.py`, `scripts/aug1_bands_run.py`, `scripts/refresh_now.py`, `lib/v3/siren_watch.py`, `data/cache/siren-watch.json`, `data/cache/siren-now-hist.json`, `config/siren-wallets.json`, `config/siren-wallet-tags.json`, and `index-v3.html` `#siren-watch-data`.
*⬜ Do not onboard ORCA, rework RAY, redesign UI or start C1–C6 during fork.
*⬜ Evidence required: hashes, byte compare, actual files, command log, manifest, machine diff where relevant.
*⬜ Cursor PASS is not evidence — CGPT independently reviews artifacts.
*⬜ Job 0 review is FILE COPY/FREEZE QA ONLY: hashes, byte compare, V3 source unchanged after lock, report-04 unchanged, correct live-index fork source, V4 start match, no extra edits. Do NOT re-audit or refresh Review04 metrics here.

### LOCKED BOUNDARIES FOR C1–C6

*⬜ No `$ held` on hold cards. Top-left portfolio box stays siren count. RAY stays out. ORCA stays absent. No hold-card look/layout/type/colour/spacing changes.
*⬜ Hold-card OUT/SELL and this-move concepts are not forbidden report action words and must not be stripped by schema/UI/language work.
*⬜ PUMP 7D buyback canonical = **$6.8M/wk** (raw **$6,760,818**, DefiLlama `holdersRevenue`, as of **25 Aug 2026**). Separate wallet-lane ~$5.7M hits are not this metric and must not be reconciled into it.
*⬜ RENDER forensics and SPX top-20 concentration remain **STALE · 12 Aug 2026** unless a collector genuinely refreshes them and records `as_of`.
*⬜ Use **Market Participation**, never “breadth”.
*⬜ Siren popup circ/tracked headers remain Grok-owned; CGPT supply/emissions ownership does not override those visible wallet-lane numbers.
*⬜ Wallet official start line = **1 Aug 2026 00:00 UTC only**; no 15 Aug wallet-start record.


⬜ **1. Canonical metric schema + complete registry**

*⬜ Create one canonical record per dynamic metric: metric_id / asset / value / raw_value / unit / scope / definition / source / as_of / fetched_at / freshness / calculation_version / owner.
*⬜ Every visible card, tooltip, modal, bar, summary and evidence section must render from the same underlying record.
*⬜ One metric = one canonical value; formatting variants derive from it.
*⬜ Add automatic visible-value ↔ evidence-value consistency checks.
*⬜ If credible sources genuinely disagree, show **CONFLICT / UNKNOWN** rather than silently choosing one.
*⬜ Any stance materially dependent on a conflicted metric must be suspended or explicitly qualified.
*⬜ Add freshness / stale-data rules and fail safely to UNKNOWN.
*⬜ Separate market/protocol / wallet / narrative / rendered-output lanes.
*⬜ Grok owns wallet records; CGPT/Cursor own non-wallet records. Siren-popup circ/tracked headers remain Grok-owned visible numbers.
*⬜ Wallet start-line date is **1 Aug 2026 00:00 UTC only**; never synthesize a 15 Aug wallet start.
*⬜ No hard-coded Review04 values in production logic.


⬜ **2. Source / collector layer**

*⬜ Move repeatable source retrieval / calculation out of HTML editing.
*⬜ Build reusable collectors for market, technical, flow, leverage, liquidity, supply, protocol and economics data.
*⬜ Preserve raw source evidence behind every collected metric.
*⬜ Every collector returns FRESH / STALE · LAST VERIFIED [date] / UNKNOWN.
*⬜ Failed fetch must never silently become zero, unchanged or fresh.
*⬜ Store exact source / raw value / as_of / fetched_at / method / calculation.
*⬜ Derived metrics must reproduce from raw inputs.
*⬜ Separate Grok wallet ingestion from non-wallet collectors. C1–C6 must not pull wallet addresses, 1 Aug counts, destinations, sirens or RPC/Helius wallet walks.
*⬜ Add source disagreement / partial coverage / blocked-source handling.
*⬜ Add evidence manifests and fetch logs automatically.


⬜ **3. Bind report UI to canonical data**

*⬜ Stop storing independent current values in hero / bars / mini-dashes / tooltips / risk lines / body / Research Census / WCM.
*⬜ All current representations derive from canonical metrics.
*⬜ Preserve historical values only when explicitly historical.
*⬜ NOW / CURRENT / TODAY labels may only use canonical current metrics.
*⬜ Tooltips inherit value / source / as_of / freshness from the same record.
*⬜ Formatting differences allowed; independent values are not.
*⬜ Eliminate duplicate-number failure mode seen in SPX and PUMP.
*⬜ UI rendering fails visibly on missing canonical records rather than reusing stale embedded text.
*⬜ C3 DO-NOT-TOUCH: no `$ held` on hold cards; top-left box stays siren count; RAY stays out; ORCA stays absent; no hold-card look/layout/type/colour/spacing changes; do not strip existing OUT/this-move concepts or treat hold-card SELL/OUT as a forbidden report action word.


⬜ **4. Production fail-closed integrity checker**

*⬜ Replace prototype `lib/v3/report_integrity.py` with production V4 checker.
*⬜ No `stat(True)` / placeholder PASS logic.
*⬜ No hard-coded weekly values.
*⬜ Every PASS must be an executed test.
*⬜ Missing expected field / test = FAIL / COVERAGE GAP.
*⬜ Test active asset / canonical metric coverage.
*⬜ Test current-price / return / liquidity / economics duplicate consistency.
*⬜ Test ATH / drawdown arithmetic.
*⬜ Test MA numeric ↔ ABOVE/BELOW language.
*⬜ Test RS sign ↔ LEADS/LAGS language.
*⬜ Test freshness / as-of / stale-state consistency.
*⬜ Test tooltip / visible / visual-bar agreement.
*⬜ Test derived metric arithmetic.
*⬜ Permanent regression testcase: SPX current-price duplicate.
*⬜ Permanent regression testcase: PUMP $6.8M vs stale $5.7M / $5.2M duplicate.
*⬜ No evidence / no test = FAIL.


⬜ **5. Shadow rebuild Review04**

*⬜ Recreate final cleaned Review04 from collectors + canonical data + renderer.
*⬜ Do not use hand-corrected HTML as the data source.
*⬜ Compare shadow output against frozen final V3.
*⬜ Classify every difference.
*⬜ Fix pipeline defects, not individual HTML occurrences.
*⬜ Reproduce fresh / stale / UNKNOWN states. UNKNOWN with evidence is a classified state, not an error by itself.
*⬜ Reproduce duplicate consistency across cards / bars / tooltips / body.
*⬜ Prove wallet lane can plug in separately without contaminating non-wallet diffs.
*⬜ Freeze only after zero unexplained differences.


⬜ **6. Weekly Review05 build / completion gate**

*⬜ Weekly flow: FETCH → CALCULATE → CLASSIFY → EXCEPTIONS → HUMAN REVIEW → RENDER → FAIL-CLOSED QA → PUBLISH.
*⬜ Oliver reviews exceptions, not hundreds of duplicated fields.
*⬜ Report metrics expected / fresh / stale / unknown / historical / unclassified.
*⬜ Unclassified > 0 = FAIL. **UNKNOWN with evidence is classified as UNKNOWN and does not count as unclassified.**
*⬜ Coverage gaps > 0 = FAIL.
*⬜ NOW / CURRENT on stale data = FAIL.
*⬜ Require page-by-page asset checklist before sign-off.
*⬜ Require actual evidence artifacts for every changed / retained / stale metric.
*⬜ Require machine diff / hashes where code or generated report changes.
*⬜ Cursor PASS never sufficient without evidence.
*⬜ Preserve audit manifest equivalent to V3.
*⬜ FAIL on missing owner, missing expected test/field, coverage gap, silent zero/substitution, or NOW/CURRENT/TODAY on stale data.

### HARD GATE AFTER JOB 6

🛑 **No Job 7–22, ORCA, language/UX pass, valuation, entity graph or second-product work until an actual weekly Review05 is built from the V4 pipeline and passes the fail-closed checker. Jobs 21–22 remain PARKED until Olly explicitly activates them.**

⬜ **6A. Hold-card exit levels — PARKED AFTER C6**

*⬜ Do not implement before Job 6 passes and Olly activates it.
*⬜ Keep exactly two arbitrary exit numbers by design.
*⬜ **SELL/OUT** = safest level above the 1 Aug / ~mid-Aug start of this move so the whole move is not given back.
*⬜ **WORRIED** = tight to now; first real dump signal.
*⬜ Daily-close-under is assumed; do not print that qualifier on the card.
*⬜ This is hold-card risk control, not report BUY/SELL/HOLD stance output.
*⬜ No card restyle as part of this job.


## V4 CORE — DECISION SYSTEM

⬜ **7. Data integrity / conflict presentation**

*⬜ Surface canonical conflict flags in UI where credible evidence disagrees.
*⬜ Separate source conflict from missing data.
*⬜ Show confidence / freshness / evidence quality without pseudo-scientific scores.
*⬜ Audit current V3 conflicts before assuming they still exist; patch only confirmed live issues.


⬜ **8. Decision equation / top-level asset summary**

*⬜ Move V4 one step from research dashboard toward decision system without pretending certainty.
*⬜ Build a compact top-level decision summary around:
* **Token outcome ≈ Demand × value capture − supply pressure**
*⬜ Treat this as a thinking framework, NOT literal maths and NOT a composite score: no composite number, no 0–100 score and no BUY/SELL/HOLD output.
*⬜ Add asset-specific adaptation where the core demand engine differs.
*⬜ Add catalyst / falsifier and tail-risk alongside the equation.
*⬜ Keep **What would change our mind?** central.
*⬜ Preserve **Known / What it suggests / Unknowns**.
*⬜ Default view answers “what matters now?” quickly; deeper evidence remains expandable.
*⬜ No BUY / SELL / HOLD / WAIT as **report decision output** until an evidence-based action framework is designed and tested; this does not apply to parked hold-card OUT/SELL risk levels.


⬜ **9. Valuation / scenario layer**

*⬜ Add valuation only where a defensible comparison framework exists.
*⬜ Build bear / base / bull scenario ranges without false precision.
*⬜ Show what has to become true for each scenario.
*⬜ Separate assumptions from observed evidence.
*⬜ Add required-return / upside-vs-downside context where useful.
*⬜ ZEC: test market cap as % of BTC market cap; 1% / 3% / 5% / 10% scenarios with future issuance.
*⬜ HYPE: circulating market cap / FDV / sustainable fee multiple / buyback-yield framing.
*⬜ GRASS: market cap + FDV vs revenue, durability and token-capture assumptions.
*⬜ Do not force valuation models where they create fake precision.


⬜ **10. Net economics / supply absorption**

*⬜ Convert scattered token-economics evidence into a decision-useful net-economics view.
*⬜ Organic demand + protocol purchases / buybacks / burns − issuance − unlocks − contributor releases − treasury distributions = **net token absorption / dilution pressure**.
*⬜ Keep every component independently sourced and auditable.
*⬜ UNKNOWN components stay UNKNOWN.
*⬜ Distinguish buyback from burn unless burn path is verified.
*⬜ Distinguish scheduled unlock from distributed tokens and distributed tokens from sold tokens.
*⬜ HYPE: Assistance Fund purchases minus emissions / contributor releases / treasury distributions.
*⬜ PUMP: preserve ~50% parent-net-revenue → buyback → burn mechanism and Apr-2027 policy caveat.
*⬜ GRASS: identify measurable bridge from business revenue to actual GRASS demand before strong value-capture claims.


⬜ **11. Change-first weekly decision layer + journal**

*⬜ Make weekly report lead with **what changed**, not repeated full snapshot. Report stance remains separate from hold-card exit/risk logic and must not rewrite the cards.
*⬜ BTC report caution must not overwrite Olly's live-bag context: high conviction bull thesis, ~3-year potential, defensively watched for whether the move behaves like only a 1-year up over the next 6–12 months.
*⬜ Lead each asset with: what changed / stance changed? / evidence / falsifier / unresolved / next watch.
*⬜ Keep full evidence beneath the change summary.
*⬜ Build decision / thesis journal: stance / price / evidence / invalidator / outcome.
*⬜ Record skipped opportunities and false alarms as well as successful calls.
*⬜ Later test which signals actually improved decisions.
*⬜ Use journal evidence to calibrate confidence language rather than inventing scores.


⬜ **12. Risk / confidence / comparability cleanup**

*⬜ Review aggregate risk counters that imply equal weighting between unequal risks.
*⬜ Mild technical concern must not count the same as protocol / legal / custody / exploit risk.
*⬜ Prefer named risk states over pseudo-scientific aggregate scoring; no composite number or 0–100 score.
*⬜ Separate data reliability / freshness / thesis relevance / interpretation confidence / decision sensitivity.
*⬜ Standardise leverage metric scope where possible.
*⬜ Where scope differs, use visibly different labels.
*⬜ Align technical windows with tactical / cycle / long-term horizon.
*⬜ Reduce duplicated evidence across Stance / summary / Risk & Confirmation / Reality Check.
*⬜ Repetition must not masquerade as independent corroboration.
*⬜ Keep secondary / forensic evidence collapsed unless decision-relevant.
*⬜ Elevate catastrophic operational / legal / structural risks above routine technical noise where appropriate.


⬜ **13. Market / regime layer**

*⬜ Build explicit top-level market regime view.
*⬜ Track macro / liquidity capacity, BTC regime, outward rotation, **Market Participation**, sector/ecosystem destination and fragility.
*⬜ Classify indicators as leading / confirming / lagging / noisy / regime-dependent.
*⬜ No one-number “Altseason Score”, regime composite score or 0–100 output.
*⬜ Separate participation from causation.
*⬜ Make regime layer decision-useful and compact.


⬜ **14. Risk & Confirmation framework**

*⬜ Universal 50D / 200D plus asset-specific confirmation / concern signals.
*⬜ No universal ATH zombie filter.
*⬜ Signal states: confirmation / concern / serious concern / unknown.
*⬜ Keep asset-specific evidence where generic indicators are weak.
*⬜ Make confirmations / falsifiers visible without turning them into scores. Do not rewrite hold-card exit levels to mirror report/market-regime language.


⬜ **15. Language / education / learning UX**

*⬜ Final whole-dashboard language pass — plain first; any humour must be sparse and unobtrusive. No swagger.
*⬜ Final plain-English QA.
*⬜ Spell out / explain every acronym.
*⬜ Tooltip = short definition.
*⬜ Learning pop-up = what it is / why it matters / common mistakes.
*⬜ Prioritise Price + Open Interest + Funding + Leverage.
*⬜ Add dashboard-title thesis pop-up with ~5 simple investment-philosophy bullets.
*⬜ Include: “The goal isn’t to predict the future, but to make better decisions with today’s evidence.”
*⬜ Keep as one UX job unless later split deliberately.
*⬜ Job 15 must not restyle hold cards or strip OUT/SELL, WORRIED, or this-move language as 'forbidden' action wording.


⬜ **16. Token-economics refinement**

*⬜ Further mini-dashboard optimisation after live use.
*⬜ Improve compact value-capture visuals where evidence is qualitative.
*⬜ Refine supply / unlock / emission visuals where better history becomes available.
*⬜ Improve cross-asset consistency only where it reduces thinking time.
*⬜ Do not add composite scores.


⬜ **17. Entity Intelligence / Wallet Graph — shared infrastructure**

*⬜ HARD-GATED after Job 6; do nothing until Olly activates it.
*⬜ Cursor/CGPT may build only empty shared plumbing/schema. Grok alone supplies wallet addresses, tags and wallet research. No invented wallets.
*⬜ UI uses entity/tags where appropriate, not raw addresses by default.
*⬜ Shared entity registry / relationships / behaviour-change / historical-snapshot plumbing only after activation.
*⬜ Hard rules: wallet ≠ person; transfer ≠ sale; CEX deposit ≠ sale; custody ≠ beneficial ownership/owner; same funder ≠ same owner.
*⬜ Cursor/CGPT must not pull 1 Aug counts, destinations, sirens, RPC/Helius wallet walks or open JOB-014/1 Aug fill.
*⬜ No paid Helius burst and no cloud agents unless Olly separately authorises them.
*⬜ Grok PASS/FAILs wallet jobs; Cursor never marks wallet work done.
*⬜ Make shared infrastructure reusable by asset pages and separate products without contaminating the report lane.


⬜ **18. Additional technical / market intelligence**

*⬜ Add technical indicators only where they improve decisions.
*⬜ Improve historical signal context / regime comparison.
*⬜ Richer ETF / fund-flow history where useful.
*⬜ New metrics only when clearly decision-useful.
*⬜ Further classifier / framework work only if live use exposes a real need.


⬜ **19. ORCA onboarding**

*⬜ RAY is out.
*⬜ Onboard ORCA only after the Job 6 Review05 hard gate has passed and Olly authorises onboarding.
*⬜ Define ORCA asset-specific metrics before implementation.
*⬜ Do not inherit RAY fields blindly.


⬜ **20. Premium Data ROI Research**

*⬜ Identify precisely which important UNKNOWNs free data cannot solve.
*⬜ Test whether one month of paid data closes them.
*⬜ Decide whether subscription has measurable decision value.


⬜ **21. Conversational Evidence Layer — PARKED**


⬜ **22. Expert Framework Extraction — PARKED**

*⬜ Extract reusable decision frameworks from selected expert voices, not their asset calls.
*⬜ Capture useful analytical frameworks without importing opinions.
*⬜ No implementation until Olly explicitly activates it.


## V4 OPERATING PRINCIPLES

Evidence over opinion.
Observation before interpretation.
Framework before narrative.
UNKNOWN rather than invented certainty. Evidence-backed UNKNOWN is classified, not unclassified. Wallet 1 Aug start-line UNKNOWN is not acceptable: official start is 1 Aug 2026 00:00 UTC only, with no guessed zero or substitute date.
Transfers are not automatically sales.
CEX deposit is not automatically a sale.
Unlock is not automatically a dump.
Custody is not beneficial ownership.
Relative strength is evidence, not explanation.
Asset/project success does not automatically mean token-holder value capture.
Repetition is not independent corroboration.
No 0–100 magic scores.
No BUY / SELL / HOLD / WAIT as report stance/action output until separately designed and tested; hold-card OUT/SELL and WORRIED labels are exempt risk-control concepts.
Every PASS requires traceable evidence.
Missing evidence = FAIL / NOT REVIEWABLE.
The dashboard should reduce thinking time, not create more.
Capital preservation first.
