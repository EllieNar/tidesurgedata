# tidesurgedata

**One consistent way to get tide gauge, river and meteorological data from many providers** — and
to assemble that data into training and forecast datasets for predictive models.

`tidesurgedata` is an open, model-agnostic Python package for the ocean and coastal community. Every
provider adapter returns data under the same contract: timezone-aware UTC timestamps, SI units,
explicit datums and sampling conventions, and a provenance record for every fetch (see
[ADR 0002](docs/design/0002-data-contract.md)).

The package does not depend on any model. Its frames are plain `pandas` objects, so you can use them
with RTide, with other models, or on their own.

> **Status: pre-alpha scaffold.** The data contracts, core utilities and synthetic ("fake") sources
> are implemented. Real provider adapters, caching, resampling and frame assembly are being built.

## Supported providers

| Provider | Module | Data | Status |
|---|---|---|---|
| NOAA CO-OPS | `sources.noaa_coops` | Water level, wind, air pressure | planned |
| USGS Water Data APIs | `sources.usgs` | River discharge, stage | planned |
| Environment Agency Tide Gauges | `sources.ea_tide` | UK National Tide Gauge Network water level | planned |
| Environment Agency rivers | `sources.ea_rivers` | River flow and level (real time + Hydrology archive) | planned |
| GESLA | `sources.gesla` | Historical high-frequency sea level | planned |
| dynamical.org | `sources.dynamical` | Weather analyses and forecasts (GFS, GEFS, HRRR, ECMWF IFS ENS, AIFS) | planned |
| Synthetic | `sources.fake` | Deterministic tide, river and pressure data for testing | available |

## Installation

```bash
pip install tidesurgedata               # core: numpy, pandas, requests, pyarrow
pip install "tidesurgedata[usgs]"       # USGS adapter (dataretrieval)
pip install "tidesurgedata[met]"        # dynamical.org weather data (xarray, zarr, icechunk, pystac)
pip install "tidesurgedata[xarray]"     # NetCDF / xarray export
pip install "tidesurgedata[all]"        # everything above
```

Until the first release, install from a clone with `pip install -e ".[dev]"`.

## Usage (Dummy Data)
```
import pandas as pd
import tidesurgedata as tsd
from tidesurgedata.sources.fake import FakeMet, FakeRiver, FakeTideGauge

met, river = FakeMet(), FakeRiver()
gauge = FakeTideGauge(pressure=met, river=river)

# Fetch data plus its provenance record
s, record = gauge.fetch_with_record("2024-01-01T00:00Z", "2024-01-08T00:00Z")
print(s.head(), record.quality, record.meta.units)

# Forecasts: latest initialisation available by the issue time
fc = met.fetch_forecast("2024-01-05T12:00Z", pd.Timedelta("48h"))
print(fc.init_time, fc.values.columns.tolist())

# Recipe logic that already works
recipe = tsd.Recipe(
    target=gauge,
    drivers=(
        tsd.Driver("discharge", river, lags_hours=(-24, -12)),
        tsd.Driver("pressure", met, lags_hours=(0,), forecast=met),
    ),
    target_column="observations",
)
print(recipe.feature_columns)   # ['discharge_lag-24h', 'discharge_lag-12h', 'pressure_lag0h']
print(recipe.max_lead_time)     # 0 days 11:00:00
print(recipe.to_json())

recipe.training_frame("2024-01-01T00:00Z", "2024-01-08T00:00Z")  # NotImplementedError: BL-12

```

## Usage (planned API)

The snippet below illustrates the intended API. Only the fake sources work today.

```python
import tidesurgedata as tsd
from tidesurgedata.sources.noaa_coops import NOAACoops
from tidesurgedata.sources.usgs import USGS
from tidesurgedata.sources.dynamical import Dynamical

recipe = tsd.Recipe(
    target=NOAACoops("8518750", product="water_level", datum="MSL"),
    drivers=(
        tsd.Driver("discharge", USGS("01376500"), lags_hours=(-24, -12)),
        tsd.Driver(
            "pressure",
            Dynamical("noaa-gfs-analysis", "pressure_surface"),
            lags_hours=(0,),
            forecast=Dynamical("noaa-gefs-forecast", "pressure_surface"),
        ),
    ),
    freq="1h",
)

train = recipe.training_frame("2020-01-01T00:00Z", "2024-01-01T00:00Z")
future = recipe.forecast_frame(issued="2024-06-01T00:00Z", horizon_hours=48)
recipe.to_json()  # reproducible, shareable dataset definition
```

## Data licences and attribution

Each provider publishes data under its own terms, and some require specific attribution text. Every
series carries its licence and exact attribution string in `SeriesMeta.licence` and
`SeriesMeta.attribution`, and these travel with exported data. **You are responsible for complying
with each provider's terms when you use or redistribute data obtained through this package.**
Examples: Environment Agency data is under the Open Government Licence with required attribution;
dynamical.org data is CC BY 4.0 (plus ECMWF Terms of Use for ECMWF datasets); GESLA licences vary by
original provider.

## Independence from models

`tidesurgedata` is a standalone package. It contains no model code and depends on no model package.
Compatibility with RTide is checked by an optional CI job through RTide's public API only (see
[ADR 0001](docs/design/0001-standalone-package.md)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [backlog](docs/dev/backlog.md).

## Licence

MIT — see [LICENSE](LICENSE).
