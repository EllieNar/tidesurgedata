"""Fixtures for the optional RTide compatibility job.

RTide loads the Skyfield ephemeris ``de421.bsp`` from the working directory. It is downloaded
once per session (sockets are enabled only for that download) into ``$DE421_DIR`` or
``~/.cache/tidesurgedata-tests`` (cached by CI) and symlinked into each test's temp directory.
"""

import os
from pathlib import Path

import pytest

DE421_URL = "https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp"


@pytest.fixture(scope="session")
def de421_path() -> Path:
    directory = Path(os.environ.get("DE421_DIR", Path.home() / ".cache" / "tidesurgedata-tests"))
    path = directory / "de421.bsp"
    if not path.exists():
        import pytest_socket
        import requests

        directory.mkdir(parents=True, exist_ok=True)
        pytest_socket.enable_socket()
        try:
            response = requests.get(DE421_URL, timeout=120)
            response.raise_for_status()
        finally:
            pytest_socket.disable_socket(allow_unix_socket=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(response.content)
        tmp.replace(path)
    return path


@pytest.fixture(autouse=True)
def rtide_workdir(tmp_path, monkeypatch, de421_path):
    """Run each test in a fresh directory containing the ephemeris."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "de421.bsp").symlink_to(de421_path)
    return tmp_path
