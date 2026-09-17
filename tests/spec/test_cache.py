"""Spec tests for the parquet cache (BL-04)."""

import contextlib
import dataclasses
import os
from pathlib import Path
from typing import ClassVar

import pandas as pd
import pytest

from tidesurgedata.cache import Cache, default_cache_root
from tidesurgedata.sources.fake import FakeRiver

BL04 = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="BL-04")
WINDOW = (pd.Timestamp("2024-01-01T00:00Z"), pd.Timestamp("2024-03-01T00:00Z"))
CALLS: list = []


@dataclasses.dataclass(frozen=True)
class CountingRiver(FakeRiver):
    quality: str = "verified"
    max_request: ClassVar[pd.Timedelta | None] = pd.Timedelta("30D")

    def _fetch(self, start, end):
        CALLS.append((start, end))
        s, _, r = super()._fetch(start, end)
        return s, self.quality, r


@pytest.fixture(autouse=True)
def _reset():
    CALLS.clear()


@BL04
def test_default_root_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("TIDESURGEDATA_CACHE", str(tmp_path))
    assert default_cache_root() == tmp_path
    monkeypatch.delenv("TIDESURGEDATA_CACHE")
    assert default_cache_root() == Path.home() / ".cache" / "tidesurgedata"


@BL04
def test_cache_miss_then_hit(tmp_path):
    cache = Cache(root=tmp_path)
    source = CountingRiver()
    first = source.fetch(*WINDOW, cache=cache)
    n_calls = len(CALLS)
    assert n_calls > 0
    second = source.fetch(*WINDOW, cache=cache)
    assert len(CALLS) == n_calls  # served from cache
    pd.testing.assert_series_equal(first, second)
    pd.testing.assert_series_equal(first, CountingRiver().fetch(*WINDOW))


@BL04
def test_cache_partial_overlap_fetches_only_missing(tmp_path):
    cache = Cache(root=tmp_path)
    source = CountingRiver()
    source.fetch(*WINDOW, cache=cache)
    CALLS.clear()
    source.fetch(WINDOW[0], WINDOW[1] + pd.Timedelta("20D"), cache=cache)
    assert CALLS and all(s >= WINDOW[1] - pd.Timedelta("30D") for s, _ in CALLS)


@BL04
def test_cache_key_includes_params_and_adapter_version(tmp_path, monkeypatch):
    cache = Cache(root=tmp_path)
    CountingRiver().fetch(*WINDOW, cache=cache)
    CALLS.clear()
    CountingRiver(seed=5).fetch(*WINDOW, cache=cache)
    assert CALLS  # different params: miss
    CALLS.clear()
    monkeypatch.setattr(CountingRiver, "adapter_version", "99")
    CountingRiver().fetch(*WINDOW, cache=cache)
    assert CALLS  # different adapter version: miss


@BL04
def test_preliminary_chunks_expire(tmp_path):
    cache = Cache(root=tmp_path, preliminary_ttl=pd.Timedelta(0))
    CountingRiver(quality="preliminary").fetch(*WINDOW, cache=cache)
    CALLS.clear()
    CountingRiver(quality="preliminary").fetch(*WINDOW, cache=cache)
    assert CALLS  # expired immediately
    verified = Cache(root=tmp_path / "v", preliminary_ttl=pd.Timedelta(0))
    CountingRiver().fetch(*WINDOW, cache=verified)
    CALLS.clear()
    CountingRiver().fetch(*WINDOW, cache=verified)
    assert not CALLS  # verified data does not expire


@BL04
def test_atomic_write(tmp_path, monkeypatch):
    cache = Cache(root=tmp_path)

    def failing_replace(src, dst):
        raise OSError("simulated crash during rename")

    monkeypatch.setattr(os, "replace", failing_replace)
    with contextlib.suppress(OSError):  # raising or warning-and-continuing are both acceptable
        CountingRiver().fetch(*WINDOW, cache=cache)
    monkeypatch.undo()
    assert not list(tmp_path.rglob("*.parquet"))  # no partial chunk visible (temp files: *.tmp)
    CALLS.clear()
    CountingRiver().fetch(*WINDOW, cache=Cache(root=tmp_path))
    assert CALLS  # nothing was cached
