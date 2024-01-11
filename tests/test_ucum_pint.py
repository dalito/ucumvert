import pytest
from pint import UnitRegistry
from test_parser import ucum_examples_valid
from ucumvert import UcumToPintTransformer
from ucumvert.ucum_pint import find_ucum_codes_that_need_mapping
from ucumvert.xml_util import get_metric_units, get_non_metric_units

ureg = UnitRegistry()


def get_unit_atoms():
    """List of all case-sensitive defined UCUM units in ucum-essence.xml"""
    return get_metric_units() + get_non_metric_units()


def test_find_ucum_codes_that_need_mapping():
    mappings = find_ucum_codes_that_need_mapping(existing_mappings={})
    assert len(mappings["prefixes"]) == 0
    assert len(mappings["metric"]) == 12  # noqa: PLR2004
    assert len(mappings["non-metric"]) == 33  # noqa: PLR2004


def test_ucum_to_pint(ucum_parser, ureg_std):
    expected_quantity = ureg("millimeter")
    parsed_data = ucum_parser.parse("mm")
    result = UcumToPintTransformer(ureg=ureg_std).transform(parsed_data)
    assert result == expected_quantity


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
    transform(parsed_data)


# comment out next line to see what is missing
@pytest.mark.skip("TODO: Add missing UCUM units to pint_ucum_defs.txt")
@pytest.mark.parametrize("unit_atom", get_unit_atoms())
def test_ucum_all_unit_atoms(ucum_parser, transform, unit_atom):
    parsed_atom = ucum_parser.parse(unit_atom)
    transform(parsed_atom)
