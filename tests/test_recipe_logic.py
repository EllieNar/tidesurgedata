import dataclasses
import json

import pandas as pd
import pytest

from tidesurgedata import Driver, Recipe, lag_column_name
from tidesurgedata.sources.dynamical import Dynamical
from tidesurgedata.sources.fake import FakeMet, FakeRiver, FakeTideGauge


@pytest.mark.parametrize(
    ("lag", "expected"),
    [
        (-24, "discharge_lag-24h"),
        (-24.0, "discharge_lag-24h"),
        (0, "discharge_lag0h"),
        (-0.0, "discharge_lag0h"),
        (-0.25, "discharge_lag-0.25h"),
        (6, "discharge_lag6h"),
        (0.1, "discharge_lag0.1h"),
        (-1.5, "discharge_lag-1.5h"),
        (-168, "discharge_lag-168h"),
        (1e-5, "discharge_lag0.00001h"),
    ],
)
def test_lag_column_name(lag, expected):
    assert lag_column_name("discharge", lag) == expected


@pytest.mark.parametrize("lag", [float("nan"), float("inf"), float("-inf")])
def test_lag_column_name_rejects_non_finite(lag):
    with pytest.raises(ValueError):
        lag_column_name("discharge", lag)


def test_feature_columns_order(fake_recipe):
    assert fake_recipe.feature_columns == [
        "discharge_lag-24h",
        "discharge_lag-12h",
        "pressure_lag0h",
    ]


def test_target_column_name(fake_recipe):
    assert fake_recipe.target_column_name == "water_level"
    custom = dataclasses.replace(fake_recipe, target_column="observations")
    assert custom.target_column_name == "observations"


def test_target_latlon(fake_recipe):
    assert fake_recipe.target_latlon == (51.5, -3.0)


# --- lead-time rule ---------------------------------------------------------------------------


def test_max_lead_time_fake_recipe(fake_recipe):
    # discharge: min(24, 12) - 1 h latency = 11 h; pressure has a forecast source.
    assert fake_recipe.max_lead_time == pd.Timedelta("11h")


def test_max_lead_time_no_drivers(fake_tide_gauge):
    assert Recipe(target=fake_tide_gauge).max_lead_time is None


def test_max_lead_time_all_forecast(fake_tide_gauge, fake_met):
    recipe = Recipe(
        target=fake_tide_gauge,
        drivers=(Driver("pressure", fake_met, (-6, 0), forecast=fake_met),),
    )
    assert recipe.max_lead_time is None


def test_max_lead_time_without_forecast_uses_latency(fake_tide_gauge, fake_met):
    # FakeMet latency is 4 h: min(-(-6), -0) - 4 h = -4 h
    recipe = Recipe(target=fake_tide_gauge, drivers=(Driver("pressure", fake_met, (-6, 0)),))
    assert recipe.max_lead_time == pd.Timedelta("-4h")


def test_max_lead_time_minimum_over_drivers(fake_tide_gauge, fake_river, fake_met):
    recipe = Recipe(
        target=fake_tide_gauge,
        drivers=(
            Driver("discharge", fake_river, (-48, -36)),  # 36 - 1 = 35 h
            Driver("pressure", fake_met, (-12,)),  # 12 - 4 = 8 h
        ),
    )
    assert recipe.max_lead_time == pd.Timedelta("8h")


def test_max_lead_time_zero_is_allowed(fake_tide_gauge, fake_river):
    recipe = Recipe(target=fake_tide_gauge, drivers=(Driver("discharge", fake_river, (-1,)),))
    assert recipe.max_lead_time == pd.Timedelta(0)


def test_max_lead_time_positive_lag(fake_tide_gauge, fake_river):
    # a lag into the future: min(-(-3), -(2)) - 1 h = -3 h
    recipe = Recipe(target=fake_tide_gauge, drivers=(Driver("discharge", fake_river, (-3, 2)),))
    assert recipe.max_lead_time == pd.Timedelta("-3h")


# --- resolved ---------------------------------------------------------------------------------


def test_resolved_locates_gridded_drivers():
    target = FakeTideGauge(lat=50.0, lon=-4.0)
    met = FakeMet(lat=None, lon=None)
    located = FakeMet(lat=10.0, lon=20.0)
    dyn = Dynamical("noaa-gfs-analysis", "pressure_surface")
    recipe = Recipe(
        target=target,
        drivers=(
            Driver("pressure", met, (0,), forecast=met),
            Driver("pressure_far", located, (0,)),
            Driver("discharge", FakeRiver(), (-1,)),
            Driver("pgfs", dyn, (0,)),
        ),
    )
    resolved = recipe.resolved()
    assert resolved.drivers[0].source == FakeMet(lat=50.0, lon=-4.0)
    assert resolved.drivers[0].forecast == FakeMet(lat=50.0, lon=-4.0)
    assert resolved.drivers[1].source == located
    assert resolved.drivers[2].source == FakeRiver()
    assert (resolved.drivers[3].source.lat, resolved.drivers[3].source.lon) == (50.0, -4.0)
    assert recipe.drivers[0].source.lat is None  # original unchanged


def test_resolved_without_gridded_does_not_need_target_metadata(fake_river):
    from tidesurgedata.sources.noaa_coops import NOAACoops

    recipe = Recipe(target=NOAACoops("8518750"), drivers=(Driver("q", fake_river, (-1,)),))
    assert recipe.resolved() == recipe


# --- serialisation ----------------------------------------------------------------------------


def test_json_round_trip(fake_recipe):
    recipe = dataclasses.replace(fake_recipe, target_column="observations", target_how="mean")
    text = recipe.to_json()
    assert json.loads(text)["schema_version"] == 1
    assert Recipe.from_json(text) == recipe
    assert Recipe.from_dict(recipe.to_dict()) == recipe
    assert Recipe.from_json(text).to_json() == text


def test_json_round_trip_with_stub_adapters():
    from tidesurgedata.sources.ea_rivers import EARiver
    from tidesurgedata.sources.ea_tide import EATideGauge

    recipe = Recipe(
        target=EATideGauge("E72639"),
        drivers=(
            Driver("flow", EARiver("3400TH", parameter="flow"), (-24, -12), how="instant"),
            Driver(
                "pressure",
                Dynamical("noaa-gfs-analysis", "pressure_surface"),
                (0,),
                forecast=Dynamical("noaa-gefs-forecast", "pressure_surface"),
                max_gap=None,
            ),
        ),
        target_column="observations",
    )
    assert Recipe.from_json(recipe.to_json()) == recipe


def test_unsupported_schema_version(fake_recipe):
    d = fake_recipe.to_dict()
    d["schema_version"] = 2
    with pytest.raises(ValueError, match="schema_version"):
        Recipe.from_dict(d)


def test_lags_normalised_to_float_tuple(fake_river):
    driver = Driver("discharge", fake_river, [-24, -12])
    assert driver.lags_hours == (-24.0, -12.0)


# --- validation -------------------------------------------------------------------------------


def test_duplicate_driver_names(fake_tide_gauge, fake_river):
    with pytest.raises(ValueError, match="unique"):
        Recipe(
            target=fake_tide_gauge,
            drivers=(Driver("q", fake_river, (-1,)), Driver("q", fake_river, (-2,))),
        )


def test_empty_lags(fake_river):
    with pytest.raises(ValueError, match="empty"):
        Driver("q", fake_river, ())


@pytest.mark.parametrize("name", ["Discharge", "1q", "q-1", "", "q lag"])
def test_invalid_driver_name(fake_river, name):
    with pytest.raises(ValueError, match="name"):
        Driver(name, fake_river, (-1,))


@pytest.mark.parametrize("freq", ["banana", "0h", "-1h"])
def test_invalid_freq(fake_tide_gauge, freq):
    with pytest.raises(ValueError, match="freq"):
        Recipe(target=fake_tide_gauge, freq=freq)


def test_lags_must_be_multiples_of_freq(fake_tide_gauge, fake_river):
    with pytest.raises(ValueError, match="multiple"):
        Recipe(target=fake_tide_gauge, drivers=(Driver("q", fake_river, (-1.5,)),), freq="1h")
    Recipe(target=fake_tide_gauge, drivers=(Driver("q", fake_river, (-1.5,)),), freq="30min")


def test_target_column_clash(fake_tide_gauge, fake_river):
    with pytest.raises(ValueError, match="clashes"):
        Recipe(
            target=fake_tide_gauge,
            drivers=(Driver("q", fake_river, (-1,)),),
            target_column="q_lag-1h",
        )


def test_forecast_must_be_forecast_source(fake_river):
    with pytest.raises(TypeError, match="ForecastSource"):
        Driver("q", fake_river, (-1,), forecast=fake_river)


@pytest.mark.parametrize(
    "kwargs", [dict(how="median"), dict(max_gap="soon"), dict(lags_hours=(float("nan"),))]
)
def test_invalid_driver_options(fake_river, kwargs):
    params = dict(name="q", source=fake_river, lags_hours=(-1,))
    params.update(kwargs)
    with pytest.raises(ValueError):
        Driver(**params)


def test_invalid_target_how(fake_tide_gauge):
    with pytest.raises(ValueError, match="target_how"):
        Recipe(target=fake_tide_gauge, target_how="median")
