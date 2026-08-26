# V4 canonical metrics (Job 1)

GitHub-tracked architecture. Live numbers still live in `index-v4.html`.
This folder is inventory only. Job 2 collectors are not authorised.

| File | Role |
|---|---|
| `metric-schema.json` | JSON Schema for one canonical record |
| `metric-registry.json` | One record per `metric_id` |
| `ui-occurrences.json` | Every extracted UI candidate → metric or coverage state |
| `FIELDS.md` | Field meanings |
| `NAMING.md` | `metric_id` convention |
| `FRESHNESS.md` | FRESH / STALE / UNKNOWN / HISTORICAL |
| `JOB-V4-1-*.md` | Coverage, conflicts, unknowns, ownership |

Extractor, classifier, and tests: `tests/job1/`.
Families grow from the live page (`metric-families.json`). Completeness is atomic facts, not a small whitelist.

Evidence zips stay local under `reports-NOT-FOR-GH/` (never GitHub).

RAY and GRASS are dormant (`LEGACY_INACTIVE`). Not active V4 report assets.

