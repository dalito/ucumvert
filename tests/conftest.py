# Common pytest fixtures for all test modules
import pytest


@pytest.fixture(scope="session")
def datadir():
    """DATADIR as a LocalPath"""
    from pathlib import Path

    return Path(__file__).resolve().parent / "data"
