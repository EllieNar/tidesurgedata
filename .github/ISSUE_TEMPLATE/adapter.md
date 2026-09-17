---
name: Data adapter
about: Propose or specify a new provider adapter
title: "feat(<source>): <provider> adapter"
labels: adapter
---

## Provider

<!-- Organisation, dataset/product name, documentation links. -->

## Endpoints

<!-- Base URLs and the specific endpoints used (data, metadata, station search). -->

## Identifiers

<!-- Station/site identifier scheme; any mapping between schemes. -->

## Variables and units

<!-- Provider variable -> canonical variable name and unit conversion (ADR 0002). -->

## Datum

<!-- Vertical datums available and which is default. -->

## Sampling and label convention

<!-- Instantaneous or window mean; window length; label (start/centre/end) and evidence. -->

## Per-request limits

<!-- Maximum span per request, rate limits -> `max_request`. -->

## Latency

<!-- Typical delay before data is available -> `latency`; evidence. -->

## Quality flags

<!-- How verified/preliminary is indicated. -->

## Licence and attribution

<!-- Licence identifier and the exact attribution text required. -->

## Authentication

<!-- None, or environment variable name. Never paste keys. -->

## Station discovery

<!-- How `find_stations` will search by location and variable. -->

## Cassette plan

<!-- Station, window and endpoints to record; expected cassette size; filtering. -->

## Acceptance criteria

- [ ] `metadata()`, `_fetch()`, `find_stations()` implemented; `xfail` markers removed
- [ ] Contract suite passes against recorded cassettes
- [ ] Live smoke test passes in the nightly job
- [ ] Licence and attribution recorded; CHANGELOG entry
