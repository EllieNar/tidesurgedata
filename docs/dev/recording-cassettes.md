# Recording cassettes

Unit tests never touch the network (ADR 0005). Adapter tests replay HTTP responses recorded with
[pytest-recording](https://github.com/kiwicom/pytest-recording) (built on vcrpy).

## Where cassettes live

`tests/cassettes/<test module name>/<test name>.yaml`, e.g.
`tests/cassettes/test_noaa_coops/TestNOAACoopsContract.test_fetch_obeys_contract.yaml`. The
directory is set by the `vcr_cassette_dir` fixture in `tests/conftest.py`.

## Recording

1. Remove the `@pytest.mark.skip(reason="BL-xx: needs cassette")` marker from the adapter's
   `Test…Contract` class (it already has `@pytest.mark.vcr`).
2. Choose a **small** window (a day or two) and a stable, verified period.
3. Record, allowing sockets for this run only:

   ```bash
   pytest tests/sources/test_noaa_coops.py --record-mode=once --force-enable-socket
   ```

   For APIs needing a key, export it first (e.g. `export API_USGS_PAT=...`); never write it to a
   file in the repository.
4. Re-run **without** network to confirm replay works:

   ```bash
   pytest tests/sources/test_noaa_coops.py
   ```

## Reviewing before committing

- **Secrets:** search the cassettes for keys, tokens and account identifiers:

  ```bash
  grep -riE "api[_-]?key|token|authorization|pat=|secret" tests/cassettes/
  ```

  Nothing should match except filtered placeholders.
- **Size:** keep each cassette well under the 500 kB `check-added-large-files` limit; shrink the
  window or the number of stations if needed.
- **Content:** no personal data; responses are provider data covered by the provider's licence.

## Filtering secrets

`vcr_config` in `tests/conftest.py` removes common authorisation headers
(`authorization`, `x-api-key`, `api-key`, `cookie`) and API-key query parameters (`api_key`,
`apikey`, `token`, `key`, `access_token`). If a provider uses another header or parameter name,
override `vcr_config` in that adapter's test module:

```python
@pytest.fixture(scope="module")
def vcr_config(vcr_config):
    return {**vcr_config, "filter_headers": [*vcr_config["filter_headers"], "x-provider-key"]}
```

## Re-recording

Delete the affected cassette files and record again with `--record-mode=once`. If an adapter's
output changes, bump its `adapter_version`.

## Live smoke tests

Each adapter also has a `@pytest.mark.live` smoke test that hits the real API. They run in the
nightly job (`pytest -m live`), never in required checks.
