# ADR 0001: Standalone, model-agnostic package

- **Status:** Proposed (sign-off at kickoff, BL-00)
- **Date:** 2026-09-17

## Context

Coastal and hydrological forecasting work repeatedly re-implements the same plumbing: calling
provider APIs with different limits, units, datums and time conventions, then assembling
lagged training and forecast datasets. RTide is one important consumer of such data, but the
same data is useful for many other models and analyses.

## Decision

- `tidesurgedata` is an open, model-agnostic community package. Its outputs are plain `pandas`
  objects plus JSON-serialisable metadata, usable with any model.
- It is **independent of RTide**: RTide is not a dependency (required or optional), is never
  imported by package code, and no RTide source code is copied, vendored, paraphrased or ported.
- No RTide-specific features (model saving, bundles, RTide documentation) live in this repository.
- Compatibility with RTide is checked **only** by an optional, non-required CI job
  (`rtide-compat`) that installs a published RTide release and uses its public API
  (`RTide(df, lat, lon)`, `Prepare_Inputs`, `Train`, `Predict`).
- Model-specific conventions are expressed through generic options (e.g.
  `Recipe.target_column="observations"`), not special cases.

## Consequences

- The package can be adopted by users of any model, and RTide releases can never block it.
- `import tidesurgedata` stays lightweight and never imports TensorFlow or RTide (enforced by
  `tests/test_import_isolation.py`).
- Changes in RTide that break compatibility surface as a failing optional job, to be resolved on
  either side without coupling release cycles.
