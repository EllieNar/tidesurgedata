"""Spec and contract tests for the GESLA adapter (BL-09)."""

import pytest

from tidesurgedata.meta import SeriesMeta
from tidesurgedata.sources.gesla import GESLA

from ..contract_suite import SourceContractTests

STUB = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="BL-09")


def make_source():
    return GESLA("newlyn-nwl-gbr-bodc")


@pytest.mark.skip(reason="BL-09: needs cassette")
@pytest.mark.vcr
class TestGESLAContract(SourceContractTests):
    @pytest.fixture
    def source(self):
        return make_source()

    @pytest.fixture
    def window(self):
        return ("2024-01-01T00:00Z", "2024-01-03T00:00Z")


@STUB
def test_metadata():
    meta = make_source().metadata()
    assert meta.source == "gesla"
    assert meta.variable == "water_level"
    assert meta.units == "m"
    assert meta.datum is not None
    assert meta.licence  # carried per station from the original provider


@STUB
def test_find_stations():
    stations = GESLA.find_stations(50.10, -5.54, radius_km=10)
    assert stations and all(isinstance(m, SeriesMeta) for m in stations)
    assert all(m.source == "gesla" for m in stations)


@pytest.mark.live
@pytest.mark.enable_socket
@STUB
def test_live_smoke():
    series = make_source().fetch("2010-01-01T00:00Z", "2010-01-02T00:00Z")
    assert len(series) > 0
