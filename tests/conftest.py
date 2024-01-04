# Common pytest fixtures for all test modules
import pytest


@pytest.fixture(scope="session")
def ucum_parse_fcn():
    """Parse function as fixture for faster tests"""
    from ucumvert.parser import ucum_parser

    return ucum_parser().parse
