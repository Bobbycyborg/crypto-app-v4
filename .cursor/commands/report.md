# /report

Run the weekly crypto report. Do not promote. Do not push.

1. Run `python3 tests/job3/test_report_pipeline.py` and `python3 tests/job3/test_binding_contract.py`.
2. Run:

```bash
python3 make_report.py --base reports-NOT-FOR-GH/HAND-report-06-before-coded-render.html --live --walk
```

3. Print `runtime-NOT-FOR-GH/run-summary.md`.

The live page stays `index-v4.html`. Wallet lines go on the candidate only.
