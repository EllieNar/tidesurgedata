"""Canonical SI units and conversions into them.

Every series produced by an adapter is expressed in one of the canonical unit strings in
:data:`CANONICAL`. Adapters convert provider units with :func:`convert` before returning data.
Vectors are stored as components (``u``, ``v``), never as speed and direction.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

__all__ = ["CANONICAL", "convert", "is_canonical"]

CANONICAL: frozenset[str] = frozenset(
    {
        "m",  # length: water level, stage
        "m s-1",  # velocity: wind and current components
        "m3 s-1",  # volume flux: river discharge
        "Pa",  # pressure
        "K",  # temperature
        "kg m-2 s-1",  # mass flux: precipitation rate
        "W m-2",  # energy flux: radiation
        "1",  # dimensionless
    }
)

_FT = 0.3048
_KNOT = 1852.0 / 3600.0


def _scale(factor: float) -> Callable[[np.ndarray], np.ndarray]:
    return lambda x: x * factor


_CONVERSIONS: dict[tuple[str, str], Callable[[np.ndarray], np.ndarray]] = {
    ("ft", "m"): _scale(_FT),
    ("cm", "m"): _scale(0.01),
    ("mm", "m"): _scale(0.001),
    ("ft3 s-1", "m3 s-1"): _scale(_FT**3),
    ("hPa", "Pa"): _scale(100.0),
    ("mbar", "Pa"): _scale(100.0),
    ("kPa", "Pa"): _scale(1000.0),
    ("knot", "m s-1"): _scale(_KNOT),
    ("degC", "K"): lambda x: x + 273.15,
    ("degF", "K"): lambda x: (x - 32.0) * 5.0 / 9.0 + 273.15,
}


def is_canonical(unit: str) -> bool:
    """Return True if ``unit`` is one of the canonical unit strings."""
    return unit in CANONICAL


def convert[T: (float, np.ndarray, pd.Series)](values: T, from_unit: str, to_unit: str) -> T:
    """Convert ``values`` from ``from_unit`` to the canonical ``to_unit``.

    Parameters
    ----------
    values : float, numpy.ndarray or pandas.Series
        Values to convert. Series keep their index and name; the result is ``float64``.
    from_unit : str
        Provider unit, e.g. ``"ft"``, ``"hPa"``, ``"degC"``.
    to_unit : str
        Canonical target unit, e.g. ``"m"``, ``"Pa"``, ``"K"``.

    Returns
    -------
    float, numpy.ndarray or pandas.Series
        Converted values, same container type as ``values``.

    Raises
    ------
    ValueError
        If the conversion is not supported.
    """
    if from_unit == to_unit:
        func: Callable[[np.ndarray], np.ndarray] = lambda x: x  # noqa: E731
    else:
        try:
            func = _CONVERSIONS[(from_unit, to_unit)]
        except KeyError:
            supported = ", ".join(f"{a}->{b}" for a, b in _CONVERSIONS)
            raise ValueError(
                f"Unsupported unit conversion {from_unit!r} -> {to_unit!r}. Supported: {supported}"
            ) from None

    if isinstance(values, pd.Series):
        return func(values.astype("float64"))
    if isinstance(values, np.ndarray):
        return func(values.astype("float64"))
    return float(func(np.float64(values)))
