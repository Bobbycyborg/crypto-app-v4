# /report

Issue the next report and put it on the live page. Same layout as the one before. Change the report content only. Do not redesign. Do not edit collectors, renderer, integrity, or lib to force a pass.

The date is the day this command is run. It is often a Monday. It does not have to be.

## 1. Save the current report

Read `config/report.json`. If `live_number` is 06, the new one is 07. Same rule for any later number.

Copy `index-v4.html` to `baselines/report-06.html` (use the current number). Add that file to `FROZEN_REPORTS` in `renderer/frozen_reports.py` so it cannot be overwritten. It then sits with reports 01–05 in the week menu.

## 2. Point the config at the new report

In `config/report.json` only:

- `previous_report_number`, `previous_report_date`, `previous_report_label` become the report you just saved.
- `report_number` and `live_number` become the next number.
- `report_date` is today. `report_label` is today plus that number, same wording as the older labels.
- Add today to `weeks`. Leave the old weeks in the list.
- Do not change which coins are held, hidden, or dormant.

## 3. Pull today's numbers

Run the two tests:

```bash
python3 tests/job3/test_report_pipeline.py
python3 tests/job3/test_binding_contract.py
```

Then build from the page you just saved, not from the old hand file:

```bash
python3 make_report.py --base baselines/report-06.html --live --walk
```

Use the real saved filename. This writes `runtime-NOT-FOR-GH/candidate-NN.html` only.

## 4. Wallets

The walk is for coins in `siren_walk` only.

- Copy the last `state/siren-state.json` before the walk. Do not delete that copy.
- Add to the files already kept. Do not start a new store.
- Compare the last report with today. Do not read a wallet's full history. Do not record every transaction.
- Record only a big buy or a big sell since the last report. A send to a known exchange or market maker counts. Skip small moves.
- Do not add wallets. Do not invent tags.

## 5. Stance lines

Write a new stance for each coin that has one, using `config/stances.json`. Copy the shape of the old entries. Use the previous report as the tone. Do not copy its facts forward.

- `title`: short. Not a list of numbers.
- `summary`: this is the line under the title. Plain English. Few numbers.
- Popup (`why`, `supports`, `holds_back`, `stronger`, `weaker`): more detail is fine. Every number needs a short reason. Do not dump figures on their own.

## 6. Put it on the live page

Run the checker and the stale gate on that exact candidate. The previous page for the stale gate is the baseline you just saved.

If both pass, promote:

```bash
python3 make_report.py --promote
```

Then push `main` so Oliver can open it and comment. He is the reviewer. Do not treat a failed gate as a pass. If a gate fails, stop and show him the summary. Do not push a failed report.

Print `runtime-NOT-FOR-GH/run-summary.md`.

## Rules that win

These add to the steps above. Where they clash, follow this list.

- Build without `--walk` unless Oliver asks. Use the siren already baked.
- Draft the stances into `config/stances.json`. Do not promote until Oliver says the stances are OK.
- After promote, stop. Do not push. Show `runtime-NOT-FOR-GH/run-summary.md` and the live page for review.
