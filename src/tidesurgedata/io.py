"""Export of series and frames with provenance, licence and attribution."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from tidesurgedata.meta import FetchRecord

if TYPE_CHECKING:
    import xarray

__all__ = ["to_csv", "to_netcdf", "to_xarray"]


def to_xarray(
    series_or_frame: pd.Series | pd.DataFrame, records: Sequence[FetchRecord]
) -> xarray.Dataset:
    """Convert to an xarray Dataset with CF attributes and provenance.

    CF-convention attributes (units, standard_name where one exists, long_name), global
    attributes carrying provenance, licence and attribution. Lazy xarray import.

    Parameters
    ----------
    series_or_frame : pandas.Series or pandas.DataFrame
        Contract-valid series or frame. The time index becomes the ``time`` coordinate.
    records : sequence of FetchRecord
        Records for the data; each variable's ``units``, ``standard_name`` and ``long_name``
        attributes come from the record whose ``meta.variable`` matches the variable (for frame
        feature columns, the driver variable).

    Returns
    -------
    xarray.Dataset
        One data variable per series/column. Global attributes include ``Conventions``
        (``"CF-1.11"``), ``history``, ``source`` package version, ``provenance`` (JSON list of
        ``FetchRecord.to_dict()``), and ``licence`` / ``attribution`` joined over all records
        without duplicates.

    Raises
    ------
    ImportError
        If xarray is not installed; the message names the ``xarray`` extra.
    """
    raise NotImplementedError("BL-18: io.to_xarray")


def to_netcdf(
    series_or_frame: pd.Series | pd.DataFrame, records: Sequence[FetchRecord], path: str | Path
) -> Path:
    """Write :func:`to_xarray` output to NetCDF at ``path`` and return the path.

    Raises
    ------
    ImportError
        If xarray or netCDF4 is not installed; the message names the ``xarray`` extra.
    """
    raise NotImplementedError("BL-18: io.to_netcdf")


def to_csv(
    series_or_frame: pd.Series | pd.DataFrame, records: Sequence[FetchRecord], path: str | Path
) -> Path:
    """Write CSV at ``path`` with a sidecar JSON provenance file; return the CSV path.

    The CSV has an ISO 8601 UTC ``time`` column followed by the data columns. The sidecar is
    ``path`` with suffix ``.provenance.json`` and contains ``{"records": [...],
    "licence": [...], "attribution": [...], "tidesurgedata_version": ...}``.
    """
    raise NotImplementedError("BL-18: io.to_csv")
