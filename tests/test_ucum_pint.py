import pytest
from pint import UnitRegistry
from test_parser import ucum_examples_valid
from ucumvert import UcumToPintTransformer

ureg = UnitRegistry()


def test_ucum_to_pint(ucum_parser):
    expected_quantity = ureg("millimeter")
    parsed_data = ucum_parser.parse("mm")
    result = UcumToPintTransformer().transform(parsed_data)
    assert result == expected_quantity


@pytest.mark.skip("TODO: Add missing UCUM units to pint_ucum_defs.txt")
@pytest.mark.parametrize(
    "ucum_code",
    ucum_examples_valid.values(),
    ids=[" ".join(kv) for kv in ucum_examples_valid.items()],
)
def test_ucum_to_pint_official_examples(ucum_parser, transform, ucum_code):
    if ucum_code == "Torr":
        # Torr is missing in ucum-essence.xml but included in the official examples.
        # see https://github.com/ucum-org/ucum/issues/289
        pytest.skip("Torr is not defined in official ucum-essence.xml")
    parsed_data = ucum_parser.parse(ucum_code)
    _result = transform(parsed_data)
