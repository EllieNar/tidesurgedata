"""Reusable contract tests for adapters.

Subclass :class:`SourceContractTests` in an adapter's test module and provide fixtures ``source``
and ``window``. Real adapters replay recorded cassettes (pytest-recording); fakes need nothing.
Forecast sources also subclass :class:`ForecastSourceContractTests` and provide ``issued`` and
``horizon``.
"""

import json

import pandas as pd

from tidesurgedata.contract import validate_forecast, validate_series
from tidesurgedata.meta import FetchRecord, SeriesMeta
from tidesurgedata.sources.base import BaseSource
from tidesurgedata.sources.registry import source_from_spec
from tidesurgedata.timeutil import to_utc


class SourceContractTests:
    """Subclass and provide fixtures `source` and `window` (start, end).
    Real adapters use recorded cassettes (pytest-recording); fakes need nothing."""

    def test_metadata_valid(self, source: BaseSource):
        meta = source.metadata()
        assert isinstance(meta, SeriesMeta)
        assert meta.source == source.registry_name
        assert SeriesMeta.from_dict(json.loads(json.dumps(meta.to_dict()))) == meta
        assert isinstance(meta.licence, str) and meta.licence
        assert isinstance(meta.attribution, str)

    def test_fetch_obeys_contract(self, source: BaseSource, window):
        start, end = (to_utc(t) for t in window)
        series = source.fetch(start, end)
        validate_series(series, source.metadata())
        assert len(series) > 0, "window should contain data"
        assert series.index.min() >= start
        assert series.index.max() < end

    def test_chunking_consistent(self, source: BaseSource, window):
        start, end = (to_utc(t) for t in window)
        middle = start + (end - start) / 2
        whole = source.fetch(start, end)
        parts = pd.concat([source.fetch(start, middle), source.fetch(middle, end)])
        pd.testing.assert_series_equal(whole, parts, check_freq=False)

    def test_spec_round_trip(self, source: BaseSource):
        spec = source.to_spec()
        assert json.loads(json.dumps(spec)) == spec
        rebuilt = source_from_spec(json.loads(json.dumps(spec)))
        assert rebuilt == source
        assert rebuilt.to_spec() == spec

    def test_record_complete(self, source: BaseSource, window):
        start, end = (to_utc(t) for t in window)
        series, record = source.fetch_with_record(start, end)
        assert isinstance(record, FetchRecord)
        assert record.meta == source.metadata()
        assert (record.start, record.end) == (start, end)
        assert record.n_values == len(series)
        assert record.n_missing == int(series.isna().sum())
        assert record.quality in {"verified", "preliminary", "mixed", "unknown"}
        assert FetchRecord.from_dict(json.loads(json.dumps(record.to_dict()))) == record


class ForecastSourceContractTests:
    """Subclass and provide fixtures `source` (a ForecastSource), `issued` and `horizon`."""

    def test_forecast_obeys_contract(self, source, issued, horizon):
        fc = source.fetch_forecast(issued, horizon)
        validate_forecast(fc, source.metadata())
        assert fc.values.index.max() >= to_utc(issued) + pd.Timedelta(horizon) - pd.Timedelta("6h")

    def test_forecast_never_uses_future_init(self, source, issued, horizon):
        issued = to_utc(issued)
        fc = source.fetch_forecast(issued, horizon)
        assert fc.init_time <= issued - source.latency

    def test_forecast_uses_latest_available_init(self, source, issued, horizon):
        issued = to_utc(issued)
        fc = source.fetch_forecast(issued, horizon)
        cutoff = issued - source.latency
        available = source.init_times(cutoff - pd.Timedelta("10D"), cutoff + pd.Timedelta(1, "ns"))
        assert fc.init_time == available.max()

    def test_init_times_in_range(self, source, issued):
        issued = to_utc(issued)
        times = source.init_times(issued - pd.Timedelta("2D"), issued)
        assert len(times) > 0
        assert times.is_monotonic_increasing and times.is_unique
        assert times.min() >= issued - pd.Timedelta("2D")
        assert times.max() < issued
