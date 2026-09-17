import dataclasses

import pytest

from tidesurgedata.sources.base import BaseSource
from tidesurgedata.sources.registry import (
    _REGISTRY,
    register_source,
    registered_sources,
    source_from_spec,
)

STUB_ADAPTERS = ["noaa_coops", "usgs", "ea_tide", "ea_rivers", "gesla", "dynamical"]
FAKES = ["fake_tide_gauge", "fake_river", "fake_met"]


@dataclasses.dataclass(frozen=True)
class Dummy(BaseSource):
    x: int = 1

    def metadata(self):
        raise NotImplementedError

    def _fetch(self, start, end):
        raise NotImplementedError


@pytest.fixture
def registered_dummy():
    register_source("test_dummy")(Dummy)
    yield Dummy
    _REGISTRY.pop("test_dummy", None)


def test_register_sets_name(registered_dummy):
    assert registered_dummy.registry_name == "test_dummy"
    assert registered_sources()["test_dummy"] is registered_dummy


def test_duplicate_registration_raises(registered_dummy):
    with pytest.raises(ValueError, match="already registered"):
        register_source("test_dummy")(Dummy)


def test_duplicate_builtin_name_raises():
    registered_sources()
    with pytest.raises(ValueError, match="already registered"):
        register_source("noaa_coops")(Dummy)


def test_non_source_rejected():
    with pytest.raises(TypeError):
        register_source("test_bad")(object)


def test_unknown_type_lists_names():
    with pytest.raises(KeyError) as info:
        source_from_spec({"type": "nope", "params": {}})
    message = str(info.value)
    for name in STUB_ADAPTERS + FAKES:
        assert name in message


@pytest.mark.parametrize("name", STUB_ADAPTERS + FAKES)
def test_all_adapters_registered(name):
    sources = registered_sources()
    assert name in sources
    assert sources[name].registry_name == name


def test_from_spec_builds(registered_dummy):
    assert source_from_spec({"type": "test_dummy", "params": {"x": 3}}) == Dummy(x=3)


def test_stub_adapters_serialise():
    from tidesurgedata.sources.dynamical import Dynamical
    from tidesurgedata.sources.noaa_coops import NOAACoops

    for source in (NOAACoops("8518750"), Dynamical("noaa-gfs-analysis", "pressure_surface")):
        assert source_from_spec(source.to_spec()) == source
