"""Environment Agency rivers adapter (BL-08). STUB.

Provider facts
--------------
- Environment Agency flood-monitoring API (near real time; 15-minute readings; transfer
  frequency varies by site), root ``https://environment.data.gov.uk/flood-monitoring``.
- Hydrology API (quality-checked archive; GUID-based station identifiers), root
  ``https://environment.data.gov.uk/hydrology``.
- Map between the two identifier schemes and mark quality accordingly (archive:
  ``"verified"``; real time: ``"preliminary"``; both in one request: ``"mixed"``).
- Open Government Licence.
- Required attribution: "This uses Environment Agency flood and river level data from the
  real-time data API (Beta)".

Implementation checklist
------------------------
- [ ] Identifier mapping between flood-monitoring references and Hydrology GUIDs.
- [ ] ``metadata()``: ``flow`` -> ``discharge`` in ``m3 s-1``; ``level`` -> ``stage`` in ``m``
      with datum; sampling convention confirmed; licence ``"OGL-UK-3.0"``; exact attribution.
- [ ] ``_fetch()``: archive for the quality-checked period, real time after it; confirm request
      limits (``max_request``) and latency.
- [ ] ``find_stations()`` via ``/id/stations?parameter=flow&lat=&long=&dist=``.
- [ ] Cassettes for both APIs; contract tests; remove markers; CHANGELOG entry.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tidesurgedata.meta import Quality, SeriesMeta
from tidesurgedata.sources.base import BaseSource
from tidesurgedata.sources.registry import register_source

__all__ = ["EARiver"]


@register_source("ea_rivers")
@dataclass(frozen=True)
class EARiver(BaseSource):
    """Environment Agency river gauging station.

    Parameters
    ----------
    station_id : str
        Flood-monitoring station reference or Hydrology API GUID.
    parameter : {"flow", "level"}
        Variable to retrieve.
    """

    station_id: str
    parameter: str = "flow"

    # TODO(BL-08): confirm max_request and latency.

    def metadata(self) -> SeriesMeta:
        raise NotImplementedError("BL-08")

    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        raise NotImplementedError("BL-08")

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        raise NotImplementedError("BL-08")
