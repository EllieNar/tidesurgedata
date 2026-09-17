"""Environment Agency tide gauge adapter (BL-07). STUB.

Provider facts
--------------
- Environment Agency Tide Gauge API, part of the flood-monitoring API, root
  ``https://environment.data.gov.uk/flood-monitoring``.
- UK National Tide Gauge Network, 44 gauges.
- Values are means over each 15-minute window, relative to local datum (``m``) and Ordnance
  Datum Newlyn (``mAOD``).
- Times are UTC. Typical latency 15-30 minutes.
- Open Government Licence; no registration.
- Required attribution: "this uses Environment Agency tide gauge data from the real-time data
  API (Beta)".
- **Confirm the window-mean label convention** (start, centre or end of the 15-minute window) and
  set ``SeriesMeta.label`` accordingly; record the evidence in the PR.

Implementation checklist
------------------------
- [ ] ``metadata()``: station name/location from the stations endpoint; ``units="m"``;
      ``datum`` ``"local"`` or ``"ODN"``; ``sampling="window_mean"``,
      ``window=15 min``, confirmed ``label``; licence ``"OGL-UK-3.0"``; exact attribution.
- [ ] ``_fetch()``: readings for the measure matching ``datum``; confirm request limits and set
      ``max_request``; quality mapping.
- [ ] ``find_stations()`` using ``/id/stations?type=TideGauge&lat=&long=&dist=``.
- [ ] Cassette; contract tests; remove markers; CHANGELOG entry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pandas as pd

from tidesurgedata.meta import Quality, SeriesMeta
from tidesurgedata.sources.base import BaseSource
from tidesurgedata.sources.registry import register_source

__all__ = ["EATideGauge"]


@register_source("ea_tide")
@dataclass(frozen=True)
class EATideGauge(BaseSource):
    """Environment Agency National Tide Gauge Network station.

    Parameters
    ----------
    station_id : str
        Flood-monitoring station reference, e.g. ``"E72639"``.
    datum : {"local", "ODN"}
        ``"local"`` for the local datum (``m``), ``"ODN"`` for Ordnance Datum Newlyn (``mAOD``).
    """

    station_id: str
    datum: str = "local"

    latency: ClassVar[pd.Timedelta] = pd.Timedelta("30min")
    # TODO(BL-07): confirm max_request.

    def metadata(self) -> SeriesMeta:
        raise NotImplementedError("BL-07")

    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        raise NotImplementedError("BL-07")

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        raise NotImplementedError("BL-07")
