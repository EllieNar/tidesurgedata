"""Spec and contract tests for the EATideGauge adapter (BL-07)."""

import pandas as pd
import pytest

from tidesurgedata.meta import SeriesMeta
from tidesurgedata.sources.ea_tide import EATideGauge

from ..contract_suite import SourceContractTests

STUB = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="BL-07")


def make_source():
    return EATideGauge("E72639")


@pytest.mark.skip(reason="BL-07: needs cassette")
@pytest.mark.vcr
class TestEATideGaugeContract(SourceContractTests):
    @pytest.fixture
    def source(self):
        return make_source()

    @pytest.fixture
    def window(self):
        return ("2024-01-01T00:00Z", "2024-01-03T00:00Z")


@STUB
def test_metadata():
    meta = make_source().metadata()
    assert meta.source == "ea_tide"
    assert meta.variable == "water_level"
    assert meta.units == "m"
    assert meta.datum is not None
    assert meta.sampling == "window_mean"
    assert meta.window == pd.Timedelta("15min")
    assert meta.label in {"start", "centre", "end"}
    assert meta.attribution == (
        "this uses Environment Agency tide gauge data from the real-time data API (Beta)"
    )


@STUB
def test_find_stations():
    stations = EATideGauge.find_stations(51.44, 0.74, radius_km=20)
    assert stations and all(isinstance(m, SeriesMeta) for m in stations)
    assert all(m.source == "ea_tide" for m in stations)


@pytest.mark.live
@pytest.mark.enable_socket
@STUB
def test_live_smoke():
    end = pd.Timestamp.now(tz="UTC").floor("1h") - pd.Timedelta("2D")
    series = make_source().fetch(end - pd.Timedelta("1D"), end)
    assert len(series) > 0
