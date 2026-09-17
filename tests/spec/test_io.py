"""Spec tests for io.to_xarray / to_netcdf / to_csv (BL-18)."""

import json

import pytest

from tidesurgedata import io

BL18 = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="BL-18")
WINDOW = ("2024-01-01T00:00Z", "2024-01-02T00:00Z")


@BL18
def test_to_xarray_attributes_and_provenance(fake_river):
    pytest.importorskip("xarray")
    series, record = fake_river.fetch_with_record(*WINDOW)
    ds = io.to_xarray(series, [record])
    var = ds["discharge"]
    assert var.attrs["units"] == "m3 s-1"
    assert "long_name" in var.attrs
    assert "time" in ds.coords
    assert ds.attrs["Conventions"].startswith("CF-")
    assert "synthetic" in ds.attrs["licence"]
    assert "attribution" in ds.attrs
    provenance = json.loads(ds.attrs["provenance"])
    assert provenance == [record.to_dict()]


@BL18
def test_to_netcdf(fake_river, tmp_path):
    pytest.importorskip("xarray")
    pytest.importorskip("netCDF4")
    series, record = fake_river.fetch_with_record(*WINDOW)
    path = io.to_netcdf(series, [record], tmp_path / "river.nc")
    assert path.exists()


@BL18
def test_to_csv_with_sidecar(fake_river, tmp_path):
    series, record = fake_river.fetch_with_record(*WINDOW)
    path = io.to_csv(series, [record], tmp_path / "river.csv")
    assert path == tmp_path / "river.csv" and path.exists()
    assert path.read_text().splitlines()[0].split(",")[:2] == ["time", "discharge"]
    sidecar = json.loads((tmp_path / "river.provenance.json").read_text())
    assert sidecar["records"] == [record.to_dict()]
    assert sidecar["licence"] == ["synthetic"]
