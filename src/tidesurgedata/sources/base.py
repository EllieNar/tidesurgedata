"""Source interfaces: the frozen contract every adapter implements.

Adapters are frozen dataclasses subclassing :class:`BaseSource` (or :class:`GriddedSource` for
point samples of gridded data). An adapter implements :meth:`BaseSource.metadata` and the
single-request hook :meth:`BaseSource._fetch`; chunking, concatenation, de-duplication, slicing,
validation and provenance are handled here, identically for every provider.
"""

from __future__ import annotations

import dataclasses
import json
import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, ClassVar, Protocol, runtime_checkable

import pandas as pd

from tidesurgedata.contract import ContractError, validate_series
from tidesurgedata.meta import FetchRecord, Quality, SeriesMeta
from tidesurgedata.timeutil import TimeLike, is_utc, split_range, to_utc

__all__ = [
    "BaseSource",
    "Forecast",
    "ForecastSource",
    "GriddedSource",
    "Source",
    "combine_quality",
    "haversine_km",
]


@runtime_checkable
class Source(Protocol):
    """Structural interface of a data source."""

    def metadata(self) -> SeriesMeta: ...
    def fetch(self, start: TimeLike, end: TimeLike) -> pd.Series: ...
    def fetch_with_record(
        self, start: TimeLike, end: TimeLike
    ) -> tuple[pd.Series, FetchRecord]: ...
    def to_spec(self) -> dict[str, Any]: ...


def combine_quality(qualities: Sequence[Quality]) -> Quality:
    """Combine chunk qualities: the common value if all agree, ``"mixed"`` otherwise.

    An empty sequence gives ``"unknown"``.
    """
    distinct = set(qualities)
    if not distinct:
        return "unknown"
    if len(distinct) == 1:
        return next(iter(distinct))
    return "mixed"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres on a sphere of radius 6371 km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(min(1.0, math.sqrt(a)))


def _merge_requests(requests: Sequence[dict[str, Any]]) -> dict[str, str]:
    """Merge per-chunk request parameters: agreeing values once, differing values comma-joined."""
    merged: dict[str, list[str]] = {}
    for req in requests:
        for k, v in req.items():
            values = merged.setdefault(str(k), [])
            if str(v) not in values:
                values.append(str(v))
    out = {k: ",".join(v) for k, v in merged.items()}
    out["n_requests"] = str(len(requests))
    return out


class BaseSource(ABC):
    """Base class for all adapters. Adapters are frozen dataclasses subclassing this.

    Class attributes
    ----------------
    registry_name : str
        Set by :func:`~tidesurgedata.sources.registry.register_source`.
    adapter_version : str
        Bump whenever the adapter's output for the same request could change (part of the cache
        key).
    max_request : pandas.Timedelta or None
        Provider per-request limit; requests are split into chunks no longer than this.
    latency : pandas.Timedelta
        Typical delay between a valid time and data being available from the provider.
    """

    registry_name: ClassVar[str]
    adapter_version: ClassVar[str] = "0"
    max_request: ClassVar[pd.Timedelta | None] = None
    latency: ClassVar[pd.Timedelta] = pd.Timedelta(0)

    @abstractmethod
    def metadata(self) -> SeriesMeta:
        """Return the metadata of the series this source produces."""

    @abstractmethod
    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        """Adapter hook: one provider request for [start, end). Return values in canonical units,
        the quality of the data returned, and the non-secret request parameters used."""

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        """Return metadata for stations of this provider within ``radius_km`` of a point.

        Parameters
        ----------
        lat, lon : float
            Search centre in degrees.
        radius_km : float
            Search radius in kilometres.
        variable : str, optional
            Restrict to stations serving this variable.

        Returns
        -------
        list of SeriesMeta
            One entry per station and variable.
        """
        raise NotImplementedError(f"{cls.__name__}.find_stations is not implemented.")

    def fetch(self, start: TimeLike, end: TimeLike) -> pd.Series:
        """Fetch the series over ``[start, end)``. See :meth:`fetch_with_record`."""
        series, _ = self.fetch_with_record(start, end)
        return series

    def fetch_with_record(self, start: TimeLike, end: TimeLike) -> tuple[pd.Series, FetchRecord]:
        """Fetch the series over ``[start, end)`` together with its provenance record.

        The range is split into chunks of at most :attr:`max_request`; :meth:`_fetch` is called
        once per chunk; results are concatenated, duplicate timestamps dropped (keeping the
        last), sorted, sliced to ``[start, end)``, named after the variable and validated.

        Parameters
        ----------
        start, end : time-like
            Timezone-aware bounds of the half-open range.

        Returns
        -------
        series : pandas.Series
            Contract-valid series.
        record : FetchRecord
            Provenance of this retrieval.

        Raises
        ------
        ValueError
            If ``start`` or ``end`` are naive, or ``end < start``.
        ContractError
            If the adapter returns data breaking the data contract.
        """
        s, e = to_utc(start), to_utc(end)
        meta = self.metadata()
        where = f"{meta.source}:{meta.station_id}:{meta.variable}"

        pieces: list[pd.Series] = []
        qualities: list[Quality] = []
        requests: list[dict[str, Any]] = []
        for cs, ce in split_range(s, e, self.max_request):
            piece, quality, request = self._fetch(cs, ce)
            if not isinstance(piece, pd.Series):
                raise ContractError(
                    "series.type", where, f"_fetch returned {type(piece).__name__}, not Series."
                )
            if not isinstance(piece.index, pd.DatetimeIndex) or not is_utc(piece.index.tz):
                raise ContractError("time.utc", where, "_fetch returned a non-UTC index.")
            pieces.append(piece)
            qualities.append(quality)
            requests.append(dict(request))

        non_empty = [p for p in pieces if len(p)]
        if non_empty:
            series = pd.concat(non_empty) if len(non_empty) > 1 else non_empty[0].copy()
        else:
            dtype = pieces[0].dtype if pieces else "float64"
            series = pd.Series([], index=pd.DatetimeIndex([], tz="UTC"), dtype=dtype)
        series = series[~series.index.duplicated(keep="last")].sort_index()
        series = series[(series.index >= s) & (series.index < e)]
        series.name = meta.variable
        series.index.name = "time"
        validate_series(series, meta)

        record = FetchRecord(
            meta=meta,
            start=s,
            end=e,
            retrieved_at=pd.Timestamp.now(tz="UTC"),
            quality=combine_quality(qualities),
            n_values=int(len(series)),
            n_missing=int(series.isna().sum()),
            request=_merge_requests(requests),
        )
        return series, record

    def to_spec(self) -> dict[str, Any]:
        """Serialise the source as ``{"type": registry_name, "params": {...}}``.

        Parameters are the dataclass fields. Nested sources are serialised as nested specs.

        Raises
        ------
        TypeError
            If the source is not a dataclass or its parameters are not JSON-serialisable.
        """
        if not dataclasses.is_dataclass(self):
            raise TypeError(f"{type(self).__name__} must be a dataclass to serialise.")
        params: dict[str, Any] = {}
        for f in dataclasses.fields(self):
            value = getattr(self, f.name)
            params[f.name] = value.to_spec() if isinstance(value, BaseSource) else value
        spec = {"type": self.registry_name, "params": params}
        try:
            json.dumps(spec, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"{type(self).__name__} parameters are not JSON-serialisable: {exc}"
            ) from exc
        return spec


class GriddedSource(BaseSource):
    """Sources sampled at a point on a grid (e.g. meteorology).

    Subclasses must have ``lat`` and ``lon`` dataclass fields; ``None`` means "not yet located"
    (a recipe resolves it to the target location).
    """

    def with_location(self, lat: float, lon: float) -> GriddedSource:
        """Return a copy of this source sampled at ``(lat, lon)``."""
        return dataclasses.replace(self, lat=lat, lon=lon)  # type: ignore[type-var]


@dataclasses.dataclass(frozen=True)
class Forecast:
    """A forecast of one variable from a single initialisation.

    Parameters
    ----------
    values : pandas.DataFrame
        Index ``valid_time`` (UTC); columns are member labels (str). Deterministic forecasts use
        a single column ``"control"``.
    init_time : pandas.Timestamp
        Initialisation time actually used (UTC).
    record : FetchRecord
        Provenance of the retrieval.
    """

    values: pd.DataFrame
    init_time: pd.Timestamp
    record: FetchRecord


@runtime_checkable
class ForecastSource(Protocol):
    """Structural interface of a source that also serves forecasts."""

    def fetch_forecast(
        self, issued: TimeLike, horizon: pd.Timedelta, members: Sequence[str] | None = None
    ) -> Forecast:
        """Use the latest initialisation time available by `issued` (respecting latency).
        Never use data initialised after that."""
        ...

    def init_times(self, start: TimeLike, end: TimeLike) -> pd.DatetimeIndex:
        """Initialisation times in ``[start, end)``."""
        ...
