# ADR 0004: Resampling convention

- **Status:** Proposed (sign-off at kickoff, BL-00)
- **Date:** 2026-09-17

## Context

Providers report instantaneous samples (tide gauges), window means labelled at the start, centre
or end of the window (EA 15-minute readings, model analyses), at many different spacings.
Naively resampling introduces phase shifts: a right-labelled hourly mean lags a semidiurnal tide
by 30 minutes, which is a large error for tidal models.

## Decision

`align.to_grid(series, meta, freq, how, max_gap)` puts series on a regular UTC grid whose points
are multiples of `freq` since the epoch, with **centred** semantics:

- **Relabelling first:** window-mean inputs are shifted to centre labels using `meta.window` and
  `meta.label` (`start`: `+window/2`; `end`: `-window/2`; `centre`: unchanged).
- **`how="instant"`:** the value at the grid time if present, else the nearest sample within
  `freq / 10`, else NaN.
- **`how="mean"`:** the mean of samples in the centred window `[t - freq/2, t + freq/2)`; NaN
  unless at least 50 % of the expected samples (window length / native spacing) are valid.
- **Gaps:** with `max_gap`, NaN runs are filled by linear interpolation in time only when the
  bounding valid values are at most `max_gap` apart. Never extrapolate.
- **Targets are never interpolated** in training frames (`max_gap=None`); drivers default to
  `how="mean"`, `max_gap="2h"`.
- `align.materialise_lags` then builds lagged columns on the grid (value at `t` is
  `series(t + lag)`); lags must be multiples of the grid step.

## Consequences

- No phase shift between drivers and targets regardless of provider conventions, provided
  adapters declare `sampling`, `window` and `label` correctly (EA label convention to be
  confirmed in BL-07).
- The 50 % rule and `max_gap` make missing-data handling explicit and reproducible.
- Grids from different windows line up, so frames can be concatenated and cached consistently.
