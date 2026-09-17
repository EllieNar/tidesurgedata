"""NOAA CO-OPS adapter (BL-05). STUB.

Provider facts
--------------
- NOAA Center for Operational Oceanographic Products and Services (CO-OPS) Data API
  (``https://api.tidesandcurrents.noaa.gov/api/prod/datagetter``).
- Per-request limits depend on the interval: 1-minute data 4 days, 6-minute data 1 month,
  hourly data 1 year. Chunk accordingly.
- A datum is mandatory for water-level products.
- Water level is preliminary until verified (monthly).
- Request times in GMT (``time_zone=gmt``).
- Many stations also serve wind, air pressure and air temperature. Products in scope: water
  level, predictions (reference only), wind, air pressure.
- US Government data; attribution to NOAA CO-OPS.

Implementation checklist
------------------------
- [ ] ``metadata()``: station name and location from the CO-OPS Metadata API; canonical units
      (request ``units=metric``; wind -> ``u``/``v`` components in ``m s-1``; pressure ``hPa`` ->
      ``Pa``); datum set for water level; sampling convention per product.
- [ ] ``max_request`` by ``interval`` (override as a property if it depends on the instance).
- [ ] ``_fetch()``: one request per chunk; parse flags; quality ``"verified"`` or
      ``"preliminary"`` from the product/data flags; missing values as NaN.
- [ ] ``find_stations()`` using the Metadata API, filtered by distance and product.
- [ ] Contract tests in ``tests/sources/test_noaa_coops.py`` with a recorded cassette; remove the
      ``xfail``/``skip`` markers.
- [ ] Live smoke test passes; licence and attribution recorded; CHANGELOG entry.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tidesurgedata.meta import Quality, SeriesMeta
from tidesurgedata.sources.base import BaseSource
from tidesurgedata.sources.registry import register_source

__all__ = ["NOAACoops"]


@register_source("noaa_coops")
@dataclass(frozen=True)
class NOAACoops(BaseSource):
    """NOAA CO-OPS station data.

    Parameters
    ----------
    station_id : str
        CO-OPS station identifier, e.g. ``"8518750"`` (The Battery, NY).
    product : str
        CO-OPS product, e.g. ``"water_level"``, ``"predictions"``, ``"wind"``, ``"air_pressure"``.
    datum : str
        Vertical datum for water-level products, e.g. ``"MSL"``, ``"MLLW"``, ``"NAVD"``.
    interval : str, optional
        Sampling interval (e.g. ``"6"``, ``"h"``); ``None`` uses the product default.
    """

    station_id: str
    product: str = "water_level"
    datum: str = "MSL"
    interval: str | None = None

    # TODO(BL-05): confirm; max_request depends on interval (1-min: 4 days, 6-min: 1 month,
    # hourly: 1 year) and latency is not stated by the provider facts.

    def metadata(self) -> SeriesMeta:
        raise NotImplementedError("BL-05")

    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        raise NotImplementedError("BL-05")

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        raise NotImplementedError("BL-05")
