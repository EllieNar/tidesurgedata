#!/usr/bin/env bash
# Create workstream labels and one GitHub issue per backlog entry (docs/dev/backlog.md).
# Generated from the backlog; review before running. Requires an authenticated `gh` CLI.
# Usage: scripts/create_issues.sh [owner/repo]   (default: thomasmonahan/tidesurgedata)
set -euo pipefail

REPO="${1:-thomasmonahan/tidesurgedata}"

label() { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force; }

label "ws:platform" "1d76db" 'Fellow 1'
label "ws:us-met" "0e8a16" 'Fellow 2'
label "ws:uk-global" "5319e7" 'Fellow 3'
label "ws:frames" "fbca04" 'Fellow 4'
label "ws:lead" "b60205" Thomas
label "adapter" "c5def5" "Provider data adapter"

gh issue create --repo "$REPO" --title 'BL-00: Contract sign-off at kickoff (Section 4, ADRs 0001–0006)' --label ws:lead --body 'Walk through the data contract (`meta.py`, `contract.py`, `sources/base.py`, `recipe.py`), the fake sources and ADRs 0001–0006 with all fellows. Record agreed changes as PRs before implementation work depends on them.

**Depends on:** —

**Acceptance criteria**

- [ ] ADRs 0001–0006 marked Accepted (or amended by PR)
- [ ] Any contract changes merged with code-owner approval
- [ ] Every fellow has a working dev environment and has run the unit tests

See `docs/dev/backlog.md` (BL-00).'
gh issue create --repo "$REPO" --title 'BL-01: CI hardening; verify branch protection and required checks' --label ws:platform --body 'Confirm `ci.yml` runs on PRs and `main`; verify branch protection (required checks `lint`, `unit`, `extras`; code-owner review; no force pushes; `rtide-compat` not required); add pip caching and job timeouts; consider a coverage report.

**Depends on:** —

**Acceptance criteria**

- [ ] A test PR demonstrates required checks block merging when failing
- [ ] `rtide-compat` failure does not block merging
- [ ] Workflows pass `actionlint`

See `docs/dev/backlog.md` (BL-01).'
gh issue create --repo "$REPO" --title 'BL-02: Cassette recording harness and first example cassette' --label ws:platform --body 'Make recording cassettes routine: confirm `vcr_config` filtering in `tests/conftest.py`, add a helper/check that scans cassettes for secrets and size, and record the first cassette for NOAA CO-OPS or EA tide so its `Test…Contract` class runs unskipped.

**Depends on:** BL-05 or BL-07

**Acceptance criteria**

- [ ] One adapter'"'"'s contract suite runs from a cassette with sockets disabled
- [ ] Cassette secret/size check runs in CI
- [ ] `docs/dev/recording-cassettes.md` updated with anything learned

See `docs/dev/backlog.md` (BL-02).'
gh issue create --repo "$REPO" --title 'BL-03: Nightly live job with failure notification' --label ws:platform --body 'Harden `nightly-live.yml`: notification on failure (e.g. an issue opened or updated automatically), retries for transient errors, and a summary of which providers failed.

**Depends on:** BL-02

**Acceptance criteria**

- [ ] A deliberately failing live test produces a notification
- [ ] Secrets are never echoed in logs

See `docs/dev/backlog.md` (BL-03).'
gh issue create --repo "$REPO" --title 'BL-04: Local parquet cache and `cache=` option on `fetch`' --label ws:platform --body 'Implement `tidesurgedata.cache.Cache` and `default_cache_root` as specified in their docstrings; add `cache: Cache | None = None` to `BaseSource.fetch` and `fetch_with_record` (contract change: code-owner review).

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/spec/test_cache.py` passes with `xfail` markers removed (hit/miss, partial overlap, key includes params and adapter_version, preliminary expiry, atomic write, env var root)

See `docs/dev/backlog.md` (BL-04).'
gh issue create --repo "$REPO" --title 'BL-05: NOAA CO-OPS adapter (water level, wind, pressure) + `find_stations`' --label ws:us-met,adapter --body 'Implement `sources/noaa_coops.py` following its module docstring (provider facts and checklist): interval-dependent chunking, mandatory datum, verified/preliminary quality, wind as u/v components, pressure in Pa.

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/sources/test_noaa_coops.py` passes with markers removed
- [ ] Contract suite runs from a recorded cassette
- [ ] Live smoke test passes nightly

See `docs/dev/backlog.md` (BL-05).'
gh issue create --repo "$REPO" --title 'BL-06: USGS adapter (`waterdata`) + `find_stations`' --label ws:us-met,adapter --body 'Implement `sources/usgs.py` using `dataretrieval.waterdata` (extra `usgs`, `dataretrieval>=1.1.0`), never the legacy `nwis` module. API key from `API_USGS_PAT` only. Convert ft³/s and ft to SI.

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/sources/test_usgs.py` passes with markers removed
- [ ] Cassette contains no API key
- [ ] Import isolation test still passes

See `docs/dev/backlog.md` (BL-06).'
gh issue create --repo "$REPO" --title 'BL-07: EA tide gauge adapter + `find_stations`' --label ws:uk-global,adapter --body 'Implement `sources/ea_tide.py` against the flood-monitoring Tide Gauge API: 15-minute window means, local datum or ODN, OGL licence with exact attribution. Confirm and document the window label convention.

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/sources/test_ea_tide.py` passes with markers removed
- [ ] Label convention evidence recorded in the PR
- [ ] Contract suite runs from a cassette

See `docs/dev/backlog.md` (BL-07).'
gh issue create --repo "$REPO" --title 'BL-08: EA rivers adapter (flood-monitoring + Hydrology API) + `find_stations`' --label ws:uk-global,adapter --body 'Implement `sources/ea_rivers.py`: map flood-monitoring references to Hydrology API GUIDs; archive data as verified, real-time as preliminary, both as mixed; exact attribution.

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/sources/test_ea_rivers.py` passes with markers removed
- [ ] Cassettes for both APIs
- [ ] Quality marking tested

See `docs/dev/backlog.md` (BL-08).'
gh issue create --repo "$REPO" --title 'BL-09: GESLA adapter (blocked on 4.1 API specification)' --label ws:uk-global,adapter --body 'Implement `sources/gesla.py` once Thomas provides the GESLA 4.1 API specification; per-station licence and attribution; local-file fallback.

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/sources/test_gesla.py` passes with markers removed
- [ ] Per-station licences carried into `SeriesMeta`

See `docs/dev/backlog.md` (BL-09).'
gh issue create --repo "$REPO" --title 'BL-10: `align.to_grid`: resampling and gap policy' --label ws:frames --body 'Implement `align.to_grid` per its docstring and ADR 0004: window-mean relabelling, instant nearest within freq/10, centred means with the 50 % rule, `max_gap` interpolation without extrapolation.

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/spec/test_align.py` BL-10 tests pass with markers removed

See `docs/dev/backlog.md` (BL-10).'
gh issue create --repo "$REPO" --title 'BL-11: `align.materialise_lags`' --label ws:frames --body 'Implement `align.materialise_lags` per its docstring: one column per lag named by `lag_column_name`, value at t = series(t + lag), non-multiple lags raise.

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/spec/test_align.py` BL-11 tests pass with markers removed

See `docs/dev/backlog.md` (BL-11).'
gh issue create --repo "$REPO" --title 'BL-12: `Recipe.training_frame` and `provenance`' --label ws:frames --body 'Implement `Recipe.training_frame` and `Recipe.provenance` per their docstrings: regular grid over [start, end), target never interpolated, drivers fetched over lag-widened windows, NaN rows kept, records of the last build.

**Depends on:** BL-10, BL-11

**Acceptance criteria**

- [ ] `tests/spec/test_recipe_frames.py` BL-12 tests pass with markers removed

See `docs/dev/backlog.md` (BL-12).'
gh issue create --repo "$REPO" --title 'BL-13: `Recipe.forecast_frame` and lead-time enforcement' --label ws:frames --body 'Implement `Recipe.forecast_frame` per its docstring and ADRs 0003/0006: grid over (issued, issued + horizon], NaN target, data only if available by issued − latency, forecast sources after issued, horizon beyond `max_lead_time` raises.

**Depends on:** BL-10, BL-11

**Acceptance criteria**

- [ ] `tests/spec/test_recipe_frames.py` BL-13 tests pass with markers removed
- [ ] Leakage test passes

See `docs/dev/backlog.md` (BL-13).'
gh issue create --repo "$REPO" --title 'BL-14: `hindcast_frames` (as-of, no leakage)' --label ws:frames --body 'Implement `hindcast.hindcast_frames` per its docstring and ADR 0006.

**Depends on:** BL-13

**Acceptance criteria**

- [ ] `tests/spec/test_hindcast.py` passes with markers removed

See `docs/dev/backlog.md` (BL-14).'
gh issue create --repo "$REPO" --title 'BL-15: dynamical.org analysis retrieval at a point' --label ws:us-met,adapter --body 'Implement `Dynamical.metadata`, `_fetch` and `find_stations` (analysis datasets) via the STAC catalog and Icechunk Zarr with xarray (extra `met`), lazy imports, CC BY 4.0 (+ ECMWF terms) licences.

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/sources/test_dynamical.py` BL-15 tests pass with markers removed
- [ ] Contract suite runs from a small recorded fixture
- [ ] Import isolation test still passes

See `docs/dev/backlog.md` (BL-15).'
gh issue create --repo "$REPO" --title 'BL-16: dynamical.org forecasts and ensemble members (stretch)' --label ws:us-met,adapter --body 'Implement `Dynamical.init_times` and `fetch_forecast`: latest init_time available by issued − latency, valid_time = init_time + lead_time, members as strings.

**Depends on:** BL-15

**Acceptance criteria**

- [ ] `tests/sources/test_dynamical.py` BL-16 tests pass with markers removed
- [ ] `ForecastSourceContractTests` pass for a forecast dataset

See `docs/dev/backlog.md` (BL-16).'
gh issue create --repo "$REPO" --title 'BL-17: Cross-provider `find_stations`' --label ws:platform --body 'Implement `discovery.find_stations` per its docstring: query registered adapters, skip NotImplementedError with a warning, merge and sort by distance.

**Depends on:** at least two adapters

**Acceptance criteria**

- [ ] `tests/spec/test_discovery.py` passes with markers removed
- [ ] Demonstrated with two real adapters (cassettes)

See `docs/dev/backlog.md` (BL-17).'
gh issue create --repo "$REPO" --title 'BL-18: `to_xarray` / `to_netcdf` / `to_csv` with CF attributes and provenance' --label ws:platform --body 'Implement `io.to_xarray`, `io.to_netcdf` and `io.to_csv` per their docstrings: CF attributes, provenance, licence and attribution; lazy xarray import.

**Depends on:** BL-00

**Acceptance criteria**

- [ ] `tests/spec/test_io.py` passes with markers removed (xarray tests run in the `extras` job)

See `docs/dev/backlog.md` (BL-18).'
gh issue create --repo "$REPO" --title 'BL-19: US demo script: CO-OPS + USGS (+ dynamical.org) training and forecast frames' --label ws:us-met --body 'Add `examples/us_demo.py` building a recipe for a US tide gauge with USGS discharge (and dynamical.org pressure if ready), producing a training frame and a forecast frame, printing provenance and attribution.

**Depends on:** BL-05, BL-06, BL-12, BL-13

**Acceptance criteria**

- [ ] Script runs end to end against live APIs
- [ ] Frames pass `validate_frame`
- [ ] Attribution printed

See `docs/dev/backlog.md` (BL-19).'
gh issue create --repo "$REPO" --title 'BL-20: UK demo script: EA tide gauge + EA rivers (+ dynamical.org) training and forecast frames' --label ws:uk-global --body 'Add `examples/uk_demo.py` building a recipe for an EA tide gauge with EA river flow (and dynamical.org pressure if ready), producing a training frame and a forecast frame, printing provenance and attribution.

**Depends on:** BL-07, BL-08, BL-12, BL-13

**Acceptance criteria**

- [ ] Script runs end to end against live APIs
- [ ] Frames pass `validate_frame`
- [ ] Attribution printed

See `docs/dev/backlog.md` (BL-20).'
gh issue create --repo "$REPO" --title 'BL-21: RTide compatibility walking skeleton green (optional job)' --label ws:platform --body 'Make `tests/compat_rtide/test_walking_skeleton.py` pass in the `rtide-compat` job (requires rtide ≥ 1.0.1 on PyPI).

**Depends on:** BL-12, BL-13

**Acceptance criteria**

- [ ] Walking skeleton passes with its `xfail` marker removed
- [ ] No RTide code or dependency added to the package

See `docs/dev/backlog.md` (BL-21).'
gh issue create --repo "$REPO" --title 'BL-22: `Recipe.forecast_frames` for ensembles (stretch)' --label ws:frames --body 'Implement `Recipe.forecast_frames` per its docstring: one forecast frame per member common to all forecast sources.

**Depends on:** BL-13, BL-16

**Acceptance criteria**

- [ ] `tests/spec/test_recipe_frames.py` BL-22 test passes with marker removed

See `docs/dev/backlog.md` (BL-22).'
