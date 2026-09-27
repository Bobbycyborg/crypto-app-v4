# Weekly report

The live file stays `index-v4.html`. Do not push from this command.

## Before you start

Edit `config/report.json` only: report number, date, previous date, held coins, hidden coins, dormant coins, siren-walk coins.

`python3 make_report.py` stops if the pipeline files are still edited. Do not edit `renderer/`, `integrity/`, `collectors/`, or `lib/` to force a pass.

## Run

Offline, from a saved pull:

```bash
python3 make_report.py --base reports-NOT-FOR-GH/HAND-report-06-before-coded-render.html --replay runtime-NOT-FOR-GH/job2/20260926T103538Z_3e1c5167
```

A new pull (this uses the network) and a wallet walk onto the candidate only:

```bash
python3 make_report.py --base reports-NOT-FOR-GH/HAND-report-06-before-coded-render.html --live --walk
```

Both write `runtime-NOT-FOR-GH/candidate-NN.html` and `runtime-NOT-FOR-GH/run-summary.md`. They do not replace the live page.

`/report` runs the tests, then the live command above, then prints the summary. Promote and freeze stay off until the checker and the stale gate both pass.

Check the page:

```bash
python3 integrity/stale_gate.py --html runtime-NOT-FOR-GH/candidate-NN.html --snapshot runtime-NOT-FOR-GH/job3/render-snapshot.json --bindings runtime-NOT-FOR-GH/job3/binding-manifest.json --previous-html baselines/report-05.html
```

A stale line fails that check. Fill only the lines marked `MANUAL:zone`. Do not invent the others.

## Wallet

Held coins only, from `config/report.json`. Proved 1 Aug starts live in `state/siren-state.json`. A walk merges into that file. It does not replace it. Plain Solana reads only. Public RPC first. No expensive Helius history.
