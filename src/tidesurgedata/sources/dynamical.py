"""dynamical.org weather data adapter (BL-15 analysis, BL-16 forecasts/ensembles). STUB.

Provider facts
--------------
- dynamical.org cloud-optimised weather data (GFS, GEFS, HRRR, ECMWF IFS ENS, AIFS) stored as
  Icechunk Zarr.
- Datasets are discovered through the STAC catalog ``https://stac.dynamical.org/catalog.json`` and
  opened with xarray (install the ``met`` extra: ``pip install "tidesurgedata[met]"``).
- Forecast datasets have ``init_time``, ``lead_time`` and (for ensembles) member dimensions.
- Licence CC BY 4.0, plus the ECMWF Terms of Use for ECMWF datasets.
- Archive start dates differ per dataset.

Implementation checklist
------------------------
- [ ] Import ``xarray``, ``zarr``, ``icechunk`` and ``pystac`` inside functions; raise
      ``ImportError`` naming the ``met`` extra.
- [ ] BL-15 ``metadata()``/``_fetch()``: analysis at a point (``method="nearest"``, later
      ``"linear"``); canonical units and variable names; vectors as ``u``/``v``; sampling
      convention from dataset attributes; licence and attribution per dataset.
- [ ] BL-15: confirm ``max_request`` and ``latency`` per dataset; archive start handling.
- [ ] BL-16 ``init_times()`` and ``fetch_forecast()``: latest ``init_time`` available by
      ``issued - latency``; ``valid_time = init_time + lead_time``; members as string labels
      (deterministic: ``"control"``).
- [ ] Small recorded fixture; contract and forecast contract tests; remove markers; CHANGELOG.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from tidesurgedata.meta import Quality, SeriesMeta
from tidesurgedata.sources.base import Forecast, GriddedSource
from tidesurgedata.sources.registry import register_source
from tidesurgedata.timeutil import TimeLike

__all__ = ["Dynamical"]


@register_source("dynamical")
@dataclass(frozen=True)
class Dynamical(GriddedSource):
    """dynamical.org dataset sampled at a point; also a ``ForecastSource`` for forecast datasets.

    Parameters
    ----------
    dataset : str
        dynamical.org dataset identifier from the STAC catalog.
    variable : str
        Canonical variable name, e.g. ``"pressure_surface"``, ``"wind_u_10m"``.
    lat, lon : float, optional
        Sample location; ``None`` until located (``Recipe.resolved`` uses the target location).
    method : {"nearest", "linear"}
        Spatial sampling method.
    """

    dataset: str
    variable: str
    lat: float | None = None
    lon: float | None = None
    method: str = "nearest"

    # TODO(BL-15): confirm max_request and latency per dataset.

    def metadata(self) -> SeriesMeta:
        raise NotImplementedError("BL-15")

    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        raise NotImplementedError("BL-15")

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        raise NotImplementedError("BL-15")

    def init_times(self, start: TimeLike, end: TimeLike) -> pd.DatetimeIndex:
        """Initialisation times of the forecast dataset in ``[start, end)``."""
        raise NotImplementedError("BL-16")

    def fetch_forecast(
        self, issued: TimeLike, horizon: pd.Timedelta, members: Sequence[str] | None = None
    ) -> Forecast:
        """Use the latest initialisation time available by `issued` (respecting latency).
        Never use data initialised after that.

        Returns a :class:`~tidesurgedata.sources.base.Forecast` with valid times from the
        initialisation time to ``issued + horizon`` and one column per requested member
        (``"control"`` for deterministic datasets); validated with
        :func:`tidesurgedata.contract.validate_forecast`.
        """
        raise NotImplementedError("BL-16")
