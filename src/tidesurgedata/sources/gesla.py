"""GESLA adapter (BL-09). STUB — blocked on the GESLA 4.1 API specification.

Provider facts
--------------
- GESLA (Global Extreme Sea Level Analysis) historical high-frequency sea level.
- Historical only; not real time.
- **Obtain the 4.1 API specification from Thomas before implementing.**
- Licences vary by original data provider and must be carried per station into
  ``SeriesMeta.licence`` (and attribution into ``SeriesMeta.attribution``).
- Fallback: read local GESLA files.

Implementation checklist
------------------------
- [ ] Obtain the 4.1 API specification.
- [ ] ``metadata()``: per-station licence, attribution, datum, sampling from GESLA headers.
- [ ] ``_fetch()``: API retrieval, or local files as fallback; GESLA quality/use flags -> NaN and
      quality.
- [ ] ``find_stations()`` from the station list.
- [ ] Cassette or small fixture file; contract tests; remove markers; CHANGELOG entry.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tidesurgedata.meta import Quality, SeriesMeta
from tidesurgedata.sources.base import BaseSource
from tidesurgedata.sources.registry import register_source

__all__ = ["GESLA"]


@register_source("gesla")
@dataclass(frozen=True)
class GESLA(BaseSource):
    """GESLA station record.

    Parameters
    ----------
    station_id : str
        GESLA station/file identifier.
    version : str
        GESLA dataset version.
    """

    station_id: str
    version: str = "4.1"

    # TODO(BL-09): confirm max_request; latency is not meaningful for a historical archive.

    def metadata(self) -> SeriesMeta:
        raise NotImplementedError("BL-09")

    def _fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Series, Quality, dict]:
        raise NotImplementedError("BL-09")

    @classmethod
    def find_stations(
        cls, lat: float, lon: float, radius_km: float, variable: str | None = None
    ) -> list[SeriesMeta]:
        raise NotImplementedError("BL-09")
