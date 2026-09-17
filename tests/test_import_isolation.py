import subprocess
import sys

HEAVY = ["xarray", "zarr", "icechunk", "pystac", "dataretrieval", "tensorflow", "rtide"]

MODULES = [
    "tidesurgedata",
    "tidesurgedata.meta",
    "tidesurgedata.contract",
    "tidesurgedata.units",
    "tidesurgedata.timeutil",
    "tidesurgedata.cache",
    "tidesurgedata.discovery",
    "tidesurgedata.io",
    "tidesurgedata.align",
    "tidesurgedata.recipe",
    "tidesurgedata.hindcast",
    "tidesurgedata.sources",
    "tidesurgedata.sources.base",
    "tidesurgedata.sources.registry",
    "tidesurgedata.sources.fake",
    "tidesurgedata.sources.noaa_coops",
    "tidesurgedata.sources.usgs",
    "tidesurgedata.sources.ea_tide",
    "tidesurgedata.sources.ea_rivers",
    "tidesurgedata.sources.gesla",
    "tidesurgedata.sources.dynamical",
]


def test_import_does_not_load_heavy_dependencies():
    code = f"""
import importlib, sys
for name in {MODULES!r}:
    importlib.import_module(name)
import tidesurgedata
tidesurgedata.registered_sources()
heavy = {HEAVY!r}
loaded = sorted(m for m in sys.modules if m.split(".")[0] in heavy)
print(",".join(loaded))
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "", f"heavy modules imported: {result.stdout.strip()}"
