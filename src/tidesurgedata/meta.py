"""Series metadata and fetch provenance records.

:class:`SeriesMeta` describes what a series *is* (provider, station, variable, units, datum,
sampling convention, licence). :class:`FetchRecord` describes one retrieval of that series
(time range, when it was retrieved, data quality and the request parameters used).

Both are frozen dataclasses with JSON-safe ``to_dict``/``from_dict`` round trips.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, get_args

import pandas as pd

from tidesurgedata import units
from tidesurgedata.timeutil import to_utc

__all__ = ["DATUM_VARIABLES", "FetchRecord", "Label", "Quality", "Sampling", "SeriesMeta"]

Quality = Literal["verified", "preliminary", "mixed", "unknown"]
Sampling = Literal["instantaneous", "window_mean"]
Label = Literal["start", "centre", "end"]

#: Variables that are heights relative to a datum; ``SeriesMeta.datum`` is required for these.
DATUM_VARIABLES: frozenset[str] = frozenset({"water_level", "stage"})


@dataclass(frozen=True)
class SeriesMeta:
    """Description of a single-variable time series from one station or grid point.

    Parameters
    ----------
    source : str
        Registry name of the adapter, e.g. ``"noaa_coops"``.
    station_id : str
        Provider station identifier (or a grid-point label for gridded sources).
    variable : str
        Variable name, e.g. ``"water_level"``, ``"discharge"``, ``"pressure_surface"``. The series
        name equals this value.
    lat : float
        Latitude in degrees, ``[-90, 90]``.
    lon : float
        Longitude in degrees, ``[-180, 360)``.
    units : str
        Canonical unit string (see :data:`tidesurgedata.units.CANONICAL`).
    datum : str or None
        Vertical datum; required for water level and stage (:data:`DATUM_VARIABLES`).
    sampling : {"instantaneous", "window_mean"}
        Whether values are instantaneous samples or means over a window.
    window : pandas.Timedelta or None
        Averaging window; required if and only if ``sampling == "window_mean"``.
    label : {"start", "centre", "end"} or None
        Which instant of the window the timestamp refers to; required if and only if
        ``sampling == "window_mean"``.
    licence : str
        Licence of the data, e.g. ``"OGL-UK-3.0"``, ``"CC-BY-4.0"``, ``"synthetic"``.
    attribution : str
        Exact attribution text required by the provider (``""`` if none).
    url : str
        Landing page or API endpoint for the station/dataset.
    name : str, optional
        Human-readable station name.
    extra : Mapping[str, str], optional
        Additional provider-specific string metadata.
    """

    source: str
    station_id: str
    variable: str
    lat: float
    lon: float
    units: str
    datum: str | None
    sampling: Sampling
    window: pd.Timedelta | None
    label: Label | None
    licence: str
    attribution: str
    url: str
    name: str = ""
    extra: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        where = f"SeriesMeta({self.source}:{self.station_id}:{self.variable})"
        for attr in ("source", "station_id", "variable"):
            if not isinstance(getattr(self, attr), str) or not getattr(self, attr):
                raise ValueError(f"{where}: {attr} must be a non-empty string.")
        if not (isinstance(self.lat, int | float) and math.isfinite(self.lat)):
            raise ValueError(f"{where}: lat must be a finite number, got {self.lat!r}.")
        if not (isinstance(self.lon, int | float) and math.isfinite(self.lon)):
            raise ValueError(f"{where}: lon must be a finite number, got {self.lon!r}.")
        if not -90.0 <= self.lat <= 90.0:
            raise ValueError(f"{where}: lat {self.lat} outside [-90, 90].")
        if not -180.0 <= self.lon < 360.0:
            raise ValueError(f"{where}: lon {self.lon} outside [-180, 360).")
        if not units.is_canonical(self.units):
            raise ValueError(
                f"{where}: units {self.units!r} are not canonical; "
                f"expected one of {sorted(units.CANONICAL)}."
            )
        if self.variable in DATUM_VARIABLES and not self.datum:
            raise ValueError(f"{where}: datum is required for variable {self.variable!r}.")
        if self.sampling not in get_args(Sampling):
            raise ValueError(f"{where}: sampling {self.sampling!r} not in {get_args(Sampling)}.")
        if self.sampling == "window_mean":
            if not isinstance(self.window, pd.Timedelta) or self.window <= pd.Timedelta(0):
                raise ValueError(
                    f"{where}: window must be a positive pandas.Timedelta for window_mean."
                )
            if self.label not in get_args(Label):
                raise ValueError(
                    f"{where}: label must be one of {get_args(Label)} for window_mean, "
                    f"got {self.label!r}."
                )
        else:
            if self.window is not None or self.label is not None:
                raise ValueError(f"{where}: window and label must be None for instantaneous data.")
        if not all(isinstance(k, str) and isinstance(v, str) for k, v in self.extra.items()):
            raise ValueError(f"{where}: extra must map str to str.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict (``window`` as an ISO 8601 duration)."""
        return {
            "source": self.source,
            "station_id": self.station_id,
            "variable": self.variable,
            "lat": float(self.lat),
            "lon": float(self.lon),
            "units": self.units,
            "datum": self.datum,
            "sampling": self.sampling,
            "window": None if self.window is None else self.window.isoformat(),
            "label": self.label,
            "licence": self.licence,
            "attribution": self.attribution,
            "url": self.url,
            "name": self.name,
            "extra": dict(self.extra),
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> SeriesMeta:
        """Inverse of :meth:`to_dict`."""
        kwargs = dict(d)
        if kwargs.get("window") is not None:
            kwargs["window"] = pd.Timedelta(kwargs["window"])
        kwargs["extra"] = dict(kwargs.get("extra") or {})
        return cls(**kwargs)


@dataclass(frozen=True)
class FetchRecord:
    """Provenance of one retrieval of a series.

    Parameters
    ----------
    meta : SeriesMeta
        Metadata of the series retrieved.
    start, end : pandas.Timestamp
        Requested half-open range ``[start, end)``, UTC.
    retrieved_at : pandas.Timestamp
        When the data was retrieved, UTC.
    quality : {"verified", "preliminary", "mixed", "unknown"}
        Quality of the data returned; ``"mixed"`` if parts differ.
    n_values : int
        Number of timestamps returned.
    n_missing : int
        Number of those values that are NaN.
    request : Mapping[str, str]
        Non-secret request parameters. Never include API keys or tokens.
    """

    meta: SeriesMeta
    start: pd.Timestamp
    end: pd.Timestamp
    retrieved_at: pd.Timestamp
    quality: Quality
    n_values: int
    n_missing: int
    request: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for attr in ("start", "end", "retrieved_at"):
            object.__setattr__(self, attr, to_utc(getattr(self, attr)))
        if self.end < self.start:
            raise ValueError(f"FetchRecord: end {self.end} is before start {self.start}.")
        if self.quality not in get_args(Quality):
            raise ValueError(f"FetchRecord: quality {self.quality!r} not in {get_args(Quality)}.")
        if self.n_values < 0 or self.n_missing < 0 or self.n_missing > self.n_values:
            raise ValueError(
                f"FetchRecord: invalid counts n_values={self.n_values}, n_missing={self.n_missing}."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict (timestamps as ISO 8601 strings)."""
        return {
            "meta": self.meta.to_dict(),
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "retrieved_at": self.retrieved_at.isoformat(),
            "quality": self.quality,
            "n_values": int(self.n_values),
            "n_missing": int(self.n_missing),
            "request": {str(k): str(v) for k, v in self.request.items()},
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> FetchRecord:
        """Inverse of :meth:`to_dict`."""
        return cls(
            meta=SeriesMeta.from_dict(d["meta"]),
            start=pd.Timestamp(d["start"]),
            end=pd.Timestamp(d["end"]),
            retrieved_at=pd.Timestamp(d["retrieved_at"]),
            quality=d["quality"],
            n_values=int(d["n_values"]),
            n_missing=int(d["n_missing"]),
            request=dict(d.get("request") or {}),
        )
