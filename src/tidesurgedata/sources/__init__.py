"""Data source interfaces, registry and adapters.

Adapter modules (``fake``, ``noaa_coops``, ``usgs``, ``ea_tide``, ``ea_rivers``, ``gesla``,
``dynamical``) are imported on demand, e.g. ``from tidesurgedata.sources.fake import FakeRiver``.
"""

from tidesurgedata.sources.base import (
    BaseSource,
    Forecast,
    ForecastSource,
    GriddedSource,
    Source,
)
from tidesurgedata.sources.registry import register_source, registered_sources, source_from_spec

__all__ = [
    "BaseSource",
    "Forecast",
    "ForecastSource",
    "GriddedSource",
    "Source",
    "register_source",
    "registered_sources",
    "source_from_spec",
]
