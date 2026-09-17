"""USGS adapter (BL-06). STUB.

Provider facts
--------------
- USGS Water Data APIs, accessed through ``dataretrieval.waterdata`` (install the ``usgs`` extra:
  ``pip install "tidesurgedata[usgs]"``; ``dataretrieval>=1.1.0``).
- **Do not use the legacy ``nwis`` module / WaterServices**: decommissioning is scheduled for
  Q1 2027.
- API key via the environment variable ``API_USGS_PAT`` (never stored in code, specs, recipes,
  records or cassettes).
- Convert ft³/s -> m³/s (discharge) and ft -> m (stage).

Implementation checklist
------------------------
- [ ] Import ``dataretrieval`` inside functions; raise ``ImportError`` naming the ``usgs`` extra.
- [ ] ``metadata()``: site name, location, parameter mapping (``discharge`` -> ``m3 s-1``,
      ``stage`` -> ``m`` with datum).
- [ ] ``_fetch()``: time-series values for ``[start, end)``; approval status -> quality
      (approved -> ``"verified"``, provisional -> ``"preliminary"``); units converted.
- [ ] Confirm per-request limits (``max_request``) and typical latency.
- [ ] ``find_stations()`` via ``waterdata`` monitoring-location queries.
- [ ] Cassette with API key filtered; contract tests; remove markers; CHANGELOG entry.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tidesurgedata.meta import Quality, SeriesMeta
from tidesurgedata.sources.base import BaseSource
from tidesurgedata.sources.registry import register_source

__all__ = ["USGS"]


@register_source("usgs")
@dataclass(frozen=True)
class USGS(BaseSource):
    """USGS monitoring-location time series.

    Parameters
    ----------
    site_id : str
        USGS site number, e.g. ``"01376500"``.
    parameter : {"discharge", "stage"}
        Variable to retrieve.
    """

    site_id: str
    parameter: str = "discharge"

    # TODO(BL-06): confirm max_request and latency.

    def metadata(self) -> SeriesMeta:
        raise NotImplementedError("BL-06")

    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        raise NotImplementedError("BL-06")

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        raise NotImplementedError("BL-06")
