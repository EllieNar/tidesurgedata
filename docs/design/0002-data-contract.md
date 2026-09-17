# ADR 0002: Data contract

- **Status:** Proposed (sign-off at kickoff, BL-00)
- **Date:** 2026-09-17

## Context

Every provider uses different time zones, units, datums, averaging conventions and missing-value
markers. Adapters written by different people will diverge unless there is one enforced contract.

## Decision

All series, forecasts and frames produced by the package obey these rules, enforced by
`tidesurgedata.contract` (`validate_series`, `validate_forecast`, `validate_frame`), which raise
`ContractError` naming the rule and the source.

| Rule | Requirement |
|---|---|
| Time | Timezone-aware **UTC** `DatetimeIndex`, strictly increasing, unique. Naive inputs to public functions are rejected with `ValueError`. Time ranges are half-open `[start, end)`. |
| Values | `float64`; missing values are `NaN`; no `inf`. |
| Units | SI canonical strings: `m`, `m s-1`, `m3 s-1`, `Pa`, `K`, `kg m-2 s-1`, `W m-2`, `1`. Vectors are stored as components (`u`, `v`), never speed and direction. |
| Series name | Equals `SeriesMeta.variable`. |
| Datum | Required in `SeriesMeta.datum` for water level and stage. |
| Lag sign | Hours; negative means the past. A lagged column at time `t` holds the driver value at `t + lag`. Column names come from `lag_column_name` (e.g. `discharge_lag-24h`). |
| Sampling | Each series declares `sampling` (`instantaneous` or `window_mean`); window means also declare `window` and `label` (`start`, `centre`, `end`). Alignment converts to a centred convention so no phase shift is introduced (a right-labelled hourly mean lags a tide by 30 minutes). |
| Frames | Regular UTC index; first column exactly the target column; then exactly the feature columns in order; `float64`; no `inf`; NaN allowed. |
| Provenance | Every fetch yields a `FetchRecord` (range, retrieval time, quality, counts, non-secret request parameters). Licence and exact attribution travel in `SeriesMeta`. |

Adapters implement only `metadata()` and the single-request hook `_fetch()`; `BaseSource`
performs chunking, concatenation, de-duplication (keeping the last), sorting, slicing, naming,
quality combination and validation identically for all providers.

## Consequences

- Downstream code (alignment, frames, export, models) can rely on the contract without
  provider-specific checks.
- Contract files (`meta.py`, `contract.py`, `sources/base.py`, `recipe.py`) change only via a
  pull request approved by a code owner.
- Adapters must convert units and time zones before returning data; mistakes fail loudly.
