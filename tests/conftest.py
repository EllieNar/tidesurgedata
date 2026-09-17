"""Shared fixtures: fake sources, a fake recipe and VCR configuration for recorded cassettes."""

from pathlib import Path

import pytest

from tidesurgedata import Driver, Recipe
from tidesurgedata.sources.fake import FakeMet, FakeRiver, FakeTideGauge

CASSETTE_ROOT = Path(__file__).parent / "cassettes"


@pytest.fixture
def fake_met() -> FakeMet:
    return FakeMet()


@pytest.fixture
def fake_river() -> FakeRiver:
    return FakeRiver()


@pytest.fixture
def fake_tide_gauge(fake_met: FakeMet, fake_river: FakeRiver) -> FakeTideGauge:
    """Tide gauge coupled to the fake pressure field and river."""
    return FakeTideGauge(pressure=fake_met, river=fake_river)


@pytest.fixture
def fake_recipe(fake_tide_gauge: FakeTideGauge, fake_river: FakeRiver, fake_met: FakeMet) -> Recipe:
    """Hourly recipe: discharge at lags (-24, -12) h; pressure at lag 0 with a forecast source."""
    return Recipe(
        target=fake_tide_gauge,
        drivers=(
            Driver("discharge", fake_river, lags_hours=(-24, -12)),
            Driver("pressure", fake_met, lags_hours=(0,), forecast=fake_met),
        ),
        freq="1h",
    )


@pytest.fixture(scope="module")
def vcr_config() -> dict:
    """Never record secrets: strip auth headers and API-key query parameters."""
    return {
        "filter_headers": ["authorization", "x-api-key", "api-key", "cookie"],
        "filter_query_parameters": ["api_key", "apikey", "token", "key", "access_token"],
        "decode_compressed_response": True,
        "record_mode": "none",
    }


@pytest.fixture(scope="module")
def vcr_cassette_dir(request: pytest.FixtureRequest) -> str:
    """Cassettes live in tests/cassettes/<test module name>/."""
    return str(CASSETTE_ROOT / request.module.__name__.split(".")[-1])
