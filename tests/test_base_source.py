import dataclasses
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

from tidesurgedata.contract import ContractError
from tidesurgedata.meta import SeriesMeta
from tidesurgedata.sources.base import BaseSource, combine_quality, haversine_km
from tidesurgedata.sources.registry import _REGISTRY, register_source, source_from_spec

CALLS: list[tuple[pd.Timestamp, pd.Timestamp]] = []


@pytest.fixture(autouse=True)
def _reset_calls():
    CALLS.clear()


def _meta(variable="discharge"):
    return SeriesMeta(
        source="test_hourly",
        station_id="T1",
        variable=variable,
        lat=0.0,
        lon=0.0,
        units="m3 s-1",
        datum=None,
        sampling="instantaneous",
        window=None,
        label=None,
        licence="synthetic",
        attribution="",
        url="",
    )


@dataclasses.dataclass(frozen=True)
class HourlySource(BaseSource):
    """In-test adapter: hourly values equal to hours since epoch.

    ``mode`` selects misbehaviour: "overlap" returns one extra hour on each side of the chunk,
    "shuffled" returns values out of order, "int" returns int64, "naive" a naive index,
    "badname" a wrong name (fixed by base), "inf" an inf value, "unsorted_dupes" duplicates.
    ``prelim_after`` marks chunks starting at or after that ISO time as preliminary.
    """

    mode: str = "ok"
    prelim_after: str | None = None

    max_request: ClassVar[pd.Timedelta | None] = pd.Timedelta("10h")

    def metadata(self) -> SeriesMeta:
        return _meta()

    def _fetch(self, start, end):
        CALLS.append((start, end))
        lo, hi = start, end
        if self.mode == "overlap":
            lo, hi = start - pd.Timedelta("1h"), end + pd.Timedelta("1h")
        index = pd.date_range(lo.ceil("1h"), hi, freq="1h", inclusive="left", tz="UTC")
        values = (index.as_unit("ns").asi8 // 3_600_000_000_000).astype("float64")
        s = pd.Series(values, index=index, name="whatever")
        if self.mode == "overlap":
            # overlapping values from a later chunk should win
            s = s + float(len(CALLS)) / 1000
        if self.mode == "shuffled":
            s = s.iloc[::-1]
        if self.mode == "int":
            s = s.astype("int64")
        if self.mode == "naive":
            s.index = s.index.tz_localize(None)
        if self.mode == "inf" and len(s):
            s.iloc[0] = np.inf
        if self.mode == "not_series":
            return s.to_frame(), "verified", {}
        quality = "verified"
        if self.prelim_after is not None and start >= pd.Timestamp(self.prelim_after):
            quality = "preliminary"
        return s, quality, {"site": "T1", "begin": start.isoformat()}


register_source("test_hourly")(HourlySource)


@dataclasses.dataclass(frozen=True)
class NotJsonSource(HourlySource):
    thing: object = dataclasses.field(default_factory=object)


START = pd.Timestamp("2024-01-01T00:00Z")
END = pd.Timestamp("2024-01-02T01:00Z")  # 25 hours


def test_chunking_obeys_max_request():
    series, record = HourlySource().fetch_with_record(START, END)
    assert len(CALLS) == 3
    assert all(e - s <= pd.Timedelta("10h") for s, e in CALLS)
    assert CALLS[0][0] == START and CALLS[-1][1] == END
    assert all(CALLS[i][1] == CALLS[i + 1][0] for i in range(len(CALLS) - 1))
    assert len(series) == 25
    assert record.request["n_requests"] == "3"
    assert record.request["site"] == "T1"
    assert "," in record.request["begin"]


def test_concatenation_dedup_keeps_last_and_slices():
    series = HourlySource(mode="overlap").fetch(START, END)
    assert len(series) == 25
    assert series.index[0] == START
    assert series.index[-1] == END - pd.Timedelta("1h")
    assert series.index.is_unique and series.index.is_monotonic_increasing
    # 10:00 is returned by chunk 1 (overlap) and chunk 2; the later chunk wins
    assert series[pd.Timestamp("2024-01-01T10:00Z")] % 1 == pytest.approx(0.002)


def test_sorting():
    series = HourlySource(mode="shuffled").fetch(START, END)
    assert series.index.is_monotonic_increasing


def test_name_set_to_variable():
    assert HourlySource().fetch(START, END).name == "discharge"


def test_empty_range():
    series, record = HourlySource().fetch_with_record(START, START)
    assert len(series) == 0
    assert series.dtype == "float64"
    assert record.quality == "unknown"
    assert CALLS == []


def test_naive_bounds_rejected():
    with pytest.raises(ValueError, match="Naive"):
        HourlySource().fetch("2024-01-01", END)


def test_mixed_quality():
    _, record = HourlySource(prelim_after="2024-01-01T12:00Z").fetch_with_record(START, END)
    assert record.quality == "mixed"
    _, record = HourlySource(prelim_after="2023-01-01T00:00Z").fetch_with_record(START, END)
    assert record.quality == "preliminary"


def test_combine_quality():
    assert combine_quality([]) == "unknown"
    assert combine_quality(["verified", "verified"]) == "verified"
    assert combine_quality(["verified", "preliminary"]) == "mixed"


@pytest.mark.parametrize(
    ("mode", "rule"),
    [
        ("int", "values.float64"),
        ("inf", "values.no_inf"),
        ("naive", "time.utc"),
        ("not_series", "series.type"),
    ],
)
def test_invalid_adapter_output_raises(mode, rule):
    with pytest.raises(ContractError) as info:
        HourlySource(mode=mode).fetch(START, END)
    assert info.value.rule == rule
    assert "test_hourly:T1" in str(info.value)


def test_record_fields():
    series, record = HourlySource().fetch_with_record(START, END)
    assert record.meta == _meta()
    assert (record.start, record.end) == (START, END)
    assert record.n_values == 25 and record.n_missing == 0
    assert str(record.retrieved_at.tz) == "UTC"


def test_to_spec_round_trip():
    source = HourlySource(mode="shuffled", prelim_after="2024-01-01T00:00Z")
    spec = source.to_spec()
    assert spec == {
        "type": "test_hourly",
        "params": {"mode": "shuffled", "prelim_after": "2024-01-01T00:00Z"},
    }
    assert source_from_spec(spec) == source


def test_non_json_params_raise():
    register_source("test_not_json")(NotJsonSource)
    try:
        with pytest.raises(TypeError, match="JSON"):
            NotJsonSource().to_spec()
    finally:
        _REGISTRY.pop("test_not_json")


def test_to_spec_requires_dataclass():
    class Plain(BaseSource):
        registry_name = "plain"

        def metadata(self):
            return _meta()

        def _fetch(self, start, end):
            raise AssertionError

    with pytest.raises(TypeError, match="dataclass"):
        Plain().to_spec()


def test_find_stations_default_not_implemented():
    with pytest.raises(NotImplementedError):
        HourlySource.find_stations(0.0, 0.0, 10.0)


def test_haversine():
    assert haversine_km(0, 0, 0, 0) == 0
    assert haversine_km(0, 0, 0, 1) == pytest.approx(111.19, rel=1e-3)
    assert haversine_km(51.5, -3.0, 51.5, 357.0) == pytest.approx(0.0, abs=1e-6)
