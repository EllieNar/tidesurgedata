# Backlog

One entry per item. Workstream labels: `ws:platform` (Fellow 1), `ws:us-met` (Fellow 2),
`ws:uk-global` (Fellow 3), `ws:frames` (Fellow 4), `ws:lead` (Thomas).

Each stub's docstring is its specification; acceptance criteria reference the spec tests that
must pass with their `xfail` markers removed. `scripts/create_issues.sh` creates one GitHub issue
per entry.

| ID | Title | Workstream | Depends on |
|---|---|---|---|
| BL-00 | Contract sign-off at kickoff (Section 4, ADRs 0001–0006) | `ws:lead` | — |
| BL-01 | CI hardening; verify branch protection and required checks | `ws:platform` | — |
| BL-02 | Cassette recording harness and first example cassette | `ws:platform` | BL-05 or BL-07 |
| BL-03 | Nightly live job with failure notification | `ws:platform` | BL-02 |
| BL-04 | Local parquet cache and `cache=` option on `fetch` | `ws:platform` | BL-00 |
| BL-05 | NOAA CO-OPS adapter (water level, wind, pressure) + `find_stations` | `ws:us-met` | BL-00 |
| BL-06 | USGS adapter (`waterdata`) + `find_stations` | `ws:us-met` | BL-00 |
| BL-07 | EA tide gauge adapter + `find_stations` | `ws:uk-global` | BL-00 |
| BL-08 | EA rivers adapter (flood-monitoring + Hydrology API) + `find_stations` | `ws:uk-global` | BL-00 |
| BL-09 | GESLA adapter (blocked on 4.1 API specification) | `ws:uk-global` | BL-00 |
| BL-10 | `align.to_grid`: resampling and gap policy | `ws:frames` | BL-00 |
| BL-11 | `align.materialise_lags` | `ws:frames` | BL-00 |
| BL-12 | `Recipe.training_frame` and `provenance` | `ws:frames` | BL-10, BL-11 |
| BL-13 | `Recipe.forecast_frame` and lead-time enforcement | `ws:frames` | BL-10, BL-11 |
| BL-14 | `hindcast_frames` (as-of, no leakage) | `ws:frames` | BL-13 |
| BL-15 | dynamical.org analysis retrieval at a point | `ws:us-met` | BL-00 |
| BL-16 | dynamical.org forecasts and ensemble members (stretch) | `ws:us-met` | BL-15 |
| BL-17 | Cross-provider `find_stations` | `ws:platform` | at least two adapters |
| BL-18 | `to_xarray` / `to_netcdf` / `to_csv` with CF attributes and provenance | `ws:platform` | BL-00 |
| BL-19 | US demo script: CO-OPS + USGS (+ dynamical.org) training and forecast frames | `ws:us-met` | BL-05, BL-06, BL-12, BL-13 |
| BL-20 | UK demo script: EA tide gauge + EA rivers (+ dynamical.org) training and forecast frames | `ws:uk-global` | BL-07, BL-08, BL-12, BL-13 |
| BL-21 | RTide compatibility walking skeleton green (optional job) | `ws:platform` | BL-12, BL-13 |
| BL-22 | `Recipe.forecast_frames` for ensembles (stretch) | `ws:frames` | BL-13, BL-16 |

## BL-00: Contract sign-off at kickoff (Section 4, ADRs 0001–0006)

- **Workstream:** `ws:lead` (Thomas)
- **Depends on:** —

Walk through the data contract (`meta.py`, `contract.py`, `sources/base.py`, `recipe.py`), the fake sources and ADRs 0001–0006 with all fellows. Record agreed changes as PRs before implementation work depends on them.

**Acceptance criteria**

- [ ] ADRs 0001–0006 marked Accepted (or amended by PR)
- [ ] Any contract changes merged with code-owner approval
- [ ] Every fellow has a working dev environment and has run the unit tests

## BL-01: CI hardening; verify branch protection and required checks

- **Workstream:** `ws:platform` (Fellow 1)
- **Depends on:** —

Confirm `ci.yml` runs on PRs and `main`; verify branch protection (required checks `lint`, `unit`, `extras`; code-owner review; no force pushes; `rtide-compat` not required); add pip caching and job timeouts; consider a coverage report.

**Acceptance criteria**

- [ ] A test PR demonstrates required checks block merging when failing
- [ ] `rtide-compat` failure does not block merging
- [ ] Workflows pass `actionlint`

## BL-02: Cassette recording harness and first example cassette

- **Workstream:** `ws:platform` (Fellow 1)
- **Depends on:** BL-05 or BL-07

Make recording cassettes routine: confirm `vcr_config` filtering in `tests/conftest.py`, add a helper/check that scans cassettes for secrets and size, and record the first cassette for NOAA CO-OPS or EA tide so its `Test…Contract` class runs unskipped.

**Acceptance criteria**

- [ ] One adapter's contract suite runs from a cassette with sockets disabled
- [ ] Cassette secret/size check runs in CI
- [ ] `docs/dev/recording-cassettes.md` updated with anything learned

## BL-03: Nightly live job with failure notification

- **Workstream:** `ws:platform` (Fellow 1)
- **Depends on:** BL-02

Harden `nightly-live.yml`: notification on failure (e.g. an issue opened or updated automatically), retries for transient errors, and a summary of which providers failed.

**Acceptance criteria**

- [ ] A deliberately failing live test produces a notification
- [ ] Secrets are never echoed in logs

## BL-04: Local parquet cache and `cache=` option on `fetch`

- **Workstream:** `ws:platform` (Fellow 1)
- **Depends on:** BL-00

Implement `tidesurgedata.cache.Cache` and `default_cache_root` as specified in their docstrings; add `cache: Cache | None = None` to `BaseSource.fetch` and `fetch_with_record` (contract change: code-owner review).

**Acceptance criteria**

- [ ] `tests/spec/test_cache.py` passes with `xfail` markers removed (hit/miss, partial overlap, key includes params and adapter_version, preliminary expiry, atomic write, env var root)

## BL-05: NOAA CO-OPS adapter (water level, wind, pressure) + `find_stations`

- **Workstream:** `ws:us-met` (Fellow 2)
- **Depends on:** BL-00

Implement `sources/noaa_coops.py` following its module docstring (provider facts and checklist): interval-dependent chunking, mandatory datum, verified/preliminary quality, wind as u/v components, pressure in Pa.

**Acceptance criteria**

- [ ] `tests/sources/test_noaa_coops.py` passes with markers removed
- [ ] Contract suite runs from a recorded cassette
- [ ] Live smoke test passes nightly

## BL-06: USGS adapter (`waterdata`) + `find_stations`

- **Workstream:** `ws:us-met` (Fellow 2)
- **Depends on:** BL-00

Implement `sources/usgs.py` using `dataretrieval.waterdata` (extra `usgs`, `dataretrieval>=1.1.0`), never the legacy `nwis` module. API key from `API_USGS_PAT` only. Convert ft³/s and ft to SI.

**Acceptance criteria**

- [ ] `tests/sources/test_usgs.py` passes with markers removed
- [ ] Cassette contains no API key
- [ ] Import isolation test still passes

## BL-07: EA tide gauge adapter + `find_stations`

- **Workstream:** `ws:uk-global` (Fellow 3)
- **Depends on:** BL-00

Implement `sources/ea_tide.py` against the flood-monitoring Tide Gauge API: 15-minute window means, local datum or ODN, OGL licence with exact attribution. Confirm and document the window label convention.

**Acceptance criteria**

- [ ] `tests/sources/test_ea_tide.py` passes with markers removed
- [ ] Label convention evidence recorded in the PR
- [ ] Contract suite runs from a cassette

## BL-08: EA rivers adapter (flood-monitoring + Hydrology API) + `find_stations`

- **Workstream:** `ws:uk-global` (Fellow 3)
- **Depends on:** BL-00

Implement `sources/ea_rivers.py`: map flood-monitoring references to Hydrology API GUIDs; archive data as verified, real-time as preliminary, both as mixed; exact attribution.

**Acceptance criteria**

- [ ] `tests/sources/test_ea_rivers.py` passes with markers removed
- [ ] Cassettes for both APIs
- [ ] Quality marking tested

## BL-09: GESLA adapter (blocked on 4.1 API specification)

- **Workstream:** `ws:uk-global` (Fellow 3)
- **Depends on:** BL-00

Implement `sources/gesla.py` once Thomas provides the GESLA 4.1 API specification; per-station licence and attribution; local-file fallback.

**Acceptance criteria**

- [ ] `tests/sources/test_gesla.py` passes with markers removed
- [ ] Per-station licences carried into `SeriesMeta`

## BL-10: `align.to_grid`: resampling and gap policy

- **Workstream:** `ws:frames` (Fellow 4)
- **Depends on:** BL-00

Implement `align.to_grid` per its docstring and ADR 0004: window-mean relabelling, instant nearest within freq/10, centred means with the 50 % rule, `max_gap` interpolation without extrapolation.

**Acceptance criteria**

- [ ] `tests/spec/test_align.py` BL-10 tests pass with markers removed

## BL-11: `align.materialise_lags`

- **Workstream:** `ws:frames` (Fellow 4)
- **Depends on:** BL-00

Implement `align.materialise_lags` per its docstring: one column per lag named by `lag_column_name`, value at t = series(t + lag), non-multiple lags raise.

**Acceptance criteria**

- [ ] `tests/spec/test_align.py` BL-11 tests pass with markers removed

## BL-12: `Recipe.training_frame` and `provenance`

- **Workstream:** `ws:frames` (Fellow 4)
- **Depends on:** BL-10, BL-11

Implement `Recipe.training_frame` and `Recipe.provenance` per their docstrings: regular grid over [start, end), target never interpolated, drivers fetched over lag-widened windows, NaN rows kept, records of the last build.

**Acceptance criteria**

- [ ] `tests/spec/test_recipe_frames.py` BL-12 tests pass with markers removed

## BL-13: `Recipe.forecast_frame` and lead-time enforcement

- **Workstream:** `ws:frames` (Fellow 4)
- **Depends on:** BL-10, BL-11

Implement `Recipe.forecast_frame` per its docstring and ADRs 0003/0006: grid over (issued, issued + horizon], NaN target, data only if available by issued − latency, forecast sources after issued, horizon beyond `max_lead_time` raises.

**Acceptance criteria**

- [ ] `tests/spec/test_recipe_frames.py` BL-13 tests pass with markers removed
- [ ] Leakage test passes

## BL-14: `hindcast_frames` (as-of, no leakage)

- **Workstream:** `ws:frames` (Fellow 4)
- **Depends on:** BL-13

Implement `hindcast.hindcast_frames` per its docstring and ADR 0006.

**Acceptance criteria**

- [ ] `tests/spec/test_hindcast.py` passes with markers removed

## BL-15: dynamical.org analysis retrieval at a point

- **Workstream:** `ws:us-met` (Fellow 2)
- **Depends on:** BL-00

Implement `Dynamical.metadata`, `_fetch` and `find_stations` (analysis datasets) via the STAC catalog and Icechunk Zarr with xarray (extra `met`), lazy imports, CC BY 4.0 (+ ECMWF terms) licences.

**Acceptance criteria**

- [ ] `tests/sources/test_dynamical.py` BL-15 tests pass with markers removed
- [ ] Contract suite runs from a small recorded fixture
- [ ] Import isolation test still passes

## BL-16: dynamical.org forecasts and ensemble members (stretch)

- **Workstream:** `ws:us-met` (Fellow 2)
- **Depends on:** BL-15

Implement `Dynamical.init_times` and `fetch_forecast`: latest init_time available by issued − latency, valid_time = init_time + lead_time, members as strings.

**Acceptance criteria**

- [ ] `tests/sources/test_dynamical.py` BL-16 tests pass with markers removed
- [ ] `ForecastSourceContractTests` pass for a forecast dataset

## BL-17: Cross-provider `find_stations`

- **Workstream:** `ws:platform` (Fellow 1)
- **Depends on:** at least two adapters

Implement `discovery.find_stations` per its docstring: query registered adapters, skip NotImplementedError with a warning, merge and sort by distance.

**Acceptance criteria**

- [ ] `tests/spec/test_discovery.py` passes with markers removed
- [ ] Demonstrated with two real adapters (cassettes)

## BL-18: `to_xarray` / `to_netcdf` / `to_csv` with CF attributes and provenance

- **Workstream:** `ws:platform` (Fellow 1)
- **Depends on:** BL-00

Implement `io.to_xarray`, `io.to_netcdf` and `io.to_csv` per their docstrings: CF attributes, provenance, licence and attribution; lazy xarray import.

**Acceptance criteria**

- [ ] `tests/spec/test_io.py` passes with markers removed (xarray tests run in the `extras` job)

## BL-19: US demo script: CO-OPS + USGS (+ dynamical.org) training and forecast frames

- **Workstream:** `ws:us-met` (Fellow 2)
- **Depends on:** BL-05, BL-06, BL-12, BL-13

Add `examples/us_demo.py` building a recipe for a US tide gauge with USGS discharge (and dynamical.org pressure if ready), producing a training frame and a forecast frame, printing provenance and attribution.

**Acceptance criteria**

- [ ] Script runs end to end against live APIs
- [ ] Frames pass `validate_frame`
- [ ] Attribution printed

## BL-20: UK demo script: EA tide gauge + EA rivers (+ dynamical.org) training and forecast frames

- **Workstream:** `ws:uk-global` (Fellow 3)
- **Depends on:** BL-07, BL-08, BL-12, BL-13

Add `examples/uk_demo.py` building a recipe for an EA tide gauge with EA river flow (and dynamical.org pressure if ready), producing a training frame and a forecast frame, printing provenance and attribution.

**Acceptance criteria**

- [ ] Script runs end to end against live APIs
- [ ] Frames pass `validate_frame`
- [ ] Attribution printed

## BL-21: RTide compatibility walking skeleton green (optional job)

- **Workstream:** `ws:platform` (Fellow 1)
- **Depends on:** BL-12, BL-13

Make `tests/compat_rtide/test_walking_skeleton.py` pass in the `rtide-compat` job (requires rtide ≥ 1.0.1 on PyPI).

**Acceptance criteria**

- [ ] Walking skeleton passes with its `xfail` marker removed
- [ ] No RTide code or dependency added to the package

## BL-22: `Recipe.forecast_frames` for ensembles (stretch)

- **Workstream:** `ws:frames` (Fellow 4)
- **Depends on:** BL-13, BL-16

Implement `Recipe.forecast_frames` per its docstring: one forecast frame per member common to all forecast sources.

**Acceptance criteria**

- [ ] `tests/spec/test_recipe_frames.py` BL-22 test passes with marker removed
