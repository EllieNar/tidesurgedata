"""Local parquet cache for fetched series (BL-04)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tidesurgedata.meta import FetchRecord
from tidesurgedata.sources.base import BaseSource

__all__ = ["CACHE_ENV_VAR", "DEFAULT_PRELIMINARY_TTL", "Cache", "default_cache_root"]

#: Environment variable overriding the cache root directory.
CACHE_ENV_VAR = "TIDESURGEDATA_CACHE"

#: Default age after which non-verified chunks expire.
DEFAULT_PRELIMINARY_TTL = pd.Timedelta("24h")


def default_cache_root() -> Path:
    """Cache root: ``$TIDESURGEDATA_CACHE`` if set, else ``~/.cache/tidesurgedata``."""
    raise NotImplementedError("BL-04: default_cache_root")


class Cache:
    """Parquet cache chunked by source-defined period.

    Key includes source, station, variable, params hash and adapter_version; preliminary chunks
    expire (default 24 h); atomic writes (temp file + rename); root from TIDESURGEDATA_CACHE or
    ~/.cache/tidesurgedata. BaseSource.fetch gains a `cache=` option.

    Parameters
    ----------
    root : str or pathlib.Path, optional
        Cache directory; default :func:`default_cache_root`.
    preliminary_ttl : pandas.Timedelta
        Age after which chunks whose quality is not ``"verified"`` are treated as a miss.

    Notes
    -----
    - Chunk period: ``source.max_request`` if set, else 30 days; chunk boundaries are aligned to
      multiples of the period since the epoch so that overlapping requests share chunks.
    - Key: ``source.registry_name``, ``meta.station_id``, ``meta.variable``, a stable hash of
      ``source.to_spec()["params"]`` and ``source.adapter_version``. Changing any of these is a
      miss.
    - Each chunk stores the series and its :class:`~tidesurgedata.meta.FetchRecord` (as JSON
      metadata). A request is served from cache only if every chunk it overlaps is present and
      not expired; otherwise missing/expired chunks are fetched and written.
    - Writes go to a temporary file in the same directory followed by ``os.replace``, so readers
      never see partial files.
    - Implementation adds ``cache: Cache | None = None`` to ``BaseSource.fetch`` and
      ``fetch_with_record``.
    """

    def __init__(
        self,
        root: str | Path | None = None,
        preliminary_ttl: pd.Timedelta = DEFAULT_PRELIMINARY_TTL,
    ) -> None:
        raise NotImplementedError("BL-04: Cache")

    def get(
        self, source: BaseSource, start: pd.Timestamp, end: pd.Timestamp
    ) -> tuple[pd.Series, FetchRecord] | None:
        """Return the cached series and record over ``[start, end)``, or ``None`` on a miss."""
        raise NotImplementedError("BL-04: Cache.get")

    def put(self, source: BaseSource, series: pd.Series, record: FetchRecord) -> None:
        """Store ``series`` (covering ``[record.start, record.end)``) as aligned chunks."""
        raise NotImplementedError("BL-04: Cache.put")

    def clear(self, source: BaseSource | None = None) -> None:
        """Remove all cached chunks, or only those of ``source``."""
        raise NotImplementedError("BL-04: Cache.clear")
