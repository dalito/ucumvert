from pathlib import Path

import pytest
from lark import LarkError
from pint import UnitRegistry
from test_parser import ucum_examples_valid

from ucumvert import (
    PintUcumRegistry,
    UcumToPintStrTransformer,
    UcumToPintTransformer,
    ucum_preprocessor,
)
from ucumvert.ucum_pint import find_ucum_codes_that_need_mapping
from ucumvert.xml_util import get_metric_units, get_non_metric_units


def get_unit_atoms():
    """List of all case-sensitive defined UCUM units in ucum-essence.xml"""
    return get_metric_units() + get_non_metric_units()


def test_find_ucum_codes_that_need_mapping():
    mappings = find_ucum_codes_that_need_mapping(existing_mappings={})
    assert len(mappings["prefixes"]) == 0
    assert len(mappings["metric"]) == 12  # noqa: PLR2004
    assert len(mappings["non-metric"]) == 33  # noqa: PLR2004


def test_ucum_to_pint(ucum_parser, ureg_std):
    expected_quantity = ureg_std("kilogram")
    parsed_data = ucum_parser.parse("kg")
    result = UcumToPintTransformer(ureg=ureg_std).transform(parsed_data)
    assert result == expected_quantity


@pytest.mark.parametrize(
    "ucum_code",
    ucum_examples_valid.values(),
    ids=[" ".join(kv) for kv in ucum_examples_valid.items()],
)
def test_ucum_to_pint_official_examples(ucum_parser, transform_ucum_pint, ucum_code):
    if ucum_code == "Torr":
        # Torr is missing in ucum-essence.xml but included in the official examples.
        # see https://github.com/ucum-org/ucum/issues/289
        pytest.skip("Torr is not defined in official ucum-essence.xml")
    if ucum_code == "[pH]":
        # TODO create pint issue
        pytest.skip("[pH] = pH_value is not defined in pint due to an issue.")
    parsed_data = ucum_parser.parse(ucum_code)
    transform_ucum_pint(parsed_data)


@pytest.mark.parametrize(
    "ucum_code",
    ucum_examples_valid.values(),
    ids=[" ".join(kv) for kv in ucum_examples_valid.items()],
)
def test_ucum_to_str_official_examples(ucum_parser, transform_ucum_str, ucum_code):
    if ucum_code == "Torr":
        # Torr is missing in ucum-essence.xml but included in the official examples.
        # see https://github.com/ucum-org/ucum/issues/289
        pytest.skip("Torr is not defined in official ucum-essence.xml")
    if ucum_code == "[pH]":
        # TODO create pint issue
        pytest.skip("[pH] = pH_value is not defined in pint due to an issue.")
    parsed_data = ucum_parser.parse(ucum_code)
    transform_ucum_str(parsed_data)


@pytest.mark.parametrize("unit_atom", get_unit_atoms())
def test_ucum_all_unit_atoms_pint(ucum_parser, transform_ucum_pint, unit_atom):
    if unit_atom == "[pH]":
        # TODO create pint issue
        pytest.skip("[pH] = pH_value is not defined in pint due to an issue.")
    parsed_atom = ucum_parser.parse(unit_atom)
    transform_ucum_pint(parsed_atom)


def test_ucum_to_pint_vs_str(ucum_parser, ureg_ucumvert):
    parsed_data = ucum_parser.parse("m/s2.kg")
    expected_quantity = UcumToPintTransformer().transform(parsed_data)
    result_str = UcumToPintStrTransformer().transform(parsed_data)
    assert result_str == "((((m) / (s)**2) * (kg)))"
    assert expected_quantity == ureg_ucumvert("m/s**2 * kg")
    assert ureg_ucumvert(result_str) == expected_quantity


@pytest.mark.parametrize("unit_atom", get_unit_atoms())
def test_ucum_all_unit_atoms_pint_vs_str(
    ucum_parser, transform_ucum_pint, transform_ucum_str, ureg_ucumvert, unit_atom
):
    if unit_atom == "[pH]":
        # TODO create pint issue
        pytest.skip("[pH] = pH_value is not defined in pint due to an issue.")
    parsed_atom = ucum_parser.parse(unit_atom)
    expected_quantity = transform_ucum_pint(parsed_atom)
    result_str = transform_ucum_str(parsed_atom)
    assert ureg_ucumvert(result_str) == expected_quantity


def test_ucum_preprocessor():
    # Don't use ureg_ucumvert from fixture here, because we want to modify it.
    defdir = Path(__file__).resolve().parents[1] / "src" / "ucumvert"
    ureg_ucumvert = UnitRegistry()
    ureg_ucumvert.load_definitions(defdir / "pint_ucum_defs.txt")
    expected = ureg_ucumvert("m*kg")
    ureg_ucumvert.preprocessors.append(ucum_preprocessor)
    assert ureg_ucumvert("m.kg") == expected
    with pytest.raises(LarkError):
        ureg_ucumvert("degC")


def test_ucum_unitregistry():
    ureg = PintUcumRegistry()
    assert ureg.from_ucum("m.kg") == ureg("m*kg")
    assert ureg.from_ucum("Cel") == ureg("degC")


def test_prefix_with_unit_that_is_also_a_prefix_issue24(ucum_parser, ureg_ucumvert):
    parsed_data = ucum_parser.parse("m[IU]/L")

    expected_quantity = ureg_ucumvert("milliinternational_unit/liter")
    assert expected_quantity == UcumToPintTransformer().transform(parsed_data)
    assert expected_quantity == 10**-3 * ureg_ucumvert("[IU]/L")

    result_str = UcumToPintStrTransformer().transform(parsed_data)
    assert result_str == "(((m[IU]) / (L)))"
