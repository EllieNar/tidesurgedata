# Hackathon kickoff: first half-day

**Goal:** everyone leaves with a working environment, a shared understanding of the contracts,
signed-off design records (BL-00), a claimed issue and a first draft pull request.

| Time | Session | Lead |
|---|---|---|
| 0:00–0:15 | Welcome, goals and scope: a model-agnostic data package; independence from RTide (ADR 0001) | Thomas |
| 0:15–0:45 | **Environment setup** (below); everyone runs the unit tests green | Fellow 1 |
| 0:45–1:30 | **Contracts walk-through:** `SeriesMeta`/`FetchRecord`, `validate_*`, `BaseSource` (chunking, quality, provenance), registry and specs, `Recipe` column layout and the lead-time rule | Thomas |
| 1:30–1:45 | Break | |
| 1:45–2:15 | **Fake sources and the walking skeleton:** fetch, chunk determinism, forecasts and latency; `tests/compat_rtide/test_walking_skeleton.py` as the end-to-end target | Fellow 4 |
| 2:15–2:45 | **BL-00 sign-off:** ADRs 0001–0006; open questions (EA label convention, latencies, GESLA 4.1 spec); agree any contract changes as PRs | All |
| 2:45–3:15 | **Claiming issues:** workstreams (`ws:platform`, `ws:us-met`, `ws:uk-global`, `ws:frames`), dependencies from the backlog, pairing plan | All |
| 3:15–4:00 | **First draft PRs:** branch, first commit, `gh pr create --draft`; each PR removes at least one `xfail` or adds one cassette plan | All |

## Environment setup

```bash
git clone https://github.com/thomasmonahan/tidesurgedata.git
cd tidesurgedata
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
pytest -m "not live and not rtide"     # expect passes, xfails and skips; no failures
```

## Before the session

- Read `README.md`, `CONTRIBUTING.md` and `docs/design/`.
- Have GitHub access to the repository and an authenticated `gh` CLI.
- US workstream: request a USGS API key (stored only as `API_USGS_PAT` in your environment).

## Outputs

- [ ] ADRs 0001–0006 accepted or amended (BL-00)
- [ ] Every issue BL-01…BL-22 has an owner or is explicitly deferred
- [ ] One draft PR per fellow
