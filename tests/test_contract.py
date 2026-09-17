import numpy as np
import pandas as pd
import pytest

from tidesurgedata.contract import (
    ContractError,
    validate_forecast,
    validate_frame,
    validate_series,
)
from tidesurgedata.meta import FetchRecord
from tidesurgedata.sources.base import Forecast

from .test_meta import make_meta


@pytest.fixture
def meta():
    return make_meta()


def series(n=5, **kwargs):
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    return pd.Series(np.arange(n, dtype="float64"), index=idx, name="water_level", **kwargs)


def test_valid_series(meta):
    validate_series(series(), meta)


def test_nan_allowed(meta):
    s = series()
    s.iloc[2] = np.nan
    validate_series(s, meta)


def test_empty_series_allowed(meta):
    validate_series(series(0), meta)


def expect_rule(rule, func, *args):
    with pytest.raises(ContractError) as info:
        func(*args)
    assert info.value.rule == rule
    assert rule in str(info.value)
    return info.value


def test_not_a_series(meta):
    expect_rule("series.type", validate_series, series().to_frame(), meta)


def test_naive_index(meta):
    s = series()
    s.index = s.index.tz_localize(None)
    err = expect_rule("time.utc", validate_series, s, meta)
    assert "fake_tide_gauge:X" in str(err)


def test_non_utc_index(meta):
    s = series()
    s.index = s.index.tz_convert("Europe/London")
    expect_rule("time.utc", validate_series, s, meta)


def test_non_datetime_index(meta):
    s = series().reset_index(drop=True)
    expect_rule("time.index_type", validate_series, s, meta)


def test_duplicates(meta):
    s = series()
    s.index = s.index[[0, 1, 1, 2, 3]]
    expect_rule("time.unique", validate_series, s, meta)


def test_non_monotonic(meta):
    s = series().iloc[[0, 2, 1, 3, 4]]
    expect_rule("time.increasing", validate_series, s, meta)


def test_int_dtype(meta):
    expect_rule("values.float64", validate_series, series().astype("int64"), meta)


def test_float32_dtype(meta):
    expect_rule("values.float64", validate_series, series().astype("float32"), meta)


def test_inf(meta):
    s = series()
    s.iloc[1] = np.inf
    expect_rule("values.no_inf", validate_series, s, meta)


def test_wrong_name(meta):
    expect_rule("series.name", validate_series, series().rename("level"), meta)


def test_non_canonical_unit(meta):
    # SeriesMeta rejects non-canonical units at construction; bypass to test the contract check.
    object.__setattr__(meta, "units", "ft")
    expect_rule("units.canonical", validate_series, series(), meta)


# --- frames -----------------------------------------------------------------------------------


def frame(columns=("observations", "a", "b"), n=6):
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame(np.ones((n, len(columns))), index=idx, columns=list(columns))


def test_valid_frame():
    validate_frame(frame(), "observations", ["a", "b"])


def test_frame_nan_allowed():
    df = frame()
    df.iloc[0, 0] = np.nan
    validate_frame(df, "observations", ["a", "b"])


def test_frame_wrong_target_column():
    expect_rule("frame.target_column", validate_frame, frame(), "water_level", ["a", "b"])


def test_frame_wrong_feature_order():
    expect_rule("frame.feature_columns", validate_frame, frame(), "observations", ["b", "a"])


def test_frame_extra_column():
    expect_rule("frame.feature_columns", validate_frame, frame(), "observations", ["a"])


def test_frame_irregular():
    df = frame().drop(index=frame().index[2])
    expect_rule("frame.regular", validate_frame, df, "observations", ["a", "b"])


def test_frame_naive():
    df = frame()
    df.index = df.index.tz_localize(None)
    expect_rule("time.utc", validate_frame, df, "observations", ["a", "b"])


def test_frame_int_dtype():
    expect_rule("values.float64", validate_frame, frame().astype(int), "observations", ["a", "b"])


def test_frame_inf():
    df = frame()
    df.iloc[3, 2] = -np.inf
    expect_rule("values.no_inf", validate_frame, df, "observations", ["a", "b"])


# --- forecasts --------------------------------------------------------------------------------


def make_forecast(meta, values=None, init="2024-01-01T00:00Z"):
    if values is None:
        idx = pd.date_range("2024-01-01T01:00", periods=3, freq="1h", tz="UTC")
        values = pd.DataFrame({"control": [1.0, 2.0, 3.0], "1": [1.0, 2.0, 3.0]}, index=idx)
    record = FetchRecord(
        meta=meta,
        start=pd.Timestamp(init),
        end=pd.Timestamp("2024-01-02T00:00Z"),
        retrieved_at=pd.Timestamp("2024-01-01T05:00Z"),
        quality="unknown",
        n_values=len(values),
        n_missing=0,
    )
    return Forecast(values=values, init_time=pd.Timestamp(init), record=record)


def test_valid_forecast(meta):
    validate_forecast(make_forecast(meta), meta)


def test_forecast_valid_time_before_init(meta):
    fc = make_forecast(meta, init="2024-01-01T02:00Z")
    expect_rule("forecast.valid_time", validate_forecast, fc, meta)


def test_forecast_non_string_members(meta):
    idx = pd.date_range("2024-01-01T01:00", periods=2, freq="1h", tz="UTC")
    fc = make_forecast(meta, values=pd.DataFrame({0: [1.0, 2.0]}, index=idx))
    expect_rule("forecast.members", validate_forecast, fc, meta)


def test_forecast_meta_mismatch(meta):
    fc = make_forecast(meta)
    expect_rule("forecast.meta", validate_forecast, fc, make_meta(station_id="Y"))
