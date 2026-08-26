# JOB-V4-1-SEMANTIC-QA (explicit-manifest rebuild)

Architecture: HTML → candidate inventory → `metrics/ui-mapping-manifest.json` → declared extractors → registry.

Meaning is not inferred at runtime. The builder applies the committed manifest only.

See `JOB-V4-1-CONFLICT-AUDIT.md` for the old-30 dispositions.

Independent checker: `tests/job1/test_job1_independent.py` (does not import `job1_classify` / `parse_raw` / production rounding).

Golden: `tests/job1/golden-semantics.json`.
