# Common pytest fixtures for all test modules
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def ucum_parser():
    """Parse function as fixture for faster tests"""
    from ucumvert.parser import get_ucum_parser

    return get_ucum_parser()


@pytest.fixture(scope="session")
def ureg_std():
    import pint

    return pint.UnitRegistry()


@pytest.fixture(scope="session")
def transform_std(ureg_std):
    from ucumvert import UcumToPintTransformer

    return UcumToPintTransformer(ureg_std).transform


@pytest.fixture(scope="session")
def ureg_ucumvert():
    import pint

    defdir = Path(__file__).resolve().parents[1] / "src" / "ucumvert"
    ureg = pint.UnitRegistry()
    ureg.load_definitions(defdir / "pint_ucum_defs.txt")
    return ureg


@pytest.fixture(scope="session")
def transform(ureg_ucumvert):
    from ucumvert import UcumToPintTransformer

    return UcumToPintTransformer(ureg_ucumvert).transform
