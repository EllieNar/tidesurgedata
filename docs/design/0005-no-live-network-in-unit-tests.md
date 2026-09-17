# ADR 0005: No live network in unit tests

- **Status:** Proposed (sign-off at kickoff, BL-00)
- **Date:** 2026-09-17

## Context

Provider APIs are slow, rate-limited, change data over time (preliminary to verified) and are
sometimes down. Tests that call them are flaky and would make required checks unreliable. Some
APIs need keys, which must never appear in logs or the repository.

## Decision

- Unit tests never access the network. `pytest-socket` is enabled for all runs
  (`--disable-socket --allow-unix-socket`).
- Adapter behaviour is tested against **recorded cassettes** (`pytest-recording` / `vcrpy`) in
  `tests/cassettes/<test module>/`, replayed with `record_mode="none"`. The VCR configuration
  filters authorisation headers and API-key query parameters. Cassettes are reviewed for secrets
  and size before merging (see `docs/dev/recording-cassettes.md`).
- Every adapter runs the shared **contract suite** (`tests/contract_suite.py`); synthetic fake
  sources run it without cassettes.
- Real endpoints are exercised only by `@pytest.mark.live` smoke tests in the **nightly live job**
  (`nightly-live.yml`), with secrets from repository secrets as environment variables.
- Stubs have spec tests marked `xfail(raises=NotImplementedError, strict=True)`; implementing a
  feature includes removing its markers.

## Consequences

- Required checks are fast and deterministic.
- Provider API changes are detected by the nightly job rather than blocking pull requests.
- Recording and reviewing cassettes is part of implementing an adapter.
