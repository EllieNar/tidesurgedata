"""Data contract validation (see ``docs/design/0002-data-contract.md``).

Every series, forecast and frame produced by this package passes through these checks. Errors
are :class:`ContractError` with a message naming the rule broken and the source involved.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from tidesurgedata import units
from tidesurgedata.meta import SeriesMeta
from tidesurgedata.timeutil import is_utc

if TYPE_CHECKING:
    from tidesurgedata.sources.base import Forecast

__all__ = ["ContractError", "validate_forecast", "validate_frame", "validate_series"]


class ContractError(ValueError):
    """Raised when data breaks the data contract."""

    def __init__(self, rule: str, where: str, detail: str) -> None:
        self.rule = rule
        self.where = where
        super().__init__(f"[{where}] contract rule '{rule}' violated: {detail}")


def _where(meta: SeriesMeta) -> str:
    return f"{meta.source}:{meta.station_id}:{meta.variable}"


def _check_time_index(index: pd.Index, where: str) -> None:
    if not isinstance(index, pd.DatetimeIndex):
        raise ContractError("time.index_type", where, f"index is {type(index).__name__}.")
    if index.tz is None:
        raise ContractError("time.utc", where, "index is naive; must be timezone-aware UTC.")
    if not is_utc(index.tz):
        raise ContractError("time.utc", where, f"index time zone is {index.tz}, not UTC.")
    if not index.is_unique:
        n = int(index.duplicated().sum())
        raise ContractError("time.unique", where, f"index has {n} duplicate timestamp(s).")
    if not index.is_monotonic_increasing:
        raise ContractError("time.increasing", where, "index is not strictly increasing.")


def _check_values(values: pd.Series | pd.DataFrame, where: str) -> None:
    dtypes = [values.dtype] if isinstance(values, pd.Series) else list(values.dtypes)
    bad = [str(d) for d in dtypes if d != np.dtype("float64")]
    if bad:
        raise ContractError("values.float64", where, f"dtype(s) {sorted(set(bad))}, not float64.")
    if np.isinf(values.to_numpy()).any():
        raise ContractError("values.no_inf", where, "values contain inf; use NaN for missing.")


def validate_series(s: pd.Series, meta: SeriesMeta) -> None:
    """Check a series against the data contract.

    Rules: ``pandas.Series``; UTC ``DatetimeIndex``, strictly increasing and unique; ``float64``
    values with no ``inf``; name equals ``meta.variable``; ``meta.units`` canonical.

    Raises
    ------
    ContractError
        On the first rule broken.
    """
    where = _where(meta)
    if not isinstance(s, pd.Series):
        raise ContractError(
            "series.type", where, f"expected pandas.Series, got {type(s).__name__}."
        )
    _check_time_index(s.index, where)
    _check_values(s, where)
    if s.name != meta.variable:
        raise ContractError(
            "series.name", where, f"series name {s.name!r} != variable {meta.variable!r}."
        )
    if not units.is_canonical(meta.units):
        raise ContractError("units.canonical", where, f"units {meta.units!r} are not canonical.")


def validate_forecast(fc: Forecast, meta: SeriesMeta) -> None:
    """Check a :class:`~tidesurgedata.sources.base.Forecast` against the data contract.

    Rules: ``values`` is a DataFrame with a valid UTC time index (``valid_time``), ``float64``
    values, no ``inf``, at least one column, string member labels; ``init_time`` is UTC; the
    record's metadata matches ``meta``; no valid time precedes ``init_time``.

    Raises
    ------
    ContractError
        On the first rule broken.
    """
    where = _where(meta)
    values = fc.values
    if not isinstance(values, pd.DataFrame):
        raise ContractError(
            "forecast.type", where, f"values must be a DataFrame, got {type(values).__name__}."
        )
    _check_time_index(values.index, where)
    _check_values(values, where)
    if values.shape[1] == 0:
        raise ContractError("forecast.members", where, "forecast has no member columns.")
    if not all(isinstance(c, str) for c in values.columns):
        raise ContractError("forecast.members", where, "member labels must be strings.")
    init = fc.init_time
    if not isinstance(init, pd.Timestamp) or not is_utc(init.tz):
        raise ContractError("forecast.init_time", where, f"init_time {init!r} is not UTC.")
    if len(values.index) and values.index[0] < init:
        raise ContractError(
            "forecast.valid_time", where, f"valid time {values.index[0]} precedes init {init}."
        )
    if fc.record.meta != meta:
        raise ContractError("forecast.meta", where, "record metadata does not match meta.")


def validate_frame(df: pd.DataFrame, target_column: str, feature_columns: Sequence[str]) -> None:
    """Check a training or forecast frame against the data contract.

    Rules: regular, strictly increasing, unique UTC ``DatetimeIndex``; columns are exactly
    ``[target_column, *feature_columns]`` in that order; all ``float64``; no ``inf``. NaN is
    allowed.

    Raises
    ------
    ContractError
        On the first rule broken.
    """
    where = f"frame:{target_column}"
    if not isinstance(df, pd.DataFrame):
        raise ContractError("frame.type", where, f"expected DataFrame, got {type(df).__name__}.")
    _check_time_index(df.index, where)
    if len(df.index) > 2:
        steps = np.unique(np.diff(df.index.asi8))
        if len(steps) != 1:
            raise ContractError("frame.regular", where, "index spacing is not regular.")
    expected = [target_column, *feature_columns]
    actual = list(df.columns)
    if actual[:1] != [target_column]:
        raise ContractError(
            "frame.target_column",
            where,
            f"first column is {actual[0] if actual else None!r}, expected {target_column!r}.",
        )
    if actual != expected:
        raise ContractError(
            "frame.feature_columns", where, f"columns {actual} != expected {expected}."
        )
    _check_values(df, where)
