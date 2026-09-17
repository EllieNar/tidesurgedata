"""Time handling helpers: UTC normalisation, request chunking and regular grids.

All time ranges in this package are half-open, ``[start, end)``.
"""

from __future__ import annotations

import datetime as dt
from typing import overload

import pandas as pd

__all__ = ["is_utc", "regular_grid", "split_range", "to_utc"]

TimeLike = str | dt.datetime | pd.Timestamp


def is_utc(tz: dt.tzinfo | None) -> bool:
    """Return True if ``tz`` is a UTC time zone (any implementation)."""
    if tz is None:
        return False
    return str(tz) in {"UTC", "Etc/UTC", "UTC+00:00", "Z"}


@overload
def to_utc(x: pd.DatetimeIndex) -> pd.DatetimeIndex: ...
@overload
def to_utc(x: TimeLike) -> pd.Timestamp: ...
def to_utc(x):
    """Convert a timezone-aware time or index to UTC.

    Parameters
    ----------
    x : str, datetime, pandas.Timestamp or pandas.DatetimeIndex
        Timezone-aware input. Strings must carry an offset, e.g. ``"2024-01-01T00:00Z"``.

    Returns
    -------
    pandas.Timestamp or pandas.DatetimeIndex
        The same instant(s) in UTC.

    Raises
    ------
    ValueError
        If the input is naive (has no time zone) or cannot be parsed.
    """
    if isinstance(x, pd.DatetimeIndex):
        if x.tz is None:
            raise ValueError("Naive DatetimeIndex rejected: times must be timezone-aware (UTC).")
        return x.tz_convert("UTC")
    try:
        ts = pd.Timestamp(x)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Cannot interpret {x!r} as a timestamp.") from exc
    if ts is pd.NaT:
        raise ValueError("NaT is not a valid time.")
    if ts.tz is None:
        raise ValueError(
            f"Naive time {x!r} rejected: times must be timezone-aware, e.g. '2024-01-01T00:00Z'."
        )
    return ts.tz_convert("UTC")


def split_range(
    start: TimeLike, end: TimeLike, max_span: pd.Timedelta | None
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Split ``[start, end)`` into contiguous half-open chunks no longer than ``max_span``.

    Parameters
    ----------
    start, end : time-like
        Timezone-aware bounds, ``start <= end``.
    max_span : pandas.Timedelta or None
        Maximum chunk length. ``None`` returns a single chunk.

    Returns
    -------
    list of (pandas.Timestamp, pandas.Timestamp)
        Chunks in order; each chunk's end equals the next chunk's start, the first starts at
        ``start`` and the last ends at ``end``. Empty if ``start == end``.

    Raises
    ------
    ValueError
        If inputs are naive, ``end < start`` or ``max_span`` is not positive.
    """
    s, e = to_utc(start), to_utc(end)
    if e < s:
        raise ValueError(f"end ({e}) is before start ({s}).")
    if s == e:
        return []
    if max_span is None:
        return [(s, e)]
    span = pd.Timedelta(max_span)
    if span <= pd.Timedelta(0):
        raise ValueError(f"max_span must be positive, got {max_span!r}.")
    chunks = []
    cur = s
    while cur < e:
        nxt = min(cur + span, e)
        chunks.append((cur, nxt))
        cur = nxt
    return chunks


def regular_grid(start: TimeLike, end: TimeLike, freq: str | pd.Timedelta) -> pd.DatetimeIndex:
    """Regular UTC grid over ``[start, end)``.

    Grid points are multiples of ``freq`` since the Unix epoch, so grids built over different
    windows line up. The first point is ``start`` rounded up to a multiple of ``freq``.

    Parameters
    ----------
    start, end : time-like
        Timezone-aware bounds.
    freq : str or pandas.Timedelta
        Fixed grid spacing, e.g. ``"1h"`` or ``"15min"``.

    Returns
    -------
    pandas.DatetimeIndex
        UTC index with ``freq`` set. Empty if no grid point falls in the range.
    """
    s, e = to_utc(start), to_utc(end)
    step = pd.Timedelta(freq)
    if step <= pd.Timedelta(0):
        raise ValueError(f"freq must be positive, got {freq!r}.")
    first = s.ceil(step)
    return pd.date_range(first, e, freq=step, inclusive="left", name="time")
