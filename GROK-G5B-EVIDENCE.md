# G5B EVIDENCE PACK

**Job:** G5B. 2Z / Drift (Velocity) / Orca as in-app pages on the main V4 dashboard  
**Date:** 26 Aug 2026  
**Owner:** Grok  
**Status:** NOT DONE. Grok has not marked this complete. CGPT reviews this pack + the diff.

## Dummy
The standalone skinny look is retired as the review surface. 2Z, Drift/Velocity, and Orca are now reduced pages inside `index-v4.html`. Same header, same hold grid, same cream/ink/Jost/DM Sans chrome as the rest of the app. Click the hold card. Or open the hash URL.

## Why this job existed
Oliver rejected `skinny/2z.html`, `skinny/drift.html`, `skinny/orca.html` + `skinny.css` on 26 Aug 2026. He said they must be pages on the main thing, use the design rules of the whole page, may be heavily reduced, and have to be part of the app.

## Before
- G5 shipped three standalone HTML pages under `skinny/` with their own `skinny.css`.
- 2Z / DRIFT / ORCA hold cards were `hold-no-article` (no `data-asset-slug`). Click did nothing.
- ORCA desk row was `no-article`.
- Live review URL was the skinny mini-site.

## After
- Three reduced `article.report.asset-v3-report.g5-page` views in `index-v4.html` (`data-asset="2z"|"drift"|"orca"`).
- Same existing report chrome: `alt-hero`, `alt-eyebrow`, `alt-ticker`, `alt-stance-headline`, `alt-summary`, `alt-group`.
- Hold cards for 2Z / DRIFT / ORCA now have slugs and open those views. Grid not redesigned.
- Hash routes: `#2z` `#drift` `#orca` (`#velocity` aliases Drift). Other cards still default to BTC on a bare load.
- `skinny/*.html` redirect into those hashes. `skinny.css` removed so it is not the review surface.

## Live URLs Oliver should open
- Main app: https://bobby.olivergoodrum.com/index-v4.html
- 2Z: https://bobby.olivergoodrum.com/index-v4.html#2z
- Drift / Velocity: https://bobby.olivergoodrum.com/index-v4.html#drift
- Orca: https://bobby.olivergoodrum.com/index-v4.html#orca

Entry from the dashboard: click the **2Z**, **DRIFT**, or **ORCA** hold card. ORCA also opens from its desk row if that list is shown.

Old skinny URLs (`/skinny/2z.html` etc.) redirect to the hashes above.

## Official source (G5 facts, unchanged)
No new research this job.

**2Z.** Official next unlock DATE / SIZE / WHO = UNKNOWN. PDF as-of 26 Sep 2025: Standard Lockup over 4 years from expected 2 Oct 2025. Unofficial 2 Oct calendars not used as the number. Q2 18 Aug 2026 ~$330,000 USDC / ~4.35M 2Z / 39 epochs; ~1.8M 2Z burned. DefiLlama fees 24h $142 / 7d $67,199 (26 Aug 2026). Dest-watch tags: TwoZ1–TwoZ20 + Wintermute.

Sources: https://doublezero.xyz/2z-tokenomics-disclosure.pdf ; https://doublezero.xyz/journal/doublezero-q2-2026-token-holder-update ; https://defillama.com/protocol/doublezero

**Drift / Velocity.** Rebrand 1 Jul 2026. Old program paused. Private beta press 25 Aug 2026. Live perps: 4. 24h volume unlisted. Do not say users came back. Dest-watch tags: Foundation, Team, Team.

Sources: https://docs.velocity.exchange/developers/migrate-from-drift ; https://coinfomania.com/velocitydex-goes-live-with-private-beta-offering-0-02-fees/ ; https://data.velocity.exchange/stats/markets ; https://defillama.com/protocol/drift-trade

**Orca.** DefiLlama 26 Aug 2026: 24h volume $459,547,210 / 7d $2,838,298,665. Fees 24h $288,490 / 7d $1,888,997. Official 87/12/1. Two official 12% splits kept separate. Dest-watch tags: Community treasury, Fee treasury, xORCA vault.

Sources: https://defillama.com/protocol/orca ; https://docs.orca.so/liquidity/concepts/trading-fees ; https://docs.orca.so/governance/tokenomics

## Files touched
- `index-v4.html`
- `skinny/2z.html` `skinny/drift.html` `skinny/orca.html` (now redirects)
- `skinny/skinny.css` (removed)
- `GROK-G5B-BRIEF.md`
- `GROK-G5B-EVIDENCE.md`
- `GROK-JOBS.md` (G5B line)

## Files left alone
`metrics/`, `tests/job1/`, Job 1 WIP, `config/wallet.json`, `config/capital.json`, dest-watch JSON, siren start-line, V3, HOM, reports dumps, other hold cards, header, grid layout.

## What this job did not do
- Invent 2Z unlock size
- Invent Velocity 24h volume
- Say users came back
- Merge the two official Orca 12% splits
- Job 19 ORCA onboard
- Restyle dashboard / header / other cards
- New wallets
- Mark PASS

## CGPT questions
1. Invented official 2Z unlock size? FAIL if yes
2. Invented Velocity volume? FAIL if yes
3. Drift page says users came back without volume prove? FAIL if yes
4. `metrics/` / `tests/job1/` in the commit? FAIL if yes
5. Wallets added/renamed? FAIL if yes
6. Fat weekly reports? FAIL if yes
7. Still a separate skinny look as the review surface? FAIL if yes
8. Dashboard / other cards restyled? FAIL if yes
9. Grok marked done? FAIL if yes

Grok has not marked this done.
