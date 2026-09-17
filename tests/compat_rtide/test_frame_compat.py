"""Frames built from fake sources work with RTide's public API (optional job)."""

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("rtide")

from rtide import RTide  # noqa: E402

from tidesurgedata.sources.fake import FakeTideGauge  # noqa: E402

pytestmark = pytest.mark.rtide


def test_frame_compat():
    gauge = FakeTideGauge(freq="1h", noise_std=0.01)
    series = gauge.fetch("2024-01-01T00:00Z", "2024-01-11T00:00Z")
    df = series.rename("observations").to_frame()

    model = RTide(df, gauge.lat, gauge.lon)
    model.Prepare_Inputs(verbose=False)
    model.Train(standard_epochs=2, verbose=False)

    future_index = pd.date_range("2024-01-11T00:00Z", periods=24, freq="1h", name="time")
    future = pd.DataFrame({"observations": np.nan}, index=future_index)
    predictions = model.Predict(future)

    values = np.asarray(predictions["rtide_test"]).reshape(-1)
    assert len(values) == len(future)
    assert np.isfinite(values).all()
