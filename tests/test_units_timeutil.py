import datetime as dt

import numpy as np
import pandas as pd
import pytest

from tidesurgedata import timeutil, units


@pytest.mark.parametrize(
    ("value", "from_unit", "to_unit", "expected"),
    [
        (1.0, "ft", "m", 0.3048),
        (100.0, "cm", "m", 1.0),
        (1000.0, "mm", "m", 1.0),
        (1.0, "ft3 s-1", "m3 s-1", 0.028316846592),
        (1013.25, "hPa", "Pa", 101325.0),
        (1013.25, "mbar", "Pa", 101325.0),
        (101.325, "kPa", "Pa", 101325.0),
        (1.0, "knot", "m s-1", 0.514444444),
        (0.0, "degC", "K", 273.15),
        (32.0, "degF", "K", 273.15),
        (212.0, "degF", "K", 373.15),
        (5.0, "m", "m", 5.0),
    ],
)
def test_convert_scalar(value, from_unit, to_unit, expected):
    assert units.convert(value, from_unit, to_unit) == pytest.approx(expected)


def test_convert_series_keeps_index_and_dtype():
    s = pd.Series([1, 2], index=["a", "b"], name="x")
    out = units.convert(s, "ft", "m")
    assert out.dtype == "float64"
    assert list(out.index) == ["a", "b"]
    assert out.name == "x"


def test_convert_array():
    out = units.convert(np.array([0, 100]), "degC", "K")
    np.testing.assert_allclose(out, [273.15, 373.15])


@pytest.mark.parametrize(("f", "t"), [("furlong", "m"), ("m", "ft"), ("hPa", "K")])
def test_convert_unknown(f, t):
    with pytest.raises(ValueError, match="Unsupported"):
        units.convert(1.0, f, t)


def test_canonical_set():
    assert {"m", "m s-1", "m3 s-1", "Pa", "K", "kg m-2 s-1", "W m-2", "1"} == units.CANONICAL


@pytest.mark.parametrize(
    "x",
    [
        "2024-01-01T00:00Z",
        "2024-01-01T01:00+01:00",
        dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc),
        pd.Timestamp("2024-01-01", tz="UTC"),
    ],
)
def test_to_utc(x):
    out = timeutil.to_utc(x)
    assert out == pd.Timestamp("2024-01-01", tz="UTC")
    assert str(out.tz) == "UTC"


@pytest.mark.parametrize(
    "x", ["2024-01-01", dt.datetime(2024, 1, 1), pd.Timestamp("2024-01-01"), "not a time"]
)
def test_to_utc_rejects_naive(x):
    with pytest.raises(ValueError):
        timeutil.to_utc(x)


def test_to_utc_index():
    idx = pd.date_range("2024-01-01", periods=2, freq="1h", tz="Europe/London")
    assert str(timeutil.to_utc(idx).tz) == "UTC"
    with pytest.raises(ValueError, match="Naive"):
        timeutil.to_utc(idx.tz_localize(None))


@pytest.mark.parametrize(
    ("start", "end", "span", "n"),
    [
        ("2024-01-01T00:00Z", "2024-03-01T00:00Z", "30D", 2),
        ("2024-01-01T00:00Z", "2024-01-31T00:00Z", "30D", 1),
        ("2024-01-01T00:00Z", "2024-01-31T00:01Z", "30D", 2),
        ("2024-01-01T00:00Z", "2024-01-02T00:00Z", "7h", 4),
        ("2024-01-01T00:00Z", "2024-01-02T00:00Z", None, 1),
    ],
)
def test_split_range_exact_coverage(start, end, span, n):
    max_span = None if span is None else pd.Timedelta(span)
    chunks = timeutil.split_range(start, end, max_span)
    assert len(chunks) == n
    assert chunks[0][0] == pd.Timestamp(start)
    assert chunks[-1][1] == pd.Timestamp(end)
    for (_, e1), (s2, _) in zip(chunks, chunks[1:], strict=False):
        assert e1 == s2  # contiguous, no overlap, no gap
    for s, e in chunks:
        assert s < e
        if max_span is not None:
            assert e - s <= max_span


def test_split_range_edge_cases():
    assert timeutil.split_range("2024-01-01T00:00Z", "2024-01-01T00:00Z", None) == []
    with pytest.raises(ValueError):
        timeutil.split_range("2024-01-02T00:00Z", "2024-01-01T00:00Z", None)
    with pytest.raises(ValueError):
        timeutil.split_range("2024-01-01T00:00Z", "2024-01-02T00:00Z", pd.Timedelta(0))
    with pytest.raises(ValueError):
        timeutil.split_range("2024-01-01", "2024-01-02T00:00Z", None)


def test_regular_grid_half_open_and_aligned():
    grid = timeutil.regular_grid("2024-01-01T00:30Z", "2024-01-01T04:00Z", "1h")
    expected = pd.date_range("2024-01-01T01:00", "2024-01-01T03:00", freq="1h", tz="UTC")
    assert list(grid) == list(expected)
    assert str(grid.tz) == "UTC"


def test_regular_grid_includes_start_when_aligned():
    grid = timeutil.regular_grid("2024-01-01T00:00Z", "2024-01-01T01:00Z", "15min")
    assert len(grid) == 4
    assert grid[0] == pd.Timestamp("2024-01-01T00:00Z")
