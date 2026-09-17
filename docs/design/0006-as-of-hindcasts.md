# ADR 0006: As-of hindcasts without leakage

- **Status:** Proposed (sign-off at kickoff, BL-00)
- **Date:** 2026-09-17

## Context

Forecast skill must be evaluated on hindcasts that reproduce what a model would have seen at each
issue time. Using data that arrived later (observations beyond the latency, or forecasts
initialised after the issue time) inflates skill and misleads users.

## Decision

- `hindcast_frames(recipe, issue_times, horizon_hours)` yields, for each issue time,
  `(issue_time, forecast_frame, observed_target)` and is model-agnostic.
- Forecast frames use observed or analysis data **only if available by `issued - latency`** of
  that source, and forecasts only from the latest initialisation available by
  `issued - latency` of the forecast source (`ForecastSource.fetch_forecast`). Nothing initialised
  after that is used.
- Horizons beyond `Recipe.max_lead_time` raise (ADR 0003).
- Provider data revisions are acknowledged: adapters return today's version of historical data.
  `FetchRecord.quality` (`verified`, `preliminary`, `mixed`, `unknown`) records what was used,
  and hindcast results should be interpreted accordingly. Preliminary cache chunks expire.
- Leakage is tested by comparing frames built from full sources with frames built from sources
  truncated at `issued - latency`; they must be identical.

## Consequences

- Hindcast skill estimates are honest with respect to data latency and forecast availability.
- Hindcasts cannot reproduce preliminary values that were later revised; this limitation is
  documented and visible in provenance.
- Latency values in adapters directly affect results and must be justified in adapter PRs.
