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
# See https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import requests

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

    def _units(self) -> str:
        """determine canonical units for the selected NOAA product"""
        units = {
            "water_level": "m",
            "predictions": "m",
            "wind": "m s-1",
            "air_pressure": "Pa",
        }

        try:
            return units[self.product]
        except KeyError:
            raise ValueError(f"Unsupported NOAA CO-OPS product: {self.product!r}") from None

    def _window(self) -> pd.Timedelta:
        """Return the averaging window for the selected NOAA product."""
        windows = {
            "water_level": pd.Timedelta("3min"),
        }

        try:
            return windows[self.product]
        except KeyError:
            raise ValueError(
                f"Sampling window not defined for NOAA CO-OPS product: {self.product!r}"
            ) from None
    
    # Describe the data
    def metadata(self) -> SeriesMeta:
        # Somehow obtain station info
        metadata_url = (
            "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/"
            f"stations/{self.station_id}.json"
            )

        response = requests.get(metadata_url)
        response.raise_for_status()

        raw = response.json()
        station = raw["stations"][0]


        return SeriesMeta(
            source=self.registry_name,
            station_id=self.station_id,
            variable=self.product,
            lat=station["lat"],
            lon=station["lng"],
            units=self._units(),
            datum=self.datum if self.product in {"water_level", "predictions"} else None,
            sampling="window_mean",
            window=self._window(),
            label="centre",
            licence="US Government public domain",  # TODO(BL-05): confirm canonical wording
            attribution="NOAA CO-OPS",
            url=station["self"],
            name=station["name"],
        )

    # Retrieve the data from the API. Does the following:
        # Construct NOAA parameters
        # Make HTTP request
        # Read JSON
        # Extract observations
        # Convert time streings -> UTC timestamps
        # Convert values -> numeric
        # Deal with missing values
        # Interpret NOAA quality
        # Return Series, Quality, request
    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        raise NotImplementedError("BL-05")

    # Discover stations
    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        raise NotImplementedError("BL-05")
