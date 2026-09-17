# Contributing to tidesurgedata

Thank you for helping build one consistent way to get tide gauge, river and meteorological data.

## Contribution terms

This project is licensed under the [MIT License](LICENSE). By submitting a contribution you agree
that it is licensed under the same terms. There is no contributor licence agreement.

## Setup

```bash
git clone https://github.com/thomasmonahan/tidesurgedata.git
cd tidesurgedata
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

Check everything works:

```bash
pytest -m "not live and not rtide"   # unit tests (no network)
ruff check . && ruff format --check .
```

## Workflow

`main` is protected: every change goes through a pull request with passing required checks
(`lint`, `unit`, `extras`) and one approval. Use short-lived branches with one purpose each:

| Prefix | Use |
|---|---|
| `feat/…` | new functionality, e.g. `feat/bl-07-ea-tide` |
| `fix/…` | bug fixes |
| `test/…` | tests and cassettes only |
| `ci/…` | workflows and tooling |

```bash
# start from an up-to-date main
git switch main && git pull
git switch -c feat/bl-07-ea-tide

# commit in small steps (Conventional Commits)
git add -p
git commit -m "feat(ea_tide): metadata and station discovery"

# publish and open a draft PR early
git push -u origin feat/bl-07-ea-tide
gh pr create --draft --title "feat(ea_tide): EA tide gauge adapter" --body "Closes #7"

# keep the branch current with main
git fetch origin
git merge origin/main

# when ready
gh pr ready
```

Pull requests are **squash merged**; the PR title becomes the commit message, so write it as a
Conventional Commit. Link the issue in the description (`Closes #N`). Head branches are deleted
automatically after merge.

## Rules

1. **Independence from RTide** ([ADR 0001](docs/design/0001-standalone-package.md)): no RTide
   code (copied, vendored, paraphrased or ported) and no RTide dependency, required or optional.
   RTide is used only in the optional `rtide-compat` job via its public API.
2. **No live network in unit tests** ([ADR 0005](docs/design/0005-no-live-network-in-unit-tests.md)).
   Use recorded cassettes; see [recording cassettes](docs/dev/recording-cassettes.md). Live smoke
   tests are marked `@pytest.mark.live` and run nightly.
3. **No secrets** in code, specs, recipes, tests, records or cassettes. API keys come from
   environment variables only (e.g. `API_USGS_PAT`).
4. **Contract files** (`meta.py`, `contract.py`, `sources/base.py`, `recipe.py`, `pyproject.toml`,
   `.github/`, `docs/design/`) change only via a pull request approved by a code owner.
5. **Removing an `xfail` marker is part of implementing a feature.** Spec tests use
   `xfail(strict=True)`, so CI fails until the marker is removed once the stub is implemented.
6. **Every adapter records licence and exact attribution text** in `SeriesMeta`.
7. **Lightweight import:** optional dependencies are imported inside functions and raise an
   `ImportError` naming the extra to install.
8. **Coding agents** work on feature branches and open pull requests like everyone else; they
   never push to `main`.
9. Add a `CHANGELOG.md` entry under "Unreleased" for user-visible changes.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat`, `fix`, `test`, `docs`,
`ci`, `chore`, `refactor`, `perf`, with an optional scope, e.g.
`feat(noaa_coops): chunk requests by interval`.

## Where to start

Read the [design records](docs/design/), then the [backlog](docs/dev/backlog.md). Each stub's
docstring is its specification, and its spec tests are in `tests/spec/` or `tests/sources/`.
