# Job 3 UI binding renderer

Static shadow renderer. **No network.** Does not modify `index-v4.html`.

## Inputs
- `index-v4.html` (read-only template)
- `renderer/binding-manifest.json`
- `renderer/writer-quarantine.json`
- render snapshot JSON from `build_snapshot.py`

## Commands
```bash
python renderer/build_binding_manifest.py --check
python renderer/build_snapshot.py --collector-run <collector-run.json> --out runtime-NOT-FOR-GH/job3/render-snapshot.json
python renderer/render_report.py --snapshot <snapshot.json> --source index-v4.html --out runtime-NOT-FOR-GH/job3/shadow-render.html
```

## Behaviour
- One canonical metric → many UI bindings; exact anchor replacement only.
- Non-OK collector status → visible `UNKNOWN` (fail-closed).
- GROK wallet / dormant RAY·GRASS·DRIFT excluded from binding.
- Shadow output quarantines `CGPT_BOUND_WRITER` live price fetches.
- Synthetic test fixtures are labelled `SYNTHETIC_TEST_ONLY` — not publishable.

Job 5 will consume this renderer for Review04 shadow rebuild.
