import json

import pandas as pd
import pytest

from tidesurgedata.meta import FetchRecord, SeriesMeta


def make_meta(**overrides):
    kwargs = dict(
        source="fake_tide_gauge",
        station_id="X",
        variable="water_level",
        lat=51.5,
        lon=-3.0,
        units="m",
        datum="MSL",
        sampling="instantaneous",
        window=None,
        label=None,
        licence="synthetic",
        attribution="",
        url="",
    )
    kwargs.update(overrides)
    return SeriesMeta(**kwargs)


def test_valid_meta():
    meta = make_meta()
    assert meta.variable == "water_level"


def test_window_mean_meta():
    meta = make_meta(sampling="window_mean", window=pd.Timedelta("15min"), label="end")
    assert meta.window == pd.Timedelta("15min")


@pytest.mark.parametrize("lat", [-90.1, 90.1, float("nan")])
def test_lat_out_of_range(lat):
    with pytest.raises(ValueError, match="lat"):
        make_meta(lat=lat)


@pytest.mark.parametrize("lon", [-180.1, 360.0, float("inf")])
def test_lon_out_of_range(lon):
    with pytest.raises(ValueError, match="lon"):
        make_meta(lon=lon)


@pytest.mark.parametrize("lon", [-180.0, 0.0, 359.99])
def test_lon_bounds_accepted(lon):
    make_meta(lon=lon)


def test_non_canonical_units():
    with pytest.raises(ValueError, match="canonical"):
        make_meta(units="ft")


def test_datum_required_for_water_level():
    with pytest.raises(ValueError, match="datum"):
        make_meta(datum=None)


def test_datum_optional_for_other_variables():
    make_meta(variable="discharge", units="m3 s-1", datum=None)


@pytest.mark.parametrize(
    "overrides",
    [
        dict(sampling="window_mean"),
        dict(sampling="window_mean", window=pd.Timedelta("1h")),
        dict(sampling="window_mean", label="centre"),
        dict(sampling="window_mean", window=pd.Timedelta(0), label="centre"),
        dict(sampling="window_mean", window=pd.Timedelta("1h"), label="middle"),
        dict(window=pd.Timedelta("1h")),
        dict(label="start"),
        dict(sampling="averaged"),
    ],
)
def test_window_label_iff_window_mean(overrides):
    with pytest.raises(ValueError):
        make_meta(**overrides)


@pytest.mark.parametrize(
    "meta",
    [
        make_meta(name="Somewhere", extra={"k": "v"}),
        make_meta(sampling="window_mean", window=pd.Timedelta("15min"), label="end"),
    ],
)
def test_meta_round_trip(meta):
    d = meta.to_dict()
    assert SeriesMeta.from_dict(json.loads(json.dumps(d))) == meta


def make_record(**overrides):
    kwargs = dict(
        meta=make_meta(),
        start=pd.Timestamp("2024-01-01", tz="UTC"),
        end=pd.Timestamp("2024-01-02", tz="UTC"),
        retrieved_at=pd.Timestamp("2024-02-01T12:00", tz="UTC"),
        quality="verified",
        n_values=240,
        n_missing=3,
        request={"product": "water_level"},
    )
    kwargs.update(overrides)
    return FetchRecord(**kwargs)


def test_record_round_trip():
    rec = make_record()
    assert FetchRecord.from_dict(json.loads(json.dumps(rec.to_dict()))) == rec


def test_record_converts_to_utc():
    rec = make_record(start=pd.Timestamp("2024-01-01T01:00", tz="Europe/Paris"))
    assert str(rec.start.tz) == "UTC"
    assert rec.start == pd.Timestamp("2024-01-01T00:00", tz="UTC")


@pytest.mark.parametrize(
    "overrides",
    [
        dict(start=pd.Timestamp("2024-01-01")),
        dict(end=pd.Timestamp("2023-12-31", tz="UTC")),
        dict(quality="good"),
        dict(n_missing=241),
        dict(n_values=-1),
    ],
)
def test_record_validation(overrides):
    with pytest.raises(ValueError):
        make_record(**overrides)
