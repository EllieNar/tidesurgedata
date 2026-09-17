"""Deterministic synthetic sources for tests, examples and development without network access.

Values are pure functions of the timestamp (and the source parameters), never of call order or
chunking, so fetching ``[a, c)`` equals fetching ``[a, b)`` and ``[b, c)`` and concatenating.
Pseudo-randomness comes from a SplitMix64 hash of the int64 timestamp and a seed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pandas as pd

from tidesurgedata.contract import validate_forecast
from tidesurgedata.meta import FetchRecord, Quality, SeriesMeta
from tidesurgedata.sources.base import (
    BaseSource,
    Forecast,
    GriddedSource,
    haversine_km,
)
from tidesurgedata.sources.registry import register_source
from tidesurgedata.timeutil import TimeLike, regular_grid, to_utc

__all__ = ["FakeMet", "FakeRiver", "FakeTideGauge"]

_NS_PER_HOUR = 3_600_000_000_000
_MASK64 = np.uint64(0xFFFFFFFFFFFFFFFF)


# --- deterministic hashing ----------------------------------------------------------------------


def _splitmix64(x: np.ndarray) -> np.ndarray:
    z = x.astype(np.uint64)
    with np.errstate(over="ignore"):
        z = z + np.uint64(0x9E3779B97F4A7C15)
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        z = z ^ (z >> np.uint64(31))
    return z & _MASK64


def _uniform(keys: np.ndarray, *salts: int) -> np.ndarray:
    """Uniform values in (0, 1) as a deterministic function of int64 ``keys`` and ``salts``."""
    h = np.asarray(keys, dtype=np.int64).view(np.uint64)
    for salt in salts:
        h = _splitmix64(h ^ _splitmix64(np.array([salt], dtype=np.int64).view(np.uint64)))
    h = _splitmix64(h)
    return ((h >> np.uint64(11)).astype(np.float64) + 0.5) / float(1 << 53)


def _normal(keys: np.ndarray, *salts: int) -> np.ndarray:
    """Standard normal values as a deterministic function of ``keys`` and ``salts`` (Box-Muller)."""
    u1 = _uniform(keys, *salts, 1)
    u2 = _uniform(keys, *salts, 2)
    return np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)


def _ns(index: pd.DatetimeIndex) -> np.ndarray:
    """Nanoseconds since the epoch, independent of the index's datetime resolution."""
    return index.as_unit("ns").asi8


def _hours(index: pd.DatetimeIndex) -> np.ndarray:
    return _ns(index) / _NS_PER_HOUR


# --- sources --------------------------------------------------------------------------------------

_MET_VARIABLES = {"pressure_surface": "Pa", "wind_u_10m": "m s-1", "wind_v_10m": "m s-1"}
_MET_MEMBERS = ("control", *(str(i) for i in range(1, 11)))


@register_source("fake_met")
@dataclass(frozen=True)
class FakeMet(GriddedSource):
    """Synthetic meteorology at a point: analysis via ``fetch`` and forecasts via
    ``fetch_forecast``.

    The analysis is a smooth synoptic signal, reported as 1-hour window means labelled at the
    window centre. Forecasts are initialised every 6 hours, available 4 hours after
    initialisation, and equal the truth plus an error that grows with lead time; members
    ``"1"``…``"10"`` add deterministic per-member perturbations to the control.

    Parameters
    ----------
    station_id : str
        Label for the grid point.
    lat, lon : float or None
        Sample location; ``None`` until located (e.g. by ``Recipe.resolved``).
    freq : str
        Output spacing.
    seed : int
        Seed for the deterministic signal and forecast errors.
    variable : {"pressure_surface", "wind_u_10m", "wind_v_10m"}
        Variable produced.
    """

    station_id: str = "FAKE-MET"
    lat: float | None = 51.5
    lon: float | None = -3.0
    freq: str = "1h"
    seed: int = 2
    variable: str = "pressure_surface"

    latency: ClassVar[pd.Timedelta] = pd.Timedelta("4h")
    init_interval: ClassVar[pd.Timedelta] = pd.Timedelta("6h")
    members: ClassVar[tuple[str, ...]] = _MET_MEMBERS

    def __post_init__(self) -> None:
        if self.variable not in _MET_VARIABLES:
            raise ValueError(f"FakeMet variable must be one of {sorted(_MET_VARIABLES)}.")

    def _located(self) -> tuple[float, float]:
        if self.lat is None or self.lon is None:
            raise ValueError("FakeMet has no location; call with_location(lat, lon) first.")
        return float(self.lat), float(self.lon)

    def metadata(self) -> SeriesMeta:
        lat, lon = self._located()
        return SeriesMeta(
            source=self.registry_name,
            station_id=self.station_id,
            variable=self.variable,
            lat=lat,
            lon=lon,
            units=_MET_VARIABLES[self.variable],
            datum=None,
            sampling="window_mean",
            window=pd.Timedelta(self.freq),
            label="centre",
            licence="synthetic",
            attribution="",
            url="",
            name="Synthetic meteorology",
        )

    def signal(self, index: pd.DatetimeIndex) -> np.ndarray:
        """Continuous 'true' value at arbitrary UTC times."""
        lat, lon = self._located()
        h = _hours(index) + lon * 2.0  # systems travel eastwards
        base, scale = (101325.0, 1.0) if self.variable == "pressure_surface" else (0.0, 0.006)
        periods = np.array([74.0, 137.0, 263.0])
        amps = np.array([800.0, 500.0, 300.0]) * scale
        salt = list(_MET_VARIABLES).index(self.variable)
        phases = 2 * np.pi * _uniform(np.arange(3), self.seed, salt) + lat / 10.0
        out = np.full(h.shape, base, dtype=np.float64)
        for p, a, ph in zip(periods, amps, phases, strict=True):
            out += a * np.sin(2 * np.pi * h / p + ph)
        return out

    def _window_mean(self, index: pd.DatetimeIndex) -> np.ndarray:
        step = pd.Timedelta(self.freq)
        offsets = (np.arange(12) + 0.5) / 12 - 0.5
        samples = [self.signal(index + step * o) for o in offsets]
        return np.mean(samples, axis=0)

    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        index = regular_grid(start, end, self.freq)
        values = self._window_mean(index)
        series = pd.Series(values, index=index, name=self.variable, dtype="float64")
        return series, "verified", {"product": "analysis", "variable": self.variable}

    def init_times(self, start: TimeLike, end: TimeLike) -> pd.DatetimeIndex:
        """Initialisation times (every 6 h at 00, 06, 12, 18 UTC) in ``[start, end)``."""
        return regular_grid(start, end, self.init_interval).rename("init_time")

    def _error(self, lead_hours: np.ndarray, init: pd.Timestamp, member_salt: int) -> np.ndarray:
        """Smooth error in lead time, amplitude growing linearly with lead."""
        scale = 60.0 if self.variable == "pressure_surface" else 0.4
        key = np.array([init.as_unit("ns").value], dtype=np.int64)
        out = np.zeros_like(lead_hours, dtype=np.float64)
        for k, period in enumerate((19.0, 41.0, 97.0)):
            amp = _normal(key, self.seed, member_salt, k, 10)[0]
            phase = 2 * np.pi * _uniform(key, self.seed, member_salt, k, 20)[0]
            out += amp * np.sin(2 * np.pi * lead_hours / period + phase)
        return scale * (lead_hours / 24.0) * out

    def fetch_forecast(
        self, issued: TimeLike, horizon: pd.Timedelta, members: Sequence[str] | None = None
    ) -> Forecast:
        """Forecast from the latest initialisation available by ``issued``.

        The initialisation used is the latest multiple of 6 h not after ``issued - latency``.
        Valid times run from the initialisation time to ``issued + horizon`` inclusive.

        Parameters
        ----------
        issued : time-like
            Time the forecast is issued (timezone-aware).
        horizon : pandas.Timedelta
            How far beyond ``issued`` valid times extend.
        members : sequence of str, optional
            Members to return; default all (``"control"``, ``"1"``…``"10"``).
        """
        issued_ts = to_utc(issued)
        horizon = pd.Timedelta(horizon)
        if horizon < pd.Timedelta(0):
            raise ValueError("horizon must be non-negative.")
        selected = tuple(self.members if members is None else members)
        unknown = set(selected) - set(self.members)
        if unknown or not selected:
            raise ValueError(f"Unknown members {sorted(unknown)}; available: {self.members}.")

        init = (issued_ts - self.latency).floor(self.init_interval)
        end = issued_ts + horizon
        index = pd.date_range(init, end, freq=self.freq, name="valid_time")
        truth = self._window_mean(index)
        lead = (index - init) / pd.Timedelta("1h")
        common = self._error(np.asarray(lead, dtype=np.float64), init, member_salt=0)
        columns = {}
        for m in selected:
            values = truth + common
            if m != "control":
                values = values + 0.5 * self._error(
                    np.asarray(lead, dtype=np.float64), init, member_salt=int(m)
                )
            columns[m] = values
        frame = pd.DataFrame(columns, index=index, dtype="float64")

        meta = self.metadata()
        record = FetchRecord(
            meta=meta,
            start=init,
            end=end + pd.Timedelta(self.freq),
            retrieved_at=pd.Timestamp.now(tz="UTC"),
            quality="unknown",
            n_values=int(frame.size),
            n_missing=int(frame.isna().to_numpy().sum()),
            request={
                "product": "forecast",
                "init_time": init.isoformat(),
                "members": ",".join(selected),
            },
        )
        forecast = Forecast(values=frame, init_time=init, record=record)
        validate_forecast(forecast, meta)
        return forecast

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        """Return the default fake grid point if within ``radius_km``."""
        return _find_default(cls, lat, lon, radius_km, variable)


@register_source("fake_river")
@dataclass(frozen=True)
class FakeRiver(BaseSource):
    """Synthetic river discharge: seasonal baseline plus deterministic flood events.

    Parameters
    ----------
    station_id : str
    lat, lon : float
    freq : str
        Output spacing.
    seed : int
        Seed for flood event timing and magnitude.
    """

    station_id: str = "FAKE-RV"
    lat: float = 51.6
    lon: float = -2.9
    freq: str = "15min"
    seed: int = 1

    latency: ClassVar[pd.Timedelta] = pd.Timedelta("1h")

    def metadata(self) -> SeriesMeta:
        return SeriesMeta(
            source=self.registry_name,
            station_id=self.station_id,
            variable="discharge",
            lat=self.lat,
            lon=self.lon,
            units="m3 s-1",
            datum=None,
            sampling="instantaneous",
            window=None,
            label=None,
            licence="synthetic",
            attribution="",
            url="",
            name="Synthetic river",
        )

    def discharge(self, index: pd.DatetimeIndex) -> np.ndarray:
        """Continuous discharge (m3 s-1) at arbitrary UTC times."""
        h = _hours(index)
        day_of_year = (h / 24.0) % 365.25
        baseline = 40.0 + 25.0 * np.cos(2 * np.pi * (day_of_year - 15.0) / 365.25)
        bin_hours = 240.0  # at most one flood event per 10-day bin
        rise = 18.0
        k = np.floor(h / bin_hours).astype(np.int64)
        floods = np.zeros_like(h)
        for back in range(3):
            b = k - back
            happens = _uniform(b, self.seed, 1) < 0.6
            onset = (b + _uniform(b, self.seed, 2) * 0.5) * bin_hours
            peak = 50.0 + 250.0 * _uniform(b, self.seed, 3)
            x = np.clip(h - onset, 0.0, None) / rise
            floods += np.where(happens, peak * x * np.exp(1.0 - x), 0.0)
        return baseline + floods

    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        index = regular_grid(start, end, self.freq)
        series = pd.Series(self.discharge(index), index=index, name="discharge", dtype="float64")
        return series, "verified", {"station": self.station_id}

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        """Return the default fake station if within ``radius_km``."""
        return _find_default(cls, lat, lon, radius_km, variable)


# Harmonic constituents: name -> (speed in degrees per hour, amplitude m, phase degrees).
_CONSTITUENTS = {
    "M2": (28.9841042, 1.20, 40.0),
    "S2": (30.0000000, 0.40, 75.0),
    "K1": (15.0410686, 0.15, 120.0),
    "O1": (13.9430356, 0.12, 300.0),
}


@register_source("fake_tide_gauge")
@dataclass(frozen=True)
class FakeTideGauge(BaseSource):
    """Synthetic tide gauge water level relative to MSL.

    ``water_level(t) = tide(t) + surge_pressure(t) + river_coeff * discharge(t - river_lag_hours)
    + noise(t)``, where ``tide`` is the sum of M2, S2, K1 and O1 harmonics and
    ``surge_pressure`` is the inverse-barometer response (-0.01 m per hPa anomaly from 101325 Pa).

    Parameters
    ----------
    station_id : str
    lat, lon : float
    freq : str
        Output spacing.
    seed : int
        Seed for the noise.
    noise_std : float
        Standard deviation of the noise (m).
    pressure : FakeMet, optional
        Couple to this pressure field.
    river : FakeRiver, optional
        Couple to this river.
    river_lag_hours : float
        Delay between river discharge and its effect on water level.
    river_coeff : float
        Water level response per unit discharge (m per m3 s-1).
    """

    station_id: str = "FAKE-TG"
    lat: float = 51.5
    lon: float = -3.0
    freq: str = "6min"
    seed: int = 0
    noise_std: float = 0.02
    pressure: FakeMet | None = None
    river: FakeRiver | None = None
    river_lag_hours: float = 12.0
    river_coeff: float = 2e-4

    max_request: ClassVar[pd.Timedelta | None] = pd.Timedelta("30D")
    latency: ClassVar[pd.Timedelta] = pd.Timedelta("10min")

    def metadata(self) -> SeriesMeta:
        return SeriesMeta(
            source=self.registry_name,
            station_id=self.station_id,
            variable="water_level",
            lat=self.lat,
            lon=self.lon,
            units="m",
            datum="MSL",
            sampling="instantaneous",
            window=None,
            label=None,
            licence="synthetic",
            attribution="",
            url="",
            name="Synthetic tide gauge",
        )

    def tide(self, index: pd.DatetimeIndex) -> np.ndarray:
        """Astronomical tide (m) at arbitrary UTC times."""
        h = _hours(index)
        out = np.zeros_like(h)
        for speed, amp, phase in _CONSTITUENTS.values():
            out += amp * np.cos(np.deg2rad(speed * h - phase))
        return out

    def water_level(self, index: pd.DatetimeIndex) -> np.ndarray:
        """Total water level (m) at arbitrary UTC times."""
        level = self.tide(index)
        if self.pressure is not None:
            level = level - 0.01 * (self.pressure.signal(index) - 101325.0) / 100.0
        if self.river is not None:
            lagged = index - pd.Timedelta(hours=self.river_lag_hours)
            level = level + self.river_coeff * self.river.discharge(lagged)
        if self.noise_std:
            level = level + self.noise_std * _normal(_ns(index), self.seed)
        return level

    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        index = regular_grid(start, end, self.freq)
        series = pd.Series(
            self.water_level(index), index=index, name="water_level", dtype="float64"
        )
        request = {"station": self.station_id, "begin": start.isoformat(), "end": end.isoformat()}
        return series, "verified", request

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        """Return the default fake station if within ``radius_km``."""
        return _find_default(cls, lat, lon, radius_km, variable)


def _find_default(
    cls: type[BaseSource], lat: float, lon: float, radius_km: float, variable: str | None
) -> list[SeriesMeta]:
    meta = cls().metadata()  # type: ignore[call-arg]
    if variable is not None and variable != meta.variable:
        return []
    if haversine_km(lat, lon, meta.lat, meta.lon) > radius_km:
        return []
    return [meta]
