# Weekly report

Read this before touching the page. The live file stays `index-v4.html`.

## Before you start

1. Edit `config/report.json` only: report number, report date, previous report date, held coins, hidden coins, dormant coins, siren-walk coins.
2. The pipeline files must be committed. `python3 make_report.py` stops if they are still edited.
3. Do not edit `renderer/`, `integrity/`, `collectors/`, or `lib/` to force a report through. A failed check is a stop.

## Run

```bash
python3 make_report.py
```

That checks the tree. It does not change the live page.

When the tree is clean and you want the next report, the same command's `--run` is not switched on yet. Do not type numbers in. Do not open a browser to fetch them. A candidate file, if rendered, goes to `runtime-NOT-FOR-GH/candidate-NN.html`.

## After the candidate exists

1. Fill only the lines marked `MANUAL:zone` for this report number. Do not invent the others.
2. Run the checker and `integrity/stale_gate.py`. Both must pass.
3. A stale date, a repeated "7d 7d", a raw long decimal, or a changed dormant coin fails the build.
4. Promote the candidate onto `index-v4.html` only after that. Then review. Push is separate and manual.

## Wallet

Held coins only, from `config/report.json`. Proved 1 Aug starts live in `state/siren-state.json`. The page is a copy of that file. Do not walk sold coins. Plain Solana reads only. Public RPC first. No expensive Helius history.
