import numpy as np
import pandas as pd
import pytest

from tidesurgedata.contract import validate_forecast, validate_series
from tidesurgedata.sources.base import ForecastSource, GriddedSource
from tidesurgedata.sources.fake import FakeMet, FakeRiver, FakeTideGauge

from .contract_suite import ForecastSourceContractTests, SourceContractTests

WINDOW = ("2024-01-01T00:00Z", "2024-02-15T00:00Z")


class TestFakeTideGaugeContract(SourceContractTests):
    @pytest.fixture
    def source(self, fake_tide_gauge):
        return fake_tide_gauge

    @pytest.fixture
    def window(self):
        return WINDOW


class TestFakeRiverContract(SourceContractTests):
    @pytest.fixture
    def source(self, fake_river):
        return fake_river

    @pytest.fixture
    def window(self):
        return WINDOW


class TestFakeMetContract(SourceContractTests):
    @pytest.fixture
    def source(self, fake_met):
        return fake_met

    @pytest.fixture
    def window(self):
        return WINDOW


class TestFakeMetForecastContract(ForecastSourceContractTests):
    @pytest.fixture
    def source(self, fake_met):
        return fake_met

    @pytest.fixture(params=["2024-01-10T00:00Z", "2024-01-10T03:59Z", "2024-01-10T04:00Z"])
    def issued(self, request):
        return request.param

    @pytest.fixture
    def horizon(self):
        return pd.Timedelta("48h")


@pytest.mark.parametrize(
    "source",
    [FakeTideGauge(pressure=FakeMet(), river=FakeRiver()), FakeRiver(), FakeMet()],
    ids=["tide", "river", "met"],
)
@pytest.mark.parametrize("split", ["2024-01-05T07:13Z", "2024-01-31T00:00Z", "2024-02-01T00:06Z"])
def test_determinism_across_chunking(source, split):
    a, c = "2024-01-01T00:00Z", "2024-02-20T00:00Z"
    whole = source.fetch(a, c)
    parts = pd.concat([source.fetch(a, split), source.fetch(split, c)])
    pd.testing.assert_series_equal(whole, parts, check_freq=False)
    pd.testing.assert_series_equal(whole, source.fetch(a, c))


def test_values_depend_on_seed():
    a = FakeTideGauge(seed=0).fetch(*WINDOW)
    b = FakeTideGauge(seed=1).fetch(*WINDOW)
    assert not np.allclose(a, b)


def test_tide_gauge_signal_plausible(fake_tide_gauge):
    s = fake_tide_gauge.fetch(*WINDOW)
    validate_series(s, fake_tide_gauge.metadata())
    assert s.index.freq is None or s.index[1] - s.index[0] == pd.Timedelta("6min")
    assert 0.6 < s.std() < 1.5  # dominated by the 1.2 m M2 tide
    assert fake_tide_gauge.max_request == pd.Timedelta("30D")
    assert fake_tide_gauge.latency == pd.Timedelta("10min")


def test_tide_gauge_couplings():
    index = pd.date_range("2024-01-01", periods=1000, freq="6min", tz="UTC")
    met, river = FakeMet(), FakeRiver()
    plain = FakeTideGauge(noise_std=0.0)
    coupled = FakeTideGauge(noise_std=0.0, pressure=met, river=river)
    diff = coupled.water_level(index) - plain.water_level(index)
    expected = -0.01 * (met.signal(index) - 101325.0) / 100.0 + 2e-4 * river.discharge(
        index - pd.Timedelta("12h")
    )
    np.testing.assert_allclose(diff, expected)


def test_river_has_floods(fake_river):
    s = fake_river.fetch("2024-01-01T00:00Z", "2024-12-31T00:00Z")
    assert (s > 0).all()
    assert s.max() > 2 * s.median()
    assert fake_river.latency == pd.Timedelta("1h")


def test_met_is_gridded_forecast_source(fake_met):
    assert isinstance(fake_met, GriddedSource)
    assert isinstance(fake_met, ForecastSource)
    meta = fake_met.metadata()
    assert meta.sampling == "window_mean"
    assert meta.window == pd.Timedelta("1h")
    assert meta.label == "centre"
    assert meta.units == "Pa"
    assert fake_met.latency == pd.Timedelta("4h")


def test_met_with_location(fake_met):
    moved = fake_met.with_location(40.0, 10.0)
    assert (moved.lat, moved.lon) == (40.0, 10.0)
    assert moved.metadata().lat == 40.0
    assert not np.allclose(moved.fetch(*WINDOW), fake_met.fetch(*WINDOW))
    with pytest.raises(ValueError, match="location"):
        FakeMet(lat=None, lon=None).metadata()


def test_met_init_times(fake_met):
    times = fake_met.init_times("2024-01-01T01:00Z", "2024-01-02T00:00Z")
    assert list(times.hour) == [6, 12, 18]


@pytest.mark.parametrize(
    "issued",
    pd.date_range("2024-01-10T00:00Z", "2024-01-11T00:00Z", freq="37min"),
)
def test_forecast_never_uses_init_after_issued_minus_latency(fake_met, issued):
    fc = fake_met.fetch_forecast(issued, pd.Timedelta("24h"))
    assert fc.init_time <= issued - fake_met.latency
    assert fc.init_time > issued - fake_met.latency - pd.Timedelta("6h")
    last = fc.values.index[-1]
    assert issued + pd.Timedelta("23h") < last <= issued + pd.Timedelta("24h")


def test_forecast_members(fake_met):
    fc = fake_met.fetch_forecast("2024-01-10T12:00Z", pd.Timedelta("72h"))
    assert list(fc.values.columns) == ["control", *[str(i) for i in range(1, 11)]]
    validate_forecast(fc, fake_met.metadata())
    subset = fake_met.fetch_forecast("2024-01-10T12:00Z", pd.Timedelta("72h"), members=["3"])
    assert list(subset.values.columns) == ["3"]
    pd.testing.assert_series_equal(subset.values["3"], fc.values["3"])
    with pytest.raises(ValueError):
        fake_met.fetch_forecast("2024-01-10T12:00Z", pd.Timedelta("72h"), members=["99"])


def test_forecast_error_grows_with_lead(fake_met):
    issued = pd.Timestamp("2024-01-10T12:00Z")
    fc = fake_met.fetch_forecast(issued, pd.Timedelta("120h"))
    truth = fake_met.fetch(fc.values.index[0], fc.values.index[-1] + pd.Timedelta("1h"))
    error = fc.values.sub(truth, axis=0).abs()
    assert error.iloc[0].max() == pytest.approx(0.0, abs=1e-6)  # lead 0 is the analysis
    early = error.iloc[:12].to_numpy().mean()
    late = error.iloc[-24:].to_numpy().mean()
    assert late > 5 * early
    assert error.iloc[-1].std() > 0  # members differ


def test_forecast_deterministic(fake_met):
    a = fake_met.fetch_forecast("2024-01-10T12:00Z", pd.Timedelta("24h"))
    b = fake_met.fetch_forecast("2024-01-10T12:00Z", pd.Timedelta("24h"))
    pd.testing.assert_frame_equal(a.values, b.values)


@pytest.mark.parametrize("cls", [FakeTideGauge, FakeRiver, FakeMet])
def test_fake_find_stations_radius(cls):
    default = cls()
    meta = default.metadata()
    assert cls.find_stations(meta.lat, meta.lon, 1.0) == [meta]
    assert cls.find_stations(meta.lat + 1.0, meta.lon, 100.0) == []  # ~111 km away
    assert cls.find_stations(meta.lat + 1.0, meta.lon, 120.0) == [meta]
    assert cls.find_stations(meta.lat, meta.lon, 1.0, variable=meta.variable) == [meta]
    assert cls.find_stations(meta.lat, meta.lon, 1.0, variable="nonexistent") == []


@pytest.mark.parametrize("source", [FakeTideGauge(), FakeRiver(), FakeMet()])
def test_fake_licence(source):
    meta = source.metadata()
    assert meta.licence == "synthetic"
    assert meta.attribution == ""
