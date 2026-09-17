"""tidesurgedata: consistent tide gauge, river and meteorological data from many providers.

Conventional import::

    import tidesurgedata as tsd
"""

from tidesurgedata._version import __version__
from tidesurgedata.align import lag_column_name
from tidesurgedata.contract import (
    ContractError,
    validate_forecast,
    validate_frame,
    validate_series,
)
from tidesurgedata.discovery import find_stations
from tidesurgedata.hindcast import hindcast_frames
from tidesurgedata.meta import FetchRecord, SeriesMeta
from tidesurgedata.recipe import Driver, Recipe
from tidesurgedata.sources import (
    BaseSource,
    Forecast,
    ForecastSource,
    GriddedSource,
    Source,
    register_source,
    registered_sources,
    source_from_spec,
)

__all__ = [
    "BaseSource",
    "ContractError",
    "Driver",
    "FetchRecord",
    "Forecast",
    "ForecastSource",
    "GriddedSource",
    "Recipe",
    "SeriesMeta",
    "Source",
    "__version__",
    "find_stations",
    "hindcast_frames",
    "lag_column_name",
    "register_source",
    "registered_sources",
    "source_from_spec",
    "validate_forecast",
    "validate_frame",
    "validate_series",
]
