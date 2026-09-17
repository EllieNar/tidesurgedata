"""Walking skeleton: recipe -> training frame -> RTide -> forecast frame -> predictions."""

import dataclasses

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("rtide")

from rtide import RTide  # noqa: E402

pytestmark = pytest.mark.rtide


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="BL-12, BL-13")
def test_walking_skeleton(fake_recipe):
    recipe = dataclasses.replace(fake_recipe, target_column="observations")
    train = recipe.training_frame("2024-01-01T00:00Z", "2024-01-15T00:00Z").dropna()
    lat, lon = recipe.target_latlon

    model = RTide(train, lat, lon)
    model.Prepare_Inputs(verbose=False)
    model.Train(standard_epochs=2, verbose=False)

    issued = pd.Timestamp("2024-01-15T00:00Z")
    future = recipe.forecast_frame(issued, horizon_hours=11)
    predictions = model.Predict(future)

    values = np.asarray(predictions["rtide_test"]).reshape(-1)
    assert len(values) == len(future) == 11
    assert np.isfinite(values).all()
