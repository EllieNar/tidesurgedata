"""Spec and contract tests for the EARiver adapter (BL-08)."""

import pandas as pd
import pytest

from tidesurgedata.meta import SeriesMeta
from tidesurgedata.sources.ea_rivers import EARiver

from ..contract_suite import SourceContractTests

STUB = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="BL-08")


def make_source():
    return EARiver("3400TH", parameter="flow")


@pytest.mark.skip(reason="BL-08: needs cassette")
@pytest.mark.vcr
class TestEARiverContract(SourceContractTests):
    @pytest.fixture
    def source(self):
        return make_source()

    @pytest.fixture
    def window(self):
        return ("2024-01-01T00:00Z", "2024-01-03T00:00Z")


@STUB
def test_metadata():
    meta = make_source().metadata()
    assert meta.source == "ea_rivers"
    assert meta.variable == "discharge"
    assert meta.units == "m3 s-1"
    assert meta.attribution == (
        "This uses Environment Agency flood and river level data from the real-time data API (Beta)"
    )


@STUB
def test_find_stations():
    stations = EARiver.find_stations(51.49, -0.12, radius_km=20, variable="discharge")
    assert stations and all(isinstance(m, SeriesMeta) for m in stations)
    assert all(m.source == "ea_rivers" for m in stations)


@pytest.mark.live
@pytest.mark.enable_socket
@STUB
def test_live_smoke():
    end = pd.Timestamp.now(tz="UTC").floor("1h") - pd.Timedelta("2D")
    series = make_source().fetch(end - pd.Timedelta("1D"), end)
    assert len(series) > 0
