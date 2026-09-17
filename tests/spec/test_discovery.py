"""Spec tests for discovery.find_stations (BL-17)."""

import dataclasses
import warnings

import pytest

from tidesurgedata.discovery import find_stations
from tidesurgedata.meta import SeriesMeta

BL17 = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="BL-17")

FAKES = ["fake_tide_gauge", "fake_river", "fake_met"]
META_FIELDS = [f.name for f in dataclasses.fields(SeriesMeta)]


@BL17
def test_find_stations_merges_and_sorts():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        df = find_stations(51.55, -2.95, radius_km=50)
    # adapters whose find_stations raises NotImplementedError are skipped with a warning
    assert any(issubclass(w.category, UserWarning) for w in caught)
    assert list(df.columns) == [*META_FIELDS, "distance_km"]
    assert set(FAKES) <= set(df["source"])
    assert df["distance_km"].is_monotonic_increasing
    assert list(df.index) == list(range(len(df)))


@BL17
def test_find_stations_subset_and_variables():
    df = find_stations(51.5, -3.0, radius_km=50, sources=["fake_river", "fake_tide_gauge"])
    assert set(df["source"]) == {"fake_river", "fake_tide_gauge"}
    df = find_stations(51.5, -3.0, radius_km=50, sources=FAKES, variables=["discharge"])
    assert list(df["source"]) == ["fake_river"]


@BL17
def test_find_stations_radius():
    df = find_stations(0.0, 0.0, radius_km=10, sources=FAKES)
    assert df.empty
    assert list(df.columns) == [*META_FIELDS, "distance_km"]


@BL17
def test_find_stations_unknown_source():
    with pytest.raises(KeyError):
        find_stations(51.5, -3.0, radius_km=50, sources=["nope"])
