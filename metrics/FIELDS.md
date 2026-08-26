# V4 Job 1 — field definitions

HTML is display truth. Do not infer missing sources. Do not pick a conflict winner.

## metric_id
Permanent unique machine id: `{asset}.{family}.{measure}[.{window}]`.
Not bound to a UI slot. Same fact → one id. Different fact → different id.
Banned leftover families: `captured`, `usd_figure`, `pct_figure`, `pp_figure`.

## asset
Ticker from the component: article `data-asset`, hold `.hold-ticker`, desk `data-asset-slug`, ETF `etf-tip-asset`.
Hold-card-only names (ORCA, BONK, …) keep their ticker. Not MARKET.
Market-level: MARKET, PORTFOLIO, GLOBAL.

## value
Agreed current display literal when all occurrences of the same fact agree (format variants listed, not winners).
If status is CONFLICT: `UNKNOWN`. Never first-seen.

## raw_value
Parsed unformatted number from the agreed literal, or UNKNOWN/null.
If CONFLICT: UNKNOWN/null.

## evidence_variants
Every occurrence (and format-variant) of this metric: occurrence_id, literal, raw_value, source, source_url, as_of, freshness.

## unit / scope / definition
Exact measured quantity in plain English. Not “Canonical record for {id}…”.

## source / source_url_or_reference
Taken only from the **same component** (tooltip foot, card link, dial `metric-tip-source`).
No ambient article-wide substring matching.

## as_of
The fact’s date from that same component. Not fetch time.

## fetched_at
UNKNOWN unless the HTML states a retrieval time. Never inferred from Report 04.

## freshness
FRESH | STALE | UNKNOWN | HISTORICAL

## calculation_version
`direct` for observed values.
Derived metrics use a real version (`drawdown_v1`, …), never `direct`.

## owner
Exactly one: CGPT_CURSOR or GROK.

## metric_type / status / historical_or_current / wallet_or_non_wallet
As enums in the schema.

## value_kind / allowed_unit / allowed_literal_shape
Declared on every canonical metric. The builder refuses to map a literal that fails the metric's type.
USD metrics cannot absorb percents. Ratio metrics cannot absorb notionals. Index cannot absorb dates.
Time basis is part of the id (`usd.30d` is not `usd.7d`; `usd_per_day.mean_30d` is not a 7d total).

## update_mode
LIVE (hold/desk ticker), REPORT_SNAPSHOT (frozen report figure), HISTORICAL, STATIC_THRESHOLD, WALLET_SNAPSHOT.
A live ticker and a report hero price are different records. Conflict only if asset + definition + window + update_mode match and values disagree.

## scope_key
Measure subtype. Spot volume is not perp volume. Platform OI is not token OI. Price return is not OI change. Fees are not revenue or buybacks. Same unit + same window is not enough to share a metric.
