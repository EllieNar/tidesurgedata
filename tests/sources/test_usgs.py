"""Spec and contract tests for the USGS adapter (BL-06)."""

import pandas as pd
import pytest

from tidesurgedata.meta import SeriesMeta
from tidesurgedata.sources.usgs import USGS

from ..contract_suite import SourceContractTests

STUB = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="BL-06")


def make_source():
    return USGS("01376500", parameter="discharge")


@pytest.mark.skip(reason="BL-06: needs cassette")
@pytest.mark.vcr
class TestUSGSContract(SourceContractTests):
    @pytest.fixture
    def source(self):
        return make_source()

    @pytest.fixture
    def window(self):
        return ("2024-01-01T00:00Z", "2024-01-03T00:00Z")


@STUB
def test_metadata():
    meta = make_source().metadata()
    assert meta.source == "usgs"
    assert meta.variable == "discharge"
    assert meta.units == "m3 s-1"
    assert meta.datum is None


@STUB
def test_find_stations():
    stations = USGS.find_stations(40.73, -74.10, radius_km=10, variable="discharge")
    assert stations and all(isinstance(m, SeriesMeta) for m in stations)
    assert all(m.source == "usgs" for m in stations)


@pytest.mark.live
@pytest.mark.enable_socket
@STUB
def test_live_smoke():
    end = pd.Timestamp.now(tz="UTC").floor("1h") - pd.Timedelta("2D")
    series = make_source().fetch(end - pd.Timedelta("1D"), end)
    assert len(series) > 0
