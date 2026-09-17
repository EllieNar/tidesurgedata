# ADR 0003: Maximum forecast lead time of a recipe

- **Status:** Proposed (sign-off at kickoff, BL-00)
- **Date:** 2026-09-17

## Context

A forecast frame can only contain driver values that are known at the issue time. A driver used
at lag `-12 h` whose data arrives one hour late can support forecasts at most 11 hours ahead,
unless forecasts of that driver are available. Users need to know this limit before they build
a model, and forecast frames must refuse horizons that would require unavailable data.

## Decision

For each driver **without** a forecast source:

```
lead_d = min(-lag for lag in lags_hours) - latency_d
```

where `latency_d` is the driver source's `latency`. Then

```
max_lead_time = min(lead_d)   over drivers without a forecast source
```

- `None` means unlimited: the recipe has no drivers, or every driver has a forecast source.
- A result `<= 0` is allowed and means the recipe is usable for training and hindcast analysis
  only.
- `Recipe.forecast_frame` raises `ValueError` for a horizon beyond `max_lead_time`.

Example: discharge at lags `(-24, -12)` with 1 h latency gives `12 h - 1 h = 11 h`; pressure at
lag `0` with a forecast source does not constrain the lead time.

## Consequences

- The limit is computed from the recipe alone, without fetching data.
- Latency values in adapters matter: they must reflect typical provider delay (documented per
  adapter, `TODO(BL-xx): confirm` where unknown).
- Drivers with forecast sources lift the limit, at the cost of forecast error in the features.
