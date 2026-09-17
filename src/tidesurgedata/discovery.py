"""Cross-provider station discovery."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

__all__ = ["find_stations"]


def find_stations(
    lat: float,
    lon: float,
    radius_km: float,
    variables: Sequence[str] | None = None,
    sources: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Find stations near a point across all providers.

    Query find_stations on each registered adapter (or the named subset); return one row per
    station/variable with SeriesMeta fields and distance_km, sorted by distance. Adapters that
    raise NotImplementedError are skipped with a warning.

    Parameters
    ----------
    lat, lon : float
        Search centre in degrees.
    radius_km : float
        Search radius in kilometres (positive).
    variables : sequence of str, optional
        Keep only these variables; default all.
    sources : sequence of str, optional
        Registry names of adapters to query; default all registered adapters. Unknown names
        raise ``KeyError``.

    Returns
    -------
    pandas.DataFrame
        One row per station and variable. Columns: every :class:`~tidesurgedata.meta.SeriesMeta`
        field (``window`` as ``pandas.Timedelta``), then ``distance_km`` (great-circle distance
        from the search centre). Sorted by ``distance_km`` ascending, ties broken by ``source``
        then ``station_id``; a fresh ``RangeIndex``. Empty (with those columns) if nothing is
        found.

    Warns
    -----
    UserWarning
        Once per adapter whose ``find_stations`` raises ``NotImplementedError``.
    """
    raise NotImplementedError("BL-17: cross-provider find_stations")
