# Common pytest fixtures for all test modules
import pytest


@pytest.fixture(scope="session")
def ucum_parser():
    """Parse function as fixture for faster tests"""
    from ucumvert.parser import get_ucum_parser

    return get_ucum_parser()


@pytest.fixture(scope="session")
def transform():
    from ucumvert import UcumToPintTransformer

    return UcumToPintTransformer().transform
