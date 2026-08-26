# V4 freshness model (Job 1)

States: FRESH | STALE | UNKNOWN | HISTORICAL

Job 1 does not invent TTL thresholds.

- If HTML already says STALE and a date (RENDER forensics, SPX top-20): freshness=STALE, as_of=that date.
- ATH / past events: HISTORICAL.
- Fixed OUT / SELL / this-move levels: not freshness-managed; metric_type=STATIC_DECISION_THRESHOLD, freshness=UNKNOWN, freshness_rule=not_applicable.
- All other current figures: freshness=UNKNOWN, freshness_rule=TBD until Job 2 collectors exist.
- fetched_at is not inferred from “August 25th, 2026 - Report 04”.
