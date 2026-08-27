# Job 4 — Production Fail-Closed Integrity Checker

Read-only, stdlib-only checker that validates shadow-rendered reports against canonical snapshots.

## CLI

```bash
python integrity/check_report.py \
  --snapshot <snapshot.json> \
  --rendered-html <rendered.html> \
  --source-html index-v4.html \
  --bindings renderer/binding-manifest.json \
  --registry metrics/metric-registry.json \
  --collector-plan collectors/collector-plan.json \
  --contract integrity/report-contract.json \
  --out integrity-report.json \
  --run-id <explicit-run-id>
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | PASS |
| 2 | FAIL |
| 3 | COVERAGE_GAP |
| 4 | INPUT_LINEAGE_FAILURE |
| 5 | Internal error |

## Contract

`integrity/build_report_contract.py --check` must reproduce `report-contract.json`.

## Scope

Active report assets: btc, sol, render, pump, io, nos, fartcoin, spx6900, zec, hype.

Excluded: ray, grass, drift. GROK wallet metrics excluded from non-wallet semantic checks.
